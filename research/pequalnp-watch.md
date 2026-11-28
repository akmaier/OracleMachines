# External research watch

The daily `review-external-sat-research` automation reviews
[alphaXiv](https://www.alphaxiv.org/) and [pequalnp.com](https://pequalnp.com/),
scheduled around noon Europe/Berlin. The hourly OracleMachines investigation
remains guided by our own gap analysis. External results are leads, not imported
axioms or a replacement research agenda.

## 28 November 2026: proof compaction, reuse guards and bounded obstructions

Compared today's review with checkpoint `7d3fad8d` and the
[current gap record](structural-reuse-priorities.md). Frozen external transfer
checks **16/16** reused targets versus **9/16** fresh targets, but mean measured
target cost is **116.00 s** versus **62.71 s**, with **79.67 s** of parent
acquisition additional. The immediate opportunity remains cheaper retained
proofs and replay while preserving the coverage gain. The papers below are new
to this watch, not necessarily newly published.

The authenticated alphaXiv MCP searches covered SAT structural reuse/learned
clauses and P=NP/SAT, prioritizing recency. Read primary PDF excerpts, live
discussions and the pequalnp board, and pinned the new Lean source through
GitHub. This is a targeted review, not a complete agent census. External code
and benchmarks were not run; the independent finite checks below are ours.

### Three leads for the current cost gap

1. **Avoid rediscovering proof information during replay.** Baek, Carneiro and
   Heule, [A Flexible Proof Format for SAT Solver-Elaborator Communication](https://www.alphaxiv.org/abs/2109.09665),
   [primary v3](https://arxiv.org/pdf/2109.09665v3), 15 April 2022, describe FRAT's
   optional propagation hints, stable clause identifiers, finalization records
   and forward/backward parsing. These support streamed elaboration and
   dependency selection. Their reported improvements concern a DRAT comparison,
   not our solver. Our resolution records already contain explicit parents and
   pivots, so merely adding hints would duplicate existing information.

   **Our next experiment:** separate the certificate needed for the current
   answer from the complete retained knowledge archive. A SAT answer can be
   checked from its model; an UNSAT resolution certificate can retain only
   ancestors of its empty clause, with checked index remapping. Keep the complete
   archive for future edits, and charge construction, extra storage, loading and
   checking. A smaller answer certificate does not make that archive smaller.

2. **Preserve the semantics of reusable proof steps.** Rebola-Pardo,
   [Short proofs without interference](https://www.alphaxiv.org/abs/2508.09851),
   [primary v1](https://arxiv.org/pdf/2508.09851v1), 13 August 2025, explains why
   RAT and related satisfiability-preserving steps can depend on the entire
   current formula. Strengthening it can invalidate a step. Theorems 7–8 give
   composition and refutation translation in a richer dynamic logic with
   program annotations. They do not make every unannotated added clause an
   original consequence. We inspected the definitions and theorem statements,
   not all proofs or a practical implementation.

   **Independent counterexample:** start with `F = (x OR y)` and add `C = x`.
   This preserves satisfiability and is vacuously RAT on `x`, since `F` has no
   clause containing `NOT x`; it is not entailed. The edit `F AND NOT x` is SAT,
   but carrying `C` into it makes it UNSAT. Exhaustive truth tables give model
   counts **3, 2, 1, 0** for these four formulas. The existing OracleMachines
   checker rejects a forged resolution derivation of `x`. A valid control
   deriving `y` from `(NOT x OR y) AND (x OR y)` preserves the model set under
   all **512** two-variable CNF strengthenings, including the empty clause.
   This is a guard against a proposed unsafe extension, not a discovered bug.

3. **Freeze specialization before evaluating transfer.** Green, Le Goues and
   Brown, [The Case for Automated Hyperspecialization: Evidence from SAT](https://www.alphaxiv.org/abs/2609.14836),
   [primary v1](https://arxiv.org/pdf/2609.14836v1), 13 September 2026, use
   workload-specific coding agents, 189 families and an 80/20 split within
   each family. Only training feedback is exposed to the agents. SAT models
   and UNSAT proofs receive independent checking; results with checking costs
   are reported separately. Checking is polynomial in input **plus output
   proof size**, which need not be polynomial in input alone. The generated
   specialist gallery explicitly permits descriptive inaccuracies. We did not
   reproduce their performance claims; no discussion was visible on the page.

   **Our follow-up:** develop admission/dispatch on the exposed panel, freeze it,
   then use a new holdout grouped by parent so sibling edits cannot cross the
   split. Compare fresh search and all-retained reuse, include SAT parents,
   and charge tuning, acquisition, recognition, proof generation and replay.
   Entirely unseen formula distributions need a further test; within-family
   validation does not establish that transfer. Invalid or unfinished runs
   remain unknown rather than disappearing from coverage counts.

### New pequalnp result and a checked special case

The board highlights [L-lib-1313](https://pequalnp.com/lemma#L-lib-1313), attributed
to outside contributor `JLDC`, marked checked at 10:19 UTC on 28 November. For
`t >= 1` output taps and at most `r` NOT gates, its displayed statement requires
distinct sampled input masks and nonempty allowed-output lists closed under
union and intersection. Infeasibility has a chain obstruction of at most
`(t+1)*2^r` samples, with a matching deletion-minimal construction. Constants
are allowed and circuit wires must be valid. **AND/OR gate count is unbounded**;
the bound is exponential in `r` and is not an arbitrary-CNF small-core theorem.

The merged [PR 54707](https://github.com/open-goat/pequalnp-proofs/pull/54707)
and [checker run](https://github.com/open-goat/pequalnp-proofs/actions/runs/46133527670)
link to [the source at revision bde913e5](https://github.com/JLDC/pequalnp-proofs/blob/bde913e54059b1353b142b62c9a3e618e9d2280c/lean/PEqualNP/Outside/L_lib_1313.lean).
Inspected the opening definitions and final statement/proof, including lines
2540–2638; Git blob is `d293a795964a01106351736377fc02e794937548`. We did not compile
Lean or audit transitive definitions. The badge alone is not our verification.

**Independent special-case proof (`t=1, r=0`).** With AND/OR and constants, every
output is monotone. Thus two comparable masks `a subset b` requiring respectively
`1` and `0` are an obstruction. Conversely, if no such pair exists, set the
output at `b` to `1` exactly when some sample forced to `1` is a subset of `b`.
This monotone function satisfies every sample. It has a monotone DNF using one
conjunction per forced-one sample, with constants for the empty cases. The
two-sample bound is sharp: on one variable, require `1` at the empty mask and
`0` at the full mask; deleting either requirement permits a constant function.
For explicitly listed samples, finding a violating pair costs at most quadratic
many subset comparisons. This concerns monotone sample fitting, not recognition
of such a representation in an arbitrary CNF.

Independent enumeration checks **6,654** specifications on zero through three
variables against **2, 3, 6 and 20** monotone truth tables respectively. Every
one of the **4,671** infeasible specifications has the claimed two-sample
obstruction; all **1,983** feasible ones admit the explicit upward-closure
construction. Missing samples are encoded as allowing either output. This
verifies only the stated special case, not the external theorem for multiple
taps or NOT gates. The obstruction remains reusable only while its two exact
requirements and the monotone circuit restriction remain valid.

The [standalone audit](external-watch/2026-11-28-reuse-guards.py) reproduces
[the deterministic evidence](external-watch/2026-11-28-reuse-guards.json), including
the reuse counterexample and checker control. Run it from any directory:

```sh
python3 research/external-watch/2026-11-28-reuse-guards.py
```

The JSON reproduced byte-for-byte in fresh processes, including Python `-O`
from a different working directory. Its script/checker hashes and base checkpoint
were checked, and all previous watch and gap-record lines were preserved. This
checks the standalone audit; the unchanged solver's full suite was not rerun.

### Decision and limits

Prioritize a controlled **answer-certificate versus knowledge-archive** comparison
on the existing fixed traces, then a separately frozen admission policy if
needed. Restrict ancestor trimming to checked logical consequences; richer
SAT-preserving transformations need their contexts and model-reconstruction
maps. The monotone obstruction is a candidate representation-specific summary,
not grounds for assigning arbitrary CNFs to a new efficient class.

The live pequalnp paper listing still displayed Note 1 and warned that its data
feed was behind. This cannot establish absence of newer work. The targeted P=NP
search established no unrestricted result that we can adopt. The
[K-record paper](https://www.alphaxiv.org/abs/2611.knowledge-solving-complexity-checking)
still resolves to **v3, 25 November**, with the same critique and author reply;
the [existing review](alphaxiv-knowledge-record-review.md) remains applicable.
No external claim changes current coverage measurements, production defaults
or manuscript theorems. No agent was contacted and no comment or publication
was made during this watch.

## 27 November 2026: reusable components, boundary reconstruction and local proofs

Compared the sources below with research checkpoint `7e4b47cb` and the
[current cost/gap record](structural-reuse-priorities.md). The latest experiment
certifies 47/48 structural queries; one 23-variable SAT root retains two
width-nine leaves. Discovery and cold checking dominate, and the complete
pipeline remains 1.67 times fresh solving. External results do not change those
measurements or production defaults.

Used the authenticated alphaXiv MCP search and primary PDF excerpts, plus live
paper/discussion and pequalnp boards. The search included SAT structure, reuse,
backdoors and P versus NP; our own paper was excluded as external evidence.
The available MCP catalog has researcher lookup but no agent-directory or
discussion-list tool, so this is a targeted review, not an exhaustive agent census.
No external code was executed, benchmarks reproduced, or theorem imported.

### Leads and their restrictions

1. **Exact component keys across changing formulas.** Bartal, Fried and Lagniez,
   [Efficient Incremental #SAT via Cross-Instance Knowledge Reuse](https://www.alphaxiv.org/abs/2605.00671),
   v1, 1 May 2026, sections 5–7, retain residual components across calls and
   discuss renaming-based cache reuse. They explain why keys that omit static
   binary clauses fail when the underlying formula changes. Full component
   storage has a memory cost; their experiments include slowdowns, and symmetry
   adds little when variable names already align. A decomposition remains valid
   after clause deletion, but their random-update setting did not benefit from
   retaining the initial decomposition. Their linked implementation is
   [d4v2](https://github.com/crillab/d4v2); we did not establish an immutable
   release matching the experiments. Published speedups are not our measurements.

   **Independent check:** exhaustive enumeration of all four assignments gives
   three models for `(x OR y)`, two after adding `(NOT x OR NOT y)`, and zero for
   the conjunction of all four binary sign patterns. Omitting all binary clauses
   makes the illustrative keys identical despite different counts and even
   different SAT status. The first two cases reproduce the paper's example;
   the third is our extension. Preserve the
   [formulas, keys and truth tables](external-watch/2026-11-27-cache-key-check.json).
   This is a counterexample to that hypothetical key, not a discovered bug in
   OracleMachines or a test of the external implementation.

2. **Local consequences beyond failed single literals.** Goldberg,
   [On Structure-Aware SAT Solving](https://www.alphaxiv.org/abs/2611.18017),
   v1, 13 November 2026, uses partial quantifier elimination (PQE) to reduce
   interactions and studies literal-redundancy certificates. Its Proposition 3
   characterizes deleting a literal from a clause by inconsistency of the
   assignment that satisfies only that literal. PQE must preserve the relation
   `exists X F = H AND exists X (F minus G)`, not merely global satisfiability.
   The striking equivalence-checking results use deliberately constructed
   multiplier circuits; even that table includes a small-instance slowdown.
   Efficient PQE remains an explicit dependency. We read definitions and the
   experiment, not a complete proof or implementation audit. No discussion posts
   were visible on this paper's page during the check.

3. **Finding and replacing bounded interactions on dense inputs.** Dreier,
   Ganian, Gründel, Sharma and Wietheger,
   [Solving SAT via Treewidth Backdoors in Linear Time: Beyond Sparsity](https://www.alphaxiv.org/abs/2610.18540),
   [v1 primary text](https://arxiv.org/html/2610.18540v1), 13 October 2026,
   Theorem 1.1 requires fixed parameters and a signed semi-ladder restriction.
   It finds a satisfying weak backdoor to bounded **incidence** treewidth, or
   reports absence of such a bounded backdoor. The negative outcome is not an
   UNSAT verdict. Section 4.1.1 defines replacement by agreement under compatible
   boundary gluing, with parameter-dependent representatives and solution
   lifting. The bounds do not make arbitrary semantic canonicalization cheap.
   Incidence treewidth also differs from our primal elimination width. This
   extends the older recursive-backdoor literature already recorded here; it
   does not supply unrestricted coverage or a practical runtime measurement.

4. **Check whether width is intrinsic before increasing it.** Krone,
   [SAT-Driven Exact Treewidth via Safe Separators and Structure-Aware Encodings](https://www.alphaxiv.org/abs/2611.33695),
   v1, 25 November 2026, decomposes exact treewidth computation using checked
   separators and combines heuristic lower/upper bounds with SAT/MaxSAT.
   Clique separators and sufficiently restricted almost-clique separators
   preserve the optimum. Dense or unbalanced cases can retain nearly the whole
   hard graph; exact treewidth remains NP-hard. Appendix F charges candidate
   enumeration and separator validation. The
   [linked source](https://github.com/NaykinYT/Treewidth) was not run or pinned
   to the reported results. A safe graph split is not permission to combine
   independent SAT answers without checking shared-variable compatibility.

### New pequalnp agent result: functional reconstruction, still exponential

The live board highlighted [L-meta-25483](https://pequalnp.com/lemma#L-meta-25483),
attributed to outside contributor `ovolee37` and marked checked on 27 November
at 10:20 UTC. Its stated circuit bound for a particular three-round key test is
`500*k*2^max(19,floor(k/2))`, for `k >= 20`; this is exponential in `k`.
The [proof PR](https://github.com/open-goat/pequalnp-proofs/pull/38599) adds
`lean/PEqualNP/Outside/L_meta_25483.lean`, pinned at source revision
`559efd12474a4b167558b7dc108c071ffa8c25b9`, with a linked
[checker run](https://github.com/open-goat/pequalnp-proofs/actions/runs/45980378986).
The inspected patch uses a backward fill, dependence on the next 19 bits,
uniqueness given a suffix, and enumeration of the remaining seed bits followed
by both original tests. We did not compile Lean or audit transitive definitions.
Its badge is a lead, not our independent verification.

The papers listing still displayed Note 1. The feed warned that updates were
paused since 10:56 UTC, so absence of another visible paper is not evidence that
no newer work exists. The P=NP search board had no checked unit. No claim from
this review resolves unrestricted SAT or P versus NP.

### Ranked follow-ups for our own line of work

These are proposed experiments, not reported results from the sources:

1. **Keep the measured cost target:** reuse verified normalized CNFs, active
   variable sets and restriction results within one cold replay. Cache identity
   must include exact immutable source/context, with collision checking and
   edit invalidation. Compare identical traversal with and without sharing to
   isolate its effect. Charge construction, lookup, retained bytes, serialization
   and cold reconstruction; do not replace source checks with trust in a digest.
2. **Keep the immediate coverage target:** apply checked relation substitution
   after probe consequences on the remaining root, against ordering/width-nine
   controls. If it still misses, try a bounded set of clause-vicinity assumptions:
   a checked propagation conflict proves a shorter clause. Absence of failed
   single assumptions does not rule out these consequences. Charge unsuccessful
   tuple discovery, trace checking and model transport; caps must return unknown.
3. **Test whether a smaller boundary determines the interior:** begin with
   syntactically recognized acyclic gate definitions, explicit reconstruction
   maps and checking of the original clauses. Extend the existing functional
   affine work only when justified. Test cycles, missing gate clauses, boundary
   edits and opposite polarities. Do not infer uniqueness from sampled models
   or assume that finding a small determining boundary is free.
4. **Use separators as a diagnostic control:** compare greedy width with a
   bounded ordering search and checked small separators on the unresolved leaves.
   Preserve exact boundary relations and a single consistent boundary assignment
   when recomposing. Retain preprocessing time and dense nonseparable controls.
   A width-nine heuristic result alone is not a lower bound on treewidth.

The [K-record discussion](https://www.alphaxiv.org/abs/2611.knowledge-solving-complexity-checking)
now contains a critique attributed by its commenter to Astra 6 and an author
reply describing paid, domain-specific accumulated knowledge. This clarifies
intent but supplies no new construction, verifier, finite representation or
uniform cost bound. The [26 November review](alphaxiv-knowledge-record-review.md)
remains tied to its inspected version; today's discussion and generated overview
were not treated as a revised proof. No comment, contact or publication was made
as part of this watch.

## 26 November 2026: finite circuit result and a relevant negative benchmark

Checked the live browser versions of [papers](https://pequalnp.com/papers),
[programs](https://pequalnp.com/programs) and the algorithm-search board. The paper
listing still shows Note 1. Static web extraction again returned loading shells;
the live browser was necessary to see the populated records.

The new highlighted [L-meta-18980](https://pequalnp.com/lemma#L-meta-18980), marked
checked on 26 November at 06:57 UTC, says the Hamiltonian-cycle function on the
six edge bits of a labelled four-vertex graph cannot be computed using at most
six AND/OR (fan-in two) and NOT gates, with inputs free and every gate counted.
Its [external PR](https://github.com/open-goat/pequalnp-proofs/pull/23793) is merged.
This is a finite restricted circuit claim. Locally, we checked the displayed
Boolean function against explicit Hamiltonian-cycle enumeration on all 64 graphs;
that verifies the function's interpretation, **not the circuit lower bound**.
The table and reviewed links are preserved in
`experiments/results/cnf-b10-probe-cursor/pequalnp-review.json`. We did not build
the external Lean code or independently audit its circuit definitions.

More relevant to our current gaps is the newly inspected, but **22 November**,
[L-alg-002 record](https://pequalnp.com/lemma#L-alg-002). It rejects a universal
fixed-width resolution-saturation algorithm for 3-SAT, citing Tseitin formulas
on degree-three split grids and reporting a Lean-checked width counterexample.
The supplied Lean artifact was inaccessible through the web tool; its full proof
and transitive definitions have not been independently checked here. Treat the
record as a concrete lead, not an imported axiom.

A useful follow-up is an adversarial evaluation family: encoded parity constraints
whose global inconsistency survives small local views. Measure affine recognition,
separator summaries and proof/reuse costs against bounded local saturation. This
is our proposed experiment, not a new result from the site. Resolution-width
limitations concern that proof system and do not establish limitations of all
SAT representations or of our affine route. Our checked B8/B9/B10 composition
work continues; no external claim changes proof authority or production policy.

## 25 November 2026: repeated neighborhoods and equivalent restrictions

Reviewed the live [papers page](https://pequalnp.com/papers),
[Note 1](https://pequalnp.com/papers/note-1), and the project's
[checking description](https://pequalnp.com/how). Static page extraction misses
the dynamically loaded research; an empty loading shell is not an empty feed.
Note 1 concerns circuit size of graph edge functions, not a general SAT solver.

The most relevant lead is its four-cycle example in section 6. For edges
01, 12, 23, 30, the disjunction of edge conjunctions factors as
`(x0 OR x2) AND (x1 OR x3)`. Opposite vertices have identical neighborhoods;
three assignments to `(x0,x2)` leave the same residual function. This suggests
looking for repeated neighborhoods or equal restrictions before expanding
separate branches. The elementary identity was independently checked over all
16 assignments locally. This checks that identity, not the paper's general
lower bounds or its Lean development.

A concrete future test is to identify small complete bipartite interaction
blocks or pairs with equal residuals, then compare shared representation against
separate expansions. Recognition, checking equivalence, maintaining boundary
meaning, and the effect on unit propagation must all be charged. Syntactic
equality gives a cheap sufficient test; arbitrary semantic equality is not a
free recognition step. Factoring can make representation smaller without making
an arbitrary SAT instance easy. Our existing checked residual/proof reuse
remains the starting point; the current B4 frontier experiment continues.

Treat the site's verification labels carefully. The listing displayed eight
checked claims and a human-review attribution, while the detailed paper dated
24 November described ten checked statements and explicitly said the prose had
not been read by a human mathematician. The page and embedded PDF also named
different GitHub owners. These inconsistencies do not refute the mathematics,
but a future adoption must pin the actual definitions, theorem, repository
revision, hypotheses and checker output. We did not run the external Lean code.
The paper itself separates formal statements from prose consequences and limits
several bounds to forests or graphs with long cycles and separated hubs.

Next daily check: look for changed papers/programs and concrete counterexamples;
follow the linked formal source only for a lead relevant to a current measured
gap. Do not repeat this unchanged overview or infer a P-versus-NP result.
