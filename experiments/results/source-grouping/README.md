# Complete-source grouping and consistent paths

Runtime checkpoint: `75483cd`. This is a correctness/proof checkpoint, not a
timing comparison. Earlier experiments and measured timings are unchanged.

## Proof and implementation

`SourceGrouping.lean` carries the entire supplied CNF as a type parameter.
Its grouped original clauses form a permutation of that input, preserving every
occurrence, including duplicates and empty clauses. Each translated bucket
carries its equality with the corresponding original bucket under agreement.
The native loop uses a proved append operation and checks its accumulated flat
input against the supplied CNF before returning the proof-carrying result.

The original CNF is satisfiable exactly when one consistent sequence of bounded
block states satisfies every bucket. `LayeredSource.lean` proves that this is
equivalent to nonemptiness of the composed relation. Its whole-source tree SAT
and UNSAT theorems require exact ordered leaf binding and identity padding.
They do not prove that the mutable JSON/node protocol establishes those premises.

The flat builder adds clause-reference storage and a final equality pass. Entry
visits are linear in clause/literal count; allocation, large-integer operations
and compiled instructions remain separate costs. The existing relation ledger
does not count them. Warm local edits do not regroup the complete source.

## Verification

- **152 tests pass**, including 16 source-update tests; exact logs are retained.
- Lean audits **2,562 declarations / 1,233 theorem declarations**, with no admits
  or added axioms.
- The new global test uses seed 1901 and 60 CNFs: 20 at each width 1–3, with
  three blocks per CNF and sparse IDs above 64 bits. It checks all **11,680
  complete assignments**, exact ordered bucket contents, clause multiplicities,
  service verdicts and positive witnesses.
- A regression confirms that individually nonempty relations can have no shared
  global path. Further cases cover repeated empty clauses, final-block units,
  65,537 supplied blocks and a flat input containing 12,000 repeated clauses.
- All 355 older distinct generic inputs pass current-engine revalidation and
  semantic audit. All five older source versions pass checked adoption and
  restart. Earlier verdict bits are not treated as current-engine decisions.
- Every old row in all 21 tables remains present. All 150 previously tracked
  experiment files retain their hashes. The archive now has 5,680 generic results
  and 1,806 refutations. The ignored local SQLite backup and preservation checks
  are recorded in `preservation.json`.

```sh
cd formal
lake build OracleMachines oracleSolver
cd ..
python3 -m unittest solver.test_source_updates
python3 -m unittest discover -s solver -p 'test_*.py'
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

`verification.json` records source and binary fingerprints. `paper-check.json`
records manuscript rendering checks. `source-study-recheck.json` validates the
historical source fingerprints, all 1,824 old outcomes and lifecycle arithmetic.
It reports the changed current binary separately; it does not rerun the old
executable or update its timings.

## Remaining obligations

The main next proof is native source-tree binding and node-identity preservation
through initialization, joins, patches and replay. Reference-count/eviction and
general factor row/equivalence-store invariants remain separate. Successful
typed compilation has the stated semantics; acceptance of every promised input,
JSON decoding, Python/SQLite and physical resource costs are not fully refined.
No efficient decomposition, small representation or uniform coverage guarantee
for unrestricted SAT follows from this checkpoint.
