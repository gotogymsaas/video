"""Fail-closed local ComfyUI Image-to-Video adapter.

Uses exported API workflows, never downloads weights or asserts image rights.
By default only creates a dry-run plan. Network is limited to local loopback.
"""
from __future__ import annotations
import copy,hashlib,json,time,uuid
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode,urlsplit
from ..core import require,sha256

MAX_IMAGE=20*1024*1024
MAX_OUTPUT=256*1024*1024

def loopback_url(server):
    u=urlsplit(server)
    require(u.scheme=="http" and u.hostname in ("127.0.0.1","localhost","::1"),
            "ComfyUI must be reachable through local HTTP loopback only")
    require(u.port is not None and 1<=u.port<=65535, "Explicit port required")
    require(not u.username and not u.password and not u.path.strip("/") and not u.query,
            "No credentials/paths in ComfyUI base URL")
    return f"http://127.0.0.1:{u.port}"

def _json_request(base,method,path,body=None):
    content=None if body is None else json.dumps(body).encode("utf-8")
    req=Request(base+path,data=content,method=method,
                headers={"Content-Type":"application/json","Accept":"application/json"})
    with urlopen(req,timeout=30) as response:
        return json.loads(response.read(2*1024*1024).decode("utf-8"))

def patch_workflow(workflow,bindings,values):
    """Map semantic fields to exact ComfyUI node inputs; no guessed node IDs."""
    require(isinstance(workflow,dict) and workflow, "Export workflow in API JSON format")
    for name in ("image","prompt","seed"):
        require(name in bindings and name in values,"Missing binding "+name)
    result=copy.deepcopy(workflow)
    for name,b in bindings.items():
        if name not in values:continue
        require(isinstance(b,dict) and isinstance(b.get("node"),str)
                and isinstance(b.get("input"),str), "Binding schema invalid")
        node=result.get(b["node"])
        require(isinstance(node,dict) and isinstance(node.get("inputs"),dict),
                "Workflow node missing: "+b["node"])
        require(b["input"] in node["inputs"], "Unknown input key: "+b["input"])
        if name=="seed":
            require(isinstance(values[name],int) and not isinstance(values[name],bool),
                    "Seed must be integer")
        node["inputs"][b["input"]]=values[name]
    return result

def validate_job(job,workspace):
    base=Path(workspace).resolve()
    require(job.get("schema")=="qaf_comfy_i2v_job_v1","Job schema unsupported")
    require(job.get("model_family")=="LTX-2.5","Explicit reviewed model family required")
    require(job.get("license_checked") is True and job.get("rights_checked") is True,
            "Model license and input rights review must be recorded")
    approval=job.get("review_document")
    require(isinstance(approval,str) and approval.strip(),"Documentary review reference required")
    approved_file=(base/approval).resolve()
    require(approved_file.is_relative_to(base) and approved_file.is_file() and
            approved_file.stat().st_size>0,"Approval document absent")
    image=(base/job.get("image","")).resolve()
    require(image.is_relative_to(base) and image.is_file(),"Source image not in workspace")
    require(image.suffix.lower() in (".jpg",".jpeg",".png",".webp"),"Unsupported source image")
    require(image.stat().st_size<=MAX_IMAGE,"Image size exceeds limit")
    wf=job.get("workflow");bindings=job.get("bindings")
    require(isinstance(wf,dict) and isinstance(bindings,dict),"Workflow/bindings missing")
    prompt=job.get("prompt");seed=job.get("seed")
    require(isinstance(prompt,str) and prompt.strip() and len(prompt)<=4000,
            "Prompt missing or too long")
    require(isinstance(seed,int) and not isinstance(seed,bool),"Invalid seed")
    values={"image":"__UPLOADED_INPUT__","prompt":prompt,"seed":seed}
    for name in ("frames","fps"):
        if name in job:values[name]=job[name]
    if "frames" in values:
        require(isinstance(values["frames"],int) and values["frames"]>=9
                and (values["frames"]-1)%8==0,"LTX default I2V frame count 8n+1")
    if "fps" in values:
        require(values["fps"] in (16,24,25,30),"Unsupported FPS")
    patch_workflow(wf,bindings,values)
    return {"input_path":image,"review_path":approved_file,"values":values,
            "input_sha256":sha256(image),"approval_sha256":sha256(approved_file)}

def _upload_image(base,image):
    boundary="----qaf-"+uuid.uuid4().hex
    header=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
            f"filename=\"{image.name}\"\r\nContent-Type: image/png\r\n\r\n").encode()
    data=header+image.read_bytes()+f"\r\n--{boundary}--\r\n".encode()
    req=Request(base+"/upload/image",data=data,method="POST",
                headers={"Content-Type":"multipart/form-data; boundary="+boundary})
    with urlopen(req,timeout=90) as reply:
        info=json.loads(reply.read(65536).decode("utf-8"))
    uploaded=info.get("name")
    require(isinstance(uploaded,str) and uploaded and "/" not in uploaded and "\\" not in uploaded,
            "Invalid upload name")
    return uploaded

def _video_entries(outputs):
    for node,val in outputs.items():
        if not isinstance(val,dict):continue
        for key in ("videos","gifs","images"):
            for file in val.get(key,[]):
                if isinstance(file,dict) and str(file.get("filename","")).lower().endswith(".mp4"):
                    yield file

def _save_mp4(base,history,output):
    candidates=list(_video_entries(history.get("outputs",{})))
    require(candidates,"No MP4 found in ComfyUI history (check SaveVideo node)")
    file=candidates[0];name=file["filename"]
    require("/" not in name and "\\" not in name and name not in (".",".."),"Unsafe video filename")
    loc=file.get("subfolder","")
    require(isinstance(loc,str) and ".." not in Path(loc).parts,"Unsafe output subfolder")
    ftype=file.get("type","output")
    require(ftype=="output","Only final output files may be imported")
    query=urlencode({"filename":name,"subfolder":loc,"type":"output"})
    request=Request(base+"/view?"+query,method="GET")
    target=Path(output).resolve()
    require(target.suffix.lower()==".mp4","Output must be MP4")
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+".partial")
    try:
        with urlopen(request,timeout=90) as response,temp.open("wb") as fp:
            copied=0
            while True:
                block=response.read(1024*1024)
                if not block:break
                copied+=len(block)
                require(copied<=MAX_OUTPUT,"Output exceeds configured safety cap")
                fp.write(block)
        require(copied>1024,"Output empty")
        temp.replace(target)
    finally:temp.unlink(missing_ok=True)
    return {"path":str(target),"bytes":copied,"sha256":sha256(target)}

def run_job(job,workspace,server="http://127.0.0.1:8188",execute=False,timeout=900,output=None):
    """Network/inference only with explicit execute=True; never auto-publish."""
    check=validate_job(job,workspace)
    # All schema and license gates run even for dry-run.
    plan={"schema":"qaf_comfy_job_report_v1","provider":"local-comfyui",
          "model_family":job["model_family"],"input_sha256":check["input_sha256"],
          "review_sha256":check["approval_sha256"],"license_not_legally_certified":True,
          "output_needs_human_approval":True,"actual_neural_inference":False,
          "prompt":job["prompt"],"seed":job["seed"]}
    if not execute:
        plan["status"]="dry_run_not_submitted"
        return plan
    require(output is not None,"Explicit output MP4 path required")
    require(10<=timeout<=3600,"Timeout must be between 10 and 3600 seconds")
    base=loopback_url(server)
    info=_json_request(base,"GET","/system_stats")
    require(isinstance(info,dict),"ComfyUI preflight failed")
    uploaded=_upload_image(base,check["input_path"])
    values=dict(check["values"],image=uploaded)
    workflow=patch_workflow(job["workflow"],job["bindings"],values)
    response=_json_request(base,"POST","/prompt",{"prompt":workflow,"client_id":uuid.uuid4().hex})
    identity=response.get("prompt_id")
    require(isinstance(identity,str) and identity,"ComfyUI did not accept prompt")
    start=time.monotonic();history=None
    while time.monotonic()-start<timeout:
        result=_json_request(base,"GET","/history/"+identity)
        if identity in result:
            history=result[identity];break
        time.sleep(2)
    require(history is not None,"ComfyUI inference timeout")
    require(history.get("status",{}).get("status_str") in (None,"success"),
            "ComfyUI reported an execution error")
    artifact=_save_mp4(base,history,output)
    plan.update({"actual_neural_inference":True,"status":"generated_unreviewed",
                 "prompt_id":identity,"artifact":artifact,
                 "model_weights_sha256":"not_supplied_by_comfyui_api",
                 "independent_quality_benchmark_passed":False})
    return plan

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("job",help="JSON job manifest, see docs")
    p.add_argument("--workspace",required=True)
    p.add_argument("--server",default="http://127.0.0.1:8188")
    p.add_argument("--execute",action="store_true",help="Actually submit to local GPU server")
    p.add_argument("--out",help="MP4 target, required when executing")
    args=p.parse_args()
    job=json.loads(Path(args.job).read_text(encoding="utf8"))
    report=run_job(job,args.workspace,args.server,args.execute,output=args.out)
    print(json.dumps(report,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
