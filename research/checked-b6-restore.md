# Share checked preparation during cold B6 recovery

Checkpoint: 26 November 2026. The existing full-result recovery workflow checked
a portable result and then rebuilt the same checked state to create a search
session. A new restore function validates once and passes the resulting state
directly into the owned session. On eighteen retained cases, checking plus
restoration is **46.86% faster**, and complete measured time is **16.47% lower**.
Both arms produce identical continuations, proofs and serialized results.

There is no new refutation: sampled recognition stays **228/246**, with **18 open**.
A short continuation adds one failed assumption, leaving **25 failures in seven
cases**. Thirteen current literal orders are exhausted. Peak process memory and
persisted result size do not materially improve.

## A checked handoff, not a trusted marker

`restore` accepts the original input/provenance and a complete portable result.
It checks the result's shape and types, privately copies the inputs and result,
then performs the same semantic checks as the existing B6 validator: source,
guards, earlier proof banks, closure, exact binding, schedule, all failure
traces, program verdict/terminal fields, and agreement between program and cursor.
It constructs a continuation only after those checks succeed. No external
"already checked" flag, digest-only match or prepared token is accepted.

The existing validator and session constructor both call the same preparation
and history-loader routines. The new function calls those once, retains their
validated queue, pending promotion, completed history, failures, bank and exact
binding, and initializes the existing session's private fields. Result checking
is not dropped merely because a cursor can be loaded. In particular, an
individually valid but inconsistent program/cursor pair is rejected. Explicit
B6 recovery needs no comparison for importing an older B5 cursor; that unused
comparison in the old constructor is also avoided.

The returned session owns its snapshot and copies public results. Later edits
to caller input or results cannot change it; changed inputs need a new restore.
Portable data is checked anew on every cold recovery. Reflection or concurrent
mutation of private internals is outside this process-local ownership contract.
The adapter depends on the frozen `PreparedB6Search` layout pinned by the source
ledger. Native compilation and its independent readers remain unchanged.

Correctness follows by matching the existing validator's accepted full-result
contract and the existing constructor's resulting state. The new routine uses
the same preparation, schedule replay and program check before constructing
that state. Subsequent advancement uses the unchanged session implementation.
Tests and the audit compare these continuations against both the old two-step
workflow and standalone discovery. Claimed open history is still scheduling
data, not a SAT or exhaustion proof.

## Matched cold recovery and total cost

Two arms run twice in opposite order on the same eighteen exposed cases:

* `separate`: full result validation, followed by the existing owned-session
  constructor, then one continuation of up to eight assumptions.
* `shared`: one full checked restore, then the identical continuation.

Both allow 262,144 occurrence visits and use the stored 256-step trace bound.
The census charges source-prefix reconstruction, checking/restoration and
copies, continuation, final serialization/reload, and independent full semantic
checking of that output. Startup/input loading, earlier acquisition, composition
diagnostics and final audit are additional. This is a different starting frontier
and workflow from the earlier 64-probe chunk benchmark; their percentage savings
must not be multiplied or treated as matched cumulative improvements.

| Summed per-target means | Separate check/construct | Shared checked restore |
| --- | ---: | ---: |
| Source reconstruction (s) | 0.36671 | 0.36673 |
| Full checking and restoration (s) | 0.28143 | 0.14956 |
| Short continuation (s) | 0.00408 | 0.00406 |
| Final persistence/reload (s) | 0.00601 | 0.00612 |
| Independent final checking (s) | 0.13368 | 0.13433 |
| Complete census (s) | 0.79580 | 0.66470 |
| Binding bytes constructed during restore | 1,488,498 | 744,249 |
| Schedule checks during restore | 17,400 | 8,700 |
| New assumptions | 56 | 56 |
| Per-probe initialization clauses | 24,832 | 24,832 |
| Propagation occurrence visits | 1,525 | 1,525 |
| Standalone result bytes | 214,799 | 214,799 |
| Maximum process RSS (bytes) | 97,353,728 | 97,337,344 |

Restoration improves on all eighteen cases, including exhausted orders. Warm
advancement is unchanged; its small timing regressions on seven cases, and final
checking regressions on fourteen, remain recorded. The RSS difference is only
16 KiB and demonstrates no material memory reduction. Final result bytes are
identical. Copying the entire result adds work to the shared path, but avoiding
the second preparation and schedule replay more than offsets it on this sample.
The comparison concerns checking a complete reported result and constructing a
session. It does not claim the same saving over an API that merely imports a
cursor while ignoring the redundant reported verdict/program.

## Discovery diagnostic and next targets

Before choosing the cost improvement, all 24 parent B6 failures were composed
into a diagnostic B7 bank. They yield no contradiction and add **25 assignments
across seven closures**, one beyond explicit exclusion variables. The complete
closures and original proofs are preserved. This pass does not implement B7
probing or a B7 native compiler.

Continuing the original B6 frontiers adds a second failure in `(61,61)`. The
current set is `(1,15):2`, `(28,18):1`, `(28,19):5`, `(37,39):4`, `(37,40):8`,
`(40,0):3`, and `(61,61):2`. **Compose all 25 and probe the resulting changed
banks next.** The diagnostic used the earlier 24, so it is not a closure for the
latest full set. Five B6 cases still have later candidates: `(37,39)`, `(37,40)`,
`(40,0)`, `(67,0)` and `(67,63)`. The other thirteen exhaust their present order;
unchanged exhausted banks need stronger interactions. None is certified SAT.

Source-prefix reconstruction now accounts for **55.17%** of the shared census.
Sharing checked prefix data under exact source, guard and context bindings is
the largest remaining individual runtime opportunity. Final independent checks
remain charged. Reducing repeated validation changes a constant factor in the
cost of checking retained provenance; it does not bound that provenance's size,
future proof layers, native contexts or unrestricted SAT.

The eighteen-case open export grows from **1,474,056 to 1,689,359 bytes**, retaining
all older fields and appending `b6_checked_restore_cursor`. The separate diagnostic
is 1,501,058 bytes. Standalone results are the same size in both arms; this change
provides computational reuse, not persistent compression or a lifetime bound.

## Validation and reproduction

All **2,021 full tests** and **156 focused tests** pass. New tests cover the
full-result contract, inconsistent program/cursor pairs, changed source and
closure, forged old bindings, forward/invalid reasons, mutation isolation,
nondefault trace bounds, interruption/retry, terminal native replay through both
readers, exhaustive binary formulas and generated small truth tables. The audit
replays both arms and independently checks every retained result and diagnostic.
All 1,120 older sources, 27,922 artifact entries in 198 parent manifests, and
64 original manuscript proof blocks remain unchanged. No native authority record,
production default or cumulative table changes.

Resume `experiments/results/cnf-checked-b6-restore/checkpoint.json`, especially
`checked_b6_restore.remaining` and each row's `b6_checked_restore_cursor`.
Earlier `b6_prepared_cursor` and `b6_probe_cursor` values are retained unchanged.
Reproduce with `pilot`, `prepare`, and `run_census` in
`compare_cnf_checked_b6_restore.py`, then `validate` and, after tests/manuscript
checks, `seal` in `validate_cnf_checked_b6_restore.py`, using a fresh directory.
