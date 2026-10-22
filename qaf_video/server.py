"""Loopback-only local studio. Token protected writes, confined files, one worker.

This is a desktop companion server, not a multi-user internet deployment.
"""
from __future__ import annotations
import base64, json, mimetypes, secrets, threading, traceback
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from .core import ValidationError, require, load, validate, atomic_json, sha256, probe
from .demo import create_project
from .pipeline import render_project, storyboard
from .planning import plan_project, benchmark
from .cinema_project import SCHEMA,validate_cinema

def validate_any(m,base,final=False):
    return validate_cinema(m,base,final) if m.get('schema')==SCHEMA else validate(m,base,final)

def read_any(path):
    m=json.loads(Path(path).read_text(encoding='utf-8'));validate_any(m,Path(path).parent);return m


def confined(root, name):
    require(isinstance(name,str) and name and not Path(name).is_absolute(), 'Use a relative workspace path')
    p=(root/name).resolve();require(p.is_relative_to(root.resolve()), 'Path escapes workspace')
    return p


class Studio:
    def __init__(self, root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.token=secrets.token_urlsafe(32);self.jobs={};self.lock=threading.RLock()
        self.worker=ThreadPoolExecutor(max_workers=1,thread_name_prefix='qaf-render')
    def busy(self):
        return any(j['state'] in ['queued','running'] for j in self.jobs.values())
    def job(self, action, function):
        with self.lock:
            require(not self.busy(), 'A job is already running; wait before starting another')
            jid=secrets.token_hex(6)
            self.jobs[jid]={'id':jid,'action':action,'state':'queued','progress':0}
        def run_job():
            with self.lock:self.jobs[jid]['state']='running'
            def progress(value):
                with self.lock:self.jobs[jid]['progress']=round(float(value),3)
            try:
                result=function(progress)
                with self.lock:self.jobs[jid].update(state='completed',progress=1,result=result)
            except Exception as e:
                with self.lock:self.jobs[jid].update(state='failed',error=f'{type(e).__name__}: {e}')
                traceback.print_exc()
        self.worker.submit(run_job)
        return {'job_id':jid}


def handler(studio):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args): pass
        def reply(self, value, status=200):
            data=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
        def valid_host(self):
            allowed=[f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
            require(self.headers.get('Host') in allowed,'Invalid local Host header')
            origin=self.headers.get('Origin')
            require(not origin or origin in ['http://'+a for a in allowed],'Cross-origin request refused')
        def do_GET(self):
            try:
                self.valid_host();u=urlparse(self.path);q=parse_qs(u.query)
                if u.path=='/':
                    html=(Path(__file__).parent/'web/index.html').read_text(encoding='utf-8').replace('__TOKEN__',studio.token).encode()
                    self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
                    self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(html)))
                    self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(html)
                elif u.path=='/api/state':
                    projects=[str(p.relative_to(studio.root)) for p in studio.root.rglob('project.json')
                              if p.resolve().is_relative_to(studio.root)][:100]
                    with studio.lock: self.reply({'projects':projects,'jobs':list(studio.jobs.values())[-20:],'busy':studio.busy()})
                elif u.path=='/api/project':
                    p=confined(studio.root,q.get('path',[''])[0]);m=json.loads(p.read_text(encoding='utf-8'))
                    profiles=[]
                    for a in (p.parent/'voice-profiles').glob('*/voice-profile.json'):
                        if a.resolve().is_relative_to(p.parent):
                            v=json.loads(a.read_text(encoding='utf-8'));profiles.append({'path':str(a.relative_to(p.parent)),'name':v.get('name',a.parent.name),
                                'reference_audio':str((a.parent/v.get('reference_audio','reference.wav')).relative_to(p.parent))})
                    self.reply({'project':m,'assets':[str(a.relative_to(p.parent)) for a in (p.parent/'assets').glob('*')
                                                    if a.is_file() and a.resolve().is_relative_to(p.parent)],'voice_profiles':profiles})
                elif u.path.startswith('/media/'):
                    self.media(confined(studio.root,unquote(u.path[len('/media/'): ])))
                else:self.reply({'error':'Not found'},404)
            except (ValidationError,ValueError,KeyError,OSError) as e:self.reply({'error':str(e)},400)
        def media(self,p):
            require(p.is_file() and p.suffix.lower() in ['.mp4','.png','.jpg','.jpeg','.webp','.wav','.mp3','.ogg','.json','.pdf'], 'Media file not available')
            size=p.stat().st_size;start=0;end=size-1;status=200
            range_header=self.headers.get('Range')
            if range_header:
                import re
                match=re.fullmatch(r'bytes=(\d+)-(\d*)',range_header)
                require(bool(match),'Unsupported media range')
                start=int(match[1]);end=min(int(match[2]) if match[2] else end,end)
                if start>end or start>=size:
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return
                status=206
            self.send_response(status);self.send_header('Content-Type',mimetypes.guess_type(p)[0] or 'application/octet-stream')
            self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
            if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            with p.open('rb') as f:
                f.seek(start);left=end-start+1
                while left:
                    data=f.read(min(left,256*1024))
                    if not data:break
                    self.wfile.write(data);left-=len(data)
        def do_POST(self):
            try:
                self.valid_host()
                require(secrets.compare_digest(self.headers.get('X-Studio-Token',''),studio.token),'Invalid studio token')
                require(self.headers.get('Content-Type','').startswith('application/json'),'JSON content required')
                size=int(self.headers.get('Content-Length','0'));require(0<size<=32*1024*1024,'Request too large or empty')
                data=json.loads(self.rfile.read(size));require(isinstance(data,dict),'Expected JSON object')
                action=urlparse(self.path).path.removeprefix('/api/')
                if action=='init':
                    folder=confined(studio.root,data.get('folder','episodio-01'))
                    result=studio.job(action,lambda progress:{'project_path':str(create_project(folder,seconds=data.get('seconds',60),samples=8).relative_to(studio.root))})
                elif action=='benchmark':result=studio.job(action,lambda progress:benchmark())
                else:
                    path=confined(studio.root,data.get('path',''));require(path.name=='project.json','Select a project.json')
                    if action in ['save','import','attach-voice','phone-screen']:
                        with studio.lock:
                            require(not studio.busy(),'Wait for the active job before editing assets or project')
                            result=self.mutate(action,path,data)
                    elif action=='validate':result=validate_any(read_any(path),path.parent,final=data.get('final') is True)
                    elif action=='cinema-audit':
                        from .cinema_pipeline import layout_audit
                        result=layout_audit(path,data.get('profile','vertical'))
                    elif action=='plan':
                        result=plan_project(path);atomic_json(path.parent/'outputs/plan.json',result)
                    elif action=='voice-prepare':
                        from .core import local_asset
                        from .voice_lab import prepare_voice
                        names=data.get('assets',[]);require(isinstance(names,list) and 1<=len(names)<=12,'Select 1–12 audio recordings')
                        files=[local_asset(path.parent,n) for n in names]
                        require(all(f.suffix.lower() in ['.ogg','.wav','.mp3','.m4a','.flac'] for f in files),'Select audio recordings')
                        folder=path.parent/'voice-profiles'/('voice-'+secrets.token_hex(4))
                        def make_profile(progress):
                            value=prepare_voice(files,folder,data.get('name','Voz de referencia'),progress)
                            return {'voice_profile':str((folder/'voice-profile.json').relative_to(path.parent)),
                                    'reference_audio':str((folder/'reference.wav').relative_to(studio.root)),
                                    'samples':len(value['samples']),'requires_listening_review':True}
                        result=studio.job(action,make_profile)
                    elif action=='voice-synthesize':
                        from .core import local_asset
                        from .voice_local import synthesize_local,runtime_settings
                        from .voice_languages import speech_plan
                        profile=local_asset(path.parent,data.get('profile',''));runtime_settings()
                        script=data.get('text','');language=data.get('language','Spanish');segments=data.get('segments')
                        speech_plan(script,language,segments)
                        out=path.parent/'assets'/('voice-'+secrets.token_hex(4)+'.wav')
                        def make_voice(progress):
                            progress(.05);episode_seconds=read_any(path)['duration']
                            use_rhythm=data.get('natural_rhythm',True) and language not in ['Chinese','Japanese','Korean'] and not segments
                            value=synthesize_local(profile,script,out,target_seconds=None,language=language,segments=segments,
                                rhythm={'episode_seconds':episode_seconds,'target_wpm':float(data.get('wpm',175))} if use_rhythm and episode_seconds>=3 else None)
                            progress(.95);m=read_any(path)
                            attached=(value['script_comparison']['rate']<=.25 and bool(value['subtitles']) and
                                      value['seconds']<=m['duration'] and value['subtitles'][-1]['end']<=m['duration'])
                            if attached:
                                m.update(voice=str(out.relative_to(path.parent)),subtitles=value['subtitles'],caption_audio_sha256=sha256(out),
                                         voice_synthesis={'report':str(out.with_suffix('.voice.json').relative_to(path.parent)),'human_approval':False})
                                if m.get('schema')==SCHEMA:
                                    m['assets'][m['voice']]={'sha256':sha256(out),'origin':'local reference-conditioned synthesis','rights':'workspace voice; review before sharing','privacy':'private'}
                                validate_any(m,path.parent);atomic_json(path,m)
                            return {'audio':str(out.relative_to(studio.root)),'report':value,'attached':attached,
                                    'requires_listening_review':True,'reason':None if attached else 'Check script, duration and ASR before attaching'}
                        result=studio.job(action,make_voice)
                    elif action=='storyboard':
                        def make_board(progress):
                            if read_any(path).get('schema')==SCHEMA:
                                from .cinema_pipeline import cinema_storyboard
                                out=cinema_storyboard(path,path.parent/'outputs/storyboard.jpg',data.get('profile','vertical'))
                            else:out=storyboard(path,path.parent/'outputs/storyboard.jpg')
                            return {'media':str(out.relative_to(studio.root))}
                        result=studio.job(action,make_board)
                    elif action=='render':
                        profile=data.get('profile','proxy');require(profile in ['proxy','vertical','landscape-proxy','horizontal'],'Invalid profile')
                        def make_video(progress):
                            out=path.parent/f'outputs/video-{profile}.mp4'
                            if read_any(path).get('schema')==SCHEMA:
                                from .cinema_pipeline import render_cinema
                                report=render_cinema(path,out,profile,cc=data.get('cc',True),final=data.get('final') is True,progress=progress)
                            else:report=render_project(path,out,profile,final=data.get('final') is True,progress=progress)
                            return {'media':str(out.relative_to(studio.root)),'report':report}
                        result=studio.job(action,make_video)
                    else:raise ValidationError('Unknown action')
                self.reply(result)
            except (ValidationError,ValueError,KeyError,OSError,TypeError) as e:self.reply({'error':str(e)},400)
        def mutate(self,action,path,data):
            if action=='phone-screen':
                from .core import local_asset
                from PIL import Image
                m=read_any(path);require(m.get('schema')==SCHEMA,'Select a cinema project')
                name=data.get('asset');screen=local_asset(path.parent,name)
                with Image.open(screen) as im:im.verify()
                m['phone_screen']=name;m['assets'][name]={'sha256':sha256(screen),'origin':'user-supplied original screenshot','rights':'supplied for production; review before sharing','privacy':'private'}
                validate_cinema(m,path.parent);atomic_json(path,m);return {'phone_screen':name,'sha256':sha256(screen)}
            if action=='save':
                m=data.get('project');validate_any(m,path.parent);atomic_json(path,m)
                return {'saved':True}
            if action=='attach-voice':
                from .core import local_asset
                m=read_any(path);name=data.get('asset');audio=local_asset(path.parent,name)
                require(audio.suffix.lower() in ['.wav','.mp3','.m4a','.flac','.ogg'],'Choose an audio recording')
                m['voice']=name;m['subtitles']=data.get('subtitles',[])
                m['caption_audio_sha256']=sha256(audio)
                if m.get('schema')==SCHEMA:m['assets'][name]={'sha256':sha256(audio),'origin':'imported audio','rights':'workspace recording; review before sharing','privacy':'private'}
                validate_any(m,path.parent);atomic_json(path,m)
                return {'attached':True,'caption_alignment_requires_review':True}
            name=data.get('name','');require(isinstance(name,str) and name==Path(name).name and name not in ['.','..'],'Invalid filename')
            require(Path(name).suffix.lower() in ['.png','.jpg','.jpeg','.webp','.mp4','.mov','.wav','.mp3','.m4a','.flac','.ogg'],'Unsupported asset extension')
            target=confined(path.parent,'assets/'+name);require(not target.exists(),'Asset already exists; use a new name')
            raw=base64.b64decode(data.get('base64',''),validate=True);require(0<len(raw)<=24*1024*1024,'Asset too large or empty')
            target.parent.mkdir(parents=True,exist_ok=True)
            try:
                target.write_bytes(raw)
                if target.suffix.lower() in ['.png','.jpg','.jpeg','.webp']:
                    from PIL import Image
                    with Image.open(target) as im:im.verify()
                else:probe(target)
            except Exception:target.unlink(missing_ok=True);raise
            return {'asset':'assets/'+name,'sha256':sha256(target),'rights':'Record origin and license in project.assets before final export'}
    return Handler


def serve(root='projects',port=8765):
    studio=Studio(root);httpd=ThreadingHTTPServer(('127.0.0.1',port),handler(studio))
    print(f'GoToGym Quantum Coach Studio → http://127.0.0.1:{httpd.server_port}',flush=True)
    print(f'Projects: {studio.root}\nCtrl+C to stop. Local access only.',flush=True)
    try:httpd.serve_forever()
    except KeyboardInterrupt:pass
    finally:httpd.server_close();studio.worker.shutdown(wait=True,cancel_futures=True)
