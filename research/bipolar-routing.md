# Checking both cofactors before selecting a continuation

The preceding [routing experiment](binary-routing.md) found a concrete blind
spot: at the first later divergence, the ordinary split variable's false
cofactor has no unit deduction, while its true cofactor has a checked unit
refutation after 39 assignments. A false-only probe cannot recognize that
deduction. This experiment extends the guard to both polarities and tests whether
the extra recognition pays for itself.

## Rule, correctness and retained evidence

Binary-frequency discovery retains its existing contradictory-subset and
whole-cover priorities. When its forced variable differs from the ordinary
total-frequency split, the optional guard inspects the ordinary variable's
false cofactor, then its true cofactor if needed. The first checked negative
cofactor permits acquisition of only the other cofactor. A cached positive
answer or an unsuccessful propagation run is inconclusive for this guard.
If neither probe refutes its cofactor, the binary-frequency choice remains.

For either Boolean value `b`, if `F[x=b]` is unsatisfiable, then `F` is
satisfiable exactly when `F[x=not b]` is satisfiable. A positive model of the
latter is extended by `x=not b` and checked against the original source. Two
negative cofactor proofs compose through the existing native split rule.
Normalization maps, unit reasons and final child bindings are checked by the
unchanged native verifier. No new trusted proof rule is introduced.

Successful probe proofs use ordinary native publication and exact canonical
keys. They can survive a retained budget stop without licensing a verdict on an
unfinished parent. Both cold readers replay them. A miss is not stored as a
solved cofactor; subsequent acquisition can repeat its propagation. The
implementation therefore reuses completed evidence, not every intermediate
computation. No default policy is changed.

## Cost model

The guard has the preceding shape limits: at most 256 variables, 4,096 clauses
and 16,384 literals. It adds at most two cofactor probes per eligible expansion.
For `V` variables and `L` literal occurrences, each repeated-scan unit propagation
costs `O((V+1)L)` literal visits, with `O(L+V)` working words for the restricted
formula and trace. Ranking and restriction add scans. Normalization, checking
historical dependencies, serialization, publication and the surviving search
remain separate costs. Source shape limits do not bound a cached proof graph.

Directly compiled negative cofactors are not ordinary native expansions. Their
probes, propagation visits, trace entries and publications have separate counters.
The shared limit of 256 ordinary expansions is neither a total-work nor a
total-memory bound. Fewer expansions alone do not establish a speedup.

## Frozen comparison

Four policies run in separate serial workers: original targeting,
binary-frequency targeting, the false-only guard, and the two-polarity guard.
Two opposite orders are retained. The 15 targets include six previous edit
controls, six fixed-seed new nearby edits, and three versions of the exposed
285-clause residual: unchanged, with variable 76's sign flipped, and with every
literal complemented. Each sign variant independently restores the same exact
pre-target proof state. Target roots are absent. Signed proof transport is not
assumed; these three trials use native acquisition directly.

Whole-query controls and edits retain the existing eight-expansion probe and
six-clause first-false partition wrapper. The new edit roots are absent from the
preceding cumulative union. Donors and maps remain supplied. These are exposed
and nearby residual tests, not an external holdout or an automatic classification
of arbitrary CNFs. Sign changes preserve satisfiability, but can change clause
scan order, search choices and exact archive matches.

Preparation, checking, persistence, warm reuse, cold replay, reconstruction and
endpoint storage are measured. Complete-worker time includes audit and
measurement overhead, while prior acquisition is sunk. Independent replay and
the test suite run after comparative timing to avoid competing CPU work.

## Result: fix the blind spot, retain the broader regression

All four policies return UNSAT on all 15 targets. Query seconds below average
the two orders; control/edit rows sum separate case streams.

| Stream | Original expansions | Binary-frequency expansions | False-only expansions | Two-polarity expansions | Binary query seconds | Two-polarity query seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Six prior controls | 108 | 53 | 52 | 54 | 0.17878 | 0.21687 |
| Original exposed residual | 7 | 30 | 30 | 4 | 0.05789 | 0.01472 |
| Flip variable 76 | 7 | 30 | 4 | 4 | 0.05769 | 0.01398 |
| Complement every literal | 7 | 30 | 5 | 4 | 0.05820 | 0.01523 |
| Six new edits | 71 | 53 | 52 | 54 | 0.18124 | 0.21540 |

Both-polarity probing removes the observed sign-dependent miss: each isolated
variant falls from 30 to four expansions. Relative to binary-frequency routing,
query time falls 73.83–75.76%, in both orders. The original ordinary policy already
takes only seven expansions and about 15 ms on each. Thus the large reduction
primarily repairs a regression introduced by binary-frequency routing. It does
not establish an advantage over every existing policy.

On controls and new edits, the two-polarity policy instead increases query time
**21.31% and 18.85%**, with both orders worse. Each stream performs 18 probes,
compiles ten checked negative cofactors, and has eight inconclusive probes. Probe
propagation costs 40,471 and 40,342 literal visits respectively, besides native
search, ranking, normalization, checking and publication. Keep the rule optional;
recognizing more deductions does not necessarily make acquisition cheaper.

The new-edit native key/payload total grows **466,301 -> 631,623 bytes** and the
endpoint checked-object total **3,038,978 -> 3,724,813 bytes**. Compressed deltas
plus raw sidecars grow **150,206 -> 163,969 bytes**; the sidecar bytes themselves
are unchanged. These are sums of independent endpoints, not a simultaneous
peak-memory bound. SQLite totals grow only 0.12% because old history dominates.

Complete measured time on controls increases 1.22% in both orders. On new edits
its mean falls 0.37%, with mixed order signs; this does not establish a workflow
speedup. For the two-polarity new-edit runs, full cold replay takes 11.27 seconds
and reconstruction plus replay 11.61 seconds out of 24.44 measured worker seconds
summed across streams. Query acquisition takes only 0.215 seconds. Historical
checking and the deliberate audit/reconstruction work dominate this harness.
Warm setup plus lookup changes little. Even the complemented isolated residual
has a 1.67% higher complete-time mean despite its large query improvement, with
mixed order signs. Preserve all these costs rather than extrapolating the local
expansion reduction to total service performance.

## Next cost target: admission, prepared cofactors and proof growth

A posthoc profile selects the largest new-edit query regression: case 31's
deletion, **90.47 -> 110.66 ms** in the uninstrumented paired trials. Its six
partition-branch expansion counts change from `[1,9,1,6,1,3]` to `[1,8,1,7,1,4]`.
Including the initial probe, the query changes from 29 to 30 ordinary expansions.
The later replacement also becomes slower despite retaining 14 expansions.

Instrumented replays reproduce every frozen publication payload, partition and
expansion count. On the deletion, native normalization calls rise **110 -> 130**,
publication calls **30 -> 39**, verification calls **48 -> 57**, and propagation
calls **23 -> 32**. The additional cofactor probes cost more than their scans:
they create canonical formulas, checked proof nodes and changed continuations.
Normalization is the largest named preprocessing cost in both profiles. Its
cumulative time overlaps with verification/publication; these times must not be
summed or interpreted as independent causes. Instrumented times are not speedup
measurements.

`next-target.json` binds the selected source, paired reports, profiles and exact
persistent pre-query state. It is the first query in its stream, so no prior-query
extra rows are needed here. The queried root is absent, and profiles add no new
proof authority. Selection is posthoc; use new cases for the next comparison.

**Next experiment:** first price admission and investigate sharing exact prepared
cofactors, normalization and propagation evidence across discovery and native
acquisition. An event-driven propagator is another candidate, but a faster scan
alone will not remove changed proof graphs or bad continuation choices. Do not
assume every additional normalization is redundant: the selected graph itself
changes. Any reused trace or prepared representation must bind the exact source,
assignment, canonical map and checker namespace. Inconclusive probes remain
non-verdicts. Compare total acquisition and retained space against binary-frequency
routing before promotion. Automatic donor discovery, source-level recomposition,
compact sidecars and cold replay remain wider gaps.

## Validation and preservation

The full suite passes **1,410 tests**; **92 focused tests** pass without SQLite
warnings. The full suite retains 44 pre-existing unclosed-database warnings.
The eight new tests include both forced polarities, SAT model lifting, cached
positive/negative handling, rejected malformed evidence, retained budget stops,
1,024 small formula/sign comparisons and both cold readers.

Independent validation checks all **120 attempts** from **72 serial workers**,
chronological dependencies, exact seeds, repeat-order agreement and reproduction
of all three preceding policies on the old controls. Both native readers replay
the cumulative authority and **32 new / 114 preceding partition sidecars**.
All earlier payloads remain unchanged. The cumulative union adds **194 unique
native records**, reaching **75,256**, with all other authority tables unchanged.
The 102 alternative-payload observations remain in trial deltas; the union keeps
the earlier payload for existing keys.

All 712 prior source fingerprints and 9,822 artifacts in 130 manifests are
preserved. Older unrelated composed/inventory audits remain manifest-bound rather
than being rerun. The final source ledger has 719 files. The manuscript builds
without warnings to 238 pages, with all 64 previous proof blocks unchanged.
Resume `experiments/results/cnf-bipolar-routing/checkpoint.json`. No external
benchmark or new Lean refinement proof is added by this checkpoint.
