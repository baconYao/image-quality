"""SSIM and MS-SSIM algorithms.

Pure OpenCV implementation:
- SSIM uses cv2's contrib "quality" module (cv2.quality.QualitySSIM_compute),
  which ships with the opencv-contrib-python package (no ffmpeg, no scikit-image).
- MS-SSIM is implemented on top of single-scale SSIM by repeatedly downsampling
  with cv2.pyrDown and combining scores with the standard Wang et al. (2003)
  5-scale weights.

Run directly to compare two images:
    uv run python scripts/metrics_ssim.py output/golden.png output/blur/psnr_20.0.png
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from common import load_image

# Standard MS-SSIM weights from Wang, Simoncelli & Bovik (2003).
MS_SSIM_WEIGHTS = np.array([0.0448, 0.2856, 0.3001, 0.2363, 0.1333])


def compute_ssim(ref: np.ndarray, dist: np.ndarray) -> float:
    """Single-scale SSIM, averaged across the B/G/R channels."""
    if ref.shape != dist.shape:
        raise ValueError(f"shape mismatch: {ref.shape} vs {dist.shape}")
    score, _ = cv2.quality.QualitySSIM_compute(ref, dist)
    # score is a 4-tuple (B, G, R, unused); average the 3 color channels.
    return float(np.mean(score[:3]))


def compute_ms_ssim(ref: np.ndarray, dist: np.ndarray, weights: np.ndarray = MS_SSIM_WEIGHTS) -> float:
    """Multi-scale SSIM using cv2.pyrDown for the scale pyramid."""
    if ref.shape != dist.shape:
        raise ValueError(f"shape mismatch: {ref.shape} vs {dist.shape}")

    levels = len(weights)
    cur_ref, cur_dist = ref.copy(), dist.copy()
    scores = []
    for level in range(levels):
        h, w = cur_ref.shape[:2]
        if min(h, w) < 11:
            # SSIM's default window needs at least 11x11; stop early and reuse
            # the last valid score for any remaining (too-small) scales.
            scores.append(scores[-1] if scores else compute_ssim(cur_ref, cur_dist))
            continue
        scores.append(compute_ssim(cur_ref, cur_dist))
        if level < levels - 1:
            cur_ref = cv2.pyrDown(cur_ref)
            cur_dist = cv2.pyrDown(cur_dist)

    scores = np.clip(np.array(scores), 1e-8, None)  # avoid log/pow of 0 or negative
    ms_ssim = float(np.prod(scores ** weights))
    return ms_ssim


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute SSIM/MS-SSIM between two images (OpenCV only).")
    parser.add_argument("reference", help="Path to the reference (golden) image")
    parser.add_argument("distorted", help="Path to the distorted/degraded image")
    args = parser.parse_args()

    ref = load_image(args.reference)
    dist = load_image(args.distorted)
    print(f"SSIM:    {compute_ssim(ref, dist):.6f}")
    print(f"MS-SSIM: {compute_ms_ssim(ref, dist):.6f}")


if __name__ == "__main__":
    main()
