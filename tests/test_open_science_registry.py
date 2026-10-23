import unittest
from pathlib import Path
from qaf_video.generative_research.open_science_registry import read_registry
class TestOpenScienceRegistry(unittest.TestCase):
 def test_all_papers_mapped_to_primary_baselines(self):
  report=read_registry(Path(__file__).resolve().parent.parent)
  self.assertEqual(report["registered"],24)
  self.assertEqual(report["independently_validated"],0)
  self.assertFalse(report["real_cinematic_superiority_demonstrated"])
