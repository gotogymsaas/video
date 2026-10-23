"""Experimental train loop over private, consented local MP4 video.
Not a production or cinematic-quality trainer; 5 frames of 16x16 only.
"""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
import torch
from .cinema_neural import CinemaVAE,VideoDiT,vae_loss,flow_loss

def safe_path(root,name):
    root=Path(root).resolve()
    p=(root/name).resolve()
    if not p.is_relative_to(root) or not p.is_file():raise ValueError("Missing/escaping private asset")
    return p

def check_manifest(path):
    path=Path(path).resolve()
    data=json.loads(path.read_text(encoding="utf8"))
    if data.get("schema")!="qaf_cinematic_training_dataset_v1":raise ValueError("Invalid schema")
    entries=data.get("samples",[])
    if not entries:raise ValueError("No clips")
    subjects={};garments={};seen=set();hashes=set();resolved=[]
    for row in entries:
        split=row.get("split")
        if split not in ("train","val","test"):raise ValueError("Bad split")
        for key in ("id","subject_id","garment_id","rights","consent_record","prompt"):
            if not isinstance(row.get(key),str) or not row[key].strip():raise ValueError("Missing "+key)
        if row["id"] in seen:raise ValueError("Duplicate ID")
        seen.add(row["id"])
        for key,index in (("subject_id",subjects),("garment_id",garments)):
            if row[key] in index and index[row[key]]!=split:raise ValueError("Cross-split leakage")
            index[row[key]]=split
        if row.get("fps")!=12 or row.get("training_frame_count")!=5:
            raise ValueError("Microtrainer requires fps=12 training_frame_count=5")
        safe_path(path.parent,row["reference_image"])
        video=safe_path(path.parent,row["video"])
        digest=hashlib.sha256(video.read_bytes()).hexdigest()
        if digest in hashes:raise ValueError("Duplicate video")
        hashes.add(digest);resolved.append((row,video))
    if not any(s["split"]=="train" for s,_ in resolved) or not any(s["split"]=="val" for s,_ in resolved):
        raise ValueError("Disjoint train and val required")
    return resolved,hashlib.sha256(path.read_bytes()).hexdigest()

def load_frames(video):
    args=["ffmpeg","-nostdin","-v","error","-i",str(video),"-vf",
          "fps=12,scale=16:16:flags=lanczos","-frames:v","5",
          "-pix_fmt","rgb24","-f","rawvideo","pipe:1"]
    p=subprocess.run(args,check=False,capture_output=True,timeout=60)
    if p.returncode or len(p.stdout)!=5*16*16*3:raise ValueError("Five decodable frames required")
    return torch.from_numpy(np.frombuffer(p.stdout,dtype=np.uint8).copy()
        .reshape(5,16,16,3).astype("float32")/255).permute(3,0,1,2).contiguous()

def train_micro_dataset(manifest,output,steps=3,seed=22,device="cpu"):
    if not 1<=steps<=1000:raise ValueError("Steps 1..1000")
    if device=="cuda" and not torch.cuda.is_available():raise ValueError("CUDA unavailable")
    records,source_hash=check_manifest(manifest)
    train=torch.stack([load_frames(path) for row,path in records if row["split"]=="train"])
    val=torch.stack([load_frames(path) for row,path in records if row["split"]=="val"])
    torch.manual_seed(seed);torch.set_num_threads(min(torch.get_num_threads(),2))
    vae=CinemaVAE().to(device);flow=VideoDiT().to(device)
    vae_opt=torch.optim.AdamW(vae.parameters(),lr=.002)
    flow_opt=torch.optim.AdamW(flow.parameters(),lr=.001)
    logs=[]
    for k in range(steps):
        video=train[k%len(train):k%len(train)+1].to(device)
        vae.train();flow.train()
        vae_opt.zero_grad(set_to_none=True)
        loss,_=vae_loss(vae,video);loss.backward();vae_opt.step()
        flow_opt.zero_grad(set_to_none=True)
        flow_err=flow_loss(vae,flow,video);flow_err.backward();flow_opt.step()
        with torch.no_grad():
            vae.eval();validation,_=vae_loss(vae,val.to(device))
        logs.append({"step":k,"vae":float(loss.detach()),"flow":float(flow_err.detach()),
                     "val":float(validation.detach())})
    dest=Path(output);dest.mkdir(parents=True,exist_ok=True)
    file=dest/"authorized_micro_model.pt"
    torch.save({"type":"16x16_experimental_microtrainer","vae":vae.state_dict(),
      "flow":flow.state_dict(),"vae_optimizer":vae_opt.state_dict(),
      "flow_optimizer":flow_opt.state_dict(),"torch_rng":torch.get_rng_state(),
      "dataset_manifest_sha256":source_hash,"seed":seed,"log":logs},file)
    report={"train_samples":len(train),"val_samples":len(val),"steps":steps,
       "source_manifest_sha256":source_hash,"checkpoint_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
       "first":logs[0],"last":logs[-1],"cinematic_model_trained":False,
       "rights_legally_verified":False,"24_papers_empirically_validated":False,
       "warning":"Training input physically decoded; no certification of permissions or video quality"}
    (dest/"report.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    return report

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest");p.add_argument("--out",required=True)
    p.add_argument("--steps",type=int,default=3);p.add_argument("--seed",type=int,default=22)
    p.add_argument("--device",choices=("cpu","cuda"),default="cpu")
    a=p.parse_args()
    print(json.dumps(train_micro_dataset(a.manifest,a.out,a.steps,a.seed,a.device),indent=2))

if __name__=="__main__":main()
