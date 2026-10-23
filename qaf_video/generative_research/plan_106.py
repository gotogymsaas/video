"""Audit coverage of all 106 candidate videos for grouped LoRA training."""
import json,sys
from pathlib import Path
def audit(path):
 d=json.loads(Path(path).read_text(encoding="utf8"))
 if d.get("schema")!="qaf_gym_full_106_plan_v1":raise ValueError("Invalid plan")
 clips=d["clips"];paths=[c["path"] for c in clips]
 if len(paths)!=106 or len(set(paths))!=106:raise ValueError("Missing/duplicated sources")
 if sum(c["bytes"] for c in clips)!=d["total_bytes"]:raise ValueError("Size mismatch")
 unreviewed=sum(c["technical_review"]!="PASSED" for c in clips)
 ungrouped=sum(c["athlete_group"] is None or c["session_group"] is None for c in clips)
 unlabeled=sum(not c["caption"] for c in clips)
 if any(c["split"] is not None for c in clips):
  groups={}
  for c in clips:
   if c["split"] is None:continue
   if c["split"] not in ("train","val","test"):raise ValueError("Invalid split")
   for key in ("athlete_group","session_group","garment_group"):
    val=c[key]
    if val is None:raise ValueError("Grouping required before split")
    pair=(key,val)
    if pair in groups and groups[pair]!=c["split"]:raise ValueError("Leakage")
    groups[pair]=c["split"]
 return {"sources":106,"unreviewed_media":unreviewed,"ungrouped":ungrouped,
         "unlabeled":unlabeled,"gpu_ready":unreviewed==ungrouped==unlabeled==0 and
         all(c["split"] for c in clips) and d.get("gpu_available_in_current_runtime") is True,
         "checkpoint_verified":False}
if __name__=="__main__":print(json.dumps(audit(sys.argv[1]),indent=2))
