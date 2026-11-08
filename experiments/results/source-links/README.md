# Named child registration and serialized source summaries

Runtime checkpoint: `6a73372`. This is a proof/correctness checkpoint. Historical
timing data is unchanged and remains tied to its original executable.

## Proof and implementation

`SourceLinks.readJoin` returns a node with `JoinLinks` indexed by the model-map
snapshot used at registration. It retains equations for the actual decoded child
names, successful lookups of both models, and equality to their checked consecutive
join. Native source registration executes this constructor. The subtype proof
erases; the runtime does not retain the map snapshot or scan/copy the store.

`original_clauses` attributes every original clause occurrence to the named
children. `decision_exact` requires one valuation satisfying both child sources,
not independently chosen SAT witnesses. `distinct_children` follows from typed
consecutive intervals; it does not prohibit shared children in the generic
relation DAG or sharing across source parents.

`insert_fresh` preserves a join's links under fresh-key model insertion.
`erase_unreferenced` preserves them when deletion removes neither decoded child.
These are conditional map-transition theorems. Zero incoming references has not
yet been proved to imply the erasure premise. `JoinLinks` is not yet part of a
global invariant for every live branch across every runtime request.

`BodyMatches.summary` now binds the decoded mask to the model's actual cached
relation. This field is part of the existing paired-store invariant and survives
its constructors. Leaves/padding retain their construction equality; branches
retain the successful relation-comparison proof. The mask-range guard remains.
No additional relation or store scan is introduced. Getter wrappers, comparisons,
allocation, transport and archive access still cost work; no new speedup or full
machine/byte bound is claimed.

The helper checks child shape before header start/height, so requests with several
defects can report a different first error. Accepted semantics and caps remain
unchanged. Warm queries do not call the join helper.

## Verification

- **165 tests pass**, including **26 focused source-update tests**, without
  resource warnings.
- Lean audits **2,874 declarations / 1,380 theorem declarations** without admits
  or added axioms.
- Distinct source clause lists with equal relations remain attributable to the
  named children. Missing/ill-typed child names and changed live bodies reject.
- Wrong masks reject even when the proposed and correct relations both admit a
  SAT answer. Tests cover leaves, identity padding, branches and malformed masks.
- Twelve parents are deleted in shuffled order. Both shared children reject
  eviction until the last parent is removed; parent queries remain correct.
- The existing suite exercises inconsistent shared valuations, failure rollback,
  generic DAG retention, local edits, old branches and restart.
- All 355 older generic inputs pass current-engine revalidation and semantic
  audit. All five saved source versions pass checked adoption and restart.
- Every previous row in all 21 tables is preserved. All 182 previous experiment
  files retain their hashes. The archive now holds 7,100 generic results,
  2,322 refutations and 40 source-state rows across checker namespaces.

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
historical source fingerprints and 1,824 recorded outcomes; it does not rerun
the old executable or replace its timings.

## Remaining obligations

Promote registration links to an invariant of every live branch. Prove immutable
identity handling and connect the runtime reference-count policy to the conditional
erasure premise. Then establish exact requested-patch semantics. Serialized
replay, Python/SQLite refinement, general factor row/equivalence caches,
acceptance completeness and full resource accounting remain open. This supplied
adjacent-block representation gives no unrestricted-SAT coverage guarantee.
