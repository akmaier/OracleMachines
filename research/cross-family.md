# Unfamiliar CNFs expose failed discovery work

The previous neighbour-only evaluation was saturated: 190 of 192 targets were
known after preparation. This study adds 48 unlabelled CNFs from four different
finite generators and retains 12 excluded same-template neighbours as controls.
The solver receives no family labels, construction witnesses or expected answers.
The generator varies requested sizes 12/16/20; actual fresh formulas have at most
21 variables. Graphs have 4/6/7 vertices. Gated Horn/dual-Horn instances are
constructed SAT controls, not evidence of hard random SAT. All 48 fresh formulas
are exhaustively checked by an independent bitset truth-table evaluator after
timing. That evaluator uses exponential work and is not part of the solver.

Every raw root is excluded from inherited native and decision roots. Unlike the
last study, **all 48 new-family targets remain unfamiliar after preparation**;
all 12 neighbour targets become known. Each chronological prefix is reconstructed
independently to verify that distinction. Four fresh processes run baseline/current
and the reverse order, preserving identical preparation and inherited state.
Generation and novelty selection take 1.636 seconds separately. No tests, builds
or profiles overlap timed production.

## Measured transfer

Both modes answer **44 SAT / 16 UNSAT**, add **398 native rows / 483,695 native
bytes**, and retain exactly identical native payloads. Twelve rows come from
ordinary preparation of the neighbour controls; the other 386 come from native
acquisition of unfamiliar targets. No near-guard rows are added. Warm replay
adds no rows. The current optional discovery policy makes **384 premise probes**,
returns `no-proposal` on all 48 targets, and makes no positive-model publications.

| Group (12 queries each) | SAT | Native rows | Native bytes | Native propagation | Added discovery propagation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random 3-CNF | 8 | 131 | 176,910 | 27,073 | 41,553 |
| Coupled parity | 8 | 130 | 142,432 | 20,190 | 36,504 |
| Gated Horn/dual-Horn | 12 | 35 | 41,521 | 6,836 | 76,289 |
| Graph colouring | 8 | 90 | 96,070 | 11,743 | 26,538 |
| Neighbour controls | 8 | 12 | 26,762 | 0 | 0 |

Propagation during discovery and acquisition rises **65,842 -> 246,726** visits
(3.75 times baseline). Mean query time rises **0.354 -> 0.482 seconds**; the two
paired increases are 0.149/0.108 seconds. Mean complete worker time rises
**21.512 -> 21.963 seconds**, with paired increases 0.351/0.551 seconds. This is a
regression on this small corpus, not a universal timing claim. Both policies use
shared ordinary/near preparation: baseline here is not an external standalone
SAT solver. Query time includes preparation, eligibility, discovery, checking,
composition and acquisition. The propagation column counts discovery/acquisition
only; the full phase counters remain in the query records.

Cold replay remains the largest measured component, **10.611/10.700 seconds**.
Setup is 4.368/4.388 seconds, compression 3.868/3.976, and warm-bank setup
1.944/1.992. Mean process RSS is approximately 706/709 MB; it includes inherited
state and is not a live-memory bound. Query/warm sidecars grow from roughly
**1.162 to 2.311 MB**, principally retaining the unsuccessful discovery traces.
Both trial databases occupy **74,706,944 bytes**, compressed to **5,364,383 bytes**.
The measured policy adds no native-state saving on these inputs.

## Next concrete target: exclude impossible unit probes

The posthoc audit identifies **192 of the 384 probes** that cannot yield the
unit refutation sought by this selector. They account for **73,488 propagation
visits**, about 40.6% of discovery propagation. They are the probes on the random
3-CNF and coupled-parity groups. The source-bound screens are replayed and match
all recorded results. This is a diagnosis; skipping them has not yet been timed
or enabled in the acquisition policy.

The necessary condition concerns the **residual after complete, consistent unit
propagation**. It contains no unit or empty clauses. If an unassigned candidate variable
occurs in no binary clause of that residual, assigning it removes satisfied
clauses and shortens other clauses to length at least two. Thus the assignment
creates neither another unit nor an empty clause, and unit propagation cannot
refute that single assumption. Building the residual binary-incidence set costs
one literal scan after the already charged propagation. This condition can
exclude futile premise probes while preserving every successful single-literal
unit refutation. It says nothing about satisfiability or deeper conditioning.

The implementation must check the propagated residual, not the original source:
`(a) AND (NOT a OR b OR c) AND (NOT a OR b OR NOT c)` has no original binary
clauses, but propagation of `a` exposes two, and assuming `NOT b` refutes it.
Retain that counterexample, prior useful guards 43/172, regression 144, model
recovery 146 and unresolved 0/131/159 when testing a future filter. Reuse the
baseline trace and avoid paying a second complete discovery pass to apply it.

Random 3-CNF and coupled parity account for **261/386 acquisition rows** and
**47,263/65,842 acquisition propagation visits**. These are the largest fresh
acquisition groups; cases 32/56/52 (random) and 21 (coupled parity) are saved
high-cost targets. Gated cases have the greatest failed-probe overhead despite
cheap native solving. Price mixed-family conditioning and affine/leftover reuse
on these prefixes after the cheap necessary-condition filter. Cold replay and
shared state dominate complete runtime, so even eliminating these probes alone
cannot produce a large end-to-end improvement.

## Persistence and scope

The experiment extends evaluation coverage; it introduces no new solving rule,
structural authority, Lean theorem, minimum-cost expansion guarantee or
unrestricted-SAT bound. The four generators are not a partition of all CNFs,
and three size settings with four samples each cannot establish scaling laws.
The growing evidence union is not a single policy's working storage. All prior
proofs, solver results and experiments remain bound to their saved artifacts.

Reproduction and the independently checked checkpoint are in
[the experiment record](../experiments/results/cnf-cross-family/README.md).

All **1,106 tests**, 12 focused tests and independent reconstruction pass. The
new checkpoint is `experiments/results/cnf-cross-family/checkpoint.json`:
**23,127 native keys**, all 22,729 old payloads, **120 new composed records**,
3,045 previous composed records, 2,957 ordinary decisions and six projections.
There are no alternate native payloads. The union occupies 74,706,944 database
bytes / 5,364,377 compressed bytes. Ready/pending banks remain 132/38, 141/66,
86/90 and 86/117. All earlier 498 sources, 5,617 artifacts and 93 manifests
are unchanged. Structural authorities and all 64 manuscript proof blocks remain
unchanged. The 209-page manuscript builds without overfull or undefined warnings.
