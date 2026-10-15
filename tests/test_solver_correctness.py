import importlib
import unittest

from sudoku_benchmark_lab.solvers.csp import CSPSolver, solve_csp
from sudoku_benchmark_lab.solvers.dlx import solve_dlx
from sudoku_benchmark_lab.validation import validate_solution
from sudoku_benchmark_lab.solvers.naive_iterative import solve_naive_iterative
from sudoku_benchmark_lab.solvers.naive_recursive import solve_naive_recursive


SOLVED_4X4 = "1 2 3 4 3 4 1 2 2 1 4 3 4 3 2 1"
PUZZLE_4X4 = "1 0 3 0 0 4 0 2 2 0 4 0 0 3 0 1"
UNSAT_4X4 = [1, 2, 3, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0]
INVALID_4X4 = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def optional_solver(module_name, function_name):
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    return getattr(module, function_name)


SOLVERS = [
    ("naive_iterative", solve_naive_iterative),
    ("naive_recursive", solve_naive_recursive),
    ("csp", solve_csp),
    ("dlx", solve_dlx),
    ("sat", optional_solver("sudoku_benchmark_lab.solvers.sat", "solve_sudoku")),
    ("smt", optional_solver("sudoku_benchmark_lab.solvers.smt", "solve_smt")),
]


class SolverCorrectnessTests(unittest.TestCase):
    def test_solvers_return_valid_4x4_solution(self):
        for name, solver in SOLVERS:
            with self.subTest(solver=name):
                if solver is None:
                    self.skipTest(f"{name} dependencies are not installed")
                result = solver(PUZZLE_4X4)

                self.assertTrue(result.solved, result.error)
                valid, error = validate_solution(PUZZLE_4X4, result.solution)
                self.assertTrue(valid, error)

    def test_solvers_accept_completed_valid_board(self):
        for name, solver in SOLVERS:
            with self.subTest(solver=name):
                if solver is None:
                    self.skipTest(f"{name} dependencies are not installed")
                result = solver(SOLVED_4X4)

                self.assertTrue(result.solved, result.error)
                self.assertEqual(result.solution, SOLVED_4X4)

    def test_solvers_reject_duplicate_givens(self):
        for name, solver in SOLVERS:
            with self.subTest(solver=name):
                if solver is None:
                    self.skipTest(f"{name} dependencies are not installed")
                result = solver(INVALID_4X4)

                self.assertEqual(result.status, "failed")

    def test_solvers_report_valid_unsat_board_as_failed(self):
        for name, solver in SOLVERS:
            with self.subTest(solver=name):
                if solver is None:
                    self.skipTest(f"{name} dependencies are not installed")
                result = solver(UNSAT_4X4)

                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.solution)

    def test_csp_naked_pairs_find_pair_when_other_two_candidate_cells_exist(self):
        solver = CSPSolver([0] * 81)
        house = solver.rows[0]
        for cell in house:
            solver.candidates[cell] = set(range(1, 10))

        solver.candidates[house[0]] = {1, 2}
        solver.candidates[house[1]] = {1, 2}
        solver.candidates[house[2]] = {3, 4}
        solver.candidates[house[3]] = {1, 2, 5}

        eliminated, valid = solver.find_naked_pairs()

        self.assertTrue(valid)
        self.assertGreater(eliminated, 0)
        self.assertEqual(solver.candidates[house[3]], {5})

    def test_naive_handles_completed_36x36_without_recursion_error(self):
        size = 36
        box = 6
        solved = [
            ((row * box + row // box + col) % size) + 1
            for row in range(size)
            for col in range(size)
        ]

        result = solve_naive_iterative(solved)

        self.assertTrue(result.solved, result.error)
        self.assertEqual(result.solution, " ".join(map(str, solved)))


if __name__ == "__main__":
    unittest.main()
