from pathlib import Path
import json,os,time
from qaf_video.voice_local import synthesize_local
b=Path(__file__).parent;r=b.parents[1]
if not (r/'qaf_video').is_dir():r=b.parent/'video'
for _ in range(600):
 if (r/'voice_models/whisper-small/model.bin').exists():break
 time.sleep(1)
else:raise TimeoutError('Voice runtime unavailable')
p=Path(os.environ.get('QAF_VOICE_PROFILE',b/'voice-profiles/barranquilla/voice-profile.json'))
text=(b/'narration-es.txt').read_text().replace('GoToGym Quantum Coach','Góu tu yim, Cuántum Cóuch').replace('GoToGym','Góu tu yim')
x=synthesize_local(p,text,b/'assets/voice.wav',python=r/'.voice-venv/bin/python',tts_model=r/'voice_models/qwen-base',asr_model=r/'voice_models/whisper-small',precision='bfloat16',seed=24,rhythm={'target_wpm':165,'episode_seconds':60})
(b/'evidence/voice.json').write_text(json.dumps(x,ensure_ascii=False,indent=2));print('Voice ready',flush=True)
