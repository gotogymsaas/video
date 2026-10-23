import json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.hybrid_motion import render_motion
class TestHybridMotion(unittest.TestCase):
 def test_existing_mp4_is_composited(self):
  if not shutil.which("ffmpeg"):self.skipTest("ffmpeg required")
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   Image.new("RGB",(320,192),(9,12,21)).save(root/"bg.png")
   Image.new("RGB",(120,220),(12,190,70)).save(root/"screen.png")
   subprocess.run(["ffmpeg","-y","-v","error","-f","lavfi","-i",
       "testsrc=size=320x192:rate=8:duration=2","-pix_fmt","yuv420p",str(root/"actor.mp4")],check=True)
   config={"schema":"qaf_cinematic_hybrid_pilot_v1","width":320,"height":192,"fps":8,"seconds":1,
     "background":"bg.png","phone_screen":"screen.png",
     "phone_quad":[[225,20],[286,29],[281,166],[222,162]],"medical_claims":"declared_only",
     "events":[{"type":"pulse","start":0,"end":1,"center":[.4,.5],"color":"emerald"}]}
   manifest=root/"shot.json";manifest.write_text(json.dumps(config))
   report=render_motion(manifest,root/"actor.mp4",root/"combined.mp4")
   self.assertEqual(report["frames"],8)
   self.assertFalse(report["generated_neural_motion_here"])
   self.assertTrue((root/"combined.mp4").is_file())
