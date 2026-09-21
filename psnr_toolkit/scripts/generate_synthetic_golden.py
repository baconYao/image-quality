"""Generate a synthetic golden sample image using pure OpenCV/numpy.

This replaces the previous `ffmpeg -f lavfi -i testsrc2=...` approach: it draws
color bars, a smooth gradient, geometric shapes and text directly with cv2
drawing primitives, giving a content-rich reference image with no ffmpeg
dependency at all. Resolution defaults to 1920x1080 but can be overridden
(e.g. --width 3840 --height 2160 for a 4K/UHD golden sample).

Usage:
    uv run python scripts/generate_synthetic_golden.py output/golden.png
    uv run python scripts/generate_synthetic_golden.py output_4k/golden.png --width 3840 --height 2160
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from common import save_image

WIDTH, HEIGHT = 1920, 1080


def _draw_color_bars(img: np.ndarray, width: int, height: int) -> None:
    bars_bgr = [
        (255, 255, 255),  # white
        (0, 255, 255),    # yellow
        (255, 255, 0),    # cyan
        (0, 255, 0),      # green
        (255, 0, 255),    # magenta
        (0, 0, 255),      # red
        (255, 0, 0),      # blue
        (0, 0, 0),        # black
    ]
    n = len(bars_bgr)
    bar_h = height // 3
    bar_w = width // n
    for i, color in enumerate(bars_bgr):
        x0, x1 = i * bar_w, (i + 1) * bar_w if i < n - 1 else width
        img[0:bar_h, x0:x1] = color


def _draw_gradient(img: np.ndarray, width: int, height: int) -> None:
    y0, y1 = height // 3, 2 * height // 3
    ramp = np.linspace(0, 255, width, dtype=np.uint8)
    gradient_row = np.stack([ramp, np.roll(ramp, width // 3), np.roll(ramp, 2 * width // 3)], axis=1)
    img[y0:y1, :] = gradient_row[np.newaxis, :, :]


def _draw_shapes_and_text(img: np.ndarray, width: int, height: int) -> None:
    y0 = 2 * height // 3
    rng = np.random.default_rng(1234)

    # Textured background noise pattern (deterministic) so the region has
    # high-frequency detail for degradation experiments to act on.
    region = img[y0:height, :]
    checker = ((np.indices(region.shape[:2]).sum(axis=0) // 20) % 2).astype(np.uint8) * 60 + 40
    region[:, :] = checker[:, :, np.newaxis]

    cv2.circle(img, (width // 6, y0 + (height - y0) // 2), 120, (0, 128, 255), -1)
    cv2.rectangle(img, (width // 3, y0 + 40), (width // 3 + 300, y0 + 240), (255, 0, 128), -1)
    pts = np.array([[width // 2 + 100, height - 40], [width // 2 + 300, height - 40], [width // 2 + 200, y0 + 40]])
    cv2.fillPoly(img, [pts], (128, 255, 0))

    for _ in range(30):
        center = (int(rng.integers(width * 2 // 3, width - 20)), int(rng.integers(y0 + 20, height - 20)))
        radius = int(rng.integers(5, 40))
        color = tuple(int(c) for c in rng.integers(0, 255, size=3))
        cv2.circle(img, center, radius, color, -1)

    cv2.putText(
        img, f"PSNR GOLDEN SAMPLE {width}x{height}", (60, y0 - 20),
        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA,
    )


def generate_synthetic_golden(width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    _draw_color_bars(img, width, height)
    _draw_gradient(img, width, height)
    _draw_shapes_and_text(img, width, height)
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic golden sample (OpenCV only).")
    parser.add_argument("output", nargs="?", default="output/golden.png", help="Output PNG path")
    parser.add_argument("--width", type=int, default=WIDTH, help="Image width (default: 1920)")
    parser.add_argument("--height", type=int, default=HEIGHT, help="Image height (default: 1080)")
    args = parser.parse_args()

    img = generate_synthetic_golden(args.width, args.height)
    save_image(args.output, img)
    print(f"Saved synthetic golden sample: {args.output} ({args.width}x{args.height})")


if __name__ == "__main__":
    main()
