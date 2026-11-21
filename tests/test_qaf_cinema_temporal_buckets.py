"""Offline tests for QAF Cinema LTX temporal windows (no Azure or real videos)."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.qaf_cinema_temporal_buckets import (
    plan_pairs, render_pairs, require_bucket, sha256,
)


class TestTemporalBuckets(unittest.TestCase):
    def fixture(self, path):
        root = Path(path)
        (root / "targets").mkdir()
        (root / "guides").mkdir()
        (root / "targets" / "001.mp4").write_bytes(b"original-target-data")
        (root / "guides" / "001.mp4").write_bytes(b"original-reference-data")
        spec = root / "pairs.json"
        spec.write_text(json.dumps({
            "schema": "qaf_ltx_v2v_control_pairs_v1",
            "control_type": "pose",
            "pairs": [{
                "target": "targets/001.mp4",
                "reference": "guides/001.mp4",
                "target_sha256": sha256(root / "targets" / "001.mp4"),
                "reference_sha256": sha256(root / "guides" / "001.mp4"),
                "prompt": "Human movement, same timing",
                "qaf_pose": {
                    "schema": "qaf_pose_evidence_8d_v1",
                    "vector": [0.8, 0.9, 0.25, 0.01, 0.02, 0.005, 0.002, 0.001],
                    "not_a_trained_ltx_condition": True,
                },
            }],
        }), encoding="utf-8")
        return spec

    def probe(self, path):
        return {"frames": 192, "width": 544, "height": 960, "fps": "24"}

    def test_121_is_supported_and_192_is_not(self):
        require_bucket(121)
        require_bucket(49)
        with self.assertRaisesRegex(ValueError, "8N_PLUS_ONE"):
            require_bucket(192)
        with self.assertRaisesRegex(ValueError, "8N_PLUS_ONE"):
            require_bucket(186)

    def test_plan_uses_real_frames_without_padding_or_gpu(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.fixture(directory)
            plan = plan_pairs(spec, directory, probe=self.probe)
            self.assertEqual(plan["bucket"], 121)
            self.assertEqual(plan["rows"][0]["start_frame"], 0)
            self.assertFalse(plan["training_approved"])
            self.assertTrue(plan["rows"][0]["qaf_evidence_available"])
            self.assertFalse(plan["rows"][0]["independent_training_rights_verified"])

    def test_short_clip_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.fixture(directory)
            def probe(path):
                return dict(self.probe(path), frames=120)
            with self.assertRaisesRegex(ValueError, "NOT_ENOUGH_REAL_FRAMES"):
                plan_pairs(spec, directory, probe=probe)

    def test_invalid_temporal_offset_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.fixture(directory)
            with self.assertRaisesRegex(ValueError, "NOT_ENOUGH_REAL_FRAMES"):
                plan_pairs(spec, directory, start_frame=72, probe=self.probe)

    def test_pair_fps_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.fixture(directory)
            def probe(path):
                data = self.probe(path)
                if "guides" in str(path):
                    data["fps"] = "25"
                return data
            with self.assertRaisesRegex(ValueError, "SOURCE_PAIR_TEMPORAL"):
                plan_pairs(spec, directory, probe=probe)

    def test_cryptographic_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.fixture(directory)
            data = json.loads(spec.read_text())
            data["pairs"][0]["reference_sha256"] = "0" * 64
            spec.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "SOURCE_REFERENCE_HASH"):
                plan_pairs(spec, directory, probe=self.probe)

    def test_invalid_qaf_vector_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.fixture(directory)
            data = json.loads(spec.read_text())
            data["pairs"][0]["qaf_pose"]["vector"] = [1.0] * 7
            spec.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "INVALID_QAF_METADATA"):
                plan_pairs(spec, directory, probe=self.probe)

    def test_baseline_without_qaf_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.fixture(directory)
            data = json.loads(spec.read_text())
            del data["pairs"][0]["qaf_pose"]
            spec.write_text(json.dumps(data))
            plan = plan_pairs(spec, directory, probe=self.probe)
            self.assertFalse(plan["rows"][0]["qaf_evidence_available"])

    def test_private_render_emits_rehashed_pairs_for_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private"
            private.mkdir()
            spec = self.fixture(private)
            plan = plan_pairs(spec, private, probe=self.probe)
            def mock_encoder(source, dest, start, frames, fps):
                self.assertEqual(frames, 121)
                self.assertEqual(fps, "24")
                dest.write_bytes(b"window:" + source.read_bytes())
            def mock_probe(path):
                return {"frames": 121, "width": 544, "height": 960, "fps": "24"}
            dest = Path(directory) / "output"
            result = render_pairs(plan, private, dest, encoder=mock_encoder,
                                  probe=mock_probe, guide_checker=lambda path, n: 1.0)
            self.assertEqual(result["windows_verified"], 1)
            self.assertFalse(result["training_approved"])
            generated = json.loads((dest / "pilot-pairs.json").read_text())
            row = generated["pairs"][0]
            self.assertEqual(row["target_sha256"], sha256(dest / row["target"]))
            self.assertEqual(row["reference_sha256"], sha256(dest / row["reference"]))
            self.assertEqual(row["qaf_pose"]["vector"][0], 0.8)

    def test_failed_output_verification_cleans_partial_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private"
            private.mkdir()
            spec = self.fixture(private)
            plan = plan_pairs(spec, private, probe=self.probe)
            dest = Path(directory) / "output"
            def mock_encoder(source, dst, start, frames, fps):
                dst.write_bytes(b"partial-output")
            with self.assertRaisesRegex(ValueError, "BUCKET_OUTPUT_VERIFICATION_FAILED"):
                render_pairs(plan, private, dest, encoder=mock_encoder,
                             probe=self.probe, guide_checker=lambda path, n: 1.0)
            self.assertFalse(dest.exists())


    def test_sparse_guide_fails_closed_even_if_frame_count_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private"
            private.mkdir()
            spec = self.fixture(private)
            plan = plan_pairs(spec, private, probe=self.probe)
            dest = Path(directory) / "output"
            def mock_encoder(source, dst, start, frames, fps):
                dst.write_bytes(b"fake-encoded-video")
            def valid_probe(path):
                return {"frames": 121, "width": 544, "height": 960, "fps": "24"}
            with self.assertRaisesRegex(ValueError, "GUIDE_TOO_SPARSE"):
                render_pairs(plan, private, dest, encoder=mock_encoder,
                             probe=valid_probe, guide_checker=lambda path, n: 0.02)
            self.assertFalse(dest.exists())

    def test_blank_guide_activity_is_not_a_quality_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private"
            private.mkdir()
            spec = self.fixture(private)
            plan = plan_pairs(spec, private, probe=self.probe)
            dest = Path(directory) / "output"
            def mock_encoder(source, dst, start, frames, fps):
                dst.write_bytes(b"fake-encoded-video")
            def valid_probe(path):
                return {"frames": 121, "width": 544, "height": 960, "fps": "24"}
            result = render_pairs(plan, private, dest, encoder=mock_encoder,
                                  probe=valid_probe, guide_checker=lambda path, n: 0.80)
            report = json.loads((dest / "technical-bucket-report.json").read_text())
            self.assertEqual(report["pose_guide_activity_coverage"], {"001": 0.8})
            self.assertTrue(report["guide_activity_is_not_joint_accuracy"])
            self.assertFalse(result["training_approved"])

    def test_render_fails_if_original_was_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private"
            private.mkdir()
            spec = self.fixture(private)
            plan = plan_pairs(spec, private, probe=self.probe)
            (private / "targets" / "001.mp4").write_bytes(b"changed")
            dest = Path(directory) / "output"
            with self.assertRaisesRegex(ValueError, "SOURCE_CHANGED"):
                render_pairs(plan, private, dest, probe=self.probe)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
