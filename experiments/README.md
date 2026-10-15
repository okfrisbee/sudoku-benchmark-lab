# Experiments

Experiment definitions and outputs live here, separate from reusable package
code and input datasets.

- [`configs/`](configs/) contains TOML suite definitions. The interactive
  **Run Suite** menu lists every TOML file in this directory.
- [`results/`](results/) contains one folder per suite config, with a new
  timestamped subfolder for each execution.
- [`results/run_01/2026-09-04_00-44-48/`](results/run_01/2026-09-04_00-44-48/)
  holds the frozen published study. Its exact generated inputs remain in
  [`datasets/suites/run_01/`](../datasets/suites/run_01/).
- [`results/calibration/`](results/calibration/) preserves the pilot
  measurements that informed the published suite.

Run metadata records the selected config and dataset hashes, environment, source
revision, and result hashes. Use a new config filename when changing a suite in
a way that would produce different datasets for the same case names. On rerun,
an existing case dataset is reused as-is when its count, board size, and clue
level match the config; metadata marks whether each dataset was generated or
reused.

New suite runs save one canonical `raw_results.csv` with one row per
puzzle-solver attempt. The runner prints a case summary after the run, but does
not save summary CSVs; use the **Summarize Results** menu to print a table for
one selected CSV. Run `python scripts/generate_report.py PATH/TO/raw_results.csv`
to write `reports/summary.md` and chart assets inside that run folder. The frozen
published run retains its original summary CSVs as historical evidence.

`run_01.toml` preserves the exact suite configuration recorded for the
published run. Its legacy `output_dir` field is retained for historical
provenance; current suite executions use the timestamped layout described above.
The frozen published raw-results CSV predates the `solver_solution` column;
new suite runs include each solver's returned board in that column.
