# Prefer a checked known quotient

Six serial workers compare cached single-block, all-block and known-target
policies on the old 68-query pilot followed by 36 excluded fresh sources. The new
policy checks at most the complete native quotient and the first-block native
quotient, preserving correct model-name transport and existing proof formats.

All arms return 42 SAT / 62 UNSAT. Four first-target hits include both SAT and
UNSAT. Compared with all blocks, native nodes fall **560 -> 552**, combined payload
falls **655,190 -> 651,784 bytes**, SQLite by 28,672 and gzip by 2,938 bytes. All eight
native savings occur in the original pilot; the fresh segment has the same 152
native additions in every arm. Thirty-eight lookups and fourteen extra transforms
are charged. Mean complete time rises 1.00% versus all blocks, with mixed paired
deltas, and 2.47% versus single block. The policy stays optional.
See [the analysis](../../../research/known-quotient-selection.md).

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_known_quotient.py prepare /tmp/cnf-known-new
python3 experiments/compare_cnf_known_quotient.py /tmp/cnf-known-new
python3 experiments/validate_cnf_known_quotient.py /tmp/cnf-known-new
python3 experiments/profile_cnf_known_quotient.py /tmp/cnf-known-new
python3 -m unittest solver.test_cnf_known_quotient solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

All workers start empty. The first 68 queries reproduce the old comparators.
Twenty-four new generated controls and twelve quotient-preserving wide edits are
excluded against every parent native/equivalence root. These are designed small
continuations, not representative arbitrary SAT. Source audits/imports precede
timing; setup, discovery, both transformations, canonicalization, checking, lookup,
acquisition, metadata scans, persistence, warm reuse, cold replay, sidecars and
compression are timed. Truth/chronology/history audits and posthoc profiling are
separate. No study tests/builds/audits overlapped the completed workers.

`attribution.json` checks all choices against records present before each query.
`profile.json` independently reproduces outputs, counters and archive payloads.
It identifies normalization and individual SQLite commits as major solve costs.
An exact census finds **469 normalization repeats within individual queries**,
covering 96.39% of repeated input literals. Peak per-query encoded input/result
state is 73,860 bytes, versus 1,448,226 over the stream. Next measure a bounded
per-query cache of normalized CNF, original names and full key, charging strict
validation, immutable snapshots, hashing, lookup, retained objects and eviction.
No normalization cache is implemented by this artifact.

## Preserve and resume

The union preserves **28,736 native / 26 affine / 42 v1 / 42 v2 / 11 v3 / 34
discovery records** byte-for-byte. It adds **150 native / 11 v2 / 11 v3** records,
for **28,886 native / 53 v2 / 22 v3**. Growth: **311,296 SQLite / 42,212 compressed
bytes**, retaining fresh results from all policies. All 5,650 composed records and
340 earlier pilot decisions remain readable, with 104 new decisions.

Use `experiments.cnf_known_quotient.KnownQuotientSolver` with the existing explicit
`MultiEquivalenceStore` reader. Recursive acquisition and production defaults are
unchanged. Known native hits can be positive or negative; extension-only targets
are not accepted as native dependencies.

All **1,253 full / 84 focused tests** pass (44 pre-existing SQLite warnings in the
full suite, none in focused tests). Validation covers 624 chronological queries,
104 exhaustive truths, 36 fresh exclusions, 48 exact choice audits and 28 known
hits across both orders, plus complete old/new histories. All 601 prior sources,
7,761 artifacts and 112 manifests remain unchanged. No new Lean or unrestricted
SAT bound follows.

The failed cold-reader dispatch setup is retained under `failed-reader-dispatch/`;
no completed sample is claimed. Its temporary acquisition database was removed
by the old cleanup path. The corrected harness preserves partial records/database
on future cold failures. The first profile comparison failed on integer model
keys versus JSON string keys; its source and failure are also retained. The final
profile normalizes representation and verifies exact counters/archive digests.

The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,253 full / 84 focused tests** pass. Final executable source
ledger: **607**. New manifest: **46 artifacts**, including the retained failed
setups and posthoc profile. Next preservation audit:
**7,807 artifacts / 113 manifests**.
