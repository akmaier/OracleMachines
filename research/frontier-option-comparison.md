# Compare retained conditioning with bounded lookahead

2026-11-13. The next original-frontier investigation reduces the open obligation
**29 variables / 120 clauses -> 27 variables / 111 clauses** with **three new
recognition states**. Structural coverage remains **58/83**, also without growth
exceptions. The original is development case **30**, original **1189**
(`reuse_holdout3/n48`), with 48 variables and 204 clauses. Its historical group
name does not make this adaptively reused case an independent holdout.

## Discovery and reuse

The prior checkpoint has no open saved split descendant. Selection therefore
returns to the smallest original-input frontier, without consulting its label.
Before acquiring children, we compare the retained pairs and two small probes:

| Option | Checked result | Integrated seconds |
|---|---|---:|
| Ordinary block: 7, 10, 16, 18 | Clear; no failed literal | 0.00533 |
| Retained augmented base, offset 24: 20, 21, 28, 29 | Clear; no forced, common or equivalence reduction | 0.00702 |
| Rank all twenty saved pairs | Variable 24 remains best under the current rank | 0.09201 |
| Acquire its cofactor plans | Three new states; one open leaf | 0.02748 |

The ordinary continuation is offset 12, after the source's original attempts and
three retained ordinary blocks. The four new clear pairs enlarge the split pool
from sixteen to twenty. The learned record is the final block of the existing
base `4c6f83b7d88417437883467cb00c57e561f7df32be5216ff903a222989e6a9b8`.
Its eligible pool is now exhausted. This does not exclude a different learned
base, stronger lookahead or the source's five remaining ordinary candidates.
Both negative records are retained and restored, so later runs need not repeat
them. A clear block is never a positive structural-coverage edge.

The selected score is **[1, 1, 28, 342, 24]**: uncovered distinct children,
missing distinct children, maximum child support, total child literals, and
variable. It was already the best retained pair before either new block. The
blocks improve our evidence about alternatives; they do not enable this split.
The rank is a heuristic, not a proven minimum acquisition cost.

| Step on the true branch | Variables | Clauses | Literal occurrences |
|---|---:|---:|---:|
| Saved cofactor | 28 | 114 | 342 |
| Variable elimination | 27 | 112 | 346 |
| Binary-path deletion, unresolved leaf | 27 | 111 | 342 |

The false branch reuses the empty-CNF terminal. It already witnesses SAT for
this residual; acquiring the true branch serves complete structural coverage,
which requires both branch plans. Elimination reduces support but initially
increases literal occurrences. No new recognized family closes the remaining
leaf, and none of the three admissions establishes a whole-solver speedup.
Both children are present, with no pending state. All previous plans survive.

## Next useful discovery work

Use the retained split frontier: the **27-variable / 111-clause / 342-literal**
source has SHA-256
`f8316d35e8afb020173cc80da0702f0c0e17a2da22d0ee3ab08ede3a54ac8f53`.
Its saved ordinary pairs are **11, 5, 8, 15**. Compare their cofactor ranks with
its first new ordinary block **19, 24, 9, 13**. Nineteen ordinary candidates
remain at this source, and zero directly recognized affine equations are saved.
Do not restart the larger original-frontier parent or repeat its exhausted
learned base. Variable numbers refer to each normalized residual separately.

The alternative learning queue retains **17 ready bases / 88 candidates**.
The five ordinary candidates left on the older 29-variable source are 20, 21,
23, 28 and 29; they remain alternatives, not prerequisites for continuing the
smaller acquired obligation. Broader recognition on this non-affine representation
and complete-plan checking from actual dependencies remain open. No efficient
partition of all CNFs, polynomial expansion or new complexity lower bound follows.

## Total cost and persistence

| Work | Seconds |
|---|---:|
| Restore parent | 17.49162 |
| Prepare checked routes and original roots | 66.78599 |
| Initial saved-pair selection | 0.08495 |
| Ordinary block / augmented block | 0.00533 / 0.00702 |
| Updated selection / child acquisition | 0.09201 / 0.02748 |
| Coverage composition and diagnostics | 0.15566 |
| Export immutable delta | 5.08491 |
| Full inventory audit | 107.72138 |
| Cold route reconstruction | 64.36063 |
| Reference acquisition / cold DAG replay | 0.02025 / 0.74256 |
| Complete pipeline, including other I/O | **270.71536** |

The exploratory comparison adds **82.05629 s**, mostly a separate restore and
preparation, and the ordinary preview adds **0.00199 s** of probe/check kernel
time. Pipeline plus these preflights is **352.77364 s**; independent validation
and manuscript compilation are additional. Ordinary-preview surrounding file
I/O is not included in its kernel measurement. All preflight results are kept.
Avoid presenting the 0.02748-second acquisition as the complete expansion cost.

The matched two-trace kernel takes **0.000773 s** saved and **0.001124 s** fresh.
Both arms check exact cofactor bindings; the fresh arm also propagates the two
assumptions. This one sub-millisecond-to-millisecond comparison supplies no robust
speedup estimate. The preceding checkpoint's opposite timing result is preserved.

Working SQLite grows **57,344 bytes** to **770,179,072 bytes / 41,752 pattern
nodes**. The delta is **122,880 raw / 5,746 compressed bytes**, preserving all
old rows and adding three pattern nodes and one ordinary continuation. There
are now 129 ordinary continuation rows and 89 ordinary windows. The separate
learned record is **974 JSON / 307 compressed bytes**. Selection, diagnostic and
preflight sidecars are additional, as is the full compressed reference snapshot;
these are not included in the delta size. Peak RAM remains unmeasured.

Independent reference proofs establish SAT for the source and both cofactors,
and check model lifts. They retain all **1,940** old nodes within **1,949**.
The reference database is **14,585,856 bytes**, its compressed snapshot **960,508
bytes**. The full inventory audit checks 1,548 sources, 41,752 pattern nodes and
21,838 residuals, leaving the reconstruction byte-identical.

## Validation and continuation

The targeted 41-test suite covers ordinary continuation, learned continuation,
exact split bindings, partial acquisition, composition and affine-route
preservation. The independent cold validator reconstructs the parent with fresh
discovery disabled. It replays initial selection, inserts only the checked clear
ordinary record, verifies the new learned block and then replays updated ranking.
New child states are introduced only afterward. It checks the full checkpoint,
coverage and growth ablation, all evidence lists, preserved reference nodes,
model lifts and unchanged reconstructed bytes. Independent cold replay passes in **176.26154 s**, additional to the pipeline
and preflights; its result is recorded in `validation.json`. Earlier full-suite and Lean results are
unchanged; no new implementation-refinement theorem is claimed.

Resume `experiments/results/cnf-frontier-comparison/report.json` through
`continue_cnf_frontier_comparison.restore_checkpoint` and `routes_for`.
Preserve all **five evidence lists**: one rewrite, 42 learned bases,
**156 augmented blocks**, **ten splits**, and one affine-family certificate,
plus earlier lemma sidecars. The new runner is restricted to an original leaf
and the observed two clear blocks; it must not be rerun unchanged now that a
split descendant is open.
