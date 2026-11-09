# Pilot: local learned hints and original-source child cores

9 November 2026. The new policy consumes selected hints in the current checked
continuation, keeps their proofs at the parent, then acquires only the restricted
or substituted original-clause core. Descendants rediscover hints; no inherited
hint context is silently omitted from a key. Terminal conflicts remain false.
The independent decision solver, earlier priorities and local budgets are unchanged.

| Mode | Closed / 3 | Total seconds | SQLite bytes | Cold seconds | Pattern nodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solver | -- | 0.07595 | 409,600 | 0.04838 | -- |
| First four clauses | 1 | 1.40035 | 3,936,256 | 0.62316 | 307 |
| Selected clauses, old choices | 1 | 1.39624 | 3,887,104 | 0.66434 | 322 |
| Parent-scoped hints, core child | 2 | 1.32145 | 3,600,384 | 0.59726 | 279 |

Baseline closes 956 only, fixed order closes 1024 only, and core closes both.
Source 1189 remains structurally unresolved. All original decisions agree with
the independent solver, which keeps 86 residuals per mode. The selected pilot
does not establish general coverage or performance.

Discovery is 1.32889 / 1.32971 / 1.24774 s for baseline/fixed/core; logical node
bytes are 2,177,394 / 2,165,706 / 1,981,557. The separate three-case Python peak
is 9,571,051 / 9,563,744 / 8,911,262 bytes, excluding native SQLite, RSS and
full-corpus peak. Core reconstruction/checking runs 45 times and omits 129 clause
occurrences / 258 literal occurrences across those calls; these are not unique
clauses or a count of source gains. All parent proofs remain saved.

Four archives cold-replay byte-identically; warm reuse inserts nothing. These
are single sequential synthetic samples without concurrent tests, builds or
commits. The [full comparison](../cnf-learning-core/README.md) includes all earlier
inputs, fresh random sources, growing/signed/edited controls and failures.

```sh
python3 experiments/compare_cnf_learning_core.py --pilot --output /tmp/new-core-pilot
```
