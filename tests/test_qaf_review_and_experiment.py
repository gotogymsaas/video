import json
import tempfile
import unittest
from pathlib import Path

from qaf_video.generative_research.review_and_experiment import (
    build_approved_split,
    build_matched_experiment_plan,
    create_review_registry,
)


class TestReviewAndExperiment(unittest.TestCase):
    def test_review_registry_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({
                "schema": "qaf_cross_repo_candidate_corpus_v1",
                "files": [{
                    "source_path": "Videos_test_gimnasio/plank.mp4",
                    "size_bytes": 123,
                    "git_blob_sha": "a" * 40,
                }],
            }))
            output = root / "review.json"
            registry = create_review_registry(inventory, output)
            self.assertTrue(output.is_file())
            self.assertFalse(registry["human_training_approval"])
            self.assertEqual(registry["rows"][0]["human_review_status"], "PENDING")
            self.assertIsNone(registry["rows"][0]["private_sha256"])

    def test_split_requires_all_approvals_and_blocks_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = root / "inventory.json"
            files = [{"source_path": f"Videos_test_gimnasio/plank-{i}.mp4",
                      "size_bytes": 123 + i, "git_blob_sha": f"{i:040x}"}
                     for i in range(300)]
            inventory.write_text(json.dumps({
                "schema": "qaf_cross_repo_candidate_corpus_v1",
                "files": files,
            }))
            registry = root / "review.json"
            result = create_review_registry(inventory, registry)
            data = result
            for index, row in enumerate(data["rows"]):
                row.update({
                    "human_review_status": "APPROVED",
                    "rights_review_status": "APPROVED",
                    "participant_consent_status": "APPROVED",
                    "commercial_training_permission": "APPROVED",
                    "technical_review": "PASSED",
                    "human_visual_review": "PASSED",
                    "reviewed_by": "human-reviewer",
                    "review_reference": "record-reference",
                    "actor_group": f"actor-{index}",
                    "session_group": f"session-{index}",
                    "garment_group": f"garment-{index}",
                    "caption": "A person performs a controlled exercise.",
                    "fps": 24,
                    "training_frame_count": 49,
                })
            registry.write_text(json.dumps(data))
            split = root / "approved.json"
            result = build_approved_split(registry, split)
            self.assertTrue(result["human_training_approval"])
            self.assertFalse(result["rights_independently_certified"])

    def test_no_approved_rows_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({
                "schema": "qaf_cross_repo_candidate_corpus_v1",
                "files": [{"source_path": "Videos_test_gimnasio/plank.mp4",
                           "size_bytes": 123, "git_blob_sha": "a" * 40}],
            }))
            registry = root / "review.json"
            create_review_registry(inventory, registry)
            with self.assertRaisesRegex(ValueError, "No individually approved clips"):
                build_approved_split(registry, root / "approved.json")

    def test_matched_experiment_has_four_non_claiming_arms(self):
        plan = build_matched_experiment_plan([{
            "id": "scene-001",
            "prompt": "A controlled gym movement",
            "source_sha256": "b" * 64,
        }])
        self.assertEqual([arm["id"] for arm in plan["arms"]], ["A", "B", "C", "D"])
        self.assertFalse(plan["training_executed"])
        self.assertFalse(plan["human_evaluation"])
        self.assertFalse(plan["cinematic_superiority_proven"])
        self.assertFalse(plan["qaf_advantage_proven"])
        self.assertEqual(plan["matched_pairs"][0]["seed"], plan["seed"])

    def test_matched_experiment_requires_real_source_hash(self):
        with self.assertRaisesRegex(ValueError, "source SHA-256"):
            build_matched_experiment_plan([{
                "id": "scene-001",
                "prompt": "A controlled gym movement",
            }])


if __name__ == "__main__":
    unittest.main()
