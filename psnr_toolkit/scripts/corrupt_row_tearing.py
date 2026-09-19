"""Simulate row-tearing / desync corruption on top of a golden sample.

Real-world cause: horizontal tearing/desync artifacts appear when frame
buffer writes and reads get out of sync (e.g. dropped sync signal, buggy
hardware decoder, or a transcoder that mis-handles interlaced/field order),
causing horizontal strips of the image to be horizontally offset from where
they should be.

This script slices the golden image into horizontal bands and shifts each
band left/right by a random amount (wrapping around) to reproduce that look.

Usage:
    uv run python scripts/corrupt_row_tearing.py output/golden.png output/broken/row_tearing.png
"""
from __future__ import annotations

import argparse

import numpy as np

from common import load_image, save_image


def row_tearing(
    img: np.ndarray,
    band_count: int = 10,
    max_shift_ratio: float = 0.06,
    seed: int = 42,
) -> np.ndarray:
    """Shift horizontal bands of the image left/right by a random amount (wraps around)."""
    rng = np.random.default_rng(seed)
    out = img.copy()
    h, w = out.shape[:2]
    max_shift = max(1, int(w * max_shift_ratio))

    band_bounds = np.linspace(0, h, band_count + 1).astype(int)
    for i in range(band_count):
        y0, y1 = band_bounds[i], band_bounds[i + 1]
        shift = int(rng.integers(-max_shift, max_shift + 1))
        if shift == 0:
            continue
        out[y0:y1, :] = np.roll(img[y0:y1, :], shift, axis=1)

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate row-tearing/desync corruption on a golden image.")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--band-count", type=int, default=10)
    parser.add_argument("--max-shift-ratio", type=float, default=0.06, help="Max horizontal shift as a fraction of width")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    golden = load_image(args.golden)
    corrupted = row_tearing(golden, args.band_count, args.max_shift_ratio, seed=args.seed)
    save_image(args.output, corrupted)
    print(f"Saved row-tearing corruption: {args.output} ({args.band_count} bands, max shift {args.max_shift_ratio:.0%} of width)")


if __name__ == "__main__":
    main()
