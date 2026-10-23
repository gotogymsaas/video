from pathlib import Path
import json,sys,os
from concurrent.futures import ThreadPoolExecutor
from qaf_video.cinema_pipeline import render_cinema,cinema_storyboard,layout_audit
from qaf_video.voice_local import synthesize_local
from qaf_video.captions import align_script
from qaf_video.captions import token
from qaf_video.music_production import produce_music
from qaf_video.core import sha256
from qaf_video.voice import write_captions
b=Path(__file__).parent;r=b.parents[1];p=b/'project.json'
if sys.argv[1]=='picture':
 for profile in ['vertical','horizontal']:
  print(layout_audit(p,profile),flush=True);cinema_storyboard(p,b/('storyboard-'+profile+'.jpg'),profile)
 with ThreadPoolExecutor(2) as ex:list(ex.map(lambda profile:render_cinema(p,b/'outputs'/('picture-'+profile+'.mp4'),profile,cc=False),['vertical','horizontal']))
elif sys.argv[1]=='voice':
 spoken=(b/'narration-es.txt').read_text().replace('GoToGym Quantum Coach','Góu tu yim, Cuántum Cóuch').replace('GoToGym','Góu tu yim')
 profile=Path(os.environ.get('QAF_VOICE_PROFILE',r/'projects/futbol-02/voice-profiles/barranquilla/voice-profile.json'))
 x=synthesize_local(profile,spoken,b/'assets/voice-film.wav',python=r/'.voice-venv/bin/python',tts_model=r/'voice_models/qwen-base',asr_model=r/'voice_models/whisper-small',rhythm={'target_wpm':150,'episode_seconds':60},precision='bfloat16',seed=23)
 (b/'evidence/voice-result.json').write_text(json.dumps(x,ensure_ascii=False,indent=2));print('Voice ready',flush=True)
elif sys.argv[1]=='finish':
 m=json.loads(p.read_text());x=json.loads((b/'evidence/voice-result.json').read_text());print('voice result keys',list(x),flush=True)
 words=[w for s in x['transcript']['segments'] for w in s.get('words',[])]
 def anchor(term,after=0):
  aliases={'abrego':'abre'}
  found=[w['start'] for w in words if aliases.get(token(w['word']),token(w['word']))==token(term) and w['start']>after]
  if not found:raise ValueError('Missing narrative anchor: '+term)
  return round(found[0]*30)/30
 boundaries=[0,anchor('Con'),anchor('organiza'),anchor('Reúne'),anchor('Así'),anchor('Si'),anchor('No'),anchor('Te'),anchor('Abre')]
 closing=next(i for i,w in enumerate(words) if token(w['word'])=='experiencia' and w['start']>boundaries[-1]+1)
 boundaries.append(round(words[closing-1]['start']*30)/30);boundaries.append(60)
 if any(z-a<1.5 for a,z in zip(boundaries,boundaries[1:])):raise ValueError('Narrative needs editorial retiming')
 for i,s in enumerate(m['shots']):s['start'],s['end']=boundaries[i:i+2]
 m['subtitles']=align_script((b/'narration-es.txt').read_text(),words,max_chars=62,aliases={'ejercicio':'ejercicios','tiene':'tienes','contesto':'contexto','abrego':'abre','osteoortritis':'osteoartritis','teorteritis':'osteoartritis','activos':'activa','brote':'brotes','reporta':'reportas'})
 write_captions(b/'subtitles-es',m['subtitles'])
 m['voice']='assets/voice-film.wav';m['caption_audio_sha256']=sha256(b/m['voice']);m['assets'][m['voice']]={'sha256':sha256(b/m['voice']),'origin':'Local reference conditioned voice synthesis','rights':'Private user-authorized series reference','privacy':'private'};p.write_text(json.dumps(m,ensure_ascii=False,indent=2))
 print(produce_music(p,preset='coastal_pulse',seed=22),flush=True)
 for profile in ['vertical','horizontal']:cinema_storyboard(p,b/('storyboard-'+profile+'.jpg'),profile)
 jobs=[(profile,cc) for profile in ['vertical','horizontal'] for cc in [True,False]]
 with ThreadPoolExecutor(4) as ex:list(ex.map(lambda job:render_cinema(p,b/'outputs'/('GoToGym_Osteoartritis_03_'+job[0]+('' if job[1] else '_limpio')+'.mp4'),job[0],cc=job[1]),jobs))
