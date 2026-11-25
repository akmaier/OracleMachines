# Pass prepared residuals into native publication

Checkpoint: 25 November 2026. The [layered compiler](layered-feedback.md) repeated
normalization while constructing and checking the same residual. Direct reuse
at publication reduces compilation time 7.43% and complete local trial time
3.72% on the same fifteen roots. Every case improves in both measured totals.
Certificates, archive sizes, proof-rule checks and coverage are unchanged.
Ordinary local solving remains faster overall.

## Why direct reuse

The earlier [general canonicalization cache](query-canonicalization-reuse.md)
reduced normalization counters but increased total cost. Its snapshots, lookups,
validation and admission work remain a preserved negative result. The present
experiment passes a producer's result directly to its next consumer, without
content matching or a retained cross-query cache.

`prepare_frame` performs ordinary normalization and key construction. Its result
contains the immutable normalized CNF, original-name map, key and a publisher
closure. The publisher accepts a proof only. It constructs its own fresh CNF and
header from that producer's result; callers cannot supply a replacement header,
key or canonical triple. The verifier's name map must be the identity map of the
normalized variables, not the producer's original-name map. Sparse-name tests
check this distinction.

During publication, exactly one call on that private header object consumes the
prepared canonical triple. The original canonicalizer is restored before proof
checking can visit a child, and again in `finally` on success or failure. Equal
but different inputs receive ordinary normalization. The original verifier still
checks the key, header equality, every proof rule and every child relation.
External `_store` calls retain their original input validation. The source is
snapshotted by normalization, so later edits to the caller's input cannot change
the prepared result.

This relies on exclusive synchronous use of the unchanged native verifier,
as do the existing compiler and handoff experiments. Private-state tampering,
replacement verifier semantics and concurrent mutation are outside that contract.
The handoff is a representation result, not permission to accept a proof.
All old seed, closure, guard, support and layer checks remain unchanged.
Binary-prefix and outer support-wrapper publications retain the original path.

A separate variant also passes frames across unchanged proof contexts: agreeing
already-fixed steps, terminal reason leaves and descent into an older proof layer.
It never passes a frame across an added assignment. Conditional leaf containment,
assumption checks and unit reconstruction still run. Both variants are optional;
no production default or certificate format changes.

## Matched measurements

The study replays all fifteen previously recognized layered-feedback roots.
All were already UNSAT in inspected snapshots. Four methods run in forward and
reverse order for each case, in 120 isolated workers. Fresh solving, the unchanged
compiler, publication reuse alone (`headers`), and publication plus unchanged-context
reuse (`prepared`) each receive identical inputs. Timing includes frame creation,
checks, method binding and cleanup; complete trials add warm checking, both cold
readers and persistence. Acquisition/discovery, unresolved fallback, input loading,
startup and final audits remain additional. There is no new coverage or holdout.

| Summed per-case mean | Fresh | Baseline | Headers | Prepared |
|---|---:|---:|---:|---:|
| Solve/compile (s) | 2.65964 | 3.88032 | 3.59202 | 3.59831 |
| Warm check (s) | 0.02844 | 0.17037 | 0.16962 | 0.17139 |
| Cold readers (s) | 2.77431 | 2.82484 | 2.81667 | 2.84743 |
| Persistence (s) | 0.99466 | 1.07608 | 1.08010 | 1.09296 |
| Complete trial (s) | 6.52243 | 8.00489 | 7.70687 | 7.76767 |
| Encoded bytes | 12,209,959 | 8,989,382 | 8,989,382 | 8,989,382 |
| Records | 959 | 3,477 | 3,477 | 3,477 |

Publication reuse improves compilation and complete time on all fifteen cases.
The two order-paired aggregate compilation differences are -0.32939/-0.24722
seconds; complete differences are -0.33221/-0.26383 seconds. Two opposite orders
are descriptive evidence, not a statistical production guarantee. Cold and warm
checks use the unchanged paths; their timing differences are not algorithmic gains.

Adding context reuse saves more operations but gives no aggregate timing advantage
over headers alone: compilation is 0.18% higher and complete time 0.79% higher.
It improves compilation on ten cases and regresses on five relative to headers.
Against the original compiler it improves fourteen cases and regresses on
`new-40-65`; preserve this exception. Carry the publication-only arm forward as
the measured cost baseline, with the full variant available for comparison.
Header compilation still takes 35.06% more time than fresh solving; complete
header trials take 18.16% more.
No end-to-end advantage over ordinary solving has been established.

## Avoided work, exact authority and memory

There are 3,415 header handoffs. They avoid re-normalizing 595,857 literal slots:
native normalization visits fall from 3,147,103 to 2,551,246. Native serialized key
bytes fall from 8,661,829 to 6,097,932. These are native-stage counters; original
source/support preparation remains additional. All 3,477 publication verifications,
670,538 verified literal slots, child checks, insertions and six authority-table
payloads remain identical. The old baseline also exactly reproduces its earlier
checkpoint's counters and tables. Both independent readers accept all thirty
unique archive/root pairs. The three compiler methods have the same archives;
no extra mathematical history is added.

Headers mode builds 6,815 frames. The full variant reuses 98 unchanged contexts,
reducing frame builds to 6,717, compiler restriction visits from 2,012,031 to
1,986,815, and native normalization visits to 2,535,308. Native verification's
1,278,612 restriction visits remain unchanged. This remaining child-relation work
is a more substantial target than claiming a gain from the 98 extra handoffs.

There is no persistent preparation cache. Frames hold existing canonical data,
an identity-name tuple and a publisher closure for their call lifetime. Identity
name construction costs O(V) words/work per frame with V normalized variables;
header list construction and the original proof checks still cost input-dependent
work. Along active recursion, extra identity tuples and control objects can use
O(sum(V_i+1)) words, in addition to the compiler's existing CNFs, keys and proof
state. No fixed byte cap or whole-process memory bound is claimed.

Peak trial RSS is 84.51 MB fresh, 66.49 MB baseline, 66.42 MB headers and 66.47 MB
prepared. Differences among the compiler arms do not establish a memory saving.
A separate diagnostic on the largest previously exposed regression traces Python
allocations only during compilation: peak bytes are 4,851,938 / 4,855,058 /
4,843,514 for baseline/headers/prepared. Inputs, pre-existing allocations, native
allocations and allocator retention lie outside that scope. It reproduces exact
counters and proof digests, and verifies that no canonicalizer override remains.
The small differences support no general memory claim.

## Validation and next target

All 1,919 tests pass, including 54 focused checks. New tests cover 1,111 small
input representations, sparse names, mutable source snapshots, invalid integer
lookalikes, false proofs, missing children, restoration on exceptions, guarded
proofs, unchanged full/support certificates, warm reuse and both cold readers.
The manuscript builds with all 64 prior proof blocks intact. Validation preserves
186 manifests, 25,188 artifacts and 1,068 sources; the checkpoint binds 1,072
sources. All earlier archives and cumulative tables remain unchanged. Existing
full-suite SQLite warnings are recorded; focused tests have none.

Coverage remains 193/246 post-binary events, with 53 unresolved cases. Twenty-one
changed closures retain 120 additional assignments and remain the next bounded
coverage opportunity. For cost, investigate repeated child-cofactor construction
and normalization with exact relation checks; publication-only reuse is the new
measured compiler baseline. This result neither bounds proof size nor supplies
an efficient complete partition of arbitrary SAT.

Resume [the checkpoint](../experiments/results/cnf-prepared-publication/checkpoint.json).
The [analysis](../experiments/results/cnf-prepared-publication/analysis.json),
[paired deltas](../experiments/results/cnf-prepared-publication/paired-deltas.json)
and [memory diagnostic](../experiments/results/cnf-prepared-publication/memory-diagnostic.json)
retain both improvements and regressions. Earlier open closures remain in their
original layered-feedback artifact.
