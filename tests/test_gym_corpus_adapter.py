import unittest,json,tempfile
from pathlib import Path
from qaf_video.generative_research.gym_corpus_adapter import materialize
class TestGymCorpusAdapter(unittest.TestCase):
 def test_requires_individual_consent(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);p="Videos_test_gimnasio/squat.mp4"
   (root/"Videos_test_gimnasio").mkdir();(root/p).write_bytes(b"synthetic fixture")
   inventory={"schema":"qaf_cross_repo_candidate_corpus_v1","files":[{"source_path":p,"size_bytes":17}]}
   (root/"inventory.json").write_text(json.dumps(inventory))
   approvals={"schema":"qaf_gym_corpus_approvals_v1","approved":[
    {"source_path":p,"training_rights_documented":False,
     "participant_consent_documented":False}]}
   (root/"approvals.json").write_text(json.dumps(approvals))
   with self.assertRaises(ValueError):
    materialize(root/"inventory.json",root/"approvals.json",root,root/"out.json")
   self.assertFalse((root/"out.json").exists())
