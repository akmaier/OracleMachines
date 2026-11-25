# Advance B6 discovery while retaining exact search history

Checkpoint: 25 November 2026. Fresh probing of the strengthened B6 closure
refutes `(37,0)`. Its source-only native certificate passes both independent
readers, reaching **228/246 sampled structural recognition**, with **18 open**.
The reference snapshot already knew this formula was UNSAT; the gain is a new
certified structural route, not a previously unknown truth value.

Twelve unchanged B5/B6 banks admit exact history transfer. It avoids **1,472
repeated assumptions** and **615,872 initialization clause visits**, producing
exactly the same programs and cursors as fresh extended search. Seven later
failed assumptions would be missed by a short restart. Complete census time,
however, improves only **0.11%** in this sample: no material total-runtime win
is demonstrated. The retained open export grows **9.03%**, despite one fewer case.

## Recognition and reuse contract

The previous composition strengthened seven closures; these start with fresh
B6 bindings. The other twelve permit import only when the full ordered B5/B6
banks, complete closure including trace order, and trace allowance are equal.
Preparation checks the original source, guards, all earlier layers and cursor
histories first. The imported cursor is rebound to the B6 policy and checked
again, including its deterministic schedule and every failed-assumption proof.
Changing the bank, closure or allowance disables migration. Explicit continuation
requires the new binding. Interrupted assumptions remain uncompleted and retry.

Identical banks and closures give identical active variables and residuals.
The implemented policies use the same source occurrence order and complement-first
promotion rule. Thus a validated completed prefix can be resumed without
repeating those assumptions. Claimed open history remains trusted scheduling
data, not a SAT or exhaustion proof; incorrect open claims can lose coverage
but cannot supply a proof axiom. Opposite failed assumptions yield a checked
refutation. Native reconstruction expands their used dependencies through B6
to B0, with support slicing, coordinate checks and bounded source-only direct
unit closure. All validation precedes warm lookup.

## Matched experiment

The nineteen exposed cases run twice in opposite order under three policies:

* `restart` attempts up to 64 assumptions from scratch.
* `matched` starts fresh with 64 plus the saved prefix length on the twelve
  exact matches, and 64 otherwise. Eleven matched budgets are 192; one is 128.
* `reuse` imports eligible history and attempts up to 64 additional assumptions;
  changed banks start fresh. Candidate exhaustion may finish earlier.

Each 64-attempt chunk has 262,144 occurrence visits and 256 trace steps,
including the closure prefix. The matched arm scales its occurrence allowance
by the number of chunks. Budgets are fixed from exposed pilot matches and
independently audited, not hidden free recognition. Index construction,
initialization and provenance checks are additional to occurrence limits.
Historical acquisition is already paid and excluded from continuation costs.

| Summed per-target means | Restart | Matched frontier | Reuse |
| --- | ---: | ---: | ---: |
| Reconstruction (s) | 0.40673 | 0.39863 | 0.40265 |
| Discovery/preparation (s) | 0.15977 | 0.16706 | 0.15807 |
| Persistence/reload (s) | 0.00503 | 0.00531 | 0.00720 |
| Semantic cold checks (s) | 0.14584 | 0.14542 | 0.14684 |
| Complete census (s) | 0.72183 | 0.72048 | 0.71970 |
| Newly attempted assumptions | 1,171 | 2,361 | 889 |
| Initialization clauses | 438,109 | 967,841 | 351,969 |
| Occurrence visits | 37,401 | 68,973 | 28,401 |
| Failed proofs retained | 6 | 13 | 13 |
| Standalone cursor/result bytes | 218,330 | 226,105 | 226,105 |

Matched and reuse produce identical results on every case. Both find thirteen
failures, including four on the gained refutation and nine in six remaining
cases. The shorter restart finds the same refutation but misses seven later
failures. Six histories exhaust their current literal order, explaining why
reuse makes fewer than nineteen times 64 new attempts. No work/trace limit
interrupts these runs.

Reuse reduces discovery/preparation time 5.38% against matched search, but the
complete-time difference is negligible. Reconstruction and semantic checking
consume **76.35%** of reuse time. Six cases regress in discovery versus matched
and five versus short restart; all reports and regressions are retained. Peak
process RSS is 97,681,408 bytes for reuse versus 97,665,024 matched: it does not
improve. Standalone cursor bytes equal matched search and exceed short restart
by 3.56%. Startup/loading, earlier acquisition and final audit remain additional.

## Native certification and memory

Four isolated trials compare fresh bounded solving and direct-unit compilation
on the one gained root, including warm checks, both cold readers and persistence:

| Per-root means | Fresh | Direct-unit compiler |
| --- | ---: | ---: |
| Solve/compile (s) | 0.51079 | 0.06891 |
| Warm check (s) | 0.00273 | 0.01978 |
| Both cold readers (s) | 0.52277 | 0.04111 |
| Persistence (s) | 0.21480 | 0.01092 |
| Complete local trial (s) | 1.25723 | 0.14327 |
| Encoded key/payload bytes | 2,521,305 | 146,110 |
| Native records | 141 | 35 |
| Maximum process RSS (bytes) | 89,194,496 | 52,641,792 |

Complete positive-trial time falls 88.60% and bytes 94.20%. Warm provenance
checking remains more expensive. Both unique archive/root pairs pass independent
restoration and checking. Acquisition, discovery and unresolved fallback are
excluded from these positive-only figures; isolated archives can duplicate state.

The full open-state export is **1,259,314 bytes for 18 cases**, up from
1,155,036 for nineteen. It retains all previous fields plus the new B6 histories.
Exact full-content bindings and proof histories still duplicate data; all older
artifacts also remain. Neither the smaller native certificate nor avoided probes
establishes a compact lifetime storage bound. At most two signed literals per
active variable occur in this policy's candidate order, but more feedback layers,
stronger interactions, provenance checking and native context expansion remain
outside that finite per-order bound. General SAT is still unresolved.

## Remaining cases, validation and next target

Nine checked failures remain in six cases: `(1,15)` has one, `(28,18)` one,
`(28,19)` one, `(37,39)` two, `(37,40)` three, and `(40,0)` one. **Next compose
these consequences** through a separately checked layer. Seven of the nine
occur beyond the short restart's frontier, showing why unchanged structures
must not simply be skipped.

Twelve other cases have no new failure. Six exhaust their present order:
`(28,17)` at 128 assumptions, `(61,0)` at 152, `(61,21)` at 146, `(61,50)` at 152,
`(61,51)` at 150, and `(61,74)` at 142. They are unresolved, not certified SAT.
If feedback leaves them unchanged, repeating the order cannot help; investigate
stronger bounded interactions with exact recomposition. In parallel priorities,
immutable checked preparation reuse and shared provenance address the largest
measured runtime and retained-space gaps. Neither is implemented by this pass.

All **2,005 full tests** and **140 focused tests** pass. Tests cover exact import
versus fresh extended search, changed-bank/trace-bound invalidation, cold split
continuation, interruption retry, malformed provenance before warm lookup,
selected/full support, independent readers, exhaustive binary inputs and
random small inputs checked against complete truth tables. All 1,111 prior
sources, 27,449 artifact entries in 196 parent manifests, and 64 manuscript proof
blocks remain unchanged. Cumulative authority tables and production defaults
are unchanged; new native archives are supplemental.

Resume `experiments/results/cnf-b6-probe-cursor/checkpoint.json`, especially
`b6_probe_cursor.remaining`. Reproduce with `prepare`, `run_census`, `cases`,
and `run_trials` in `compare_cnf_b6_probe_cursor.py`, then `validate` and, after
tests/manuscript checks, `seal` in `validate_cnf_b6_probe_cursor.py`, using a
fresh output directory with the preserved pilot and source snapshot.
