import random
import unittest

from sudoku_benchmark_lab.board import parse_board
from sudoku_benchmark_lab.datasets.generation import (
    clue_count, clue_ranges, expand_difficulties, generate_dataset_records,
    generate_pattern_solution, generate_puzzle,
)
from sudoku_benchmark_lab.validation import validate_solution


class GenerationTests(unittest.TestCase):
    def test_pattern_solution_is_valid(self):
        for size in (4, 9, 16, 25, 36):
            with self.subTest(size=size):
                board = generate_pattern_solution(size, seed=123)
                self.assertEqual(len(parse_board(board)), size * size)
                self.assertTrue(validate_solution(board, board)[0])

    def test_seeded_generation_and_clue_counts(self):
        for difficulty, (low, high) in clue_ranges().items():
            count, percent = clue_count(9, difficulty, random.Random(123))
            self.assertTrue(low <= percent <= high)
            self.assertEqual(count, round(81 * percent))
        first = generate_dataset_records(9, "mixed", 5, seed=123)
        self.assertEqual(first, generate_dataset_records(9, "mixed", 5, seed=123))
        self.assertEqual(expand_difficulties("mixed", 5), ["easy", "easy", "medium", "medium", "hard"])
        for record in first:
            self.assertNotIn("verification_mode", record)
            self.assertNotIn("unique", record)
            self.assertTrue(validate_solution(record["puzzle"], record["solution"])[0])

    def test_requested_clues(self):
        puzzle = generate_puzzle(size=4, clues=6, seed=123)
        self.assertEqual(puzzle.actual_clues, 6)
        self.assertTrue(validate_solution(puzzle.puzzle, puzzle.solution)[0])


if __name__ == "__main__":
    unittest.main()
