"""Simulate chroma/color-channel corruption on a golden sample.

Real-world cause: color space mishandling during transcoding is a very common
real-world bug class -- e.g. a wrong YUV<->RGB matrix (BT.601 vs BT.709),
swapped Cb/Cr planes, chroma subsampling misalignment, or dropped chroma
planes when a stream is corrupted. This produces washed-out colors, color
casts (commonly a green or purple tint), or fully desaturated ("grayscale
luma-only") frames while the luma/brightness stays intact.

This script converts the golden image to YCrCb, then reproduces two common
failure modes:
  - "chroma_loss": Cr/Cb set to neutral (128) -> fully desaturated frame, as
    if the chroma planes never arrived/decoded.
  - "chroma_swap": Cr and Cb planes swapped -> classic color-cast bug from a
    wrong channel order / matrix during transcoding.

Usage:
    uv run python scripts/corrupt_color_channel.py output/golden.png output/broken/chroma_loss.png --mode chroma_loss
    uv run python scripts/corrupt_color_channel.py output/golden.png output/broken/chroma_swap.png --mode chroma_swap
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from common import load_image, save_image


def chroma_loss(img: np.ndarray) -> np.ndarray:
    """Zero out chroma (Cr/Cb -> neutral 128), simulating dropped/undecoded chroma planes."""
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 1] = 128
    ycrcb[:, :, 2] = 128
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def chroma_swap(img: np.ndarray) -> np.ndarray:
    """Swap Cr/Cb planes, simulating a wrong color-matrix/channel-order transcode bug."""
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    swapped = ycrcb.copy()
    swapped[:, :, 1] = ycrcb[:, :, 2]
    swapped[:, :, 2] = ycrcb[:, :, 1]
    return cv2.cvtColor(swapped, cv2.COLOR_YCrCb2BGR)


MODES = {
    "chroma_loss": chroma_loss,
    "chroma_swap": chroma_swap,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate chroma/color-channel corruption on a golden image.")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--mode", choices=list(MODES.keys()), default="chroma_loss")
    args = parser.parse_args()

    golden = load_image(args.golden)
    corrupted = MODES[args.mode](golden)
    save_image(args.output, corrupted)
    print(f"Saved color-channel corruption ({args.mode}): {args.output}")


if __name__ == "__main__":
    main()
