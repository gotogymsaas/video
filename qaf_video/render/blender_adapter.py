"""Explicit optional Cycles adapter. Uses a local installed Blender only."""
from pathlib import Path
import json,shutil,tempfile
from ..core import run,require

def render(output,width=1080,height=1920,samples=64):
    executable=shutil.which('blender');require(executable is not None,'Blender not installed; use native renderer or install Blender')
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='qaf_blender_') as tmp:
        config=Path(tmp)/'job.json';config.write_text(json.dumps({'output':str(output),'width':width,'height':height,'samples':samples}))
        run([executable,'--background','--factory-startup','--python-exit-code','1','--python',Path(__file__).with_name('blender_scene.py'),'--',config],timeout=3600)
    require(output.exists(),'Blender produced no image');return output
