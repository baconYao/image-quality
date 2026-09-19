"""PSNR / SSIM via the ffmpeg command line (used ONLY to cross-check the
OpenCV implementations in metrics_psnr.py / metrics_ssim.py; it is not part
of the main pipeline).

Why this exists
----------------
Every other script in this toolkit intentionally avoids ffmpeg. But to trust
the pure-OpenCV numbers we need an independent second implementation to
compare against. ffmpeg ships native `psnr` and `ssim` video filters that are
widely used as an industry reference, so we shell out to them here.

MS-SSIM / VMAF are NOT computed by this script: the system ffmpeg binary on
this machine was built WITHOUT `--enable-libvmaf` (`ffmpeg -h filter=libvmaf`
reports "Unknown filter"), so there is no ffmpeg-native way to get them
without recompiling ffmpeg from source. Since libvmaf's own `vmaf` CLI
(already used by metrics_vmaf.py) is the *exact same upstream library* that
ffmpeg's `-vf libvmaf` would call if it were compiled in, we treat that
standalone binary's `vmaf` / `float_ms_ssim` output as the ffmpeg-equivalent
ground truth for those two metrics instead of re-implementing them here.

Usage:
    uv run python scripts/metrics_ffmpeg.py output/golden.png output/noise/psnr_20.0.png
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

_PSNR_AVG_RE = re.compile(r"average:(inf|[\d.]+)")
_SSIM_ALL_RE = re.compile(r"All:([\d.]+)")


def _run_ffmpeg_filter(ref_path: str, dist_path: str, filter_name: str, ffmpeg_bin: str) -> str:
    """Run ffmpeg with a 2-input filter (psnr/ssim) and return its stderr text."""
    cmd = [
        ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "info",
        "-i", str(ref_path), "-i", str(dist_path),
        "-lavfi", filter_name, "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({filter_name}): {proc.stderr[-800:]}")
    return proc.stderr


def compute_psnr_ffmpeg(ref_path: str, dist_path: str, ffmpeg_bin: str = "ffmpeg") -> float:
    """PSNR (dB) between two images using ffmpeg's native `psnr` filter."""
    stderr = _run_ffmpeg_filter(ref_path, dist_path, "psnr", ffmpeg_bin)
    match = _PSNR_AVG_RE.search(stderr)
    if not match:
        raise RuntimeError(f"could not parse PSNR from ffmpeg output:\n{stderr}")
    value = match.group(1)
    return float("inf") if value == "inf" else float(value)


def compute_ssim_ffmpeg(ref_path: str, dist_path: str, ffmpeg_bin: str = "ffmpeg") -> float:
    """SSIM (0-1) between two images using ffmpeg's native `ssim` filter (the "All" value)."""
    stderr = _run_ffmpeg_filter(ref_path, dist_path, "ssim", ffmpeg_bin)
    match = _SSIM_ALL_RE.search(stderr)
    if not match:
        raise RuntimeError(f"could not parse SSIM from ffmpeg output:\n{stderr}")
    return float(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute PSNR/SSIM between two images via ffmpeg's CLI filters.")
    parser.add_argument("reference")
    parser.add_argument("distorted")
    parser.add_argument("--ffmpeg-bin", default="ffmpeg")
    args = parser.parse_args()

    try:
        psnr = compute_psnr_ffmpeg(args.reference, args.distorted, args.ffmpeg_bin)
        ssim = compute_ssim_ffmpeg(args.reference, args.distorted, args.ffmpeg_bin)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"ffmpeg comparison failed: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"PSNR (ffmpeg): {psnr:.6f} dB")
    print(f"SSIM (ffmpeg): {ssim:.6f}")


if __name__ == "__main__":
    main()
