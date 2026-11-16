# Publish a checked SAT witness before solving a clause deletion

2026-11-16. The optional decision path now reuses a retained SAT witness before
trying the existing UNSAT guard or fresh search. On the same twelve constructed
edits, **fresh reference expansions fall from 427 to 59** compared with the guard
alone. Six additional stored answer certificates make **65 new rows** in total.
Measured complete stream time falls **50.39%** and peak RSS **18.15%** against
that control. The comparison includes checking and persistence, but remains
conditional on the common previously acquired history.

## The applicable cases and exact check

For an identified retained formula `F = G ∧ C`, the answer already proved for
`F` determines the next step. A SAT witness for `F` also satisfies `G`; the new
path transports it to the query's variable coordinates and checks every query
clause. An UNSAT proof instead permits the existing guard, restricting `G` by
the assignment falsifying `C`. A missing result or missing exact candidate
supplies no conclusion and leaves ordinary solving responsible for the query.
These are elementary consequences of satisfaction and the previous guard, not
new complexity results.

The candidate bank recognizes exact single-clause extensions in common input
coordinates, with a clause-count filter. It is deliberately small: twelve
retained templates. The experiment's interface excludes tautological clauses
and does not search arbitrary variable permutations, multi-clause edits or
logical equivalence. The conditional case distinction is complete for a found,
checked one-clause extension; it is not an efficient partition of arbitrary SAT.
The UNSAT branch can still leave an arbitrary formula, as the preceding
[guard construction](clause-deletion-guard.md) demonstrates.

`cnf_clause_witness_reuse.reuse_witness` first checks whether the exact query is
already stored. On a new match it verifies the stronger root and its SAT model,
checks the model against the edited query, then writes one ordinary query SAT
certificate through the unchanged residual checker. The certificate contains
the complete canonical query and its model. It can be checked without the
original template or a transfer alias. Coordinate transport explicitly handles
variables that disappear after deletion. Missing, UNSAT or malformed premises
never supply a positive answer.

The existing negative guard and ordinary solver remain unchanged. The wrapper
is optional research code; the native solver and structural planner are not
modified. A reference decision node is not a structural pattern node.

## Matched comparison and where the saving occurs

All three modes start from the same **613-node reference seed**, whose acquisition,
checking and compression cost **0.91359 seconds** in the preceding study. This
run's acquisition-free seed preflight costs **0.18338 seconds** separately.
The twelve edits are unchanged. Each stream processes them twice. Three fresh
process triples rotate mode order so that each mode occupies each position once.
Tests and builds run after timing.

| Resource per stream | Ordinary | UNSAT guard | Witness plus guard |
| --- | ---: | ---: | ---: |
| Fresh reference expansions | 502 | 427 | 59 |
| New stored rows | 502 | 427 | 65 |
| Published SAT query witnesses | 0 | 0 | 6 |
| New decision splits | 200 | 174 | 24 |
| Query processing and bookkeeping, seconds | 0.59026 | 0.55587 | 0.17794 |
| Full cold checking, seconds | 0.34821 | 0.32884 | 0.20609 |
| Compression, seconds | 0.31209 | 0.29340 | 0.19537 |
| Complete stream, seconds | 1.26932 | 1.19691 | 0.59381 |
| Mean peak RSS, rounded bytes | 84,699,819 | 84,672,512 | 69,304,320 |
| Final reference rows | 1,115 | 1,040 | 678 |
| SQLite bytes | 5,804,032 | 5,431,296 | 3,244,032 |
| Database gzip bytes | 431,983 | 405,995 | 260,883 |
| Raw query sidecar bytes, first repetition | 328,891 | 405,507 | 416,088 |

The six SAT-template edits need no new search. Each publishes one checked answer
row. Edits **19, 21 and 23**, which previously needed **115, 120 and 129** fresh
nodes, now each need zero expansions and one publication. The six UNSAT-template
cases retain precisely the guard's expansion counts: **13, 10, 12, 22, 1 and 1**
for edits 7, 9, 11, 13, 15 and 17. Case 13 still accounts for 22 of the 59 fresh
expansions. All modes agree on **nine SAT and three UNSAT answers**. Every second
visit inserts zero rows.

Against ordinary solving, fresh expansions fall **88.25%**, new stored rows
**87.05%**, whole time **53.22%**, RSS **18.18%**, and SQLite space **44.11%**.
Against the guard alone, the respective reductions are **86.18%, 84.78%, 50.39%,
18.15% and 40.27%**. The three whole times are ordinary
**1.26255 / 1.28693 / 1.25847**, guarded **1.19750 / 1.19287 / 1.20036**, and
witness **0.59481 / 0.59846 / 0.58817** seconds. All paired comparisons agree in
sign. This is still a small constructed workload, not a general performance bound.

Database gzip plus the verbose raw query sidecar falls from **760,874 ordinary**
and **811,502 guarded** to **676,971 bytes** in the first repetition. Sidecar
size alone rises. Cold checking and compression now consume about **68%** of
the shorter witness stream, so avoided search does not eliminate persistence
or proof costs. The clock also includes restoration, bank construction, matching,
premise validation, witness checking/publication, bookkeeping and sidecar writing;
imports and final report writing are excluded. Historical acquisition remains
charged separately. This is not a comparison with solving all edits from an
empty history.

## Validation and retention

All **388 tests** pass, including exhaustive SAT-witness transfer across
single-clause deletions of every satisfiable two-variable CNF, support loss,
self-contained cold query certificates, already-cached roots, missing/UNSAT
premises and tampered models or bindings. Independent validation takes
**23.27957 seconds**, partly concurrent with tests. It checks all archived
reference nodes, **216 new query-result replays**, the four previous streams,
source bindings, budgets, six publications per witness run and unchanged seed
rows. Ordinary and guard control archives are byte-identical to the preceding
study. Repetitions within each mode have identical logical records and archives.

The durable reference union retains **1,169 distinct keys**, using **5,931,008
SQLite / 450,067 gzip bytes**. These keys already occur in the previous ordinary
and guard histories; no new distinct reference key is claimed. One SAT key has
an alternative valid certificate in the three witness trials. The union keeps
the earlier certificate; all alternatives remain in their original archives.
Thus smaller measured arm snapshots do not imply that research history was
pruned or global stored evidence decreased.

The new checkpoint preserves the unchanged **2,614 structural patterns / 259
pairs / seventeen inherited missing children**, original **17/24 coverage with
999 proof steps**, and separate **24/24 supplemental coverage with 208 steps**.
It retains the previous `reference_study`, adds `witness_reuse_study`, and binds
`reference_union` plus `reference_decisions`. Restore the reference union with
the existing archive restorer and `ResidualSolver`; its twelve query decisions
replay without fresh search. Keep both structural and decision evidence.

Checkpoint: `experiments/results/cnf-clause-witness-reuse/checkpoint.json`.
SHA-256: `79c224246b77270980ddb5685ab32464df19057dfe95a7db976a5b18019de63b`.
Report SHA-256: `3005787a6d6eb257b19ee39a7b4cd33137384f93ec0f3c2547142b31bfd254d2`.
The new directory retains **49 manifested artifacts plus its manifest,
7,549,821 bytes** total. Later audits inherit **3,669 artifacts / 64 manifests**.

## Next discovery: new deletions of UNSAT templates

The measured twelve roots are now cached. Repeating them cannot demonstrate
broader discovery. The remaining fresh work came from the exceptional cofactors
of UNSAT templates, particularly case 13. Test previously unseen deletions with
a frozen history and complete candidate-check costs.

A post-hoc screen follows the established one-variable model-rotation idea:
flip a variable in the sole clause falsified by a known deletion witness, then
check all clauses of the original formula. Exactly one remaining falsified
clause identifies a new deletion for which the modified model is a valid witness.
This is the transition-clause reasoning used in
[Belov and Marques-Silva's model rotation](https://www.cs.utexas.edu/~hunt/fmcad/FMCAD11/papers/74.pdf).

Seven flips across the known SAT deletion witnesses for cases 7, 9 and 13 yield
two verified new-input proposals from case 9. Flipping variable **260** leaves
only `(-230,120,260)` false; flipping **150** leaves only `(-100,150,160)` false.
The corresponding CNFs each have **28 variables / 81 clauses / 238 literals**,
and neither complete root is in the 1,169-key union. Both models, sources and
identities are retained in `rotation-screen.json`. No fresh reference search
runs, but the seven full-clause checks and old-proof checking are real work;
the diagnostic costs **0.03762 seconds** separately.

Case 7 leaves two or three falsified clauses; both case-13 flips leave three.
Those failures are retained. The proposals are checked SAT models, not published
cache rows or a measured rotation speedup. The next experiment should publish
and cold-check the two candidates, evaluate unseen neighboring deletions against
ordinary and guard controls, and measure whether indexed clause updates or
bounded further rotations avoid enough search to repay discovery. Original
case 7 remains the separate broader structural-discovery pointer.
