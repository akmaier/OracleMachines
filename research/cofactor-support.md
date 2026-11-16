# Checked support reuse between guarded subproblems

The new bank reuses a refutation when a previously unseen guarded subproblem
contains a known UNSAT clause support. It recognizes 16 such inputs in the
matched stream and saves 72 fresh expansions. Building every support proof in
advance nevertheless costs more than those savings: complete runtime rises
23.01%. This remains an optional experiment. The next target is proof construction
on a match, with all necessary checking retained.

## Recognition and exact recomposition

Suppose a checked refutation establishes that G together with clause C is UNSAT.
Every model of G must then falsify C. Let alpha assign all literals of C false.
If a checked UNSAT core K is a clause subset of the residual G restricted by
alpha, the residual is UNSAT and so is G. The new route checks the old guard,
matches K in the actual residual's coordinates, and publishes the residual
refutation using the frozen contradictory-subset certificate rule. The existing
guard replay then establishes the complete query answer. A cofactor key alone
is never substituted for the complete query key.

The guard itself is not a negative answer. For example, G = not x and C = x
have an UNSAT conjunction while G is SAT. Preparation therefore uses only
checked negative cofactors, and a failed support match falls back to the
ordinary solver. Of 148 inherited guarded decisions, 145 are negative and three
are positive; the latter are excluded. A new guarded SAT input also occurs in
this experiment and is solved normally.

Supports are extracted from the stored proof DAG without fresh solving. The
extractor follows unit traces, split branches, implication paths, reductions
and the other frozen certificate rules. It maps selected clauses back through
normalization to the original residual coordinates. Every derived core and
published subset wrapper is checked by the unchanged verifier.

The 145 negative cofactors yield 112 distinct raw supports. Removing supports
that contain another retained support leaves 104. This antichain preserves
every superset match: each discarded support contains a retained one, and every
retained support belonged to the original bank. It does not claim minimum
supports or search arbitrary variable renamings. The current interface expects non-tautological
clauses with nonzero integer literals; general CNF normalization is a separate
requirement. Recognition costs include
source/guard verification, restriction, canonicalization, set construction,
containment search, proof publication and persistence.

## Matched measurements

Both modes start from the same 14,630-key union, old 145-core bank and 260
extension templates. They use incremental accounting and the complete snapshot
cold audit. The candidate additionally extracts and stores the cofactor bank;
all preparation is inside its worker clock. A fixed salted order selects the
next 64 double deletions per original template after excluding all 576 earlier
answered queries, including guarded answers without complete roots, and cached
complete roots. Selection costs 1.45429 s separately. These are constructed
development inputs, not an independent arbitrary-SAT sample.

Four fresh-process pairs alternate mode order. Each stream visits all 192
queries twice, with no concurrent tests, builds or profiles. The control also
performs the target-cache lookup, so the optional bank's extra work is isolated.

| Measurement | Current bank | Added cofactor bank |
|---|---:|---:|
| Cofactor support hits | 0 | 16 |
| Fresh expansions | 234 | 162 |
| Split nodes | 69 | 49 |
| Preparation proof nodes | 0 | 1,310 |
| New query rows | 380 | 324 |
| All new rows | 380 | 1,634 |
| Mean preparation seconds | 0 | 1.82086 |
| Mean two-visit query seconds | 1.33223 | 0.87849 |
| Mean complete worker seconds | 7.93324 | 9.75898 |
| Mean cold audit seconds | 3.10069 | 3.39589 |
| Mean compression seconds | 2.64869 | 2.81458 |
| Mean peak RSS, bytes | 463,675,392 | 506,449,920 |
| SQLite bytes | 48,062,464 | 49,614,848 |
| Gzip bytes | 3,763,522 | 3,964,072 |

Fresh expansions fall **30.77%** and query time **34.06%**, with no per-query
expansion regressions. Complete time rises **23.01%**, mean peak RSS **9.23%**,
SQLite size **3.23%** and gzip size **5.33%**. All four pairs show a whole-time
regression, ranging from 19.69% to 26.00%. The small-repeat timing variation does
not change that conclusion. The first-trial gzip plus raw sidecars grows from
9,556,044 to 10,739,863 bytes. There is no end-to-end speedup or space saving.

The complete clock includes restoration, old-bank checking, support discovery,
certificate construction, matching, querying, final preservation checks, full
cold replay, sidecars and compression. Process launch, imports, command-line
protocol/catalog reads, final summary digest construction and report writing
are excluded. Historical
acquisition remains charged in earlier experiments. No amortization break-even
has been established, and gains on different streams must not be multiplied.

Both modes answer **84 SAT / 108 UNSAT**. There are 63 old full-query core hits,
83 witness publications and 46 guards. Of these guards, 45 lead to UNSAT and
one to SAT; six targets are already cached. The new bank answers 16 previously
uncached negative targets without search. All 72 saved expansions come from
those hits; no additional saving comes from other preparation rows. Fourteen
retained cores are used. Every measured hit has the same guard clause as its
first retained origin, although a unit test demonstrates valid transfer between
different guard clauses. This workload does not demonstrate broad transfer
across guards or SAT categories.

Repeated visits add no rows. The candidate still performs 151 negative and 11
positive expansions, across 24 queries. Case 7 in this new catalog is the guarded
SAT counterexample; both modes use 11 expansions on it. This is not original
structural case 7. The largest remaining negative cases are 191 (17 expansions),
82, 112 and 184 (14 each), and 87 (12).

## Why preparation dominates, and the next test

Extraction visits 1,075 negative proof nodes and stores 791 derived cores plus
519 subset wrappers. Of those 1,310 preparation nodes, the retained 104-core
bank needs 1,272, while the 14 cores actually matched by this stream need only
118. The query proofs likewise depend on only 118 preparation nodes. Merely
pruning unused nodes from the complete retained bank removes at most 38 nodes;
it cannot remove the main cost while preserving that whole ready-made bank.

The next credible experiment is to separate support discovery from certificate
construction. Retain source-bound support proposals and construct/check a
derived proof only when a new residual matches. The frozen verifier must accept
the derived core before it can justify UNSAT. Discovery and match verification
still cost work, and a match may need a large proof. This policy has not yet
been implemented or measured. Choosing only the 14 cores used here would use
future workload information and could lose coverage; it is not a valid tested
selection policy. No old rows or unsuccessful trials were deleted.

The method recognizes an exact conditional subset pattern; it does not provide
an efficient partition covering arbitrary CNFs. Its preparation is bounded by
the acquired proof graph, whose acquisition and size can be exponential.
Original structural closure remains 17/24 and the separate supplemental corpus
24/24. These observations add no Lean theorem or unrestricted-SAT claim.

The [result directory](../experiments/results/cnf-cofactor-support/README.md)
preserves every trial, support origin, dominance witness, query and refutation.


All 434 tests pass. Independent ordinary-solver validation checks eight complete
archives and 3,072 trial query replays, every union node, all support origins
and dominance witnesses, 845 inherited decisions and all 192 new decisions with
fresh search disabled. Earlier 348 source bindings, 3,873 artifacts / 68 manifests
and 64 proof blocks remain unchanged. The manuscript builds to 194 pages.

Resume `experiments/results/cnf-cofactor-support/checkpoint.json`. Preserve
inherited fields plus `cofactor_support_study`, `cofactor_support_decisions` and
`cofactor_support_bank`. The latter binds `cofactor-0/cofactor-bank.json`; load
its `cores` field to reuse the 104 already materialized supports. Do not repeat
extraction for a warm run. A test of deferred construction needs matched seed
clones or genuinely new support proposals, with acquisition charged explicitly.

The union retains 16,320 keys / 49,610,752 SQLite / 3,953,721 gzip bytes. It keeps
all earlier payloads and both modes' distinct new nodes; sixteen alternative
certificate occurrences remain in trial archives. The new decision catalog has
146 direct full-query roots and 46 guarded records, including the SAT case.
Structural authority remains 2,614 patterns / 259 split pairs / 17 missing
children, original 17/24 / 999 proof steps, and separate supplemental 24/24 / 208.
Original case 7 retains its separate discovery pointer.
