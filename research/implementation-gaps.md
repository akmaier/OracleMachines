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

## Seven-priority implementation follow-up

The follow-up preserves the preceding diagnostics as historical evidence.
Implementation commits `d3321a7`, `580e1b1`, and `b080a39` address the practical
priorities before broadening the experiment. None closes the unrestricted
uniform-complexity question.

| Gap | Implemented progress | Remaining obligation |
| --- | --- | --- |
| 1. Structural coverage | Native CNF compilation checks a supplied disjoint ordered partition, width 1–4, with each clause confined to adjacent blocks. A second pass binds source edges and identity padding to the checked root. | Discover useful partitions; cover broader decompositions and edits; prove width/coverage/acquisition bounds for the promised family. No arbitrary-SAT width guarantee follows. |
| 2. Executable cost | A costed executable composition and replacement reference returns counts and the same values as production operations. Lean proves at most `q^3` middle-state tests per join and `h+1+h*q^3` tests plus node events per replacement. | Refine allocation, bit arithmetic, compiler execution, hashing, IPC, persistence and replay costs. This is not a whole-service machine-cost proof. |
| 3. Semantic reuse | Complete native equality checking and checked parent matching let downstream factors reuse row values while retaining new provenance. Iterative Python evaluation removes the depth-256 limit. | Evidence IDs still propagate; final context checks, witnesses and certificates can remain global. Prove the equivalence/row-cache state invariants and reduce context work without invalid assumption reuse. Symbolic and native capacity limits remain. |
| 4. Retention | Native layered retention keeps a complete live dependency closure, reports logical cells, and refuses a working set that exceeds its configured cap. Old versions remain durable. | Bound actual RSS/transient allocation and physical storage, rather than selected cells/pages; charge history replay and unbounded archive growth. |
| 5. Request/proof connection | Lean proves exact rowwise relation comparison, accepted full-tree witness traces/lengths, prefix/suffix composition, identity-padding preservation, local CNF clause semantics and mathematical source binding. Runtime checks reject forged shortened lengths and source/root mismatches. | Complete the refinement through JSON, partition construction, hash maps, Python, SQLite, truncated witnesses and restart state. General UNSAT proof-size bounds are not supplied. |
| 6. Arbitration | Final outcomes are logged at most once. Proposals have separate calls, outcomes and elapsed measurements, with at most 250 ms/10% reserved for all attempts before fallback. | Learn cost-sensitive gates among prediction, portfolio and solving; bound feature/model/replay overhead and failures. Budget reservation alone gives neither optimal routing nor a universal speedup. |
| 7. Evidence | A frozen study uses previously unused mixed-label circuit instances, later application horizons, a deterministic polarity baseline, matched live/restarted proof modes, distinct width-four relations, semantic edits/deletions and source compilation. All failures are retained. | Broader representative workloads, more repetitions, current competing solvers, hard comparable total-resource limits and independent replication. |

The semantic diagnostic now establishes one equality and rebinds 16 successor
projections after replacing the first XOR by equality in a 16-edge chain. It
performs two combination-row acquisitions while still updating all 17 evidence
buckets. This is a reduction in value computation, not a constant-time complete
update. Tests include adding a contradiction, deleting a necessary assumption,
branching from the old version and restart.

With 256 distinct width-four relations, initial registration needs 511 native
nodes, replacement nine, and an unchanged query zero. At a cap exactly equal to
the live set, nine obsolete native entries are evicted on replacement; the new
root fits without replaying all 511. A smaller cap refuses the request, while the
saved roots remain queryable after reopening with sufficient capacity.

The full-tree witness and source-binding theorems concern explicit mathematical
objects. Their presence does not certify every executable protocol branch. The
current audit includes 2,090 declarations and 1,047 theorem declarations, with
no admits or added axioms. The distinction between these proved components and
the remaining implementation refinement is part of the result.

## Gap analysis after the seven-priority follow-up

This 8 November 2026 analysis reviews runtime commit `269f095`. The final-outcome
logging defect, reset thrashing on unchanged layered roots, and Python's
depth-256 lazy-evaluation limit have targeted repairs and passing regressions.
They should not be listed as unchanged open defects. Remaining practical gaps
concern work outside relation evaluation, source coverage and proof refinement.

The new [diagnostic audit](../experiments/results/priority-gap-audit/README.md)
records temporary-store experiments and SQL deltas. The original priority study
revalidates: 1,047 correct completions, 105 resource failures and no wrong answers
among 1,152 attempts. The ten priority regressions pass again. These checks are
neither a complete correctness proof nor an independent replication.

### Semantic reuse works, but provenance updates remain global (gap 3)

The 16/64/320-edge equal-projection edits acquire only five native rows and two
combination rows. Nevertheless, they rebind 16/64/320 successor projections and
change 17/65/321 buckets. Existing three-repeat median edit times are
8.811/33.920/240.298 ms. The operation counts, rather than these few timing points,
identify the remaining global work.

The new audit finds **zero new `interface_relation` objects** in all three edits.
At 320 edges it nevertheless inserts 3,430 knowledge objects with 550,879
compressed payload bytes and grows logical database allocation by 1,556,480
bytes. Most objects are persistent-map nodes, interface evidence and elimination
buckets. Another 639 row-cache records store checked values under new evidence
identities. The intermediate counter reports 3,429 objects because the final
result is inserted after it is sampled.

Behavior already shares well here. The remaining question is whether evidence
can be maintained locally. New parent identities still flow through the suffix
(`solver/interfaces.py:398`, `solver/planning.py`). Each native rebind enumerates
all interface assignments, even if few rows are known
(`formal/OracleMachines/InterfaceProtocol.lean:250`). General expansion also
enumerates the manifest, reconstructs SAT witnesses and extracts full negative
proof DAGs. The native negative-context check uses list membership for every
reachable leaf; distinct leaves and active identities can require quadratically
many identity comparisons.

**Next obligation:** maintain shared semantic values separately from versioned
derivations and checked context roots, then update provenance and context by
deltas. Prove that removed assumptions cannot justify a new result. Add a
decision-only general-expansion API and charge full witness/certificate output
separately. Measure new SQL bytes and context visits, not only computed rows.
Simply stopping parent-identity propagation would invalidate provenance.

### Retention scans the live graph under pressure (gap 4)

The repair reduces new native definitions to 9/11 per 256/1,024-edge edit.
At a cap equal to the live closure, however, **each of six consecutive edits
visits all 511/2,047 live nodes**, reading 554/2,100 nodes in total. Doubling the
cap reduces those edits to zero retention visits and 43/53 node reads. Unchanged
queries require no closure scan at either cap.

`solver/layered.py:110` builds the live set, sorts retained IDs and sends them
all to native code. `LayeredProtocol.retain` rebuilds a map and checks dependency
closure. Logarithmic summary recomputation is therefore not a logarithmic
complete update at the tight cap. Headroom postpones this work; six edits do not
establish long-stream amortization. Historical branch selection and restart have
separate replay costs. General factor retention still resets its whole worker
at a separate threshold (`solver/interfaces.py:495`).

**Next obligation:** maintain live reachability incrementally for specified
active roots, or prove a batch-retention amortized bound with explicit headroom
and branch-switch assumptions. Test many eviction cycles and report total
visits, transport and native work. Retain durable history with an explicit
archive-capacity policy. Logical cells/pages do not bound actual RSS, transient
allocation or physical disk.

### Source-bound incremental CNF updates are missing (gap 1)

The compiler checks a supplied disjoint ordered partition with blocks of at most
four variables and clauses confined to neighboring blocks. It neither discovers
the partition nor covers general bounded-width decompositions. For example,
clauses `(x OR y_i)` with more than eleven distinct neighbors of `x` cannot fit
this width-four partition: every neighbor must fit in `x`'s block or its two
adjacent blocks. These formulas are easy to satisfy by setting `x` true. The
restriction therefore excludes some very simple families.

More immediately, `layered_cnf` requires a **fresh full source request**.
It compiles twice and compares every source edge against the checked tree.
Generic `layered` edits can reuse its state, but their new answers concern
edited relations and have no new binding to an edited original CNF. The source
API has no end-to-end logarithmic update guarantee.

**Next obligation:** introduce persistent checked source versions, clause-to-block
indexes and validated local source deltas. Preserve source identity through
replacement, deletion and restart. Prove this precise family before extending
to overlapping path/tree decompositions. Charge initial decomposition and
compilation. An unrestricted-SAT width or compactness guarantee remains a
research premise, not an implementation detail.

### Proved components do not yet prove the stateful service (gap 5)

The Lean results establish local clause semantics, mathematical source binding,
full-tree witness traces, and value equality of costed and production tree
operations. They do not establish the complete executable pipeline.

The most consequential next invariant concerns native factor equivalence classes
and transferred rows. `factorEquate` and `factor_rebind` maintain mutable hash-map
state; semantic lemmas justify the intended operations, but no theorem preserves
their store invariant through every protocol transition. JSON/partition
construction, native memo state, truncated witnesses, SQLite/Python recovery and
restart remain obligations. An axiom audit establishes proof hygiene, not that
every runtime branch satisfies its specification. These diagnostics found no
wrong answer.

**Next obligation:** prove that every stored row equals evaluation of its current
immutable definition and that every equivalence class denotes one relation on
its named scope. Prove preservation under define, acquire, equate, rebind and
reset; compose this with source/context binding and restart. State the remaining
trusted runtime boundary. General short UNSAT certificates are not assumed;
a proof-size refusal is not an UNSAT verdict.

### The complete cost ledger remains unproved (gap 2)

`LayeredCosts.lean` proves at most `q^3` tested middle states per join and
`h+1+h*q^3` tests/node events per reference replacement. It excludes allocation,
bit arithmetic, masks, hash maps, JSON, Python/SQL work, retention, source binding
and replay. The diagnostics show that these exclusions can dominate. Equality
also costs work to discover; `factorClass` has neither path compression nor
union by rank, and its cost is absent from the row-acquisition count.

**Next obligation:** implement a ledger for these terms and prove a restricted
service bound with explicit resident-state, output and restart conditions.
Measure actual new payload bytes separately from bytes serialized:
`relation_payload_bytes` increases even when SQL deduplicates every relation.
Functional equivalence of counted and production operations alone supplies no
native instruction or bit-machine bound.

### Budgeted speculation is not cost-sensitive selection (gap 6)

At-most-once final observations and the shared proposal deadline are implemented.
The limit is 250 ms or 10% of time remaining **when proposals start**, whichever
is smaller. Retrieval and feature/model work happen beforehand; training and
archive work happen afterward. A proposal timeout kills the native worker and
can incur later replay. These costs are measured in elapsed time but are not
bounded by the proposal budget. The router chooses checked versus interfaces,
not which predictor/portfolio actions are worthwhile.

The manuscript's fixed-policy break-even proposition does not directly prove
performance of this adaptive service. It excludes online updates and requires
the same baseline on fallback. An adaptive guarantee must charge updates and
interference as well as benefits from accepted answers.

**Next obligation:** gate mechanisms by avoided solver cost versus all incremental
costs, including worker-state loss. Keep an always-checked option and test workload
shifts. Regret or overhead guarantees need explicit workload/resource assumptions;
a timeout alone proves no universal speedup.

### Application evidence is insufficient for an efficiency claim (gap 7)

Chronological median times are 649.47 ms learned, 458.58 ms checked and 263.01 ms
for the deterministic polarity baseline. The learner accepts 30/32 signed units
per repetition; polarity accepts all 32. Neither accepts a public-shift or
application proposal. This supports a synthetic heuristic benefit, not a
learning-specific gain on those public applications.

Every service mode completes 9/24 application attempts, on different subsets.
Full-stream times include failures and cannot rank equivalent completed work.
Direct CNF completes 24/24 with a different certification/storage boundary.
All process-tree RSS reads failed, leaving no valid RSS peak measurement.

Representation is a concrete bottleneck: the saved Towers-38 CNF has 517,974 bytes,
while unary formula encoding needs 181,707,058 bytes, roughly 351 times as much.
Every service mode rejects it at the 8 MiB input cap. Full-study failures comprise
21 input-cap, 39 archive-cap, 30 proof-size and 15 deadline failures. These are
resource failures, not SAT/UNSAT decisions or complexity lower bounds.

**Next obligation:** verify a compact source interface, then compare matched
certified baselines on the same completed inputs. Report completion rates,
paired costs, storage growth and functioning RSS observation. Freeze a new
holdout after choosing the policy; add repetitions and realistic edit, restart
and branch streams. Universal System 1/System 2 superiority is not established.

### The theoretical premise and recommended order

Exact finite-domain expansion does not imply uniform polynomial construction.
A cost bound in the number of stored components does not bound how many
components or expansions cover every length-n SAT instance. The missing invariant
must jointly control width, acquisition, representation size, coverage schedule,
maintenance and evaluation. The manuscript states these conditions; it does not
prove them for unrestricted SAT. This audit supplies neither that proof nor a
counterexample to the conditional mathematics.

The practical order is **3, 4, 1, 5, 2, 6, 7**: reduce provenance and retention
work, connect local edits to source CNF, prove the new state transitions, complete
the restricted cost account, improve selection, then test the resulting claim.
Maintain regression checks throughout. Compact general input encoding is an
independent prerequisite for meaningful application evaluation and can precede
the final experiment.

A concrete next theorem should cover decision-only local CNF edits in a supplied
fixed-width decomposition: preserve checked source identity and current-context
validity, include retention and evidence in the full-update bound, and give
explicit additional terms for restart, history selection and full output. This
would strengthen the resource-accounting contribution without assuming a solution
to P versus NP.

## Source-update implementation after the audit

Commits `57a6d23` and `07354c8` address the concrete restricted target. The
general seven-item audit above remains the record of the starting point.

- **Retention:** live references and native incoming-reference counts now
  support incremental eviction. In the 256-edge tight-cap regression, 128
  consecutive edits each need nine evictions and at most 34 live-reference
  updates, without a 511-node closure scan. Old versions remain archived.
- **Provenance and source binding:** `source_cnf` stores current clauses in the
  same balanced tree as their relations. Warm bucket replacements change only
  the source path; the native checker verifies the requested edit and unchanged
  subtree identities. Empty replacement buckets delete clauses. Partition changes
  still require initial compilation of a new family.
- **Formal connection:** native `CheckedSource` nodes contain proofs aligning
  cached trees with the current local CNF. The executed decision has exact
  positive/negative theorems. Source edits preserve all unselected leaves, and
  the counted executable reference has the bound stated in `SourceInvariant.lean`.
- **Accounting:** source metrics distinguish transport bytes, serialization,
  newly inserted raw/packed payloads, node reads, patch/binding visits, reference
  work, final logical cells and transient reservation. Complete elapsed phases
  are measured. Archive and actual-memory costs are not inferred from cell counts.
- **Evidence:** all 141 tests pass; Lean audits 2,279 declarations and 1,106
  theorem declarations. The [matched source study](../experiments/results/source-updates/README.md)
  compares local updates with full rebuilding under the same source checker.

This addresses gaps 1/3/4 on the supplied adjacent-block family and strengthens
gaps 2/5. It does not optimize the general factor-DAG provenance suffix or prove
its mutable row/equivalence invariants. Complete JSON/global-mapping/storage
refinement, machine costs, archive-growth policy, cost-sensitive gating and
unrestricted coverage remain open. The new benchmark measures a restricted
structural mechanism, not a learning-specific or general SAT speedup.

## Indexed context and upgrade preservation follow-up

The next review closes three implementation gaps:

- General negative-proof context checks index the active identities once.
  Lean proves exact agreement with the old list-membership condition, including
  duplicates and arbitrary order. Membership probes are bounded by the proof's
  leaf count. The native response and Python ledger expose index-entry and probe
  counts. The graph traversal and context construction remain global, and hashing
  costs are not assumed constant in a worst-case machine bound.
- Source versions from earlier checker namespaces are now replayed under the
  current checker. Their stored verdicts are not trusted. Current-engine rows
  are added only after checked replay; previous rows and objects remain intact.
  A source-ID index supports the older-namespace lookup. Engine upgrades can
  still require full native replay and do not have a warm-update guarantee.
- Database cleanup covers configuration, migration, and later initialization
  failures. Two independent test-owned connection leaks are also fixed. The
  full suite passes 144 tests without resource warnings. Lean audits 2,290
  declarations and 1,113 theorem declarations without admits or added axioms.

The next highest-value obligations are the source compiler's global-ID mapping
proof, reference-count/eviction invariants, and the general factor row/equivalence
store invariant. After those, measure alternative representations for the global
provenance path and remove the unary-input expansion in application experiments.
These tasks can make the stated restricted guarantee more complete. They do not
establish efficient decompositions or compressed exact models for arbitrary SAT.

## Original-variable mapping proof follow-up (8 November)

The next checkpoint closes the local mapping obligation identified above.
`SourceMapping.lean` replaces unchecked position pairs with dependent entries
that prove the original block lookup and width bound. An executable alignment
check proves completeness for every supplied array coordinate. Global valuations
encode into bounded block states, and arbitrary block states yield agreeing
global valuations. These conversions include empty/short blocks and unused IDs.

The native initial compiler now uses proof-carrying clause translation. Its
local-edit compiler returns a `CheckedCNF` indexed by the requested original
clauses. Lean proves evaluation equality and SAT/UNSAT equivalence for each
translated bucket. Iterative accumulation is tied back to the request by array
equality checks. This is actual runtime construction of the proved values.

All 148 tests pass without resource warnings. Lean audits 2,477 declarations and
1,188 theorem declarations without admits or added axioms. Both compiler paths
agree with 9,520 exhaustive boundary assignments across 112 local CNFs. Additional
tests cover sparse IDs above 64 bits, slot permutations, missing/duplicate/zero
IDs, locality violations, empty clauses versus empty buckets, short and empty
blocks, old versions after restart, and long iterative translation inputs.

Resource limits remain explicit: the layout check makes an extra pass over
blocks and variables. Builders accumulate original arrays and compare them with
the input. Initial grouping scans literal positions before translation. These
linear entry visits, temporary arrays, ID hashing/comparison and allocation are
outside the existing relation-evaluation counter. We claim no speedup from this
proof change and preserve the earlier timing study as historical evidence.

Highest-priority remaining work:

1. Compose local translation with the **global grouping loop and source-tree
   binding**. Every original clause must reach exactly its intended edge; native
   node/layout identities must retain the proved meaning through requests and
   edits. The current local theorem does not prove that end-to-end property.
2. Prove the **native incoming-reference and Python live-reference invariants**
   through shared children, replacement, failure, eviction and replay. Current
   pressure/branch/restart tests remain evidence rather than a state theorem.
3. Prove the general factor **row/equivalence-store invariant**. The restricted
   adjacent-block compiler does not settle the general factor-DAG obligations.
4. Add mapping, checking, retention, serialization and archive access to an
   explicit restricted ledger; distinguish entry visits from bit-machine costs.
5. Replace unary general input encoding before broader application evaluation;
   retain failures and compare matched certified boundaries. Cost-sensitive
   routing, hard total-memory bounds and unrestricted coverage remain open.

Runtime checkpoint `dd0c44c` is committed and pushed. The manuscript and the
[verification record](../experiments/results/source-mapping/README.md) include
archive revalidation: all 355 distinct generic inputs pass; five older source
versions are checked under the new engine and after restart. Every old row in
all 21 tables and all 142 prior experiment files is preserved. The archive now
contains 5,325 generic results and 1,677 refutations. Historical timing results
remain tied to their original runtime; this checkpoint has no new timing study.

## Complete source grouping and path semantics (8 November)

`SourceGrouping.lean` closes the global flat-CNF grouping part of the preceding
priority. `GroupedCNF` contains both original and translated buckets, fixed edge
counts, a permutation proof preserving every original clause occurrence, and
the per-edge evaluation equalities. The actual grouping loop uses the proved
append operation and checks its accumulated input against the supplied CNF.
Repeated clauses and empty clauses cannot disappear from the proved partition.

The whole original CNF is satisfiable exactly when **one consistent sequence**
of bounded block states satisfies every compiled relation. Local nonemptiness
alone is insufficient. New path/sequence lemmas connect that sequence to the
composed relation. `CompiledSource.bound_tree_exact` and `bound_tree_unsat` then
connect the original CNF to a valid tree summary **assuming** exact ordered leaf
binding and identity padding. That assumption is explicit and is not discharged
by calling a theorem about the reference tree alone.

The native compiler now returns the grouped proof indexed by the supplied CNF.
This proves correctness of successful typed compilation, not completeness of
acceptance for every promised input and not refinement of JSON decoding. Warm
edits retain the existing local compiler; no full-source regrouping is added to
that path. Initial grouping adds a temporary array of clause references and a
final equality check, outside the relation-evaluation ledger. Proofs are erased;
runtime comparisons, allocation and arbitrary-size IDs still cost work.

The next highest-priority obligations are now:

1. **Native source-tree binding and identity preservation.** Carry original-source
   meaning, layout, start and span through stored nodes and joins. Prove that
   initial binding, patches and replay supply the leaf-binding premise above.
   The current runtime checks these facts, but has no complete state theorem.
2. **Reference-count/eviction invariants** across shared children, failures,
   historical branches and replay, in both native and Python stores.
3. **General row/equivalence-store refinement**, including source/context binding;
   the adjacent-block result does not establish general factor-DAG invariants.
4. **Complete restricted accounting**, including grouping/equality passes,
   retention, transport and archive access, with bit costs distinguished from
   entry counts. Acceptance completeness and cap behavior also need specification.
5. **Compact general input and matched application evidence**, followed by
   cost-sensitive selection. Hard total-resource and unrestricted-coverage
   guarantees remain open. This proof checkpoint makes no timing claim.

Validation: all 152 tests pass without resource warnings; Lean audits 2,562
declarations and 1,233 theorem declarations without admits or added axioms.
The new checks cover all 11,680 complete assignments of 60 generated global CNFs,
exact bucket contents and occurrence counts, and service decisions/witnesses.
They include individually nonempty relations with no common path, repeated empty
clauses, final-block units, the 65,537-block cap and 12,000 repeated clauses.
Runtime checkpoint `75483cd` is committed and pushed. The manuscript and the
[grouping verification record](../experiments/results/source-grouping/README.md)
include archive revalidation: all 355 distinct generic inputs pass semantic audit;
all five old source versions pass current-engine adoption and restart. Every old
row in all 21 tables and all 150 earlier experiment files is preserved. There
are now 5,680 generic results and 1,806 refutations. Historical timing evidence
remains unchanged and tied to its original runtime.

## Executable complete-source binding (8 November, third hourly follow-up)

`SourceBinding.lean` closes the initial complete-source part of priority 1.
Its executable constructor checks the actual stored tree's width and ordered
leaves, including each identity-padding leaf. On success it returns a
`BoundCompilation` carrying the binding premise, tree validity and exact
comparison-call count. Its positive and negative decision theorems concern the
complete original CNF. Both native full-source queries and initial source-version
binding use this result. Original-clause/provenance checks remain in place.

The accumulator traversal is proved to preserve leaf order; it visits logical
tree occurrences even when native nodes are shared. The tail-recursive scan is
proved to accept exactly equal leaf lists and to make one relation-comparison
call per logical leaf on success. Both Python APIs expose this count, together
with diagnostic row and source-evaluation reference bounds. Initial source-version
binding adds a source-relation evaluation pass. Allocation, original-source
indexing, bit/mask costs, endpoint queries, transport and storage are separate.
No speedup, RSS bound or complete native cost theorem is claimed. Warm edits and
current-source queries do not repeat the full scan.

All 156 tests pass without resource warnings; Lean audits 2,615 declarations and
1,259 theorem declarations without admits or added axioms. The new regressions
cover wrong ordered leaves despite a matching final answer, nonidentity padding
that composes to identity, dimensions, valid witnesses, counters at widths 1, 2
and 4, and 65,536 logical leaves sharing just 17 native nodes.

Remaining priorities:

1. **Preserve original-source identity through native joins, patches and replay.**
   Initial full binding now supplies its premise. Carry layout, start and span
   with original-source nodes and prove that mutable store transitions preserve
   them. The existing local-source invariant and transition tests do not yet
   establish that complete state theorem.
2. **Reference-count/eviction invariants** in native and Python stores, including
   shared children, failure, historical branches and replay.
3. **General factor row/equivalence-store refinement.** The adjacent-block
   proof does not discharge general source/context binding obligations.
4. **Complete restricted accounting:** the new scan counts comparison calls,
   not all relation evaluation, allocation, retention, serialization or bit costs.
   Acceptance completeness and cap behavior also need specification.
5. **Compact general input and matched application evidence**, then cost-sensitive
   selection. Hard total-resource and unrestricted-coverage guarantees remain open.

Runtime checkpoint `bc977eb` is committed and pushed. The manuscript and the
[binding verification record](../experiments/results/source-binding/README.md)
include successful revalidation/semantic audit of all 355 generic inputs and
checked adoption/restart of all five older source versions. Every old row in all
21 tables and all 158 earlier experiment files is preserved. The archive now
contains 6,035 generic results and 1,935 refutations. Historical timing evidence
remains unchanged and tied to its original runtime. The next run should start
with the node/layout/start/span invariant above, without treating this initial
full scan as a proof of later local transitions.

## Original-source nodes and consecutive joins (8 November, fourth hourly follow-up)

`SourceNodes.lean` retains the original clause arrays and their `CheckedCNF`
translations in a tree indexed by layout, width, start and height. Logical leaves
prove their edge is in range; padding leaves prove their edge is outside the
logical source and compile to identity. A join requires equal child heights and
the exact consecutive start. `CheckedNode` aligns this original tree with the
actual cached relation tree. The constructors carry the proof through registration
and joins. Join theorems preserve the complete original clause list and every
occurrence, including duplicate and empty clauses.

The executed node decision now has exact positive/negative theorems for the
original clauses stored in that node. Consistent paths use the indexed global
edge positions. Satisfying valuations extend through identity padding by repeating
the final block state; accepting paths yield agreeing global valuations via the
complete layout map. Clause flattening belongs to the specification and is not
executed by warm decisions or joins.

The native context's model map is typed by its exact layout and width. Registration
uses typed starts and the new constructors; replay rebuilds the same kind of
checked nodes. A context change resets both native maps, and failed batches expose
no partial state. These runtime paths have regression coverage. A formal theorem
relating the two named maps and JSON bodies is still missing.

Resource accounting records newly registered original-source nodes, clause entries
and literal entries. These diagnostics include replay and exclude duplicate
registrations. Original integer arrays now remain reachable from leaves alongside
JSON evidence and local translations. Joins retain child references; they do not
flatten the original source. The extra retention is not free, and entry counts
are not a byte/RSS or whole-runtime cost theorem. Warm unchanged queries report
zero new original-source nodes. No new timing claim is made.

All 159 tests pass without resource warnings, including 20 source-update tests.
Lean audits 2,751 declarations and 1,320 theorem declarations without admits or
added axioms. New cases cover nonconsecutive/reversed children, invalid dimensions
and layouts, failed-batch rollback, duplicate registration, shared-variable
conflicts, source-payload counts, sparse IDs above 64 bits, empty/short blocks,
branching, deletion and restart.

Next priorities:

1. **Named-store and requested-patch refinement.** The typed constructors now
   preserve layout, interval and original-source semantics. Prove correspondence
   between JSON identities, child references, relation-store entries and typed
   model entries. Then prove that `checkPatch` accepts the requested clause
   replacement and preserves every unedited original bucket. Correct semantics
   of the returned node does not alone prove it is the requested successor.
2. **Native/Python reference counts and eviction**, including shared children,
   failures, historical branches and replay.
3. **General factor row/equivalence-store refinement.** The new original-source
   proof remains specific to the supplied adjacent-block representation.
4. **Complete restricted costs and acceptance specification**, including original
   payload retention, mapping, transport, archive access and bit operations.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** Hard total-resource and unrestricted-coverage guarantees remain open.

Runtime checkpoint `b7dfcf4` is committed and pushed. The manuscript and the
[source-node verification record](../experiments/results/source-nodes/README.md)
include successful revalidation and semantic audit of 355 generic inputs and
checked adoption/restart of five saved source versions. Every previous row in
all 21 tables and all 166 earlier experiment files remains intact. The archive
now contains 6,390 generic results and 2,064 refutations. Historical timing data
remains tied to its original runtime. Resume with named-store correspondence and
requested-patch refinement; do not repeat or weaken the now-typed interval proof.

## Paired native maps and source metadata (8 November, fifth hourly follow-up)

`SourceStore.lean` closes the pointwise named-map part of priority 1. The native
context now contains one store carrying a proof that its relation and original
model maps have the same keys. At each key the stored relation tree is exactly
the model's checked tree. `BodyMatches` retains equations from the actual JSON
getters for identity, layout, width, start and height. Logical and padding leaves
also retain exact original-clause arrays, including order and duplicate/empty
entries. This is root metadata and leaf payload correspondence, not a complete
serialized graph theorem.

Initialization, paired insertion and paired erasure construct the invariant.
`lookup_exact` and `missing_exact` recover correspondence or matching absence at
any key. `lookup_semantics` connects a retrieved tree's positive and negative
decisions to satisfiability and unsatisfiability of its model's original clauses.
Native registration and deletion now use these operations. The proof needs no
store scan; parsed/header wrappers retain getter equations as erased proofs.
Temporary runtime wrappers, parsing, comparisons and reference-map operations
still cost work. No new timing, byte/RSS or complete machine-cost bound is claimed.

The generic and source stores share the same increment/decrement loops, including
underflow and referenced-node rejection. Refcount correctness is not assumed by
the map proof, and remains a separate theorem. Failed functional batches expose
no partial new state. New regressions check unknown/duplicate deletion midway
through a batch, child-reference rejection after rollback, parent-before-child
deletion, shared descendants, safe name reuse with different original clauses,
equal relations with distinct provenance, and missing-field rollback.

Remaining priorities:

1. **Named child links and requested-patch refinement.** Relate decoded left/right
   names and serialized masks to the actual typed children and summaries. Prove
   dependency lifetime/identity stability under permitted store changes. Then
   prove that `checkPatch` selects exactly the requested original-clause successor
   and preserves unedited buckets. Root metadata and map agreement alone do not
   prove this. `Store.insert` preserves correspondence even for replacement; the
   current protocol separately rejects changed bodies under a live identity.
2. **Native/Python reference counts and eviction**, including shared children,
   failed batches, historical branches and replay. The new erase proof covers
   paired map correspondence, not safety of dependency reclamation.
3. **General factor row/equivalence-store refinement.** The adjacent-block proof
   does not establish general factor-DAG or Python/SQLite invariants.
4. **Complete restricted costs and acceptance specification**, including decoding,
   header allocation, original payload retention, transport, archive and bit costs.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** Hard total-resource and unrestricted-coverage guarantees remain open.

Validation: all **162 tests pass**, including **23 source-update tests**, without
resource warnings. Lean audits **2,858 declarations / 1,367 theorem declarations**
without admits or added axioms. Runtime checkpoint `9cf68a4` is committed and
pushed. The manuscript and the
[source-store verification record](../experiments/results/source-store/README.md)
include successful revalidation and semantic audit of all 355 generic inputs and
checked adoption/restart of five older source versions. Every previous row in
all 21 tables and all 174 earlier experiment files remains intact. The archive
now contains 6,745 generic results, 2,193 refutations and 35 source-state rows
across checker namespaces. The historical timing study remains unchanged.
Resume with named child links/dependency lifetime and requested-patch refinement;
do not treat this pointwise root invariant as complete serialized-graph refinement.

## Named child registration and summary binding (8 November, sixth hourly follow-up)

`SourceLinks.lean` proves the registration-time portion of named child refinement.
The executed `readJoin` constructor returns a node with `JoinLinks` indexed by the
actual model map used in that call. It retains equations for decoded left/right
names, successful lookup of the exact child models, and equality to their checked
consecutive join. The original-clause theorem attributes every occurrence to
those children, even when distinct sources have equal relations. The decision
theorem requires one valuation satisfying both child sources; independent local
SAT answers do not suffice.

Fresh-key insertion preserves existing `JoinLinks`. Erasing a key preserves a
join when the key is neither decoded child. These are conditional transition
lemmas, not an established lifetime invariant for the full runtime. The latter
still needs to show that zero incoming references implies the erasure premise,
and that every live branch has links valid in the current map. The registration
proof is erased; it does not retain its model-map snapshot or perform a store scan.

`BodyMatches.summary` also binds the decoded mask to the model's actual cached
summary. Unlike the registration-snapshot predicate, this field is already part
of the paired native-store invariant and survives all its constructors. Leaf,
padding and branch registration retain proofs from their existing checks. No new
relation scan is added. Getter wrappers, comparisons and allocation still cost
work; there is no new machine/byte bound or measured speedup claim.

The join helper checks its child shape before the header start/height checks.
Malformed requests with several defects may therefore report a different first
error. Accepted request semantics and all resource caps are unchanged. Tests
exercise original-clause provenance under equal relations, missing/ill-typed
child names, live-identity rebinding rejection, incorrect but satisfiable masks,
and 12 parents removed in shuffled order while retaining their shared children.

Next priorities:

1. **Global named-link lifetime and requested-patch refinement.** Promote
   registration links to an invariant of every live branch. Prove fresh identity
   insertion and immutable duplicate handling; connect zero incoming references
   to the `erase_unreferenced` premise. Then prove that `checkPatch` selects
   exactly the requested successor and preserves unedited original buckets.
2. **Native/Python reference counts and eviction**, including shared children,
   failures, historical branches and replay. Tests are not an arithmetic proof.
3. **General factor row/equivalence-store refinement** and complete serialized
   replay/Python/SQLite correspondence.
4. **Complete restricted costs and acceptance specification**, including runtime
   parsing, allocation, payload retention, transport, archive access and bit costs.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** No unrestricted-SAT coverage or total-resource bound follows.

Validation: all **165 tests pass**, including **26 source-update tests**, without
resource warnings. Lean audits **2,874 declarations / 1,380 theorem declarations**
without admits or added axioms. The previous manuscript proof blocks remain
unchanged. Runtime checkpoint `6a73372` is committed and pushed. The manuscript
and [source-link verification record](../experiments/results/source-links/README.md)
include revalidation and semantic audit of all 355 older generic inputs and
checked adoption/restart of five source versions. Every previous row in all 21
tables and all 182 earlier experiment files remains intact. The archive now holds
7,100 results, 2,322 refutations and 40 source-state rows across checker namespaces.
Earlier timing evidence remains tied to its original runtime. Resume with a
global live-branch link invariant and the reference-count erasure premise; do not
treat registration correctness as completed lifetime or requested-patch refinement.

## Exact incoming counts and live dependency preservation (8 November, seventh hourly follow-up)

`ReferenceCounts.lean` defines each incoming count as the sum of decoded child
occurrences across all live native parents. The finite parent-domain witness and
sum occur only in a proposition and erase. The executed increment fold has an
exact addition theorem; successful decrement returns an exact subtraction
equation and retains underflow rejection. Fresh insertion and zero-count erasure
preserve the aggregate invariant. `Exact.zero_no_child` proves that count zero
excludes the key from every live parent's decoded child list.

`SourceLifetime.lean` wraps the paired store with exact counts and a global
`Linked` invariant: every live branch names its exact current child models.
Insertion uses fresh-key preservation; deletion combines the decoded metadata
with zero-count exclusion to discharge the conditional deletion premise from
`SourceLinks`. `lookup_branch` recovers current child links from a named relation
lookup. The native source context now uses this wrapper. Its registration path
supplies the actual missing-key equation and a leaf-or-checked-join proof.
Duplicate definitions change no state. Source deletion executes the proved
decrement and returns both preserved invariants. A failed batch exposes no new
state. Unreferenced identities can be reused without rebinding a live parent.

The new source operations decode at most two direct children per node. They do
not compute the proof's finite domain or global sum, scan the store, or retain
registration snapshots. Runtime hashing, maps, wrappers, integer/bit operations,
source payloads, transport and archive access remain costs. No new timing,
allocation/RSS or complete machine-cost bound is claimed. The generic relation
store still uses its earlier loops; the Python active-root/reference policy is
also outside this new native-source invariant.

A new regression independently recounts the complete live reference graph of
44 source nodes with 16 roots and shared internal descendants. It compares
deletion acceptance/rejection after randomized operations and duplicate
definitions, queries surviving roots, removes all remaining nodes in dependency
order, rebuilds the same names and reclaims them again. Earlier rollback,
parent-sharing, identity-reuse, branching and restart checks remain in place.

Next priorities:

1. **Exact requested-patch semantics.** Use current `lookup_branch` links to prove
   that successful `checkPatch` compares the actual typed children. Connect leaf
   clause equality to the requested replacement, and identical unedited names
   to unchanged original buckets. The current node's correct SAT semantics does
   not alone prove it is the requested successor. Root coverage, edit validation
   and complete initial binding remain part of this integration obligation.
2. **Python retention and complete serialized replay/SQLite refinement.** Native
   source dependency safety is now proved; this does not prove Python policy,
   archive integrity, outer transport, or the generic relation-store loops.
3. **General factor row/equivalence-store refinement.** Adjacent-block source
   invariants do not establish general factor-DAG guarantees.
4. **Complete restricted costs and acceptance specification**, including complete
   decrement/operation acceptance, caps, parsing, maps, allocation, payloads,
   transport, archive access and bit costs.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** No unrestricted-SAT coverage or total-resource bound follows.

Validation at the lifetime checkpoint: all **166 tests pass**, including **27
source-update tests**, without resource warnings. Lean audits **2,944 declarations /
1,416 theorem declarations** without admits or added axioms. Runtime checkpoint
`3382876` is committed and pushed. The manuscript and
[lifetime verification record](../experiments/results/source-lifetime/README.md)
include revalidation and semantic audit of all 355 older generic inputs and
checked adoption/restart of five saved source versions. Every previous row in
all 21 tables and all 190 earlier experiment files remains intact. The archive
now holds 7,455 results, 2,451 refutations and 45 source-state rows across checker
namespaces. Previous timing evidence remains unchanged. Resume with the typed
requested-patch argument using current child links; native source count/lifetime
preservation no longer needs to be assumed.


## 2026-11-08 08:08 UTC — exact native source-patch semantics

`SourcePatch.lean` defines the original clause bucket at each global edge of an
indexed source tree. `Patched old new edits` preserves start/height, makes every
requested edge equal its supplied original array, and preserves every edge
absent from the request. The leaf lemma retains clause order, duplicates and
empty clauses. The join lemma composes the two filtered edit lists at the typed
partition boundary; it does not infer source equality from relation equality.

`readNode` ties each executed relation/model lookup to the paired-store proof.
`readParts` decodes current child names, reads their current models, and uses the
live dependency invariant to identify the parent as their exact consecutive
join. That join equality is proof-only: checking a patch does not recompute a
relation join. `checkNodes` returns the visit count with a `Patched` certificate.
It accepts an unedited subtree only under identical names, handles a replacement
leaf with an exact original-array comparison, and combines the child proofs.
`check` attaches the two live root names to the transition.

The executed `checkRequest` also carries equations for the actual base, root and
edit-array JSON getters. `readEdits` proves entry-by-entry decoding of edge IDs
and clause arrays and the logical-edge bounds; the batch-size bound is recorded.
Duplicate rejection remains executed, and the transition proof does not assume
that the supplied edit list is unique. `SourceUpdates.patchQuery` now invokes
this checker before querying the same unchanged store and request.

The checker compares decoded original arrays, rather than raw JSON values.
Malformed payloads fail decoding. The specification's bucket functions and all
transition proofs erase. Runtime work includes typed node/body lookups, direct
child getters, edit-list filtering and original-array comparison, plus temporary
wrappers. Empty subtrees stop after identity and direct-root checks. There is no
flat-source traversal or summary recomposition. The visit counter keeps its prior
meaning; it is not a total native-instruction, allocation or bit-cost measure.
No timing improvement is claimed.

New regressions cover two edits across the root split with padding, request-order
independence, duplicate original clauses, literal order, equal-relation forged
payloads, omitted edits, duplicate/out-of-range/malformed requests, same-root
checks, different unedited aliases, missing roots and partition mismatch. The
alias rejection is deliberately conservative: source or relation equivalence
alone does not authorize changing an unedited identity.

Remaining priorities:

1. **Compose the full source API contract.** The native requested bucket
   transition is proved. Connect initial raw-CNF binding, root coverage and the
   serialized returned verdict/witness to a single successful-request theorem.
   Prove accepted source bucket equality gives the intended flattened original
   CNF, including padding and complete logical-edge coverage. Existing typed
   node decision semantics does not itself establish this whole API theorem.
2. **Python retention and complete serialized replay/SQLite refinement.** Native
   counts, live dependencies and patch semantics are proved; Python active-root
   policy, archive integrity, outer transport and generic relation loops are not.
3. **General factor row/equivalence-store refinement.** Adjacent-block guarantees
   do not establish general factor-DAG guarantees.
4. **Acceptance completeness and complete restricted costs.** Include caps,
   decrement acceptance, parsing, maps, integer/bit operations, array comparison,
   filter/lookup work, allocation, source payloads, transport and archive access.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** No unrestricted-SAT coverage or total-resource bound follows.

Validation: **169 tests pass**, including **30 source-update tests**. The decoder
also accepts all 4,096 entries up to root lookup, rejects 4,097 entries at the cap,
and leaves the worker usable. Lean audits **3,043 declarations / 1,461 theorem
declarations**, with no admits or added axioms. Runtime checkpoint `32b4748`
is committed and pushed. All 355 older generic inputs pass revalidation and
semantic audit, and all five source versions pass checked adoption and restart.
Every old row in 21 tables and all 198 earlier experiment files remains intact.
The archive now holds 7,810 results, 2,580 refutations and 50 source-state rows.
The manuscript and [patch verification record](../experiments/results/source-patches/README.md)
record the result. Earlier timings and all 32 previous manuscript proof blocks
remain unchanged. Resume with full source-API composition and persistent replay;
the native requested bucket transition no longer needs to be assumed.
