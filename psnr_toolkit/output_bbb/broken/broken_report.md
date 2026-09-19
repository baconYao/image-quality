# Broken-Image Pattern Comparison

Golden reference: `output_bbb/golden.png`

Each pattern below is a standalone "broken image" style test image (not calibrated to any PSNR target) compared directly against the golden sample, the same way the black/white anchors were compared.

| Pattern | PSNR (dB) | SSIM | MS-SSIM | VMAF |
|---|---|---|---|---|
| block_glitch | 19.847 | 0.8854 | 0.7916 | 61.33 |
| chroma_loss | 17.056 | 0.9186 | 0.8762 | 97.13 |
| chroma_swap | 14.075 | 0.8646 | 0.7813 | 92.55 |
| heavy_compression | 22.527 | 0.5806 | 0.7237 | 30.38 |
| packet_loss | 19.040 | 0.8935 | 0.8603 | 57.94 |
| row_tearing | 16.816 | 0.4101 | 0.3673 | 4.97 |
