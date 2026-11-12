# Independent reconstruction index: negative empty-history control

Implementation `f6fb244`; execution order scan then indexed. Both modes use the
accounted solver and the same prepared-probe policy, starting with empty evidence.
The 96 previously published controls cover 12/24/40 variables, signed variants,
edits and disjoint Horn mixtures (seed 202611091650). They are not an independent
holdout. Depth is two, probe/learn limits four. Both modes close 88 inputs.

| Measure | Previous scan | Checker index |
| --- | ---: | ---: |
| Discovery seconds | 6.36510 | 6.63704 |
| Total query seconds | 7.54255 | 7.89263 |
| Full cold audit seconds | 3.62441 | 3.76949 |
| Warm combined seconds | 0.05138 | 0.04793 |
| Final database bytes | 33460224 | 33460224 |
| Four-case Python peak bytes | 615971 | 738163 |

The index hits only 658 times in 15,071 checks. Source preparation visits
4,054,848 literals and affected-clause reconstruction another 471,454, compared
with 4,173,407 in the previous scan. It therefore does more literal work and
regresses in measured time and sampled memory. It remains optional and unpromoted.

All paired roots, profiles, summaries, decisions, solver counters and per-query
archive totals match. Both raw databases are byte-identical. All three evidence
table digests match; cold audits verify every node/source/residual, SQLite integrity
and byte-preserving replay. Both complete archives and all per-query inputs/results
are retained. The final validation is in the adjacent profile directory.

Query timers charge lookup, preparation, checking, persistence, solving and root
lifts. Initialization, compression, cold audit and small-prefix allocation are
separate report fields. Python allocation excludes native SQLite, RSS and full-history
peak. These are single ordered synthetic comparisons; timings do not imply a stable
general slowdown. They provide no reason to promote the candidate. Larger prepared
workloads were not benchmarked after this failed control and the negative pilot.

```sh
python3 experiments/compare_cnf_indexed_check.py --suite empty --output /tmp/cnf-indexed-check-empty-rerun
```
