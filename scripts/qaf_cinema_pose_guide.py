"""Render fail-closed pose skeleton guides for LTX V2V reference pairs.

The guide is generated only from named, confidence-filtered MediaPipe
pose observations. It never invents depth or segmentation and never
restores detail that is absent from the source video.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


SCHEMA = "qaf_cinema_pose_guide_v1"
JOINT_EDGES = (
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26),
    (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32),
)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_pose_guide(observation_path, output_path, target_path=None,
                     width=540, height=960, fps=24):
    observation_path = Path(observation_path).resolve()
    output_path = Path(output_path).resolve()
    data = json.loads(observation_path.read_text(encoding="utf-8"))
    if data.get("schema") != "qaf_cinematic_observations_v1":
        raise ValueError("INVALID_OBSERVATION_SCHEMA")
    timeline = data.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise ValueError("EMPTY_POSE_TIMELINE")
    if data.get("frames") != len(timeline):
        raise ValueError("OBSERVATION_FRAME_COUNT_MISMATCH")
    observation_width = data.get("width")
    observation_height = data.get("height")
    if not isinstance(observation_width, int) or observation_width <= 0:
        raise ValueError("INVALID_OBSERVATION_WIDTH")
    if not isinstance(observation_height, int) or observation_height <= 0:
        raise ValueError("INVALID_OBSERVATION_HEIGHT")
    if width % 32 or height % 32:
        raise ValueError("GUIDE_GEOMETRY_NOT_DIVISIBLE_BY_32")
    if not isinstance(fps, int) or fps <= 0:
        raise ValueError("INVALID_GUIDE_FPS")
    if output_path.exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    if target_path is not None:
        target = Path(target_path).resolve()
        if not target.is_file():
            raise ValueError("TARGET_VIDEO_MISSING")
        source_hash = data.get("source_mp4_sha256")
        if not isinstance(source_hash, str) or len(source_hash) != 64:
            raise ValueError("SOURCE_SHA256_REQUIRED")
        if sha256(target) != source_hash:
            raise ValueError("SOURCE_SHA256_MISMATCH")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-nostdin", "-v", "error", "-f", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "pipe:0", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-y", str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for frame_index, record in enumerate(timeline):
        if record.get("frame") != frame_index:
            process.stdin.close()
            process.wait()
            raise ValueError("NON_MONOTONIC_GUIDE_TIMELINE")
        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        joints = {}
        for point in record.get("pose", []):
            joint_id = point.get("joint_id")
            confidence = point.get("confidence")
            x = point.get("x")
            y = point.get("y")
            if not isinstance(joint_id, int):
                continue
            if not all(isinstance(value, (int, float)) for value in (confidence, x, y)):
                continue
            if confidence < 0.45:
                continue
            px = int(max(0, min(width - 1, x * width)))
            py = int(max(0, min(height - 1, y * height)))
            joints[joint_id] = (px, py)
            draw.ellipse((px - 4, py - 4, px + 4, py + 4),
                         fill=(0, 220, 255), outline=(255, 255, 255), width=1)
        for start, end in JOINT_EDGES:
            if start in joints and end in joints:
                draw.line((joints[start], joints[end]),
                          fill=(255, 200, 0), width=3)
        process.stdin.write(image.tobytes())
    process.stdin.close()
    stderr = process.stderr.read().decode(errors="replace")
    code = process.wait(timeout=300)
    if code != 0:
        output_path.unlink(missing_ok=True)
        raise ValueError("POSE_GUIDE_ENCODER_FAILED")
    report = {
        "schema": SCHEMA,
        "training_run_executed": False,
        "frame_count": len(timeline),
        "fps": fps,
        "width": width,
        "height": height,
        "observation_width": observation_width,
        "observation_height": observation_height,
        "observation_sha256": sha256(observation_path),
        "source_sha256": data.get("source_mp4_sha256"),
        "guide_sha256": sha256(output_path),
        "named_pose_only": True,
        "depth_estimated": False,
        "cinematic_detail_restored": False,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()
    report = build_pose_guide(args.observations, args.out, args.target,
                              args.width, args.height, args.fps)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
