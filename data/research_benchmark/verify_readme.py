"""Verify that published benchmark documentation matches the saved results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


START_MARKER = "<!-- BENCHMARK_TABLES_START -->"
END_MARKER = "<!-- BENCHMARK_TABLES_END -->"
HIGHLIGHTS_START_MARKER = "<!-- BENCHMARK_HIGHLIGHTS_START -->"
HIGHLIGHTS_END_MARKER = "<!-- BENCHMARK_HIGHLIGHTS_END -->"
RESULTS_START_MARKER = "<!-- BENCHMARK_RESULTS_START -->"
RESULTS_END_MARKER = "<!-- BENCHMARK_RESULTS_END -->"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_README = REPOSITORY_ROOT / "README.md"
DEFAULT_BENCHMARK = REPOSITORY_ROOT / "BENCHMARK.md"
DEFAULT_TABLES = (
    REPOSITORY_ROOT
    / "data"
    / "research_benchmark"
    / "final"
    / "readme_tables.md"
)
DEFAULT_SIZE_SUMMARY = DEFAULT_TABLES.with_name("summary_by_size.csv")
DEFAULT_CASE_SUMMARY = DEFAULT_TABLES.with_name("summary_by_case.csv")


def verify_readme_tables(
    readme_path: str | Path = DEFAULT_BENCHMARK,
    tables_path: str | Path = DEFAULT_TABLES,
) -> None:
    embedded = _embedded_block(
        Path(readme_path),
        START_MARKER,
        END_MARKER,
        "detailed benchmark tables",
    )
    expected = Path(tables_path).read_text(encoding="utf-8").strip()
    if embedded != expected:
        raise ValueError("BENCHMARK tables do not match the saved artifact.")


def verify_readme_highlights(
    readme_path: str | Path = DEFAULT_README,
    size_summary_path: str | Path = DEFAULT_SIZE_SUMMARY,
    case_summary_path: str | Path = DEFAULT_CASE_SUMMARY,
) -> None:
    embedded = _embedded_block(
        Path(readme_path),
        HIGHLIGHTS_START_MARKER,
        HIGHLIGHTS_END_MARKER,
        "benchmark highlights",
    )
    expected = render_readme_highlights(size_summary_path, case_summary_path).strip()
    if embedded != expected:
        raise ValueError("README highlights do not match the saved summaries.")


def verify_readme_results(
    readme_path: str | Path = DEFAULT_README,
    size_summary_path: str | Path = DEFAULT_SIZE_SUMMARY,
) -> None:
    embedded = _embedded_block(
        Path(readme_path),
        RESULTS_START_MARKER,
        RESULTS_END_MARKER,
        "benchmark results",
    )
    expected = render_readme_results(size_summary_path).strip()
    if embedded != expected:
        raise ValueError("README results do not match the saved size summary.")


def render_readme_highlights(
    size_summary_path: str | Path = DEFAULT_SIZE_SUMMARY,
    case_summary_path: str | Path = DEFAULT_CASE_SUMMARY,
) -> str:
    size_rows = {
        (int(row["size"]), row["solver"]): row
        for row in _read_csv(size_summary_path)
    }
    case_rows = {
        (row["case"], row["solver"]): row
        for row in _read_csv(case_summary_path)
    }

    naive_9_easy = case_rows[("9x9_easy", "naive")]
    csp_9_hard = case_rows[("9x9_hard", "csp")]
    sat_16 = size_rows[(16, "sat")]
    dlx_16 = size_rows[(16, "dlx")]
    sat_25 = size_rows[(25, "sat")]
    dlx_25 = size_rows[(25, "dlx")]
    rows_36_easy = [
        row for (case, _), row in case_rows.items() if case == "36x36_easy"
    ]
    rows_36_medium = [
        row for (case, _), row in case_rows.items() if case == "36x36_medium"
    ]
    rows_36_hard = [
        row for (case, _), row in case_rows.items() if case == "36x36_hard"
    ]

    return "\n".join(
        [
            "| Size | Headline result |",
            "|---:|:---|",
            (
                "| 9×9 | Naive was fastest with many clues at "
                f"{_milliseconds(naive_9_easy)} median; CSP solved "
                f"{csp_9_hard['solved']}/{csp_9_hard['tested']} low-clue puzzles "
                f"at {_milliseconds(csp_9_hard)} median. |"
            ),
            (
                f"| 16×16 | SAT solved {sat_16['solved']}/{sat_16['tested']}; "
                f"DLX solved {dlx_16['solved']}/{dlx_16['tested']}, and its median "
                f"successful run was {_milliseconds(dlx_16)}, compared with "
                f"{_milliseconds(sat_16)} for SAT. |"
            ),
            (
                f"| 25×25 | SAT solved {sat_25['solved']}/{sat_25['tested']}; "
                f"DLX solved {dlx_25['solved']}/{dlx_25['tested']}, and its median "
                f"successful run was {_milliseconds(dlx_25)}, compared with "
                f"{_milliseconds(sat_25)} for SAT. |"
            ),
            (
                "| 36×36 | Across all six solvers: high-clue "
                f"{_solved_fraction(rows_36_easy)}, mid-clue "
                f"{_solved_fraction(rows_36_medium)}, and low-clue "
                f"{_solved_fraction(rows_36_hard)} "
                f"({_sum_field(rows_36_hard, 'timeouts')} timeouts). |"
            ),
        ]
    ) + "\n"


def render_readme_results(
    size_summary_path: str | Path = DEFAULT_SIZE_SUMMARY,
) -> str:
    rows = _read_csv(size_summary_path)
    return "\n".join(
        [
            "| Size | Solver | Solved | Timeouts | Median successful run | Mean successful run |",
            "|---:|:---|---:|---:|---:|---:|",
            *[
                f"| {row['size']}×{row['size']} | {_solver_label(row['solver'])} | "
                f"{row['solved']}/{row['tested']} | {row['timeouts']} | "
                f"{_milliseconds(row, 'median_runtime_s')} | "
                f"{_milliseconds(row, 'avg_runtime_s')} |"
                for row in rows
            ],
        ]
    ) + "\n"


def _embedded_block(
    path: Path,
    start_marker: str,
    end_marker: str,
    description: str,
) -> str:
    text = path.read_text(encoding="utf-8")
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError(f"{path.name} must contain one {description} marker pair.")
    return text.split(start_marker, 1)[1].split(end_marker, 1)[0].strip()


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def _milliseconds(
    row: dict[str, str],
    field: str = "median_runtime_s",
) -> str:
    return f"{float(row[field]) * 1000:.3f} ms"


def _solver_label(name: str) -> str:
    return {
        "naive": "Naive",
        "naive_recursive": "Naive recursive",
        "csp": "CSP",
        "sat": "SAT",
        "smt": "SMT",
        "dlx": "DLX",
    }.get(name, name)


def _sum_field(rows: list[dict[str, str]], field: str) -> int:
    return sum(int(row[field]) for row in rows)


def _solved_fraction(rows: list[dict[str, str]]) -> str:
    return f"{_sum_field(rows, 'solved')}/{_sum_field(rows, 'tested')}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--size-summary", type=Path, default=DEFAULT_SIZE_SUMMARY)
    parser.add_argument("--case-summary", type=Path, default=DEFAULT_CASE_SUMMARY)
    args = parser.parse_args()
    verify_readme_highlights(args.readme, args.size_summary, args.case_summary)
    verify_readme_results(args.readme, args.size_summary)
    verify_readme_tables(args.benchmark, args.tables)
    print("README highlights/results and BENCHMARK tables match the saved data.")


if __name__ == "__main__":
    main()
