# Saved probe effects: frontier comparison

**Decision: optional, not promoted.** See the [proof and resource account](../../../research/probe-rank.md).

These two runs reverse execution order while keeping the policy and budgets fixed. The sibling directory ending in `-reverse` is the second run; the exact order is recorded in each report. Each mode starts from an empty archive.

| Measure | Baseline | Probe ranking |
| --- | ---: | ---: |
| Mean discovery seconds | 5.198541 | 5.449083 |
| Mean total seconds | 8.223418 | 8.633905 |
| Mean ordinary solver seconds | 3.001884 | 3.158242 |
| Closed inputs | 60 | 60 |
| SQLite bytes | 35,840,000 | 35,979,264 |
| Pattern nodes | 1,540 | 1,524 |
| Selected unresolved leaves | 54 | 54 |
| Their literal occurrences | 13,755 | 13,755 |
| Mean cold seconds | 3.499693 | 3.581641 |
| Mean warm seconds | 0.027193 | 0.027932 |

Four-case peak traced Python allocation in the first run: 2,902,681 -> 2,910,797 bytes. This is not full-process or full-corpus memory.

No coverage gains or losses occur. All SAT answers and root profiles agree. Cold checks leave each database byte-identical; warm replay inserts nothing. Each policy produces the same archive bytes in both execution orders. Previous results are preserved.

The ranking only promotes an existing candidate with positive original unit counts in both branches. It adds no probe or SCC discovery and no duplicate unit proof. Missing effects stay unknown; continuations over augmented sources are excluded. The checker validates source-bound traces before reconstructing the order.

The 106 prior frontier leaves each receive one additional conditioning level in both modes. This is development data and gives no new original-source closure count. Twenty-six OR nodes reorder, but both policies try 268 candidates. The optional policy has fewer nodes but more bytes. The old winning cases 4, 17 and 50 remain closed.

Two samples are not significance estimates. Total includes discovery/checking, serialization, SQLite, the ordinary solver and model lifts. Loading, summaries, hashing and compression are excluded; initialization, warm and cold are separate. Four-case Python allocations exclude native SQLite, RSS and whole-suite peak. Different policy keys duplicate unchanged state, so historical storage is not freed.

`report.json` retains cases, per-query records, fingerprints and all archives; `summary.json` aggregates timing and costs. `mechanisms.json` binds the checked archive/report and records every acquired OR source, original unit counts, unknowns, candidate orders and first successful alternatives. All 453 Python tests pass. Lean proves candidate membership and local closure invariance under explicit branch hypotheses; Python refinement and global resource guarantees remain open.

Reproduce into new directories:

```sh
python3 experiments/compare_cnf_probe_rank.py --suite frontier --output /tmp/probe-rank-frontier
python3 experiments/compare_cnf_probe_rank.py --suite frontier --reverse --output /tmp/probe-rank-frontier-reverse
python3 experiments/analyze_cnf_probe_rank.py /tmp/probe-rank-frontier
```
