"""Local reference-conditioned speech adapter; no audio uploads or web calls."""
from __future__ import annotations
import json,os,re,subprocess,sys,tempfile,unicodedata,math
from pathlib import Path
from .core import require,ValidationError,atomic_json,local_asset,sha256
from .voice_languages import normalize_language,speech_plan,codec_token_budget


def caption_words(words,max_chars=68):
    cues=[];current=[];start=end=0.
    for word in words:
        a,z=float(word['start']),float(word['end']);text=word['word'].strip()
        require(math.isfinite(a) and math.isfinite(z),'Nonfinite ASR timing')
        require(len(text)<=90,'ASR word too long for captions')
        if not text or z<=a:continue
        require(a>=0 and (not cues or a>=cues[-1]['end']-.02),'Overlapping ASR word times')
        if current and (len(' '.join(current+[text]))>max_chars or z-start>4.5):
            cues.append({'start':start,'end':end,'text':' '.join(current)});current=[]
        if not current:start=max(a,cues[-1]['end'] if cues else 0)
        current.append(text);end=max(z,start+.001)
    if current:cues.append({'start':start,'end':end,'text':' '.join(current)})
    return cues


def word_error_rate(expected,actual):
    def tokenize(s):
        s=''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
        return re.findall(r'\w+',s)
    a,b=tokenize(expected),tokenize(actual);require(bool(a),'Expected script is empty')
    require(len(a)<=2000 and len(b)<=4000,'Transcript too long')
    row=list(range(len(b)+1))
    for i,left in enumerate(a,1):
        new=[i]
        for j,right in enumerate(b,1):new.append(min(new[-1]+1,row[j]+1,row[j-1]+(left!=right)))
        row=new
    return {'rate':row[-1]/len(a),'edits':row[-1],'expected_words':len(a),
            'note':'ASR-based script comparison; recognizer errors can inflate this value.'}


def runtime_settings(python=None,tts_model=None,asr_model=None):
    root=Path.cwd();default_python=root/'.voice-venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    # Keep the venv interpreter's symlink path: resolving it loses pyvenv.cfg.
    executable=Path(python or os.environ.get('QAF_VOICE_PYTHON') or (default_python if default_python.is_file() else sys.executable)).absolute()
    tts=Path(tts_model or os.environ.get('QAF_VOICE_MODEL') or root/'voice_models/qwen-base').resolve()
    asr=Path(asr_model or os.environ.get('QAF_ASR_MODEL') or root/'voice_models/whisper-small').resolve()
    require(executable.is_file(),'Voice Python environment missing; run scripts/setup_local_voice.py')
    require(tts.is_dir() and (tts/'model.safetensors').is_file(),'Local TTS weights missing; run scripts/setup_local_voice.py')
    require(asr.is_dir() and (asr/'model.bin').is_file(),'Local ASR weights missing; run scripts/setup_local_voice.py')
    return executable,tts,asr


def _worker(request,python):
    with tempfile.TemporaryDirectory(prefix='qaf_local_voice_') as tmp:
        tmp=Path(tmp);request={**request,'result':str(tmp/'result.json')};atomic_json(tmp/'request.json',request)
        env=os.environ.copy()
        # Applied before Python starts, in addition to the worker's import guard.
        env.update(ORT_DISABLE_TELEMETRY='1',HF_HUB_DISABLE_TELEMETRY='1',HF_HUB_OFFLINE='1',
                   TRANSFORMERS_OFFLINE='1',DO_NOT_TRACK='1',GRADIO_ANALYTICS_ENABLED='False')
        package_root=str(Path(__file__).resolve().parent.parent)
        env['PYTHONPATH']=package_root+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
        try:
            result=subprocess.run([str(python),'-m','qaf_video.local_voice_worker',str(tmp/'request.json')],
                                  capture_output=True,text=True,env=env,timeout=1800)
        except subprocess.TimeoutExpired as e:raise ValidationError('Local voice generation exceeded 30 minutes; use a shorter script or a faster device') from e
        require(result.returncode==0,f'Local voice worker failed (exit {result.returncode}): '+result.stderr[-2000:])
        return json.loads((tmp/'result.json').read_text(encoding='utf-8'))


def transcribe_local(audio,python=None,asr_model=None,tts_model=None,language='Spanish'):
    # ASR does not require the TTS model or its heavyweight runtime.
    executable=Path(python or os.environ.get('QAF_ASR_PYTHON') or os.environ.get('QAF_VOICE_PYTHON') or sys.executable).absolute()
    asr=Path(asr_model or os.environ.get('QAF_ASR_MODEL') or Path.cwd()/'voice_models/whisper-small').resolve()
    require(executable.is_file() and (asr/'model.bin').is_file(),'Local ASR runtime or weights missing')
    return _worker({'operation':'transcribe','audio':str(Path(audio).resolve()),'asr_model':str(asr),
                    'language':normalize_language(language)},executable)


def synthesize_local(profile,text,output,python=None,tts_model=None,asr_model=None,device='cpu',seed=22,target_seconds=None,
                     language='Spanish',segments=None,rhythm=None,precision=None):
    plan=speech_plan(text,language,segments)
    for part in plan:codec_token_budget(part['text'],target_seconds)
    require(device in ['cpu','cuda:0','mps'],'Unsupported inference device')
    require(precision in [None,'float32','float16','bfloat16'],'Unsupported inference precision')
    require(device!='cpu' or precision!='float16','Use float32 or bfloat16 for CPU inference')
    if rhythm is not None:
        require(isinstance(rhythm,dict) and target_seconds is None,'Choose continuous rhythm or legacy timing')
        require(all(p['language'] not in ['Chinese','Japanese','Korean'] for p in plan),'Use native phrase pacing for languages without comparable word counts')
        require(80<=float(rhythm.get('target_wpm',175))<=240 and 3<=float(rhythm.get('episode_seconds',60))<=600,'Invalid rhythm budget')
    path=Path(profile).resolve();p=json.loads(path.read_text(encoding='utf-8'))
    require(p.get('schema')=='qaf_voice_profile_v1','Invalid voice profile')
    ref=local_asset(path.parent,p.get('reference_audio'))
    require(sha256(ref)==p.get('reference_sha256'),'Voice reference changed')
    output=Path(output).resolve();require(output.suffix.lower()=='.wav','Local voice output must be WAV')
    executable,tts,asr=runtime_settings(python,tts_model,asr_model)
    return _worker({'operation':'synthesize','profile':str(path),'text':text,'output':str(output),
                    'tts_model':str(tts),'asr_model':str(asr),'device':device,'seed':seed,
                    'target_seconds':target_seconds,'language':normalize_language(language),'segments':segments,'rhythm':rhythm,
                    **({'precision':precision} if precision else {})},executable)
