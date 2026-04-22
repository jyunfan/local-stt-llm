# Evaluation Templates

This directory contains starter templates for the evaluation protocol described in [docs/edge_stt_research_plan.md](/Users/jftsai/src/local-stt-llm/docs/edge_stt_research_plan.md).

## Structure

```text
eval/
  manifests/
    asr_eval_manifest.jsonl
    command_eval_manifest.jsonl
  refs/
    command_catalog.csv
  preds/
    .gitkeep
  metrics/
    .gitkeep
```

## Notes

- All text files should use UTF-8 encoding.
- `audio_path` should point to the actual waveform used for evaluation.
- `utt_id` must be unique across all manifests.
- `preds/` and `metrics/` are run output directories and are intentionally empty by default.
- For English use WER as the main transcription metric.
- For Chinese and Japanese use CER as the main transcription metric.

## Minimal Workflow

1. Fill `manifests/asr_eval_manifest.jsonl` with general ASR evaluation samples.
2. Fill `manifests/command_eval_manifest.jsonl` with command-and-control samples.
3. Expand `refs/command_catalog.csv` so every command sample has a stable `command_id`.
4. Run each model and write one `predictions.jsonl` under `preds/{run_id}/`.
5. Aggregate utterance-level and summary metrics into `metrics/{run_id}/`.
