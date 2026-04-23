# 工作日誌

## 2026-04-23

### Edge STT 評測流程落地

今天把原本只有研究計畫與評測規格的內容，往「可以真的跑」的方向推進，完成以下工作：

1. 建立 Whisper 測試環境
   - 新增 Dockerfile：`docker/whisper-cpu.Dockerfile`
   - 新增 Python 依賴：`requirements-whisper.txt`
   - 採用 `faster-whisper==1.1.1`，避免 CPU Docker 測試環境被完整 PyTorch/CUDA 依賴拖得過重
   - Docker image 已成功 build：`local-stt-whisper:cpu`

2. 建立真實 Whisper 推論腳本
   - 新增 `scripts/run_whisper_inference.py`
   - 功能：
     - 讀取 JSONL manifest
     - 載入 Whisper-family 模型
     - 對每筆音檔做 ASR 推論
     - 輸出 `predictions.jsonl`
   - 目前驗證模型：`whisper-tiny`
   - 目前驗證 runtime：`faster-whisper`
   - 目前驗證 device / compute：CPU / int8

3. 建立合成音檔流程
   - 新增 `scripts/synthesize_test_audio.sh`
   - 使用 macOS `say` 合成三個測試語音：
     - English：`Turn on the bedroom light.`
     - 中文：`打開客廳冷氣。`
     - 日本語：`音量を下げて。`
   - 使用 `ffmpeg` 轉成 16 kHz mono WAV
   - 產出位置：
     - `eval/audio/synthetic/en/turn_on_bedroom_light.wav`
     - `eval/audio/synthetic/zh/turn_on_living_room_ac.wav`
     - `eval/audio/synthetic/ja/volume_down.wav`

4. 建立 synthetic Whisper manifest
   - 新增 `eval/manifests/synthetic_whisper_eval_manifest.jsonl`
   - 包含 EN / ZH / JA 三筆 ASR 測試樣本
   - 可直接餵給 `scripts/run_whisper_inference.py`

5. 產生真實模型輸出與報告
   - 本機 venv 跑過一次 Whisper 推論：
     - predictions：`eval/preds/whisper_tiny_synthetic/predictions.jsonl`
     - metrics：`eval/metrics/whisper_tiny_synthetic/`
   - Docker container 跑過一次 Whisper 推論：
     - predictions：`eval/preds/whisper_tiny_synthetic_docker/predictions.jsonl`
     - metrics：`eval/metrics/whisper_tiny_synthetic_docker/`

6. 更新聚合評測腳本
   - 更新 `scripts/eval_aggregate.py`
   - 加入基本標點 normalization，避免 `Turn on the bedroom light.` 因句點或大小寫被算成錯誤
   - 重新驗證既有 unittest 沒有被破壞

7. 補充 Docker 使用文件
   - 新增 `docs/whisper_docker_quickstart.md`
   - 記錄：
     - Docker build 指令
     - 合成音檔指令
     - Docker 推論指令
     - metrics aggregation 指令
     - 已驗證 smoke test 結果

### 驗證結果

已執行並通過：

```bash
python3 -m unittest discover -s tests -v
```

結果：

```text
test_aggregate_outputs (test_eval_aggregate.EvalAggregateTest) ... ok

----------------------------------------------------------------------
Ran 1 test in ...

OK
```

Docker Whisper smoke test 已完成：

```bash
docker run --rm \
  -v /Users/jftsai/src/local-stt-llm:/app \
  local-stt-whisper:cpu \
  python3 scripts/run_whisper_inference.py \
    --manifest eval/manifests/synthetic_whisper_eval_manifest.jsonl \
    --output eval/preds/whisper_tiny_synthetic_docker/predictions.jsonl \
    --model tiny \
    --device cpu \
    --compute-type int8
```

聚合後報告：

```bash
python3 scripts/eval_aggregate.py \
  --asr-manifest eval/manifests/synthetic_whisper_eval_manifest.jsonl \
  --command-manifest eval/manifests/command_eval_manifest.jsonl \
  --command-catalog eval/refs/command_catalog.csv \
  --predictions eval/preds/whisper_tiny_synthetic_docker/predictions.jsonl \
  --output-dir eval/metrics/whisper_tiny_synthetic_docker \
  --run-id whisper_tiny_synthetic_docker
```

目前 Docker report 摘要：

| Metric | Value |
|---|---:|
| Utterances | 3 |
| WER Macro | 0.0 |
| CER Macro | 0.0 |
| Avg Norm Error | 0.0 |
| Exact Match Rate | 1.0 |
| RTF P50 | 0.004332 |
| E2E Latency P50 (ms) | 10.178 |

### 注意事項

- Whisper 模型權重沒有放進 repo；第一次執行會從 Hugging Face 下載。
- 目前音檔是 TTS 合成資料，只適合 smoke test，不代表真實語音/噪聲/手機收音條件。
- 目前 `peak_ram_mb` 與 `avg_power_w` 尚未接實際量測工具，所以 report 中仍是 `null`。
- Docker image 已驗證可跑，但還沒有 commit 這次新增檔案。
