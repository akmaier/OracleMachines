# Sharing preparation across independently cold-checked B12 snapshots

Checkpoint: 26 November 2026. An owned cold-validation batch reduces checking
**26.98% for source order** and **26.97% for untested-first** against separate
calls to the current validator. Complete measured workflow time falls
**11.79% / 11.39%**. Every saved snapshot, reconstructed bank, provenance entry
and discovery counter is unchanged. Coverage stays **232/246**, with fourteen
open; this experiment adds no failure, assignment or native certificate.

## Recognition and exact validation

`cnf_b12_cold_batch.validate_many` accepts the original 24 portable inputs, five
closures, one ordering policy and a nonempty list or tuple of snapshots. It
privately copies inputs, closures and snapshots before any counter callback.
All snapshots must have valid headers and the same positive integer trace bound;
mixed bounds must be checked in separate batches. The batch reconstructs the
common B12 clauses, provenance, closure, schedule and binding once, checking all
lower histories through the existing shared preparation.

For **every** snapshot, it runs the unchanged B12 cursor loader, which checks the
exact input/policy binding, deterministic completed prefix and saved failed-probe
proofs. It then checks the exported program against the source-derived bank and
requires exact program/cursor agreement. No proof check is skipped for duplicates
or later snapshots. No prepared object or trust is accepted from discovery, and
nothing remains trusted between calls. Changed source, history, closure, policy,
bound or malformed proof must pass the same checks as an ordinary cold call.

The equivalence argument is limited and direct: fixed owned inputs, closures,
policy and trace bound determine one common preparation. Snapshot checks do not
mutate that preparation; the loader reconstructs private cursor state. Replacing
repeated preparations by this single preparation therefore leaves each individual
acceptance check and returned bank unchanged. Tests also compare with frozen B12
validation and independent reconstruction from lower routines.

This API checks the supplied snapshots **individually**. It does not certify that
they form consecutive rounds, cover every round, or obey an acquisition budget.
Reversed or duplicate valid snapshots remain valid and are each checked. The
experiment audit separately demands exact equality with all previously saved
rounds. As before, claimed open completions are schedule history rather than
proofs: they are not rerun, so coverage reuse assumes honest production. Failed
proofs are checked independently; neither a complete label nor an open prefix
establishes SAT. No new trust claim is introduced.

## Matched workload and costs

Four balanced rotating orders compare separate cold calls with the batch before
the regression suite runs. Both arms use the same already-batched discovery,
reconstruct the same fourteen source cases, serialize every round, reload it and
cold-check it. Twelve cases have one snapshot; `(37,39)` and `(67,63)` have three,
for **18 snapshots per ordering**. The separate arm retains the prior comparison's
list of prepared returns and checks their equality; the batch returns one common
prepared tuple. This is a replay optimization for these saved histories.

| Mode | Reconstruction (s) | Discovery (s) | Cold checking (s) | Persistence (s) | Complete census (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| source separate | 0.15825 | 0.18291 | 0.23974 | 0.00531 | 0.59987 |
| source batch | 0.15767 | 0.18234 | 0.17506 | 0.00544 | 0.52913 |
| unseen separate | 0.15817 | 0.18493 | 0.23956 | 0.00504 | 0.59542 |
| unseen batch | 0.15643 | 0.18211 | 0.17495 | 0.00560 | 0.52759 |

Common cold preparations fall **18 → 14** for each policy. All-history schedule
checks fall **35,192 → 28,404** because the common lower histories are checked
once per batch. Every current snapshot is still replayed and proof-checked.
Discovery is unchanged: **296 probes**, eighteen index builds, and
10,028 / 8,969 occurrence visits. Cold checking on the two multi-snapshot cases
alone falls **65.21% / 64.94%**. These are measured timings on an exposed small
frontier, not a prediction for arbitrary inputs or independent held-out workloads.

Seven source-order and two untested-first case-level checking regressions remain,
all on single-snapshot cases. Persistence is **2.56% / 11.06% slower** in aggregate,
although its implementation and bytes are unchanged. Discovery and reconstruction
also fluctuate; their counters agree exactly. Raw per-case measurements and all
regressions are retained rather than attributing these changes to new search work.
Startup/input loading, acquisition, pilots, native compilation and final lineage
audits are additional; audit timings overlap tests and are not production timings.

Snapshot sizes stay **226,983 / 229,561 bytes**. Peak RSS rises from
**99,188,736 to 99,483,648 bytes** for source order, and **99,172,352 to 100,564,992**
for untested-first. There is **no measured memory or proof-storage saving**.
The existing **15,490-byte** frontier overlay still references **4,508,174 bytes
across 214 transitive files**; no duplicate resume overlay is created. Earlier
native archives and other evidence are additional. This experiment's new evidence
adds storage, even though the logical frontier is unchanged.

## Resource statement and remaining gaps

For `r` snapshots on one common context, repeated preparation work `rP` becomes
`P`. Common input copying also occurs once. Each snapshot still pays ownership
copying, header/binding work, cursor replay, proof checks and program agreement;
serialization and reloading are unchanged. Grouping incompatible contexts and
recognizing equality across them is outside this API. It accepts only an already
specified common context and verifies each binding; no semantic equivalence
oracle or cross-call cache is assumed.

If common portable inputs occupy `H` bytes, snapshots occupy `S_i`, prepared state
uses `M` space and one snapshot check needs at most `W`, additional batch live
space is `O(H + sum(S_i) + M + W)`, apart from caller-owned data and counters.
It is not a streaming validator: owning the entire list can cost more space than
checking and releasing snapshots individually. A caller retaining every separate
prepared return also pays for those returns. The measured RSS does not establish
a memory improvement under either usage. No lifetime storage bound changes.

The optimized workflow is now approximately **34–35% discovery, 33% checking and
30% reconstruction**. No phase overwhelmingly dominates. Return to the coverage
gap: compare the strengthened closures at `(37,39)` and `(67,63)` against retained
B13 schedules. Both old B12 orders are exhausted on all fixed banks, so identical
repetition cannot supply new information. Unchanged exhausted cases need stronger
checked interactions or another decomposition. Earlier native-compilation
regressions and uniform arbitrary-SAT acquisition/resource obligations remain.

## Preservation and validation

Resume `experiments/results/cnf-b12-cold-batch/checkpoint.json`, field
`b12_cold_batch.remaining`, with the existing
`compare_cnf_b12_continuation_batch.load_frontier` loader. The binding is identical
to the parent's remaining frontier; earlier checkpoint fields are retained.

The audit preserves **1,183 source fingerprints** and **32,048 artifact entries
in 213 manifests**. Four new source files bring the ledger to 1,187. Reference
and cumulative tables, all native archive bindings, every previous failure and
both policies' saved round sequences remain unchanged.

Nine new tests cover every historical snapshot and independent bank reconstruction;
corruption at every snapshot position; changed histories, sources, closures and
policies; valid but incompatible trace bounds; private ownership and callback
mutation; duplicate/reversed snapshots; cross-call invalidation; malformed headers;
and small-model correctness. The latter enumerates all 256 subsets of eight
signed unit/binary clauses on two variables plus seventy generated five-variable
formulas, checking applicable unit-simplified open histories against exhaustive
models. It is not general CNF coverage.

All **2,154 tests** and **36 focused tests** pass. The full suite retains 44 SQLite
resource warnings, as in the parent run; focused tests have none. The manuscript builds at 307 pages without LaTeX warnings; all 64 existing
proof blocks remain byte-identical. Protocol, pilot, four-order census,
audit, decision and raw/normalized logs are preserved under
`experiments/results/cnf-b12-cold-batch/`. No production default, new tractable
family, native certificate or polynomial unrestricted-SAT result is claimed.
