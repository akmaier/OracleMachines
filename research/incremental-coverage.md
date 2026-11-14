# Reuse the finite coverage graph across an expansion

`experiments/cnf_incremental_coverage.py` retains the complete reachable rule
graph used by the existing coverage composer. After an append-only expansion,
it compares the complete checked external-route catalog, checks changed reachable
sources and new descendants, and propagates newly justified premises through a
reverse dependency index. It does not repeat traversal of every old pattern.

This is a maintenance improvement for an already acquired finite graph. It adds
no SAT category and does not reduce the cost of discovering the graph in general.
The separate discovery checkpoint remains
`experiments/results/cnf-local-forcing/report.json`, with the same unresolved
22-variable / 88-clause source and all five evidence lists.

## Authority and invalidation

The caller must preserve historical pattern payloads and recognition policy,
and must provide the **complete newly checked external-route catalog** at every
update. The measured transition uses the hash-bound, conflict-checked append
from the preceding forced-reduction experiment. The index rejects removed rules
or changed premises, including at currently unreachable external sources.
Deletion, replacement or a policy change requires rebuilding the index.

A pending route may become available when its target is acquired, without a new
route record. The complete route loader must therefore refresh pending records
before comparison. Only comparing inserted route records would miss this case.
The real pending-forced-route test exercises it. Source-local partial maps and
positive-only proof bundles do not satisfy this catalog contract.

For each source, alternatives are OR choices and each rule's child list is an
AND obligation. Both split children remain mandatory. Duplicate canonical child
identities retain two premise occurrences, even though one child's derivation
discharges both. A closed base has no premises. An unsupported cycle never
starts propagation. An old unresolved result can become closed; the index does
not freeze unsuccessful results as final answers.

## Why the update preserves the least fixed point

The old composer and this index use the same checked `options` function. The
initial graph includes every reachable option. Each justified source has a
finite ordered derivation whose premises were justified earlier. This invariant
holds for zero-premise rules and is preserved whenever a waiting rule reaches
zero remaining premises.

An append preserves old derivations. Comparing the entire external catalog finds
every changed reachable source; following its new premises includes every newly
reachable source and all its options. Immutable internal nodes need no rescan.
New rules begin with exactly their unproved premise occurrences, and the reverse
index decrements each such occurrence when its source first becomes justified.
When the queue is empty, every rule with justified premises has a justified
conclusion. The result is a fixed point containing the old least fixed point.
Every added justification has a finite derivation, so it belongs to the new least
fixed point; conversely induction on any finite derivation shows that its
conclusion is eventually justified. Thus the updated closure equals full
recomposition for the same finite catalog.

This argument concerns the implemented graph algorithm, with checked rules and
the stated immutability/completeness assumptions. It is not a new Lean refinement
of the Python implementation. Noncoverage means absence of a complete structural
plan in this finite catalog, not UNSAT or impossibility of another SAT method.

## Persistence and cost boundary

The serialized index interns each source key once per graph and stores rule
descriptors with integer child references. It retains the external catalog,
including currently unreachable sources. It does not trust serialized closure
flags: cold loading recomputes propagation and compares every reachable source's
entire option set against the authoritative inventory and complete checked
routes. Missing alternatives, omitted nodes, altered premises, extra unreachable
nodes and changed root bindings are rejected. Full authority and evidence remain
required; the index is additional reusable state.

Once the checked catalog is supplied, an update pays for comparing that catalog,
checking changed sources and newly reachable nodes, adding their rules and
premises, and discharging affected reverse dependencies. Across append-only
updates, each node is justified at most once and each waiting premise occurrence
is discharged at most once. This does not bound rule discovery or the size of
the acquired graph. Key and descriptor encoding/comparison bytes are charged;
these are not constant-size machine identifiers in the implementation.

Certificate output still traverses the needed proof and scans justification
order, and the comparison additionally runs the original plan checker. Full
snapshot serialization and cold completeness checking remain proportional to
the retained graph and its semantic dependencies. Both the full and the
without-growth control graphs are stored, adding duplication. A future delta
format or shared graph representation would need its own checked binding.

## Reproduction

Run `python3 -m unittest solver.test_cnf_incremental_coverage` for the new tests.
The exhaustive check covers all 512 directed graphs on three vertices and all
eight choices of bases; further deterministic mixed AND/OR update sequences
compare every step against full recomposition and replay its proof. Tests also
cover cold artifact corruption, failed-update preservation, unreachable routes,
both-branch coverage and real pending-target admission.

Run `python3 experiments/compare_cnf_incremental_coverage.py NEW_DIRECTORY` to
replay the saved forced update. This leaves the discovery archives unchanged.
The two warm arms use the same verified parent and complete refreshed catalog,
with order reversed on the second repetition. Reset copies for this repeated
experiment are outside timing. First construction, authority reconstruction,
route refresh, snapshot serialization and cold replay are recorded separately.

## Measured result and the remaining bottleneck

The saved forced append introduces one route and one unresolved target. The full
index grows from **12,802 to 12,803 reachable sources**, with **12,906 rules /
13,387 premise occurrences** after the update. Each incremental arm checks only
the changed source and new target in each of the two graphs: **four option-source
checks**, versus **25,605 source visits** for full recomposition. No new source
becomes justified. Both methods preserve **58/83** covered development cases,
including in the without-growth control. This is finite structural coverage,
not a new SAT answer.

| Measured operation | Seconds |
|---|---:|
| Initial authoritative reconstruction | 21.71711 |
| Initial complete route preparation | 6.33774 |
| First construction of both indexes, including historical node checking | 55.68532 |
| Complete external-route refresh with warm verifier caches | 0.94030 |
| Warm full composition and original proof checking, mean | 0.26146 |
| Warm incremental update and original proof checking, mean | 0.03949 |
| Full post-update catalog audit with warm caches | 0.18862 |
| Serialize and compress both complete indexes | 7.96452 |
| Cold full recomposition, including route preparation | 62.62709 |
| Cold index loading/completeness audit, including route preparation | 64.41089 |

The narrow warm operation saves **84.90%**, but its two control samples are
**0.11338 and 0.40955 seconds**, versus **0.03760 and 0.04137 seconds** incrementally.
Do not treat two variable control samples as a stable speedup estimate. Adding
the measured shared complete-route refresh to each mean reduces the indicated
saving to **18.47%**. The roughly 55-second old cold composition cost mostly
disappears already with warm historical validation caches; it must not be
attributed entirely to the new graph index.

Cold replay is **1.78381 seconds slower** with the persisted index. It checks the
same **22,603 historical nodes / 191,717,696 node-JSON bytes**, because exact cold
catalog validation still invokes the original semantic validators. Serializing
the full snapshot also costs much more than one warm update saves. These are
retained regressions and costs, not hidden preprocessing.

The complete pair of indexes is **94,113,609 raw JSON bytes / 11,241,021 compressed
bytes**, additional to the unchanged **770,371,584-byte** authoritative SQLite.
The full graph's source keys alone represent **38,413,298 encoded bytes**. The
without-growth graph duplicates most of that logical data. Existing verifier
caches are still retained during warm use; the measurements establish no peak
RAM reduction. The complete study takes **232.70213 seconds**, including both
cold controls, first construction, integrity checks and serialization.

The immediate next step is **useful discovery in a bounded warm session**: retain
the checked inventory and graph while advancing the 22-variable leaf, and charge
the first restoration/build once. Ordinary candidates remain **16, 18, 21, 22**,
and saved split pairs rank **13, 5, 6, 11**, in the new source's coordinates. Keep
one admission allowance and preserve every acquired delta. Complete route refresh
is now the larger repeated warm maintenance cost; avoid replacing it with a
partial catalog without a checked pending-edge dependency index. Cold semantic
revalidation and full-snapshot persistence remain open, so this prototype should
not replace full composition for isolated cold runs merely because its warm
microbenchmark is faster.
