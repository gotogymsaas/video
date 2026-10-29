import copy,unittest,tempfile
from pathlib import Path
from PIL import Image
from qaf_video.animation import camera_sample,crop_box,reveal_times,reveal_progress,validate_motion
from qaf_video.core import ValidationError
from qaf_video.render.compositor import Movie
class AnimationTests(unittest.TestCase):
 def setUp(self):
  self.shot={'start':0,'end':4,'motion':{'keyframes':[{'at':0,'focus':[0,0],'zoom':1},{'at':.5,'focus':[.7,.4],'zoom':1.3},{'at':1,'focus':[1,1],'zoom':1.1}]}}
 def test_continuous_stopped_internal_key(self):
  point,z=camera_sample(self.shot,.5);self.assertEqual(point,(.7,.4));self.assertEqual(z,1.3)
  for sign in [-1,1]:
   p,_=camera_sample(self.shot,.5+sign*1e-5);self.assertLess(max(abs(a-b) for a,b in zip(point,p))/1e-5,1e-6)
 def test_crop_bounds_and_aspect_for_both_formats(self):
  for target in [(1080,1920),(1920,1080)]:
   for i in range(101):
    f,z=camera_sample(self.shot,i/100);l,t,r,b=crop_box((1672,940),target,f,z)
    self.assertTrue(0<=l<r<=1672 and 0<=t<b<=940);self.assertAlmostEqual((r-l)/(b-t),target[0]/target[1])
 def test_invalid_motion(self):
  for value in [float('nan'),True,2]:
   m=copy.deepcopy(self.shot['motion']);m['keyframes'][0]['at']=value
   with self.assertRaises(ValidationError):validate_motion(m)
 def test_real_caption_alignment_and_order(self):
  s={'start':1,'end':4,'nodes':['A','B'],'node_cues':[0,1]};caps=[{'start':1.2,'end':1.5},{'start':2.1,'end':2.6}]
  self.assertAlmostEqual(reveal_times(s,caps)[0],.2);s['node_cues']=[1,0]
  with self.assertRaises(ValidationError):reveal_times(s,caps)
 def test_outside_caption_rejected(self):
  with self.assertRaises(ValidationError):reveal_times({'start':3,'end':4,'nodes':['A'],'node_cues':[0]},[{'start':2,'end':2.5}])
 def test_reveal_endpoints(self):
  self.assertEqual(reveal_progress(0,1),0);self.assertEqual(reveal_progress(2,1),1)
 def test_compositor_integrates_motion_and_cues(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td);Image.new('RGB',(600,900),'#526873').save(base/'photo.png')
   shot={**self.shot,'asset':'photo.png','nodes':['A','B'],'node_cues':[0,1]}
   m={'shots':[shot],'duration':4,'fps':30,'subtitles':[{'start':1,'end':1.3,'text':'A'},{'start':2,'end':2.3,'text':'B'}]}
   movie=Movie(m,base,'proxy');before=movie.frame(shot,.8);after=movie.frame(shot,2.7)
   self.assertEqual(before.size,after.size);self.assertNotEqual(before.tobytes(),after.tobytes())
if __name__=='__main__':unittest.main()
