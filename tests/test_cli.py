import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from sudoku_benchmark_lab import cli


class SummaryMenuTests(unittest.TestCase):
    def test_summarizes_one_selected_result_csv(self):
        with tempfile.TemporaryDirectory() as root:
            csv_path = Path(root) / "raw_results.csv"
            csv_path.touch()
            summary = pd.DataFrame([{"solver": "naive", "solved": 1, "tested": 1}])
            output = io.StringIO()
            with (
                patch("sudoku_benchmark_lab.cli.discover_result_csvs", return_value=[csv_path]),
                patch("sudoku_benchmark_lab.cli.summarize_result_csv", return_value=summary) as summarize,
                patch("builtins.input", return_value="1"),
                patch("sudoku_benchmark_lab.cli.print_summary_table") as print_table,
                redirect_stdout(output),
            ):
                cli.summarize_results_menu()

        summarize.assert_called_once_with(csv_path)
        print_table.assert_called_once_with(summary)
        self.assertIn("Available benchmark result CSVs", output.getvalue())


if __name__ == "__main__":
    unittest.main()
