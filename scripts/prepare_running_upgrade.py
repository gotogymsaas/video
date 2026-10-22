"""Create a private canonical episode from the previous editable production.

Only synthetic production voice is copied. No biometric reference is needed.
"""
import argparse,json,shutil
from pathlib import Path
from qaf_video.core import atomic_json,sha256
from qaf_video.voice_rhythm import natural_voice
from qaf_video.voice_local import transcribe_local
from qaf_video.captions import align_script,pronunciation_review
from qaf_video.voice import write_captions
from qaf_video.audio_scene import mix_story
from qaf_video.cinema_project import validate_cinema

def prepare(original,output,screen,asr_python=None,asr_model=None):
 original=Path(original).resolve();output=Path(output).resolve();assets=output/'assets';evidence=output/'evidence';assets.mkdir(parents=True,exist_ok=True);evidence.mkdir(exist_ok=True)
 for name in ['01_dawn.png','02_laces.png','03_walk.png','04_sunrise.png','05_journal.png','logo-gotogym.png','music-original.wav','ambience-original.wav']:shutil.copyfile(original/'assets'/name,assets/name)
 shutil.copytree(original/'assets/fonts',assets/'fonts',dirs_exist_ok=True);shutil.copyfile(screen,assets/'pantalla-inicio.png');shutil.copyfile(original/'evidence/running-example-checks.json',evidence/'running-example-checks.json')
 text=(original/'narration-es.txt').read_text().strip();rhythm=natural_voice(original/'assets/narration.wav',assets/'voice-film.wav',text,target_wpm=175,lead_seconds=.6)
 transcript=transcribe_local(assets/'voice-film.wav',python=asr_python,asr_model=asr_model);atomic_json(evidence/'final-voice-transcript.json',transcript)
 words=[w for s in transcript['segments'] for w in s['words']];captions=align_script(text,words,aliases={'cinco':'5','veinte':'20'})
 write_captions(output/'outputs/Running_60s',captions);atomic_json(output/'captions.json',captions);(output/'narration-es.txt').write_text(text+'\n')
 mix=mix_story(assets/'mix.wav',60,assets/'voice-film.wav',assets/'music-original.wav',assets/'ambience-original.wav')
 atomic_json(evidence/'voice-improvement.json',{'previous_tempo':.82,'previous_inserted_pauses':11,'current':rhythm,'relative_spoken_speed':rhythm['tempo_factor']/.82,'narration_seconds':rhythm['target_seconds'],'editorial_rest_count':0,'note':'Visual/music product hold follows the naturally complete narration; no speech is stretched to sixty seconds.'})
 atomic_json(evidence/'pronunciation-review.json',pronunciation_review(text,transcript['text'],glossary={'running':'audición regional'}))
 beats=[0,4.5,9.5,11.4,17.7,21,24.3,27.5,31.3,35.1,37.7,40.2,54,60]
 layouts=['headline','headline','headline','inputs','choice','headline','headline','headline','diary','diary','headline','phone','outro']
 titles=['Tus primeros\n5K.','Hoy es\ndiferente.','Tu día\ncambió.','Tu día, conectado.','Compara opciones.','Caminar\ntambién cuenta.','Camina\ny trota.','Tú decides.','Lo que\nrealmente hiciste.','Tu historia\ncuenta.','Una forma\nde continuar.','Bienvenido a GoToGym.','Tu próximo paso']
 names=['02_laces.png','01_dawn.png','01_dawn.png','01_dawn.png','01_dawn.png','03_walk.png','04_sunrise.png','04_sunrise.png','05_journal.png','05_journal.png','04_sunrise.png',None,None]
 brows=['UN OBJETIVO QUE IMPORTA','POCO DESCANSO. POCO TIEMPO.','LA META PERMANECE','','','HOY / CASO ILUSTRATIVO','OTRO DÍA / MEJOR DESCANSO','EL SIGUIENTE PASO ES TUYO','','','SOSTENER EL PROPÓSITO','TU PUNTO DE PARTIDA','']
 bodies={0:'El próximo paso / Episodio 01',5:'15 minutos · propuesta para revisar',6:'20 minutos · otro escenario de ejemplo',11:'Tu próximo paso empieza aquí.'};shots=[]
 for i,layout in enumerate(layouts):
  s={'start':beats[i],'end':beats[i+1],'layout':layout,'title':titles[i],'eyebrow':brows[i],'body':bodies.get(i,''),'focus':[.46,.5],'zoom':[1.,1.035]}
  if names[i]:s['asset']='assets/'+names[i]
  if i in [1,2]:s['right']=True
  if i==2:s.update(focus=[.435,.28],zoom=[1.58,1.63])
  if i==9:s['continuity']=True
  if i==3:s['claim_ids']=['C1']
  if i in [4,5,6,7]:s['claim_ids']=['C2']
  if i in [8,9]:s['claim_ids']=['C3']
  shots.append(s)
 source='gotogymsaas/appdesplegada@6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62'
 claims={'C1':{'source':source+'/backend/api/qaf_running_intelligence/engine.py','scope':'declared context; no inferred biometrics','status':'verified_local','evidence_asset':'evidence/running-example-checks.json'},'C2':{'source':source+'/backend/api/qaf_running_intelligence/engine.py','scope':'finite rule-based choice for complete fictional fixtures; no clinical effect','status':'verified_local','evidence_asset':'evidence/running-example-checks.json'},'C3':{'source':source+'/QAF/08_agentes_coach/ESTADO_IMPLEMENTACION_RUNNING_OSTEOARTRITIS_2026-10-18.md','scope':'documented previous_result/feedback continuity; no production test here','status':'documented'}}
 m={'schema':'qaf_cinema_project_v1','title':'El próximo paso · Running v2','duration':60,'fps':30,'mode':'conceptual','shots':shots,'voice':'assets/voice-film.wav','mix':'assets/mix.wav','logo':'assets/logo-gotogym.png','phone_screen':'assets/pantalla-inicio.png','fonts':{'regular':'assets/fonts/NimbusSans-Regular.otf','bold':'assets/fonts/NimbusSans-Bold.otf','serif':'assets/fonts/NimbusRoman-Italic.otf'},'subtitles':captions,'caption_audio_sha256':sha256(assets/'voice-film.wav'),'claims':claims,'input_cards':[{'label':'DESCANSO','value':'5 h'},{'label':'TIEMPO','value':'20 min'},{'label':'HISTORIAL','value':'Inicio'}],'comparison_cards':[{'label':'CAMINAR','value':'Compatible'},{'label':'TROTAR','value':'No elegida','active':False},{'label':'CORRER','value':'No elegida','active':False}],'reviews':{},'assets':{},'sales_structure':{'natural_problem':'Quiero correr mis primeros cinco kilómetros','tactical_obstacle':'Poco descanso y veinte minutos','strategic_goal':'Mantener continuidad con el objetivo'},'treatment':'photographic cinematic animatic; no generated human motion'}
 referenced={s['asset'] for s in shots if s.get('asset')}|set(m['fonts'].values())|{m[k] for k in ['voice','mix','logo','phone_screen']}|{'evidence/running-example-checks.json'}
 for name in sorted(referenced):
  p=output/name;origin='original user application screenshot' if 'pantalla' in name else 'original product repository logo' if 'logo' in name else 'generated photographic keyframe' if p.suffix=='.png' else 'URW Base35 licensed font' if p.suffix=='.otf' else 'local synthetic voice / original score' if p.suffix=='.wav' else 'execution of pinned product fixture'
  m['assets'][name]={'sha256':sha256(p),'origin':origin,'rights':'supplied GoToGym production asset; see font licenses','privacy':'private' if p.suffix=='.wav' else 'public'}
 validate_cinema(m,output);atomic_json(output/'project.json',m);return {'project':str(output/'project.json'),'voice_seconds':rhythm['target_seconds'],'tempo':rhythm['tempo_factor'],'captions':len(captions),'mix_lufs':mix['output_measurement']['input_i']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('original',type=Path);p.add_argument('output',type=Path);p.add_argument('--screen',type=Path,required=True);p.add_argument('--asr-python',type=Path);p.add_argument('--asr-model',type=Path);a=p.parse_args();print(json.dumps(prepare(a.original,a.output,a.screen,a.asr_python,a.asr_model),ensure_ascii=False,indent=2))
