# Retained learning: 47/83 to 52/83 structural coverage

Implementation checkpoint: `6f82d5f`. Parent:
`experiments/results/cnf-frontier-learning/report.json`. See
[the research note](../../../research/retained-learning-batch.md) for restrictions,
matched controls, complete cost accounting and next targets.

- Five new original closures: cases 24, 40, 50, 66 and 81, all independently SAT.
  The growth-exception ablation retains all 52 closures.
- 36 saved clear learning bases selected; 144 advances produce 141 blocks
  (131 clear, nine forced, one equivalence), with 77 new pattern nodes.
- Six successful augmented blocks have clear same-variable original controls;
  four controls also find forced values. All inputs are reused development cases.
- One shared 128-state budget and a 32-new-state per-target cap. No cap binds;
  no successful target is pending. Every historical proof row is preserved.
- 577 Python tests pass. Standalone replay performs no new discovery and leaves
  the reconstructed history and reference database bytes unchanged. All 164
  inherited reference proofs survive in the 1,156-node extended archive.
- Pipeline: 263.21369 seconds; separate standalone validation: 147.33912 seconds.
  Preparation and cold checking dominate; no whole-solver speedup is claimed.

`report.json` binds the implementation, parent, immutable delta and other
archives by hash. `additions.json.gz` stores only the new augmented records and
their controls. `diagnostics.json.gz` retains both selections, the search trace,
all admissions, and the exact remaining target/leaf identities. `coverage.json.gz`
is the finite composition witness. `proof-delta.sqlite3.gz` uses the eight-table
schema and stores 77 new pattern rows. `reference.sqlite3.gz` is a complete extended
reference snapshot; it is additional storage, not part of the pattern database.
`validation.json`, `full-validation.txt` and `run.txt` preserve verification and
execution evidence.

The working database has 41,659 pattern nodes and occupies 768,598,016 bytes,
an increase of 1,044,480 bytes. Peak RAM is unmeasured. External proof records,
diagnostics and reference archives are accounted separately in the research note.

Next: the smallest acquired open target has a ten-variable / 51-clause leaf
with one untried ordinary probe. There are also 18 ready learned formulas with
92 unused ranked variables. Five raw queue entries are already exhausted;
re-run the selection filter instead of counting them as untried work.

To resume, call `continue_cnf_learning.restore_checkpoint` with this report and
pass all returned rewrites, learning bases and augmented blocks to
`ContinuedLearningRoutes`. A subsequent batch uses a fresh output directory and
`--parent experiments/results/cnf-learning-batch/report.json`. Earlier loaders
do not include this new external proof layer.
