# Causal trace slicing before native proof expansion

Checkpoint: 26 November 2026. Native conversion now removes unit-trace steps
that do not contribute to the checked contradiction, reusing a dependency-closed
slice whenever the same bank trace is expanded again. This targets the previous
checkpoint's dominant measured cost. On `(37,39)`, it reduces native records from
**5,587 to 76** with the same source-unit shortcut budget. Both independent cold
readers accept the source-only result. The earlier `(67,63)` snapshot also remains
certified. **Coverage stays 234/246, with twelve unresolved snapshots**; this is a
construction improvement, not discovery of a new SAT class.

## Identified structure and correctness

Unit propagation records assignments as it traverses the bank, including branches
that never influence the final conflict. The old native compiler turned these
irrelevant steps into source splits and recursively expanded their reasons. Each
split can create another restricted source context, so a modest number of extra
trace steps can produce many more native records and expensive cold checks.

The new compiler applies the existing backward causal slicer to each checked bank
trace before expanding it. Start with the variables of its conflict clause. Walk
the trace backwards; keep a unit only when its variable is needed, replace that
variable by the other variables of its reason clause, and continue. Remaining
initial dependencies must be contained in the failed assumption, or empty for an
unconditional trace. The kept steps retain their original chronological order and
clause IDs. Every discarded step is irrelevant to the retained contradiction.
This is dependency closure, not an algorithm for finding a minimum proof or core.

Soundness follows directly from the checked trace. Induct over retained steps:
all other literals of a kept reason are falsified by the initial assumption or
previously retained assignments, so that reason still forces its recorded unit.
The final retained assignment falsifies the same conflict clause. All earlier
provenance is checked before slicing. Native conversion then follows exactly the
previous rule: split the restricted source, justify each excluded branch through
a strictly earlier bank, and publish only ordinary source-only records. Direct
source-unit shortcuts and both independent native readers retain their checks.
No slice, asserted open probe or augmented clause becomes independent authority.

The memo belongs to one compile call with an immutable prepared bank sequence.
Its key includes the bank stage, failed assumption, exact ordered unit trace and
conflict clause. Identical clause numbers from different stages do not share a
slice. The same trace under different stronger conditioning contexts can reuse its
slice because the slice was established under the original failed assumption;
each native context and record is still separately checked. A new call builds a
new memo, and warm root hits still revalidate the incoming source, prefix, closures
and all histories. Changed inputs cannot inherit a trusted slice from an old call.
Key construction and memo lookups are counted, and peak process memory is measured.
For one trace, slicing visits each trace step once and scans the reason literals
of retained steps. Its work is linear in those explicit trace/reason payloads
under ordinary set-operation assumptions. Constructing a memo key still visits
the whole offered trace, including on a hit. The memo retains keys and slices
for unique traces until compilation ends; it does not bound how many native
conditioning contexts or stored clauses the subsequent compiler will generate.

## Why the shortcut budget matters

The preserved full compiler on `(37,39)` builds 12,251 prepared frames, publishes
5,516 splits, tries 93 direct unit closures and skips 6,671 further candidates
because its global allowance is exhausted. It checks and serializes a 77.50 MB
native graph. Slicing examines 993 unique trace steps, retains 467, and records 17
memo hits across 37 trace expansions. It builds 81 prepared frames, publishes
39 splits and closes 35 contexts directly, without exhausting the same budget.
All exact counters, including 1,664 steps visited while constructing memo keys,
are retained in the reports.

This is an interaction between dependency pruning and bounded direct closure.
An ablation increases the full compiler's shortcut allowance eightfold, from
262,144 to 2,097,152. It reduces the main case to 146 records without slicing.
Therefore the full 5,587-to-76 reduction must not be attributed to removing trace
steps alone. Slicing still reaches fewer records with the original allowance.
Neither approach gives a worst-case size bound for the native graph.

## Matched measurements

Four balanced cyclic mode orders run in separate processes on each of two already
certified frontier snapshots, before heavy tests and lineage audits. Every mode
occupies each order position once. `full` and `sliced` use the same shortcut work
limit 262,144 and trace limit 256; `full_large` changes only the work limit to
2,097,152. `fresh` uses the existing solver with node limit 256. The older-case
baseline here is the generic compiler with its checked zero-round saturation
trace; it need not have the same graph as the earlier B13-specific compiler.

| Snapshot | Mode | Construct (s) | Warm (s) | Cold readers (s) | Persist (s) | Complete (s) | Records | Record bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| (37,39) | full | 22.34315 | 0.04141 | 23.02682 | 6.93664 | 52.71934 | 5,587 | 77,497,609 |
| (37,39) | sliced | 0.31849 | 0.03704 | 0.32378 | 0.11460 | 0.79748 | 76 | 1,560,875 |
| (37,39) | full_large | 0.60211 | 0.03816 | 0.60852 | 0.26071 | 1.51482 | 146 | 2,826,494 |
| (37,39) | fresh | 0.31018 | 0.00279 | 0.32617 | 0.12941 | 0.77409 | 88 | 1,543,539 |
| (67,63) | full | 0.34192 | 0.02542 | 0.35197 | 0.11996 | 0.84336 | 118 | 1,674,855 |
| (67,63) | sliced | 0.32849 | 0.02573 | 0.37470 | 0.11765 | 0.85274 | 107 | 1,521,056 |
| (67,63) | full_large | 0.34350 | 0.02528 | 0.35281 | 0.11963 | 0.84551 | 118 | 1,674,855 |
| (67,63) | fresh | 0.26679 | 0.00208 | 0.26698 | 0.08865 | 0.62960 | 95 | 1,256,004 |

On the main case, slicing reduces complete time **98.49%** and raw record bytes
**97.99%** relative to full expansion at the same budget. Peak RSS falls **91.52%**.
Against the eightfold-budget ablation it is **47.36% faster** and stores **44.78%
fewer raw bytes**. It remains **3.02% slower** and **1.12% larger** than fresh
solving in raw bytes; its compressed archive is smaller.

On the earlier case, slicing saves **9.18%** of raw bytes but is **1.11% slower**
overall than full expansion. That small runtime regression is retained. It is
**35.44% slower** and **21.10% larger** than fresh solving. Four repetitions do not
establish significance for small timing differences. Fresh is the lowest measured
complete-time route on both snapshots; there is no production-default change.

| Snapshot | Mode | Peak RSS (bytes) | Compressed archive (bytes) |
| --- | --- | ---: | ---: |
| (37,39) | full | 967,245,824 | 8,524,365 |
| (37,39) | sliced | 82,018,304 | 153,770 |
| (37,39) | full_large | 97,435,648 | 345,779 |
| (37,39) | fresh | 80,576,512 | 189,777 |
| (67,63) | full | 81,969,152 | 164,521 |
| (67,63) | sliced | 79,872,000 | 151,881 |
| (67,63) | full_large | 81,969,152 | 164,521 |
| (67,63) | fresh | 72,990,720 | 126,513 |

Times include original-bank validation and slicing in construction, database
handling, a warm call, both cold readers and compressed persistence. Warm compiler
calls recheck provenance; fresh warm calls invoke the solver again. Historical
acquisition, discovery, input loading and final lineage audits remain additional.
They are complete measured native workflows, not total lifetime costs. The two
selected cases establish neither typical behavior nor cross-category dominance.

Fresh solving remains a necessary comparison. Record count alone does not predict
retained bytes: native keys and payloads repeat each residual's clauses. Even a
smaller node count can carry larger residuals. Reusing a shorter proof is useful
without guaranteeing that reconstruction beats fresh solving on every case.
All four arms, pilot results and intermediate evidence are retained.

## Validation, preservation and next step

Resume `experiments/results/cnf-sliced-saturation/checkpoint.json`, key
`sliced_saturation.remaining`, through the preceding saturation module's
`load_frontier`. The remaining binding and all twelve rows are unchanged. New
supplemental archives certify already known roots; no additional coverage is
claimed and no old certificate or cumulative authority table is rewritten.
All 1,199 previous source fingerprints and 32,817 artifact entries in 217 manifests
remain unchanged. Four new science/test files bring the source ledger to 1,203.

Validation includes 2,183 full tests and 22 focused tests, both cold archive
readers, independent checks of sliced new-bank traces, warm corruption rejection,
assumption-independent conflicts and identical clause indices across different
banks. Truth-table checks start from every subset of the eight two-variable
unit/binary clauses plus 70 seeded five-variable inputs, retaining only cases with
valid interrupted lower histories. Growing disjoint mixtures exercise both shortcut
settings and repeated construction. This is not exhaustive larger-CNF coverage.
All 64 prior manuscript proof blocks remain byte-identical.

The first focused-test import hit Python's recursion limit in the frozen historical
module chain. Loading its existing base module before the chain fixes import
nesting without changing old sources or solver behavior. The failed log and initial
comparison source are retained; the correction preceded the declared trials.

**Next priority:** return to coverage and characterize shared-variable interactions
or bounded conditioning/decomposition in the twelve exhausted fixed points. The
large avoidable native expansion is reduced on these examples. Remaining native
costs include repeated whole-residual payloads and cold checking; compare support
selection or shared representation only with exact recomposition and a fresh-solve
baseline. Uniform acquisition, compact closure and efficient solution of every
arbitrary CNF remain open.
