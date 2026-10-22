"""Atomic render jobs, provenance, delivery checks and repeatable storyboards."""
from __future__ import annotations
import json,os,platform,subprocess,tempfile,time,shutil
from pathlib import Path
from PIL import Image
from . import __version__
from .core import load,validate,local_asset,sha256,digest,atomic_json,PROFILES,probe,run,require,ValidationError
from .render.compositor import Movie


def delivery_check(path,fps,seconds,size,audio_required=False):
    info=probe(path,True);v=next(s for s in info['streams'] if s['codec_type']=='video');audio=next((s for s in info['streams'] if s['codec_type']=='audio'),{})
    decode=run(['ffmpeg','-v','error','-i',path,'-f','null','-'])
    checks={'frames':int(v['nb_read_frames'])==round(fps*seconds),'duration':abs(float(info['format']['duration'])-seconds)<=.06,'size':(v['width'],v['height'])==tuple(size),'fps':abs(eval_fraction(v['avg_frame_rate'])-fps)<1e-6,'codec':v['codec_name']=='h264','decode':not decode.stderr.strip(),'audio':not audio_required or audio.get('codec_name')=='aac'}
    return {'technical_passed':all(checks.values()),'checks':checks,'audio_present':bool(audio),'editorial_quality':'requires human playback review'}
def eval_fraction(s):
    a,b=s.split('/');return float(a)/float(b)

def storyboard(project,output,profile='proxy'):
    path=Path(project).resolve();m=load(path);m['_storyboard_static']=True;movie=Movie(m,path.parent,profile);thumbs=[]
    try:
        for shot in m['shots']:
            im=movie.frame(shot,shot['start']+min(.75,(shot['end']-shot['start'])/2));im.thumbnail((270,480));thumbs.append(im);movie.close_decoder();movie.current=None
    finally:movie.close_decoder()
    width=max(im.width for im in thumbs);height=max(im.height for im in thumbs)
    sheet=Image.new('RGB',(width*3,height*((len(thumbs)+2)//3)),'#101012')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%3)*width,(i//3)*height))
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output);return output


def render_project(project,output,profile='proxy',final=False,progress=None):
    started=time.perf_counter();p=Path(project).resolve();m=load(p);validate(m,p.parent,final)
    require(profile in PROFILES,'Unknown output profile')
    if final:require(profile not in ['proxy','landscape-proxy'] and m.get('color_pipeline')=='srgb_linear_composite','Final needs full resolution and linear composition')
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    dependencies={}
    for s in m['shots']:
        if s.get('asset'):dependencies[s['asset']]=sha256(local_asset(p.parent,s['asset']))
    for key in ['voice','music','ambience','effects','logo']:
        if m.get(key):dependencies[m[key]]=sha256(local_asset(p.parent,m[key]))
    package=Path(__file__).parent
    source_hash=digest({str(f.relative_to(package)):sha256(f) for f in package.rglob('*') if f.is_file() and f.suffix in ['.py','.json','.ttf']})
    key=digest({'project':m,'assets':dependencies,'profile':profile,'code':source_hash,'version':__version__})
    sidecar=output.with_suffix('.report.json')
    if output.exists() and sidecar.exists():
        report=json.loads(sidecar.read_text())
        if report.get('render_key')==key and report.get('output_sha256')==sha256(output):
            if progress:progress(1)
            return {**report,'cache_hit':True}
    w,h=PROFILES[profile];fps=m['fps'];frames=round(m['duration']*fps);movie=Movie(m,p.parent,profile)
    with tempfile.TemporaryDirectory(prefix='.render_',dir=output.parent) as tmp:
        tmp=Path(tmp);silent=tmp/'picture.mp4'
        with (tmp/'encoder.log').open('w+') as log:
            process=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','pipe:0','-an','-vf','scale=out_color_matrix=bt709:out_range=tv','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1','-color_range','tv','-movflags','+faststart',str(silent)],stdin=subprocess.PIPE,stderr=log)
            try:
                for s in m['shots']:
                    for f in range(round(s['start']*fps),round(s['end']*fps)):
                        process.stdin.write(movie.frame(s,f/fps).tobytes())
                        if progress and f%fps==0:progress(.85*f/frames)
                process.stdin.close();require(process.wait(timeout=120)==0,'Video encoder failed')
            finally:
                movie.close_decoder()
                if process.poll() is None:process.terminate();process.wait(timeout=10)
        result=tmp/'delivery.mp4';audio_report=None
        if any(m.get(k) for k in ['voice','music','ambience','effects']):
            from .audio import mix_audio
            stems={k:local_asset(p.parent,m[k]) for k in ['voice','music','ambience','effects'] if m.get(k)}
            audio=tmp/'mix.wav';audio_report=mix_audio(audio,seconds=m['duration'],**stems)
        recovered_errors=[]
        # Keep the verified picture and mix until the container is decoded.
        # A single fresh mux may recover a transient incomplete-container write.
        for attempt in [1,2]:
            try:
                if audio_report:
                    run(['ffmpeg','-y','-v','error','-i',silent,'-i',audio,'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(m['duration']),'-movflags','+faststart',result])
                else:shutil.copyfile(silent,result)
                with result.open('rb') as f:os.fsync(f.fileno())
                check=delivery_check(result,fps,m['duration'],(w,h),bool(audio_report));require(check['technical_passed'],'Delivery technical checks failed')
                if audio_report:
                    from .audio import measure
                    encoded=measure(result);audio_report['encoded_measurement']=encoded
                    require(abs(float(encoded['input_i'])+14)<=1.5 and float(encoded['input_tp'])<=-.8,'Encoded audio outside configured loudness/peak tolerance')
                break
            except ValidationError as error:
                if attempt==2:raise
                recovered_errors.append(str(error))
        os.replace(result,output)
    report={'version':__version__,'render_key':key,'cache_hit':False,'output_sha256':sha256(output),'assets_sha256':dependencies,'fps':fps,'frames':frames,'seconds':m['duration'],'resolution':[w,h],'profile':profile,'color_pipeline':m.get('color_pipeline','srgb_preview'),'state':'rendered_pending_playback_review','mode':m['mode'],'final_documentary_checks':final,'reviews':m.get('reviews',{}),'technical':check,'audio':audio_report,'delivery_attempts':attempt,'recovered_errors':recovered_errors,'wall_seconds':time.perf_counter()-started,'environment':{'python':platform.python_version(),'pillow':Image.__version__,'ffmpeg':run(['ffmpeg','-version']).stdout.splitlines()[0]}}
    atomic_json(sidecar,report)
    if progress:progress(1)
    return report
