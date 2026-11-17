# Recover the target model from a positive proposed child

The optional selector binds and verifies a child's saved unit trace, restores
the proposed assignment, transports the model to target coordinates and checks
every target clause. Direct publication checks that model through the existing
native SAT verifier. It acquires neither the proposed negative premise nor a
child node and adds at most one target row after earlier preparation. Other
choices and negative proof obligations remain unchanged.

Thirty-nine exact-prefix arms cover thirteen saved queries under native baseline,
retained-prefix discovery and positive-child recovery. Case 146 now uses one
native row instead of six, 1,798 native bytes instead of 6,688, and 25,527
serialized delta/record bytes instead of 30,595. Propagation falls from 3,304 to
2,045 visits versus the preceding policy; native baseline needs 1,847. One
explicit model publication accompanies zero expansion calls. The other twelve
controls preserve preceding native payloads. Single-arm times establish no
stable general speedup. Prefix reconstruction and shared preparation are
accounted separately from the measured arm.

Six fresh workers run baseline/retained/positive and the reverse order on 192
new query roots. These are 64 double-deletion neighbours per old template,
excluding inherited query and native roots, including 1,280 earlier query roots
per template. Catalogue selection takes 1.583 seconds separately. No tests,
profiles or builds overlap production. All modes answer 93 SAT and 99 UNSAT.

| Measure | Baseline | Previous policy | Positive child |
| --- | ---: | ---: | ---: |
| New native rows | 197 | 197 | 197 |
| Added native bytes | 441,084 | 441,084 | 441,084 |
| Expansion calls | 2 | 0 | 0 |
| Explicit trace publications | 0 | 2 | 2 |
| Explicit model publications | 0 | 0 | 0 |
| Propagation literal visits | 1,831 | 1,831 | 1,831 |
| Mean complete worker seconds | 21.126 | 20.697 | 20.700 |

The new route never activates. After preparation, 190 targets already have known
native roots; the two remaining calls use a known propagated residual or unit
conflict. Ordinary preparation adds 195 rows and target acquisition two. Native
payloads are identical in every mode, and warm replay acquires no rows. The two
complete-time differences against the preceding policy are +0.399/-0.394 seconds,
so no stable timing or memory gain is established. No difference can be
attributed to successful positive-model recovery on this set. Cold replay is
the largest measured complete-time component.

New raw roots do not ensure unfamiliar residuals after preparation. The next
evaluation needs different template families and pre-query target-familiarity
counts. Preserve these neighbours as warm-reuse controls and retain prior
0/131/159 for unresolved interaction, 146 for positive model recovery and older
36 for the unpriced single-variable two-CNF decomposition. The current result
does not broaden general structural authority or guarantee small decompositions.

The 22,729-key union preserves all 22,532 old native payloads, adds 197 keys with
no alternatives, and retains 615 new composed records alongside 2,430 earlier
composed records, 2,957 ordinary decisions and six projections. The evidence
union occupies 73,793,536 database bytes / 5,266,420 compressed bytes; it retains
all arms rather than representing one policy's working storage. Ready/pending
banks are 132/38, 141/66, 86/90 and 86/117. Structural and supplemental authorities
are unchanged; all prior 493 sources, 5,455 artifacts and 92 manifests remain
preserved.

All 1,102 tests and 26 focused tests pass. The full suite emits 44 existing
SQLite ResourceWarnings; focused tests emit none. Independent validation rebuilds
every control prefix, regenerates the catalogue, checks selection and lifted
models, and verifies native/composed proofs and warm/cold replay without
acquisition. The 209-page paper builds cleanly with all 64 proof blocks unchanged.
The protocol freezes 497 runtime sources; validation adds one posthoc analyzer
for 498 total.

Reproduce from the repository root into a new output directory:

```sh
python3 experiments/compare_cnf_positive_child.py /tmp/cnf-positive-child-reproduction
python3 experiments/validate_cnf_positive_child.py /tmp/cnf-positive-child-reproduction
python3 experiments/analyze_cnf_positive_child.py /tmp/cnf-positive-child-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_positive_child solver.test_cnf_trace_fallback solver.test_cnf_propagated_reuse
```

No new Lean theorem, stable general speedup, live-memory bound, minimum-cost
expansion rule or unrestricted-SAT efficiency result is established.

New manifest: **162 artifacts**. Next preservation audit: **5617 artifacts / 93 manifests**. Final source ledger: **498**.
