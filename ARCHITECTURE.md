# Architecture

This is a Sudoku-specific Python package for generating puzzle datasets, comparing solvers, and running reproducible studies. The interactive application and research suite share the same solver registry, timed runner, solution validator, and reporting code.

## Components

| Module | Responsibility |
|:---|:---|
| `board.py`, `validation.py` | Parse and format Sudoku boards; independently check a completed answer against givens and Sudoku rules. |
| `solvers/` | Six algorithms, a shared `SolverResult`, and an explicit registry of names and labels. SAT and SMT are imported only when selected. |
| `datasets/generation.py` | Build seeded completed boards, remove clues, and create puzzle records. Clue levels describe clue density, not human difficulty. |
| `datasets/io.py` | Read and write JSONL and locate generated datasets. Accept legacy fields in old research records. |
| `benchmark/runner.py` | Execute one solver per child process with a timeout; validate claimed solutions; return per-attempt tabular results. |
| `benchmark/reporting.py`, `visualization.py` | Save per-attempt rows (including each solver's returned board), aggregate metrics, and draw plots. Runtime summaries use successful solves, while throughput charges timeouts. |
| `benchmark/suite.py` | Discover TOML suites, generate seeded case datasets, run the configured matrix, and write CSV results and provenance metadata. |
| `cli.py` | Interactive input, menus, progress output, and graph choices. |

The dependency direction is board and result contracts → solvers and datasets → benchmark → CLI. The runner and dataset modules never prompt. A suite calls the same runner as the interactive benchmark. The root `main.py` remains a small compatibility entry point.

## Solver and data contracts

A registered solver accepts a board string or list of integer cells and returns `SolverResult`. `0` means empty. Space-separated strings support values above nine. A `solved` result contains a completed board; the runner checks it against original clues and every row, column, and box before recording success. Raw result CSVs preserve the normalized `solver_solution` for each attempt; absent answers are blank and malformed answers are retained for debugging. The generated reference completion is not an equality oracle because clue removal does not guarantee a unique solution. SAT/SMT dependencies stay local to their implementations. To add a solver, register its module, callable, and label in `solvers/registry.py`; no plugin discovery is used.

Generation starts from a seeded complete board and removes a seeded clue pattern. It does not test uniqueness. New JSONL records omit historical `verification_mode` and `unique` fields; the reader accepts old records containing them. An experiment specifies solver names, puzzle counts, seeds, sizes, and timeouts in a TOML suite file under `experiments/configs/`. The CLI lists every TOML file there and invokes the suite runner. Case datasets are kept under `data/datasets/suites/<config-name>/`; run outputs are written to a new timestamped directory under `experiments/results/<config-name>/`.

The runner charges a timed-out attempt exactly its time limit. Successful runtime is measured inside the solver and excludes process startup, result transport, and independent answer validation. Published measurements should only be compared with these definitions in mind.

## Configuration and historical evidence

Application settings live in `config.py` as validated Python defaults; callers can pass nested overrides to `load_config()`. Paths default to the checkout's `data/` folders, or to `data/` under the current directory when installed outside a checkout. Suite matrices remain in TOML because they describe individual experiments. Each result folder snapshots application settings to `project_config.json`; metadata records the suite config path and hash, dataset paths and hashes, source revision, environment, and result artifact hashes. Every execution receives a unique timestamped result folder.

The published study is frozen evidence under `experiments/results/run_01/2026-09-04_00-44-48/`; its case datasets are under `data/datasets/suites/run_01/`. Historical metadata retains the source paths and hashes recorded at the time of the run. Calibration measurements are under `experiments/results/calibration/`.
