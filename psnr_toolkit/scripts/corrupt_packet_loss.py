"""Simulate packet-loss / undecoded-region corruption on top of a golden sample.

Real-world cause: when streaming over an unreliable network (RTP/UDP packet
loss, dropped segments in adaptive bitrate streaming), an entire contiguous
region of the frame -- often a horizontal band, since most codecs decode in
raster-scan slice order -- fails to decode and the player either freezes that
region, or the renderer fills it with a flat placeholder color, until the next
keyframe/IDR arrives.

This script blanks out one or more contiguous bands/regions of the golden
image with a flat placeholder color to reproduce that look.

Usage:
    uv run python scripts/corrupt_packet_loss.py output/golden.png output/broken/packet_loss.png
"""
from __future__ import annotations

import argparse

import numpy as np

from common import load_image, save_image

PLACEHOLDER_COLOR_BGR = (128, 128, 128)  # flat gray, common "no data yet" placeholder


def packet_loss(
    img: np.ndarray,
    band_height_ratio: float = 0.18,
    band_start_ratio: float = 0.35,
    color_bgr: tuple[int, int, int] = PLACEHOLDER_COLOR_BGR,
) -> np.ndarray:
    """Blank out one contiguous horizontal band with a flat placeholder color."""
    out = img.copy()
    h, w = out.shape[:2]

    y0 = int(h * band_start_ratio)
    band_h = int(h * band_height_ratio)
    y1 = min(h, y0 + band_h)

    out[y0:y1, :] = color_bgr
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate packet-loss / undecoded-region corruption on a golden image.")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--band-height-ratio", type=float, default=0.18, help="Fraction of frame height blanked out")
    parser.add_argument("--band-start-ratio", type=float, default=0.35, help="Where the band starts (fraction of height)")
    args = parser.parse_args()

    golden = load_image(args.golden)
    corrupted = packet_loss(golden, args.band_height_ratio, args.band_start_ratio)
    save_image(args.output, corrupted)
    print(f"Saved packet-loss corruption: {args.output} (band height={args.band_height_ratio:.0%} of frame)")


if __name__ == "__main__":
    main()
