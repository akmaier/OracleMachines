# Reusing failed reachability searches during shortening

Checkpoint: 24 November 2026. This extends the optional
[shared-context detector](shortening-context-reuse.md), using the same 615 saved
events and checked guard templates. It improves bounded local recognition;
ordinary whole-query results do not change.

## The reusable structure

For a candidate literal r, a completed unsuccessful BFS gives a set R containing
r, excluding -r, and closed under every outgoing graph edge. Every path from r
stays in R, so it cannot reach -r. R need not remain the *exact* reachable set.
Deleting edges preserves this certificate. An added edge (u,v) only threatens
it when u is in R and v is outside R. An inverse membership index identifies
the potentially affected certificates, which are invalidated before reuse.

Certificates use original source literals, including polarity. They never use
the shrinking local variable numbers. Each round rebuilds the graph from the
current checked source and guards, then compares its exact edge set with the
previous graph. The cache is private to one discovery call. It neither survives
process restart nor authorizes a SAT or UNSAT answer. A found contradiction
still needs the existing independent path, template and native proof checks.

The first version independently rescanned the complete graph on every cache
admission. Its preserved exploration found 199 refuted events, but spent over
five million additional edge checks and stopped 26 attempts at that budget.
The second version admits internally completed BFS results without repeating
their closure scan: queue exhaustion means every outgoing edge of every reached
vertex was already inspected. Supplied sets still require the full check.
Interrupted traversals are never admitted, and an incomplete update clears the
cache and stops discovery.

## Matched discovery comparison

Two alternating, isolated repetitions per target compare four modes. Times are
the sums of per-target two-run means, in seconds; they are descriptive samples,
not confidence intervals. Every miss is included. The complete phase includes
initial local binding, discovery and event serialization. Input/protocol loads,
process startup, original guard acquisition and final audits remain additional.

| Mode | Refuted events | Distinct roots | Discovery | Complete phase |
|---|---:|---:|---:|---:|
| Original, 64 fresh BFS roots | 142 | 97 | 6.55291 | 11.74840 |
| Original, 128 fresh BFS roots | 211 | 139 | 8.75225 | 13.96009 |
| Cache with full admission check, 64 roots | 199 | 132 | 9.11839 | 14.35201 |
| Cache with completed-BFS admission, 64 roots | 202 | 134 | 8.62661 | 13.84983 |

The selected cache gains 60 events and 37 distinct local roots with no lost
refutations versus the original 64-root policy. All 37 roots are already present
in ordinary whole-query search archives. The 128-root control finds more at
nearly the same observed runtime. Neither alternative dominates: four events
are cache-only and thirteen are larger-budget-only. Combining outcomes after
the fact is a coverage inventory, not a free live portfolio.

The selected cache leaves 320 root-budget stops and 93 attempts without a useful
forced literal. A stop is unresolved, not satisfiable and not evidence that no
stronger structural method applies. Initial binding remains about 5.19 seconds.

## Charged costs and limits

The selected cache performs 30,784 fresh BFS traversals and 369,897 BFS edge
visits, versus 53,118 and 564,931 for the 128-root control. It adds 15,883 cache
hits, 10,274 invalidation checks, 1,118,390 graph-delta edge visits, 310,254 index
insertions and 156,191 removals. Comparing BFS work alone hides these costs.

Both cache modes retain the 32-round and 256-edge witness-path limits. Their
16,384 checking cap per attempt covers BFS visits, full admission checks where
used, and relevant added-edge invalidation checks. Graph construction, edge-set
conversion/differences/sorting, lookup, index maintenance, source scanning,
normalization and template checks are additional. Cache hits do not consume
fresh BFS slots. This is consequently not an equal total-work budget.

With M retained memberships and E graph edges, cache storage is O(M+E) in word
units: each membership also appears in the inverse index, and updates temporarily
hold old/new edge sets. The limit M <= 16,384 is not a process-RAM limit. The
largest observed M is 1,456. Maximum census-worker peak RSS is 80,822,272 bytes
for the original 64-root policy, 81,608,704 for 128 roots, and 83,378,176 for
completed-BFS reuse. These small-run measurements include interpreter and other
state; they do not establish a general memory ratio.

For A added edges and d(u) certificates containing u, an update scans old/new
edge sets, sorts A, inspects relevant memberships, and removes invalidated sets.
Expected hash-table work includes O(E_old+E_new + sum_(u,v in A) d(u) + D), where
D counts memberships removed; sorting and allocation are additional. Worst-case
hash behavior and source preparation are not hidden in this expression. A new
edge can invalidate every stored set. No global compactness or arbitrary-SAT
polynomial bound follows.

## Reproduction and remaining gap

All 37 newly recognized local roots enter 222 isolated compilation workers: two
alternating repetitions of ordinary search, full-context compilation and
selected-support compilation. Every arm returns UNSAT, verified against the
source by both existing native readers and checks of all six authority tables.
Warm rechecks add no records. Timings below exclude prior binding/discovery,
input loading, process startup and final report writing.

| Method | Solve/compile s | Cold audit s | Complete phase s | Records | Record bytes |
|---|---:|---:|---:|---:|---:|
| Ordinary search | 1.08273 | 1.39225 | 3.01905 | 400 | 4,665,940 |
| Full-context compiler | 7.55455 | 7.25958 | 17.82919 | 2,282 | 25,419,955 |
| Selected-support compiler | 2.61820 | 1.30900 | 5.29984 | 2,302 | 3,153,584 |

Selected supports reduce compile time 65.34% and record bytes 87.59% versus full
contexts. They retain 32.41% fewer record bytes than ordinary search but take
more time, before adding discovery. More, smaller records explain why a node
count alone reverses the storage comparison. Maximum worker peak RSS is
62,291,968 / 69,730,304 / 51,707,904 bytes in the same order. Compressed archives
and actual compression times are retained; record bytes are not database pages
or total retained experiment storage.

All 1,839 solver tests and 32 focused tests pass. All 754 positive programs
across the four policies receive independent source-bound replay checks. The
archive audit checks 111 distinct new databases with both native readers and
preserves 175 prior manifests, 19,708 prior artifact entries and 1,015 frozen
sources. The new checkpoint binds 1,021 sources. The cumulative reference bank
is unchanged; these proof archives are supplemental.

The result directory is `experiments/results/cnf-reach-reuse`. It preserves both
explorations, the initial six-test source snapshot, all four matched censuses,
complete discovery programs, local compilation comparisons and compressed native
proof archives. The second exploratory launcher substituted the completed-BFS
module; the protocol binds that actual module explicitly rather than treating
the launcher's inherited fingerprint list as sufficient provenance.

The evidence argues for measured routing and structural root priorities, rather
than unconditional caching or larger budgets. The four cache-only and thirteen
larger-budget-only events give concrete counterexamples to a single dominant
policy. Inspect their reachable sets, forced-round progress and remaining budget
before proposing a predictor. Charge that predictor and retain failed cases.
Useful automatic guard acquisition, held-out whole-query gains, compact closure
and uniform bounds for arbitrary CNFs remain open.

Two instrumented diagnostics, target/event 1/25 and 37/17, illustrate the opposite
coverage outcomes. In both, preparation of each conditioned state dominates
cumulative discovery time; normalization remains a large part. Those cumulative
entries overlap and profiling changes the timings. This suggests coupling any
root-priority experiment with a check of incremental state preparation, rather
than expecting fewer BFS traversals alone to produce an equal runtime saving.
