# Bounded pivot search: validation and compatible archives

`validate_cnf_pivot_alternatives.py` binds both schedules on both input sets to
their source checkpoints, fingerprints, options, budgets and original case lists.
Each delta is restored over its exact paid base; logical table digests, SQLite
integrity, unchanged old-row counts and idempotent application are checked.
All four experiment histories previously passed full node/source/solver cold
verification and separate projection-trial/recomposition replay without changed
bytes. Those phase times are reported separately and include overlapping checks
of old dependencies.

Every trial budget is at most eight, all old closures survive, and no new source
closes. No successful replacement exists, so the retained endpoint files are
empty initialized reference stores, not new SAT/UNSAT proofs. All ordinary solver
rows are preserved; no ordinary-solver speedup is claimed. Read-only frontier
analysis is bound by code/report hashes and its retained counts are checked.

The two original-input deltas share **554 identical pattern rows and 287 identical
trial rows**. Applying both preserves all old values and yields **708 unique new
pattern nodes / 345 trial records**, rather than duplicating their sums of 1,262
nodes / 632 records. The repeated-control deltas share 101 pattern and 35 trial
rows, yielding 121 unique new nodes / 45 trials. Compatible unions have recorded
logical table hashes and integrity checks. Each constituent graph was already
cold-checked; no additional full merged cold replay or merged runtime claim is
made. Restore the base, verify archive hashes, and apply both deltas using the
experiment runner's `apply_delta` to resume from all results.

All **527 Python tests** pass. The formal directory is unchanged from `21a90ac`;
`validation.json` binds the prior 4,219-declaration / 2,031-theorem Lean audit.
No new Lean build, refinement theorem or order-search bound is claimed.
The manuscript preserves all 63 prior proof blocks exactly and has 230 unique
labels. Its 143-page PDF builds without warnings or over/underfull boxes. Pages
135--137 were rendered at 100 dpi and visually reviewed; `pdf-review.json` binds
the final source, PDF and page image hashes.
