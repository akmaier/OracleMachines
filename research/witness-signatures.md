# Bounded exploration of SAT witness signatures

The current coverage probe reuses checked SAT assignments across clause-deletion
queries. It extends the earlier [model-rotation experiment](model-rotation.md)
to assignments falsifying up to two clauses of a fixed template. This is an
optional discovery mechanism, not a new arbitrary-SAT algorithm or a replacement
for the exact fallback. Its value must be measured on new queries after charging
discovery, checking and retained state.

## Exact recognition and the limit of compression

For a template clause set F and a complete Boolean assignment a on its variables,
let B(a) be the clauses of F falsified by a. For every Q contained in F,

`a satisfies Q iff B(a) intersects Q trivially iff B(a) is contained in F minus Q`.

This is exact in the shared input coordinates. Equal B sets induce equal lookup
coverage over all deletion queries, so lookup needs only one representative per
signature. Each returned assignment is still checked against the full query and
published as an ordinary SAT model certificate. A query outside the template
misses this index. The current interface rejects tautological clauses and invalid
literals; callers must normalize them or use the fallback. Failure, absence and
budget exhaustion never justify UNSAT.

Equal signatures do **not** preserve model-rotation transitions. For
F = {(-x or -y), y}, assignments (x,y)=(0,0) and (1,0) both falsify only y.
Flipping y satisfies F in the first assignment and falsifies (-x or -y) in the
second. Keeping just the second assignment would lose that direct route to a
model of F. The implementation therefore deduplicates complete assignments for
exploration and uses one representative per B only for lookup. It does not claim
that a compact lookup quotient is also a compact state space for discovery.

## Bounded acquisition and persistence

The seed batch consists of earlier SAT records whose full models are checked.
Variables absent from a seed query are completed with False. Each template keeps
assignments with at most two false clauses. A FIFO queue flips variables in the
currently false clauses, updating the signature through incident clauses. All
attempts, including rejected and duplicate flips, the queue position, accepted
assignments and seed/parent origins are retained. The fixed per-template budget
does not reset on another query or restart. Seeds are sealed before exploration;
interleaved online seeding and incremental extension of this bank are not yet
implemented.

Cold restoration rescans each stored assignment and reconstructs the complete
bounded transcript, including seed identities and failed attempts. This costs
work; it is included in the complete comparison clock. Restoration does not
replace a query's full model check with a saved validity flag. The negative
support index remains the already acquired 170-entry frontier, with the same
complete proof/query and historical-lineage audit in every mode.

## Bounds and remaining construction obligation

For m template clauses and an at-most-d-false-clause signature, there are at most
sum(i=0..d) binomial(m,i) lookup signatures. With d=2 this is quadratic in m.
This bounds the number of distinct signatures, not the effort of finding their
witnesses or the number of assignments needed for useful transitions.

With S seed assignments and a cap of B attempted flips per template, at most
S+B assignment states and B attempt records are retained. In addition to input
and indexing overhead, the bit masks cost O((S+B)(n+m)) bits and the transcript
uses O(B(m+log(S+B)+log n)) bits; Python object overhead and seed-origin text add
space. Signature representatives cost at most O(S+B) indices. No claim is made
that this explicit representation is minimal.

The current constructor builds incidence lists by scanning variables against
clauses. Candidate generation rescans false clauses and template variable
positions at each queue step; it is not an O(1) transition. Signature updates
visit incident clauses and perform Python arbitrary-precision bit operations.
Lookup checks template containment and scans retained signatures, followed by
full model checking, canonicalization and publication on a hit. Complete clocks
include these costs even where counters isolate only clause evaluations.
Cold checking reconstructs both seed observations and the bounded exploration.

A small deletion budget alone cannot supply the missing efficient construction.
For arbitrary CNF G and a fresh variable z, F = G and z and -z is immediately
refutable; deleting -z gives G and z, satisfiable exactly when G is satisfiable.
Thus finding every satisfiable one-deletion witness of such templates already
includes arbitrary SAT. This reduction identifies the obligation; it proves
neither an unconditional lower bound nor P unequal to NP. The earlier polynomial
signature-count bound does not remove it.

## Historical screen

The screen excludes the entire active-support decision catalog from its seeds.
For its six previously identified hard targets, the minimum number of query
clauses violated by an old witness is one in every case, including four UNSAT
queries. No single flip in a violated clause repairs any of the six. This is a
preserved failed heuristic, not a satisfiability classification.

Caps of 0, 64 and 256 attempts per template cover 95 of that catalog's 97 SAT
queries. At 1,024, historical case 137 is reached; at 4,096, case 2 is reached as
well. Across three templates the latter uses 12,288 attempts, keeps 3,276 distinct
assignments and 947 signatures. Every hit is checked against its complete query.
The cap for the subsequent fresh comparison was chosen from this screen. These
historical results do not themselves measure current end-to-end savings.

The screen artifacts are in `experiments/results/cnf-witness-signature-probe`.
Its unused validator fingerprint predates a stricter transfer-event check; that
exact validator snapshot is retained as `validator-preflight.py`. All sources
executed by the screen are unchanged. The timed protocol binds the final validator.

## Fresh-stream result: no additional transfers

All modes start from the current 17,532-key union and actively load the same
170-entry negative index. Selection excludes 1,344 prior sidecar answers and
cached full roots, then takes the next 64 salted two-deletion queries from each
of the three templates. Three balanced fresh-process triples visit all 192
queries twice. Tests, builds and profiles do not overlap the timed workers.

| Mode | Expansions / splits | Extra model transfers | Complete seconds | Mean peak RSS bytes |
| --- | ---: | ---: | ---: | ---: |
| Active negative index, existing witness route | 214 / 68 | 0 | 10.68687 | 502,360,747 |
| Add signatures of existing models | 214 / 68 | 0 | 10.73314 | 574,297,429 |
| Also explore 4,096 flips per template | 214 / 68 | 0 | 11.33255 | 547,667,968 |

The new lookup runs only after old full-query core and one-clause witness misses.
All 96 SAT queries already succeed through that old witness route. All 118 new
lookup calls, counting both visits, miss. The other 96 answers are UNSAT; 59 use
guards, including 26 negative-support transfers and eight cached children.
The remaining 25 queries account for all 214 expansions. Every mode adds the
same 415 rows, and all nine proof databases are byte-identical. Repeated visits
add no rows. Materializing existing pending negative supports contributes 42
of the 415 rows, independently of positive exploration.

The zero-flip bank deduplicates 747 earlier SAT records to 82 assignment/signature
states. Exploration retains 3,282 assignments but only 945 signatures after
12,288 attempts; 103,961 incident-clause evaluations and 37,952 signature tests
are charged. The raw witness bank grows from 36,527 to 2,955,127 bytes. All seeds
in this comparison are already acquired, including the two historical targets;
this is a different seed batch from the screen. A fixed FIFO budget also makes
discovery order-sensitive, so additional seeds do not imply a monotone signature
frontier at the same cap.

Exploration increases total runtime **6.04%**, with regressions in every triple
(5.49%, 7.28%, 5.37%). Zero-flip lookup differs by 0.43%, with mixed paired signs;
there is no demonstrated speedup. Mean peak RSS rises 9.02% for exploration and
14.32% for zero-flip lookup. The exploration pairs include a negative RSS change,
so do not interpret these noisy process peaks as an exact per-state memory cost.
Gzip plus raw sidecars grows from 12,158,436 to 15,671,480 bytes for exploration
(12,752,885 for zero-flip lookup). The explicit model bank and transfer trace,
including misses, are retained; there is no persistent-space saving.

Complete time includes restore, all preparation, discovery, lookup, full model
checks, publication, append accounting, persistence, complete cold proof/query
and negative-lineage audit, witness-bank serialization/reconstruction, compression,
row digest and transfer serialization. Imports, initial command-line JSON reads
and the final wrapper report rewrite are excluded. Selection and historical
acquisition are separately charged. Witness-bank reconstruction averages 0.46949
seconds with exploration. The control spends 40.45% on full cold audit and 33.11%
on compression, limiting total gains from search alone.

## Next targets and restart

Keep positive exploration optional. It demonstrates two previously unavailable
historical transfers, but gives no incremental coverage on the next stream.
The current residual expansion cost is entirely negative: template 6 contributes
94 expansions, template 8 contributes 69 and template 12 contributes 51. This
supersedes the previous template-12-only priority, rather than extrapolating it.

The strongest immediate coverage probe is the negative cofactor pair at new
catalog cases **123 and 189**, both template 6 with guard [130,140], costing 17
and 16 expansions. Compare their shared residual proof structure and supports;
then test transfers across different guards and templates. Other large cases
are 74 and 106 (15 each), 42, 157 and 175 (14 each). These are current catalog
IDs, not original structural case IDs. Old support acquisition remains available;
do not rebuild it or count index growth as measured coverage.

The experiment and its complete query records are in
`experiments/results/cnf-witness-signatures`. Its checkpoint preserves inherited
fields and adds `witness_signatures_study`, `witness_signatures_decisions` and
`witness_signatures_index`. The positive bank is a fixed, sealed seed batch; load
and validate it for optional use rather than silently resetting its exploration
budget. Its presence in the checkpoint does not enable it by default. The old
negative frontier and its six ordered source catalogs are unchanged.

## Validation and preserved authority

The independent audit passes: all **473 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,613 inherited decisions** and
all 192 new decisions. Fresh validation search is disabled. The union preserves
**17,947 keys / 55,951,360 SQLite / 4,291,520 gzip bytes**, adding 415 keys while
keeping every old payload. There are no alternate certificate occurrences; new
decisions have 133 direct roots and 59 guarded negative children. The old negative
index remains unchanged, including pending proposals requiring checked materialization.

Resume `experiments/results/cnf-witness-signatures/checkpoint.json`. It preserves
inherited fields and adds `witness_signatures_study`, `witness_signatures_decisions`
and the optional, sealed `witness_signatures_index`. All prior **369 sources /
4,097 artifacts / 72 manifests** remain unchanged. Runtime binds 374 sources;
the analyzer brings the ledger to 375. Structural authority remains **2,614 patterns /
259 pairs / 17 missing children**, original **17/24 / 999 steps**, separate
supplemental **24/24 / 208**, and original case 7's discovery pointer. No new Lean claim.
The manuscript builds to **198 pages** without warnings; its **64 proof blocks**
are unchanged.

The preserved negative frontier now has **113 available retained roots / 57 pending**;
pending descriptions still require checked materialization. The new manifest binds
**77 artifacts**, including the historical probe. The next preservation audit
inherits **4174 artifacts / 73 manifests**.
