"""Project validation, provenance and portable files. No external account access."""
from __future__ import annotations
import hashlib,json,math,os,subprocess,tempfile
from pathlib import Path

ASSETS=Path(__file__).parent/'assets'
PROFILES={'vertical':(1080,1920),'horizontal':(1920,1080),'proxy':(540,960),'landscape-proxy':(960,540)}
class ValidationError(ValueError):pass

def finite(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def require(condition,message):
    if not condition:raise ValidationError(message)
def sha256(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def atomic_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.write_',suffix='.json')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        os.replace(tmp,p)
    finally:Path(tmp).unlink(missing_ok=True)
def local_asset(base,name):
    require(isinstance(name,str) and bool(name),'Asset path required')
    base=Path(base).resolve();p=(base/name).resolve()
    require(p.is_relative_to(base),'Asset escapes project directory')
    require(p.is_file(),f'Asset missing: {name}')
    return p

def run(args,**kw):
    args=list(args)
    if str(args[0])=='ffmpeg' and '-nostdin' not in args:args.insert(1,'-nostdin')
    try:return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,**kw)
    except FileNotFoundError as e:raise ValidationError(f'Missing executable: {args[0]}') from e
    except subprocess.CalledProcessError as e:raise ValidationError(f'{args[0]} failed: {(e.stderr or "")[-1800:]}') from e

def probe(p,count=False):
    args=['ffprobe','-v','error']+(['-count_frames'] if count else [])
    return json.loads(run(args+['-show_streams','-show_format','-of','json',p]).stdout)
def duration(p):return float(probe(p)['format']['duration'])
def load(path):
    p=Path(path).resolve();m=json.loads(p.read_text(encoding='utf-8'));validate(m,p.parent);return m

def validate(m,base,final=False,verify_assets=True):
    require(isinstance(m,dict) and m.get('schema')=='qaf_video_project_v1','Unsupported project schema')
    fps=m.get('fps');seconds=m.get('duration')
    require(isinstance(fps,int) and not isinstance(fps,bool) and 1<=fps<=60,'FPS must be integer 1–60')
    require(finite(seconds) and 0<seconds<=600,'Duration must be 0–600 seconds')
    require(abs(seconds*fps-round(seconds*fps))<1e-6,'Duration must align to frames')
    require(m.get('mode') in ['conceptual','demonstration'],'Mode must be conceptual or demonstration')
    shots=m.get('shots');require(isinstance(shots,list) and 1<=len(shots)<=100,'1–100 shots required')
    claims=m.get('claims',{});require(isinstance(claims,dict),'Claims must be a map')
    end=0
    asset_names=[]
    for i,s in enumerate(shots):
        require(isinstance(s,dict),f'Invalid shot {i}')
        a,b=s.get('start'),s.get('end')
        require(finite(a) and finite(b) and abs(a-end)<1e-6 and b>a,f'Shot {i}: gap, overlap or invalid times')
        require(all(abs(v*fps-round(v*fps))<1e-6 for v in (a,b)),f'Shot {i}: fractional frame')
        end=b
        require(s.get('kind','image') in ['image','video'],f'Shot {i}: unsupported kind')
        for key in ['title','body','eyebrow','card']:
            require(isinstance(s.get(key,''),str),f'Shot {i}: text must be a string')
        require(len(s.get('title',''))<=100 and len(s.get('body',''))<=190,f'Shot {i}: shorten text')
        require(isinstance(s.get('focus',{}),dict),'Focus must be a map')
        for focus in s.get('focus',{'vertical':[.5,.5]}).values():
            require(isinstance(focus,list) and len(focus)==2 and all(finite(x) and 0<=x<=1 for x in focus),'Invalid focus')
        zoom=s.get('zoom',[1,1.06]);require(isinstance(zoom,list) and len(zoom)==2 and all(finite(z) and 1<=z<=1.3 for z in zoom),'Zoom outside 1–1.3')
        nodes=s.get('nodes',[]);require(isinstance(nodes,list) and len(nodes)<=5 and all(isinstance(n,str) and len(n)<=22 for n in nodes),'Node labels too long')
        if s.get('asset'):
            asset_names.append(s['asset'])
            if verify_assets:
                p=local_asset(base,s['asset'])
                if s.get('kind','image')=='video':
                    require(finite(s.get('in',0)) and s.get('in',0)>=0,'Invalid video in-point')
                    require(duration(p)+.04>=b-a+s.get('in',0),'Video too short')
                else:
                    from PIL import Image
                    with Image.open(p) as im:im.verify()
        ids=s.get('claim_ids',[]);require(isinstance(ids,list),'claim_ids must be a list')
        if s.get('evidence_required') or ((final or m['mode']=='demonstration') and any(s.get(k) for k in ['title','body','card'])):
            require(bool(ids),f'Shot {i}: claim binding required')
        for cid in ids:
            require(isinstance(cid,str),'Claim identifiers must be strings')
            c=claims.get(cid);require(isinstance(c,dict) and c.get('source'),f'Claim missing source: {cid}')
            require(c.get('status') in ['verified','conceptual','experimental','unsupported'],'Invalid claim status')
            if final or m['mode']=='demonstration':require(c['status']=='verified',f'Unverified claim: {cid}')
            if c['status']=='verified':
                require(c.get('scope') and c.get('verified_at') and c.get('reviewer'),f'Incomplete claim record: {cid}')
    require(abs(end-seconds)<1e-6,'Timeline does not end at duration')
    for key in ['voice','music','ambience','effects','logo']:
        if m.get(key):
            asset_names.append(m[key])
            if verify_assets:local_asset(base,m[key])
    subs=m.get('subtitles',[]);require(isinstance(subs,list),'Subtitles must be a list');last=0
    for s in subs:
        require(isinstance(s,dict),'Subtitle must be a record')
        require(finite(s.get('start')) and finite(s.get('end')) and last<=s['start']<s['end']<=seconds,'Invalid subtitle interval')
        require(isinstance(s.get('text'),str) and 0<len(s['text'])<=90,'Subtitle must contain 1–90 characters')
        last=s['end']
    if m.get('voice') and verify_assets:require(duration(local_asset(base,m['voice']))<=seconds,'Voice exceeds episode')
    if final:
        require(bool(m.get('voice')) and bool(m.get('logo')),'Final needs voice and original logo')
        require(bool(subs),'Final needs aligned captions')
        require(m.get('caption_audio_sha256')==sha256(local_asset(base,m['voice'])),'Captions do not reference current voice')
        reviews=m.get('reviews',{})
        for key in ['brand','voice','claims','rights','picture','accessibility']:
            review=reviews.get(key,{})
            require(isinstance(review,dict) and review.get('approved') is True and review.get('reviewer') and review.get('at'),f'Missing review: {key}')
        for name in set(asset_names):
            a=m.get('assets',{}).get(name,{})
            require(a.get('origin') and a.get('rights') and a.get('sha256')==sha256(local_asset(base,name)),f'Asset provenance incomplete or changed: {name}')
    return {'valid':True,'frames':round(fps*seconds),'mode':m['mode'],'final_documentary_checks':bool(final),'human_review_not_automated':True}
