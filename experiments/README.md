# Experiments

Experiment definitions and outputs live here, separate from reusable package
code and input datasets.

- [`configs/`](configs/) contains TOML suite definitions. The interactive
  **Run Suite** menu lists every TOML file in this directory.
- [`results/`](results/) contains one folder per suite config, with a new
  timestamped subfolder for each execution.
- [`results/run_01/2026-09-04_00-44-48/`](results/run_01/2026-09-04_00-44-48/)
  holds the frozen published study. Its exact generated inputs remain in
  [`data/datasets/suites/run_01/`](../data/datasets/suites/run_01/).
- [`results/calibration/`](results/calibration/) preserves the pilot
  measurements that informed the published suite.

Run metadata records the selected config and dataset hashes, environment, source
revision, and result hashes. Use a new config filename when changing a suite in
a way that would produce different datasets for the same case names.

`run_01.toml` preserves the exact suite configuration recorded for the
published run. Its legacy `output_dir` field is retained for historical
provenance; current suite executions use the timestamped layout described above.
