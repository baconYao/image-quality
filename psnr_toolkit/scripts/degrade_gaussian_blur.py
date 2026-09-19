"""Gaussian-blur degradation algorithm.

Applies calibrated Gaussian blur (cv2.GaussianBlur) to an image so the result
hits a target PSNR (dB) relative to the golden reference. The blur sigma is
found via binary search, verified with the OpenCV-based PSNR metric — no
ffmpeg involved.

Usage:
    uv run python scripts/degrade_gaussian_blur.py output/golden.png output/blur
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from common import load_image, save_image, target_list
from metrics_psnr import compute_psnr

TOL_DB = 0.05
MAX_ITERS = 60


_SMALL_SIGMA_LIMIT = 15.0  # above this, use the downscale/upscale trick below


def gaussian_blur(img: np.ndarray, sigma: float) -> np.ndarray:
    """Blur a BGR uint8 image to an effective Gaussian sigma.

    For small sigma this is a direct cv2.GaussianBlur call. For large sigma,
    a direct call would need a huge (thousands-of-pixels-wide) kernel, which
    is extremely slow. Instead we use the standard downscale -> small-kernel
    blur -> upscale trick: shrinking the image by sigma/_SMALL_SIGMA_LIMIT
    first means the equivalent blur only ever needs a small kernel, and the
    resize cost is O(pixels) regardless of how large sigma is. This keeps the
    whole binary-search calibration fast even for very strong blur (needed to
    reach low target PSNR values on low-detail content), while remaining
    100% OpenCV (no ffmpeg).
    """
    if sigma <= 0:
        return img.copy()
    if sigma <= _SMALL_SIGMA_LIMIT:
        ksize = int(sigma * 6) | 1  # force odd
        ksize = max(ksize, 3)
        return cv2.GaussianBlur(img, (ksize, ksize), sigmaX=sigma, borderType=cv2.BORDER_REFLECT)

    h, w = img.shape[:2]
    scale = _SMALL_SIGMA_LIMIT / sigma
    small_w, small_h = max(int(round(w * scale)), 4), max(int(round(h * scale)), 4)
    small = cv2.resize(img, (small_w, small_h), interpolation=cv2.INTER_AREA)
    ksize = int(_SMALL_SIGMA_LIMIT * 6) | 1
    small = cv2.GaussianBlur(small, (ksize, ksize), sigmaX=_SMALL_SIGMA_LIMIT, borderType=cv2.BORDER_REFLECT)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def calibrate_blur_for_target(
    golden: np.ndarray, target_db: float, hi_bound: float = 3000.0, tol: float = TOL_DB, max_iters: int = MAX_ITERS
) -> tuple[np.ndarray, float, float]:
    """Binary-search the blur sigma that makes PSNR(golden, blurred) ~= target_db.

    Returns (best_image, best_sigma, best_psnr). If the target is below the
    PSNR floor reachable by blurring alone (content-dependent), returns the
    closest achievable result at hi_bound.
    """
    lo, hi = 0.0, hi_bound
    best_img, best_sigma, best_psnr = None, None, None
    for _ in range(max_iters):
        mid = (lo + hi) / 2
        candidate = gaussian_blur(golden, mid)
        psnr = compute_psnr(golden, candidate)
        if best_psnr is None or abs(psnr - target_db) < abs(best_psnr - target_db):
            best_img, best_sigma, best_psnr = candidate, mid, psnr
        if abs(psnr - target_db) <= tol:
            break
        if psnr > target_db:
            lo = mid  # need more blur -> lower PSNR
        else:
            hi = mid  # need less blur -> higher PSNR
    return best_img, best_sigma, best_psnr


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PSNR-calibrated Gaussian-blur images (OpenCV only).")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("outdir", help="Output directory for psnr_<target>.png files")
    parser.add_argument("--targets", default=None, help="Comma-separated PSNR targets; default is 30.0..15.0 step 0.5")
    parser.add_argument("--hi-bound", type=float, default=3000.0, help="Upper bound for blur sigma binary search")
    args = parser.parse_args()

    golden = load_image(args.golden)
    targets = [float(t) for t in args.targets.split(",")] if args.targets else target_list()

    outdir = Path(args.outdir)
    for t in targets:
        img, sigma, actual = calibrate_blur_for_target(golden, t, hi_bound=args.hi_bound)
        out_path = outdir / f"psnr_{t:.1f}.png"
        save_image(out_path, img)
        print(f"target={t:.1f} actual={actual:.3f} sigma={sigma:.3f} -> {out_path}")


if __name__ == "__main__":
    main()
