# Certified affine batch preparation and sharing

Runtime checkpoint **`e0cb8d3`**. `AffineNormalize.lean` proves that removing exact
duplicate rows preserves every boundary assignment. Prepared batches are reused
independently of the current boundary; normalized transitions are reused only
after matching the complete boundary and normalized batch. Every new state still
represents its own original history, including row order and multiplicity.

The Python archive stores eligible repeated batches separately and keeps compact
version references. The original canonical version hash is unchanged. Reading a
reference validates the batch and reconstructed version; existing rows are never
rewritten. Admission requires a repeated batch and at least 128 payload bytes
saved per reference. The 256-entry candidate index retains hashes only. An exact
version retry does not trigger an admission. Small and unique batches stay inline.
This is an adaptive storage heuristic, not an all-workload savings theorem.

## Matched experiment

Four modes use the same binary, 64 kernel slots and four resident versions:
`baseline` disables both new options, `normalize` removes duplicates and caches
preparation, `share` enables archive sharing, and `combined` enables both. Thus
the baseline already has the earlier exact transition cache. There are six cases,
five sequential repetitions and rotated mode order: **120 runs / 2,800 decisions**.
Widths 16 and 32 cover repeated batches, novel batches and increasing duplicate
multiplicities. Each stream includes positive and negative branches. The first
two patterns reuse earlier inputs; multiplicity creates distinct original batches
with a recurring normalized relation. This constructed opportunity is intentional.

Service setup, configuration, decoding, lookup/comparison, calculation, transport,
persistence and shutdown are charged. Each run starts a fresh process/database.
Independent full-system elimination checks inputs before timing. The final archive
inspection is excluded and reported separately. Python interpreter/import and
experiment orchestration time are excluded. No build, test or archive adoption
runs concurrently with the final experiment. `pilot/` retains a preliminary
single repetition using identical input/runtime fingerprints; its timings are
excluded from the final medians.

| Width | Stream | Baseline ms | Normalize ms | Share ms | Both ms | Source bytes, baseline -> both |
|---:|---|---:|---:|---:|---:|---:|
| 16 | repeated | 161.45 | 167.25 | 167.62 | 163.29 | 4,265 -> 4,265 |
| 16 | novel | 172.69 | 167.83 | 170.90 | 174.00 | 6,226 -> 6,226 |
| 16 | multiplicity | 367.70 | 223.21 | 365.01 | 223.19 | 17,692 -> 17,692 |
| 32 | repeated | 236.75 | 234.90 | 260.44 | 252.47 | 16,656 -> 6,499 |
| 32 | novel | 413.65 | 411.78 | 410.41 | 412.89 | 22,000 -> 22,000 |
| 32 | multiplicity | 1246.55 | 417.58 | 1254.48 | 430.52 | 51,643 -> 51,643 |

These are descriptive local medians, not significance tests or universal bounds.
The raw records retain ranges, phase costs and negative cases.

- Width-32 multiplicity gains **14/18 kernel hits** where exact ordered inputs
  previously gave none. The executed elimination/decision ledger drops
  **30,266,133 -> 461,575** (98.5%). Both options reduce median service time
  **1,246.55 -> 430.52 ms** (65.5%, 2.90x); normalization alone takes 417.58 ms.
  Submitted rows total **8,673**, reduced to **513** across the stream.
- Width-16 multiplicity reduces the ledger **3,983,509 -> 62,343** and elapsed
  time **367.70 -> 223.19 ms** with both options (39.3%).
- Width-32 repeated has 30 preparation hits and 30 transition hits. Source
  payload drops **16,656 -> 6,499 bytes** (61.0%): one 452-byte batch object plus
  6,047 bytes of version payload, including 30 references. Whole database size
  drops **274,432 -> 262,144 bytes** (12 KiB, 4.5%). The version count stays 35.
  Both options take **252.47 ms**, versus **236.75 ms** baseline (6.6% more).
  Normalization alone takes 234.90 ms; sharing alone takes 260.44 ms. Extra
  reconstruction and validation work can outweigh reduced elimination on hits.
- Width-16 repeated batches stay inline because they fail the savings threshold.
  Novel streams admit no shared objects, have no hits, and preserve source payload
  exactly. Combined median changes are +0.8% and -0.2%; these small differences
  establish neither a speedup nor a general overhead bound.
- Multiplicity variants keep distinct original batches in storage. Semantic
  normalization makes computation reusable; it does not silently change sources.

## Memory and cost boundary

Default preparation and transition maps each have 64 slots. Preparation retains
original typed batches plus normalized lists, sharing those lists with transition
keys. Original request JSON still resides per native version. This can increase
live memory while reducing work. The recorded RSS is a cumulative service
observation, not an isolated allocation experiment or a proved RAM bound. We
make no process-memory reduction claim. Slot caps are not byte budgets.

The kernel miss bound is O(b^3+b^2*c') for c' unique rows. Original-source hashing,
decoding, preparation and persistence remain additional. Preparation input-cell
counters do not count every hash-set probe, insertion, resize or collision.
`uncached_reference_cells` is the selected normalized calculation without
transition hits; it is not the unnormalized counterfactual. Use the baseline
mode for that comparison. `counted_complete` remains false.

For T versions, shared batches replace their repeated coefficient payload with
one batch object and version links; inline occurrences remain. Source coefficient
payload is O(sum_inline b*c_t + sum_shared_batches b*|B|), before compression and
all metadata/index/result costs. Each version remains archived. Fully novel
streams can still require O(sum_t b*c_t); there is no default archive size cap.

## Checks and preservation

- **207 tests pass**, including 26 affine growth, six affine archive and 36 source
  update tests. Coverage includes complete-frontier agreement on branching
  systems, differing duplicate counts, hash-slot collisions, restart, corrupted
  and recursive references, novel-batch admission, and rollback after a shared
  batch has already been inserted. Original identities and rows remain intact.
- Lean audits **4,043 declarations / 1,911 theorem declarations**, without admits
  or added axioms. The native chronological original-input theorem still holds.
- Generated C inspection confirms preparation hits skip duplicate removal,
  normalized lists pass by reference into kernels, and original-history proof
  transport invokes no second elimination and retains no history ancestor chain.
- All **355** older generic inputs, **five** source versions and **268** distinct
  affine versions pass revalidation. The archive contains **10,295 results /
  3,483 refutations / 85 source rows / 1,340 affine result rows** across engine
  namespaces; the latter represent 268 distinct affine histories.
- Every old row in **22 tables** and all **583** preceding experiment files are
  unchanged. The main database is **19,738,624 bytes** after adding the new
  namespace. Old inline source objects are preserved, so this is not a migration
  of the old archive into a smaller format. Experiment databases/backups are
  retained separately and are additional local disk use.
- All **36** earlier manuscript proof blocks are preserved in order; one proof
  and the four-mode measurement are added. The prior exact-kernel proposition
  is explicitly scoped to its unnormalized mode.
- The old six-stream diagnostic reproduces every prior count and nominal charge
  with normalization, sharing and the kernel cache explicitly disabled.

`comparison-check.json` verifies timing sums, counters, medians, runtime/input
fingerprints, all retained run rows, original batch reconstruction and identical
version identities across all modes. `preservation.json` records the backup and
adoption; `after-work-preservation.json` checks the old rows/artifacts again.
Build/test logs and source fingerprints accompany this record.

## Next expansion priorities

1. Native checked batch registration/handles: avoid decoding, hashing and retaining
   the same original request body per version; extend the source-origin theorem.
2. Byte-based admission and cache budgets, with isolated live-allocation profiling.
   Repay the measured reconstruction/validation overhead before claiming speed.
3. Broader equivalence (row permutation, canonical row space, variable renaming)
   with certified transport and charged discovery costs. First-occurrence order
   currently remains part of the normalized transition key.
4. Low-rank equation changes and reusable elimination structure, with the exact
   interface and reconstruction conditions proved.
5. Checked durable kernel checkpoints to reduce cold replay. Replay still walks
   original history and maintains an O(T) identifier plan.
6. Python/SQLite and serialized-witness refinement and complete physical-resource
   accounting. General CNF does not inherit affine compact closure; no new
   unrestricted SAT or P-versus-NP claim follows.

Reproduce in a new directory, preserving all previous output:

```sh
python3 experiments/compare_affine_batches.py --output experiments/results/affine-batches-new --repetitions 5
```
