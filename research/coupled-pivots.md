# Coupled pivot deviations with a recognition-state budget

The earlier pivot and ancestor schedules left original coverage at 31/83 and
repeated-control coverage at 88/96. Most new targets returned to known unresolved
cores. About 96% of constructed near-frontier candidates exceeded the unchanged
clause-growth allowance. This experiment tests a different continuation before
considering a larger allowance.

## Frozen experiment

Restore the complete union from the frontier study: all four prior proof deltas,
the original base, every failed trial, all source bindings and ordinary solver
proofs. On each still-open original, walk its selected open plan and find retained
first-pivot trials whose selected unresolved canonical leaf **multiset** differs
from their source's multiset. Rank these by change in selected open literal count,
then resulting literal count, distinct leaf count, source BFS rank and pivot.
Take at most four routes. The score is a heuristic, not semantic distance to a
tractable family or a guarantee of successful coverage.

For each selected first route, reconstruct its exact projected CNF in the original
source's variable coordinates. Generate second pivots under the existing 64-pair,
64-candidate and two-clause-growth limits. Retain second pivots sharing a source
clause with the first pivot; rank them by the existing syntactic family score.
This interaction restriction is a search heuristic and excludes no SAT class.
Round-robin over the selected routes, applying two consecutive projections
**before** invoking the unchanged recognizer. No growth limit is relaxed. Each
input admits at most eight new completed coupled trials.

An unresolved terminal can lack every admissible first elimination under these
caps. Two-step search cannot escape such a terminal if its first step must satisfy
the same cap. The present candidates therefore originate at retained earlier
divergent routes, not by assuming every terminal admits a move. A changed selected
frontier is not necessarily a globally unseen residual.

## Admission budget and persistence

A separate cap of **32 distinct newly entered recognizer states per open input**
applies before `_discover` runs, including every recursive descendant and unfinished
ancestor. The canonical identity retains source CNF, recognizer configuration and
remaining depth. Existing checked nodes can be loaded without spending a new-state
slot. The prepared-history view only checks stored nodes and does not discover.
Thus all new persisted recognition nodes fit within the admitted-state count.

If another state would exceed the cap, discovery stops for that input. No fake
child, closure summary or negative SAT result is emitted. Already completed
descendant certificates remain in the history; the stopped source and pivot pair
are logged for resumption. An unfinished parent's in-memory work is not itself a
certificate and may need recomputation. Tests exercise partial-child persistence,
restart, a zero budget and identity with uncapped completed certificates.

The budget does not bound candidate construction, prior graph checking, profile
cost per admitted state, the bytes in each state, or total process memory. Repeated
entries are counted separately; the experiment stops on the first denial for an
input. Counts of distinct new states are not a bound on total computation.

Completed coupled records bind the original source key, both pivots, the final
canonical target and variable map, and its checked summary. Replay reconstructs
both projections independently, checks the retained first route, and verifies the
final binding. A successful local replacement must still compose through the
original AND/conditioning/unary graph. Each projection is an exact existential
elimination; target models lift through the second step and then the first. The
existing elimination semantics compose, but no new Lean refinement or efficient
search theorem is claimed. Closure remains structural coverage, not a SAT verdict.

The new `cnf_coupled_trials_v1` table is separate from previous one-pivot trials.
All five tables are preserved and exported as an exact-base delta. Rebuild,
idempotence, complete cold audit and separate old/coupled trial replay are charged.
Any new closed replacement additionally receives an independent endpoint solve
and checked two-step model lift. Failed and budget-stopped work is retained.

## Results

The method and budgets above are fixed before running the selected original
inputs and repeated development control. Results will be recorded after checking.
