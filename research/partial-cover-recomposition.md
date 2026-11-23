# Reuse intact branches after a support deletion

The optional partial-cover route keeps surviving conditional unit supports and
acquires only failed leaves. On the same 23-source, six-guard stream, expansion
dispatches fall from 39 to 32. Preparation plus query is 3.99% lower than
unit-gated complete-cover reuse, but 2.45% higher than the native baseline.
All four paired repeats have that ordering. Keep the policy experimental.

## Exact construction

The existing bank first tries complete covers. After a miss, the new route
considers at most four ready covers with the same supplied outer guard. It
prefers fewer missing leaf supports, then more intact leaves, then the oldest
origin. Recognition uses clause containment and the existing checked cover
tree; no target verdict or future origin selects a plan.

Each root-to-leaf path implies that leaf's recorded assumptions. An intact
support publishes a native unit refutation of the full conditioned target. A
broken support supplies no answer: the ordinary bounded solver acquires that
conditioned target. Two negative children publish the existing native split
certificate. A positive child lifts its assignment through the path and must
satisfy the full target before a native model is stored. The native verifier
checks every publication.

The checked full-target unit prefix from the gate is retained. A split already
fixed by that prefix follows only its compatible child; the root is then
reconstructed with the existing unit rule or a full witness. A split variable
absent from the current residual needs only one identical cofactor. These
operations preserve semantics, rather than treating a matched fraction of
leaves as a verdict.

All missing leaves share one native dispatch budget. Exhaustion returns
unresolved and commits only already verified dependency prefixes, never an
incomplete parent. This budget excludes matching, support publication, split
assembly and verification. Those costs remain in the measured wall time.

The tree contains at most 64 checked node occurrences under the existing bank
limits. For a fixed candidate, reconstruction adds bounded tree traversal,
restriction, normalization and native checking around the sum of acquisitions
at reached missing leaves. Those acquisitions still have unrestricted SAT
worst cases. A finite plan or complete decomposition alone gives no uniform
polynomial acquisition or storage bound.

## Matched comparison

The historical prefix, donor acquisition, static hints and source order are
identical across three policies and four alternating serial orders: 1,656
queries in total. Each worker returns 125 UNSAT and 13 SAT cofactor answers.
This is an informed experiment on previously exposed edits and supplied guards,
not a held-out benchmark or additional whole-CNF coverage cell.

| Measure, mean per worker | Native baseline | Unit-gated covers | Partial covers |
| --- | ---: | ---: | ---: |
| Preparation + query, seconds | 0.428174 | 0.456871 | 0.438657 |
| Expansion dispatches | 55 | 39 | 32 |
| New native payload, bytes | 1,551,836 | 1,535,146 | 1,508,442 |
| Active hints, bytes | 11,505 | 76,533 | 42,031 |
| Compressed delta + hints, bytes | 156,321 | 218,158 | 180,373 |
| Selected retained Python state, bytes | 8,460,643 | 8,493,876 | 8,362,875 |
| Complete worker, seconds | 3.519164 | 3.558042 | 3.565918 |

Partial reuse cuts native payload by 2.80% and selected retained state by 1.16%
against baseline. Hints remain larger. Complete-worker mean is 1.33% higher
than baseline: the query improvement does not establish an end-to-end gain.
Selected state excludes other containers and transient/native allocations;
process peak RSS, cold replay, reconstruction and persistence are also recorded.
Hint reload is checked and timed separately from complete-worker answer replay.
One root canonicalization before the composer's counter reset is included in
wall time but omitted from its aggregated literal/key counters; use those
counters diagnostically, not as an exact total operation count. Expansion
dispatch accounting and the shared budget are unaffected.

| Query | Result | Intact leaves | Baseline ms | Unit-gated ms | Partial ms |
| --- | --- | ---: | ---: | ---: | ---: |
| 7 / guard 4 | SAT | 2 of 3 | 8.632 | 15.345 | 17.798 |
| 15 / guard 3 | UNSAT | 2 of 3 | 17.138 | 24.106 | 26.134 |
| 19 / guard 3 | UNSAT | 2 of 3 | 17.881 | 26.325 | 15.390 |
| 20 / guard 3 | UNSAT | 1 of 3 | 23.612 | 33.115 | 21.481 |

There are four partial attempts, five acquired leaves, six published intact
supports and two surviving complete-cover hits. The SAT control stays SAT.
The first two attempts include lazy extraction and still regress. The later
two reuse already extracted covers and beat baseline, showing where the work
can amortize on these particular edits.

This pilot registers only the preceding policy's expensive negative native
fallbacks. Recomposition outcomes are not new learned origins. Consequently,
the live partial stream uses the earlier three-leaf cover; the previous
posthoc four-leaf examples from origins 15 and 19 are not seeded. Smaller hints
partly reflect fewer registered origins, not merely smaller certificates.
Automatic guard selection, correspondence, origin policy and arbitrary-edit
closure remain open.

## Next bottleneck and preserved evidence

A separate diagnostic rebuild profiles only the four partial queries and
produces byte-identical proof deltas, routes and decisions. On case 15/guard 3,
38 canonicalization calls include 29 normalizations; normalization accounts
for about 26 of 72 profiled milliseconds. Cover extraction takes about 20 ms,
and recomposition about 45 ms. Cumulative times overlap and profiler overhead
prevents comparing these values directly with ordinary timings.

The next target is sharing immutable conditioned residuals, name maps and
support membership through cover traversal and leaf publication. The caller,
leaf materializer and native verifier repeatedly reconstruct related inputs.
Preserve independent certificate checks; first remove duplicate caller-side
preparation and carry its counters explicitly. Compare cold extraction and
later reuse separately, retaining the positive-control loss. Learning from
recomposed negative results is a secondary coverage/storage tradeoff.

`experiments/results/cnf-partial-cover/` retains raw policy deltas, chronological
origins, every conditional branch, persistence/cold checks and the profile.
Twelve new tests cover all 256 deletions of a three-variable contradiction,
alternative negative reasons, positive lifting, sparse names, unit pruning,
corrupt paths/prefixes, shared budgets and restart after an incomplete attempt.
The initial tests confused the falsifying branch of an all-negative clause;
the source and two failed assertions are preserved, with corrected fixtures.

Validation passes 1,571 full tests and 82 focused tests. Both readers audit all
1,656 comparisons, 76,501 cumulative native records, unchanged extension tables
and 342 preceding partition records. Twenty native identities are added without
replacing earlier authoritative payloads. All 12,914 preceding artifacts across
146 manifests remain unchanged. The new seal binds 833 source files. The full
suite reports 44 existing unclosed-SQLite warnings; the focused suite has none.
The manuscript builds to 248 pages without LaTeX/layout warnings and retains
all 64 preceding proof environments unchanged.
