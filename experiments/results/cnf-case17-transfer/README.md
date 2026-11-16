# Case-17 policy transfer and history ablation

Read [the analysis](../../../research/case17-policy-transfer.md) for scope,
resource accounting and remaining gaps.

- `protocol.json` freezes the two parent histories, unchanged policy, target,
  bounds and reversed repetition orders.
- `retained-*` and `before_case16-*` preserve each fresh-process stream, every
  batch archive, acquisition count, operation and cold check.
- `report.json` compares target acquisition, lifecycle time, peak RSS and storage.
- `*-target-proof.json` and `*-explanation.json` show identical 96-step proofs,
  with no contribution from the 547 patterns or 66 pairs added for case 16.
- `reconstruction.json` independently checks both parents, four trial archives,
  exact delta/operation/proof equality, and the full preservation union.
- `checkpoint.json`, `checkpoint-protocol.json`, `queries.json`, `proof.json`,
  `pending.json` and `union/history.sqlite3.gz` preserve 1,790 patterns, 171 pairs
  and 7/24 coverage. No earlier results are dropped by the history control.
- `next-discovery.json` binds the remaining case-22 mixture to the new union.
- `validation.json`, logs and `manifest.json` record tests, source and artifact
  preservation, manuscript checks and file hashes.

Reproduce into a new directory from the repository root:

```sh
python3 experiments/compare_cnf_case17_transfer.py /tmp/case17-reproduction
python3 experiments/validate_cnf_case17_transfer.py /tmp/case17-reproduction
```

Restore without new acquisition, using a destination that does not exist:

```python
from experiments.validate_cnf_bootstrap import restore_checkpoint
checkpoint, checked = restore_checkpoint(
    'experiments/results/cnf-case17-transfer/checkpoint.json',
    '/tmp/case17-restored.sqlite3',
)
```

This is an adaptive development-input result. Finite structural coverage and
observed conditional depth do not establish uniformly efficient arbitrary SAT.
