# ffmpeg vs OpenCV cross-validation (output)

Compares the pure-OpenCV metric implementations used throughout this
toolkit against ffmpeg's native `psnr`/`ssim` CLI filters, and against
the standalone libvmaf binary's `float_ms_ssim`/`vmaf` features.

Thresholds: PSNR delta > 0.5 dB -> WARN, SSIM/MS-SSIM delta > 0.05 -> WARN.

| Sample | PSNR (OpenCV) | PSNR (ffmpeg) | ΔPSNR | flag | SSIM (OpenCV) | SSIM (ffmpeg) | ΔSSIM | flag | MS-SSIM (OpenCV) | MS-SSIM (libvmaf) | ΔMS-SSIM | flag | VMAF (libvmaf) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noise@30.0dB | 30.007 | 30.007 | 0.000 | OK | 0.5352 | 0.4870 | 0.0481 | OK | 0.8644 | 0.9706 | 0.1062 | WARN | 89.99 |
| noise@25.0dB | 25.032 | 25.032 | 0.000 | OK | 0.3132 | 0.3109 | 0.0023 | OK | 0.7858 | 0.9229 | 0.1371 | WARN | 83.51 |
| noise@20.0dB | 19.965 | 19.965 | 0.000 | OK | 0.1604 | 0.1741 | 0.0137 | OK | 0.6915 | 0.8235 | 0.1320 | WARN | 69.63 |
| noise@15.0dB | 14.995 | 14.995 | 0.000 | OK | 0.0755 | 0.0865 | 0.0110 | OK | 0.5665 | 0.6706 | 0.1042 | WARN | 46.67 |
| blur@30.0dB | 29.961 | 29.961 | 0.000 | OK | 0.9487 | 0.9411 | 0.0076 | OK | 0.9942 | 0.9903 | 0.0039 | OK | 56.19 |
| blur@25.0dB | 25.000 | 25.000 | 0.000 | OK | 0.8716 | 0.8569 | 0.0147 | OK | 0.9563 | 0.9455 | 0.0109 | OK | 0.00 |
| blur@20.0dB | 20.045 | 20.045 | 0.000 | OK | 0.7888 | 0.7428 | 0.0460 | OK | 0.7520 | 0.7521 | 0.0000 | OK | 0.00 |
| blur@15.0dB | 15.026 | 15.026 | 0.000 | OK | 0.6729 | 0.6321 | 0.0408 | OK | 0.5277 | 0.6432 | 0.1155 | WARN | 0.00 |
| black | 4.707 | 4.707 | 0.000 | OK | 0.1881 | 0.1854 | 0.0026 | OK | 0.1574 | 0.5788 | 0.4214 | WARN | 0.00 |
| white | 3.536 | 3.536 | 0.000 | OK | 0.4989 | 0.4895 | 0.0094 | OK | 0.3891 | 0.6471 | 0.2580 | WARN | 0.00 |
| broken/block_glitch | 15.474 | 15.474 | 0.000 | OK | 0.8782 | 0.8961 | 0.0179 | OK | 0.7299 | 0.7810 | 0.0511 | WARN | 57.72 |
| broken/packet_loss | 18.243 | 18.243 | 0.000 | OK | 0.9556 | 0.9560 | 0.0004 | OK | 0.9260 | 0.9559 | 0.0298 | OK | 92.67 |
| broken/row_tearing | 10.885 | 10.885 | 0.000 | OK | 0.6849 | 0.6581 | 0.0268 | OK | 0.5712 | 0.5998 | 0.0286 | OK | 0.00 |
| broken/heavy_compression | 23.567 | 23.567 | 0.000 | OK | 0.7796 | 0.7583 | 0.0213 | OK | 0.8641 | 0.9458 | 0.0817 | WARN | 63.38 |
| broken/chroma_loss | 9.644 | 9.644 | 0.000 | OK | 0.7230 | 0.7257 | 0.0027 | OK | 0.6551 | 0.9996 | 0.3445 | WARN | 97.34 |
| broken/chroma_swap | 7.614 | 7.614 | 0.000 | OK | 0.7081 | 0.7091 | 0.0011 | OK | 0.6379 | 0.9873 | 0.3494 | WARN | 93.90 |

**Summary**: 16 samples compared, 11 flagged WARN.

Notes:
- PSNR: OpenCV (`cv2.PSNR`) and ffmpeg (`-lavfi psnr`) use the identical MSE-based
  formula and agree to within rounding error on every sample tested.
- SSIM: OpenCV (`cv2.quality.QualitySSIM`, 11x11 Gaussian window, Wang et al. 2003)
  and ffmpeg's `ssim` filter (8x8 uniform window) are two different *valid* SSIM
  variants, so a small systematic delta (commonly 0.01-0.05) is expected and not a bug.
- MS-SSIM: OpenCV's pyrDown-pyramid implementation is compared against libvmaf's
  `float_ms_ssim` feature (a from-scratch MS-SSIM implementation) — again expect a
  small delta from window/scale differences, not pixel-level identity.
- VMAF has no second OpenCV implementation to diff against; it is included here for
  reference and is always computed via the same standalone libvmaf binary used by
  `metrics_vmaf.py` in the main pipeline.
