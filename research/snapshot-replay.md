# One size census per cold proof snapshot

Cold replay previously recomputed the same archive count and payload total after
each query. A read-only snapshot now computes these totals once and returns them
through the existing `archive_storage()` interface. The experiment executes the
same frozen complete audit: every certificate, query, guard and witness is still
checked by the unchanged verifier. It does not trust the persisted size ledger.

## Matched result

Both modes use the existing delta expansion worker and start from the same
14,208-key reference union, 145 persisted cores and 260 extension templates.
Selection excludes all 384 previously answered double deletions, including
guarded answers without complete query roots, and then excludes cached complete
roots. The next 64 per original template are chosen in the same salted order
and interleaved. Selection costs 1.48599 s separately. These are constructed
development inputs, not a blind sample of arbitrary SAT.

Four fresh-process pairs alternate mode order. Each stream visits all 192 inputs
twice. No tests, builds or profilers overlap the timed workers. Only the final
cold audit changes; expansion and all final preservation checks are identical.

| Measurement | Ordinary audit | Snapshot audit |
|---|---:|---:|
| Mean complete worker seconds | 15.15167 | 7.84969 |
| Mean cold audit seconds | 10.43075 | 3.12634 |
| Mean two-visit query seconds | 1.28359 | 1.27165 |
| Mean setup seconds | 0.73096 | 0.75027 |
| Mean compression seconds | 2.59580 | 2.59602 |
| Mean peak RSS, bytes | 453,730,304 | 455,503,872 |
| Cold size censuses | 384 | 1 |
| Cold proof nodes checked | 14,630 | 14,630 |
| SQLite bytes | 46,530,560 | 46,530,560 |
| Gzip bytes | 3,674,583 | 3,674,583 |

Complete time falls **48.19%** and cold replay **70.03%**. Complete-time reductions
range from 47.84% to 48.90% across the four pairs. Peak RSS rises **0.39%**, so
there is no memory saving; the earlier delta-worker memory regression remains
unresolved. Query and setup changes are small timing variation, not altered
search. Both logical and physical certificate archives are identical in all
eight runs. Storage is unchanged. The new operation adds no persistent table,
trigger or proof node.

The worker clock includes restoration, bank loading/checking, expansion,
bookkeeping, final full preservation checks, complete cold replay, query sidecar
writing and compression. It excludes process launch, imports, command-line
protocol/catalog reads and final report writing. Historical extraction and
acquisition remain charged in previous experiments. These savings must not be
multiplied by the preceding experiment's percentages: the new input set and
starting union differ. No cumulative amortization break-even is established.

## Why the cached totals remain exact

`SnapshotResidualSolver` opens the source through SQLite's read-only URI mode,
starts a read transaction and independently evaluates the original count/length
query. This first read establishes the view used by all later proof loads and
queries. An authorizer permits read operations and rejects writes, schema
changes, attachments, transaction-ending statements and savepoints. The session
also checks that the transaction remains active. Search and publication reject;
the frozen audit separately disables fresh expansion as before.

Let S be that pinned database view. Its rows and payloads are fixed throughout
the read transaction, so the count and length sum computed from S remain the
answer to every later size request in the same session. This argument depends
on snapshot ownership and transaction continuity, not on validity of a saved
accounting singleton. The proof checker continues to establish the separate
SAT/UNSAT claim for every loaded certificate.

The measured audits use private, closed archive clones. The scoped solver
substitution owns its process and is not a concurrent multithreaded audit API.
Replacing private connection state or disabling the authorizer is outside the
contract. A direct snapshot-reader test permits a concurrent WAL writer and
confirms that the reader retains its old view; a new reader sees the committed
rows. This is a logical snapshot test, not a claim that hashing a live database
file also binds an external WAL. Archive-byte bindings here are checked on the
private clones, before and after the audit. Read locks and snapshot lifetime
would need their own accounting in a shared online service.

For Q replayed queries and archive length B across R rows, the previous metadata
work revisited O(Q(B+R)) history. The snapshot charges one O(B+R) census and Q
constant-size returns, plus opening and transaction setup. Full certificate
verification, query reconstruction, hashing and serialization keep their own
costs. The session retains only a fixed number of additional counters, with
logarithmic integer bit lengths in an unbounded model. SQLite TEXT length units
match bytes for generated ASCII JSON but not arbitrary Unicode or embedded NUL.
No SAT search or proof-size bound improves.

## Remaining costs and structural gaps

Both modes answer **98 SAT / 94 UNSAT**, with **54 core hits**, **98 witness
publications** and **40 guards**. Of those guarded negative queries, **37** still
need fresh search, accounting for all **270 expansions**, including **85 splits**.
The largest cases are 100 (21 expansions), 41 (19), 188 (18), and 5 and 142
(17 each). These are case IDs in this experiment's catalog. Original template
12 contributes 129 expansions, template 8 contributes 81, and template 6 contributes
60. Repeated visits add no rows. The existing structural closure does not grow.

Cold verification now uses **39.83%** of complete worker time and compression
**33.07%**; the query loop uses **16.20%**, setup **9.56%**. These are the measured
cost categories, not evidence that fresh SAT search dominates total time.
Further cost work should profile remaining proof normalization and allocation,
or compare persistence methods that avoid rewriting unchanged evidence. It must
retain independent proof checking and all historical certificates.

For broader reuse, the concrete structural target is the 37 negative queries
with fresh expansion. Compare their refutation supports and guarded cofactors
with the retained bank. Publishing a complete query refutation from a guard
would require a checked composition of its stronger UNSAT premise and restricted
child; storing the child key alone is invalid. Smaller or incremental supports
may transfer to later edits, but discovery, certificate construction and the
growth of the proof graph must be measured. The old 121-core antichain has not
yet been benchmarked and does not by itself expand superset coverage.

See [the result directory](../experiments/results/cnf-snapshot-replay/README.md)
for frozen sources, all trials, independent reconstruction and reproduction.


All 426 tests pass, including exhaustive small-CNF equivalence, blocked writes
and transaction changes, missing inputs, unknown queries, corrupted unqueried
proofs, altered answers/identities/models, witness/guard checks, and snapshot
stability under a WAL writer. Independent ordinary-solver validation replays
3,072 trial queries across eight full archives, every union node, 653 inherited
decisions and all 192 new decisions with fresh search disabled.

Resume `experiments/results/cnf-snapshot-replay/checkpoint.json`. Preserve all
inherited fields plus `snapshot_replay_study` and `snapshot_replay_decisions`.
The union retains 14,630 keys / 46,530,560 SQLite / 3,674,583 gzip bytes; it also
retains the existing accounting schema, which the snapshot audit does not trust.
The 192 new decisions comprise 152 direct roots and 40 explicit guarded records.
Structural authority remains 2,614 patterns / 259 split pairs / 17 missing
children, original 17/24 / 999 proof steps, and separate supplemental 24/24 / 208.
Original case 7 keeps its separate discovery pointer. The manuscript builds to
193 pages, retaining all 64 existing proof blocks. No Lean theorem changes.
