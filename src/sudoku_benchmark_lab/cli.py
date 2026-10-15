"""Interactive Sudoku commands; core modules never prompt for input."""

import time

from sudoku_benchmark_lab.board import print_board, validate_size
from sudoku_benchmark_lab.benchmark.reporting import (
    print_summary_table, result_path, summary_dataframe, write_csv,
)
from sudoku_benchmark_lab.benchmark.analysis import (
    PROJECT_ROOT,
    discover_result_csvs,
    summarize_result_csv,
)
from sudoku_benchmark_lab.benchmark.runner import benchmark_dataset, solve_with_timeout
from sudoku_benchmark_lab.benchmark.suite import list_suite_configs, run_suite
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
    save = input("Save raw benchmark results to CSV? (y/n): ").strip().lower() == "y"
    table = benchmark_dataset(dataset, solver_names=None if choice == "all" else [choice], progress=print)
    summary = summary_dataframe(table)
    print(f"\n-----Results-----\nPuzzles Tested: {table['puzzle_index'].nunique()}\n")
    print_summary_table(summary)
    if save:
        csv_path = result_path(dataset)
        write_csv(table, csv_path)
        print(f"\nCSV written to: {csv_path}")
    return table


def run_suite_menu():
    configs = list_suite_configs()
    if not configs:
        print("\nNo suite configs found in experiments/configs/.")
        return
    selected = prompt_choice(
        "\nAvailable benchmark suites:", [path.name for path in configs]
    )
    if selected is None:
        print("Invalid suite config.")
        return
    config_path = next(path for path in configs if path.name == selected)
    try:
        output = run_suite(config_path)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Benchmark suite failed: {error}")
        return
    print(f"\nSuite results written to: {output}")


def summarize_results_menu():
    result_files = discover_result_csvs()
    if not result_files:
        print("\nNo benchmark result CSVs found in results/ or experiments/results/.")
        return
    options = [
        str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path)
        for path in result_files
    ]
    selected = prompt_choice("\nAvailable benchmark result CSVs:", options)
    if selected is None:
        print("Invalid result CSV.")
        return
    path = result_files[options.index(selected)]
    try:
        summary = summarize_result_csv(path)
    except (OSError, ValueError) as error:
        print(f"Could not summarize results: {error}")
        return
    print(f"\nSummary for: {path}")
    print_summary_table(summary)


def main():
    while True:
        print(
            "\n-----Sudoku Menu-----\n"
            "1. Enter Puzzle\n2. Generate Dataset\n3. Benchmark\n"
            "4. Run Suite\n5. Summarize Results\n6. Quit"
        )
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
            run_suite_menu()
        elif choice == "5":
            summarize_results_menu()
        elif choice == "6":
            return
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
