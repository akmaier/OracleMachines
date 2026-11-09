# Reusing original probe effects without discarding candidates

9 November 2026. The optional `ProbeRankInventory` tests the next idea after
obstruction-only ranking: use already-proved propagation effects while retaining
every baseline conditioning candidate. **Do not promote this policy.** It keeps
coverage, but the two reversed-order frontier runs regress in discovery and total
time. Fresh controls expose a more useful limitation: most branching states have
no original probe information to rank.

## Policy and evidence binding

Start with the same capped shortest-balanced candidate list. Read only original
probe attempts in that source's `clear` or `learning_clear` profile. For each
candidate measured under both Boolean assumptions, count its additional propagated
variables, u0 and u1. Among those with both counts positive, maximize
`(min(u0,u1), u0+u1)`, breaking ties by the old order. Move the winner to the front;
retain the relative order of every other candidate. No eligible candidate means
the old order. Missing traces are unknown, not measured zero effects.

The helper `choices_after_checked_probes` is internal, **not a proof checker**.
During discovery the original traces have just been generated. Before replay
reconstructs an order, the inherited checker independently verifies every trace
against the exact restricted original source, including reasons and fixed points.
Original unit variables use parent names. Learned continuations are excluded:
they refer to an augmented source and cannot silently replace original proofs.
The original profile already persists every reused trace, so ranking stores no
new unit certificate. Scopes restore the parent's profile after nested acquisition
and exceptions; edited sources and different policies have separate exact keys.

## What can be proved

For a finite candidate set V, structural closure by conditioning is
`OR(v in V, closed(v=false) AND closed(v=true))`. A permutation preserves that
expression if corresponding child closure outcomes agree. Stopping at the first
true term or after exhausting V implements the same expression. The argument
extends over a finite expansion with unchanged reductions, component composition,
per-child budgets and candidate sets. There must be no timeout or shared work
budget that expires differently, or history-dependent change in recognition.

`promote_existing_candidate_membership` in `Residuals.lean` proves that promoting
an existing member preserves membership. `conditioning_pool_closure_invariant`
proves the local closure equivalence under explicit candidate/child hypotheses.
These are not an end-to-end Python refinement. Recursive correspondence, source
normalization, database operations and costs are separate obligations. The result
does not preserve the chosen proof graph, acquisition order, runtime or the
minimum-cost plan. It cannot broaden coverage of a fixed candidate pool.

## Matched results

See the [frontier report](../experiments/results/cnf-probe-rank-frontier/README.md)
and [fresh report](../experiments/results/cnf-probe-rank-fresh/README.md). Each suite
has two runs with execution order reversed, the frozen policy and identical
depth/candidate/probe/learning budgets. Frontier inputs receive one extra split in
both modes; their closure counts are not new original-source coverage.

| Mean or exact measure | Frontier baseline | Probe ranking | Fresh baseline | Probe ranking |
| --- | ---: | ---: | ---: | ---: |
| Structural closure | 60/106 | 60/106 | 71/96 | 71/96 |
| Discovery/checking/persistence (s) | 5.19854 | 5.44908 | 1.78113 | 1.79121 |
| Total with ordinary solver/lifts (s) | 8.22342 | 8.63390 | 3.07464 | 3.07502 |
| Cold complete replay (s) | 3.49969 | 3.58164 | 1.21814 | 1.21632 |
| Warm inventory replay (s) | 0.02719 | 0.02793 | 0.02476 | 0.02512 |
| SQLite bytes | 35,840,000 | 35,979,264 | 15,417,344 | 15,585,280 |
| Pattern nodes | 1,540 | 1,524 | 684 | 684 |
| Conditioning attempts | 268 | 268 | 101 | 101 |

Frontier discovery regresses 4.82% and total 4.99% on the two-run means. Ordinary
solver variation contributes to total; two samples establish no significance.
Twenty-six of 106 distinct OR states change order. Both policies keep the same
54 selected unresolved leaves and 13,755 literal occurrences. Cases 4, 17 and 50
retain their earlier closures; replacing candidates was avoided. Reduced node
count does not imply reduced bytes: repeated policy configuration in exact keys
outweighs these small graph savings. Old archives remain retained.

Fresh cases were fixed before viewing their results: seed 202611091730, variables
12/24/40, random 3-CNF or mixed 2/3-CNF, signed permutations, clause edits and
disjoint Horn mixtures. Means are effectively unchanged; the first and reversed
runs disagree on the sign of the small timing difference. No candidate order
changes, all 684 nodes' kinds agree, and extra policy-key bytes increase storage.
This is synthetic evidence, not industrial transfer or full-process memory data.

## Cost of the ranking and the remaining information gap

Beyond the old ranking, the helper makes an O(p) table of original attempt lengths,
then scans c candidates, using O(p+c) transient entries. Python list lengths are
constant-time; units are not rescanned or re-propagated. The exact-source context
comparison can cost O(L), so a conservative extra bound is O(L+p+c) word work.
This assumes ordinary hash-table behavior and bounded-cost integer operations;
bit costs and total recursive acquisition remain separate. There is no new
retained proof cache. The changed policy string occurs in persisted node/source
keys and references; those serialization and storage costs are charged.

The diagnostic counts **282 measured and 142 unknown** candidate positions in
the frontier, but only **9 measured and 147 unknown** in fresh OR states. Of the
39 fresh OR states, **36 have no binary clauses**. Operation counters include
discovery and checking; `mechanisms.json` counts each acquired OR state once.

For a normalized formula with at least three distinct variables per clause, assigning
one variable either satisfies a clause or removes at most one literal. Every
surviving clause still has width at least two. Unit propagation therefore cannot
start from this single assumption. This is an elementary limitation of this
specific evidence, not of all look-ahead or all SAT algorithms. The current
binary-occurrence probe selector supplies no attempts for such states. Assigning
two variables can create a unit, and one assignment can expose informative
binary relations even without units.

The next coverage target is a **bounded two-variable interface or newly exposed
binary relation**, with exact branch recomposition and charged recognition cost.
Choose it from unresolved states rather than tuning another scalar unit-count
score. Successful structural plans should also become portable across policy
identities: the older two-policy closure union remains 63/106, but acquiring both
policies is extra work. For runtime, direct reuse of original unit proofs at a
conditioning edge needs explicit normalization, clause-index and variable transport;
a ranking proxy does not perform that reuse. None of these improvements is yet
implemented or promises a small interface for arbitrary SAT.

## Validation

All 453 Python tests pass. Five added tests cover metadata ordering/unknowns,
all 106 frontier closures, 512 tiny and 80 fresh edited/signed tree/model checks,
cold replay with discovery disabled, corruption, old-row coexistence and nested
context restoration. All eight measured archives cold-check every node, source
and ordinary solver certificate without changing bytes; warm replay inserts no
rows. Archives are identical between execution orders for each policy/suite.
Reports retain input cases, per-query metrics, regressions, fingerprints, complete
archives and allocation subsets. Four-case traced allocations exclude native
SQLite, RSS and full-corpus peak. Loading, summary walks, hashing and compression
are outside acquisition timers; initialization, cold and warm replay are separate.
The optional policy leaves the original 898/985 baseline unchanged.

The complete Lean build and axiom audit pass: **4,140 namespace declarations /
1,981 theorem declarations**, allowing only the existing standard Lean axioms.
