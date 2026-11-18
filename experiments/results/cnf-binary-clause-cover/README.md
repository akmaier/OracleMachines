# Wider-clause conflicts from a satisfiable binary core

The optional rule checks a source clause whose every literal is forced false by
binary implication paths. It shares reachability results within one residual,
with at most eight roots and source-clause width four. Paths compile into the
unchanged native split/unit/implication format. The final two literals reuse a
contradiction cycle; source-bound checking remains mandatory.

On sixty new queries, **three covers in two random-three-CNF cases replace eight
search expansions with six compiled children**. Actual native additions fall
**226 -> 224**, by **2,174 payload bytes**. Child propagation falls 23,611 -> 23,069.
Both policies return 38 SAT / 22 UNSAT with identical earlier discovery traces.
Mean query and complete-worker times improve **1.27% / 0.40%**, with both paired
orders improving. Peak RSS rises about **9.53 MB** and sidecars grow about 5.4 KB.
This is a small finite gain with a memory tradeoff. The policy remains optional.
See [the detailed analysis](../../../research/binary-clause-cover.md).

## Reproduce

Run from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_binary_clause_cover.py prepare /tmp/cnf-cover-new
python3 experiments/compare_cnf_binary_clause_cover.py /tmp/cnf-cover-new
python3 experiments/validate_cnf_binary_clause_cover.py /tmp/cnf-cover-new
python3 experiments/analyze_cnf_binary_clause_cover.py /tmp/cnf-cover-new
python3 experiments/diagnose_cnf_binary_clause_cover.py /tmp/cnf-cover-new
python3 -m unittest solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Two opposite serial orders use separate processes; no tests/profiles ran alongside
these workers. Runtime fingerprints are frozen in `protocol.json`. All preparation,
recognition misses, graph work, compilation, checking, persistence, warm reuse,
serialization, compression, full cold replay and process RSS remain measured.
Final report rewrites, posthoc validation/diagnosis and tests/builds are outside
worker timings. Family labels never enter selection. Diagnostic reachability is
uncapped and includes direct publications, so its counts are not native-expansion
opportunities. Seven untimed empty-archive checks retain the rejected unfused
compiler, which made larger proofs, beside the baseline and final compiler.

## Resume and checks

Restore `checkpoint.json`'s `reference_union`. It preserves all **27,368 old native
payloads and thirteen extensions byte-for-byte**, reaching **27,600 native keys /
eighteen extensions**. It adds 110 native and ten negative composed records to
5,230 inherited records. Comparator history adds 569,344 SQLite / 66,325 compressed
bytes. Three alternative native proofs remain in the trial archives; the union
keeps first payloads and also preserves six candidate-only keys.

Enable the optional native rule with
`experiments.cnf_binary_clause_cover.AccountedBinaryClauseCoverSolver`.
Old native readers verify its proofs; affine extensions retain the explicit
`experiments.cnf_affine_session.TerminalStore` reader. Existing default solvers,
old archives and runtime sources remain unchanged.

All **1,196 tests**, **27 focused tests**, 240 chronological query audits and twenty
affine-publication counter audits pass. Validation checks 48 exhaustive family
truth tables, warm answers and full historical replay of every trial and the
union. The eight new tests cover 4,096 small binary subsets with a wide clause,
corrupt paths, missing variables, budget exhaustion, signed renaming, shared
reachability, disabled leaves and cold replay with acquisition forbidden.
The full suite retains 44 existing SQLite resource warnings; focused tests have
none. The **220-page** manuscript builds with a clean final log and all **64 old
proof blocks unchanged**. No new Lean theorem is claimed.

All 560 prior sources, 7,478 artifacts and 105 manifests remain unchanged. Next
investigate partial binary backbones in new cases 32/40/52, which still require
4,377/3,020/2,880 child propagation visits. Full historical replay and graph cover
discovery remain larger costs. This rule does not resolve unrestricted SAT.

Final source ledger: **567**. New manifest: **39 artifacts**. Next preservation
audit: **7,517 artifacts / 106 manifests**.
