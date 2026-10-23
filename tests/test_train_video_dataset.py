"""Private microtrainer: only executes with optional PyTorch and FFmpeg."""
import importlib.util, tempfile, unittest, json, shutil, subprocess
from pathlib import Path
from PIL import Image
HAS_TORCH=importlib.util.find_spec("torch") is not None
if HAS_TORCH:
 from qaf_video.generative_research.train_video_dataset import check_manifest,train_micro_dataset
@unittest.skipUnless(HAS_TORCH and shutil.which("ffmpeg"),"optional CUDA/CPU training test")
class TestPrivateTrain(unittest.TestCase):
 def fixture(self,root):
  samples=[]
  for i,split in enumerate(("train","val","test")):
   Image.new("RGB",(32,32),(i*45,20,20)).save(root/f"{i}.png")
   subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i",
      f"color=c=0x{i+2}02040:s=32x32:r=12:d=1","-pix_fmt","yuv420p",str(root/f"{i}.mp4")],check=True)
   samples.append({"id":str(i),"split":split,"subject_id":str(i),"garment_id":"g"+str(i),
    "rights":"test fixture","consent_record":"no real persons","prompt":"solid color",
    "reference_image":f"{i}.png","video":f"{i}.mp4","fps":12,"training_frame_count":5})
  file=root/"dataset.json"
  file.write_text(json.dumps({"schema":"qaf_cinematic_training_dataset_v1","samples":samples}))
  return file
 def test_micro_training(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.fixture(root)
   report=train_micro_dataset(manifest,root/"out",steps=2)
   self.assertFalse(report["cinematic_model_trained"])
   self.assertTrue((root/"out/authorized_micro_model.pt").is_file())
 def test_split_protection(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.fixture(root)
   data=json.loads(manifest.read_text())
   data["samples"][1]["subject_id"]=data["samples"][0]["subject_id"]
   manifest.write_text(json.dumps(data))
   with self.assertRaisesRegex(ValueError,"leakage"):check_manifest(manifest)
