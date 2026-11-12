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

The implementation and budgets were frozen in `b79c757`. Both runs preserve all
old coverage and acquire **no closed replacement**.

| Measurement | 83 selected originals | 96 repeated controls |
| --- | ---: | ---: |
| Structural closures before / after | 31 / 31 | 88 / 88 |
| New coupled trials | 25 | 15 |
| New recognition nodes | 32 | 17 |
| Maximum admitted states for one input | 11 | 6 |
| Inputs stopped by the 32-state cap | 0 | 0 |
| Resident expansion seconds | 0.62200 | 0.21175 |
| Seed verification seconds | 69.09120 | 5.80214 |
| Full cold audit seconds | 114.39522 | 51.43271 |
| Separate old/pair trial replay seconds | 69.81471 | 5.89978 |
| Seed database bytes | 760,606,720 | 468,971,520 |
| Expanded working database bytes | 761,499,648 | 469,438,464 |
| Delta SQLite bytes | 937,984 | 499,712 |
| Compressed delta bytes | 54,883 | 24,584 |

These are incremental single development runs from fully paid histories, not a
comparison with fresh solving. Restore, clone, export and reconstruction also
have separate report fields. Cold passes repeat some dependencies and are charged
in addition to resident expansion. The admission cap never binds here, so it does
not explain the negative coverage result or establish a measured runtime saving.

Only **18 of the 52 still-open originals** have a retained divergent first route.
There are 59 such routes; the four-route cap selects 55. Their second-step scan
constructs 2,008 candidate projections, rejects 1,839 for growth, and admits 169.
The interaction restriction removes 144, leaving **25** second pivots, all tested.
Another 122 candidate choices exceed the pair cap before construction. Repeated
controls admit 23 interacting second choices, with 15 new trials and eight exact
saved-trial hits. These counts expose the restrictions of the chosen search;
they do not exclude other routes, pairs or problem families.

## Novel paths mostly reuse known residuals

Relative to each retained first route, **17/25** original coupled trials have the
same selected unresolved leaf multiset. Of the eight changed frontiers, one has
fewer selected open literals and seven have more; none closes. **24/25** trials
end entirely in leaves already present somewhere in the seed. Nine immediate
target roots already exist there as well. The new nodes comprise 23 elimination
nodes, seven binary-path nodes, one probing node and only **one unresolved leaf**.

The repeated control reconverges with its first route in **11/15** trials. The
other four reduce selected open literals, but still do not close. All fifteen
frontiers use seed leaves; the seventeen new nodes are ten binary-path and seven
elimination nodes. Thus a residual novel relative to an original's selected
frontier need not be new to the accumulated history. The separate continuation
analysis records both distinctions and keeps exact variable bindings along paths.

## An explicit admission barrier in the newly exposed core

The sole new unresolved core has **35 variables, 150 clauses and 478 literals**.
Its full CNF and every inspected pair are preserved in
`experiments/results/cnf-coupled-pivots-originals/core-admission-audit.json`.
A separate read-only diagnostic removes the two-clause growth test while keeping
the 64-pair limit, reconstructing every resulting two-step projection. All variable
choices fit below the 64-candidate cap, so there is no candidate truncation here.

Of 35 first pivots, 30 meet the pair limit and all increase clause count by at
least **3**; five exceed the pair limit. The **662** permitted ordered pairs all
increase final clause count by at least **7**. Both minimum-growth orders use
noninteracting pivots 15 and 22. Interacting pairs grow by at least **15** clauses.
Independent enumeration confirms the first-pivot and ordered-pair sets.

Consequently, merely allowing temporary first-step growth while requiring final
growth at most four cannot unlock this core under the same pair cap. This is a
local obstruction to this representation and move rule, not a SAT lower bound.
No recognizer runs in this diagnostic and no new endpoint is asserted. A useful
next test is the least-cost escape (first-step growth three) followed by ordinary
simplification, with the admission cap retained. Wider interactions or a larger
net budget are separate hypotheses, not automatic consequences of two-step reuse.

If a future escape closes this new leaf, whole-source coverage must also propagate
through the saved alternative routes that led to it. The current `covered` call
uses old graph edges plus individually closed replacements; it does not compose
arbitrary open one-pivot and coupled records recursively. Such recomposition needs
its own checked finite justification before a local success becomes an original
gain. With zero closed replacements in this run, this limitation hides no claimed
new coverage.

## Validation and resumption

All **535 Python tests** pass, including exhaustive two-variable projection/lift
checks, descendant-budget interruption, completed-child preservation, restart,
saved-trial reuse and malformed bindings. Five-table delta roundtrip, idempotence
and conflict rejection also pass. Both complete histories pass cold verification
and separate old/coupled replay; emitted deltas reconstruct the recorded logical
tables and preserve every old row. New node identities are checked against the
per-input admitted-state fingerprints. The full test log retains SQLite
`ResourceWarning`s during garbage collection; an isolated run of the four new
tests with forced collection emitted none. They did not fail the suite. Formal
sources and manuscript are unchanged; no new Lean build is claimed.

The original history now has **41,331 pattern nodes**, 563 previous one-pivot
trials and **25 coupled trials**, with all 1,548 source bindings and 21,838 ordinary
solver proof rows intact. The repeated history has 24,999 pattern nodes, 65 old
trials, 15 coupled trials, 1,561 bindings and 23,116 ordinary solver rows. Endpoint
reference archives are empty initialized stores because there is no new closure.

To resume, use `restore_seed` from `compare_cnf_coupled_pivots.py` to reconstruct
the full frontier union, then apply this run's checked delta with
`apply_coupled_delta` (which includes the fifth table). Verify the archive hashes
and logical table digests in the report and validation record. Replay old trials
and `replay_coupled` before using their summaries. Preserve budget-stop logs and
continue with new budget scope rather than treating an interrupted attempt as a
permanent negative cache entry.
