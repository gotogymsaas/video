"""Install an isolated optional voice runtime and download public model weights.

No recordings or scripts are read by this setup program. Inference runs offline.
"""
from pathlib import Path
import os,subprocess,sys,venv

ROOT=Path(__file__).resolve().parents[1]
os.environ.update(ORT_DISABLE_TELEMETRY='1',HF_HUB_DISABLE_TELEMETRY='1',
                  DO_NOT_TRACK='1',GRADIO_ANALYTICS_ENABLED='False')
runtime=ROOT/'.voice-venv'
if not runtime.exists():venv.EnvBuilder(with_pip=True).create(runtime)
python=runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
def call(*args):subprocess.run([str(python),*args],check=True,cwd=ROOT,env=os.environ.copy())
if sys.platform.startswith('linux'):
    call('-m','pip','install','torch==2.6.0','torchaudio==2.6.0','--index-url','https://download.pytorch.org/whl/cpu')
else:call('-m','pip','install','torch==2.6.0','torchaudio==2.6.0')
call('-m','pip','install','qwen-tts==0.1.1','faster-whisper==1.2.1')
call('-c',
     'from huggingface_hub import snapshot_download; '
     'snapshot_download("Qwen/Qwen3-TTS-12Hz-0.6B-Base", revision="5d83992436eae1d760afd27aff78a71d676296fc", '
     'local_dir="voice_models/qwen-base", allow_patterns=["*.json","*.txt","*.safetensors","speech_tokenizer/*"],max_workers=2); '
     'snapshot_download("Systran/faster-whisper-small", revision="536b0662742c02347bc0e980a01041f333bce120", local_dir="voice_models/whisper-small", '
     'allow_patterns=["*.json","*.txt","*.bin"],max_workers=2)')
print('Motor local instalado. Los modelos requieren aproximadamente 3 GB de disco. Reabre el estudio.')
