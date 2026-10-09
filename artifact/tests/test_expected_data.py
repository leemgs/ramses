import csv
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from generate_expected_data import MODELS, SOURCE, SYSTEM_FACTORS, TASK_BASE_MS
from generate_expected_data import write_industrial, write_raw, write_sensitivity


class TestExpectedData(unittest.TestCase):
    def test_complete_matrix_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.jsonl"
            write_raw(path, seed=7, requests_per_run=2)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            expected = len(SYSTEM_FACTORS) * len(MODELS) * len(TASK_BASE_MS) * 5 * 2
            self.assertEqual(len(rows), expected)
            self.assertTrue(all(row["data_source"] == SOURCE for row in rows))
            groups = {(row["system"], row["model"], row["task"]) for row in rows}
            self.assertEqual(len(groups), len(SYSTEM_FACTORS) * len(MODELS) * len(TASK_BASE_MS))

    def test_csvs_are_marked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = (root / "industrial.csv", root / "sensitivity.csv")
            write_industrial(paths[0]); write_sensitivity(paths[1])
            for path in paths:
                with path.open(newline="") as source:
                    rows = list(csv.DictReader(source))
                self.assertTrue(rows)
                self.assertTrue(all(row["data_source"] == SOURCE for row in rows))


if __name__ == "__main__":
    unittest.main()
