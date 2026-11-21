"""Build fail-closed human review and matched-experiment manifests.

This module creates evidence manifests only. It does not mark media approved,
accept rights or launch training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REVIEW_SCHEMA = "qaf_cinema_human_review_registry_v1"
EXPERIMENT_SCHEMA = "qaf_cinema_matched_experiment_plan_v1"
APPROVAL_SCHEMA = "qaf_gym_corpus_approvals_v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_review_registry(inventory_path, output_path):
    inventory_path = Path(inventory_path).resolve()
    output_path = Path(output_path).resolve()
    require(output_path.suffix == ".json", "Output must be JSON")
    require(not output_path.exists(), "Review registry already exists")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    require(inventory.get("schema") == "qaf_cross_repo_candidate_corpus_v1",
            "Invalid candidate inventory")
    rows = []
    for index, entry in enumerate(inventory.get("files", []), 1):
        require(isinstance(entry.get("source_path"), str),
                "Inventory source path required")
        rows.append({
            "id": f"review-{index:03d}",
            "source_path": entry["source_path"],
            "inventory_size_bytes": entry.get("size_bytes"),
            "inventory_git_blob_sha": entry.get("git_blob_sha"),
            "technical_review": "PENDING",
            "human_visual_review": "PENDING",
            "human_review_status": "PENDING",
            "rights_review_status": "PENDING",
            "participant_consent_status": "PENDING",
            "commercial_training_permission": "PENDING",
            "reviewed_by": None,
            "review_reference": None,
            "actor_group": None,
            "session_group": None,
            "garment_group": None,
            "caption": None,
            "split": None,
            "training_frame_count": None,
            "fps": None,
            "private_sha256": None,
            "cinematic_reference_library": "PENDING",
            "motion_library": "PENDING",
            "qaf_control_library": "PENDING",
        })
    registry = {
        "schema": REVIEW_SCHEMA,
        "source_inventory_sha256": file_sha256(inventory_path),
        "human_training_approval": False,
        "rows": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return registry


def build_approved_split(registry_path, output_path, seed=20261121):
    registry_path = Path(registry_path).resolve()
    output_path = Path(output_path).resolve()
    require(output_path.suffix == ".json", "Output must be JSON")
    require(not output_path.exists(), "Approved split manifest already exists")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    require(registry.get("schema") == REVIEW_SCHEMA, "Invalid review registry")
    require(type(seed) is int, "Seed must be an integer")

    approved = []
    group_splits = {}
    for row in registry.get("rows", []):
        require(isinstance(row, dict), "Invalid review row")
        if row["human_review_status"] != "APPROVED":
            continue
        required = (
            "source_path", "reviewed_by", "review_reference", "actor_group",
            "session_group", "garment_group", "caption", "fps",
            "training_frame_count",
        )
        require(all(row.get(key) not in (None, "") for key in required),
                "Approved row missing required human review fields")
        require(row["rights_review_status"] == "APPROVED",
                "Rights review required")
        require(row["participant_consent_status"] == "APPROVED",
                "Participant consent required")
        require(row["commercial_training_permission"] == "APPROVED",
                "Commercial training permission required")
        require(row["technical_review"] == "PASSED",
                "Technical media review required")
        require(row["human_visual_review"] == "PASSED",
                "Human visual review required")
        require(type(row["fps"]) is int and 8 <= row["fps"] <= 60,
                "Invalid FPS")
        require(type(row["training_frame_count"]) is int
                and (row["training_frame_count"] - 1) % 8 == 0
                and row["training_frame_count"] >= 9,
                "Invalid LTX frame count")

        group_key = "|".join((
            str(row["actor_group"]),
            str(row["session_group"]),
            str(row["garment_group"]),
        ))
        digest = hashlib.sha256(
            f"{seed}|{group_key}".encode("utf-8")
        ).digest()[0]
        bucket = digest % 100
        split = "train" if bucket < 80 else "val" if bucket < 90 else "test"
        for label in ("actor", "session", "garment"):
            value = row[f"{label}_group"]
            key = (label, value)
            if key in group_splits:
                require(group_splits[key] == split,
                        "Cross-split actor/session/garment leakage")
            else:
                group_splits[key] = split
        approved.append({
            "source_path": row["source_path"],
            "split": split,
            "actor_group": row["actor_group"],
            "session_group": row["session_group"],
            "garment_group": row["garment_group"],
            "caption": row["caption"],
            "fps": row["fps"],
            "training_frame_count": row["training_frame_count"],
            "reviewed_by": row["reviewed_by"],
            "review_reference": row["review_reference"],
        })

    require(approved, "No individually approved clips")
    counts = {split: sum(r["split"] == split for r in approved)
              for split in ("train", "val", "test")}
    require(all(counts.values()), "Train, val and test sets are required")
    result = {
        "schema": APPROVAL_SCHEMA,
        "seed": seed,
        "human_training_approval": True,
        "rights_independently_certified": False,
        "split_counts": counts,
        "approved": [{
            "source_path": row["source_path"],
            "training_rights_documented": True,
            "participant_consent_documented": True,
            "reviewed_by": row["reviewed_by"],
            "review_reference": row["review_reference"],
            "actor_group": row["actor_group"],
            "session_group": row["session_group"],
            "garment_group": row["garment_group"],
            "split": row["split"],
            "caption": row["caption"],
            "fps": row["fps"],
            "training_frame_count": row["training_frame_count"],
        } for row in approved],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return result


def build_matched_experiment_plan(scenes, seed=20261121, gpu_hours=24):
    require(isinstance(scenes, list) and scenes, "Scenes required")
    require(type(seed) is int, "Seed must be an integer")
    require(type(gpu_hours) in (int, float) and 0 < gpu_hours <= 100,
            "Invalid GPU-hour budget")
    arms = [
        {
            "id": "A",
            "name": "base_ltx",
            "condition": "No LoRA, no QAF planning",
        },
        {
            "id": "B",
            "name": "visual_lora",
            "condition": "Visual LoRA only",
        },
        {
            "id": "C",
            "name": "classical_control",
            "condition": "Official pose/depth/Canny IC-LoRA control",
        },
        {
            "id": "D",
            "name": "qaf_control",
            "condition": "Same classical control plus QAF planning metadata",
        },
    ]
    pairs = []
    for scene in scenes:
        require(isinstance(scene, dict), "Invalid scene")
        require(isinstance(scene.get("id"), str) and scene["id"],
                "Scene id required")
        require(isinstance(scene.get("prompt"), str) and scene["prompt"].strip(),
                "Scene prompt required")
        require(scene.get("source_sha256"),
                "Scene source SHA-256 required")
        pairs.append({
            "scene": scene["id"],
            "prompt": scene["prompt"],
            "source_sha256": scene["source_sha256"],
            "seed": seed,
            "duration_seconds": scene.get("duration_seconds", 5),
            "arms": [arm["id"] for arm in arms],
        })
    return {
        "schema": EXPERIMENT_SCHEMA,
        "training_executed": False,
        "human_evaluation": False,
        "cinematic_superiority_proven": False,
        "qaf_advantage_proven": False,
        "seed": seed,
        "gpu_hour_cap": gpu_hours,
        "arms": arms,
        "matched_pairs": pairs,
        "control_requirements": [
            "Same checkpoint",
            "Same prompt",
            "Same seed",
            "Same duration",
            "Same compute budget",
            "Same target and reference geometry",
            "Blind human review",
            "Real MP4 and checkpoint verification",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    review = sub.add_parser("create-review")
    review.add_argument("inventory")
    review.add_argument("--out", required=True)
    split = sub.add_parser("build-split")
    split.add_argument("registry")
    split.add_argument("--out", required=True)
    split.add_argument("--seed", type=int, default=20261121)
    experiment = sub.add_parser("plan-experiment")
    experiment.add_argument("scenes")
    experiment.add_argument("--out", required=True)
    experiment.add_argument("--seed", type=int, default=20261121)
    experiment.add_argument("--gpu-hours", type=float, default=24)
    args = parser.parse_args()
    if args.command == "create-review":
        result = create_review_registry(args.inventory, args.out)
    elif args.command == "build-split":
        result = build_approved_split(args.registry, args.out, args.seed)
    else:
        scenes = json.loads(Path(args.scenes).read_text(encoding="utf-8"))
        if isinstance(scenes, dict):
            scenes = scenes.get("scenes")
        result = build_matched_experiment_plan(scenes, args.seed, args.gpu_hours)
        out = Path(args.out).resolve()
        require(not out.exists(), "Experiment plan already exists")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(json.dumps({"schema": result["schema"],
                      "human_training_approval": result.get("human_training_approval", False),
                      "training_executed": False,
                      "note": "No media approval or GPU training is implied"},
                     indent=2))
