import unittest
from pathlib import Path
from qaf_video.generative_research.plan_106 import audit
class Plan106Tests(unittest.TestCase):
 def test_all_106_accounted_for_without_false_gpu_claims(self):
  path=Path(__file__).resolve().parent.parent/"docs/generative_research/gym_corpus/training_plan_106.json"
  result=audit(path)
  self.assertEqual(result["sources"],106)
  self.assertEqual(result["unreviewed_media"],106)
  self.assertFalse(result["gpu_ready"])
