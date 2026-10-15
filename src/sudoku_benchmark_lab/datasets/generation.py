from dataclasses import dataclass
from pathlib import Path
import random
import re

from sudoku_benchmark_lab.board import format_board, parse_board, validate_size
from sudoku_benchmark_lab.config import load_config


def clue_ranges() -> dict[str, tuple[float, float]]:
    return load_config()["generation"]["clue_percent_ranges"]


def difficulties() -> tuple[str, ...]:
    return (*clue_ranges(), "mixed")


@dataclass
class GeneratedPuzzle:
    puzzle: str
    solution: str
    size: int
    box_size: int
    target_clues: int
    actual_clues: int


def generate_pattern_solution(size: int = 9, seed: int | None = None) -> str:
    n, box = validate_size(size)
    rng = random.Random(seed)

    def pattern(row: int, col: int) -> int:
        return (box * (row % box) + row // box + col) % n

    def shuffled_groups() -> list[int]:
        groups = list(range(box))
        rng.shuffle(groups)
        indexes = []
        for group in groups:
            members = list(range(group * box, (group + 1) * box))
            rng.shuffle(members)
            indexes.extend(members)
        return indexes

    rows = shuffled_groups()
    cols = shuffled_groups()
    digits = list(range(1, n + 1))
    rng.shuffle(digits)

    values = [digits[pattern(row, col)] for row in rows for col in cols]
    return format_board(values)


def generate_puzzle(
    size: int = 9,
    clues: int | None = None,
    seed: int | None = None,
) -> GeneratedPuzzle:
    n, box = validate_size(size)

    if clues is None:
        clues = max(n, round(n * n * 0.4))
    if not (0 <= clues <= n * n):
        raise ValueError(f"Clues must be in range 0..{n * n}")

    solution = generate_pattern_solution(n, seed=seed)
    puzzle_values = parse_board(solution)
    indexes = list(range(n * n))
    random.Random(seed).shuffle(indexes)

    for index in indexes[: n * n - clues]:
        puzzle_values[index] = 0

    return GeneratedPuzzle(
        puzzle=format_board(puzzle_values),
        solution=solution,
        size=n,
        box_size=box,
        target_clues=clues,
        actual_clues=sum(1 for value in puzzle_values if value != 0),
    )


def random_clue_percent(difficulty: str, rng: random.Random) -> float:
    ranges = clue_ranges()
    if difficulty not in ranges:
        raise ValueError(f"Unsupported difficulty: {difficulty}")
    low, high = ranges[difficulty]
    return rng.uniform(low, high)


def clue_count(size: int, difficulty: str, rng: random.Random) -> tuple[int, float]:
    clue_percent = random_clue_percent(difficulty, rng)
    return round(size * size * clue_percent), clue_percent


def expand_difficulties(difficulty: str, count: int) -> list[str]:
    ranges = clue_ranges()
    if difficulty not in difficulties():
        raise ValueError(f"Unsupported difficulty: {difficulty}")
    if count <= 0:
        raise ValueError("Count must be positive")
    if difficulty != "mixed":
        return [difficulty] * count

    base, remainder = divmod(count, len(ranges))
    expanded: list[str] = []
    for name in ranges:
        expanded.extend([name] * (base + (1 if remainder > 0 else 0)))
        remainder -= 1
    return expanded


def dataset_path(
    size: int,
    difficulty: str,
    count: int,
) -> Path:
    validate_size(size)
    if difficulty not in difficulties():
        raise ValueError(f"Unsupported difficulty: {difficulty}")
    if count < 0:
        raise ValueError("Count cannot be negative")
    return (
        Path(load_config()["paths"]["datasets_dir"])
        / f"{size}x{size}_{difficulty}_{count}.jsonl"
    )


def dataset_size_from_path(path: str | Path) -> int:
    match = re.match(r"^(\d+)x\1_", Path(path).name)
    if not match:
        raise ValueError(f"Cannot determine dataset size from filename: {path}")
    return int(match.group(1))


def generate_dataset_records(
    size: int,
    difficulty: str,
    count: int,
    seed: int | None = None,
):
    validate_size(size)
    rng = random.Random(seed)
    records = []

    for index, actual_difficulty in enumerate(
        expand_difficulties(difficulty, count), start=1
    ):
        puzzle_seed = rng.randrange(2**63)
        target_clues, clue_percent = clue_count(size, actual_difficulty, rng)

        generated = generate_puzzle(
            size=size,
            clues=target_clues,
            seed=puzzle_seed,
        )

        records.append(
            {
                "id": index,
                "size": size,
                "difficulty": actual_difficulty,
                "clue_percent": clue_percent,
                "target_clues": target_clues,
                "actual_clues": generated.actual_clues,
                "puzzle": generated.puzzle,
                "solution": generated.solution,
                "seed": puzzle_seed,
            }
        )

    return records


def generate_dataset(
    size: int,
    difficulty: str,
    count: int,
    seed: int | None = None,
) -> Path:
    from .io import write_dataset_records

    records = generate_dataset_records(size, difficulty, count, seed=seed)
    return write_dataset_records(records, size, difficulty)
