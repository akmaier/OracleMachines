# Exact subset filtering with independent replay

The preceding [additive-elimination profile](additive-elimination.md) identified
repeated subset search inside structural recognition as a measurable cost. This
follow-up changes that search, preserving its exact certificate policy and the
whole acquisition database. It does not expand structural coverage or change
the ordinary SAT solver.

## A negative result for whole-input caching

The retained trace replays the previously costly source at original corpus index
1444: 48 variables and 204 clauses, from the previously paid prefix. Its 1,694
subset calls contain 851 distinct ordered CNFs. There are 843 proposal calls and
851 checking calls, with no repeated source within either role. Separate LRU
caches with 64, 256 or 1,024 slots therefore all have zero hits. Sharing unchecked
proposal results with the checker would defeat the intended independent replay.
The traced output exactly reproduces the previous profile archive; the archive
is referenced, not duplicated. Instrumented trace times are not speedup evidence.

## Reuse the necessary literal condition

If a retained clause R is a subset of C, each literal of R must occur in C.
Choose one literal of each nonempty retained clause as its anchor, selecting the
least frequent source literal and breaking ties by signed identifier. Store the
clause's retained-order rank in that literal's posting list. For C, visit only
postings named by literals in C, retain strictly shorter candidates, and test
their subsets in ascending rank order. Each retained clause appears in one list,
so ranks need no deduplication. An empty retained clause is an unconditional
candidate. Equal-width duplicates use the existing exact-set lookup. Uniform
width and repeated-literal inputs fall back to the earlier implementation.

This is a per-call structural index, not a cross-input answer cache. Its source
sets, frequencies and postings are rebuilt on each call. The independent checker
validates coverage and actual retained subset witnesses, then builds its own
index from the actual source to check the exact first-witness policy. Original
implication proofs are still checked before they supply augmented-clause reasons.
No proposal index, mutable result or unchecked implication crosses that boundary.

`AnchoredImpliedInventory`, `AnchoredClauseInventory` and
`AnchoredAdditiveInventory` are optional classes. They change no persisted schema,
policy key, pivot choice or recognition budget. The matched experiment below uses
the additive allowance-two configuration solely to reproduce the profiled work;
it does not promote the negative additive-growth policy.

## Correctness and resources

`SubsetAnchor.lean` proves the necessary-literal condition, completeness with an
explicit empty-clause case, and preservation of the first matching witness when
only impossible candidates are removed. These abstract list lemmas do not refine
Python's posting construction, candidate sorting, persistence or resource costs.
The full Lean build and axiom audit pass at **4,219 declarations / 2,031 theorem
declarations**. All **521 Python tests** pass. New checks exhaust two-variable
CNFs and short ordered clause sequences, compare all 1,694 retained trace
certificates, and cover random edits, large signed identifiers, duplicate and
empty clauses, invalid witnesses, forged implication origins and cold histories.

On the indexed, distinct-literal path, setup for m clauses and L literal
occurrences requires O(L + m log m) expected container work. Let Q_j be posting entries visited for target j, q_j its eligible
ranks, r_j the subset tests actually performed and w_j its width. A conservative
expected operation account is

    O(L + m log m + sum_j (Q_j + q_j log(q_j+1) + r_j w_j)).

The temporary index, clause sets and candidate array use O(L+m) logical space.
Integer hashing/comparison, encoded bit lengths and allocator overhead remain
additional machine costs. Q_j can approach m, so worst-case candidate work can
remain quadratic; rank sorting and index preparation can make an input slower.
There is no universal runtime improvement or reduced persistent-space bound.

## Measurement protocol

The kernel benchmark replays the retained calls in five alternating-order
repetitions, including counters and equality assertions. It retains adverse
controls for uniform widths, shared literals, units, repeated literals and an
empty clause. Its trace median falls from **1.116163 to 0.556901 seconds**. The
shared-literal mixed-width control instead rises from **0.0002990 to 0.0003839
seconds**; these microsecond controls are descriptive, not robust latency claims.

Full comparisons separately charge acquisition queries, warm reuse, seed restore,
clone/open, old-row preservation, cold checking and a four-source allocation
sample. Each new final database must be byte-identical to the preceding
allowance-two archive, including ordinary-solver proofs and all rejected plans.
The already checked endpoint proofs remain applicable to these identical bytes;
we do not repeat endpoint solving or duplicate its archives. Previously paid
prefix construction and endpoint diagnostics remain part of the historical cost.

These are selected prior failures and reused controls on one host. They are not
an untouched holdout, a new full-corpus evaluation or a claim of faster arbitrary
SAT solving. The next coverage gap remains finding useful endpoint-producing
orders under a charged discovery budget, rather than merely admitting more steps.

## Complete acquisition on the original sources

On the same 83 selected prior misses, query time falls from **155.78451 to
139.68494 seconds** (10.33%), with discovery **153.95887 to 137.57819 seconds**.
Ordinary-solver time is **1.81349 / 2.09437 seconds**, with identical solver
counters and proofs; its timing variation is not a changed solving algorithm.
Both modes close the same **31/83** sources and reproduce the same
**734,814,208-byte** acquisition archive. The paid prefix is **417,370,112 bytes**,
so newly acquired space remains **317,444,096 bytes**. No retained-space gain
or reduction of the 52 open originals follows from this index.

Full cold checking falls from **111.46828 to 102.79093 seconds** (7.78%). All
40,292 pattern nodes, 1,548 source bindings and 21,838 ordinary-solver proof nodes
pass replay with no changed bytes. All paid-prefix rows survive. Four-source
peak Python allocation is **17,354,467 / 17,353,807 bytes**, effectively unchanged
in this sample; it cannot establish a full-process memory reduction.

## Repeated controls and limits of transfer

The separate 96-input repeated control retains exactly **88 closures** and the
same **465,776,640-byte** database. Query time falls **14.44058 -> 13.76681 seconds**
(4.67%) and discovery **13.22787 -> 12.50985**. Cold checking is **50.73523 /
50.49557 seconds**, effectively unchanged at this level of replication. Most
of that archive is the shared prefix. Four-source peak Python allocation is
632,786 / 632,634 bytes, again no meaningful sampled reduction. The historical
`fresh_cases()` name does not make this an untouched holdout.

The improvement is smaller than the isolated kernel gain. Recognition beyond
subset search, proof replay, original solving, source bindings and persistence
remain charged. No new source closes, no proof graph shrinks, and the larger
additive budgets remain unpromoted. A new full-corpus evaluation is not supplied.
The next investigation should return to a small budget of alternative pivot
orders, validating whether they expose a useful endpoint and retaining every
failed attempt. The current index can lower that supporting recognition cost.

Reversing mode order on the 57-leaf comparison reproduces both databases and
zero closures, with baseline / anchored query **4.48221 / 4.18113 seconds** and
cold checking **1.74265 / 1.55124 seconds**. This is a second leaf control, not
replication of the original-source or repeated-control totals. All eight cold
runs across the four comparisons preserve archive bytes. The three unique
acquisition archives and their existing endpoint evidence are reused by hash.

Full phase records: [originals](../experiments/results/cnf-anchored-subsets-originals/README.md),
[leaves](../experiments/results/cnf-anchored-subsets-remaining/README.md),
[reversed leaves](../experiments/results/cnf-anchored-subsets-remaining-reverse/README.md),
[repeated controls](../experiments/results/cnf-anchored-subsets-fresh/README.md),
[kernel](../experiments/results/cnf-anchor-kernel/README.md) and
[negative cache trace](../experiments/results/cnf-subset-reuse-trace/README.md).
