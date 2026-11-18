# Simultaneous binary-equivalence blocks

Six serial workers compare the previous cached single-block solver with uncached
and cached all-block solvers on the same 68 inputs from empty archives. Twelve
sources receive two blocks. All return 21 SAT / 47 UNSAT; the two all-block arms
produce identical certificates and acquisitions.

Propagation falls **51,326 -> 51,059 (0.52%)**, but native certificates grow
**398 -> 408** and combined payload **492,731 -> 496,214 bytes**. All-block cached
query time falls in both orders; complete deltas **-0.03893 / +0.00438 seconds**
are mixed. The policy remains optional. This artifact preserves the regression,
not an unconditional claim that more reduction saves total work.

The prefix audit identifies a concrete cause: queries **7 and 34** already have
a known one-block quotient, but the all-block quotient is new. Selecting it adds
eight native records across those two queries. Two later queries account for the
other two additional records. Next test exact known-quotient selection, charging
the second transformation, canonicalization, lookup and verification. These
opportunities are not yet implemented savings.
See [the analysis](../../../research/multiblock-equivalence.md).

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_multiblock_equivalence.py prepare /tmp/cnf-multiblock-new
python3 experiments/compare_cnf_multiblock_equivalence.py /tmp/cnf-multiblock-new
python3 experiments/validate_cnf_multiblock_equivalence.py /tmp/cnf-multiblock-new
python3 -m unittest solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Every worker starts empty and shares answers within its stream. The catalog and
source fingerprints are frozen before acquisition. Setup, discovery, keying,
transport, checking, acquisition, metadata scans, publication, warm reuse, cold
proof replay, sidecars and compression are timed. Imports/source audits,
truth/chronology/history audits and final reports are outside worker timing.
No study tests/builds/audits overlapped timed workers. Query time includes audit
metadata; `attribution.json` separately retains public `solve` timing.

## Preserve and resume

The union preserves **28,691 native / 26 affine / 42 v1 / 42 v2 / 34 discovery
records** byte-for-byte. It adds **45 native keys and eleven v3 records**, retaining
both policies' work; the native union is **28,736**. No old payload is replaced.
Union growth: **81,920 SQLite / 6,918 compressed bytes**. All 5,650 old composed
records and 272 earlier pilot decisions remain readable, with 68 new decisions.

Use `experiments.cnf_multiblock_equivalence.MultiEquivalenceSolver` and its explicit
`MultiEquivalenceStore` reader. Single-block negatives retain v2; multiple-block
negatives use v3 with native-only dependencies. Both readers preserve v1/v2 access.
The memory discovery cache is session-local and does not change proof authority.
Native recursive search and prepared production defaults are unchanged.

All **1,245 full / 76 focused tests** pass. Full tests retain 44 pre-existing SQLite
warnings; focused tests have none. Nine new tests include 4,096 binary cores,
1,020 signed/wide two-block mixtures with all assignments, growing block counts,
malformed evidence, old/new cold replay and truth/model checks. Validation covers
408 chronological queries, 68 exhaustive source truths and 24 quotient truths,
all earlier histories and 596 previous executable sources / 7,722 artifacts /
111 manifests. There is no new Lean or unrestricted-SAT resource bound.

The **224-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,245 full / 76 focused tests** pass (44 pre-existing SQLite
warnings in the full suite, none in focused tests). Final executable source
ledger: **601**. New manifest: **39 artifacts**. Next preservation audit:
**7,761 artifacts / 112 manifests**.
