# Reuse a clause-cover proof through its selected source support

Updated 2026-11-24. This follows [learned-guard clause covers](guard-clause-covers.md).
The improvement addresses their measured duplication of full local CNFs. It is
an optional proof compiler, not a change to live search or a minimum-cost solver.

## Construction and reuse conditions

For a checked cover of an actual source clause C, form H from C, every original
binary clause used by its paths, and the actual source clauses supporting every
selected learned edge. Check membership, guard traces, path transitions and the
identity of C before publishing anything. H is a subset of the enclosing CNF F;
the chosen guards remain consequences of H, so the same cover refutes H.

Normalize H, transport its selected guards and paths into those compact
coordinates, and compile with the frozen native cover compiler. Publish one
existing negative `component` certificate from F to that checked root. H need
not be an independent component: extra clauses may share its variables. The
wrapper is a negative subset lift, not a positive component join.

Reuse requires the exact normalized support key and a successful native proof
read. Changing or deleting a required source clause invalidates membership;
changing F outside H preserves the negative lift but requires a new wrapper.
Variable names and clause indices are recomputed for each enclosing input.
The implementation handles order-preserving renaming, not arbitrary semantic
or graph isomorphism. If H equals F, it uses the frozen full-context compiler.
If a path or guard assumption names a coordinate absent from H, it also falls
back explicitly; it does not invent a coordinate map for an absent variable.

Let S_F and S_H count source and selected-support literal occurrences, and let
q be cover width plus total path length. In the successful subset branch, the
explicit native proof content has an O(q S_H + S_F) word-size envelope instead
of O(q S_F), including full child keys. This is not a physical RAM bound. Node
counts can increase when full-context coincidences disappear. With one fixed
checked H reused across F_1,...,F_k, the corresponding retained content has an
O(q S_H + sum S_F_i) envelope. Every new wrapper still stores its enclosing CNF;
source scanning, recognition, normalization, lookup, verification and persistence
remain real costs. Neither H nor its paths are claimed to be globally minimal.

## Coverage and matched local comparison

All seven previously unverified relaxed-budget proposals have valid source
supports and distinct roots. Together with the previous 11 distinct roots,
there are 18 local cases. Ordinary search already retains every root after the
original query. All 22 proposals, including four duplicate roots, remain in the
record. There is no new whole-query completion and no change to the eight
unresolved query results.

The comparison uses fresh isolated workers, empty stores and two alternating
serial repetitions for ordinary search, the frozen full-context cover compiler,
and the support compiler. It tests all 18 local cases and eight controlled cases;
156 workers are preserved. All authorities, including equivalence certificates,
are checked by both existing snapshot readers. The original 11 ordinary/full
controls reproduce the preceding native database bytes exactly.

| Sum of per-case means, 18 local CNFs | Ordinary search | Full-context cover | Selected-support cover |
| --- | ---: | ---: | ---: |
| Solve/compile seconds | 0.48743 | 0.77840 | 0.19227 |
| Complete-worker seconds | 1.36568 | 2.01897 | 0.56481 |
| Cold verification seconds, both readers | 0.61811 | 0.94938 | 0.28269 |
| Stored records across six tables | 178 | 275 | 290 |
| Record bytes, keys plus payloads | 2,100,503 | 3,179,203 | 440,066 |
| SQLite bytes | 3,919,872 | 5,001,216 | 942,080 |
| Compressed archive bytes | 279,080 | 324,368 | 75,358 |

Compared with full-context compilation, solve/compile time falls 75.30%,
complete-worker time 72.03%, and record bytes 86.16%. Records increase 5.45%;
smaller bodies, not fewer records, explain the saving. The supports contain
1,534 of 18,631 enclosing literal occurrences. The sum of per-case mean peak
RSS falls only about 4.51%. That is not a simultaneous peak, and the logical
record reduction must not be presented as the same reduction in process RAM.

Per-case discovery and independent source binding add 0.14476 seconds to the
support arm across the 18 unique contexts, giving 0.33703 versus ordinary
search's 0.48743 seconds. This comparison still excludes earlier acquisition,
discovery misses, process startup and shared orchestration. On the original
11-case subgroup, adding those measured costs gives 0.21138 versus 0.17884
seconds for ordinary search: that subgroup still regresses. The seven newly
checked cases give 0.12565 versus 0.30859 seconds. Do not turn the combined local
saving into a live whole-query claim.

The eight controlled cases use supplied width-3/6 cores with 0/16/64/256 extra
clauses that share a core variable. Support compilation reduces record bytes
from 194,789 to 71,044 relative to full-context composition, but takes 0.05406
seconds versus ordinary search's 0.02949. Its complete-worker total is 0.17346
versus 0.17069 seconds. The two unpadded cases use the full-support fallback.
These regressions remain part of the comparison.

Complete-worker timing includes input loading, setup, solve, repeated-root
checking, both cold readers, accounting and archive compression. Imports and
process startup, common proposal preparation and earlier origin acquisition
remain additional. These short experiments provide measured local evidence,
not stable production ratios or a universal runtime guarantee.

## Persistent expansion without recompiling the core

A separate append-only stream starts from an empty store and closes/reopens it
between all eight controlled contexts. Both arms see the same order. Six padded
contexts reuse a saved support root; each inserts exactly one wrapper and no
new core proof node. Every earlier row remains byte-identical, and every archive
is replayed with both readers.

| Eight-context stream | Full-context cover | Selected-support cover |
| --- | ---: | ---: |
| Solve/compile seconds | 0.06721 | 0.01778 |
| Complete-worker seconds | 0.23051 | 0.05084 |
| Final records | 70 | 25 |
| Final record bytes | 143,234 | 25,737 |
| Final SQLite bytes | 286,720 | 61,440 |

This is exact support reuse across changed contexts, including cold proof reads.
It does not remove wrapper growth, recognize arbitrary equivalent cores or
shrink previously published history. All new alternatives remain in supplemental
checkpoint-linked archives; the existing cumulative bank is preserved unchanged.

## Next discovery gap: partial clause shortening

The preserved six-variable example has four ternary gadget clauses proving two
binary guards, `(not x or a)` and `(not x or not a)`. Their satisfiable graph
forces only `not x`. Add all four source clauses `(x or +/-y or +/-z)`. No wider
source clause is entirely excluded by the existing graph, so both the guard SCC
gate and the current clause-cover detector remain inconclusive. Conditioning
on the checked `not x` leaves the four contradictory binary clauses on y,z.

All 16 subsets of those four wider clauses are checked over all 64 assignments:
only the full set is UNSAT. This is an elementary recognizer separation, not a
failure of ordinary solving or a new complexity result. It motivates an exact
extension that shortens source clauses using checked forced literals, adds the
resulting binary consequences with their supports, and repeats closure. Reuse
proofs for the forced literals and selected supports; do not treat a conditioned
consequence as unconditional without the appropriate source proof.

Next inventory that pattern on unresolved contexts and fresh mixtures. Charge
source scanning, reachability, iteration, support maintenance, compilation and
cold replay. Automatic acquisition and a uniformly efficient partition of all
CNFs remain open. The new support compiler stays optional pending live tests.

## Validation and continuation

All 1,815 solver tests and 45 focused tests pass; the full run retains the 43
existing SQLite ResourceWarnings and the focused run has none. Tests cover
sparse support coordinates, signed renamings, overlapping source clauses,
missing evidence, changed wrapper indices, absent-coordinate fallback,
exhaustive small graph families and persisted reuse after reopening.

Preservation checks 172 prior manifests, 16,947 artifact entries and all 1,000
previously frozen sources. Eighty-nine distinct supplemental archives are
independently audited. The 160,338-record cumulative native bank, five other
tables, prior supplemental banks and all 64 previous manuscript proof blocks
remain unchanged. Resume `experiments/results/cnf-cover-support/checkpoint.json`;
its new banks supplement, rather than replace or automatically seed, causal
search history. The preflight harness draft is retained: it was corrected to
allow capped ordinary results before any timed worker, though all 26 measured
cases ultimately finish.
