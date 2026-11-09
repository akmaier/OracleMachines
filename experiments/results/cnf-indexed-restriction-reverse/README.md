# Reverse-order full comparison for indexed restriction

The first full study reduced discovery and cold replay but regressed total time.
This second full study reverses mode order, using the unchanged implementation,
runner, cases and budgets. The combined order is baseline / indexed / indexed /
baseline. All answers, profiles and database bytes still match the previous
archive. Within-mode operation counters and storage repeat exactly across runs.

| Second full sample | Baseline, second | Indexed, first |
| --- | ---: | ---: |
| Total seconds | 142.37374 | 128.27877 |
| Discovery seconds | 100.72151 | 87.66682 |
| Ordinary solver seconds | 41.59385 | 40.54429 |
| Cold replay seconds | 61.47054 | 57.36231 |
| Warm replay seconds | 0.27772 | 0.26131 |
| Initialization seconds | 0.24576 | 0.00167 |
| Six-case Python peak bytes | 22,474,570 | 24,072,950 |

Together with the [first study](../cnf-indexed-restriction/README.md), means are
137.36963 -> 131.36045 s total, 97.29044 -> 89.16122 s discovery and 61.16937 ->
56.70501 s cold replay. This is 4.37%, 8.36% and 7.30% less respectively. The
ordinary solver mean is instead 40.02449 -> 42.13410 s. Two samples per mode
balance order but do not establish significance, industrial performance or a
pointwise speed guarantee. The first-run total regression is preserved.

Each mode checks all 25,047 nodes, 1,465 source bindings and 21,838 solver
residuals cold without modifying the existing 437,620,736-byte archive. The
archive is referenced, not duplicated. All 70 report fingerprints and the order
wrapper's script/runner/report hashes are recorded. See the first study for
independent tests, correctness conditions, locality regressions and profiling.

Reproduce after the primary result exists, with a fresh output path:

```sh
python3 experiments/recheck_cnf_indexed_restriction_full.py --output /tmp/new-indexed-full-reverse
```
