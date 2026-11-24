# Prioritize the potential yield of a shortening step

Checkpoint: 24 November 2026. This follows
[negative reachability reuse](negative-reach-reuse.md). The preceding comparison
showed complementary misses: a larger uncached budget and cached searches did
not dominate one another. This experiment changes which candidate is searched
first, while retaining the same inference rules and native proof authority.

## Fixed structural rule

For each eligible literal r, count its occurrences in current ternary source
clauses. Search in descending count order, with signed numeric order for ties.
If a checked path proves not-r, each such clause loses r and becomes binary.
The score measures potential source-clause shortening, not guaranteed new graph
edges: reduced clauses may coincide or already be present. It does not establish
that r can be excluded, that a useful path is short, or that the resulting
binary graph will refute the source.

The eligible roots remain exactly the model-false literals in source clauses
of width greater than two, as in the frozen detector. Longer clauses receive
zero immediate ternary yield; a necessary step affecting only those clauses can
therefore be delayed. Equal scores still depend on variable numbering. The rule
is a scheduling heuristic, not a canonical partition or a new inference rule.

Scores are recomputed from the checked current cofactor each round. Literal
forcing still requires a path from r to not-r. Every published program replays
source supports, guards and paths, followed by native certificate construction.
The negative-search cache, when enabled, retains its original coordinate and
invalidation requirements. Disabling it supplies a separate ordering ablation.

## Cost and scope

Root enumeration and scoring scan current clauses and their wider-clause
literals, then sort R eligible roots. Together they cost O(C+L_w+R log R) work
and O(R) words, under ordinary word and hash-table assumptions. The numeric
control already enumerates and sorts roots; the ternary tally and score-key
lookups are the main incremental operations. The pass counters below are not
all additional visits relative to that control. This is
per prepared state; state construction, guard binding and native verification
remain additional. The literal and clause scans and scored-root counts are
recorded, and sorting is included in elapsed discovery time.

The 64-root policies share a 32-round cap, a 256-edge witness limit, and a
16,384 BFS/invalidation-check limit. Scoring, graph preparation and cache
maintenance are outside that checking cap and remain charged. The uncached
ordering ablation retains the cached implementation's coordinate preparation,
so it is not presented as the fastest possible uncached solver.

The fixed rule was recorded before the new census. Four policies enter two
alternating isolated repetitions for each of eight targets: numeric ordering
with reuse, ternary ordering with reuse, ternary ordering without reuse, and
the original numeric detector with 128 roots. All 615 exposed events enter the
cost and coverage totals. The older controls must reproduce their exact programs
and counters. No parameter was selected from the new outcomes.

Forty-eight deterministic edits add signed permutations and support-preserving
clauses at three fixed chronological positions per target. They are evaluated
after the rule was fixed, but share the exposed source families. This is an edit
test, not an independent-domain holdout. All misses and losses are retained;
an unresolved result never authorizes a SAT answer.

## Matched results

Times are sums of per-target two-run means in seconds. The complete measured
phase includes initial local binding, discovery and event serialization. Input
loading, process startup, original template acquisition, final report writing
and preservation audits are additional. The sample does not establish a stable
timing ratio or a general speed guarantee.

| Policy | Refuted events | Distinct roots | Discovery s | Complete phase s |
|---|---:|---:|---:|---:|
| Numeric with reuse, 64 roots | 202 | 134 | 8.62367 | 13.87567 |
| Ternary-first with reuse, 64 roots | 263 | 170 | 7.77112 | 13.00844 |
| Ternary-first without reuse, 64 roots | 227 | 145 | 6.73860 | 11.95823 |
| Numeric without reuse, 128 roots | 211 | 139 | 8.73492 | 13.97728 |

Ternary-first reuse gains 72 events but loses 11 versus numeric reuse, for a net
gain of 61. Measured discovery time falls 9.89% and the complete phase 6.25%.
It is not a pointwise replacement for the old ordering. The uncached ordering
ablation gains 52 and loses 27, trading coverage for lower measured cost.

The cached ordering recognizes 38 local roots outside the union of both older
controls; the uncached ordering recognizes 27 of those same roots. All 38 were
already stored by ordinary whole-query search. The new comparison therefore
does not establish additional completed whole queries. The cached policy leaves
257 root-budget stops and 95 attempts without a useful forced literal.

The useful pattern is earlier closure with fewer conditioned states. Numeric
reuse prepares 3,263 states and makes 2,648 forced steps; ternary-first reuse
prepares 2,777 states and makes 2,162 steps while recognizing more events. BFS
roots fall from 30,784 to 27,075, BFS edge visits from 369,897 to 327,276, and
normalization literal visits from 10,013,857 to 8,694,145. The scoring pass
visits 902,476 clauses, 1,932,243 wider-clause literals and 207,334
scored roots. These costs remain in the elapsed-time comparison.

Maximum census-worker peak RSS is 83,361,792 / 81,739,776 / 81,133,568 /
82,673,664 bytes in table order. The largest observed cached membership falls
from 1,456 to 1,409. These small-run maxima include other resident state and do
not establish proportional memory savings or a production RAM bound.

On the 48 edited cases, numeric reuse recognizes eight, ternary-first reuse
fourteen, ternary-first without reuse twelve, and the 128-root control eight.
The two ordering variants gain six/four cases without losing an old success.
Discovery totals are 0.61159 / 0.55978 / 0.51014 / 0.60945 seconds in that order.
These are serial within-process edit checks, not independent workload evidence.

## Native proof and persistence costs

The 38 new roots enter 152 isolated workers: two alternating repetitions of
ordinary search and selected-support compilation. Both methods return UNSAT
for every source, checked by both independent native readers and all six
authority tables. Warm rechecks add no stored records. The cumulative bank is
unchanged; the new archives are supplemental.

| Method | Solve/compile s | Cold audit s | Complete phase s | Records | Record bytes |
|---|---:|---:|---:|---:|---:|
| Ordinary search | 1.06101 | 1.41328 | 3.01942 | 439 | 4,888,823 |
| Selected-support compiler | 1.77779 | 1.04039 | 3.73598 | 1,779 | 2,278,938 |

Selected supports retain 53.38% fewer record bytes but take longer to construct,
before charging discovery. More small records do not imply more content bytes.
Maximum worker peak RSS is 56,803,328 / 52,412,416 bytes. Compressed archive sizes
and actual compression times are retained separately; record bytes are not
database pages or all retained experiment storage. The policy remains optional.

## Remaining limits and next target

All eleven ordering regressions stop at the 64-root budget. Diagnostics replay
their checked prefixes and inspect simple sufficient no-path conditions:
no outgoing edge at r, no incoming edge at not-r, or different weak components.
At the final recorded states these exclude 0--17 eligible candidates. Two
regressions have zero such exclusions. These counts overlap and include cache
hits; they do not equal avoided fresh BFS or prove the regressions will close.
The measured policy has not incorporated these filters.

The next narrow experiment is to test charged structural reachability filters
before scoring/search, retaining both ordering controls. Preferably derive the
filters from already prepared graph data, measure their effect on fresh-root
consumption, and preserve the two zero-exclusion cases. Larger unresolved
interactions still need useful guard discovery, exact state reuse and held-out
whole-query evaluation. No rule here covers arbitrary CNF efficiently.

All 1,844 solver tests and 29 focused tests pass. Independent source-bound replay
checks all 903 positive census programs and all positive edit programs. Both
native readers audit 76 distinct new archives. The preservation boundary checks
176 prior manifests, 20,356 artifact entries and 1,021 frozen sources; the new
checkpoint binds 1,025 sources. All 64 earlier manuscript proof blocks remain.

The result directory is `experiments/results/cnf-shortening-priority`. Previous
banks and frozen sources remain intact. New proof archives supplement the
existing checkpoint; search scheduling does not alter certificate semantics or
establish uniform polynomial expansion for arbitrary SAT.
