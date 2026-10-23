import tempfile,json,unittest
from pathlib import Path
from PIL import Image
from qaf_video.generative_research.editorial_timeline import load_timeline,quad_at,claims_at
class TestEditorialTimeline(unittest.TestCase):
 def test_exact_quad_interpolation_and_privacy(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"timeline.json"
   obj={"schema":"qaf_editorial_timeline_v1","frames":4,"width":128,"height":128,
   "phone_keyframes":[{"frame":0,"quad":[[10,10],[40,10],[40,90],[10,90]]},
    {"frame":3,"quad":[[20,10],[50,10],[50,90],[20,90]]}],
   "claim_events":[{"start":1,"end":3,"privacy_approved":True,"claim":{
    "id":"activity","label":"Actividad declarada","value":3,"unit":"hours",
    "evidence_class":"user_reported","source_record":"private-evidence-1",
    "observed_at":"2026-10-23","asserts_diagnosis":False,"asserts_treatment":False}}]}
   p.write_text(json.dumps(obj));data,_=load_timeline(p,4,128,128)
   self.assertAlmostEqual(quad_at(data,1)[0][0],13.3333333)
   blank=Image.new("RGB",(128,128))
   self.assertNotEqual(claims_at(blank,data,1).tobytes(),blank.tobytes())
   obj["claim_events"][0]["privacy_approved"]=False;p.write_text(json.dumps(obj))
   with self.assertRaises(ValueError):load_timeline(p,4,128,128)
