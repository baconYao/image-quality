# ffmpeg vs OpenCV cross-validation (output_bbb)

Compares the pure-OpenCV metric implementations used throughout this
toolkit against ffmpeg's native `psnr`/`ssim` CLI filters, and against
the standalone libvmaf binary's `float_ms_ssim`/`vmaf` features.

Thresholds: PSNR delta > 0.5 dB -> WARN, SSIM/MS-SSIM delta > 0.05 -> WARN.

| Sample | PSNR (OpenCV) | PSNR (ffmpeg) | ΔPSNR | flag | SSIM (OpenCV) | SSIM (ffmpeg) | ΔSSIM | flag | MS-SSIM (OpenCV) | MS-SSIM (libvmaf) | ΔMS-SSIM | flag | VMAF (libvmaf) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noise@30.0dB | 29.964 | 29.964 | 0.000 | OK | 0.6875 | 0.7256 | 0.0381 | OK | 0.9723 | 0.9791 | 0.0069 | OK | 91.06 |
| noise@25.0dB | 24.997 | 24.997 | 0.000 | OK | 0.4514 | 0.5001 | 0.0487 | OK | 0.9347 | 0.9428 | 0.0081 | OK | 83.72 |
| noise@20.0dB | 19.956 | 19.956 | 0.000 | OK | 0.2387 | 0.2789 | 0.0402 | OK | 0.8575 | 0.8585 | 0.0010 | OK | 68.47 |
| noise@15.0dB | 15.009 | 15.009 | 0.000 | OK | 0.1039 | 0.1263 | 0.0224 | OK | 0.7190 | 0.7056 | 0.0134 | OK | 45.26 |
| blur@30.0dB | 30.018 | 30.018 | 0.000 | OK | 0.8631 | 0.8733 | 0.0102 | OK | 0.9771 | 0.9591 | 0.0179 | OK | 38.88 |
| blur@25.0dB | 25.038 | 25.038 | 0.000 | OK | 0.6567 | 0.6083 | 0.0484 | OK | 0.8275 | 0.7624 | 0.0651 | WARN | 0.00 |
| blur@20.0dB | 20.019 | 20.019 | 0.000 | OK | 0.5840 | 0.4978 | 0.0862 | WARN | 0.5163 | 0.4561 | 0.0603 | WARN | 1.79 |
| blur@15.0dB | 15.008 | 15.008 | 0.000 | OK | 0.5388 | 0.4572 | 0.0816 | WARN | 0.4464 | 0.4354 | 0.0110 | OK | 3.43 |
| black | 8.356 | 8.356 | 0.000 | OK | 0.0018 | 0.0000 | 0.0018 | OK | 0.0013 | 0.3822 | 0.3809 | WARN | 3.38 |
| white | 3.088 | 3.088 | 0.000 | OK | 0.3103 | 0.2608 | 0.0496 | OK | 0.2462 | 0.4158 | 0.1695 | WARN | 3.38 |
| broken/block_glitch | 19.847 | 19.847 | 0.000 | OK | 0.8854 | 0.8898 | 0.0044 | OK | 0.7916 | 0.7991 | 0.0075 | OK | 61.33 |
| broken/packet_loss | 19.040 | 19.040 | 0.000 | OK | 0.8935 | 0.8800 | 0.0135 | OK | 0.8603 | 0.8591 | 0.0012 | OK | 57.94 |
| broken/row_tearing | 16.816 | 16.816 | 0.000 | OK | 0.4101 | 0.3266 | 0.0835 | WARN | 0.3673 | 0.3223 | 0.0450 | OK | 4.97 |
| broken/heavy_compression | 22.527 | 22.527 | 0.000 | OK | 0.5806 | 0.5537 | 0.0269 | OK | 0.7237 | 0.7757 | 0.0520 | WARN | 30.38 |
| broken/chroma_loss | 17.056 | 17.056 | 0.000 | OK | 0.9186 | 0.9146 | 0.0040 | OK | 0.8762 | 0.9997 | 0.1235 | WARN | 97.13 |
| broken/chroma_swap | 14.075 | 14.075 | 0.000 | OK | 0.8646 | 0.8564 | 0.0081 | OK | 0.7813 | 0.9978 | 0.2164 | WARN | 92.55 |

**Summary**: 16 samples compared, 9 flagged WARN.

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
