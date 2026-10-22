"""Rebuild the five Spanish research proposals with XeLaTeX."""
from pathlib import Path
import subprocess,tempfile,shutil

def main():
 root=Path(__file__).resolve().parent;out=root/'papers';out.mkdir(exist_ok=True)
 for source in sorted((root/'source').glob('*.tex')):
  with tempfile.TemporaryDirectory() as tmp:
   for _ in range(2):
    subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error','-output-directory',tmp,str(source)],check=True,stdout=subprocess.DEVNULL)
   log=(Path(tmp)/(source.stem+'.log')).read_text()
   if 'Overfull' in log:raise RuntimeError('Layout overflow: '+source.name)
   shutil.copy2(Path(tmp)/(source.stem+'.pdf'),out)
if __name__=='__main__':main()
