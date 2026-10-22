"""Single-encode cinematic jobs with atomic publication and verified caching."""
import json,os,platform,subprocess,tempfile,time
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from . import __version__
from .core import PROFILES,require,local_asset,sha256,digest,atomic_json,run
from .cinema_project import load_cinema,render_key
from .cinema import Film
from .pipeline import delivery_check
from .audio import measure

def layout_audit(project,profile='vertical'):
    path=Path(project).resolve();m,_=load_cinema(path);film=Film(m,path.parent,profile);records=[]
    for i,s in enumerate(m['shots']):
        film.frame((s['start']+s['end'])/2,True);bad=[b for b in film.layout_boxes if not b['inside_canvas']]
        records.append({'shot':i+1,'layout':s['layout'],'text_count':len(film.layout_boxes),'clipped_text':bad,'passed':not bad})
    return {'profile':profile,'shots':records,'passed':all(s['passed'] for s in records),'phone':film.phone_reports,
            'scope':'text canvas bounds at shot midpoints; aesthetic/overlap review remains human'}

def cinema_storyboard(project,output,profile='vertical'):
    path=Path(project).resolve();m,_=load_cinema(path);film=Film(m,path.parent,profile);tw,th=(270,480) if film.vertical else (480,270)
    sheet=Image.new('RGB',(tw*3,(th+42)*((len(m['shots'])+2)//3)),'#101012');d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype(str(local_asset(path.parent,m['fonts']['regular'])),14)
    for i,s in enumerate(m['shots']):
        im=film.frame((s['start']+s['end'])/2,True);im.thumbnail((tw,th));x=i%3*tw;y=i//3*(th+42);sheet.paste(im,(x,y))
        d.text((x+5,y+th+5),f"{s['start']:04.1f}–{s['end']:04.1f} / {s['layout']}",font=font,fill='white')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output);return output

def render_cinema(project,output,profile='vertical',cc=True,final=False,progress=None):
    started=time.perf_counter();path=Path(project).resolve();m,validation=load_cinema(path,final)
    require(profile in PROFILES,'Invalid profile');output=Path(output).resolve();require(output.suffix=='.mp4','Output must be MP4');output.parent.mkdir(parents=True,exist_ok=True)
    audit=layout_audit(path,profile);require(audit['passed'],'Clipped typography; correct layout')
    package=Path(__file__).parent;code=digest({str(p.relative_to(package)):sha256(p) for p in package.rglob('*.py')})
    environment={'python':platform.python_version(),'pillow':Image.__version__,'ffmpeg':run(['ffmpeg','-version']).stdout.splitlines()[0]}
    key=render_key(m,validation['dependencies'],profile,cc,code,environment);sidecar=output.with_suffix('.report.json')
    if output.is_file() and sidecar.is_file():
        r=json.loads(sidecar.read_text())
        if r.get('render_key')==key and r.get('output_sha256')==sha256(output):
            if progress:progress(1)
            return {**r,'cache_hit':True}
    film=Film(m,path.parent,profile);frames=round(m['duration']*m['fps']);w,h=film.w,film.h
    with tempfile.TemporaryDirectory(prefix='.cinema_',dir=output.parent) as temp:
        tmp=Path(temp);result=tmp/'delivery.mp4';audio=m.get('mix')
        args=['ffmpeg','-y','-nostdin','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(m['fps']),'-i','pipe:0']
        if audio:args+=['-i',str(local_asset(path.parent,audio))]
        args+=['-map','0:v'];args+=['-map','1:a','-c:a','aac','-b:a','192k','-ar','48000','-ac','2'] if audio else ['-an']
        args+=['-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p','-c:v','libx264','-preset','fast','-crf','19','-threads','4',
               '-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1','-color_range','tv','-t',str(m['duration']),'-movflags','+faststart',str(result)]
        with (tmp/'encoder.log').open('w+') as log:
            process=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=log)
            try:
                for i in range(frames):
                    process.stdin.write(film.frame(i/m['fps'],cc).tobytes())
                    if progress and i%m['fps']==0:progress(.9*i/frames)
                process.stdin.close();status=process.wait(timeout=120)
                if status:log.seek(0);raise RuntimeError('Encoder failed: '+log.read()[-1800:])
            finally:
                if process.poll() is None:process.terminate();process.wait(timeout=10)
        check=delivery_check(result,m['fps'],m['duration'],(w,h),bool(audio));require(check['technical_passed'],'Cinematic delivery failed')
        encoded=measure(result) if audio else None
        if encoded:require(abs(float(encoded['input_i'])+14)<=1 and float(encoded['input_tp'])<=-1.,'Encoded audio outside profile')
        os.replace(result,output)
    r={'schema':'qaf_cinema_render_v1','version':__version__,'render_key':key,'cache_hit':False,'output_sha256':sha256(output),'assets_sha256':validation['dependencies'],
       'seconds':m['duration'],'frames':frames,'fps':m['fps'],'profile':profile,'resolution':[w,h],'captions_burned':cc,'video_encode_generations':1,
       'color_pipeline':'SDR sRGB graphics to limited-range BT.709 matrix','technical':check,'audio_encoded':encoded,'layout':audit,'environment':environment,
       'state':'rendered_pending_human_playback','final_documentary_checks':final,'treatment':'photographic cinematic animatic','wall_seconds':time.perf_counter()-started}
    atomic_json(sidecar,r)
    if progress:progress(1)
    return r
