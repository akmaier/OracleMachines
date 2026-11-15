# Complete the retained development subset

2026-11-15. Two independent six-batch histories raise checked structural coverage
**78/83 -> 83/83**, completing the five remaining development originals. There is
no selected continuation or pending split in the final global query. This closes
this retained subset, not the problem of classifying arbitrary CNFs efficiently.

## Acquisition and complete recomposition

| Batch | Original | Initial variables / clauses / literals | Entries | Stored | Result |
| --- | --- | --- | ---: | ---: | --- |
| 0 | 1196 | 43 / 181 / 549 | 26 | 26 | Original closes; SAT |
| 1 | 1376 | 43 / 186 / 562 | 22 | 22 | Original closes; UNSAT |
| 2 | 1064 | 44 / 177 / 523 | 26 | 26 | Original closes; SAT |
| 3 | 1302 | 44 / 184 / 552 | 18 | 18 | Original closes; UNSAT |
| 4 | 1443 | 46 / 183 / 539 | 32 | 29 | Pending split at 43 / 172 / 510; three inputs interrupted |
| 5 | 1443 | 43 / 172 / 510 | 23 | 23 | Remaining branches and original close; SAT |

Every batch retains the existing **32-state / twelve-advance limits**. This run
permits six batches instead of four; its sequence times are not matched comparisons
with the earlier shorter runs. The total is **147 admission entries / 144 distinct
inputs**, with three interrupted inputs re-entered and completed. No admitted input
remains unstored. The final batch's selector retains empty original-index labels;
checked ancestry supplies scope **1443 / index 72**.

The last original needs several distinct conditioning obligations. The selected
size changes from 40 variables to 43 when the query switches branches; it is not
growth of the same residual. Subsequent selected sizes are 37 and 34 variables.
Both cofactor premises are retained and checked for structural recomposition.
The independent reference answers are **three SAT and two UNSAT originals**.
Intermediate refutations remain conditional on their checked source ancestry.

The new delta contains **98 probes, sixteen eliminations, fourteen binary-path
reductions, ten unresolved records, four family terminals and two polarity
transformations**. The final positive original-coverage proof includes
**10 of the ten new unresolved records** through external composition;
stored node payloads retain their original outcomes. Sixteen new split records
increase the split-evidence count from 82 to 98. Prepared trace acquisition and
reference evidence remain paid resources, not free oracle answers.

## Which families close the remaining branches?

| Variables / clauses / literals | Checked overlapping classes | Satisfying / all assignments |
| --- | --- | ---: |
| 13 / 19 / 42 | horn, zero_valid | 50 / 8192 |
| 10 / 11 / 23 | horn, zero_valid | 60 / 1024 |
| 6 / 7 / 14 | two_cnf | 13 / 64 |
| 5 / 5 / 10 | dual_horn, one_valid, two_cnf | 10 / 32 |

The **13/19/42** and **10/11/23** Horn targets follow checked polarity transformations.
Their source size triples are unchanged. The **6/7/14** terminal is 2-CNF while the
recorded Horn, dual-Horn and both constant-assignment tests are excluded. The
**5/5/10** terminal overlaps dual-Horn, 2-CNF and one-valid. These are applications
of established recognizers; they do not add a new tractable family.

A separate diagnostic directly checks the five syntactic class predicates and
enumerates all **9,312 assignments** across the four small terminals. It also
checks both polarity maps on all **9,216 source assignments**, including the
variable-name maps, and confirms equal source/target model counts. This costs
**0.19350 seconds** beyond production and cold replay.
The exhaustive checks are deliberately bounded and do not supply an efficient
procedure for arbitrary CNFs.

## What reuse is actually established?

Touched split prefixes contain **170 occurrences /
148 distinct records**, including **4 inherited records**.
Their nonempty intersections with the preceding checkpoint contain only these
record kinds: **retained_plan**. Within this sequence:

| First original | Second original | Shared exact prefix records | Shared new records |
| --- | --- | ---: | ---: |
| 1064 | 1196 | 1 | 0 |
| 1064 | 1302 | 1 | 0 |
| 1064 | 1376 | 1 | 0 |
| 1064 | 1443 | 1 | 0 |
| 1196 | 1302 | 1 | 0 |
| 1196 | 1376 | 1 | 0 |
| 1196 | 1443 | 1 | 0 |
| 1302 | 1376 | 1 | 0 |
| 1302 | 1443 | 1 | 0 |
| 1376 | 1443 | 1 | 0 |

These are measured prefix intersections, not all proof alternatives or an
exhaustive search for semantic equivalence. Repeated family names and reduction
shapes do not justify certificate transport. The remaining discovery gap is
certified sharing of nonterminal or boundary descriptions on genuinely new inputs.
It includes acquiring the forcing evidence that enables the many probe steps.

The complete selected original-coverage proof gives a broader, still bounded view.
All **4,822 steps** are reachable from its **83 roots**. Only **fourteen exact steps**
are used by more than one original: ten family leaves and four direct retained-plan
references to family leaves. All shared CNFs have **at most two variables**. They
include empty conjunctions, contradictions, unit clauses and tiny binary formulas.
Thus the shared nonterminal steps are references to already resolved small families,
not shared elimination or probing chains on larger cores.

The sum of separate per-original distinct-step visits is **4,991**, versus **4,822
unique steps**, giving **169 repeated visits**. A reverse traversal with owner
bitsets and independent root-by-root traversals agree. This diagnostic costs
**0.06660 seconds** separately. These are graph-overlap counts, not measured runtime
savings or avoided acquisition. They cover this selected certificate, excluding
alternative plans, acquisition traces and the reference solver's proof graph.
Different variable names or configurations may hide other equivalent components;
the count does not establish their absence.

New pattern keys occupy **339,089 bytes**, payloads
**898,665 bytes**, and stored CNFs contain
**46,798 literal slots**. These are representation counts,
not demonstrated net compression savings after indexes, checking and reconstruction.

## Scope of the completed subset

The diagnostic binds the historical
`experiments/results/cnf-retained-plans-full/report.json` by SHA-256
`6b09f04a02286d4a9ca5ac692ea0bf4d7b481f90b2ce3c2fad9490aab42ddc32`.
All **83 source formulas exactly match the 83 recorded misses** of its retained
policy on **1,497 historical inputs**. The subset has been repeatedly and adaptively
used for development. It is not a fresh holdout.

This input-identity check does **not** perform a fresh combined-policy replay of
the full historical corpus. The old prepared result of **902/985 non-tiny sources**
remains a separate measurement. Historical and current options differ, and old
plans need explicit source/configuration binding in a combined query. Do not
report a new full-corpus runtime or a fresh 985/985 evaluation by adding counts.

## Charged costs and validation

Mean six-batch sequence time is **77.64131 seconds**, including
**64.54345 seconds** initial catalog/query/serialization,
**7.85484 seconds** in workers and **3.20071 seconds**
local expansion within workers. Updated global queries cost
**1.72922 seconds**, their serialization
**2.69424 seconds**. Parent restoration adds
**27.63698 seconds**. Materialization is allowed but actual cache/fallback
use is not reported by the parent wrapper. No new full structural-history snapshot is stored.
Six batch copies total **4,709,650,432 logical bytes** per sequence. Final route
preparation costs **9.32521 seconds**, global coverage
**63.29751 seconds**, and the full producer
**292.73114 seconds**. Lightweight source inspection overlapped its last
stage. These are reproducibility runs, not matched speedup measurements; peak RAM
remains unmeasured.

History grows **2,019,328 bytes** to **786,116,608 bytes / 42,876 patterns**.
The structural delta uses **2,097,152 SQLite bytes / 108,380 compressed bytes**.
Separate reference evidence grows **6,779 -> 8,789 nodes**, adding **15,405,056
SQLite bytes**, to **62,128,128 bytes / 4,212,090 compressed bytes**. Initial checking
dominates local expansion time; reference evidence dominates new working database
bytes. Neither is a bound on worst-case expansion or peak memory.

The saved reproducibility bundle contains **187 manifested artifacts totaling
18,886,631 bytes**, excluding the manifest itself. It includes repeated query
proofs, the reference archive, diagnostics and logs. These saved bytes are separate
from working-database growth and the older optional structural-history snapshot.

All **299 tests** pass before production. Independent reconstruction disables
materialization and fresh discovery/reference search. It checks both histories,
every acquisition prefix, **14 saved global queries**, original SAT models and all
**8,789 reference nodes**. Its **1234.36954 seconds** are an audit cost. All
**2,650 prior artifacts / 43 manifests**, **145 prior source fingerprints** and
**6,779 old reference payloads** remain unchanged. See the
[saved experiment](../experiments/results/cnf-case1196-discovery/README.md).

## Next investigation

Restore the completed checkpoint with
`experiments.continue_cnf_case1196_discovery.restore_checkpoint` and
`experiments/results/cnf-case1196-discovery/report.json`. Preserve evidence
**(1,42,156,98,1)** and **two bridges**. Its **`next_selection.source` is null**;
do not resume the completed initial case 1196 or invent another pending obligation.

The next coverage question concerns **new inputs**. First bind the historical
successful plans and this completed subset in an explicit combined query and
check full-corpus regression without fresh acquisition. Then freeze the policy
and budget before a new unlabelled sample with growing sizes and adversarial
mixtures or edits. Compare prepared and empty history on matched formulas, charging
trace discovery, verification, persistence and cold replay. Preserve unresolved
cases rather than tuning the policy on their labels. The central test is whether
stored structure reduces acquisition on inputs absent from the prepared archive.
Finite corpus completion supplies neither compact closure nor a uniformly
polynomial solution covering every CNF.
