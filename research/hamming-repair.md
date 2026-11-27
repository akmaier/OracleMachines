# Exact bounded repair and the last exposed external case

The remaining external source, `uf50-01000.cnf`, now has a complete checked SAT
model. The already exposed panel rises from **24/25 to 25/25 originals**, with
**12/12 derived controls** unchanged. This is completion of this finite panel,
not a representative coverage estimate, a new tractable SAT class or an efficient
solution of arbitrary CNFs. The prior synthetic 182/182 union remains separate.

The new optional gate runs only after the unchanged signed-choice/capacity/
conditioning portfolio leaves a source unresolved. It accepts only clauses;
filenames, publisher answers and benchmark categories never select a model.
Production defaults are unchanged. A fixed 20,000-state repair allowance closes
the one remaining source in **12,669 distinct states**, producing a model at
distance **27** from the seed. Every original clause is checked independently.
The earlier incomplete proof and rejected proposals remain preserved.

## Exact decomposition and shared structure

A deterministic greedy proposer orders clauses by decreasing width and literal
tuple, selects variable-disjoint clauses, sets each selected clause's first
literal true and its other literals false, and defaults unused variables false.
This requires no matching or truth label. On the retained random source it
reconstructs exactly the previous rejected proposal, with 26 false clauses.

For any complete seed `s`, write an assignment as `s XOR z`, where `z` is the
set of changed variables. This is a bijective literal-sign substitution with
linear occurrence volume. It preserves the SAT obligation. A polynomial
conversion to another SAT instance does not make that instance easy.

Search explores sets `M` of variables already flipped. Future steps only add
variables, so each full target has a unique final mask, even though several
branch paths may reach it. If a clause is false at `s XOR M`, every satisfying
extension must flip at least one of its variables outside `M`. Branch over all
such variables. The branches can overlap; a memo keyed by the complete mask
shares identical states without treating different states as equivalent.

Two leaves exclude all satisfying extensions within the remaining radius:

- A false clause with no unflipped variable is permanently false in this branch.
- A set of false clauses with pairwise disjoint available-variable sets requires
  at least one additional flip per clause. More such clauses than remaining
  flips excludes the branch.

These rules cover every possible satisfying assignment in the chosen Hamming
ball. A complete exhaustion excludes that ball only. With radius equal to the
actual source support it excludes the full assignment space. A state-budget stop
is **unknown**, even when the current best assignment has only one false clause.
The portfolio gate publishes only complete SAT models, not negative conclusions
from failed or interrupted search.

An occurrence index is built afresh from validated canonical source clauses.
Each flip and undo changes satisfaction counts only in clauses containing that
variable. The same source index and untouched counts serve all states; masks
share convergent paths. The checker for a SAT witness uses none of this state.
A separate exclusion checker reads source clauses and masks directly, verifies
all false-clause premises, disjoint packings and required children, and checks
that all stored nodes are reachable. Children strictly increase the mask, so
the proof is acyclic. Cold exclusion checks disable the search function.

This generalizes the repository's earlier single-transition-clause model
rotation and pure-variable repair experiments: the seed need not satisfy a
known deletion, and flips may temporarily break previously satisfied clauses.
Those interactions remain explicit through the satisfaction counts and complete
source check. This is an exact bounded search construction, not a claim of a new
general SAT algorithm or of polynomially many states.

## A checked minimum distance, not just a successful heuristic

The larger-budget supplementary diagnosis records a complete radius-25 exclusion
DAG with **35,065 states**, plus a model at distance **26** found in 6,748 states.
Together they certify that this particular seed has **minimum repair distance
26**. The radius-25 search reaches assignments with only one false clause; that
does not mean a small repair can complete them within that radius.

The exclusion JSON occupies **2,408,673 bytes**, or **272,571 gzip bytes**. Its
construction takes 0.57186 seconds, and two source-bound reload/checks take
0.10839 and 0.10938 seconds. These are additional diagnostic costs, outside the
paired pipeline benchmark, with an explicit 100,000-state allowance. The
pipeline's first model at distance 27 is sufficient for SAT; it does not perform
minimum-distance search and does not store this exclusion DAG in every trial.

## Independent checks and costs that remain

Explicit truth tables check **25,629 ball queries** over **5,108 inputs**:
512 two-variable CNFs with every seed, 3,304 three-variable CNFs with at most
three distinct clauses, 1,000 new random small CNFs, all 228 retained satisfiable
domain misses, and 64 fresh signed, edited or mixed sources. The checker accepts
12,500 SAT balls and 13,129 exclusion balls in agreement with truth tables.
An additional one-state allowance yields 2,860 explicitly unknown attempts.
All 30 fresh SAT witnesses survive a satisfied-clause addition and fail a
contradicting addition. These finite exhaustive searches do not turn the old
228 structural misses into newly recognized tractable structures.

Twenty focused tests exercise malformed inputs and seeds, sparse signed names,
duplicates and tautologies, all seeds/radii of a small formula, empty sources,
packing overlap, missing branches, changed sources, invalid masks, shared states,
budget exhaustion, cold checking, and the optional portfolio wrapper. An initial
memoization fixture failed to exercise a shared path; that failure log is kept
and the corrected fixture demonstrates actual memo hits.

The state cap bounds distinct explored masks, not complete cost. Source
normalization and sorting, occurrence-index construction, false-clause scans,
packing and branch ranking, incident updates/undos, arbitrary-width mask
operations, witness checks, copying and persistence remain charged work. If
`B` states are admitted and maximum clause width is `w`, at most `B*w` branch
edges are generated, but duplicate edges can still need flip/undo work.
Masks require up to `n` bits each, and an exclusion node may list up to `m`
clause indices. Memory is not constant per arbitrary-size source. Without a
fixed cap the number of masks in a radius-`r` ball can be the sum of `choose(n,j)`
for `j <= r`; taking `r=n` reintroduces the unrestricted exponential obligation.

## Matched full-workflow measurements

Four fresh-process pairs alternate baseline/repair order. Initial raw parsing,
source preparation, discovery/internal checks, explicit checking, JSON writes,
compression, warm replay and two cold reload/checks are charged. Every replay
reparses the source and reloads its certificate; operator banks start empty per
phase, while OS caches are not flushed. Startup, final metadata, audits and the
minimum-distance diagnosis are additional. The baseline leaves one input open;
this is not a comparison with a complete fresh CDCL solve of every source.

| Measurement | Previous portfolio | With bounded repair |
|---|---:|---:|
| Mean complete seconds | 23.43449 | 23.30960 |
| Acquisition/internal checks | 11.25582 | 11.54279 |
| Explicit checking | 2.25444 | 2.19557 |
| Warm replay | 3.20266 | 3.07918 |
| Two cold replays | 6.38662 | 6.16799 |
| Compression/persistence | 0.25650 | 0.24923 |
| JSON proof bytes | 28,912,506 | 27,489,632 |
| Gzip proof bytes | 419,973 | 402,186 |
| Maximum observed RSS bytes | 91,521,024 | 89,669,632 |

Mean complete time is 0.53% lower, with paired changes **+2.50%, −0.75%,
−1.94%, −1.78%**. The signs are mixed and the difference is small: retain the
coverage gain, without claiming a reliable speedup. More expensive discovery
is partly offset by replacing a large incomplete proof with a **1,237-byte SAT
witness wrapper**, making explicit checking and replay cheaper. Both arms add
the same wrapper layer, which changes indentation bytes relative to prior runs.

The repair builds 654 indexed occurrences, explores 12,669 distinct masks,
records 404 memo hits, generates 13,088 branch edges and performs 357,291 incident
updates. It additionally charges 499,485 false-clause literal positions, 179,075
gain occurrences and 302,934 packing-variable positions. These are different
operation categories, not a single complete instruction count. The original
26 failed clauses involve 39 variables. The radius-25 diagnostic has 23,495
split nodes, 4,944 blocked leaves and 6,626 packing leaves; convergent children
share stored masks. No source index is trusted across an edit or cold import.

## Fresh constructed boundaries at the unchanged cap

A separate protocol freezes **32 new planted-SAT sources** before running the
fixed repair policy: eight each at 50, 60, 70 and 80 variables, clause density
4.36, sparse renamed variables and shuffled clauses. Planted models validate
truth afterward and never seed the search. The repair gate finds **22 models**
and reaches its 20,000-state cap on **10 sources**. Exact inputs, audit models,
counts and all outcomes are retained. Five of the capped searches reach one false
clause, again insufficient to claim a complete model or cheap repair.

This is a repair-only constructed probe, not a fresh external benchmark and not
a claim that the full portfolio leaves all ten sources open. Its execution may
overlap independent checks, so its times are excluded from performance claims.
The largest new boundary is these ten reproducible repair failures, especially
which shared constraints prevent completion of the near models. Keep the same
cap when investigating structural reductions, and separately freeze external
inputs before transfer claims. Historical gate-only domain misses also remain
valid negative recognition evidence.

All **2,505 full and 20 focused tests pass**. Validation reproduces all eight
paired reports, source-bound checks and cold counters. All 243 prior manifests,
81,700 artifact entries, 1,326 scientific sources and 83 old proof blocks are
preserved. The new checkpoint adds one proof and five scientific sources; the
existing SQLite resource warnings and preliminary fixture failure remain in the
logs. Resume `experiments/results/cnf-hamming-repair/checkpoint.json`, key
`hamming_repair`.

## Remaining research priorities

Freeze unseen external encodings before assessing transfer beyond the now
exposed panel. Retain unresolved and budget-exhausted cases at the fixed policy;
do not repeatedly tune the cap to each source. Study which seed transformations,
small interfaces, nonclique compatibilities and reusable conditional descriptions
reduce interaction before general search. The old conservative recognizer still
misses its 228 SAT domain patterns, even though explicit small search can solve
them. Efficient recognition, compact shared negative evidence, proof reuse after
edits and unrestricted acquisition bounds remain open. Panel completion does not
resolve any of these general gaps.
