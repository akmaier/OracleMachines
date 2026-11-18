# Bounded publication with dependency-closed committed prefixes

Six serial workers compare direct verification, a one-record publication adapter
and a 32-record/256-KiB adapter in forward/reverse order. All replay the same 104
sources from empty archives. Batching reduces commits **605 -> 104** and mean
query time **35.55%**, with both orders improving. Against the one-record adapter,
query time improves **36.30%**. Exact outputs, non-batch work counters, native/v2/v3
payloads and final storage are unchanged. See
[the analysis](../../../research/bounded-publication-batches.md).

Successful answers flush their dependency chain before returning. Failed queries
retain committed prefixes, roll back pending writes and invalidate checked aliases
of pending keys. Uncertain rollback requires reopening. Partial-query visibility
changes: unfinished work in the current batch can be lost. This is an optional
exclusive-owner experiment, not a default/format change or general SAT result.

Peak pending state is **27 records / 39,747 encoded payload bytes / 17,086 charged
pending-key object bytes**. The timed workload does not reach the configured caps;
tests exercise smaller cuts and oversized single records. Separate journal
sampling rises **49,760 -> 103,112 bytes**. The caps exclude journals, page caches,
allocator overhead, existing checked proofs and lock duration. No process-memory
saving is claimed.

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_publication_batches.py prepare /tmp/cnf-batches-new
python3 experiments/compare_cnf_publication_batches.py /tmp/cnf-batches-new
python3 experiments/validate_cnf_publication_batches.py /tmp/cnf-batches-new
python3 experiments/profile_cnf_publication_batches.py /tmp/cnf-batches-new
python3 -m unittest -v solver.test_cnf_publication_batches solver.test_cnf_canonical_verify solver.test_cnf_query_canonical_cache solver.test_cnf_known_quotient solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Workers include setup, discovery, normalization, proof checking, byte sizing,
metadata, batching/commit, warm/cold replay, sidecars and compression. Imports and
source checks precede timing; tests/builds/audits/profiles follow all workers.
`profile.json` separately reproduces each arm's outputs/counters/digests and samples
journal sizes on additional replays. Instrumented times and overlapping inclusive
times must not be substituted for matched wall times.

Observed complete-time reductions are 26.87% versus direct control and 24.24%
versus the one-record adapter. The first direct cold sample is unusually slow
(0.14304 seconds versus 0.08365 in its second order); all arms use the same reader
on identical archives, so this cold variation is not a batching improvement.
Both paired query deltas improve independently. The one-record adapter's query
overhead is 1.18%; warm queries have no publication commits.

## Preservation and validation

`checkpoint.json` references the unchanged parent union and histories: **28,886
native / 26 affine / 42 v1 / 53 v2 / 22 v3 / 34 discovery records**, and all **5,650
composed / 444 pilot decisions**. No duplicate union archive or new mathematical
answer is added. All **619 previous sources / 7,904 artifacts / 115 manifests**
remain unchanged.

Validation passes **624 chronological queries / 416 alternative-control comparisons /
104 exhaustive truths / 144 choices / 84 known hits**. The extra prefix replay
independently verifies all visible native/extension proofs after **104 commits**.
Both readers still validate the complete old archive; 28,886 normalizer fixed
points and 4,961 representation mutations agree with the old criterion.

All **1,283 full / 114 focused tests** pass. New tests cover count/byte bounds,
oversized records, rollback and checked-state invalidation, failures before/after
commit, rollback poisoning, ignored duplicate accounting, warm use, and process
exit followed by writable recovery/read-only proof verification. Power loss and
concurrent writers are not tested. The full suite emits 43 SQLite warnings at
pre-existing sites; the focused suite emits none. The initial test fixture
miscounted a unit query's stored residual; its source/log are preserved under
`failed-test/`.

The **227-page manuscript** builds with all **64 earlier proof blocks** unchanged.
Final source ledger: **625**. The next measured bottleneck is ordinary residual
normalization (1,163 calls); investigate exact raw-result reuse across acquisition
and proof checking, preserving source/conditioning identity and name maps.

Final executable source ledger: **625**. The new manifest binds **43 artifacts**;
next preservation audit: **7,947 artifacts / 116 manifests**.
