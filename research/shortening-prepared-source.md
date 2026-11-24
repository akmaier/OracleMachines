# Reuse immutable inputs across conditioned SAT states

Checkpoint: 25 November 2026. The preceding [filter experiment](shortening-reach-filters.md)
left repeated source preparation as a larger cost than path filtering. This
experiment removes that repetition while preserving the ternary-first endpoint
policy, its limits, every discovery program and every native proof record.

## What can be reused

Within one discovery call the original canonical CNF and supplied conditional
unit templates never change. Only the conditioning assignment changes. The old
state builder nevertheless normalizes the original source, rebuilds its variable
and clause sets, validates every original template and checks containment again
at every state. These checks repeat facts already established at entry.

`PreparedSource.prepare` checks the canonical source and each original support
once. It validates a private copy of each template and stores immutable nested
tuples and mapping proxies, plus parsed guard pairs and the source variable set.
Subsequent caller edits cannot change this state. The object lasts for one
discovery call; a source or template edit requires new preparation. It is not a
persistent cache, a certificate, or an argument accepted by the native compiler.

Each conditioned state still validates its assignment, restricts and normalizes
the actual source, checks guard compatibility and live coordinates, constructs
its current clause-position map, transports support clauses and unit reasons,
validates the reduced template, and checks every RUP reason against the actual
current CNF. Satisfied clauses are restricted before absent-coordinate tests.
The frozen program validator and native compiler independently recheck the
original source and all published consequences. No changed-cofactor obligation
is discharged by an earlier state.

The discovery function differs only at its preparation and state-builder calls.
AST comparison checks that control flow, root order, negative-cache handling,
filters, limits and returned programs stay the same. Original support containment
is valid at every state because the stored original source cannot change; the
transported support must still be contained in that state's actual cofactor.

## Matched costs and unchanged coverage

Thirty-two isolated workers cover eight targets, two engines and two alternating
repetitions. All 615 exposed events, including misses, enter the comparison.
Copying and preparation are included in discovery. Means of the two repetitions,
summed over targets, are:

| Measured phase | Existing preparation | Owned preparation |
|---|---:|---:|
| Discovery | 7.62653 s | 5.98966 s |
| Initial event binding | 5.00313 s | 5.00540 s |
| Complete measured phase | 12.66067 s | 11.02757 s |

Discovery falls 21.46% and the complete measured phase 12.90%. Both the 156
one-state events and the 459 events with several states improve in aggregate.
Two repetitions do not establish a stable speed ratio or pointwise improvement.
Origin acquisition, process startup, input loading and preservation audits are
additional. The selected endpoint policy remains optional; this comparison does
not rerun ordinary whole-query solving or establish an advantage over it.

All programs match the frozen control, including their unresolved outcomes. The
same 266 events and 173 distinct local roots are refuted. All 96 earlier edits
also preserve their programs. Search still makes 2,837 states, 26,361 fresh roots
and 339,030 BFS edge visits. Reduced-template and position checks remain: 12,983
native-bound hints and 396,982 reason-literal checks. The exact removed work is:

| Repeated static work removed | Count |
|---|---:|
| Source normalization literal visits | 2,921,976 |
| Original template checks | 17,331 |
| Original support literal visits | 585,592 |
| Original template reason-literal visits | 562,633 |

For each event, adding its static normalization/template counter vector once per
state to the new counts reconstructs every old operational count, after removing
the three new preparation counters. This is stronger evidence of avoided work
than timing alone. It does not count Python allocation, copying or set-building
as free: those operations remain in the measured time and memory.

## Memory and persistence

For source encoding size L, source variable count V and total template encoding
size T, preparation retains O(L+V+T) words under the existing word/hash-table
model. It borrows immutable source clauses when possible and copies mutable
template containers. Temporary copying and validation also need space. This
tradeoff avoids repeated allocations but does not imply lower peak memory.
The largest prepared-input proxy is 6,773 scalar slots; this includes retained
source and template content, not just incremental allocations, and omits Python
container overhead and integer bit lengths.

Maximum census worker RSS is 82,264,064 bytes for the control and 83,673,088 for
the candidate. On one separately instrumented seven-state event, traced peak
allocations fall from 375,000 to 337,216 bytes. These measurements describe
different scopes and are not a uniform memory bound. The profile still identifies
current-cofactor normalization, restriction and template transport as material
costs. The new source copies disappear at the end of discovery.

Two native compilation streams use the first occurrence of every one of the 173
recognized roots. They produce byte-identical databases across all six authority
tables: 6,535 native records, 10,508,807 key/payload bytes, and empty other tables.
Both independent cold readers accept every root. Warm replay adds or changes no
record. Discovery takes 2.57430 versus 2.00191 seconds in these streams, while
compilation takes 7.90129 versus 7.42774 seconds, warm validation 2.60777 versus
2.64672, cold validation 3.05943 versus 3.08744, and persistence 1.43187 versus
1.42804. Complete stream times are 17.62925 and 16.63988 seconds. These are single
streams; compilation and validation code are unchanged, so their timing variation
is not evidence of a compiler optimization. Persistent proof size is identical.

A separate expansion stream reopens the database at padding sizes 4, 16, 64 and
256. It retains the original twelve-record proof, then adds exactly one wrapper
per expansion with a support hit. Its databases match the earlier archived
bytes. Existing results are referenced, not replaced. The cumulative bank stays
unchanged; the new 173-root comparison archives are supplemental.

## Bounds, validation and next gap

Let A be the repeated original-source/template preparation cost per state, R the
number of conditioned states, and D the new ownership/preparation overhead after
the initial checks. The change removes R repetitions of A and pays D once;
cofactor-dependent work and search remain. Canonicalization includes sorting,
and template validation includes support ordering and reason checks, so A should
not be silently treated as linear in input length. This reuse does not reduce
the number of distinct states required on arbitrary CNF, or bound acquisition,
proof size or persistent growth by a polynomial.

All 1,861 solver tests pass, including 19 focused tests. Coverage includes every
partial assignment to the six-variable fixture, all 256 source deletions,
seeded unlabelled CNFs checked against exhaustive truth, changing input ownership,
malformed supports, forced execution of changed-cofactor checks, budget stops and
cold native reuse. All 64 previous manuscript proof blocks are unchanged.
The audit preserves 1,032 earlier frozen source files and 178 manifests containing
21,373 artifact entries; four new source files bring the frozen count to 1,036.

The first native-stream archive call incorrectly supplied a filename to a helper
that expects a directory. It failed after cold verification, before publishing an
archive. The original driver, protocol and failure logs are retained. The single
helper-argument correction is checked against that source snapshot; timed census
code and product code are unchanged. Both complete native streams were rerun.

**Next target:** measure a discovery-budget frontier using the saved preparation
cost to explore the 245 root-budget stops. Compare broader budgets with both the
new 64-root baseline and the old total measured cost, including compilation and
cold replay. Keep the 104 no-useful-literal cases separate: more BFS budget does
not supply missing consequences in their current supported binary graphs. Those
cases need stronger useful guards or another exact structural description.
Current-cofactor normalization remains a supporting optimization opportunity,
but broader certified coverage is the next objective. No live-query or
unrestricted-SAT result follows from this checkpoint.

Resume `experiments/results/cnf-shortening-prepared-source/checkpoint.json`.
The protocol, all event programs and counters, profiles, scaling cases, native
archives, edited cases, validation and failed attempts are saved beside it.
