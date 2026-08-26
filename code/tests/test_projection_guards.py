import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from make_figures import reject_projections as reject_figure_projections
from make_tables import reject_projections as reject_table_projections


class TestProjectionGuards(unittest.TestCase):
    def test_synthetic_rows_are_rejected(self):
        rows = [{"data_source": "synthetic_expected_projection_not_measured"}]
        with self.assertRaises(SystemExit):
            reject_table_projections(rows, "summary")
        with self.assertRaises(SystemExit):
            reject_figure_projections(rows, "summary")

    def test_measured_rows_are_accepted(self):
        rows = [{"data_source": "measured_a100_run"}]
        self.assertIsNone(reject_table_projections(rows, "summary"))
        self.assertIsNone(reject_figure_projections(rows, "summary"))


if __name__ == "__main__":
    unittest.main()
