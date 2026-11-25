# Transfer exact search histories across unchanged feedback banks

Checkpoint: 25 November 2026. Fresh B5 discovery refutes **five more events**;
all five native roots pass both independent readers. Sampled recognition reaches
**226/246**, leaving **20 unresolved**. All five formulas already had UNSAT
answers in the reference snapshot; this is broader certified structural
recognition, not five previously unknown truth values.

Sixteen B4/B5 bank-and-closure pairs are exactly unchanged. Transferring their
checked histories avoids **1,024 repeated assumptions** while exactly matching
a fresh search reaching the same frontier. It also discovers five failed probes
beyond the shorter restart's prefix. Measured discovery time improves 4.38%
against the matched frontier, but complete census time only 1.48%. Reconstruction
and provenance checking still dominate. All **1,987 tests** pass.

## Recognition, invalidation and proof contract

The [previous composition](b4-cursor-feedback.md) strengthened nine open B5
closures and left sixteen unchanged. Restarting all histories would discard
useful work on those sixteen; importing all histories would skip potentially
new failures on the nine changed banks. The candidate compares the full B4/B5
clause sequences, complete closure including trace order, and trace allowance.
Only exact matches permit migration. Source and all earlier layers have already
been checked, and the old cursor must pass its original input/policy binding,
schedule and every failed-proof check.

For an exact match, the residual bank and active variables are identical. Both
implemented policies use the same source occurrence order and complement-first
promotion rule. The cursor is copied into the new B5 format/binding, then its
schedule and failures are checked again under B5 before continuation. A changed
bank, closure trace or trace allowance starts fresh. A directly supplied old B4
cursor is rejected; later explicit B5 continuation must match its exact binding.
Interrupted attempts are never marked completed and are retried.

This transfers scheduling history, not a proof that open assumptions are
satisfiable. Claimed open entries are trusted in the same sense as earlier
cursors; forged history can lose coverage but supplies no logical axiom.
Every failed assumption remains a checked contradiction on its actual bank.
Opposite failed assumptions yield a refutation compiled through decreasing
dependencies B5 through B0. Support selection, bounded source-only direct unit
closure and existing native checks remain. No production default or cumulative
authority table changes.

## Matched search and complete costs

The 25 exposed cases run twice in reverse order under three policies:

* `restart`: start fresh and attempt up to 64 assumptions per case.
* `matched`: start fresh and attempt up to 128 on the sixteen exact matches,
  and 64 on the nine changed banks, reaching the reuse policy's frontier.
* `reuse`: import each eligible 64-assumption B4 prefix, then attempt up to 64
  additional assumptions; start fresh on changed banks.

The matched-control budgets are fixed from pilot-identified matches, independently
rechecked in the audit. All arms still pay preparation and exact comparison.
A 64-assumption pass permits 262,144 occurrence visits and 256 trace steps;
the 128 control doubles the occurrence allowance. Index construction, per-probe
initialization, full-content bindings and checks are additional. Historical
acquisition is already paid and excluded from current continuation costs.

| Summed per-target means | Restart | Matched frontier | Reuse |
| --- | ---: | ---: | ---: |
| Reconstruction (s) | 0.50506 | 0.50571 | 0.50169 |
| Discovery/preparation (s) | 0.19289 | 0.20070 | 0.19190 |
| Persistence/reload (s) | 0.00892 | 0.00802 | 0.00857 |
| Semantic cold checks (s) | 0.17703 | 0.17838 | 0.17704 |
| Complete census (s) | 0.88870 | 0.89750 | 0.88422 |
| Newly attempted assumptions | 1,305 | 2,323 | 1,299 |
| Per-probe initialization clauses | 490,232 | 870,272 | 488,768 |
| Propagation occurrence visits | 51,271 | 77,675 | 48,007 |
| Failed proofs retained | 34 | 39 | 39 |
| Standalone cursor/result bytes | 312,831 | 319,536 | 319,536 |

Reuse and the matched control produce identical programs and cursors on every
case, including all five refutations. Reuse saves exactly 1,024 probes and
381,504 initialization clause visits against that control. The smaller restart
finds the same five refutations but misses five later failures. One order ends
at 128 assumptions and another at 122, explaining why reuse attempts six fewer
new assumptions
than the shorter restart. Work and trace limits do not interrupt these trials.

The 1.48% complete-time difference is descriptive, not a general speed theorem.
Three cases regress in discovery time versus the matched control and thirteen
versus the shorter restart; all are retained. Search peak RSS is essentially
unchanged: 97,386,496 bytes for reuse and 97,452,032 for both controls. Against
the matched frontier, retained cursor size is identical. Against the shorter
restart, retaining the later history costs 2.14% more bytes. Reconstruction and
semantic checks together consume about 77% of the reuse census. Startup/loading,
prior acquisition, final audit and unrestricted fallback remain additional.

## Native results and retained open state

Twenty isolated positive trials compare fresh bounded solving with the measured
direct-unit native compiler on the five distinct gained roots:

| Summed per-root means | Fresh | Direct-unit compiler |
| --- | ---: | ---: |
| Solve/compile (s) | 1.12221 | 0.27215 |
| Warm check (s) | 0.00985 | 0.05845 |
| Both cold readers (s) | 1.12063 | 0.20022 |
| Persistence (s) | 0.39578 | 0.04499 |
| Complete local trial (s) | 2.67493 | 0.58810 |
| Encoded key/payload bytes | 5,239,018 | 653,817 |
| Native records | 421 | 187 |
| Maximum process RSS (bytes) | 73,990,144 | 53,821,440 |

All five improve in solve/compile time, complete time and bytes: aggregate
complete time falls 78.01% and bytes 87.52%. Warm provenance checking remains
more expensive. Both readers accept all ten unique archive/root pairs. Positive
comparisons exclude earlier acquisition/discovery and unresolved fallback;
isolated archives can duplicate records and do not establish a total workload
or lifetime memory bound.

The twenty remaining events retain **26 B5 failures in eight cases**. Five of
these failures occur only after importing the old prefix and reaching later
candidates. Twelve open cases have no new failure. Two exhaust the current
single-literal order; neither is certified SAT. The full open export is
1,175,494 bytes versus the previous 1,199,685 bytes for 25 cases: five closed
cases have been removed while later history is retained. This is not same-set
compression, and total history still grows because all older artifacts remain.

## Validation and next target

All 1,987 tests and 122 focused tests pass. Tests cover exact migration versus a
fresh extended frontier, changed-bank and trace-bound invalidation, cold
continuation, interruptions, malformed proof/history rejection before warm
lookup, selected/full support, independent readers, and exhaustive binary and
generated small formulas checked by complete truth tables. All 1,102 earlier
source fingerprints, 27,026 artifact entries in 194 parent manifests and 64
original manuscript proof blocks remain unchanged.

**Next coverage target:** compose the 26 checked B5 failures in those eight
remaining cases through a separately checked layer. The other twelve require
later candidates or stronger interaction, especially the two whose current
literal order is exhausted. Reuse needs an explicit equivalence check across
future layers; do not transfer a cursor merely because a family name matches.
Repeated source/provenance preparation remains the largest avoidable census
cost, and exact full-content bindings still duplicate state. No uniform
polynomial construction or compact lifetime bound for arbitrary CNF follows.

Resume `experiments/results/cnf-b5-probe-cursor/checkpoint.json`, especially
`b5_probe_cursor.remaining`. Reproduction uses `prepare`, `run_census`, `cases`
and `run_trials` in `compare_cnf_b5_probe_cursor.py`, then `validate` and, after
tests and manuscript checks, `seal` in `validate_cnf_b5_probe_cursor.py`, with
a fresh output directory containing the preserved pilot and source snapshot.
