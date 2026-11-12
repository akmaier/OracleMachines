# Prepared probe reuse: fresh matched comparison

Implementation checkpoint: `836fb96`. Optional `PreparedProbeInventory` versus
`RetainedPlanInventory`; both use `AccountedResidualSolver`. Execution order:
rediscover then reuse. Settings: depth 2, probe limit 4,
learn limit 4. Other settings and exact runtime hashes are in `report.json`.

The same 417,370,112-byte previously acquired archive is restored and cloned for each mode. Its original construction and retained storage remain charged as prior history.

These are the 96 previously published fresh-input controls (seed 202611091650), with 12/24/40 variables, signed variants, edits and disjoint Horn mixtures. They are fresh relative to preparation, not an independent holdout. Both modes retain 88 closures.

| Measure | Rediscover | Reuse |
| --- | ---: | ---: |
| Queries | 96 | 96 |
| Structural closures | 88 | 88 |
| Total query seconds | 7.70214 | 8.61204 |
| Discovery seconds | 6.44922 | 7.07650 |
| Ordinary solver seconds | 1.24699 | 1.52934 |
| Initialization seconds | 0.05130 | 0.05516 |
| Warm combined seconds | 0.04877 | 0.05063 |
| Full cold audit seconds | 49.37668 | 49.77160 |
| Final database bytes | 450830336 | 450830336 |
| Sampled peak Python bytes | 620357 | 620565 |
| prepared_probe_reuses | 0 | 0 |
| prepared_probe_attempts_reused | 0 | 0 |
| probe_attempts | 10254 | 10254 |
| verified_probe_attempts | 10248 | 10248 |
| ordered_propagation_calls | 15655 | 15655 |
| checked_probe_lookup_calls | 4361 | 4361 |
| checked_probe_misses | 1886 | 1886 |
| checked_probe_hits | 2475 | 2475 |
| checked_probe_key_bytes | 10885071 | 10885071 |

No prepared probe trace is reused. Discovery and solver work counters match; the observed timing difference cannot be credited to avoided probe acquisition. Preserve this control, including its regression when present, rather than treating the candidate as a general speedup.

Query timers include acquisition, lookup, checking, persistence, ordinary solving
and root/model lifts. Opening, seed restoration/cloning, compression, row-preservation
checks and cold replay are separate fields in the report. Warm replay includes
discovery and the ordinary solver. Peak allocation uses only the reported small
prefix ([0, 1, 2, 3]); it excludes native SQLite, RSS and full-history
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
python3 experiments/compare_cnf_prepared_probes.py --suite fresh --output /tmp/cnf-prepared-probes-fresh-rerun
```
