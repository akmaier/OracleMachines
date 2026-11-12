# Frontier search: evidence and compatible histories

`validate_cnf_frontier_pivots.py` checks the frozen experiment source fingerprints,
both exact input reports, merged seed hashes/digests, identical input/configuration
and new-trial budgets, and every emitted delta. Reconstruction must reproduce the
recorded logical tables; a second application must leave bytes unchanged. All old
row counts, full cold/trial audit counts, frontier statistics, endpoint archives,
coverage preservation and per-input caps are checked. The runner separately
rejects missing or changed old payloads before emitting a delta.

All four histories already passed complete cold graph/source/solver verification
and exact trial/recomposition replay without changed bytes. No new source closes;
endpoint reference stores therefore contain no solved evidence. The optional
scheduler changes acquisition, not the ordinary SAT decision path.

The original-suite new deltas share 57 exact pattern rows and 29 trial rows.
Together they add 299 unique nodes / 218 trials over the previous merged seed.
The complete union has **41,299 pattern nodes, 563 trials, 1,548 source bindings
and 21,838 ordinary solver proof rows**. The repeated-control deltas share six
pattern rows and two trials, adding 25 nodes / 20 trials; its complete union has
24,982 patterns, 65 trials, 1,561 bindings and 23,116 solver rows. Compatible union
digests and SQLite integrity are checked. No extra full merged cold replay or
combined runtime is claimed.

Restore the original base and both earlier pivot deltas listed by each suite's
input reports, then apply both new mode deltas, checking all hashes. Compare
with `compatible_unions[*].merged_table_digests` in `validation.json`. This keeps
all failed explorations available without duplicating immutable payloads.

All **531 Python tests** pass in the retained full-suite log. Formal sources and
the manuscript are unchanged from `16fdf79`; no new Lean build or theorem is
claimed. Timed runs finished before the final test suite and validation analysis.
