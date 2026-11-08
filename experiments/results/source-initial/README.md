# Initial raw-CNF binding and returned native verdict

Runtime checkpoint: `92a1ddd`. This is a proof/correctness checkpoint. Historical
timing evidence remains tied to its original executable and is unchanged.

## Proof and implementation

`SourceInitial.compileSource_fields` derives actual width/layers/clauses getter
equations from success of the existing compiler. `readCompilation` retains them
without reparsing or compiling twice. `checkBinding` follows the current live
children, whose exact consecutive-join relationship is already proved. It
compares every original leaf array with its compiled bucket, including literal
order and repeated/empty clauses. Padding is compared with the empty array.

`matches_complete` proves that the live clause list equals the concatenation of
all compiled original buckets. `matched_partition` composes this with the compiler's
permutation proof, preserving every occurrence from the actual raw input. Global
input order may differ from grouped tree order. `partition_eval` proves equality
under every original-variable valuation.

`InitialResponse` combines actual request fields, live identity, layout agreement,
root coverage, exact buckets, clause permutation, nested verdict and returned
SAT/UNSAT semantics. `SourceUpdates.bindSource_success` applies to the exposed
native JSON-returning function, which executes this constructor. The existing
relation-binding scan and decoded-answer comparison remain executed. The verdict
is returned unchanged after that comparison.

The actual returned `binding_visits` getter is certified, with
`visits + 1 = 2^(height + 1)` and `height < 17`. This counts logical node visits
including padding. It excludes map access, parsing, array comparisons, allocation,
the separate relation scan and witness work. Initial binding remains a full scan;
warm queries and patches are unchanged. Flattening and composition of proofs
remain specifications. No speedup, physical-memory bound or unrestricted-SAT
claim follows.

## Verification

- **174 tests pass**, including **35 source-update tests**, without warnings.
- Lean audits **3,154 declarations / 1,539 theorem declarations**, without admits
  or added axioms.
- Global clause permutations preserving grouped arrays are accepted. Dropped or
  added duplicate clauses and changed literal order are rejected even when SAT
  answers agree. One empty clause is distinguished from two.
- Both decision and witness response modes exercise the actual nested verdict.
- Exact complete scan counts hold for 1, 2, 3, 5, 17 and 33 logical edges, with
  padding. These tests are not a cap-wide acceptance-completeness proof.
- Wrong layouts, malformed fields, partial/shifted/missing roots and invalid
  witness-mode fields are rejected while the existing live root remains usable.
- All 355 older generic inputs pass revalidation and semantic audit. Five saved
  source versions pass checked adoption and restart.
- Every old row in 21 tables and all 214 prior experiment files remains intact.
  The archive now holds 8,520 results, 2,838 refutations and 60 source-state rows.

```sh
cd formal
lake build OracleMachines oracleSolver
cd ..
python3 -m unittest solver.test_source_updates
python3 -m unittest discover -s solver -p 'test_*.py'
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

`verification.json` records 91 source/binary fingerprints and the checks.
`preservation.json` identifies the ignored SQLite backup and records old-row and
artifact comparisons. `paper-check.json` records visual review of the revised
PDF and preservation of all 32 earlier manuscript proof blocks.
`source-study-recheck.json` validates 73 historical source fingerprints and 1,824
recorded outcomes. It neither reruns the historical executable nor replaces timings.

## Remaining obligations

The initial, query and patch APIs have individual native success theorems.
Compose them across operation histories with evolving stores and retained source
identities. Serialized witnesses and original-variable interpretation, byte
transport, Python active-root retention, replay/SQLite refinement, generic stores,
acceptance completeness and total resource costs remain open. The supplied
adjacent-block representation establishes no unrestricted-SAT coverage guarantee.
