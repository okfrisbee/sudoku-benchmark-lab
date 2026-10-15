# Data layout

Project datasets and benchmark outputs live here:

- `datasets/` contains JSONL datasets created from the interactive menu or
  generator API.
- `results/data/` and `results/summary/` contain ad hoc benchmark CSV output.
- [`research_benchmark/`](research_benchmark/) is the curated study behind the
  repository documentation. It groups the calibration evidence, suite command,
  published-table checker, frozen benchmark configuration, selected datasets, and final
  results.

The complete `data/` tree is eligible for version control. Review newly
generated datasets and ad hoc results before committing them.
