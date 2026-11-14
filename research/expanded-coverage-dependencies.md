# Expanded positive coverage and complete dependency accounting

This study continues the selected-route replay work. It makes the internal plans
hidden behind the existing positive proof explicit and corrects the count of
checked inventory nodes. It preserves the same 58 covered roots among 83 reused
development inputs, the same discovery frontier and every old archive.

The subsequent [hybrid primitive checker](positive-primitive-replay.md) validates
the selected semantic steps directly and retains full historical checking only
where still needed. The measurements below describe this earlier exporter and
its original replay; their frozen artifacts remain unchanged.

## The missing verifier cache

`RetainedPlanInventory` checks saved plans under a second configuration, using
`h.prepared`. The two verifier objects share SQLite but have separate checked-node
maps. The previous dependency helper inspected only `h.checked`. Its elapsed
timings included both views; its node and payload totals did not.

| Selected replay cache | Nodes | Node JSON bytes | Key bytes |
|---|---:|---:|---:|
| Current policy | 10,258 | 88,614,890 | 27,263,272 |
| Retained policy | 1,697 | 8,610,646 | 3,207,374 |
| Complete, disjoint union | **11,955** | **97,225,536** | **30,470,646** |

The comparison that loads all external routes checks **13,211 nodes /
109,165,321 node JSON bytes**, including the same 1,697 prepared-policy nodes.
The recorded mean times, **35.72304 versus 30.35446 seconds**, and their 15.03%
reduction are unchanged. The saved historical reports remain byte-identical;
`previous_accounting_correction` in the new report records the corrected totals
for every earlier sample. Documentation and the manuscript now include both views.
These are serialized logical payloads, not Python heap or peak-RAM measurements.

The new accounting helper walks the retained verifier views, unions exact keys,
reports duplicated cache entries and rejects conflicting payloads or cyclic view
references. Here the policy-bound key sets are disjoint. Separate configurations
must not silently share an unchecked closure assertion merely because their
normalized formulas match.

## Expand each implicit base

The original witness has **593 steps**, including 117 `base` steps. A base means
that the original inventory checker established closure; it can represent a
whole derivation rather than a primitive recognized family. The exporter now
replaces such implicit uses with their selected internal plans. It follows exact
retained-policy references, expands component conjunctions and both children of
conditioning, and retains external routes with their original identities.

The result has **2,748 unique ordered steps**, exposing **2,155 previously hidden
steps**. It has 2,275 current-policy nodes and 473 prepared-policy nodes. Repeated
subproofs remain shared: the exporter records 120 references to already expanded
nodes. Both edge occurrences remain explicit when canonical children coincide.

| Expanded rule | Steps |
|---|---:|
| Checked single-child transformations | 2,269 |
| Conditioning, both children | 166 |
| Primitive recognized-family leaves | 126 |
| Exact retained-plan references | 115 |
| Component conjunctions | 16 |
| Selected external rules | 56 |

The external rules include the independent affine/one-clause certificate, seven
saved splits and the selected ordinary, learned, elimination and growth routes.
The graph contains no implicit `base` rule. Its replay rejects missing or reordered
premises, omitted branch occurrences, false family leaves, foreign configurations,
missing retained references and changed exact bindings. Current and retained
source identities remain distinct and are checked by the appropriate original
verifier. A successful finite graph establishes the same positive structural
coverage claim, not a SAT truth value or complete coverage of all inputs.

## What still lies outside the graph

All **11,955 nodes** are still checked by the existing validators during both
selected and expanded replay. The original outer witness hides 11,362 of them;
the expanded positive graph leaves **9,207 outside its explicit structural
steps**, accounting for **78,657,022 node JSON bytes**. The expanded graph's own
node payloads total **18,568,514 bytes**, but they still contain historical
profiles and alternatives. These figures are not the size or memory bound of
a standalone proof checker.

The 9,207 outside nodes include 3,590 elimination nodes, 2,828 probe nodes and
1,366 binary-path nodes, plus other families, alternatives and unresolved states.
They include dependencies of selected external evidence as well as historical
policy checks. Absence from the positive structural graph therefore does not
prove a node dispensable. The next step is a separate primitive transformation
checker that makes its exact premises explicit and proves why each omitted
historical check is unnecessary for the positive claim. Retained references,
source-bound learned reasons and both conditioning branches must survive.

## Costs and limits

After checked history is available, graph expansion takes **0.26315 seconds**,
including rechecking the old ordered proof. The expanded graph occupies
**11,960,299 JSON bytes / 777,176 compressed bytes**. It references the retained
history and sidecars; it is not a self-contained portable certificate. Dependency
diagnostics add **898,927 compressed bytes**. No solver row changes, and SQLite
remains **770,338,816 bytes / 41,758 pattern nodes**.

Fresh selected replay takes **30.51477 seconds**; fresh expanded replay takes
**34.50104 seconds** in this single ordered run. Both check identical sets of
inventory keys across both policies, with fresh discovery disabled. The expanded
representation has no demonstrated runtime saving: it exposes the obligations
needed for the next checker. The complete study takes **97.55245 seconds**,
including **22.19944 seconds** of restoration, accounting, export and replay.
This is not a full archive audit or a complete expansion/solving benchmark.

The 57-test suite passes, including new tests for hidden retained-policy steps,
branch multiplicity, dependency order, cache accounting and tampered evidence.
Cold replay independently reads the serialized expanded graph without the old
outer certificate or any previously checked node/route objects. Parent artifacts,
all history bytes and the 58-root claim are preserved. No new Lean refinement,
tractable SAT family or unrestricted polynomial bound is established.

## Resume

Run `python3 experiments/analyze_cnf_expanded_coverage.py OUTPUT_DIRECTORY` to
reproduce the study. The report, expanded graph, exact dependency-key hashes,
tests, manuscript check and artifact hashes are under
`experiments/results/cnf-expanded-coverage/`.

For discovery, still resume `experiments/results/cnf-reused-branch/report.json`
through `continue_cnf_reused_branch.restore_checkpoint`. Preserve all five lists
**(1 rewrite, 42 learned bases, 156 augmented blocks, 11 splits, 1 affine family)**
and earlier sidecars. The 23-variable / 93-clause leaf and its saved pairs
**5, 6, 11, 13** remain unchanged; the next ordinary block is **7, 9, 16, 17**.
This is a verification study, not a new discovery checkpoint.
