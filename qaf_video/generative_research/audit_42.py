"""Fail-closed scientific coverage audit of QAF Cinema 42 manuscripts."""
from __future__ import annotations
import json
from pathlib import Path
def audit(root):
 root=Path(root).resolve()
 data=json.loads((root/"docs/generative_research/cinema_42/registry.json").read_text(encoding="utf8"))
 if data.get("schema")!="qaf_cinema_42_implementation_registry_v1":raise ValueError("Bad schema")
 required={f"P{i:02d}{j}" for i in range(1,13) for j in range(1,4)} | {f"A0{i}" for i in range(1,7)}
 studies=data.get("studies",[])
 if len(studies)!=42 or {x["id"] for x in studies}!=required:raise ValueError("Incomplete 42-paper registry")
 linked=0
 for row in studies:
  name=row.get("related_module")
  if name:
   path=(root/"qaf_video"/name).resolve()
   if not path.is_relative_to(root/"qaf_video"):raise ValueError("Unsafe module path")
   linked+=int(path.is_file())
 return {"registered":len(studies),"technology_papers":36,"learning_syntheses":6,
         "linked_partial_modules":linked,"scientifically_verified":sum(x["verified"] is True for x in studies),
         "complete":all(x["verified"] is True for x in studies),
         "warning":"Related existing code is not equivalent to implementing or validating a scientific paper."}
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("repo",nargs="?",default=".")
 a=p.parse_args();print(json.dumps(audit(a.repo),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
