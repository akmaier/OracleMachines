# Pattern discovery with an exact residual partition

The new `PatternInventory` analyzes CNFs without generator labels, retains
overlapping recognized patterns and records exact component/conditioning
decompositions. It is a separate persistent analysis path over the existing
normalization, restriction, component and matching helpers. The SAT decision
engine is unchanged. This experiment measures discovery coverage and its added
cost, not a solver speedup or a complete efficient classification of SAT.

## Profiles and certificates

Every normalized formula receives seven outcomes in fixed order: Horn,
dual-Horn, 2-CNF, all-false witness, all-true witness, the existing explicit
matching representation, and a complete direct encoding of one parity equation.
The first six are complete tests for the stated syntax/witness property.
Single-parity recognition is capped at eight variables by default: exceeding
the cap is **unresolved**, not excluded. An exclusion concerns the stated
representation, not semantic equivalence to a tractable family or hardness.
Complementary binary clause pairs are recorded as an additional local feature.

The parity certificate names its variables and right-hand side. For q variables,
each distinct non-tautological full-width clause excludes one assignment. If
there are exactly 2^(q-1) such clauses, all excluding assignments of parity p,
they exclude precisely that half of the Boolean cube. The CNF therefore means
XOR(variables)=1-p. The checker verifies the explicit clauses, count and parity;
it does not search truth tables to recognize a hidden affine representation.
Conjunctions of overlapping equations are not yet extracted as a system.

Exact source records preserve original order, duplicates, tautologies and
variable names. Profiles concern their normalized residuals. Keys contain full
serialized identities, not a collision-free-hash assumption. Name bindings map
each local residual back to its parent variables. Policy parameters are part of
the identity. The outcome vector defines disjoint reporting cells covering all
valid inputs for the fixed policy; that bookkeeping fact does not make every
cell efficiently solvable. Invalid literals are rejected separately.

Independent variable components combine by AND. The checker reconstructs all
parent clauses from the child bindings and checks disjoint supports, independently
of the component discoverer. Conditioning records both exact restrictions and
combines by OR. Candidate variables are selected by decreasing occurrence count,
then ID, with at most four per node. Search stops at the first fully explained
alternative, otherwise selecting minimum unresolved literal occurrences. All
attempted alternatives remain stored, including unsuccessful ones.

**Closed** means every selected leaf has a recognized family. It does not mean
SAT: for example, a decomposition into contradictory 2-CNF leaves is closed.
An unresolved leaf supplies no verdict. The normal residual solver separately
decides every benchmark input, with its existing checked SAT/UNSAT records.
Analysis can remain unresolved even when that solver already has an easy answer.

## Coverage and cost

The 664-input corpus contains all 512 subsets of the nine non-tautological clauses
over two variables (including the empty clause/formula), 120 seeded larger CNFs, 16 structural
controls and 16 renamed/reordered/duplicated variants. Generator labels are
reporting metadata only. Random support permutations test representation
sensitivity; normalization shares only order-preserving names, not arbitrary
isomorphisms. All root signatures agree between the structured cases and their
variants. There are **24 observed root cells**; this is not a complete list of
possible cells over all finite CNFs. The two-variable sources normalize to 257
distinct residuals because every source containing an empty clause collapses to
that contradiction; all 512 original source records remain retained.

All 512 tiny inputs are closed already under the whole-formula tests. The more
informative comparison is the remaining 152:

| Analysis mode | Closed / 152 | Sum of per-input distinct unresolved literal occurrences | Analysis + solving seconds | Pattern nodes | SQLite bytes, including solver |
| --- | ---: | ---: | ---: | ---: | ---: |
| Solver only | Not analyzed | Not analyzed | 0.30139 | 0 | 385,024 |
| Whole formulas | 39 | 16,779 | 0.87571 | 398 | 1,650,688 |
| Independent components | 45 | 16,471 | 0.77352 | 401 | 1,654,784 |
| Components + one conditioning level | 57 | 5,077 | 1.18181 | 1,140 | 3,026,944 |
| Components + two conditioning levels | 102 | 1,970 | 2.02127 | 2,801 | 6,459,392 |

Timings cover the full 664-input corpus and are single sequential samples.
The comparison is additive: the inventory runs before the same unchanged SAT
solver in every analysis mode. Each solver archive contains the same 699 residual
records. At two levels, analysis alone costs 1.70180 s, and retains 3,688,352
logical node bytes plus 452,011 exact-source bytes. The observations do not
justify enabling this eager analysis on every solver request.

The literal aggregate counts each selected canonical unresolved residual once
per input. Across different inputs it can count shared residuals repeatedly;
it is neither a global archive-size measure nor a runtime bound. Separate
record fields preserve tree-multiplicity summaries and distinct selected DAG
summaries. The decrease is partly driven by the large ten-variable parity
control: it exceeds the parity cap, but one conditioning step exposes uniform
witnesses in both branches. Report this contribution rather than treating the
aggregate as evidence of broad random-CNF tractability.

Components recognize a matching formula beside unrelated equivalence or parity
components. One level explains an overlapping-parity example and a parity unit
addition. Two levels explain a parity bridge and the four-variable complete
exclusion cube. The latter is UNSAT, checked independently by the ordinary solver.

## Unresolved cells and next experiment

Two levels leave **50 inputs unresolved**: 42 of 120 seeded CNFs, plus four
structural controls and their variants. Forty-eight have every tested pattern
excluded; two exceed the parity cap while failing the other tests. This is
failure of the stated representation tests, not proof of computational hardness.

The retained structural misses are complete exclusion cubes on five/six
variables, a coupled matching/parity formula, and an activated guarded formula.
A bridge clause defeats independent decomposition; a unit can expose all the
guarded interaction. Increasing conditioning depth merely spends more analysis
and memory, and is not automatically the next best action.

**Next discovery target:** refine the connected unresolved cells by exact clause
support and sign patterns. Test whether complete parity halves, complete exclusion
cubes and multiple explicit parity equations can be recognized and recomposed
without branching, while preserving arbitrary leftover coupling clauses. Run the
same recognizer on all 50 unresolved inputs and matched variants, without labels;
report zero gains on random CNFs if that is what happens. Recognizing an embedded
equation alone must not authorize dropping its couplings. Other tractable-class
extensions remain candidates once this partition has evidence.

## Memory, replay and validation

Full cold audits take 0.07812 s for whole-formula analysis and 0.36241 s for two
levels, versus 0.02049 s for the solver-only archive. These audits read all
analysis nodes and alternatives, check exact source bindings and validate every
solver residual. Warm reinspection of all inputs takes 0.02684 and 0.02998 s,
respectively; original input normalization and serialization remain charged.

Separate tracemalloc runs on six listed mixed/guarded cases measure peaks of
60,634 bytes for solving alone, 99,218 with whole profiles and 205,298 with two
levels. These small memory diagnostics exclude native SQLite and process RSS;
they are not peaks for the entire 664-input benchmark.

All **276 Python tests pass**. New tests check exhaustive two-variable coverage,
overlaps, parity truth tables through six variables, 80 random branching cases,
pointwise assignment recomposition, source renamings, old/cold records, invalid
inputs and forged certificates. A faulty component discoverer proposing
overlapping supports is independently rejected. The five final archives contain
4,740 pattern nodes and 2,656 source records in total, plus 699 solver residuals
per archive. All replay with unchanged bytes and no new solving. All five
preserved initial archives also pass the stronger final checker.

No new Lean theorem is asserted. `satisfiable_split` in `Residuals.lean` supplies
the existing semantic conditioning identity; this Python planner, its recognition,
source bindings and SQL are outside that refinement. Finite semantic coverage,
bounded discovery and cheap prepared-state reuse remain distinct from uniform
polynomial acquisition and compact closure for arbitrary SAT.

Reproduce into a new directory:

```sh
python3 experiments/compare_cnf_pattern_inventory.py --output /tmp/new-pattern-study
python3 -m unittest discover -s solver -v
```

`report.json` stores exact inputs, policies, fingerprints, all results and archive
digests; `summary.json` is its compact aggregation. Input generation, truth-table
validation, inter-operation checks, storage scans and offline compression are
outside timed acquisition. Database initialization and warm/cold operations are
separate fields. The first run is preserved in `cnf-pattern-inventory-initial`
with the then-current source snapshots; it predates the additional direct
component-partition check and is not pooled into these final timings.
