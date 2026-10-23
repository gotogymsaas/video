import json,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.open_corpus import audit_asset,compile_training_manifest
from qaf_video.generative_research.paired_benchmark import matched_video_benchmark,video_proxy_metrics

class TestOpenCinematicStack(unittest.TestCase):
 def fixture(self,root,i,split):
  from shutil import which
  Image.new("RGB",(32,32),(40+i*30,30,15)).save(root/f"{i}.png")
  (root/f"proof{i}.txt").write_text("Fixture only, no real persons")
  mp4=root/f"{i}.mp4"
  subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i",
    f"testsrc=size=32x32:rate={12+i}:duration=1",
    "-an","-pix_fmt","yuv420p",str(mp4)],check=True)
  return {"schema":"qaf_open_cinematic_asset_v1","source_id":"blender-sprite-fright",
   "source_url":"https://studio.blender.org/projects/sprite-fright/pages/about/",
   "license_url":"https://creativecommons.org/licenses/by/4.0/",
   "license_id":"CC-BY-4.0","attribution":"synthetic fixture author",
   "reviewer":"fixture reviewer","review_date":"2026-10-22",
   "commercial_training_permission":"documented","consent_reference":f"proof{i}.txt",
   "subject_id":f"synthetic_subject_{i}","garment_id":f"synthetic_garment_{i}",
   "clip":f"{i}.mp4","reference_image":f"{i}.png",
   "reviewed_for_training":True,"explicit_restrictions_resolved":True,
   "scope":"commercial_video_model","id":str(i),"split":split,
   "fps":12,"training_frame_count":13,"prompt":"synthetic patterned video"}
 def test_block_pexels_and_openvid(self):
  with tempfile.TemporaryDirectory() as tmp:
   for source in ("pexels-api","openvid-1m","ucf101"):
    with self.assertRaises(ValueError):audit_asset({"schema":"qaf_open_cinematic_asset_v1","source_id":source},tmp)
 def test_source_requires_review(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);a=self.fixture(root,0,"train")
   a["reviewed_for_training"]=False
   with self.assertRaisesRegex(ValueError,"review"):audit_asset(a,root)
 def test_manifest_and_compatible_decoder(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);a=self.fixture(root,0,"train");b=self.fixture(root,1,"val")
   r=compile_training_manifest(root,[a,b],"dataset.json")
   self.assertEqual(r["samples"],2)
   self.assertEqual(video_proxy_metrics(root/"0.mp4")["frames_evaluated"],8)
   self.assertEqual(json.loads((root/"dataset.json").read_text())["schema"],"qaf_cinematic_training_dataset_v1")
 def test_paired_benchmark_is_proxy_not_proof(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.fixture(root,0,"train");self.fixture(root,1,"val")
   d={"schema":"qaf_video_paired_benchmark_v1","pairs":[
       {"id":"x","seed":22,"scene":"synthetic","qaf":"0.mp4","baseline":"1.mp4"}]}
   m=root/"pairs.json";m.write_text(json.dumps(d))
   r=matched_video_benchmark(root,m,boots=100)
   self.assertFalse(r["cinematic_superiority_proven"])
   self.assertEqual(r["pairs"],1)
