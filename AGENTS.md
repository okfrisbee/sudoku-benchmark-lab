# Working in this repository

- Start with [ARCHITECTURE.md](ARCHITECTURE.md) for module responsibilities and dependency rules. Read [BENCHMARK.md](BENCHMARK.md) for the published study.
- Install with `python -m pip install -e '.[dev]'`. Run `python -m pytest -q` after changes. The tests also run with `PYTHONPATH=src python -m unittest discover -s tests`.
- Add a solver under `src/sudoku_benchmark_lab/solvers/`, register its name, function, and label in `solvers/registry.py`, and test solved, invalid, and unsatisfiable boards. Return `SolverResult`; benchmark code checks completed answers independently.
- Add a suite by placing a TOML config in `experiments/configs/`; the interactive **Run Suite** menu discovers every TOML file there. Runs create timestamped result folders under `experiments/results/<config-name>/`; case datasets are stored under `datasets/suites/<config-name>/`. Use a new config filename when you intend to generate different datasets for the same case names.
- Interactive datasets live in `datasets/`; normal benchmark raw CSVs live in `results/<dataset>/<timestamp>/raw_results.csv`. Do not write summary CSVs; summaries are computed from raw rows for display or analysis.
- Use the **Summarize Results** menu item to print a table for one selected raw CSV. Run `python scripts/generate_report.py PATH/TO/raw_results.csv` to save `reports/summary.md` and chart assets inside that run folder; keep suite cases separate.
- Keep application settings in `config.py`; keep experiment case matrices in their suite TOML files. Keep input prompts in `cli.py`, JSONL handling in `datasets/io.py`, and timed execution in `benchmark/runner.py`. Do not add puzzle solvability or uniqueness checks as an implicit part of generation.
- Update this guide and `ARCHITECTURE.md` when architectural boundaries change.
