"""Run a deterministic, evidence-producing benchmark suite."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from importlib import metadata as importlib_metadata
import json
from math import isqrt
import multiprocessing
import os
from pathlib import Path
import platform
import subprocess
import time
import tomllib
from typing import Any

import pandas as pd

from sudoku_benchmark_lab.config import load_config
from sudoku_benchmark_lab.board import board_size, parse_board
from sudoku_benchmark_lab.datasets.generation import generate_dataset_records
from sudoku_benchmark_lab.datasets.io import read_dataset
from sudoku_benchmark_lab.solvers.registry import (
    SOLVERS,
    canonical_solver_name,
    get_solver,
)
from sudoku_benchmark_lab.benchmark.reporting import (
    print_summary_table,
    summary_dataframe,
)
from sudoku_benchmark_lab.benchmark.runner import (
    benchmark_dataset,
    solve_with_timeout,
    validate_solver_result,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIGS_DIR = PROJECT_ROOT / "experiments/configs"
SUITE_DATASETS_DIR = PROJECT_ROOT / "datasets/suites"
RESULTS_DIR = PROJECT_ROOT / "experiments/results"
DEFAULT_CONFIG_PATH = CONFIGS_DIR / "run_01.toml"
SOURCE_FILES = [
    Path("src/sudoku_benchmark_lab") / path for path in (
        "benchmark/reporting.py", "benchmark/runner.py", "benchmark/suite.py",
        "board.py", "config.py", "validation.py", "datasets/generation.py", "datasets/io.py",
        "solvers/registry.py", "solvers/result.py", "solvers/csp.py",
        "solvers/dlx.py", "solvers/naive.py", "solvers/naive_recursive.py",
        "solvers/sat.py", "solvers/smt.py",
    )
]


def load_suite_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("rb") as config_file:
        config = tomllib.load(config_file)

    suite = config.get("suite")
    cases = config.get("cases")
    if not isinstance(suite, dict):
        raise ValueError("Benchmark config must contain a [suite] table.")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Benchmark config must define at least one [[cases]] table.")

    name = _non_empty_string(suite, "name")
    solvers = suite.get("solvers")
    if (
        not isinstance(solvers, list)
        or not solvers
        or not all(isinstance(solver, str) for solver in solvers)
    ):
        raise ValueError("suite.solvers must be a non-empty list of solver names.")
    if len(solvers) != len(set(solvers)):
        raise ValueError("suite.solvers must not contain duplicates.")
    solvers = [canonical_solver_name(solver) for solver in solvers]
    if len(solvers) != len(set(solvers)):
        raise ValueError("suite.solvers must not contain duplicate canonical solver names.")
    unknown_solvers = [solver for solver in solvers if solver not in SOLVERS]
    if unknown_solvers:
        raise ValueError(f"Unknown solver(s): {', '.join(unknown_solvers)}")

    clue_ranges = load_config()["generation"]["clue_percent_ranges"]
    validated_cases = []
    seen_names = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Each benchmark case must be a table.")
        case_name = _non_empty_string(case, "name")
        if (
            Path(case_name).name != case_name
            or "\\" in case_name
            or case_name in {".", ".."}
        ):
            raise ValueError(f"Case name {case_name!r} must be a filename-safe name.")
        if case_name in seen_names:
            raise ValueError(f"Duplicate benchmark case name: {case_name}")
        seen_names.add(case_name)

        size = _positive_int(case, "size")
        box = isqrt(size)
        if box * box != size:
            raise ValueError(f"Case {case_name!r} size must be a perfect square.")
        difficulty = _non_empty_string(case, "difficulty")
        if difficulty not in clue_ranges:
            raise ValueError(
                f"Case {case_name!r} has unknown difficulty {difficulty!r}."
            )
        count = _positive_int(case, "count")
        seed = _non_negative_int(case, "seed")
        timeout_seconds = _positive_number(case, "timeout_seconds")
        validated_cases.append(
            {
                "name": case_name,
                "size": size,
                "difficulty": difficulty,
                "count": count,
                "seed": seed,
                "timeout_seconds": timeout_seconds,
            }
        )

    return {
        "name": name,
        "warmup": bool(suite.get("warmup", True)),
        "solvers": solvers,
        "cases": validated_cases,
    }


def run_suite(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    output_dir: str | Path | None = None,
    datasets_root: str | Path | None = None,
) -> Path:
    config_path = Path(config_path)
    suite = load_suite_config(config_path)
    run_name = config_path.stem
    datasets_dir = Path(datasets_root) if datasets_root else SUITE_DATASETS_DIR / run_name
    datasets_dir.mkdir(parents=True, exist_ok=True)

    prepared_cases = []
    for case in suite["cases"]:
        dataset_path = datasets_dir / f"{case['name']}.jsonl"
        if dataset_path.exists():
            records = read_dataset(dataset_path)
            _validate_existing_dataset(dataset_path, records, case)
            dataset_source = "reused_existing"
            print(
                f"\nUsing existing dataset for {case['name']}: "
                f"{dataset_path} ({len(records)} puzzles)"
            )
        else:
            print(
                f"\nGenerating {case['count']} deterministic {case['name']} puzzles "
                f"(seed={case['seed']})..."
            )
            records = generate_dataset_records(
                case["size"],
                case["difficulty"],
                case["count"],
                seed=case["seed"],
            )
            _write_dataset_without_replacing(dataset_path, records)
            dataset_source = "generated"
        prepared_cases.append((case, records, dataset_path, dataset_source))

    destination = Path(output_dir) if output_dir else _new_results_directory(run_name)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty benchmark directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now().astimezone()
    wall_start = time.perf_counter()
    raw_tables = []
    case_summaries = []
    dataset_files = []
    dataset_sources = {}

    print(f"Benchmark suite: {suite['name']}")
    print(f"Output: {destination}")

    warmup_complete = False
    for case, records, dataset_path, dataset_source in prepared_cases:
        dataset_files.append(dataset_path)
        dataset_sources[str(dataset_path)] = dataset_source

        if suite["warmup"] and not warmup_complete:
            print("Warming each solver once (not recorded)...")
            puzzle = records[0]["puzzle"]
            for solver_name in suite["solvers"]:
                result = solve_with_timeout(
                    get_solver(solver_name),
                    puzzle,
                    timeout_seconds=case["timeout_seconds"],
                )
                validate_solver_result(puzzle, result)
            warmup_complete = True

        print(
            f"Running {case['name']} with a {case['timeout_seconds']:g} s "
            "per-solver cutoff..."
        )
        table = benchmark_dataset(
            dataset_path,
            case["size"],
            solver_names=suite["solvers"],
            timeout_seconds=case["timeout_seconds"],
        )

        table.insert(0, "case", case["name"])
        table.insert(1, "dataset", _repository_or_absolute_path(dataset_path))
        raw_tables.append(table)

        summary = summary_dataframe(table, tested=case["count"])
        summary.insert(0, "case", case["name"])
        summary.insert(1, "size", case["size"])
        summary.insert(2, "difficulty", case["difficulty"])
        summary.insert(3, "puzzle_count", case["count"])
        summary.insert(4, "timeout_seconds", case["timeout_seconds"])
        case_summaries.append(summary)

    raw = pd.concat(raw_tables, ignore_index=True)
    by_case = pd.concat(case_summaries, ignore_index=True)

    raw_path = destination / "raw_results.csv"
    raw.to_csv(raw_path, index=False)

    finished_at = datetime.now().astimezone()
    metadata = _environment_metadata(
        suite=suite,
        config_path=config_path,
        destination=destination,
        dataset_files=dataset_files,
        dataset_sources=dataset_sources,
        result_files=[raw_path],
        started_at=started_at,
        finished_at=finished_at,
        wall_seconds=time.perf_counter() - wall_start,
    )
    metadata_path = destination / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    errors = raw[raw["status"].eq("error")]
    print(f"\nRaw results: {raw_path}")
    print("\nSummary by case (not saved):")
    print_summary_table(by_case)
    print(f"Environment metadata: {metadata_path}")
    if not errors.empty:
        raise RuntimeError(
            f"Benchmark completed with {len(errors)} error result(s); inspect {raw_path}."
        )
    return destination


def _environment_metadata(
    *,
    suite: dict[str, Any],
    config_path: Path,
    destination: Path,
    dataset_files: list[Path],
    dataset_sources: dict[str, str],
    result_files: list[Path],
    started_at: datetime,
    finished_at: datetime,
    wall_seconds: float,
) -> dict[str, Any]:
    requirement_names = _requirement_names(PROJECT_ROOT / "requirements.txt")
    dependencies = {}
    for name in requirement_names:
        try:
            dependencies[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            dependencies[name] = None

    return {
        "suite": suite["name"],
        "benchmark_date": started_at.date().isoformat(),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "wall_seconds": wall_seconds,
        "cpu": _cpu_model(),
        "logical_cpu_count": os.cpu_count(),
        "operating_system": _operating_system(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "dependencies": dependencies,
        "multiprocessing_start_method": (
            "fork" if "fork" in multiprocessing.get_all_start_methods() else "default"
        ),
        "timer": "time.perf_counter",
        "runtime_scope": (
            "End-to-end solver function runtime, including parsing, model/data-structure "
            "setup, search, and solution construction; child-process launch and result "
            "validation are excluded."
        ),
        "timeout_scope": (
            "Wall-clock cutoff enforced by a dedicated child process. Timeout rows are "
            "charged exactly the configured cutoff; parent termination overhead is excluded."
        ),
        "correctness_check": (
            "Every solved result was checked for preserved givens and valid rows, columns, "
            "and boxes."
        ),
        "warmup": (
            "One unrecorded solve per solver on the first case"
            if suite["warmup"]
            else "disabled"
        ),
        "solver_order": suite["solvers"],
        "cases": suite["cases"],
        "clue_percent_ranges": load_config()["generation"]["clue_percent_ranges"],
        "source_revision": _git_revision(),
        "suite_config": str(config_path.resolve().relative_to(PROJECT_ROOT))
        if config_path.resolve().is_relative_to(PROJECT_ROOT)
        else str(config_path.resolve()),
        "suite_config_sha256": _sha256(config_path),
        "source_file_sha256": {
            str(path): _sha256(PROJECT_ROOT / path)
            for path in SOURCE_FILES if (PROJECT_ROOT / path).exists()
        },
        "artifact_sha256": {
            str(path.relative_to(destination)): _sha256(path)
            for path in result_files
        },
        "dataset_files": [
            {
                "path": str(path.resolve().relative_to(PROJECT_ROOT))
                if path.resolve().is_relative_to(PROJECT_ROOT)
                else str(path.resolve()),
                "sha256": _sha256(path),
                "source": dataset_sources[str(path)],
            }
            for path in dataset_files
        ],
    }


def _validate_existing_dataset(
    path: Path,
    records: list[dict[str, Any]],
    case: dict[str, Any],
) -> None:
    if len(records) != case["count"]:
        raise ValueError(
            f"Existing dataset {path} contains {len(records)} puzzles; "
            f"the suite config expects {case['count']}."
        )
    for index, record in enumerate(records, 1):
        actual_size, _box = board_size(parse_board(record["puzzle"]))
        if actual_size != case["size"]:
            raise ValueError(
                f"Puzzle {index} in {path} has size {actual_size}; "
                f"the suite config expects {case['size']}."
            )
        difficulty = record.get("difficulty")
        if difficulty is not None and difficulty != case["difficulty"]:
            raise ValueError(
                f"Puzzle {index} in {path} has clue level {difficulty!r}; "
                f"the suite config expects {case['difficulty']!r}."
            )


def _write_dataset_without_replacing(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    """Write a deterministic suite dataset, preserving any existing version."""
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        for record in records:
            temporary.write(json.dumps(record, sort_keys=True) + "\n")
    try:
        if path.exists():
            if _sha256(path) != _sha256(temporary_path):
                raise FileExistsError(
                    f"Dataset appeared during generation with different contents: {path}. "
                    "Retry the suite to load and validate the saved dataset."
                )
            return
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _new_results_directory(run_name: str) -> Path:
    """Create a unique timestamped result directory for this suite config."""
    run_root = RESULTS_DIR / run_name
    run_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S_%f")
    destination = run_root / stamp
    destination.mkdir()
    return destination


def _repository_or_absolute_path(path: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(PROJECT_ROOT):
        return str(resolved.relative_to(PROJECT_ROOT))
    return str(resolved)


def list_suite_configs(directory: str | Path = CONFIGS_DIR) -> list[Path]:
    """Return TOML suite configs in stable display order."""
    config_dir = Path(directory)
    return sorted(path for path in config_dir.glob("*.toml") if path.is_file())


def _requirement_names(path: Path) -> list[str]:
    names = []
    for line in path.read_text(encoding="utf-8").splitlines():
        requirement = line.strip()
        if not requirement or requirement.startswith("#"):
            continue
        names.append(requirement.split("==", 1)[0])
    return names


def _cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def _operating_system() -> str:
    os_release = Path("/etc/os-release")
    if os_release.exists():
        for line in os_release.read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    return platform.system()


def _git_revision() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    return result.stdout.strip() or None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _non_empty_string(table: dict[str, Any], key: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string.")
    return value


def _positive_int(table: dict[str, Any], key: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{key} must be a positive integer.")
    return value


def _non_negative_int(table: dict[str, Any], key: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer.")
    return value


def _positive_number(table: dict[str, Any], key: str) -> float:
    value = table.get(key)
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(f"{key} must be a positive number.")
    return float(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"suite TOML (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="write results to this specific directory instead of the timestamped default",
    )
    args = parser.parse_args()
    run_suite(args.config, args.output_dir)


if __name__ == "__main__":
    main()
