# Local discovery needs a cost check on the remaining child

Target-local failed-literal discovery now has historical acquisition measurements
and a comparison on 192 new neighbouring CNFs. The fixed policy finds valid
guards cheaply, but one fresh regression cancels the other native-row savings.
The next gap is admission after discovery, especially preserving cached work
when a forced assignment changes the residual.

## Fixed policy and accounting

After shared ordinary reuse and the optional premise-first guard, the policy
checks each still-unknown target. It propagates once, reuses that baseline result
to exclude forced variables, ranks remaining variables by original binary-clause
incidence with source-identifier ties, and probes false then true for at most
four variables. It stops at the first unit-refuted premise. A terminal baseline
or selected premise trace is published through the unchanged native verifier.
The remaining child is solved normally; checked guard chains retain the answer
and lift SAT witnesses. Failed probes do not certify anything.

There is no extra core-bank scan at this discovery stage. Existing bank setup,
ordinary recognition, native normalization, ranking, checking, serialization and
persistence remain charged. For a variable budget b, discovery runs at most
1+2b unit-propagation calls. The scan-based implementation needs at most n+1
passes per call over at most L+1 literals, before separate normalization/sorting
costs. The bound concerns discovery, not the unrestricted child solve. Retained
probe roots and traces also cost space; fewer expansion calls alone measure
neither computation nor memory.

## Historical pricing

Six arms restore the original prefixes before cases 43, 172 and 70. Baseline
proofs and sidecars match the preceding experiment. Local choices match the
earlier read-only original-binary ranking. Sharing baseline propagation avoids
1,090 repeated literal visits across those three diagnostic choices.

| Case | Selected assumption | Native rows, baseline / local | Native bytes, baseline / local | Propagation visits, baseline / local |
| --- | --- | ---: | ---: | ---: |
| 43 | `[-20]` | 10 / 7 | 9,798 / 5,688 | 1,611 / 1,950 |
| 172 | `[-140]` | 9 / 7 | 13,839 / 9,208 | 1,952 / 1,841 |
| 70 | `[50]` | 4 / 5 | 5,978 / 6,590 | 938 / 1,972 |
| Total | | 23 / 19 | 29,615 / 21,486 | 4,501 / 5,763 |

The local policy improves case 172 over the previously priced supplied guard
(eight rows), and needs no conditioned-bank candidate list. Case 70 still
regresses. Serialized deltas plus chains increase 88,960 -> 95,457 bytes despite
the native-byte reduction. This remains historical pricing, not fresh evidence.

## New neighbouring inputs expose the admission failure

The generator excludes all inherited ordinary/composed query roots and native
roots, then selects 64 double-deletion neighbours from each of three templates.
Four separate worker processes run two reversed-order baseline/local pairs.
The same 192 inputs produce 84 SAT and 108 UNSAT answers in both policies.
No tests, profiling or builds overlap production. These are new query roots
from this generator, not an independent distribution of arbitrary SAT instances.

| Measure | Baseline | Local |
| --- | ---: | ---: |
| New native rows | 250 | 250 |
| Added native bytes | 495,299 | 490,681 |
| Expansion calls | 19 | 12 |
| Explicit trace publications | 0 | 7 |
| Probe + premise/child propagation visits | 6,634 | 7,797 |
| Mean serialized query/warm records | 5,409,405 bytes | 5,473,649.5 bytes |
| Mean query time | 1.498 s | 1.563 s |
| Mean complete worker time | 17.337 s | 20.173 s |

All seven remaining targets enter local discovery: four already have baseline
unit conflicts, and three yield a guard on the first premise probe. Seven
trace publications account for the seven fewer expansion calls; total new rows
do not fall. Native bytes decline only 0.93%, while measured propagation rises
17.53% and serialized records grow 1.19%. Complete time is higher in both pairs
by 3.026 and 2.646 seconds. These two pairs give no stable general runtime claim.
Cold replay averages 8.681 / 10.463 seconds and setup varies despite identical
preparation work. Mean process peak RSS is about 522 / 516 MB; this small noisy
difference does not establish a live-state memory improvement. SQLite occupies
69,156,864 / 69,148,672 bytes, while compressed trials are 5,042,730 / 5,043,275
bytes: physical and compressed storage need separate reporting.

The three guard cases explain the native-row result:

| Fresh case | Assumption | Baseline / local rows | Baseline / local native bytes | Local restricted child |
| --- | --- | ---: | ---: | --- |
| 144 | `[-270]` | 3 / **11** | 6,331 / 17,363 | Two forced units, then general splitting |
| 167 | `[-90]` | 8 / **2** | 15,325 / 3,462 | Unit conflict, 26 trace steps |
| 190 | `[-110]` | 4 / **2** | 6,834 / 3,047 | Unit conflict, seven trace steps |

Case 144 accounts for **10 of the 12 remaining child expansions**. Its baseline
uses one split, two unit nodes and a pre-existing negative dependency with
61 clauses / 159 literals. The local child uses three splits and seven unit
nodes, plus the separate premise row, and has no pre-query dependency hit.
The saved proof frontiers bind that cached root for further investigation.
This identifies a reuse risk when changing residuals; it does not show that
every conditioning step loses a reusable proof. Per-query fresh contributions
come from streams whose prefixes can diverge, so they are not isolated causal
comparisons at identical states.

## Next experiment

Screen the restricted child before publishing the guard. Start with an exact
known native answer or a retained unit-terminal trace, and keep ordinary solving
as fallback for a nonterminal child such as case 144. Reuse both premise and
child traces during checked publication. Preserve cheap native-family priority:
even two terminal certificates can cost more than a single native two-CNF proof.
This is a proposed admission rule, not a minimum-cost guarantee.

Compare at case 144's exact fresh-trial prefix, retaining 167/190 as positive
controls and historical 43/172 as useful nonterminal cases a strict gate would
miss. Then use another excluded query set. Do not present the apparent eight-row
posthoc recovery as a measured stream improvement. Investigate whether the
baseline's cached negative dependency can be transported through the proposed
assignment cheaply; the diagnostic records its root, but no such transport is
implemented here. Compact source references and shared cold checking remain
supporting targets because checking and duplicated sidecar sources dominate
the complete cost.

## Preservation

Resume [the checkpoint](../experiments/results/cnf-local-guard/checkpoint.json).
It preserves all **21,528 previous native payloads** and contains **21,801 keys**,
with no alternative payloads. The union retains 390 new composed records: six
historical controls and both 192-query policies, rebuilt against the union's
checked witnesses. All 2,957 ordinary decisions, 438 earlier composed records
and six earlier projections also pass cold checking. Composed schemas remain
separate from ordinary catalogs. The new database is 69,226,496 bytes, compressed
to 5,050,133 bytes; all arm artifacts remain retained.

All **1,069 tests** and 12 focused tests pass, including exhaustive two-variable
CNFs under original and renamed/polarity-reversed representations. The full
suite retains 44 existing SQLite ResourceWarnings; focused tests emit none.
All **469 prior sources / 5,057 artifacts / 87 manifests**, four frontier
lineages, structural authorities and 64 manuscript proof blocks are preserved.
Fresh query validation does not enlarge the separate structural-coverage
authority. No new Lean, compact-closure or unrestricted-SAT theorem is claimed.
