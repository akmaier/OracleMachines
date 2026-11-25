# Probe changed closures and retain the next proof layer

Checkpoint: 25 November 2026. Another bounded probe round refutes eight of the
53 events left by [two-layer feedback](layered-feedback.md). All eight distinct
roots compile to native certificates and pass both independent cold readers.
Recognition reaches **201/246 post-binary events**, leaving **45 unresolved**.
All eight were already UNSAT in inspected snapshots, and fresh local solving
also proves them. This expands the bounded recognizer on an exposed sample; it
does not discover a new tractable class or settle unrestricted SAT.

## Which work can be skipped

Only 21 of the 53 saved closures changed after adding the preceding failed
probes. The control repeats the existing deterministic, complement-promoting
probe order on every second feedback bank. The candidate first validates both
old proof layers and both closures, then compares the complete first and second
banks and their fixed assignments. Exact equality allows the scheduler to skip
that event as **unresolved**. Both arms include this equality diagnostic; only the candidate acts on it.
The comparison uses no approximate signature.

On these retained inputs, the 32 skipped events yield no failed probe in the
control either. Both methods find the same eight refutations and the same 49
failed probes overall. The candidate avoids 2,048 assumptions: 2,969 become 921.
This reduction removes repeated search, not seed checking or reconstruction.

The skip is a search policy, not a theorem that an unchanged formula cannot
benefit from more search. An unresolved proof program certifies its recorded
failures, not the probes it omitted. Changing the candidate order, budgets,
semantics or prior search history can invalidate an expectation of identical
coverage. A regression test deliberately supplies an unchanged bank with an
empty history: the candidate leaves it unresolved while the control refutes it.
The policy remains sound because neither the skip nor an open probe certifies
SAT or search exhaustion. Exact reusable search-prefix receipts and a cursor
for previously untested candidates remain open work.

## Checked third-stage probes

Let B0 contain the source and checked guard consequences, B1 additionally contain
units justified by the original failed probes, and B2 additionally contain units
justified by the next failed probes. The source, guards, each original proof on
B0, each next proof on B1, and the complete unit closures on B1/B2 are checked
before scheduling. New assumptions range over variables still active after the
B2 closure. Each event has an additional cap of 64 assumptions, 262,144 occurrence
visits and 256 trace steps, including the saved closure prefix. These are new
budgets, not lifetime limits; preparation and indexing are additional work.

The residual is built once. A failed residual probe is transported back to B2
using exact clause origins, with the closure trace prepended. Opposite failed
assumptions give an UNSAT proof. New probes never become premises for other
probes in this round. They remain a separate proof layer whose reasons refer
to B2. A subsequent feedback bank has not yet been propagated in this checkpoint.

Native reconstruction slices the causal support of both terminal traces, then
recursively includes the older failed-probe and guard supports they use. Expansion
of an exclusion leaf descends from B2 to B1 or B0, or B1 to B0; it cannot refer
forward. The two top traces become a native split on their opposite assumptions.
Checked binary-prefix frames lift the result back to the original event root.
All publication checks, child relations and cold readers remain unchanged.
The compiler uses the publication-only handoff from
[prepared publication](prepared-publication.md). No production default changes.

## Matched costs

The census uses two opposite orders per target and method, in 32 isolated workers
covering all 53 events. The pilot was exposed before timing. Input loading,
startup, previous acquisition and the final audit are additional. The complete
census includes source-prefix reconstruction and event serialization; discovery
includes seed/closure checks, scheduling, conditioning, indexing and propagation.

| Summed target mean | All events | Changed events |
|---|---:|---:|
| Discovery (s) | 0.26477 | 0.23367 |
| Prefix reconstruction (s) | 0.92847 | 0.93337 |
| Complete census (s) | 1.19897 | 1.17252 |
| Assumed probes | 2,969 | 921 |
| Occurrence visits | 111,214 | 45,964 |
| Probe initialization clauses | 1,157,819 | 329,595 |
| Index literal slots | 57,491 | 19,657 |

Discovery falls **11.75%**, while complete census time falls only **2.21%**.
Source-prefix reconstruction still accounts for about 80% of complete cost.
The reconstruction paths are identical; their timing difference is not an
algorithmic improvement. Two order repetitions are descriptive measurements.
They do not establish a production speedup or general runtime guarantee.

All eight new roots receive two opposite-order fresh/native comparisons, in
32 further isolated workers. Complete trials include warm checking, both cold
readers and persistence. They exclude discovery, prior acquisition, unresolved
fallback, loading and startup.

| Summed case mean | Fresh solving | Layered native proof |
|---|---:|---:|
| Solve/compile (s) | 0.89211 | 1.55292 |
| Warm checking (s) | 0.01398 | 0.08154 |
| Cold readers (s) | 0.95297 | 1.15508 |
| Persistence (s) | 0.31095 | 0.39183 |
| Complete trial (s) | 2.20470 | 3.21401 |
| Encoded record bytes | 4,569,461 | 3,925,230 |
| Records | 379 | 1,518 |

Compilation is **74.07% slower** and complete trials **45.78% slower** than fresh
solving. Only one of eight compile times and two complete times improve. Bytes
fall 14.10% in aggregate, but three cases grow. All regressions remain in
`analysis.json`. Smaller supports do not imply fewer proof nodes or faster
publication: the source support falls from 8,481 to 1,878 literal occurrences,
yet reconstruction still emits 1,429 trace splits and checks 1,518 records.
There is no demonstrated full-workload advantage over ordinary solving.

## Space, preservation and remaining gaps

All old banks, guard templates and failure traces remain necessary for checking.
The scheduler's exact comparison takes at most linear bank/assignment work with
no retained equality index. A searched event additionally builds the conditioned
bank and occurrence index; each failed probe copies the closure prefix. New
probe buffers, ranking and output storage remain input-dependent. The skip
avoids those probe allocations, not the already-loaded proof history.

Peak census RSS is 96.85 MB for all and 96.73 MB for changed, providing no useful
whole-process memory-saving evidence. Peak native-trial RSS is 69.57 MB versus
64.27 MB fresh. The 1,518 native records are supplemental isolated archives;
the cumulative authority tables are unchanged. Archive sums can duplicate
content shared across cases.

The 45 remaining events retain all their previous sources, guards, proof layers
and closures, with the new round attached. Eight now carry **27 additional failed
probes on B2**, with 1,243 unit-trace steps. Their compact probe-list encoding is
13,165 bytes; the complete self-contained remaining-state file is 811,351 bytes,
and the eight case files total 145,557 bytes. These export sizes are not database
or RAM bounds. The other 37 remaining events have no newly failed assumption,
including all 32 skipped events. No previous evidence is removed.

The next coverage target is a checked feedback pass over those 27 failures,
without new assumptions. For cases with no new failures, preserve a source-bound
search cursor and try untested candidates rather than the same fixed prefix.
The main cost opportunities remain reuse of checked source/prefix preparation
and reducing native cofactor construction and publication while preserving
semantic checks. More rounds can still require exponentially many distinct
contexts and unlimited retained history; these measurements do not bound that
process.

All 1,927 tests pass, including 62 focused tests. New checks cover exhaustive
truth tables on small generated CNFs, budget stops, guards, backward proof
provenance, support/full compilation, malformed warm-cache inputs, both cold
readers, and the scheduling counterexample. All 64 earlier manuscript proof
blocks, 1,072 earlier source fingerprints, 187 parent manifests and 25,456 earlier
artifact entries are unchanged. The 16 unique new archive/root pairs pass both
independent readers. Resume
`experiments/results/cnf-changed-closure-probes/checkpoint.json`.
