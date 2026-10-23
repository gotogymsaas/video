import unittest,tempfile
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.hybrid_vfx import frame,validate_events,path_point
class EnergyTests(unittest.TestCase):
 def test_trace_and_endpoints(self):
  self.assertEqual(path_point([[0,0],[0,0],[1,0],[1,1]],.5),(1.,0.))
  self.assertEqual(path_point([[.3,.4],[.3,.4]],.7),(.3,.4))
  base=Image.new('RGB',(320,192),(12,20,30));s={'width':320,'height':192,'seconds':1,'phone_overlay':False,'camera':{'zoom':[1,1]},'events':[{'type':'trace','start':0,'end':1,'points':[[.1,.5],[.9,.5]]}]}
  validate_events(s['events'])
  with tempfile.TemporaryDirectory() as d:
   a,_=frame(s,Path(d),0,background=base);self.assertEqual(a.tobytes(),base.tobytes())
   a,_=frame(s,Path(d),.3,background=base);z,_=frame(s,Path(d),.7,background=base);self.assertNotEqual(a.tobytes(),z.tobytes())
   a,_=frame(s,Path(d),.5,background=base,foreground_mask=Image.new('L',base.size,255));self.assertEqual(a.tobytes(),base.tobytes())
 def test_camera_mask_alignment(self):
  base=Image.new('RGB',(320,192));base.paste((255,0,0),(0,0,80,192));mask=base.getchannel('R')
  s={'width':320,'height':192,'seconds':1,'phone_overlay':False,'camera':{'zoom':[1.2,1.2]},'events':[{'type':'trace','start':0,'end':1,'points':[[.235,.5],[.235,.5]],'color':'gold'}]}
  with tempfile.TemporaryDirectory() as d:
   a,_=frame(s,Path(d),.5,background=base,foreground_mask=mask)
   self.assertGreater(max(a.getpixel((75,96))),0)
 def test_invalid_events(self):
  for end in [float('nan'),True,2,-1]:
   with self.assertRaises(ValueError):validate_events([{'type':'pulse','start':0,'end':end,'center':[.5,.5]}])
  with self.assertRaises(ValueError):validate_events([{'type':'link','start':0,'end':1,'points':[[.5,.5]]}])
