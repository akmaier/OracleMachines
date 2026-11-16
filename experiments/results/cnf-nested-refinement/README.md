# Nested conditioning versus broader first-level acquisition

Read [the analysis](../../../research/nested-conditioning-discovery.md) for the
bounded policies, proof structure, full cost breakdown and limitations.

- `protocol.json` freezes the complete parent union, case-16 target, budgets and
  two reversed workflow orders before continuation.
- `flat-*` and `nested-*` preserve every batch archive, unfinished choice, work
  counter and checked positive proof. Flat exhausts all 59 source variables;
  nested adds eleven deeper pairs and closes the original.
- `initial-frontiers.json` records eight distinct reduced frontier keys, without
  claiming semantic inequivalence.
- `case16-proof.json` and `explanation.json` expose twelve conditional nodes,
  maximum conditional depth five, 265 unary reductions and nine family leaves.
- `lifecycle/` contains supplemental fresh-process runs with full stream time,
  bookkeeping and peak RSS; their timings are outside the paired local means.
- `checkpoint.json`, `checkpoint-protocol.json`, `queries.json`, `proof.json`,
  `pending.json` and `union/history.sqlite3.gz` retain all successful and failed
  alternatives: 1,701 patterns, 162 pairs and 6/24 structural coverage.
- `reconstruction.json`, `validation.json`, logs and `manifest.json` preserve
  cold replay, test and prior-artifact checks.
- `next-discovery.json` binds case 17 and its four saved pairs to the new union;
  case 16 is complete and is not a remaining discovery obligation.

Reproduce into a new directory from the repository root:

```sh
python3 experiments/compare_cnf_nested_refinement.py /tmp/nested-reproduction
python3 experiments/validate_cnf_nested_refinement.py /tmp/nested-reproduction
python3 experiments/explain_cnf_nested_refinement.py /tmp/nested-reproduction
python3 experiments/measure_cnf_nested_lifecycle.py /tmp/nested-reproduction nested
python3 experiments/measure_cnf_nested_lifecycle.py /tmp/nested-reproduction flat
```

Restore the combined checkpoint with fresh acquisition forbidden:

```python
from experiments.validate_cnf_bootstrap import restore_checkpoint
report, checked = restore_checkpoint(
    'experiments/results/cnf-nested-refinement/checkpoint.json',
    '/tmp/nested-restored.sqlite3',  # destination must not already exist
)
```

No uniform polynomial bound, fixed five-variable backdoor, minimum-depth result,
or SAT/UNSAT answer follows from this finite adaptive experiment.
