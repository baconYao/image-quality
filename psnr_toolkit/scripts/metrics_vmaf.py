"""VMAF metric wrapper (optional; not required for the core PSNR/SSIM pipeline).

VMAF itself is a C library (Netflix's libvmaf) with no official PyPI/uv
package, so it cannot be pip/uv-installed like opencv or numpy. This script
assumes a `vmaf` CLI binary has already been built separately (e.g. via
`meson`/`ninja` from https://github.com/Netflix/vmaf, installed to
~/.local/bin/vmaf) and simply drives it.

Crucially, no ffmpeg is used anywhere in this script: the BGR -> YUV420p
planar conversion needed by libvmaf is done with cv2.cvtColor +
raw-byte writes, replacing the previous `ffmpeg -pix_fmt yuv420p` step.

Usage:
    uv run python scripts/metrics_vmaf.py output/golden.png output/blur/psnr_20.0.png
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

from common import load_image

DEFAULT_VMAF_BIN = os.path.expanduser("~/.local/bin/vmaf")
DEFAULT_LIB_DIR = os.path.expanduser("~/.local/lib/x86_64-linux-gnu")


def bgr_to_yuv420p_bytes(img: np.ndarray) -> bytes:
    """Convert a BGR uint8 image to raw planar YUV 4:2:0 bytes (I420) via OpenCV."""
    h, w = img.shape[:2]
    if h % 2 or w % 2:
        raise ValueError("width/height must be even for 4:2:0 chroma subsampling")
    yuv_i420 = cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420)  # shape: (h*3/2, w)
    return yuv_i420.tobytes()


def compute_vmaf(
    ref: np.ndarray,
    dist: np.ndarray,
    vmaf_bin: str = DEFAULT_VMAF_BIN,
    lib_dir: str = DEFAULT_LIB_DIR,
    model: str = "version=vmaf_v0.6.1",
) -> dict:
    """Run the external `vmaf` binary and return {'ssim', 'ms_ssim', 'vmaf'}."""
    if not os.path.exists(vmaf_bin):
        raise FileNotFoundError(
            f"vmaf binary not found at {vmaf_bin}. Build libvmaf separately "
            "(meson+ninja, see module docstring) — it is not a uv/pip package."
        )
    if ref.shape != dist.shape:
        raise ValueError(f"shape mismatch: {ref.shape} vs {dist.shape}")

    h, w = ref.shape[:2]
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = lib_dir + ":" + env.get("LD_LIBRARY_PATH", "")

    with tempfile.TemporaryDirectory() as tmp:
        ref_path = Path(tmp) / "ref.yuv"
        dist_path = Path(tmp) / "dist.yuv"
        out_path = Path(tmp) / "out.json"
        ref_path.write_bytes(bgr_to_yuv420p_bytes(ref))
        dist_path.write_bytes(bgr_to_yuv420p_bytes(dist))

        subprocess.run(
            [
                vmaf_bin, "-r", str(ref_path), "-d", str(dist_path),
                "-w", str(w), "-h", str(h), "-p", "420", "-b", "8",
                "-m", model,
                "--feature", "float_ssim", "--feature", "float_ms_ssim",
                "-o", str(out_path), "--json", "-q",
            ],
            check=True, env=env, capture_output=True,
        )
        data = json.loads(out_path.read_text())

    metrics = data["frames"][0]["metrics"]
    return {
        "ssim": metrics["float_ssim"],
        "ms_ssim": metrics["float_ms_ssim"],
        "vmaf": metrics["vmaf"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute VMAF (+SSIM/MS-SSIM) via an externally built libvmaf CLI.")
    parser.add_argument("reference")
    parser.add_argument("distorted")
    parser.add_argument("--vmaf-bin", default=DEFAULT_VMAF_BIN)
    parser.add_argument("--lib-dir", default=DEFAULT_LIB_DIR)
    args = parser.parse_args()

    ref = load_image(args.reference)
    dist = load_image(args.distorted)
    try:
        result = compute_vmaf(ref, dist, vmaf_bin=args.vmaf_bin, lib_dir=args.lib_dir)
    except FileNotFoundError as exc:
        print(f"Skipped (VMAF binary unavailable): {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"SSIM (libvmaf):    {result['ssim']:.6f}")
    print(f"MS-SSIM (libvmaf): {result['ms_ssim']:.6f}")
    print(f"VMAF:              {result['vmaf']:.3f}")


if __name__ == "__main__":
    main()
