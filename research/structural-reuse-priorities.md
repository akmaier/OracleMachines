# Structural reuse: cost map and investigation priorities

Updated 2026-11-24 after the user's shift toward pattern discovery and a valid
partition of the entire SAT problem. This is the working record for the hourly
investigation. Start with the [discovery plan](sat-pattern-discovery.md), then
consult [implementation history](implementation-gaps.md),
[resource bounds](resource-bounds.md) and the measurements below.

**Primary objective:** discover useful SAT categories and exact decompositions
from arbitrary CNF input, retaining explicit coverage of unresolved cases.
Recognized-family optimization continues as supporting work. A complete
classification and efficient solution of every resulting cell are separate
obligations; retain overlaps, checked recognition and composition costs.

## Current investigation: interactions beyond one remaining guard variable

[Direct certificate transport](local-certificate-transport.md) reuses 148 local
unit refutations on the same guided search path. It reduces fresh probe
propagation visits 17.19%, but aggregate solve time only 0.55%; complete-worker
time rises 0.20%. All eight exposed edits still stop at 256 dispatches. Native
checked-cache totals fall 0.135%; SQLite totals fall just 8,192 bytes. Peak RSS
shows no reduction. The mechanism remains optional, with all regressions saved.

**Next target: discover how surviving guards with multiple unfixed assumptions
interact at actual local residuals.** Group by exact current support/component,
measure overlap and complementary regions, and determine where exact local
composition closes an interaction versus where fresh acquisition remains.
Require component-local support and checked recomposition. Do not repeat the
existing guard-frontier tree solely because it covers more assignment mass;
its comparisons already showed that more covered mass need not reduce work.

Full-cofactor preparation, reason binding and native checking remain costs even
when a local unit trace is known. Matching and opposite-branch acquisition also
remain. An index or smaller local counter alone is not a total-cost result.
Keep automatic origin discovery, general coordinate transport, fresh unlabelled
evaluation and unrestricted expansion bounds explicit. Resume
`experiments/results/cnf-guard-certificate-reuse/checkpoint.json`; the prior
cumulative authority and alternate raw certificates remain preserved.

## Previous investigation: reuse local certificates under a fixed selection path

[The live guard selector](guard-probe-selection.md) removes duplicate tracking
normalization and event retention. Tracking alone preserves native counters and
SQLite files with 1.27% aggregate solve overhead. Guided selection makes 148
offers, changing the variable at 75 sites, but costs 1.84% more solve time and
0.77% more complete-worker time. All eight exposed edits remain unresolved.
Checked-cache endpoint totals increase 1.68%, plus 249--403 KB banks per worker.
Keep this negative result and all four controls; no default change is justified.

**Next target: transport a surviving conditional certificate to the actual local
cofactor, holding probe selection fixed.** The saved guard is currently used
as a selection hint while the local refutation is acquired again. Review
`experiments/cnf_conditional_unit_support.py` and its `materialize` path first.
Bind source variables, fixed assignments and current clause support exactly;
missing support in a selected component must fall back to the unchanged probe.
Compare total construction/checking, proof bytes, warm reuse and cold replay.
This candidate does not remove the opposite branch or all normalization costs.

The adaptive query-only profile selects the largest regression, edit 28
(+11.13%). Guided normalization takes 0.50635 profiled seconds, native checking
0.49224, negative-child checking 0.31392 and guard choice only 0.00188. Cumulative
times overlap. Fewer normalization and propagation calls still cost more because
the chosen residuals change. An index for guard matching is therefore a low
priority on this evidence.

Avoid repeating preserved alternatives: broad proof-normalization reuse had
mixed gains, the prepared-cofactor memo regressed despite less normalization,
and checked ordered normalization already exists. Direct canonical-header
checking is already in the live stack. Any new sharing of preparation must
identify its additional boundary and preserve independent proof checks.

Broader structural coverage remains open: after useful local certificate reuse,
census interactions among guards with more than one unfixed assumption, with
component-local support and explicit unresolved regions. Origin recognition,
general coordinate transport and fresh unlabelled evaluation remain necessary.
Resume `experiments/results/cnf-guard-probe-selection/checkpoint.json` with the
multipart reader. All previous authority and failed comparisons remain saved.

## Previous investigation: select useful probes without expensive capture

[The passive guard-probe census](guard-probe-census.md) finds a concrete target:
648 ordinary contexts expose 394 distinct unit-refutable local cofactors.
Ordinary probing misses 260 of those polarities; 232 concern a different
variable, and all 260 are absent at the first probe of their recorded context.
The 395 prior templates are explicitly provisioned and all survive their edits.
Local checking is essential: full-source exclusions do not automatically refute
a component or subset. Every actual candidate is independently checked.

**Next target: a bounded live guard-guided selector at ordinary probe sites.**
Use the existing unit/split/model proof path; charge recognition and source maps,
check actual local cofactors, and retain an order-matched control. All eight
inputs still stop at 256 dispatches in the passive census, with byte-identical
native databases. These are opportunities to change selection, not demonstrated
runtime or whole-input coverage improvements.

The chief immediate cost is observer overhead: aggregate solve time rises
7.82736 to 10.30903 seconds; separate checking/storage adds 3.15887 seconds.
Live matching performs 32,044 guard checks and 262,032 guard-pair checks.
Coordinate tracking and diagnostic serialization are also charged, so these
figures do not isolate matching as the dominant subroutine. Avoid full event
capture in a live implementation; investigate incremental matching with precise
rollback, deleted-support and subset-binding rules. Compare total runtime,
retained state and fresh whole-root coverage before adopting any default.

Automatic origin discovery and fresh unlabelled evaluation remain open. The
captured event graphs reach 2.34 MB, excluding banks and tracking frames; a key
or event cap is not a whole-process bound. Existing source extraction sharing
remains second. Resume `experiments/results/cnf-guard-probe-census/checkpoint.json`
with the multipart reader. The cumulative audit preserves all prior payloads
and raw alternatives, including the failed memory-charge audit assumption.

## Previous investigation: use exclusions at ordinary search contexts

[Shared guard-frontier selection](guard-frontier-selection.md) quantifies the
saved structure: ten of 395 guards are subsumed within their origin, and five
complementary pairs remain among inclusion-minimal guards. Sorted-prefix tries
would use 2,512 edges for 3,239 guard-literal occurrences; this is a structural
count, not a proof-memory saving. Preserve alternative supports under deletions.

The new greedy tree spends the same 129-node allowance on uniform covered mass
per added split. All eight plans close more assignment mass; origin 63 improves
from 1.02% to 27.34%. But both cold edits still stop at 256 dispatches. On edit
64, solve mean falls 27.38% and complete-worker mean 3.68% versus the previous
plan; its database is 1.80% smaller. Edit 28 instead costs 4.66% more solve time.
The new supported route is still 14.58%/83.68% slower than ordinary solving on
64/28. No default change or expanded whole-input coverage is justified.

The same-new-tree open control isolates the support effect: only 0.64% solve
saving on 64, with mixed pair signs, and a 13.97% regression on 28. Much of the
target-64 gain is associated with branch order. Two open regions there consume
122 and 69 of 256 native dispatches, with 152/151 variables and 613/600 clauses
before acquisition. The second remains unfinished. These are operation counts,
not wall-time attribution. Counting more closed assignments is an inadequate
cost objective for the remaining search.

**Next target: apply checked exclusions at natural search contexts.** Avoid
imposing another guard tree on ordinary acquisition. Review
`experiments/cnf_trace_learning.py` and `experiments/cnf_probe_learning.py` first:
their existing source-checked binary implications are relevant machinery, but
do not already implement exclusions from arbitrary multi-assumption guards.
Test a bounded extension with exact support containment, no circular reasons,
native proof lifting and deleted-clause invalidation. Retain the ordinary,
old-tree and open-tree controls; fresh unlabelled evaluation and automatic
origin discovery remain open. No compact closure of arbitrary SAT follows.

A concrete first census is guard-guided failed-literal selection: at an ordinary
context matching all but one assumption, offer that last variable to the
existing `cnf_whole_lookahead.py` unit-certificate and split/model machinery.
Check exact coordinate binding, count opportunities absent from current probing,
and charge matching before implementation. This may avoid a new arbitrary-clause
proof format; it supplies no verdict on the opposite branch and has no measured
hit rate yet.

Source restriction and unit-extraction sharing remain second: the previous
census paid 7.53 seconds beyond source search/capture. Increasing the 256-event
capture allowance or discarding dominated alternatives is not justified by
this result. Output-tree size does not bound copied certificate banks, pending
candidate lists, contexts or all process memory.

Resume `experiments/results/cnf-guard-frontier/checkpoint.json` with
`experiments.cnf_archive_parts.restore_archive`. All earlier authority payloads
and alternative trial proofs remain preserved, including every negative result.

## Previous investigation: use conditional exclusions without costly tree expansion

[The unfinished-origin census](stopped-origin-supports.md) supplies 342 checked
conditional templates from all seven stopped sources, plus 53 from completed
control 27. Every template survives its paired edit. Capture leaves the original
72-query search counters and six-table proof payloads unchanged. Missing tail
certificates are explicit: source 60 has three candidates rolled back on stop.

The first 129-node plans do not repay their cost. They use only 5--18 distinct
templates each; the selected closed regions cover 0.0254%--6.8146% of uniform
assignments, not SAT-instance coverage. Four alternating cold trials on edits
28/64 consume 31/15 support leaves but still stop at 256 dispatches. Against
identical trees with all certificates removed, solve time rises 6.31%/5.62%,
complete-worker time 1.63%/1.22%, and database size 1.06%/0.20%. The ordinary
solve route is faster still, but differs in handoff and stop-tail publication.
No default changes and no new whole-CNF coverage are justified.

**Next target: shared conditional exclusions and guard redundancy.** Start with
the preserved 395 templates: quantify subsumed assumptions, shared prefixes
and overlapping regions before choosing a representation. The current
first-compatible tree wastes its bounded frontier on narrow contexts and forces
a costly order. Investigate a bounded shared representation or checked clauses
excluding the guarded assignments while retaining exact support invalidation.
Measure remaining acquisition and construction cost; more local reuse alone
did not save total work. Fresh unlabelled inputs are required after these
exposed diagnostics, and no compact closure of arbitrary SAT is established.

Second, independent extraction costs 7.5308 seconds across eight origins,
in addition to 10.1341 seconds of observed source search and capture. Reusing
source restriction/propagation prefixes is a concrete cost opportunity. The
candidate cap rejects 138 further events; increasing it without better selection
would add preparation and storage before demonstrating useful coverage.
Selected pending graphs reach 10.31 MB despite the slot cap; it is not a byte
or whole-process limit. Tail recovery is a smaller separate gap in this census.

Resume `experiments/results/cnf-stopped-origins/checkpoint.json` using
`experiments.cnf_archive_parts.restore_archive`. Conditional native proofs,
failed development replay, same-tree controls and every previous payload remain
preserved. The cumulative audit rechecks new nodes and dependencies, verifies
old payload identity, and retains preceding full-history audits by their hashes.

## Previous investigation: reuse unfinished origins across small edits

[Deferred binary preparation](probe-binary-lazy.md) closes the identified waste:
the exposed target normalizes six residuals instead of 67, with identical
certificates. Four repetitions save 3.21% exposed / 3.57% fresh solve time and
1.60% / 1.48% complete-worker time versus eager closure. One exposed worker pair
regresses. The new gate is still slower than handoff-only by 5.24% / 4.97% solve
and 4.11% / 4.05% worker time; keep it experimental. Proof bytes and retained
state are identical to eager closure. Fresh payload remains 2.67% above the
handoff control, despite 51 fewer native dispatches.

All policies retain 40/48 exposed and 34/48 fresh roots. Different streams are
not a policy-induced coverage loss. Eight fresh random-three roots, four
disjoint-mixture roots and two shared-mixture roots remain unresolved. Those
three categories consume 97.13% of fresh lazy solve time. Further gate tuning
alone leaves that coverage frontier intact.

**Next target: census source-bound partial plans from budget-stopped origins.**
The largest fresh paired regression is edited disjoint mixture 64. Its earlier
source 63 also stops at 256 dispatches; identical variable coordinates expose
exactly one removed and one added clause. The current whole-plan route searches
ten completed negative origins and finds no eligible plan. It requires a checked
negative root, so 63 cannot supply a branch plan. Individual stored residuals
can already be reused; the missing route is broader source-bound recomposition
from an unfinished origin, not a claim that all previous work is discarded.

The posthoc census includes all 24 base/edit pairs: seven have unfinished origins
at the time of their edits, whose targets remain unfinished, across random-three and both mixture categories. Start
with 63/64, retain exact guards and source mappings for checked conditional
leaves, and mark every unresolved branch open. Use completed-origin 27/28 as a
control: it already reuses 22/27 leaves but still stops. A deleted support must
invalidate its leaf; every split needs complete coverage before a verdict.
First measure reusable supports and bounded skeleton retention, including cold
reload and edit checks. Classify leaf proof kinds: the current partial extractor
leaves unsupported endpoints, including implications, open. No coverage or speed gain is established for this
candidate. Avoid treating a stopped parent as a negative proof.

The remaining binary cost is a secondary candidate: validate a previous binary
model against the current subset before rebuilding its graph. This needs a
coordinate-aware hit census and complete checking of current binary clauses;
no model-sharing hit rate has been measured. Prefer the unfinished-origin
coverage investigation before another local gate optimization.

Resume `experiments/results/cnf-probe-binary-lazy/checkpoint.json` with
`experiments.cnf_archive_parts.restore_archive`. The study preserves both timing
controls, failed test fixture, all older authoritative payloads and raw trials.

## Previous investigation: avoid full preparation on inconclusive binary checks

[Binary closure inside whole probes](probe-binary-closure.md) establishes a
real recognition opportunity and a negative total-cost result. An unchanged
exact-prefix census finds 19 checked binary refutations among 353 unit-consistent
cofactors. The optional gate uses those existing native proof rules, but four
alternating repetitions retain 40/48 roots in each stream while raising solve
mean 8.85% exposed / 8.86% fresh and complete-worker mean 5.27% / 5.03%.
Every pair regresses. Keep this gate experimental; more local certificates are
not evidence of cheaper expansion or broader whole-input coverage.

Fresh closure compiles 80 negative cofactors from 2,239 attempts and leaves
2,159 inconclusive. It saves 61 native dispatches but adds 172 native records,
2.72% payload and 2.69% selected retained Python state. Native dispatch counts
exclude the gate's compiled certificates. The larger accounting is decisive.

**Next target: defer full-residual canonicalization until a raw binary
contradiction needs publication.** The largest fresh paired regression is
unresolved repeat 38 (size 150): 1.1528 to 1.3005 seconds. Its gate makes 100
SCC calls, finds six refutations and normalizes 67 residuals; 61 normalizations
serve only misses. The existing SCC routine accepts noncompact variable labels.
Test raw post-UP binary discovery first, canonicalize and build the checked
source-bound certificate only on hits, and preserve old certificate bytes by
canonical SCC reconstruction if needed. Measure against both the preceding
handoff policy and the slower closure gate; this saving is not yet measured.

This removes only part of the overhead. The exact-prefix profile attributes
0.1078 of 0.3275 instrumented helper seconds to normalization, and 0.1228 to SCC;
these cumulative costs are not unprofiled savings estimates. Binary model or
graph reuse is a secondary candidate, requiring current-clause validation and
explicit coordinate handling. The fresh remaining roots are six random-three
sources and shared-mix edits 34/67. Their interaction still needs broader
certified coverage, regardless of cheaper recognition.

Resume `experiments/results/cnf-probe-binary-census/checkpoint.json` with
`experiments.cnf_archive_parts.restore_archive`. The failed guard-test fixture
and corrected audit-variable failure are preserved alongside the negative
benchmark. All earlier authoritative payloads and experiments remain intact.

## Previous investigation: distinguish preparation savings from new structure

[Consumed preparation lifetime](probe-lifetime.md) clears used references and
separates cleanup from earlier admission. Four alternating repetitions show
4.57% exposed / 3.54% fresh solve savings and 1.67% / 1.92% complete-worker
savings versus original 2 MiB retention. Original 4 MiB retention gives similar
savings; the comparison with early release has mixed signs. Cleanup alone adds
0.74% / 0.12% solve time. All controls and regressions remain preserved.

**Memory conclusion:** the 2 MiB pending cap is not a 2 MiB full-visit cap.
Its fresh envelope reaches 4,607,922 bytes. On the largest unresolved attempt,
new traced allocations peak at 27.32 MB versus 27.18 MB for original 2 MiB
retention and 27.33 MB for original 4 MiB retention. Selected retained state
and proof payload are identical across arms. Do not claim a memory reduction
from the lower pending counter, or increase capacity again without a new reason.

**Next target: census checked binary structure in inconclusive probes.** The
fresh stream retains 40/48 distinct roots in every arm; six random-three roots
and edited disjoint/shared mixtures 61/67 remain unresolved. Random-three costs
53.80% of fresh transfer solve time and the mixture families another 43.56%.
Case 37 is the largest unresolved attempt at 1.2852 seconds. It already performs
145 binary SCC checks, yielding ten refutations and 135 satisfiable-subset
misses, but 49 whole probes remain inconclusive. Inspect their exact residuals
for an existing binary refutation after any already computed unit assignments.
Measure both polarities, restriction, mapping and source-bound proof checks.
This is a discovery hypothesis, not an observed additional certificate. A
satisfiable binary subset gives no verdict on its other clauses.

Use the two mixture edits as controls. Case 61 reuses 20/25 proof leaves but
still exhausts acquisition on the rest. Certified interaction coverage matters
more than further handoff tuning that leaves the same search tree. Supporting
runtime work can inspect 372 remaining negative-child canonicalizations on
case 37, but must retain the earlier proof-memo and ordered-normalization
regressions rather than retrying a broad cache without evidence.

Resume `experiments/results/cnf-probe-lifetime/checkpoint.json` with
`experiments.cnf_archive_parts.restore_archive`. No production default or
unrestricted-SAT claim changes. Exposed coverage stays 42/48; comparing that
with fresh 40/48 does not measure a policy-induced loss.

## Previous investigation: release consumed preparation before retaining more

[Exact probe-to-child handoff](probe-handoff.md) reuses work from inconclusive
whole-clause probes at the ordinary child while preserving prior pool and
recognition order. Four alternating repetitions give a 2 MiB selected-payload
policy solve savings of 3.58% exposed and 2.68% fresh; complete-worker savings
are 1.98% and 1.58%. Every pair improves. The 256 KiB policy is slower by
0.31% and 1.16% in solve mean. Proof bytes, models, dispatches, retained solver
graphs and 42/48 coverage are identical across all three policies.

**Next target: shorten the lifetime of consumed offers.** At 2 MiB, the fresh
stream consumes 783 preparations and reuses 659 propagation results, but rejects
684 offers and discards 218 admitted ones. Ancestor offers remain charged until
the entire child visit returns. Determine when ownership can move to the already
existing native visit, and remove now-unused preparation references. Release
only after canonicalization and any needed propagation have been consumed;
keep genuine pending opposite branches charged. Lowering a counter alone is
not a memory improvement. Measure admission sizing (1.66 million fresh literal
visits), failed offers, peak charge and RSS before considering a higher cap.

Fresh worst unresolved case 37 (size 138, mean 1.2407 seconds) consumes only 11
offers at 2 MiB and rejects 90; normalization calls fall 739 to 728. Its exact
prefix and native payloads match the measured worker. This is the concrete
lifetime test case, not a new supplied structural label.

Random-three still accounts for 76.64% of fresh solve time and all six remaining
unresolved roots. Broader structural decomposition remains the coverage gap.
The handoff changes acquisition overhead, not the search tree or tractable
categories. Use the exact-prefix profile and retain the small-cap regression.
Resume `experiments/results/cnf-probe-handoff/checkpoint.json`; its cumulative
archive uses `experiments.cnf_archive_parts.restore_archive`.

## Previous investigation: reuse work from inconclusive whole-clause probes

[Complete-result priority](whole-pool-priority.md) removes the two exposed
57/58-dispatch reconstructions by using existing complete proofs. Each measured
stream has five such hits. Exposed solve mean improves 2.17%; fresh solve mean
changes only -0.08%, with mixed paired signs. Fresh complete-worker mean falls
1.63% and native payload 3.03%. Coverage remains 42/48, and affine completion
alone is still faster. The earlier case-70 partial transfer survives in 223
dispatches; its added complete-lookup miss remains a measured regression.

**Next target: confirm and exploit the handoff from an inconclusive whole-clause
probe to the actual ordinary child.** Random-three consumes 69.70% of fresh
solve time and contains all six roots still unresolved at the end. Inspect the
exact-prefix profile of fresh case 40: 131 specialized cofactor preparations,
126 nonconflicting bipolar probes and 48 whole-clause lookahead misses. It also
performs 779 general normalizations. Determine which restriction, normalization
and propagation results are produced twice before proposing a saved-work bound.
Use the existing `cnf_cofactor_handoff.py` machinery when applicable, preserving
higher-priority discovery and full certificate checks. Charge retaining,
matching, copying and discarding offers. Its earlier mixed total-cost results
remain relevant; no nonconflicting probe is a SAT certificate.

Complete-first arbitration also retains a secondary cost gap: fresh misses
62/67 gain 126.93/110.65 ms without reducing dispatches. Do not extend the gate
blindly. The six unresolved random-three roots are the broader coverage gap.
Resume `experiments/results/cnf-whole-pool-priority/checkpoint.json`, using
`experiments.cnf_archive_parts.restore_archive` for its cumulative history.
Transport chunking preserves every byte but does not reduce archive growth.

## Previous investigation: preserve cheap complete reuse before partial reconstruction

[Whole-proof frontiers](whole-proof-frontiers.md) closes the exposed case-70
gap. Automatic matching selects its earlier checked refutation, retains 22
surviving leaves and acquires the five uncovered leaves within 223 dispatches.
Distinct-root coverage grows from 38/48 to 39/48. Open leaves carry no authority;
the ordinary native checker verifies the completed target.

The cost comparison rejects this priority as a default. Exposed solve mean
regresses 1.54%; fresh solve mean regresses 4.04%, with no fresh coverage gain.
Fresh proof payload grows 6.85%. Two edits (31/34) change from one dispatch each
to 57/58, adding 329.33 ms of the stream's 499.15 ms solve-time increase. Their
valid partial evidence displaces the preceding cheaper completion path.

**Next target: apply the existing `cnf_pool_priority.try_pools` before committing
to partial extraction.** Exact-prefix causal probes confirm complete negative-pool
hits for both edits without fresh expansion. The exposed case-70 probe misses.
Use those results to design the gate, preserve the successful case-70 transfer,
and measure failed pool checks on a new frozen stream. Do not infer a total-cost
win from fewer native dispatches: fresh case 70 uses 89 instead of 115 but takes
slightly longer.

Random-three consumes 73.74% of fresh solve time and remains the largest general
cost. The two unnecessary edit expansions are the most concrete immediate reuse
opportunity. The 64-node extraction frontier and nine unsupported endpoints in
the larger diagnostic remain secondary questions after restoring cheap complete
reuse priority. Resume `experiments/results/cnf-whole-proof-reuse/checkpoint.json`.
No efficient arbitrary-CNF closure or new native proof authority is claimed.

## Previous investigation: use an earlier whole-CNF proof on an unresolved edit

[Whole-input affine completion](whole-input-affine-completion.md) closes the
preceding case-43 gap: 16 checked affine assignments all fail a remaining clause.
The existing extension authority publishes UNSAT without native expansion.
Exposed coverage grows from 39 to 40 of 48 distinct roots. On the new 96/120
stream no completion is eligible, so answers, proof bytes and retained state
match ordered probing. Broader coverage on new inputs remains open.
Exposed solve mean improves 6.94% and selected retained Python state falls
6.62%; fresh solve mean regresses 0.46%. The combined policy still costs 16.99%
more fresh solve time than the original binary route. Preserve this tradeoff.

**Next target: automatically transfer the checked proof from fresh case 69 to
its still-unresolved edit 70.** The integrated policy solves case 69 in 246
dispatches; case 70 then exhausts 256. Inspect the lost source support and
surviving branches, and use the existing partial-cover extraction/recomposition
machinery before inventing a new proof rule. Recognition must receive only
source CNFs and earlier checked proofs, with no supplied guard or future answer.
Charge extraction, correspondence, failed support matching and full recomposition.

Random-three attempts consume 72.95% of fresh solve time and all twelve exhaust the cap;
their eight distinct roots have no extracted equations. Two edited mixed roots
(61 and 70) are also unresolved and have no direct affine core. The case-69 proof
gives case 70 a concrete prior result to reuse. Case 61 precedes its base root's
eventual completion on repeat, so that later proof cannot justify earlier reuse.

Resume `experiments/results/cnf-whole-affine/checkpoint.json`, its exact-prefix
profiles and `frontier-inspection.json`. Affine enumeration retains its `2^d`
cost and eight-free-coordinate cap. No production default changes, compact
closure result or unrestricted-SAT guarantee follows.

## Previous investigation: use the consistent affine core already discovered

[Canonical probe preparation](ordered-probe-preparation.md) saves 4.54% solve
mean on a fresh holdout against whole-clause lookahead, with identical decisions
and proof bytes. Exposed timing is mixed. Even the improved policy remains
20.20% slower than the original binary route on the fresh stream, with 12.83%
more native payload. It completes 39/48 distinct roots instead of 38/48; the
local preparation specialization itself adds no coverage.

**Next target: whole-input affine completion on unresolved case 43.** Checked
extraction finds 111 consistent equations of rank 108 on 112 actual variables,
leaving four free bits and 61 coupling clauses. There are only 16 affine-space
candidates. The current top-level probe ignores consistent spaces, but
`cnf_affine_completion.py` and `cnf_affine_negative.py` already provide completion
and checked negative exhaustion up to eight free coordinates. Test their
integration with full-source witness checks, separate negative authority, charged
recognition, fresh validation and cold replay. Do not implement a new proof rule
before examining these existing modules.

Eight other fresh unresolved roots have no extracted affine equations and remain
controls. Their twelve random-three attempts all exhaust the native cap. This
structural integration is more promising than another small preparation saving;
it does not cover arbitrary CNF or remove the exponential free-dimension bound.

Resume `experiments/results/cnf-ordered-probe/checkpoint.json` and its
`frontier-inspection.json`. The 16-candidate observation is verified rank
information, not a newly asserted verdict for case 43.

## Previous investigation: price failed whole-clause probes before adding more

[Whole-input lookahead](whole-cnf-lookahead.md) tests 72 fresh exposed and 72
prospective holdout queries with no supplied guard or family label. Random 3-CNF
is the largest initial cost. Wider-clause probing reduces expansion dispatches
by 12.1% exposed and 16.6% held out, and native payload by 2.5% and 7.4%.
However, solve time rises 10.08% and 3.71%. Keep the policy optional.

One held-out base query completes earlier (251 dispatches rather than a stop at
256), enabling cheap reuse on its edit. Both policies eventually complete the
same 47 of 48 distinct held-out roots. Case 1 remains unresolved; this is no
new tractable class or distinct-root coverage improvement. The modest held-out
complete-worker gain comes partly from cheaper replay and does not erase the
solve-time regression.

**Next target:** reduce the 310 exposed and 499 held-out inconclusive probe
attempts through a cheap source-derived gate and reuse of prepared cofactors.
Inspect unit-chain seeds, repeated restriction/canonicalization and checked
cofactor hits. Preserve exact cached-negative authority even when propagation
would miss. Use the unresolved held-out case 1 and early-completion case 36 to
explain interactions, then freeze new validation inputs before tuning. The
shared-mixture regression must be included; do not route by generator labels.

Resume `experiments/results/cnf-whole-discovery/checkpoint.json`. The study
preserves raw trials, exact-prefix profiles, explicit unknowns and the cumulative
proof archive. The two previous partial-cover refinements remain failed defaults.

## Previous investigation: return to discovery on unlabelled whole CNFs

[Live finer-origin admission](refined-proof-origins.md) tests the preceding
hypothesis. The case-15 cover is selected for cases 19/20, but native expansion
stays at **32 dispatches and five missing leaves**. Preparation/query mean
regresses **2.39%** (three pairs worse), hints grow **45.89%**, and native payload
grows **1.13%**. Complete-worker mean is 0.65% lower with mixed pairs; it does
not establish a consistent total-cost advantage. Reject this admission rule
as a default and retain the counterexample.

**Next primary target: discover useful conditions on unlabelled whole CNFs.**
Freeze fresh seeds for the existing larger-mixture generators, record novelty
against the preserved archive, and compare cold discovery with later reuse on
base/edit/repeat streams. Use the current solver and inspect existing automatic
guard recognizers under matched budgets, with no supplied assignments or
future answers. Identify the largest remaining shared-variable interaction
and implement one checkable decomposition that explains it. Preserve unknowns
and charge failed recognition and exact recomposition.

Consult `cnf_larger_mixtures.py`, `compare_cnf_affine_probe_safe.py`,
`cnf_pattern_inventory.py`, `cnf_ranked_binary_targets.py`, `cnf_local_guard.py`
and `cnf_alternative_guard.py` before designing another recognizer. The latest
23-source stream measures already solved conditional queries and cannot
establish progress in whole-input structural coverage.

The ranking lesson is concrete: more intact leaves can refine only already
solved branches. Case 19 pays for an extra extraction and publications while
its missing residual is unchanged; case 20's smaller residual still takes
three dispatches in total. Future reuse selection must price the remaining
computations and certificate construction, not intact-leaf counts alone.
Resume `experiments/results/cnf-refined-origins/checkpoint.json`. All previous
results and alternative valid proofs are retained; production defaults stay.

## Previous investigation: price finer reusable branches after recomposition

[Missing-leaf handoff](missing-leaf-handoff.md) removes five duplicate
normalizations, saving 3,133 literal visits and 13,573 key-serialization bytes
with identical native proofs and checks. Nevertheless, preparation/query mean
regresses **2.29%**, and complete-worker mean **2.58%**; both have two wins and
two losses. Keep optional. Selected endpoint Python state is 11,655 bytes
smaller; stored bytes and structural coverage are unchanged.

**Next target: test a finer surviving subbranch from an earlier recomposed
proof.** The actual case-15 proof adds a split inside case 20's failed support.
With the same checked unit prefix, one missing residual changes from 693 to
683 literals (113 to 112 variables), while the other stays at 673 literals.
Missing-leaf counts remain two. This is a small hypothesis requiring a complete
cost comparison, including extra extraction, hints and branch publication.

Do not blindly admit every recomposed root: the actual case-19 proof gives
case 20 exactly the current missing residuals. The three prospective pairs
all preserve missing-leaf counts. Their diagnostic is chronological and uses
actual proof bytes, but is not an evaluated online admission policy. Retain
the negative control. If the finer branch does not pay, prioritize broader
unlabelled guard/map discovery over further preparation micro-optimizations.

Resume `experiments/results/cnf-leaf-handoff/checkpoint.json` and its bound
`origin-followup.json`. Native acquisition/checking, automatic useful guards,
variable correspondence and unrestricted compact closure remain unresolved.
No production default changes.

## Previous investigation: pass prepared missing leaves into native acquisition

[Indexed origin carry](carried-clause-origins.md) preserves exact extracted
bundles and all native proofs while skipping **2,647 unchanged representatives**.
Cover-phase mean improves **8.36%** in all four pairs. However, preparation plus
query regresses **1.79%** overall (two wins, two losses), and complete-worker
mean regresses **6.32%**. Keep optional and retain that total-cost failure.
Map copies and indexing are charged; endpoint state and stored bytes are equal.

**Next primary target: repeated input normalization at the five missing-leaf
acquisitions.** Partial traversal already has a conditioned formula/name/key
triple, then `_visit` reconstructs it. The case 15 profile still has 27
normalizations, about 24 of 62 instrumented milliseconds; verification accounts
for about 17 ms and overlaps those costs. Investigate explicit call-local
preparation transport at this producer/consumer boundary, keeping every source
and native proof check. Preserve SAT witness lifting and the shared budget.

The existing [general normalization cache](query-canonicalization-reuse.md)
already lost after lookup/sizing/validation overhead. Do not reintroduce it
without new evidence. The indexed extractor still copies O(m) map containers
on affected transitions; improving that is secondary to the remaining measured
acquisition/checking costs. Automatic guards/maps and unrestricted bounds stay
open.

Resume `experiments/results/cnf-carried-origins/checkpoint.json`. No new native
identities are needed; the cumulative archive is reused. Raw pair regressions,
all original representatives and identical-proof diagnostics are preserved.

## Previous investigation: reuse provenance during cold cover extraction

[Shared partial preparation](prepared-partial-recomposition.md) avoids six
repeated leaf preparations and one unchanged frame while preserving **identical
native payloads, hints, origins, decisions and 32 dispatches**. Preparation plus
query improves **0.98%** on average against the previous partial route, with
three pairs improving and one regressing. The native-baseline difference is
only **0.06%**; treat it as a local tie. No default change.

**Next primary target: original-clause provenance in cold conditional-cover
extraction.** Cases 7/guard 4 and 15/guard 3 still cost **17.46/24.86 ms**, versus
baseline **9.10/17.39 ms**. Each first-use extraction takes about 20 instrumented
milliseconds; cold queries make roughly 2,000 restriction calls while the
extractor rescans the full source at every proof node. Carry original reason
bindings through unit, split and component transitions, reusing unchanged
residuals and checking deterministic duplicate representatives and assumptions.
Consult the existing preimage-reuse machinery before creating another mapper.

The later transfers avoid discovery and remain cheaper. Preserve the SAT
control, extraction bounds and unsupported endpoints; price setup, retained
provenance, native checks and subsequent reuse. The prepared composer now
charges its root canonicalization explicitly; its seven fewer normalization
calls are independently confirmed by identical-proof profiles.

Resume `experiments/results/cnf-prepared-partial/checkpoint.json`. No new native
identities are required: reuse the preceding cumulative archive. Automatic
useful guards/maps, new origins after recomposition and unrestricted bounds
remain open.

## Previous investigation: share residual preparation in partial recomposition

[Partial covers](partial-cover-recomposition.md) now retain intact supports and
solve only failed leaves, with checked split/unit recomposition and full SAT
witness lifting. Four attempts include one SAT control. Dispatches fall **39
to 32**, preparation plus query improves **3.99%** against complete-cover reuse,
and native payload is **2.80% below baseline**. Yet preparation plus query stays
**2.45% above baseline**; complete-worker time does not improve. Keep optional.

**Next primary target: duplicate conditioned-residual construction and support
checking.** Cold extraction plus recomposition still makes case 15/guard 3
**26.13 ms**, versus baseline **17.14 ms**. A diagnostic profile finds 38
canonicalization calls including 29 normalizations; normalization is about
26 of 72 profiled milliseconds. Reuse immutable residuals/maps and prepared
support membership inside traversal and leaf publication, retaining every
native certificate check. Carry preparation counters across resets explicitly.

Later cases 19/20 beat baseline at **15.39/21.48 ms** versus **17.88/23.61 ms**,
so retain cold and warm distinctions and the case 7 SAT regression. The partial
stream currently learns no new origins from recomposition; it uses the older
three-leaf cover, not the posthoc four-leaf examples from the previous stream.
Extending that origin policy is a secondary coverage/storage tradeoff.

Resume `experiments/results/cnf-partial-cover/checkpoint.json`. The exact
chronological branches, paired costs and identical-proof diagnostic profile
are preserved. Automatic guards/maps and unrestricted bounds remain open.

## Previous investigation: reuse intact branches of partially broken covers

[Unit gating](unit-cover-gate.md) fixes the largest regression: case 6/guard 3
returns to a native unit proof, **17.77 to 3.30 ms**, while the two useful later
transfers survive. Gated learning saves **5.53%** preparation-plus-query time
against ungated learning but remains **6.76% slower** than baseline. The
gate-only ablation preserves identical native proofs; its fewer dispatches
are bookkeeping savings. Keep the learned route experimental.

**Next primary target: exact partial-cover recomposition on cases 19/20,
guard 3.** A single deleted clause breaks one leaf while three of four earlier
supports remain valid (origin 15 for target 19, origin 19 for target 20).
Current all-or-nothing matching discards that opportunity and reacquires the
entire target. Query means are 24.83/31.48 ms against baseline 17.67/22.71 ms.

Preserve checked intact leaves and solve only failed branches, with explicit
path guards, source maps and unit-prefix binding. A negative root needs all
reachable branches; a positive leaf needs full-target witness lifting. Price
the complete construction and discovery, rather than counting matched leaves
as a solved query. Retain the nearby SAT controls and all earlier authority.
Automatic guards/maps and unrestricted bounds remain open.

Resume `experiments/results/cnf-unit-cover-gate/checkpoint.json`.
`next-target.json` binds exact missing clauses, prior origins and the ordered
stream; it is diagnostic evidence, not a measured partial-cover algorithm.

## Previous investigation: avoid costly cover discovery on cheap unit conflicts

[Learned conditional covers](learned-conditional-covers.md) transfer earlier
source-bound reasons to three later cofactors after the existing negative pool
misses. Native expansion dispatches fall **43 to 33**, with all branch guards
checked and no future answers seeded. However, preparation-plus-query mean is
**7.74% worse**, native payload grows 1.95%, and active hints grow from 11,505 to
54,396 bytes. All four paired repeats regress on preparation plus query. Keep
the policy experimental; there is no new whole-input coverage cell.

**Next primary target: preserve a cheap full-target unit conflict before lazy
cover extraction and recomposition.** Case 6/guard 3 was already a one-expansion
unit refutation; the learned cover makes it **3.57 to 17.60 ms**. Failed first
discoveries at cases 7/guard 4 (SAT) and 9/guard 5 add about 6 ms each. Later
transfer at case 16/guards 3 and 4 saves only about 1.43 and 2.37 ms. Price a
checked unit gate on misses, sharing its prefix with fallback when possible.
Then test amortization over more distinct supported edits.

Ready covers also retain origin keys and name maps despite self-contained unit
proofs; separating active certificates from archived provenance is a secondary
space opportunity. Deferred origins still need exact reconstruction bindings.
Automatic useful guards/maps, arbitrary-edit closure and general bounds remain
open. Resume `experiments/results/cnf-learned-conditional/checkpoint.json`;
`analysis.json` retains paired per-query costs and every transfer certificate.

## Previous investigation: transfer conditional supports across nearby edits

[Shared template preparation](template-preparation.md) removes 71 duplicate
checks, restrictions and canonicalizations with identical proofs, routes,
storage and native verification. Four alternating pairs reduce local
preparation-plus-query means **14.35%**, but complete-worker time does not improve.
The operation uses immutable source/guard bindings within one call; it adds
temporary source-copy space and changes no default solver or coverage class.

**Next primary target: conditional supports in five related native fallbacks.**
Cases 4/guards 3 and 4, 15/guard 3, and 16/guards 3 and 4 consume **56.28% of
native-fallback query time**, with 22 expansion dispatches. Cases 15 and 16 are
two-clause deletions from case 4. Determine which earlier source-bound reasons
survive the later edits and whether they can improve on the existing negative
pool, which already misses here. Keep the SAT case 7/guard 4 as a control.

Preserve branch assumptions and explicit variable maps. Charge discovery,
recognition, full-target recomposition and cold verification; only earlier
stream results may supply authority. This tests reusable patterns across edits
instead of presuming that all needed supports remain available. Automatic guard
selection, wider correspondence and whole-input coverage remain open.

Resume `experiments/results/cnf-template-preparation/checkpoint.json`.
`next-target.json` binds the source queries, chronological availability and
ranked costs. The new checkpoint reuses the previous immutable cumulative
archive because every measured native proof already exists there.

## Previous investigation: share template preparation already held by the caller

[Early checked-pool lookup](pool-priority.md) recovers eight negative-core and
four witness hits before recovery preparation. With ordinary native fallback,
all proof bytes and the selected-container memory endpoint remain identical to
compact reuse. Two-order preparation-plus-query mean falls **2.50%**; complete
worker time is essentially unchanged, and native-only total query preparation
remains slightly cheaper. Recovery still grows time and stored payload. Keep
these scheduling options experimental; fewer dispatch counts add no coverage.

**Next primary target: reuse the live source/assignment/cofactor during the
71 template publications.** The query has already restricted, canonicalized
and checked that exact target. `materialize` repeats source containment,
restriction and canonicalization. There are 173 template checks: 102 uncached
initial checks plus 71 repeated checks. An instrumented query-only profile puts
normalization and template materialization at about 0.297 and 0.295 seconds
cumulatively; these overlap and do not predict a speedup.

Preserve immutable source and assignment bindings, the exact compact-name map,
and all native proof checks. Prefer passing already computed preparation in
this call over a cross-query cache with new invalidation rules. Charge copying,
retained state, misses, checking and cold replay. Full proof serialization and
cumulative native storage remain open even if this construction becomes cheaper.

Resume `experiments/results/cnf-pool-priority/checkpoint.json`. `profile.json`
binds an identical-proof diagnostic run. `analysis.json` includes failed-probe
counters before fallback resets, all paired measurements and the recovery
regressions. The new four edits still use supplied guards and correspondence;
this is a construction opportunity, not efficient arbitrary-SAT coverage.

## Previous investigation: preserve cheap pool hits before conditional recovery

[Missing-clause recovery](conditional-support-recovery.md) identifies one extra
forced value after unit propagation in three exposed hard cofactors. The SAT
case falls from six expansions to two. The rule is existing deletion-guard /
failed-literal reasoning, with native proof and full witness reconstruction.
For a unit-refutable strengthening missing only one clause, a saturated
nonconflicting unit prefix leaves at most one new failed literal.

The full cost comparison rejects enabling the route unconditionally. Screened
recovery reduces 90-query expansions 36 to 17 but raises preparation-plus-query
time and stored payload. A narrower ordinary-fallback gate gives **36 to 30**
expansions, yet **10.66% more preparation-plus-query time** and **13.05% more
native payload**. All decisions remain identical. No default changes.

**Next primary target: preserve checked negative-core and witness-pool hits
before recovery preparation.** Additional case 12 / guard 3 already reuses a
negative core in one expansion: recovery increases publication from one node
(4,086 serialized proof bytes) to nine (22,101). Cases 13 / 4 and 14 / 4 already
have witness hits. For genuine remaining recovery wins, compare the cost of
full native reconstruction with existing checked guard composition. Keep
recognition, maintenance and cold validation in the comparison.

Resume `experiments/results/cnf-conditional-recovery/checkpoint.json`.
`analysis.json` retains bound sources, guards and both policies' counters; its
largest regressions are more informative than the smallest expansion counts.
The prior fourteen misses, failed other-template matching and the positive case
are preserved. Supplied guards/maps and arbitrary-CNF coverage remain open.

## Previous investigation: recover after missing reasons, retaining positive cases

[Conditional unit supports](conditional-unit-support.md) yield six source-bound
refutations with 3–28 clauses. Both these templates and the stronger conditioned
causal-core baseline reuse the same **40 of 66 supplied conditional queries**;
query expansions fall 68 to 28, but preparation-plus-query time regresses against
native solving. There is no incremental coverage win over conditioned cores.
The common donor costs nine expansions; causal preparation costs five more.

Separating runtime certificates from archived provenance reduces template hints
**51,929 to 11,505 bytes**, with identical native proofs. Proof delta plus hints
is 75,014 bytes, still above native-only 65,359. Native target CNFs continue to
accumulate. This establishes a representation saving, not general memory or
runtime improvement. Cold hint validation is charged separately from the
workers' cold answer replay; the full provenance remains preserved.

**Next primary target: bounded alternative-reason recovery and witness reuse
when a small edit destroys a support.** The largest remaining UNSAT miss is
case 4 (`delete-reason-2`), template 4: five expansions, 13.94 ms in the first
order. Case 7 (`random-three-deletions-1`), template 4 uses six expansions and is
SAT: never infer a negative answer from the donor's remaining structure. Compare
both with native fallback and the existing conditioned causal bank. Automatic
guard selection and variable correspondence are still supplied, unpriced gaps.

Resume `experiments/results/cnf-conditional-unit-support/checkpoint.json`.
`analysis.json` preserves fourteen fallback sources, guards, counters and new IDs.
Use the protocol prefix plus preparation and preceding query additions only.
Retain the two-order timing regressions, the oversized metadata candidate and
all existing native/extension proofs. This adds no whole-input coverage cell.

## Previous investigation: conditional mixed-width supports before full reconstruction

[Direct joint-prefix reuse](joint-prefix-reuse.md) removes two redundant
reconstructions from each edit group, reusing a canonical triple already live in
the caller. The largest query falls from **116 to 114 normalizations** and **103
to 101 restrictions**, with all 51 verification calls intact. Query means fall
2.98% on controls and 1.42% on nearby new edits, but no-hit queries also vary and
one isolated-branch order regresses. Treat the exact work reduction as established;
these two-order timings do not establish a robust runtime speedup. Proof bytes,
persistent storage, checked-object endpoints and coverage remain unchanged.

**Next primary target: recognize transferable conditional unit supports in the
remaining mixed-width branch before constructing full residual proofs.** Its
checked DAG contains **five split and nine unit nodes**, all newly acquired. The
unit nodes store 6,495 literal occurrences; their local reasons use 148, comprising
18 unit, 47 binary and 12 ternary clauses across the nine nodes. Six unit nodes
end in conflicts; three have child obligations. This is potential structure to
investigate, not a 148-literal unconditional core or a proven compression ratio.

Census explicit ancestor conditions and original-variable maps, then compare
bounded recognition/transport against the existing causal support and core bank.
Test nearby edits and sign changes, including source membership failures and
missing child evidence. A match must preserve its conditions and full-source
certificate checks. Charge discovery, mapping, validation, materialization and
cold replay. This offers a larger possible reduction than removing another two
canonicalizations, but cross-input reuse has not yet been demonstrated.

Resume `experiments/results/cnf-joint-prefix/checkpoint.json`. In `next-target.json`,
the `novel` observation (query position **0**), acquisition index **2**, binds
**125 variables, 258 ternary and 56 binary clauses; 886 literal occurrences**,
budget **247** and **three earlier native IDs**. The `proof_census` records the
checked reachable DAG. Restore only its bound prefix and those IDs; replay the
preceding probe/branch for warm pools. The final union must never seed comparison
queries. The largest new query is 86.36 ms and keeps branch counts `[1,9,1,6,1,3]`
after eight probe expansions. Automatic correspondence, whole-source composition,
useful arbitrary-CNF coverage, storage growth and cold replay remain open.

## Previous checkpoint: reuse checked order, then attack mixed-branch construction

[Fused causal reconstruction](preimage-fusion.md) exploits exact order invariants:
restriction preserves order within each clause. After the residual clauses are
sorted, monotone variable compaction preserves their lexicographic order too.
It shares untouched parent tuples and maps selected child positions directly to
their first parent representative. There is only one duplicate reduced clause
in the exposed 26-request census, so broad duplicate compression was not the win.

The initial two-order comparison reduces query means by **5.53% on six controls**
and **5.65% on six new edits**. Six additional balanced pairs, including mode
setup, improve **6.32%** and **4.49%** respectively; one new-edit pair regresses.
Every expansion count, native proof byte and partition stays identical. Persistent
space and checked-object endpoint space are unchanged. Complete-worker means
change only **+0.27% / -0.16%**, with no robust end-to-end gain. A zero-hit isolated
branch has noisy timings, so its apparent changes are not attributed to fusion.
Keep the method optional and serial; this adds no coverage cell.

**Next primary target: shared source-bound conditioning and reason construction
inside the remaining nine-expansion mixed branch.** The largest new query is
case 31's deletion: 89.04 ms in the initial fused mean, with branch expansion
counts **[1,9,1,6,1,3]** after eight probe expansions. Its profile still has **116
normalizations**, **103 restrictions** and **51 verification calls**. Inspect
`force_all` and `excluded_context`: prefix preparation, backwards parent
construction and excluded-path compilation revisit related conditioned sources.
First census exact source/assignment/renaming pairs and live consumers; then test
a bounded direct handoff or shared immutable description. Native verification
must still independently check every edge. Do not introduce another broad memo
without measuring a sufficiently narrow producer/consumer pattern.

Resume `experiments/results/cnf-preimage-fusion/checkpoint.json`. The `novel`
observation in `next-target.json`, query position **0**, acquisition index **2**,
binds **125 variables, 259 ternary clauses and 56 binary clauses; 889
literal occurrences**, budget **247**, and **three earlier native IDs** from its
bound trial delta. The target is absent. Restore only that prefix and those IDs;
replay the preceding probe/branch stream for warm pools. The final union must
never seed comparisons. The previous six-expansion source is retained under the
`controls` observation, acquisition index 4.

Automatic donors/maps, source-level composition, a useful partition of arbitrary
CNFs, persistent-space growth and cold replay remain larger general gaps. Local
construction savings do not establish compact or uniformly cheap SAT expansion.

## Previous checkpoint: repeated preparation in the remaining mixed branch

[Consequence priority](consequence-priority.md) reuses the checked two-polarity
cofactor probe before a single late binary consequence. It recovers the case-61
failure while preserving the exposed joint benefit. Six new edits take **57
versus 63 joint expansions**, save **4.54% query time** and **3.91% native payload**.
They improve **3.34%** versus one-target timing, but controls still regress
**0.80%** versus that baseline. The optional policy adds no new coverage cell.

**Next primary target: repeated source-bound preparation and causal support
extraction around the remaining six-expansion branch.** The largest new query,
case 31's replacement, takes **32 / 27 / 25 expansions** under one-target / joint /
priority, but priority's **94.12 ms** is slower than joint's **91.25 ms**. Its
profile records **142 normalizations**, **6,353 restriction calls**, seven
negative-reuse calls and 26 causal preimage calls. Identify repeated conditioned
clauses and reason/support descriptions, then test exact reuse with every
source, assignment and availability check intact. Earlier broad cofactor and
normalization memos already regressed; do not repeat them without a narrower
producer/consumer pattern and a measured total-cost case.

Resume `experiments/results/cnf-consequence-priority/checkpoint.json`. In its
`next-target.json`, the `novel` observation (query position **1**) has acquisition
index **4**: **125 variables, 257 ternary, 60 binary and one unit clause; 892
literal occurrences**. It needs six expansions with a budget of **242**. Restore
its prefix plus **42 earlier native IDs** from the bound trial delta. The target
was absent. This reconstructs persistent availability, not warm pools; replay
the preceding stream to recover those. The final union must never seed comparisons.

The case-61 streams restore baseline-identical proof bytes, so their **4 -> 3**
expansion reduction partly reflects compiling rather than visiting a unit-refuted
child. Keep publications and total time visible. General defaults remain unchanged;
automatic donors/maps, source recomposition, cold audit/storage and unrestricted
interaction bounds remain open.

## Previous checkpoint: price the surviving mixed-width continuation

[Joint consequences](joint-binary-consequences.md) reduce the exposed branch from
**9 to 4 expansions**, with **24.10% less query time** and **24.86% less new proof
payload**; both sign variants improve too. A same-discovery, single-selected
ablation takes six expansions. The recognizer shares one graph, inspects at most
eight ranked targets and retains at most two consequences not already implied by
earlier selections. Existing native units/splits independently certify them.

**Next primary target: a cheap structural acceptance test for consequences whose
surviving full-CNF continuation is actually useful.** On six new edits, expansions
fall **58 -> 55**, but query time rises **4.05%** and proof payload **8.65%**.
The case-61 deletion is the counterexample: **4 -> 7 expansions**, **6.58 -> 16.06
ms**, and **24,340 -> 71,373 new bytes**. The following replacement remains one
expansion but also slows, with different stored intermediate evidence. Run a
single-selected versus joint ablation there, then compare any acceptance test on
both helpful and harmful cases. Preserve propagation/cache priority and charge
assessment and proof construction. General defaults remain unchanged.

The largest new query is case 31's deletion: **29 -> 23 expansions**, **84.15 ->
76.14 ms**, with joint branch counts **[1,4,1,5,1,3]** after eight probe expansions.
Its profile has **104 normalizations** and **23 discovery calls**; canonicalization
and proof construction outweigh graph recognition in instrumented time. Reuse
exact conditioning/preparation where justified; a broad cofactor memo already
failed its total-cost test. Do not replace discovery work with repeated unrelated
hardening or assume fewer expansion-counter increments imply less total work.

Resume `experiments/results/cnf-joint-backbone/checkpoint.json`. Its
`next-target.json` binds the exposed branch and largest query, exact prefixes,
earlier native IDs, paths and profiles. The informative regression is the frozen
`novel-61-{mode}-0` stream, seeded from protocol prefix `61`; the final union must
not seed comparison queries. All previous payloads and unsuccessful trials remain
preserved. Automatic donor/map selection, source recomposition, cold audit and
storage costs remain open. No new whole-source coverage or unrestricted bound
is claimed.

## Previous checkpoint: combine useful binary consequences

[Live native fallback](live-fallback.md) makes the existing routing decision before
unwinding the search stack. The exposed replacement takes **11 instead of 17**
expansions and **20.71% less query time**, with the same native proof bytes.
Six controls improve **2.58%**, but six new edits never need native fallback and
regress **3.89%** in query time. Counts and all paired proof deltas/sidecars match
except the six avoided control expansions. General defaults remain unchanged.

**Next primary target: joint propagation of independently forced binary values in
the dominant mixed-width branch.** Reuse a source-bound implication graph and
several checked paths when their consequences cover different variables. Test
whether a bounded consequence set reduces repeated restrictions, graph discovery
or ordinary splits enough to pay for recognition and proof compilation. Compare
with one-target and two-target policies. More deductions can still enlarge the
certificate or choose a worse continuation; retain these counterexamples.

The largest fresh query still uses **29 expansions** and takes **81.82/87.31 ms**
under restart/live routing. Its branch counts are **[1,9,1,6,1,3]** after the initial
eight expansions. The nine-expansion branch has **125 variables, 57 binary and
261 ternary clauses, 897 literal occurrences**. In
`experiments/results/cnf-live-fallback/next-target.json`, the `novel` capture's
acquisition at index **2** binds the exact source and pre-acquisition prefix:
the historical seed plus three earlier native IDs from the bound trial delta.
Its root is absent, and 247 expansions remain. Warm hint pools are not serialized.

Native fallback continuation is now a narrow optional mechanism, not the next
structural bottleneck. It keeps unfinished frames only during the synchronous
call; process loss discards them. The frame census is not a peak-memory bound,
and complete-worker timing changes have mixed signs. Automatic donor/map
selection, original-source recomposition and cold-audit/storage costs remain
separate larger obligations. Resume
`experiments/results/cnf-live-fallback/checkpoint.json`: 75,724 native records
and 258 partition records, with prior authority preserved. No new whole-input
coverage or unrestricted bound is claimed.

## Previous checkpoint: preserve unfinished acquisition work

[Bounded second-target recognition](binary-target-fallback.md) finds a checked
binary consequence missed by the first target. The exposed branch and sign
variants still need nine expansions. On six new edits the optional policy takes
**69 -> 60 expansions** and reduces query time **8.29%**, with both orders better;
complete measured worker time improves only **0.61%**. Controls regress **1.14%**,
and the complemented branch regresses **3.27%**. Defaults remain unchanged.

**Next primary target: reuse the unfinished continuation across probe and native
fallback.** The main saving occurs in new case 61's replacement, which now finishes
within the eight-expansion probe. A bound posthoc ablation gives **11 -> 8** direct
expansions but **17 -> 8** through the probe/restart wrapper. The baseline uses
six extra expansions relative to direct acquisition even after retaining completed
proofs; the net difference need not consist only of identical repeated frames. Continuation loss was already observed in the earlier probe study; this
exact case offers a narrow comparison of restart, direct solving and resumption.

Bind retained frames to exact source, policy and solver state; unresolved frames
must not enter the checked answer archive. Charge memory, invalidation, publication
and cold reconstruction. Test both verdicts, budget stops and source edits. Keep
state bounded and discard unusable frames when partition routing is selected.
This can help across categories without assuming every CNF has cheap structure.

`experiments/results/cnf-binary-interactions/next-target.json` binds the boundary
ablation and the largest query's profiles and historical prefixes. Direct-ablation
proof bytes are subsets of the frozen, independently checked trial deltas. The
largest query remains case 31's deletion at **83.67/84.72 ms**, with 29 expansions
in either policy. More recognized consequences do not necessarily reduce proof
size: publications there rise from 29 to 30. Consequence utility and compression
remain secondary targets; automatic donors/maps and original-source composition
remain larger coverage gaps. Full cold auditing still dominates the complete
worker, so it must remain distinct from query latency.

Resume `experiments/results/cnf-binary-interactions/checkpoint.json`: **75,677
native records**, **242 partition records**, all prior extension authority intact.
The checkpoint adds no whole-input decision coverage or unrestricted-SAT bound.

## Previous checkpoint: the remaining binary/ternary branch

[Shared partition preparation](partition-preparation.md) replaces four identical
branch constructions with one shared producer preparation and one independent
reconstruction. On six new edits, binary-frequency query time falls **6.15%** and
cofactor-handoff query time **4.01%**, with both orders improving. Native payloads,
models, partitions and expansions match each parent. A single returned preparation
graph is **35.72% smaller**; process peak memory is not established. Complete
new-edit worker time regresses **1.07% / 0.23%**, so defaults remain unchanged.

**Next primary target: discover useful structure in the dominant residual branch.**
The prepared binary-frequency policy's largest query takes 82.51 ms. Its second
first-false branch takes nine expansions and 22.51 ms in the first trial. The
saved input has **125 variables, 57 binary clauses and 263 ternary clauses**.
Investigate a compact checked consequence set, useful decomposition or shared
subproof across that interaction. Compare existing bounded recognizers first;
charge recognition, remaining search and proof construction. Inconclusive
propagation supplies preparation only, and any result still needs exact source
recomposition.

`experiments/results/cnf-partition-preparation/next-target.json` binds all four
profiles and a `branch_candidate` captured before acquisition. Its historical
prefix plus **three** earlier rows from the bound trial delta reconstruct persistent
availability. A fresh reader verifies them and confirms the target is absent.
The target has 247 expansions left in the shared budget. Warm transient pools are
not serialized. Use this seed, not the final union containing the answer.

The cheaper prepared policy has branch expansions `[1,9,1,6,1,3]`; prepared
cofactor handoff has `[1,9,1,7,1,4]`. Probe admission and continuation choice remain
open. Cold replay and sidecar representation dominate the complete measured worker,
which includes full auditing; these costs are distinct from query latency.
Automatic donor/map selection and original-source coverage remain broader gaps.

Resume `experiments/results/cnf-partition-preparation/checkpoint.json`: **75,508
native records**, with all older authority intact. This adds no tractable class
or uniform unrestricted-SAT expansion guarantee.

## Previous checkpoint: share partition preparation

The [direct cofactor handoff](cofactor-handoff.md) avoids unrelated memo lookups
and reuses three nonconflicting unit propagations on six new edits. Query time
falls **2.66% on the mean, with both orders improving**, and identical models, proof bytes, partitions
and expansions. Complete measured worker time changes **+0.15% with mixed signs**.
The optional mechanism does not fix the routing regression: new edits still take
55 versus 53 expansions, 17.39% more query time and 38.87% more native payload
than binary-frequency routing. General defaults remain unchanged.

**Next primary target: repeated first-false partition construction.** The largest
fresh handoff query takes **108.98 ms**. An untimed audit finds four identical
six-branch structures per query, at premise publication, acquisition, sidecar
construction and checking. The same four calls occur under binary-frequency
routing. Avoid constructing unused premise branches and share immutable preparation
between acquisition and sidecar construction. Keep the independent record checker,
fresh prerequisite lookups and exact source/ordered-clause/guard/name-map bindings.
Charge retained space, invalidation, malformed-sidecar checks and cold replay.
This opportunity can help the cheaper policy without requiring two-polarity routing.

`experiments/results/cnf-cofactor-handoff/next-target.json` preserves the source,
exact pre-query prefix, all three profiles and duplicate-structure audit. The
selected deletion has no extra earlier-query publications. Handoff reduces native
normalizations 130 -> 127 and propagations 33 -> 31, but publications remain 39;
binary-frequency routing uses 108, 24 and 29 respectively. Probe admission and
the surviving continuation remain the next search-policy gap. Cold replay and
sidecar representation dominate the complete measured worker, which includes
auditing costs and must not be equated with query latency.

Resume `experiments/results/cnf-cofactor-handoff/checkpoint.json`: **75,416 native
records** with all earlier authority preserved. This acquisition study adds no
whole-source coverage cell or uniformly polynomial unrestricted-SAT bound.

## Previous checkpoint: avoid broad lookup for prepared work

The [prepared-cofactor memo](prepared-cofactors.md) reuses 13 exact normalization
results on six new edits, reducing normalizer input-literal visits **7.34%**.
Every proof payload, decision and expansion is identical to two-polarity routing.
Mean query time nevertheless rises **0.75%, with both orders worse**. There are **101 misses
for 13 hits**, plus snapshots, validation, sizing and eviction. The bounded memo
remains an unsuccessful speed optimization. Persistent proof storage is unchanged.

**Next primary target: direct handoff of prepared cofactors and unit traces.**
The largest fresh prepared query takes **110.66 ms**. Its profile reduces native
normalization calls **130 -> 122**, while publication remains 39 and propagation 33.
Avoid checking unrelated consumers for a memo hit. Pass immutable prepared work
to the actual selected child, and investigate sharing a non-conflicting unit trace
without changing discovery priority or treating it as a SAT answer. Exact raw
source, assignment, variable-name map and checker bindings remain necessary.

`experiments/results/cnf-prepared-cofactors/next-target.json` binds the source,
pre-query prefix, paired profiles and a separate object-graph/probe audit. Only
three of 22 probe calls are unit-free, accounting for 2,378 literal visits, so a
trivial propagation screen is only a partial opportunity. Cached negative
cofactors still require lookup even when no unit deduction is possible.

The larger admission/continuation gap remains: binary-frequency routing takes 53
expansions on these edits, against 61 for both two-polarity arms. Changing only
normalization cannot eliminate the additional search/proof graph. Compare new
policies against both. Cold replay, automatic donors/maps, source recomposition
and compact sidecars remain wider gaps. Resume
`experiments/results/cnf-prepared-cofactors/checkpoint.json`.

## Previous checkpoint: price recognition and the surviving continuation

The [two-polarity experiment](bipolar-routing.md) fixes the saved blind spot:
the original residual, variable-76 sign flip and global complement all take
**four versus 30 expansions** under binary-frequency routing. Checking either
negative cofactor uses unchanged native proof rules and preserves completed
evidence. The false-only rule takes 30, four and five expansions respectively.

The rule is **not promoted**. Query time rises **21.31% on controls and 18.85% on
new edits**, with both orders worse. New-edit native payload grows **35.45%**.
More recognition can change the continuation unfavourably; a
successful local deduction does not establish a total-cost saving. Direct probe
work remains separate from the ordinary expansion counter.

**Next primary target: cheaper admission and shared prepared cofactors.**
Use the saved paired trials and posthoc profile in
`experiments/results/cnf-bipolar-routing/next-target.json`. The selected deletion
rises from **90.47 to 110.66 ms**. Native normalization calls rise **110 -> 130**,
publication calls **30 -> 39**, and propagation calls **23 -> 32**. These costs
overlap and reflect changed proof graphs too; do not assume every new call is
redundant. Investigate sharing exact prepared cofactors, normalization and checked
propagation evidence across discovery and acquisition. Compare any
bounded/event-driven propagation or continuation policy
against binary-frequency routing on fresh cases; preserve the regression and
charge proof checking and storage. A source-bound completed proof can be reused;
an inconclusive probe cannot be treated as a solved cofactor.

Full cold checking and reconstruction dominate complete measured worker time;
the new-edit complete-time mean changes only -0.37% with mixed order signs.
Reducing acquisition alone will not remove that historical replay cost.

Resume `experiments/results/cnf-bipolar-routing/checkpoint.json`. Donor selection
and maps remain supplied. Automatic retrieval, source composition and compact
sidecars are still broader coverage/storage gaps. No uniform arbitrary-SAT
efficiency or new tractable class follows from this local recognition change.

## Previous checkpoint: probe polarity at a verified routing counterexample

The [matched-state routing study](binary-routing.md) reproduces the saved
regression at **10 / 35 / 33 expansions** from identical persistent state.
Different earlier archives therefore do not explain this local policy effect.
A checked default-false cofactor guard was implemented and tested, but is **not
promoted**: it changes control expansions **88 -> 86** and new-edit expansions
**53 -> 52**, while query time rises **4.32% / 4.82%** in both orders. Extra
propagation, checking and direct publication outweigh those small count changes.

**Next primary target: the unprobed true cofactor at the first later divergence.**
The original policy selects variable 76; the guard chooses binary-forced variable
8. The false cofactor of 76 produces no unit deduction, while its true cofactor
has an independently checked contradiction after 39 forced assignments. Compare
both-polarity probing or justified polarity selection, with signed variants and
fresh edits. Charge both successes and misses; reuse checked cofactor evidence.

`experiments/results/cnf-binary-routing/next-target.json` binds the 285-clause,
784-literal residual and exact pre-target availability: the saved regression
prefix plus one checked earlier publication. Instrumentation stops before the
target is visited. A fresh reader verifies this prefix and confirms the target
root is absent. Do not seed the next comparison from the final union.

The false-only guard remains preserved as a failed optimization. Its expansion
counter excludes direct probe work, which is separately measured. No new
whole-source coverage is established. Automatic retrieval, source composition,
compact sidecars and cost-aware continuation selection remain open.

Resume `experiments/results/cnf-binary-routing/checkpoint.json`. The old source
and artifact ledgers, exploratory proofs, first-pass timings and repeated timing
stratum are retained. The general solver defaults stay unchanged.

## Previous checkpoint: choose a useful binary consequence without bad routing

[Bounded binary target rankings](ranked-binary-targets.md) resolve the saved
61-expansion branch in **25 expansions** with four total-frequency targets and
**nine** with one binary-frequency target. The earlier recognizer missed two
binary-forced literals because it targeted a different variable. Whole-cover
recognition, native proof checking and compilation remain unchanged.

On six new residual edits, binary-frequency targeting reduces expansions
**107 -> 51** and query time **49.19%** in both orders. Complete measured time
falls **2.63%**; compressed deltas plus raw sidecars shrink **199,383 -> 149,999
bytes**. All 16 targets already close under the baseline. Donors/maps remain
supplied, and the general affine policy stays unchanged.

**Next primary target: the replacement branch that regresses from 10 to 33
expansions.** Its whole query rises **28 -> 51**, although the preceding deletion
improves **86 -> 29**. The original policy's one reused previous-query proof is
still available and belongs to another branch. The costly branch's final proofs
have no seed or previous-query dependencies under any policy. Do not attribute
this regression to lost earlier results without a controlled test.

`experiments/results/cnf-ranked-binary-targets/next-target.json` binds the exact
source and persistent pre-branch state: the common prefix plus 35 earlier
publications, with the target root absent. Compare rankings from this identical
state, then inspect which cofactor structures distinguish useful and expensive
forced-variable choices. Fixed occurrence rankings can still pick a costly
continuation. On the exposed boundary, query time also regresses 1.63% despite
fewer expansions; full replay and warm reuse do not consistently improve.

Resume `experiments/results/cnf-ranked-binary-targets/checkpoint.json`.
**1,394 full / 76 focused tests**, 96 chronological attempts and cumulative replay
pass. Preserve **74,879 native records**, all previous payloads and alternate
trial proofs. Automatic retrieval, source composition and compact sidecars remain
coverage and storage gaps; this local result proves no uniform SAT bound.

## Previous checkpoint: the expensive branch left by a six-clause partition

[Probe before partitioning](probed-support-partition.md) protects cheap native
queries and retains checked proofs from a stopped eight-expansion probe. Probe
and subsequent work share the same 256-expansion limit. The previous six-clause
deletion boundary improves from **75 to 26 expansions**, including the probe;
unprobed partitioning takes 18. Two cheap controls finish within the probe.

Across three exposed targets and six fresh core-clause edits, combined query time
falls **46.23% / 12.49%**, in both orders. All nine targets already finish under
the baseline; no new whole-source coverage is claimed. Complete measured time
changes by only **0.46% / 0.53%**, with mixed paired signs on the exposed cases.
Endpoint checked objects shrink, but compressed deltas plus raw sidecars grow
**26.73% / 77.09%** and warm setup plus lookup regresses. Keep the affine baseline.

**Next primary target: the 61-expansion branch in fresh case 31's deletion.**
That query regresses to **86 versus 65 expansions**, while the replacement takes
28 versus 65. One branch accounts for **61 of 122 fresh-stream expansions**.
`experiments/results/cnf-probed-partition/next-branch.json` binds its source and
exact pre-branch proof state: the common prefix plus five earlier publications,
with the branch's own root absent. Unit propagation leaves 920 residual literals.
Inspect its shared-variable interactions and binary structure, then freeze one
recognition/decomposition comparison that can explain this regression and
transfer to fresh inputs. Do not import its final archived answer into the seed.

The second fresh query reuses one native proof first published by the first query;
formula changes also contribute, so this is not a causal runtime attribution.
Probe-then-native repeats five incomplete expansions on the exposed hard case:
completed proof retention does not preserve the search continuation. Automatic
donor/map discovery and source-level composition remain major coverage gaps;
continuation reuse and compact sidecars are supporting work.

Resume `experiments/results/cnf-probed-partition/checkpoint.json`. Validation:
**1,388 full / 70 focused tests**, 90 attempts, 24 new partition records and
**74,517 cumulative native records**. All prior sources, artifacts and proof
payloads are retained. Limits bound selected operations, not arbitrary-SAT time
or memory; supplied candidates still require automatic discovery evidence.

## Previous checkpoint: predict useful structure after missing-clause conditioning

[Transported support partitions](transported-support-partition.md) now combine
bounded causal extraction, checked transport and the existing first-false rule.
The prefix-controlled pilot uses three supplied historical residuals and six fixed
edits, with five arms and two opposite orders. Every baseline already solves all
nine targets; no source-level closure or automatic-discovery gain is claimed.

**The useful pattern is case 31:** five missing clauses produce three unit
conflicts and two branches that use binary-backbone reasoning. Reverse order cuts
historical expansions **69 to 17** and query time **0.14747 to 0.06522 seconds**.
Its combined edit stream improves **143 to 92 expansions**, **0.30542 to 0.22353
seconds**, entirely through the addition. Deletion leaves six missing clauses,
falls back, and regresses from 74 to 75 expansions. Cases 25 and 61 regress because
ordinary reuse already takes only two/four expansions.
The existing single-unresolved-branch screen rejects the useful case and accepts
the expensive alternatives. Aggregate screen query time rises **49.47% / 26.81%**.

**Next primary target: the six-missing-clause deletion boundary and branch costs.**
That deletion consumes 75 of 112 edit expansions and about half the reverse arm's
edit query time. Read-only prefix-plus-addition screening gives four unit conflicts
and two nonterminal branches in both orders, with no known native branch or
propagated-residual root. Neither remaining mixture is binary, Horn or dual-Horn.
`next-boundary.json` preserves this unsolved diagnostic. Freeze a new comparison
before increasing the cap; a repeated branch shape is not a cheapness guarantee.
Inspect exact archive hits and the binary implication/backbone structure exposed
by conditioning. Permit multiple unresolved branches when their combined cost is
credible; protect cheap native queries from expensive preparation. Charge probing
against a shared budget and test new unlabelled mixtures. Neither branch count
nor residual literal count alone predicts the saving on this pilot. Donor/map
selection remains supplied and must become automatic before an end-to-end claim.

The fixed reverse arm reduces aggregate query time **24.87% historical / 5.94%
on edits**, but complete measured workflow time changes by only **0.55% / 0.61%**
in two repeats. Sidecar loading makes warm setup plus lookup slower; historical
cold replay also regresses. Endpoint checked-object totals fall **31.22% / 12.07%**,
but compressed proof delta plus uncompressed partition sidecars grow **117.16% /
88.11%**. Compact source-bound sidecars are a supporting target. Keep the safe
affine baseline and preserve the failed screen; do not deploy a posthoc best arm.

Resume `experiments/results/cnf-transported-partition/checkpoint.json`. The three
prefixes contain only proofs committed before the original source query; target
roots are absent. Trial deltas and checked sidecars retain exact evidence, while
the union preserves all earlier payloads. New native expansion remains uncapped
in general; the 256 limit is a shared per-query stop, not polynomial SAT closure.

## Previous checkpoint: compose transported supports with a few missing clauses

[Source-variable transport](residual-variable-transport.md) now retains bounded
normalization maps and restores hint metadata after restart. Five transfers work
on numbering-shift controls versus zero compact-coordinate transfers. General
renaming discovery remains open, and this is **not a net speedup**: fresh holdout
query time rises **5.26% against affine / 1.56% against compact**, in both orders.
All arms retain identical native/affine proof digests, 10,249 recorded expansions
and 33 SAT / 38 UNSAT / 37 unresolved attempts. Keep the safe affine baseline.

Maps produce **1,758 candidates versus 31**, but **zero holdout transfers**.
A counter/result/digest-matched census finds **7–220 missing clauses, median 89**;
none qualifies for the previous one-missing-clause support path. Existing bounded
causal extraction on eighteen closest candidates gives six budget stops and
twelve supports still missing **3–19 clauses**, with no new refutation. These
negative results are retained; neither enlarging the pool nor enabling the
one-missing path is justified by this evidence.

**Next primary target: reuse the existing guarded/first-false composition rules
on transported supports with small gaps.** Start with the residual selected from
holdout case 61 (30 support clauses, three absent); cases 25 and 31 each miss five.
Reconstruct and check the extracted core, bind the exact target residual, screen
branch costs, and account for premise publication, every branch and cold replay.
The target plus all missing clauses is UNSAT because it contains the core; this
excludes only the all-true region. All other regions need checked composition,
and a SAT branch must lift correctly. Use the historical
[first-false partition](clause-partition.md) and [guard recognition](premise-guard.md)
implementations, preserving their regressions. A source-level verdict cannot be
inferred from a conditional residual alone. Fresh inputs must follow the pilot.

Random/shared mixtures consume **81.26%** of first-order holdout query time;
37 stops consume **27.627 / 30.091 seconds**. Alternative supports, unrelated
renaming discovery and representative external workloads remain open. Retained
map/hint budgets do not cap total proof checking, archive size or SAT expansion.

Resume `experiments/results/cnf-residual-transport/checkpoint.json` for preserved
proof evidence. Its `hint_resume_archive` retains the mapped policy's metadata;
the cumulative union merges proof authority only. Detailed mismatches and exact
residual/origin bindings are in `mismatch-analysis.json`. Tests, historical audit,
source ledger and manuscript build are bound in `checks.json`.

## Previous checkpoint: retain variable correspondence before widening retrieval

[The partial-residual pool](partial-residual-retrieval.md) is a **negative result**
for the tested admission/index policy. Query time increases **5.88% exposed /
4.27% fresh holdout**, and complete time increases **3.08% / 2.13%**, in both
orders. Outcomes and recorded native expansion counts do not improve. Holdout
SQLite changes by only -0.034%; checked objects and compressed storage grow.
Keep `InputSafeAffineProbeSolver` as the performance baseline.

The pool admits committed nonterminal negative proofs under a 512 KiB retained
charge, including residuals left by stops. All matches pass the existing native
checker. Holdout produces **one hit / 1,346 probes / 37 candidates**, after
28.15 MB of tail reads, 993 admissions and 985 evictions. Instrumented admission
costs 1.863 seconds versus 0.341 for retrieval, with repeated size charging a
large component. These profile times are diagnostic and overlap at call sites.

**Next primary target: bounded root-variable correspondence for residual reuse.**
A checked counterexample shows that separately compacted literal anchors miss a
core which the unchanged subset checker accepts under a supplied injection.
Retain normalization maps as untrusted proposals, compose them into source/root
coordinates, and recheck transported clauses and native proof authority. Test
same-source branches and edits before general renaming search. Never lift a
conditional refutation to its unconditioned source. Bound map admission and
lookup, charge persistence/reconstruction, and use a fresh split. The example
establishes a blind spot, not the prevalence or cost saving of automatic mapping.

Avoid growing the current pool blindly. Selective admission and incremental
accounting are supporting work once useful mappings are demonstrated. Random
and shared mixtures consume **86.02%** of first-order holdout query time; 27
stops consume **19.463 / 23.074 seconds**. Wider family discovery, alternative
surviving supports, separator decomposition and external validation remain open.

Resume `experiments/results/cnf-partial-residual-pool/checkpoint.json` for all
preserved evidence; the optional pool is not the performance baseline. The final
source ledger, union counts, historical checks and test/build evidence are bound
in its `checks.json`. All prior sources, proofs and trial artifacts are retained.

## Previous checkpoint: retrieve supports from committed partial searches

[The bounded affine probe](bounded-affine-probe.md) now runs before native
acquisition, with the existing independent source/row checker and separate proof
table. The public adapter snapshots finite outer/inner inputs; review caught an
iterator-consumption flaw in the first kernel, and all twelve workers were rerun
with copying charged. All first-run decisions and proof tables match the rerun.

Against planned reuse, mean query time falls **20.25% exposed / 41.87% on the
fresh 96/108/120 holdout**; complete time falls **20.34% / 41.88%**, in both orders.
Holdout SQLite storage falls **42.15%**, checked objects **42.99%**, and cold proof
time **42.74%**. Outcomes improve from **50 SAT / 32 UNSAT / 26 unresolved** to
**50 SAT / 43 UNSAT / 15 unresolved attempts**. No previously completed attempt
is lost. All eighteen holdout parity attempts use affine certificates without
native expansion. This is a constructed-stream result, not unrestricted closure.

**Keep the regression:** matched warm solve time increases **89.44% / 93.27%**
against planned reuse. Copying, extra lookups and repeated canonicalization on
native fallback cost work. Improving that path is supporting work; it is smaller
than the remaining acquisition cost on this stream.

**Next primary target: bounded support retrieval from checked residual proofs
left by incomplete searches.** Random 3-CNF and shared mixtures now consume
**92.46%** of holdout query time. The fifteen budget stops consume **9.335 / 12.187
seconds** and commit **3,820 negative residual records**, all below the preceding
4,096-literal origin limit. The present negative pool admits completed native
query roots only. Native exact residual reuse already exists, so the experiment
must add useful checked support/containment matches across changed residual keys.
Charge selection, extraction, checking, invalidation and cold reconstruction;
do not treat conditioned residual refutations as unconditional source refutations.

Nine distinct source roots remain absent at stream end. Every stopped holdout
source has affine rank zero and 96--120 free variables; the existing small-free-
dimension completion path cannot settle these cases directly. Alternative
surviving supports, variable correspondence, shared-variable decomposition and
representative external benchmarks remain open. Candidate eligibility is not
evidence of a net saving or a polynomial bound.

Resume `experiments/results/cnf-affine-probe-safe/checkpoint.json`. The union has
**54,418 native / 47 affine-negative records**, preserving all earlier payloads.
All **664 prior sources / 8,275 prior artifacts** and **57 first-run artifacts**
remain intact. Validation checks **1,296 chronological attempts / 1,296 exact
first-run comparisons / 512 exhaustive formulas**. All **1,347 full / 208 focused
tests** pass. The **232-page manuscript** builds cleanly with **64 proof blocks**
unchanged; final source ledger **672**. All limits and warning sites are recorded.

## Previous checkpoint: recognize affine contradictions before native acquisition

[Shared support derivations](shared-support-derivations.md) now retain causal
choices under a 4 MiB plan charge and emit through the unchanged native verifier.
The second support-selection traversal disappears: 415 exposed / 518 fresh-holdout
node visits. Against negative edit reuse, mean query time falls **6.45% / 2.62%**
and complete worker time **3.14% / 1.02%**, in both orders. Proof bytes, decisions,
expansions and persistent storage are identical. Accepted plan charges peak at
711,610 / 1,378,956 bytes. The cap excludes transients and emission workspace.

**Retain the limits:** holdout query time remains **0.87% above witness-only search**
on the mean, with mixed paired signs. Checked-object space, RSS and mean warm/cold
times increase slightly against negative reuse. All modes retain the same ten
holdout budget-stopped attempts. This optimization does not expand family closure.

**Next primary target: integrate a bounded affine-negative probe into general CNF
acquisition.** Random 3-CNF and parity mixtures account for **79.16%** of first-order
holdout query time. Applying the existing source-bound affine checker to all 108
inputs without labels yields 14 negative observations, including stopped cases
42 and 43. Case 43 remains absent at native stream end. The screen takes 0.099
seconds but excludes publication, persistence and cold replay; it is posthoc
evidence, not an integrated speedup. Keep the original unknown observations.
Consistent subsystems give no verdict for leftover clauses. Freeze a fresh split
and measure misses and all costs against both existing policies.

The ten stopped attempts consumed 4.976 of 8.428 query seconds and committed
2,622 checked negative residuals. Their source/assumption bindings must be
transported before cross-edit reuse. Six distinct source roots remain missing at
stream end. This is the next broader gap after affine integration; alternative
surviving supports and durable candidate retention remain open.

Resume `experiments/results/cnf-support-plan/checkpoint.json`. Preserve all
**658 prior sources / 8,197 artifacts / 121 manifests**. The union contains
**45,061 native records**, with earlier payloads authoritative and alternative
valid proofs retained in trial archives. The audit checks **1,296 attempts /
432 exact plan comparisons / 512 exhaustive formulas**. Final source ledger:
**664**. Test/build evidence and unchanged proof blocks are bound in `checks.json`.

## Previous checkpoint: share support discovery with proof materialization

[On-demand negative edit reuse](on-demand-negative-edit-reuse.md) now remembers
sixteen checked native UNSAT roots, recognizes near edits without supplied donor
labels, and defers causal proof materialization until a surviving support matches.
Ten negative transfers occur in each exposed/fresh-size stream. All targets still
pass the original native verifier; deleted required clauses cause a miss.

**Retain the query regression:** mean query time rises **2.40% exposed / 5.81%
holdout**, in both orders. Warm time also rises. Keep the preceding witness pool
as the latency baseline. Native expansions fall **1,961 to 1,579 / 3,159 to 2,781**,
but core materialization adds **650 / 740** records. Total records rise while
smaller formulas reduce SQLite bytes **15.30% / 9.37%**, checked-object bytes
**13.14% / 8.21%**, and cold proof time **17.94% / 6.13%**. Complete worker time
falls 7.40% / 1.46%, with the first holdout gain only 12 ms. This is an optional
space/replay tradeoff on constructed workloads, not a general speedup.

**Next primary target: reuse a bounded derivation plan across discovery and
checked materialization.** Holdout discovery visits 994 support nodes, followed
by another 488 materialization visits. The current plan stores only indices/key,
so coordinate reconstruction and causal traversal repeat. Normalization and
restriction dominate the posthoc profile; every result/counter/native digest
matches the frozen trial. Retain exact parent clauses, residual identities,
renamings and unit/branch evidence under a byte budget, then emit through the
unchanged verifier. Charge plan creation, checking, storage, invalidation and
restart. Use a fresh split; do not promote an unmeasured saving.

Six of sixteen holdout near matches fail because their selected support still
requires a deleted clause. Alternative surviving preimages/supports and selection
beyond the first near match remain separate discovery gaps. The negative pool
starts empty after restart, so durable candidate retention also remains open.
Outcome counts are unchanged: exposed **70 SAT / 36 UNSAT / 2 unresolved** and
holdout **57 SAT / 48 UNSAT / 3 unresolved attempts**. Neither decision coverage
nor recognized-family closure increased.

Resume `experiments/results/cnf-negative-edit-pool/checkpoint.json`. Preserve all
**652 prior sources / 8,141 artifacts / 120 manifests**. The append-only union has
**39,211 native** records, with all earlier proofs and observations rechecked.
All **1,327 full / 188 focused tests** and 512 exhaustive formula checks pass.
The **230-page manuscript** builds without warnings and retains 64 proof blocks;
44 unchanged-site SQLite warnings remain in the full suite. Final source ledger:
**658**. The failed profiler's JSON/in-memory model-key comparison and its corrected
rerun are preserved. No timed run was altered.

## Previous checkpoint: negative search reuse and durable candidate retention

[Bounded automatic witness retrieval](bounded-witness-pool.md) now tests at most
four recent same-size assignment vectors from a 64-entry pool. It receives no
supplied donor relationships or family labels. Every hit passes the complete
CNF and native witness checks; misses give no UNSAT evidence. Packed coordinates
are arbitrary compact-rank proposals, not a claim of semantic correspondence.

On separate 108-query exposed and frozen size-holdout streams, mean query time
falls **2.97% / 8.27%**, and complete worker time **4.36% / 9.06%**, with both orders
improving. Holdout edit expansions fall **1,342 to 955**, native records **3,292 to
2,873**, SQLite bytes **34,770,944 to 30,937,088**, and checked-object-plus-pool
bytes **83,155,305 to 74,284,351**. Candidate retained charge stays below 14,200
bytes. These are matched-stream observations, not unrestricted resource bounds.
Each arm still has two budget-limited attempts. Family closure was not expanded.

**Highest-value next target: dependency-checked negative reuse across edits.**
Random 3-CNF and parity still consume about **83%** of first-order pool query time
in both streams. Parity has zero hits, unchanged expansion counts and higher
lookup cost. Test whether retained refutations depend only on clauses surviving
an edit, preserving all shared-variable conditions and independent verification.
Discovery/dependency accounting must show a net gain; a deleted premise cannot
silently remain authoritative. New candidate screening should avoid spending
more on the families with no witnessed savings.

**Concrete persistence gap:** seeding from the newest 64 native payloads rebuilds
**zero** candidates after the exposed stream's UNSAT tail, versus 33 on holdout.
A bounded SAT-only index is a plausible low-cost supporting improvement, with
its update, byte limit, durability and reconstruction charges measured explicitly.
The current entry/width cap excludes seed JSON bytes and transient allocations.
Holdout warm time also regresses slightly. Keep all misses and regressions.

Resume `experiments/results/cnf-witness-pool/checkpoint.json`. The immutable prior
**647 sources / 8,088 artifacts / 119 manifests** remain intact. Both readers check
the append-only union of **34,426 native** records and all earlier extensions;
**5,650 composed / 444 pilot decisions**, 108 earlier larger-stream observations
and 624 inventory nodes remain valid. The audit checks 864 chronological attempts
and all 512 two-variable clause-set formulas. Eight new tests bring the full suite
to **1,319**, focused suite **150**, with 44 earlier-site SQLite warnings only in
the full suite. The **229-page manuscript** builds without warnings and retains
64 proof blocks unchanged. Final source ledger: **652**. The failed audit's
incorrect nested recovery-result access is preserved with its corrected rerun.

## Previous checkpoint: retrieve reusable witnesses across clause edits

[The larger-mixture study](larger-mixture-expansion-costs.md) freezes **108 queries /
72 new canonical roots**, with scales 24/48/72, six designs, edits and exact-root
repeats. Plain batching now wins mean query time: the memo regresses **1.49%** and
ordered normalization **1.09%**, in both orders. Keep all timings and alternatives;
the earlier small-catalog improvements did not generalize to this designed stream.

All variants initially return **70 SAT / 36 UNSAT / 2 unresolved attempts** under
256 native expansions per attempt. Budget stops are not UNSAT. Both preserve
256 committed records, rolling back 20/13 pending records. A later repeat solves
one stopped base using the accumulated archive. **Random 3-CNF consumes 58.48% of
query time**, parity mixtures 21.54%. Edits need **1,013 expansions / 1,055 records**,
nearly matching bases' 1,041 / 1,086. New acquisition across edits is the main
reuse gap. Normalization remains the largest profiled exclusive routine; avoiding
whole acquisitions can avoid its work together with restriction and propagation.

The timed archive grows to **2,259 records / 12.13 MB encoded payload / 22.85 MB
SQLite**, with **53.93 MB** in checked Python cache objects. Cohort measurements
are cumulative observations, not asymptotic bounds. Worker RSS includes benchmark
metadata and cold replay. The separate bounded inventory closes only **18/108**
family decompositions, despite 106 completed decisions. Every root has the same
coarse syntax vector; unresolved interactions remain explicit. Its 624 checked
nodes and 108 source bindings are persisted separately.

**Concrete recovery:** a fully checked later donor model also satisfies the one
root still unresolved at stream end. The new optional helper validates the full
target and publishes **one SAT certificate / 7,895 payload bytes / zero expansions**.
Both readers now certify **48 SAT / 24 UNSAT distinct roots**. This post-timing
recovery preserves both original budget-stop observations; candidate selection
was supplied, so it is not yet a general retrieval algorithm or complexity result.

**Next highest-value implementation target: bounded, label-free candidate retrieval
for SAT witnesses**, with complete checks, misses and persistence charged. A
posthoc check finds **21/23 available parent models** also satisfy their edits;
those edits incurred 225 expansions, but their work is not an additive guaranteed
saving. The hardest remaining mechanism is partial negative-search reuse across
clause edits; witness reuse does not solve UNSAT cases. Preserve a fresh evaluation
split before tuning on this now-exposed stream. Compact proof state and better
recognition of mixed/shared interactions remain open.

Resume `experiments/results/cnf-larger-mixtures/checkpoint.json`. All **638 prior
sources / 8,032 artifacts / 118 manifests** are unchanged. The union now contains
**31,141 native** records, with all old affine/equivalence/discovery records and
**5,650 composed / 444 pilot decisions** intact. The failed inventory audit's
incomplete expected configuration is preserved and corrected. All **1,311 full / 142 focused tests** pass; 44 existing-site SQLite warnings
remain in the full suite, none in focused tests. The **228-page manuscript**
builds without warnings with **64 prior proof blocks** unchanged. Final source
ledger: **647**; details are in `checks.json`.

## Previous checkpoint: broaden the cost and discovery evidence

[Ordered residual normalization](ordered-residual-normalization.md) checks local
literal order and uses a two-pointer tautology test; unordered/duplicate-literal
clauses keep the original fallback. Signed compact renaming preserves order, so
the mapped clause needs no second sort. Global deduplication/sorting, support,
name maps, exact keys and every proof check remain unchanged. Empty clauses do
not bypass validation of the remaining input. This exact transformation applies
to valid CNFs generally but adds no tractable SAT category.

On the same 104 sources, the optional path avoids **96,099 sort calls**. Mean query
time falls **2.17%** and complete time **1.68%** against batching, with both orders
improving. It is still **1.19% slower than the 128-KiB memo** on query time, and
warm time **regresses 2.95%**. It adds no retained normalization cache, but measured
RSS does not fall. Answers, models, all ordinary counters, proofs and persistent
storage match batching exactly. Keep both alternatives optional; do not promote
small measured gains into a general runtime claim.

**Next highest-value gap: representative cost and discovery evidence on a larger
held-out mixture stream.** Ordered normalization remains the largest exclusive
site here (1,163 calls / 0.07034 exclusive / 0.14104 inclusive profiled seconds);
restriction costs 780 calls / 0.06935 inclusive seconds. After several optimizations
on the same 104 small sources, another local reduction needs stronger evidence.
Freeze larger novel/mixed/edited CNFs and deterministic budgets, measure
recognition outcomes and unresolved interactions alongside acquisition, runtime
and retained proof state, then choose the dominant bottleneck. Compare the three
preserved variants. Direct invariant transport and combining ordering with reuse
are candidates only; broader structure discovery remains the main objective.

Resume `experiments/results/cnf-ordered-normalization/checkpoint.json`.
All **632 prior sources / 7,990 artifacts / 117 manifests** and the full proof/decision
union remain unchanged. Validation covers **624 chronological queries / 416 exact
comparisons / 104 truths / 104 committed prefixes**, both old readers, and ordered
normalization agreement on **28,886 archived CNFs / 4,961 mutations**. Eight new
tests add exhaustive small clauses/formulas, adversarial inputs, failure recovery
and full-key/model/proof comparisons. All **1,300 full / 131 focused tests** pass. The full suite retains 44 SQLite
ResourceWarnings at unchanged files; focused tests emit none. The **228-page
manuscript** builds without warnings and preserves **64 earlier proof blocks**.
Final source ledger: **638**; build and suite details are in `checks.json`.

## Previous checkpoint: preserve residual clause invariants

[Targeted proof-normalization reuse](proof-normalization-reuse.md) now retains
`_visit` results only for `_negative_child` checks. Exact raw inputs bind the
immutable CNF, name map and key; the original child-key and checked-UNSAT tests
still run. Invalid equal-hash literals are rejected before lookup. Query-local
FIFO state clears on success/failure and adds no persisted proof authority.

On the same 104 inputs, the 128-KiB cap avoids **262 of 311** negative-child
normalizations, reducing normalization visits **21.31%**. Mean query time improves
**3.88%**, with both orders improving, but mean complete time improves only 2.07%
and its second paired delta **regresses 1.86 ms**. The 32-KiB arm also regresses
in its second query measurement. Keep this optional; there is no robust general
speedup claim. All decisions, proofs, expansions, publication counters and final
storage remain identical. Peak retained charge is **131,020 bytes / 13 entries**;
an independent graph walk measures 83,489 bytes. The cap excludes transients,
allocator overhead and full-solver memory. Persistent storage does not shrink.

**Next highest-value target: preserve local clause order during residual
normalization.** The census finds **501/546 producer inputs / 47,894 literal units**
with sorted, distinct, tautology-free literals. Restrictions preserve that local
property, but not global clause order, duplicates or compact names. Prove and
check those boundaries before bypassing any sorting or renaming. Memo128 still
spends 901 normalization calls / **0.14642 inclusive profiled seconds**, compared
with 780 restrictions / 0.07031 seconds. Its admission sizing alone costs
0.02845 seconds; shorter-lived direct transport is the second candidate. Profile
times overlap and are separate from matched wall times. No new pattern coverage
or unrestricted SAT bound follows from this supporting optimization.

Resume `experiments/results/cnf-proof-normalization-reuse/checkpoint.json`.
The parent union and **5,650 composed / 444 pilot results** remain unchanged.
Validation covers **624 queries / 416 exact comparisons / 104 truths / 104 visible
committed prefixes**, both old readers, all **28,886 fixed points / 4,961 mutations**.
All **625 prior sources / 7,947 artifacts / 116 manifests** are preserved. Nine
new tests cover proof authority, name maps, invalid literals, capacity and failure
cleanup. All **1,292 full / 123 focused tests** pass. The full suite emits 44 SQLite
ResourceWarnings versus 43 in the parent, at unchanged source/stdlib files;
focused tests emit none. The **227-page manuscript / 64 prior proof blocks**
remain valid. Final source ledger: **632**; details are in `checks.json`.

## Previous checkpoint: reuse repeated residual construction and normalization

[Bounded publication batches](bounded-publication-batches.md) group the unchanged
verified INSERT stream, flushing before a successful answer. Failed queries roll
back the pending suffix and evict its checked aliases; committed prefixes remain.
Uncertain rollback poisons the instance until reopening. Exclusive ownership is
required. The optional policy changes partial-query visibility, with no proof
format or journal/synchronous-setting change.

On the same 104 sources, **605 commits fall to 104**. Mean query time falls
**35.55%** versus direct verification and **36.30%** versus a one-record adapter,
with gains in both orders. Observed complete reductions are 26.87% / 24.24%, but
an unusually slow first control cold sample must not be attributed to batching.
Every non-batch counter, answer, model, certificate and storage byte count matches.
The timed 32-record / 256-KiB policy peaks at **27 records / 39,747 payload bytes /
17,086 charged pending-key object bytes**; neither limit is reached here. Separate
tests exercise cuts and oversized records. Journal sampling rises **49,760 ->
103,112 bytes**; process RSS also rises. These limits do not cap SQLite journals,
whole-solver RAM or lock duration. Completed results remain durable; unfinished
batches may be lost on failure.

**Next highest-value target: repeated residual construction and canonicalization
across acquisition and proof checking.** The posthoc profile leaves **1,163
normalizer calls / 0.07401 exclusive / 0.18230 inclusive seconds** as the largest
exclusive site,
while 104 commits take 0.03340 seconds. Restriction still costs 780 calls / 0.06973
inclusive seconds. Count exact raw repeats, including noncompact name maps, at
those call sites before selecting transport/reuse. Keep source/conditioning
identity, variable maps, full keys and independent proof checks bound. The earlier
already-normalized-output census found only 45 visitation opportunities; do not
claim additional savings yet or reinstate the regressing general cache.

Resume `experiments/results/cnf-publication-batches/checkpoint.json`. The parent
archive and decisions are referenced unchanged: **28,886 native / 26 affine /
42 v1 / 53 v2 / 22 v3 / 34 discovery records**, all **5,650 composed / 444 pilot
results**. Validation covers 624 chronological queries, 416 alternative/control
comparisons, 104 exhaustive truths, 144 choices and 84 known hits. An independent
replay certifies every externally visible archive after **104 batch commits**.
Full old histories/readers and all 28,886 canonical fixed points remain valid.
All **619 prior sources / 7,904 artifacts / 115 manifests** remain unchanged.
All **1,283 full / 114 focused tests** pass, including process-exit recovery and
rollback tests; 43 pre-existing-site SQLite warnings remain in the full suite,
none in focused tests. The **227-page manuscript** builds with all **64 prior
proof blocks** unchanged. No new structural coverage, Lean theorem or unrestricted
SAT resource bound follows.

Final executable source ledger: **625**. The new manifest binds **43 artifacts**;
next preservation audit: **7,947 artifacts / 116 manifests**.

## Previous checkpoint: batch verified publication without losing durable results

[Direct canonical verification](direct-canonical-verification.md) now recognizes
stored normalizer fixed points without sorting/renaming, then passes the checked
immutable CNF/name-map/key triple once to the original verifier. Every key, SAT
model, negative proof rule and child dependency remains checked. Acquisition and
cold replay share this optional recognizer; no canonical cache is retained.

On the same 104-source stream, **552 normalization calls / 55,601 literal visits**
are replaced by explicit canonical-form checks. Normalization-only visits fall
**31.75%**; total input validation is not removed. Mean query time falls **5.79%**,
cold replay **18.12%**, and complete time **6.63%**. Both paired query/cold/complete
deltas improve; warm deltas remain mixed. All answers, models, quotient choices,
ordinary proof/acquisition counters, 552 native / 53 extension payloads and
1,179,648 SQLite bytes remain identical. No general speedup or new coverage claim.

**Next highest-value target: bounded publication transactions.** The posthoc
identical-output profile leaves **605 SQLite transaction exits / 0.12607 exclusive
seconds**, now the largest exclusive site, plus 1,591 SQL executions. A separate
census finds only **45 visitation opportunities / 8,011 literal units** that equal
an earlier normalized output in the same query; direct transport remains a smaller
secondary target. Test batching with explicit dependency-closure durability,
partial-query visibility, memory limits, rollback/invalidation and injected
failures. Preserve committed history and commit a returned answer's dependencies
before success. This is a next design investigation, not an implemented saving.

Resume `experiments/results/cnf-canonical-verify/checkpoint.json`. Parent archive
and all decisions are referenced unchanged: **28,886 native / 26 affine / 42 v1 /
53 v2 / 22 v3 / 34 discovery records**, all **5,650 composed / 444 pilot decisions**.
Both readers validate every native record; all 28,886 formulas match the original
normalizer, and 4,961 representation mutations match its acceptance criterion.
The audit also covers 624 chronological queries, 416 exact alternative/control
comparisons, 104 exhaustive truths, 144 choices and 84 known hits. All **613 prior
sources / 7,859 artifacts / 114 manifests** remain unchanged. A test-generator
setup error is preserved. All **1,271 full / 102 focused tests** pass, with 43
SQLite warnings at pre-existing sites in the full suite and none in focused tests. The
**226-page manuscript** builds cleanly with all **64 prior proof blocks** unchanged.
No production-default change, new Lean theorem or unrestricted SAT bound follows.

Final executable source ledger: **619**. The new manifest binds **45 artifacts**;
next preservation audit: **7,904 artifacts / 115 manifests**.

## Previous checkpoint: avoid rediscovering already validated canonical results

[Bounded query-local normalization reuse](query-canonicalization-reuse.md) now
implements the previous repeat opportunity with exact CNF/name-map/key triples,
strict pre-lookup literal validation, conservative object charging, FIFO eviction
and unconditional query-end clearing. Both 128 KiB and 8 KiB arms preserve all
answers, models, quotient choices, ordinary acquisition counters and certificates.

On the same 104 replayed inputs, 128 KiB saves **19.57% of normalization visits /
19.55% of serialized key bytes**, with **368 hits / 470 evictions** and a peak
**131,018 charged bytes / 20 entries**. Yet mean complete time rises **3.65%**,
with positive deltas in both orders. At 8 KiB it rises **8.44%**, with only fourteen
hits and 1,295 oversized skips. Every lookup adds validation/copying/hash work.
Warm streams have zero cache hits and regress. Keep the optional experiment and
its negative result; no production/default change or storage saving is claimed.

**Next highest-value target: reuse validated canonical results directly along
native verification and child visitation.** The separate control profile assigns
552 calls / 0.08700 inclusive seconds to `_verify`, and 546 / 0.08263 seconds to
`_visit`. The cache increases both costs. Investigate passing exact immutable
triples between appropriate callers or cheaper explicit canonical-form recognition,
while preserving external-input validation and all proof checks. Charge warm-path
cost and identity transport; increasing the general cache size is not the next
default step. The 605 individual SQLite commits remain a separate durability task.

Resume `experiments/results/cnf-query-canonical-cache/checkpoint.json`. Its parent
archive is referenced unchanged: **28,886 native / 26 affine / 42 v1 / 53 v2 /
22 v3 / 34 discovery records**, all 5,650 composed and 444 pilot decisions.
Validation covers 832 chronological queries, 416 exact cache/control comparisons,
104 exhaustive truths, 144 choice checks and 84 known hits. All **607 prior sources /
7,807 artifacts / 113 manifests** remain unchanged. Two validator setup errors are
preserved; timing workers and solver results were unaffected. All **1,262 full /
93 focused tests** pass, with 44 pre-existing SQLite warnings in the full suite and
none in focused tests. No new coverage, Lean theorem or unrestricted SAT bound.

The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. Final executable source ledger: **613**. The new manifest binds **52
artifacts**. Next preservation audit: **7,859 artifacts / 114 manifests**.

## Previous checkpoint: reuse normalization within each query

[Known-quotient selection](known-quotient-selection.md) checks the complete native
target, then the first-block target only on a miss, before fresh acquisition.
Correct canonical-name transport and the selected source evidence retain existing
SAT models and v2/v3 proof authorities. At most two alternatives are considered.

The 68-query pilot plus 36 excluded fresh sources recover **eight native nodes**
versus all-block acquisition (560 -> 552), saving **3,406 payload / 28,672 SQLite /
2,938 gzip bytes**. All eight native savings occur on the original pilot; the fresh
segment has the same 152 native additions under every policy. Four first-target
hits include SAT and UNSAT. Thirty-eight lookups and fourteen extra transforms
are charged. Mean complete time rises 1.00% versus all blocks, with mixed paired
deltas, and 2.47% versus single block. Keep the policy optional.

**Next highest-value structural reuse target: per-query normalization results.**
A separate identical-output solve profile places normalization and individual
SQLite commits ahead of propagation in elapsed cost. An exact census finds 505
repeats among 1,715 normalization calls; 469 repeats occur within one query and
cover 96.39% of repeated input literals. Peak per-query encoded input/result state
is 73,860 bytes versus 1,448,226 for the full stream. Test a bounded immutable cache
of the CNF/name-map/key triple; charge validation, copying, hashing, lookup,
objects and eviction. Reject booleans/floats before hits. These are opportunities,
not implemented savings. Transaction batching remains a separate durability task.

Resume `experiments/results/cnf-known-quotient/checkpoint.json`: all prior **28,736
native / 26 affine / 42 v1 / 42 v2 / 11 v3 / 34 discovery records** preserved; union
now **28,886 native / 53 v2 / 22 v3**. Full histories, 624 chronological queries,
104 truths, 36 fresh exclusions and both orders of all known choices validate.
The failed benchmark dispatch and profile-comparison setups are retained. All
601 previous sources / 7,761 artifacts / 112 manifests are unchanged. No new
Lean or unrestricted-SAT resource bound follows.


The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,253 full / 84 focused tests** pass. Final executable source
ledger: **607**. New manifest: **46 artifacts**, including the retained failed
setups and posthoc profile. Next preservation audit:
**7,807 artifacts / 113 manifests**.

## Previous checkpoint: preserve known quotients before fresh acquisition

[Multiple-block equivalence](multiblock-equivalence.md) checks disjoint supports,
unions signed maps and substitutes every source clause once. Single-block
negatives retain v2; multiple-block negatives use compact v3 with native negative
dependencies. Twelve pilot inputs now use two blocks. All cached/uncached
all-block acquisitions match, and old formats remain readable.

On the unchanged 68-source pilot, applied merges rise **45 -> 57** and propagation
falls **51,326 -> 51,059 (0.52%)**. But native expansions rise **358 -> 366**, native
certificates **398 -> 408**, and combined payload **492,731 -> 496,214 bytes**.
SQLite grows 4,096 / gzip 2,114 bytes. Query time falls in both orders; complete
cached deltas **-0.03893 / +0.00438 seconds** remain mixed. Keep this optional and
retain the measured storage regression; more substitution is not less acquisition.

**Next highest-value target: choose an already known quotient.** At actual query
prefixes 7 and 34, both streams already contain the one-block quotient while the
all-block quotient is new. Ignoring it costs five and three extra native records;
two other later queries add one record each after their history changes. Compare
the exact one/all quotient keys before fresh solving, with checked recomposition
and charged second-quotient construction, lookup, verification and storage. The
diagnosis is not an implemented saving or a search for the globally optimal subset.

Resume `experiments/results/cnf-multiblock-equivalence/checkpoint.json`: all
**28,691 native / 26 affine / 42 v1 / 42 v2 / 34 discovery records** preserved;
45 new native keys and eleven v3 records added. Native union: **28,736**.
Union growth is 81,920 SQLite / 6,918 compressed bytes. Old/new histories, 408
chronological queries and 68 source truths validate, with both quotient truths
checked on the twelve affected sources. All 596 prior sources / 7,722 artifacts /
111 manifests remain unchanged. No new Lean or unrestricted-SAT bound follows.


The **224-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,245 full / 76 focused tests** pass (44 pre-existing SQLite
warnings in the full suite, none in focused tests). Final executable source
ledger: **601**. New manifest: **39 artifacts**. Next preservation audit:
**7,761 artifacts / 112 manifests**.

## Previous checkpoint: reduce child acquisition with multiple equivalence blocks

[Binary-core discovery reuse](binary-core-discovery-reuse.md) implements the 22
repeated-core opportunities on the unchanged 68-input pilot. Binary-local trees
are translated to current source indices and checked before substitution; binary
or coordinate edits miss the exact key. Null discovery outcomes are never SAT
answers. Native and compact proof payloads match byte-for-byte.

Acquisition graph/SCC work falls **44.53%**: constructed edges 4,276 -> 2,372 and
SCC visits 8,552 -> 4,744. The 34 entries use **11,906 serialized / 25,887 Python
object bytes**. Persistent mode adds 36,864 SQLite / 3,618 trial gzip bytes and
recomputes every entry at cold validation. Acquisition plus cold discovery thus
rises **10.94%** above the uncached control. Memory-mode complete timings have
mixed signs; persistent total gains are only 0.00091 / 0.00254 seconds with mixed
query timing. Keep both modes optional; this is no established production speedup.

**Next:** multi-block substitution on the twelve diagnosed sources with a second
disjoint block. Child solving still costs 51,326 propagation visits / 358 expansions.
Price proof size and child acquisition before claiming broader gains. Sharing the
other recognizers' graph construction remains a separate target: 8,344 subset
edges, 6,772 cover edges and 171 subset SCC calls are unchanged.

Resume `experiments/results/cnf-binary-core-cache/checkpoint.json`: all **28,691
native / 26 affine / 42 v1 / 42 v2** records unchanged, plus 34 discovery entries.
Old/new histories, 408 chronological queries and 68 exhaustive truths validate.
All 591 prior sources / 7,683 artifacts / 110 manifests are preserved. No new
coverage, Lean theorem or unrestricted-SAT resource bound follows.


All **1,236 full / 67 focused tests** pass, with 44 pre-existing SQLite warnings
in the full suite and none in the focused suite. The **223-page manuscript**
builds cleanly and all **64 previous proof blocks** are unchanged. Final source
ledger: **596**. New manifest: **39 artifacts**. Next preservation audit:
**7,722 artifacts / 111 manifests**.

## Previous checkpoint: reuse binary-core discovery across wide-clause edits

[Compact equivalence certificates](compact-equivalence-certificates.md) remove
redundant source/child formula fields. Exact source-key parsing and checked
substitution reconstruct their identities; both old and new readers remain
available. On the unchanged 68-input pilot, native acquisitions and all 42
negative reconstructions match. Equivalence storage falls **68,878 -> 26,998
bytes (60.80%)**; combined payload falls to **492,731 bytes**, **6.17% below the
native control**. Native-plus-extension count remains 440 versus 420.

SQLite falls 61,440 bytes versus v1; gzip falls only 1,172 bytes. Complete-worker
paired deltas have mixed signs against both v1 and native control. Query time
remains **3.93% above the native control**, higher in both orders. The compact
API remains optional; this is a representation improvement with no new solving
coverage or established production speedup.

**Next highest-value target:** cache binary-core discovery and source-checkable
equivalence trees. The same 56 eligible inputs contain **34 distinct exact binary
keys / 22 repeats**; wide-clause additions preserve those cores. Current code
still constructs 4,276 edges and visits 8,552 SCC edges. Reuse binary-local clause
references, transport them to each full source, and check exact literal coordinates.
Binary deletions/changes must invalidate or miss the key. Charge extraction/keying,
cache lookup, retained space, verification, persistence and cold reconstruction
alongside avoided graph/SCC work. Do not count these diagnostic repeats as
implemented cache hits. Keep baseline history and all unsuccessful comparisons.

**Next coverage target:** twelve inputs contain two disjoint equivalence blocks
but the policy merges only one. Complete quotients remove two variables/eight
literals; none was known at its query prefix. Multi-block acquisition and shared
SCC computation with the other recognizers remain open. Prepared production
admission and recursive integration still need their own measured certificates
and resource accounting. Compactness alone does not resolve arbitrary interaction.

Resume `experiments/results/cnf-compact-equivalence/checkpoint.json`. All **28,691
native payloads / twenty-six affine / forty-two v1 equivalence records** remain
byte-identical; the union adds **forty-two v2 alternatives**. No native or v1 record
is inserted or replaced. Keeping both versions grows the union by 69,632 SQLite /
3,701 compressed bytes, separate from the smaller v2-only trial. New negative
roots require the explicit compact reader, with legacy fallback; native recursive
search and existing defaults remain unchanged.

All **1,228 tests**, **59 focused tests**, 408 chronological query/dependency audits,
68 exhaustive truths, warm answers and complete old/new histories pass. Full tests
retain 44 old SQLite warnings; focused tests have none. All 586 prior sources,
7,642 artifacts and 109 manifests remain unchanged. No new Lean theorem or
unrestricted-SAT resource bound follows.


The **223-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **591**. New manifest: **41
artifacts**. Next preservation audit: **7,683 artifacts / 110 manifests**.

## Previous checkpoint: remove duplicated formulas from quotient certificates

[Binary equivalence acquisition](binary-equivalence-acquisition.md) now has a
checked top-level quotient API. Two shared trees certify a signed block with
exactly `2(k-1)` edges. Every source clause is substituted; SAT models lift to
native witnesses, and UNSAT uses an explicit extension record with a native
negative child. Recursive native search and old proof formats remain unchanged.
The prototype still performs its own SCC work and is outside the prepared
production admission pipeline.

The 68-input empty-archive pilot (eleven saved sources, 33 edits, 24 fresh controls)
reduces propagation **61,517 -> 51,326 (16.57%)**, but native-plus-extension
certificates grow **420 -> 440**, payload **525,136 -> 534,611 bytes**, and complete
time **1.29%**. Both timing orders regress. Forty-five extra substitution steps
accompany six fewer native expansions. All selected blocks merge only one
variable. Keep the policy optional; this is a preserved cost regression, not an
end-to-end production gain or new arbitrary-SAT coverage result.

**Next highest-value target:** remove two redundant fields from the negative
extension payload. The 68,878 stored bytes contain **20,673 bytes of source CNFs**
and **20,535 bytes of child keys**, versus only 2,713 bytes of equivalence evidence.
The full canonical source key already encodes the source; checked substitution
reconstructs the child key. Test a separately versioned compact record and reader
on the same workloads, preserving version-one readability and exact source/child
checks. Charge parsing, normalization and replay; do not claim the 41,208-byte
opportunity as a measured net saving. Full keys can remain collision independent.

**Second target:** reuse the **22 repeated binary cores among 56 eligible inputs**.
Adding wide clauses preserves their binary SCCs; deletion invalidates that key.
Reuse must transport binary-local clause indices to the current source and respect
literal coordinates. Current code rebuilds 4,276 edges and visits 8,552 SCC edges.
The repeated-core census is not yet a cache or timing improvement.

**Third target:** twelve inputs have two disjoint equivalence blocks, but only one
is used. Posthoc full quotients remove two variables/eight literals with preserved
truth; none is already known at its query prefix. Avoid assuming multi-block
rewriting saves acquisition before charging certificates and child solving.
Production admission and recursive integration remain open after these pilot costs.

Resume `experiments/results/cnf-binary-equivalence/checkpoint.json`: **28,691 native
keys / twenty-six affine extensions / forty-two equivalence records**, preserving
all prior payloads. New negatives require `EquivalenceStore`; they are not native
source roots. Four native alternatives remain in trial archives. Union growth:
1,327,104 SQLite / 127,289 compressed bytes, including comparator histories.
Earlier native/composed/affine authorities and solver defaults remain unchanged.

All **1,220 tests**, **51 focused tests**, 272 chronological query/dependency audits,
68 exhaustive truths, warm answers and full old/new cold histories pass. The full
suite retains 44 old SQLite warnings; focused tests have none. All 581 prior sources,
7,608 artifacts and 108 manifests are unchanged. No new Lean or unrestricted-SAT
resource bound follows.


The **222-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **586**. New manifest: **34
artifacts**. Next preservation audit: **7,642 artifacts / 109 manifests**.

## Previous checkpoint: merge binary-equivalent variables across the full source

[Targeted backbone discovery](targeted-backbone-discovery.md) closes all fourteen
saved recognition misses, including the six split nodes. One extra implication
root is allowed after the unchanged whole-cover budget; completed searches are
reused. On sixty fresh queries, selections rise two -> twelve, native additions
fall **252 -> 250**, payload falls **2,599 bytes**, and child propagation visits
fall **29,008 -> 27,154 (6.39%)**. Fifty-six extra searches and 8,756 ranking visits
are charged. Eight full covers and four affine extensions remain unchanged.

Timing is unstable: the first pair saves 0.00495 s of query time but adds 0.08083 s
complete time; the reverse pair also has large changes in unchanged preparation
and cold replay. Do not report the raw 28.21% query mean as a stable speedup.
SQLite size is unchanged, compressed trial size falls 114 bytes, and sidecars
grow about 5.4 KB. The solver stays optional. No study tests/audits overlapped
the timed workers.

**Next highest-coverage target:** source-checked binary SCC equivalences and exact
substitution across every clause. The new census has **67 mixed binary cores
without forced literals**; twenty contain equivalence blocks, including **eleven
ordinary split nodes**. Ten are graph-colouring and one is random-three case 56,
whose saved split source implies `x1 = not x8`. Hashes and signed blocks are in
`experiments/results/cnf-targeted-backbone/attribution.json`; 242 independent
two-CNF disagreement checks validate all diagnosed blocks. These are opportunities,
not implemented savings. Reuse the earlier probe-equivalence substitution logic,
but establish native acquisition certificates, model lifting and negative
recomposition before measuring the change. Avoid counting eight model records
and one subsumption record as eleven additional split opportunities.

Random-three cases **44 / 56** still cost **5,153 / 4,866 child propagation visits**.
The remaining 25 forced-variable sources only force variables other than the
frequency choice after full-cover exclusions; arbitrary alternate choices may
repeat the earlier first-path storage regression. Prioritize the equivalence
bridge over another unpriced forcing heuristic. Twenty stored sources have no
binary clauses. Larger/less explicit inputs and general interaction remain open.

**Other large costs:** graph discovery spends **26,440 visits**, against 3,840 in
acquisition. Cases 59/47/55 spend 4,231/4,127/3,191 visits before covers. Full
historical cold replay averages 14.2--16.4 seconds in this noisy run. Earlier
admission and cheaper replay remain separate total-cost targets.

Resume `experiments/results/cnf-targeted-backbone/checkpoint.json`: **28,145 native
keys / twenty-six extensions**, preserving every earlier payload. The optional
solver is `experiments.cnf_targeted_backbone.AccountedTargetedBackboneSolver`;
affine negatives retain `TerminalStore`. Four alternative native roots remain
in trial archives, while the union retains first payloads. Growth: 647,168 SQLite /
71,842 compressed bytes, including baseline history. No default solver changes.

All **1,212 tests**, **43 focused tests**, 240 chronological query audits and
sixteen publication counter audits pass. Warm reuse, 48 exhaustive family truths
and full cold histories validate. The full suite retains 44 old SQLite warnings;
focused tests have none. All 574 prior sources, 7,568 artifacts and 107 manifests
are unchanged. There is no new Lean theorem or unrestricted-SAT resource bound.


The **222-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **581**. New manifest: **40
artifacts**. Next preservation audit: **7,608 artifacts / 108 manifests**.

## Previous checkpoint: target the missed split-variable backbones

[Partial backbone reuse](binary-backbone-reuse.md) now transports a retained
implication path directly into an excluded-branch unit proof, without fresh
propagation. Only the surviving cofactor is searched; a SAT lift publishes no
excluded child. Whole-clause covers retain priority.

The first-path policy saves propagation but adds **five native nodes** on a fresh
sixty-query stream. A frequency gate instead saves **two nodes / 1,767 bytes**,
with a 3.04% mean query reduction in both orders. Complete-worker timing is mixed
and its mean is 0.02% higher; keep both policies optional. Compiled children,
ranking and proof transport are charged. The earlier storage regression and a
corrected preflight fixture are preserved.

**Next highest-coverage target:** one targeted implication query for the selected
split variable. Cover-oriented candidates miss a forced default variable in
fourteen stored sources. **Six are ordinary split nodes**, with matching recorded
variables: cases **20, 28, 32, 44 and two residuals of 52**. Exact hashes and forced
literals are in the new `attribution.json`. The other eight include directly stored
models/subsumption; fourteen is not a count of avoidable expansions. Use the binary
model to select the opposite premise, charge the extra root search, and compare
with the unchanged cover budget. This opportunity is diagnostic, not implemented.

New cases **32/44/56** still pay **5,494/4,114/3,894 child propagation visits**.
The stored-node census also contains 75 satisfiable mixed binary cores with no
forced literal, plus twenty nodes with no binary clauses. Those interactions,
larger sizes and less explicit encodings remain broader coverage gaps.

**Second cost target:** graph discovery spends **27,451 visits**, versus 2,606 in
acquisition. Cases 47/59/55 reach covers after 4,415/4,415/3,335 visits. Full
historical replay still costs 13.3 s and dominates fresh query time.

Resume `experiments/results/cnf-binary-backbone/checkpoint.json`: **27,888 native
keys / twenty-two extensions**, preserving all earlier payloads. It lists both
optional backbone solvers; affine negatives retain `TerminalStore`. Eight roots
have alternative native evidence in the trials; the union preserves first
payloads and all three policies. Growth: 712,704 SQLite / 78,123 compressed bytes.
No default solver or unrestricted-SAT resource bound changes.

All **1,204 tests**, 35 focused tests, 360 chronological query audits and 24
affine-publication counter audits pass. The 221-page manuscript builds with all
64 old proof blocks unchanged and a clean final log. All 567 prior sources,
7,517 artifacts and 106 manifests are unchanged. Full tests retain 44 existing
SQLite warnings; focused tests have none. Final source ledger: **574**.
New manifest: **51 artifacts**. Next audit: **7,568 artifacts / 107 manifests**.

## Previous checkpoint: reuse partial binary backbones before splitting

[Binary implication covers](binary-clause-cover.md) now recognize a wider source
clause whose every literal is forced false by a satisfiable binary core. Source
paths compile into existing native proofs; the final two literals reuse a
contradictory cycle without another SCC search. Three covers in two fresh
random-three-CNF queries replace **eight expansions with six compiled children**.
Actual native additions fall only **226 -> 224**, by 2,174 payload bytes.

Mean query time improves **1.27%** and complete-worker time **0.40%**, with both
paired orders improving. Peak RSS rises about **9.53 MB**, and 44 examined
residuals still miss. The policy remains optional. The rejected compiler, which
made larger proofs, is retained with its mechanism checks. Do not report the
eight avoided expansions as eight avoided stored nodes.

**Next highest-coverage target:** new random-three cases **32/40/52**, still costing
**4,377/3,020/2,880 child propagation visits**. Use checked partial binary
backbones to avoid expensive branches even when no whole clause is covered.
Compare the induced source simplification and stored child proofs with the
existing split choice; include discovery and graph/path maintenance costs.
The earlier residual census has 44 partial backbones but only nine full covers.
Its fourteen repeated binary keys include directly published nodes and are not
established native-expansion cache hits.

**Second target:** graph discovery costs **24,645 visits**, against 953 during
acquisition. Cases 47/59/35 find covers after 3,485/3,485/3,107 visits. Earlier
cover admission remains promising. Full historical replay still costs 13.6 s.
These costs dominate the modest fresh leaf improvement.

Resume `experiments/results/cnf-binary-clause-cover/checkpoint.json`: **27,600
native keys / eighteen extensions**, preserving every earlier payload. Optional
native solver: `experiments.cnf_binary_clause_cover.AccountedBinaryClauseCoverSolver`.
Affine negatives retain `TerminalStore`. Three native alternatives remain in
trial archives; the union keeps first payloads. Comparator history grows the
union by 569,344 SQLite / 66,325 compressed bytes. There is no unrestricted-SAT
resource guarantee.

All **1,196 tests**, 27 focused tests, 240 chronological query audits and twenty
affine-publication counter audits pass. The 220-page manuscript builds with all
64 old proof blocks unchanged and a clean final log. All 560 prior sources,
7,478 artifacts and 105 manifests are unchanged. Full tests retain 44 existing
SQLite warnings; focused tests have none. Final source ledger: **567**.
New manifest: **39 artifacts**. Next audit: **7,517 artifacts / 106 manifests**.

## Previous checkpoint: residuals with satisfiable binary cores

[Binary-subset refutation](binary-subset-refutation.md) closes eight additional
native leaves on a fresh sixty-query stream. It removes **22 native nodes /
16,393 payload bytes** across random three-CNF and graph colouring, using the
existing source-indexed implication checker. Native additions fall **281 -> 259**.
All prior discovery evidence remains identical. The policy is optional: **76 of
84 SCC calls miss**, query timing has mixed signs, and mean complete-worker time
rises **0.82%** despite a 3.40% mean query reduction. Retain this regression.

**Next highest-coverage target:** new random-three cases **56 and 44** still pay
**5,159 / 5,117 child propagation visits**. Their remaining wide clauses interact
with satisfiable binary cores. Look for reusable binary graphs or conditional
compatibility descriptions that avoid repeated graph construction and splitting;
a satisfiable core alone cannot decide the full source. The current negative
rule is sufficient and source checked, without solving every such residual.

**Second target:** graph discovery spends **28,131 visits**, versus 4,724 in
acquisition. Cases 59/47/43 reach checked covers after 4,271/3,319/3,191 visits.
Earlier admission or reuse of cover evidence is still credible. Historical cold
replay remains about 13.5 seconds and dominates query time. Acquisition counters
alone do not determine total runtime.

Resume `experiments/results/cnf-binary-subset/checkpoint.json`: **27,368 native
keys / thirteen extensions**, preserving all prior payloads. The optional native
solver is `experiments.cnf_binary_subset.AccountedBinarySubsetSolver`; affine
extensions retain the explicit `TerminalStore` reader. Eight shorter native
alternatives remain in the trial archives; the union keeps the first proof for
each root. Selecting cheaper native alternatives without replacing history is
another reuse gap. This union grows 688,128 SQLite / 79,234 compressed bytes,
including comparator history. No unrestricted-SAT resource bound follows.

All **1,188 tests**, nineteen focused tests, 240 chronological query audits and
twelve affine-publication counter audits pass. The 220-page manuscript builds
with all 64 old proof blocks unchanged and a clean final log. All 553 prior
sources, 7,439 artifacts and 104 manifests are unchanged. Full tests retain 44
existing SQLite warnings; focused tests have none. Final source ledger: **560**.
New manifest: **39 artifacts**. Next audit: **7,478 artifacts / 105 manifests**.

## Previous checkpoint: recognize the expensive no-equation residuals

[Resumable affine sessions](affine-session-reuse.md) now run on a newly excluded
sixty-query stream. Three checked negatives replace 67 native nodes with three
extension certificates; nine other coupled inputs produce models. All twelve
coupled inputs avoid native expansion on this stream. The policies retain
identical discovery evidence. Combined additions fall **344 -> 280 certificates**
and payload **460,091 -> 384,362 bytes**. Mean query time falls **7.76%**; mean
complete worker time falls only **0.45%**, with both paired deltas negative.
Full cold replay remains about thirteen seconds. Sixty extension lookup misses
are charged; this fresh stream has no exact-target extension hits.

**Next highest-coverage target:** random three-CNF still expands **140 nodes /
27,761 propagation visits**. Start with saved fresh case 56 (33 nodes / 8,144
visits), then 44 and 52. Their affine extraction has no equations. Inspect
conditioned residuals for reusable clause/component descriptions and exact
recomposition, rather than treating a family label as a recognizer. Persist
counterexamples and account for discovery overhead on the other categories.

**Second cost target:** graph discovery spends 25,375 propagation visits, versus
5,416 in child acquisition. Cases 47/35 retain no proposal; case 59 reaches a
negative cover only after 4,271 discovery visits. Partial-cover completion and
early admission remain credible improvements. Gated Horn already avoids native
expansion but pays 12,579 discovery visits. Historical replay dominates total
runtime; propagation counts alone do not determine the largest wall-time saving.

Resume `experiments/results/cnf-affine-session/checkpoint.json`, using its
explicit `TerminalStore` reader and native/negative catalogs. It preserves every
prior payload and contains **27,087 native keys / ten extension certificates**.
Terminal-first replay no longer loads the alternative native proofs. The union
retains comparator results too, growing 888,832 SQLite bytes / 95,921 compressed
bytes over its parent. Broader recognition, hidden encodings, large free dimension
and extension-aware internal support scheduling remain open; native search still
cannot depend silently on versioned extension proofs.


All **1,181 tests**, twelve focused tests, 240 chronological query audits and
six negative publication-counter audits pass. All **548 prior sources,
7,399 artifacts and 103 manifests** remain unchanged. The final source ledger
has 553 entries, including the posthoc validator and analyzer. Full
historical native/composed/projection replay passes for every worker and the
union. The 219-page manuscript builds with all 64 existing proof blocks unchanged
and a clean final compiler log. The full suite retains 44 existing unclosed-SQLite
warnings; focused tests have none. No new Lean theorem is claimed.


New manifest: **40 artifacts**. Next preservation audit: **7,439 artifacts / 104 manifests**. Final source ledger: **553**.

## Previous checkpoint: adopt checked negative reuse on a fresh stream

[Negative affine publication](affine-negative-publication.md) now stores checked
row contradictions and complete-space exhaustion certificates in a versioned
extension table. Exact-source lookup and guarded negative composition are
explicit; native search and native payloads remain unchanged. Seven selected
negative targets replace **134 native nodes / 175,449 bytes** with **seven
extension certificates / 21,561 bytes**, avoiding 20,949 propagation visits.
Six controls keep the same 47 native nodes. Across thirteen exact prefixes,
combined new payload falls 229,996 -> 76,108 bytes and summed query time falls
0.13998 -> 0.05627 seconds. Both timing orders improve, including comparison-arm
costs, but this is a retrospective pilot, not a new coverage or stream result.

**Next concrete target:** integrate this explicitly versioned backend into a
newly excluded stream and its resumable query path. Measure lookup, discovery,
publication, guards, native fallback and full cold replay together. The preserved
union contains native alternatives as well as the seven new refutations; current
chain checking prefers those native alternatives and rechecks 134 native nodes.
Choosing the cheaper already-checked certificate is a separate reuse opportunity.
Never let native search silently depend on extension proofs its reader ignores.

All 26,743 native payloads are preserved. The optional extended checkpoint is
`experiments/results/cnf-affine-negative/checkpoint.json`; the last ordinary
production checkpoint remains `experiments/results/cnf-affine-completion/checkpoint.json`.
The extended archive grows 45,056 SQLite bytes / 4,627 compressed bytes because
it preserves both histories. Each unchanged control pays 8,192 empty-table bytes.
Broader coverage gaps remain: hidden/no-equation structure and large free
dimension. A complete projection onto leftover-clause variables is a candidate
for reducing the relevant dimension; it has not yet been implemented or priced.
The previous random-three-CNF frontier of 169 nodes remains unchanged.


All **1,177 tests**, 16 focused tests, 52 independently reconstructed comparison
arms and fourteen negative publication-counter audits pass. All **544 prior
sources, 7,171 artifacts and 102 manifests** remain unchanged. The final source
ledger contains 548 entries. All 26,743 native proofs and seven new negative
chains replay without acquisition. The 218-page manuscript builds with its
64 existing proof blocks unchanged and a clean final compiler log. The full
suite retains 44 existing unclosed-SQLite warnings; focused tests have none.


New manifest: **228 artifacts**. Next preservation audit: **7,399 artifacts / 103 manifests**. Final source ledger: **548**.

## Previous checkpoint: publish retained negative affine evidence

[Affine completion](affine-completion.md) connects the existing exact extractor
and checked basis routines to native positive publication. A Gray-order walk
reuses one basis XOR per next candidate and packed leftover clauses. Only a
model verified against the whole raw target changes acquisition; prior routes
keep priority. The total free dimension is capped at eight before basis
construction or enumeration, including variables absent from the equations.

Eight saved satisfiable coupled targets shrink **80 -> 8 nodes / 82,179 ->
10,860 native bytes**. On sixty fresh queries, nine added models reduce native
additions **395 -> 336 nodes / 482,568 -> 424,272 bytes**. Mean query time falls
about **11.00%**, with both orders improving, while complete-worker deltas have mixed signs. Full
cold replay still costs about 12.7 seconds. Diagnostics grow 7.86%; trial SQLite
falls 118,784 bytes and mean RSS falls 2.87 MB. These are finite matched gains,
without end-to-end dominance over the native baseline.

**Next concrete target: a checked negative publication interface.** The fresh
bridge already verifies one inconsistent system (case 29) and two exhausted
spaces (41/57, four/eight candidates). These still acquire **51 native fallback
nodes / 7,829 propagation visits**. Four saved negative coupled controls still
acquire 83 nodes. Preserve their exact source, extraction, row or basis evidence
and every rejecting leftover clause; price a compatible stored negative decision
and its cold replay against the current fallback. A small translation into the
current native proof kinds has not been established. If a versioned checker is
needed, keep all old proofs valid and make the new authority explicit.

**Broader coverage remains open.** Seventeen fresh bridge calls find no
extracted equations. Random three-CNF, unrecognized encodings and large free
dimension are outside this completion rule. A 2^d basis search is only bounded
because the policy enforces its cap. Exact projection, shared affine kernels
and better failure recognition remain candidates; none removes the general
SAT interaction or the cost of building the retained knowledge.

The lower-cost scheduling opportunity also remains: admit completed covers
inside the original probe pass and maintain clause coverage without repeated
full scans. This is distinct from closing the negative affine publication gap.

The fresh base discovery agrees on all 49 locally unfamiliar queries across
the two policies. Eleven neighbour queries become known after preparation;
neighbour case 4 remains unfamiliar behind two checked guards and adds ten
nodes in every policy. This is a shared control miss, not an affine regression.
Random three-CNF still adds 169 nodes / 28,452 acquisition propagation visits.
Fresh graph case 47 retains incomplete covers with two missing conditions per
candidate clause, beyond the one-extra-probe rule. These misses are preserved
alongside the negative affine publication target.

All **1,169 tests**, 24 focused tests, 324 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-affine-completion/checkpoint.json`:
**26,743 native keys**, preserving all 26,279 prior payloads, with 264 new
composed records alongside 4,719 inherited records, 2,957 ordinary decisions
and six projections. The union uses 82,378,752 database bytes / 6,217,639
compressed bytes. Twenty-six roots have alternate certificates in 67 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 539 prior sources,
6,871 artifacts and 101 manifests remain unchanged. The 217-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem,
native proof kind or unrestricted-SAT resource guarantee is claimed.


New manifest: **300 artifacts**. Next preservation audit: **7,171 artifacts / 102 manifests**. Final source ledger: **544**.

## Previous checkpoint: reuse affine discovery in costly coupled inputs

[Cover-directed probing](cover-directed-probe.md) closes the three saved missing
conditions with one extra probe each. One older control also benefits: four
saved parents shrink **52 -> 32 acquired nodes / 63,028 -> 38,503 native bytes**.
On sixty fresh queries, four extra conditions reduce acquisition **431 -> 407
nodes / 542,374 -> 512,936 bytes**. All 99 base probes and fourteen positive
publications remain. The extra conditions use the existing SCC solver and cover
compiler; no new proof kind or general search is used during publication.

Mean query time falls **10.22%**, with both paired deltas negative. Total
propagation falls **104,544 -> 98,303 visits**, including the extra conditions.
Complete-worker deltas have mixed signs and the mean rises about 0.023 seconds,
partly through cold replay. Diagnostics grow 0.82%, trial SQLite falls 36,864
bytes and mean peak RSS rises 1.61 MB. Native acquisition and query savings are
measured here; an end-to-end speedup or general memory bound is not established.
The overlapped first timing attempt is preserved and excluded; all sixty pilot
control deltas match the clean run.

**Largest remaining measured acquisition cost:** coupled parity and random
three-CNF still add **308 native nodes / 52,385 acquisition propagation visits**,
unchanged across policies. Coupled parity alone adds 163 nodes / 25,354 visits;
random three-CNF adds 145 / 27,031. These dominate the remaining native work.
The existing pattern-discovery layer already extracts explicit affine equations
and preserves leftover clauses, whereas this native acquisition path currently
has uniform and binary leaves. The next broad-coverage investigation should
measure a source-checked bridge from that existing affine extraction to native
acquisition on unlabelled coupled inputs: record rank, free dimension and
leftover interaction before choosing a completion rule. Charge extraction,
projection, checking and any enumeration; a 2^d free-coordinate search is only
cheap when d is small, not uniformly polynomial for arbitrary CNF. Positive
models require full-source verification and negative results require their own
checked recomposition. This is a concrete integration target, not an already
measured improvement.

**Smaller direct cost target: admit covers during the original pass.**
The four chosen covers had their required original conditions after 8, 5, 7
and 4 base probes, compared with eight executed for each. For those clauses,
early admission could avoid eight later probes. This retrospective observation
is not a tested early-selection policy. Track clause coverage as negative
conditions arrive, choose an explicit extra-probe budget, and compare the saved
suffix against maintenance, failed candidates and changed prefix choices.
Avoid repeatedly rescanning every source clause after each negative result.

**The larger structural gap is seeding families with no negative condition.**
This extension needs an existing partial cover. It does not admit new probes on
random three-CNF or coupled parity and leaves their interactions to native
acquisition. Broader positive discovery, shared nonbinary structure and covers
missing several conditions remain open. Unit-conflict conditions and clauses
shortened by baseline propagation also need checked composition. The remaining
cell still contains arbitrary SAT; compact covers are a restricted guarantee.

All **1,161 tests**, 24 focused tests, 300 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-cover-probe/checkpoint.json`:
**26,279 native keys**, preserving all 25,757 earlier payloads, with 240 new
composed records alongside 4,479 inherited records, 2,957 ordinary decisions
and six projections. The union uses 81,416,192 database bytes / 6,113,510
compressed bytes. Fourteen roots have alternate certificates in 27 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 534 earlier sources,
6,641 artifacts and 100 manifests remain unchanged. The 216-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem or
unrestricted-SAT resource guarantee is claimed.


New manifest: **230 artifacts**. Next preservation audit: **6,871 artifacts / 101 manifests**. Final source ledger: **539**.

## Previous checkpoint: complete nearly covered source clauses

[Negative clause-cover compilation](negative-cover.md) reuses retained
conditional refutations to publish an ordinary native parent proof. The three
motivating controls shrink **36 -> 24 nodes / 50,554 -> 33,240 native bytes**.
On sixty fresh queries, one newly recognized cover replaces fourteen fallback
expansions with eight compiled nodes: total additions fall **370 -> 364 nodes /
464,868 -> 457,715 bytes**. All fourteen positive publications and 95 probes
are preserved; independent comparison finds identical discovery on all 48
family queries. This improves acquisition after discovery, not the probe cost.

Paired query-time changes have opposite signs (-0.00440/+0.00963 s). Both
complete-worker changes are negative, but cold-replay variation explains much
of the mean 0.089-second reduction. Diagnostics grow about 0.05%, trial SQLite
size falls 12,288 bytes, and mean RSS rises 1.57 MB. Native certificate savings
are established on these cases; a stable query-time or general memory gain is
not. The compiler introduces no new proof kind, SCC solving or general search.

The next concrete discovery target is **cover-directed candidate admission**.
Fresh cases 51, 55 and 59 each have a source clause missing just one refuted
literal, and that literal lies outside the current candidate set. Case 51
needs -158 for [-158, -54, 16]; case 55 needs -156 for [-156, -113, -12]
(or 191 for [-151, -56, 191]); case 59 needs -320 for [-320, -71, 52].
These are candidates for measurement, not already checked extra conditions.
Charge the added probes and retain failures; the missing condition need not
have a binary residual or a cheap proof. Earlier stopping at a completed cover
and covers exposed by baseline propagation are separate opportunities. A gated
K4 regression preserves the latter recognition miss.

**The larger coverage gap remains the unresolved SAT interaction.** Random
three-CNF and coupled parity still cost **253 acquisition nodes / 47,204
acquisition propagation visits** on this stream, without access through the
negative binary filter. Graph discovery itself costs 24,650 propagation visits,
unchanged by compilation. Broader positive admission and shared nonbinary
structure remain necessary; completing the easy covers does not resolve them.

All **1,153 tests**, 24 focused tests, 294 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-negative-cover/checkpoint.json`:
**25,757 native keys**, preserving all 25,334 earlier payloads, with 234 new
composed records alongside 4,245 inherited records, 2,957 ordinary decisions
and six projections. The preservation union uses 80,306,176 database bytes /
5,993,018 compressed bytes. Eight roots have alternate certificates in sixteen
retained evidence occurrences. Ready/pending banks remain 132/38, 141/66,
87/89 and 87/116; there are no new support activations. Original structural
coverage remains 17/24 and supplemental positive coverage 24/24. All 529 prior
sources, 6,431 artifacts and 99 manifests remain unchanged. The 215-page
manuscript builds with all 64 existing proof blocks unchanged. No new Lean
theorem or unrestricted-SAT resource guarantee is claimed.


New manifest: **210 artifacts**. Next preservation audit: **6,641 artifacts / 100 manifests**. Final source ledger: **534**.

## Previous checkpoint: recompose retained negative conditions

[Mixed two-CNF completion](mixed-completion.md) now solves binary residuals
that fail both uniform witnesses, reusing the current canonical binding,
propagation assignment and residual. Four saved positive controls shrink
**14 -> 4 nodes / 6,163 -> 2,357 native bytes**. Twenty-one other saved contexts
retain their native certificates. A new sixty-query stream gains two mixed
model completions, reducing acquisition **385 -> 381 nodes / 437,869 -> 436,179
bytes** and premise probes **102 -> 89**. This broadens checked model recognition
under the same probe policy; it does not cover arbitrary CNF efficiently.

Mean query time falls **0.37242 -> 0.35566 s**, and complete-worker time
**24.06008 -> 23.88454 s**, with both paired differences negative. Much of the
complete-worker change is cold-replay variation, so it is not isolated as an
SCC benefit. Diagnostic sidecars grow **1.18%** and mean RSS about **1.91 MB**;
trial database size is unchanged. The fourteen SCC calls include twelve
negative conditions. Preserve these costs and misses alongside the gains.

**Next concrete target: a source clause covered by conditional refutations.**
Fresh case **59 in the mixed-completion stream** has checked negative
conditions under -141, 47 and 72, exactly covering source clause
[-141, 47, 72]. Every parent model must satisfy one of these literals; each
condition is unsatisfiable. The cover therefore supplies an exhaustive parent
argument. Current acquisition still uses twelve native nodes. Implement a
source-bound combined certificate with independent checking, persistence and
a matched cost comparison. Charge all conditional discovery and certificates;
a single negative condition is never a parent refutation. The posthoc evidence
retains premise indices and residual bindings for resumption. The same pattern
appears in saved mixed-controls 43 and 47. These three parent acquisitions total
**36 nodes / 50,554 bytes**, before charging any combined-certificate cost.
There are no repeated exact ordered residuals among the fourteen fresh SCC
attempts within a query, so simple exact memoization is not the current target.

**Broader discovery remains the larger unresolved problem.** Random three-CNF
and coupled parity cost **272 acquisition nodes / 43,685 propagation visits**
on the current stream, without any probes admitted by the negative binary
filter. Positive witnesses outside that filter and wider shared interactions
remain open. Direct model publication can also omit intermediate nodes useful
for later queries; measure that tradeoff on subsequent expansions. General SAT
still reduces to the residual cell outside the uniform and binary recognizers.
The manuscript gives the construction and a 257-formula audit supports it.

All **1,145 tests**, 25 focused tests, 292 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-mixed-completion/checkpoint.json`:
**25,334 native keys**, preserving all 24,922 earlier payloads, with 232 new
composed records alongside 4,013 inherited records, 2,957 ordinary decisions
and six projections. The union uses 79,339,520 database bytes / 5,889,616
compressed bytes. Four roots have alternate certificates in eight retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116; no new activation is attributed to this policy. Original structural
coverage remains 17/24, supplemental positive coverage 24/24. All 524 prior
sources, 6,228 artifacts and 98 manifests remain unchanged. The manuscript
builds at 214 pages with all 64 existing proof blocks unchanged. The finite
embedding audit checks 257 formulas (255 SAT / two UNSAT).

New manifest: **203 artifacts**. Next preservation audit: **6,431 artifacts / 99 manifests**. Final source ledger: **529**.

## Previous investigation: mixed residual acquisition after early positive stopping

[Inline completion](inline-completion.md) now stops discovery at the first
checked positive completion. It reuses the live propagation assignment,
residual and canonical binding. On sixty new excluded queries, probes fall
**190 -> 106**, discovery/acquisition propagation **171,670 -> 109,554** and
gated-Horn propagation **72,205 -> 10,484**. Selection normalization falls
80,200 -> 31,510 literal occurrences. Candidate ranking and budget are unchanged;
unvisited candidates are explicitly outside the executed prefix.

The thirteen model publications and 446 acquired native nodes are unchanged.
Four valid alternative models change total native payload by only three bytes.
Mean query time falls **0.45709 -> 0.42358 s** (both orders), and diagnostic
sidecars fall **11.16%**. Complete workers instead rise **23.24245 -> 23.40440 s**
(both orders). Cold replay dominates at about 11.4 s. Native database size and
process RSS do not materially improve. Keep this measured discovery saving
separate from total runtime, native-state growth and broader SAT coverage.

**Next concrete coverage target:** integrate a mixed two-CNF model using the
live conditioned residual. Posthoc analysis of this run checks **thirteen
positive conditions on fresh cases 15/27/39/51**. Their current parent
acquisition totals **14 nodes / 6,163 bytes**. Four direct models could avoid
part of that work, but discovery, SCC solving, transport and verification still
need a timed comparison. The same audit checks fifteen negative conditions on
fresh cases 43/47/55/59, whose parents acquire **54 nodes / 75,511 bytes**.
Negative parent recomposition remains open. These are this run's case IDs;
retain the previous study's case 39 and 43/51/55/59 as separate fixed controls.

**Largest unresolved fresh acquisition:** random three-CNF and coupled parity
still consume **329 acquisition nodes / 56,622 propagation visits**. The negative binary filter offers
no premise probes there. Investigate positive discovery outside that filter
and shared conditional structure, with explicit misses and complete cost.
Graph acquisition still costs **11,452 propagation visits**. The inline policy
performs 106 checks including 93 misses; broader recognition must earn its cost.
General-SAT interaction, compact closure and uniform polynomial bounds remain
open. Incremental replay could address the largest complete-worker cost, but
must retain the independent full inherited audit as its comparator.

All **1,137 tests**, 24 focused tests, 276 independent counter audits and
full reconstruction pass. Resume `experiments/results/cnf-inline-completion/checkpoint.json`:
**24,922 native keys**, preserving all 24,444 prior payloads, with 216 new
composed records alongside 3,797 inherited records, 2,957 ordinary decisions
and six projections. The union uses 78,471,168 database bytes / 5,788,630
compressed bytes. Alternate certificates for eight roots remain in fifteen
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116; no frontier activation is attributed to this change. Original structural
coverage stays 17/24 and supplemental positive coverage 24/24. All 519 prior
sources, 6,073 artifacts and 97 manifests remain unchanged. The manuscript
builds at 213 pages with all 64 existing proof blocks unchanged.

New manifest: **155 artifacts**. Next preservation audit: **6,228 artifacts / 98 manifests**. Final source ledger: **524**.

## Previous investigation: mixed two-CNF conditions and earlier positive stopping

[Uniform conditioned completion](uniform-premise.md) now recognizes exact
all-false/all-true residual models after a checked saved unit trace. This covers
unit-closed Horn and dual-Horn residuals and broader sign patterns. Failure of
both completions remains unresolved; a fresh-variable conjunction embeds general
SAT in that remaining cell. The manuscript and a 256-formula finite audit make
this limitation explicit.

On sixty fresh queries, **nine additional gated-Horn targets** accept the new
route. With the three previous positive recoveries, all twelve gated targets
publish one model each. New native additions fall **452 -> 434 nodes** and
**535,908 -> 521,248 bytes**. The 27 avoided expansions require nine model
publications. The selector also pays for **96 failed graph-colouring attempts**;
all are retained. Seventeen exact-prefix controls preserve the earlier successes
and difficult misses; the new case 14 shrinks three nodes to one.

Mean query time changes **0.44913 -> 0.44780 s**, with opposite paired signs.
Complete-worker differences are **-0.22305/-0.36887 s**, but two runs do not
establish general scaling. Diagnostic sidecars grow **2.83%**. Native baseline
still has cheaper queries, and full cold replay dominates at about 11.2 seconds.
Keep native proof savings, diagnostic storage and total runtime separate.

**Next coverage target:** mixed two-CNF conditions that fail both uniform
completions. Posthoc SCC analysis finds twenty conditions on five fresh graph
queries. Case **39**, from this study's fresh stream, has four mixed models
already transported and checked against the raw target-plus-assumption; current
acquisition is three nodes / 1,444 bytes. Integrate and price one such model at
the saved prefix. Cases **43/51/55/59** have sixteen checked contradictory
implication paths and currently acquire 52 parent nodes in total. Investigate
native conditional refutation publication and the existing guard interface,
complementary branches or checked symmetry transport. A single negative
condition must never stand in for a parent refutation. SCC diagnosis is not yet
a timed acquisition policy. These case IDs refer to the current fresh corpus,
not earlier historical controls with the same numbers.

**Largest avoidable discovery cost:** the twelve gated inputs still pay
**74,194 propagation visits**, followed by zero acquisition propagation.
The current wrapper finishes the earlier probe pass before checking completion.
Fuse checked positive completion into discovery and measure early stopping,
retaining the present policy as a comparator. Reuse bound canonical forms where
possible. No extra probes or changed budgets should be hidden in this comparison.

Random three-CNF and coupled parity still cost **320 acquisition nodes / 54,301
propagation visits**; no saved uniform attempts are available after filtering.
Positive discovery outside the negative binary filter, wider interactions,
compact closure and uniform arbitrary-SAT bounds remain open. Keep successful
model controls, historical guards/regressions and unresolved 0/131/159.


All **1,129 tests**, 23 focused tests, 138 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-uniform-premise/checkpoint.json`:
**24,444 native keys**, preserving all 23,987 prior payloads, with 216 new
composed records alongside 3,581 inherited records, 2,957 ordinary decisions
and six projections. The union uses 77,484,032 database bytes / 5,677,574
compressed bytes. Five alternate model payloads remain preserved (fourteen
occurrences). Ready/pending banks are 132/38, 141/66, **87/89** and **87/116**.
The two gains refer to one 568-byte negative certificate acquired by shared
ordinary preparation for neighbour case 1 in every mode: causal core 46 and
incremental-causal core 51. This activation is not a uniform-policy gain.
All 514 earlier sources, 5,918 artifacts and 96 manifests remain unchanged.
The paper builds at 212 pages with all 64 existing proof blocks unchanged;
structural authority and original coverage remain unchanged. No new Lean theorem
or unrestricted-SAT resource bound is claimed.

New manifest: **155 artifacts**. Next preservation audit: **6,073 artifacts / 97 manifests**. Final source ledger: **519**.

## Previous investigation: solve and lift nonterminal conditioned families

[Positive-premise recovery](positive-premise.md) now reuses a model already
present in saved discovery. Case 50 falls from three acquired nodes / 2,503
native bytes to one checked model node / 1,482 bytes. Thirteen earlier control
contexts retain their exact certificates. Fresh gated-Horn cases 26/54 also
close this way: total additions fall **410 -> 406 nodes / 472,534 -> 469,867
native bytes**, with two model publications and six fewer expansions. Existing
search limits, admitted choices and the candidate prefix remain unchanged.

This is a small measured acquisition saving. Mean query time falls
**0.4220 -> 0.4018 s**, but complete-worker paired differences are
**-0.2144/+0.0855 s**. Diagnostic sidecars grow about 0.36%; process RSS is
essentially unchanged. Discovery costs remain, and native baseline still uses
only 0.3507 s query time versus 0.4018 s. Full cold replay remains about 10.8 s.
Do not present this as a general end-to-end or memory scaling improvement.

**Next discovery priority:** use the already saved propagation trace and source
mapping to solve and lift **nonterminal conditioned Horn, dual-Horn and two-CNF
residuals**. The earlier audit found 89 recognized/constant candidates across
20 targets. Start with the gated-Horn conditions: current discovery pays
73,886 propagation visits against 5,751 acquisition visits after recovery.
A checked positive child model suffices for its parent. A negative condition
requires the other branches or another sound parent certificate. Charge family
recognition, residual solving, transport and verification; avoid replaying the
baseline propagation. Preserve case 50 and fresh 26/54 as positive controls,
146 as positive-child control, guards 43/172, regression 144, and misses
0/131/159. Apply the same recognition to unlabelled mixed and edited inputs.

**Remaining discovery restriction:** recovery scans only already retained
attempts after the old selector finishes. Earlier positive stopping, candidate
ranking and a positive-witness path outside the negative binary filter remain
open. The explicit no-binary positive example is retained in the tests.
The signed negative-probe filter remains supporting work, not implemented.
Random three-CNF and coupled parity still account for 257 acquisition nodes /
46,651 propagation visits; the new recovery path does not help them. Efficient
coverage of arbitrary CNF and a uniform polynomial resource bound remain open.


All **1,120 tests**, 31 focused tests, 135 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-positive-premise/checkpoint.json`:
**23,987 native keys**, preserving all 23,577 prior payloads, with 210 new
composed records alongside 3,371 inherited records, 2,957 ordinary decisions
and six projections. The union uses 76,537,856 database bytes / 5,571,577
compressed bytes. Three alternate model payloads remain in measured evidence
(six occurrences); preserved native payloads are never replaced. Ready/pending
banks remain 132/38, 141/66, 86/90 and 86/117. All 508 earlier source fingerprints,
5,780 artifacts and 95 manifests remain intact. The paper builds at 212 pages
with all 64 existing proof blocks unchanged. The initial replay validator's
scratch-directory failure and its separate corrected replay revision are retained.
No new Lean theorem, structural authority or unrestricted-SAT bound is claimed.

New manifest: **138 artifacts**. Next preservation audit: **5,918 artifacts / 96 manifests**. Final source ledger: **514**.

## Previous investigation: reuse positive premise results and conditioned families

[Residual binary filtering](binary-probe.md) is implemented as an optional policy.
It preserves the original candidate prefix and all selected results. On 60 new
queries it removes **192/386 probes**, cuts discovery/acquisition propagation
**252,999 -> 179,463 (29.07%)**, and reduces query/warm sidecars **15.13%**.
All modes retain identical **450 new rows / 521,286 native bytes**. Twenty-six
historical arms preserve all certificates, useful guards and model recovery;
none permits a skip, so they retain the incidence-scan overhead as controls.

**Do not infer a total runtime improvement.** Query differences have opposite
signs; complete workers are **21.947/22.234 s** for previous/filtered policies.
Cold replay remains about 10.8 s. Native baseline uses only 69,351 propagation
visits. This is a verified discovery-work and trace-storage reduction, with
unchanged native proof space and no general speedup established.

The user's SAT-to-SAT reduction suggestion now frames this search explicitly:
construct and check low-cost transformations to acquired or tractable targets,
including matching and model/proof transport in the cost. Cheap conversion alone
does not solve an unfamiliar hard target. Conditioning needs exact branch
recomposition; polynomial online lookup with expensive offline compilation is a
different claim from a uniform polynomial decider. See the source-backed
[reduction discussion](binary-probe.md#remaining-gaps) and manuscript oracle section.

**Next discovery priority:** the saved premise screens expose 89 recognized
conditioned residuals across 20 targets. In case 50, assumption `-169` already
closes positively, and independent transport verifies a complete target model.
The selector ignores it because it looks only for a unit conflict, then acquires
three rows / 2,503 bytes. Implement checked positive-premise recovery and price
it at that saved prefix. Follow with Horn/dual-Horn/two-CNF conditional results
and exact recomposition; family recognition alone is not a SAT decision. One
refuted condition does not refute the parent. This new model/publication route
is not implemented or timed. Keep candidate filters scoped to negative unit
probes so they do not silently remove positive-witness opportunities.

**Supporting refinement:** keep signed binary incidence after consistent
unit closure. An unassigned candidate needs its falsified literal in a residual
binary clause to seed another unit. The posthoc audit identifies **83 remaining
futile probes / 28,774 visits** (35 gated Horn, 48 graph-colouring probes).
Implement and price this signed filter without refilling the original candidate
prefix, retain successful historical guards and the propagation-created-binary
counterexample, and reuse the existing baseline trace. This stronger condition
is not implemented or timed yet. It does not decide SAT or deeper closure.

**Next acquisition targets:** gated Horn pays 75,825 discovery visits against
6,572 native visits. Random 3-CNF and coupled parity still account for 279/432
new-family acquisition rows and 45,877/66,607 visits. Investigate mixed-family
conditioning and affine/leftover reuse at saved prefixes; preserve old cases
32/56/52/21 and 0/131/159, positive controls 36/146 and useful/regressing guards
43/172/144. Recognition, state checking and persistence must remain charged.

All **1,113 tests**, 24 focused tests and independent reconstruction pass.
Resume `experiments/results/cnf-binary-probe/checkpoint.json`: **23,577 native
keys**, all 23,127 earlier payloads, **206 new composed records**, 3,165 earlier
composed records, 2,957 ordinary decisions and six projections. No alternate
payloads are needed. The union occupies 75,649,024 database bytes / 5,474,412
compressed bytes. Ready/pending banks remain 132/38, 141/66, 86/90 and 86/117.
Prior 503 sources / 5,655 artifacts / 94 manifests, structural authorities and
all 64 manuscript proof blocks remain unchanged. The 211-page paper builds
without overfull or undefined warnings. No new Lean theorem or unrestricted-SAT
resource bound is claimed.


New manifest: **125 artifacts**. Next preservation audit: **5780 artifacts / 95 manifests**. Final source ledger: **508**.

## Previous investigation: reject structurally futile discovery probes

[Cross-family evaluation](cross-family.md) now separates raw-query novelty from
unfamiliar acquisition. All 48 new-family targets remain unfamiliar after
preparation; all 12 same-template controls become known. Four matched workers
retain identical **398 new rows / 483,695 native bytes**. Optional discovery
makes **384 unsuccessful probes**, increasing propagation **65,842 -> 246,726**
and mean query time **0.354 -> 0.482 s**. Both paired timing differences are
positive. This is preserved negative evidence, not broader tractability.

**Next concrete improvement:** after consistent baseline unit propagation, skip
single-literal unit-refutation probes for unassigned variables absent from all residual
binary clauses. Such an assignment cannot create a unit or empty clause. The
posthoc audit identifies **192 futile probes / 73,488 propagation visits** in
random 3-CNF and coupled-parity inputs. Build the incidence set once, reuse the
baseline trace, validate the residual/source coordinate mapping and preserve
successful older guards. The condition must inspect the propagated residual;
original clause widths are insufficient. The filter is not implemented or timed
in this checkpoint. Keep all unsuccessful screens as matched controls.

**Next structural acquisition targets:** random 3-CNF and coupled parity cost
**261/386 new acquisition rows**, with **47,263/65,842 acquisition propagation
visits**. Saved cases 32/56/52 and 21 are the largest propagation controls.
Gated Horn/dual-Horn has the largest discovery overhead despite cheap native
solving. Investigate mixed-family conditioning and affine/leftover reuse at
these exact prefixes. Preserve older 0/131/159, positive model recovery 146,
one-variable two-CNF decomposition 36, useful guards 43/172 and regression 144.

Cold replay (**10.611/10.700 s**) still dominates complete workers
(**21.512/21.963 s**). Query/warm sidecars roughly double, **1.162 -> 2.311 MB**,
while native storage is identical. Filtering these probes can reduce wasted
acquisition work but cannot alone deliver a large complete-runtime gain.
The fixed corpus has four finite generators, no general scaling or coverage
claim, and no new solver policy or structural authority.

All **1,106 tests**, 12 focused tests and independent reconstruction pass. The
new checkpoint is `experiments/results/cnf-cross-family/checkpoint.json`:
**23,127 native keys**, all 22,729 old payloads, **120 new composed records**,
3,045 previous composed records, 2,957 ordinary decisions and six projections.
There are no alternate native payloads. The union occupies 74,706,944 database
bytes / 5,364,377 compressed bytes. Ready/pending banks remain 132/38, 141/66,
86/90 and 86/117. All earlier 498 sources, 5,617 artifacts and 93 manifests
are unchanged. Structural authorities and all 64 manuscript proof blocks remain
unchanged. The 209-page manuscript builds without overfull or undefined warnings.


New manifest: **38 artifacts**. Next preservation audit: **5655 artifacts / 94 manifests**. Final source ledger: **503**.

## Previous investigation: broaden unfamiliar residuals and price nonterminal decompositions

[Positive-child model recovery](positive-child.md) is implemented. At the exact
case-146 prefix, it lifts 26 child unit deductions to a checked whole-target
model and publishes **one native row instead of six**. Added native bytes fall
**6,688 -> 1,798 (73.12%)**, and propagation **3,304 -> 2,045** against the previous
policy. It acquires neither the proposed negative premise nor child node. Native
baseline still uses fewer visits (1,847); the single timing sample is not a
general speedup. The other twelve equal-state controls preserve prior payloads.

**The fresh workload now scarcely exercises new residual acquisition.** On
another 192 excluded query roots, **190 targets are known after preparation**.
The two discovery calls use an existing propagated residual or unit conflict;
the new model-recovery route never activates. All policies add identical
**197 rows / 441,084 native bytes**: 195 rows from ordinary preparation and two
from target acquisition. Propagation is 1,831 visits in every mode. Opposite
timing-pair signs establish no new gain. Raw query novelty is not child novelty.

**Next priority:** extend the evaluation to different template families and
report pre-query target familiarity as well as root exclusion. Keep these
well-covered neighbours as warm-reuse controls, charge generation/preparation,
and compare matched policies on unfamiliar residuals. Do not count this stream
as broader arbitrary-SAT coverage or keep using more same-template neighbours
as the sole transfer test.

**Retained structural targets:** prior cases 0/131/159 still have nonfamily
children after the proposed condition and propagation. Price alternative small
conditioning sets and cached-dependency reuse at their exact prefixes, retaining
case 146 as the model-recovery control and older case 36 as the known one-variable
two-CNF decomposition. The prior failed single-variable test concerned immediate
syntactic two-CNF; further propagation and mixed-family closure remain open.
Preserve useful historical 43/172 and regressing 144 controls. No absolute
residual-size threshold or small-decomposition guarantee is established.

Cold replay remains the largest complete-time component (**10.282/10.111/10.107 s**).
Shared checking and compact source references remain supporting total-cost targets.
The new result changes a restricted positive publication path; it adds no new
general structural authority, Lean theorem or unrestricted-SAT bound.

All **1,102 tests**, 26 focused tests and independent replay pass. Resume
`experiments/results/cnf-positive-child/checkpoint.json`: **22,729 keys**, all
22,532 previous payloads, **615 new composed records**, 2,430 earlier composed
records, 2,957 ordinary decisions and six projections. Prior **493 sources /
5,455 artifacts / 92 manifests** and structural authorities remain unchanged.
Ready/pending banks are 132/38, 141/66, 86/90 and 86/117.

New manifest: **162 artifacts**. Next preservation audit: **5617 artifacts / 93 manifests**. Final source ledger: **498**.

## Previous investigation: recover models from positive-terminal proposed children

[Retained-prefix fallback](trace-fallback.md) now reuses baseline unit traces
when discovery rejects a guard. It keeps the original target and ordinary
residual solving; the rejected guard is not acquired. At the saved case-36/186
prefixes, visits fall **5,299 -> 4,046 / 3,608 -> 3,234**, preserving every native
payload. Twenty-seven equal-state arms retain all previous controls. Fewer
expansion calls are accompanied by explicit trace publications, not fewer rows.

**Fresh transfer is measured, but total savings remain limited.** Three of the
next 192 queries reuse a prefix. Previous/new visits fall **24,342 -> 22,811
(6.29%)**, with identical **269-row / 527,030-byte additions**. Sidecars grow
0.077%; opposite timing-pair signs establish no stable speedup. Native baseline
uses **14,126 visits / 271 rows**. Discovery still adds 61.48% propagation work
against baseline, so keep the policy optional. The earlier propagated-residual
route has two hits on this stream; both optional policies share them.

**Most concrete next win: the gate misses case 146's positive closure.** Its proposed
child has 26 checked unit deductions and **no remaining clauses**. The gate
accepts known children or unit conflicts, so it misses this positive closure.
The posthoc diagnostic verifies the canonical child model. Next, lift it through
the proposed assignment, check the original target, and publish that SAT witness
directly when valid. This can avoid acquiring an unnecessary negative premise;
measure actual rows and total costs before claiming savings. The original-target
model transport and alternate publication have not yet been implemented or timed.

**Next unresolved structural targets: cases 0/131.** These account for **17/14
of 43 remaining child expansions**. Case 0 has no baseline forced prefix and
pays 1,908 extra discovery visits. After the proposed condition and propagation,
cases 0/131/159 retain nonfamily residuals of **139/119/125 literals**. Price
alternative conditioning and cached dependencies at equal prefixes, retaining
historical useful 43/172 and regressing 144 controls. Do not route by size alone.

None of the four baseline residuals (0/131/146/159) has one variable whose two
immediate restrictions are syntactic two-CNF. This complete syntactic test does
not exclude closure after further propagation. Retain the negative controls and
the previous case-36 positive decomposition; its alternate acquisition cost
remains unmeasured. No small-conditioning-set guarantee holds in the current
argument for arbitrary CNF.

Cold replay remains the largest full-time component (**9.031/9.091/9.017 s**).
Shared checking and compact sources remain supporting targets. The stream still
comes from three old templates and gives no new general structural authority.

All **1,094 tests**, 25 focused tests and independent replay pass. Resume
`experiments/results/cnf-trace-fallback/checkpoint.json`: **22,532 keys**, every
22,259 prior payload preserved, **603 new composed records**, 1,827 earlier
composed records, 2,957 ordinary decisions and six projections. All **488 prior
sources / 5,329 artifacts / 91 manifests** and structural authorities are
preserved. Ready/pending frontiers are 132/38, 141/66, 85/91 and 85/118.

New manifest: **126 artifacts**. Next preservation audit: **5455 artifacts / 92 manifests**. Final source ledger: **493**.

## Previous investigation: reuse saved propagation after discovery rejects a child

[Propagated-residual reuse](propagated-reuse.md) is implemented and independently
checked. At the exact prefix of case 85, propagation falls **5,750 -> 955** and
four premise probes disappear. Storage remains **one row / 1,672 native bytes**;
one trace publication replaces the expansion call. The other six equal-state
controls preserve the old gate's payloads and propagation, including its misses
on useful historical 43/172 guards.

**The next excluded stream has no new residual hits.** All three policies answer
99 SAT / 93 UNSAT queries. Baseline/admission/propagated rows are **215/199/199**,
and propagation visits **9,528/14,907/14,907**. Both admission policies produce
identical native payloads. The additional lookup/recognition adds sidecar bytes
(**+0.12%**); opposite timing-pair signs establish no stable speedup. Keep this
path optional. The existing gate's row saving is not a gain from the new check.

**Most concrete expansion gap: fresh cases 36/186.** These account for all
**11 remaining child expansions (5/6)**. Their absent, nonfamily residuals follow
saved prefixes of **13/1 forced variables**, but rejected discovery falls back
to the original target and repeats propagation. Reuse the retained unit trace
on this fallback, then acquire the unknown residual. Preserve source/model
binding and native dependency choice; measure equal-state positive and rejection
controls before another excluded stream. Residual solving remains unrestricted.

**Coverage opportunity:** case 36's residual has 11 variables, 23 clauses and
49 literals. Each of its three wide clauses contains canonical variable 6;
both assignments produce two-CNF. The read-only diagnostic retains both branches
and checks all 2,048 assignments. Case 186 has no single-variable counterpart.
Charge recognition and two-branch checking before claiming a saving; this
decomposition has not been acquired or timed. Avoid an absolute size threshold.

Cold replay remains the largest measured complete-time component (means
**13.001/13.639/12.760 s**). Shared checking and compact sources remain supporting
targets. The fresh queries come from three old templates, not arbitrary-SAT
coverage. No new structural authority, Lean proof or unrestricted efficiency bound.

All **1,085 tests**, 21 focused tests, 21 equal-state arms and six fresh workers
validate. Resume `experiments/results/cnf-propagated-reuse/checkpoint.json`:
**22,259 keys**, all 22,036 prior payloads preserved, **597 new composed records**,
1,230 previous composed records, 2,957 ordinary decisions and six projections.
All **483 prior sources / 5,222 artifacts / 90 manifests**, frontier lineages
and structural authorities are preserved.

New manifest: **107 artifacts**. Next preservation audit: **5329 artifacts / 91 manifests**. Final source ledger: **488**.

## Previous investigation: reuse propagated residuals before trying new premises

[The fixed gate on another 192 excluded queries](child-stream.md) reduces new
native rows **229 -> 221** and added native bytes **460,398 -> 448,420**, but
propagation rises **5,590 -> 11,343**, sidecars grow **2.44%**, and observed mean
complete time rises **28.229 -> 31.695 seconds**. Both timing pairs regress.
Eight explicit trace publications accompany the **17 -> 1** expansion reduction.
Keep the gate optional; fewer expansion calls are not a total-cost improvement.

**Most concrete expansion opportunity: new case 85.** Baseline propagation fixes
23 variables and exposes the already checked SAT root `cnf-residual-v1:[[-2,-1]]`.
The diagnostic verifies its 80-byte payload and lifts the cached model to the
restricted target using the saved forced assignments. The current policy still
tries four premises, then repeats propagation during fallback: **4,795 + 955**
visits against baseline's **955**. The extra 4,795 visits explain most of the
5,753-visit stream increase. This is a checked opportunity, not an implemented
or timed improvement.

**Next:** immediately after baseline propagation, check the normalized residual
for a cached answer or cheap native family before ranking/probing. Reuse the
retained unit trace for publication and preserve exact source/model binding.
Measure case 85 at its saved prefix, retain no-hit/nonterminal and earlier 43/172
controls, then use another excluded stream. Charge recognition, normalization,
lookup, checking and persistence. Avoid fitting a size threshold to saved cases.

Cold replay is still the largest complete-time component (**15.985 / 21.513 s**).
Compact source references and shared checking remain supporting total-cost targets.
The fresh roots come from three old templates, not arbitrary-SAT coverage; two
pairs and process RSS establish no general timing or memory bound.

All **1,076 tests**, 19 focused tests and independent cold/prefix checks pass.
Resume `experiments/results/cnf-child-stream/checkpoint.json`: **22,036 keys**,
all 21,801 old payloads preserved, **384 new composed records**, 846 previous
composed records, 2,957 ordinary decisions and six projections. All **480 prior
sources / 5,186 artifacts / 89 manifests**, frontier lineages and structural
authorities remain preserved. No new Lean or unrestricted-SAT bound.

New manifest: **36 artifacts**. Next preservation audit: **5222 artifacts / 90 manifests**. Final source ledger: **483**.

## Previous investigation: broaden child admission without repeating costly rejection

[Restricted-child admission](child-admission.md) now has eighteen equal-state
controls. At the preceding trial's exact prefixes, case 144 returns from
**11 to 3 rows**, while cases 167/190 retain **2/2 rows**. Across these three
selected controls the gate uses **7 rows**, compared with **15** for both native
baseline and unconditional local discovery. Native bytes are **12,840** versus
28,490 / 23,872; serialized delta/record bytes are **73,439** versus 78,189 / 90,645.
This is a retrospective control result, not a fresh-stream improvement.

**The gate is too restrictive for useful nonterminal children.** It rejects
historical 43/172, losing their 10/9 -> 7/7 row savings. Historical propagation
rises **4,501 -> 8,666** against baseline. Even the three positive/regression
controls use **5,285** propagation visits against baseline's **4,821** because
case 144 pays discovery and screening before fallback. Keep this policy optional.

The admitted path publishes at most two native rows and performs no general
child expansion; earlier preparation, proof checking and fallback remain charged.
After propagation, all four rejected children are unknown and outside the cheap
syntactic families. Beneficial case 172 leaves **112 literals**, versus **111**
for regressing case 70, so an absolute smaller-residual threshold cannot separate
them. Cached dependency transport and broader bounded child proofs remain open.

**Next:** measure the fixed gate on another excluded query stream, preserving the
six equal-state controls. Charge rejected probes; investigate reuse of their
propagation traces and structural tests for useful nonterminal children. Do not
promote a posthoc size threshold or the selected eight-row recovery to a general
claim. Compact source references and shared cold replay remain supporting targets.

All **1,076 tests**, 19 focused tests and independent cold checks pass. Resume
`experiments/results/cnf-child-admission/checkpoint.json`: **21,801 native keys**,
the exact previous archive, **18 new composed records**, 828 prior composed records,
2,957 ordinary decisions and six projections. Prior **475 sources / 5,115 artifacts
/ 88 manifests**, four frontier lineages and structural authorities are preserved.
No new Lean or unrestricted-SAT bound. Single-sample arm times establish no stable
runtime or peak-memory gain; these controls exclude repeated bank preparation.

New manifest: **71 artifacts**. Next preservation audit: **5186 artifacts / 89 manifests**. Final source ledger: **480**.

## Previous investigation: reject costly forced residuals before acquisition

[Target-local discovery](local-guard.md) now has six historical controls and
four matched streams on **192 new neighbouring CNFs**. It finds guards without
another core-bank scan, reusing baseline propagation for ranking. Historical
rows improve **23 -> 19**, but fresh rows remain **250 -> 250**. Expansion calls
fall **19 -> 12** only alongside **seven trace publications**. Fresh native bytes
fall **0.93%**, propagation rises **17.53%**, serialized records grow **1.19%**,
and observed mean complete time rises **17.337 -> 20.173 s**. Keep the route optional.

**Dominant remaining search gap: fresh case 144.** Its forced `270=true` route
grows **3 -> 11 rows**, accounting for **10/12 remaining child expansions**.
Baseline uses a pre-existing 61-clause / 159-literal negative dependency; the
conditioned child has no pre-query dependency hit and needs three splits. In
contrast, fresh cases **167/190** improve **8/4 -> 2/2 rows** because their
restricted children close by unit propagation. The saved proof frontiers identify
the cached root; no cofactor transport or minimum-cost conclusion is established.

**Next:** screen the restricted child before publishing a guard. Test a known
native answer or retained unit-terminal proof as an admission condition, preserve
cheap native-family priority, and fall back on case 144's nonterminal child.
Reuse premise and child traces. Measure exact-prefix controls, then another
excluded set; do not count the posthoc eight-row recovery as a deployed saving.
Retain historical 43/172 as useful nonterminal cases that a strict gate would
miss. Investigate checked transport of the baseline cached dependency only when
its recognition and certificate costs can be charged.

Cold replay remains the largest full-cost component (means **8.681 / 10.463 s**).
Compact references for duplicated guard sources and shared cold checking are
supporting targets. Two timing pairs and process peak RSS establish no general
speedup or live-memory bound. New queries remain from three neighbouring-input
families; arbitrary-SAT coverage and uniform efficiency are separate obligations.

All **1,069 tests**, six historical and four fresh audits, 2,957 ordinary and
828 composed records plus six projections pass. Resume
`experiments/results/cnf-local-guard/checkpoint.json`: **21,801 keys**, all 21,528
old payloads preserved and no alternative payloads. Prior **469 sources / 5,057
artifacts / 87 manifests**, four frontiers, structural authorities and 64 proof
blocks remain preserved. No new Lean or unrestricted-SAT bound.

New manifest: **58 artifacts**. Next preservation audit: **5115 artifacts / 88 manifests**.

## Previous investigation: price bounded target-local discovery and retain fallback

[Single-assumption guard acquisition](assumption-guard.md) is now priced. Cases
43/172 improve from **10/9 -> 7/8 native rows**, but 70 regresses **4 -> 5**.
Across the three historical cases, rows fall **23 -> 20** and native bytes fall
**16.99%**, while propagation visits rise **31.24%** and serialized results grow
**10.91%**. Retaining unit traces avoids 1,166 repeated propagation visits versus
direct premise solving; both routes store identical proofs. No stable total-time
or peak-memory gain follows. Keep the optional route and the rejection control.

**Highest-priority discovery gap:** the two priced candidates still came from a
roughly 32,000-literal full-bank conditioning scan. A checked read-only local
ranking now finds different unit-refuted assumptions directly from the targets:
**43 + [-20]**, **172 + [-140]**, **70 + [50]**, after **one/one/two probes**.
It ranks at most four unforced variables by binary incidence and probes false
then true. Original and unit-residual scoring select the same first conflict here,
although later orders differ; the latter pays another restriction pass. Discovery plus probe propagation visits
are 1,759/871/1,499; these are different operations from the old restriction count.

**Next:** price those local candidates and their absent restricted-child proofs,
then validate the fixed ranking/budget on excluded queries and adversarial edits.
Do not assume a valid forced literal is cost-beneficial: case 70 already refutes
that inference. Charge failed probes and reuse retained baseline/probe traces
where justified. A compact source-reference representation for chain sidecars
and shared cold checking remain supporting cost targets: full replay dominates
the complete samples, and sidecars currently offset native storage savings.

All **1,064 tests**, nine matched-arm audits, 2,957 ordinary and 438 composed
records plus six projections pass. Resume
`experiments/results/cnf-assumption-guard/checkpoint.json`: **21,528 keys**, all
21,525 prior payloads preserved, only three new keys and no alternative payload.
Prior **462 sources / 5,008 artifacts / 86 manifests**, four frontiers, structural
authorities and 64 manuscript proof blocks are unchanged. No new Lean, fresh
coverage, stable runtime or arbitrary-SAT bound.


New manifest: **49 artifacts**. Next preservation audit: **5057 artifacts / 87 manifests**.

## Previous investigation: minimize assumptions before adding partition branches

[Conditioned-core acquisition and direct-premise controls](conditioned-core.md)
separate branch choice from certificate reuse on cases 43/172/70. All six paired
orders have identical child roots, proofs and expansion counts. Separate cofactor
acquisition adds a row in 43 and payload in every pair. Direct reverse improves
43 from **10 -> 7 rows**, while forward minimizes bytes; 172 is an ordinary split
on `[40,50]`, and both case-70 orders regress. Trying all candidates costs **94
expansions versus 23 baseline**. Keep this prototype optional; lower expansion
counters alone do not establish less work or memory.

**Next priority:** replace these two-assumption partitions with a checked
single-assumption guard where possible. A read-only exact-prefix probe proves
unit conflicts for **43 + [-230]**, **172 + [-40]** and **70 + [-40]**, using
283/642/241 propagation literal visits. Each supports one forced variable rather
than two branches. All three remaining native child roots are absent; price
their acquisition and all composition before claiming savings. Reuse retained
unit traces and compare with both saved baselines and direct partitions, then
test bounded discovery on excluded inputs. In case 70, the small support is
just `[40,50]` and `[40,-50]`. In 43/172, recomputing after assumption deletion
finds conflicts that backward slicing of the original trace does not expose.

Broader recognition and selection remain open: a roughly 32,000-literal full-bank
conditioning scan is not cheap discovery, and posthoc best orders do not supply
a policy. Full cold replay dominates these complete samples. Native bytes,
retained sidecars and live memory must stay separate: the seven-row case-43
alternative actually has a slightly larger serialized delta-plus-decision.

All **1,057 tests**, fifteen matched-arm audits, 2,957 ordinary and 429 composed
records plus six projections pass. Resume
`experiments/results/cnf-conditioned-core-exposed/checkpoint.json`: **21,525 keys**,
all 21,482 prior payloads preserved. Six alternate certificates and the initial
two-CNF gate rejection remain retained. Prior **451 sources / 4,916 artifacts /
85 manifests**, four frontiers, structural authorities and 64 manuscript proof
blocks are preserved. No new Lean, fresh coverage, stable runtime or arbitrary-SAT bound.


New manifest: **92 artifacts** across complete and rejected runs. Next preservation audit: **5008 artifacts / 86 manifests**.

## Previous investigation: match conditioned cores after accepted guards

[Terminal-first screening](terminal-first-screen.md) fixes the previous regression.
On exact pre-query case 176, new rows fall **3 -> 1**, native payload **6,137 ->
2,229 bytes**, and propagation visits **5,289 -> 1,110**. It skips all 3,585 posting
visits, two core reads and four plans. Nonterminal cases 6/68/135 keep exactly the
same plans and proof payloads. Index setup remains paid; single samples establish
no stable total-time or peak-memory improvement. This is historical validation,
not new excluded-input coverage.

**Highest-priority gap:** cases **43 and 172** still require 19/26 expansions after
the extra guard. A read-only probe finds no further single-clause guard and no
eligible raw-core plan. Restricting checked negative cores under the same guard
assignments exposes **two-clause gaps in both cases**. Case 172's conditioned
core 209 is three clauses / four literals and already has a checked native root;
case 43's nearby restricted roots are absent (e.g. core 214: seven clauses /
fourteen literals). Price these projections at the saved prefixes, including
restricted-core certification and all model lifting. Use case 70 as a smaller
control. Compare against an ordinary clause split: tiny conditioned cores may
only encode that split, not a substantive reuse saving.

Conditioning the full ready bank costs roughly **32,000 restriction literal
visits per case** across two diagnostic passes. Cache by checked parent and exact
assignment; do not assume a bounded plan budget makes discovery cheap. The probe
publishes no result. This matching gap is more promising than repeating the
unchanged raw-core screen after another guard.

All **1,047 tests**, eight matched-arm audits, 2,957 ordinary and 414 composed
records pass. Resume `experiments/results/cnf-terminal-first-complete/checkpoint.json`:
**21,482 native keys**, no added native payload and eight retained control sidecars.
The prior compressed archive is referenced directly. All **443 prior sources /
4,843 artifacts / 84 manifests** pass preservation. Earlier structural authorities
and all 64 manuscript proof blocks remain unchanged. The incomplete harness run
and its six completed arms remain preserved. No new Lean or unrestricted-SAT bound.

New manifest: **73 artifacts** across complete and incomplete runs. Next preservation audit: **4916 artifacts / 85 manifests**.

## Previous investigation: avoid terminal repartitioning, then inspect guarded residuals

[Bounded plan screening with retained unit traces](partition-screen.md) now checks
up to four plans without solving them all. Historical cases 6 and 68 select the
previously best orders; case 135 rejects the nearest two-clause orders and finds
a three-clause alternative. New proof rows total **41 -> 23**, with **nine trace
publications** replacing expansion calls. All acquisition/checking remains paid.

**Fresh counterexample:** on 192 excluded queries, only case 176 reaches screening.
Its unsplit target already conflicts by unit propagation. The selected partition
reduces the expansion counter by one but adds two rows: totals **247 -> 249 rows**,
**495,506 -> 499,414 native bytes**, and **8,190 -> 12,369 combined propagation
literal visits**. This selector remains optional. The small complete-time mean
difference does not establish a total-runtime or live-memory improvement.

**First fix:** reuse the terminal unsplit trace before discovering partition
plans. **Largest remaining search target:** cases **43 and 172**, accounting for
**19/26 expansions**, followed by case 70 with four. All accept an extra guard,
so this policy never screens their residuals. Restore their exact fresh-trial
prefixes and price bounded further decomposition. An extra guard can expose
structure without finishing the query; do not infer cheap closure from it.

All **1,042 tests**, independent selection reconstruction, four fresh trials, six
complete historical controls and cold replay pass. The failed historical harness
assumption and its five completed arms remain recorded. Resume
`experiments/results/cnf-partition-screen/expanded-checkpoint.json`: **21,482 native
keys**, all 21,225 old payloads preserved; 192 new mixed decisions and six control
records are retained alongside all 2,957 ordinary and 208 prior composed records.
Seven control keys are additional to the fresh union. Earlier structural
coverage/authorities and 64 paper proof blocks remain unchanged. Prior **435
sources / 4,762 artifacts / 83 manifests** pass preservation. No new Lean or
unrestricted-SAT guarantee.

New manifest: **81 artifacts**. Next preservation audit: **4843 artifacts / 84 manifests**.

## Previous investigation: screen partition plans before full solving

[Exact first-false partitions](clause-partition.md) now compose several missing
clauses soundly: earlier clauses hold, the selected clause is false, every
negative branch is checked, and SAT witnesses lift through the original guards.
Native proof format is unchanged; composed reuse requires checked partition
sidecars. Eleven exact historical-prefix arms test all nearest ready cores from
the preceding diagnosis in forward/reverse order.

**Measured opportunity:** case **68** improves **27 -> 11 expansions**, **27 -> 12
rows**, and **32,827 -> 16,605 added native bytes** with core 258 in reverse order.
Case **6** improves **7 -> 3** in reverse order. But case **135** regresses **7 ->
8/10** in both orders, and case 6's forward order adds a row without reducing
expansions. Trying all eight candidate plans costs **105 expansions**, versus
41 for the three baselines. Best observed choices are not a cheap selector;
there is no fresh-query or stable total-runtime improvement claim.

**Next priority:** bounded propagation-based plan screening that retains checked
unit traces for reuse during publication, followed by fresh excluded inputs.
A read-only probe finds two terminal conflicts plus a 122-literal residual in
case 68's best plan; the competing two-conflict plan leaves 153 literals. Case
6's better order makes all three branches terminal. These signals are computed
without SAT search, but candidate discovery and screening must still be charged.
The current probe is diagnostic and uses the already selected historical plans.

Keep **135 as the rejection/fallback control**: its 117-literal residual is smaller
than the 158-literal baseline yet costs more to solve. Residual size, missing-clause
count and terminal count do not certify savings. Broader coverage, reusable plan
recognition and cross-plan sharing remain open. Full cold replay still costs
roughly five seconds per arm, far exceeding the 7–22 ms query-phase samples;
compact records and shared checking remain supporting cost targets.

Resume `experiments/results/cnf-clause-partition/checkpoint.json`: **21,225 native
keys**, all 21,128 previous payloads preserved, plus eight partition records for
three already known sources. All **1,035 tests**, eleven complete arm audits,
2,957 inherited ordinary decisions, 200 inherited chains and the new partitions
pass. Previous 429 sources and 4,706 artifacts / 82 manifests remain unchanged.
The paper builds to 204 pages with 64 unchanged proof blocks. No new Lean or
unrestricted-SAT resource theorem.


New manifest: **56 artifacts**. Next preservation audit: **4762 artifacts / 83 manifests**.

## Previous investigation: cover several missing clauses exactly

[Prepared premise-first guards](premise-guard.md) validate guard-chain savings on
**192 fresh queries**: expansions **139 -> 67**, new rows **436 -> 364**, and added
native payload **18.03% lower**. Seven cases improve with no per-query expansion
or publication regressions. Eight extra guards all use stored strengthened
premises. The prepared selector preserves the core-first native proofs while
reducing additional verified nodes **247 -> 102** and literal visits including
its index setup **208,132 -> 36,985**. A pending core can suggest a clause only
because the actual strengthened premise is independently checked negative.

**Highest-priority coverage target:** case **68**, costing **27/67 expansions**.
Its nearest overlapping ready cores miss three clauses. Cases **6 and 135** cost
seven expansions each and miss three/two clauses respectively. Price an exact
multiple-clause decomposition, retaining 135 as a smaller control. A negative
T AND C1 AND ... AND Ck forces at least one Ci false, not all of them. Use complete
alternative coverage or a partition by the first falsified clause; charge
premise construction, branch checking, recomposition and duplicated child work.
The read-only pre-query diagnosis is retained; no such inference is implemented.

**Total-cost limitation:** complete-time changes have mixed paired signs.
Premise-first averages 2.72% below ordinary but 6.03% above core-first; neither
establishes a stable speedup. Cold replay/compression consume about 61.9%/20.2%
of its mean. Larger chain records increase retained trial bytes **0.414%** versus
ordinary. Compact sidecar references and shared cold checking are supporting
cost opportunities; fewer expansions do not by themselves establish memory or
runtime savings. Broader SAT classes remain untested.

All **1,028 tests**, six complete trial audits, 2,957 inherited ordinary decisions,
eight inherited chains and 192 new chains pass. Frozen-worker first-query and
native-proof parity also passes. Resume
`experiments/results/cnf-premise-guard/checkpoint.json` (**21,128 native keys**,
all 20,666 prior payloads preserved). Prior 422 sources and 4,649 artifacts /
81 manifests remain unchanged; structural authorities and 64 proof blocks remain
unchanged. No unrestricted-SAT resource claim.


New manifest: **57 artifacts**. Next preservation audit: **4706 artifacts / 82 manifests**.

## Previous investigation: avoid duplicate checking in guard composition

[Checked guard chains](guard-chain.md) reduce expansions and new rows **68 -> 29**
on the eight exact historical prefixes. Added native payload falls **57.72%**;
serialized deltas plus chains fall **13.47%**. Cases 56 and 176 fall **41 -> 11**
expansions, and control 155 remains SAT. These are historical cases, not fresh
coverage. Selection and premise checking outweigh child-solve time saved in the
single samples; no total runtime or peak-memory improvement is established.

**Next priority:** check the stored strengthened premise before the separate
core proof, and reuse prepared core clause sets for near-containment. All six
selected premises already exist. A read-only check-cost probe reduces verified
nodes **148 -> 57**, literal payload **13,299 -> 8,073**, and read bytes
**122,683 -> 68,141**. This is not yet a deployed selector or discovery comparison.
Missing premises still need the checked-core/subset fallback. Compare the change
on fresh excluded inputs with setup, recognition, checking and cold replay charged.
More guards and smaller residuals do not guarantee lower total cost.

Cases 176/41/179 retain ten/eight/four expansions. Broader coverage and exact
recomposition remain priorities; this step supplies checked composition without
changing the native proof format. Composed source conclusions require the bound
sidecars and optional `GuardChainBank`; native root lookup alone is insufficient.

Resume `experiments/results/cnf-guard-chain/checkpoint.json` (**20,666 native keys**,
all prior payloads preserved, eight checked chain conclusions). All 16 arms,
2,957 inherited decisions and **1,022 solver tests** pass. Prior 416 sources and
4,579 artifacts / 80 manifests remain unchanged. No new unrestricted-SAT bound.


New manifest: **70 artifacts**. Next preservation audit: **4649 artifacts / 81 manifests**.

## Previous investigation: compose restrictions from nearly contained cores

[The terminal-filter comparison](terminal-guard.md) gives **no new fresh hit**:
both policies use 68 expansions and 309 new rows on 192 new neighbouring queries.
The optional selector passes historical admission/rejection controls, but none
of eight unresolved targets contains a pending support. Twenty initial pending
entries have terminal-conflict origins; their availability does not solve this
matching gap. The extra scan adds 3,064 candidate inspections and 95,624 clause
units. Timing variation establishes no total speedup; keep the policy optional.

**Highest-priority next test:** cases **56 (17 expansions)** and **176 (24)**,
accounting for 41/68 expansions. A checked core missing one clause from each
target justifies an additional restriction: target sizes fall **79/218 ->
67/172** and **86/240 -> 77/209** clauses/literals. Neither restricted target is
already reusable. Implement checked composition and price the remaining solve,
including recognition, premise publication and persistence. Case **155 is SAT**
and is an essential control against treating near-containment as UNSAT.

Six of eight unresolved cases admit such a restriction. Cases 41 and 179 remain
at least three and two clauses from an overlapping ready core. Almost all fresh
search is concentrated in template 12 (67/68 expansions). No measured hit uses
an unseen guard relative to all recorded origins of its support. Broader
discovery, proof composition and arbitrary-SAT bounds remain open.

Resume `experiments/results/cnf-terminal-guard/checkpoint.json` (**20,649 keys**).
All previous payloads and structural authorities are preserved; eight full
trial replays, 1,013 solver tests and two condition tests pass.


New manifest: **66 artifacts**. Next preservation audit: **4579 artifacts / 80 manifests**.

## Previous investigation: recognize terminal conflict supports

[Pricing all six pending alternatives](pending-guard-costs.md) separates a
promising case from costly derivations. Exact pre-query payload replay gives:

- **Case 85:** six fresh expansions / six rows become two derived rows, with
  payload **11,350 -> 1,805 bytes**. Its origin is a terminal unit conflict.
- **Case 23:** eleven fresh rows become 35 derived rows; payload rises 9.44%.
- **Case 103:** one fresh row becomes twelve under every candidate. Smaller
  causal supports still traverse the same seven origin nodes as legacy supports.

Every candidate avoids fresh SAT search; only case 85 reduces added rows and
payload. All six origin certificates have kind `units`, but only 85 contains a
conflict rather than a child reference. For one such checked terminal origin,
the existing causal extractor and target subset step publish **at most two rows**.
This bounds neither bytes nor checking/recognition time. Single diagnostic times
and cold prefix sessions establish no full-workload speedup.

**Next target:** test a terminal-origin admission filter on new excluded inputs,
charging recognition, checking, repeated selection, persistence and cold replay.
Keep 23 and 103 as controls against unrestricted pending-proof materialization.
Recursive derivation-graph pricing/sharing remains open; clause count alone is
insufficient. Complete cold replay remains a dominant overall cost.

Nine independently reconstructed arms, all 2,765 inherited decisions and 32
relevant tests pass. New deltas retain all certificates, including three
alternative occurrences for one target. Resume
`experiments/results/cnf-pending-guards/checkpoint.json`: **20,340 keys**, adding
70 and preserving all 20,270 old payloads. No fresh source-query coverage, new
Lean result or unrestricted-SAT bound. The initial validator's temporary-path
failure is retained; the corrected checker leaves measured sources unchanged.

All 403 prior sources and 4,467 artifacts in 78 manifests remain unchanged.

New manifest: **46 artifacts**. Next preservation audit: **4513 artifacts / 79 manifests**.

## Previous investigation: bounded guard choice and pending alternatives

[Alternative-guard selection](alternative-guard.md) tries one other matching
extension only after the first residual misses the archive and support bank.
It accepts checked cached targets or ready negative supports; selection itself
never solves or materializes a pending description. Ordinary guard checking,
subset publication, child checking and model lifting remain required.

**Verified fresh coverage:** one additional hit on current case **36** reduces
expansions **142 -> 135 (4.93%)**, splits **49 -> 47**, and new proof rows
**362 -> 356 (1.66%)**. Materialization stays at 49 rows. No query regresses in
expansion count. The selector runs on 15 first-visit misses and once on a repeat;
repeated queries add no rows but may repeat guard choice.

**No established total-cost win:** mean complete time rises **13.60267 ->
13.77944 seconds (1.30%)**. Paired changes are -28.44%, +36.27%, -28.34%, +48.04%,
tracking order in these four pairs; cause is untraced. Peak RSS averages 4.85%
higher with mixed signs. Query time is 24.59% lower on average, but neither a
stable total speedup nor a memory improvement follows. Guard-selection traces
increase gzip plus first-trial sidecars **2.23%**. Full cold audit and compression
consume **52.62% / 27.04%** of candidate time.

**Next coverage target:** price checked materialization for pending alternative
supports on current **case 23 (11 expansions)** and **85 (six)**. Keep case
**103 (one expansion)** as a low-cost fallback control. These three cases account
for six skipped pending matches. Do not enable unrestricted derivation: a small
support may cost more to obtain than its target costs to solve. Preserve partial
checked derivations if testing a budget, and charge recognition, derivation,
publication and changed later sharing. Controlled probes require the original
pre-query state; fresh generalization must exclude these now-retained cases.

All **135 remaining expansions are negative**. Largest current cases are
**2 (18), 120 (17), 66/67/180 (14 each), 7 (13), 23/155 (11 each)**. Templates
6/8/12 contribute 55/34/46. These stream-local IDs differ from earlier catalogs.

**Controls:** replay of the frozen prior worker gives the same semantic queries
and a byte-identical database as the new first-guard baseline. Historical case
121, restored from its original 19,543-key snapshot, selects the diagnosed ready
alternative with zero fresh SAT expansions and one new subset proof. Its earlier
20-node count was measured in the historical stream, not an isolated matched
runtime control. The regression proof archive is separately preserved.

**Guard provenance:** case 101 differs from its core's first recorded guard,
in both policies, but another origin already uses that guard. No hit uses a
removed-clause assignment absent from all recorded origins of its selected core.
Do not interpret a first-origin mismatch as demonstrated unseen-guard transfer.

Both policies use the same 19,907-key union and old 389-origin portfolio,
excluding 2,304 prior sidecar answers and cached roots, then visiting 192 new
neighbours twice in four alternating pairs. No support discovery occurs; the
larger optional causal index remains preserved and unloaded. Broader structural
coverage, optimal expansion and arbitrary-SAT polynomial bounds remain open.

Independent validation passes **518 tests**, eight complete fresh-trial
archive checks / **3,072 query replays**, every union node, **2,573 inherited
decisions** and all 192 new decisions. Archive validation disables fresh search
and reconstructs guard selection and proof choice from pre-query append history.
Separate untimed frozen-worker replay recomputes the baseline, matching semantic
queries and proof bytes. The historical regression adds one proof row without
fresh SAT search and passes full cold proof/query and both-lineage checks.

The fresh-query union retains **20,270 keys / 63,492,096 SQLite / 4,704,611 gzip
bytes**, adding 363 keys and preserving every prior payload. There are no
alternate certificates. New decisions have **144 direct roots / 48 negative
guards**. The historical regression's additional target proof is not in this
union; its complete archive and guarded result remain separately retained in
`experiments/results/cnf-alternative-guard/historical-control/` and bound by
`control-check.json`. It is not counted as a fresh-query coverage gain.

Resume `experiments/results/cnf-alternative-guard/checkpoint.json`. It preserves
all prior semantic fields and adds `alternative_guard_study` and
`alternative_guard_decisions`. The measured banks retain the same eight-catalog /
389-origin history, with **132/75 legacy** and **67/109 causal** ready/pending
entries. The original 170-entry frontier has **126/44**; the optional 203-entry
expanded causal frontier has **67/136**, retaining its eleven-catalog / 526-origin
lineage. All four lineage checks pass. The two newest catalogs contain 98
negative guarded records not acquired into that larger optional frontier.

All prior **397 sources / 4,406 artifacts / 77 manifests** remain unchanged.
Runtime binds 401 sources; analyzer and control checker bring the ledger to 403.
Structural authority stays **2,614 patterns / 259 pairs / 17 missing children**,
original **17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The paper builds cleanly to **202 pages** with
**64 unchanged proof blocks**. No new Lean or unrestricted-SAT resource theorem.
The full test log retains 24 unclosed-SQLite ResourceWarnings from older tests;
eight focused new tests emit none with warnings enabled. Allocation origins
remain untraced.

Checkpoint SHA-256: `ff7c124f610f1a7e11207b6f248d8f420d7bd0272ff91df0c9c9d75d4e8b729d`.
Report SHA-256: `4f15e41ec39a67b7df6172cb64eba7b9c863c492655fdc1b44d9ee674d766909`.


The new manifest binds **61 artifacts**. The next preservation audit inherits
**4467 artifacts / 78 manifests**.

## Previous investigation: acquisition saturation and alternative guards

[Incremental causal acquisition](incremental-causal.md) now preserves the old
history while extracting only new guarded-negative source records. Independent
reconstruction yields the same frontier with **1,181 versus 3,708 support-node
visits (68.15% fewer)**. Dependencies can still be old; full provenance and
ordinary proof checks remain mandatory. This count is not a total-runtime bound.

**Fresh-query result: no coverage gain.** The 137 source records add 28 raw /
27 retained supports, growing the causal frontier **176 -> 203**, but none of
the new entries is selected on the next 192 queries. Both policies transfer
**37 cofactors**, expand **126 nodes** and add **364 rows**. All eight trial proof
databases are byte-identical. New supports remain available as learned state;
do not enable acquisition for every batch merely because the index grows.

**Total cost:** mean complete time rises **12.70798 -> 13.32969 seconds (4.89%)**,
with regressions in three of four pairs. Query time improves 29.01% because
acquisition checks 3,572 proof nodes before queries, reducing query verifications
3,333 -> 1,895; it does not reduce search. Preparation rises 0.11359 -> 1.39511
seconds. The new index costs **2,183,937 bytes**; gzip plus first-trial sidecars
grows **19.04%**. RSS has mixed paired signs and no demonstrated improvement.
Full cold replay and compression consume 38.17% / 29.71% of extended runtime.

**Next best target: guard selection before fresh solving.** In a separate
read-only probe against the initial archive, all twelve unresolved queries have
two valid deletion guards. For **case 121**, the alternative target contains an
old, already checked causal support; the chosen target costs **20 expansions**.
Test a bounded alternative-guard check after the first target misses the archive
and support bank. Charge recognition, checking and publication, and account for
changes in later sharing. The 20-node opportunity is local, not a demonstrated
batch or runtime saving. The diagnostic publishes no new target proof.

Case 121 is now retained. Reproduce its opportunity from the pre-query
19,543-key snapshot and test generalization on fresh queries from the new union;
re-solving the cached case cannot validate the new policy.

Other large negative cases are **182 (26), 51 (19), 10/81 (15 each)**. Remaining
expansions are **120 negative / six positive** (SAT case 67); templates 6/8/12
contribute 34/56/36. Raw clause proximity is only a discovery hint. The recorded
near-supports keep exact missing clauses, and require nonempty overlap to avoid
the empty-clause refutation's vacuous distance-one result. Missing clauses cannot
be silently supplied. These are current-stream IDs, not original structural cases.

Both modes start from 19,543 keys, excluding 2,112 prior sidecar answers and
cached roots, and visit 192 new neighbours twice in four alternating process
pairs. The old legacy and causal banks have eight catalogs / 389 origins; the
extended causal index has eleven / 526. No old retained entry is retired in
this batch. All observed measured hits still share their first origin's guard.
Broader discovery, economical acquisition and unrestricted polynomial bounds
remain open.

Independent validation passes **510 tests**, eight complete archive checks /
**3,072 trial query replays**, every union node, **2,381 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. Incremental and
complete acquisition have identical frontier structure. Every portfolio choice
is reconstructed from the append history available before its query. All eight
trial proof databases are byte-identical; there are no alternate certificates.
The union retains **19,907 keys / 62,033,920 SQLite / 4,632,742 gzip bytes**,
adding 364 keys while preserving all prior payloads. New decisions comprise
**141 direct roots / 51 guards**, including one positive guarded result.

Resume `experiments/results/cnf-incremental-causal/checkpoint.json`. It preserves
all previous semantic fields and adds `incremental_causal_study`,
`incremental_causal_decisions`, `incremental_causal_proposals` and
`incremental_causal_portfolio`. Keep the enlarged bank optional. Its 203 retained
entries have **62 ready roots / 141 pending**, with eleven-catalog / 526-origin
lineage. The old causal bank has **62/114**, legacy **131/76**, and original
170-entry bank **125/45** (ready/pending). All four lineage checks pass.
The newest catalog adds 50 guarded-negative records that have not been acquired
into the expanded index; broad automatic reacquisition has no demonstrated
benefit on this workload.

All prior **391 sources / 4,345 artifacts / 76 manifests** remain unchanged.
Runtime binds 395 sources; the analyzer and guard probe bring the ledger to
397. Structural authority stays **2,614 patterns / 259 pairs / 17 missing
children**, original **17/24 / 999 steps**, separate supplemental **24/24 / 208**,
and original case 7's discovery pointer. The manuscript builds cleanly to
**201 pages** with **64 unchanged proof blocks**. No new Lean or unrestricted-SAT
resource bound. The full test log retains 24 unclosed-SQLite ResourceWarnings
from older tests; eight focused new tests emit none with warnings enabled.
Their allocation origins remain untraced.

Checkpoint SHA-256: `f3941f25743a6ce157e446a4d5aec53a0750ce4bfa1dcaf26970833d477a5e0b`.
Report SHA-256: `f58224656b5addf7c9ae648a7c94f0d827cfc05838e96d295e35493038b5141b`.


The new manifest binds **61 artifacts**. The next preservation audit inherits
**4406 artifacts / 77 manifests**.

## Previous investigation: proof selection and the remaining negative cases

[Checked proof selection](proof-choice.md) combines the acquired legacy and
causal frontiers. It tries an available negative proof first, then falls back to
the first legacy or causal derivation. All source guards, ordinary proof checks
and both complete lineage audits remain required. This is a measured heuristic,
not a minimum-cost guarantee.

**Resolved derivation gap:** the combined policy retains all **30 causal hits**
and **35 expansions**, while materialization falls **137 -> 57 rows (58.39%)**
and total new rows **351 -> 271 (22.79%)**. It uses 25 ready proofs and five
materializations. On 26 overlapping targets, legacy/causal/combined derivation
costs **85/121/41 rows**. This is a fresh stream; the older 41-row opportunity was
not used as an assumed result.

**Runtime and memory tradeoff:** mean complete time is **11.08200 seconds**, versus
12.42048 for causal and 13.45278 for legacy. These mean improvements (10.78% /
17.62%) each include one regression among three pairs. Peak RSS rises **5.53% /
16.55%**, with positive paired differences. The allocation cause remains untraced.
Keep the combined option available for reducing proof growth; do not claim a
stable runtime or memory win. Gzip plus first-trial raw sidecars falls to
11,727,695 bytes, but all earlier history and trial archives remain additional.

**Highest-value coverage target:** acquire causal supports incrementally from
preserved new negative outcomes, then examine the seven uncovered residuals.
All **35 remaining expansions are UNSAT**: current cases **46/48** cost seven,
**27** six, **7/101/156** four, and **86** three. Templates 6/8/12 account for
17/11/7. All measured transfers still share their first origin's guard. Changes
of guard and shared conditional structure remain the informative coverage tests.
Do not rebuild the same old frontier again; charge new acquisition explicitly.

**Dominant complete costs:** cold replay and compression consume **43.69% /
31.96%** of combined time. Checking both lineages costs 0.53090 seconds and is
only part of full cold replay. Retain complete checking until a measured equally
strong replacement exists. The next discovery experiment must charge these
costs as well as live-memory growth, not only fresh search nodes.

The experiment uses the same 19,091-key union, excluding 1,920 previous sidecar
answers and cached roots. It visits 192 new neighbours twice in three balanced
process triples. Both frontiers retain the same eight-catalog / 389-origin
history; no new supports were discovered. The combined 778 origin references
are links into those two histories, not 778 distinct sources. The two newer
catalogs' 94 negative guarded outcomes remain preserved but unincorporated.

Independent validation passes **502 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **2,189 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. Every combined
selection is reconstructed from the archive's append history before that query.
The union retains **19,543 keys / 60,649,472 SQLite / 4,567,169 gzip bytes**,
adding 452 keys while preserving every earlier payload. All **38 alternate
certificate occurrences** remain in trial archives. New decisions have
**149 direct roots / 43 negative guards**.

Resume `experiments/results/cnf-proof-choice/checkpoint.json`. It preserves
all prior semantic fields and adds `proof_choice_study`, `proof_choice_decisions`
and `proof_choice_portfolio`. The composite references the original immutable
legacy and causal banks. Their union readiness is **129/78** and **60/116**
(ready/pending); the original 170-entry frontier has **125/45**. All three
complete lineage checks pass. The fixed measured banks still use eight catalogs;
**137 guarded-negative origin records** from the three subsequent catalogs now
remain available for incremental acquisition. These are source records, not a
claim of 137 distinct residual structures.

All prior **386 sources / 4,286 artifacts / 75 manifests** remain unchanged.
Runtime binds 390 sources; the analyzer brings the ledger to 391. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds cleanly to **201 pages** with
**64 unchanged proof blocks**. No new Lean or unrestricted-SAT resource bound.
The full suite retains 24 unclosed-SQLite ResourceWarnings during older tests;
10 focused new tests emit none with warnings enabled. Their allocation origins
remain untraced.

Checkpoint SHA-256: `dc35b10ea9a53856e6d1b906aac4d629cf247bdc60c888f1ea01f56b8fc714fa`.
Report SHA-256: `4dfdbc24d4b76325aaf98ce14231849ee1f18ad6a84a66dc50d190ef15d2b228`.


The new manifest binds **59 artifacts**. The next preservation audit inherits
**4345 artifacts / 76 manifests**.

## Previous investigation: retained causal frontiers and proof choice

[Retained causal loading](retained-causal.md) avoids rediscovering the acquired
frontier while preserving its pending entries, matching materializer, actual
proof checks and complete cold query/provenance audit. It does not persist a
validity flag. Source-file fingerprint and policy markers identify the saved
hints; only ordinary checked negative proofs justify a transfer.

**Resolved cost gap:** support discovery visits **2,851 -> 0 nodes**, preparation
falls **2.29443 -> 0.08099 seconds**, and complete time falls **12.74826 ->
10.63701 seconds (16.56%)** against rebuilding, improving in all three pairs.
Rebuilt and retained modes have identical frontier files and byte-identical
proof databases. Query time rises 46.39% because discovery had warmed checks
before queries, but complete time improves. Historical acquisition remains charged.

**Fresh coverage:** against loading the 207-entry legacy frontier, the retained
176-entry causal frontier transfers **25 instead of 19** targets, cutting
expansions **120 -> 93 (22.5%)** and splits **37 -> 30**. Six extra hits account
for all 27 saved expansions; no query regresses. Every hit still shares its first
origin's guard, so broad cross-guard reuse remains open. Complete time is only
**0.67% higher than legacy** (10.56570 seconds), with mixed paired signs: there
is no demonstrated net speedup over that baseline.

**Highest-value expansion-cost target: choose among available proofs.** On the
19 targets both banks cover, retained causal reuse creates **74 materialization
rows versus 33** for legacy. The six additional causal targets need another 26
materialization rows and six publications. Test using an already cheaper proof
on overlapping matches and causal supports for added coverage. The apparent
41-row opportunity is attribution, not a guaranteed dispatcher saving: earlier
choices can affect sharing and later cache contents. Keep all checks and measure
matched novel queries. Do not routinely rebuild the fixed causal frontier again.

**Memory/total-cost limits:** retained causal reuse adds **365 versus 319 rows**
and raises mean peak RSS **14.56% versus legacy** and **11.24% versus rebuild**,
with positive paired differences. Allocation cause is not established. Gzip plus
first-trial raw sidecars falls 12,657,545 -> 12,173,774 bytes versus legacy, but
historical trials and the final union remain additional retained state. Complete
cold audit and compression account for **41.29% / 33.65%** of retained runtime.
Do not infer that either verification or old acquisition can be omitted.

**Coverage targets:** remaining work is **74 negative / 19 positive expansions**.
Current negative cases **14 / 161** cost 19 / 15; SAT cases **45 / 91** cost 14 /
five. Templates 12/6/8 account for 54/33/6. Compare their conditional structures
and genuinely different guards; these are current-catalog IDs. Incremental
causal discovery from new origins is still separate and unimplemented here.

All modes start from 18,672 acquired keys, exclude all 1,728 prior sidecar answers
and cached roots, and visit 192 new neighbours twice in three balanced process
triples. Both banks use the same 389 origins from eight ordered catalogs; none
adds the latest 51 negative origins. Loading preserves all history and pending
entries. Positive witness exploration remains preserved but disabled.


Independent validation passes **492 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,997 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. The union retains
**19,091 keys / 59,228,160 SQLite / 4,491,457 gzip bytes**, adding 419 keys while
preserving every earlier payload. All **48 alternate certificate occurrences**
remain in trial archives. New decisions have **147 direct roots / 45 guards**,
including two positive guarded results.

Resume `experiments/results/cnf-retained-causal/checkpoint.json`. It preserves
all inherited semantic fields, adding `retained_causal_study` and
`retained_causal_decisions`; the saved frontiers themselves are unchanged. Load
`causal_support_proposals` with the fingerprinted causal loader and matching
materializer. In the union, the causal frontier has **48 ready roots / 128 pending**;
the extended legacy frontier has **121 / 86**, and the original 170-entry frontier
has **120 / 50**. Both measured banks keep the same eight-catalog, 389-origin
lineage. The ninth catalog is excluded from selection but not added to discovery.
The original frontier retains its six-catalog lineage. All three union audits pass.

All prior **381 sources / 4,230 artifacts / 74 manifests** remain unchanged.
Runtime binds 385 sources; the analyzer brings the ledger to 386. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds to **200 pages** without warnings,
with **64 unchanged proof blocks**. No new Lean result or unrestricted-SAT bound.
The full test log retains 24 unclosed-SQLite ResourceWarnings during older tests;
the six focused new tests emit none with warnings enabled. Their allocation
origins remain untraced; this is not a failed proof check.

Checkpoint SHA-256: `34e1408f8937fab8a5e9ace56122ab95b6e49a15f1ec21b85a02270098081a2c`.
Report SHA-256: `ea39bfb8165519399ac7117dc82156f90b59b5c16d0cd6c735ababb05e90c3ea`.


The new manifest binds **56 artifacts**. The next preservation audit inherits
**4286 artifacts / 75 manifests**.

## Previous investigation: causal unit slicing and acquisition overhead

[Causal support extraction](causal-support.md) removes propagated assignments
that the contradiction does not use. The dependency-closed subsequence still
forces every retained unit and gives the same required child clauses or conflict.
Derived certificates use the unchanged ordinary checker. Pending descriptions
are materialized only on a match; complete source-query guards and cold lineage
checks remain required. This is proof-relative support reduction, not minimum cores.

**Coverage gain:** on 192 new queries, causal supports give **38 rather than 29
cofactor transfers**, cutting expansions **195 -> 100 (48.72%)** and splits
**65 -> 33**. Nine new target hits account for all savings; no query regresses in
expansions. Merely extending the old extraction with the same new sources gives
no extra hits. Causal slicing removes **5,585 / 14,613 unit steps**, and retained
clause occurrences fall **7,385 -> 4,568** against extension. All observed causal
hits still share their first origin's guard; cross-guard coverage remains open.

**Cost gap:** complete time grows **10.89172 -> 12.61998 seconds (15.87%)** versus
active loading, and **8.50%** versus old-rule extension. Every matched triple has
both regressions. Query time improves **27.04%** versus active, but causal
preparation re-extracts all 389 origins and costs **2.33282 versus 0.08516 seconds**.
Its 31 materializations add 275 proof rows instead of 59; total new rows rise
423 -> 553. Mean peak RSS rises 2.36%. Gzip plus first-trial raw sidecars falls
only 12,164,674 -> 12,152,030 bytes (0.10%); no asymptotic space claim follows.

**Highest-value cost target:** load the acquired causal frontier without rebuilding
old supports, then measure incremental acquisition on genuinely novel queries.
Retain the causal materializer and complete lineage checks. Repeated queries
already benefit from exact caching, so they cannot establish discovery amortization.
Further derivation sharing may reduce the 275 materialization rows, but the
observed preparation cost is the first bottleneck. Keep the old frontier available.

**Next coverage targets:** 95 remaining expansions are negative and five belong
to SAT case 42. Largest negatives are current cases **187 (20), 159 (17), 50/60
(16 each)**. Templates 12/6/8 contribute 42/38/20 expansions. Compare their proof
dependencies and boundary assignments, then test genuinely different guards.
Do not infer that identical guards are required simply because every measured
hit shares its first origin's guard. Current catalog IDs differ from original
structural cases and from the previous stream's IDs.

All workers start from the 17,947-key union, exclude all 1,536 prior sidecar
answers and cached full roots, and use three balanced process triples with two
visits. Modes compare the saved 170-entry frontier, extension to 207 entries from
103 newly acquired negative origins, and causal re-extraction to 176 entries from
all 389 origins. All query, construction, persistence and complete cold audit
costs remain charged. The historical probe shrinks cases 123/189 to 26/34 clauses
but does not merge them; cases 157/175 acquire new mutual support containment.
Positive exploration remains preserved but disabled after its failed fresh test.


Independent validation passes **486 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,805 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. The union retains
**18,672 keys / 57,823,232 SQLite / 4,419,183 gzip bytes**, adding 725 keys while
keeping every earlier payload. All **41 alternate certificate occurrences** remain
in trial archives. New decisions comprise **140 direct roots / 52 guards**,
including one positive guarded result.

Resume `experiments/results/cnf-causal-support/checkpoint.json`. Preserve
`causal_support_study`, `causal_support_decisions`, `causal_support_proposals`
and `extended_support_proposals`, along with every inherited field. The causal
frontier has **34 ready roots / 142 pending**; the extended frontier has
**118 / 89**, and the original 170-entry frontier has **119 / 51** in the union.
All three lineage audits pass. Causal pending entries require the causal
materializer; the old materializer is not interchangeable. Both new banks use
eight source catalogs in protocol order; the original bank still uses six.

All prior **375 sources / 4,174 artifacts / 73 manifests** remain unchanged.
Runtime binds 380 sources; the analyzer brings the ledger to 381. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds to **199 pages** without
warnings, preserving all **64 proof blocks**. No new Lean result is claimed.

Checkpoint SHA-256: `47af7ad8959666bab1107e17b63bd37a3ff71c5d28d29758fb49e435de65cb43`.
Report SHA-256: `260a06be421b7adfd802e50ba7cf948b96abcdf1e1bd4901dda8677313b33a71`.


The new manifest binds **56 artifacts**, including the read-only historical
probe. The next preservation audit inherits **4230 artifacts / 74 manifests**.

## Previous investigation: witness signatures and a failed fresh-stream transfer

[Bounded witness exploration](witness-signatures.md) establishes an exact reuse
pattern for deletion queries: the set of clauses falsified by a stored assignment
fully describes its lookup coverage. Equal signatures do not preserve useful
flip transitions, however. A two-variable counterexample shows why exploration
must retain distinct assignments even when lookup can use one representative.

**Historical discovery:** excluding the previous active-support answers from
seeds, 1,024 flips per template reaches its hard SAT case 137; 4,096 also reaches
case 2. No single flip repairs any of the six diagnostic targets. The successful
cap uses 12,288 attempts, 3,276 assignments and 947 signatures across three
shared-coordinate templates. Failed smaller budgets and all transcripts persist.

**Fresh comparison:** the next 192 queries give **zero additional transfers**.
All 96 SAT cases already use the old witness route; all **214 expansions / 68
splits** belong to 25 UNSAT cases. Existing active loading, added signatures and
added exploration produce identical proof databases with 415 new rows. Mean
complete time is **10.68687 / 10.73314 / 11.33255 seconds**. Exploration regresses
**6.04%**, in every matched triple. Keep it optional. Mean RSS rises 9.02%, with
mixed paired signs; gzip plus raw sidecars grows 12,158,436 -> 15,671,480 bytes.
The current-seed bank grows 82 -> 3,282 assignments but compresses lookup to
945 signatures. This is no measured expansion or persistent-space improvement.

**Next coverage priority:** shared negative cofactors. Current template 6 costs
**94 expansions**, template 8 costs 69 and template 12 costs 51; the previous
concentration on template 12 no longer describes this stream. Start with current
cases **123 and 189** (17 and 16 expansions), both template 6 under guard
[130,140]. Identify shared residual proof/support structure, then test genuinely
different guards and templates. Cases 74 and 106 cost 15 each; 42, 157 and 175
cost 14 each. Keep these current IDs separate from original structural cases.

**Cost priority:** complete cold audit and compression consume **40.45% / 33.11%**
of active-control runtime. Avoid repeated preparation and duplicated persistent
state, while preserving complete checking. Do not spend another run blindly
growing the positive bank: on this stream its misses are all negative. New
positive exploration needs evidence of uncovered SAT targets or another useful
category before further acquisition. The negative frontier stays at the acquired
170 entries and should be loaded rather than rebuilt.

The comparison starts with 17,532 keys, excludes all 1,344 prior sidecar answers
and cached full roots, and uses three balanced fresh-process triples with two
visits. All model checks, fixed-budget discovery, serialization, cold state
reconstruction, negative-lineage audit and compression are charged. Tautological
clauses are outside this index interface; a miss falls back. The fixed seed batch
is sealed before exploration, and its persisted budget never resets on reuse.
A quadratic number of possible two-false-clause signatures does not give cheap
representative construction: one deletion from G and z and -z already encodes
arbitrary SAT. No uniform-polynomial or minimal-expansion result follows.


The independent audit passes: all **473 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,613 inherited decisions** and
all 192 new decisions. Fresh validation search is disabled. The union preserves
**17,947 keys / 55,951,360 SQLite / 4,291,520 gzip bytes**, adding 415 keys while
keeping every old payload. There are no alternate certificate occurrences; new
decisions have 133 direct roots and 59 guarded negative children. The old negative
index remains unchanged, including pending proposals requiring checked materialization.

Resume `experiments/results/cnf-witness-signatures/checkpoint.json`. It preserves
inherited fields and adds `witness_signatures_study`, `witness_signatures_decisions`
and the optional, sealed `witness_signatures_index`. All prior **369 sources /
4,097 artifacts / 72 manifests** remain unchanged. Runtime binds 374 sources;
the analyzer brings the ledger to 375. Structural authority remains **2,614 patterns /
259 pairs / 17 missing children**, original **17/24 / 999 steps**, separate
supplemental **24/24 / 208**, and original case 7's discovery pointer. No new Lean claim.
The manuscript builds to **198 pages** without warnings; its **64 proof blocks**
are unchanged.

Checkpoint SHA-256: `e70222825ae73661087f5ea61665fcfc08ee7008acda710fc0ec674c89b59b52`.
Report SHA-256: `5ddf4d0377262e60a4175001a92c0455b01170ebce944bacc1194ad51f003837`.


The preserved negative frontier now has **113 available retained roots / 57 pending**;
pending descriptions still require checked materialization. The new manifest binds
**77 artifacts**, including the historical probe. The next preservation audit
inherits **4174 artifacts / 73 manifests**.

## Previous investigation: active support checks with full cold lineage

[Active support checking](active-support.md) avoids checking unrelated old
lineage before queries while retaining complete cold proof, query and provenance
audit. Mean complete time falls **11.52069 -> 10.36579 seconds (10.02%)** versus
eager checking, and **6.85%** versus the loaded-index control. Every matched
triple improves. Both extension modes retain identical proof archives and search
work; no logical check is replaced by an unchecked persisted trust flag.

**Why it is sound:** a match checks the actual core's canonical identity and
ordinary negative proof before subset publication. Missing roots require checked
materialization. The current query's guard remains checked online. The cold
auditor runs the unchanged full proof/query audit, then checks all index origins
and dominance on the same pinned snapshot before closing it, including on
failure. Historical lineage is deferred, not removed. All modes pay for the
complete audit; this timing boundary is broader than earlier benchmarks.

**Measured work:** active preparation normalizes **517,355** literal occurrences
rather than **1,904,438**, and makes **1,563** database lookups rather than **6,625**.
Preparation falls **1.78958 -> 0.51719 seconds**. Query time rises **27.91%** as
checks move to active use, but complete time improves. Mean peak RSS is **7.89%**
below eager and **5.06%** below loaded; paired eager differences change sign.
There is no asymptotic memory improvement or persistent-space saving. Gzip plus
raw sidecars rises **11,657,158 -> 11,894,676 bytes** against loaded.

**Negative discovery result:** 42 new negative sources expand the frontier
**151 -> 170 entries**, but all modes still make **25 transfers / 187 expansions /
64 splits**. There are **no additional target hits**. Index growth is not a
coverage measure. The active method has not been compared with active loading
without extension, so this run does not establish that growing the bank pays.
Reuse the acquired 170-entry index rather than rebuilding it for a later claim.

**Next coverage target:** template 12 accounts for **169/187** remaining
expansions, template 8 for 18 and template 6 for none. Fifteen negative queries
need 145 expansions; guarded SAT cases **137 and 2** need **26 and 16**. Largest
negatives are 29 (23), 140 (18), 116 (17) and 149 (15). These are new-catalog IDs.
Inspect shared conditional structure and retained SAT-witness repair/transfer
on these residuals, including genuinely different guards. Every measured support
hit still shares its first origin's guard clause. Broader cross-category coverage
remains open. For cost work, compare active loading before further acquisition;
complete cold audit and compression now cost **40.03% / 31.81%** of active time.

All modes return **97 SAT / 95 UNSAT**, with 95 witness publications, 51 old
full-query core hits and 46 guards (44 negative, two positive). Four targets are
cached. Extension uses 22 supports for 25 transfers and materializes four roots
through 13 proof rows. Its frontier has 106 ready roots and 64 pending proposals.
The comparison uses the latest **17,161-key** union, excludes all **1,152** prior
sidecar answers and complete cached roots, and visits 192 new constructed
neighbours twice in three balanced process triples. This is not an arbitrary-SAT
benchmark, minimum-expansion result or uniform-polynomial guarantee.

Resume `experiments/results/cnf-active-support/checkpoint.json`. Preserve all
inherited fields plus `active_support_study`, `active_support_decisions` and
`active_support_proposals`. Load this complete 170-entry index, including pending
entries and its raw-support/origin history. Its six source catalogs stay in their
existing order; a subsequent extension must supply only a genuinely new batch.
The union contains **17,532 keys / 54,337,536 SQLite / 4,206,056 gzip bytes**,
adding 371 keys while retaining every old payload. Two alternate certificate
occurrences remain in trial archives. New decisions comprise **146 direct roots /
46 guards**, including the two SAT cases. The union also has 106 available retained
roots and 64 pending ones; pending entries cannot justify UNSAT before verification.

All **461 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,421 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **364 sources / 4,042 artifacts /
71 manifests** remain unchanged. Runtime binds 368 sources; the analyzer brings
the ledger to 369. Structural authority stays 2,614 patterns / 259 pairs / 17
missing children, original 17/24 / 999 steps, separate supplemental 24/24 / 208,
and original case 7's discovery pointer. No new Lean claim.
Checkpoint SHA-256: `ddab750444c8546722ca5d15acee2abbda32455e9dd2dcc785715ebdcfaa62b1`.
Report SHA-256: `9b616b087f471249cebe07ea6c29a864980c46d3736425e613b6cfa1de556b70`.
The manuscript builds to 197 pages without warnings; all 64 proof blocks are unchanged.
The new manifest binds 55 artifacts; next audit inherits **4,097 artifacts / 72 manifests**.

## Previous investigation: incremental discovery and old evidence costs

[Incremental support discovery](incremental-support.md) reuses the saved index
and extracts supports only from newly acquired negative results. Adding **99**
new sources to **145** old ones gives exactly the same frontier as full
rediscovery: **168 raw supports / 151 retained entries**, up from 112 / 104.
Three superseded old entries remain in history. Pending proposals survive
restart and further extension; they cannot justify UNSAT before materialization
and ordinary proof checking.

**Coverage gain:** on another 192 unseen constructed neighbours, the expanded
index transfers **18 rather than 14** targets and reduces expansions
**199 -> 162 (18.59%)**. Cases 53, 121, 163 and 190 account for all 37 saved
expansions. Three materializations add 39 proof rows. All modes return
**105 SAT / 87 UNSAT**, including one guarded SAT result. Every measured transfer
still shares its first origin's guard clause; broad cross-category discovery
remains open. Both extension modes have identical logical/physical archives.

**Cost result:** incremental extraction visits **715 rather than 1,697** proof
nodes (57.87% fewer), but preparation only falls **1.82786 -> 1.78856 seconds**.
Complete time is **11.69363 -> 11.64076 seconds**, a near-flat **0.45%** difference,
with no demonstrated practical speedup or memory improvement. Against loading
the ready bank (**11.17962 seconds**), extension still regresses **4.12%**, in
every matched triple. Gzip plus raw sidecars grows **11,064,817 -> 11,617,440 bytes**.
Keep extension optional. This is a current-union comparison, not another
historical construction replay: all workers begin with **16,760 keys**, and
selection excludes all **960** prior sidecar answers and cached complete roots.

**Next highest-value gap: repeated checking of saved evidence.** The diagnostic
records **7,216 proof reads / 14,281 canonicalizations** for incremental discovery,
versus **6,783 / 13,518** for rebuilding. Old provenance and ready-core checking
offset avoided extraction. Separate active match requirements from full lineage
audit, retaining both: a checked negative core justifies subset reuse independently
of its discovery guard, while a pending proposal needs checked materialization.
Test demand-driven checks or reuse within an owned append-only session, retaining
invalidation and a separately charged complete cold audit. Do not persist unchecked
trust flags. The diagnostic overlapped the correctness suite; use its call counts
and structure, not its elapsed times. Timed workers ran alone.

**Remaining coverage probes:** 18 negative cases need 154 expansions; guarded
SAT case 188 needs eight. Template 8 contributes 66 expansions, template 6 adds
51 and template 12 adds 45. Largest new-catalog negatives are 61 (19), 72 and
142 (18 each), and 19 (14). Keep these distinct from original structural case IDs.
Cold audit and compression remain 34.93% and 29.74% of complete incremental time.
The 151-entry trial frontier has 104 available roots and 47 pending proposals;
these 104 available roots are a different set from the original 104 ready cores.

Resume `experiments/results/cnf-incremental-support/checkpoint.json`. Preserve
all inherited fields plus `incremental_support_study`, `incremental_support_decisions`
and `incremental_support_proposals`. The latter stores the complete extended
index (including all raw supports, origins and dominance), not just ready cores.
For the next extension, supply the five old decision catalogs in their existing
order and only genuinely new batches. Repeated batch identities reject. Use the
extended index to preserve acquired discovery rather than returning to the old
104-entry frontier. Match-time proof checks still apply to every pending root.

The union retains **17,161 keys / 52,809,728 SQLite / 4,124,643 gzip bytes**, adding
401 keys while keeping every earlier payload. Eight alternate certificate
occurrences remain in trial archives. The new catalog has **149 direct roots /
43 guarded decisions** (42 negative, one positive). All 104 original ready cores
remain in history; the extended frontier has 104 available roots and 47 pending
proposals in the union as well as the candidate trials.

All **451 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,229 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **358 sources / 3,979 artifacts /
70 manifests** remain unchanged. Runtime binds 363 sources; the post-hoc analyzer
brings the ledger to 364. Structural authority remains 2,614 patterns / 259 pairs /
17 missing children, original 17/24 / 999 steps, separate supplemental 24/24 /
208, and original case 7's discovery pointer. No new Lean or unrestricted-SAT claim.
Checkpoint SHA-256: `6c60e95e1a8f0f0dc12fc2e24dba38178cc35ae5e13a07a28d43b30d0180700c`.
Report SHA-256: `c5c12f205dd77b370d4120ce0baf06e33ab0ecc1268e2fa7d8ac14fbd4ef5275`.
The manuscript builds to 196 pages without warnings; all 64 proof blocks are unchanged.
The new manifest binds 63 artifacts; next audit inherits **4,042 artifacts / 71 manifests**.

## Previous investigation: support proofs constructed on demand

[Deferred support construction](deferred-support.md) now implements the prior
highest-priority experiment. On a further 192 unseen constructed inputs, eager
and deferred policies transfer the same 19 supports to **23 novel targets** and
reduce fresh expansions **302 -> 177 (41.39%)**. Deferral constructs **209 rather
than 1,310** support-proof rows, cutting all new rows **1,648 -> 547**. Complete
time falls **11.43996 -> 10.30105 seconds (9.96%)** against eager construction,
but remains **9.21% above the old-bank control's 9.43274 seconds**. All three
matched triples have both effects. Keep the mode optional.

**What is established:** discovery returns the same 104-support antichain without
publishing derived proofs. A matched proposal must be materialized and checked
before the frozen subset rule can publish UNSAT. All 209 materialization rows
are used by this stream's query proof closure; 83 proposed roots remain pending
in the deferred trial. Eager construction retains 1,101 additional preparation
rows outside that query closure. This is measured liveness, not a minimum-proof
guarantee. No prior result is deleted. Guarded answers still require the complete
source--guard--child evidence.

**Cost limits:** mean query time is 19.22% higher than eager construction because
needed construction moves to the query, although complete time improves. Mean
RSS is 3.78% lower than eager, but paired differences change sign; no robust memory
gain is established. SQLite falls 2.92% and gzip 4.47% against eager. Relative to
the old bank, mean RSS rises 1.87%, gzip rises 0.17%, and raw sidecars add further
space. Discovery still costs **1.22612 seconds**, against **0.33067 seconds** of
query savings over the old bank. Cold replay and compression remain the largest
phases, at 34.94% and 29.71% of complete deferred time.

**Next acquisition target:** reuse persisted ready supports and source-bound
proposals, then profile incremental discovery on genuinely new negative sources.
Do not repeatedly re-extract the existing 104-core bank. Before another global
recognizer, inspect the **21 unmatched negative queries / 177 expansions** for
shared conditional supports, particularly template 8 (**90 expansions**). New
study cases 164 (20), 35/160 (17 each) and 16/136 (16 each) are the largest misses.
Every measured hit still shares its first origin's guard clause. Cross-guard
and broad cross-category discovery remain open; constructed neighbouring inputs
do not demonstrate an efficient partition of arbitrary SAT.

**Comparison scope:** all workers use identical historical **14,630-key**
pre-acquisition clones. Selection excludes all **768** previous sidecar answers
and complete roots from the **16,320-key latest authority**, which stays
preserved with its already-ready bank. This isolates a construction policy,
not savings from rebuilding an already-paid bank. The new outer timer includes
final digest and report generation; historical percentages are not composable.

Resume `experiments/results/cnf-deferred-support/checkpoint.json`. Preserve every
inherited field plus `deferred_support_study`, `deferred_support_decisions`,
`deferred_support_proposals` and `reference_union`. The union has **16,760 keys /
51,294,208 SQLite / 4,046,593 gzip bytes**, with 440 new keys and 46 alternate
certificate occurrences retained in trials. The new catalog has **138 direct
roots / 54 guarded negatives**. All 104 previously ready cores remain ready in
the final union; the 83 pending proposals describe only the historical trial.

All **442 tests**, nine full archive checks / **3,456 trial query replays**, every
union node, **1,037 inherited decisions** and all new decisions pass. Prior
**353 sources / 3,923 artifacts / 69 manifests** are unchanged. Runtime binds
357 sources and the analyzer brings the ledger to 358. Structural authority stays
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
All 64 manuscript proof blocks remain unchanged; no new Lean claim.
Checkpoint SHA-256: `711be45dc4a9e5a79c3c94aaac179ee1a44af1013ca364f9633df8fc97af20cc`.
Report SHA-256: `3c762d725a6e0f058e309a098f124334a38feee3f4e8856069a2a41a5974bbb7`.
The manuscript builds to 195 pages without warnings. The new manifest binds
56 artifacts; the next audit inherits **3,979 artifacts / 70 manifests**.

## Previous investigation: checked support transfer between guarded cofactors

[Cofactor support reuse](cofactor-support.md) certifies **16 previously uncached
restricted subproblems** through checked clause containment. Fresh expansions
fall **234 -> 162 (30.77%)**, and query time **1.33223 -> 0.87849 s (34.06%)**.
But constructing the whole bank adds **1,310 proof nodes** and makes complete
time **7.93324 -> 9.75898 s (23.01% worse)**, peak RSS **9.23% higher**, and SQLite
**3.23% larger**. Every matched pair regresses in total time. Keep this optional;
fewer expansions do not establish an end-to-end gain.

**Highest next target: defer new support proofs until a match.** Preparation
visits 1,075 old negative proof nodes and constructs 112 raw supports; the
containment antichain has 104 and preserves every superset match. Only 14 of
those supports are used here. The full retained bank needs 1,272 preparation
nodes, but the matched supports and query proofs need only **118**. Simple
pruning saves at most 38 nodes; building only after a checked match is the more
credible next test. Support proposals alone must never justify UNSAT. Discovery,
materialization, checking and persistence must all remain charged. The policy
has not yet been implemented or measured; selecting only the 14 observed cores
would use future workload information and can lose coverage.

**Preserve and reuse this acquired bank:** its 104 cores are already materialized
in the latest union. Load `cofactor_support_bank` and its `cores` field for warm
runs instead of extracting them again. To evaluate a new construction policy,
use explicitly matched historical seed clones or newly discovered supports, and
retain an unseen stream; do not present already-paid construction as a saving.

**Coverage limits and remaining cases:** 145 of 148 inherited guarded decisions
are negative; the three SAT cofactors do not supply negative supports. The new
stream returns 84 SAT / 108 UNSAT, with 63 old full-query core hits, 83 witness
publications and 46 guards (45 negative, one positive). Six targets were cached.
All 72 avoided expansions come from the 16 new cofactor hits. Each measured hit
shares the guard clause of its first retained origin; cross-guard transfer is
covered only by a unit test. No broader cross-category coverage is established.
The candidate still performs 151 negative / 11 positive expansions on 24 cases.
New-catalog case 7 is SAT; it is distinct from original structural case 7.
Largest remaining negatives are new cases 191, 82, 112, 184 and 87.

Resume `experiments/results/cnf-cofactor-support/checkpoint.json`. Preserve all
inherited fields plus `cofactor_support_study`, `cofactor_support_decisions`,
`cofactor_support_bank` and `reference_union`. The union retains **16,320 keys /
49,610,752 SQLite / 3,953,721 gzip bytes**. Earlier payloads win overlaps; sixteen
alternate certificate occurrences remain in trial archives. The new catalog has
**146 direct roots / 46 guarded records**. Guarded decisions bind source, guard
and child together; a negative child alone is not the complete-query identity.

All **434 tests**, eight complete archive checks / **3,072 trial query replays**,
every union node, **845 inherited decisions** and all new decisions pass. All
348 prior sources, 3,873 artifacts / 68 manifests and 64 proof blocks are
preserved. Runtime binds 352 sources; the post-hoc analyzer brings the ledger to
353. The paper builds to 194 pages without warnings. Structural authority stays
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
Checkpoint SHA-256: `c27c247ca9b278ab7ce44fab7db020a933dc5dc1a688c4a3e01e5fc85c3c11f8`.
Report SHA-256: `6d2f204b3476475735747858344b2caaef52e86921b2e7fecf20672e21226692`.
The new manifest adds **50 artifacts**; the next preservation audit inherits
**3,923 artifacts / 69 manifests**.

## Previous investigation: one census per cold proof snapshot

[Snapshot replay](snapshot-replay.md) replaces 384 repeated cold size scans with
one independent census on a pinned read-only view. It runs the same frozen
complete audit and verifier. On the next 192 unseen double deletions, mean
complete time falls **15.15167 -> 7.84969 s (48.19%)** and cold replay
**10.43075 -> 3.12634 s (70.03%)**. Four alternating process pairs preserve
identical expansion work and identical logical/physical proof archives. Peak
RSS rises **0.39%**; no memory or storage reduction is shown. The earlier delta
memory regression remains open.

**Current largest costs:** complete cold verification is **39.83%** of candidate
worker time, compression **33.07%**, query work **16.20%**, setup **9.56%**.
Further total-cost improvements need evidence about repeated proof normalization,
allocation or rewriting unchanged persistent evidence. Profile before choosing
another checker optimization; retain every logical check and all old certificates.
Snapshot totals are independently computed, not trusted from saved accounting.
The benchmark uses private closed clones and one owned process per audit; shared
service concurrency and hostile private-connection changes are outside scope.

**Next primary structural target:** **37 negative queries** still require fresh
search and account for all **270 expansions / 85 splits**. They belong to 40
guarded negatives; all modes otherwise use 54 core hits and 98 witness answers,
returning 98 SAT / 94 UNSAT. Cases 100, 41 and 188 use 21, 19 and 18 expansions;
original template 12 supplies 129/270. Compare refutation supports and guarded
cofactors across these cases. A full-query negative certificate requires checked
composition of the stronger UNSAT premise and the restricted child; treating
the child as the query is invalid. Charge construction, checking and persistence
when testing any transfer. The 121-core antichain remains unbenchmarked and
preserves existing superset coverage rather than expanding it.

Resume `experiments/results/cnf-snapshot-replay/checkpoint.json`. Preserve every
inherited study/decision field plus `snapshot_replay_study`,
`snapshot_replay_decisions` and `reference_union`. The union adds 422 keys and
retains **14,630 keys / 46,530,560 SQLite / 3,674,583 gzip bytes**. The new catalog
has **152 direct roots / 40 guarded cofactor records**; guarded replay binds the
source, guard and child together. All 384 earlier double-deletion answers were
excluded from selection, including those without direct roots. Do not multiply
speedups across different input sets or ignore earlier acquisition costs.

All **426 tests**, eight complete archive checks / **3,072 trial query replays**,
every union node, **653 inherited decisions** and all new decisions pass using
the ordinary solver for independent validation. All 343 prior source bindings,
3,831 artifacts / 67 manifests and 64 proof blocks are preserved. Runtime binds
347 sources; the post-hoc analyzer brings the final ledger to 348. The manuscript
builds to 193 pages without warnings. Structural authority is unchanged:
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
Checkpoint SHA-256: `86ed6d602def81787d3b1b88c9b3151f8ccba1929f223d73a279acd438bd2bfe`.
Report SHA-256: `0b5be879e1beeda66a27fef48fd42cfa3fa5f7df02cd73bdc6e8202fe0f9fe22`.
The new manifest adds **42 artifacts**; the next preservation audit inherits
**3,873 artifacts / 68 manifests**.

## Previous investigation: exact insertion deltas over persisted proof graphs

[Incremental archive accounting](incremental-archive-accounting.md) removes the
full-history query scans identified by the previous profile. On the next **192
unseen double deletions**, complete time falls **37.48164 -> 14.81201 s (60.48%)**,
and query time **23.96449 -> 1.37640 s (94.26%)**. All modes use the same retained
145-core bank and 13,869-key seed; initial extraction remains charged separately.
The existing ledger accounts for an 18.65% complete-time reduction; adding the
new guarded insertion cursor saves a further 51.42%. Full inventories fall
**772 -> 3**, with final preservation and cold proof checks retained.

**Regressions and boundaries:** peak RSS rises **9.56%** to 448,435,541 bytes.
Accounting adds 4 KiB SQLite / 696 gzip bytes; logical proof rows are identical.
The cursor requires an exclusively owned append-only session, detects external
commits/schema changes and rejects local rewrites. Opening, conflict repair,
full cold replay and compression remain charged. No proof-space compression,
new search algorithm, broader structural closure or amortized break-even is shown.

**Highest next cost target:** the unchanged cold audit is 67.95% of candidate
worker time, compression another 17.09%. A separate cold profile attributes
**7.21981 s** to **384 full archive-size censuses** within a **14.87488 s**
instrumented audit. Test one independently checked census for an immutable
snapshot while retaining every proof and query check. Also locate the RSS
regression before claiming a memory improvement. Do not mix instrumented and
unprofiled timings or add nested profiling categories.

**Next structural target:** all modes return 96 SAT / 96 UNSAT, with 41 core
hits, 96 witness publications and 55 guarded negative queries. Of these, 44
use fresh search, accounting for all **202 expansions**, including 56 splits. Cases 66 and 76 each use 16
expansions, case 41 uses 12. Inspect their shared supports/cofactors for further
reuse. Case IDs belong to this experiment's catalog. Repeated visits add no rows.
The antichain of 121 old supports remains an unbenchmarked alternative; it
preserves recognized supersets but need not reduce these unresolved searches.

Resume `experiments/results/cnf-incremental-archive/checkpoint.json`. Preserve
all inherited studies and decisions plus `incremental_archive_study`,
`incremental_archive_decisions` and `reference_union`. The new union retains
**14,208 keys / 44,781,568 SQLite / 3,563,875 gzip bytes**. Its new catalog has
**137 direct query certificates / 55 guarded cofactor records**; the latter
require source, guard and child together. Structural authority is unchanged:
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 proof
steps, separate supplemental 24/24 / 208, and original case 7's discovery pointer.

All **418 tests**, nine cold archives / **3,456 trial query replays**, every union
node, 461 inherited decisions and all new decisions pass. Preserve 336 earlier
sources, 3,783 artifacts / 66 manifests and all 64 proof blocks. Runtime binds
341 sources; the attribution and cold-profile tools bring the final ledger to
343. The manuscript builds to 192 pages without warnings.
Checkpoint SHA-256: `53cf74216546839373aeb00d7d14321be0617a3b35da4a2cefa086aa1ee6a02d`.
Report SHA-256: `9feaf6eb279c05a8355c19e1d855eba693946a9be536d8367e24e299acab0c89`.
The new manifest adds **48 artifacts**; the next preservation audit inherits
**3,831 artifacts / 67 manifests**.

## Previous investigation: incremental accounting after checked UNSAT reuse

[Checked UNSAT supports](unsat-support-reuse.md) recognize new negative inputs by
exact containment in a retained refutation core. On **192 unseen double
clause deletions**, the full bank certifies **40 UNSAT queries** by this route
and cuts fresh expansions **524 -> 355 (32.25%)**. However, complete runtime
rises **28.51440 -> 39.96590 s (40.16%)**, mean peak RSS **28.15%**, and SQLite
**23.74%**. The regression occurs in all three repetitions; this remains an
optional experiment. All modes return **102 SAT / 90 UNSAT**. The small
three-core bank saves only five expansions and has no reliable runtime gain.

**Highest next target: exact incremental archive accounting.** A separately
profiled warm pass spends **5.80760 s** copying full row inventories and
**3.45805 s** recomputing archive size: **84.55%** of its **10.95876 s** loop.
Core matching takes only **0.01618 s**. Replace per-query full-history scans
with checked append-only deltas and maintained size totals, preserving a full
final audit. Then compare further unseen edits using the **already persisted
core bank** and identical full initial unions. Charge initial core acquisition
and retained storage explicitly; no amortized break-even has been shown.

**Structural gain and limit:** all 188 known negative sources yield 145 distinct
supports. The original templates shrink 82 clauses to 64 and 63, and 96 to 80.
Derived nodes use the frozen verifier and existing certificate format. A failed
match never implies SAT or UNSAT. Supports are not minimal, arbitrary renamings
are not searched, and the acquired proof DAG can still be exponential. The
full bank leaves **328 negative / 27 positive** fresh expansions.

**Retained compression evidence:** removing dominated supports leaves **121**
and preserves the recognized family for every superset query. Its required
preparation graph shrinks **4,092 -> 3,804 nodes**; this candidate has not been
benchmarked. Only **10/4,102 preparation nodes** are unused by the current full
bank and query proofs, so simple pruning offers little. No rows were deleted.
The main cost is real retained proof data plus repeated accounting over it.

Resume `experiments/results/cnf-unsat-support/checkpoint.json`; the bound study
points to `all-0/cores.json`. Preserve inherited studies and decision catalogs,
plus `unsat_support_study`, `unsat_support_decisions` and `reference_union`.
The union retains **13,869 keys / 43,380,736 SQLite / 3,479,528 gzip bytes**.
The new catalog has **139 direct certificates and 53 explicit guarded cofactor
records**; never substitute a cofactor key for the complete query identity.
Structural authority remains **2,614 patterns / 259 pairs / seventeen missing
children**, original **17/24 / 999 proof steps**, and separate supplemental
**24/24 / 208 proof steps**. Original case 7 is its separate discovery pointer.

All **403 tests**, nine cold archive checks / **3,456 trial query replays**, the
support screen, every union node, 269 inherited decisions and all 192 new
decisions pass. Earlier 330 sources, 3,723 artifacts / 65 manifests and 64 proof
blocks are preserved. Runtime binds 334 sources; post-hoc attribution and warm
profiling bring the final ledger to 336. These are constructed development
inputs, not independent evidence for uniformly efficient arbitrary SAT.
Checkpoint SHA-256: `07e1a04864038caf4ba5a60b388e8c22b1c90116d9b11d819e7b7bd7dd7d31cf`.
Report SHA-256: `f732924b833023efc8f3a52a33071bdff524d7abc105790eed8f41c8bfb4fdba`.

The new manifest adds **60 artifacts**; the next audit inherits **3,783 artifacts /
66 manifests**. The manuscript builds to **191 pages**.

## Previous investigation: negative proof reuse after bounded model rotation

[Bounded model rotation](model-rotation.md) reduces fresh reference expansions
**1,876 -> 1,509 (19.56%)** on **257 previously uncached deletions** of three
checked UNSAT templates. It publishes 57 checked SAT certificates, making 1,566
new rows. Complete runtime falls **11.28948 -> 10.48075 s (7.16%)**, mean peak RSS
**3.86%**, and SQLite **4.15%** against the guarded control. Ordinary solving uses
6,126 expansions and 27.82621 s. All modes agree on **72 SAT / 185 UNSAT**;
repeated visits add no rows. Three process triples balance mode position.

**Highest next target: reusable negative proof supports.** UNSAT queries consume
**1,216/1,509 expansions (80.58%)**, unchanged by rotation. Old template 12
accounts for 612 of these, with new deletion-catalog case 11 alone using 47.
The exact inputs, removed clauses and target hashes are retained in
`cost-attribution.json`. Determine whether checked UNSAT certificates expose
small clause supports or shared negative cofactors that transfer to further
queries by checked containment. Do not assume that failed rotations identify
UNSAT, or that two individually safe deletions can be combined safely.

**Retained limits:** 189 flips yield 99 singleton-false outcomes and 90 failures.
Of these, 57 publish absent keys and 42 reach old ones. Only 37 first query
encounters use a published direct answer; publication count is not avoided-solve
count. The first two templates hit 64-flip caps with six queued flips each;
the third exhausts its chosen-witness queue after 61 flips. Alternative witnesses
can open different routes. All attempts, origins, models and cursors persist;
cold certificate replay works, while engine-state import/resume remains open.

**Storage remains a gap:** combined database gzip and raw sidecars is 9,921,762
bytes, below guarded 10,419,742 but above ordinary 8,541,670. Guard sidecars repeat
whole stronger CNFs. The durable union preserves all old payloads and adds
7,935 distinct keys: **9,104 keys / 32,595,968 SQLite / 2,524,507 gzip bytes**.
Smaller arm memory does not mean smaller total retained history. One-witness
rotation has a bounded scan budget, not a uniform efficient SAT guarantee.

Resume `experiments/results/cnf-model-rotation/checkpoint.json`. Preserve all
inherited reference studies/decisions and the new `model_rotation_study`,
`model_rotation_decisions` and `reference_union`. Structural authority remains
**2,614 patterns / 259 pairs / seventeen missing children**, original **17/24 /
999 proof steps**, and separate supplemental **24/24 / 208 proof steps**.
Original case 7 remains its independent structural discovery pointer.

All **394 tests**, nine cold archive checks / **4,626 query replays**, rotation
origins and every union node pass. Earlier twelve reference decisions also
replay unchanged. Selection/preflight costs 0.35307 s separately; earlier
acquisition costs remain in historical records. These are constructed
neighboring inputs including known positive candidates, not a blind holdout.
Runtime binds 329 sources; the post-hoc attribution brings the final ledger
to 330. All prior 325 sources, 3,669 artifacts / 64 manifests and 64 manuscript
proof blocks are preserved.
Checkpoint SHA-256: `1049220a45fe5de68b1d3657ffd86dd0ea8ed0fd7202120324f94472b4304e1a`.
Report SHA-256: `91b60f9fb1b3403cae305cc5a23df6f76cc0a8aa92d772b084c281de0fd36535`.

The new manifest adds **54 artifacts**; the next audit inherits **3,723 artifacts /
65 manifests**. The manuscript builds to **189 pages**.

## Previous investigation: model reuse on previously unseen clause deletions

[Checked SAT witness publication](clause-witness-reuse.md) removes the dominant
positive-query search on the twelve constructed edits. Relative to the UNSAT
guard alone, fresh reference expansions fall **427 -> 59**, with **six answer
publications / 65 new stored rows**. Whole time falls **1.19691 -> 0.59381 s
(50.39%)**, RSS **18.15%**, and SQLite **40.27%**. Ordinary solving needs 502
expansions and 1.26932 s. All modes return nine SAT and three UNSAT answers;
all repeated visits add zero rows. These are conditional decision measurements,
not structural-coverage gains or an unrestricted-SAT guarantee.

**Highest next discovery target:** previously unseen deletions of the UNSAT
templates. Existing twelve roots are now cached. A seven-attempt, one-variable
model-rotation screen finds two valid new-input witnesses from case 9, both for
**28 variables / 81 clauses / 238 literals**, with absent reference roots.
Flipping variable 260 leaves only `(-230,120,260)` false; flipping 150 leaves
only `(-100,150,160)` false. Their complete CNFs and models are preserved in
`rotation-screen.json`. Publish/check these candidates and test a fixed broader
set of neighboring deletions against ordinary and guard controls, charging
all failed proposals and full or indexed clause checking. This uses established
model-rotation reasoning; no rotation speedup has yet been measured.

**Retained failures:** case 7's three flips leave two or three clauses false;
both case-13 flips leave three. Case 13 still needs 22 of 59 fresh reference
expansions. No SAT witness supplies an UNSAT conclusion. A checked negative
premise still leaves an exceptional cofactor that can contain arbitrary SAT.

**Dominant measured costs now:** complete reference checking and compression,
about **68%** of the shorter stream. Database gzip plus raw query sidecar is
**676,971 bytes**, versus 811,502 guarded and 760,874 ordinary. Sidecar size alone
increases. All modes inherit the same 613-node seed, whose acquisition cost of
**0.91359 s** remains separate; this run's seed preflight costs **0.18338 s**.
Three triples balance position, but these remain development examples.

Resume `experiments/results/cnf-clause-witness-reuse/checkpoint.json`. Its new
`reference_union` retains **1,169 distinct keys**, using **5,931,008 SQLite /
450,067 gzip bytes**. No reference key is newly discovered relative to the
combined previous arms; alternate valid SAT certificates remain in the trial
archives, and the union keeps earlier payloads. Preserve `reference_study`,
`witness_reuse_study`, `reference_decisions` and the separate rotation proposals.
The structural authority remains **2,614 patterns / 259 pairs / seventeen
missing children**, with original **17/24 / 999 proof steps** and supplemental
**24/24 / 208 proof steps**. Original case 7 remains its discovery pointer.

All **388 tests**, nine new stream reconstructions / **216 query replays**, the
four prior streams and the reference union pass. The control databases match
the prior study byte for byte. All prior 320 sources, 3,620 artifacts / 63
manifests and 64 manuscript proof blocks remain unchanged. Runtime binds 324
sources; the post-hoc rotation screen raises the final ledger to 325.
Checkpoint SHA-256: `79c224246b77270980ddb5685ab32464df19057dfe95a7db976a5b18019de63b`.
Report SHA-256: `3005787a6d6eb257b19ee39a7b4cd33137384f93ec0f3c2547142b31bfd254d2`.
The new manifest adds **49 artifacts**; the next audit inherits **3,669 artifacts /
64 manifests**. The manuscript builds to **188 pages**.

## Previous investigation: reuse SAT witnesses before solving edited inputs

[Checked clause-deletion guards](clause-deletion-guard.md) reduce new reference
residual nodes **502 -> 427 (14.94%)**, decision splits **200 -> 174**, and complete
stream time **1.27860 -> 1.17492 seconds (8.11%)** on twelve constructed edits.
This is a separate SAT decision experiment with the unchanged `ResidualSolver`,
not a structural-coverage increase or a new production policy. Six retained
UNSAT proofs justify forcing the removed clause false; six SAT premises decline.
Both modes return nine SAT and three UNSAT answers, independently replayed.

**Highest next target:** positive witness transfer. Edits **19, 21 and 23** use
**364/427 remaining reference nodes**, although their undeleted formulas are SAT.
The analyzer verifies that all six retained SAT-template models satisfy their
edited inputs. Implement checked witness reuse before fresh search, preserving
the UNSAT guard and an ordinary control. Charge matching, model checking and
persistence. The current wrapper does not yet use this positive transfer.

**Limits exposed:** case 13 remains at **22 reference nodes / eleven splits**
after forcing two variables; this is distinct from its earlier 29 structural
patterns. Case 7 uses two more splits. Cases 15 and 17 supply 67 of 75 avoided
nodes, reducing **43/26 -> 1/1**. The general exceptional cofactor can remain
arbitrary SAT: `F = H AND NOT x AND x` is cheaply UNSAT, while deleting `x` and
forcing it false leaves arbitrary `H`. The underlying clause-deletion reasoning
is established in transition-clause/MUS work; no new complexity claim follows.

**Accounting:** preparing the common 613-node reference seed costs **0.91359 s**
separately. SQLite falls 6.42%, but compressed database plus raw query sidecar
increases **760,368 -> 810,993 bytes**. Two repetitions establish only this local
measurement; the small RSS change is not broad memory evidence. Cold archive
checking remains about 28% of stream time. Tests and retrospective validation
run outside the timed workers.

Resume `experiments/results/cnf-clause-deletion-guard/checkpoint.json`. It retains
the unchanged **2,614 structural patterns / 259 pairs / seventeen missing
children**, original **17/24 coverage / 999-step proof**, and separate **24/24
supplemental coverage / 208-step proof**. Its `reference_study` binding preserves
the new decision archives and guard sidecars; keep them on continuation.
All **382 tests**, all four reference streams and all **96 query-result replays**
pass. The analyzer also checks the hardness construction on all 512 two-variable
CNFs. Runtime binds 319 sources; the final ledger binds 320 with the analyzer.
All prior 315 sources, 3,588 artifacts / 62 manifests and 64 proof blocks remain
unchanged. Original case 7 remains the separate structural discovery pointer.
Checkpoint SHA-256: `e182f0023fc82ecb8ec674cbdc33c913ca91a104066b0a6d67c72812f8ea6b05`.
Report SHA-256: `70507d8854ddf5d7110b00c16604f5956e452e9003fb4af2cd011deb71f5b005`.
The new manifest adds **32 artifacts**; the next audit inherits **3,620 artifacts /
63 manifests**. The manuscript builds to **187 pages**.

## Previous investigation: reuse after edits change the exact formula

[Cross-input join transfer](join-transfer.md) avoids **35 acquisitions and 154
probes** on 24 distinct constructed CNFs. The unchanged solver receives only
CNFs. Its two matched histories differ by exactly **39 saved proof nodes and
four splits**. All 24 query proofs match across histories; the second visit
acquires nothing. Acquisition falls **206 -> 171**, probes **1132 -> 978**.
Three first encounters account for the entire difference: twelve, ten and
thirteen saved nodes below the 27-, 32- and 39-variable joins. The small anchor
and two nodes above the useful 32-variable descendants remain unused.

**Highest next discovery target:** clause-deletion controls receive no
acquisition saving and account for **136/171 new patterns and 768/978 probes**.
Inspect constructed **case 13** (33 variables / 95 clauses / 274 literals /
width four, 29 new patterns / 218 probes) against its matching preimage. Determine
which clause dependencies block transfer, and seek an exact shared residual or
checked split transport. An edit invalidating one projection does not exclude
all reuse. Keep variable maps, boundary checks and proof dependencies explicit.
Original **case 7** remains a separate broader coverage control, with seven
open saved children and pivot 14's true child already covered.

**Largest measured whole-stream cost:** full cold auditing, about **52%** of
14.48/14.33 seconds. Mean solve/bookkeeping falls 4.48%, but whole runtime only
0.99%; two pairs do not establish a reliable small timing effect. RSS rises
0.168%, SQLite 0.091% and gzip 0.486%. The treatment ends with all control rows
plus four unused preloaded nodes. Seed preparation takes **16.014 seconds**
separately and historical acquisition remains charged. This is a local reuse
saving, not a demonstrated net acquisition-plus-use or memory improvement.

**Secondary opportunity:** some positive preimages miss their specified anchor
under the default reduction order despite a checked one-pair projection. Reuse
the earlier projection infrastructure cautiously; its expensive global-index
preparation and negative frontier results remain preserved. Do not tune a new
route heuristic on these 24 constructed cases alone.

Restore `experiments/results/cnf-join-transfer/checkpoint.json`: **2,614 patterns /
259 pairs / seventeen inherited missing children**, preserving all earlier rows
and all trial additions. Original structural coverage remains **17/24**, with
the same **999-step proof**. The separate 24 constructed inputs have a **208-step
proof**, bound by `supplemental_queries` and `supplemental_proof`. Preserve both
catalogs in later unions. Storage is **47,181,824 SQLite / 2,375,854 gzip bytes**.
All **376 tests**, four independent stream reconstructions and 192 query-proof
replays pass. Prior 309 sources, 3,550 artifacts / 61 manifests and all 64
manuscript proof blocks remain unchanged. Runtime binds 313 sources; the final
ledger also binds the post-hoc analyzer and supplemental replay checker (315). Synthetic structural
coverage does not imply efficient arbitrary SAT or supply SAT/UNSAT answers.
Checkpoint SHA-256: `5bd57b9b2bf1007a4b447764c40d8c4d920450f6f90699342926218c41b9a652`.
Report SHA-256: `98eb6b23f6bcb2d80c9dc7714bad65ce5de37c6fb0875cdd8e9ee7c4160cf346`.
The new manifest adds **38 artifacts**; the next audit inherits **3,588 artifacts /
62 manifests**. The manuscript builds to **186 pages**.

## Previous investigation: transfer exact nonterminal joins to new inputs

[Case-10 transfer](progress-transfer.md) raises structural coverage **16/24 ->
17/24**, but the unchanged gate makes the same costly choice as always-pilot.
The first trial grows **1042 -> 1468 literals**, so the gate explores; the second
route leaves **1040**, and both pilots switch to pivot 17. Committed/pilot counts
are **106/119 patterns, 653/778 probes, eighteen/twenty-four assumptions and
nine/twelve splits**. Gated and always-pilot operations, proofs and archives
match. The gate stays optional; growth of the first frontier does not establish
the value of another route.

**More promising structural evidence:** the distinct final proofs share **39
new nodes, including 37 nonterminals**, arranged below four identical formula
keys. Two joins follow elimination from different parents and two follow
probing. The joins contain 27, 32, 39 and four variables, with 12, 12, 13 and two
new descendant nodes respectively. Their disjoint new regions plus one inherited
contradiction form a **40-step independently verified subproof**, saved under
`experiments/results/cnf-progress-transfer/joins/`. These are exact policy/depth/
canonical-CNF matches, with checked boundary transformations.

The 39-variable join is reached from two different 40-variable / 151-clause
parents with 460 and 457 literals. Elimination produces the same 153-clause /
475-literal formula in both routes. Increasing literal count can therefore
reach a reusable boundary. The measured acquisition intersection has 45 rows
and five splits; the proof intersection has 39 rows and four splits.

**Highest next target:** test whether previously unseen related inputs can
reach these joins cheaply. Use distinct parents with the same checked
elimination image and edits that break the image; keep discovery, verification,
lookup, replay and persistence in the comparison. The exact cache already
recognizes an encountered key. The missing work is reaching it and establishing
the boundary relation. The current finding concerns one original under different
policies, not a cross-input saving. Its whole root is already covered, so
re-solving that same query through these joins would not be a useful benchmark.

**Costs:** committed/pilot/gated whole means are **9.31591 / 9.39216 / 9.41249 s**.
Gated local expansion is **17.79% higher**, RSS **0.65% higher**, SQLite **0.54%
higher** and gzip **0.57% higher** than committed. Mean whole time is 1.04%
higher, but two triples cannot establish a small timing effect. Full auditing
remains **78--79%** of time. Join analysis costs 0.18489 s separately; raw shared
row bytes are not measured memory savings.

Restore `experiments/results/cnf-progress-transfer/checkpoint.json`: **2,443 patterns /
249 pairs / seventeen inherited missing children / 17 of 24 originals covered**,
with a **999-step proof**. Seven originals remain unknown. All 180 distinct new
patterns and sixteen splits survive; storage is **44,810,240 SQLite / 2,271,560
gzip bytes**. All **372 tests** and six independent archive replays pass. Prior
307 sources, 3,500 artifacts and 64 manuscript proof blocks are unchanged. The
measured checkpoint binds 308 sources; the final preservation ledger also binds
the post-hoc join analyzer, totaling 309 sources.
The new manifest adds **50 artifacts**; the next audit inherits
**3,550 artifacts / 61 manifests**.
Checkpoint SHA-256: `00339dad38ba2c73524de9610a7dacb83b82eef1c6cf34d938e95867e38d7812`.
Report SHA-256: `de158d11eb005a7490c1ebd26c971e4ec28f9bbad754829b7b8fc843da133237`.

The separate discovery pointer is **case 7**, random 3-CNF with selected
**33 variables / 152 clauses / 470 literals / width four**. All eight saved
children exist; pivot 14's true child is covered and seven remain open. Only
the depth-zero original root exists. Keep it as a broader coverage control while
testing reuse beyond one original. No default policy or arbitrary-SAT bound changes.

## Previous investigation: test the limits of the progress gate

[The progress-gated trial](progress-pilot.md) closes connected case **21**, raising
structural coverage **15/24 -> 16/24**. The rule was frozen before acquisition:
skip the second trial when the first completed acquisition strictly reduces the
selected unresolved literal mass, otherwise use the existing two-route pilot.
Partial work and the original baseline survive cold restart. All trial and
continuation work shares the unchanged 128-admission / sixteen-operation budget.

The first trial reduces **1141 -> 1099 literals**, so the gate stays on pivot 23.
Always-pilot tries pivot 17 and sees **1097**, changing routes for a two-literal
advantage. Gated/committed acquisition is **24 patterns / 100 probes / eight
assumptions / four splits**, versus **32 / 175 / twelve / six** for always-pilot.
The gate matches committed operations, proof and stored bytes. The always-pilot
proof is one step shorter (41 versus 42), but its eight losing-trial patterns
are unused. The different final proofs share no newly acquired node.

Against always-pilot, local expansion falls **35.25%**, peak RSS **0.65%**, SQLite
**0.40%** and gzip **0.57%**. Whole-stream means are committed/pilot/gated
**8.48923 / 8.75818 / 8.62917 s**. Gated versus pilot pair rankings disagree;
the 1.47% lower mean is not reliable speedup evidence. Gated is 1.65% slower
than committed in mean whole time despite identical work. Complete auditing
still takes about **82--83%** of time; two triples cannot isolate small overheads.
Do not promote the policy or equate acquisition counts with end-to-end savings.

**Next target:** case **10**, random 3-CNF, selected **45-variable / 180-clause /
557-literal / width-five** residual. All eight children of saved pivots 20, 3,
17 and 22 exist and remain uncovered. Only the depth-zero original root exists.
Transfer the unchanged rule and both controls, checking the prefix precondition.
Look for an early literal decrease that hides an expensive continuation, and
explain structural differences if policies diverge. The gate is not a potential
function or a minimum-cost guarantee. Broader nonterminal reuse and efficient
full-history auditing remain open.

Restore `experiments/results/cnf-progress-pilot/checkpoint.json`: **2,263 patterns /
233 pairs / seventeen inherited missing children / 16 of 24 originals covered**,
with an **884-step proof**. Eight originals remain unknown. The union retains all
48 distinct new patterns and nine splits, using **42,033,152 SQLite / 2,131,824
gzip bytes**. All **372 tests** pass. Independent full replay checks six archives,
original bindings, query proofs, complete catalogs, preserved prefixes, shared
budgets and cold scheduling state. All prior 303 sources, 3,453 artifacts and
64 proof blocks are unchanged; the new source ledger has 307 entries.
The new manifest adds **47 artifacts**; the next audit inherits
**3,500 artifacts / 60 manifests**.
Checkpoint SHA-256: `2916dc12e35e4339580981da0ae8d36c2b20b0607471811e78f43044731f03e4`.
Report SHA-256: `e1c00e179d7a1fd0090fe50788c325912cc58216e69e9058df48bf72e42fe633`.

## Previous investigation: decide when another trial is worth acquiring

[The unchanged pilot transfer](pilot-transfer.md) closes case **13**, raising
structural coverage **14/24 -> 15/24**, but adds work without changing the proof.
Committed/pilot counts are **27/37 new patterns, 128/179 probes, six/eight source
assumptions and three/four splits**. Both choose saved pivot 41 and produce the
same 38-step proof. The pilot inserts exactly one extra trial after the first
operation; its ten extra patterns add no measured corpus coverage and are unused
by the proof. All results remain stored; future reuse is unproven.

Local expansion rises **37.18%**, peak RSS **0.40%**, total SQLite **0.41%** and
gzip **0.53%**. Whole-stream means are **8.33858/8.24283 s**, but the two paired
runs disagree on which mode is faster. The small mean difference is unresolved,
not a reliable speedup. Complete cold auditing still uses about **83--84%** of
time. Broader shared nonterminal structure remains unobserved in these proofs.

**Next target:** case **21**, a connected binary mixture with selected
**45-variable / 201-clause / 616-literal / width-four** residual. All eight saved
children of pivots 2, 1, 23 and 17 exist and remain uncovered. The depth-zero
original root exists; the optional depth-one root does not. Check the pilot's
prefix precondition. Test a progress-sensitive trial gate against committed and
always-pilot controls, preserving shared budgets and every acquired state.
One possible gate tries another route only when the first completed step fails
to reduce unresolved literal mass: case 11 grew 1106 -> 1535, case 13 shrank
610 -> 539. This is a **post-hoc hypothesis, not a validated policy**. Freeze it
before the next acquisition. Covered-child presence alone is insufficient, as
the earlier case-6 counterexample shows. No minimum-cost or arbitrary-SAT bound
follows from these development inputs.

Restore `experiments/results/cnf-pilot-transfer/checkpoint.json`: **2,215 patterns /
224 pairs / seventeen inherited missing children / 15 of 24 originals covered**,
with an **844-step proof**. Nine originals remain unknown. Union storage is
**41,099,264 SQLite / 2,073,167 gzip bytes**, retaining 37 new patterns and four
splits from both arms. All **367 tests** pass. The frozen independent validator
replays all four archives, positive proofs, original bindings, complete catalogs,
shared budgets and cold pilot state. Prior 302 sources, 3,417 artifacts and
64 manuscript proof blocks remain unchanged; the new ledger binds 303 sources.
The new manifest adds **36 artifacts**; the next audit inherits
**3,453 artifacts / 59 manifests**.
Checkpoint SHA-256: `3882197b783780457b4a2719fe8ef02e9abb00e1c5662d866ac38de5cfd25a33`.
Report SHA-256: `724cf369e17c738d0571de212fd021b9c348e73eca6a3f5bd25b2d7d265c3a49`.

## Previous investigation: transfer the bounded pilot and test its limits

[The charged pilot](pilot-refinement.md) improves case **11** and raises coverage
**13/24 -> 14/24**. It completes one nested acquisition on each of two saved
routes, within the same 128-admission / sixteen-operation batch allowance as
continuation. Pivot 6 grows to three obligations / 1535 literals; pivot 32 falls
to one / 559. The pilot selects pivot 32. Both trials and all their states are
charged and preserved; no default inference policy changes.

Committed/pilot acquisition is **44/19 patterns, 178/77 probes, eighteen/six
source assumptions and nine/three splits**. Local expansion falls **59.31%**,
whole stream **4.64%** (8.23501 -> 7.85315 s), peak RSS **1.52%**, total SQLite
**1.17%**, gzip **1.43%**. Complete audit remains **84.0%** of candidate time.
The large acquisition reduction is not a corresponding end-to-end or worst-case
saving. The 29-step winning proof has conditional depth two versus 53 steps /
depth five for the control. Neither depth is a fixed backdoor-size claim.

The pilot spends ten admissions and 55 probes on its two trials. Three states
from the losing route remain unused in the final proof but preserved. They are
also the three new states shared with the control; there is no new shared
nonterminal in the two final proofs. Broader structural reuse remains open.
The earlier failed one-profile lookahead and case-6 selection counterexample
remain active evidence against treating this single success as universal.

**Next target:** case **13**, random 3-CNF, selected **47-variable / 213-clause /
649-literal / width-four** residual. Eight saved children exist. Pivot **41's
true child is covered**; the other seven children remain open. Both original
recognition-depth roots exist. Transfer the unchanged pilot and committed
control, checking its unary-prefix/two-candidate precondition and charging all
trial work. Keep interrupted phases resumable. Replicate before considering
adoption or extending the scheduler to multiple interacting components.

Restore `experiments/results/cnf-pilot-refinement/checkpoint.json`: **2,178 patterns /
220 pairs / seventeen inherited missing children / 14 of 24 originals covered**,
with an **807-step proof**. Ten originals remain unknown. The union retains all
sixty distinct new patterns and eleven splits from both arms and occupies
**40,517,632 SQLite / 2,037,803 gzip bytes**. All **367 tests** pass, including
cold restart and shared-budget checks. All four archives independently replay.
All prior 298 sources, 3,378 artifacts and 64 manuscript proof blocks survive;
the new checkpoint binds **302 sources** and adds **39 manifested artifacts**.
The next audit inherits **3,417 artifacts / 58 manifests**.
Checkpoint SHA-256: `bf2097a76947241f8aa53a3e23438f117e4e9f146f7967b5408cf1ff3a794bf4`.
Report SHA-256: `d4f7b055b86a052827edf9086aae7b9ea7d4c69e6e1f4a841256b0ebac17c85d`.

## Previous investigation: predict downstream expansion, not just frontier size

[The case-6 history control](saved-split-reuse.md) closes another original:
**12/24 -> 13/24 coverage**. It also refutes a minimum-cost interpretation of the
current selector. Keeping four saved source splits chooses pivot 13, which has
one covered child and only 409 visible remaining literals. That continuation
adds **74 patterns / 547 probes**. An isolated control preserving all patterns
but omitting those four certificates reconstructs pivot 11 and adds **63 patterns /
345 probes**, despite its 796-literal initial frontier. Both close in one batch.
This changes selection information and certificate availability together; it is
not a recommendation to forget history.

**Highest discovery gap:** rank downstream simplification opportunities rather
than assuming smaller remaining CNFs are cheaper. An acquisition-free audit of
twelve remaining source nodes finds **no changed choice** when counting only
distinct uncovered obligations. Retain that null result. Next, compare the
committed-choice policy with bounded exploration of more than one saved route,
charging every trial and preserving admitted states; consult earlier lookahead
results before repeating work. No global optimum or cheap recognition of it is
established. The two case-6 routes share **none of their newly acquired states**,
so broader nonterminal reuse remains another gap.

**Costs:** retained/control means are **8.07061/7.82088 s** whole-stream and
**410.06/384.09 MB** peak RSS. Local expansion is slightly faster on the retained
route despite more probes. Gzip size ranks the arms opposite to SQLite size.
The full audit remains about **82%** of time; do not forecast end-to-end savings
from state counts alone. All four archives and both initial variants independently
replay. All **363 tests** pass; all old artifacts, sources and 64 proofs survive.

**Next target:** case **11**, random 3-CNF. Its selected residual has **45 variables /
196 clauses / 608 literals / maximum width five**. The eight saved children of
pivots 2,32,7,6 are present and uncovered. The depth-zero original root is present;
the optional depth-one root is absent and must remain unknown unless acquired.
The new pointer handles this explicitly; the first validator failure is preserved.

Restore `experiments/results/cnf-saved-split-reuse/checkpoint.json`: **2,118 patterns /
209 pairs / 17 inherited missing children / 13 of 24 originals covered**, with a
**779-step proof**. Eleven originals remain unknown. The union preserves both
exploratory routes (137 new patterns and ten new split identities) and occupies
**39,448,576 SQLite / 1,970,166 gzip bytes**. The checkpoint binds **298 sources**.
The parent preservation audit covers **3,338 artifacts / 56 manifests / 294 sources**.
The new manifest adds **40 artifacts**; the next audit inherits
**3,378 artifacts / 57 manifests**, plus the 298-source ledger.
Checkpoint SHA-256: `2f9d6443796a369afc18bba67a5bbd6da87ad7d66c1c1a48f1313ef89aa59fff`.
Report SHA-256: `52f260ff86b9b6d5944dd5785791b4f63adda7e30d1991247bcf61547996167a`.

## Previous investigation: reuse the covered branch and reduce complete audit work

[Checked canonical form in the cold auditor](canonical-cold-audit.md) closes case
**19**, raising coverage **11/24 -> 12/24** with **35 patterns / five pairs / ten
source assumptions / 135 probes**. Its 42-step proof uses six conditional nodes
at maximum depth three and 35 reductions. Seven steps and one split were already
stored. Only the contradiction terminal is shared within the proof; larger
nonterminal reuse remains unestablished. Conditional depth is not a fixed
backdoor-size claim.

Four alternating-order paired runs give complete audit **6.75146 -> 6.46583 s
(4.23%)** and whole stream **8.20199 -> 7.88948 s (3.81%)**. Both still perform
complete independent checking and identical acquisition. The optional canonical
precheck scans actual sources and falls back to old normalization, trusting no
parent validity flag. Earlier negative checker-index experiments remain intact.
Snapshot bytes match. **Mean RSS increases 589,824 bytes (0.153%)**; no memory or
persistent-storage saving is established. The full audit remains **82.0%** of
stream time; compression is **9.0%**, local expansion **3.0%**. Further audit
reuse needs explicit trust/invalidation and a matched complete-check control.

**Next discovery target:** case **6**, random 3-CNF, with a selected **36-variable /
148-clause / 444-literal / width-three** residual. All eight saved children exist.
The false child of pivot **13 is already covered**; its true sibling and the
other six children are not. Start by inspecting that sibling and preserving the
covered side. Historical enumeration cost ranks this target, not a new cost
bound. Continue testing whether conditional interactions expose larger shared
components rather than merely the universal contradiction terminal.

Restore `experiments/results/cnf-canonical-audit/checkpoint.json`: **1,981 patterns /
199 pairs / 17 inherited missing children / 12 of 24 originals covered**, with a
**706-step positive proof**. Twelve originals remain structurally unknown.
The union is **37,580,800 SQLite / 1,883,472 gzip bytes**. All **360 tests** pass;
all eight trial snapshots, the parent and union independently replay. Earlier
290 sources, 3,290 artifacts and all 64 manuscript proof blocks are preserved.
The new checkpoint binds **294 source files** and adds **48 manifested
artifacts**. The next preservation audit inherits **3,338 artifacts /
56 manifests**; see its manifest and validation.
Checkpoint SHA-256: `c18e567e7b3fc7ce177b9e456549e3dc2aebce07703309fabcb22944828e4082`.
Report SHA-256: `a122327ea37619f87bf15c6f7d4a839ab7f3ada7ba0d6f19526963baeb47aab0`.

## Previous investigation: remaining discovery and the final full audit

[Grouping complete audits](grouped-checkpoints.md) closes cases **23, 18 and 15**,
raising coverage **8/24 -> 11/24**. Both modes acquire **147 patterns / 21 pairs /
42 source assumptions / 707 probes**, and every positive query proof is checked
independently on its exact snapshot. The grouped mode completely audits history
once at group end; the control does so after every batch. All intermediate
snapshots are retained, but the first two grouped snapshots are not globally
certified during the stream. Unrelated corruption detection is delayed until
the final full audit; publication of a verified checkpoint still requires it.

Two reversed fresh-process repetitions give **24.13644 -> 11.65332 seconds
(51.72%)** for the three-query sequence. Acquisitions, proofs and all snapshot
bytes match. **Mean peak RSS rises 453.58 -> 488.51 MB (7.70%)**; preserve this
regression. The final database size and all three snapshots are unchanged.
Retrospective validation independently checks all twelve archives and their
positive proofs, outside the operational timing comparison.

**Discovery finding:** the connected case closes with no decomposition step,
using eight conditional nodes and 63 reductions to expose contradiction and a
five-variable 2-CNF leaf. The two random cases add Horn/zero-valid and zero/one-valid
leaves. Conditional depths are four, four and five, not fixed backdoor sizes.
None of the later proofs uses a newly acquired pattern from an earlier query in
the group. Larger shared components remain unobserved; the measured saving comes
from audit reuse. The canonical contradiction remains the only shared proof node.

**Largest remaining cost:** one full audit takes **6.94599 seconds (59.6%)** of the
grouped stream; compression adds **1.97996 seconds (17.0%)**. Investigate checked
reuse of an immutable parent plus verification of new records, with an explicit
trust boundary and full fallback. Do not trust a serialized validity flag.
Profile the RSS regression before claiming memory savings from larger groups.

**Next discovery target:** case **19**, a random 3-CNF whose selected residual has
**58 variables / 276 clauses / 841 literals / maximum width four**. All eight
children of its four saved pairs are present and uncovered. Continue the unchanged
policy from the new union; historical timing sets priority, not a new cost bound.
Cases 15, 16, 17, 18, 22 and 23 are now complete.

Restore `experiments/results/cnf-grouped-checkpoints/checkpoint.json` with the
existing bootstrap helper. It retains **1,946 patterns / 194 pairs / 17 inherited
missing children / 11/24 coverage**, with a **665-step positive proof** and **13
unknown originals**. The union occupies **36,884,480 SQLite / 1,834,327 gzip bytes**.
All **356 tests** pass. Every previous result, source and existing manuscript
proof block is preserved. Validation binds **290 sources** and adds **52 manifested
artifacts**; the next audit inherits **3,290 artifacts / 55 manifests**.
Checkpoint SHA-256: `7963a1e20851caedcd0d278d3a5f5ab56ea2855fdd5e5c2102a04df9544354e7`.
Report SHA-256: `f2958d258afd84ee0c1301bef5335851ee6dd1ff07d9ce969618eb22bcc7c034`.

## Previous investigation: connected mixtures and shared checkpoint checking

[Root-complete split checking](scoped-refinement.md) closes case 22 and raises
coverage **7/24 -> 8/24**, with **9 new patterns / 2 pairs / 4 source assumptions /
29 probes** in both modes. The optional scoped registry indexes every split but
checks semantic certificates only for sources reachable from the requested root.
It preserves all alternatives at those sources, full-database lookups and append
guards. Independent full cold checks remain mandatory at each archived batch.

Two reversed fresh-process repetitions give **12.59685 -> 6.94722 seconds (44.85%)**
whole-stream time. Startup falls **5.72447 -> 0.16200 seconds**; mean peak process
RSS falls **461.45 -> 360.73 MB (21.83%)**. Both histories, all acquisitions,
choices, proofs and archive bytes match. Persistent storage is unchanged. Live
startup checks **40 vs 1,790 pattern nodes / 4 vs 171 split certificates**; the
full audit still checks everything. This is a finite development comparison,
not a universal speedup or a bound independent of historical storage.

**Largest remaining cost:** full cold checking is **5.96027 seconds**, about **86%**
of the scoped stream; compression adds about 0.61 seconds. Investigate sharing a
guarded session and one complete checkpoint audit across several queries, while
retaining per-query results and checking every positive proof. Query scoping alone
does not eliminate full row maps, archive reads, identity scans or table guards.

**Next discovery target:** case **23**, a **connected binary mixture** with a
selected **59-variable / 255-clause / 767-literal / width-four** residual. Its four
saved pairs have all eight children present and uncovered. Transfer the unchanged
policy and investigate shared-variable interaction; do not repeat its initial
acquisition. Case 22's proof explicitly separates an easy 2-CNF component. It uses
23 old pattern steps and nine new ones; only the contradiction terminal is shared.
The three conditional levels are not a fixed three-variable backdoor.

Restore `experiments/results/cnf-scoped-refinement/checkpoint.json` through the
existing bootstrap helper. It preserves **1,799 patterns / 173 pairs / 17 inherited
missing children / 8/24 coverage**, with a **477-step positive proof** and **16
unknown originals**. The union occupies **34,148,352 SQLite / 1,652,138 gzip bytes**.
The new `next-discovery.json` binds case 23 using historical timing for priority.
Cases 16, 17 and 22 are complete. All **351 tests** and independent checks of the
parent, four trial archives and union pass. Previous artifacts, sources and all
64 existing manuscript proof blocks remain unchanged. Validation binds **286
sources** and adds **34 manifested artifacts**; the next audit inherits **3,238
artifacts / 54 manifests**. Checkpoint SHA-256:
`d4d3bbfd93c23199868bf8e28831f840cefb69a8606639f1c59b71d8da4496a2`.
Report SHA-256: `f11f0e5462ea831c3d3e23258966f75cbf235a57a6a9003d2942046528e4a24c`.

## Previous investigation: transfer across mixtures without scanning all history

[The unchanged nested policy closes case 17](case17-policy-transfer.md) in one
batch, raising current coverage **6/24 -> 7/24**. A matched history ablation
produces exactly the same **89 new patterns / 9 pairs / 18 source assumptions /
531 probes**, choices and target proof when the **547 patterns / 66 pairs**
acquired for case 16 are absent. None of those case-16 additions is in the new
proof. This is policy transfer on development data, without measured marginal
reuse of the case-16 records. Seven older pattern steps still contribute.

The proof has **96 unique steps: 10 conditional / 84 unary / 2 constant family
leaves**, with conditional depth six. Only the contradiction is shared, on ten
paths. Do not infer a fixed six-variable backdoor or broad nonterminal sharing.

**Largest measured cost:** full-history startup plus cold checking takes
**11.50553 s**, versus **0.62379 s** local expansion. Whole-stream means are
**12.86418 s retained / 8.59953 s before case 16**; mean peak RSS is **443.88 /
318.14 MB**. These two-repetition, fresh-process observations include complete
history work and different initial coverage (6/24 versus 5/24). Preserve both
histories; investigate a source-local checked view with exact global fallback
and complete relevant split routes, not deletion of earlier results. The old
read-through helper does not yet handle the new split table/registry scans.

**Next discovery target:** case **22**, a **disjoint binary mixture** with a
selected **48-variable / 204-clause / 612-literal** residual. All eight children
of its four saved pairs are present; one is covered, but no full pair is covered.
Reuse that work. Transfer the unchanged
policy to it; charge discovery and distinguish easy-component reuse from closure
of the hard residual. The bound target in `cnf-case17-transfer/next-discovery.json`
uses historical timing for prioritization, not a new measurement on the union.
Cases 16 and 17 are complete and must not be restarted as unknown.

Restore `experiments/results/cnf-case17-transfer/checkpoint.json` through the
existing bootstrap restoration helper. It preserves **1,790 patterns / 171 pairs /
17 inherited missing children / 7/24 coverage**, with a **446-step positive proof**
and **17 unknown originals**. The union occupies **33,972,224 SQLite / 1,640,046 gzip
bytes**. All **345 tests** pass; both parents, all four trial archives and the union
are independently checked without acquisition. All previous source files,
artifacts and manuscript proof blocks remain unchanged.

Checkpoint SHA-256: `3d52f04bd98db9f0cc72a4df33afb940953cd75de2e139ee49910d283a61cbcc`.
Report SHA-256: `8ce007b096aacd0fe9b24a0d15bda17c23c358d7302172b737b8a7bc289da9c0`.
Validation binds **282 sources** and adds **33 manifested artifacts**, preserving
all previous 280 sources and 3,171 artifacts. The next audit inherits **3,204
artifacts / 53 manifests**; include this manifest as well as its parents.

## Previous investigation: transfer deeper conditional discovery to case 17

[Nested conditioning](nested-conditioning-discovery.md) closes case 16 and raises
the current corpus to **6/24** covered originals. The matched flat control tries
all **55 remaining source pivots**: together with the four saved choices, all
59 pairs have acquired children but none closes under that flat history and
recognizer. Nested refinement adds **11 pairs** and reuses interrupted work across
three bounded batches. This is a finite discovery gain, not a SAT lower bound.

The checked original proof contains **12 conditional nodes / maximum conditional
depth 5 / 265 unary reductions / 9 distinct family leaves**. The variables are
branch-dependent and use changing coordinates; do not call this a fixed
five-variable backdoor. Initially the eight reduced frontier keys are distinct.
Only the canonical contradiction is shared within the final proof, on five paths;
there is no observed nonterminal sharing. The old one-level failure was a limit
of structural exposure, not evidence that no deeper recognized plan exists.

**Next discovery target:** case **17**, the next largest previously measured
unresolved query, with a **60-variable / 255-clause / 765-literal** selected
component. Continue from the new union and test transfer of the adaptive policy,
retaining its failures and charging deeper preparation. Case 22 is another
uncapped control. Case 16 is complete and must not be restarted as uncovered.
The exact next source and its four saved pairs are bound in
`experiments/results/cnf-nested-refinement/next-discovery.json`.

Nested refinement uses **2,403 probes / 275 new patterns / 22 source assumptions**;
flat acquisition uses **2,291 / 272 / 110**. Thus the success is not a reduction in
every resource. Mean local expansion is **1.40774 vs 3.54080 s**, with setup, every
cold archive, compression and supplemental lifecycle measurements reported
separately. Two nested batches are capped; the final saved-pair resumption adds
27 patterns and 215 probes with no fresh source assumption. Reducing the 265
unary proof steps is a supporting storage/checking opportunity, not yet a saving.

Restore `experiments/results/cnf-nested-refinement/checkpoint.json` through
`experiments.validate_cnf_bootstrap.restore_checkpoint`. It preserves **1,701
patterns / 162 pairs / 17 inherited missing children**, with a **352-step positive
proof** and **18 unknown originals**. There is no overlap between the 547 new rows
of the two workflows, so both the successful and unsuccessful acquisitions are
retained. The union occupies **32,346,112 SQLite / 1,537,733 gzip bytes**.

All **345 tests** pass, and every primary batch archive and the combined union
replay without new acquisition. The prior 274 sources, 3,097 artifacts and 64
manuscript proof blocks remain unchanged. Checkpoint SHA-256: `a362b51025c1c5d386604893de66a8c940902f69b655e484f54fec6115fe4785`.
Final validation binds **280 sources** and adds **74 manifested artifacts**;
the next audit inherits **3,171 artifacts / 52 manifests**.

## Previous investigation: deeper interaction in an uncapped 59-variable residual

[Incremental split checking](incremental-split-checking.md) removes the previous
quadratic route-verification loop. On the same 24-input enumeration stream, mean
query time falls **7.41290 -> 4.26395 seconds (42.5%)** over three paired repetitions.
Split checks fall **3,913 -> 258**, with identical variables, admissions, probes,
pending flags, archive bytes and positive proofs. Coverage remains **5/24**.
The live registry adds metadata; no memory or persistent-space reduction is
claimed. Independent cold proof checking remains unchanged.

**Next discovery target:** case **16** is the largest mean unresolved query at
**0.31922 s / 205 probes / 27 admissions**. It is **not capped**. Its selected
component has **59 variables, 245 clauses and 743 literals**. The four saved
pivots (7, 37, 5 and 51) have all eight child records present; all remain open even
under the complete 1,154-pattern union. Follow their existing reduction edges and
investigate deeper conditioning or interaction summaries. Repeating these four
acquisitions or merely increasing the same uncapped allowance cannot improve this
fixed policy. Cases 17 and 22 provide adjacent, also-uncapped controls.

The exact source and branches are bound in
`experiments/results/cnf-split-registry/next-discovery.json`. Restore the unchanged
parent `cnf-bootstrap-conditioning/checkpoint.json` through its existing helper,
preserving all **1,154 patterns / 96 pairs / 17 missing children**. The smaller
enumeration-only histories contain 643 patterns, 86 pairs and one missing child;
do not substitute them for the richer union when continuing discovery.

**Remaining runtime cost:** fresh cofactor acquisition and recognition/checking
now dominate the query profile. Route maintenance takes only **0.09428 s** of
the **4.26395 s** stream. Cold replay still costs about **2.1 s**, and complete
row audits and table-count guards remain charged. The registry is optional and
requires exclusive append-only inventory ownership; no general time bound follows.

All **341 tests** and nine cold archives pass; every previously bound source,
artifact and the 64 manuscript proof blocks remain unchanged. The previous
42-input and 83-source completions are still complete. Report SHA-256: `1bc0bd946f4b38f9f70144d3dd9f537913c1d93217c625781de4e1c45ae3c5d4`.
Validation binds **274 source files** and adds **30 manifested artifacts**;
the next preservation audit inherits **3,097 artifacts / 51 manifests**.

## Previous investigation: reuse checked conditioning records incrementally

[Broader source conditioning](bootstrap-conditioning.md) removes the previous
binary-clause prerequisite: all **24/24** selected residuals have candidates.
Both unit-closed branches are checked and persisted before child acquisition.
On the same frozen inputs, trying up to four candidates covers **5/24**, versus
**4/24** for ordinary depth-one conditioning, **2/24** for first selection and
**2/24** for smaller-cofactor selection. This is an adaptive workflow comparison:
ordinary restarts the whole original, while external routes reuse depth-zero
ancestors and expand one component. Forty recognition admissions and up to eight
separately charged source assumptions are not an equal total-work allowance.

**Highest credible cost saving:** replace repeated complete split-route catalog
construction with an incremental checked registry. Enumeration uses **3,946 vs
5,699 probes** and **558 vs 737 new patterns**, yet queries take **7.41975 vs
6.13657 seconds**. A separate instrumented run reproduces the same graph and
counts **3,913 split verifications for 86 records** during queries. Rechecking
all earlier pairs after each insertion explains the count exactly:
`86*87/2 + 2*86 = 3913`. Bind cached evidence to the exact source, full policy and
immutable record contents; keep pending child obligations in a reverse index.
Activate routes only when both children exist, propagate coverage correctly, and
retain independent cold checking. No speedup is established before measurement.

**Next discovery gap:** nineteen originals remain outside this finite coverage.
After removing the verification overhead, investigate deeper interactions,
alternative components and selectors for propagation cascades. Four choices on
one component are not a uniformly efficient partition of arbitrary SAT.

Restore `experiments/results/cnf-bootstrap-conditioning/checkpoint.json` using
`experiments.validate_cnf_bootstrap.restore_checkpoint`. The union retains
**1,154 patterns, 96 source pairs, 17 missing children and a 68-step positive
proof**, with **5/24** coverage. It occupies **21,790,720 SQLite / 1,055,418 gzip
bytes**; pooling all alternatives adds no further covered original. The earlier
42-input and 83-source checkpoints remain complete and unchanged. All **335
tests** and eleven cold archives pass. The initial validator's seed/union path
collision was repaired with exact original seed hashes and retained recovery
evidence; use only the final checkpoint.

Checkpoint SHA-256: `f6754b02a68246dfe2a1bce79920a4e35b68270fe64d678986f93a552dec7ec7`.
Validation binds **269 source files** and adds **44 manifested artifacts**;
the next preservation audit inherits **3,067 artifacts / 50 manifests**.

## Previous investigation: acquiring useful candidates before ranking

[The new-input lookahead study](lookahead-bank.md) freezes 24 random 3-CNF and
binary-mixture inputs. Under **depth-zero preparation, 22/24 selected unresolved
components have zero binary clauses and no saved source-assumption pairs**. The
binary-frequency selector therefore offers nothing to rank on those inputs.
This is a limitation of this prepared-pair expansion experiment, not of ordinary
positive-depth conditioning or the complete solver. No original is classified
as UNSAT by a missed pattern or empty candidate pool.

**Highest discovery target:** compare charged ordinary conditioning with broader
source-pair acquisition to create a useful common candidate pool, then evaluate
selection. Use the existing shortest-clause ranking as a baseline; retain and
check both assumptions and charge preparation. More width in the same empty
binary-only pool cannot help. Keep the frozen depth-zero result as a negative
control and measure any positive-depth preparation separately.

**Implemented reuse, failed score:** an optional exact source/policy probe bank
avoids **36 repeated probes (142 -> 106)** on the two eligible connected mixtures.
The lookahead score picks the same pairs as size ranking, which needs only **72
probes**. All three selected-pattern graphs are identical, with zero new original
coverage. Lookahead thus adds 34 probes, 8 bank rows / 36,684 logical bytes, and
73,728 SQLite bytes over size selection. Mean query times are **0.12251 s size /
0.15344 s lookahead-reuse**; setup adds about 0.26 s. The bank remains experimental.
All 331 tests and nine cold archive checks pass. No default inference source is
changed, and no general efficiency or compact-state claim is justified.

The new seed is `experiments/results/cnf-lookahead-bank/seed.json`, with 85
patterns and 24 explicit unknown coverage cases. Its sources are distinct from
the bound historical originals; no residual-wide novelty claim is made. Preserve
all eight arm archives, including failures. The previous 42-input checkpoint
`cnf-transfer-split/checkpoint.json` remains complete with null selection, as does
the older 83-source checkpoint. These are separate corpora and policies.

Report SHA-256: `96665203ed1328cada324b2f56251c57584644049b747d6d3a190b45d937dfb1`.
Validation binds **175 source files** and adds **27 manifested artifacts**;
the next preservation audit inherits **3,023 artifacts / 49 manifests**.

## Previous investigation: predicting useful conditioning cascades

[The saved-pair comparison](transfer-split-selection.md) completes **42/42** inputs
in the new transfer stream. On the connected 38-variable residual, variable 14
closes both children with **13 new records / 30 fresh probes**. Seven probe
reductions on one branch expose two independent 2-CNF components; three on the
other reach a contradiction. The original root follows through its checked
ancestors. This is finite adaptive coverage, not an arbitrary-SAT result.

**Largest discovery gap:** the current smaller-cofactor ranking chooses variable
6, which uses 45 probes and remains open. The winning variable 14 has more raw
cofactor literals (863 versus 829); variable 27 uses fewer probes but also remains
open. All four pairs were compared from the same history under a complete
32-state allowance, in two orders. Discovery of the winner costs **38 admissions
and 188 probes per four-pair comparison**, not just its 30 probes. Investigate
cheap indicators or reusable bounded lookahead for propagation cascades and
component exposure on new frozen inputs. Compare with size ranking and exhaustive
candidate enumeration; no universal selector or minimum-cost guarantee is known.

**Supporting runtime gap:** full cold checking costs about **1.12 s** before the
winning **0.032 s** local expansion. On the initial pair, retained history saves
only one terminal record and no probes over a source-row-only control. Selective
checked startup and reusable lookahead evidence are better-supported targets than
assuming the entire history is beneficial to every query.

Restore `experiments/results/cnf-transfer-split/checkpoint.json` with
`experiments.validate_cnf_transfer_split.restore_checkpoint`. The union preserves
**443 old + 34 new = 477 patterns**, all four alternatives, 33 early-family
certificates and a 133-step positive proof for the other nine roots. It occupies
**7,688,192 SQLite / 412,774 gzip bytes**. **There is no pending original in this
42-input stream**; `next_selection` is null. Keep the failed variable-6/27/37 trials
as selection counterexamples, without restarting them as uncovered originals.

All **327 tests** and thirteen cold archive checks pass. Prior artifacts and the
old 83-source checkpoint remain intact. The 64 manuscript proof blocks are
unchanged; no new Lean theorem or SAT/UNSAT answer is claimed.

Checkpoint SHA-256: `b59eacad9247879b97b1baa5bc729d3608c72f492896cebc43f4091f06adc5e3`.
Validation binds **171 source files** and adds **46 manifested artifacts**.
The next preservation audit inherits **2,996 artifacts / 48 manifests**.

## Previous investigation: the connected 38-variable interaction

[Complete admission accounting](complete-admission-frontier.md) now gates both
recognition entrances, including transient fused restrictions. At allowance 32,
the corrected gate avoids **40 probes (503 -> 463)** on the same 42-input stream
while producing an **identical 107-record graph** and **41/42 coverage**. All
323 tests and sixteen cold archive checks pass. This is avoided interrupted work;
there is no observed storage reduction or general runtime guarantee.

**Highest structural target:** a generous 4096-state allowance returns normally
but leaves case 41 unresolved. Its selected frontier is a **connected 38-variable,
165-clause, 502-literal residual**, at conditioning depth zero. The original is
48/204/612. Current simplification, bounded probing and projection do not close
it. Inspect its exact interaction and conditioning/interface alternatives; merely
increasing this policy's acquisition allowance has already failed to close it.
Restore `experiments/results/cnf-complete-admission/complete4096-0/report.json` and
its archive; bind the residual through `selected-frontier.json`, preserving the
original source context and all alternatives. The 443-record full-stream history
contains the completed current-policy search, including unsuccessful alternatives.

**Next reuse target:** four cold-open 32-state resumptions preserve 107 previous
rows and add 79, but repeat **33 of 128 admissions** and remain capped. Empty-history
continuation repeats 39. The generous last query also acquires **34 transient
profiles** that are not stored. Investigate source/policy-bound checked profile
persistence for interrupted ancestors and transient restrictions, charging cold
verification and space before claiming savings. Prepared continuation is slightly
slower in this experiment despite fewer probes; retain that negative result.

Historical artifacts and inference sources remain unchanged. The new cap limits
distinct acquisition states, not verification, repeated visits, normalization or
elapsed time. The old 83-source checkpoint remains complete. This is finite
structural coverage, not a SAT/UNSAT verdict or an arbitrary-SAT efficiency bound.

Report SHA-256: `3445e004fbcf96b44babb2754dc23ee5351db0ac6378f346c72adc3c55dd29b9`.
The validation binds **166 source files** and adds **44 manifested artifacts**;
the next preservation audit inherits **2,950 artifacts / 47 manifests**.

## Previous investigation: unresolved new-input interaction and complete accounting

[The transfer controls](subsumption-transfer-controls.md) expose a confound: the
shared **18/22/48** node reduces to **16/18/36 2-CNF**. Twelve new variants reuse its
proof, but a supplemental early-family check handles **33/42 inputs** without a
prepared template. It reduces fresh probes **1,022 -> 503**, actual new patterns
**197 -> 107**, and working SQLite bytes **2,510,848 -> 1,466,368**. Mean preparation
plus queries is **0.49636 -> 0.38107 s** in two repetitions. This is conditional
family exposure, not evidence for reuse of a reduced core outside known families.

**Next dominant target:** frozen input **41**, **48 variables / 204 clauses / 612
literals**, remains unknown under every arm and costs 272 probe attempts. The six
random inputs consume about **0.315 of 0.378 s** in the improved stream. Its source
is in `experiments/results/cnf-subsumption-transfer/protocol.json`, with normalized
fingerprint `511dd0f7c367b2af3e9f447f8411ef8ed10e0265dfcde5666b7d35f0b4aa1a22`.
Inspect that stored frontier and its interactions. Further tuning of the already
easy motif is unlikely to address the largest cost.

**Resource-accounting correction:** the inherited 32-state cap limits calls
through `_discover`, while fused conditioning can acquire through `_discover_profile`.
The independent initial rerun records eighteen additional nodes outside the ledger
in every arm. Cover all acquisition entrances before asserting a global state cap;
keep recorded admissions, actual stored patterns and unfinished work separate.
All completed proofs still check. The old archived studies remain unchanged.

The original and supplemental studies preserve all 42 inputs, misses and archives,
including the generator preflight failure and the loss of incidental warm reuse.
All **318 tests** and twelve cold archive replays pass. The family control was
chosen after inspecting the first result and is labelled accordingly. Next reuse
tests should use cores outside existing terminal families and compare against
cheap family recognition. The completed case1196 checkpoint retains its null
selection; this new stream does not replace it.

Initial report SHA-256:
`1c921283eb5893e801eb945704a9c7fcb114d2692516790b62e86417fa757c3e`.
Supplemental report SHA-256:
`f35001bc53774ba8ba53b719885083ef2238f21245340126b2a047514859496e`.
Validation binds **162 source files** and adds **55 manifested artifacts**, including
the preflight failure. The next audit inherits **2,906 artifacts / 46 manifests**.

## Previous investigation: transfer of larger shared components

[Full historical corpus replay](full-corpus-coverage.md) now checks **1,497/1,497
inputs**, including **985/985 non-tiny cases**, with **zero new acquisitions**.
The union explicitly binds 1,414 sources to the original retained policy and 83
to the expanded policy. This is a complete historical regression, not a holdout
or an efficient classification of arbitrary CNFs.

A self-contained positive bundle reduces mean fresh-process replay from
**46.48527 s to 11.22907 s** in two reversed-order repetitions. It occupies
**11,271,594 compressed bytes** and reconstructs **146,747,392 SQLite bytes**.
Preparation, historical acquisition and producer costs remain charged. The
bundle adds storage and cannot replace the full discovery history.

**Highest-value next test:** evaluate transfer from larger shared edit-family
components to unseen inputs under a frozen policy and budget. The old successful
set has **67 shared nonterminal proof steps** after 301 duplicate canonical roots
are collapsed. The largest source has **18/22/48** variables/clauses/literals,
shared by cases **1454, 1457, 1460**. But across the old-success/new-coverage proof
boundary, exact overlap is still only **20 family steps**, at most three variables.
Use the larger components as concrete candidates; compare prepared and empty
history on fresh edits, connected mixtures and invalidating changes, charging
recognition, forcing evidence, checking and persistence. Graph sharing alone does
not establish avoided acquisition.

All **306 tests** and four fresh-process replays pass. Continue expansion from the
unchanged `cnf-case1196-discovery` checkpoint; its next source is null. The new
`cnf-coverage-union` artifact is positive-proof-only. Preserve the completed
83-source state and evidence **(1,42,156,98,1)** with two bridges.

Union report SHA-256:
`d2bbb9591401978393da509cb2309312aa71b0927699cc221a3cec4c5340df30`.
Its validation binds **155 source files** and adds **14 manifested artifacts**.
The next preservation audit inherits **2,851 artifacts across 45 manifests**.

## Previous investigation: transfer beyond the completed development subset

[The final six-batch sequence](case1196-completion.md) raises structural coverage
**78/83 -> 83/83** on the retained development misses, with **144 new records /
147 admissions**. All five remaining originals are checked: three SAT and two UNSAT.
The three interrupted inputs are completed. Four terminals expose Horn, 2-CNF and
dual-Horn overlaps; exhaustive bounded checks validate their classifications and
both polarity maps. This completes a finite development subset, not arbitrary SAT.

The full selected proof has **4,822 steps**, of which only **14** are shared across
originals. All shared CNFs have at most **two variables**; the four shared
nonterminal steps directly reference family leaves. There are **169 repeated
per-root step visits**, not a measured runtime saving. This locates the remaining
structural gap more precisely: discover and certify reusable larger cores or
boundary descriptions, beyond these small resolved ends of the proof.

**There is no pending source.** Restore
`experiments/results/cnf-case1196-discovery/report.json` using
`experiments.continue_cnf_case1196_discovery.restore_checkpoint` as the prepared
state. Its `next_selection.source` is null; the initial case 1196 is complete.
Preserve evidence **(1,42,156,98,1)** and two bridges.

**Next priority:** test transfer to new unlabelled inputs under a frozen policy and
budget. As preparation, bind the preserved historical successful plans and the
new coverage in a combined query and replay the full historical corpus without
fresh acquisition. The 83 formulas exactly match the old retained-policy misses
among 1,497 inputs, but no new full-corpus replay or runtime has yet been measured.
The old **902/985 non-tiny** result remains separate. Then compare prepared versus
empty history on matched fresh sizes, mixtures and edits, charging forcing-trace
acquisition as well as local expansion. Seek certified nonterminal or boundary
sharing; matching family names or finite completion do not establish it.

Mean six-batch sequence time is **77.64131 seconds**, including
**64.54345 seconds** startup and **3.20071 seconds** local
expansion. This longer allowance is not a speed comparison with four-batch runs.
History adds **2,019,328 bytes**; reference evidence adds **15,405,056 bytes**.

Report SHA-256: `f8c8081bb0c345a3ed45c566e55b1641bb9ca436064c30ad7afd5a434cb1bb66`.
The new `validation.json` and `manifest.json` inherit **43 prior manifests /
2,650 prior artifacts / 145 prior source fingerprints**. All 299 tests and
independent reconstruction pass.
The new validation binds **151 source files** and the manifest adds **187 artifacts**:
inherit **2,837 artifacts across 44 manifests** in the next preservation audit.

## Previous investigation: finish the five remaining originals

[Resuming the retained branches](case1063-discovery.md) raises structural coverage
**75/83 -> 78/83**, completing **1063, 1371 and 1158**. All three originals are SAT;
1158's selected residual is UNSAT, so conditioning ancestry remains essential.
Two independent four-batch runs store **54 records** on **63 admissions / 54 distinct
inputs**. Case 1063 completes with three new records after fifty had been stored.
New terminals include overlapping Horn/2-CNF/zero-valid and Horn/zero-valid cases.
Sixteen exact prefix records are reused within case 1063; two inherited unresolved
records now participate in the complete coverage proof without payload changes.
Across distinct originals, measured prefix overlap reaches only the contradiction terminal.

**Next:** case **1196 / index 36**, **43/181/549**, **no pending split**. Resume
`next_selection` from `experiments/results/cnf-case1063-discovery/report.json`
using `experiments.continue_cnf_case1063_discovery.restore_checkpoint`. The initial
case 1063 source is already complete. Preserve evidence **(1,42,156,82,1)** and
two bridges; all admitted inputs are stored.

Mean sequence time is **71.68154 seconds**, including
**64.51870 seconds** startup and **1.01341 seconds** local
expansion. History adds **733,184 bytes**, separate reference evidence
**3,682,304 bytes**. Retain one checked session and seek certified sharing beyond
contradiction terminals. Five development originals remain uncovered; even full
coverage of this corpus would not establish an efficient arbitrary-SAT partition.
New unlabelled and adversarial evaluation remains necessary.

Report SHA-256: `cb6211074e9cda532b0bf8323df0931bb2ae3d4d0cbdc91ebab33854ee986be5`.
The new `validation.json` and `manifest.json` inherit **42 prior manifests /
2,526 prior artifacts / 140 prior source fingerprints**. All 299 tests and
independent reconstruction pass.
The new validation binds **145 source files** and the manifest adds **124 artifacts**:
inherit **2,650 artifacts across 43 manifests** in the next preservation audit.

## Previous investigation: preserve the pending expansion frontier

[Mixed-family discovery](case1121-discovery.md) raises coverage **73/83 -> 75/83**,
closing **1121 (SAT)** and **1336 (UNSAT)**. Two independent four-batch sequences
store **67 records** and charge **81 entries / 67 distinct inputs**. A checked
affine projection reduces **14/16/34 -> 13/14/30**; an exhaustive bounded audit
confirms its exact boundary models. This is an application of the existing rule.

**Next:** case **1063 / index 15**, pending **22/89/309**. All admitted inputs
are stored, but the split's second branch has admitted zero inputs and remains
pending. Preserve that separate frontier. Resume `next_selection` plus pending
split from `experiments/results/cnf-case1121-discovery/report.json` using
`experiments.continue_cnf_case1121_discovery.restore_checkpoint`; the initial case
1121 source is already complete. Empty selector indices stay empty; checked
dependency ancestry supplies the original scope. Evidence **(1,42,156,78,1)** and
two bridges remain required.

Mean sequence time is **72.02025 seconds**, including
**64.41599 seconds** startup and **1.23698 seconds** local
expansion. History adds **913,408 bytes**; reference evidence adds **5,423,104 bytes**.
Reuse a checked session; investigate actual shared nonterminal/boundary identities
across originals. A repeated method or matching shape is not reusable evidence.
Eight originals remain uncovered; no arbitrary-SAT bound follows.

Report SHA-256: `0282e3d40a20a20701c24503b7cd7608655806dace6e937e47082b1e30702790`.
The new `validation.json` and `manifest.json` are the preservation anchors. They
inherit **41 prior manifests / 2,400 prior artifacts / 135 prior source fingerprints**.
The new validation binds **140 source files**; its manifest adds **126 artifacts**
(2,526 artifacts across 42 manifests for the next preservation audit).
All 299 tests and the independent cold reconstruction pass.

## Previous investigation: finish mixed reduction obligations

[Completing the pending mixed reduction chains](pending-discovery-closure.md)
closes **case 1062**, raising structural coverage **72/83 -> 73/83**. Two independent
four-batch runs store the same **68 records**: 23 probes, 22 eliminations, 13 binary-path
reductions, three polarity transformations, five family terminals and two unresolved
intermediate records. They charge **84 admission entries / 68 distinct inputs**;
16 entries repeat interrupted work inside this sequence. All **eight earlier
interrupted inputs** and all newly interrupted inputs are now stored.

Three polarity transformations expose Horn terminals without reducing variables,
clauses or literals: **8/10/23**, **14/17/43**, **6/6/16**. A separate **9/18/49**
terminal is all-zero satisfiable but neither Horn nor 2-CNF. These are applications
of existing checked rules, not new tractable classes. The first 19-variable branch
closes before another 36-variable branch is selected; selected size alone is not
monotone progress. Original coverage requires all outstanding structural premises.
The original and all four touched split sources are **SAT**; classification coverage
is separate from SAT decision.

Mean complete sequence time is **70.46120 seconds**, including
**63.74848 seconds** startup and **0.84877 seconds** local
expansion. Checked materialized parent restoration adds **8.70349 seconds**.
History grows **843,776 bytes** to **782,450,688 bytes /
42,611 patterns**; reference evidence grows **5,488 -> 5,612 nodes**. Peak RAM is
unmeasured. Repetition establishes reproducibility, not a matched speedup.

**Next priority:** **case 1121 / index 23**, **41/174/513**, no pending split.
Resume **`experiments/results/cnf-pending-discovery/report.json`** with
**`experiments.continue_cnf_pending_discovery.restore_checkpoint`**. Use
**`next_selection`**, not the completed initial 19-variable source. Preserve evidence
**(1,42,156,72,1)** and **two bridges**. Its default restorer uses the existing checked
materialization of its parent and then applies the new delta; independent audit
uses the original reconstruction chain with that cache disabled.

Touched prefixes reuse **two probe records and one contradiction terminal** from
the preceding case-1062 prefixes. The intersections with earlier cases 1195 and
1406 contain only that terminal. This supports reuse within a resumed original,
without establishing shared nonterminal representations between different inputs.
Across the six case-1062 batches in both checkpoints, **148 entries / 121 distinct
inputs** expose **27 repeated admissions**. All 121 records are now stored; preserving
unfinished control frames remains a possible way to avoid re-entry, with runtime
benefit still unmeasured. Ten originals remain uncovered. Continue discovery in a retained
session and measure actual shared identities or certified boundary descriptions.
No compact closure or uniformly polynomial arbitrary-SAT acquisition bound follows.

The new acquisition report SHA-256 is
`2b552019b9eaba71a058d7d6a1dc1a28817aa6a6a40d18a16a18b34fb56c2c00`.
For the next preservation audit, inherit
`experiments/results/cnf-pending-discovery/validation.json` and its `manifest.json`:
**135 source fingerprints**, **40 older manifests / 2,277 older artifacts**, plus
this result's **123 artifacts**. All 299 tests pass; independent replay checks
both repetitions, every prefix, ten saved global queries and 5,612 reference nodes.

## Previous investigation: reuse the checked materialized history

[Materializing a checked checkpoint](materialized-checkpoint-reuse.md) reduces
measured reconstruction **155.45916 -> 9.94660 seconds**.
Including a fresh complete catalog and global query, mean startup falls
**220.33037 -> 74.76157 seconds (66.07%)**.
Two reversed-order repetitions reconstruct byte-identical databases, retain all
five evidence groups and two bridges, and select the same pending split.
This is a checkpoint-reuse result; structural coverage remains **72/83** and no
new patterns or reference proofs are acquired.

The optional compressed snapshot adds **87,337,082 bytes** of local disk storage.
Publication from an already checked history costs **7.88791 seconds**; a
separate authoritative reconstruction costs **150.88545 seconds**.
Both are charged. The fast path checks the complete database byte identity
before opening SQLite, all logical table digests, code/policy/parent bindings,
all sidecar bytes, bridges and the positive coverage proof. Complete catalog and
negative-frontier checking remain separate, paid startup work. A hash is useful
only relative to the descriptor bound by the reviewed experiment report.

**Next priority:** use the optional restorer in
`experiments.cnf_materialized_resume.restore_checkpoint` with
`experiments/results/cnf-materialized-checkpoint/report.json`, or the unchanged
`continue_cnf_retained_discovery.restore_checkpoint` with the acquisition report.
The final entry point additionally checks all **125 historical source fingerprints**;
this separately measured guard costs **0.01286 seconds**. All **299 tests** pass.
Both return the same acquisition state. Resume its **`next_selection` plus
pending split at 19/77/261**, case **1062 / index 14**, whose selector original-index
list remains empty. Preserve evidence **(1,42,156,69,1)**, **two bridges** and the
**eight interrupted input identities** in the acquisition artifacts. Eleven
originals remain structurally uncovered. With reconstruction reduced, complete
startup checking (64.49429 seconds) remains the largest repeated
cost; keep one checked session across further discovery batches. Investigate
shared nonterminal or boundary descriptions in the pending mixed reductions.
No compact closure or uniformly polynomial acquisition bound is established.

For the next preservation audit, inherit
`experiments/results/cnf-materialized-checkpoint/validation.json` and its
`manifest.json`: **131 source fingerprints**, **39 older manifests / 2,251 older
artifacts**, plus this result's **26 artifacts**. The acquisition checkpoint itself
remains `cnf-retained-discovery`; use `cnf_materialized_resume` for the complete
historical source guard, rather than the lower-level benchmark loader.

## Previous investigation: retained discovery across original scopes

[Discovery across retained original scopes](retained-discovery-sequence.md)
raises structural coverage **70/83 -> 72/83**, covering **cases 1406 and 1195**
before continuing into **case 1062**. Two independent four-batch runs store the
same **63 records**: 19 probe reductions, 27 eliminations, 13 binary-path
reductions, one family terminal and three unresolved records. They charge **74
admission entries / 71 distinct inputs**; three entries repeat interrupted work,
and eight inputs still have no stored record.

The first two selected residuals are UNSAT, while their original formulas are
SAT. Their checked paths include earlier conditioning, so local refutation does
not transfer SAT truth to the original. A later **4/5/14** terminal is both
zero-valid and one-valid, but neither Horn nor 2-CNF. It does not close case 1062's
remaining branches. Classification coverage and SAT decision remain distinct.

Mean four-batch sequence time is **73.47861 seconds**, including **66.09003
seconds** initial catalog/global checking, **4.17511 seconds** workers and
**1.02047 seconds** local expansion within those workers. The shared parent
restore costs another **145.39246 seconds**. One paid startup now serves all four
batches; no matched fresh-per-batch comparison or universal speedup is claimed.
History grows **856,064 bytes** to **781,606,912 bytes / 42,543 patterns**.
Reference evidence grows **5,182 -> 5,488 nodes**; peak RAM remains unmeasured.

**Next priority:** resume the pending split at **19/77/261**, within **case 1062,
index 14**. The selector's original-index list is empty for this retained work;
independent dependency-path checking supplies the scope. Resume
**`cnf-retained-discovery/report.json`** with
**`continue_cnf_retained_discovery.restore_checkpoint`**, report SHA-256
`0d59f8bb3018c78b5da947a31d1a0d492103c15968df7d706b7ad1910b038f84`.
Use **`next_selection` and its pending split**, not the initial source bound to
case 1406. Preserve evidence **(1, 42, 156, 69, 1)** and **two bridges**.

The touched prefixes have **75 occurrences / 64 distinct records**. Within
these prefixes across three original scopes, only the inherited contradiction terminal is shared;
**none of the 63 new records is shared across scopes**. This limits the current
cross-input reuse claim. Eleven originals remain uncovered. Continue the mixed reduction chains and
measure whether any nonterminal identities or exact boundary summaries can be
shared; matching reduction names alone is not such reuse. Keep unsuccessful
choices and eight interrupted input identities. Cold reconstruction and checking
remain the largest costs, and support further guarded reuse or a verified
materialized checkpoint. No compact closure or polynomial acquisition bound for
arbitrary SAT follows from these observations.

## Previous investigation: conditional refutation and shared terminals

[Conditional refutation with a shared terminal](conditional-refutation-reuse.md)
closes **case 1227**, raising structural coverage **69/83 -> 70/83**. A saved
split exposes two chains of three and two new probe reductions. Both reach the
same existing contradiction terminal. Two independent runs store the same
**five new records** in one advance, with no interrupted admissions. This is
exact terminal reuse and a new covered original, not a new tractable SAT class.

Mean local expansion costs **0.15935 seconds**, the complete worker **1.18892
seconds**, and the full sequence **68.83255 seconds**. Initial construction,
global checking and serialization still cost **66.68418 seconds**; the separately
charged parent restore is **140.08953 seconds**. These repeated development runs
do not establish a speedup against another solver. Structural history grows
**73,728 bytes** to **780,750,848 bytes / 42,480 patterns**. Reference evidence
grows **4,802 -> 5,182 nodes**, adding **3,702,784 SQLite bytes**; that validation
cost remains separate from the structural delta. Peak RAM is unmeasured.

**Next discovery priority:** **case 1406, index 64**, **40/168/505**, no pending
split. Resume **`cnf-case1227/report.json`** with
**`continue_cnf_case1227.restore_checkpoint`**, report SHA-256
`240f8151528c19ef69cac3b958abfc489710ffa1961944799d957545ff10f722`.
Use **`next_selection`**, not the completed `source`. Preserve evidence
**(1, 42, 156, 64, 1)** and **two bridges**. Thirteen originals remain unresolved.

Cold checking remains the dominant measured cost. Continue discovery through
retained sessions where possible; extend checked replay only with its exact
source, policy and immutable-dependency guards. Similar reduction chains do not
supply proof transport between different CNFs, and a short refutation on this
case supplies no uniform acquisition bound for arbitrary SAT.

## Previous investigation: retain checked evidence through replay

[Checked checkpoint replay](checked-checkpoint-replay.md) removes repeated node
verification across the latest five append checkpoints and their startup query.
Two reversed-order runs reduce **replay plus startup 94.29444 -> 87.70659 seconds
(6.99%)**. Suffix replay falls **28.92930 -> 24.22978 seconds (16.24%)**; startup
falls **65.36514 -> 63.47681 seconds (2.89%)**. Node verifications fall
**28,059 -> 23,320**, avoiding **4,739 repeats (16.89%)**. Both arms keep full
archive/source identity checks, ten full table-digest scans, all delta/positive
checks and the complete global query. These are development-history observations.

The live verifier carries exact checked immutable dependencies through guarded,
conflict-checked appends. Failed appends roll back and invalidate it. External
changes, unexplained own-connection writes and policy/schema changes reject reuse;
exclusive file/connection ownership and immutable Python cache objects remain
requirements. No trust cache is persisted. Positive coverage does not establish
complete negative frontier information, so startup still builds and queries the
complete catalog. The fresh control uses the same merge guards and discards
verifiers between phases; the independent audit uses the frozen old restorers.

There are **no new pattern rows or coverage gains** in this replay experiment.
History remains **780,677,120 bytes / 42,475 patterns**, structural coverage
**69/83**, and reference evidence **4,802 nodes**. The candidate carries **1,027**
checked nodes into startup. Both arms finish with **23,320** checked nodes, also
their maximum recorded count. This is not a process-RAM measurement; retaining
objects longer and auxiliary caches still cost memory. All **283 tests** pass.

**Next priority:** resume structural discovery on **case 1227, index 38**, at
**40 variables / 165 clauses / 494 literals**, with no pending split. The verified
acquisition checkpoint remains **`cnf-canonical-source/report.json`**, SHA-256
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`; use its
**`next_selection`** and **`compare_cnf_canonical_source.restore_checkpoint`**.
Keep evidence **(1, 42, 156, 63, 1)** and **two bridges**. This run changes replay
machinery only, so it does not replace that acquisition checkpoint.

Cold startup still costs about **63.48 seconds**; older parent restoration is
separate (observed **114.50 seconds**, overlapping tests before measured arms).
Extend checked reuse into earlier checkpoint schemas only after verifying their
contracts. A further specific gap is repeated expanded-certificate traversal and direct
semantic rule checking: later positive checks still cost about **2.6 seconds** even when they verify
zero new inventory nodes. Measure source/evidence binding and decoding before
adding another cache. Current evidence supplies no unrestricted-SAT bound.

## Previous investigation: checked canonical order and the next original

[Checked canonical-source reuse](checked-canonical-sources.md) closes
**case 1190**, raising structural coverage **68/83 -> 69/83**, and stores **25
new records**. Twelve eliminations, seven binary-path reductions, four probes,
one polarity change and one Horn/zero-valid terminal complete the pending split.
The terminal has **8 variables / 10 clauses / 27 literals**. All twelve formerly
unstored states now have records; the batch enters and stores 25 states.

The new representation check avoids sorting and renaming only after scanning
the source and proving that its order and compact labels already satisfy the
old normal form. It keeps exact keys, maps, certificate policy and stored bytes;
other sources fall back to the original normalizer. No retained cache is added.
Two reversed-order repetitions reduce the **complete startup-and-expansion
sequence 71.96107 -> 68.45498 seconds (4.87%)**; initial global preparation drops
**69.51709 -> 65.98742 seconds (5.08%)**. These are development-case measurements,
not a held-out or unrestricted-SAT guarantee. Both methods keep the batch copy;
the preceding copy-removal regression remains unchanged.

**Next discovery target:** **40/165/494**, original **case 1227**, retained index
**38**, no pending split. Resume **`cnf-canonical-source/report.json`** with
**`compare_cnf_canonical_source.restore_checkpoint`**, report SHA-256
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`.
Use **`next_selection`**, not the completed `source`. Keep evidence
**(1, 42, 156, 63, 1)** and **two bridges**. The restorer and independent replay
still use the original normalizer; the new inventory is an optional equivalent
implementation for subsequent comparisons and discovery.

**Largest remaining costs:** parent restoration **134.48837 seconds** and
initial global checking still dominate. A cold profile places normalization
at about **20% of instrumented query time**; unit fixed-point reconstruction
is the larger individual primitive. Investigate repeated source-bound checking
and sharing of immutable structure before expanding caches. The existing probe
cache evicts often, but repeated use of those evicted keys has not been measured.
Check whether already validated authority can survive restoration into startup.
A positive certificate does not establish complete negative frontier information.

The candidate accepts **28,169 / 48,182** canonicalization calls and still pays
**20,013** fallbacks. It replaces 11,031,610 old-normalizer input-literal charges
but adds 16,666,740 precheck visits; these counts are not a total CPU-work saving.
History grows **319,488 bytes** to **780,677,120 bytes / 42,475 patterns**. Delta:
**380,928 bytes / 14,120 compressed**. Both methods retain **20,404 / 2,916**
checked current/prepared objects; peak RAM is unmeasured. Reference nodes grow
**4,750 -> 4,802**. All **274 tests**, independent eight-query/prefix replay and
reference checking pass. No previous proof blocks or experiment sources change.

## Previous investigation: batch copies and continued conditional discovery

[The batch-copy comparison](expansion-without-batch-copy.md) stores **82 new
pattern records** across four bounded expansions: 30 eliminations, 27 probes,
17 binary-path reductions, three family terminals and five unresolved records.
The terminals include Horn/zero-valid and 2-CNF cases, but overall coverage stays
**68/83**. The sequence charges **105 admission entries**, including re-entry;
twelve final entries remain unstored. Recognized endpoints do not imply cheap
recognition or acquisition of every ancestor.

**Retain the negative result:** omitting all per-batch seed copies avoids
**3,118,911,488 logical copied bytes**, yet mean four-worker time regresses
**4.61350 -> 6.28484 seconds (36.23%)** and the complete sequence regresses
**75.23972 -> 77.78679 seconds (3.39%)**. Both methods still hash all historical
tables and retain identical evidence. The first digest without a copy takes
about **3.28 seconds**, versus **0.44--0.50 seconds** after copying; later scans
are similar. OS/cache causality is unmeasured. Keep the copied-seed default;
test copying the first batch only during subsequent fresh discovery. That
combined policy has not been measured and cannot inherit a speedup by adding
times from separate runs.

**Resume** `cnf-copyless-sequence/report.json` with
`compare_cnf_copyless_sequence.restore_checkpoint`, report SHA-256
`0cf43154fba97eae8b971d700b7381fa671d2347aac4f45a41300ad208e1dcfd`.
Use **`next_selection` with its pending split**, at **26/94/284**, not the initial
`source`. Preserve evidence **(1, 42, 156, 63, 1)** and **two bridges**. Initial
binding is original **case 1190, index 31**; retained selections have an empty
original-index list. Cold validation checks actual dependency ancestry rather
than inventing a selector binding. Such a path does not transfer SAT truth or
complete the original's other obligations.

**Largest total-cost gaps:** initial global checking/construction remains
**67--69 seconds**, parent restoration **129.01658 seconds**, and final cold
coverage **71.31630 seconds**. Warm query cost is only **0.25 seconds**, plus
**0.31 seconds** output serialization. Reuse the checked session, then investigate
complete cold authority and resumable unfinished work. Persisted positive
coverage alone cannot certify the unresolved frontier. For broader discovery,
track certified reduction chains and the interaction left after each terminal,
not just family labels or matching shapes.

History grows **1,085,440 bytes** to **780,357,632 bytes / 42,450 patterns**;
the union delta is **1,175,552 bytes / 52,938 compressed**. Both methods retain
**20,379 current / 2,916 prepared checked objects**, with no measured peak RAM.
Reference nodes grow **4,481 -> 4,750**. Failure-only archives preserve committed
rows as explicitly unchecked evidence and cannot become verified checkpoints.
All **266 tests**, independent acquisition-prefix and twenty-query replay, and
reference validation pass. No unrestricted-SAT or minimum-expansion bound follows.

## Previous investigation: share maintained routes with global queries

[Maintained global queries](maintained-global-catalog.md) reduce mean updated
query time **1.52633 -> 0.23719 seconds (84.46%)** while performing the same
full composition, plan checks and original selection. Both methods retain the
same inventory and route maintenance; the baseline rebuilds another catalog.
The **complete short sequence regresses 70.96985 -> 71.79572 seconds (1.16%)**:
initial checking varies more than the warm-query saving. Preserve that result;
measure longer retained sessions before claiming a total-cost improvement.

Fresh expansion stores **27 patterns** and closes the selected residual of
**case 1443**. One cofactor reaches an inherited contradiction after two probes;
the other uses 25 new nodes, interleaving binary-path reductions, elimination
and probes before a polarity change exposes a **Horn, zero-valid** terminal.
Coverage stays **68/83**: other original obligations remain. This shows a
composable reduction chain, not a new tractable class for every CNF.

**Next discovery target:** **40/163/490**, original **case 1190**, index **31**,
no pending split. Keep the checked inventory and complete maintained catalog
alive across several such residuals, measuring startup amortization. Investigate
repeated reduction chains using exact certified edges, not shape similarity.
**Largest complete-cost gap:** parent restoration **124.46543 seconds** and
initial global checking/construction **67--69 seconds**; cold final coverage
is **71.74615 seconds**. These dominate the remaining **0.23719-second** warm
query. Positive-only stored proofs cannot certify negative frontier claims.
Within the first retained worker, preparation costs **1.04254 seconds** versus
**0.22849 seconds** local expansion; full-table digests alone cost **0.48173
seconds**, and a complete seed copy remains. Compare removing redundant
copying under the checked append boundary before further query tuning; retain
the earlier append-time guarded-digest regression.

Resume **`cnf-session-catalog/report.json`** using
**`compare_cnf_session_catalog.restore_checkpoint`**, report SHA-256
`f856409b5a58b402ccf6f545dc8570cae22952a79b2b06460a8f68ab2635e10b`.
Use `next_selection`, not the completed `source`. Evidence is
**(1, 42, 156, 57, 1)** with **two bridges**. History is **779,272,192 bytes /
42,368 patterns**, up **372,736 bytes**; delta **438,272 bytes / 20,280 compressed**.
Both methods end with **710 routes**, no pending targets, and
**20,297 / 2,916** checked pattern/prepared objects. Catalog sharing adds no
persistent index; peak RAM is unmeasured. Reference nodes grow **4,413 -> 4,481**;
positive coverage stays **3,564 steps**. Guards preserve acquisition ledgers and
reject stale authority, but rely on immutable caller-owned cached objects.

All **259 tests**, independent replay of **eight global queries**, prefix
catalog checks and reference validation pass; all **64 previous proof blocks**
are preserved. The detailed validation record binds previous artifacts and
sources. No unrestricted-SAT complexity or minimum-expansion bound follows.

## Previous investigation: distinguish cold checking from global graph work

[The global navigation comparison](indexed-original-navigation.md) replays the
saved six-pattern append without new acquisition. Retaining the checked inventory
reduces the complete measured two-query sequence **138.45321 ->
75.96089 seconds (45.14%)**, including initial
construction and both original selections. The final query alone falls
**65.45308 -> 1.40345 seconds**.
Most of the old cold global cost is repeated semantic checking.

**Next cost to remove:** complete route rebuilding still costs **1.12777 of
1.40345 seconds (80.36%)** in the warm full query. Original selection costs only
**0.07732 seconds**. Reuse the existing complete route-maintenance state during
fresh bounded expansion and global queries; do not prioritize more selector
micro-optimization. The index reduces graph visits (26,109 to six option-source
checks across two graphs), but it adds retained state and changes selection time
only slightly. All methods end with **20,270 / 2,916** checked pattern/prepared
objects; indexes additionally retain **13,055 / 13,054-node** graphs.

The new indexed selector preserves exact selections and uses full composition
for sources outside its original graph. Both indexed updates check only
**6 option sources**, but complete-sequence results against retained
full composition are mixed: **74.19371/73.95375 seconds** in the first repetition
and **75.46496/77.96803 seconds** in the second (indexed/full). Keep the index
optional. A mean from two variable observations does not establish a stable
net benefit or reduced peak RAM. Coverage remains **68/83**; this is replay of
previous work, not a newly completed original.

Resume fresh discovery from **`cnf-original-handoff/report.json`** using
**`compare_cnf_original_handoff.restore_checkpoint`**. Next is **40/158/467**,
original **case 1443**, retained index **72**, no pending split. Preserve evidence
**(1, 42, 156, 56, 1)** and **two bridges**. Keep the inventory and complete
maintained routes alive through a bounded sequence of new expansions and global
queries. Cold reconstruction, initial global checking and growth of retained
state remain open; no unrestricted-SAT efficiency bound follows.

Independent cold validation passes in **259.30996 seconds**, checking all
**twelve selections and coverage certificates** with the original algorithms on
fresh inventories and verifying all **4,413 reference nodes**. The copied
scheduler bodies match their frozen baseline after reversing only the closure
calls and extra argument. All **254 tests** pass; the manuscript builds to
**165 pages** with all **64 previous proof blocks** unchanged. All **1,634 prior
artifacts / 31 manifests** and **95 historical source files** are preserved.
The new manifest binds **32 artifacts**. Validation tasks overlapped, so cold
elapsed time is not a performance comparison.

## Previous investigation: retain checked state across originals

[The original-transition comparison](original-session-handoff.md) closes
**case 1061**, raising coverage **67/83 -> 68/83** with **six probe patterns**.
Two reversed-order repetitions per method produce identical operations and
stored evidence. Retaining the session reduces the complete measured sequence
**18.99400 -> 11.61121 seconds (38.87%)**, including initial construction,
replay of completed case 1120, binding to case 1061 and expansion. This replays
the already stored case-1120 result; it does not acquire that original again.
The worker-only reduction **8.56483 -> 0.94843 seconds** excludes the common
initial query. Retention increases live checked-cache counts and saves no
persistent space. Both new cofactor chains reach an inherited contradiction.
The selected conditional residual is UNSAT; original case 1061 is SAT, with a
checked model. Structural coverage of the original is the completed obligation.

1. **Maintain global coverage and original navigation across expansions.**
   Final route preparation and global coverage still cost **69.64522 seconds**,
   versus **0.14447 seconds** mean retained local expansion. Compare the existing
   `CoverageIndex` with full recomposition on matched appends, checking complete
   catalog updates, implicit rules and activation of formerly missing targets.
   The current transition consumes an already selected original-bound focus;
   it does not yet maintain global selection incrementally.
2. **Use the retained session on the next unresolved interaction.** Next is
   **40/158/467**, original **case 1443**, retained index **72**, no pending split.
   Inspect its saved pairs and conditional reductions. The previous transition
   needed only six probe nodes and the existing contradiction terminal, so
   acquisition was much cheaper than repeated checking and navigation. That is
   a finite observation, not a bound for the remaining fifteen originals.
3. **Separate cold reconstruction and live memory from warm gains.** Parent
   replay costs **119.01318 seconds**. Retention ends with **3,100 checked pattern
   objects / 108 prepared checked objects**, versus **2,453 / 11** after restart.
   These counts are not peak RAM; cache lifetime and eviction remain open.
   Guarded digest reuse remains experimental after the previous regression.

Resume **`experiments/results/cnf-original-handoff/report.json`** with
**`compare_cnf_original_handoff.restore_checkpoint`**, SHA-256
`6944b224d026a09bc6aa1bc6bb118d55b29a94a851ef2f2fcc2054f7c9358175`.
Evidence is **(1, 42, 156, 56, 1)** with **two bridges**. Use `next_selection`,
source hash `275abd014656ded13e9b3acab99c976726b7ca9b424f91c71d1a6ea057fd21f6`;
the report's `source` is completed. History is **778,899,456 bytes / 42,341
patterns**, up **77,824 bytes**. The delta is **7,095 compressed bytes**;
reference nodes grow **4,198 -> 4,413** and positive coverage steps **3,518 ->
3,564**. All **709 activation routes** have available targets. No unrestricted
SAT efficiency or minimum-expansion guarantee follows.

Independent cold replay passes in **514.17263 seconds**, reproducing all four
arms and checking **4,413 reference nodes**. All **249 tests** and the
**164-page** manuscript build pass; **64 previous proof blocks** remain
unchanged. All **1,567 artifacts / 30 prior manifests**, **91 historical source
files** and **4,198 prior reference payloads** are preserved. The new manifest
binds **67 artifacts**. Validation work overlapped; its elapsed time is not a
performance comparison.

## Previous investigation: live scans, original coverage and a retained regression

[The matched digest investigation](guarded-table-digests.md) closes the saved
34-variable interaction and original **case 1120**. All six independent runs
store **32 patterns** in one batch, with no unfinished admissions; coverage
increases **66/83 -> 67/83**. Live full scans reduce mean worker time from
**12.68940 to 8.55304 seconds** (**32.6%** on these measurements). Both scan all
rows. Guarded hash reuse is **not** the cause: the focus closes before a second
batch. The separate append replay skips seven tables but has no mean refresh
speedup and a slower complete sequence. Keep that regression and favor live
full scans for subsequent work.

1. **Carry checked state across original focuses, while broadening coverage.**
   The next source is **39/167/519**, original **case 1061**, retained index **13**,
   with no pending split. Inspect its unresolved interactions and saved pairs.
   The live-full worker still spends **7.54456 of 8.55304 seconds** constructing
   the checked session; retaining it across sources is the largest remaining
   worker opportunity. Preserve exact original binding and charge navigation.
2. **Avoid rebuilding unaffected global coverage.** Final route preparation and
   global coverage take **69.46916 seconds**, versus **0.17183 seconds** mean
   local expansion. Parent reconstruction is **114.01706 seconds**. Investigate
   integration of the existing `CoverageIndex` and live route maintenance with
   the original-case navigator. Complete catalog and implicit-rule updates need
   explicit checks; do not trust persisted closure flags.
3. **Leave guarded digest reuse experimental.** It reuses **24,281 rows** across
   seven tables but must rescan **42,335 pattern rows**. Mean refresh is
   **0.42716 versus 0.42444 seconds**; complete replay sequences are
   **6.22119 versus 4.71509 seconds**. Initial count scans alone cost about
   **0.72--0.79 seconds** on copied seeds. Eliminate that redundant first scan
   before a longer amortization study. Unchanged-read savings do not establish
   expansion savings, and changing pattern-table growth remains unrestricted.

Resume **`experiments/results/cnf-guarded-digests/report.json`** with
**`compare_cnf_guarded_digests.restore_checkpoint`**, SHA-256
`15f28884970be856f78475cdc426604f499998f6f2483ebbaa2760f8e8cc194f`.
Preserve evidence **(1, 42, 156, 55, 1)** and **two bridges**. The report's `source`
is now completed; follow `next_selection`, key hash
`88d90c3204e339d9422e80bd0a4ef8fa3db398874e034334de0ba7995916e92b`.
History is **778,821,632 bytes / 42,335 patterns**, up **405,504 bytes**; the delta
is **21,314 compressed bytes**. Reference nodes grow **4,153 -> 4,198** and the
positive certificate **3,360 -> 3,518 steps**. All **708 activation routes** have
available targets. Sixteen original cases remain open; no arbitrary-SAT size or
runtime bound follows.

Independent replay checks all **4,198 reference nodes** and reproduces all six
arms without fresh recognition or reference search. All **245 tests**, the
**164-page** manuscript build and preservation of **64 old proof blocks** pass.
All **1,493 prior artifacts / 29 manifests** are unchanged. Cold validation takes
**545.69979 seconds** with other validation work overlapping; it is not a speed
comparison. The checkpoint manifest binds **74 artifacts**.

## Previous investigation: mixed terminal classes and repeated table scans

[The conditional continuation and profile](reduction-reuse-profile.md) store
**35 patterns**, completing the saved 25-variable split through **7/7/19
zero-valid** and **6/6/12 2-CNF** terminals. Neither terminal is Horn or dual-Horn;
the second accepts neither uniform assignment. The original-bound focus remains
open and coverage stays **66/83**. Both repetitions produce identical logical
work; only the second is instrumented.

1. **Measure and avoid redundant full-table digest scans.** Ordinary workers
   total **17.86459 s**, with **17.31958 s** preparation and **0.34281 s** expansion.
   The second instrumented batch spends **3.78143 of 4.78940 s** recomputing all
   eight table digests, versus **0.13202 s** copying and **0.00393 s** guarding the
   retained session. Profile per table, then compare checked reuse of unchanged
   table digests on the same expansion. Changed tables still require correct
   recomputation or an incremental structure; the existing key-ordered hash is
   not an append-only transcript. Retain cold authority checks and invalidation.
2. **Continue the next mixed interaction and inspect exact reuse.** The pending
   **34/120/355** split has **31/102/295** and **31/104/295** targets, both absent.
   Preserve the saved pair and the completed conditional evidence. Investigate
   convergence after checked reduction across different recognized classes,
   rather than expecting the raw cofactors to have identical syntax.
3. **Bound repeated unfinished work explicitly.** The two batches charge 64
   admissions, store 35 patterns and leave 13 final inputs unstored. Sixteen
   first-batch interruptions are charged again. Checked local continuations
   remain a possible improvement; no arbitrary-CNF decomposition-size, cache-
   size or efficient-recognition bound follows from these finite runs.

Resume **`experiments/results/cnf-reduction-reuse/report.json`** through
**`continue_cnf_reduction_reuse.restore_checkpoint`**, report SHA-256
`e6610fbbbbd52dcc6986ca8881f4e8aea1a3ba16ef33fb9beee5b42ec978337e`.
Preserve evidence **(1, 42, 156, 55, 1)** and **two bridges**. Read `next_selection`;
its pending source hash is
`1aa4a355993275a5aed0d3f263d5e5d2078b4fd6330ce9f8eb3d864fec88db6a`.
The focus remains original **case 1120**, retained index **22**. History grows
**430,080 bytes** to **778,416,128 bytes / 42,303 patterns**; the union delta is
**18,876 compressed bytes**. Reference nodes grow **4,114 -> 4,153**; the global
positive certificate remains byte-identical. Instrumented and ordinary timings
must stay separate. No runtime or memory reduction is established by this run.

Independent cold replay passes in **417.85190 s**, checking every intermediate
catalog with fresh discovery and reference search disabled. It verifies all
**4,153 reference nodes**, preserves all **4,114 prior payloads** and all
**1,428 artifacts / 28 prior manifests**, and confirms exact reuse of the sixteen
completed false-cofactor certificates. All **238 tests** pass; the manuscript
builds to **163 pages** with all **64 previous proof blocks** unchanged. The
checkpoint manifest binds **65 artifacts**, with commands and limitations in
`validation.json`.

## Previous investigation: exclude renaming proposals and continue case 1120

[The signed-renaming audit](signed-renaming-filter.md) distinguishes all **32
candidate targets** and excludes all **496 pairwise signed variable bijections**.
Three pairs matched variable, clause and literal counts; stronger width and
paired-occurrence invariants reject them. The audit costs **0.03586 s**, including
writing. It establishes a necessary-condition filter, not a positive equivalence
checker, SAT classification theorem or comparative speedup.

The unchanged worker then stores **54 patterns**, including a **5/4/9 Horn and
zero-valid terminal**, in two batches per independent run. **Coverage remains
66/83**. One interrupted state is reentered and completed; nine final inputs
remain unstored. Both repeats produce identical per-batch evidence.

1. **Resume the saved interaction and seek convergence after reduction.** The
   next source is **25/96/309**, with pending **23/89/277** and **22/73/215**
   targets. Preserve the exact pair and charge interrupted work. The initial
   32 targets cannot reuse one another by signed renaming, but descendants
   may converge after checked reductions. Test this broader opportunity before
   expensive isomorphism search on the rejected original pairs.
2. **Profile remaining preparation and cold reconstruction.** Two-batch workers
   average **18.01738 s**, of which **16.81073 s** is preparation and **0.91088 s**
   expansion. Acquisition alone is **0.43381 s**. Restoration costs **105.00548 s**
   and final route preparation/global coverage **68.70599 s**. Retaining checked
   sessions already avoids repeated checking between the two batches; further
   savings require locating the remaining snapshot and authority work.
3. **Investigate bounded continuation when repeated frames dominate.** Nine
   interrupted inputs expose incomplete recursive work. Persisting checked
   local frames could avoid repetition, but needs explicit invariants and a
   matched measurement. No bound on decomposition depth, number of batches,
   total stored state or recognition cost for arbitrary CNFs follows.

Resume **`experiments/results/cnf-original-1120/report.json`** through
**`continue_cnf_original_1120.restore_checkpoint`**, SHA-256
`d0ffd584ce79e219103ec891f04b7a038aff42cc9b9b86221bbf0c0b41f4fb8e`.
Keep evidence **(1, 42, 156, 54, 1)** and **two bridges**. Read `next_selection`;
its pending source hash is
`7187942ac65244a2700f4c0e912ca876ca046144695d4392d2b006913ac98bd7`.
The original focus is case **1120**, retained index **22**. History grows
**749,568 bytes** to **777,986,048 bytes / 42,268 patterns**. The new delta is
**38,073 compressed bytes**; reference nodes grow **3,830 -> 4,114**, while the
**3,360-step global positive certificate** remains byte-identical. The live
index has **707 routes / two missing-target links**. No memory reduction is
claimed. Validation details and the exact invariant argument are in the linked
investigation record.

Cold reconstruction passes in **419.43195 s** with fresh discovery and reference
search disabled. All **238 tests**, **4,114 reference-node checks** and prior
artifact-preservation checks pass. The manuscript builds to **163 pages** with
all **64 proof blocks** unchanged. The new findings also confirm actual reuse
of an inherited two-variable plan and the empty-CNF terminal after reductions.

## Previous investigation: finish the retained interaction and return to originals

[The conditional continuation](session-frontier-closure.md) completes the true
32-variable cofactor through **29 new patterns** to a **7/21/85 one-valid
terminal**, outside Horn, dual-Horn and 2-CNF. Its false branch reuses the stored
refutation. Two independent runs finish in one 32-entry batch, preserving
identical evidence. All seven previously interrupted inputs are charged again.
The enclosing **39/161/495** focus closes and the saved-split frontier empties.
**Coverage remains 66/83:** seventeen original inputs still have unresolved
leaves. Empty retained obligations are not complete original-input coverage.

1. **Investigate the next source bound to an uncovered original.** The global
   navigator selects **39/162/510**, original **case 1120**, retained case index
   **22**. It has `learning_clear` status and no pending split. Inspect its
   remaining shared-variable interactions and saved alternatives before fresh
   acquisition. Preserve the original binding and compare alternative choices
   on the same source if changing the scheduler. The earlier 1062 original
   remains open through a different **40/174/541** leaf.
   The next profile has **16 saved pairs / 32 distinct absent target keys**.
   Variable-5 and variable-22 true targets share shape **37/138/416** but have
   different keys. Test a checked renaming before treating matching counts as
   reusable structure; the negative exact-overlap result is preserved.
2. **Profile cold reconstruction and snapshot preparation.** Mean expansion
   is **0.15429 s** within a **12.41063 s** complete worker; preparation costs
   **12.16111 s**, including **7.38139 s** checked session startup. Restoration
   adds **99.77114 s**, final route preparation/global coverage **70.02150 s**.
   These two repetitions are not a speed comparison. Avoid resetting a live
   checked session when subsequent work can safely reuse it, but retain cold
   authority checks and measure remaining phases separately.
3. **Keep general discovery and persistence limits explicit.** This reduction
   recognizes an existing terminal class on a new conditional chain. No bound
   on recognition depth, total decomposition size or accumulated storage follows.
   There are no interrupted states left in this focus; the general checked-local-
   continuation gap remains for other long chains.

Resume **`experiments/results/cnf-session-frontier/report.json`** through
**`continue_cnf_session_frontier.restore_checkpoint`**, SHA-256
`8349c88556f684eaaed5d0ea296e465cddf85086c2d240d30644ecb2e7436625`.
Keep evidence **(1, 42, 156, 48, 1)** and **two bridges**. Select the next
source from the bound `next_selection` archive, **not the completed `source`
field**. Its key hash is
`4270b94e85e15c2b76fb43fe6a320f98d3908c0020fa3a27e6daf5404c3831f5`.
History is **777,236,480 bytes / 42,214 patterns**, growing **364,544 bytes**;
the delta is **15,542 compressed bytes**. No split sidecars or external probe
rows are added. The **3,830-node reference archive** and **3,360-step global
positive certificate** retain their sizes. The live index has **701 routes /
zero missing-target links**. Persistent growth and peak RAM remain separate.

Independent cold replay passes in **346.50085 s**, reproducing both workers
and every intermediate catalog without fresh discovery or reference search.
It checks all **3,830 reference nodes**, verifies both cofactor results and
confirms the seven previously interrupted states are now stored. All **233
tests** pass. The manuscript builds to **162 pages**, with no overfull boxes
or undefined references; all **64 previous proof blocks** are unchanged.
All **1,321 artifacts across 26 prior manifests** and all prior reference
payloads are preserved. The reference archive and global positive certificate
are byte-identical to the parent. The new manifest binds **40 artifacts /
4,103,023 bytes**, including the local/global frontier distinction and the
negative exact-overlap check on the next 32 candidate targets. Commands, source
fingerprints and concurrency notes are in
`experiments/results/cnf-session-frontier/validation.json`.

## Previous investigation: retain checked state across expansion batches

[The startup profile and matched comparison](retained-expansion-session.md)
identify repeated route checking as the dominant warm preparation cost.
Keeping the live checked inventory and maintained catalog across two 32-entry
batches reduces their mean combined worker time **23.32780 -> 16.18611 s
(30.61%)**, including initial checking. Second-batch startup falls
**7.40238 -> 0.00404 s**. The boundary rejects unmaintained writes, changed
policies, sidecars and external versions before resetting the admission ledger.
It requires exclusive ownership and immutable old rows/caches; cold restart
still reconstructs and checks authority. Cache lifetime increases; this is not
a memory reduction.

1. **Resume the remaining conditional interaction.** Both methods store the
   same **44 patterns**, including **6/7/18** and **4/3/6 Horn terminals**, while
   coverage remains **66/83**. The new **36/144/434** split has an acquired false
   **31/120/344** child and a pending true **32/110/308** child. Preserve the false
   child and resume the exact pair, charging the seven unfinished entries again.
2. **Separate the remaining preparation and cold costs.** The retained second
   worker still spends **3.69664 s** in preparation, including copying and table
   digests. Profile those phases before selecting another shortcut. Historical
   restoration costs **95.47416 s** and final global checking **69.18542 s** outside
   the paired workers; neither benefits from live session retention.
3. **Preserve unfinished recognition safely.** Thirteen first-batch entries
   must be charged again in the second batch. A live checked cache does not save
   those unfinished recursive computations. Checked local continuations remain
   a distinct gap, with source/target bindings and branch obligations required.

Resume **`experiments/results/cnf-expansion-session/report.json`** through
**`compare_cnf_expansion_session.restore_checkpoint`**, SHA-256
`a9133c94e01789bb80298de290f17177f71ae428f6d827142bd287722dca9793`.
Keep evidence **(1, 42, 156, 48, 1)** and **two bridges**. The linked note binds
the pending targets. The frontier has **two open splits / no acquired open leaf /
one pending target**. History is **776,871,936 bytes / 42,185 patterns**, growing
**540,672 bytes**; the union delta is **22,766 compressed bytes**. Reference
evidence has **3,830 nodes**, the positive certificate **3,360 steps**, and the
live index **701 routes / one missing-target link**. The current evidence gives
no efficient arbitrary-CNF decomposition or compact-state guarantee.

Independent cold replay passes in **518.83008 s**, reproducing all eight
workers and their intermediate catalogs without fresh discovery or reference
search. It verifies **3,830 reference nodes**. All **233 tests** pass. The
manuscript builds to **162 pages**, with no overfull boxes or undefined
references; all **64 previous proof blocks** remain unchanged. All **1,220
artifacts across 25 prior manifests** and all **3,803 previous reference
payloads** are preserved. The new manifest binds **101 artifacts / 4,289,703
bytes**, including the startup profile, eight workers, cold replay, structural
findings and test/build logs. The initial failed external-write test fixture
is retained and explained; its correction changes stored bytes rather than
issuing an external no-op update. Exact commands, source fingerprints and
concurrency notes are in
`experiments/results/cnf-expansion-session/validation.json`.

## Previous investigation: guarded delta export and a conditional one-valid branch

[Append-only export](append-delta-export.md) cuts mean complete-worker time
**13.11241 -> 9.92093 s (24.34%)** with identical search and delta bytes in
two reversed-order repetitions. Export falls **4.87738 -> 0.76122 s**, charging
**0.66334 s** boundary setup to preparation. Row counts still scan historical
index pages; there is no delta-only asymptotic bound or persistent-space gain.
The rejected first guard and its baseline are preserved separately.

1. **Resume the two exact pending cofactors for broader structural coverage.**
   The previously interrupted 29-variable branch now closes through **21 new
   states** to a **9/16/43 one-valid terminal**, outside Horn, dual-Horn and
   2-CNF. Its sibling leads to **24/88/274**, whose new split has missing
   **20/68/198 false** and **21/71/208 true** targets. Reentry of all thirteen
   previously unstored states is charged; eleven new unfinished inputs remain.
   Both targets and the separate unresolved 36-variable leaf are obligations.
2. **Profile checked startup before optimizing its dominant cost.** Preparation
   now averages **8.84331 s** of the **9.92093 s** worker, including boundary
   setup. Cloning, repeated historical digests and catalog loading need separate
   measurements. Historical reconstruction adds **90.58347 s** outside the
   worker. A retained verified snapshot may avoid repeated work, but authority,
   invalidation and cold reconstruction must remain explicit.
3. **Retain the interruption-safe continuation gap.** Only **21 of 32 entered
   states** are stored. Pending local certificates could preserve unfinished
   recognition, but would need independently checked source/target bindings
   and branch obligations. The current exporter changes no acquisition order.

Resume **`experiments/results/cnf-append-export-checked/report.json`** through
**`compare_cnf_append_export.restore_checkpoint`**, SHA-256
`81e1c7c0b887277cefa62df011738e73c809a9fef16897ba5238e84bf45732d4`.
Keep evidence **(1, 42, 156, 46, 1)** and **two bridges**. The method note binds
the pending source and both target hashes. Coverage is **66/83**, with
**five open splits / one acquired leaf / two pending targets**. History grows
to **776,331,264 bytes / 42,141 patterns**; the unchanged-format delta is
**12,754 compressed bytes**. There are **3,803 reference nodes**, a **3,360-step**
positive certificate and **699 live indexed routes / two missing-target links**.
Neither peak-RAM savings nor efficient arbitrary-CNF decomposition is proved.


Independent cold replay passes in **365.45167 s**, checks all four workers and
all four intermediate catalogs, and verifies **3,803 reference nodes** without
fresh discovery or reference search. All **229 tests** pass. The manuscript
builds to **161 pages**, with no overfull boxes or undefined references; all
**64 previous proof blocks** are unchanged. All **1,147 artifacts across 24
prior manifests** and all **3,781 prior reference payloads** are preserved.
The new manifest binds **73 artifacts / 3,954,783 bytes**, including the rejected
attempt. Exact commands, source fingerprints, concurrency notes and checks
are in `experiments/results/cnf-append-export-checked/validation.json`.

## Previous investigation: conditional Horn closure and the cost of interruption

[The new continuation](conditional-frontier-resumption.md) closes the missing
32-variable cofactor through eleven new states to a **17/26/62 Horn and
zero-valid terminal**. Its sibling remains open. A new variable-2 split of
**31/122/370** reaches **24/88/274** on one side and interrupts its true
**29/115/343** target. Both repeats enter **32 states**, store **19**, and leave
**13 entered but unstored**. Coverage remains **66/83**, with **4 open splits /
2 acquired leaves / 1 pending target**. These are source-bound reductions; the
new Horn endpoint is not identical to a previously stored terminal.

1. **Continue certified discovery from the saved variable-2 pair.** Resume its
   true 29-variable target while reusing the acquired false child. Charge the
   thirteen unstored keys again. Afterward, inspect the remaining 24- and
   36-variable interactions. Keep both branch obligations and distinguish
   reuse of completed certificates from recurrence of a reduction pattern.
2. **Target checked startup/export reuse for total runtime.** Mean worker
   preparation/export are **8.06032 / 4.85783 s**, roughly **97%** of the
   **13.25993 s** worker. Expansion is **0.25005 s**, including acquisition
   **0.13225**, selection **0.09339**, maintenance **0.02355** and coverage
   **0.00086 s**. Full historical restoration costs **92.09233 s** outside the
   worker. The run changes no scheduling policy and establishes no speedup.
3. **Evaluate interruption-safe local continuation records.** The thirteen
   unstored states repeat a known persistence gap. A deterministic unary chain
   longer than every fresh budget can make no persistent progress on any
   retry under the present recursive storage order. The linked analysis gives
   the conditional argument and required source, target and branch bindings.
   Pending local certificates must remain separate from closed patterns.
   Compare avoided recognition against added checking, serialization and cold
   replay; it is not yet the largest measured runtime cost.

Resume **`experiments/results/cnf-conditional-frontier/report.json`** through
**`continue_cnf_conditional_frontier.restore_checkpoint`**, SHA-256
`f55bdcefe556222a5b6043f03591e38f10ad8c76bc3c3c73a8eb45aed73c0ef8`.
Keep evidence lists **(1, 42, 156, 45, 1)** and **two bridges**, with the complete
bridge-aware builder and positive verifier. The union adds **19 patterns /
1 split**, growing history to **776,065,024 bytes / 42,120 patterns**; its delta
is **14,220 compressed bytes**. Reference evidence contains **3,781 nodes**,
and the expanded positive certificate remains **3,360 steps**. The live index
has **698 routes / one pending link** and adds memory.

Pending source: `09831bee0e0295f91c4d21b79ffe25508d3dad8b48e5052b4bfde74367574914`.
Missing true target: `944e1c80b727c779838a814ab6d1509ae46b22afbde7e978523bb96c8f0ce859`.

Independent cold replay passes in **305.33218 s** with all **3,781 reference
nodes** checked and both prefix catalogs matching full construction. All
**222 tests** and the **161-page** manuscript build pass; all **64 proof blocks**
are unchanged. All **1,107 artifacts in 23 prior manifests** and previous
reference payloads remain unchanged. The new manifest binds **40 artifacts**.

## Previous investigation: selective activation removes the dominant warm cost

[Pattern activation](pattern-activation.md) retains a complete checked catalog
and revisits routes waiting on newly acquired roots. It accepts only guarded
pattern appends and the reported checked split, preserving both branch
obligations and builder order. Other writes or sidecars use the previous
maintenance path; external writers require reopening checked state.

With identical scheduling and persistent results, mean historical route updates
fall **2.18377 -> 0.02296 s**, expansion **2.41356 -> 0.23051 s**, and complete
worker time **15.08509 -> 12.86353 s (14.73%)**. On current partial expansion the
corresponding costs are **3.33336 -> 0.03679 s**, **3.75094 -> 0.44504 s**, and
**16.85095 -> 13.40605 s (20.44%)**. Preparation/export variation contributes to
whole-worker differences and is not an activation improvement. Both workloads
use two reversed-order repetitions. The current original remains open; no
completed-original speedup is claimed for it.

1. **Resume the exact pending variable-5 pair of original 1062.** Three advances
   store all **32 admitted states**, with no entered-but-unstored key. The
   **34/143/440** source has an acquired false child leading to **31/122/370**,
   and an absent true **32/136/405** target. Resume that target before reranking.
   A separate existing **36/144/434** plan also remains unresolved. These three
   obligations must all be accounted for; closing the pending target alone
   need not close the original. Coverage remains **66/83**.
2. **Exploit the newly exposed reduction patterns in the remaining cofactors.**
   A variable-8 split of **35/149/466** takes twenty-one states on its true
   branch to reach a **7/9/19** Horn, zero-valid terminal. Its other child stays
   open. The first variable-25 split reuses an old unresolved 36-variable plan
   after two new reductions, which saves intermediate recognition but is not
   reuse of a completed proof. Current selective expansion spends about
   **0.26735 s acquiring** and **0.13948 s selecting**, versus **0.03679 s** on
   maintenance. Investigate exact reusable subpaths and better prediction of
   useful conditional families. The alternative first variable-17 split is
   still untested; this run held search choices fixed.
3. **Reduce setup and persistence costs without losing checked authority.**
   Current worker preparation/export average **7.83564 / 4.97464 s** after the
   optimization. Parent restoration is **80.22699 s** and final global checking
   **68.84394 s**, both outside the warm worker. The live index ends with
   **697 route entries / one missing-target link** and adds memory. There is no
   persistent-space saving or measured peak-RAM reduction. Broader activation
   mixtures, cold-start costs and indexed authority access remain open.

Resume **`experiments/results/cnf-pattern-activation/report.json`** through
**`compare_cnf_pattern_activation.restore_checkpoint`**, SHA-256
`7af092282dfda5070c4dbf1006daa8cff22a218487af28e40b59e8dc51894c7c`.
Keep evidence lists **(1, 42, 156, 44, 1)** and **two bridges**, with the complete
bridge-aware builder and positive verifier. The union adds **32 patterns /
3 splits / no external probe rows**, growing history to **775,811,072 bytes /
42,101 patterns**. Its delta is **23,539 compressed bytes**. Reference evidence
preserves all 3,575 previous nodes and contains **3,734**; the positive
certificate remains **3,360 steps**. The frontier has **3 open split records /
2 acquired leaves / 1 pending target**. Independent cold reconstruction passes
in **498.30431 s**, including all eight workers, four stepwise prefix comparisons
and all **3,734 reference nodes**. All **222 tests** pass and the **160-page**
manuscript builds, preserving its **64 proof blocks**. All **22 prior manifests /
1,009 artifacts** and all previous reference payloads are unchanged. The new
manifest binds **98 artifacts**; full validation is recorded beside the report.

Pending source:
`26f134186dbdd90745599fa2d41308823b8c08b752f19d5f53124ffd4ecd73f1`.
Missing true target:
`72697c710335660e1dc9c934e995f7c37577a9226c546fd7233d4e3685cb3615`.

## Previous investigation: conditional Horn closure and activation after acquisition

[Exact pending-pair resumption](pending-pair-resumption.md) closes original
**1154 / index 27**, raising coverage **65/83 -> 66/83**, also without growth
exceptions. Reusing the acquired false cofactor takes no new admissions. The
missing true **30/111/330** cofactor needs sixteen states to expose a
**19/66/214** residual. Its saved variable-3 split takes another fourteen states
and reaches two different Horn, zero-valid terminals after checked polarity
changes. All **30 admitted states are stored**; all thirteen previously
interrupted keys are reentered and stored. The recurrence is in the reduction
pattern, not an identical terminal or a transported proof between the branches.

Two independent repeats reproduce the same operations and logical results.
Mean acquisition is **0.12262 s**, compared with **2.17729 s** for two full route
updates: **91.2% of the 2.38750 s expansion**. Preparation is **8.01578 s**,
export **4.76630 s**, and the complete worker **15.23836 s**. This is a coverage
checkpoint, not a new comparative speedup. Both steps change the database, so
the inactive-split optimization correctly skips neither rebuild.

1. **Broaden structural discovery on original 1062 / index 14.** The next
   unlabelled residual is **39/161/495**. All sixteen saved candidates have
   absent cofactor roots. The current rank prefers variable 25, with two
   37-variable children and 896 total literals; variable 17 instead gives
   38- and 32-variable children with 765 total literals. Compare these choices
   on matched budgets and completed obligations; four ordinary candidates
   (28, 29, 30, 33) remain available. Determine which choices expose checked
   transformations toward a recognized family. Keep
   overlaps and unresolved cases explicit; the two Horn endpoints above do
   not establish a Horn backdoor in the original coordinates or a uniformly
   cheap recognition strategy. No retained split is pending now; seventeen
   original formulas remain structurally uncovered.
2. **Maintain affected routes after real acquisition.** The two completed
   advances provide concrete validation cases: arrival of the last missing
   root activates an old split; acquisition of both targets permits a new
   split to attach immediately. Maintain all route types, projection bridges
   and newly available premises, and compare complete catalogs against cold
   reconstruction. Acquisition costs only about 0.12 s; optimize the measured
   2.18 s refresh cost before interrupted-recognition bookkeeping.
3. **Reduce history reconstruction only with complete accounting.** Parent
   restoration costs **76.28286 s**, and final preparation/global coverage
   **68.16053 s**. A warm maintenance improvement does not eliminate these
   costs. Persistent growth and verification remain separate obligations.

Resume **`experiments/results/cnf-pending-pair/report.json`** through
**`continue_cnf_pending_pair.restore_checkpoint`**, SHA-256
`0e310e043cc74e29d102115663db88c513acf8bf865fac7412fea1e0eb4f5760`.
Retain evidence lists **(1, 42, 156, 41, 1)** and **two bridges**, using the
bridge-aware catalog and positive verifier. The old `source` focus is now
closed; resume from **`next_selection`**. The union adds **30 patterns / 1 split /
no external probe records** and grows history to **775,376,896 bytes / 42,069
patterns**. The new compressed delta is **17,007 bytes**. The reference archive
preserves all 3,467 prior nodes and contains **3,575**; the positive certificate
has **3,360 steps**. Independent cold replay passes in **289.93906 s**; all
**215 tests** pass and the **159-page** manuscript preserves **64 proof blocks**.
All **969 earlier artifacts** and **3,467 prior reference payloads** are unchanged.
Validation details are in the checkpoint's `validation.json`.

## Previous investigation: skip inactive split updates, resume the remaining cofactor

[Pending-split maintenance](pending-split-maintenance.md) avoids a complete route
rebuild when a checked split is the only sidecar change, the database is
unchanged, and at least one target root is absent. It keeps both branch
obligations and checks exact admission accounting. Later writes rebuild routes,
so newly available targets can activate old splits. External writers require
reopening checked state. The condition is independent of the CNF family.

On the historical interruption, mean final-update time falls **1.08509 ->
0.01138 s**. Expansion falls **4.71930 -> 3.59923 s**, and complete worker time
**17.55753 -> 16.15178 s (8.01%)**, with identical operations and persistent
results. On current resumption every advance writes patterns, so all three
updates rebuild and expansion is unchanged (**3.54491 / 3.54578 s**). This
negative control bounds applicability; preparation/export variation is not a
maintenance improvement. There is no persistent memory saving.

Current resumption stores **19 patterns** under one **32-state allowance**.
It acquires the old variable-26 pair with nine states and resolves a 23-variable
leaf with eight more. The separate **33/130/400** leaf splits at local variable
**18**: the false **29/96/275** cofactor takes two states, while the true
**30/111/330** cofactor consumes thirteen admissions without storing those
ancestor plans. Original structural coverage remains **65/83**. One pending
target remains and there are no acquired open leaves in the retained frontier.

1. **Resume the exact variable-18 pair and inspect the remaining cofactor.**
   Reuse the acquired false child, charge reentry of thirteen unstored keys, and
   follow the true 30/111/330 target. The preceding reductions exposed a
   ten-variable polarity-to-Horn transition; inspect whether conditioning the
   remaining target exposes shared terminals or another checked family route.
   Preserve both branch bindings and verify closure of the original separately.
2. **Maintain affected routes after actual acquisition.** All three current
   updates cost about **1.08--1.11 s** apiece. Acquisition totals about **0.15 s**
   for the baseline worker. A dependency index must include every route kind and
   activate old pending edges when their last target arrives; cold comparison
   must cover both family/probe reductions and split/projection sidecars.
   Current preparation is about **8.1 s**, export **4.7 s**, and current authority
   reconstruction **72.00904 s**. Avoid presenting a warm update saving as a
   reduction of these separate costs.
3. **Measure the value of interrupted-recognition continuations.** Thirteen
   ancestors remain unstored, but the final acquisition costs only about
   **0.06 s**, against **1.08 s** for rebuilding. The admission loss is material
   to this bounded run; it is not the dominant runtime. A checkpoint must bind
   exact CNFs/configuration, children and incomplete obligations without making
   incomplete plans into coverage or dropping reference evidence.

Resume **`experiments/results/cnf-pending-maintenance/report.json`** through
**`compare_cnf_pending_maintenance.restore_checkpoint`**, SHA-256
`9a48fc85512e52c566dd60f0396a4bacf842b48267ee47606394d271d221f8d0`.
Keep five evidence lists **(1, 42, 156, 40, 1)** and **two bridges**, with the
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`. The union
adds **19 patterns / 2 splits / no external probe records**, growing history to
**775,004,160 bytes / 42,039 patterns**. The new delta is **12,874 compressed
bytes**. Reference evidence preserves all **3,422** prior nodes and has **3,467**
in total. The existing positive certificate still has **3,239 steps**.

Pending source SHA-256:
`1fab57607093cb833cc8fa0f21d88c2e7e9eb094dac7cdd416e8a786e3fcf056`.
Missing true target SHA-256:
`5124e2d5f451e42b274ed6886d29676c94f89e27bb3054f77b530f2f3091a3a4`.

Cold replay passes in **487.75798 s**, with complete catalog comparisons and
all **3,467 reference nodes** verified. All five old interrupted keys are now
stored. **215 tests pass**; the paper builds to **159 pages** with all **64 proof
blocks unchanged**. All **865 prior manifested artifacts** are preserved; the
new manifest binds **104 artifacts**.

## Previous investigation: a cheaper completed cofactor, an unfinished original

[Combining the saved-pair and maintenance policies](combined-expansion.md) tests
original **1154 / index 27**. Both modes begin with the same exhausted-source
split, local variable 30 of **38/158/500**. Early selection completes the same
true cofactor with **9 additional states vs 20**, beyond the common ten-state
acquisition. Mean expansion after that common step is **1.11924 vs 3.64836 s**.
Both early branches reach the same retained empty-CNF terminal. Stepwise cold
reconstruction proves completion using only the rows then available.

The original stays structurally open: **65/83** coverage. Ordinary reaches
**12 advances / 30 stored states**; early reaches **4 advances / 32 admitted /
27 stored / 5 interrupted states**. Their mean whole-worker times of **17.80102 /
17.20828 s** concern different unfinished obligations and are not a completed
original speedup. Both perform four full route refreshes (**4.33169 / 4.29539 s**).
The extra eight ordinary clear blocks already avoid rebuilding. Earlier
scheduling and maintenance savings cannot be added.

1. **Resume the exact pending pair, then the remaining acquired leaf.** The
   selected **30/116/363** source has a saved local-variable-26 split with both
   target roots absent: **29/108/336** and **19/54/140**. Reuse the union's 47
   completed new patterns and explicitly measure reentry of the five unstored
   ancestors. Keep one fresh shared allowance and both polarities; do not rerank
   pending work. A separate **33/130/400** acquired leaf remains. Closing this
   pending pair alone does not guarantee closure of the original.
2. **Avoid semantic-route refresh when a pending split changes no active rule.**
   The final early advance stores no pattern or probe row; it adds a checked
   split whose child roots are absent. Its mean full refresh is **1.06672 s**,
   versus **0.03448 s** acquisition. Investigate a checked metadata update with
   explicit sidecar and target-availability guards. Activation after later
   acquisition, scheduling and admission accounting must still agree with cold
   reconstruction. More broadly, preparation and activation dominate: current
   reconstruction costs **67.80502 s**, final preparation/coverage **67.41552 s**,
   and workers spend about **7.7 s** preparing and **4.7--5.1 s** exporting.
3. **Preserve interrupted recognition only with a measured benefit.** Five
   entered ancestor keys are recorded, but their discovered certificates were
   not serialized before the state cap. Test continuation records or a
   finishing-aware budget against exact cold resumption, without treating
   incomplete plans as coverage. Their measured acquisition time is currently
   much smaller than full route refresh, so do not mistake the state counter
   for the dominant runtime cost. Cross-path transport beyond shared terminals
   remains open: the two completed cofactor paths have disjoint new keys after
   the common prefix.

Resume **`experiments/results/cnf-combined-expansion/report.json`** through
**`compare_cnf_combined_expansion.restore_checkpoint`**, SHA-256
`33c45cc536dc9ada0acdb4d1ef9a17bd9a71e260704644aa656af42835c349c3`.
Keep five evidence lists **(1, 42, 156, 38, 1)** and **two bridges**; use the
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`. The union
adds **47 patterns, 6 continuations, 4 windows and 5 split records**. Full history
is **774,766,592 bytes / 42,020 patterns**; it is not one 32-state run. The retained
frontier has **two pending targets / one acquired leaf**, and three retained
split records remain open. Independent replay passes in **302.33071 s**, checks
all **3,422 reference nodes**, preserves both branch obligations and verifies
stepwise progress. All reference-checked split sources/cofactors are SAT; the
open obligation is full structural decomposition, not finding one SAT witness.
Next selected source SHA-256:
`f68661ab48e945151f89e250ebbcc35eb2ff8034799d2a83e2ddd88d7306567d`.

Verification: 209 regression tests pass; the paper builds to 158 pages with all
64 proof blocks unchanged. All 784 prior manifested artifacts are preserved;
81 new artifacts bind the comparison and independent replay.

## Previous investigation: clear probes preserve the semantic route graph

[Checked clear-probe maintenance](clear-probe-maintenance.md) closes original
**1263 / index 42**, raising coverage **64/83 -> 65/83**. Both maintenance modes
use the same ordinary scheduler and acquire the same eleven patterns in four
advances. Keeping the unchanged complete route catalog across two clear appends
reduces mean worker time **17.23793 -> 14.87208 s (13.72%)**. On the historical
forcing control, six skipped rebuilds reduce **20.13427 -> 14.18042 s (29.57%)**
with the same eight advances and twenty-one states. The helper still rebuilds
for forcing, new nodes or changed sidecars. No persistent state saving is claimed.

1. **Broaden decomposition at the next uncovered original.** Original **1154 /
   index 27** has a selected **38 / 158 / 500** leaf. Its ordinary probe pool is
   exhausted; all eleven saved pairs have unacquired child roots. The best rank
   is **[2, 2, 36, 906, 30]**. Acquire and inspect this exact pair, looking for
   shared family certificates and unresolved interfaces in its descendants.
   Compare early-saved versus ordinary scheduling only on descendants with
   remaining probes, where a real choice exists. Use the optional maintenance
   helper where eligible; its savings cannot simply be added to prior scheduling
   gains without a matched combined experiment.
2. **Reduce preparation and activation cost without dropping route alternatives.**
   Optimized worker preparation is still **7.69031 / 7.26581 s**, versus expansion
   **2.46956 / 2.24496 s**. Two full rebuilds remain in each case. The complete
   study charges **62.36289 s** for current restoration and **67.55856 s** for
   global route preparation/coverage. Incremental activation after acquisition
   or a checked prepared state has more remaining cost to address than clear
   probe arithmetic. Guard new target availability, sidecars and invalidation;
   charge construction, cold reconstruction and memory. Current guards still
   serialize all sidecars and retain **1,220,757 / 941,068 bytes** of payload.
3. **Discover cross-path reuse beyond exact normalized keys.** The previous
   early-saved forcing path still differs from the ordinary path. The new helper
   changes neither path nor storage. Seek exact transport or reusable interfaces
   between intermediate states, with recognition and proof costs included.

Resume **`experiments/results/cnf-clear-maintenance/report.json`** using
**`compare_cnf_clear_maintenance.restore_checkpoint`**; SHA-256
`b4aa304049758bff8e80b2118437321a9edf7128657b3a9303a4985ae57daa78`.
Keep five evidence lists **(1, 42, 156, 33, 1)** and **two bridges**; use the
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`. The union
adds eleven patterns, one window, one continuation and two split records. Full
history is **774,000,640 bytes / 41,973 patterns**, with all 33 split sources and
both bridge targets closed. All **209 tests** and independent cold replay pass;
the replay checks identical histories across modes and all **3,259 reference
nodes**. Eighteen originals remain uncovered. Next source:
`f33c327595b24645a6f64e8a072295c51fb2a414872d0de0f84da49192f0085d`.

## Previous investigation: early saved splits avoid repeated probe work

[Selecting saved pairs before further probing](early-saved-expansion.md) closes
original **1160 / index 29**, raising structural coverage **63/83 -> 64/83**. The
ordinary and early policies acquire the same sixteen new pattern keys, but take
**12 vs 2 advances**. Mean expansion is **13.62996 vs 2.24986 s**, and complete
worker time **26.38845 vs 14.69517 s** (**44.31% lower**). On the earlier forcing
control 1189, complete worker time falls **24.83%**, with **21 vs 20** new states.
Both policies finish both cases; early selection remains optional.

1. **Test how broadly saved-pair selection transfers.** Continue at original
   **1263 / index 42**, selected **37 / 152 / 470** leaf. Its next ordinary
   variables are **32, 33, 34, 37**. Compare the best currently saved pair with
   further probing under identical budgets and seeds. Seek cases where new
   forcing beats immediate splitting; two successful development examples do
   not identify a reliable universal selector. Preserve both branch obligations.
2. **Reduce maintenance cost independently of the search choice.** Even the two
   early runs spend **2.10985 / 2.92588 s** refreshing full routes out of
   **2.24986 / 3.04871 s** of expansion. The full study spends **57.71801 s**
   restoring the current authority and **68.76609 s** preparing/checking final
   global coverage. Incremental activation and prepared checked state remain
   larger total-cost opportunities than arithmetic micro-optimizations. Charge
   invalidation, cold replay and storage, including pending children and later
   forcing; avoid a policy change disguised as a maintenance optimization.
3. **Transport useful structure across different paths.** The forcing control's
   21 ordinary and 20 early new keys are disjoint relative to their common older
   seed. Check common intermediate substructure and exact variable maps before
   duplicating recognition. Structural closure is distinct from a SAT witness
   and from a lower bound on future acquisition.

Resume **`experiments/results/cnf-early-saved/report.json`** through
**`compare_cnf_early_saved.restore_checkpoint`**. Report SHA-256:
`995476297ac2e99710b26b67d9ecc3e95963ab624e68282e7b5108da077999d3`.
Retain five evidence lists **(1, 42, 156, 31, 1)** and the separate **two-bridge**
archive. Use its bridge-aware `routes_for` and
`cnf_projection_bridge.verify_positive`. Both bridge targets and all 31 retained
split sources close. The union retains **36 new patterns**, all extra ordinary
probe work and all earlier results, for **773,828,608 bytes / 41,962 patterns**.
It is not one 32-state run. Nineteen originals remain uncovered. Next source:
`746b92609a26b66fe74b529bdeb36a5a46ca58129c1bcca04c5088bd23d02eeb`.
Its sixteen saved pairs have no acquired child root; best rank is
**[2, 2, 35, 817, 6]**. All **204 tests** and independent cold replay pass,
including **3,203 reference nodes**. The manuscript builds with all 64 proof
blocks unchanged; 533 earlier artifacts remain hash-identical.

## Previous investigation: acquiring a smaller projection costs more

[The bounded acquisition comparison](projection-acquisition.md) completes case
**1298 / index 47**, raising coverage **62/83 -> 63/83** in both views. Ordinary
continuation and projection start from identical independent seeds and complete
the same source. Ordinary uses **4 advances / 8 states / 4.45329 s** of expansion;
projection uses **8 / 9 / 8.70178 s**. Complete worker means are **16.62221 vs
21.45978 s**. Removing a variable does not establish cheaper acquisition.

1. **Reuse existing probe evidence when considering a transformation.** Ordinary
   continuation performs 20 additional external assumption attempts; the new
   target needs 44. Both eventual split pairs already exist in their respective
   initial pattern records. Test selecting a promising saved pair before
   exhausting all clear probes, with matched forcing controls. If transferring
   a split across projection, check the variable map and both cofactors. A
   projection bridge alone does not transport a unit-propagation trace or prove
   that a failed heuristic search can be skipped. Preserve any contrary cases.
2. **Avoid complete route refresh after a clear probe block.** Refresh consumes
   **4.05191 / 8.15891 s**, or **91.0% / 93.8%** of expansion. Keep candidate
   availability current without rebuilding unchanged semantic routes. Validate
   activation of newly acquired targets, new forced routes and closure changes;
   compare complete costs, including cold reconstruction and persistence.
3. **Continue classification on the next original, without assuming size implies
   similarity.** Case **1160 / index 29** has a **37 / 151 / 456** selected leaf.
   Despite almost identical dimensions to the completed leaf, their stored
   normalized clause sets have no exact clause in common. Broader variable
   transport or shared substructure requires its own discovery and certificate.

Resume **`experiments/results/cnf-projection-acquisition/report.json`** with
**`compare_cnf_projection_acquisition.restore_checkpoint`**. Report SHA-256:
`d865c287709cccdd0af56c1a23a564618e369be41fd4e971c21c0834b3510b2a`.
Retain five evidence lists **(1, 42, 156, 26, 1)** and its separate **two-bridge**
archive. Use `compare_cnf_projection_acquisition.routes_for(h, evidence, bridges)`
and `cnf_projection_bridge.verify_positive`. Both bridge targets and every
retained split source close. The union keeps **14 new patterns**, including
both paths' work; full history is **773,255,168 bytes / 41,926 patterns**. The
ordinary/projection arms share three newly acquired exact keys, so the union
is not a single nine-state run. Twenty originals remain uncovered. Next source:
`614772f5cb0f59835870e117b1653b225e008eb44416371335350a725cac6149`.
All **199 relevant tests pass**. Independent cold replay checks all four arms,
global coverage and **3,022 reference nodes** with discovery and reference
expansion disabled. The manuscript builds with all 64 proof blocks unchanged.

## Previous investigation: target discovery works, frontier matches remain absent

[Automatic projection lookup](projection-lookup.md) finds the previous bridge
without a supplied target, but finds **no new bridge on 23 unresolved frontier
sources**. Coverage remains **62/83**. The complete current-policy catalog holds
**19,841 formulas / 17,801 minimal-clause signatures**. Indexed query batches take
**0.87112 s vs 1.55276 s** for scanning the same prepared catalog, while building
it costs **14.42661 s** and adds **28,110,848 bytes**. Do not interpret a faster
lookup as a demonstrated total expansion saving or enable the catalog by default.

1. **Acquire and classify the newly exposed bounded projection.** On the selected
   **37 / 151 / 455** residual of case 1298, variable **13** produces 154 clauses;
   checked subsumption leaves **36 variables / 153 clauses / 470 literals**, within
   final clause growth two but with fifteen more literal occurrences. Its target is not acquired. Compare bounded acquisition with ordinary
   continuation from the same seed. Exact target key is in the new study's
   `selected-diagnostics.json.gz`, SHA-256
   `2689db3a9f1f850442aacef39eb4e6acd62bc431404592a129dc81b9695d94cf`.
2. **Broaden useful structure before accelerating more matching.** Of 967 tested
   variables, 95 exceed the pair cap and 845 exceed final clause growth after
   subsumption. Only 27 projections reach lookup. Investigate which intermediate
   projections expose a family or later reusable target, charging failed work.
3. **Keep catalog preparation conditional on likely reuse.** The warm saving is
   **0.68164 s per batch**; one known match does not justify global preparation.
   Try demand-driven scope and factoring shared policy bytes if indexing becomes
   useful. Full route refresh remains a separate measured expansion bottleneck.

The solver authority and all earlier results are unchanged. Resume
`experiments/results/cnf-projection-bridge/report.json` using its restorer and
bridge archive as documented below. The new lookup study preserves the optional
catalog and negative findings at `experiments/results/cnf-projection-lookup/`.
All **194 tests pass**. Independent cold replay validates the complete index,
all matched result sets and unchanged global coverage without new recognition.

## Previous investigation: exact projection shares the completed proof

[A checked projection connects the two selected leaves](projection-bridge.md).
Eliminating variable **16** from **29 / 108 / 337**, then deleting one clause
subsumed by `[-19, 5]`, gives the exact retained **28 / 110 / 351** target.
The ordinary elimination budget rejected the intermediate three-clause growth;
final growth after deletion is two. Both paths can now use one completed proof.

Matched completion uses **13 instead of 25 new states**, and **6 instead of 7
advances**. With discovery charged, mean expansion time is **15.09% lower** and
complete worker time **6.99% lower** across two reversed repetitions. Both modes
complete the same two roots. The combined route and pattern/probe delta is
**13,170 vs 18,956 compressed bytes**. Route refresh still consumes **6.02 s** of
**6.42 s** of bridge expansion. These are conditional development results.

1. **Discover converging projections on the next original.** Case **1298 / index
   47** has a **37 / 151 / 455** selected leaf. Try checking final subsumption
   before rejecting a projected clause budget, and match the resulting structure
   to retained targets. Current bridge recognition needs a target supplied;
   cheap candidate indexing and wider structural coverage are still missing.
2. **Amortize recognition and maintenance.** Discovery here costs **0.00691 s**,
   but full route refresh dominates warm work, and restoration/final global
   checking dominate the **219.35 s** study. Charge target filtering, failed
   projection proposals and canonicalization when broadening the search.
3. **Preserve exact reuse conditions.** Replay all opposing pairs, every deleted
   clause's retained subsumer, endpoint identities and variable transport. A
   missing or unresolved target cannot close its source. Our search covers one
   eliminated variable and order-preserving renaming, not arbitrary equivalence.

Coverage rises **61/83 -> 62/83**. All 24 saved split records have closed sources, while 21 originals
remain uncovered. Full history is **772,972,544 bytes / 41,912 patterns**. The
union preserves the independent arm's extra work and all earlier results.
All **187 tests pass**; independent cold replay confirms both arms, the complete
corpus and **2,921 reference nodes** with new recognition and expansion forbidden.

Resume **`experiments/results/cnf-projection-bridge/report.json`** through
**`compare_cnf_projection_bridge.restore_checkpoint`**, evidence counts
**(1, 42, 156, 24, 1)**. Load its separate **`bridges`** archive as well, and use
**`compare_cnf_projection_bridge.routes_for(h, evidence, bridges)`**. The old
five-list route constructor alone does not install the bridge. Extended positive
proofs use **`cnf_projection_bridge.verify_positive`**. Report SHA-256:
`aa68aa76ffac56fd767b0540b3ab9b683650a97ea3c4822dedb1bdd4cf4df809`.
Next source SHA-256:
`dd822fabc78af1efd220882ae9ead41593645ea916f4753c13b000b080a162b7`.

## Previous investigation: smaller stored expansion, maintenance still dominates

[Matched first-split choices on case 1299](split-cost-1299.md) retain **13 vs 29
new patterns** for initial variable **1 vs 17**, with **15,849 vs 28,842 compressed
delta bytes**. Both twelve-step paths remain structurally open, taking **12.72181
vs 12.72706 s** on two-repetition means. The difference reverses sign between
repetitions. Complete worker time is **25.58026 vs 24.82740 s**, so no faster
policy is established. Both seeds, budgets and continuation policies match;
repetition order reverses. Complete route refresh costs **11.98 vs 11.96 s**, about
**94%** of expansion. All alternatives and unsuccessful work are retained.

1. **Continue the 28-variable unresolved leaf and test common structure with
   the retained 29-variable alternative.** The selected leaf is **28 / 110 / 351**,
   SHA-256 `dd04e43d15b115ab5d60b5b4aef44d03001fcfe6910263b218b5f35776ed70ab`.
   Both leaves have exhausted ordinary probes and retain **21** clear pairs,
   with no presently acquired candidate child root. The selected leaf's current
   best rank is **[2, 2, 26, 571, 17]**. Similarity of the two leaves is an
   investigation lead, not an equivalence certificate; check exact transports,
   implications or shared components before reusing proofs across them.
2. **Avoid full route refresh after clear blocks.** Measure an incremental or
   deferred catalog update against the full implementation while continuing
   useful discovery. A clear block changes saved candidate availability even if
   it adds no forced route. Account for trace, admission and closure invalidation,
   and test later forcing and previously inactive routes. This offers a larger
   warm saving than reducing the **0.71--0.73 s** spent on acquisition/ranking.
3. **Measure decision progress separately from full structural coverage.** Each
   initial split acquires a SAT branch, while the other retains unresolved work.
   SAT witnesses can decide a source without classifying both cofactors. Preserve
   both metrics and their distinct proof requirements; do not import reference
   answers into the structural coverage count or infer a forced value from a
   closure flag.

Coverage remains **61/83** in both views. The union adds **42 unique patterns**,
**21 probe blocks** and **4 split records**; it is not one 32-state run. Full
history is **772,599,808 bytes / 41,887 patterns**; its compressed delta is
**43,317 bytes**. The complete four-arm producer takes **252.67688 s**, including
**45.38279 s** restoring the parent and **67.42831 s** preparing/checking final
global coverage. The positive proof stays at **3,043 steps**.

Resume **`experiments/results/cnf-split-cost-1299/report.json`** through
**`compare_cnf_split_cost.restore_checkpoint`**, evidence counts
**(1, 42, 156, 21, 1)**. The report hash is
`76e56eb9db1dd60c2d171c3fa0b349b68f1628c25878e61ddc90c6a2667cd1fd`.
Do not rerun the comparison to continue. The 29-variable alternative and all
earlier results remain in this authority. Neither arm establishes a minimum-cost
completion or a general SAT expansion bound.

## Previous investigation: conditional refutation transfers; 22 originals remain

[The next discovery case](transfer-1304.md) closes original **1304 / index 52**,
raising structural coverage **60/83 -> 61/83**, also without growth-exception
routes. After one clear ordinary probe, the saved split on local variable **32**
uses **10/32 admissions**. Three failed-literal reductions refute its false
cofactor; six reductions reach a twelve-variable zero-valid SAT terminal in its
true cofactor. That terminal is neither Horn, dual-Horn nor 2-CNF. All seventeen
retained split sources now close, but 22 original inputs remain uncovered.

1. **Test conditional refutation on the next uncovered original.** Case
   **1299 / index 48** has the next selected **36-variable / 162-clause /
   517-literal** leaf. Ordinary candidates **33, 34 and 36** remain at offset 12.
   No saved pair currently has a present or closed child root. After the probes,
   compare variable **17** (34- and 32-variable children, 927 total literals)
   with variable **1** (16- and 35-variable children, 617 total literals). The
   current maximum-support rank chooses 17, while 1 exposes a much smaller
   branch. Use matched snapshots and the same budget; no acquisition saving is
   measured yet. Keep failed choices and both branch obligations.
2. **Reuse proved negative cofactors as stronger forcing evidence.** In the
   completed case, the false-cofactor refutation proves that the parent entails
   variable **32=true**, despite the clear ordinary probes. The current result
   stores the split, not a new inferred-unit route. Such reuse must check the
   actual UNSAT proof, exact source and variable transport. A closure flag is
   insufficient: case 1445 had two closed SAT branches.
3. **Reduce maintenance while doing useful discovery.** Initial preparation
   remains dominant at **106.78542 s**, versus **0.20118 s** for acquisition and
   ranking and **2.01995 s** for route refresh. Retained checked sessions amortize
   that preparation. The early policy misses twice and ranks 50 pairs; seventeen
   are immediately ranked again after ordinary exhaustion. That duplicate scan
   can be removed only while retaining the exact catalog/target validity contract.

The **9,914-byte compressed delta** adds ten patterns and one continuation, with
one separate split sidecar. Full history is **771,715,072 bytes / 41,845 patterns**;
all earlier rows remain, and the positive proof has **3,043 steps**. All **181
relevant tests** pass; independent cold replay confirms every original flag and
the next selection. Resume
**`experiments/results/cnf-transfer-1304/report.json`** through
`continue_cnf_pending_warm.restore_checkpoint` with evidence counts
**(1, 42, 156, 17, 1)**. Next source SHA-256:
`6b9b95c54e6bc4dcab8c537abb5c636401c87ad995a9ae5957fa2c821c19f1b0`.

## Previous investigation: the pending split closes; 23 originals remain

[Exact pending-cofactor continuation](pending-warm-expansion.md) closes case
**1445**, raising structural coverage **59/83 -> 60/83** in both full and
without-growth views. One advance uses **20/32 admissions**. Four are previously
unfinished states reconstructed and charged again; all twenty now have completed
records. The false branch is reused with zero admissions. The true branch reaches
a **7-variable Horn, zero-valid terminal, not 2-CNF**, after four probes, four
binary-path deletions, ten eliminations and a polarity transformation. The false
branch had already reached six-variable Horn structure.

1. **Transfer this transformation sequence to the next uncovered original.**
   The retained split frontier is empty, but 23 originals remain uncovered.
   The next selected leaf is case **1304 / index 52**, **34 variables / 148 clauses /
   490 literals**. Check saved cofactor candidates and its final ordinary candidate,
   local variable **34** at offset 12. Keep exact recognition, both branch
   obligations and unsuccessful alternatives; no short chain is guaranteed.
2. **Amortize cold preparation while doing that discovery.** This run spends
   **103.25725 s** on reconstruction, routes and the first index audit, versus
   **0.05998 s** acquiring the branch and **0.98680 s** refreshing routes. Useful
   bounded sequences in a retained checked session offer a larger immediate
   total-cost opportunity than shaving this acquisition alone. Invalidate
   candidate results when traces, targets or closure change.
3. **Preserve unfinished reductions without claiming completed proofs.** Four
   admitted identities had to be recomputed because their recursive descendants
   were unfinished. A separate checked pending-reduction representation could
   preserve more of that work. Test budget cuts and restart progress explicitly;
   repeated fixed-budget retries need not progress on every reduction chain.

The **11,805-byte compressed delta** adds twenty patterns, with no new external
probe blocks or split records. Full history is **771,592,192 bytes / 41,835
patterns**; all earlier rows remain. The positive proof has **2,948 steps**.
All **181 relevant tests** and independent cold reconstruction of the complete
original coverage flags and next selection pass. The exact resume authority is
**`experiments/results/cnf-pending-warm/report.json`**,
using `continue_cnf_pending_warm.restore_checkpoint`, with evidence counts
**(1, 42, 156, 16, 1)**. Next source SHA-256:
`bef0f0de793f31155199f7c6a8dba7819495f90e23de8817a9967edc55880f35`.

## Previous investigation: conditional early-reuse gain and a pending Horn route

[The paired comparison](early-closed-expansion.md) shows an actual scheduling gain
on case **1445**: early closed-cofactor reuse skips two clear blocks, taking
**6 rather than 8 advances** and **6.27974 rather than 8.08296 seconds** for expansion
(22.31%). Both policies reach the same 32-state boundary and identical pattern
records. Full worker saving is **13.52%**, with preparation and delta persistence.
On forcing control **1189**, the successful proof is preserved but expansion is
**1.64% slower** because eight failed early searches add checking. Keep this
regression: the policy is a candidate with conditional benefits.

The current source splits at **27 variables / 93 clauses / 287 literals**. Its
false cofactor closes through 24 states and a polarity transformation to a
**6-variable Horn terminal, not 2-CNF**. The true **23 / 70 / 196** cofactor remains
pending after four additional unfinished admissions. Overall coverage is still
**59/83**. The cap accounts for entered states, including unfinished ancestors:
32 admissions correspond to 28 new completed pattern rows in this run.

1. **Resume the exact pending true cofactor.** It belongs to the saved split on
   local variable **4**; its false branch is already closed. Reuse every completed
   descendant and record the cost of reconstructing unfinished work. Pending target
   SHA-256: `69d0f3cad2b4d527495373e3fecf905d0c538d98adb833dbd0373598cfb0280e`.
   Do not rerank the parent or interpret the admission cap as a hardness result.
2. **Reduce repeated unsuccessful candidate checking.** Early search ranks 94
   pairs on each case, versus 41 and 15 for probe-first; acquisition is slower in
   both comparisons. Test checking only novel trace pairs, with exact invalidation
   when targets are admitted or routes/coverage change. Retain the forcing control
   and charge recognition before claiming an improvement.
3. **Keep total maintenance costs visible while expanding coverage.** Route
   refresh still dominates the warm arms. Final whole-corpus checking costs
   **60.00692 s**, beyond **7.44994 s** of route preparation; current/control
   reconstruction costs **32.97981 / 25.34922 s**. Broader unlabelled and adversarial
   cases remain needed; a short closed-cofactor chain need not exist for every CNF.

Both arms' results and all previous evidence are retained. The combined
**19,191-byte compressed delta** adds 28 patterns and six probe blocks, plus two
split records; full history is **771,342,336 bytes / 41,815 patterns**. Each arm
had its own 32-state allowance; the merged checkpoint is not one such experiment.
All **181 relevant tests** and independent cold replay of all four arms pass.
Resume **`experiments/results/cnf-early-closed/report.json`** with
`compare_cnf_early_closed.restore_checkpoint`, preserving evidence counts
**(1, 42, 156, 16, 1)**. Continue from the merged checkpoint rather than rerunning
the comparison. The pending split source SHA-256 is
`6be85c519f3e56d3096ab3e1ed2ad63597d70459193d435d885457fca290ca39`.

## Previous investigation: reuse a closed cofactor before exhausting probes

[The next original-frontier batch](original-warm-expansion.md) reaches case **1445**,
whose smallest selected residual has **33 variables / 121 clauses / 359 literals**.
Two saved splits reuse one existing empty-CNF terminal, and binary-path deletion
plus elimination leave a single open **29 / 103 / 307** residual. The batch uses
**7/32 admissions**; structural coverage remains **59/83**. This is partial transfer
of the previous transformation sequence, not another original-level closure.

The largest repeated warm cost is still full route maintenance: **11.55914 s**
versus **0.20427 s** for acquisition. Initial complete preparation costs **94.52082 s**.
The selected split traces were already present in their source nodes, yet seven
clear ordinary blocks preceded their use, incurring **6.73336 s** of route refresh.

1. **Test early reuse of an already closed cofactor.** On the current leaf, saved
   local variable **12** yields one checked closed child and one missing cofactor
   of **28 variables / 281 literals**. Compare taking that pair now against the
   six remaining ordinary candidates **18, 20, 23, 24, 28, 29**, starting at offset
   12. Charge recognition/ranking and preserve both structural obligations. Keep
   case 1189 as a contrasting control where probing found a useful forced value.
   Early splitting can lose that opportunity; no counterfactual saving is yet measured.
2. **Avoid repeated global maintenance for clear-only blocks.** Ten of twelve
   advances add clear probe records without new states or forced edges. An exact
   append path could update probe-prefix maps without refreshing unchanged coverage
   rules, but must preserve catalog completeness and pending-target activation.
   Work on this alongside discovery rather than replacing the discovery objective.
3. **Expand beyond this selected path.** Twenty-four originals remain uncovered.
   The new original selector prevents an empty retained frontier from ending all
   work, but its smallest-support ranking is a heuristic. Arbitrary CNFs need not
   have a closed cofactor or a short chain of such reductions.

All **176 relevant tests** and independent checkpoint reconstruction pass. The
**14,150-byte compressed delta** adds seven patterns and ten probe blocks, with two
separate split records. Full history is **770,924,544 bytes / 41,787 patterns**;
all old rows remain. Resume **`experiments/results/cnf-original-warm/report.json`**
through `continue_cnf_original_warm.restore_checkpoint`, retaining evidence counts
**(1, 42, 156, 14, 1)**. The active leaf SHA-256 is
`ef925b9a7d10a3bab64accecd2ce12015dfa400b13bc949f39781e28c55069f8`.

## Previous investigation: a warm batch closes another original

[Eight retained-session advances](warm-expansion-batch.md) raise structural
coverage **58/83 -> 59/83**, closing original case **1189** (48 variables / 204
clauses). A forced value on the 22-variable source exposes five binary-path
deletions and six eliminations, leaving a 15-variable residual. After its ordinary
probes are exhausted, a retained split reaches two checked 2-CNF terminals.
Both branches close; the reference solver confirms both SAT. The session uses
**21/32 admissions** and propagates closure through 65 sources per coverage graph.

Actual discovery takes **0.11884 s** across eight steps; complete external-route
refresh takes **7.59057 s**. Warm composition/checking totals **1.30709 s full /
0.30604 s incremental**, giving an indicated **11.00%** saving after selection,
acquisition and refresh. Initial reconstruction/preparation/auditing still costs
**91.13181 s**. Saved split-trace replay is slightly slower than fresh propagation
on this one pair; the regression is retained. No unrestricted bound follows.

1. **Select another uncovered original or a learned base.** The retained split
   frontier is now empty, while **24/83 original inputs remain uncovered**. Use
   `continue_cnf_original_splits.select` / `selected_frontiers` to seed a new
   original; merely rerunning the retained-frontier batch would find no work.
   The learned queue still has **17 ready bases / 88 candidates**. Its smallest
   ready source has 33 variables / 359 literals and eight remaining candidates
   at offset 24; its exact identity is in the new discovery note.
2. **Transfer the observed transformation sequence.** Search for forced
   restrictions that expose redundant wide clauses through binary implications,
   permit bounded elimination, and leave small splits into recognized families.
   Compare saved evidence and residual ranks across the remaining originals;
   do not infer that every CNF has a short such sequence.
3. **Reduce complete-route maintenance while doing useful discovery.** Eight
   refreshes cost much more than acquisition. A future delta catalog must track
   all pending-target dependencies and preserve exact completeness. Keep the
   initial cold semantic audit and archive/persistence cost explicit.

All **160 relevant tests** and fresh checkpoint reconstruction pass. The
**15,484-byte compressed delta** adds 21 patterns and seven probe blocks;
one split sidecar is added. History is **770,707,456 bytes / 41,780 pattern nodes**,
with every old row preserved. The positive proof now has **2,828 steps**.
Resume from **`experiments/results/cnf-warm-batch/report.json`** through
`continue_cnf_warm_batch.restore_checkpoint`, preserving evidence counts
**(1, 42, 156, 12, 1)**. No new full graph snapshot was written.

## Previous investigation: incremental coverage and the cold-cost boundary

[Incremental coverage](incremental-coverage.md) retains the complete finite rule
graph and updates affected obligations after the saved forced expansion. In the
full and without-growth graphs together, it checks **four option sources** rather
than visiting **25,605** again. Warm composition plus original proof checking
averages **0.26146 -> 0.03949 seconds**. The two full-control samples vary
substantially; including the shared **0.94030-second** complete route refresh
gives an indicated **18.47%** saving, not 84.90% for the whole update.

The important limit is cold cost: initial index construction costs **55.68532 s**;
cold replay is **64.41089 s**, versus **62.62709 s** for full recomposition.
Serializing the complete pair costs **7.96452 s** and adds **11,241,021 compressed
bytes** (94,113,609 raw JSON bytes). Most of the previous 55-second composition
cost is historical semantic validation, already avoided by keeping ordinary
verifier caches warm. It is not all a saving attributable to the new index.

1. **Advance discovery within one bounded warm session.** Reuse the checked
   inventory and graph across useful advances, charging restoration and first
   construction once. On the unchanged **22-variable / 88-clause** leaf, ordinary
   candidates are **16, 18, 21, 22**, and saved split pairs rank **13, 5, 6, 11**.
   Preserve one admission allowance and every new delta. Avoid another isolated
   verification-only tuning run before using this support for actual discovery.
2. **Track complete external-route dependencies.** Global route refresh now costs
   more than the warm composition update. A future exact delta path must include
   pending routes activated by newly acquired targets, even without new route
   records. Current code deliberately still refreshes and compares the entire
   checked catalog; partial positive maps cannot establish completeness.
3. **Reduce cold revalidation and persistence cost with explicit evidence.** The
   full catalog audit still loads 22,603 historical nodes. Two graph snapshots
   duplicate most keys, and full serialization costs more than a warm update
   saves. Preserve the measured cold regression; do not deploy this index as an
   automatic replacement for isolated cold composition.

All **156 relevant tests** pass, including 4,096 exhaustive small graph/base
combinations, mixed AND/OR update sequences, corruption and real pending-target
admission. Cold graph replay and full recomposition agree at **58/83**. No new
SAT category or recognition node is acquired by this study. The reusable index
is in **`experiments/results/cnf-incremental-coverage/`**; the authoritative
discovery checkpoint remains **`experiments/results/cnf-local-forcing/report.json`**,
resumed through `continue_cnf_local_forcing.restore_checkpoint` with all five
evidence lists **(1, 42, 156, 11, 1)**. Append-only rules, immutable pattern payloads
and fixed policy are required; deletions/rebindings require a rebuild.

## Previous investigation: forced reduction and the global-composition cost

[Source-local forced expansion](source-local-forcing.md) proves source variable
**22=true** and shrinks the open leaf **23 variables / 93 clauses / 288 literals
-> 22 / 88 / 272**, admitting one unresolved state. The continuation and target
are persistent and cold-checked. Coverage stays **58/83**; the target remains open.

The local worker takes **0.13717 s** versus **10.03384 s** for eager preparation,
acquisition and export, with authority already reconstructed. Its working SQLite
is **126,976 bytes**, while the full authority is still required. Actual advance
and target recognition are slightly slower. The larger measured costs are now
**55.48722 s global composition/checking**, **21.99791 s initial reconstruction**
and **6.47823 s global route preparation**. Global validation retains 22,603 nodes
and 191,717,696 node-JSON bytes; this is not measured peak RAM.

1. **Continue discovery on the smaller leaf.** Next ordinary candidates are
   **16, 18, 21, 22**; saved split pairs rank **13, 5, 6, 11**. Compare useful work
   under one allowance. These identifiers are local to the new normalized source:
   new variable 22 denotes old variable 23, not the forced variable removed.
   The broader learned queue still has 17 ready bases / 88 candidates.
2. **Update only affected coverage obligations.** Global recomposition is now
   the largest measured cost. Persist a complete rule/reverse-dependency index,
   check new edges, retain both split obligations and invalidate pending/negative
   results when their premises change. Establish that contract before replacing
   complete composition; a partial positive catalog cannot certify noncoverage.
3. **Amortize restoration across useful advances.** Preserve the full authority
   and all five evidence lists, charge its first reconstruction, and use bounded
   batches. Extend source-local access to split and learned dependencies only as
   needed by the next discovery step. A small local working store is not a bound
   on all dependencies or on arbitrary SAT expansion.

All **148 relevant tests** pass; independent reconstruction and positive replay
succeed. The **4,447-byte compressed delta** adds one continuation and one node;
full history is now **770,371,584 bytes / 41,759 pattern nodes**. Resume through
`continue_cnf_local_forcing.restore_checkpoint` using
**`experiments/results/cnf-local-forcing/report.json`**, with evidence counts
**(1, 42, 156, 11, 1)**. The active leaf SHA-256 is
`545c51d457452dc1fd3dec970e5eadc1f85ba4012c889be2164277966968bf29`.

## Previous investigation: source-local ordinary expansion with exact membership

[Source-local expansion](source-local-expansion.md) saves the checked clear
window for **7, 9, 16, 17** on the 23-variable / 93-clause leaf. An empty working
store consults full read-only history on every missing identity, validates old
premises and exports only novel rows. The matched one-block worker falls from
**10.99932 to 0.12683 s (98.85%)**, including preparation and delta export;
working SQLite is **94,208 bytes**, with the **770,338,816-byte authority still
required**. First restoration costs **20.59393 s** separately. Probing itself is
slightly slower. This is not a full-pipeline or arbitrary-SAT speedup.

1. **Advance the leaf using the next ordinary block versus retained splits.**
   Ordinary candidates are now **18, 21, 22, 23**; saved split pairs remain
   **5, 6, 11, 13**. Use a shared admission allowance. The wider learned queue
   still has 17 bases / 88 candidates. Avoid rediscovering the new saved window.
2. **Extend exact local access to split traces and learned antecedents.** The
   ordinary-stream API has checked prefix and authoritative membership semantics,
   but is not a complete route catalog or global frontier selector. Add only the
   source-bound dependencies needed by the next operation, and retain explicit
   sidecar membership and recomposition obligations. No local absence may imply
   novelty, probe exhaustion or exclusion elsewhere.
3. **Amortize the now-dominant restoration when doing useful discovery.** Keep a
   verified authority available across a bounded batch, charging preparation,
   merge and cold checking. The current local worker avoids full copying, eager
   route preparation and full-table delta comparison; first construction and
   archive storage remain. Further positive-only replay tuning is lower priority.

All **146 relevant tests** pass. The new delta is **2,025 compressed bytes**, adds
one clear window and no pattern nodes, and changes no closure edge. Coverage
remains **58/83**. Full history grows to **770,347,008 bytes**, with all prior
records preserved. Resume using `continue_cnf_source_local.restore_checkpoint`
on **`experiments/results/cnf-source-local-checked/report.json`**, preserving all
five inherited lists **(1, 42, 156, 11, 1)**. The older `cnf-source-local/` directory
is a preserved preliminary run with invalid delta metadata, not a checkpoint.

## Previous investigation: standalone positive data without lineage reconstruction

[The positive data bundle](positive-proof-bundle.md) preserves the same 58 roots
and 2,748 proof steps using **2,797 pattern rows + 82 external-record rows** and
all five sidecar lists. Independent processes replay outside the repository's
working directory with lineage restoration disabled. Mean complete cold process
time falls **23.95282 -> 3.03614 s (87.32%)**; semantic replay remains about 2.7 s.
The artifact is **3,169,051 compressed bytes** and reconstructs **40,538,112 bytes**
of temporary SQLite, versus 770,338,816 bytes for full history. Original storage
is preserved; this adds a reusable artifact rather than shrinking the archive.

1. **Connect positive reuse to a source-local open-frontier working state.** The
   bundle now removes full restoration for positive replay, but discovery still
   uses the old full preparation/audit path. Establish the exact frontier records
   and completeness/admission contracts before partial resumption. A missing row
   in this bundle proves neither novelty nor probe exhaustion. Preserve all
   existing results, check any new delta against authoritative history, and charge
   that work. Avoid repeatedly optimizing the now-small positive replay alone.
2. **Advance the unchanged 23-variable / 93-clause leaf.** Compare ordinary
   candidates **7, 9, 16, 17** with saved pairs **5, 6, 11, 13** under one shared
   admission allowance. The wider learned queue remains 17 bases / 88 candidates.
   The bundle provides no added coverage or efficient classification of all CNFs.
3. **Retain production and warm costs.** First-bundle production still pays
   **20.82422 s restoration + 2.78123 s capture + 1.53465 s serialization/compression**,
   plus integrity/diagnostic work. The previous warm regression remains; no new
   validation cache was introduced. Unused sidecar records and historical fields
   remain packaged. Shrinking them is secondary to making expansion reuse work.

All **139 relevant tests** pass; consumer checks match the same 471 historical
nodes across both policies. Results and a separately reviewable claim file are
in `experiments/results/cnf-positive-bundle/`. This is positive-proof data, not a
discovery checkpoint or complete catalog. Continue discovery from
`cnf-reused-branch/report.json` with full evidence counts **(1, 42, 156, 11, 1)**.

## Previous investigation: sufficient positive checks without historical search replay

[Hybrid primitive replay](positive-primitive-replay.md) checks the same 2,748-step
graph and 58 roots. Mean cold replay falls **30.15238 -> 2.71821 seconds (90.99%)**
over two repetitions in reversed order. Direct checks handle 2,687 internal
steps; five subsumption steps and 56 external rules retain their original
validators. Full historical checking falls **11,955 -> 471 nodes**, while the
total distinct inventory rows read falls **11,955 -> 2,797**. The difference
matters: selected steps still require real semantic checks and row reads.

1. **Reduce preparation through a sufficient selected-proof bundle and explicit
   frontier dependencies.** Restoration now costs **20.91624 s**, versus
   **2.71821 s** for positive replay. The checker still reads the old full rows
   and sidecars; 49 historical dependencies remain outside the graph. Export and
   validate the actually required records before attempting partial reconstruction.
   Discovery also needs its open frontier; missing records cannot certify a
   complete catalog, exclusion or exhaustion. The old full-audit path remains.
2. **Resume bounded discovery on the 23-variable / 93-clause leaf.** Coverage is
   unchanged. Compare ordinary candidates **7, 9, 16, 17** with saved pairs
   **5, 6, 11, 13** under one shared admission allowance. The wider learned queue
   retains 17 bases / 88 candidates. This replay improvement is supporting work,
   not an added tractable SAT family or an arbitrary-input resource bound.
3. **Keep the warm-cache tradeoff explicit.** Mean warm replay regresses
   **0.25349 -> 1.88878 s** because direct steps are rechecked. A separate positive
   cache would need exact source/proof/configuration/data bindings. Never insert
   weaker positive results into historical validation caches or replace their
   stronger audit contract. No peak-RAM saving has been measured.

All **132 relevant tests** pass. Historical checked-node JSON drops from
97,225,536 to 3,096,763 bytes, but direct graph reads add 18,568,514 bytes and the
graph, keys, sidecars and other caches still occupy memory. SQLite remains
**770,338,816 bytes / 41,758 nodes**. Results are preserved under
`experiments/results/cnf-positive-primitives/`; this is not a discovery checkpoint.
Resume `cnf-reused-branch/report.json` with evidence counts **(1, 42, 156, 11, 1)**.

## Previous investigation: explicit proof obligations across both verifier policies

[The expanded proof](expanded-coverage-dependencies.md) turns 593 outer steps
into **2,748 explicit steps**, including 115 retained-plan references. It verifies
the same 58 roots and exposes 2,155 hidden steps. The accounting audit also
corrects the earlier omission of the prepared-policy cache: selected replay
checks **11,955 nodes / 97,225,536 node JSON bytes**, not just the 10,258 nodes in
the current-policy view. The earlier timing measurements already included both.

1. **Build a sufficient primitive checker for the expanded positive graph.**
   **9,207 checked nodes / 78,657,022 node JSON bytes** lie outside its explicit
   structural steps. They include external evidence dependencies; do not assume
   all are removable. Start by separating the selected transformation's logical
   premises from prior failed recognizers, candidate ranking and losing plans.
   Preserve exact bindings, retained references and both conditioning branches.
   The graph is not yet self-contained, and cold expanded replay remains slower
   in the one measured run (**34.50104 versus 30.51477 seconds**).
2. **Continue bounded discovery on the unchanged open leaf.** The **23-variable /
   93-clause** source retains pairs **5, 6, 11, 13**. Compare ordinary candidates
   **7, 9, 16, 17** with those splits under one shared admission allowance. The
   wider learned queue remains 17 bases / 88 candidates. This study adds no root
   coverage or new tractable family.
3. **Integrate only after defining what is still checked.** A positive proof
   subset is not a complete discovery catalog or an archive audit. Charge both
   verifier views, source/sidecar preparation, reconstruction and persistence;
   do not infer total memory from the outer proof length or JSON payload alone.

Reproduction and correction records are in `experiments/results/cnf-expanded-coverage/`.
Resume discovery from `experiments/results/cnf-reused-branch/report.json` through
`continue_cnf_reused_branch.restore_checkpoint`, retaining all five lists
**(1, 42, 156, 11, 1)** and earlier sidecars. SQLite remains **770,338,816 bytes /
41,758 nodes**. The 57-test suite and fresh expanded-proof replay pass.

## Previous investigation: selected positive replay and its real dependency cost

[Selected-route verification](selected-route-verification.md) preserves the
593-step positive proof for 58/83 roots while checking only its external route
dependencies. Mean cold replay falls **35.72304 -> 30.35446 seconds (15.03%)**
over two repetitions with reversed order. Corrected counts across both verifier policies fall **13,211 -> 11,955**;
node JSON payload falls **109,165,321 -> 97,225,536 bytes**. The original count
omitted 1,697 prepared-policy nodes; the timing samples are unchanged. Archive bytes and
coverage are unchanged. This measures positive replay, not complete expansion.

1. **Expand the successful proof's internal dependencies before pruning them.**
   The 593 explicit steps still require **11,362 additional inventory nodes**.
   Internal profiles, all stored alternatives, summaries and retained-plan
   premises remain checked. Determine which support the successful semantic plan
   and which only reconstruct historical policy. Do not assume all additional
   nodes are dispensable, or that a base step is a constant-cost axiom.
2. **Continue bounded discovery on the unchanged 23-variable leaf.** Saved pairs
   **5, 6, 11, 13** need two missing children each; compare the next ordinary block
   **7, 9, 16, 17** before conditioning. Follow the saved split descendant with
   one admission allowance. The wider learned queue remains 17 bases / 88
   candidates; no new family or root was added by this verification study.
3. **Integrate positive replay without losing discovery or audit coverage.**
   `verify_selected_plan` returns a positive-only subset. Its missing routes
   cannot justify exclusion, exhaustion or UNSAT. Old expansion runners still
   reconstruct the full catalog and perform full audits. A next integration must
   combine positive reuse with the actual open-frontier dependencies and measure
   all preparation, reconstruction, persistence and checking costs.

The comparison is retained in `experiments/results/cnf-selected-routes/`; its
report is a study, not a new reconstructible discovery checkpoint. Resume
`experiments/results/cnf-reused-branch/report.json` through
`continue_cnf_reused_branch.restore_checkpoint` and preserve five lists
**(1 rewrite, 42 bases, 156 augmented blocks, 11 splits, 1 affine family)** and
all earlier sidecars. The inventory remains **770,338,816 bytes / 41,758 nodes**.
Peak RAM and a full-pipeline speedup remain unmeasured.

## Previous investigation: reuse one cofactor and retain the smaller obligation

[The reused-branch expansion](reused-branch-expansion.md) acquires variable 7's
missing false cofactor while sharing its checked empty true cofactor. Three new
recognition states reduce case 30's open leaf **25 variables / 99 clauses ->
23 variables / 93 clauses**. Coverage stays **58/83**, with no pending children.
The independent solver confirms both cofactors SAT; structural coverage remains
a separate objective.

1. **Compare bounded probing with the saved pairs on the 23-variable leaf.**
   Pairs **5, 6, 11, 13** each need two missing children; the best current rank
   is **[2, 2, 20, 376, 5]**. No common-value/equivalence rewrite or directly
   extracted affine equation is found. The next ordinary block is **7, 9, 16,
   17** (17 candidates remain); the wider learned queue has **17 bases / 88
   candidates**. Preserve the new normalization and both branch obligations.
   Check for useful reusable cofactors between blocks instead of requiring probe exhaustion, and share a single admission
   allowance across bounded local work. Use `frontier-profiles.json.gz` and
   `next-options.json.gz`; do not revisit the exhausted 25-variable parent.
2. **Reduce global verification overhead.** Acquisition takes **0.02474 s** but
   the pipeline **271.17740 s**: preparation **65.75065 s**, full audit
   **106.37684 s**, cold routes **63.97337 s**. Measure the dependency closure of
   the retained **593-step positive witness** before implementing selective
   verification. Source/configuration bindings and inherited premises must still
   be checked; explicit witness length alone is not the checking cost.
3. **Account for growth and incomplete reuse.** Elimination reduces support but
   grows 92 clauses / 281 literals to **93 / 288**. New recognition still performs
   36 probe attempts; sharing the chosen source pair does not make all child
   inference reusable. SQLite adds **49,152 bytes** to **770,338,816 bytes /
   41,758 nodes**, compressed delta **4,841 bytes**, sidecars additional. No new
   tractable family, peak-RAM reduction or unrestricted resource bound is proved.

Resume `experiments/results/cnf-reused-branch/report.json` through
`continue_cnf_reused_branch.restore_checkpoint` and `routes_for`. Preserve five
lists **(1 rewrite, 42 bases, 156 augmented blocks, 11 splits, 1 affine family)**
and earlier sidecars. The 37-test suite, full audit and **171.36780 s** independent
cold replay pass; all 1,977 reference nodes survive within 1,998.

## Previous investigation: bounded batches preserve evidence and avoid preparation

[The matched batch experiment](frontier-batching.md) tests all **17** remaining
ordinary candidates on case 30's **25-variable / 99-clause** leaf in one bounded
pass. Five clear blocks and one exhausted advance preserve **21 saved pairs**;
no state is admitted and coverage stays **58/83**. All six prefixes and final
logical tables match the sequential preparation control under the same shared
allowance. Instrumented search takes **0.31960 s versus 5.46878 s**; **5.14561 s**
is repeated route preparation avoided by batching.

1. **Acquire the retained variable-7 split, or compare another inference.**
   Its true branch is the shared empty-CNF terminal; only the false branch
   (**24 variables / 94 clauses / 287 literals**) is missing. It ranks first
   among 21 saved pairs and was already available in the first new window.
   Check cofactor opportunities between blocks instead of requiring exhaustion.
   No common-value/equivalence rewrite is found. Variables **2, 4, 12, 21** are
   outside the binary pool; their unit-free restrictions cannot start unit
   propagation, so extra single-assumption tests add no deduction. The other
   **17 learned bases / 88 candidates** remain available.
2. **Address cold verification of complete positive plans.** Initial preparation
   is **65.62419 / 70.54924 s** in the two arms, full audit **111.99494 s**, cold
   routes **66.03018 s**. The control keeps its inventory cache warm; its five
   route rebuilds are much cheaper than five cold restarts. Profile and implement
   dependency-local verification with exact source/configuration binding. The
   retained positive witness has **593 explicit steps for 58 roots**; its full
   checking dependency closure still needs measurement. Batching
   does not remove global initial preparation or audit.
3. **Keep the measurement's scope explicit.** Preparation plus instrumented search
   is **65.94379 / 76.01801 s**, but initial-preparation variation is not an
   established batching effect. The **358.12190 s** experimental pipeline includes
   both arms. SQLite adds **53,248 bytes** to **770,289,664 bytes / 41,755 nodes**;
   compressed delta **2,990 bytes**, other archives additional. No new family,
   original coverage gain, peak-RAM reduction or unrestricted bound is established.

Resume `experiments/results/cnf-frontier-batch/report.json` with
`continue_cnf_frontier_batch.restore_checkpoint` and `routes_for`, preserving
five evidence lists **(1, 42, 156, 10, 1)** and all earlier sidecars. The targeted
**37-test** suite, full audit and **169.35837 s** independent cold replay pass.
Use `frontier-profiles.json.gz` and `next-options.json.gz` for source-bound next
steps. Repeating this batch on the now-exhausted source cannot expand coverage.

## Previous investigation: forced propagation reduces the retained obligation

[The forced-frontier continuation](frontier-forcing.md) reduces case 30's open
leaf **27 variables / 111 clauses -> 25 variables / 99 clauses** with **three
new recognition states**. Variable 19 is clear; assuming normalized variable 24
false produces a checked contradiction, so only its true restriction is acquired.
Binary-path deletion and elimination expose the new unresolved leaf. Structural
coverage remains **58/83** and all previous results survive.

1. **Continue discovery in a bounded batch.** The new leaf's saved pairs are
   **5, 6, 8, 11**; compare them with ordinary candidates **13, 15, 7, 9**.
   Seventeen ordinary candidates remain and no affine equation is directly
   extracted. Use the saved split frontier. Test several steps/sources in one
   bounded search with a shared admission allowance, preserving every record and
   comparing with its sequential prefix. Avoid another full restore/audit for
   each individual block. The separate **17 learned bases / 88 candidates** remain.
2. **Reduce complete-plan verification to its dependencies.** Acquisition costs
   **0.02582 s**, whereas the pipeline takes **277.21655 s**. Preparation, audit
   and cold routes dominate. Batching's saving still needs measurement, and
   dependency-local checking remains open. All four competing saved pairs need
   two missing children, but their acquisition costs were not measured; the
   forced route is not proved globally cheapest.
3. **Keep resource and coverage limits explicit.** SQLite adds **57,344 bytes**
   to **770,236,416 bytes / 41,755 nodes**; compressed delta **6,081 bytes**, with
   sidecars and reference snapshots additional. Elimination briefly increases
   clauses/literals. No original gain, peak-RAM reduction, new family or general
   polynomial expansion bound is established.

Resume `experiments/results/cnf-frontier-forcing/report.json` through
`continue_cnf_frontier_forcing.restore_checkpoint` and `routes_for`. Keep five
lists: **1 rewrite, 42 bases, 156 augmented blocks, 10 splits, 1 affine family**,
plus earlier sidecars. The targeted 33-test suite, full audit and **174.55350 s**
independent cold replay pass and are recorded in this checkpoint. All 1,949 old reference nodes survive
within 1,977. Exact next-source coordinates are in `frontier-profiles.json.gz`.

## Previous investigation: compare lookahead with retained conditioning

[The original-frontier comparison](frontier-option-comparison.md) reduces case
30's obligation **29 variables / 120 clauses -> 27 variables / 111 clauses**,
with **three new recognition states**. Coverage stays **58/83**. One ordinary
block and the last block on its retained learned base are clear; both are saved.
Ranking all twenty pairs still chooses variable 24. Its false branch reuses the
empty-CNF terminal; elimination and binary-path deletion leave the true branch open.

1. **Compare saved pairs with probing on the new 27-variable leaf.** Its saved
   pairs are **11, 5, 8, 15**; the next ordinary block is **19, 24, 9, 13**.
   Nineteen ordinary candidates remain, and no affine equation is directly
   recognized. Use the external split frontier, not the older original parent.
   The older learned base is exhausted; the other **17 bases / 88 candidates**
   remain available. Probe exhaustion is not required before a justified split.
2. **Check complete plans from their actual dependencies.** Local acquisition
   costs **0.02748 s**, but the pipeline costs **270.71536 s**, plus **82.05829 s**
   of preflight work. Preparation, full audit and cold routes dominate. The empty
   branch already witnesses SAT; completing the other branch addresses structural
   coverage. The local two-trace control is not a full-solver speedup measurement.
3. **Retain the limits and all evidence.** SQLite adds **57,344 bytes** to
   **770,179,072 bytes / 41,752 nodes**; delta **5,746 compressed bytes**, with
   learned evidence, diagnostics and reference snapshots additional. Reduced
   support briefly increases literal count. No new original closes and these
   are reused development cases. A state allowance does not bound total cost.

Resume `experiments/results/cnf-frontier-comparison/report.json` with
`continue_cnf_frontier_comparison.restore_checkpoint` and `routes_for`.
Keep **five lists**: 1 rewrite, 42 learned bases, **156 augmented blocks**,
**10 splits**, 1 affine family, and all earlier lemma sidecars. The targeted
41-test suite, full audit and **176.26154 s** independent cold replay pass; see
`validation.json`. All 1,940 reference nodes survive within 1,949. The open source
and its exact candidates are retained in `frontier-profiles.json.gz`.

## Previous investigation: saved cofactors complete the non-affine original

[The completed probe pool and split](exhausted-probe-split.md) raise structural
coverage **57/83 -> 58/83**. The last ordinary probe is clear. Ranking all five
saved pairs selects variable 10: its true branch is the shared empty-CNF terminal;
seven new states reduce the false branch to Horn form. Both plans close case 73,
and all nine saved split sources are now closed with no pending child.

1. **Return to the original-input frontier.** There are **27 selected leaves
   across 25 open originals**. The smallest is **case 30: 29 variables / 120 clauses
   / 362 literals**. Compare its saved pair ranks with the next ordinary block
   **7, 10, 16, 18** (five more follow) and the separate learned-clause route.
   Probe exhaustion is not a prerequisite for a justified split; this run
   selected a pair that was already available before the new probe. The alternative queue retains **18 bases / 92 candidates**,
   including four previously untried augmented candidates on case 30. The saved
   split frontier is empty, so repeating the last runner unchanged is inapplicable.
2. **Reduce complete-plan verification to its actual dependencies.** The new
   window costs **0.00181 s**, pair acquisition **0.01667 s**; total pipeline cost
   is **270.70538 s**. Preparation (66.55717 s), full audit (108.42947 s) and cold
   routes (64.45513 s) dominate. Saved two-trace replay is slower in the tiny local
   control (0.000430 versus 0.000349 s fresh); no reliable timing advantage follows.
   An empty cofactor already witnesses SAT: distinguish early decision from
   acquiring both branches for complete structural coverage.
3. **Control retained space and establish generality.** SQLite adds **90,112
   bytes** to **770,121,728 bytes / 41,749 nodes**. The delta is **5,411 compressed
   bytes**, plus sidecars. This is another reused development case, not a holdout
   or arbitrary-SAT guarantee. A 32-state allowance does not bound total work.

Resume `experiments/results/cnf-probe-split/report.json` with
`continue_cnf_probe_split.restore_checkpoint` and `routes_for`. Preserve all five
evidence lists, now including nine splits, and earlier lemma sidecars. Thirty-eight
targeted tests, the full audit and **167.82586 s** independent cold replay pass.
Reference proofs retain all 1,906 old nodes within 1,940. The independent cold validator replays selection before adding
new child states; see `validation.json` and `open-originals.json.gz`.

## Previous investigation: a forced literal exposes a ten-variable obligation

[Probe continuation below the saved split](original-frontier-probe.md) reduces
case 73's open leaf **13 variables / 62 clauses -> 10 variables / 44 clauses**.
One failed literal unlocks two eliminations and binary-path deletion, with four
new recognition states. Coverage stays **57/83**; all previous evidence survives.

1. **Test the one remaining ordinary variable, 7, on the ten-variable leaf.**
   Saved pairs cover 10, 3, 5 and 6. If the new pair is clear, preserve it and
   rank exact cofactor splits. The leaf has no directly extracted affine equation.
   Use the retained split frontier, not the selected original view of its older
   parent. The 18-base / 92-variable alternative learning queue remains available.
2. **Check complete positive plans from their actual dependencies.** Acquisition
   costs **0.02000 s**; preparation **69.25253 s**, full audit **115.65564 s**, cold
   routes **65.40336 s**, total **282.11723 s**. Local support reduction does not
   establish a whole-solver runtime improvement. Compact local replay alone is
   insufficient to justify a complete positive coverage plan.
3. **Bound retained space and test generality.** SQLite adds **57,344 bytes** to
   **770,031,616 bytes / 41,742 nodes**. The new delta is **6,225 compressed bytes**;
   sidecars are additional. No original gain or independent holdout gain occurs,
   and the 32-state admission cap is not a polynomial-time or peak-RAM bound.

Resume `experiments/results/cnf-original-probe/report.json` with
`continue_cnf_original_probes.restore_checkpoint` and `routes_for`. Keep all five
evidence lists, including eight splits and the affine family certificate, plus
earlier lemma sidecars. The full audit, 29 targeted tests and **164.19006 s**
independent cold replay pass. Reference proofs preserve all 1,898 old nodes within
1,906. See `validation.json` for the
independent cold replay and `frontier-profiles.json.gz` for the exact next source.

## Previous investigation: saved conditioning exposes a smaller non-affine leaf

[The original-frontier split](original-frontier-split.md) chooses case 73's
20-variable / 80-clause leaf without using its label, ranks all fourteen retained
pairs, and splits on variable 18. **Ten new recognition states** close the true
branch and reduce the false branch to **13 variables / 62 clauses / 219 literals**.
Coverage stays **57/83**; both cofactors are independently SAT, but one structural
obligation remains open. The affine closure and all older evidence survive.

1. **Finish the four untried probes on the new 13-variable leaf.** Its saved
   attempts cover variables 6, 9, 12 and 13; ordinary candidates **1, 4, 7 and 8**
   remain. Pay for that single block before another conditioning layer. If it is
   clear, retain the evidence and compare a newly saved split or proved clause
   augmentation. The leaf still has zero directly extracted parity equations.
   Use the external split frontier; selected original routes still expose its
   older parent. The 18-base / 92-variable alternative learning queue remains.
2. **Reduce complete-plan checking cost from actual dependencies.** Acquisition
   costs **0.04525 s**; preparation **65.86672 s**, full audit **107.92519 s**, cold
   routes **63.93178 s**, total **267.75550 s**. The matched two-trace control is
   one tiny sample and establishes no robust speedup. Preserve the distinction
   between a compact local fact and a fully justified positive coverage plan.
3. **Keep retained-space and generality limits explicit.** SQLite adds **126,976
   bytes** to **769,974,272 bytes / 41,738 nodes**. The delta is **8,671 compressed
   bytes**, plus sidecars. Smaller support does not shrink history. A 32-state
   admission allowance does not establish polynomial expansion or bounded RAM.

Resume `experiments/results/cnf-original-split/report.json` using
`continue_cnf_original_splits.restore_checkpoint` and `routes_for`. Preserve
**five evidence lists**, now including **eight splits**, 42 learned bases, 155
augmented blocks and the affine family record, plus earlier lemma sidecars.
Twenty-seven targeted tests, full inventory audit and independent cold replay
validate the checkpoint. All 1,883 previous reference nodes survive within 1,898.

## Previous investigation: affine plus one clause closes the encoding-cap case

[The affine/one-clause extension](affine-one-clause.md) raises coverage
**56/83 -> 57/83**, also without growth exceptions. It scans all 29 selected
leaves, reuses saved checked affine rows, and accepts one. The source-bound
certificate is **1,056 compressed bytes**; the **769,847,296-byte** inventory
remains unchanged. Twenty-one targeted tests and independent cold replay check
the complete basis, source binding, coverage and reference proofs.

1. **Change structure on the remaining non-affine leaves.** All **28 selected
   open leaves across 26 originals have zero directly recognized parity equations**.
   Repeating this affine scan or expanding its one-clause handler will not address
   these representations. Target case 73's **20-variable / 80-clause** exhausted
   leaf with a retained cofactor decomposition; compare case 30's four untried
   augmented candidates on its **29-variable / 120-clause** leaf. Keep the parent
   18-base / 92-variable ready queue. Hidden or conditioned affine structure is
   possible, but its discovery needs evidence rather than a label assumption.
2. **Check complete positive plans from their actual dependencies.** The new local
   pass costs **0.00599 s**, while restoration/preparation costs **14.80944 / 64.60772 s**.
   Pipeline time is **82.32152 s**, with an unchanged inventory and a narrower
   audit scope than the parent; this is not a matched whole-solver speedup.
3. **Retain the cost limits.** A complete nullspace basis can require quadratic
   bits, even though this rule avoids exponential direct parity re-encoding.
   Matched generated cases show only **1.11--1.24x** local reuse savings after
   checks. The new proof and diagnostic artifacts add storage; no global peak-RAM
   reduction, minimum-cost expansion or arbitrary-SAT bound is established.

Resume `experiments/results/cnf-affine-clause/report.json` with
`continue_cnf_affine_clause.restore_checkpoint` **and its `routes_for`**. Preserve
all **five evidence lists**, including the new family proofs as well as seven
splits, 42 learned bases and 155 augmented blocks. The reference archive preserves
all 1,869 old nodes within 1,883 nodes. Earlier lemma sidecars, Lean and the older
902/985 full-corpus result remain unchanged.

## Previous investigation: a saved split completes one original decomposition

[The saved-cofactor experiment](saved-cofactor-closure.md) raises structural
coverage **55/83 -> 56/83**, also without growth-exception routes. Ranking all
fourteen saved pairs selects variable 15 of the 19-variable / 84-clause leaf.
Both cofactors close with **18 new recognition states** under one shared 32-state
allowance, completing development case 71 (48 variables / 204 clauses). Independent
reference proofs and model lifts pass. All seven saved split sources and eleven
acquired learned targets are now closed; the old split frontier has no pending
or open child.

1. **Test an affine core with one remaining clause as a recognized family.**
   The checked `encoding-cap-affine.json` diagnostic finds exactly two consistent
   parity equations and one eleven-literal coupling clause in case 0's 11-variable
   leaf. For a consistent affine system, a single clause is satisfiable precisely
   when one of its literals is compatible with that system. A particular solution
   and nullspace basis can determine this without expanding the affine relation
   into CNF. Implement and check both model construction and the all-literals-
   impossible certificate, with charged extraction and linear algebra. This is a
   standard linear-algebra consequence and an implementation opportunity, not a
   new tractability claim for arbitrary CNF. The existing minimum-width-five
   obstruction explains why repeating shallow probes misses this structure.
2. **Move the general scheduler to an uncovered original.**
   `open-originals.json.gz` records 27 open originals and 29 distinct selected
   leaves, with no exact leaf shared across originals. The **20-variable / 80-clause
   leaf of case 73** has exhausted ordinary and current augmented probes and is a
   concrete next saved-cofactor target. Compare it with the four remaining learned
   candidates on the **29-variable / 120-clause leaf of case 30**. The full ready
   queue still has **18 bases / 92 variables**, each currently tied to one selected
   original; case 14 has two ready leaves. The 11-variable encoding-cap example
   already has a width-five no-trigger obstruction and no saved probe pairs: use
   structural/affine treatment or explicitly charged deeper conditioning there,
   not another unchanged shallow pass.
3. **Extend dependency-local checking to complete positive coverage plans.**
   Resident acquisition takes **0.05914 s** and ranking **0.04395 s**, but the full
   pipeline costs **271.74 s**, including **110.36 s** for the inventory audit.
   Compact fact checking from the previous run does not replace these obligations.
4. **Keep costs and persistence explicit.** The working database adds **200,704
   bytes** to **769,847,296 bytes** / **41,728 pattern nodes**. The compressed delta
   is **9,471 bytes**. All 1,775 old reference nodes survive within 1,869 nodes.
   Fourteen relevant tests, the full audit, and **163.74 s** independent cold
   selection/coverage/reference replay pass with no new discovery. Peak RAM and
   general minimum-cost or polynomial expansion remain unproved.

Resume `experiments/results/cnf-saved-splits/report.json` with
`continue_cnf_saved_splits.restore_checkpoint`, preserving **seven splits, 42
learned bases and 155 augmented blocks**, plus the earlier lemma sidecars. Its
runner intentionally requires an open saved-split leaf; the next run must select
from the newly recorded original frontiers or the ready learning queue instead.
These are reused development cases; the older 902/985 study and Lean sources are
unchanged.

## Previous investigation: transport parent lemmas, then change the inference

[Checked parent-lemma transport](parent-lemma-transport.md) preserves eight of
sixteen parent lemmas across the saved branch and both eliminations; one is
already explicit and **seven can be added** to the 19-variable / 84-clause leaf.
All seven also follow from the leaf's saved traces. That local route adds eleven
clauses, but **neither augmentation reduces support**. All binary-variable pairs
remain clear (32 and 34 traces respectively); separate exact-source exhaustion
certificates retain this result. Structural coverage stays **55/83**.

1. **Try another saved cofactor of the 19-variable leaf**, preserving both branch
   obligations and closed siblings. Repeating the two recorded augmentations is
   unproductive. A further round using their new traces is a distinct, untested
   alternative; the result is not a proof of complete clause saturation.
2. **Reuse positive facts with their actual dependencies.** A source-bound
   transport certificate now checks conditioning, complete projection, binary
   path deletion and variable maps without loading the whole inventory. It is
   **2,362 compressed bytes**. Compact replay of both augmentations and their
   obstructions costs **0.111--0.162 s**; additional inventory reconstruction and
   ancestry checking costs **13.85--14.43 s**. Export itself costs **14.05 s**.
   These modes have different ancestry obligations and are not whole-solver
   speedup measurements. On this leaf, the already acquired local proof is smaller.
3. **Keep the remaining discovery and accounting obligations explicit.** The
   18-base / 92-variable alternative queue and dependency-local coverage checking
   remain open. No structural state was added. The **769,646,592-byte** history,
   six splits, 42 learned bases, 155 blocks and reference results are unchanged.
   Thirty-seven relevant tests and two read-only cold ancestry checks pass.

Resume the inventory from `experiments/results/cnf-reuse-frontier/report.json`;
also retain the new proofs in `experiments/results/cnf-lemma-transport/`. The latter
is a sidecar experiment, not a replacement coverage checkpoint or a new Lean proof.

## Previous investigation: retain the probing limit without restoring the inventory

[Continuation and compact exhaustion replay](retained-split-frontier.md) exhaust
the ten remaining candidates on the **19-variable / 84-clause** leaf. Three clear
blocks add no recognition states; original structural coverage stays **55/83**.
Twenty-eight clear traces cover fourteen binary variables. The other five cannot
start unit propagation. No retained pair yields a common/equivalence rewrite.
Repeating ordinary probes on this exact source has no discovery value.

The new source-bound certificate keeps only the formula and required traces:
**1,347 compressed bytes**. Two fresh-process replays take **0.082--0.125 s**,
versus **14.10--14.20 s** reconstructing the identical proof from history. Packing
costs 0.00288 s after the traces are available; prior acquisition and the exporting
diagnostic's 14.03 s restoration remain charged. This verifies one unit-refutation
obstruction, not SAT/UNSAT, full coverage, ancestry or the whole inventory.

1. **Change inference on the 19-variable leaf.** Compare source-proved clause
   augmentation with a split from its fourteen saved pairs. Explore transport of
   retained parent lemmas only with checked variable bindings and elimination
   conditions. The old negative certificate cannot be inherited by a changed
   formula. Retain the alternative **18-base / 92-variable** learned queue.
2. **Extend checking with explicit dependency boundaries.** Compact replay avoids
   inventory restoration for this one fact. Positive routes and complete coverage
   plans still need their relevant dependencies checked; the full audit costs
   **113.33 s**. Do not substitute a compact fact for a whole-plan audit.
3. **Keep cost and coverage separate.** Local acquisition costs 0.00870 s, but the
   continuation pipeline costs **271.54 s** and delta export alone 5.40 s. The
   28,672-byte working-database growth stores negative evidence, not wider closure.

Resume `experiments/results/cnf-reuse-frontier/report.json` using
`continue_cnf_reuse_frontier.restore_checkpoint` and `routes_for`. Keep all six
splits, 42 learned bases and 155 augmented blocks. Working SQLite is
**769,646,592 bytes**, with 41,710 pattern nodes, 87 windows and 128 ordinary
continuations. All 1,775 reference nodes survive byte for byte. All **17 relevant
tests**, the full inventory audit and **154.19 s** standalone cold replay pass.
The 589-test full-suite result remains in the parent; it was not rerun here.
`obstruction.certificates.json.gz`, `obstruction.json` and
`replay-comparison.json` bind the compact evidence and measurements. The manuscript
now explains this narrow reuse result; Lean sources and unrestricted claims are
unchanged.

## Previous investigation: conditioning passes the exhausted learned batch

[The learned-clause/saved-split comparison](learning-versus-saved-split.md)
starts both arms from the same 22-variable / 90-clause residual with a 32-state
recognition allowance. The new 16-clause batch exhausts its augmented probes
without a reduction. The saved split needs **four new recognition states** and
leaves a **19-variable / 84-clause** obligation, with its other branch closed.
Original coverage remains **55/83**. This is local structural progress; it does
not establish an original-level gain or a general timing advantage.

1. **Continue the acquired 19-variable leaf.** Its original profile is
   `learning_clear`, but ten ranked ordinary candidates remain untried. Reuse
   all parent splits and closed siblings. Compare another bounded continuation
   with the alternative queue before repeating work on exhausted sources.
2. **Keep the 18-base / 92-variable learning queue.** The new base joins the
   exhausted group; do not rerun this exact 16-clause batch. The full saved
   source implication graph also provides no forced value, equivalence or
   contradiction. This does not exclude larger batches or stronger inference.
3. **Reduce cold validation cost when expanding the scope.** Local acquisition
   is only about 0.038 s for learning and 0.034 s for splitting, before ranking
   and repeated cold preparation. The 434.32-second pipeline includes a 117.76 s
   inventory audit and roughly 5.6 s per delta export, even for an empty delta.
   Dependency-local checking and export are concrete high-cost gaps.
   Recognition-state caps still do not bound total checking work, memory or
   retained bytes.

Resume `experiments/results/cnf-learning-split/report.json` through
`compare_cnf_learning_split.restore_checkpoint` and
`compare_cnf_split_batch.routes_for`. Retain **six external splits**, **42 learned
bases** and **155 augmented blocks**. The selected frontier is under
`diagnostics.json.gz` -> `frontier`; separate learned-target diagnostics keep
successful external routes visible. There are no pending cofactor children in
this run. The prior export failure and all completed proofs are preserved too.
Working SQLite adds **57,344 bytes** to **769,617,920 bytes** and retains **41,710
pattern nodes**. All 1,750 earlier reference nodes remain within 1,775 checked
nodes. Reference solving proves the source, augmented formula and both cofactors
SAT; structural closure of the selected remaining leaf is a separate obligation.
All **589 tests**, full inventory audit and independent cold replay pass. The
latter certifies the augmented obstruction: 42 clear traces cover 21 binary
variables, and variable 12 cannot start unit propagation. No single-variable
unit refutation succeeds after this precise batch. Cold replay costs **297.82 s**.

## Previous investigation: reuse reaches a 22-variable inference boundary

[Continuation through retained splits](retained-split-frontier.md) follows the
saved open cofactor instead of restarting its 33-variable parent. A forced
reduction shrinks the selected leaf **27/101 -> 22/90** (variables/clauses), using
**six recognition states in 0.06866 s**. Original coverage stays **55/83**, including
the growth-exception ablation. Six clear blocks and one forced block are retained;
no admission cap binds. All **589 tests** pass.

1. **Change the inference on the 22-variable source.** Its 38 saved clear traces
   cover both values of all 19 binary-clause variables. The other three cannot
   initiate unit propagation. This certifies failure of single-assumption unit
   refutation on the unchanged source. All retained pairs also fail the current
   common-value/equivalence test. Inspect unused entailed binary consequences for
   a new learned batch, compared with nested cofactor acquisition from those saved
   pairs. Repeating the exhausted ordinary stream has no discovery value.
2. **Retain the alternative 18-base / 92-variable learning queue.** Compare total
   acquisition/checking/storage work and useful structural coverage; the smaller
   leaf is not itself a new original-level closure. No SAT/UNSAT conclusion follows
   from the unit-refutation obstruction.
3. **Keep cold verification costs explicit.** Preparation costs 64.68 s, full
   inventory audit 104.39 s and cold route reconstruction 63.60 s in the 256.65-second
   pipeline. Navigation costs 0.00688 s. Dependency-local validation remains an
   opportunity; state caps do not bound retained bytes or total CPU work.

Resume `experiments/results/cnf-split-frontier/report.json` with
`continue_cnf_split_frontier.restore_checkpoint` and
`compare_cnf_split_batch.routes_for`. The new frontier view follows nested saved
splits and reports missing children explicitly; it does not enumerate every
alternative learned route or compute a cheapest decomposition. Keep all five
external splits. Working SQLite adds **176,128 bytes** to **769,560,576 bytes**,
with **41,706 pattern nodes**, **86 windows** and **126 ordinary continuations**.
The 41 learning bases and 150 augmented blocks remain. All 1,721 prior reference
nodes survive in the 1,750-node archive. `obstruction.json` preserves the checked
inference limit; the unchanged older checkpoint would repeat this work.

## Previous investigation: matched cofactor acquisition reaches 55/83

[The isolated cofactor/probe comparison](saved-cofactor-batch.md) starts both
arms from the same 53/83 parent. Splitting reaches **55/83** with 30 new states;
ordinary continuation reaches **54/83** with seven. Case **37 is UNSAT** and
case **77 is SAT** by independent reference proofs. Splitting alone adds case 77
in this comparison. Its acquisition costs **0.14475 s** plus **0.05791 s** ranking,
versus **0.09725 s** for ordinary continuation. This is additional coverage at
higher local cost, not a general speedup. Both arms and their negative results
remain available in the merged checkpoint. All **585 tests** pass.

1. **Continue the acquired 27-variable / 101-clause cofactor leaf.** Three of four
   selected target fragments close; the remaining split has one closed branch
   and this open leaf on its true branch. There are 18 ranked ordinary variables.
   Use `diagnostics.json.gz` → `children` for the exact key: the old target view
   alone still follows the 33-variable parent and omits open external split edges.
   Reuse the saved parent split and closed sibling instead of restarting either.
2. **Keep the 18 ready learned bases as the alternative queue.** The merged
   coverage filter still leaves 92 ranked variables there. Ten bases are covered,
   nine exhausted, three initially successful and one has an acquired open target.
   Prefer measured progress per total acquisition/checking/storage cost; the new
   control shows ordinary continuation can reproduce part of a split gain.
3. **Cold proof verification remains the dominant runtime cost.** Fresh arm
   preparation costs 65.37/67.69 s and full inventory checking 107.02 s, compared
   with subsecond local acquisition. The 405.18-second comparison includes several
   independent preparations; it is not one warm expansion's runtime. Exact
   dependency-local validation remains a separate unimplemented opportunity.

Resume `experiments/results/cnf-split-batch/report.json` with
`compare_cnf_split_batch.restore_checkpoint` and `routes_for`, including **all
five external splits**. The union adds 36 distinct pattern nodes, four windows
and thirteen continuations; one new node is shared by the isolated arms.
Working SQLite grows **720,896 bytes** to **769,384,448 bytes** and contains
**41,700 pattern nodes**, **84 windows**, **121 ordinary continuations**, 41
learning bases and 150 augmented blocks. All old proof rows survive; the extended
reference archive retains all 1,175 old nodes within 1,721 checked nodes. Separate
artifacts add storage, peak RAM is unmeasured, and repeated splitting can still
be exponential. This result concerns 83 reused development cases.

## Previous investigation: saved cofactor traces raise coverage to 53/83

[Saved-trace splitting](saved-trace-splitting.md) closes the ten-variable leaf
and raises coverage **52/83 -> 53/83**, including the growth-exception ablation.
Case **2** (`holdout3`, n32, original 894) is independently **SAT**. The new route
references both clear source traces for variable 5 and requires plans for both
cofactors. It adds **five pattern nodes**, one ordinary clear window and one
external split. All **581 tests** pass; older proof rows remain unchanged.

The last ordinary probe is clear. Ten checked attempts plus the no-trigger lemma
exclude single-assumption unit refutation on the ten-variable source. Its clear
traces remain useful as exact cofactor descriptions. All five ranked pairs have
two absent children; the chosen pair minimizes the bounded ranking's support/
literal terms, not total solving cost. No state admission cap binds.

1. **Try retained pairs on the four remaining acquired open targets.** Their
   selected leaves have **33, 33, 36 and 38 variables**. Rank available exact
   cofactors and acquire them under a shared cap; compare against later probing.
   Splitting requires one checked pair, not exhaustion of all other variables.
2. **Recheck the 18 previously ready learned formulas when the predicted split
   cost is worse.** Their 92 unused ranked variables remain available; reapply
   the coverage filter before scheduling. Include the new
   split layer in every comparison; the preceding loader alone omits case 2's
   coverage route. Keep all failed cofactor acquisitions and clear probe blocks.
3. **Do not equate avoided propagation with faster replay.** The selected warm
   control costs **0.50192 ms** with reuse versus **0.46004 ms** fresh: no speedup
   is demonstrated. Reuse avoids two fresh assumption traces but reads 10,454
   source-payload bytes. Source decoding/checking is a local improvement target;
   preparation **66.52 s**, full cold inventory **107.45 s** and cold routes
   **63.69 s** remain the dominant costs of the **263.26 s** pipeline.

Working SQLite grows **65,536 bytes** to **768,663,552 bytes**. Resume
**41,664 pattern nodes, 80 ordinary windows, 108 ordinary continuations, 41 learning
bases, 150 augmented blocks and one external split** using
`compare_cnf_trace_split.restore_checkpoint` with
`experiments/results/cnf-trace-split/report.json`. Construct
`ContinuedLearningRoutes`, then attach every returned split with
`cnf_trace_split.attach`. All 1,156 earlier reference nodes survive in the
1,175-node extended archive. External artifacts are separate from SQLite size;
peak RAM remains unmeasured. This adds a charged conditioning step beyond the
old recognizer depth, not a new tractability theorem or an unrestricted bound.

## Previous investigation: retained learning raises coverage to 52/83

[The shared-budget continuation](retained-learning-batch.md) reuses the 36 earlier
clear learning bases and raises coverage **47/83 -> 52/83**, including the
growth-exception ablation. Cases **24, 40, 50, 66 and 81** are independently
proved **SAT**. The run adds 141 augmented blocks (131 clear, nine forced, one
equivalence) and 77 pattern nodes. No target admission cap binds; no successful
child remains pending. All 577 Python tests pass.

**Attribution is mixed:** six successful augmented blocks have clear matched
original-source controls, while four controls also force a value. The gain is
broader checked coverage, not a measured whole-solver speedup or evidence that
all reductions require learning. All cases remain reused development inputs.

1. **Probe the smallest acquired open target first.** Its selected leaf has
   **10 variables / 51 clauses**, with one ordinary ranked variable still unused.
   Four other selected leaves have 33, 33, 36 and 38 variables. The checkpoint
   retains exact target and leaf identities; do not restart from original CNFs.
2. **Continue the 18 ready learned formulas.** They have **92 untried ranked
   variables** and need no repeated clause selection or initial probes. The raw
   queue has 23 entries, but five have consumed their final clear block. Use the
   persisted selection filter. Across all 41 bases, the final statuses are 18
   ready, nine exhausted, six covered, five acquired open targets and three
   initially successful bases.
3. **Keep exhausted inference and cold validation as explicit gaps.** Another
   learning layer must bind augmented reasons to their actual dependencies;
   bounded conditioning is an alternative. For runtime, preparation **66.28 s**,
   full inventory audit **107.69 s** and cold routes **63.57 s** still dominate
   the **263.21 s** pipeline. Later probes/checks cost **0.62674 s**, controls
   **0.39536 s**, target recognition **0.32568 s**. Dependency-local validation
   remains an unimplemented opportunity.

Working SQLite grows **1,044,480 bytes** to **768,598,016 bytes** and holds
**41,659 pattern nodes**. External block/control, diagnostic, coverage and
reference archives are separate. All 164 earlier reference proof nodes survive
unchanged in the 1,156-node extended archive. Peak RAM remains unmeasured.

Resume `experiments/results/cnf-learning-batch/report.json` with
`continue_cnf_learning.restore_checkpoint`; pass all returned rewrites, bases and
augmented blocks to `ContinuedLearningRoutes`. There are now 150 augmented blocks;
the 41 learning bases, 79 ordinary windows and 108 ordinary continuations are
unchanged. A subsequent pass uses a new output directory and `--parent` with this
report. Older experiments, manuscript, Lean and the 902/985 study remain intact.

## Previous investigation: later augmented probes close case 32; coverage reaches 47/83

[Learned-formula continuation](frontier-learning-continuation.md) raises coverage
**46/83 -> 47/83**, including the growth-exception ablation. Case **32**
(`reuse_holdout3`, n48, original 1191) now has a complete structural plan and an
independent **SAT** proof for the original. Its 23-variable residual closes after
a later forced block and 17 target-state admissions. No admission cap binds.

The source-pair and complete implication-graph scans find no reduction on either
starting leaf. Checked learned batches contain 16 and six clauses. The smaller
source's augmented probes are clear initially and at offset 4, then forced at
offset 8. Every same-variable original-source control remains clear, supporting
a propagation benefit beyond a ranking change. Target recognition still performs
additional work; the original-level gain uses the composed proof route.

The 39-variable leaf stays open. Its six-clause augmented formula exhausts all
29 binary-variable probes; ten other variables cannot trigger unit propagation.
This is an exact **single-assumption unit-refutation obstruction**, not an
arbitrary-algorithm limit. Raising the same clause-selection cap alone will not
change its six-clause batch, which already processes all saved source candidates.

1. **Continue the 36 earlier clear learned formulas.** Their source evidence,
   learned clauses and first augmented blocks are already retained. Filter
   sources already covered by another route, rank the rest by exposed size, and
   use the new continuation manager under an explicit shared budget. Preserve
   controls and all unsuccessful blocks. Do not repeat the unchanged source
   graph scan or clause acquisition just to reach their later variables.
2. **Use the exhausted 39-variable source as a secondary structural test.**
   Its new augmented traces may justify another bounded learning layer with
   explicit proof dependencies. Compare this reuse with two-variable conditioning;
   neither repeating the exhausted ranking nor treating augmented reasons as
   original-source reasons is valid progress.
3. **Retain the full cost account.** Source checks/scans cost **0.04568 s**,
   initial learning **0.01057 s**, later augmented probing/checking **0.03867 s**,
   controls **0.02608 s** and target recognition **0.05576 s**. Full preparation
   costs **65.25 s**, cold inventory **106.56 s** and cold routes **63.18 s**.
   Dependency-local validation remains the largest runtime opportunity.

All **573 tests** and standalone cold checks pass. There are **16 initial and
61 later augmented attempts, 135 recognition attempts and 82 control attempts**.
Two learning bases share eight source references across 22 clauses; nine later
blocks contain eight clear outcomes and one forced result. Original-source
exhaustion is also certified on both starting leaves. SQLite grows **212,992
bytes** to **767,553,536 bytes**; the node delta compresses to 11,813 bytes,
with external proof records and diagnostics stored separately. Peak RAM is
unmeasured. The full pipeline costs **256.47 s**, plus **71.67 s** standalone
validation; there is no whole-solver speedup or unrestricted-SAT bound.

Resume **41,582 pattern nodes** with `restore_checkpoint` in
`experiments/compare_cnf_frontier_learning.py`, supplying
`experiments/results/cnf-frontier-learning/report.json`. Pass all returned paired
rewrites, learning bases and augmented blocks to `ContinuedLearningRoutes`.
The 79 ordinary windows and 108 ordinary continuations are unchanged; the nine
augmented blocks form a separate evidence layer. All older results, the 902/985
prepared study, manuscript and Lean sources remain unchanged.

## Previous investigation: learned-target continuation closes one more original

[The bounded target continuation](learned-target-continuation.md) raises coverage
**45/83 -> 46/83**, including the growth-exception ablation. Case **58** (`fresh3`,
n48, original 1340) closes and is independently proved **UNSAT**. Case 32's
selected leaf shrinks **27 -> 23 variables** (97 clauses), but remains open.
The other selected leaf stays at 39 variables / 160 clauses.

**Both remaining leaves have exhausted their ranked probes.** Case 32 reaches
the eight-step cap exactly after its final partial clear block, so its recorded
`step_limit` is not evidence of untried candidates. Another unchanged pass would
only replay the saved forced route and record exhaustion. No admission cap binds
and no target is pending. Clear probes remain inconclusive about SAT.

1. **Reuse the later traces on the 23-variable leaf.** Its initial bounded
   learning did not consume these subsequent windows. Check paired consequences,
   equivalences and additional implications on this exact source before acquiring
   new assumptions. If that fails, compare bounded two-variable conditioning
   with an equal-budget augmented-source continuation. Preserve exact formula
   dependencies and keep nested augmented traces out of source reason indices.
2. **Keep the 39-variable exhausted leaf and the 36 earlier clear augmented
   trials as secondary targets.** Repeating ordinary probes at the two exhausted
   leaves adds no assumptions. The current gain is an additive coverage result,
   not an isolated estimate of learning's benefit over the same extra probing
   budget on an unaugmented target.
3. **Cold validation remains the largest runtime cost.** Three local passes cost
   **0.11697 s**, but route preparation costs **65.97 s**, full cold inventory
   **107.76 s** and cold route replay **63.30 s**. Dependency-local verification
   remains an opportunity; excluding these costs would hide the dominant work.

The run retains **15 blocks (13 clear / two forced), 105 direct attempts, 87
recognition attempts and 10 new nodes**. All **569 tests** and independent cold
replay pass. Working SQLite grows **327,680 bytes** to **767,340,544 bytes**;
the delta compresses to 18,000 bytes, with diagnostics, coverage and independent
reference proofs stored separately. Peak RAM is unmeasured. The pipeline costs
**256.68 s**, plus **71.33 s** standalone validation. No whole-solver speedup or
unrestricted-SAT bound follows.

Resume **41,565 pattern nodes, 79 windows and 108 continuation blocks** with
`restore_checkpoint` in `experiments/compare_cnf_target_probe.py`, supplying
`experiments/results/cnf-target-probe/report.json`. Pass both returned external
record lists to `LearnedTraceRoutes`. The diagnostic archive retains exact
remaining leaf keys and every successful/unsuccessful block. Older rows, the
902/985 prepared study, manuscript and Lean sources remain unchanged.

## Previous investigation: learned clauses strengthen two sources; coverage stays 45/83

The [retained-implication study](saved-implication-learning.md) checks complete
binary reachability on the same 41 sources. It finds **no forced values or
contradictions**, and only the previously retained equivalence. These negative
results have exact path/closure certificates. Graph composition alone is not
the next coverage opportunity on this fixed evidence.

Using **284 checked clauses in 39 bounded batches** with the full CNF produces
36 clear trials, two equivalences and one forced value. Controls use the same
augmented ranking on the unaugmented source: 38 remain clear and one gives the
old equivalence. Thus cases **31 and 32 have stronger propagation**, independently
of ranking changes. All three targets remain structurally open; **45/83 stays
45/83**, also without growth-exception routes. Reference proofs confirm both
newly strengthened residuals SAT and the old-equivalence residual UNSAT; these
are residual answers, not new original-level structural coverage.

| Original case | Source -> direct target -> remaining selected leaf | Untried ranked variables at leaf |
| --- | --- | --- |
| 32 (`reuse_holdout3`, original 1191) | 34 -> 33 -> **27** variables | **17** |
| 31 (`reuse_holdout3`, original 1190) | 40 -> 39 -> **39** variables | **21** |
| 58 (`fresh3`, original 1340) | 37 -> 36 -> **35** variables | **23** |

1. **Follow the smaller acquired targets, starting with case 32.** Its single
   27-variable, width-two leaf already includes the checked learning and further
   reductions. Reuse that state and its initial attempts; acquire a bounded next
   window before revisiting the larger source. Keep all parent learning routes
   in global recomposition. No current admission cap binds and no target is pending.
2. **Continue the 36 clear augmented trials under an explicit budget.** Their
   clauses and first four probe variables are now saved. Later attempts must be
   checked against the exact augmented formula, not treated as original-source
   evidence. Compare an additional window with stronger conditioning, retaining
   same-variable controls and all unsuccessful results. Do not repeat the
   unchanged graph search or assume the 16-clause batch is exhaustive.
3. **Retain the structural obstructions and the full cost account.** The
   width-five source and the width-two stalled source without useful learned
   clauses still need different treatment. Cold checking remains dominant:
   **64.75 s** preparation, **106.92 s** inventory, **63.50 s** routes. The graph
   scan costs **0.74307 s**, learning **0.23493 s**, controls **0.14577 s** and target
   recognition **0.14217 s**. There is no whole-solver speedup claim.

All **566 tests** and independent cold replay pass. The run acquires **15 nodes**,
311 augmented probe attempts, 312 control attempts and 138 target-recognition
attempts. It preserves 126 interned source references for the 284 clauses.
SQLite grows **249,856 bytes**; compressed delta/learning/diagnostic artifacts
add 15,053 / 36,867 / 16,664 bytes, plus reference proofs. The measured pipeline
takes **255.75 s**; standalone validation costs another **70.96 s**. Peak RAM is
unmeasured. The next-target diagnostic is read-only and retains exact leaf keys.

Resume **41,555 pattern nodes** with `restore_checkpoint` in
`experiments/compare_cnf_trace_learning.py`; pass both returned record lists to
`LearnedTraceRoutes`. All earlier eight-table rows, external pair rewrites,
75 windows and 97 continuation blocks remain preserved. The older 902/985
full-corpus result, manuscript and Lean sources are unchanged.

## Previous investigation: saved pairs expose one equivalence, but no coverage gain

The [saved-trace study](saved-trace-reuse.md) checks **1,240 saved attempts across
41 exposed clear sources** in **0.52728 s**. There are no common-value pairs and
one signed-equivalence block: **x27=x5** on case 58 (`fresh3`, n48, original 1340).
Exact substitution reduces its source from **37 to 36 variables**. Subsequent
recognition admits five nodes and performs 42 new probes in **0.04364 s**, but
the target stays open. Coverage remains **45/83**, also without growth-exception
routes. A separate 49-node reference archive confirms this residual is UNSAT;
that fallback answer is not counted as structural coverage.

The bounded binary-learning scan retains **284 candidate clauses on 39 sources**,
including **161 justified by later-window traces on 37 sources**. Other candidates
come from initial profiles and may have been considered by earlier learning.
Four sources reach the cap of 16 clauses, so this is not an exhaustive candidate
inventory. All 40 sources without a direct paired rewrite remain recorded.

1. **Combine the saved implications before acquiring new assumptions.** Build a
   checked binary implication graph, including contrapositives, and look for
   forced literals, contradictory components and additional equivalences. Retain
   source-linked path witnesses. If graph conclusions are insufficient, test
   propagation on the augmented CNF under an explicit clause/probe budget.
   Among the five certified single-assumption obstructions, cases 2, 73 and 27
   supply 10, 10 and three candidate clauses; cases 0 and 51 supply none.
2. **Target the remaining obstruction by structure.** Case 51 is a width-two
   stalled source without new nonredundant implications in the saved traces;
   bounded nested conditioning is a more direct next candidate. Case 0 still
   has minimum width five, excluding plain unit triggers after at most three
   assignments. Preserve the exact scope of that obstruction.
3. **Treat cold replay as the dominant runtime cost.** This run pays **65.75 s**
   preparation, **109.08 s** full cold inventory and **62.85 s** cold routes;
   acquisition/validation takes **257.50 s** before the separate validator.
   A warm chosen-pair microbenchmark improves from 0.11823 to 0.06768 s per 100
   repetitions (five-run medians), but it excludes selection, persistence and
   target acquisition. There is no whole-solver speedup or RAM claim.

All **561 tests** and independent cold reconstruction pass. Working SQLite grows
**86,016 bytes**, with a **5,818-byte compressed node delta** and **1,957-byte
rewrite artifact**. The opportunity log adds 73,273 compressed bytes (4,090,411
uncompressed); full textual reference keys are not constant-size pointers.
Resume **41,540 pattern nodes** through `restore_checkpoint` in
`experiments/compare_cnf_trace_reuse.py`, passing the returned records to
`TraceRoutes`; using only the old probe runner omits this additional route.
All prior eight-table rows, 75 windows and 97 continuation blocks are preserved.
The old 902/985 full-corpus result, manuscript and Lean sources are unchanged.

## Previous investigation: deeper probes close six cases and expose a certified limit

The [resumed-probe study](probe-resumption.md) retains the same four-source and
32-state limits and raises coverage **39/83 -> 45/83**. Independent reference
proofs confirm four SAT and two UNSAT gains, all with 48 variables. Removing
growth-exception routes keeps all 45 covered. The parent-report runner resumes
complete checked lineages, so subsequent passes can advance the latest history.

The run adds **46 continuation blocks (39 clear / seven forced), 327 assumption
attempts and 74 nodes**, with 758 saved-prefix attempt references and no new initial
windows. Case 46 closes after using all 32 state admissions; no input is interrupted
and no target is pending. Resident search/check/persist/compose costs **0.53596 s**;
preparation **65.21 s**, full cold inventory **108.60 s**, separate route replay
**63.07 s**, and acquisition/validation **257.28 s**. Storage grows **1,581,056
bytes**, with an **86,923-byte compressed delta**. Peak RAM is unmeasured; this is
additional coverage rather than a whole-solver speedup.

The 38 open originals expose **41 clear streams** on selected paths after saved
forced rewrites. **36 have 1--16 ranked candidates left; five are exhausted.**
A separate exact diagnostic certifies that all five exhausted sources have no
single-assumption unit refutation: 104 checked attempts cover both values of
52 binary variables; 79 other variable instances cannot create an initial unit.
The 11-variable encoding-cap source has minimum width five, so at most three
assigned variables cannot trigger propagation. The other four sources have
minimum width two. These are limits of this inference rule, not SAT decisions.

1. **Reuse the complete saved trace pairs for stronger consequences.** Later
   windows only searched for failed literals; the initial recognizer's bounded
   common-consequence, equivalence and binary-learning policy did not consume all
   these later traces. Check those relationships before acquiring new assumptions.
   Keep original-source evidence separate from augmented learning continuations.
2. **Use the certified obstruction to target stronger reasoning.** If paired-trace
   reuse is insufficient, try bounded nested assumptions on the four width-two
   sources. The width-five encoding-cap source needs different structural treatment
   or enough explicitly charged conditioning to reach a unit trigger. No shallow
   plain-probing guarantee applies there.
3. **Advance the 36 unfinished streams as a coverage control; profile cold replay
   for runtime savings.** Resume this report with the existing runner and same
   limits. The exhaustion diagnostic verifies only its required source facts in
   0.02974 s after 4.73048 s restoration (5.35440 s overall). Its smaller proof
   obligation does not justify skipping dependencies in a full coverage audit.

All **557 tests** pass; the acquisition checkpoint separately preserves its
552-test log and independent eight-table/cold/reference validation. Two preliminary
diagnostic failures exposed the `learning_clear` wrapper; their logs and untimed
replay limitation are retained. The final checker directly verifies each original
assumption trace, excluding nested augmented-source traces. Resume from **41,535
pattern nodes, 75 windows and 97 continuation blocks**, alongside every older
trial/source/proof row. The new reference archive adds 1,238 solver nodes. Earlier
full prepared coverage remains 902/985; manuscript and Lean sources are unchanged.

## Previous investigation: checked prefixes let discovery advance without rediscovery

The [prefix-continuation study](probe-continuation.md) advances saved clear probe
windows while retaining their checked traces by reference. A continuation binds
the exact source/configuration/depth, width and offset, and requires its complete
clear predecessor. Missing, foreign or forced prefixes cannot authorize a cursor.
Pending forced residuals survive restart and become routes only after acquisition.

Coverage improves **36/83 -> 39/83**: one SAT and two UNSAT 48-variable development
cases, independently confirmed. All 39 remain covered without the growth-exception
routes. The run adds **51 continuation blocks (43 clear / eight forced), five
initial windows and 45 nodes**. It makes 409 new attempts and references 408 saved
attempts without rediscovery. No cap binds (maximum 13 new states / three sources).

The matched warm probe substep uses **373 versus 781 attempts**, with five-run
median **0.13230 versus 0.27631 seconds**: **2.09x** faster for ranking, discovery
and checking after prefix validation. Both microbenchmarks exclude persistence
and target recognition. Resident search/check/persist/compose costs **0.56578 s**;
preparation **64.41 s**, full cold inventory **110.39 s**, separate route replay
**63.13 s**, and the whole acquisition/validation pipeline **257.43 s**. Cold
checking remains the dominant measured cost. No end-to-end solver speedup or
peak-RAM reduction is claimed. Working storage grows **1,359,872 bytes**; the
delta is **1,429,504 SQLite / 82,368 compressed bytes**.

1. **Advance the remaining 42 clear streams with the existing mechanism.** They
   retain 2--20 eligible candidates each; one other clear stream is exhausted.
   Resume the full eight-table history and measure additional coverage per new
   attempt under the same bounds before expanding the policy or admission caps.
2. **Investigate four forced-but-open targets.** Three of eight forced targets
   close locally and one more through composed routes. The remaining four retain
   unresolved interactions. All five locally open targets have one selected
   unresolved leaf, giving concrete residuals for further structural diagnosis.
3. **Profile cold proof replay for the largest runtime win.** Distinguish required
   reachable dependencies from repeated reconstruction and unrelated history;
   preserve exact checking and invalidation requirements. Warm prefix savings
   do not remove the preparation cost. Peak RAM and independent evaluation remain
   separate obligations.

All **547 tests**, eight-table reconstruction, cold prefix/finite-plan replay,
growth ablation and independent reference checks pass. Resume from **41,461
pattern nodes, 75 initial windows, 51 continuation blocks, 563 pivot trials,
25 coupled trials and one growth trial**, retaining all 1,548 source bindings and
21,838 earlier solver rows. The new 513-node reference archive is additional
evidence. Earlier full prepared coverage remains 902/985. Manuscript and formal
sources are unchanged; these are reused development sources, not a new SAT class.

## Previous investigation: retained probe windows broaden coverage without the exception

The [probe-window investigation](probe-window.md) identifies the initial trigger
of the growth success: deleting two binary pivot clauses moves an already failed
assumption into the first four ranked probes. Complete source-coordinate traces
show no new remaining-variable single-assumption refutation after projection.
This is a selection-window effect on that core, not a general statement that
elimination cannot strengthen propagation.

Continuing with four previously untried binary-frequency candidates, at most four
unresolved sources and 32 new states per original improves coverage
**32/83 -> 36/83**. The four new 48-variable originals are independently confirmed
as **three SAT and one UNSAT**. Removing the earlier growth-exception route still
leaves all 36 covered. The positive-control core needs two continued windows;
the first forced value alone leaves an open residual.

The run preserves **70 windows** (52 clear, 18 forced), 475 assumption attempts
and **81 new recognition nodes**. Resident search/check/persist/compose costs
**0.84607 seconds**, including the positive control. Working storage increases
**2,142,208 bytes**; the delta is **2,220,032 SQLite / 129,619 compressed bytes**.
Preparation costs **65.30 seconds**, complete cold audit **106.60**, and separate
route replay **63.02**. Full pipeline time is **252.05 seconds**. This is additional
work for coverage, not a demonstrated runtime or RAM saving. Peak RAM is unmeasured.

Neither admission nor source-visit caps bind. The next evidence-backed gaps are:

1. **Advance a window while reusing its checked prefix.** Of 52 fully clear
   windows, **51 still have ranked binary candidates available** (3--24 each).
   Repeating the current source/width key correctly reuses its result but does
   not advance. Add an explicit continuation position and reuse the existing
   original and window traces before testing the next bounded block. This is
   further discovery, not a claim that those variables will close the source.
2. **Explain forced-but-open continuations.** Only five immediate window targets
   close; other forced values require more composition or leave open interfaces.
   Check whether combining compatible checked consequences can avoid repeated
   recognition, while preserving full source/name bindings and exact costs.
3. **Maintain finite-route coverage incrementally.** Repeated composition still
   scans reachable plans; cold verification remains the dominant measured time.
   A persisted reverse-premise index needs explicit update and invalidation rules.

All **543 tests**, seven-table reconstruction, cold finite-plan replay, growth
ablation and independent endpoint checks pass. Resume from **41,416 pattern nodes,
563 pivot trials, 25 coupled trials, one growth trial and 70 probe windows**;
all 1,548 source bindings and 21,838 older solver proof rows remain intact. The
409-node reference archive is additional evidence. These are reused development
sources; the earlier full prepared result remains **902/985**. Formal sources and
manuscript are unchanged, with no unrestricted SAT complexity claim.

## Previous investigation: one growth exception closes a saved alternative route

The [growth-three escape](growth-escape.md) closes the preserved 35-variable core.
Only its first projection receives allowance three; all descendants retain the
old recognizer and allowance two. Pivot 15 produces four new probing states and
no unresolved leaf, in **0.02275 resident seconds**. The growth-two control admits
no pivot. Warm search reuses the trial with zero new states in **0.00321 seconds**.
The delta is **122,880 SQLite / 7,870 compressed bytes**; working storage increases
69,632 bytes over the seed with an empty sixth table. Peak RAM was not measured.

Finite checked composition now follows open saved alternatives as well as old
plans. It requires every component/conditioning premise and rejects circular
support. This raises the selected-original coverage **31/83 -> 32/83**: case 33,
the 48-variable `reuse_holdout3` source (original case 1193). A separate complete
solver confirms UNSAT for the core, its target and the gained original. This is
one reused development case, despite its historical group name, not a fresh
holdout or a new tractable SAT family.

Composition visits 12,595 nodes / 13,176 premises in **0.05919 seconds** and retains
a **47-step, 41,065-byte compressed witness**. Its resident replay takes 0.00042
seconds; preparation costs **62.92 seconds** and fresh-cache route/witness replay
**12.17 seconds**. The escape run separately pays 65.69 seconds for preparation,
114.37 for complete cold audit and 67.68 for trial replay. These overlapping
verification phases are charged, not hidden in subsecond expansion timings.

1. **Identify when a small projection unlocks propagation.** Compare source and
   projected probe traces, binary clauses and forced values to explain why the
   unique growth-three move works here. Then test a frozen predictor on other
   preserved open cores with matched admission budgets and controls. Minimum raw
   clause growth alone is not a guarantee of useful simplification.
2. **Extend only where evidence supports the growth cost.** Check whether the
   same pattern covers other unresolved cells without repeated broad searches or
   unconditional budget increases. The earlier raw-pair lower-growth diagnostic
   remains valid; subsequent probing, rather than a net-four raw pair, closes this
   case. Keep unrecognized cases and negative trials in the history.
3. **Maintain route evidence incrementally.** The first finite composition scans
   the reachable graph. Its reverse-premise index could support updates only to
   ancestors of new closures, provided rule identity, invalidation and persistence
   are checked. Cold history verification still dominates end-to-end time.

All **540 tests** pass. Preserve the six-table history with **41,335 pattern nodes,
563 one-pivot trials, 25 coupled trials and one growth trial**, plus every earlier
source binding and solver proof. The source-coverage witness and its separate
212-node reference solver archive are additional artifacts. Formal sources and
manuscript are unchanged. The earlier full prepared result remains **902/985**;
there is no new full-corpus result or unrestricted SAT complexity claim.

## Previous investigation: state-capped coupled routes expose an admission barrier

The [coupled-pivot study](coupled-pivots.md) resumes every earlier history and
tries an interacting second pivot on retained divergent first routes. Both steps
keep the old pair/growth caps. It closes the entry-budget accounting gap by
guarding **every newly entered recognition state**, including descendants and
unfinished parents, at **32 per open input**. Completed certificates survive a
stop; cached states remain reusable. Preparation, checking, per-state work and
bytes are additional, so this is not a total runtime or RAM bound.

The original run acquires **25 trials / 32 nodes** in **0.62200 resident seconds**,
with no coverage gain: **31/83** remains. The repeated control adds **15 / 17** in
**0.21175 seconds**, retaining **88/96**. Neither run hits the state cap (maximum
11 and 6 states on an input). Original seed verification costs **69.09 seconds**,
full cold audit **114.40**, and separate trial replay **69.81**. These exceed the
new search cost and remain charged. The new delta is **937,984 SQLite / 54,883
compressed bytes**; no ordinary-solver speedup is claimed.

Only 18 still-open originals have retained divergent routes. The selected routes
admit just 25 interacting second pivots. Of their results, **17/25** return to the
first route's frontier and **24/25** use only seed leaves. Exactly one new unresolved
core appears. It has 35 variables / 150 clauses. An exhaustive candidate diagnostic
within the 64-pair cap finds minimum first-step growth **3**, minimum two-step net
growth **7**, and minimum interacting-pair growth **15**. All 662 admitted ordered
pairs fail a net-growth-four allowance, even with temporary intermediate growth.
This is a restricted move-rule obstruction, not a general SAT lower bound.

1. **Test the least-cost escape with ordinary simplification.** Start from the
   preserved new core and its minimum-growth-three first pivot; charge the extra
   clause allowance explicitly and keep the admission budget. A net-four coupled
   relaxation alone is already ruled out on this core under the current pair cap.
2. **Compose success through saved alternative routes.** A future closed leaf
   may be reachable only through an earlier open pivot/coupled trial. The present
   composition accepts individually closed replacements and does not recursively
   compose every open trial. Add checked finite route justification before counting
   any resulting whole-original gain. No gains are currently hidden or claimed.
3. **Keep move availability separate from exploration limits.** The state budget
   did not bind this experiment; increasing it without new admissible moves is not
   supported. Other moves, broader interactions and larger growth are hypotheses
   requiring matched checks, preserved failures and complete cost accounting.

All **535 tests** and artifact checks pass. Resume from **41,331 pattern nodes,
563 one-pivot trials and 25 coupled trials**, plus all earlier solver proofs and
source bindings, using the study's fifth-table reconstruction recipe. The earlier
full prepared measurement remains **902/985**; there is no new full-corpus result.

## Previous investigation: later ancestors reduce acquisition, not unresolved coverage

The [matched ancestor study](frontier-pivots.md) starts from the exact union of
both prior pivot histories, including their 345 original-suite trials. It compares
the first four open elimination ancestors with four ancestors nearest selected
unresolved terminals, keeping the same interaction-first candidate order and
pair/growth caps. Prior trials are checked and reused; each open input can acquire
at most eight **new** trials. That cap still does not bound descendant discovery.

On the 83 originals, early search acquires **145 trials / 266 new nodes** in
**3.76670 resident expansion seconds**. Near-frontier search acquires **102 trials /
90 nodes** in **1.75051 seconds**. Both retain **31/83** closures, with no closed
replacement. Near-frontier search reconverges in **82/102** trials; 20 trials
reach novel selected leaves, but none closes. The growth limit rejects 6,388 of
6,640 constructed candidates there. This is a narrower, cheaper exploration on
these inputs, not a same-work SAT speedup or a coverage improvement.

The seed costs **752,304,128 bytes** and **64--68 seconds** to verify before
resident search. Full cold checking is another **107--110 seconds**, and separate
trial replay costs **62 seconds**, with overlapping dependencies charged. The
frontier delta is **3,018,752 SQLite / 165,286 compressed bytes**, versus
**6,807,552 / 382,806** for early search. Repeated controls retain **88/96** in both
modes, adding 10 versus 12 new trials. All previous rows and failed acquisitions
are preserved. The earlier full prepared measurement remains **902/985**.

All **531 tests** pass. The new original deltas share 57 pattern rows / 29 trial
rows and add **299 unique nodes / 218 trials** together. The latest reusable
union now holds **41,299 pattern nodes / 563 trials**, plus every earlier source
binding and ordinary solver proof. Use the linked study's updated resume recipe.

1. **Test coupled deviations at retained divergent states with a new-state cap.**
   A later ancestor alone does not supply coverage at the tested limits. Keep
   source/configuration/depth identities and exact recomposition, and account for
   every newly acquired descendant rather than only entry targets. Distinguish
   this from relaxing the intermediate growth allowance.
2. **Explain the admission barrier before another broad sweep.** About 96% of
   near-frontier constructed candidates violate the current growth cap. Investigate
   a concrete interacting-variable structure that could permit a useful coupled
   continuation, including its intermediate clauses and recognition cost. Fewer
   literals or a novel residual are not successful-closure criteria.
3. **Reuse the compatible histories and retain the negative controls.** Candidate
   preparation still runs on cache hits; seed checking and cold replay dominate
   the measured elapsed work. Peak process memory, an independent holdout and a
   competitive incremental solver comparison remain separate gaps. Other ancestor
   choices and unselected branches are not exhausted by this experiment.

## Previous investigation: bounded pivot changes mostly reconverge

The [bounded-pivot study](pivot-alternatives.md) tests at most four earlier open
elimination ancestors and eight full alternative target recognitions per open
original. It preserves the same pair/growth caps and the entire paid proof graph.
**316 trials** add **602 pattern nodes**, but no closed alternative: original
coverage remains **31/83**. Resident expansion costs **6.45902 seconds**, after
**63.19332 seconds** of requested-source verification. The new rows are retained
as a **15,208,448-byte SQLite / 857,460-byte compressed delta** over the existing
734,814,208-byte base. Full cold and separate trial audits are additional costs.

The useful pattern is reconvergence: **295/316 (93.35%)** trials reach the exact
same multiset of selected unresolved canonical leaf keys as their source plans.
All immediate target roots are new, so reuse happens in their descendants.
Only 21 trials reach novel selected leaves (13 distinct); four reduce selected
open literals and seventeen increase them. None produces a recognized endpoint.
Also, **271/316** alternate pivots share no source clause with the selected one;
260 of those reconverge. Independence is not a safe universal pruning rule:
eleven such trials have different selected frontiers.

An interaction-first follow-up keeps the same four/eight budgets and pays an
extra source scan. It increases interacting trials **45 -> 74**, yet retains
**31/83** closures with no successful replacement. Expansion is **7.11551 seconds**
and acquires **660** pattern nodes, versus 602. This is another negative coverage
control. The first repeated-input control also remains **88/96**, with 56 attempts
and 40 unique persisted trials. These are selected/reused development inputs,
not untouched evaluations or a new full-corpus result.

The interaction-first follow-up still reconverges in **290/316 (91.77%)** trials,
with seventeen distinct novel leaves and no closed replacement. Both schedules
also retain **88/96** on repeated controls. All **527 tests** pass; the formal
sources and earlier projection theorem are unchanged. The original-suite deltas
share **554 pattern rows / 287 trial rows** and combine into **708 unique new
nodes / 345 trials**. Use the study's resume recipe to retain all of this work.

1. **Investigate where the paths first diverge, with a distinct-state budget.**
   Use the retained novel frontiers and ancestor-to-source links to test a small
   coupled continuation before returning to the greedy recognizer. Reuse exact
   residual/configuration/budget states and charge every new state, rather than
   assuming an eight-entry cap bounds the descendant discovery graph. Validate
   any endpoint all the way to its original source.
2. **Audit ancestor selection before raising trial or growth limits.** The current
   policy visits only the first four open elimination ancestors in breadth-first
   order. It does not exhaust later bottlenecks or all open branches. Compare a
   targeted later-ancestor schedule at the same cap before inferring that useful
   single-pivot alternatives do not exist. The tested growth and interaction
   changes are not sufficient success predictors.
3. **Preserve and reuse failed exploration at its actual scope.** Trials bind
   source, pivot, exact target and recognizer configuration. Compatible deltas
   can share immutable rows; the paid base and cold verification remain charged.
   An open result under this policy excludes neither a different continuation
   nor a tractable semantic class. Full-history peak memory, independent holdouts
   and a competitive incremental solver comparison remain open. The earlier full
   prepared measurement is still **902/985**.

## Previous investigation: exact subset filtering; useful orders remain the coverage gap

The [required-literal index](anchored-subsets.md) addresses the preceding profile's
largest own-time function while preserving every recognition outcome. The costly
source's 1,694 calls have **zero exact-input cache hits within either independent
role** (843 proposals / 851 checks). A whole-input LRU is therefore not the useful
reuse mechanism on this trace. A per-call anchor index filters impossible subset
candidates instead, retaining the old first-witness order and separate checking.

Five alternating-order kernel replays reduce the selected trace median from
**1.116163 to 0.556901 seconds**. Actual subset tests fall from **4,904,264 to
150,503**. Shared-literal controls can regress, and traced kernel peak rises from
84,047 to 88,045 Python bytes. These are kernel results, not a general SAT ratio.
All **521 tests** and the **4,219-declaration / 2,031-theorem** Lean audit pass.
The formal lemmas establish the necessary condition and first-match preservation;
Python refinement and total machine-cost proofs remain open.

The saved 57-leaf complete comparison falls from **4.54924 to 4.06818 seconds**
query and **1.73407 to 1.53721 seconds** cold checking, with the exact same
19,894,272-byte database and zero closures. Stored graphs and results are unchanged.
The optional index does not promote the previous negative additive-growth policy.

On the 83 original prior misses, matched query time falls **155.78451 ->
139.68494 seconds (10.33%)**, discovery **153.95887 -> 137.57819**, and complete
cold checking **111.46828 -> 102.79093 (7.78%)**. Both close exactly **31/83** and
reproduce the same **734,814,208-byte** archive, preserving all prior rows.
Four-source peak Python allocation is effectively unchanged at 17.35 MB; this
sample excludes native memory and full-history peak. No faster ordinary solver,
smaller history or new closure is claimed.

The repeated 96-input control retains **88 closures** and identical bytes. Query
time falls **14.44058 -> 13.76681 seconds (4.67%)**; cold replay is essentially
unchanged at **50.73523 / 50.49557**. A shared prefix and other pipeline costs
limit the kernel gain's effect on full acquisition. These are single matched
runs, with adverse controls retained and no untouched holdout.

1. **Find useful alternative orders under an explicit total discovery budget.**
   Test whether a small set of pivot choices exposes units, binary implications,
   separators, affine structure or another recognized endpoint. Validate success
   back to the original source. Charge unsuccessful lookahead and all index work.
   Do not automatically raise growth limits: the previous extra 2,530 valid edges
   gained zero source closures.
2. **Target remaining repeated work with evidence.** The zero-hit trace rules out
   whole-input proposal/check caching as the next shortcut on this source. Exact
   structural reuse across neighboring inputs needs changed-clause, implication
   origin and witness-order dependencies; those are not supplied by this ephemeral
   index. Reprofile after a coverage change before choosing further micro-optimization.
3. **Measure transfer and account for retained evidence.** Current inputs are
   selected failures and reused controls. Untouched holdouts, a common incremental
   CDCL comparison and full-history peak memory remain open. This index changes
   neither archived bytes nor the earlier full prepared result **902/985**.

## Previous investigation: useful endpoints, not just more admissible steps

The [fixed additive experiment](additive-elimination.md) implements independently
checked allowances of one and two clauses after earlier rules fail. Lean now
proves at most n0 steps, m0+d*n0 clauses per state and
(n0+1)*n0*(m0+d*n0) retained formula slots for one normalized accepted chain.
All **516 tests** and the **4,216-declaration / 2,028-theorem** Lean audit pass.
The theorem guarantees neither a useful pivot nor a small full discovery graph.

The candidate opportunity does **not** produce additional closures. On the 57
saved leaves, all three policies close zero; selected open literals increase
25,488 -> 25,838 -> 26,604. On the 83 original prior misses, all three close the
same **31**, with no gains or losses. Query time is
**121.61751 / 142.26465 / 163.21184 seconds** for baseline / allowance one / two;
acquisition databases are **674,234,368 / 700,178,432 / 734,814,208 bytes**.
Above the shared paid prefix, allowance two adds 23.6% more space and costs 34.2%
more query time. These are single ordered controls, not universal ratios.

The new rules acquire **1,021 / 2,530** additive edges across the originals.
Allowance two tests 155,645 candidates and rejects 151,131 for growth. All three
leave 52 original sources unresolved and 57 selected leaves. Cheap admission and
strict support decrease alone are therefore poor proxies for useful endpoint
progress. Both policies remain optional. Larger growth budgets should not be
the automatic next experiment.

The repeated 96-input control also retains exactly **88 closures** in all modes,
with query times **10.45184 / 12.74294 / 14.87718 seconds** and larger databases.
All nine acquisition archives and nine separate reference archives pass the
stated cold checks. The largest reference database adds **1,236,189,184 bytes**
before compression, beyond acquisition; its endpoint answers and models persist.

A separate profile of case 73 (48 variables / 204 clauses) identifies repeated
subset search as a concrete cost target: `indexed_certificate` runs **1,694**
times, with **1.67039 own / 2.21385 cumulative seconds** in **13.30082** instrumented
discovery seconds. `_find_core` has 3.48529 cumulative seconds; these nested times
must not be added. Direct additive discovery/checking total **0.24555 seconds**.
The profile is one source from the paid prefix, not the preceding ordered cache
history or a causal ablation. Count repeated exact source/augmented-CNF calls
before assuming a cache can remove all this work. Keep proposal and independently
checked-result caches distinct; ordered clauses and implication reasons matter.

The two-clause final frontier now contains **43 leaves needing three extra
clauses, eleven needing four, two needing five**, and one without a pair-bounded
candidate. These local margins have moved without gaining closures. Retained
subsumption permits a current-budget step in 22 leaves but is not an integrated
coverage result. Preserve these cases rather than automatically raising limits.

1. **Investigate which alternative orders expose useful endpoints.** Compare a
   small explicitly budgeted set of alternative pivots on retained stalled cores.
   Record whether they create units, binary implications, component separators,
   affine structure or a recognized family, then check whole-source composition.
   Keep candidate count and all failed lookahead work charged; a failed greedy
   order does not exclude another successful order. Avoid treating local growth
   margins as coverage gains.
2. **Reduce repeated recognition when it dominates acquisition.** Use the saved
   profile to measure repeated exact original/augmented subset queries before
   choosing a cache or admission rewrite. Reuse must bind actual source content,
   parent clauses, retained-resolvent membership, budgets and relevant recognition
   dependencies. Unchanged pivot occurrences alone are insufficient. Shared
   occurrence scans across growth thresholds are an opportunity, not yet a
   measured saving or the assumed dominant cost.
3. **Validate transfer and retain the full cost.** Preserve reference proofs and
   models as well as the acquisition databases; they consume additional space.
   Reused controls and selected prior failures do not replace an untouched
   holdout. The earlier full prepared result remains **902/985**; this subset
   experiment does not update it or establish efficient arbitrary-SAT coverage.

## Previous investigation: small additive clause growth was the next coverage test

The [clause-count fallback](clause-bound-elimination.md) is implemented, checked
and remains optional. It closes **31/83** original prior misses versus **29/83**,
with no losses and two distinct 48-variable gains. Query time grows
**78.06321 -> 113.63899 seconds (+45.57%)** and complete database bytes
**621,146,112 -> 674,234,368**. Added bytes above the paid prefix grow **26.05%**.
The separate 96-input repeated control retains the same **88 closures**, while
time grows **8.90872 -> 10.48245 seconds**. Opposite-order leaf runs reproduce
the same databases and one new leaf closure at higher cost. No default promotion
or fresh full-corpus result follows.

All **511 tests** and the **4,195-declaration / 2,018-theorem** Lean audit pass.
Lean proves conditional size bounds for one accepted chain, not pivot availability
or full discovery costs. All eight archives cold-check unchanged, prior rows
survive, and every new edge receives independent endpoint/model validation.
Original-input endpoint diagnostics cost **961.43125 seconds**, separately from
query time; their older reference solver still performs a per-solve SQL census.
No profile isolates that cost from solving. Production queries already use the
incremental accounting implementation.

The [exact frontier diagnostic](../experiments/results/cnf-clause-bound-elimination-originals/growth-barriers.json)
finds **57 selected leaves / 25,488 literals** remaining across **52 unresolved
originals**. Of these leaves, **32** have a pivot needing only one additional
clause, **50** need at most two, and **56** need at most four under current pair
and candidate caps. Removing the pair cap alone helps just one other leaf,
whose cheapest admissible pivots require 72 pairs. Retained-clause subsumption
would admit a non-growing pivot in 12 leaves. These counts describe candidate
opportunities, not successful chains or added closures.

1. **Test fixed additive clause budgets of one and two.** Preserve earlier
   accepted choices and exact complete-pair checks. A fixed allowance d keeps
   any elimination-only chain within m0+d*n0 clauses; alternatively the fixed
   pair cap B gives m0+B*n0. This bounds formula payload, not an efficient order
   search or all branches. Compare whole-source outcomes and total costs before
   promotion. The additive policy and its Lean resource theorem remain open.
2. **Measure and reduce repeated failed recognition.** The current extension
   tests 166,437 candidates, rejects 162,187 for clause growth and acquires
   2,504 new nodes for two extra original closures. Each new target reruns the
   structural pipeline. Profile a representative costly source before choosing
   between cheaper candidate admission, reusable unchanged occurrence analyses
   and more selective acquisition. Retained-clause duplicate membership can
   change even when pivot occurrences do not; include that invalidation dependency.
3. **Separate useful order discovery from checking one chain.** An unsuccessful
   greedy order does not exclude another useful order. Preserve alternatives,
   negative cases and the pair-cap exception. The repeated 96-input control gives
   no coverage transfer, so an untouched holdout and broader rerun remain open.
   Census optimization in the diagnostic is supporting work; it does not address
   the measured 111.89 seconds of original-source structural discovery.

The earlier full prepared measurement remains **902/985**. This optional subset
policy explains 31 of its saved 83 misses, without proving efficient arbitrary
SAT coverage or a uniformly polynomial construction.

## Previous investigation: literal-growth admission is the larger remaining gap

The [retained-clause subsumption fallback](subsumed-elimination.md) is implemented,
independently checked and proved at the semantic level in Lean. It permits ten
extra steps on the 59 remaining leaves, but closes none and removes only 24 more
literal occurrences. On the 83 original misses, both policies close **the same
29**. Total query time rises **79.65962 -> 88.16727 seconds** and database bytes
**621,146,112 -> 628,133,888**. Two opposite-order leaf comparisons also regress.
All **506 tests** and the **4,173-declaration / 2,009-theorem** Lean audit pass;
all six archives cold-check unchanged and every prior row survives. The fallback
stays optional, with the failed evidence preserved rather than promoted.

The more informative [diagnostic](../experiments/results/cnf-subsumed-elimination-originals/growth-opportunity.json)
separates clause growth from literal growth. **48/59** remaining leaves admit a
candidate with non-growing clause count without subsumption, or **49/59** with it,
under the existing pair/candidate caps. All need at most eight extra literals;
15 plain candidates need only one. None admits the current joint non-growth rule.
These are measured candidate opportunities, not new closures or runtime results.

The next ranked steps are:

1. **Test clause-count-based admission before further subsumption tuning.**
   Keep the plain baseline and explicit width/candidate/pair accounting. For an
   elimination-only chain with at most m0 clauses and decreasing variable count
   from n0, each normalized CNF has at most m0*n0 literal occurrences. The current
   per-step literal cap is stronger than needed for that local size bound. The
   argument guarantees neither a next pivot nor a bound on the entire branching
   history. Measure accepted-chain length, intermediate width, exact checks,
   cold replay and original-source closures, preserving any ordering losses.
2. **Reduce the dominant failed candidate work.** The added fallback tests 86,305
   pivots, rejects 85,902 for growth and performs 8,639,284 subset tests for no new
   original closure. Prefer a cheap plain clause-count policy to retaining this
   overhead by default. The earlier single-binary-occurrence sufficient rule and
   exact invalidation-aware reuse remain cost candidates; their timing benefit
   is still unmeasured. Operation counts alone do not establish a time breakdown.
3. **Test transfer only after a credible gain.** The two leaf orders and matched
   original misses are negative, so no fresh holdout or full-corpus promotion was
   attempted. Any stronger admission rule needs independent/adversarial controls
   and whole-source recomposition, not extrapolation from available pivots.

The optional bounded policy still closes 29 of the saved 83 misses; 54 originals
remain unresolved. The earlier full-corpus 902/985 measurement is not replaced by
these subset experiments. No efficient partition covering arbitrary SAT follows.

## Previous investigation: checked elimination broadens coverage at extra cost

The [bounded-elimination extension](variable-elimination.md) introduces complete
opposing-pair projection at previously unresolved terminal nodes, with independent
checking and model restoration. A separate pure-only control uses pair limit zero.
On the **99 saved unresolved leaves**, baseline / pure-only / bounded close
**0 / 14 / 37**. On the **83 original unresolved sources**, starting from the same
paid 417,370,112-byte prefix, they close **0 / 11 / 29**. The bounded candidate
retains every pure-only closure and leaves **54 originals / 59 selected leaves /
26,205 literals** unresolved. This is a measured whole-input gain on prior misses,
not a rerun of all 1,497 cases or a new default policy.

Coverage is more expensive here. Original-source total query time is
**64.76503 / 71.86221 / 80.09857 s**, and database bytes are
**605,675,520 / 627,138,560 / 621,146,112**. The ordinary solver still searches the
original CNFs with identical counters. All old rows are retained. Exact source
and child bindings, growth caps and all opposing pairs remain checked. Lean
proves the semantic projection identity; it does not refine Python or its costs.
All **501 Python tests** and the expanded **4,168-declaration / 2,004-theorem**
Lean audit pass. See the [frontier](../experiments/results/cnf-variable-elimination-frontier/README.md)
and [whole-input](../experiments/results/cnf-variable-elimination-originals/README.md)
records for separate cold, memory and model checks.

The new measured cost is failed candidate analysis: **167,129 candidates tested,
156,757 growth rejections, 1,457,523 opposing pairs visited**, versus **2,822**
accepted elimination nodes. Raising the pair cap alone does not address that
dominant rejection category. The next ranked investigations are:

1. **Profile and avoid repeated failed elimination analyses.** Test exact reuse
   of unchanged occurrence neighborhoods or inexpensive rejection bounds before
   building all resolvents. Source updates can change retained-clause duplicate
   membership even if pivot occurrences are unchanged; include that dependency
   in recognition, invalidation and checking. Do not assume counters equal time.
   The accepted mixed steps include 1,588 with a single occurrence on one side,
   versus 111 with multiple occurrences on both sides. Test a cheap sufficient
   rule for a single binary occurrence before exhaustive ranking, charging any
   changed order/coverage. Exact target sharing is sparse: 2,822 elimination edges
   reach 2,821 distinct targets, with only one repeated incoming reference.
2. **Remove provably redundant resolvents before judging growth.** A retained
   subclause may already imply a new resolvent. Measure this opportunity on the
   remaining frontier before changing the policy; preserve complete opposing-pair
   coverage, exact recomposition and model lifting. A smaller target is not by
   itself a cheaper expansion.
   The read-only follow-up identifies this opportunity in **10/59** current open
   leaves. **58/59** still have pair-bounded candidates but no currently non-growing
   step; simply increasing the pair cap is therefore not the main next test.
3. **Measure transfer and ordering effects.** The new study deliberately targets
   previous failures. A separate fresh/adversarial policy comparison, alternative
   elimination order and a full-corpus rerun remain open before promotion. Pure
   elimination is a control, not a novel method or an omitted baseline.

The prior full prepared result remains **902/985**. Twenty-nine of its saved
misses now have additional checked closures under the new policy. Keep this
source-level evidence separate from a new full-corpus timing/coverage claim.
No uniform polynomial solution for arbitrary SAT has been established.

## Previous investigation: clause overlap is real, but scalar caching loses

The [clause-mask follow-up](clause-mask-reuse.md) tests the smaller shared structure
suggested by the preceding source-index failure. Two costly prepared sources reuse
immutable clauses at **70.32% / 70.53%** of clause visits. A checker-owned 64-bit
mask can skip a clause only when assignment overlap is impossible; collisions
trigger ordinary scanning. The bounded FIFO stores validated representation facts,
with every source reason and fixed point still checked. All **496 tests** pass.

Two matched 96-input empty-history controls, in opposite execution orders, reject
promotion. Literal work including preparation falls **4,173,407 -> 1,873,711
(55.10%)**, but total query time rises **7.37185 -> 7.56226 s** and
**7.31352 -> 7.57542 s**. Sampled four-case Python peak rises about **41%**;
first-order values are **615,971 -> 871,147 bytes**. All four databases are identical
at **33,460,224 bytes**, answers and proof records agree, and cold replay passes.
Both modes retain **88/96** closures. The three-source prepared pilot is nearly
flat in runtime. The optional cache stays disabled; no full prepared-corpus run
is justified by these controls. This is not evidence of a universal slowdown,
but it defeats an inference from a high hit rate or lower literal counts alone.

The older full-run attribution still puts about **83% of discovery time in 83
unresolved sources**. Reconstruction is its largest profiled individual own-time
entry on source 1194; a short per-clause scan is not necessarily worth caching.
No new family closes, and the historical prepared frontier remains **83 sources /
99 selected leaves / 31,203 literals**. The next ranked targets are now:

1. **Bounded, independently checked variable elimination on the unresolved
   frontier.** First measure which inputs admit small transformations, including
   recognition and possible growth. Retain exact recomposition and model lifting.
   Prefer eliminating future residual acquisition or exposing a known family to
   another attempt at scalar cache tuning. This is an investigation, not an
   established efficient solution for each unresolved category.
2. **Transport into equivalent cores and coarse shared transformations.** A
   useful representation must avoid whole recognition/checking or substantial
   output work across different CNFs. Fixed-position block overlap was measured
   only by unbounded observer sets, not implemented as a production cache. Require
   stable order and proof-reason positions plus explicit invalidation and cost.
3. **Selected proof dependencies and append-only upgrades.** Preserve failed
   acquisition traces while checking only sound required dependencies. Keep this
   lower priority than unresolved-source discovery; exact closed-plan reuse has
   a smaller measured cost ceiling.

Do not repeat source-capacity increases or per-clause dictionary caches without
a new mechanism that avoids their measured overhead. Both negative comparisons,
their complete archives and the diagnostic counters are retained. The default
policy remains **898/985** and optional prepared coverage **902/985**; those are
historical full-corpus results, not new measurements of this checker candidate.

## Previous investigation: exact object identity misses reusable structure

A cold-cache profile of source 1194 identifies independent reconstruction as the
largest individual Python own-time cost: **2,617 calls / 0.33136 own seconds** in
a 3.08000-second instrumented query. The optional [checker source index](indexed-check.md)
was implemented and tested, but its first matched control failed to improve cost.
On 96 inputs with empty history, discovery changes **6.36510 -> 6.63704 s**,
total **7.54255 -> 7.89263 s**, and sampled Python peak **615,971 -> 738,163 bytes**.
All answers, evidence and 88 closures agree; storage is unchanged. No default changes.

The key result is the failed reuse mechanism. Only **658 / 15,071** checks hit the
source-identity index. Preparation examines **4,054,848** literals, followed by
**471,454** affected-clause literal visits; the old scan examines **4,173,407**.
Avoiding unaffected scans did not avoid rebuilding nearly all indexes. On source
1194, raising the budget **32-fold** leaves both views together at exactly
**80 / 2,617 hits**, with **2,537 admissions** and **858,647 preparation literals**.
Capacity alone does not fix this measured case.

An additional bounded source-identity/assignment memo for restricted results was
also preserved. In the same isolated source it gets **498 / 3,231** restriction
hits, but checker hits only rise to **141 / 2,617**. Timings are **1.12695 s** for
the existing implementation, **1.17052 s** for indexing alone and **1.19950 s** for
the combined candidate. These are single ordered diagnostics, not general ratios.
The negative control and pilot did not justify a full 1,497-input expansion run.
The candidates remain separate, experimental and unpromoted.

A no-eviction audit bounds the exact-whole-source opportunity: **2,537 distinct
source objects represent 2,167 distinct CNFs**, leaving **370 duplicate admissions**
(14.58% of object admissions). There are still only 80 identity hits. Holding all
sources costs 2,215,640 logical index slots in this diagnostic. Exact tuple interning
could at most eliminate those 370 duplicate admissions here, before its own hashing,
equality and retention costs. It cannot combine the 2,167 different CNFs.

Next investigate **checked reuse across related but unequal residuals**, especially
unchanged clause blocks and small assignment deltas. First measure their overlap
and how much preparation can be updated locally while preserving source binding,
clause order and unit-reason positions. The older clause-support cache already
regressed, so reuse its negative evidence rather than repeating a dictionary lookup
per clause without an amortization argument. Exact whole-CNF interning is a smaller
bounded opportunity in this case, not the main expected win. Charge discovery,
local verification, invalidation, output assembly and retained space; a shared
representation does not by itself justify cheaper independent checking.

Broader equivalent-core transport, checked binary variable elimination, selected
closed-proof checking and later append-only upgrades remain open. The latest full
prepared result is still the earlier **902/985**, with 83 unresolved sources; these
new controls establish no coverage gain. See [profile and failed pilots](../experiments/results/cnf-indexed-check-profile/README.md)
and [matched empty-history evidence](../experiments/results/cnf-indexed-check-empty/README.md).

## Previous investigation: reusable evidence from unsuccessful expansion

Cost attribution changes the immediate priority: the **83 unresolved inputs use
67.35991 / 81.41598 discovery seconds (82.74%)** in the accounted run. Directly
retained closed roots use only 13.74019 seconds. A selected closed-proof checker
therefore has a smaller measured ceiling than reuse that also addresses open
expansions. The per-case attribution is preserved with the new full experiment.

The optional [prepared-probe extension](prepared-probes.md) reuses source-bound
probe traces from old **unclosed** plans, after independent checking. In the
matched 1,497-query run, 2,437 traces avoid fresh acquisition: probe attempts
fall **77,804 -> 60,972 (21.63%)**, while checked attempts stay **77,498**.
Discovery changes **79.80360 -> 78.51427 s (1.62%)** and total query time
**85.97296 -> 84.07622 s**. This is a modest single-run timing difference; some
of the total change occurs in the unchanged ordinary solver and is not a search
saving. Both modes include transactional accounting. No new family closes.

All evidence tables and the final database bytes match. Storage stays
**629,280,768 bytes**, six-case Python peak is **24,164,349 / 24,199,805 bytes**,
and full cold audit costs **77.21884 / 76.58480 s**. The new hint has one-call
lifetime and uses the existing bounded verification cache; it does not remove
old evidence or reduce the two graph caches. The empty-history control reuses
zero traces, so its timing variation cannot support this mechanism. Fresh inputs
also reuse no traces and regress **7.70214 -> 8.61204 s** in total query time.
See the
[full evidence](../experiments/results/cnf-prepared-probes-full/README.md) and
fresh/empty controls there. All 481 Python tests pass.

The next ranked targets are:

1. **Avoid repeated checking and construction inside unresolved expansion.**
   The full run still performs 110,811 simplification checks over 41,141,207
   literal visits, and new probe checking barely changes. These are operation
   counts, not a time attribution. Profile a costly unresolved source to separate
   residual reconstruction, normalization, recognizers and evidence admission,
   then test sharing an exact checked intermediate state across transformations.
   Preserve source, assignment and policy bindings, bounded cache costs and
   invalidation. Another acquisition-only cache has a limited demonstrated gain.
2. **Broaden reuse beyond an exact CNF/depth match.** There are still 83 open
   originals / 99 selected leaves / 31,203 literals. Checked binary variable
   elimination or transport into an equivalent core may expose a shared solved
   structure. Measure actual source gains and all interface/model-lift costs;
   neither a local rewrite nor a complete partition guarantees efficient closure.
3. **Check selected sound dependencies of closed plans with shared state.**
   Keep failed alternatives archived, but avoid checking them when an independent
   selected proof suffices. This remains worthwhile, with the smaller cost ceiling
   above; it was not implemented in this run.
4. **Admission and later upgrades.** Reject references whose recognition/checking
   costs exceed avoided acquisition, and allow append-only upgrades after useful
   later preparation. The original fresh control's family-only references still
   save no descendant acquisition. Neither mechanism is implemented here.

Default coverage remains 898/985; optional prepared coverage stays 902/985.
No uniform arbitrary-SAT resource bound or new Lean refinement follows.

## Previous investigation: remove archive scans; return to discovery costs

The optional [transactional accounting](residual-accounting.md) removes the
per-query residual census without changing search or discovery. On the same
prepared prefix and 1,497 queries, total query cost falls **171.12270 -> 87.88366 s
(48.64%)**. The ordinary solver portion falls **90.03441 -> 6.40760 s**;
discovery stays **80.99467 -> 81.41598 s**, now about **92.6%** of the accounted
query total. This is a bookkeeping saving on prepared history, not faster fresh
SAT search or new structural coverage. Coverage remains **902/985** in both modes.

All per-query archive totals and all three stored evidence-table digests agree.
Every seed row remains unchanged. One opening census is charged; no further
census occurs during acquisition or warm reuse. Initialization grows
**0.00098 -> 0.12228 s**. Added archive overhead is **4,096 bytes**. Warm combined
discovery-and-solver replay falls **84.36440 -> 0.61496 s**; this is not the old
discovery-only warm metric. Full cold proof audits still cost **84.49631 / 79.18184
s**, and six-case Python peaks remain **24,159,525 / 24,164,413 bytes**. The
empty-history control has no clear acquisition gain (**7.70202 -> 7.73052 s**).
The 96 fresh-input controls with prepared history improve **15.20412 -> 8.38678
s**, keeping 88 closures and identical acquired evidence. Their saved scan work
does not imply faster underlying SAT search.
The original scan-based solver remains the control; use the optional accounted
mode in future prepared-archive experiments to expose reasoning costs clearly.

The next ranked targets are:

1. **Reuse a selected sound proof without rechecking all failed acquisition
   alternatives or retaining two large decoded graphs.** Discovery is now the
   dominant measured query cost. The existing profile points to reconstruction,
   propagation and normalization; the retained-plan run checks 13,315 old nodes
   and acquires 13,560 new ones. Develop a source-bound selected-proof checker,
   preserving the full historical trace separately. Compare its cold checking,
   admission and cache costs against the current full-policy checker. A smaller
   proof representation alone does not establish cheaper first use.
2. **Transfer useful structure beyond exact prepared sources.** The 83 unresolved
   original inputs / 99 selected leaves / 31,203 literals are unchanged. Checked
   binary literal elimination and transport of successful plans into different
   equivalent cores are the next coverage candidates. Preserve shared-variable
   compatibility, model lifting and remaining branch obligations explicitly.
3. **Avoid references that save no substantive acquisition.** The previous fresh
   control's 20 references are all family leaves and save no nodes. A cheap
   admission rule needs matched total-cost evidence, including its own lookup.
4. **Upgrade cached unsuccessful plans when later preparation becomes useful.**
   This needs append-only successor identities and explicit dependency rules;
   the exact-reference implementation only benefits first acquisition.

All **476 Python tests** and the unchanged Lean build/axiom audit pass (**4,148
declarations / 1,988 theorems**). The default classification policy is unchanged
(898/985); the 902/985 result uses the optional prepared policy. The accounting
change supplies no new Lean refinement, SAT family or unrestricted polynomial
bound. See the [full matched evidence](../experiments/results/cnf-accounting-full/README.md).

## Previous investigation: reuse closed plans; expose metadata and cache costs

The [retained-plan reference](retained-plans.md) reuses an independently checked
old graph before acquiring another graph for the exact same CNF and depth. On a
common 417,370,112-byte prepared prefix, non-tiny closure improves **901/985 ->
902/985**, recovering source 1471 with no losses. Discovery drops **98.33619 ->
81.96656 s (16.65%)**, total **190.63432 -> 177.05292 s (7.12%)**, added archive
**338,288,640 -> 211,906,560 bytes (37.36%)**, and combined archive
**755,658,752 -> 629,276,672 bytes (16.72%)**. Preparation remains charged as
earlier history; this is not a from-scratch portfolio. The default stays unchanged.

The tradeoffs are retained. Six-case Python peak rises **20,124,942 -> 24,084,738
bytes (19.68%)**, and warm replay **0.27327 -> 0.41059 s**. The 96 fresh inputs
at depth two keep 88 closures, with discovery **6.57530 -> 6.80303 s**. All 20
fresh internal references point to family nodes; both modes add 1,988 nodes.
The empty-history control also gains nothing and costs 4.76% more discovery.

The next ranked targets are now:

1. **Stop rescanning the complete residual archive for metadata on every query.**
   `ResidualSolver.solve` runs a full `count/sum(length(...))` census even on a
   cached decision. A separate 12-repeat diagnostic on 21,838 rows / 65,665,771
   payload units averages **57.14 ms** per scan. Multiplying by 1,497 queries
   suggests about 85.54 seconds of bookkeeping, not an exact attribution of the
   92.18/94.98-second solver portions. Maintain exact statistics or collect them
   outside the per-query decision path, with initial reconstruction, updates and
   invalidation tested. This is the largest concrete avoidable runtime cost in
   the current measured total; it is not SAT search or a complexity breakthrough.
2. **Share verification work without retaining two large decoded graphs.** The
   new run checks 13,315 old nodes and adds 13,560 new nodes. Old-policy validation
   still checks every failed alternative, even when only a selected closed proof
   is needed. Develop a source-bound soundness checker for reusable selected
   proofs, keeping the full historical trace archived separately. No selective
   checker, bounded shared cache or general proof transport is implemented yet.
3. **Prefer references that avoid real descendant acquisition.** The full run
   has 2,127 references, including 463 old OR and 1,116 probe nodes; the fresh
   control's 20 references are all family leaves and avoid no node acquisition.
   Measure an admission rule against these retained losses. An exact match alone
   does not imply a cheaper expansion.
4. **Expand beyond exact prepared sources.** There remain 83 uncovered original
   inputs / 99 selected unresolved leaves / 31,203 literals in this optional
   prepared run. Checked binary literal elimination and transport to genuinely
   different equivalent cores remain candidates. Cached misses also need explicit
   append-only upgrades when useful preparation arrives later. None follows from
   the exact-reference rule, and fresh-input coverage has not improved.

All **469 Python tests** and the unchanged Lean build/axiom audit pass (**4,148
declarations / 1,988 theorems**). No new Lean refinement is claimed. All 63 earlier
manuscript proof blocks are unchanged. The [full evidence](../experiments/results/cnf-retained-plans-full/README.md)
preserves both complete archives, reference-kind counts, cold checks, allocation
regressions and profile. Benchmark-only failures and frozen runner versions remain
retained; completed acquisitions were recovered from verified checkpoints.

## Previous investigation: binary paths broaden coverage but add acquisition state

The [binary-path experiment](binary-paths.md) deletes wide clauses entailed by
paths in retained original binary clauses. Checked transitive reasoning raises
full non-tiny coverage **898/985 -> 901/985**: four gains, one bounded-search loss.
All ordinary SAT answers agree. Extra-depth frontier closure rises **60/106 ->
63/106**, including against an early direct-subsumption control. A fresh 96-case
sample stays at 75 closures. This established simplification is optional; the
retained default remains **898/985**.

The full matched run charges discovery **81.47602 -> 97.00720 s (+19.06%)**, total
**122.46371 -> 139.46329 s (+13.88%)**, archive **417,370,112 -> 475,529,216 bytes
(+13.93%)**, and cold replay **52.18170 -> 59.56008 s**. A separate slow-source
profile still leads with reconstruction, propagation and normalization. Shared
proofs reduce node count but increase JSON bytes versus independent paths;
even all 456,745 proposal bytes are small beside the 58,159,104-byte archive
increase. Prioritize avoiding intermediate acquisition, not proof encoding alone.

The next ranked gaps are:

1. **Carry successful plans through equivalent-state changes.** Source 1471
   isolates a concrete loss: the old successful split at variable 1 drops out of
   a four-candidate child list after sound deletion. The earlier certificate is
   retained; the two complete archives cover 902/985 inputs in union. Build a
   source-bound, independently checked reuse path before acquiring another full
   policy graph. That observed union is not an efficient combined algorithm.
2. **Share preparation and avoid duplicate intermediate states.** The pass makes
   3,555 positive reductions but acquires 3,507 additional pattern nodes overall.
   Test whether retained-binary indexes and checked reduction plans can survive
   normalization with explicit clause/name transport. Preserve verification,
   invalidation and cold replay costs; no such shared layer exists yet.
3. **Use the same relations to expose more structure.** Certified hidden-literal
   elimination could shorten clauses that cannot be deleted. Test binary-free
   states after conditioning and adversarial edits, with exact model semantics.
   This is established preprocessing, not a new tractability claim; its useful
   scheduling and full acquisition cost remain open here.

All **461 Python tests** pass, and the Lean build/axiom audit passes at **4,148
declarations / 1,988 theorem declarations**. Four new semantic lemmas prove edge,
path, clause and batch soundness; Python refinement and uniform resource bounds
remain separate. The [full evidence](../experiments/results/cnf-binary-paths-full/README.md)
preserves every gain/loss, cold-checked archive, allocation diagnostic and profile.
All 62 earlier manuscript proofs survive alongside the new proposition.

## Previous investigation: saved unit counts do not predict cheaper closure

The [checked probe-ranking experiment](probe-rank.md) preserves the entire old
candidate set and changes only order. Two reversed-order frontier runs keep
**60/106** closed but regress in mean discovery **5.19854 -> 5.44908 s (4.82%)**
and total **8.22342 -> 8.63390 s (4.99%)**. Both attempt 268 candidates, despite
26 changed orders. Fewer nodes (1,540 -> 1,524) coexist with more SQLite bytes
(35,840,000 -> 35,979,264). The policy stays optional; do not promote it.

The frozen fresh controls keep **71/96** closed and change no order. Of 39 OR
states, **36 have no binary clauses**; just **9/156** candidate positions have
paired original traces. For a normalized CNF of minimum width three, one assignment
cannot create a unit, so these missing single-variable effects cannot be repaired
by another unit-count score. Both execution orders, archives and regressions remain
retained. Original-source coverage stays **898/985**.

The next ranked gaps are:

1. **Expose interactions invisible to a single-assumption probe.** Investigate a
   bounded two-variable interface or the binary relation exposed after one split
   on the unresolved binary-free states. Require exact recomposition and charge
   candidate discovery and all branches. There is no small-interface guarantee
   for arbitrary SAT. Do not replace missing evidence with a zero-effect score.
2. **Reuse a successful plan independently of the ranking that found it.** The
   prior obstruction/baseline union remains 63/106; running both costs extra.
   Source/child-bound, independently checked plans could avoid reacquisition and
   repeated policy-key state. No such portable plan layer is implemented yet.
3. **Reuse proof work directly before tuning another proxy.** Conditioning still
   constructs and normalizes residuals, then prepares/checks their closures.
   Reusing original probe reasons there requires clause-index and variable-name
   transport; ranking by the number of reasons performs none of that transport.
   Whole-source reconstruction/normalization remains the measured dominant cost.
4. **Keep coverage preservation distinct from efficiency.** Two new Lean lemmas
   prove candidate membership and local closure invariance given corresponding
   child closures. Global finite-expansion induction also requires unchanged
   reductions/budgets and no history-dependent timeout. There is no Python
   refinement, optimality result, or new unrestricted-SAT tractability claim.

Implementation/evidence checkpoint **7b5fa22**. The full Lean build and axiom
audit pass (**4,140 declarations / 1,981 theorem declarations**). All 61 previous
manuscript proof blocks survive, with one new local-closure proposition.

All **453 Python tests** pass. Cold replay checks every saved proof/source and
preserves bytes; warm replay adds nothing. Fresh-key overhead is measured rather
than ignored. Four-case allocation diagnostics do not bound total process memory.
See the [frontier evidence](../experiments/results/cnf-probe-rank-frontier/README.md)
and [fresh evidence](../experiments/results/cnf-probe-rank-fresh/README.md).

## Previous investigation: static obstruction ranking regresses

The [matched frontier experiment](../experiments/results/cnf-obstruction-frontier/README.md)
gives the 106 previously exhausted leaves one extra conditioning level in both
modes at the same four-candidate/probe/learning limits. A new checked ranking
based on auxiliary-path source clauses closes **57/106**, versus **60/106** for
the existing ranking: three gains, six losses. Discovery **4.96403 -> 5.21714 s**
regresses 5.10%, fresh SQLite **35,840,000 -> 37,498,880 bytes**, and cold replay
**3.49873 -> 3.53507 s**. The ordinary solver varies in the opposite direction,
leaving total almost unchanged. This is a negative result; **do not promote** the
optional `ObstructionChoicesInventory` or treat it as new whole-source coverage.
The retained original policy stays **898/985**, with 87 source misses.

The next ranked gaps are:

1. **Reuse checked propagation influence instead of relying on direct overlap.**
   All six losses discard the old winning variable; five such variables lie
   outside the saved obstruction's source support. In case 4, original checked
   traces under variable 6 reach the obstruction indirectly and damage three/four
   of its four auxiliary edges. No fresh propagation was needed to recover this
   information. Test those already-proved consequences in a class-aware bounded
   choice policy that retains baseline diversity. Cases 17 and 50 are mandatory
   counterexamples: their original probes damage no saved edge but later discovery
   closes the branches. Missing traces for other candidates are unknown, not zero
   influence. Breaking one recorded path proves neither renamability nor closure.
2. **Separate successful structural evidence from the ranking that found it.**
   The two frontier policies' union is 63/106. Merely running both has extra cost;
   an efficient combined policy is not implemented. The saved proofs can inform
   a future portable-plan layer with exact source/child bindings and cold checks,
   avoiding policy-key duplication and repeated acquisition. Preserve every old
   result and measure recognition/check/serialization costs before claiming reuse.
3. **Keep the whole-source bottleneck in view.** This extra-depth frontier study
   does not replace the earlier whole-corpus profile: the retained 87 source misses
   still account for 70.6% of discovery, with reconstruction, normalization and
   indexed subset checks leading on source 1448. Broader coverage needs interactions
   across classes, not another unguided increase in search depth or pair budget.
4. **Use fresh evidence before promoting a revised heuristic.** The 106 leaves
   are development data. New seeds, signed edits and adversarial mixtures must
   accompany any follow-up comparison; keep the same budget and retain losses.
   A single selected certificate is not an isomorphism-invariant structural model,
   and small traced memory diagnostics do not bound total process memory.

All **448 tests** pass, including independent cold replay without auxiliary
rediscovery. Both complete archives, all nine changed cases, guarded-support
counterexamples and original-probe influence traces are retained. The
[proof/resource account](obstruction-conditioning.md) distinguishes raw restriction
from propagation and other-family closure. All 60 earlier manuscript proof blocks
remain, with one new obstruction-preservation proposition. Lean sources are
unchanged; no new Python refinement or unrestricted tractability result follows.
Implementation/evidence checkpoint **d25a2e5**.

## Retained baseline: 35 renamed leaves yield 29 source closures

The [terminal Horn-renaming study](../experiments/results/cnf-polarity-horn/README.md)
closes all 35 saved positive leaves and **29 additional whole inputs**, with no
lost closures: **869/985 -> 898/985 non-tiny**. Full acquisition adds 188 checked
renaming edges; the ordinary SAT solver is unchanged. Most remaining work remains:
**87 sources / 106 selected leaves / 32,404 literals** unresolved, consuming
**70.6% of discovery time**. Every remaining leaf has a checked renaming exclusion;
none is merely capped. Auxiliary UNSAT is not original UNSAT.

Single-run discovery falls **84.99193 -> 80.78495 s (4.95%)**, total **126.02211 ->
122.78419 s**, cold replay **54.89246 -> 51.32492 s** and fresh SQLite **437,620,736
-> 417,370,112 bytes**. Warm replay regresses **0.26877 -> 0.29138 s**. Six-case
Python peak falls **24,073,154 -> 20,286,004 bytes**; this excludes native SQLite,
RSS and full-corpus peak. Old and new snapshots remain retained (854,990,848 raw
bytes together). Do not describe fresh-policy comparison as freed historical space.

The next ranked gaps are:

1. **Explain the checked renaming obstructions through interactions.** Of the 106
   remaining leaves, 92 have maximum width three, 13 width four and one width
   eleven. Source-linked negative auxiliary paths identify a concrete obstruction
   to this class. Investigate shared variables across those paths and small
   interfaces whose exact conditioning exposes different recognized families in
   different branches. Compare coverage and total discovery under matched budgets;
   a conflict path alone gives no small separator/backdoor guarantee. Do not rerun
   the same recognition as though the exclusion were a budget miss.
2. **Reduce repeated acquisition while preserving these proofs.** Source 1448 is
   the current slowest unresolved discovery query. Its separate instrumented
   profile has 909 reconstructions (0.16950 s own / 0.24526 s cumulative), 566
   normalizations (0.12614 / 0.32228 s) and 118 indexed subset-certificate calls
   (0.11573 / 0.15694 s). Polarity discovery is only 31 calls / 0.04967 s cumulative.
   Exact normalization/source-state reuse is supporting work; its lookup, memory
   and invalidation costs must beat rebuilding. Nested cumulative costs are not
   additive.
3. **Test earlier renaming only as an acquisition optimization.** The separate
   0.57908 s original-root probe recognizes 555 normalized inputs, all already
   closed by the baseline; none of the 29 gains admits a whole-source renaming.
   The gains therefore need residual exposure and composition. Earlier cheap
   admission might avoid known-family preprocessing but alone will not cover the
   remaining sources. Keep its recognition budget and overlap policy explicit.
4. **Broaden evidence and avoid policy-state duplication.** This is one sequential
   synthetic-corpus comparison. Full mixed-policy migration space, industrial
   transfer, total-process memory and repeated balanced timing remain unmeasured.
   Versioned keys preserve old rows but duplicate unchanged structures between
   policies. A policy-independent structural layer needs exact evidence bindings;
   never drop the prior verified archives merely to report smaller storage.

All **441 Python tests** and the full Lean build/axiom audit pass (**4,136
namespace declarations / 1,977 theorem declarations**). Both cold archives are
byte-preserving, all 188 new edges have independently agreeing endpoints and
checked model lifts, and warm replay inserts nothing. All 59 earlier manuscript
proof blocks survive; a new polarity proposition is added. Implementation
checkpoint **86d603b**. The exact 35-leaf target is complete; unrestricted efficient
coverage and the interaction obligations above remain open.

## Previous checkpoint: one-pass checking; 35 polarity-renaming opportunities

The [one-pass checker study](../experiments/results/cnf-single-pass-check/README.md)
reduces full discovery **93.90373 -> 87.70857 s (6.60%)** and total **137.78680 ->
130.04664 s (5.62%)**, with identical 1,497 answers, profiles and archive bytes.
It shares 44,643,882 untouched literal occurrences without another retained cache.
The initial clause-support cache regressed in both pilots and remains unselected.
Cold replay regresses **57.32273 -> 57.93447 s**; six-case Python peak is essentially
unchanged (**24,072,934 -> 24,073,162 bytes**). Twelve-query ABBA BAAB means support
4.60% total / 5.23% discovery savings, with overlapping samples. Forty-eight
controls retain five regressions, especially wide clauses with many removals.

Integrated coverage remains **869/985 non-tiny**, with **116 sources / 148 leaves /
33,651 literals** unresolved. A separate checked, read-only frontier probe now
identifies **35 leaves (852 literals)** that become Horn after consistent variable
flips. It checks positive renamings directly and negative auxiliary implication
paths, with 32,018 pair constraints. This established class is absent from the
current inventory. These are leaf opportunities, not achieved source closures.

The next ranked gaps are:

1. **Integrate checked polarity renaming before further cache tuning.** The 35
   frontier certificates provide concrete broader-coverage evidence. Use a
   versioned recognizer/terminal certificate, explicit model transport and exact
   recomposition; test unlabelled signed variants, edits, exhaustive small formulas
   and fresh mixtures. Compare full acquisition and cold replay. Auxiliary
   pair-formula UNSAT excludes renamability, not SAT of the original formula.
   The method is established: [Mannila and Mehlhorn (1985)](https://people.mpi-inf.mpg.de/~mehlhorn/ftp/RenamingHorn.pdf)
   describes the pair-constraint characterization. Most unresolved literal work
   lies outside these small positives; do not infer complete class coverage.
2. **Normalization and residual reconstruction remain substantial.** The current
   run's slowest unresolved source is 1446. In its separate profile, 1,063
   reconstructions fall 0.37732 -> 0.29957 s cumulative, while normalization has
   678 calls / 0.40226 s cumulative. The new helper remains largest named own time
   at 0.20778 s. Measure identical normalization inputs and exact transport costs
   before proposing reuse; do not skip canonical identities or checker bindings.
3. **Keep the measured copying limits visible.** Wide affected clauses regress
   in all three helper-control sizes. Mutable inputs still copy; partial buffers
   may be discarded after late satisfaction. No new cache helps the selected
   method, but the source/proof graph and 437,620,736-byte archive remain. The
   conditional worst-case reconstruction bound stays O(1+A+m+L).
4. **Remaining interactions and acquisition are still open.** The 35 positive
   renamings account for only 852 of 33,651 frontier literals. Keep the other 113
   selected leaves explicit and investigate exact decompositions/relations there
   after integrating and measuring the recognized class. Closed leaves do not
   by themselves establish closed roots or uniform polynomial expansion.

All **433 tests** pass; full cold replay is byte-identical. All 58 earlier proof
blocks survive, with one new reconstruction invariant; Lean is unchanged. The
implementation checkpoint is **d0b8917**. The result, failed cache attempts,
diagnostic, bounds and concrete next frontier certificates are all preserved.

## Previous checkpoint: source-index reuse exposes checker reconstruction

The [indexed-restriction study](../experiments/results/cnf-indexed-restriction/README.md)
reuses validated immutable source indexes across assumptions, rebuilding affected
clauses and sharing unchanged tuples. All **1,497 answers, profiles and archive
bytes agree**; coverage remains **869/985 non-tiny**, with **116 sources / 148 leaves /
33,651 literals** unresolved. The independent checker still reconstructs its input
branch directly; indexed branch construction remains trusted Python.

The first full comparison is mixed: discovery **93.85938 -> 90.65563 s**, cold
replay **60.86819 -> 56.04772 s**, but total **132.36551 -> 134.44214 s** regresses.
The unchanged solver path takes 13.70% longer; one sequential sample cannot
separate variation from cache-induced process/memory effects. Twelve-query ABBA
BAAB mean total **4.81769 -> 4.35747 s** supports locality-dependent savings,
not a general full-corpus result. A reversed-order full comparison is retained
separately in the linked study. Six-case Python peak grows **1,598,364 bytes**;
SQLite stays **437,620,736 bytes**. The 32,768-unit index cap is not a byte cap.

The reversed full run balances order across two samples per mode. Paired means
are **137.36963 -> 131.36045 s total (4.37%)**, **97.29044 -> 89.16122 s discovery
(8.36%)**, and **61.16937 -> 56.70501 s cold replay (7.30%)**. Counters and archive
hashes repeat exactly. These limited synthetic controls support an optional
tradeoff; the first regression and roughly 1.60 MB peak increase remain relevant.

The next ranked gaps are:

1. **Independent simplification reconstruction is now the largest named cost.**
   Source 1194's restriction cumulative time falls **0.82784 -> 0.21269 s** for
   the same 3,399 calls. Its **2,303 simplification checks** remain at **0.27952 s
   own / 0.55562 s cumulative**; full reconstruction stays **51,574,914 literal
   visits**. Measure repeated semantic inputs before choosing exact checked-result
   reuse or independent prepared-state reconstruction. Do not treat unverified
   discovery state, mutable proof identity or incomplete source bindings as checks.
2. **Broader SAT pattern coverage remains a primary research obligation.** These
   resource optimizations add no category. Select a concrete source-entailed
   relation or exact interaction decomposition in the 116 unresolved sources;
   measure removed unresolved leaves and recognition cost. Faster unchanged
   classifications alone do not resolve the discovery gap.
3. **New/equal-source preparation and materialized output remain expensive.**
   Full operations have 241,198 hits / 275,865 calls, but still validate and prepare
   **10,412,650 literals each**, then assemble **28,938,355 clause positions**.
   Equal reallocation and fresh-append controls have no hits and regress. Sharing
   exact source descriptions or append-prefix postings needs explicit binding and
   invalidation. Reusing exact source/assignment results could avoid repeated outer
   assembly, but adds retained state and must preserve immutability.
4. **Reduce memory and check broader workloads before wider adoption.**
   The index's logical cap does not make its 1.60 MB Python peak increase free.
   Sparse reuse is favorable, while equal reallocations peak at 3.24 MB in a helper
   control. Capacity sweeps, admission policies and total-process measurements
   remain open. Retain the baseline and all regressions; do not infer universal
   wins from a warm helper stream or selected timing subset.

All **425 tests** pass; full and pilot archives replay cold byte-identically.
Tests cover 87,516 small formula/partial-assignment pairs, 4,000 random/edited
restrictions and the 148 saved frontier probes. The
[correctness and resource account](indexed-restriction.md) explains validated
immutability, strong references, fallback behavior, output sharing and conditional
word costs. The implementation checkpoint is **2809c48**. This is not a Lean
refinement or unrestricted expansion bound; earlier proofs and results remain.

## Previous checkpoint: propagation savings expose source reconstruction

The [ordered propagation study](../experiments/results/cnf-ordered-propagation/README.md)
uses affected-clause updates while preserving the exact original unit/reason and
first-conflict order. All **1,497 answers, profiles and database bytes agree**;
coverage stays **869/985 non-tiny**, leaving **116 sources / 148 leaves / 33,651
literals** open. The ordinary SAT solver and independent proof checker are unchanged.

Full discovery falls **111.13169 -> 97.76173 s (12.03%)**; total **154.63114 ->
137.59078 s** also includes variation in the unchanged solver. Twelve-query ABBA
BAAB means support **5.38111 -> 4.83970 s total** and **5.08503 -> 4.55072 s discovery**.
Cold replay barely changes (**63.40473 -> 62.61754 s**). Six-case Python peak grows
**22,258,170 -> 22,474,570 bytes**; SQLite stays **437,620,736 bytes**. Results are
synthetic, with no universal speedup or full-process memory bound.

The next ranked gaps are:

1. **Share source restriction and residual reconstruction across assumptions.**
   Source 1194 still performs **3,399 restrictions** and **2,303 simplification
   checks**. After propagation cumulative time falls **0.79372 -> 0.31541 s**,
   restriction is the largest named own-time cost (**0.40355 s own / 0.82048 s
   cumulative**); checking has **0.27656 / 0.54588 s**. Full restriction and
   reconstruction visits remain **82,210,169 / 51,574,914**. Prepare immutable
   source indexes and update exact affected state, with source/assumption bindings
   and independent reconstruction checks. Charge lookup, construction and invalidation.
2. **Discover new structure in unresolved interactions.** The same 116 sources
   still need certified relations or exact decompositions. This optimization
   makes experiments cheaper but adds no category. Investigate the most informative
   remaining interactions rather than increasing blind budgets or only tuning caches.
3. **Amortize or avoid wasted occurrence-index preparation.** Every closure still
   builds fresh state: **32,071,047 index entries** versus **5,356,250 affected
   occurrence visits** in the full run. A reverse chain benefits greatly, but a
   two-clause prefix conflict with 1,024 unrelated clauses regresses **0.00248 ->
   0.41982 ms**, and its Python peak grows **1,752 -> 528,448 bytes**. Test shared
   preparation or a cheap prefix/lazy-index rule before calling this pointwise
   better. Forward-chain and colliding-integer-hash regressions are also preserved.
4. **Evidence/cache space remains secondary.** The 1 MiB proof-check cache,
   duplicated evidence and unintegrated implication relevance filter retain their
   previous opportunities. They do not remove first discovery or source scanning.

All **417 tests** pass. Full and pilot cold archives replay byte-identically;
32 adversarial controls and balanced timing runs preserve exact traces. The
[algorithm-level trace proof](ordered-propagation.md) gives a conditional
O(1+L+m log(m+1)) word-operation account per closure, with map and bit-cost caveats.
It is not a Lean refinement or unrestricted SAT bound. The implementation checkpoint
is **bbd2607**; the scan baseline remains available. Next runs should start from
these new measurements, not repeat the now-completed propagation experiment.

## Previous checkpoint: exact proof reuse reduces acquisition cost

The [bounded check-cache study](../experiments/results/cnf-checked-probe-reuse/README.md)
preserves every previous structural result and the complete archive byte for byte.
On the same **1,497 inputs**, coverage stays **869/985 non-tiny**, with **116 open
sources / 148 leaves / 33,651 literals**. A successful complete probe check may be
reused only under the same full source/proof/policy key. The cache is ephemeral,
starts empty on cold replay, returns fresh decoded results and retains at most
**1 MiB of serialized strings**. Edits and evictions cause rechecking. The old
checker remains available; persistent proofs and identities do not change.

Full single-sample total time falls **168.30879 -> 150.39216 s (10.65%)**, discovery
**125.59834 -> 108.60557 s**, and cold replay **71.60183 -> 62.58623 s**. Twelve-query
ABBA BAAB means are **6.17550 -> 5.33388 s** total. These are synthetic measurements,
not a general SAT speed guarantee or significance result. SQLite stays exactly
**437,620,736 bytes**; six-case Python peak grows **21,161,086 -> 22,258,162 bytes**.
The cap excludes allocator/LRU overhead, transient construction and original state.
All full modes share the existing archive rather than retaining another copy.

The next ranked gaps are now:

1. **First-time propagation and remaining clause scans.** Source 1194's separate
   profile reduces restrictions **5,763 -> 3,399** and simplification checks
   **4,657 -> 2,303**, but propagation stays **2,221 calls** and becomes the largest
   named own-time cost. The full workload still visits **105,860,805 propagation
   literals**. Test reusable occurrence indexes or affected-clause propagation
   across assumptions, charging preparation and invalidation. Preserve or
   explicitly version proof order: changed traces can alter learning selection.
2. **New structure in unresolved interactions.** This cache preserves coverage;
   it does not discover new relations. The 116 open sources need certified
   relations or exact decomposition hypotheses, measured against their remaining
   interactions. Neither larger blind budgets nor cache hits solve this gap.
3. **Lower cache/evidence overhead without losing useful reuse.** Full operations
   have 34,971 hits / 57,798 lookups, but serialize **135.221 MB** of key data and
   decode **29.376 MB**. A 256 KiB pilot gets 1,385 versus 1,387 hits at 1 MiB;
   compare full-corpus memory and time before choosing a smaller cap. The earlier
   relevance filter (29,897 -> 7,505 implication candidates, no coverage gain)
   remains a separate possible evidence reduction. First-check and discovery
   costs cannot be replaced by unverified context.

All **410 tests** pass. A found tuple/list serialization alias is fixed by checking
the old original-attempts container requirement before lookup; its counterexample,
preliminary pilot and aborted runs are preserved. Both final full modes and all
five guarded pilot modes replay cold byte-identically, including alternatives,
source bindings and solver certificates. Reports have **62 fingerprints**, with
explicit snapshots for superseded pilot scripts. Lean source and its preceding
4,130/1,972 audit remain unchanged; this cache has no formal Python refinement.
The implementation checkpoint is **9aba9df**. No unrestricted efficiency or new
tractable class follows from exact repeated-check reuse.

## Previous checkpoint: five more closures; proof replay remains dominant

The [implication-subset study](../experiments/results/cnf-implied-subsumption/README.md)
reuses binary consequences of original checked probes as signed-subset witnesses.
It adds no propagation phase. Earlier subset exposures retain priority, and failed
pools/searches persist. A separate indexing-only mode preserves old certificates
and archive identities while skipping impossible equal-width comparisons.

Across **1,497 queries**, closure rises **864 -> 869 / 985 non-tiny**, with gains
**857, 1185, 1289, 1368 and 1467** and no losses. The old subset rises **837 -> 841 /
949**, and new-query closure **27 -> 28 / 36**. This is structural coverage, not a
change to the independent SAT decision solver. All answers agree.

Full single-sample operation time is essentially unchanged: **169.84716 ->
169.80609 s**. Discovery is **127.44196 -> 126.71711 s**, SQLite **438.288 ->
437.621 MB**, and cold replay **71.70525 -> 69.97623 s**. Logical node payload
instead grows **178.289 -> 179.396 MB**, and six-case Python peak **20.390 ->
21.161 MB**. Fewer nodes (25,752 -> 25,047) do not establish lower retained state.
The optional candidate is a coverage improvement, not a general speedup.

The next gaps are ranked by the evidence:

1. **Reuse exact restriction and proof-checking state.** The largest unresolved
   source remains 1194, at **1.67226 s** discovery. Its separate profile again
   has **5,763 restrictions, 4,657 simplification checks and 2,221 propagations**.
   These costs dominate its own-time profile even after indexing. Share prepared
   clause/assumption state or checked evidence with explicit dependencies and
   invalidation; measure acquisition and replay, not just fewer logical probes.
2. **Discover structure in the remaining interactions.** There are **116 open
   sources / 148 distinct selected leaves / 33,651 literals** in the expanded
   corpus. Filtering the existing implication pools exposes **no additional
   selected leaf**. Broader coverage needs new source-entailed relations or a
   different exact decomposition, with charged discovery and recomposition.
   Do not increase probe budgets blindly or confuse an unresolved classification
   with an efficient solver for that category.
3. **Keep only useful implication witnesses, while charging recognition.** An
   offline control retains proved binaries only when they fit a long clause of
   the original minimal core. It reduces the pool **29,897 -> 7,505 (74.90%)**
   across all 3,684 nonempty pools and preserves all **82** encountered implication
   exposures. It uses **2,278,253 relevance comparisons**; augmented subset tests
   fall **8,990,250 -> 7,138,675** per search/check. This is an unintegrated storage
   and recognition opportunity, not a measured total-cost saving or a theorem
   preserving every syntactic family. Keep exact origin proofs and old results.
4. **Reduce duplicated state and cold replay.** Search fields grow **3.963 ->
   9.030 MB**, including **5.087 MB** of implication data. Many failed pools remain
   useful evidence of limits but need not duplicate all underlying proof state.
   Exact references or shared immutable evidence require source binding and
   cold reconstruction. There is no full-process or lifetime archive space bound.

All **403 tests** and the **4,130 / 1,972** Lean declaration/theorem audit pass.
The new semantic lemma composes entailment and signed-core equivalence; Python
refinement and unrestricted resource bounds remain open. Full, pilot and previous
archives replay byte-identically, and both new reports have **59 fingerprints**.
See the study for balanced timing and complete old-archive indexing controls.
The next run should use the profiled restriction/checking bottleneck or a concrete
coverage hypothesis; the smaller implication pool alone does not improve coverage.

## Previous checkpoint: four closures, costly failed subset searches

The [signed-subsumption study](../experiments/results/cnf-signed-subsumption/README.md)
integrates the previous frontier witnesses. Only exhausted unresolved leaves
are searched; a reduced core is followed only when an existing basic family
recognizer succeeds. Exact retained signed witnesses, source-index coverage,
normalization and model lifts are checked; failed searches persist. Earlier
reductions and budgets stay fixed. All previous solver results remain available.

On **1,461 queries**, non-tiny closure rises **833 -> 837 / 949**, with gains on
**977, 1044, 1053 and 1365** and no losses. The old subset improves **806 -> 810 /
913**; new-query closure stays 27/36. This is a coverage gain, not a SAT speedup.
The full single sample grows **145.71977 -> 156.17943 s**, discovery **105.46141 ->
117.30413 s**, SQLite **404.410 -> 408.302 MB**, cold replay **61.80056 -> 66.82085 s**
and six-case Python peak **19.997 -> 20.390 MB**. Twelve-query balanced controls
instead average **7.28617 -> 6.98024 s**, but include all four gained sources;
they do not establish a full-corpus speedup. Keep the policy optional.

The ranked gaps now have direct evidence:

1. **Avoid unsuccessful recognition work while extending proof reuse.** The
   3,753 terminal searches expose only 31 local families. Discovery and checking
   each perform 33,367,619 subset comparisons. Of these, **27,083,138 (81.17%)**
   compare distinct normalized clauses of equal width and cannot succeed.
   Length buckets should skip those comparisons with identical certificates;
   preserve a fallback/check for nonnormalized inputs if the helper admits them.
   This is the immediate acquisition-cost fix, not a measured saving yet.
2. **Use already proved implications to expose more families.** Eight of the
   remaining selected leaves become 2-CNF in an offline checked control when
   all original-probe binary consequences are made explicit. This includes
   consequences filtered as binary-transitive: redundant propagation clauses
   can still be useful subset witnesses. Sources **1185, 1289 and 1368** could
   complete their present plans; five other affected sources retain an open leaf.
   Integrate after earlier priorities, retain original proof dependencies, and
   charge enumeration, indexing, witness checking and cold replay. These are
   prospective gains, not part of 837/949.
3. **Reuse restriction and proof-checking state.** The largest unresolved source,
   1194, costs **1.60328 s** discovery. Its separate profile has 5,763 restrictions,
   4,657 simplification checks and 2,221 propagations. This remains a broader
   runtime target than subset comparisons alone. A reuse design must bind each
   fixed point to its exact clauses and assumptions; changed clauses invalidate
   unproved reuse. Fewer logical probes alone do not establish less total work.
4. **Control retained state and cold replay.** The new policy has fewer nodes
   (24,367 -> 24,122) but more logical node bytes (161.206 -> 166.021 MB). Search
   certificates/profiles alone add 3.706 MB; source bindings also grow. Indexed
   or shared evidence needs exact dependencies and byte-level measurements.
   Six-case traced Python memory is not RSS or a global memory bound; preserving
   multiple policy archives retains all their state.
5. **Cover the irreducible interactions.** There remain **112 open sources / 149
   selected leaves**, with 32,043 literal occurrences. Most subset reductions
   do not expose a basic family. The next methods must recognize interactions
   beyond this bounded search, with exact recomposition and charged discovery.
   An explicit unresolved category completes a partition, not an efficient
   solution for every member. No unrestricted-SAT polynomial bound follows.

All **395 tests**, three full/pilot/previous cold checks per group and **56 report
fingerprints** pass. The Lean build audits **4,129 / 1,971 declarations/theorems**,
including three signed-core semantic lemmas. Python refinement and global
acquisition/storage guarantees remain open. Next run: remove the provably futile
subset comparisons, verify identical coverage/certificates on the saved archives,
then integrate the saved implication-subset controls under a matched total-cost
comparison. Retain the naive policy and its regression as the control.

## Previous checkpoint: preserve useful probes, expose hidden 2-CNF

The [activity experiment](../experiments/results/cnf-activity/README.md) retains
old informative continuation candidates, omits checked unchanged pairs, and
fills freed positions with active original-core variables. It uses the same
batch, two phases and four-variable cap. On **1,425 queries**, closure remains
**806/913 non-tiny**, with no source gains or losses. Source 956 is recovered from
the preceding core-order regression. Source 977's unresolved part shrinks
**two leaves / 138 literals -> one leaf / 22 literals**, but remains open.

Continuation attempts fall **31,741 -> 7,184 (77.37%)**. This mainly avoids
unchanged pairs; active-plus-novel probes grow **5,334 -> 5,569**. All 421 old
local reductions in 3,001 saved states survive; sixteen clear states gain one.
All 255 earlier transition controls have a reduction. Local progress preservation
is justified, but different reductions/descendants still prevent a global
coverage monotonicity claim.

**Do not claim a runtime speedup.** The single full-run times are **161.35645 ->
134.22746 s**, but the unchanged solver varies **44.42359 -> 35.13847 s**. Balanced
ABBA BAAB trials on eight queries give mean totals **3.85140 -> 3.88671 s**, slightly
slower for activity. Cold replay also grows **55.11608 -> 57.63553 s**, and warm
lookup **0.27624 -> 0.34976 s**. SQLite shrinks **376.205 -> 375.824 MB**, logical
node payload **148.632 -> 147.670 MB**, and six-case Python peak **20.265 ->
19.997 MB**. Keep all single-sample and memory-scope limitations; the policy stays
optional.

**Highest-priority discovery target: checked signed-clause subsumption exposing
tractable cores.** The saved [frontier witnesses](../experiments/results/cnf-activity/frontier-subsumption.json)
remove 217 redundant clauses / 666 literals from 105 of 147 selected open leaves,
using 672,003 subset comparisons. Seven resulting cores are recognized as 2-CNF.
For source 977, binary clauses `(-7,3)` and `(-3,9)` subsume its two remaining
ternary clauses. The pattern crosses previous workload groups, and exposes an
existing tractable family rather than adding another bounded probe rule.

Integrating these exact reductions could complete the current selected plans of
**977, 1044, 1053 and 1365**; sources 907, 1179 and 1363 would still have another
open leaf. These are prospective completions, not executed source gains. Keep
signed subset witnesses tied to retained source clauses and reconstruct exact
child normalization/model lifts, including variables that disappear. Preserve
earlier recognized-family priorities. Compare recognition/checking/acquisition,
all unsuccessful searches, storage and cold replay on all relevant states, not
only the 147 selected frontier leaves. Reuse the existing positive-subsumption
ideas where appropriate, but its restricted solver path is not this signed
inventory reduction. Subsumption itself is established, not a general SAT advance.

Supporting targets follow the measured frontier: 61 inconclusive continuations
(12,984 literals), 39 empty continuations (10,639), 46 clear passes without a batch
(4,264), and one without initial binary candidates (283). Source 1194 costs
1.47590 s discovery; restriction, unit checking and propagation dominate its
separate profile. A larger initial-variable pool alone misses most of this gap.
Share preparation or propagation only when matched total costs justify it.

All **388 tests**, the unchanged Lean audit (**4,126 / 1,968 declarations/theorems**),
three full, three pilot and three prior cold archive checks pass. Both new reports
have 53 matching fingerprints; diagnostics and repeated timing trials retain
input/script hashes. Efficient arbitrary-CNF discovery and global resource bounds
remain open.

## Previous checkpoint: core-only probe choices

The [core-order experiment](../experiments/results/cnf-core-order/README.md)
changes only the continuation ranking, using the existing learned batch and
probe budget. On **1,389 inputs**, non-tiny closure falls **776 -> 775 / 877**:
no source gains, and source **956** is lost. The local hint-study case 97 closes,
but original source 977 remains open. Do not promote the new policy.

Total time falls **120.81853 -> 116.67493 s** (3.43%), discovery **88.69202 ->
85.68326 s**, SQLite **347.566 -> 346.976 MB**, cold replay **50.51029 -> 47.82982 s**,
and six-case Python peak **20.265 -> 19.623 MB**. These are single sequential
samples; the unchanged solver's time varies by 1.13 s between combined modes.
Selected unresolved literal occurrences worsen **26,137 -> 26,734**. No source
coverage improvement or general speedup follows from removing 8,772 ranking
reconstructions. All earlier policies and results remain available.

**Highest-priority discovery target:** use checked delta activity to combine
active original-core candidates with newly ranked candidates, under the existing
continuation budget. At equal CNF/depth, **239** old learned reductions become
clear and **16** old clear states gain a reduction. In **189/239** local losses,
all original core pairs are inactive under the learned batch. At source 956,
core choices `(9,17,18,2)` are all inactive; the old newly ranked variable 14
supplies the useful conflict. Reusing only original choices misses it.

Across all **255 gained/lost local states**, active core variables plus novel
old-ranking variables fit within four choices. Seven other changed shared states
already need five, so this is an observed opportunity, not a uniform bound.
Original clear traces must be checked before delta tests; inactive pairs retain
valid references. Unchanged unit sets cannot produce a new common/equivalence
witness in this procedure. Compare the proposed combined choices first on these
controls, 956 and local 97/original 977, then on full sources. Changed first
conflicts and descendants can still lose coverage. No combined policy or recovery
result has yet been implemented.

Supporting priorities:

1. **Preserve old choices while sharing preparation.** The first-cap batch is
   the prefix of the deterministic sixteen-clause pool for caps at most sixteen.
   Reuse the checked pool and ranking inputs rather than reconstructing them.
   This can isolate savings without changing coverage; no saving is measured yet.
2. **Reuse propagation state where it dominates.** The new frontier has 102 open
   sources and 142 distinct selected leaves (99 learning-clear, 43 clear).
   Source 1194 costs 1.45407 s discovery; restriction, unit checking and propagation
   dominate its separate profile. Probe-kind nodes account for 87.079 MB, but the
   probing field alone is 15.273 MB: whole-node payload is not proof-only storage.
3. **Integrate portable hints only within a justified continuation.** Keep exact
   source/context bindings and delta validation; the earlier extra pass still
   has unfavorable costs. Avoid adding another pass to repair a ranking miss.

All **380 Python tests**, the unchanged Lean build/axiom audit (**4,126 / 1,968**
declarations/theorems), three full, three pilot and four previous cold archive
checks pass. Both new reports have 50 matching fingerprints. The implementation
and preserved measurements are pushed in **544054d**. Global efficient arbitrary-
CNF discovery, compact closure and acquisition/storage bounds remain open.

## Previous checkpoint: portable proofs and the ranking hypothesis

**Previous proposed experiment (now tested above):** rank continuation variables on the original core,
using the existing learned batch and existing number of passes. The
[portable-hint control](../experiments/results/cnf-hint-transport/README.md)
isolates a local miss caused by ranking: both the transported and rediscovered
batches close local case **97** with core choices `(4,5,7,19)`, and both stay open
with baseline-continuation choices `(4,5,7,11)`. Test this case and original source
**977**, then the old **956/1024/1189** controls and full old/fresh source workloads.
Derive choices from the exact core or checked complete original traces, never an
unchecked stored list. Charge ranking, later graph changes and any losses. Do
not add another probe pass or promote the optional hint overlay.

The transport primitive now works on **1,005 eligible hint occurrences** from
**494 learned-parent edges** (449 prior and 45 fresh): every translated reason
prefix yields an independently checked child-core proof without fresh search.
There are **984** distinct core/clause records. Replay needs no parent graph;
the exact core and hint context still bind proof use and heuristic plans. This
implements portable evidence, not complete cross-generation planner integration.

The local hint overlay closes **224/494** children versus **223/494**, with no
losses. Its one gain is an **unselected alternative of source 977**, and is absent
from every saved selected source path. Do not add it to the previous **719/805**
original-source coverage. The controlled two-by-two comparison shows that the
gain needs different probe choices, not a stronger inherited batch.

The extra-pass policy costs **16.82765 versus 14.41354 s**, plus **0.95129 s** for
transport preparation. SQLite grows **55.120 -> 63.885 MB**, cold replay
**4.70738 -> 7.72522 s**, and six-core Python peak **7.372 -> 7.431 MB**. Ordinary
nodes fall 2,167 -> 1,999, but proof and context payloads add **2.181 + 3.097 MB**;
logical probes rise **14,468 -> 16,136**. The favorable reason-prefix scan count
(11,510 versus 287,160 fresh-search literal visits) is not an end-to-end speedup.
Fresh proof search is conditional on supplied candidate clauses; all parent
checking, preparation, storage and replay remain charged.

Prior priorities before the core-order test:

1. **Core-ranked continuation under the existing budget.** Isolate the measured
   variable-choice cause, avoiding reconstruction of a redundant learned view
   solely for ranking. Whole-source coverage and cost decide whether to adopt it.
2. **Integrate portable evidence into an existing pass.** The saved diagnostic
   finds 1,456 inactive and 102 active hint deltas at 196 original-probe cores.
   Reuse only after original closure validation and an inactive-delta check;
   these are opportunities, not saved probes. Avoid repeating a fresh pass that
   then falls back to another full discovery pass.
3. **Reduce proof/context duplication if integration earns its cost.** Full-core
   hint keys, per-hint normalization and separately replayed plan contexts now
   outweigh ordinary-node savings. Context omission is not a valid compression.

All **374 Python tests**, the full Lean build/axiom audit (**4,126 declarations /
1,968 theorem declarations**) and four new cold archive replays pass. All 51
fingerprints match; previous archives are preserved. These are sequential
synthetic local controls, not unrestricted-SAT bounds or an industrial speedup.

The preceding parent-scoped core study follows with its whole-source denominators.

The full **1,317-input** core experiment gives **719/805** non-tiny closures
versus **718/805** for baseline and fixed order, with no losses against either.
All close **14/24** fresh random cases; **86** core sources remain unresolved.
Total time is **94.870 / 97.402 / 97.835 s**, SQLite **284.111 / 284.299 / 284.094 MB**,
and cold replay **40.281 / 41.160 / 40.384 s** for baseline/fixed/core. Core is
3.13% slower than baseline in this single sample. Six-case Python peak rises
**20.022 / 20.127 / 20.265 MB**, excluding native memory/RSS and full-corpus peak.
The selected pilot's savings do not generalize; keep this policy optional.

At the saved 956 parent, all policies force only `14=false`. Removing the
redundant additions yields its **54-clause original restriction**, which closes.
This controlled core is shared exactly in a regression test. Within the full
core archive, however, **no two learned parents share a child core**. The measured
gain comes from altered descendant discovery, not demonstrated large core merging.
There are 449 successful learned edges, 385 with changed normalized child syntax.
All parent hints and proofs remain persistent; children receive no inherited hints.
The 907 absent eligible transported hint occurrences include the 319 immediately
reacquired clauses above, not 319 distinct implications or measured saved seconds.

Prior targets, now partly tested by the portable-hint experiment:

1. **Transport checked hints without changing core recognition.** Test the measured
   reacquisition opportunities and coverage controls before full old/fresh inputs.
   Charge proof/context storage, transport, checking and cold replay. Larger
   learning batches alone are not the experiment. Cached implication proofs do
   not automatically remove probes required by the current ranking policy.
2. **Reuse checked propagation state to expose additional structure.** The new
   largest unresolved source is **1297**, a fresh 48-variable CNF: **1.47150 s**
   discovery and 456 unresolved literals. Restriction, unit checking/propagation
   and literal helpers dominate its separate profile. Only one successful learned
   parent occurs there, so hint transport alone will not remove its main cost.
3. **Share proof payloads where the measurements justify it.** Probe records are
   **72.386 MB / 63.76%** of core logical node bytes. Source bindings, checking and
   cold replay must survive any compression. Neither physical database pages nor
   a successful selected pilot measures broad semantic-core compression.

The selected frontier contains **124** unresolved leaves, 86 learning-clear and
38 clear. All **366 Python tests**, the full Lean build/axiom audit (**4,125
declarations / 1,967 theorem declarations**) and four full, four pilot and four
preceding archive replays pass. Both reports' 47 fingerprints match. Primary and
diagnostic timings ran sequentially without concurrent tests, builds or commits.
Core construction adds work; no efficient arbitrary-SAT coverage or uniform
storage bound has been obtained.

The preceding fixed-order investigation follows with its own corpus and timings.

The [fixed-order experiment](../experiments/results/cnf-learning-fixed-order/README.md)
implements the previous target and explains why it is insufficient. All 1,281
inputs give the same **692/769** non-tiny and **18/24** fresh random closures under
baseline, selection and fixed order. Both selected modes gain 1024 and lose 956;
fixed order changes no source closure relative to selection. Seventy-seven
sources remain unresolved. Total time is **77.916 / 82.421 / 80.720 s** and SQLite
**252.244 / 252.498 / 252.391 MB** for baseline/selection/fixed. Fixed remains
3.60% slower than baseline in this single sample; no general timing advantage
over selection follows from its 2.06% lower sample time.

At source **956**'s saved 18-variable parent, baseline and fixed order both force
only `14=false`. Their restricted original CNF is **the identical 54-clause core**.
Baseline retains three extra learned clauses and its 17-variable, 57-clause child
closes. Fixed retains four and its 17-variable, 58-clause child stays open with
eighteen unresolved literals. All additions are entailed, so the two child
relations agree. Recognition, ranking and full persistent keys nevertheless see
different representations. The [checked controls](../experiments/results/cnf-learning-fixed-order/mechanisms.json)
retain the exact clauses and acquired child paths. This is a concrete opportunity
for certificate-backed core sharing, not cheap general semantic canonicalization.

Fixed order adds **6,418 ranking reconstructions** across acquisition/checking.
Nodes rise **16,052 -> 16,126**, logical probes **89,782 -> 90,713**, logical node
bytes **100.113 -> 100.315 MB**, cold replay **33.506 -> 34.309 s** and the same
six-case Python peak **20.022 -> 20.127 MB** versus baseline. Selected unresolved
literals fall **18,362 -> 17,971** without greater source coverage. The current
frontier has **111** distinct leaves, 71 learning-clear and forty clear. Source
**1194** remains the largest discovery case (1.417 s), dominated by restriction
and unit checking/propagation. Sharing proof records and avoiding repeated scans
remain supporting targets, after the representation-sensitive discovery experiment.

All **358 Python tests**, the unchanged Lean build/axiom audit (**4,122 declarations /
1,965 theorem declarations**) and four full, four pilot and three preceding archive
replays pass. Both reports' 43 fingerprints match. Measurements ran sequentially
without concurrent tests, builds or commits. Restricted exactness, incomplete
structural coverage and the open arbitrary-SAT construction bound remain distinct.

The preceding selection investigation follows; its smaller corpus has its own
denominators and timing samples.

The [bounded-selection experiment](../experiments/results/cnf-learning-selection/README.md)
implements the previous target: choose four clauses from at most sixteen proved
candidates by saved-closure activation and origin diversity. The thirteen-source
pilot gains source 1024; the complete 1,245-input comparison also loses source
956. Non-tiny closure stays **662/733**, fresh random closure **16/24**, with **71
source misses**. Total time rises **71.417 -> 73.194 s (+2.49%)**, SQLite
**227.385 -> 227.832 MB**, cold replay **29.815 -> 30.359 s**, and the same six-case
Python peak **20.022 -> 20.121 MB**. These are single sequential samples, without
concurrent tests, builds or commits during measurements. Keep the policy optional.

The saved [path controls](../experiments/results/cnf-learning-selection/selection-paths.json)
explain the key gap. At 1024, both batches use the same four choices and activate
the same single saved closure; only the new clauses refute its assumption. At
956, neither batch activates any original closure. The old choices first force
variable 14, the new choices variable 16, under either batch. All four local
controls report a reduction, but the actual new source plan later stays open.
Therefore activation counts, origin diversity and a coarse reduction label
miss consequential interactions. Track the first conflict and the resulting
child structure. The locally improved common reduction on 1189 still does not
close that source; preserve it as a negative control.

The [complete diagnostic](../experiments/results/cnf-learning-selection/mechanisms.json)
retains all 606 changed selection parents, including 126 reorder-only cases,
their four checked local controls, and the previous 94 selected unresolved leaves.
Local counterfactuals are not whole-source coverage. Selected unresolved literals
fall **17,687 -> 17,327**, yet nodes rise **14,592 -> 14,653** and logical probes
**82,036 -> 82,782**. Of the current 103 selected leaves, 66 remain learning-clear
and 37 clear. The largest discovery case remains **1194** (1.464 s); restriction,
unit checking/propagation and literal helpers dominate its separate profile.
Avoiding repeated scans and sharing probe records remain supporting cost targets.

All **353 Python tests**, the full Lean build/axiom audit (**4,122 declarations /
1,965 theorem declarations**), and three full, three pilot and four preceding
archive replays pass. The subset theorem preserves source models independently
of selection quality. The capped candidate filter can miss useful alternatives;
there is no complete efficient arbitrary-SAT construction or compactness result.

The preceding studies follow in reverse order. Their denominators and timings
belong to their own matched corpora and must not be compared as a single fixed
workload.

The [closure-reuse comparison](../experiments/results/cnf-probe-closure-compact/README.md)
retains all 1,209 sources and all 13,066 semantic nodes, including alternatives.
Coverage stays **634/697 non-tiny inputs**, **15/24 fresh random inputs**; 63
sources remain unresolved. Checked references avoid 14,705 of 17,548 continuation
propagations; 672 active repeated assumptions and 2,171 fresh ones still propagate.
The compact sample changes total time **62.759 -> 61.687 s**, SQLite **197.104 ->
196.096 MB**, cold replay **26.785 -> 25.094 s**, and the same six-case Python peak
**20.378 -> 20.022 MB**. These are small single-sample effects; a checkpoint commit
overlapped part of compact acquisition, so retain the timing limitation.

The [first representation](../experiments/results/cnf-probe-closure-reuse/README.md)
saves 807,098 local proof bytes but grows SQLite to 200.323 MB because an added
policy field is repeated in full keys. It remains preserved. Replacing the
local-learning version tag keeps a distinct namespace and removes that overhead.
The current compact logical node total is 78.533 MB; probe nodes still occupy
49.281 MB. Source 1194 is the largest remaining discovery case, with restriction,
unit checking/propagation and literal helpers dominating the separate profile.
The fixed-point/derivation lemmas pass Lean's full audit (4,121 declarations /
1,964 theorem declarations); all 348 Python tests and complete new/old archive
checks pass. No Python/SQLite refinement or unrestricted resource bound follows.

The [bounded-learning study](../experiments/results/cnf-probe-learning/README.md)
implements the preceding implication target. On 1,173 inputs, non-tiny closure
rises 604/661 -> 607/661, including a fresh 48-variable UNSAT source (18/24 ->
19/24 fresh closure). There are no observed lost closures. However, total time
rises 48.177 -> 52.697 s, SQLite 163.533 -> 168.268 MB, cold checking 20.785 ->
22.013 s and the targeted Python peak 18.466 -> 20.378 MB. Keep it optional.
The extra pass is charged; total probe budgets are not equal.

The attribution diagnostic matters: fixed continuation choices without added
clauses still reduce 49 of 229 successful learning nodes, including both old
source gains (956/1057). The selected node at fresh gain 1155 stays inconclusive
without additions. Thus stronger propagation and changed choices both matter;
local counterfactuals do not prove whole-source coverage or free recognition.
All 1,709 failed learning attempts remain archived. Logical node bytes grow
63.466 -> 66.573 MB despite four fewer nodes; batch/continuation JSON alone is
1.946 MB. Selected unresolved literals fall 12,686 -> 11,106. Support reduction
or fewer nodes alone is insufficient for low total acquisition cost.

The largest remaining discovery case is now **1063**, at 1.208 s main discovery.
Restriction, unit checks/propagation and literal helpers dominate a separate
profile. Probe nodes occupy **41.132 / 66.573 MB** logical payload. Reusing checked
closures and sharing their proof records targets these measured costs while
retaining the useful learned propagation. The follow-up above measures that opportunity without adding coverage. Fifty-four source cases remain structurally
unresolved; efficient arbitrary-CNF construction and compact coverage are open.

The [signed-equivalence study](../experiments/results/cnf-probe-equivalence/README.md)
implements the preceding target. Seven of sixteen selected source misses close
in the pilot, with slightly lower time and storage. On the full 1,137-input
comparison, closure rises 567/625 -> 574/625 non-tiny sources, but fresh random
closure stays 18/24. Time rises 38.293 -> 39.731 s, SQLite 130.597 -> 135.569 MB,
and cold checking 15.208 -> 15.856 s. Keep the policy optional. All seven gains
are old cases and three are variants of one input. The prior common policy and
all unsuccessful traces remain preserved.

The full run acquires 624 equivalence rewrites merging 1,145 variables across
nodes; 431 shared exact parents retain identical probe lists. Still, probes rise
37,049 -> 41,039, pattern nodes 9,584 -> 9,952 and logical bytes 50.062 -> 52.575
MB. Selected unresolved literals fall 10,300 -> 9,674. The six-case traced Python
peak falls 14.564 -> 11.586 MB, but this excludes native memory and full-corpus
peak. Local compactness, targeted live allocation and total durable storage must
remain separate accounts.

Probe nodes occupy **32.136 / 52.575 MB** logical payload. The remaining 48-variable
case 1061 again spends most profiled own time in restriction, unit checks/propagation,
normalization and literal helpers. Occurrence-driven scans and shared checked
rewrite chains remain supporting work. The new implication opportunity extends
beyond equivalence blocks, but neither its counts nor the successful reductions
provide efficient closure of arbitrary SAT.

The [common-consequence comparison](../experiments/results/cnf-common-consequence/README.md)
implements the previous target, with a narrow gain and a total-cost regression.
On 1,101 inputs it closes 537/589 non-tiny cases versus 536/589; fresh random
closure remains 40/64. Time rises 32.122 -> 32.759 s, SQLite 104.436 -> 107.758 MB
and cold checking 12.033 -> 12.563 s. Keep it optional. Although arbitrary
conditioning candidates and selected unresolved literals fall, probes rise
29,280 -> 31,745. Common facts require no new probe at the same node, but their
reduced children trigger new work. Do not equate smaller residuals with lower
total acquisition or promote all archived opportunities to claimed root gains.

Probe nodes now dominate logical storage (23.647 of 40.749 MB), and the largest
remaining 48-variable discovery case again spends most profiled own time in
restriction, unit checks/propagation, normalization and literal-processing
helpers. Occurrence-driven scans and shared rewrite chains remain supporting
cost work. The selected equivalence opportunity will not explain all larger
3-CNF misses; preserve those cases as a separate unresolved group.

The [failed-literal comparison](../experiments/results/cnf-failed-literal/README.md)
implements the preceding target. On 1,025 matched inputs, closure rises from
358/513 to 484/513 non-tiny cases and from 19/64 to 51/64 fresh random cases.
Time falls 27.111 -> 18.878 s, SQLite 93.143 -> 65.057 MB, and cold checking
10.079 -> 6.412 s. Twenty-nine cases remain open. Probing every binary variable
on these misses closes only two more, while inventory time rises 6.817 ->
11.495 s. Do not respond by raising the global cap unconditionally.

Probe nodes now dominate logical payload: 12.545 of 22.743 MB. The largest
remaining discovery case spends most profiled own time in restriction scans,
unit propagation/checks, normalization and their literal helpers. Reusing
existing implications is the primary discovery target; sharing forced chains
and avoiding repeated scans are supporting cost targets. No complete efficient
arbitrary-CNF partition or bounded total acquisition follows.

The [fused-edge comparison](../experiments/results/cnf-fused-conditioning/README.md)
implements the previous intermediate-state target. All 3,999 archived OR plans
across three policy pairs retain their choices and final child relations. On
shortest-clause ordering, nodes fall from 11,224 to 6,281, SQLite from 96.911 to
65.573 MB and total time from 21.170 to 17.638 s, with unchanged 330/437 coverage.
Frequency and combined unit/pure processing also improve. Targeted six-case
traced Python peaks fall, while the earlier easy-case diagnostic slightly grows;
all scope limits and the in-memory pilot runtime regression are retained.

The remaining shortest-clause node payload is mainly unresolved CNFs (12.124 MB)
and OR nodes (11.510 MB), rather than discarded simplification intermediates.
All 107 non-tiny misses remain, including the fresh 20/32-variable 3-CNFs. This
now favors stronger checked discovery over another unconditional representation
change. Repeated recognition still increases with fused incoming edges and is
supporting work if it dominates the next probe profile.

The optional balanced-short-clause policy improves cap-four unit-only coverage
from 322/437 to 330/437 but raises total time from 17.203 to 20.246 s and SQLite
from 79.118 to 96.911 MB. It tries fewer candidates yet acquires more nodes:
9,162 -> 11,224, with repeated child references falling from 3,344 to 2,469.
Simplification nodes account for about 91% of increased logical node payload.
This identifies a representation/reuse gap, not a reason to enable the heuristic
by default. Relative to combined unit/pure processing it gains six cases and
loses five. Keep both comparators. The rule is an established-heuristic variant,
not a new family certificate or an efficient unrestricted classification.

The frozen-policy holdout gain is only two of 72 fresh formulae. All 32 new
3-CNFs on 20/32 variables remain open under every measured policy, including
eight frequency candidates. A cheaper checked closure could support budgeted
lookahead that investigates these interactions. More candidates alone raises
total time to 42.110 s for 332/437 closure; this is not the preferred next step.

Checked unit/pure simplification now closes all 36 old misses and exposes the
matching/parity core without conditioning. At depth two, total non-tiny coverage
rises from 217/329 to 290/329; total analysis plus solving falls from 8.097 to
7.154 s and SQLite from 39.727 to 31.732 MB. Units alone reach 289/329 in 6.604 s:
keep that faster comparator rather than enabling both reductions unconditionally.
Pure-only and depth-zero regressions are retained. These are standard reductions
in an analysis layer; the separate decision solver already has unit propagation.

Supporting opportunities remain checked decision integration (the largest single
operation still solves an original affine source), native affine boundary rows
(one renamed cap miss), and avoiding repeated scans/unused parent profiles on
long unit/pure chains. Prioritize these when they enable discovery; arbitrary
SAT still has no proved small decomposition or uniformly polynomial acquisition.

The [projection study](../experiments/results/cnf-affine-projection/README.md)
implements exact affine projection with a bounded CNF encoding and checked model
lifting. It closes all six growing coupled controls at depth zero, including
128 equations/258 variables projecting to two variables and one clause. On 775
inputs, depth-two analysis plus solving falls from 4.471 to 3.750 s and SQLite
from 22.913 to 19.030 MB. That checkpoint adds no depth-two closures on the original
664 inputs; its 36 misses were later addressed by simplification. The small memory diagnostic grows, and mixed-case
overhead and encoding-budget failures are retained. Three new Lean theorems
establish semantic composition with invariant leftovers, not Python refinement.

The largest remaining measured cost on the 258-variable coupled control is now
ordinary solving of the original source: 565 of 579 ms, versus 13 ms discovery.
Using checked projected decisions could avoid this duplication; it is supporting
integration work alongside the primary discovery target. Native affine boundary
rows would avoid exponential CNF re-encoding. Neither improvement is implemented.

The [affine extraction study](../experiments/results/cnf-affine-patterns/README.md)
implements the previous support/sign-pattern target. Exact extraction plus checked
elimination closes 14 of the previous 50 unresolved inputs, leaving 34 seeded
CNFs and the coupled matching/parity pair. The eight seeded gains use small
unit/binary contradictions after conditioning, not large hidden XORs. On 733
sources, depth-two analysis plus solving falls from 3.305 to 2.901 s and SQLite
from 14.324 to 13.386 MB; on the original 664, time is almost unchanged (1.847
versus 1.841 s). Pure affine controls improve, while coupled controls retain
extra recognition cost without closure. Depth-zero storage increases. This is
still an additive analysis layer, not a faster general SAT solver.

The preserved [first inventory](../experiments/results/cnf-pattern-inventory/README.md)
is implemented: seven recognition outcomes retain overlaps in 24 observed root
cells. Beyond 512 exhaustive tiny sources, whole-formula tests explain 39/152
inputs, components 45/152, one conditioning level 57/152 and two levels 102/152.
The last mode leaves 42 seeded CNFs plus four structural cases and their variants
unresolved. Full analysis plus solving takes 2.021 s versus 0.301 s for solving
alone, and SQLite grows from 0.385 to 6.459 MB. It is an analysis tool, not a
speedup. The persistent result includes all failed alternatives and cold checks.

The propagation profile remains useful evidence: a pinned 2,048-variable chain
spends 2.67 s in preparation, with about 98% of instrumented time in repeated
propagation scans. The queue improvement is now supporting work, prioritized
when it enables discovery experiments or exposes new structural reuse.

Bounded equivalence retry is implemented as an optional layer. At 1,024
variables, total time falls from 0.78490 to 0.05932 s; at 4,096, from 11.88170
to 0.27261 s. The matched raised-global-budget comparator is slightly faster
on these chains and also solves dense controls that the targeted policy rejects.
There is no evidence that targeted escalation has lower expected total cost.
For supporting optimization work, investigate inert-posting compression/cost
estimation on the dense 1,024-variable miss (0.893 s versus 0.117 s with a larger global
budget). Parity remains the next repeated structural miss (32 fallbacks /
0.175 s / 326 KB). Successful matching preparation remains another profile target.

Matching repair is implemented. It removes all 80 old matching misses and keeps
the equivalence gains. The larger 32-block, 8-choice case falls from 8.303 s /
20.33 MB to 0.253 s / 0.424 MB. Mixed-base extraction and searching around
non-unit coupling conflicts remain important cross-category gaps, but their
current controls are small; scale/profile them before ranking their total saving.

## Current cost map

These matched synthetic measurements do not establish a globally dominant cost
across a representative SAT workload distribution. They inform the discovery
priorities without replacing the coverage objective.

The arbitrary-CNF history/residual code is an experimental Python path. The
production restricted-family engines and Lean semantic results are separate;
their capabilities are not already integrated into one verified general solver.

| Workload regime | Current costly work and evidence | Most promising investigation |
| --- | --- | --- |
| A local change needs several variables to move together | Equivalence blocks and matching paths now repair successfully. The 32-block, 8-choice matching case falls from 8.303 s / 20.33 MB / 33 bases to 0.253 s / 0.424 MB / one base. The original 40 parity misses remain. | Parity-preserving directions; component-local discovery and proposal search guided by coupling conflicts. |
| Unit implications activate in an unfavorable scan order | The pinned 2,048-variable chain takes 2.67 s to prepare. About 98% of a separate instrumented preparation is in propagation; 16.78 million charged literal visits for 8,189 source occurrences. | Supporting optimization: queue newly forced values and update affected occurrences; preserve independently checked reason traces. |
| Recognized equivalence repairs succeed | Optional bounded retry reduces the 4,096-variable chain from 11.882 to 0.273 s, including 0.217 s preparation. Every moved member/posting is still visited. | Shared group assignments/certificates and affected interfaces, with cold reconstruction and count invariants maintained. |
| A recognized move exceeds the fixed budget | Retry removes the ordinary-chain miss. Dense 1,024-variable control still takes 0.893 s with fallback, versus 0.117 s at global budget 32,768. A contradictory block incurs 40.36 rather than 31.01 ms expansion. | Compress inert postings and improve cost estimates; retain both extra-work losses and missed savings. No optimal budget policy established. |
| Matching moves succeed | At 32 blocks of 8 choices, initial preparation is 206.58 of 253.08 ms. A warm move changes four indicators, visits 32 postings per pass and allocates 439 trie nodes. Cold final replay is slightly slower. | Profile base preparation and cold checking; do not optimize two-edge path search while initialization dominates. |
| A small update defeats pure model reuse | New affected-clause repair removes all 32 original-control fallbacks. On matching size 16 / 128 protected flips it reduces operation time from 3.478 s to 0.147 s and logical payload from 12.46 MB to 0.158 MB. | Keep these gains while avoiding unnecessary index preparation; shared source/dependencies remain needed on genuine fallback. |
| A general residual escapes tractable recognizers | Branching creates distinct residuals; each is normalized, checked and persisted. There is no polynomial bound on their number. Existing matching recognition reduced one restricted example from 5,191 residuals to one. | Expose tractable components and small interfaces before branching; preserve useful state when a component changes class. |
| Reuse succeeds and the logical update is cheap | In the new 128-addition UNSAT diagnostic, SQLite execution and transaction-context exit account for about 87% of exclusive profiled time. | Reduce redundant archive work while preserving durability and version identities. |
| Sparse, very long variable identifiers | Near 2^1024, 32 updates retain 32,801 trie nodes. `map_get`/`map_set` account for about 62% of exclusive time in the new diagnostic. | Compress unary paths; compare exact-key representation and cold reconstruction costs. |
| The old assignment already satisfies every addition | Affected-clause indexing raises peak traced Python allocations from 249,217 to 473,849 bytes versus pure repair on the matched compatible stream. | Lazy or workload-selected index preparation, with activation cost charged. |
| One change affects many clauses | At 4,096 affected clauses, avoiding a new base still increases operation time from 109.99 to 125.48 ms; index preparation takes 103.32 ms. | Budget index activation and maintenance by anticipated reuse, not merely by avoided solver calls. |
| Restart, export or repeated events dominate | Cold repair replay can cost more than an isolated final base. Repeating a unit 128 times retains 10,719 logical bytes versus 1,393 for full-source semantic deduplication. | Separate shared semantic state from exact event provenance; measure cold validation and output costs explicitly. |

Evidence: [matched repair comparison](../experiments/results/cnf-repair-history/README.md),
[affected-clause comparison](../experiments/results/cnf-affected-history/README.md),
[joint equivalence comparison](../experiments/results/cnf-equivalence-history/README.md),
[retained matching comparison](../experiments/results/cnf-matching-history/README.md),
[bounded budget comparison and preparation profile](../experiments/results/cnf-budgeted-history/README.md),
[coordinated-change diagnostic](../experiments/results/structured-repair-gaps/README.md),
[new diagnostic profiles](evidence/2026-11-08/reuse-cost-profile/README.md),
[general-CNF investigation](arbitrary-sat-expansion.md). Times are individual
samples, not significance estimates. Profile percentages describe instrumented
diagnostics only. SQL execution is not a measurement of disk I/O alone.

The previous large gain came from eliminating repeated acquisition, not just
speeding up an already cheap append. On size-16 matching SAT plus 128 fresh units,
repair reduced 129 bases to one, operation time from 2.619 s to 0.073 s and
logical archive payload from 12,020,154 to 100,706 bytes. That opportunity is
already implemented for pure repairs. Its speedup must not be counted again as
evidence that the next optimization will produce the same gain.

## How each hourly run chooses work

1. Read the discovery plan and select one gap that can expand certified pattern
   coverage or explain a substantial unresolved cell. Use current cost evidence
   to judge whether the discovery is useful, not as the sole selection criterion.
2. Make the classifier, overlap policy, recognition certificate and exact
   decomposition/recomposition rule explicit. A failed recognizer is not proof
   of nonmembership or UNSAT. Track unresolved cases rather than dropping them.
3. Compare on matched unlabelled inputs, exhaustive small cases and adversarial
   mixtures/edits. Charge discovery, verification, state size, persistence and
   cold replay. Preserve failures and counterexamples.
4. Implement or prove one concrete improvement, persist its scope and costs,
   update the unresolved-cell priorities and commit/push verified checkpoints.
   Known-family optimization is secondary unless it enables this experiment.

Do not turn this into repeated status analysis. Keep complete coverage, exact
recomposition, compactness and efficient discovery as separate obligations.

## Ranked gaps across SAT categories

### 1. Discover categories and characterize unresolved interaction

The initial [audited pattern inventory](sat-pattern-discovery.md) is complete
for the stated bounded policy. Next, split its unresolved cells with useful
structural invariants. Forty-eight remaining inputs exclude every tested pattern;
two exceed the parity cap while failing the other tests. None of those outcomes
proves hardness or excludes semantic equivalence to a broader tractable class.
The current controlled misses include complete exclusion cubes, coupled matching
and parity, and an activated guarded CNF. Exact support/sign-pattern discovery
is the next concrete probe; random-CNF coverage must be reported alongside the
structured controls. Preserve separate construction and composition obligations.

### Supporting optimization: avoid repeated propagation scans

Occurrence-driven propagation remains a measured opportunity: 2.67 s preparation
on the pinned 2,048-variable chain, with about 98% of a separate profiled run in
propagation. Queue newly forced values and update affected occurrences, retaining
independently checked reason traces. Charge construction, queue memory and cold
replay. Schedule this when it supports discovery, rather than automatically
placing it ahead of the user's research objective.

### 2. Reuse coordinated structural changes

The preceding one-variable repair was too narrow even on easy subclasses. The
[diagnostic](../experiments/results/structured-repair-gaps/README.md) supplies and
independently validates a coordinated change at every rejected step:

| Structure | Preserved internal invariant | Appropriate change |
| --- | --- | --- |
| Literal-equivalence block | All equalities, including signed variants | Implemented for complementary binary pairs in a base; change all dependent variables and independently check the final state. |
| Affine equations A x = b over GF(2) | A(x + z) = b when A z = 0 | Apply a nullspace direction, potentially changing many variables. |
| Matching component | Choice coverage and resource exclusivity | Implemented for strict whole matching bases; retain endpoints and unit pins, search an alternating path, then check all affected clauses. |
| Horn component | Consequences of the retained facts/rules | Propagate a changed requirement with retained reasons; check negative constraints and couplings. |

Equivalence and matching now have measured implementations; parity and Horn
maintenance remain proposals. The joint comparison automatically discovers the
equivalence blocks, charges their recognition and preserves all old constraints.
On 32 blocks of 32 variables it reduces operation time from 2.4689 to 0.06676 s,
logical storage from 3,792,631 to 98,663 bytes, and peak traced Python allocations
from 45,575,163 to 1,925,402 bytes. Cold final query grows from 40.88 to 44.42 ms.
Repeating the last known update from its parent after restart takes 88.32 versus
45.98 ms; these archives already contain that result. That checkpoint's matching
control still retained 33 bases / 2,267,324 bytes; the following matching-state
implementation removes those fallbacks.

The generic joint record contains a changed-variable list, not trusted structural
claims. The matching adapter now supplies automatically discovered moves to it;
nullspace discovery remains open. Initial binary-pair discovery is cached
per base and invoked only after scalar failure; additions do not enlarge the
discovered blocks. Nonpaired implication cycles, new equalities and blocks beyond
the optional retry's size/density/identifier limits remain failures. A corrected signed benchmark forces 32 actual
repairs; the initial already-compatible signed control remains archived.

**Implementation obligations:** aggregate all true-literal count changes before
checking the final assignment. Intermediate one-variable states may violate
clauses, so repeated calls to the existing operation cannot implement a joint
repair. For a certified internal component E and remaining constraints G, a move
that preserves E still needs to preserve affected clauses of G and satisfy the
new addition. Earlier deltas belong to this check. A derived equivalence alone
does not certify preservation of every source clause using those variables.

Skipping internal clause checks also does not maintain their existing count-map
entries. Update them, or retain a typed component state with explicit invalidation
and charged reconstruction when a different engine needs those counts. Group
assignment representations can avoid rewriting every dependent variable, while
full witness export remains output-sized. Bounds must charge moved variables,
affected interfaces, discovery and maintenance, not only the number of groups.

**Completed acceptance checks:** 23 matched cases, 46 new archives, 255 Python
tests and the Lean axiom audit pass. The new archives' 1,144 versions and 869
residuals cold-check without changed bytes; 82 prior archives also replay
unchanged. Couplings, signed equalities, contradictions, repeated changes,
exact count recomputation and forged records are checked. Lean proves the
semantic final-state protection rule, not the Python count/index implementation.

**Completed matching checkpoint:** 37 matched cases retain 74 new archives,
1,414 versions and 608 residuals, all cold-checked without byte changes; 58 prior
archives also replay unchanged. All 261 tests pass. At 32 four-choice blocks,
operation time falls from 0.92416 to 0.04882 s, logical storage from 2,267,324 to
50,257 bytes, and peak traced Python allocation from 24,840,875 to 1,192,534 bytes.
The code retains choice/resource/unit-pin tries and updates only changed paths.
Cold final replay increases from 17.93 to 20.25 ms. No new Lean graph refinement
is claimed: matching moves use the existing joint semantic protection theorem.

**Remaining matching gaps:** one chosen path per literal can fail a non-unit
coupling although a longer valid path exists. Whole-base recognition misses a
matching component beside an unrelated equivalence component. Spare resources
permit valid models with extra true choice indicators, outside the retained
exact matching view. These controls all remain SAT but need fallback. Unit
constraints guide search, whereas arbitrary coupling clauses only enter final
checking. Recognizing subcomponents and using failed checks to guide a bounded
alternative-path search are promising, with their own discovery/maintenance cost.
Old versions and sources must remain available through every class transition.

Retaining a known matching and using alternating paths under edge deletions is
established in [Régin (1994), pp. 364–366](https://cdn.aaai.org/AAAI/1994/AAAI94-055.pdf).
The implemented contribution is a checked persistent integration with explicit
full-source accounting, not a new matching algorithm or a general CNF guarantee.

### Completed baseline: single-variable affected-clause repair

This is the broadest concrete implemented improvement: assignment validity is independent
of whether the model came from Horn solving, 2-SAT, matching, affine elimination
or general search. The preceding pure-repair interface only accepts a changed
literal whose opposite is absent from the whole parent source. The new
`AffectedRepairHistory` checks affected-clause counts and retains the older path
as a comparator; it is not automatically selected by the production solver.

For example, with `F = (y) AND (NOT x OR y)`, assignment `x=false, y=true`
satisfies F. Appending `(x)` can safely flip x; purity rejects it because `NOT x`
occurs in F. The retained control repeats this pattern 32 times. The new
interface now accepts all of these changes without new acquisition.

A stronger sufficient condition is to maintain each old clause's number of true
**distinct signed literals**. If a currently false literal l is set true, then

```
new_count(C) = old_count(C) - [opposite(l) in C] + [l in C].
```

Accept only if all affected old clauses still have a positive count and the new
clause is satisfied. Clauses containing neither sign are unchanged. The formula
also handles tautologies containing both signs; duplicate literal occurrences
must not inflate the counts. Exact signed occurrence lists and counts must refer
to the current version, including all earlier deltas and older branches.

For one candidate x, this requires O(|D| + occ(x)) logical literal/clause visits
with suitable indexes, plus persistent index, arithmetic, certificate and storage
costs. The affected set can include the entire formula. Trying many candidates
must be budgeted. Independently safe flips cannot be composed using stale counts;
joint repairs require joint changes to the counts and a new check. Failure to
find a bounded repair supplies no UNSAT verdict.

**Completed checks:** 35 matched cases include growing protected histories,
occurrence degree, contradictions, duplicate literals, tautologies, compatible
updates, sparse IDs and coordinated changes. That checkpoint passed 249 tests; old versions
and cold verification are preserved. Lean proves the semantic protection rule,
not the count-map implementation. The 512-flip control falls from 5.059 s to
0.327 s and 8,921,728 to 83,082 logical bytes. The size-16 matching control reduces
peak traced Python allocation from 86,261,287 to 2,837,728 bytes. Cold replay and
index preparation become more expensive; see the retained losses above.
Single-variable
local search is classical; the research question here is checked persistent reuse
and its full cost, not novelty of flipping a Boolean variable.

### 3. Retain propagation and class-specific intermediate state

The residual prototype caches exact normalized residual results, but rebuilds
many intermediate structures. A failed fast path can therefore discard useful
work even when most of the source is unchanged.

In particular, `_visit` stores a successful residual as its CNF and a flat model;
it does not retain the matching, implication graph or other producer state.
`PositiveHistory.prepare` stores the full source on a new base. These two choices
explain why solver-result caching does not yet provide persistent component-state
reuse. A component witness forest and immutable source references would also
avoid repeatedly flattening/copying unaffected models, with reconstruction and
variable mappings charged when a full witness is requested.

SAT categories overlap. An equivalence chain is simultaneously Horn, dual-Horn,
2-CNF and affine. Retain several checked views of one shared source component
instead of making its identity depend on a single class label. Common objects
should expose source/dependency references, assumptions, interface variables,
verdict/witness or refutation, and an explicitly exact or one-sided summary.

| Category | State worth retaining | Recognition, maintenance and limitation |
| --- | --- | --- |
| Horn / dual-Horn | Derived literals, dependency reasons and a propagation queue. | Replace repeated full propagation scans with affected work. Distinguish proved consequences from arbitrary choices in a model. Additions preserve old consequences; deletion requires dependency retraction. A new implication can still force a global cascade. |
| 2-CNF | Implication edges, SCC/condensation information and contradiction paths. | Check that new clauses remain binary or isolate the nonbinary interaction. An edge can merge many SCCs; arbitrary constant update time does not follow. |
| Matching / reducible positive cores | Matching, choice/resource graph, reduction witnesses and Hall certificates. | The new adapter retains the graph and selected endpoints for strict whole bases. Core reductions, component-local extraction, extra selected indicators and arbitrary coupling-guided search remain open. |
| Explicit affine/XOR | Row basis, rank changes and projected boundary equations. | Reuse the existing restricted engine through checked extraction/source bindings. Recognizing hidden XOR structure in arbitrary CNF is additional work. New independent equations can change every relevant boundary. |
| Disjoint or bounded-interface components | Component identities, dependency graph and exact boundary summaries. | Update affected components and stop propagation when their summary is unchanged. Coupling components or increasing width may invalidate the cheap decomposition. |

Prioritize the category where a profile shows repeated construction to be costly.
Do not implement five dynamic data structures merely because all are available.
The current propagation loop repeatedly scans clauses; implication SCCs, matching
and connected components are still reconstructed for new uncached residuals.
The matching history adapter avoids that acquisition only when its proposal works. These are
concrete maintenance gaps, not yet evidence of an end-to-end speedup.

### 4. Reduce hard interaction between otherwise easy components

This has the largest potential effect on search growth, but less immediate
measurement support than the repair control. Two components that are individually
satisfiable need not have compatible assignments on shared variables. Store or
derive an exact boundary relation

```
R_C(b) = there exists an assignment to C's private variables satisfying C at b.
```

Then reuse unaffected relations across source changes and across solver
categories. An affine basis, binary implications or a bounded diagram/table can
represent particular relations compactly; no one representation is compact for
all projected CNFs. Explicit tables may require 2^|b| entries. Converting between
representations, proving equivalence and discovering separators all need budgets.
A necessary condition must not be mistaken for the complete relation.

Before ordinary branching, investigate whether a small set of decisions splits
the residual into independently tractable parts, potentially of different types.
Choose decisions by exposed structure as well as occurrence count; charge the
lookahead. Measure distinct residuals and total work on mixed Horn/2-CNF/affine/
matching instances with controlled interface size and on adversarial overlap.

This direction is established in work on
[heterogeneous backdoors](https://www.cs.ox.ac.uk/standa.zivny/publications/gmosz14aaai-preprint.pdf)
and [component backdoor depth](https://drops.dagstuhl.de/opus/volltexte/2022/16984/pdf/LIPIcs-ESA-2022-46.pdf).
Those results motivate parameterized investigations; they do not guarantee cheap
discovery or a small parameter for every CNF. Our irreducible positive-overlap
encoding already shows why merely combining individually easy clause groups
does not give an unrestricted polynomial solver.

### 5. Share source, certificates and summaries across class transitions

Use durable clause identities, source deltas, assumptions and checked dependency
references as the common interface. A component changing class should not force
copies of unaffected components or invalidate facts whose dependencies still hold.
Separate exact event/source history from the shared semantic compilation cache.
SAT witnesses must satisfy the updated source; UNSAT refutations remain applicable
under conjunctive additions, with their source references checked.

The current residual key sorts/deduplicates and compacts ordered variable names;
it is not a full semantic or arbitrary-isomorphism canonical form. Try budgeted
type-specific normalization and candidate indexes followed by exact verification.
Do not assume an efficient arbitrary semantic-equivalence oracle. KD-trees or
similarity search can propose candidates but cannot establish reuse soundness.

The existing affine engine is useful evidence that repeated kernels can be
shared, but its successes and normalization costs belong to a restricted input
representation. Integration with the general CNF history needs a checked source
interface and measurements of recognition, conversion and proof reuse.

### 6. Remove representation costs where solving has already disappeared

Compress unary trie paths for long sparse identifiers and consider lazy support
index preparation for streams already satisfied by the current model. Activation
must reconstruct all earlier constraints and charge that cost. Physical input
and exact identifier output still cost their encoded length.

Repeated semantic no-ops should share state, but keeping every version identity
still requires provenance. Repeated events can share payloads or be run-length
encoded when exact reconstruction remains possible. Do not claim constant total
space for an unbounded version history.

On already-UNSAT streams, persistence currently dominates the new profile.
Investigate redundant SQL/serialization work or explicitly batched transactions
if the interface permits them. Do not claim a speedup by silently weakening the
guarantee that acknowledged updates are durable. Cold validation checkpoints must
also retain a stated trust boundary; skipping checks of an untrusted archive is
not free reuse. This priority moves upward when cheap-update streams dominate.

## Bounds and evidence still missing

Let M be the number of distinct acquired residuals and L_i their encoded sizes.
The prototype performs normalization, recognition, checking and persistence over
these residuals; storing full keys/certificates charges their aggregate sizes.
Reducing per-node overhead does not bound M polynomially. Likewise, incremental
maintenance helps only if affected structure or repeated summaries stay small.

When rejected updates repeatedly acquire copied prefixes of sizes L_t, source
storage alone can grow with their sum. Constant-size additions and a fresh copy
at every step can give quadratic cumulative source storage. Accepted repair on a
fixed base instead stores that base plus deltas and version references. Its
pure-repair assignment/support trie retains base nodes plus O(sum_t (d_t+1)b_t) copied
nodes and O(T) roots, with d_t addition length and b_t identifier bit length.
The stronger affected-clause index adds occurrence entries and persistent count
paths, with per-step path bound O(d_t*b_t + (r_t+1) log(m_t+2)), where r_t is the
affected clause count and m_t the parent clause count. Retained histories can
therefore still accumulate substantial state even when every update is accepted.
These node counts exclude integer/pointer/SQL byte overhead and cold rebuilding.
Joint repair adds the q_t moved variables: accepted retained paths are bounded by
O((d_t+q_t)b_t + (A_t+1) log(m_t+2)), with A_t distinct affected clauses, plus
posting entries and roots. It still scans the sum of moved variables' occurrence
lists. Discovery, cached block maps and repeated encoded move lists are additional;
see [the expanded accounting](resource-bounds.md#9-simultaneous-repair-in-the-experimental-cnf-history).

The next evaluation gap is a common workload matrix spanning categories and
their transitions, with growing easy and hard interactions, repeated and novel
components, sparse/dense identifiers, cold and warm histories. Record disjoint
phase times where possible, end-to-end time, retained logical/SQLite bytes,
allocation/RSS scope, replay time, residual count, fallback count and affected
clause/interface size. A competitive incremental-CDCL baseline is also missing
for this prototype. Five diagnostic samples cannot establish a global ranking.

No general small-interface, compact closure, bounded repair or uniformly
polynomial acquisition theorem has been established. The restrictions and
resource charges above remain necessary even when precomputed answers are cheap
to reuse.
