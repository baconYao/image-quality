"""Pipeline orchestrator: ties the individual algorithm scripts together.

This script does not implement any algorithm itself — it only calls the
dedicated modules (generate_*, degrade_*, metrics_*) so each algorithm stays
in its own file, per-task requirement. No ffmpeg is used anywhere.

Usage:
    uv run python scripts/run_pipeline.py --golden output/golden.png --outdir output
    uv run python scripts/run_pipeline.py --golden output_bbb/golden.png --outdir output_bbb --with-vmaf
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from common import load_image, save_image, target_list
from degrade_gaussian_blur import calibrate_blur_for_target
from degrade_gaussian_noise import calibrate_noise_for_target
from generate_solid_color import generate_solid_color
from metrics_psnr import compute_psnr
from metrics_ssim import compute_ms_ssim, compute_ssim

try:
    from metrics_vmaf import compute_vmaf
    _VMAF_IMPORT_OK = True
except Exception:  # pragma: no cover - optional dependency
    _VMAF_IMPORT_OK = False


def run(golden_path: str, outdir: str, with_vmaf: bool, step: float = 0.5) -> None:
    outdir_p = Path(outdir)
    golden = load_image(golden_path)
    height, width = golden.shape[:2]

    save_image(outdir_p / "golden.png", golden)
    save_image(outdir_p / "black.png", generate_solid_color((0, 0, 0), width, height))
    save_image(outdir_p / "white.png", generate_solid_color((255, 255, 255), width, height))

    rows = []
    for kind, calibrate in (("noise", calibrate_noise_for_target), ("blur", calibrate_blur_for_target)):
        for t in target_list(step=step):
            if kind == "noise":
                img, param, actual = calibrate(golden, t, seed=int(t * 10))
            else:
                img, param, actual = calibrate(golden, t)
            out_path = outdir_p / kind / f"psnr_{t:.1f}.png"
            save_image(out_path, img)

            row = {"type": kind, "target_psnr": t, "param": param, "psnr": actual}
            row["ssim"] = compute_ssim(golden, img)
            row["ms_ssim"] = compute_ms_ssim(golden, img)
            if with_vmaf and _VMAF_IMPORT_OK:
                try:
                    row["vmaf"] = compute_vmaf(golden, img)["vmaf"]
                except Exception as exc:  # pragma: no cover
                    print(f"  (vmaf skipped: {exc})")
                    row["vmaf"] = None
            rows.append(row)
            print(f"[{kind}] target={t:.1f} psnr={actual:.3f} ssim={row['ssim']:.4f} ms_ssim={row['ms_ssim']:.4f}")

    # anchors: golden vs black/white
    anchors = []
    for name in ("black", "white"):
        anchor_img = load_image(outdir_p / f"{name}.png")
        anchor = {
            "name": name,
            "psnr": compute_psnr(golden, anchor_img),
            "ssim": compute_ssim(golden, anchor_img),
            "ms_ssim": compute_ms_ssim(golden, anchor_img),
        }
        if with_vmaf and _VMAF_IMPORT_OK:
            try:
                anchor["vmaf"] = compute_vmaf(golden, anchor_img)["vmaf"]
            except Exception as exc:  # pragma: no cover
                print(f"  (vmaf skipped for {name}: {exc})")
        anchors.append(anchor)

    _write_csv(outdir_p / "metrics.csv", rows, anchors)
    print(f"Done. Metrics written to {outdir_p / 'metrics.csv'}")


def _write_csv(path: Path, rows: list[dict], anchors: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "target_psnr", "param", "psnr", "ssim", "ms_ssim", "vmaf"])
        for r in rows:
            writer.writerow([r["type"], r["target_psnr"], r["param"], r["psnr"], r["ssim"], r["ms_ssim"], r.get("vmaf", "")])
        for a in anchors:
            writer.writerow([f"anchor_{a['name']}", "", "", a["psnr"], a["ssim"], a["ms_ssim"], a.get("vmaf", "")])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full noise/blur PSNR sweep pipeline (OpenCV only).")
    parser.add_argument("--golden", required=True, help="Path to the golden reference image")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--with-vmaf", action="store_true", help="Also compute VMAF (requires a locally built vmaf binary)")
    parser.add_argument("--step", type=float, default=1.0, help="PSNR step between targets, e.g. 0.5 for finer 31-point sweep (default: 1.0, 16 points)")
    args = parser.parse_args()
    run(args.golden, args.outdir, args.with_vmaf, args.step)


if __name__ == "__main__":
    main()
