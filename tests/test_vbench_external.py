import tempfile,unittest
from pathlib import Path
from qaf_video.generative_research.vbench_external import vbench_plan,execute_vbench
class TestVbenchExternal(unittest.TestCase):
 def test_dry_run_preflight_and_dimensions(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/"checkout").mkdir();(root/"clips").mkdir()
   (root/"checkout/evaluate.py").write_text("pass")
   (root/"clips/test.mp4").write_bytes(b"synthetic placeholder")
   plan=vbench_plan(root/"checkout",root/"clips",["motion_smoothness"])
   self.assertFalse(plan["executed"])
   self.assertFalse(execute_vbench(plan)["executed"])
   self.assertEqual(plan["source_clips"],1)
 def test_custom_input_rejects_human_action(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/"checkout").mkdir();(root/"clips").mkdir()
   (root/"checkout/evaluate.py").write_text("pass")
   (root/"clips/test.mp4").write_bytes(b"placeholder")
   with self.assertRaisesRegex(ValueError,"unsupported"):
    vbench_plan(root/"checkout",root/"clips",["human_action"])
 def test_custom_has_explicit_mode(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/"checkout").mkdir();(root/"clips").mkdir()
   (root/"checkout/evaluate.py").write_text("pass")
   (root/"clips/test.mp4").write_bytes(b"placeholder")
   result=vbench_plan(root/"checkout",root/"clips",["motion_smoothness"])
   self.assertEqual(result["jobs"][0][-2:],["--mode","custom_input"])
 def test_dimension_injection_fails_closed(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/"checkout").mkdir();(root/"clips").mkdir()
   (root/"checkout/evaluate.py").write_text("pass")
   (root/"clips/test.mp4").write_bytes(b"synthetic placeholder")
   with self.assertRaises(ValueError):
    vbench_plan(root/"checkout",root/"clips",["human_action; rm -rf ."])
