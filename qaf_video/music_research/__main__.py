"""Executable music research pipeline: no cloud service or weights required."""
import argparse,json
from pathlib import Path
from .preference import target,choose
from .arrangement import align
from .synthesis import render,PRESETS
from .mixing import mix
from .evaluation import paired_report,verify_asset

def main(argv=None):
 p=argparse.ArgumentParser(prog='python -m qaf_video.music_research')
 s=p.add_subparsers(dest='cmd',required=True)
 a=s.add_parser('sketch');a.add_argument('--out',required=True);a.add_argument('--preset',choices=PRESETS,default='run_club');a.add_argument('--seconds',type=float,default=60);a.add_argument('--seed',type=int,default=22);a.add_argument('--plan',help='JSON result from align; bpm and duration must match')
 a=s.add_parser('align');a.add_argument('--bpm',type=float,default=124);a.add_argument('--seconds',type=float,default=60);a.add_argument('--cues',nargs=3,type=float,default=[13,29,50]);a.add_argument('--tolerance',type=float,default=.25)
 a=s.add_parser('select');a.add_argument('brief')
 a=s.add_parser('mix');a.add_argument('--voice',required=True);a.add_argument('--music',required=True);a.add_argument('--out',required=True);a.add_argument('--seconds',type=float,default=60);a.add_argument('--bpm',type=float,default=124)
 a=s.add_parser('evaluate');a.add_argument('ratings')
 a=s.add_parser('rights');a.add_argument('asset');a.add_argument('manifest');a.add_argument('--as-of',required=True)
 args=p.parse_args(argv)
 def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
 if args.cmd=='sketch':
  cues=None
  if args.plan:
   plan=read(args.plan)
   if abs(plan['bpm']-PRESETS[args.preset]['bpm'])>1e-6 or abs(plan['duration']-args.seconds)>1e-6:raise ValueError('Plan/preset mismatch')
   cues=plan['aligned_cues']
  result=render(args.out,args.preset,args.seconds,seed=args.seed,cues=cues)
 elif args.cmd=='align':result=align(args.cues,args.seconds,args.bpm,tolerance=args.tolerance)
 elif args.cmd=='select':
  b=read(args.brief);t=target(b['references'],b['as_of']);result={'target':t,'decision':choose(b['candidates'],t['features'])}
 elif args.cmd=='mix':result=mix(args.out,args.voice,args.music,args.seconds,args.bpm)
 elif args.cmd=='evaluate':result=paired_report(read(args.ratings))
 else:result=verify_asset(args.asset,read(args.manifest),args.as_of)
 print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
if __name__=='__main__':main()
