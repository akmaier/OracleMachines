# Bounded pivot expansion: interacting-pivots / fresh

This is incremental acquisition from the specified paid archive, not a fresh-solving speedup.
At most four earlier open elimination ancestors and eight full target recognitions per unresolved original; pair/growth caps are unchanged.
The interaction-first policy was chosen after examining the first development run. Neither input set is an untouched holdout.

| Measurement | Value |
|---|---:|
| Inputs | 96 |
| Final structural closures | 88 |
| New original closures | 0 |
| Trial attempts | 56 |
| Unique persisted trials | 40 |
| New pattern nodes | 117 |
| Restore/clone seconds | 0.43335 |
| Requested base-source verification seconds | 5.37474 |
| Resident expansion seconds | 0.91811 |
| Warm recomposition seconds | 0.00225 |
| Old-row preservation seconds | 1.56840 |
| Delta writing/compression seconds | 0.39888 |
| Rebuild/logical comparison seconds | 0.68803 |
| Full cold audit seconds | 51.12259 |
| Separate trial/recomposition audit seconds | 5.81798 |
| Paid base bytes | 465776640 |
| Expanded working SQLite bytes | 468176896 |
| Delta SQLite bytes | 2437120 |
| Compressed delta bytes | 112449 |
| Exact source-frontier reconvergences | 32 |
| Novel distinct selected leaves | 5 |

Reproduce: `python3 experiments/compare_cnf_interacting_pivots.py experiments/results/cnf-interacting-pivots-fresh --suite fresh` (choose a new output directory).

`report.json` binds the base archive, source checkpoint, fingerprints, exact inputs, budgets, phase costs and delta hashes.
`proof-delta.sqlite3.gz` contains only new pattern/trial rows. Restore the exact base archive recorded in the report, verify both hashes, then apply the delta with `apply_delta` in the experiment runner.
Every pre-existing row survives. Cold replay validates old/new nodes, original source bindings, solver proofs, and the separate trial certificates without byte changes.
Logical table hashes describe reconstruction; SQLite page layouts need not match after applying rows in a different order.

`frontier-analysis.json` is a separately timed read-only analysis of selected unresolved canonical leaf multisets, retaining multiplicity and each path's variable bindings.
All immediate target roots are new. Their descendant reuse and identical final frontiers are not claims about all possible pivot orders.

No replacement closes in this run. The endpoint-reference file is an empty initialized store and contains no new SAT/UNSAT evidence.
Full cold audit and trial/recomposition audit overlap in the old dependencies they check; both phase times are charged separately.
The trial cap does not bound inherited recognition work, full proof-graph growth or process memory. Peak RSS/native memory is unmeasured.
Existing archive creation and earlier endpoint proofs remain paid historical costs. No default solver or full-corpus coverage change follows.
