# Diagnostic profiles for the structural-reuse cost map

Five fresh archives were generated using solver checkpoint
`fc52bfe3d509af6700199946ab775ac6ce4af024`. The purpose is to identify costs that
remain after the preceding pure-repair improvement, not to claim a new speedup.
Recipes come from repair-history cases 8, 13, 18 and 19 and residual-DAG case 20.

| Recipe | Profiled seconds | Fallbacks | Main observation |
| --- | ---: | ---: | --- |
| Size-16 matching SAT + 128 fresh positive units | 0.09224 | 0 | Preparation, normalization and persistence remain after all repeated acquisitions are avoided. |
| Blocked-but-SAT, 32 pairs | 0.07096 | 32 | `prepare` remains on the update path; no improvement from purity on safe nonpure flips. |
| 32 identifiers near 2^1024 | 0.04390 | 0 | `map_get` + `map_set` use about 62% of exclusive time. |
| UNSAT base + 128 additions | 0.03224 | 0 | SQLite execute + transaction-context exit use about 87% of exclusive time. |
| Seeded 3-CNF, 12 variables, case 20 | 0.01692 | N/A | Branching, normalization, restriction and certificate persistence all occur; too small to represent hard general SAT. |

`report.json` retains the leading 15 exclusive and cumulative function entries
per sample and the SHA-256 of each decompressed SQLite archive. The compressed
archives preserve the newly acquired results. Correct answers were checked
against the retained recipes; final history sources and SAT witnesses were
checked after profiling. A separate cold replay is recorded in
`archive-replay.json`: all 356 versions and all 58 residual rows across the five
archives checked successfully, with zero new expansions and identical database
bytes after replay.

These are single cProfile runs. Instrumentation changes performance, particularly
for many small Python operations. Exclusive/self times may be added for disjoint
functions; cumulative times include nested calls and must not be summed or
treated as disjoint phases. SQLite execute includes more than disk I/O, and
transaction-context exit includes commit handling. No claim about fsync latency
alone follows.

History profiles include base preparation, accepted updates, rejected attempts
and materialization/acquisition fallback. Archive setup/opening and final source
and witness exports, digests, compression and cold replay are outside the timed
region. The generic residual profile covers `solve`. Memory observations in the
cost map come from the preceding separate allocation study, not these profiles.
The initial run used the same operations before the runner gained a mandatory
fresh output directory and an explicit initial-answer assertion.

Reproduce from the repository root, choosing a nonexistent directory:

```sh
python3 research/evidence/2026-11-08/reuse-cost-profile/run_profiles.py --output /tmp/oracle-reuse-profile-new
```

The runner refuses existing output directories to preserve earlier evidence.
This is an analysis-only checkpoint: no solver semantics, manuscript theorem or
Lean implementation claim changed. See the
[ranked cost map](../../../structural-reuse-priorities.md) for the next experiment.
