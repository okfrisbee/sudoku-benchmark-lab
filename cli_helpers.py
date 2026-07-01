import json
from pathlib import Path
from typing import Any

from board_utils import validate_size
from config import load_config


def prompt_choice(title, options):
    print(title)
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")

    choice = input().strip()
    if not choice.isdigit():
        return None

    index = int(choice)
    if index < 1 or index > len(options):
        return None
    return options[index - 1]


def prompt_difficulty(difficulties):
    selected = prompt_choice(
        "\nSelect difficulty:",
        list(difficulties),
    )
    if selected is None:
        print("Invalid difficulty.")
    return selected


def list_datasets(size: int | None = None) -> list[Path]:
    if size is not None:
        validate_size(size)
    directory = Path(load_config()["paths"]["datasets_dir"])
    if not directory.exists():
        return []
    pattern = f"{size}x{size}_*.jsonl" if size is not None else "*.jsonl"
    return sorted(directory.glob(pattern))


def read_dataset(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def select_dataset(size: int | None = None):
    datasets = list_datasets(size)
    if not datasets:
        size_label = f" for {size}x{size}" if size is not None else ""
        print(f"\nNo datasets found{size_label}. Generate a dataset first.")
        return None

    options = [path.name for path in datasets]
    selected = prompt_choice("\nAvailable datasets:", options)
    if selected is None:
        print("Invalid dataset.")
        return None

    return datasets[options.index(selected)]


def prompt_size():
    print("\nEnter puzzle size:")
    value = input().strip()
    if not value.isdigit():
        print("Invalid size.")
        return None

    size = int(value)
    try:
        validate_size(size)
    except ValueError:
        print("Invalid size.")
        return None
    return size


def prompt_positive_int(message):
    print(message)
    value = input().strip()
    if not value.isdigit() or int(value) <= 0:
        print("Invalid count.")
        return None
    return int(value)
