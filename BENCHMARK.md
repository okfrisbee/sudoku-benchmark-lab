# Benchmark details

This page explains how the published comparison was chosen, run, and saved.
For the quick result summary, findings, and solver tradeoffs, start with the
project [README](README.md).

## What was tested

The benchmark contains 244 seeded puzzles:

- 150 at 9×9
- 60 at 16×16
- 24 at 25×25
- 10 at 36×36

All six solvers received every puzzle, producing 1,464 attempts. Because the
puzzles are generated from seeds, the exact same boards can be recreated.

The configuration and CSV files use `difficulty` as a field name, but the field
only describes **clue level**:

- `easy` means 75–85% of cells are already filled.
- `medium` means 50–60% are filled.
- `hard` means 25–35% are filled.

These names do not describe how difficult a puzzle is for a person. Randomly
removing clues also does not guarantee a single answer.

The code understands board sizes with square boxes. In practice, 4×4 is too
small to be a useful speed test, 9×9 through 25×25 give useful comparisons, and
36×36 acts as a small scaling test where puzzles with few clues are often too
slow for the chosen limits.

## How the test size was chosen

The final settings were chosen only after two small pilot runs. The first used
two puzzles from every size and clue level. The second added more puzzles where
the early result was unclear, using different seeds.

Those pilots showed:

- High- and mid-clue 9×9 results settled into the same solver order by 12
  puzzles. Low-clue 9×9 backtracking times varied much more, so the final run
  used 50 puzzles at every 9×9 clue level.
- At 16×16, two seconds was enough to separate the consistently finishing
  solvers from those that often ran too long.
- At 25×25, SAT and DLX remained useful on puzzles with fewer clues, while
  several other solvers repeatedly reached the time limit. Smaller samples kept
  the overall run reasonable.
- At 36×36, every solver handled the high-clue pilot, but the other clue levels
  were mostly timeouts. A few puzzles were enough to show that boundary.
- 4×4 was left to the correctness tests because even high-clue 9×9 runs were
  already below one millisecond.

The final puzzle counts, seeds, and time limits are in the first table below.
They were locked before the final benchmark began and were not changed to make
the final results look better. The pilot CSVs and fuller decision notes are in
[calibration notes](experiments/results/calibration/README.md).

## How runs and timings work

- Solvers run one at a time and receive the same puzzles in the same order.
- Each attempt runs in its own child process. If it is still running at the
  case’s time limit, that process is stopped and the result is recorded as a
  timeout.
- Before recording results, each solver gets one warm-up solve on the first
  9×9 puzzle.
- Python’s `time.perf_counter()` clock measures the full solver call: reading the
  board, building its internal representation, searching, and creating the
  answer.
- Starting the child process, sending its result back, and checking the answer
  are outside the successful runtime.
- A timeout is recorded as exactly the allowed time. The small extra delay
  needed to stop the process is not charged to the solver.
- A solve only counts after an independent check confirms every original clue
  and every row, column, and box.
- Median, average, and p95 use completed solves only. The median is the middle
  successful time; p95 is a slow-tail measure where 95% of successful runs were
  at or below that value.
- Throughput divides completed puzzles by all charged solver time, including
  full timeout allowances. Read it together with the success count.

## Test machine

| Item | Value |
|:---|:---|
| Benchmark date | 2026-09-04 |
| CPU | AMD Ryzen 7 3800X 8-Core Processor (16 logical CPUs) |
| Operating system | Ubuntu 24.04.4 LTS under WSL2, Linux 6.6.87.1 |
| Python | CPython 3.12.3 |
| Solver packages | python-sat 1.8.dev30; z3-solver 4.16.0.0 |
| Reporting packages | pandas 2.3.3; NumPy 2.4.2 |
| Complete run time | 463.488 seconds |

The saved
[metadata file](experiments/results/run_01/2026-09-04_00-44-48/metadata.json) includes the full
package list, timestamps, definitions, and file hashes.

## Detailed results

<!-- BENCHMARK_TABLES_START -->
### Frozen benchmark configuration

| Size | Clue-density tier | Clue range | Puzzles | Timeout / solver | Seed |
|---:|:---|---:|---:|---:|---:|
| 9×9 | easy | 75–85% | 50 | 1 s | 2026090401 |
| 9×9 | medium | 50–60% | 50 | 1 s | 2026090402 |
| 9×9 | hard | 25–35% | 50 | 1 s | 2026090403 |
| 16×16 | easy | 75–85% | 24 | 1 s | 2026090411 |
| 16×16 | medium | 50–60% | 20 | 2 s | 2026090412 |
| 16×16 | hard | 25–35% | 16 | 2 s | 2026090413 |
| 25×25 | easy | 75–85% | 10 | 1.5 s | 2026090421 |
| 25×25 | medium | 50–60% | 8 | 2.5 s | 2026090422 |
| 25×25 | hard | 25–35% | 6 | 2.5 s | 2026090423 |
| 36×36 | easy | 75–85% | 4 | 3 s | 2026090431 |
| 36×36 | medium | 50–60% | 3 | 3 s | 2026090432 |
| 36×36 | hard | 25–35% | 3 | 3 s | 2026090433 |

### Results aggregated by size

Runtime statistics use successful solves only. Throughput is solved puzzles divided by total solver time, with each timeout charged at its cutoff.

| Size | Solver | Attempted | Solved | Success | Timeouts | Median (ms) | Mean (ms) | p95 (ms) | Throughput (puzzles/s) |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| 9×9 | Naive | 150 | 146 | 97.3% | 4 | 0.622 | 15.723 | 65.823 | 23.19 |
| 9×9 | Naive recursive | 150 | 145 | 96.7% | 5 | 0.820 | 26.601 | 113.107 | 16.37 |
| 9×9 | CSP | 150 | 150 | 100.0% | 0 | 1.312 | 1.540 | 2.805 | 649.25 |
| 9×9 | SAT | 150 | 150 | 100.0% | 0 | 26.073 | 26.647 | 30.907 | 37.53 |
| 9×9 | SMT | 150 | 150 | 100.0% | 0 | 64.773 | 130.262 | 460.146 | 7.68 |
| 9×9 | DLX | 150 | 150 | 100.0% | 0 | 2.170 | 2.145 | 3.259 | 466.21 |
| 16×16 | Naive | 60 | 42 | 70.0% | 18 | 1.292 | 46.657 | 270.250 | 1.11 |
| 16×16 | Naive recursive | 60 | 41 | 68.3% | 19 | 1.961 | 154.694 | 1028.300 | 0.92 |
| 16×16 | CSP | 60 | 53 | 88.3% | 7 | 3.768 | 49.083 | 94.538 | 3.19 |
| 16×16 | SAT | 60 | 60 | 100.0% | 0 | 114.036 | 116.184 | 138.935 | 8.61 |
| 16×16 | SMT | 60 | 44 | 73.3% | 16 | 152.490 | 200.440 | 386.580 | 1.08 |
| 16×16 | DLX | 60 | 59 | 98.3% | 1 | 8.299 | 8.915 | 15.098 | 23.36 |
| 25×25 | Naive | 24 | 10 | 41.7% | 14 | 1.818 | 1.912 | 2.637 | 0.29 |
| 25×25 | Naive recursive | 24 | 10 | 41.7% | 14 | 6.187 | 6.262 | 8.227 | 0.29 |
| 25×25 | CSP | 24 | 17 | 70.8% | 7 | 9.940 | 64.437 | 229.820 | 0.91 |
| 25×25 | SAT | 24 | 24 | 100.0% | 0 | 511.858 | 543.097 | 748.372 | 1.84 |
| 25×25 | SMT | 24 | 14 | 58.3% | 10 | 333.007 | 606.301 | 1607.840 | 0.42 |
| 25×25 | DLX | 24 | 23 | 95.8% | 1 | 29.133 | 147.960 | 316.605 | 3.90 |
| 36×36 | Naive | 10 | 4 | 40.0% | 6 | 3.688 | 4.825 | 7.675 | 0.22 |
| 36×36 | Naive recursive | 10 | 4 | 40.0% | 6 | 21.706 | 22.437 | 28.799 | 0.22 |
| 36×36 | CSP | 10 | 5 | 50.0% | 5 | 17.888 | 31.277 | 72.884 | 0.33 |
| 36×36 | SAT | 10 | 6 | 60.0% | 4 | 1682.173 | 1667.483 | 1811.862 | 0.27 |
| 36×36 | SMT | 10 | 4 | 40.0% | 6 | 957.212 | 964.751 | 1006.926 | 0.18 |
| 36×36 | DLX | 10 | 5 | 50.0% | 5 | 42.414 | 62.148 | 118.865 | 0.33 |

### Results by clue-density tier

Each cell is `solved/attempted · median successful runtime · timeouts`.

| Size / tier | Naive | Naive recursive | CSP | SAT | SMT | DLX |
|:---|---:|---:|---:|---:|---:|---:|
| 9×9 easy | 50/50 · 0.421 ms · 0 TO | 50/50 · 0.537 ms · 0 TO | 50/50 · 0.972 ms · 0 TO | 50/50 · 25.915 ms · 0 TO | 50/50 · 57.812 ms · 0 TO | 50/50 · 1.365 ms · 0 TO |
| 9×9 medium | 50/50 · 0.569 ms · 0 TO | 50/50 · 0.864 ms · 0 TO | 50/50 · 1.173 ms · 0 TO | 50/50 · 27.350 ms · 0 TO | 50/50 · 64.476 ms · 0 TO | 50/50 · 2.201 ms · 0 TO |
| 9×9 hard | 46/50 · 6.112 ms · 4 TO | 45/50 · 11.090 ms · 5 TO | 50/50 · 1.996 ms · 0 TO | 50/50 · 25.488 ms · 0 TO | 50/50 · 221.851 ms · 0 TO | 50/50 · 2.598 ms · 0 TO |
| 16×16 easy | 24/24 · 0.795 ms · 0 TO | 24/24 · 1.439 ms · 0 TO | 24/24 · 2.690 ms · 0 TO | 24/24 · 114.793 ms · 0 TO | 24/24 · 141.776 ms · 0 TO | 24/24 · 5.447 ms · 0 TO |
| 16×16 medium | 18/20 · 28.009 ms · 2 TO | 17/20 · 96.312 ms · 3 TO | 20/20 · 4.342 ms · 0 TO | 20/20 · 115.386 ms · 0 TO | 20/20 · 245.759 ms · 0 TO | 20/20 · 8.548 ms · 0 TO |
| 16×16 hard | 0/16 · — · 16 TO | 0/16 · — · 16 TO | 9/16 · 64.778 ms · 7 TO | 16/16 · 108.846 ms · 0 TO | 0/16 · — · 16 TO | 15/16 · 13.107 ms · 1 TO |
| 25×25 easy | 10/10 · 1.818 ms · 0 TO | 10/10 · 6.187 ms · 0 TO | 10/10 · 8.766 ms · 0 TO | 10/10 · 493.869 ms · 0 TO | 10/10 · 326.057 ms · 0 TO | 10/10 · 15.993 ms · 0 TO |
| 25×25 medium | 0/8 · — · 8 TO | 0/8 · — · 8 TO | 7/8 · 11.375 ms · 1 TO | 8/8 · 530.839 ms · 0 TO | 4/8 · 1150.436 ms · 4 TO | 8/8 · 33.154 ms · 0 TO |
| 25×25 hard | 0/6 · — · 6 TO | 0/6 · — · 6 TO | 0/6 · — · 6 TO | 6/6 · 550.324 ms · 0 TO | 0/6 · — · 6 TO | 5/6 · 134.720 ms · 1 TO |
| 36×36 easy | 4/4 · 3.688 ms · 0 TO | 4/4 · 21.706 ms · 0 TO | 4/4 · 17.481 ms · 0 TO | 4/4 · 1587.108 ms · 0 TO | 4/4 · 957.212 ms · 0 TO | 4/4 · 41.108 ms · 0 TO |
| 36×36 medium | 0/3 · — · 3 TO | 0/3 · — · 3 TO | 1/3 · 86.354 ms · 2 TO | 2/3 · 1786.377 ms · 1 TO | 0/3 · — · 3 TO | 1/3 · 135.146 ms · 2 TO |
| 36×36 hard | 0/3 · — · 3 TO | 0/3 · — · 3 TO | 0/3 · — · 3 TO | 0/3 · — · 3 TO | 0/3 · — · 3 TO | 0/3 · — · 3 TO |
<!-- BENCHMARK_TABLES_END -->

For a shorter explanation of what these measurements mean, see
[What the results show](README.md#what-the-results-show) in the main README.

## Limits of this benchmark

- These are generated pattern-based puzzles with randomly removed clues, not
  hand-designed or competition puzzles.
- Clue level is not the same as human difficulty.
- Every puzzle has at least one answer, but it may have more than one. The
  benchmark accepts any valid completion.
- The 25×25 and especially 36×36 samples are intentionally small. They show
  scaling behavior, not precise success percentages for every possible puzzle.
- The numbers come from one serial run on one WSL2 computer. Very short times
  can change with hardware, Python version, power settings, and other system
  activity.
- Solver order stayed fixed after the warm-up, so small order or temperature
  effects may remain.
- A timeout only means a solver did not finish within this benchmark’s limit.
  It does not mean the puzzle has no answer or that the solver could never
  finish with more time.

## Run a benchmark suite

Install the project as shown in the [quick start](README.md#quick-start), then
choose **Run Suite** from the interactive menu. The menu lists TOML files in
[`experiments/configs/`](experiments/configs/). Every execution creates a new
timestamped results folder under `experiments/results/<config-name>/` and
stores the seeded case datasets under `data/datasets/suites/<config-name>/`.

```bash
.venv/bin/sudoku-lab
```

The puzzle seeds, solver order, case order, and time limits stay fixed. Runtime
values will naturally change on a different computer. Run metadata records the
configuration and dataset hashes for reproducibility.

## Saved evidence

- [`raw_results.csv`](experiments/results/run_01/2026-09-04_00-44-48/raw_results.csv) has one row
  for every solver attempt.
- [`summary_by_case.csv`](experiments/results/run_01/2026-09-04_00-44-48/summary_by_case.csv)
  groups results by board size, clue level, and solver.
- [`summary_by_size.csv`](experiments/results/run_01/2026-09-04_00-44-48/summary_by_size.csv)
  groups results by board size and solver.
- [`readme_tables.md`](experiments/results/run_01/2026-09-04_00-44-48/readme_tables.md) is the
  saved source for the detailed tables above.
- [`run_01.toml`](experiments/configs/run_01.toml) is the exact suite configuration.
- [`run_01 datasets`](data/datasets/suites/run_01/) contains the exact puzzles used.
- [`metadata.json`](experiments/results/run_01/2026-09-04_00-44-48/metadata.json) records the
  machine, method, and SHA-256 file hashes.

The reusable runner is in `src/sudoku_benchmark_lab/benchmark/`; suite configs
and run outputs are indexed in [experiments](experiments/README.md). Calibration
pilot measurements are under `experiments/results/calibration/`.

