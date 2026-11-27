# Frozen external SATLIB audit of structural expansion

Checkpoint: 27 November 2026. The existing method transfers to external inputs,
but the previous synthetic panel's 182/182 result does not generalize uniformly.
On **25 frozen original SATLIB inputs**, unchanged cutset expansion raises
certified coverage **17/25 → 19/25**, closing two graph-colouring instances. The
12 derived controls remain **10/12**. No baseline certificate is lost. The two
denominators are kept separate; the aggregate 27/37 → 29/37 is not 37 independent
external samples.

The complete measured structural-discovery workflow costs **35.17482 s** versus
**15.70674 s**, a **123.95% increase**, with all four paired signs unfavorable.
It includes initial source preparation and discovery, not just a continuation
stage. There is no fallback here: unresolved inputs remain unresolved, so this is
not total time to answer every query or a comparison against fresh solving.
Production defaults and the earlier synthetic certificate union remain unchanged.

## Frozen inputs and exact admission

The public source is the University of British Columbia's
[SATLIB benchmark collection](https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html).
Selection was saved before download/evaluation: the first four CNF basenames in
lexicographic order from `uf20-91`, `uf50-218`, `uuf50-218` and `flat30-60`; the
first four `par8*.cnf` basenames in PARITY; and all five PHOLE files. This is a
size/family-limited convenience sample, not random or representative selection.
The parity selection includes both compact and larger encodings. The originals
range from 20 to 350 declared variables and 91 to 1,157 clauses.

For the first selected input in each archive group, a predetermined seed produces
one signed permutation; a second control deletes its first clause and flips the
first literal of its last nonempty clause. Those twelve controls are related to
six originals. Their derived status is explicit, including the renaming bijection.
Edited inputs do not inherit publisher truth labels. These first-of-group controls
do not test renaming stability of the two newly closed graph-colouring inputs.

`selection.json` predates all measurements; `acquisition.json` binds original URLs,
archive hashes, members and retained raw bytes. The algorithms receive only CNF
clauses. Family, filename, publisher answer and descriptions are separate audit
metadata. All certified answers agree with the applicable publisher labels, but
those labels supply no proof authority. There are no exact normalized duplicates
within the new panel or against the preceding 182-query panel. This is not an
all-history, semantic-equivalence or isomorphism novelty claim.

`cnf_external_cutsets.py` adds a strict DIMACS reader and a fixed-policy adapter.
The reader checks the header, declared variable range, clause count and complete
zero termination, preserving raw clauses and rejecting trailing data. It supports
SATLIB's legacy percent terminator with an optional final zero. Comments are
excluded from the solver input. The independent input audit parses all 37 raw
files with a separate cursor implementation, rejects 148 malformed variants and
checks exact literal bijections/clause multisets for all six renamed controls.

## Reuse and recomposition on previously unseen inputs

Both modes run the unchanged two-round selective-width pipeline from the raw
input. The expanded mode then uses the already-tested width-four-cover/cut-four
continuation on unresolved depth-zero leaves, in their stored order. It changes
no old limits, ranking rule, recognizer or scientific source. Initial certificates
are exactly equal between modes on every input.

The adapter reconstructs each frontier from its checked original-root context.
It rejects a still-unmaterialized wide frontier before constructing a truth table.
For admitted frontiers, it shares the old prefix and exact factor covers across
the complete Boolean cutset partition, with the earlier global projection budget
accounting intact. A model must lift through all earlier reductions and satisfy
the original external CNF. Further leaf attempts stop only after such a checked
root witness. Incomplete covers and branches remain explicit.

This adapter promotes only new SAT witnesses. A frontier UNSAT result does not
alone refute the original root. Whole-root UNSAT results still come from the
unchanged pipeline; a future UNSAT recomposition rule must discharge every parent
branch. The retained results contain one newly refuted frontier, but its root
still has unresolved alternatives, so transport alone would not close that gap.
There are at most four eligible leaves per root under the unchanged depth limit.

## Coverage by source group

These catalog groups describe provenance; they are not disjoint semantic SAT
classes or a new partition of all CNFs.

| Original source group | Inputs | Baseline certified | Expanded certified |
| --- | ---: | ---: | ---: |
| Uniform 3-SAT, 20 variables | 4 | 4 | 4 |
| Uniform 3-SAT, 50 variables | 4 | 3 | 3 |
| Unsatisfiable uniform 3-SAT, 50 variables | 4 | 4 | 4 |
| Flat graph colouring | 4 | 2 | 4 |
| Parity encodings | 4 | 4 | 4 |
| Pigeonhole encodings | 5 | 0 | 0 |
| **Originals total** | **25** | **17** | **19** |

The gains are `flat30-10.cnf` and `flat30-100.cnf` (`e013`, `e014`). Expanded
certificates prove 15 originals SAT and four UNSAT. The six unresolved originals
are `uf50-01000.cnf` and `hole6.cnf` through `hole10.cnf`. A renamed and an edited
`hole10` remain unresolved as well. Every source and its checked incomplete
certificate is retained in `remaining.json`.

There are 35 frontier attempts: two SAT, one UNSAT, 29 unresolved and three
rejected for unmaterialized clause width. Across materialized attempts, factor
classification returns 7,930 covers, 185 checked width-four obstructions and
15 budget-unresolved results. These count occurrences, not unique structures.
The 128 retained cofactor programs contain 13 SAT, 47 UNSAT and 68 unresolved
branches. Sixty stop at bag width and eight at reserved projection work. No limit
exhaustion is converted into an impossibility or UNSAT statement.

A revealing admission gap is that **184/185 obstructions and all 15 budget-open
factors have just one excluded assignment**: they are wide single-clause
relations. The general cover search spends effort rediscovering a simple local
representation restriction. The width-four obstruction excludes an exact CNF
cover on the same variables; it does not exclude auxiliary encodings, broader
relations, conditioning or a compact global capacity argument.

## Matched costs and limits

Four paired process orders start empty. All initial discovery, preparation,
expansion/internal checks, explicit checking, raw-source parsing, evidence writes,
compression, warm replay and two cold passes are charged. Every replay reparses
the source and loads the JSON certificate. The bounded verified-operator bank is
empty at the start of each phase; operating-system caches are not flushed.
Download/selection, process startup, final metadata and independent audits are
separate. Unlike the preceding frontier study, there is no excluded historical
root acquisition for these new inputs.

| Policy | Complete seconds | Acquisition/internal checks | Explicit checks | Warm | Two cold passes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 15.70674 | 8.63766 | 1.24696 | 1.78996 | 3.60378 |
| Expanded | 35.17482 | 15.75755 | 3.97464 | 5.01476 | 9.95976 |

Paired regressions are 130.41%, 119.87%, 124.52% and 121.34%. New JSON evidence
grows **24,587,244 → 30,653,233 bytes**, or **431,796 → 562,509 compressed**.
Peak RSS grows **112,361,472 → 132,907,008 bytes**; these are process observations,
not memory bounds. Acquisition and cold replay dominate. Pigeonhole originals
and their two controls consume **4.64803 s** of expanded acquisition versus
**1.19522 s** baseline, adding no root verdict. These phase totals include their
initial processing and checks; they are not isolated cover-search timings.

The graph-colouring originals consume 6.39656 s of expanded acquisition versus
2.98318 s baseline for the two gains. Full per-input costs, failure diagnostics,
counts and all paired timings are retained. No new native fallback archive is
created because there is no fallback in this evaluation.

## Checks and ranked next targets

All **2,447 full and 16 focused tests pass**, with no changed assertions or
deadlines. Existing unclosed-SQLite ResourceWarnings are retained.
Sixteen focused tests exercise malformed and legacy DIMACS, all two-variable
CNF reader round trips, SAT/UNSAT controls, fixed-policy binding, changed sources
and models, missing targets, wide-frontier admission and cold replay without
discovery. The complete test-suite and manuscript checks are in `checks.json`.
The validator independently checks all eight saved runs, regenerates deterministic
certificates and counters, and replays every warm/cold schedule. All 240 previous
manifests, 80,609 artifact entries, 1,312 scientific sources and 82 proof blocks
are preserved; the earlier 182/182 union is unchanged.

1. **Compact global capacity/injectivity structure.** Five of the six unresolved
   originals are pigeonhole inputs. Investigate a CNF-derived certificate for a
   demand exceeding available capacity, such as a checked matching/Hall-style
   deficiency core. Recognition must use clauses and variable incidence, never
   the filename; test renamed, edited and mixed controls. This is a proposed
   representation, not an implemented new authority or a general SAT claim.
2. **Cheap admission and heterogeneous factor descriptions.** Almost all observed
   noncovers are single-clause tables. Directly certifying their minimal width can
   avoid generic consequence enumeration, but will not itself close a root.
   Retaining wide clauses or other exact relations across conditioning may avoid
   requiring every factor to have a width-four cover. Charge any conversion,
   extra variables and inverse transport; smaller clause width alone is not
   smaller global interaction.
3. **Validated source/context reuse.** Rechecking complete old root contexts and
   preparing their frontiers repeatedly remains a credible cost target. Discovery
   and cold replay dominate this external workflow too. Exact bindings, ownership
   and invalidation must be preserved; the current measurement gives no estimate
   of an unimplemented optimization's savings.

Resume `experiments/results/cnf-external-cutsets/checkpoint.json`, key
`external_cutsets`. Keep this external denominator separate from the synthetic
panel and from the derived controls. Efficient universal classification,
nonconstant transfer across arbitrary structures and unrestricted expansion
bounds remain open.
