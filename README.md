# Oracle Machines

A perspective on **resource accounting for learned reasoning**: how preprocessing,
stored knowledge, neural representations, and exact solvers redistribute computation
between acquiring an answer and using it later.

**Terminology:** SAT with no fixed size cap remains the satisfiability problem.
UNSAT denotes unsatisfiable valid formulas and is coNP-complete. An invalid
encoding is neither a satisfiable nor an unsatisfiable formula.

The central architectural conclusion is that **the efficiency rationale for
combining System 1 and System 2 survives either resolution of P versus NP**.
Either way, the relevant comparison is avoided computation versus acquisition,
retrieval, verification, and control costs. Actual savings depend on the workload
and implementation.

The exact reuse identity applies to **every decidable language**, including
problems in PSPACE, EXPTIME, and EXPSPACE. This generality concerns the cost
comparison. Cheap certification, compact storage, and efficient acquisition need
their own justification, and finite tables for an undecidable language do not
provide a uniform computable way to construct them.

The project connects established ideas from complexity theory, knowledge
compilation, memoization, and amortized inference to the interaction between fast
and deliberative computation. Its contribution is an explanatory synthesis; the
finite-domain constructions do not establish a collapse of unrestricted complexity
classes.

## Paper

The current draft is **Bounded-Domain SAT, Compiled Knowledge, and Amortized
Reasoning: A perspective on resource accounting for learned reasoning**.

- [LaTeX source](paper/bounded_domain_sat_and_amortized_reasoning.tex)
- Author: Andreas Maier
- Status: working draft
- Format: self-contained LaTeX with embedded bibliography and TikZ figures

The paper distinguishes the costs of construction, storage, inference, training,
verification, and fallback solving. It examines exact finite-domain SAT tables,
finite restrictions of language classes, oracle simulation, explicit ReLU
representations, nonuniform advice, caching, and certified fallback. System 1 and
System 2 serve as a computational analogy, not as complexity classes.

The expanded draft compares these ideas with neural-advice and speedup-learning
literature, discusses the failed Deolalikar argument and Wen's learned-oracle
claims, and proves conditional expected-savings and bounded-overhead results.
An exact reuse identity states when avoiding repeated solves repays cache costs.
These savings conditions apply whether P = NP or P != NP, and a scaling example
shows how reuse can help even when solving has polynomial cost.
The detailed argument audit makes setup costs explicit in every cache bound,
states the finite-expectation assumptions for unbounded query domains, and proves
that uniform computable construction of exact finite tables is equivalent to
decidability. It also explains why optimal metareasoning can remain hard.
The literature comparison attributes the utility criterion to Minton, discusses
self-improving algorithms for polynomial-time tasks, and relates fast/slow
arbitration to Milli et al. and SOFAI. These are established precedents for the
paper's explanatory cost bounds.
The follow-up search adds Goré and Nguyen's published global-caching solver for
an EXPTIME-complete problem and Ferrara et al.'s model-checking preprocessing
work. The finite-table construction criterion is explicitly attributed to
standard computability, and the EXPTIME obstruction to the time hierarchy.
These connections strengthen the perspective without establishing theorem novelty.
An explicit induction now constructs exact answers on successively larger finite
domains. Separate results state the uniform expansion bounds that would imply
polynomial-time decision and the workload conditions that amortize costly
expansion. The correctness induction supplies neither bound by itself and does
not prove P = NP.
The executable development now supplies an exact SAT solver, a counted binary
parser, polynomial bounds for fixed or logarithmically growing variable ranges,
and certified witness reuse. A reference fallback adds lazy search on distinct
occurring variables, sound partial-assignment pruning, and reusable checked
refutation trees. Bounded witness and refutation portfolios survive restarts;
all earlier results remain archived.
The default service now adds shared AIG simplification, a bounded local attempt,
and CaDiCaL's mature CDCL engine. SAT witnesses and LRAT UNSAT proofs must pass
Lean checkers. The formula-to-CNF connection is proved; the external solver's
verdict is never sufficient. Indexed proposals and a long-lived JSON-lines
service reduce retrieval and startup overhead. These modern paths report wall
time and explicitly mark their abstract work counts as unmeasured.
An explicit evaluator machine realizes the reported evaluation count exactly
and has a checked bound on intermediate data size. A converse encoding proof
extends the restricted bounds to every accepted binary request.
The [persistent solver](solver/README.md) retains every completed result across
restarts. The [reproducible studies](experiments/README.md) compare reuse with
lazy solving and checked CDCL, while retaining the earlier exhaustive reference.
They do not establish efficient exact learning on unrestricted instances.

The seven-item follow-up adds compact restricted coverage, a complete assignment
search transition system with payload bounds, live CaDiCaL clause reuse, a bounded
persistent predictor, query deadlines, strict cache checks, and disjoint measured
phases. At that milestone, all 69 tests and the 694-theorem axiom audit pass. The expanded study checks
1,260 answers on public and chronological streams and reports gains, overhead,
and memory costs. [Implementation scope](research/implementation-gaps.md) records
which engineering gaps are addressed and which stronger mathematical claims
remain open. None of these changes establishes unrestricted polynomial SAT.

The structural follow-up targets items 1 and 4. Lean proves exact composition
through a bounded shared interface, so total variables may grow while local
acquisition stays bounded. `--components` implements independent-component reuse
under variable renaming and checked transfer of UNSAT cores to added constraints.
`--incremental` now saves stable circuit definitions and selected learned clauses
across restarts. Shared immutable terms, shapes, maps and prefixes reduce
duplication; full request archival costs remain.

The [structural study](experiments/results/structural/summary.json) checks another
420 answers. One acquired shape serves 127 component occurrences through
expansion to 128 variables. Connected-chain and storage controls show the limits:
that component-only milestone leaves nonempty interfaces for the next extension,
and the whole database can grow despite sharing. Try
`python3 solver/persistent.py --components --incremental serve`.

The five-step extension now adds local bucket elimination, persistent add/replace/
remove snapshots, lazy checked rows, semantic relation storage, and checked
incremental LRAT. Use `--interfaces` for the delta API and `--incremental-proofs`
for the proof-enabled live CDCL path; they can be combined for checked fallback.
The [first interface study](experiments/results/interfaces/README.md) reports 792 correct
answers, local reuse and transport savings, and the overheads of checking,
restart and archival storage. That milestone passed 95 tests and audited 837
theorem declarations. All 2,130 older results and 516 proofs remain unchanged, with 355
newly revalidated results and 129 proofs added. The manuscript now includes the
local elimination and shared-circuit proof arguments, their cost boundaries,
and published BDD representation limits. Small width, affected-state size and
cheap acquisition for unrestricted SAT remain unproved.

The central question is when the expense of acquiring reusable knowledge is repaid
by reduced future computation. Exact representability alone establishes neither
compactness nor efficient learning, and a correct hybrid need not be faster overall.

## Build

Install a LaTeX distribution with `latexmk` and the packages used by the source
(including `newtx`, TikZ, and `natbib`). From the repository root:

```sh
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error bounded_domain_sat_and_amortized_reasoning.tex
```

Alternatively, run `pdflatex` twice:

```sh
cd paper
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
```

The PDF is generated alongside the source. To remove auxiliary build files while
keeping the PDF, run `latexmk -c` from `paper/`.

## Repository layout

```text
paper/
  bounded_domain_sat_and_amortized_reasoning.tex
formal/
  OracleMachines.lean
  OracleMachines/
  lean-toolchain
  lakefile.toml
  lake-manifest.json
  README.md
solver/
  persistent.py
  test_persistent.py
  README.md
experiments/
  run_workloads.py
  results/
research/
README.md
LICENSE
```

## Lean verification

The [Lean project](formal/README.md) checks the expansion invariant, explicit
table size, conditional polynomial cost bound, staged savings criterion, and
amortization limits. It also proves that the explicit table and exponential
expansion costs are not polynomially bounded. A theorem map identifies the exact
coverage and remaining obligations.

With Lean's version manager installed, run:

```sh
cd formal
lake exe cache get
lake build
```

The toolchain and dependencies are pinned. The default build audits all declarations in the formal library
namespace for admitted proofs and additional axioms. The formalization treats
general runtime costs as explicit numerical ledgers and connects a concrete
SAT parser and core to an operational cost model. It proves polynomial bounds
for a **fixed** variable cap and for variable width at most `floor(log2(L+1))`,
where `L` is the encoded length. These restrictions do not give a bound for all
SAT inputs or a formalization of P versus NP.
The evaluator's transition and data-size proofs are a component of a runtime
argument for complete-witness evaluation; combined machine simulations for
parsing, partial evaluation, and full search remain open. The lazy search has a
checked bound of `2^(d+1)-1` nodes for `d` distinct occurring variables. Refutation
size can still be exponential.

## Persistent solver

Build the executable with `./solver/build.sh`. Then, from
the repository root, run `python3 solver/persistent.py solve 010`. Subsequent
calls reuse the result from `solver/.cache/results.sqlite3`; new formulas can
also reuse retained witnesses and refutation certificates after checking them. SAT and UNSAT
results accumulate without eviction. The [service documentation](solver/README.md)
covers encoding, storage, restart behavior, integrity checks, and testing.
The database is local and ignored by Git; source code and reproducible experiment
results are versioned.
Use `python3 solver/persistent.py serve` for multiple JSON-lines queries in one
process. The default `auto` backend combines local checks with certified CDCL;
`--backend lean` retains the original counted lazy solver.

## Literature review

The [annotated literature review](research/literature-review-2026-11-07.md) compares
the draft with work on neural advice, speedup learning, compilation, and failed
complexity proofs, including Deolalikar and Wen. It includes
[supplementary BibTeX](research/related-work.bib) and saved OpenAlex/SemOpenAlex
query evidence. The closest precedents and relevant historical cautions are now
integrated into the manuscript's self-contained bibliography.

The review also contains a [detailed proof audit](research/literature-review-2026-11-07.md#detailed-argument-audit-and-scope-beyond-np)
covering every formal argument, the repaired accounting omission, and the limits
of extending the result beyond NP.
The [publication-status reassessment](research/literature-review-2026-11-07.md#publication-status-of-the-generalized-observations)
maps the generalized claims to prior work and distinguishes checked publications,
an MSc thesis, and sources whose full text could not be verified.
The [induction audit](research/literature-review-2026-11-07.md#inductive-expansion-proof-and-limitations)
checks the expanding-domain proof, its cost conditions, and counterexamples to
an unconditional polynomial-time conclusion.

## License

This repository includes an [MIT license](LICENSE).


## Scaling follow-up

The solver now supports affected-bucket updates, direct bounded BDD operations,
live graph/proof reuse, checked negative-core transfer, logical archive caps and
measured full-query route selection. All historical results remain persistent.
The [scaling study](experiments/results/scaling/README.md) records 1,470 correct
answers, including 672 UNSAT, across 147 runs. The earlier milestone passed 106 tests and
audited 879 theorem declarations. The [formal notes](formal/README.md) state
conditional resource bounds and the remaining refinement obligations.

Reuse reduces selected acquisition/planning costs, but checked solving remains
faster on several measured streams. Direct symbolic compression does not give a
polynomial bound on arbitrary intermediate diagrams. Logical database limits do
not bound whole-process memory; capacity exhaustion preserves history and stops
acquisition. The unrestricted polynomial SAT argument remains open.


## Durable reuse and balanced-chain follow-up

The latest implementation adds durable batches, persistent bucket maps, balanced
chain summaries, fused symbolic projection, individually checked proof fragments,
and structural routing with reserved fallback time. **114 tests pass**; Lean
checks **941 theorem declarations**. The explicit chain API uses ten compositions
and eleven node writes for a replacement at 1,024 edges. Whole witnesses and
service costs are accounted separately.

The [new study](experiments/results/followup/README.md) records 2,259 correct
answers and 30 archive-cap errors across 210 runs, including selected TACAS 2026
artifact inputs and a held-out counter. It preserves failures, resource samples,
and every older dataset. The live archive retains all historical rows and now
contains 3,550 results and 1,032 proofs. The [gap register](research/implementation-gaps.md)
and revised manuscript distinguish these implementation results from the open
unrestricted width, representation, acquisition and full-machine obligations.

## Bounded layers and comparable inputs

The latest [study](experiments/results/structured/README.md) adds checked Boolean
layers of width 1–4, persistent source/order indexes, payload-limited active
caches, WAL checkpoint controls, and failure-aware route scores. The layer
replacement theorem exposes exponential width dependence and logarithmic depth;
full witnesses and service overhead remain separate. Native materialization was
also repaired after inspecting generated C.

All **119 tests pass**, and Lean audits **991 theorem declarations**. A new
175-run comparison completes 2,450 queries correctly, with enabled learning,
three additional artifact families and identical full-formula service inputs.
Learning helps the signed-unit stream but does not improve the public-only
streams. A separate cache-pressure study retains every historical state while
measuring the cost of smaller active retention. All older datasets and archive
rows remain unchanged; the live store now holds 3,905 results and 1,161 proofs.
The [gap register](research/implementation-gaps.md) records what remains open.

## Seven-priority follow-up

The current implementation separates semantic row reuse from current provenance,
uses iterative lazy evaluation, retains complete native layered working sets,
and records final route outcomes once. Speculative witness/proof checking now
has a separate budget and measured outcomes. A new `layered_cnf` API checks and
compiles CNF under a supplied adjacent-block partition; it does not discover a
bounded-width decomposition for unrestricted SAT.

**129 tests pass**, and Lean audits **1,047 theorem declarations**. The new
costed reference returns operation counts and is proved equivalent to tree
replacement. Additional proofs cover relation comparison, full witness traces,
prefix/suffix composition and mathematical source binding. Whole-service cost
and protocol refinement remain open. The [priority gap register](research/implementation-gaps.md#seven-priority-implementation-follow-up)
distinguishes implemented improvements from those remaining obligations.

The [new evaluation](experiments/results/priorities/README.md) adds unused public
members, larger mixed-label application sources, a no-training polarity baseline,
matched live/restarted proof modes and distinct-relation pressure. Its
[development pilot](experiments/results/priorities-pilot/README.md) is preserved.
Every previous database row and all 93 historical experiment files remain intact.
The live solver contains **4,260 results / 1,290 proofs**, plus saved expansion
branches and source bindings checked again after restart.

## Incremental CNF source versions

`source_cnf` preserves the actual clauses in a balanced tree alongside their
checked relations. A local edit replaces an edge's entire clause bucket; an
empty bucket deletes its clauses. The supplied disjoint ordered variable
partition stays fixed, with a supplied width from one to four and at most that
many variables per block. Every clause must
fit in one block or two neighboring blocks. There is no decomposition discovery
or unrestricted-SAT width guarantee.

```python
from solver.persistent import PersistentSolver

with PersistentSolver() as solver:
    first = solver.source_cnf(1, [[1, 2], [-1, -2]], [[1], [2], [3]])
    contradiction = solver.source_cnf(base=first['state'], replace={0: [[1], [-1]]})
    deleted = solver.source_cnf(base=contradiction['state'], replace={0: []})
    assert first['answer'] and not contradiction['answer'] and deleted['answer']
```

Use `op: "source_cnf"` with the same fields in the JSON-lines service. Queries
are decision-only by default; `witness=True` requests the complete block-state
path and adds its output/checking cost. Versions remain in the SQLite archive
and are replayed and checked after restart. After a checker upgrade, the saved
clauses and summaries are checked by the new engine before a current result is
stored; old answer bits are ignored and every old row remains intact. The result
reports `revalidated_source=True` on first use from an older namespace. A
different partition starts a new source family and pays initial compilation.

The native decision carries a Lean proof connecting its cached summary to the
current local-source tree. Local patch checks reject changes to unedited
subtrees. Incremental reference tracking removes the former full-closure scan
under layered cache pressure. At a tight cap, a single height-h source edit
temporarily reserves up to h+1 additional relation nodes until its transition
is checked, then evicts obsolete nodes. Archive history, metadata, source
payloads and process memory have separate costs.

The reference update bound is proved. Original-variable translation and complete
CNF grouping now have the proofs described below; native tree binding, JSON,
persistent maps, Python/SQLite and machine costs still have refinement obligations.
General factor-DAG provenance, adaptive gating and unrestricted structural
coverage are unchanged. At this milestone **141 tests passed**, and Lean audited
**2,279 declarations / 1,106 theorem declarations**. See the
[source-update study](experiments/results/source-updates/README.md) for matched
full-source rebuilding, lifecycle costs, replay, stored bytes and sampled RSS.

The follow-up uses an indexed assumption check for general-factor negative
proofs. Lean proves equality with the previous membership condition, including
duplicates; counters report index entries and membership probes. It avoids
repeated list scans while retaining the full evidence traversal. Initialization
failures now close their database handles, and the two test-owned connection
leaks are fixed. At that checkpoint **144 tests passed without resource warnings**,
and Lean audited **2,290 declarations / 1,113 theorem declarations**.

That checkpoint's live archive held **4,970 results / 1,548 refutations**, with all older
rows preserved. The [context and upgrade report](experiments/results/context-index/README.md)
records the diagnostics and checked source adoption. To revalidate the earlier
source-study records after updating the solver, use:

```sh
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

This checks historical source fingerprints and recorded evidence; it reports the
current binary separately and does not claim to rerun the historical executable.

The mapping checkpoint proves the conversion from original variable IDs to bounded
block states. Native positions carry array-lookup and width proofs; an alignment
pass establishes completeness. Both compilation paths now use checked local
translations. Lean proves that each translated CNF bucket is satisfiable exactly
when its boundary relation has an accepting pair. The proof includes short and
empty blocks and unused variables. The following checkpoint proves global clause
grouping; the connection through native node identities remains separate.

At that milestone **148 tests passed**, including exhaustive checks of 9,520 boundary
assignments across 112 local CNFs through both native compiler paths. Lean audited
**2,477 declarations / 1,188 theorem declarations**. Alignment and source
equality checks add passes and temporary arrays; these costs are outside the
existing relation-evaluation counter. This checkpoint makes no new speed claim.

The [mapping verification record](experiments/results/source-mapping/README.md)
preserves build/test logs, fingerprints and archive revalidation. That archive
held **5,325 results / 1,677 refutations**. Every old row in all 21 tables and
all 142 earlier experiment files remained intact. The five saved source versions
were rechecked under the new engine and after restart. The
[persistent gap analysis](research/implementation-gaps.md) records the next proof,
accounting and evaluation obligations.

The latest checkpoint connects the **complete original CNF** to its grouped
relations. The compiler carries a permutation proof preserving every clause
occurrence, including duplicates and empty clauses, together with the local
semantic equalities. Lean proves SAT/UNSAT equivalence with a consistent path
through all buckets. Individually nonempty relations need not share such a path.
A tree-summary theorem follows when exact leaf binding and identity padding are
supplied. Proving that the native mutable protocol supplies those premises is
still open, as are reference-count and general row/equivalence-store invariants.

**152 tests pass**, and Lean audits **2,562 declarations / 1,233 theorem declarations**
without admits or added axioms. The new global checks cover 11,680 complete
assignments across 60 CNFs, exact clause multiplicities, service witnesses,
incompatible shared boundaries, 65,537 blocks and 12,000 repeated clauses. The
[grouping verification record](experiments/results/source-grouping/README.md)
preserves the evidence. All historical rows and all 150 prior experiment files
remain intact. The archive now holds **5,680 results / 1,806 refutations** after
checked revalidation. Added grouping/equality work is explicitly outside the
relation-evaluation ledger. No new timing or unrestricted-SAT claim is made.
