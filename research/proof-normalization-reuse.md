# Reuse normalization between acquisition and negative-proof checking

The new optional `ProofNormalizationSolver` retains pure normalization results
produced by `_visit` and reuses them only inside `_negative_child`. On the same
104-input catalog, a 128 KiB cap avoids 262 normalizations and 21.31% of ordinary
normalization literal visits. Mean query time falls 3.88%. Complete time falls
2.07% on average, but the second paired complete measurement regresses. This is
a modest, workload-specific improvement with a verified reduction in work;
it does not establish a reliable general runtime gain or expand SAT coverage.

## Evidence and mechanism

The preceding profile placed normalization above other exclusive costs. An
untimed census now finds that all 311 negative-child checks repeat an exact raw
residual from earlier in the same query. Its immediate predecessor is `_visit`
in 270 cases, a cover compiler in 34, and an excluded-child helper in seven.
There are also 53 repeated quotient-dependency inputs. The diagnostic preserves
the parent's decisions, counters and certificate bytes. Its retained raw-input
history is diagnostic overhead, excluded from runtime claims.

The implementation targets the 546 `_visit` producers and 311 negative-proof
consumers. Producers run the original normalizer, then store an immutable raw
tuple with its normalized CNF, original variable names and exact serialized key.
Consumers validate nonzero, exact Python integers before equality lookup:
`True` and `1.0` must not hit an entry for `1`. A hit substitutes only that triple.
The original referenced-key comparison, archive lookup and checked-UNSAT-child
requirement still execute. Cached normalization cannot authenticate an absent,
corrupt, positive or unrelated child. Other callers retain their original path.

The memo lasts for one source query and clears on success or failure. FIFO
eviction and oversize skipping affect performance only. No memo entry is written
to the proof archive. Inputs are copied before retention, and name maps remain
bound to the exact raw input; equivalent normalized formulas do not justify
interchanging their original names. The batched publication policy, its failure
handling and direct canonical-certificate checking remain unchanged.

## Matched costs

Six serial workers start from empty archives, with forward and reverse orders.
All use the same 32-record/256-KiB publication policy and direct cold reader.
Timing includes setup, snapshots, recognition, validation, keying, admission,
byte charging, eviction, solving, proof checking, metadata, persistence,
warm/cold replay, sidecars and compression. Imports, history checks, profiling
and tests are outside worker timing.

| Measurement | Parent batching | 128 KiB memo | 32 KiB memo |
|---|---:|---:|---:|
| Normalizer calls | 1,163 | 901 | 985 |
| Normalization literal visits | 119,547 | 94,069 | 105,001 |
| Reused negative-child results | 0 | 262 / 311 | 178 / 311 |
| Serialized key bytes | 678,378 | 578,276 | 620,930 |
| Admissions / evictions / oversized skips | 0 / 0 / 0 | 546 / 59 / 0 | 542 / 274 / 4 |
| Peak retained charge, bytes | 0 | 131,020 | 32,739 |
| Peak retained entries | 0 | 13 | 8 |
| Mean query time, seconds | 0.325621 | 0.313001 | 0.320946 |
| Mean complete time, seconds | 0.557509 | 0.545952 | 0.554061 |

The 128 KiB query deltas are -22.37 and -2.87 ms; complete deltas are -24.98
and **+1.86 ms**. The 32 KiB query deltas are -12.95 and **+3.61 ms**; complete
deltas are -13.31 and **+6.42 ms**. Keep both orders and regressions. Two short
replays do not support a statistical speedup claim. Warm queries have no memo
producer/consumer work, and cold readers are identical; timing differences there
are not evidence of normalization-reuse savings.

All arms retain exactly 552 native and 53 extension certificates, 651,784 combined
key/payload bytes, 1,179,648 SQLite bytes and 125,493 compressed bytes. Answers,
models, quotient choices, 505 expansions, proof-check counters and 104 commits
are identical. Only ordinary normalization/key serialization and new memo work
counters differ. Persistent storage does not shrink.

## Memory and complexity

Admission charges the dictionary's actual size plus a conservative sum of tuple,
string and integer object sizes. Shared references are deliberately overcounted.
The largest input integer bounds raw/name integer charges even when normalization
removes a tautology or collapses an empty clause. The cap holds after each
operation for retained memo objects; it excludes transient snapshots, resizing,
allocator overhead, the existing proof cache and whole-process memory.

An independent untimed object-graph walk checks all 546 admissions in each memo
arm. Deduplicated peak graph sizes are 83,489 and 25,418 bytes, below respective
conservative charges. Mean worker RSS is 60.62 / 60.78 / 60.72 MB for control /
128 KiB / 32 KiB. This provides no process-memory reduction claim. Aggregate
counter sums of per-query peaks are not global peaks; the report's dedicated
peak fields contain the actual maxima.

A hit still scans and hashes the raw formula; it is not constant-time access
independent of input size. Producers still normalize, copy and size their input.
Integer width, hashing/equality, tuple allocation, eviction and proof lookup must
be charged. Fixed retained space neither bounds the number of distinct residuals
nor removes arbitrary SAT's unresolved worst-case expansion cost.

## Validation and preservation

The audit checks 624 chronological queries, 416 exact alternative/control pairs,
104 exhaustive truths, 144 quotient choices and 84 known hits. A separate memo128
replay independently validates the visible proof archive after every one of its
104 commits. Both old readers validate the complete preserved union; all 28,886
canonical fixed points and 4,961 representation mutations remain consistent.

The unchanged parent archive contains 28,886 native, 26 affine, 42 v1, 53 v2,
22 v3 and 34 discovery records, with 5,650 composed and 444 pilot decisions.
All 625 earlier source fingerprints and 7,947 artifacts across 116 manifests are
verified unchanged. No duplicate union or new mathematical answer is added.
The checkpoint is
`experiments/results/cnf-proof-normalization-reuse/checkpoint.json`.

Nine new tests cover invalid equal-hash literals, exact name maps, mutable caller
inputs, wrong/positive/missing children, strict capacity and oversize cases,
failure cleanup, commit rollback/retry and warm reuse. All **1,292 full / 123 focused tests** pass. The full suite emits 44 unclosed-SQLite
ResourceWarnings versus 43 in the parent, at unchanged source/stdlib files with
a different garbage-collection emission distribution; focused tests emit none.
This existing suite issue is not fixed here. The **227-page manuscript** builds
without warnings, with all **64 earlier proof blocks** unchanged. The final source
ledger contains **632** fingerprints. Build and preservation checks are recorded
alongside the checkpoint. This adds no Lean theorem or change to the earlier proof blocks.

## Next investigation

Normalization remains the largest exclusive site: memo128 leaves 901 calls,
0.05987 exclusive / 0.14642 inclusive profiled seconds. Restriction remains
780 calls / 0.07031 inclusive seconds. Memo admission sizing itself consumes
0.02845 inclusive seconds; its 53,773 producer literal units and 30,259 consumer
validation units explain why skipped normalizations yield only a small net gain.
Inclusive timings overlap and must not be added as independent costs.

The next candidate is an ordered-clause residual path: 501 of 546 producer inputs
already have sorted, distinct, tautology-free clause literals, covering 47,894
literal units. Restrictions preserve that local property. They do **not** preserve
global clause order, clause uniqueness or compact variable names. A useful fast
path must check or transport the local invariant while retaining exact global
deduplication, renaming, name maps and keys. Compare it directly with the parent
and this memo on the same inputs, including novel and adversarial edits. Do not
promote it before measuring the recognition and fallback cost.

Second, investigate shorter-lived producer-to-check transport that avoids the
memo's repeated charging and hashing. Extending to cover/quotient helpers without
measuring their extra admission cost could reproduce the earlier general-cache
regression. Structural coverage, interacting unresolved components and uniform
resource bounds remain separate open research problems.
