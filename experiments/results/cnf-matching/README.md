# Recognized matching removes a residual-search bottleneck

8 November 2026. This extends the separate research candidate; it does not change
the production solver's trusted path or establish polynomial time for every CNF.
The manuscript proves the matching reduction, and
`research/residual-candidate.md` records its bounds and remaining scope.

## Recognized structure and correctness

Positive clauses must have pairwise disjoint variable sets. Every remaining
clause must be a negative pair, and each connected component of their conflict
graph must be a clique. Positive clauses are choices; conflict cliques are
resources. A variable belongs to one resource and at most one choice. A SAT
assignment gives a matching covering all choices, and such a matching produces
a full source witness. A failed augmenting-path search returns a set of choices
with fewer neighboring resources, checked independently as a Hall obstruction.

This is established matching reasoning; Lenchner's 2019 CMP-SAT preprint is a
direct SAT precedent. We claim neither a new tractable class nor a full
implementation of its broader recognition transformations. The implementation
checks explicit structure only. Overlapping positive clauses or a missing
conflict-clique edge can invalidate the argument, and both have satisfiable
counterexamples in the tests. Those cases continue through general search.

With p choices and e choice-resource edges, matching uses O(p*e) graph traversals
after sorting adjacency lists. Recognition, source normalization, repeated-scan
unit propagation, checking, full-key construction, serialization and SQLite are
also charged. Their costs are polynomial on this family. A single acquired node
does not mean constant work or memory. Full process peak RSS and a complete
Lean bit-cost simulation are not supplied.

## Matched measurements

The report contains **39 inputs / 153 decisions / 75 retained archives**. There
are 36 matched acquisition comparisons, plus matching-only sizes 12/24/48 holes.
The matching mode also has warm and cold replay for every input. Expected
answers all agree. Single timing samples were collected after the test and Lean
jobs completed; mechanism counts, rather than a general speedup estimate, are
the primary evidence. The baseline is the previous portfolio, not competitive
external CDCL.

| Pigeons / holes | Previous expanded nodes | Matching expanded nodes | Previous logical bytes | Matching logical bytes |
|---|---:|---:|---:|---:|
| 4 / 3 | 8 | 1 | 4,407 | 494 |
| 5 / 4 | 34 | 1 | 28,578 | 971 |
| 6 / 5 | 122 | 1 | 151,642 | 1,720 |
| 7 / 6 | 416 | 1 | 741,698 | 2,808 |
| 8 / 7 | 1,436 | 1 | 3,554,525 | 4,282 |
| 9 / 8 | 5,191 | 1 | 17,290,081 | 6,208 |

At eight holes, observed acquisition time changes from 6.166 seconds to 0.0021
seconds in this implementation. This is one observation, not a robust timing
study. Cold checking visits one source/Hall certificate node instead of 5,191
dependency nodes. At 48 holes the matcher still acquires one node, but source
and retained payload grow to **1,496,174 bytes**. The explicit pigeonhole input
contains O(h^3) literal occurrences, or O(h^3 log h) encoded bits, for h holes.

`cold-baseline-verification.json` additionally records cold replay of all seven
previous-portfolio pigeonhole archives, confirming the 5,191-node cold check
at eight holes with zero new search and unchanged rows. These supplemental
checks are separate from the 153 decisions in the main report.

Satisfiable matching instances with 4/8/16/32 choice groups take one node, versus
6/14/30/62 for the previous portfolio. Thirty-two repeated general components
still require six nodes: matching recognition does not solve that different
structure. Near misses remain in the report, including an overlapping-choice
case where recognition adds overhead and does not reduce the four-node search.

Every warm/cold replay adds zero new residual nodes. All **104** earlier
experiment archives were decompressed, hash-checked, reopened, and semantically
rechecked by the new reader without adding or changing any row. The new 75
compressed SQLite snapshots occupy **2,600,231 bytes**. Compression is offline
evidence packaging, not an online solver optimization. Full CNFs remain the
exact database keys; copied keys and source payloads are included in logical
storage. The prior artifacts and all unsuccessful cases remain intact.

## Verification and reproduction

All **220** repository Python tests pass. This includes the previous complete
two-variable CNF enumeration, random checks, corruption tests and budget tests,
plus all 512 three-by-three matching-domain graphs, recognizer near misses,
and cold Hall-certificate rejection after tampering. The 512 graph cases include
empty domains; those are rejected by recognition and handled as empty clauses.

Lean's audit passes **4,062 declarations / 1,925 theorem declarations** without
new axioms. The additional theorem is the finite-cardinality obstruction to an
injective choice. It does not verify the entire Python checker or connect its
CNF source to a native acceptance theorem. The matching proposition's full
CNF-to-graph equivalence is proved in the manuscript.

```sh
python3 experiments/compare_cnf_matching.py --output /tmp/cnf-matching-new
python3 -m unittest solver.test_cnf_residuals -v
```

Source and driver fingerprints, literal/edge counters, all source CNFs, row
digests and archive hashes are in `report.json`. Initialization time is separate.
Solve timing includes reporting's final SQLite size scan; offline digest checks,
snapshots, compression and JSON report writing are excluded. No main production
solver database is used by either experiment.

The remaining universal gap is overlapping positive requirements. The earlier
indicator construction embeds arbitrary CNF in this syntax with disjoint
negative pairs, so a polynomial algorithm for arbitrary positive overlap would
solve unrestricted SAT. No such algorithm or uniform polynomial residual-count
bound has been established in this checkpoint.
