"""Gaussian-noise degradation algorithm.

Adds calibrated additive white Gaussian noise to an image so that the
resulting image hits a target PSNR (dB) relative to the golden reference.
The noise standard deviation (sigma) is found via binary search, verified
with the OpenCV-based PSNR metric (see metrics_psnr.py) — no ffmpeg.

Usage:
    uv run python scripts/degrade_gaussian_noise.py output/golden.png output/noise --targets 30,29.5,...,15
    uv run python scripts/degrade_gaussian_noise.py output/golden.png output/noise  # full 30..15 sweep
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from common import load_image, save_image, target_list
from metrics_psnr import compute_psnr

TOL_DB = 0.05
MAX_ITERS = 40


def add_gaussian_noise(img: np.ndarray, sigma: float, seed: int) -> np.ndarray:
    """Add zero-mean Gaussian noise with the given sigma to a BGR uint8 image."""
    if sigma <= 0:
        return img.copy()
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, img.shape)
    out = img.astype(np.float64) + noise
    return np.clip(out, 0, 255).astype(np.uint8)


def calibrate_noise_for_target(
    golden: np.ndarray, target_db: float, seed: int, tol: float = TOL_DB, max_iters: int = MAX_ITERS
) -> tuple[np.ndarray, float, float]:
    """Binary-search the noise sigma that makes PSNR(golden, noisy) ~= target_db.

    Returns (best_image, best_sigma, best_psnr).
    """
    target_mse = 255.0 ** 2 / (10 ** (target_db / 10))
    sigma_guess = target_mse ** 0.5
    lo, hi = 0.0, sigma_guess * 3 + 5

    best_img, best_sigma, best_psnr = None, None, None
    for _ in range(max_iters):
        mid = (lo + hi) / 2
        candidate = add_gaussian_noise(golden, mid, seed)
        psnr = compute_psnr(golden, candidate)
        if best_psnr is None or abs(psnr - target_db) < abs(best_psnr - target_db):
            best_img, best_sigma, best_psnr = candidate, mid, psnr
        if abs(psnr - target_db) <= tol:
            break
        if psnr > target_db:
            lo = mid  # need more noise -> lower PSNR
        else:
            hi = mid  # need less noise -> higher PSNR
    return best_img, best_sigma, best_psnr


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PSNR-calibrated Gaussian-noise images (OpenCV only).")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("outdir", help="Output directory for psnr_<target>.png files")
    parser.add_argument("--targets", default=None, help="Comma-separated PSNR targets; default is 30.0..15.0 step 0.5")
    args = parser.parse_args()

    golden = load_image(args.golden)
    targets = [float(t) for t in args.targets.split(",")] if args.targets else target_list()

    outdir = Path(args.outdir)
    for t in targets:
        img, sigma, actual = calibrate_noise_for_target(golden, t, seed=int(t * 10))
        out_path = outdir / f"psnr_{t:.1f}.png"
        save_image(out_path, img)
        print(f"target={t:.1f} actual={actual:.3f} sigma={sigma:.3f} -> {out_path}")


if __name__ == "__main__":
    main()
