"""PSNR (Peak Signal-to-Noise Ratio) algorithm.

Pure OpenCV implementation — uses cv2.PSNR (no ffmpeg).

Run directly to compare two images:
    uv run python scripts/metrics_psnr.py output/golden.png output/noise/psnr_20.0.png
"""
from __future__ import annotations

import argparse
import sys

import cv2
import numpy as np

from common import load_image


def compute_psnr(ref: np.ndarray, dist: np.ndarray) -> float:
    """Compute PSNR (dB) between two BGR uint8 images of the same shape.

    Returns float('inf') when the two images are pixel-identical.
    """
    if ref.shape != dist.shape:
        raise ValueError(f"shape mismatch: {ref.shape} vs {dist.shape}")
    return cv2.PSNR(ref, dist)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute PSNR between two images (OpenCV only).")
    parser.add_argument("reference", help="Path to the reference (golden) image")
    parser.add_argument("distorted", help="Path to the distorted/degraded image")
    args = parser.parse_args()

    ref = load_image(args.reference)
    dist = load_image(args.distorted)
    psnr = compute_psnr(ref, dist)
    print(f"PSNR: {psnr:.6f} dB")


if __name__ == "__main__":
    main()
