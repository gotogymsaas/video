"""Prepare 8n+1 frame-aligned, private LTX pose-control pilot windows.

CPU/FFmpeg only. Never approves media rights, visual quality or model training.
The output directory must be outside this public repository and must not exist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

SCHEMA = "qaf_cinema_temporal_bucket_v1"
PAIRS_SCHEMA = "qaf_ltx_v2v_control_pairs_v1"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def private_file(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("UNSAFE_OR_ABSOLUTE_SOURCE")
    base = Path(root).resolve()
    path = (base / relative).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError("PRIVATE_SOURCE_MISSING_OR_ESCAPE")
    return path


def ffprobe(path):
    command = ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
               "-show_entries", "stream=nb_read_frames,width,height,avg_frame_rate,r_frame_rate",
               "-of", "json", str(path)]
    try:
        result = subprocess.run(command, capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("FFPROBE_UNAVAILABLE") from exc
    if result.returncode:
        raise ValueError("FFPROBE_FAILED")
    try:
        stream = json.loads(result.stdout)["streams"][0]
        frame_count = int(stream["nb_read_frames"])
        width, height = int(stream["width"]), int(stream["height"])
        average = Fraction(stream["avg_frame_rate"])
        native = Fraction(stream["r_frame_rate"])
    except (KeyError, ValueError, IndexError, ZeroDivisionError) as exc:
        raise ValueError("INVALID_VIDEO_METADATA") from exc
    if frame_count < 1 or min(width, height) <= 0 or average <= 0 or native != average:
        raise ValueError("NON_CONSTANT_OR_INVALID_VIDEO_RATE")
    return {"frames": frame_count, "width": width, "height": height, "fps": str(average)}


def require_bucket(frames):
    if type(frames) is not int or not 9 <= frames <= 121 or (frames - 1) % 8:
        raise ValueError("BUCKET_MUST_BE_8N_PLUS_ONE_AT_MOST_121")


def plan_pairs(spec, private_root, bucket=121, start_frame=0, probe=ffprobe):
    """Validate all paired clips and produce a plan without writing any files."""
    require_bucket(bucket)
    if type(start_frame) is not int or start_frame < 0:
        raise ValueError("INVALID_START_FRAME")
    source = json.loads(Path(spec).read_text(encoding="utf-8"))
    if source.get("schema") != PAIRS_SCHEMA or source.get("control_type") not in ("pose", "depth", "canny"):
        raise ValueError("INVALID_INPUT_PAIR_SCHEMA")
    rows = source.get("pairs")
    if not isinstance(rows, list) or not rows:
        raise ValueError("EMPTY_INPUT_PAIR_LIST")
    processed = []
    for index, row in enumerate(rows, 1):
        target = private_file(private_root, row.get("target"))
        reference = private_file(private_root, row.get("reference"))
        if target == reference:
            raise ValueError("TARGET_MUST_DIFFER_FROM_REFERENCE")
        if sha256(target) != row.get("target_sha256"):
            raise ValueError("SOURCE_TARGET_HASH_MISMATCH")
        if sha256(reference) != row.get("reference_sha256"):
            raise ValueError("SOURCE_REFERENCE_HASH_MISMATCH")
        a, b = probe(target), probe(reference)
        if a["frames"] != b["frames"] or a["fps"] != b["fps"]:
            raise ValueError("SOURCE_PAIR_TEMPORAL_MISMATCH")
        if a["width"] != b["width"] or a["height"] != b["height"]:
            raise ValueError("SOURCE_PAIR_SPATIAL_MISMATCH")
        if a["width"] % 32 or a["height"] % 32:
            raise ValueError("UNSUPPORTED_SPATIAL_DIMENSIONS")
        if a["frames"] < start_frame + bucket:
            raise ValueError("NOT_ENOUGH_REAL_FRAMES_FOR_BUCKET")
        if Fraction(a["fps"]) != 24:
            raise ValueError("REQUIRES_PRENORMALIZED_24_FPS")
        if not isinstance(row.get("prompt"), str) or not row["prompt"].strip():
            raise ValueError("CAPTION_REQUIRED")
        # No claim that observed joints cover every frame inside the selected window.
        qaf = row.get("qaf_pose")
        if qaf is not None:
            vector = qaf.get("vector") if isinstance(qaf, dict) else None
            if (not isinstance(vector, list) or len(vector) != 8
                    or not all(type(value) in (float, int) and math.isfinite(value) for value in vector)
                    or qaf.get("schema") != "qaf_pose_evidence_8d_v1"
                    or qaf.get("not_a_trained_ltx_condition") is not True):
                raise ValueError("INVALID_QAF_METADATA")
        processed.append({
            "id": f"{index:03d}",
            "target": row["target"], "reference": row["reference"],
            "target_source_hash": row["target_sha256"],
            "reference_source_hash": row["reference_sha256"],
            "prompt": row["prompt"], "qaf_pose": qaf,
            "start_frame": start_frame, "frames": bucket,
            "fps": a["fps"], "width": a["width"], "height": a["height"],
            "qaf_evidence_available": qaf is not None,
            "human_quality_review_complete": False,
            "independent_training_rights_verified": False,
            "training_approved": False,
        })
    return {"schema": SCHEMA, "control_type": source["control_type"],
            "source_spec_sha256": sha256(spec), "bucket": bucket,
            "clip_count": len(processed),
            "technical_windows_only": True, "training_approved": False,
            "rows": processed}


def encode_window(source, destination, start_frame, frame_count, fps):
    stop = start_frame + frame_count
    args = ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", str(source),
            "-vf", f"trim=start_frame={start_frame}:end_frame={stop},setpts=PTS-STARTPTS",
            "-frames:v", str(frame_count), "-an", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-r", str(Fraction(fps)),
            "-vsync", "0", "-movflags", "+faststart", str(destination)]
    try:
        result = subprocess.run(args, capture_output=True, check=False, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("FFMPEG_WINDOW_UNAVAILABLE") from exc
    if result.returncode:
        raise ValueError("FFMPEG_WINDOW_FAILED")


def guide_activity(path, frames):
    """Fraction of raster pose-guide frames with measurable non-black skeleton marks.

    This is a coverage proxy only; it does NOT validate joint accuracy or motion.
    """
    width, height = 128, 224
    args = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
            "-vf", f"scale={width}:{height}:flags=area,format=gray",
            "-frames:v", str(frames), "-f", "rawvideo", "pipe:1"]
    try:
        result = subprocess.run(args, capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("GUIDE_DECODER_UNAVAILABLE") from exc
    size = width * height
    if result.returncode or len(result.stdout) != frames * size:
        raise ValueError("GUIDE_DECODE_INCOMPLETE")
    active = 0
    for frame in range(frames):
        image = result.stdout[frame * size:(frame + 1) * size]
        if sum(value > 16 for value in image) >= 4:
            active += 1
    return active / frames


def render_pairs(plan, private_root, out_root, *, encoder=encode_window,
                 probe=ffprobe, guide_checker=guide_activity,
                 min_guide_coverage=0.60):
    """Create exactly one private bucket per pair; delete partial outputs on failure."""
    if plan.get("schema") != SCHEMA or not plan.get("rows"):
        raise ValueError("INVALID_PLAN")
    if (type(min_guide_coverage) not in (float, int) or
            not math.isfinite(min_guide_coverage) or
            not 0 <= min_guide_coverage <= 1):
        raise ValueError("INVALID_MIN_GUIDE_COVERAGE")
    destination = Path(out_root).resolve()
    repository = Path(__file__).resolve().parents[1]
    if destination.is_relative_to(repository):
        raise ValueError("OUTPUT_MUST_BE_OUTSIDE_PUBLIC_REPOSITORY")
    if destination.exists():
        raise ValueError("REFUSING_TO_OVERWRITE_PRIVATE_OUTPUT")
    destination.mkdir(parents=True, exist_ok=False)
    try:
        (destination / "targets").mkdir()
        (destination / "guides").mkdir()
        paired = []
        measured_coverage = {}
        for row in plan["rows"]:
            if row.get("training_approved") is not False:
                raise ValueError("PLAN_MUST_NOT_AUTOAPPROVE_TRAINING")
            source_target = private_file(private_root, row["target"])
            source_reference = private_file(private_root, row["reference"])
            if (sha256(source_target) != row["target_source_hash"]
                    or sha256(source_reference) != row["reference_source_hash"]):
                raise ValueError("SOURCE_CHANGED_SINCE_PREFLIGHT")
            dest_target = destination / "targets" / (row["id"] + ".mp4")
            dest_reference = destination / "guides" / (row["id"] + ".mp4")
            for src, dst in ((source_target, dest_target),
                             (source_reference, dest_reference)):
                encoder(src, dst, row["start_frame"], row["frames"], row["fps"])
                if not dst.is_file() or dst.stat().st_size == 0:
                    raise ValueError("OUTPUT_CLIP_MISSING")
                observed = probe(dst)
                if (observed["frames"] != row["frames"]
                        or observed["fps"] != row["fps"]
                        or observed["width"] != row["width"]
                        or observed["height"] != row["height"]):
                    raise ValueError("BUCKET_OUTPUT_VERIFICATION_FAILED")
            coverage = guide_checker(dest_reference, row["frames"])
            if type(coverage) not in (float, int) or not math.isfinite(coverage):
                raise ValueError("INVALID_GUIDE_ACTIVITY_REPORT")
            if coverage < min_guide_coverage:
                raise ValueError("GUIDE_TOO_SPARSE_FOR_PILOT")
            measured_coverage[row["id"]] = round(coverage, 4)
            entry = {
                "target": "targets/" + row["id"] + ".mp4",
                "reference": "guides/" + row["id"] + ".mp4",
                "target_sha256": sha256(dest_target),
                "reference_sha256": sha256(dest_reference),
                "prompt": row["prompt"],
            }
            if row.get("qaf_pose") is not None:
                entry["qaf_pose"] = row["qaf_pose"]
            paired.append(entry)
        spec = {"schema": PAIRS_SCHEMA, "control_type": plan["control_type"],
                "pairs": paired}
        (destination / "pilot-pairs.json").write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary = dict(plan)
        summary["pose_guide_activity_coverage"] = measured_coverage
        summary["min_pose_guide_activity_coverage"] = min_guide_coverage
        summary["guide_activity_is_not_joint_accuracy"] = True
        summary["source_content_hashes_in_private_manifest"] = True
        summary["rendered_and_verified"] = True
        summary["gpu_training_executed"] = False
        (destination / "technical-bucket-report.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"windows_verified": len(paired), "bucket": plan["bucket"],
                "training_approved": False, "gpu_training_executed": False,
                "private_output": str(destination)}
    except BaseException:
        shutil.rmtree(destination)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Private pilot-pairs.json")
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--out-root", required=True, help="New private directory outside Git")
    parser.add_argument("--bucket", type=int, default=121)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--min-guide-coverage", type=float, default=0.60,
                        help="Measured fraction of rendered guide frames containing pose marks")
    parser.add_argument("--execute", action="store_true", help="Explicitly write CPU clips")
    args = parser.parse_args()
    plan = plan_pairs(args.spec, args.private_root, args.bucket, args.start_frame)
    if args.execute:
        result = render_pairs(plan, args.private_root, args.out_root,
                              min_guide_coverage=args.min_guide_coverage)
    else:
        result = {"validated_sources": plan["clip_count"], "bucket": plan["bucket"],
                  "would_write_to": str(Path(args.out_root).resolve()),
                  "execute_required": True, "training_approved": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
