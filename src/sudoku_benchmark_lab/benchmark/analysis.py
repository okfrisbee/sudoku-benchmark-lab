"""Create Markdown reports from saved Sudoku benchmark result CSVs."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import re

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import pandas as pd

from sudoku_benchmark_lab.benchmark.reporting import summary_dataframe


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_EXPERIMENT_RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"


def discover_result_csvs(
    results_dir: str | Path = DEFAULT_RESULTS_DIR,
    experiment_results_dir: str | Path = DEFAULT_EXPERIMENT_RESULTS_DIR,
) -> list[Path]:
    """Find raw results from normal benchmarks and suite runs."""
    normal_root = Path(results_dir)
    experiment_root = Path(experiment_results_dir)
    discovered = []
    if normal_root.exists():
        discovered.extend(
            path for path in normal_root.rglob("raw_results.csv") if path.is_file()
        )
        # Retain discoverability for result CSVs written by older versions.
        discovered.extend(path for path in normal_root.glob("*_results.csv") if path.is_file())
    if experiment_root.exists():
        discovered.extend(
            path for path in experiment_root.rglob("raw_results.csv") if path.is_file()
        )
    return sorted({path.resolve() for path in discovered})


def create_markdown_report(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Summarize one raw results CSV beside its run artifacts."""
    source = Path(input_path).resolve()
    output = (
        Path(output_path).resolve()
        if output_path is not None
        else source.parent / "summary.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = output.parent / "summary_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    sections = [
        f"# Benchmark Summary: {source.stem}",
        "",
        "This report summarizes one saved raw benchmark CSV. Suite cases remain "
        "separate so differences in puzzle size, clue level, and time limits stay visible.",
        "",
        f"Source: `{_display_path(source)}`",
        "",
    ]
    summary = summarize_result_csv(source)
    chart_data = summary.copy()
    if "case" not in chart_data:
        chart_data.insert(0, "case", source.stem)
    chart_data = chart_data.rename(columns={"case": "Case", "solver": "Solver"})
    stem = _safe_stem(source.stem)
    success_chart = assets_dir / f"{stem}_success_rate.png"
    runtime_chart = assets_dir / f"{stem}_median_runtime.png"
    _plot_metric(chart_data, "success_rate", success_chart, "Success rate (%)", percent=True)
    _plot_metric(
        chart_data,
        "median_runtime_s",
        runtime_chart,
        "Median successful runtime (seconds)",
        logarithmic=True,
    )
    sections.extend(
        [
            _markdown_table(summary),
            "",
            f"![Success rate by case and solver]({_relative_asset(output, success_chart)})",
            "",
            f"![Median successful runtime by case and solver]({_relative_asset(output, runtime_chart)})",
            "",
        ]
    )

    output.write_text("\n".join(sections), encoding="utf-8")
    return output


def _read_result_csv(path: Path) -> pd.DataFrame:
    table = pd.read_csv(path)
    if table.empty:
        raise ValueError(f"Result CSV is empty: {path}")
    if "solver" not in table.columns or "status" not in table.columns:
        raise ValueError(f"Result CSV must contain solver and status columns: {path}")
    if "puzzle_index" not in table.columns:
        if "puzzle_id" in table.columns:
            table["puzzle_index"] = table["puzzle_id"]
        else:
            raise ValueError(f"Result CSV must contain puzzle_index or puzzle_id: {path}")

    table["status"] = table["status"].fillna("").astype(str).str.lower()
    table["puzzle_index"] = table["puzzle_index"].fillna("").astype(str)
    table["runtime_seconds"] = pd.to_numeric(
        table.get("runtime_seconds", pd.Series(index=table.index, dtype=float)),
        errors="coerce",
    ).fillna(0.0)
    for column in ("setup_seconds", "solve_seconds", "backtracks", "assignments", "recursive_calls"):
        if column not in table:
            table[column] = float("nan")
        else:
            table[column] = pd.to_numeric(table[column], errors="coerce")

    if "solution_found" in table:
        values = table["solution_found"]
        table["solution_found"] = values.map(_as_bool).fillna(False).astype(bool)
    else:
        table["solution_found"] = table["status"].eq("solved")
    return table


def _as_bool(value):
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"true", "1", "yes", "solved"}


def summarize_result_csv(input_path: str | Path) -> pd.DataFrame:
    """Return solver metrics from one raw CSV, separating suite cases when present."""
    path = Path(input_path)
    table = _read_result_csv(path)
    has_cases = (
        "case" in table.columns
        and table["case"].notna().any()
        and table["case"].astype(str).str.strip().ne("").any()
    )
    if has_cases:
        groups = table.groupby("case", sort=False, dropna=False)
    else:
        groups = [(None, table)]

    rows = []
    for case_name, case_rows in groups:
        tested = case_rows["puzzle_index"].nunique()
        summary = summary_dataframe(case_rows, tested=tested)
        for _, metrics in summary.iterrows():
            row = metrics.to_dict()
            if has_cases:
                row = {
                    "case": case_name,
                    "size": _first_value(case_rows, "size"),
                    "difficulty": _first_value(case_rows, "difficulty"),
                    "puzzle_count": tested,
                    "timeout_seconds": _first_value(case_rows, "timeout_seconds"),
                    **row,
                }
            rows.append(row)
    return pd.DataFrame(rows)


def _first_value(table: pd.DataFrame, column: str):
    if column not in table:
        return "—"
    values = table[column].dropna()
    if values.empty:
        return "—"
    return values.iloc[0]


def _markdown_table(summary: pd.DataFrame) -> str:
    labels = {
        "case": "Case",
        "size": "Size",
        "difficulty": "Clue level",
        "puzzle_count": "Puzzles",
        "timeout_seconds": "Timeout (s)",
        "solver": "Solver",
        "solved": "Solved",
        "tested": "Tested",
        "success_rate": "Success rate",
        "timeouts": "Timeouts",
        "failures": "Failures",
        "errors": "Errors",
        "median_runtime_s": "Median successful runtime (s)",
        "p95_runtime_s": "P95 runtime (s)",
        "throughput_puzzles_s": "Throughput (puzzles/s)",
    }
    headers = [column for column in labels if column in summary.columns]
    lines = [
        "| " + " | ".join(labels[column] for column in headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in summary.iterrows():
        values = []
        for column in headers:
            value = row[column]
            if column == "solved":
                rendered = f"{int(value)}/{int(row['tested'])}"
            elif column == "success_rate":
                rendered = f"{value:.1f}%"
            elif column in {
                "timeout_seconds",
                "median_runtime_s",
                "p95_runtime_s",
                "throughput_puzzles_s",
            }:
                rendered = _number(value)
            else:
                rendered = str(value)
            values.append(rendered.replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _plot_metric(
    summary: pd.DataFrame,
    metric: str,
    path: Path,
    title: str,
    *,
    percent: bool = False,
    logarithmic: bool = False,
) -> None:
    cases = list(dict.fromkeys(summary["Case"].astype(str)))
    solvers = list(dict.fromkeys(summary["Solver"].astype(str)))
    width = 0.8 / max(1, len(solvers))
    positions = list(range(len(cases)))
    lookup = {
        (str(row["Case"]), str(row["Solver"])): row[metric]
        for _, row in summary.iterrows()
    }

    fig = Figure(figsize=(max(8, len(cases) * 0.9), 4.8), dpi=150)
    FigureCanvasAgg(fig)
    axis = fig.subplots()
    for solver_index, solver in enumerate(solvers):
        offset = (solver_index - (len(solvers) - 1) / 2) * width
        values = [lookup.get((case, solver), float("nan")) for case in cases]
        axis.bar([pos + offset for pos in positions], values, width, label=solver)
    axis.set_title(title)
    axis.set_xlabel("Suite case" if len(cases) > 1 or cases[0] not in {"all"} else "Dataset")
    axis.set_ylabel(title)
    axis.set_xticks(positions, cases, rotation=35, ha="right")
    if percent:
        axis.set_ylim(0, 100)
    if logarithmic and any(
        isinstance(value, (int, float)) and math.isfinite(value) and value > 0
        for value in lookup.values()
    ):
        axis.set_yscale("log")
    axis.legend(title="Solver", ncols=min(len(solvers), 4))
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _relative_asset(output: Path, asset: Path) -> str:
    return asset.relative_to(output.parent).as_posix()


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "results"


def _number(value) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, help="one raw benchmark result CSV")
    parser.add_argument(
        "--output",
        type=Path,
        help="Markdown report path (default: summary.md beside the CSV)",
    )
    args = parser.parse_args(argv)
    try:
        report = create_markdown_report(args.input_csv, args.output)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Markdown report written to: {report}")
    print(f"Chart images written to: {report.parent / 'summary_assets'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
