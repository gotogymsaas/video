"""Canonical timeline, file provenance and human approval gates."""
import json
from pathlib import Path
from .core import require,finite,local_asset,sha256,digest
SCHEMA='qaf_cinema_project_v1'
LAYOUTS={'headline','inputs','choice','diary','phone','outro'}

def validate_cinema(m,base,final=False):
    require(isinstance(m,dict) and m.get('schema')==SCHEMA,'Invalid cinema schema')
    fps=m.get('fps');duration=m.get('duration');require(isinstance(fps,int) and not isinstance(fps,bool) and 1<=fps<=60,'Invalid FPS')
    require(finite(duration) and 0<duration<=600 and abs(duration*fps-round(duration*fps))<1e-6,'Invalid duration')
    shots=m.get('shots');require(isinstance(shots,list) and 1<=len(shots)<=100,'1–100 shots required');end=0.;dependencies={};bindings=0
    def asset(name):
        p=local_asset(base,name);record=m.get('assets',{}).get(name,{});actual=sha256(p)
        require(record.get('sha256')==actual,'Changed or unregistered asset: '+name)
        require(record.get('origin') and record.get('rights') and record.get('privacy') in ['public','private'],'Asset provenance incomplete')
        dependencies[name]=actual;return p
    for s in shots:
        a,b=s.get('start'),s.get('end');require(finite(a) and finite(b) and abs(a-end)<1e-6 and b>a,'Timeline gap or overlap')
        require(all(abs(round(t*fps)-t*fps)<1e-5 for t in (a,b)),'Timeline must align to frames');require(s.get('layout') in LAYOUTS,'Unknown layout')
        require(all(isinstance(s.get(k,''),str) and len(s.get(k,''))<=200 for k in ['title','body','eyebrow']),'Invalid text')
        z=s.get('zoom',[1,1]);f=s.get('focus',[.5,.5]);require(len(z)==2 and all(finite(v) and 1<=v<=1.7 for v in z),'Invalid zoom')
        require(len(f)==2 and all(finite(v) and 0<=v<=1 for v in f),'Invalid focus')
        require(s.get('kind','image')=='image','Cinema keyframe renderer accepts stills; standard renderer accepts video')
        if s.get('vfx') is not None:
            from .generative_research.hybrid_vfx import validate_events
            require(isinstance(s['vfx'],dict) and s['vfx'].get('purpose')=='conceptual','Declare VFX conceptual')
            validate_events(s['vfx'].get('events'),1.)
        if s.get('asset'):asset(s['asset'])
        for cid in s.get('claim_ids',[]):
            c=m.get('claims',{}).get(cid,{});require(c.get('source') and c.get('scope') and c.get('status') in ['verified_local','illustrative','documented'],'Unbound claim')
            if c['status']=='verified_local':require(c.get('evidence_asset'),'Local claim needs evidence');asset(c['evidence_asset'])
            bindings+=1
        if s['layout'] in ['inputs','choice','diary']:require(s.get('claim_ids'),'Product mechanism needs evidence binding')
        end=b
    require(abs(end-duration)<1e-6,'Timeline must cover the entire film')
    for key in ['voice','mix','music','logo','phone_screen']:
        if m.get(key):asset(m[key])
    for name in m.get('fonts',{}).values():asset(name)
    if any(s['layout']=='phone' for s in shots):require(m.get('phone_screen'),'Phone shot requires screen')
    if m.get('voice'):require(m.get('caption_audio_sha256')==dependencies[m['voice']],'Captions are stale')
    last=0
    for c in m.get('subtitles',[]):
        require(finite(c.get('start')) and finite(c.get('end')) and last<=c['start']<c['end']<=duration,'Invalid captions')
        require(isinstance(c.get('text'),str) and 0<len(c['text'])<=90,'Invalid caption text');last=c['end']
    if final and m.get('music_production'):
        require(m['music_production'].get('voice_sha256')==dependencies.get(m.get('voice')),'Voice changed; regenerate the music mix')
        require(m.get('reviews',{}).get('audio',{}).get('asset_sha256')==dependencies.get(m.get('mix')),'Audio review must bind the current mix hash')
    if final:
        for key in ['voice','brand','claims','rights','picture','accessibility']+(['audio'] if m.get('music_production') else []):
            r=m.get('reviews',{}).get(key,{});require(r.get('approved') is True and r.get('reviewer') and r.get('at'),'Missing human review: '+key)
    return {'valid':True,'frames':round(duration*fps),'dependencies':dependencies,'claim_bindings':bindings,'final_documentary_checks':final,'human_playback_review':not final}

def load_cinema(path,final=False):
    path=Path(path).resolve();m=json.loads(path.read_text());return m,validate_cinema(m,path.parent,final)

def render_key(m,dependencies,profile,cc,engine,environment):return digest({'project':m,'dependencies':dependencies,'profile':profile,'captions':cc,'engine':engine,'environment':environment})

def public_asset_list(m):return {n:r for n,r in m.get('assets',{}).items() if r.get('privacy')=='public'}
