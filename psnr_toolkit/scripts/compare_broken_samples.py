"""Compare a set of "broken image" patterns directly against a golden sample.

Each broken pattern is scored once against the golden (no PSNR calibration /
sweep, unlike the noise & blur degradation sets) -- same spirit as the
existing golden-vs-black / golden-vs-white anchor comparison.

Usage:
    uv run python scripts/compare_broken_samples.py output/golden.png output/broken
    uv run python scripts/compare_broken_samples.py output/golden.png output/broken --with-vmaf
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from common import load_image
from metrics_psnr import compute_psnr
from metrics_ssim import compute_ssim, compute_ms_ssim

try:
    from metrics_vmaf import compute_vmaf
except Exception:  # pragma: no cover - vmaf binary may not be installed
    compute_vmaf = None


def compare_broken_samples(golden_path: str, broken_dir: str, with_vmaf: bool = False) -> list[dict]:
    golden = load_image(golden_path)
    broken_dir_p = Path(broken_dir)
    png_files = sorted(broken_dir_p.glob("*.png"))

    rows = []
    for png_path in png_files:
        dist = load_image(png_path)
        if dist.shape != golden.shape:
            print(f"  skip {png_path.name}: shape mismatch {dist.shape} vs golden {golden.shape}")
            continue

        psnr = compute_psnr(golden, dist)
        ssim = compute_ssim(golden, dist)
        ms_ssim = compute_ms_ssim(golden, dist)
        vmaf = None
        if with_vmaf and compute_vmaf is not None:
            vmaf = compute_vmaf(golden, dist)["vmaf"]

        row = {
            "pattern": png_path.stem,
            "psnr": psnr,
            "ssim": ssim,
            "ms_ssim": ms_ssim,
            "vmaf": vmaf,
        }
        rows.append(row)
        vmaf_str = f"{vmaf:.2f}" if vmaf is not None else "n/a"
        print(f"  {png_path.name:24s} PSNR={psnr:7.3f}dB  SSIM={ssim:.4f}  MS-SSIM={ms_ssim:.4f}  VMAF={vmaf_str}")

    return rows


def write_csv(rows: list[dict], csv_path: str) -> None:
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["pattern", "psnr", "ssim", "ms_ssim", "vmaf"])
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict], golden_path: str, report_path: str) -> None:
    lines = [
        "# Broken-Image Pattern Comparison\n",
        f"\nGolden reference: `{golden_path}`\n",
        "\nEach pattern below is a standalone \"broken image\" style test image "
        "(not calibrated to any PSNR target) compared directly against the golden sample, "
        "the same way the black/white anchors were compared.\n",
        "\n| Pattern | PSNR (dB) | SSIM | MS-SSIM | VMAF |",
        "\n|---|---|---|---|---|",
    ]
    for row in rows:
        vmaf_str = f"{row['vmaf']:.2f}" if row["vmaf"] is not None else "n/a"
        psnr_str = "inf" if row["psnr"] == float("inf") else f"{row['psnr']:.3f}"
        lines.append(f"\n| {row['pattern']} | {psnr_str} | {row['ssim']:.4f} | {row['ms_ssim']:.4f} | {vmaf_str} |")
    lines.append("\n")
    Path(report_path).write_text("".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare broken-image patterns against a golden sample (OpenCV only).")
    parser.add_argument("golden", help="Path to the golden reference image")
    parser.add_argument("broken_dir", help="Directory containing broken-pattern PNGs")
    parser.add_argument("--with-vmaf", action="store_true", help="Also compute VMAF (requires external vmaf binary)")
    parser.add_argument("--csv", default=None, help="Output CSV path (default: <broken_dir>/broken_metrics.csv)")
    parser.add_argument("--report", default=None, help="Output Markdown report path (default: <broken_dir>/broken_report.md)")
    args = parser.parse_args()

    csv_path = args.csv or str(Path(args.broken_dir) / "broken_metrics.csv")
    report_path = args.report or str(Path(args.broken_dir) / "broken_report.md")

    print(f"Comparing broken patterns in {args.broken_dir} against golden {args.golden} ...")
    rows = compare_broken_samples(args.golden, args.broken_dir, with_vmaf=args.with_vmaf)
    write_csv(rows, csv_path)
    write_report(rows, args.golden, report_path)
    print(f"\nWrote: {csv_path}")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    main()
