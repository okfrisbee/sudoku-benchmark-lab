from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from sudoku_benchmark_lab.config import DEFAULT_CONFIG


@contextmanager
def temporary_config(
    root: str | Path,
    datasets_dir: str | Path | None = None,
    benchmark_results_dir: str | Path | None = None,
    solver_timeout_seconds: float = 60,
    clue_percent_ranges: dict[str, tuple[float, float]] | None = None,
) -> Iterator[dict]:
    config = deepcopy(DEFAULT_CONFIG)
    root_path = Path(root)
    config["paths"]["datasets_dir"] = str(datasets_dir or root_path / "datasets")
    config["paths"]["benchmark_results_dir"] = str(benchmark_results_dir or root_path / "results")
    config["benchmark"]["solver_timeout_seconds"] = solver_timeout_seconds
    if clue_percent_ranges is not None:
        config["generation"]["clue_percent_ranges"] = clue_percent_ranges
    with patch("sudoku_benchmark_lab.config.DEFAULT_CONFIG", config):
        yield config
