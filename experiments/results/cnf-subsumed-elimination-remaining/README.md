# Subsumption fallback on 59 remaining selected leaves

Runtime checkpoint `14ae642`. Baseline is the previous bounded-elimination
policy; the candidate adds retained-source-clause subsumption only after that
terminal rule returns a null proposal. Execution order: baseline, subsumed.
Both modes start from empty history with conditioning depth zero. These are
the 59 saved leaves remaining after bounded elimination, not a fresh holdout.

| Measurement | Previous bounded policy | Subsumption fallback |
| --- | ---: | ---: |
| Closures | 0 | 0 |
| Selected open leaves | 59 | 59 |
| Selected open literals | 26,205 | 26,181 |
| Total query seconds | 2.88938 | 3.12938 |
| Discovery seconds | 0.58286 | 0.81040 |
| Complete database bytes | 17,969,152 | 18,169,856 |
| Pattern nodes | 59 | 70 |
| Cold audit seconds | 1.12372 | 1.20431 |
| Warm combined seconds | 0.03618 | 0.04031 |
| Four-source peak Python bytes | 1,919,676 | 1,921,585 |

There are no new closures and no lost closures. The candidate acquires 10
new subsumed elimination edges, with independent source/target decisions and SAT
model lifts checked on all of them (8 SAT / 2 UNSAT). This extra
diagnostic takes 0.55848 seconds outside query acquisition. Existing-rule
edges receive complete cold proof checking; their additional endpoint/model
diagnostic is not repeated in this comparison.

The fallback tests 2,726 candidates, rejects
2,716 for growth and performs 255,149
subset tests. Counts include unsuccessful and unselected alternatives, not only
final selected proof paths. The original-input decision solver and its search
counters are unchanged. Query time charges recognition, checking, persistence,
ordinary solving and successful root lifts.

`report.json` retains per-query outcomes, counters, complete compressed archives,
source/history preservation checks, cold audits, additional model diagnostics
and allocation samples. `summary.json` aggregates these observations. Restore,
clone, opening, selected-frontier walks, archive compression, cold audit and model
diagnostics are outside query timing and reported separately. Allocation samples
the same first four queries, excluding native SQLite, RSS and full-history peak.

The opposite-order run has identical database bytes and hashes for each mode,
with the same ten new subsumed steps, zero closures and 24-literal reduction.
Both orders cost more overall. The small comparison establishes neither a
general slowdown nor a whole-input closure result.

All complete cold audits leave bytes unchanged. The optional candidate is not
promoted. See [the mechanism, proof scope and next gap](../../../research/subsumed-elimination.md)
and [aggregate validation](../cnf-subsumed-elimination-validation/README.md).

```sh
python3 experiments/compare_cnf_subsumed_elimination.py --suite remaining --output /tmp/subsumed-remaining-new
```

Run timed comparisons without concurrent tests, builds, profiling or archive
analysis. Use new destinations to preserve the earlier experiments.
