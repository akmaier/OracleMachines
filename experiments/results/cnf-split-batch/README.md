# Saved-cofactor batch comparison

Parent: `../cnf-trace-split/report.json` (53/83 structural coverage).
Implementation checkpoint: `a3a966a`.

Isolated saved splits reach **55/83** (30 new states); ordinary continuation
reaches **54/83** (seven). Both arms use the same four initial leaves and a
32-state allowance per source. The merged history preserves all evidence and
reaches 55/83, also without the growth exception. Case 37 is independently UNSAT;
case 77 is SAT. These are adaptively reused development cases.

- `report.json`: policies, fingerprints, arm/union metrics, logical digests and
  independent reference bindings.
- `selection.json.gz`, `splits.json.gz`: frozen source/rank data and four new
  checked cofactor splits; the parent contributes one more split.
- `split-*`, `probe-*`: both isolated deltas, diagnostics and coverage proofs.
- `proof-delta.sqlite3.gz`: exact immutable union relative to the parent.
- `diagnostics.json.gz`, `coverage.json.gz`: merged frontier and coverage proofs.
- `reference.sqlite3.gz`: extended independent reference archive, preserving all
  parent proof rows.
- `validation.json`, `full-validation.txt`: standalone cold replay and 585 tests.

Resume with `experiments.compare_cnf_split_batch.restore_checkpoint` and
`routes_for`, including all five split records. The next selected open leaf has
27 variables and 101 clauses, under the true branch of the first saved split;
its sibling is closed. Read `diagnostics.json.gz` → `children`, since the older
target view does not follow open external split routes.

Working SQLite grows 720,896 bytes to 769,384,448 bytes; separate archives add
storage. Split acquisition costs 0.14475 seconds plus 0.05791 seconds ranking,
versus 0.09725 seconds for ordinary probing. Cold checking dominates the full
comparison. No general speedup, peak-RAM bound or unrestricted-SAT theorem is
established. See [the full analysis](../../../research/saved-cofactor-batch.md).
