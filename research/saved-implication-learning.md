# Combining retained implications with the full CNF

The preceding [saved-pair study](saved-trace-reuse.md) left 45 of 83 development
originals covered. It retained 284 candidate binary clauses from 41 exposed
clear sources; 161 candidates came from later probe windows. This study asks
whether composing those implications changes the remaining structural problem.
It uses the same 41 sources, preserving the parent's extra equivalence route.
It does not claim to enumerate every newly exposed alternative frontier.

## What the graph can establish

A checked unit derivation of literal l under assumption x establishes
F entails (not x or l). This gives both graph edges x -> l and not l -> not x.
Original binary clauses supply their two edges as well. All top-level saved
attempts are rechecked against F before graph construction; nested learning
continuations belong to augmented formulas and cannot silently supply reasons
on F. Graph construction uses every saved conditional unit, without the later
16-clause selection cap.

For each signed source variable, a retained discovery tree supplies a path to
every reported reachable vertex. The checker requires each parent to precede
its child and each edge to occur in the reconstructed graph. It then checks
that the vertex set is closed under every outgoing edge. Paths establish that
the set contains only reachable vertices; edge closure establishes that it
omits none. This gives an exact reachability certificate without rerunning the
search algorithm. A path x -> not x establishes not x; mutual paths establish
a signed equivalence; mutual paths between opposite literals refute F.

These are conclusions of an entailed binary subtheory. Even a complete negative
reachability result does not decide a source containing nonbinary clauses.
The checker does not discard those remaining interactions or treat absence of
a graph refutation as SAT.

## Why the full CNF still matters

Conditional consequences can strengthen propagation when stored as clauses.
For example, x -> a, x -> b and (not a or not b or c) let propagation under x
derive c. The learned clause (not x or c) also exposes its contrapositive:
propagation under not c can now derive not x immediately. That propagation step
need not be available through the original ternary clause alone.

The implementation selects at most 16 clauses using the existing deterministic
binary-path redundancy filter, then performs one four-variable lookahead pass
on the augmented **complete CNF**. Every selected clause has a source-trace
reference and unit index. Required references are interned once per record, so
several clauses from one trace do not duplicate its full identity. The checker
replays the source reasons before it checks any augmented-source reason. There
is no circular use of the clauses being justified.

The augmented formula is logically equivalent to the source: each added clause
is entailed, and every original clause remains. A subsequent forced-value,
common-consequence or equivalence rewrite must strictly reduce variable support
and bind the exact canonical target and variable transport. Model lifting is
checked against the full original source. Clear follow-up probes are retained
as unsuccessful trials with no child edge; missing targets remain pending and
cannot count as covered. Target acquisition uses the existing 32-state cap.

## Controls and resource obligations

Adding binary clauses changes both propagation and the frequency ranking used
to select probe variables. The matched control therefore probes the original
source using **the same variable order selected on the augmented formula**.
Its complete checked traces distinguish a propagation gain from a ranking-only
gain. Control computations are additional work and are retained and charged.
The old trace-pair equivalence also remains a separate baseline route, preventing
it from being counted again as a new improvement.

For K checked source attempts and a source with L literal occurrences, direct
trace validation includes O(K L) restriction/reconstruction work plus local
reason checks. Let V and E denote the signed graph's vertices and edges. This
diagnostic performs a traversal from each vertex, costing O(V(V+E)); its path
trees may retain O(V squared) entries. The checker pays their path and closure
costs explicitly. This is a diagnostic implementation, not a linear-time SCC
algorithm or a universal SAT bound.

Clause selection uses the existing ordered reachability filter, and still pays
recognition and redundancy checks. The bounded follow-up pass has at most eight
new assumption attempts, plus any forced/common closure. New target recognition
can perform further probing and elimination. The 32-state cap bounds admission
count, not state size, elapsed time, reference-proof work or total history RAM.
Cold archive and route validation remain separate from these local costs.

The logical rules are standard implications and exact reductions. Neither their
composition nor a fixed number of learned binary clauses supplies polynomial
coverage of arbitrary SAT. The implementation is checked in Python; this study
does not extend the Lean formalization or make a new complexity-class claim.

## Persistent checkpoint

`experiments/cnf_trace_learning.py` contains graph certificates, checked learned
clauses, bounded follow-up probes and exact coverage routes. The experiment
retains all successful and unsuccessful learning records before target
recognition, then exports an additive eight-table delta and independent reference
proofs. The standalone validator rechecks graph closure, clause selection,
source bindings, matched controls and finite coverage without new discovery.

Resume with `restore_checkpoint` in `experiments/compare_cnf_trace_learning.py`.
It returns the report, the old trace-rewrite records and the new learning records;
pass both record lists to `LearnedTraceRoutes`. Restoring only the older generic
probe history would omit these additional alternatives. The parent's rows and
external artifacts remain immutable.

## Measured result, 13 November 2026

The full binary graph over all 41 sources contains 3,026 signed-vertex instances
and 2,620 edges in total. It incorporates 1,781 conditional unit occurrences.
Complete path and closure checks find no forced values, no contradictory
components and only the old x27=x5 equivalence on case 58. The 2,786 retained tree
edges and 3,902 edge-closure checks are recorded; this negative result concerns
the saved binary theories, not the satisfiability of the complete CNFs.

The 39 nonempty batches contain 284 clauses justified by **126 interned source
references**. Their augmented follow-up probes return 36 clear outcomes, two
equivalences and one forced value. The same-order controls on the original
sources return 38 clear outcomes and the old equivalence. Specifically:

| Case | Augmented outcome | Same-order control | Source / target / final selected leaf variables |
| --- | --- | --- | --- |
| 32, `reuse_holdout3`, original 1191 | x25 = not x1 | clear | 34 / 33 / 27 |
| 31, `reuse_holdout3`, original 1190 | x15 = true | clear | 40 / 39 / 39 |
| 58, `fresh3`, original 1340 | x27 = x5 | same equivalence | 37 / 36 / 35 |

Thus the clauses strengthen propagation on two sources independently of ranking.
The third uses an already known equivalence, but carries the checked clauses
into its distinct target. None closes a new original. Coverage remains **45/83**,
including the growth-exception ablation. The reference solver proves the case
32 and 31 residuals SAT and the case 58 residual UNSAT. These statements concern
the exposed residuals; no new original answer or structural-coverage gain is
inferred from those separate fallback proofs.

The first target uses nine admissions, the second two and the third four:
**15 new pattern nodes** in total, with no pending target and no cap reached.
Each ends at one unresolved width-two leaf. The 27-variable leaf has 17 remaining
binary-ranked variables after its saved source attempts; the 39-variable leaf
has 21 and the 35-variable leaf has 23. The read-only `remaining-targets.json`
binds their exact keys and makes the 27-variable leaf the preferred next trial.
Its inspection takes 0.05486 s after 6.23251 s of reconstruction, 6.87035 s in
all, with unchanged history bytes and no new assumptions.

| Phase | Seconds |
| --- | ---: |
| Restore parent history | 5.49427 |
| Source checks, full graph discovery and checking | 0.74307 |
| Clause selection, evidence checks and augmented probes | 0.23493 |
| Same-order controls, including evidence/choice preparation | 0.14577 |
| Prepare full baseline routes | 64.74929 |
| Three target acquisitions and checks | 0.14217 |
| Full cold inventory | 106.91850 |
| Cold routes and coverage | 63.50435 |
| Independent reference solving / replay | 0.16640 / 0.04968 |
| Acquisition/validation pipeline before final report write | 255.75100 |
| Subsequent standalone validator | 70.96163 |

The pipeline also includes cloning, serialization, additive export, reconstruction
and recomposition; it excludes the standalone validator, tests and untimed pilot.
There are **311 new augmented lookahead attempts**, **312 control attempts** and
**138 target-recognition attempts**, in addition to reference-solver work.
The binary implications themselves reuse already stored source assumptions.
There is no end-to-end solver speedup or measured peak-RAM reduction.

The working database grows **249,856 bytes**. The additive delta occupies 311,296
SQLite bytes / 15,053 compressed bytes. The learning records occupy 570,738 JSON
bytes / 36,867 compressed bytes; graph/control diagnostics occupy 103,065 JSON
bytes / 16,664 compressed bytes. The independent reference archive contains 143
nodes in 1,019,904 SQLite bytes / 62,984 compressed bytes. These are separate
persistent artifacts, not measurements of simultaneous RAM. All old rows and
external proofs remain unchanged.

All **566 tests** pass. The standalone validator independently reconstructs the
checkpoint, checks every graph closure, regenerates the deterministic clause
selection, verifies source-bound clauses and same-order controls, replays the
finite coverage plan and independent reference proofs, and confirms no new
cold discovery or database-byte changes. The pilot retains the graph miss and
same-order observations. It also retains a corrected test-fixture indexing error:
the first clear probe had no unit to corrupt, so the test now selects an actual
unit-bearing trace. Manuscript and Lean sources are unchanged.

## Next experiment

Use the already acquired 27-variable leaf from case 32, its exact source key and
its saved initial attempts. A bounded subsequent probe window is the most direct
way to test whether the smaller residual exposes a further reusable reduction.
Keep the two external route layers in original-level recomposition. Alternatively,
resume later variables on one of the 36 clear augmented formulas, preserving
that formula's learned-clause dependencies and the distinction from source
traces. Compare a fixed added window with bounded conditioning rather than
repeating the same graph search or increasing every budget at once.
