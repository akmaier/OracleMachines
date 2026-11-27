# Repeated binary forcing before conditioned buckets

Date: 27 November 2026. Parent: `267532d0` (publication checkpoint after research
`1b33707e`). Evidence: `experiments/results/cnf-iterated-forcing/`.

## Result and decision

Bounded repeated forcing certifies **6/24** exposed structural misses, three SAT
and three UNSAT. New unique-panel coverage remains **22/24**, and exact-repeat
coverage remains **3/4**. There are no coverage losses. The unchanged fallback
already decides all 52 queries. This improves restricted acquisition coverage,
not the availability of SAT answers or a classification rate on arbitrary CNFs.

Complete cost falls **18.23%** against the single-pass policy in the same wrapper,
from 2.59466 to 2.12170 seconds. All six paired comparisons improve, ranging from
10.37% to 32.50%. Fresh solving still costs only 0.82988 seconds: closure remains
**2.56 times fresh**, and production defaults are unchanged. Repeated forcing is
the next structural baseline; simply increasing its round cap has no support
here because no measured closure reaches that cap.

## Exact rule, progress and recomposition

An incoming cofactor first uses the preceding unit, binary-conflict and one-block
signed-equivalence preparation. A supported binary path from `not l` to `l`
entails `l`. Add the verified consequences as units, propagate, normalize the
result and search again. Wide clauses shortened by these consequences can become
new binary implications; this is what the previous single pass omitted.

Every round stores its supported paths and unit steps against the exact current
CNF. The checker reconstructs that CNF from preceding rounds, verifies every path
and unit restriction, and reconstructs the inverse renaming. Model lifting walks
these maps in reverse order before the initial signed-equivalence and unit maps.
It checks every SAT incoming transport, even for an unused SAT child. An UNSAT
split still needs both exact children; unknown is never a refutation.

A successor round requires a strict decrease in the number of active variables.
A final round with no decrease may still add entailed units, but cannot repeat.
With `n` incoming active variables there can be at most `n` accepted rounds:
productive rounds decrease a nonnegative count, no forcing exists on a constant,
and a nonprogressing round must be last. The explicit round cap is eight. Partial
unit processing, early stopping and exhausted budgets preserve exactness; they
do not assert that a fixed point was reached.

The 262,144 graph-edge-visit allowance is **cumulative across all forcing rounds
on one incoming cofactor**. Returned path steps sum to at most these visited
edges. Replay independently enforces a cumulative path-step bound; it does not
claim to reconstruct unrecorded discovery visits. Every unit invocation separately
allows 512 steps and 262,144 reserved index-work units. Every bucket node has its
own 262,144 probe allowance, depth two and width eight. Setup, start enumeration,
queues, path assembly, normalization, lookup, verification, time and RAM are extra.
The binary partition still has an exponential depth bound.

The new `cnf-iterated-forcing-v1` authority has `once` and `closure` modes. The
former is audited against the preceding separate-path implementation after a
lossless format translation. The latter repeats only forcing and units, not SCC
substitution. Discovery rebuilds the binary graph each round; there is no claimed
incremental graph-maintenance speedup. Old native, equivalence, affine and Lean
formats are unchanged.

## Recognition, sharing and invalidation

Full normalized residual and remaining depth still identify reusable local nodes
under a fixed policy. Incoming histories retain separate round evidence and
transport. Exact root programs share within each measured stream, but each warm
and cold use is rechecked. Source edits invalidate clause-index bindings; maps
and paths cannot be transplanted to a new source without checking them again.
Round/step/depth policy changes invalidate cache keys.

Both arms have 21 shared targets and fifteen joins of distinct raw cofactors,
all constant. No additional nonconstant semantic sharing is established. The gain
comes from exposing consequences sooner and reducing later bucket/fallback work,
while retaining the exact residual-sharing machinery.

## Frozen comparison and complete costs

The panel has 24 exposed sources (15 SAT, nine UNSAT), 24 new constructions
(ten SAT, fourteen UNSAT) and four SAT repeats. The new controls were frozen
before implementing the kernel, with seed `2711270903`. They include random
three-CNFs at 15/19/23 variables, guarded forcing cascades of increasing depth and
deleted links, parity prisms at sizes 8/10/12, and opposed-clause chains. Variable
names, signs and order are scrambled; descriptions and independent truth labels
are withheld from acquisition. No new normalized source duplicates the prior
panel. These are synthetic controls, not representative external SAT benchmarks.

All six permutations of the three modes run in fresh processes with the same
fallback. Complete cost charges input preparation, discovery, checks, evidence
and database persistence, warm use, cold reconstruction and compression.
Interpreter startup, report metadata, panel generation, post-hoc diagnostics,
historical acquisition and final preservation audit are additional costs.

| Measure | Fresh | One pass | Repeated closure |
|---|---:|---:|---:|
| Complete seconds | 0.82988 | 2.59466 | 2.12170 |
| Discovery seconds | 0 | 0.55496 | 0.51010 |
| Solve/check seconds | 0.36345 | 0.56120 | 0.44027 |
| Warm seconds | 0.02640 | 0.33540 | 0.28465 |
| Cold seconds | 0.26019 | 0.90352 | 0.69853 |
| Evidence writes seconds | 0 | 0.03183 | 0.02525 |
| Archive persistence seconds | 0.17210 | 0.19884 | 0.15526 |
| Raw JSON certificate bytes | 0 | 3,646,507 | 3,520,828 |
| Native record bytes | 1,063,204 | 796,000 | 589,421 |
| Combined compressed SQLite/JSON bytes | 204,714 | 218,868 | 176,174 |
| Peak process RSS bytes | 74,924,032 | 74,711,040 | 71,188,480 |

Diagnostic bytes are separately 0/129,409/142,636. Historical copies and container
overhead are additional. Peak RSS is a process-level observation, not an
asymptotic or universal memory guarantee. Both native readers audit fallback
archives; two additional JSON passes share the same checker, not independent
JSON implementations. Cold verification remains the largest measured phase.

Bucket nodes fall **186 to 175**, split nodes **83 to 80**, and elimination steps
**407 to 327**. Accepted forcing rounds rise **51 to 96** and unit steps **156 to
317**, with 23 incoming edges accepting multiple rounds and a maximum of six.
Discovered forced-literal occurrences rise **131 to 298**, path steps **488 to
1,292**, searches **3,206 to 4,670** and edge visits **7,862 to 14,034**. Including
acquisition checks, support checks rise **1,535 to 3,970**. Compact forcing records
grow **8,014 to 18,923 bytes**. More local evidence is profitable here only because
it removes enough later work; it is not a compression of forcing itself.

No closure call hits its round, traversal or nonprogress stop: 67 incoming edges
end constant and 141 finish without another forced literal. Maximum cumulative
traversal is 782 visits, well below the allowance. Initial preparation and branch
choices differ once more roots close, so raw call-count changes are not a pure
per-call microbenchmark.

## Remaining gap and next experiment

There are **20 unique unresolved roots** (18 exposed, two new), plus one repeated
query. Their 30 unknown depth-zero nodes all fail width limits: nineteen at width
nine, six at ten and five at eleven. Seven stop before elimination; 23 retain
partial bucket work. The separately checked structural profile finds no units,
components, Horn/dual-Horn leaves, binary conflicts or remaining one-way forcing.
Only one equivalence block remains, merging one variable. That profile costs
0.01995 seconds and supplies no additional root verdict.

The stronger lead is **failed assumptions using full-CNF unit propagation**.
A separate diagnostic tries both signs of each variable, up to 128 probes per
leaf, and checks every returned unit reason and conflict clause against its
source. All 1,022 probes fit without truncation. Every one of the 30 leaves has a
failed assumption, with 207 failed-literal occurrences; six leaves have failures
on both signs of some variable. Wider clauses therefore expose consequences
that binary reachability alone cannot see. Nonfailed probes are not SAT witnesses.

This diagnostic costs **0.09285 seconds**, charging 505,678 propagation-literal
visits and 9,576 checked reason/conflict literals. It is post-hoc, not part of the
matched acquisition, and six diagnostic leaf refutations are not six new root
certificates. The next target is bounded, source-certified full-CNF failed-literal
closure before buckets, reusing the repository's checked propagation ideas while
preserving exact round transport. Charge unsuccessful probes, repeated scans,
reconstruction, verification and fallback. General wide interactions and efficient
unrestricted coverage remain unresolved.

## Validation and preservation

All **2,300 full tests and 34 focused tests pass**. Twelve new tests cover all
512 two-variable clause sets, seeded mixtures, multi-round chains, deleted links,
sparse signed lifting, single-pass equality with the old policy, partial caps,
nonprogress rejection, corrupt rounds and cold replay with recognition disabled.
All 230 preceding research manifests, 42,390 artifact entries, 1,263 scientific
sources and 72 proof blocks remain unchanged. Five new source/test files bring
scientific fingerprints to 1,268; the manuscript adds one restricted proposition.
The previously published alphaXiv snapshots remain unchanged. Existing SQLite
ResourceWarnings, all measured regressions and the single-pass misses are retained.
