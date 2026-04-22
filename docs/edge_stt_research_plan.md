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
