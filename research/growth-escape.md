# A controlled growth-three escape from a retained SAT core

The [coupled-pivot experiment](coupled-pivots.md) exposed one previously unseen
unresolved core: 35 variables, 150 clauses and 478 literals. Its complete source
and exhaustive pair-capped diagnostic persist in the earlier archive. Within
64 opposing pairs, the least first-step clause growth is three, attained only
by pivot 15. The old recognizer allows two. This experiment isolates that one
admission obstruction; minimum clause growth is not minimum computational cost.

## Checked exception and reuse scope

`cnf_growth_escape.py` enumerates the same pair/candidate-capped projections,
retains the minimum-growth admitted candidates, and reconstructs each exact
existential projection independently before discovery. Only this first edge
receives allowance three. Its target uses the original recognizer configuration
(allowance two) and the source's remaining conditioning depth. Thus previously
stored targets and descendants retain their exact identities and can be reused.

Each trial records the exact source key, pivot, explicit growth allowance,
canonical child key, variable-name binding and checked child summary. Its identity
includes the allowance. Cold checking reconstructs all resolvents and validates
the caller's allowance; changing the record to claim a different budget is rejected.
The inherited elimination/model-lift argument applies without a new semantic rule.
Closed recognition means a complete structural plan, not a Boolean SAT answer.

One admission scope permits at most 32 distinct newly entered recognizer states,
including descendants and unfinished ancestors. A stop persists completed child
proofs without inventing a target edge or negative SAT result. Replay checks saved
trials without running proposal discovery; a warm search still pays candidate
preparation before reusing a saved trial. These caps do not bound preparation,
old-history verification, bytes per state, accumulated storage or process memory.

## Experiment and accounting

The driver restores the complete original-input history, including both earlier
pivot schedules, both ancestor schedules and the coupled trials. It compares
allowance two and allowance three on the same source and prepared history, then
tests warm reuse with a zero-new-state budget. This is one selected development
core and a single timed run, not a general speed comparison or an independent
evaluation. Timings include trial checking and persistence; restore, clone,
preparation, diagnostics, export, reconstruction and cold passes are separate.

The sixth SQLite table is `cnf_growth_trials_v1`. The old five tables remain
immutable except for newly acquired pattern rows. The artifact includes a delta,
old-row preservation checks, logical table digests, a complete cold inventory
audit and separate replay of all three trial types. An independent validator
enumerates variable occurrences to check the exact minimum-growth choices and
the next unresolved frontier. No previously stored failed trial or proof is erased.

The [preserved run](../experiments/results/cnf-growth-escape/README.md), frozen at
`6134c54`, closes the core. Pivot 15 constructs a 34-variable, 153-clause,
506-literal target. Four new probing nodes then give a complete plan, with
intermediate source sizes 33/145/456, 32/141/441 and 30/123/360
(variables/clauses/literals). There is no unresolved leaf in that target plan.
The extra clause allowance exposes effective failed-literal probing; it does not
make further raw projections satisfy the earlier two-step net-growth constraint.

Resident control preparation costs **0.0026375 seconds**, without an admitted
growth-two pivot. Growth-three expansion, checking and persistence cost
**0.0227487 seconds** and admit four new states. Warm search costs **0.0032055
seconds**, rechecking the saved trial without acquiring any state. The database
grows by **69,632 bytes**, including the trial, over a seed with the empty sixth
table already created. The separate delta costs **122,880 SQLite bytes / 7,870
compressed bytes**. These are storage figures, not measured peak RAM.

Preparation of the paid history takes **65.69 seconds**, full cold inventory
checking **114.37**, and separate trial replay **67.68**. These remain additional
costs, with overlapping verification work explicitly charged. All 538 tests and
independent six-table artifact validation pass. Original coverage remains 31/83
under the earlier composition routine because this leaf is reached through an
open saved alternative; the local result alone does not establish a source gain.

## Finite composition through saved alternatives

`cnf_route_composition.py` rechecks every stored pivot, coupled and growth edge
before exposing it to composition. Every immutable old rule and saved alternative
becomes a possible rule with explicit child premises. Components require all
children. Each conditioning choice requires both children, while different
conditioning choices or saved projections are alternatives. A checked closed old
plan supplies a premise-free base.

A worklist computes the least fixed point: a rule can justify its source only
after every premise has been justified. Cycles alone supply no base. The saved
witness retains only steps needed for claimed roots and orders each child before
its parent. An independent replay reconstructs the selected rules and checks this
ordering, exact route identities and every claimed root. Duplicate child keys
retain premise multiplicity during acquisition; their separate variable bindings
are checked by the inventory and projection checkers.

After underlying certificate checking, this composition performs O(V+E) graph
operations for reachable nodes and rule-premise occurrences. Keys, serialization,
lookup and verification costs are additional; V and E can themselves be large.
This is a finite-history composition argument, not an unrestricted SAT bound or
a Lean refinement of the Python implementation.

## Limits

An escape that merely removes a variable can leave a denser unresolved formula.
Useful progress requires subsequent recognition, simplification or a reusable
decomposition; support reduction alone supplies none of those guarantees. A fixed
growth allowance bounds one accepted elimination chain's clause accumulation,
but neither guarantees another admissible pivot nor bounds the entire planner.

Further expansion still needs a useful projection, a tractable endpoint and
complete source-level composition. A single selected successful core supplies no
bound on the number or cost of such escapes needed on other inputs. No
unrestricted SAT complexity claim or new formal theorem follows from this
experiment.
