import json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.hybrid_motion import render_motion
class TestTrackedHybridMotion(unittest.TestCase):
 def test_dynamic_hand_anchor_and_mask_integrate(self):
  if not shutil.which("ffmpeg"):self.skipTest("ffmpeg required")
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   Image.new("RGB",(128,128),(12,15,20)).save(root/"bg.png")
   Image.new("RGB",(60,100),(0,200,100)).save(root/"screen.png")
   Image.new("L",(128,128),255).save(root/"mask.png")
   Image.new("L",(128,128),40).save(root/"depth.png")
   subprocess.run(["ffmpeg","-y","-v","error","-f","lavfi","-i",
    "testsrc=size=128x128:rate=4:duration=2","-pix_fmt","yuv420p",str(root/"motion.mp4")],check=True)
   shot={"schema":"qaf_cinematic_hybrid_pilot_v1","width":128,"height":128,"fps":4,"seconds":1,
     "background":"bg.png","phone_screen":"screen.png",
     "phone_quad":[[75,6],[105,6],[105,92],[75,92]],"medical_claims":"declared_only",
     "hand_follow_energy":True,"depth_threshold":128,
     "events":[{"type":"pulse","color":"emerald","center":[.5,.5],"start":0,"end":1}]}
   (root/"shot.json").write_text(json.dumps(shot))
   bundle={"schema":"qaf_cinematic_observations_v1","width":128,"height":128,"frames":4,
    "timeline":[{"frame":i,"mask":"mask.png","depth":"depth.png",
      "hands":[{"x":.2+.1*i,"y":.5,"confidence":.9}],"pose":[]} for i in range(4)]}
   (root/"obs.json").write_text(json.dumps(bundle))
   result=render_motion(root/"shot.json",root/"motion.mp4",root/"combined.mp4",observations=root/"obs.json")
   self.assertTrue(result["vision_observations_used"])
   self.assertTrue((root/"combined.mp4").is_file())
