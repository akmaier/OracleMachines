# Exact clause-width partitions of residual Boolean factors

Checkpoint: 27 November 2026. The remaining obstruction is more specific than
large local tables: **all 244 active factors admit exact clauses of width at most
four**, yet the two SAT roots remain structurally unresolved. Of the 17 dense
projected relations, one needs width two, four need width three, and **twelve
require width four on the same variables**. Checked negative witnesses establish
that last restriction; it is not a solver-time lower bound.

Replacing every table by its exact cover reduces the three primal edge counts
**130→116, 232→203 and 217→201**. A width-nine continuation then performs four
more eliminations, but stops again at widths eleven, ten and ten. The incremental
stage costs **11.95% more than continuing the original tables at width ten**, with
all eight paired signs unfavorable. Neither method decides a new leaf or root.
Retain this informative negative result and leave production defaults unchanged.

## An exact, checkable local partition

For an explicit relation R on n Boolean coordinates and a width k, an equivalent
CNF over these same coordinates exists exactly when every assignment outside R
is excluded by some entailed clause of width at most k. Equivalently, each such
assignment has a restriction to at most k coordinates that no model of R extends.

The positive certificate is a clause list. The checker evaluates it independently
on every row of the original table and requires exact equality, including false
rows. The negative certificate is one excluded row a plus, for every coordinate
subset of size min(k,n), a model of R agreeing with a on that subset. Any clause
of width at most k falsified by a would also be falsified by one of these models,
so cannot be an entailed clause. Smaller subsets extend to the checked subsets.
The two certificates are incompatible. With unlimited finite enumeration one must
exist; the implementation's exhausted search budget produces **unresolved**, not
an impossibility claim.

`cnf_factor_clause_width.py` implements this partition for materialized tables on
at most twelve coordinates. It handles empty/full relations and single-clause
tables directly, otherwise enumerating bounded-width consequences using masks.
The search cap counts candidate clauses and candidate completion witnesses;
mask construction, subsumption and bit-operation costs are additional measured
work. Validation enumerates cover rows or checks the supplied completion witnesses
without rerunning discovery. Parity tests exercise relations whose smallest
same-variable clause width is their full arity.

These are **same-variable exact representation bounds**. They do not exclude
auxiliary-variable encodings, conditioning, simplification using other factors or
other decomposition orders. Nor does a short-clause representation imply cheap
SAT: interaction between its clauses can still be difficult. Obtaining the truth
table of an arbitrary succinct CNF is a separate, potentially exponential task.
The theorem is a local partition of explicit relations, not an efficient
classification or solution of arbitrary SAT inputs.

## Source-bound recomposition and continuation

Each study input is an original residual CNF with its saved unresolved width-nine
projection prefix. The checker first validates that prefix and reconstructs its
active tables. Every active factor must appear exactly once in the classification
list, with an exact scope/table binding. Only covers for **all** factors permit
construction of a replacement CNF. Obstruction or budget exhaustion leaves the
continuation unresolved; no factor is silently dropped.

The conjunction of the checked covers is exactly the old active-factor relation.
Its new bucket certificate runs at width nine and uses only the original
projection allowance remaining after the prefix. For SAT, the terminal witness
is transported back through every old reconstruction choice and checked against
the source CNF. UNSAT follows through exact equivalence. Tests cover SAT and UNSAT
transport, changed evidence, missing factors and attempted budget resets. These
are leaf/source certificates; replacing them into an earlier conditioning graph
would still require full root recomposition before claiming a root verdict.

## What the remaining factors require

The complete width census independently checks widths zero through four for every
factor. The exact minima are:

| Smallest same-variable clause width | All active factors | Dense projected factors |
| --- | ---: | ---: |
| 0 | 3 | 0 |
| 1 | 0 | 0 |
| 2 | 89 | 1 |
| 3 | 140 | 4 |
| 4 | 12 | 12 |

All 17 dense factors have scopes of five to eight variables. Their covers contain
78 clauses; with the 224 ordinary clauses the raw replacement contains 302 clauses
(297 after normalization and deduplication).
The three constant-true factors disappear. Local edge occurrences across dense
factors fall 355→224; these overlap, so the global edge decrease is only 59.
This exposes useful local structure but does not eliminate the global coupling.

Width-three classification covers 232 factors and gives **twelve certified
obstructions**, containing 491 completion witnesses. Consequently no complete
replacement CNF is available under that restriction. Width four covers all 244.
Its 17,670 candidate-clause checks use 62,162 mask intersections; cover verification
and all source/prefix checks are additional. No benchmark source or family label
guides recognition.

## Matched incremental costs and retained failures

Eight cyclic process orders compare retaining the checked frontier (`hold`),
continuing its original tables at width ten (`wide`), and exact classification at
clause widths three/four with width-nine continuation when complete. All use the
previous verified-operator bank, initially empty for each acquisition/warm/cold
phase. Two cold passes each start empty.

| Policy | Incremental stage seconds | Warm replay | Two cold passes | Added certificate bytes, compressed |
| --- | ---: | ---: | ---: | ---: |
| Hold | 0.083423 | 0.020232 | 0.040259 | 48 |
| Wide | 0.149693 | 0.034291 | 0.068099 | 730 |
| Clause width 3 | 0.108229 | 0.022706 | 0.044930 | 4,054 |
| Clause width 4 | 0.167585 | 0.032563 | 0.064954 | 5,438 |

Width-four decomposition costs **100.89% more than hold**, **54.84% more than
width-three classification**, and **11.95% more than wide**. All eight signs are
unfavorable for each comparison. It projects 768 rows with 9,216 reserved probes,
versus 2,048 rows/23,552 probes for wide, but recognition and evidence costs exceed
that avoided projection work. Its uncompressed evidence is 113,513 bytes versus
2,262 for wide. Logical clause width shrinks while certificate storage grows.

This charges input, prefix validation/reconstruction, recognition, internal and
explicit checking, writes, warm/cold replay and compression. It is an **incremental
study of three frontiers**, not a new complete 182-query pipeline benchmark.
Historical acquisition, prior root preparation, startup, final report metadata
and independent audits are additional. Measured structural coverage remains the
previous **180/182**; all three study continuations remain unresolved. Process RSS
and all phase/counter details remain in `analysis.json`; they are observations,
not worst-case memory bounds.

The earlier static and dynamic decomposition screens are retained. Width-two
covers helped one dense factor but enabled no projection. Width-three covers
helped five and enabled one projection in the diagnostic mixed-table program.
Width-four covers, including refactoring new projected outputs, still decided no
frontier. Those search screens are explicitly distinct from the final independent
certificates and charged whole-active-CNF replacement study.

## Verification and next gaps

All **2,415 full and 14 focused tests pass**, with no changed deadlines or
assertions. Existing unclosed-SQLite ResourceWarnings remain in the full-suite
log. Fourteen new tests cover all relations on up to three variables at every width,
seeded larger tables, budget exhaustion, parity, scope transport, certificate
mutations and source-bound continuation. An independent exhaustive audit checks
**all 65,536 four-variable relations** at width three: **43,146 exact covers and
22,390 obstructions**. Its independent criterion detects an excluded hypercube
vertex whose four neighbors are all included. Every complete certificate is
retained in a compressed stream. These finite counts do not estimate coverage
on arbitrary CNFs or external workloads.

1. **Global interaction is the next coverage target.** Exact local covers are now
   available, so additional clause-width enumeration on these unchanged factors
   cannot supply the missing verdict. Investigate a separator or conditioning
   step on the coupled factor graph, with both branch obligations and exact model
   transport. The observed next widths concern the current order/factorization,
   not lower bounds on optimal decomposition.
2. **Other local representations remain distinct options.** The twelve width-three
   obstructions apply without auxiliaries or external context. A context-aware
   or auxiliary representation needs its own recognition and recomposition proof;
   do not relabel this negative result as an unrestricted barrier.
3. **Repeated validated source preparation remains the cost target.** The previous
   full-pipeline profile, not this small incremental study, identifies 5,449
   normalizations and 6,127 restrictions per replay. Further cost work should
   charge exact bindings and invalidation, while broader nonconstant transfer and
   external validation remain open.

All 238 prior manifests, 80,208 artifact entries, 1,304 scientific sources and 80
proof blocks are preserved. Four scientific sources and one local correctness
proof are added. Resume
`experiments/results/cnf-factor-refinement/checkpoint.json`, key
`factor_clause_width`. `width-census.json` contains every factor classification;
`factor-shapes.json` records exact graph changes. Final tests and manuscript checks
are recorded in `checks.json`.
