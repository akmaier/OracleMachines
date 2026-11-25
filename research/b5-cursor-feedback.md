# Compose B5 failures into a checked sixth feedback bank

Checkpoint: 25 November 2026. The 26 retained B5 failed assumptions imply 26
exclusion units. Propagating them together refutes `(64,16)` without a new
assumed probe. Its native certificate passes both independent readers, raising
sampled structural recognition from **226/246 to 227/246**, with **19 open**.
The reference snapshot already labels this formula UNSAT; this is a new checked
structural route to that answer, not a previously unknown truth value.

Seven remaining closures gain **22 assignments**, including ten beyond explicit
exclusion variables. Complete local certification of the gained root takes
0.09771 seconds versus 0.27312 for fresh bounded solving, with 80.73% fewer
encoded bytes. The 20-case discovery census is 0.29% slower than its control,
and reconstruction plus semantic checking still take 78.71% of its time.

## Pattern and soundness

The recognized pattern is interaction among individually checked failed
assumptions. For each saved trace proving that B5 with literal l is inconsistent,
B5 entails the exclusion unit not-l. Thus B6, formed by adjoining these units,
has exactly the same models as B5. A checked unconditional B6 propagation
conflict is consequently a refutation. Repeating this reasoning through the
previous banks preserves the source formula's meaning; source guards retain
their checked conditional proofs. No open search-history entry becomes an axiom.

Preparation validates the source, guards, older proof layers, complete closures,
and all three cursor bindings/schedules/failure traces before any warm result
lookup. New exclusions cite proofs on B5. Native reconstruction expands those
reasons through strictly decreasing banks B6 to B0. Support slicing retains and
remaps every used dependency, checks the compact proof again, and falls back
to full support when coordinates cannot be transported. The existing bounded
direct unit shortcut uses only the actual source residual; failure or exhaustion
falls back to layered reconstruction. Neither an open result nor an exhausted
single-literal order decides SAT.

A changed bank invalidates its old scheduling binding. The next pass may only
transfer B5 history after checking exact bank and complete-closure equality,
including trace and trace allowance, as in the previous migration experiment.
The seven changed cases require fresh bindings. Twelve unchanged cases retain
candidate histories, subject to those exact checks. A shared category label or
equal assignment count is insufficient.

## Matched evidence and cost

The exposed 20-case parent frontier is tested twice in opposite arm order.
Both arms pay all provenance checks and construct B6; `base` propagates B5,
while `feedback` propagates B6. Both use the same 262,144 occurrence allowance
and 256-step trace limit, with zero new assumed probes. Construction, indexing,
initialization, reconstruction, serialization/reload and semantic cold checking
are charged separately or in complete time. Startup/loading, prior acquisition,
final audit and diagnostic closure exports are additional. There is no holdout.

| Summed per-target means | B5 control | B6 composition |
| --- | ---: | ---: |
| Source reconstruction (s) | 0.41395 | 0.41489 |
| Discovery/preparation (s) | 0.14602 | 0.14679 |
| Semantic cold checks/reload (s) | 0.14084 | 0.14039 |
| Complete census (s) | 0.70346 | 0.70547 |
| Propagation occurrence visits | 728 | 1,379 |
| Initialization clauses | 7,950 | 7,976 |
| Refuted events | 0 | 1 |
| Maximum process RSS (bytes) | 97,550,336 | 97,566,720 |

Composition expands coverage but does not reduce census runtime or peak memory.
All per-case regressions remain in the reports and decision record. The small
runtime differences are descriptive measurements, not a general speed bound.
The single gained root runs twice under fresh solving, layered compilation with
shortcuts disabled, and direct-unit compilation:

| Per-root means | Fresh | Shortcuts disabled | Direct units |
| --- | ---: | ---: | ---: |
| Solve/compile (s) | 0.10877 | 0.25005 | 0.04625 |
| Warm check (s) | 0.00130 | 0.00893 | 0.00900 |
| Both cold readers (s) | 0.11754 | 0.16341 | 0.03260 |
| Persistence (s) | 0.04126 | 0.07387 | 0.00740 |
| Complete trial (s) | 0.27312 | 0.49947 | 0.09771 |
| Encoded key/payload bytes | 527,579 | 563,568 | 101,657 |
| Native records | 78 | 324 | 44 |
| Maximum process RSS (bytes) | 58,818,560 | 60,014,592 | 50,905,088 |

Direct compilation reduces complete time 64.22% against fresh solving and
80.44% against disabled shortcuts. Warm provenance checking remains more
expensive than fresh warm lookup. Disabled shortcuts regress against fresh
solving. These positive-only trials include warm checking, both cold readers,
and persistence, but exclude acquisition, discovery and unresolved fallback.
All three unique archive/root pairs are independently restored and checked.

## Retained space and next opportunity

For k checked exclusions, the new bank adds at most k clauses and k literal
occurrences. This implementation still builds a clause-origin map, sorts the
whole resulting bank and constructs a fresh index. With m clauses, L literal
occurrences and maximum width w, sorting can cost O((m+k) log(m+k) w) literal
comparisons; the index needs O(L+k) space and initialization work. These charges
are in addition to checking all retained provenance. The propagation allowance
bounds occurrence visits, not total preparation, indexing or verification.
Direct native closure has its own shared query allowance; the fallback can
still expand many contexts. No bound on future layer count or unrestricted
certificate size follows.

The 19-case export retains all older fields plus complete B6 closures:
**1,155,036 bytes**, compared with the parent's 1,175,494 bytes for 20 cases.
Removing a closed case means this is not same-set compression. All historical
artifacts remain, so lifetime storage continues to grow. The remaining 12 B5
failures have now been incorporated; simply composing them again supplies no
new information. Seven cases strengthen: `(28,18)`, `(28,19)`, `(37,0)`,
`(61,52)`, `(61,60)`, `(61,61)`, and `(67,63)`. Case `(37,0)` gains 16 assignments,
ten beyond its six exclusion variables, making it the first coverage target
for fresh bounded probing. Twelve unchanged cases need later candidates or
stronger interaction; `(28,17)` already exhausts its current literal order.

Repeated source/provenance preparation remains the largest avoidable census
cost. Reuse of an immutable checked preparation should preserve full-content
bindings and cold validation and be evaluated separately from probing savings.
This checkpoint changes neither production defaults nor cumulative authority
tables. No efficient partition or uniformly polynomial solution of arbitrary
CNF has been established.

## Validation and reproduction

All **1,995 full tests** and **130 focused tests** pass. New tests cover joint
failure interaction, full/selected support, disabled/direct compilation, cold
readers, warm provenance rejection, forward-reason rejection, interrupted
propagation and generated small formulas checked against complete truth tables.
All 1,107 prior source fingerprints, 27,344 artifact entries in 195 prior
manifests, and 64 original manuscript proof blocks remain unchanged.

Resume `experiments/results/cnf-b5-cursor-feedback/checkpoint.json`, especially
`b5_cursor_feedback.remaining-closures`. Reproduce using `prepare`, `run_census`,
`cases`, and `run_trials` in `compare_cnf_b5_cursor_feedback.py`, then `validate`
and, after tests/manuscript checks, `seal` in `validate_cnf_b5_cursor_feedback.py`.
Use a fresh output directory with the preserved pilot and source snapshot.
