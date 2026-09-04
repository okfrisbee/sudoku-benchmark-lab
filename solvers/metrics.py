from dataclasses import dataclass
from typing import Literal

from board_utils import board_size, parse_board


SolverStatus = Literal["solved", "failed", "error", "timeout"]


@dataclass
class SolverResult:
    solution: str | None
    status: SolverStatus
    runtime_seconds: float
    setup_seconds: float | None = None
    solve_seconds: float | None = None
    backtracks: int | None = None
    assignments: int | None = None
    recursive_calls: int | None = None
    error: str | None = None

    @property
    def solved(self) -> bool:
        return self.status == "solved" and self.solution is not None


def validate_solution(
    puzzle: str | list[int],
    solution: str | list[int],
) -> tuple[bool, str | None]:
    try:
        puzzle_values = parse_board(puzzle)
        solution_values = parse_board(solution)
    except ValueError as exc:
        return False, str(exc)

    if len(puzzle_values) != len(solution_values):
        return False, "Solution size does not match puzzle size."

    size, box = board_size(puzzle_values)
    expected = set(range(1, size + 1))

    for index, given in enumerate(puzzle_values):
        if given != 0 and solution_values[index] != given:
            return False, "Solution does not preserve puzzle givens."

    for value in solution_values:
        if value not in expected:
            return False, f"Solution contains value outside 1..{size}."

    for row in range(size):
        values = solution_values[row * size : (row + 1) * size]
        if set(values) != expected:
            return False, "Solution has an invalid row."

    for col in range(size):
        values = [solution_values[row * size + col] for row in range(size)]
        if set(values) != expected:
            return False, "Solution has an invalid column."

    for box_row in range(0, size, box):
        for box_col in range(0, size, box):
            values = [
                solution_values[row * size + col]
                for row in range(box_row, box_row + box)
                for col in range(box_col, box_col + box)
            ]
            if set(values) != expected:
                return False, "Solution has an invalid box."

    return True, None
