# Reusing a checked UNSAT proof after deleting a clause

2026-11-16. An optional decision path now uses a verified UNSAT result to force
the falsifying assignment of a deleted clause. On the twelve constructed edits
from [join transfer](join-transfer.md), it reduces new **reference residual nodes
from 502 to 427 (14.94%)** and measured complete stream time **8.11%**. This is a
SAT decision experiment using the unchanged `ResidualSolver`, separate from the
structural-coverage planner. Original structural coverage remains **17/24** and
the supplemental constructed set remains **24/24**.

## Exact condition and limitation

Let `F = G ∧ C`, where `G` is obtained by deleting exactly one clause `C` in
shared variable coordinates. If an independently checked proof establishes
`F ∈ UNSAT`, then every model of `G` must falsify `C`: otherwise it would also
satisfy `F`. Write `a` for the assignment falsifying every literal of `C`. Thus
`G` is satisfiable exactly when `G restricted by a` is satisfiable. A model of
the restricted formula lifts by adjoining `a`; a checked UNSAT result for that
formula, together with the old UNSAT premise, proves `G` unsatisfiable.

The implementation checks exact clause-set difference, the stronger formula's
canonical root, and its stored decision certificate. A structural coverage flag,
missing result or SAT result cannot activate the guard. SAT models are checked
against the complete edited input after lifting. A small candidate bank uses
clause count followed by exact set containment; it neither searches arbitrary
variable renamings nor treats similar formula shapes as evidence. The interface
rejects tautological clauses; ordinary solver policy is unchanged.

This is an elementary consequence of established clause-deletion reasoning,
not a new complexity result. Belov and Marques-Silva describe transition clauses
and the fact that a model after deleting one clause from an UNSAT formula
falsifies exactly that clause (Proposition 1). Their recursive model rotation
uses models to find further transition clauses; our experiment instead evaluates
a checked forced-assignment wrapper. [FMCAD 2011 paper](https://www.cs.utexas.edu/~hunt/fmcad/FMCAD11/papers/74.pdf)

Even a unit deletion and a cheap UNSAT premise can leave arbitrary SAT. For
any CNF `H` and fresh `x`, take `G = H ∧ ¬x` and `F = G ∧ x`. The old formula
has a unit contradiction; deleting `x` and applying the guard leaves exactly
`H`. The analyzer checks this construction on all **512 CNFs over the nine
normalized clauses on two variables**, including the empty clause. The general
argument is syntactic and does not depend on this finite check. No uniform bound
on the remaining solving follows. No new Lean formalization is claimed.

## What happens on the edits

The initial partition diagnostic for case 13 found no stored exact residual in
any of its three cells after unit closure. Its deleted clause is `¬320 ∨ 280`.
The new decision proof verifies that the undeleted formula is UNSAT; it therefore
suffices to set `320=true, 280=false`. This reduces the raw source from
**33 variables / 95 clauses / 274 literals** to **31 / 86 / 245**, but does not
reduce measured residual acquisition on this case: **22 nodes and eleven splits
in either mode**. The earlier structural planner's 29-node count measures a
different inventory and is not a comparator for these reference-node counts.

| Edited case | Undeleted / edited SAT answers | Ordinary / guarded new residual nodes | Ordinary / guarded splits |
| --- | --- | ---: | ---: |
| 7 | UNSAT / SAT | 13 / 13 | 4 / 6 |
| 9 | UNSAT / SAT | 11 / 10 | 4 / 3 |
| 11 | UNSAT / UNSAT | 19 / 12 | 6 / 4 |
| 13 | UNSAT / SAT | 22 / 22 | 11 / 11 |
| 15 | UNSAT / UNSAT | 43 / 1 | 16 / 0 |
| 17 | UNSAT / UNSAT | 26 / 1 | 9 / 0 |

The guard applies on these six inputs. All other undeleted templates are SAT,
so the guard declines and ordinary solving runs. Their edited inputs are also
SAT. Across all twelve cases, both modes agree on **nine SAT and three UNSAT
answers**, with checked witnesses or negative certificates. Case 7 performs two
more splits under the guard. Cases 15 and 17 supply 67 of the 75 avoided nodes;
the retained failures prevent attributing the result to a universal advantage.

## Charged experiment

Before either mode, all twelve undeleted formulas are solved with the reference
solver, creating **613 checked residual nodes**. This preparation, cold check
and seed compression cost **0.91359 seconds**, separately. Both modes restore the
same seed; neither can access previously solved edited roots from the structural
archive. The query bank contains the undeleted formulas but no supplied match for
the incoming query. Two fresh-process repetitions reverse mode order. Each
processes twelve edits and then repeats them; both second visits add zero nodes.

| Resource per stream | Ordinary | Guarded |
| --- | ---: | ---: |
| New residual nodes | 502 | 427 |
| New decision splits | 200 | 174 |
| Query processing and bookkeeping, seconds | 0.58998 | 0.53240 |
| Full cold audit, seconds | 0.35883 | 0.33097 |
| Compression, seconds | 0.31183 | 0.29279 |
| Setup, seconds | 0.00731 | 0.00825 |
| Complete stream, seconds | 1.27860 | 1.17492 |
| Mean peak RSS, bytes | 84,762,624 | 84,598,784 |
| Final residual nodes | 1,115 | 1,040 |
| SQLite bytes | 5,804,032 | 5,431,296 |
| Compressed database bytes | 431,983 | 405,995 |
| Raw query sidecar bytes, first repetition | 328,385 | 404,998 |

Query time falls **9.76%**, complete time **8.11%**, and SQLite space **6.42%**.
Paired whole times are **1.30099/1.25622** seconds ordinary and **1.17002/1.17982**
guarded. Two repetitions are a development measurement, not broad performance
evidence. Peak RSS differs by only **0.193%**. The database gzip shrinks **6.02%**,
but database gzip plus the verbose raw query sidecar grows from **760,368 to
810,993 bytes** in the first repetition. Proof metadata must remain in the
storage account; these sidecars have not been compacted.

The clock includes restoration, bank construction, candidate checks, UNSAT
premise replay, solving, lifted-witness checking, bookkeeping, full cold auditing,
sidecar serialization and compression. Imports and final report writing are
excluded. Prior acquisition and the 0.91359-second seed preparation remain
separate; there is no comparison here against solving edits without first
acquiring their undeleted templates. Reference decisions are newly acquired
proofs, not answers inferred from earlier structural coverage.

Independent validation takes **19.62021 seconds**, outside operational timing
and partly concurrent with tests. It checks all archived nodes, all 96 query
results, exact source bindings, forced assignments, immutable seed rows,
repetition identity, agreement between modes, and both preserved structural
catalogs, with fresh reference search disabled. All **382 tests** pass, including
exhaustive two-variable checks of the conditional identity and rejection of
satisfiable, missing or foreign premises, wrong edits and conflicting models.

## Persistence and next work

All reference seeds, four stream archives, decision sidecars, witnesses and
failed comparisons are retained under `experiments/results/cnf-clause-deletion-guard`.
Its `checkpoint.json` references the unchanged **2,614-pattern / 259-pair**
structural authority, retaining the **999-step original proof**, the **208-step
supplemental proof**, and all seventeen inherited missing children. The new
`reference_study` field binds the separate decision experiment; later runs must
retain these reference archives and sidecars too. No old source or artifact is
rewritten, and no default solver policy changes.
The new result directory retains **32 manifested artifacts plus its manifest,
3,858,771 bytes** total. The next audit inherits **3,620 artifacts / 63 manifests**.

The largest next opportunity is **positive witness transfer on clause deletion**.
The 39-variable-anchor edits 19, 21 and 23 consume **364 of the remaining 427
reference nodes (85.2%)**, despite their undeleted formulas already being SAT.
The analyzer directly verifies that each retained stronger witness satisfies
its edited input, for all six SAT-template cases. This is a validated proposal,
not an implemented runtime saving: the current guard deliberately declines
SAT premises. Implement checked witness reuse before fresh search, with its
lookup, validation and persistence costs, while retaining the UNSAT guard and
an ordinary control. Case 13 still needs better handling within its exceptional
cofactor. Original case 7 remains a separate broader structural discovery target.
