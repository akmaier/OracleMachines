# Retained clauses can certify redundant resolvents

The preceding [bounded-elimination experiment](variable-elimination.md) leaves
59 selected open leaves. Its read-only diagnostic finds ten with a non-growing
candidate if retained source clauses justify omitting new resolvents. This
extension implements that condition as an optional fallback. It runs only after
the previous terminal elimination proposal is null; it does not replace an
existing accepted pivot at that node. Changed descendants can still affect
bounded parent selection, so coverage losses must be measured, not ruled out by
this local ordering statement.

Variable elimination combined with subsumption is established preprocessing:
[Een and Biere, SAT 2005](https://fmv.jku.at/papers/EenBiere-SAT05.pdf), especially
sections 4.1--4.4, describe their interaction and the maintenance needed to avoid
revisiting unchanged work. This repository adds a checked integration and a
resource comparison; the transformation is not a new tractable SAT class.

## Exact omission condition

Partition the source at variable x into retained clauses R, positive clauses
`x OR P_i`, and negative clauses `NOT x OR N_j`. Every opposing pair produces
`P_i OR N_j`. A non-tautological resolvent may be omitted when a clause r in R
is a subclause of it. Every model of the target then satisfies r and hence that
resolvent. Adding the omitted resolvents therefore changes no target model.
The full elimination projection theorem and its model-extension rule still
apply. A clause being deleted with x cannot serve as r: its truth would itself
depend on the extension being constructed.

`SubsumedElimination.lean` proves subclause implication, redundant-clause removal
and exact projection when each opposing pair is kept or covered by a retained
subclause. The semantic construction uses explicit clause lists; Python parsing,
tautology removal, deduplication, normalization, witness indices, scheduling,
persistence and costs remain outside that Lean refinement. The full axiom audit
passes at 4,173 declarations / 2,009 theorem declarations.

## Discovery, independent checking and invalidation

The optional `SubsumedEliminationInventory` has a separate persistent configuration.
Discovery orders at most 64 variables by opposing-pair count and identifier, and
visits at most 64 opposing pairs for each. It indexes each source clause by its
smallest signed literal, treating the empty clause separately. A possible retained
subclause's anchor must occur in the resolvent. Exact subset checking, not the
anchor, proves redundancy; the reason must omit both pivot polarities.

Each omission records three source positions: the positive parent, negative
parent and retained reason. The independent checker validates these references,
rejects repeated pair references and deleted or unrelated reasons, enumerates
every opposing pair, and checks every omitted resolvent against its actual reason.
It reconstructs the remaining target and checks the same non-growth and exact
child-binding obligations as before. A null proposal remains unresolved. SAT
lifting verifies the target model, restores the pivot and checks the full source.
Existing family proofs and failed alternatives remain retained and checked.

Reasons are tied to an exact source and its ordering. Inserting, deleting,
strengthening or reordering a clause requires a new binding and witness check.
Unchanged pivot occurrence lists alone are insufficient for reuse: a retained
subclause may be added or removed. No cross-source omission cache or persistent
touched-clause maintenance is implemented here.

## Additional resource obligations

For L literal occurrences, m clauses, n variables, maximum width w, candidate
cap K and opposing-pair cap B, preparing the occurrence/anchor index uses O(L+m)
logical slots and expected container work, followed by O(n log n) ordering.
Candidate search adds up to O(K B m w) expected subset work in the worst case;
the anchor filter does not improve this worst-case guarantee. It also pays
source validation, removed-clause accounting, pair unions and resolvent sorting.
The entire old failed elimination attempt runs before this fallback.

A certificate has at most B omission triples plus its pivot. Source indices
require O(log(m+1)) bits each; literal identifiers retain their own bit cost.
Checking uses the references instead of the discovery anchor search, but still
charges every pair. The current list-membership validation can cost O(B m),
in addition to source scans, O(B w) reason/pair work and target sorting. These
are logical expected-container bounds, not constant-time hashing or bit-cost
guarantees. Live resolvents and witnesses use O(B w+B) additional logical slots.

Each accepted step removes a variable without increasing clauses or literal
occurrences. This bounds elimination-chain length, not the hardness of a final
core or the number of alternatives acquired elsewhere. Source/profile copies,
old failed obligations, child keys and snapshots remain stored. The fallback
does not establish a smaller total archive or uniformly cheap expansion.

The implementation passes all 506 Python tests, including exhaustive tiny-CNF
projection and lifts, random edits and signed 130-bit identifiers, explicit
growth rescue, invalid reasons, and persistence/corruption checks on all ten
saved candidate leaves. These correctness checks do not establish a runtime gain.

## Saved-frontier comparison

A matched comparison starts from empty history and queries all 59 remaining
selected leaves at conditioning depth zero. Both the previous bounded rule and
the subsumption fallback close **zero**. Selected open literal occurrences fall
only **26,205 -> 26,181**. Total query time rises **2.88938 -> 3.12938 seconds** and
database bytes **17,969,152 -> 18,169,856**. A further valid elimination is therefore
not sufficient to expose one of the currently recognized terminal families.

The [complete record](../experiments/results/cnf-subsumed-elimination-remaining/README.md)
retains both archives, individual outcomes, full cold checking, separate model
diagnostics and the allocation sample. The ordinary solver still decides every
original leaf with matched search counters. This is a negative result for total
cost on these selected failures, not a claim that subsumption is generally
unhelpful. Whole-source recomposition and ordering effects require separate
measurement; local candidate availability alone supplies neither.

Reversing the execution order gives the same negative result: **2.96506 ->
3.30563 seconds**, still zero closures. Each mode's archive is byte-identical
across the two ordered comparisons. Ten new subsumed edges and one subsequent
ordinary elimination are retained, with 70 total nodes instead of 59. All new
edges have independent endpoint/model checks (eight SAT, two UNSAT). Those
verdicts come from ordinary solving, not from structural closure.

## Whole original inputs

The separate [83-source comparison](../experiments/results/cnf-subsumed-elimination-originals/README.md)
starts each policy from the same paid 417,370,112-byte prefix. The previous policy
and subsumption fallback close **the same 29 sources**, leaving 54 open. Both
retain 59 selected open leaves; their literal totals are 26,205 and 26,181.

| Measurement | Previous bounded policy | Subsumption fallback |
| --- | ---: | ---: |
| Total query seconds | 79.65962 | 88.16727 |
| Discovery seconds | 77.92568 | 86.41462 |
| Complete database bytes | 621,146,112 | 628,133,888 |
| Pattern nodes | 34,514 | 34,692 |
| Cold audit seconds | 79.17392 | 81.08654 |
| Four-source peak Python bytes | 16,820,009 | 15,136,923 |

The fallback tests 86,305 additional pivots and rejects 85,902 for growth. It
visits 824,446 opposing pairs and performs 8,639,284 subset tests. Its 324 new
elimination edges include unselected plans. Independent endpoint solving/model
lifting covers all 324 (217 SAT / 107 UNSAT) and takes another 33.47933 seconds.
Existing-rule edges receive complete cold proof checking; their extra endpoint
diagnostic is not repeated in these runs. Ordinary solver residual evidence and
search counters agree. Every old row survives, and all six complete cold audits
leave bytes unchanged. The original baseline reproduces the previous bounded
database exactly. Sampled Python allocation falls while archive size increases;
the sample excludes native memory, RSS and full-history peak.

The candidate remains optional and is not promoted. No fresh holdout or new
full-corpus run is justified by these negative controls. The 29-closure result
is unchanged, and the unsuccessful evidence is retained for later decisions.

## Why a clause-count bound is a separate next experiment

The present admission rule requires both non-growing clause count and
non-growing literal count. The latter condition is sufficient but unnecessary
for a polynomial bound on the size of a single intermediate CNF. A normalized,
non-tautological clause has at most one literal per variable. Consequently a CNF
with m clauses and n variables has at most mn literal occurrences. Along an
elimination-only chain with non-growing clause count, m stays at most its initial
value m0 and n decreases from n0, giving at most m0*n0 literals at each step and
at most n0 steps. This allows some resolvent-width growth without exponential
growth of the individual formulas.

This elementary bound does not guarantee an admissible next pivot, a tractable
final core or a polynomial bound on the full inventory's branching history. It
also does not bound integer encoding, checker overhead or the space retained
across unrelated source queries. Clause-count-based admission is already used
in the cited preprocessing literature. A read-only diagnostic measures how many
current leaves would admit such a pivot before changing our implementation;
availability is still not a measured new structural closure.

The [growth diagnostic](../experiments/results/cnf-subsumed-elimination-originals/growth-opportunity.json)
finds a candidate with non-growing clause count in **48/59** leaves without subsumption
and **49/59** with it, preserving the 64-candidate / 64-pair limits. All need at
most eight additional literal occurrences. With a one-literal allowance, the
counts are **15/59** and **19/59**; with four, both are **43/59**. None admits the
present joint non-growth rule. This prioritizes the cheaper plain clause-count
policy for the next controlled test; subsumption supplies only one extra leaf
of candidate availability at the broader width allowance. No such new policy,
closure or timing gain is implemented by this diagnostic. The initial diagnostic
and its exact script are also retained; they examined only the subsumption view.
