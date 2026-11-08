# Certified affine append, compact boundaries and persistent replay

Runtime checkpoint: `3b953b8`. This implements a restricted coefficient solver
using established affine elimination. It is not a new tractability claim or a
comparison with optimized SAT solvers. Historical timing evidence is unchanged.

## What is established

Every append adds a fresh width-`b` variable block. Its equations mention the old
and fresh boundaries. The preceding summary is lifted, conjoined with the new
batch, projected and compressed by Lean-certified coefficient operations.
`extend_exact` proves full boundary-solution equivalence; the `State` invariant
composes it over the original equation history. Positive and negative decisions
are exact, including histories that become contradictory after an append.

The current summary has at most `b+1` equations, or `(b+1)^2` logical coefficient
and right-hand-side cells. It is neither an assignment table nor a bound on
physical memory or all archived versions. `AffineCosts.lean` executes charged
loops, proves their outputs equal the semantic operations, and bounds an append
plus decision by `O(b^3+b^2*c)` for `c` new equations. The replay bound sums those
charges over history. Native returned decisions and charge fields have typed
state theorems. Charges cover whole-list pivot scans, produced row cells and
constant checks. Allocation, transport, persistence and machine execution remain
additional costs; `counted_complete=false` is explicit.

SQLite retains immutable original batches and prior results. Restarts reconstruct
summaries from original equations instead of trusting archived answers. Warm
appends use resident parent summaries. Native limits are widths 1..128, 4,096
equations per batch and 4,096 resident versions. A cap violation is an error.
The mathematical proof is not restricted to that fixed history cap.

## Verification and evidence

- **184 tests pass**, including **10 affine-growth tests**.
- The Lean audit passes **3,485 declarations / 1,708 theorem declarations**, with
  no admits or added axioms.
- Exhaustive sets check 135 random branching updates at widths 1..3. Independent
  full-system integer-bitset elimination checks larger cases through width 128.
- Other tests cover redundant/constant equations, contradictions, empty appends,
  immutable parents, poisoned cached answers, source corruption, replay, rollback,
  malformed native requests, and maximum native batch/version capacities.
- The archived study checks **272 decisions and 12 restart decisions** at widths
  2, 8, 32 and 64. All **284 agree** with elimination of the original systems.
  It retains **268 immutable versions**, including contradictory successors and
  unconstrained branches. Each principal chain has 64 appends.
- At 64 appends, the summaries have **6 / 72 / 1,056 / 4,160 cells**. The last
  append charges are **127 / 4,537 / 243,937 / 1,892,801**, below their respective
  budgets **178 / 4,912 / 248,488 / 1,910,088**. These are coefficient charges,
  not measured CPU instructions. The current query's wall/phase/transport records
  are separate; a warm query returns the saved version's acquisition charge.
- Each restarted principal chain reconstructs 65 versions. Its two branches then
  each register one additional version. Earlier equations are not discarded.
- All 355 old generic inputs pass revalidation/audit; five prior source versions
  pass adoption/restart. Every old row in 21 tables and all 222 earlier experiment
  files is unchanged, verified again after the affine run.
- The live archive holds **8,875 results, 2,967 refutations, 65 source-state rows
  and 268 affine-state rows**. The ignored SQLite backup is identified in the
  preservation report. Historical source-study validation checks 73 fingerprints
  and 1,824 stored outcomes; it does not rerun the historical executable.

`growth.json` includes source/engine identity and all recorded metrics.
`inputs.json.gz` retains the original content-addressed source nodes (55,176
compressed bytes); parent pointers reconstruct every tested system.
`verification.json` fingerprints 99 source/binary files. `preservation.json` and
`after-growth-preservation.json` check all prior rows and artifacts. Build/test
logs and manuscript proof-preservation/render checks are also retained.

## Remaining limits

Affine closure does not cover arbitrary CNF. The interface cannot edit older
interior blocks or mention forgotten variables; it has no full-history witness
output. JSON decoding and named-store histories, Python/SQLite correspondence,
complete native costs and physical memory bounds remain outside the algebraic
proof. The earlier general source-CNF operation-history theorem is still open.
Broader decomposition management, mixed CNF/XOR backdoors and a matched performance
comparison are follow-up tasks. Retaining and replaying history is charged, not
constant-space or constant-time.

The affine tractability is classical: Schaefer, *The complexity of satisfiability
problems* (STOC 1978), [DOI](https://doi.org/10.1145/800133.804350).
Chen's [Section 4 presentation](https://arxiv.org/html/cs/0611018) explicitly gives
linear-equation elimination. Our contribution here is the formal/runtime/persistent
implementation and accounting, without a theorem-novelty claim.
