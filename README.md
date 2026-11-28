# Oracle Machines

A perspective on **resource accounting for learned reasoning**: how preprocessing,
stored knowledge, neural representations, and exact solvers redistribute computation
between acquiring an answer and using it later.

**Terminology:** SAT with no fixed size cap remains the satisfiability problem.
UNSAT denotes unsatisfiable valid formulas and is coNP-complete. An invalid
encoding is neither a satisfiable nor an unsatisfiable formula.

The central architectural conclusion is that **the efficiency rationale for
combining System 1 and System 2 survives either resolution of P versus NP**.
Either way, the relevant comparison is avoided computation versus acquisition,
retrieval, verification, and control costs. Actual savings depend on the workload
and implementation.

The exact reuse identity applies to **every decidable language**, including
problems in PSPACE, EXPTIME, and EXPSPACE. This generality concerns the cost
comparison. Cheap certification, compact storage, and efficient acquisition need
their own justification, and finite tables for an undecidable language do not
provide a uniform computable way to construct them.

The project connects established ideas from complexity theory, knowledge
compilation, memoization, and amortized inference to the interaction between fast
and deliberative computation. Its contribution is an explanatory synthesis; the
finite-domain constructions do not establish a collapse of unrestricted complexity
classes.

## Paper

[Separate answer certificates from retained knowledge](research/answer-certificate-projection.md):
all sixteen reused answers are preserved while replay falls **45.71%**.
Preparation costs **9.80 seconds**, about five repeated checks to repay;
full archives remain stored, so total storage grows. All **2,708 tests pass**.

[Reuse a local proof-checking context](research/prepared-prefix-replay.md): source
reconstruction improves 45.00% and the complete measured workflow 23.41%, with
identical hints and search results. Sparse-hint and missing-support regressions
are preserved. Memory and structural recognition remain unchanged at 230/246.
All 2,075 tests pass.


[Share common proof preparation](research/shared-joint-preparation.md): complete
measured discovery/checking time falls 22.07% on sixteen current cases, with
identical banks, results and search counters. Memory and retained state are
unchanged; source reconstruction is the next largest cost. Recognition stays 230/246.
All 2,066 tests pass.


[Probe combined constraints with exact history reuse](research/joint-probe-cursor.md):
one additional checked refutation raises sampled recognition to 230/246.
Reuse avoids 1,878 probes but saves only 1.49% of complete census time; the new
native certificate is slower and larger than fresh solving. Six orders remain
unfinished, and one newly strengthened residual is the next coverage target.
All 2,057 tests pass.


[Compose failures on their original banks](research/joint-cursor-feedback.md):
one additional source-only refutation raises sampled recognition to 229/246.
The combined certificate uses 35 records versus 77 fresh, with 39.93% lower
complete positive-case time. B7-only proofs also suffice; joint proofs reduce
cost. Four remaining closures strengthen. All 2,048 tests and both independent
readers pass; unrestricted-SAT and lifetime-storage bounds remain open.

Previous:

[Share checked B7 expansion](research/fused-b7-expansion.md): combining validation,
composition and search cuts expansion time 44.70% and total measured time 16.97%,
with identical results on eighteen inputs. Eleven empty stages reuse physical
state. All 2,039 tests pass. Both discovery histories remain unchanged; combining
their proofs and sharing source reconstruction are the next targets.

Previous:

[Explore B7 failure interactions](research/b7-probe-cursor.md): composition
forces 26 assignments and probing finds 15 failed assumptions, without a new
refutation. Exact reuse avoids 1,788 probes, but total measured saving is only
1.05% versus matched fresh search. Adding the layer is costlier than continuing
B6; avoiding empty layers and repeated preparation is the next target. All 2,030
tests pass. Both discovery histories and regressions are retained.

Previous:

[Share checked cold recovery](research/checked-b6-restore.md): validating a full
saved result and constructing its session share preparation, reducing restoration
time 46.86% and complete measured time 16.47%, with identical results. Source
reconstruction now dominates. No new refutation; 25 failures in seven cases are
retained for composition. All 2,021 tests pass. Storage and general-SAT bounds
remain open.

Previous:

[Reuse checked B6 preparation](research/prepared-b6-search.md): prepared sessions
cut complete incremental-search time 44.32% versus repeated chunk calls, with
identical results. A single uninterrupted pass remains 2.61% faster; peak memory
and cold recovery do not improve. Continuation retains 24 failures in seven
cases, with coverage unchanged at 228/246. All 2,013 tests pass.

Previous:

[Advance B6 discovery](research/b6-probe-cursor.md): one more checked structural
refutation reaches 228/246 sampled recognition, with 18 open. Exact history
transfer avoids 1,472 repeated assumptions, but complete census time barely
changes and the open export grows 9%. Nine failures in six cases are ready for
composition; six other cases exhaust the current literal order without deciding
SAT. All 2,005 tests pass.

Previous:

[Compose B5 failures](research/b5-cursor-feedback.md): one additional checked
refutation reaches 227/246 sampled recognition, leaving 19 open. Seven remaining
closures gain 22 assignments. The gained root uses 81% fewer certificate bytes
than fresh solving; the full discovery census is slightly slower. All 1,995
tests pass. Next probe the strengthened closures and reduce repeated preparation.

Previous:

[Transfer exact B4/B5 frontiers](research/b5-probe-cursor.md): five more events
obtain checked native refutations, reaching 226/246 sampled coverage with 20 open.
Sixteen exact bank/closure matches reuse 1,024 prior assumptions and match a
fresh extended search exactly; complete census time improves only 1.48%.
Twenty open states retain 26 new failures in eight cases for composition.
All 1,987 tests pass. Acquisition and unrestricted-SAT obligations remain explicit.

Previous:

[Compose B4 failures](research/b4-cursor-feedback.md): four more events obtain
checked native refutations, reaching 221/246 sampled coverage with 25 unresolved.
On all four gained roots, direct-unit certificates beat fresh bounded solving;
complete positive trial time falls 73.35% and bytes 81.40%, excluding historical
acquisition and discovery. All 1,977 tests pass. Nine open B5 closures gain 85
assignments; these and later candidates in sixteen unchanged cases are next.

Previous:

[Fresh B4 frontiers](research/b4-probe-cursor.md) expose 69 checked failures in
13 open cases, with no direct refutations. Changed-only probing avoids 640
assumptions with the same observed failures; complete census time improves
only 2.02%, and peak memory does not improve. All 1,969 tests pass. Coverage
remains 217/246. Next compose these failures; preserve the full control cursors
for later candidates. [External research](research/pequalnp-watch.md) is reviewed
daily for relevant ideas while our own gap analysis continues to guide the work.

Previous:

[Close native residuals before expanding saved proofs](research/direct-unit-closure.md).
Bounded ordinary unit proofs reduce complete local trial time 78.35% and encoded
bytes 80.33% versus the B4 compiler on the same eleven roots. Records fall from
2,246 to 306, all independently checked. One case remains slower than fresh
solving; acquisition and unresolved fallback are outside this comparison. All
1,961 tests pass. Coverage stays 217/246; next probe the 19 strengthened closures.

Previous:

[Compose the cursor's saved failures](research/cursor-feedback.md). One checked
propagation pass closes 12 more events without new assumed probes, reaching
217/246 sampled events; 29 remain unresolved. Nineteen open closures gain 70
assignments. Both readers verify all 11 distinct new native roots; all 1,953
tests pass. Complete positive-case trials are 60.18% slower than fresh solving,
so the next cost target is repeated certificate expansion. Next coverage target:
probe the strengthened B4 closures with fresh bindings.

Previous:

[Resume the probe frontier](research/probe-cursor.md). Cold cursors avoid 2,624
repeated probes and exactly match one 128-probe run. Later candidates yield 142
additional failures in 31 cases; two first-prefix refutations bring coverage to
205/246. Resume saves 1.37% total time versus restart, but costs more than a single
uninterrupted run. All 1,945 tests pass. Next: compose the 161 failures retained
in 31 open cases and reuse checked preparation.

Previous:

[Compose the third layer of failures](research/third-feedback.md). Two more
verified refutations require no new assumed probes, bringing sampled coverage
to 203/246; 43 remain open. Six closures gain 18 assignments. Native compilation
is 2.16 times as slow as fresh solving and uses 27.92% more record bytes on the
two gains. All 1,935 tests pass. Next: resume untested candidates and reduce proof
construction costs; retain the observed regressions.

Previous:

[Probe changed closures](research/changed-closure-probes.md). Eight more events
have verified native proofs, reaching 201/246 recognized events; 45 remain open.
Skipping unchanged cases avoids 2,048 probes and reduces discovery 11.75%, but
complete census time only 2.21%. Native compilation remains slower than fresh
solving. All 1,927 tests pass. Next: compose the 27 new failures retained in eight
open cases and advance search beyond previously tested candidates.

Previous:

[Reuse prepared residuals at publication](research/prepared-publication.md).
Compilation falls 7.43% and complete local trial time 3.72% on the fifteen latest
roots, with identical proofs and checks; all 1,919 tests pass. Coverage and storage
are unchanged. Ordinary solving is still faster. Next: exact child-cofactor reuse
and bounded search on the 21 changed closures.

Previous:

[Compose the next layer of saved failed probes](research/layered-feedback.md).
One propagation pass closes 16 more events without new assumed probes, producing
15 verified native roots; all 1,911 tests pass. The remaining 53 cases retain
207 assignments. Native compilation is 54% slower than ordinary solving despite
26% fewer bytes. Next: reuse canonical cofactors and probe the 21 changed closures.

Previous:

[Probe the residual of a checked closure](research/closure-probes.md).
An additional bounded round closes 47 of 116 remaining events, with 41 distinct
new native proofs; all 1,903 tests pass. Reusing the closure halves propagation
visits and cuts discovery time 8.45%, with the same coverage as restarting.
Prefix reconstruction still dominates total census cost. Next: compose the 180
new failures retained in 37 open events and reuse preparation across rounds.

Previous:

[Feed saved exclusions back into propagation](research/probe-feedback.md).
One pass closes 64 of 180 remaining events without new assumed probes. All 53
distinct gained roots have native proofs; all 1,897 tests pass. The 116 open cases
retain 656 checked assignments for the next bounded search. Proof bytes roughly
halve versus ordinary local solving, but the whole-workload cost comparison
remains open. Next: condition on those closures and test new probes with provenance.

Previous:
[Compile smaller causal source supports](research/probe-support.md).
The same 60 recognized roots now compile 73% faster with 79% fewer proof bytes
than the full compiler; all 1,889 tests pass. Cold reuse across growing supersets
adds just a wrapper for each later formula. Coverage is unchanged, and ordinary
local solving remains faster in aggregate. Next: checked exclusion feedback and
profiling the remaining proof-construction costs.

Previous:
[Use failed probes to prioritize their opposites](research/complement-probes.md).
The same 64-assumption budget now closes 66 of 246 remaining events, up from 26.
All 37 additional distinct roots have checked native archives; two were unknown
in the prior snapshots. All 1,881 tests pass. Native proof reconstruction remains
slower and larger than ordinary local solving. Next: checked exclusion feedback
and smaller source-support proofs. A retained counterexample prevents treating
this sample gain as a universal guarantee.

Previous:
[Reuse wider guards in bounded unit probes](research/wide-guard-probes.md).
The new detector closes 26 remaining events, versus 24 with binary guards and
16 with source clauses alone. All 23 distinct gained roots have checked native
proofs; all 1,875 tests pass. Proof reconstruction is substantially more expensive
than ordinary local solving. Next: reuse failed probes to test untried opposites,
while retaining the proof-cost regression and unresolved cases.

Previous:
[Convert preparation savings into broader discovery](research/shortening-budget-frontier.md).
A fixed search-budget sweep raises recognition from 266 to 347 of 615 events at
slightly less measured cost than the older implementation, or to 369 with a small
increase. All 67 gained local roots have checked native archives; all 1,865 tests
pass. They were already known to ordinary whole-query search, so no whole-query
speedup is claimed. Next: exploit wider checked guards in the remaining cases.

Previous:
[Reuse immutable source preparation across conditioning](research/shortening-prepared-source.md).
Discovery time falls 21.46% across 615 saved events, including copying costs;
the complete measured phase falls 12.90%. All programs and 173 native root proofs
are identical, with unchanged persistent proof size. All 1,861 tests pass.
Next measure whether broader discovery budgets convert the saving into coverage.
No whole-query speedup or unrestricted-SAT bound is established.

Previous:
[Filter impossible paths using binary-clause structure](research/shortening-reach-filters.md).
Endpoint filters increase ternary-first recognition from 263 to 266 saved events;
weak components add no further successes. Contrapositive edge pairs make the
incoming-endpoint index redundant, so a specialized version removes its scans
without changing any result. Measured savings are small, and ordinary search
beats proof compilation on the three new local roots. All 1,853 tests pass.
The filters remain optional; the next target is repeated source preparation.

Previous:
[Prioritize literals with more potential clause shortening](research/shortening-root-priority.md).
Ternary-first ordering with reuse recognizes 263 of 615 saved events, versus
202 with numeric ordering, while measured discovery time falls 9.89%. It gains
72 events and loses 11, so it remains optional. Thirty-eight roots beyond both
previous controls have checked native archives; ordinary search already knows
them. Edited-case checks and all 1,844 tests pass. Costs and regressions remain
explicit; no whole-query improvement is claimed.

Previous:
[Reuse completed negative reachability searches](research/negative-reach-reuse.md).
The optional detector recognizes 202 of 615 saved event patterns versus 142
at the original budget, representing 37 additional local roots. Each new root
has checked native proof archives. Ordinary search already knows these roots.
The uncached detector with twice the root budget recognizes 211 events at nearly
the same measured cost, with four cache-only and thirteen larger-budget-only events. Selected
supports save retained bytes but ordinary solving remains faster. Reuse stays
optional, with all misses, costs and prior evidence preserved.

Previous:
[Share checked preparation during partial clause shortening](research/shortening-context-reuse.md).
One immutable context now serves the guard checks within each conditioned state.
Discovery is 57.63% faster and compilation 28.90% faster than the frozen support
compiler, with identical discovery programs and native proof archives. Every
reason and conflict remains checked. The preserved failed trial led to
a regression fix for satisfied support clauses with disappearing variables.
The method remains optional; ordinary solving and all discovery misses stay in
the cost comparison.

Previous: [Discover binary interactions by checked partial clause shortening](research/guard-partial-shortening.md).
The offline detector closes 104 previously missed event patterns, representing
67 local roots, by iterating forced literals and rebuilding the binary graph.
All 67 are eventually found by ordinary search. Native replay validates every
step and keeps the selected support reusable across changed enclosing formulas.
Matched costs, misses and persistent proof archives are retained; the policy
stays optional and no whole-query gain is claimed.

Previous: [Reuse clause-cover proofs through their selected supports](research/guard-cover-support.md).
Across 18 local CNFs, compilation takes 75.30% less time and stores 86.16% fewer
record bytes than full-context covers. Six persisted expansions each add only
one wrapper. All seven pending proposals are now checked; ordinary search already
finds all 18 roots. Preparation costs and small-case regressions remain, so this
stays optional. Next: exact partial clause shortening with reusable proof supports.

Previous: [Compile wider source-clause covers from learned guards](research/guard-clause-covers.md).
Fifteen supported proposals yield 11 distinct local refutations, nine at previously
inconclusive gate sites. Ordinary search eventually finds all of them. The new
compiler is slower and stores more state, so it stays offline. Next reduce proof
contexts to shared supports and investigate partial clause shortening. The new
checkpoint preserves 38 supplemental proof archives and the unchanged cumulative
history.

Previous: [Share source preparation across selected guard proofs](research/guard-context-reuse.md).
Normalization visits fall 60.88% and position-map visits 56.63%, with identical
native proofs. Complete-worker time nevertheless rises 0.28%; keep this optional.
A preserved 12-variable counterexample identifies the next coverage gap: learned
binary guards can exclude every literal of a wider source clause while their
graph remains satisfiable. Next test bounded clause covers on that augmented
graph, with actual support proofs and native recomposition.

Previous: [Reuse the immutable parent when publishing proof history](research/history-layer-publication.md).
The same 173-record append now publishes about 38.1 KB instead of another
152.6 MB full snapshot. Preparation and publication fall 85.96%, and the
complete worker falls 71.40%, including cold restoration, exact table
comparison and proof replay. The parent remains required; cold restoration is
slower and the materialized history remains 2.10 GB. No SAT coverage or query
runtime changes. Resume the new checkpoint with its explicitly named layer
reader; the previous full snapshot remains available.

Previous: [Compose guard proofs on their supporting clauses](research/guard-support-composition.md).
The same 34 local closures now use compact native cores and checked subset
wrappers. Solve time falls 3.61% and checked native state 5.17% versus full-context
witness composition. Ordinary search remains faster by the measured 4.60%
overhead; no additional whole query completes. The audit identifies a larger
publication cost: 109 seconds recompressing old history for 173 new records.
Next test a checked parent-plus-delta archive; shared local context binding is
the next solver target. Prior results stay preserved and the gate stays optional.

Previous: [Prepare local proofs only for guard contradiction witnesses](research/guard-witness-deferral.md).
Deferring support checks preserves all 34 local closures and identical native
databases while reducing checked consequences from 1,218 to 87. Solve time falls
7.01% versus the eager gate, but remains 7.87% above ordinary search; no additional
whole query completes. The next target is native composition over the actual
contradictory clause support, with a checked lift to the full context. The gate
remains optional; prior results and regressions stay preserved.

Previous: [Test guard closure during live search](research/guard-closure-live.md).
Unit and binary guards close 25 and 34 local contexts, but complete no additional
whole query. Solve time rises 7.40% and 18.80% against ordinary search. The profile
points to proof preparation on inconclusive sites: next build a tentative graph
first and validate only its contradiction paths before native publication.
Both gates remain optional; all previous results and regressions are preserved.

Previous: [Compose guard interactions into checked local refutations](research/guard-interactions.md).
Saved consequences refute 61 local CNFs; 20 need binary guards, and three roots
were absent after the earlier shared query budget stopped. Local closure
acquisition takes 36.55% less time in single cold pairs, but discovery and storage
costs remain additional; isolated exclusion compilation regresses. No new whole
input completes. Next: a selective live closure check, starting with opposite
unit guards. All proofs, comparisons and prior solver results stay preserved.

Previous: [Reuse conditional certificates on the actual local cofactor](research/local-certificate-transport.md).
Direct reuse replaces 148 fresh unit refutations on the same guided search path.
Probe propagation work falls 17.19%, but solve time only 0.55%; complete-worker
time rises 0.20%. All eight exposed edits remain unresolved. The implementation
stays optional. Next: discover useful interactions among multi-assumption guards,
with exact local support and composition checks. Previous results stay preserved.

Previous: [Test guard-guided probes inside ordinary search](research/guard-probe-selection.md).
The new tracker preserves native search with 1.27% aggregate solve overhead.
Guard-guided selection instead costs 1.84% more overall, with mixed per-case
results and no new completed inputs. The largest regression's profile puts
normalization, checking and propagation far above guard matching. Next: test
direct reuse of conditional certificates on the exact local cofactor while
holding probe selection fixed. All controls and unsuccessful results are saved.

Previous: [Find missed probes at ordinary search contexts](research/guard-probe-census.md).
Saved guards identify 394 independently checked negative cofactors; ordinary
probing misses 260 of those polarities, including 232 on different variables.
Search and native proof files remain identical. All eight targets still stop;
capture adds about 32% solve time. Next: test a bounded live selector with cheaper
matching and exact local checking. No runtime or whole-input coverage gain is
claimed by this passive census; every previous result remains preserved.

Previous: [Select shared guard regions within the split budget](research/guard-frontier-selection.md).
The new plan cuts solve time 27.38% on one exposed edit but adds 4.66% on the
other. Both remain unresolved, and ordinary solving is still faster. Larger
closed assignment regions are useful structure, not a search-cost guarantee.
Next: apply checked exclusions at ordinary search contexts without forcing a
separate tree. All previous templates, controls and proof results remain saved.

Previous: [Capture conditional supports from unfinished origins](research/stopped-origin-supports.md).
Seven unfinished sources yield 342 checked conditional templates that survive
their edits. The first bounded plans still leave both tested targets unresolved:
solve time rises 6.31% / 5.62% versus the same trees with open leaves. Keep the
observer experimental. Next: compress and use the conditional exclusions without
imposing the current expensive branch order; charge extraction and checking.

Previous: [Defer binary preparation and retain the coverage frontier](research/probe-binary-lazy.md).
Lazy preparation saves 3.57% fresh solve time versus eager binary closure, but
remains 4.97% slower than handoff-only. Proof bytes are identical to eager closure;
all three policies retain 34/48 fresh coverage. Keep the gate experimental.
Next: reuse checked conditional leaves from unfinished origins across small
edits, with explicit open branches and source-support invalidation.

Previous: [Measure binary refutations inside inconclusive probes](research/probe-binary-closure.md).
The new gate finds valid cofactors but keeps 40/48 coverage and increases fresh
solve time 8.86%, complete-worker time 5.03%, and native payload 2.72%. It remains
experimental. Next: defer full-residual normalization until a binary refutation
actually requires a stored certificate; 61 of 67 normalizations in the worst
fresh regression serve only inconclusive checks.

Previous: [Retire consumed preparation and account for active memory](research/probe-lifetime.md).
Early release saves 3.54% fresh solve time and 1.92% complete-worker time versus
2 MiB retention; original 4 MiB retention nearly matches it. Proof storage and
coverage are unchanged, and no substantial memory reduction is demonstrated.
Next: inspect inconclusive probes for existing binary refutations on the eight
fresh roots still unresolved, including two edited mixtures.

Previous: [Reuse probe preparation at the actual child](research/probe-handoff.md).
A 2 MiB preparation allowance reduces solve mean 3.58% exposed / 2.68% fresh;
a 256 KiB allowance is slower. Proof storage and 42/48 coverage remain unchanged.
Next: release consumed ancestor preparation so useful descendant offers fit.

Previous: [Prefer complete results before partial reconstruction](research/whole-pool-priority.md).
Existing proofs replace two 57/58-dispatch reconstructions with zero fresh search.
Exposed solve mean improves 2.17%; fresh solve time is essentially unchanged,
while fresh complete-worker time falls 1.63% and proof payload 3.03%. Coverage
stays 42/48, and affine completion alone remains faster. The next target is
reusing inconclusive probe preparation on the unresolved random-three roots.

[Reuse surviving leaves from a whole refutation](research/whole-proof-frontiers.md).
An unresolved edit now has a checked native refutation within the same budget.
Exposed coverage grows from 38/48 to 39/48; fresh coverage is unchanged and solve
time regresses 4.04%. Next: preserve cheap complete reuse before partial reconstruction.

Previous: [Complete an already discovered affine space](research/whole-input-affine-completion.md).
An unresolved whole CNF now has a checked UNSAT certificate after testing only
16 affine candidates. Exposed coverage grows from 39/48 to 40/48 distinct roots;
fresh inputs retain the preceding coverage. Next: automatically reuse a checked
whole-CNF proof on a nearby edit that still exhausts the expansion budget.

Previous: [Reuse canonical clause structure in probe preparation](research/ordered-probe-preparation.md).
Fresh solve mean improves 4.54% against lookahead with identical proof bytes.
The next target is an unresolved whole CNF whose checked affine core leaves
only 16 assignments; existing completion and exhaustion checkers can be reused.

Previous: [Measure whole-input lookahead and its failed-probe costs](research/whole-cnf-lookahead.md).
The optional policy saves dispatches and stored proofs but adds solve time. It
completes one held-out query earlier; both arms eventually solve 47/48 distinct
roots. Next: price failed-probe recognition and share cofactor preparation.

Previous: [Test finer origins from recomposed proofs](research/refined-proof-origins.md).
The finer cover retains more supports but avoids no native expansion. It adds
2.39% preparation/query time and 45.89% hint bytes, so the admission policy stays
experimental. This motivated the whole-input study above.

[Pass prepared missing leaves into acquisition](research/missing-leaf-handoff.md).
Five duplicate normalizations disappear with identical native proof bytes and
checks, but preparation/query mean regresses 2.29%. The experiment stays
optional. Next: test a specific finer reusable subbranch; blanket admission of
newly recomposed origins does not reduce missing-leaf counts in the diagnostic.

[Carry original clause provenance](research/carried-clause-origins.md).
Indexed updates preserve exact supports and proofs while skipping 2,647
unchanged representatives. Cover-phase time improves 8.36%, but whole-stream
preparation/query mean regresses 1.79%; the negative result is retained. Next:
reuse the prepared missing-leaf input at the native acquisition boundary.

[Reuse checked order during causal reconstruction](research/preimage-fusion.md).
Sharing untouched clauses and their canonical order reduces repeated support
construction. Balanced repeats save 6.32% on controls and 4.49% on nearby new-edit
query means, including setup. Proofs and storage stay identical; complete-worker
cost barely changes. Next: source-bound reuse inside the surviving mixed branch.

[Prioritize a checked full-CNF cofactor](research/consequence-priority.md).
A narrow arbitration rule recovers the late-consequence regression and preserves
the useful joint case. New edits save 4.54% query time and 3.91% native payload
versus joint conditioning. Controls still regress slightly versus one-target
search; defaults remain unchanged. Next: reuse repeated conditioned structure
and causal support in the remaining expensive branch.

[Combine useful binary consequences](research/joint-binary-consequences.md).
The exposed branch takes four rather than nine expansions, saving 24.10% query
time and 24.86% new proof payload. Nearby new edits regress 4.05% in time, so the
policy stays optional. Next: recognize when a correct consequence yields a cheaper
full-CNF continuation, including its proof and future reuse costs.

[Resume native fallback before unwinding](research/live-fallback.md).
The exposed query takes 11 rather than 17 expansions and 20.71% less query time,
with identical proofs. New edits never need fallback and regress 3.89%, so the
mechanism remains optional. Next: share discovery and propagation of independently
useful binary consequences in the dominant partition branch.

[Try a second binary target after a miss](research/binary-target-fallback.md).
The optional recognizer reduces six new edits from 69 to 60 expansions and query
time by 8.29%; controls regress 1.14%. A direct-solving ablation separates better
search from avoided probe restart. Exposed branches still need nine expansions.
Next: reuse unfinished acquisition continuations while preserving checked proofs.

[Share first-false partition preparation](research/partition-preparation.md).
One shared preparation plus independent reconstruction replaces four identical
constructions. New-edit query time falls 6.15% under binary-frequency routing,
with identical proofs; complete worker time still regresses. The selected
preparation graph is 35.72% smaller, without a process-memory claim. Next: inspect
the saved 125-variable binary/ternary branch that still needs nine expansions.

[Hand prepared cofactor work directly to its child](research/cofactor-handoff.md).
One-use normalization and unit-propagation reuse lowers query time 2.66% on six
new edits, preserving all proof bytes. Complete worker time does not improve;
probe routing still costs more than binary-frequency routing. Next: share the
identical partition structure currently built four times per selected query.

[Reuse prepared cofactor normalization](research/prepared-cofactors.md).
A bounded memo removes about 7% of normalizer input work on nearby edits while
preserving every proof byte. New-edit query time still rises 0.75%; lookup and
validation costs offset the reuse. It remains optional. Next: direct handoff of
prepared cofactors and useful propagation evidence, with probe admission charged.

[Check both cofactor polarities](research/bipolar-routing.md).
The two-polarity guard reduces the saved residual and both sign variants from
30 to four expansions. It fixes the demonstrated recognition blind spot, but
raises time and proof storage on nearby edit streams. Keep it optional; cheaper
probe admission and reuse of propagation work are the next cost questions.

[Control routing and probe polarity](research/binary-routing.md).
An identical-state comparison confirms the routing regression. A false-only
cofactor guard lowers expansion counts but increases query time, so it is kept
as an unsuccessful experiment. A missed, checked true-cofactor contradiction is
the next precise discovery target.

[Choose binary consequences beyond the next split variable](research/ranked-binary-targets.md).
Binary-frequency targeting cuts the saved branch from 61 to nine expansions and
six new residual edits from 107 to 51. Another branch regresses from ten to 33,
so cost-aware routing remains the next gap. All proof records and failed cases
are retained; the general solver default is unchanged.

[Probe cheap native queries before support partitioning](research/probed-support-partition.md).
A short probe preserves checked partial proofs and avoids costly preparation for
cheap queries. The six-clause boundary improves from 75 to 26 expansions, but a
fresh deletion regresses from 65 to 86. Its dominant 61-expansion branch is saved
for the next structural investigation. Storage and warm-setup regressions remain;
the affine baseline stays in place.

[Compose transported supports with missing clauses](research/transported-support-partition.md).
A checked historical-prefix pilot cuts one residual's expansions from 69 to 17;
its edit stream improves from 143 to 92 through the addition, while deletion
falls back and regresses. Two cheap cases regress, and the old
branch-count screen selects poorly. Query gains shrink to under 1% in the complete
measured workflow; sidecar storage grows. Next: recognize useful structure after
conditioning and price all branches. The affine baseline stays in place.

[Retain variable maps across residuals](research/residual-variable-transport.md).
Automatic map transport and cold hint recovery work on numbering-shift controls,
but fresh-holdout query time rises 5.26% with unchanged outcomes. A mismatch audit
finds supports still missing 3–19 clauses. Next: price guarded/first-false
composition on the smallest gaps; keep the affine policy as the baseline.

[Learn from bounded partial-residual retrieval](research/partial-residual-retrieval.md).
The candidate pool adds 4.27% holdout query time with unchanged outcomes and
expansion counts. Keep the affine policy as the baseline. A checked counterexample
shows how compact variable numbering hides a reusable core; the next target is
bounded variable correspondence, with discovery and maintenance costs charged.

[Recognize affine contradictions before acquisition](research/bounded-affine-probe.md).
The checked probe reduces fresh-holdout query time 41.87% and SQLite storage
42.15% against planned reuse; unresolved attempts fall from 26 to 15. Warm replay
regresses, including on matched cases. All remaining holdout stops have affine
rank zero. Next: reuse certified residual supports from committed partial searches.

[Share support discovery with proof construction](research/shared-support-derivations.md).
Bounded query-local plans reduce query time 6.45% exposed and 2.62% on a fresh
size holdout against negative edit reuse, with identical proof bytes. Holdout
query time still exceeds witness-only search by 0.87% on the mean. A separate
checked affine screen refutes two native budget-stopped attempts; integrating
that structural probe with all costs charged is the next target.

[Reuse negative proofs only after an edit match](research/on-demand-negative-edit-reuse.md).
The optional policy finds ten checked UNSAT transfers per stream and reduces
holdout SQLite storage 9.37%, but query time increases 5.81%. Core materialization
adds smaller proof records. Next: share the bounded derivation work between
support discovery and checked publication; keep the latency regression visible.

[Retrieve SAT witnesses automatically](research/bounded-witness-pool.md).
A bounded pool checks assignment candidates without supplied donor labels. Across
exposed and separately frozen size-holdout streams, mean query time falls 2.97%
and 8.27%; holdout edit expansions fall from 1,342 to 955. Two capped attempts
remain unresolved in each arm. Next: reuse negative search across edits and retain
useful candidates through cold restart.

[Measure larger mixtures and recover a stopped query](research/larger-mixture-expansion-costs.md).
On 108 new-stream queries, both normalization alternatives regress; random 3-CNF
and fresh work after small edits dominate. A later checked model closes the last
unresolved source with one certificate and zero expansions. Initial budget stops
remain recorded. Next: bounded witness retrieval without generator hints.

[Preserve clause order during normalization](research/ordered-residual-normalization.md).
The optional exact path avoids 96,099 sort calls on the same 104 inputs, reducing
mean query time 2.17% against batching without a retained normalization cache.
The earlier memo remains faster; warm time regresses. Proofs and storage match.
Next: profile larger held-out mixtures before selecting another optimization.

[Reuse normalization during proof checking](research/proof-normalization-reuse.md).
On the same 104 inputs, a bounded optional memo avoids 262 repeated normalizations
and 21.31% of normalization visits. Mean query time falls 3.88%; complete-time
results are mixed. Proofs and persistent storage are unchanged. Next: exploit
preserved clause order without losing exact names, deduplication or proof checks.

[Batch verified publications](research/bounded-publication-batches.md).
On the same 104 inputs, grouping checked writes reduces commits from 605 to 104
and mean query time 35.55%, with identical answers and proof storage. Failed
queries retain committed prefixes; recovery and cache invalidation are tested.
Pending state and journal size grow. Next: reduce repeated residual normalization.

[Recognize canonical certificates directly](research/direct-canonical-verification.md).
Checking the stored normal form avoids 552 sorting/renaming calls while preserving
every proof rule. On the same 104 inputs, mean total runtime falls 6.63% and cold
replay 18.12%, with identical storage. Both readers validate all 28,886 native
records. The next measured bottleneck is 605 individual SQLite commits.

[Measure bounded normalization reuse](research/query-canonicalization-reuse.md).
A query-local cache avoids 19.57% of normalization visits on the same 104 inputs,
but validation and bookkeeping raise mean complete runtime 3.65%. Proofs and
acquisition are identical; keep the cache optional. Next: reuse validated results
directly between callers, with all identity and certificate checks preserved.

[Choose a checked known quotient](research/known-quotient-selection.md).
The new policy recovers eight extra native certificates from the all-block pilot,
with SAT and UNSAT reuse validated on an extended 104-query stream. Extra choice
work still raises mean runtime. Profiling identifies the next broader target:
469 repeated normalization calls within individual queries, with their variable
maps and exact keys preserved.

[Substitute multiple equivalence blocks](research/multiblock-equivalence.md).
Twelve pilot inputs now use a second block, but propagation falls only 0.52%
while native certificates grow by ten. Two sources already had a known one-block
quotient that the new policy ignored. Next: choose a checked known quotient before
fresh acquisition. All prior proofs and the measured regression are preserved.

[Reuse binary-core discovery](research/binary-core-discovery-reuse.md).
Exact reuse avoids 22 repeated graph constructions and cuts acquisition SCC work
44.53% on the same pilot. It retains 34 entries (11.9 KB serialized); persistent
cold validation makes total discovery work higher. Timings remain inconclusive.
All proof payloads are unchanged. Next: reduce child solving by substituting
multiple disjoint equivalence blocks.

[Compact equivalence certificates](research/compact-equivalence-certificates.md).
Exact source-key parsing and checked substitution remove duplicated formulas,
shrinking equivalence storage 60.80%. Combined certificate payload is now 6.17%
below the native control on the same pilot; query time remains higher. Both
formats and all previous results are preserved. Next: reuse binary-core discovery
across the 22 repeated cores in this workload.

[Acquire checked binary equivalence quotients](research/binary-equivalence-acquisition.md).
Two shared implication trees support exact full-source substitution and model/proof
reconstruction. A 68-input pilot reduces propagation 16.57% but increases combined
storage and runtime, so the API remains optional. Next: remove duplicated formulas
from its certificates. The preserved checkpoint contains 28,691 native keys,
twenty-six affine and forty-two explicit equivalence records.

[Target binary-forced split variables](research/targeted-backbone-discovery.md).
One additional implication query closes the six saved split-node recognition
misses. On sixty fresh queries it saves two stored nodes and 6.39% of child
propagation visits; noisy timing does not establish an end-to-end speedup.
Resume 28,145 native keys / twenty-six extensions in
`experiments/results/cnf-targeted-backbone/`. Next: checked variable merging from
binary equivalences, found in eleven ordinary split nodes without forced literals.

[Reuse partial binary backbones](research/binary-backbone-reuse.md).
A checked implication path now supplies an excluded-branch proof without rerunning
propagation. A frequency gate saves two native nodes on sixty fresh queries;
query time improves 3.04%, while total-worker time is essentially unchanged.
The first-path policy's storage regression is retained. Resume 27,888 native keys /
twenty-two extensions in `experiments/results/cnf-binary-backbone/`.

[Cover a wider clause with binary implications](research/binary-clause-cover.md).
Three certified covers on a fresh sixty-query stream replace eight search
expansions with six compiled children: a net saving of two stored nodes.
Query and complete-worker time improve slightly in both orders, while peak RSS
rises about 9.53 MB. The optional checkpoint preserves 27,600 native keys and
eighteen affine extensions. Next: reuse partial binary backbones before splitting.

[Refute mixed residuals through their binary subset](research/binary-subset-refutation.md).
Eight checked leaves remove 22 native nodes and 16,393 payload bytes on a fresh
sixty-query stream. Timing remains mixed, with mean complete-worker time up 0.82%,
so this remains optional. Resume the preserved 27,368-native / thirteen-extension
checkpoint in `experiments/results/cnf-binary-subset/`. The next discovery gap is
compatibility between satisfiable binary cores and the remaining wide clauses.

[Resume affine negatives on fresh queries](research/affine-session-reuse.md).
On sixty newly excluded queries, combined additions fall 344 -> 280 certificates
and mean query time 7.76%; complete worker time falls 0.45%. All prior payloads
remain in a resumable checkpoint with 27,087 native keys and ten affine negatives.
The largest unresolved acquisition cost is now random three-CNF; graph discovery
is another substantial cost. Evidence: `experiments/results/cnf-affine-session/`.

[Publish checked negative affine evidence](research/affine-negative-publication.md).
Seven selected negative targets now use seven versioned extension certificates
instead of 134 fresh native nodes. All 26,743 prior native payloads remain intact.
This matched prefix pilot improves both timing orders; a fresh-stream evaluation
and automatic production-checkpoint adoption remain open. The optional extension
checkpoint is in `experiments/results/cnf-affine-negative/`.

[Reuse checked affine spaces for native model completion](research/affine-completion.md).
Eight saved targets shrink 80 -> 8 native nodes. Nine fresh added models reduce
acquisition 395 -> 336 nodes and query time about 11%; complete-worker timing
remains mixed. Diagnostics grow 7.86%, while native storage and mean RSS fall.
All 1,169 tests and independent replay pass. Resume its checkpoint: 26,743
native keys preserve all earlier payloads. The next gap is publishing negative
affine evidence that already checks successfully but still triggers fallback. Evidence is in
`experiments/results/cnf-affine-completion/`.

[Choose one extra premise to complete a partial negative cover](research/cover-directed-probe.md).
Four saved parents shrink 52 -> 32 acquired nodes. On sixty fresh queries,
four added probes reduce acquisition 431 -> 407 nodes and query time 10.22%;
complete-worker time remains mixed. Diagnostic storage and peak memory grow
slightly. All 1,161 tests and independent replay pass. Resume its checkpoint:
26,279 native keys preserve all earlier payloads. Coupled parity and random
three-CNF still dominate acquisition; reuse of the existing affine discovery
layer is the next broader-coverage target. Evidence is preserved
in `experiments/results/cnf-cover-probe/`.

[Compile retained negative conditions into native parent proofs](research/negative-cover.md).
Three saved covers shrink 36 -> 24 acquired nodes; one fresh cover reduces
aggregate additions 370 -> 364 nodes, saving 7,153 native bytes. Discovery is
unchanged and query timing remains mixed. Three further cases each lack one
condition outside the candidate set, providing the next discovery target.
All 1,153 tests and independent replay pass. Resume
`experiments/results/cnf-negative-cover/checkpoint.json`: 25,757 native keys
preserve all earlier payloads. The 215-page manuscript builds with all existing
proof blocks unchanged.

[Complete mixed two-CNF conditions using the live residual](research/mixed-completion.md).
Four saved controls shrink from fourteen acquired nodes to four; two fresh
mixed-model completions reduce native additions 385 -> 381 nodes. Query and
complete-worker times improve in both orders, while diagnostics grow 1.18%.
The next target is a source clause whose every literal has a retained conditional
refutation, enabling exact parent recomposition. Evidence is in
`experiments/results/cnf-mixed-completion/`.
All 1,145 tests and independent replay pass. Resume its `checkpoint.json`:
25,334 native keys preserve all earlier payloads; the 214-page manuscript
builds with all existing proof blocks unchanged.

[Stop discovery when a checked model is already available](research/inline-completion.md).
Inline completion removes 84 of 190 probes on sixty fresh queries. Propagation
falls 36.18%, query time 7.33% and diagnostic sidecars 11.16%; native acquisition
is unchanged, and complete-worker time increases slightly. The next targets
are mixed conditioned models and positive discovery beyond the negative binary
filter. Evidence is in `experiments/results/cnf-inline-completion/`.
All 1,137 tests and independent replay pass. Resume its `checkpoint.json`:
24,922 native keys preserve all previous payloads; the 213-page manuscript
builds with every existing proof block unchanged.

[Complete conditioned residuals with checked uniform assignments](research/uniform-premise.md).
Nine additional fresh targets avoid search; native additions fall 452 -> 434
nodes and 535,908 -> 521,248 bytes. Diagnostic sidecars grow 2.83%, and query
timing remains mixed. All 1,129 tests pass. The next targets are mixed two-CNF
conditions and earlier positive stopping, which can avoid finishing unnecessary
probe passes. Evidence is in `experiments/results/cnf-uniform-premise/`.
Resume its `checkpoint.json`: 24,444 native keys with all previous payloads preserved;
independent replay and the manuscript build pass.

[Reuse satisfying assignments already found by premise probes](research/positive-premise.md).
Checked recovery replaces three acquired nodes with one in the motivating saved
case and two fresh gated-Horn cases. Across sixty fresh queries, native additions
fall 410 -> 406 nodes; complete timing remains inconclusive and diagnostic
sidecars grow slightly. All 1,120 tests pass. The next target is solving and
lifting nonterminal conditioned families without repeating earlier discovery.
Evidence is retained in `experiments/results/cnf-positive-premise/`.
Resume its `checkpoint.json`: 23,987 native keys with all previous payloads preserved;
independent replay, counter audits and the 212-page manuscript build pass.

[Skip structurally futile premise probes](research/binary-probe.md).
The optional residual binary filter removes 192 of 386 probes on 60 new queries,
reduces propagation work 29.07% and query/warm sidecars 15.13%, preserving identical
native certificates. Timing does not establish an end-to-end gain. The next
reuse target is a valid target model already present in case 50's discarded
premise probe; direct recovery is not implemented yet. Results and controls are preserved in
`experiments/results/cnf-binary-probe/`. All 1,113 tests and independent replay
pass. Resume `experiments/results/cnf-binary-probe/checkpoint.json`: 23,577 native
keys and 206 new composed records, with every earlier result preserved.

[Unfamiliar CNFs expose wasted discovery](research/cross-family.md).
All 48 new-family targets require unfamiliar acquisition, while 12 neighbour
controls are known after preparation. Discovery performs 384 unsuccessful probes
and raises mean query time 0.354 -> 0.482 seconds, with identical native results.
A checked structural condition identifies 192 probes that cannot produce a unit
refutation; implementing and pricing that filter is the next target. Full cold
replay remains the largest runtime component. Results and proofs are preserved
in `experiments/results/cnf-cross-family/`. All 1,106 tests and independent
reconstruction pass. Resume `experiments/results/cnf-cross-family/checkpoint.json`:
23,127 native keys and 120 new composed records, preserving all earlier results.

[Recover a target model from a positive child](research/positive-child.md).
At case 146's exact prefix, checked model recovery reduces six native rows to
one and native bytes 6,688 -> 1,798. The next 192-query set has no activation:
190 targets are already known after preparation. Broader evaluation now needs
new template families and uncached child targets. All 1,102 tests and independent
replay pass. Resume `experiments/results/cnf-positive-child/checkpoint.json`:
22,729 native keys and 615 additional composed records, with all earlier results
preserved.


[Reuse unit traces after rejected discovery](research/trace-fallback.md).
On 192 new queries, three retained prefixes reduce propagation visits
24,342 -> 22,811 while preserving identical native payloads and storage.
Discovery still exceeds native baseline work, and timing pairs establish no
stable speedup. A checked positive-terminal child in case 146 exposes the next
model-reuse opportunity; cases 0/131 remain the largest unresolved residuals.
All 1,094 tests and independent replay pass. Resume
`experiments/results/cnf-trace-fallback/checkpoint.json`: 22,532 native keys and
603 additional composed records, preserving every previous result.


[Reuse answers exposed by propagation](research/propagated-reuse.md).
At case 85's exact prefix, the new optional path cuts propagation visits
5,750 -> 955 and avoids four premise probes, retaining the same one-row result.
A further 192-query comparison has no new residual hits and no stable timing
gain. Next, reuse saved unit traces after rejected discovery and test small
conditioning sets. All 1,085 tests and independent replay pass. Resume
`experiments/results/cnf-propagated-reuse/checkpoint.json`: 22,259 native keys,
597 additional composed records, with all earlier results preserved.


[Fresh admission saves rows but misses a cached residual](research/child-stream.md).
On 192 new queries, the unchanged gate reduces rows 229 -> 221 while increasing
propagation, sidecars and observed complete time. Case 85 exposes a checked binary
residual after propagation; the next step is to reuse it before new probes.
All 1,076 tests and independent replay pass. Resume
`experiments/results/cnf-child-stream/checkpoint.json`: 22,036 native keys and
384 additional composed records, preserving every previous result.


[Check restricted children before acquiring guards](research/child-admission.md).
Eighteen equal-state controls repair case 144's 11-row route to three rows while
retaining the two-row solutions in 167/190. The strict gate also loses useful
43/172 savings and adds rejected-probe work, so it stays optional pending another
excluded stream. All 1,076 tests pass. Resume
`experiments/results/cnf-child-admission/checkpoint.json`: the unchanged 21,801-key
native archive and 18 additional composed records, with all earlier results kept.


[Test local discovery on new queries and isolate its regression](research/local-guard.md).
On **192 new neighbouring CNFs**, native rows stay at 250: seven fewer expansion
calls are replaced by seven trace publications. Native bytes fall slightly,
while propagation, serialized records and observed complete time increase.
Fresh case 144 accounts for **10/12 remaining child expansions**; screening its
restricted child before guard acquisition is the next target. All **1,069 tests**
pass. Resume `experiments/results/cnf-local-guard/checkpoint.json` (**21,801 native
keys**, all previous results preserved). The policy remains optional.

[Price single-assumption guards and identify local discovery candidates](research/assumption-guard.md).
Historical cases reduce native rows **23 -> 20** and native bytes **17%**, but
propagation visits rise **31%** and serialized records grow **11%**. Case 70
regresses. Retained traces avoid duplicate premise propagation; they store the
same proofs as direct acquisition. Bounded target-local discovery finds new
guards whose child costs are next to measure. All **1,064 tests** pass. Resume
`experiments/results/cnf-assumption-guard/checkpoint.json` (**21,528 native keys**,
all previous results preserved). No fresh-coverage or stable total-speed claim.

[Separate cofactor reuse from branch-choice gains](research/conditioned-core.md).
Fifteen historical controls show a case-43 partition reducing proof rows
**10 -> 7**, but acquiring a separate cofactor adds cost without saving branch
solving. Regressions are retained. A checked read-only probe finds a narrower
single-assumption guard for all three cases; remaining child acquisition is the
next measurement. All **1,057 tests** pass. Resume
`experiments/results/cnf-conditioned-core-exposed/checkpoint.json` (**21,525 native
keys**, all earlier payloads and sidecars preserved). No fresh-coverage or stable
total-runtime gain is claimed.

[Reuse terminal targets before partition discovery](research/terminal-first-screen.md).
The saved regression now uses **one proof row instead of three**, with propagation
visits **5,289 -> 1,110**; nonterminal controls preserve their exact proofs.
The next gap is matching stored cores after accepted guards: conditioning exposes
two-clause gaps in cases 43/172, responsible for 19/26 remaining expansions.
These candidates still need a measured acquisition/recomposition comparison.
All **1,047 tests** pass. Resume
`experiments/results/cnf-terminal-first-complete/checkpoint.json` (**21,482 native
keys**, existing archive reused, all results preserved).

[Screen partition plans and reuse their unit traces](research/partition-screen.md).
Historical controls reduce new proof rows **41 -> 23**, but fresh case 176 exposes
a regression: repartitioning a target already refuted by unit propagation adds
two rows. Keep the selector optional. Next, reuse terminal unsplit traces and
inspect cases 43/172, which hold **19/26 remaining expansions** after an extra
guard. All **1,042 tests** and independent replay pass. Resume
`experiments/results/cnf-partition-screen/expanded-checkpoint.json` (**21,482 native
keys**; prior results and all new sidecars retained). No stable total-speed claim.

[Compose exact multiple-clause partitions and retain their regressions](research/clause-partition.md).
On historical case 68, the best tested partition reduces expansions **27 -> 11**;
case 6 improves **7 -> 3**, while both case-135 plans regress. Trying every candidate
costs more than the baselines, so the next task is cheaper plan screening using
checked propagation traces. All **1,035 tests** and independent replay pass.
Resume `experiments/results/cnf-clause-partition/checkpoint.json` (**21,225 native
keys** plus checked partition sidecars; all previous results preserved). No fresh
coverage or stable total-runtime gain is claimed.

[Reuse checked premises and test fresh guard-chain coverage](research/premise-guard.md).
On **192 new queries**, expansions fall **139 -> 67** and new proof rows **436 ->
364**. Prepared matching and premise-first checks reduce additional verified
nodes **247 -> 102** versus the previous chain policy. Complete timings remain
variable, and larger chain records increase retained trial bytes 0.414% versus
ordinary solving. All **1,028 tests** and independent replay pass. Next, cover
multiple missing clauses exactly; the largest remaining case costs 27 expansions.
Resume `experiments/results/cnf-premise-guard/checkpoint.json` (**21,128 keys**
plus bound chain records; previous results preserved).

[Compose checked restrictions and price the remaining solve](research/guard-chain.md).
On eight historical cases, expansions fall **68 -> 29**, added native proof
payload falls **57.72%**, and deltas plus chain records shrink **13.47%**. Added
recognition/checking outweighs child-solve time saved; no total runtime gain is
established. All **1,022 tests** and independent replay pass. Next, avoid duplicate
premise checking and test fresh inputs. Resume
`experiments/results/cnf-guard-chain/checkpoint.json` (**20,666 native keys** plus
eight checked chain conclusions); composed reuse requires its bound sidecars.

[Test terminal admission and locate the remaining matching gap](research/terminal-guard.md).
The optional filter adds no hits on 192 fresh queries: both policies use 68
expansions. Historical controls pass. Cases 56 and 176 account for 41 expansions;
checked near-supports justify smaller residuals, whose composition and cost are
the next test. No total speedup is established. Resume
`experiments/results/cnf-terminal-guard/checkpoint.json` (20,649 keys).

[Price pending guard proofs before using them](research/pending-guard-costs.md).
Historical probes identify a terminal-conflict case needing **two proof rows
instead of six fresh expansions**, with **84.10% less added payload**. Other
pending alternatives cost more than fresh solving. All results are preserved;
resume `experiments/results/cnf-pending-guards/checkpoint.json` (20,340 keys).
Fresh-query evaluation of a terminal-origin filter is the next target.

[Choose another checked guard before fresh solving](research/alternative-guard.md).
On 192 fresh queries, one extra reusable residual reduces expansions **142 ->
135** and new proof rows **362 -> 356**. Mean total time is 1.30% higher with
large paired variation; a runtime or memory win is not established. Frozen-worker
parity, historical regression and all **518 tests** pass. Next, price pending
alternative proofs against the work they might avoid.
Resume `experiments/results/cnf-alternative-guard/checkpoint.json`
(20,270 preserved keys); the selector remains an optional policy.

[Acquire causal supports incrementally and retain the failed coverage test](research/incremental-causal.md).
Incremental extraction matches full reconstruction with **68.15% fewer support
visits**, but its 27 additional retained supports give **no new hits** on fresh
queries and increase mean complete time **4.89%**. Keep acquisition optional.
A read-only probe identifies an alternative checked guard for case 121 that
could avoid 20 local expansions; matched policy costs remain to be tested.
All **510 tests** and independent complete replay pass.
Resume `experiments/results/cnf-incremental-causal/checkpoint.json`
(19,907 preserved keys); the enlarged bank remains optional.

[Choose a checked available proof before deriving another support](research/proof-choice.md).
Combining the acquired frontiers preserves causal coverage while reducing proof
materialization **58.39%** and new proof rows **22.79%** on 192 fresh queries.
Mean complete time improves **10.78% versus causal-only reuse**, with mixed paired
timing signs, while peak RSS rises **5.53%**. The next coverage target is
incremental discovery from new negative outcomes and seven remaining residuals.
All **502 tests** pass; the combined policy remains an explicit memory/runtime
tradeoff rather than a minimum-cost claim.
Resume `experiments/results/cnf-proof-choice/checkpoint.json` (19,543 preserved
keys); independent complete replay and inherited-result validation pass.

[Reuse the acquired causal frontier without rediscovery](research/retained-causal.md).
Loading reduces complete time **16.56% versus rebuilding**, with identical proof
archives and full cold audit. It uses **22.5% fewer expansions** than the loaded
legacy frontier, but total time is effectively flat and peak memory is higher.
The next target is choosing cheaper existing proofs where both banks match;
smaller supports currently cause extra derivation. All **492 tests** and complete
archive replay pass. Resume `experiments/results/cnf-retained-causal/checkpoint.json`
(19,091 preserved keys).

[Remove unused propagation dependencies from refutations](research/causal-support.md).
Causal supports cover nine additional negative targets, cutting fresh expansions
**48.72% (195 -> 100)** and query time **27.04%**. Rebuilding old supports still
increases complete runtime **15.87%**, and smaller supports require more proof
rows. The next cost target is loading the acquired causal frontier without
re-extraction. All **486 tests** and complete archive replay pass; broad
cross-guard coverage remains open. Resume
`experiments/results/cnf-causal-support/checkpoint.json` (18,672 preserved keys).

[Explore SAT witnesses without confusing lookup compression with cheap discovery](research/witness-signatures.md).
Bounded flips reach two hard historical SAT targets, but give **no extra transfers**
on the next 192 queries and increase complete runtime **6.04%**. Keep exploration
optional. Equal falsified-clause signatures preserve lookup, but a checked
counterexample shows that they do not preserve flip transitions. All **473 tests**
pass. The next coverage target is shared negative cofactors: all **214 remaining
expansions** in this stream are UNSAT cases, with template 6 contributing 94.
Resume `experiments/results/cnf-witness-signatures/checkpoint.json` (17,947
preserved keys); the positive bank remains optional. Complete archive replay passes.

[Check matched proofs while retaining the complete audit](research/active-support.md).
Demand-driven checks reduce total runtime **10.02% versus eager extension** and
**6.85% versus the loaded-index control**, with identical search work and a full
cold provenance audit charged in every mode. Growing the index **151 -> 170**
adds no coverage on this stream. All **461 tests** and 3,456 independent trial
replays pass. Resume `experiments/results/cnf-active-support/checkpoint.json`
(17,532 preserved keys). Unresolved template-12 residuals are the next coverage target.

[Incremental support discovery](research/incremental-support.md) extends the saved
frontier **104 -> 151 entries** and covers four additional targets on a new stream,
cutting expansions **199 -> 162**. It visits **57.87% fewer extraction nodes** than
full rediscovery, but complete runtime is almost unchanged and remains **4.12%
higher than loading the ready bank**. Repeated evidence checking is the next cost
target. All **451 tests** pass; proposals remain unproved until checked materialization.
Resume `experiments/results/cnf-incremental-support/checkpoint.json` (17,161 preserved keys).

[Construct support proofs only after a match](research/deferred-support.md).
On a new 192-input stream, this preserves all 23 transfers while cutting support
construction **1,310 -> 209 proof rows**. Complete runtime falls **9.96% against
eager construction**, but remains **9.21% above the old-bank control**. Discovery
still outweighs the query savings, so the mode remains optional. All **442 tests**
and 3,456 independent trial replays pass. Resume
`experiments/results/cnf-deferred-support/checkpoint.json` (16,760 preserved keys).
The existing ready bank remains available; this measures construction on matched
historical clones, not rebuilding an already-paid bank.

[Checked cofactor supports extend refutation reuse](research/cofactor-support.md).
On a further 192 unseen constructed inputs, 16 new transfers cut fresh expansions
**30.77%** and query time **34.06%**, but preparing the whole bank increases total
runtime **23.01%** and peak RSS **9.23%**. This remains optional. Only 118 of 1,310
preparation nodes are needed by this stream; constructing proofs only on a match
is the next test. All **434 tests** and 3,072 independent cold trial replays pass.
The bank and all outcomes persist in
`experiments/results/cnf-cofactor-support/checkpoint.json`.

[One census per cold proof snapshot](research/snapshot-replay.md) cuts complete
runtime **48.19%** and cold replay **70.03%** on a further 192 unseen constructed
inputs. Every proof check remains, and both modes have identical archives and
search counts. Peak RSS rises **0.39%**. All **426 tests** and 3,072 independent
cold trial replays pass. The union retains 14,630 keys. Next structural target:
shared refutations among the 37 negative queries that still need fresh search.
Current checkpoint: `experiments/results/cnf-snapshot-replay/checkpoint.json`.

[Exact insertion deltas avoid repeated archive scans](research/incremental-archive-accounting.md).
On the next 192 unseen double deletions, complete runtime falls **60.48%** and
query time **94.26%**, with identical proof rows and search counts. Peak RSS rises
**9.56%**, so this is a time improvement with a memory regression. All **418 tests**
and 3,456 cold trial query replays pass. The retained union has 14,208 reference
keys. Next: remove repeated size scans from immutable cold replay while retaining
all certificate checks, and inspect shared proofs in the 55 guarded negative
queries. Current checkpoint: `experiments/results/cnf-incremental-archive/checkpoint.json`.

[Checked UNSAT supports expose an accounting bottleneck](research/unsat-support-reuse.md).
On 192 unseen double deletions, the full core bank cuts fresh expansions **32.25%**
but increases complete runtime **40.16%** and peak RSS **28.15%**. This remains an
optional experiment. A warm profile attributes **84.55%** of loop time to full
archive scans; exact incremental accounting is next. All **403 tests** and
3,456 cold trial query replays pass. Current checkpoint:
`experiments/results/cnf-unsat-support/checkpoint.json`.

[Bounded model rotation extends reuse to unseen deletions](research/model-rotation.md).
On 257 previously uncached constructed inputs, rotation reduces fresh expansions
**1,876 -> 1,509**, complete runtime **7.16%**, and peak RSS **3.86%** against the
guarded control. All **394 tests** and 4,626 cold query replays pass. The durable
union preserves 9,104 reference keys. UNSAT queries now account for **80.58%** of
remaining expansions; extracting reusable negative proof supports is next.
Current checkpoint: `experiments/results/cnf-model-rotation/checkpoint.json`.

[Checked SAT witnesses avoid fresh clause-deletion search](research/clause-witness-reuse.md).
Compared with the UNSAT guard, fresh reference expansions fall **427 -> 59**,
plus six stored answer certificates; complete time falls **50.39%** on the same
twelve constructed edits. All **388 tests** and cold replay pass. Earlier results
remain retained in a 1,169-key reference union. Two additional checked witness
proposals identify previously unseen deletions for the next discovery experiment.

[A checked UNSAT proof narrows clause-deletion search](research/clause-deletion-guard.md).
On twelve constructed edits, the optional decision wrapper reduces new reference
nodes **502 -> 427** and measured complete time **8.11%**. Case 13 does not improve;
two other cases supply most gains. All **382 tests** and cold replay pass.
Structural coverage stays **17/24**. Next: reuse retained SAT witnesses, which
already satisfy the edited inputs responsible for most remaining search.

[Saved subproofs transfer across new inputs](research/join-transfer.md): on 24
constructed CNFs, preloading exact joins avoids **35 pattern acquisitions and
154 probes**, with identical structural proofs. Whole runtime falls only 0.99%
in two paired runs, while storage rises slightly. Edited controls gain no
acquisition saving and now dominate the remaining work. **376 tests** and cold
replay pass; original-corpus coverage remains **17/24**. Current checkpoint:
`experiments/results/cnf-join-transfer/checkpoint.json`.

[Case-10 transfer exposes exact nonterminal joins](research/progress-transfer.md),
raising structural coverage **16/24 -> 17/24**. The gate costs more than immediate
commitment, but the different proofs rejoin at **four formulas and share 39 new
proof nodes**. Their subproof is independently checked; **372 tests** pass.
Next: test these saved joins on related inputs whose complete answer is not
already cached, charging recognition and verification.

[A progress gate for exploratory trials](research/progress-pilot.md) closes
connected case 21, raising structural coverage **15/24 -> 16/24**. It matches
immediate commitment's proof and storage while using **25% fewer new patterns
and 43% fewer probes** than always trying two routes. Whole-runtime comparisons
remain inconclusive; the gate stays optional. All **372 tests** pass. Next:
test whether early progress can conceal an expensive continuation on case 10.

[Transferring the pilot unchanged](research/pilot-transfer.md) closes case 13,
raising structural coverage **14/24 -> 15/24**, but exposes a regression: the
pilot adds **37% more patterns and 40% more probes for the same proof**. Local
expansion takes 37% longer; paired whole-runtime results disagree. All **367
tests** and independent archive replay pass. The next gap is deciding when a
second trial is worth acquiring, tested on the next connected mixture.

[A bounded pilot across saved routes](research/pilot-refinement.md) closes case 11,
raising coverage **13/24 -> 14/24**. Including both trials, new patterns fall
**44 -> 19**, probes **178 -> 77**, and local expansion time **59.31%**. Whole-stream
time falls **4.64%** and peak memory **1.52%**; full verification still dominates.
All **367 tests** pass. The policy stays optional; the transfer result above and
earlier failed lookahead experiments remain preserved.

[Testing the value of saved splits](research/saved-split-reuse.md) closes case 6,
raising coverage **12/24 -> 13/24**, and exposes a selection counterexample:
the preferred saved route needs **74 new patterns / 547 probes**, versus **63 /
345** when the isolated control reconstructs its source split. Both proofs and
all exploratory work are retained; **363 tests** pass. A smaller visible frontier
does not guarantee cheaper expansion. Next: downstream cost prediction on case 11.

[Checked canonical form in complete cold auditing](research/canonical-cold-audit.md)
closes case 19, raising coverage **11/24 -> 12/24**. Four paired runs reduce the
full audit **4.23%** and whole-stream time **3.81%**, with identical acquisitions,
proofs and snapshots. Peak RSS rises **0.153%**; storage is unchanged. All **360
tests** pass. The next discovery target is case 6, where one saved branch is
already covered and can be reused while investigating its unfinished sibling.

[Sharing full audits across three queries](research/grouped-checkpoints.md)
raises coverage **8/24 -> 11/24** and reduces measured sequence time
**24.14 -> 11.65 seconds (51.72%)**. Each positive query proof is checked separately;
complete archive validation moves to group end. Acquisitions and snapshots match,
while mean peak RSS rises **7.70%**. All **356 tests** pass. Cross-query reuse of
new components remains unobserved; case 19 is the next discovery target.

[Checking only the reachable split graph](research/scoped-refinement.md) closes
case 22 and raises coverage **7/24 -> 8/24**. Complete measured time falls
**12.60 -> 6.95 seconds (44.85%)**, with identical acquisitions and proofs and a
full cold audit in both modes. All **351 tests** pass. Persistent storage is
unchanged; the optional live view avoids checking unrelated history twice.
Next: the connected case-23 mixture and amortizing full checkpoint checks.

[Policy transfer with a history control](research/case17-policy-transfer.md)
closes the next 60-variable residual and raises coverage **6/24 -> 7/24**.
Both histories acquire the same 89 patterns using 531 probes; none of the
case-16 additions contributes to the new proof. Complete-history loading and
checking dominate the measured cost. All **345 tests** pass and every result
remains preserved. Next: the unresolved case-22 mixture and selective checked
access to the growing archive.

[Nested conditional refinement](research/nested-conditioning-discovery.md) closes
the 59-variable frontier and raises current coverage **5/24 -> 6/24**. Trying all
59 first-level pivots leaves it uncovered under the same recognizer. The successful
proof has 12 conditional nodes and depth five, interleaved with 265 checked
reductions. All **345 tests** pass; both workflows remain preserved.

[Incremental split checking](research/incremental-split-checking.md) reduces mean
query time **7.413 -> 4.264 seconds** on the same 24-input enumeration stream.
Database bytes, proofs and **5/24** coverage are unchanged; live cache metadata is
additional. All **341 tests** pass. The next discovery target is an uncovered
59-variable residual whose four saved splits are already fully acquired.

[Broader conditioning candidates](research/bootstrap-conditioning.md) now cover
5/24 inputs versus ordinary depth one's 4/24 in a supplemental comparison.
Enumeration uses fewer probes and stored patterns, but takes longer. Profiling
identifies repeated split verification as the next reuse target; all **335 tests**
pass and all alternatives are preserved.

[The new-input lookahead test](research/lookahead-bank.md) preserves a useful
negative result: checked evidence avoids repeated probes, but this score adds
work and no coverage. Most depth-zero residuals lack saved pairs altogether.
Candidate acquisition is the next target; all **331 tests** pass.

[A saved conditioning pair completes the 42-input stream](research/transfer-split-selection.md).
The winning split needs 13 new records and 30 probes, but the current size-based
ranking misses it. All four alternatives are preserved. The next discovery target
is predicting useful propagation cascades; all **327 tests** pass.

[The complete admission audit](research/complete-admission-frontier.md) avoids
40 additional probes with the same stored graph. A generous allowance still
leaves a connected **38-variable residual**, now preserved as the next structural
target. Interrupted profile work is the next reuse candidate; all **323 tests**
and sixteen archive checks pass.

[The new-input transfer control](research/subsumption-transfer-controls.md) finds a
simpler improvement: expose existing families before probing. On a 42-input
constructed stream, fresh probes fall **1,022 -> 503** and working SQLite size
**2.51 -> 1.47 MB**, with coverage unchanged at **41/42**. The tested shared core
reduces to 2-CNF, so these gains do not establish nonterminal proof reuse. A new
48-variable random case dominates the remaining cost; the analysis also corrects
the scope of the inherited admission counter.

[The full historical corpus now has checked coverage](research/full-corpus-coverage.md):
**1,497/1,497 inputs**, including **985/985 non-tiny cases**, with no new acquisition.
A source-bound policy union replays from an **11.27 MB compressed bundle** in
**11.23 seconds** versus **46.49 seconds** with history restoration. These are
prepared-proof replay costs on development data. Next: test whether larger shared
edit-family components reduce acquisition on unseen inputs.

[The retained development subset is complete](research/case1196-completion.md):
structural coverage reaches **83/83**, with **144 new records** in the final six-batch
sequence. Both repetitions and independent replay agree. Mean sequence time is
**77.64 seconds**, including **3.20 seconds** local expansion.
Next: combined-policy full-corpus checking and transfer to new unlabelled inputs.
This finite result does not establish an efficient solution of arbitrary SAT.

[Completing retained branches across three originals](research/case1063-discovery.md)
raises structural coverage **75/83 -> 78/83** with **54 new records**. Case 1063
completes with only three additional records after fifty had been stored. Four
batches take **71.68 seconds**, including **1.01 seconds** local expansion.
Case 1196 is next; five originals remain uncovered.

[Mixed-family discovery and the remaining frontier](research/case1121-discovery.md)
raises structural coverage **73/83 -> 75/83**, closing cases 1121 and 1336 with
**67 new records**. A small affine projection is checked exhaustively. Four batches
take **72.02 seconds**, including **1.24 seconds** local expansion.
Case 1063 retains a pending branch with no new admissions even though every admitted input is stored.

[Completing the pending mixed reductions](research/pending-discovery-closure.md)
raises structural coverage **72/83 -> 73/83**, completing case 1062 with **68 new
records**, including three polarity transformations into Horn formulas. All eight
previously interrupted inputs are completed. Four batches take **70.46 seconds**,
including **0.85 seconds** local expansion; case 1121 is next.

[Materializing a checked checkpoint](research/materialized-checkpoint-reuse.md)
reduces measured reconstruction plus complete startup **220.33 ->
74.76 seconds (66.07%)**, with identical databases,
evidence and pending selection. The optional cache adds **87,337,082 bytes**; its
construction cost is charged separately. Structural coverage remains **72/83**.

[Discovery across retained original scopes](research/retained-discovery-sequence.md)
raises structural coverage to **72/83**, covering cases 1406 and 1195 and
preserving the partial expansion of case 1062. Four batches share one checked
startup, store **63 records**, and take **73.48 seconds** in total, including
**1.02 seconds** local expansion. Eight interrupted inputs and a pending
19-variable split remain explicit; cold checking is still the dominant cost.

[Conditional refutation with a shared terminal](research/conditional-refutation-reuse.md)
raises structural coverage to **70/83**, closing case 1227 with **five new probe
records** and one shared contradiction terminal. Local expansion takes about
**0.16 seconds**, while cold startup still costs about **66.68 seconds**.
Structural storage grows **73,728 bytes**; separate reference evidence grows
by 380 nodes. Case 1406 is the next discovery target.

[Retaining checked evidence through checkpoint replay](research/checked-checkpoint-replay.md)
reduces the measured five-checkpoint replay and startup **94.29 -> 87.71 seconds
(6.99%)**, avoiding **4,739 repeated node verifications**. Stored evidence and
coverage remain unchanged at **69/83**; case 1227 is the next discovery target.

[Reusing checked canonical source order](research/checked-canonical-sources.md)
raises structural coverage to **69/83**, completing case 1190 with **25 new
records**. Avoiding repeated sorting and renaming after a complete form check
reduces the measured startup-and-expansion sequence **71.96 -> 68.45 seconds
(4.87%)**, with identical stored evidence and no added cache. Cold checking
remains the larger cost; the next selected original is case 1227.

[Testing expansion without batch-seed copies](research/expansion-without-batch-copy.md)
stores **82 new pattern records**, including Horn/zero-valid and 2-CNF terminals.
Coverage remains **68/83**, with a pending split at **26 variables**. Avoiding
3.12 GB of logical copies makes the measured complete sequence **3.39% slower**;
the copied-seed default remains. The saved result distinguishes a slow first
digest from later warm batches and preserves the next discovery checkpoint.

[Reusing the maintained route catalog in global queries](research/maintained-global-catalog.md)
reduces the measured warm query **1.526 -> 0.237 seconds (84.46%)**.
The complete short sequence is slightly slower because startup checking varies;
no total-cost improvement is established. Fresh expansion stores **27 patterns**,
closing a residual through contradiction and Horn/zero-valid branches. Original
coverage remains **68/83**; the next selected focus belongs to case 1190.

[Separating cold global checking from indexed navigation](research/indexed-original-navigation.md)
reduces the measured two-query sequence **138.45 -> 75.96 seconds**
by retaining the checked inventory. The optional graph index preserves exact
selection but shows mixed total-cost results. This replays the saved expansion;
coverage remains **68/83**, with no new acquisition.

[Carrying checked state across original cases](research/original-session-handoff.md)
closes case 1061 and raises coverage to **68/83** with **six new probe patterns**.
Retaining the session reduces the measured query-and-expansion sequence from
**18.99 to 11.61 seconds (38.87%)**, including initial construction and binding
to the next original. Both methods store identical evidence; retention keeps
more checked objects in memory. That comparison identified global checking as
the next large cost.

[Live digest scans and the next completed original](research/guarded-table-digests.md)
raise structural coverage to **67/83**, storing **32 patterns**. Reading the live
database reduces observed worker time by **32.6%** against scanning its copy.
A separate cache of unchanged table hashes shows no average benefit after an
append; its regression is retained. Checked-session startup and global coverage
are now the larger measured costs.

[Following reductions across different SAT classes](research/reduction-reuse-profile.md)
stores **35 patterns** and completes a conditional pair through a zero-valid
terminal and a 2-CNF terminal. Coverage remains **66/83**. Profiling identifies
full-table digest rescanning as the main remaining second-batch preparation
cost; this diagnosis establishes no new speedup.

[Checking signed-renaming reuse before expansion](research/signed-renaming-filter.md)
excludes all **496 pairs** among the next 32 candidate targets using clause widths
and occurrence counts. Matching shapes were insufficient. The unchanged expansion
then stores **54 patterns** and reaches a five-variable Horn terminal; coverage
remains **66/83**, with another conditional pair pending. The audit takes **0.036
seconds** including writing; it establishes no comparative speedup.

[Completing the retained conditional interaction](research/session-frontier-closure.md)
stores **29 patterns** and reaches a seven-variable all-true terminal while
reusing the other branch's refutation. All saved split obligations close, but
original-input coverage remains **66/83**. The global navigator moves to case
1120; completing a local subproblem does not certify its entire original input.

[Keeping checked state between expansion batches](research/retained-expansion-session.md)
reduces mean time for two complete workers **30.61%**, from **23.33 to 16.19
seconds**, including initial checking. Both methods enter the same 64 states
across two budgets and store **44 patterns**, including two conditional Horn
terminals. Coverage remains **66/83**. A live session avoids repeated catalog
verification; cold reconstruction and persistent storage do not shrink.

[Exporting only appended evidence](research/append-delta-export.md) reduces
mean complete-worker time **24.34%**, from **13.11 to 9.92 seconds**, with
identical search and delta bytes on the matched bounded expansion. It adds
**21 patterns** and reaches a conditional all-true terminal outside Horn,
dual-Horn and 2-CNF. Coverage stays **66/83**; both targets of the next split
remain pending. Checked startup now dominates warm cost; storage is unchanged
between export methods.

[Continuing the conditional frontier](research/conditional-frontier-resumption.md)
reaches another checked Horn branch and retains **19 new patterns**. Coverage
remains **66/83**. Thirteen interrupted states expose a persistence gap: bounded
retries need not progress when a recursive chain cannot finish within the
allowance. Preparation and export still dominate the measured worker cost.

[Updating only affected routes after acquisition](research/pattern-activation.md)
reduces observed complete-worker time **14.7%** on the completed historical case
and **20.4%** on the next bounded expansion, with identical search choices and
persistent results. The latter stores **32 new patterns** and exposes another
conditional Horn route, while coverage remains **66/83**. Preparation and export
now dominate the measured worker; the new index does not reduce stored bytes.

[Resuming the exact pending pair](research/pending-pair-resumption.md) closes
case 1154 and raises structural coverage to **66/83**. Thirty new states expose
two conditional routes to Horn formulas; all thirteen previously interrupted
states are now stored. Acquisition takes **0.123 s**, while rebuilding the reuse
catalog takes **2.177 s**, identifying the next substantial runtime target.
Seventeen originals remain structurally uncovered.

[Keeping routes across inactive pending splits](research/pending-split-maintenance.md)
reduces mean bounded-worker time **8.0%** on the interruption control, with
identical operations and stored results. Resuming the saved frontier adds
**19 patterns** and leaves one pending cofactor; coverage remains **65/83**.
The new guard gives no expansion saving when acquisition actually changes the
database.

[Combining the two reuse policies](research/combined-expansion.md) completes the
same cofactor with **9 instead of 20 additional states**, reusing the empty-CNF
terminal on both early branches. The complete original remains structurally
open, so coverage stays **65/83**. The comparison also exposes five interrupted,
unstored recognition states and shows why previous runtime gains cannot simply
be added together. Both paths and the exact pending split are preserved.

[Retaining checked routes after clear probes](research/clear-probe-maintenance.md)
closes case 1263, raising structural coverage to **65/83**. With search choices
and stored results unchanged, complete worker time falls **13.7%** on this case
and **29.6%** on the forcing control. Only clear probe appends can skip a rebuild;
forcing, acquisition and new evidence still refresh the full catalog. This
optional optimization adds a resident snapshot and does not reduce stored state.

[Selecting saved split pairs earlier](research/early-saved-expansion.md) closes
case 1160 and raises structural coverage to **64/83**. On that case, the same
sixteen new patterns take **2 instead of 12 advances**, reducing complete worker
time by **44.3%**. A historical forcing control improves by **24.8%**. Both
policies' results are preserved; the early policy remains optional pending
broader evaluation.

[Acquiring the bounded projection](research/projection-acquisition.md) closes
case 1298, raising structural coverage to **63/83**. The matched ordinary path
closes it too and costs less: **4.45 vs 8.70 seconds**, **8 vs 9 new states**.
Projection adds probe work and route refresh despite removing a variable. Both
alternatives are preserved. This regression makes reuse of existing probe
history and cheaper route maintenance the next priorities.

[Automatic target discovery](research/projection-lookup.md) now recovers the
previous projection bridge without being given its target. It finds **no new
match on the 23 unresolved frontier sources**. Indexed discovery is faster than
scanning a prepared catalog, but construction costs **14.4 s / 28.1 MB**. That
study exposed the **36-variable / 153-clause** projection tested above. Its
coverage was **62/83** before the acquisition comparison.

[Exact projection now connects the two expansion paths](research/projection-bridge.md).
A checked elimination and subsumption step lets both leaves reuse one proof:
**13 instead of 25 new states**, **15.1% less warm expansion time** and **7.0% less
complete worker time**, including discovery. Both modes complete the same two
roots in the matched development comparison. Coverage rises **61/83 -> 62/83**.
All earlier work is retained; the next original has a **37-variable / 151-clause**
selected leaf. Broader discovery of these connections is the next priority.

[A matched split comparison](research/split-cost-1299.md) exposes the current
tradeoff: one choice stores **13 instead of 29 new patterns**, with **45% fewer
compressed delta bytes**, but both take about **12.7 seconds** and leave the
case structurally open. Route refresh consumes **94%** of expansion time; the
smaller arm's complete worker is slightly slower. Both alternatives are retained,
leaving **28- and 29-variable** unresolved leaves. Structural coverage remains
**61/83**. The [priority record](research/structural-reuse-priorities.md) binds the
new resumable checkpoint and the next discovery and maintenance targets.

[A conditional refutation and a zero-valid component](research/transfer-1304.md)
close another development input, raising structural coverage **60/83 -> 61/83**.
A saved split needs **10 new states**: three failed-literal reductions refute one
branch; six reach a formula satisfied by the all-false assignment in the other.
Acquisition and ranking cost **0.201 seconds**, with **106.79 seconds** of initial
reconstruction and checking charged separately. The delta adds **9,914 compressed
bytes**. All **181 relevant tests** and cold replay pass. The next selected
residual has **36 variables / 162 clauses**, supplying the split-ranking
tradeoff tested above.

[Resuming the pending split](research/pending-warm-expansion.md) raises structural
coverage **59/83 -> 60/83**. The true branch reaches a seven-variable Horn
terminal using **20 admissions**, while its closed sibling is reused. Four
unfinished states from the previous run are recomputed and charged again.
Acquisition takes **0.060 seconds**; initial reconstruction and checking still
cost **103.26 seconds**. The delta adds **11,805 compressed bytes** and preserves
all earlier results. All **181 relevant tests** and independent cold replay pass.
The next selected residual has **34 variables / 148 clauses**.

[Early closed-cofactor reuse](research/early-closed-expansion.md) now has a matched
comparison: **22.31% less expansion time** on case 1445, but a **1.64% regression**
on forcing control 1189. Both policies preserve the same pattern records and
proof outcomes. One new branch closes through a six-variable Horn terminal;
the other remains pending at 23 variables under the 32-state allowance. Coverage
stays **59/83**. All **181 relevant tests** and cold replay of all four arms pass.
The [priority record](research/structural-reuse-priorities.md) identifies the exact
pending target and the cost of repeated unsuccessful candidate searches.

[The preceding original-frontier batch](research/original-warm-expansion.md) reduces
another open residual from **33 to 29 variables**, using **7/32 admissions**.
Two splits reuse the same earlier empty-CNF terminal; overall coverage stays
**59/83**. The next opportunity is to use these known closed cofactors earlier:
seven clear probe blocks preceded the selected splits, costing **6.73 seconds**
in route refresh alone. Acquisition took **0.204 seconds**, while full initial
preparation still cost **94.52 seconds**. All **176 relevant tests** pass.

[The preceding discovery batch](research/warm-expansion-batch.md) raises structural
coverage **58/83 -> 59/83**. A forced restriction exposes binary-implication
deletions and variable elimination; a saved split of the remaining 15-variable
source reaches two 2-CNF terminals. The batch uses **21/32 admissions** and retains
all earlier results. Actual discovery takes **0.119 seconds**, with **7.59 seconds**
of route refresh and **91.13 seconds** of initial preparation charged separately.
All **160 relevant tests** pass. The next target is another uncovered original:
the retained split frontier is closed, but 24 original inputs remain uncovered.

[Incremental coverage maintenance](research/incremental-coverage.md) now reuses
the acquired rule graph. Warm composition and checking average **0.261 to 0.039
seconds**, or an indicated **18.47%** saving after including complete route
refresh. Cold replay remains expensive and is slightly slower with the index
(**64.41 versus 62.63 seconds**); the new snapshot also adds storage. All **156
relevant tests** passed at that checkpoint. This motivated the bounded warm
discovery session above, preserving the initial construction cost in the account.

[The latest forced reduction](research/source-local-forcing.md) proves one
frontier variable true and shrinks the open source from **23 variables / 93
clauses to 22 / 88**, using one new recognition state. Coverage remains **58/83**.
The matched local expansion worker takes **0.137 seconds** with history available;
**55.49 seconds of cold global recomposition** was its largest measured cost.
All **148 relevant tests** pass, and the new checkpoint preserves earlier results.

[Source-local expansion](research/source-local-expansion.md) now preserves the
next four ordinary probes while loading only their needed historical premises.
With full authoritative history already available, the matched one-block worker
falls from **11.00 to 0.127 seconds**; initial restoration still costs **20.59
seconds**. Coverage remains **58/83**. Resume from the checked source-local
checkpoint named in the [priority record](research/structural-reuse-priorities.md).

The latest [probe-and-split continuation](research/exhausted-probe-split.md)
raises structural coverage **57/83 -> 58/83**. The last ordinary probe is clear;
ranking its retained cofactor pairs then completes the ten-variable residual.
One branch reuses the empty-CNF terminal, while seven new recognition states
reduce the other to Horn form. Both checked plans close the original 48-variable,
204-clause development case. All earlier evidence remains retained.

The preceding [affine/one-clause investigation](research/affine-one-clause.md)
raises structural coverage **56/83 -> 57/83** on the reused development set.
Checked linear algebra closes a case missed by shallow probes, without expanding
the affine relation into CNF or changing the historical inventory. The positive
proof is 1,056 compressed bytes; 21 targeted tests and cold replay validate it.
All 28 remaining selected leaves lack directly recognized parity equations.
The [priority record](research/structural-reuse-priorities.md) identifies the next
discovery and verification gaps. No unrestricted-SAT complexity claim follows.

The earlier [saved-cofactor investigation](research/saved-trace-splitting.md)
raises structural coverage **52/83 -> 53/83** and independently proves the new
32-variable original SAT. A checked split reuses two clear assumption traces,
requires both cofactor plans and adds five pattern nodes. All **581 tests** pass.
The local timing control shows no replay speedup; cold checking still dominates.
Four acquired open targets remain for bounded cofactor reuse and comparison
against further probing.

The preceding [retained-learning investigation](research/retained-learning-batch.md)
raises structural coverage **47/83 -> 52/83** on the reused development originals;
all five gains are independently SAT. It reuses saved clauses and prefixes,
adds 141 later blocks and 77 pattern nodes, and preserves all older evidence.
Six successful augmented blocks have clear matched controls; four controls also
find forced values. All **577 tests** pass. Cold validation
still dominates runtime. The next targets are a ten-variable residual with one
untried probe and 18 learned formulas with unused later variables.

The earlier [resumed-probe investigation](research/probe-resumption.md) raises
coverage **39/83 -> 45/83**, with four SAT and two UNSAT gains on reused
48-variable development cases. It also certifies that five remaining sources
have **no single-assumption unit refutation**; more plain single-variable probes
cannot close those sources. Their saved paired traces may still support stronger
common consequences, equivalences or learned implications. All **557 tests** pass,
with previous results preserved. Cold verification remains the dominant cost.

The preceding [prefix-continuation investigation](research/probe-continuation.md)
shares checked probe prefixes and advances bounded discovery. Coverage rises
**36/83 -> 39/83**, with one SAT and two UNSAT gains on reused 48-variable
development cases. The matched warm probe substep is **2.09x faster** than
rediscovering the same prefix; full cold verification still dominates runtime.
All **547 tests** and cold artifact/reference checks pass. The eight-table history
retains all earlier results, 51 new continuation blocks and 45 new proof nodes.
This extends coverage and avoids repeated probing; it is not a whole-SAT speedup.

The preceding [probe-window investigation](research/probe-window.md) finds that the
growth escape first succeeds by promoting an already refutable assumption into
the bounded probe window. Continued probes preserve the original recognizer and
raise selected-original coverage **32/83 -> 36/83**: three SAT gains and one UNSAT
gain, all with 48 variables. Removing the growth-exception route retains all 36
closures. All **543 tests** and cold checks pass. The new 70 window records and
81 proof nodes add work and storage; this is broader coverage, not a speedup claim.

The preceding [growth-escape investigation](research/growth-escape.md) closes the
saved core with one explicitly budgeted three-clause growth step and four new
probing states. A finite checked witness propagates the result through a saved
coupled route, raising selected-original coverage **31/83 -> 32/83**. Removing
the growth edge from the same graph removes the gain. A separate solver confirms
UNSAT for the gained 48-variable original. All **540 Python tests** and cold
artifact checks pass; costs and previous results remain preserved. This is one
development case, not a general SAT speedup or a new full-corpus measurement.

The preceding [coupled-pivot investigation](research/coupled-pivots.md) reuses the
saved divergent routes and adds a cap covering every new recognition state,
including descendants. Its 25 original-input trials add 32 proof nodes but leave
coverage at 31/83. Only one unresolved core is new to the history; all 662 allowed
ordered pivot pairs there grow by at least seven clauses. This identifies a
concrete admission barrier for the next experiment. All **535 Python tests** pass,
and all earlier results and new trials persist. The preceding
[ancestor-selection study](research/frontier-pivots.md) retains the matched early
versus later-node controls.

The preceding [subset-search investigation](research/anchored-subsets.md) preserves
the exact recognition certificates while filtering impossible subsumers by a
required literal. Whole-input caching has zero hits within independent proposal
and checking roles on the retained costly trace. The optional index instead
reduces candidate work within each call; it changes no structural coverage or
stored results. All **521 tests** and the Lean audit of **4,219 declarations /
2,031 theorems** pass. Matched costs and adverse controls are retained in the study.

The next iterations prioritize [SAT pattern discovery](research/sat-pattern-discovery.md):
an exact classification covering all valid CNFs, explicit unresolved cases and
checked decomposition across interacting classes. Known-family optimization
continues as supporting work. Coverage and efficient solution of every class
remain separate obligations.

The [first pattern inventory](experiments/results/cnf-pattern-inventory/README.md)
records overlapping classes, explicit parity encodings and exact component/branch
decompositions. On 152 inputs beyond the exhaustive tiny cases, whole-formula
tests explain 39 and two conditioning levels explain 102. The remaining 50 cases
and all failed alternatives are retained. Analysis currently adds runtime and
memory; it identifies discovery gaps rather than accelerating the SAT engine.

The [affine discovery extension](experiments/results/cnf-affine-patterns/README.md)
extracts complete parity encodings, checks their equations and keeps all leftover
couplings. It closes 14 of those 50 cases; the remaining 36 and observed cost
regressions are preserved. Exact composition across small shared interfaces is
the next discovery target. The ordinary SAT solver is unchanged.

The [projection extension](experiments/results/cnf-affine-projection/README.md)
now implements exact interface reduction and checked model lifting. Six growing
coupled affine controls close without branching; the original 36 open sources
still expose gaps in mixed leftovers. Lean composition lemmas, cost regressions
and encoding-budget failures are preserved alongside the gains.

The [checked simplification study](experiments/results/cnf-simplification/README.md)
now exposes structure through unit propagation and whole-residual pure literals.
It closes all 36 old discovery misses; on the expanded corpus, depth-two coverage
rises from 217/329 to 290/329 beyond tiny exhaustive cases. Units alone reach
289/329 at lower runtime. The remaining 38 random 3-CNFs and one boundary-cap
case are retained. Tests, complete archives and cost regressions accompany the
results; this analysis is still separate from the ordinary decision solver.

The [conditioning comparison](experiments/results/cnf-conditioning/README.md)
finds eight additional closures over unit-only frequency ordering at the same
depth and candidate cap. Its shortest-clause policy costs more time and storage,
and loses five cases relative to combined unit/pure processing, so it remains
optional. The next target is duplicated intermediate state: conditioning and
forced-unit closure currently acquire separate full residuals. All fresh
20/32-variable 3-CNFs remain unresolved in this bounded discovery experiment.

The [fused-edge implementation](experiments/results/cnf-fused-conditioning/README.md)
now stores conditioning and its checked simplification together, preserving every
branching plan and coverage result. On the shortest-clause policy, total measured
time falls from 21.17 to 17.64 s and SQLite from 96.91 to 65.57 MB. Targeted Python
allocation also falls; regressions and measurement limits are retained. This
reduces acquisition overhead while leaving the discovery gap unchanged.

The [checked probing experiment](experiments/results/cnf-failed-literal/README.md)
now uses unit-conflict proofs under an assumption to force its opposite. On
1,025 matched inputs, four-candidate probing raises non-tiny structural closure
from 358/513 to 484/513, including 19/64 -> 51/64 on fresh random formulas.
Total time falls from 27.11 to 18.88 s and SQLite from 93.14 to 65.06 MB.
This is standard failed-literal reasoning in the separate discovery layer;
29 cases remain unresolved. Probing every binary variable closes only two more
and costs more. The next target is common consequences already present in both
inconclusive assumption traces, with their reuse and checking charged.

The [common-consequence study](experiments/results/cnf-common-consequence/README.md)
implements that reuse as an optional necessary-assignment policy. On 1,101
inputs it adds one structural closure (536/589 -> 537/589), with no fresh-random
gain, while time rises 32.12 -> 32.76 s and SQLite 104.44 -> 107.76 MB. The
policy stays optional and the regression is preserved. Smaller selected
residuals trigger additional probing and retained state. The next focused
discovery target is checked signed-equivalence substitution on the selected
unresolved paths where existing probe traces already imply such relations.

The [signed-equivalence study](experiments/results/cnf-probe-equivalence/README.md)
now applies those relations throughout the source and checks signed model lifts.
On 1,137 inputs it adds seven old closures (567/625 -> 574/625 non-tiny), with no
gain on 24 fresh random sources. Total time rises 38.29 -> 39.73 s and SQLite
130.60 -> 135.57 MB, so the policy stays optional. The next target is bounded
local learning from checked one-way implications beyond existing binary paths,
present on selected unresolved paths of 37 remaining source misses.

The [bounded-learning study](experiments/results/cnf-probe-learning/README.md)
now turns saved one-way implications into checked binary clauses for one extra
probe pass. It adds three closures (604/661 -> 607/661), including one fresh
48-variable source, but total time rises 48.18 -> 52.70 s and SQLite 163.53 ->
168.27 MB. The policy stays optional. Changed variable choices explain part of
the gains; added propagation matters for the fresh gain. The next supporting
target is reusing the 10,018 continuation certificates that exactly repeat earlier
ones, while keeping new implications, dependencies and unresolved cases explicit.

The [closure-reuse follow-up](experiments/results/cnf-probe-closure-compact/README.md)
now avoids 14,705 repeated propagations by checking added clauses under saved
unit closures. All 1,209 source plans and 13,066 semantic nodes are preserved.
Coverage stays 634/697 non-tiny inputs. A compact policy tag removes the first
trial's storage regression: total time is 62.76 -> 61.69 s, SQLite 197.10 ->
196.10 MB and cold replay 26.78 -> 25.09 s in single samples. The failed trial
and timing limitations remain recorded. All 348 Python tests and the full Lean
audit pass. The unused implication candidates motivate the following selection
experiment, with selection and changed probe choices charged.

The [bounded-selection study](experiments/results/cnf-learning-selection/README.md)
tests four clauses chosen from up to sixteen proved candidates. It gains one
source closure and loses another: coverage stays **662/733** non-tiny inputs and
**16/24** fresh random inputs. Total time rises **71.42 -> 73.19 s (+2.49%)** and
SQLite **227.39 -> 227.83 MB**, so the policy remains experimental. Saved controls
show that a changed first forced variable can redirect later discovery even when
both local probes succeed. The next experiment freezes continuation choices to
separate this effect from clause strength. All **353 tests**, the full Lean audit
and new/previous archive replays pass; all failed attempts remain preserved.

The [fixed-order control](experiments/results/cnf-learning-fixed-order/README.md)
now shows why retaining the old probe choices is insufficient. Coverage remains
**692/769** on the enlarged corpus, with the same gained and lost source. In the
lost case both policies force the same assignment and leave the same 54-clause
original core, but different redundant learned additions lead to different
subsequent discovery. Fixed order costs **80.72 s versus 77.92 s** for baseline;
it remains optional. Next: separate shared residual cores from checked propagation
hints while retaining each plan's hint context. All **358 tests**, the Lean audit
and cold archive checks pass. This does not establish efficient arbitrary-SAT coverage.

The [parent-scoped core experiment](experiments/results/cnf-learning-core/README.md)
now recovers that loss while retaining the earlier gain: **719/805** non-tiny
inputs close, versus **718/805**, with no lost closures. It uses checked hints
at the parent and gives the child only the original-clause core. The full run
costs **97.83 s versus 94.87 s** for baseline; the pilot's savings do not generalize.
It finds **319 clause occurrences** rediscovered in immediate children across
165 edges, making checked hint transport the next reuse target. No new shared
learned-child cores occur within the full run; broad compression is not measured.
All **366 tests**, the expanded Lean audit and new/previous archive checks pass.
Eighty-six sources remain structurally unresolved; arbitrary-SAT bounds stay open.

The [portable-hint follow-up](experiments/results/cnf-hint-transport/README.md)
translates all **1,005 eligible hint occurrences** into proofs checked directly
against child cores. An extra hint pass gains one local closure among 494 edges,
but increases time and memory. The gain occurs outside selected source paths and
comes from probe choices: the child's existing clauses also suffice with those
choices. This motivated ranking the existing continuation on its core without
adding another pass, tested below. Whole-source coverage in that study remains **719/805**. All **374 tests**, the Lean audit
and new cold archive checks pass; parent-independent proofs and failed cost
experiments remain persistent.

The [core-order trial](experiments/results/cnf-core-order/README.md) tests that
ranking change with the existing batch and probe budget. Across 1,389 queries,
non-tiny closure falls **776 -> 775 / 877**, with no gains and a loss on source
956. Time falls **120.82 -> 116.67 s**, but this single sample and coverage loss
do not justify replacing the existing policy. All **380 tests**, the unchanged
Lean audit and new/previous cold archive checks pass. The next discovery target
combines active core candidates with newly ranked variables: this union fits the
four-variable cap in all 255 gained/lost local states, but can exceed it elsewhere.
The failed ranking rule and its counterexamples remain preserved.

The [activity-guided follow-up](experiments/results/cnf-activity/README.md)
preserves **806/913** non-tiny closures and reduces continuation attempts
**31,741 -> 7,184**. Balanced repeated timing controls do **not** establish a
speedup. Source 977's open residual shrinks to 22 literals. Checked signed
subsumption then exposes seven prospective 2-CNF leaves, which could complete
four current source plans after integration. That is the next discovery target;
those closures are not yet counted. All **388 tests**, the Lean audit and new/
previous cold replay checks pass; failed timing claims and witnesses are preserved.

The [signed-subsumption integration](experiments/results/cnf-signed-subsumption/README.md)
now closes those four sources: **833 -> 837 / 949** non-tiny queries in the expanded
study, with no losses. The broad sample becomes slower and larger; the optional
policy is a coverage improvement, not a demonstrated general speedup. All **395
tests** and three new Lean lemmas pass. The [current priorities](research/structural-reuse-priorities.md)
target futile equal-width comparisons (81% of subset tests), reuse of already
proved implications, repeated propagation/checking and retained state. Eight
further residuals expose 2-CNF in a saved diagnostic; three potential source
closures still require integration. **112 sources** remain structurally unresolved.

The [original-implication follow-up](experiments/results/cnf-implied-subsumption/README.md)
closes five additional sources: **864 -> 869 / 985** non-tiny queries, with no losses.
It reuses existing proofs as subset witnesses and skips futile equal-width tests.
Full-sample time stays near **170 seconds**; logical state and the six-case Python
peak grow. All **403 tests** and the Lean audit pass. The current frontier has
**116 open sources** in the enlarged corpus. Repeated restriction/proof checking
remains the main profiled cost; an offline relevance filter removes 75% of saved
implication candidates while retaining the observed exposures, but adds no new
frontier coverage and has not yet been integrated or timed end to end.

The [bounded proof-check cache](experiments/results/cnf-checked-probe-reuse/README.md)
then preserves every result and database byte while reducing full-sample time
**168.31 -> 150.39 seconds** and cold replay **71.60 -> 62.59 seconds**. Repeated
selected controls also improve. The six-case Python peak rises by **1.10 MB**;
the cache is capped at 1 MiB of serialized strings, with other memory charged
separately. All **410 tests** pass. First-time propagation now dominates the
profiled remaining work; structural coverage stays **869/985** non-tiny inputs.

The [ordered propagation study](experiments/results/cnf-ordered-propagation/README.md)
reduces discovery from 111.13 to 97.76 seconds while preserving the exact old
proof traces and all archive bytes. Repeated selected-query controls support
about a 10% total-time reduction. Six-case Python peak rises by 216 KB; early
conflicts can regress because index preparation is wasted. All 417 tests pass.
Coverage stays 869/985 non-tiny: broader discovery remains open, while repeated
restriction and residual reconstruction are now the leading measured cost gaps.

The [immutable source-index study](experiments/results/cnf-indexed-restriction/README.md)
then reuses occurrence lists across restrictions and shares unchanged clause
tuples. Two full runs per mode average **8.36% less discovery time, 4.37% less
total time and 7.30% less cold replay**, with identical proofs and archive bytes.
Six-case Python peak grows **1.60 MB**. The first total-time regression and poor
reuse on newly allocated/edited sources are preserved. All **425 tests** pass;
independent simplification reconstruction is now the leading measured cost gap,
and structural coverage remains unchanged.

The [one-pass checking follow-up](experiments/results/cnf-single-pass-check/README.md)
shares untouched clause tuples while independently reconstructing residuals in
one pass. Full discovery improves **6.60%**, total **5.62%**; cold replay regresses
**1.07%**, and measured peak memory is essentially unchanged. All **433 tests**
pass, with identical archive bytes. The rejected clause-support caches and wide
clause regressions are preserved. A separate checked probe identifies **35 of
148 unresolved leaves** that become Horn after variable polarity changes; integrating
these certificates and measuring root coverage was the next discovery priority.

The [checked Horn-renaming integration](experiments/results/cnf-polarity-horn/README.md)
now closes all 35 saved leaves and **29 additional complete inputs**: non-tiny
structural coverage rises **869/985 -> 898/985**, with no lost closures. None of
the new gains admits a whole-source renaming; exposed residuals compose through
the existing decomposition. Single-run discovery falls **4.95%**, fresh SQLite
**4.63%** and six-case Python peak **15.73%**; warm replay regresses. Earlier
archives remain retained, so this is not a historical-storage reduction. All
**441 tests** and the Lean axiom audit pass. The **87 remaining sources / 106
leaves** now have checked renaming exclusions. Their auxiliary conflict paths
provide the next concrete target for interface and conditioning discovery.

The [obstruction-guided conditioning test](experiments/results/cnf-obstruction-frontier/README.md)
then checks whether those exclusions improve split selection. At the same budgets,
one extra level closes **60/106 frontier leaves** with the current ranking and
**57/106** with the new rule. Its three gains, six losses, higher discovery time
and larger archive are retained; the rule stays optional. Five lost winning
variables lie outside the recorded obstruction. Saved probe proofs expose an
indirect propagation effect in one case, giving a concrete next reuse target.
All **448 tests** pass. Original-source coverage remains **898/985**.

The [saved-probe ordering test](experiments/results/cnf-probe-rank-frontier/README.md)
keeps every baseline candidate and reuses original proofs to change only order.
Coverage is preserved, but two reversed-order runs regress in mean discovery
**4.82%**; the policy is not promoted. The [96 fresh controls](experiments/results/cnf-probe-rank-fresh/README.md)
change no order: **36/39 branching states have no binary clauses**, leaving most
candidates without unit-probe evidence. Bounded multi-variable interactions and
portable successful plans are the next targets. Two Lean lemmas capture the
local coverage condition; all **453 Python tests** pass. Original-source coverage
remains **898/985**.

The [binary-path extension](research/binary-paths.md) removes wide clauses entailed
by retained binary reasons. Full structural coverage becomes **901/985** (four
gains, one bounded-search loss), but discovery rises **19.06%** and fresh archive
size **13.93%**. It remains optional. The lost case exposes the next reuse gap:
a sound reduction displaces an earlier successful split from a capped candidate
list. Both proof archives remain intact. All **461 Python tests** and the Lean
build/axiom audit pass; four new semantic lemmas justify the deletion rule.

The [retained-plan follow-up](research/retained-plans.md) references old closed
graphs before new acquisition. With the same prepared archive, coverage reaches
**902/985** without lost closures, discovery falls **16.65%**, and added storage
falls **37.36%**. Six-case peak Python allocation rises **19.68%**; fresh-input
coverage is unchanged and slightly slower, so the method remains optional.
All **469 tests** and the unchanged Lean audit pass. At that checkpoint, the next measured cost was a
full residual-storage census repeated after every solver query, including hits.

The optional [archive-accounting follow-up](research/residual-accounting.md)
maintains exact totals transactionally. On the same prepared 1,497 inputs, query
time falls **171.12 -> 87.88 seconds (48.64%)**, with identical search, coverage
and stored evidence. Initialization includes one full census; retained overhead
is **4 KiB**. Empty-history acquisition shows no clear improvement. All **476
tests** and the unchanged Lean audit pass. Discovery now accounts for about **92.6%** of query time; selected
proof reuse and transport beyond exact prepared sources are the next targets.

The optional [prepared-probe follow-up](research/prepared-probes.md) reuses
independently checked traces from old unresolved plans. It avoids 21.63% of fresh
probe attempts on the prepared original corpus, but discovery time changes only
**79.80360 -> 78.51427 s** in one ordered comparison. Evidence and storage remain
identical; coverage stays **902/985**. Fresh-input and empty-history controls reuse
no traces, and the fresh control runs slower. All **481 tests** pass. The
[updated priorities](research/structural-reuse-priorities.md) concentrate on the
83 unresolved sources, which consume about 83% of discovery time.


The [independent reconstruction investigation](research/indexed-check.md) found a
limit to source-identity caching: the 96-input control regressed, and a 32-fold
larger cache left hard-case hits unchanged. A no-eviction audit found 2,167 distinct
CNFs among 2,537 source objects, so exact whole-formula sharing has limited headroom
there. Both unsuccessful candidates and their evidence remain optional; the next
target is checked reuse across related residuals. All **490 tests** and the unchanged
Lean audit pass. No new structural coverage is claimed.

The [clause-sharing follow-up](research/clause-mask-reuse.md) finds about 70%
clause reuse in two costly sources, but a bounded checker mask fails to turn it
into a total-cost benefit. Two 96-input controls cut literal work 55.10% while
total time rises 2.58% and 3.58%, and sampled Python peak rises about 41%.
Evidence and storage match exactly. All **496 tests** pass; the prototype stays
optional and disabled. The next priority is checked variable elimination and
equivalent-core discovery on the unresolved frontier.

The [checked variable-elimination extension](research/variable-elimination.md)
now closes **29 of the 83 previously unresolved original inputs**, compared with
11 for pure-only elimination. It broadens coverage at higher total cost:
**64.77 -> 80.10 seconds**, with a larger retained archive. The candidate remains
optional. All **501 tests** pass, and Lean proves the exact existential projection
identity, with implementation refinement still separate. This subset study does
not rerun the full corpus or establish a polynomial arbitrary-SAT solution.

A [checked subsumption follow-up](research/subsumed-elimination.md) passes all
**506 tests** and adds a Lean omission/projection proof, but yields **no further
closures**: the same 29/83 close, with higher time and storage. It remains
optional. The next measured opportunity is less restrictive growth admission:
**48/59** remaining leaves have a candidate with non-growing clause count and at
most eight extra literals, even without subsumption. Candidate availability is
not a new closure or a general SAT bound.

The [clause-count admission experiment](research/clause-bound-elimination.md)
relaxes the per-step literal limit while retaining complete resolvent checking.
All **511 Python tests** and the **4,195-declaration / 2,018-theorem** Lean audit
pass. Lean bounds one accepted elimination chain: at most n steps, mn literals
per formula and (n+1)mn retained formula slots under explicit normalization
and clause-count premises. It does not guarantee an admissible next step or
bound the full discovery graph. The optional policy closes **31/83** original prior misses versus **29/83**,
at higher time and storage cost, and adds no closures on the repeated 96-input
control. The next measured opportunity is a fixed allowance of one or two extra
clauses: 32/57 remaining leaves need one, and 50/57 at most two. These candidate
counts do not establish new closures or an efficient complete elimination order.

The [additive-growth follow-up](research/additive-elimination.md) implements
checked allowances of one and two extra clauses. All **516 tests** and the
**4,216-declaration / 2,028-theorem** Lean audit pass. Lean bounds one normalized
accepted chain by n steps, m+d*n clauses per state and (n+1)*n*(m+d*n) formula
slots, without guaranteeing a useful next pivot or a small full planner. Neither
budget adds a closure on the 57 saved leaves or the 83 original prior misses:
all original modes close the same **31**, while query time and storage increase.
The new endpoint proofs and models are retained, with their additional storage
charged. These policies remain optional. The next focus is useful endpoint
selection and reuse of failed recognition, not larger growth budgets by default.

The latest [arbitrary-CNF research candidate](research/residual-candidate.md)
combines tractable leaves, residual reuse, and recognized matching constraints.
The [matching experiment](experiments/results/cnf-matching/README.md) reduces a
nine-pigeon/eight-hole case from 5,191 acquired residuals to one checked Hall
certificate. This is a restricted-family improvement in a separate Python
prototype; no uniformly polynomial solution for every CNF has been established.

The [positive-core follow-up](experiments/results/cnf-subsumption/README.md)
removes checked redundant positive supersets and reuses the same stored core
across growing sources. Laminar choices reduce to disjoint minimal choices;
irreducible overlap remains open. The source copies and recognition work are
still charged, even when no new core search is needed.

The [delta-history comparison](experiments/results/cnf-positive-history/README.md)
now stores a fixed base once and keeps witnessed positive additions as parent
references and clause deltas. At 16 holes and 128 redundant additions, logical
storage falls from 10,957,771 to 118,668 bytes. Warm append avoids full-source
rediscovery; cold replay, novel constraints and repeated-event losses remain
explicit in the comparison.

The [decision-history extension](experiments/results/cnf-decision-history/README.md)
now reuses an UNSAT base for arbitrary clause additions, or a stored SAT model
when it still satisfies the new clause. Accepted updates avoid subset discovery
and fresh solving. The comparison retains failed-model fallback, repeated-event
losses and cold-replay costs; the rules do not bound general SAT acquisition.

The [repair-history study](experiments/results/cnf-repair-history/README.md)
adds checked single-variable repairs using persistent occurrence and assignment
indexes. A variable can change only when its opposite literal is absent from
the entire parent source. This avoids 128 fresh-base acquisitions on the measured
fresh-unit stream; blocked repairs, index memory and sparse-name costs remain.

The [affected-clause repair study](experiments/results/cnf-affected-history/README.md)
admits safe changes when both signs occur, using versioned clause counts and
occurrence lists. On the measured size-16 matching history it avoids 128 new
acquisitions, reducing operation time from 3.478 to 0.147 seconds and logical
storage from 12.46 MB to 0.158 MB. Eager indexing can increase memory and cold
replay costs.

The [joint-repair study](experiments/results/cnf-equivalence-history/README.md)
recognizes explicit signed-equivalence blocks and checks simultaneous changes
against all affected clauses, including earlier additions. On 32 blocks of 32
variables, acquisition/update time falls from 2.469 to 0.0668 seconds and logical
storage from 3.79 MB to 0.099 MB. Cold final replay is slightly slower. The
[cost map](research/structural-reuse-priorities.md) tracks the next measured gaps.

The [matching-history study](experiments/results/cnf-matching-history/README.md)
now retains matching endpoints and unit constraints, finds alternating changes,
and validates them with the same joint checker. On 32 blocks of eight choices,
operation time falls from 8.303 to 0.253 seconds and logical payload from 20.33 MB
to 0.424 MB. Over-budget recognized repairs, parity moves, mixed-base discovery
and non-unit coupling conflicts remain explicit gaps. These restricted gains do
not give a uniformly polynomial algorithm for arbitrary CNF.

The [budget comparison](experiments/results/cnf-budgeted-history/README.md)
adds an optional bounded retry for recognized equivalence moves. At 1,024
variables it reduces acquisition/update time from 0.785 to 0.059 seconds and
logical storage from 189,168 to 99,129 bytes. Simply raising the global budget
is slightly faster on these chains and handles dense controls that the targeted
cap misses; neither policy is established as optimal. Profiling identifies
repeated full-source unit propagation as the next large preparation cost.

The current draft is **Bounded-Domain SAT, Compiled Knowledge, and Amortized
Reasoning: A perspective on resource accounting for learned reasoning**.

- [LaTeX source](paper/bounded_domain_sat_and_amortized_reasoning.tex)
- Author: Andreas Maier
- Status: working draft
- Format: self-contained LaTeX with embedded bibliography and TikZ figures

The paper distinguishes the costs of construction, storage, inference, training,
verification, and fallback solving. It examines exact finite-domain SAT tables,
finite restrictions of language classes, oracle simulation, explicit ReLU
representations, nonuniform advice, caching, and certified fallback. System 1 and
System 2 serve as a computational analogy, not as complexity classes.

The expanded draft compares these ideas with neural-advice and speedup-learning
literature, discusses the failed Deolalikar argument and Wen's learned-oracle
claims, and proves conditional expected-savings and bounded-overhead results.
An exact reuse identity states when avoiding repeated solves repays cache costs.
These savings conditions apply whether P = NP or P != NP, and a scaling example
shows how reuse can help even when solving has polynomial cost.
The detailed argument audit makes setup costs explicit in every cache bound,
states the finite-expectation assumptions for unbounded query domains, and proves
that uniform computable construction of exact finite tables is equivalent to
decidability. It also explains why optimal metareasoning can remain hard.
The literature comparison attributes the utility criterion to Minton, discusses
self-improving algorithms for polynomial-time tasks, and relates fast/slow
arbitration to Milli et al. and SOFAI. These are established precedents for the
paper's explanatory cost bounds.
The follow-up search adds Goré and Nguyen's published global-caching solver for
an EXPTIME-complete problem and Ferrara et al.'s model-checking preprocessing
work. The finite-table construction criterion is explicitly attributed to
standard computability, and the EXPTIME obstruction to the time hierarchy.
These connections strengthen the perspective without establishing theorem novelty.
An explicit induction now constructs exact answers on successively larger finite
domains. Separate results state the uniform expansion bounds that would imply
polynomial-time decision and the workload conditions that amortize costly
expansion. The correctness induction supplies neither bound by itself and does
not prove P = NP.
The executable development now supplies an exact SAT solver, a counted binary
parser, polynomial bounds for fixed or logarithmically growing variable ranges,
and certified witness reuse. A reference fallback adds lazy search on distinct
occurring variables, sound partial-assignment pruning, and reusable checked
refutation trees. Bounded witness and refutation portfolios survive restarts;
all earlier results remain archived.
The default service now adds shared AIG simplification, a bounded local attempt,
and CaDiCaL's mature CDCL engine. SAT witnesses and LRAT UNSAT proofs must pass
Lean checkers. The formula-to-CNF connection is proved; the external solver's
verdict is never sufficient. Indexed proposals and a long-lived JSON-lines
service reduce retrieval and startup overhead. These modern paths report wall
time and explicitly mark their abstract work counts as unmeasured.
An explicit evaluator machine realizes the reported evaluation count exactly
and has a checked bound on intermediate data size. A converse encoding proof
extends the restricted bounds to every accepted binary request.
The [persistent solver](solver/README.md) retains every completed result across
restarts. The [reproducible studies](experiments/README.md) compare reuse with
lazy solving and checked CDCL, while retaining the earlier exhaustive reference.
They do not establish efficient exact learning on unrestricted instances.

The seven-item follow-up adds compact restricted coverage, a complete assignment
search transition system with payload bounds, live CaDiCaL clause reuse, a bounded
persistent predictor, query deadlines, strict cache checks, and disjoint measured
phases. At that milestone, all 69 tests and the 694-theorem axiom audit pass. The expanded study checks
1,260 answers on public and chronological streams and reports gains, overhead,
and memory costs. [Implementation scope](research/implementation-gaps.md) records
which engineering gaps are addressed and which stronger mathematical claims
remain open. None of these changes establishes unrestricted polynomial SAT.

The structural follow-up targets items 1 and 4. Lean proves exact composition
through a bounded shared interface, so total variables may grow while local
acquisition stays bounded. `--components` implements independent-component reuse
under variable renaming and checked transfer of UNSAT cores to added constraints.
`--incremental` now saves stable circuit definitions and selected learned clauses
across restarts. Shared immutable terms, shapes, maps and prefixes reduce
duplication; full request archival costs remain.

The [structural study](experiments/results/structural/summary.json) checks another
420 answers. One acquired shape serves 127 component occurrences through
expansion to 128 variables. Connected-chain and storage controls show the limits:
that component-only milestone leaves nonempty interfaces for the next extension,
and the whole database can grow despite sharing. Try
`python3 solver/persistent.py --components --incremental serve`.

The five-step extension now adds local bucket elimination, persistent add/replace/
remove snapshots, lazy checked rows, semantic relation storage, and checked
incremental LRAT. Use `--interfaces` for the delta API and `--incremental-proofs`
for the proof-enabled live CDCL path; they can be combined for checked fallback.
The [first interface study](experiments/results/interfaces/README.md) reports 792 correct
answers, local reuse and transport savings, and the overheads of checking,
restart and archival storage. That milestone passed 95 tests and audited 837
theorem declarations. All 2,130 older results and 516 proofs remain unchanged, with 355
newly revalidated results and 129 proofs added. The manuscript now includes the
local elimination and shared-circuit proof arguments, their cost boundaries,
and published BDD representation limits. Small width, affected-state size and
cheap acquisition for unrestricted SAT remain unproved.

The central question is when the expense of acquiring reusable knowledge is repaid
by reduced future computation. Exact representability alone establishes neither
compactness nor efficient learning, and a correct hybrid need not be faster overall.

## Build

Install a LaTeX distribution with `latexmk` and the packages used by the source
(including `newtx`, TikZ, and `natbib`). From the repository root:

```sh
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error bounded_domain_sat_and_amortized_reasoning.tex
```

Alternatively, run `pdflatex` twice:

```sh
cd paper
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
```

The PDF is generated alongside the source. To remove auxiliary build files while
keeping the PDF, run `latexmk -c` from `paper/`.

## Repository layout

```text
paper/
  bounded_domain_sat_and_amortized_reasoning.tex
formal/
  OracleMachines.lean
  OracleMachines/
  lean-toolchain
  lakefile.toml
  lake-manifest.json
  README.md
solver/
  persistent.py
  test_persistent.py
  README.md
experiments/
  run_workloads.py
  results/
research/
README.md
LICENSE
```

## Lean verification

The [Lean project](formal/README.md) checks the expansion invariant, explicit
table size, conditional polynomial cost bound, staged savings criterion, and
amortization limits. It also proves that the explicit table and exponential
expansion costs are not polynomially bounded. A theorem map identifies the exact
coverage and remaining obligations.

With Lean's version manager installed, run:

```sh
cd formal
lake exe cache get
lake build
```

The toolchain and dependencies are pinned. The default build audits all declarations in the formal library
namespace for admitted proofs and additional axioms. The formalization treats
general runtime costs as explicit numerical ledgers and connects a concrete
SAT parser and core to an operational cost model. It proves polynomial bounds
for a **fixed** variable cap and for variable width at most `floor(log2(L+1))`,
where `L` is the encoded length. These restrictions do not give a bound for all
SAT inputs or a formalization of P versus NP.
The evaluator's transition and data-size proofs are a component of a runtime
argument for complete-witness evaluation; combined machine simulations for
parsing, partial evaluation, and full search remain open. The lazy search has a
checked bound of `2^(d+1)-1` nodes for `d` distinct occurring variables. Refutation
size can still be exponential.

## Persistent solver

Build the executable with `./solver/build.sh`. Then, from
the repository root, run `python3 solver/persistent.py solve 010`. Subsequent
calls reuse the result from `solver/.cache/results.sqlite3`; new formulas can
also reuse retained witnesses and refutation certificates after checking them. SAT and UNSAT
results accumulate without eviction. The [service documentation](solver/README.md)
covers encoding, storage, restart behavior, integrity checks, and testing.
The database is local and ignored by Git; source code and reproducible experiment
results are versioned.
Use `python3 solver/persistent.py serve` for multiple JSON-lines queries in one
process. The default `auto` backend combines local checks with certified CDCL;
`--backend lean` retains the original counted lazy solver.

## Literature review

The [annotated literature review](research/literature-review-2026-11-07.md) compares
the draft with work on neural advice, speedup learning, compilation, and failed
complexity proofs, including Deolalikar and Wen. It includes
[supplementary BibTeX](research/related-work.bib) and saved OpenAlex/SemOpenAlex
query evidence. The closest precedents and relevant historical cautions are now
integrated into the manuscript's self-contained bibliography.

The review also contains a [detailed proof audit](research/literature-review-2026-11-07.md#detailed-argument-audit-and-scope-beyond-np)
covering every formal argument, the repaired accounting omission, and the limits
of extending the result beyond NP.
The [publication-status reassessment](research/literature-review-2026-11-07.md#publication-status-of-the-generalized-observations)
maps the generalized claims to prior work and distinguishes checked publications,
an MSc thesis, and sources whose full text could not be verified.
The [induction audit](research/literature-review-2026-11-07.md#inductive-expansion-proof-and-limitations)
checks the expanding-domain proof, its cost conditions, and counterexamples to
an unconditional polynomial-time conclusion.

## License

This repository includes an [MIT license](LICENSE).


## Scaling follow-up

The solver now supports affected-bucket updates, direct bounded BDD operations,
live graph/proof reuse, checked negative-core transfer, logical archive caps and
measured full-query route selection. All historical results remain persistent.
The [scaling study](experiments/results/scaling/README.md) records 1,470 correct
answers, including 672 UNSAT, across 147 runs. The earlier milestone passed 106 tests and
audited 879 theorem declarations. The [formal notes](formal/README.md) state
conditional resource bounds and the remaining refinement obligations.

Reuse reduces selected acquisition/planning costs, but checked solving remains
faster on several measured streams. Direct symbolic compression does not give a
polynomial bound on arbitrary intermediate diagrams. Logical database limits do
not bound whole-process memory; capacity exhaustion preserves history and stops
acquisition. The unrestricted polynomial SAT argument remains open.


## Durable reuse and balanced-chain follow-up

The latest implementation adds durable batches, persistent bucket maps, balanced
chain summaries, fused symbolic projection, individually checked proof fragments,
and structural routing with reserved fallback time. **114 tests pass**; Lean
checks **941 theorem declarations**. The explicit chain API uses ten compositions
and eleven node writes for a replacement at 1,024 edges. Whole witnesses and
service costs are accounted separately.

The [new study](experiments/results/followup/README.md) records 2,259 correct
answers and 30 archive-cap errors across 210 runs, including selected TACAS 2026
artifact inputs and a held-out counter. It preserves failures, resource samples,
and every older dataset. The live archive retains all historical rows and now
contains 3,550 results and 1,032 proofs. The [gap register](research/implementation-gaps.md)
and revised manuscript distinguish these implementation results from the open
unrestricted width, representation, acquisition and full-machine obligations.

## Bounded layers and comparable inputs

The latest [study](experiments/results/structured/README.md) adds checked Boolean
layers of width 1–4, persistent source/order indexes, payload-limited active
caches, WAL checkpoint controls, and failure-aware route scores. The layer
replacement theorem exposes exponential width dependence and logarithmic depth;
full witnesses and service overhead remain separate. Native materialization was
also repaired after inspecting generated C.

All **119 tests pass**, and Lean audits **991 theorem declarations**. A new
175-run comparison completes 2,450 queries correctly, with enabled learning,
three additional artifact families and identical full-formula service inputs.
Learning helps the signed-unit stream but does not improve the public-only
streams. A separate cache-pressure study retains every historical state while
measuring the cost of smaller active retention. All older datasets and archive
rows remain unchanged; the live store now holds 3,905 results and 1,161 proofs.
The [gap register](research/implementation-gaps.md) records what remains open.

## Seven-priority follow-up

The current implementation separates semantic row reuse from current provenance,
uses iterative lazy evaluation, retains complete native layered working sets,
and records final route outcomes once. Speculative witness/proof checking now
has a separate budget and measured outcomes. A new `layered_cnf` API checks and
compiles CNF under a supplied adjacent-block partition; it does not discover a
bounded-width decomposition for unrestricted SAT.

**129 tests pass**, and Lean audits **1,047 theorem declarations**. The new
costed reference returns operation counts and is proved equivalent to tree
replacement. Additional proofs cover relation comparison, full witness traces,
prefix/suffix composition and mathematical source binding. Whole-service cost
and protocol refinement remain open. The [priority gap register](research/implementation-gaps.md#seven-priority-implementation-follow-up)
distinguishes implemented improvements from those remaining obligations.

The [new evaluation](experiments/results/priorities/README.md) adds unused public
members, larger mixed-label application sources, a no-training polarity baseline,
matched live/restarted proof modes and distinct-relation pressure. Its
[development pilot](experiments/results/priorities-pilot/README.md) is preserved.
Every previous database row and all 93 historical experiment files remain intact.
The live solver contains **4,260 results / 1,290 proofs**, plus saved expansion
branches and source bindings checked again after restart.

## Incremental CNF source versions

`source_cnf` preserves the actual clauses in a balanced tree alongside their
checked relations. A local edit replaces an edge's entire clause bucket; an
empty bucket deletes its clauses. The supplied disjoint ordered variable
partition stays fixed, with a supplied width from one to four and at most that
many variables per block. Every clause must
fit in one block or two neighboring blocks. There is no decomposition discovery
or unrestricted-SAT width guarantee.

```python
from solver.persistent import PersistentSolver

with PersistentSolver() as solver:
    first = solver.source_cnf(1, [[1, 2], [-1, -2]], [[1], [2], [3]])
    contradiction = solver.source_cnf(base=first['state'], replace={0: [[1], [-1]]})
    deleted = solver.source_cnf(base=contradiction['state'], replace={0: []})
    assert first['answer'] and not contradiction['answer'] and deleted['answer']
```

Use `op: "source_cnf"` with the same fields in the JSON-lines service. Queries
are decision-only by default; `witness=True` requests the complete block-state
path and adds its output/checking cost. Versions remain in the SQLite archive
and are replayed and checked after restart. After a checker upgrade, the saved
clauses and summaries are checked by the new engine before a current result is
stored; old answer bits are ignored and every old row remains intact. The result
reports `revalidated_source=True` on first use from an older namespace. A
different partition starts a new source family and pays initial compilation.

The native decision carries a Lean proof connecting its cached summary to the
original clauses retained in its indexed source tree. Local patch checks reject changes to unedited
subtrees. Incremental reference tracking removes the former full-closure scan
under layered cache pressure. At a tight cap, a single height-h source edit
temporarily reserves up to h+1 additional relation nodes until its transition
is checked, then evicts obsolete nodes. Archive history, metadata, source
payloads and process memory have separate costs.

The reference update bound is proved. Original-variable translation and complete
CNF grouping and complete initial binding now have the proofs described below;
mutable node/patch identities, JSON, persistent maps, Python/SQLite and machine
costs still have refinement obligations.
General factor-DAG provenance, adaptive gating and unrestricted structural
coverage are unchanged. At this milestone **141 tests passed**, and Lean audited
**2,279 declarations / 1,106 theorem declarations**. See the
[source-update study](experiments/results/source-updates/README.md) for matched
full-source rebuilding, lifecycle costs, replay, stored bytes and sampled RSS.

The follow-up uses an indexed assumption check for general-factor negative
proofs. Lean proves equality with the previous membership condition, including
duplicates; counters report index entries and membership probes. It avoids
repeated list scans while retaining the full evidence traversal. Initialization
failures now close their database handles, and the two test-owned connection
leaks are fixed. At that checkpoint **144 tests passed without resource warnings**,
and Lean audited **2,290 declarations / 1,113 theorem declarations**.

That checkpoint's live archive held **4,970 results / 1,548 refutations**, with all older
rows preserved. The [context and upgrade report](experiments/results/context-index/README.md)
records the diagnostics and checked source adoption. To revalidate the earlier
source-study records after updating the solver, use:

```sh
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

This checks historical source fingerprints and recorded evidence; it reports the
current binary separately and does not claim to rerun the historical executable.

The mapping checkpoint proves the conversion from original variable IDs to bounded
block states. Native positions carry array-lookup and width proofs; an alignment
pass establishes completeness. Both compilation paths now use checked local
translations. Lean proves that each translated CNF bucket is satisfiable exactly
when its boundary relation has an accepting pair. The proof includes short and
empty blocks and unused variables. The following checkpoint proves global clause
grouping; the connection through native node identities remains separate.

At that milestone **148 tests passed**, including exhaustive checks of 9,520 boundary
assignments across 112 local CNFs through both native compiler paths. Lean audited
**2,477 declarations / 1,188 theorem declarations**. Alignment and source
equality checks add passes and temporary arrays; these costs are outside the
existing relation-evaluation counter. This checkpoint makes no new speed claim.

The [mapping verification record](experiments/results/source-mapping/README.md)
preserves build/test logs, fingerprints and archive revalidation. That archive
held **5,325 results / 1,677 refutations**. Every old row in all 21 tables and
all 142 earlier experiment files remained intact. The five saved source versions
were rechecked under the new engine and after restart. The
[persistent gap analysis](research/implementation-gaps.md) records the next proof,
accounting and evaluation obligations.

The grouping checkpoint connects the **complete original CNF** to its grouped
relations. The compiler carries a permutation proof preserving every clause
occurrence, including duplicates and empty clauses, together with the local
semantic equalities. Lean proves SAT/UNSAT equivalence with a consistent path
through all buckets. Individually nonempty relations need not share such a path.
A tree-summary theorem follows when exact leaf binding and identity padding are
supplied. The following checkpoint supplies this premise for complete-source
checks; preservation through native patches and replay is still open, as are
reference-count and general row/equivalence-store invariants.

At that milestone **152 tests passed**, and Lean audited **2,562 declarations / 1,233 theorem declarations**
without admits or added axioms. The new global checks cover 11,680 complete
assignments across 60 CNFs, exact clause multiplicities, service witnesses,
incompatible shared boundaries, 65,537 blocks and 12,000 repeated clauses. The
[grouping verification record](experiments/results/source-grouping/README.md)
preserves the evidence. All historical rows and all 150 prior experiment files
remained intact. That archive held **5,680 results / 1,806 refutations** after
checked revalidation. Added grouping/equality work is explicitly outside the
relation-evaluation ledger. No new timing or unrestricted-SAT claim is made.

The binding checkpoint proves **executable complete-source binding** against the
actual stored tree. `SourceBinding.lean` checks every ordered leaf and individual
identity-padding relation, then returns a proof that its decision agrees with
the original CNF. Both native full-source queries and initial source-version
binding use this result. Original-clause/provenance checks remain in place.

The scan has a proved count of one relation comparison per logical leaf. New
metrics expose that count and diagnostic cell/source-evaluation bounds. Shared
nodes still incur work for each logical occurrence. Initial source-version binding
adds a source-evaluation pass; warm queries and local edits do not repeat it.
Allocation, bit costs, transport and storage still need separate accounting.

At that milestone **156 tests passed** and Lean audited **2,615 declarations / 1,259 theorem declarations**
without admits or added axioms. New tests cover incorrect binding despite a
matching final answer, nonidentity padding that composes to identity, dimensions,
counts and 65,536 logical leaves sharing 17 native nodes. The
[binding verification record](experiments/results/source-binding/README.md)
preserves the evidence. All old rows in 21 tables and all 158 earlier experiment
files remained intact. That archive held **6,035 results / 1,935 refutations**;
all 355 distinct generic inputs and five old source versions pass revalidation.
Native identity/patch/replay invariants and complete resource bounds remain open.
The historical timing study is unchanged; this proof adds no new speed claim.

The preceding checkpoint retains **original-source meaning through native joins**.
`SourceNodes.lean` indexes source nodes by their exact layout, width, start and
height. Logical leaves keep original clauses and translation proofs; joins require
consecutive intervals and preserve all clause occurrences. The cached decision
now has SAT/UNSAT equivalence theorems for those original clauses. Native
registration and replay use these constructors; warm decisions read the summary
without flattening or traversing the source.

New metrics count registered original-source nodes, clause entries and literal
entries, including replay. The retained original integer arrays have additional
storage cost alongside JSON evidence and local translations. These counters are
diagnostic entries, not bytes or RSS. No new timing or memory-reduction claim is made.

**159 tests pass**, and Lean audits **2,751 declarations / 1,320 theorem declarations**
without admits or added axioms. Regressions cover invalid joins/layouts, failed
batches, duplicate registration, shared-variable conflicts, sparse IDs, empty
blocks, payload counters and restart. The
[source-node verification record](experiments/results/source-nodes/README.md)
preserves the evidence. Every old row in 21 tables and all 166 earlier experiment
files remain intact. The archive now holds **6,390 results / 2,064 refutations**.
Its named-store obligation is partly closed by the following checkpoint.

The preceding checkpoint proves **paired native-map and decoded-metadata
correspondence**. `SourceStore.lean` couples each named relation tree to its exact
original-source model and retains matching identity, layout, width, start, height
and original leaf clauses. Initialization, insertion and erasure preserve the
invariant without a store scan. Lookup theorems connect the retrieved tree's
decision to its original clauses. Runtime parsing, comparisons and temporary
headers remain costs; proof fields erase.

**162 tests pass**, including 23 source-update tests. Lean audits **2,858
declarations / 1,367 theorem declarations** without admits or added axioms.
New regressions cover deletion-batch rollback, shared descendants, safe identifier
reuse, distinct provenance with equal relations and missing-field rollback.
The [source-store verification record](experiments/results/source-store/README.md)
preserves the evidence. All 355 older generic inputs and five saved source
versions pass current-engine revalidation. Every old row in 21 tables and all
174 earlier experiment files remain intact. The archive holds **6,745 results /
2,193 refutations**.

The preceding checkpoint proves **named child registration and serialized-summary
binding**. `SourceLinks.readJoin` connects decoded child names to the exact models
retrieved at registration, then proves original-clause composition and the need
for one valuation satisfying both sources. Conditional lemmas preserve links
under fresh insertion and deletion avoiding both children. The paired native
store also retains exact equality between each decoded mask's relation and its
model's cached summary.

**165 tests pass**, including 26 source-update tests. Lean audits **2,874
declarations / 1,380 theorem declarations** without admits or added axioms.
The [source-link verification record](experiments/results/source-links/README.md)
records malformed child/mask checks, distinct provenance under equal relations,
and shared-child retention across shuffled parent deletions. All 355 generic
inputs and five saved source versions pass revalidation. Every old row in 21
tables and all 182 earlier experiment files remain intact. The archive holds
**7,100 results / 2,322 refutations**.

The preceding checkpoint proves **native source dependency lifetime**.
`ReferenceCounts.lean` relates incoming counts to the exact number of decoded
child occurrences across live parents. `SourceLifetime.lean` uses count zero to
prove safe deletion and preserves each surviving branch's exact named children.
The executed source context carries these invariants through fresh insertion and
deletion; duplicate definitions change no state. The aggregate sum and finite
parent-domain witness exist only in proofs. Updates still touch at most two
direct child counts, without scanning the store.

**166 tests pass**, including 27 source-update tests. Lean audits **2,944
declarations / 1,416 theorem declarations** without admits or added axioms.
An independent full-graph recount checks eviction decisions for 44 nodes with
16 roots, shared descendants, duplicate registrations and randomized deletion,
followed by complete reclamation and reuse of the same names. The
[lifetime verification record](experiments/results/source-lifetime/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every previous row in 21 tables and all 190 earlier experiment files remain
intact. The archive holds **7,455 results / 2,451 refutations**.

Next is exact requested-patch semantics. Python retention, the generic relation
store, complete persistence refinement, acceptance completeness and full resource
costs remain separate obligations. No new timing or unrestricted-SAT guarantee
is claimed.


The preceding checkpoint proves **exact native source-patch semantics**.
`SourcePatch.lean` connects decoded request fields and current live root/child
lookups to the original arrays: every requested bucket gets its supplied clauses,
and every unedited bucket stays unchanged. Equal relations cannot substitute for
exact original arrays. The executed checker carries this certificate and keeps
its path-visit counter; the proofs add no full-source scan or relation join.

**169 tests pass**, including **30 source-update tests**. Lean audits **3,043
declarations / 1,461 theorem declarations**, with no admits or added axioms.
New checks cover split-path edits with padding, order and duplicate original
clauses under equal relations, invalid requests/roots/partitions, unchanged
aliases, and the complete 4,096-entry decoding cap. Runtime checkpoint `32b4748`
is committed and pushed. The [patch verification record](experiments/results/source-patches/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every old row in 21 tables and all 198 earlier experiment files remains intact.
The archive now holds **7,810 results / 2,580 refutations / 50 source-state rows**.

Next is composing initial raw-CNF binding, complete root coverage, the
bucket-to-flattened-CNF transition and the returned verdict/witness into one
successful-request theorem. Python retention, complete replay/SQLite refinement,
generic relation/factor stores, acceptance completeness and total resource costs
remain open. The updated checker pays for direct lookups, decoding, edit-list
filtering and array comparisons. Earlier timings are unchanged; no speedup or
unrestricted-SAT guarantee follows.


The preceding checkpoint proves **complete successor formulas and returned native
decisions**. `SourceFormula.lean` connects ordered bucket flattening to the exact
original clause list, characterizes interval coverage and empty padding, and
proves that an accepted patch gives the complete requested successor CNF.
`SourceVerdict.lean` certifies root coverage and the actual returned answer field.
The exposed query/patch functions have success theorems, including the nested
patch verdict, with both SAT and UNSAT equivalences for the original formula.

**171 tests pass**, including **32 source-update tests**. Lean audits **3,107
declarations / 1,506 theorem declarations**, with no admits or added axioms.
New tests reject incomplete, shifted and oversized roots and check actual verdicts
against exhaustive truth tables over 54 transitions with 1, 3 and 5 logical edges.
They include padding, old branches, deletion, repeated and empty clauses, and both
answer modes. Runtime checkpoint `9673dee` is committed and pushed. The
[verdict verification record](experiments/results/source-verdicts/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every old row in 21 tables and all 206 earlier experiment files remains intact.
The archive holds **8,165 results / 2,709 refutations / 55 source-state rows**.

Next is the complete initial raw-CNF anchor and composition over accepted
operation histories. Serialized witness contents, byte transport, Python
retention and complete replay/SQLite refinement also remain open. Flattening is
specification work; warm decisions add no full-source scan or summary rebuild.
Total physical/resource costs and unrestricted coverage are not established.
Earlier timing evidence remains unchanged.


The latest checkpoint closes the **initial raw-CNF binding** gap.
`SourceInitial.lean` connects the actual request getters to the live root's exact
original buckets, complete coverage, clause permutation and returned verdict.
Grouping may reorder clauses globally; duplicate and empty clause occurrences
remain intact. `SourceUpdates.bindSource_success` covers the native JSON-returning
function. The executed original-bucket scan proves `visits + 1 = 2^(height + 1)`
and `height < 17`; this counts logical visits, not total machine work. Initial
compilation and both complete binding scans remain charged. Warm paths are unchanged.

**174 tests pass**, including **35 source-update tests**. Lean audits **3,154
declarations / 1,539 theorem declarations**, without admits or added axioms.
Runtime checkpoint `92a1ddd` is committed and pushed. The
[initial-binding verification record](experiments/results/source-initial/README.md)
records all 355 generic inputs revalidated, five source versions adopted and
restarted, every old row in 21 tables preserved, and all 214 earlier experiment
files unchanged. The archive holds **8,520 results / 2,838 refutations / 60
source-state rows**.

Next is composition over accepted operation histories. Serialized witness values,
byte transport, Python active-root retention, replay/SQLite refinement, generic
stores, acceptance completeness and complete resource bounds remain open. Earlier
timings are unchanged; no new unrestricted-SAT guarantee follows.

## Certified affine growth

The affine path adds fresh variable blocks while retaining an exact summary of
all preceding parity equations. Its summary has at most `b+1` equations over a
width-`b` boundary, or `(b+1)^2` coefficient/right-hand-side cells. One resident
append with `c` new equations has reference charge `O(b^3 + b^2*c)`. The native
solver executes the Lean-certified coefficient operations; it does not enumerate
boundary assignments. This is a restricted affine result using established
Gaussian elimination, with explicit construction and replay costs.

Original batches, immutable versions and results persist in SQLite. Restart
replays original equations, and adding a contradictory batch never changes a
saved parent's answer. The interface is decision-only, with an optional boundary
summary; it does not return a full-history witness. Width, batch and resident
version caps are explicit refusals. General CNF, arbitrary older-variable edits,
complete persistence refinement and total machine-cost bounds remain open.

See the [API and limits](solver/README.md#affine-growth),
[formal contracts](formal/README.md#affine-growth), and
[archived validation](experiments/results/affine-growth/README.md).
The checkpoint passes **184 tests** and the Lean audit of **3,485 declarations /
1,708 theorem declarations**. It retains all prior results and 268 affine versions.

The next checkpoint (`88f26a8`) composes the native source-CNF response contracts
across arbitrary finite request histories, including rejected batches and layout
resets. Earlier observations keep their event-specific source meaning; reused
names are not assumed to denote the same formula after deletion/reset.

Affine native histories now use erased proof data, so resident children do not
keep runtime ancestor states reachable. The service bounds resident versions independently
of archive length and replays old branches with eviction. A 4,101-append test grows
and restarts with only two resident versions. All **190 tests pass**; Lean audits
**3,625 declarations / 1,766 theorem declarations**. Complete Python/SQLite
refinement, broader decompositions and total machine costs remain open.
See the [history and retention record](experiments/results/history-retention/README.md).

Checkpoint `1037595` connects affine decoded Boolean inputs and named-store
histories to the original-equation invariant. **192 tests** and the Lean audit
of **3,794 declarations / 1,836 theorem declarations** pass. Expansion work is now
prioritized around compression and reuse: the repeated affine streams contain
14 identical algebraic calls among 18 distinct history expansions. This motivates
an exact transition cache, implemented in the next checkpoint below. See the
[current gap record](research/implementation-gaps.md) and
[pattern evidence](experiments/results/affine-history/README.md).

Checkpoint `f80f678` implements exact certified transition reuse. A cache hit
checks the full boundary summary and equation batch, reuses the algebraic result,
and attaches it to the new version's own history. Hash collisions cannot authorize
reuse. The cache is configurable, bounded by slots, and disabled with
`affine_kernel_slots=0`.

In five matched repetitions, repeated width-16 streams fall from **167.57 to
144.21 ms** and repeated width-32 streams from **496.37 to 215.54 ms** (2.30x).
Novel streams have no hits and roughly unchanged timings with slight median
overhead. These are synthetic affine results, without a general SAT speed claim.
All **197 tests** and the Lean audit of **3,938 declarations / 1,875 theorem
declarations** pass; all 405 older experiment files and old archive rows remain.
See the [cache experiment and limits](experiments/results/affine-kernel-cache/README.md).


## Shared affine batches and certified preparation

Checkpoint `e0cb8d3` adds duplicate-free computation and adaptive original-batch
sharing. Prepared typed rows and normalized transitions can be reused across
histories with different duplicate counts. The source archive retains exact row
order/multiplicity and legacy version identities; existing rows are unchanged.

In five matched repetitions, width-32 changing-multiplicity streams fall from
**1,246.55 to 430.52 ms** with both options. Repeated width-32 source payload falls
**16,656 -> 6,499 bytes**, and database size falls by **12 KiB**. That storage gain
costs **6.6%** more elapsed time on the exact repeated stream. Novel streams gain
no reuse. Native request JSON is still per version, so these measurements do not
establish a reduction in process memory. Each cache has its own slot occupancy;
byte budgets and batch handles remain open.

All **207 tests** pass; Lean audits **4,043 declarations / 1,911 theorem
declarations**. Every old archive row and all 583 earlier experiment files remain.
See the [four-mode evidence and remaining limits](experiments/results/affine-batch-reuse/README.md)
and [current expansion priorities](research/implementation-gaps.md).


The [current resource-bounds audit](research/resource-bounds.md) separates general
SAT, finite coverage, factor/layered expansion, affine hits/misses, cold replay,
live memory and archive growth. It records exact formal bounds, derived payload
accounts, configured refusals, measured phase costs and the remaining proof gaps.

The [resident-width follow-up](experiments/results/affine-resident-metadata/README.md)
removes a redundant parent decode: shared warm appends use seven instead of nine
object reads. All 210 tests pass; the native proof code and earlier archive remain
unchanged. The [KD-tree assessment](research/indexed-reuse.md) distinguishes exact
lookup from candidate search for a future checked repair path.

[Uniformly cheap expansion](research/expansion-preconditions.md) makes the next
target explicit: maintain a closed structural invariant that enables cheap
construction even for unseen updates. A diagnostic finds point boundaries in
all regular steps of the existing repeated/novel affine streams. Conditional
semantic lemmas are Lean-checked; specialized native recognition and construction
remain to be implemented and measured against richer boundary families.

The [arbitrary-SAT expansion analysis](research/arbitrary-sat-expansion.md)
refocuses the next milestone on interacting tractable classes: checked class
leaves, heterogeneous backdoors, recursive component splitting and persistent
residual reuse. It records the literature, an explicit obstruction to independent
class solving, and the discovery/recombination costs that remain unresolved.
