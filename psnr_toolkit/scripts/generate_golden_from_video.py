"""Extract a 1920x1080 golden sample frame from a video file using OpenCV.

Uses cv2.VideoCapture only — no ffmpeg binary is invoked. This is meant to
replace the previous `ffmpeg -ss ... -frames:v 1` frame-extraction step.

The video file itself must already exist locally (download it with curl/wget
beforehand, e.g. from the official Big Buck Bunny sample mirrors); this script
only performs decoding + frame selection via OpenCV.

Usage:
    uv run python scripts/generate_golden_from_video.py /path/to/video.mp4 output/golden.png --seconds 5
"""
from __future__ import annotations

import argparse
import sys

import cv2

from common import save_image


def extract_frame(video_path: str, seconds: float = 5.0, size: tuple[int, int] = (1920, 1080)):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"cv2.VideoCapture could not open: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_index = int(seconds * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise IOError(f"Failed to read frame at {seconds}s (frame #{frame_index}) from {video_path}")

    h, w = frame.shape[:2]
    if (w, h) != size:
        frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a golden sample frame from a video (OpenCV only).")
    parser.add_argument("video", help="Path to a local video file (e.g. Big Buck Bunny .mp4)")
    parser.add_argument("output", nargs="?", default="output_bbb/golden.png", help="Output PNG path")
    parser.add_argument("--seconds", type=float, default=5.0, help="Timestamp (seconds) of the frame to extract")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()

    try:
        frame = extract_frame(args.video, args.seconds, (args.width, args.height))
    except IOError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    save_image(args.output, frame)
    print(f"Saved golden sample frame: {args.output} ({args.width}x{args.height}, t={args.seconds}s)")


if __name__ == "__main__":
    main()
