"""Optional external VBench runner; no download, install or GPU execution by default.

Version-agnostic VBench v1 evaluator contract from official documentation.
VBench 2.0 can be run separately with its native instructions and pre-trained
weights. Objective scores are only part of a human-audited benchmark.
"""
from __future__ import annotations
import json,subprocess
from pathlib import Path
from ..core import require,sha256

STANDARD_DIMENSIONS={
"subject_consistency","background_consistency","temporal_flickering",
"motion_smoothness","dynamic_degree","aesthetic_quality","imaging_quality",
"object_class","multiple_objects","human_action","color","spatial_relationship",
"scene","temporal_style","appearance_style","overall_consistency"
}
CUSTOM_DIMENSIONS={
"subject_consistency","background_consistency","motion_smoothness",
"dynamic_degree","aesthetic_quality","imaging_quality"
}
def vbench_plan(vbench_repo,video_dir,dimensions=("subject_consistency","motion_smoothness",
                                              "dynamic_degree","imaging_quality"), mode="custom_input"):
    root=Path(vbench_repo).resolve()
    videos=Path(video_dir).resolve()
    require((root/"evaluate.py").is_file(),"VBench checkout lacks evaluate.py")
    require(videos.is_dir(),"Video evaluation directory absent")
    clips=sorted(p for p in videos.glob("*.mp4") if p.is_file())
    require(bool(clips),"No MP4 files in evaluation folder")
    dims=list(dimensions)
    require(bool(dims) and len(set(dims))==len(dims),"Invalid dimensions")
    require(mode in ("custom_input","vbench_standard"),"Unsupported VBench mode")
    allowed=CUSTOM_DIMENSIONS if mode=="custom_input" else STANDARD_DIMENSIONS
    require(set(dims).issubset(allowed),"Dimension unsupported in the selected VBench mode")
    jobs=[["python","evaluate.py","--videos_path",str(videos),"--dimension",dim,
           "--mode",mode] for dim in dims]
    return {"schema":"qaf_vbench_external_plan_v1","cwd":str(root),"mode":mode,
            "source_clips":len(clips),"sha256":{p.name:sha256(p) for p in clips},
            "jobs":jobs,"executed":False,"requires_external_models":True,
            "requires_human_review":True,"license_review_is_external":True}

def execute_vbench(plan,run=False,timeout=3600):
    require(plan.get("schema")=="qaf_vbench_external_plan_v1","Invalid plan")
    if not run:return {"executed":False,"jobs":len(plan.get("jobs",[])),
                       "warning":"No VBench evaluation run: add --execute and install its official dependencies"}
    require(60<=timeout<=86400,"Timeout out of bounds")
    reports=[]
    for command in plan["jobs"]:
        require(len(command)==8 and command[:2]==["python","evaluate.py"] and
                command[2]=="--videos_path" and command[4]=="--dimension" and
                command[6]=="--mode" and command[7] in ("custom_input","vbench_standard") and
                command[5] in (CUSTOM_DIMENSIONS if command[7]=="custom_input" else STANDARD_DIMENSIONS),
                "Unsafe VBench argv")
        res=subprocess.run(command,cwd=plan["cwd"],capture_output=True,text=True,
                           timeout=timeout,check=False)
        reports.append({"dimension":command[5],"returncode":res.returncode,
                        "stdout_tail":res.stdout[-1200:],"stderr_tail":res.stderr[-1200:]})
        if res.returncode!=0:
            break
    success=len(reports)==len(plan["jobs"]) and all(x["returncode"]==0 for x in reports)
    return {"executed":True,"all_dimensions_completed":success,
            "results":reports,"quality_superiority_certified":False,
            "warning":"Inspect evaluator output, same-backbone matched seeds, licensing and blinded human ratings"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("vbench_repo");p.add_argument("video_dir")
    p.add_argument("--dimensions",nargs="+",default=["subject_consistency","motion_smoothness","dynamic_degree","imaging_quality"])
    p.add_argument("--mode",choices=["custom_input","vbench_standard"],default="custom_input")
    p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    plan=vbench_plan(a.vbench_repo,a.video_dir,a.dimensions,mode=a.mode)
    print(json.dumps({"plan":plan,"run":execute_vbench(plan,a.execute)},indent=2))

if __name__=="__main__":main()
