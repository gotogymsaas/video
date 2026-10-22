"""Package source and a deliberately private production episode for its owner."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
EXCLUDE={'.git','__pycache__','.venv','.voice-venv','voice_models','build','dist','.qaf-cache'}

def source_files():
 for folder in ['qaf_video','docs','tests','scripts','examples']:
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and not set(p.relative_to(ROOT).parts).intersection(EXCLUDE) and p.suffix not in ['.pyc','.aux','.log','.out','.toc']:yield p,p.relative_to(ROOT)
 for name in ['pyproject.toml','MANIFEST.in','README.md','CHANGELOG.md','NOTICE.md','iniciar_estudio.py','iniciar_estudio.sh','iniciar_estudio.bat']:
  yield ROOT/name,Path(name)

def package(episode,out):
 episode=Path(episode).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);entries=list(source_files())
 for p in episode.rglob('*'):
  rel=p.relative_to(episode)
  if p.is_file() and not set(rel.parts).intersection({'__pycache__'}) and not any(part.startswith('qa-') for part in rel.parts):entries.append((p,Path('projects/running-v2')/rel))
 for p in sorted((ROOT/'dist').glob('*0.4.0*.whl')):entries.append((p,Path('instalacion')/p.name))
 readme='''# GoToGym audiovisual 0.4\n\n1. Instala Python 3.11 o posterior, FFmpeg y FFprobe.\n2. Ejecuta `python iniciar_estudio.py` o el lanzador de tu sistema.\n3. En el estudio selecciona `running-v2/project.json`.\n4. Reproduce los videos en `projects/running-v2/outputs`.\n5. En Cine y pantalla móvil revisa la captura original y genera el formato elegido.\n\nLa voz de ejemplo, la narración original y el perfil autorizado de Barranquilla están incluidos en este paquete privado. Las notas originales completas no se redistribuyen. Para sintetizar guiones nuevos instala el motor con `python scripts/setup_local_voice.py`; sus pesos no se incluyen. Luego selecciona el perfil en Tu voz de marca y usa el ritmo objetivo. Reproducir y renderizar el episodio no requiere instalar esos modelos.\n\nLos ocho artículos y el dossier están en `docs/robustness`. El informe de versión contiene 72 pruebas aprobadas, medidas y límites. Los videos son animatics fotográficos con cámara y gráficos animados. La evaluación de acento, naturalidad y preferencia artística permanece separada de la validación técnica.\n\nReferencia de voz y medios: uso privado de producción; no subirlos al repositorio público. El código y los artículos sí se publican en https://github.com/gotogymsaas/video.\n'''
 inventory=[{'path':str(rel),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p,rel in entries]
 archive=out/'GoToGym_Audiovisual_v04.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,rel in entries:z.write(p,'GoToGym_Audiovisual_v04/'+rel.as_posix())
  z.writestr('GoToGym_Audiovisual_v04/LEEME_PRIMERO.md',readme)
  z.writestr('GoToGym_Audiovisual_v04/CHECKSUMS.json',json.dumps({'schema':'qaf_private_package_v1','files':inventory,'note':'self inventory and readme excluded from hashes'},ensure_ascii=False,indent=2))
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  assert 'GoToGym_Audiovisual_v04/projects/running-v2/voice-profiles/barranquilla/reference.wav' in z.namelist()
  screen=z.read('GoToGym_Audiovisual_v04/projects/running-v2/assets/pantalla-inicio.png');assert hashlib.sha256(screen).hexdigest()==hashlib.sha256((episode/'assets/pantalla-inicio.png').read_bytes()).hexdigest()
 papers=out/'GoToGym_8_Articulos_QAF_v04.zip'
 with zipfile.ZipFile(papers,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted((ROOT/'docs/robustness').rglob('*')):
   if p.is_file() and p.suffix in ['.pdf','.tex','.json','.md']:z.write(p,'Articulos_QAF/'+p.relative_to(ROOT/'docs/robustness').as_posix())
 for name in ['Vertical','Horizontal']:shutil.copyfile(episode/f'outputs/GoToGym_Running_v2_{name}.mp4',out/f'GoToGym_Running_v2_{name}.mp4')
 shutil.copyfile(ROOT/'docs/robustness/Dossier_Cientifico_QAF_Audiovisual_v04.pdf',out/'Dossier_Cientifico_QAF_Audiovisual_v04.pdf')
 print(json.dumps([{'file':str(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file()],indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--episode',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();package(a.episode,a.out)
