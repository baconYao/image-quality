"""Apply every transcode-corruption algorithm to a golden sample in one go.

This is an orchestrator only -- it does not implement any corruption itself,
it just calls each `corrupt_*.py` module and saves the result, mirroring the
style of `run_pipeline.py`.

Usage:
    uv run python scripts/generate_transcode_corruptions.py output/golden.png output/broken
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_image, save_image
from corrupt_block_glitch import block_glitch
from corrupt_packet_loss import packet_loss
from corrupt_row_tearing import row_tearing
from corrupt_heavy_compression import heavy_compression
from corrupt_color_channel import chroma_loss, chroma_swap


def generate_all(golden_path: str, outdir: str) -> None:
    golden = load_image(golden_path)
    outdir_p = Path(outdir)

    variants = {
        "block_glitch.png": block_glitch(golden),
        "packet_loss.png": packet_loss(golden),
        "row_tearing.png": row_tearing(golden),
        "heavy_compression.png": heavy_compression(golden, quality=3),
        "chroma_loss.png": chroma_loss(golden),
        "chroma_swap.png": chroma_swap(golden),
    }

    for name, img in variants.items():
        out_path = outdir_p / name
        save_image(out_path, img)
        print(f"Saved: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all transcode-corruption variants from a golden image.")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("outdir", help="Output directory")
    args = parser.parse_args()

    generate_all(args.golden, args.outdir)


if __name__ == "__main__":
    main()
