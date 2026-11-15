# Broader conditioning candidate experiment

Read [the analysis](../../../research/bootstrap-conditioning.md) for the exact
split rule, workload differences, costs and remaining limitations.

- `protocol.json` freezes the same 24 prior inputs, changed depth policy and
  source fingerprints. This is a supplemental development experiment.
- `seed.json` and root `history.sqlite3.gz` retain the charged 85-pattern seed.
- `report.json` compares four workflows in two reversed orders. Every arm retains
  its full database, failed alternatives and acquisition counters.
- `diagnostic/` reproduces enumeration with profiling; its times are not main
  benchmark samples. Query verification is repeated 3,913 times for 86 records.
- `checkpoint.json`, `queries.json`, `proof.json`, `pending.json` and
  `union/history.sqlite3.gz` form the final restoration entry point: 1,154 patterns,
  96 source pairs, 5/24 covered originals and 17 missing children.
- `reconstruction.json` records independent no-acquisition cold checks;
  `validation.json` and `manifest.json` bind validation and preservation evidence.
- `validation-recovery/` retains the initial validator's archive-path collision
  and exact seed recovery. Its initial checkpoint is superseded and invalid.

From the repository root, reproduce into a new output directory:

```sh
python3 experiments/compare_cnf_bootstrap.py /tmp/bootstrap-reproduction
python3 experiments/profile_cnf_bootstrap.py /tmp/bootstrap-reproduction/diagnostic /tmp/bootstrap-reproduction
python3 experiments/validate_cnf_bootstrap.py /tmp/bootstrap-reproduction
```

Restore the committed union without fresh discovery:

```python
from experiments.validate_cnf_bootstrap import restore_checkpoint
report, checked = restore_checkpoint(
    'experiments/results/cnf-bootstrap-conditioning/checkpoint.json',
    '/tmp/bootstrap-restored.sqlite3',  # must not already exist
)
```

Enumeration covers 5/24 versus ordinary depth one's 4/24, with fewer probes and
patterns but longer elapsed queries. The next target is incremental checking of
immutable split records. Unknown coverage is not an UNSAT verdict. No universal
efficiency result follows from this finite experiment.
