# Moving pivot deviations toward unresolved leaves

The previous two schedules inspected only the first four open elimination
ancestors. They mostly returned to the same selected unresolved cores and gained
no coverage. This study isolates ancestor choice before increasing projection
growth or trying coupled deviations.

## Frozen comparison

Both modes restore the exact union of the two previous pivot histories, including
all failed trials. They keep the recognizer, opposing-pair cap 64, candidate cap
64, clause-growth cap 2, and interaction-first candidate ordering unchanged.
The **early** control uses the first four elimination ancestors in breadth-first
selected-plan order. The **frontier** mode visits the whole selected open graph,
computes each node's longest path to a selected open terminal, and takes the four
elimination nodes with smallest height. Breadth-first discovery order breaks
ties. All children of a component conjunction and both children of the selected
conditioning alternative participate; closed children do not extend open height.
Unselected conditioning alternatives remain available to final recomposition.

Each open original can acquire at most **eight new trial records**. The two modes
start from independent clones of the same merged seed. A prior trial is reused
only for its exact source key and pivot, with the source key already binding the
recognizer configuration and remaining depth. The saved projection, target map
and summary are checked before skipping it. A failed cached trial does not rule
out different continuations of its target. Candidate construction and ranking
still run, so this cache does not avoid all preparation. New records are shared
across later inputs within each mode.

This differs from the previous cap of eight attempts, which could repeat old
trials. Both current modes have the same new-trial allowance. Earlier timings
are therefore historical context, not a matched control for this experiment.
The data remain selected development inputs, not an untouched holdout.

## Exactness and resource obligations

Every new edge uses the existing complete opposing-pair reconstruction and trial
checker. Successful local replacements count only after whole-source
recomposition; all old closed results survive. The definition of structural
coverage and the ordinary SAT solver are unchanged. The previously checked
existential-projection identity supplies the reduction semantics; no new formal
refinement or efficient search theorem is claimed.

Frontier selection adds O(V+E+M log M) graph/container work and O(V+E) graph
scratch for V selected open nodes, E selected edges and M elimination ancestors.
Source loading/checking and identifier lengths are additional. The graph may
include many nodes even though at most four are selected. Candidate construction
has the earlier per-ancestor costs. Eight new entry targets still do not bound
their inherited recognizer descendants, full-process memory or total discovery
time. A budget on distinct acquired descendant states remains a separate gap.

All seed rows, including prior trials, must be unchanged. Each output is a delta
relative to the merged seed, containing only new rows in all four tables. Both
original deltas and the original base remain necessary for reconstruction.
Exports are rebuilt and compared by logical table digests, applied twice to
check idempotence, fully cold-audited, and separately replayed for trial binding
and whole-source coverage. Cold checks deliberately repeat some dependencies;
their costs are recorded separately. Independent endpoint solving/model lifting
is performed for any new closed replacement, and its proofs are preserved.

## Results

The schedules above were frozen in `691e52a`. On the 83 selected original inputs,
both begin with **31 structurally closed inputs** and the same **752,304,128-byte
merged seed** (including 345 prior trials). Neither acquires a closed replacement
or improves original coverage.

| Original-input measurement | Early ancestors | Near-frontier ancestors |
| --- | ---: | ---: |
| New trials | 145 | 102 |
| Reused trial visits | 344 | 149 |
| New recognition nodes | 266 | 90 |
| Resident expansion seconds | 3.76670 | 1.75051 |
| Seed verification seconds | 67.85165 | 64.16580 |
| Full cold audit seconds | 110.13683 | 107.31572 |
| Separate trial replay seconds | 62.42473 | 61.62448 |
| Final working database bytes | 759,062,528 | 755,269,632 |
| Delta SQLite bytes | 6,807,552 | 3,018,752 |
| Compressed delta bytes | 382,806 | 165,286 |
| Same selected frontier as the trial source | 125/145 | 82/102 |
| Distinct novel selected leaves | 11 | 9 |

The frontier schedule visits 781 selected graph nodes rather than 606, but its
selected ancestors admit fewer candidates: **252/6,640 constructed projections**,
versus 535/7,136. The remaining 6,388 and 6,601 violate the unchanged growth cap;
pair-limit rejections occur before construction and are counted separately.
Only 11 new frontier trials use interacting pivots; 91 use independent pivots.
Its 183 selected ancestors across open inputs have total height 495. These are
occurrence counts across inputs, not distinct global node counts.

Both schedules produce twenty trials with novel selected leaves. In each, five
reduce selected unresolved literal count and fifteen increase it; none closes.
The frontier schedule therefore spends less on this bounded exploration, but
also conducts fewer new trials. The timings are single ordered runs, not a
same-work solver speedup or a proof of minimum expansion cost. Seed verification,
cold checking, candidate construction, export and replay remain charged.

This comparison weakens the hypothesis that moving a single deviation nearer
the existing leaf is sufficient at the current pair/growth caps. It leaves
coupled deviations, other ancestors, larger admissible intermediate states and
unselected branches unresolved. Repeating broad one-pivot sweeps has diminishing
coverage value on these development inputs. A next test should focus on the
retained divergent states with a limit on distinct newly acquired descendants,
and make any relaxation of intermediate growth an explicit separate hypothesis.

The repeated-input control reverses mode order (frontier, then early) on the
same 96 reused inputs. Both retain **88/96** closures. Its merged seed occupies
468,307,968 bytes and contains 45 prior trials. Frontier adds **10 trials / 12
nodes** in **0.18479 seconds**, with a 356,352-byte SQLite delta / 17,419 bytes
compressed. Early adds **12 trials / 19 nodes** in **0.26631 seconds**, with
495,616 / 25,361 delta bytes. Seed verification costs 5.67924 / 6.49374 seconds;
full cold audit 51.28781 / 51.32559; separate trial replay 5.82656 / 5.89315.
Only 3/10 frontier trials reconverge, versus 7/12 early trials, but all changed
frontiers increase selected unresolved literal count. Different residuals alone
are therefore not enough. This repeated control is not a reversed repeat of the
original-input timing comparison, and no general speedup ratio is claimed.

## Validation and the next persistent seed

All **531 Python tests** pass. Full cold graph verification, separate exact trial
replay, independent delta reconstruction, idempotent application, payload
preservation and report/fingerprint checks pass for all four runs. No new closed
replacement exists, so the endpoint reference archives are empty initialized
stores. Formal sources and the manuscript remain unchanged from `16fdf79`;
this study establishes no new theorem or structural coverage.

The two new original-suite deltas share **57 identical pattern rows and 29 trial
rows**. Their union adds **299 unique nodes / 218 trials** over the merged seed,
leaving **41,299 total pattern nodes / 563 trials**. The ordinary solver's 21,838
proof rows and 1,548 source bindings are unchanged. The repeated-control union
adds **25 nodes / 20 trials**, leaving 24,982 pattern nodes / 65 trials, with all
23,116 ordinary solver rows and 1,561 source bindings preserved. Sharing is exact
immutable-row reuse, not a claim of semantic compression or measured peak RAM.

To continue, use `experiments/results/cnf-frontier-pivots-originals/report.json`:
restore the original base and both input-report deltas, then apply both new
`results[*].delta` archives. Check compressed/unpacked hashes before application
and the final logical digests in
`experiments/results/cnf-frontier-pivots-validation/validation.json`. The same
recipe applies separately to the repeated-input suite. Thus future work can reuse
all earlier failed and successful acquisitions. Each constituent history passed
complete cold replay; union validation checks exact payload compatibility and
SQLite integrity, without claiming an additional full merged cold audit.

The subsequent [coupled-pivot study](coupled-pivots.md) resumes this complete union
and adds state-capped two-step trials. Use its updated five-table resume recipe
to retain those additional proofs, failures and the newly exposed unresolved core.
