import tempfile
import unittest
from pathlib import Path

from sudoku_benchmark_lab.benchmark.analysis import (
    create_markdown_report,
    discover_result_csvs,
    _read_result_csv,
    summarize_result_csv,
)


class BenchmarkAnalysisTests(unittest.TestCase):
    def test_discovers_only_normal_and_suite_raw_result_files(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            normal = root / "results"
            experiments = root / "experiments" / "results"
            suite_run = experiments / "run_01" / "2026-10-15_01"
            calibration = experiments / "calibration"
            normal.mkdir(parents=True)
            suite_run.mkdir(parents=True)
            calibration.mkdir(parents=True)
            normal_file = normal / "sample" / "2026-10-15_01" / "raw_results.csv"
            suite_file = suite_run / "raw_results.csv"
            normal_file.parent.mkdir(parents=True)
            normal_file.write_text("solver,status,puzzle_index,runtime_seconds\n", encoding="utf-8")
            suite_file.write_text("solver,status,puzzle_index,runtime_seconds\n", encoding="utf-8")
            (normal / "sample_summary.csv").write_text("ignored\n", encoding="utf-8")
            (suite_run / "summary_by_case.csv").write_text("ignored\n", encoding="utf-8")
            (calibration / "initial_raw.csv").write_text("ignored\n", encoding="utf-8")

            found = discover_result_csvs(normal, experiments)

        self.assertEqual(found, sorted([normal_file.resolve(), suite_file.resolve()]))

    def test_summarizes_suite_cases_separately_and_supports_legacy_raw_csv(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "raw_results.csv"
            path.write_text(
                "case,size,difficulty,puzzle_index,solver,status,runtime_seconds,timeout_seconds\n"
                "4x4_easy,4,easy,1,naive,solved,0.1,1\n"
                "4x4_easy,4,easy,2,naive,timeout,1,1\n"
                "4x4_hard,4,hard,1,naive,solved,0.3,1\n",
                encoding="utf-8",
            )
            summary = summarize_result_csv(path)

        self.assertEqual(summary["case"].tolist(), ["4x4_easy", "4x4_hard"])
        self.assertEqual(summary["solved"].tolist(), [1, 1])
        self.assertEqual(summary["tested"].tolist(), [2, 1])
        self.assertEqual(summary["success_rate"].tolist(), [50.0, 100.0])
        self.assertEqual(summary["timeout_seconds"].tolist(), [1, 1])

    def test_creates_markdown_report_and_visualizations(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            run = root / "sample" / "2026-10-15_01"
            run.mkdir(parents=True)
            csv_path = run / "raw_results.csv"
            csv_path.write_text(
                "size,difficulty,puzzle_index,solver,status,runtime_seconds,solution_found\n"
                "9,easy,1,naive,solved,0.01,True\n"
                "9,easy,1,csp,solved,0.02,True\n"
                "9,easy,2,naive,timeout,1.0,False\n"
                "9,easy,2,csp,solved,0.03,True\n",
                encoding="utf-8",
            )
            report = create_markdown_report(csv_path)

            content = report.read_text(encoding="utf-8")
            self.assertIn("raw_results", content)
            self.assertIn("naive", content)
            self.assertIn("Success rate", content)
            self.assertEqual(report, run / "summary.md")
            assets = run / "summary_assets"
            self.assertTrue((assets / "raw_results_success_rate.png").exists())
            self.assertTrue((assets / "raw_results_median_runtime.png").exists())


if __name__ == "__main__":
    unittest.main()
