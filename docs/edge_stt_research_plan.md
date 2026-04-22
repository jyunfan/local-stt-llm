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
>
> 本版固定前提：
> - 語言範圍：**英文 / 中文 / 日文**
> - 目標硬體：**手機（Android / iPhone）**
> - 授權限制：**必須可商用**

第一階段建議先選 5 個代表模型，優先保留符合「多語 + 手機部署 + 可商用」條件者：

1. **OpenAI Whisper tiny**（39M，多語，超輕量手機基線）
2. **OpenAI Whisper base**（74M，多語，手機可行主力基線）
3. **OpenAI Whisper small**（244M，多語，中階精度組）
4. **OpenAI Whisper large-v3-turbo**（約809M，高精度上限組）
5. **Qwen3-ASR-0.6B**（0.6B，多語，中文能力與新架構代表）

第二階段可加入「條件式候選」做補充對照，但不列入主結論：
- **Moonshine 非英文版本**：雖然 edge 友善，但非英文模型目前採 community license，不適合直接作為一般商用結論。
- **Parakeet-TDT-0.6B-v3**：可商用，但官方支援語言為歐洲語系，不符合本研究的中/日需求。
- **Distil-Whisper 系列**：目前官方主力 checkpoint 仍偏英語，不適合本版多語主題。

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

## D. 硬體矩陣（手機導向）
至少包含兩類手機：
1. **中高階 Android 手機**（優先觀察 NPU / DSP / GPU 可用性）
2. **近兩代 iPhone**（觀察 Core ML / Metal 路線）

可加一台桌機 GPU 作為「離線能力上限」參考，但最終結論以手機實測為準。

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

## 6. 已固定的決策條件

1. **語言範圍**：英文 / 中文 / 日文
2. **目標硬體**：手機
3. **授權限制**：必須可商用

---

## 7. 初步結論

在「手機上的 edge 控制」情境下，建議採用「**兩層評估**」：
1. 先用 WER/CER 篩除明顯不適合模型；
2. 再以 CSR、錯誤命令率、延遲與功耗做最終選型。

最終研究輸出不只要回答「誰最準」，而是回答「**誰最適合在手機上可靠地控制設備**」。

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

因此本版最穩健的做法是：
- 以 **Whisper tiny / base / small** 建立手機可跑的標準基線，
- 用 **Whisper large-v3-turbo** 當高精度上限，
- 用 **Qwen3-ASR-0.6B** 作為新一代多語 speech-LLM 對照，
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

---

## 12. 最終模型 Shortlist（5 個）

以下為本研究版的最終 shortlist；排序不是最終名次，而是建議實驗順序。

| 模型 | 參數量 | EN/ZH/JA | 商用可行性 | 手機部署定位 | 建議角色 |
|---|---:|---|---|---|---|
| **OpenAI Whisper tiny** | 39M | 支援 | 是（Apache-2.0） | 最容易上手機，適合 batch=1 / 即時測試 | 超輕量 baseline |
| **OpenAI Whisper base** | 74M | 支援 | 是（Apache-2.0） | 手機主力甜蜜點之一 | 主 baseline |
| **OpenAI Whisper small** | 244M | 支援 | 是（Apache-2.0） | 中高階手機可評估，可能需量化 | 精度提升組 |
| **OpenAI Whisper large-v3-turbo** | ~809M | 支援 | 是（MIT） | 高階手機或分段/量化部署 | 高精度上限組 |
| **Qwen3-ASR-0.6B** | 0.6B | 支援 | 是（Apache-2.0） | 新架構候選，重點看中文/日文與延遲 | 非 Whisper 對照組 |

### Shortlist 選型理由
- **Whisper tiny / base / small**：同一系列可形成清楚的大小-精度-延遲曲線，適合做手機 Pareto 分析。
- **Whisper large-v3-turbo**：作為高精度參考，能幫你判斷手機端量化與裁切後的精度損失是否值得。
- **Qwen3-ASR-0.6B**：在中文與多語辨識上值得納入，但是否適合手機控制場景，要特別看首 token 延遲與峰值記憶體。

### 不納入主 shortlist 的原因
- **Distil-Whisper**：官方主力 checkpoint 以英語為主，與本研究語言範圍不完全對齊。
- **Parakeet-TDT-0.6B-v3**：可商用，但官方重點語言不含中文/日文。
- **Moonshine 非英文 variants**：目前屬限制型 community license，商用條件不夠通用。

---

## 13. 實驗表格模板（可直接貼進報告）

### A. 模型與部署條件表

| Model | Params | License | Languages in Scope | Runtime | Precision | Streaming | Device |
|---|---:|---|---|---|---|---|---|
| Whisper tiny | 39M | Apache-2.0 | EN/ZH/JA | whisper.cpp / Core ML / ONNX | FP16 / INT8 | Yes/No | device_name |
| Whisper base | 74M | Apache-2.0 | EN/ZH/JA | whisper.cpp / Core ML / ONNX | FP16 / INT8 | Yes/No | device_name |
| Whisper small | 244M | Apache-2.0 | EN/ZH/JA | whisper.cpp / Core ML / ONNX | FP16 / INT8 / INT4 | Yes/No | device_name |
| Whisper large-v3-turbo | ~809M | MIT | EN/ZH/JA | Transformers / ONNX / Core ML | FP16 / INT8 | Yes/No | device_name |
| Qwen3-ASR-0.6B | 0.6B | Apache-2.0 | EN/ZH/JA | Transformers / vendor runtime | FP16 / INT8 | Yes/No | device_name |

### B. 主結果表（泛化轉寫）

| Model | Device | Precision | EN WER | ZH CER | JA CER | Avg Norm Error | RTF | P50 Latency (ms) | P95 Latency (ms) | Peak RAM (MB) | Avg Power (W) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Whisper tiny | phone_a | INT8 |  |  |  |  |  |  |  |  |  |
| Whisper base | phone_a | INT8 |  |  |  |  |  |  |  |  |  |
| Whisper small | phone_a | INT8 |  |  |  |  |  |  |  |  |  |
| Whisper large-v3-turbo | phone_b | INT8 |  |  |  |  |  |  |  |  |  |
| Qwen3-ASR-0.6B | phone_b | INT8 |  |  |  |  |  |  |  |  |  |

### C. 控制任務表（最重要）

| Model | Device | Scenario | CSR (%) | Wrong Command Rate (%) | False Activation Rate (%) | Intent F1 | Slot F1 | P50 E2E (ms) | P95 E2E (ms) | Pass/Fail |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Whisper tiny | phone_a | quiet_nearfield |  |  |  |  |  |  |  |  |
| Whisper tiny | phone_a | tv_noise_farfield |  |  |  |  |  |  |  |  |
| Whisper base | phone_a | quiet_nearfield |  |  |  |  |  |  |  |  |
| Whisper small | phone_a | appliance_noise |  |  |  |  |  |  |  |  |
| Qwen3-ASR-0.6B | phone_b | mixed_accent |  |  |  |  |  |  |  |  |

### D. 失敗案例表

| ID | Model | Language | Scenario | Reference | Prediction | Error Type | Safety Severity | Notes |
|---|---|---|---|---|---|---|---|---|
| ex001 | Whisper base | ZH | kitchen_noise | 打開客廳的燈 | 打開客廳冷氣 | wrong_command | high | 名詞混淆 |
| ex002 | Qwen3-ASR-0.6B | JA | farfield | 音量を下げて | 音量を上げて | polarity_flip | critical | 方向相反 |

---

## 14. 評測腳本規格（欄位 / 檔案格式 / 統計方式）

本節目標是讓所有模型共用同一份 manifest、同一份輸出 schema、同一套統計口徑。

### A. 建議目錄格式

```text
eval/
  manifests/
    asr_eval_manifest.jsonl
    command_eval_manifest.jsonl
  refs/
    command_catalog.csv
  preds/
    {run_id}/predictions.jsonl
  metrics/
    {run_id}/utterance_metrics.csv
    {run_id}/summary_metrics.json
```

### B. `asr_eval_manifest.jsonl`

每行一筆樣本，UTF-8 JSON Lines：

```json
{"utt_id":"cv_en_0001","audio_path":"data/en/cv_en_0001.wav","lang":"en","task":"asr","split":"test","domain":"read_speech","duration_sec":4.82,"text_ref":"turn on the bedroom light","speaker_id":"spk01","accent":"us","snr_db":35.2,"distance":"near","noise_tag":"quiet"}
{"utt_id":"fleurs_ja_0001","audio_path":"data/ja/fleurs_ja_0001.wav","lang":"ja","task":"asr","split":"test","domain":"general","duration_sec":7.11,"text_ref":"エアコンをつけてください","speaker_id":"spk19","accent":"jp","snr_db":18.4,"distance":"far","noise_tag":"tv"}
```

必要欄位：
- `utt_id`
- `audio_path`
- `lang`：`en` / `zh` / `ja`
- `task`：`asr` 或 `command`
- `split`：`dev` / `test`
- `text_ref`
- `duration_sec`

建議欄位：
- `speaker_id`
- `accent`
- `snr_db`
- `distance`
- `noise_tag`
- `device_position`
- `command_id`
- `intent_ref`
- `slots_ref`

### C. `command_catalog.csv`

用來定義控制語句的標準語意，供 CSR / wrong-command 統計：

```csv
command_id,intent,slots_schema,safety_level,example
cmd_light_on,light_on,"{\"room\":\"string\"}",medium,turn on the bedroom light
cmd_volume_down,volume_down,"{\"delta\":\"number\"}",high,音量を下げて
cmd_ac_on,ac_on,"{\"room\":\"string\"}",high,打開客廳冷氣
```

### D. `predictions.jsonl`

每個模型 run 輸出一份，格式固定：

```json
{"utt_id":"cv_en_0001","model_id":"whisper-base","device":"iphone_15","precision":"int8","runtime":"coreml","streaming":false,"decode_config":{"beam_size":1,"vad":true},"text_pred":"turn on the bedroom light","lang_pred":"en","tokens":4,"audio_sec":4.82,"load_ms":120.4,"first_token_ms":182.7,"decode_ms":301.3,"e2e_ms":484.0,"rtf":0.10,"peak_ram_mb":512.4,"avg_power_w":1.9,"command_pred":{"intent":"light_on","slots":{"room":"bedroom"}}}
```

必要欄位：
- `utt_id`
- `model_id`
- `device`
- `precision`
- `runtime`
- `streaming`
- `text_pred`
- `audio_sec`
- `e2e_ms`
- `rtf`
- `peak_ram_mb`

控制任務額外欄位：
- `command_pred.intent`
- `command_pred.slots`
- `lang_pred`
- `first_token_ms`

### E. `utterance_metrics.csv`

逐句統計，便於 debug 與 error slicing：

```csv
utt_id,model_id,lang,task,wer,cer,exact_match,csr_hit,wrong_command,false_activation,intent_f1,slot_f1,e2e_ms,rtf,peak_ram_mb
cv_en_0001,whisper-base,en,asr,0.00,0.00,1,1,0,0,1.00,1.00,484.0,0.10,512.4
fleurs_ja_0001,qwen3-asr-0.6b,ja,command,0.25,0.12,0,0,1,0,0.00,0.50,913.2,0.28,1820.3
```

### F. `summary_metrics.json`

建議至少輸出：

```json
{
  "run_id": "2026-04-22_whisper-base_iphone15_int8",
  "group_by": ["model_id", "device", "precision", "lang", "task", "noise_tag", "distance"],
  "n_utterances": 1200,
  "total_audio_sec": 5238.4,
  "metrics": {
    "wer_macro": 0.128,
    "wer_micro": 0.119,
    "cer_macro": 0.084,
    "csr": 0.941,
    "wrong_command_rate": 0.021,
    "false_activation_rate": 0.008,
    "intent_f1_macro": 0.952,
    "slot_f1_macro": 0.933,
    "rtf_p50": 0.18,
    "rtf_p95": 0.31,
    "e2e_ms_p50": 612.4,
    "e2e_ms_p95": 1098.3,
    "peak_ram_mb_p95": 944.1,
    "avg_power_w_mean": 2.6
  }
}
```

### G. 統計方式

1. **ASR 主指標**
   - 英文用 **WER**
   - 中文、日文以 **CER** 為主，必要時補字詞切分後 WER
   - 報告主表建議加入 `Avg Norm Error`，做跨語言彙總

2. **跨語言彙總方式**
   - 不建議直接把英文 WER 與中日 CER 混成單一平均
   - 建議先做語言內正規化，再取 macro average：
   - `Avg Norm Error = mean(EN_WER, ZH_CER, JA_CER)`

3. **控制任務指標**
   - `CSR = 正確 intent 且必要 slots 正確的樣本數 / 全部 command 樣本數`
   - `Wrong Command Rate = 產生錯誤 intent 或危險相反指令的樣本數 / 全部 command 樣本數`
   - `False Activation Rate = 非命令音訊卻觸發命令的樣本數 / 非命令樣本數`

4. **延遲與效能**
   - `P50 / P95` 皆以 utterance-level 分布計
   - `RTF = e2e_ms / (audio_sec * 1000)`
   - streaming 模式另外保留 `first_token_ms`

5. **顯著性與穩定性**
   - 每組至少重跑 3 次，回報 mean ± std
   - 主要對照可加 bootstrap 95% CI
   - 手機功耗至少觀測完整推論區間，不只取單點峰值

---

## 15. 測試與執行方式（目前 repo 可直接使用）

本 repo 已提供一支可直接執行的聚合腳本與一組 sample 測試資料：

- 聚合腳本：`scripts/eval_aggregate.py`
- 測試檔：`tests/test_eval_aggregate.py`
- sample predictions：`eval/preds/sample_run/predictions.jsonl`
- sample 輸出目錄：`eval/metrics/sample_run/`

### A. 產生 sample report

在 repo 根目錄執行：

```bash
python3 scripts/eval_aggregate.py \
  --asr-manifest eval/manifests/asr_eval_manifest.jsonl \
  --command-manifest eval/manifests/command_eval_manifest.jsonl \
  --command-catalog eval/refs/command_catalog.csv \
  --predictions eval/preds/sample_run/predictions.jsonl \
  --output-dir eval/metrics/sample_run \
  --run-id sample_run
```

預期輸出：
- `eval/metrics/sample_run/utterance_metrics.csv`
- `eval/metrics/sample_run/summary_metrics.json`

終端預期會看到類似訊息：

```text
Wrote 7 utterance rows to eval/metrics/sample_run/utterance_metrics.csv
Wrote summary report to eval/metrics/sample_run/summary_metrics.json
```

### B. 執行單元測試

在 repo 根目錄執行：

```bash
python3 -m unittest discover -s tests -v
```

預期結果：

```text
test_aggregate_outputs (test_eval_aggregate.EvalAggregateTest) ... ok

----------------------------------------------------------------------
Ran 1 test in ...

OK
```

### C. 測試覆蓋內容

目前測試至少驗證以下行為：
- 能正確讀取 `asr` 與 `command` 兩種 manifest
- 能將 `predictions.jsonl` 與 reference 以 `utt_id` 正確對齊
- 能輸出 `utterance_metrics.csv` 與 `summary_metrics.json`
- 能正確統計 `CSR`
- 能正確統計 `Wrong Command Rate`
- 能正確統計 `False Activation Rate`
- 能正確計算 `Avg Norm Error`

### D. 目前 sample report 的示範結果

以 `sample_run` 為例，目前輸出摘要可作為 smoke test 參考：

| Metric | Value |
|---|---:|
| Avg Norm Error | 0.177778 |
| CSR | 0.666667 |
| Wrong Command Rate | 0.333333 |
| False Activation Rate | 1.0 |
| E2E Latency P50 (ms) | 340.0 |
| Peak RAM P95 (MB) | 521.7 |

若後續更換 sample predictions，應同步更新此表與測試 assertion。
