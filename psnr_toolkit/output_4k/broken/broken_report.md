# Broken-Image Pattern Comparison

Golden reference: `output_4k/golden.png`

Each pattern below is a standalone "broken image" style test image (not calibrated to any PSNR target) compared directly against the golden sample, the same way the black/white anchors were compared.

| Pattern | PSNR (dB) | SSIM | MS-SSIM | VMAF |
|---|---|---|---|---|
| block_glitch | 15.449 | 0.8769 | 0.6882 | 65.23 |
| chroma_loss | 10.067 | 0.7587 | 0.7276 | 97.44 |
| chroma_swap | 8.034 | 0.7395 | 0.7071 | 95.46 |
| heavy_compression | 24.254 | 0.7851 | 0.8817 | 72.62 |
| packet_loss | 18.245 | 0.9601 | 0.9429 | 93.76 |
| row_tearing | 11.174 | 0.6613 | 0.5302 | 0.00 |
