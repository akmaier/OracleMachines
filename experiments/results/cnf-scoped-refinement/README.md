# Root-complete checking and case-22 continuation

[The analysis](../../../research/scoped-refinement.md) describes the scope
invariant, complete cost accounting and remaining limits.

- `protocol.json` fixes the common complete history, target, limits and two
  reversed mode orders. No inference or selection policy changes between modes.
- `eager-*` and `scoped-*` retain every fresh-process stream, batch archive,
  operation, proof, resource count and full cold check.
- `report.json` compares startup, expansion, bookkeeping, compression, full cold
  verification, whole-stream time, process RSS and live checked metadata.
- `reconstruction.json` independently verifies all archives, exact acquisition
  and proof equality, and completeness of the scoped reachable catalogs.
- `target-proof.json` and `explanation.json` describe the original's 32-step proof,
  including its separate 2-CNF component and shared contradiction terminal.
- `checkpoint.json`, `checkpoint-protocol.json`, `queries.json`, `proof.json`,
  `pending.json` and `union/history.sqlite3.gz` retain 1,799 patterns, 173 pairs and
  8/24 structural coverage. All unsuccessful historical alternatives remain.
- `next-discovery.json` binds case 23's connected mixture to this complete union.
- `validation.json`, test/build logs and `manifest.json` preserve validation and
  prior-artifact evidence. The initial targeted-test failure records a SQLite
  no-op update assumption; the corrected test makes an actual external write.

Reproduce into a new directory from the repository root:

```sh
python3 experiments/compare_cnf_scoped_refinement.py /tmp/scoped-reproduction
python3 experiments/validate_cnf_scoped_refinement.py /tmp/scoped-reproduction
```

Restore with fresh acquisition forbidden; the destination must not exist:

```python
from experiments.validate_cnf_bootstrap import restore_checkpoint
checkpoint, checked = restore_checkpoint(
    'experiments/results/cnf-scoped-refinement/checkpoint.json',
    '/tmp/scoped-restored.sqlite3',
)
```

A scoped live query does not certify unrelated history. The persisted checkpoint
has passed the complete independent check; no unrestricted-SAT efficiency claim
or default solver-policy change follows from this finite comparison.
