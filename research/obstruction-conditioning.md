# Conditioning from checked renaming obstructions

9 November 2026. This experiment tests the top remaining discovery gap after
terminal Horn renaming: can a source-linked exclusion certificate guide better
conditioning? The implemented heuristic is optional and **not promoted**. At the
same budgets it gains three frontier leaves but loses six, with higher discovery
cost. The failed direction and its reusable counterexamples remain preserved.

## Exact information supplied by an obstruction

Let W be the set of original clauses used by the two checked auxiliary implication
paths, and let U contain every variable in those clauses. If a partial assignment
has domain disjoint from U, every clause in W remains unchanged under **raw
restriction**. Its original pairs and contradiction paths remain present. Therefore
the raw restricted CNF still cannot be made Horn by polarity renaming.

This follows directly: none of those clauses can be satisfied or lose a literal
when none of its variables is assigned; the checked contradiction is a subformula
of the new auxiliary pair constraints. A Horn renaming would satisfy this
contradictory subformula, which is impossible.

The condition concerns raw restriction and this one syntactic class. It does not
license pruning variables outside U. Subsequent propagation can reach U; another
family can close a residual; a conflict elsewhere can let normalization collapse
the formula to terminal false. Neither an auxiliary contradiction nor surviving
class obstruction is a general SAT/UNSAT verdict.

Full source-clause supports matter, not only the two positions named by each
edge. Guard every clause of the four-pair obstruction on variables 1 and 2 by a
positive variable 3. The same auxiliary paths use only positions for 1 and 2,
but setting 3 true deletes every source clause. The test fixture preserves this
counterexample to endpoint-only reasoning.

## Implemented optional policy

`ObstructionChoicesInventory` extends the current `PolarityHornInventory` with
`conditioning_obstruction=balanced-source-path-v1` in its configuration and keys.
It constructs and checks one auxiliary certificate only when the existing planner
actually conditions. For an exclusion, it deduplicates the source clause IDs from
both paths, counts positive and negative occurrences for each variable, and ranks
by their product, then their sum. Exact ties retain the old shortest-balanced
ranking. The existing candidate cap remains four; every chosen variable still
has both branches checked. A positive or capped auxiliary result uses the old
ranking. No class outcome is converted into a SAT answer.

Each OR node stores its source-bound certificate. The independent checker replays
that certificate, reconstructs the same ranking and verifies every attempted
branch and selection. It never reruns auxiliary SCC discovery. Invocation-scoped
state restores the parent's context after child acquisition and on exceptions;
no new cross-source proof cache is introduced. Earlier reductions, recognizers,
terminal renaming and probe budgets retain their behavior. Changing the candidate
set can lose a bounded closure, so this policy does not replace the baseline.

## Resource account

Write m,L,v,Q for clauses, literal occurrences, variables and pair constraints,
p for supplied path length, c for distinct cited source clauses and L_W for their
literal occurrences. New auxiliary discovery adds the existing conditional
O(m+L+Q+v log(v+1)) word/comparison bound, subject to the 65,536-pair cap. Ranking
and independent replay add O(m+L+p+c log(c+1)+v log(v+1)) work, including the old
ranking, source checks and L_W<=L score visits. Extra counters and exact context
comparison are charged. Long integers, hash behavior and bit costs remain explicit.

Generated auxiliary paths have O(v) edges, so their source-coordinate certificates
have O(v) entries. The full pair formula is transient. Stored graphs still include
original CNFs, failed alternatives, child keys and full source bindings. Distinct
policy keys preserve old results but duplicate some state between policies.
Whole-planner acquisition and memory need bounds on all acquired alternatives;
this local ranking gives no such bound for arbitrary SAT.

## Matched outcome and why the ranking fails

The [complete frontier study](../experiments/results/cnf-obstruction-frontier/README.md)
gives each of the 106 previously exhausted leaves **one additional conditioning
level in both modes**, with four candidate/probe/learning limits. This is not a
new whole-source coverage result. Baseline closure is 60/106; obstruction ranking
is 57/106. Three gains and six losses are retained. Discovery increases 4.96403 ->
5.21714 s (5.10%), fresh SQLite 35,840,000 -> 37,498,880 bytes, and cold replay
3.49873 -> 3.53507 s. The unchanged solver varies in the opposite direction,
leaving total time essentially flat. The small allocation subset falls slightly;
that is not a full-process memory improvement.

All six lost winning variables disappear from the new four-candidate set. Five
lie outside the source support of the particular saved obstruction. Thus a single
refutation is a poor complete model of useful structural interactions.

A separate diagnostic reuses **only existing original-pass probe certificates**.
It independently checks them against the restricted source, using parent variable
names and preserving their reason indices. For frontier case 4, the old successful
variable 6 is outside the obstruction support {1,4,5,9,10,11,13}. Its false probe
forces 10=false and 5=true, damaging three of the four saved auxiliary edges.
Its true probe forces 7=false, then 1=true and 8=true, damaging all four. Direct
conditioning on 6 damages none. This explains an indirect interaction that the
source-only score misses without doing any fresh propagation.

This explanation is deliberately limited. The old winning variables for cases
17 and 50 also have saved original probes, but those traces damage none of the
recorded edges. Their later checked discovery still closes both branches. Other
lost winners and all three new winners lack original-pass probe traces. Missing
traces are unknown, not proof of no influence. Damaging one saved path is also
not proof that all renaming obstructions disappear.

## Next experiment and retained limits

Test whether already-checked propagation consequences improve candidate choices
across classes at the same budgets, preserving a channel for the baseline choices.
Measure which cases have such reusable evidence before spending on new lookahead.
Include cases 17 and 50 so that fixing case 4 is not mistaken for a general solution.
The two policies' closure union is 63/106, but replaying both searches has extra
cost and is not an implemented efficient portfolio. Portable reuse of successful
plans across policy identities remains a separate useful storage/acquisition gap.

All 448 Python tests pass, including the seven added tests for saved frontier
certificates, guarded supports, raw-restriction persistence, exhaustive tiny and
random tree/model checks, capped fallback, old-row coexistence, cold checks with
SCC discovery disabled, corruption rejection and context restoration. Existing
Lean conditioning/model-transport lemmas justify the unchanged semantic branching
rule. Lean sources are unchanged; this heuristic has no new formal refinement or
unrestricted tractability claim.
