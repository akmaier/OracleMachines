# Terminal polarity-renaming integration pilot

Eight previously used diagnostic inputs, unchanged options (depth two, four probe
and learning candidates). Baseline closure is 2/8; the new terminal policy closes
5/8, adding source cases 858, 875 and 970. Selected distinct unresolved leaves
fall from 9 to 4 and literals from 699 to 534. All ordinary answers agree; full
cold audits pass and warm replay inserts no rows. Both complete pilot archives
and per-query results are retained.

This pilot validates the comparison harness and recomposition. Its timings are
**not clean performance evidence**: the full Lean audit was running concurrently.
Use the subsequent full matched study for measured costs. The eight cases are
selected diagnostics, not a representative or independent holdout corpus.

Reproduce from repository root:

```sh
python3 experiments/compare_cnf_polarity_horn.py --pilot --output /tmp/polarity-pilot
```

The exact comparison script used by the pilot is retained as
`comparison-source.py.txt`, matching its recorded fingerprint. The implementation
checkpoint adds deletion of redundant successful-run checkpoint JSON files;
interrupted-run checkpoints remain. This changes no measured algorithm.
