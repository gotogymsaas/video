"""Conservative stem-energy planning, distinct from perceptual intelligibility."""
import numpy as np
from pathlib import Path
from .quality import select
from .voice_lab import decode
from .audio import mix_audio
from .core import require,atomic_json

def dialogue_margin(voice,music,gain,sample_rate=16000):
    size=round(.04*sample_rate);frames=min(len(voice),len(music))//size;require(frames>0,'Stems too short')
    v=np.sqrt(np.mean(np.asarray(voice[:frames*size]).reshape(frames,size)**2,axis=1));m=np.sqrt(np.mean(np.asarray(music[:frames*size]).reshape(frames,size)**2,axis=1))*gain
    active=v>max(.006,float(v.max())*.04);require(active.any(),'No voice activity');margin=20*np.log10((v[active]+1e-9)/(m[active]+1e-9))
    return {'median_db':float(np.median(margin)),'p10_db':float(np.quantile(margin,.1)),'active_frames':int(active.sum()),'scope':'mono stem RMS before ducking; excludes ambience; no perceptual prediction'}

def mix_story(output,seconds,voice,music,ambience=None):
    v=decode(voice,16000);m=decode(music,16000);candidates=[]
    for gain in [.08,.10,.14,.18,.22]:
        metric=dialogue_margin(v,m,gain);candidates.append({'music_gain':gain,'margin':metric,'loss':((metric['median_db']-16)/16)**2,'feasible':metric['median_db']>=8})
    decision=select(candidates);r=mix_audio(output,seconds,voice,music,ambience,profile={'gains':{'music':decision['selected']['music_gain']},'release_ms':450})
    r.update(balance_decision=decision,target_margin_db=16);atomic_json(Path(output).with_suffix('.audio.json'),r);return r
