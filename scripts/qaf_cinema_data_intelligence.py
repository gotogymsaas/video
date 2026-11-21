"""QAF Cinema Data Intelligence: private, read-only CPU corpus triage.

Audits real MP4s and already-extracted landmark observations. It never upgrades
source media, certifies visual excellence, approves rights, trains, or calls Azure.
Quality heuristics require human calibration against real cinematographic footage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

W, H, SAMPLE_COUNT = 160, 90, 10
SCHEMA = "qaf_cinema_data_intelligence_v1"
JOINT_EDGES = ((11, 12), (11, 23), (12, 24), (23, 24), (23, 25),
               (24, 26), (25, 27), (26, 28), (11, 13), (12, 14))


def inside(root, rel):
    """Reject absolute paths, escapes, symlinks leading outside the private root."""
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        raise ValueError("UNSAFE_RELATIVE_PATH")
    base = Path(root).resolve()
    path = (base / rel).resolve()
    if not path.is_relative_to(base):
        raise ValueError("UNSAFE_RELATIVE_PATH")
    return path


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def command(args, *, timeout=90):
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise ValueError("MISSING_BINARY_OR_TIMEOUT") from exc
    if result.returncode:
        raise ValueError("MEDIA_DECODER_FAILED")
    return result.stdout


def probe_video(path):
    raw = command(["ffprobe", "-v", "error", "-select_streams", "v:0",
                   "-show_entries", "stream=width,height,avg_frame_rate,codec_name,bit_rate:"
                   "format=duration,size,bit_rate", "-of", "json", str(path)])
    data = json.loads(raw)
    streams = data.get("streams", [])
    if not streams:
        raise ValueError("NO_VIDEO_STREAM")
    v = streams[0]
    width, height = int(v["width"]), int(v["height"])
    duration = float(data.get("format", {}).get("duration", 0))
    if width <= 0 or height <= 0 or not math.isfinite(duration) or duration <= 0:
        raise ValueError("INVALID_VIDEO_METADATA")
    return {"width": width, "height": height, "duration_seconds": duration,
            "codec": v.get("codec_name", "unknown"),
            "bit_rate": v.get("bit_rate") or data.get("format", {}).get("bit_rate")}


def gray_samples(path):
    raw = command(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
                   "-vf", f"fps=2,scale={W}:{H}:flags=area,format=gray",
                   "-frames:v", str(SAMPLE_COUNT), "-f", "rawvideo", "pipe:1"])
    size = W * H
    if len(raw) % size or not raw:
        raise ValueError("NO_COMPLETE_SAMPLED_FRAMES")
    return [raw[i:i + size] for i in range(0, len(raw), size)]


def sample_metrics(frames):
    """Cheap luma proxies; never describe them as perceptual quality scores."""
    if not frames or any(len(frame) != W * H for frame in frames):
        raise ValueError("INVALID_FRAME_SIZE")
    means, blacks, whites, gradients = [], [], [], []
    for data in frames:
        n = len(data)
        means.append(sum(data) / n)
        blacks.append(sum(value <= 16 for value in data) / n)
        whites.append(sum(value >= 240 for value in data) / n)
        # Spatial gradient is a proxy strongly confounded by texture and camera.
        total = 0
        count = 0
        for y in range(1, H - 1, 2):
            off = y * W
            for x in range(1, W - 1, 2):
                pos = off + x
                total += abs(data[pos] - data[pos - 1])
                total += abs(data[pos] - data[pos - W])
                count += 2
        gradients.append(total / max(1, count))
    diffs = [sum(abs(a - b) for a, b in zip(frames[i - 1], frames[i])) / (W * H)
             for i in range(1, len(frames))]
    return {"frames_sampled": len(frames),
            "mean_luma": round(sum(means) / len(means), 3),
            "mean_black_fraction": round(sum(blacks) / len(blacks), 4),
            "mean_white_fraction": round(sum(whites) / len(whites), 4),
            "spatial_gradient_proxy": round(sum(gradients) / len(gradients), 3),
            "sampled_frame_difference_proxy": round(sum(diffs) / len(diffs), 3) if diffs else None}


def qaf_structural_features(observations):
    """Measured pose relations from stable MediaPipe joint_id, not trained QAF weights.

    Historical unlabeled arrays are intentionally excluded: filtering low-visibility
    landmarks changes array positions, so positional enumeration would falsify joints.
    """
    if observations.get("schema") != "qaf_cinematic_observations_v1":
        raise ValueError("INVALID_OBSERVATION_SCHEMA")
    timeline = observations.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise ValueError("EMPTY_OBSERVATIONS")
    tracked = []
    for frame_no, rec in enumerate(timeline):
        if rec.get("frame") != frame_no:
            raise ValueError("NON_MONOTONIC_OBSERVATIONS")
        joints = {}
        for pt in rec.get("pose", []):
            idx = pt.get("joint_id")
            confidence = pt.get("confidence")
            if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx <= 32:
                continue
            if not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or confidence < .5:
                continue
            x, y = pt.get("x"), pt.get("y")
            if not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1
                       for v in (x, y)):
                continue
            if idx in joints:
                raise ValueError("DUPLICATED_JOINT_ID")
            joints[idx] = (float(x), float(y), float(confidence))
        tracked.append(joints)
    good = [j for j in tracked if len(j) >= 4]
    observed = len(good)
    coverage = observed / len(timeline)
    if observed < 4:
        return {"available": False, "reason": "INSUFFICIENT_NAMED_POSE_FRAMES",
                "coverage": round(coverage, 4), "vector": None}
    stable = set.intersection(*(set(j) for j in good))
    if len(stable) < 4:
        return {"available": False, "reason": "INSUFFICIENT_STABLE_JOINTS",
                "coverage": round(coverage, 4), "vector": None}
    # Per-frame normalized values, NOT velocity in real-world physical units.
    motions, accelerations, jerks, confs = [], [], [], []
    for idx in sorted(stable):
        xy = [(j[idx][0], j[idx][1]) for j in good]
        confs.extend(j[idx][2] for j in good)
        differences = [[xy[t][k] - xy[t - 1][k] for k in (0, 1)]
                       for t in range(1, len(xy))]
        acceler = [[differences[t][k] - differences[t - 1][k] for k in (0, 1)]
                   for t in range(1, len(differences))]
        jerk = [[acceler[t][k] - acceler[t - 1][k] for k in (0, 1)]
                for t in range(1, len(acceler))]
        motions.extend(math.hypot(*v) for v in differences)
        accelerations.extend(math.hypot(*v) for v in acceler)
        jerks.extend(math.hypot(*v) for v in jerk)
    bone_lengths = []
    for a, b in JOINT_EDGES:
        if a in stable and b in stable:
            lengths = [math.dist(j[a][:2], j[b][:2]) for j in good]
            mean = sum(lengths) / len(lengths)
            if mean > 1e-6:
                bone_lengths.append(sum(abs(value - mean) for value in lengths) / (len(lengths) * mean))
    if not bone_lengths:
        return {"available": False, "reason": "NO_STABLE_BONE_EDGES",
                "coverage": round(coverage, 4), "vector": None}
    avg = lambda x: sum(x) / len(x) if x else 0
    # Research-only 8D Phi_Q: coverage, confidence, stable joint density,
    # displacement, frame-to-frame motion, acceleration, jerk, bone consistency.
    centroid_start = [avg([good[0][i][k] for i in stable]) for k in (0, 1)]
    centroid_end = [avg([good[-1][i][k] for i in stable]) for k in (0, 1)]
    vector = [coverage, avg(confs), len(stable) / 33,
              math.dist(centroid_start, centroid_end), avg(motions),
              avg(accelerations), avg(jerks), avg(bone_lengths)]
    return {"available": True, "schema": "qaf_pose_evidence_8d_v1",
            "feature_names": ["coverage", "confidence", "stable_joint_fraction",
                              "centroid_displacement", "per_frame_motion",
                              "per_frame_acceleration", "per_frame_jerk",
                              "bone_length_relative_variation"],
            "vector": [round(value, 7) for value in vector],
            "coverage": round(coverage, 4),
            "units": "normalized_pixel_coordinates_per_sampled_frame",
            "not_a_trained_ltx_condition": True}


def inspect_clip(path, observations=None, *, probe_fn=probe_video, frames_fn=gray_samples):
    if not path.is_file():
        return {"state": "MISSING_SOURCE", "training_approved": False}
    try:
        info = probe_fn(path)
        metric = sample_metrics(frames_fn(path))
        flags = []
        if info["width"] < 1280 or info["height"] < 720:
            flags.append("LOW_RESOLUTION_FOR_CINEMA_REFERENCE")
        if metric["mean_luma"] < 40 or metric["mean_black_fraction"] > .40:
            flags.append("DARK_OR_CRUSHED_SHADOWS_PROXY")
        if metric["mean_luma"] > 215 or metric["mean_white_fraction"] > .30:
            flags.append("BRIGHT_OR_CLIPPED_HIGHLIGHTS_PROXY")
        if metric["spatial_gradient_proxy"] < 3:
            flags.append("LOW_SPATIAL_GRADIENT_PROXY")
        if metric["frames_sampled"] < 3:
            flags.append("TOO_FEW_SAMPLED_FRAMES")
        result = {"state": "REVIEW_REQUIRED", "sha256": digest(path),
                  "technical": info, "heuristic_metrics": metric, "flags": flags,
                  "visual_review_candidate": not flags, "training_approved": False}
        if observations is not None and observations.is_file():
            evidence = json.loads(observations.read_text(encoding="utf-8"))
            if evidence.get("source_mp4_sha256") != result["sha256"]:
                raise ValueError("OBSERVATION_SOURCE_HASH_MISMATCH_OR_MISSING")
            result["qaf_pose"] = qaf_structural_features(evidence)
            result["observations_sha256"] = digest(observations)
        else:
            result["qaf_pose"] = {"available": False, "reason": "NO_NAMED_OBSERVATIONS", "vector": None}
        result["motion_review_candidate"] = bool(result["qaf_pose"].get("available"))
        return result
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        # Never promote failed, truncated, or untrusted media.
        return {"state": "TECHNICAL_FAILURE", "error_code": type(exc).__name__,
                "training_approved": False}


def audit(inventory, media_root, observations_root=None, *, limit=None):
    data = json.loads(Path(inventory).read_text(encoding="utf-8"))
    if data.get("schema") != "qaf_cross_repo_candidate_corpus_v1" or not isinstance(data.get("files"), list):
        raise ValueError("INVALID_CANDIDATE_INVENTORY")
    if not data["files"] or len({x["source_path"] for x in data["files"]}) != len(data["files"]):
        raise ValueError("EMPTY_OR_DUPLICATE_INVENTORY")
    if limit is not None and limit < 1:
        raise ValueError("INVALID_LIMIT")
    rows = []
    root = Path(media_root).resolve()
    obs_root = Path(observations_root).resolve() if observations_root else None
    chosen = data["files"][:limit] if limit else data["files"]
    for idx, entry in enumerate(chosen):
        rel = entry["source_path"]
        path = inside(root, rel)
        # Observation names are keyed to index, not private athlete filename.
        obs = inside(obs_root, f"{idx + 1:03d}.json") if obs_root else None
        examined = inspect_clip(path, obs)
        rows.append({"id": f"{idx + 1:03d}", "source_relpath": rel, **examined})
    return {"schema": SCHEMA, "inventory_sha256": digest(inventory),
            "scope": {"inventory_count": len(data["files"]), "examined": len(chosen),
                      "complete_inventory": len(chosen) == len(data["files"])},
            "summary": {"missing": sum(x["state"] == "MISSING_SOURCE" for x in rows),
                        "failed": sum(x["state"] == "TECHNICAL_FAILURE" for x in rows),
                        "visual_review_candidates": sum(bool(x.get("visual_review_candidate")) for x in rows),
                        "motion_review_candidates": sum(bool(x.get("motion_review_candidate")) for x in rows)},
            "rows": rows, "all_training_unapproved": True,
            "warning": "Scores are proxies; no commercial quality, dataset rights, QAF advantage, IC-LoRA integration, or real GPU training is certified."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--media-root", required=True)
    parser.add_argument("--observations-root")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out", type=Path, required=True,
                        help="Private JSON output; never commit film or identifying observations")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output already exists; do not overwrite provenance")
    report = audit(args.inventory, args.media_root, args.observations_root, limit=args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": SCHEMA, "summary": report["summary"],
                      "report_path": str(args.out), "training_approved": False}, indent=2))


if __name__ == "__main__":
    main()
