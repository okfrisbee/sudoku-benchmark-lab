import multiprocessing
import queue
import time

from sudoku_benchmark_lab.config import load_config
from sudoku_benchmark_lab.board import board_size, parse_board
from sudoku_benchmark_lab.datasets.io import read_dataset
from .reporting import (
    results_dataframe,
)

from sudoku_benchmark_lab.solvers.registry import SOLVERS, canonical_solver_name, get_solver
from sudoku_benchmark_lab.solvers.result import SolverResult
from sudoku_benchmark_lab.validation import validate_solution


def _run_solver_process(solver_fn, puzzle, result_queue):
    result_queue.put(solver_fn(puzzle))


def solve_with_timeout(
    solver_fn,
    puzzle,
    timeout_seconds=None,
) -> SolverResult:
    if timeout_seconds is None:
        timeout_seconds = load_config()["benchmark"]["solver_timeout_seconds"]
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    start = time.perf_counter()
    context_name = "fork" if "fork" in multiprocessing.get_all_start_methods() else None
    context = multiprocessing.get_context(context_name)
    result_queue = context.Queue(maxsize=1)
    process = context.Process(
        target=_run_solver_process,
        args=(solver_fn, puzzle, result_queue),
    )

    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        return SolverResult(
            solution=None,
            status="timeout",
            # A timeout is a censored observation: the solver consumed its
            # whole allowance, while the extra parent-side termination time is
            # harness overhead rather than solver runtime.
            runtime_seconds=float(timeout_seconds),
            error=f"Timed out after {timeout_seconds} seconds.",
        )

    try:
        # A multiprocessing.Queue uses a feeder thread.  The process may have
        # exited just before that thread makes the result visible to the
        # parent, so a non-blocking read can incorrectly report a crash.
        return result_queue.get(timeout=0.1)
    except queue.Empty:
        return SolverResult(
            solution=None,
            status="error",
            runtime_seconds=time.perf_counter() - start,
            error=f"Solver process exited with code {process.exitcode} without a result.",
        )


def _csv_row(size, puzzle_index, solver_name, result, record, timeout_seconds):
    return {
        "puzzle_index": puzzle_index,
        "solver_name": solver_name,
        "result": result,
        "metadata": {
            "size": size,
            "difficulty": record.get("difficulty", ""),
            "clue_percent": record.get("clue_percent", ""),
            "clues": record.get("actual_clues", ""),
            "puzzle_id": record.get("id", puzzle_index),
            "puzzle_seed": record.get("seed", ""),
            "timeout_seconds": timeout_seconds,
        },
    }


def validate_solver_result(puzzle, result: SolverResult) -> SolverResult:
    if not result.solved:
        return result

    valid, error = validate_solution(puzzle, result.solution)
    if valid:
        return result

    return SolverResult(
        solution=result.solution,
        status="error",
        runtime_seconds=result.runtime_seconds,
        setup_seconds=result.setup_seconds,
        solve_seconds=result.solve_seconds,
        backtracks=result.backtracks,
        assignments=result.assignments,
        recursive_calls=result.recursive_calls,
        error=f"Invalid solver solution: {error}",
    )


def benchmark_dataset(
    dataset_path,
    size=None,
    solver_names=None,
    timeout_seconds=None,
    progress=None,
):
    if timeout_seconds is None:
        timeout_seconds = load_config()["benchmark"]["solver_timeout_seconds"]
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    records = read_dataset(dataset_path)
    if not records:
        raise ValueError("Dataset has no puzzles")

    names = list(SOLVERS) if solver_names is None else [
        canonical_solver_name(name) for name in solver_names
    ]
    if not names or len(set(names)) != len(names):
        raise ValueError("Select at least one distinct solver")
    unknown = set(names) - SOLVERS.keys()
    if unknown:
        raise ValueError(f"Unknown solver(s): {', '.join(sorted(unknown))}")
    solvers = {name: get_solver(name) for name in names}

    csv_rows = []
    tested = 0

    for i, record in enumerate(records, start=1):
        puzzle = record["puzzle"]
        actual_size, _box = board_size(parse_board(puzzle))
        if size is not None and size != actual_size:
            raise ValueError(f"Dataset puzzle {i} has size {actual_size}, expected {size}")
        row_parts = [f"{i}:"]
        for name, fn in solvers.items():
            result = solve_with_timeout(
                fn,
                puzzle,
                timeout_seconds=timeout_seconds,
            )
            result = validate_solver_result(puzzle, result)
            csv_rows.append(
                _csv_row(actual_size, i, name, result, record, timeout_seconds)
            )

            if result.solved:
                row_parts.append(f"{name}={result.runtime_seconds:.4f}s")
            else:
                row_parts.append(f"{name}={result.status.upper()}")

        tested += 1
        if progress is not None:
            progress(" | ".join(row_parts))

    return results_dataframe(csv_rows)
