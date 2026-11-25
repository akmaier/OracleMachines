# Probe the residual of a checked closure

Checkpoint: 25 November 2026. The [feedback pass](probe-feedback.md) left 116
events open with complete checked unit closures. An additional budget of 64
assumed probes now refutes 47 events, representing 41 distinct new roots. This
extends recognition to 177 of the original 246 post-binary events; 69 remain
unresolved. The added search budget produces the coverage gain. Conditioning
on the closure makes that search cheaper without changing coverage in this sample.

## Reuse and proof obligations

Validate the old failed probes, guards and closure before using any saved fact.
Every closure step must be unit under its predecessors, its assignment map must
agree, and no unsatisfied empty or unit clause may remain. Remove satisfied
clauses and fixed-false literals, deduplicate residual clauses, and retain an
original augmented-bank clause ID for every remaining clause. Variable names
are preserved during discovery. The original-source literal ranking is filtered
to variables occurring in this residual; a failed assumption promotes its
untested opposite.

The closure is entailed by the source with its checked guards and old exclusions.
Hence a residual model extends by the closure assignment, while a source model
restricts to a residual model. For a failed residual probe, prepend the checked
closure trace and map its reasons back to the augmented bank. The assumption
uses an unfixed variable, so it cannot contradict a closure step. An independent
checker verifies the entire lifted trace. Failed opposite assumptions refute
the source. Open and exhausted searches remain unresolved, including the current
refutation-only API's empty residual case.

Native reconstruction causally slices both failed traces and the old exclusions
they use. It selects their source support, transports coordinates and checks the
compact certificate before compilation. Old exclusion leaves expand to their
original source/guard proofs under the current branch context. Existing native
split and subset rules join the two branches and lift the original binary prefix.
No learned clause is admitted as an axiom. All checks precede warm root reuse;
source, guard, seed or closure edits require renewed binding.

New failures depend on the old feedback bank. They are retained as a separate
proof layer, not appended to the original seed format. They have not yet been
fed back into another propagation round. This separation makes the dependency
order explicit and prevents circular justification.

## Matched discovery and retained state

Both arms validate the same inputs, build the residual and use the same candidate
order. Restart propagates the full feedback bank for each assumption; conditioned
mode uses the residual index and lifts failures. The budget is **64 additional
assumptions**, 262,144 indexed occurrence visits and 256 unit steps per certificate,
including the closure prefix. It is not the original search budget. A pilot exposed
the outcomes before measurement; two alternating repetitions per target and mode
give 32 isolated census workers over eight targets, not an independent holdout.

| Measure, summed per-target means | Restart | Conditioned |
|---|---:|---:|
| Refuted / unresolved events | 47 / 69 | 47 / 69 |
| Discovery | 0.59058 s | 0.54068 s |
| Saved-prefix reconstruction | 2.23439 s | 2.24098 s |
| Complete census | 2.83627 s | 2.79350 s |
| Assumed probes | 5,063 | 5,063 |
| Propagation occurrence visits | 536,665 | 268,008 |
| Initialized clause slots | 2,062,917 | 1,930,964 |
| Index literal occurrences | 133,486 | 118,720 |
| Propagated unit steps | 36,938 | 18,597 |
| Retained certificate unit steps | 13,376 | 13,378 |

Visits fall 50.06%, discovery 8.45%, and complete census time 1.51%. Prefix
reconstruction accounts for 80.22% of the conditioned census. Checking, condition
construction, ranking, indexing and certificate lifting are charged to discovery;
prior acquisition, saved-closure diagnostics, loading/startup and final audits
remain additional. Both arms stop all 69 misses at the root budget, with no work
or trace cap reached. Identical coverage is empirical: different propagation order
and a charged closure prefix can affect bounded outcomes on other inputs.

The conditioned index contains 11.06% fewer literal occurrences in aggregate,
but both arms retain the full source and feedback bank. Peak census RSS is
96,501,760 bytes for both, including loaded inputs and interpreter. This is not
an 11% total-memory reduction. The largest per-event index has 1,809 literals
in either arm. Conditioning removes 656 fixed variables across events, with a
maximum of 27 per event and 149 remaining active variables.

The 344 saved new failures include 2,634 copied closure steps. Their full lifted
traces have two more steps than restart, because propagation order can differ.
Compact serialized program bytes rise from 156,933 to 157,432; this excludes
common inputs and native archives. Reusing work does not automatically compress
its certificate. Sharing a checked closure prefix across certificates is a
separate opportunity, with binding and replay costs still to be charged.

## Native proof cost and preservation

The 47 gains contain 41 distinct roots absent from the preceding recognized sets.
Thirty-seven were already UNSAT in inspected snapshots and four were unknown.
Ordinary local solving and reconstruction both refute all 41. There are 164
isolated trials, two alternating repetitions per method, and both independent
cold readers accept all 82 unique archive/root pairs. Warm reuse changes no
authority table.

| Summed per-case mean | Fresh local solver | Closure compiler |
|---|---:|---:|
| Solve or compile | 5.35369 s | 5.70532 s |
| Warm check | 0.07348 s | 0.50879 s |
| Cold readers | 5.70760 s | 4.10581 s |
| Persistence | 1.99794 s | 1.34822 s |
| Complete local trial | 13.30158 s | 11.77838 s |
| Encoded record bytes | 25,538,657 | 12,908,078 |
| Records | 2,011 | 4,960 |

Compilation is 6.57% slower in aggregate, while record bytes fall 49.46% and
complete local trials fall 11.45%. Compilation improves on 15 cases, complete
trials on 17, and bytes on 31; all other cases remain explicit regressions.
Charging the 41 representative events' continuation adds 0.94926 seconds,
giving 12.72764 seconds versus 13.30158 for fresh local trials. This small subtotal
excludes seed acquisition and fallback on 69 misses; it is not a whole-workload
advantage. Isolated record totals can duplicate shared proofs.

Source support falls from 43,114 to 8,616 literals with no coordinate fallback.
Compilation creates 4,527 trace splits and 41 opposite-probe splits, reuses 296
cofactor results, and retains 62 original binary-prefix splits. It expands 237
old-exclusion leaves and handles 122 already-fixed trace steps. Peak trial RSS
is 88.28 MB for fresh solving and 63.78 MB for reconstruction; these process
maxima are not general memory bounds. New archives are supplemental. The
cumulative bank, its six authority tables and every prior result remain intact.

Validation preserves 184 prior manifests, 24,487 artifacts and 1,060 sources;
the checkpoint binds 1,064 sources. All 1,903 tests pass, including 38 focused
tests. The new checks cover small exhaustive truth comparisons, guarded and
unguarded provenance, support lifting, budget stops, malformed input before
warm reuse and both cold readers. An initially unsorted guard-test fixture and
its failure log are preserved alongside the corrected fixture. All 64 manuscript
proof blocks remain unchanged; existing full-suite SQLite warnings are recorded.

## Bounds and next target

Let the checked feedback bank have C clauses and L literal occurrences, its
closure K assignments, and the residual C_r clauses and L_r occurrences. Let P
be attempted probes and F saved failures. Building the residual takes O(L)
expected word work plus sorting; indexing takes O(C_r+L_r) work/space. Each probe
initializes O(C_r) state and visits at most O(L_r) occurrences. Lifting adds O(FK)
copied prefix steps plus the residual failed traces. Original-source ranking,
seed/guard/closure checking, normalization and native reconstruction are additional.
The original bank remains resident, so working memory includes O(C+L+C_r+L_r)
words plus inputs, proofs, assignments and sorting storage. These are costs of a
bounded recognizer, not bounds for a complete unrestricted-SAT solver.

**Next coverage target:** 37 of the 69 open events retain 180 new failures,
alongside 125 old exclusions across the remaining set. Feed the new complements
into one checked propagation round while keeping their old-bank dependencies
explicit. The other 32 events have no new failures; twenty have neither old nor
new exclusions. Repeating unchanged probes there adds no information. They need
a separate untested-candidate or interaction analysis, with an explicit budget.

**Next cost target:** reuse source-bound preparation and prefix reconstruction
across rounds, then investigate shared closure prefixes in retained certificates.
The census is now dominated by reconstruction, while native proof compilation
still trails ordinary solving. Further reductions in propagation alone have a
small total-cost ceiling. No bound on discovery rounds, distinct contexts,
unlimited history or unrestricted-SAT complexity follows from these measurements.

Resume [the checkpoint](../experiments/results/cnf-closure-probes/checkpoint.json).
The [protocol](../experiments/results/cnf-closure-probes/protocol.json),
[analysis](../experiments/results/cnf-closure-probes/analysis.json),
[retained-state accounting](../experiments/results/cnf-closure-probes/retained-state.json)
and [remaining cases](../experiments/results/cnf-closure-probes/remaining.json)
preserve the successes, misses, proof layers and measured regressions.
