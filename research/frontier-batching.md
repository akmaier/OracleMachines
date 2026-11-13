# Bounded batching of retained frontier probes

This continuation starts from the forced-frontier checkpoint and investigates
repeated preparation around small expansion steps. It uses the same search
implementation in both arms: at most eight advances, four distinct sources and
one shared allowance of 32 recognition states. The allowance is not reset
between steps or sources. An exhausted source consumes an advance and remains
unresolved unless another checked route closes it.

## Discovery and exact reuse

The selected open leaf of case 30 has 25 variables, 99 clauses and 304 literal
occurrences. All 17 remaining ordinary candidates are clear. Five new blocks at
offsets 0, 4, 8, 12 and 16 retain 34 checked assumption traces. A sixth advance
finds the pool exhausted. No recognition state is acquired, no pending child is
created, and structural coverage stays at 58/83, also without growth exceptions.
The four earlier pairs and 17 new pairs remain available for exact conditioning.
These are reused development inputs, not an independent holdout.

A clear failed-literal test is inconclusive: it supplies neither a SAT model nor
a refutation. It does supply checked unit propagation for the two restrictions,
which the saved-cofactor route can reference without rediscovering those traces.
Both cofactors must have complete recognition plans to close this structural
obligation. The older ancestor already has an empty cofactor witnessing SAT;
completing this open descendant addresses the stronger decomposition objective.

## Next structural option and excluded repetition

Ranking all 21 checked pairs takes **0.04304 s** in independent replay and
selects normalized **variable 7**, with rank **[1, 1, 24, 287, 7]**: one uncovered
child, one missing child, maximum support 24, and 287 cofactor literal occurrences.
Its true cofactor reuses the existing empty-CNF terminal. Its false cofactor has
**24 variables / 94 clauses / 287 literals** and remains unacquired. Before this
batch, the best saved rank was **[2, 2, 23, 422, 5]**, requiring two new children.
These heuristic ranks do not compare the actual acquisition costs of the plans.

Variable 7's two references are indices 4 and 5 in the **first new window**.
It was therefore available before the other four continuation blocks. Pool
exhaustion was unnecessary to select it. A useful next scheduler should check
for cheap retained cofactors between blocks while retaining a shared budget;
a fixed eight-step cap alone does not minimize discovery work. All extra clear
results remain useful evidence and are preserved, rather than hidden as free work.

The pair scan finds **no common-value or equivalence rewrite** under the current
checker (110 unit visits for each scan). The four unprobed variables **2, 4, 12,
21** occur in no binary clause. The source is unit-free, and each of their two
restrictions still has minimum clause width two. Thus unit propagation has no
initial unit and cannot produce a conflict on those restrictions. This explains
why repeating this particular failed-literal test on those variables cannot
help; it does not exclude useful conditioning on them or stronger reasoning.
The checks and exact source identity are retained in `frontier-profiles.json.gz`.

## Matched preparation control

`cnf_probe_batch_control.ObservedRoutes` wraps the existing `cnf_target_probe.search`.
The batch keeps its checked routes across advances. The sequential preparation
control rebuilds them before each subsequent advance, retaining the inventory's
warm verifier cache, search queue, visited-source set and admission allowance.
It also recomposes the same original roots after each rebuild. Thus the control
measures repeated checked-route preparation; it does not model restarting the
entire process, reloading the history, or rerunning a full audit after each step.

Both arms record every step's accumulated probe-record hash, admitted state
identities and payload hashes, and original-root coverage. The experiment
requires equal visits, all six equal prefixes, equal admissions, equal final
logical tables and equal final coverage. The final immutable delta preserves
all old rows. A single full audit checks the resulting history; cold replay
independently checks the certificates with fresh discovery disabled.

The cost comparison includes initial preparation and instrumented search in
each arm. Prefix snapshots and coverage composition are included in those search
timings and recorded separately. The experimental pipeline additionally charges
restoration, both arms, delta export, full audit, cold routes and reference replay.
Its elapsed time is not a standalone batch production time. There is one
batch-first measurement, without randomized order or a confidence interval.
No claim about competitive SAT-solver speed, peak RAM or polynomial expansion
follows from avoiding redundant preparation.

## Measured cost and retention

| Scope | Batch (s) | Sequential preparation control (s) |
|---|---:|---:|
| Initial history copy, checked routes and root composition | 65.62419 | 70.54924 |
| Instrumented search | 0.31960 | 5.46878 |
| Of search: six prefix snapshots and compositions | 0.30190 | 0.30159 |
| Of search: five repeated route preparations | 0 | 5.14561 |
| Initial preparation plus instrumented search | **65.94379** | **76.01801** |

The directly measured avoided work is **5.14561 s** of repeated preparation.
Initial preparation differs by 4.92505 s between the single-run arms; that
variation is not an established batching benefit. The small search-only ratio
would greatly overstate a complete-solver improvement. No statistically supported
end-to-end speedup is claimed.

The full experimental pipeline takes **358.12190 s**, including both arms. Parent
restoration takes 19.75650 s, selection/ranking 0.02231 s, composition/diagnostics
0.15240 s, delta export 5.39775 s, the full audit **111.99494 s**, and cold route
reconstruction **66.03018 s**. Remaining I/O and reference replay are included in
the pipeline; reference cold replay takes 0.75132 s. Independent validation and
manuscript compilation are additional. Cold preparation and checking remain the
dominant costs, even though the inner pass now shares its prepared state. The retained
positive coverage witness contains only **593 explicit steps for 58 roots**,
compared with 41,755 archive pattern nodes. This is a concrete starting point for
a dependency-local verifier, not a bound on its required closure: base certificates,
prepared histories and referenced probe-prefix records can add dependencies.
A selective checker must validate those bindings and premises before accepting
a plan; merely loading 593 records would not establish correctness.

SQLite grows **53,248 bytes** to **770,289,664 bytes**. It retains the same
**41,755 pattern nodes**, adding one ordinary window and four continuations
(**91 / 133** rows now). The immutable delta is **118,784 raw / 2,990 compressed
bytes**. Prefix, selection and diagnostic archives are additional. All **1,977**
reference nodes survive, with the reference snapshot byte-identical to its
parent (14,667,776 raw / 968,187 compressed bytes). No new reference solve is
needed for these clear records. Peak RAM is unmeasured.

## Continuation and limitations

Resume `experiments/results/cnf-frontier-batch/report.json` through
`continue_cnf_frontier_batch.restore_checkpoint` and `routes_for`. Preserve all
five evidence lists (1 rewrite, 42 learned bases, 156 augmented blocks, 10 splits,
1 affine family), together with earlier sidecars. The new records are ordinary
SQLite probe rows; they do not alter those five sidecar lists.

Do not rerun ordinary probing on this exhausted source. Use the retained
variable-7 pair and acquire its missing false cofactor under a shared allowance,
or compare another applicable inference. Exhaustion of this fixed probe policy is
not exhaustion of SAT reasoning. The alternative learning queue still retains
17 ready bases and 88 candidates. Dependency-local checking of complete positive
plans remains the larger verification gap: batching avoids repeated preparation
inside one pass but does not remove the initial global preparation or cold audit.

The 37 targeted tests include matching uninstrumented, batched and sequential
search on clear exhaustion, forced acquisition and interrupted acquisition, and
reject a route rebuild that replaces the shared allowance. These supplement the
existing continuation, split, composition and affine-route tests. Independent
cold replay passes in **169.35837 s**, with fresh discovery
disabled, all five evidence lists preserved and unchanged reconstructed bytes.
No new Lean refinement or unrestricted complexity theorem is claimed.
