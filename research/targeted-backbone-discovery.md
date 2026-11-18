# Target the split variable after binary clause covers

A useful forced variable need not occur in a wider clause that the binary model
falsifies. The optional targeted solver therefore keeps the existing whole-cover
phase, then checks the frequency-selected variable directly. If the binary model
assigns it true, search from its negative literal to its positive literal; if
false, search the other direction. A successful source-indexed path proves that
the opposite assignment is impossible. The checked survivor and excluded-branch
compiler from [partial backbone reuse](binary-backbone-reuse.md) are unchanged.

The eight-root, width-four cover phase retains priority. The targeted phase adds
at most one root search per eligible mixed residual, reusing completed cover
searches, including negative results. A cover budget stop is inconclusive and is
not cached. A variable absent from the binary core skips the query. The graph is
built lazily and shared with cover searches. Inputs with units, no binary clauses,
or only binary clauses retain the preceding dispatch; a contradictory binary
subset still closes immediately. This is established implication reasoning, not
a new SAT tractability result. Existing solver defaults remain unchanged.

For a satisfiable binary core, its model rules out one forced-false polarity.
Searching the opposite polarity is sufficient to detect whether the selected
variable is binary-forced. This does not detect all consequences of wider clauses,
nor imply that the selected variable is the cheapest one to eliminate. The extra
ranking, graph construction and search take `O(L + V_B + E_B)` time and
`O(V + V_B + E_B)` temporary space in the adjacency-list operation model, for
source literal count `L`, total variables `V`, and binary vertices/edges
`V_B/E_B`. Fixed cover limits bound retained paths by a constant multiple of
`V_B`. Full restriction, canonicalization, proof checking, publication and
historical replay remain additional costs. Later unrestricted branching can
still be exponential. There is no new Lean theorem or uniform SAT bound.

## Saved opportunities and fresh comparison

All fourteen previously missed stored sources now yield a checked path for their
frequency-selected variable, including all six ordinary split nodes. The other
eight stored sources are models/subsumption records, so fourteen is not a count
of avoided expansions. Separate empty-archive solves of the preceding sixty
whole inputs reduce stored nodes **697 -> 691**, payload **977,664 -> 973,482
bytes**, expansion calls **655 -> 629**, and propagation visits **146,471 ->
139,259**. Compiled excluded children rise two -> twenty-two. These untimed
mechanism runs do not reproduce the prepared historical prefixes.

Four serial workers compare frequency-only and targeted recognition in opposite
orders on sixty newly excluded queries. Twelve neighbours become known after
preparation; all 48 family targets remain unfamiliar. Both policies return
**44 SAT / 16 UNSAT**, with all 120 paired admission traces and 120 probe-counter
sets identical. Family metadata never enters the solver.

| Per worker, except mean times/RSS | Frequency only | Targeted |
|---|---:|---:|
| New native nodes | 252 | 250 |
| Native payload bytes | 323,614 | 321,015 |
| Ordinary expansion calls | 169 | 163 |
| Backbone selections | 2 | 12 |
| Positive lifts / negative splits | 1 / 1 | 7 / 5 |
| Compiled excluded children | 1 | 5 |
| Child propagation visits | 29,008 | 27,154 |
| Discovery propagation visits | 41,156 | 41,156 |
| Ranking literal visits | 1,074 | 8,756 |
| Shared graph edges constructed | 2,458 | 2,784 |
| Cover / extra root searches | 192 / 0 | 190 / 56 |
| Query seconds | 0.45452 | 0.32630 |
| Complete-worker seconds | 33.92844 | 31.50804 |
| Full cold replay seconds | 14.21936 | 16.38196 |
| Mean peak RSS bytes | 837,730,304 | 819,388,416 |
| Trial SQLite bytes | 85,921,792 | 85,921,792 |
| Compressed trial bytes | 6,612,991 | 6,612,877 |

The targeted phase makes 71 calls: fourteen cached searches, 56 new searches and
one absent variable. Twelve paths succeed and 58 queries miss. Extra searches
visit 370 edges and retain 359 reached entries in aggregate; 79 selected-path
edges are checked, 44 reason literals transported, and seventeen forced units
compiled. Eight whole-clause covers, sixteen cover children and four affine
extensions / 11,684 bytes remain unchanged. The net saving is **two native nodes /
2,599 payload bytes**, with **1,854 fewer child propagation visits (6.39%)**.
Changes in these totals occur only in random three-CNF; graph-colouring receives
fourteen extra searches without a node or propagation reduction.

Wall time is unstable and does not establish an end-to-end gain. Query deltas are
**-0.00495 / -0.25149 seconds** in the two orders; complete-worker deltas are
**+0.08083 / -4.92162 seconds**. Even unchanged preparation averages 9.72 seconds
in the baseline versus 5.71 seconds in the candidate, while candidate cold replay
is slower by 0.13838 / 4.18681 seconds. The raw mean query reduction of 28.21% and
complete reduction of 7.13% must not be interpreted as stable speedups. The first
pair's query reduction is only 1.51%, with complete time slightly higher. Keep
both policies optional. SQLite size is unchanged, compression saves 114 bytes,
and sidecars grow about 5.4 KB. The 18.34 MB mean RSS difference is not a scaling
bound. No timing run overlapped this study's tests, audits or profiling.

## Remaining interaction and next experiment

The candidate's stored-node census has 112 satisfiable mixed binary cores:
45 have some forced literal and 67 have none. There are no remaining missed
binary-forced frequency variables under this diagnostic. Twenty-five sources
force only other variables after full-cover exclusions. The census includes
directly published and compiled nodes; it is not an expansion count.

There are **43 sources with nontrivial signed-equivalence blocks**, twenty with
no forced literal. Of those twenty, **eleven are split nodes**, eight are models
and one is a subsumption node. Ten split nodes are graph-colouring residuals;
the other is random-three case 56, root
`d41679137b54d44719e8d87cfe761fe5c8002b058142180a66dfb234c0f5f3b0`, whose
binary clauses imply `x1 = not x8`. Source hashes and blocks are retained in
`attribution.json`. The uncapped posthoc census uses mutual reachability and
independently rules out both disagreements through 242 two-CNF counterchecks.
It is outside worker timing and is not yet an implemented substitution saving.

**Next coverage target:** reuse binary SCC equivalences to merge variables in
the full CNF, with checked bidirectional paths, exact substitution, model lifting
and a negative dependency certificate. The earlier `cnf_probe_equivalence.py`
inventory already has signed-substitution logic, but its paired-probe format is
not a native acquisition certificate. Establish that bridge and compare against
the targeted baseline before claiming reuse or smaller proofs. Prioritize the
saved eleven split nodes; model publications must not inflate opportunity counts.

Random-three cases **44 / 56** still cost **5,153 / 4,866 child propagation
visits**, with no extracted affine equations. Graph discovery costs **26,440
visits** versus 3,840 acquisition visits; cases 59/47/55 spend 4,231/4,127/3,191
visits before reaching covers. Earlier discovery admission and historical cold
replay remain separate large cost gaps. Twenty stored sources have no binary
clauses at all, and this finite corpus does not resolve arbitrary wide-clause
interaction, compact closure or uniform efficient expansion.

## Preservation and validation

Resume `experiments/results/cnf-targeted-backbone/checkpoint.json` with the
optional `experiments.cnf_targeted_backbone.AccountedTargetedBackboneSolver`.
The union preserves all **27,888 prior native payloads / twenty-two extensions**
byte-for-byte and reaches **28,145 native keys / twenty-six extensions**. It adds
112 native and eight negative composed records to 5,530 inherited records.
Four roots have alternative native evidence in the trials; the union retains
its first payload. SQLite grows **647,168 bytes**, compressed history **71,842
bytes**, including the comparator's history. Affine negatives still require the
explicit `TerminalStore` reader; no native proof silently depends on extensions.

All **1,212 tests**, **43 focused tests**, 240 chronological query audits, sixteen
publication counter audits, 48 exhaustive family truths, warm reuse and full
historical replay pass. Eight new tests include 4,096 small formulas, selected
binary-forcing completeness, unchanged cover outcomes, positive/negative cache
hits, zero cover budget with an independent target budget, missing variables,
signed transports, direct compilation, cold readers, edits and disabled leaves.
The full suite retains 44 pre-existing SQLite warnings; focused tests have none.
All 574 prior sources, 7,568 artifacts and 107 manifests remain unchanged.

The **222-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **581**. New manifest: **40
artifacts**. Next preservation audit: **7,608 artifacts / 108 manifests**.
