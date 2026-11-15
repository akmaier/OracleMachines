# Reuse unchanged table digests during expansion

The previous run located repeated full-table scans in batch preparation. This
experiment separates three choices: hash the batch's copied database, hash every
table on the live solver connection, or reuse hashes of provably unchanged live
tables. Every choice still creates the batch copy and performs the same bounded
expansion, checks and append export. Two independent repetitions run the methods
in opposite orders.

## Expansion result and measured cost

The saved **34/120/355** split closes the enclosing case-1120 focus in one batch.
All six independent arms enter and store the same **32 patterns**: fifteen probe,
eight elimination, six binary-path, two family and one polarity node. No entered
input remains unstored; all thirteen previous interruptions are completed. Coverage increases **66/83 -> 67/83**, gaining retained
index **22**. The driver stops on focus closure, as it should: there is no second
expansion batch in which unchanged-table digest reuse could explain a saving.

The new terminal certificates also describe a useful class transition. One
cofactor reaches **6/11/29 zero-valid**, outside syntactic Horn, dual-Horn, 2-CNF
and one-valid. Another reaches a **5/7/16** formula excluded by those five direct
recognizers; the existing polarity certificate flips local variables **4 and
5**, producing a **5/7/16 Horn and zero-valid** terminal. The checkpoint's
`terminal-patterns.json` records the node hashes and these descriptors. This
uses the existing recognition rules and supplies no new all-CNF coverage theorem.

| One-batch worker, two repetitions | Copied full scan | Live full scan | Guarded live scan |
| --- | ---: | ---: | ---: |
| Mean worker seconds | 12.68940 | 8.55304 | 8.50387 |
| Mean digest seconds | 4.47472 | 0.46050 | 0.48794 |
| Mean checked-session startup seconds | 7.56520 | 7.54456 | 7.47956 |
| Mean expansion seconds | 0.17096 | 0.17183 | 0.16833 |

The observed live-full worker reduction is **32.6%** against the copied scan.
Both methods hash every row. Thus this comparison supports reading the already
owned database, and does not attribute the reduction to reusing table hashes.
Guarded mode also computes all initial hashes; its small worker-time difference
from live-full is not evidence that the guard makes initial hashing faster.
There are only two observations per mode, shared OS caches and no confidence
interval or holdout claim. The batch copy remains charged in every method.

A separate warmed seed scan costs **0.43978 seconds**, with **0.34600 seconds**
in the pattern table and **0.08047 seconds** in the residual table. Patterns
account for about **79%** of that scan time. Since acquisition changes this table,
unchanged-table reuse cannot remove the dominant warmed hashing cost.

The producer costs **270.41897 seconds** across all six arms, including
**114.01706 seconds** of parent reconstruction and **69.46916 seconds** of final
route preparation plus global coverage. These common verification costs are
outside the worker comparison and remain substantial. No pipeline-wide 32.6%
reduction is claimed.

Persistent history grows **405,504 bytes** to **778,821,632 bytes / 42,335
patterns**. The new delta is **479,232 SQLite bytes / 21,314 compressed bytes**.
Reference nodes grow **4,153 -> 4,198**; the expanded positive certificate grows
**3,360 -> 3,518 steps**. The activation index retains **708 routes**, now with
**zero missing-target links**. Empty retained obligations do not mean all
originals are covered: sixteen remain open.

## Retained regression: digest refresh after a real append

Because the focus closes after one batch, a separate replay measures refresh on
that exact 32-row append. It binds the checkpoint and delta hashes, restores the
parent independently, applies the delta on the owning connection, and compares
every result with a new-connection full scan. It does not perform fresh solving.
Three repetitions reverse the order of full and guarded scans. Preparation,
initial hashing, merging and refresh are charged; independent audit is separate.

| Mean isolated cost, seconds | Full live scan | Guarded reuse |
| --- | ---: | ---: |
| Initial hash snapshot | 4.14096 | 5.62201 |
| Refresh after append | 0.42444 | 0.42716 |
| Copy + initial hash + append + refresh | 4.71509 | 6.22119 |
| Additional unchanged snapshot | 0.42282 | 0.00898 |

Guarded refresh scans **42,335 pattern rows** and reuses **24,281 rows** across
seven tables. Full refresh scans **66,616 rows**. Two guarded refreshes take
**0.34916/0.35779 seconds**, but the third takes **0.57453 seconds**, erasing the
mean advantage. Its initial count guard alone costs **0.72083--0.78602 seconds**
on the copied seed. Retaining fewer scans therefore does **not** establish a
runtime reduction for these short sequences. The unchanged-snapshot saving is
real within this measurement, but represents another read with no expansion.

Keep the guarded helper experimental. Use **live full scans** for the next
expansion comparison. If revisiting guarded reuse, first remove the redundant
initial count scans by using row counts obtained during the initial full hash,
under the same lock; measure enough changed batches to charge that setup cost.
The much larger remaining worker cost is checked-session construction.

## Validation

Independent cold replay passes in **545.69979 seconds**, with fresh recognition
and reference search disabled. It reproduces all six intermediate catalogs and
checks all **4,198 reference nodes**, including lifted models for both cofactors
and the original **48/204/612** case-1120 model. The false and true cofactors use
**21 and 11 new prefix nodes** respectively; their class transitions do not
represent reuse of identical stored prefix nodes between these two branches.
All **4,153 previous reference payloads** and **1,493 artifacts / 29 prior
manifests** are unchanged. All **245 tests** pass. The manuscript builds to
**164 pages**, preserving all **64 previous proof blocks**. Timed producer and
refresh runs finished before tests and cold validation; validation work overlapped
and its elapsed time is not used for a speed comparison. The checkpoint manifest
binds **74 artifacts**; commands, fingerprints and limitations are in
`validation.json`.

## Resume and remaining targets

Resume `experiments/results/cnf-guarded-digests/report.json` through
`compare_cnf_guarded_digests.restore_checkpoint`, report SHA-256
`15f28884970be856f78475cdc426604f499998f6f2483ebbaa2760f8e8cc194f`.
Evidence remains **(1, 42, 156, 55, 1)** with **two bridges**. The completed
`source` field remains the case-1120 focus; use **`next_selection`** to move on.
It selects **39/167/519**, original **case 1061**, retained index **13**, key hash
`88d90c3204e339d9422e80bd0a4ef8fa3db398874e034334de0ba7995916e92b`,
with no pending split. Do not restart acquisition on the completed focus.

The next useful integration question is whether a checked live session and
coverage index can continue across original cases. Initial session construction
still costs about **7.54 seconds** of the **8.55-second** live-full worker. Global
route preparation plus coverage costs **69.47 seconds**; parent reconstruction
costs **114.02 seconds**. The existing `CoverageIndex` provides a candidate, but
complete catalog maintenance, implicit rules and original-case binding must
still be checked. No reuse across original focuses is measured here.

## Exact reuse condition

`experiments/cnf_guarded_digests.py` computes its initial hashes itself. It does
not accept a claimed hash from a report. For each table it retains the row count,
maximum rowid and key-ordered digest, plus the owning connection's change counter,
data version and schema version. Only the same exclusively owned connection may
write between snapshots. The supported persistent schema has no temporary table
name shadowing. On each snapshot, an immediate transaction excludes
concurrent writers while the guards and hashes are computed.

Let `a_t` count rows above table `t`'s previous maximum rowid. The guard requires
unchanged data and schema versions, an increase of exactly `a_t` in each table's
cardinality, and an increase of exactly `sum(a_t)` in the connection's total
change count. Under the ordinary SQLite write contract, these equalities exclude
updates, deletions, replacements, writes to other tables, low-rowid inserts and
rolled-back writes. An ignored duplicate insertion changes neither count and is
harmless. Rolled-back writes are conservatively rejected even if the final
contents match. Rejection invalidates the cache; a new instance must scan again.

The count argument uses both equalities. A deletion reduces net cardinality while
increasing the change count; an update increases the latter without increasing
cardinality. A replacement removes an old row without a corresponding net gain.
After excluding these operations, matching the suffix count to the total gain
excludes insertions below the old rowid boundary. Consequently, a table with
`a_t = 0` has exactly its previous contents and may reuse its digest. Every table
with `a_t > 0` is fully rehashed in key order. Newly inserted keys may precede old
keys: hashing just their suffix would not produce the existing digest format.

This is a live bookkeeping invariant. It neither proves the stored SAT
certificates nor protects against raw-file tampering, falsified SQLite pragmas or
changes to caller-owned cache objects. Those are outside the exclusive-ownership
contract. A restart computes hashes and checks certificate authority again.

## Resource bound

For `T` tables, the retained digest state has `O(T)` entries and contains no copied
certificate payloads. Let `H_t` be the complete key-ordered scan cost for table
`t`, including retrieval, encoding and hashing. The initial snapshot costs
`sum(H_t)` plus guards. A later snapshot costs

`G + sum(H_t for changed tables t)`,

where `G` includes the row-count and rowid queries. These queries still visit
index pages; this implementation has no constant-time or delta-only guard bound.
If all tables change, all hashes are recomputed and the guard is extra work.
Reducing scans of unchanged tables establishes no bound on the size of the
changing pattern table or on arbitrary-CNF expansion.

## Reproduction

Run `python3 -u experiments/compare_cnf_guarded_digests.py OUTPUT`, then
`python3 -u experiments/validate_cnf_guarded_digests.py OUTPUT`. The second command
reconstructs every intermediate catalog without this cache, disables fresh
recognition and reference search, checks certificates and compares all six
sequences. Run `python3 -u experiments/benchmark_cnf_digest_refresh.py OUTPUT`
for the separate append-refresh replay. `solver/test_cnf_guarded_digests.py` exercises the invalidation cases
and compares each accepted snapshot with a fresh full scan.
