# Transported support partition pilot

See [the research account](../../../research/transported-support-partition.md)
for scope, results, regressions and the next target. This is a supplied-candidate
residual pilot. Every arm solves all nine targets. The affine policy remains the
baseline; automatic discovery and source-level integration are still open.

- `protocol.json`: frozen policies, source fingerprints, historical bindings,
  exact prefixes, budgets, two opposite orders and limitations.
- `prefix-*.json.gz`: dependency-ordered proof rows available before the original
  source query. No later work is used to seed a worker.
- `cases.json`: three selected historical residuals and six fixed edits.
- `historical-*` and `edits-*`: separate worker reports, query logs, proof deltas,
  partition sidecars and warm results. Combine each delta with its bound prefix
  using `compare_cnf_transported_partition.restore` to reconstruct a trial.
- `analysis.json`: aggregate and per-case costs, per-edit routes/expansions,
  branch structural counters, paired differences and limitations. The deletion
  in case 31 falls back at six missing clauses; its gain comes from the addition.
- `next-boundary.json`: read-only six-clause deletion screening from the prefix
  plus first addition, excluding deletion results. No search or publication.
- `union/`, `union-partitions.json`, `checkpoint.json`: cumulative native proof
  authority and checked compositions. Every earlier payload stays authoritative;
  alternative trial proofs remain in the deltas.
- `validation.json`, `checks.json`, `manifest.json`: chronological/prefix audits,
  historical replay, tests, build and source/artifact hashes.

The archived delta plus raw partition sidecar grows despite smaller native proof
payloads. Warm-bank setup also costs more. The small complete-time differences
are observations from two repeats, not robust deployment evidence.

From the repository root, reproduce into a new output directory:

```sh
python3 experiments/compare_cnf_transported_partition.py prepare /tmp/oracle-partition-repeat
python3 experiments/compare_cnf_transported_partition.py /tmp/oracle-partition-repeat
python3 experiments/analyze_cnf_transported_partition.py /tmp/oracle-partition-repeat
python3 experiments/validate_cnf_transported_partition.py /tmp/oracle-partition-repeat
```

The preflight is descriptive, uses the final archive, and is excluded from
comparative timings. The independent validator recomputes supports from prefixes.
`initial-tests/` and `development-tests.log` preserve the first fixture failure;
`development-tests-fixed.log` records its correction before timing.
