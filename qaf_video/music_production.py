"""Transactional bridge from Music Lab to a validated cinema project."""
from __future__ import annotations
import copy,json,os,shutil,tempfile,secrets
from pathlib import Path
from .core import require,sha256,atomic_json,local_asset
from .cinema_project import load_cinema,validate_cinema
from .music_research.synthesis import render,PRESETS
from .music_research.arrangement import align
from .music_research.mixing import mix

def produce_music(project,preset='run_club',seed=22,cues=None,progress=None):
    path=Path(project).resolve();before=path.read_bytes();m,_=load_cinema(path);base=path.parent
    selection=None
    if m.get('music_brief'):
        from .music_research.preference import target,choose
        brief=m['music_brief'];desired=target(brief['references'],brief['as_of'])
        selection={'target':desired,'decision':choose(brief['candidates'],desired['features'])}
        preset=selection['decision']['selected']['id']
    require(preset in PRESETS,'Unknown musical direction')
    require(isinstance(seed,int) and not isinstance(seed,bool) and 0<=seed<2**32,'Invalid seed')
    require(.5<=m['duration']<=120,'Music sketches support 0.5–120 seconds')
    voice=local_asset(base,m.get('voice',''));require(voice.suffix.lower()=='.wav','Attach a WAV narration first')
    cues=cues if cues is not None else [m['duration']*v for v in (.22,.48,.83)]
    require(isinstance(cues,list) and len(cues)==3,'Three music cues required')
    bpm=PRESETS[preset]['bpm'];plan=align(cues,m['duration'],bpm,tolerance=.28)
    root=base/'assets/music'
    require(root.resolve().is_relative_to(base),'Music folder escapes project')
    root.mkdir(parents=True,exist_ok=True)
    name=preset+'-'+secrets.token_hex(5);target=root/name;installed=False
    try:
        with tempfile.TemporaryDirectory(prefix='.score_',dir=root) as tmp:
            tmp=Path(tmp)
            result=render(tmp,preset,m['duration'],seed=seed,cues=plan['aligned_cues'])
            atomic_json(tmp/'plan.json',plan)
            if selection:atomic_json(tmp/'selection.json',selection)
            if progress:progress(.35)
            measured=mix(tmp/'mix.wav',voice,tmp/'preview.wav',m['duration'],bpm)
            if progress:progress(.85)
            os.replace(tmp,target);installed=True
        updated=copy.deepcopy(m)
        for p in target.iterdir():
            if not p.is_file():continue
            relative=p.relative_to(base).as_posix()
            updated.setdefault('assets',{})[relative]={'sha256':sha256(p),'origin':'GoToGym original DSP and measured mix',
                'rights':'generated from repository code; music/IP and editorial review pending',
                'privacy':'private' if p.name.startswith('mix') else 'public'}
        rel=target.relative_to(base).as_posix()
        updated['music']=rel+'/preview.wav';updated['mix']=rel+'/mix.wav'
        updated['music_production']={'version':'qaf_music_production_v1','preset':preset,'seed':seed,'bpm':bpm,
             'plan':rel+'/plan.json','manifest':rel+'/manifest.json','voice_sha256':sha256(voice),
             'human_approved':False,'selection':rel+'/selection.json' if selection else None,'scope':'original DSP sketch with measured sidechain mix; not a trained neural model'}
        updated.setdefault('reviews',{})['audio']={'approved':False,'reviewer':'','at':''}
        validate_cinema(updated,base)
        require(path.read_bytes()==before,'Project changed during composition; retry after reloading')
        atomic_json(path,updated)
    except BaseException:
        if installed:shutil.rmtree(target,ignore_errors=True)
        raise
    if progress:progress(1)
    return {'music':updated['music'],'mix':updated['mix'],'preset':preset,'plan':plan,
            'measurement':measured['output_measurement'],'stems':list(result['outputs']),
            'project_updated':True,'requires_listening_review':True}
