# Exact incoming counts and native source dependency lifetime

Runtime checkpoint: `3382876`. This is a proof/correctness checkpoint. Earlier
timing evidence is unchanged and remains tied to its original executable.

## Proof and implementation

`ReferenceCounts.Exact` states that every incoming count equals the sum of decoded
child-reference occurrences across all live parents. Its finite parent-domain
witness and aggregate sum occur in a proposition and erase. The specification
counts multiplicities, including repeated entries in a child list.

`increment_exact` proves the executed fold's pointwise addition law. Successful
`decrement` returns its exact subtraction equation, retaining underflow rejection.
`exact_insert` and `exact_erase` preserve the aggregate invariant. A zero count
excludes the key from every live parent's decoded child list (`zero_no_child`).

`SourceLifetime.Store` wraps the paired native store with exact counts and a global
`Linked` invariant. Every live branch names its exact current child models.
`linked_insert` uses fresh-key preservation. `linked_erase` combines decoded
metadata with zero-count exclusion to discharge the earlier conditional deletion
premise. `lookup_branch` recovers the current links from a named relation lookup.

The native source context executes these constructors. Registration supplies the
actual missing-key equation plus a leaf-or-checked-join proof. Duplicate
registration changes no state. Source deletion executes the proved decrement
and returns both preserved invariants; failed functional batches expose no new
store. Removing a parent may release children for later deletion. An unreferenced
name can be reused without rebinding a live parent.

Each body decodes at most two direct children. No finite-domain construction,
aggregate recount or full-store scan is introduced. Runtime hashes, maps,
wrappers, integer operations, retained sources and transport remain costs.
This is not a complete allocation, RSS or bit-machine theorem, and no new timing
claim is made. Generic relation-store loops and Python active-reference policy
remain outside this native source wrapper's invariant.

## Verification

- **166 tests pass**, including **27 source-update tests**, without resource
  warnings.
- Lean audits **2,944 declarations / 1,416 theorem declarations**, without admits
  or added axioms.
- A new test constructs 44 nodes with 16 roots and shared internal descendants.
  An independent full recount predicts the zero-count deletion frontier during
  randomized operations and duplicate definitions; surviving roots are queried.
- Remaining nodes are removed in dependency order. The same names are rebuilt,
  queried and completely reclaimed again, checking for stale/inflated counts.
- Existing checks cover failure rollback, shared parents, identity reuse, source
  changes, tight resident caps, historical branches, context reset and restart.
- All 355 older generic inputs pass current-engine revalidation and semantic
  audit. All five saved source versions pass checked adoption and restart.
- Every old row in all 21 tables remains intact. All 190 prior experiment files
  retain their hashes. The archive now holds 7,455 generic results, 2,451
  refutations and 45 source-state rows across checker namespaces.

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
all 32 earlier manuscript proof blocks. `source-study-recheck.json` checks 73
historical source fingerprints and all 1,824 recorded outcomes. It does not
rerun the old executable or replace its timings.

## Remaining obligations

Exact requested-patch semantics is the next native proof. The current node's
correct SAT meaning and safe dependencies do not alone prove that it is the
requested successor. Python retention, generic relation-store invariants,
complete serialized replay/SQLite correspondence, general factor caches,
acceptance completeness and full resource accounting remain open. The supplied
adjacent-block representation gives no unrestricted-SAT coverage guarantee.
