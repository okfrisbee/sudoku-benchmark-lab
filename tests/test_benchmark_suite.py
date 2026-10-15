from pathlib import Path
import tempfile
import unittest

from sudoku_benchmark_lab.benchmark.suite import load_suite_config, run_suite


def write_suite_config(path: Path, *, solvers='["csp"]', duplicate=False) -> None:
    cases = [
        "[[cases]]",
        'name = "4x4_easy"',
        "size = 4",
        'difficulty = "easy"',
        "count = 2",
        "seed = 123",
        "timeout_seconds = 0.5",
    ]
    if duplicate:
        cases.extend(cases)
    path.write_text(
        "\n".join(
            [
                "[suite]",
                'name = "test-suite"',
                'output_dir = "results"',
                f"solvers = {solvers}",
                "",
                *cases,
                "",
            ]
        ),
        encoding="utf-8",
    )


class BenchmarkSuiteConfigTests(unittest.TestCase):
    def test_small_suite_writes_artifacts_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            config = Path(root) / "suite.toml"
            destination = Path(root) / "output"
            write_suite_config(config, solvers='["naive"]')
            run_suite(config, destination)
            self.assertEqual(len((destination / "raw_results.csv").read_text().splitlines()), 3)
            self.assertTrue((destination / "metadata.json").exists())
            with self.assertRaises(FileExistsError):
                run_suite(config, destination)

    def test_loads_valid_case_matrix(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "suite.toml"
            write_suite_config(path)

            suite = load_suite_config(path)

        self.assertEqual(suite["name"], "test-suite")
        self.assertEqual(suite["solvers"], ["csp"])
        self.assertEqual(suite["cases"][0]["count"], 2)
        self.assertEqual(suite["cases"][0]["timeout_seconds"], 0.5)

    def test_rejects_unknown_solver(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "suite.toml"
            write_suite_config(path, solvers='["not-a-solver"]')

            with self.assertRaisesRegex(ValueError, "Unknown solver"):
                load_suite_config(path)

    def test_rejects_duplicate_case_name(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "suite.toml"
            write_suite_config(path, duplicate=True)

            with self.assertRaisesRegex(ValueError, "Duplicate benchmark case"):
                load_suite_config(path)


if __name__ == "__main__":
    unittest.main()
