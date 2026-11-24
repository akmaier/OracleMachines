# Exact partial clause shortening from checked guards

Updated 24 November 2026. This extends the sufficient recognizer in
[selected-support clause covers](guard-cover-support.md). The implementation
is an offline experiment. It changes neither live solver dispatch nor the
cumulative history used as causal input.

## Construction and exact recomposition

At a conditioned source R, construct a graph from its actual unit/binary clauses
and checked guard consequences whose supporting clauses are present. A path
from not-l to l proves that every model of R satisfies l. Restrict R by l and
rebuild the graph. A wider source clause can now become binary, exposing another
forced literal or an SCC contradiction. Each successful round fixes a previously
live variable. A budget stop or absence of a useful forced literal is unresolved,
never UNSAT.

The discovery program records each path in source coordinates. Before any new
native write, a separate replay binds every transition to the actual conditioned
source or a checked guard, verifies the final contradiction, and collects its
original clause support H. Compilation refutes the rejected branch of every
forced choice using the existing path compiler, then joins it with the refuted
live branch using the existing native split rule. The final contradiction uses
existing empty, unit or split certificates. There is no new trusted proof rule.

The selected support need not be an independent component. Replaying the same
program on normalized H yields a reusable negative root; one existing negative
subset wrapper lifts that result to F. Missing support invalidates reuse. Changed
clauses outside H are allowed, including clauses sharing variables with H. An
explicit full-context fallback handles evidence coordinates absent from H.
This is order-preserving normalization, not general semantic canonicalization
or minimum-support discovery.

The reasoning is elementary. If G is a consequence of R and G entails l, then
R is satisfiable exactly when R restricted by l is satisfiable. Iterating this
identity and checking the terminal contradiction justifies the refutation.
It does not say that an arbitrary CNF has useful short guards or forced literals,
or that every UNSAT input reaches this terminal condition.

## Evaluation scope

The census replays all 615 saved satisfiable-graph events from eight previously
unresolved queries. It binds all available local templates to the actual source;
the old SCC and cover comparisons use that same supported graph. Discovery allows
32 forced rounds, 64 cumulative BFS roots, 16,384 cumulative visited BFS edges and
256 edges per witness path. Source scanning, normalization, template checking,
SCC construction and program storage are additional work outside those BFS caps.

There are 142 refuted events, representing 97 distinct local roots. Of these,
104 events / 67 roots are missed by both initial SCC contradiction detection and
the older full-clause cover detector with matching relaxed BFS budgets. All 67
are already retained after ordinary search. One other root is absent from that
archive, but it closes with zero shortening rounds: supplying additional checked
guards enables its initial SCC contradiction. Credit that observation to the
supported-guard inventory, not partial shortening. No whole query is rerun or
newly completed.

The remaining 473 events consist of 388 root-budget stops and 85 attempts with no
useful forced literal under this policy. The miss costs remain in the record.
Every discovered configuration enters a matched three-arm comparison: capped
ordinary search, full-context compilation, and selected-support compilation.
Eight supplied chain controls add depths 1/2/4/8 with 0/64 overlapping padding
clauses. Two alternating serial repetitions use isolated worker processes, for
630 workers in total. Discovery and initial source binding are reported separately
and must be added to compiler costs; earlier template acquisition is additional.

The new tests also check all 256 subsets of the eight-clause separation against
all 64 assignments, 200 unlabelled random formulas, signed permutations, repeated
shortening, satisfiable edits, malformed programs and cold reuse. A first test
harness draft used the wrong SQLite column name; that failed draft and log are
preserved. The correction changes only the test query.

## Resource obligations

Let r be the number of forced rounds, P the total path length including the two
terminal paths, and S the source literal count. Conditional on supplied checked
supports and an accepted program, native compilation uses O(r+P+1) proof nodes
before reuse. When required coordinates survive in H, selection gives a word-content envelope
O((r+P+1) S_H + S_F), including the enclosing wrapper and full child keys.
The compiler does not claim H or the paths are minimal.

A cold hit on the exact H root can avoid new core proof nodes, but validation,
source membership, normalization, input scanning and one enclosing wrapper remain.
The prototype retains complete replay frames and rebinds templates after every
round, so smaller persistent records do not establish the same RAM saving.
Neither the BFS budgets nor the proof-content envelope is a whole-process time
or memory bound. Automatic useful guard acquisition, complete arbitrary-CNF
coverage, live routing and a favorable total-cost comparison remain open.

## Matched costs and persistence

| Sum of per-case means, 97 local CNFs | Ordinary search | Full-context shortening | Selected-support shortening |
| --- | ---: | ---: | ---: |
| Solve/compile seconds | 2.31647 | 11.73316 | 4.93164 |
| Complete-worker seconds | 6.73768 | 27.67483 | 10.33868 |
| Cold replay seconds, both readers | 3.18738 | 10.47503 | 2.29620 |
| Stored records | 928 | 3,535 | 3,630 |
| Record bytes | 9,938,150 | 35,017,067 | 4,416,810 |
| SQLite bytes | 19,255,296 | 55,173,120 | 8,245,248 |

All three arms refute all 97 local cases and all eight controls. Selected
supports reduce compilation time 57.97%, complete-worker time 62.64% and record
bytes 87.39% relative to full-context compilation. Record count increases 2.69%.
The sum of per-case mean peak RSS falls 9.50%, which is neither the same saving
as record bytes nor a simultaneous process-memory total.

Ordinary search is faster: selected-support compilation alone takes 2.13 times
its solve time. Adding binding and discovery for the 97 selected configurations
adds 0.68089 + 2.47280 seconds, giving 8.08533 seconds before earlier acquisition
and any miss costs. Across all 615 events, binding takes 5.16800 seconds and
discovery 15.40578 seconds, including the unresolved attempts. Those totals are
not a matched end-to-end comparison against the 97 positive-only solves. They
show why a selective live policy and charged acquisition remain necessary.

The eight supplied chain controls also regress versus ordinary solving:
full/support/ordinary solve times are 0.05727/0.05229/0.02087 seconds; complete
worker totals are 0.19570/0.17214/0.14262 seconds. Record bytes are
62,935/37,298/37,253. Fewer SQLite pages do not imply less logical proof content
or faster solving.

A separate support-only stream closes and reopens the archive between four
contexts with padding 4/16/64/256. The first writes 12 records; each subsequent
context reuses the same support and writes one wrapper, with no new core node.
Record bytes grow 4,345 / 5,155 / 6,637 / 11,146. Every older row remains
byte-identical and both readers replay every snapshot. This establishes exact
reuse after reopening, not a matched stream speedup. Earlier cumulative history
is unchanged; the new checkpoint links 315 independently audited supplemental
archives and preserves every earlier bank.

## Next bottleneck and validation

On the previously most expensive miss (target 37, event 17), an instrumented
run spends 0.481 cumulative seconds in local hint binding and 0.395 in
normalization, within 0.554 cumulative seconds in discovery. It performs 265
normalizations across 19 conditioned states. These overlapping profile times
are diagnostic, not additive or an uninstrumented speed estimate.

The highest measured next target is one immutable normalized context and clause
position map per conditioned state, shared by its guard checks. Preserve all
reason and conflict checks, rebuild the binding after every assignment, and
compare exact programs, proofs, misses and total costs. Reducing repeated binding
may make broader root exploration affordable; it does not resolve the 388
budget stops or guarantee useful short guards. Root selection and automatic
origins remain coverage obligations.

All 1,823 solver tests and 32 focused tests pass. The full run retains 44 SQLite
ResourceWarnings; focused checks have none. All 1,006 prior frozen sources,
173 prior manifests / 17,347 artifact entries, the cumulative six-table history
and 64 manuscript proof blocks remain unchanged. The 315 supplemental archives
are verified with both frozen snapshot readers. Resume
`experiments/results/cnf-guard-shortening/checkpoint.json`. No new results are
automatically inserted into live causal search.
