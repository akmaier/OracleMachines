# Bounded retry for large recognized equivalence moves

The previous fixed proposal budget unnecessarily rejected a known block move.
`BudgetedRepairHistory` adds an optional, bounded retry. On a 1,024-variable
chain it reduces acquisition/update time from **0.78490 to 0.05932 s**, logical
payload from **189,168 to 99,129 bytes**, and peak traced Python allocations from
**3,071,073 to 1,741,448 bytes**. At 4,096 variables, total time falls from
**11.88170 to 0.27261 s**. These are synthetic, single sequential measurements.

## Policy and scope

The preceding scalar/equivalence/matching pipeline runs unchanged. If it fails,
the policy may retry only the first recognized base-equivalence block whose
joint aggregation exhausted the budget. The retry has `min(32768, 8*q)` visits,
where q is the block size, with default caps of 8,192 variables and 64-bit
variable identifiers. Each moved variable and posting costs a visit. There is
at most one retry. A zero ordinary or escalation budget disables it. Configuration
can set stricter caps. This experimental class is opt-in; the preceding engines
and their defaults remain available.

The recognized block is identified by its existing cached tuple. Completed
ordinary rejections, matching paths, parity moves and newly introduced equalities
do not receive the larger budget. A sorted block's largest variable identifies
the maximum trie-key length without a second scan. The policy retains a reference
to the tuple, not a copied model. It retries aggregation from the start; the
earlier failed work remains in the counters and timed operation.

The multiplier eight is a heuristic. A plain q-variable chain has 4q-4 postings,
so a complete proposal needs 5q-4 visits. Couplings, earlier additions and repeated
clauses can increase that number or make the final move invalid. Every accepted
move is independently checked against every affected clause, using the existing
`append-joint` format. A missed repair supplies no verdict. No minimum-cost,
uniform polynomial SAT, or new Lean refinement claim follows.

## Three matched policies

`fixed` is the unchanged matching engine with its case budget (usually 4,096).
`raised` uses that engine with 32,768 for every case. `targeted` uses the new
bounded policy over the ordinary case budget. This makes the simple alternative
visible: **globally raising the budget is slightly faster on the successful
chains and also repairs the dense controls that the targeted cap rejects**.
The evidence does not establish that targeted escalation has lower expected
cost. Its narrower extra-work envelope is a tradeoff, not a dominance result.

| Case | Total seconds fixed / raised / targeted | Fallbacks fixed / raised / targeted |
| --- | ---: | ---: |
| Chain, 1,024 variables | 0.78490 / 0.05637 / 0.05932 | 1 / 0 / 0 |
| Chain, 2,048 variables | 2.99486 / 0.12208 / 0.12418 | 1 / 0 / 0 |
| Chain, 4,096 variables | 11.88170 / 0.26717 / 0.27261 | 1 / 0 / 0 |
| Two blocks of 1,024 | 3.18143 / 0.12359 / 0.12807 | 2 / 0 / 0 |
| 1,024 variables plus 8,192 tautologies | 0.89220 / 0.11656 / 0.89334 | 1 / 0 / 1 |
| 32 parity updates | 0.17419 / 0.18421 / 0.17497 | 32 / 32 / 32 |
| 32 matching blocks of eight choices | 0.22779 / 0.23497 / 0.23089 | 0 / 0 / 0 |

At 1,024 variables, expansion alone falls from 739.17 to 13.29 ms; initial
preparation remains about 46 ms. The successful retry charges 5,116 visits in
addition to the original 4,096, and independent checking visits another 1,024
variables and 4,092 postings. Bases fall from two to one, SQLite from 356,352 to
196,608 bytes. At 4,096 variables, expansion falls from 11.67323 to 0.05553 s,
logical payload from 861,936 to 452,409 bytes and SQLite from 1,507,328 to
798,720 bytes. The two-block stream keeps one base instead of three and reduces
logical payload from 670,393 to 216,856 bytes.

Cold final replay is not cheaper: at 1,024 variables it increases from 43.48 to
45.25 ms, and at 4,096 from 200.53 to 220.76 ms. Repeating the known last update
from its parent after restart falls from 93.12 to 52.00 ms at 1,024 variables;
both archives already contain that result. Warm/cold query, resumed update,
database initialization, witness export and storage inspection are separate
fields in the report.

## Losses and next costs

The dense 1,024-variable control exhausts the retry's 8,192 visits and still
falls back. The raised policy succeeds and uses about half its logical storage.
The two-variable, 8,192-tautology control likewise receives only 16 retry visits.
These are concrete misses caused by the density cap, not hard SAT instances.
They motivate compressing logically inert postings or obtaining a better
cost estimate before choosing the retry allowance.

For an already pinned 2,048-variable block, appending its opposite unit is UNSAT.
The targeted retry correctly rejects it but increases expansion from 31.01 to
40.36 ms. Its 1,024-variable counterpart increases expansion from 16.30 to
19.17 ms and traced peak allocation from 3,013,284 to 3,087,252 bytes. History
couplings, explicit size/identifier limits, new equalities, nonpaired cycles,
mixed bases and non-unit matching conflicts are retained as controls.

The largest remaining total cost in this matrix is actually preparation of the
pinned 2,048-variable chain: 2.67 s before any expansion in targeted mode.
A separate in-memory cProfile run attributes 8.778 of 8.939 instrumented seconds
to `propagate` and its callees (about 98%). It charges 16,779,261 literal visits
for a source with 8,189 literal occurrences. The implementation repeatedly scans
the whole CNF rather than updating occurrences reached by newly forced values.
The next priority is a queue/occurrence propagation engine with independently
checked reasons and exact archive compatibility. This is an identified cost,
not a measured speedup from an implementation that does not yet exist.

## Reproduction, preservation and limits

Run from the repository root, selecting a **new** output directory:

```sh
python3 experiments/compare_cnf_budgeted_history.py --output /tmp/new-budget-study
python3 -m unittest discover -s solver -v
```

`report.json` retains exact cases, source fingerprints, timings, counters,
81 compressed SQLite archives and nine separate allocation runs. `summary.json`
is a derived compact view. The previous matching reader validates every new
archive (582 versions / 357 residuals) and all 74 matching-study archives
(1,414 versions / 608 residuals), with unchanged bytes and zero new expansions.
Tests also cover cold checking with discovery disabled, older-reader compatibility,
120 random branching additions, exact count reconstruction, conflicts, hard
limits and lack of persistent mutation on rejection. All **268 tests pass**.

Timing includes preparation, discovery, failed work, checking, maintenance,
serialization, SQL and fallback materialization. Input assembly, inter-operation
validation, offline compression and archive audits are outside timed acquisition.
Tracemalloc reruns are separate from timing and exclude native SQLite and RSS.
The preparation profile is separately instrumented and uses in-memory SQLite.
No representative workload distribution, significance estimate or comparison
with competitive incremental SAT solvers is provided. The joint semantic Lean
lemmas apply unchanged; Python policy, count indexes and persistence are not
formally refined by those lemmas.
