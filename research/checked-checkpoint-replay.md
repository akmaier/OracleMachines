# Retaining checked evidence during checkpoint replay

2026-11-15. The preceding profile identified cold preparation as a larger cost
than local expansion. The latest five checkpoint restorers repeatedly open a
fresh inventory for delta checking, another for positive coverage, and another
for startup. This investigation preserves those checks while retaining the
already checked dependencies between them.

## Reuse condition and correctness

`CheckedReplay` starts from an identity-bound, reconstructed parent. The caller
exclusively owns the database connection, file and cached objects. A successful
merge can only append an absent key or find its identical existing payload.
Conflicting payloads are rejected. New patterns, probe windows and continuation
records receive the same checks as the previous cold delta checker; unsupported
record tables must remain empty in the delta. Archive and source fingerprints,
full table digests, bridge checks and expanded positive certificates remain
separate obligations in the comparison driver.

The invariant is that every cached verdict was established under the same
policy against its exact, immutable source and referenced rows. Appending other
rows preserves those premises. A newly checked row can then extend the cache.
This is induction on checked append operations, not an assumption that an
unexamined row is valid. Missing-node lookups are not promoted to negative
certificates. A node's stored internal coverage summary is distinct from the
complete external route catalog, which is reconstructed and queried at startup.

A merge holds a write reservation, checks every proposed row, and commits only
after validation. Failure rolls back the suffix and invalidates the live replay
object, including any partial cache populated during the failed check. Checked
state cannot be handed off after invalidation. Guards reject data-version,
schema, policy or unexplained same-connection changes and unfinished acquisition.
The contract requires immutable cached Python objects and exclusive ownership;
it does not defend against arbitrary memory edits, raw-file modification or
forged SQLite pragmas. No trust cache is serialized to disk.

Nine focused tests exercise repeated and novel rows, equivalence with the frozen
cold checker, conflicting old payloads, forged new certificates, unsupported
delta tables, external and direct writes, policy changes, unfinished checking,
rollback of writing callbacks and ownership transfer. The full preceding test
suite is retained.

## Cost model and experiment

Let C_i be the set of nodes checked in replay phase i, including each node's
policy identity. Fresh verifiers pay dependency checking again when a node
occurs in several C_i. Retention can pay that node check once across their union.
Top-level certificate traversal, source/key comparisons, guard work, all delta
rows and ten full table-digest scans across the five stages remain. Retained
space follows the union of dependency closures rather than the maximum closure
of a single fresh phase. Neither the number of nodes nor their certificate
sizes have a uniform polynomial bound here.

The matched experiment starts from the same restored older checkpoint and
replays the guarded-digest, original-handoff, session-catalog, copyless-sequence
and canonical-source checkpoints. Each arm pays a seed copy, report/source
identity checks, archive hashing and decompression, full before/after table
digests, conflict checks, all new-row and expanded positive checks, and a complete
global query with output serialization. Two repetitions reverse execution order.
The fresh control uses the same guarded merge/check implementation but discards
its inventory after each phase; the candidate carries it into startup. An
additional independent audit uses the frozen legacy restorers and fresh checks.

The test suite finishes before the first measured arm. It overlaps the shared
older restoration, so that restoration's elapsed time is a charged setup
observation, not a clean comparative measurement. The matched arms run without
tests, profiling or a manuscript build. Both orders share OS caches and use the
same development history; these measurements are not held-out speed guarantees.

## Measured result

| Mean seconds or count | Fresh verifiers | Retained verifier |
| --- | ---: | ---: |
| Five-checkpoint suffix replay | 28.92930 | 24.22978 |
| Startup, complete query and serialization | 65.36514 | 63.47681 |
| Complete measured sequence | 94.29444 | 87.70659 |
| Positive-check phases within replay | 21.10661 | 14.82851 |
| Node verifications across replay and startup | 28,059 | 23,320 |
| Checked nodes carried into startup | 0 | 1,027 |
| Final / maximum recorded checked-node count | 23,320 | 23,320 |

The complete sequence improves **6.99%**, replay **16.24%**, and startup **2.89%**.
Sequence samples are **94.25839 / 94.33048 seconds** for fresh verifiers and
**87.12909 / 88.28409 seconds** for retained state. The candidate avoids **4,739
repeated verifications (16.89%)**. Phase savings cannot be added as independent
speed ratios; copying, digests and other preparation vary between observations.
The shared older restoration costs **114.50260 seconds**, with the overlap
qualification above, and is outside these matched sequences.

All five historical appends are replayed, comprising **172 already recorded
rows**. This experiment acquires no new SAT patterns and changes no stored
certificate, policy or structural coverage. History remains **780,677,120 bytes /
42,475 patterns**, coverage **69/83**, and the retained reference contains **4,802
nodes**. The four final histories have the parent's exact logical table digests;
all complete-query certificates and next selections match the parent. The
maximum recorded checked-node count is unchanged, but object residence time,
other caches and process peak RAM are not captured by that count. There is no
new persistent cache or disk-space reduction.

## Next work and unchanged resume checkpoint

Resume `experiments/results/cnf-canonical-source/report.json` with the frozen
`compare_cnf_canonical_source.restore_checkpoint`, using **next_selection**:
**case 1227, index 38, 40/165/494, no pending split**. Its report hash remains
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`.
Preserve evidence **(1, 42, 156, 63, 1)** and **two bridges**. The new live replay
helper is optional machinery; a process restart must still validate its parent.

First continue discovery on that unresolved original. For further replay work,
check the contracts of earlier checkpoint schemas before extending this suffix.
Later positive-check phases still take about **2.6 seconds** while checking zero
new inventory nodes: retaining nodes does not avoid repeated certificate
traversal, source/evidence binding or decoding. Investigate that measured work
before adding another cache. The remaining global startup is about **63.48
seconds** and older restoration is separate. No complete efficient partition
of arbitrary SAT or uniform polynomial expansion bound follows here.


The retained session-catalog and copyless stages each replay **3,564 positive
steps**, including **3,458 direct semantic-rule checks**, despite checking zero
new inventory nodes. Their first-run positive phases take **2.63705** and
**2.65856 seconds**. `PositiveReplay` deliberately reads untrusted rows and
checks selected semantic reductions separately from the inventory's stronger
historical-policy contract. A future cache must bind the exact source, row,
policy and selected rule, preserve all external-evidence checks, and still check
premise order and root justification in each certificate. A counter showing
zero new inventory nodes does not mean that semantic verification is absent.

## Final validation and preservation

The independent legacy audit passes, including full restoration, complete global
composition, exact certificate and next-selection equality, and unchanged final
database bytes. Restoration takes **143.36951 seconds** and startup **65.00404
seconds**; these are separate validation observations, with manuscript compilation
overlapping part of the audit. The full producer takes **692.74356 seconds**.
All **283 tests** pass. No fresh discovery occurs in any replay or audit.

All **2,058 prior artifacts from 36 manifests** retain their hashes, and validation
checks **119 source fingerprints**. The new manifest binds **19 artifacts /
2,610,547 bytes**, excluding itself. Existing reference evidence remains unchanged;
this run introduces no new reference nodes. The manuscript builds to **168 pages**
with all **64 prior proof blocks unchanged**, no new proof blocks, no undefined
references and no overfull boxes. Test, build and producer logs are retained.
