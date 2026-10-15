# Sudoku Solver Benchmark Lab

Compare six genuinely different ways to solve Sudoku using the same inputs,
result format, timeout rules, and correctness checks. The project ranges from
simple backtracking to constraint-based methods, SAT/SMT solvers, and exact
cover. It also includes dataset generation, answer checking, CSV reports, and
benchmark graphs.

**Main takeaway:** no solver is best everywhere. Simple backtracking wins when
a puzzle already has many clues. CSP is a strong choice for standard 9×9
puzzles. DLX is usually the best balance of speed and reliability as boards
grow, while SAT takes longer to set up but was the only solver that completed
every benchmark puzzle through 25×25.

The code can read any `N×N` board where `sqrt(N)` is an integer, such as 4×4,
9×9, 16×16, 25×25, and 36×36. That describes the accepted board format, not a
guarantee that every solver will finish quickly. In the benchmark, 36×36
low-clue puzzles timed out for every solver.

## Benchmark summary

The final study used 244 repeatable puzzles and recorded 1,464 solver attempts.
“High,” “mid,” and “low clue” describe how much of the board is filled in; they
are not ratings of human puzzle difficulty.

<!-- BENCHMARK_HIGHLIGHTS_START -->
| Size | Headline result |
|---:|:---|
| 9×9 | Naive was fastest with many clues at 0.421 ms median; CSP solved 50/50 low-clue puzzles at 1.996 ms median. |
| 16×16 | SAT solved 60/60; DLX solved 59/60, and its median successful run was 8.299 ms, compared with 114.036 ms for SAT. |
| 25×25 | SAT solved 24/24; DLX solved 23/24, and its median successful run was 29.133 ms, compared with 511.858 ms for SAT. |
| 36×36 | Across all six solvers: high-clue 24/24, mid-clue 4/18, and low-clue 0/18 (18 timeouts). |
<!-- BENCHMARK_HIGHLIGHTS_END -->

The table above is the short version. [BENCHMARK.md](BENCHMARK.md) keeps the
calibration work, fixed test settings, timing rules, test machine, complete
per-tier tables, and limitations. All saved data is under
[data/research_benchmark](data/research_benchmark/README.md).

## Quick start

Python 3.11 or newer is recommended. The published benchmark used Python
3.12.3.

```bash
git clone https://github.com/okfrisbee/sudoku-benchmark-lab.git
cd sudoku-benchmark-lab
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python main.py
```

That starts the interactive application, where you can solve a puzzle, generate
a dataset, or run a comparison. On Windows, replace
`.venv/bin/python` with `.venv\Scripts\python`.

## What you can do

- **Solve with one shared result format.** Every solver reports whether it
  solved, failed, errored, or reached the time limit.
- **Generate repeatable datasets.** A seed recreates the same finished board and
  the same clue pattern.
- **Check answers.** Independently check each completed board before recording
  a solver attempt as successful.
- **Compare solvers fairly.** Give every solver the same puzzles and time limit,
  and stop slow attempts safely in their own process.
- **Save useful results.** Write one CSV row per attempt plus summaries for
  success, timeouts, typical runtime, slow-tail runtime, and throughput.
- **Plot comparisons.** View per-puzzle times and average-time bar charts after
  an interactive benchmark.

## Six approaches to the same puzzle

These implementations do more than vary one backtracking routine:

- **Naive** tries values in board order while keeping quick row, column, and box
  lookup sets. It has very little startup work.
- **Naive recursive** performs the same kind of trial and error using a simpler
  recursive function and direct validity checks.
- **CSP** keeps track of each cell’s possible values, applies common deductions,
  and guesses first where the fewest choices remain.
- **SAT** turns the puzzle into many yes/no rules and passes them to the CaDiCaL
  SAT solver.
- **SMT** describes cells as integers with Sudoku rules and asks Z3 to find
  values that satisfy them.
- **DLX** turns Sudoku into an exact-cover problem and searches it with
  Algorithm X and dancing links.

All six use the same parser and return a `SolverResult`. A solution only counts
after a separate check confirms that it keeps every original clue and has valid
rows, columns, and boxes.

## Benchmark results

These totals combine the three clue levels for each board size.

<!-- BENCHMARK_RESULTS_START -->
| Size | Solver | Solved | Timeouts | Median successful run | Mean successful run |
|---:|:---|---:|---:|---:|---:|
| 9×9 | Naive | 146/150 | 4 | 0.622 ms | 15.723 ms |
| 9×9 | Naive recursive | 145/150 | 5 | 0.820 ms | 26.601 ms |
| 9×9 | CSP | 150/150 | 0 | 1.312 ms | 1.540 ms |
| 9×9 | SAT | 150/150 | 0 | 26.073 ms | 26.647 ms |
| 9×9 | SMT | 150/150 | 0 | 64.773 ms | 130.262 ms |
| 9×9 | DLX | 150/150 | 0 | 2.170 ms | 2.145 ms |
| 16×16 | Naive | 42/60 | 18 | 1.292 ms | 46.657 ms |
| 16×16 | Naive recursive | 41/60 | 19 | 1.961 ms | 154.694 ms |
| 16×16 | CSP | 53/60 | 7 | 3.768 ms | 49.083 ms |
| 16×16 | SAT | 60/60 | 0 | 114.036 ms | 116.184 ms |
| 16×16 | SMT | 44/60 | 16 | 152.490 ms | 200.440 ms |
| 16×16 | DLX | 59/60 | 1 | 8.299 ms | 8.915 ms |
| 25×25 | Naive | 10/24 | 14 | 1.818 ms | 1.912 ms |
| 25×25 | Naive recursive | 10/24 | 14 | 6.187 ms | 6.262 ms |
| 25×25 | CSP | 17/24 | 7 | 9.940 ms | 64.437 ms |
| 25×25 | SAT | 24/24 | 0 | 511.858 ms | 543.097 ms |
| 25×25 | SMT | 14/24 | 10 | 333.007 ms | 606.301 ms |
| 25×25 | DLX | 23/24 | 1 | 29.133 ms | 147.960 ms |
| 36×36 | Naive | 4/10 | 6 | 3.688 ms | 4.825 ms |
| 36×36 | Naive recursive | 4/10 | 6 | 21.706 ms | 22.437 ms |
| 36×36 | CSP | 5/10 | 5 | 17.888 ms | 31.277 ms |
| 36×36 | SAT | 6/10 | 4 | 1682.173 ms | 1667.483 ms |
| 36×36 | SMT | 4/10 | 6 | 957.212 ms | 964.751 ms |
| 36×36 | DLX | 5/10 | 5 | 42.414 ms | 62.148 ms |
<!-- BENCHMARK_RESULTS_END -->

The median and mean are calculated only from runs that finished. The median is
the middle runtime; the mean is the usual arithmetic average and is more
affected by unusually slow solves. Either can be misleading when a solver has
many timeouts, so read the runtime and completion columns together. Every
unfinished attempt in this final run was a timeout. The
[full report](BENCHMARK.md#detailed-results) also includes p95 slow-tail times,
throughput, and results for each clue level.

## What the results show

- **With many clues, simple code wins.** These puzzles need little guessing, so
  Naive’s small amount of setup work gave it the best median at every board
  size: 0.421 ms at 9×9 through 3.688 ms at 36×36.
- **CSP was especially effective on smaller search-heavy puzzles.** It solved
  all 50 low-clue 9×9 puzzles at a 1.996 ms median and all 20 mid-clue 16×16
  puzzles at a 4.342 ms median. Its results became less predictable on sparse,
  larger boards.
- **DLX was usually the fast large-board option.** It solved 59/60 puzzles at
  16×16 and 23/24 at 25×25, with much lower successful runtimes than SAT. Its
  one timeout at each size shows that it was not perfectly reliable.
- **SAT was the reliability leader through 25×25.** It completed every puzzle
  at those sizes, but building and solving its rule set cost much more time on
  easy, high-clue boards.
- **36×36 exposed the practical limit.** Every solver completed the four
  high-clue puzzles. Only 4 of 18 mid-clue attempts finished, and none of the 18
  low-clue attempts did so within three seconds.

## Practical tradeoffs

| Solver | Where it helps | What to watch for |
|:---|:---|:---|
| Naive | Extremely fast when many cells are already filled. | Guessing can grow suddenly, leading to long runs or timeouts. |
| Naive recursive | Easy-to-follow reference implementation. | Usually slower than the iterative version with the same search weakness. |
| CSP | Fast deductions and excellent 9×9 results. | Sparse 16×16 and larger puzzles can still require too much guessing. |
| SAT | Most dependable solver through 25×25 in this study. | Turning Sudoku into yes/no rules adds noticeable startup cost. |
| SMT | Clear, flexible integer description of Sudoku. | Z3 took substantial setup and search time on these datasets. |
| DLX | Strong mix of speed and reliability on larger boards. | A few sparse puzzles still caused long searches and timeouts. |

These are conclusions from this dataset and machine, not a universal ranking.

## Use a solver from Python

```python
from sudoku_benchmark_lab.solvers.dlx import solve_dlx

puzzle = "1 0 3 0 0 4 0 2 2 0 4 0 0 3 0 1"
result = solve_dlx(puzzle)

if result.solved:
    print(result.solution)
    print(f"{result.runtime_seconds:.6f} seconds")
else:
    print(result.status, result.error)
```

Use spaces between cells when values can be greater than 9. In every size, `0`
means an empty cell.

## Generate datasets

The generator starts with a valid, shuffled finished board and removes cells.
Generated datasets use JSON Lines, with one puzzle record per line.

The API and saved data still use the field name `difficulty` for compatibility,
but it really means **clue level**:

| `difficulty` value | Given cells | Plain-language meaning |
|:---|---:|:---|
| `easy` | 75–85% | Many clues |
| `medium` | 50–60% | A middle number of clues |
| `hard` | 25–35% | Few clues |

These labels do not measure human solving difficulty. Removing clues at random
also does not guarantee one unique answer. A puzzle with fewer clues may even
be quicker for a program if it has many valid ways to finish.

```python
from sudoku_benchmark_lab.datasets.generation import generate_dataset

path = generate_dataset(size=9, difficulty="mixed", count=100, seed=123)
print(path)
```

New datasets go to `data/datasets/`. Interactive benchmark results go to
`data/results/`. The research benchmark’s exact puzzles and results are already
saved in `data/research_benchmark/`.

Puzzle generation starts from a completed board and removes clues. It does not
test whether the remaining clues define a unique solution. Older datasets can
contain `verification_mode` and `unique` fields; readers accept those historical
records, while new datasets omit the fields.

## Run your own comparison

To choose a generated dataset and compare one or all solvers, start the
interactive menu and select **Benchmark**:

```bash
.venv/bin/sudoku-lab
```

To repeat the published benchmark, use a new or empty output directory:

```bash
.venv/bin/python -m data.research_benchmark.suite \
  --config data/research_benchmark/final_benchmark.toml \
  --output-dir /tmp/sudoku-benchmark-reproduction
```

The research suite recreates the seeded puzzles, gives each solver one warm-up
run, checks every returned answer, and saves the detailed results. It refuses
to overwrite a non-empty directory.

## Tests and documentation checks

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m data.research_benchmark.verify_readme
```

The second command rebuilds the two README result tables from the saved CSVs and
checks that the full tables in `BENCHMARK.md` match their saved source.

For package boundaries and development commands, see [ARCHITECTURE.md](ARCHITECTURE.md)
and [AGENTS.md](AGENTS.md).
