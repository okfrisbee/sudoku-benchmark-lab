# Data layout

Project datasets and benchmark outputs live here:

- `datasets/` contains JSONL datasets created from the interactive menu or
  generator API. Suite-generated datasets are grouped under `datasets/suites/`
  by suite config name.
- `results/data/` and `results/summary/` contain ad hoc benchmark CSV output.
- The published suite datasets are in `datasets/suites/run_01/`.

Suite definitions and their result artifacts live under [`experiments/`](../experiments/README.md).

The complete `data/` tree is eligible for version control. Review newly
generated datasets and ad hoc results before committing them.
