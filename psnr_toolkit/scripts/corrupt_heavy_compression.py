"""Simulate heavy re-compression (bitrate starvation) corruption on a golden sample.

Real-world cause: when a transcoder is forced to hit an extremely low target
bitrate (e.g. aggressive cost-saving transcode, cellular network adaptive
bitrate ladder), the encoder must throw away most of the high-frequency
detail, producing large flat DCT-block artifacts, color bleeding, and mosquito
noise around edges -- the classic "over-compressed video" look.

We reproduce this purely with OpenCV's built-in JPEG codec (no ffmpeg): encode
the golden image at a very low JPEG quality in memory, then decode it back.
JPEG uses the same block-based DCT quantization idea as H.264/H.265 intra
frames, so this is a reasonable stand-in for heavy transcode compression
artifacts.

Usage:
    uv run python scripts/corrupt_heavy_compression.py output/golden.png output/broken/heavy_compression.png
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from common import load_image, save_image


def heavy_compression(img: np.ndarray, quality: int = 3) -> np.ndarray:
    """Re-encode/decode through JPEG at a very low quality to simulate bitrate starvation."""
    ok, encoded = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("cv2.imencode failed")
    decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if decoded is None:
        raise RuntimeError("cv2.imdecode failed")
    return decoded


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate heavy re-compression artifacts on a golden image.")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--quality", type=int, default=3, help="JPEG quality 0-100; lower = more artifacts")
    args = parser.parse_args()

    golden = load_image(args.golden)
    corrupted = heavy_compression(golden, args.quality)
    save_image(args.output, corrupted)
    print(f"Saved heavy-compression corruption: {args.output} (JPEG quality={args.quality})")


if __name__ == "__main__":
    main()
