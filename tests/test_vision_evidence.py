import json,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.vision_evidence import (
 validate_observations,read_observations,per_frame_evidence,anchor_point,depth_occlusion_mask)
class TestVisionEvidence(unittest.TestCase):
 def test_per_frame_segmentation_and_depth(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   Image.new("L",(128,128),255).save(root/"mask.png")
   Image.new("L",(128,128),90).save(root/"depth.png")
   data={"schema":"qaf_cinematic_observations_v1","width":128,"height":128,"frames":1,
    "timeline":[{"frame":0,"mask":"mask.png","depth":"depth.png",
      "hands":[{"x":.7,"y":.4,"confidence":.9}],"pose":[]}]}
   path=root/"evidence.json";path.write_text(json.dumps(data))
   bundle,base=read_observations(path,1,128,128)
   evidence=per_frame_evidence(bundle,base,0)
   self.assertEqual(anchor_point(evidence),(.7,.4))
   self.assertEqual(depth_occlusion_mask(evidence["mask"],evidence["depth"],128).getpixel((0,0)),255)
   self.assertEqual(depth_occlusion_mask(evidence["mask"],evidence["depth"],40).getpixel((0,0)),0)
 def test_no_missing_frames_or_path_escape(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);Image.new("L",(128,128),255).save(root/"mask.png")
   d={"schema":"qaf_cinematic_observations_v1","width":128,"height":128,"frames":2,
      "timeline":[{"frame":0,"mask":"mask.png"}]}
   with self.assertRaises(ValueError):validate_observations(d,root,2,128,128)
   d["frames"]=1;d["timeline"][0]["mask"]="../escape.png"
   with self.assertRaises(ValueError):validate_observations(d,root,1,128,128)
 def test_no_identity_guess_from_missing_hands(self):
  self.assertIsNone(anchor_point({"hands":[]}))
