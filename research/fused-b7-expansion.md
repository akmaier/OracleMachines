# Share checked preparation across composition and B7 search

Checkpoint: 26 November 2026. A single owned expansion validates the original B6
result once, composes its checked exclusions and searches B7. Empty checked
failure sets reuse the existing clause bank, exact closure trace, residual view
and checked schedule. On the same eighteen expansion inputs, this reduces
**expansion time 44.70%** and **complete measured time 16.97%** versus separate
composition and discovery. All returned closures, cursors and failure proofs
match the preserved B7 results on this corpus.

This is a cost improvement, not further search: recognition remains **228/246**,
with **18 open**. Both existing discovery routes remain available: **30 B6 failed
assumptions** and **15 B7 failed assumptions**, with their original provenance.
No new native compiler, authority record or production default is introduced.

## One checked operation and an exact no-op

The public `expand` operation accepts all original B6 inputs and the complete
B6 result. It privately copies those inputs, prepares and checks the earlier
proof layers, loads the B6 cursor, checks every retained failure and verifies
program/cursor agreement. Only an unresolved B6 result may enter this expansion.
No caller-supplied prepared state, verified marker or digest-only shortcut is
accepted. Optional B7 continuation cursors are checked against the resulting
full binding and schedule.

For nonempty failure sets, each checked contradiction under assumption `l`
entails `(-l,)`. Appending these exclusions preserves the satisfying assignments
of the prior bank. The operation constructs and checks a complete B7 unit
closure, then builds its residual view. A contradictory composition is rejected
explicitly for separate feedback-refutation handling; this API does not turn it
into an open or SAT verdict. Composition remains a complete scan outside the
bounded occurrence-probe budget.

If the checked B6 failure set is empty, B7 adds no clause. The prior bank's
checked unit fixed point is therefore still a fixed point, with unchanged reason
IDs and residual clauses. The function shares these objects internally rather
than rebuilding the clause dictionary, sorting it, propagating again and
reconstructing the residual view. Eleven measured cases qualify, sharing banks
containing **3,970 clauses**. This skips physical reconstruction of an empty
stage; the logical B7 version and portable B7 binding remain present.

When the bank, closure trace and trace allowance match, the old B6 schedule has
already been validated on the same candidate order. It can be handed directly
to the B7 search without another load/replay. A trace-bound change disables that
history import. Changed banks start fresh, and explicit B7 cursors still undergo
their own independent load/check. Each new probe uses the existing bounded
propagation implementation and maps reasons back to the checked B7 bank.

The no-op rule preserves the *existing* valid closure trace. An alternate valid
trace order can differ from the trace produced by deterministic recomputation;
then serialized results and bounded scheduling can differ while remaining valid.
The exact byte/result equality reported here is for the measured corpus, whose
old traces match recomputation. A dedicated test checks the alternate-order case
against the unchanged independent validator. Inputs or returned payload edits
cannot mutate the caller's original data through an alias retained by expansion.

## Matched cost and attribution

Two repetitions in opposite arm order compare:

* **Split:** the existing composition routine followed by existing B7 discovery.
* **Fused, rebuild:** validate once and share the checked schedule, but rebuild
  every clause bank, closure and residual view.
* **Fused, reuse:** additionally reuse those objects on empty checked failures.

All three arms replay the original inputs of the previous B7 experiment. They
perform the same 546 new probes and produce the same full closures/results;
this checkpoint does not advance either saved frontier. The independent final
validator rechecks every output, including the source, guards, all prior proof
layers, closure, binding, schedule and program agreement.

| Summed per-target means | Split | Fused, rebuild | Fused, reuse |
| --- | ---: | ---: | ---: |
| Source reconstruction (s) | 0.36155 | 0.36425 | 0.35874 |
| Complete expansion (s) | 0.29800 | 0.17470 | 0.16479 |
| Persistence/reload (s) | 0.00668 | 0.00599 | 0.00549 |
| Independent final checking (s) | 0.14734 | 0.14767 | 0.14560 |
| Complete census (s) | 0.81751 | 0.69668 | 0.67877 |
| Binding bytes constructed in expansion | 1,675,213 | 930,964 | 930,964 |
| Schedule checks in expansion | 19,300 | 8,756 | 8,756 |
| Whole-input copies | 0 | 18 | 18 |
| New probes | 546 | 546 | 546 |
| Probe initialization clauses | 217,940 | 217,940 | 217,940 |
| Propagation occurrence visits | 23,500 | 23,500 | 23,500 |
| Serialized closure/result bytes | 214,592 | 214,592 | 214,592 |
| Peak process RSS (bytes) | 97,435,648 | 97,468,416 | 97,304,576 |

The census charges source-prefix reconstruction, recognition, private copying,
complete composition/search, serialization/reload and independent final checking.
Startup/input loading, historical acquisition and final audit are additional.
The controls pay the same search budget; preserving the validated schedule
removes checking work without removing any new probe.

Expansion improves on all eighteen cases versus split. Beyond shared validation,
empty-stage reuse reduces expansion time a further **5.67%** versus fused rebuild
and complete measured time **2.57%**. Two changed cases regress in expansion time
against that control; all regressions remain in the analysis. The small differences
in unchanged reconstruction and verification stages are timing variation, not
changes in their algorithms. These percentages are not cumulative with earlier
experiments on other starting frontiers or workflows.

The RSS difference is about 128 KiB, with no material process-memory improvement.
Every remaining probe still initializes arrays for every residual clause; even
exhausted orders still construct the occurrence index. Exact binding strings
and independent cold validation also remain. Source-prefix reconstruction is now
**52.85%** of complete measured time, the largest individual runtime target.

## Persistence, limitations and next work

The prior **2,122,938-byte** open export is referenced unchanged. The checkpoint
does not append another identical cursor version or duplicate that export.
Per-arm census files still grow the experiment archive, and neither lifetime
storage nor the number/size of future proof layers is bounded by this change.
Portable results have identical size across the arms.

The next coverage step remains combining the B6 and B7 failures, including the
three B6-only new failures at `(37,40)`, while checking every reason on its original
bank. Updating B6 inputs changes the B7 binding; relabelling a cursor does not
establish valid transport. Ten B7 and sixteen B6 orders are already exhausted,
without SAT certificates. The next larger cost target is sharing source-prefix
reconstruction with explicit source/guard/context bindings; independent cold
checking remains charged. Uniform polynomial arbitrary-SAT coverage is still
unproved.

All **2,039 full tests** and **174 focused tests** pass. The tests cover both
physical reconstruction paths, exact result matching, malformed prior results,
forward reasons, no-op bypass attempts, alternate valid closure ordering,
trace-bound changes, cold continuation, interruption/retry, terminal checking,
explicit composition conflicts and small truth tables. The initial alternate-trace
test incorrectly used a helper that assumes no source units. Its failing log,
fixture and initial protocol are preserved; the corrected test explicitly builds
valid earlier layers. Timed implementation, harness, inputs and measurements did
not change, and the audit checks this correction separately.

The audit preserves **1,129 prior sources**, **28,380 artifact entries in 200
parent manifests**, and **64 original manuscript proof blocks**. Resume
`experiments/results/cnf-fused-b7-expansion/checkpoint.json`; its
`fused_b7_expansion.remaining` binding points to the unchanged B7 open export.
Reproduce `pilot`, `prepare`, `run_census`, `validate` and `seal` using the compare
and validate scripts and a fresh directory; the fixture-correction evidence is
specific to this recorded run, not a prerequisite of the expansion algorithm.
