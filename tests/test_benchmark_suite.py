from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import sudoku_benchmark_lab.benchmark.suite as suite_module
from sudoku_benchmark_lab.benchmark.suite import (
    list_suite_configs,
    load_suite_config,
    run_suite,
)


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
            datasets = Path(root) / "datasets" / "suite"
            write_suite_config(config, solvers='["naive"]')
            run_suite(config, destination, datasets)
            self.assertEqual(len((destination / "raw_results.csv").read_text().splitlines()), 3)
            self.assertTrue((destination / "metadata.json").exists())
            self.assertTrue((datasets / "4x4_easy.jsonl").exists())
            metadata = json.loads(
                (destination / "metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                metadata["suite_config_sha256"],
                hashlib.sha256(config.read_bytes()).hexdigest(),
            )
            self.assertEqual(metadata["dataset_files"][0]["path"], str((datasets / "4x4_easy.jsonl").resolve()))
            with self.assertRaises(FileExistsError):
                run_suite(config, destination, datasets)

    def test_lists_every_toml_config_in_name_order(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            (directory / "zeta.toml").write_text("", encoding="utf-8")
            (directory / "alpha.toml").write_text("", encoding="utf-8")
            (directory / "ignored.txt").write_text("", encoding="utf-8")
            self.assertEqual(
                [path.name for path in list_suite_configs(directory)],
                ["alpha.toml", "zeta.toml"],
            )

    def test_default_runs_get_unique_timestamped_result_directories(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            config = root / "run_02.toml"
            datasets = root / "datasets"
            write_suite_config(config, solvers='["naive"]')
            with patch.object(suite_module, "RESULTS_DIR", root / "results"):
                first = run_suite(config, datasets_root=datasets)
                second = run_suite(config, datasets_root=datasets)
                self.assertEqual(first.parent.name, "run_02")
                self.assertEqual(second.parent.name, "run_02")
                self.assertNotEqual(first, second)
                self.assertTrue((first / "metadata.json").exists())
                self.assertTrue((second / "metadata.json").exists())

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
