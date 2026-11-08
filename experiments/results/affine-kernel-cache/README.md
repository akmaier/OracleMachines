# Certified exact affine transition reuse

Runtime checkpoint: `f80f678`. `AffineKernel.lean` separates a reusable algebraic
result from each append's immutable original history. Every hit requires the same
width, complete ordered parent summary and complete ordered equation batch. A hash
only chooses a candidate. Dependent equality transports the certificate; history
attachment uses the current parent. Equal SAT answers alone never authorize reuse.

## Cost and retention boundary

The default is 64 direct-mapped slots; `affine_kernel_slots=0` bypasses hashing and
lookup. Configurable range: 0..4,096. A miss executes the earlier
O(b^3+b^2*c) coefficient calculation and adds cache overhead. A hit skips
elimination/decision, but scans a key with at most `(b+1)^2+c*(2*b+1)` coefficient
cells and compares at most one candidate. List/dimension checks, hash arithmetic,
allocation, maps, decoding, transport, durable writes and physical memory remain
outside these partial ledgers. `counted_complete` remains false.

Entries retain O(b^2+b*c) coefficient payload, without runtime source ancestors.
The slot cap is not a byte/RSS cap. Version eviction preserves kernels; reset and
worker restart clear them. SQLite retains all original batches and completed
results. Cold replay may encounter fresh kernel hits, but still reconstructs from
source; no durable kernel certificate is trusted. Node reports retain creation
metadata. Actual per-request work is recorded in `affine_updates`, so an ordinary
resident query does not spuriously add a hit or repeat an old charge.

## Matched measurements

`matched/` contains 80 runs: eight cases, two modes, five sequential rotated
repetitions. Each mode uses the same binary, input histories, fresh process and
fresh database, with four resident versions. Service setup, native configuration,
all append calls, decoding, hashing/comparison, elimination, transport, persistence
and shutdown contribute to totals. Python worker import and independent correctness
checking are outside timing. Final database inspection is outside totals and
reported separately. Raw records retain per-phase timing and transport/storage
metrics. The first six streams exactly match the earlier frozen input bytes after
decoding. Width 32 adds longer streams; it changes both width and stream length.

| Width | Stream | Expansions | Hits | Disabled median ms | Enabled median ms |
|---:|---|---:|---:|---:|---:|
| 2 | repeated | 18 | 14 | 134.81 | 132.38 |
| 2 | novel | 18 | 0 | 133.09 | 133.22 |
| 8 | repeated | 18 | 14 | 140.52 | 135.68 |
| 8 | novel | 18 | 0 | 136.96 | 137.28 |
| 16 | repeated | 18 | 14 | 167.57 | 144.21 |
| 16 | novel | 18 | 0 | 155.24 | 156.03 |
| 32 | repeated | 34 | 30 | 496.37 | 215.54 |
| 32 | novel | 34 | 0 | 386.10 | 387.00 |

Width-16 repeated work drops from **719,509 to 75,943** elimination/decision cells
(89.4%); key hashing visits **21,025** cells and candidate comparison is bounded by
**18,864**. Median elapsed service time drops **13.9%**. Width-32 repeated work drops
from **10,987,813 to 565,063**; median time drops **56.6%**, a **2.30x** speedup.
Its five disabled totals range **492.85--513.17 ms**, enabled **213.97--218.24 ms**.

Novel cases have no hits and median overhead of approximately **0.1--0.5%**. Small
differences, including width 2, are not statistical evidence of benefit or a
precise overhead bound. These synthetic affine streams establish no broad CNF
advantage or unrestricted complexity result. The raw data includes outliers.

`pilot-overlap/` preserves an earlier scheduling pilot that began while archive
adoption was running. All its timings are excluded from this table. The final
study begins after adoption finishes, without concurrent builds, tests or archive
adoption. Input hashes and binary/source fingerprints agree between studies.
Neither study overwrites the older history-retention timing artifacts.

## Correctness and preservation

- All **1,760** measured decisions agree with independent elimination of the full
  original systems. Every completed decision remains in its run database.
- **197 tests pass**, including **22 affine / 36 source-update** tests. New cases
  force one-slot collisions, distinguish different SAT boundary relations,
  compare exhaustive frontiers with caching off/on, and cover history rebinding,
  eviction, restart, configuration rejection and failed archive transactions.
- Lean audits **3,938 declarations / 1,875 theorem declarations**, without admits
  or added axioms. The native chronological origin theorem is maintained.
- Generated C inspection confirms the hit branch does not call elimination or
  decision, and history attachment retains only the summary at runtime.
- All **355** old generic inputs, **five** source versions and **268** distinct
  affine versions pass revalidation. Both affine verdicts pass restart with two
  resident versions.
- Every old row in **22 tables** and all **405** previous experiment files remain
  unchanged. The live archive has **9,940 results / 3,354 refutations / 80
  source-state rows / 1,072 affine-state rows** across engine versions.
- `pattern-recheck.json` reproduces the old diagnostic counts and nominal charges
  with the kernel cache explicitly disabled. The diagnostic driver now requests
  this setting rather than relying on the old uncached default.
- All **35** previous manuscript proof blocks are preserved byte-for-byte and in
  order; the manuscript adds one exact-kernel proof and this measured comparison.

`comparison-check.json` checks timing sums, medians, input equality, hit counts,
nominal-charge agreement and retained run rows. `after-work-preservation.json`
checks old rows and artifacts after the experiment. `verification.json` records
code/binary fingerprints; build and test logs are retained alongside it.

## Remaining opportunities

Exact duplicate removal could reduce misses, but it must preserve original source
multiplicity and pay for normalization. It does not add kernel hits in the earlier
six-stream diagnostic. Canonical row-space keys, checked variable renaming,
low-rank elimination updates, collision/admission policy and durable kernel
certificates remain unimplemented. Python/SQLite refinement, serialized witnesses
and complete machine/space costs remain open. No positive hit rate or all-workload
speedup is guaranteed. See the current expansion priorities in
[the persistent gap record](../../../research/implementation-gaps.md).
