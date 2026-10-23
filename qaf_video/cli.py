"""Command-line interface. All core production commands work without cloud keys."""
from __future__ import annotations
import argparse, asyncio, importlib.util, json, shutil, sys
from pathlib import Path
from .core import ValidationError, load, validate, atomic_json, run


def parser():
    p=argparse.ArgumentParser(prog='qaf-video',description='GoToGym Quantum Coach · audiovisual studio')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Check local dependencies and optional integrations')
    init=sub.add_parser('init',help='Create a portable 60-second conceptual demonstration')
    init.add_argument('folder');init.add_argument('--seconds',type=float,default=60);init.add_argument('--fps',type=int,default=30);init.add_argument('--samples',type=int,default=12)
    for name in ['validate','plan','storyboard','render']:
        c=sub.add_parser(name);c.add_argument('project',type=Path)
        if name in ['validate','render']:c.add_argument('--final',action='store_true')
        if name in ['plan','storyboard','render']:c.add_argument('--out',type=Path,required=True)
        if name in ['storyboard','render']:c.add_argument('--profile',choices=['proxy','vertical','landscape-proxy','horizontal'],default='proxy')
        if name=='plan':c.add_argument('--budget',type=int)
    c=sub.add_parser('native-render');c.add_argument('--out',type=Path,required=True)
    c.add_argument('--width',type=int,default=640);c.add_argument('--height',type=int,default=360)
    c.add_argument('--samples',type=int,default=16);c.add_argument('--seed',type=int,default=22);c.add_argument('--bounces',type=int,default=5)
    c=sub.add_parser('blender-render');c.add_argument('--out',type=Path,required=True)
    c.add_argument('--width',type=int,default=1920);c.add_argument('--height',type=int,default=1080);c.add_argument('--samples',type=int,default=64)
    c=sub.add_parser('mix');c.add_argument('--out',type=Path,required=True);c.add_argument('--seconds',type=float,required=True)
    for name in ['voice','music','ambience','effects']:c.add_argument('--'+name,type=Path)
    c=sub.add_parser('voice',help='Optional online synthesis; Colombian locale, accent subject to audition')
    c.add_argument('--list',action='store_true');c.add_argument('--locale',default='es-CO')
    c.add_argument('--text-file',type=Path);c.add_argument('--out',type=Path)
    c.add_argument('--voice',default='es-CO-SalomeNeural');c.add_argument('--rate',default='+0%');c.add_argument('--pitch',default='+0Hz')
    c=sub.add_parser('voice-prepare',help='Analyze and prepare local voice references (WAV/OGG/MP3)')
    c.add_argument('files',type=Path,nargs='+');c.add_argument('--out',type=Path,required=True)
    c.add_argument('--name',default='Voz de referencia · Barranquilla')
    c=sub.add_parser('voice-clone',help='Generate a new script with a local reference-conditioned model')
    c.add_argument('--profile',type=Path,required=True)
    source=c.add_mutually_exclusive_group(required=True)
    source.add_argument('--text-file',type=Path);source.add_argument('--segments-file',type=Path,help='JSON array of text/language phrases')
    from .voice_languages import normalize_language,LANGUAGES
    c.add_argument('--language',type=normalize_language,choices=list(LANGUAGES),default='Spanish',help='Target language name or ISO code; reference language remains independent')
    c.add_argument('--out',type=Path,required=True);c.add_argument('--python',type=Path)
    c.add_argument('--tts-model',type=Path);c.add_argument('--asr-model',type=Path)
    c.add_argument('--precision',choices=['float32','bfloat16','float16'],help='Explicit inference precision; float16 is not supported on CPU')
    c.add_argument('--device',choices=['cpu','cuda:0','mps'],default='cpu');c.add_argument('--seed',type=int,default=22)
    c.add_argument('--seconds',type=float,help='Fit within bounded tempo and real pauses; reject unsuitable script lengths')
    c=sub.add_parser('attach-voice',help='Attach recording and real caption intervals to a project')
    c.add_argument('project',type=Path);c.add_argument('--asset',required=True)
    c.add_argument('--captions',type=Path,required=True,help='JSON list, or .voice.json containing subtitles')
    c=sub.add_parser('benchmark');c.add_argument('--out',type=Path)
    c=sub.add_parser('build',help='Execute a confined built-in production DAG')
    c.add_argument('workflow',type=Path);c.add_argument('--workspace',type=Path,required=True)
    c=sub.add_parser('serve');c.add_argument('--workspace',default='projects');c.add_argument('--port',type=int,default=8765)
    c=sub.add_parser('voice-rhythm',help='Continuous speech without inserted sentence gaps')
    c.add_argument('source',type=Path);c.add_argument('--text-file',type=Path,required=True);c.add_argument('--out',type=Path,required=True)
    c.add_argument('--wpm',type=float,default=175);c.add_argument('--seconds',type=float,default=60)
    for name in ['cinema-audit','cinema-storyboard','cinema-render']:
        c=sub.add_parser(name);c.add_argument('project',type=Path);c.add_argument('--profile',choices=['proxy','vertical','landscape-proxy','horizontal'],default='vertical')
        if name!='cinema-audit':c.add_argument('--out',type=Path,required=True)
        if name=='cinema-render':c.add_argument('--no-cc',action='store_true');c.add_argument('--final',action='store_true')
    return p


def main(argv=None):
    p=parser();a=p.parse_args(argv)
    try:
        if a.command=='doctor':
            from .voice_local import runtime_settings
            try:
                runtime_settings();reference_voice={'configured':True,'processing':'local, offline worker'}
            except ValidationError as error:reference_voice={'configured':False,'setup':str(error)}
            result={'python':sys.version.split()[0],'ffmpeg':shutil.which('ffmpeg'),
                    'ffprobe':shutil.which('ffprobe'),'blender':shutil.which('blender'),
                    'edge_tts_installed':bool(importlib.util.find_spec('edge_tts')),'reference_voice':reference_voice,
                    'native_renderer':'CPU reference available','cloud_video_generation':'not integrated',
                    'voice_accent':'Barranquilla requires an audition; not certified by locale',
                    'core_ready':bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))}
        elif a.command=='init':
            from .demo import create_project
            result={'project':str(create_project(a.folder,a.seconds,a.fps,a.samples))}
        elif a.command=='validate':result=validate(load(a.project),a.project.resolve().parent,a.final)
        elif a.command=='plan':
            from .planning import plan_project
            result=plan_project(a.project,a.budget);atomic_json(a.out,result)
        elif a.command=='storyboard':
            from .pipeline import storyboard
            result={'storyboard':str(storyboard(a.project,a.out,a.profile))}
        elif a.command=='render':
            from .pipeline import render_project
            result=render_project(a.project,a.out,a.profile,a.final,
                    progress=lambda x:print(f'\rRender {x:.0%}',end='',file=sys.stderr,flush=True))
            print(file=sys.stderr)
        elif a.command=='native-render':
            from .render.pathtrace import save
            result=save(a.out,width=a.width,height=a.height,samples=a.samples,seed=a.seed,bounces=a.bounces)
        elif a.command=='blender-render':
            from .render.blender_adapter import render
            result={'image':str(render(a.out,width=a.width,height=a.height,samples=a.samples))}
        elif a.command=='mix':
            from .audio import mix_audio
            result=mix_audio(a.out,a.seconds,a.voice,a.music,a.ambience,a.effects)
        elif a.command=='voice':
            from .voice import available_voices,synthesize
            if a.list:result=asyncio.run(available_voices(a.locale))
            else:
                if not a.text_file or not a.out:p.error('voice requires --text-file and --out (or --list)')
                result=asyncio.run(synthesize(a.text_file.read_text(encoding='utf-8'),a.out,a.voice,a.rate,a.pitch))
        elif a.command=='voice-prepare':
            from .voice_lab import prepare_voice
            profile=prepare_voice(a.files,a.out,a.name)
            result={'profile':str(a.out/'voice-profile.json'),'samples':len(profile['samples']),
                    'reference_seconds':profile['reference_selection']['end']-profile['reference_selection']['start'],
                    'requires_listening_review':True}
        elif a.command=='voice-clone':
            from .voice_local import synthesize_local
            text=a.text_file.read_text(encoding='utf-8') if a.text_file else ''
            segments=json.loads(a.segments_file.read_text(encoding='utf-8')) if a.segments_file else None
            result=synthesize_local(a.profile,text,a.out,a.python,a.tts_model,a.asr_model,a.device,a.seed,a.seconds,
                                    language=a.language,segments=segments,precision=a.precision)
        elif a.command=='attach-voice':
            from .core import local_asset,sha256
            m=load(a.project);audio=local_asset(a.project.resolve().parent,a.asset)
            captions=json.loads(a.captions.read_text(encoding='utf-8'))
            m.update(voice=a.asset,subtitles=captions.get('subtitles',[]) if isinstance(captions,dict) else captions,
                     caption_audio_sha256=sha256(audio))
            validate(m,a.project.resolve().parent);atomic_json(a.project,m)
            from .voice import write_captions
            write_captions(a.project.resolve().parent/'subtitles',m['subtitles'])
            result={'attached':a.asset,'alignment_requires_human_review':True}
        elif a.command=='benchmark':
            from .planning import benchmark
            result=benchmark()
            if a.out:atomic_json(a.out,result)
        elif a.command=='build':
            from .graph import build
            result=build(a.workflow,a.workspace)
        elif a.command=='voice-rhythm':
            from .voice_rhythm import natural_voice
            result=natural_voice(a.source,a.out,a.text_file.read_text(encoding='utf-8'),a.seconds,a.wpm)
        elif a.command=='cinema-audit':
            from .cinema_pipeline import layout_audit
            result=layout_audit(a.project,a.profile)
        elif a.command=='cinema-storyboard':
            from .cinema_pipeline import cinema_storyboard
            result={'storyboard':str(cinema_storyboard(a.project,a.out,a.profile))}
        elif a.command=='cinema-render':
            from .cinema_pipeline import render_cinema
            result=render_cinema(a.project,a.out,a.profile,not a.no_cc,a.final,progress=lambda x:print(f'\rCine {x:.0%}',end='',file=sys.stderr,flush=True))
            print(file=sys.stderr)
        elif a.command=='serve':
            from .server import serve
            serve(a.workspace,a.port);return 0
        else:p.error('Unknown command')
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False));return 0
    except (ValidationError,ValueError,OSError,RuntimeError) as e:
        print(f'ERROR: {e}',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
