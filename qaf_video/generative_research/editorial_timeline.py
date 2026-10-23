"""Author-controlled phone tracking and time-coded wellness claims."""
import json,math
from pathlib import Path
from ..core import require,sha256
from .scientific_overlay import validate_claims,overlay_card
def load_timeline(path,frames,width,height):
 p=Path(path).resolve();d=json.loads(p.read_text(encoding="utf8"))
 require(d.get("schema")=="qaf_editorial_timeline_v1","Invalid schema")
 require((d.get("frames"),d.get("width"),d.get("height"))==(frames,width,height),"Geometry mismatch")
 keys=d.get("phone_keyframes",[])
 require(isinstance(keys,list) and 2<=len(keys)<=frames,"Missing keyframes")
 indices=[]
 for key in keys:
  n=key.get("frame");q=key.get("quad")
  require(type(n)==int and 0<=n<frames,"Bad frame index")
  require(isinstance(q,list) and len(q)==4 and all(isinstance(pt,list) and len(pt)==2 and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<bound for v,bound in zip(pt,(width,height))) for pt in q),"Bad phone quad")
  cross=[]
  for j in range(4):
   a,b,c=q[j],q[(j+1)%4],q[(j+2)%4]
   cross.append((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))
  require(all(v>0 for v in cross) or all(v<0 for v in cross),"Non-convex phone")
  indices.append(n)
 require(indices==sorted(set(indices)) and indices[0]==0 and indices[-1]==frames-1,"Timeline not covered")
 claims=d.get("claim_events",[])
 require(isinstance(claims,list) and len(claims)<=20,"Too many overlays")
 if claims:validate_claims({"schema":"qaf_scientific_overlay_v1","claims":[e["claim"] for e in claims]})
 for e in claims:
  require(type(e.get("start"))==int and type(e.get("end"))==int and 0<=e["start"]<e["end"]<=frames,"Claim interval")
  require(e.get("privacy_approved") is True,"Missing human privacy approval")
 return d,sha256(p)
def quad_at(timeline,index):
 for a,b in zip(timeline["phone_keyframes"],timeline["phone_keyframes"][1:]):
  if a["frame"]<=index<=b["frame"]:
   t=(index-a["frame"])/(b["frame"]-a["frame"])
   return [[(1-t)*a["quad"][i][j]+t*b["quad"][i][j] for j in (0,1)] for i in range(4)]
 raise ValueError("Uncovered frame")
def claims_at(image,timeline,index):
 visible=[e for e in timeline.get("claim_events",[]) if e["start"]<=index<e["end"]]
 out=image
 for i,e in enumerate(visible):out=overlay_card(out,e["claim"],16,16+i*100)
 return out
