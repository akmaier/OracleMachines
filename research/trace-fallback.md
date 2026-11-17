# Reuse the baseline unit trace when discovery rejects a guard

The optional fallback now keeps the work already performed by discovery. When
the previous selector declines a candidate but its baseline has a nonempty unit
prefix, the solver publishes the original target using that trace and solves
the remaining residual normally. It does not acquire the rejected guard.

This reduces repeated propagation and preserves the native proof payloads on
all measured comparisons. It does not bound the remaining search, reduce stored
rows, or establish a stable total-runtime improvement.

## Contract and cost

The preceding selector still determines known-target, native-family, terminal,
propagated-residual and accepted-guard choices. A new choice is made only after
that selector returns no choice and retains at least one forced assignment.
The source-bound baseline trace is passed to the existing screened publisher.
It verifies each unit reason, restricts the same normalized target, runs the
ordinary native solver on that residual and checks the resulting source model
or negative certificate. Rejected guards and their discovery traces remain in
the experimental record; they are not published as accepted dependencies.

The old fallback repeats the target's propagation after discovery has already
performed it. The new fallback replaces that repeated pass with indexed unit
reason checks, while charging restriction, normalization, dependency reads,
publication and source verification. The residual's expansion budget still
applies, and exhaustion returns no verdict. One explicit target publication
replaces its expansion call, so fewer expansion calls do not imply fewer rows.
There is no constant bound on the residual proof or a new worst-case SAT bound.

## Exact-prefix controls

Twenty-seven arms cover the previous seven prefixes and cases 36/186 from the
preceding stream. They compare native baseline, propagated-residual discovery
and the new retained-prefix fallback. All arms restore identical native rows,
start with an empty checked-node cache and replay the same accepted guards.
Prefix reconstruction and copying are charged separately from per-arm execution.

| Control | Baseline visits | Previous visits | Retained-prefix visits | Rows, all modes |
| --- | ---: | ---: | ---: | ---: |
| Prior stream 36 | 1,453 | 5,299 | 4,046 | 5 |
| Prior stream 186 | 1,636 | 3,608 | 3,234 | 6 |

The new path removes 1,253 and 374 propagation visits respectively. It checks
28 and one unit-reason literals before publication. Discovery still costs
substantially more than native baseline. Single-arm timings do not improve:
the measured previous/new evaluation times are 5.821/5.989 ms and
7.027/7.193 ms. These samples establish no stable timing conclusion.

Historical cases 43/70 and older fresh case 144 also reuse their prefixes;
historical 172 has no baseline unit prefix and remains unchanged. Across all
nine controls, previous/new visits fall 23,813 -> 20,896. Both retain exactly
42 rows, 59,225 native bytes and 227,509 serialized delta/record bytes. Native
baseline uses 50 rows and 13,366 visits. The gate still rejects historically
useful nonterminal children; trace reuse alone does not recover their row savings.

## Another excluded stream

The frozen generator selects 64 double-deletion neighbours from each of three
existing templates, excluding all inherited query and native roots. There are
1,216 previous query roots per template; selection takes 1.541 seconds separately.
Six fresh workers run baseline/propagated/retained and the reverse order. Tests,
profiles and builds do not overlap production. All policies answer 103 SAT and
89 UNSAT queries; warm replay acquires no rows.

| Measure | Baseline | Previous policy | Retained prefix |
| --- | ---: | ---: | ---: |
| New native rows | 271 | 269 | 269 |
| Added native bytes | 527,695 | 527,030 | 527,030 |
| Expansion calls | 53 | 46 | 43 |
| Explicit trace publications | 0 | 5 | 8 |
| Propagation literal visits | 14,126 | 24,342 | 22,811 |
| Mean query/warm sidecar bytes | 5,358,819.5 | 5,504,126 | 5,508,350 |
| Mean query seconds | 0.822 | 0.840 | 0.835 |
| Mean full cold replay seconds | 9.031 | 9.091 | 9.017 |
| Mean complete worker seconds | 18.300 | 18.467 | 18.299 |

Three new queries reuse baseline prefixes. The previous/new native archives are
identical, and visits fall by 1,531 (6.29%). The extra prefix checks inspect
sixteen unit-reason literals across these queries. Sidecars grow 4,224 bytes
(0.077%). The new-versus-previous complete-time differences are +0.091 and
-0.426 seconds, so there is no stable speedup. The two-row saving against native
baseline belongs to the existing admission policy. Propagation still exceeds
baseline by 61.48%; repeated unsuccessful premise probes remain costly.

The earlier propagated-residual route has two fresh hits in this set, after
none in the preceding set. Those hits are shared by both optional policies.
Process peak RSS averages 765/763/764 MB, which is not a live-state memory bound.
All trial databases use 72,716,288 bytes; compressed sizes are
5,222,358/5,223,035/5,223,035 bytes. Logical additions and physical archive size
need separate accounting. These roots remain neighbours of three old templates,
not an independent arbitrary-SAT distribution or new structural authority.

## Next bottleneck

Four fresh queries account for all 43 remaining child expansion calls:

| Case in this catalogue | Saved forced variables | Exposed variables / clauses / literals | Child expansions |
| --- | ---: | ---: | ---: |
| 0 | 0 | 25 / 68 / 183 | 17 |
| 131 | 2 | 26 / 65 / 177 | 14 |
| 146 | 4 | 24 / 58 / 144 | 5 |
| 159 | 4 | 20 / 50 / 138 | 7 |

The gate labels all four proposals nonterminal, but a separate replay of each
rejected child's unit trace reveals a more concrete gap: **case 146 is already
positive-terminal**. Its 26 forced variables satisfy every clause of that child;
no residual clauses remain. The posthoc artifact retains the exact trace and
checks the canonical child model. The current gate tests only a known child or
unit conflict, so it overlooks this positive closure. Cases 0/131/159 still leave
nonfamily residuals with 139/119/125 literals after the proposed condition and
propagation.

**Next:** lift the case-146 child model through its proposed assignment and
check it against the original target. A successful full-target witness can be
published directly; a SAT certificate does not require acquiring the proposed
negative premise. Measure exact-prefix rows, recognition, model transport and
verification before claiming a saving, then test another excluded stream.
The current diagnostic neither constructs that original-target witness nor
acquires or times the alternate result.

Then price the genuinely unresolved cases 0/131, which account for 17/14 of the
43 expansion calls. Case 0 has no initial unit prefix and pays 1,908 extra
propagation visits for discovery. A read-only exhaustive single-variable test
finds no variable whose two immediate restrictions are syntactic two-CNF in any
of the four baseline residuals. This test does not run further propagation;
conditioning followed by propagation or mixed-family closure remains open.
The earlier case-36 single-variable decomposition remains a positive control
whose alternative proof acquisition is unmeasured. Preserve shared-variable
interactions, native dependency reuse and rejected-probe costs. Cold replay
remains the largest complete-time component; shared checking and compact source
references remain supporting targets.

## Validation and resume point

All 1,094 tests and 25 focused tests pass. The new tests cover positive and
negative unknown residuals, rejected-guard preservation, renaming and polarity
transport, disabled leaves, budget exhaustion, corrupted traces, cold replay,
and 256 three-variable clause subsets in two representations. Independent
validation reconstructs all 27 control prefixes, regenerates the fresh catalogue,
checks every selection and certificate, and verifies identical previous/new
native payloads across all controls and fresh streams.

Resume `experiments/results/cnf-trace-fallback/checkpoint.json`: 22,532 native
keys, all 22,259 previous payloads preserved, 603 new composed records alongside
1,827 earlier composed records, 2,957 ordinary decisions and six projections.
There are no alternative payloads. All 488 prior sources, 5,329 artifacts and
91 manifests remain unchanged. Ready/pending frontiers are 132/38 (active),
141/66 (extended), 85/91 (causal) and 85/118 (incremental causal). These are
retained-bank availability counts, not new structural authority. Original and
supplemental structural coverage remain unchanged.

The evidence union uses 72,720,384 database bytes and 5,223,549 compressed bytes.
It retains all arms, rather than representing a single policy's working storage.
The paper preserves all 64 previous proof blocks. No new Lean theorem or
unrestricted-SAT efficiency bound is established.
