# Exact native source-patch semantics

Runtime checkpoint: `32b4748`. This is a proof/correctness checkpoint. Earlier
timing evidence remains tied to its original executable and is unchanged.

## Proof and implementation

`SourcePatch.Patched` preserves start and height, sets every requested edge to
its supplied original clause array, and preserves every unedited bucket. The
leaf lemma compares original arrays, including literal order, duplicate clauses
and empty clauses. The join lemma combines the two filtered requests at the
typed partition boundary. Equal relation summaries do not identify source arrays.

`LiveNode` connects actual native relation/model lookups to the paired-store
invariant. `readParts` decodes live child names, reads their current models and
uses the dependency invariant to identify the exact consecutive join. This join
equality erases; no relation summary is recomputed by patch checking.

`checkNodes` returns a visit count with the bucket-transition proof. An empty
edit list requires identical names; a leaf compares its original array; a branch
combines the recursive certificates. `check` records the actual live root names.
`checkRequest` retains the actual JSON base/root/edits getters, the batch bound,
entry-by-entry edge/clause decoding and logical-edge bounds. Duplicate rejection
remains executed; the transition proof does not assume uniqueness.

`SourceUpdates.patchQuery` uses this checker before querying the same unchanged
store and request. Comparison now uses decoded original arrays, with malformed
arrays rejected by decoding. Changed unedited identities are still rejected even
when their original sources are equivalent; acceptance completeness is not claimed.

The bucket function and transition propositions are specifications, erased from
runtime checking. Lookups, direct child getters, filtering, array comparisons and
temporary wrappers remain runtime costs along visited paths. There is no flat
source scan or summary recomposition. The visit counter is not a complete native
instruction, allocation, RSS or bit-cost theorem. No timing improvement is claimed.

## Verification

- **169 tests pass**, including **30 source-update tests**, without resource warnings.
- Lean audits **3,043 declarations / 1,461 theorem declarations**, with no admits
  or added axioms.
- New tests cover two edits in opposite tree halves with padding, request order,
  equal-relation payload forgeries, duplicate clauses and literal order.
- Omitted edits, changed unedited aliases, wrong partitions, missing roots,
  malformed arrays, duplicate requests and out-of-range edges are rejected.
- The complete 4,096-entry batch is decoded before root lookup; 4,097 entries
  are rejected at the cap, and the worker remains usable.
- Existing randomized edits, shared dependencies, rollback, historical branches,
  tight working-set caps, identity reuse and restart checks remain in place.
- All 355 older generic inputs pass revalidation and semantic audit. Five saved
  source versions pass checked adoption and restart.
- Every old row in 21 tables and all 198 prior experiment files remains intact.
  The archive now holds 7,810 results, 2,580 refutations and 50 source-state rows.

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
comparisons. `paper-check.json` records visual review of the revised PDF and
preservation of all 32 earlier manuscript proof blocks.
`source-study-recheck.json` validates 73 historical source fingerprints and 1,824
recorded outcomes. It neither reruns the earlier executable nor replaces timings.

## Remaining obligations

Compose initial raw-CNF binding, complete root coverage, the bucket-to-flattened-CNF
transition and the returned verdict/witness into one successful-request theorem.
Native patch soundness is now proved; Python retention, complete replay/SQLite
refinement, generic relation/factor stores, acceptance completeness and complete
resource accounting remain open. The supplied adjacent-block representation
does not establish unrestricted-SAT coverage or a total-resource guarantee.
