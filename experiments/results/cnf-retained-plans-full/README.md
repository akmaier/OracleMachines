# Exact retained-plan references: full

**Optional prepared-history method.** See [mechanism, guarantees and limitations](../../../research/retained-plans.md).

| Measure | Reacquire binary-path graph | Reference prepared closed plans |
| --- | ---: | ---: |
| Structural closures | 1,413 | 1,414 |
| Discovery/checking/persistence seconds | 98.336185 | 81.966561 |
| Complete query seconds | 190.634324 | 177.052916 |
| Ordinary solver seconds (including census) | 92.175137 | 94.978687 |
| Combined SQLite bytes | 755,658,752 | 629,276,672 |
| Added SQLite bytes | 338,288,640 | 211,906,560 |
| Cold replay seconds | 95.643973 | 82.523449 |
| Warm replay seconds | 0.273274 | 0.410594 |

The 1,497 cases include 512 tiny cases. Non-tiny closure is **901/985 -> 902/985**, with gain **1471** and no losses. Every earlier baseline closure is also preserved. The common seed is 417,370,112 bytes. Added pattern nodes fall 25,578 -> 13,560, but six-case peak traced Python allocation rises 20,124,942 -> 24,084,738 bytes. The ordinary solver is unchanged. References replace fresh graph acquisition; they do not remove the cost of building the seed.

Both modes have the same conditioning/probe/learning budgets and begin with empty checker caches. Total includes preparation, exact-key lookup, full first-use verification, serialization, persistence, ordinary solving and model checks. Seed restoration, cloning, initialization, summary walks, preservation scans, compression, allocation diagnostics and cold/warm replay are excluded or separate. The seed's earlier acquisition and retained bytes remain lifetime costs.

Every old row remains byte-identical. Cold replay verifies both policies, all failed alternatives, exact source bindings and ordinary solver proofs; database bytes remain unchanged. Warm replay inserts no rows. No new SAT decision rule or uniform arbitrary-SAT bound is claimed. Full-source references require exact normalized CNF, depth and fixed old policy. Already-cached misses do not automatically upgrade when new preparation arrives later.

`references.json` records the actual referenced proof kinds and wrapper bytes. Six-case (full) or four-case allocation excludes native SQLite, RSS and full-history peak. Single synthetic comparisons are not significance estimates. All **469 Python tests** and the unchanged Lean build/axiom audit pass (4,148 declarations / 1,988 theorems).

The timed acquisitions and both cold audits completed before a final tuple/list equality assertion failed. `finish_cnf_retained_plans.py` verifies all canonical profiles/answers and archive hashes, then finalizes the saved records. `benchmark-at-acquisition.py.txt` binds the timed code and `finalization-failure.txt` preserves the failure. Only allocation diagnostics repeat. Original initial restore timing was not checkpointed and remains null; its later allocation-only repeat is separate.

Reproduce with a new output directory:

```sh
python3 experiments/compare_cnf_retained_plans.py --suite full --output /tmp/retained-plans-full
python3 experiments/analyze_cnf_retained_plans.py /tmp/retained-plans-full
```

`profile.json` separately profiles source 1441 and measures the ordinary solver's full-storage metadata census. Its repeated mean is 57.14 ms over 21,838 rows / 65,665,771 payload units. This is bookkeeping, not SAT search. The query-count extrapolation is an estimate, not an exact subtraction from total time.
