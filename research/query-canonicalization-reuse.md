# Bounded reuse of canonicalization within one query

The repeated-normalization opportunity is real, but a general cache does not
reduce total cost on the current 104-input stream. The 128 KiB experiment avoids
19.57% of normalization literal visits and 19.55% of key serialization, while mean
complete-worker time rises 3.65%. Both paired complete-time deltas are positive.
Keep this optional research code; the default solver and all earlier executables
remain unchanged.

## What is reused

`experiments.cnf_query_canonical_cache.QueryCanonicalSolver` extends the existing
known-quotient policy. Each source query opens an empty cache and closes it in a
`finally` block, including after failure. A key is the complete immutable raw CNF
snapshot. A value retains the normalized CNF, original-variable name map and full
canonical key together. This is exact-input reuse, not semantic matching or a new
SAT category. Inputs with equal normalized formulas but different variable names
remain separate entries.

Every lookup validates that each literal is an exact nonzero integer before
dictionary access. This prevents Python's equality between `True`, `1.0` and `1`
from accepting an invalid input as a hit. Hash equality alone never establishes
identity. On a miss the unchanged normalizer runs. Certificates, model lifting,
native acquisition, discovery reuse and all proof readers retain their existing
behavior. A cached transformation does not authenticate an external certificate.

The object budget charges actual tuple/dictionary/string sizes and conservative
integer sizes, overcounting shared objects. Input/name integers use the largest
input magnitude's object size; normalized integers use the variable-count bound.
The budget also includes result and entry tuples and the stored charge integer.
Oversized entries are skipped; admitted entries evict in FIFO order until the
retained charge fits. No recency index is retained. Tests compare the charge with
a deduplicated traversal of the actual object graph, including large integers.

The cap holds after cache operations for these retained cache objects. Temporary
snapshots, new results, dictionary resizing, allocator overhead, metric counters,
the solver's other caches and process RSS are outside that cap. Clearing a cache
also does not promise that Python returns allocated memory to the operating
system. The previous 73,860-byte encoded query footprint was not a Python-object
bound; the conservative 128 KiB cache still evicts 470 entries over this stream.

## Matched experiment

Eight fresh-process workers run serially in forward and reverse policy order:
single-block control, unchanged known-quotient control, 128 KiB cache and 8 KiB
cache. Each starts with an empty archive and receives exactly the previous 104
inputs. Earlier novelty labels describe the previous study; all inputs here are
replays, including its 24 generated controls and twelve designed edits. There is
no new coverage claim or representative large-SAT evaluation.

| Quantity | Known-quotient control | 128 KiB cache | 8 KiB cache |
|---|---:|---:|---:|
| Normalization literal visits | 175,148 | 140,863 | 174,541 |
| Key bytes serialized | 678,378 | 545,747 | 675,988 |
| Cache calls / hits | — | 1,715 / 368 | 1,715 / 14 |
| Extra validated input literals | 0 | 175,148 | 175,148 |
| FIFO evictions / oversized skips | — | 470 / 0 | 316 / 1,295 |
| Peak charged cache bytes | 0 | 131,018 | 8,167 |
| Peak simultaneous entries | 0 | 20 | 5 |
| Mean query time, seconds | 0.45683 | 0.47550 | 0.51112 |
| Mean warm time, seconds | 0.01067 | 0.01534 | 0.01496 |
| Mean cold time, seconds | 0.09877 | 0.09888 | 0.09766 |
| Mean complete-worker time, seconds | 0.69122 | 0.71647 | 0.74958 |

The 128 KiB cache recovers 368 of the 469 within-query repeat opportunities in
the earlier exact census. It reuses 34,285 input literal units; the 8 KiB cache
reuses only 607. Every lookup still snapshots, validates and hashes its input.
Misses additionally run the original validation/normalization and admission
sizing. Fewer normalization visits therefore do not mean fewer total scans.

Against the known-quotient control, complete-time paired deltas are
**+0.04802 / +0.00247 seconds** at 128 KiB and **+0.05281 / +0.06391 seconds** at
8 KiB. Mean query times rise 4.09% and 11.88%; complete times rise 3.65% and 8.44%.
Two orders are descriptive measurements, not a statistical production result.
All warm streams have zero cache hits and no fresh expansion. Their cache work
raises mean warm time by 43.78% and 40.14%, albeit over about 0.011 seconds of
baseline work.

All three known-quotient arms retain identical answers, models, choice traces,
acquisition IDs, ordinary work counters and native/v2/v3 certificate payloads:
552 native plus 53 extension records, 651,784 combined payload bytes,
1,179,648 SQLite bytes and 125,493 gzip bytes. Native expansions stay at 505 and
propagation visits at 74,503. Cache state is never persisted. Instrumentation does
increase the two query/warm sidecars from about 786 KB to 903 KB or 899 KB.
Mean peak process RSS is 59.23/59.20/60.05 MB respectively; these small-process
observations do not establish a process-memory saving.

Complete-worker time charges setup, snapshots, validation, normalization, keying,
lookup, sizing, eviction, discovery, solving, checking, metadata scans, persistence,
warm/cold replay, sidecar serialization and compression. Source/import audits,
exhaustive truth checks, historical audits and posthoc profiles are outside worker
timing. No tests/builds/audits overlapped the completed timing workers.

## Correctness, resources and the next target

The safety argument is local: an immutable exact input determines a pure result
triple; a hit returns that same triple, and a miss computes it unchanged. Eviction
only removes opportunities. Query-local lifetime prevents one query's state from
being mistaken for another query's validation. Tests cover mutable caller input,
name transport, invalid equal-hash literals, empty/tautological/duplicate clauses,
large integers, eviction, disabled caching, exceptions and 1,000 small clause
combinations, followed by generated source/edit decision checks.

For a hit with input length L, snapshotting, literal validation and full-key
hashing/comparison still depend on L and integer bit lengths. Dictionary behavior
and eviction costs also remain; no worst-case constant lookup claim is made.
Relative cost is the original computation minus hit normalization/key generation,
plus all lookup/admission/eviction work. The retained cache charge is bounded by
the configured B. Neither statement bounds the arbitrary residual's solving or
proof size, and this implementation supplies no new uniform polynomial expansion
result or Lean theorem.

The next promising target is explicit reuse along already validated call paths:
pass the CNF/name-map/key triple from its producer to the next consumer instead
of rediscovering identity through a general dictionary. Start with repeated
normalization in native verification and child acquisition. The separate baseline
profile assigns 552 canonicalization calls / 0.08700 inclusive seconds to `_verify`
and 546 / 0.08263 seconds to `_visit`. In the 128 KiB arm these same sites take
0.12743 and 0.13059 instrumented seconds. The cache wrapper alone uses 0.07388
exclusive seconds; all three profiles reproduce their arm's exact counters and
certificates. Instrumentation affects paths unequally, so these times identify
work to investigate, not a substitute for the matched wall-time comparison.
Require a precise immutable identity contract,
preserve external-input validation and certificate checks, and measure all changed
paths, including warm queries. Merely enlarging this cache is not the next default
step. The 605 individual SQLite transaction exits remain a separate candidate;
batching needs an explicit atomicity/recovery design before it can be compared.

## Preservation and reproduction

Resume `experiments/results/cnf-query-canonical-cache/checkpoint.json`. The parent
archive and decisions are referenced unchanged rather than copied again: 28,886
native, 26 affine, 42 v1, 53 v2, 22 v3 and 34 discovery records. All 5,650 composed
records and 444 earlier pilot decisions remain readable. Trial archives preserve
the repeated acquisitions without adding duplicate mathematical history.

The artifact's README gives the commands. `report.json` holds matched timings,
`attribution.json` paired differences, `profile.json` separate instrumented
solve-only profiles, and `validation.json` chronological and historical checks.
Two validator setup failures (omitted zero counters and an optional control field)
are preserved under `failed-validation/`; neither affected the timing workers or
solver outputs.

All **1,262 full / 93 focused tests** pass. Validation covers 832 chronological
queries, 416 exact cache/control comparisons and 104 exhaustive truths. All 607
prior sources and 7,807 artifacts remain unchanged. The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. Final executable source ledger: **613**. The new manifest binds **52
artifacts**. Next preservation audit: **7,859 artifacts / 114 manifests**.
