# Saved trace reuse

Source-bound paired traces yield one checked equivalence, x27=x5, reducing a
37-variable residual to 36 variables. It does not close a new original:
**45/83 remains 45/83**. The scan retains all 40 negative pair outcomes and 284
bounded binary-learning candidates on 39 sources, of which 161 use later traces.

- `report.json`: parent identity, implementation fingerprints, complete costs,
  scan counts, acquisitions, matched controls and reference bindings.
- `opportunities.json.gz`: all 41 source scans and exact references; the clause
  list is capped at 16 per source and has not been applied.
- `rewrites.json.gz`: checked substitution and existing trace references.
- `proof-delta.sqlite3.gz`: five new pattern nodes, preserving all older rows.
- `coverage.json.gz`: finite coverage witness; no new roots are covered.
- `reference.sqlite3.gz`: 49 independently checked nodes proving the rewritten
  residual and target UNSAT; this is separate from structural coverage.
- `validation.json`, `full-validation.txt`: independent reconstruction and
  **561 passing tests**; existing SQLite resource warnings remain in the log.

Deriving the equivalence uses no new assumptions. Target recognition acquires
42 probes and five nodes in 0.04364 seconds. The whole source scan costs 0.52728
seconds. Full preparation/cold audits still dominate the 257.50-second measured
pipeline; standalone validation and tests are additional. The warm selected-pair
control is about 1.75 times faster with saved traces and is not an end-to-end
solver comparison. Peak RAM is unmeasured.

Reproduce from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/trace-tests.log 2>&1
python3 experiments/compare_cnf_trace_reuse.py experiments/results/NEW
python3 experiments/validate_cnf_trace_reuse.py experiments/results/NEW --test-log /tmp/trace-tests.log
```

Run timing separately from tests. Resume with `restore_checkpoint` in
`experiments/compare_cnf_trace_reuse.py`; pass the returned rewrite records to
`TraceRoutes`. The older generic probe runner does not load these external
routes. Details and limitations: [saved-trace-reuse.md](../../../research/saved-trace-reuse.md).
