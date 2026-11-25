# Compose failed probes across two checked proof layers

Checkpoint: 25 November 2026. The [closure-probe round](closure-probes.md) left
69 events unresolved, retaining 180 new failed probes in 37 events. Adding their
complements and propagating once now refutes 16 events, representing 15 distinct
new roots. No new assumed probes are made. Recognition reaches 193 of the original
246 post-binary events; 53 remain unresolved. All 15 roots already had UNSAT status
in the inspected snapshots, and ordinary local solving also refutes them.

## Exact composition and reconstruction

Let B0 contain the source and its checked guards. Old failed probes have conflict
traces on B0 under their respective assumptions; their complements form U1.
Thus B1 = B0 together with U1 is equivalent to the original source. New failed
probes are checked on B1, not B0. Their complements U2 give B2 = B1 together
with U2, again equivalent to the source. A unit conflict on B2 is therefore a
refutation. An open closure is only a collection of entailed assignments.

The implementation validates the original seed, old closure and new probe layer
before building B2. Clause IDs bind each trace to its specific bank. New probes
on old fixed variables are rejected. Each learned-unit origin names either an
old proof on B0 or a new proof on B1. Reconstruction must descend strictly to a
lower layer: a proof cannot use itself or another fact from its own new layer.
The original and new seeds cannot be flattened into one original-bank seed.

Causal support selection follows both layers back to source clauses and checked
guards. It transports and rechecks the selected proof before native compilation.
When a learned unit is falsified by the current branch, expand its saved failed
probe under that stronger context. Already assigned trace variables either agree
and are skipped, or disagree and terminate at the checked reason. Native splits,
empty/unit leaves and subset wrappers preserve source-only authority. No learned
unit is admitted as an axiom. Original binary-prefix lifting is unchanged, and
all portable checks precede warm reuse or publication.

## Matched discovery

The two arms validate the same layers and construct both banks. Base propagates
B1, while feedback propagates B2. Both make one unconditional pass, capped at
262,144 occurrence visits and 256 unit steps. Two alternating isolated repetitions
per target and mode give 32 census workers over eight targets. Pilot outcomes
were exposed before timing. An initial pilot redundantly checked new traces;
its source and results are retained before removing that duplicate check. This
is not an independent holdout or an iteration to an unrestricted fixed point.

| Measure, summed per-target means | Base | Feedback |
|---|---:|---:|
| Refuted / open events | 0 / 69 | 16 / 53 |
| Discovery | 0.27823 s | 0.27560 s |
| Saved-prefix reconstruction | 1.24479 s | 1.23027 s |
| Complete census | 1.53066 s | 1.51325 s |
| Bank literal occurrences | 80,669 | 80,849 |
| Initialized clause slots | 27,911 | 28,091 |
| Occurrence visits | 2,929 | 12,009 |
| Unit assignments | 207 | 989 |

Both arms check 305 failed-probe proofs: 125 old and 180 new. Every new exclusion
adds a distinct unit. All 69 passes complete without a work or trace cap; there
are zero new assumed probes. The small timing differences do not establish a
stable speed advantage. Preparation and proof checking dominate this short pass,
with saved-prefix reconstruction additional. Prior acquisition, closure
diagnostics, loading/startup, native compilation and final audits remain charged
separately. Peak census RSS is 96.47 MB for base and 96.58 MB for feedback.

## Native costs: coverage improves, reconstruction regresses

The 16 gains contain 15 distinct roots absent from the preceding recognized sets.
All are UNSAT in the prior inspected snapshots. Fresh solving and reconstruction
both refute all 15 in 60 isolated trials, two alternating repetitions per method.
Both cold readers accept all 30 unique archive/root pairs; warm reuse adds no
records to any of the six authority tables.

| Summed per-case mean | Fresh local solver | Layered compiler |
|---|---:|---:|
| Solve or compile | 2.53550 s | 3.91085 s |
| Warm check | 0.02775 s | 0.16463 s |
| Cold readers | 2.66090 s | 2.69872 s |
| Persistence | 0.97361 s | 1.07253 s |
| Complete local trial | 6.26689 s | 7.90190 s |
| Encoded record bytes | 12,209,959 | 8,989,382 |
| Records | 959 | 3,477 |

Compilation is 54.24% slower and complete local trials 26.09% slower, despite
26.38% fewer aggregate record bytes. Only two cases improve in runtime; seven
use fewer bytes. All regressions are retained. Charging representative
continuation adds 0.30670 seconds, giving 8.20860 seconds versus 6.26689 for fresh
local trials. This positive-only subtotal still excludes acquisition and fallback
on the misses. There is no demonstrated end-to-end advantage on this set.
Isolated byte sums may duplicate shared proofs. Peak trial RSS is 85.41 MB for
fresh solving and 67.21 MB for reconstruction; these are process maxima, not a
general memory bound.

Source support falls from 16,371 to 3,823 literals with no coordinate fallback.
The compiler makes 3,351 trace splits plus 16 original prefix splits, reuses 243
cofactor results, and handles 98 already-fixed trace steps. It expands 67 new
exclusion leaves and 163 old leaves, although the selected supports use only 56
old exclusions. Repeated expansion under different contexts remains costly.

A separate profile of `new-1-38`, the largest exposed compilation regression,
reproduces its exact counters and authority digests. It records 1,584 normalization
calls (0.448 s cumulative), 1,414 restriction scans (0.256 s), and 317 native
publication verifications (0.411 s). These instrumented cumulative costs overlap
and must not be added. They identify repeated cofactor construction and checking
as a more credible next runtime target than the now-small propagation pass.
The profile is diagnostic, not an additional matched speed measurement.

## Persistent closures and next work

A separately charged scan reconstructs and checks complete B2 closures for all
53 open events. They retain 207 assignments, compared with 87 in their old B1
closures: 120 new assignments, including 67 beyond the new exclusion variables.
Exactly 21 events gain assignments. The other 32 are unchanged; twenty have
neither old nor new exclusions. The remaining set retains 59 old and 53 new
failed probes. Both proof layers and both closures are stored with their bank
bindings. The extra closure diagnostic takes 0.24079 seconds; these portable
facts are not independent native verdicts or SAT certificates.

**Next runtime target:** reuse immutable canonical cofactors and validated
preparation during reconstruction, retaining checks at publication and independent
cold replay. The profile shows why another propagation-only optimization has
limited value. Measure recognition, checking and cache space alongside any gain.

**Next coverage target:** a bounded search on the 21 changed closures can exploit
the 120 additional assignments. The 32 unchanged cases need untested candidates,
a different budget or stronger interaction; repeating the identical probe prefix
cannot discover more. Do not treat repeated rounds as a polynomial completeness
argument, or assume that every new layer yields progress.

For a source-plus-guard bank with C clauses and L occurrences, and U1/U2 retained
units, indexing and one complete propagation pass use O(C+L+U1+U2) expected word
work/space under the existing dictionary model. Bank sorting and every proof,
closure and provenance check are additional. The implementation retains all
three banks and the seed traces. Fixed two-layer descent prevents circular
justification but does not bound native proof expansion, future layers, distinct
contexts or unlimited retained history.

All 1,911 tests pass, including 46 focused checks for both proof representations,
guard provenance, malformed/forward dependencies before cold and warm writes,
budgets, exhaustive truth checks on small generated formulas and both cold
readers. The manuscript's 64 earlier proof blocks are unchanged. Validation
preserves 185 prior manifests, 24,953 artifacts and 1,064 sources; the new
checkpoint binds 1,068 sources. All earlier archives and cumulative authority
tables remain unchanged; new proofs are supplemental. Existing full-suite SQLite
warnings are recorded, with none in focused tests.

Resume [the checkpoint](../experiments/results/cnf-layered-feedback/checkpoint.json).
The [analysis](../experiments/results/cnf-layered-feedback/analysis.json),
[profile](../experiments/results/cnf-layered-feedback/profile-largest.json) and
[open closures](../experiments/results/cnf-layered-feedback/remaining-closures.json)
retain the new results, cost regression and next reusable state.
