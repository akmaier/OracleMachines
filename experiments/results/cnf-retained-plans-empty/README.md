# Exact retained-plan references: empty

**Optional prepared-history method.** See [mechanism, guarantees and limitations](../../../research/retained-plans.md).

| Measure | Reacquire binary-path graph | Reference prepared closed plans |
| --- | ---: | ---: |
| Structural closures | 88 | 88 |
| Discovery/checking/persistence seconds | 6.362364 | 6.665360 |
| Complete query seconds | 7.709440 | 7.980444 |
| Ordinary solver seconds (including census) | 1.341068 | 1.308832 |
| Combined SQLite bytes | 33,030,144 | 33,456,128 |
| Added SQLite bytes | 33,001,472 | 33,427,456 |
| Cold replay seconds | 3.590121 | 3.633345 |
| Warm replay seconds | 0.024528 | 0.025249 |

These are the same 96 control cases at depth two, with no prepared history. Both close 88 and retain 1,988 nodes. All 1,735 old-policy lookups miss. The added lookup/policy-key cost is retained as a negative control. The timed runner is saved in benchmark-snapshot.py.txt; later changes fix only full/mixed-history benchmark assertions and audit plumbing.

Both modes have the same conditioning/probe/learning budgets and begin with empty checker caches. Total includes preparation, exact-key lookup, full first-use verification, serialization, persistence, ordinary solving and model checks. Seed restoration, cloning, initialization, summary walks, preservation scans, compression, allocation diagnostics and cold/warm replay are excluded or separate. The seed's earlier acquisition and retained bytes remain lifetime costs.

Every old row remains byte-identical. Cold replay verifies both policies, all failed alternatives, exact source bindings and ordinary solver proofs; database bytes remain unchanged. Warm replay inserts no rows. No new SAT decision rule or uniform arbitrary-SAT bound is claimed. Full-source references require exact normalized CNF, depth and fixed old policy. Already-cached misses do not automatically upgrade when new preparation arrives later.

`references.json` records the actual referenced proof kinds and wrapper bytes. Six-case (full) or four-case allocation excludes native SQLite, RSS and full-history peak. Single synthetic comparisons are not significance estimates. All **469 Python tests** and the unchanged Lean build/axiom audit pass (4,148 declarations / 1,988 theorems).

Reproduce with a new output directory:

```sh
python3 experiments/compare_cnf_retained_plans.py --suite empty --output /tmp/retained-plans-empty
python3 experiments/analyze_cnf_retained_plans.py /tmp/retained-plans-empty
```
