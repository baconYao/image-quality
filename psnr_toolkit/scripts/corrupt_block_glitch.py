"""Simulate macroblock/block-decode corruption on top of a golden sample.

Real-world cause: during transcoding/streaming, if a macroblock fails to
decode (packet loss, bitstream corruption, hardware decode error), the
renderer often shows a solid-color block, a duplicated/shifted block from
elsewhere in the frame, or a block filled with garbage data instead of the
correct pixels.

This script reproduces that look by taking random blocks out of the golden
image and overwriting them with either:
  - a flat "error" color (common decoder fallback for undecodable blocks)
  - a shifted copy of another region of the same frame (common when the
    decoder repeats the last successfully decoded block)

Usage:
    uv run python scripts/corrupt_block_glitch.py output/golden.png output/broken/block_glitch.png
"""
from __future__ import annotations

import argparse

import numpy as np

from common import load_image, save_image

ERROR_COLORS_BGR = [
    (128, 128, 128),  # flat gray -- classic "undecoded macroblock" fallback
    (0, 200, 0),      # flat green -- classic decode-error / no-signal color
]


def block_glitch(
    img: np.ndarray,
    block_size: int = 32,
    corruption_ratio: float = 0.12,
    shifted_copy_prob: float = 0.5,
    seed: int = 42,
) -> np.ndarray:
    """Overwrite a random subset of macroblock-sized tiles with decode-error artifacts."""
    rng = np.random.default_rng(seed)
    out = img.copy()
    h, w = out.shape[:2]

    rows = h // block_size
    cols = w // block_size
    total_blocks = rows * cols
    n_corrupt = max(1, int(total_blocks * corruption_ratio))

    block_indices = rng.choice(total_blocks, size=n_corrupt, replace=False)
    for idx in block_indices:
        r, c = divmod(int(idx), cols)
        y0, y1 = r * block_size, (r + 1) * block_size
        x0, x1 = c * block_size, (c + 1) * block_size

        if rng.random() < shifted_copy_prob:
            # Duplicate/shift artifact: copy a block from a random other location
            # (simulates a decoder repeating a previously-decoded reference block).
            src_r = int(rng.integers(0, rows))
            src_c = int(rng.integers(0, cols))
            sy0, sy1 = src_r * block_size, (src_r + 1) * block_size
            sx0, sx1 = src_c * block_size, (src_c + 1) * block_size
            out[y0:y1, x0:x1] = img[sy0:sy1, sx0:sx1]
        else:
            # Flat error-color block (undecodable macroblock fallback).
            color = ERROR_COLORS_BGR[int(rng.integers(0, len(ERROR_COLORS_BGR)))]
            out[y0:y1, x0:x1] = color

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate macroblock decode-error corruption on a golden image.")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--block-size", type=int, default=32)
    parser.add_argument("--corruption-ratio", type=float, default=0.12, help="Fraction of blocks to corrupt (0-1)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    golden = load_image(args.golden)
    corrupted = block_glitch(golden, args.block_size, args.corruption_ratio, seed=args.seed)
    save_image(args.output, corrupted)
    print(f"Saved block-glitch corruption: {args.output} ({args.corruption_ratio:.0%} of blocks corrupted)")


if __name__ == "__main__":
    main()
