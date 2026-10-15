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
import shutil
import subprocess
import time
import tomllib
from typing import Any

import pandas as pd

from sudoku_benchmark_lab.config import load_config
from sudoku_benchmark_lab.config import load_config
from sudoku_benchmark_lab.datasets.generation import generate_dataset_records
from sudoku_benchmark_lab.solvers.registry import SOLVERS, get_solver, solver_label
from sudoku_benchmark_lab.benchmark.reporting import summary_dataframe
from sudoku_benchmark_lab.benchmark.runner import (
    benchmark_dataset,
    solve_with_timeout,
    validate_solver_result,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "data/research_benchmark/final_benchmark.toml"
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
    output_dir = _non_empty_string(suite, "output_dir")
    solvers = suite.get("solvers")
    if (
        not isinstance(solvers, list)
        or not solvers
        or not all(isinstance(solver, str) for solver in solvers)
    ):
        raise ValueError("suite.solvers must be a non-empty list of solver names.")
    if len(solvers) != len(set(solvers)):
        raise ValueError("suite.solvers must not contain duplicates.")
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
        "output_dir": output_dir,
        "warmup": bool(suite.get("warmup", True)),
        "solvers": solvers,
        "cases": validated_cases,
    }


def run_suite(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    output_dir: str | Path | None = None,
) -> Path:
    config_path = Path(config_path)
    suite = load_suite_config(config_path)
    destination = Path(output_dir or suite["output_dir"])
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(
            f"Refusing to overwrite non-empty benchmark directory: {destination}"
        )

    destination.mkdir(parents=True, exist_ok=True)
    datasets_dir = destination / "datasets"
    datasets_dir.mkdir()
    shutil.copy2(config_path, destination / "suite_config.toml")
    project_config_path = destination / "project_config.json"
    project_config_text = json.dumps(load_config(), indent=2, sort_keys=True) + "\n"
    project_config_path.write_text(project_config_text, encoding="utf-8")

    started_at = datetime.now().astimezone()
    wall_start = time.perf_counter()
    raw_tables = []
    case_summaries = []
    dataset_files = []

    print(f"Benchmark suite: {suite['name']}")
    print(f"Output: {destination}")

    warmup_complete = False
    for case in suite["cases"]:
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
        dataset_path = datasets_dir / f"{case['name']}.jsonl"
        _write_jsonl(records, dataset_path)
        dataset_files.append(dataset_path)

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
        table.insert(1, "dataset", str(dataset_path.relative_to(destination)))
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
    by_size = _summary_by_size(raw, suite)

    raw_path = destination / "raw_results.csv"
    case_summary_path = destination / "summary_by_case.csv"
    size_summary_path = destination / "summary_by_size.csv"
    readme_tables_path = destination / "readme_tables.md"
    raw.to_csv(raw_path, index=False)
    by_case.to_csv(case_summary_path, index=False)
    by_size.to_csv(size_summary_path, index=False)
    readme_tables_path.write_text(
        render_readme_tables(suite, by_case, by_size),
        encoding="utf-8",
    )

    finished_at = datetime.now().astimezone()
    metadata = _environment_metadata(
        suite=suite,
        config_path=config_path,
        destination=destination,
        dataset_files=dataset_files,
        result_files=[raw_path, case_summary_path, size_summary_path, readme_tables_path, project_config_path],
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
    print(f"Case summary: {case_summary_path}")
    print(f"Size summary: {size_summary_path}")
    print(f"Environment metadata: {metadata_path}")
    if not errors.empty:
        raise RuntimeError(
            f"Benchmark completed with {len(errors)} error result(s); inspect {raw_path}."
        )
    return destination


def render_readme_tables(
    suite: dict[str, Any],
    by_case: pd.DataFrame,
    by_size: pd.DataFrame,
) -> str:
    clue_ranges = load_config()["generation"]["clue_percent_ranges"]
    lines = [
        "### Frozen benchmark configuration",
        "",
        "| Size | Clue-density tier | Clue range | Puzzles | Timeout / solver | Seed |",
        "|---:|:---|---:|---:|---:|---:|",
    ]
    for case in suite["cases"]:
        low, high = clue_ranges[case["difficulty"]]
        lines.append(
            f"| {case['size']}×{case['size']} | {case['difficulty']} | "
            f"{low * 100:.0f}–{high * 100:.0f}% | {case['count']} | "
            f"{case['timeout_seconds']:g} s | {case['seed']} |"
        )

    lines.extend(
        [
            "",
            "### Results aggregated by size",
            "",
            "Runtime statistics use successful solves only. Throughput is solved puzzles divided by total solver time, with each timeout charged at its cutoff.",
            "",
            "| Size | Solver | Attempted | Solved | Success | Timeouts | Median (ms) | Mean (ms) | p95 (ms) | Throughput (puzzles/s) |",
            "|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in by_size.itertuples(index=False):
        lines.append(
            f"| {row.size}×{row.size} | {solver_label(row.solver)} | "
            f"{row.tested} | {row.solved} | {row.success_rate:.1f}% | "
            f"{row.timeouts} | {_milliseconds(row.median_runtime_s)} | "
            f"{_milliseconds(row.avg_runtime_s)} | "
            f"{_milliseconds(row.p95_runtime_s)} | "
            f"{row.throughput_puzzles_s:.2f} |"
        )

    lines.extend(
        [
            "",
            "### Results by clue-density tier",
            "",
            "Each cell is `solved/attempted · median successful runtime · timeouts`.",
            "",
            "| Size / tier | "
            + " | ".join(solver_label(name) for name in suite["solvers"])
            + " |",
            "|:---|" + "---:|" * len(suite["solvers"]),
        ]
    )
    for case in suite["cases"]:
        case_rows = by_case[by_case["case"].eq(case["name"])].set_index("solver")
        cells = [
            _compact_result(case_rows.loc[solver_name])
            for solver_name in suite["solvers"]
        ]
        lines.append(
            f"| {case['size']}×{case['size']} {case['difficulty']} | "
            + " | ".join(cells)
            + " |"
        )

    return "\n".join(lines) + "\n"


def _summary_by_size(raw: pd.DataFrame, suite: dict[str, Any]) -> pd.DataFrame:
    rows = []
    size_order = list(dict.fromkeys(case["size"] for case in suite["cases"]))
    for size in size_order:
        for solver_name in suite["solvers"]:
            solver_rows = raw[
                raw["size"].eq(size) & raw["solver"].eq(solver_name)
            ]
            summary = summary_dataframe(solver_rows, tested=len(solver_rows)).iloc[0]
            row = {"size": size, **summary.to_dict()}
            rows.append(row)
    return pd.DataFrame(rows)


def _environment_metadata(
    *,
    suite: dict[str, Any],
    config_path: Path,
    destination: Path,
    dataset_files: list[Path],
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
        "suite_config_sha256": _sha256(config_path),
        "project_config_sha256": hashlib.sha256(
            json.dumps(load_config(), sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "source_file_sha256": {
            str(path): _sha256(PROJECT_ROOT / path)
            for path in SOURCE_FILES if (PROJECT_ROOT / path).exists()
        },
        "artifact_sha256": {
            str(path.relative_to(destination)): _sha256(path)
            for path in [*dataset_files, *result_files]
        },
    }


def _write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, sort_keys=True) + "\n")


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


def _milliseconds(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"{value * 1000:.3f}"


def _compact_result(row: pd.Series) -> str:
    runtime = _milliseconds(row["median_runtime_s"])
    runtime_label = "—" if runtime == "—" else f"{runtime} ms"
    return (
        f"{int(row['solved'])}/{int(row['tested'])} · {runtime_label} · "
        f"{int(row['timeouts'])} TO"
    )


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
        help="write to this new/empty directory instead of suite.output_dir",
    )
    args = parser.parse_args()
    run_suite(args.config, args.output_dir)


if __name__ == "__main__":
    main()
