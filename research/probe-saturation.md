# Checked failed-literal saturation with reusable rounds

Checkpoint: 26 November 2026. A generic iteration replaces the need to invent
another named search layer after every productive failed-literal pass. On the
remaining changed snapshot `(37,39)`, two checked rounds find **14 new failed
assumptions** and a unit contradiction. Original-source native reconstruction
and both cold archive readers certify the result. Structural coverage increases
from **233/246 to 234/246**, leaving **twelve open snapshots**. Fresh solving also
refutes this case, and is substantially cheaper than provenance reconstruction.
This result concerns the snapshot, not its entire generating target formula.

## Rule, recognition and exact recomposition

The seed is the checked B13 feedback bank: 602 B13 clauses plus the two previously
proved units give 604 clauses. The generic kernel takes any valid seed CNF and
an optional ordering source covering its variables. It preserves original
coordinate IDs, including sparse names, while removing duplicates and tautologies.
An ordering source is a heuristic, not an authority for adding clauses.

For each round, compute and check complete unit closure, probe the remaining
signed variables using the existing bounded cursor engine, and check each failed
assumption against that exact round's bank. After an exhausted productive round,
append the negations of failed assumptions as unit clauses. Continue on the
strengthened bank. Stop at a checked contradiction, a budget interruption, or an
exhausted pass that supplies no new unit. A fixed point is **unresolved**, never
a SAT certificate. Existing honest-production assumptions about claimed open
probes remain explicit; refutations rely on checked failure traces, not on those
open claims. A bound-exhausted trace is also unresolved.

There is a simple progress bound for this particular rule. Each productive
completed round probes only variables unassigned by its checked initial closure.
A checked failed assumption therefore fixes a previously unassigned seed
variable in the next closure, or makes that closure contradictory. Assignments
are monotone as units are added. With `n` seed variables, at most `n` productive
completed rounds can occur, followed if necessary by one no-gain pass. Interrupted
calls do not count as new productive rounds and have no such bound on their number.
The bound does not solve every fixed point, bound acquisition of the seed, or
bound native proof expansion. It is not a polynomial algorithm for arbitrary SAT.

A saved round is reused only after checking the seed, ordered variable policy,
current bank, complete closure, trace limit, cursor and every retained failed
proof. An interrupted round continues its checked cursor. Completed productive
rounds are replayed to reconstruct the next bank; an unchanged exhausted terminal
can be returned without fresh probes. Changing the seed or ordering invalidates
the history, and changing the trace bound requires a new record. JSON serialization
and cold replay use the same independently reconstructed seed, never discovery's
live prepared state. The twelve other B13 rows have identical exhausted banks,
no failed probes to append and unchanged checked closures; their histories are
verified and retained without another search pass.

The native compiler dynamically indexes the generic rounds. A unit attributed
to round `i` is justified by its failed-assumption trace on that round's earlier
bank. Every dependency descends to an earlier bank, and its actual assumption
must hold in the current context. Older B13 and lower origins retain their frozen
maps. Source leaves, guard supports, prefix reconstruction and direct source-unit
shortcuts use the existing source-only empty/unit/split record format. Thus the
inductive argument for earlier native compilation also covers an arbitrary finite
list of checked rounds. Warm compiler hits check provenance first; native readers
need only the source and native archive. This measured snapshot has no prefix steps.

## Coverage and matched discovery costs

Round one probes 270 assumptions and fails `44, 142, -80, -60, 50`. Round two
probes 260 and fails `-62, 5, -43, 107, -74, 84, 132, 88, 108`. The resulting unit
contradiction is checked before native conversion. The same final record results
whether both rounds are acquired together or the second resumes a saved first
round. Tests also cover interrupted cursors, terminal reuse, sparse renaming,
duplicates, tautologies and disjoint mixtures.

Six permutations of the following modes run in separate processes before heavy
checks. `once` permits one round; `saturate` permits eight; `resume` loads the
separately acquired first round and permits eight additional rounds. The last two
produce exactly equal results. `once` versus `saturate` is a coverage comparison
with different aggregate budgets, not an equal-budget performance contest.

| Mode | Preparation (s) | Discovery/checking saved state (s) | Cold verification (s) | Persistence (s) | Complete (s) | Fresh probes | Result bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| once | 0.02229 | 0.00709 | 0.02775 | 0.00097 | 0.05811 | 270 | 39,649 |
| saturate | 0.02248 | 0.01391 | 0.03112 | 0.00128 | 0.06880 | 530 | 70,705 |
| resume | 0.02290 | 0.01512 | 0.03058 | 0.00132 | 0.06993 | 260 | 70,705 |

Resume avoids **270 probes (50.94%)**, but is **1.65% slower overall** here; checking
saved rounds offsets the inexpensive probes. Acquiring once then resuming costs
**0.12804 s**, versus **0.06880 s** in one call. This is exact work reuse, not a
measured runtime or memory win. Both snapshots are retained when resuming, so
saved-state retention adds 39,649 bytes beyond the final 70,705-byte result.
Peak RSS is 50,970,624 / 51,347,456 / 51,642,368 bytes in table order. Reconstruction
of the original snapshot, input loading, historical acquisition and final lineage
audits are additional; original-bank seed preparation and cold seed reconstruction
are included in the measured phases. Small timing differences on one selected
case do not establish broad performance effects.

## Native expansion is the dominant measured cost

Two opposite fresh-process orders compare a fresh solver (256-node limit) with
direct source-only compilation (source-unit work limit 262,144, trace limit 256).
Pilot archives are retained and checked separately, but excluded from these means.
Both routes certify the same original snapshot; there is one coverage gain.

| Route | Solve/convert (s) | Warm (s) | Both cold readers (s) | Persistence (s) | Complete (s) | Records | Record bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0.29982 | 0.00268 | 0.32388 | 0.12759 | 0.75903 | 88 | 1,543,539 |
| direct provenance | 21.47261 | 0.04043 | 22.88668 | 6.69520 | 51.45391 | 5,587 | 77,497,609 |

Direct reconstruction costs **67.79 times** as much end to end and stores
**50.21 times** as many raw record bytes. Peak RSS is **80,461,824 versus
914,161,664 bytes**; compressed archives are **189,777 versus 8,524,365 bytes**.
Construction and cold verification account for about **42% and 44%** of direct
time. Repeated conditioned source contexts dominate this workflow despite native
canonical reuse and bounded direct-unit shortcuts. The result is a strong retained
counterexample to equating a short augmented trace with a cheap native certificate.
The smaller fresh archive is selected for the continuation overlay; all direct
archives and proofs remain. No production-default change or speedup is claimed.

These totals include database creation, construction with checked provenance,
warm reuse, both independent cold readers and compressed persistence. Historical
acquisition, the discovery workflow above, loading and final audits are additional.
Compiler warm calls revalidate histories; fresh warm calls invoke the solver again.
They are distinct public workflows, not the same isolated native lookup.

## Preserved evidence and next gaps

Resume `experiments/results/cnf-probe-saturation/checkpoint.json`, key
`probe_saturation.remaining`, using the comparison module's `load_frontier`.
Only `(37,39)` is removed. Every field of the twelve remaining rows, all cumulative
authority tables, previous native archives, 1,194 prior source fingerprints and
32,729 artifact entries in 216 manifests are preserved. Five new source files
bring the source ledger to 1,199. The initial kernel prototype compacted sparse
variable names; its source is retained. The corrected implementation preserves
those IDs and passed the sparse-name tests before the declared timing trials.
The first final-audit run assumed pilot reports had the later benchmark schema;
its `KeyError` and validator source are retained. The corrected adapter checks
that pilot archive hashes and results exactly match the independently replayed
benchmark archives, without changing any trial or pilot data.

Validation includes **2,175 full tests and 21 focused tests**; all 256 subsets of
the eight non-tautological unit/binary clauses on two variables, an explicit empty
clause, and 100 seeded arbitrary five-variable CNFs are checked against exhaustive
assignments. Invalid bindings, false completion claims, corrupt proofs and stale
warm inputs are rejected. Both source-only archive readers pass. All 64 existing
manuscript proof blocks remain byte-identical. These bounded tests are neither
exhaustive large-CNF coverage nor a completeness theorem for propagation.

**Next coverage priority:** study shared-variable interactions and bounded
conditioning/decomposition in the twelve fixed points. A further identical
failed-literal pass cannot add information. Identify what stronger interaction
would separate those cases before extending another bank or repeating acquisition.
**Next cost priority:** profile and reduce repeated source contexts in native
conversion, or use a measured cost gate that selects a smaller fresh certificate.
Charge construction, cold checking and retained bytes together. The generic round
bound closes an implementation gap; efficient discovery and recomposition for
every arbitrary CNF, compact oracle acquisition and uniform resource bounds remain
open.
