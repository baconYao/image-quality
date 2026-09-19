"""Generate a synthetic 1920x1080 golden sample image using pure OpenCV/numpy.

This replaces the previous `ffmpeg -f lavfi -i testsrc2=...` approach: it draws
color bars, a smooth gradient, geometric shapes and text directly with cv2
drawing primitives, giving a content-rich reference image with no ffmpeg
dependency at all.

Usage:
    uv run python scripts/generate_synthetic_golden.py output/golden.png
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from common import save_image

WIDTH, HEIGHT = 1920, 1080


def _draw_color_bars(img: np.ndarray) -> None:
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
    bar_h = HEIGHT // 3
    bar_w = WIDTH // n
    for i, color in enumerate(bars_bgr):
        x0, x1 = i * bar_w, (i + 1) * bar_w if i < n - 1 else WIDTH
        img[0:bar_h, x0:x1] = color


def _draw_gradient(img: np.ndarray) -> None:
    y0, y1 = HEIGHT // 3, 2 * HEIGHT // 3
    ramp = np.linspace(0, 255, WIDTH, dtype=np.uint8)
    gradient_row = np.stack([ramp, np.roll(ramp, WIDTH // 3), np.roll(ramp, 2 * WIDTH // 3)], axis=1)
    img[y0:y1, :] = gradient_row[np.newaxis, :, :]


def _draw_shapes_and_text(img: np.ndarray) -> None:
    y0 = 2 * HEIGHT // 3
    rng = np.random.default_rng(1234)

    # Textured background noise pattern (deterministic) so the region has
    # high-frequency detail for degradation experiments to act on.
    region = img[y0:HEIGHT, :]
    checker = ((np.indices(region.shape[:2]).sum(axis=0) // 20) % 2).astype(np.uint8) * 60 + 40
    region[:, :] = checker[:, :, np.newaxis]

    cv2.circle(img, (WIDTH // 6, y0 + (HEIGHT - y0) // 2), 120, (0, 128, 255), -1)
    cv2.rectangle(img, (WIDTH // 3, y0 + 40), (WIDTH // 3 + 300, y0 + 240), (255, 0, 128), -1)
    pts = np.array([[WIDTH // 2 + 100, HEIGHT - 40], [WIDTH // 2 + 300, HEIGHT - 40], [WIDTH // 2 + 200, y0 + 40]])
    cv2.fillPoly(img, [pts], (128, 255, 0))

    for _ in range(30):
        center = (int(rng.integers(WIDTH * 2 // 3, WIDTH - 20)), int(rng.integers(y0 + 20, HEIGHT - 20)))
        radius = int(rng.integers(5, 40))
        color = tuple(int(c) for c in rng.integers(0, 255, size=3))
        cv2.circle(img, center, radius, color, -1)

    cv2.putText(
        img, "PSNR GOLDEN SAMPLE 1920x1080", (60, y0 - 20),
        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA,
    )


def generate_synthetic_golden() -> np.ndarray:
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    _draw_color_bars(img)
    _draw_gradient(img)
    _draw_shapes_and_text(img)
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic 1920x1080 golden sample (OpenCV only).")
    parser.add_argument("output", nargs="?", default="output/golden.png", help="Output PNG path")
    args = parser.parse_args()

    img = generate_synthetic_golden()
    save_image(args.output, img)
    print(f"Saved synthetic golden sample: {args.output} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
