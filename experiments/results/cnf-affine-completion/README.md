# Reuse checked affine spaces for native model completion

See [the analysis](../../../research/affine-completion.md) for correctness,
resource bounds, matched measurements and remaining gaps. The optional bridge
reuses exact parity extraction and a checked complete affine basis. It packs
leftover clauses once and enumerates candidates in Gray order, changing one
basis direction per next candidate. A model must satisfy the full raw target
before existing native publication. The total free dimension is capped at eight
before basis construction, including variables outside the extracted equations.
Earlier admitted routes keep priority; negative diagnostics retain fallback.

Forty-one saved contexts compare the preceding probe policy with the bridge
(82 arms); one positive target repeats in reverse order (84 arms total).
Eight changed targets shrink **80 -> 8 native nodes / 82,179 -> 10,860 bytes**.
The other 33 contexts retain their certificates. Four saved negative coupled
controls still acquire 83 nodes.

Six fresh workers run baseline/probe/affine and its reverse in serial order.
All modes return **39 SAT / 21 UNSAT** on sixty queries. After shared preparation,
48 family targets and neighbour case 4 remain unfamiliar; eleven other neighbours
are known. Case 4 still adds ten nodes in every mode. Prior discovery is identical
on all 49 unfamiliar queries. Nine additional affine models reduce native
additions **395 -> 336 nodes / 482,568 -> 424,272 bytes**.

Mean query time falls about **11.00%**, with both paired deltas negative.
Complete-worker deltas have mixed signs and the native baseline retains the
smaller mean complete runtime. Diagnostics grow 7.86%, trial SQLite falls
118,784 bytes and mean RSS falls 2.87 MB. These are finite matched improvements,
without an end-to-end or unrestricted-SAT scaling guarantee.

Fresh cases 29, 41 and 57 already have checked inconsistent-row or exhausted-space
evidence, yet still acquire **51 fallback nodes / 7,829 propagation visits**.
Compatible negative publication is the next target. Random three-CNF still adds
169 nodes, and graph case 47 needs two missing cover conditions, beyond the
one-extra-probe policy. No-equation and large-free-dimension cells remain open.

## Reproduce

Run from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_affine_completion.py /tmp/new-affine-completion
python3 experiments/validate_cnf_affine_completion.py /tmp/new-affine-completion
python3 experiments/analyze_cnf_affine_completion.py /tmp/new-affine-completion
python3 -m unittest solver.test_cnf_affine_completion solver.test_cnf_cover_probe solver.test_cnf_negative_cover -q
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

Preflight passed 82 exact-prefix arms, sixty independently reconstructed fresh
selections and an eight-query worker with inherited warm/cold replay. Production
started after preflight completed and ran without concurrent tests, builds or
profiles. Truth checks, independent reconstruction and attribution ran afterwards.
`initial-diagnosis.json` preserves the untimed motivating profiles, whose binary
coefficient enumeration differs from the production Gray walk.

`protocol.json` freezes 543 runtime sources; `validation.json` adds the posthoc
analyzer for 544 sources. All 324 counter audits pass. Independent replay binds
exact source grouping, clause ownership, row operations and the complete basis,
reconstructing each candidate directly from its Gray coefficient vector rather
than the incremental producer. Every rejected clause and accepted model is
checked. Extraction, verification, basis, packing and candidate counters are
reconstructed from evidence; native publication and historical replay remain
separate charges.

All 1,169 tests and 24 focused tests pass. Eight new tests include 512 exhaustive
support/coordinate comparisons and 64 random affine mixtures checked against
all assignments. They cover caps, corruption, forced prefixes, signed variables,
negative evidence, known nodes and cold native replay. The full suite retains
44 existing unclosed-SQLite warnings; focused tests have none. The manuscript
builds with 217 pages and 64 unchanged proof blocks. No new Lean theorem or
native proof kind is claimed.

## Preserved checkpoint

All **1,169 tests**, 24 focused tests, 324 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-affine-completion/checkpoint.json`:
**26,743 native keys**, preserving all 26,279 prior payloads, with 264 new
composed records alongside 4,719 inherited records, 2,957 ordinary decisions
and six projections. The union uses 82,378,752 database bytes / 6,217,639
compressed bytes. Twenty-six roots have alternate certificates in 67 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 539 prior sources,
6,871 artifacts and 101 manifests remain unchanged. The 217-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem,
native proof kind or unrestricted-SAT resource guarantee is claimed.

New manifest: **300 artifacts**. Next preservation audit: **7,171 artifacts / 102 manifests**. Final source ledger: **544**.
