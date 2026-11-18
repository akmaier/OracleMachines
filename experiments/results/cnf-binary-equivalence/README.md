# Binary equivalence acquisition pilot

The optional top-level API discovers one binary SCC equivalence block, substitutes
it in every source clause and solves the quotient with the unchanged native
solver. Two source-indexed trees certify `k` equivalent literals using `2(k-1)`
edges. SAT lifts publish native witnesses; negative records have an explicit
separate authority and ordinary native UNSAT dependencies.

The pilot starts each worker from an empty archive and retains results within its
stream: eleven saved residuals, 33 clause edits and 24 unfamiliar generated
controls. This is not historical production-prefix replay. All 68 decisions
(21 SAT / 47 UNSAT) match exhaustive truth. Forty-five selected blocks each merge
one variable. Native nodes fall 420 -> 398, but 42 extension records raise the
combined total to **440**. Propagation falls **16.57%**; combined payload rises
**1.80%** and complete-worker mean **1.29%**, with both timing orders regressing.
The optional prototype and its regression are preserved.

See [the analysis](../../../research/binary-equivalence-acquisition.md) for the
certificate proof, costs, per-group differences and limits. New negative payloads
repeat 20,673 bytes of source CNFs and 20,535 bytes of reconstructible child keys;
only 2,713 bytes encode equivalence evidence. A compact version with exact checked
reconstruction is the next experiment. Twenty-two repeated binary keys and twelve
unused second blocks are separately recorded opportunities, not achieved savings.

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_binary_equivalence.py prepare /tmp/cnf-equivalence-new
python3 experiments/compare_cnf_binary_equivalence.py /tmp/cnf-equivalence-new
python3 experiments/validate_cnf_binary_equivalence.py /tmp/cnf-equivalence-new
python3 -m unittest solver.test_cnf_binary_equivalence solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Four workers run serially in opposite orders. No study tests/audits/builds run
concurrently with timing. Complete time includes setup, recognition, acquisition,
checking, persistence, metadata scans, warm reuse, cold replay, sidecar writing and
compression. Imports and source-fingerprint audits precede worker timing.
Truth tables, posthoc attribution, old-history union and final report
writes are outside worker timing. The initial audit was followed by the validator's
`structure` mode, which adds block/repeated-core/byte attribution without changing
the completed union or timed outputs.

## Resume and validation

`checkpoint.json` preserves **28,145 old native payloads / twenty-six affine
extensions** byte-for-byte and reaches **28,691 native keys / forty-two new
equivalence records**. It retains 5,650 old composed records and adds 136 explicit
pilot decisions. Four alternative native roots remain in trials; the union keeps
its first payloads. Union growth is 1,327,104 SQLite / 127,289 compressed bytes,
including comparator histories. The API is
`experiments.cnf_binary_equivalence.BinaryEquivalenceSolver`; negative equivalence
roots require `EquivalenceStore` and must not be passed to callers assuming an
ordinary native root. Old native and affine readers remain unchanged.

All **1,220 tests**, **51 focused tests**, 272 chronological dependency audits,
68 exhaustive truth tables, warm answers and all old/new cold certificates pass.
Eight tests include exhaustive 4,096-source quotient/lifting checks, a 24-variable
shared-tree fixture, corrupt/cyclic evidence, missing or positive dependencies,
signed names, disappearing representatives, clause edits and disabled leaves.
The full suite retains 44 pre-existing SQLite warnings; focused tests have none.
All 581 prior sources, 7,608 artifacts and 108 manifests remain unchanged.
No new Lean theorem, production speedup or unrestricted-SAT bound is claimed.

The **222-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **586**. New manifest: **34
artifacts**. Next preservation audit: **7,642 artifacts / 109 manifests**.
