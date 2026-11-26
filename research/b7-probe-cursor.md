# B7 discovery and the cost of adding another proof layer

Checkpoint: 26 November 2026. Composing all 25 retained B6 failed assumptions
forces **26 additional assignments in seven cases**, including one beyond the
explicit exclusions. Bounded probing after composition finds **15 failed
assumptions in five cases**. No additional case is refuted: sampled structural
recognition remains **228/246**, with **18 open**.

Exact reuse avoids **1,788 repeated probes** across eleven unchanged clause
sets. It saves only **1.05% of complete measured time** against fresh search
reaching the same frontier. With two repetitions, this small difference does
not establish a robust end-to-end speedup. Adding the layer costs **26.98% more**
than continuing the existing B6 search, which explores a different frontier.
The main opportunities are avoiding empty layers and repeated preparation,
while retaining the new information from changed clause sets.

## Recognition, composition and invalidation

`cnf_b6_cursor_feedback.py` validates the complete existing B6 result, including
its original source, guards, prior banks, closure, binding, schedule and every
failure trace. For each checked contradiction under assumption `l`, it appends
`(-l,)` with an origin identifying that B6 proof. Each new reason points strictly
to the preceding bank. Completed open assumptions add no clause.

If B6 entails every appended exclusion, B7 has exactly the same satisfying
assignments as B6. Computing a checked unit fixed point of B7 therefore preserves
satisfiability. A contradictory fixed point is a refutation; a consistent fixed
point is not a SAT certificate. The eighteen exposed cases have consistent
fixed points. The composition module can check a contradiction on other inputs,
but this checkpoint does not add a B7 native compiler or publish new authority
records.

`cnf_b7_probe_cursor.py` probes the residual B7 clauses after that closure. It
lifts each trace back to the B7 clause IDs and checks each retained failure
independently. Its cursor binds the full source and B7 clauses, the exact closure
including its trace, the candidate order and trace allowance. Cold reload checks
all original provenance and the deterministic completed schedule.

A B6 cursor may migrate only when B6 and B7 clauses, closure traces and trace
allowances match exactly. These conditions preserve the residual clauses,
reason IDs, candidate order, available trace budget and complement-first
schedule. Eleven cases qualify, with 1,788 previously completed assumptions.
Seven changed cases start fresh. Altered source, closure, proof, policy binding
or trace allowance invalidates the corresponding saved cursor. Open history
remains scheduling data: a forged but valid-looking completed prefix cannot
establish SAT or a proof of exhaustive search. Every used failure is checked.

## Matched measurements

The frozen pilot is followed by two opposite-order repetitions on all eighteen
cases, in isolated processes for each target and arm:

* **B6 continuation:** continue the existing saved B6 cursor for up to 64 probes.
* **B7 restart:** compose B6 failures, then start B7 search with 64 probes.
* **B7 matched fresh:** the same B7 search, extending its probe/work allowances
  by the old prefix only on exact matches, to reach the reused frontier.
* **B7 reuse:** import exact matches; otherwise start fresh, with 64 new probes.

Matched fresh and reuse perform eligibility recognition once each and emit
identical full results. An initial screening harness redundantly prepared the
matched arm to select its allowance; its source and results are preserved but
excluded from the timed comparison. Final matching happens inside discovery,
after the same preparation already needed by every B7 arm.

The census charges source-prefix reconstruction, complete scan-based composition,
search and its recognition/checking, serialization/reload, and independent
semantic checking of the returned result. Composition is additional to the
bounded occurrence-probe budget. Startup/input loading, historical acquisition
and the final lineage audit are additional costs.

| Summed per-target means | B6 continuation | B7 restart | B7 matched fresh | B7 reuse |
| --- | ---: | ---: | ---: | ---: |
| Source reconstruction (s) | 0.36546 | 0.36616 | 0.36596 | 0.36659 |
| Composition (s) | 0.00000 | 0.14575 | 0.14528 | 0.14566 |
| Discovery (s) | 0.13993 | 0.15958 | 0.16599 | 0.15558 |
| Independent verification (s) | 0.13429 | 0.14762 | 0.14715 | 0.14767 |
| Persistence/reload (s) | 0.00622 | 0.00618 | 0.00585 | 0.00607 |
| Complete census (s) | 0.65030 | 0.83025 | 0.83446 | 0.82573 |
| New probes | 192 | 1,152 | 2,334 | 546 |
| Probe initialization clauses | 96,208 | 417,536 | 877,394 | 217,940 |
| Propagation occurrence visits | 5,213 | 40,329 | 64,491 | 23,500 |
| Serialized closure/result bytes | 217,779 | 209,367 | 214,592 | 214,592 |
| Peak process RSS (bytes) | 97,353,728 | 97,468,416 | 97,452,032 | 97,419,264 |

Reuse avoids 659,454 clause initializations and 40,991 occurrence visits against
matched fresh search. Discovery time falls 6.27%, but source reconstruction,
composition and final checking alone account for **79.92%** of reuse's total.
Discovery regresses on four cases versus matched fresh; all per-case timing
regressions remain in the analysis. Against B6 continuation, both discovery and
verification regress on every case. The arms have different search coverage,
so B7 is an additional discovery route, not an established faster replacement.
Peak memory does not materially improve. Fresh short restart emits fewer bytes
because it retains a shorter frontier; matched fresh and reuse emit identical
bytes.

## Two retained frontiers and the next targets

B7 failures are `(28,18):1`, `(28,19):3`, `(37,40):8`, `(40,0):1`, and `(67,63):2`.
Ten B7 orders are exhausted; the remaining eight have later candidates.

The comparison also advances B6, adding three failures at `(37,40)` and two at
`(67,63)`, for **30 B6 failures in eight cases**. The two at `(67,63)` also occur
in B7. The three new B6 failures at `(37,40)` are absent from the current B7
history; they must not be discarded when combining the two routes. B6 now has
sixteen exhausted orders, leaving `(37,40)` and `(67,63)` with later candidates.
Neither route supplies a SAT verdict.

The next coverage step is to combine the retained B6 and B7 failures while
checking each on its original bank, then probe only the affected residuals.
Replacing the B6 inputs with their comparison continuation changes the B7
provenance binding: the existing B7 cursor cannot simply be relabelled. Proof
transport or revalidation and a new schedule decision must be explicit.

The next cost step is to avoid creating an empty layer on the eleven unchanged
cases, and to share checked preparation between composition and search. Source
reconstruction is the largest single stage at **44.40%** of total time. Exact
bindings and cold validation remain required. No uniform bound on future proof
layers, all-CNF recognition or total search follows from finite-prefix reuse.

## Storage and validation

The open export grows **25.67%**, from **1,689,359 to 2,122,938 bytes**, because
it preserves all earlier histories and adds the B7 closure, B7 cursor and B6
comparison continuation. This is no persistent compression or lifetime-space
improvement. Exact clause comparison and serialization cost scale with explicit
bank and binding size. Each new probe still initializes arrays for every
residual clause; reuse avoids whole probes, not the cost of each remaining one.

All **2,030 full tests** and **165 focused tests** pass. New tests cover exact
import, changed-bank reset, binding and forward-reason rejection, closure/trace
invalidation, interruption/retry, JSON continuation, joint failure composition,
all sixteen subsets of the four signed binary clauses on two variables, and
generated small truth tables. Both complete
result checkers are exercised by the audit; no new native archive is created.
All **1,124 prior source fingerprints**, **28,081 artifact entries in 199
parent manifests**, and **64 original manuscript proof blocks** are preserved.
The unrestricted-SAT and native B7 compilation gaps remain explicit.

Resume `experiments/results/cnf-b7-probe-cursor/checkpoint.json`. Each row in
`remaining.json` retains the original `b6_checked_restore_cursor` and appends
`b6_comparison_cursor`, `b6_cursor_feedback_closure`, and `b7_probe_cursor`.
Reproduce `pilot`, `prepare`, `run_census`, `validate`, and `seal` using the
corresponding compare/validate scripts and a fresh output directory.
