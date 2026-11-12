# Residual archive accounting

The optional `AccountedResidualSolver` preserves the existing search, certificate
checker and stored residual rows. Its superclass remains the census control.
The change targets the full `count/sum(length(...))` performed after every query,
including cache hits. This is metadata work, not a new SAT algorithm.

One private SQLite row holds the residual count, the historical SQL payload-length
total and a dirty flag. Five triggers maintain it in the same transaction as
ordinary insertions, updates and deletions. Other connections and the old solver
also fire these triggers. Writes to unrelated pattern tables do not invalidate
the totals. Every open independently reconstructs the counters under a write
lock; old residuals are never rewritten. An unchanged cold open leaves the
archive bytes unchanged after this one census.

SQLite replacement can delete a conflicting row without firing delete triggers
when recursive triggers are disabled, as specified in SQLite's
[conflict-resolution documentation](https://www.sqlite.org/lang_conflict.html).
Before a possible key or rowid conflict,
we therefore mark the totals dirty. The next metadata read reconstructs them
under a write lock. Ignored duplicates and upserts can cause conservative extra
censuses. Rollbacks restore both data and counters, including reconstruction in
a caller-owned transaction. Direct modification of the private accounting schema
during an open connection is outside the contract. Counters do not certify SAT
answers; the original proof checker still does that.

The invariant is conditional on `dirty=0`: the singleton equals the count and
length sum of the residual table in the same database snapshot. It holds after
the opening census. A non-conflicting insertion adds one row and its length;
deletion subtracts them; update changes only the length contribution. A possible
replacement invalidates the invariant's premise before the write. Reconstruction
restores it while holding the write lock. SQLite commits and rollbacks treat the
data and trigger updates together. A metadata read therefore returns either a
clean snapshot or a reconstructed one. This argument concerns accounting; it
adds no SAT-solving or Python-to-Lean refinement theorem.

Let B be the residual key/payload length and R the number of residuals. Opening
costs O(B+R); a clean metadata read accesses one row. An ordinary insertion adds
one indexed conflict check and length accounting for its key/payload, plus a
constant number of metadata updates in the existing transaction. Logical retained
accounting state is one row and five fixed trigger definitions. Conflicting
writes can still incur O(B+R) reconstruction at the next read. Disk-page overhead,
commit latency, initial scanning, locking and cold verification remain charged.
The old `archive_payload_bytes` field retains SQLite TEXT length semantics;
generated JSON is ASCII, but arbitrary Unicode or NUL-containing SQL values must
not be described as UTF-8 byte counts.

Only metadata retrieval has a constant-size state access. Reading a new input,
checking a source witness, constructing keys and cold proof replay retain their
own costs. Failed discovery and fresh search remain possible. This distinction
matters when interpreting a large warm-query speedup on a prepared archive.

Initial validation: 476 Python tests pass, including exhaustive two-variable
answer/proof/metadata equivalence, independent legacy writers, rollbacks,
replacement under both recursive-trigger modes, cold preservation and resource
budget failure. A first budget-test fixture unexpectedly reused two identical
canonical children; disabling reuse for that test exercises partial persistence.
The solver remains optional. Structural coverage and unrestricted-SAT obligations
are unchanged.

The comparison runner is `experiments/compare_cnf_accounting.py`, with `--suite`
set to `full`, `fresh` or `empty` and a new `--output` directory. `--reverse`
reverses the execution order. Both modes use the same retained-plan discovery
policy and cloned seed. Every query must have the same source-bound plan,
profile, summary, ordinary decision, search counters and exact archive totals.
All three evidence tables must have identical sorted key/payload digests.
Opening, archive restoration/cloning, compression, row-preservation checks,
cold audit and small-prefix Python allocation are reported separately. Warm
combined replay includes both discovery and the ordinary solver; earlier
discovery-only warm measurements are not its comparator. Complete acquisition
checkpoints are saved before the longer cold audit.

## Matched measurements

The [1,497-query prepared comparison](../experiments/results/cnf-accounting-full/README.md)
uses the same 417,370,112-byte seed and retained-plan policy in both modes. Values
below are census control -> maintained accounting:

| Measurement | Census | Accounted |
|---|---:|---:|
| Non-tiny structural closure | 902/985 | 902/985 |
| Query time (seconds) | 171.12270 | 87.88366 |
| Discovery (seconds) | 80.99467 | 81.41598 |
| Ordinary solver (seconds) | 90.03441 | 6.40760 |
| Initialization (seconds) | 0.00098 | 0.12228 |
| Warm combined replay (seconds) | 84.36440 | 0.61496 |
| Full cold evidence audit (seconds) | 84.49631 | 79.18184 |
| Separate cold solver open (seconds) | 0.08662 | 0.14813 |
| SQLite bytes | 629,276,672 | 629,280,768 |
| Six-case traced Python peak (bytes) | 24,159,525 | 24,164,413 |

Query cost falls 48.64%, while discovery changes by only 0.52%. It now accounts
for about 92.6% of the accounted query cost. All answers, source identities,
recognition profiles, closure summaries, search counters and per-query totals
agree. All three evidence-table digests match; every seed row is preserved. The
accounting path performs one opening census and zero per-query reconstructions.
Independent validation scans and cold audits are outside these query timers.
The old 21,838 residuals / 65,665,771 length units do not grow on this prepared
corpus: this measures reuse of previously acquired answers, not faster new SAT
search. Added accounting state is 4,096 bytes, with no meaningful memory saving.

The [empty-history control](../experiments/results/cnf-accounting-empty/README.md)
retains 88/96 closures and identical evidence: query time is **7.70202 -> 7.73052
seconds**, ordinary solver **1.26394 -> 1.24975**, and warm combined replay
**0.27283 -> 0.05134**. Both modes acquire 1,287 residuals / 3,341,590 units.
This control does not show a clear acquisition speedup. Counters trade extra
per-write work and opening cost against scans avoided over later queries.

On the [96 fresh-input controls with prepared history](../experiments/results/cnf-accounting-fresh/README.md),
both modes still close 88 and acquire the same **1,278** additional residuals.
Query time falls **15.20412 -> 8.38678 seconds**; ordinary solver time
**7.92061 -> 1.50081**; discovery **7.27256 -> 6.87997**; warm combined replay
**6.36229 -> 0.05113**. Cold full audits cost **53.11792 / 50.56766 seconds**.
Both modes end at **23,116 residuals / 69,006,358 units**, with 4,096 extra SQLite
bytes for accounting. These inputs are novel relative to the original seed,
but reused from the published comparison rather than an independent holdout.
Earlier residuals can share internal subproblems, explaining the different new
row count from the empty control. No additional closure or evidence compression
occurs here.

These are single comparisons; they are not statistical significance estimates.
The empty control ran on 9 November and the prepared comparison on 12 November;
only within-suite paired timings are compared. The next runtime and memory
target is selected-proof checking with shared or bounded decoded state. The
next coverage target remains transport beyond exact prepared sources, including
checked binary elimination and explicit shared-variable compatibility.

The unchanged Lean build/axiom audit passes at 4,148 declarations / 1,988 theorems.
The manuscript's 63 existing proof blocks are unchanged; Section 12.72 describes
this accounting change, including opening, conflicts, regressions and scope.
The proof-audit rerun initially encountered missing temporary toolchain sidecars;
the failure and digest-verified repair are retained in the full result directory.
