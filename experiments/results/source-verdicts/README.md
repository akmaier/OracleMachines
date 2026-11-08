# Complete successor formulas and returned native decisions

Runtime checkpoint: `9673dee`. This is a proof/correctness checkpoint. Earlier
timing evidence remains tied to its original executable and is unchanged.

## Proof and implementation

`SourceFormula.flatten_source` proves that ordered flattening of a complete
indexed interval is exactly the source node's original clause list. It preserves
order and multiplicity. `bucket_present` characterizes interval membership;
`bucket_padding` proves that padding contributes an empty array.

`replaceBuckets` defines the requested replacement function. `patched_buckets`
and `patched_formula` connect an accepted native patch to that function and the
complete flattened successor CNF. Both truth values have exact semantics:
`patched_decide` gives satisfiability, and `patched_unsat` gives absence of a
satisfying valuation. The proof needs no added edit-uniqueness assumption.
Flattening remains specification work and is not executed by a warm query.

`SourceVerdict.Covers` certifies the executed root checks: origin zero, enough
leaves for every logical edge, and the existing minimal padded height. Coverage
proves every logical edge is represented and transfers to the predecessor using
the patch's start/height equalities.

`SourceVerdict.query` retains the actual request root getter, current model
lookup, coverage and returned Boolean getter. The decision-only response getter
proof is definitional. Witness-mode calls use the existing decoded-answer
comparison; serialized witness values are not covered by this new theorem.

`compose_patch` identifies the queried node with the exact requested successor
and combines request decoding/bounds, both live root identities, both coverage
proofs, complete successor-formula equality and returned SAT/UNSAT semantics.
The patch response also certifies its nested `verdict` getter. Explicit
`SourceUpdates.query_success` and `patchQuery_success` theorems apply these
certificates to every successful call of the exposed JSON-returning functions.
Those functions execute the checked constructors. Existing unknown-root error
messages are preserved.

The result concerns native JSON values. Byte transport and the full initial
raw-CNF anchor remain separate. No source flattening, full-source scan or relation
summary recomposition is introduced on warm calls. Lookups, root checks, decoding,
comparisons, filters, wrappers, cached endpoint tests and requested witness work
remain costs. No new timing, memory or unrestricted-SAT guarantee is claimed.

## Verification

- **171 tests pass**, including **32 source-update tests**, without resource warnings.
- Lean audits **3,107 declarations / 1,506 theorem declarations**, with no admits
  or added axioms.
- Incomplete, shifted and oversized roots are rejected in direct-query and
  empty-patch modes, both with and without witnesses.
- Independent exhaustive truth tables check actual nested patch verdicts and
  direct queries against flattened original CNFs over 54 transitions.
- The transitions cover 1, 3 and 5 logical edges, padding, historical branches,
  deletion, repeated and empty clauses, and both SAT and UNSAT outcomes.
- Positive witnesses are checked independently; malformed witness-mode values
  are rejected. Existing diagnostic, rollback, dependency-lifetime and replay
  tests remain in place.
- All 355 older generic inputs pass revalidation and semantic audit. Five saved
  source versions pass checked adoption and restart.
- Every old row in 21 tables and all 206 prior experiment files remains intact.
  The archive now holds 8,165 results, 2,709 refutations and 55 source-state rows.

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

Connect the complete initial raw-CNF request and original-bucket traversal to
the live root in one successful-call theorem, then compose operation histories.
Serialized witnesses and their original-variable interpretation, byte transport,
Python active-root policy, complete replay/SQLite refinement, generic relation
and factor stores, acceptance completeness and total resource costs remain open.
The supplied adjacent-block representation gives no unrestricted-SAT coverage
or total-resource guarantee.
