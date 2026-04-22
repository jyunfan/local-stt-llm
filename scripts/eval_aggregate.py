#!/usr/bin/env python3
"""Aggregate ASR and command evaluation outputs into CSV and JSON reports."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


UTTERANCE_FIELDNAMES = [
    "utt_id",
    "model_id",
    "device",
    "precision",
    "runtime",
    "streaming",
    "lang",
    "task",
    "noise_tag",
    "distance",
    "wer",
    "cer",
    "exact_match",
    "csr_hit",
    "wrong_command",
    "false_activation",
    "intent_f1",
    "slot_f1",
    "audio_sec",
    "first_token_ms",
    "e2e_ms",
    "rtf",
    "peak_ram_mb",
    "avg_power_w",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate STT predictions into utterance and summary metrics."
    )
    parser.add_argument("--asr-manifest", required=True, help="Path to ASR manifest JSONL.")
    parser.add_argument(
        "--command-manifest", required=True, help="Path to command manifest JSONL."
    )
    parser.add_argument(
        "--command-catalog", required=True, help="Path to command catalog CSV."
    )
    parser.add_argument(
        "--predictions", required=True, help="Path to predictions JSONL for one run."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where utterance_metrics.csv and summary_metrics.json are written.",
    )
    parser.add_argument("--run-id", required=True, help="Stable run identifier for reports.")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected object on line {line_number} of {path}")
            rows.append(row)
    return rows


def load_command_catalog(path: Path) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            command_id = row["command_id"]
            catalog[command_id] = row
    return catalog


def normalize_text(text: str, lang: str) -> str:
    text = (text or "").strip().lower()
    if lang == "en":
        return " ".join(text.split())
    return "".join(text.split())


def tokenize_words(text: str) -> list[str]:
    return [token for token in text.split(" ") if token]


def tokenize_chars(text: str) -> list[str]:
    return list(text)


def levenshtein_distance(seq_a: list[str], seq_b: list[str]) -> int:
    if not seq_a:
        return len(seq_b)
    if not seq_b:
        return len(seq_a)

    prev = list(range(len(seq_b) + 1))
    for i, token_a in enumerate(seq_a, start=1):
        curr = [i]
        for j, token_b in enumerate(seq_b, start=1):
            cost = 0 if token_a == token_b else 1
            curr.append(
                min(
                    prev[j] + 1,
                    curr[j - 1] + 1,
                    prev[j - 1] + cost,
                )
            )
        prev = curr
    return prev[-1]


def error_rate(reference: str, prediction: str, unit: str) -> float:
    if unit == "word":
        ref_tokens = tokenize_words(reference)
        pred_tokens = tokenize_words(prediction)
    elif unit == "char":
        ref_tokens = tokenize_chars(reference)
        pred_tokens = tokenize_chars(prediction)
    else:
        raise ValueError(f"Unsupported unit: {unit}")

    if not ref_tokens:
        return 0.0 if not pred_tokens else 1.0
    return levenshtein_distance(ref_tokens, pred_tokens) / len(ref_tokens)


def parse_slots(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.fmean(values)


def stdev_or_none(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return statistics.stdev(values)


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def compute_slot_f1(ref_slots: dict[str, Any], pred_slots: dict[str, Any]) -> float:
    ref_pairs = {(key, json.dumps(value, ensure_ascii=False, sort_keys=True)) for key, value in ref_slots.items()}
    pred_pairs = {(key, json.dumps(value, ensure_ascii=False, sort_keys=True)) for key, value in pred_slots.items()}
    if not ref_pairs and not pred_pairs:
        return 1.0
    tp = len(ref_pairs & pred_pairs)
    fp = len(pred_pairs - ref_pairs)
    fn = len(ref_pairs - pred_pairs)
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def compute_intent_f1(ref_intent: str, pred_intent: str) -> float:
    return 1.0 if ref_intent == pred_intent else 0.0


def compute_command_metrics(sample: dict[str, Any], prediction: dict[str, Any]) -> dict[str, float | int]:
    ref_intent = sample.get("intent_ref", "none")
    ref_slots = parse_slots(sample.get("slots_ref"))
    pred_command = prediction.get("command_pred") or {}
    pred_intent = pred_command.get("intent", "none")
    pred_slots = parse_slots(pred_command.get("slots"))

    intent_f1 = compute_intent_f1(ref_intent, pred_intent)
    slot_f1 = compute_slot_f1(ref_slots, pred_slots)
    csr_hit = int(intent_f1 == 1.0 and slot_f1 == 1.0 and ref_intent != "none")

    wrong_command = int(
        ref_intent not in ("none", "")
        and pred_intent not in ("none", "")
        and (intent_f1 < 1.0 or slot_f1 < 1.0)
    )
    false_activation = int(ref_intent == "none" and pred_intent not in ("none", ""))

    return {
        "intent_f1": intent_f1,
        "slot_f1": slot_f1,
        "csr_hit": csr_hit,
        "wrong_command": wrong_command,
        "false_activation": false_activation,
    }


def merge_samples(
    asr_rows: list[dict[str, Any]],
    command_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    references = {row["utt_id"]: row for row in asr_rows + command_rows}
    merged_rows: list[dict[str, Any]] = []

    for prediction in predictions:
        utt_id = prediction["utt_id"]
        if utt_id not in references:
            raise ValueError(f"Prediction utt_id not found in manifests: {utt_id}")
        sample = references[utt_id]
        lang = sample["lang"]
        task = sample["task"]

        ref_text = normalize_text(sample.get("text_ref", ""), lang)
        pred_text = normalize_text(prediction.get("text_pred", ""), lang)
        wer = error_rate(ref_text, pred_text, "word") if lang == "en" else None
        cer = error_rate(ref_text, pred_text, "char")
        exact_match = int(ref_text == pred_text)

        row: dict[str, Any] = {
            "utt_id": utt_id,
            "model_id": prediction.get("model_id", ""),
            "device": prediction.get("device", ""),
            "precision": prediction.get("precision", ""),
            "runtime": prediction.get("runtime", ""),
            "streaming": bool(prediction.get("streaming", False)),
            "lang": lang,
            "task": task,
            "noise_tag": sample.get("noise_tag", ""),
            "distance": sample.get("distance", ""),
            "wer": wer,
            "cer": cer,
            "exact_match": exact_match,
            "csr_hit": 0,
            "wrong_command": 0,
            "false_activation": 0,
            "intent_f1": None,
            "slot_f1": None,
            "audio_sec": safe_float(prediction.get("audio_sec")),
            "first_token_ms": safe_float(prediction.get("first_token_ms")),
            "e2e_ms": safe_float(prediction.get("e2e_ms")),
            "rtf": safe_float(prediction.get("rtf")),
            "peak_ram_mb": safe_float(prediction.get("peak_ram_mb")),
            "avg_power_w": safe_float(prediction.get("avg_power_w")),
        }

        if task == "command":
            row.update(compute_command_metrics(sample, prediction))
        merged_rows.append(row)

    return merged_rows


def compute_summary(
    merged_rows: list[dict[str, Any]], run_id: str, group_by: list[str]
) -> dict[str, Any]:
    wer_values = [row["wer"] for row in merged_rows if row["wer"] is not None]
    cer_values = [row["cer"] for row in merged_rows if row["cer"] is not None]
    asr_rows = [row for row in merged_rows if row["task"] == "asr"]
    command_rows = [row for row in merged_rows if row["task"] == "command"]
    positive_command_rows = [
        row
        for row in command_rows
        if references_for_micro.get(row["utt_id"], {}).get("intent_ref") not in ("none", "")
    ]
    negative_rows = [
        row
        for row in command_rows
        if references_for_micro.get(row["utt_id"], {}).get("intent_ref") == "none"
    ]

    en_rows = [row for row in asr_rows if row["lang"] == "en" and row["wer"] is not None]
    zh_rows = [row for row in asr_rows if row["lang"] == "zh" and row["cer"] is not None]
    ja_rows = [row for row in asr_rows if row["lang"] == "ja" and row["cer"] is not None]
    avg_norm_candidates = []
    if en_rows:
        avg_norm_candidates.append(statistics.fmean(row["wer"] for row in en_rows))
    if zh_rows:
        avg_norm_candidates.append(statistics.fmean(row["cer"] for row in zh_rows))
    if ja_rows:
        avg_norm_candidates.append(statistics.fmean(row["cer"] for row in ja_rows))

    summary = {
        "run_id": run_id,
        "group_by": group_by,
        "n_utterances": len(merged_rows),
        "total_audio_sec": round_or_none(
            sum(row["audio_sec"] for row in merged_rows if row["audio_sec"] is not None)
        ),
        "metrics": {
            "wer_macro": round_or_none(mean_or_none(wer_values)),
            "wer_micro": round_or_none(micro_error_rate(merged_rows, unit="word", lang="en")),
            "cer_macro": round_or_none(mean_or_none(cer_values)),
            "cer_micro": round_or_none(micro_error_rate(merged_rows, unit="char", lang=None)),
            "avg_norm_error": round_or_none(mean_or_none(avg_norm_candidates)),
            "exact_match_rate": round_or_none(
                mean_or_none([row["exact_match"] for row in merged_rows])
            ),
            "csr": round_or_none(
                mean_or_none(
                    [row["csr_hit"] for row in positive_command_rows if row["intent_f1"] is not None]
                )
            ),
            "wrong_command_rate": round_or_none(
                mean_or_none(
                    [
                        row["wrong_command"]
                        for row in positive_command_rows
                        if row["intent_f1"] is not None
                    ]
                )
            ),
            "false_activation_rate": round_or_none(
                mean_or_none([row["false_activation"] for row in negative_rows])
            ),
            "intent_f1_macro": round_or_none(
                mean_or_none(
                    [row["intent_f1"] for row in positive_command_rows if row["intent_f1"] is not None]
                )
            ),
            "slot_f1_macro": round_or_none(
                mean_or_none(
                    [row["slot_f1"] for row in positive_command_rows if row["slot_f1"] is not None]
                )
            ),
            "rtf_mean": round_or_none(mean_or_none(numeric_values(merged_rows, "rtf"))),
            "rtf_std": round_or_none(stdev_or_none(numeric_values(merged_rows, "rtf"))),
            "rtf_p50": round_or_none(percentile(numeric_values(merged_rows, "rtf"), 0.50)),
            "rtf_p95": round_or_none(percentile(numeric_values(merged_rows, "rtf"), 0.95)),
            "e2e_ms_mean": round_or_none(mean_or_none(numeric_values(merged_rows, "e2e_ms"))),
            "e2e_ms_std": round_or_none(stdev_or_none(numeric_values(merged_rows, "e2e_ms"))),
            "e2e_ms_p50": round_or_none(percentile(numeric_values(merged_rows, "e2e_ms"), 0.50)),
            "e2e_ms_p95": round_or_none(percentile(numeric_values(merged_rows, "e2e_ms"), 0.95)),
            "first_token_ms_p50": round_or_none(
                percentile(numeric_values(merged_rows, "first_token_ms"), 0.50)
            ),
            "first_token_ms_p95": round_or_none(
                percentile(numeric_values(merged_rows, "first_token_ms"), 0.95)
            ),
            "peak_ram_mb_p95": round_or_none(
                percentile(numeric_values(merged_rows, "peak_ram_mb"), 0.95)
            ),
            "avg_power_w_mean": round_or_none(
                mean_or_none(numeric_values(merged_rows, "avg_power_w"))
            ),
        },
        "counts": {
            "by_lang": dict(Counter(row["lang"] for row in merged_rows)),
            "by_task": dict(Counter(row["task"] for row in merged_rows)),
        },
    }
    return summary


def numeric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [row[key] for row in rows if row.get(key) is not None]


def micro_error_rate(rows: list[dict[str, Any]], unit: str, lang: str | None) -> float | None:
    total_distance = 0
    total_length = 0
    for row in rows:
        if row["task"] != "asr":
            continue
        if lang is not None and row["lang"] != lang:
            continue
        sample_lang = row["lang"]
        ref = normalize_text(references_for_micro[row["utt_id"]]["text_ref"], sample_lang)
        pred = normalize_text(predictions_for_micro[row["utt_id"]].get("text_pred", ""), sample_lang)
        if unit == "word":
            ref_tokens = tokenize_words(ref)
            pred_tokens = tokenize_words(pred)
        else:
            ref_tokens = tokenize_chars(ref)
            pred_tokens = tokenize_chars(pred)
        if not ref_tokens:
            continue
        total_distance += levenshtein_distance(ref_tokens, pred_tokens)
        total_length += len(ref_tokens)
    if total_length == 0:
        return None
    return total_distance / total_length


def write_utterance_metrics(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=UTTERANCE_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, bool)
                    else (round_or_none(value) if isinstance(value, float) else value)
                    for key, value in row.items()
                    if key in UTTERANCE_FIELDNAMES
                }
            )


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


references_for_micro: dict[str, dict[str, Any]] = {}
predictions_for_micro: dict[str, dict[str, Any]] = {}


def main() -> int:
    args = parse_args()

    asr_manifest = Path(args.asr_manifest)
    command_manifest = Path(args.command_manifest)
    command_catalog_path = Path(args.command_catalog)
    predictions_path = Path(args.predictions)
    output_dir = Path(args.output_dir)

    asr_rows = load_jsonl(asr_manifest)
    command_rows = load_jsonl(command_manifest)
    _command_catalog = load_command_catalog(command_catalog_path)
    predictions = load_jsonl(predictions_path)

    global references_for_micro
    global predictions_for_micro
    references_for_micro = {row["utt_id"]: row for row in asr_rows + command_rows}
    predictions_for_micro = {row["utt_id"]: row for row in predictions}

    merged_rows = merge_samples(asr_rows, command_rows, predictions)
    summary = compute_summary(
        merged_rows,
        run_id=args.run_id,
        group_by=["model_id", "device", "precision", "lang", "task", "noise_tag", "distance"],
    )

    write_utterance_metrics(output_dir / "utterance_metrics.csv", merged_rows)
    write_summary(output_dir / "summary_metrics.json", summary)

    print(f"Wrote {len(merged_rows)} utterance rows to {output_dir / 'utterance_metrics.csv'}")
    print(f"Wrote summary report to {output_dir / 'summary_metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
