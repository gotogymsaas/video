import json,tempfile,unittest
from pathlib import Path
from qaf_video.generative_research.neural_program import plan_program,compare_matched_trials
class TestNeuralProgram(unittest.TestCase):
 def fixture(self,root):
  d=root/"clips";d.mkdir()
  samples=[]
  for i,split in enumerate(("train","val","test")):
   (d/f"{i}.mp4").write_bytes(("fixture"+str(i)).encode())
   samples.append({"split":split,"subject_id":str(i),"garment_id":str(i),
      "video":f"clips/{i}.mp4","prompt":"A moving person",
      "rights":"controlled synthetic fixture","consent_record":"synthetic fixture"})
  (root/"dataset.json").write_text(json.dumps({"schema":"qaf_cinematic_training_dataset_v1","samples":samples}))
  (root/"license.txt").write_text("SYNTHETIC TEST ONLY")
  (root/"models").mkdir()
  for name in ("transformer","text_encoder","video_vae"):(root/"models"/name).write_text("SYNTHETIC")
  (root/"trainer/scripts").mkdir(parents=True)
  (root/"trainer/scripts/train.py").write_text("pass")
  (root/"trainer/scripts/process_dataset.py").write_text("pass")
  (root/"train.yaml").write_text("test_only: true")
  job={"schema":"qaf_neural_program_v1","dataset_manifest":"dataset.json","legal_review":"license.txt",
       "trainer_dir":"trainer","trainer_config":"train.yaml","approved_to_train":True,
       "backbone":"LTX-2.5","training_mode":"i2v_lora","max_gpu_hours":1,
       "model_files":{k:"models/"+k for k in ("transformer","text_encoder","video_vae")}}
  (root/"program.json").write_text(json.dumps(job))
  return job
 def test_dry_run_preflight_only(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.fixture(root)
   r=plan_program("program.json",root)
   self.assertFalse(r["training_performed"])
   self.assertEqual(r["split_counts"]["test"],1)
 def test_leakage_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.fixture(root)
   p=root/"dataset.json";d=json.loads(p.read_text())
   d["samples"][1]["subject_id"]="0";p.write_text(json.dumps(d))
   with self.assertRaisesRegex(ValueError,"leakage"):plan_program("program.json",root)
 def test_human_benchmark_is_not_auto_certified(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for n in ("q1.mp4","b1.mp4","q2.mp4","b2.mp4"):(root/n).write_bytes(b"fixture")
   records=[]
   for i in (1,2):
    records.append({"id":str(i),"seed":i,"same_backbone":True,
      "same_compute_budget":True,"blind_review":True,
      "qaf":{"video":f"q{i}.mp4","human_score":7.0},
      "baseline":{"video":f"b{i}.mp4","human_score":6.0}})
   (root/"pair.json").write_text(json.dumps({"schema":"qaf_cinema_matched_trials_v1","trials":records}))
   r=compare_matched_trials("pair.json",root)
   self.assertFalse(r["qaf_superiority_proven"])
   self.assertEqual(r["pairs"],2)
