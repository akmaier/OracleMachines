# Exact binary-core discovery reuse

Six serial workers compare compact acquisition, an in-memory discovery cache and
a persisted cache in opposite orders on the same 68-input catalog. All proof
payloads and decisions match. Twenty-two hits avoid repeated graphs: acquisition
SCC visits fall **8,552 -> 4,744 (44.53%)**. The 34 entries require **11,906 key/value
bytes / 25,887 Python-object bytes**. Persistent cold validation recomputes every
outcome, so acquisition plus replay SCC work is **10.94% above** the control.
Memory total timing has mixed signs; persistent total changes are small with mixed
query timing. Both APIs remain optional. No fresh coverage or production speedup
is claimed. See [the full analysis](../../../research/binary-core-discovery-reuse.md).

## Reproduce

From the repository root, use a new output destination:

```sh
python3 experiments/compare_cnf_binary_core_cache.py prepare /tmp/cnf-core-new
python3 experiments/compare_cnf_binary_core_cache.py /tmp/cnf-core-new
python3 experiments/validate_cnf_binary_core_cache.py /tmp/cnf-core-new
python3 -m unittest solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

`protocol.json` binds the unchanged catalog and sources before acquisition. Every
worker starts empty. Source audits and imports precede timing; extraction, keying,
discovery, transport, checking, acquisition, metadata scans, publication, warm
source replay, cold proof/cache validation, sidecars and compression are timed.
Truth, chronology and history audits and final report writing are outside worker
timing. No study tests/builds/audits ran concurrently with the timed workers.
Public `solve` times are recorded separately in `attribution.json`; query timing
also includes audit metadata and retained-cache serialization.

## Preserve and resume

The checkpoint preserves **28,691 native / 26 affine / 42 v1 / 42 v2** certificate
payloads byte-for-byte and adds 34 discovery entries plus 68 explicit decisions.
It retains all 5,650 composed records and 204 old pilot decisions; four alternative
native roots remain in the trial archives. Union growth is **36,864 SQLite /
2,681 compressed bytes**. Trial growth is 36,864 SQLite / 3,618 compressed bytes.

Use `experiments.cnf_binary_core_cache.CachedBinaryEquivalenceSolver` with its
explicit compact proof reader. `persistent_cache=False` retains discovery only
for the session while answer certificates still persist. The discovery table is
not an answer authority. Cold cache loading recomputes complete recognizer outcomes
before trusting them; transported trees are always checked against current source
clauses. Binary or coordinate changes miss the key. The inherited `reuse` flag
controls certificate reuse, separately from the discovery cache.

All **1,236 tests / 67 focused tests** pass. Full tests retain 44 pre-existing
SQLite warnings; focused tests have none. Checks include 4,096 small binary-core
combinations with two wide-clause choices, malformed entries, coordinate/edge
changes, full solver truth/payload agreement, 408 chronological query audits,
68 exhaustive truths and complete old/new histories. All 591 previous sources,
7,683 artifacts and 110 manifests remain unchanged.

Next investigate multi-block substitution on twelve diagnosed sources, pricing
child solving and certificate size. Propagation (51,326 visits) and native
expansion (358 nodes) remain unchanged. Recursive graph sharing and cheaper cold
validation are separate open targets; no new Lean or unrestricted-SAT bound follows.

All **1,236 full / 67 focused tests** pass, with 44 pre-existing SQLite warnings
in the full suite and none in the focused suite. The **223-page manuscript**
builds cleanly and all **64 previous proof blocks** are unchanged. Final source
ledger: **596**. New manifest: **39 artifacts**. Next preservation audit:
**7,722 artifacts / 111 manifests**.
