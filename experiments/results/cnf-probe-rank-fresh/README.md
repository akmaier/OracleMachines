# Saved probe effects: fresh comparison

**Decision: optional, not promoted.** See the [proof and resource account](../../../research/probe-rank.md).

These two runs reverse execution order while keeping the policy and budgets fixed. The sibling directory ending in `-reverse` is the second run; the exact order is recorded in each report. Each mode starts from an empty archive.

| Measure | Baseline | Probe ranking |
| --- | ---: | ---: |
| Mean discovery seconds | 1.781130 | 1.791209 |
| Mean total seconds | 3.074635 | 3.075017 |
| Mean ordinary solver seconds | 1.288604 | 1.278296 |
| Closed inputs | 71 | 71 |
| SQLite bytes | 15,417,344 | 15,585,280 |
| Pattern nodes | 684 | 684 |
| Selected unresolved leaves | 23 | 23 |
| Their literal occurrences | 7,819 | 7,819 |
| Mean cold seconds | 1.218140 | 1.216324 |
| Mean warm seconds | 0.024756 | 0.025116 |

Four-case peak traced Python allocation in the first run: 695,542 -> 698,770 bytes. This is not full-process or full-corpus memory.

No coverage gains or losses occur. All SAT answers and root profiles agree. Cold checks leave each database byte-identical; warm replay inserts nothing. Each policy produces the same archive bytes in both execution orders. Previous results are preserved.

The ranking only promotes an existing candidate with positive original unit counts in both branches. It adds no probe or SCC discovery and no duplicate unit proof. Missing effects stay unknown; continuations over augmented sources are excluded. The checker validates source-bound traces before reconstructing the order.

The 96 fresh cases use the frozen seed 202611091730 and 12/24/40 variables, signed permutations, edits and disjoint mixtures. None of 39 OR states changes order. Thirty-six have no binary clauses, and 147/156 candidate positions have no original paired traces. This absence of reusable single-assumption information is the main finding.

Two samples are not significance estimates. Total includes discovery/checking, serialization, SQLite, the ordinary solver and model lifts. Loading, summaries, hashing and compression are excluded; initialization, warm and cold are separate. Four-case Python allocations exclude native SQLite, RSS and whole-suite peak. Different policy keys duplicate unchanged state, so historical storage is not freed.

`report.json` retains cases, per-query records, fingerprints and all archives; `summary.json` aggregates timing and costs. `mechanisms.json` binds the checked archive/report and records every acquired OR source, original unit counts, unknowns, candidate orders and first successful alternatives. All 453 Python tests pass. Lean proves candidate membership and local closure invariance under explicit branch hypotheses; Python refinement and global resource guarantees remain open.

Reproduce into new directories:

```sh
python3 experiments/compare_cnf_probe_rank.py --suite fresh --output /tmp/probe-rank-fresh
python3 experiments/compare_cnf_probe_rank.py --suite fresh --reverse --output /tmp/probe-rank-fresh-reverse
python3 experiments/analyze_cnf_probe_rank.py /tmp/probe-rank-fresh
```
