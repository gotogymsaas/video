"""Install the core locally and open the audiovisual studio."""
from pathlib import Path
import os,shutil,subprocess,sys,time,urllib.request,webbrowser

def main():
 root=Path(__file__).resolve().parent
 if sys.version_info<(3,11):raise SystemExit('Necesitas Python 3.11 o posterior.')
 if not all(shutil.which(n) for n in ['ffmpeg','ffprobe']):raise SystemExit('Instala FFmpeg y FFprobe y añádelos al PATH: https://ffmpeg.org/download.html')
 python=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
 if not python.is_file():subprocess.run([sys.executable,'-m','venv',str(root/'.venv')],check=True)
 subprocess.run([str(python),'-m','pip','install','-e',str(root)],check=True,cwd=root)
 process=subprocess.Popen([str(python),'-m','qaf_video','serve','--workspace',str(root/'projects'),'--port','8765'],cwd=root)
 try:
  for _ in range(30):
   if process.poll() is not None:raise SystemExit('El estudio no pudo iniciar; revisa la consola.')
   try:urllib.request.urlopen('http://127.0.0.1:8765/api/state',timeout=1).close();webbrowser.open('http://127.0.0.1:8765');break
   except OSError:time.sleep(.2)
  process.wait()
 except KeyboardInterrupt:process.terminate();process.wait()
if __name__=='__main__':main()
