import itertools,json,tempfile,unittest,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from qaf_video.core import ValidationError,sha256,atomic_json,ASSETS
from qaf_video.quality import select,contrast,text_contract
from qaf_video.phone import homography,phone_plate,place_phone
from qaf_video.voice_rhythm import silence_metrics,natural_voice
from qaf_video.voice_lab import write_wav,decode
from qaf_video.captions import align_script,pronunciation_review
from qaf_video.cinema_project import validate_cinema,render_key,public_asset_list
from qaf_video.release import public_inventory
from qaf_video.audio_scene import dialogue_margin

class DecisionTests(unittest.TestCase):
 def test_fixed_basis_normalization_and_native_constraint(self):
  r=select([{'loss':0,'feasible':False},{'loss':3},{'loss':4}]);self.assertEqual(r['selected_index'],1);self.assertEqual(r['classical_baseline_index'],1);self.assertAlmostEqual(sum(r['probabilities']),1);self.assertEqual(r['probabilities'][0],0);self.assertGreaterEqual(min(np.linalg.eigvalsh(np.diag(r['probabilities']))),0)
 def test_compiled_qubo_matches_native_optimum_exhaustively(self):
  loss=np.array([.9,.2,.6,.8,1.1,.7]);r=select([{'loss':v} for v in loss]);q=r['qubo']
  def energy(bits):return q['constant']+np.dot(q['diagonal'],bits)+sum(q['off_diagonal']*bits[i]*bits[j] for i in range(6) for j in range(i+1,6))
  result=min(itertools.product([0,1],repeat=6),key=energy);self.assertEqual(sum(result),1);self.assertEqual(result.index(1),int(np.argmin(loss)))
 def test_no_feasible_and_nan_rejected(self):
  with self.assertRaises(ValidationError):select([{'loss':0,'feasible':False}])
  with self.assertRaises(ValidationError):select([{'loss':float('nan')}])
 def test_contrast_and_mobile_bounds(self):
  self.assertAlmostEqual(contrast('#FFFFFF','#000000'),21);self.assertGreater(contrast('#0FBFB0','#101012'),4.5);self.assertFalse(text_contract([100,20,1000,20],[1080,1920],36)['inside_canvas']);self.assertTrue(text_contract([30,40,900,100],[1080,1920],36)['readable'])
class PhoneTests(unittest.TestCase):
 def test_projective_corner_reprojection_and_inverse(self):
  a=np.array([[0,0],[400,0],[400,800],[0,800]],float);b=np.array([[30,40],[420,65],[400,900],[15,860]],float);h=homography(a,b);z=np.column_stack([a,np.ones(4)])@h.T;np.testing.assert_allclose(z[:,:2]/z[:,2:],b,atol=1e-8);z=np.column_stack([b,np.ones(4)])@np.linalg.inv(h).T;np.testing.assert_allclose(z[:,:2]/z[:,2:],a,atol=1e-8)
 def test_full_screen_keeps_bottom_and_aspect(self):
  screen=Image.new('RGB',(300,600),'#0FBFB0');screen.paste('#D4B46A',(0,590,300,600));plate,r=phone_plate(screen,1200);x,y,w,h=r['screen_box'];self.assertLess(r['aspect_error'],.001);self.assertEqual(plate.getpixel((x+w//2,y+h-5))[:3],(212,180,106))
 def test_degenerate_and_crossed_quad_rejected(self):
  with self.assertRaises(ValidationError):homography([(0,0)]*4,[(1,1)]*4)
  with self.assertRaises(ValidationError):place_phone(Image.new('RGB',(400,800)),Image.new('RGB',(200,400)),[(0,0),(300,700),(300,0),(0,700)])
class RhythmCaptionTests(unittest.TestCase):
 def test_energy_detector_distinguishes_edge_silence_and_internal_gap(self):
  sr=1000;t=np.arange(2000)/sr;tone=.1*np.sin(2*np.pi*100*t);r=silence_metrics(np.r_[np.zeros(300),tone,np.zeros(800),tone,np.zeros(300)],sr);self.assertEqual(r['internal_gaps_over_650ms'],1);self.assertAlmostEqual(r['max_internal_gap'],.8,places=2)
 def test_continuous_timing_never_inserts_sentence_pauses_or_pads_minute(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);sr=48000;t=np.arange(sr*4)/sr;write_wav(root/'source.wav',.1*np.sin(2*np.pi*180*t),sr);r=natural_voice(root/'source.wav',root/'out.wav','uno dos tres cuatro cinco seis siete ocho nueve diez once doce',10,180);self.assertEqual(r['added_pauses'],0);self.assertLess(len(decode(root/'out.wav'))/48000,5);self.assertLessEqual(abs(r['tempo_factor']-1),.081)
 def test_measured_caption_anchors_and_revision_queue(self):
  words=[{'word':'Tu','start':1.,'end':1.3},{'word':'día','start':1.3,'end':1.7},{'word':'cambio','start':1.7,'end':2.2}];r=align_script('Tu día cambió.',words);self.assertEqual(r[0]['start'],1);self.assertEqual(r[0]['end'],2.2)
  with self.assertRaises(ValidationError):align_script('Hola.',words)
 def test_missing_foreign_term_remains_a_listening_issue(self):
  r=pronunciation_review('Quantum Coach','coach','English',{'Quantum Coach':'audition'});self.assertGreater(r['script_comparison']['rate'],0);self.assertFalse(r['terms'][0]['recognizer_found']);self.assertFalse(r['approved'])
 def test_dialogue_margin_changes_with_music_gain(self):
  t=np.arange(16000)/16000;v=.1*np.sin(2*np.pi*200*t);m=.1*np.sin(2*np.pi*300*t);self.assertAlmostEqual(dialogue_margin(v,m,.1)['median_db']-dialogue_margin(v,m,.2)['median_db'],6.0206,places=3)
class ProvenanceTests(unittest.TestCase):
 def manifest(self,root):
  (root/'screen.png').write_bytes(b'exact source bytes');return {'schema':'qaf_cinema_project_v1','duration':2,'fps':30,'shots':[{'start':0,'end':2,'layout':'phone'}],'phone_screen':'screen.png','assets':{'screen.png':{'sha256':sha256(root/'screen.png'),'origin':'user','rights':'production','privacy':'public'}}}
 def test_source_change_invalidates_project(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);m=self.manifest(root);self.assertEqual(validate_cinema(m,root)['frames'],60);(root/'screen.png').write_bytes(b'new')
   with self.assertRaises(ValidationError):validate_cinema(m,root)
 def test_gap_and_unbound_mechanism_are_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);m=self.manifest(root);m['shots'][0]['start']=.1
   with self.assertRaises(ValidationError):validate_cinema(m,root)
   m['shots'][0].update(start=0,layout='inputs')
   with self.assertRaises(ValidationError):validate_cinema(m,root)
 def test_caption_hash_and_unreviewed_final_are_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);m=self.manifest(root)
   with self.assertRaises(ValidationError):validate_cinema(m,root,True)
   m.update(voice='screen.png',caption_audio_sha256='stale')
   with self.assertRaises(ValidationError):validate_cinema(m,root)
 def test_cache_invalidates_captions_fonts_engine_environment(self):
  base=render_key({}, {'font':'a'},'vertical',True,'v1',{'ffmpeg':'x'})
  for args in [({}, {'font':'b'},'vertical',True,'v1',{'ffmpeg':'x'}),({}, {'font':'a'},'vertical',False,'v1',{'ffmpeg':'x'}),({}, {'font':'a'},'vertical',True,'v2',{'ffmpeg':'x'}),({}, {'font':'a'},'vertical',True,'v1',{'ffmpeg':'y'})]:self.assertNotEqual(base,render_key(*args))
 def test_public_bundle_rejects_voice_and_model_weights(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'voice.wav').write_bytes(b'private');(root/'code.py').write_text('pass')
   with self.assertRaises(ValidationError):public_inventory(root,['voice.wav'])
   self.assertEqual(len(public_inventory(root,['code.py'])),1)
  self.assertEqual(public_asset_list({'assets':{'ref':{'privacy':'private'},'screen':{'privacy':'public'}}}),{'screen':{'privacy':'public'}})
class CinemaIntegrationTests(unittest.TestCase):
 def test_both_aspects_single_encode_full_decode_and_verified_cache(self):
  from qaf_video.cinema_pipeline import render_cinema
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);Image.new('RGB',(200,400),'#0FBFB0').save(root/'screen.png');Image.new('RGB',(100,100),'#D4B46A').save(root/'logo.png')
   for name in ['DejaVuSans.ttf','DejaVuSans-Bold.ttf']:shutil.copyfile(ASSETS/'fonts'/name,root/name)
   m={'schema':'qaf_cinema_project_v1','duration':.5,'fps':8,'title':'Smoke','shots':[{'start':0,'end':.5,'layout':'phone','title':'Tu próximo paso'}],'phone_screen':'screen.png','logo':'logo.png','fonts':{'regular':'DejaVuSans.ttf','bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSans.ttf'},'assets':{}}
   for name in ['screen.png','logo.png','DejaVuSans.ttf','DejaVuSans-Bold.ttf']:m['assets'][name]={'sha256':sha256(root/name),'origin':'fixture','rights':'fixture','privacy':'public'}
   atomic_json(root/'project.json',m)
   for profile in ['proxy','landscape-proxy']:
    r=render_cinema(root/'project.json',root/f'{profile}.mp4',profile);self.assertTrue(r['technical']['technical_passed']);self.assertEqual(r['frames'],4);self.assertEqual(r['video_encode_generations'],1);self.assertTrue(render_cinema(root/'project.json',root/f'{profile}.mp4',profile)['cache_hit'])
   (root/'proxy.mp4').write_bytes(b'incomplete');self.assertFalse(render_cinema(root/'project.json',root/'proxy.mp4','proxy')['cache_hit'])
if __name__=='__main__':unittest.main()
