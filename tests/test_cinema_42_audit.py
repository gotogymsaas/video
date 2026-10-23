import unittest
from pathlib import Path
from qaf_video.generative_research.audit_42 import audit
class Test42ScientificCoverage(unittest.TestCase):
 def test_full_registry_and_no_unsupported_completion(self):
  result=audit(Path(__file__).resolve().parent.parent)
  self.assertEqual(result["registered"],42)
  self.assertEqual(result["technology_papers"],36)
  self.assertEqual(result["learning_syntheses"],6)
  self.assertEqual(result["scientifically_verified"],0)
  self.assertFalse(result["complete"])
