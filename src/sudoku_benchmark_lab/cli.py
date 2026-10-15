"""Interactive Sudoku commands; core modules never prompt for input."""

import time

from sudoku_benchmark_lab.board import print_board, validate_size
from sudoku_benchmark_lab.benchmark.reporting import (
    print_summary_table, result_paths, summary_dataframe, write_csv,
)
from sudoku_benchmark_lab.benchmark.runner import benchmark_dataset, solve_with_timeout
from sudoku_benchmark_lab.benchmark.visualization import visualization_data, visualize_benchmark
from sudoku_benchmark_lab.datasets.generation import difficulties, generate_dataset
from sudoku_benchmark_lab.datasets.io import list_datasets
from sudoku_benchmark_lab.solvers.csp import solve_csp
from sudoku_benchmark_lab.solvers.registry import SOLVERS
from sudoku_benchmark_lab.validation import validate_solution


def prompt_choice(title, options):
    print(title)
    for index, option in enumerate(options, 1):
        print(f"{index}. {option}")
    choice = input().strip()
    return options[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(options) else None


def prompt_size():
    value = input("\nEnter puzzle size: ").strip()
    try:
        size = int(value)
        validate_size(size)
        return size
    except ValueError:
        print("Invalid size.")
        return None


def generate_menu():
    size = prompt_size()
    if size is None:
        return
    difficulty = prompt_choice("\nSelect clue level:", difficulties())
    if difficulty is None:
        print("Invalid clue level.")
        return
    value = input("\nHow many puzzles should be generated? ").strip()
    if not value.isdigit() or int(value) <= 0:
        print("Invalid count.")
        return
    started = time.perf_counter()
    path = generate_dataset(size, difficulty, int(value))
    print(f"Dataset written to: {path}")
    print(f"Generation time: {time.perf_counter() - started:.4f}s")


def select_dataset():
    datasets = list_datasets()
    if not datasets:
        print("\nNo datasets found. Generate a dataset first.")
        return None
    selected = prompt_choice("\nAvailable datasets:", [path.name for path in datasets])
    return datasets[[path.name for path in datasets].index(selected)] if selected else None


def benchmark_menu():
    dataset = select_dataset()
    if dataset is None:
        return None
    choice = prompt_choice("\nSelect benchmark solver mode:", ["all", *SOLVERS])
    if choice is None:
        print("Invalid benchmark solver mode.")
        return None
    save = input("Save benchmark results and summary to CSV? (y/n): ").strip().lower() == "y"
    table = benchmark_dataset(dataset, solver_names=None if choice == "all" else [choice], progress=print)
    summary = summary_dataframe(table)
    print(f"\n-----Results-----\nPuzzles Tested: {table['puzzle_index'].nunique()}\n")
    print_summary_table(summary)
    if save:
        raw_path, summary_path = result_paths(dataset)
        write_csv(table, raw_path)
        write_csv(summary, summary_path)
        print(f"\nCSV written to: {raw_path}\nSummary CSV written to: {summary_path}")
    return table


def main():
    while True:
        print("\n-----Sudoku Menu-----\n1. Enter Puzzle\n2. Generate Dataset\n3. Benchmark\n4. Quit")
        choice = input().strip()
        if choice == "1":
            puzzle = input("\nEnter puzzle as one line: ").strip()
            result = solve_with_timeout(solve_csp, puzzle)
            if result.solved:
                result = result if validate_solution(puzzle, result.solution)[0] else None
            if result is not None and result.solved:
                print("\nSolved Board:")
                print_board(result.solution)
                print(f"Time Elapsed: {result.runtime_seconds:.4f}s")
            else:
                print("Puzzle was not solved.")
        elif choice == "2":
            generate_menu()
        elif choice == "3":
            table = benchmark_menu()
            if table is not None and not table.empty and input("\nVisualize data? (y/n): ").strip().lower() == "y":
                times, count, averages = visualization_data(table)
                show_naive = "naive" not in times or input("Show naive solver on graph? (y/n): ").strip().lower() == "y"
                visualize_benchmark(times, count, averages, show_naive=show_naive)
        elif choice == "4":
            return
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
