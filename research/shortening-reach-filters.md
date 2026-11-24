# Reject impossible binary-graph paths before fresh search

Checkpoint: 24 November 2026. This follows the root-budget regressions in
[ternary-first ordering](shortening-root-priority.md). The experiment adds
elementary reachability filters to both numeric and ternary-first ordering;
source reasoning and native certificate authority remain unchanged.

## Exact scope of the filters

For a nonzero candidate literal r, a directed path from r to -r cannot exist if
r has no outgoing edge, -r has no incoming edge, or the endpoints belong to
different weak components of the current implication graph. A directed path
would also be an undirected path, so the last condition is sufficient. Sharing
a weak component does not establish directed reachability.

These are conditions on the supported binary graph, not on the entire CNF.
Wider clauses can still imply -r even when that graph has no such path. Skipping
a candidate therefore authorizes neither SAT nor UNSAT. An exhausted or bounded
detector remains unresolved. Every published contradiction still requires the
existing source-bound path and guard checks and native proof replay.

The detector first tests its existing negative-search cache. On a miss it
prepares an incoming-endpoint set from the current adjacency lists. Endpoint
mode applies the two degree tests. Weak mode additionally builds an undirected
union-find index, lazily at the first candidate that survives those tests.
Each conditioned state receives a new index in its current local coordinates;
no index crosses a changed graph or variable renumbering.

Filtered roots do not spend a fresh BFS slot or generate a completed-BFS cache
entry. This is a tradeoff: after a graph change, an older full reachable set
might remain valid where the simple filter no longer applies. We therefore
measure losses as well as gains instead of assuming pointwise dominance.

## Resource accounting and comparison

For V graph vertices and E directed adjacency entries, the incoming set takes
O(V+E) scan work and O(V) extra words. The lazy union-find index adds O(V) words;
union by size and path halving provide near-linear amortized graph-index work
under ordinary word/hash-table assumptions. Find calls, parent hops, edge visits,
unions, candidate checks, rejections and the largest index are counted. Existing
adjacency storage is borrowed, not copied. Indices are rebuilt per state.

The 64 fresh-BFS-root, 32-round and 256-witness-edge limits remain. The 16,384
checking budget covers BFS and cache invalidation, while filter construction,
component checks, scoring, graph preparation and index maintenance are separately
counted and included in elapsed time. Skipping a search is not free work and
these are not equal total-work budgets.

Six policies enter two alternating isolated repetitions per target over all
615 exposed events: numeric/ternary ordering without filters, with endpoint
filters, and with endpoint plus weak-component filters. Both unfiltered
controls must reproduce their prior programs and counters. Shared forced-step
prefixes and completed programs are compared within each ordering. The filters
are fixed before this census, with no parameter tuning.

The edit test repeats the previous 48 renamed/added-clause sources and generates
48 further edits with a new fixed seed. Repeated controls must reproduce their
prior programs. Both edit groups share exposed source families and do not
establish independent-domain performance. New roots are measured against the
union of all four preceding policies, including the 128-root control and the
uncached ordering ablation.

The preserved result directory is `experiments/results/cnf-shortening-filters`.
All previous banks, sources, failed ideas and proof blocks remain intact. New
native archives are supplemental; no live query policy changes automatically.

## Clause-specific preparation

The generic census finds zero rejections unique to the incoming-endpoint test.
This is structural, not an empirical coincidence. For each implication edge
u -> v produced by a binary clause, the builder also inserts -v -> -u. A unit
clause produces one self-contrapositive edge. Consequently, an incoming edge to
-r exists exactly when an outgoing edge from r exists. The incoming-index scan
is redundant for these graphs.

The specialized implementation removes that scan and set, while retaining the
outgoing test and the optional weak-component index. Its discovery function is
AST-identical to the generic version; only filter preparation and lookup differ.
The generic implementation remains preserved for comparison. Two further
alternating isolated repetitions compare both implementations for all four
filtered policies, requiring identical programs and counters other than the
removed index scans. The specialization was chosen after the generic census,
with the contrapositive invariant stated explicitly.

## Generic census and bounded coverage

Times below sum per-target two-run means in seconds. The complete measured phase
includes initial local binding, discovery and event serialization. Acquisition,
input loading, process startup, final report writing and preservation audits
remain additional. These small repeated samples are descriptive measurements.

| Order/filter | Refuted events | Distinct roots | Discovery s | Complete phase s |
|---|---:|---:|---:|---:|
| Numeric, none | 202 | 134 | 8.56951 | 13.79011 |
| Numeric, endpoints | 204 | 136 | 8.80648 | 14.02425 |
| Numeric, weak components too | 210 | 139 | 9.49568 | 14.72403 |
| Ternary-first, none | 263 | 170 | 7.70442 | 12.94034 |
| Ternary-first, endpoints | 266 | 173 | 8.02671 | 13.25283 |
| Ternary-first, weak components too | 266 | 173 | 8.69187 | 13.92533 |

Each filtered policy retains all successes of its corresponding unfiltered
order in this census. Numeric endpoints gain two events and weak components
gain eight. Ternary-first gains three with either filter. Weak components add
no further ternary-first successes and cost more. None of these policies repairs
any of the eleven earlier ordering regressions. There is no general dominance
guarantee under graph changes and bounded cache storage.

The ternary endpoint policy leaves 245 root-budget stops and 104 attempts with
no useful forced literal. Adding weak-component tests changes these to 220 and
129, without adding a refutation. Turning a budget stop into a fixed point of
this bounded graph method does not establish SAT or a new solved category.

Numeric endpoint/weak filters reject 2,008 / 2,271 candidates by empty outgoing
adjacency; weak components reject another 7,099. The corresponding ternary
counts are 2,676 / 2,938 and 6,670. These checks occur after a cache miss.
The generic versions scan 620,786 / 632,177 / 533,755 / 550,725 incoming edges,
respectively, without gaining a rejection from that second endpoint test.
Weak indices scan the graph again and perform 1,332,800 numeric or 1,161,136
ternary find calls. The largest component index contains 242 literal vertices.

Fewer fresh traversals do not mean less total work. Ternary endpoints reduce
fresh BFS roots from 27,075 to 26,361 but raise BFS edge visits from 327,276 to
339,030 and conditioned states from 2,777 to 2,837. Weak filters use 22,953 roots,
338,595 edge visits and 2,914 states. The detector explores further instead of
simply doing less. Maximum cached membership rises from 1,409 to 1,538/1,564;
no retained-cache or process-memory reduction follows from these counts.

## Edits, proof construction and persistence

Neither the 48 repeated edits nor the 48 newly seeded edits gains a recognition
from these filters. Both groups have eight numeric-order successes and fourteen
ternary-order successes, with the same successful cases before and after each
filter. The new seed does not make these source families independent evidence.

Three roots fall outside the union of all preceding policies. All three were
already present in ordinary whole-query search archives. They enter twelve
isolated native-proof workers, with two alternating repetitions each of ordinary
search and selected-support compilation. Both existing readers validate the
answers against their sources and check all six authority tables. Warm rechecks
add no records, and the cumulative bank is unchanged.

| Method | Solve/compile s | Cold audit s | Complete phase s | Records | Record bytes |
|---|---:|---:|---:|---:|---:|
| Ordinary search | 0.04549 | 0.07722 | 0.15341 | 17 | 193,188 |
| Selected-support compiler | 0.25871 | 0.11846 | 0.51439 | 240 | 294,104 |

Across these three cases, selected-support compilation is slower and retains
more content in aggregate than ordinary search, before adding discovery. This regression is
preserved. Selected supports need not be minimal or beat a short ordinary proof.
The complete phase includes warm checking, cold replay and actual compression;
input loading, process startup and earlier acquisition remain additional.

## Matched specialization and decision

The second comparison uses 128 isolated workers: two alternating generic and
specialized runs for each target and filtered policy. Programs and all counters
except incoming-index preparation are identical. These are new matched samples;
their generic times are not substituted into the earlier six-policy census.

| Policy | Generic discovery s | Specialized discovery s | Generic complete s | Specialized complete s |
|---|---:|---:|---:|---:|
| Numeric endpoints | 8.80652 | 8.69148 | 14.04474 | 13.93310 |
| Numeric weak components | 9.46966 | 9.38382 | 14.71844 | 14.62822 |
| Ternary endpoints | 8.00335 | 7.93273 | 13.24734 | 13.17452 |
| Ternary weak components | 8.65979 | 8.57701 | 13.90524 | 13.82420 |

The specialized code eliminates the redundant scans and incoming sets exactly.
Observed discovery reductions are only 0.88--1.31%; two repetitions do not
establish a stable runtime ratio. The endpoint-only specialization needs constant
extra filter state and a constant expected adjacency lookup per candidate; the
optional weak index still needs O(V) words and construction work. This does not
establish a useful end-to-end advantage over unfiltered ternary-first discovery.

Keep both filters optional. Do not spend the next run on further weak-component
index polishing for ternary-first coverage: it added no successes beyond degree
tests, repaired none of the eleven targeted regressions, and added no edit-test
successes. The corpus now provides explicit negative evidence for that route.

The next larger cost target is repeated immutable source and template preparation
across conditioned states. Profile that work and test an owned, immutable
prepared source whose validation can be reused, retaining every check that
depends on changed assignments, supports or guards. Compare exact programs and
native records first; broader root budgets or stronger relation discovery must
then be charged separately. More path filtering alone cannot create missing
binary consequences or solve the remaining general CNFs.

All 1,853 solver tests and 30 focused tests pass. Independent replay checks all
1,411 positive census programs and the positive edit programs. Six new native
archives are checked by both readers. The preservation boundary verifies 177
prior manifests, 20,859 artifact entries and 1,025 frozen sources; the checkpoint
binds 1,032 sources. All 64 previous manuscript proof blocks remain unchanged.
The first final audit stopped on a peak-RSS aggregation initialization error;
its validator and log are retained, and the corrected audit was rerun. Timed
workers, product sources and proof results were unchanged by that correction.
