# Share support discovery with checked proof construction

The optional `PlannedNegativeSolver` retains the causal choices made during
support discovery and uses them to emit the ordinary proof. It removes a second
support-selection traversal without changing the native verifier or the preceding
negative-origin selection policy. On matched exposed and fresh size-holdout
streams, mean query time falls **6.45% / 2.62%** against negative edit reuse.
The holdout still costs **0.87% more than witness-only search** on the mean, with
mixed paired signs. Keep both baselines; this is not a general latency result.

## What is shared, checked and discarded

Discovery records the selected parent clauses, compact names, core identity,
dependencies, causal unit trace and split choices. A query-local recipe covers
each supported native negative proof form: empty clause, implication conflict,
Hall conflict, component, positive subsumption, units and split. Emission follows
the saved dependencies in the original order and reconstructs ordinary proofs.
It still restricts formulas where required, constructs subset certificates,
serializes records and invokes the unchanged native checker. Saving the support
choices does not make proof construction or checking free.

The plan is a hint. No result is accepted because a recipe says that it is valid.
The origin must have a checked negative proof, the core must be independently
checked, and the target must contain the certified support in the checked
coordinates. An existing identical core is reused without a self-reference.
All plans clear after a hit, miss or exception. Cold replay needs only the ordinary
persisted certificates; it does not restore plans or negative candidate order.

Preparation keeps the preceding limits of 256 support nodes and 131,072 source
literals. A new 4 MiB conservative charge includes recipe strings, origin keys,
result objects and indices, core-key strings and both mapping tables. Duplicate
references are charged conservatively. The charge is checked after insertion:
an oversized candidate can allocate temporary memory before the whole partial
plan is discarded. Encoding/decoding transients, the active emission workspace,
allocator overhead and the existing checked graph are outside this limit.
It is a retained-plan limit, not a process-memory bound.

On plan-cap exhaustion the solver charges discarded preparation and falls back
to the preceding bounded extractor. This can repeat work. A support-budget stop
or missing required clause supplies no verdict. Native expansion counts exclude
proof materialization, while support limits exclude prerequisite verification,
emitted certificate size and fallback. No total polynomial bound follows.

## Frozen comparison

Twelve serial workers compare witness-only retrieval (`pool`), the preceding
negative edit policy (`negative`), and shared plans (`plan`) in two opposite mode
orders. Every worker starts empty with the same 256-native-expansion limit per
attempt. The exposed scales are 24/48/72; the fresh holdout uses 42/66/90. Each
stream has 108 queries and 72 distinct roots, using six designs, two samples and
base/edit/repeat variants. All holdout roots were absent from the prior union.
The solver receives no generator labels or supplied donor relationships.

| Measurement | Exposed negative | Exposed plan | Holdout negative | Holdout plan |
|---|---:|---:|---:|---:|
| Mean query seconds | 2.61769 | 2.44895 | 8.65822 | 8.43098 |
| Mean complete worker seconds | 5.16024 | 4.99842 | 17.22116 | 17.04635 |
| Native records | 2,298 | 2,298 | 5,443 | 5,443 |
| Key/payload bytes | 9,852,603 | 9,852,603 | 33,900,072 | 33,900,072 |
| SQLite bytes | 18,231,296 | 18,231,296 | 59,691,008 | 59,691,008 |
| Checked graph and candidate bytes | 44,165,133 | 44,173,507 | 146,304,548 | 146,313,399 |
| Mean cold proof seconds | 0.90982 | 0.91466 | 3.26082 | 3.28200 |
| Mean warm seconds | 0.04269 | 0.04306 | 0.05603 | 0.05657 |

Query and complete-time differences improve against `negative` in both orders;
complete time falls 3.14% / 1.02%. Every query's result, native expansion count,
new record identities/order and actual proof bytes match that policy. Preparation,
recognition, plan serialization/sizing, emission, checking, publication, graph
sizing, warm/cold replay, cold reconstruction, sidecars and compression are charged
by the complete worker. Study preparation and posthoc audits/profiles are separate.
Two orders on synthetic designs do not establish representative performance.

The plan eliminates **415 / 518 repeated support-node visits**, replacing them
with recipe emission. Discovery still visits 448 / 889 nodes, including failed
proposals. Accepted retained-plan charges peak at **711,610 / 1,378,956 bytes**;
no plan-cap fallback occurs in these streams. Capacity fallback is tested
separately. Summing per-query peaks would not measure peak memory.

Permanent proof storage is identical to `negative`. Measured checked-object space
rises slightly because reconstructed objects share references differently; process
RSS also rises slightly, and includes harness and replay objects. Mean cold and
warm times regress. These costs remain in the record. Compared with `pool`,
SQLite storage remains 15.30% / 6.55% smaller, inherited from the negative policy,
while record counts are higher. Pool query means are 2.58311 / 8.35832 seconds:
planning wins exposed query time but does not establish a holdout latency win.

Outcomes remain **70 SAT / 36 UNSAT / 2 unresolved attempts** exposed and
**57 SAT / 41 UNSAT / 10 unresolved attempts** on holdout, for all three modes.
The optimization adds no decision coverage or recognized-family closure. The
posthoc profile matches all outputs, counters and native digests. Instrumented
holdout materialization drops from 1.342 to 0.458 seconds; discovery is 1.311
versus 1.350 seconds. These diagnostic clocks overlap routine inclusive times
and are not the matched worker measurements.

## The next structural opportunity

In the first holdout plan worker, random 3-CNF and parity mixtures consume
**79.16%** of query time. Ten budget-stopped attempts account for 4.976 of 8.428
seconds. They leave 2,622 checked negative residual records across their commits,
but those are refutations of conditioned residuals, not automatically of the
unconditioned source. Six distinct source roots remain absent at stream end;
some earlier stopped roots finish on later repeats. Partial-search transport
across edits therefore remains a substantial reuse gap.

A posthoc screen applies the existing explicit-parity extractor and independent
affine-negative checker to **every one of the 108 holdout inputs**, without family
labels. It obtains **14 checked negative observations**, including budget-stopped
cases **42 and 43**. Case 42 later completes natively; case 43 is still missing
at native stream end. Total screen time is 0.099 seconds, including normalization,
extraction and checking but excluding publication, persistence and cold replay.
The certificates and source bindings are retained in `affine-screen.json`.

This is evidence for integrating an existing authority into the general query
path, not a new affine algorithm or a measured end-to-end saving. The timed
unknown observations stay unchanged. A consistent extracted subsystem gives no
verdict for its leftover CNF. The two certificates do not settle the other eight
budget-stopped attempts or all parity mixtures.

**Next primary experiment:** a bounded, source-checked affine-negative probe before
expensive native acquisition, with a fresh frozen split and both latency baselines.
Charge misses, row discovery, elimination, certificate construction, publication,
restart and retained state. Preserve ordinary fallback for consistent/incomplete
subsystems. Follow with checked transport of committed residual proofs and
alternative surviving supports: four current holdout support proposals miss
containment, with no support-budget stop. Durable candidate retention, broad
variable correspondence and representative external workloads remain open.

## Preservation and validation

Resume `experiments/results/cnf-support-plan/checkpoint.json`. The append-only
union has **45,061 native records** and all previous extension tables. All
658 prior source files and 8,197 artifacts across 121 manifests remain unchanged.
The audit checks 1,296 chronological attempts, 432 exact plan/negative query
comparisons and every one of the 512 two-variable clause-set formulas. Earlier
composed/pilot decisions, witness/negative observations and larger-stream evidence
remain valid. Earlier authoritative bytes win union conflicts; 260 alternative
valid-payload observations remain in their full trial archives.

Nine new tests cover proof forms, one-pass support selection, byte/node/literal
limits, tampered plans, deleted premises, rollback, cold replay and exhaustive
truth-table agreement. All **1,336 full / 197 focused tests** pass. The **231-page
manuscript** builds without warnings and keeps 64 proof blocks unchanged. The
full suite emits 44 SQLite warnings: 42 at unchanged project files and two at
interpreter collection sites; focused tests emit none. One collection site differs
from the preceding run, so the first finalizer's overly strict site check fails.
Its source/state/failure are preserved, along with a second audit failure from
unresolved Homebrew path aliases. The corrected audit resolves paths and records
the changed site. A collection site does not identify where a connection was
opened; no timed result or test changed.
`checks.json` records this evidence; the final source ledger has 664 files.
The affine screen is a separate checked artifact, not a rewrite of native outcomes
or an insertion into the authoritative SQLite union. No unrestricted SAT or
P-versus-NP conclusion follows.
