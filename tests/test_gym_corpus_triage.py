import json,tempfile,unittest
from pathlib import Path
from qaf_video.generative_research.gym_corpus_triage import plan
class TestGymTriage(unittest.TestCase):
 def test_classifier_does_not_auto_approve(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);inv={"schema":"qaf_cross_repo_candidate_corpus_v1",
     "source_repository":"gotogymsaas/appdesplegada","source_tree_sha":"a"*40,
     "files":[{"source_path":"Videos_test_gimnasio/plank.mp4",
       "size_bytes":300,"git_blob_sha":"b"*40},
       {"source_path":"Videos_test_gimnasio/WhatsApp Video 2026.mp4",
       "size_bytes":200,"git_blob_sha":"b"*40}]}
   path=root/"inventory.json";path.write_text(json.dumps(inv))
   r=plan(path)
   self.assertEqual(r["candidate_count"],2)
   self.assertEqual(r["named_exercise_candidates"],1)
   self.assertEqual(len(r["git_exact_duplicate_groups"]),1)
   self.assertFalse(any(row["eligible_for_training"] for row in r["clips"]))
   self.assertFalse(r["rights_review_performed"])
