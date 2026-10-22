"""Continuous pitch-preserving speech; no padding to fill a film."""
import math,re,tempfile
from pathlib import Path
import numpy as np
from .core import require,run,sha256,atomic_json
from .voice_lab import decode,normalize_voice
from .quality import select

def silence_metrics(samples,sample_rate=48000,threshold_db=-42,min_gap=.12):
    x=np.asarray(samples,dtype=float);require(x.ndim==1 and len(x)>0 and np.isfinite(x).all(),'Invalid mono signal')
    size=max(1,round(.02*sample_rate));n=len(x)//size
    rms=np.sqrt(np.mean(x[:n*size].reshape(n,size)**2,axis=1)) if n else np.array([])
    start=None;runs=[];duration=len(x)/sample_rate
    for i,quiet in enumerate(np.append(rms<10**(threshold_db/20),False)):
        if quiet and start is None:start=i
        elif not quiet and start is not None:
            if (i-start)*size/sample_rate>=min_gap:runs.append({'start':start*size/sample_rate,'end':i*size/sample_rate})
            start=None
    internal=[r for r in runs if r['start']>.05 and r['end']<duration-.05]
    return {'seconds':duration,'threshold_dbfs':threshold_db,'frame_seconds':size/sample_rate,'internal_gaps':internal,
            'internal_gaps_over_650ms':sum(r['end']-r['start']>.65 for r in internal),
            'max_internal_gap':max((r['end']-r['start'] for r in internal),default=0.),
            'note':'Energy proxy; not a linguistic pause detector.'}

def natural_voice(source,output,text,episode_seconds=60,target_wpm=175,lead_seconds=.6):
    require(80<=target_wpm<=240 and math.isfinite(target_wpm),'Target rate must be 80–240 WPM')
    require(0<=lead_seconds<=3 and 3<=episode_seconds<=600,'Invalid episode budget')
    words=len(re.findall(r'\b\w+\b',text));require(words>0,'Script required')
    source=Path(source).resolve();output=Path(output).resolve();require(source!=output,'Preserve source')
    x=decode(source,48000);original=len(x)/48000;wpm=60*words/original
    preferred=float(np.clip(target_wpm/wpm,.9,1.08));rates=sorted(set([.9,.92,.94,.96,.98,1.,1.02,1.04,1.06,1.08,preferred]))
    candidates=[{'tempo':r,'wpm':wpm*r,'seconds':original/r+lead_seconds,
                 'loss':((wpm*r-target_wpm)/target_wpm)**2+.002*math.log(r)**2,
                 'feasible':original/r+lead_seconds<=episode_seconds-.4} for r in rates]
    decision=select(candidates);rate=decision['selected']['tempo'];output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.rhythm_',dir=output.parent) as folder:
        raw=Path(folder)/'continuous.wav'
        run(['ffmpeg','-y','-v','error','-i',source,'-af',f'atempo={rate},adelay={round(lead_seconds*1000)}:all=1','-ar','48000','-ac','1','-c:a','pcm_s24le',raw])
        loudness=normalize_voice(raw,output)
    y=decode(output,48000)
    r={'schema':'qaf_voice_rhythm_v1','tempo_factor':rate,'source_wpm':wpm,'target_wpm':target_wpm,'estimated_spoken_wpm':wpm*rate,
       'original_seconds':original,'target_seconds':len(y)/48000,'episode_seconds':episode_seconds,'lead_seconds':lead_seconds,
       'pause_insertions':[],'added_pauses':0,'pitch_shift':False,'closing_hold_seconds':max(0,episode_seconds-len(y)/48000),
       'before':silence_metrics(x),'after':silence_metrics(y),'source_sha256':sha256(source),'output_sha256':sha256(output),
       'decision':decision,'loudness':loudness,'listening_review':'pending; WPM and energy gaps do not certify naturalness'}
    atomic_json(output.with_suffix('.rhythm.json'),r);return r
