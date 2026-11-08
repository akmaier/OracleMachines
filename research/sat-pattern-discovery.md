# Discovery and exact coverage of arbitrary CNF

Direction set by the user on 8 November 2026: prioritize discovering SAT patterns
and a valid partition covering the entire problem. Continue improving known
families as supporting work. This is a research plan, not an achieved efficient
partition or a new tractability theorem.

## What a valid partition must mean

The universe is all valid finite CNF encodings, including satisfiable and
unsatisfiable formulas. Invalid encodings are reported separately. Keep two
objects distinct: classification of whole formulas and decomposition of the
assignments/constraints of one formula. Splitting clauses into easy families
does not make their conjunction easy; shared-variable compatibility must remain
in the representation and cost account.

For whole-input classification, retain a versioned vector of deterministic
recognition outcomes rather than hiding overlapping patterns behind the first
successful recognizer. With outcomes in {recognized, excluded, unresolved},
the sets of inputs producing each outcome vector form disjoint cells covering
the universe. Empty cells can be omitted. "Excluded" requires a complete test
or a checked exclusion argument for the stated property; a budget stop or a
failed sufficient recognizer is "unresolved". Recognition-policy version,
deterministic work budget and any fixed seed or archive snapshot belong to the
cell definition. Wall-clock timing measures cost, not reproducible membership.
Cells describe recognition outcomes,
not necessarily the formula's full semantic class membership.

This supplies a bookkeeping partition immediately, but is not the research
achievement. The objective is to explain and progressively split its unresolved
cells using useful structural invariants and checked transformations. Reporting
only "known family versus everything else" does not meet the next milestone.
Overlapping class certificates remain available for alternative solver choices;
a routing priority must not erase them. Recognizers must terminate with an
explicit outcome, including when their search budget expires.

For decomposition within one formula, record exact source-linked residuals:

- Conditioning on x=false and x=true partitions assignments and combines by OR.
  UNSAT needs both branches unless another checked refutation already applies.
- Components on disjoint remaining variables combine by AND. Shared variables
  require an exact interface relation or conditioning before independent solving.
- A recognized residual can retain a family certificate and reuse operation.
  Unresolved residuals remain explicit and use the complete checked fallback.

These rules give semantic coverage, with no promise of a small decomposition.
The supplied strong-backdoor, scattered-class and component-depth literature in
[the existing analysis](arbitrary-sat-expansion.md) is the starting point. Read
primary sources before extending their results; retain their hypotheses.

## First milestone: an audited pattern inventory

**Implemented checkpoint:** the [664-input study](../experiments/results/cnf-pattern-inventory/README.md)
now records seven overlapping pattern outcomes, source bindings, independently
checked component partitions and bounded conditioning alternatives. It recognizes
the full direct encoding of one parity equation within a width cap. Two levels
explain 102/152 non-exhaustive inputs; 50 remain unresolved. Analysis adds time
and space and is not enabled as a solver optimization. The 24 observed root cells
are not a complete enumeration of all possible signatures. The next experiment
refines connected unresolved cells by exact clause support/sign patterns.

**Follow-up implemented:** [explicit affine extraction](../experiments/results/cnf-affine-patterns/README.md)
groups complete parity halves by support, retains every leftover clause, and
checks triangular GF(2) row operations. It recognizes direct overlapping affine
systems and inconsistent affine subsystems with couplings. New outcomes have
versioned identities; the previous inventory and archives remain valid. At depth
two, original non-tiny closure rises from 102/152 to 116/152. All eight seeded
gains come from unit/binary contradictions exposed by conditioning. Pure growing
affine cases close, but adding one binary coupling clause keeps four growing
controls unresolved. Their two-variable interfaces are the next target for
exact projection and composition, with checked witness lifting. General hidden
affine recognition and efficient arbitrary-CNF decomposition remain open.

The original acceptance criteria and remaining integration scope follow.

Build an analysis mode over the current residual solver. It should discover
patterns from CNF input without generator labels and preserve source identities.
The solver already has propagation, Horn/dual-Horn/2-CNF leaves, matching
recognition, independent components and exact variable splits. Instrument and
extend these capabilities rather than presenting them as absent or duplicating
their logic. The history adapters' whole-base restrictions are a separate gap.

Record, per formula and residual: all recognition outcomes; checked evidence;
connected components and shared interfaces; attempts at explicit equivalence,
parity and matching structure; discovered conditioning variables/depth; and the
size and structural profile of the unresolved part. Report measured or supplied
width bounds separately from an uncomputed optimum. Explicit XOR input is not
evidence that hidden parity in arbitrary CNF has been recognized.

Start with exhaustive normalized CNFs over two variables (including empty
formulas and empty clauses), then seeded larger samples and structured mixtures.
Include renamings, literal/clause reorderings, duplicates, redundant encodings,
connected mixtures, bridge clauses and the guarded arbitrary-CNF unit expansion.
Evaluate whole inputs and conditioned components. Compare to existing routing
on identical inputs; the corpus generator's label must not select the method.

Acceptance criteria:

1. Every valid input receives exactly one outcome-vector cell, with all applicable
   positive certificates retained and unresolved cases visible.
2. Exhaustive small cases check coverage, classifier consistency and exact
   branch/component recomposition against truth tables. Tests complement proofs;
   they do not establish universal coverage or complexity by themselves.
3. Report how much unresolved literal/residual work remains, new distinct
   residuals and certified reuse, not just total SAT successes or timing wins.
4. Charge discovery failures, certificate verification, preprocessing, memory,
   updates, serialization, persistence and cold replay. Preserve regressions.
5. Save counterexamples that expose missing patterns or invalid combinations.
   Repeated restarts should reuse these results rather than rediscover them.

## Following iterations

First split the largest informative unresolved cells. Favor discoveries that
transfer across several families: component-local recognition, shared-variable
interaction, and conditioning that reveals different tractable classes in
different branches. Then investigate canonical descriptions and checked transports
that let equivalent discovered structures share state across histories.

Test edits that preserve a certificate and edits that invalidate it. A bridge
clause can merge components; a unit can expose an arbitrary guarded CNF. Preserve
old results while rebuilding only the affected valid dependency closure.

Choose each iteration by likely expansion of certified structural coverage and
reduction of unresolved interaction, with discovery and total cost measured.
Propagation queues, dense-posting compression and known-family speedups remain
useful, especially when they enable the discovery experiment; they no longer
automatically outrank discovery merely because a synthetic case is expensive.

The remaining universal question is whether all inputs admit useful states and
updates with uniform construction, size and evaluation bounds. An exhaustive
partition, small-case coverage or inexpensive updates after unbounded preparation
does not settle it. Keep the cost of the prepared oracle explicit.
