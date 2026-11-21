import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.qaf_cinema_pose_guide import build_pose_guide, sha256


class TestPoseGuide(unittest.TestCase):
    def make_files(self, root):
        target = root / "target.mp4"
        target.write_bytes(b"target-source")
        observation = root / "observation.json"
        observation.write_text(json.dumps({
            "schema": "qaf_cinematic_observations_v1",
            "width": 540,
            "height": 960,
            "frames": 2,
            "source_mp4_sha256": sha256(target),
            "timeline": [
                {"frame": 0, "pose": [{"joint_id": 11, "x": 0.5, "y": 0.5, "confidence": 0.9},
                                       {"joint_id": 12, "x": 0.6, "y": 0.5, "confidence": 0.9}]},
                {"frame": 1, "pose": [{"joint_id": 11, "x": 0.5, "y": 0.5, "confidence": 0.9},
                                       {"joint_id": 12, "x": 0.6, "y": 0.5, "confidence": 0.9}]},
            ],
        }), encoding="utf-8")
        return target, observation

    def test_source_hash_and_metadata_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, observation = self.make_files(root)
            data = json.loads(observation.read_text())
            data["source_mp4_sha256"] = "a" * 64
            observation.write_text(json.dumps(data))
            output = root / "guide.mp4"
            fake_stdin = unittest.mock.MagicMock()
            fake_process = unittest.mock.MagicMock()
            fake_process.stdin = fake_stdin
            fake_process.stderr.read.return_value = b""
            fake_process.wait.return_value = 0
            with patch("scripts.qaf_cinema_pose_guide.subprocess.Popen",
                       return_value=fake_process):
                with patch("scripts.qaf_cinema_pose_guide.sha256",
                           side_effect=lambda path: "a" * 64 if Path(path).name.endswith(".mp4") else "b" * 64):
                    report = build_pose_guide(observation, output, target,
                                              width=544, height=960, fps=24)
            self.assertFalse(report["training_run_executed"])
            self.assertTrue(report["named_pose_only"])
            self.assertFalse(report["cinematic_detail_restored"])

    def test_wrong_source_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, observation = self.make_files(root)
            data = json.loads(observation.read_text())
            data["source_mp4_sha256"] = "0" * 64
            observation.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "SOURCE_SHA256_MISMATCH"):
                build_pose_guide(observation, root / "guide.mp4", target,
                                 width=544, height=960, fps=24)

    def test_guide_geometry_can_normalize_observation_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, observation = self.make_files(root)
            data = json.loads(observation.read_text())
            data["source_mp4_sha256"] = "a" * 64
            observation.write_text(json.dumps(data))
            output = root / "guide.mp4"
            fake_process = unittest.mock.MagicMock()
            fake_process.stdin = unittest.mock.MagicMock()
            fake_process.stderr.read.return_value = b""
            fake_process.wait.return_value = 0
            with patch("scripts.qaf_cinema_pose_guide.subprocess.Popen",
                       return_value=fake_process):
                with patch("scripts.qaf_cinema_pose_guide.sha256",
                           return_value="a" * 64):
                    report = build_pose_guide(observation, output, target,
                                              width=544, height=960, fps=24)
            self.assertEqual(report["width"], 544)
            self.assertEqual(report["observation_width"], 540)

    def test_non_monotonic_timeline_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, observation = self.make_files(root)
            data = json.loads(observation.read_text())
            data["timeline"][1]["frame"] = 9
            observation.write_text(json.dumps(data))
            fake_stdin = unittest.mock.MagicMock()
            fake_process = unittest.mock.MagicMock()
            fake_process.stdin = fake_stdin
            with patch("scripts.qaf_cinema_pose_guide.subprocess.Popen",
                       return_value=fake_process):
                with self.assertRaisesRegex(ValueError, "NON_MONOTONIC"):
                    build_pose_guide(observation, root / "guide.mp4", target,
                                     width=544, height=960, fps=24)

    def test_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, observation = self.make_files(root)
            output = root / "guide.mp4"
            output.write_bytes(b"existing")
            with self.assertRaisesRegex(ValueError, "OUTPUT_ALREADY_EXISTS"):
                build_pose_guide(observation, output, target,
                                 width=544, height=960, fps=24)
