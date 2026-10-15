# Research benchmark: 2026-09-04

This directory is the self-contained research bundle for the benchmark
highlighted in the repository [`README.md`](../../README.md) and documented in
detail in [`BENCHMARK.md`](../../BENCHMARK.md).

- [`suite.py`](suite.py) retains the documented command for the benchmark suite
  implemented in `sudoku_benchmark_lab.benchmark.suite`.
- [`verify_readme.py`](verify_readme.py) derives the root README highlights and
  compact results from the summary CSVs, then checks that the detailed
  `BENCHMARK.md` tables are copied exactly from the saved generated table.
- [`final_benchmark.toml`](final_benchmark.toml) is the active case matrix for
  reproducing the study in a new output directory.
- [`calibration/`](calibration/) contains both bounded pilot studies, their
  mechanical summary, and the rationale for the final sample sizes/timeouts.
- [`final/`](final/) contains the frozen configuration snapshot, exact selected
  datasets, raw solver attempts, summary CSVs, generated README tables, and
  environment/provenance metadata.

The reusable runner and reporting code remain under `benchmark/`. From the
repository root, reproduce the suite with:

```bash
.venv/bin/python -m data.research_benchmark.suite \
  --config data/research_benchmark/final_benchmark.toml \
  --output-dir /tmp/sudoku-benchmark-reproduction
```

The immutable `final/suite_config.toml` snapshot retains the output path used
when the run was created, and `final/metadata.json` retains the suite source path
and hash recorded at run time. The active files were subsequently organized
into this directory; no measured results or generated tables were changed.
