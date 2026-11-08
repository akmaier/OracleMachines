# Original-variable mapping and checked local translation

Runtime checkpoint: `dd0c44c`. This is a correctness/proof follow-up. The earlier
source-update timing study and all other historical experiment files are intact.

`SourceMapping.lean` ties each native position to the original block-array entry
and its width bound. An executable completeness check covers every coordinate.
Global valuations encode into bounded block states; arbitrary block states give
agreeing global valuations. Literal, clause and local CNF translations carry
semantic equality for their supplied source. The initial compiler uses checked
clause translation; the local-edit compiler returns `CheckedCNF`. SAT and UNSAT
equivalence are proved for each checked local bucket.

The iterative builders compare accumulated original arrays with the requested
input before returning. This adds passes and temporary arrays. The layout check
adds block traversal and one lookup per variable entry. Initial grouping also
looks up literal positions before translation. These entry visits, large-ID
hashing/comparison and allocation are outside the existing relation-evaluation
counter. No speedup or complete machine-cost bound is claimed here.

## Checks

- **148 tests pass**, including 12 source-update tests. Exact build/test logs are
  retained in this directory.
- **2,477 Lean declarations / 1,188 theorem declarations** pass the transitive
  axiom audit, without admits or added axioms.
- Both native compiler paths agree with exhaustive boundary enumeration on 112
  local CNFs: 28 per width, widths 1–4, 9,520 assignments per path in total. The
  fixed random seed is 1897; IDs exceed 64 bits and slots are permuted.
- Additional native rejection tests cover duplicate, zero and missing IDs,
  oversized blocks and nonlocal literals. Source tests cover empty/short blocks,
  unused variables, empty clauses versus empty buckets, local edits, old branches
  and restart. A 30,001-literal clause and 12,000-clause bucket check long inputs.
- All 355 distinct older generic inputs pass current-engine revalidation and
  semantic audit. All five saved source versions pass checked adoption and
  restart. Older verdict bits are not imported as current decisions.
- Every old row in all 21 tables remains present. All 142 previously tracked
  experiment files retain their hashes. The live archive now has 5,325 generic
  results and 1,677 refutations. The SQLite backup is local and ignored by Git;
  `preservation.json` records its location and all preservation checks.

```sh
cd formal
lake build OracleMachines oracleSolver
cd ..
python3 -m unittest solver.test_source_updates
python3 -m unittest discover -s solver -p 'test_*.py'
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

`verification.json` records the exact runtime revision, source/binary hashes and
check scope. `source-study-recheck.json` validates historical source fingerprints,
all 1,824 saved outcomes and lifecycle arithmetic. It reports the current binary
separately and does not rerun the historical executable or refresh its timings.

## Remaining boundary

The next proof should compose local translation with global clause grouping and
native source-tree binding. Every original clause must reach its intended edge,
and node/layout identities must retain that meaning through requests and edits.
The current local proof does not establish that whole-service property. Native
and Python reference-count/eviction invariants, the general factor row/equivalence
store invariant, JSON/SQLite refinement, and complete physical-resource accounting
also remain open. No efficient decomposition or coverage premise is established
for unrestricted SAT.
