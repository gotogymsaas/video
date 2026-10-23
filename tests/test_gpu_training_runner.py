import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from qaf_video.generative_research.gpu_training_runner import training_execution
def make_fixture(root):
 d=root/"clips";d.mkdir()
 samples=[]
 for i,split in enumerate(("train","val","test")):
  (d/f"{i}.mp4").write_bytes(("fixture"+str(i)).encode())
  samples.append({"split":split,"subject_id":str(i),"garment_id":str(i),
   "video":f"clips/{i}.mp4","prompt":"Synthetic action","rights":"controlled synthetic",
   "consent_record":"synthetic fixture"})
 (root/"dataset.json").write_text(json.dumps({"schema":"qaf_cinematic_training_dataset_v1","samples":samples}))
 (root/"license.txt").write_text("SYNTHETIC")
 (root/"models").mkdir()
 for name in ("transformer","text_encoder","video_vae"):(root/"models"/name).write_text("synthetic model")
 (root/"trainer/scripts").mkdir(parents=True)
 for name in ("train.py","process_dataset.py"):(root/"trainer/scripts"/name).write_text("pass")
 (root/"train.yaml").write_text("test_only: true")
 job={"schema":"qaf_neural_program_v1","dataset_manifest":"dataset.json",
    "legal_review":"license.txt","trainer_dir":"trainer","trainer_config":"train.yaml",
    "approved_to_train":True,"backbone":"LTX-2.5","training_mode":"i2v_lora",
    "max_gpu_hours":1,"model_files":{k:"models/"+k for k in
    ("transformer","text_encoder","video_vae")}}
 (root/"program.json").write_text(json.dumps(job))
\nclass TestGPURunner(unittest.TestCase):
 def test_no_involuntary_training_when_disabled(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);make_fixture(root)
   with patch("qaf_video.generative_research.gpu_training_runner.subprocess.run") as mocked:
    result=training_execution("program.json",root,root/"run",execute=False)
    self.assertEqual(result["status"],"DRY_RUN_ONLY")
    self.assertFalse(result["gpu_training_completed"])
    mocked.assert_not_called()
 def test_explicit_training_requires_env_approval(self):
  from tests.test_neural_program import TestNeuralProgram
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);TestNeuralProgram().fixture(root)
   with patch.dict("os.environ",{"QAF_CINEMA_ALLOW_GPU_TRAINING":""}):
    with self.assertRaisesRegex(ValueError,"ALLOW_GPU"):
     training_execution("program.json",root,root/"run",execute=True)
