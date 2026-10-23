from pathlib import Path
import json,hashlib
from qaf_video.captions import align_script,token
from qaf_video.voice import write_captions
b=Path(__file__).parent
m={'schema':'qaf_cinema_project_v1','mode':'conceptual','logo':'assets/logo-gotogym.png','phone_screen':'assets/pantalla-inicio.png','fonts':{'regular':'assets/fonts/NimbusSans-Regular.otf','bold':'assets/fonts/NimbusSans-Bold.otf','serif':'assets/fonts/NimbusRoman-Italic.otf'}}
x=json.loads((b/'evidence/voice.json').read_text());words=[w for s in x['transcript']['segments'] for w in s['words']]
def anchor(term,after=0):
 a={'abrego':'abre'};v=next(w['start'] for w in words if a.get(token(w['word']),token(w['word']))==token(term) and w['start']>after);return round(v*30)/30
times=[0,anchor('A'),anchor('Con'),anchor('Comparte'),anchor('Si'),anchor('Tú',25),anchor('Las'),anchor('Abre'),49,60]
def shot(i,title='',body='',eyebrow='',layout='headline',asset='court.png',**kw):
 s=dict(start=times[i],end=times[i+1],layout=layout,title=title,body=body,eyebrow=eyebrow,focus=[.5,.40],zoom=[1,1.035],claim_ids=['guidance'],**kw)
 if asset:s['asset']='assets/'+asset
 return s
shots=[shot(0,'Un punto.\nTodo por jugar.',eyebrow='TENIS / EPISODIO 04'),shot(1,'Encuentra\nun foco.',eyebrow='EL SIGUIENTE PUNTO'),shot(2,'Cuenta lo que\nte pasa.',eyebrow='GOTOGYM QUANTUM COACH',asset='bench.png'),shot(3,layout='inputs',asset='bench.png'),shot(4,layout='choice',asset='bench.png'),shot(5,'Revisa.\nDecide.',eyebrow='TÚ CONSERVAS EL CONTROL',layout='diary',asset=None,labels=['Tu objetivo','Tu contexto','Tu siguiente paso']),shot(6,'Visualización\nconceptual.','Tu relato orienta la propuesta.','TU EXPERIENCIA CUENTA',asset='bench.png'),shot(7,'Tu próximo punto.','Empieza contigo.','GOTOGYM QUANTUM COACH',layout='phone',asset=None),shot(8,layout='outro',asset=None)]
for i in [0,2,6]:shots[i]['vfx']={'purpose':'conceptual','events':[{'type':'trace','start':0,'end':1,'points':[[.15,.56],[.30,.48],[.72,.52],[.86,.41]],'color':'gold'},{'type':'pulse','start':.15,'end':.9,'center':[.78,.54],'color':'mint'}]}
shots[7]['vfx']={'purpose':'conceptual','events':[{'type':'trace','start':0,'end':1,'points':[[.12,.17],[.87,.17],[.87,.81],[.12,.81]],'color':'mint'}]}
m.update(title='Tu próximo punto / Tenis / Episodio 04',duration=60,fps=30,shots=shots,assets={},reviews={},claims={'guidance':{'source':'https://github.com/gotogymsaas/appdesplegada/blob/6d2e95d031c2e3c2b83c8c1e442fd6315ef95d62/backend/api/qaf_tennis_intelligence/engine.py','scope':'Fictional declared pressure; local engine suggests a 12-second routine. No visual sensing, prediction or production verification claimed.','status':'verified_local','evidence_asset':'evidence/tennis-example.json'}},context_eyebrow='TENIS / CONTEXTO DECLARADO',context_heading='Tu experiencia, primero.',choice_heading='Un foco entre puntos.',context_footer='Datos declarados · ejemplo ficticio',input_cards=[{'label':'NIVEL DECLARADO','value':'Intermedio'},{'label':'OBJETIVO','value':'Volver al presente'},{'label':'CONTEXTO DECLARADO','value':'Presión tras perder un punto'}],comparison_cards=[{'label':'RESPIRAR','value':'Vuelve al presente'},{'label':'ELEGIR','value':'Un objetivo claro'},{'label':'CONTINUAR','value':'Atención al próximo punto'}],result_card={'label':'RUTINA SUGERIDA','value':'12 segundos','body':'Entre puntos · para revisar'},campaign={'cta':'Escribe «Activa tenis»','slogan_vertical':'Tu próximo punto\nempieza contigo.','slogan_horizontal':'Tu próximo punto empieza contigo.'},sales_structure={'human_goal':'Volver al presente entre puntos','obstacle':'Presión declarada','demonstration':'Contexto -> rutina sugerida -> revisión','cta':'Activa tenis'},treatment='Fictional generated photographs, local generative voice and own procedural VFX. No generated human action or measured ball trajectory.')
m['subtitles']=align_script((b/'narration-es.txt').read_text(),words,max_chars=62,aliases={'gotogin':'gotogym','abrego':'abre','puedes':'puede'})
m['voice']='assets/voice.wav';m['caption_audio_sha256']=hashlib.sha256((b/m['voice']).read_bytes()).hexdigest()
for p in list((b/'assets').rglob('*'))+[b/'evidence/tennis-example.json']:
 if not p.is_file() or (p.suffix not in ['.png','.otf','.ttf'] and p.name not in ['tennis-example.json','voice.wav']):continue
 n=p.relative_to(b).as_posix();m['assets'][n]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'origin':'Commissioned fictional generation, original brand asset or local source fixture','rights':'Series production; licenses bundled; human review pending','privacy':'private' if p.name=='voice.wav' else 'public'}
write_captions(b/'subtitles-es',m['subtitles']);(b/'project.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));print('Project ready',flush=True)
