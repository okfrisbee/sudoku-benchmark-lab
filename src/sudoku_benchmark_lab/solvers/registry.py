"""Explicit Sudoku solver names, labels, and lazy imports."""

from collections.abc import Callable
from importlib import import_module

from .result import SolverResult

Solver = Callable[[str | list[int]], SolverResult]

# Lazy imports let generation and pure Python solvers work without SAT/SMT extras.
SOLVERS = {
    "naive": ("naive", "solve_naive", "Naive"),
    "naive_recursive": ("naive_recursive", "solve_naive_recursive", "Naive recursive"),
    "csp": ("csp", "solve_csp", "CSP"),
    "sat": ("sat", "solve_sudoku", "SAT"),
    "smt": ("smt", "solve_smt", "SMT"),
    "dlx": ("dlx", "solve_dlx", "DLX"),
}


def get_solver(name: str) -> Solver:
    if name not in SOLVERS:
        raise ValueError(f"Unknown solver: {name}")
    module, function, _label = SOLVERS[name]
    return getattr(import_module(f"sudoku_benchmark_lab.solvers.{module}"), function)


def solver_label(name: str) -> str:
    return SOLVERS[name][2] if name in SOLVERS else name
