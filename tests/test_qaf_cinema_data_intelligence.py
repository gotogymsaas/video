"""Unit tests for offline QAF Cinema Data Intelligence. No Azure or video downloads."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/qaf_cinema_data_intelligence.py"
SPEC = importlib.util.spec_from_file_location("qaf_cinema_data_intelligence", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def named_pose(frames=6):
    timeline = []
    for index in range(frames):
        coords = {11: (.25 + .002 * index, .22), 12: (.70, .22),
                  23: (.30 + .01 * index, .55), 24: (.65, .55),
                  25: (.29 + .01 * index, .72), 26: (.66, .72),
                  27: (.29 + .01 * index, .90), 28: (.66, .90)}
        pose = [{"joint_id": joint, "x": x, "y": y, "confidence": .95}
                for joint, (x, y) in coords.items()]
        timeline.append({"frame": index, "pose": pose})
    return {"schema": "qaf_cinematic_observations_v1", "timeline": timeline,
            "width": 960, "height": 540, "frames": frames}


def textured_frame():
    return bytes(130 + (20 if (x // 3 + y // 3) % 2 else -20)
                 for y in range(module.H) for x in range(module.W))


class TestDataIntelligence(unittest.TestCase):
    def test_path_escape_and_absolute_path_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for bad in ("../private.mp4", "/tmp/somewhere.mp4", ""):
                with self.assertRaises(ValueError):
                    module.inside(directory, bad)

    def test_quality_proxies_are_not_a_quality_certificate(self):
        stats = module.sample_metrics([textured_frame()] * 4)
        self.assertEqual(stats["frames_sampled"], 4)
        self.assertGreater(stats["spatial_gradient_proxy"], 0)
        self.assertEqual(stats["sampled_frame_difference_proxy"], 0)

    def test_real_named_pose_yields_evidence_not_model_weights(self):
        features = module.qaf_structural_features(named_pose())
        self.assertTrue(features["available"])
        self.assertEqual(len(features["vector"]), 8)
        self.assertTrue(features["not_a_trained_ltx_condition"])
        self.assertGreater(features["vector"][4], 0)

    def test_unlabeled_legacy_landmarks_do_not_invent_joint_ids(self):
        sample = named_pose()
        for frame in sample["timeline"]:
            for joint in frame["pose"]:
                del joint["joint_id"]
        features = module.qaf_structural_features(sample)
        self.assertFalse(features["available"])
        self.assertIsNone(features["vector"])

    def test_invalid_frame_order_and_duplicate_joint_are_blocked(self):
        bad = named_pose()
        bad["timeline"][2]["frame"] = 20
        with self.assertRaises(ValueError):
            module.qaf_structural_features(bad)
        bad = named_pose()
        bad["timeline"][0]["pose"].append(dict(bad["timeline"][0]["pose"][0]))
        with self.assertRaises(ValueError):
            module.qaf_structural_features(bad)

    def test_missing_bone_edges_fails_closed(self):
        sample = named_pose()
        for frame in sample["timeline"]:
            frame["pose"] = [dict(joint, joint_id=idx)
                             for idx, joint in enumerate(frame["pose"][:4], start=0)]
        result = module.qaf_structural_features(sample)
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "NO_STABLE_BONE_EDGES")

    def test_inspect_clip_never_auto_approves_and_uses_qaf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "clip.mp4"
            file.write_bytes(b"synthetic test fixture - no real video")
            observations = root / "pose.json"
            evidence = named_pose()
            evidence["source_mp4_sha256"] = module.digest(file)
            observations.write_text(json.dumps(evidence), encoding="utf-8")
            result = module.inspect_clip(
                file, observations,
                probe_fn=lambda path: {"width": 1920, "height": 1080,
                                       "duration_seconds": 6, "codec": "h264"},
                frames_fn=lambda path: [textured_frame()] * 5)
            self.assertEqual(result["state"], "REVIEW_REQUIRED")
            self.assertTrue(result["motion_review_candidate"])
            self.assertTrue(result["visual_review_candidate"])
            self.assertFalse(result["training_approved"])
            self.assertEqual(result["qaf_pose"]["schema"], "qaf_pose_evidence_8d_v1")

    def test_bad_observation_source_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clip = root / "clip.mp4"
            clip.write_bytes(b"source-A")
            obs = root / "001.json"
            evidence = named_pose()
            evidence["source_mp4_sha256"] = "0" * 64
            obs.write_text(json.dumps(evidence), encoding="utf8")
            result = module.inspect_clip(
                clip, obs,
                probe_fn=lambda p: {"width": 1920, "height": 1080, "duration_seconds": 5},
                frames_fn=lambda p: [textured_frame()] * 5)
            self.assertEqual(result["state"], "TECHNICAL_FAILURE")
            self.assertFalse(result["training_approved"])

    def test_low_light_is_flagged_even_with_high_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "dark.mp4"
            file.write_bytes(b"synthetic")
            report = module.inspect_clip(
                file,
                probe_fn=lambda path: {"width": 1920, "height": 1080,
                                       "duration_seconds": 5, "codec": "h264"},
                frames_fn=lambda path: [bytes(module.W * module.H)] * 5)
            self.assertFalse(report["visual_review_candidate"])
            self.assertIn("DARK_OR_CRUSHED_SHADOWS_PROXY", report["flags"])

    def test_inventory_does_not_mark_missing_media_as_training_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "media").mkdir()
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({
                "schema": "qaf_cross_repo_candidate_corpus_v1",
                "files": [{"source_path": "Video/A.mp4"},
                          {"source_path": "Video/B.mp4"}]}), encoding="utf-8")
            report = module.audit(inventory, root / "media")
            self.assertEqual(report["scope"]["examined"], 2)
            self.assertEqual(report["summary"]["missing"], 2)
            self.assertEqual(report["summary"]["motion_review_candidates"], 0)
            self.assertTrue(report["all_training_unapproved"])

    def test_inventory_rejects_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({
                "schema": "qaf_cross_repo_candidate_corpus_v1",
                "files": [{"source_path": "same.mp4"},
                          {"source_path": "same.mp4"}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                module.audit(inventory, root)


if __name__ == "__main__":
    unittest.main()
