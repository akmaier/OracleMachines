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
original clauses retained in its indexed source tree. Local patch checks reject changes to unedited
subtrees. Incremental reference tracking removes the former full-closure scan
under layered cache pressure. At a tight cap, a single height-h source edit
temporarily reserves up to h+1 additional relation nodes until its transition
is checked, then evicts obsolete nodes. Archive history, metadata, source
payloads and process memory have separate costs.

The reference update bound is proved. Original-variable translation and complete
CNF grouping and complete initial binding now have the proofs described below;
mutable node/patch identities, JSON, persistent maps, Python/SQLite and machine
costs still have refinement obligations.
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

The grouping checkpoint connects the **complete original CNF** to its grouped
relations. The compiler carries a permutation proof preserving every clause
occurrence, including duplicates and empty clauses, together with the local
semantic equalities. Lean proves SAT/UNSAT equivalence with a consistent path
through all buckets. Individually nonempty relations need not share such a path.
A tree-summary theorem follows when exact leaf binding and identity padding are
supplied. The following checkpoint supplies this premise for complete-source
checks; preservation through native patches and replay is still open, as are
reference-count and general row/equivalence-store invariants.

At that milestone **152 tests passed**, and Lean audited **2,562 declarations / 1,233 theorem declarations**
without admits or added axioms. The new global checks cover 11,680 complete
assignments across 60 CNFs, exact clause multiplicities, service witnesses,
incompatible shared boundaries, 65,537 blocks and 12,000 repeated clauses. The
[grouping verification record](experiments/results/source-grouping/README.md)
preserves the evidence. All historical rows and all 150 prior experiment files
remained intact. That archive held **5,680 results / 1,806 refutations** after
checked revalidation. Added grouping/equality work is explicitly outside the
relation-evaluation ledger. No new timing or unrestricted-SAT claim is made.

The binding checkpoint proves **executable complete-source binding** against the
actual stored tree. `SourceBinding.lean` checks every ordered leaf and individual
identity-padding relation, then returns a proof that its decision agrees with
the original CNF. Both native full-source queries and initial source-version
binding use this result. Original-clause/provenance checks remain in place.

The scan has a proved count of one relation comparison per logical leaf. New
metrics expose that count and diagnostic cell/source-evaluation bounds. Shared
nodes still incur work for each logical occurrence. Initial source-version binding
adds a source-evaluation pass; warm queries and local edits do not repeat it.
Allocation, bit costs, transport and storage still need separate accounting.

At that milestone **156 tests passed** and Lean audited **2,615 declarations / 1,259 theorem declarations**
without admits or added axioms. New tests cover incorrect binding despite a
matching final answer, nonidentity padding that composes to identity, dimensions,
counts and 65,536 logical leaves sharing 17 native nodes. The
[binding verification record](experiments/results/source-binding/README.md)
preserves the evidence. All old rows in 21 tables and all 158 earlier experiment
files remained intact. That archive held **6,035 results / 1,935 refutations**;
all 355 distinct generic inputs and five old source versions pass revalidation.
Native identity/patch/replay invariants and complete resource bounds remain open.
The historical timing study is unchanged; this proof adds no new speed claim.

The preceding checkpoint retains **original-source meaning through native joins**.
`SourceNodes.lean` indexes source nodes by their exact layout, width, start and
height. Logical leaves keep original clauses and translation proofs; joins require
consecutive intervals and preserve all clause occurrences. The cached decision
now has SAT/UNSAT equivalence theorems for those original clauses. Native
registration and replay use these constructors; warm decisions read the summary
without flattening or traversing the source.

New metrics count registered original-source nodes, clause entries and literal
entries, including replay. The retained original integer arrays have additional
storage cost alongside JSON evidence and local translations. These counters are
diagnostic entries, not bytes or RSS. No new timing or memory-reduction claim is made.

**159 tests pass**, and Lean audits **2,751 declarations / 1,320 theorem declarations**
without admits or added axioms. Regressions cover invalid joins/layouts, failed
batches, duplicate registration, shared-variable conflicts, sparse IDs, empty
blocks, payload counters and restart. The
[source-node verification record](experiments/results/source-nodes/README.md)
preserves the evidence. Every old row in 21 tables and all 166 earlier experiment
files remain intact. The archive now holds **6,390 results / 2,064 refutations**.
Its named-store obligation is partly closed by the following checkpoint.

The preceding checkpoint proves **paired native-map and decoded-metadata
correspondence**. `SourceStore.lean` couples each named relation tree to its exact
original-source model and retains matching identity, layout, width, start, height
and original leaf clauses. Initialization, insertion and erasure preserve the
invariant without a store scan. Lookup theorems connect the retrieved tree's
decision to its original clauses. Runtime parsing, comparisons and temporary
headers remain costs; proof fields erase.

**162 tests pass**, including 23 source-update tests. Lean audits **2,858
declarations / 1,367 theorem declarations** without admits or added axioms.
New regressions cover deletion-batch rollback, shared descendants, safe identifier
reuse, distinct provenance with equal relations and missing-field rollback.
The [source-store verification record](experiments/results/source-store/README.md)
preserves the evidence. All 355 older generic inputs and five saved source
versions pass current-engine revalidation. Every old row in 21 tables and all
174 earlier experiment files remain intact. The archive holds **6,745 results /
2,193 refutations**.

The preceding checkpoint proves **named child registration and serialized-summary
binding**. `SourceLinks.readJoin` connects decoded child names to the exact models
retrieved at registration, then proves original-clause composition and the need
for one valuation satisfying both sources. Conditional lemmas preserve links
under fresh insertion and deletion avoiding both children. The paired native
store also retains exact equality between each decoded mask's relation and its
model's cached summary.

**165 tests pass**, including 26 source-update tests. Lean audits **2,874
declarations / 1,380 theorem declarations** without admits or added axioms.
The [source-link verification record](experiments/results/source-links/README.md)
records malformed child/mask checks, distinct provenance under equal relations,
and shared-child retention across shuffled parent deletions. All 355 generic
inputs and five saved source versions pass revalidation. Every old row in 21
tables and all 182 earlier experiment files remain intact. The archive holds
**7,100 results / 2,322 refutations**.

The preceding checkpoint proves **native source dependency lifetime**.
`ReferenceCounts.lean` relates incoming counts to the exact number of decoded
child occurrences across live parents. `SourceLifetime.lean` uses count zero to
prove safe deletion and preserves each surviving branch's exact named children.
The executed source context carries these invariants through fresh insertion and
deletion; duplicate definitions change no state. The aggregate sum and finite
parent-domain witness exist only in proofs. Updates still touch at most two
direct child counts, without scanning the store.

**166 tests pass**, including 27 source-update tests. Lean audits **2,944
declarations / 1,416 theorem declarations** without admits or added axioms.
An independent full-graph recount checks eviction decisions for 44 nodes with
16 roots, shared descendants, duplicate registrations and randomized deletion,
followed by complete reclamation and reuse of the same names. The
[lifetime verification record](experiments/results/source-lifetime/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every previous row in 21 tables and all 190 earlier experiment files remain
intact. The archive holds **7,455 results / 2,451 refutations**.

Next is exact requested-patch semantics. Python retention, the generic relation
store, complete persistence refinement, acceptance completeness and full resource
costs remain separate obligations. No new timing or unrestricted-SAT guarantee
is claimed.


The preceding checkpoint proves **exact native source-patch semantics**.
`SourcePatch.lean` connects decoded request fields and current live root/child
lookups to the original arrays: every requested bucket gets its supplied clauses,
and every unedited bucket stays unchanged. Equal relations cannot substitute for
exact original arrays. The executed checker carries this certificate and keeps
its path-visit counter; the proofs add no full-source scan or relation join.

**169 tests pass**, including **30 source-update tests**. Lean audits **3,043
declarations / 1,461 theorem declarations**, with no admits or added axioms.
New checks cover split-path edits with padding, order and duplicate original
clauses under equal relations, invalid requests/roots/partitions, unchanged
aliases, and the complete 4,096-entry decoding cap. Runtime checkpoint `32b4748`
is committed and pushed. The [patch verification record](experiments/results/source-patches/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every old row in 21 tables and all 198 earlier experiment files remains intact.
The archive now holds **7,810 results / 2,580 refutations / 50 source-state rows**.

Next is composing initial raw-CNF binding, complete root coverage, the
bucket-to-flattened-CNF transition and the returned verdict/witness into one
successful-request theorem. Python retention, complete replay/SQLite refinement,
generic relation/factor stores, acceptance completeness and total resource costs
remain open. The updated checker pays for direct lookups, decoding, edit-list
filtering and array comparisons. Earlier timings are unchanged; no speedup or
unrestricted-SAT guarantee follows.


The preceding checkpoint proves **complete successor formulas and returned native
decisions**. `SourceFormula.lean` connects ordered bucket flattening to the exact
original clause list, characterizes interval coverage and empty padding, and
proves that an accepted patch gives the complete requested successor CNF.
`SourceVerdict.lean` certifies root coverage and the actual returned answer field.
The exposed query/patch functions have success theorems, including the nested
patch verdict, with both SAT and UNSAT equivalences for the original formula.

**171 tests pass**, including **32 source-update tests**. Lean audits **3,107
declarations / 1,506 theorem declarations**, with no admits or added axioms.
New tests reject incomplete, shifted and oversized roots and check actual verdicts
against exhaustive truth tables over 54 transitions with 1, 3 and 5 logical edges.
They include padding, old branches, deletion, repeated and empty clauses, and both
answer modes. Runtime checkpoint `9673dee` is committed and pushed. The
[verdict verification record](experiments/results/source-verdicts/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every old row in 21 tables and all 206 earlier experiment files remains intact.
The archive holds **8,165 results / 2,709 refutations / 55 source-state rows**.

Next is the complete initial raw-CNF anchor and composition over accepted
operation histories. Serialized witness contents, byte transport, Python
retention and complete replay/SQLite refinement also remain open. Flattening is
specification work; warm decisions add no full-source scan or summary rebuild.
Total physical/resource costs and unrestricted coverage are not established.
Earlier timing evidence remains unchanged.


The latest checkpoint closes the **initial raw-CNF binding** gap.
`SourceInitial.lean` connects the actual request getters to the live root's exact
original buckets, complete coverage, clause permutation and returned verdict.
Grouping may reorder clauses globally; duplicate and empty clause occurrences
remain intact. `SourceUpdates.bindSource_success` covers the native JSON-returning
function. The executed original-bucket scan proves `visits + 1 = 2^(height + 1)`
and `height < 17`; this counts logical visits, not total machine work. Initial
compilation and both complete binding scans remain charged. Warm paths are unchanged.

**174 tests pass**, including **35 source-update tests**. Lean audits **3,154
declarations / 1,539 theorem declarations**, without admits or added axioms.
Runtime checkpoint `92a1ddd` is committed and pushed. The
[initial-binding verification record](experiments/results/source-initial/README.md)
records all 355 generic inputs revalidated, five source versions adopted and
restarted, every old row in 21 tables preserved, and all 214 earlier experiment
files unchanged. The archive holds **8,520 results / 2,838 refutations / 60
source-state rows**.

Next is composition over accepted operation histories. Serialized witness values,
byte transport, Python active-root retention, replay/SQLite refinement, generic
stores, acceptance completeness and complete resource bounds remain open. Earlier
timings are unchanged; no new unrestricted-SAT guarantee follows.

## Certified affine growth

The affine path adds fresh variable blocks while retaining an exact summary of
all preceding parity equations. Its summary has at most `b+1` equations over a
width-`b` boundary, or `(b+1)^2` coefficient/right-hand-side cells. One resident
append with `c` new equations has reference charge `O(b^3 + b^2*c)`. The native
solver executes the Lean-certified coefficient operations; it does not enumerate
boundary assignments. This is a restricted affine result using established
Gaussian elimination, with explicit construction and replay costs.

Original batches, immutable versions and results persist in SQLite. Restart
replays original equations, and adding a contradictory batch never changes a
saved parent's answer. The interface is decision-only, with an optional boundary
summary; it does not return a full-history witness. Width, batch and resident
version caps are explicit refusals. General CNF, arbitrary older-variable edits,
complete persistence refinement and total machine-cost bounds remain open.

See the [API and limits](solver/README.md#affine-growth),
[formal contracts](formal/README.md#affine-growth), and
[archived validation](experiments/results/affine-growth/README.md).
The checkpoint passes **184 tests** and the Lean audit of **3,485 declarations /
1,708 theorem declarations**. It retains all prior results and 268 affine versions.

The next checkpoint (`88f26a8`) composes the native source-CNF response contracts
across arbitrary finite request histories, including rejected batches and layout
resets. Earlier observations keep their event-specific source meaning; reused
names are not assumed to denote the same formula after deletion/reset.

Affine native histories now use erased proof data, so resident children do not
keep runtime ancestor states reachable. The service bounds resident versions independently
of archive length and replays old branches with eviction. A 4,101-append test grows
and restarts with only two resident versions. All **190 tests pass**; Lean audits
**3,625 declarations / 1,766 theorem declarations**. Complete Python/SQLite
refinement, broader decompositions and total machine costs remain open.
See the [history and retention record](experiments/results/history-retention/README.md).

Checkpoint `1037595` connects affine decoded Boolean inputs and named-store
histories to the original-equation invariant. **192 tests** and the Lean audit
of **3,794 declarations / 1,836 theorem declarations** pass. Expansion work is now
prioritized around compression and reuse: the repeated affine streams contain
14 identical algebraic calls among 18 distinct history expansions. This motivates
an exact transition cache, implemented in the next checkpoint below. See the
[current gap record](research/implementation-gaps.md) and
[pattern evidence](experiments/results/affine-history/README.md).

Checkpoint `f80f678` implements exact certified transition reuse. A cache hit
checks the full boundary summary and equation batch, reuses the algebraic result,
and attaches it to the new version's own history. Hash collisions cannot authorize
reuse. The cache is configurable, bounded by slots, and disabled with
`affine_kernel_slots=0`.

In five matched repetitions, repeated width-16 streams fall from **167.57 to
144.21 ms** and repeated width-32 streams from **496.37 to 215.54 ms** (2.30x).
Novel streams have no hits and roughly unchanged timings with slight median
overhead. These are synthetic affine results, without a general SAT speed claim.
All **197 tests** and the Lean audit of **3,938 declarations / 1,875 theorem
declarations** pass; all 405 older experiment files and old archive rows remain.
See the [cache experiment and limits](experiments/results/affine-kernel-cache/README.md).


## Shared affine batches and certified preparation

Checkpoint `e0cb8d3` adds duplicate-free computation and adaptive original-batch
sharing. Prepared typed rows and normalized transitions can be reused across
histories with different duplicate counts. The source archive retains exact row
order/multiplicity and legacy version identities; existing rows are unchanged.

In five matched repetitions, width-32 changing-multiplicity streams fall from
**1,246.55 to 430.52 ms** with both options. Repeated width-32 source payload falls
**16,656 -> 6,499 bytes**, and database size falls by **12 KiB**. That storage gain
costs **6.6%** more elapsed time on the exact repeated stream. Novel streams gain
no reuse. Native request JSON is still per version, so these measurements do not
establish a reduction in process memory. Each cache has its own slot occupancy;
byte budgets and batch handles remain open.

All **207 tests** pass; Lean audits **4,043 declarations / 1,911 theorem
declarations**. Every old archive row and all 583 earlier experiment files remain.
See the [four-mode evidence and remaining limits](experiments/results/affine-batch-reuse/README.md)
and [current expansion priorities](research/implementation-gaps.md).


The [current resource-bounds audit](research/resource-bounds.md) separates general
SAT, finite coverage, factor/layered expansion, affine hits/misses, cold replay,
live memory and archive growth. It records exact formal bounds, derived payload
accounts, configured refusals, measured phase costs and the remaining proof gaps.

The [resident-width follow-up](experiments/results/affine-resident-metadata/README.md)
removes a redundant parent decode: shared warm appends use seven instead of nine
object reads. All 210 tests pass; the native proof code and earlier archive remain
unchanged. The [KD-tree assessment](research/indexed-reuse.md) distinguishes exact
lookup from candidate search for a future checked repair path.
