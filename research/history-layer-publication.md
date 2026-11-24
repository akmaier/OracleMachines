# Publish append records without recompressing old proof history

24 November 2026. The preceding support-composition checkpoint added 173 native
records but recompressed the entire 2.10 GB cumulative history. This experiment
publishes that same already checked expansion as an immutable parent archive,
a compressed append database and a bound descriptor. It performs no fresh SAT
acquisition and changes no solver decisions, proofs or pattern coverage.

## Exact preservation contract

For each of the six authority tables, every parent key must occur in the target
with the identical payload. The delta contains exactly the target keys absent
from that parent. Restoration rejects every overlapping key, including a duplicate
with the same payload. Applying all six tables occurs in one transaction, so an
error rolls back earlier inserts and accounting-trigger updates. Native proofs
remain subject to the existing readers; an archive hash is not a SAT certificate.

The descriptor binds the parent, compressed delta, schema-compatible row counts,
chain depth, and the materialized database's size and SHA-256. It is rooted in a
trusted checkpoint entry. Restoration checks each dependency and reconstructs in
a temporary directory, publishing the destination only after its final physical
hash matches. An existing destination is never overwritten. Legacy single-file
and multipart histories remain readable through the new reader.

Inputs to preparation and publication must be closed, checkpointed and exclusively
owned immutable snapshots. Preparation verifies their identities, exact schema
and trigger definitions, all old payloads, new key types, and append accounting.
This is an endpoint comparison; it does not certify that no intervening write,
rollback or replacement ever occurred. Prepared Python objects are not a new
persistent trust boundary or a concurrent-writer protocol.

The first trial exposed a useful incompatibility: both historical endpoints
contain the identical explicitly dirty accounting tuple `(1,28691,45329525,1)`.
Those stale counters are not the actual 160,338 native records. The original
implementation rejected them before publication. Its source, protocol, tests,
input timings and failure log are retained under `failed-clean-ledger/`.
The revised implementation preserves an unchanged dirty tuple as metadata and
counts authority rows directly. Clean ledgers must follow exact append increments;
changed dirty metadata or a clean-to-dirty transition requires a full snapshot.
The existing accounted solver reconstructs stale counters when opened. No proof
validity or resource count is inferred from a dirty ledger.

The earlier `cnf_append_delta.py` targets eight historical tables and requires an
owned live connection plus its original append boundary. It cannot be applied
unchanged to this six-table snapshot. The new implementation keeps its append and
conflict discipline but discovers new keys by comparing immutable snapshots.

## Resource accounting

Let B be the full database bytes and D the exported append database bytes.
Compression consumes D instead of B, but total publication is not O(D): source
identity hashing still reads both complete snapshots, indexed joins check all
old keys and payloads, and one full parent copy plus reconstruction hash binds
the new physical database. The prepared key lists retain the new IDs; SQLite
page caches and individual payloads require additional working memory. Export
and compression still scale with the append set and its payloads.

The descriptor's `compressed_bytes` counts the parent dependency plus the delta.
`incremental_retained_bytes` counts newly published delta and descriptor files.
These quantities must not be confused with each other or with materialized SQLite
space. The parent remains necessary, and preservation of old controls means this
research repository does not shrink when a new format is added.

Cold restoration still reads the complete parent and every intervening delta,
checks their hashes and writes a full database. It also checks duplicate keys and
hashes the resulting bytes. Chains are limited to 32 layers; later publication
requires a compacted full snapshot or another supported fallback. Compaction,
ancestor retention and cold-reader costs cannot be amortized away without a
workload argument. Non-append payload or schema changes use the full snapshot.

A layer can have a different physical SHA-256 from the old full snapshot because
transaction boundaries and SQLite layout/header bytes can differ. The six tables
and accounting tuple must match exactly; each layer's own physical reconstruction
is separately hash-bound. Repeated trial layers must reproduce the same physical
hash. A previous raw-file hash is never silently reassigned to different bytes.

## Matched experiment

Two serial repetitions use opposite publication orders on the exact preceding
parent and target. Both pay the same snapshot preparation checks. The control
uses the frozen full gzip-and-parts publisher. Each layer exports only new rows,
compresses them, reconstructs once and publishes its descriptor. Both then cold
restore, compare all authority rows and metadata against the target, and replay
every newly added native root and its dependencies through both readers.

The complete-worker interval includes these operations and hash checks. Imports
and frozen-source hashing precede that interval; restoration of the two common
input snapshots is reported separately. The final preservation audit is also
additional. Two repetitions on one exposed historical append are diagnostics,
not confidence intervals or evidence for arbitrary future expansions.

## Results and next step

Means over two serial repetitions; seconds unless a row states bytes.

| Cost | Full snapshot | Parent plus delta |
|---|---:|---:|
| Preparation | 25.10532 | 13.60070 |
| Publication after preparation | 107.88634 | 5.07342 |
| Preparation and publication | 132.99170 | 18.67420 |
| Cold restoration | 1.60643 | 3.23116 |
| Full logical comparison | 3.37663 | 14.51644 |
| New-root dependency replay | 2.11432 | 2.11030 |
| Complete worker | 141.94210 | 40.58869 |
| Mean peak RSS, bytes | 1,375,010,816 | 51,650,560 |
| Newly retained archive files, bytes | 152,624,963 | 38,120.5 |
| Required compressed dependency bytes | 152,623,819 | 152,621,777 |

Preparation plus publication falls **85.96%** and the complete
worker falls **71.40%**. Publication after the shared preparation
algorithm falls 95.30%. The two paired complete-worker reductions are
75.99% and 65.51%; retain both rather than presenting the mean as a guarantee.
The identical preparation algorithm itself varies substantially with order and
cache state: full trials take 42.23000 / 7.98064 seconds and layer trials
11.47698 / 15.72442. There is no claim that layering accelerates those checks.

The new append database is 438,272 bytes and compresses to **36,562 bytes**.
With the descriptor, newly retained files are about **38.1 KB** instead of
**152.6 MB**, a 99.975% reduction in incremental output. Descriptor
size differs by one byte between repeats because it retains timing metadata.
The required parent-plus-delta compressed payload is almost unchanged: it is
only 2,042 bytes below the full snapshot. Neither total retained history nor
cold materialized storage becomes 38 KB. All six tables remain identical;
the raw database remains **2,102,272,000 bytes**.

Mean peak RSS is 96.24% lower in these workers. The frozen full publisher
loads the full database before gzip compression; the layer compresses only the
append database. This measurement is specific to these publishers and one
expansion, not an optimal-compression or general memory bound.

Retain the regressions: cold restore approximately doubles, and full logical
comparison rises from 3.38 to 14.52 seconds. File layout, cache state and repeated
SQL payload joins can affect these phases; this experiment does not isolate
their causes. New-proof dependency replay is effectively unchanged. The complete
worker includes both regressions and still improves. No query-runtime reduction
or new SAT coverage was measured.

**Next publication limit:** preparation and full comparison now dominate the
layer worker. A future exclusively owned append boundary captured during the
checked merge could avoid rediscovering new keys from both endpoints; it needs
explicit conflict, rollback, schema and accounting-state contracts. Existing
historical cursors are not directly compatible. Parent verification, cold reads,
materialization and chain compaction remain charged. Do not bypass proof checking
or assert an O(delta) total cost.

**Next solver target:** return to sharing one immutable local CNF/position-map
binding per contradiction witness across its selected guard certificates. The
previous profile identifies repeated RUP context checks as the remaining gate
cost. Reset on changed contexts and keep every reason, conflict and native check.
Compare complete query costs and fresh unlabelled cases; earlier broad core-pool
retrieval failures still apply. Automatic origin discovery, useful wider
interactions and efficient arbitrary-CNF coverage remain open.

## Reproduction and continuation

From the repository root, the comparison commands are:

```sh
python3 experiments/compare_cnf_history_layers.py prepare OUTPUT
python3 experiments/compare_cnf_history_layers.py inputs OUTPUT FRESH_WORK_DIRECTORY
python3 experiments/compare_cnf_history_layers.py run OUTPUT FRESH_WORK_DIRECTORY
```

The sealed experiment is under `experiments/results/cnf-history-layers/`.
Resume its `checkpoint.json` with
`experiments.cnf_history_layers.restore_archive(checkpoint['reference_union'], destination)`.
The previous full snapshot remains under `full_snapshot_control` and its original
checkpoint. Frozen legacy readers do not accept the new layer descriptor; use
the explicitly named reader or the preserved full control. No solver policy
changes merely because the history now has a different transport representation.

## Validation

The focused suite has 24 tests, including multi-layer reconstruction, duplicate
conflicts and rollback, old-payload changes, schemas, corrupted dependencies,
depth limits, dirty accounting, native replay and atomic destination publication.
All 1,789 solver tests pass, with the same 43 pre-existing unclosed-SQLite
ResourceWarnings and none in the focused suite. The 264-page manuscript builds
without warnings; all 64 previous proof blocks are byte-identical. The full suite
and preservation audit are recorded in the sealed `checks.json`.
The audit restores all four trial archives and compares every authority row;
it additionally replays new roots through both readers once per policy. Every
timed trial already performs that replay. Earlier full-history proof authority
is reused through 169 bound manifests and 16,266 unchanged artifact entries,
not claimed as a fresh proof check of all 160,338 old and new native roots.
All 978 previously frozen sources and the 64 prior manuscript proof blocks stay
unchanged. The new code introduces no proof rule and no Lean change.

The additional final preservation audit takes 144.66 seconds, outside
the measured workers. Hashing all prior artifacts, four complete reconstructions
and table comparisons remain charged; the 71.40% worker saving is not a claim
about reducing every part of a research iteration by that amount.
