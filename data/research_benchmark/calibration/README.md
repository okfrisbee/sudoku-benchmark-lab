# Calibration notes

These files preserve the pilot measurements used to choose the final benchmark
matrix in [`final_benchmark.toml`](../final_benchmark.toml).
They are calibration evidence, not the published benchmark result.

## Studies

The initial sweep used two generated puzzles per clue-density tier and all six
solvers. Cutoffs were 1 second for 9×9 and 16×16, and 2 seconds for 25×25 and
36×36. Dataset seeds began at `2026090400` and incremented in this order:
9×9 easy/medium/hard, 16×16 easy/medium/hard, 25×25 easy/medium/hard, then
36×36 easy/medium/hard.

The extended sweep used independent seeds beginning at `2026091400`, in the
same case order, with this matrix:

| Size | Easy | Medium | Hard | Timeout(s) |
|---:|---:|---:|---:|:---|
| 9×9 | 12 | 12 | 12 | 1 / 1 / 1 s |
| 16×16 | 6 | 6 | 6 | 1 / 2 / 2 s |
| 25×25 | 4 | 4 | 4 | 1.5 / 2.5 / 2.5 s |
| 36×36 | 3 | 1 | 1 | 3 / 3 / 3 s |

## Evidence used for the decision

- On 9×9 easy, the naive median was 0.435, 0.418, and 0.418 ms at cumulative
  sample sizes 3, 6, and 12. On medium it was 0.512, 0.514, and 0.514 ms. The
  solver ordering was also unchanged. This supported one run each over many
  independent puzzles instead of repeated runs of the same tiny workload.
- The 9×9 hard distribution was more skewed: the naive median moved from
  16.7 ms at 3 puzzles to 7.93 ms at 12. The final sample was therefore raised
  to 50 puzzles for every 9×9 tier.
- At 16×16 medium and a 2-second cutoff, CSP, SAT, SMT, and DLX solved 6/6;
  naive solved 6/6 but had a 1.85-second tail, and naive recursive solved 5/6.
  At 16×16 hard, SAT solved 6/6, DLX 5/6, CSP 2/6, and the other three solvers
  0/6. A 2-second cutoff preserves this separation without extending it merely
  to force slower solvers to finish.
- At 25×25 medium and 2.5 seconds, SAT and DLX solved 4/4, CSP 3/4, SMT 2/4,
  and both naive solvers 0/4. On hard, SAT solved 4/4 and DLX 1/4; every other
  solver timed out. The final sample is intentionally small at this cost.
- Dense 36×36 puzzles completed within 1.75 seconds for all solvers in the
  extended sweep. Sparse 36×36 results were dominated by 3-second timeouts,
  so the final suite retains only three medium and three hard puzzles as an
  explicit scaling boundary.
- 4×4 was excluded from performance measurement. Even dense 9×9 procedural
  solves were already sub-millisecond, so 4×4 is useful for correctness tests
  but not for differentiating these implementations.

`initial_raw.csv` and `extended_raw.csv` contain one row per solver attempt.
`summary.csv` is a mechanical group-by summary. Timeout durations in these
pilot files include a small amount of process-termination overhead; final
timeout rows are charged exactly the configured cutoff.
