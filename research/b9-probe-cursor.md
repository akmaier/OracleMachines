# B9 discovery: retain complementary failures from both banks

Checkpoint: 26 November 2026. The next search pass finds **eight B9 failed
assumptions across four cases**. Their complements and unit consequences force
14 additional assignments. Continuing B8 separately finds ten new failures,
including four absent from the B9 pass. Combining the two independently checked
histories forces **17 additional assignments** across those same four cases.
Neither closure produces a contradiction. Recognition stays **230/246**, with
16 open; there is no new native certificate.

This is evidence for keeping complementary bounded searches, rather than assuming
a stronger clause bank makes every older unfinished search redundant. A changed
bank changes the active literal order and the prefix of work reached under a cap.

## Search boundary and exact reuse

`experiments/cnf_b9_probe_cursor.py` validates the original B8 result through the
shared checker, retaining every source, template, binding, schedule and proof
check. It owns copies of the inputs, adds the complements of the checked B8
failures, and verifies a complete open unit closure of that B9 bank. B9 failures
are checked against B9; they cannot justify themselves through the next bank.

Fifteen cases have exactly the same B8 and B9 clause banks, closure assignments
and trace order, and trace allowance. Their source-derived schedules can be
imported after those comparisons and full retained-proof checking. The stronger
`(28,18)` bank fails this test and starts fresh. Binding includes the full source,
bank, closure, literal order, policy and trace allowance. A stale cursor, edited
source, altered closure, malformed proof or changed allowance cannot silently
reuse that history. No prepared authority token is accepted across calls.

Open completed probes remain scheduling information, not checked SAT evidence.
Skipping them assumes honestly generated history; every retained failed probe
is independently checked. Exhaustion never establishes SAT. The final audit also
reconstructs B9 with the frozen B8 feedback implementation and checks the new
program directly against that independently reconstructed bank.

## What the two frontiers discover

The table lists **failed assumptions**, whose complements are forced. Added
assignments count all unit consequences relative to the saved B9 closure.

| Case | New B9 failures | New B8 continuation failures | B9 added assignments | Combined added assignments |
| --- | --- | --- | ---: | ---: |
| `(1,15)` | `39` | `39` | 1 | 1 |
| `(28,18)` | `56,21` | `6,25,28,2` | 3 | 6 |
| `(37,39)` | `117` | `117` | 1 | 1 |
| `(40,0)` | `25,114,26,75` | `25,114,26,75` | 9 | 9 |

The older B8 failure `-62` at `(28,18)` is preserved and is already incorporated
in its B9 bank; it is not counted as a new failure. B9 has two new failures not
found by this B8 continuation; B8 has four not found by this B9 pass. Both routes
share the other six new failures. The combined closure therefore uses all twelve
distinct new failures, with their original bank proofs. Three extra assignments
at `(28,18)` are gained over the B9-only closure. Neither the stronger bank nor
these finite prefixes imply that either route subsumes the other computationally.

Eleven B9 orders are now exhausted. Five retain candidates:
`(1,15)`, `(28,18)`, `(37,39)`, `(40,0)`, `(67,63)`.
The newly exhausted case is `(61,61)`. The four strengthened closures above are
the next coverage targets, particularly the nine new assignments at `(40,0)` and
the complementary proof sets at `(28,18)`. Exhausted unchanged cases need stronger
interaction or a different decomposition, not another restart of the same order.

## Matched costs and the retained regression

Two isolated repetitions run in opposite order. All arms use the latest local
context reconstruction. The same source events and fixed limits are used:
64 additional probes, occurrence-work allowance 262,144 and trace allowance 256.
The matched fresh arm adds the imported completion count to its probe budget and
scales its work allowance. It reproduces every reuse result exactly on this
workload. The fixed-budget restart and B8 continuation are separate comparisons;
they explore different frontiers and are not matched controls.

| Measurement | Continue B8 | B9 restart | B9 matched fresh | B9 reuse |
| --- | ---: | ---: | ---: | ---: |
| Source reconstruction (s) | 0.19206 | 0.19123 | 0.18999 | 0.18809 |
| Discovery and checking prior history (s) | 0.16791 | 0.19730 | 0.20664 | 0.19067 |
| Independent cold checking (s) | 0.16170 | 0.18538 | 0.18556 | 0.18350 |
| Persistence/reload (s) | 0.00514 | 0.00582 | 0.00504 | 0.00575 |
| Complete census (s) | 0.53010 | 0.58312 | 0.59038 | 0.57111 |
| Fresh probe attempts | 312 | 1,024 | 2,522 | 324 |
| Serialized result bytes | 187,972 | 173,787 | 186,336 | 186,336 |
| Peak process RSS (bytes) | 98,746,368 | 99,024,896 | 98,828,288 | 98,795,520 |

Exact reuse avoids **2,198 probes**, cutting matched discovery time **7.73%** and
complete census time **3.26%**. Discovery improves on all sixteen case-level means.
Reconstruction/checking/persistence timing regressions are retained in
`analysis.json`; result bytes are identical to matched fresh. There is no material
memory reduction. B9 reuse still costs **7.74% more** than continuing B8 and finds
fewer new failures in this pass, although its two unique failures improve the
combined closure. Do not extrapolate saved probe count to total speedup.

Census time includes input ownership copies, recognition, reconstruction,
discovery, independent cold proof checking and serialization/reload. Startup and
input loading, historical acquisition, pilot work and the lineage audit are
additional. The diagnostic that independently checks both histories and computes
both complete closures takes **0.77961 s**, outside the census. Overlay writing,
binding checks and reload of its parent and results take **0.01216 s** separately.
These are finite measurements, not a universal timing guarantee. There is no
native compilation or unresolved fallback hidden in these totals.

## Storage and bounds

The resume frontier is a **10,429-byte overlay** referencing the unchanged
2,070,735-byte parent frontier and 32 result files (374,308 bytes). All 33 referenced
files total **2,445,043 bytes**; together with the overlay they occupy 2,455,472
bytes. A hypothetical fully expanded compact export would occupy 2,447,881 bytes.
Thus the references avoid writing another multi-megabyte duplicate when the
parent and results are already retained; they do not make the standalone
dependency set smaller. Both historical proof sets, trial repetitions and all
prior native archives remain. Total lifetime storage still grows.

Load with `compare_cnf_b9_probe_cursor.load_frontier(checkpoint['b9_probe_cursor']['remaining'])`.
It verifies the parent binding and rejects missing, duplicate or overwriting
rows. Each returned row preserves the old source fields and adds `b9_result` and
`b8_comparison_result` bindings plus `b9_feedback_closure` and `b9_joint_closure`.
Decode each result with `old.bound` and perform the normal semantic proof checks
before using it. A hash binding is an integrity check, not proof authority.

For a fixed bank on `n` source variables, this schedule completes at most `2n`
distinct literal probes. With trace limit `t`, its retained completed list and
failed-probe traces use `O(n + nt)` word slots, plus the full binding and existing
proof history. Integer and clause-index bit widths must be charged separately.
Copies, canonicalization, index construction, inherited proof checking and binding
serialization lie outside the occurrence-work cap. None of these bounds limits
the size or acquisition cost of all preceding banks, the number of future
expansions, or arbitrary-SAT solving time.

## Validation and next step

All **2,082 full tests** and **34 focused tests** pass. Seven new tests cover all
sixteen current inputs, matched-fresh equality, frozen bank reconstruction,
changed bank/allowance rejection, edited proofs/schedules/closures/sources,
ownership, interrupted and cold-reloaded continuation, and overlay integrity.
Truth-table checks enumerate all 256 subsets of signed unit/binary clauses on
two variables and 70 generated five-variable formulas. Unit contradictions are
checked directly; other inputs are unit-simplified before the open-frontier
helper constructs the applicable B9 histories. Already closed cases do not enter
B9. Every returned failure is compared with the models of its residual source.

The first test run exposed the older fixture helper's open-unit-closure
precondition. Its source, failed log and initial protocol remain; only the test
setup changed. The first audit tried to compare per-event complete time, which
is recorded only per worker. Its source and failed log remain; the corrected
audit compares the available per-event stages and worker complete totals. Neither
correction changes the discovery implementation, input selection or measured runs.

The audit preserves 1,150 previous source fingerprints, 29,475 artifact entries
in 205 manifests, all cumulative/reference/native bindings, and 64 original
manuscript proof blocks. The final source ledger has 1,154 entries. Existing
SQLite ResourceWarnings remain in the full test log; focused tests are clean.

Resume `experiments/results/cnf-b9-probe-cursor/checkpoint.json`. Prioritize checked
joint composition and probing of the four strengthened closures. Retain both
unfinished B8 and B9 histories. Reconstruction (32.93%), discovery (33.39%) and
cold checking (32.13%) now split the census cost almost equally; repeated boundary
checks remain a cost target, alongside the earlier low-yield-context regressions.
Native proof expansion, complete efficient classification and lifetime-space
bounds remain open.
