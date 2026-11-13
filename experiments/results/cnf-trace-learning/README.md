# Retained implications and bounded CNF lookahead

This study composes all saved original-source conditional units into a binary
implication graph, then applies a capped batch of checked clauses to the full
CNF. It uses the same 41 development sources as the saved-pair study and retains
all parent routes. A matched control probes the original formula using the same
variable order chosen after augmentation, separating propagation gains from
ranking changes.

- `report.json`: parent hash, implementation fingerprints, counts, timings,
  coverage, admission outcomes and independent reference bindings.
- `diagnostics.json.gz`: exact graph reachability certificates for all 41
  sources, with successful and unsuccessful same-variable controls.
- `learning.json.gz`: all learned-clause proofs and augmented probe attempts,
  including clear outcomes. Each required source reference is interned once.
- `proof-delta.sqlite3.gz`: additive pattern-node changes; old rows are preserved.
- `coverage.json.gz`: finite structural coverage witness, separate from answers.
- `reference.sqlite3.gz`: independent source/target and gained-original proofs.
- `validation.json`, `full-validation.txt`: independent cold reconstruction and
  the full Python test log. Existing SQLite resource warnings remain visible.
- `pilot/`: the preliminary graph/control observations and a test-fixture failure
  caused by assuming the first probe trace had a unit; the test now selects an
  actual unit-bearing trace before corrupting its reason.

Reproduce from the repository root, with tests and timing run sequentially:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/trace-learning-tests.log 2>&1
python3 experiments/compare_cnf_trace_learning.py experiments/results/NEW
python3 experiments/validate_cnf_trace_learning.py experiments/results/NEW --test-log /tmp/trace-learning-tests.log
```

Resume with `restore_checkpoint` in `experiments/compare_cnf_trace_learning.py`.
Pass both returned record lists to `LearnedTraceRoutes`; older restoration
helpers omit these new alternatives. The parent eight-table history, pair
rewrites and earlier solver archives are immutable.

Detailed evidence, limits and next targets:
[saved-implication-learning.md](../../../research/saved-implication-learning.md).

The result is **two stronger reductions, but unchanged coverage at 45/83**.
All **566 tests** and independent cold replay pass. The run adds 15 nodes;
its three remaining selected leaves have 27, 39 and 35 variables. Exact keys,
remaining ranked candidates and read-only costs are in `remaining-targets.json`.
Reproduce that diagnostic with:

```sh
python3 experiments/inspect_cnf_trace_learning.py experiments/results/NEW
```
