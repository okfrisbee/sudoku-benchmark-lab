import time

from z3 import And, Distinct, Int, Solver, sat, unsat

from sudoku_benchmark_lab.board import board_size, format_board, parse_board
from sudoku_benchmark_lab.solvers.result import SolverResult


def build_z3_sudoku_solver(board):
    values = parse_board(board)
    n, box = board_size(values)

    if n <= 0:
        raise ValueError("Board must contain at least one cell")

    solver = Solver()
    cells = [[Int(f"cell_{r}_{c}") for c in range(n)] for r in range(n)]

    for r in range(n):
        for c in range(n):
            solver.add(And(cells[r][c] >= 1, cells[r][c] <= n))

    for r in range(n):
        solver.add(Distinct(cells[r]))

    for c in range(n):
        solver.add(Distinct([cells[r][c] for r in range(n)]))

    for br in range(0, n, box):
        for bc in range(0, n, box):
            solver.add(
                Distinct(
                    [
                        cells[r][c]
                        for r in range(br, br + box)
                        for c in range(bc, bc + box)
                    ]
                )
            )

    for index, value in enumerate(values):
        if value != 0:
            r, c = divmod(index, n)
            solver.add(cells[r][c] == value)

    return solver, cells, values, n, box



def solve_smt(board: str | list[int]) -> SolverResult:
    start = time.perf_counter()
    setup_seconds = None
    solve_seconds = None

    try:
        setup_start = time.perf_counter()
        solver, cells, _values, n, _box = build_z3_sudoku_solver(board)
        setup_seconds = time.perf_counter() - setup_start

        solve_start = time.perf_counter()
        check_result = solver.check()
        solve_seconds = time.perf_counter() - solve_start

        if check_result == unsat:
            return SolverResult(
                solution=None,
                status="failed",
                runtime_seconds=time.perf_counter() - start,
                setup_seconds=setup_seconds,
                solve_seconds=solve_seconds,
                error="Sudoku is UNSAT.",
            )
        if check_result != sat:
            return SolverResult(
                solution=None,
                status="error",
                runtime_seconds=time.perf_counter() - start,
                setup_seconds=setup_seconds,
                solve_seconds=solve_seconds,
                error=f"Z3 returned {check_result}: {solver.reason_unknown()}",
            )

        model = solver.model()
        solved = [model[cells[r][c]].as_long() for r in range(n) for c in range(n)]
        return SolverResult(
            solution=format_board(solved),
            status="solved",
            runtime_seconds=time.perf_counter() - start,
            setup_seconds=setup_seconds,
            solve_seconds=solve_seconds,
        )
    except ValueError as exc:
        return SolverResult(
            solution=None,
            status="failed",
            runtime_seconds=time.perf_counter() - start,
            setup_seconds=setup_seconds,
            solve_seconds=solve_seconds,
            error=str(exc),
        )
    except Exception as exc:
        return SolverResult(
            solution=None,
            status="error",
            runtime_seconds=time.perf_counter() - start,
            setup_seconds=setup_seconds,
            solve_seconds=solve_seconds,
            error=str(exc),
        )
