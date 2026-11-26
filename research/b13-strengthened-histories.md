# Extend checked histories within B13 before adding another bank layer

Checkpoint: 26 November 2026. Updating B13's two B12 inputs to their completed,
checked histories exposes **14 new failed assumptions** on the two changed cases.
At `(37,39)`, feedback forces 37=false and 61=true, reducing the residual from
**545 to 534 clauses**, **1,552 to 1,515 literals**, and **137 to 135 variables**.
At `(67,63)`, the twelve new failures jointly produce a **checked 34-step unit
refutation on the augmented bank**. This is retained as a candidate awaiting
source-only native reconstruction; native coverage remains **232/246** and all
fourteen frontier rows remain. No native certificate is published by this run.

## Reuse pattern and exact boundaries

The existing B13 schema already combines source-order B12 failures, untested-first
B12 failures and B11 continuation. It accepts longer checked B12 histories without
a new B14 layer. Replace only those two histories and the resulting complete
closure. Every extended history is checked on its original B12 bank, including its
binding, schedule, failed proofs and program agreement; B11 remains separate.
The frozen B13 constructor rebuilds the augmented clauses and original provenance.
An independent reconstruction from lower routines checks the result.

This changes the physical bank only on `(37,39)` and `(67,63)`: **601 → 602** and
**437 → 440** clauses respectively before restriction. The other twelve banks and
provenance tuples are exactly unchanged, and their existing exhausted B13 results
remain valid under the extended histories. They are preserved without another
search. This is not a general recognizer that accepts extensions without checking.

Saved old-bank cursors are invalid on the changed banks and are rejected. Search
starts again on the strengthened banks, while the old cursors remain available
for comparison and future reuse. New failed assumptions and older histories are
never treated as proofs on a different bank without their original-bank checks.
Open completions retain the earlier honest-production assumption; exhaustion
neither proves SAT nor rules out stronger interaction on another bank.

The complete old-bank continuation finds 32 at `(37,39)` and -119, -116, 131 at
`(67,63)`, all already present in the latest B12-derived knowledge. Strengthened
B13 finds -61 and 37 at the first case; at the second it finds -130, -123, -112,
-88, -9, 45, 50, 79, 100, 107, 110 and 133. These variables were not fixed by the
initial strengthened closure. Applying their negated unit conclusions yields the
reported additional closure or contradiction, with all original proofs retained.

## Exploration, matched costs and regressions

The pilot tried 64 and 320 additional probes. At 64, old continuation finds no
failure at `(37,39)` and two already-known failures at `(67,63)`; strengthening
finds no failure at the first and four new failures at the second. The declared
timing comparison uses **320 additional probes**, at most **1,310,720 occurrence
work**, and trace bound **256**, to finish these schedules. It is exploratory,
selected-case evidence, not a held-out test or a 64-probe comparison.

All six mode permutations run in separate processes before heavy checks. Each arm
reconstructs the same two sources, prepares its context, searches, serializes and
reloads its result, and independently cold-checks it. `continue` resumes old B13;
`fresh` restarts that same old bank; `strengthen` starts the updated bank. The two
old-bank results match exactly when complete. Acquisition, startup/loading, pilot,
feedback composition, native compilation and lineage audits are additional.

| Mode | Reconstruction (s) | Discovery (s) | Checking (s) | Persistence (s) | Complete census (s) | Probes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| old continuation | 0.02579 | 0.04384 | 0.04097 | 0.00188 | 0.11556 | 356 |
| old fresh | 0.02519 | 0.04486 | 0.04032 | 0.00090 | 0.11355 | 548 |
| strengthened | 0.02526 | 0.04675 | 0.04324 | 0.00136 | 0.12060 | 536 |

Strengthening costs **4.37% more** than old continuation and **6.21% more** than
old fresh search, while supplying the new implications and augmented conflict.
Continuation avoids **192 probes**, improving discovery **2.27%**, but is **1.77%
slower overall** in these measurements. Its persistence time is noisy and higher;
we do not claim an end-to-end speedup from avoided probes alone.

Occurrence visits are 11,905 / 18,352 / 19,496 in the three arms. Each prepares
once per case. Strengthened results occupy **44,108 bytes**, compared with
**34,206 bytes** for either old-bank arm, a **28.95% increase**. Peak RSS remains
about 100 MB (99,614,720 / 99,745,792 / 99,631,104 bytes); no memory saving is
established. Feedback separately costs about 1.32 ms and 0.45 ms in the audit,
which overlaps tests and is not an isolated production timing.

## Certification boundary and next step

The independent checker accepts the source-derived B13 history proofs and the
34-step final contradiction on their augmented bank. The native archives still
require a source-only proof graph, with every derived-unit origin recursively
reconstructed. No new native root is counted until that graph is published and
checked by both cold readers. The full candidate is persisted, not discarded or
misreported as an open complete closure. This distinction is why the native
coverage number does not increase yet.

**Highest-priority next step:** reconstruct `(67,63)`'s candidate through native
source-only certificates, preserving the original prefix and comparing all
conversion/checking/storage costs with bounded fresh solving. The B10 feedback
compiler is a useful starting point, but the newer origin kinds must be mapped
and validated explicitly: B10 comparison (bank 10, input 23), B11 (bank 11,
input 22), B12 source/unseen (bank 12, inputs 24/25), B11 continuation (bank 11,
input 26), and B13 failures (bank 13, appended full result). Final feedback uses
bank 14. Every recursive proof edge must decrease the bank stage. Do not merely
relabel a B10 certificate or skip original-bank premise checks.

After that, examine `(37,39)`'s two new values and the twelve unchanged exhausted
cases for stronger interactions or another decomposition. The present result
reuses a fixed preparation/provenance schema, but neither bounds the number of
necessary rounds nor produces an efficient partition of arbitrary CNFs. Input
history, proof-check and persistence costs remain explicit.

## Preservation and validation

Resume `experiments/results/cnf-b13-strengthened-histories/checkpoint.json`, key
`b13_strengthened_histories.remaining`, using the corresponding comparison
module's `load_frontier`. Each row keeps its earlier fields. New fields preserve
both changed-bank results, old continuations, the exact context closure and
feedback proof; `(67,63)` is tagged `candidate_refutation_pending_native`.
The **6,871-byte** overlay references **4,601,978 bytes across 219 transitive
files**. Earlier native archives and the new experiment evidence are additional.

The audit preserves **1,187 source fingerprints** and **32,515 artifact entries
in 214 manifests**. Three new scientific source files bring this ledger to 1,190.
Reference and cumulative tables and all native archive bindings are unchanged.
The separate authorized alphaXiv publication has its own preserved PDF/metadata
and publication registry; its first version covers verified checkpoint 918fc95a.
The daily updater can publish this later verified research as a revision.

An initial test incorrectly assumed both feedback closures remained open. Its
failure revealed the augmented contradiction. The initial test, protocol and
failed focused/full runs are retained. Only the test expectation changed; the
timed driver, pilot and census results are unchanged. The corrected test validates
the refutation and rejects a corrupted conflict index instead of treating it as
an open closure. All **2,161 tests** and **25 focused tests** pass; prior proof
blocks remain byte-identical. No external alphaXiv claim is used as a premise.
