# Direct canonical-form recognition with unchanged proof rules

Six serial workers compare the known-quotient control, the previous 128 KiB cache
and direct recognition in forward and reverse orders. All replay the same 104
inputs from empty archives. Direct recognition replaces 552 sorting/renaming
normalizations with explicit canonical-form checks. Mean query time falls 5.79%,
cold replay 18.12% and complete time 6.63% against the known-quotient control; both
paired query/cold/complete deltas improve. Warm deltas remain mixed. Exact answers,
models, choices, semantic proof counters, payloads and storage remain unchanged.
See [the analysis](../../../research/direct-canonical-verification.md).

This optional reader validates strict integer literals, strict literal/clause
order, tautology exclusion, compact support and the empty-clause collapse. The
checked immutable triple is consumed once by the original verifier, which retains
every key, witness and negative-proof check. Both acquisition and cold replay use
the same recognizer in the `linear` arm; unchanged-reader audits follow. No
canonical cache is retained. Temporary sets, tuples, maps and key strings still
cost work and space. There is no new SAT coverage or general performance claim.

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_canonical_verify.py prepare /tmp/cnf-direct-new
python3 experiments/compare_cnf_canonical_verify.py /tmp/cnf-direct-new
python3 experiments/validate_cnf_canonical_verify.py /tmp/cnf-direct-new
python3 experiments/profile_cnf_canonical_verify.py /tmp/cnf-direct-new
python3 -m unittest solver.test_cnf_canonical_verify solver.test_cnf_query_canonical_cache solver.test_cnf_known_quotient solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Worker time charges setup, direct recognition, source/residual normalization,
keying, discovery, solving, checking, metadata scans, publication, warm/cold replay,
sidecars and compression. Imports/source audits precede timing. Truth/history
audits, tests, builds and separate profiles occur afterward; none overlap the
matched workers. Instrumented profile times exclude setup/metadata/warm/cold/
compression and are not comparator wall times. Inclusive times overlap.

`report.json` binds all six worker reports/archives. `attribution.json` records
paired differences. `profile.json` verifies identical outputs/counters/digests per
arm and includes a separate exact-output census. The census finds only 45 `_visit`
calls with an earlier normalized output; its diagnostic retained state is not an
implemented transport mechanism or an uncharged production cache. The initial
test-generator sample-range mistake is preserved under `failed-test/`; it occurred
before source freezing and all timed workers.

## Preservation and next target

`checkpoint.json` references the unchanged parent archive and all decision files:
**28,886 native / 26 affine / 42 v1 / 53 v2 / 22 v3 / 34 discovery records**, and
all **5,650 composed / 444 pilot decisions**. No duplicate mathematical history
or new certificate format is introduced. Trial archives retain every acquisition.

Validation passes **624 chronological queries**, **416 alternative/control query
comparisons**, **104 exhaustive truths**, **144 choices / 84 known hits**, and full
old histories. Both readers verify every native record with matching semantic
proof counters. All **28,886 canonical fixed points** and **4,961 representation
mutations** agree with the original normalizer. All **613 previous sources /
7,859 artifacts / 114 manifests** remain unchanged.

All **1,271 full / 102 focused tests** pass; the full suite has 43 SQLite warnings at pre-existing
sites and the focused suite has none. The **226-page manuscript** builds
cleanly with all **64 previous proof blocks** unchanged. Final source ledger: **619**.

The largest remaining exclusive profile cost is **605 individual SQLite commits**.
Next investigate bounded batching with durable dependency closure, explicit
partial-query visibility, rollback/cache invalidation and fault/reopen tests.
It is a prospective experiment, not an implemented saving. Direct normalized-result
transport at the 45 visitation opportunities is the smaller secondary target.

The first seal expected the parent full-suite warning count of 44; this run emitted
43. The omitted warning was at an unchanged affine-pattern site. The failed seal
source/log are retained under `failed-seal/`; the corrected seal checks both the
actual count and that all normalized warning sites/counts are within the parent.

Final executable source ledger: **619**. The new manifest binds **45 artifacts**;
next preservation audit: **7,904 artifacts / 115 manifests**.
