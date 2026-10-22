"""Public source inventory; voice references require a separate private package."""
from pathlib import Path
from .core import require,sha256
PRIVATE_SUFFIXES={'.wav','.ogg','.mp3','.m4a','.flac','.safetensors','.bin','.mp4','.mov'}

def public_inventory(root,paths):
    root=Path(root).resolve();records=[]
    for name in paths:
        p=(root/name).resolve();require(p.is_relative_to(root) and p.is_file(),'Invalid release file')
        require(not set(p.relative_to(root).parts).intersection({'voice-private','voice-profiles','voice_models','.voice-venv','.git','.env'}),'Private material in public release')
        require(p.suffix.lower() not in PRIVATE_SUFFIXES and not p.name.endswith(('.voice.json','.rhythm.json')),'Voice, private reports and weights must not enter public release')
        records.append({'path':str(p.relative_to(root)),'sha256':sha256(p),'bytes':p.stat().st_size})
    return records
