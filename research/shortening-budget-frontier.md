# Convert preparation savings into bounded discovery coverage

Checkpoint: 25 November 2026. The [prepared-source experiment](shortening-prepared-source.md)
reduced repeated work without changing coverage. This fixed sweep asks whether
that saving can pay for more useful searches. It changes only the fresh BFS root
allowance: 64, 96, 128 or 256. The existing 32-round, 256-path and 16,384 combined
BFS/invalidation/admission-check limits remain, as does the cache membership cap.

## What a larger root budget guarantees

The root limit only stops an otherwise identical deterministic search. Increasing
it preserves the sequence of operations until the smaller limit stops execution.
Thus every completed smaller-budget refutation remains identical. A smaller run
that ends for a reason other than the root limit also remains identical. A run
that hits the root limit may extend its forced-step prefix; it need not find a
refutation. This property concerns this detector with its other parameters fixed,
not arbitrary search heuristics or total computational effort.

The sweep uses the frozen prepared-source implementation and the earlier
repeated-preparation 64-root control. No inference, certificate format, live
default or source-validation rule changes. All five settings are fixed before
measurement. Eight targets, five settings and two alternating repetitions give
80 isolated census workers over all 615 exposed events.

## Coverage and charged discovery cost

| Setting | Refuted events | Distinct roots | Root-limit stops | No useful literal | Discovery | Complete phase |
|---|---:|---:|---:|---:|---:|---:|
| Earlier preparation, 64 | 266 | 173 | 245 | 104 | 7.80051 s | 12.95475 s |
| Prepared, 64 | 266 | 173 | 245 | 104 | 6.10815 s | 11.23735 s |
| Prepared, 96 | 318 | 206 | 133 | 164 | 7.11800 s | 12.29904 s |
| Prepared, 128 | 347 | 224 | 47 | 221 | 7.60298 s | 12.76253 s |
| Prepared, 256 | 369 | 240 | 1 | 245 | 8.01857 s | 13.16403 s |

Times are means of two repetitions, summed over targets. The complete phase
includes initial event binding, discovery with copying and preparation, and event
serialization. Original knowledge acquisition, process startup, input loading and
preservation audits are additional. Native compilation and replay are measured
separately below. Root allowances are not wall-time or total-work guarantees.

The 96-root setting gains 52 events at 8.75% less discovery time and 5.06% less
complete-phase time than the earlier 64-root implementation. The 128-root setting
gains 81 events at 2.53% and 1.48% less, respectively. The latter timing margin is
small; two repetitions do not establish a stable speed ratio. At 256 roots,
recognition gains 103 events while discovery costs 2.80% more and the complete
phase 1.62% more than the earlier control. Relative to the new prepared 64-root
baseline, every larger budget costs more. These are descriptive tradeoffs, not a
uniform faster solver or an automatically selected policy.

All earlier successes remain, every forced-step prefix is checked, and all
non-root-limit outcomes remain unchanged as predicted. The 96 previous edited
cases rise from 28 refutations to 34, 38 and 40, without losses. These are
transformations of exposed families, not independent-domain validation.

Larger allowances also spend more actual work. Prepared 64/96/128/256 use
2,837/3,289/3,552/3,770 conditioned states, 26,361/32,469/35,592/37,449 fresh
roots, and 339,030/444,394/509,333/557,568 BFS edge visits. Maximum cached literal
memberships rise from 1,538 to 1,841, 2,166 and 2,181. Maximum prepared-input slots
stay 6,773. Census worker RSS ranges from about 79.6 to 83.6 MB across settings;
these process maxima include interpreter/input state and do not establish a
monotone memory benefit. Persistent storage remains separate from query-local
search state.

## New native proofs and the cost that remains

The largest allowance adds 67 distinct local roots beyond prepared64; 58 are
also outside the earlier six-policy filter union. All 67 already occur in the
checked ordinary whole-query snapshots. The improvement is in the bounded
pattern detector, not in the whole solver's known answers.

Every new root enters two alternating isolated comparisons of ordinary local
search and selected-support compilation: 268 workers. Both approaches refute all
67 cases; both independent readers validate all six authority tables. Repeated
runs match proof counts and table digests, warm rechecks add no records, and 134
unique native archive/root pairs are audited.

| Local certification cost | Ordinary search | Support compilation |
|---|---:|---:|
| Solve or compile | 3.41877 s | 6.84888 s |
| Warm verification | 0.13119 s | 2.55595 s |
| Cold verification | 3.94279 s | 3.42864 s |
| Persistence | 1.19186 s | 0.83185 s |
| Complete trial phases | 8.93284 s | 13.81499 s |
| Key/payload bytes | 15,360,617 | 9,296,395 |
| Records | 1,114 | 5,321 |

These are sums of per-case mean costs in independent databases, before census
discovery. Their stored bytes can duplicate shared subproofs and are not the
incremental growth of one cumulative bank. Support compilation is slower in
solve/compile time on 57 of 67 cases and in complete trial time on 54. It uses
more bytes on 30 cases despite saving about 39.5% in aggregate. Both the gains
and regressions are retained. Cheaper discovery does not remove this certification
cost or establish a whole-query speedup. The cumulative bank is unchanged; all
new comparison proofs are supplemental archives.

## The informative unresolved cases

At 256 roots, only target 1 / event 3 still hits the root limit, after 23 forced
steps with 100 variables remaining. It has a checked UNSAT result in the ordinary
snapshot. The other 245 events exhaust the detector's available useful binary
consequences. Of these, 230 have checked UNSAT results in the snapshot and 15
are absent from the checked stores used by the diagnosis. Absence remains unknown;
it is not a SAT or UNSAT verdict.

The diagnosis independently replays every partial program's edges using the
frozen source-bound checker before inspecting its final cofactor. A deterministic
completion of the binary model supplies no full-source SAT witness on any of the
246 remaining events. Failure of that one candidate assignment proves nothing
about satisfiability. All snapshot files remain byte-identical after inspection.

Of the 245 exhausted events, 228 retain checked guard consequences wider than two
literals. Across the remaining events there are 540 ternary guard occurrences,
422 of width four, 302 of width five and further larger guards. These are event
occurrences, not counts of distinct reusable templates. The current binary graph
cannot exploit their full joint interaction before more literals become fixed.
Their presence does not guarantee that a stronger local rule will succeed.

**Next target:** test bounded unit-propagation probes through the actual source
and already checked wider guard consequences, with explicit provenance for every
derived clause and native reconstruction of any useful exclusion. Begin with the
230 checked-negative exhausted events, retain the 15 unknown cases as unknown,
and compare against the binary-only detector and ordinary local solving. Charge
recognition, probe work, support selection, checking and cold replay. The 17
exhausted events without wider guards remain a separate acquisition/interaction
gap. This is a more informative coverage target than another general increase
above 256 roots on this corpus.

All 1,865 tests pass, including 12 focused tests. Budget-prefix and stop invariance
are tested on conditioned chains and 180 seeded unlabelled CNFs, with exhaustive
truth checks on the small cases. All 64 earlier manuscript proof blocks, 1,036
frozen source files and 179 manifests containing 21,482 artifact entries are
preserved. Four new research/test files bring the frozen source count to 1,040.
No unrestricted-SAT tractability, complete efficient partition, or uniform
persistent-storage bound follows.

Resume `experiments/results/cnf-shortening-budget-frontier/checkpoint.json`.
