"""Deterministic hybrid QAF VFX: energy, light, exact UI, and MP4 drafts. NOT neural I2V."""
import json,math,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from ..core import require,sha256
from ..phone import place_phone
COLORS={"emerald":(0,200,118),"gold":(212,180,106),"mint":(15,191,176)}
def validate_events(events,seconds=1.):
 require(isinstance(events,list) and len(events)<=40,'Bad VFX count')
 for e in events:
  require(isinstance(e,dict) and e.get('type') in ('pulse','link','trace') and e.get('color','emerald') in COLORS,'Unsupported VFX')
  a,z=e.get('start'),e.get('end')
  require(all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in (a,z)) and 0<=a<z<=seconds,'Event bounds')
  pts=[e.get('center',[])] if e['type']=='pulse' else e.get('points',[])
  require(isinstance(pts,list) and (len(pts)==1 if e['type']=='pulse' else 2<=len(pts)<=12),'Event coordinates')
  require(all(isinstance(p,(list,tuple)) and len(p)==2 and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and 0<=x<=1 for x in p) for p in pts),'Event coordinates')
 return events
def path_point(points,u):
 p=np.asarray(points,dtype=float);lengths=np.linalg.norm(np.diff(p,axis=0),axis=1);total=float(lengths.sum())
 if not total:return tuple(p[0])
 target=float(np.clip(u,0,1))*total;previous=0.
 for i,length in enumerate(lengths):
  if length and target<=previous+length:return tuple(p[i]+(p[i+1]-p[i])*(target-previous)/length)
  previous+=length
 return tuple(p[-1])
def ease(t):
 t=float(np.clip(t,0,1));return t**3*(10-15*t+6*t*t)
def load_spec(path):
 p=Path(path).resolve();s=json.loads(p.read_text(encoding="utf8"))
 require(s.get("schema")=="qaf_cinematic_hybrid_pilot_v1","Wrong schema")
 fps=s.get("fps");sec=s.get("seconds");w=s.get("width");h=s.get("height")
 require(isinstance(fps,int) and 1<=fps<=60,"Invalid FPS")
 require(isinstance(sec,(int,float)) and 0<sec<=20 and abs(sec*fps-round(sec*fps))<1e-6,"Invalid duration")
 require(isinstance(w,int) and isinstance(h,int) and w%2==h%2==0 and 128<=min(w,h)<=max(w,h)<=1920,"Invalid canvas")
 require(s.get("medical_claims")=="declared_only","No inferred medical claims")
 for key in ("background","phone_screen"):
  name=s.get(key);require(isinstance(name,str) and name,"Missing asset")
  asset=(p.parent/name).resolve();require(asset.is_relative_to(p.parent) and asset.is_file(),"Unsafe asset")
  with Image.open(asset) as image:image.verify()
 if s.get("subject_mask"):
  mask=(p.parent/s["subject_mask"]).resolve()
  require(mask.is_relative_to(p.parent) and mask.is_file(),"Unsafe mask")
  with Image.open(mask) as image:image.verify()
 q=s.get("phone_quad");require(isinstance(q,list) and len(q)==4 and all(len(a)==2 and all(isinstance(x,(float,int)) and math.isfinite(x) for x in a) for a in q),"Four corners required")
 validate_events(s.get('events',[]),sec)
 return s,p.parent
def frame(spec,root,t,background=None,foreground_mask=None):
 w,h=spec["width"],spec["height"]
 photo=(background.convert("RGB") if background is not None else Image.open(root/spec["background"]).convert("RGB")).resize((w,h))
 z0,z1=spec.get("camera",{}).get("zoom",[1,1.05])
 require(1<=z0<=1.2 and 1<=z1<=1.2,"Zoom invalid")
 z=z0+(z1-z0)*ease(t/spec["seconds"]);cw,ch=w/z,h/z
 photo=photo.resize((w,h),Image.Resampling.BICUBIC,box=((w-cw)/2,(h-ch)/2,(w+cw)/2,(h+ch)/2))
 layer=Image.new("RGBA",(w,h));draw=ImageDraw.Draw(layer,"RGBA")
 for e in spec.get("events",[]):
  if not e["start"]<=t<=e["end"]:continue
  progress=(t-e["start"])/(e["end"]-e["start"])
  color=COLORS[e.get("color","emerald")]+(round(190*math.sin(math.pi*progress)**1.3),)
  if e["type"]=="pulse":
   x,y=e["center"];x*=w;y*=h;r=(.05+.18*ease(progress))*min(w,h)
   draw.ellipse((x-r,y-r,x+r,y+r),outline=color,width=max(2,w//320))
  elif e['type']=='link':draw.line([(round(x*w),round(y*h)) for x,y in e['points']],fill=color,width=max(2,w//320))
  else:
   for j in range(18):
    x,y=path_point(e['points'],max(0,ease(progress)-(17-j)*.008));x*=w;y*=h;r=max(2,min(w,h)*(.0015+j*.00015))
    draw.ellipse((x-r,y-r,x+r,y+r),fill=color[:3]+(round(color[3]*(j+1)/18),))
 glow=layer.filter(ImageFilter.GaussianBlur(max(3,w//80)))
 source=np.asarray(photo,dtype=np.float32);lit=np.asarray(glow.convert("RGB"),dtype=np.float32)
 alpha=np.asarray(glow.getchannel("A"),dtype=np.float32)[...,None]/255
 canvas=Image.fromarray(np.uint8(np.clip(source+(lit-source)*alpha*.45,0,255))).convert("RGBA")
 canvas=Image.alpha_composite(Image.alpha_composite(canvas,glow),layer)
 if foreground_mask is not None or spec.get("subject_mask"):
  mask=(foreground_mask.convert("L") if foreground_mask is not None
        else Image.open(root/spec["subject_mask"]).convert("L")).resize((w,h))
  mask=mask.resize((w,h),Image.Resampling.BICUBIC,box=((w-cw)/2,(h-ch)/2,(w+cw)/2,(h+ch)/2))
  foreground=Image.new("RGBA",(w,h));foreground.paste(photo.convert("RGBA"),(0,0),mask)
  canvas=Image.alpha_composite(canvas,foreground)
 report={}
 if spec.get('phone_overlay',True):canvas,report=place_phone(canvas,Image.open(root/spec["phone_screen"]).convert("RGB"),spec["phone_quad"])
 return canvas.convert("RGB"),report
def render(project,output):
 project=Path(project).resolve();spec,root=load_spec(project)
 out=Path(output).resolve();require(out.suffix.lower()==".mp4","Only MP4 output")
 out.parent.mkdir(parents=True,exist_ok=True)
 frames=round(spec["fps"]*spec["seconds"]);require(frames<=600,"Frame limit")
 args=["ffmpeg","-nostdin","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f'{spec["width"]}x{spec["height"]}',"-r",str(spec["fps"]),"-i","pipe:0","-an","-c:v","libx264","-pix_fmt","yuv420p",str(out)]
 proc=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  for i in range(frames):
   im,_=frame(spec,root,i/spec["fps"]);proc.stdin.write(im.tobytes())
  proc.stdin.close();error=proc.stderr.read().decode(errors="replace");proc.stderr.close()
  require(proc.wait(timeout=180)==0,"FFmpeg failed: "+error[-500:])
 finally:
  if proc.poll() is None:proc.kill();proc.wait()
 report={"frames":frames,"fps":spec["fps"],"sha256":sha256(out),"source_sha256":sha256(project),
         "neural_motion_generated":False,"needs_human_review":True}
 out.with_suffix(".report.json").write_text(json.dumps(report,indent=2),encoding="utf8")
 return report
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("manifest");p.add_argument("--out",required=True)
 a=p.parse_args();print(json.dumps(render(a.manifest,a.out),indent=2))
if __name__=="__main__":main()
