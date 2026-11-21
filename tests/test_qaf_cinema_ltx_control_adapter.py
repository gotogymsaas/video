import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.qaf_cinema_ltx_control_adapter import build_manifest, sha256


def evidence():
    return {
        "schema": "qaf_pose_evidence_8d_v1",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        "not_a_trained_ltx_condition": True,
    }


class TestLtxControlAdapter(unittest.TestCase):
    def make_pair(self, root):
        target = root / "target.mp4"
        reference = root / "reference.mp4"
        target.write_bytes(b"target-video")
        reference.write_bytes(b"reference-video")
        spec = root / "pairs.json"
        spec.write_text(json.dumps({
            "schema": "qaf_ltx_v2v_control_pairs_v1",
            "control_type": "pose",
            "pairs": [{
                "target": "target.mp4",
                "reference": "reference.mp4",
                "target_sha256": sha256(target),
                "reference_sha256": sha256(reference),
                "prompt": "A verified pose-guided scene",
                "qaf_pose": evidence(),
            }],
        }), encoding="utf-8")
        return spec

    def test_8d_vector_is_metadata_not_direct_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.make_pair(root)
            info = {"frames": 49, "width": 768, "height": 448, "fps": "24"}
            with patch("scripts.qaf_cinema_ltx_control_adapter.video_info",
                       return_value=info):
                report = build_manifest(spec, root)
        self.assertFalse(report["training_run_executed"])
        self.assertTrue(report["samples"][0]["qaf_8d_not_direct_ltx_condition"])
        self.assertEqual(len(report["samples"][0]["qaf_pose_8d"]), 8)
        self.assertEqual(report["ltx_dataset"][0]["video"], str(root / "target.mp4"))
        self.assertEqual(report["ltx_dataset"][0]["reference_video"], str(root / "reference.mp4"))
        self.assertEqual(report["ltx_dataset"][0]["caption"], "A verified pose-guided scene")

    def test_wrong_target_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.make_pair(root)
            data = json.loads(spec.read_text())
            data["pairs"][0]["target_sha256"] = "0" * 64
            spec.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "TARGET_SHA256_MISMATCH"):
                build_manifest(spec, root)

    def test_reference_and_target_frame_counts_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.make_pair(root)
            with patch("scripts.qaf_cinema_ltx_control_adapter.video_info",
                       side_effect=[{"frames": 49, "width": 768, "height": 448, "fps": "24"},
                                    {"frames": 25, "width": 768, "height": 448, "fps": "24"}]):
                with self.assertRaisesRegex(ValueError, "FRAME_COUNT_MISMATCH"):
                    build_manifest(spec, root)


    def test_wrong_reference_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.make_pair(root)
            data = json.loads(spec.read_text())
            data["pairs"][0]["reference_sha256"] = "0" * 64
            spec.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "REFERENCE_SHA256_MISMATCH"):
                build_manifest(spec, root)

    def test_target_reference_fps_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.make_pair(root)
            with patch("scripts.qaf_cinema_ltx_control_adapter.video_info",
                       side_effect=[{"frames": 49, "width": 768, "height": 448, "fps": "24"},
                                    {"frames": 49, "width": 768, "height": 448, "fps": "30"}]):
                with self.assertRaisesRegex(ValueError, "FPS_MISMATCH"):
                    build_manifest(spec, root)

    def test_classical_baseline_without_qaf_evidence_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.make_pair(root)
            data = json.loads(spec.read_text())
            del data["pairs"][0]["qaf_pose"]
            spec.write_text(json.dumps(data))
            with patch("scripts.qaf_cinema_ltx_control_adapter.video_info",
                       return_value={"frames": 49, "width": 768,
                                     "height": 448, "fps": "24"}):
                report = build_manifest(spec, root)
            self.assertIsNone(report["samples"][0]["qaf_pose_8d"])
            self.assertEqual(report["ltx_dataset"][0]["caption"],
                             "A verified pose-guided scene")

    def test_8d_vector_must_not_be_directly_marked_for_ltx(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.make_pair(root)
            data = json.loads(spec.read_text())
            bad = evidence()
            bad["not_a_trained_ltx_condition"] = False
            data["pairs"][0]["qaf_pose"] = bad
            spec.write_text(json.dumps(data))
            with patch("scripts.qaf_cinema_ltx_control_adapter.video_info",
                       return_value={"frames": 49, "width": 768, "height": 448, "fps": "24"}):
                with self.assertRaisesRegex(ValueError, "NOT_MARKED_NON_LTX"):
                    build_manifest(spec, root)
