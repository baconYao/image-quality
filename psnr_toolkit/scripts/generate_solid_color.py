"""Generate solid-color reference images (e.g. full black / full white) via numpy.

No ffmpeg involved — a solid color image is just a constant-valued array.

Usage:
    uv run python scripts/generate_solid_color.py black output/black.png
    uv run python scripts/generate_solid_color.py white output/white.png
    uv run python scripts/generate_solid_color.py 128,64,255 output/custom.png
"""
from __future__ import annotations

import argparse

import numpy as np

from common import save_image

NAMED_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
}


def generate_solid_color(color_bgr: tuple[int, int, int], width: int = 1920, height: int = 1080) -> np.ndarray:
    img = np.empty((height, width, 3), dtype=np.uint8)
    img[:, :] = color_bgr
    return img


def parse_color(value: str) -> tuple[int, int, int]:
    if value in NAMED_COLORS:
        return NAMED_COLORS[value]
    parts = [int(p) for p in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("color must be 'black', 'white', or 'B,G,R'")
    return tuple(parts)  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a solid-color 1920x1080 image (OpenCV/numpy only).")
    parser.add_argument("color", type=parse_color, help="'black', 'white', or 'B,G,R' (e.g. 0,255,0)")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()

    img = generate_solid_color(args.color, args.width, args.height)
    save_image(args.output, img)
    print(f"Saved solid color image: {args.output} (BGR={args.color}, {args.width}x{args.height})")


if __name__ == "__main__":
    main()
