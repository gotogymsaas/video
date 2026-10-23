"""Metadata triage and private FFprobe evaluation for GoToGym gym video corpus.

Never presumes film consent or AI training rights. Filename inference is merely
a review suggestion. Byte-identical and Git object duplicate checks differ
from visual/perceptual duplicates, which require actual local decoding.
"""
from __future__ import annotations
import argparse, json, hashlib, re
from collections import Counter,defaultdict
from pathlib import Path
from ..core import probe

SCHEMA="qaf_gym_corpus_triage_v1"
KNOWN={"bench_press","bent_over_row","bodyweight_squat","deadlift","lunge",
       "overhead_press","plank","pull_up","push_up","single_leg_rdl"}

def plan(inventory):
    data=json.loads(Path(inventory).read_text(encoding="utf8"))
    if data.get("schema")!="qaf_cross_repo_candidate_corpus_v1":
        raise ValueError("Wrong inventory schema")
    files=data.get("files",[])
    seen_paths=set();blobs=defaultdict(list);rows=[]
    for item in files:
        path=item.get("source_path");size=item.get("size_bytes");blob=item.get("git_blob_sha")
        if not isinstance(path,str) or not path.startswith("Videos_test_gimnasio/") or not path.lower().endswith(".mp4") or path in seen_paths:
            raise ValueError("Invalid or duplicated source path")
        seen_paths.add(path)
        if type(size)!=int or size<=0 or not isinstance(blob,str) or not re.fullmatch("[0-9a-f]{40}",blob):
            raise ValueError("Invalid repository metadata")
        blobs[blob].append(path)
        stem=Path(path).stem
        exercise=stem if stem in KNOWN else None
        rows.append({"source_path":path,"git_blob_sha":blob,"size_bytes":size,
            "exercise_suggestion":exercise,"caption_verified":False,
            "copyright_and_ai_training_rights":"UNREVIEWED",
            "participant_likeness_consent":"UNREVIEWED",
            "possible_minor_review":"REQUIRED",
            "source_category":"named_exercise" if exercise else "unclassified_recording",
            "review_priority":"FIRST" if exercise else "SECOND",
            "eligible_for_training":False,
            "actor_group":None,"garment_group":None,"train_split":None,
            "duration_s":None,"width":None,"height":None,"fps":None,
            "sha256_local":None,"perceptual_duplicate_analysis":"NOT_RUN"})
    return {"schema":SCHEMA,"source_repository":data["source_repository"],
       "source_tree_sha":data["source_tree_sha"],
       "candidate_count":len(rows),"total_source_bytes":sum(x["size_bytes"] for x in rows),
       "named_exercise_candidates":sum(x["exercise_suggestion"] is not None for x in rows),
       "git_exact_duplicate_groups":[v for v in blobs.values() if len(v)>1],
       "full_video_decode_performed":False,"rights_review_performed":False,
       "training_performed":False,"clips":rows}

def inspect_private(report,local_root):
    root=Path(local_root).resolve()
    if not root.is_dir():raise ValueError("Local private source folder absent")
    output=json.loads(json.dumps(report))
    by_digest=defaultdict(list);checked=0;missing=[]
    for row in output["clips"]:
        path=(root/row["source_path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            missing.append(row["source_path"]);continue
        if path.stat().st_size!=row["size_bytes"]:
            raise ValueError("Source file byte size does not match repository inventory")
        info=probe(path)
        streams=[s for s in info.get("streams",[]) if s.get("codec_type")=="video"]
        if not streams:raise ValueError("Missing decoded video metadata")
        stream=streams[0]
        fps_string=stream.get("avg_frame_rate","0/1")
        num,den=map(int,fps_string.split("/"))
        if den==0 or num==0:raise ValueError("No valid source FPS")
        h=hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
        digest=h.hexdigest();by_digest[digest].append(row["source_path"])
        row.update({"duration_s":float(info["format"]["duration"]),
                    "width":int(stream["width"]),"height":int(stream["height"]),
                    "fps":round(num/den,4),"sha256_local":digest})
        checked+=1
    output["private_media_inspected"]=checked
    output["missing_local_media_count"]=len(missing)
    output["sha256_exact_duplicate_groups"]=[v for v in by_digest.values() if len(v)>1]
    output["full_video_decode_performed"]=False
    output["rights_review_performed"]=False
    return output

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("inventory");ap.add_argument("--local-root")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    result=plan(args.inventory)
    if args.local_root:result=inspect_private(result,args.local_root)
    output=Path(args.out).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in result.items() if k!="clips"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
