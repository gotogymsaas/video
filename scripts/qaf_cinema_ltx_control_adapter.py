"""Validate and package official LTX IC-LoRA reference controls.

This tool never treats the QAF 8D vector as an LTX control signal. It only
accepts a paired reference video (pose/depth/canny raster) and emits a dataset
manifest for the official reference_video convention.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path


SCHEMA = "qaf_ltx_v2v_control_manifest_v1"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inside(root, rel):
    if not isinstance(rel, str) or not rel:
        raise ValueError("INVALID_RELATIVE_PATH")
    base = Path(root).resolve()
    path = (base / rel).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError("CONTROL_OR_TARGET_OUTSIDE_PRIVATE_ROOT")
    return path


def video_info(path):
    command = ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
               "-show_entries", "stream=nb_read_frames,width,height,avg_frame_rate",
               "-of", "json", str(path)]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=90, check=False)
    if result.returncode:
        raise ValueError("REFERENCE_OR_TARGET_DECODER_FAILED")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise ValueError("NO_VIDEO_STREAM")
    stream = streams[0]
    frames = int(stream.get("nb_read_frames") or 0)
    width = int(stream["width"])
    height = int(stream["height"])
    try:
        fps = Fraction(stream["avg_frame_rate"])
    except (KeyError, ValueError, ZeroDivisionError):
        raise ValueError("INVALID_CONTROL_VIDEO_FPS") from None
    if frames <= 0 or width <= 0 or height <= 0 or fps <= 0:
        raise ValueError("INVALID_CONTROL_VIDEO_METADATA")
    return {"frames": frames, "width": width, "height": height, "fps": str(fps)}


def qaf_vector(row):
    evidence = row.get("qaf_pose")
    if not isinstance(evidence, dict) or evidence.get("schema") != "qaf_pose_evidence_8d_v1":
        raise ValueError("QAF_8D_EVIDENCE_REQUIRED")
    vector = evidence.get("vector")
    if not isinstance(vector, list) or len(vector) != 8:
        raise ValueError("QAF_8D_VECTOR_MUST_HAVE_8_VALUES")
    if evidence.get("not_a_trained_ltx_condition") is not True:
        raise ValueError("QAF_VECTOR_NOT_MARKED_NON_LTX_CONTROL")
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector):
        raise ValueError("INVALID_QAF_8D_VALUE")
    return [float(value) for value in vector]


def build_manifest(spec, private_root):
    path = Path(spec).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "qaf_ltx_v2v_control_pairs_v1":
        raise ValueError("INVALID_CONTROL_PAIR_SCHEMA")
    if data.get("control_type") not in ("pose", "depth", "canny"):
        raise ValueError("UNSUPPORTED_LTX_CONTROL_TYPE")
    rows = data.get("pairs")
    if not isinstance(rows, list) or not rows:
        raise ValueError("EMPTY_CONTROL_PAIR_LIST")
    root = Path(private_root).resolve()
    manifest = []
    official_dataset = []
    for row in rows:
        target = inside(root, row.get("target"))
        reference = inside(root, row.get("reference"))
        target_hash = sha256(target)
        if row.get("target_sha256") != target_hash:
            raise ValueError("TARGET_SHA256_MISMATCH")
        reference_hash = sha256(reference)
        if row.get("reference_sha256") != reference_hash:
            raise ValueError("REFERENCE_SHA256_MISMATCH")
        target_info = video_info(target)
        reference_info = video_info(reference)
        if target_info["frames"] != reference_info["frames"]:
            raise ValueError("TARGET_REFERENCE_FRAME_COUNT_MISMATCH")
        if target_info["fps"] != reference_info["fps"]:
            raise ValueError("TARGET_REFERENCE_FPS_MISMATCH")
        if target_info["width"] % 32 or target_info["height"] % 32:
            raise ValueError("TARGET_DIMENSION_NOT_DIVISIBLE_BY_32")
        if reference_info["width"] % 32 or reference_info["height"] % 32:
            raise ValueError("REFERENCE_DIMENSION_NOT_DIVISIBLE_BY_32")
        prompt = row.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("CONTROL_PAIR_PROMPT_REQUIRED")
        official_dataset.append({
            "video": str(target), "reference_video": str(reference), "caption": prompt,
        })
        manifest.append({
            "target": str(target),
            "reference_video": str(reference),
            "prompt": prompt,
            "control_type": data["control_type"],
            "target_sha256": target_hash,
            "reference_sha256": reference_hash,
            "frame_count": target_info["frames"],
            "qaf_pose_8d": qaf_vector(row),
            "qaf_8d_not_direct_ltx_condition": True,
        })
    result = {
        "schema": SCHEMA,
        "training_run_executed": False,
        "control_type": data["control_type"],
        "paired_samples": len(manifest),
        "samples": manifest,
        "ltx_dataset": official_dataset,
        "ltx_strategy": {
            "name": "flexible",
            "video": {
                "is_generated": True,
                "latents_dir": "latents",
                "conditions": [{
                    "type": "reference",
                    "latents_dir": "reference_latents",
                    "probability": 1.0,
                }],
            },
        },
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    dataset_out = out.with_name(out.stem + ".ltx.json")
    if out.exists() or dataset_out.exists():
        parser.error("Output or official dataset already exists")
    report = build_manifest(args.spec, args.private_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    dataset_out.write_text(json.dumps(report["ltx_dataset"], ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "schema": SCHEMA,
        "paired_samples": report["paired_samples"],
        "training_run_executed": False,
        "out": str(out),
        "official_dataset_file": str(dataset_out),
    }, indent=2))


if __name__ == "__main__":
    main()
