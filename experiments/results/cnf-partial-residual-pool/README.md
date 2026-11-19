# Bounded partial-residual retrieval

This frozen experiment is a negative performance result. The optional candidate
pool increases mean query time 5.88% exposed / 4.27% on fresh sizes, with unchanged
outcomes and recorded expansion counts. Retain the input-safe affine policy as
the performance baseline. See [analysis](../../../research/partial-residual-retrieval.md).

- `protocol.json` freezes cases, budgets, parent and sources before eight serial workers.
- `report.json` and trial directories retain timings, counters, queries and archives.
- `analysis.json` groups costs and differences without altering timed observations.
- `profile.json` reproduces all counters/results/native/affine digests under instrumentation.
- `coordinate-example.json` and its archive preserve a checked supplied-map blind spot.
- `residual-frontier.json` screens every holdout source after timing without adding verdicts.
- `validation.json` audits chronological publication, independent replay and old histories.
- `checkpoint.json` points to the append-only evidence union and all previous studies.
- `checks.json` binds tests, manuscript, 64 unchanged proof blocks and 678 sources.
- `manifest.json` seals all artifacts; prior manifests remain unchanged.

The retained pool/index charge is capped at 512 KiB, with separate bounded causal
plans. These are not total process, proof-checking or persistent-storage bounds.
Cold seeding reconstructs the newest bounded tail, not the former pool order.
The coordinate map in the diagnostic is supplied; automatic map discovery and
its frequency on the timed streams remain open. No arbitrary-SAT bound follows.

The prefreeze policy and its successful tests are preserved in `initial-policy/`
and the initial/refined test logs. This revision excludes inexpensive terminal
proofs from the candidate pool. No timed outcome was used to choose that filter.
Full-suite SQLite warnings remain recorded; focused tests emit none.

To rerun the frozen comparison in a new destination, from the repository root:

```sh
python3 experiments/compare_cnf_partial_residual_pool.py prepare /tmp/oracle-partial-study
python3 experiments/compare_cnf_partial_residual_pool.py /tmp/oracle-partial-study
python3 experiments/profile_cnf_partial_residual_pool.py /tmp/oracle-partial-study
python3 experiments/validate_cnf_partial_residual_pool.py /tmp/oracle-partial-study
```

Do not overwrite the preserved result directory. Profiling and independent
validation run after all timed workers. The finalizer also requires the full and
focused test logs and final LaTeX log described in `checks.json`.
