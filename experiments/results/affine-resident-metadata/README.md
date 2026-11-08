# Reuse of checked resident parent widths

Runtime checkpoint **`569cda4`** replaces a redundant source-object read with the
width already confirmed by a successful native definition. The bounded residency
map keeps this integer until eviction, reset, worker replacement or rollback.
The public requested source and every missing replay source are still read and
validated. No original source, persisted result or native proof changes.

`affine_reuse_metadata=False` selects the former read path. Both modes keep
duplicate normalization, shared batches, 64 kernel slots and four resident
versions. `matched/` contains **60 runs / 2,160 decisions**: widths 16/32/64,
repeated/novel batches, five sequential repetitions with rotated mode order,
34 expansions and two cold branch queries per run. Each cold query creates a
new service and native worker; operating-system file caches are not flushed.

Setup, requests, storage accounting, persistence and shutdown are charged.
Independent elimination of each complete original history runs before timing.
The final archive audit, Python interpreter/import and orchestration are excluded.
No tests, builds or archive-adoption jobs ran concurrently with the measurement.
The recorded source revision is the preceding commit; source fingerprints match
the runtime checkpoint above, as checked in `comparison-check.json`.

## Measured costs

Medians in milliseconds; warm time covers the 28 interior appends after initial
fill. Cold time includes setup and shutdown for both reconstruction queries.

| Width | Stream | Whole stream, old -> new | Warm appends, old -> new | Two cold queries, old -> new |
|---:|---|---:|---:|---:|
| 16 | repeated | 166.50 -> 160.80 | 27.22 -> 25.84 | 114.76 -> 105.96 |
| 16 | novel | 189.43 -> 186.49 | 51.32 -> 50.72 | 164.67 -> 162.06 |
| 32 | repeated | 238.00 -> 232.72 | 84.39 -> 78.22 | 214.46 -> 201.90 |
| 32 | novel | 388.70 -> 393.50 | 227.78 -> 229.05 | 551.07 -> 543.16 |
| 64 | repeated | 534.69 -> 509.73 | 280.72 -> 260.76 | 640.65 -> 599.29 |
| 64 | novel | 1696.66 -> 1678.52 | 1365.82 -> 1350.57 | 2975.43 -> 2971.10 |

These are descriptive local timings, not significance tests or a universal
speedup. The width-32 novel stream has a slightly worse whole-stream median.
Elimination and kernel hit counts are identical. The deterministic saving is
one full parent-object read per registered append: **4 -> 3** object reads for
an inline warm append, **9 -> 7** when its parent references a shared batch.
In the width-32 shared sample, packed bytes read fall **2,904 -> 2,291**; wire
bytes remain 31,131 sent / 8,175 received, and inserted payload remains 471 bytes.

Repeated width-32/64 whole-stream reads fall **288 -> 223**, and the two cold
queries fall **384 -> 258**. Other cases fall **137 -> 103** and **204 -> 138**.
Source/result object contents, source identities and matched database sizes are
equal across modes. Measurement rows may differ. The main database is untouched.

## Bound and correctness boundary

The additional retained state is O(V) bounded integers, one per existing resident
entry. One temporary parent-batch decode is removed from each forward replay
step. This is not an RSS measurement or a whole-process memory theorem. The
source-input, backward replay plan, coefficient work, archive growth and native
response bounds remain as documented in [the resource audit](../../../research/resource-bounds.md).

All **210 tests** pass, including forged source widths, corruption, long-history
replay, exhaustive small frontiers, rollback and worker replacement. New tests
verify exact read counts and reject a native width mismatch before metadata is
published. `initial-test-run.log` preserves an initial fixture failure: the test
expected `ValueError` but malformed zlib bytes raised `zlib.error`. The corrected
fixture explicitly uses raw encoding to exercise a size-integrity rejection;
no runtime corruption check was weakened.

`comparison-check.json` verifies every run's input/runtime fingerprints, timing
sums, original-history oracle results, retained database size, native transport
and all 30 paired source/result object sets. `preservation-before.json` and
`preservation-after.json` confirm all **743** preceding experiment files, every
row in the main archive's **22 tables**, the native binary and manuscript remain
unchanged. No Lean source changed or new theorem is claimed; the previous Lean
audit still concerns the same code. Python/SQLite refinement remains open.

## Remaining expansion work

Seven object reads, full batch transport/decoding and full definition replies
remain on the representative shared hit. Checked batch handles and compact
replies remain actionable. Cold replay still needs O(T) identifiers and original
source reconstruction. [KD-tree candidate retrieval](../../../research/indexed-reuse.md)
requires a checked repair path before it can exploit merely similar transitions.

Reproduce without overwriting evidence:

```sh
python3 experiments/compare_affine_metadata.py --output experiments/results/affine-metadata-new --repetitions 5
```

## Follow-on structural diagnosis

After the metadata checkpoint, `structural-closure.json` checks the user's
stronger target of making cheap expansion available for every admitted update.
All 204 distinct benchmark updates fit a cube-substitution prototype, with point
boundaries on all 192 regular successors. The prototype passes complete-frontier
checks on 5,010 accepted cases among 11,862 small cases; 6,852 are declined for
general solving. This is an evaluation limitation and a new optimization target,
not a measured or deployed native speedup.

[The precondition analysis](../../../research/expansion-preconditions.md) gives
the conditions, derived costs and revised priorities. Five conditional semantic
lemmas now pass Lean's audit (4,049 declarations / 1,916 theorems); the native
binary remains unchanged. The manuscript adds the result and benchmark caveat,
preserving all 37 prior proof blocks and adding one. Thus the earlier preservation
report's unchanged manuscript/binary statement refers to the metadata checkpoint;
`structural-check.json` records the subsequent proof and document changes.
