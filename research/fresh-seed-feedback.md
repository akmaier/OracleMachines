# Feedback certificates from fresh CNFs

Date: 27 November 2026 (Europe/Berlin). Parent checkpoint: `45b01fc5`.
Evidence: `experiments/results/cnf-fresh-seed-feedback/`.

## Improvement and transfer experiment

`cnf_source_feedback_native.py` reconstructs a checked implication-feedback chain
directly from its supplied CNF. It needs no B13 templates, closures, cursors,
prefix or previously acquired derived-bank history. The feedback discovery rule
is unchanged. Both existing cold readers accept all eight source refutations
found on a new frozen 36-case synthetic panel. One edited mixture needs two
feedback levels, containing four and two branch lemmas respectively.

This closes an interface gap: an arbitrary seed no longer needs the historical
adapter to obtain a source-only native certificate. It does not extend the
discovery rule's coverage or prove efficient solving of every CNF. The old
246-snapshot frontier stays exactly preserved and empty. The fresh panel is a
separate experiment, not an extension of that denominator.

Inputs were frozen before compiler implementation, with SHA-256
`d29e58c65824ca52f58e6b4f7b0ea22a4464c52770e88f01df5392861a84ec95`.
They include clause cubes of widths 3, 4 and 5; random 3-CNF and signed implication
cycles with 6, 9 and 12 variables; parity constraints on graphs with 6, 9 and 12
edge variables; disjoint and shared-coordinate mixtures; and single-literal
bridge edits. Signed variable permutations, sparse names, literal order, clause
order and case order are scrambled deterministically. Discovery receives only
CNFs; generator descriptions and exhaustive truth labels are used only for audit.
These are small generated cases, not a representative SAT distribution or an
independent external benchmark. They are held out from the earlier frontier work,
but are now exposed and must not become the sole development target.

Independent exhaustive enumeration finds **22 SAT and 14 UNSAT** cases. Feedback
refutes **8 of the 14 UNSAT** cases and returns unresolved on the other 28 inputs.
It emits no SAT verdict. The unchanged fresh fallback decides all 36 correctly.
The six feedback-unresolved UNSAT cases are retained in `remaining.json`: full
clause cubes of widths 4 and 5, all three odd-charge parity graphs, and the largest
contradictory bridge mixture. Their failure is specific to this bounded feedback
rule, not the whole portfolio. SAT cases can also contain useful derived units;
an unresolved result is not a proof that no structure was discovered.

## Construction, reuse and invalidation

Each root bank has source-clause origins plus units justified by earlier checked
feedback levels. A branch environment adds its signed condition and successive
failed-probe units. Native construction follows a sliced unit contradiction.
For a forced literal it reconstructs the excluded side from the clause's origin
and the live side from the rest of the trace, then publishes an ordinary native
split. A source-clause leaf requires every literal to be false in the current
context and publishes an empty-clause residual. A branch condition cannot justify
its own excluded context. Local probes must refer to a smaller bank stage;
cross-pivot references from a branch must refer to a smaller feedback level.

Correctness follows by induction over these dependencies and the remaining
trace. A checked failed probe proves its opposite unit under the enclosing
context. A checked failed conditioning side proves the corresponding root-bank
unit. Every source leaf is false in its supplied context, and both children of
each native split refute exactly its normalized source residuals. The existing
native verifier checks every publication; cold readers reconstruct these same
source-only dependencies without the feedback chain. This argument is conditional
on the checked input chain and says nothing about how cheaply that chain is found.

Slice memoization binds environment, bank stage, assumption and ordered trace.
The persistent solver shares only exact normalized residuals, including those
encountered in different panel cases. This recognizes sorted-name transport and
literal/clause normalization, not arbitrary isomorphism or semantic equivalence.
Warm compilation still validates the source, ordering and whole chain before a
root cache hit. Edited source clauses, stale banks, reordered levels, flipped
assumptions and altered conflicts are rejected before publication. Equivalent
clause order, duplicates and removable tautologies preserve normalization.

One direct-unit shortcut allowance is shared across all levels of a compilation.
It bounds only those shortcut work units; the rest of native expansion is not
bounded by it. General graph size, checking cost, Python stack/memory limits and
discovery cost remain explicit limitations. Source-only compilation can still
expand substantially or cost more than fresh search.

## Cost protocol and observations

Six process-order permutations compare the unchanged fresh solver, feedback
compilation with previously acquired chains, and online acquisition plus feedback
compilation. All modes use the same fallback on open cases, start with an empty
database, share exact residuals within the same panel order, repeat all queries
warm, replay both cold readers and compress the archive. Input and history
loading, hashing, recognition, validation and persistence are charged. The prepared
mode excludes earlier chain acquisition; online writes and retains all search
histories. Interpreter startup, report-metadata serialization and the final
lineage audit are outside the reported workflow, and are not free in a deployment.
Feedback has two rounds and up to sixteen pivots per round; fresh has its existing
256-node allowance. These are different algorithms and resource limits.

The initial profiler records about 1.017 s inside feedback discovery across the
panel. Its implication collection takes 0.598 s, including 0.566 s of partition
validation; partition discovery takes 0.407 s. Those times are nested, not
additive. Repeated normalization takes 0.198 s. The underlying failed-literal
search accounts for about 0.066 s. Thus checking and repeated preparation dominate
this small fresh panel, unlike an assumption that search necessarily dominates.
Profiler timings are diagnostic; the unprofiled comparisons are authoritative.

| Workflow | Query construction (s) | Warm queries (s) | Both cold readers (s) | Archive persistence (s) | Complete (s) | Records | Raw record bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fresh | 0.03547 | 0.00604 | 0.02766 | 0.00648 | 0.08072 | 88 | 57,400 |
| Previously acquired feedback + fallback | 0.05599 | 0.01750 | 0.02642 | 0.00678 | 0.12040 | 102 | 61,072 |
| Online feedback + fallback | 0.05450 | 0.01863 | 0.02867 | 0.00684 | 0.44621 | 102 | 61,072 |

Prepared feedback costs **49.16% more** than fresh despite excluding acquisition. Online costs **5.53 times** fresh. Its discovery costs 0.30854 s (69.15% of the complete workflow), and history persistence costs 0.02270 s. Prepared input-chain loading takes 0.00825 s and reads 355,102 bytes. Online writes 2,154,538 bytes of new chains and search histories per run. These costs are included in complete times; the columns above are therefore not an exhaustive phase sum.

The two feedback workflows produce identical archive graphs, with **6.40% more raw record bytes** than fresh. Compressed archives occupy 12,779, 13,786 and 13,786 bytes, respectively. Peak process RSS is 51,691,520, 54,493,184 and 54,509,568 bytes. The baseline chains, online histories and unsuccessful attempts remain on disk in addition to these archive sizes. No runtime or memory improvement is claimed on this panel; the gain is direct certified applicability without historical B13 inputs.


The initial benchmark audit was intentionally stopped when it encountered a
legitimate non-native equivalence root from the existing fallback. The corrected
audit uses the established native/equivalence/affine/cache authority traversal
with both cold readers and original-source checks. Its failed script, protocol
and log remain under `failed-native-only-audit/`. The last initial timing order
overlapped test startup and is retained but replaced by an isolated rerun; the
comparison bindings and timing-control record identify the included samples.

## Validation and next priorities

The focused tests cover all 256 two-variable unit/binary clause subsets, forty
seeded five-variable inputs, all panel refutations with shortcuts both enabled
and disabled, the two-level case, sparse-coordinate normalization, warm mutation
rejection, source-only cold replay and a one-unit global shortcut allowance.
They also ensure unresolved chains cannot gain authority from an existing root.
The historical preparation function is patched to fail in a test, demonstrating
that the new compiler does not call it. Existing helper code is reused; no prior
scientific source, native archive or proof is rewritten.

1. Test checked non-unit boundary consequences or deeper conditioning on the six
   fresh UNSAT gaps, with a second unexposed panel reserved before development.
   Record clause growth and native recomposition costs, not only successful
   refutations. The parity constraints and bridge edit expose different kinds of
   shared-variable interaction.
2. Reduce repeated checking/preparation only after profiling the new candidate.
   Producer-owned checked seed/index bindings may be reusable within a call, but
   require exact identity, ownership and invalidation. Stored claims must still
   receive full cold checks. This is a measured supporting opportunity, not a
   reason to optimize only the eight already recognized cases.
3. Keep fresh solving as the measured alternative and current workflow choice.
   Unrestricted completeness, polynomial acquisition, compact boundary closure
   and bounded source-only expansion remain open. This result implies no
   resolution of P versus NP.
