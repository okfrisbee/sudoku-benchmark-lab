# Working in this repository

- Start with [ARCHITECTURE.md](ARCHITECTURE.md) for module responsibilities and dependency rules. Read [BENCHMARK.md](BENCHMARK.md) for the published study.
- Install with `python -m pip install -e '.[dev]'`. Run `python -m pytest -q` and `python -m data.research_benchmark.verify_readme` after changes. The tests also run with `PYTHONPATH=src python -m unittest discover -s tests`.
- Add a solver under `src/sudoku_benchmark_lab/solvers/`, register its name, function, and label in `solvers/registry.py`, and test solved, invalid, and unsatisfiable boards. Return `SolverResult`; benchmark code checks completed answers independently.
- Add an experiment with a new suite TOML and a new output directory. The published `data/research_benchmark/final/` and calibration data are historical evidence: do not overwrite, move, or rewrite them during code refactors. Its `metadata.json` describes the original source revision and file hashes.
- Keep input prompts in `cli.py`, JSONL handling in `datasets/io.py`, and timed execution in `benchmark/runner.py`. Do not add puzzle solvability or uniqueness checks as an implicit part of generation.
- Update this guide and `ARCHITECTURE.md` when architectural boundaries change.
