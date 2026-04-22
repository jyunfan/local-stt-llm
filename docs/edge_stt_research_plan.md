# Open Source 小模型（<=3B）Speech-to-Text 研究計劃（Edge Device 控制場景）

> 版本日期：2026-04-22

## 1. 研究目標

### 主目標
比較開源、參數量 <=3B 的語音轉文字模型，在 Edge Device 條件下的實際表現，並評估是否適合「語音控制」場景。

### 次目標
1. 分析「準確率、延遲、資源耗用」三者間的 trade-off。
2. 評估模型在多語言、口音、噪聲條件下的穩健性。
3. 建立可部署門檻：判斷哪些模型可達到控制場景可用標準（特別是錯誤命令率）。

---

## 2. 研究範圍與模型池（第一階段）

> 註：在工程上，STT 任務通常由 ASR / Speech Foundation Model 負責，不一定是純文字 LLM。

第一階段建議先選 4~6 個代表模型：

1. **OpenAI Whisper tiny/base/small**（經典基線）
2. **Distil-Whisper distil-small.en**（166M，壓縮版，適合資源受限）
3. **NVIDIA Parakeet-TDT-0.6B-v3**（600M，多語）
4. **Qwen3-ASR-0.6B**（600M，多語/方言）
5. **SeamlessM4T v2 large**（2.3B，3B 內上限參考組）

第二階段可加入超輕量模型（例如 ultra-edge 導向模型）做補充對照。

---

## 3. 實驗設計

## A. 任務層次
至少分三類任務，避免只看 WER：

1. **自由語音轉寫**（General ASR）
2. **控制語音辨識**（Command-and-Control）
3. **壓力測試**（噪聲、遠場、重口音）

## B. 評估指標

### 轉寫品質
- WER（Word Error Rate）
- CER（Character Error Rate）

### 控制可用性（重點）
- CSR（Command Success Rate）
- Wrong Command Rate（錯誤命令率）
- False Activation Rate（誤觸發率）

### 系統效能
- RTF（Real-time Factor）
- 端到端延遲（P50/P95）
- 模型載入時間
- 峰值 RAM / VRAM
- 平均功耗（W）

## C. 資料策略

### 公開資料（泛化能力）
- Common Voice
- FLEURS
- LibriSpeech（依語言需求）

### 場景資料（核心）
建立控制語料（20~50 條命令模板），涵蓋：
- 多說話人
- 多口音
- 不同 SNR（安靜、家電背景、TV/音樂背景）
- 不同距離（近場/遠場）

建議資料量：
- 初步比較：10~20 小時
- 穩定結論：30 小時以上

## D. 硬體矩陣（Edge 導向）
至少包含兩種：
1. 低功耗 CPU / SBC 裝置
2. 行動裝置或小型邊緣運算盒（x86/ARM）

可加一台桌機 GPU 作為「能力上限」參考。

## E. 公平比較設定
- 統一採樣率與前處理
- 統一 VAD 策略
- 統一 batch（edge 建議 batch=1）
- 比較 FP16 / INT8 / INT4
- 分 streaming 與 offline 兩組

---

## 4. 報告輸出架構

1. 問題定義：為何 edge 控制不能只看一般 ASR 指標
2. 模型分類：ASR 架構與 speech-language model 差異
3. Benchmark protocol：資料、硬體、指標與統計方法
4. 主結果：準確率-延遲-功耗的 Pareto 分析
5. 風險分析：錯誤命令案例與安全分級
6. 部署建議：依場景提供選型建議（ultra-edge / multilingual / 商用授權）

---

## 5. 時程建議（8 週）

- **W1**：確定模型清單、語料規格、評估協議
- **W2**：建立統一推論與記錄 pipeline
- **W3-W4**：公開資料基準測試
- **W5**：控制語料與噪聲壓測
- **W6**：量化與 streaming ablation
- **W7**：誤差與風險分析
- **W8**：整合圖表與結論

---

## 6. 決策前需先確認的三件事

1. **語言範圍**：中文、雙語（中英）或多語
2. **目標硬體**：最終部署裝置類型
3. **授權限制**：是否必須可商用（會影響模型篩選）

---

## 7. 初步結論

在「edge 控制」情境下，建議採用「**兩層評估**」：
1. 先用 WER/CER 篩除明顯不適合模型；
2. 再以 CSR、錯誤命令率、延遲與功耗做最終選型。

最終研究輸出不只要回答「誰最準」，而是回答「**誰最適合在指定硬體上可靠地控制設備**」。

---

## 8. 與既有研究「相同/可直接沿用」的部分

以下整理目前可對齊的既有研究方向，對應你現在要做的 edge STT 小模型評估：

### A. 小模型蒸餾與資源受限推論（與本研究高度重疊）
- **Distil-Whisper（2023）**：核心問題就是大型 ASR 在低延遲與資源受限場景部署困難，透過知識蒸餾降低模型成本。
- **可沿用**：以「準確率 vs 延遲/記憶體」做比較的思路，適合放進本計畫的第一層篩選。

### B. Edge 裝置語音辨識（與本研究場景高度重疊）
- **EdgeSpeechNets（2018）**：直接針對 edge 語音辨識，並以模型大小、運算量、手機延遲做比較。
- **TinySpeech（2020）**：同樣聚焦小型化、低計算成本的 on-device speech recognition。
- **可沿用**：
  1. 把「模型 footprint、MACs、實機延遲」列為主指標。
  2. 強調「在實際裝置上的效率」而非只看離線準確率。

### C. 指令/喚醒類語音任務（與你的控制目標直接重疊）
- Keyword spotting / command recognition 研究長期使用 Google Speech Commands 等資料集，重點在低延遲、低誤觸發。
- **可沿用**：把 **Wrong Command Rate、False Activation Rate** 設為主要 KPI，並加入噪聲與遠場壓力測試。

### D. 開源實作趨勢（與部署方式重疊）
- **Moonshine** 與 **Whisper 生態（如 whisper.cpp / ONNX）** 都強調 on-device 與低延遲部署。
- **可沿用**：
  1. 同一模型做多後端（PyTorch/ONNX/ggml）比較。
  2. 將量化（INT8/INT4）和 streaming 模式列為獨立實驗維度。

## 9. 可直接採用的「先前研究方法」對照表

| 你現在要做的項目 | 先前研究已有做法 | 你可直接採用的做法 |
|---|---|---|
| 小模型是否可用於 edge | Distil-Whisper、EdgeSpeechNets、TinySpeech 都強調壓縮與實機效率 | 先用 WER/CER 篩選，再用延遲、記憶體、功耗做二次篩選 |
| 是否適合控制場景 | Keyword spotting/command 任務重視誤觸發與誤判 | 把 CSR、Wrong Command Rate、False Activation 當主指標 |
| 多硬體可部署性 | Edge 研究普遍做實機 latency/memory 驗證 | 至少兩種 edge 裝置 + 一個桌機上限組 |
| 公平比較 | 既有研究會固定輸入條件與模型設定 | 統一採樣率/VAD/batch，分 offline 與 streaming |

## 10. 補充結論（針對你的問題）

你現在要做的研究，和既有文獻最重疊的核心有三點：
1. **小模型壓縮後的可用性**（Distillation / Tiny model）
2. **Edge 實機效率驗證**（latency、memory、compute）
3. **控制任務安全性**（誤觸發與錯誤命令）

因此最穩健的做法是：
- 以 Distil-Whisper / Whisper 小模型作 baseline，
- 補上一個 edge 友善模型（如 Moonshine），
- 最後用「控制任務 KPI」決定是否可部署，而不是只用 WER 排名。

## 11. 參考研究與資源（供後續延伸）

- Distil-Whisper 論文（arXiv, 2023）：https://arxiv.org/abs/2311.00430
- Multilingual DistilWhisper（arXiv, 2023）：https://arxiv.org/abs/2311.01070
- EdgeSpeechNets（arXiv, 2018）：https://arxiv.org/abs/1810.08559
- TinySpeech（arXiv, 2020）：https://arxiv.org/abs/2008.04245
- Google Speech Commands Dataset（TF）：https://www.tensorflow.org/datasets/catalog/speech_commands
- Moonshine（GitHub）：https://github.com/usefulsensors/moonshine
- OpenAI Whisper（HF）：https://huggingface.co/openai/whisper-tiny
- Distil-Whisper 模型卡（HF）：https://huggingface.co/distil-whisper/distil-small.en
- NVIDIA Parakeet-TDT-0.6B-v3（HF）：https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
- Qwen3-ASR-0.6B（HF）：https://huggingface.co/Qwen/Qwen3-ASR-0.6B
- SeamlessM4T v2 large（HF）：https://huggingface.co/facebook/seamless-m4t-v2-large
