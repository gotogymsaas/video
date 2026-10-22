import hashlib,itertools,json,tempfile,unittest,wave
from pathlib import Path
import numpy as np
from qaf_video.music_research.preference import choose,target
from qaf_video.music_research.arrangement import align
from qaf_video.music_research.synthesis import render
from qaf_video.music_research.mixing import release_ms,mix
from qaf_video.music_research.evaluation import paired_report,verify_asset

class MusicResearchTests(unittest.TestCase):
 def test_freshness_and_future_rejection(self):
  refs=[{'observed_at':'2026-10-22','confidence':1,'features':[1]*5},{'observed_at':'2026-07-24','confidence':1,'features':[0]*5}]
  self.assertTrue(np.allclose(target(refs,'2026-10-22')['features'],2/3))
  with self.assertRaises(ValueError):target(refs,'2026-01-01')
 def test_feasible_rho_and_same_information_control(self):
  cs=[{'id':'perfect-but-forbidden','features':[.8]*5,'feasible':False},{'id':'allowed','features':[.4]*5,'feasible':True}]
  result=choose(cs,[.8]*5)
  self.assertEqual(result['selected']['id'],'allowed');p=np.array(result['probabilities'])
  self.assertAlmostEqual(p.sum(),1);self.assertTrue((p>=0).all());self.assertEqual(p[0],0)
  self.assertEqual(result['classical_baseline_index'],result['selected_index'])
 def test_relation_changes_utility_without_quantum_advantage(self):
  cs=[{'features':[.9,.5,.5,.1,.5],'feasible':True},{'features':[.6,.5,.5,.4,.5],'feasible':True}]
  r=choose(cs,[.7,.5,.5,.7,.5]);self.assertFalse(r['incremental_advantage_claimed'])
  self.assertGreater(r['alternatives'][0]['relational_loss'],r['alternatives'][1]['relational_loss'])
 def test_reject_nonfinite(self):
  with self.assertRaises(ValueError):choose([{'features':[float('nan')]*5}], [.5]*5)
  with self.assertRaises(ValueError):align([1,2,3],bpm=float('nan'))
 def test_dp_matches_exhaustive_oracle(self):
  cues=[1.1,2.2,3.3];r=align(cues,4,120,tolerance=.5,gap=.4)
  grid=np.arange(0,4,.5);sets=[grid[abs(grid-c)<=.5+1e-9] for c in cues]
  oracle=min(sum((a-b)**2 for a,b in zip(p,cues)) for p in itertools.product(*sets) if all(b-a>=.4 for a,b in zip(p,p[1:])))
  self.assertAlmostEqual(r['loss_seconds_squared'],oracle)
 def test_no_silent_fallback_on_infeasible_cues(self):
  with self.assertRaises(ValueError):align([1.2],seconds=2,bpm=120,tolerance=.01)
  with self.assertRaises(ValueError):align([1,1],seconds=2)
 def test_seed_pcm_duration_and_stems(self):
  with tempfile.TemporaryDirectory() as d:
   a=render(Path(d)/'a',seconds=1,sample_rate=16000);b=render(Path(d)/'b',seconds=1,sample_rate=16000)
   self.assertEqual(a['outputs'],b['outputs']);self.assertFalse(a['human_approved'])
   with wave.open(str(Path(d)/'a/preview.wav')) as w:
    self.assertEqual(w.getnframes(),16000);self.assertEqual(w.getnchannels(),2)
    pcm=np.frombuffer(w.readframes(16000),dtype='<i2');self.assertGreater(np.abs(pcm).max(),1000)
   changed=render(Path(d)/'c',seconds=1,sample_rate=16000,seed=23)
   self.assertNotEqual(a['outputs']['drums']['sha256'],changed['outputs']['drums']['sha256'])
 def test_plan_cues_are_used(self):
  with tempfile.TemporaryDirectory() as d:
   r=render(d,seconds=2,sample_rate=16000,cues=[.4,1.,1.6]);self.assertEqual(r['section_cues'],[.4,1.,1.6])
 def test_beat_relative_release(self):
  self.assertAlmostEqual(release_ms(120),375)
  with self.assertRaises(ValueError):release_ms(-1)
 def test_cluster_bootstrap_does_not_invent_evidence(self):
  rows=[{'listener':str(i),'episode':str(j),'baseline':40,'candidate':60} for i in range(4) for j in range(2)]
  r=paired_report(rows);self.assertEqual(r['mean_gain_100pt'],20);self.assertEqual(r['status'],'insufficient_evidence')
  self.assertFalse(r['automatic_release'])
  with self.assertRaises(ValueError):paired_report(rows+rows[:1])
  with self.assertRaises(ValueError):paired_report(rows,min_listeners=0)
 def test_rights_fail_closed_and_hash_bound(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'music.wav';p.write_bytes(b'fixture');m={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'origin':'test','rights_record':'signed-record-1','license_id':'original','reviewer':'owner','reviewed_at':'2026-10-22','valid_until':'2026-12-31','commercial_use':True,'sync_rights':True}
   self.assertTrue(verify_asset(p,m,'2026-10-22')['contract_passed'])
   with self.assertRaises(ValueError):verify_asset(p,{**m,'sync_rights':False},'2026-10-22')
   p.write_bytes(b'changed')
   with self.assertRaises(ValueError):verify_asset(p,m,'2026-10-22')
 def test_measured_mix_integration(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);render(d/'music',seconds=3,sample_rate=16000)
   t=np.arange(48000)/16000;voice=.2*np.sin(2*np.pi*210*t)*(np.sin(2*np.pi*2*t)>0)
   from qaf_video.music_research.synthesis import write_wav
   write_wav(d/'voice.wav',np.column_stack([voice,voice]),16000)
   r=mix(d/'mix.wav',d/'voice.wav',d/'music/preview.wav',3)
   self.assertTrue(r['two_pass']);self.assertTrue(r['ducking']);self.assertFalse(r['perceptual_approval'])
   self.assertLessEqual(float(r['output_measurement']['input_tp']),-1)

if __name__=='__main__':unittest.main()
