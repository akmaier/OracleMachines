# Saved cofactors versus ordinary probe continuation

The saved-trace checkpoint covers 53 of the 83 retained development originals.
Four acquired open leaves below learned targets have 33, 33, 36 and 38 variables.
This experiment compares reuse of their existing cofactor traces with later
ordinary probing. It preserves both arms and merges their immutable evidence.

## Comparison contract

Both arms start from an identical parent database with fresh verifier caches.
All source identities and candidate rankings are frozen before acquisition. For
each source, at most eight retained opposite-polarity pairs are ranked using the
existing distinct uncovered/missing child, support and literal criteria. The
split arm chooses the first ranked pair. Both branches remain necessary for
structural closure; a SAT answer for one branch does not close the partition.

Each source receives at most 32 distinct recognition-state admissions. The split
arm also shares a global 128-state budget and does not reset it between branches
or sources. The ordinary arm uses up to eight advances and four visited sources
per initial leaf; its four separate 32-state allowances total at most 128. It
reports both the union of admitted identities and the sum of per-pass admissions:
an unfinished identity revisited in another ordinary pass can be charged again.
This is a matched admission allowance, not a matched CPU-work budget. Reentered
states, inference, proof checking and discovery can require additional work.

Candidate ranking, each arm's cold preparation, acquisition, composition,
serialization, persistence, merged replay and independent reference checks are
charged. Shared preparation is reported separately. No whole-solver timing
comparison or peak-RAM bound follows from these single measurements.

Each completed record remains immutable. Partial children and inconclusive
probe blocks survive. A split cannot contribute a coverage route until both
children exist; it closes only when both have checked structural plans. Each
newly completed child can also activate older pending probe or learned routes,
which are refreshed before coverage is measured. Diagnostics preserve both
cofactor obligations, including missing children and selected old-plan
frontiers; those frontiers do not enumerate every possible alternative plan.

## Reproduction and resumption

```sh
python3 -m unittest discover -s solver > /tmp/cnf-split-batch-tests.log 2>&1
python3 experiments/compare_cnf_split_batch.py /tmp/cnf-split-batch-reproduction
python3 experiments/validate_cnf_split_batch.py /tmp/cnf-split-batch-reproduction --test-log /tmp/cnf-split-batch-tests.log
```

The runner's parent is `experiments/results/cnf-trace-split/report.json`.
`compare_cnf_split_batch.restore_checkpoint` restores the merged child checkpoint
and returns rewrites, learning bases, augmented continuations and **all** split
records, including the inherited split. `routes_for` checks and attaches all
four evidence layers. Omitting the external split layer loses certified routes.

Four new regression tests check zero-budget pending branches, shared allowances,
partial resumption, duplicate-source skipping, cold reuse without discovery and
invalid limits. The standalone validator reconstructs each arm independently,
replays frozen selection, verifies all new nodes and proof routes, checks the
merged logical database against the union of both deltas, and checks preserved
reference proofs without new discovery. The runner also audits the full merged
inventory and checks idempotent delta replay. No historical implementation file,
experiment or Lean theorem is modified.

Results will be recorded after the timed run and independent cold replay.
