import json,unittest,tempfile,shutil
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.hybrid_vfx import load_spec,frame,render
class TestHybridVFX(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  Image.new("RGB",(320,192),(15,20,33)).save(self.root/"bg.png")
  Image.new("RGB",(120,220),(30,180,80)).save(self.root/"screen.png")
  self.spec={"schema":"qaf_cinematic_hybrid_pilot_v1","width":320,"height":192,"fps":8,"seconds":1,
    "background":"bg.png","phone_screen":"screen.png","phone_quad":[[225,20],[286,29],[281,166],[222,162]],"medical_claims":"declared_only",
    "events":[{"type":"pulse","start":0,"end":1,"center":[.4,.5],"color":"emerald"}]}
  self.path=self.root/"project.json";self.path.write_text(json.dumps(self.spec))
 def tearDown(self):self.temp.cleanup()
 def test_composite(self):
  spec,root=load_spec(self.path);im,details=frame(spec,root,.5)
  self.assertEqual(im.size,(320,192));self.assertEqual(details["source_size"],[120,220])
 def test_declared_only(self):
  self.spec["medical_claims"]="joint_regeneration";self.path.write_text(json.dumps(self.spec))
  with self.assertRaises(ValueError):load_spec(self.path)
 def test_mp4_export(self):
  if not shutil.which("ffmpeg"):self.skipTest("ffmpeg missing")
  report=render(self.path,self.root/"draft.mp4")
  self.assertFalse(report["neural_motion_generated"])
  self.assertEqual(report["frames"],8)
