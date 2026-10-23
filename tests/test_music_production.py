import json,tempfile,unittest,wave,hashlib
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
from qaf_video.music_production import produce_music
from qaf_video.cinema_project import validate_cinema
from qaf_video.core import sha256
from qaf_video.music_research.synthesis import write_wav

class MusicProductionTests(unittest.TestCase):
 def fixture(self,d):
  d=Path(d);(d/'assets').mkdir();Image.new('RGB',(10,10)).save(d/'assets/logo.png')
  t=np.arange(48000)/16000;a=.2*np.sin(2*np.pi*220*t)
  write_wav(d/'assets/voice.wav',np.column_stack([a,a]),16000)
  def asset(n):return {'sha256':sha256(d/n),'origin':'synthetic fixture','rights':'test only','privacy':'private'}
  m={'schema':'qaf_cinema_project_v1','duration':3,'fps':12,'shots':[{'start':0,'end':3,'layout':'outro','title':'test'}],
     'logo':'assets/logo.png','voice':'assets/voice.wav','caption_audio_sha256':sha256(d/'assets/voice.wav'),
     'assets':{n:asset(n) for n in ['assets/voice.wav','assets/logo.png']},'reviews':{'audio':{'approved':True,'reviewer':'old','at':'old'}}}
  p=d/'project.json';p.write_text(json.dumps(m));return p,m
 def test_real_pipeline_attaches_stems_mix_and_invalidates_approval(self):
  with tempfile.TemporaryDirectory() as d:
   p,m=self.fixture(d);r=produce_music(p);updated=json.loads(p.read_text())
   self.assertTrue(r['project_updated']);self.assertTrue((Path(d)/updated['mix']).is_file())
   self.assertFalse(updated['reviews']['audio']['approved']);self.assertFalse(updated['music_production']['human_approved'])
   self.assertIn('drums',r['stems']);self.assertTrue(validate_cinema(updated,Path(d))['valid'])
   with self.assertRaises(ValueError):validate_cinema(updated,Path(d),True)
   updated['reviews']={k:{'approved':True,'reviewer':'synthetic test fixture','at':'2026-10-22'} for k in ['audio','voice','brand','claims','rights','picture','accessibility']}
   updated['reviews']['audio']['asset_sha256']=sha256(Path(d)/updated['mix'])
   self.assertTrue(validate_cinema(updated,Path(d),True)['valid'])
   updated['reviews']['audio']['asset_sha256']='stale'
   with self.assertRaisesRegex(ValueError,'current mix hash'):validate_cinema(updated,Path(d),True)
   updated['reviews']['audio']['asset_sha256']=sha256(Path(d)/updated['mix'])
   updated['music_production']['voice_sha256']='stale'
   with self.assertRaisesRegex(ValueError,'Voice changed'):validate_cinema(updated,Path(d),True)
 def test_failure_preserves_project_and_previous_mix(self):
  with tempfile.TemporaryDirectory() as d:
   p,m=self.fixture(d);before=p.read_bytes()
   with patch('qaf_video.music_production.mix',side_effect=ValueError('mix failed')):
    with self.assertRaises(ValueError):produce_music(p)
   self.assertEqual(before,p.read_bytes());self.assertEqual(list((Path(d)/'assets/music').iterdir()),[])
 def test_contextual_brief_selects_and_records_candidate(self):
  with tempfile.TemporaryDirectory() as d:
   p,m=self.fixture(d)
   m['music_brief']={'as_of':'2026-10-22','references':[{'observed_at':'2026-10-22','confidence':1,'features':[.5]*5}],
                    'candidates':[{'id':'coastal_pulse','features':[.5]*5,'feasible':True}]}
   p.write_text(json.dumps(m));r=produce_music(p)
   self.assertEqual(r['preset'],'coastal_pulse')
   updated=json.loads(p.read_text());self.assertTrue((Path(d)/updated['music_production']['selection']).is_file())
 def test_concurrent_project_change_is_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   p,m=self.fixture(d)
   from qaf_video.music_research.mixing import mix as real_mix
   def changed(*args,**kwargs):
    result=real_mix(*args,**kwargs);p.write_text('changed by another editor');return result
   with patch('qaf_video.music_production.mix',side_effect=changed):
    with self.assertRaisesRegex(ValueError,'Project changed'):produce_music(p)
   self.assertEqual(p.read_text(),'changed by another editor')
   self.assertEqual(list((Path(d)/'assets/music').iterdir()),[])
 def test_voice_precision_rejects_cpu_fp16_and_unknown_modes(self):
  from qaf_video.voice_local import synthesize_local
  for mode in ['float16','imaginary']:
   with self.assertRaises(ValueError):synthesize_local('unused','hola','unused.wav',precision=mode)
 def test_unknown_preset_fails_without_mutation(self):
  with tempfile.TemporaryDirectory() as d:
   p,m=self.fixture(d);before=p.read_bytes()
   with self.assertRaises(ValueError):produce_music(p,'unknown')
   self.assertEqual(before,p.read_bytes())
 def test_cinema_defaults_and_football_copy_are_separate(self):
  # Read the same renderer to ensure football fields never overwrite Running defaults.
  from qaf_video.cinema import Film
  from PIL import ImageFont
  with tempfile.TemporaryDirectory() as d:
   p,m=self.fixture(d)
   m['campaign']={'cta':'Escribe «Activa fútbol»','slogan_vertical':'Comprende\ntu juego.','slogan_horizontal':'Comprende tu juego.'}
   font=Path(__file__).resolve().parents[1]/'qaf_video/assets/fonts/DejaVuSans.ttf'
   m['fonts']={k:str(font) for k in ['regular','bold','serif']}
   # local_asset forbids outside project, so copy into the fixture.
   import shutil
   shutil.copy2(font,Path(d)/'font.ttf');m['fonts']={k:'font.ttf' for k in ['regular','bold','serif']}
   f=Film(m,d,'proxy');self.assertEqual(f.frame(1).size,(540,960))
   self.assertIn('Escribe «Activa fútbol»',[x['text'] for x in f.layout_boxes])

if __name__=='__main__':unittest.main()
