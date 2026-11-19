# Bounded affine probing with finite-input snapshots

The [analysis](../../../research/bounded-affine-probe.md) explains the optional
policy, measured results, remaining cases and resource limits. The active solver
is `experiments.cnf_affine_probe_safe.InputSafeAffineProbeSolver`. It snapshots
finite outer/inner CNF iterables, then uses the existing separate affine-negative
checker before planned native acquisition. A consistent subsystem or discovery
budget stop falls back without a verdict.

Twelve serial workers compare witness-only retrieval, planned negative reuse and
the probe in opposite orders. Exposed sizes are 42/66/90; fresh sizes are
96/108/120. Each stream has 108 attempts/72 roots from six designed generators,
two samples and base/edit/repeat variants. Policy/source hashes are frozen before
timing. No generator labels or donor relationships enter search.

Normalized-source limits are 256 variables, 4,096 clauses and 16,384 literals;
discovery stops before exceeding 65,536 row XORs. Copying, canonicalization,
stored-proof checking, publication, native fallback and the whole retained archive
are outside these discovery limits. Every arm creates the empty affine table.
Native proofs never gain affine dependencies. Ordinary native batching remains
unchanged; an affine proof commits immediately on the idle owned connection.

The complete worker charges snapshotting, setup, successful/failed probes,
elimination, independent checking, publication, fallback, graph sizing, warm/cold
replay, cold reconstruction, sidecars and compression. Preparation and posthoc
audits are separate. RSS includes harness and replay objects. These constructed
size splits are not representative external benchmarks or unrestricted SAT bounds.

## Reproduce

Use a fresh destination from the repository root:

```sh
python3 experiments/compare_cnf_affine_probe_safe.py prepare /tmp/cnf-affine-safe-new
python3 experiments/compare_cnf_affine_probe_safe.py /tmp/cnf-affine-safe-new
python3 experiments/validate_cnf_affine_probe.py /tmp/cnf-affine-safe-new
python3 -m unittest solver.test_cnf_affine_probe solver.test_cnf_affine_probe_safe solver.test_cnf_affine_negative solver.test_cnf_affine_patterns
python3 -m unittest discover -s solver -p 'test_*.py'
```

The validator also requires the preserved first-run records in
`experiments/results/cnf-affine-probe`. Review found that their reusable-sequence
kernel could consume an outer iterator before fallback. The input adapter fixes
this and all twelve workers are rerun without changing cases or limits. Every
list-input decision and proof table is compared with those first runs; their
timings remain separate. Initial fixture failures are preserved there as well.

`validation.json` audits chronology, independent readers, append-only history,
exhaustive two-variable formulas and earlier observations. `analysis.json` records
paired costs, outcomes and family/variant cohorts. `residual-frontier.json`
preserves checked affine descriptions of all 108 holdout inputs after timing;
consistent subsystems do not settle coupling clauses, and this analysis publishes
no extra conclusions. Old budget stops remain historical observations.

Resume `checkpoint.json`. `checks.json` records tests, the manuscript build,
64 unchanged proof blocks and the final source ledger; `manifest.json` seals the
artifacts. The previous 664 sources and 8,275 artifacts remain unchanged, together
with 57 artifacts from the superseded first timing. Preserve all alternative
valid proofs rather than replacing earlier authoritative bytes.
