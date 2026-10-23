import copy,json,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.comfy_local import (patch_workflow,loopback_url,
  run_job,validate_job)

class TestComfyLocal(unittest.TestCase):
 def job(self,root):
  Image.new("RGB",(32,32),(12,23,45)).save(root/"reference.png")
  (root/"license-review.txt").write_text("Synthetic fixture, reviewer required")
  return {"schema":"qaf_comfy_i2v_job_v1","model_family":"LTX-2.5",
   "license_checked":True,"rights_checked":True,
   "review_document":"license-review.txt","image":"reference.png",
   "prompt":"A scene with genuine coherent motion","seed":22,"fps":24,"frames":97,
   "workflow":{"1":{"inputs":{"image":"old.png"},"class_type":"LoadImage"},
               "2":{"inputs":{"text":"old"},"class_type":"CLIPTextEncode"},
               "3":{"inputs":{"noise_seed":0},"class_type":"KSampler"},
               "4":{"inputs":{"length":9},"class_type":"LatentVideo"}},
   "bindings":{"image":{"node":"1","input":"image"},
               "prompt":{"node":"2","input":"text"},
               "seed":{"node":"3","input":"noise_seed"},
               "frames":{"node":"4","input":"length"}}}
 def test_loopback_only(self):
  self.assertEqual(loopback_url("http://localhost:8188"),"http://127.0.0.1:8188")
  for u in ("https://localhost:8188","http://example.com:8188","http://127.0.0.1:8188/foo"):
   with self.assertRaises(ValueError):loopback_url(u)
 def test_patch_uses_exact_node_mapping(self):
  with tempfile.TemporaryDirectory() as p:
   root=Path(p);j=self.job(root)
   v={"image":"uploaded.png","prompt":"action","seed":123,"frames":97}
   patched=patch_workflow(j["workflow"],j["bindings"],v)
   self.assertEqual(patched["1"]["inputs"]["image"],"uploaded.png")
   self.assertEqual(patched["4"]["inputs"]["length"],97)
   self.assertEqual(j["workflow"]["1"]["inputs"]["image"],"old.png")
 def test_dry_run_does_not_touch_gpu(self):
  with tempfile.TemporaryDirectory() as p:
   root=Path(p);j=self.job(root)
   r=run_job(j,root)
   self.assertEqual(r["status"],"dry_run_not_submitted")
   self.assertFalse(r["actual_neural_inference"])
 def test_licensing_and_export_configuration_fail_closed(self):
  with tempfile.TemporaryDirectory() as p:
   root=Path(p);j=self.job(root)
   j["license_checked"]=False
   with self.assertRaises(ValueError):validate_job(j,root)
   j["license_checked"]=True;j["frames"]=96
   with self.assertRaises(ValueError):validate_job(j,root)
   j["frames"]=97;j["bindings"]["prompt"]["node"]="no-such-node"
   with self.assertRaises(ValueError):validate_job(j,root)
