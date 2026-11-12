# Clause-count admission permits bounded literal growth

The previous [subsumption experiment](subsumed-elimination.md) found a plain
clause-count-preserving elimination in 48 of its 59 remaining leaves. The earlier
rule rejected those steps because literal occurrences grew. This experiment
removes that second admission condition, keeping the same 64-candidate and
64-opposing-pair caps. Clause-count-based variable elimination is established SAT
preprocessing (Een and Biere, SAT 2005); the contribution here is a checked
integration, a conditional size proof and a retained resource comparison.

## Exact rule and persistence

`ClauseBoundEliminationInventory` first runs the existing joint clause/literal
non-growth policy. Only a null terminal proposal invokes the new fallback. It
keeps all non-tautological opposing-pair resolvents, removes exact duplicates,
and accepts a target with no more clauses than the source. It does not invoke
the more expensive retained-clause subsumption fallback. Candidate ranking still
prefers the smallest literal delta, then clause delta, pair count and variable.
Thus choices accepted by the previous local rule remain unchanged. Descendant
changes can nevertheless alter bounded parent selection; gains and losses are
both measured.

A certificate names the pivot. The independent checker reconstructs every
opposing pair from the actual source, validates clause count and strict variable
support decrease, and binds the complete target to its child. It never trusts
discovery's target or accounting. The existing exact existential-projection
identity applies unchanged; SAT lifting restores the pivot and checks the whole
source. A null proposal means unresolved, not UNSAT or exclusion from a class.
Separate configuration keys preserve previous results and failed alternatives.
Cold replay needs no discovery. No cross-source analysis cache is introduced.

Tests cover all 512 two-variable CNFs and every pivot, random six-variable
formulas, edits and signed 130-bit renamings, a four-clause 12-to-16-literal
projection, explicit clause-growth rejection, model/certificate corruption and
SQL replay. All 48 saved plain admission opportunities have a checked candidate;
that test is not a claim that any of their original roots closes.

## What Lean bounds, and what remains unproved

For normalized non-tautological clauses over n variables, each clause has width
at most n. A formula with at most m clauses therefore has at most mn literal
occurrences. Along an elimination-only chain starting with m0 clauses and n0
variables, clause count never increases and support strictly decreases. Hence:

- there are at most n0 accepted steps;
- every intermediate formula has at most m0*n0 literal occurrences;
- retaining all at most n0+1 formula states costs at most
  `(n0+1)*m0*n0` literal slots.

`ClauseBoundElimination.lean` proves these conditional counting statements. The
state-sequence normalization and size premises are explicit. It does not refine
Python, prove an acceptable next pivot exists, or bound the planner's other
branches, profiles, duplicated keys, separate inputs or final solver. Literal
slots are not bytes: original identifier sizes and their operations remain
charged. The full Lean audit passes at 4,195 declarations / 2,018 theorems.

Discovery pays the earlier failed policy first, then source validation and
occurrence indexing, O(n log n) candidate sorting, removed-clause accounting and
at most K*B opposing-pair constructions for K=B=64. With maximum width w,
removed-parent accounting costs at most O(K*L), and pair construction adds
O(K*B*w) expected container work. Independent checking rescans the source,
constructs at most B resolvents and sorts the complete target. These are logical
expected-container accounts, not constant-time hashing or bit-cost guarantees.
Every accepted child still reruns structural recognition. A bounded formula can
therefore be expensive to acquire repeatedly.

## Saved-leaf comparison

The inputs are the 59 final leaves from the preceding subsumption run, not its
initial frontier. Both modes start with empty history at conditioning depth zero.
The baseline closes zero; clause-count admission closes **one** (case 8).
Unresolved leaves fall from 59 to 58 and their literal total from 26,181 to 26,126.
The candidate obtains 95 new elimination edges, all increasing literal count,
plus three subsequent edges under the earlier rule. Consecutive elimination
chains have at most seven steps here; the maximum new target width is six.
These are structural closures, distinct from the independently checked SAT
answers of the unchanged ordinary solver.

Total query time grows **2.84076 -> 4.09001 seconds**, including discovery
**0.57939 -> 1.77437 seconds**. Complete database bytes grow
**17,518,592 -> 19,488,768**. Cold verification takes **1.06376 -> 1.61667 seconds**;
all bytes and ordinary residual evidence remain unchanged by replay. The new
95 edges have independently solved endpoints (63 SAT, 32 UNSAT), with SAT model
lifting, costing a further **5.35454 seconds**. Four-case peak Python allocation
rises **1,919,676 -> 2,719,945 bytes**. That sample excludes native SQLite, RSS
and the full history peak. Records, all archives and phase costs are preserved in
[the leaf comparison](../experiments/results/cnf-clause-bound-elimination-remaining/report.json).

The new fallback tests 5,810 candidates and rejects 5,627 for clause growth.
Only 95 new nodes are acquired, and only one leaf closes: available initial
pivots are much more common than useful complete chains. This selected,
one-order comparison establishes neither a general speedup nor default-policy
promotion. Whole-source recomposition and transfer are separate experiments.

An unresolved leaf after the chosen elimination order does not exclude a
successful order from the original formula. A short, polynomial-size chain is
an efficiently representable witness under these local size conditions, but
finding such a chain can still require exploring many choices. Neither the
current greedy ranking nor an efficient complete order search is proved to
reach a recognized terminal family on every input. Recognition of this stronger
structural class must not be confused with checking one proposed chain.

The fixed opposing-pair cap offers a separate, weaker size invariant for a
future policy. With cap B, any accepted step adds at most B clauses. At most n0
steps therefore keep clause count at most m0+B*n0, and normalized literal count
at most n0*(m0+B*n0), even when individual clause counts increase. This elementary
bound does not guarantee any admissible pivot and is not yet the implemented
admission rule or a Lean theorem in this extension. It suggests measuring a
small allowed clause increase before assuming that per-step clause non-growth
is necessary for polynomial formula size. Full discovery and retained history
still require their own bounds.

## Original-source recomposition

With the same paid 417,370,112-byte prefix and conditioning depth two, the new
policy closes **31/83** original prior misses versus **29/83**, losing none of
the baseline's closures. The two gains are cases 12 and 21 in this comparison,
original corpus indices **1058 and 1118**, in the `common_holdout3` and
`equivalence_holdout3` provenance groups respectively; both have 48 variables.
These are prior selected failures despite their historical group names, not
untouched holdouts. Selected unresolved leaves fall **59 -> 57**, and their
literal total **26,205 -> 25,488**. The 52 remaining original sources remain
unresolved by structural recognition.

Total query time increases **78.06321 -> 113.63899 seconds**; discovery accounts
for **76.41349 -> 111.88597 seconds**. The complete database grows
**621,146,112 -> 674,234,368 bytes**. Relative to the common paid prefix, added
bytes grow **203,776,000 -> 256,864,256**, about 26.05% more. Every prior source,
pattern and ordinary residual row survives, and the baseline exactly reproduces
the earlier bounded-elimination database. Cold verification costs
**79.31544 -> 93.78991 seconds**, with unchanged bytes. Four-source peak Python
allocation is **16,820,521 -> 16,028,812 bytes**; this limited sample does not
contradict the larger archive or establish a smaller full-history peak.

There are **2,504 new clause-count edges**, all with increasing literal count,
plus 2,777 earlier-rule edges. Both endpoints of all new edges are independently
solved: **1,493 SAT / 1,011 UNSAT**, with checked SAT model restoration. That
additional diagnostic costs **961.43125 seconds**. It uses the older
`ResidualSolver`, whose `archive_storage()` performs an SQL census after every
solve. The ordinary query path uses the already optimized
`AccountedResidualSolver`. No profile here isolates census time from solving;
do not attribute all diagnostic time to either one. This costly validation
phase is separate from query acquisition, not hidden in its timing.

Consecutive elimination chains reach 13 steps; new targets reach width eight.
All observed chains satisfy the clause/support/literal bounds. The new fallback
examines **166,437 candidates**, rejects **162,187** for clause growth and visits
**2,091,250 opposing pairs**. These counts include failed and unselected choices.
The full solver's answers, profiles, search counters and retained residual table
match; structural closure has improved, but actual SAT search has not changed.

[Complete records and archives](../experiments/results/cnf-clause-bound-elimination-originals/report.json)
preserve this coverage/cost trade-off. The candidate remains optional. These
results are not a fresh full-corpus run, a universal timing ratio, an optimal
elimination order or a polynomial arbitrary-SAT solution.

## Separate repeated controls

The 96-input control set reuses the published seed 202611091650 and generator
from the earlier binary-path study: random formulas, signed renamings, clause
edits and disjoint Horn mixtures with base sizes 12, 24 and 40 variables.
Mixtures append seven fresh variables. Its historical
`fresh_cases()` name does not make it an untouched holdout. This comparison
uses the same paid 417,370,112-byte prefix and conditioning depth two.

Both modes close exactly **88/96**, with no gained or lost closures. Query time
grows **8.90872 -> 10.48245 seconds** and database bytes
**453,582,848 -> 456,785,920**. Selected open literals fall **2,713 -> 2,682**, but
all eight open sources remain unresolved. All 130 new edges pass endpoint
checks (111 SAT, 19 UNSAT) and SAT lifting, separately costing **5.07637 seconds**.
Cold replay takes **49.42162 / 49.38030 seconds** without byte changes. No transfer
in structural closure is established by this control, and no full-corpus run
or default promotion follows. The order-reversed saved-leaf comparison is a
separate reproducibility check, not an independent new dataset.

## Reproducibility and next growth barrier

Reversing the two leaf modes reproduces each database exactly, with the same
one closure and no losses. Times again regress: **2.95454 -> 4.27301 seconds**.
This is an order control on the same inputs, not a new general timing estimate.

The [read-only final-frontier scan](../experiments/results/cnf-clause-bound-elimination-originals/growth-barriers.json)
reconstructs all pivot targets and separately records the actual runtime budgets.
Among the **57 remaining original-source leaves**, none admits the current plain
rule. **56** have a pair-bounded candidate. Their minimum clause increases are:
**32 leaves need one**, **18 need two**, **5 need three**, and **1 needs four**.
Thus **50/57** admit a candidate if up to two extra clauses are allowed. These
are opportunities, not additional closures or performance results. A retained
subclause omission would admit a non-growing candidate in 12/57; its integrated
cost and eventual usefulness remain untested with this new policy.

Only one leaf gains a plain non-growing pivot when the pair cap is removed.
It has 49 clauses, 11 variables and 283 literal occurrences; its cheapest such
candidates require 72 pairs rather than 64 and remove 16 clauses. Raising the
pair cap alone therefore misses the main current barrier. The all-pivot scan
and every margin are retained so a later run can distinguish this exception
from the 56 clause-growth cases.

The next ranked experiment is plain additive admission with a per-step clause
increase of at most one, then two, keeping complete checking, pair/candidate
caps and the earlier choices. A fixed allowance d also yields the elementary
chain bound m0+d*n0 clauses, without guaranteeing that a useful pivot exists.
Measure original-source gains/losses, the cost of repeatedly running structural
recognition, wider intermediates, checking, persistence and cold replay. Retain
the separate pair-cap exception and subsumption opportunities as controls. Do
not promote from candidate counts or optimize the diagnostic census as though
it were the main discovery cost. The current implementation and Lean theorem
remain the clause-count-non-growing version.
