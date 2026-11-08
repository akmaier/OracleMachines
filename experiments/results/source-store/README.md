# Paired native maps and decoded source metadata

Runtime checkpoint: `9cf68a4`. This is a proof/correctness checkpoint. The previous
timing study is unchanged and remains tied to its original executable.

## Proof and implementation

`SourceStore.lean` gives the native context a store with a pointwise agreement
proof. Its relation and original-source model maps have the same keys. At each
key the relation tree is exactly the model's checked tree. `BodyMatches` retains
equations from the actual JSON field getters for identity, layout, width, start
and height. Logical and padding leaves retain exactly the original-clause array,
including order and repeated or empty entries.

Initialization, paired insertion and paired erasure construct this invariant.
`lookup_exact` and `missing_exact` recover matching models or absence at each
key. `lookup_semantics` proves that a retrieved tree's positive decision is
equivalent to satisfiability of its model's original clauses; a negative decision
is equivalent to their unsatisfiability. Registration and deletion execute the
new constructors. No whole-store verification pass is added.

Parsed/header wrappers retain getter equations as erased proofs. Temporary
runtime wrappers, parsing, comparisons, allocation and reference maps still
cost work. The existing reference-count loops are shared between generic and
source stores, retaining their underflow/reference checks. Their arithmetic is
not part of the new map theorem. No speedup, byte/RSS or complete cost bound is
claimed.

## Verification

- **162 tests pass**, including **23 focused source-update tests**. Logs contain
  no resource warnings.
- Lean audits **2,858 declarations / 1,367 theorem declarations**, without admits
  or added axioms.
- New tests fail unknown/duplicate deletion midway through a batch, then verify
  that the root and referenced-child rejection remain intact. Successful
  parent-before-child deletion removes both entries.
- Shared descendants survive deletion of another parent. Deleted identifiers
  can be registered with different original clauses without stale decisions.
  Equal relations retain distinct provenance, and missing metadata rolls back
  earlier definitions in the same batch.
- The full suite also exercises generic shared-child retention, source edits,
  historical branches, adoption and restart.
- All 355 older generic inputs pass current-engine revalidation and semantic
  audit. All five saved source versions pass checked adoption and restart.
- Every prior row in all 21 tables is preserved. All 174 previous experiment
  files retain their hashes. The archive now contains 6,745 generic results,
  2,193 refutations and 35 source-state rows across checker namespaces.

```sh
cd formal
lake build OracleMachines oracleSolver
cd ..
python3 -m unittest solver.test_source_updates
python3 -m unittest discover -s solver -p 'test_*.py'
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

`verification.json` records source/binary fingerprints and checks.
`preservation.json` records the ignored SQLite backup and old-row/artifact
comparisons. `paper-check.json` records rendered PDF review and preservation of
all 32 previous manuscript proof blocks. `source-study-recheck.json` verifies
73 historical source fingerprints and all 1,824 recorded outcomes; it does not
rerun the old executable or replace its timings.

## Remaining obligations

This pointwise proof covers map agreement, root metadata and original leaf
payloads. It does not yet relate named left/right references to the actual typed
children or serialized masks to cached summaries. It permits paired replacement;
the current protocol separately rejects changed bodies under a live identity.
Dependency lifetime under eviction, refcount arithmetic and exact requested-patch
semantics therefore remain priorities. Correctness of the returned node alone
does not prove that it is the requested successor. Complete serialized replay,
Python/SQLite refinement, general factor row/equivalence caches, acceptance
completeness and full resource accounting remain open. The adjacent-block
representation gives no unrestricted-SAT structural or coverage guarantee.
