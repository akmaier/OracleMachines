# Selected-source bounded-learning pilot

9 November 2026. The 37 old sources were selected from the preceding signed-
equivalence archive: their chosen unresolved paths contain saved implications
without a path in the existing binary graph. `original_case` preserves source
IDs. This is a post-selected diagnostic, not a fresh holdout. The inventories
use depth two and four probe/conditioning candidates; the new policy adds at
most four proved binary clauses for one further bounded probe pass. A child
requires strict support decrease; unsuccessful learning attempts remain stored.

| Mode | Closed / 37 | Total seconds | SQLite bytes | Pattern nodes | Cold seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solving | -- | 1.22646 | 7,254,016 | -- | 0.37380 |
| Signed-equivalence baseline | 0 | 16.98242 | 53,002,240 | 4,560 | 7.88471 |
| Bounded learning | 1 | 19.27531 | 56,647,680 | 4,737 | 9.16931 |

The sole gain is **original case 1057**, an existing 48-variable 3-CNF. Logical
node bytes rise 27,423,700 -> 30,052,178. Warm inventory replay rises 0.01050 ->
0.01116 s. A separate allocation diagnostic on the first three selected sources
has Python peaks 3,340,408 -> 3,761,458 bytes; it excludes native SQLite memory,
RSS and whole-corpus peak. Ordinary solver residual count remains 1,170. All
three complete archives replay byte-identically. Times are single sequential
samples, without a significance claim. Targeted unit tests finished near the
start of the solver-only mode; the later full study runs timed modes without
concurrent test/build jobs and is the primary runtime comparison.

The [full study](../cnf-probe-learning/README.md) retains this pilot and measures
fresh random inputs and growing, signed and edited controls. The pilot provides
no evidence for a general runtime improvement or efficient arbitrary-SAT closure.
