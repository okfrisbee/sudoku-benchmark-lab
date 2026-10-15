import os

import matplotlib

matplotlib.use("TkAgg" if os.environ.get("DISPLAY") else "Agg")

import matplotlib.pyplot as plt


def visualization_data(results_table):
    times_by_solver = {
        name: solver_results["runtime_seconds"].tolist()
        for name, solver_results in results_table.groupby("solver", sort=False)
    }
    tested = results_table["puzzle_index"].nunique()
    avgs = (
        results_table.groupby("solver", sort=False)["runtime_seconds"].mean().to_dict()
    )
    return times_by_solver, tested, avgs


def visualize_benchmark(times_by_solver, tested, avgs, show_naive=True):
    plt.figure()
    for name, ts in times_by_solver.items():
        if name == "naive" and not show_naive:
            continue
        xs = range(1, len(ts) + 1)
        ys = ts
        plt.plot(xs, ys, label=name)
    plt.title(f"Sudoku Benchmark: Per-puzzle solve times (n={tested})")
    plt.xlabel("Puzzle #")
    plt.ylabel("Time (seconds)")
    plt.legend()
    plt.tight_layout()

    plt.figure()
    names, values = list(avgs.keys()), list(avgs.values())
    plt.bar(names, values)
    plt.title("Average solve time")
    plt.xlabel("Solver")
    plt.ylabel("Avg time (seconds)")
    plt.tight_layout()

    plt.show()
