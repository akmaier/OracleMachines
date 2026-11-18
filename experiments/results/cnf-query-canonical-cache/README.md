# Bounded canonicalization reuse: preserve the regression

Eight serial workers compare the previous single/known-quotient controls with
128 KiB and 8 KiB query-local caches in opposite orders. Each starts empty and
replays the same 104 sources. The larger cache avoids 19.57% of normalization
visits and 19.55% of serialized key bytes, but complete time rises 3.65%; the
smaller cache raises it 8.44%. Both complete-time paired deltas are positive at
each capacity. Warm queries have no cache hits. All certificates, acquisition
choices and answers match the known-quotient control exactly. Keep this optional;
there is no production speedup, extra SAT coverage or new unrestricted bound.
See [the analysis](../../../research/query-canonicalization-reuse.md).

The 128 KiB cache peaks at 131,018 conservatively charged object bytes and twenty
entries; 8 KiB peaks at 8,167 bytes and five entries. The cap excludes transient
construction, allocator overhead, counters and other solver state. All lookups
still snapshot and validate literals before exact dictionary comparison. Cache
state clears on success and failure and is never persisted.

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_query_canonical_cache.py prepare /tmp/cnf-canonical-new
python3 experiments/compare_cnf_query_canonical_cache.py /tmp/cnf-canonical-new
python3 experiments/validate_cnf_query_canonical_cache.py /tmp/cnf-canonical-new
python3 experiments/profile_cnf_query_canonical_cache.py /tmp/cnf-canonical-new
python3 -m unittest solver.test_cnf_query_canonical_cache solver.test_cnf_known_quotient solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Matched workers include setup, snapshot/validation, normalization, keying, cache
lookup/admission/eviction, discovery, solving, checking, metadata scans, publication,
warm/cold replay, sidecars and compression. Imports/source checks precede timing.
Truth/history audits, tests, builds and the separate profiles occur afterward.
No tests/builds/audits overlapped the matched workers. Profile times exclude setup,
metadata, warm/cold replay and compression; inclusive function times overlap and
instrumentation affects different paths differently.

`report.json` binds all eight worker reports and their archives. `attribution.json`
records paired changes and zero warm hits. `profile.json` reproduces exact outputs,
counters and archive digests for all three known-quotient arms, with canonical
caller counts. Two validator setup mistakes (missing zero counters and an optional
control field) are retained under `failed-validation/`. They did not alter solver
code, timing samples or previous artifacts.

## Preserve and resume

`checkpoint.json` references the exact parent union archive and all prior decisions
instead of storing another identical copy. It preserves **28,886 native / 26 affine /
42 v1 / 53 v2 / 22 v3 / 34 discovery records**, plus all **5,650 composed / 444 pilot
decisions**. No new mathematical result is added to those tables. Trial archives
retain every repeated acquisition, including the two unchanged control streams.

Validation passes **832 chronological query audits**, **416 exact cache/control
comparisons**, **104 exhaustive truths**, **144 choice checks** and **84 known-hit
checks**, followed by full old-history/table validation. All **607 previous sources /
7,807 artifacts / 113 manifests** remain unchanged. All **1,262 full / 93 focused
tests** pass; the full suite emits its 44 pre-existing SQLite warnings, and the
focused suite emits none. The **225-page manuscript** builds with all **64 prior
proof blocks** unchanged. Final source ledger: **613**.

The next target is direct reuse of validated immutable canonical results in native
verification/visitation, with exact identity and all external evidence checks
preserved. The general cache wrapper adds more work than it saves here. Individual
SQLite commits remain a separate atomicity/recovery investigation.

The final manifest binds **52 artifacts**. Next preservation audit: **7,859
artifacts / 114 manifests**.
