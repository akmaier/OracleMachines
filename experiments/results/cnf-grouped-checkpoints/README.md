# Grouped full audits with independent per-query proofs

[The analysis](../../../research/grouped-checkpoints.md) explains audit scope,
the memory regression, structural discoveries and remaining limits.

- `protocol.json` freezes the shared parent, cases 23/18/15, batch limits and two
  reversed mode orders. Only complete-audit scheduling differs between modes.
- `each_batch-*` and `group_end-*` preserve all twelve intermediate snapshots,
  per-query cold proof checks, operations and scheduled full audits.
- `report.json` compares complete sequence costs, acquisition and process RSS.
- `case-*-proof.json` and `case-*-explanation.json` record the three original-input
  proofs, family overlaps, reduction/decomposition structure and reuse provenance.
- `reconstruction.json` records retrospective full checking of every prefix,
  complete reachable-catalog comparisons, immutable history and snapshot equality.
- `checkpoint.json`, `checkpoint-protocol.json`, `queries.json`, `proof.json`,
  `pending.json` and `union/history.sqlite3.gz` preserve 1,946 patterns, 194 pairs
  and 11/24 structural coverage. All prior unsuccessful alternatives remain.
- `next-discovery.json` binds case 19 to the new union.
- `validation.json`, raw logs and `manifest.json` preserve tests, manuscript
  checks and the complete source/artifact audit.

Reproduce into a new directory from the repository root:

```sh
python3 experiments/compare_cnf_grouped_checkpoints.py /tmp/grouped-reproduction
python3 experiments/validate_cnf_grouped_checkpoints.py /tmp/grouped-reproduction
```

Restore without fresh acquisition; the destination must not exist:

```python
from experiments.validate_cnf_bootstrap import restore_checkpoint
checkpoint, checked = restore_checkpoint(
    'experiments/results/cnf-grouped-checkpoints/checkpoint.json',
    '/tmp/grouped-restored.sqlite3',
)
```

Grouped intermediate snapshots are not globally certified during execution;
each positive structural claim is checked, and the final full audit remains
mandatory before publishing a globally verified checkpoint. The retrospective
research validator separately checked every saved prefix. Coverage is not a
SAT/UNSAT output, and no unrestricted-SAT efficiency bound is claimed.
