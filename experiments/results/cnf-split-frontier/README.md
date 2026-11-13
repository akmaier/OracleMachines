# Continuation through retained splits

Parent: `../cnf-split-batch/report.json` (55/83 coverage).
Implementation checkpoint: `447e807`.

The checked frontier view follows the existing open split child rather than
restarting its 33-variable parent. Bounded ordinary continuation reduces the
selected leaf **27 variables / 101 clauses -> 22 variables / 90 clauses** with
six new recognition states. Original coverage stays **55/83**, also without the
growth exception. Six clear blocks and one forced block remain archived.

The remaining leaf has a checked obstruction to single-variable unit refutation:
38 clear traces cover both values of 19 binary-clause variables; the other three
cannot initiate unit propagation. No saved pair yields the implemented common
value or equivalence rewrite. This does not decide SAT/UNSAT or exclude stronger
learning or conditioning. Do not repeat the unchanged ordinary probe stream.

- `report.json`: provenance, policy, fingerprints, all resource measurements,
  exact database digests and independent reference bindings.
- `selection.json.gz`, `diagnostics.json.gz`: exact selected source, split ancestry,
  continuation visits, remaining leaf and other learning queues.
- `proof-delta.sqlite3.gz`, `new-probes.json.gz`, `coverage.json.gz`: preserved
  acquisition rows and checked original-level coverage.
- `reference.sqlite3.gz`: 1,750 independent proof nodes, retaining all 1,721 old
  nodes. The forced source and exact target are independently SAT; structural
  coverage of the remaining partition is still open.
- `obstruction.json`, `obstruction.rewrites.json.gz`: checked propagation limit
  and empty list of applicable paired rewrites.
- `validation.json`, `full-validation.txt`, `cold-validation.txt`: 589 tests and
  cold replay with new acquisition disabled and database bytes unchanged.

Working SQLite grows 176,128 bytes to 769,560,576 bytes. Navigation costs 0.00688 s
and acquisition 0.06866 s; cold verification dominates the 256.65-second pipeline.
The separate obstruction check costs 11.80 s including reconstruction, and the
independent cold validator costs 151.51 s. These are single-run measurements,
with no general speedup or peak-RAM bound.

Resume with `experiments.continue_cnf_split_frontier.restore_checkpoint` and
`compare_cnf_split_batch.routes_for`, retaining all five external splits. The
next investigation is a stronger source-proved learned batch versus nested
cofactor acquisition on the exact 22-variable leaf. The alternative queue has
18 ready bases with 92 remaining ranked variables. See
[the full analysis](../../../research/retained-split-frontier.md).
