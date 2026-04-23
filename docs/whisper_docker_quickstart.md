# Whisper Docker Quickstart

## 1. Build the image

```bash
docker build -f docker/whisper-cpu.Dockerfile -t local-stt-whisper:cpu .
```

## 2. Synthesize test audio on macOS host

```bash
bash scripts/synthesize_test_audio.sh
```

This creates WAV files under `eval/audio/synthetic/`.

## 3. Run Whisper inside Docker

```bash
docker run --rm \
  -v "$PWD":/app \
  local-stt-whisper:cpu \
  python3 scripts/run_whisper_inference.py \
    --manifest eval/manifests/synthetic_whisper_eval_manifest.jsonl \
    --output eval/preds/whisper_tiny_synthetic/predictions.jsonl \
    --model tiny \
    --device cpu \
    --compute-type int8
```

## 4. Aggregate the report

```bash
python3 scripts/eval_aggregate.py \
  --asr-manifest eval/manifests/synthetic_whisper_eval_manifest.jsonl \
  --command-manifest eval/manifests/command_eval_manifest.jsonl \
  --command-catalog eval/refs/command_catalog.csv \
  --predictions eval/preds/whisper_tiny_synthetic/predictions.jsonl \
  --output-dir eval/metrics/whisper_tiny_synthetic \
  --run-id whisper_tiny_synthetic
```

For the Docker run, aggregate the Docker output with:

```bash
python3 scripts/eval_aggregate.py \
  --asr-manifest eval/manifests/synthetic_whisper_eval_manifest.jsonl \
  --command-manifest eval/manifests/command_eval_manifest.jsonl \
  --command-catalog eval/refs/command_catalog.csv \
  --predictions eval/preds/whisper_tiny_synthetic_docker/predictions.jsonl \
  --output-dir eval/metrics/whisper_tiny_synthetic_docker \
  --run-id whisper_tiny_synthetic_docker
```

## Verified Smoke Test

The Docker path has been verified with `whisper-tiny`, CPU, and `int8` compute type on the three synthetic EN/ZH/JA WAV files:

| Metric | Value |
|---|---:|
| Utterances | 3 |
| WER Macro | 0.0 |
| CER Macro | 0.0 |
| Avg Norm Error | 0.0 |
| Exact Match Rate | 1.0 |
| RTF P50 | 0.004332 |
| E2E Latency P50 (ms) | 10.178 |

## Notes

- The first Whisper run downloads the model weights.
- `faster-whisper` uses CTranslate2 and is much lighter than a full PyTorch setup for CPU testing.
- For a pure ASR-only run, use an ASR-only manifest when aggregating.
