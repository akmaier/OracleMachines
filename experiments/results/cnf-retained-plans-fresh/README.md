# Exact retained-plan references: fresh

**Optional prepared-history method.** See [mechanism, guarantees and limitations](../../../research/retained-plans.md).

| Measure | Reacquire binary-path graph | Reference prepared closed plans |
| --- | ---: | ---: |
| Structural closures | 88 | 88 |
| Discovery/checking/persistence seconds | 6.575296 | 6.803031 |
| Complete query seconds | 14.100845 | 14.401687 |
| Ordinary solver seconds (including census) | 7.516473 | 7.590010 |
| Combined SQLite bytes | 450,355,200 | 450,826,240 |
| Added SQLite bytes | 32,985,088 | 33,456,128 |
| Cold replay seconds | 49.433765 | 50.315491 |
| Warm replay seconds | 0.025028 | 0.024912 |

These 96 random, signed, edited and disjoint-mixture cases use the earlier binary-path control set, now at depth two. They are fresh relative to the prepared original-corpus seed, not a new independently drawn holdout. Both modes close 88. None of the query roots is a retained reference; all 20 internal references point to family nodes. Both add 1,988 pattern nodes. Discovery and storage regress, so an exact match alone is not evidence that a reference is cheaper.

Both modes have the same conditioning/probe/learning budgets and begin with empty checker caches. Total includes preparation, exact-key lookup, full first-use verification, serialization, persistence, ordinary solving and model checks. Seed restoration, cloning, initialization, summary walks, preservation scans, compression, allocation diagnostics and cold/warm replay are excluded or separate. The seed's earlier acquisition and retained bytes remain lifetime costs.

Every old row remains byte-identical. Cold replay verifies both policies, all failed alternatives, exact source bindings and ordinary solver proofs; database bytes remain unchanged. Warm replay inserts no rows. No new SAT decision rule or uniform arbitrary-SAT bound is claimed. Full-source references require exact normalized CNF, depth and fixed old policy. Already-cached misses do not automatically upgrade when new preparation arrives later.

`references.json` records the actual referenced proof kinds and wrapper bytes. Six-case (full) or four-case allocation excludes native SQLite, RSS and full-history peak. Single synthetic comparisons are not significance estimates. All **469 Python tests** and the unchanged Lean build/axiom audit pass (4,148 declarations / 1,988 theorems).

Reproduce with a new output directory:

```sh
python3 experiments/compare_cnf_retained_plans.py --suite fresh --output /tmp/retained-plans-fresh
python3 experiments/analyze_cnf_retained_plans.py /tmp/retained-plans-fresh
```
