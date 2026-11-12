# Coupled pivots from the complete original-input history

Frozen search code: `b79c757`. Reproduce from the repository root:

```sh
python3 experiments/compare_cnf_coupled_pivots.py experiments/results/NEW-DIRECTORY
```

The seed contains every earlier pivot and ancestor-schedule result. Four retained
divergent routes, eight new coupled trials and 32 newly entered recognition states
per open input bound this search. The state guard includes recursive descendants
and unfinished ancestors; pair/candidate/growth caps remain 64 / 64 / 2 per step.

The run adds **25 trials / 32 nodes**, retaining **31/83** structural closures.
No input reaches the state cap (maximum 11). Resident expansion is 0.62200 seconds,
after 69.09120 seconds of seed verification; full cold audit takes 114.39522 and
separate trial replay 69.81471 seconds. These are separate paid phases, not a
subsecond cold-start SAT result. All prior rows survive.

`continuation-analysis.json` compares against each retained first route and the
entire seed: 17/25 frontiers match their first route, and 24/25 contain only seed
leaves. Exactly one new unresolved core appears. Its full CNF and all inspected
pairs are in `core-admission-audit.json`: 35 variables, 150 clauses, minimum
first-step growth three, minimum pair growth seven, interacting minimum fifteen.
All 662 permitted ordered pairs exceed net growth four. This diagnostic makes
no recognizer call and supplies no closure or general SAT lower bound.

The emitted five-table delta contains only new rows. Restore the full frontier
union with `restore_seed`, then use `apply_coupled_delta`, not the older four-table
helper. Check the compressed/unpacked hashes and final table digests. Complete
cold verification, separate old/coupled replay, reconstruction and idempotence
passed. The endpoint archive is an empty initialized store, not new solved evidence.
