import time

from board_utils import board_size, format_board, parse_board
from solvers.metrics import SolverResult


def solve_naive_recursive(board: str | list[int]) -> SolverResult:
    start = time.perf_counter()
    recursive_calls = 0
    assignments = 0
    backtracks = 0

    try:
        cells = parse_board(board)
        size, box_size = board_size(cells)
    except ValueError as exc:
        return SolverResult(
            solution=None,
            status="failed",
            runtime_seconds=time.perf_counter() - start,
            error=str(exc),
        )

    def is_valid(index: int, value: int) -> bool:
        row, col = divmod(index, size)

        if value in cells[row * size : (row + 1) * size]:
            return False
        if any(cells[r * size + col] == value for r in range(size)):
            return False

        box_row = (row // box_size) * box_size
        box_col = (col // box_size) * box_size
        return all(
            cells[r * size + c] != value
            for r in range(box_row, box_row + box_size)
            for c in range(box_col, box_col + box_size)
        )

    # Validate the clues before solving.
    for index, value in enumerate(cells):
        if value == 0:
            continue
        cells[index] = 0
        valid = is_valid(index, value)
        cells[index] = value
        if not valid:
            return SolverResult(
                solution=None,
                status="failed",
                runtime_seconds=time.perf_counter() - start,
                error="Invalid board state.",
            )

    def backtrack() -> bool:
        nonlocal recursive_calls, assignments, backtracks
        recursive_calls += 1

        try:
            index = cells.index(0)
        except ValueError:
            return True

        for value in range(1, size + 1):
            if not is_valid(index, value):
                continue

            cells[index] = value
            assignments += 1

            if backtrack():
                return True

            cells[index] = 0
            backtracks += 1

        return False

    solved = backtrack()
    return SolverResult(
        solution=format_board(cells) if solved else None,
        status="solved" if solved else "failed",
        runtime_seconds=time.perf_counter() - start,
        backtracks=backtracks,
        assignments=assignments,
        recursive_calls=recursive_calls,
    )
