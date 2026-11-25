# Compose failures found beyond the old probe prefix

Checkpoint: 25 November 2026. Composing the 161 checked B3 failures saved by the
[persistent cursor study](probe-cursor.md) refutes **12 of the 41 remaining
events without new assumed probes**. These events contain **11 distinct native
roots**, all accepted by both independent readers. Sampled recognition rises
from 205/246 to **217/246**, with **29 unresolved**. One gained root had an unknown
answer in the inspected snapshot; the other ten were already recorded UNSAT.
Fresh bounded local solving also proves all eleven in the present comparison.

This is a coverage improvement, not an aggregate runtime improvement. On the
eleven positives, native compilation takes 90.14% more time than fresh solving;
complete local trials take 60.18% more and encoded records use 0.73% more bytes.
The experiment and every regression are retained. Production defaults and the
cumulative authority tables are unchanged.

## Exact composition and invalidation

Let B0 be the checked source/guard bank. Earlier failed-probe layers supply
consequences in B1, B2 and B3. A saved cursor failure under literal l is checked
against its exact B3 bank, including its transported closure prefix. It proves
that B3 entails not-l. B4 consists of B3 and these checked unit consequences.
One unconditional propagation pass on B4 can combine consequences obtained by
different probes, without reacquiring those probes.

Every model of the source satisfies B0 and, inductively, each added unit. Thus
a checked conflict on B4 proves that the source has no model. Search history
alone supplies no unit: an alleged open probe, an exhausted candidate list or a
budget-limited result remains unresolved. The cursor's full binding and schedule
are validated, but its open-history entries remain trusted scheduling data under
the earlier contract. They are never native proof axioms.

The support planner selects the source clauses, guards and earlier failed traces
actually needed by a conflict. It remaps coordinates and checks the reduced
banks again. Native reconstruction descends strictly through B4/B3/B2/B1/B0;
it never treats a B3 failure as a proof on B0. Ordinary component, unit, empty
and split rules establish the final certificate, with unchanged native child
checks and both independent cold readers. Warm root lookup follows validation
of the current supplied provenance. Publication uses the previously measured
immutable header handoff; general context caching is not enabled.

The old cursor binds B3. It cannot justify skipping tested candidates on a
different B4 bank, even when a candidate was previously open. Changed formulas,
guards, closure traces, proof coordinates or cursor bindings must be checked
again. Complete fixed points on the remaining B4 banks are preserved separately
as `cursor_feedback_closure`; all earlier closure and cursor fields remain intact.

## Measured work and storage

The protocol freezes the current 41 events from eight targets. The pilot was
exposed before timing; this is not a holdout. Two opposite-order repetitions per
target and arm produce 32 isolated census workers. Both arms check all previous
layers, closures and cursor history and construct B4; the control propagates B3
and the candidate propagates B4. This isolates the effect of the checked new
units; it is not a comparison against a control that omits their acquisition
and validation altogether.

| Sum of per-target mean times | B3 control | B4 feedback |
| --- | ---: | ---: |
| Discovery, checking and preparation | 0.21959 s | 0.21901 s |
| Source/prefix reconstruction | 0.71145 s | 0.70988 s |
| Complete census | 0.93508 s | 0.93364 s |
| Refuted events | 0 | 12 |

The small timing difference is not evidence of a speed advantage. About 76% of
the candidate census is source/prefix reconstruction. Both arms perform exactly
41 unconditional unit passes and zero assumed probes. Feedback adds 161 unit
occurrences to the indexed banks (47,629 to 47,790 aggregate literal occurrences)
and raises propagation occurrence visits from 1,053 to 6,515. Full preparation,
history checks and sorting remain charged outside the propagation-visit cap.
Peak process RSS is 96,993,280 versus 97,075,200 bytes, providing no useful
census memory reduction.

Eleven positive roots receive fresh and layered native trials in both orders,
for 44 isolated trials. The totals below sum per-root means. Complete trials
include setup, compilation/solving, warm checking, both cold readers and archive
serialization; they exclude discovery, earlier evidence acquisition and fallback
on unresolved events. Final validation independently restores all **22 unique
archive/root pairs** and checks both readers and all authority-table digests.

| Positive-case metric | Fresh | Layered feedback |
| --- | ---: | ---: |
| Solve/compile | 1.17985 s | 2.24338 s |
| Warm check | 0.01770 s | 0.09731 s |
| Cold readers | 1.26201 s | 1.71413 s |
| Persistence | 0.43028 s | 0.61255 s |
| Complete trials | 2.93697 s | 4.70459 s |
| Encoded key and payload bytes | 5,702,467 | 5,744,105 |
| Records | 489 | 2,246 |

Runtime improves on two roots and regresses on nine. Bytes improve on nine, but
`new-28-62` and `new-61-70` grow enough to reverse the aggregate saving. The latter
requires 1,585,067 bytes versus 484,719 fresh and 1.21141 seconds versus 0.25972
seconds complete. Despite causal support selection, the compiler still creates
2,065 native split nodes. This identifies repeated proof expansion and cofactor
preparation as a concrete cost target; fewer selected source clauses alone do
not ensure cheaper certificates. Peak positive-worker RSS is 88,768,512 bytes
fresh versus 76,988,416 layered, a local measurement without a general memory
bound. Independent archives can duplicate records that a shared store would reuse.

The 29 open B4 closures contain **97 assignments**, with **70 additions in 19
events** relative to their B3 closures. Of those additions, **24 go beyond the
46 retained cursor-exclusion variables**. Ten events remain unchanged. A separate
scan-based reconstruction/checking diagnostic costs 0.18231 seconds; it is not
included in bounded census timings. The complete closure/history export is
989,481 bytes and retains every previous field. The smaller event population
prevents interpreting its size as a per-instance storage reduction.

For a checked B3 bank with C clauses and L literal occurrences and U added units,
the occurrence index and one complete propagation pass require O(C+L+U) expected
word work and space, in addition to dictionary construction/sorting and checking
all retained traces and bindings. This is a local propagation bound. It does
not bound acquisition, the number of future banks, context-dependent native
expansion, serialization or lifetime storage. The implementation's 262,144
occurrence-visit and 256-step trace budgets do not bound total preparation work.
No result here gives a uniform polynomial algorithm for arbitrary CNF.

## Validation and next targets

All **1,953 solver tests** and **88 focused tests** pass. New tests include a
14-variable exhaustive fixture, random five-variable formulas, source/guard
prefix lifting, full and reduced support, cold replay, open satisfiable inputs,
budget limits and rejection of malformed provenance before warm lookup.
The manuscript retains all 64 existing proof blocks byte-for-byte. The audit
preserves 1,086 previous source fingerprints and 190 previous manifests covering
26,289 artifact entries; the new ledger contains 1,090 sources. Earlier artifacts,
including failed ideas, are unchanged.

The highest coverage opportunity is bounded probing on the **19 strengthened B4
closures**, with fresh exact bindings. Previously open B3 candidates can now
fail, so carrying forward B3 skip history would lose opportunities. The ten
unchanged cases need untried candidates or stronger interaction; blindly repeating
the same completed prefix adds no information. Do not infer exhaustion or SAT
from a skip.

The highest measured cost opportunity is to avoid repeated source/cofactor and
native proof construction while preserving exact checking. First measure the
two large certificate-growth cases against the existing publication-only
baseline; retain branch/context identity and invalidation explicitly. The
current experiment does not establish that additional caching will pay for its
own preparation and retained space.

Resume from
`experiments/results/cnf-cursor-feedback/checkpoint.json` and its
`remaining-closures.json`. `analysis.json` records all timings and regressions;
`support-plans.json` records reduced derivations; the sealed manifest binds all
new evidence. Earlier acquisition and unresolved fallback still need a complete
workload comparison before claiming net savings.
