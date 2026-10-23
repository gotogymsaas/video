"""Convert reviewed copies of appdesplegada gym clips to QAF private dataset.

This script never downloads private footage, never assumes rights from GitHub
access and never writes consent records into public repository.
"""
from __future__ import annotations
import json,hashlib,argparse
from pathlib import Path

def fail(condition,message):
 if not condition:raise ValueError(message)
def materialize(candidate_inventory,approval_manifest,clips_root,output):
 inventory=json.loads(Path(candidate_inventory).read_text(encoding="utf-8"))
 fail(inventory.get("schema")=="qaf_cross_repo_candidate_corpus_v1","Invalid inventory")
 allowed={x["source_path"]:x for x in inventory["files"]}
 approvals=json.loads(Path(approval_manifest).read_text(encoding="utf-8"))
 fail(approvals.get("schema")=="qaf_gym_corpus_approvals_v1","Invalid approval manifest")
 root=Path(clips_root).resolve()
 fail(root.is_dir(),"Private clips root required")
 output=Path(output).resolve()
 fail(output.is_relative_to(root),"Output should be in private clips root")
 rows=[];tracked=set();splits={"train":0,"val":0,"test":0}
 actors={};garments={}
 for row in approvals.get("approved",[]):
  path=row.get("source_path")
  fail(path in allowed and path not in tracked,"Unknown or duplicate candidate clip")
  tracked.add(path)
  fail(row.get("training_rights_documented") is True and
       row.get("participant_consent_documented") is True and
       row.get("reviewed_by") and row.get("review_reference"),
       "Training needs individually documented rights, consent and reviewer")
  split=row.get("split");fail(split in splits,"Train/val/test split required")
  actor=row.get("actor_group");garment=row.get("garment_group")
  fail(isinstance(actor,str) and actor and isinstance(garment,str) and garment,
       "Group by real actor and garment across takes")
  for val,index in ((actor,actors),(garment,garments)):
   fail(val not in index or index[val]==split,"Cross-split identity/garment leakage")
   index[val]=split
  local=(root/path).resolve()
  fail(local.is_relative_to(root) and local.is_file(),"Local original video absent")
  fail(local.stat().st_size==allowed[path]["size_bytes"],
       "Local video size differs from GitHub inventory")
  fail(isinstance(row.get("caption"),str) and len(row["caption"].strip())>=8,
       "Human-verified caption required")
  fail(isinstance(row.get("fps"),int) and 8<=row["fps"]<=60,"Sample FPS required")
  fail(isinstance(row.get("training_frame_count"),int) and (row["training_frame_count"]-1)%8==0
       and row["training_frame_count"]>=9,"LTX temporal dimension should be 8n+1")
  h=hashlib.sha256()
  with local.open("rb") as f:
   for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
  rows.append({"id":f"gym-{len(rows):04d}","split":split,"subject_id":actor,
   "garment_id":garment,"video":path,"prompt":row["caption"],
   "rights":row["review_reference"],"consent_record":row["review_reference"],
   "fps":row["fps"],"training_frame_count":row["training_frame_count"],
   "clip_sha256":h.hexdigest()})
  splits[split]+=1
 fail(all(v>0 for v in splits.values()),"Approved train/val/test sets required")
 result={"schema":"qaf_cinematic_training_dataset_v1","samples":rows}
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 return {"approved_clips":len(rows),"splits":splits,"output":str(output),
         "training_executed":False,"rights_independently_certified":False}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("inventory");p.add_argument("approvals");p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 a=p.parse_args()
 print(json.dumps(materialize(a.inventory,a.approvals,a.root,a.out),indent=2))
if __name__=="__main__":main()
