import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from qaf_video.generative_research.gpu_training_runner import training_execution
class TestGPURunner(unittest.TestCase):
 def test_no_involuntary_training_when_disabled(self):
  from tests.test_neural_program import TestNeuralProgram
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);TestNeuralProgram().fixture(root)
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
