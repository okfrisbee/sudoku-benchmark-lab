from pathlib import Path
import tempfile
import time
import unittest

from sudoku_benchmark_lab.benchmark.reporting import (
    result_paths, results_dataframe, summary_dataframe, write_csv,
)
from sudoku_benchmark_lab.benchmark.runner import (
    benchmark_dataset, solve_with_timeout, validate_solver_result,
)
from sudoku_benchmark_lab.datasets.generation import generate_dataset_records
from sudoku_benchmark_lab.datasets.io import write_dataset_records
from sudoku_benchmark_lab.solvers.result import SolverResult
from tests.config_helpers import temporary_config


def slow_solver(_puzzle):
    time.sleep(1)
    return SolverResult(solution=None, status="failed", runtime_seconds=1)


def crashing_solver(_puzzle):
    raise RuntimeError("boom")


def invalid_solver(_puzzle):
    return SolverResult(solution="1 " * 16, status="solved", runtime_seconds=0.001)


class BenchmarkTests(unittest.TestCase):
    def test_timeout_and_crash(self):
        self.assertEqual(solve_with_timeout(slow_solver, "", 0.02).status, "timeout")
        self.assertEqual(solve_with_timeout(crashing_solver, "", 1).status, "error")

    def test_invalid_solution_is_not_counted(self):
        puzzle = "1 0 3 0 0 4 0 2 2 0 4 0 0 3 0 1"
        result = validate_solver_result(puzzle, invalid_solver(puzzle))
        self.assertEqual(result.status, "error")
        self.assertIn("Invalid solver solution", result.error)

    def test_summary_charges_timeout_but_excludes_it_from_successful_runtime(self):
        rows = [
            {"puzzle_index": index, "solver_name": "fake", "result": result}
            for index, result in enumerate([
                SolverResult("1 2 3 4", "solved", 0.1),
                SolverResult("1 2 3 4", "solved", 0.3),
                SolverResult(None, "timeout", 2.0),
            ], 1)
        ]
        summary = summary_dataframe(results_dataframe(rows)).iloc[0]
        self.assertEqual(summary["solved"], 2)
        self.assertEqual(summary["timeouts"], 1)
        self.assertAlmostEqual(summary["median_runtime_s"], 0.2)
        self.assertAlmostEqual(summary["throughput_puzzles_s"], 2 / 2.4)

    def test_results_csv_keeps_solver_answers_and_empty_answers(self):
        invalid_answer = "1 " * 16
        rows = [
            {
                "puzzle_index": 1,
                "solver_name": "invalid",
                "result": SolverResult(invalid_answer, "error", 0.01),
            },
            {
                "puzzle_index": 2,
                "solver_name": "timed_out",
                "result": SolverResult(None, "timeout", 1.0),
            },
        ]

        table = results_dataframe(rows)

        self.assertEqual(table.loc[0, "solver_solution"], " ".join(["1"] * 16))
        self.assertEqual(table.loc[1, "solver_solution"], "")

    def test_result_data_and_filter_validation(self):
        records = generate_dataset_records(4, "easy", 1, seed=123)
        with tempfile.TemporaryDirectory() as root:
            with temporary_config(root, datasets_dir=root, benchmark_results_dir=Path(root) / "results"):
                path = write_dataset_records(records, 4, "easy")
                with self.assertRaisesRegex(ValueError, "Unknown solver"):
                    benchmark_dataset(path, solver_names=["missing"])
                with self.assertRaisesRegex(ValueError, "expected 9"):
                    benchmark_dataset(path, size=9, solver_names=["naive"])
                table = benchmark_dataset(path, 4, solver_names=["naive"])
                summary = summary_dataframe(table).iloc[0]
                csv_path, summary_path = result_paths(path)
                write_csv(table, csv_path)
                write_csv(summary_dataframe(table), summary_path)
                self.assertTrue(csv_path.exists())
                self.assertTrue(summary_path.exists())
                self.assertIn("solver_solution", table.columns)
                self.assertTrue(table.loc[0, "solver_solution"])

        self.assertEqual(table["status"].tolist(), ["solved"])
        self.assertEqual(table["size"].tolist(), [4])
        self.assertEqual(summary["solved"], 1)
        self.assertEqual(csv_path.name, "4x4_easy_1_results.csv")
        self.assertEqual(summary_path.name, "4x4_easy_1_summary.csv")


if __name__ == "__main__":
    unittest.main()
