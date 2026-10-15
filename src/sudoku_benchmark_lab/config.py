"""Project settings and validation for Sudoku Benchmark Lab."""

from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = (
    PROJECT_ROOT
    if (PROJECT_ROOT / "pyproject.toml").exists()
    else Path.cwd()
)

# Keep the complete application configuration here so source and installed
# runs use the same defaults without depending on a working-directory file.
DEFAULT_CONFIG: dict[str, Any] = {
    "paths": {
        "datasets_dir": str(DATA_ROOT / "data" / "datasets"),
        "benchmark_results_dir": str(DATA_ROOT / "data" / "results"),
    },
    "generation": {
        "clue_percent_ranges": {
            "easy": (0.75, 0.85),
            "medium": (0.50, 0.60),
            "hard": (0.25, 0.35),
        },
    },
    "benchmark": {"solver_timeout_seconds": 60.0},
}


def load_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a validated copy of the defaults, with optional nested overrides."""
    config = deepcopy(DEFAULT_CONFIG)
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise ValueError("Config overrides must be a mapping")
        _merge(config, overrides)
    _validate(config)
    return config


def _merge(target: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if key not in target:
            raise ValueError(f"Unknown config setting: {key}")
        if isinstance(target[key], dict) and isinstance(value, dict):
            _merge(target[key], value)
        elif isinstance(target[key], dict) != isinstance(value, dict):
            raise ValueError(f"Config setting '{key}' has the wrong type")
        else:
            target[key] = value


def _validate(config: dict[str, Any]) -> None:
    paths = _table(config, "paths")
    paths["datasets_dir"] = _non_empty_string(paths, "datasets_dir")
    paths["benchmark_results_dir"] = _non_empty_string(paths, "benchmark_results_dir")

    generation = _table(config, "generation")
    ranges = _table(generation, "clue_percent_ranges")
    if not ranges:
        raise ValueError("clue_percent_ranges must define at least one range")
    validated = {}
    for name, bounds in ranges.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(bounds, (tuple, list)) or len(bounds) != 2 or not all(_is_number(v) for v in bounds):
            raise ValueError(f"Clue percent range for {name!r} must be two numbers")
        low, high = float(bounds[0]), float(bounds[1])
        if not 0.0 <= low <= high <= 1.0:
            raise ValueError(f"Clue percent range for {name!r} must satisfy 0 <= low <= high <= 1")
        validated[name] = (low, high)
    generation["clue_percent_ranges"] = validated

    benchmark = _table(config, "benchmark")
    timeout = benchmark.get("solver_timeout_seconds")
    if not _is_number(timeout) or timeout <= 0:
        raise ValueError("solver_timeout_seconds must be a positive number")
    benchmark["solver_timeout_seconds"] = float(timeout)


def _table(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Config key '{key}' must be a mapping")
    return value


def _non_empty_string(config: dict[str, Any], key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Config key '{key}' must be a non-empty string")
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
