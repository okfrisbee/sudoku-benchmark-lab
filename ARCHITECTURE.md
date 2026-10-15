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
| `benchmark/reporting.py`, `visualization.py` | Aggregate and save results; draw plots. Runtime summaries use successful solves, while throughput charges timeouts. |
| `benchmark/suite.py` | Run a configured case matrix with seeded datasets, warm-up, result files, and environment metadata. |
| `cli.py` | Interactive input, menus, progress output, and graph choices. |

The dependency direction is board and result contracts → solvers and datasets → benchmark → CLI. `benchmark/runner.py` and dataset modules never prompt. The research suite calls the same runner as the interactive benchmark. The root `main.py`, `benchmark/runner.py`, and `data/research_benchmark/suite.py` retain existing command paths as small entry-point wrappers.

## Solver and data contracts

A registered solver accepts a board string or list of integer cells and returns `SolverResult`. `0` means empty. Space-separated strings support values above nine. A `solved` result contains a completed board; the runner checks it against original clues and every row, column, and box before recording success. SAT/SMT dependencies stay local to their implementations. To add a solver, register its module, callable, and label in `solvers/registry.py`; no plugin discovery is used.

Generation starts from a seeded complete board and removes a seeded clue pattern. It does not test uniqueness. New JSONL records omit historical `verification_mode` and `unique` fields; the reader accepts old records containing them. An experiment specifies solver names, puzzle counts, seeds, sizes, and timeouts in a TOML suite file.

The runner charges a timed-out attempt exactly its time limit. Successful runtime is measured inside the solver and excludes process startup, result transport, and independent answer validation. Published measurements should only be compared with these definitions in mind.

## Configuration and historical evidence

`config.py` validates `config.toml` when an operation needs it and resolves relative data paths from that file's directory. An explicit config path can be supplied programmatically; the packaged default is a fallback outside a source checkout. Suite outputs copy their configuration and capture source and artifact hashes. Use a new output directory for each study.

The original research datasets, CSVs, and metadata under `data/research_benchmark/final/` are frozen evidence. The paths and hashes in their `metadata.json` refer to the original source revision. Moving code does not rewrite that history. `data/research_benchmark/verify_readme.py` checks the published README and BENCHMARK tables against those saved results.
