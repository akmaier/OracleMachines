# Saved guards identify missed failed-literal probes

24 November 2026. The unchanged ordinary solver reaches 648 probing contexts
on the eight saved origin/edit pairs. Matching previous conditional guards
offers 394 distinct local cofactors, all independently refuted by unit
propagation. Ordinary probing does not try 260 of those polarities at their
recorded contexts; 232 use a different variable from its selected probe.
All 260 are absent from the live database when that context is first observed.
This is a measured selection opportunity, not a demonstrated faster policy.

The experiment and its causal inputs are bound in
[`protocol.json`](../experiments/results/cnf-guard-probe-census/protocol.json).
The complete results, checked proposals and native histories are retained in
[`report.json`](../experiments/results/cnf-guard-probe-census/report.json).

## Recognition and authority

The previous banks contain 395 source-checked conditional unit templates from
origins 0, 3, 27, 36, 39, 60, 63 and 66. Their clause supports all survive the
corresponding one-clause replacement. Each target restores the exact causal
history immediately after its origin, before its edit. Later repeats and the
cumulative preservation archive supply no search answers.

At an ordinary probing context, a passive observer tracks the mapping from
local canonical variables to the target's canonical source variables, together
with fixed source assignments. A guard proposes its last variable/polarity
only if all other assumptions match and that variable is present locally.
Incompatible guards, multiple missing assumptions and absent variables cannot
offer a probe. Duplicate offers for the same local variable/polarity are grouped;
their alternative templates remain retained. Root support containment is checked
before matching. The current implementation scans the eligible bank at each
context: 32,044 guard checks and 262,032 guard-pair checks in total.

A source-level exclusion alone cannot refute a selected component or clause
subset. Independent replay checks the source-coordinate injection and verifies
that every mapped local clause belongs to the restricted source. It then
restricts the **actual local cofactor** and constructs an existing native unit
certificate only if unit propagation finds a conflict. The tests preserve a
counterexample where the source guard is valid but the selected subset remains
satisfiable. Neither a guard match nor an inconclusive probe gives authority.
One negative polarity also gives no verdict on its opposite branch or parent.

The observer performs read-only presence queries before the ordinary probe,
without calling the proof reader or warming its checked cache. These queries
can see pending rows in the native transaction. Presence is instrumented
availability metadata, not proof authority or a separately replayed transaction
trace. Posthoc certificates are saved in a separate bank and never enter either
search. Original and observed verdicts, all native counters and complete SQLite
files are byte-identical for every pair. The two previously measured native
controls also reproduce their earlier counters and six-table payload digests.

## Opportunities and costs

| Edit | Observed contexts | Proposed negative cofactors | Untried polarity | Different variable |
|---:|---:|---:|---:|---:|
| 1 | 80 | 16 | 13 | 11 |
| 4 | 80 | 29 | 27 | 26 |
| 28 | 81 | 58 | 33 | 27 |
| 37 | 72 | 50 | 27 | 25 |
| 40 | 84 | 101 | 71 | 68 |
| 61 | 92 | 55 | 30 | 22 |
| 64 | 74 | 12 | 8 | 8 |
| 67 | 85 | 73 | 51 | 45 |
| **Total** | **648** | **394** | **260** | **232** |

There are 248 contexts with at least one proposal. Of the 648 contexts, 353
represent the full restricted source and 295 a strict subset. The latter
yield 134 of the 394 negative cofactors. All pass actual local checking in this
sample, but the subset counterexample rules out treating this as a general
guarantee. The 134 already tried proposals show overlap with ordinary probing;
the other 260 are distinct from one another, not 260 additional completed SAT
instances. All eight targets still stop at 256 dispatches.

One cold native/observed pair per edit takes 7.82736 / 10.30903 seconds of
aggregate solve time, a 31.71% observation increase. Independent posthoc checking
and certificate storage add 3.15887 seconds. The complete census takes 99.95011
seconds, including restoration, setup, analysis, serialization and archive
creation; earlier source acquisition and the later preservation audit are
additional. These sequential diagnostic pairs are not repeated performance
comparisons and do not isolate matching from coordinate tracking. No live
policy speedup is measured.

The observer checks 395 templates initially. Off-line validation deliberately
rechecks support at every context; sharing that work is a further opportunity.
Observed event graphs range from 881,220 to 2,344,173 charged Python bytes per
target. This excludes the template bank, tracking frames, database and transient
allocations. The 256-event and 8 MiB parent-key bounds do not bound those costs,
nor proposal child keys or all process memory. No binding or event-limit misses
occur in this sample. The standalone conditional bank is 6,144,000 SQLite bytes
and 551,089 compressed bytes. This is diagnostic storage, not a necessary live
policy footprint or total historical growth.

## Next experiment and limits

The highest-priority test is now a bounded live selector at ordinary probe
sites, using checked surviving guards to propose a variable and the existing
unit/split/model machinery to establish and compose results. It must charge
matching and source-coordinate maintenance, preserve the same dispatch budget,
and compare against ordinary probing and an order-matched control. The current
32% capture overhead makes a cheaper live implementation necessary before a
total-cost saving is credible. Avoid retaining full diagnostic event graphs in
the live route; investigate incremental guard matching only with explicit
rollback, deletion and component-binding conditions.

All eight pairs are exposed, and origin banks are provisioned. Automatic origin
recognition, variable transport across general rewrites, fresh unlabelled
evaluation and benefits outside the current ordinary probe sites remain open.
There is no claim of minimum-cost expansion, compact closure or polynomial
unrestricted SAT. These local opportunities may change the later search path;
their usefulness cannot be inferred by summing independent avoided probes.

The preservation audit checks every distinct worker database with both readers,
appends new authority without changing old payloads and replays every new
cumulative dependency. Earlier full-history audits remain hash-bound. The first
audit attempt incorrectly required an identity-sensitive Python memory charge
to survive JSON reload; its source and failure log are retained. Reloaded
graphs lose object sharing, so live and reloaded charges are reported separately.
The cumulative archive adds 232 native records and reaches 158,130; the five
other table counts remain unchanged. Its SQLite size grows by 3,686,400 bytes
to 2,065,260,544 bytes, and its compressed size grows by 341,268 bytes to
149,975,161 bytes. All earlier payloads remain byte-identical. The preservation
audit takes 271.76316 seconds, including 107.69179 seconds of cumulative gzip
creation; that maintenance cost is separate from the query timings above.

All 1,722 Python tests and 78 focused tests pass. The full suite retains the
44 existing SQLite `ResourceWarning` reports; the focused suite has none.
The manuscript builds to 257 pages without warnings, with all 64 prior proof
blocks unchanged. The sealed checkpoint binds 943 sources and preserves
162 prior manifests covering 14,809 artifact entries. Resume from
`experiments/results/cnf-guard-probe-census/checkpoint.json` with
`experiments.cnf_archive_parts.restore_archive`.
