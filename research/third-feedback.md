# Compose the third layer of failed probes

Checkpoint: 25 November 2026. One checked propagation pass over the 27 failures
retained by [changed-closure probing](changed-closure-probes.md) refutes two more
events without any new assumed probe. Both distinct native roots pass both cold
readers. Recognition reaches **203/246 post-binary events**, leaving **43 open**.
Both gained roots were already UNSAT in inspected snapshots, and ordinary local
solving also proves them. This is increased bounded-recognizer coverage on an
exposed sample, not a new tractability result.

## What is reused and what is checked

B0 contains the source and checked guard consequences. Original failed probes
on B0 justify units in B1. Failed probes on B1 justify further units in B2. The
latest retained failures are checked on B2, and their complements now become
units in B3. Both the control and candidate check the full source, guard proofs,
previous failures, saved closures and new failures, then construct B3. The
control propagates B2; the candidate propagates B3. There are 45 unconditional
propagation calls in each arm and zero new assumed probes.

No proof depends on a unit introduced by its own failed-probe layer. Each B2
failure is checked before its complement is added to B3. Native reconstruction
expands a used exclusion through its actual lower-bank trace, recursively reaching
source clauses or checked guards. Dependencies strictly decrease from B3 to
B2/B1/B0, from B2 to B1/B0, and from B1 to B0. Causal support selection includes
all necessary older traces and guard source clauses before remapping variables.
Existing proof rules, publication checks and cold readers remain unchanged.

The pass has the previous per-event limits: 262,144 occurrence visits and 256
trace steps. Checking, construction and indexing remain additional. Open or
budget-limited outcomes are unresolved, never SAT. Three fixed exclusion layers
do not imply a bound on further layers or on recursive native proof expansion.
The compiler retains publication-only preparation reuse; no production default
or certificate format changes.

## Matched discovery and reconstruction costs

The 45 remaining events span eight targets. Two opposite orders for each target
and arm give 32 isolated census workers. Pilot outcomes were exposed before timing.
Complete census time includes prefix reconstruction, checked preparation,
indexing, propagation and event serialization; earlier acquisition, startup,
loading and final audits remain additional.

| Summed target mean | B2 control | B3 feedback |
|---|---:|---:|
| Discovery (s) | 0.19622 | 0.19890 |
| Prefix reconstruction (s) | 0.80540 | 0.81673 |
| Complete census (s) | 1.00702 | 1.02114 |
| Refuted events | 0 | 2 |
| Assumed probes | 0 | 0 |
| Unconditional propagation calls | 45 | 45 |
| Occurrence visits | 1,349 | 3,036 |
| Derived trace units | 92 | 230 |
| Index literal slots | 53,541 | 53,568 |

This is additional coverage at additional cost, not a discovery speedup. Only
27 literal slots are added to the indexed banks, but they trigger more propagation.
Prefix reconstruction remains about 80% of complete cost. Its path is unchanged;
its timing difference is noise rather than an algorithmic change. Two orders
provide descriptive measurements, not a statistical guarantee.

The two new roots receive two opposite-order fresh/native comparisons each, in
eight isolated workers. Complete trials include warm checking, both cold readers
and persistence, but exclude discovery, acquisition, unresolved fallback, loading
and startup. All four unique archive/root pairs pass both readers.

| Summed case mean | Fresh solving | Layered native proof |
|---|---:|---:|
| Solve/compile (s) | 0.48330 | 1.04567 |
| Warm checking (s) | 0.00477 | 0.02387 |
| Cold readers (s) | 0.49591 | 0.88781 |
| Persistence (s) | 0.19562 | 0.27620 |
| Complete trial (s) | 1.18954 | 2.24492 |
| Encoded record bytes | 2,394,394 | 3,062,862 |
| Records | 145 | 823 |

Compilation is **116.36% slower** and complete trials **88.72% slower** than fresh
solving. Both roots regress in both timings. Encoded bytes grow **27.92%** in
aggregate: `new-1-57` grows and `new-37-62` shrinks. Every regression is retained.
Causal source support shrinks from 2,901 to 780 literal occurrences, but native
reconstruction still emits 793 trace splits and one binary-prefix split. It uses
six original failures, seven second-stage failures and nine third-stage failures.
A smaller support is insufficient to ensure a smaller or faster native proof.

## Space, new closures and the next investigation

Let C and L be the clause and occurrence counts in B2 and U the number of added
units. Index construction and one complete propagation pass use O(C+L+U) expected
word work and space, in addition to sorting, checking and existing proof history.
Both banks and all needed earlier traces remain available. Native source-cofactor
construction, repeated lower-proof expansion, publication and retained records
are additional and have no input-independent size guarantee.

Peak census RSS is 96.67 MB for B2 and 96.73 MB for B3. Peak trial RSS is 78.40 MB
fresh and 77.99 MB layered. These small differences establish no general RAM
saving. The larger aggregate native record payload is a storage regression on
these two cases. Supplemental isolated archives can duplicate shared content;
cumulative authority tables remain untouched.

The 43 open events retain all original sources, guards, proof layers and saved
closures. A separate scan-based diagnostic reconstructs and checks their complete
B3 unit closures, charging its counters and 0.21165 seconds outside timed bounded
discovery. They contain **90 assignments** in total. Six cases gain **18 assignments**
over their B2 closure, including **five beyond the 13 newly added exclusion
variables** in those cases. Thirty-seven closures do not change. The original
27 failures have not been erased: the two gained case files retain their fourteen
failures, and the open-state files retain the other thirteen.

`remaining-closures.json` is the next resumption state. It adds explicitly named
B3 closure fields without overwriting any earlier closure or proof. The complete
export is 819,457 bytes, while the open-state file before this extra diagnostic
is 765,499 bytes; the two case files total 51,517 bytes. These export sizes do not
bound process RAM, native tables or future history.

The highest coverage opportunity is now a source-bound cursor for previously
untested candidates on the 37 unchanged cases. Saved unresolved programs do not
record or certify their complete tested prefix. Preserve enough scheduling state
to resume an actual search and invalidate reuse when the exact bank, ranking or
semantics change. The six changed B3 closures support a further bounded search,
but repeating propagation on the same complete fixed point adds nothing.

The cost priority remains checked preparation reuse and cheaper native proof
construction. Further coverage should be evaluated together with this 2.16-fold
compile-time and 1.28-fold byte regression; no full-workload advantage over
ordinary solving is established. No unrestricted-SAT or P-versus-NP bound follows.

All 1,935 tests pass, including 70 focused tests. New tests cover exhaustive truth
checks, all three exclusion layers, malformed and forward dependencies, guards,
full/support native compilation, warm validation, both cold readers, budget stops
and satisfiable open banks. All 64 earlier manuscript proof blocks, 1,077 earlier
source fingerprints, 188 parent manifests and 25,615 earlier artifact entries
remain intact. Resume `experiments/results/cnf-third-feedback/checkpoint.json`.
