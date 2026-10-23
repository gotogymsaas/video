import tempfile,unittest,json
from pathlib import Path
from qaf_video.generative_research.program_audit import PAPERS,audit_program
class TestQafProgramAudit(unittest.TestCase):
 def test_all_24_papers_are_versioned(self):
  self.assertEqual(len(PAPERS),24)
  audit=audit_program(Path(__file__).resolve().parent.parent)
  self.assertEqual(audit["documented_papers"],24)
  self.assertEqual(audit["missing_documentation"],[])
  self.assertTrue(all(audit["software_gates"].values()))
  self.assertFalse(audit["program_100_percent_verified"])
 def test_never_claim_real_cinema_from_synthetic_manifest(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   docs=root/"docs/generative_research/foundation_24";docs.mkdir(parents=True)
   for paper in PAPERS:(docs/(paper+"_proof.md")).write_text("Proposal only")
   evidence=root/"evidence.json"
   evidence.write_text(json.dumps({"schema":"qaf_cinematic_evidence_v1",
     "dataset_origin":"synthetic","model_type":"synthetic_smoke_only",
     "validated_papers":list(PAPERS),"real_video_training":True,
     "matched_budget_baseline":True,"ood_evaluation":True,"reviewer_approved":True}))
   a=audit_program(root,evidence)
   self.assertFalse(a["program_100_percent_verified"])
   self.assertTrue(any("Synthetic" in x for x in a["blocked_reasons"]))
 def test_empty_repository_has_no_completion(self):
  with tempfile.TemporaryDirectory() as d:
   a=audit_program(d)
   self.assertEqual(a["documented_papers"],0)
   self.assertFalse(a["program_100_percent_verified"])
