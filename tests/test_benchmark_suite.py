from pathlib import Path
from contextlib import redirect_stdout
import hashlib
import io
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
from sudoku_benchmark_lab.datasets.generation import generate_dataset_records


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
            write_suite_config(config, solvers='["naive_iterative"]')
            output = io.StringIO()
            with redirect_stdout(output):
                run_suite(config, destination, datasets)
            self.assertIn("Summary by case (not saved)", output.getvalue())
            self.assertIn("4x4_easy", output.getvalue())
            self.assertEqual(len((destination / "raw_results.csv").read_text().splitlines()), 3)
            self.assertEqual(
                [path.name for path in destination.glob("*.csv")],
                ["raw_results.csv"],
            )
            self.assertFalse((destination / "readme_tables.md").exists())
            self.assertTrue((destination / "metadata.json").exists())
            self.assertFalse((destination / "project_config.json").exists())
            self.assertFalse((destination / "project_config.toml").exists())
            self.assertTrue((datasets / "4x4_easy.jsonl").exists())
            metadata = json.loads(
                (destination / "metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                metadata["suite_config_sha256"],
                hashlib.sha256(config.read_bytes()).hexdigest(),
            )
            self.assertNotIn("readme_tables.md", metadata["artifact_sha256"])
            self.assertEqual(
                set(metadata["artifact_sha256"]),
                {"raw_results.csv"},
            )
            self.assertNotIn("project_config_sha256", metadata)
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
            write_suite_config(config, solvers='["naive_iterative"]')
            with patch.object(suite_module, "RESULTS_DIR", root / "results"):
                first = run_suite(config, datasets_root=datasets)
                second = run_suite(config, datasets_root=datasets)
                self.assertEqual(first.parent.name, "run_02")
                self.assertEqual(second.parent.name, "run_02")
                self.assertNotEqual(first, second)
                self.assertTrue((first / "metadata.json").exists())
                self.assertTrue((second / "metadata.json").exists())

    def test_existing_dataset_is_reused_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            config = root / "run_03.toml"
            destination = root / "results"
            datasets = root / "datasets"
            dataset_path = datasets / "4x4_easy.jsonl"
            datasets.mkdir()
            write_suite_config(config, solvers='["naive_iterative"]')

            records = generate_dataset_records(4, "easy", 2, seed=123)
            for record in records:
                record["verification_mode"] = "legacy"
            dataset_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            original_dataset = dataset_path.read_bytes()

            run_suite(config, destination, datasets)

            self.assertEqual(dataset_path.read_bytes(), original_dataset)
            metadata = json.loads(
                (destination / "metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["dataset_files"][0]["source"], "reused_existing")

    def test_loads_valid_case_matrix(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "suite.toml"
            write_suite_config(path)

            suite = load_suite_config(path)

        self.assertEqual(suite["name"], "test-suite")
        self.assertEqual(suite["solvers"], ["csp"])
        self.assertEqual(suite["cases"][0]["count"], 2)
        self.assertEqual(suite["cases"][0]["timeout_seconds"], 0.5)

    def test_current_run_config_uses_canonical_solver_name(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "suite.toml"
            write_suite_config(path, solvers='["naive_iterative"]')

            suite = load_suite_config(path)

        self.assertEqual(suite["solvers"], ["naive_iterative"])

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
