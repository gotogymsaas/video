"""Offline synthetic tests, not proof of human approval or real media rights."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.qaf_cinema_training_governance import (
    draft_review, experiment_plan, plan, safe_private_output, sha256, write_json_private
)


class TestCinemaGovernance(unittest.TestCase):
    def fixture(self, base, n=12):
        root = Path(base)
        media = root / "media"
        (media / "Videos_test_gimnasio").mkdir(parents=True)
        inventory = root / "inventory.json"
        entries = []
        for i in range(n):
            rel = f"Videos_test_gimnasio/FAKE_CLIP_{i:02}.mp4"
            file = media / rel
            file.write_bytes(f"FAKE_VIDEO_DATA_{i}".encode())
            entries.append({"source_path": rel, "git_blob_sha": f"{i+1:040x}",
                            "size_bytes": file.stat().st_size})
        inventory.write_text(json.dumps({"schema": "qaf_cross_repo_candidate_corpus_v1",
                                         "files": entries}), encoding="utf-8")
        review = draft_review(inventory)
        for i, row in enumerate(review["entries"]):
            row.update({
                "source_sha256": sha256(media / row["source_path"]),
                "review_status": "APPROVED",
                "visual_review": "APPROVED",
                "motion_review": "APPROVED",
                "reviewer": f"SYNTHETIC_REVIEWER_{i}",
                "review_record": f"FAKE_REVIEW_{i}",
                "training_rights_documented": True,
                "training_rights_record": f"FAKE_RIGHTS_{i}",
                "participant_consent_documented": True,
                "consent_record": f"FAKE_CONSENT_{i}",
                "synthetic_likeness_permission_documented": True,
                "likeness_record": f"FAKE_LIKENESS_{i}",
                "minor_status": "NO_MINORS",
                "music_clearance": "NOT_PRESENT",
                "logo_clearance": "NOT_PRESENT",
                "actor_group": f"actor_{i}",
                "session_group": f"session_{i}",
                "garment_group": f"garment_{i}",
                "near_duplicate_status": "CLEARED",
                "caption": f"A synthetic human movement test {i}",
            })
        reviewfile = root / "review.json"
        reviewfile.write_text(json.dumps(review), encoding="utf-8")
        return inventory, reviewfile, media

    def mutate(self, filename, action):
        data = json.loads(filename.read_text())
        action(data["entries"])
        filename.write_text(json.dumps(data), encoding="utf-8")

    def test_template_has_zero_preapproved_rights(self):
        with tempfile.TemporaryDirectory() as d:
            inv, _, _ = self.fixture(d)
            result = draft_review(inv)
            self.assertEqual(len(result["entries"]), 12)
            self.assertTrue(all(x["review_status"] == "PENDING" for x in result["entries"]))
            self.assertTrue(all(not x["training_rights_documented"] for x in result["entries"]))

    def test_draft_can_checksum_real_bytes_without_approving_rights(self):
        with tempfile.TemporaryDirectory() as d:
            inv, _, media = self.fixture(d)
            rows = draft_review(inv, media)["entries"]
            self.assertEqual(len(rows), 12)
            self.assertTrue(all(len(row["source_sha256"]) == 64 for row in rows))
            self.assertTrue(all(row["review_status"] == "PENDING" for row in rows))
            self.assertTrue(all(not row["training_rights_documented"] for row in rows))

    def test_draft_rejects_mismatched_local_files(self):
        with tempfile.TemporaryDirectory() as d:
            inv, _, media = self.fixture(d)
            (media / "Videos_test_gimnasio/FAKE_CLIP_00.mp4").write_bytes(b"wrong size")
            with self.assertRaisesRegex(ValueError, "PRIVATE_MEDIA_SIZE_MISMATCH"):
                draft_review(inv, media)

    def test_clean_groups_produce_three_splits_deterministically(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            a = plan(inv, review, media, seed=17)
            b = plan(inv, review, media, seed=17)
            self.assertEqual(a["samples"], b["samples"])
            self.assertEqual(sum(a["actual_counts"].values()), 12)
            self.assertTrue(all(a["actual_counts"].values()))
            self.assertFalse(a["training_approved_by_this_tool"])
            self.assertFalse(a["gpu_training_executed"])

    def test_actor_session_garment_and_duplicates_cannot_leak(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            def edit(rows):
                rows[0]["actor_group"] = rows[1]["actor_group"]
                rows[2]["session_group"] = rows[3]["session_group"]
                rows[4]["garment_group"] = rows[5]["garment_group"]
                rows[6]["near_duplicate_group"] = "similar_take"
                rows[7]["near_duplicate_group"] = "similar_take"
                rows[6]["near_duplicate_status"] = "GROUPED"
                rows[7]["near_duplicate_status"] = "GROUPED"
            self.mutate(review, edit)
            result = plan(inv, review, media)
            by_path = {row["source_path"]: row["split"] for row in result["samples"]}
            rows = json.loads(review.read_text())["entries"]
            for a, b in ((0, 1), (2, 3), (4, 5), (6, 7)):
                self.assertEqual(by_path[rows[a]["source_path"]],
                                 by_path[rows[b]["source_path"]])

    def test_motion_only_bridge_keeps_indirect_related_visual_clips_together(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            def edit(rows):
                # Clip 1 carries the same actor as visual clip 0 and the
                # same garment as visual clip 2, but is not a training target.
                rows[1]["visual_review"] = "MOTION_ONLY"
                rows[1]["actor_group"] = rows[0]["actor_group"]
                rows[1]["garment_group"] = rows[2]["garment_group"]
            self.mutate(review, edit)
            result = plan(inv, review, media)
            rows = json.loads(review.read_text())["entries"]
            assignments = {row["source_path"]: row["split"] for row in result["samples"]}
            visual0 = rows[0]["source_path"]
            visual2 = rows[2]["source_path"]
            motion1 = rows[1]["source_path"]
            self.assertEqual(assignments[visual0], assignments[visual2])
            self.assertEqual(result["motion_only_provisional_group_splits"][motion1],
                             assignments[visual0])
            self.assertTrue(result["motion_only_use_as_control_requires_separate_review"])

    def test_one_actor_cannot_be_artificially_split(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d, 7)
            self.mutate(review, lambda rows: [
                row.update(actor_group="one_actor_all") for row in rows])
            with self.assertRaisesRegex(ValueError, "INSUFFICIENT_INDEPENDENT_GROUPS"):
                plan(inv, review, media)

    def test_missing_likeness_consent_and_pending_review_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            self.mutate(review, lambda rows:
                        rows[0].update(synthetic_likeness_permission_documented=False))
            with self.assertRaisesRegex(ValueError, "COMMERCIAL_GENERATIVE_TRAINING_RIGHTS"):
                plan(inv, review, media)
            self.mutate(review, lambda rows: rows[0].update(review_status="PENDING"))
            with self.assertRaisesRegex(ValueError, "HUMAN_REVIEW_NOT_COMPLETE"):
                plan(inv, review, media)

    def test_minors_music_and_unreviewed_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            self.mutate(review, lambda rows:
                        rows[0].update(minor_status="UNKNOWN"))
            with self.assertRaisesRegex(ValueError, "MINORS_REQUIRE"):
                plan(inv, review, media)
            self.mutate(review, lambda rows:
                        rows[0].update(minor_status="NO_MINORS",
                                       music_clearance="UNREVIEWED"))
            with self.assertRaisesRegex(ValueError, "UNCLEARED_MUSIC"):
                plan(inv, review, media)
            self.mutate(review, lambda rows:
                        rows[0].update(music_clearance="NOT_PRESENT",
                                       logo_clearance="EXCLUDED_FROM_MODEL"))
            with self.assertRaisesRegex(ValueError, "UNCLEARED_MUSIC"):
                plan(inv, review, media)
            self.mutate(review, lambda rows:
                        rows[0].update(logo_clearance="NOT_PRESENT",
                                       near_duplicate_status="UNREVIEWED"))
            with self.assertRaisesRegex(ValueError, "VISUAL_DUPLICATE_REVIEW"):
                plan(inv, review, media)

    def test_modified_source_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            (media / "Videos_test_gimnasio/FAKE_CLIP_00.mp4").write_bytes(b"replaced")
            with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_DO_NOT_MATCH"):
                plan(inv, review, media)

    def test_incomplete_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            self.mutate(review, lambda rows: rows.pop())
            with self.assertRaisesRegex(ValueError, "INCOMPLETE_CORPUS_REVIEW"):
                plan(inv, review, media)

    def test_motion_only_not_used_as_visual_gradient_target(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            self.mutate(review, lambda rows:
                        rows[0].update(visual_review="MOTION_ONLY"))
            result = plan(inv, review, media)
            self.assertEqual(len(result["samples"]), 11)
            self.assertEqual(len(result["motion_only_excluded_from_gradient_training"]), 1)

    def test_identical_bytes_rejected_as_duplicate_training_source(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            rows = json.loads(review.read_text())
            a = media / rows["entries"][0]["source_path"]
            b = media / rows["entries"][1]["source_path"]
            b.write_bytes(a.read_bytes())
            rows["entries"][1]["source_sha256"] = sha256(b)
            invdata = json.loads(inv.read_text())
            invdata["files"][1]["size_bytes"] = b.stat().st_size
            inv.write_text(json.dumps(invdata), encoding="utf8")
            rows["source_inventory_sha256"] = sha256(inv)
            review.write_text(json.dumps(rows), encoding="utf8")
            with self.assertRaisesRegex(ValueError, "IDENTICAL_VIDEO_DUPLICATE"):
                plan(inv, review, media)

    def test_experiment_matrix_shares_test_cases_and_no_active_gpu_stop(self):
        with tempfile.TemporaryDirectory() as d:
            inv, review, media = self.fixture(d)
            split = plan(inv, review, media)
            exp = experiment_plan(split, (41, 42), 1.0)
            self.assertEqual(len(exp["arms"]), 4)
            self.assertEqual(len(exp["evaluation_cases"]), split["actual_counts"]["test"] * 2)
            self.assertFalse(exp["training_executed"])
            self.assertFalse(exp["hard_stop_implemented"])
            self.assertFalse(exp["qaf_conditioning_implemented_and_validated"])

    def test_private_export_cannot_enter_repo_or_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "private-approval.json"
            write_json_private(path, {"test": True})
            with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                safe_private_output(path)
        repo = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, "INSIDE_PUBLIC_REPOSITORY"):
            safe_private_output(repo / "private-approval.json")


if __name__ == "__main__":
    unittest.main()
