# Batch verified publications while preserving committed results

On the existing 104-source replay, bounded publication reduces commits from 605
to 104 and mean query time by 35.55% against the direct-verification control. All
answers, models, proof payloads and non-batching work counters remain identical.
The mechanism changes when verified records become externally visible. A failed
query can lose its unfinished batch; completed queries and committed prefixes
remain available. It stays an optional experiment, with no new SAT coverage.

## Publication and failure contract

`BatchedPublicationSolver` inherits the previous search and direct certificate
verifier. Its connection adapter groups the original checked INSERT stream, with
limits on successful inserted records and encoded key/payload bytes. A batch is
flushed before an insertion would exceed its payload limit, when a record/count
limit is reached, and before a successful query returns. One oversized record is
committed alone. Setup/schema commits occur before batching begins; SQLite's
journal and synchronous settings are unchanged.

The solver requires exclusive ownership of an idle connection. Untracked write
interfaces and direct commit/rollback inside a query are rejected. The original
transactional accounting singleton shares the native writes' transaction,
including reconstruction after ignored duplicate inserts. The existing append-only
proof format and all checks remain unchanged.

On failure, SQLite rolls back the pending suffix and the adapter evicts checked
aliases for its native/v1/v2/v3 keys. Committed rows remain, and the pure binary-core
discovery cache remains reusable. A failure after a successful commit retains
that prefix. An uncertain rollback poisons the instance: it cannot answer another
query until the archive is reopened through a new solver. No answer is returned
before the final commit succeeds.

The dependency argument is an induction over committed batches. Before insertion,
the original verifier checks every dependency against an already committed row
or an earlier verified row visible in the same transaction. Committing the whole
batch therefore preserves dependency closure. Rolling back the pending suffix
leaves the preceding closed archive. The cache invalidation rule prevents a
rolled-back row from subsequently serving as checked evidence. This argument
assumes the existing append-only producer/checker contract and exclusive ownership;
it is not a new Lean verification of SQLite or Python.

## Matched costs

Six serial workers use forward/reverse order: unchanged direct verification,
the adapter with one record per batch, and the adapter with 32 records / 256 KiB.
All start empty on exactly the same 104 sources (42 SAT / 62 UNSAT). These are
replayed small inputs, not new or representative arbitrary-SAT coverage.

| Quantity | Direct control | One-record adapter | 32-record adapter |
|---|---:|---:|---:|
| Verified inserted records | 605 | 605 | 605 |
| Publication commits | 605 | 605 | 104 |
| Native expansions | 505 | 505 | 505 |
| Mean query seconds | 0.46559 | 0.47109 | 0.30007 |
| Mean warm seconds | 0.01109 | 0.01112 | 0.01144 |
| Mean cold seconds | 0.11335 | 0.08360 | 0.08535 |
| Mean complete-worker seconds | 0.71633 | 0.69140 | 0.52383 |
| Peak pending records | — | 1 | 27 |
| Peak pending encoded key/payload bytes | — | 3,762 | 39,747 |
| Peak charged pending-key object bytes | — | 1,468 | 17,086 |

Against the direct control, query deltas are **-0.20882 / -0.12221 seconds** and
complete deltas **-0.26445 / -0.12054 seconds**. The observed mean complete reduction
is 26.87%. However, the first direct-control cold replay takes 0.14304 seconds,
versus 0.08365 in its second order; every other cold sample is about 0.083–0.085
seconds. The same reader checks identical archives in all arms. Treat this cold
variation separately rather than attributing it to batching. Against the
one-record adapter, query time falls 36.30% and complete time 24.24%; both orders
improve. The one-record adapter itself raises query time 1.18% over direct control.
Two order-balanced samples are descriptive, not a general performance law.

All arms retain 552 native / 53 extension records, 651,784 combined payload bytes,
1,179,648 SQLite bytes and 125,493 gzip bytes. Normalization, proof checking and
key serialization are unchanged. Byte sizing adds a scan of all 651,784 encoded
key/payload bytes. Query/warm sidecars grow from about 804 KB to 861 KB through
instrumentation. Mean peak RSS is 59.60 / 60.38 / 60.51 MB respectively, so this
experiment supplies no process-memory reduction.

At 32 records the timed workload never reaches either configured limit: the
largest query inserts 27 records, so the policy commits once per query. Separate
tests exercise earlier count/byte cuts and oversized single records. The extra
Python charge covers pending-key lists, tuples and their string referents, with
shared objects counted conservatively. It excludes adapter scalars, SQLite page
caches, journals, allocator overhead and the solver's existing checked-proof cache.
The payload bound is at most the configured limit or one oversized record;
there is no whole-process memory cap.

A separate untimed replay samples rollback-journal size after every INSERT.
Peak journal size rises **49,760 -> 103,112 bytes** between one and 32 records.
Both use `journal_mode=delete` and `synchronous=2`, as observed without changing
settings. Payload limits do not bound journal size or elapsed lock-holding time:
a long search between publications can retain a transaction. Multiwriter
throughput, power-loss testing and alternative journal modes remain unevaluated.

Timing includes preparation, recognition, normalization, discovery, solving,
checking, accounting, key/payload sizing, commit work, warm/cold replay, sidecars
and compression. Imports/source audits precede timing; truth/history audits,
tests, builds, profiles and journal sampling follow all timed workers.

## Validation, preservation and next target

All **1,283 full / 114 focused tests** pass. Twelve new tests cover successful
closure, count/byte limits, oversized records, failure before/after commit, native
and extension cache invalidation, uncertain rollback, duplicate accounting, warm
queries and abrupt process exit. Writable reopen performs journal recovery before
an independent read-only proof audit. These process-exit tests do not simulate
power loss. The initial fixture incorrectly counted a unit query as one record;
its source/log are retained under `failed-test/`.

The audit checks **624 chronological queries / 416 alternative-control comparisons /
104 exhaustive truths / 144 quotient choices / 84 known hits**. An extra replay
independently verifies the entire externally visible proof archive after each of
the **104 actual batch commits**. The full existing archive and histories remain
readable by both readers; 28,886 canonical fixed points and 4,961 representation
mutations still agree with the original normalizer.

Resume `experiments/results/cnf-publication-batches/checkpoint.json`. It references
the unchanged parent archive and decision files: **28,886 native / 26 affine /
42 v1 / 53 v2 / 22 v3 / 34 discovery records**, plus all **5,650 composed / 444
pilot decisions**. All **619 prior sources / 7,904 artifacts / 115 manifests** are
unchanged. No new mathematical answers or duplicate union archive are added.

The identical-output solve-only profile moves ordinary normalization to the
largest exclusive site: **1,163 calls / 0.07401 exclusive / 0.18230 inclusive
seconds**. Commits now
cost **0.03340 seconds for 104 calls**, versus 0.12266 for 605 transaction exits
in the control. Restriction still costs 780 calls / 0.06973 inclusive seconds.
Inclusive times overlap and instrumentation changes timings; these are cost
locations, not additional matched speedups.

**Next investigate repeated residual construction and canonicalization across
child acquisition and proof checking.** First count exact raw repeats at those
call sites, including noncompact variable names; the preceding census of only
already-normalized outputs found 45 visitation opportunities. Transport or reuse
must retain the source/conditioning identity, original-variable map and full key,
and preserve independent proof checks. Avoid reinstating the general cache that
already regressed. This is an unresolved opportunity, with no claimed savings or
uniform polynomial bound for arbitrary SAT.

Final executable source ledger: **625**. The new manifest binds **43 artifacts**;
next preservation audit: **7,947 artifacts / 116 manifests**.
