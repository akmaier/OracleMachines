# Compact equivalence certificate comparison

Version two stores only the format, negative answer and two-tree evidence. Its
canonical full source key and checked substitution reconstruct the source and
native UNSAT child. Old version-one records remain readable and unchanged;
native recursive search never reads either extension table.

Six serial workers compare the native control, original quotient API and compact
API on the same 68-input catalog from empty archives. All return 21 SAT / 47 UNSAT.
Between quotient versions, all 68 chronological acquisitions, native payloads,
source models, search/discovery counters and 42 reconstructed negatives match.

Equivalence storage falls **68,878 -> 26,998 bytes (60.80%)**. Combined payload
falls to **492,731 bytes**, 6.17% below the native control, although the combined
certificate count stays 440 versus 420. SQLite falls 61,440 bytes versus v1, gzip
1,172 bytes. Complete-worker paired deltas have mixed signs, and query time
remains 3.93% above the native control. Both APIs remain optional. This changes
representation, not coverage or native solving work.
See [the analysis](../../../research/compact-equivalence-certificates.md).

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_compact_equivalence.py prepare /tmp/cnf-compact-new
python3 experiments/compare_cnf_compact_equivalence.py /tmp/cnf-compact-new
python3 experiments/validate_cnf_compact_equivalence.py /tmp/cnf-compact-new
python3 -m unittest solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

`workload_origin` binds the preceding pilot's exact catalog. Its familiarity
labels describe that original selection, not new inputs to this checkpoint.
Workers run serially in opposite orders without concurrent study tests/builds/
audits. Complete time includes setup, discovery, acquisition, checking, metadata
scans, persistence, warm queries, cold replay, sidecar writing and compression.
Imports/source audits precede timing; truth checks, union/history audits and final
report writing are outside worker timing. The inherited preparation bindings
are unchanged and checked explicitly by the finalizer.

## Preserve and resume

`checkpoint.json` preserves **28,691 native payloads / twenty-six affine records /
42 v1 equivalence records** byte-for-byte. It adds 42 v2 alternatives and 68
explicit compact decisions alongside 5,650 old composed and 136 old pilot records.
No new native or v1 payload is inserted; four alternative native roots stay in
trial archives. Keeping both versions grows the union by 69,632 SQLite / 3,701
compressed bytes. This is separate from the smaller compact-only trial archive.
The API is `experiments.cnf_compact_equivalence.CompactBinaryEquivalenceSolver`,
with `CompactEquivalenceStore` for explicit negative roots and legacy fallback.
Old native and affine authorities remain unchanged.

All **1,228 tests**, **59 focused tests**, 408 chronological dependency audits,
68 exhaustive truth tables, warm reuse and full old/new histories validate.
Eight new tests include 4,096 cross-version acquisitions, canonical-key rejection,
wrong source/child publication, missing/positive dependencies, corrupt evidence,
both formats coexisting, old-only/native-only archives, edits and disabled leaves.
The full suite retains 44 pre-existing SQLite warnings; focused tests have none.
All 586 prior sources, 7,642 artifacts and 109 manifests remain unchanged.

Next reuse the unchanged catalog's 22 repeated binary cores with explicit index
transport, invalidation and cache/cold accounting. The compact format leaves SCC
work unchanged. Multiple-block quotients, prepared production and recursive native
integration remain open. No new Lean theorem or unrestricted-SAT bound is claimed.

The **223-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **591**. New manifest: **41
artifacts**. Next preservation audit: **7,683 artifacts / 110 manifests**.
