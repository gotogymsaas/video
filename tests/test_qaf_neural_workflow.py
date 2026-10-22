"""Neural readiness, QAF inference gates and safe production bridge."""
import json,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.training_readiness import validate_dataset
from qaf_video.generative_research.production_bridge import ingest_generated_clip
from qaf_video.generative_research.applicability import qaf_applicability

class TestCinematicReadiness(unittest.TestCase):
 def test_qaf_non_identifiability(self):
  r=qaf_applicability([.7]*15,[.7]*15,5,4,10,True)
  self.assertEqual(r["region"],"Non-identifiable")
 def test_cost_breakdown(self):
  r=qaf_applicability([.8]*15,[.7]*15,20,3,10,True)
  self.assertEqual(r["region"],"Computational-breakdown")
 def test_dataset_leakage(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   Image.new("RGB",(16,16)).save(root/"a.png")
   (root/"a.mp4").write_bytes(b"fixture for verify_media=False")
   samples=[]
   for i,split in enumerate(("train","val","test")):
    samples.append({"id":str(i),"split":split,"subject_id":"same-subject" if i<2 else "test",
      "garment_id":"g"+str(i),"reference_image":"a.png","video":"a.mp4",
      "prompt":"a running human","consent_record":"signed/"+str(i),
      "rights":"owner permission","fps":12,"training_frame_count":13})
   manifest=root/"dataset.json";manifest.write_text(json.dumps({"schema":"qaf_cinematic_training_dataset_v1","samples":samples}))
   with self.assertRaisesRegex(ValueError,"leakage|shared"):validate_dataset(manifest,verify_media=False)
 def test_dataset_split_success(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);samples=[]
   for i,split in enumerate(("train","val","test")):
    Image.new("RGB",(16,16),(i*40,20,20)).save(root/f"{i}.png")
    (root/f"{i}.mp4").write_bytes(f"fake-{i}".encode())
    samples.append({"id":str(i),"split":split,"subject_id":"person"+str(i),
      "garment_id":"g"+str(i),"reference_image":f"{i}.png","video":f"{i}.mp4",
      "prompt":"athlete runs outdoors","consent_record":"permissions/"+str(i),
      "rights":"authorized test","fps":12,"training_frame_count":13})
   manifest=root/"dataset.json";manifest.write_text(json.dumps({"schema":"qaf_cinematic_training_dataset_v1","samples":samples}))
   r=validate_dataset(manifest,verify_media=False)
   self.assertEqual(r["samples"],3)
 def test_generated_clip_in_base_project(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/"assets").mkdir()
   Image.new("RGB",(96,96),(20,60,90)).save(root/"assets/still.png")
   clip=root/"assets/generated-source.mp4"
   subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","color=c=blue:s=96x96:r=12:d=2",
                   "-an","-c:v","libx264","-pix_fmt","yuv420p",str(clip)],check=True)
   project={"schema":"qaf_video_project_v1","fps":12,"duration":2,"mode":"conceptual",
      "shots":[{"start":0,"end":2,"kind":"image","asset":"assets/still.png",
                "title":"","body":"","eyebrow":"","claim_ids":[]}],"claims":{},"assets":{},
      "reviews":{"picture":{"approved":True,"reviewer":"old","at":"2026-10-22"}}}
   file=root/"project.json";file.write_text(json.dumps(project))
   proof={"model_id":"local-demo-neural","model_license":"research","input_image":"assets/still.png",
          "rights":"authorized fixture","consent_record":"no persons in fixture",
          "prompt":"abstract blue plane moves","seed":22}
   result=ingest_generated_clip(file,0,"assets/generated-source.mp4",proof)
   self.assertTrue(result["attached"])
   edited=json.loads(file.read_text())
   self.assertEqual(edited["shots"][0]["kind"],"video")
   self.assertFalse(edited["reviews"]["picture"]["approved"])
   self.assertEqual(edited["assets"][result["asset"]]["human_approved"],False)
 def test_missing_provenance_rejected(self):
  with self.assertRaises((ValueError,FileNotFoundError)):
   ingest_generated_clip("missing/project.json",0,"assets/clip.mp4",{})

if __name__=="__main__":unittest.main()
