"""Local, auditable research workflow; external model training is never implicit."""
from __future__ import annotations
import argparse,json
from .training_readiness import validate_dataset,inspect_checkpoint
from .production_bridge import ingest_generated_clip
from .applicability import qaf_applicability

def main(argv=None):
 p=argparse.ArgumentParser(prog="python -m qaf_video.generative_research")
 sub=p.add_subparsers(dest="command",required=True)
 d=sub.add_parser("validate-dataset",help="Rights, split, media and training-frame checks")
 d.add_argument("manifest");d.add_argument("--model",choices=["hunyuan15","ltx"],default="hunyuan15")
 m=sub.add_parser("inspect-checkpoint")
 m.add_argument("workspace");m.add_argument("checkpoint");m.add_argument("--sha256")
 i=sub.add_parser("ingest-clip",help="Attach already-rendered external neural MP4 to a classic project")
 i.add_argument("project");i.add_argument("--shot",type=int,required=True)
 i.add_argument("--clip",required=True,help="Relative path inside the project folder")
 i.add_argument("--provenance",required=True,help="Local JSON of rights, model, seed and source still")
 a=sub.add_parser("applicability",help="Evaluate measured paired QAF-vs-classical samples")
 a.add_argument("measurements",help="JSON with arrays qaf_quality and baseline_quality")
 args=p.parse_args(argv)
 if args.command=="validate-dataset":result=validate_dataset(args.manifest,args.model)
 elif args.command=="inspect-checkpoint":result=inspect_checkpoint(args.workspace,args.checkpoint,args.sha256)
 elif args.command=="ingest-clip":
  with open(args.provenance,encoding="utf-8") as f:provenance=json.load(f)
  result=ingest_generated_clip(args.project,args.shot,args.clip,provenance)
 else:
  with open(args.measurements,encoding="utf-8") as f:m=json.load(f)
  result=qaf_applicability(**m)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 return 0

if __name__=="__main__":raise SystemExit(main())
