# Share checked contexts during partial shortening

Updated 24 November 2026. This addresses the repeated normalization measured in
[iterative partial shortening](guard-partial-shortening.md). The implementation
remains optional and offline.

## Change and validity conditions

For each conditioned source, compute its normalized CNF and variable map once.
When the first compatible guard needs checking, prepare one immutable context
containing that CNF, its clause positions, the coordinate map and the assignment.
All guard checks in that state share the context. The next assignment creates a
new context; changed source clauses also require reconstruction. Nothing is
retained as trusted certificate state or shared across independent calls.

The implementation reuses the previously checked `LocalContext` and bound RUP checker, with a
transport routine that restricts clauses before testing surviving coordinates. Every original template is still validated against
its source, every reduced support must occur in the local CNF, and every unit
reason and conflict is checked against that exact CNF. It removes repeated
canonical-source validation and serialization for individual guards. It does not
remove guard proof checks or change their meaning.

The old experiment is frozen. A separate implementation changes only its state
preparation function; an AST comparison fixes all other discovery, replay,
support selection and compilation functions. Independent native snapshot readers
remain the publication authority. The old implementation is never patched at
runtime, so concurrent calls and frozen controls remain independent.

Testing exposed one validity-check error in the frozen preparation: normalization
represents any CNF containing an empty clause by the singleton empty clause. Its
later equality check against all restricted clauses can reject that sound
collapse if other clauses remain. Direct source restriction handles it correctly.
A source-bound refutation, the old rejection and both cold reader audits are
preserved separately. This regression is outside the matched census; it is not
a new whole-query completion or a runtime saving.

## Matched evaluation

The discovery comparison replays all 615 saved events in two alternating serial
repetitions for each of eight targets. Each arm pays initial local template
binding, discovery including misses, and event serialization. Loading shared
protocol/origin inputs and process startup remain additional. The 615 discovery
programs must match exactly, including all path choices and budget outcomes.

The compilation comparison uses all 97 local cases and eight supplied chain
controls, with ordinary search, frozen selected-support compilation and shared
context compilation. Two alternating repetitions use 630 isolated workers.
Every archive must match its prior table digests and database bytes, and both
snapshot readers check it. Temporary archive compression is charged; verified
identical archives reference the existing files instead of adding duplicate
permanent banks. Complete-worker timing includes case loading, setup, compilation,
warm checks, cold replay, accounting and compression. Protocol/control selection,
imports, process startup, acquisition and discovery are additional.

The nine new tests compare all 729 partial assignments of the six-variable
example and all 256 source-clause subsets, with independent truth checks of
refutations. They also cover signed
renamings, unlabelled random formulas, invalid proof data, changed sources,
concurrent calls and cold persistent reuse. The initial failed test and the
empty-cofactor example remain preserved. A first timed attempt failed at case 22
because the reused transport helper checked an absent coordinate before a later
literal satisfied that clause. Native compilation rejected the unsupported edge.
The failed sources, reports and profile are preserved; the corrected transport
checks satisfaction first, and all 105 proof tables pass a preflight comparison.

## Limits and resource accounting

This is a preparation optimization for fixed supplied guards and a fixed
recognition policy. It adds no SAT category to the matched census and establishes
no live whole-query improvement. Each state still scans and normalizes source
content, checks templates and builds its binary graph. Unsuccessful root searches,
initial guard acquisition and positive-only selection costs remain charged.
The native proof representation, retained record bytes and wrapper growth remain
unchanged. Reduced normalization visits do not imply the same reduction in RSS.
The proof-content envelope remains the earlier conditional bound; no uniform
unrestricted-SAT time or memory bound is established.

## Measured results

| Discovery, sums of target means | Frozen | Shared context |
| --- | ---: | ---: |
| Initial local binding seconds | 5.18241 | 5.17864 |
| Discovery seconds, including misses | 15.41523 | 6.53121 |
| Complete measured census phase seconds | 20.63127 | 11.74341 |
| Normalization literal visits | 19,680,665 | 7,932,837 |
| Template checks | 33,377 | 33,377 |
| Unit-reason/conflict literal checks | 400,811 | 400,811 |
| BFS root attempts | 32,548 | 32,548 |
| BFS edge visits | 326,422 | 326,422 |

Discovery falls 57.63%, its complete measured phase 43.08%, and normalization
visits 59.69%. All 615 programs match exactly: 142 refutations, 388 root-budget
stops and 85 no-useful-literal outcomes. Initial binding is effectively unchanged.
These are two repetitions of an exposed diagnostic workload, not production
performance ratios. Acquisition and input/protocol setup remain additional.

| 97 local cases, sums of per-case means | Ordinary | Frozen support compiler | Shared-context compiler |
| --- | ---: | ---: | ---: |
| Solve/compile seconds | 2.32904 | 4.88731 | 3.47493 |
| Complete-worker seconds | 6.78229 | 10.31049 | 7.55220 |
| Warm-check seconds | 0.15009 | 2.57321 | 1.22838 |
| Cold replay seconds, both readers | 3.14802 | 2.27139 | 2.27283 |
| Record bytes | 9,938,150 | 4,416,810 | 4,416,810 |
| Records | 928 | 3,630 | 3,630 |

Compilation falls 28.90% and complete-worker time 26.75% against the frozen
support compiler. Ordinary solving remains faster, even before adding discovery
and initial binding. The eight supplied controls also regress versus ordinary
solving: shared/frozen/ordinary solve totals are 0.04521/0.04874/0.01910 seconds;
complete-worker totals are 0.16560/0.17384/0.14810. Keep the policy optional.
Cold replay, native storage and measured peak RSS are effectively unchanged.
Summed peak-RSS samples are not a simultaneous process-tree memory bound.

The cold-reopen stream reproduces all prior database bytes in both modes.
Its first context writes 12 records; each of three subsequent contexts writes
one wrapper and reuses the support root. Every previous row remains byte-identical.
All 105 compilation cases also reproduce their prior archives exactly. The final
audit checks 215 unique archives, mostly by reference to existing files; only
the separate empty-cofactor regression adds a new supplemental archive. No
cumulative solver bank changes or receives future-query results.

The formerly most expensive miss still takes 19 conditioned states. Its
normalization calls fall from 265 to 58; instrumented discovery cumulative time
is 0.557/0.189 seconds and normalization 0.396/0.089 seconds for frozen/shared.
Profile times overlap and are diagnostic. Source preparation still has a cost,
including validation and rebuilding after every assignment.

## Remaining priority and continuation

The largest unchanged fixed phase is initial local binding, about 5.18 seconds.
The more informative coverage gap is the 388 root-budget stops. Next inspect
which unsuccessful roots or unchanged implication components recur across rounds,
and test structure-guided root selection or exact reuse within a charged budget.
A cached negative search is valid only for an unchanged checked graph/component;
new edges or changed coordinates require invalidation or a justified update.
Compare every proposal with the current policy on the same contexts and fresh
edits, charging hashing, discovery, proof construction and persistence. Larger
budgets alone do not establish efficient arbitrary-CNF coverage.

All 1,832 solver tests and 41 focused tests pass. The full suite retains 43
SQLite ResourceWarnings; focused checks have none. Preservation verifies 1,010
prior frozen sources, 174 previous manifests / 18,750 artifact entries, the
unchanged cumulative six-table bank, all previous proof archives and 64 manuscript
proof blocks. The failed experiment is additionally preserved and included in
the new manifest. Resume `experiments/results/cnf-shortening-context/checkpoint.json`.
