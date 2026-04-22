import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval_aggregate.py"
ASR_MANIFEST = ROOT / "eval" / "manifests" / "asr_eval_manifest.jsonl"
COMMAND_MANIFEST = ROOT / "eval" / "manifests" / "command_eval_manifest.jsonl"
COMMAND_CATALOG = ROOT / "eval" / "refs" / "command_catalog.csv"
PREDICTIONS = ROOT / "eval" / "preds" / "sample_run" / "predictions.jsonl"


class EvalAggregateTest(unittest.TestCase):
    def test_aggregate_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--asr-manifest",
                    str(ASR_MANIFEST),
                    "--command-manifest",
                    str(COMMAND_MANIFEST),
                    "--command-catalog",
                    str(COMMAND_CATALOG),
                    "--predictions",
                    str(PREDICTIONS),
                    "--output-dir",
                    str(output_dir),
                    "--run-id",
                    "sample_run",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("Wrote 7 utterance rows", result.stdout)

            utterance_path = output_dir / "utterance_metrics.csv"
            summary_path = output_dir / "summary_metrics.json"
            self.assertTrue(utterance_path.exists())
            self.assertTrue(summary_path.exists())

            with utterance_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 7)

            by_utt = {row["utt_id"]: row for row in rows}
            self.assertEqual(by_utt["cmd_en_0001"]["csr_hit"], "1")
            self.assertEqual(by_utt["cmd_zh_0001"]["wrong_command"], "1")
            self.assertEqual(by_utt["noncmd_zh_0001"]["false_activation"], "1")

            with summary_path.open("r", encoding="utf-8") as handle:
                summary = json.load(handle)

            self.assertEqual(summary["n_utterances"], 7)
            self.assertEqual(summary["counts"]["by_lang"], {"en": 2, "zh": 3, "ja": 2})
            self.assertAlmostEqual(summary["metrics"]["csr"], 0.666667, places=6)
            self.assertAlmostEqual(summary["metrics"]["wrong_command_rate"], 0.333333, places=6)
            self.assertAlmostEqual(summary["metrics"]["false_activation_rate"], 1.0, places=6)
            self.assertAlmostEqual(summary["metrics"]["intent_f1_macro"], 0.666667, places=6)
            self.assertAlmostEqual(summary["metrics"]["slot_f1_macro"], 1.0, places=6)
            self.assertAlmostEqual(summary["metrics"]["avg_norm_error"], 0.177778, places=6)


if __name__ == "__main__":
    unittest.main()
