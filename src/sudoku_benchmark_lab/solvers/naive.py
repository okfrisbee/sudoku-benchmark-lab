import time

from sudoku_benchmark_lab.board import board_size, format_board, parse_board
from sudoku_benchmark_lab.solvers.result import SolverResult


def solve_naive(board: str | list[int]) -> SolverResult:
    start = time.perf_counter()
    recursive_calls = 0
    assignments = 0
    backtracks = 0

    def failed(error: str) -> SolverResult:
        return SolverResult(
            solution=None,
            status="failed",
            runtime_seconds=time.perf_counter() - start,
            backtracks=backtracks,
            assignments=assignments,
            recursive_calls=recursive_calls,
            error=error,
        )

    try:
        cells = parse_board(board)
        n, box = board_size(cells)
        if n <= 0:
            return failed("Board must contain at least one cell.")
    except ValueError as exc:
        return failed(str(exc))

    def valid_group(values: list[int]) -> bool:
        seen = set()
        for value in values:
            if value == 0:
                continue
            if value in seen:
                return False
            seen.add(value)
        return True

    for row in range(n):
        if not valid_group(cells[row * n : (row + 1) * n]):
            return failed("Invalid board state.")

    for col in range(n):
        if not valid_group([cells[row * n + col] for row in range(n)]):
            return failed("Invalid board state.")

    for box_row in range(0, n, box):
        for box_col in range(0, n, box):
            values = [
                cells[row * n + col]
                for row in range(box_row, box_row + box)
                for col in range(box_col, box_col + box)
            ]
            if not valid_group(values):
                return failed("Invalid board state.")

    row_values = [set() for _ in range(n)]
    col_values = [set() for _ in range(n)]
    box_values = [set() for _ in range(n)]
    empty_cells = []

    for index, value in enumerate(cells):
        row, col = divmod(index, n)
        box_index = (row // box) * box + (col // box)
        if value == 0:
            empty_cells.append(index)
            continue

        row_values[row].add(value)
        col_values[col].add(value)
        box_values[box_index].add(value)

    def is_valid(index: int, value: int) -> bool:
        row, col = divmod(index, n)
        box_index = (row // box) * box + (col // box)
        return (
            value not in row_values[row]
            and value not in col_values[col]
            and value not in box_values[box_index]
        )

    def place(index: int, value: int) -> None:
        row, col = divmod(index, n)
        box_index = (row // box) * box + (col // box)
        cells[index] = value
        row_values[row].add(value)
        col_values[col].add(value)
        box_values[box_index].add(value)

    def remove(index: int, value: int) -> None:
        row, col = divmod(index, n)
        box_index = (row // box) * box + (col // box)
        cells[index] = 0
        row_values[row].remove(value)
        col_values[col].remove(value)
        box_values[box_index].remove(value)

    def backtrack() -> bool:
        nonlocal recursive_calls, assignments, backtracks
        if not empty_cells:
            recursive_calls += 1
            return True

        depth = 0

        while 0 <= depth < len(empty_cells):
            recursive_calls += 1
            index = empty_cells[depth]
            current = cells[index]
            start_value = 1

            if current != 0:
                remove(index, current)
                start_value = current + 1

            for value in range(start_value, n + 1):
                if not is_valid(index, value):
                    continue

                place(index, value)
                assignments += 1
                depth += 1
                break
            else:
                backtracks += 1
                depth -= 1

        return depth == len(empty_cells)

    solved = backtrack()
    return SolverResult(
        solution=format_board(cells) if solved else None,
        status="solved" if solved else "failed",
        runtime_seconds=time.perf_counter() - start,
        backtracks=backtracks,
        assignments=assignments,
        recursive_calls=recursive_calls,
    )
