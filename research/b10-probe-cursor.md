# Joint B10 probing closes two more retained cases

Checkpoint: 26 November 2026. Combining the checked B8 continuation and B9
failures, then probing the resulting B10 bank, produces source-only native
refutations for **`(28,18)` and `(40,0)`**. Both independent cold readers accept
the certificates. Sampled structural recognition rises from **230/246 to
232/246**, leaving **14 open**. The reference snapshot already knew these roots
were UNSAT; the gain is this structural route's certified coverage.

Continuing B9 alone also refutes `(40,0)` through feedback within the measured
allowance. B10 additionally closes `(28,18)`, which B9 continuation leaves open.
The result does not attribute both gains uniquely to the combined bank.

## Composition, recognition and proof authority

The new preparation owns copies of all inputs and independently validates the
original B8 history, its newer continuation and the B9 search result. It checks
that the comparison reconstructs exactly the original B8 clauses and provenance.
It then adds complements of failed assumptions from both histories, retaining
each reason's original bank: B8 comparison at bank 8, B9 at bank 9. Duplicate
clauses retain the earlier valid origin. The complete B10 unit closure is checked.

Four banks change: `(1,15)`, `(28,18)`, `(37,39)` and `(40,0)`. They start fresh.
Twelve others have identical B9/B10 clauses, complete closure traces and trace
allowances, so their source-derived probe schedules can be imported exactly.
Bindings contain the full source, bank, closure, order, policy and trace bound.
Stale formats, changed sources or allowances, altered schedules and invalid
reasons are rejected. Claimed open completions remain scheduling information,
not SAT certificates; semantic trust is never derived from an open cursor.

The independent audit reconstructs the earlier banks with the frozen B8 feedback
implementation, checks each original-bank program, constructs B10 again, and
compares all clauses and origins. Each new failure proof is also checked directly
on that bank. B11 feedback adds its complement and checks the final unit trace.
The native compiler recursively follows each derived reason to a strictly lower
bank. Its leaves discharge original source clauses or checked conditional source
supports. Only the existing empty, unit and split proof rules are published.
There is no new native axiom or rule. Even warm cache hits follow portable checks.

## New failures and the remaining frontier

B10 finds 17 failed assumptions:

| Case | Failed assumptions | Outcome |
| --- | --- | --- |
| `(28,18)` | `31,-49,-45,-40,5,11,63,-18,-12,35,38,-17,46` | Their complements compose to a unit contradiction |
| `(40,0)` | `32,-32` | Both branches refute; feedback also exposes a contradiction |
| `(37,39)` | `-112` | Forces variable 112 true; remains open |
| `(67,63)` | `66` | Forces variable 66 false; remains open |

The first two gained roots are removed from the new resume view, with their full
histories and native archives retained. Eleven remaining B10 orders are exhausted.
Three are unfinished: `(1,15)`, `(37,39)`, `(67,63)`. The latter two now have stronger
closures and are the next coverage targets. Unchanged exhausted cases need
stronger interaction, a different decomposition or a broader proof method.
Exhaustion is not a SAT answer.

The B9 comparison retains seven failures at `(28,18)` but no contradiction, and
five at `(40,0)` whose composition already refutes. It also reaches failure `66`
at `(67,63)`. Both B9 and B10 result files remain available, including unresolved
comparisons; no historical frontier is overwritten.

## Search cost: more coverage, more preparation

Two isolated repetitions run in opposite order with 64 additional probes,
occurrence-work allowance 262,144 and trace limit 256. Matched fresh adds the
number of reusable completions and scales its work allowance, reproducing every
reuse result exactly on this workload. Fixed-budget restart and B9 continuation
are separate coverage/cost comparisons, not matched controls.

| Measurement | Continue B9 | B10 restart | B10 matched fresh | B10 reuse |
| --- | ---: | ---: | ---: | ---: |
| Reconstruction (s) | 0.19616 | 0.20093 | 0.20379 | 0.20037 |
| Discovery, including preparation (s) | 0.19862 | 0.41381 | 0.42399 | 0.40479 |
| Independent cold checking (s) | 0.19261 | 0.40135 | 0.39560 | 0.39172 |
| Persistence/reload (s) | 0.00495 | 0.01189 | 0.00633 | 0.00636 |
| Complete census (s) | 0.60177 | 1.03683 | 1.04037 | 1.01102 |
| Fresh probe attempts | 296 | 962 | 2,204 | 258 |
| Serialized result bytes | 192,741 | 184,441 | 189,782 | 189,782 |

Exact reuse avoids **1,946 probes**, but reduces matched complete time only
**2.82%** and discovery time **4.53%**. Discovery improves on fourteen case-level
means and regresses on two. All other stage regressions remain in the analysis.
B10 reuse costs **68.01% more** than continuing B9, for one additional refuted
case. Peak process RSS remains about 100 MB; no memory reduction is established.
Reconstruction is 19.82%, discovery 40.04% and cold checking 38.74% of total time.
The added history validation, including repeated B8 preparation, is the dominant
avoidable cost. Share it under exact checks before adding more duplicate layers.

The census charges ownership, recognition, reconstruction, discovery, independent
checking and result persistence. Startup/loading, acquisition, pilots, native
compilation and lineage auditing remain additional. Checked B11 feedback across
all sixteen cases costs **0.81705 s** separately; the B9 comparison feedback check
costs **0.23888 s**. Complete remaining closures cost **0.00882 s** and overlay
publication/reload **0.02013 s** separately. These finite trials do not establish
a universal improvement or a total acquisition advantage.

## Native certificates: a gain and a preserved regression

The two gained source roots are tested in two opposite-order repetitions with
fresh solving, full dependency reconstruction without shortcuts, and the existing
bounded direct-unit shortcut. Native totals include construction, warm checking,
both independent cold readers and persistence. Discovery and historical
acquisition are additional. The direct gate/index/occurrence allowance is globally
262,144 within each compilation and its trace allowance is 256; preparation and
recursive fallback are not bounded by that counter.

| Case and mode | Verdict | Complete time (s) | Records | Record bytes |
| --- | --- | ---: | ---: | ---: |
| `(28,18)` fresh | UNSAT | 0.20314 | 56 | 345,767 |
| `(28,18)` shortcuts disabled | UNSAT | 5.62605 | 1,498 | 7,568,829 |
| `(28,18)` direct | UNSAT | 0.39648 | 91 | 635,391 |
| `(40,0)` fresh, 256-node cap | Unresolved | 3.06636 | 364 | 5,326,109 |
| `(40,0)` shortcuts disabled | UNSAT | 7.19207 | 791 | 9,804,482 |
| `(40,0)` direct | UNSAT | 0.45873 | 29 | 520,461 |

At `(28,18)`, direct reconstruction is **95.17% slower** and stores **83.76% more
bytes** than successful fresh solving. Fresh uses one binary-equivalence record
and 55 residual records; direct uses 91 residual records. Equivalence reuse and
smaller source supports remain native cost opportunities. Warm proof validation
also costs more than ordinary warm lookup.

At `(40,0)`, the new certificate completes where the fresh baseline stops at its
256-node cap. Its lower elapsed time and stored bytes are compared with that
**unfinished bounded attempt**, not a completed fresh solution. The partial
fresh records are preserved and audited; no warm terminal lookup is possible.
Do not report a completed-solve speedup from these numbers. Pooled native peak
RSS is 62,193,664 bytes direct, 170,557,440 disabled and 121,470,976 fresh; these
finite mode peaks are not general memory bounds.

The initial native harness wrongly required every fresh trial to finish UNSAT.
It stopped on this legitimate bounded result. The exact initial source, protocol
and reproduced failure log remain. The correction records unresolved outcomes,
audits their partial records and skips warm terminal lookup. Completed earlier
trials are preserved; census code and measured search inputs are unchanged.

## Persistence, bounds and verification

The new resume overlay is **7,077 bytes**. Its transitive frontier dependencies
occupy **2,768,222 bytes in 62 files**, plus the overlay itself. The parent overlay
retains histories for the gained cases too. A hypothetical fully expanded compact
export of the fourteen remaining rows is 2,406,299 bytes. References avoid a new
duplicate export when dependencies are already retained; they do not reduce the
standalone dependency set. Native archives and diagnostic trials are additional.
The twelve native trial archives occupy 5,881,810 compressed bytes and represent
six distinct archive/root audit combinations. Lifetime storage continues growing.

Resume `experiments/results/cnf-b10-probe-cursor/checkpoint.json`, using
`compare_cnf_b10_probe_cursor.load_frontier(checkpoint['b10_probe_cursor']['remaining'])`.
It checks the parent bindings and excluded/remaining key sets. New fields are
`b10_result`, `b9_continuation_result` and `b10_feedback_closure`; result bindings
must be decoded and semantically checked before reuse. All original fields and
earlier histories remain. A hash or cursor is not proof authority.

The fixed-bank literal schedule completes at most twice the source-variable
count. A trace bound limits each retained probe trace, not the number or size of
all inherited histories. Copying, index construction, canonicalization and
checking precede or lie outside the probe occurrence cap. Native dependency
expansion strictly descends the finite bank list but can duplicate contexts; this
termination argument is not a polynomial bound. Complete efficient arbitrary-SAT
recognition, uniformly cheap construction and bounded lifetime storage remain open.

All **2,091 full tests** and **43 focused tests** pass. Nine new tests cover exact
reuse, original-bank provenance, malformed histories and bindings, changed
closures/trace bounds, cold and interrupted continuation, ownership, both gained
native roots, disabled shortcuts, both cold readers, warm rejection before lookup,
unresolved publication rejection and overlay corruption. Exhaustive signed
unit/binary formulas on two variables and seventy generated five-variable inputs
are unit-simplified before applicable open histories are constructed; all returned
failures/refutations are checked against exhaustive models.

The audit preserves **1,154 prior source fingerprints**, **29,728 artifact entries
in 206 manifests**, all old cumulative/reference/native bindings, and **64 original
manuscript proof blocks**. The final source ledger has 1,159 entries. Six new
archive/root combinations pass both independent readers. Existing SQLite
ResourceWarnings remain in the full suite; focused tests are clean. The separate
[daily external review](pequalnp-watch.md) adds a possible adversarial parity
benchmark; no external theorem or proof code was imported into this checkpoint.
