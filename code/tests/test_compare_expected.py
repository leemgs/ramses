import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "code" / "compare_expected.py"
KEYS = ("system", "task", "model", "precision", "input_tokens",
        "output_tokens", "batch", "concurrency")
METRICS = ("p50_ms", "p95_ms", "p99_ms", "energy_per_request_j")


def write_summary(path, rows):
    fields = [*KEYS, *METRICS, "data_source"]
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def row(system, source, value="10"):
    result = dict(zip(KEYS, (system, "ttft", "llama3-8b", "fp16",
                             "128", "1", "1", "1")))
    result.update({metric: value for metric in METRICS})
    result["data_source"] = source
    return result


class CompareExpectedTests(unittest.TestCase):
    def test_retains_unmatched_configurations(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            expected, actual, output = (tmp / name for name in
                                        ("expected.csv", "actual.csv", "out.csv"))
            write_summary(expected, [row("default", "synthetic_expected_projection_not_measured"),
                                     row("ramses", "synthetic_expected_projection_not_measured")])
            write_summary(actual, [row("default", "hardware_measurement", "12"),
                                   row("vllm", "hardware_measurement", "8")])
            subprocess.run([sys.executable, SCRIPT, expected, actual, output], check=True)
            with output.open(newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual({r["comparison_status"] for r in rows},
                             {"matched", "expected_only", "actual_only"})

    def test_rejects_projection_as_actual(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            expected, actual, output = (tmp / name for name in
                                        ("expected.csv", "actual.csv", "out.csv"))
            projection = "synthetic_expected_projection_not_measured"
            write_summary(expected, [row("default", projection)])
            write_summary(actual, [row("default", projection)])
            result = subprocess.run([sys.executable, SCRIPT, expected, actual, output],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("synthetic projection", result.stderr)


if __name__ == "__main__":
    unittest.main()
