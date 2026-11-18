# Larger mixtures, budget stops and checked witness recovery

This frozen 108-query stream contains six designs at scales 24/48/72, two samples
each, and base/edit/monotonically relabelled repeat variants. Its 72 distinct
canonical roots are absent from the preceding archive. No solver outcome selects
inputs, and labels never enter timed search. See the
[analysis](../../../research/larger-mixture-expansion-costs.md).

Six serial workers compare unchanged batching, memo128 and ordered normalization
in opposite orders. Both alternatives regress on query time: 1.49% and 1.09%.
All produce 70 SAT, 36 UNSAT and two unresolved attempts under a 256-native-
expansion cap. This cap excludes other work and is not a time, memory or stored-
record bound. Budget exhaustion means no verdict. Verified committed prefixes
survive while pending suffixes roll back. All timings and failures are retained.

A later repeat closes the stopped base. A separate post-timing operation then
checks that model against the remaining edited source and publishes one native
SAT certificate with zero expansions. Both readers certify the resulting 72
roots: 48 SAT / 24 UNSAT. Neither original budget-stop observation is rewritten.
Donor selection is supplied, so candidate retrieval remains an implementation gap.

## Reproduce

From the repository root, choose a fresh destination:

```sh
python3 experiments/compare_cnf_larger_mixtures.py prepare /tmp/cnf-larger-new
python3 experiments/compare_cnf_larger_mixtures.py /tmp/cnf-larger-new
python3 experiments/profile_cnf_larger_mixtures.py /tmp/cnf-larger-new
python3 experiments/validate_cnf_larger_mixtures.py /tmp/cnf-larger-new
python3 experiments/resume_cnf_larger_mixtures.py /tmp/cnf-larger-new
python3 -m unittest -v solver.test_cnf_checked_model_reuse solver.test_cnf_larger_mixtures solver.test_cnf_ordered_normalization solver.test_cnf_proof_normalization_reuse solver.test_cnf_publication_batches solver.test_cnf_canonical_verify solver.test_cnf_query_canonical_cache solver.test_cnf_known_quotient solver.test_cnf_multiblock_equivalence solver.test_cnf_binary_core_cache solver.test_cnf_compact_equivalence solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Worker timing includes setup, append-delta metadata, normalization, discovery,
search, checking, publication, final checked-object measurement, warm/cold replay,
sidecars and compression. Preparation is reported separately. Profiles, bounded
pattern discovery, history audits and witness opportunities are posthoc and occur
after every timed worker. Recovery is also separate; its donor became available
only later in the original stream. The solver algorithms and timed protocol were
not tuned after seeing these results.

## Results and boundaries

Random 3-CNF consumes 58.48% of query time; parity mixtures consume 21.54%.
Edits require 1,013 expansions / 1,055 new records, nearly as much as bases.
The timed archive has 2,259 native records, 12,128,848 key/payload bytes and
22,851,584 SQLite bytes. Checked Python cache objects occupy 53,930,391 bytes.
These measurements are identical across variants. Worker RSS includes benchmark
metadata, cold proof loading and compression; it is not isolated solver memory.

All root profiles share six syntax exclusions and width-capped unresolved parity
recognition. The bounded inventory closes only 18/108 family decompositions,
all gated-Horn cases. It stores 624 checked pattern nodes and 108 exact source
bindings, including unsuccessful alternatives. Structural closure is not a SAT
answer, and native solver completion does not imply recognition completeness.

Full target checks show that 21/23 available parent SAT models also satisfy their
edits. Their observed 225 expansions are an opportunity indicator, not an additive
counterfactual saving. Automatic candidate retrieval, coordinate choices,
publication and changed future archive contents still need evaluation.

The recovery helper keeps original variable names bound, validates the donor and
complete target, and sends a valid model through the native witness checker. A
miss means neither UNSAT nor absence of other reusable models. Recovery adds one
record / 7,895 key/payload bytes. Its observed 2.84 ms excludes candidate discovery
and all earlier acquisition; it must not be compared directly with a failed cold
attempt as a general speedup.

## Preservation and checks

The audit validates 648 chronological attempts, 540 non-self cross-arm/repeat
comparisons, every new proof and the historical 5,650 composed / 444 pilot
decisions. It preserves all 638 prior source fingerprints and 8,032 artifacts
across 118 manifests. The timed stream contributes 2,254 previously absent native
records; recovery adds one more. The authoritative union now has 31,141 native /
26 affine / 42 v1 / 53 v2 / 22 v3 / 34 discovery records. Trial archives, the
pre-recovery checkpoint, inventory and original unknown observations are retained.

The first inventory audit failed because its expected configuration omitted the
default `decompose=True`. Its validator, log and already checked union remain in
`failed-audit/`. The corrected check uses the complete configuration. No timed
run was discarded or repeated to obtain a better result.

All 1,311 full / 142 focused tests pass. Earlier 1,305-test and 136-test logs are
retained before the recovery helper was added. Forty-four unclosed-SQLite warnings
remain at unchanged files in the full suite; focused tests emit none. The
228-page manuscript builds without warnings, preserving all 64 prior proof
blocks. Final source ledger: 647. `manifest.json` seals all checkpoint artifacts.

Resume from `checkpoint.json`, which binds the recovered union. The next target
is bounded witness candidate retrieval without generator hints, followed by
partial negative-proof reuse across edits and compact retained proof state.
This finite catalog completion supplies no uniform bound for arbitrary SAT.
