# On-demand negative reuse: smaller payload, slower queries

The optional `NegativeEditPoolSolver` now retrieves checked UNSAT supports across
small clause edits without supplied donor relationships. It builds on the existing
[causal extractor](causal-support.md), rather than introducing another proof rule.
Across exposed and fresh size-holdout streams, it finds ten negative transfers in
each and reduces fresh expansion. Query time nevertheless **increases 2.40% and
5.81%**. Keep the witness pool as the latency baseline and this path as an optional
space/replay tradeoff. Fewer search expansions do not imply a cheaper acquisition.

## Recognition, dependencies and checking

The solver remembers at most 16 completed native UNSAT root descriptions, each
with at most 4,096 literals. It excludes the empty-clause root, whose reuse cannot
help a nontrivial target. On the first expanded residual of a query, it scans recent
origins for clause containment or a difference of at most one missing clause.
Comparison uses actual signed clauses in compact variable coordinates. These
coordinates need not match the original variable identities of related inputs;
containment is still sufficient when the native checker validates the transported
negative subset. Variable-rank changes can cause misses. No generator label,
base-case ID or supplied donor relation enters the solver.

A contained whole origin supplies a ready checked subset. Otherwise, the first
near match triggers causal support discovery. Only a support whose every clause
is present in the target is materialized. Each separate discovery/materialization
traversal permits at most 256 support nodes and 131,072 source literals. A stop or
missing required clause gives no verdict and falls back to the preceding solver.
The policy processes at most one such origin per query. Proposals may be cached
with the bounded origin description, but are never proof authority.

The authority remains the ordinary native verifier. The origin must still have a
checked negative proof; after materialization, the derived core must have one too.
The target is published with exact clause indices and a checked contradictory
subset. If the core already equals the target, its existing proof is reused to
avoid a self-reference. An unsupported deleted premise never certifies UNSAT.
A changed proposal identity fails closed. SAT witnesses still receive complete
target checks through the inherited witness pool.

All earlier proofs and extraction implementations are immutable. This is an
integration of established proof-based core extraction and existing project
machinery, not a novel UNSAT rule or a new tractable SAT family. A certified core
K recognizes the upward-closed family of formulas containing K in the checked
coordinates. This does not give efficient or complete coverage of arbitrary CNFs.

## Frozen matched experiment

Eight serial workers compare the prior witness pool with the new policy in two
orders. Each starts empty. Both use the same 256-native-expansion cap per attempt;
core extraction/publication is separately counted and is outside that cap.
Exposed sizes are 24/48/72; a new holdout uses 36/60/84. Each stream contains 108
queries and 72 roots from the same six designs, two samples, and base/edit/repeat
variants. Holdout roots are absent from the preceding union. Sources and policy
were frozen before either stream, with no selection by solver outcome.

| Measurement | Exposed pool | Exposed negative | Holdout pool | Holdout negative |
|---|---:|---:|---:|---:|
| Mean query seconds | 2.67970 | 2.74396 | 4.84076 | 5.12209 |
| Mean complete worker seconds | 5.74704 | 5.32194 | 10.72402 | 10.56785 |
| Fresh native expansions | 1,961 | 1,579 | 3,159 | 2,781 |
| Native records | 2,044 | 2,298 | 3,414 | 3,745 |
| Key/payload bytes | 11,569,416 | 9,852,603 | 21,321,146 | 19,351,849 |
| SQLite bytes | 21,524,480 | 18,231,296 | 38,293,504 | 34,705,408 |
| Checked graph and candidate bytes | 50,843,748 | 44,165,133 | 92,374,013 | 84,789,324 |
| Mean cold proof seconds | 1.13055 | 0.92774 | 2.06532 | 1.93880 |

Query time regresses in both orders. Complete worker time improves 7.40% exposed
and 1.46% holdout, but the first holdout difference is only 12 ms. Complete time
includes setup, recognition, extraction, solving, independent verification,
publication, append metadata, retained-object measurement, warm replay, cold proof
replay, cold solver reconstruction, sidecars and compression. Two orders do not
support a general runtime claim. Preparation and posthoc audits/profiles are
separate; process RSS includes harness and replay objects.

The policy saves **382 / 378** native expansions, all on edits, but materializes
**650 / 740** core or subset-wrapper records. Total record counts therefore rise
**12.43% / 9.70%**, while payload bytes fall **14.84% / 9.24%** and SQLite bytes fall
**15.30% / 9.37%**. Smaller formulas in the additional records explain why counting
records alone misstates storage. Checked graph measurements fall **13.14% / 8.21%**;
these are retained objects, not isolated peak solver memory.

Exposed outcomes remain 70 SAT / 36 UNSAT / 2 unresolved attempts; holdout outcomes
remain 57 SAT / 48 UNSAT / 3 unresolved. All original budget observations remain.
The negative arm makes 12 / 16 support discoveries, of which 2 / 6 miss containment.
Every successful transfer is on an edit. Holdout hits cover parity (4), disjoint
mixtures (3), colouring (2), and shared mixtures (1); random 3-CNF has no negative
hit. This is reuse across several designs, not increased decision or family closure.

## Dominant remaining cost

The holdout performs **994 support-node visits in discovery and another 488 in
materialization**. The exposed stream performs 448 and another 415. Discovery
currently retains only support indices and identity; materialization repeats
coordinate reconstruction and causal traversal. Derived certificate verification
and serialization then add their necessary costs. The materialized graph can
contain more rows even after the query avoided a search subtree.

A posthoc profile reproduces every result, counter and native archive digest.
Normalization and restriction are its largest exclusive routines. The holdout
has 10,838 normalizer calls and 283,039 restriction-scan calls. Instrumented
phase clocks report about 1.46 seconds for discovery and 1.12 for materialization;
they are diagnostic, overlap routine inclusive timings, and are not the matched
worker timings. The profiling run was separate from the benchmark workers.

**Next primary experiment:** retain a bounded, source-bound derivation plan from
discovery and reuse it during checked materialization. It must bind exact parent
clause indices, residual identities, renamings, unit reasons and branch choices;
it must not turn a cached plan into a trusted proof. Charge construction, retained
bytes, checking, rollback and persistence. Compare on a fresh split before
promoting it. Avoid re-running a support traversal merely to emit the same plan.

The six failed holdout proposals are a distinct coverage gap: the chosen proof's
support still needs a deleted clause. Alternative surviving clause preimages or
proof supports may help, but their discovery and proof costs need evaluation.
A failed support does not show the edited formula is SAT. Candidate order also
limits coverage; the first near match can prevent a useful later one from being
considered. Broad variable correspondence search remains unimplemented.

## Resource and persistence limits

For a target with L literals and retained origins of sizes L_i, candidate matching
costs O(L + sum L_i) expected hash work in the worst complete scan, with an early
stop after two missing clauses per origin. Hashing, equality and integer bit costs
remain explicit. The entry and literal caps bound retained descriptions, not
Python byte allocation, temporary extractor state or the full checked proof graph.
Each proposal is a subset of its origin; both sets and their key strings consume
space. Peaks are 16 origins containing 11,868 / 14,610 literal occurrences, plus
cached proposals and metadata. Per-query retained counters are snapshots, not
additive peak-space measurements.

Traversal budgets cap processed support nodes/literals separately for discovery
and materialization. They exclude prerequisite proof loading/checking, normalized
keys, emitted proofs, transient storage and fallback. Partial checked publications
remain subject to the existing bounded-batch durability/rollback rules. These
limits establish neither a polynomial acquired proof size nor a uniform expansion
bound for SAT. The chosen acquired refutation may itself be exponential.

The negative pool is ephemeral and starts empty on reopening. Cold exact-root
replay validates saved ordinary certificates and can readmit completed roots;
it does not restore the old candidate order or cached proposals. Useful negative
hints and the prior SAT-only index persistence gap remain open. All derived
certificates are preserved in trial archives and the append-only union.

## Validation

The audit checks 864 chronological attempts, all new certificates, 512 exhaustive
two-variable clause-set formulas, both old readers, and the unchanged historical
5,650 composed / 444 pilot decisions. It also rechecks all 864 earlier witness-pool
observations, 108 larger-stream observations, their recovery, and 624 inventory
nodes. All 652 prior sources and 8,141 artifacts across 120 manifests remain
unchanged. The union adds 4,785 keys for **39,211 native records**, retaining prior
payloads when an alternative valid proof differs. All trial archives remain.

The first profiler comparison failed on JSON string model keys versus in-memory
integer keys. Its source/log are preserved in `failed-profile/`; normalized JSON
comparison then confirms identical semantic fields, counters and native digests.
Timed runs and solver policy were unchanged. Resume from
`experiments/results/cnf-negative-edit-pool/checkpoint.json`.


All 1,327 full / 188 focused tests pass, including stale origins, required-clause
deletion, budgets, independent replay and exhaustive small formulas. The full
suite retains 44 SQLite ResourceWarnings at unchanged files; focused tests emit
none. The 230-page manuscript builds without warnings and preserves all 64 proof
blocks. The final source ledger has 658 entries. `checks.json` and `manifest.json`
seal the verified checkpoint and retained failed profiling attempt.
