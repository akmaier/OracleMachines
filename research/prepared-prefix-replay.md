# Reuse one local proof-checking context during source reconstruction

Checkpoint: 26 November 2026. Reusing an exact local checking context reduces
source reconstruction time **45.00%** and complete measured workflow time
**23.41%** on the sixteen current cases. Every reconstructed state, hint, proof
origin, search result and downstream counter remains identical. Peak process
memory and serialized state are essentially unchanged. Structural coverage stays
**230/246**; this checkpoint replays the existing frontier.

The improvement has a clear limit: synthetic zero-hint, single-hint and
missing-support cases regress because copying and context setup are not amortized.
Those counterexamples remain in the results. No universal speedup is claimed.

## Profiling changed the target

The previous cost record identified source-prefix reconstruction as the largest
stage. Profiling showed that **all sixteen saved binary prefixes are empty**.
Their reconstruction nevertheless checks 320 transported local hints. The old
`local_hints` path invokes the original RUP checker separately for each hint, and
that checker validates and normalizes the same local CNF each time. The profile
records 416 calls to normalization and 320 calls to that checker; binary-prefix
step reuse would not address this workload.

The diagnostic profile, counters and raw `pstats` file are preserved. Profiling
runs after input loading, includes instrumentation overhead and is excluded from
the matched timing trials. The implementation targets the repeated local source
validation, while leaving binary-prefix replay and downstream preparation intact.

## Exact boundary and proof checks

The new `local_hints` function owns copies of the source, templates and event. It
checks the canonical original source, event root, injective variable mapping,
fixed assignments and the condition that the mapped local clauses are a subset
of the restricted original source. It still checks every original template and
its membership in the original source, guard compatibility and missing variables.

On the first eligible candidate it constructs the existing immutable
`LocalContext` for that exact local CNF, mapping and fixed assignment. All later
candidates in this one call share its source and clause-position map. The existing
`transport_state` routine still checks support containment after conditioning,
translates every trace, validates the lifted template, and checks every RUP unit
reason and conflict against the context's actual source clauses. Hint ordering,
origin-template indices, clause indices and the whole-residual flag are preserved.

The original RUP checker validates the local source on every invocation. The
context checker validates that source once at construction and performs the same
clause, reason and conflict checks on its immutable copy. Since neither the source
nor its map can change during the call, repeating the source validation adds no
new proof obligation. The event boundary and all proof checks remain necessary.
A hint whose original support is valid but absent from the local subset is rejected.

No caller-supplied context or checked marker is accepted. Contexts do not cross
events, source edits or calls. Prefix payloads are copied separately and replayed
with the original checker, including nonempty prefixes. Downstream shared joint
discovery and cold validation use the same implementations and allowances as the
baseline. The final audit reconstructs every case with the original binder and
checks every search result with the frozen full validator as well.

Across the sixteen cases, instrumented normalization literal visits fall from
**460,644 to 118,539**. The number of verified local hints remains **640** and the
number of checked reason literals remains **28,316** across initial reconstruction
and subsequent empty-prefix replay. The 320 initial hints now use sixteen local
contexts. Total context preparations increase from 16 to 32 because the unchanged
prefix-replay path also creates a context per case; the removed work is the many
separate source normalizations, not the number of proof checks.

## Matched complete cost

Two isolated repetitions in opposite order replay the same inputs and saved B8
results. The baseline includes the previous shared-joint-preparation improvement.

| Measurement | Original reconstruction | Shared local context |
| --- | ---: | ---: |
| Complete source reconstruction (s) | 0.35028 | 0.19266 |
| Downstream discovery (s) | 0.17155 | 0.16964 |
| Independent cold checking (s) | 0.16443 | 0.16101 |
| Persistence/reload (s) | 0.00558 | 0.00540 |
| Complete workflow (s) | 0.69546 | 0.53267 |
| Serialized result bytes | 177,042 | 177,042 |
| Peak process RSS (bytes) | 98,828,288 | 98,762,752 |

Reconstruction improves on all sixteen case-level means. Downstream code and
counters do not change; its timing variation is retained, including three
discovery and two checking regressions. The complete **23.41%** reduction includes
these variations, ownership copies, recognition, reconstruction, search, cold
checking and persistence. Input loading/startup, historical acquisition, profile,
pilot and final lineage audit are additional. No new feedback discovery or native
compilation is hidden in these replay totals. Two repetitions are finite evidence,
not a guarantee across machines or workloads.

## Synthetic scaling and failed amortization

The synthetic controls use 8, 32 and 128 variables with no hints, a single hint,
novel hints on distinct clauses, repeated hints, and a valid original proof whose
support is absent from the local subset. Each arm makes sixteen independent cold
`local_hints` calls per fixture, in two opposite-order isolated repetitions. These
are reconstruction-only diagnostics: fixture generation and summary serialization
are outside the timings. Full persistence is charged in the main census above.

| Fixture | Original total (ms) | Context total (ms) | Reduction |
| --- | ---: | ---: | ---: |
| Novel hints, 8 variables | 2.878 | 2.418 | 15.99% |
| Repeated hints, 8 variables | 2.795 | 2.400 | 14.14% |
| Novel hints, 32 variables | 26.932 | 9.417 | 65.03% |
| Repeated hints, 32 variables | 26.885 | 9.308 | 65.38% |
| Novel hints, 128 variables | 353.540 | 38.675 | 89.06% |
| Repeated hints, 128 variables | 364.391 | 37.550 | 89.70% |
| No hints, 128 variables | 6.698 | 8.346 | -24.60% |
| One hint, 128 variables | 9.497 | 11.391 | -19.94% |
| Missing support, 128 variables | 7.396 | 11.323 | -53.11% |

All no-hint, one-hint and missing-support fixtures regress at every tested size.
The complete tables and proofs remain in `analysis.json`. Context construction
is lazy after guard filtering, but a candidate can pass that filter and still
lose clause support during transport; setup then produces no accepted hint.
Even the no-hint path pays ownership copying. A future admission gate must account
for that overhead and predict useful sharing cheaply enough to repay recognition.
The novel-hint improvement shows that identical proof templates are not required:
the reusable object is their common local source and clause index.

## Bounds, retained state and next work

For `h` accepted hints sharing a local source with `L` literal occurrences, let
`N(L)` denote the implementation's canonical-source validation cost. The old RUP
path repeats `N(L)` for each accepted hint. Context reuse performs that validation
once, builds the positions map, and still checks all hint clauses and reason
literals. Ownership copying, template validation, transport and source/event
recognition remain additional. Exact costs also depend on sorting and encoding;
this is not a unit-cost bound independent of the representation.

The additional live context stores `O(1+L+n)` word slots for `n` local variables,
alongside owned input payloads and returned hints. It is released after the call;
there is no cross-event cache. The measured roughly 99 MB process peak does not
establish a memory saving. The existing **2,070,735-byte** open export, all native
archives and previous certificates are referenced unchanged. New experiments
still increase lifetime storage.

Reconstruction is now **36.17%** of total time, discovery **31.85%**, and cold
checking **30.23%**. Revisit repeated source/template work across these boundaries,
especially the checked handoff from initial hint transport through empty-prefix
replay to joint preparation. The low-yield synthetic regressions also motivate a
cheap context-admission rule. For coverage, keep the stronger `(28,18)` bank, six
unfinished orders and ten exhausted unchanged orders; the previous native
certificate regression remains. None of these measurements establishes compact
closure, complete efficient classification or a uniform arbitrary-SAT bound.

## Validation and reproduction

The audit preserves **1,146 prior source fingerprints**, **29,327 artifact entries
in 204 parent manifests**, all cumulative tables, reference/native bindings and
**64 original manuscript proof blocks**. It checks exact source/state/hint equality,
every main and synthetic result, all downstream counters, and complete cold
validation with the original implementation.

All **2,075 full tests** and **64 focused tests** pass. Nine new tests cover all current inputs, synthetic controls, conditioning and
component renaming, malformed events/templates, missing support, ownership under
caller mutation, nonempty binary-prefix replay, all 256 subsets of signed unit and
binary clauses on two variables, and seventy generated formulas with unlabelled
conditioned subsets and truth-table checks. The first nonempty-prefix fixture
incorrectly omitted the forced variable from wide clauses, so discovery returned
an empty prefix. Its failed log, source and protocol remain. The corrected fixture
exercises a genuine path; measured implementation and census code are unchanged.

Resume `experiments/results/cnf-prepared-prefix-replay/checkpoint.json`, using
`prepared_prefix_replay.remaining` for the unchanged frontier. Reproduce `prepare`,
`run_census` and `run_synthetic` with the compare script in a fresh directory
containing the preserved profile/pilot, then `validate` and `seal` with the validator.
Production defaults, proof rules and structural coverage are unchanged.
