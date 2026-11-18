# Partial backbone reuse with direct excluded-branch proofs

Successful implication paths from unsuccessful whole-clause cover searches now
supply forced-variable evidence. Only the surviving cofactor is searched. SAT
lifts a checked full-source model; UNSAT combines with an excluded-branch unit
proof transported directly from the path, without rerunning propagation.
Existing native proof formats and readers remain unchanged.

Two optional policies are measured: first retained path, and a frequency gate
that accepts only a path for the ordinary frequency-selected variable. This gate
does not guarantee identical fallback control flow. On sixty new queries, all
policies return 42 SAT / 18 UNSAT with identical preceding discovery evidence.

First adds five native nodes despite less propagation. Frequency saves **two
nodes / 1,767 payload bytes**, with **3.04% lower mean query time** in both orders.
Its complete-worker timing remains mixed, with a **0.02% higher mean**. It accepts
only two candidates and rejects twelve other residuals. Peak RSS and small trial
storage reductions are measured, not scaling guarantees. Both policies remain
optional; the first-path storage regression is retained.
See [the analysis](../../../research/binary-backbone-reuse.md).

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_binary_backbone.py prepare /tmp/cnf-backbone-new
python3 experiments/compare_cnf_binary_backbone.py /tmp/cnf-backbone-new
python3 experiments/validate_cnf_binary_backbone.py /tmp/cnf-backbone-new
python3 experiments/analyze_cnf_binary_backbone.py /tmp/cnf-backbone-new
python3 experiments/diagnose_cnf_binary_backbone.py /tmp/cnf-backbone-new
python3 -m unittest solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Six workers run serially in opposite orders, without concurrent tests/profiles.
`protocol.json` binds the production sources. Costs include preparation,
recognition, ranking, path checking/transport, compiled children, storage, warm
reuse, serialization, compression, full historical replay and process RSS.
Final report rewrites and posthoc analysis/validation/tests/builds are outside
worker timing. Mechanism checks use separate empty archives and report no timings.
The corrected preflight fixture, old test source and protocol snapshot are
retained; the correction preceded every production worker.

## Resume and checks

`checkpoint.json` preserves all **27,600 previous native payloads / eighteen
extensions byte-for-byte**, reaching **27,888 native keys / twenty-two extensions**.
It adds 168 native and twelve negative composed records to 5,350 inherited records.
All three policies' histories remain. Union growth is 712,704 SQLite / 78,123
compressed bytes. Eight roots have alternative native evidence in trial archives;
the union preserves its first payloads. Both optional solver classes are named
in the checkpoint; affine negatives retain the explicit `TerminalStore` reader.
The previous default solver is unchanged.

All **1,204 tests**, **35 focused tests**, 360 chronological query audits and 24
affine-publication counter audits pass. The validator checks 48 exhaustive family
truths, warm answers and full cold replay for every trial and the union. Eight
new tests cover both policies on 4,096 small mixed sources, corrupted paths,
signed lifts, frequency admission, history preservation, cold replay, and direct
compilation with propagation/search forbidden. The full suite retains 44 existing
SQLite resource warnings; focused tests have none. The **221-page manuscript**
builds with a clean final log and all **64 prior proof blocks unchanged**.
All 567 prior sources, 7,517 artifacts and 106 manifests remain unchanged.

Next test targeted recognition of the six ordinary split nodes in
`attribution.json` whose chosen variables are binary-forced but missed by the
cover-oriented candidate search. Its fourteen-source diagnostic includes seven
models and one subsumption node, so it is not a count of avoidable expansions.
The same census has 75 mixed satisfiable binary cores with no forced literals.
No new Lean theorem or unrestricted-SAT bound is claimed.

Final source ledger: **574**. New manifest: **51 artifacts**. Next preservation
audit: **7,568 artifacts / 107 manifests**.
