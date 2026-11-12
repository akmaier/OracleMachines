# Checked variable elimination at unresolved leaves

The earlier cache experiments reduced individual operations without reducing
total cost. This follow-up changes the structural representation itself. It
tries bounded Davis-Putnam elimination after the current planner leaves a source
unresolved. The rule is established preprocessing, not a new SAT class:
[Een and Biere (SAT 2005)](https://fmv.jku.at/papers/EenBiere-SAT05.pdf) describe
variable elimination with growth limits, and the
[Handbook preprocessing chapter](https://fmv.jku.at/papers/BiereJarvisaloKiesl-SAT-Handbook-2021-Preprocessing-Chapter-Manuscript.pdf)
discusses model reconstruction and the limits of inferring solver speed from
formula reduction. Our contribution here is the checked integration, retained
evidence and resource measurements in this repository's structural inventory.

## Exact projection and model restoration

Write a normalized source as unaffected clauses R, positive clauses
`x OR P_i`, and negative clauses `NOT x OR N_j`. Remove all clauses mentioning x
and retain R together with every non-tautological resolvent `P_i OR N_j`.
Exact duplicate resolvents and copies already in R need occur only once.
For every assignment to the other variables, the resulting formula holds if
and only if some Boolean value of x makes the original formula hold. This is
existential projection, not logical equivalence over all original variables.

Forward soundness follows because a source model satisfies each resolvent.
For the converse, if all positive tails hold, set x=false. Otherwise an
unsatisfied positive tail forces every negative tail to hold, since all opposing
pairs were retained; set x=true. Thus either choice preserves the unaffected
clauses and satisfies every deleted clause. Omitting an unaccounted opposing
pair can break this argument. The regression suite retains an explicit example
where an incomplete resolvent set has a model with no extension to the source.

`formal/OracleMachines/VariableElimination.lean` proves this exact equivalence
for explicit CNF lists and a valuation updated at x. The theorem requires that
the retained clauses and both tail lists do not contain x. It also proves the
source and projected-CNF semantic decompositions. The current axiom audit passes
4,168 declarations / 2,004 theorem declarations. These Lean results do not refine
the Python parser, normalization, tautology/duplicate removal, scheduling,
persistence or resource counters. Those remain separately tested obligations.

## Checked integration and reuse conditions

`VariableEliminationInventory` extends the optional prepared-probe policy. It
only intervenes when the previous planner would retain an unresolved terminal
node. Existing family closures, failed alternatives and other proof obligations
remain intact. The policy has a separate persistent configuration identity.

Discovery builds occurrence lists and considers up to 64 variables, ordered by
opposing-pair count and variable name. Each candidate has at most 64 opposing
pairs. A step is admitted only when neither clause count nor literal-occurrence
count increases, after tautology removal and exact deduplication. Discovery
chooses the largest literal reduction, breaking ties by clause reduction, pair
count and variable name. Rejected or unexamined candidates remain unresolved;
the proposal makes no assertion that all possible eliminations were excluded.

The certificate stores one variable. The checker independently reads the actual
source, partitions its clauses, enumerates every opposing pair, reconstructs
the complete target and checks both growth bounds. It uses no discovery index
or trusted proposed residual. The normal edge checker binds the exact normalized
target, names and depth. Every accepted step removes its variable, so repeated
eliminations on one path terminate. Other recognizers run on the resulting core;
any unresolved child remains explicit. Pure-only elimination is a separate
control with pair limit zero, not credited as a mixed-polarity discovery gain.

Lifting checks a complete Boolean model for the child support, reverses its
canonical variable names, fills other now-irrelevant source variables, and chooses
x by the positive-tail test above. It finally checks every source clause. SAT
and UNSAT equivalence follow from the projection rule; structural closure alone
still supplies neither verdict. The unchanged ordinary residual solver continues
to decide the original input in the comparisons.

Exact target keys can reuse an already stored core with the same remaining depth
and configuration. Equivalent formulas with different canonical syntax do not
automatically share a core. Original source records and elimination nodes remain
durable. A source edit has a different binding and must be checked again, including
all new clauses involving x. One cannot simply append such clauses to an old
projected target and assume that its eliminated variables remain unconstrained.

## Resource obligations

Let L and m be source literal occurrences and clauses, n its variable count,
K the candidate cap, B the opposing-pair cap, and w the largest source width.
Source validation/indexing costs O(L) expected set/dictionary work, and ordering
costs O(n log n). Each candidate processes at most B pairs of tails of width at
most w, including unions, tautology and duplicate checks. Thus candidate work is
O(K B w) expected set work, plus source occurrence accounting. In this Python
implementation, the removed-clause size sums across candidates can cost O(K L).
The independent checker additionally rescans the source, builds and sorts the
complete target. Sorting, tuple hashing/comparison, integer bit sizes and Python
container overhead must be charged; these expressions are not bit-complexity or
constant-time hash guarantees.

Each accepted step reduces variable count and never increases m or L. A chain
therefore has at most the original n elimination steps. These local bounds do
not force an elimination to exist or make the remaining core easy. Recognition,
other transformations, conditioning branches and the ordinary fallback retain
their own costs. The recursive Python inventory is not a stack-safe implementation
for arbitrary elimination-chain lengths.

Live occurrence lists, clauses and candidate resolvents take O(L + B w) logical
slots per active step, apart from sorting containers and the other graph caches.
The full checker can transiently hold the source and target. The retained proof
node still contains source/profile copies and a child key, while the child adds
its own checked node. A one-variable certificate is not a constant-size total
proof. Historical archive growth and decoded graph memory can therefore increase
even when every transformed CNF shrinks. Cold replay must reconstruct and verify
all retained transformations; this cost is measured separately.

## Selected-frontier evidence

The read-only opportunity probe extracts the 99 selected unresolved leaves of
the earlier prepared corpus, associated with 83 original inputs and 31,203
literal occurrences. Within the 64-pair cap, 81 leaves have a non-growing
candidate. Seventy-one admit a candidate occurring in both polarities, 55 admit
a pure variable, and 10 admit only pure candidates. These sets overlap and are
not a partition into tractable semantic classes.

The matched 99-leaf comparison starts with empty history and conditioning depth
zero. Baseline / pure-only / bounded elimination close **0 / 14 / 37** leaves,
respectively. The bounded result contains 35 satisfiable and 2 unsatisfiable
closed leaves, as independently decided on the original CNFs. No open leaf is
labelled UNSAT. Selected unresolved literal totals are **31,203 / 29,164 / 27,130**.
Every source/model decision is preserved. All 163 pure-only and 379 bounded
elimination edges have both endpoints independently solved; SAT child models are
lifted and checked against their sources. All three complete archives pass cold
audit without modification.

This coverage costs more on the isolated leaves. Total query seconds are
**3.21234 / 3.83297 / 4.97015**, and database bytes are
**20,000,768 / 22,454,272 / 26,185,728**. The unchanged ordinary solver is included
in those totals. Four-case peak traced Python allocation is
**718,814 / 1,344,096 / 1,923,674 bytes**; this excludes native SQLite, process RSS
and full-history peak. These are single ordered synthetic comparisons, not a
general speed claim. Leaf closures alone do not determine how many original
inputs now close or how much earlier conditioning work is avoided.

See the complete
[frontier evidence](../experiments/results/cnf-variable-elimination-frontier/README.md).
The full 501-test Python suite passes, including exhaustive two-variable
existential checks, randomized edits and large identifiers, growth/cap failures,
corruption rejection, model lifting and byte-preserving restart. No uniformly
polynomial solution or efficient partition covering every CNF is established.

## Whole original inputs and paid preparation

A separate matched run starts each mode from the same 417,370,112-byte prepared
prefix and queries the 83 original sources that were unresolved in the previous
full run. It keeps conditioning depth two and the previous probe/learning limits.
This tests actual source recomposition rather than extrapolating the leaf counts.
The prefix represents prior paid acquisition; its restoration, cloning, opening,
checking and retention remain explicit liabilities.

| Acquisition measurement | Baseline | Pure-only | Bounded |
| --- | ---: | ---: | ---: |
| Newly closed original sources | 0 | 11 | 29 |
| Remaining open original sources | 83 | 72 | 54 |
| Selected open leaves | 99 | 84 | 59 |
| Selected open literals | 31,203 | 28,653 | 26,205 |
| Discovery seconds | 62.92410 | 70.27491 | 78.27921 |
| Total query seconds | 64.76503 | 71.86221 | 80.09857 |
| Complete database bytes | 605,675,520 | 627,138,560 | 621,146,112 |
| Cold audit seconds | 73.18420 | 77.08544 | 79.28780 |
| Four-source peak Python bytes | 20,284,653 | 21,098,539 | 16,819,577 |

The bounded candidate retains every pure-only closure and adds 18 original-source
closures beyond that control. It broadens certified structural coverage while
running slower overall on this matched subset. The smaller final archive than
pure-only does not make it smaller than baseline. The ordinary solver still
decides the original CNFs with identical search counters in all three modes.
These measurements do not establish cheaper arbitrary-SAT decision or expansion.

The new candidate tries 167,129 elimination candidates and rejects 156,757 for
growth, visiting 1,457,523 opposing pairs during discovery. It acquires 2,822
elimination nodes. Thus failed candidate analysis is an explicit next cost to
profile, including whether unchanged occurrence neighborhoods could reuse earlier
analyses. Such reuse must also track the retained clauses that make a resolvent
an exact duplicate; unchanged pivot occurrences alone are not a sufficient
invalidation condition. A new retained clause can change the growth decision.

The [whole-input record](../experiments/results/cnf-variable-elimination-originals/README.md)
retains per-query evidence, complete archives and separate cold/model checks.
The previous 902/985 full-corpus result remains historical. The new measurement
covers its 83 misses only; it is not a new run of all 1,497 cases, an independent
holdout, or a promotion to the default policy. The 54 remaining sources and the
cost of recognizing useful transformations are the next obligations.

All six archives pass complete cold audit without changing bytes. The original
subset retains every one of the prefix's 22,071 pattern nodes, 1,465 source rows
and 21,838 residual rows. Both endpoints of all 1,728 pure-only and 2,822 bounded
elimination edges are independently solved, with SAT lifts checked. The additional
bounded model diagnostic takes **688.09686 seconds**; this is retained validation
cost, not hidden inside the 80.09857-second query figure. The four-original Python
sample has a lower peak for the bounded mode, unlike the leaf sample; neither
sample bounds full-history memory or RSS.

## Remaining structure and the next experiment

The [read-only structure analysis](../experiments/results/cnf-variable-elimination-probe/structure-reuse.json)
finds **1,123 pure steps, 1,588 mixed steps with one occurrence on one side, and
111 mixed steps with multiple occurrences on both sides** in the original subset.
One-sided occurrence is therefore the dominant accepted mixed pattern here.
The 2,822 elimination edges have 2,821 distinct target keys: only one target has
two incoming elimination references. There are no repeated elimination targets
in the 99-leaf study. The current gain is chiefly exposing reducible structure,
not extensive sharing of exact target CNFs. These graph counts do not measure
when a target was acquired or all other sources of cache reuse.

After elimination, **58 of 59** selected open leaves still have candidates within
the 64-pair cap, but none admits a non-growing step under the current rule, even
when the diagnostic examines all variables. The growth condition is the observed
barrier for these 58 leaves. In **10 of 59**, a candidate becomes non-growing if
new resolvents already subsumed by a retained source clause are omitted. This is
a measured candidate opportunity, not an implemented checker, a new closure or a
timing gain. The corresponding isolated-frontier count is 11 of 62.

For cost reduction, first profile unsuccessful candidate work and test cheaper
admission before the full ranking search. A concrete sufficient case is a variable
with one occurrence in a binary clause on one side: resolving that clause against
the opposite side adds at most one clause per opposing occurrence, each no wider
than its opposing parent. Removing both sides therefore cannot increase clause
or literal count. The pair budget still applies. Recognition can use the existing
occurrence index, but its frequency, changed elimination order and actual total
cost must be measured. General one-sided occurrences in wider clauses do not
satisfy this argument automatically. Retained-clause subsumption is the next
coverage extension; a certificate must account for every omitted resolvent.
