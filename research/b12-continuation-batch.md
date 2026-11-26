# Sharing B12 preparation across bounded continuation rounds

Checkpoint: 26 November 2026. A privately prepared batch reproduces every result
of repeated B12 continuation calls while reducing discovery time **25.50% for
source order** and **25.24% for untested-first**. Complete measured workflow time
falls **10.03% / 9.32%**, including a separate cold check of every saved round.
Peak memory and result bytes do not materially improve. Coverage stays
**232/246**, with **14 open** and no new native certificate.

## New implications and exhausted orders

Three additional rounds, each allowing at most 64 probes, finish the two remaining
B12 schedules. Both orders find failure **32** at `(37,39)` and **131** at `(67,63)`.
The checked joint closure adds four assignments in local bank coordinates:

| Case | Additional forced values | Residual clauses | Residual literals | Residual variables |
| --- | --- | ---: | ---: | ---: |
| `(37,39)` | 32=false | 553 → 545 | 1,575 → 1,552 | 138 → 137 |
| `(67,63)` | 49=true, 131=false, 145=true | 347 → 330 | 986 → 935 | 134 → 131 |

Source order also rediscovers 83 at `(67,63)`; untested-first rediscovers -119 and
-116. Those failures were already available from the other retained history and
are not counted as new implications. At completion, both orders have the same
failed-assumption sets on these fixed B12 banks, though their sequences differ.

All fourteen **B12** orders are now exhausted in both policies. This is not a SAT
verdict, and it does not exhaust other banks: retained B13 histories and the new
combined closures remain separate search opportunities. A union consumes all its
rounds and both order budgets; it is not a single 64-probe result. The new clauses
have not been counted as native root certificates.

## Exact reuse and a continuation boundary that must not be skipped

The new API accepts the original 24 B12 inputs, five closures, a saved cursor,
round limit and per-round probe/work/trace bounds. It privately copies these,
prepares the common bank/provenance/closure/order once and checks all lower
histories through the existing shared B12 preparation. It then uses the unchanged
search engine for each bounded round. Every result is copied before export.

Each round reloads its portable cursor, even within the owned call. This matters:
the existing engine can pop the next root before noticing a probe/work limit.
Passing its mutated queue directly to the next round could skip that unfinished
root or lose an opposite-literal promotion. Replaying the completed sequence
reconstructs the exact next root, checks its policy binding and rechecks retained
failed proofs. Only the invariant preparation is shared. Index construction and
probe allowances still reset separately per round.

The batch stops on a generated complete result, a refutation, or zero completed
progress. A stalled root is retained for later resumption with appropriate
resources. The API does not infer exhaustion from an unchecked incoming program
label. Changed sources, closures, policy or trace bounds fail the existing exact
bindings; histories and supplied cursors remain independently checked. Open
completions retain the earlier honesty assumption for coverage reuse and never
constitute SAT or UNSAT evidence.

No caller-supplied prepared object or trusted marker is accepted, and no authority
survives the call. Every exported round keeps the existing B12 format and passes
its ordinary cold validator. Final auditing also reconstructs the banks and
provenance independently from frozen lower routines. No batch-specific proof
format or native compiler is introduced.

## Matched measurements

Four balanced rotating mode orders run before the heavy regression suite. Each
mode uses the same fourteen exposed inputs and at most three additional rounds
per policy. Twelve cases stop after one already-complete round; the two productive
cases use three rounds, giving **18 snapshots per ordering**. The separate arm
calls the current shared-B12 discovery API each round. Both arms retain independent
snapshot copies, serialize/reload every snapshot and cold-check each separately.

| Mode | Reconstruction (s) | Discovery (s) | Cold checking (s) | Persistence (s) | Complete census (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| source separate | 0.16452 | 0.25510 | 0.24823 | 0.00587 | 0.68498 |
| source batch | 0.16425 | 0.19005 | 0.24717 | 0.00558 | 0.61624 |
| unseen separate | 0.16273 | 0.25401 | 0.24516 | 0.00634 | 0.67816 |
| unseen batch | 0.16413 | 0.18989 | 0.24739 | 0.00525 | 0.61496 |

On the two productive cases alone, discovery falls **62.56% / 62.66%**. Across all
cases, common preparations fall **18 → 14** per policy. Search still performs
**296 probes**, **18 index builds**, and **10,028 / 8,969 occurrence visits**.
The exact per-round results and search counters agree. All-history schedule checks
fall **34,896 → 28,108** because lower histories are no longer rechecked through
repeated preparations; these checks must not be misclassified as search work.

Each order has five case-level discovery regressions, all among cases using only
one round. No preparation reuse is available there. Unchanged cold checking has
six / nine case regressions; aggregate untested-first checking is **0.91% slower**.
Source persistence has ten case regressions despite a lower aggregate time. All
case-level measurements are retained; the batching benefit is concentrated in
multi-round cases rather than universal across inputs.

Source snapshots remain **226,983 bytes** in both arms; untested-first snapshots
remain **229,561 bytes**. Peak process RSS changes **99,074,048 → 99,090,432 bytes**
and **98,992,128 → 99,008,512 bytes** respectively. No peak-memory or proof-storage
saving is established. Keeping multiple snapshots costs their retained space.
Startup/input loading, acquisition, pilots, native compilation, feedback composition
and final lineage audits are additional. Audit diagnostics overlap tests and are
not production timings.

## Bounds, limitations and next target

For `r` rounds, common preparation cost `P` changes from `rP` to `P`. Cursor reload,
index construction, search, snapshot copying, persistence and cold checking remain
charged for each round. A round has its own probe/occurrence limits; the batch's
allowance is the sum over its executed rounds. These limits do not cover history
checking, copying, exact binding construction or index setup. No uniform
polynomial bound on arbitrary SAT or oracle acquisition follows.

After batching, cold checking is about **40%** of measured total time, discovery
31% and source reconstruction 27%. An independently owned cold batch could share
invariant preparation while retaining every snapshot's proof check; that is the
next measured runtime target, not a permission to trust discovery state.

The next coverage targets are the two newly strengthened residuals above. Compare
them with retained B13 schedules before adding another feedback layer. Repeating
an identical exhausted B12 order cannot add information. For unchanged exhausted
cases, investigate stronger checked interactions or another decomposition, using
the preserved negative experiments to avoid repetition. The earlier native
compilation regression remains; no new production default is selected here.

## Preservation and validation

Resume `experiments/results/cnf-b12-continuation-batch/checkpoint.json`, field
`b12_continuation_batch.remaining`, using
`compare_cnf_b12_continuation_batch.load_frontier`. The **15,490-byte** overlay
references **4,508,174 bytes across 214 transitive frontier files**, including both
policies and every round. Earlier native archives and other evidence are additional.
This avoids a flattened duplicate resume export; lifetime evidence storage grows.

The audit preserves **1,179 earlier source fingerprints** and **31,573 artifact
entries in 212 manifests**. Four new source files bring the ledger to 1,183.
Reference/cumulative tables and all native archive bindings remain unchanged.

Nine new tests cover every historical snapshot, one-probe boundaries and cursor
reloads, stalled work and cold resumption, caller mutation and snapshot aliasing,
original-history/closure/cursor/policy corruption, trace isolation, exported proof
checking, overlays and small-model correctness. The small-model check enumerates
all 256 subsets of eight signed unit/binary clauses on two variables and seventy
generated five-variable formulas, then checks applicable unit-simplified open
histories against exhaustive models. This is not general SAT coverage.

An initial test wrongly treated `cursor_schedule_checks` as a search-only counter.
Its failure is retained; the corrected test distinguishes lower-history work from
search operations and verifies a portable cursor reload for every round. The
implementation and pilot were unchanged by that test correction.

All **2,145 tests** and **36 focused tests** pass. The full suite reports
44 SQLite resource warnings (44 in the parent run); the focused suite reports
0. No SQLite implementation changed. The manuscript builds without LaTeX
warnings at 307 pages, and all 64 existing proof blocks remain byte-identical.
Protocol, pilot, balanced census, corrections, audit, decision and raw/normalized
logs are retained in `experiments/results/cnf-b12-continuation-batch/`.
