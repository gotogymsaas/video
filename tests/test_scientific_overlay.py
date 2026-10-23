import json,tempfile,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.scientific_overlay import validate_claims,render_overlay
class TestScientificOverlay(unittest.TestCase):
 def sample(self):
  return {"schema":"qaf_scientific_overlay_v1","claims":[{"id":"rest",
   "label":"Descanso registrado","value":7.5,"unit":"hours",
   "evidence_class":"user_reported","source_record":"private-note-032",
   "observed_at":"2026-10-22","asserts_diagnosis":False,"asserts_treatment":False}]}
 def test_render_declared_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   Image.new("RGB",(640,320),(10,20,31)).save(p/"back.png")
   (p/"claim.json").write_text(json.dumps(self.sample()))
   result=render_overlay(p/"back.png",p/"claim.json",p/"out.png")
   self.assertEqual(result["claims"],1)
   self.assertFalse(result["clinical_assertions_generated"])
   self.assertTrue((p/"out.png").is_file())
 def test_blocks_unsubstantiated_diagnosis(self):
  data=self.sample();data["claims"][0]["asserts_diagnosis"]=True
  with self.assertRaises(ValueError):validate_claims(data)
 def test_blocks_invalid_unit_and_number(self):
  data=self.sample();data["claims"][0]["unit"]="joint_regeneration"
  with self.assertRaises(ValueError):validate_claims(data)
  data=self.sample();data["claims"][0]["value"]="12"
  with self.assertRaises(ValueError):validate_claims(data)
