# Constructing support proofs only after a match

Separating support descriptions from their proofs avoids most unnecessary proof
construction on this stream. Deferred construction makes the same 23 transfers
as eager construction, while publishing 209 support-proof nodes instead of
1,310. Complete time falls 9.96% against eager construction. It still rises
9.21% against the old-bank control, because discovering the proposals costs
more than this stream saves. The mode remains optional.

## What a proposal can establish

Discovery follows the same checked negative proof DAG as the eager extractor,
but records only selected clause indices, the corresponding canonical root and
its checked source. It visits the same 1,075 negative nodes without publishing
any derived proof. The provenance mapping and containment antichain are unchanged:
145 negative guarded sources yield 112 raw supports and 104 retained proposals.
The three earlier guarded SAT results remain excluded from negative evidence.

A proposal is not a refutation. After a target contains a proposed support in
the same variable coordinates, the matcher first looks for a checked negative
core root. If absent, the frozen extractor derives and verifies that root from
the bound origin. Only then may the frozen subset rule publish the target
refutation. A missing, positive or mismatching origin cannot supply an UNSAT
answer. A malformed proposal may fail or leave valid partial derivations; it
cannot bypass the proof checker. Reopening a pending proposal requires the
persisted checked origin. Derived proofs use ordinary archive rows and need no
special trust flag.

For a guarded target, the stronger UNSAT premise and its checked deletion guard
are still needed to establish the full query answer. A negative residual alone
is not the complete-query identity. The proposal route does not discover new
variable renamings or remove this recomposition obligation. The experiment owns
its process during the scoped extractor substitution; this is not a shared
multithreaded service API.

## Construction-policy comparison

The latest authority already contains 16,320 keys and the complete 104-core
bank. Rebuilding that bank would not be necessary in a warm run. This study is
an explicit construction-policy ablation on identical historical **14,630-key
pre-acquisition clones**. It preserves the latest authority, excludes all 768
previous sidecar answers and all cached complete roots there, then selects the
next 64 double deletions per original template. Selection costs 1.70757 seconds
separately. These are constructed neighbouring development inputs, not an
independent arbitrary-SAT benchmark.

Three balanced fresh-process triples compare the old bank alone, eager support
construction and deferred construction. Each visits 192 queries twice. No tests,
builds or profiles overlap timed workers. Discovery, construction, checking,
query work, persistence, full cold replay and compression are charged. The new
outer clock also includes final row digest and report generation, previously
excluded from worker time. Imports, command-line protocol reads and the wrapper's
final report rewrite remain excluded. Historical acquisition remains separately
charged; percentages from previous streams or timing boundaries cannot be combined.

| Measurement | Old bank | Eager construction | Deferred construction |
|---|---:|---:|---:|
| New support hits | 0 | 23 | 23 |
| Fresh expansions | 302 | 177 | 177 |
| Split nodes | 93 | 56 | 56 |
| Support-proof rows constructed | 0 | 1,310 | 209 |
| All new rows | 440 | 1,648 | 547 |
| Mean discovery/preparation seconds | 0 | 2.23097 | 1.22612 |
| Mean two-visit query seconds | 1.65512 | 1.11094 | 1.32445 |
| Mean complete seconds | 9.43274 | 11.43996 | 10.30105 |
| Mean cold replay seconds | 3.69117 | 3.83854 | 3.59897 |
| Mean compression seconds | 3.00149 | 3.15543 | 3.06015 |
| Mean peak RSS, bytes | 411,566,080 | 435,737,941 | 419,261,099 |
| SQLite bytes | 48,214,016 | 49,631,232 | 48,181,248 |
| Gzip bytes | 3,784,888 | 3,968,768 | 3,791,179 |

Deferred construction reduces support-proof construction 84.05% and total new
rows 66.81% against eager construction. Its complete runtime improves in all
three matched triples, by 8.92–11.57%. Moving construction into query handling
makes query time 19.22% higher than eager construction; the complete measure
still improves. Mean peak RSS is 3.78% lower, but individual samples range
widely and paired memory differences change sign. This is not a robust memory
improvement claim. SQLite falls 2.92%, gzip 4.47% against eager construction.

Against the old bank, expansions fall 41.39% and query time 19.98%, but complete
runtime is 8.70–10.16% higher in every triple. Mean peak RSS rises 1.87%; gzip
rises 0.17%. SQLite is 0.07% smaller despite 24.32% more new rows, because rows
have different payload sizes. Including raw sidecars, neither support mode
reduces retained bytes against the old-bank control. Saving expansions alone
does not establish a total-cost gain.

## Reuse, liveness and the next gap

All modes return 93 SAT and 99 UNSAT answers: 93 witness publications, 45 old
full-query core hits and 54 negative guards. Ten restricted targets are already
cached. Both support policies use the same 19 cores for 23 previously uncached
targets. Deferred construction invokes the extractor 19 times, then reuses
existing proofs for the other four hits. Its final archive contains 21 of the
104 proposed roots; 83 remain pending. Every one of its 209 materialization
rows is needed by the observed query proof closure. Eager construction stores
1,101 additional preparation rows not needed by that closure. This is a
post-hoc dependency observation, not a general minimum-proof guarantee or an
online rule that selects cores using future queries. Repeated visits add no rows.

All 177 remaining expansions belong to 21 negative queries. Template 8 contributes
90, template 12 contributes 62, and template 6 contributes 25. The largest cases
are 164 (20), 35 and 160 (17 each), and 16 and 136 (16 each). These are IDs in
this study, not original structural case IDs. Every measured support hit still
shares the guard clause of its first origin. The stream does not demonstrate
cross-guard or broad cross-category transfer.

The remaining avoidable acquisition cost is proposal discovery and source
checking: 1.22612 seconds here, against only 0.33067 seconds of query-time
saving over the old bank. Reuse the existing ready bank and persisted proposals;
do not rescan all historical proofs to rebuild them each run. Before adding
another global recognizer, profile discovery on genuinely new negative sources
and inspect the unmatched template-8 targets for shared conditional supports.
Source identity, raw coordinates, guard validity and proof checking must survive
any incremental discovery/index scheme. Cold replay and compression remain the
largest total-time phases (34.94% and 29.71%). No checker optimization is justified
by these phase totals alone.

Discovery still traverses the acquired negative proof DAG. If its size is D and
its literal volume is L, the cost includes visiting these records, support
preimage transport, canonicalization and antichain construction, not merely O(D)
constant work. The current matcher scans up to K supports and their clauses per
novel target. Materialization costs the proof subgraph required by matched
origins and any derivations the frozen extractor constructs along the way;
shared memoized nodes are reused within the owned session. Support proposals,
source records, ready proofs and per-query evidence all occupy space. D and the
materialized subgraphs can be exponential in the original input length. This
changes construction policy, not the unrestricted-SAT complexity bound, original
structural closure, or Lean proof coverage.

See the [reproducible artifacts](../experiments/results/cnf-deferred-support/README.md).

## Validation and persistent authority

All 442 tests pass, including exhaustive two-variable support comparisons,
all frozen proof kinds, no-publication discovery, malformed proposal rejection,
repeat reuse and reopening pending proposals. Independent ordinary-solver
validation checks nine complete trial archives and 3,456 query replays, every
union node, 1,037 inherited decisions and all 192 new decisions with fresh
search disabled. Eager and deferred support frontiers match exactly; repeated
trials have identical logical and physical archives within each mode.

Resume `experiments/results/cnf-deferred-support/checkpoint.json`. It preserves
the latest authority and all inherited fields, adding `deferred_support_study`,
`deferred_support_decisions` and `deferred_support_proposals`. The union contains
**16,760 keys / 51,294,208 SQLite / 4,046,593 gzip bytes**, adding 440 keys to the
latest authority. Earlier payloads win overlaps; 46 alternate certificate
occurrences remain in the trial archives. New decisions comprise 138 direct
roots and 54 guarded negative records. Preserve source, guard and child together.
The earlier 104-core ready bank remains fully materialized in this union. The
83 pending roots describe the historical deferred trial, not missing proofs in
the final union. The new proposal field retains that trial's discovery evidence;
it does not represent 104 newly discovered supports.

All 353 prior sources and 3,923 artifacts / 69 manifests remain unchanged. The
runtime protocol binds 357 sources; the post-hoc analyzer brings the ledger to
358. All 64 manuscript proof blocks remain unchanged. Structural authority stays
2,614 patterns / 259 split pairs / 17 missing children, original 17/24 / 999
steps, separate supplemental 24/24 / 208, and original case 7's discovery pointer.
No new Lean verification or broader structural closure is claimed.

The manuscript builds to 195 pages without warnings. All 64 proof blocks are unchanged.
