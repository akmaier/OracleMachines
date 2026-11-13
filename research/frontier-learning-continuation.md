# Continuing learned reasoning beyond the first probe block

The [target-continuation study](learned-target-continuation.md) left selected
23- and 39-variable residuals with no remaining ordinary ranked probes. This
study first checks whether their newly stored traces supply stronger reusable
consequences. Both are development residuals chosen from earlier experiments;
the retained pilot also informed this implementation.

## Exact formula and proof dependencies

Every original-source assumption trace is checked against the complete source.
Common literals and signed equivalences use both polarities of one variable.
A complete graph certificate covers the binary clauses and all implications
from saved units. A negative graph result concerns that binary subtheory, not
the complete source with nonbinary clauses.

When these simple consequences do not reduce the source, the existing selector
retains at most 16 checked implication clauses. Each new clause is entailed by
the original formula, so adding it preserves the entire model set. The initial
four-variable lookahead pass is retained as a base learning record. New blocks
continue on this **exact augmented formula**, with the original clauses in their
original order and the checked learned clauses appended. Their reason indices
must never be interpreted as original-source indices.

`LearningBlocks` names a complete base record by its digest. The checker resolves
that reference to the retained record, validates all its implications and initial
probes, and reconstructs the augmented ranking. Distinct records colliding on
the same base identity are rejected. Prefix offsets increase by four; every
predecessor must contain both clear polarities of four variables. A short final
block terminates the pool. Missing prefixes, changed bases and successful
prefixes cannot justify another block.

A successful later block must strictly reduce support and bind its exact child
and variable transport. Missing children remain pending, not covered. Clear
blocks add no coverage edge. The inherited finite route checker requires the
complete premises of every original-level route. Independent residual/original
solutions remain separate from structural availability. SAT model lifting is
checked against the original complete source after the necessary assignments
or signed substitution are restored.

The manager reuses checked base contexts and prefix blocks during a session.
A cold load checks them again. Each continuation stores a 64-character base
reference rather than another copy of the learned-clause evidence. It still
stores its new assumption reasons and, on success, the complete canonical child
identity. Hashing, clause checks, ranking, prefix checks, serialization and cold
reconstruction remain charged; shared evidence is not free advice.

## Limits and controls

The policy allows one 16-clause batch, a four-variable initial pass, at most
eight later four-variable advances, and 32 target state admissions per source.
The augmented ranking is capped at 64 variables. Only one successful later block
is acquired per source in this study. These caps bound counts, not the cost or
size of each state. A wider learning batch or different conditioning policy may
find additional structure; no exhaustive saturation or arbitrary-SAT efficiency
claim follows.

For every augmented block, the control probes the original formula using the
same variable order. This distinguishes stronger propagation from a changed
ranking. Controls acquire additional traces and consume additional resources.
It is not an equal-total-cost comparison against two-variable conditioning or
another solver. Pilot and tests are also separate costs from the timed pipeline.

The exhaustion certificate has a narrower meaning than a complexity lower bound.
For a normalized source whose minimum clause width is at least two, a variable
absent from every binary clause cannot create an initial unit or empty clause
under either assignment. Checked clear fixed points for both polarities of every
binary variable, plus this structural fact for the remaining variables, exclude
single-assumption unit refutation. They do not exclude reasoning with new clauses,
multiple assumptions, component structure or another algorithm.

The implementation and artifacts are in `experiments/results/cnf-frontier-learning`.
Restoration returns all paired rewrites, learning bases and later blocks for
`ContinuedLearningRoutes`. All previous eight-table rows remain immutable. The
full test suite contains 573 passing tests, including new later-block model
lifting, prefix integrity, forged evidence, pending-target replay and exhaustion
checks. The pilot preserves the corrected tuple/list test-fixture mistake.

## Measured result, 13 November 2026

Coverage increases **46/83 -> 47/83**, and all 47 remain covered without the
exceptional growth routes. Case **32** (`reuse_holdout3`, n48, original 1191)
now has a complete structural plan. The independent reference archive proves
the **original SAT** and checks its witness. Its exposed 23-variable source and
successful continuation target are also independently SAT, with model lifting
checked. These historical group labels do not constitute an independent holdout.

The two original sources supply **84 saved attempts**, covering both polarities
of 42 binary-variable instances. The no-trigger lemma handles 20 other variable
instances. Neither the pair scans nor the complete implication graphs expose a
common value, equivalence, forced literal or contradiction. These negative
results are retained with their exact source dependencies.

| Source | Checked added clauses | Initial augmented block | Later blocks | Result |
| --- | ---: | --- | --- | --- |
| 23 variables / 97 clauses | 16 | clear | offset 4 clear; offset 8 forced after three attempts | Original case 32 closes; 17 states admitted |
| 39 variables / 160 clauses | 6 | clear | offsets 4 through 28 clear; final block has one variable | Remains open; no states admitted |

Every same-variable original-source control remains clear. On the smaller
source, adding retained implications therefore strengthens propagation beyond
the effect of selecting a different variable. Target recognition subsequently
uses existing rules and further probes, so the coverage gain is a composed
result rather than a claim that these learned clauses alone decide the original.
No admission cap binds and no target is pending.

The 39-variable source also has an exact exhaustion certificate **after adding
its six clauses**: 58 clear attempts cover all 29 augmented binary variables,
and ten remaining variables cannot trigger unit propagation. This excludes
single-assumption unit refutation on that exact augmented formula. Its batch
contains fewer than 16 clauses, so increasing the same selection cap alone
would not change it: the current filter already processes its entire saved
original-source candidate pool. New augmented traces may support further
learning, but only with the augmented formula's explicit proof dependencies.

The two learning bases contain 22 clauses with **eight interned source-trace
references**. The run retains nine later blocks, eight clear and one forced.
There are **16 initial augmented attempts, 61 later augmented attempts, 135
additional target-recognition attempts and 82 control attempts**. Verification
and prefix replay counts are recorded separately; they are not new discoveries.

| Phase | Seconds |
| --- | ---: |
| Restore parent history | 7.45586 |
| Prepare full baseline routes | 65.24826 |
| Source traces, pair/graph scans and original exhaustion checks | 0.04568 |
| Initial learned batches and augmented probes | 0.01057 |
| Later augmented blocks and checks | 0.03867 |
| Same-order original-source controls | 0.02608 |
| Target recognition and checks | 0.05576 |
| Repeated continuation persistence during acquisition | 0.00208 |
| Augmented exhaustion diagnosis | 0.01021 |
| Original-level recomposition and remaining-target diagnosis | 0.10968 |
| Full cold inventory | 106.55780 |
| Cold routes, coverage and remaining-target diagnosis | 63.17620 |
| Independent reference solving / replay | 0.19652 / 0.06378 |
| Acquisition/validation pipeline before final report write | 256.46938 |

The pipeline also includes copying, export, compression, artifact serialization
and reconstruction. It excludes the pilot, fixture extraction, test development,
full tests and the subsequent standalone validator. Cold verification remains
the dominant cost; no whole-solver speedup follows from the small local timings.

Working SQLite grows **212,992 bytes** to **767,553,536 bytes**, with **41,582
pattern nodes**. All old eight-table rows remain unchanged, including 79 ordinary
probe windows and 108 ordinary continuation blocks. The nine new augmented
continuations are a separate evidence layer, not rows in those ordinary tables.

| Additional artifact | Uncompressed bytes | Compressed bytes |
| --- | ---: | ---: |
| Pattern delta (SQLite) | 282,624 | 11,813 |
| Two learning bases (JSON) | 30,870 | 2,718 |
| Nine augmented continuations (JSON) | 10,022 | 1,814 |
| Diagnostics and controls (JSON) | 50,090 | 5,505 |
| Finite coverage witness (JSON) | 1,239,449 | 201,172 |
| Independent reference proofs (SQLite, 164 nodes) | 1,257,472 | 79,152 |

These artifacts, report and logs are additional to the working SQLite history.
Persistent sizes are not peak-RAM measurements. The complete prior solver history
and external paired/learning evidence remain available. Manuscript and Lean
sources are unchanged; this is another experimentally checked route rather than
a new unrestricted complexity result.

## Next highest-value gap

The newly closed source no longer needs more ordinary expansion. Apply the
continuation mechanism to the **36 earlier clear learning records**, filtering
sources already covered by other routes and ordering the rest by exposed size.
Their implication evidence and initial augmented probes are already stored;
reusing these bases avoids repeating clause acquisition and the unchanged graph
scan. Use an explicit shared work budget and retain same-variable controls,
negative outcomes, target admissions and full cold costs.

Keep the exhausted 39-variable source as a harder secondary case. Its augmented
traces may justify another bounded learning layer, with explicit dependencies
back to the original source. Compare that reuse with two-variable conditioning;
do not rerun the same exhausted ranking or silently treat augmented reason
indices as original-source indices. Larger independent workloads, total-memory
measurement, dependency-local cold checking and unrestricted coverage remain
open.

All **573 tests**, the full cold inventory audit and the standalone validator
pass. The standalone run takes **71.67049 seconds** in addition to the pipeline.
It reconstructs all archives, checks original/augmented exhaustion, pair and
graph evidence, deterministic clause selection, every matched control, complete
prefix chains, exact coverage and independent reference proofs. No new probe
discovery or reference expansion occurs, and database bytes remain unchanged.
