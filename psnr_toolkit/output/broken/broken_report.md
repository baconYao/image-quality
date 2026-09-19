# Broken-Image Pattern Comparison

Golden reference: `output/golden.png`

Each pattern below is a standalone "broken image" style test image (not calibrated to any PSNR target) compared directly against the golden sample, the same way the black/white anchors were compared.

| Pattern | PSNR (dB) | SSIM | MS-SSIM | VMAF |
|---|---|---|---|---|
| block_glitch | 15.474 | 0.8782 | 0.7299 | 57.72 |
| chroma_loss | 9.644 | 0.7230 | 0.6551 | 97.34 |
| chroma_swap | 7.614 | 0.7081 | 0.6379 | 93.90 |
| heavy_compression | 23.567 | 0.7796 | 0.8641 | 63.38 |
| packet_loss | 18.243 | 0.9556 | 0.9260 | 92.67 |
| row_tearing | 10.885 | 0.6849 | 0.5712 | 0.00 |
