from pathlib import Path
from typing import Any
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.toml"


def config_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path).resolve()
    return CONFIG_PATH if CONFIG_PATH.exists() else Path(__file__).with_name("default_config.toml")


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    source = config_path(path)
    if not source.exists():
        raise FileNotFoundError(f"Required config file not found: {source}")

    with source.open("rb") as config_file:
        config = tomllib.load(config_file)

    paths = _table(config, "paths")
    generation = _table(config, "generation")
    benchmark = _table(config, "benchmark")

    return {
        "paths": {
            "datasets_dir": str(_resolve_path(source, _non_empty_string(paths, "datasets_dir"))),
            "benchmark_results_dir": str(_resolve_path(source, _non_empty_string(paths, "benchmark_results_dir"))),
        },
        "generation": {
            "clue_percent_ranges": _clue_ranges(
                _table(generation, "clue_percent_ranges")
            ),
        },
        "benchmark": {
            "solver_timeout_seconds": _positive_number(
                benchmark,
                "solver_timeout_seconds",
            ),
        },
    }


def _resolve_path(source: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else source.parent / candidate


def _table(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Config key '{key}' must be a table.")
    return value


def _non_empty_string(config: dict[str, Any], key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Config key '{key}' must be a non-empty string.")
    return value


def _positive_number(config: dict[str, Any], key: str) -> float:
    value = config.get(key)
    if not _is_number(value) or value <= 0:
        raise ValueError(f"Config key '{key}' must be a positive number.")
    return float(value)


def _clue_ranges(ranges: dict[str, Any]) -> dict[str, tuple[float, float]]:
    if not ranges:
        raise ValueError("Config key 'clue_percent_ranges' must define at least one range.")

    validated = {}
    for difficulty, range_value in ranges.items():
        if (
            not isinstance(difficulty, str)
            or not difficulty.strip()
            or not isinstance(range_value, list)
            or len(range_value) != 2
            or not all(_is_number(value) for value in range_value)
        ):
            raise ValueError(
                f"Clue percent range for '{difficulty}' must be two numbers."
            )

        low, high = float(range_value[0]), float(range_value[1])
        if not 0.0 <= low <= high <= 1.0:
            raise ValueError(
                f"Clue percent range for '{difficulty}' must satisfy 0.0 <= low <= high <= 1.0."
            )
        validated[difficulty] = (low, high)

    return validated


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
