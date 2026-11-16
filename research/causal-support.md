# Causal unit supports for negative cofactor reuse

The previous [witness-signature study](witness-signatures.md) left all fresh
expansions on negative queries. Its costly cases share conditional structure,
but the old support extractor retains every unit-propagation reason, including
assignments unrelated to the contradiction. This study removes those irrelevant
dependencies while keeping the unchanged residual proof format and checker.
The supports remain proof-dependent and need not be minimum unsatisfiable cores.

## The preserved implication

At a checked unit-proof node, let A be its complete propagated assignment. The
node ends either in a falsified clause or a checked negative residual child.
For a conflict, begin with the variables of that clause. For a negative child,
first extract its selected support and lift those residual clauses to actual
parent clauses. Begin with the variables of those clauses that A assigned.

Scan the already checked unit trace backwards. Retain an assignment precisely
when its variable is needed. Retaining its reason clause also makes all other
variables in that reason necessary. They occur earlier in a valid unit trace,
so the backwards pass closes the dependencies. Preserve the original order of
the retained subsequence. The implementation rejects an unresolved dependency.

Each retained assignment is still forced: every other literal in its reason
is false under an earlier retained assignment. For a conflict, all its literals
are therefore false under the retained trace. For a child, every assigned variable
appearing in a selected parent clause is retained, so restricting those clauses
by the smaller assignment gives exactly the same selected child clauses.
Retained reason clauses are satisfied by their forced literals. Thus the selected
parent clauses plus those reasons remain UNSAT. The code checks equality of the
required residuals and publishes only through the ordinary residual verifier.

If no unit is needed for the child, its extracted core already supplies the
required normalized negative root. This avoids publishing an empty unit trace
or a self-referential certificate. Existing component, split, implication, Hall
and subsumption rules remain in use; recursive core choices can change. The
local slicing argument concerns the selected child support, not a claim that
every resulting core is a subset of every earlier extraction.

Index-only discovery stores descriptions without derived proof rows. On a match,
`CausalCoreBank` materializes the support using the same causal extractor and
checks its ordinary negative proof before subset publication. A target cofactor
still needs the complete query and its checked guard; a negative child alone is
not a complete-query certificate. Pending descriptions never justify UNSAT by
themselves. Complete proof/query and historical-lineage checks remain charged
in the cold audit, including unmatched entries.

## Discovery cost and persistence

At each unit node the extra backwards pass examines the original trace and the
literals in retained reason clauses. Selecting child preimages and checking the
required residuals also cost work. Across a shared proof DAG, the extractor memo
visits a node once per extraction session; input proof validation, normalization,
coordinate transport, containment and publication remain separate charges.
This is a graph-relative bound, not a polynomial bound in the original CNF size:
the acquired refutation and extracted proofs can be exponentially large.

The causal bank must use its matching materializer. The older bank and its raw
history remain intact. An ordinary checked root can be reused regardless of how
it was acquired, but a missing causal root cannot silently be reconstructed with
the old all-units extractor. A changed derived identity fails closed. Current
discovery rebuilds supports from all selected origins; incremental refinement
of the causal bank is not implemented in this study.

The method does not minimize cores, find all interchangeable clauses, search for
arbitrary variable renamings or prove efficient coverage of every CNF. A smaller
description can require additional checked proof construction and storage. Its
value is measured against both the saved bank and an extended bank using the
same new sources with the previous extraction rule.

## Historical diagnostic

The read-only probe uses seven previously identified negative cases, with fresh
solving and publication disabled. Their old/causal support sizes are:

| Previous catalog case | Old clauses | Causal clauses |
| --- | ---: | ---: |
| 123 | 49 | 26 |
| 189 | 49 | 34 |
| 74 | 54 | 38 |
| 106 | 48 | 41 |
| 42 | 42 | 27 |
| 157 | 44 | 29 |
| 175 | 44 | 29 |

Across their shared proof traversal, 254 of 532 unit steps disappear from the
selected supports. Cases 123 and 189 still have different cores despite their
common guard. Cases 157 and 175 acquire mutual support containment that the
old extractor did not find. These are proposal-level historical observations;
actual query transfers require ordinary checked materialization. The probe is
preserved in `experiments/results/cnf-causal-support-probe`.

## Matched fresh-stream comparison

Every worker starts from the current 17,947-key union. Selection excludes all
1,536 prior sidecar answers and cached complete roots, then takes 64 further
two-deletion neighbours per template. Three balanced fresh-process triples visit
each query twice. Timed workers run without overlapping tests, builds or profiles.
All modes retain the old whole-query core and one-clause SAT witness routes;
the unsuccessful positive-exploration mode stays disabled.

The active control loads the existing 170-entry frontier from 286 origins.
The extended control applies the old extractor only to 103 newly acquired
negative cofactors, producing 232 raw supports and 207 frontier entries from
389 origins. The causal candidate re-extracts all 389 origins with unit slicing,
giving 189 raw supports and 176 frontier entries. This comparison separates
adding sources from changing the support description. Preparation publishes no
proof rows in any mode; actual matches trigger checked materialization.

| Mode | Cofactor hits | Expansions / splits | New rows | Complete seconds | Query seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Active saved frontier | 29 | 195 / 65 | 423 | 10.89172 | 1.66936 |
| Extend with old extraction | 29 | 195 / 65 | 429 | 11.63135 | 1.28432 |
| Causal extraction | 38 | 100 / 33 | 553 | 12.61998 | 1.21800 |

Nine additional negative targets—cases 6, 23, 27, 32, 112, 120, 131, 171 and
182—account for all 95 saved expansions, a **48.72% reduction**. No query has
more expansions. All modes answer **95 SAT / 97 UNSAT**, with 52 guards including
one positive child. Repeated visits add no rows. Every observed causal hit still
shares the first origin's guard clause; broad cross-guard reuse is not demonstrated.

Causal discovery removes **5,585 of 14,613** examined unit steps (38.22%) while
traversing 2,851 proof nodes. The extended control traverses 873 nodes because it
reuses the old index. Retained clause occurrences fall **7,385 -> 4,568 (38.14%)**
relative to extension. These are smaller exact descriptions and greater measured
containment coverage, not minimum cores or general semantic equivalence classes.

## Where the saving is lost

Complete runtime is **15.87% higher than active loading**, and **8.50% higher than
extension**, with both regressions in every matched triple. Query time is 27.04%
lower than active and 5.16% lower than extension. Extended preparation also warms
the ordinary proof checks; its lower query time without fewer expansions must
not be attributed to new structural coverage. All preparation remains charged.

Causal preparation costs **2.33282 seconds**, versus 0.08516 for active loading
and 0.95163 for extension. Its 31 matched missing roots require **275 new proof
rows**, versus 59/65 for active/extended. The row accounting is explicit:

- Active: 195 expansions + 59 materialization rows + 94 SAT witness publications
  + 46 whole-query core publications + 29 cofactor publications = 423 new rows.
- Causal: 100 expansions + 275 materialization rows + 94 SAT witness publications
  + 46 whole-query core publications + 38 cofactor publications = 553 new rows.

Thus smaller descriptions do not imply fewer retained proof nodes. The causal
trial has 34 available frontier roots and 142 pending descriptions. The extended
trial has 117 available and 90 pending. Unmatched pending entries remain proposals,
and all current-query guards and used core proofs still require checking.

Mean peak RSS is 2.36% above active and 3.88% below extension. Causal SQLite size
is 57,528,320 bytes versus 57,647,104 / 57,651,200. Gzip plus first-trial raw
sidecars is 12,152,030 bytes versus 12,164,674 / 12,640,746. The tiny 0.10% saving
against active does not establish an asymptotic memory improvement; historical
trial archives and the final union are retained separately. Compare their costs
without treating saved descriptions as free certificates.

Complete time includes restoration, preparation and discovery, lookup, checking,
materialization, queries, persistence, full cold proof/query and used-index lineage
audit, compression and final digest/report generation. Imports, initial command-line
JSON reads and the final wrapper rewrite are excluded. Selection and all earlier
acquisition remain separately charged. Fresh solving is disabled during discovery,
materialization and independent replay.

## Next bottleneck and scope

Use the acquired causal frontier on the next matched stream rather than rebuilding
all 389 old source supports. Test active loading before another discovery pass;
then develop incremental causal extraction with explicit source and materializer
bindings. A claim that acquisition has amortized must be measured on additional
novel queries: simply repeating these queries already benefits from exact caching.
Derivation sharing is a second cost target, because 31 materializations add 275
rows even though smaller supports avoid 95 expansions.

For broader coverage, inspect the remaining 100 expansions: 95 negative and five
on SAT case 42. Negative case 187 costs 20, case 159 costs 17, and cases 50/60
cost 16 each. Templates 12/6/8 account for 42/38/20 expansions. These are current
catalog IDs. Compare unresolved proof dependencies and boundary assignments,
then test different guards; do not infer that origin guard equality is a
necessary condition merely because it holds for this observed stream.

The previous banks and every inherited checkpoint field remain available. The
new checkpoint records `causal_support_study`, `causal_support_decisions`,
`causal_support_proposals` and `extended_support_proposals`. Both new frontiers
use the eight source catalogs in protocol order; the older 170-entry frontier
retains its six-catalog lineage. Load causal proposals with `CausalCoreBank` and
the causal materializer, keeping pending roots unproved until checked. The
positive witness bank remains preserved and optional. No original structural
closure or new Lean theorem is claimed.

## Validation and retained authority

Independent validation passes **486 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,805 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. The union retains
**18,672 keys / 57,823,232 SQLite / 4,419,183 gzip bytes**, adding 725 keys while
keeping every earlier payload. All **41 alternate certificate occurrences** remain
in trial archives. New decisions comprise **140 direct roots / 52 guards**,
including one positive guarded result.

Resume `experiments/results/cnf-causal-support/checkpoint.json`. Preserve
`causal_support_study`, `causal_support_decisions`, `causal_support_proposals`
and `extended_support_proposals`, along with every inherited field. The causal
frontier has **34 ready roots / 142 pending**; the extended frontier has
**118 / 89**, and the original 170-entry frontier has **119 / 51** in the union.
All three lineage audits pass. Causal pending entries require the causal
materializer; the old materializer is not interchangeable. Both new banks use
eight source catalogs in protocol order; the original bank still uses six.

All prior **375 sources / 4,174 artifacts / 73 manifests** remain unchanged.
Runtime binds 380 sources; the analyzer brings the ledger to 381. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds to **199 pages** without
warnings, preserving all **64 proof blocks**. No new Lean result is claimed.

The new manifest binds **56 artifacts**, including the read-only historical
probe. The next preservation audit inherits **4230 artifacts / 74 manifests**.
