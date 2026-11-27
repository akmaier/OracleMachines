# Exact semantic support in non-affine bucket relations

Date: 27 November 2026. Parent: `8fe48c30`.
Evidence: `experiments/results/cnf-semantic-buckets/`.

## Result and the remaining obstruction

Complete Boolean bucket elimination directly handles **2/6** distinct exposed
misses from the affine-boundary experiment and **18/24** newly frozen synthetic
constructions. Removing irrelevant boundary coordinates does not add decisions
beyond ordinary bucket elimination on this panel. The existing fallback decides
all 34 queries. These are acquisition-family counts, not new SAT answers that
were unavailable to the complete portfolio.

The concrete improvement is smaller intermediate relations: semantic support
removal reduces elimination steps **352 to 287**, retained output-table rows
**3,389 to 2,194**, and JSON proof bytes **45,268 to 39,607**. However, complete
runtime remains worse than the current solver. Ten acquisition misses all exceed
the width-eight cap **before their first elimination**, so compression applied
after a bucket cannot unlock them. This distinguishes a failure of recognition
order from a need to optimize later table operations.

## Exact recognition and recomposition

Each normalized source clause becomes its complete Boolean relation. For a
chosen variable, collect every active factor mentioning it and compute the exact
existential projection of their conjunction. The deterministic planner minimizes
bag width, then incident factor count, then variable name. It does not use family
labels, truth values or future timing results. Unknown width/work stops preserve
a partial checked program and give no verdict.

A coordinate is inessential exactly when its two cofactors agree on every row.
Discovery tests each coordinate and removes all inessential coordinates. The
resulting smaller table represents the same relation for every assignment to the
original boundary. The checker independently enumerates both eliminated-variable
values for each full boundary assignment and compares the reduced table with the
exact conjunction/projection. Every incident input must be present; omitting an
active factor invalidates the step. Each step removes a variable and introduces
none. A zero active relation proves UNSAT; SAT requires all active relations to
be true constants and a model satisfying the original source.

**Witness dependence is different from result dependence.** The projected result
of `x = y` is true for both values of `y`, but reconstructing `x` requires knowing
`y`. Choice tables therefore retain the full, unreduced boundary. During reverse
lifting, surviving variables have their later-stage values; disappeared free
variables default to false. The saved choice reconstructs the eliminated variable.
A control adds `[y]` and requires the lifted model `x = y = true`; discarding the
choice dependency fails verification. Result compression alone is not permission
to discard reconstruction information.

The shared variant keys an operator proposal by its local variable order,
eliminated position, reduction flag and sorted exact input scopes/tables. Thus
identically described subproblems with different external names can share a
proposal. General variable permutations, sign symmetry and semantic-equivalence
search are not implemented. Every cached proposal is fully checked before a
verdict; the cache is not a proof authority. Exact canonical source programs also
share within each stream, including partial programs at the same fixed policy.
Source edits invalidate them. A later larger-budget run must reacquire discovery.
Operator caching is local to a worker; its serialized diagnostic archive is not
loaded as a trusted persistent service.

The `cnf-semantic-buckets-v1` JSON authority is separate. Native, equivalence,
affine and Lean factor formats remain unchanged. Both existing native cold
readers audit fallback records; each cold pass additionally invokes the same
bucket checker. There are not two independent bucket-checker implementations.
All incoming warm and cold programs are fully checked. The measured discovery
allowance bounds reserved table probes on cache misses, not planning,
normalization, verification, leaf construction, runtime or RAM. Input leaf and
bucket widths are bounded before allocating their tables. All tables are complete;
missing or uncomputed rows never mean false.

## Frozen workload and controls

Freeze 24 constructions before implementation: random three-CNFs of 9/12/16/20
variables, disjoint and linked AND-gate groups, growing parity prisms, and gate
edits. They contain 20 SAT and four UNSAT inputs. Four exact repeated queries are
separate stream controls, all SAT. No normalized source duplicates the preceding
panel; these remain designed synthetic families, not representative external SAT
benchmarks. Six exposed development inputs contain four SAT and two UNSAT cases.
Descriptions and independent DPLL truth labels are withheld from solving.

Exhaustive two-variable formulas, all 256 three-variable Boolean tables, seeded
mixtures, sparse renaming, corrupted cache entries, omitted factors and dependent
witness choices validate the transformation. The verifier can cold-replay proofs
with both projection and support-discovery functions disabled.

Four cyclic process orders compare the current solver (`fresh`), complete tables
with unreduced scopes (`raw`), semantic support removal (`reduced`) and that same
removal plus operator caching (`shared`). All start empty and use the same
fallback. Recognition, checking, JSON/SQLite persistence, warm replay, both cold
passes and compression are charged. Interpreter startup, report metadata, panel
generation and final lineage audit are additional. Fixed policy is bag width
eight and 262,144 reserved discovery probes.

| Workflow | Discovery (s) | Solve/check (s) | Warm (s) | Cold (s) | Complete (s) | JSON proof bytes | Operator bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0.00000 | 0.08503 | 0.00822 | 0.05394 | 0.18233 | 0 | 2 | 55,050,240 |
| raw | 0.05019 | 0.07087 | 0.03214 | 0.09765 | 0.28389 | 45,268 | 2 | 54,001,664 |
| reduced | 0.04841 | 0.06963 | 0.03019 | 0.09402 | 0.27653 | 39,607 | 2 | 53,919,744 |
| shared | 0.04653 | 0.07171 | 0.02978 | 0.09298 | 0.27445 | 39,607 | 12,989 | 54,067,200 |

Support compression saves **18.47% steps**, **35.26% retained relation rows** and
**12.51% JSON certificate bytes**. Of 328 removed coordinates, **306 come from 200 constant-output steps** and only **22 from 21 nonconstant steps**. The saving is dominated by constant relations; there is no constant-only ablation, so the full cost benefit cannot be attributed to nonconstant support recognition. Full witness-choice rows decline only
**3,389 to 3,034**, following the shorter elimination sequence; they are not
shrunk to the result's 2,194 rows. Relation bytes and runtime must not be inferred
from the output-row reduction alone.

Mean complete time falls 2.59% from raw to reduced, but one paired order regresses
0.26%. Shared saves another 0.75% on the mean; one paired order regresses 8.03%.
These short, mixed-sign comparisons do not establish a robust runtime improvement.
Shared records 164 operator hits and only 123 misses, but full checking still
performs 64,284 table probes in the acquisition/solve phases. Discovery probes
fall 19,047 to 17,188 versus reduced; verification is not bypassed. Shared and
reduced certificates are byte-identical.

**Shared remains 50.53% slower than fresh**, and every paired comparison regresses
38.51–62.12%. The current solver remains selected. All bucket variants leave the
same 124,836 bytes of SQLite proof records, versus 182,007 fresh. Combined raw
SQLite/JSON/operator encodings occupy 170,106 bytes raw, 164,445 reduced and
177,432 shared (the empty operator list is two bytes). Their compressed packages
are 34,352, 32,925 and 34,882 bytes, versus 39,737 fresh. Operator caching therefore
undoes the storage benefit relative to reduced and even exceeds raw's package.
Diagnostic bytes are 1,255/1,253/1,245 and are additional, as are historical data,
repeated reports and database/container overhead. RSS changes little across the
bucket arms; no peak-memory reduction follows from the table-row count.

## Next priority

The remaining four exposed and six new random-three-CNF inputs all stop at the
initial bag-width check, with zero reserved projection work. Increasing the table
cap would expose an exponential width cost, not explain the structure. Next test
small factor combinations or conditioning **before** full incident-bucket
elimination, with exact recomposition, recognition cost and another reserved
panel. Such a step might expose smaller semantic support before the large bucket
is formed. This is a hypothesis, not an implemented win. Keep the present wide
cases as regression controls. Their fallback verdicts remain available.

The full choice-table requirement and cold-check cost are additional limits for
reuse: sharing result tables does not automatically share model reconstruction
or proof checking. No production integration is selected, and no general bound
on CNF width, compact closure or polynomial unrestricted-SAT solving follows.

Resume `experiments/results/cnf-semantic-buckets/checkpoint.json`, key
`semantic_buckets.remaining`. Prior 224 manifests, 35,821 artifact entries,
1,233 sources and all 66 earlier proof blocks remain unchanged. Five new source/
test files raise the source ledger to 1,238. One restricted support/lifting proof
is added; earlier regressions and all new comparison arms remain preserved.

Validation: **2,242 full tests and 21 focused tests pass**. The audit replays all sixteen measured arms, complete/partial JSON programs, operator cache proposals and two unique SQLite archives. All prior artifact/source hashes and 66 earlier proofs remain unchanged. Existing unclosed-SQLite ResourceWarnings are retained in the full log; focused tests have none.
