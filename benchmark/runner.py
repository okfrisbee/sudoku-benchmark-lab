"""Compatibility entry point for ``python -m benchmark.runner``."""

from sudoku_benchmark_lab.cli import benchmark_menu


if __name__ == "__main__":
    benchmark_menu()
