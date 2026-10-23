"""Reproducible reference benchmark for real local video clips.

Objective proxy metrics never replace VBench 2.0 or blinded human review.
"""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from ..core import require, sha256

SCHEMA="qaf_video_paired_benchmark_v1"

def _video(path, fps=8, side=48, max_frames=128):
    p=Path(path).resolve()
    require(p.is_file() and p.suffix.lower() in (".mp4",".webm",".mov"),
            "Video source must exist")
    args=["ffmpeg","-nostdin","-v","error","-i",str(p),
          "-vf",f"fps={fps},scale={side}:{side}:flags=bicubic,format=gray",
          "-frames:v",str(max_frames),"-f","rawvideo","pipe:1"]
    result=subprocess.run(args,capture_output=True,timeout=120,check=False)
    require(result.returncode==0,"Cannot decode video: "+result.stderr.decode(errors="replace")[-300:])
    width=side*side
    n=len(result.stdout)//width
    require(n>=4 and len(result.stdout)==n*width,"Need >=4 decoded frames")
    x=np.frombuffer(result.stdout,dtype=np.uint8).reshape(n,side,side).astype(np.float32)/255
    return x

def video_proxy_metrics(path):
    frames=_video(path)
    means=frames.mean(axis=(1,2))
    inter=np.abs(np.diff(frames,axis=0))
    return {"frames_evaluated":int(len(frames)),
            "luminance_flicker":float(np.abs(np.diff(means)).mean()),
            "frame_difference":float(inter.mean()),
            "third_difference":float(np.abs(np.diff(frames,n=3,axis=0)).mean()),
            "file_sha256":sha256(path),
            "warning":"Camera cuts, brightness flashes and movement confound these proxy metrics"}

def matched_video_benchmark(root, manifest, seed=22, boots=1000):
    root=Path(root).resolve()
    d=json.loads(Path(manifest).read_text(encoding="utf-8"))
    require(d.get("schema")==SCHEMA,"Unsupported benchmark")
    pairs=d.get("pairs",[])
    require(isinstance(pairs,list) and pairs,"Need paired experiments")
    seen=set();results=[];diffs=[]
    for pair in pairs:
        key=pair.get("id")
        require(isinstance(key,str) and key and key not in seen,"Duplicate pair id")
        seen.add(key)
        for field in ("seed","scene","qaf","baseline"):
            require(field in pair,"Missing "+field)
        require(isinstance(pair["seed"],int),"Seed must be integer")
        files={}
        for name in ("qaf","baseline"):
            p=(root/pair[name]).resolve()
            require(p.is_relative_to(root),"Video outside benchmark root")
            files[name]=video_proxy_metrics(p)
        diff=files["qaf"]["luminance_flicker"]-files["baseline"]["luminance_flicker"]
        diffs.append(diff)
        results.append({"id":key,"seed":pair["seed"],"scene":pair["scene"],
                        "proxy_flicker_delta_qaf_minus_baseline":float(diff),
                        "qaf":files["qaf"],"baseline":files["baseline"]})
    diffs=np.asarray(diffs,dtype=float)
    rng=np.random.default_rng(seed)
    ci=np.quantile(rng.choice(diffs,size=(boots,len(diffs)),replace=True).mean(axis=1),[.025,.975])
    return {"schema":"qaf_video_paired_benchmark_report_v1","pairs":len(pairs),
            "proxy_flicker_delta_mean":float(diffs.mean()),
            "bootstrap_95ci":[float(x) for x in ci],
            "proxy_metric_only":True,"human_evaluation":False,
            "vbench_executed":False,"cinematic_superiority_proven":False,
            "qaf_advantage_proven":False,"results":results,
            "caution":"Lower global flicker need not mean better realism. Match seed, prompt, weights, duration, hardware and human preference."}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("root");p.add_argument("manifest")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    report=matched_video_benchmark(args.root,args.manifest)
    Path(args.out).write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))

if __name__=="__main__":main()
