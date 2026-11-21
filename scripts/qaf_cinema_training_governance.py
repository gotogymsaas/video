"""Private rights-and-groups gate for QAF Cinema, entirely CPU/offline.

Produces a review template from the public source inventory, then accepts
only independently reviewed clips for leakage-safe train/val/test splitting.
Never grants rights, fabricates actor/session groups, downloads media, uploads
observations, deploys to Azure or starts training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

REVIEW_SCHEMA = "qaf_cinema_review_register_v1"
SPLIT_SCHEMA = "qaf_cinema_grouped_splits_v1"
EXPERIMENT_SCHEMA = "qaf_cinema_matched_experiment_plan_v1"
SPLITS = ("train", "val", "test")
ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as data:
        for block in iter(lambda: data.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_private_output(path):
    p = Path(path).resolve()
    if p.is_relative_to(ROOT):
        raise ValueError("PRIVATE_OUTPUT_CANNOT_BE_INSIDE_PUBLIC_REPOSITORY")
    if p.exists():
        raise ValueError("PRIVATE_OUTPUT_ALREADY_EXISTS")
    return p


def read_inventory(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "qaf_cross_repo_candidate_corpus_v1":
        raise ValueError("UNEXPECTED_SOURCE_INVENTORY")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("EMPTY_INVENTORY")
    by_path = {}
    for row in files:
        rel = row.get("source_path")
        digest = row.get("git_blob_sha")
        size = row.get("size_bytes")
        if (not isinstance(rel, str) or not rel.startswith("Videos_test_gimnasio/")
                or Path(rel).is_absolute() or ".." in Path(rel).parts
                or not rel.lower().endswith(".mp4")
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{40}", digest)
                or type(size) is not int or size <= 0 or rel in by_path):
            raise ValueError("INVALID_OR_DUPLICATE_INVENTORY_ENTRY")
        by_path[rel] = row
    return by_path


def draft_review(inventory, media_root=None):
    entries = []
    for rel, row in sorted(read_inventory(inventory).items()):
        checksum = None
        if media_root is not None:
            source = private_source(media_root, rel)
            if source.stat().st_size != row["size_bytes"]:
                raise ValueError("PRIVATE_MEDIA_SIZE_MISMATCH")
            checksum = sha256(source)
        entries.append({
            "source_path": rel, "git_blob_sha": row["git_blob_sha"],
            "source_sha256": checksum, "review_status": "PENDING",
            "visual_review": "PENDING", "motion_review": "PENDING",
            "reviewer": None, "review_record": None,
            "training_rights_documented": False,
            "training_rights_record": None,
            "participant_consent_documented": False,
            "consent_record": None,
            "synthetic_likeness_permission_documented": False,
            "likeness_record": None, "minor_status": "UNKNOWN",
            "music_clearance": "UNREVIEWED",
            "logo_clearance": "UNREVIEWED",
            "actor_group": None, "session_group": None,
            "garment_group": None, "near_duplicate_status": "UNREVIEWED",
            "near_duplicate_group": None, "caption": None,
        })
    return {"schema": REVIEW_SCHEMA, "source_inventory_sha256": sha256(inventory),
            "entries": entries, "all_unreviewed_initially": True,
            "warning": "This template records no actual permission, visual acceptance or completed splits."}


def private_source(root, rel):
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError("PRIVATE_MEDIA_ROOT_NOT_FOUND")
    path = (base / rel).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError("PRIVATE_SOURCE_MISSING_OR_ESCAPES_ROOT")
    return path


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_review(row, expected, media_root):
    if row.get("review_status") == "EXCLUDED":
        if not (nonempty(row.get("reviewer")) and nonempty(row.get("review_record"))):
            raise ValueError("EXCLUSIONS_REQUIRE_HUMAN_REVIEW_RECORD")
        return None
    if row.get("review_status") != "APPROVED":
        raise ValueError("HUMAN_REVIEW_NOT_COMPLETE")
    mandatory = (
        "reviewer", "review_record", "training_rights_record", "consent_record",
        "likeness_record", "actor_group", "session_group", "garment_group", "caption",
    )
    if any(not nonempty(row.get(field)) for field in mandatory):
        raise ValueError("MISSING_HUMAN_RIGHTS_GROUP_OR_CAPTION_EVIDENCE")
    for flag in ("training_rights_documented", "participant_consent_documented",
                 "synthetic_likeness_permission_documented"):
        if row.get(flag) is not True:
            raise ValueError("COMMERCIAL_GENERATIVE_TRAINING_RIGHTS_NOT_VERIFIED")
    if row.get("minor_status") != "NO_MINORS":
        raise ValueError("MINORS_REQUIRE_SEPARATE_LEGAL_REVIEW")
    for field in ("music_clearance", "logo_clearance"):
        if row.get(field) not in ("CLEARED", "NOT_PRESENT"):
            raise ValueError("UNCLEARED_MUSIC_OR_BRAND_ELEMENTS")
    if row.get("visual_review") not in ("APPROVED", "MOTION_ONLY"):
        raise ValueError("VISUAL_REVIEW_NOT_COMPLETE")
    if row.get("motion_review") not in ("APPROVED", "UNSUITABLE"):
        raise ValueError("MOTION_REVIEW_NOT_COMPLETE")
    if row.get("near_duplicate_status") not in ("CLEARED", "GROUPED"):
        raise ValueError("VISUAL_DUPLICATE_REVIEW_REQUIRED")
    if row["near_duplicate_status"] == "GROUPED" and not nonempty(row.get("near_duplicate_group")):
        raise ValueError("NEAR_DUPLICATE_GROUP_REQUIRED")
    digest = row.get("source_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("SOURCE_SHA256_REQUIRED")
    clip = private_source(media_root, row["source_path"])
    if clip.stat().st_size != expected["size_bytes"] or sha256(clip) != digest:
        raise ValueError("SOURCE_BYTES_DO_NOT_MATCH_REVIEW")
    return dict(row)


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def components(rows):
    """Group connected clips by shared actor, session, garment or near-duplicate."""
    uf = UnionFind(len(rows))
    owners = {}
    unique_hash = {}
    for i, row in enumerate(rows):
        digest = row["source_sha256"]
        if digest in unique_hash:
            raise ValueError("IDENTICAL_VIDEO_DUPLICATE_SHOULD_BE_EXCLUDED")
        unique_hash[digest] = i
        for key in ("actor_group", "session_group", "garment_group", "near_duplicate_group"):
            val = row.get(key)
            if val is None:
                continue
            if not nonempty(val):
                raise ValueError("EMPTY_LEAKAGE_GROUP")
            marker = (key, val)
            if marker in owners:
                uf.join(i, owners[marker])
            else:
                owners[marker] = i
    result = {}
    for i, row in enumerate(rows):
        result.setdefault(uf.find(i), []).append(row)
    return list(result.values())


def grouped_split(groups, seed):
    """Deterministic approximation of 80/10/10 without crossing connected groups."""
    if len(groups) < 3:
        raise ValueError("INSUFFICIENT_INDEPENDENT_GROUPS_FOR_THREE_SPLITS")
    count = sum(len(group) for group in groups)
    targets = {"train": count * 0.8, "val": count * 0.1, "test": count * 0.1}
    totals = {split: 0 for split in SPLITS}
    assigned = {}
    ordered = sorted(groups, key=lambda group: (
        -len(group),
        hashlib.sha256((str(seed) + "|" + "|".join(sorted(x["source_path"] for x in group)))
                       .encode("utf-8")).hexdigest(),
    ))
    for i, group in enumerate(ordered):
        remaining = len(ordered) - i
        missing = [split for split in SPLITS if totals[split] == 0]
        allowed = missing if len(missing) == remaining else list(SPLITS)
        # Optimize global target count deviations, then deterministic tie-break.
        choice = min(allowed, key=lambda split: (
            sum(abs(totals[key] + (len(group) if key == split else 0) - targets[key])
                for key in SPLITS),
            SPLITS.index(split),
        ))
        for row in group:
            assigned[row["source_path"]] = choice
        totals[choice] += len(group)
    if any(total == 0 for total in totals.values()):
        raise ValueError("EMPTY_SPLIT")
    return assigned, totals


def plan(inventory, review, media_root, seed=42):
    expected = read_inventory(inventory)
    data = json.loads(Path(review).read_text(encoding="utf-8"))
    if data.get("schema") != REVIEW_SCHEMA:
        raise ValueError("INVALID_REVIEW_SCHEMA")
    if data.get("source_inventory_sha256") != sha256(inventory):
        raise ValueError("STALE_SOURCE_INVENTORY")
    rows = data.get("entries")
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("INCOMPLETE_CORPUS_REVIEW")
    if type(seed) is not int or not 0 <= seed < (2 ** 32):
        raise ValueError("INVALID_SEED")
    seen = set()
    approved, excluded = [], []
    for row in rows:
        path = row.get("source_path")
        if path not in expected or path in seen:
            raise ValueError("UNRECOGNIZED_OR_DUPLICATED_REVIEW_CLIP")
        seen.add(path)
        if row.get("git_blob_sha") != expected[path]["git_blob_sha"]:
            raise ValueError("CHANGED_SOURCE_GIT_BLOB")
        verified = validate_review(row, expected[path], media_root)
        if verified is None:
            excluded.append(path)
        else:
            approved.append(verified)
    if seen != set(expected):
        raise ValueError("MISSING_REVIEWED_CLIPS")
    if len(approved) < 3:
        raise ValueError("TOO_FEW_APPROVED_CLIPS")
    # Use only human-accepted cinematic targets for an LTX visual LoRA pilot.
    visually_approved = [row for row in approved if row["visual_review"] == "APPROVED"]
    if len(visually_approved) < 3:
        raise ValueError("INSUFFICIENT_CINEMATICALLY_APPROVED_CLIPS")
    # Motion-only clips are excluded from gradient targets; may later be independent
    # controls, subject to a separate legal/evaluation protocol.
    rejected_visual = [row["source_path"] for row in approved
                       if row["visual_review"] != "APPROVED"]
    # Build leakage components across ALL approved rows, including MOTION_ONLY.
    # Motion-only sources can bridge a visual actor to another visual garment.
    # If excluded from this graph, an indirect cross-split relation is missed.
    all_groups = components(approved)
    training_groups = [
        [row for row in group if row["visual_review"] == "APPROVED"]
        for group in all_groups
    ]
    training_groups = [group for group in training_groups if group]
    assignment, totals = grouped_split(training_groups, seed)
    motion_control_assignments = {}
    for group in all_groups:
        visual = [row for row in group if row["visual_review"] == "APPROVED"]
        split = assignment[visual[0]["source_path"]] if visual else None
        for row in group:
            if row["visual_review"] == "MOTION_ONLY":
                motion_control_assignments[row["source_path"]] = split
    samples = [
        {"sample_id": hashlib.sha256(row["source_path"].encode()).hexdigest()[:16],
         "source_path": row["source_path"], "source_sha256": row["source_sha256"],
         "split": assignment[row["source_path"]],
         "actor_group": row["actor_group"], "session_group": row["session_group"],
         "garment_group": row["garment_group"],
         "near_duplicate_group": row.get("near_duplicate_group"),
         "prompt": row["caption"], "review_reference": row["review_record"],
         "rights_reference": row["training_rights_record"],
         "consent_reference": row["consent_record"],
         "synthetic_likeness_reference": row["likeness_record"],
         "rights_and_visual_reviewed": True}
        for row in sorted(visually_approved, key=lambda r: r["source_path"])
    ]
    return {
        "schema": SPLIT_SCHEMA, "inventory_sha256": sha256(inventory),
        "private_review_sha256": sha256(review), "seed": seed,
        "approved_cinematic_count": len(samples), "excluded_count": len(excluded),
        "motion_only_excluded_from_gradient_training": rejected_visual,
        "independent_components": len(training_groups),
        "all_approved_components": len(all_groups),
        "motion_only_provisional_group_splits": motion_control_assignments,
        "motion_only_use_as_control_requires_separate_review": True,
        "requested_split_fraction": [0.8, 0.1, 0.1],
        "actual_counts": totals,
        "ratio_warning": "Group sizes can prevent exact 80/10/10; verify component balance.",
        "samples": samples, "gpu_training_executed": False, "model_weights_loaded": False,
        "training_approved_by_this_tool": False,
    }


def experiment_plan(split_plan, seeds=(41, 42, 43), max_gpu_hours=1.0):
    if split_plan.get("schema") != SPLIT_SCHEMA:
        raise ValueError("REQUIRES_VALIDATED_GROUPED_SPLIT")
    if (type(max_gpu_hours) not in (float, int) or
            not math.isfinite(max_gpu_hours) or max_gpu_hours <= 0):
        raise ValueError("INVALID_GPU_HOUR_CAP")
    if not seeds or len(set(seeds)) != len(seeds) or any(type(x) is not int for x in seeds):
        raise ValueError("INVALID_MATCHED_SEEDS")
    test = [row for row in split_plan["samples"] if row["split"] == "test"]
    if not test:
        raise ValueError("HELD_OUT_TEST_SET_REQUIRED")
    common = [{"sample_id": row["sample_id"], "seed": seed,
               "prompt": row["prompt"], "source_sha256": row["source_sha256"]}
              for row in test for seed in seeds]
    return {
        "schema": EXPERIMENT_SCHEMA,
        "evaluation_cases": common,
        "arms": [
            {"name": "A_BASE", "training": "none", "control": "none"},
            {"name": "B_VISUAL_LORA", "training": "visual_lora", "control": "none"},
            {"name": "C_CLASSIC_POSE", "training": "visual_lora", "control": "classical_pose"},
            {"name": "D_QAF_PLAN_POSE", "training": "visual_lora", "control": "qaf_planning_plus_same_pose"},
        ],
        "same_test_cases_and_seeds_all_arms": True,
        "same_lora_checkpoint_for_C_and_D": True,
        "same_inference_settings_required": True,
        "require_independent_blinded_review": True,
        "max_gpu_hours_requested_per_run": max_gpu_hours,
        "hard_stop_implemented": False,
        "quota_approved": False,
        "commercial_rights_certified_by_this_tool": False,
        "pose_raster_pairs_bound_and_verified": False,
        "qaf_conditioning_implemented_and_validated": False,
        "training_executed": False,
        "warning": "Experiment planning only; cannot train or spend GPU without verified quota, reviewed controls, rights and a real hard stop.",
    }


def write_json_private(path, data):
    output = safe_private_output(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    return str(output)


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    sub = arg.add_subparsers(dest="action", required=True)
    draft = sub.add_parser("draft")
    draft.add_argument("--inventory", required=True)
    draft.add_argument("--media-root",
                       help="Optional private original media root; only fills source hashes")
    draft.add_argument("--out", required=True)
    verify = sub.add_parser("plan")
    verify.add_argument("--inventory", required=True)
    verify.add_argument("--review", required=True)
    verify.add_argument("--media-root", required=True)
    verify.add_argument("--out", required=True)
    verify.add_argument("--experiments-out")
    verify.add_argument("--seed", type=int, default=42)
    args = arg.parse_args()
    if args.action == "draft":
        template = draft_review(args.inventory, args.media_root)
        out = write_json_private(args.out, template)
        result = {"review_slots": len(template["entries"]), "reviewed": 0,
                  "rights_approved": 0, "output": out, "training_approved": False}
    else:
        output = plan(args.inventory, args.review, args.media_root, args.seed)
        exp_path = None
        if args.experiments_out:
            # Prevent half-completed file operations by verifying both locations first.
            safe_private_output(args.out)
            safe_private_output(args.experiments_out)
            if Path(args.out).resolve() == Path(args.experiments_out).resolve():
                raise ValueError("EXPERIMENT_OUTPUT_MUST_DIFFER")
            experiment = experiment_plan(output)
            exp_path = write_json_private(args.experiments_out, experiment)
        out = write_json_private(args.out, output)
        result = {"private_grouped_manifest": out, "experiment_plan": exp_path,
                  "split_counts": output["actual_counts"], "approved": len(output["samples"]),
                  "gpu_training_executed": False, "hard_stop_implemented": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
