# Test the opposite of a checked failed probe

Checkpoint: 25 November 2026. The [full-clause probe study](wide-guard-probes.md)
left 220 all-guard events unresolved, with 1,218 failed literals whose opposites
had not been tested. Prioritizing those opposites now refutes 66 of the same 246
events, compared with 26 under the frozen order and the same 64-assumption limit.
This is broader detector coverage. Native proof construction remains slower and
larger than ordinary local solving.

## What changes and what remains an obligation

After a unit-propagation probe under literal l reaches a checked conflict, keep
its trace and try not-l next if that assumption has not already been tested.
Two conflicting branches refute the cofactor. If the promoted branch stays open,
resume the old order; an open unit closure is not a SAT verdict. A tested set
skips promoted literals when their original queue entries are reached. There is
no new cross-call cache, exclusion feedback or inference rule. Earlier code
already retained failed-probe traces; this change uses them to schedule search.

The source, selected guards, occurrence index, trace validator and native compiler
are unchanged. Each guard must still bind to the current source. Reuse across
an edit requires rebuilding and checking that binding. All assumptions, including
promoted ones, spend the existing root, occurrence-visit and trace budgets.

The loop invariant is that every recorded failure has a trace on the same checked
clause bank, and each tested literal is searched at most once. Scheduling adds no
logical authority. If the two signs of a variable both have checked conflicts,
the unchanged native compiler joins the two refutations by a split; otherwise
search remains unresolved. Without a stopping budget there are at most 2V
assumptions for V variables. This argument establishes sound scheduling and
finite termination, not completeness of unit probing for arbitrary SAT.

With P attempted assumptions, deque initialization and tested-set scheduling add
O(V+P) expected word work and O(V+min(P,2V)) words, using the existing hash-table
model. The old source-based ordering still costs sorting work. Each unit probe
still initializes clause state, so index reuse does not eliminate O(C) copying
for C clauses. The previous O(C+L+P(C+L)) probe bound and O(PV) retained-trace bound
remain, in addition to ordering, source/guard checking and native reconstruction.
These are bounds for this bounded detector, not the complete SAT solver.

## Matched coverage and costs

All 246 exposed events enter six arms: source, binary-guard and all-guard banks,
each with frozen or complement scheduling. Two alternating isolated repetitions
per target produce 96 census workers. Limits remain 64 assumed literals,
262,144 occurrence visits and 256 unit steps per trace. An unconditional probe
precedes the assumptions. Every frozen program and deterministic counter matches
the previous checkpoint; every new trace is independently checked.

| Clause bank | Frozen events | Complement events | Discovery, frozen / complement | Complete phase, frozen / complement |
|---|---:|---:|---:|---:|
| Source | 16 | 55 | 0.97800 / 0.92760 s | 5.32238 / 5.26624 s |
| Binary guards | 24 | 64 | 0.98821 / 0.92102 s | 5.34081 / 5.22213 s |
| All guards | 26 | 66 | 0.98971 / 0.92587 s | 5.32998 / 5.25440 s |

Times are per-target means of two repetitions, summed over targets. Complete
phase includes discovery, binding and saved binary-prefix reconstruction, plus
event serialization. Prior acquisition and binary discovery, loading, process
startup and final preservation audits are additional. For all guards,
reconstruction is 4.31920 / 4.30996 seconds. Discovery falls 6.45%; this complete
phase falls only 1.42%. These small timings are sample observations, not a stable
whole-query speed advantage.

Each bank preserves all of its own frozen-order successes in this sample.
Adding guards to the adaptive schedule need not preserve source-bank successes:
the binary arm loses target 28 / event 71 while gaining ten other source-bank
misses. All guards recover that event and preserve the source and binary event
sets here. All programs, counts and changed-event inputs remain in the artifact.

The all-guard arm reduces assumed probes from 15,212 to 12,699 and occurrence
visits from 1,054,393 to 764,400 (27.50%). Clause initialization slots fall from
5,834,594 to 4,983,166. It executes 984 promoted probes; 918 stay open. Earlier
termination reduces stored successful probe traces from 1,946 to 1,161; it is
not compression of the earlier proof archive, which remains intact. Maximum
queue size is 298 literals and tested-set size is 64. Census peak RSS stays near
82.6--82.7 MB; no general peak-memory reduction is established.

A permanent eight-clause counterexample shows why sample preservation is not a
guarantee. A failed probe promotes an open opposite before the decisive pair
from the old order. With three assumptions the frozen order refutes and the
new order does not; at four the new order refutes too. The open-opposite test
fixture also initially failed to exercise promotion because its opposite was
already tested; the original test and failure log are retained before correction.

## Native proofs, persistent results and remaining costs

The new schedule recognizes 60 distinct all-guard roots, including 37 absent
from the previous three-bank success union. These 37 enter 148 isolated native
trials: fresh local solving and compilation of the guarded extension, twice each
in alternating order. Both methods prove all 37 UNSAT. Two roots, target 28 /
event 71 and target 37 / event 89, were unknown in the inspected snapshot stores;
the other 35 already had UNSAT results there. This does not establish that reuse
beats ordinary search on those two cases.

| Summed per-case mean | Fresh local solving | Guarded extension |
|---|---:|---:|
| Solve or compile | 1.40474 s | 8.05303 s |
| Warm check | 0.06142 s | 0.31298 s |
| Cold readers | 1.72359 s | 7.38338 s |
| Persistence | 0.45205 s | 2.20154 s |
| Complete trial | 3.77522 s | 18.06486 s |
| Encoded record bytes | 6,319,690 | 24,370,613 |
| Records | 548 | 2,717 |

Extension compilation is slower and larger on all 37 cases. The compiler expands
guarded steps into source-only splits with full cofactors. The totals use isolated
databases and can duplicate shared subproofs; they are not cumulative-bank growth.
Warm checks add no authority rows. Both independent cold readers check all 74
unique archive/root pairs. The prior cumulative bank and all earlier proof and
experiment artifacts remain unchanged.

The final suite passes 1,881 tests, including 16 focused tests. Validation checks
181 previous manifests, 22,614 previous artifacts and 1,045 prior source files;
1,050 source files are bound in the new checkpoint. All 64 manuscript proof
blocks remain unchanged. Existing SQLite ResourceWarnings in the full suite are
recorded; focused tests have none.

## Next gaps

There are 180 unresolved all-guard events, all stopped at the root limit. Of
these, 160 retain 851 checked exclusions. Only 14 exclusions now have an untested
opposite, compared with 1,218 before; the other opposite closures stayed open.
Twenty events have no exclusion in the attempted prefix. The next coverage
question is whether accumulated exclusions expose further useful propagation
when fed back with explicit provenance. The retained one-pass chain example
already shows that scheduling alone does not provide that closure. A wider
search budget and iterative feedback are distinct experiments.

The largest measured total-cost gap remains native proof expansion: choose and
share small source supports instead of repeatedly storing full cofactors. Any
feedback experiment must account for this certification cost, along with
recognition, invalidation, retained traces, persistence and cold reconstruction.
Exposed-case improvements do not supply independent-domain evidence, an efficient
partition of every CNF or a uniform polynomial solution of unrestricted SAT.

Resume [the preserved checkpoint](../experiments/results/cnf-complement-probes/checkpoint.json).
The [protocol](../experiments/results/cnf-complement-probes/protocol.json),
[analysis](../experiments/results/cnf-complement-probes/analysis.json),
[changed events](../experiments/results/cnf-complement-probes/changed-events.json)
and [remaining probes](../experiments/results/cnf-complement-probes/remaining-probes.json)
retain the comparison and its limitations.
