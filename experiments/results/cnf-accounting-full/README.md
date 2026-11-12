# Transactional residual accounting: full control

Matched 1497-input comparison with the same retained-plan policy and 417,370,112-byte prepared seed. Execution order: census, accounted.

| Measurement | Full census | Maintained counters |
|---|---:|---:|
| Queries | 1,497 | 1,497 |
| Closed | 1,414 | 1,414 |
| Query time (s) | 171.12270 | 87.88366 |
| Discovery (s) | 80.99467 | 81.41598 |
| Ordinary solver (s) | 90.03441 | 6.40760 |
| Initialization (s) | 0.00098 | 0.12228 |
| Warm combined replay (s) | 84.36440 | 0.61496 |
| SQLite bytes | 629,276,672 | 629,280,768 |
| Separate cold solver open (s) | 0.08662 | 0.14813 |
| Full cold evidence audit (s) | 84.49631 | 79.18184 |
| Small-prefix Python peak (bytes) | 24,159,525 | 24,164,413 |

All per-query answers, source-bound plans, profiles, summaries, search counters and exact archive totals agree. All three evidence tables have identical sorted key/payload digests; every original row is preserved. The independent full cold audits pass and leave archive bytes unchanged.

The accounted path performs one opening census and no reconstruction in query or warm replay. Independent validation scans, cold audits, row-preservation checks, compression and allocation diagnostics are outside query timing and separately reported. Original preparation is retained history, not free preprocessing. Warm replay includes both discovery and solver; older discovery-only warm measurements are not its comparator. Python allocation excludes native SQLite, RSS and full-history peak.

These are single comparisons. The fresh/empty controls reuse the previously published 96-input sample, not an independent holdout. The same search and proof checking remain in both modes. Counter maintenance does not establish new coverage or a general SAT bound.

Artifacts: [report](report.json), [summary](summary.json), [census archive](archive-census.sqlite3.gz), [accounted archive](archive-accounted.sqlite3.gz). Runtime file hashes, raw/compressed archive hashes, timing scopes, seed provenance and all query records are retained.

Reproduce: `python3 experiments/compare_cnf_accounting.py --suite full --output NEW_DIRECTORY`.

See [mechanism, invariant and limitations](../../../research/residual-accounting.md).
