# Original-source nodes and consecutive native joins

Runtime checkpoint: `b7dfcf4`. This is a proof/correctness checkpoint, not a
timing comparison. Earlier experiments and measured timings are unchanged.

## Proof and implementation

`SourceNodes.lean` introduces `OriginalTree`, indexed by the exact layout array,
width, start and height. Logical leaves retain original integer clauses with
their checked translation at an in-range edge. Padding leaves prove their edge
is outside the logical source and compile to identity. A branch requires equal
child heights and the exact consecutive start.

`CheckedNode` aligns this original tree with its actual cached relation tree.
Checked leaf, padding and join constructors preserve that alignment. Join theorems
preserve the concatenated original clause list and every clause occurrence.
`CheckedNode.decide_exact` and `unsat_exact` connect the executed decision to
the original clauses stored in the node. The proof relates paths to global edge
positions; satisfying valuations extend through padding by repeating the final
block state, and accepting paths induce a global valuation through the layout map.

The native context's model map is typed by its layout and width. Registration
uses the new constructors and typed child starts. Query checks use typed root
start/height, and decision-only queries read the cached summary. Replay constructs
the same kind of nodes. Context changes reset both maps; failed batches return
no new store. Flattening original clauses is a specification operation, not a
warm-query or join operation.

The original integer arrays now remain reachable from native source leaves,
alongside JSON evidence and translated clauses. New diagnostic counters report
newly registered original-source nodes, clause entries and literal entries,
including replay. Duplicate registration and warm unchanged queries add zero.
Joins retain child references. These are entry counts, not physical byte/RSS
bounds or new formal allocation theorems. No speedup, memory reduction or complete
native cost theorem is claimed.

## Verification

- **159 tests pass**, including 20 focused source-update tests.
- Lean audits **2,751 declarations / 1,320 theorem declarations**, without admits
  or added axioms. Build and test logs are retained.
- New tests reject nonconsecutive/reversed children, inconsistent heights/widths
  and incorrect layouts. Conflicting requirements on a shared original variable
  give UNSAT despite nonempty individual leaf relations.
- A failed definition batch exposes no partial node. Layout reset removes old
  nodes; changing the layout under an existing identity is rejected. Duplicate
  registration reports zero added original payload entries.
- Sparse IDs above 64 bits, permuted slots, empty/short blocks, local edits,
  deletion, old branches and restart pass. A four-leaf source registers seven
  original-source nodes; one height-two edit registers three nodes plus one
  clause and one literal. An unchanged query registers none.
- All 355 distinct older generic inputs pass current-engine revalidation and
  semantic audit. All five saved source versions pass checked adoption and restart.
- Every old row in all 21 tables remains present; all 166 previous experiment
  files retain their hashes. The archive now contains 6,390 generic results,
  2,064 refutations and 30 source-state rows across checker namespaces.

```sh
cd formal
lake build OracleMachines oracleSolver
cd ..
python3 -m unittest solver.test_source_updates
python3 -m unittest discover -s solver -p 'test_*.py'
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

`verification.json` records source/binary fingerprints and checks. Final additions
to the join occurrence proofs leave the tested native binary unchanged; its hash
was checked after the final Lean build. `preservation.json` records the ignored
SQLite backup and old-row/artifact comparisons. `paper-check.json` records PDF
review and preservation of all 32 previous manuscript proof blocks.
`source-study-recheck.json` checks 73 historical source fingerprints and all 1,824
old outcomes. It does not rerun the old executable or replace its timings.

## Remaining obligations

The decision theorem concerns the original clauses of the returned typed node.
A state theorem must still connect named JSON nodes, child references, relation
entries and typed model entries. It must then prove that accepted `checkPatch`
requests select exactly the requested successor and preserve unedited buckets.
Typed node semantics alone does not establish this correspondence. Reference
counts, eviction, serialized persistence/replay, general factor row/equivalence
caches, acceptance completeness and full resource costs remain open. The supplied
adjacent-block family gives no unrestricted-SAT structural or coverage guarantee.
