"""Bounded pitch-preserving tempo and pauses for a measured episode duration."""
from pathlib import Path
import math,tempfile
import numpy as np
from .core import require,run
from .voice_lab import decode,write_wav,normalize_voice


def fit_voice(source,output,seconds,words):
    require(isinstance(seconds,(float,int)) and math.isfinite(seconds) and 3<=seconds<=600,'Invalid target duration')
    x=decode(source,48000);original=len(x)/48000
    # A short script cannot be turned into a minute by filling long silence.
    rate=float(np.clip(original/max(1,seconds-3),.8,1.08))
    require(original/rate<=seconds-.1,'Voice is too long; shorten the script rather than cutting speech')
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.voice_time_',dir=output.parent) as tmp:
        tmp=Path(tmp);tempo=tmp/'tempo.wav'
        run(['ffmpeg','-y','-v','error','-i',source,'-af',f'atempo={rate}','-ar','48000','-ac','1','-c:a','pcm_s24le',tempo])
        y=decode(tempo,48000);remaining=seconds-len(y)/48000-.15
        # Reserve at most three seconds for the closing card.
        extend=max(0.,remaining-3.)
        pauses=[]
        for left,right in zip(words,words[1:]):
            a,b=float(left['end'])/rate,float(right['start'])/rate
            if b-a<.10:continue
            middle=(a+b)/2;cut=round(middle*48000)
            segment=y[max(0,cut-240):min(len(y),cut+240)]
            if len(segment) and np.sqrt(np.mean(segment**2))<.012:
                pauses.append((cut,min(.7,max(.2,b-a))))
        require(extend<=sum(cap for _,cap in pauses)+.05,
                'Script is too short for this duration within natural tempo/pause limits; expand the script')
        additions=[]
        for cut,capacity in sorted(pauses,key=lambda p:p[0]):
            extra=min(extend,capacity);extend-=extra
            if extra>0:additions.append((cut,round(extra*48000)))
        parts=[np.zeros(round(.15*48000))];start=0
        for cut,count in additions:
            parts.extend([y[start:cut],np.zeros(count)]);start=cut
        parts.append(y[start:]);z=np.concatenate(parts)
        target=round(seconds*48000);require(len(z)<=target,'Timing exceeded target')
        z=np.pad(z,(0,target-len(z)))
        raw=tmp/'timed.wav';write_wav(raw,z,48000)
        loudness=normalize_voice(raw,output)
    return {'target_seconds':seconds,'original_seconds':original,'tempo_factor':rate,
            'added_pauses':len(additions),'lead_seconds':.15,'pitch_shift':False,
            'pause_insertions':[{'at_seconds':cut/48000,'seconds':count/48000} for cut,count in additions],
            'closing_hold_seconds':(target-len(np.concatenate(parts)))/48000,'loudness':loudness,
            'listening_review':'pending; bounded timing does not prove editorial naturalness'}
