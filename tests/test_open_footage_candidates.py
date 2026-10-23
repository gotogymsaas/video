import json,unittest
from pathlib import Path
class TestOpenFootageCandidates(unittest.TestCase):
 def test_all_public_candidates_are_pending_review(self):
  root=Path(__file__).resolve().parent.parent
  data=json.loads((root/"docs/generative_research/open_science/candidate_corpus.json").read_text())
  self.assertEqual(data["schema"],"qaf_cinematic_open_footage_candidates_v1")
  self.assertGreaterEqual(len(data["sources"]),3)
  for row in data["sources"]:
   self.assertFalse(row["automatically_allowed"])
   self.assertTrue(row["file_page"].startswith("https://commons.wikimedia.org/wiki/File:"))
   self.assertTrue(row["must_check"])
