# Transactional residual accounting: empty control

Matched 96-input comparison with the same retained-plan policy and empty history. Execution order: accounted, census.

| Measurement | Full census | Maintained counters |
|---|---:|---:|
| Queries | 96 | 96 |
| Closed | 88 | 88 |
| Query time (s) | 7.70202 | 7.73052 |
| Discovery (s) | 6.43240 | 6.47490 |
| Ordinary solver (s) | 1.26394 | 1.24975 |
| Initialization (s) | 0.00061 | 0.00113 |
| Warm combined replay (s) | 0.27283 | 0.05134 |
| SQLite bytes | 33,456,128 | 33,460,224 |
| Separate cold solver open (s) | 0.00408 | 0.00633 |
| Full cold evidence audit (s) | 3.54486 | 3.54443 |
| Small-prefix Python peak (bytes) | 610,579 | 615,595 |

All per-query answers, source-bound plans, profiles, summaries, search counters and exact archive totals agree. All three evidence tables have identical sorted key/payload digests; every original row is preserved. The independent full cold audits pass and leave archive bytes unchanged.

The accounted path performs one opening census and no reconstruction in query or warm replay. Independent validation scans, cold audits, row-preservation checks, compression and allocation diagnostics are outside query timing and separately reported. Original preparation is retained history, not free preprocessing. Warm replay includes both discovery and solver; older discovery-only warm measurements are not its comparator. Python allocation excludes native SQLite, RSS and full-history peak.

These are single comparisons. The fresh/empty controls reuse the previously published 96-input sample, not an independent holdout. The same search and proof checking remain in both modes. Counter maintenance does not establish new coverage or a general SAT bound.

Artifacts: [report](report.json), [summary](summary.json), [census archive](archive-census.sqlite3.gz), [accounted archive](archive-accounted.sqlite3.gz). Runtime file hashes, raw/compressed archive hashes, timing scopes, seed provenance and all query records are retained.

Reproduce: `python3 experiments/compare_cnf_accounting.py --suite empty --reverse --output NEW_DIRECTORY`.

See [mechanism, invariant and limitations](../../../research/residual-accounting.md).
