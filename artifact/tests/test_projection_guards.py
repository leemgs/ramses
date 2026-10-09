import unittest
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parents[1]))
from make_figures import reject_projections as reject_figure_projections
from make_tables import (latex_text, reject_projections as reject_table_projections,
                         write_table_body)


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

    def test_table_body_leaves_final_row_open_for_booktabs_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "body.tex"
            write_table_body(output, [r"first \\", r"last \\"])
            self.assertEqual(output.read_text(), "first \\\\\nlast\n")

    def test_latex_text_escapes_csv_identifiers(self):
        self.assertEqual(latex_text("actual_mvtec&ad"), r"actual\_mvtec\&ad")


if __name__ == "__main__":
    unittest.main()
