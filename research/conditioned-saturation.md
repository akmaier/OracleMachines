# Conditioned saturation closes nine retained fixed points

Date: 26 November 2026. Parent checkpoint: `5bbcc2de` (causal saturation slicing).
Evidence: `experiments/results/cnf-conditioned-saturation/`.

## Pattern and exact recomposition

The twelve retained B13 feedback banks are fixed points for the current flat
failed-literal saturation rule. Conditioning on one variable before applying that
same rule exposes additional interactions. The bounded search tries at most
sixteen distinct, unfixed variables in the frozen source occurrence order. For
each pivot `v`, it checks saturation separately on `B ∧ ¬v` and `B ∧ v`.
Nine snapshots have a pivot whose two branches refute. Their reconstructed
original-source certificates pass both cold readers: structural coverage rises
**234/246 → 243/246**, leaving three open frontier rows.

The partition is exact for every Boolean CNF: every assignment belongs to exactly
one of the two branches. If both branches are unsatisfiable, their parent is
unsatisfiable. If only `B ∧ l` refutes, the valid conclusion is `B ⇒ ¬l`.
An exhausted or interrupted branch supplies no SAT verdict. The partition rule
covers all assignments; this bounded implementation does not solve every cell.

This strictly strengthens the flat rule even without acquired banks. The eight
clauses excluding every assignment on three variables have no flat failed-literal
unit contradiction. Conditioning on one variable leaves both two-variable
branches refutable by that rule. Conversely, gating the four-clause two-variable
contradiction with a third literal gives a satisfiable formula with only one failed
branch. Tests retain both examples.

Recognition binds the exact canonical seed, variable coordinates, frozen ordering,
pivot, branch sign and trace bound. Both child traces are checked. Resume first
checks the entire saved record; it reuses completed child results and continues
interrupted searches only under those bindings. An edited seed, swapped branch,
different pivot or incompatible bound invalidates reuse. Duplicate clauses,
tautologies and clause permutations use the kernel's existing canonical seed.

Native reconstruction retains the preceding causal slicer. It inserts the local
condition into the last acquired bank, preserving all older bank indices, and
expands every derived reason back to the original source. The branch's assignment
is present in every recursive context. It cannot justify its own excluded context:
the compiler explicitly rejects a condition-origin leaf. Each branch owns its
slice memo; the parent combines the two source residuals with an ordinary native
split and reconstructs the original prefix. No new certificate format is added.
Every warm hit still checks incoming source, prefix and provenance first.

The split is a semantic identity. Recognition, acquired-bank construction, proof
expansion and the number of future splits remain charged separately. Recursing
this rule without a depth or width restriction may enumerate exponentially many
contexts. Nothing here supplies a uniformly polynomial constructor, compact
closure, or efficient solution for every CNF.

## Discovery, reuse and retained state

Six fresh-process permutations of `flat`, `conditioned` and `resume` cover the
same twelve unlabelled snapshots. All use per-call bounds of eight rounds, 512
probes, 2,097,152 work units and trace length 256. Conditioned search makes up to
two calls per pivot; these are **not equal total search budgets**. The experiment
was developed on this retained frontier and is not held-out generalization.

| Mode | Prepare (s) | Discover (s) | Cold check (s) | Persist (s) | Complete (s) | Result bytes | Peak RSS (bytes) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Flat | 0.16362 | 0.03882 | 0.18691 | 0.00642 | 0.39602 | 236,393 | 58,687,488 |
| Conditioned | 0.16308 | 0.81985 | 0.85189 | 0.08027 | 1.91544 | 5,264,828 | 85,704,704 |
| Resume | 0.16339 | 0.95479 | 0.83245 | 0.07841 | 2.02939 | 5,264,828 | 90,177,536 |

Flat repeats 2,062 probes without a new failed assumption. Conditioned search uses
62 pivots, 124 branch calls and 39,474 probes, finding nine paired refutations.
Resume avoids 768 probes (38,706 instead of 39,474) but takes **5.95% more complete
time**, with the same final result bytes and higher peak RSS. Its separately
acquired first-pivot records cost another 0.24041 s and 594,758 bytes. Preserve
this regression; saved search work alone does not justify a reuse policy.

Complete discovery time includes checked seed preparation, search, serialization,
reload and independent cold reconstruction/checking. JSON input loading, original
snapshot binding, historical acquisition and final lineage auditing are additional;
the protocol records the first acquisition and original binding (0.19174 s across
the twelve cases) separately.
Discovery and checking each account for about 43–44% of conditioned cost. Neither
may be omitted when evaluating a cheaper recognition or reuse strategy.

## Native conversion versus fresh solving

Two opposite mode orders compare every successful pair against the existing fresh
solver with its 256-node limit. Both routes refute all nine snapshots. The table
reports means including construction, a warm call, both cold readers, database
handling and compressed persistence. Discovery above and historical acquisition
are additional. Each compiler branch has its own 262,144 direct-unit work allowance,
so the combined allowance is at most 524,288. Fresh uses a different algorithm.

| Snapshot | Fresh complete (s) | Conditioned complete (s) | Fresh records | Conditioned records | Fresh bytes | Conditioned bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| (1,0) | 1.25235 | 1.20289 | 174 | 124 | 2,449,870 | 2,145,582 |
| (1,15) | 1.36218 | 0.76600 | 195 | 81 | 2,793,577 | 1,358,052 |
| (28,17) | 0.34717 | 0.39607 | 106 | 86 | 678,652 | 616,970 |
| (61,21) | 0.25046 | 0.43053 | 59 | 81 | 457,649 | 709,833 |
| (61,51) | 0.60459 | 0.68954 | 157 | 97 | 1,177,901 | 880,839 |
| (61,52) | 0.37035 | 0.47166 | 93 | 92 | 679,023 | 783,487 |
| (61,60) | 0.30682 | 0.26814 | 76 | 45 | 549,202 | 383,607 |
| (61,61) | 0.29564 | 0.28390 | 75 | 47 | 539,140 | 399,342 |
| (61,74) | 0.30199 | 0.20561 | 76 | 29 | 562,635 | 262,474 |
| Total | 5.09154 | 4.71433 | 1,011 | 682 | 9,887,649 | 7,540,186 |

Conditioned conversion saves **7.41%** aggregate native-workflow time and **23.74%**
raw bytes, but is slower on four of nine cases. Two repetitions do not establish
significance for small differences. Its 0.37720 s aggregate saving is smaller than
the additional discovery census, so this is not a demonstrated end-to-end win over
fresh solving. All fresh and conditioned certificates remain; the overlay selects
the cheaper measured certified native workflow per snapshot, without changing
production defaults or hiding discovery costs.

Summed native construction, warm, cold-check and persistence times are respectively
2.02663, 0.30948, 1.76302 and 0.58773 s for conditioned reconstruction, versus
2.14760, 0.01414, 2.14264 and 0.74288 s fresh. Warm compiler reuse still reconstructs
and validates histories, explaining its much larger warm cost. Maximum process
RSS is 91,979,776 bytes conditioned and 97,665,024 fresh; compressed archives total
809,301 and 1,064,528 bytes. Per-case RSS and all phase samples are retained.
These process peaks are not lifetime storage bounds.

All conditioned archives use only `cnf_residual_v1` authority. Fresh `(61,21)` also
uses one independently checked `cnf_binary_equivalence_v2` record; its 59-record
total includes that record. The first audit incorrectly required exclusively
residual authority for the fresh solver too. The failed assertion and validator
are retained; the corrected audit checks this exact exception and both readers.
An earlier pilot used an old input helper restricted to two targets and raised
`StopIteration`; the preserved correction uses the broader original input reader.
Neither correction changes the measured kernels or their results.

## Remaining interactions and continuation

| Snapshot | Pivots checked | Failed branches | Combining their implied units |
| --- | ---: | ---: | --- |
| (61,0) | 16 | 9 | Checked augmented-bank contradiction |
| (61,50) | 16 | 2 | Two more assignments; 334 → 314 residual clauses |
| (67,0) | 16 | 10 | Checked augmented-bank contradiction |

The two contradictions combine information across different pivots. No single
tested pivot has both branches refuted. **They remain candidate refutations until
source-only reconstruction and both native readers pass**; coverage remains 243,
and all three rows retain every prior field. The analysis saves the derived units,
joint traces and remaining closure, so later work need not rediscover them.

Next compile these cross-pivot implications with their exact branch premises;
compare against fresh solving before selecting a representation. Then condition
or saturate the strengthened `(61,50)` bank. Its 30 open branch fixed points are
not SAT certificates. For cost, avoid rechecking unchanged bank construction and
duplicating branch seeds only with explicit ownership and invalidation conditions.

Resume `experiments/results/cnf-conditioned-saturation/checkpoint.json`, key
`conditioned_saturation.remaining`, with this comparison module's `load_frontier`.
All 1,203 prior source fingerprints and 32,919 artifact entries in 218 manifests
remain unchanged; five new science/test files bring the source ledger to 1,208.
All older certificates, cumulative tables and 64 manuscript proof blocks remain.
Validation comprises 2,191 full tests, 24 focused tests, independent seed
reconstruction, all new archive audits, exhaustive nonempty subsets of the eight
two-variable unit/binary clauses, 100 seeded five-variable formulas, sparse
relabeling, interrupted/terminal reuse, and corrupted warm binding rejection.
