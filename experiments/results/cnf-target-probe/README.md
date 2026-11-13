# Bounded probing below learned targets

This pass resumes the three acquired learned-clause targets from
`cnf-trace-learning`, ordered by the smallest selected leaf. Each target gets
at most eight calls to advance a four-variable probe block, four distinct
sources and one shared 32-state admission budget. Saved clear prefixes are
reused; a forced block follows its exact target. Reused forced blocks and
exhaustion also consume a step. All parent proof alternatives remain available
when the original cases are recomposed.

- `report.json`: parent hash, implementation fingerprints, policy, coverage,
  counters, timings, state admissions and independent reference bindings.
- `diagnostics.json.gz`: exact target ordering, before/after selected leaves,
  every visited source/block and every newly stored probe identity.
- `proof-delta.sqlite3.gz`: additive changes across the eight history tables.
- `coverage.json.gz`: finite structural coverage witness, separate from answers.
- `reference.sqlite3.gz`: independent proofs for every new forced source/target
  pair and every gained original, with SAT model lifting checked.
- `validation.json`, `full-validation.txt`: independent cold replay and full tests.

Run tests and timed experiments sequentially from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/target-probe-tests.log 2>&1
python3 experiments/compare_cnf_target_probe.py experiments/results/NEW
python3 experiments/validate_cnf_target_probe.py experiments/results/NEW --test-log /tmp/target-probe-tests.log
```

For another pass, supply `--parent experiments/results/cnf-target-probe/report.json`.
`restore_checkpoint` in `compare_cnf_target_probe.py` reconstructs the full lineage
and returns both external proof lists. Supply them to `LearnedTraceRoutes`; using
an older restoration helper would omit these new probe records. Fingerprinted
implementation files and all earlier artifacts must remain unchanged.

The step limit bounds calls to advance, not total frontier traversal, checking,
target recognition, state size or reference work. The candidate pool remains
capped at 64 ranked variables. Clear outcomes are inconclusive. This is a study
of reused development cases, with no claim of arbitrary-SAT tractability or an
end-to-end solver speedup. Peak RAM is not measured.

The result is **46/83 covered**, up from 45/83, with the new case 58 independently
proved UNSAT. Coverage remains 46 without growth-exception routes. Case 32's
leaf shrinks from 27 to 23 variables but stays open; it and the 39-variable leaf
now have no remaining ranked probes. All 569 tests and standalone cold checks
pass. The pass retains 10 new states and 15 probe blocks; working SQLite grows
327,680 bytes. Local acquisition costs 0.11697 seconds, while the complete
acquisition/validation pipeline costs 256.68 seconds, plus the standalone
71.33-second validator. `acquisition.log` retains the run's console output.

Full accounting and the next target:
[learned-target-continuation.md](../../../research/learned-target-continuation.md).
