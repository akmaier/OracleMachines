# Prepared probe reuse: full matched comparison

Implementation checkpoint: `836fb96`. Optional `PreparedProbeInventory` versus
`RetainedPlanInventory`; both use `AccountedResidualSolver`. Execution order:
reuse then rediscover. Settings: depth 2, probe limit 4,
learn limit 4. Other settings and exact runtime hashes are in `report.json`.

The same 417,370,112-byte previously acquired archive is restored and cloned for each mode. Its original construction and retained storage remain charged as prior history.

The original 1,497 sources include 512 exhaustive tiny CNFs and 985 larger inputs. Non-tiny closure stays 902/985, with the same 83 open sources and earlier 99 selected leaves / 31,203 literals.

| Measure | Rediscover | Reuse |
| --- | ---: | ---: |
| Queries | 1497 | 1497 |
| Structural closures | 1414 | 1414 |
| Total query seconds | 85.97296 | 84.07622 |
| Discovery seconds | 79.80360 | 78.51427 |
| Ordinary solver seconds | 6.11058 | 5.50420 |
| Initialization seconds | 0.10039 | 0.15712 |
| Warm combined seconds | 0.59213 | 0.58386 |
| Full cold audit seconds | 77.21884 | 76.58480 |
| Final database bytes | 629280768 | 629280768 |
| Sampled peak Python bytes | 24164349 | 24199805 |
| prepared_probe_reuses | 0 | 2437 |
| prepared_probe_attempts_reused | 0 | 15454 |
| probe_attempts | 77804 | 60972 |
| verified_probe_attempts | 77498 | 77498 |
| ordered_propagation_calls | 109950 | 92273 |
| checked_probe_lookup_calls | 22492 | 24929 |
| checked_probe_misses | 11339 | 11340 |
| checked_probe_hits | 11153 | 13589 |
| checked_probe_key_bytes | 69146160 | 76712050 |

The deterministic acquisition reduction is substantial, but timing changes are modest: fresh probe attempts fall 21.63%, discovery time 1.62%. Full independent verification still checks 77,498 attempts. Total timing includes variation in the unchanged ordinary solver, whose counters match. The new source-binding visits total 838,095 literals. There is no storage or demonstrated memory saving.

Query timers include acquisition, lookup, checking, persistence, ordinary solving
and root/model lifts. Opening, seed restoration/cloning, compression, row-preservation
checks and cold replay are separate fields in the report. Warm replay includes
discovery and the ordinary solver. Peak allocation uses only the reported small
prefix ([858, 875, 907, 970, 1042, 1061]); it excludes native SQLite, RSS and full-history
peak. These single ordered synthetic runs establish no statistical speedup.

Every paired root, profile, summary, answer, residual archive total and solver
counter agrees. All three evidence-table digests match, all prior rows survive,
and the complete final database hashes agree between modes. Both cold audits check
every old and new stored node/source and ordinary residual proof, preserve database
bytes and pass SQLite integrity checks. Compression retains both complete archives;
compressed hashes can differ because gzip records the archive filenames.

`report.json` preserves every input and per-query result; `summary.json` includes
phase costs, counters and audit details. Both compressed SQLite archives are retained.
The full experiment directory also contains cost attribution, paired analysis and
validation logs. No new SAT class, certificate format or Lean refinement is claimed.

Reproduce into a new output directory from the repository root:

```sh
python3 experiments/compare_cnf_prepared_probes.py --suite full --reverse --output /tmp/cnf-prepared-probes-full-rerun
```
