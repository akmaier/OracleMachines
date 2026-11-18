# Targeted acquisition-to-proof normalization reuse

An optional memo retains pure normalization triples from `_visit` and supplies
them only to `_negative_child`. Full-key matching and checked-UNSAT-child proof
requirements remain unchanged. The 128-KiB arm avoids 262 normalizations / 25,478
literal visits (21.31%). Mean query time improves 3.88%; mean complete time
improves 2.07%, but its second paired measurement regresses. The 32-KiB arm's
second query measurement also regresses. All samples are preserved. See the
[analysis](../../../research/proof-normalization-reuse.md).

The diagnosis was performed before protocol freezing. It binds its own source
and parent checkpoint and reproduces parent decisions, counters and certificate
digests. Six serial workers then compare the unchanged batched control with
128-KiB and 32-KiB memos in forward/reverse order. All replay the same 104 inputs
from empty archives; no new coverage or mathematical answer is claimed.

## Reproduce

From the repository root, choose a new destination:

```sh
python3 experiments/inspect_cnf_residual_normalization.py /tmp/cnf-proof-reuse-new
python3 experiments/compare_cnf_proof_normalization_reuse.py prepare /tmp/cnf-proof-reuse-new
python3 experiments/compare_cnf_proof_normalization_reuse.py /tmp/cnf-proof-reuse-new
python3 experiments/validate_cnf_proof_normalization_reuse.py /tmp/cnf-proof-reuse-new
python3 experiments/profile_cnf_proof_normalization_reuse.py /tmp/cnf-proof-reuse-new
python3 -m unittest -v solver.test_cnf_proof_normalization_reuse solver.test_cnf_publication_batches solver.test_cnf_canonical_verify solver.test_cnf_query_canonical_cache solver.test_cnf_known_quotient solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Workers time setup, all memo maintenance and strict literal checks, normalization,
discovery, solving, proof checking, metadata, publication, warm/cold replay and
compression. Profiling, diagnostic retention, exhaustive truth, history audits,
object-graph sampling and tests are outside matched worker timing. All workers
finish before those later checks. No failed candidate run was discarded.

## Boundaries and preservation

The fixed retained-object caps include conservative tuple/string/integer charges
and actual dictionary size after operations. They exclude transient snapshots,
dictionary resizing, allocator overhead and full-solver memory. An independent
untimed replay checks actual object graph size against the conservative charge
after all 546 producer admissions per arm. The 128-KiB arm peaks at 131,020 charged
bytes / thirteen entries, with 83,489 actual graph bytes. Memo state clears on
success and failure; it never authenticates a proof or survives a source query.

All arms reproduce the same 552 native / 53 extension records, 505 expansions,
104 commits, 651,784 key/payload bytes and 1,179,648 SQLite bytes. Warm queries have
no memo producers or consumers; cold readers are identical. No cold-replay,
process-memory or persistent-storage reduction is attributed to this change.

Validation covers 624 chronological queries, 416 exact alternative/control pairs,
104 exhaustive truths, 144 quotient choices, 84 known hits and independent proof
validation after all 104 memo128 commits. Both old readers validate the complete
parent union; all 28,886 fixed points and 4,961 representation mutations agree.
The 28,886 native / 26 affine / 42 v1 / 53 v2 / 22 v3 / 34 discovery records and
5,650 composed / 444 pilot decisions remain unchanged. The checkpoint references
the old archive rather than duplicating it. All 625 earlier source fingerprints
and 7,947 artifacts across 116 manifests are checked unchanged.

All 1,292 full / 123 focused tests pass. The full suite emits 44 unclosed-SQLite
ResourceWarnings versus 43 in the parent; emission locations shift among unchanged
files as garbage collection occurs. Focused tests emit none. The warning counts
and distribution delta are retained in `checks.json`; this issue remains open.
The 227-page manuscript builds without warnings and preserves all 64 proof blocks.
The final ledger contains 632 source fingerprints; `manifest.json` binds this
checkpoint's artifacts.

Next: exploit clause-local ordering in residuals while preserving exact global
normalization and name maps. The memo still pays 0.02845 profiled inclusive seconds
for admission sizing, so shorter-lived direct transport is another candidate.
Neither candidate is implemented or counted as a saving here. The optional memo
adds no structural coverage, Lean theorem or unrestricted SAT resource bound.
