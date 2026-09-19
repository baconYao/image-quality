# psnr-toolkit

一個**不使用 ffmpeg**、每個演算法拆成獨立 Python 檔案、用 [uv](https://docs.astral.sh/uv/) 管理套件與執行環境的 PSNR / SSIM / MS-SSIM 視覺失真比較工具。

## 相依套件（uv 管理）

`pyproject.toml` 內宣告：

| 套件 | 用途 |
|---|---|
| `opencv-contrib-python` | 圖片讀寫、影片幀擷取（`cv2.VideoCapture`）、高斯模糊（`cv2.GaussianBlur`）、PSNR（`cv2.PSNR`）、SSIM（`cv2.quality.QualitySSIM_compute`）— **取代所有原本用 ffmpeg 做的事** |
| `numpy` | 高斯雜訊產生、二分搜尋、陣列運算 |

安裝環境（自動建立 `.venv` 並鎖定版本）：

```bash
cd psnr_toolkit
uv sync
```

執行任何腳本一律用 `uv run`（不需手動啟動虛擬環境）：

```bash
uv run python scripts/generate_synthetic_golden.py output/golden.png
```

> **VMAF 是選用/額外的**：VMAF（`scripts/metrics_vmaf.py`）依賴 Netflix 的 `libvmaf`，
> 這是一個 C 函式庫，**沒有官方 PyPI/uv 套件**，因此不在 `uv sync` 管理範圍內。
> 若要使用，需自行以 `meson`/`ninja` 從 [Netflix/vmaf](https://github.com/Netflix/vmaf)
> 原始碼編譯出 `vmaf` 執行檔（本機已編譯安裝在 `~/.local/bin/vmaf`）。
> 該腳本本身轉換 YUV 仍是用 OpenCV（`cv2.cvtColor(..., COLOR_BGR2YUV_I420)`），
> 同樣沒有呼叫 ffmpeg。

> **跨工具驗證用的 ffmpeg 是額外/選用的系統依賴**：`scripts/metrics_ffmpeg.py` +
> `scripts/compare_ffmpeg_vs_opencv.py` 這兩支腳本會呼叫系統上的 `ffmpeg` 執行檔
> （例如 `apt install ffmpeg`），純粹用來**驗證** OpenCV 算出來的 PSNR/SSIM 準不準，
> 完全獨立於主要 pipeline（`run_pipeline.py` 等其餘腳本仍然 100% 不碰 ffmpeg）。

## 檔案結構（每個演算法一個檔案）

```
scripts/
  common.py                      # 共用的圖片讀寫工具（cv2 imread/imwrite）
  generate_synthetic_golden.py   # 演算法：合成 1920x1080 golden sample（色塊+漸層+圖形，取代 ffmpeg testsrc2）
  generate_golden_from_video.py  # 演算法：用 cv2.VideoCapture 從影片擷取一幀golden sample
  generate_solid_color.py        # 演算法：產生全黑/全白（或任意純色）圖片
  degrade_gaussian_noise.py      # 演算法：高斯雜訊失真 + 二分搜尋校準到目標 PSNR
  degrade_gaussian_blur.py       # 演算法：高斯模糊失真 + 二分搜尋校準到目標 PSNR（含大sigma效能優化）
  metrics_psnr.py                # 演算法：PSNR（cv2.PSNR）
  metrics_ssim.py                # 演算法：SSIM + MS-SSIM（cv2.quality + 多尺度金字塔）
  metrics_vmaf.py                # 選用：VMAF（需另外編譯 libvmaf，非 uv 套件）
  corrupt_block_glitch.py        # 演算法：模擬 macroblock 解碼錯誤（色塊/位移區塊）
  corrupt_packet_loss.py         # 演算法：模擬封包遺失（整條色帶被灰色佔位取代）
  corrupt_row_tearing.py         # 演算法：模擬 tearing/desync（橫向條帶錯位）
  corrupt_heavy_compression.py   # 演算法：模擬極低位元率轉檔（JPEG 低品質重編碼）
  corrupt_color_channel.py       # 演算法：模擬色彩空間/色度損壞（chroma_loss / chroma_swap）
  generate_transcode_corruptions.py  # 整合腳本：對 golden 套用以上全部轉檔損壞演算法
  compare_broken_samples.py      # 整合腳本：把任一資料夾內的圖與 golden 逐張比較（不做 PSNR 校準）
  run_pipeline.py                # 整合腳本：呼叫以上各演算法跑完整 30.0→15.0dB 掃描
  build_report.py                # 整合腳本：彙整 testsrc + BBB 兩組資料集的 noise/blur/broken 結果成單一 REPORT.md
  metrics_ffmpeg.py               # 驗證用：用系統 ffmpeg 的 psnr/ssim filter 重新計算 PSNR/SSIM（不用於主 pipeline）
  compare_ffmpeg_vs_opencv.py     # 整合腳本：對照 OpenCV vs ffmpeg（PSNR/SSIM）與 libvmaf（MS-SSIM/VMAF），輸出差異報表
```

## 各演算法怎麼被拆開

- **golden sample 產生**：`generate_synthetic_golden.py`（純合成圖案）與
  `generate_golden_from_video.py`（從本地影片檔用 `cv2.VideoCapture` 擷取幀，
  取代 `ffmpeg -ss ... -frames:v 1`）二選一。
- **全黑/全白**：`generate_solid_color.py`，純 numpy 填色，不需要任何解碼器。
- **失真演算法**：
  - `degrade_gaussian_noise.py`：對每個目標 PSNR，用二分搜尋加成性高斯雜訊的
    標準差（sigma），直到 `metrics_psnr.py` 量測出的 PSNR 落在 ±0.05dB 內。
  - `degrade_gaussian_blur.py`：同樣二分搜尋 `cv2.GaussianBlur` 的 sigma；
    當 sigma 很大時（低 PSNR 目標）改用「縮小→小核模糊→放大」的技巧避免
    龐大核心導致計算爆量，效能與精度兼顧。
- **指標**：`metrics_psnr.py`（PSNR）、`metrics_ssim.py`（SSIM/MS-SSIM），
  兩者都只依賴 opencv-contrib 的 `cv2.PSNR` / `cv2.quality.QualitySSIM_compute`，
  MS-SSIM 是在此基礎上手刻的多尺度（`cv2.pyrDown`）加權幾何平均。
- **Broken image（模擬真實轉檔損壞）**：以下每個演算法都是**直接基於 golden sample**
  做破壞（不是憑空合成的圖案），模擬轉檔/串流過程中實際會發生的損壞類型：
  - `corrupt_block_glitch.py`：隨機挑選 macroblock 大小的區塊，替換成
    「灰/綠色錯誤區塊」或「從畫面其他位置複製過來的區塊」——模擬解碼器遇到
    無法解碼的區塊時的常見 fallback 行為。
  - `corrupt_packet_loss.py`：整條橫向色帶被灰色佔位色取代——模擬串流封包
    遺失、該區域畫面尚未收到資料時的常見畫面。
  - `corrupt_row_tearing.py`：把畫面切成多條橫帶，每條隨機水平位移——模擬
    畫面撕裂（tearing）/ 讀寫不同步的常見瑕疵。
  - `corrupt_heavy_compression.py`：用 `cv2.imencode` 以極低 JPEG 品質
    重新編碼再解碼——模擬轉檔位元率嚴重不足時的區塊化/色彩糊開瑕疵
    （JPEG 與 H.264/H.265 intra frame 同樣是 DCT 區塊量化，瑕疵型態相近）。
  - `corrupt_color_channel.py`：轉成 YCrCb 後破壞色度平面——
    `chroma_loss`（Cr/Cb 歸零，模擬色度資料遺失/未解碼，畫面變灰階但亮度正常）、
    `chroma_swap`（Cr/Cb 對調，模擬色彩矩陣/色版順序寫錯的轉檔 bug，導致偏色）。

  `generate_transcode_corruptions.py` 會一次套用以上所有演算法並輸出到指定資料夾，
  再用 `compare_broken_samples.py` 與 golden 逐張比較 PSNR/SSIM/MS-SSIM/VMAF。

## 使用範例

```bash
cd psnr_toolkit

# 1. 產生兩種 golden sample
uv run python scripts/generate_synthetic_golden.py output/golden.png
uv run python scripts/generate_golden_from_video.py /path/to/bigbuckbunny.mp4 output_bbb/golden.png --seconds 5

# 2. 一次跑完整條 pipeline（golden + black/white + noise/blur 31張 x2 + metrics.csv）
uv run python scripts/run_pipeline.py --golden output/golden.png --outdir output
uv run python scripts/run_pipeline.py --golden output_bbb/golden.png --outdir output_bbb

# 3. 或單獨執行某個演算法
uv run python scripts/degrade_gaussian_noise.py output/golden.png output/noise --targets 25,20,15
uv run python scripts/degrade_gaussian_blur.py output/golden.png output/blur

# 4. 單獨驗證兩張圖的指標
uv run python scripts/metrics_psnr.py output/golden.png output/noise/psnr_20.0.png
uv run python scripts/metrics_ssim.py output/golden.png output/blur/psnr_20.0.png

# 5.（選用，需先自行編譯 libvmaf）
uv run python scripts/metrics_vmaf.py output/golden.png output/blur/psnr_20.0.png

# 6. 基於 golden 產生「模擬真實轉檔損壞」的樣本，並與 golden 比較
uv run python scripts/generate_transcode_corruptions.py output/golden.png output/broken
uv run python scripts/compare_broken_samples.py output/golden.png output/broken --with-vmaf

# 6b. 也可以單獨執行某一種損壞演算法、自訂參數
uv run python scripts/corrupt_block_glitch.py output/golden.png output/broken/block_glitch.png --corruption-ratio 0.3
uv run python scripts/corrupt_heavy_compression.py output/golden.png output/broken/heavy_compression.png --quality 1

# 7. 彙整 testsrc + BBB 兩組資料集的 noise/blur/broken 完整結果成一份 REPORT.md
uv run python scripts/build_report.py

# 8.（需系統安裝 ffmpeg）驗證 OpenCV 算出來的 PSNR/SSIM 跟 ffmpeg CLI 算出來的差多少
uv run python scripts/metrics_ffmpeg.py output/golden.png output/noise/psnr_20.0.png
uv run python scripts/compare_ffmpeg_vs_opencv.py --outdir output
uv run python scripts/compare_ffmpeg_vs_opencv.py --outdir output_bbb
```

## 輸出

`run_pipeline.py` 會在指定的 `--outdir` 產生：

```
<outdir>/golden.png
<outdir>/black.png
<outdir>/white.png
<outdir>/noise/psnr_30.0.png ... psnr_15.0.png   (預設 16 張，1.0dB 一階；可用 --step 0.5 產生 31 張)
<outdir>/blur/psnr_30.0.png  ... psnr_15.0.png   (同上)
<outdir>/metrics.csv          # type, target_psnr, param, psnr, ssim, ms_ssim, (vmaf)
```

`generate_transcode_corruptions.py` + `compare_broken_samples.py` 另外會在（例如）
`output/broken/` 產生：

```
output/broken/block_glitch.png
output/broken/packet_loss.png
output/broken/row_tearing.png
output/broken/heavy_compression.png
output/broken/chroma_loss.png
output/broken/chroma_swap.png
output/broken/broken_metrics.csv   # pattern, psnr, ssim, ms_ssim, (vmaf)
output/broken/broken_report.md
```

實測結果（golden 分別為 testsrc 合成圖 / Big Buck Bunny 影格）：

| 損壞類型 | testsrc PSNR | testsrc VMAF | BBB PSNR | BBB VMAF |
|---|---|---|---|---|
| block_glitch（macroblock 解碼錯誤） | 15.47 dB | 57.72 | 19.85 dB | 61.33 |
| packet_loss（封包遺失色帶） | 18.24 dB | 92.67 | 19.04 dB | 57.94 |
| row_tearing（畫面撕裂） | 10.89 dB | 0.00 | 16.82 dB | 4.97 |
| heavy_compression（極低位元率轉碼） | 23.57 dB | 63.38 | 22.53 dB | 30.38 |
| chroma_loss（色度遺失/灰階化） | 9.64 dB | **97.34** | 17.06 dB | **97.13** |
| chroma_swap（色彩矩陣寫錯偏色） | 7.61 dB | **93.90** | 14.08 dB | **92.55** |

⚠️ **值得注意的發現**：`chroma_loss` / `chroma_swap` 的 **PSNR 非常低（7~17dB）**，
一般認知這是「嚴重損壞」，但 **VMAF 卻高達 92~97**！這是因為 VMAF 的核心模型
主要以**亮度（luma）通道**評估品質，對純色彩偏移/失真並不敏感——但人眼其實
會立刻注意到「整張照片變灰階」或「整體偏色」這類問題。這與先前雜訊 vs 模糊
的發現互相呼應：**任何單一指標都可能在特定失真類型上失準**，PSNR 對結構性
損壞（模糊）過於寬容，VMAF 則對純色彩損壞過於寬容，實務上建議至少交叉比對
PSNR + SSIM + VMAF 三者，並輔以人工抽樣檢視。

全程沒有呼叫任何 `ffmpeg` 指令（`metrics_ffmpeg.py` / `compare_ffmpeg_vs_opencv.py` 除外，
這兩支腳本的存在目的正是拿 ffmpeg 當「獨立第二種實作」來驗證 OpenCV 算出來的數字）。

## ffmpeg vs OpenCV 交叉驗證

`compare_ffmpeg_vs_opencv.py` 針對每個資料集挑選 16 個代表性樣本（noise/blur 各
30/25/20/15dB、黑/白錨點、6 種轉檔損壞），同時用 OpenCV 與 ffmpeg CLI（`-lavfi psnr`
/ `-lavfi ssim`）各算一次 PSNR / SSIM，並拿 libvmaf 的 `float_ms_ssim` 當 MS-SSIM
的對照組，輸出 `<outdir>/ffmpeg_vs_opencv.csv` + `.md`。

| Dataset | 樣本數 | PSNR 差異>0.5dB | SSIM 差異>0.05 | MS-SSIM 差異>0.05 | 最大 ΔPSNR | 最大 ΔSSIM |
|---|---|---|---|---|---|---|
| testsrc | 16 | 0/16 | 0/16 | 11/16 | 0.000 dB | 0.0481 |
| Big Buck Bunny | 16 | 0/16 | 3/16 | 7/16 | 0.000 dB | 0.0862 |

**結論**：
- **PSNR** 在所有樣本上與 ffmpeg 算出來的值**完全一致**（誤差 0.000dB）——兩邊用的都是
  同一種 MSE 公式，這是預期中最強的驗證結果。
- **SSIM** 誤差普遍落在 0.01~0.05 之間，屬於正常範圍：OpenCV 的 `quality.QualitySSIM`
  用標準 Wang et al. (2003) 11x11 高斯窗，ffmpeg 的 `ssim` filter 預設用 8x8 均勻窗，
  兩者都是「合法」但實作細節不同的 SSIM 變體。
- **MS-SSIM** 差異明顯較大（尤其在黑/白錨點與純色度損壞樣本上可到 0.3~0.4），代表本專案
  以 `cv2.pyrDown` 金字塔堆疊算出來的 MS-SSIM，跟 libvmaf 的 `float_ms_ssim` **不能直接
  互相比較絕對數值**，但兩者呈現的「趨勢」（品質好壞排序）仍然一致，仍可用來看相對變化。
- **VMAF** 沒有第二套獨立實作可比較（本專案的 VMAF 本來就是呼叫同一個 libvmaf 執行檔）。

> 這支腳本需要系統上有 `ffmpeg` 執行檔（`sudo apt install ffmpeg` 或等效方式），
> 是唯一會呼叫 ffmpeg 的地方，且僅用於驗證，不影響其餘 pipeline 的輸出。

