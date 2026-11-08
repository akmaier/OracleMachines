# Executable complete-source binding

Runtime checkpoint: `bc977eb`. This is a proof/correctness checkpoint, not a
timing comparison. Earlier experiments and measured timings are unchanged.

## Proof and implementation

`SourceBinding.lean` checks the actual stored `CheckedTree` against the complete
compiled original CNF. It checks width and capacity, then compares every ordered
logical leaf with its source relation or individual identity-padding relation.
The returned `BoundCompilation` carries the exact leaf equality and tree validity.
Its executed Boolean decision has positive and negative equivalence theorems for
the original CNF. Both native `layered_source_query` and initial `source_bind`
use this result. The latter retains its original-clause/provenance checks.

The accumulator traversal is proved to preserve leaf order. It visits expanded
tree occurrences, not merely distinct shared native nodes. The tail-recursive
scan is proved to accept exactly equal leaf lists. It returns a proved count of
one relation comparison per logical leaf on success, and at most the actual
leaf count on failure. Counts concern comparison calls, not machine instructions.

Both Python interfaces report the padded leaf count N, comparison calls, and
reference bounds N*q² and (N+c+L)*q², where q=2^width, c is the source clause
count and L its literal count. Only comparison calls have a new executable
counting theorem. The other bounds apply the existing row/clause/literal ledger;
the aggregate native cost is not proved. Mask/bit costs, source indexing,
allocation, endpoint queries, witnesses, JSON and storage are separate costs.
Initial source-version binding adds a source-relation scan. Full-source layered
queries already compared those relations. Warm queries and local edits do not
run the new scan. No speedup, memory reduction or hard RSS bound is claimed.

## Verification

- **156 tests pass**, including 30 focused priority/source-update tests.
- Lean audits **2,615 declarations / 1,259 theorem declarations**, without admits
  or added axioms. Build and test logs are retained.
- Wrong ordered leaves are rejected even when their final SAT/UNSAT answer agrees.
- Nonidentity padding is rejected even when its combined relation is identity.
- Width/capacity mismatches, valid witnesses and counts at widths 1, 2 and 4 pass.
- A tree with only **17 distinct native nodes** expands to **65,536 logical
  leaves**. At width one, the accepted scan reports 65,536 comparisons and a
  262,144-cell reference bound. This is a stack/shared-occurrence regression,
  not a speed benchmark or bound in the number of unique nodes.
- All 355 distinct older generic inputs pass current-engine revalidation and
  semantic audit. All five saved source versions pass checked adoption and restart.
- Every old row in all 21 tables remains present, and all 158 prior experiment
  files retain their hashes. The archive now has 6,035 generic results and 1,935
  refutations. `preservation.json` records the ignored SQLite backup and checks.

```sh
cd formal
lake build OracleMachines oracleSolver
cd ..
python3 -m unittest solver.test_priorities solver.test_source_updates
python3 -m unittest discover -s solver -p 'test_*.py'
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

`verification.json` records source/binary fingerprints and validation counts.
`paper-check.json` records rendering checks and preservation of all 32 previous
manuscript proof blocks. `source-study-recheck.json` validates 73 historical
source fingerprints, all 1,824 old outcomes and lifecycle arithmetic. It reports
the changed current binary separately; it does not rerun the old executable or
replace its timings.

## Remaining obligations

Initial complete-source binding is supplied. Original-source node identity,
layout, start and span still need a state invariant preserved by native joins,
patches and replay. Reference-count/eviction and general factor row/equivalence
store invariants are separate gaps. JSON decoding, acceptance completeness,
Python/SQLite and full resource costs remain outside the proved boundary.
No efficient decomposition, small representation or uniform coverage guarantee
for unrestricted SAT follows.
