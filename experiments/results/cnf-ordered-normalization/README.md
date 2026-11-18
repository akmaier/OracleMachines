# Checked clause-order normalization

The optional ordered path validates every literal, recognizes strictly ordered
clauses, checks them for complementary pairs with two pointers, and falls back
to the original set/sort method otherwise. Signed compact renaming preserves
order, so the second clause sort is unnecessary on both paths. Global clause
deduplication/sorting, support sorting, name maps and full keys remain exact.
See the [analysis and correctness argument](../../../research/ordered-residual-normalization.md).

Six serial workers replay the same 104 inputs from empty archives, comparing
batching, the preceding 128-KiB memo and the ordered path in opposite orders.
The ordered path avoids 96,099 sort calls, but mean query time improves only
2.17% and complete time 1.68% against batching. It remains 1.19% slower than the
memo on queries; warm time regresses 2.95%. All samples and regressions remain.
There is no default change, new structural coverage or general speedup claim.

## Reproduce

From the repository root, choose a new destination:

```sh
python3 experiments/compare_cnf_ordered_normalization.py prepare /tmp/cnf-ordered-new
python3 experiments/compare_cnf_ordered_normalization.py /tmp/cnf-ordered-new
python3 experiments/validate_cnf_ordered_normalization.py /tmp/cnf-ordered-new
python3 experiments/profile_cnf_ordered_normalization.py /tmp/cnf-ordered-new
python3 -m unittest -v solver.test_cnf_ordered_normalization solver.test_cnf_proof_normalization_reuse solver.test_cnf_publication_batches solver.test_cnf_canonical_verify solver.test_cnf_query_canonical_cache solver.test_cnf_known_quotient solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

The eight new tests passed before freezing the timed protocol. Timing includes
setup, snapshots, recognition/fallback, normalization, keying, discovery, proof
checking, metadata, persistence, warm/cold replay, sidecars and compression.
Imports and source checks precede timing; truth/history audits, profiles, full
tests and builds follow all workers. No failed implementation or timed run was
discarded. Inclusive profile times overlap and must not replace wall times.

## Checks and limits

All ordered decisions, models, ordinary counters and proof bytes match batching.
All arms retain 552 native / 53 extension records, 505 expansions, 104 commits,
651,784 combined key/payload bytes and 1,179,648 SQLite bytes. The ordered path
retains no additional cache; transient snapshots, global sets, tuple comparisons,
integer width and allocator overhead remain. Measured process memory does not
decrease. Identical cold readers/archives imply no cold benefit from this change.

Validation covers 624 chronological queries, 416 exact alternative/control pairs,
104 exhaustive truths, 144 quotient choices, 84 known hits and independent proof
validation after all 104 ordered-arm commits. Both old readers validate the
preserved union. The ordered normalizer matches the original on 28,886 archived
CNFs and 4,961 mutations. Tests also exhaust small clauses/formulas and cover
duplicates, tautologies, invalid literals after empty clauses, sparse/huge names,
restriction counterexamples, seeded edits, warm reuse and rollback/recovery.

The 28,886 native / 26 affine / 42 v1 / 53 v2 / 22 v3 / 34 discovery records and
5,650 composed / 444 pilot decisions remain unchanged. The checkpoint references
the original union without copying it. All 632 previous source fingerprints and
7,990 artifacts across 117 manifests are verified unchanged. The final ledger
contains 638 fingerprints; the manifest binds this checkpoint's artifacts.

All 1,300 full / 131 focused tests pass. The full suite retains 44 unclosed-SQLite
ResourceWarnings at unchanged files; focused tests emit none. This existing
suite issue is not fixed here. The 228-page manuscript builds without warnings
and preserves all 64 earlier proof blocks. No Lean theorem or uniform polynomial
expansion bound is added.

Next: freeze larger held-out mixed/edited/unresolved CNFs and measure discovery,
fresh acquisition and retained proof-state growth across the preserved variants.
The current small gains do not justify selecting another optimization solely
from this repeatedly measured catalog. Direct invariant transport and combining
ordering with memo reuse remain untested candidates.
