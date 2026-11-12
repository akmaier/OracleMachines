# Subsumption fallback on 83 original prior misses

Runtime checkpoint `14ae642`. Baseline is the previous bounded-elimination
policy; the candidate adds retained-source-clause subsumption only after that
terminal rule returns a null proposal. Execution order: baseline, subsumed.
Both modes restore the same paid 417,370,112-byte prefix and conditioning
depth two. This is the earlier 83-miss subset, not a new full-corpus run.

| Measurement | Previous bounded policy | Subsumption fallback |
| --- | ---: | ---: |
| Closures | 29 | 29 |
| Selected open leaves | 59 | 59 |
| Selected open literals | 26,205 | 26,181 |
| Total query seconds | 79.65962 | 88.16727 |
| Discovery seconds | 77.92568 | 86.41462 |
| Complete database bytes | 621,146,112 | 628,133,888 |
| Pattern nodes | 34,514 | 34,692 |
| Cold audit seconds | 79.17392 | 81.08654 |
| Warm combined seconds | 0.07768 | 0.07864 |
| Four-source peak Python bytes | 16,820,009 | 15,136,923 |

There are no new closures and no lost closures. The candidate acquires 324
new subsumed elimination edges, with independent source/target decisions and SAT
model lifts checked on all of them (217 SAT / 107 UNSAT). This extra
diagnostic takes 33.47933 seconds outside query acquisition. Existing-rule
edges receive complete cold proof checking; their additional endpoint/model
diagnostic is not repeated in this comparison.

The fallback tests 86,305 candidates, rejects
85,902 for growth and performs 8,639,284
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

All 22,071 old pattern nodes, 1,465 source rows and 21,838 residual rows survive.
The baseline reproduces the preceding bounded-elimination database exactly.
Both modes close the same 29/83 and leave 54 sources unresolved. This negative
control does not justify promotion or another full-corpus/fresh-holdout run.

`growth-opportunity.json` is a subsequent read-only diagnostic, bound to its
script and the two reports. It finds candidates with non-growing clause count
in 48/59 remaining leaves without subsumption or 49/59 with it, if up to eight
extra literals are allowed. It implements no such policy and measures no new
closures. `growth-opportunity-initial.json` and `growth-analysis-initial.py`
preserve the initial subsumption-only diagnostic before adding the plain-rule
ablation. The snapshot script needs `PYTHONPATH=.` when run from this checkout;
use a new output path. The current analyzer lives under `experiments/`.

All complete cold audits leave bytes unchanged. The optional candidate is not
promoted. See [the mechanism, proof scope and next gap](../../../research/subsumed-elimination.md)
and [aggregate validation](../cnf-subsumed-elimination-validation/README.md).

```sh
python3 experiments/compare_cnf_subsumed_elimination.py --suite originals --output /tmp/subsumed-originals-new
```

Run timed comparisons without concurrent tests, builds, profiling or archive
analysis. Use new destinations to preserve the earlier experiments.
