"""Shared image I/O helpers used by every algorithm script.

All image handling in this project goes through OpenCV (cv2) — no ffmpeg
binary is invoked anywhere in this package. Images are read/written as BGR
uint8 arrays, which is OpenCV's native in-memory format.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_image(path: str | Path) -> np.ndarray:
    """Load an image from disk as a BGR uint8 numpy array."""
    path = str(path)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"cv2 could not read image: {path}")
    return img


def save_image(path: str | Path, img: np.ndarray) -> None:
    """Save a BGR uint8 numpy array to disk (PNG, lossless)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), img)
    if not ok:
        raise IOError(f"cv2 failed to write image: {path}")


def target_list(hi: float = 30.0, lo: float = 15.0, step: float = 0.5) -> list[float]:
    """Return the list of target PSNR values: 30.0, 29.5, ..., 15.0."""
    n = round((hi - lo) / step) + 1
    return [round(hi - step * i, 1) for i in range(n)]
