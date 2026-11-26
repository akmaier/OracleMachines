# Joint B13 expansion versus continuation of both B12 orders

Checkpoint: 26 November 2026. Continuing the saved B12 source order discovers
failed assumptions **-119 and -116** at `(67,63)`. Their checked consequences
force local variables **119=true and 116=true**. The combined closure reduces
that residual from **358 to 347 clauses**, **1,025 to 986 literals**, and **136 to
134 variables**. No case closes: coverage remains **232/246**, with **14 open**.

The new B13 bank combines both earlier B12 proof sets and the retained B11
continuation. Under the same additional 64-probe allowance, B13 finds no new
failure. Continuing the B12 untested-first order finds -68, already supplied by
the earlier source-order result. This is a retained negative result for immediate
source-order expansion from the stronger bank, and evidence for preserving useful
unfinished schedules. It is not a universal superiority claim for continuation. The two new failures
occur at zero-based positions 103 and 105 of the continued source schedule;
neither is reached in B13's fresh 64-probe prefix.

## Checked composition and reuse

One privately owned copy contains 27 inputs, six closures, and any supplied
cursor or result. The common B12 prefix is reconstructed once using the previous
sharing implementation. Source-order B12, untested-first B12 and B11 continuation
each receive an independent original-bank program, schedule, binding and proof
check. Different trace bounds and ordering policies retain distinct bindings.

The two B12 orders share a bank but can have different schedules. The B11 history
is checked on its earlier bank. Their failed-assumption units are inserted in
source/unseen/B11 order, preserving the first origin of duplicate clauses. The
complete combined closure is checked before searching B13. No trusted prepared
object is accepted from another call. Cold checking repeats ownership and
preparation independently. The final audit reconstructs the bank and provenance
from frozen lower-bank routines rather than trusting B13's preparation function.

Only one bank changes, `(67,63)`. Thirteen unchanged cases import the checked
B12 **source-order** cursor only when clauses, the entire closure trace and trace
bound agree exactly. B13 uses the same deterministic source order on these banks.
No untested-first history is silently relabelled as source order. A changed bank
starts fresh. Open completions remain scheduling hints, not SAT certificates or
proof of semantic exhaustion.

Exact reuse avoids **2,074 probe attempts** and **51,384 occurrence visits**
compared with matched fresh reconstruction. Reuse and matched results agree
exactly. The repeated fresh arm is given the old completion allowance in addition
to the 64 new probes; it tests the cost of replacing reuse, not an equal-work
search competitor. Both B12 continuations receive the same additional 64-probe
budget as B13 reuse. Combining discoveries charges both budgets.

The `(1,15)` order completes its final 52 probes without a failure. Twelve orders
are now exhausted; `(37,39)` and `(67,63)` remain unfinished. Exhaustion is an
operational fact about this bounded single-assumption procedure, never a SAT
answer. All earlier schedules and both complementary B12 proof histories remain.

## Measurements and timing uncertainty

The initial two opposite-order censuses show large variation in unchanged source
reconstruction, from 0.26070 seconds in B13 reuse to 0.37821 seconds in B12 source
continuation. Complete times are 0.92733 and 1.31383 seconds respectively. These
numbers alone do not establish a runtime advantage for B13. All initial reports
are retained, including their apparent 29.42% reduction and case regressions.

A follow-up with four balanced rotating mode orders was declared after observing
this variation and before measurement. It runs after the full and focused tests,
uses identical inputs, policies and allowances, and retains the initial trial.
The recorded follow-up analysis determines the timing conclusion below.

Unchanged reconstruction is now stable across modes (0.16473–0.16580 s).
B13 reuse is **7.91% slower than source continuation** and **8.67% slower than
untested-first continuation**, while finding no new failure. The earlier apparent
runtime win does not survive this follow-up. Exact reuse is a separate saving:
B13 reuse is **1.86% faster** than matched fresh B13, with identical results.

| Follow-up mode | Reconstruction (s) | Discovery (s) | Cold checking (s) | Persistence (s) | Complete census (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| source | 0.16473 | 0.18733 | 0.18146 | 0.00430 | 0.55471 |
| unseen | 0.16580 | 0.18845 | 0.18191 | 0.00412 | 0.55081 |
| reuse | 0.16578 | 0.21141 | 0.20485 | 0.00476 | 0.59857 |
| matched | 0.16558 | 0.22491 | 0.20372 | 0.00448 | 0.60993 |

This ranks continued source-order probing ahead of immediate B13 expansion on
the measured cases, without proving a universal ranking. B13 discovery plus cold
checking consumes **69.54%** of its measured time; source reconstruction is
**27.70%**. The additional original-bank histories cost work even though common
preparation is shared once. Probe savings alone do not predict total savings.

B13 results use **153,906 bytes**, versus **156,526 / 155,608 bytes** for continued
source / untested-first. These are different search histories, not compression
of the same proof set. Peak RSS is **98,631,680 / 98,680,832 / 98,680,832 /
98,680,832 bytes** for source / unseen / reuse / matched. No material peak-memory
improvement is established. Per-case regressions and both timing runs are retained.
The follow-up has 9 cold-checking case regressions versus matched fresh B13,
despite its small total-time saving.


The census charges reconstruction, ownership, preparation, recognition, search,
serialization/reload and cold checking. Startup/input loading, historical
acquisition, pilots, native compilation and final lineage auditing are additional.
The first diagnostic audit overlapped tests; the final audit is also separate from
the census and must not be interpreted as production compilation cost.

## Remaining gaps and next target

The useful discovery in this run comes from continuing the old source schedule.
Prioritize the two unfinished cases and the newly simplified `(67,63)` residual;
compare further continuation against any changed-bank schedule before adding
another feedback layer. Retain B13 and its negative outcome for comparison.
Twelve exhausted unchanged cases need stronger interactions, such as bounded
joint assumptions or a different decomposition, rather than an identical rerun.

The common lower history is prepared once per call, but original-bank proof
checking, canonicalization and source reconstruction remain real costs outside
the occurrence budget. This experiment does not improve native compilation,
prove compact closure, establish an efficient partition of arbitrary CNF, or
bound oracle acquisition uniformly by a polynomial. Previous native regressions
remain open. No new native certificate or production default is introduced.

## Preservation and validation

Resume `experiments/results/cnf-b13-probe-cursor/checkpoint.json`, field
`b13_probe_cursor.remaining`, with
`compare_cnf_b13_probe_cursor.load_frontier`. Its **11,733-byte** overlay references
**4,039,897 bytes across 177 transitive frontier files**. Prior native archives and
other evidence are additional. The overlay avoids a flattened duplicate export;
new experiment diagnostics still increase lifetime storage.

All **1,175 prior source fingerprints** and **30,962 artifact entries in 211
manifests** are preserved. Four new source files bring the ledger to 1,179.
Reference/cumulative tables and native archive bindings remain unchanged.

Nine new tests check independent composition, exact import conditions, policy and
trace-bound isolation, every old history/closure, corrupted proofs and results,
owned cold/interrupted continuations, alternative complete closure traces,
overlay integrity, and small-model correctness. The latter enumerates all 256
subsets of eight signed unit/binary clauses on two variables and seventy generated
five-variable formulas, unit-simplifies them, and checks applicable open histories
against exhaustive models. This is bounded testing, not general SAT coverage.

All **2,136 tests** and **36 focused tests** pass. The full suite reports
44 SQLite resource warnings (44 in the parent run); the focused suite has
0. No SQLite implementation changed. The manuscript builds without LaTeX
warnings, and all 64 existing proof blocks remain byte-identical. Protocol,
pilots, both censuses, audits, decision and raw/normalized logs are retained in
`experiments/results/cnf-b13-probe-cursor/`.

One audit-harness failure is preserved in `failed-followup-audit.log`: it tried to
parse the bound Python benchmark runner as JSON. The corrected audit checks its
SHA-256 directly; the search code and both censuses are unchanged.
