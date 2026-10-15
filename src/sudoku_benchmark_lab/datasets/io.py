"""JSONL dataset storage; legacy record fields are accepted as-is."""

import json
from pathlib import Path
from typing import Any

from sudoku_benchmark_lab.board import board_size, parse_board
from sudoku_benchmark_lab.config import load_config


def read_dataset(path: str | Path) -> list[dict[str, Any]]:
    records = []
    with Path(path).open(encoding="utf-8") as source:
        for number, line in enumerate(source, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or "puzzle" not in record:
                raise ValueError(f"Dataset record {number} has no puzzle")
            size, _box = board_size(parse_board(record["puzzle"]))
            if "size" in record and record["size"] != size:
                raise ValueError(f"Dataset record {number} has mismatched size")
            records.append(record)
    return records


def write_dataset_records(records: list[dict[str, Any]], size: int, difficulty: str) -> Path:
    from .generation import dataset_path

    path = dataset_path(size, difficulty, len(records))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for record in records:
            if board_size(parse_board(record["puzzle"]))[0] != size:
                raise ValueError("Dataset record size does not match requested size")
            output.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def list_datasets(size: int | None = None) -> list[Path]:
    from sudoku_benchmark_lab.board import validate_size

    if size is not None:
        validate_size(size)
    directory = Path(load_config()["paths"]["datasets_dir"])
    pattern = f"{size}x{size}_*.jsonl" if size is not None else "*.jsonl"
    return sorted(directory.glob(pattern)) if directory.exists() else []
