# Resume ordinary frontier probes through exact history lookups

The open 23-variable, 93-clause source now retains a checked ordinary window for
variables **7, 9, 16 and 17**. Both assumptions for each variable are clear:
unit propagation finds no conflict, so this block supplies no forced reduction
and no SAT verdict. Structural coverage remains **58/83 reused development
inputs**. The next ordinary candidates are **18, 21, 22 and 23**. Saved split
pairs **5, 6, 11 and 13** and the wider 17-base / 88-candidate learned queue remain.

This run also establishes a narrow path from positive reuse toward cheaper
expansion. An initially empty working database reads exact missing identities
from the complete, read-only authoritative archive. The old source and prefix
validators run before reuse. Newly acquired records are appended locally and
exported as a delta. The positive-only bundle is not used as a discovery store.

The following [forced-reduction checkpoint](source-local-forcing.md) advances
this window and retains a smaller 22-variable residual. The measurements below
describe the preceding clear-block experiment.

## Membership, scope and validation contracts

`experiments/cnf_source_local.py` implements two separate mechanisms:

1. `ReadThrough` accepts only exact-key reads and inserts on six fixed tables.
   Every local miss consults a pinned read transaction on authoritative history.
   A successful historical read is copied into the working cache. Every proposed
   insertion independently checks authoritative membership and refuses an old
   identity. Local transaction rollback also rolls back new-row metadata.
   Export includes novel rows only, excluding imported dependencies.
2. `SourceProbeRoutes` gives the existing ordinary continuation scheduler lazy
   exact membership maps. A saved window is checked before entering its cache;
   saved continuations use the original recursive prefix checker. Numeric
   offsets alone never authorize skipping work. Iteration over the partial map
   fails instead of pretending to enumerate all routes. The API is bound to one
   source and one inventory instance; it is not a complete route catalog.

The authority must be reconstructed and bound to its preserved parent first.
The local store starts empty, and both historical validation caches start fresh.
The read transaction fixes the authority's snapshot. No portable absence proof
or disconnected resumption is supplied: without that archive, the operation
cannot proceed. A local absence never authorizes a new state. Ordinary stream
exhaustion follows checked clear blocks and recomputed bounded ranking, and says
nothing about learned streams, other routes, structural coverage or UNSAT.

Admission remains owned by the caller. `advance_one` does not reset the allowance;
forced residuals pass through the unchanged recognizer and retain a pending edge
if the allowance is exhausted. Tests include a forced residual acquired after
restart and an existing pattern omitted from the local database that must reuse
history with zero admissions. The real measured block requires no new pattern
states. Thus it tests useful expansion persistence, but not expensive branching.

The final delta is conflict-checked against full history, applied to a copy and
cold-checked using the original semantic validators. Reapplying it is bytewise
idempotent; the parent remains byte-identical. Only one clear probe-window row is
added. No edge or pattern changes, so the existing coverage proof stays valid and
the route set gains no closure edge. This is a local validation extension to an
already checked parent, not a fresh audit of every historical record.

## Matched cost accounting

Both modes receive the same reconstructed authority, preselected source,
configuration and 32-state allowance. Each performs one ordinary advance and
exports its delta in a fresh subprocess outside the repository working directory.
The eager control uses `ContinuationRoutes`, prepares its historical route
catalog, copies the full database and uses the old full-table delta exporter.
The local mode loads only the needed source and uses its new-row index for export.
The two modes produce byte-identical deltas, identical probe records and the
same discovery counts, with zero admitted states.

| Mean measure | Eager control | Source-local mode |
|---|---:|---:|
| Preparation, seconds | 5.84773 | 0.01070 |
| One advance, seconds | 0.00656 | 0.00744 |
| Delta export, seconds | 4.81971 | 0.00140 |
| Worker operation, seconds | 10.89267 | 0.01991 |
| Complete process, seconds | **10.99932** | **0.12683** |
| Working SQLite bytes | 770,347,008 | 94,208 |
| Historical nodes checked, both policies | 1,692 | 1 |

The complete-process reduction is **98.85% for this operation with an available
authority**. It removes catalog preparation, full copying and full-table delta
comparison. Actual probing is slightly slower, and no faster SAT decision
procedure is demonstrated. The samples run eager/local then local/eager, sharing
OS caches; two repetitions provide no confidence interval. No tests or builds
overlap these timed workers. Source selection was reused from the preceding
checkpoint and is not part of this comparison.

The local mode imports **one historical row / 9,352 key-plus-payload bytes**.
It makes three read-path authority lookups (two misses) and one additional
insertion membership check. A separate cold resume imports the source and new
window, **two rows / 14,725 bytes**, without new discovery. These are logical
bytes and SQLite sizes, not total memory or measured peak RAM. The authority
itself remains **770,338,816 bytes**, in addition to the local working database.
It has not been compressed away or deleted. The dependency closure can still
span much of the archive on another source. This access policy supplies no
source-independent bound on imported rows or validation work.

First restoration still costs **20.59393 seconds**. The final copy/merge costs
**0.10878 seconds**, and cold delta checking costs **0.06109 seconds**; integrity
checks, compression and diagnostics also remain in the **45.50471-second** study
pipeline, which includes all four timed workers. These shared operations are
outside the worker comparison. Do not apply its 98.85% saving to first restoration,
the full discovery pipeline or arbitrary SAT expansion.

Persistent history grows by one probe-window row, from **770,338,816 to
770,347,008 bytes** in the measured reconstruction. There are still **41,758
pattern nodes**. The novel delta is **2,025 compressed bytes / 77,824 SQLite
bytes** (including its fixed schema). All five evidence lists remain unchanged,
with counts **(1, 42, 156, 11, 1)**; no former solver result is removed.

## Validation, limitations and next work

Seven new tests cover omitted historical states, matched clear prefixes, bounded
exhaustion, cold replay, idempotent merge, forced pending work, shared admissions,
malformed and missing prefixes, changed sources, denied scans/writes, authoritative
collisions, transaction rollback, nonempty working stores and corrupted deltas.
The complete relevant suite has **146 passing tests**. The checkpoint restoration
also independently reconstructs the old lineage, checks the new delta and compares
all logical table digests. Earlier positive proofs and artifact manifests remain
preserved. There is no new Lean refinement or unrestricted construction bound.

The preliminary `cnf-source-local/` run is retained with a note: its producer
mistakenly assigned the compression helper's empty return value as delta metadata.
It is not a resumable checkpoint, and its timings are not used above. The
corrected producer and independently verified checkpoint are under
`experiments/results/cnf-source-local-checked/`.

The next discovery task is to compare the retained split pairs with the next
ordinary block under a shared allowance. Extend source-local access to the exact
trace references and learned antecedents needed by those operations; their sidecar
membership and global selection are not covered by this ordinary-stream API.
First restoration now dominates this small operation. Batching useful advances
against a preserved authority could amortize it, but neither a minimum-cost
scheduler nor complete efficient classification of arbitrary CNFs follows.

## Reproduce and resume

Run `python3 experiments/continue_cnf_source_local.py OUTPUT_DIRECTORY` to repeat
the matched study. To restore the new complete checkpoint, use
`experiments.continue_cnf_source_local.restore_checkpoint` with
`experiments/results/cnf-source-local-checked/report.json`, a fresh SQLite output
path and a fresh temporary directory. It returns the checkpoint and all five
inherited evidence lists. This preserves the new window; restoring only the older
`cnf-reused-branch/report.json` would lose that latest acquisition from the active
working state. Old artifacts remain authoritative for their earlier checkpoints.
