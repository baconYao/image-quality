# PSNR / SSIM / MS-SSIM / VMAF 視覺品質比較實驗

這個 repo 用來回答一個問題：**PSNR 數值到底跟人眼實際看到的畫質差異，有多大關係？**

透過對同一張 golden sample 套用「可控制的失真」（雜訊、模糊、以及模擬真實轉檔/串流損壞），
在 30.0 → 15.0 dB（每 1.0 dB 一張）的範圍內產生比對樣本，並用 PSNR、SSIM、MS-SSIM、VMAF
四種指標評分，藉此觀察「同樣的 PSNR 數值，在不同失真類型下，人眼感受與其他指標是否一致」。

## 目前主要工具：`psnr_toolkit/`

**請直接使用 `psnr_toolkit/`，這是目前唯一持續維護、可正常運作的版本。**

- 100% 使用 [OpenCV](https://opencv.org/)（`opencv-contrib-python`）+ `numpy`，**不依賴 ffmpeg**
- 用 [uv](https://docs.astral.sh/uv/) 管理 Python 套件與虛擬環境
- 每一種演算法（雜訊、模糊、各種轉檔損壞模擬、PSNR/SSIM/MS-SSIM/VMAF 計算）都拆成獨立的
  Python 檔案，方便單獨測試、複用、替換

```bash
cd psnr_toolkit
uv sync                       # 安裝相依套件（自動建立 .venv）
uv run python scripts/run_pipeline.py --golden output/golden.png --outdir output
```

詳細的檔案結構、每個演算法對應的檔案、完整使用範例，請看
**[`psnr_toolkit/README.md`](psnr_toolkit/README.md)**。

完整測試數據（testsrc 合成圖 + Big Buck Bunny 影格兩組 golden，noise/blur 完整 16 點掃描 +
6 種轉檔損壞樣本）請看 **[`psnr_toolkit/REPORT.md`](psnr_toolkit/REPORT.md)**。

## 測試結果摘要

> 完整數據見 [`psnr_toolkit/REPORT.md`](psnr_toolkit/REPORT.md)，這裡只列核心結論。

### 1. 同樣 PSNR，雜訊 vs 模糊，VMAF 差非常多

以兩組 golden（testsrc 合成圖、Big Buck Bunny 影格）在 PSNR ≈ 20dB 時比較：

| 失真類型 | PSNR | VMAF |
|---|---|---|
| Gaussian noise | ~20 dB | 65 ~ 69 |
| Gaussian blur | ~20 dB | **0.00**（已觸底） |

雜訊在 20dB 仍有一定可看性，模糊在同樣 PSNR 下已經被 VMAF 判定為完全不合格。
**PSNR 對「模糊」這種結構性失真過於寬容**，無法反映真實的視覺傷害程度。

### 2. VMAF ≥ 80（「適合觀看」）的可接受下限

| 資料集 | Noise 下限 | Blur 下限 |
|---|---|---|
| testsrc（合成圖） | PSNR ≈ 24.0 dB | 30dB 內從未達標 |
| Big Buck Bunny（真實影格） | PSNR ≈ 24.0 dB | 30dB 內從未達標 |

模糊即使在最高的 PSNR=30dB，VMAF 也只有 39~56 分，從未進入「適合觀看」的等級。

### 3. 模擬真實轉檔損壞（不是合成圖案，而是直接破壞 golden）

在 golden 上模擬常見的轉檔/串流損壞，按 PSNR 由低到高排序（節錄 testsrc 結果）：

| 損壞類型 | 模擬情境 | PSNR | VMAF |
|---|---|---|---|
| chroma_swap | 色彩矩陣/色版順序寫錯（偏色） | 7.61 dB | **93.90** |
| chroma_loss | 色度資料遺失（畫面灰階化） | 9.64 dB | **97.34** |
| row_tearing | 畫面撕裂/讀寫不同步 | 10.89 dB | 0.00 |
| block_glitch | macroblock 解碼錯誤 | 15.47 dB | 57.72 |
| packet_loss | 串流封包遺失（色帶佔位） | 18.24 dB | 92.67 |
| heavy_compression | 極低位元率轉碼 | 23.57 dB | 63.38 |

⚠️ **重要發現**：`chroma_loss` / `chroma_swap`（純色彩損壞）PSNR 很低（7~17dB，
看起來像嚴重損壞），但 VMAF 卻高達 92~97 分！原因是 VMAF 的核心模型主要評估
**亮度（luma）通道**，對純色彩偏移不敏感——但人眼會立刻注意到「整張變灰階」
或「明顯偏色」。這說明**任何單一指標都可能在特定失真類型上失準**：
PSNR 對模糊過於寬容、VMAF 對色彩損壞過於寬容。實務上建議至少交叉比對
PSNR + SSIM/MS-SSIM + VMAF，並輔以人工抽樣檢視色彩正確性。

### 4. 極端錨點（黑/白）作為量表下界參考

| 比較 | PSNR | VMAF |
|---|---|---|
| golden vs 全黑 | ~3~8 dB（依資料集） | ~0~3 |
| golden vs 全白 | ~3 dB | ~0~3 |

用來確認整個量表在最壞情況下的下界是合理的（遠低於 15~30dB 的失真掃描範圍）。

### 5. ffmpeg vs OpenCV 交叉驗證

為了確認整份報告倚賴的 OpenCV 實作準不準，額外用系統 `ffmpeg` CLI（`-lavfi psnr` /
`-lavfi ssim`）重新算一次同一批樣本，兩邊互相對照：

| 指標 | 與 ffmpeg 的差異 | 結論 |
|---|---|---|
| PSNR | 0.000 dB（完全一致） | 同一種 MSE 公式，可信 |
| SSIM | 0.01~0.05 | 兩種合法但窗大小不同的 SSIM 變體，屬正常誤差 |
| MS-SSIM | 最大到 0.3~0.4（少數樣本） | 與 libvmaf 的 MS-SSIM 實作差異較大，僅適合看「趨勢」 |
| VMAF | 無法用 ffmpeg 驗證 | 本機 ffmpeg 未編譯 `libvmaf`，VMAF 仍只有單一（libvmaf CLI）來源 |

詳見 **[`psnr_toolkit/README.md` 的「ffmpeg vs OpenCV 交叉驗證」章節](psnr_toolkit/README.md#ffmpeg-vs-opencv-交叉驗證)**。

## Repo 結構

```
.
├── README.md                   # 本文件
├── psnr_toolkit/                # ✅ 唯一使用中的工具（OpenCV + uv，無 ffmpeg）
│   ├── README.md                # 詳細使用說明、每個演算法對應的檔案
│   ├── REPORT.md                # 完整測試數據報告（本文摘要的完整版）
│   ├── scripts/                  # 每個演算法一個檔案
│   ├── output/                   # testsrc 合成 golden 的產出（含 ffmpeg_vs_opencv.csv/.md）
│   └── output_bbb/                # Big Buck Bunny golden 的產出（同上）
│
└── VIEWING_RECOMMENDATION.md    # 依 VMAF 分級「適合人眼觀看」的建議門檻
```

## 快速開始

```bash
cd psnr_toolkit
uv sync

# 產生兩種 golden sample
uv run python scripts/generate_synthetic_golden.py output/golden.png
uv run python scripts/generate_golden_from_video.py /path/to/video.mp4 output_bbb/golden.png --seconds 5

# 跑完整實驗（noise + blur 掃描 + 黑白錨點 + metrics.csv）
uv run python scripts/run_pipeline.py --golden output/golden.png --outdir output --with-vmaf

# 產生模擬真實轉檔損壞的樣本，並與 golden 比較
uv run python scripts/generate_transcode_corruptions.py output/golden.png output/broken
uv run python scripts/compare_broken_samples.py output/golden.png output/broken --with-vmaf

# 彙整成一份完整報告
uv run python scripts/build_report.py
```

> VMAF 為選用功能，需另外自行編譯 [libvmaf](https://github.com/Netflix/vmaf)
> （非 uv/pip 套件），詳見 `psnr_toolkit/README.md`。
