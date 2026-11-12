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


## 2026-11-08 09:06 UTC — complete successor formula and returned decision

`SourceFormula.lean` supplies the missing bucket-to-original-CNF step.
`flatten_source` proves that ordered flattening of the complete indexed interval
is exactly the node's original clause list, including order and multiplicity.
`bucket_present` characterizes its exact interval; `bucket_padding` proves that
padding contributes the empty clause array. `replaceBuckets` gives the requested
replacement function. `patched_buckets` and `patched_formula` connect an accepted
patch to that function and its complete flattened CNF. `patched_decide` and
`patched_unsat` give both SAT and UNSAT equivalences for this successor formula.
These flattening operations are specifications, not work on the native warm path.

`SourceVerdict.lean` certifies the native root checks: origin zero, enough leaves
for every logical edge, and the existing minimal padded height. Coverage proves
that every logical edge has a bucket and transfers to the predecessor through
the patch's start/height equalities. The query constructor records the actual
request root getter, current model lookup, coverage and returned Boolean getter.
The decision-only JSON getter equation holds definitionally. Witness-mode queries
reuse the existing returned-answer comparison; the proof does not yet certify
the serialized witness contents.

`compose_patch` identifies the queried node with the exact successor named in
the decoded patch request. It combines request decoding and bounds, both live
model lookups, coverage of both roots, the exact flattened successor formula and
both truth-value equivalences. `patchQuery` certifies the nested `verdict` getter
of the actual JSON result. `SourceUpdates.query_success` and
`patchQuery_success` transfer these certificates to the exposed JSON-returning
functions on every successful call. Native query and patch requests now execute
these constructors. Existing unknown-root diagnostics are preserved.

No flattening, full-source scan or relation-summary recomposition is introduced
on a warm decision/patch path. Direct lookups, root checks, decoding, comparisons,
filtering, wrappers, cached endpoint tests and requested witness work remain
costs. JSON getter proofs concern native JSON values; byte serialization and
outer transport are not thereby proved. There is no new timing, memory or
unrestricted-SAT guarantee.

New tests reject incomplete, shifted and nonminimal padded roots in both query
and empty-patch modes, with and without witnesses. Independent exhaustive
truth-table checks compare nested patch verdicts and direct queries against the
flattened original successor over 54 transitions, including historical branches,
1/3/5 logical edges, padding, deletion, repeated clauses and empty clauses. Both
SAT and UNSAT outcomes occur, and returned positive witnesses are checked
independently. These tests supplement, rather than replace, the proof.

Remaining priorities:

1. **Initial raw-CNF anchor and history composition.** Query/root coverage,
   complete successor formulas and the actual returned decision field are now
   proved. Connect the complete initial JSON CNF and original-bucket traversal
   to the live root under one native success theorem, then compose a history
   of accepted operations. Existing compiled-source and relation-binding theorems
   alone do not certify that entire initial source-provenance path.
2. **Serialized witnesses, Python retention and persistent replay.** Prove the
   truncated witness values and their original-variable interpretation, byte
   transport, active-root policy and complete replay/SQLite correspondence.
   Native live-child and incoming-count preservation remain established.
3. **Generic relation/factor stores.** Their retention loops and row/equivalence
   caches remain outside the adjacent-block source-store invariant.
4. **Acceptance completeness and complete costs.** Include source bounds, caps,
   decoding, array comparisons, map/bit operations, allocation, archive access,
   transport and restart. Logical path/event counts are not total machine costs.
5. **Compact general input, matched evaluation and cost-sensitive selection.**
   No unrestricted coverage or total-resource guarantee follows.

Verification: all **171 tests pass**, including **32 source-update tests**.
Lean audits **3,107 declarations / 1,506 theorem declarations**, with no admits
or added axioms. Runtime checkpoint `9673dee` is committed and pushed.
All 355 older generic inputs pass revalidation and semantic audit, and all five
saved source versions pass checked adoption and restart. Every old row in 21
tables and all 206 earlier experiment files remains intact. The archive holds
8,165 results, 2,709 refutations and 55 source-state rows. The manuscript and
[verdict verification record](../experiments/results/source-verdicts/README.md)
record the result. Earlier timing evidence and all 32 previous manuscript proof
blocks remain unchanged. Resume with the full initial raw-CNF anchor; complete
successor-formula equality, root coverage and returned native decision fields
no longer need to be assumed.


## 2026-11-08 10:15 UTC — initial raw-CNF binding and returned verdict

`SourceInitial.lean` closes the initial source-provenance path. The theorem
`compileSource_fields` derives actual width/layers/clauses getter equations from
success of the existing compiler. `readCompilation` carries these equations with
the compilation result, without a second parser or compilation implementation.

The executed `checkBinding` follows current live child names and models through
`readParts`; their join equalities come from the established live-store invariant.
Each leaf's original array must equal the compiled original bucket, including
literal order, duplicate clauses and empty clauses. Padding must match an empty
array. `matches_complete` proves equality with the full ordered concatenation of
these buckets. `matched_partition` composes this equality with the grouping
permutation. Thus the live root retains every raw input clause occurrence, but
global input order is not claimed to equal grouped tree order. `partition_eval`
proves equal evaluation for every original-variable valuation.

`InitialResponse` includes actual input and root getters, live model identity,
layout agreement, complete/minimal root coverage, exact bucket agreement, clause
permutation, nested returned verdict and SAT/UNSAT equivalences for the actual
input. `SourceUpdates.bindSource_success` transfers it to the exposed native
JSON-returning function. That function now executes the certified constructor.
The original relation-binding scan and decoded-answer comparison remain executed;
the checked verdict is returned unchanged instead of rewriting its equal answer.

The original-bucket traversal also certifies the actual `binding_visits` getter,
`visits + 1 = 2^(height + 1)` and `height < fuel`. The API uses fuel 17, covering
permitted heights through 16. The count covers logical node visits with padding.
It excludes parsing, map access, original-array comparisons, allocation, the
separate relation scan and witness work. Full initial binding remains charged;
warm query and patch paths are unchanged. Flattening is specification work.

New tests accept global clause permutations that preserve compiled bucket arrays,
then reject dropped/added duplicate clauses and changed literal order despite
equal SAT answers. They distinguish one empty clause from two, exercise both
response modes, and check exact padded scan counts for 1/2/3/5/17/33 logical edges.
Malformed input, wrong layouts, partial/shifted or missing roots and invalid
witness-mode fields are rejected while the original live root remains usable.
These finite tests do not establish cap-wide acceptance completeness.

Remaining priorities:

1. **Operation-history composition.** Initial, query and patch native APIs now
   have individual success theorems. Define a history with store states and
   retained source identities, then compose initial anchoring, successful node
   definitions/deletions and requested patches. Keep the original CNF permutation
   at initialization distinct from the exact ordered bucket replacements later.
2. **Serialized witnesses, Python retention and persistent replay.** Certify
   truncated witness values and original-variable interpretation, byte transport,
   active-root retention and complete replay/SQLite correspondence. Native current
   child identities and incoming counts remain proved.
3. **Generic relation/factor stores.** Their retention loops and row/equivalence
   caches remain outside the adjacent-block source-store invariant.
4. **Acceptance completeness and total costs.** Include source bounds, caps,
   error paths, decoding, array comparisons, map/bit operations, allocation,
   archive access, transport and restart. Successful logical visit counts are
   not total machine-cost bounds.
5. **Compact general input, matched evaluation and cost-sensitive selection.**
   No unrestricted coverage or total-resource guarantee follows from this result.

Verification: all **174 tests pass**, including **35 source-update tests**.
Lean audits **3,154 declarations / 1,539 theorem declarations**, without admits
or added axioms. Runtime checkpoint `92a1ddd` is committed and pushed. All 355
older generic inputs pass revalidation and semantic audit. All five saved source
versions pass checked adoption and restart. Every old row in 21 tables and all
214 earlier experiment files remains intact. The archive holds 8,520 results,
2,838 refutations and 60 source-state rows. The manuscript and
[initial-binding record](../experiments/results/source-initial/README.md) retain
the evidence. Earlier timings and all 32 previous manuscript proof blocks remain
unchanged. Resume with native operation-history composition; the complete initial
raw-CNF-to-live-root-to-returned-decision path no longer needs to be assumed.

## 2026-11-08 — certified affine growth instead of assignment-table expansion

User direction: attack the expansion bottleneck through genuine fresh-variable
growth, closed compact summaries, structural reuse and cumulative accounting.
Runtime checkpoint **3b953b8**, pushed. This is a separate restricted affine path;
it does not silently replace or weaken the existing CNF source-store contracts.

Implemented four Lean modules and `PersistentSolver.affine_grow`. Each append
introduces a fresh width-`b` block and equations on the old and fresh boundaries.
The exact summary is the existential projection of the full original history.
Elimination and basis compression operate directly on GF(2) coefficient vectors,
with at most `b+1` summary rows and `(b+1)^2` logical cells. Contradiction is explicit;
old version answers remain valid even when an added batch makes a successor UNSAT.
The native path executes the certified charged loops and returns proved decision
and charge fields for typed states. Both SAT and UNSAT refer to the specified
constraint history, not to different input-size conventions.

The charge bound is `O(b^3+b^2*c)` per resident append with `c` new equations.
`replayRun_bound` sums the same charges over typed original histories. Full-list
pivot scans, produced coefficients/rhs and terminal checks are charged; primitive
machine instructions, allocation, parsing, map work, transport and archive access
are not. This improves on a purely declared arithmetic ledger: value equivalence
and per-loop charges are now part of the executed coefficient implementation.
It still does not provide an end-to-end machine-cost theorem.

Immutable source batches and results persist in the new `affine_states` and
content-addressed object records. Replay reconstructs from original equations,
never saved summaries or answers. Corrupt source objects and malformed histories
are rejected. Failed transactions preserve old database rows; extra immutable
native nodes can remain until restart. The current summary is bounded; retained
history grows. No full-history witness is output. Caps (width 128, batch 4,096,
native versions 4,096) cause refusal, not a negative verdict. Native version
capacity includes initialization, so a single resident chain has at most 4,095
appends. The mathematical result has no such fixed cap.

Validation: **184 tests**, including **10 affine tests**; Lean audit **3,485
declarations / 1,708 theorem declarations**, with no admits or added axioms.
Exhaustive frontier sets cover 135 branching updates at widths 1..3. Independent
full-system elimination covers width 128. Archived evaluation checks **284**
decisions/restarts and retains **268** affine versions at widths 2/8/32/64.
An 80-step fixed-width regression has constant per-step charge and summary size.
All 355 earlier generic inputs and five source versions pass revalidation/restart.
All old rows in 21 tables and all 222 earlier experiment files remain intact,
including after the affine experiment. Archive counts: **8,875 generic results /
2,967 refutations / 65 source-state rows / 268 affine-state rows**. See the
[affine evidence](../experiments/results/affine-growth/README.md).
The manuscript adds the exact-growth proposition, cost model and limitations,
attributes affine tractability to Schaefer and Gaussian elimination, and preserves
all 32 earlier proof blocks. There is no matched speed comparison in this study.

Remaining priorities, with distinct scopes:

1. **Compose native operation histories.** For the general source-CNF API,
   compose existing initialization/query/patch success theorems with named-store
   definitions/deletions and retained source identities. For affine, typed history
   exactness is proved, but raw JSON/named-store history correspondence is still
   an integration boundary. Do not report the former as solved by the latter.
2. **Persistence and witness refinement.** Prove Python retention/replay/SQLite
   correspondence and serialized general-source witnesses. An affine witness API
   would require saved elimination information/back-substitution and output costs.
3. **Broader growth and mixed structure.** Add supplied tree decompositions with
   certified separators or extend the affine frontier contract. Recognition and
   maintenance costs must be charged. Arbitrary older-block edits are unsupported.
   A mixed CNF/XOR route could use supplied small backdoors; finding such backdoors
   and the worst-case `2^k` branching remain explicit restrictions.
4. **Complete costs and lifetime policy.** Refine coefficient charges to actual
   field/index/list operations and include native maps, decoding, allocation,
   archive growth, errors and restarts. Add bounded active affine retention without
   deleting durable versions; current native capacity refuses when full.
5. **Matched evaluation and dispatch.** Compare this path with a full Gaussian
   solver and checked CDCL on identical XOR workloads, include fixed/growing width,
   repeated/novel equations and restarts. Automatic recognition or selection needs
   conversion/verification costs. Current evidence establishes no competitive
   speedup, general-CNF coverage or unrestricted polynomial expansion.
6. **Generic relation/factor stores.** Their retention and equivalence caches
   remain outside the adjacent-block source-store invariant. Compact affine
   summaries do not establish polynomial closure for those general representations.

Resume with the general native history theorem or a matched affine cost study.
Retain `experiments/results/affine-growth/` and all earlier evidence; do not overwrite
older timing artifacts. The polynomial restricted step is now concrete and checked;
unrestricted SAT still lacks the required compact-closure/construction invariant.

## 2026-11-08: native histories, erased affine provenance and matched reuse

Runtime checkpoint **`88f26a8`** addresses native source-history composition,
bounded active affine retention, and the missing matched reuse comparison.
Evidence: [history-retention](../experiments/results/history-retention/README.md).
All older results and timing artifacts remain available.

**Native source-CNF histories.** The worker now executes `SourceHistory.handle`.
Its success contract retains the complete initial raw-CNF, current-root or exact
patch response certificate, as appropriate. Errors leave the predecessor store
unchanged, including failures after partial local construction. The finite-trace
induction composes arbitrary definition, deletion, reset, compilation, binding,
query and patch interleavings. Every successful query decides the complete
original CNF of its root in that event's store. Earlier observations remain valid
under continuation. This is eventwise semantics: a name deleted and reused can
refer to a different formula. It does not prove immutable Python content-hash
lineage across process generations, byte transport, serialized witness contents
or SQLite behavior. The worker does not accumulate the mathematical trace.

**Affine residency.** Inspection found that the earlier native `State` carried
its entire original history as runtime data. Deleting ancestor map entries alone
would not release those ancestors. `AffineResident` now retains original-history
semantics through Mathlib `Erased`; generated C has only the summary as the
resident state field. Current request JSON and node metadata remain additional
runtime data. The summary and coefficient-charge proofs still hold.
`dropNames_preserves` proves other native lookups unchanged after eviction.
Python protects the required parent and evicts older resident nodes, with a
configurable cap of 2..4,096 versions (default 256). It reconstructs evicted
versions from original archived equations, reading one batch at a time. Failed
transactions mark residency uncertain and trigger an affine-store reset before
the next checked replay. The simultaneous native cap no longer caps history
length: a regression appends 4,101 times, queries an evicted historical version,
and restarts with only two residents. The replay plan/cycle check still uses
O(T) identifiers; the durable history grows. A resident count is neither a byte
bound nor a formal proof of the Python policy.

**Validation and preservation.** All **190 tests** pass, including **15 affine /
36 source-update** tests. Lean audits **3,625 declarations / 1,766 theorem
declarations**, without admits or added axioms. All **355** earlier generic inputs
pass revalidation/audit; five source versions pass adoption/restart. All **268**
old affine versions pass source replay under a four-version cap, with positive
and negative restart checks under a two-version cap. Every old row in **22 tables**
and all **233** earlier experiment files remain intact. The live archive contains
**9,230 results / 3,096 refutations / 70 source-state rows / 536 affine-state rows**.
All 33 earlier manuscript proof blocks remain verbatim; one native-history proof
is added.

**Matched study.** Six fixed-width streams (2/8/16, repeated/novel equations), four
modes and three sequential repetitions give **72 runs / 1,296 correct decisions**,
including 72 negative decisions and no failed runs. Each mode receives the same
original parity systems and retains its results. Resident and full-parent-replay
modes share the delta input, archive and native algebra; restart and checked-CDCL
modes charge their lifecycle/conversion costs. At width 16, the median full-replay
times are **2.85 / 2.30** times the resident times. The smallest repeated stream
shows no gain. Three repetitions do not establish significance for small
differences or general workload performance. The CDCL pipeline uses a different
representation and certification path, so its timings do not isolate solver
algorithm speed. Independent full Gaussian elimination checks original-system
answers; it is not a certified timed baseline. A pilot overlapping archive
adoption is retained separately and excluded from the reported comparison.

Remaining priorities, with the newly closed scopes distinguished:

1. **Protocol and persistence refinement.** Connect affine raw JSON and native
   named-store histories to the typed history theorem. Prove Python content-hash
   lineage, retention/replay and SQLite correspondence, including failures and
   process-generation changes. The general native source-CNF eventwise history
   theorem is now available; it does not discharge these separate obligations.
2. **Witnesses.** Prove serialized general-source witness contents. Add an affine
   full-history witness route with retained elimination information and checked
   back-substitution; charge the necessarily growing output and archive work.
3. **Broader structure.** Extend supplied decompositions to certified separators
   on trees or mixed CNF/XOR with supplied small backdoors. Charge recognition,
   maintenance and conversion. Arbitrary older-block edits and worst-case `2^k`
   backdoor branching remain outside the current affine append guarantee.
4. **Complete costs.** Refine coefficient charges to actual field/index/list,
   decoding, native-map and allocation costs. Include archive growth, failure,
   replay planning, restarts and physical storage. The new eviction policy and
   erased provenance remove a concrete lifetime problem; total resource bounds
   and formal Python-policy correctness remain open.
5. **Evaluation and selection.** Extend the matched study to growing widths,
   adversarial mixes, realistic inputs and a timed complete Gaussian baseline.
   Add cost-sensitive dispatch only with charged recognition/conversion and
   comparable correctness obligations. Six synthetic streams do not show a
   uniform benefit, broad CNF coverage or significance for small differences.
6. **General relation/factor stores.** Prove their retention and equivalence-cache
   invariants separately. The adjacent-block source invariant and compact affine
   summaries do not establish compact closure for general representations.

Resume with affine protocol/history refinement or checked witness reconstruction.
Keep the matched and pilot evidence separate. There is still no compact-closure
or efficient-acquisition invariant for unrestricted SAT; no conclusion about
P versus NP follows from these restricted results.

## 2026-11-08: affine input provenance and expansion-focused priorities

Runtime checkpoint **`1037595`** closes the native affine decoded-input/history
connection. The user has redirected the existing hourly task toward **reducing
expansion work through compression and reuse patterns**. Proof, persistence and
evaluation work should support concrete expansion improvements rather than
continue as an independent general-hardening queue.

`AffineProtocol` now certifies exact Boolean row fields, dimensions, row order
and multiplicity, initial width, the actual parent lookup, returned node and
query lookup. `AffineHistory.handle` is the executed worker dispatcher. Its
chronological `Origin` invariant proves that every resident history after a trace
from the empty store comes from actual decoded requests in that trace. Successful
queries decide that original history. Rejections preserve the predecessor;
eviction retains only old nodes; reset empties the store. Mathematical trace and
origin evidence are erased from runtime states.

An important reuse distinction is now explicit and tested. Retrying a retained
child returns its existing history even if its parent name was deleted and
redefined. A fresh child binds the current parent. Deleting the old child and
reusing its name can therefore yield a different answer. The retry path also
checks decoded modes, widths or parent names, and typed equation lists; its
source-agreement proof does not assume correctness of Lean's partial general
JSON equality function. This adds parsing/comparison work on explicit retries.
Byte transport, cross-process content-hash lineage, Python/SQLite refinement and
serialized witnesses remain separate. There is no new performance claim for
this protocol checkpoint.

All **192 tests** pass, including **17 affine / 36 source-update** tests. Lean
audits **3,794 declarations / 1,836 theorem declarations**, without admits or
added axioms. All 355 old generic inputs, five source versions and 268 distinct
old affine versions pass revalidation; both affine verdicts pass restart under a
two-version cap. Every old row in 22 tables and all 394 prior experiment files
remain. The live archive has **9,585 results / 3,225 refutations / 75 source-state
rows / 804 affine-state rows**. All 34 prior manuscript proof blocks remain;
one affine-history proof is added. See
[the evidence](../experiments/results/affine-history/README.md).

### Current expansion costs and a concrete reuse pattern

For boundary width b and c new equations, a resident affine append has reference
coefficient-work bound **O(b^3 + b^2 c)** and summary payload **O(b^2)**. These do
not depend on the number T of earlier appends. Cold replay sums prior append
costs and retains O(T) identifiers in its plan. Parsing, comparison, maps,
hashing, serialization, allocation and archive work are additional costs. A
complete machine-time bound has not been proved. General CNF still lacks the
compact-closure guarantee needed for polynomial expansion.

`experiments/analyze_affine_reuse.py` replays the six frozen comparison streams,
retaining all source versions and checking 108 decisions independently. Each
repeated stream has **14 identical kernel inputs among 18 expansions**, despite
18 distinct version identities. Here a kernel input means the exact ordered
parent summary and the exact local equation batch, including its order. At
width 16, repeated calls account for **643,566 / 719,509 coefficient-work units
(89.4%)**; 240 duplicate rows also occur across the stream. All three novel
streams have zero such repeats. Sorting/deduplicating batches reveals no extra
repeated calls in these cases. The diagnostic installs no kernel cache and
establishes no realized speedup. It does not detect row-space equivalence or
variable symmetries. Earlier timing artifacts remain tied to their old binary.

### Next expansion priorities

1. **Reuse exact algebraic transitions across distinct histories.** Cache the
   boundary transformation for identical width, parent summary and equation
   batch. Construct a fresh source-history certificate for every append; do not
   return another version's history or confuse equal SAT answers with equivalent
   boundary relations. Check full keys rather than trusting hash equality.
   Charge comparison, lookup, insertion, eviction and durable version records.
   Compare against the current path on repeated and novel streams.
2. **Compress equation batches and boundary keys.** Prove and measure duplicate
   elimination first. Then test canonical row-space forms and variable renaming
   only when their discovery/normalization cost can repay the saved elimination.
   Preserve original row order and multiplicity in the source archive even when
   the computational representation removes redundancies.
3. **Update only changed structure.** Investigate small-rank equation changes,
   reusable elimination steps and shared separator components. State exactly
   which edits preserve the summary invariant and when reconstruction is needed.
   Expand supplied decomposition families with recognition/maintenance costs.
4. **Measure all acquisition and reuse costs.** Broaden repeated/novel workloads
   to growing widths, adversarial misses and cold reconstruction. Track stored
   components, compression ratios, reference work and elapsed phase costs.
   Retain unsuccessful trials and counterexamples; avoid repeating dead ends.
5. **Supporting obligations.** Complete Python/SQLite and witness refinement,
   general-store invariants and machine/resource accounting when they are needed
   to justify a specific expansion optimization. These are still open; the native
   source-CNF and native affine event-history scopes are now proved.

The scheduled task remains hourly in this chat, with these expansion priorities.
The next concrete target is an exact transition cache that separates a reusable
boundary calculation from each append's immutable original history.


## 2026-11-08: exact transition reuse implemented and measured

Runtime **`f80f678`** completes the first expansion priority above. The reusable
`Kernel previous equations` certifies its exact summary, verdict and nominal
coefficient charge. A hit checks width and both complete typed input lists after
hash selection, then attaches the result to the current parent's erased original
history. The native chronological origin theorem still applies, including the new
cache-configuration operation. Cache entries contain no source ancestor states.

The service defaults to 64 direct-mapped slots, configurable from 0 to 4,096.
Zero bypasses hashing/lookup. Version eviction leaves kernels available; reset
and restart clear them. Each entry retains O(b^2+b*c) coefficient cells; this is
not a byte/RSS bound. Hash collisions can evict useful entries but cannot cause a
false hit. Query reports retain creation metadata; per-request `affine_updates`
separates actually executed construction work, hits/misses, key scans and
candidate-comparison bounds. Completed source versions/results remain durable.

### Costs and evidence

- A miss retains the **O(b^3+b^2*c)** elimination bound and adds cache overhead.
- A hit skips elimination and decision. Its hashed coefficient payload is at most
  **(b+1)^2+c*(2*b+1)**, with at most one structural candidate comparison. List,
  dimension and map checks, hash arithmetic, allocation, decoding, transport and
  archive work remain additional costs. A hit is not a zero-cost expansion.
- Over actual hits A, the elimination/decision ledger is the sum of nominal
  charges for non-hits. Capacity, collisions and input variation determine A;
  no positive hit rate is guaranteed.
- Five sequential, rotated, same-binary repetitions compare 64 slots with zero.
  The six old input streams are unchanged. Two width-32 streams add longer
  histories. **80 runs / 1,760 independently checked decisions** retain all
  completed versions and results, under four resident versions.
- Width-16 repeated: **14/18 hits**, coefficient ledger **719,509 -> 75,943**
  (89.4% reduction); hashing **21,025** cells, candidate comparison at most
  **18,864**. Median elapsed service time **167.57 -> 144.21 ms** (13.9% less).
- Width-32 repeated: **30/34 hits**, ledger **10,987,813 -> 565,063**;
  median **496.37 -> 215.54 ms** (56.6% less, **2.30x**). Width and stream length
  both increase, so this does not isolate scaling with width alone.
- Novel streams: **zero hits**, median overhead approximately **0.1--0.5%**.
  Small differences are descriptive, not a significance test or overhead bound.
  An overlapping-adoption pilot is retained separately and excluded. The final
  run starts only after adoption finishes; both use identical input bytes/binary.

**197 tests** pass, including **22 affine / 36 source-update** tests. Lean audits
**3,938 declarations / 1,875 theorem declarations**, without admits or added
axioms. New regressions force single-slot collisions, distinguish SAT boundary
relations, compare complete frontiers with the cache off/on, and exercise source
rebinding, eviction, restart, configuration rejection and rollback. Generated C
inspection confirms no elimination call on hits and no runtime history ancestors.

All **355** earlier generic inputs, **five** source versions and **268** distinct
affine versions pass revalidation. Every old row in **22 tables**, all **405**
preceding experiment files and all **35** prior manuscript proof blocks remain.
The live archive now has **9,940 results / 3,354 refutations / 80 source-state
rows / 1,072 affine-state rows**. The disabled-cache pattern diagnostic reproduces
its previous counts and charges. The manuscript adds an exact-kernel proposition
and the measured comparison. See [the evidence](../experiments/results/affine-kernel-cache/README.md).

### Next concrete expansion work

1. **Remove redundant rows before elimination.** Start with exact duplicate rows,
   prove preservation of every boundary solution, retain original multiplicity in
   source records, and measure normalization versus saved construction on misses.
   The width-16 repeated stream still contains 240 duplicate rows. Exact kernel
   hits already avoid their elimination; compression must justify its own work.
2. **Expose equivalence beyond exact ordered keys.** Test canonical row-space
   forms and variable permutations with full certificates. Measure discovery and
   normalization before claiming a wider useful reuse class. The earlier batch
   sorting/dedup diagnostic found no additional hits in the six frozen streams.
3. **Share work across small changes.** Reuse elimination steps for low-rank
   equation updates or unchanged separator components; prove when changes preserve
   the retained interface and when reconstruction is required.
4. **Improve cache admission and collision behavior only with evidence.** Stress
   interleaved hot kernels, adversarial collisions, growing widths, cold replay
   and variable batch sizes. Compare slot policy, retained bytes and per-phase
   costs. No all-workload speedup is possible for blind exact caching.
5. **Retain the remaining proof boundary.** Durable kernel certificates, serialized
   witnesses, Python/SQLite correspondence, complete machine/space costs and
   general-CNF compact closure are still open. Current kernels are process-local;
   restart reconstructs from original source batches. This result says nothing
   new about unrestricted SAT or P versus NP.

## 2026-11-08: storage growth and an additional expansion opportunity

Read-only audit at `9773ede`: the main database is **18,907,136 bytes (18.03 MiB)**.
Its **1,072 affine result rows represent 268 distinct versions across four engine
namespaces**, not 1,072 distinct histories. The 268 `affine_version` objects occupy
**4,205,628 raw JSON bytes / 139,444 compressed payload bytes**; 537 result objects
occupy **117,090 compressed payload bytes**. Database pages/indexes and other
solver paths are additional. The much larger local `.cache` tree includes all
retained experiment databases and backups; it is not one solver's active state.

For width b, at most c equations per append, T archived versions, V resident
versions and K kernel slots:

- The current summary has at most `(b+1)^2` coefficient cells.
- Retained native version summaries **and request bodies** plus kernel keys and
  results have coefficient/request payload O((V+K)*(b^2+b*c)), before metadata
  and transient allocations. Defaults are V=256 and K=64. Neither cap bounds RSS.
- Original history records store a parent link plus the new batch, avoiding a
  complete-history copy on every append. Raw source coefficient payload grows
  as O(sum_t b*c_t), or O(T*b*c) with fixed upper bounds. Logical version/answer
  records also grow with T. Step counters, indexes, engine namespaces and their
  byte encodings are additional; this is not a strict constant-byte-per-step theorem.
- By default archived affine results contain no boundary summary (`summary=False`).
  Requesting and retaining summaries can add O(T*b^2) coefficient payload. Exact
  duplicate whole objects share one row, but report/engine variants can add records.
- Cold replay still keeps O(T) identifiers in its backward plan/cycle check and
  reconstructs from original batches. There is no durable checked-kernel shortcut.
- The archive has no default size cap. An optional page cap refuses new work when
  full; it neither discards old results nor establishes a hard physical-disk bound.

**New concrete target: share exact equation batches across version records.**
The source-object hash includes the parent, so an identical local batch inside a
new history is currently serialized/compressed again. `KnowledgeStore` deduplicates
whole objects and compresses each object independently; it does not intern the
embedded batch. Separate immutable batch objects could preserve exact order and
multiplicity while version records retain parent/batch links. For U distinct
batches, their coefficient payload would scale with U instead of T; version
metadata would still grow with T. A later native batch-registration interface could
also avoid decoding and hashing a known batch on every reuse, but needs a new
source-origin proof and explicit checking of registrations.

`experiments/results/affine-kernel-cache/storage-audit.json` records a serialization
model using the existing zlib setting. In the width-32 repeated stream, 35 source
versions contain only four distinct batches. Their compressed source payload is
**16,656 bytes**; the modeled batch objects plus links occupy **5,593 bytes**
(66.4% less). Width-16 repeated payload falls **4,265 -> 3,009 bytes** in this model.
The same split **increases** modeled novel-stream payload: **6,226 -> 7,616 bytes**
at width 16 and **22,000 -> 24,344 bytes** at width 32. These estimates exclude
additional SQLite/index costs and are not measured database savings. Existing
parent hashes are placeholders; migration, runtime and checking costs remain
unmeasured. Old rows are preserved; new formats would first apply to new versions.

Prioritize a measured sharing/admission policy alongside duplicate-row removal.
Preserve exact source batches; use semantic normalization only in a separately
certified computational representation. Bit-packed Boolean storage, byte-based
cache budgets and phase/RSS measurements are further concrete targets. Broader
canonicalization, low-rank updates, checked restart checkpoints and complete
Python/SQLite/resource refinement remain open. No compact-closure result for
general CNF follows from the current affine representation.


## 2026-11-08: shared batches and certified duplicate removal

Runtime **`e0cb8d3`** implements the two concrete targets from the storage audit.
`AffineNormalize.lean` proves exact row membership, no duplicates, length reduction
and preservation of every boundary assignment. `Kernel.restoreOriginal` attaches
a normalized calculation to the actual original batch and current parent history.
The native chronological origin proof remains valid. Prepared typed batches and
normalized transitions have separately occupied bounded maps (64 slots each by
default); each hit checks full equality after hash selection.

The archive now supports an `affine_batch_ref_v1` encoding under the same legacy
logical version hash. Reads validate the shared batch and reconstructed original
source. Every old inline object stays unchanged. Only repeated batches with at
least 128 compressed-payload bytes saved per reference are admitted; the discovery
index retains at most 256 hashes. Small and unique batches stay inline. The policy
can still add CPU work and first-admission overhead; it has no universal space or
time guarantee. Both new options are independently configurable and default on.

### Measured gains and remaining costs

The matched study compares baseline, normalization, sharing, and both options;
all modes keep the prior exact kernel cache. Five sequential rotated repetitions
cover 120 runs and **2,800 decisions**, independently checked against complete
original systems. Archive adoption finishes before the final run. The pilot is
retained separately and excluded; input and runtime fingerprints agree.

- Width-32 changing multiplicity: **0 -> 14/18 hits**, executed coefficient work
  **30,266,133 -> 461,575**, median time **1,246.55 -> 430.52 ms** with both options
  (65.5% less). Raw rows total 8,673, normalized rows 513. Normalization alone takes
  417.58 ms. Original batches remain distinct in storage.
- Width-16 changing multiplicity: **367.70 -> 223.19 ms** (39.3% less).
- Width-32 exact repeated batches: source payload **16,656 -> 6,499 bytes**
  (61.0% less); database **274,432 -> 262,144 bytes** (12 KiB less). One shared
  batch supports 30 references while all 35 versions remain. Median time with
  both options **236.75 -> 252.47 ms** (6.6% more). Extra reconstruction and
  validation remain a concrete cost to reduce.
- Width-16 repeated batches fail the savings threshold and stay inline. Novel
  streams gain no hits or shared objects and retain identical source payload.
  Small median timing changes (+0.8%, -0.2% with both) establish no broad benefit.

**Memory is not fully shared yet.** Prepared normalized lists are shared with
transition keys, but preparation entries retain the original typed input for
checking, and each resident version still stores its request JSON. Additional
cache entries may increase RAM. With width/row bounds b,c, retained coefficient
and request payload is O((V+K+P)*(b^2+b*c)), before metadata and temporary work,
where P is preparation slots. Slot counts are not byte/RSS bounds. No measured
process-memory reduction is claimed. Hash-set probes/resizing/collisions and
allocation remain outside the normalization input-cell counter.

**Storage now follows a hybrid model.** Inline versions keep their batch payload;
shared batches retain their coefficient payload once plus links for each version.
Thus source coefficient payload is O(sum_inline b*c_t + sum_shared_batches b*|B|),
before compression, metadata, results and indexes. Fully novel input still gives
O(sum_t b*c_t), and the archive has no default size cap. Existing inline records
are not rewritten, so old archive size does not automatically shrink. The main DB
is now **19,738,624 bytes**; it includes a new engine namespace and contains
**10,295 results / 3,483 refutations / 85 source rows / 1,340 affine rows**. The
latter remain **268 distinct histories**, now across five engine namespaces.
Retained experiments and backups consume additional disk space.

### Verification and preserved evidence

**207 tests** pass (26 affine growth / six affine archive / 36 source updates).
Lean audits **4,043 declarations / 1,911 theorem declarations** without admits or
added axioms. Tests cover complete frontier equivalence, changing multiplicities,
collisions, corrupt references, restart with sharing disabled, and rollback after
shared admission. Generated C skips deduplication on preparation hits and performs
no second elimination when transporting back to original-source meaning.
All 355 older generic inputs, five source versions and 268 affine versions pass
revalidation. Every old row in 22 tables and all **583** preceding experiment
files remain intact. The old unnormalized diagnostic reproduces its counts and
charges. All **36** preceding manuscript proofs are unchanged; one is added.
See [the complete evidence](../experiments/results/affine-batch-reuse/README.md).

### Next priorities for expansion effort

1. **Checked native batch handles.** Register original batches once and reuse
   typed/normalized data across requests. Eliminate repeated JSON decoding and
   per-version request copies where possible, with a revised source-origin proof.
   This targets the measured repeated-stream overhead as well as memory.
2. **Byte budgets and admission.** Profile live allocations and compressed reads;
   compare saved payload with added checking/reconstruction. Bound cache bytes,
   not just slots. Keep rejection atomic and all durable results intact.
3. **Broader certified equivalence.** First-occurrence normalization does not
   identify row permutations, equal row spaces or variable renaming. Charge
   discovery and transport before claiming extra useful hits.
4. **Low-rank changes.** Reuse elimination structure for small equation edits;
   identify exact interface conditions and reconstruction requirements.
5. **Checked restart checkpoints.** Native caches remain process-local; cold
   replay still walks source histories and keeps an O(T) identifier plan.
6. **Remaining refinement boundary.** Python/SQLite, serialized witnesses and
   complete machine/space costs remain open. None of this gives compact closure
   for general CNF or changes the status of unrestricted SAT or P versus NP.


## 2026-11-08: complete resource audit before the next optimization

[Current computation, memory and expansion bounds](resource-bounds.md) now
collects the formal results and implementation limits across every active solver
family. The [read-only snapshot](../experiments/results/resource-audit-2026-11-08/snapshot.json)
records the source revision, page/object inventory and recomputed phase medians.
No solver behavior or previous results changed in this audit.

Two concrete affine-hit costs are now identified in code and preserved records:
`AffineGrowth.run/ensure` reread the original source and parent, and native
`defineChecked` always returns the full summary. A measured width-32 shared hit
has zero elimination work but nine object reads and 8,175 response bytes. Checked
batch handles, lightweight parent metadata and compact append replies can target
these costs; the current proof must be maintained when changing the protocol.

Memory claims also need a better measurement boundary: service RSS is cumulative
Python-process RSS, and reaped-child statistics omit the simultaneous live native
process tree. Slot limits and compressed disk payload are not RAM bounds. The
archive inventory additionally shows that the measurement/result tables and their
primary indexes occupy about 64% of the current main DB. Which cost dominates
therefore depends on whether the workload has hits, novel rows, cold replay,
growing width, or many preserved result namespaces. Future changes should be
chosen against this inventory and measured independently.


## 2026-11-08: reuse checked resident widths; assess KD-tree search

`AffineGrowth.verified` now retains the width returned by a successful native
definition, after checking it against the validated original source. Forward
replay can compare a child's width with that resident parent metadata instead
of decompressing and decoding the parent's full batch again. The value exists
only with the resident node: eviction, worker replacement, reset and failed
transactions remove it. A mismatching native width fails before publication.
Every public base read still validates original archived content. Cold replay
still reads and checks every missing source and recreates native definitions.

This is a bounded Python orchestration improvement, not a new Lean theorem.
The native binary, its original-history theorem, all manuscript proofs and the
main archive are unchanged. Retained metadata adds O(V) bounded integers;
one transient parent decode disappears, but whole-process memory is unmeasured.
`affine_reuse_metadata=False` provides the matched previous read path.

The [matched evidence](../experiments/results/affine-resident-metadata/README.md)
contains five rotated repetitions of widths 16/32/64 and repeated/novel streams:
**60 runs / 2,160 decisions**, including two fresh-service cold reconstructions
per run. Independent full-history elimination verifies the inputs; original
source rows and identities are recovered in every run. Elimination counters and
kernel hits are identical across modes.

- Inline warm append: **4 -> 3** object reads. Shared warm append: **9 -> 7**;
  the width-32 sample reads **2,904 -> 2,291 packed bytes**. Wire bytes and
  inserted source/result payload are unchanged.
- Width-32 repeated stream: 28 warm appends **84.39 -> 78.22 ms**; whole stream
  including setup/shutdown **238.00 -> 232.72 ms**. Two cold reconstructions
  **214.46 -> 201.90 ms**, with **384 -> 258** object reads.
- Width-64 repeated: warm appends **280.72 -> 260.76 ms**; whole stream
  **534.69 -> 509.73 ms**. Cold reconstructions **640.65 -> 599.29 ms**.
- Novel streams still need the same elimination. Width-32 whole-stream median
  **388.70 -> 393.50 ms** is slightly worse despite fewer reads. Local timing
  differences are descriptive; no universal speedup or complexity-class change
  follows. Source payload and matched database sizes remain equal.

**210 tests pass**, including the existing long-history, source-corruption,
forged-width, branching-frontier and restart tests plus direct checks of the
metadata lifetime and read reduction. The initial additional test expected the
wrong exception for damaged compressed bytes; that failed test log is preserved.
Its fixture now selects raw encoding to test an explicit size-integrity rejection.
All **743** preceding experiment files and all rows of the main archive's **22**
tables are preserved; no new engine namespace was needed.

The user proposed KD-trees. [The indexed-reuse assessment](indexed-reuse.md)
records the literature, a one-bit SAT/UNSAT counterexample, source/interface and
invalidation requirements, full costs and a matched future experiment. Existing
native exact lookup examines one hash-selected candidate, not every stored state.
A KD-tree could shortlist candidates for low-rank or other checked repairs;
that repair path is currently missing. It cannot turn proximity into a valid
answer or replace exact checks. No KD-tree speedup has been measured.

**Next bottleneck:** seven reads remain on a shared warm append, together with
full request decoding, repeated source serialization and an 8,175-byte native
reply in the width-32 sample. Pursue checked batch handles and compact definition
replies, then measure byte admission and repair/canonicalization opportunities.
The backward replay plan remains O(T), persistent storage remains unbounded by
default, and unrestricted SAT receives no affine closure guarantee.


## 2026-11-08: cheap expansion as a maintained structural invariant

The user requested conditions that make the favorable case available for every
allowed expansion. [The precondition analysis](expansion-preconditions.md)
specifies sufficient boundary information, closure, cheap recognition, bounded
affected structure, checked construction, initialized/resident state and full
accounting. This supplies a meaningful restricted-family target; caching or
precomputing all cases cannot establish it without construction/space bounds.

The preserved affine benchmarks expose an immediate opportunity: all 192 regular
updates across six width-16/32/64 repeated and novel streams have point successor
boundaries. The initialization fixes the fresh block and each following batch
defines the next variables from old ones. The two final branches per stream are
contradictory and unconstrained. A substitution prototype covers **all 204**
updates. It matches complete frontiers on **5,010 accepted cases** among 11,862
small tests and declines 6,852 for general solving. This reveals an evaluation
restriction as well as an optimization opportunity: "novel batch" does not mean
"general correlated affine boundary."

`StructuralExpansion.lean` adds five checked semantic theorems: empty propagation,
total-relation nonemptiness, functional singleton closure, bijective transport,
and a singleton append tied to the original affine history and batch semantics.
The complete Lean audit passes **4,049 declarations / 1,916 theorems** without
admits or new axioms. These are conditional semantics; executable recognition,
native dispatch, source-origin integration and the specialized resource ledger
remain open. The native binary has not changed. The manuscript now states both
the structural result and the limitation discovered in the existing workloads.

For a known point and a recognized functional affine update, direct evaluation
targets O(b*c+b^2) dense coefficient work, including recognition and explicit
point-summary construction, instead of generic O(b^3+b^2*c') elimination. For an
arbitrary affine boundary and a signed-permutation update, column transport and
RHS adjustment target O(r*b) after O(b*c) recognition. These are derived targets,
not measured native speedups or optimality theorems. Original source/archive
growth and transport still have to be charged.

**Revised next priority:** certify a point-boundary capability and functional-row
recognizer, construct successors directly, and preserve native chronological
history and accounting. Add correlated/partial frontiers and unsupported updates
to matched evaluation before drawing general conclusions. Then implement the
signed-permutation case, checked batch handles and compact replies. KD-trees can
later shortlist candidates for a checked repair; they do not replace these
preconditions. Retain the generic path and every previous source/result.


## 2026-11-08: refocus on arbitrary SAT and interacting tractable classes

The user now prioritizes minimum-cost expansion for arbitrary SAT. The next
milestone therefore moves from an affine-only fast path to a general residual
decomposition with tractable leaves. [The analysis](arbitrary-sat-expansion.md)
distinguishes whole-input classification from splitting a formula into parts,
reviews Schaefer's language classification, heterogeneous/scattered backdoors,
component-backdoor depth and representation-specific compilation lower bounds.
Class recognition, discovery, recombination and persistent maintenance are part
of the cost. No uniformly cheap complete cover of arbitrary SAT is established.

An explicit linear-size indicator construction transforms any CNF into a
conjunction of positive dual-Horn and negative Horn/2-CNF parts. Their interaction
still encodes the original SAT problem. The retained diagnostic checks complete
assignment correspondence on **460 formulas** (224 SAT / 236 UNSAT), including
all 256 two-variable formulas formed from nonempty nontautological clauses. It
also reproduces Gaspers et al.'s published heterogeneous-backdoor example: one
variable yields Horn or 2-CNF residuals, while homogeneous searches through size
two can fail. The search counts and failures remain in
`experiments/results/sat-class-decomposition/diagnostic.json`; the enumerator is
a small diagnostic, not an efficient backdoor detector or native solver path.

**Next priority:** checked Horn/dual-Horn/2-CNF leaves and a bounded recursive
planner alternating variable splits with independent component splits, with
exact residual reuse and the existing complete checked fallback. Then add
source-linked dependency/invalidation and OR/AND recomposition proofs, matched
hard connected workloads, structural-change edits and cold replay. Optimize
total new work, not only the number of backdoor variables. Affine constructors
remain potential leaves; preserve their proofs and all earlier evidence.

For a supplied strong backdoor of size k the branch bound is 2^k times polynomial
leaf work; for a suitable supplied component-backdoor tree, depth d can replace
global size in published evaluation bounds. Neither k nor d is uniformly small
on all SAT inputs, and finding the structure is charged separately. A universal
polynomial acquisition/expansion/query result would prove P=NP; this logical
implication does not establish that such a result is impossible. Current runtime,
Lean theorems and manuscript are unchanged by this research checkpoint.


## 2026-11-08: distinguish prepared expansion from an ordinary SAT algorithm

The user's clarification changes how the previous implication should be read:
cheap expansion and queries after expensive size-dependent preparation do not
establish ordinary P=NP. The analysis and manuscript now explicitly separate
acquisition C_prep(n), incremental work U(H, delta), queries Q(H, x), and storage.
The uniform-expansion corollary retains its stronger hypotheses: one fixed finite
seed, uniformly polynomial total work, and coverage of all lengths. A very large
fixed seed is an asymptotic constant; a supplied family of states growing with n
can hide nonpolynomial acquisition and must be accounted for separately.

The oracle section now includes Baker-Gill-Solovay's PSPACE-complete example:
P^A=NP^A=PSPACE, with the polynomial-space simulation argument. This genuine
oracle model leaves internal answer computation uncharged. It neither supplies
a finite constructed archive nor proves that our acquired state has the same
power. No ordinary or relativized class collapse is claimed for our solver.

**Working objective:** minimize additional work given acquired state, record its
acquisition and memory cost, and prove precisely which future changes its stored
summaries support. The heterogeneous decomposition priorities remain; their
future bounds should expose the prepared-state invariant and new residual work.
No general polynomial expansion guarantee has been demonstrated. This checkpoint
changes exposition only; executable code, Lean proofs and stored solver results
remain unchanged.

Validation: checked the oracle argument against the original 1975 paper's
Theorem 2; all 38 existing manuscript proof blocks are byte-for-byte unchanged
and all 147 labels are unique. Two LaTeX passes produce a 76-page PDF with no
warnings or overfull/underfull boxes. Revised pages 6/18 and adjoining pages 7/19
were rendered and visually inspected. `git diff --check` passes. No solver or
Lean tests were rerun for this exposition-only change.


## 2026-11-08: executable arbitrary-CNF residual candidate

The user asks to pursue a uniform polynomial solution for every CNF, charging
all acquisition. [The candidate analysis](residual-candidate.md) records a new
research implementation with explicit Horn/dual-Horn/2-CNF leaves, independent
components, variable branching, and persistent exact residual reuse. Full CNF
keys avoid a collision-free-hash assumption. SAT models and UNSAT dependency
certificates are checked in Python on acquisition and cold replay; this is not
yet part of the production solver's Lean trust boundary.

All 217 Python tests pass. Lean proves conditioning and branch recomposition;
the audit passes 4,061 declarations / 1,924 theorems without additional axioms.
The first experiment retains 156 matched decisions over 26 inputs, including
warm and cold replay, plus all 104 result archives. Thirty-two repeated
components need 6 expansions versus 161 without search reuse. Seven pigeons
into six holes need 416 versus 1,235. Cold replay creates no new nodes but checks
all 416 negative-certificate nodes. All prior solver results remain untouched.

The residual count still lacks a uniform polynomial bound. The immediate
structural opportunity is matching: the pigeonhole family should be recognized
and solved with a matching/Hall certificate rather than residual branching.
This is established tractable-class reasoning, with a direct CMP-SAT precedent
in Lenchner's 2019 preprint, and does not cover every CNF. Initial evidence,
including cases where decomposition adds work, is preserved for comparison.


## 2026-11-08: matching structure replaces a growing search family

Implemented the next structural leaf in the experimental CNF candidate. It
recognizes disjoint positive choices and complete negative exclusion cliques,
solves the resulting bipartite matching problem, and independently checks a
source witness or Hall deficiency certificate. Missing clique edges and
overlapping choices are rejected; satisfiable counterexamples to these two
unsound relaxations are retained. This is established matching/CMP-SAT reasoning,
not a claimed novel class or a uniform solution of all CNFs.

[Matched evidence](../experiments/results/cnf-matching/README.md) contains 153
decisions over 39 inputs. Nine pigeons / eight holes drop from 5,191 acquired
residuals and 17,290,081 logical bytes to one residual and 6,208 bytes. Cold
checking drops to one source/Hall node. Matching-only scaling reaches 48 holes,
still with one node but 1,496,174 retained logical bytes, illustrating that the
source cost grows. Four near-miss cases and all previous difficult cases remain.
All 104 earlier archives reload with unchanged row digests and no new expansions.
Every new result/certificate is retained in 75 additional compressed snapshots.

All 220 Python tests pass. Lean checks conditioning, branch recomposition and the
cardinality obstruction, with an audit of 4,062 declarations / 1,925 theorems.
The manuscript adds the full mathematical matching reduction and proof. The
Python recognizer/checker is still outside the production Lean trust boundary;
production code and its result archive are not targeted by these experiments.

**Next mathematical priority:** positive-clause overlap. Replacing each SAT
variable by complementary indicators embeds arbitrary CNF into overlapping
positive clauses with disjoint negative pairs. Thus the resource graph can be
simple while shared satisfaction carries the full problem. Investigate removal
of redundant/laminar choices, overlap backdoors, and exact summaries of shared
satisfaction. A k-variable overlap backdoor can still require 2^k branches;
neither a universally small k nor a polynomial number of residuals is proved.
Keep acquisition, recognition, intermediate representation and cold checking in
the bound. Native source-linked certification is a separate implementation gap.

Final validation: all 38 previous manuscript proof blocks are unchanged and one
matching proof is added. The 78-page PDF builds without warnings and revised
pages 70/71, adjoining page 72, and bibliography pages 76/77 were rendered and
visually checked. The prior experiment's artifacts are unchanged; current
candidate/driver fingerprints match their report. The separate cold-baseline
audit confirms 5,191 checked nodes at eight holes, with zero new expansions.


## 2026-11-08: redundant positive expansion reuses a checked minimal core

Implemented the next recorded opportunity: positive-clause subsumption exposes
matching leaves hidden by redundant overlap and makes equivalent source versions
reuse one exact normalized core. Every deletion has a retained subset witness.
Negative source wrappers check those witnesses and the exact negative child;
positive sources retain full checked models. Laminar positive families have
disjoint minimal members, so complete negative exclusion cliques retain a
polynomial matching construction after this charged preprocessing. Arbitrary
irreducible overlap remains outside that guarantee.

[The matched experiment](../experiments/results/cnf-subsumption/README.md) retains
39 static inputs and four nine-query histories: 450 correct decisions and 86
compressed archives. A laminar eight-hole input drops from 23 nodes / 201,735
logical bytes to two nodes / 17,538 bytes. More substantially, eight redundant
extensions of an acquired eight-hole core drop from 23,046 total new nodes and
84,546,940 retained logical bytes to nine nodes and 82,514 bytes. After the first
query, each addition creates one source record and performs no new core search.
Final cold negative replay checks two nodes instead of 5,359. All 179 previously
preserved candidate archives still check with unchanged row digests and no new
expansions; the production result archive was not targeted.

All 224 Python tests pass. Added tests exhaustively preserve all models of 2,048
small positive families, check warm/cold SAT and UNSAT core reuse, and reject
invalid/circular containment witnesses and changed dependencies. Lean adds three
semantic lemmas for containment, covered-core models and witnessed extension;
the audit passes 4,066 declarations / 1,928 theorems. This does not bring the
Python checker or its database inside the native Lean trust boundary.

**Retained limitation and next expansion priorities:** the new pass still scans
and normalizes each full source, rebuilds the containment index, and copies the
source and core key into its new record. An unchanged core can therefore coexist
with quadratic cumulative source-copy payload over linearly growing histories.
Investigate an incremental retained-clause index and persistent source deltas,
with explicit invalidation when witnesses or conflicts change. Also evaluate a
cost policy: seeded case 20 increases from 12 to 20 nodes and 12,029 to 18,637
bytes because reduction wrappers do not repay their cost. Three other controls
also grow, and these unsuccessful comparisons are preserved. A useful next gate
would require an exposed tractable leaf or a cached core before paying for an
additional reduction node; that policy is not implemented or proved optimal.

Subsumption is published preprocessing (Een and Biere, SAT 2005), not a new
general SAT algorithm. Worst-case discovery still has O(p^2 w) containment probes
plus source scanning, sorting, index and bit costs. No universal minimum-expansion
or polynomial arbitrary-SAT bound follows from the successful restricted stream.

Manuscript checkpoint: Proposition 12.28 gives the model-preserving minimal-core
reduction, the laminar matching corollary and the witnessed-extension invariant.
All 39 preceding proof blocks are unchanged; there are now 40 proof blocks and
151 unique labels. The 79-page PDF builds without warnings or overfull/underfull
boxes. Revised pages 71/72, adjoining page 73 and bibliography page 76 were
rendered and visually inspected. All 86 new compressed snapshots decompress to
their recorded hashes, and candidate/driver fingerprints match the report.
Code, Lean, data and research documentation were committed and pushed in
`1d3b2eb`; the manuscript and this final validation follow in a separate checkpoint.


## 2026-11-08: persistent witnessed deltas remove repeated source copies

Implemented `experiments/cnf_positive_history.py`, a separate prepared-state
interface that stores a solved base once, retains its positive-clause index,
and appends clause deltas with checked subset witnesses and integer parent/base
references. The exact base-plus-delta source can be reconstructed on demand.
Warm append avoids full-source normalization, index reconstruction, full core-key
copying and solver expansion. Parent versions are archive-local checked handles;
they do not identify arbitrary externally supplied full CNFs. Unsupported edits
require a newly acquired base, while older versions and results remain immutable.

[The matched comparison](../experiments/results/cnf-positive-history/README.md)
preserves 24 histories / 4,848 decisions / 48 compressed archives. At 16 holes
and 128 redundant additions, retained logical payload drops from 10,957,771 to
118,668 bytes and SQLite size from 15,130,624 to 237,568 bytes. At four holes and
512 additions, logical payload drops from 6,034,220 to 45,043 bytes. The last
append reads its new clause, performs four containment probes, writes one small
delta and invokes no residual-solver operation. All 265 preceding candidate
archives replay with unchanged row digests and no new expansions.

All 230 Python tests pass, including exact reconstructed sources, SAT/UNSAT
witness behavior, sparse variable names, forks, duplicate operations, changed
constraints, cold corruption checks and a 1,200-step iterative cold replay.
Lean proves `positive_history_models`; its audit passes 4,067 declarations /
1,929 theorem declarations. This semantic proof does not verify the Python
implementation, its SQL identity protocol or its machine costs. The new API is
separate from the production solver, whose result archive was not targeted.

**Remaining costs and preserved failures:** cold query validates the base and
all required ancestor deltas; the 512-addition history checks 513 records. Full
source export remains charged, and novel constraints materialize and solve a
fresh base. Thirty-two new units grow logical storage from the old interface's
30,657 bytes to 57,756. Repeating one identical clause on successive parents uses
11,742 bytes versus 1,410 after old CNF normalization; repeating the identical
parent/operation reuses a version but still pays table overhead. The mixed
history also loses slightly. These cases remain in the archived comparison.
SAT timings expose the different witness-output interfaces; the old solver
returns a model on every call, while the history API exports it separately.

**Next concrete reuse patterns:** compress repeated event runs or separate
semantic no-op versions from exact event provenance; share unchanged source
structure when a new base is required; and consider the simpler monotone rule
for adding clauses to an already checked UNSAT base. The current uniform
positive-subset protocol does not exploit that negative-only shortcut. The
earlier subsumption policy regressions, cold-validation cost and arbitrary
irreducible positive overlap remain open. None of these measurements proves
minimum expansion work for every case or polynomial acquisition for all SAT.

Final validation: Proposition 12.29 states the history invariant and retained-bit
bound. All 40 previous manuscript proof blocks are unchanged; there are now
41 proofs and 153 unique labels. The 80-page PDF builds without warnings or
overfull/underfull boxes; pages 72/73 and adjoining page 74 were rendered and
visually inspected. All 48 new snapshots decompress to their recorded hashes,
and source fingerprints match the report. An independent gzip replay records
the final handles for all 24 history snapshots and checks their exact source
recipes, answers and unchanged row digests in `history-replay.json`. Code,
formalization and comparison evidence were committed and pushed in `fa7feb6`;
the manuscript and final validation follow in the next checkpoint.


## 2026-11-08: arbitrary UNSAT additions and surviving SAT assignments

Implemented two further reuse cases in the separate CNF history prototype.
`append_decision` accepts any well-formed signed clause, including an empty one,
over a checked UNSAT base. For a SAT base it accepts exactly when the fixed
stored assignment satisfies the new clause, treating missing variables as false.
The latter preserves a witness and verdict, not every base model. A failed model
supplies no UNSAT conclusion and writes no version. Fresh solving remains the
fallback. The old positive-subset API and its persisted records remain supported.

Both new record kinds retain exact clauses and parent/base references. Cold
replay checks every required ancestor and its rule against the checked base.
Warm accepted additions avoid subset discovery and residual solving. Syntax,
model probes where applicable, serialization, SQL indexing, preparation, source
export and cold replay remain charged. Deletion/replacement and externally
mutating already checked cached rows are outside the append-only interface.

[The matched comparison](../experiments/results/cnf-decision-history/README.md)
retains 22 histories, 3,894 correct decisions and 66 compressed archives. For
size-16 SAT and 128 compatible signed additions, the preceding history interface
acquires 129 bases and retains 15,195,873 logical bytes; the new interface keeps
one base and 99,170 bytes. Summed base-plus-update time falls from 3.611 to
0.04691 seconds in single samples. The full-source comparator uses 9,235,556
bytes and 2.781 seconds. Size-16 UNSAT arbitrary additions fall from 3,670,847
to 109,468 bytes and 0.71682 to 0.05710 seconds versus positive-only history.
Actual SQLite sizes are recorded separately; these are not peak-RSS results.

Preserved counterexamples matter: repeated signed clauses use 8,926 bytes versus
1,396 with full-source deduplication; 32 fresh positive units still force 32
fallback acquisitions and 58,812 bytes versus 30,657. A failed model that remains
SAT and a true SAT-to-UNSAT transition both need one fresh base, then reuse it
for 31 additions. Size-16 UNSAT cold replay takes 10.13 ms versus 5.94 ms for the
preceding history's isolated final base and 1.57 ms for the full-source cache,
whose input now contains an empty clause. No universal runtime gain follows.

All 235 Python tests pass, including 320 enumerated base/clause combinations,
model-set shrinkage, sparse assignments, failed-model non-refutation, mixed
legacy/new records, malformed and forged deltas, and 1,200-step UNSAT replay.
Lean adds four semantic lemmas for fixed-model and refuted histories; its audit
passes 4,071 declarations / 1,933 theorem declarations with standard axioms only.
These proofs do not verify Python, SQL or machine costs. All 313 earlier
archives replay unchanged with no new expansions. Every new compressed archive
was separately reloaded and checked against its exact source recipe and row
hash. The production solver and result archive were not targeted.

**Next expansion priorities:** (1) allow small checked model repairs and share
source structure across new bases; (2) compress repeated event provenance while
preserving old version identities; (3) reduce cold history validation and avoid
unused eager positive-index preparation. In particular, a positive unit on a
genuinely fresh variable can extend a model, but absence from the base model
does not prove freshness: previous deltas may constrain it. An occurrence or
other explicit invalidation invariant is required. General irreducible positive
overlap and unrestricted polynomial construction remain open. The new cases
reuse already acquired answers; they do not bound acquiring every CNF.

Manuscript validation: Section 12.38 and Proposition 12.30 now state both rules,
prove their distinct invariants, and report the comparison and losses. All 41
previous proof blocks remain unchanged; the paper now has 42 proofs and 155
unique labels. Two LaTeX passes produce an 81-page PDF without warnings or
box overflows/underflows. Pages 73/74 and adjoining page 75 were rendered and
visually inspected. The implementation, proof and experiment checkpoint was
committed and pushed as `8ad5f8e`; this manuscript update follows separately.


## 2026-11-08: checked pure-literal model repair without fresh base copies

Implemented the next recorded case in `experiments/cnf_repair_history.py`.
If the current assignment fails a new clause, it may change one literal to true
only when its opposite occurs nowhere in the complete parent source. This
protects all old clauses, handles both fresh and existing pure variables, and
retains fallback when the sufficient condition fails. A persistent binary trie
shares positive/negative occurrence flags and assignment values across versions.
It indexes exact original clauses and every delta, including tautologies and
prior non-repair additions. Older branches and models remain unchanged.

Cold verification reconstructs the derived index from checked source records and
validates each repair. The new reader accepts older history formats; old readers
reject new repair records. The preceding base class gained a certificate hook
with unchanged legacy behavior. Production code and its result archive remain
untouched. The Python trie/SQL checker is outside the Lean trust boundary.

[The comparison](../experiments/results/cnf-repair-history/README.md) preserves
20 histories, 3,924 correct decisions and 60 archives. At size-16 SAT with 128
fresh positive units, the preceding decision history acquires 129 bases and
retains 12,020,154 logical bytes. Repair keeps one base and 100,706 bytes; summed
acquisition/update time falls from 2.61853 to 0.07326 seconds. SQLite size falls
from 21,618,688 to 208,896 bytes. The last append uses 88 trie-node visits,
allocates 28 nodes across its assignment/support updates, and performs no solver
work. The final version set shares 2,048 distinct trie nodes. Separate tracing
reports peak Python allocations of 77,265,863 versus 1,740,168 bytes; it excludes
native SQLite allocations and total process RSS. Timings are single samples.

The accepted warm operation uses O((d+1)b) trie-node work for d literals and
b-bit identifiers, plus syntax, bit serialization, integer, dictionary and SQL
costs. Whole-parent scans/model copies are absent. Preparation and cold history
checking remain charged; size-16 cold query takes 13.20 ms versus 7.58 ms for
the preceding final fresh base. Exact source export and sparse witness output
are optional and explicitly measured. No unrestricted acquisition bound follows.

Preserved losses identify further structure. A parent containing (1) and
(-x or 1) permits changing x, but the pure-literal test rejects it. Both histories
fall back 32 times in this control, and repair adds overhead. Repeated units
retain 10,719 bytes versus 1,393 with full-source deduplication. Already-compatible
additions raise peak traced allocations from 108,869 to 249,217 bytes. Thirty-two
variables near 2^1024 create 32,801 trie nodes and take 38.73 ms versus 33.18 ms
for decision fallback; cold replay takes 25.29 ms versus 0.22 ms. These are
retained counterexamples to universal speedup, not omitted failures.

All 242 Python tests pass. They include 168 enumerated base/clause combinations,
300 seeded branching proposals, sparse 1,201-bit index keys, 128-repair cold
replay, exact source/witness checks, old API compatibility and forged-record
rejection. A base tautology preserving the normalized solver key still changes
support and correctly invalidates a claimed repair. Lean proves the signed
occurrence update and pure-repair preservation/extension rules; the axiom audit
passes 4,079 declarations / 1,939 theorem declarations. It does not verify the
integer parser, trie, persistence or machine costs. All 379 preceding archives
replay without row changes or new expansions. Every new compressed archive was
independently reloaded and matched to its exact source and row hash.

**Next bottlenecks and recognition requirements:**
1. Check affected opposite-sign clauses (or retain true-literal counts) to allow
   safe flips that purity rejects. Every affected prior occurrence must be found;
   a small affected set is an explicit condition, not an arbitrary-SAT guarantee.
2. Compress long unary trie paths for sparse identifiers. Exact identifiers and
   source serialization still cost their bit length. The current map uses one
   node per bit on an updated path.
3. Prepare the repair index lazily or select it by measured reuse. Compatible
   streams should not always pay eager support maintenance; activation/restart
   must still reconstruct and charge all earlier constraints.
4. Share fresh-base source structure and compress repeated provenance without
   losing historical versions. Repair rejection still triggers copied bases.
General irreducible overlap, arbitrary model repair and uniformly polynomial
construction for every CNF remain open.

Manuscript validation: Section 12.39 and Proposition 12.31 now give the repair
rule, proof, shared-index accounting, allocation measurements and counterexamples.
All 42 earlier proof blocks remain unchanged; the draft has 43 proof blocks and
157 unique labels. The 82-page PDF builds without warnings or box overflows or
underflows; pages 74/75 and adjoining page 76 were rendered and visually checked.
Code, proofs, all measurements and earlier-archive verification were committed
and pushed as `5c9f5ea`; the manuscript checkpoint follows separately.

## 2026-11-08: cost-directed priorities across SAT categories

The hourly investigation now starts from the compact
[structural-reuse cost map](structural-reuse-priorities.md). Its prompt was
shortened to identify the dominant remaining runtime or memory cost, choose one
gap with the highest credible total saving, compare on matched workloads and
update the ranking. The hourly schedule, target chat and notification intent
are unchanged.

[Five new diagnostic profiles](evidence/2026-11-08/reuse-cost-profile/README.md)
retain fresh archives without changing any preceding results. They distinguish
reacquisition after failed repair, residual search, sparse-identifier index cost
and persistence on already-cheap updates. In their respective instrumented
controls, trie lookup/update accounts for about 62% of exclusive time and SQLite
execution/transaction-context exit for about 87%. These are separate workloads,
not a global phase breakdown or uninstrumented speed claim.

The immediate next experiment is checked nonpure single-variable repair with
versioned affected-clause counts. The existing blocked-but-SAT control still
acquires 32 new bases unnecessarily. Broader opportunities are retained
propagation/class state, mixed-class boundary summaries, and shared source/proof
dependencies across class transitions. The cost map gives their recognition and
invalidation conditions, resource limitations and a workload-driven ranking.

This checkpoint adds analysis and profiling evidence only. General repair,
small interfaces for every CNF, compact closure and uniformly polynomial
acquisition remain open. The Python prototype is still outside the Lean
implementation trust boundary; no manuscript theorem was strengthened here.
Cold validation checks all 356 versions and 58 residuals in the five new archives
with no new expansions or database-byte changes. New local documentation links
resolve; the diagnostic runner refuses an existing output directory. No solver
code changed, so the prior full solver test/audit results are not claimed as
newly rerun checks.

## 2026-11-08: checked affected-clause repairs avoid copied fresh bases

Implemented the top cost-map experiment in `experiments/cnf_affected_history.py`.
The new interface keeps exact distinct-true-literal counts and variable-to-clause
occurrence lists in immutable versioned tries. It accepts a single-variable
change only when all affected old counts remain positive. Tautologies have zero
net count change; duplicate literals do not create false protection. Candidate
occurrence visits are budgeted. Rejection supplies no verdict and retains
ordinary solving as fallback. Cold checking rebuilds all derived indexes from
exact checked history, with no trusted persisted count or affected-clause list.

The [matched experiment](../experiments/results/cnf-affected-history/README.md)
retains 35 cases, 7,230 correct acquisition/update/replay decisions and 70 archives.
The original 32-fallback control now has zero fallbacks. On matching SAT size 16
with 128 protected flips, bases fall from 129 to one, operation time from 3.47813
to 0.14730 s and logical archive payload from 12,460,337 to 158,332 bytes. Separate
tracing reports peak Python allocations of 86,261,287 versus 2,837,728 bytes,
excluding native SQLite and process RSS. The last update checks one old clause
in discovery and again in verification; it performs 202 trie-node visits and
allocates 66 trie nodes without residual solving. At 512 protected flips the
operation sum falls from 5.05929 to 0.32684 s. These are single synthetic samples.

Losses are retained: compatible streams roughly double traced index allocations;
sparse-ID paths also nearly double peak allocations; cold replay is more costly.
A single flip affecting 4,096 old clauses avoids fallback but takes 125.48 ms
versus 109.99 ms because index preparation dominates. Budget exhaustion and a
coordinated-flip example still require fresh acquisition. A separate first
screening run overlapped with tests/builds and is retained without being used
for primary timing claims.

All 249 Python tests pass, including exact index reconstruction, 294 base/clause
combinations, 400 seeded branching proposals, forged records and old/new format
checks. Lean proves `affected_repair_preserves` and `affected_repair_extension`;
the axiom audit passes 4,081 declarations / 1,941 theorem declarations. These
semantic proofs do not verify the Python count maps or SQL. All 439 preceding
benchmark archives replay without new expansion or changed rows. Independent
decompression/replay checks every version and residual in the new primary and
screening archives, with exact source/witness checks and unchanged database bytes.

**Next target:** selectively activate the stronger index, keeping the pure path
for streams that need no nonpure repair. Account for first activation, all later
constraint maintenance and cold reconstruction. The current node-operation
bound is O((d+1)b + (k+r+1) log(m+2)), for d new literals, b-bit variable IDs,
m parent clauses, k discovery occurrence visits and r affected old clauses.
r can equal m. Coordinated repairs, general small affected sets, shared fresh
base sources and unrestricted polynomial acquisition remain open.

Manuscript Section 12.40 / Proposition 12.32 states the distinct-literal count
identity and its proof, the versioned index accounting, measurements and losses.
All 43 previous proof blocks remain unchanged; there are now 44 proofs and 159
unique labels. The 84-page PDF builds without LaTeX warnings or box diagnostics;
pages 75--78 were rendered and visually reviewed. Both new experiment runs were
independently replayed: 140 archives, 14,180 historical versions and 2,568 residual
records, with zero new expansions and unchanged database bytes.
The implementation, proofs, tests and preserved experiment checkpoint was
committed and pushed as `15e9c9e`; this manuscript and priority update follows.

## 2026-11-08: structural reuse across SAT categories, after single-variable repair

The [new diagnostic](../experiments/results/structured-repair-gaps/README.md)
finds 240 single-variable repair misses across 12 equivalence, parity and matching
histories. Every new unit has an independently checked coordinated repair; no
rejection exhausts the discovery budget. Equivalence needs a whole block flip,
parity needs two flips, and the matching control needs a four-indicator swap.
These supplied transformations are not yet a discovered/certified repair API.
The generator knows the structure, and full-source checking of supplied moves
is diagnostic validation rather than a measured optimized path.

For 32 equivalence blocks of 32 variables, the current implementation retains
33 bases and 3,792,631 logical bytes, taking 2.697 s for base preparation and the
32 rejected-update/fallback operations. The matching control with 32 independent
4-by-4 blocks retains 33 bases / 2,267,324 bytes and takes 0.946 s. Single samples
show repeated acquisition on these constructed easy families; they do not measure
the speed of a replacement or characterize typical SAT workloads.

The cost map now promotes checked simultaneous equivalence-block repair as the
next research experiment. Shared component source, witnesses and typed states
are the enabling architecture. Current positive residual records flatten models
and discard the solver's matching/implication state; new bases still copy their
source. Several class views can describe the same component, so class labels
should not define storage identity. Mixed-component boundary summaries and
structure-aware branching remain the larger search-growth opportunity.

Simultaneous repair must accumulate clause-count changes before checking: an
intermediate assignment may be invalid while the final assignment is valid.
Internal preservation does not keep old per-clause count indexes current for
free. Maintain them or explicitly invalidate/reconstruct them, and check every
affected external constraint and earlier addition. Selective index activation
remains a smaller engineering fix for the already measured allocation losses.

The diagnostic retains 12 new archives, exact sources, model-dependent additions,
proposed moves and source fingerprints. Independent decompression/replay checks
all historical versions, candidate moves and residual records without new
expansion or changed database bytes. Solver code and manuscript claims are
unchanged; the existing full test/audit results were not rerun for this analysis.
The established heterogeneous-backdoor and component-depth literature remains
the basis for the proposed mixed-class search direction, not a novelty claim.

## 2026-11-08: checked simultaneous equivalence repair

Implemented `EquivalenceRepairHistory`, with lazy per-base discovery of connected
variables in complementary binary clause pairs. The existing single-variable
rule runs first. A generic joint record stores the exact addition and changed
variables. Its independent checker aggregates all affected count changes before
checking the final assignment, including external clauses and earlier additions.
Old assignment/count roots remain immutable, and cold replay reconstructs all
indexes without trusting discovery or stored derived counts. New equivalences in
deltas and nonpaired implication SCCs are intentionally not discovered.

The [matched study](../experiments/results/cnf-equivalence-history/README.md)
removes all 120 unsigned-chain misses plus 32 signed-chain misses. At 32 blocks
of width 32, summed acquisition/update time falls from 2.46892 to 0.06676 s,
logical storage from 3,792,631 to 98,663 bytes, SQLite from 6,668,288 to 204,800
bytes, and peak separately traced Python allocations from 45,575,163 to 1,925,402
bytes. Bases fall from 33 to one. These are synthetic samples; tracing excludes
native SQLite and process RSS. Cold final query grows from 40.88 to 44.42 ms;
repeating the last known update after restart takes 88.32 versus 45.98 ms,
including reconstruction and fresh proposal recognition.

All 23 histories retain 46 archives, 1,144 historical versions and 869 residuals,
checked without byte changes or fresh expansion. Another 82 prior archives
(7,342 versions / 1,782 residuals) replay unchanged. The 255-test Python suite
passes, including randomized branches, exact count/posting recomputation,
couplings, signed/repeated changes, contradictory and budgeted cases, and forged
records. Lean adds `joint_repair_preserves` and `joint_repair_extension`; the full
build and axiom audit pass (4,083 declarations / 1,943 theorem declarations).
These are semantic protection lemmas, not a refinement of Python or SQL.
The verified implementation/evidence checkpoint is `12ae27a`, pushed to main.

The initial comparison is preserved separately: complementing the unsigned input
recipe produced signed additions already true under the solver's chosen model.
The corrected control explicitly forces 32 signed repairs. Its run also measures
cold resumption separately from querying the final version. No timing samples
from the two runs are pooled.

Remaining costs are explicit. A 1,024-variable block exceeds the default
4,096-visit discovery budget and still falls back. Every block variable and
internal posting is visited; zero-net counts avoid writes, not discovery/check
visits. Move lists are repeated in durable records, and assignments are not
represented by one group bit. Compatible and scalar-only histories never build
the new block index, although their older affected-clause indexes remain eager.
The resource-bounds document records recognition, checking, retained paths,
temporary aggregation, serialization and cold costs separately.

**Next target:** matching-state reuse and discovered alternating moves through
the joint checker. The 32-block, 4-choice control still requires 32 fallbacks,
retains 33 bases / 2,267,324 logical bytes, and takes 1.002 s on the new path
versus 0.934 s on the scalar baseline. Parity remains another missed adapter.
Both need prior-addition/external-constraint checks and explicit budgets; the
generic checker alone provides no procedure for finding a valid move. Shared
source/component state across genuine fallback remains open. No unrestricted
polynomial expansion or acquisition claim follows.

The manuscript now contains Section 12.41 and Proposition 12.33, with the joint
count identity, proof, discovery restrictions, operation/storage bounds and
matched gains and losses. All 44 earlier proof blocks are preserved, with one
new proof and 161 unique labels. `latexmk` builds the 85-page PDF without final
warnings or overfull/underfull boxes; pages 76--79 were rendered and inspected.

## 2026-11-08: retained matching state and alternating proposals

Implemented `MatchingRepairHistory` as an optional layer over the existing joint
checker. After scalar/equivalence failure, it recognizes a strict whole matching
base, retains selected choice/resource endpoints and earlier unit pins in shared
tries, and searches for an alternating path to satisfy the requested literal.
Accepted moves use the existing `append-joint` format and independently check
every affected original or added clause. Warm updates maintain only changed
endpoints; old versions remain immutable. Cold final checking requires no graph
state, and the previous equivalence reader accepts matching-generated records.

The [matched study](../experiments/results/cnf-matching-history/README.md) removes
all 80 matching misses from the prior diagnostic and avoids 161 acquisitions
across the enlarged 37-case matrix. At 32 four-choice blocks, operation time
falls from 0.92416 to 0.04882 s, logical payload from 2,267,324 to 50,257 bytes,
SQLite from 3,973,120 to 110,592 bytes, and separately traced peak Python
allocations from 24,840,875 to 1,192,534 bytes. Bases fall from 33 to one.
At 32 eight-choice blocks, time falls from 8.30345 to 0.25308 s and logical
payload from 20,331,832 to 424,089 bytes. Input sizes, graph recognition, failed
proposals, state maintenance, checking, serialization and persistence are charged;
tracing excludes native SQLite and RSS, and timings are single synthetic samples.

Cold final replay for four-choice blocks increases from 17.93 to 20.25 ms.
Repeating the last known update after restart takes 40.03 versus 23.46 ms,
including graph/view reconstruction; both archives already contain its result.
The last warm move scans two graph edges, changes four indicators, visits 16
postings in discovery and again in checking, updates four matching endpoints
and allocates 182 trie nodes. It performs no base scan or new residual solve.
A 64-choice cycle changes 128 indicators and visits 256 postings per pass, so a
unit addition can still affect the whole component.

All 261 Python tests pass. New tests include 400 branching unit histories
checked against all permutation models of a three-choice square instance, exact
count/endpoint/pin reconstruction, long cycles, free resources, old versions,
budget failure and cold/older-reader compatibility. All 74 new archives (1,414
versions / 608 residuals) and 58 prior archives (1,396 versions / 1,367 residuals)
replay with unchanged bytes and zero new expansion. The verified implementation
and evidence are committed/pushed as `5181faf`. The Lean build reuses the
existing joint semantic lemmas; its audit passes unchanged at 4,083 declarations
and 1,943 theorem declarations. No new graph/index/runtime refinement is claimed.

Retained failures are informative. Search tries one path per literal. A non-unit
coupling can defeat it while a longer valid cycle exists; a unit prohibition
guides search around the corresponding edge successfully. A disjoint unrelated
equivalence component prevents whole-base matching recognition. Parallel
indicators, unused negative-only indicators and new graph structure are also
outside recognition. With spare resources, a valid model can select extra
indicators in one choice; that invalidates the optional matching view, and
discarding an extra indicator may violate an earlier unit. All such misses
remain satisfiable controls or explicitly checked contradictions, not inferred
UNSAT verdicts from proposal failure.

The literature check confirms this is established matching machinery:
[Régin (1994), pp. 364–366](https://cdn.aaai.org/AAAI/1994/AAAI94-055.pdf) uses
alternating paths/cycles and retains a known matching while propagating edge
deletions. The manuscript's Section 12.42 cites it and distinguishes our
persistent, full-source-checked integration from that prior algorithm and its
complete filtering. All 45 previous proof blocks are preserved, with 162 unique
labels. The 87-page PDF builds without final warnings or box errors; changed
pages 78--80 and the added reference link on page 86 were visually inspected.

**Next measured target:** the 1,024-variable equivalence-block budget rejection
still takes 0.786 s, including about 0.741 s after preparation. Evaluate a charged,
structure-aware budget escalation or smaller checking representation against
fallback, retaining adverse high-degree controls. Do not raise all search budgets
without a total-cost comparison. Parity remains the largest measured repeated
miss stream (32 fallbacks / 0.170 s / 326,256 bytes). Preparation dominates the
successful larger matching stream (206.58 of 253.08 ms), so profile it before
optimizing its cheap path search. Component extraction and coupling-guided path
search have credible cross-category potential but need scaled evidence. General
SAT acquisition, closure size and uniform polynomial expansion remain open.

## 2026-11-08: bounded retry and the next measured bottleneck

Implemented optional `BudgetedRepairHistory` over the unchanged matching engine.
After ordinary failure it may retry only the first exhausted recognized base
block, with min(32,768, 8*q) variable/posting visits, at most 8,192 variables and
64-bit identifiers by default. It retains a reference to the existing tuple,
charges all failed work and uses the unchanged independent joint checker and
archive format. Discovery exhaustion never implies UNSAT. Completed rejections,
matching paths and unrecognized structures do not receive this retry.

The preserved [screening](../experiments/results/cnf-budget-screening/README.md)
motivated a [27-case, three-policy comparison](../experiments/results/cnf-budgeted-history/README.md).
At 1,024 variables, total operation time falls from 0.78490 to 0.05932 s,
expansion from 739.17 to 13.29 ms, logical payload from 189,168 to 99,129 bytes,
SQLite from 356,352 to 196,608 bytes and peak traced Python allocations from
3,071,073 to 1,741,448 bytes. Bases fall from two to one. At 4,096 variables,
total time falls from 11.88170 to 0.27261 s and expansion from 11.67323 to
0.05553 s. These are single synthetic timings, with allocation tracing separate.
The report charges preparation, failed discovery, checking, maintenance,
serialization, persistence and fallback; input assembly and audits are separate.

The simple alternative is important: globally raising the budget to 32,768
is slightly faster on the successful chains and also solves dense controls that
the targeted cap rejects. On 1,024 variables with 8,192 tautologies, the targeted
policy still takes 0.89334 s with fallback, versus 0.11656 s for the raised
policy. No expected-cost superiority or optimal budget claim is supported.
The pinned 2,048-variable conflict pays 40.36 rather than 31.01 ms expansion
because the extra check correctly rejects it. Cold final replay on the plain
1,024-variable chain increases from 43.48 to 45.25 ms. The global/targeted
tradeoff, caps and failures are retained, not hidden by the successful examples.

All 268 Python tests pass, including 120 random branching additions, old-version
count reconstruction, limits, disabled discovery, conflicts, rejected-operation
immutability and older-reader replay. All 81 new archives (582 versions / 357
residuals) and 74 preceding matching archives (1,414 versions / 608 residuals)
validate through the previous matching reader with unchanged bytes and zero
new expansions. The proposal policy adds no formal theorem: the existing Lean
joint semantic rules remain the boundary; Python indexes and resource accounting
are not refined by them. Source fingerprints match the recorded experiment.

**Next target:** repeated-scan unit propagation. The new pinned 2,048-variable
control spends 2.67 s in preparation. A separate in-memory cProfile run attributes
8.778 of 8.939 instrumented seconds (about 98%) to `propagate` and its callees,
with 16,779,261 charged literal visits for 8,189 source occurrences. Implement
an occurrence-driven queue with independently checked reasons, charging setup,
queue memory, conflicting/easy controls, fallback and cold replay. Preserve old
certificates; no speedup is yet claimed for this unimplemented change. Thereafter
address inert/dense postings and cost estimation, parity-preserving repair,
mixed-component extraction and coupling-guided alternative paths. General SAT
branching/closure and compact arbitrary-CNF representations remain open.

The manuscript's Section 12.43 now reports the budget comparison, regressions,
resource limits and next propagation target. It also makes the arbitrary-SAT
obligation concrete: G = AND_i(z OR C_i) has an immediate witness z=true, but
adding the single unit NOT z makes satisfiability equivalent to arbitrary
F = AND_i C_i. Cheap old witnesses therefore do not guarantee cheap expansion;
expensive preparation may have absorbed the unresolved work. This argument does
not rule out such preprocessing. The arbitrary-SAT research record now separates
complete fallback coverage from missing uniform recognition, composition,
representation, acquisition and update bounds.

Implementation/evidence checkpoint `df41bee` is pushed. The Lean build and audit
pass unchanged at 4,083 declarations / 1,943 theorem declarations. All 45 previous
proof blocks are unchanged, with 163 unique labels. The final PDF compiles without
warnings or box errors; changed pages 80--81 were visually inspected.

## 2026-11-08: prioritize pattern discovery and exact coverage

The user redirected the next iterations toward discovering SAT patterns and a
valid partition of the entire SAT problem. Known-family optimization remains
useful supporting work. The previous propagation-first execution order is
superseded by this research priority; its profile and all earlier results remain.

The new `research/sat-pattern-discovery.md` defines the first milestone: an
audited pattern inventory over existing residual-solver capabilities, tested on
unlabelled CNFs, exhaustive small cases and adversarial mixtures/edits. Record
all recognition outcomes and positive certificates, including overlaps; describe
unresolved cells and their interactions rather than only counting successful
specialized routes. A failed bounded recognizer is not a semantic exclusion.
Deterministic, versioned outcome vectors provide an exhaustive disjoint reporting
partition, but do not by themselves constitute an efficient structural solution.

The plan distinguishes whole-input classification from exact conditioning and
component decomposition within a formula. Shared-variable compatibility remains
explicit. Discovery, recomposition, compactness, acquisition and update costs
are separate obligations. The next discovery is selected by coverage and insight
into unresolved interaction, with total cost measured. Existing Horn/dual-Horn,
2-CNF, matching, component and variable-split paths are starting capabilities,
not missing features to reimplement.

The hourly heartbeat prompt now follows this discovery-first direction, keeping
its hourly cadence, active state and existing chat. It still requires preserved
results, tests, verified commits/pushes and quiet operation without material
progress. This checkpoint changes plans and scheduling, not solver behavior or
mathematical results; no manuscript change or new solver tests are needed.

## 2026-11-08: first persistent SAT pattern inventory

Implemented `PatternInventory` as a separate analysis layer using existing
residual helpers. It records seven overlapping syntax/witness outcomes, a
complete direct single-parity encoding certificate within a width cap, exact
source/name bindings, independent component partitions and bounded variable
conditioning. Failed recognition and all attempted alternative residuals remain
explicit and persistent. The SAT engine and its answer/certificate protocol are
unchanged; closed analysis means recognized-family coverage, not satisfiability.

The checker recomputes profiles, validates exact branch restrictions, and directly
reconstructs component source clauses with disjoint supports independently of
the component discoverer. A test injects a faulty overlapping discoverer and
confirms rejection. The parity argument uses distinct full-width clauses to
exclude exactly one half of the Boolean cube; hidden affine equivalence is not
recognized. Above the default eight-variable cap the outcome is unresolved.

The [664-input comparison](../experiments/results/cnf-pattern-inventory/README.md)
contains all 512 subsets of the nine non-tautological two-variable clauses,
120 seeded larger CNFs, 16 structural controls and 16 variants. The tiny sources
normalize to 257 distinct residuals, with exact originals preserved. There are
24 observed root signature cells. Of the other 152 inputs, whole-formula tests
explain 39, independent components 45, one conditioning level 57, and two levels
102. Pointwise checks cover both candidate restrictions and component assignment
recomposition on small inputs, including alternatives not selected for the final
coverage summary. Generator labels are never passed to discovery.

The costs are explicit: analysis plus unchanged solving takes 2.02127 s at two
levels versus 0.30139 s without analysis; analysis alone costs 1.70180 s. SQLite
increases from 385,024 to 6,459,392 bytes. All modes retain the same 699 ordinary
solver residuals. Two-level analysis adds 2,801 pattern nodes (3,688,352 logical
bytes) and 664 sources (452,011 bytes). Cold full audit increases from 20.49 to
362.41 ms. Separate tracing on six mixed/guarded cases measures 60,634 versus
205,298 peak Python bytes, excluding native SQLite/RSS. No solver acceleration
or representative-distribution claim is made.

All 276 Python tests pass. The five final archives contain 4,740 pattern nodes
and 2,656 sources in total, with 699 solver residuals per archive; they replay
without byte changes or new solving. The initial five-policy run and source
snapshots are preserved separately because its component checker only rederived
the discovered groups. All those valid initial archives also pass the stronger
final direct-partition checker unchanged. Recorded source fingerprints match.
The existing Lean conditioning identity is relevant, but no new refinement of
this Python inventory, parity recognizer or SQLite is claimed.

**Next discovery target:** 50 inputs remain unresolved after two levels: 42
seeded CNFs and four structural cases with variants. Forty-eight occupy the
all-excluded pattern cell; two exceed the parity cap while failing other tests.
The controlled misses are five/six-variable complete exclusion cubes, coupled
matching/parity and an activated guarded formula. Refine these connected cells
by exact clause support and sign patterns: complete parity halves, explicit
contradictions and collections of parity equations, preserving leftover couplings.
Evaluate the same recognizer on all unresolved inputs and variants, and retain
zero or negative results on random CNFs. Raising conditioning depth alone is
not the chosen next step. General efficient discovery, compact closure and
polynomial arbitrary-CNF acquisition remain open.

Implementation and evidence checkpoint `c1f39a0` is pushed. The manuscript's
Section 12.44 now records the classifier, elementary direct-parity argument,
exact recomposition checks, coverage gains, overhead and retained unresolved
cases. The Lean build passes unchanged (4,083 declarations / 1,943 theorem
declarations); no new implementation-refinement claim is made. All 45 prior
proof blocks are preserved, with 164 unique labels. The 89-page PDF compiles
without final warnings or box errors, and changed pages 81--82 were visually
inspected. The next discovery target is persisted in both research priority files.

## 2026-11-08: support/sign extraction with exact affine couplings

Implemented the planned connected-cell refinement in
`experiments/cnf_affine_patterns.py`. Complete parity halves on each support
become equations; every other clause remains in an exact leftover list. The
independent checker verifies source partition, supports, distinct signs, counts
and triangular elimination dependencies. Pure systems and contradictory affine
subsystems add separate outcome fields. Mixed consistent systems remain open.
The policy version is in every identity, and old inventory rows/decisions are
unchanged. This is an optional analysis layer, not solver/history integration.

The [preserved 733-source comparison](../experiments/results/cnf-affine-patterns/README.md)
includes all earlier sources plus growing systems, couplings, fresh random CNFs
and adversarial edits/variants. At depth two it closes 14 of the prior 50 open
inputs, leaving 34 seeded CNFs and coupled matching/parity with its variant.
The eight seeded gains use contradictory width-one/two equation subsystems
after conditioning. They are not evidence of discovering large hidden parity.
Five of 48 fresh seeded cases also gain closure, with the same limitation.
Whole-input random closure does not improve. The exact mechanisms and remaining
interfaces are persisted in `mechanisms.json` with an analysis script.

Across all 733 inputs, depth-two analysis plus solving falls from 3.30542 to
2.90083 seconds and SQLite from 14,323,712 to 13,385,728 bytes. Pattern nodes
fall from 3,790 to 3,126. On the original 664 sources total time stays almost
unchanged (1.84691 versus 1.84100 seconds). Depth-zero storage increases by
491,520 bytes. Coupled controls retain recognition overhead: the 16-equation
case increases from 0.05067 to 0.07849 seconds without closure. These are single
sequential samples. Separate six-case Python memory, warm reuse and cold audit
are included; the report distinguishes them from acquisition and process RSS.

All 284 Python tests pass, including exhaustive pointwise checks, random mixtures,
renamings, corrupt certificates, faulty discovery, and coexistence/cold replay
of old and new versions. All five new archives and all five prior final archives
replay without changes or new solving. Previous evidence is preserved.

**Next target:** exact projection and composition at affine/coupling interfaces.
The 32-equation coupled source has 66 variables but only two shared with its
one leftover binary clause. Current frequency-first conditioning misses this
opportunity. Retain arbitrary leftover clauses, checked witness lifting and
refutation semantics, with projection and persistence cost charged. Test the
matching/parity control and all unresolved random cases too. No new Lean
implementation refinement, efficient universal partition, compact universal
oracle or unrestricted polynomial SAT algorithm is established here.

Implementation/evidence checkpoint `e1e7608` is committed and pushed. Manuscript
Section 12.45 adds the exact extraction proposition and proof, checked elimination
scope, matched coverage/costs, retained regressions and next interface target.
All 45 earlier proof blocks remain intact (46 total; 166 unique labels). The
90-page PDF builds without warnings or box errors; changed pages 82--83 were
visually inspected. The existing Lean build and axiom audit pass unchanged
(4,083 declarations / 1,943 theorem declarations). No new Lean theorem is claimed.

## 2026-11-08: checked affine projection and existential composition

Implemented `experiments/cnf_affine_projection.py` and a versioned optional
inventory policy. Internal-first elimination projects extracted equations onto
the variables retained by leftover clauses. Independent checks verify row
dependencies, exact boundary constraints, budgeted direct CNF encoding, child
identity/bindings and strict variable decrease. Models lift by back substitution
and are checked against the full parent CNF. Projection has existential semantics;
it is not pointwise equivalence on eliminated variables. A budget miss retains
the original planner. Exact originals and old archive rows remain unchanged.

The [775-source comparison](../experiments/results/cnf-affine-projection/README.md)
includes all previous 733 sources, growing 64/128-equation coupled cases, exact
boundary/budget controls with variants and 32 fresh affine mixtures. Six growing
coupled cases gain closure even at depth zero. Depth-two closure beyond the 512
tiny cases rises from 209/263 to 215/263. The original 664-source result stays
at 116/152 non-tiny inputs: 34 seeded CNFs and the matching/parity pair remain
open. Initial test expectations that projection alone would close matching/parity
were disproved and corrected to retain the miss. Its source shrinks from 13/61
variables/literals to 10/29; selected unresolved literals shrink from 22 to 18.

Total depth-two analysis plus original solving and root lifting falls from
4.47144 to 3.75039 seconds, SQLite from 22,913,024 to 19,030,016 bytes, and full
cold audit from 1.40055 to 0.98692 seconds. Depth-zero operation time/storage and
the six-case peak Python diagnostic increase. All regressions remain recorded.
The selected unresolved-literal aggregate falls from 31,924 to 1,579, dominated
by growing controls rather than new random coverage. At 258 variables, discovery
is 13.13 ms but original-source solving still takes 564.84 ms, identifying an
integration cost rather than further projection cost.

All 292 Python tests pass, including exhaustive two-variable affine systems and
boundaries, existential fibers, lifting, forged dependencies, encoding-budget
checks before enumeration and cold corruption/coexistence. All five new and five
previous affine-study archives replay without byte changes or new solving. New
Lean lemmas in `AffineCoupling.lean` compose the existing executable projection
theorem with a leftover predicate invariant on eliminated variables, proving
fiber/SAT/UNSAT equivalence. They do not refine the Python pipeline.

**Next target:** checked simplification and interface-aware conditioning of mixed
leftovers. The remaining matching/parity bridge has a positive-only variable;
setting it true exposes matching. Test this against both-polarity couplings and
all unresolved random cases. Native affine boundary rows would avoid the observed
direct-encoding cap; integrating projected decisions could avoid expensive
original-source solving. Keep these supporting opportunities distinct from the
primary unresolved discovery obligation and arbitrary-SAT resource bounds.

Implementation checkpoint `b98dbe2` is committed and pushed. The six growing
coupled systems all share exactly one archived projected child, confirmed by
the retained identity hashes; original sources and bindings remain distinct.
Manuscript Section 12.46 adds the projection proposition/proof, cost account and
negative results. All 46 prior proof blocks remain intact (47 total; 168 unique
labels). The 92-page PDF builds without warnings or box errors; changed pages
83--85 were visually inspected. The Lean build and axiom audit pass with 4,087
declarations / 1,946 theorem declarations, including the three new composition
lemmas. The next discovery and integration targets are persisted in both priority
files and the evidence README.

## Checked simplification in the structural inventory (8 November, 22:19 run)

The mixed-leftover target is implemented in `cnf_simplification.py`. Unit
propagation reuses the existing solver routine. Independent replay checks forced
clause reasons, conflicts and whole-residual pure rounds; exact source bindings
and assignments support checked model lifting. A new `simplify` node strictly
reduces support without consuming conditioning depth. Policies have distinct
identities and coexist with all older records. The decision solver is unchanged.

The [841-source comparison](../experiments/results/cnf-simplification/README.md)
contains all prior 775 sources, 48 harder random 3-CNFs, adversarial bridges and
variants, and growing unit/pure controls. Depth-two non-tiny closure rises from
217/329 to 290/329; all 36 original misses close. Most gains use standard unit
propagation: units-only closes 289/329 in 6.60422 s versus 7.15375 s combined.
Projection takes 8.09694 s; pure-only regresses to 8.50842 s. The combined archive
shrinks from 39,727,104 to 31,731,712 bytes; exact source payload increases.
Six-case traced Python allocation is nearly unchanged and excludes native memory.

The matching/parity source follows projection, pure bridge removal, then matching
at depth zero. Both-polarity bridges are retained unless valid propagation or
conditioning resolves them. All 32 affine mixtures close at depth two. However,
38 of 48 new random 3-CNFs and the renamed wide-boundary cap case remain open.
The random group costs 3.26227 of 4.62418 s of discovery and is the next target:
profile its alternatives and test structure-aware conditioning at matched work
budgets. The unit-only policy remains an essential cheaper comparator. Actual
projected decision integration and native affine boundaries are supporting gaps.

All 301 Python tests pass (22.72 s), including exhaustive small existential
fibers, lifting, arbitrary renamings, false purity, malformed reasons and cold
corruption/coexistence. All seven new and five previous archives replay unchanged;
every mode retains the same 2,146 ordinary solver residuals. The Lean build passes
without a new formal claim: existing condition/pure-repair semantics support the
argument, while Python and persistence remain outside refinement. The 1,162 new
simplification edges reference 550 distinct children; this is within-policy
reuse, not arbitrary semantic canonicalization. The pure-chain control's signed
chain is disconnected from its matching-plus-bridge component; its unused parent
profile work and repeated scans are explicitly preserved as costs, not concealed
as a connected-interface result.

Verified implementation checkpoint `d264f5e` is pushed. Manuscript Section 12.47
now includes the exact existential simplification proposition and proof, the
policy ablations, reuse counts, resource bounds and remaining misses. All 47
earlier proof blocks remain intact (48 total; 170 unique labels). The 93-page
PDF builds without warnings or box errors; pages 85--87 were visually inspected.
The persistent next target is the expensive unresolved random 3-CNF group, with
structure-aware conditioning compared against the cheaper unit-only policy.

## Conditioning choices and the cost of intermediate residuals (8 November)

The current run profiles the prior 48 random 3-CNFs and tests a fixed
MOMS-inspired shortest-clause ordering. `cnf_conditioning.py` supplies an optional
versioned policy; the original frequency ordering and archive identities are
unchanged. Both Boolean branches and all attempted alternatives are checked.
Counting and sorting cost O(L + v log v) word/comparison operations plus encoding
costs; there is no new recognition class or optimality theorem. The primary
literature link and exact variant are recorded in the evidence README.

The [949-source comparison](../experiments/results/cnf-conditioning/README.md)
keeps all 841 old sources and adds 72 fresh formulae plus 36 transfer controls.
At depth two/cap four, coverage beyond tiny exhaustive inputs rises from 322/437
to 330/437 against the unit-only baseline, but total time rises from 17.20315 to
20.24553 s and SQLite from 79,118,336 to 96,911,360 bytes. Only two of the eight
gains are fresh inputs. Relative to combined unit/pure processing there are six
gains and five losses, including old case 631. Keep the policy optional. Even
cap-eight frequency conditioning closes none of the 32 fresh 3-CNFs at 20/32
variables. Bounded misses are not lower bounds on every decomposition.

Fewer attempted candidates (4,300 -> 3,956) produce more distinct nodes
(9,162 -> 11,224). Logical simplification-node payload increases by 8,405,501
bytes, about 91% of the total increase. Repeated child references also fall.
The next concrete target is one checked edge combining a conditioning assumption
and its forced-unit closure. Retain reason references, parent identity, exact
reconstruction and model transport; compare with the current full intermediate
node representation before spending more work on lookahead. Preserve terminal
recognition behavior and charge cold replay. This optimization is not implemented
and cannot be counted as an achieved saving.

The development profile, all pilot losses, exact gain/loss sources, node-kind
byte totals, paths and five new archives are persisted. Five new and seven old
archives replay unchanged, and every mode retains the same 4,034 ordinary solver
residuals. All 306 Python tests pass (22.90 s), covering branch semantics,
exhaustive tiny cases, random mixtures, renamings/edits, candidate-order corruption
and policy coexistence. The Lean build/audit still passes at 4,087 declarations /
1,946 theorem declarations; no new formalization is claimed.

Implementation/evidence checkpoint `42cb199` is pushed. Manuscript Section 12.48
records the conditioning rule, verified prior-work citation, fresh-input limits,
coverage/cost tradeoff and the next checked-edge opportunity. All 48 earlier
proof blocks remain intact, with 171 unique labels. The 94-page PDF builds
without warnings or box errors; changed pages 86--88 and bibliography pages
93--94 were visually inspected. The policy stays optional and all prior results
and counterexamples remain available for subsequent runs.

## Checked conditioning/closure edges (9 November)

`cnf_fused_conditioning.py` implements the proposed contraction. It fuses only
conditioned children whose old next step was simplification. Recognized leaves
and independent components keep their priority. The edge stores the existing
unit/pure certificate and final child binding in parent IDs; checking rebuilds
the intermediate restriction, validates gates/reasons and checks the exact
target. SAT models lift through the branch assumption and are checked against
the full parent. Root/source and pre-existing intermediate records are retained.

The [949-source comparison](../experiments/results/cnf-fused-conditioning/README.md)
checks three policy pairs. Every root profile, coverage summary and acquired
candidate count is identical. The full archive analyzer checks all 3,999 OR plans
for identical choices, selected alternatives and final child CNF/depth/bindings
after contraction. All non-simplification CNF/depth pairs remain. This is corpus
evidence and executable checking, not a new Lean implementation refinement.

For shortest-clause ordering, nodes fall from 11,224 to 6,281, SQLite from
96,911,360 to 65,572,864 bytes, and total time from 21.16978 to 17.63829 s.
Frequency falls 17.33216 -> 15.97544 s and combined unit/pure falls 18.49975 ->
17.14480 s. Shortest-clause cold audit falls 7.89184 -> 6.93005 s. A separate
branch-heavy six-case traced Python peak falls 5,682,777 -> 3,756,516 bytes.
The old easy-case diagnostic grows slightly; warm replay and the in-memory pilot
retain runtime regressions. Native memory and full-corpus peak are unmeasured.

All 312 Python tests pass (25.12 s), including exhaustive branch fibers, model
lifting, terminal/component priority, invalid/missing reasons and transport,
cold corruption and coexistence. Seven new and five prior archives replay
unchanged; every mode retains the same 4,034 solver residuals. The Lean build and
audit remain at 4,087 declarations / 1,946 theorem declarations.

No new cases close. The shortest-clause policy still has 107 non-tiny misses,
and all measured policies miss the 32 fresh 20/32-variable 3-CNFs. Its remaining
payload is chiefly unresolved CNFs and OR alternatives. Next investigate bounded
unit-conflict probing on binary-rich conditioned residuals, using checked
refutations to justify forced values. Charge probes even when they consume no
branching depth, retain failures, and compare against the existing policies.
Repeated recognition is a supporting cost, not a reason to omit validation.

Implementation/evidence checkpoint `041303e` is pushed. Manuscript Section 12.49
states and proves the exact existential relation for a fused branch, records the
matched savings and regressions, and separates representation savings from new
structural coverage. All 48 earlier proof blocks remain intact (49 total; 173
unique labels). The 96-page PDF builds without warnings or box errors; pages
87--89 were visually inspected. The next run should start with the bounded
unit-conflict probing opportunity above, retaining the fused and unfused archives
as baselines rather than repeating the completed contraction experiment.

## Bounded checked failed-literal discovery (9 November)

`cnf_failed_literal.py` implements the next discovery step. After existing
family, component, simplification and projection priorities, it probes binary
variables in incidence order with an optional per-residual cap. A checked unit
conflict forces the opposite value; that assumption and unit closure reach the
child directly. Forced rewrites preserve arbitrary-branch depth but strictly
reduce support. All inconclusive probes, reasons, exact children and model lifts
are checked and retained. The ordinary SAT decision solver is unchanged.

The [1,025-input study](../experiments/results/cnf-failed-literal/README.md)
retains all 949 previous inputs and adds 64 random holdout formulas and 12
constructed/transfer/invalidation controls. At depth two and four conditioning
candidates, four-variable probing raises closure 358/513 -> 484/513 non-tiny
inputs and 19/64 -> 51/64 fresh random inputs. Its 126 gains include 88 SAT and
38 UNSAT inputs; no baseline closure is lost on this corpus. Total time falls
27.11056 -> 18.87839 s, SQLite 93,143,040 -> 65,056,768 bytes and full cold audit
10.07933 -> 6.41165 s. The one-variable policy reaches 465/513 in 18.93343 s.
All modes retain the same 5,379 ordinary solver residuals. Six-case traced Python
peaks fall; native/full-corpus peaks are unmeasured and warm time slightly grows.

Twenty-nine misses remain. Probing every binary variable on these sources closes
only cases 968 and 1024, at higher inventory time (6.81731 -> 11.49531 s), storage
and cold cost. The initial diagnostic omitted ordinary-solver tables, causing
the shared auditor to create tables and fail byte preservation. Its archive and
failure log are retained; final diagnostic archives initialize empty tables and
both replay byte-identically. No certificate correctness failure occurred.

Probe nodes now occupy 12.545 of 22.743 MB logical state. Profiling the largest
discovery miss, case 894, points to repeated restriction, unit propagation/checks
and normalization. More promising for discovery than raising the cap: 245
archived inconclusive-probe nodes already have a common literal propagated by
both assumptions, including 179 unresolved nodes. By Boolean case splitting
that consequence is forced. These counts include unselected alternatives; using
the facts is not implemented and does not yet add coverage. Next implement
checked common-consequence reuse from existing traces, retaining failed probes,
transport and dependency checks, then compare total cost and remaining cases.
Probe-chain sharing and occurrence-driven scans are supporting cost targets.

All 319 Python tests pass (27.38 s), including exhaustive fibers, random mixtures,
renamings/edits, corrupt reasons/assumptions/transports and cold coexistence.
Four new and seven prior complete archives replay unchanged. The two new Lean
lemmas `failed_condition_forces` and `satisfiable_failed_condition` prove the
semantic rule from a supplied refutation; they do not refine Python or SQLite.
The full Lean build/audit passes at 4,089 declarations / 1,948 theorem declarations.

Implementation/evidence checkpoint `7d4f068` is pushed. Manuscript Section 12.50
adds the failed-assumption proposition and proof, the binary-incidence gate
argument, verified prior-work attribution, matched results and cap limitations.
All 49 earlier proof blocks remain intact (50 total; 175 unique labels). The
97-page PDF builds without warnings or box errors; pages 89--90 and bibliography
page 95 were visually inspected. Resume with checked common-consequence reuse
from the stored probe traces; retain the 29-case cap diagnostic and avoid
repeating unconditional probe-budget escalation.

## Checked common consequences and their downstream cost (9 November)

`cnf_common_consequence.py` implements the standard necessary-assignment rule.
It preserves all failed-literal attempts, then applies all common literals from
the first complete inconclusive pair with a nonempty intersection. Both unit
traces, pair selection, retained closure, exact target and model transport are
checked. Support strictly decreases. Earlier recognition/component/reduction
priorities and old-policy archives remain valid. Small hooks in the previous
inventory share checking/lifting without changing its record format or policy.

The [1,101-input comparison](../experiments/results/cnf-common-consequence/README.md)
preserves all 1,025 old inputs and adds 64 fresh random formulas (through 48
variables) and 12 growing/signed/edit controls. Coverage rises 536/589 -> 537/589
non-tiny cases, solely old case 968; no baseline closure is lost, and fresh
coverage remains 40/64. Total time rises 32.12172 -> 32.75928 s, SQLite
104,435,712 -> 107,757,568 bytes and cold audit 12.03279 -> 12.56291 s. The
post-selected 29-miss pilot also gains one closure at higher cost and is retained.
This policy stays optional; there is no measured general speedup.

There are 477 common rewrites assigning 663 literals. All 355 common nodes with
a matching baseline CNF/depth retain identical probe lists. Despite fewer
arbitrary candidates (2,036 -> 1,957) and selected unresolved literals
(9,728 -> 8,101), total probes rise 29,280 -> 31,745 and logical node bytes
38,929,223 -> 40,749,002. New residuals cause repeated acquisition. Witness and
closure JSON is only 34,415 bytes, while probe-node payload grows by 2,410,587.
The targeted six-case peak and warm replay also slightly regress. All modes
retain 7,393 ordinary solver residuals; the decision solver is unchanged.

Fifty-two non-tiny cases remain open. A fresh 48-variable miss is now the largest
discovery cost; profiling still points to restriction, unit checks/propagation,
normalization and literal helpers. Saved paired implications contain a more
structural next opportunity: signed variable equivalences not already expressed
by a direct binary pair. There are 269 such archived unresolved nodes, but only
16 on selected paths, affecting 16/52 missed sources and 799/8,101 selected
unresolved literals. Implement and check full-CNF substitution and signed model
transport on those selected residuals first. Measure whether a recognizable
family/component emerges before applying the rewrite to all alternatives.
These counts imply neither new coverage nor a resolution of the larger misses.

All 326 Python tests pass (27.50 s), including exhaustive fibers, multiple
common literals, saved-trace reuse, mixtures/edits, invalid/omitted witnesses,
transport and cold corruption. Three new and four preceding complete archives
replay byte-identically. Two new Lean lemmas prove the common-consequence rule
and exact SAT restriction from explicit implication hypotheses. The full build
and axiom audit pass at 4,091 declarations / 1,950 theorem declarations; Python,
SQLite and resource bounds remain outside the refinement.

Implementation/evidence checkpoint `79e1404` is pushed. Manuscript Section 12.51
adds the common-consequence proposition and proof, the verified necessary-
assignment citation, measured cost regression and selected-path limits on the
next equivalence opportunity. All 50 earlier proof blocks remain intact (51
total; 177 unique labels). The 99-page PDF builds without warnings or box errors;
pages 90--92 and bibliography page 96 were visually inspected. Resume with the
16 selected unresolved equivalence candidates, preserving this optional policy
and its negative cost evidence rather than enabling it unconditionally.

## Checked signed equivalence and its acquisition cost (9 November)

`cnf_probe_equivalence.py` implements exact full-CNF substitution using the first
eligible opposite-consequence probe pair. It preserves failed-literal/common
priority and all attempted probes. One star-shaped block receives the smallest
variable as representative, with explicit signs. The checker validates source
reasons, first-pair selection, complete map, strict support decrease and exact
child binding. Model lifting composes compact names and signed representatives,
including representatives that vanish after tautology removal, then checks the
full parent. Old policies/archives coexist unchanged. Recognition overlaps and
all remaining interactions are retained; this is not a new universal SAT class.

The [selected pilot](../experiments/results/cnf-probe-equivalence-pilot/README.md)
closes seven of sixteen old source misses. Total time slightly falls 4.92437 ->
4.86584 s, SQLite 16,863,232 -> 16,326,656 bytes and nodes 1,698 -> 1,585.
The [full comparison](../experiments/results/cnf-probe-equivalence/README.md)
retains all 1,101 previous sources and adds 24 fresh random 3-CNFs through 48
variables plus twelve growing, signed and edited controls. Non-tiny closure rises
567/625 -> 574/625; the same seven old cases gain and none lose on this corpus.
Three gains are variants of one source. Fresh random closure remains 18/24.
Fifty-one source misses remain. The independent decision solver is unchanged.

The full cost conclusion reverses the pilot: total time rises 38.29300 ->
39.73059 s, discovery 27.77853 -> 29.08758 s, SQLite 130,596,864 -> 135,569,408
bytes and cold audit 15.20846 -> 15.85644 s. Warm replay rises 0.14485 -> 0.29462
s. Keep this policy optional. These are single sequential synthetic measurements;
no significance or industrial-performance claim follows.

There are 624 equivalence rewrites merging 1,145 variables across acquired nodes.
All 431 shared exact parent CNF/depth pairs retain identical probe lists. Yet
attempts rise 37,049 -> 41,039 and pattern nodes 9,584 -> 9,952. Conditioning
candidates fall 2,232 -> 2,063 and selected unresolved literals 10,300 -> 9,674.
Logical bytes rise 50,062,370 -> 52,575,330; probe nodes alone occupy 32,136,270.
The signed witnesses use only 25,670 JSON bytes. Full keys/profiles, the added
policy identity and changed descendants remain charged. The six-case traced
Python peak falls 14,564,269 -> 11,586,228 bytes, but excludes native SQLite,
RSS and full-corpus peak. Reduced support, targeted live memory and total durable
storage must not be conflated. The 261 immediately unresolved equivalence children
also show that merging known relations need not expose a recognized family.

Next investigate **bounded local learning from saved one-way implications**.
Seventy of 77 selected unresolved nodes have 552 implied binary clauses absent
explicitly in their parent (node/clause pairs). Binary-graph analysis shows 333
already have implication paths; **219 lack such a path**, on **47 selected nodes
affecting 37 missed sources**. `implication-boundaries.json` preserves exact
assumption/reason dependencies and affected source IDs. No-path evidence is not
semantic nonredundancy; other reasoning may entail the clause. Case 1061 remains
the largest discovery cost (0.96542 s, separately instrumented 2.96676 s), with
restriction, unit checking/propagation, normalization and helpers dominant.
Start bounded learning on these selected misses, charge redundancy recognition,
extra propagation/clauses, checking and archive growth, and measure before enabling
it globally. Supporting scan/sharing optimizations remain relevant. None of these
opportunities establishes compact exact coverage of arbitrary SAT.

All 333 Python tests pass (27.90 s), including exhaustive small fibers, signed
and transitive blocks, disappeared representatives, mixtures, source edits,
invalid/omitted witnesses, lifts and cold corruption. Three new full archives,
three pilot archives and three preceding full archives replay byte-identically;
all 28 code/test fingerprints in each new benchmark report still match. Three
named Lean lemmas prove substitution evaluation, the opposite-assumption rule
and SAT preservation from explicit compatibility hypotheses. The full build and
axiom audit pass at 4,101 declarations / 1,957 theorem declarations (including
generated declarations). Python, SQLite and resource accounting are not refined
by those semantic lemmas.

Implementation/evidence checkpoint **4373610** is pushed. Manuscript Section 12.52
adds Proposition 12.40 with proof, the checked signed lift, verified prior-work
references, measured gains/regressions and the remaining implication opportunity.
All 51 earlier proof blocks remain intact (52 total; 179 unique labels). The
100-page PDF builds with no final-pass warnings or box errors; pages 92--94 and
bibliography pages 98--99 were visually inspected. Resume from the bounded-learning
target above, preserving the full-corpus regression and the remaining 51 misses.

## Bounded local learning and gain attribution (9 November)

`cnf_probe_learning.py` adds one bounded continuation round after the previous
probe rules are inconclusive. Saved original-source implications license at most
four binary clauses; duplicates and binary-path consequences are skipped, including
paths through earlier accepted batch clauses. The checker verifies original
reasons before trusting additions, preventing circular justification. A second
bounded probe pass receives the augmented source. Only strict support reduction
can acquire a child; a failed round remains in the profile and continues ordinary
planning on the original CNF. Exact children and forced/signed lifts are checked.
Old recognition overlaps, priorities and archives remain intact.

The [37-source pilot](../experiments/results/cnf-probe-learning-pilot/README.md)
closes only old source 1057, with time 16.98242 -> 19.27531 s and SQLite
53,002,240 -> 56,647,680 bytes. The
[full study](../experiments/results/cnf-probe-learning/README.md) retains all
1,137 previous inputs and adds 24 fresh random 3-CNFs through 48 variables plus
twelve growing, signed and edited controls. Non-tiny structural closure rises
604/661 -> 607/661, with no lost baseline closure on this corpus. Gains are
956 (old, 20 variables, SAT), 1057 (old, 48 variables, UNSAT) and 1155 (fresh,
48 variables, UNSAT). Fresh closure rises 18/24 -> 19/24. Fifty-four cases remain
structurally unresolved: 49 old and five fresh. The independent source solver
still decides all inputs and retains the same 9,760 residuals in all modes.

The policy stays optional. Total time rises 48.17697 -> 52.69690 s, discovery
35.64804 -> 39.96872 s, SQLite 163,532,800 -> 168,267,776 bytes and full cold
checking 20.78528 -> 22.01280 s. The six-case traced Python peak rises
18,466,093 -> 20,377,761 bytes; native memory, RSS and full-corpus peak are not
measured. These are single sequential synthetic measurements. Learning adds a
second probe pass, so the modes do not have equal total probe budgets. All extra
work is charged; the targeted pilot's minor test overlap is disclosed separately.

There are 1,938 learning attempts and 4,909 proposed clauses. Of these attempts,
1,709 are inconclusive; 229 yield support reductions (150 forced, 53 equivalence,
26 common). Only seven immediately reach a recognized family, while 68 still
lead to an unresolved child. All 1,780 shared exact parent CNF/depth pairs retain
their original attempt lists. Total probes rise 47,286 -> 62,784. Pattern nodes
fall 11,410 -> 11,406, yet logical bytes rise 63,465,538 -> 66,573,092. Batch and
continuation JSON occupies 1,945,661 bytes. Selected unresolved literals fall
12,686 -> 11,106. Eighty selected distinct unresolved nodes remain, with 48
inconclusive learning rounds and 32 clear profiles. Neither fewer nodes nor
smaller remaining interactions guarantees lower acquisition cost.

`learning-mechanisms.json` preserves an attribution diagnostic: use the same
continuation variables on the source without additions. Forty-nine of 229
successful nodes still reduce (39 forced, five common, five equivalence). This
includes the selected learning nodes on both old gains. The selected node on
fresh gain 1155 stays inconclusive without additions. Stronger propagation and
changed choices both contribute; neither semantic necessity nor counterfactual
whole-source closure follows. Obtaining the changed choices is not free. The
old 77 selected leaves are also replayed: thirty have no batch, 41 remain
inconclusive, five force assignments and one yields equivalence. All traces,
including failures, are retained. The published constraint-resolvent example's
unmodified all-true recognition and its signed learning variant remain tests.

**Next target:** reuse the checked original closure when the added batch has
no unit or conflict under that closure and its assumption; otherwise resume
propagation or retain the full fallback. Of 15,052 continuation probes, 13,194
repeat an original assumption and **10,018 repeat the complete certificate**.
This is a concrete opportunity to reduce scans and share proof records without
dropping stronger propagation. Preserve source/batch identities, clause-index
transport and all fresh candidate probes. Measure exact plans/coverage, fibers,
checking, total cost and cold replay before enabling it. This supports further
discovery on the 48 selected leaves where learning remains inconclusive; no
runtime saving or new closure from reuse is yet measured. The largest discovery
case is now 1063 (1.20829 s, separately profiled 4.07290 s). Restriction scans,
unit checking/propagation and literal helpers dominate; probe nodes account for
41,131,705 / 66,573,092 logical node bytes. Do not raise the global probe cap yet.

All **341 Python tests** pass (28.55 s), including all 512 two-variable sources
and 3,304 subsets with at most three three-variable clauses at caps 0/1/4,
pointwise learned-source equivalence, reduced fibers, signed mixtures, corrupted
or circular proofs, invalid lifts, source edits, cold corruption and policy
coexistence. Three new full archives, three pilot archives and three preceding
full archives replay byte-identically. All 31 code/test fingerprints in each
new benchmark report match. Two new Lean lemmas prove assumption-to-clause
entailment and batch model preservation under explicit original-source hypotheses.
The full build/axiom audit passes at **4,103 declarations / 1,959 theorem
declarations**. Python, SQLite and resource bounds remain outside refinement.

Implementation/evidence checkpoint **eb412fe** is pushed. Manuscript Section 12.53
adds Proposition 12.41, its proof, the established local-learning citation,
coverage/cost results, the changed-choice diagnostic and the next closure-reuse
condition. All 52 earlier proof blocks remain intact (53 total; 181 unique labels).
The 102-page PDF builds with no final-pass warnings or box errors; pages 93--96
were visually inspected. Resume from checked continuation reuse, preserving the
full cost regression and all 54 structurally unresolved sources.

## 9 November: checked closure reuse and bounded-batch selection frontier

The preceding target is implemented and verified in checkpoint **f275a49**,
already pushed. `ProbeClosureReuseInventory` references an old same-assumption
unit proof only after checking its original reasons, complete fixed point and
learned batch, then testing every added clause. An active addition or fresh
assumption uses the full pass. Restriction preserves the old clause prefix and
reason indices; wrong-source, edited, circular or corrupt references are rejected.
The final child and model lift remain fully checked. The independent solver is
unchanged and no unsuccessful attempt is discarded.

The [matched study](../experiments/results/cnf-probe-closure-compact/README.md)
retains all 1,173 old sources and adds 36 controls/holdouts. All **1,209 source
plans** and **13,066 semantic nodes** match, including alternatives and selected
paths. Closure stays **634/697** non-tiny and **15/24** fresh random inputs.
All policies retain 10,856 ordinary solver residuals. The continuation has
17,548 probes: **14,705** reused closures, **672** active repeated assumptions,
**2,171** fresh assumptions. Original passes account for 55,553 logical probes.

The first namespace stores an extra field in every full key. It compresses
807,098 local proof bytes but increases SQLite from 197,103,616 to 200,323,072
bytes. This failed representation and its complete archives remain preserved.
`CompactProbeClosureInventory` replaces the local-learning version tag instead,
keeping a distinct namespace and identical profile proofs. Its sample changes
total time **62.75908 -> 61.68668 s**, discovery **48.01501 -> 46.53708 s**, SQLite
**197,103,616 -> 196,096,000 bytes**, cold replay **26.78483 -> 25.09448 s**, and
six-case traced Python peak **20,377,769 -> 20,021,725 bytes**. These are modest
single-sample effects; checkpoint staging/commit overlapped compact acquisition.
No tests/builds/profiles overlapped primary timing. The compact report explicitly
inherits the three frozen reference modes and newly measures only its own mode.

All **348 Python tests** pass (30.12 s), including exhaustive small fibers,
independent full replay of expanded references, active deltas, new assumptions,
corrupted original reasons, wrong references, signed edits, invalid lifts, cold
coexistence and byte-identical replay. An eight-variable seeded example was added
because the older learning fixtures did not exercise active repeated assumptions;
it now verifies that merely matching an assumption cannot license reuse.
Three first-study archives, three preceding archives and the compact archive
all replay byte-identically. Fingerprints and inherited archive hashes are checked.

Lean formalizes signed unit reasons/derivations and the syntactic fixed-point
criterion. It proves append-only preservation of the whole old derivation and
that the added-clause check is necessary and sufficient once the original closure
is checked. `checked_unit_closure_append` combines these. Full build and axiom
audit pass at **4,121 declarations / 1,964 theorem declarations**. These lemmas
do not refine Python, clause-index serialization, SQLite or complexity bounds.

The manuscript adds Section **12.54**, Proposition **12.42**, its proof and
Table **15**, including both storage outcomes and the exact cost restrictions.
All 53 preceding proof blocks remain intact (54 total; 184 unique labels).
The 104-page PDF builds without final-pass warnings or box errors; changed
pages and the transition into discussion are visually checked.

**Next discovery experiment:** choose a better four-clause batch from already
proved implications, preserving current clause and probe caps. The selected
remainder contains 94 unresolved nodes, sixty learning-clear and 34 clear.
Twenty batches reach cap four; enumeration up to sixteen exposes **61 further
eligible clauses on sixteen leaves affecting thirteen source misses**. Thirty-eight
existing batches draw their clauses from one assumption. The complete
[frontier record](../experiments/results/cnf-probe-closure-compact/learning-frontier.json)
retains every candidate, dependency and no-opportunity leaf. It costs 1,805
candidate visits, 14,871 source literal visits, 6,203 graph vertices and 5,971
graph edges; its separately timed generation is 0.00378 s excluding archive
load/traversal. One leaf reaches the diagnostic cap; this is not exhaustive.

Rank candidates by activation of checked closures and diversity of assumptions,
charge selection, and use a fixed-choice control to distinguish stronger
propagation from altered continuation ranking. Start with the thirteen affected
sources then run all old and fresh unlabelled inputs. No alternate batch was
executed here; these are opportunities, not new closures. Source **1194** remains
the largest discovery cost, dominated by restriction and unit checking/propagation.
Sixty-three source cases remain structurally unresolved. Keep exact classification
and efficient arbitrary-SAT construction/compactness as separate obligations.

## 9 November: bounded clause selection exposes a continuation-order gap

Implementation/evidence checkpoint **69d7780** is pushed. The optional
`SelectedLearningInventory` chooses at most four clauses from sixteen eligible
original-source implications, preferring activation of uncovered saved closures,
origin diversity, total activation and pool order. Its distinct policy namespace
coexists with every old archive. The checker validates original traces first,
reconstructs the selection, then checks references, continuation, strict support
decrease, child and lift. Original defaults and the independent decision solver
are unchanged. The candidate filter can use earlier pool clauses later omitted;
this preserves entailment but can exclude useful alternatives.

The [thirteen-source pilot](../experiments/results/cnf-learning-selection-pilot/README.md)
gains source 1024, with slightly higher total cost. The
[full comparison](../experiments/results/cnf-learning-selection/README.md)
retains all 1,209 prior inputs and adds 24 random 3-CNFs at 20/32/48 variables and
twelve growing, signed and edited controls. It gains **1024**, a satisfiable
guarded source, but loses **956**, a satisfiable random 20-variable source. Thus
closure stays **662/733** non-tiny and **16/24** fresh random inputs, with **71
source misses**. All new controls close under either policy; the unchanged solver
decides every original source and keeps 12,516 residuals. A structural miss does
not change a SAT answer. Preserve this negative aggregate result.

Total time rises **71.41739 -> 73.19404 s (+2.49%)**, discovery **53.49192 ->
54.70319 s**, SQLite **227,385,344 -> 227,831,808 bytes**, cold replay **29.81471 ->
30.35939 s** and the same six-case Python peak **20,021,677 -> 20,121,481 bytes**.
Peak excludes native SQLite, RSS and full-corpus peak. All timing samples are
single sequential runs; primary modes, memory diagnostics and separate profiles
ran without concurrent tests, builds or commits. Nodes rise **14,592 -> 14,653**,
logical node bytes **89,963,443 -> 90,219,745** and logical probes **82,036 ->
82,782**. Fewer conditioning candidates (2,850 -> 2,835) and selected unresolved
literals (17,687 -> 17,327) do not establish lower total cost or greater coverage.
The largest discovery case remains 1194 (1.46397 s); restriction and unit
checking/propagation dominate its separate profile. Keep selection optional.

`mechanisms.json` retains every changed parent and four checked local controls
crossing old/new batches with old/new continuation choices. There are 606 changed
nodes, including 126 reorder-only cases and 562 exact common parents with identical
original proofs. `selection-paths.json` preserves explicit normalized CNFs,
clauses, choices, first conflicts and dependencies for the gained/lost sources.
At 1024, identical choices and equal scalar activation counts still allow only
the selected batch to refute `3=false`. At 956, no original closure activates;
all four controls force a variable, but old choices first refute `14=true` and
new choices `16=false`, under either batch. The actual selected source plan then
remains unresolved. This identifies an effect hidden by local reduction counts.
Replaying all 94 prior selected leaves also improves one local common reduction
on 1189 without closing that source. These are local controls, not counterfactual
whole-source coverage. Failed batches and regressions remain available.

**Next experiment:** hold continuation variable list/order fixed to the ranking
computed from the old first-four batch while applying the selected batch. Charge
old-batch/ranking construction and keep clause/probe caps. Start with 956, 1024
and 1189, then all old and fresh inputs. No whole-source benefit is yet measured;
fixed choices do not guarantee preservation of coverage. Track learned-clause
interactions, first conflict and resulting child structure; activation/diversity
scores alone cannot distinguish the observed outcomes. Do not repeat the same
greedy trial or globally raise caps as a substitute for this control.

All **353 Python tests** pass (32.08 s): exhaustive 512 two-variable inputs and
3,304 three-variable subsets of at most three clauses at learning caps 0/1/4,
exact model fibers, independently expanded proof references, masks against the
delta predicate, signed mixtures/edits, invalid selections/reasons, disabled mode,
cold corruption and policy coexistence. Three full, three pilot and four preceding
archives replay byte-identically; warm reuse inserts nothing. Both reports' forty
code/test fingerprints match. `selected_signed_batch_models` adds the semantic
subset corollary without a ranking hypothesis. The full Lean build and axiom
audit pass at **4,122 declarations / 1,965 theorem declarations**. No Python,
SQLite or resource refinement, compact arbitrary-SAT representation, or uniform
polynomial construction follows.

Manuscript Section **12.55** and Table **16** record the rule, subset argument,
costs, gain/loss, four-way controls and next experiment. All **54 earlier proof
blocks** remain intact, with **186 unique labels**. The **106-page** PDF builds
without final-pass warnings or box errors; pages 96--100, including the changed
section, table and discussion transition, were visually inspected. The discovery plan, ranked priorities,
resource bounds and project/formal READMEs record this completed experiment and
the controlled next target.

## 9 November: fixed continuation choices and a shared-core counterexample

Implementation/evidence checkpoint **bdc6dc7** is pushed. The optional
`FixedOrderLearningInventory` reconstructs the old first-four batch and its
binary-frequency ranking at each exact parent, then propagates the selected
batch under that variable list/order. Both reconstruction and checking are
charged. The checker validates original proofs before reconstructing choices;
no persisted ranking hint is trusted. The original phase, earlier recognition
and decomposition priorities, local caps, strict support decrease and exact
child/model-lift obligations remain unchanged. A separate policy tag preserves
all old archives. The independent decision solver is unchanged.

The [three-source pilot](../experiments/results/cnf-learning-fixed-order-pilot/README.md)
tests 956/1024/1189. Fixed order keeps the earlier gain 1024 but neither recovers
956 nor closes 1189. The [full comparison](../experiments/results/cnf-learning-fixed-order/README.md)
retains all 1,245 previous inputs and adds 24 random 3-CNFs at 20/32/48 variables
plus twelve growing/signed/edited controls. All three policies close **692/769**
non-tiny and **18/24** fresh random inputs. Both selected modes gain 1024 and lose
956 against baseline, with no closure changes between selection and fixed order.
**77 sources** remain structurally unresolved; all original decisions agree and
the ordinary solver retains **13,641 residuals** per mode.

Baseline/selection/fixed total time is **77.91555 / 82.42121 / 80.71966 s**, SQLite
**252,243,968 / 252,497,920 / 252,391,424 bytes**, cold replay **33.50593 / 33.58541 /
34.30859 s**, and same-six-case Python peak **20,021,661 / 20,121,465 / 20,127,074
bytes**. Fixed order is 3.60% slower than baseline. Its 2.06% lower sample time
than selection is not a general speed claim. Peak excludes native SQLite/RSS
and the full corpus. Primary modes, memory diagnostics and separate profiling
ran sequentially without concurrent tests, Lean builds or commits.

Nodes are **16,052 / 16,106 / 16,126**, logical probes **89,782 / 90,513 / 90,713**,
and logical node bytes **100,112,588 / 100,290,071 / 100,315,272**. Physical storage
and logical payload move differently; the shorter fixed-policy tag also changes
keys/source records. Fixed order incurs **6,418 reconstructions**, **25,662 ranked
candidate positions**, and 254,742 learned candidate visits versus selection's
152,026. Selected unresolved literals fall 18,362 -> 17,971 versus baseline
without greater coverage. The frontier retains 111 distinct leaves, 71
learning-clear and forty clear. Source **1194** remains the largest discovery
case at 1.41725 s; its separate 4.58346 s profile again identifies restriction,
unit checking/propagation and literal helpers.

The preserved `mechanisms.json` contains all three selected source paths, every
current unresolved leaf and controlled parent/child acquisitions. On 956's saved
18-variable parent, baseline and fixed order both first refute `14=true`, fix
only `14=false`, and leave **the identical 54-clause original restriction**.
Baseline retains three extra clauses `[1,17]`, `[9,13]`, `[16,17]`; its 17-variable,
57-clause child closes. Fixed retains four `[-18,16]`, `[9,13]`, `[13,18]`, `[16,17]`;
its 17-variable, 58-clause child stays open with eighteen unresolved literals.
All additions are originally entailed, so the two restricted model relations
agree. Immediate order was only part of the earlier loss; representation changes
still affect descendant discovery. At 1024, both selected policies force `3=true`
and close the 27-variable child. Do not promote fixed order as a coverage fix.

**Next experiment:** separate the restricted original core from checked learned
hints. Use the core for structural identity/recognition and retain scoped hints
for propagation. Test 956/1024/1189 and the saved frontier before old/fresh full
inputs. Charge core reconstruction, hint checks, transport, canonicalization,
serialization and cold replay. Keep hint/policy context on discovery plans even
when core decisions/certificates share storage. Edits, changed assignments and
dependencies require revalidation. Removing useful hints can lose coverage; no
improvement from this next representation is measured yet. The rule uses known
entailment and shared provenance, not unrestricted semantic equivalence testing.

All **358 Python tests** pass (30.30 s), including all 512 two-variable inputs and
3,304 three-variable subsets of at most three clauses at caps 0/1/4, exact fibers,
independently expanded references, a seeded changed-order fixture, signed
mixtures/edits, wrong orders, corrupt reasons, omitted/forged batches, disabled
mode and cold coexistence. Four full, four pilot and three preceding archives
replay byte-identically; warm reuse inserts nothing. Both reports' **43 code/test
fingerprints** match. The unchanged Lean build/axiom audit passes at **4,122
declarations / 1,965 theorem declarations**. Existing semantic lemmas justify the
choice-independent reductions; no new Python or complexity refinement is claimed.

Manuscript Section **12.56** and Table **17** record the policy, bounds, complete
negative coverage result and the same-core counterexample. Applying the existing
batch equivalence to valuations extending a partial assignment proves the stated
restricted-model equality. All **54 earlier proof blocks** remain unchanged, with
**188 unique labels**. The **107-page** PDF builds without final-pass warnings or
box errors; changed pages 99--102, including the table, equality and discussion
transition, were visually inspected. Project/formal READMEs, resource bounds, discovery plan and ranked
priorities now point to the shared-core/hint experiment.

## 9 November 2026: checked parent hints with original-clause child cores

Implemented the next representation experiment in `CoreLearningInventory`.
It fully checks the fixed-order learned continuation, retains its hints/proofs
at the parent, and builds a successful child only from the restricted or
substituted original parent clauses. Checked terminal conflicts remain false.
Children receive no inherited hint context and discover their own hints. Equal
normalized cores at equal depth/policy can therefore share plans safely; source
edits, changed reductions and proof dependencies still need full validation.
Earlier priorities, overlaps, exact decomposition and per-node caps are unchanged.
This optional inventory does not alter the complete decision solver.

The [pilot](../experiments/results/cnf-learning-core-pilot/README.md) recovers 956
and retains 1024, leaving 1189 open. Its lower time/storage are selected-case
results. The [full comparison](../experiments/results/cnf-learning-core/README.md)
preserves all 1,281 preceding inputs, adds 24 fresh random 3-CNFs and twelve
growing/signed/edited controls, and closes **719/805** non-tiny inputs versus
**718/805** under baseline/fixed order. There are no lost closures against either.
All close 14/24 fresh random sources; **86** core sources remain structurally
unresolved. All original SAT/UNSAT decisions agree, and the independent solver
retains **15,069 residuals** per mode.

Baseline/fixed/core total time is **94.86962 / 97.40244 / 97.83486 s**, discovery
**70.87369 / 72.76849 / 73.16855 s**, SQLite **284,110,848 / 284,299,264 /
284,094,464 bytes**, cold replay **40.28060 / 41.15963 / 40.38357 s**, and same-six
case Python peak **20,021,661 / 20,127,082 / 20,265,076 bytes**. Core is 3.13%
slower than baseline; the pilot savings do not generalize. These are single
sequential samples. Peak excludes native SQLite, RSS and the full corpus.
Timings, allocation diagnostics, prior archive audits and separate profiling ran
without concurrent tests, Lean builds or commits. Warm/cold replay are separate;
operation time excludes generation, truth tables, summary walks, initialization,
compression and post-run analysis, as specified in the retained report.

Core stores **17,833 nodes / 113,536,866 logical node bytes**, with **72,386,084
bytes (63.76%)** in probe nodes. Its 449 learned edges comprise 311 forced,
42 common and 96 signed-equivalence reductions; 385 change normalized child
syntax and none changes variable transport. There are 380 exact parent/depth
controls in fixed order with identical parent proof records. Reconstruction adds
expected O(L+q+v) time and O(L+v) temporary space after the augmented reduction
is already checked. Across 1,347 repeated reconstruction/checking calls, child
syntax omits 3,156 clause / 6,312 literal occurrences. Parent proofs remain stored.
These occurrence counts do not establish unique redundancy or bytes saved.

The saved 956 parent forces only `14=false` under all policies. Its original
54-clause restriction closes, while fixed order's 58-clause augmented child
stays open. A regression test obtains the same core from both independently
checked batches and confirms exact reuse. **No two learned parents share a child
core in the full run.** The coverage gain is therefore altered descendant
discovery, not evidence of broad within-run core merging or semantic canonicalization.

The [mechanism record](../experiments/results/cnf-learning-core/mechanisms.json)
preserves both parent controls, selected paths for 956/1024/1189 and actual gains,
all 124 selected unresolved leaves (86 learning-clear / 38 clear), every learned
core edge and a separate profile. Transporting proved clauses diagnostically
through exact assignments/substitutions and variable maps yields **992 eligible
hint occurrences**, 85 already in core and **907 absent**. Of these, **319 are
learned again in the immediate child's batch across 165 edges**, including 127
learning-clear and 38 learned children. None in this sample mentions variables
outside the core; that invalid transport possibility is recorded explicitly.
Counts are occurrences, not unique facts, avoided probes or saved seconds.

**Next experiment:** reuse checked hint evidence across these edges while keeping
structural recognition on the core. Preserve source entailment, exact reduction,
variable map and hint-dependent propagation context. Compare those 165 edges,
956/1024/1189, the frontier and full old/fresh inputs at unchanged caps, including
all checking/storage/replay costs and any losses. Cached implication proofs do
not automatically remove the original probes required by current ranking or
earlier reductions; skipping them needs a checked policy change. This inherited
hint policy is not yet implemented. The largest unresolved case is now fresh
48-variable source 1297 at **1.47150 s**, with 456 selected unresolved literals.
Its separate 3.36725 s profile is dominated by restriction, simplification checking,
propagation and literal helpers, and has only one successful learned parent.
Reusing checked propagation state remains the broader supporting cost target.

All **366 Python tests** pass (32.601 s). New tests include all 512 two-variable
CNFs and 3,304 three-variable subsets of at most three clauses at caps 0/1/4,
exact fibers and independently expanded references, forced/common/equivalence
fixtures, signed mixtures, edits, disabled mode, forged dependencies, wrong child
bindings, preserved learned conflicts and cold coexistence. A failed 25,000-input
random search for the conflict fixture is recorded; a constructive pair forcing
opposite shared outputs supplies the retained counterexample. Four full, four
pilot and four preceding archives cold-replay byte-identically; warm reuse inserts
nothing. Both reports' **47 code/test/Lean fingerprints** and all archive hashes match.

Lean adds `CompletePartial`, `entailed_signed_batch_partial_models` and
`entailed_signed_views_common_core`. Originally entailed batches preserve models
under any common partial assignment, including incompatible assignments with
no models. These semantic lemmas do not refine Python filtering, encoding, model
transport, SQLite or costs. The full build/axiom audit passes at **4,125 declarations
/ 1,967 theorem declarations**. Implementation, proofs and artifacts are pushed
in **599f921**. The manuscript records the method, complete tradeoff and next gap
in Section **12.57**, Table **18**. Prior proof blocks remain unchanged; efficient
arbitrary-SAT discovery, compact global closure and uniform acquisition bounds
remain open.


The rebuilt **109-page** PDF has no final-pass warnings or box errors. Changed
pages 100--103, including Table 18 and the discussion transition, were visually
inspected. All **54 prior proof blocks** remain unchanged and **190 labels** are
unique. Project/formal READMEs, resource bounds, discovery and ranked priorities
record both the modest coverage gain and the full-run time/memory regressions.

## 9 November 2026: portable core proofs, extra-pass regression, ranking control

Implemented `cnf_hint_transport.py`: map a checked parent's original implication
reason prefix through its exact forced/common assignment or signed equivalence
and normalized child transport. Parent probe reasons index the restricted parent,
so the translator reconstructs original clause indices before mapping to child
indices. Satisfied/tautological reasons disappear; missing refutations remain
explicit misses rather than invoking hidden fresh search. An independent RUP
checker accepts only a unit-conflict derivation against the exact child core.
The resulting record is portable without the parent graph, with complete
core/clause identity and independently checked reasons. Parent evidence and
earlier archives remain preserved.

`HintAssistedInventory.inspect_hints` supplies an explicit, context-keyed local
control. Recognition and earlier priorities stay on the core. Eligible children
receive one extra bounded pass using proved hints and core-ranked choices;
successful rewrites construct original-clause cores with exact lifting, and
inconclusive passes fall back to the unchanged ordinary planner. All hints and
their order, depth and policy are part of the persistent plan identity. Ordinary
descendants do not inherit hints implicitly. This is an optional local control,
not a replacement of the original whole-source planner at the same total budget.

The [preserved study](../experiments/results/cnf-hint-transport/README.md) covers
all **449** previous learned-parent edges and **45** distinct new parents from
36 fresh sources at seed **20261109064108**. The ordinary planner closes 30/36
fresh originals; their full graphs, answers and solver certificates are archived.
All **1,005** eligible hint occurrences (907 prior, 98 new) translate without
fresh search, into **984** distinct core-clause records. Omissions are 448 satisfied,
64 tautological, 99 explicit and four duplicate occurrences; no outside-variable
or failed-prefix miss occurs in this sample. Universal transport completeness
and Python refinement are not established.

The mapped-prefix walk visits **11,510 reason literals**, versus **287,160** for
fresh scan-based proof search given the same candidates. This is not an overall
speed ratio: transport preparation **0.95129 s** includes full parent checking,
core projection, normalization, index mapping and proof checks; fresh proof
search/checking/persistence costs **0.93100 s** conditional on supplied candidates.
The separately recorded fresh-source acquisition/solving costs **8.87824 s**.

Local baseline/hint closure is **223/494 -> 224/494**, with no losses. Prior-edge
closure is 198/449 -> 199/449; fresh-edge closure stays 25/45. The independent
solver verifies every child core, agrees in both modes and retains **6,051
residuals**. Operation time is **14.41354 / 16.82765 s** before hint preparation
(+16.75%, or +23.35% including preparation), discovery **6.06309 / 7.87721 s**,
SQLite **55,119,872 / 63,885,312 bytes**, cold replay **4.70738 / 7.72522 s**, warm
lookup **0.06691 / 1.31088 s**, and matched-six-core Python peak **7,372,293 /
7,430,827 bytes**. Peak excludes preparation, native SQLite, RSS and full corpus.
Hint cold time includes ordinary graph/solver and separate fresh hint-plan audits;
their repeated checking remains charged. Primary runs, memory diagnostics, builds,
tests and later controls ran sequentially without overlaps affecting primary timing.

Ordinary nodes fall **2,167 -> 1,999**, payload **11,157,841 -> 9,943,442 bytes**,
but portable hint records add **2,181,006 bytes** and 494 context plans add
**3,096,507 bytes**. Probes rise **14,468 -> 16,136**; selected unresolved literal
occurrences fall **57,827 -> 57,595**. The overlay is clear on 180 cases, skipped
on 83, forced on 169, common on 27 and equivalence-reducing on 35. Reductions do
not by themselves count as new closures. The extra-pass policy remains optional.

The local gain is **case 97**, a 25-variable, 81-clause core at depth zero, reached
through a common reduction in an **unselected alternative of original source 977**.
It is absent from every saved selected whole-source path. The source's selected
plan remains open with two leaves and 138 literals; the local baseline has one
open leaf with 223 literals. Do not increment the preceding **719/805** source
coverage using this local result.

The [mechanism record](../experiments/results/cnf-hint-transport/mechanisms.json)
crosses transported/rediscovered batches with core/baseline-continuation choices.
Both batches close using `(4,5,7,19)`, refuting `19=true` and forcing
`19=false,13=false`; both stay clear/open using `(4,5,7,11)`. This isolates the
variable-choice policy as sufficient to explain the gain. Stronger inherited
clauses are unnecessary for this control. A further diagnostic records **1,456
inactive / 102 active deltas** across original probe closures on **196 cores**.
Original proofs must be checked first; this is an opportunity count, not executed
reuse or avoided probes.

**Next experiment:** core-ranked continuation choices with the existing learned
batch, existing pass count and local caps. Derive choices from the checked original
traces or exact core, test 97/977 and 956/1024/1189 first, then complete old/fresh
source workloads. Record any losses and avoid rebuilding an old augmented batch
solely to rank. Portable hints can later enter a separately checked existing-pass
policy; do not assume an additional pass is efficient. Recognition, coverage,
total cost and full-source effects remain separate metrics.

All **374 Python tests** pass (32.796 s). Eight new tests cover exhaustive small
RUP soundness, forced/common/equivalence translations, signed renamings and edits,
wrong parent dependencies, corrupted core reasons, exact-source bindings,
empty/nonentailed clauses, model fibers, explicit contexts, wrong children and
cold replay without parent access. A first negative test mistakenly expected a
valid proof to fail after removing an unused clause; it was corrected to test
the store's exact-source binding separately from proof validity. The full Lean
build/axiom audit passes at **4,126 declarations / 1,968 theorem declarations**.
New `Fragments.core_fragment_sound` derives exact-core entailment from the existing
fragment checker and core-premise membership. It does not verify Python translation
or persistence. The manuscript attributes the underlying proof method to existing
hinted clausal checking rather than claiming novelty.

Four new archives replay byte-identically; warm reuse inserts nothing. All **51
code/test/Lean fingerprints**, four archive hashes and analyzer hashes match.
Implementation, proof and experiment checkpoint **a0f57c9** is pushed. Manuscript
Section **12.58**, Table **19**, and the discovery/resource/priority records retain
the successful portability result, unfavorable costs and ranking-dependent gain.
Efficient arbitrary-SAT classification, compact closure and global acquisition
bounds remain open.

The **111-page** PDF builds without final-pass warnings or box errors. Changed
pages 102--105, including Table 19 and the discussion transition, were visually
inspected. All **54 previous proof blocks** remain unchanged and **192 labels**
are unique. Object/database initialization was outside local operation timings
and not separately timed; this limitation is retained with the measured costs.


## 9 November 2026, 07:38 UTC heartbeat: core-order counterexample and next selection gap

Implemented optional `CoreOrderLearningInventory` in
[cnf_learning_core_order.py](../experiments/cnf_learning_core_order.py). It retains
the selected batch, existing two probe phases, exact core child and earlier
priorities. The continuation extracts choices from the complete original clear
trace only after original discovery or full independent checking. Extraction is
O(p), with O(p) temporary references; original ranking and all source/reason checks
remain charged. Separate policy identity preserves prior nodes and results.

Six new tests cover 512 exhaustive two-variable inputs and 3,304 three-variable
subsets with up to three clauses across multiple caps, exact model fibers,
forced/common/equivalence lifts, the saved local case 97, malformed original
traces/order/batches/continuations, signed mixtures and edits, disabled learning,
wrong-child rejection and byte-identical cold coexistence. All **380 tests** pass
in **33.602 s**. The unchanged full Lean build/axiom audit passes at **4,126
declarations / 1,968 theorem declarations**. There is no new Python refinement or
unrestricted acquisition bound.

The four-source pilot retains 956/977/1024/1189. The full
[matched study](../experiments/results/cnf-core-order/README.md) keeps all 1,317
previous inputs, all 36 original source queries from the hint study, and adds
36 controls at seed **20261109073810**: 24 fresh random 3-CNFs and twelve growing,
signed or edited queries, including repeats. Routing sees only CNF input. All
512 exhaustive tiny cases close. Non-tiny coverage falls **776 -> 775 / 877**,
with **no gains and only source 956 lost**. Old-input coverage is 719 -> 718 / 805;
both modes close 30/36 hint-study queries and 27/36 new queries. The unchanged
independent solver agrees on every answer and retains 18,104 residuals per mode.

Baseline/new operation times are **120.81853 / 116.67493 s**, discovery
**88.69202 / 85.68326 s**, SQLite **347,566,080 / 346,976,256 bytes**, cold replay
**50.51029 / 47.82982 s**, warm lookup **0.25672 / 0.22710 s**, and six-case Python
peak **20,265,108 / 19,623,309 bytes**. Initialization is separately measured at
0.06160 / 0.22272 s. Main timings include recognition, discovery, checking,
serialization, persistence, solving and successful root lifts, excluding generation,
truth tables, summary walks, compression, allocation diagnostics and cold replay.
Memory excludes native SQLite, RSS and full-corpus peak. Modes, memory diagnostics,
profiles, tests and builds run sequentially. The unchanged solver varies by 1.13 s
between combined modes, so the 3.43% total-time drop is not wholly a ranking saving
or a statistical result. Keep the policy optional with its coverage regression.

Pattern nodes fall **21,122 -> 21,005**, logical node bytes **137,740,084 ->
137,076,682**, and the same 1,365 source records occupy **5,225,670 -> 5,250,240
bytes**. Probe attempts fall 119,412 -> 118,152. Reused continuation probes rise
24,672 -> 27,611; active original probes rise 1,492 -> 1,700; newly chosen probes
fall 3,527 -> zero. The old 8,772 auxiliary ranking reconstructions disappear;
new extraction calls number 8,106 and copy 32,326 candidate entries. These are
counts over different residual populations and repeated checks. Selected unresolved
literal occurrences increase **26,137 -> 26,734**.

The loss has a concrete cause. At the common 18-variable, 62-clause depth-one
parent of source 956, both policies select exactly the same batch. Old choices
`(17,9,14,16)` refute `14=true`. New choices `(9,17,18,2)` are all inactive under
the batch, and stay clear. The new source path has one unresolved leaf containing
sixteen literals. The preceding local case 97 still closes with the same batch,
forcing `19=false,13=false`, but it remains outside the selected source-977 path.
Do not count it as an original-source gain. This new 956 ranking loss is separate
from the older redundant-child representation loss.

The [mechanism ledger](../experiments/results/cnf-core-order/mechanisms.json)
retains source paths, all changed shared CNF/depth states, both probe records,
old/core choices, validated batch activity, novel variables, the frontier and a
separate profile. There are **239 learned -> clear** and **16 clear -> learned**
shared-state transitions. In 189 of the local losses, no original core pair is
active. Every one of these 255 gained/lost local states has at most four variables
in the union of active core candidates and novel old-ranking candidates. Loss
union sizes are `{1:166,2:51,3:17,4:5}`; gain sizes are `{2:7,3:6,4:3}`. All 3,001
changed shared states retain identical learned batches; across that larger set,
seven unions already have five candidates. This is not a uniform width bound.

**Next discovery experiment:** use the checked original traces and batch-activity
masks to select active core plus novel candidates within the existing continuation
budget. Inactive unchanged paired closures cannot acquire new forced/common/
equivalence outcomes in the current procedure; retain their valid references.
Test all 255 local transition controls, then original 956 and local 97/original
977, before full source workloads. The union may exceed the cap, and differing
first conflicts or descendants can still change coverage. No combined rule or
recovered closure is implemented in this checkpoint. Supporting exact reuse can
share the deterministic sixteen-clause pool: for caps at most sixteen, its prefix
is the old first-cap batch. This could avoid reconstruction while preserving old
choices, but has not been measured.

The new frontier has **102 unresolved sources / 142 distinct selected leaves**,
99 learning-clear and 43 clear. Source **1194** costs **1.45407 s** discovery with
426 unresolved literal occurrences. Its separate profile records 5,307 restrictions,
4,311 unit-simplification checks and 2,069 propagations; those remain primary
costs. Probe-kind nodes hold 87,079,296 logical bytes, including CNFs, identities,
edges and other fields. Probing fields alone total 15,272,772 bytes. Do not confuse
whole-node storage with certificate payload.

Three full, three pilot and four prior archives replay byte-identically; warm
reuse inserts no records. Both new reports have **50 matching code/test/Lean
fingerprints**. Archive, analyzer and input-report hashes match. Implementation,
tests, measurements and counterexamples are committed and pushed as **544054d**.
Existing policies, previous solver results, proofs and archives are preserved.

Manuscript Section **12.59**, Table **20**, and the README/discovery/resource/
priority records now retain the cost/coverage trade-off and the proposed combined
selection. The **112-page PDF** builds with no final-pass warnings or box errors;
pages **104--106** were visually inspected. All **54 prior proof blocks** remain
unchanged, and **194 labels** are unique. One initial build placed outputs in the
repository root; its six generated files were removed and the final build used
the paper directory. Efficient arbitrary-CNF discovery, total closure size and
lifetime acquisition/storage bounds remain open.


## 9 November 2026, 08:39 UTC heartbeat: preserve local progress and expose signed cores

Implemented optional `ActivityLearningInventory` in
[cnf_learning_activity.py](../experiments/cnf_learning_activity.py). After complete
original probing or full independent replay, it checks both original closures
against the selected learned batch. It keeps old-ranked candidates unless both
closures are inactive, then fills freed positions with active core variables in
original order. Only additions may be truncated. The selected batch is shared
within one checked invocation; no persistent activity mask, unchecked candidate
list or cross-source cache is trusted. Original reasons, two phases, caps, earlier
priorities and exact original-core child binding remain intact. Empty continuations
are explicit checked clear results.

A fixed source/batch retains any old local reduction: omitted unchanged pairs
cannot supply a new forced/common/equivalence outcome; every informative old
candidate fits the cap and keeps its order. Added probes can cause earlier-priority
reductions, but still give local progress. This is not monotone whole-source
coverage, a Python refinement proof, or an unrestricted-SAT bound. Selection costs
expected O(U + p*q + p^2) beyond old-ranking reconstruction, with O(p + u_max)
temporary state beyond the existing traces/batch. All other acquisition, checking,
propagation, normalization and persistence remain charged.

Eight new tests cover exhaustive small model fibers, forced/common/equivalence
lifts, the local case 97, all **255** saved local transition controls, **seven**
overflow controls, empty continuations, malformed traces/orders/children, signed
edits, disabled learning and cold coexistence. All **388 tests pass in 39.515 s**.
The unchanged Lean build/axiom audit passes at **4,126 declarations / 1,968
theorem declarations**. Existing code, previous proofs and archives are preserved.

The [full study](../experiments/results/cnf-activity/README.md) retains all 1,389
prior queries and adds 36 at seed **20261109083909**: 24 fresh random 3-CNFs plus
twelve growing/signed/edited queries, including repeats. Both policies close all
512 tiny inputs and **806/913 non-tiny inputs**, with **no gains or losses**.
They close 30/36 fresh queries, including 18/24 new random inputs. All original
answers agree with the unchanged independent solver; all modes retain 19,557
solver residuals. The four-source pilot restores 956 relative to core-only ranking,
keeps 1024 closed, and leaves 977/1189 open. Source 977 now selects the formerly
unselected local case-97 core; its open part shrinks **two leaves / 138 literals ->
one leaf / 22 literals**. The whole source remains unresolved.

Continuation attempts fall **31,741 -> 7,184 (77.37%)**, logical probes
**127,741 -> 103,413**, and verified attempts **250,703 -> 223,315**. Reused
continuation probes fall 26,407 -> 1,615; active probes rise 1,588 -> 1,810 and
novel probes 3,746 -> 3,759. Active/new propagation therefore increases
**5,334 -> 5,569**. Most avoided work concerns unchanged pairs, not fresh solving.
Across discovery/checking there are 9,460 choice calls, 32,620 inactive / 5,100
active original pairs, 28,424 omitted inactive positions, 9,402 retained old
positions, 682 added positions, 3,088 empty continuations and 36 truncations.
These are repeated-operation counts over different descendants.

Single full-run baseline/activity time is **161.35645 / 134.22746 s**, discovery
**116.82649 / 99.01207 s**, but the unchanged solver varies **44.42359 / 35.13847 s**.
A new [balanced timing control](../experiments/results/cnf-activity/timing-control.json)
uses ABBA BAAB order, four fresh-database trials per policy on sources
858/875/907/970/1042/1061/956/977. Mean total time is **3.85140 / 3.88671 s** and
mean discovery **3.64992 / 3.68110 s**: activity is slightly slower on the subset.
All answers, summaries, counters, storage and database hashes repeat within each
mode. This does not establish statistical significance or a full-corpus estimate,
but prevents a speedup claim from the single full sample. Keep the policy optional
and preserve the unsuccessful timing result.

SQLite bytes are **376,205,312 / 375,824,384**, pattern nodes **22,549 / 22,581**,
logical node bytes **148,631,944 / 147,670,431**, probing-field bytes
**16,760,009 / 15,465,288**, and source bytes **5,405,961 / 5,422,677** across 1,393
records. Cold replay grows **55.11608 / 57.63553 s**, warm lookup **0.27624 /
0.34976 s**, and initialization **0.06187 / 0.28580 s**. Six-case Python peak is
**20,265,108 / 19,996,930 bytes**, excluding native SQLite, RSS and the full-corpus
peak. Operation timings include recognition, discovery, checking, serialization,
persistence, independent solving and successful lifts; generation, truth tables,
summary walks, initialization, compression, allocations and cold replay are outside.
Primary runs, allocation diagnostics, profiling, balanced trials, tests and builds
run sequentially. Exact preparation remains charged; no global cost guarantee follows.

The [mechanism ledger](../experiments/results/cnf-activity/mechanisms.json) replays
all **3,001** previously changed shared CNF/depth states: **421 learned -> learned**,
**16 clear -> learned**, and 2,564 remain clear. All 255 prior gained/lost local
controls reduce, and all informative old candidates survive the seven overflows.
In the new full archives, shared states have eighteen clear-to-learned and no
learned-to-clear transitions. These local reductions are not extra source closures.

The new frontier has **107 open sources / 147 distinct leaves**: 61 inconclusive
continuations (12,984 literals), 39 empty continuations (10,639), 46 clear passes
without a batch (4,264), and one without initial binary candidates (283). Source
**1194** costs **1.47590 s** discovery with 424 unresolved literal occurrences.
Its separate profile records 5,763 restrictions, 4,657 unit checks and 2,221
propagations. Probe-kind nodes occupy 96.289 MB including CNFs/keys/edges; probing
fields alone occupy 15.465 MB. Simply widening initial candidate selection when
binary ranking is empty addresses only one selected leaf here.

**Next discovery target: checked signed-clause subsumption exposing tractable
cores.** The [offline diagnostic](../experiments/results/cnf-activity/frontier-subsumption.json)
changes 105 frontier leaves, removing 217 clauses / 666 literals through 672,003
subset comparisons. Seven resulting cores are recognized as 2-CNF. Retained
signed-subset witnesses, complete source-index coverage, normalization maps and
classifier evidence are stored for every leaf. Removing a clause subsumed by a
retained clause preserves all models; values of disappearing variables are free.
For source 977, `(-7,3)` subsumes `(-7,-1,3)`, and `(-3,9)` subsumes `(-3,7,9)`.
The remaining clauses are binary.

Integrating these exact reductions could complete current selected plans for
**977, 1044, 1053 and 1365**. Sources 907, 1179 and 1363 retain another unresolved
leaf. These are **prospective completions**, not part of the measured 806/913.
The existing ordinary solver has positive-clause subsumption; the inventory lacks
this signed step. Subsumption is established simplification, not a novel arbitrary-
SAT solution. Next implement the source-bound transformation, checked exact child
binding and model lift, preserve earlier family priorities, and compare all relevant
states, failed recognition, storage and cold replay. The selected-frontier comparison
count is not a full-pipeline resource result. Add adversarial sign/order edits,
invalid retained dependencies and small exhaustive model-equivalence checks.

Three full, three pilot and three previous archives replay byte-identically, and
warm replay inserts nothing. Both reports have **53 matching fingerprints**;
archive and diagnostic/timing input/script hashes match. Verified implementation,
measurements, negative timing controls and prospective witnesses are pushed in
**e264fc3**. Manuscript Section **12.60**, Table **21**, README and persistent
priority/discovery/resource records now distinguish local progress, unchanged
source coverage, negative timing evidence and the next signed-core opportunity.
The **114-page PDF** builds with no final-pass warnings or box errors. Pages
**105--108** were visually inspected; all **54 earlier proof blocks** are unchanged
and **196 labels** are unique. Uniform arbitrary-CNF discovery, compact closure
and lifetime acquisition/storage bounds remain open.

## Checkpoint: terminal signed subsumption and its acquisition cost (9 November 2026)

The user's request to identify and work on the largest gaps led to integration
of the seven saved signed-subset opportunities. `SignedSubsumptionInventory`
extends the activity policy only at exhausted unresolved leaves. Every removal
has a retained signed source clause; complete index coverage, deterministic
search, normalization, family evidence and model lifting are checked. Failed
searches persist, with no new probe phase or hidden recursive budget. Earlier
policies, results and proofs remain available. Implementation/proofs and the
selected nine-source pilot are committed and pushed in **9924740**.

The [full study](../experiments/results/cnf-signed-subsumption/README.md) retains
all 1,425 old queries and adds 36 controls/holdouts. Non-tiny closure rises **833
-> 837 / 949**, with gains **977, 1044, 1053, 1365** and no losses. The old subset
rises 806 -> 810 / 913; both modes close 27/36 new queries. The ordinary solver
is unchanged and agrees in every mode, with 20,544 residuals per full archive.
Closure refers to recognized structural leaves, not satisfiability.

The gain has a broad-sample cost regression. Total operation time grows
**145.71977 -> 156.17943 s**, discovery **105.46141 -> 117.30413 s**, SQLite
**404.410 -> 408.302 MB**, cold replay **61.80056 -> 66.82085 s**, and six-case
Python peak **19.997 -> 20.390 MB**. Pattern nodes fall 24,367 -> 24,122, but
logical node bytes grow 161.206 -> 166.021 MB. Balanced twelve-query trials
instead average 7.28617 -> 6.98024 seconds; these include all four gains and
are not a full-corpus estimate or significance result. Keep the policy optional.

Three concrete next gaps are now saved with evidence:

1. **Futile subset comparisons.** The 3,753 searches expose 31 local families and
   retain 3,722 failures. Discovery and checking each perform 33,367,619 tests.
   `pair-costs.json` identifies **27,083,138 (81.17%)** equal-width comparisons
   that cannot succeed for distinct normalized clauses. Add length filtering,
   preserve duplicate/non-normalized helper semantics or enforce its precondition,
   and check that all saved witnesses/coverage remain identical. This saving is
   prospective until measured; do not replace the preserved naive result.
2. **Reuse proved implications for representation changes.** `mechanisms.json`
   independently replays original probe traces and uses all their binary
   consequences, including binary-transitive ones discarded by current learning
   selection, as subset witnesses. Eight remaining leaves expose 2-CNF. Current
   plans for **1185/1289/1368** could close; five other sources retain another
   open leaf. Integrate after existing priorities and charge enumeration,
   witness/proof checks, normalization, persistence and cold replay. These are
   not counted as executed source gains.
3. **Repeated restriction/checking and retained state.** Source 1194 still takes
   1.60328 s discovery; its separate profile records 5,763 restrictions, 4,657
   simplification checks and 2,221 propagations. Search evidence alone adds
   3.706 MB, and cold replay remains expensive. Share exact prepared state and
   certificates only with explicit dependency/invalidation rules and total-cost
   measurement. There is no lifetime archive or full-process memory bound.

The remaining frontier contains **112 sources / 149 distinct leaves / 32,043
literal occurrences**. Efficient discovery and recomposition for their general
interactions remain open. The subset routine has expected O(L + m log(m+1) + m²w)
work and O(L+m) temporary space per eligible CNF, with equally charged replay;
this is not an unrestricted-SAT efficiency claim or bit-machine refinement.

All **395 tests** pass. Three new Lean lemmas establish signed subsumption,
model equivalence and arbitrary extension on disappearing variables; the full
axiom audit passes **4,129 declarations / 1,971 theorem declarations**. All three
full, three pilot and three previous archives replay byte-identically; warm
reuse inserts nothing. Both reports have **56 matching fingerprints**, and the
mechanism, timing and pair-cost diagnostics have verified input/script hashes.

Manuscript Section **12.61**, Proposition **12.43** and Table **22** distinguish
the proved reduction, four measured gains, broad cost regression and unintegrated
implication opportunities. All **54 previous proof blocks** remain; there are
55 proofs and **199 unique labels**. The **116-page PDF** builds with no final-pass
warnings or box errors; pages **107--110** were rendered and visually inspected.
The ranked priority, discovery and resource records and README are updated for
the next run. No Python refinement, universal compact closure or P-versus-NP
conclusion is asserted.

## 2026-11-09: indexed witnesses and original implication exposure

The implementation/proof checkpoint **f978ad4** is committed and pushed. The
user's hourly-prompt correction was applied separately: the active hourly schedule
now has one concise paragraph pointing to the repository's gap analysis, with
flexibility to choose the next useful step and notifications only for meaningful
progress or blockers. Detailed procedures stay in this record and study files.

`ImpliedSubsumptionInventory` skips futile equal-width subset comparisons while
preserving the old first-retained witness; exact duplicates use a lookup and
repeated literals use the old fallback. Indexing-only mode keeps old archive
identities. A separate optional implication policy first preserves old exposures,
then uses every distinct absent binary from original probe traces as a potential
subset witness, including binary-transitive clauses filtered from learning. No
fresh propagation pass is added. Original reasons precede origin reconstruction,
subset checking, recognition and model lifting. Failed pools/searches persist.
The four-clause learned batch cap is unchanged; the additional subset-witness pool
has separate charged size b<=U, where U is original unit-trace length.

The [full study](../experiments/results/cnf-implied-subsumption/README.md) retains
1,461 old inputs and adds 36 controls/holdouts. Non-tiny closure rises **864 ->
869 / 985**, with gains **857, 1185, 1289, 1368 and 1467**, no losses, and every
independent solver answer unchanged. Old-subset coverage rises **837 -> 841 / 949**;
new-query coverage **27 -> 28 / 36**, including 15 -> 16 / 24 new random 3-CNFs.
This is checked structural coverage, not satisfiability or a faster SAT decision
procedure. The deliberately selected twelve-source pilot and old results remain.

Full single-sample total time is **169.84716 -> 169.80609 s**, discovery **127.44196
-> 126.71711 s**, SQLite **438.288 -> 437.621 MB**, and cold replay **71.70525 ->
69.97623 s**. Logical node bytes instead grow **178.289 -> 179.396 MB** despite
nodes falling **25,752 -> 25,047**. Six-case Python peak grows **20.390 -> 21.161 MB**.
Twelve-query ABBA BAAB means are **6.99619 -> 6.17832 s** total; these include three
gained sources and are not repeated full-corpus estimates or significance evidence.
Keep the candidate optional. All benchmark modes, allocations, profiles and
repeated timing controls ran sequentially after verification completed.

The separate indexing-only audit replays **24,122 old nodes / 1,429 sources** with
identical bytes and no inserts. Its 3,753 terminal checks reduce subset comparisons
**33,367,619 -> 6,284,481**, removing **81.17%** of pairs with identical certificates.
Its standalone node replay is 51.15654 s, excluding file preparation and source
binding replay; do not compare it directly with a full cold audit including
ordinary solver certificates. Expected indexed search is O(L+m log(m+1)+P w),
temporary space O(L+m), with P=O(m²) still possible. This does not improve an
unrestricted-SAT worst-case bound.

The new policy has 3,916 terminal searches, 110 local exposures (28 original,
82 implied), 3,684 nonempty pools and 29,897 binary clauses. Search evidence grows
**3.963 -> 9.030 MB**, including **5.087 MB** of implication data. The saved offline
relevance control retains only proved binaries fitting a long clause of the
original minimal core: **29,897 -> 7,505 (74.90%)**, all 82 observed exposures
preserved, **zero new frontier leaves**. It costs 2,278,253 relevance comparisons;
augmented subset tests fall 8,990,250 -> 7,138,675 per search/check. Integration,
end-to-end timing/storage and general syntactic family preservation remain open.
Do not count this as new executed coverage or a total-cost saving.

The next priorities have concrete evidence:

1. **Repeated restriction and proof checking.** Source 1194 remains the largest
   unresolved discovery case at 1.67226 s. Its separate profile again has 5,763
   restrictions, 4,657 simplification checks and 2,221 propagations, dominating
   own time. Share exact prepared clause/assumption or proof state with explicit
   source binding and invalidation; compare acquisition, persistence and cold replay.
2. **Unresolved structural interactions.** The enlarged frontier contains **116
   sources / 148 leaves / 33,651 literals**. Existing-pool relevance filtering
   adds no coverage. Test new source-entailed relations or exact decompositions,
   charging discovery and recomposition. A larger blind budget is not a structural
   explanation, and an unresolved category is not an efficient solver.
3. **Useful pools and shared evidence.** Integrate relevance filtering only with
   checked origins, preserved old results and all recognition costs; recorded local
   preservation is not a universal family-preservation theorem. Source references
   may reduce duplicated failed evidence, but lifetime archive and full-process
   memory bounds remain open.

All **403 Python tests** pass. The Lean lemma
`signed_core_of_entailed_batch_models` composes entailed augmentation and signed-core
model equivalence; the full build audits **4,130 declarations / 1,972 theorems**.
It does not refine Python's encodings, checker, persistence or costs. All three
full, three pilot and three previous archives replay byte-identically, including
all alternatives and sources; full modes retain **21,838 solver residuals**. Warm
reuse inserts nothing. Both new reports have **59 matching fingerprints**; all
mechanism, timing and index-control script/input hashes were verified.

Manuscript Section **12.62**, Corollary **12.44** and Table **23** record the semantic
composition, five measured gains, mixed resource effects and unintegrated pool
opportunity. All **55 previous proof blocks** remain, with 56 proofs and **202
unique labels**. The **118-page PDF** builds without final-pass warnings or box
errors; pages **109--112** were rendered and visually inspected. README, ranked
priorities, discovery and resource records are updated. No unrestricted efficient
partition, universal compact closure or P-versus-NP conclusion is asserted.

## 2026-11-09: bounded reuse of exact successful probe checks

The profiled restriction/checking bottleneck led to a narrow exact-reuse change.
`CheckedProbeReuseInventory` wraps the existing complete probe checker in an
optional ephemeral LRU cache. Keys serialize the full source, proof and config;
only successful checks admit results, and hits return fresh decoded values.
Edits miss, eviction requires rechecking, and cold replay begins empty. There is
no object-identity shortcut, partial signature, unchecked hint or persistent
policy change. Implementation, seven new tests and pilot/counterexample records
are committed and pushed as **9aba9df**. The hourly automation prompt is unchanged.

Two failures are preserved. The first full harness compared live tuple-containing
profiles with JSON-loaded lists; comparison now uses the exact canonical JSON
encoding. Subsequent review found that the preliminary cache could identify a
malformed tuple of original attempts with a valid list and bypass the old checker
on a warm hit. Non-list attempts now go to the original checker before cache
lookup. A regression test warms the cache then requires rejection. That full run
was intentionally interrupted before any completed full report. Preliminary code,
tests, pilot and logs remain; the final guarded pilot has fresh measurements.
The full runner also keeps extra pointwise checks out of the timed query stream
so they cannot supply uncharged cache warmup. Tests and the identical prior
archive retain that independent small-fiber validation.

The [full matched study](../experiments/results/cnf-checked-probe-reuse/README.md)
uses all **1,497** previous inputs. Both modes reproduce every answer, structural
profile, root identity and database byte. Coverage stays **869/985 non-tiny**,
with **116 sources / 148 distinct selected leaves / 33,651 literals** open. This
is cheaper repeated checking, not new structural coverage or a change to the
independent SAT decision solver. The archive is referenced once rather than
copied: **437,620,736 bytes**, 25,047 pattern nodes, 1,465 source bindings and
21,838 ordinary solver residuals. Both full and all five guarded pilot modes
replay cold byte-identically, including every alternative/source/solver proof;
warm replay inserts nothing.

Full single-sample total time falls **168.30879 -> 150.39216 s (10.65%)**, discovery
**125.59834 -> 108.60557 s (13.53%)**, and cold replay **71.60183 -> 62.58623 s (12.59%)**.
The six-case Python peak grows **21,161,086 -> 22,258,162 bytes**, a 1,097,076-byte
increase. Logical node storage is unchanged at 179,395,726 bytes. The 1 MiB cap
bounds retained serialized cache strings only, excluding allocator/LRU overhead,
transient construction, native SQLite/RSS and the original acquired state.

Twelve-query ABBA BAAB controls average **6.17550 -> 5.33388 s** total and
**5.88231 -> 5.04230 s** discovery. Four cached totals (5.27161--5.38252 s) are below
four baseline totals (6.11412--6.22190 s); unchanged solver means are 0.29174 ->
0.29045 s. Answers/summaries match the full study; within-mode counters, storage
and database hashes repeat. These selected synthetic measurements do not establish
significance, industrial performance or repeated full-corpus estimates. Benchmark
modes, allocation diagnostics, repeated controls and profiles ran sequentially.

Full operations make **57,798 lookups / 34,971 hits / 22,827 misses/admissions /
22,571 evictions**. They serialize 135,220,528 key bytes and 22,273,703 result
bytes, decode 29,375,582 bytes on hits, and admit 78,031,066 total string bytes
while retaining at most 1,048,576. Probe replays fall **248,307 -> 113,301**;
restriction visits **126,081,638 -> 82,210,169**; simplification reconstruction
visits **82,973,454 -> 51,574,914**. Propagation visits stay **105,860,805**.
Cold replay starts empty and has 17,266 hits / 40,357 lookups, reducing verified
probe attempts **181,314 -> 115,029** without skipping any first check.

The next priorities follow the saved profile and unchanged frontier:

1. **First-time propagation and remaining scans.** The largest baseline miss,
   source 1194, reduces restrictions **5,763 -> 3,399** and simplification checks
   **4,657 -> 2,303**. Propagation stays **2,221 calls** and becomes the largest
   named own-time cost. Test occurrence-index preparation and affected-clause
   propagation across assumptions. Bind indexes to the exact source; preserve
   or explicitly version proof order because traces affect later learning choices.
2. **Broader structural discovery.** The 116 open sources still need new
   source-entailed relations or exact decompositions. Neither this cache nor the
   saved implication relevance filter adds frontier coverage. Charge recognition,
   recomposition and unresolved interaction; a complete partition is not an
   efficient solution of every class.
3. **Smaller retained overhead.** The guarded eight-source pilot gets 1,385 hits
   at 256 KiB versus 1,387 at 1 MiB. Compare full-corpus costs before choosing a
   smaller capacity. The unintegrated 29,897 -> 7,505 implication-pool filter is
   another evidence-size opportunity, with its relevance comparisons charged.

All **410 tests** pass. Lean sources are unchanged from the preceding audit of
**4,130 declarations / 1,972 theorem declarations**; no new formal Python
refinement is claimed. The final full report has **62 verified fingerprints**;
both pilot reports resolve all 62 through current files or preserved snapshots.
Timing/profile hashes and the actual referenced gzip archive hash are verified.

Manuscript Section **12.63** and Table **24** record the cache invariant, its found
counterexample, charged recognition/storage costs, measurements and remaining
propagation/coverage gaps. All **56 previous proof blocks** remain; there are
**204 unique labels**. The **120-page PDF** builds without final-pass warnings or
box errors, and pages **111--114** were rendered and visually inspected. README,
ranked priorities, discovery and resource records are updated. No new tractable
family, compact closure or unrestricted-SAT worst-case improvement is asserted.

## 2026-11-09: affected-clause propagation with identical proof order

Implemented `OrderedPropagationInventory` over the existing 1 MiB check-cache
inventory. Simplification discovery uses an occurrence index and events ordered
by scan round and clause ID; the independent checker and ordinary SAT solver
stay unchanged. Exact order matters because different unit/conflict traces can
change later learning choices. Context-scoped selection restores the prior engine
on nesting and exceptions. The reference engine and all earlier results remain.

The [full study](../experiments/results/cnf-ordered-propagation/README.md) preserves
all 1,497 answers/profiles and the complete prior database bytes. Coverage stays
869/985 non-tiny, with 116 unresolved sources. Discovery falls 111.13169 ->
97.76173 s; balanced subset means are 5.08503 -> 4.55072 s. Total full time
154.63114 -> 137.59078 s includes variation in the unchanged solver. Cold replay
barely improves (63.40473 -> 62.61754 s); six-case Python peak rises by 216,400
bytes. SQLite stays 437,620,736 bytes. No new duplicate full archive is retained.

All 417 tests pass, including 9,724 exhaustive ordered small formulas, 3,000
random edits, all 148 saved frontier probe discoveries, archive identity and
independent reason checks. Both modes fully replay cold unchanged. The manuscript
adds an algorithm-level trace proof, preserving all 56 previous proof blocks;
Lean files remain unchanged and were not rebuilt. The full/pilot reports each
have 66 fingerprints. Thirty-two controls preserve strong reverse-chain gains
and early-conflict, forward-chain and hash-collision regressions. They prevent a
pointwise speed or unconditional word-cost claim.

Next: restriction is now the largest named own-time cost on source 1194, with
3,399 calls and 0.82048 s cumulative; simplification checking has 2,303 calls and
0.54588 s cumulative. Share exactly bound source/assumption state and residual
reconstruction, accounting for construction, invalidation and first-use costs.
Per-call occurrence indexes are still rebuilt; short conflicts expose wasted
preparation. Broader certified coverage and unrestricted SAT obligations remain
open. See [the current ranked record](structural-reuse-priorities.md).

## 2026-11-09: immutable-source occurrence reuse for restriction

Implemented `IndexedRestrictionInventory` above ordered propagation. A bounded
cache retains only sources validated as exact immutable tuple/tuple/nonzero-int
objects and their signed occurrence lists. Hits require the same strongly held
source; mutable/unusual/oversized inputs use the old scan, edits or separate equal
objects prepare afresh, and eviction/restart lose index reuse. Unaffected immutable
clause tuples are shared in the returned ordered residual. No proof verdict or
assignment result is cached, and the independent simplification checker is unchanged.
Indexed branch construction remains a trusted Python step, not a new Lean refinement.

The [full study](../experiments/results/cnf-indexed-restriction/README.md) preserves
all 1,497 answers/profiles and prior archive bytes. The first sample improves
discovery 93.85938 -> 90.65563 s and cold replay 60.86819 -> 56.04772 s, but total
regresses 132.36551 -> 134.44214 s as the ordinary solver phase also varies.
Selected ABBA BAAB mean total is 4.81769 -> 4.35747 s; a reversed-order full
comparison is retained separately to assess the mixed full result. Six-case
Python peak grows 1,598,364 bytes, and retained memory grows 1,285,252 bytes.
SQLite is still exactly 437,620,736 bytes, referenced rather than duplicated.

All 425 tests pass, covering 87,516 exhaustive formula/partial-assignment pairs,
4,000 random/edited restrictions, types/mutation, source lifetime, fallback/caps,
sharing and old archive replay. Both modes check all evidence cold unchanged.
Full/pilot reports each have 70 fingerprints; separate profiles, timing and
32 locality controls preserve favorable reuse and equal/new-source regressions.
The manuscript adds an algorithm-level correctness argument and preserves all
57 previous proof blocks; Lean sources are unchanged and were not rebuilt.

The cost target has shifted: restriction on source 1194 falls 0.82784 -> 0.21269 s
cumulative; simplification checking remains the largest named own-time cost, with
2,303 calls and 0.55562 s cumulative. Full reconstruction still visits 51,574,914
literals. Broader coverage remains 869/985 non-tiny, with 116 unresolved sources;
new certified relations or exact interaction decompositions are still required.
Retained-space reduction, independent checker reuse and exact new-source/append
preparation are recorded in the current ranked gap analysis.

The full reverse-order control is complete. Across two samples per mode, means
are 137.36963 -> 131.36045 s total, 97.29044 -> 89.16122 s discovery and 61.16937 ->
56.70501 s cold replay (4.37%, 8.36% and 7.30% reductions). All within-mode operation
counters and archive hashes repeat. The reverse allocation repeats the roughly
1.60 MB Python peak increase. These limited synthetic samples balance order but
do not erase the initial regression, establish significance or justify universal
speed claims. Both complete reports and the order-control hashes are preserved.


## 2026-11-09: one-pass independent reconstruction and the next coverage target

The [matched study](../experiments/results/cnf-single-pass-check/README.md) replaces
repeated checker scans with a direct prefix-invariant reconstruction. It lazily
copies affected clauses and shares untouched tuples without another retained cache.
Unit reasons, conflict and fixed-point checks, pure rounds and source bindings
remain independent of discovery. Default scan behavior and all previous evidence
are preserved. The proposed clause-support cache regressed in both pilots; its
code, exact snapshots and unsuccessful experiments remain available but unselected.

On 1,497 inputs, discovery falls 93.90373 -> 87.70857 s (6.60%) and total
137.78680 -> 130.04664 s (5.62%). Cold replay regresses 57.32273 -> 57.93447 s;
warm replay also increases. Six-case Python peak is essentially unchanged at
24,072,934 -> 24,073,162 bytes. All answers, profiles, identities and persistent
bytes agree. ABBA BAAB subset means support 4.60% total / 5.23% discovery savings,
with overlapping trials. Five of 48 helper controls regress, including wide
clauses where every clause changes. No pointwise speed or total-memory win follows.

All 433 tests pass. New tests cover 175,032 exhaustive reconstruction-policy
combinations per candidate, full-checker policies, random edits, unusual inputs,
forged certificates, independence from discovery, all saved frontier proofs and
cold corruption rejection. Full cold audits replay 25,047 pattern nodes, 1,465
source bindings and 21,838 solver residuals, preserving the existing 437,620,736-byte
archive. The full report has 75 fingerprints; separate timing, profile, control
and frontier diagnostics bind their scripts and inputs. Implementation checkpoint:
`d0b8917`. All 58 preceding manuscript proof blocks remain, with one new invariant;
Lean sources are unchanged and were not rebuilt.

The current profile selects source 1446: reconstruction cumulative time falls
0.37732 -> 0.29957 s, while normalization remains 0.40226 s cumulative. The
reconstruction helper still has the largest named own time. Further implementation
reuse must preserve checked input identities and charge preparation; the rejected
cache shows why a high hit count alone is insufficient.

A separate read-only discovery probe identifies 35 of 148 selected unresolved
leaves as Horn after consistent polarity changes (852 of 33,651 literals). It
checks every positive flip and negative auxiliary implication refutation, and
matches exhaustive flip enumeration on 512 tiny formulas. This is an established
renamable-Horn test, not a novel class. Negative auxiliary results do not imply
UNSAT of the original CNF. Current integrated coverage stays 869/985 non-tiny,
with 116 source misses. The next priority is versioned recognition, checked
polarity/model transport and exact ancestor recomposition, followed by matched
acquisition, storage and cold replay. Most remaining literals lie outside these
small positive leaves, so broader interaction discovery remains necessary.


## 2026-11-09: the 35 polarity opportunities are integrated

Checkpoint **86d603b** adds a versioned terminal Horn-renaming edge, direct
positive Horn checking, source-linked negative auxiliary paths and a pre-enumeration
pair cap. Models lift through normalized names and a fixed polarity involution;
Lean proves evaluation and SAT/UNSAT preservation. The old policy and archives
remain available. Negative auxiliary proofs exclude a class, not original SAT.

The [1,497-source comparison](../experiments/results/cnf-polarity-horn/README.md)
closes 29 additional whole sources, with no losses (**869/985 -> 898/985 non-tiny**).
All 35 saved positive leaves close independently; 188 acquired edges pass endpoint
and model checks. The 87 remaining sources have 106 selected unresolved leaves
and 32,404 literals, each with a checked renaming exclusion. Every new whole-source
gain is itself excluded from renaming, demonstrating residual composition across
source categories. Earlier decomposition priorities and budgets remain intact.

Single-run discovery is 80.78495 versus 84.99193 s; total 122.78419 versus
126.02211 s; cold replay 51.32492 versus 54.89246 s. Warm replay regresses. Fresh
SQLite is 417,370,112 versus 437,620,736 bytes; six-case traced peak is 20,286,004
versus 24,073,154 bytes. Historical archives still consume retained space. All
441 Python tests and the full Lean audit pass (4,136 declarations / 1,977 theorem
declarations). All 59 earlier manuscript proof blocks survive.

Next: exploit the saved non-renaming obstruction paths to find shared-variable
interfaces or conditioning choices that expose different tractable residuals,
with matched budgets and exact recomposition. Repeated recognition alone cannot
undo those exclusions. The remaining sources take 70.6% of discovery time;
normalization/reconstruction and indexed subset certificates are supporting cost
gaps. Repeated/industrial evaluation, full-process memory, policy-independent
storage sharing and unrestricted efficient coverage remain open.


## 2026-11-09: obstruction-only conditioning is not promoted

The [106-leaf experiment](../experiments/results/cnf-obstruction-frontier/README.md)
adds checked source-path ranking as an optional policy, with persistent certificates,
independent checker replay and unchanged candidate/branch/probe limits. Giving
both modes one additional conditioning level closes 60/106 under the retained
policy and 57/106 under the candidate. Its three gains and six losses are preserved;
discovery rises 5.10% and SQLite from 35,840,000 to 37,498,880 bytes. This negative
result does not change original-source coverage (898/985).

Checkpoint **d25a2e5** preserves both full archives, exact changed source/choice
records, a guarded-support counterexample and separately checked original-probe
influence. Five lost old winning variables lie outside the recorded obstruction's
support. In case 4, already-acquired unit traces show indirect propagation into
that support, without fresh solving. Cases 17 and 50 remain counterexamples to
using that effect alone: their original closures leave the saved edges intact,
but later discovery still closes the branches.

All 448 tests pass, including source context restoration, cold checking without
SCC rediscovery, corrupted evidence and old-row preservation. All 60 previous
manuscript proof blocks remain; the new proposition only concerns untouched
obstructions under raw restriction. Lean sources are unchanged. Next test checked
propagation influence across families and portable reuse of successful plans,
with baseline diversity, explicit missing traces, matched budgets and fresh data.
Do not repeat this static-overlap heuristic or promote its favorable small memory
subset as a general result.

## 2026-11-09: reuse unit traces to reorder, preserve coverage, reject slowdown

Added optional `ProbeRankInventory`, reusing only original source-bound traces
and promoting one existing candidate while retaining the rest. No new probe or
auxiliary discovery is requested; checking reconstructs the order after validating
the original proofs. All 453 Python tests pass. New Lean lemmas establish set
membership and the local closure implication, without a Python refinement.

The [two-run frontier comparison](../experiments/results/cnf-probe-rank-frontier/README.md)
keeps 60/106 closures but discovery increases 5.19854 -> 5.44908 seconds; total
8.22342 -> 8.63390. Attempts stay at 268. Nodes fall 1,540 -> 1,524 while SQLite
grows 35,840,000 -> 35,979,264 bytes. The [fresh controls](../experiments/results/cnf-probe-rank-fresh/README.md)
keep 71/96 closures, with no changed candidate orders and effectively flat mean
time. Thirty-six of 39 branching states lack binary clauses; only 9/156 candidate
positions have paired traces. Archive bytes are reproducible across execution
orders, independently cold-checked, and preserved under warm replay. No policy
promotion or original-source coverage gain follows. Next investigate bounded
multi-variable interfaces or exposed binary relations, and portable successful
plans/direct proof transport instead of another scalar ordering proxy.


## 2026-11-09: retained binary paths, new closures and a scheduling counterexample

Added optional `BinaryPathInventory` and an independent source-linked checker.
Binary implication paths entail wider clauses; only those wide clauses are
removed, preserving all reasons for simultaneous deletion. Reachability searches
at most 64 roots per residual and stores shared proof prefixes. Cold checking
validates edges, endpoints, normalized children and exact summaries without
reachability rediscovery. The default `PolarityHornInventory` stays unchanged.

The [full comparison](../experiments/results/cnf-binary-paths-full/README.md)
raises structural coverage 898/985 -> 901/985, with four gains and one loss. All
ordinary answers agree. Discovery rises 81.47602 -> 97.00720 s; total 122.46371 ->
139.46329 s; SQLite 417,370,112 -> 475,529,216 bytes. The frontier gains three
closures beyond the direct-only control, while 96 fresh cases gain none. Every
archive, failed alternative, source and previous experiment remains preserved.

`loss-alternatives.json` isolates source 1471: after equivalent deletion, an old
successful variable-1 split disappears from a child's four-candidate list. The
old closure-invariance theorem requires unchanged membership and therefore does
not cover this change. Reusing the existing checked plan, instead of acquiring
both policy graphs, is the next concrete gap. The archive union 902/985 is an
observation, not an implemented efficient portfolio.

The full graph stores fewer proof-prefix nodes than separate paths (21,894 vs
25,359), but more positive JSON bytes (334,245 vs 230,535). Full-state acquisition
and preparation dominate the remaining cost. Shared preparation needs explicit
clause/name transport; hidden-literal elimination is another unimplemented
coverage experiment. See [proof, costs and limitations](binary-paths.md).

All 461 Python tests pass. Four new Lean lemmas prove retained binary edge/path
soundness, clause entailment and batch equivalence. Full build/axiom audit passes
at 4,148 declarations / 1,988 theorem declarations. All 62 previous manuscript
proof blocks survive, with one added proposition. No unrestricted-SAT bound is
claimed, and this higher-cost optional policy is not promoted.


## 2026-11-09: exact references preserve the old plan and reduce reacquisition

`RetainedPlanInventory` checks a positive old closure with the original verifier
and records an exact source/depth/policy reference before new binary-path
acquisition. It keeps the old graph and all failed alternatives unchanged. A
reference does not require the new scheduler to choose the old winning variable.
Corrupt source/policy/depth/profile bindings, false positive hints and missing
proof dependencies reject reuse. An absent or non-closed hint only skips reuse.

The [full prepared-history comparison](../experiments/results/cnf-retained-plans-full/README.md)
recovers source 1471: 901/985 -> 902/985, with no losses. Discovery falls 98.33619
-> 81.96656 s, total 190.63432 -> 177.05292, added SQLite 338,288,640 -> 211,906,560
bytes, and combined SQLite 755,658,752 -> 629,276,672. Original acquisition and
417,370,112 seed bytes remain liabilities. Cold replay falls 95.64397 -> 82.52345 s;
warm replay regresses 0.27327 -> 0.41059. Six-case Python peak grows 19.68%.
The fresh and empty-history controls keep 88/96 closures and regress in discovery.

Benchmark-only tuple/list assertions and a mixed-connection audit lock were
retained and fixed. Completed full acquisition and cold audits were recovered
from preserved checkpoints after finalization failed; the original runner is
frozen, all profiles/answers/hashes rechecked, and no acquisition timer estimated.
Both full archives and every seed row remain preserved. Eight new tests cover
proof reuse, the actual lost split, edits/corruption, small models and cold replay;
all 469 tests pass. Lean sources are unchanged; the full build/axiom audit passes.

The next large cost is a full metadata census in `ResidualSolver.solve` on every
query: a separate scan averages 57.14 ms over 21,838 rows. Avoid or maintain that
aggregate without changing decisions. Then reduce duplicated verifier state and
checking of historical failed alternatives, reject unprofitable trivial references,
and develop exact transport/upgrades beyond a fixed prepared prefix. The default
policy is unchanged. See [mechanism and limits](retained-plans.md).


## 2026-11-12: transactional residual accounting, measured and preserved

Implementation checkpoint `e32b33f` introduces optional `AccountedResidualSolver`;
the historical `ResidualSolver` remains the full-census control. Opening rebuilds
one counter row; triggers maintain it transactionally for normal residual writes.
Possible key/rowid conflicts invalidate it for locked reconstruction. Rollback,
legacy writers, Unicode/NUL SQL length semantics, cold reconstruction and partial
budget failures are tested. Direct alteration of private accounting state during
a live connection is outside the contract. No proof/search method is replaced.

All 476 Python tests pass. Full, fresh and empty matched comparisons preserve all
prior rows, match every per-query total, and produce identical evidence-table
digests. Query cost is 171.12270 -> 87.88366 seconds on prepared original inputs,
15.20412 -> 8.38678 on the fresh prepared controls, and 7.70202 -> 7.73052 without
history. All acquired results and six complete compressed archives are retained.
Added SQLite overhead is 4,096 bytes. Ordinary counters perform one opening census
and no per-query rebuild in these runs; independent validation scans are separate.

No coverage or underlying search gain is claimed. Discovery and duplicated
verifier state now dominate the measured prepared workload. Next: selected sound
proof reuse, shared/bounded checking state, useful-reference admission and plan
transport beyond exact prepared sources. See [mechanism and limits](residual-accounting.md)
and the updated [priority record](structural-reuse-priorities.md).

The unchanged Lean build/axiom audit passes at 4,148 declarations / 1,988 theorems.
Its first rerun exposed 16 missing sidecar files in the temporary toolchain;
only those files were restored from the digest-verified official release. The
failure and repair record are preserved with the full benchmark. The manuscript
adds the accounting invariant, measured costs and controls; all 63 previous
proof blocks remain unchanged. No Lean refinement of SQLite is claimed.


## 2026-11-12: reuse checked traces from old unresolved plans

Cost attribution of the accounted run shows the 83 unresolved inputs consume
67.35991 / 81.41598 discovery seconds. This changed the immediate target from
selected closed-proof validation to useful intermediate evidence from failed
expansion. Implementation checkpoint `836fb96` adds optional
`PreparedProbeInventory` and a no-op extension hook to the retained-plan reader.
Saved probe traces from an exact old open plan undergo the ordinary independent
source-bound check before replacing acquisition. No old closure, classification
or child graph is trusted. Pending hints are scoped and cleared on failures;
source/settings edits, corrupted evidence and empty history are tested.

All 481 Python tests pass, including 512 exhaustive tiny CNFs, seeded larger
inputs and preserved cold replay. The full matched run reuses 2,437 traces,
reducing fresh probe attempts 77,804 -> 60,972, but verification attempts remain
77,498. Discovery falls 79.80360 -> 78.51427 seconds (1.62%); total query time
85.97296 -> 84.07622. The unchanged solver accounts for part of that timing
variation, so it is not all avoided acquisition. All three evidence tables and full
database bytes match, every old row survives and both cold audits pass. Storage
stays 629,280,768 bytes; sampled Python peak slightly increases. No new coverage
is claimed: the optional prepared result stays 902/985, default 898/985.

See [full evidence](../experiments/results/cnf-prepared-probes-full/README.md)
and [mechanism and limits](prepared-probes.md). This acquisition optimization
has limited measured headroom while intermediate verification and other discovery
work remain. Next profile the expensive open expansions, then share exact checked
intermediate states or expose equivalent cores. Selected closed-proof checking
is still open, with a smaller measured cost ceiling than the unresolved inputs.


The fresh and empty controls each reuse zero traces and keep 88/96 closures.
Fresh total time regresses 7.70214 -> 8.61204 seconds; empty changes
7.59890 -> 7.43109. Identical operation counts make these controls evidence
against claiming a general benefit. All six compressed archives and every paired
record are validated. The unchanged Lean audit passes (4,148 declarations /
1,988 theorems); the manuscript keeps all 63 proof blocks, adds section 12.73,
builds without warnings and passes visual review of the changed pages.


## 2026-11-12: source-identity indexing fails to amortize preparation

Profiled the costly unresolved source 1194 from the old prepared archive. Independent
reconstruction is the largest individual Python own-time entry. Checkpoint `f6fb244`
adds an optional checker-owned occurrence index, with exact immutable source binding,
separate discovery/checker state and a shared 32,768-slot checker budget. All original
proof reasons and fixed points remain checked. It passed 487 tests before timing.

The 96-input empty-history control retains 88 closures and byte-identical databases,
but discovery regresses 6.36510 -> 6.63704 seconds and total 7.54255 -> 7.89263. Only
658/15,071 reconstruction calls hit. Preparing nearly every source adds enough work
to erase the avoided untouched-clause scans. Sampled Python peak increases. Both
complete archives and failed timing evidence are retained, not promoted.

A 32-fold capacity increase on source 1194 leaves 80/2,617 hits across both views.
An extra exact source/assignment restriction memo also fails in a three-way pilot:
1.12695 seconds current, 1.17052 indexed, 1.19950 combined. It gets 498 restriction
hits but only 141 checker-index hits. Three additional tests verify its reuse, type
fallbacks, budget behavior and byte-preserving replay; the full 490-test suite passes.

A no-eviction observer proves the measured identity limit is not eviction: 2,537
retained source identities contain only 2,167 exact CNF values, with 370 duplicate
admissions. Exact whole-source interning has limited headroom here. Next measure
reuse of unchanged clause blocks and checked deltas across related but unequal
residuals; avoid repeating the earlier per-clause cache regression. No full new
prepared-corpus benchmark was justified after these negative controls. Historical
optional coverage stays 902/985; no new coverage or unrestricted bound is claimed.

The unchanged Lean audit passes (4,148 declarations / 1,988 theorems). The manuscript
keeps all 63 proof blocks, adds section 12.74, builds warning-free and passes visual
review. [Mechanism and limits](indexed-check.md), [preserved diagnostics](../experiments/results/cnf-indexed-check-profile/README.md)
and the priority record retain the next target and the unsuccessful alternatives.


## 2026-11-12: shared-clause masks reduce scans but fail total-cost controls

Checkpoint `c7914b5` adds an optional independent clause-mask reconstruction
engine and observer. Two hard prepared sources share exact immutable clauses at
70.32% and 70.53% of visits. Only independently validated representation facts
are retained. A zero mask intersection proves no assignment overlap; collisions
require scanning. Every unit reason, conflict and fixed-point obligation remains
checked. Both checker views share a 32,768-slot FIFO, with no new persistent state.

All 496 Python tests pass, including exhaustive tiny reconstruction, arbitrary
large/colliding identifiers, mutations, malformed types, forged evidence and
byte-preserving cold replay. The three-source pilot is almost flat in runtime.
Two matched 96-input empty-history comparisons, in opposite execution orders,
reduce literal work including preparation 4,173,407 -> 1,873,711 (55.10%). Yet total
query time rises 7.37185 -> 7.56226 and 7.31352 -> 7.57542 seconds. Four-case peak
traced Python allocation rises about 41%. Counters outside reconstruction are
identical. Both modes close 88/96; all four 33,460,224-byte databases match exactly
and all cold audits pass without changing bytes. Every archive is preserved.

The candidate remains optional and disabled. No full prepared-corpus run was
justified. Historical default/optional coverage remains 898/985 and 902/985;
the new controls do not remeasure that corpus. Overlap alone is not a gain when
lookup, preparation, FIFO maintenance and output assembly consume the avoided
short scans. A coarser representation still needs stable proof-reason positions
and a concrete cost advantage. The revised priority is bounded checked variable
elimination on the unresolved frontier, followed by transport into shared cores.

The existing Lean audit passes (4,148 declarations / 1,988 theorems); all 63
manuscript proof blocks remain unchanged. Section 12.74 records the follow-up,
the PDF builds warning-free and pages 127--129 pass visual review. See
[mechanism and limits](clause-mask-reuse.md) and
[preserved evidence](../experiments/results/cnf-clause-mask-pilot/README.md).

## 2026-11-12: checked elimination closes 29 earlier misses at extra cost

Checkpoint `e7a806b` adds optional bounded Davis--Putnam elimination at unresolved
terminal nodes. A certificate identifies a pivot; the independent checker rebuilds
all opposing-pair resolvents and checks exact binding, pair and growth limits.
SAT models lift back to the source. A null proposal proves neither impossibility
nor UNSAT. Lean proves the existential projection identity under explicit pivot
absence conditions; Python normalization, persistence and costs remain outside
that formal result. All 501 Python tests and the 4,168-declaration / 2,004-theorem
Lean audit pass.

The matched 99-leaf comparison closes 0 / 14 / 37 leaves for baseline / pure-only /
bounded elimination. A separate run queries all 83 original prior misses from the
same paid prefix: 0 / 11 / 29 close, retaining every pure-only closure. The bounded
candidate leaves 54 original sources, 59 selected open leaves and 26,205 literals.
It does not rerun the full 1,497-input corpus. Query time rises 64.76503 -> 80.09857
seconds and database bytes 605,675,520 -> 621,146,112. No default policy changes.
Every old row survives, all six complete archives cold-replay without changes,
and independent endpoint/model checks cover all 1,728 pure-only and 2,822 bounded
original-input elimination edges. The latter diagnostic costs 688.09686 seconds
in addition to query and cold-audit time; it is retained as validation cost.

The next bottleneck is concrete: 167,129 candidate tests, 156,757 growth rejections
and 1,457,523 discovery pairs. Accepted mixed steps mostly have one occurrence on
one side (1,588, versus 111 with multiple occurrences on both sides). A single
binary occurrence gives a cheap sufficient non-growth rule, whose frequency and
ordering effects remain unmeasured. Exact target sharing is limited: 2,822 edges
reach 2,821 target keys. The remaining frontier has 58/59 leaves with pair-bounded
candidates but no non-growing step under the current rule. Ten admit a candidate
if retained-clause subsumption removes redundant new resolvents. This opportunity
is not yet integrated or an additional closure. Profile failed candidate work,
then test cheap admission and checked redundancy before increasing caps.

The [mechanism and resource account](variable-elimination.md),
[frontier comparison](../experiments/results/cnf-variable-elimination-frontier/README.md),
[original-source comparison](../experiments/results/cnf-variable-elimination-originals/README.md)
and [analysis/provenance](../experiments/results/cnf-variable-elimination-probe/README.md)
preserve the evidence and limitations. Section 12.75 records the result while
keeping every earlier manuscript proof block. The PDF builds without warnings;
pages 128--130 pass visual review. The aggregate validator confirms report and
runtime hashes, all six archive integrity checks, identical ordinary-solver
residual tables, all 63 unchanged proof blocks and 225 unique labels. No
unrestricted polynomial SAT bound or complete efficient structural partition is
established.

## 2026-11-12: subsumption fallback is correct but does not close more inputs

Checkpoint `14ae642` adds an optional retained-clause subsumption fallback after
ordinary bounded elimination fails. Every omitted resolvent names its two
parents and a source subclause that survives pivot elimination. The independent
checker visits all pairs, verifies those reasons, checks non-growth and binds
the complete child. Source/model lifting and all earlier obligations remain.
Lean proves subclause implication, redundant-clause removal and the corresponding
existential projection. All 506 tests and the 4,173-declaration / 2,009-theorem
axiom audit pass; Python refinement and costs remain separate obligations.

The matched 59-leaf comparison permits ten new subsumed elimination edges and
one following ordinary elimination, but closes none. Selected open literals
fall only 26,205 -> 26,181. Query time rises 2.88938 -> 3.12938 seconds, and
2.96506 -> 3.30563 in reversed order; per-mode archives match exactly. The
83-original comparison preserves exactly the same 29 closures, with time
79.65962 -> 88.16727 seconds and storage 621,146,112 -> 628,133,888 bytes. The
baseline archive reproduces the previous bounded run. The candidate acquires
324 subsumed edges across all retained alternatives, with 86,305 candidate tests,
85,902 growth rejections and 8,639,284 subset tests. All new edges have independent
endpoint/model diagnostics; the original-input diagnostic costs 33.47933 seconds
outside acquisition. All six archives cold-check unchanged and all old rows
survive. Existing-rule edges receive complete cold proof checks without repeating
their extra endpoint diagnostic in these runs. The fallback is not promoted.

A read-only ablation finds the larger opportunity: 48/59 remaining leaves admit
a candidate without increasing clause count if up to eight extra literals are
allowed, or 49/59 with subsumption. Fifteen plain candidates need only one extra
literal. None satisfies the present joint non-growth rule. For a normalized CNF
with m clauses and n variables, L <= mn; an elimination-only chain with at most
m0 clauses and decreasing variables from n0 therefore has at most m0*n0 literals
per intermediate CNF and at most n0 steps. This does not guarantee a next pivot,
a tractable endpoint or a bound on all retained branching history. The next
controlled test is plain clause-count-based admission, with exact checks and
explicit intermediate-width costs. No such policy or extra closure is claimed
by the diagnostic.

The [mechanism and limitations](subsumed-elimination.md),
[remaining-leaf controls](../experiments/results/cnf-subsumed-elimination-remaining/README.md),
[original-source comparison](../experiments/results/cnf-subsumed-elimination-originals/README.md)
and [aggregate validation](../experiments/results/cnf-subsumed-elimination-validation/README.md)
retain the failed experiment, complete archives and next target. The manuscript
adds section 12.76 while preserving all 63 previous proof blocks. Fresh holdouts
and a new full-corpus run were not justified by the negative controls; there is
no new unrestricted SAT complexity claim.

The aggregate validator also confirms identical ordinary-solver residual tables,
opposite-order per-mode archive equality, all six SQLite integrity checks,
runtime/report fingerprints and 226 unique manuscript labels. The PDF builds
without warnings; pages 129--131 pass visual inspection with final file hashes
recorded alongside the proof and test logs.

## 12 November: permit literal growth while bounding an elimination chain

Implemented `ClauseBoundEliminationInventory`, preserving the earlier joint
non-growth choices and trying a clause-count-only fallback at unresolved
terminals. Complete opposing-pair reconstruction, strict support decrease,
exact child binding and SAT model lifting remain independently checked. All
**511 Python tests** pass, including exhaustive small projection, random edits,
large signed identifiers, explicit growing-literal examples, clause-growth
rejection, history preservation and corruption checks. Lean's audit passes
**4,195 declarations / 2,018 theorems**; `ClauseBoundElimination.lean` proves
conditional per-formula, chain-length and formula-state payload bounds.

The 59 post-subsumption leaves yield one closure versus zero, at higher time and
storage. Whole-source recomposition on the 83 prior misses yields **31 versus
29 closures**, with no losses; the two gains are distinct 48-variable sources.
There remain 52 original misses and 57 selected leaves / 25,488 literals. Query
time grows **78.06321 -> 113.63899 seconds**, complete archive bytes
**621,146,112 -> 674,234,368**, and newly added bytes above the common prefix
**203,776,000 -> 256,864,256**. Every old row survives. The baseline reproduces
the earlier bounded archive exactly. Complete cold checking preserves bytes;
all 2,504 new edges pass independent endpoint solving and SAT model lifting.

The new endpoints cost **961.43125 seconds** to diagnose. The diagnostic still
uses `ResidualSolver` and its per-solve SQL census; ordinary queries use the
already optimized `AccountedResidualSolver`. Census versus solving time is not
profiled here. Do not hide the diagnostic phase or attribute all of it to the
new discovery policy. Four-case Python allocation is only a sample, not a
full-history or native-memory bound.

There is still no admissible-pivot availability theorem or efficient complete
elimination-order search. The rule tests 166,437 additional candidates and
rejects 162,187 for clause growth. A fixed opposing-pair cap B would also keep
an accepted elimination-only chain within m0+B*n0 clauses if clause growth were
allowed; this looser policy remains unimplemented. Recognition, alternatives,
persistence and the final fallback remain separate from that formula bound.
See [the full mechanism and limitations](clause-bound-elimination.md).

## 12 November: checked additive growth, with a negative coverage result

`AdditiveEliminationInventory` and `AdditiveElimination.lean` implement and bound
fixed per-step allowances of one and two clauses after earlier non-growth rules
fail. Every projection has complete opposing-pair checking, strict support
decrease, exact target binding and checked model restoration. Prior rows and all
failed alternatives are preserved. All **516 tests** and the **4,216-declaration /
2,028-theorem** Lean audit pass. The chain bounds remain conditional and do not
establish an efficient arbitrary-SAT construction.

The [matched evidence](additive-elimination.md) is negative for the intended
coverage gain: zero new closures on 57 final leaves or 83 original prior misses.
All original modes close the same 31. Query time rises from 121.61751 to 142.26465
and 163.21184 seconds; acquisition bytes rise from 674,234,368 to 700,178,432 and
734,814,208. The added rules acquire 1,021 and 2,530 independently checked edges.
Reference endpoint proofs, models and answers now persist in separate archives;
the largest reference database occupies 1,236,189,184 bytes before compression.
It is charged separately from acquisition. No old solver evidence is replaced.

The current gap is useful order/endpoint discovery and avoiding unsuccessful
repeated recognition. Valid steps and a small formula bound are insufficient
progress criteria. The ranked [priority record](structural-reuse-priorities.md)
retains the controls, limits and next target. Default policy remains unchanged.

## 12 November: required-literal filtering preserves exact subset certificates

Added optional anchored subset inventories, leaving the earlier runtime classes
and archives intact. A retained nonempty clause is stored under one required
literal; candidate ranks preserve the earlier first-witness order. Empty clauses
and equal-width duplicates are explicit, with fallback for uniform-width and
repeated-literal inputs. Independent checking validates every witness and builds
its own index from the actual source. Original implication origins remain bound
to checked source traces. No cross-source answer cache or invalidation rule is
assumed.

The [retained study](anchored-subsets.md) records a negative whole-input cache
result, exact kernel comparisons and complete acquisition/cold comparisons.
All 521 Python tests and the Lean audit of 4,219 declarations / 2,031 theorems
pass. The three new abstract lemmas prove necessary-literal completeness and
first-match preservation, not Python refinement or machine costs. Coverage and
stored results are unchanged by design; new endpoint-producing discovery and
full-history memory bounds remain open.

The verified originals comparison reduces query time **155.78451 -> 139.68494
seconds (10.33%)** and cold checking **111.46828 -> 102.79093 (7.78%)**, with the
same 31/83 closures and 734,814,208-byte archive. The repeated control improves
query time by 4.67%, with unchanged 88/96 coverage and bytes; cold time and sampled
allocation are essentially unchanged. Reversed leaf order also favors the index.
All eight cold runs and three unique acquisition archive integrity checks pass.
The source/report validator preserves all 63 earlier proof blocks and checks 229
unique labels. The 142-page PDF builds without warnings; pages 133--135 pass
visual review. Evidence and failed cache/control ideas persist in the linked study.

## 12 November: bounded pivot deviations and exact descendant reuse

Implemented optional search over four earlier open elimination ancestors and
at most eight fully recognized target projections per open source. Complete
projection checking, exact target/name binding and independent trial replay
protect every alternative. Old nodes remain immutable, while original-source
recomposition checks component conjunction and both conditioning branches.
The search persists all acquired target histories and unique trial records as
an exact-base-bound delta. No default recognizer, ordinary solver or formal
source is changed. All **527 Python tests** pass.

The first original-source experiment makes **316 trials**, adds **602 pattern
nodes**, and retains **31/83** closures with no gains. **295/316** trials reach
the exact same selected frontier; 271 pivot pairs share no source clause, with
260 exact reconvergences. The interaction-priority follow-up raises interacting
trials **45 -> 74**, adds 660 nodes, but also gains no closure. Resident expansion
costs **6.45902 / 7.11551 seconds**, with initial and cold verification charged
separately. New delta SQLite bytes are **15,208,448 / 16,248,832** over the same
734,814,208-byte paid base. Repeated controls remain 88/96 in both schedules.
The [full study](pivot-alternatives.md) retains phase costs, failed attempts and
limitations. Coupled continuations, later ancestor selection and an explicit
new-state budget remain the next discovery gaps.

Both schedules' proof deltas also combine without conflicting payloads. The
original-suite union retains 708 distinct new pattern nodes / 345 trials, sharing
554 node rows and 287 trial rows between schedules. Repeated-control union counts
are 121 new nodes / 45 trials. The persistent resume recipe and logical table
hashes are in the study and validation record; later runs should reuse this union
rather than discard the unsuccessful acquisitions. Every constituent graph has
passed full cold checking. The final PDF preserves 63 existing proofs, has 230
unique labels, builds without warnings and passes visual review on pages 135--137.

## 12 November: reuse failed trials and test later elimination ancestors

Implemented a near-frontier ancestor schedule and a matched early-ancestor
control, both starting from the exact union of the two prior pivot histories.
Prior source/pivot/configuration trials are independently checked and reused;
only new trials spend the eight-entry budget. All old rows, including trial
records, are protected against modification. New deltas are relative to that
merged seed, with exact reconstruction, idempotence and cold/trial checks.

On selected originals, early search acquires 145 trials / 266 nodes and frontier
search 102 / 90; coverage remains 31/83. Frontier acquisition costs 1.75051 seconds
versus 3.76670, with fewer trials and separate 64--68-second seed verification.
Its new SQLite delta occupies 3,018,752 bytes versus 6,807,552. Repeated controls
add 10 / 12 trials and retain 88/96. These are negative coverage results, not a
solver speedup. The [study](frontier-pivots.md) records the preparation, graph
traversal, cold replay, storage and discovery limitations. Next: bounded coupled
continuations at retained divergent states, rather than an unmotivated larger
one-pivot sweep. No formal or manuscript theorem was changed.

All **531 tests** and the artifact validation pass. The two new original deltas
combine without conflicts, sharing 57 pattern rows / 29 trial rows. Their union
adds 299 unique pattern nodes / 218 trials; the complete original history now
retains 41,299 pattern nodes and 563 trials. The repeated-control union adds
25 nodes / 20 trials, reaching 24,982 nodes and 65 trials. The study's latest
resume recipe and validation digests preserve this work for the next iteration.
