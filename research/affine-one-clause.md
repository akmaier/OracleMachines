# Decide one clause over a checked affine core

2026-11-13. Structural coverage rises **56/83 -> 57/83**, also without growth
exceptions. The new rule closes case 0 (`projection_variant/encoding_cap`, original
case 742: 14 variables / 132 clauses) by deciding its 11-variable / 49-clause
residual. All previous inventory rows remain byte-identical. These are adaptively
reused development instances, not a fresh holdout or arbitrary-SAT coverage claim.

## Exact family and certificate

Extract complete direct parity encodings and preserve every other clause. The
new family accepts at most one remaining clause C. An inconsistent affine core
proves UNSAT. Otherwise, from checked triangular rows construct a particular
solution a and a complete nullspace basis v_j. A literal x_i=b is compatible iff
a_i=b or some v_j has coordinate i equal to one. In the latter case a+v_j gives
the required model. One compatible literal suffices for C. If all literals are
forced false, the formula is UNSAT. No clause means the consistent affine system
is SAT. More than one leftover clause returns **unknown**, not UNSAT: different
clauses may require incompatible solutions.

`experiments/cnf_affine_clause.py` independently checks the exact source partition,
row reductions, particular solution and every homogeneous direction. Identity
coordinates on the free variables certify independence of n-rank vectors and
hence completeness. Omitting a direction cannot establish an UNSAT certificate.
SAT models are checked against the full source CNF. Input variable labels must be
dense before constructing masks; the normalizer supplies the explicit renaming.
These are standard linear-algebra facts, not a new tractability theorem. The
manuscript adds the proposition and proof; no new Lean refinement is claimed.

The positive record is a zero-premise checked family route. Its exact node key
and full source formula are bound before coverage composition. Existing nodes
are not reclassified or rewritten. All seven splits, 42 learned bases, 155
augmented blocks and earlier lemma sidecars survive.

## Coverage and the next discovery gap

The runner scans **all 29 distinct selected leaves** of the 27 open originals,
using each node's already saved affine extraction. Exactly one qualifies: two
equations of widths five and six, rank two, and one eleven-literal clause. It is
SAT and completes the retained decomposition of case 0. Independent reference
solving verifies both the leaf and original formula.

The other **28 leaves, across 26 originals**, have **zero equations recognized
by this explicit parity extractor**, with 80--186 leftover clauses. Thus extending
only the affine clause handler has no direct opportunity on their present
representations. This does not prove absence of hidden parity or useful
conditioned structure. No exact selected leaf is shared between originals.

The next bounded discovery target is case 73's 20-variable / 80-clause leaf,
whose ordinary and current augmented probes are exhausted. Compare a retained
cofactor decomposition with the four remaining augmented candidates on case
30's 29-variable / 120-clause leaf. Keep the 18-base / 92-variable ready queue
from the parent. Repeating the unchanged affine scan has no discovery value.
The selected frontier is one navigation policy, not every available alternative.

## Costs and memory

| Work in the development checkpoint | Seconds |
|---|---:|
| Restore immutable history | 14.80944 |
| Prepare checked routes, roots and selected leaves | 64.60772 |
| Check 29 extractions and construct/attach one family proof | 0.00599 |
| Serialize family proof and selection diagnostics | 0.03560 |
| Compose closure and remaining frontiers | 0.14099 |
| Serialize coverage and remaining frontiers | 0.22520 |
| Independent reference acquisition / cold DAG check | 0.01215 / 0.74112 |
| Complete pipeline, including other I/O | **82.32152** |

The **769,847,296-byte** inventory and **41,728 pattern nodes** are unchanged.
The new family sidecar is **3,446 raw / 1,056 compressed bytes**. Selection,
coverage, report and remaining-frontier artifacts are additional; the family
record size is not total archive growth. The reference database grows 49,152
bytes to **14,290,944 bytes**, preserves all **1,869** earlier nodes byte for byte
and contains **1,883** nodes. Its complete compressed archive is 934,845 bytes,
not a delta. No resident inventory memory reduction is claimed.

For e equations, n variables, rank r and d=n-r, space construction visits
r(d+1) triangular rows, while one space check evaluates e(d+1) equation-vector
parities. Each row or vector has up to n bits, so these are big-integer operation
counts, not unit bit costs. The solution space uses O(n(d+1)) bits, potentially
quadratic. Literal compatibility uses at most |C|d direction tests. Input
normalization, source partition checks, grouping, support sorting, initial
elimination and proof serialization are additional. Stored extraction includes
the CNF, equation supports, reduced rows and elimination dependencies. The direct
CNF input for a width-w parity may already contain 2^(w-1) clauses.

The matched generated study in `experiments/results/cnf-affine-clause-costs/`
uses twelve cases with 11--96 variables: particular-model SAT, repaired-model
SAT and UNSAT with a nonempty kernel. Random labels and clause order are normalized
in both arms. Fresh construction and exact-source reuse both pay full source,
equation, space and decision checks. Each has nine timed repetitions; a separate
tracemalloc run measures local Python allocations without perturbing those times.

Median reuse savings range from **1.11x to 1.24x**. On the 96-variable repair
case, fresh/reuse takes **1.828 / 1.477 ms**, with local traced peaks
**86,300 / 71,176 bytes**. Its full proof is 6,772 raw / 2,527 compressed bytes.
These are local Python allocations, not process RSS or whole-history peak RAM.
Seed acquisition is recorded separately. A changed single clause reuses the
space but pays a fresh source extraction and checks; a second-clause control is
declined. Thirteen saved proofs pass fresh-process replay in **0.00686 s** without
discovery. These timings do not establish a whole-solver speedup.

## Validation and resumption

Twenty-one targeted tests pass, including 512 two-variable CNFs, 3,304 three-variable
clause subsets of size at most three (normalized before checking), 160 randomized
affine mixtures and their renamed/sign-flipped variants, SAT/UNSAT, missing or
forged basis vectors, altered equations, exact-source route binding and cold
replay. This is not a new full-suite result.

The standalone validator reconstructs the checkpoint, checks every selected
leaf's acceptance or rejection, replays the complete coverage plan and ablation,
checks all reference nodes and verifies byte-identical preservation with new
discovery disabled. It checks reachable inventory dependencies, not a fresh full
scan of unrelated unchanged rows; the parent full audit remains retained. The
82.32-second pipeline therefore has different validation obligations from the
preceding 271.74-second run and is not a matched speedup comparison.

Two initial validator attempts exposed a diagnostic comparison bug: JSON changes
integer model keys to strings and numeric sorting differs from lexical sorting
above variable nine. Comparing decoded objects fixes the comparison without
changing solver certificates. Their failure logs are retained. Final independent cold replay passes in **81.77622 s**; validation
details and hashes are in `validation.json` beside the checkpoint.

Resume **`experiments/results/cnf-affine-clause/report.json`** with
**`continue_cnf_affine_clause.restore_checkpoint` and its `routes_for`**. The return
value contains the report followed by **five** evidence lists; the fifth holds
the affine family records. Passing only the previous four to an older route
builder would silently lose this new coverage. Preserve all five when advancing
another discovery scheduler; the new runner itself is a one-pass experiment
against the fixed parent, not an incremental generic scheduler.

```sh
python3 -m unittest solver.test_cnf_affine_clause solver.test_cnf_affine_patterns \
  solver.test_cnf_route_composition > /tmp/affine-clause-tests.txt 2>&1
python3 experiments/validate_cnf_affine_clause.py \
  experiments/results/cnf-affine-clause --test-log /tmp/affine-clause-tests.txt
python3 experiments/benchmark_cnf_affine_clause.py /tmp/affine-clause-costs
python3 experiments/benchmark_cnf_affine_clause.py /tmp/affine-clause-costs --replay
```

Dependency-local checking for a complete positive coverage plan is still the
largest measured runtime opportunity. General discovery of a compact exact
decomposition, bounded total states/space, and uniform polynomial construction
for every CNF remain open.
