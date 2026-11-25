# Reuse wider guard consequences in bounded unit probes

Checkpoint: 25 November 2026. The [budget frontier](shortening-budget-frontier.md)
left 246 events unresolved after binary discovery. This experiment tests a
stronger, still bounded inference step on those events. It refutes 26 additional
events, representing 23 distinct local roots. Only two of the event gains require
wider guards beyond the binary-guard control. Native reconstruction verifies the
results but costs substantially more than ordinary local solving.

## Recognition, provenance and index reuse

Three controls use the same final source cofactor and literal order: source
clauses alone, source plus checked guards of width at most two, and source plus
all checked guards. Each runs one unconditional unit-propagation probe followed
by at most 64 single-literal assumptions. A source-based occurrence score orders
both signs of every live variable, with signed numeric ties. Guard mode does not
change this order. The scan does not feed a newly proved exclusion back into
later probes. A contradiction without an assumption, or contradictions under
both signs of one variable, establishes a refutation. Other outcomes remain
unresolved, never SAT.

One clause-occurrence index is built per discovery call and reused by all probes.
Each probe copies clause lengths and XOR summaries, initializes satisfaction
flags and a unit queue, then touches the occurrences of assigned literals. A
clause's XOR summary identifies its last unassigned literal when it becomes
unit; it is bookkeeping, not an affine inference rule. The index belongs to one
exact cofactor and guard set. Source/template edits require reconstruction.

Every guard is backed by a checked conditional unit trace on source clauses.
The independent program validator rebuilds the exact extended clause bank and
checks each unit reason and conflict. Extended clauses never become native
axioms. For a trace step forcing literal l from clause C, the branch assigning
not-l falsifies all of C. Its source-only conditional proof refutes that branch.
A native split joins this exclusion to the checked continuation. The terminal
conflict uses the same source-only leaf construction; opposite failed assumptions
join at their variable. Existing binary-prefix steps are checked and lifted back
to the original local source. Only existing empty, unit and split proof rules
are published. An absent normalized variable requires the excluded child to be
exactly the current cofactor, rather than permitting a split on a missing name.

All portable proof checks precede root reuse or publication. The native readers
remain independent of the new probe algorithm. Stored successes can be replayed
without changing any existing records.

## Matched remaining-case comparison

The protocol fixes 64 assumed literals, 262,144 occurrence visits across all
probes, and at most 256 unit steps per trace. Each guard mode enters two
alternating isolated repetitions for eight targets: 48 census workers. All 246
remaining events are included, including the earlier root-budget stop and the
15 cases with unknown snapshot status.

| Clause bank | New refuted events | Successful conditional traces | Discovery | Reconstruction | Complete phase |
|---|---:|---:|---:|---:|---:|
| Source | 16 | 1,760 | 0.95776 s | 4.22074 s | 5.20112 s |
| Source and binary guards | 24 | 1,907 | 0.97409 s | 4.26073 s | 5.25755 s |
| Source and all guards | 26 | 1,946 | 0.96247 s | 4.19671 s | 5.18191 s |

Values are means of two repetitions, summed over targets. Reconstruction includes
initial event binding and independent replay of the saved binary prefix. Discovery
includes source/template checks, index preparation, counter initialization and
all probe work. The earlier binary discovery, original acquisition, process
startup, input loading and final preservation audit remain additional. This is
a continuation from saved states, not a live whole-query comparison.

No source-control success is lost by adding binary guards, and no binary-guard
success is lost by adding all guards in this sample. Wider guards add target 28 /
event 5 and target 40 / event 73. These small timing differences do not establish
a stable speed advantage. Most recognition gain comes from propagating through
wider source clauses, rather than from the wider stored guards themselves.

The all-guard arm builds 246 indices over 258,398 literal occurrences and performs
15,458 probes, including the unconditional probes. It initializes 5,834,594
clause slots and visits 1,054,393 indexed occurrences. These initialization counts
matter: fewer visited occurrences do not make per-probe copying free. Maximum
index size is 1,809 literal occurrences; maximum per-event occurrence visits are
9,848, well below the work cap. All 220 remaining all-guard events hit the
64-assumption cap. Census RSS is about 82.6--82.7 MB across the three arms,
including interpreter/input state.

With C clauses and L literal occurrences in the fixed extended bank, index
preparation takes O(L+C) word work and storage. A complete probe initializes O(C)
state and visits each assigned variable's occurrences at most once, giving
O(C+L) word work before early stopping. Across P probes this gives
O(L+C+P(C+L)), plus source/guard validation and trace storage. Successful retained
traces can require O(PV) words for V variables. The occurrence cap excludes index
construction, initialization, guard checking and native reconstruction. XOR and
hash operations use the ordinary word model; scalar counts are not byte bounds.
No statement here bounds the work needed to solve every CNF.

## Native certificates expose the dominant regression

All 23 refuted local roots already have checked UNSAT results in ordinary
whole-query snapshots. They enter 92 isolated fresh/extension workers, with two
alternating repetitions. Both methods refute every case; both independent readers
accept all six authority tables. Repeated proofs match their table digests,
warm replay changes no record, and 46 distinct archive/root pairs are audited.

| Local certification cost | Ordinary search | Probe extension |
|---|---:|---:|
| Solve or compile | 0.71085 s | 4.55969 s |
| Warm verification | 0.03377 s | 0.27066 s |
| Cold verification | 0.90518 s | 4.14027 s |
| Persistence | 0.23816 s | 1.20253 s |
| Complete local trials | 1.97290 s | 10.24679 s |
| Key/payload bytes | 3,145,434 | 13,789,150 |
| Records | 315 | 1,726 |

Extension compilation includes source binding, the earlier binary prefix and
native reconstruction of guarded unit traces. It is slower on every case and
uses more record bytes on 22 of 23. The current compiler retains full cofactors
through many splits; it has no support-slicing optimization. Isolated database
sums can repeat shared content and are not cumulative-bank growth. These results
establish certified additional patterns, not an end-to-end efficiency gain.
The cumulative bank remains unchanged; new native archives are supplemental.

## Reusable exclusions and the next target

All successful conditional traces are preserved in the event programs and
independently checked. They are not all separately materialized in native
archives. In the 220 remaining all-guard events, 200 have at least one proved
exclusion. There are 1,602 such exclusions; for 1,218 of them the opposite
assumption was not tested within the budget. These untested complements occur in
191 events. Their outcomes are unknown, not presumed contradictory.

**Next coverage target:** reuse the checked failure and prioritize its untested
opposite under the same probe budget, rather than restarting the known failed
probe. Compare with the frozen ordering, retain any losses, and charge lookup,
verification and native reconstruction. This is a more direct opportunity than
assuming wider guards alone will close the remaining cases. After that, test
feedback of certified exclusions into subsequent propagation, with explicit
invalidation and source-coordinate rules. Twenty unresolved events have no
exclusion in the tested prefix and need a separate investigation.

**Main total-cost gap:** economical native support selection. More recognized
patterns are not useful speedups if their full-cofactor proof expansion dominates
ordinary solving. Keep the present compiler as a sound control; any compact
replacement must preserve source-only authority and cold replay.

The initial extension test incorrectly expected one pass to close a chain that
requires feedback between rounds. Its source and failure log are retained, the
claim was corrected, and a permanent regression checks that the case remains
unresolved despite valid exclusions. Additional tests cover random unit closures
against scan propagation, exhaustive truth on small random CNFs, signed guard
renamings, malformed proofs, budget stops, prefix lifting, warm and cold replay.
All 1,875 tests pass, including 18 focused tests. All 64 earlier manuscript proof
blocks, 1,040 frozen source files and 180 manifests containing 22,276 prior
artifact entries remain preserved. Five new source/test files bring the total to
1,045. No unrestricted-SAT classification or polynomial-time conclusion follows.

Resume `experiments/results/cnf-wide-guard-probes/checkpoint.json`.
