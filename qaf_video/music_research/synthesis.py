"""M02: original seeded DSP sketches, editable isolated stems. No samples/weights."""
from pathlib import Path
import hashlib,json,math,wave
import numpy as np
from .arrangement import energy_at

PRESETS={
 'coastal_pulse':{'bpm':112.,'swing':.12,'hat_step':.5,'bass_steps':[0,1.5,2.75,3.5], 'root':45},
 'run_club':{'bpm':124.,'swing':.04,'hat_step':.5,'bass_steps':[.5,1.5,2.5,3.5], 'root':45},
 'future_stride':{'bpm':136.,'swing':.08,'hat_step':.25,'bass_steps':[0,1.75,2.5,3.25], 'root':42},
}

def write_wav(path,a,sr):
    if not np.isfinite(a).all() or np.max(np.abs(a),initial=0)>1:raise ValueError('Invalid PCM')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((a*32767).astype('<i2').tobytes())

def render(directory,preset='run_club',seconds=60.,sample_rate=48000,seed=22,cues=None):
    if preset not in PRESETS or not math.isfinite(seconds) or not .5<=seconds<=120:
        raise ValueError('Invalid preset or duration')
    if sample_rate not in (16000,24000,48000) or not isinstance(seed,int):raise ValueError('Invalid PCM config')
    cfg=PRESETS[preset];bpm=cfg['bpm'];beat=60/bpm;n=round(seconds*sample_rate)
    cues=[seconds*x for x in (.22,.48,.83)] if cues is None else list(cues)
    if len(cues)!=3 or not all(math.isfinite(c) and 0<c<seconds for c in cues) or cues!=sorted(set(cues)):
        raise ValueError('Three ordered section cues required')
    root=Path(directory);root.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(seed)
    stems={k:np.zeros((n,2),np.float32) for k in ('drums','bass','harmony','motif')}
    def add(name,time,sig,gain=1.,pan=0.):
        start=round(time*sample_rate)
        if not 0<=start<n:return
        count=min(len(sig),n-start);sig=sig[:count]*gain
        stems[name][start:start+count,0]+=sig*math.sqrt((1-pan)/2)
        stems[name][start:start+count,1]+=sig*math.sqrt((1+pan)/2)
    def tt(d):return np.arange(round(d*sample_rate))/sample_rate
    t=tt(.42);freq=48+100*np.exp(-t/0.025)
    kick=np.sin(2*np.pi*np.cumsum(freq)/sample_rate)*np.exp(-t/0.11)*(1-np.exp(-t/.001))
    t=tt(.18);noise=rng.normal(size=len(t));hp=noise-np.roll(noise,1)
    clap=hp*np.exp(-t/.035)*(1-np.exp(-t/.001))*.22
    t=tt(.065);noise=rng.normal(size=len(t));hat=(noise-np.roll(noise,1))*np.exp(-t/.016)*.12
    for j,b in enumerate(np.arange(0,seconds/beat,cfg['hat_step'])):
        time=b*beat+(cfg['swing']*beat if j%2 else 0)
        e=energy_at(time,cues)
        add('drums',time,hat,e*(.65 if j%2 else 1),(-.3 if j%2 else .3))
    for b in range(math.ceil(seconds/beat)):
        time=b*beat;e=energy_at(time,cues)
        # Club pulse; other sketches use a sparse kick and syncopated bass.
        if preset=='run_club' or b%4 in (0,2):add('drums',time,kick,.60*e)
        if b%4 in (1,3):add('drums',time,clap,.75*e)
    roots=[0,5,3,7]
    for bar,start in enumerate(np.arange(0,seconds,beat*4)):
        midi=cfg['root']+roots[(bar//2)%4];f=440*2**((midi-69)/12);e=energy_at(start,cues)
        for pos in cfg['bass_steps']:
            t=tt(beat*.6);en=(1-np.exp(-t/.006))*np.exp(-t/.16)
            sig=(np.sin(2*np.pi*f*t)+.22*np.sin(4*np.pi*f*t))*en
            add('bass',start+pos*beat,sig,.31*e)
        t=tt(beat*3.8);env=np.sin(np.pi*np.arange(len(t))/len(t))**2
        chord=sum(np.sin(2*np.pi*f*2**(s/12)*t) for s in (12,15,19))/3
        add('harmony',start,chord*env,.13*e,.12)
        for k,pos in enumerate((.75,1.5,2.75,3.5)):
            note=(12,19,22,15)[(k+bar%2)%4];f2=f*2**(note/12)
            t=tt(.36);sig=(np.sin(2*np.pi*f2*t)+.15*np.sin(4*np.pi*f2*t))*np.exp(-t/.095)*(1-np.exp(-t/.002))
            add('motif',start+pos*beat,sig,.13*e,(-.4 if k%2 else .4))
    # Section breaks remove drum hits briefly; no random timing of the narrative.
    time=np.arange(n)/sample_rate
    for c in cues:
        mask=(time>c-.12)&(time<c)
        stems['drums'][mask]*=np.clip((c-time[mask])/.12,0,1)[:,None]
    fade=np.minimum(1,time/.04)*np.minimum(1,(seconds-time)/.7)
    mix=sum(stems.values());peak=float(np.abs(mix).max());gain=.82/max(peak,.82)
    outputs={}
    for key,a in {**stems,'preview':mix}.items():
        p=root/(key+'.wav');write_wav(p,a*fade[:,None]*gain,sample_rate)
        outputs[key]={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    result={'schema':'qaf_music_sketch_v1','preset':preset,'config':cfg,'seed':seed,'duration':seconds,
            'sample_rate':sample_rate,'section_cues':cues,'outputs':outputs,
            'generation':'original DSP sketch; no samples; no neural model',
            'rights_status':'generated_from_repository_code; human IP/editorial review pending',
            'human_approved':False,'trend_validated':False,'common_gain':gain}
    (root/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
