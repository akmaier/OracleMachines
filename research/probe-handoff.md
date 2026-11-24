# Reuse an inconclusive probe when search visits the same child

The preceding profile found repeated restriction, canonicalization and unit
propagation on unresolved random 3-CNF. A whole-clause probe prepares both
polarities of the ordinary split variable. If neither refutes its cofactor,
ordinary search can later prepare exactly the same child again. This experiment
passes that existing preparation to the actual child without changing discovery
priority, branch order, proof authority or the expansion budget.

## Exact correspondence

`ProbeHandoffSolver` inserts its expansion hook at the existing ordered-probe
mixin. The negative pool and witness pool still run first. Binary discovery,
compiled covers and partial-backbone handling retain their existing order.
After an inconclusive whole-clause probe, ordinary propagation, recognized
leaves, subsumption, matching and decomposition still precede splitting.

An immutable offer contains the raw restricted CNF, its canonical CNF and label
map, its exact key and, when computed, the deterministic nonconflicting unit
propagation result. A continuation consumes an offer only for the identical
parent object, identical counter object and exact single-variable Boolean
assignment. The following visit must receive that same raw child object.
Canonicalization and propagation are each consumed once. An equal but distinct
source, another assignment, another counter or a verifier uses the original
path. All certificate verification explicitly suppresses propagation hints.
A nonconflicting probe supplies preparation, not a satisfying assignment.

The semantic invariant is local. The parent is already canonical; restriction
preserves literal order and cannot create a tautology. Deduplication and the
strictly increasing compact label map therefore reproduce general normalization
exactly. Deterministic propagation on that immutable canonical child gives the
same assignment, trace and conflict result on reuse. All subsequent branch
choices and certificate checks use the original routines. Matching and capacity
control only whether preparation is repeated. This argument requires the exact
bindings and preserved method order; equality of verdicts alone would not test
those implementation obligations.

The offer does not cross queries and does not enter SQLite. Exception and budget
stop cleanup releases all pending offers; previously checked prefix proofs
remain in the archive. Warm lookup and either original cold reader need no
handoff metadata. The research adapter requires an exclusive synchronous solver
session and rejects an already installed foreign restriction engine.

## Resource accounting and lifetime

Let a selected parent have literal payload L, and let R be the payload of its
restricted child. Reusing its raw restriction avoids a scan charged by L.
Reusing its canonical form avoids general normalization, support relabeling and
key serialization on that raw child. Reusing deterministic propagation avoids
its recorded literal visits, while copying its assignment and trace still costs
work proportional to their size. None of these savings removes the original
probe, the search below the child or proof checking.

Admission freezes the propagation result and calculates a conservative Python
payload charge. This visits the offer's literals, including offers that fail
admission. Ancestor offers and an unvisited opposite branch remain charged while
the selected child runs. Thus a cap can prevent most descendant reuse even when
the whole computation is sequential. An unused offer also costs construction,
sizing, matching and disposal. Larger capacity alone need not improve runtime.

The existing lookahead gate still permits at most 256 variables, 4,096 clauses
and 16,384 literals per eligible canonical parent. Discovery and gate testing
are charged, and larger parents continue through the original fallback. A fixed
256-dispatch cap can return unresolved; it is not a polynomial-time decider for
all formulas.

The two tested caps are 256 KiB and 2 MiB of selected offer payload. The charge
counts shared objects repeatedly; it excludes control containers, Python frames,
allocator overhead and construction transients. It is not a process-memory
bound. The existing retained solver-graph measure and peak RSS remain separate.
No persistent proof compression or new arbitrary-CNF coverage follows from this
local preparation reuse.

## Development evidence and frozen comparison

An exact chronological replay of the preceding holdout through case 40 starts
empty and reproduces its status, native dispatches and all retained payloads.
With 256 KiB, the target admits and consumes one offer and rejects 106. With
2 MiB, it admits 16, consumes 11, discards five and rejects 91. Both still stop
at 256 dispatches. The larger allowance was chosen using this exposed diagnostic;
neither capacity is chosen using fresh outcomes.

The first development version placed its override above the existing pool
methods and changed case 15's valid model. The corrected mixin placement retains
those methods. A chronological pool-ordering regression test now checks this
behavior. Two earlier comparison failures concerned integer versus JSON string
model keys and numeric versus lexical key ordering. Their logs remain available;
none is evidence of a SAT/UNSAT disagreement.

The prospective protocol compares the preceding policy and the two capacities
in four alternating serial repetitions. The previous 108/132 construction sizes
are exposed; fresh sizes 114/138 use seed 202611240057. Each stream has 72 queries,
48 distinct roots and six families. Search receives only source CNFs, starts
empty and retains earlier checked results. Archive novelty does not seed search.
Every arm uses the same 256-dispatch cap.

Solve and complete-worker times charge attempted reuse, verification,
publication, warm/cold reuse, reconstruction, serialization and compression.
Imports, source hashes and case loading precede the complete-worker timer;
final report bookkeeping follows it. Cumulative preservation, the exposed
diagnostics and profiling are measured separately. All six table payloads,
completed answers, models, dispatches and chronological publications are checked
for equality across arms, including retained prefixes from unresolved queries.

## Measured result

| Measure | Exposed baseline | Exposed 256 KiB | Exposed 2 MiB | Fresh baseline | Fresh 256 KiB | Fresh 2 MiB |
|---|---:|---:|---:|---:|---:|---:|
| Mean solve seconds | 14.7812 | 14.8272 | 14.2519 | 15.1096 | 15.2846 | 14.7044 |
| Mean complete-worker seconds | 28.8935 | 28.9681 | 28.3220 | 29.1767 | 29.3915 | 28.7146 |
| Consumed preparations | 0 | 109 | 835 | 0 | 54 | 783 |
| Reused propagation results | 0 | 94 | 697 | 0 | 49 | 659 |
| Capacity rejections | 0 | 1,634 | 720 | 0 | 1,598 | 684 |
| Admitted but discarded | 0 | 42 | 230 | 0 | 33 | 218 |
| Peak selected offer bytes | 0 | 262,101 | 2,096,757 | 0 | 261,916 | 2,096,979 |

The 2 MiB policy reduces solve mean **3.58% exposed / 2.68% fresh** and
complete-worker mean **1.98% / 1.58%**. All four pairs improve both measures
on both streams. Fresh paired solve changes range from -0.99% to -4.92%.
The 256 KiB policy regresses solve mean **0.31% / 1.16%** and worker mean
**0.26% / 0.74%**, with three slower solve pairs per stream. Keep both results;
reusing a few preparations does not repay the admission work here.

All three arms retain **42/48 completed distinct roots** per stream and identical
models, dispatches and authority payloads. The exposed stream has 5,960 native
records and 57,848,807 key-plus-payload bytes; fresh has 5,599 and 58,546,391.
Selected retained Python graphs are 244,928,957 and 248,400,985 bytes respectively.
The selected graph excludes query logs and native allocations; worker RSS also
covers replay and reconstruction phases. SQLite sizes (90,742,784 / 90,890,240 bytes) and compressed sizes
(6,757,657 / 6,995,653 bytes) are also identical across policies. No persistent
memory reduction accompanies this local runtime saving.

Mean RSS stays near 825 MB exposed and 826--830 MB fresh. Its small differences
do not establish lower process memory: offer charge, retained graph size and
RSS measure different things. The 2 MiB policy adds bounded selected preparation
payload, with excluded control and construction costs stated above. Fresh warm
replay changes from 0.2020 to 0.2062 seconds, cold verification from 5.6762 to
5.7078, and cold reconstruction from 1.1234 to 1.0152. These phases are included
in worker totals; improvements are not universal across phases.

Fresh large-cap reuse avoids 750,877 restriction literal visits, 715,031
normalization literal visits and 1,291,626 native propagation literal visits.
Native propagation visits fall 21.68% and normalization visits 6.72%. But
admission sizing scans 1,664,172 literals, including rejected offers, and freezes
9,634 trace/assignment entries. Copying consumed traces costs 3,784 entries.
Those costs, plus unaffected recognition, checking and persistence, explain why
scan savings are larger than the total runtime improvement.

The six fresh roots still unresolved at the end are all random-three. That
family accounts for 76.64% of large-cap solve time. The policy remains optional. The measured larger variant is
`ProbeHandoffSolver(..., handoff_bytes=2*1024*1024)`; the frozen constructor's
256 KiB default remains the smaller experimental control. This fixed-seed comparison establishes a local saved-work mechanism and its
tradeoff, not a broad performance guarantee or additional certified SAT family.
The checkpoint, raw archives and machine-readable next-target record are in
`experiments/results/cnf-probe-handoff/`.

## Next lifetime question

The fresh profile selects case 37 (size 138), the largest mean unresolved
large-cap attempt at 1.2407 seconds before instrumentation. The 256 KiB policy
consumes one offer and rejects 106; the 2 MiB policy consumes 11, discards six
and rejects 90. General normalization calls fall only from 739 to 728 and
restriction scans from 868 to 857. All policies still stop at 256 dispatches.
The profile replays the exact earlier prefix, and its retained payloads equal
the matched archive. Profiling ran outside the comparison, alongside other
verification; function times are diagnostic, with overlapping cumulative time.
Use the exact call counts and matched unprofiled times for this conclusion.

The prototype holds a consumed offer's charge until its whole recursive visit
returns. This is conservative, but can block descendant offers after the native
visit already owns the raw and canonical child and propagation has consumed its
trace. Before increasing the cap again, identify those ownership transitions
and release preparation that is no longer needed. Preserve any genuinely pending
opposite branch. The implementation must remove its references as well as lower
its accounting; otherwise a smaller counter would conceal retained memory.
Measure this against the current two-cap policy, including construction and
sizing of failed admissions. More reusable preparations still do not certify an
unresolved residual or establish a tractable partition of arbitrary CNF.

## Validation and preserved history

All 1,670 tests pass, including 59 focused checks. The full suite retains 44
pre-existing SQLite ResourceWarnings; the focused run has none. Independent
readers audit 1,728 benchmark queries and 82 diagnostic queries, every retained
prefix node, and all 342 earlier partition records. All six authority-table
payloads match across the three policies on each stream. The cumulative union
preserves every prior payload and adds 5,582 native records and eight affine
records, for totals of 132,783 native and 123 affine records; the other four
tables are unchanged. Alternative valid payloads remain in raw trial archives.
The manuscript builds to 253 pages without warnings; all 64 earlier proof
blocks remain unchanged. Multipart transport preserves the cumulative database
bytes and adds no SAT authority. The 156 earlier manifests and their 13,984
artifacts remain unchanged.
