# Finer proof origins do not necessarily reduce expansion

The previous diagnostic found a finer branch in an earlier recomposed proof.
We now admit selected completed recompositions into the live origin bank and
measure their use on subsequent queries. The finer cover is selected, but it
does not avoid native acquisition. Dispatches remain at 32, while preparation
plus query takes 2.39% longer, hints grow 45.89%, and native payload grows 1.13%.
Retain this failed policy as an optional experiment, without changing defaults.

## Admission and exact reuse

The policy proposes an origin only after a completed partial-cover query used
at least two native expansion dispatches. It checks that the committed root is
negative, validates its source-name map and copies the supplied outer guard.
Positive results, stopped queries, missing roots, duplicate entries and cheaper
recompositions do not enter the bank. The two-dispatch threshold is a heuristic,
not a bound on future savings or a requirement for correctness.

Admission is lazy. An entry initially contains only its native origin, variable
map and guard. Existing limits remain sixteen entries and 262,144 serialized
bytes, with oldest-first eviction. Eviction removes hints, never native proofs.
On a later eligible query, existing bounded extraction, complete-cover matching
and partial-cover selection determine whether the entry can be used. At most
four eligible candidates are examined. The partial rank still prefers fewer
missing leaves, then more intact leaves, then the oldest candidate.

An admitted root cannot influence the query that produced it. The query log
records admission after completion; independent replay checks that each reused
origin precedes its target. Every source containment, path assumption, branch
composition, native certificate and lifted SAT witness retains its existing
check. The native and hint formats are unchanged. This changes origin selection,
not proof authority or the semantics of SAT.

For a source with L literal occurrences and v variables, map validation and
reconstruction add sorting/set work on the names and a traversal of the source.
Admission also scans the bounded bank and serializes it for the byte cap.
These costs and integer/key sizes remain charged. The serialized hint cap is
not a cap on total process memory, discovery time or the append-only proof
archive. Lazy extraction still has its own node/literal budgets and can fail.

## Matched results

Three policies use the same historical prefix, donor, 23 sources and six
supplied guards in four alternating serial orders: 1,656 conditional queries.
Each worker returns 125 UNSAT and 13 SAT results. No generator label, case ID
or future result enters admission. These exposed workloads motivated the
heuristic; they are not a fresh holdout or a general SAT distribution.

| Mean per worker | Native baseline | Previous handoff | Refined origins |
| --- | ---: | ---: | ---: |
| Preparation + query, seconds | 0.393080 | 0.395584 | 0.405040 |
| Native expansion dispatches | 55 | 32 | 32 |
| New native payload, bytes | 1,551,836 | 1,508,442 | 1,525,496 |
| Active hints, bytes | 11,505 | 42,031 | 61,318 |
| Selected retained Python state, bytes | 8,460,643 | 8,337,127 | 8,439,124 |
| Complete worker, seconds | 3.277047 | 3.304886 | 3.283433 |

Preparation/query changes against handoff are +6.19%, +1.70%, +3.31% and -1.37%
across the four pairs. Complete-worker mean is 0.65% lower, with two faster and
two slower pairs. The mixed full-worker timing does not establish a consistent
overall improvement. The added hint bytes, proof payload and selected endpoint
state are deterministic in all repeats. The latter grows by 101,997 bytes,
or 1.22%; it is not a peak-memory measurement.

Compressed proof deltas fall slightly, from 138,342 to 138,070 bytes, despite
larger uncompressed payload. Compression can benefit from repeated proof
structure while acquisition, checking and logical storage increase. It should
not be substituted for those costs.

| Query | Result | Baseline ms | Handoff ms | Refined ms |
| --- | --- | ---: | ---: | ---: |
| 7 / guard 4 | SAT | 8.984 | 14.289 | 14.547 |
| 15 / guard 3 | UNSAT | 15.621 | 21.178 | 22.210 |
| 19 / guard 3 | UNSAT | 16.437 | 12.572 | 20.638 |
| 20 / guard 3 | UNSAT | 21.620 | 18.268 | 19.184 |

Cases 15 and 20 become lazy origins. Case 7 remains positive and is rejected;
case 19 costs one expansion and is skipped. The new case-15 cover is extracted
and selected for cases 19 and 20. Case 19 retains three of four leaves rather
than two of three, but its one missing residual is unchanged. It pays for cold
extraction and more recomposition work. Case 20 has two missing leaves under
both covers; its slightly smaller branch still needs two native dispatches,
and the other needs one. The intended reduction in acquisition does not occur.

Across the stream, native missing leaves remain five. Published support leaves
rise from six to eight, split publications from six to eight, and cover
extractions from two to three. Native verification count rises from 197 to
199. There are 7,939 additional normalization literal visits and 45,422
additional key-serialization bytes. New admission validates 1,596 source
literals. Combined cover-phase mean rises from 32.50 to 37.66 ms. Timed workers
finish before diagnostic profiling and audits; profiled cumulative times
overlap and are excluded from the comparison.

## Consequence for the next investigation

More intact leaves are not necessarily more useful reuse. A refinement may
subdivide branches already supported while leaving the expensive unresolved
computation intact. Even a smaller unresolved formula may take the same search
steps and require additional certificates. A future cost model should compare
the remaining computations and the work needed to construct their certificates,
not rank candidates solely by intact-leaf counts or formula size.

This concludes the narrow finer-origin experiment. Return to discovery on
unlabelled whole CNFs: freeze fresh seeds for the existing larger-mixture
generators, record novelty against the preserved archive, and compare cold
discovery with subsequent reuse on base/edit/repeat streams. Inspect the current
automatic guard recognizers before adding another one. Select the largest
remaining shared-variable interaction under matched budgets, then test a
checkable decomposition without supplying its guards in advance. Preserve
explicit unknowns and all recognition/recomposition costs.

All current conditional inputs were already solved by the baseline. The new
origins add no whole-CNF coverage cell or uniform efficient construction for
arbitrary SAT. Automatic useful guards, variable correspondence and compact
reusable closure remain open.

Nine new tests cover lazy admission, source and guard binding, positive/missing
root rejection, budget stops, small acquisitions, eviction without proof loss,
both cold readers and all 256 deletions of the three-variable exclusion cube.
The full suite passes 1,611 tests and the focused suite passes 102. A development
test initially assumed a two-variable contradiction would need multiple native
dispatches; native binary reasoning closes it in one. The preserved failure was
corrected by using a three-variable contradiction for that admission fixture.
Raw evidence is retained in `experiments/results/cnf-refined-origins/`.

Independent validation checks all 1,656 comparative queries, twelve extracted
bundles, 76,506 cumulative native records, unchanged extension tables and 342
prior partition records. Five new native identities are appended; every prior
authoritative payload and alternative valid proof is preserved. All 13,273
prior artifacts across 150 manifests remain unchanged. The new seal binds
857 source files and 88 artifacts, bringing the record to 151 manifests and
13,361 artifacts. The full suite retains 44 existing unclosed-SQLite warnings;
the focused suite has none. The manuscript builds to 249 pages without
LaTeX/layout warnings and retains its 64 existing proof environments.
