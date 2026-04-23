#!/usr/bin/env python3
"""Run Whisper-family inference on a JSONL manifest and emit predictions.jsonl."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run faster-whisper inference for each sample in a manifest."
    )
    parser.add_argument("--manifest", required=True, help="Path to JSONL manifest.")
    parser.add_argument(
        "--output", required=True, help="Path to predictions.jsonl written by this run."
    )
    parser.add_argument("--model", default="tiny", help="Whisper model name.")
    parser.add_argument(
        "--device",
        default="cpu",
        help="Torch device string, for example cpu, cuda, or mps.",
    )
    parser.add_argument(
        "--runtime", default="faster-whisper", help="Runtime label written to output."
    )
    parser.add_argument(
        "--precision", default="fp32", help="Precision label written to output."
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Override language for all rows. Otherwise use manifest lang field.",
    )
    parser.add_argument(
        "--temperature", type=float, default=0.0, help="Whisper decode temperature."
    )
    parser.add_argument(
        "--beam-size", type=int, default=1, help="Whisper beam size."
    )
    parser.add_argument(
        "--best-of", type=int, default=1, help="Whisper best_of setting."
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="faster-whisper compute type, for example int8 or float32.",
    )
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


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def infer_rows(args: argparse.Namespace, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"faster-whisper runtime import failed: {exc}. "
            "Install requirements-whisper.txt first."
        ) from exc

    load_start = time.perf_counter()
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
    )
    load_ms = (time.perf_counter() - load_start) * 1000.0

    predictions: list[dict[str, Any]] = []
    for row in rows:
        audio_path = Path(row["audio_path"])
        if not audio_path.is_absolute():
            audio_path = Path.cwd() / audio_path
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        language = args.language or row.get("lang")
        start = time.perf_counter()
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            task="transcribe",
            temperature=args.temperature,
            beam_size=args.beam_size,
            best_of=args.best_of,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        audio_sec = float(row.get("duration_sec") or 0.0)
        rtf = (elapsed_ms / 1000.0) / audio_sec if audio_sec > 0 else None
        text_pred = "".join(segment.text for segment in segments).strip()

        predictions.append(
            {
                "utt_id": row["utt_id"],
                "model_id": f"whisper-{args.model}",
                "device": args.device,
                "precision": args.precision,
                "runtime": args.runtime,
                "streaming": False,
                "decode_config": {
                    "beam_size": args.beam_size,
                    "best_of": args.best_of,
                    "temperature": args.temperature,
                    "compute_type": args.compute_type,
                },
                "text_pred": text_pred,
                "lang_pred": getattr(info, "language", language),
                "audio_sec": audio_sec,
                "load_ms": round(load_ms, 3),
                "first_token_ms": None,
                "e2e_ms": round(elapsed_ms, 3),
                "rtf": round(rtf, 6) if rtf is not None else None,
                "peak_ram_mb": None,
                "avg_power_w": None,
            }
        )

    return predictions


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    rows = load_jsonl(manifest_path)
    predictions = infer_rows(args, rows)
    write_jsonl(output_path, predictions)
    print(f"Wrote {len(predictions)} predictions to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
