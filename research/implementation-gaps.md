# Implementation follow-up: seven remaining gaps

This record tracks the work requested on 7 November 2026. A completed
implementation is distinguished from a stronger theorem that it does not prove.
Earlier experiments and persisted results must remain intact.

| Item | Concrete work | Stronger claim that must not be inferred |
| --- | --- | --- |
| 1. Uniform expansion | Executable compact coverage states for the logarithmic-width SAT family, with preservation, coverage, construction-size and query-cost theorems. | Uniform polynomial-time SAT for unrestricted inputs. |
| 2. Accounting | Disjoint elapsed phases, child resource measurements, certificate and storage sizes, explicit unknown formal costs. | A complete machine-level cost proof for external CDCL or SQLite. |
| 3. Machine/memory | Extend operational semantics and storage bounds beyond one evaluation; expose remaining bit-machine obligations. | Verified compilation/runtime or constant-memory search. |
| 4. Internal reuse | Long-lived CaDiCaL over shared circuit definitions and root assumptions; independently check answers. | An incremental UNSAT proof checker if negative answers still require a fresh LRAT run. |
| 5. Service guarantees | Deadlines covering native work and certificate checks, bounded message/proof sizes, recovery, checked-cache option, and rollback tests. | Kernel verification of Python, the OS, and SQLite. |
| 6. Learned proposals | Persist a compact online predictor, charge updates, check every proposal, and test chronological held-out transfer. | Efficient exact learning of unrestricted SAT. |
| 7. Evidence | Public SATLIB instances and structural/shift streams; direct and checked baselines; retained failures/timeouts; memory and acquisition costs. | Universal speedup or a representative SAT-competition result. |

First implementation milestone:

- `CompactExpansion.lean` proves preservation, eventual coverage, construction
  cells/steps, SAT/UNSAT soundness, and the restricted reference-query bound.
- `SearchMachine.lean` proves operational search composition and reachable-state
  payload bounds. Parsed programs and assignment generation remain supplied.
- Live CaDiCaL clause reuse, a checksummed bounded predictor, disjoint elapsed
  phases, deadline-aware I/O, monitored external files, and strict cache checking
  are implemented. Internal clauses remain live-session state; saved results,
  certificates and models survive restart.
- Lean's transitive axiom audit: 1,197 declarations / 651 theorem declarations.
  All 57 integration tests pass, including truth-table comparisons, timeout
  recovery, forged proposals/cache entries, concurrent model updates, and DIMACS
  conversion. No proof admits or new axioms were introduced.

The final public/chronological benchmark and manuscript now include this work.
The stronger claims in the final column remain open.

The public pilot exposed native stack exhaustion during counted length discovery.
A proved compiler replacement now preserves the exact value and ledger while
using stack-safe list length; ASCII decoding accumulates iteratively as well.
A regression test covers an encoding over 500,000 bits. The pilot is retained
in `experiments/results/expanded-pilot/`, including 32 failures (12 direct
DIMACS trailer errors, 20 checked-path stack overflows).

Evidence at the first follow-up milestone (items 1 and 4 are extended below):

| Item | Implemented and checked | Remaining boundary |
| --- | --- | --- |
| 1 | Compact coverage, exactness/preservation, unary construction, restricted decision ledger; native demonstration. | No unrestricted polynomial constructor. Coverage/promise checks are outside that ledger. |
| 2 | Disjoint wall-time phases, service/reaped-child CPU, process RSS, proof/model/database bytes, explicit unknown formal totals. | No full CDCL/SQLite instruction proof, simultaneous process-tree peak, energy or hard physical memory cap. |
| 3 | Complete assignment-search traces, reachable-state payload bound, restricted quadratic space, proved stack-safe length replacement. | Parsing/generation are supplied to the trace; no full bit-machine/compiled-runtime proof or production-CDCL memory proof. |
| 4 | Shared live circuit clauses, retained learned clauses and root assumptions; every proposed result checked independently. | Internal clauses do not survive restart; negative proposals still use a fresh LRAT run. |
| 5 | Query deadlines, size limits, bounded child I/O, reaping/recovery, SQLite rollback, strict-cache rechecking and adversarial tests. | Cooperative timing, outer transport and OS/runtime trust remain; budgeted service can return an error. |
| 6 | Bounded persistent predictor, charged training from checked answers, transactional concurrent updates, chronological new-witness transfer. | Simple tractable family; no exact general-SAT learning guarantee or universal savings under shift. |
| 7 | 28 public SATLIB instances, four chronological/structural streams, six modes, three repetitions; all 1,260 answers correct. | Older small suites, local host noise, no current competition baseline or equal-total-memory study. |

The benchmark and manuscript report regressions as well as gains. Internal
retention does not isolate the causal contribution of learned clauses. The
combined predictor policy includes other mechanisms; incremental alone performs
similarly on signed units. Initial benchmark execution overlapped the test suite
briefly; small timing differences should not be interpreted as significant.

The live store preserves all 1,420 previous rows and 258 proofs, adds 355 checked
current-engine results and 129 proofs, and retains a bounded current model.
`experiments/results/expanded/persistence.json` records the replay, semantic audit,
and hashes confirming preservation. Four historical experiment datasets are
unchanged. `expanded-pilot/` preserves the development failures; `expanded/`
contains the final data and source/binary fingerprints.

## Structural follow-up on items 1 and 4

The next implementation milestone adds bounded-interface composition in
`Components.lean` and durable structural knowledge in the service. The formal
result allows total variables to grow through disjoint private blocks: the
exponential parameter is local plus interface width. Its declared acquisition
budget charges each distinct shape once; intersections charge each occurrence.
It does not prove that arbitrary SAT admits such a decomposition.

`--components` implements the empty-interface case. It normalizes variable names,
shares component results and content-addressed terms/shapes/maps/prefix nodes,
and checks the recomposed witness. A native checked conjunct certificate allows
renamed UNSAT cores to survive new constraints, including component mergers.
It does not transfer under arbitrary deletion or negation. Nonempty-interface
summary construction and separator discovery remain implementation gaps.

Incremental sessions now archive stable circuit definitions and selected short
learned clauses in immutable compressed objects. Restarts replay a bounded
clause subset; concurrent workers fork sessions. This is untrusted proposal
state, not incremental LRAT certification. General negative proposals still
require an independent proof. Active caps never delete the historical archive.
The original full-input result archive still grows independently of structural
compression; all storage categories must remain in the accounting.

Validation at this milestone: 69 integration tests pass; the Lean axiom audit
checks 1,264 declarations / 694 theorem declarations. Tests cover incompatible
positive components, renamed and extended negative cores, forged component
records, truth-table comparisons, durable clauses, poisoned replay state,
concurrent sessions and schema migration without lost results.

The structural study completes this follow-up with 420/420 correct answers.
One two-variable component shape serves 127 occurrences across expansion to
128 variables; one UNSAT core survives six connected extensions. The chain
control still needs seven acquisitions. The full component database is larger
than the checked baseline despite reduced duplication, so no whole-archive
compression or universal speedup claim is made. The paper now contains both
restricted structural proofs, prior-work attribution, measured overheads and
remaining boundaries.

Next steps recorded at the structural milestone:

1. Find and verify small separators, then implement the nonempty-interface
   relations proved in Lean. The present runtime uses disjoint components only.
2. Support proof-carrying incremental learned clauses and certification of
   general negative proposals. Current certified negative reuse transfers
   existing conjunct cores; otherwise an independent LRAT run remains necessary.
3. Extend the declared structural ledger to concrete acquisition, normalization,
   compressed retrieval and verification costs. Establish total-memory policies
   without confusing an immutable evidence archive with a bounded active model.
4. Broaden equivalence detection beyond first-occurrence renaming and fixed term
   order, while charging the matching cost. The four-instance negative index
   deliberately provides incomplete retrieval.

These are implementation and restricted-proof tasks. No argument currently
bounds local/interface width, exact representation size or acquisition time
polynomially for unrestricted SAT.

## Implementation of local interfaces: first milestone

The local-interface engine now performs checked variable elimination, retains
its dependency DAG, shares semantic relation payloads, and accepts persistent
add/replace/remove snapshots. Native checks establish the original-constraint
partition, every table/projection, and the final query context. This includes
negative reuse after extension and rejection after removal of an assumption.
Lean proves the exact bucket-elimination rule and unaffected-factor invariance.
Snapshot maps are persistent AVL trees; all previous roots and results remain.

New relations select constant, dense bitmap, sparse, or reduced ordered decision
DAG encodings by actual serialized size. Immutable object storage uses raw or
zlib bytes, whichever is smaller. Existing schemas and old zlib objects remain
readable. General incremental clause proof integration, lazy row acquisition,
expanded cost proofs, the benchmark and manuscript reconciliation are the next
parts of the same requested five-step implementation.


## Five-step implementation: proof and lazy-acquisition milestone

1. Local bucket elimination handles nonempty interfaces and preserves the old
   order when it fits the width cap. Width failure uses checked complete solving.
2. Persistent manifests and factor dependencies preserve every previous state.
   Deltas parse supplied constraints; row and factor caches reuse unchanged
   dependencies. Planning and final checks can still scan the active graph.
3. Lazy rows are now operational, not just an encoding. Unknown rows cannot
   refute a query. Native row recomputation checks acquired/replayed proposals.
   `--incremental-proofs` additionally archives assumption-aware proof dependencies
   and checks negative live traces using Lean LRAT. Supported UNSAT queries no
   longer require a fresh CDCL solve. Unsupported/invalid traces use fallback.
4. Complete relations share behavior independently of syntax/evidence. Exact
   constant/bitmap/sparse/BDD encoding chooses the smallest serialized payload;
   raw-or-zlib storage never expands individual new object payloads. Partial
   rows, evidence and historical versions still consume additional archive space.
5. `InterfaceCosts.lean` connects local evaluation and projection to explicit
   operation bounds. All elapsed phases, acquisition/replay counters and storage
   remain charged. A whole-machine/CDCL/SQLite cost theorem remains open.

The complete Lean build audits 1,554 declarations / 837 theorem declarations.
All 92 integration tests pass, including poisoned partial rows, forged proof
hints, changed assumptions, restart replay and negative certificates checked
without permitting a fresh standalone solve. Benchmarking and manuscript
reconciliation complete this same five-step follow-up in the next commit.


The five-step follow-up is now implemented and documented in the manuscript.
The new study has 108 runs and 792/792 correct answers, including 198 negatives.
Both proof-enabled modes certify all their negatives through incremental LRAT.
Interface delta reuse reduces local acquisition and transport but often loses
on total time; the archive also remains larger. The paper attributes bucket
elimination, persistent structures, BDDs and incremental proof checking to prior
work, and adds published representation-specific lower bounds.

Remaining research limits are unrestricted width and representation size,
affected-dependency bounds under arbitrary edits, proof/restart cost, bounded
whole-archive memory, and a full machine-cost theorem. These are stronger than
the completed implementation tasks. No polynomial-time SAT claim follows.

Final compatibility review adds tests for semantic payload sharing with separate
provenance, Lean-only fallback, and component certificates combined with the new
proof option. All 95 tests pass. The compatibility fixes affect combinations
outside the timed modes (except a backend dispatch guard on width fallback);
the native binary and its Lean audit are unchanged.

## Scaling follow-up: indexed planning and direct symbolic proposals

The planner now maintains incidence counts instead of rebuilding adjacency at
every elimination step. Persistent plans route changed sources through affected
buckets in a retained order and stop propagation at identical output identities.
The counters separate affected buckets, reused buckets, source comparisons and
snapshot copying. Width failure rebuilds an order or uses checked fallback.
Copying/serializing plans, collecting active constraints and checking final
answers remain global operations; this is not an O(delta) whole-query bound.

The opt-in `--symbolic` path constructs reduced ordered decision diagrams from
formula syntax and performs conjunction, restriction and existential projection
directly. It archives symbolic proposals and enforces node/work caps. Native
factor-row and original-answer checks remain authoritative, including after
restart. This avoids Python truth-table acquisition, but native verification,
small-scope row-cache capacity and worst-case diagram growth are still charged.
Twenty-eight interface/scaling tests pass at this milestone, including exhaustive
small-formula comparisons, random edits, archived branching, poisoned symbolic
proposals, caps and an 80-variable parity diagram built without table rows.

The next milestone adds live incremental-LRAT checking against the existing
native graph, plus session-verified negative cores. A selected archived core is
rechecked once after restart; subsequent conjunct extensions reuse the checked
native fact. Removing a required conjunct fails the transfer check. General
per-clause verification reuse and zero-cost restart are not established.

`--max-archive-bytes` limits logical SQLite pages and refuses further acquisition
at capacity, preserving all committed history. WAL/temporary files and total
process memory are separately reported, not claimed bounded by that option.
`--adaptive` selects between checked and interface solving from prior measured
complete-query durations, persists observations, and charges selection/update
work. This is an empirical policy, not a universal speedup guarantee.

`Scaling.lean` checks symbolic restriction/conjunction/projection semantics on a
reference tree, conjunct-refutation transfer, a depth/fanout affected-node
envelope, conditional polynomial update costs, cumulative work/archive bounds,
and the fixed-capacity obstruction for positive archive increments. The common
polynomial bounds on affected work, representation capacity, per-row work and
all overhead remain explicit hypotheses. The full audit now checks 1,650
declarations / 879 theorem declarations. The ROBDD optimizer and native protocol
state are still outside an end-to-end kernel theorem.


The follow-up benchmark has 147 sequential runs and 1,470/1,470 correct answers
(672 UNSAT), including larger chains, distant edits, 11 public SATLIB instances
and distribution shifts. An endpoint edit recomputes one of 33 buckets; a bridge
can affect them all. Direct symbolic proposals improve the distant-edit stream
from 566.34 ms to 377.54 ms, while checked solving takes 283.35 ms. All public
instances exceed the interface width cap and use checked fallback. Adaptive
selection reduces wasted interface work but does not beat checked solving here.
Every mode has the same 8 MiB logical-page cap; no run reaches it. Total RAM and
WAL storage are not bounded by that cap. Full results, peak allocations, archive
costs, source hashes and uncertainty limits are retained in the scaling study.

Remaining obligations: avoid global plan/source copying and final scans; bound
or predict affected regions under edits; improve symbolic intermediate size and
variable order with charged matching; reuse general verified proof fragments;
prove native protocol/optimizer refinement and full machine costs; bound total
process-tree memory; evaluate modern application suites and stronger routing.
The uniform polynomial coverage/acquisition/representation/verification bounds
for all SAT instances remain unproved. No unrestricted lower bound is claimed.


Final verification: 106 tests pass; all 27 earlier manuscript proof texts are
unchanged, and the conditional scaling proposition adds one proof. The rebuilt
45-page PDF has no overfull boxes or unresolved references and was visually
reviewed. A new backup preserves the live archive; all 2,485 old results, 645
proofs and other older rows remain unchanged, along with 44 previous experiment
files. There are now 2,840 results and 774 proofs, including 355 revalidated
current-engine inputs independently audited. Validation/source hashes and row
fingerprints are recorded with the scaling study.


## Six-task follow-up: durable reuse and concrete restricted updates

All six implementation tasks have now been addressed. The following table keeps
the completed work separate from stronger unproved guarantees.

| Task | Implemented and checked | Remaining boundary |
| --- | --- | --- |
| 1. Overhead | One durable transaction per interface operation; native batches; persistent AVL bucket maps; write-free width preflight. | Source/order scans, full context checks and SQLite costs remain. No O(delta) whole-query claim. |
| 2. Balanced expansion | Explicit persistent binary-relation chain API, eager four-entry summaries, checked joins, logarithmic replacement ledger, preserved roots. | Recognition of arbitrary SAT, general graph edits and full witnesses are outside the bound. |
| 3. Symbolic work | Fused conjunction/abstraction, safe-point GC with root remapping, explicit variable-order metadata and experiments. | No general intermediate-size or efficient-order guarantee; exponential cases remain. |
| 4. Proof fragments | Native per-fragment hinted RUP checks, permanent-premise dependencies, final current-root check, checked restart replay; Lean soundness. | Full certificates still traversed/serialized; protocol/adapter refinement and unrestricted proof-size bounds remain. |
| 5. Routing/resources | Structural features, early screening, reserved fallback budgets, process-tree RSS and full scratch sampling. | No universal route gain/regret bound or hard total RAM/WAL cap. |
| 6. Proof/evidence | 114 tests; 1,828-declaration/941-theorem audit; fixed held-out counter and selected 2026 artifact inputs; manuscript and literature reconciliation. | Small selected suites, no competitive modern-solver benchmark, no full machine-cost proof or unrestricted polynomial SAT result. |

The study records 2,259 correct answers (1,188 UNSAT) and 30 archive-cap errors
from 2,289 attempts across 210 runs. All errors occur at the last two selected
towers increments in five full-input modes. Delta modes complete all twelve;
no wrong answers or timeouts occur. Incomplete stream totals include failures
and must not be used as full-solution times. Sampled RSS reaches 329.14 MiB,
with missed reads and finite sampling intervals explicitly retained.

The separate chain study confirms ten compositions and eleven node writes for
one replacement in a 1,024-edge chain; complete witness checking visits all
1,024 edges. The construction is an established finite-monoid dynamic word
problem (Frandsen et al. 1997; Amarilli et al. 2021), not a novel complexity bound.
The manuscript also cites CUDD relational products and Schreiber et al. 2026
for distributed incremental proof checking. Standard reuse principles are not
presented as new results.

The live archive retains all 3,195 previous results, 903 proofs, and other old
rows. New revalidation/audit adds 355 answers and 129 proofs, for 3,550 total
results and 1,032 proofs. All 63 historical experiment files are unchanged.
The reports are in `experiments/results/followup/`; previous studies stay intact.

## Current work on gaps 1, 3, 4, 6, and 7

The numbering below is the gap list selected for this task; earlier milestone
numbering above is retained as history.

| Gap | Completed change | Remaining limit |
| --- | --- | --- |
| 1. Beyond Boolean chains | Supplied bounded Boolean layers, checked finite-state joins, exact summaries, preserved old leaves and roots, explicit width-dependent replacement ledger. | No arbitrary-graph decomposition or unrestricted SAT width/acquisition bound; table size is exponential in layer width. |
| 3. Global planning metadata | Persistent source reference counts, rank/order, constants and bucket indexes; local named deltas avoid whole-source comparison and plan copying. | Full active-context validation, full witnesses and certificates remain global; an edit may propagate across all buckets. |
| 4. Compression and active memory | Payload-bounded proposal caches, symbolic root trimming/node caps, charged safe-point WAL checkpoint attempts; all archived evidence retained. | Serialized payload is not heap/RSS. Transient objects, native memory and blocked WAL checkpoints prevent a hard total bound; archive growth remains. |
| 6. Failure-aware routing | Recent completed-answer cost with a query-budget penalty per failure; failed-only routes cannot win by being fast. | Periodic exploration still retries; no universal speedup or regret theorem under arbitrary shifts. |
| 7. Broader comparable evidence | Frozen full-formula inputs across modes, enabled online learning, separate delta/layer evidence, new artifact families and sampled watchdog thresholds. | Small application prefixes, selected SATLIB examples and a toy prediction family remain limited evidence; sampled thresholds are not hard memory limits. |

The native audit exposed a concrete refinement pitfall: Lean arity expansion
could delay a function-valued `freeze` until lookup. The earlier mathematical
summary and replacement proofs remained sound, but the compiled representation
could repeat acquisition. Both chain and layered joins now materialize data
before creating lookup closures. Generated C confirms that ordering. This is
implementation evidence, not a formal compiler or complete runtime-cost proof.
The development timeout is retained with the new study. All 119 tests pass on
the corrected build; the transitive Lean audit checks 1,957 declarations and
991 theorem declarations without admits or new axioms.

A relevant published extension is Amarilli, Barloy, Jachiet and Paperman (MFCS
2025), *Dynamic Membership for Regular Tree Languages*,
[DOI 10.4230/LIPIcs.MFCS.2025.8](https://doi.org/10.4230/LIPIcs.MFCS.2025.8).
It establishes an O(log n / log log n) relabeling-update bound for a fixed regular
tree language. The fixed language, tree representation and permitted edits
matter. Implementing that richer interface is a possible next restricted step;
it does not remove unrestricted SAT's missing structural hypotheses.

## Post-implementation gap analysis

This analysis reviews commit `ee3ba62` and adds deterministic diagnostics in
`experiments/results/gap-analysis/`. It does not change the solver or reinterpret
an operation counter as total execution cost. The seven identifiers below keep
1/3/4/6/7 aligned with the preceding selected tasks; 2 and 5 name the remaining
cost and certification obligations.

Three concrete mechanisms now deserve priority over adding another instance
family. First, semantic equality does not stop general-plan propagation. Second,
the native layered-cache policy can repeatedly discard the entire useful working
set. Third, a late query failure can create both a successful and a failed route
observation for the same request. These are distinct from the open uniform
complexity question.

| Gap | Current evidence and remaining obligation | Concrete completion criterion |
| --- | --- | --- |
| 1. Uniform structural coverage | The layered family is supplied to the solver. At Boolean width b, summaries use 2^(2b) cells and the abstract composition budget is 2^(3b). No general-CNF recognizer/compiler or bound on width across arbitrary edits is proved. | Define a broader promised family, check its decomposition, and charge recognition, compilation, expansion count and updates. Logarithmic width in input length could support a polynomial restricted bound; that width guarantee must be proved, not assumed for arbitrary SAT. |
| 2. Executable cost refinement | `replacementWork` charges q^3 by definition and proves the resulting recurrence. This does not prove that native calls, table allocation, bit arithmetic, hashing, persistence and replay obey that ledger. The previous materialization defect illustrates the distinction. | Prove bounds for a costed executable composition and tree update, connect them to the supplied representation, then add explicit service/replay terms. Keep compiled-runtime costs separate until justified. |
| 3. Semantic reuse and global work | Version-three metadata avoids whole-plan copies. However, propagation compares output evidence identities. Equal projected truth tables with different parent identities can invalidate every bucket. Full context traversal, full witnesses and certificate extraction remain global; lazy recursion falls back at depth 256. | Separate semantic relation identity from current provenance, certify equality before stopping value propagation, preserve assumption/deletion checks, and use iterative evaluation. For a decision-only interface, establish an explicit bound on context updates as well as summary updates. |
| 4. Active retention and archive costs | Small Python payload caches preserve historical evidence, but native retention has a separate reset policy. A 256-edge width-four working set exceeds its reset threshold and replays all 511 nodes on every query. Fixed active limits still do not bound RSS, transient allocations, WAL or the growing archive. | Manage the live native working set explicitly, reuse unchanged verified root answers, and report what happens when the working set exceeds budget. Charge replay/eviction amortization. Preserve durable history in a separately budgeted archive; define refusal or storage expansion at capacity. |
| 5. Request-to-proof connection | `Tree.Valid` and summary exactness are proved. The layered protocol does not yet have a complete theorem connecting JSON masks, logical length, identity padding, endpoint restrictions, witness extraction and persistent updates to the user's source formula. General proof sizes and restart costs are unbounded here. | Prove protocol invariants, mask conversions, witness soundness/completeness and source-compilation correctness. Extend negative-proof context checks through edits and replay; do not assume polynomial UNSAT certificates for unrestricted instances. |
| 6. End-to-end arbitration | The route selector chooses only checked versus interfaces. It does not gate predictor/portfolio attempts. Portfolio `native_prepare` takes a median 10,806.82 ms on the chronological stream versus 52.23 ms for checked mode. A post-solve accounting failure also produces two contradictory observations for one request. | Record one final outcome per request; distinguish attempted path and fallback. Add proposal-specific measurements and budgets with reserved fallback capacity, then route among relevant mechanisms using complete measured cost. Test late failures and workload shifts. |
| 7. Evidence and attribution | The main study is reproducible and preserves failures, but application inputs are tiny all-UNSAT prefixes. Public examples were previously used during development. Prediction gains are on signed units, with no accepted prediction on the public shift. Repeated-relation layers mask native working-set pressure. | Freeze genuinely unused, larger mixed-label application streams; include distinct-relation and adversarial edits, cold/warm/restart modes, matched incremental baselines and a cheap deterministic signed-unit heuristic. Use enforced total-resource limits if claiming them. |

### Reproduced semantic-propagation gap

A 16-edge XOR chain is satisfiable. Replacing its first XOR by equality leaves
the first eliminated relation over variable 1 equal to `[true, true]`. The
projected scope and complete values are identical before and after the edit.
The evidence identity changes, because it records different parents. The current
planner therefore recomputes all 17 buckets: zero reused buckets and zero
propagation stops. No incorrect SAT answer occurs.

This exposes the difference between sharing a compressed relation payload and
using semantic equality to stop value propagation. A repair must retain new
provenance even when the value is unchanged. Reusing an old proof after deleting
one of its assumptions would be unsound. Full witness output may also need to
change even when the root decision is unchanged.

Evidence: `semantic.json`; implementation: `solver/planning.py` (`output !=
old_output`), `solver/interfaces.py` (`project_node` and `run`).

### Reproduced native replay gap

Use 256 distinct random relations with a planted zero-state path. At width three,
the first query registers 511 native nodes, a replacement registers nine, and an
unchanged query registers zero. At width four, the reset threshold is 187 nodes.
The first query registers 511 nodes, already exceeding that threshold. Both the
replacement and the unchanged next query reset and register all 511 again.
The unchanged query reports zero Python compositions but 511 native definitions.

This is a performance and accounting gap, not a refutation of the abstract
logarithmic tree-replacement theorem. It also shows that the reset threshold is
not a hard occupancy bound: the pending batch can exceed it. Raising the number
alone does not resolve the general working-set/memory tradeoff. An unchanged
verified root can be memoized; larger edits need an explicit retention/replay
policy with stated memory assumptions.

Evidence: `replay.json`; implementation: `solver/layered.py`, lines 97–117.

### Reproduced routing-observation gap

Inject a failure in `archive_usage` after solving one satisfiable query. The API
raises an error, but `route_observations` contains success=1 and success=0 for the
same attempted route. `solve` records success before storage accounting, then
its exception handler records failure. This is a fault-injection result, not a
failure observed in the timed study. The accepted solver result can remain
correctly persisted while the service request fails; those outcomes need
separate meanings rather than two indistinguishable request observations.

Evidence: `routing.json`; implementation: `solver/persistent.py`, lines 466–481.
The existing score regression tests inject route observations directly and do
not cover this late-failure path.

### Priority and interpretation

The fastest useful sequence is: repair final-outcome recording; stop native
reset/replay on unchanged working sets; separate semantic value propagation from
provenance maintenance; then remove recursive depth limitations and bound full
context checks. Validate each against these diagnostics before enlarging the
benchmark. Exact-count claims should include native replay, not only Python
composition counters.

For the paper, the main theoretical gap remains uniform resource control.
Inductive exactness at each finite stage does not establish polynomial
construction, representation, verification or cumulative expansion cost. The
current results support a perspective on accounting for reusable reasoning and
restricted verified constructions. They do not establish a new general SAT
complexity result or a universal System 1/System 2 speedup.
