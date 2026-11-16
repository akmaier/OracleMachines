# Incremental bookkeeping for persisted SAT evidence

The previous support experiment saved search but spent most warm-query time
scanning its growing archive. This experiment reuses the existing
[transactional size ledger](residual-accounting.md) and adds a guarded cursor
that exports only new certificate rows. It changes bookkeeping, not SAT search,
proof checking or the recognized structural classes.

## Matched costs

All modes start from the same 13,869-key reference union, the same persisted
145-core bank and 260 single-deletion templates. They do not extract the cores
again. The original extraction, proof acquisition and retained storage remain
charged in the earlier experiment. These measurements do not establish a
cumulative amortization break-even.

Selection follows the previous salted ordering over double deletions, excluding
all 192 previously answered queries (including the 53 guarded answers without
direct roots), then excluding any cached complete root. The next 64 inputs per
template are interleaved. Selection costs 1.46245 s separately. These are
constructed neighbouring inputs, not a blind arbitrary-SAT holdout.

Three balanced fresh-process triples visit the 192 inputs twice. `scanned` uses
the ordinary solver and full row inventories before and after every query;
`ledger` replaces only the solver's size aggregation; `delta` also uses the new
insertion cursor. No tests, builds or profilers overlap the timed workers.

| Measurement | Scanned | Ledger | Ledger + delta |
|---|---:|---:|---:|
| Mean complete worker seconds | 37.48164 | 30.49257 | 14.81201 |
| Mean two-visit query seconds | 23.96449 | 16.90468 | 1.37640 |
| Mean repeated-visit seconds | 11.63897 | 8.13676 | 0.16423 |
| Mean cold audit seconds | 10.10131 | 10.18020 | 10.06537 |
| Mean compression seconds | 2.54735 | 2.54418 | 2.53148 |
| Mean peak RSS, bytes | 409,310,549 | 409,343,317 | 448,435,541 |
| Full row inventories | 772 | 772 | 3 |
| SQLite bytes | 44,781,568 | 44,785,664 | 44,785,664 |
| Gzip bytes | 3,563,875 | 3,564,571 | 3,564,571 |

Compared with full scans, delta mode reduces complete time **60.48%**, query
time **94.26%**, and repeated-query time **98.59%**. The ledger alone reduces
complete time **18.65%**; adding deltas reduces it a further **51.42%**. The
complete clock includes restoration, bank loading/checking, accounting setup,
queries, final preservation checks, cold replay, sidecar writing and compression.
It excludes process launch, imports, command-line protocol/catalog reads and
final report writing. All historical acquisition remains outside this new-worker
clock and preserved in earlier accounts.

**Memory does not improve:** mean peak RSS rises **9.56%**. This is a whole-process
high-water mark including cold verification, not a query-only allocation count.
We have not attributed the extra peak to a particular phase. Accounting adds
4,096 physical database bytes and 696 gzip bytes; all modes retain exactly the
same proof rows. Delta mode's first-trial gzip plus raw query sidecar totals
9,537,614 bytes, versus 9,523,666 for the scanned control. This is no proof-space
compression result. The repeated CNFs in sidecars remain a storage target.

## Invariant and invalidation

`ResidualAppendCursor` requires an exclusively owned `AccountedResidualSolver`
connection. Its temporary state holds the largest rowid and rejects local
updates, deletes, replacements and nonmonotone insertions. The existing ledger
updates count and SQL length totals in the same transaction as the proof row.
Rollbacks restore both the ledger and cursor high-water mark. The cursor reads
only committed insertions after its previous mark, checking their count, length
sum and final rowid before advancing its in-memory snapshot.

The insertion suffix is exact by induction on committed append transactions:
the starting mark covers the complete old archive; each permitted new row has
a larger rowid; rewrites are forbidden; and rollback contributes neither a row
nor a high-water change. Thus a successful consumption returns every newly
committed row once. The separately maintained totals check the suffix accounting.
This argument assumes the owned-connection contract and valid solver writes;
the cursor itself does not certify the contents of a SAT proof.

Committed external writes or schema changes invalidate the cursor and require
full comparison. It is not a trust boundary against hostile private-schema
changes or a concurrent-solving protocol. An ignored duplicate may conservatively
dirty the inherited ledger and trigger a full census, even when no row is added.
Opening always reconstructs the ledger once; reopening requires a new cursor.
All measured candidate runs need exactly one opening census and no repairs.
Full initial/final inventories, independent final count/length aggregation and
complete cold certificate replay remain charged. No old archive row is deleted.

If the archive contains R rows with total key/payload length B, repeated full
inventories and size scans cost proportional to the history visited at each
query. The normal append path instead charges the opening/final scans, a
constant number of metadata accesses per query, indexed insertion checks, and
the newly written/exported payload. A suffix lookup also pays the rowid-index
seek. Conflict repair, full cold verification and compression retain their
full-history costs. SQLite TEXT length units agree with byte counts for our
ASCII JSON, but not for arbitrary Unicode or embedded NUL values. There is no
change to SAT's worst-case branching or proof-size bounds.

## Search coverage and next gaps

All modes answer **96 SAT / 96 UNSAT**, use **41 checked core hits**, publish
**96 witness answers**, and use **55 UNSAT guards**. They perform the same
**202 fresh expansions**, including **56 split nodes**, and add **339 keys**;
repeated visits add none. All 202 fresh expansions belong to negative queries.
The largest cases are 66 and 76 (16 expansions each), then 41 (12). Template
totals are 79, 47 and 76 expansions. These identifiers refer to this new catalog,
not the older original or supplemental structural inputs.

The delta worker spends **67.95%** of its time in the unchanged cold audit and
**17.09%** in compression. Investigate which cold operations still reread
unchanged evidence before reducing any verification. Keep a complete independent
certificate check and exact full-query/guard identities. The memory increase
also needs phase-level attribution. For further structural discovery, the 55
guarded negative cases include 44 that still expand fresh residuals. Look for
reusable supports or negative cofactors across their proof graphs rather than claiming
that accounting has expanded structural closure.

The experiment, source bindings, counterexamples and reproduction commands are
in [the result directory](../experiments/results/cnf-incremental-archive/README.md).

A separate post-hoc cold profile confirms a concrete remaining accounting cost:
384 calls to the unchanged ordinary solver's `archive_storage()` take 7.21981 s
of a 14.87488 s instrumented audit. Complete certificate verification still
visits all 14,208 nodes and takes 6.89997 s cumulatively; canonicalization is
nested within it and must not be added again. These instrumented timings are
not the matched worker timings. The next candidate is one independently checked
size census for an immutable cold snapshot, while preserving every proof and
query check. No audit checks have been removed in the current experiment.

All 418 tests pass, including 15 focused ledger/cursor tests, exhaustive small
CNFs, rollbacks, failed budgets, rejected rewrites, duplicate inserts, external
writers, schema changes and reopening. Independent validation checks nine
complete archives and 3,456 trial query replays, every union node, 461 inherited
decisions and all 192 new decisions with fresh search disabled. Ledger and delta
archives are also physically identical in every repetition. The new union uses
the plain scanned schema so the optional accounting schema is not required for
future replay.

Resume `experiments/results/cnf-incremental-archive/checkpoint.json`. Preserve
all inherited fields plus `incremental_archive_study` and
`incremental_archive_decisions`. The union holds 14,208 keys / 44,781,568 SQLite /
3,563,875 gzip bytes. Its 192 new decisions contain 137 direct query roots and
55 explicit guarded cofactor records. The latter require their complete source,
guard and child together. Structural authority remains 2,614 patterns / 259
split pairs / 17 missing children, original 17/24 with 999 proof steps, and
separate supplemental 24/24 with 208 proof steps. Original case 7 remains its
separate discovery pointer. No Lean theorem or unrestricted-SAT claim changes.
