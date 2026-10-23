import json,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.ltx_dataset_export import (export_ltx25,prepare_ltx25_commands)

class TestLtxDatasetExport(unittest.TestCase):
 def make(self,p):
  samples=[]
  for i,split in enumerate(("train","val","test")):
   Image.new("RGB",(32,32),(20+i*40,0,30)).save(p/f"{i}.png")
   subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i",
      f"testsrc=size=32x32:rate=12:duration={1+i}",
      "-pix_fmt","yuv420p",str(p/f"{i}.mp4")],check=True)
   samples.append({"id":str(i),"split":split,"subject_id":str(i),
                   "garment_id":"g"+str(i),"prompt":"A geometric object moves",
                   "rights":"research fixture","consent_record":"no living persons",
                   "fps":12,"training_frame_count":49,
                   "reference_image":f"{i}.png","video":f"{i}.mp4"})
  file=p/"dataset.json"
  file.write_text(json.dumps({"schema":"qaf_cinematic_training_dataset_v1","samples":samples}))
  return file
 def test_export_official_video_caption_format(self):
  with tempfile.TemporaryDirectory() as p:
   root=Path(p);source=self.make(root)
   result=export_ltx25(source,root/"ltx-export")
   self.assertEqual(result["sample_counts"]["train"],1)
   row=json.loads((root/"ltx-export/train.ltx.json").read_text())[0]
   self.assertEqual(set(row),{"video","caption"})
   self.assertTrue(Path(row["video"]).exists())
   self.assertFalse(result["training_run_executed"])
 def test_reject_incompatible_frame_bucket(self):
  with tempfile.TemporaryDirectory() as p:
   root=Path(p);source=self.make(root)
   with self.assertRaises(ValueError):export_ltx25(source,root/"out",bucket="768x448x48",verify_media=False)
 def test_runner_never_invokes_external_tools(self):
  with tempfile.TemporaryDirectory() as p:
   root=Path(p);(root/"scripts").mkdir()
   (root/"scripts/process_dataset.py").write_text("pass")
   (root/"scripts/train.py").write_text("pass")
   for n in ("model.safetensors","gemma.safetensors","video.safetensors","audio.safetensors","license.txt"):
    (root/n).write_bytes(b"test")
   export=root/"report.json"
   export.write_text(json.dumps({"schema":"qaf_ltx_data_export_report_v1",
                 "bucket":"768x448x49","metadata_files":{"train":"dataset.json"}}))
   r=prepare_ltx25_commands(root,export,*(root/n for n in
      ("model.safetensors","gemma.safetensors","video.safetensors","audio.safetensors","license.txt")))
   self.assertTrue(r["not_executed"])
   self.assertEqual(r["preprocess_argv"]["train"][:3],["uv","run","python"])
