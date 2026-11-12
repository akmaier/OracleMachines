# Transactional residual accounting: fresh control

Matched 96-input comparison with the same retained-plan policy and 417,370,112-byte prepared seed. Execution order: accounted, census.

| Measurement | Full census | Maintained counters |
|---|---:|---:|
| Queries | 96 | 96 |
| Closed | 88 | 88 |
| Query time (s) | 15.20412 | 8.38678 |
| Discovery (s) | 7.27256 | 6.87997 |
| Ordinary solver (s) | 7.92061 | 1.50081 |
| Initialization (s) | 0.00071 | 0.05278 |
| Warm combined replay (s) | 6.36229 | 0.05113 |
| SQLite bytes | 450,826,240 | 450,830,336 |
| Separate cold solver open (s) | 0.00502 | 0.06220 |
| Full cold evidence audit (s) | 53.11792 | 50.56766 |
| Small-prefix Python peak (bytes) | 615,349 | 620,357 |

All per-query answers, source-bound plans, profiles, summaries, search counters and exact archive totals agree. All three evidence tables have identical sorted key/payload digests; every original row is preserved. The independent full cold audits pass and leave archive bytes unchanged.

The accounted path performs one opening census and no reconstruction in query or warm replay. Independent validation scans, cold audits, row-preservation checks, compression and allocation diagnostics are outside query timing and separately reported. Original preparation is retained history, not free preprocessing. Warm replay includes both discovery and solver; older discovery-only warm measurements are not its comparator. Python allocation excludes native SQLite, RSS and full-history peak.

These are single comparisons. The fresh/empty controls reuse the previously published 96-input sample, not an independent holdout. The same search and proof checking remain in both modes. Counter maintenance does not establish new coverage or a general SAT bound.

Artifacts: [report](report.json), [summary](summary.json), [census archive](archive-census.sqlite3.gz), [accounted archive](archive-accounted.sqlite3.gz). Runtime file hashes, raw/compressed archive hashes, timing scopes, seed provenance and all query records are retained.

Reproduce: `python3 experiments/compare_cnf_accounting.py --suite fresh --reverse --output NEW_DIRECTORY`.

See [mechanism, invariant and limitations](../../../research/residual-accounting.md).
