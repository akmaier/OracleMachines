# Refute a mixed residual through its binary subset

The new optional native leaf recognizes a contradiction even when unrelated
wide clauses remain. If the binary clauses contain paths from `x` to `¬x` and
back, they refute the entire residual. Every edge retains its original clause
index, so the existing native implication checker verifies the result. There is
no new proof format or trusted decision procedure.

This closes a specific recognition gap in the acquisition path. The earlier
binary-path inventory can delete entailed wide clauses, but ordinary native
search previously invoked its SCC solver only when the whole residual was
binary. The new rule tests the binary subset of a mixed residual. A satisfiable
subset is inconclusive; the wider clauses still impose joint constraints.

## Scope, costs and reuse

The optional `AccountedBinarySubsetSolver` applies the test only during fresh
native expansion with leaves enabled. Any unit/empty clause leaves the original
propagation route in charge. Pure binary and non-binary-only sources skip SCC.
A further necessary-condition filter requires both a positive-only and a
negative-only binary clause: otherwise a uniform assignment satisfies the binary
subset. Each failed test returns to the original complete search.

For a normalized residual with `m` clauses and `b` binary clauses, width/sign
recognition takes `O(m+b)` work. The implication graph has at most `4b` signed
vertices and `2b` edges; SCC and path extraction take `O(b)` work and temporary
space in the usual indexed graph model. Python sorting and map operations add
implementation costs; the existing solver sorts the variables, so its worst-case
comparison-model construction bound is `O(b log b)`, rather than a literal
linear-time implementation guarantee. The two paths use `O(b)` steps. The full
source key, source-bound certificate, serialization, storage and verification
remain charged. Source encoding and integer bit costs are additional.

Across expanded residuals, these costs add to the original search cost on misses.
The number and size of those residuals can still be exponential. A contradiction
saves a subtree, but there is no general guarantee that the saved work outweighs
recognition. Existing exact canonical-key reuse applies to the resulting proof;
the method does not yet cache or incrementally maintain binary graphs across
different residuals. It does not alter existing cached proofs.

## Evidence

The retrospective census of the preceding session finds 123 mixed residuals,
ten binary contradictions and thirteen whole-residual models obtainable from a
binary model with uniform completion. Only the negative rule is implemented.
These are residual counts, not distinct whole-query coverage gains. In a separate
empty-archive mechanism check, old case 56 shrinks **33 -> 26 expanded nodes** and
**8,144 -> 6,075 propagation visits**; earlier closure makes one of its four
observed contradiction descendants unnecessary. Old case 44 remains unchanged
and pays three failed SCC calls. These five checks have no shared preparation and
are not reported as exact-prefix timing comparisons.

A new sixty-query catalog excludes every inherited native/query root. It contains
twelve neighbours and 48 generated cases from four families. Both policies use
the same affine sessions and return **40 SAT / 20 UNSAT**. All twelve neighbours
become known after preparation; the 48 family targets remain unfamiliar. All 120
paired discovery traces and probe-counter sets match. Labels never enter selection.

| Per worker, except mean times/RSS | Session baseline | Binary subset |
|---|---:|---:|
| Added native nodes | 281 | 259 |
| Expanded native nodes | 208 | 186 |
| New native payload bytes | 363,736 | 347,343 |
| New extension certificates / bytes | 3 / 9,801 | 3 / 9,801 |
| Child propagation visits | 32,980 | 30,779 |
| Discovery propagation visits | 44,556 | 44,556 |
| Query seconds | 0.43247 | 0.41775 |
| Full cold replay seconds | 13.36327 | 13.49378 |
| Complete worker seconds | 27.67783 | 27.90523 |
| SQLite bytes | 84,000,768 | 83,984,384 |
| Compressed bytes | 6,397,771 | 6,395,452 |
| Mean peak RSS bytes | 789,430,272 | 768,237,568 |

Eight new refutation leaves remove 22 native nodes: sixteen in random three-CNF
and six in graph colouring. The candidate pays **186 recognition calls, 6,823
width checks, 4,654 binary sign visits, 84 SCC calls and 3,282 constructed edges**.
Only eight SCC calls refute their source; **76 are misses**. It stores 83 path
steps. Other families acquire the same number of nodes. Diagnostic sidecars grow
by about 5.1 KB per worker. Full keys, checking, serialization, compression,
setup, warm reuse and cold replay are included in the worker totals.

The mean query reduction is 3.40%, but paired changes are **+0.02453 / -0.05397 s**.
Complete-worker changes are **+0.90077 / -0.44596 s**, averaging a **0.82% increase**.
Cold changes are +0.39037 / -0.12934 s. Two orders establish deterministic work
and storage reductions, not a stable runtime win. The policy remains optional;
its extra work and the timing regression are preserved.

## Preservation and next target

Resume `experiments/results/cnf-binary-subset/checkpoint.json`. Its union preserves
all **27,087 old native payloads and ten extension certificates byte-for-byte**,
and contains **27,368 native keys / thirteen extensions**. It adds 114 native and
six negative chain records to 5,110 inherited composed records. The union retains
comparator history, growing **688,128 SQLite / 79,234 compressed bytes**; this is
separate from the smaller candidate trial. Eight roots have alternative native
proofs, retained in the trial archives and listed in `validation.json`. The union
keeps the first payload, so it does not silently replace those baseline proofs
with shorter alternatives. Choosing among native certificates remains open.

The existing `TerminalStore` still handles affine extensions. To enable the new
leaf on fresh native work, construct
`experiments.cnf_binary_subset.AccountedBinarySubsetSolver`; the checkpoint names
this optional solver explicitly. Old native readers can verify its new proofs.

Independent validation checks 240 chronological queries, twelve affine-publication
counter records, exhaustive truth for 48 generated cases, warm answers and full
historical replay for every worker and the union. Seven new tests include all
4,096 binary subsets on three variables with a wide clause, corrupted source
indices, signed renaming, incomplete positive cores, disabled leaves and cold
replay with search/writes forbidden. All 553 prior source hashes, 7,439 artifacts
and 104 manifests remain intact.

The most informative next acquisition cases are **new cases 56 and 44**, still
costing 5,159 and 5,117 child propagation visits. Their binary cores do not close
the remaining wide-clause interaction. Investigate repeated binary graphs and
conditional compatibility with the wide clauses before increasing probe depth.
The 76 failed SCCs are the direct overhead target. Graph discovery costs 28,131
visits against 4,724 in acquisition; early completion of its retained covers is
the second target. Full historical replay still costs about 13.5 seconds.
These finite reductions establish neither broad runtime dominance nor a uniform
polynomial expansion bound for unrestricted SAT.

All **1,188 tests** and **nineteen focused tests** pass. The full suite retains
44 existing SQLite resource warnings; focused tests have none. The **220-page**
manuscript builds with a clean final log and all **64 existing proof blocks
unchanged**. No new Lean theorem is claimed.

Final source ledger: **560**. New manifest: **39 artifacts**. Next preservation
audit: **7,478 artifacts / 105 manifests**.
