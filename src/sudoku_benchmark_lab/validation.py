"""Independently check solver answers before recording success."""

from sudoku_benchmark_lab.board import board_size, parse_board


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
