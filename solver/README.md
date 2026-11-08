# Persistent checked SAT service

Every completed SAT or UNSAT verdict is retained. SAT means that a valid formula
is satisfiable; UNSAT means it is unsatisfiable. A malformed encoding is an error,
never an UNSAT verdict. SAT records retain satisfying assignments. UNSAT records
retain checked refutation trees, LRAT proofs, or certificates that the compiled
circuit simplifies to false. Results and certificates survive restarts without
eviction.

## Build and use

With the pinned Lean toolchain available, run from the repository root:

```sh
./solver/build.sh
python3 solver/persistent.py solve 010
python3 solver/persistent.py solve 010
python3 solver/persistent.py solve 0101010
python3 solver/persistent.py stats
python3 solver/persistent.py audit
python3 solver/persistent.py revalidate
```

The build helper records the toolchain's bundled CaDiCaL path locally. The
measured version is 2.1.2 with ASCII LRAT output. The default `--backend auto`
uses verified simplification and a bounded local attempt before calling
CaDiCaL. `--backend cadical` skips that local search; `--backend lean` retains
the counted lazy solver. Set `ORACLE_CADICAL` or pass `--cadical /path/to/cadical`
to choose a compatible binary. Without CaDiCaL, `auto` uses the complete lazy
fallback. An external timeout (default 30 seconds, configurable with `--timeout`)
returns an error and stores no SAT/UNSAT verdict.

`010` encodes variable 0. The first call solves it and retains witness `1`.
The second retrieves the exact result. `0101010` is its double negation; the
stored witness can certify that different input. `0100101011` encodes
`x0 AND NOT x0`. The [encoding](../formal/OracleMachines/Encoding.lean) uses
binary postfix instructions and unary variable indices.

Keep the service warm for multiple queries:

```sh
python3 solver/persistent.py serve
```

Send one JSON object per line, for example `{"bits":"010"}` or
`{"bits":"0101010","learn":false}`. Each line gets a result or error; EOF closes
the service. One process keeps SQLite and the native checker open and amortizes
engine fingerprinting. Every newly acquired result still commits before its
response. `learn:false` disables cross-formula proposals and active-witness
updates, while exact results are still retained and reused.

## Checked acceleration

The automatic policy tries saved proposals, shared circuit simplification,
all-false/all-true witnesses, and up to 64 local search nodes. Exhausting this
node budget means no answer yet. Every successful local proposal is independently
checked. The policy then invokes CaDiCaL, which supplies mature unit propagation,
watched literals, clause learning, restart and phase heuristics, preprocessing,
and inprocessing. This integration uses its default techniques; it does not
implement every SAT algorithm or guarantee that one policy wins on all inputs.

[CDCL.lean](../formal/OracleMachines/CDCL.lean) proves that our cached AND/inverter
graph preserves the original formula's value. Lean's standard library provides
the CNF translation theorem and LRAT checker. A SAT model is checked directly on
the original formula. An UNSAT proof is checked against CNF reconstructed from
that formula. A CaDiCaL verdict, exit status, or temporary DIMACS file is never
sufficient for acceptance. Invalid certificates, failed subprocesses, and
timeouts store no answer. This is soundness of completed answers, not a
termination guarantee under finite service budgets. The standard-library
theorems compose directly, without a native-decision axiom; the axiom audit passes.

Identical gates share circuit nodes; constants and complementary terms simplify.
A proof can transfer across some syntactic changes, such as double negation,
but every transfer is checked on the current formula. An LRAT proof refers to
specific clause identifiers; arbitrary conjunction extensions need not preserve
it. SAT witnesses and tree proofs retain their respective reuse rules.

At most four stored witnesses and four stored proofs are proposed on each new
formula. An index of distinct proposals avoids scanning archived duplicates.
The active witness is tried first, followed by recent acquisitions. Proof
proposals are limited to 65,536 serialized bytes; larger proofs remain archived.
A bounded proposal count does not make certificate checking constant cost.
Exact hits avoid parsing and solving, and do not rewrite an unchanged active
witness. The default CaDiCaL path starts a new process per unresolved query.
The optional incremental path below retains internal clauses across queries.

## Persistence and trust

The default database is `solver/.cache/results.sqlite3`, which Git ignores.
Use `--cache /absolute/path/results.sqlite3` before the subcommand to choose a
durable location. SQLite transactions and full synchronization commit a new
result, certificate, and active witness together. WAL mode permits concurrent
readers and serialized writers. There is no automatic deletion of earlier
results; storage grows with the number and size of distinct queries.

Results are keyed by the complete binary input and SHA-256 fingerprint of the
compiled checker. When that binary changes, a new namespace is used and old
records remain. The process-local fingerprint cache is invalidated by a change
in file identity, size, or timestamps. `revalidate` solves older engines' inputs
with the current engine and commits each result. It never imports an old answer
as a current decision, removes old records, or invents historical proof provenance.
An interrupted replay can resume. Malformed or interrupted queries are never
stored as UNSAT.

The database is a trusted local store produced by this solver. Row checksums
detect accidental corruption; they do not authenticate against deliberate edits.
Exact hits trust that store. Cross-formula proposals are always checked afresh.
`audit` solves every current input with reuse disabled and independently checks
its saved witness or certificate. This can be expensive. Lean's functional
cache proof assumes a loaded cache satisfies the invariant established by prior
writes. Native compilation/runtime, Python, SQLite, JSON, process communication,
and disk integrity are outside the kernel proof. Copy an active database using
SQLite backup tools, or close all connections first to include its WAL contents.

Schema version 5 adds checksummed predictor states, retaining the version-4
distinct-proposal index and measurement table, the version-3 proof archive,
and all earlier result rows.
The version-1 migration adds parser costs; historical unmeasured parser costs
remain SQL `NULL`, never zero. Missing historical certificates are not invented.

## Accounting

With `--backend lean`, `core_work` is the abstract operation ledger of the
verified lazy evaluator and search; `parse_work` charges binary parsing, and
`counted_work` is their sum. Modern acquisitions instead return `core_work`,
`counted_work`, and `nodes` as JSON `null`, with `counted_complete:false`. CNF
construction, bounded preliminary search, CDCL, and LRAT checking have no complete
abstract ledger. Parser work alone is known, including both parses when an
external answer needs verification. It must not be interpreted as total work.

`wall_ns` includes query handling, IPC, verification, lookup, and committed
writes. `PersistentSolver.setup_ns` separately records connection and engine
fingerprinting time. External solves expose `external_ns`, `verification_ns`,
`cnf_clauses`, and `proof_bytes`; verification includes reparsing, proof/model
handling, and the native check. JSON, ASCII conversion, database operations, and
runtime costs are covered by elapsed time, not the old formal operation bound.

An exact hit has zero parser/core work because it runs no native query; lookup
and disk costs still appear in wall time. `original_acquisition_core_work`,
`original_acquisition_parse_work`, and `original_measurements` describe the
first acquisition, with unknown modern core cost exposed as `null`. The legacy
non-null SQL core-cost column uses a zero placeholder for modern acquisitions;
the measurement flag is authoritative. Consumers must use that flag or the public
interface, never interpret the raw placeholder as free acquisition.

## Counted lazy reference and native protocol

The lazy reference branches on distinct occurring variables, using three-valued
partial evaluation to close branches early. It never constructs a list of all
assignments. For example, `x100` needs three search nodes and returns a correctly
indexed 101-bit witness. A negative result carries a tree with checked partial
contradictions at leaves and both variable values checked at every split.
Lean proves the checker sound and the search complete, with at most
`2^(d+1)-1` nodes for `d` distinct occurring variables. A failing single assignment
is never evidence of UNSAT. Trees, search, and the durable archive can still be
exponential. Neither this reference nor the CDCL path proves a polynomial bound
for general SAT.

The old eager reference remains native mode `exhaustive`; `baseline` is lazy
search without proposals; `hybrid` enables checked proposals. Requests accept
`bits`, `mode`, `candidates` (at most four bit strings), and `proofs` (at most
four trees). The singular `candidate` field remains compatible. Tree proofs
are `"conflict"` or `[index, low, high]`. Earlier fixed-width coefficients and
single-witness overhead bounds describe their original implementations.

Modern requests use `prepare`, `verify_witness`, and `verify_certificate`.
LRAT certificates have `format:"lrat"` and a `text` field; constant-false
certificates have `format:"aig_false"`. The Python service handles CNF export,
external solving, and independent verification. Public `source` values are
`cache`, `fallback`, `verified_witness`, and `verified_refutation`; `fallback`
includes newly acquired results found by local preprocessing.

## Validation

```sh
python3 -m unittest discover -s solver -p 'test_*.py' -v
```

All 57 integration tests pass with both native binaries built. The original tests cover retention, restart,
engine namespaces, concurrent writers, corruption, schema migration, witness and
tree transfer, sparse indices, and 400 formulas compared with independent truth
tables and the eager reference. Accelerated tests add 120 seeded CNFs checked
against truth tables, valid and forged external models/proofs, wrong-formula
and malformed LRAT, timeouts, unavailable-solver fallback, search-budget
exhaustion, gate sharing, indexed retrieval, and the warm JSON-lines interface.
Tests use temporary databases; they never replace the persistent store.

## Live clause reuse and learned proposals

Build the optional CaDiCaL C++ bridge from the pinned official source:

```sh
git clone --branch rel-2.1.2 https://github.com/arminbiere/cadical.git /tmp/oracle-cadical
cd /tmp/oracle-cadical
./configure
make -j4
cd /path/to/OracleMachines
./solver/build_incremental.sh /tmp/oracle-cadical
python3 solver/persistent.py --incremental --learned serve
```

The build helper checks commit `3ff42f04384489916f017acd6d5e7cbfa7257be7`
and rejects modified tracked source. This bridge keeps shared Tseitin definitions
and CaDiCaL's learned clauses in a live process. Each query uses a root assumption;
the next query replaces that assumption. SAT models pass the original-formula
Lean checker. Negative proposals require a fresh standalone LRAT proof and check.
Consequently, this is not an incremental UNSAT certificate integration. Metrics
record retained clauses before/after solving and newly added definitions.
Selected internal state now survives restart. Schema 6 stores immutable,
content-addressed zlib objects: stable circuit definitions and deltas of learned
clauses. Each process forks a session; concurrent sessions never mix variable
IDs. Export keeps clauses of at most 64 literals, at most 4,096 per query;
restart replays at most 20,000 clauses, preferring short clauses. The 200,000-node
budget starts a new active session without deleting the archive. Solver
heuristics, activities and trails are not checkpointed. Restored clauses are
untrusted proposals; SAT still needs a checked model and general UNSAT still
needs independently checked LRAT. Replay and storage have real costs; these
limits are not a bound on the entire archive or peak Python memory.

`--learned` enables five shared bounded perceptron weights over syntactic literal
polarity features. Training uses only newly acquired, checked SAT witnesses.
Updates and result insertion share one transaction, including concurrent writers.
The predictor has bounded serialized parameters (under 256 bytes), survives
restart in the current engine namespace, and can propose new witnesses rather
than only retrieving old ones. This size excludes the growing result archive
and input features. Wrong proposals cause fallback; there is no UNSAT prediction,
general-SAT learning guarantee, or universal speedup claim. `learn:false` disables
the witness/proof portfolio and model updates, but an explicitly enabled
incremental engine still retains its clauses. `learned_witness` is an
additional result source.

## Structural expansion and component reuse

`--components` enables a separate, persistent structural policy. The service
splits top-level conjuncts into variable-connected components, renames their
variables by first occurrence and acquires each canonical component once.
Renamed copies reuse its witness or refutation. Positive witnesses are joined
only across disjoint variable sets and checked against the original formula.
A new connecting constraint merges components, so incompatible partial answers
are never simply combined. Normalization preserves term order: it does not find
arbitrary Boolean equivalences or graph isomorphisms.

Negative reuse checks a component certificate in Lean: paths must select actual
conjuncts, the selected conjunction must equal the renamed archived formula,
and its base proof must verify. This supports renamed cores and added
constraints without a fresh SAT search. A bounded index of four recent negative
instances also finds cores inside merged components. Deletion and negation do
not justify this transfer. Hashes and compression alone never certify answers.

Shared terms, shapes, variable maps and expansion-prefix nodes form an immutable
content-addressed DAG. Identical objects are stored once. The whole-query result
archive still retains original inputs and certificates; its growth is reported
separately. `learn:false` disables the portfolio/predictor, but explicitly
enabled component and incremental policies remain active. Component results
appear as `component_witness` or `component_refutation`, with hit/acquisition and
storage metrics. Partial checked components can remain after a query timeout;
no incomplete whole-query answer is cached.

`Components.lean` proves the more general bounded-interface composition rule.
The current runtime decomposition uses an empty interface; it does not yet
discover separators or construct nonempty interface tables. For fixed interface
width and local width, the abstract enumeration budget is linear in component
occurrences. Large connected components remain unrestricted SAT problems.

## Deadlines, strict cache checks, and measured resources

`--query-timeout` (default 30 seconds) covers lookup, native writes/reads,
preparation, solving, checking, training, and persistence. The separate
`--timeout` can impose a shorter external-solver limit. An expired native worker
is killed and reaped; later requests start a fresh one. SQLite checks use progress
callbacks and a remaining-time busy timeout. Python loops check cooperatively.
This is not a hard real-time scheduling guarantee, and initialization is separate.
Every accepted result commits atomically; interruption does not create an UNSAT
entry. Budget exhaustion returns an error, so a budgeted service is incomplete.

Default caps are 8 MiB of binary input, 64 MiB per native message/external output,
and 16 MiB per LRAT proof (`--max-proof-bytes`). External output goes to temporary
files and file sizes are monitored every 20 ms. These are limits on accepted/read
data; disk growth may overshoot between polls. They are not physical RAM limits.
The API exposes all three byte caps. Unbounded input handling in the outer JSON
transport remains a deployment concern; use a bounded request proxy for hostile
network traffic.

`--verify-cache` rechecks saved SAT witnesses or UNSAT certificates on every exact
hit. Historical negatives without certificates are solved again. Checksums alone
are not semantic checks or authentication. Strict hits charge their parsing and
checking and no longer report a zero formal core count. Runtime and I/O remain
outside Lean's kernel proof.

`phase_ns` partitions measured query wall time into disjoint phases, including
serialization, native request modes, prediction, training, external solving,
lookup/retrieval, persistence, and residual control. The sum equals `wall_ns`.
`service_cpu_ns` measures Python process CPU; `reaped_children_cpu_ns` measures
the CPU of children reaped during the query. Live native workers are absent from
that child count until reaped. RSS fields are process-lifetime high-water marks
for the service and reaped children; they are neither a simultaneous process-tree
peak nor per-query allocation. The live bridge separately reports its own RSS.
These measurements do not turn the modern pipeline into a formally counted one.

Native `mode:"restricted"` with optional `stage` demonstrates compact coverage
of valid inputs whose width is at most `floor(log2(length+1))`. An uncovered input
returns `answer:null`, including out-of-family inputs. `coverage_cells` and the
reference decision bound describe that restricted construction. Queries still
solve the formula; the bound excludes coverage-guard overhead and compiled costs.
The Python API's `reuse_exact=False` is an experimental baseline that recomputes
queries while retaining every result in the archive.

[Reproducible experiments](../experiments/README.md) include initialization,
verification, persistence, and shutdown costs and retain every historical dataset.

## Checked local interfaces and expansion snapshots

`--interfaces --max-interface 3` enables persistent factor elimination. Each
factor stores a relation over its ordered scope; projection joins a bucket and
forgets one variable. A deterministic small-degree heuristic and previous
elimination order control the bags. Queries outside the width cap use the old
checked solver. The native process checks every new or replayed factor and
validates the final source-constraint context, so a saved negative result cannot
survive removal of a required assumption. Factor DAG certificates can also be
checked independently against the original formula.

The JSON-lines service additionally accepts:

```json
{"op":"expand","add":{"first":"010"}}
{"op":"expand","base":"<state from previous result>","add":{"second":"0110"},"remove":[]}
```

Names identify constraints. Adding an existing name replaces it; removing a name
requires it to exist. Each returned state is immutable and can be extended or
revisited after restart. Persistent AVL manifests share unchanged map subtrees.
Only supplied constraints are parsed again. Planning and final witness checking
can still visit the active graph; these costs are charged. Width failures reconstruct the active conjunction and use the checked fallback,
including an indivisible constraint that exceeds the leaf-width cap. Deadline
or reconstruction-size exhaustion returns an error without a completed snapshot.

Relation payloads use separate known/value bitmaps: unknown never means false.
Rows are acquired on demand, with short-circuit evaluation and persistent checked
row proposals. Replayed rows are recalculated by the native worker before use;
unknown entries never support a refutation. Equal complete relations share one
payload even when their evidence differs. Schema 8
adds raw-or-zlib object encoding, selecting compression only when it is smaller;
legacy zlib objects remain readable and all old records remain intact. Python's
active node cache is capped; the archive is append-only. Native worker capacity
and interface limits bound accepted evidence, not total process memory.

`Interfaces.lean` proves leaf-table exactness, projection exactness and
entailment, unchanged-factor preservation, bucket-elimination equivalence,
empty-relation refutation, and semantic replacement. `InterfaceProtocol.lean`
uses these operations in the native checked DAG service. JSON, DAG bookkeeping,
Python, SQLite and native execution remain implementation boundaries. The
resource record includes all seven phase categories; measured work and the
complete compiled-machine instruction count remain distinct.


`InterfaceCosts.lean` proves a local evaluator bound of s*(w+2) for s syntax
nodes and w scope variables, at most 2^w rows per complete table, and a charged
short-circuit conjunction/projection bound. The executable records acquired
rows, native row checks/rechecks, DAG hits, ordering work, and all elapsed phases.
These local reference bounds leave graph planning, representation conversion,
verification, persistence and restart in explicit additional costs.

## Checked incremental negative proofs

`--incremental-proofs` enables the proof-carrying alternative to `--incremental`.
The native Lean compiler maintains a shared AIG and stable variable identities.
Only its definitional clauses are permanent; a query root is an assumption.
CaDiCaL's tracer exports original/derived clause IDs and antecedents. The adapter
archives backward proof dependencies and reconstructs an LRAT certificate for
each negative query. The Lean checker uses the existing graph for live traces and checks the reachable
proof against the current root. Standalone certificate replay reconstructs the graph. SAT witnesses still pass the original
formula evaluator. A rejected or unavailable incremental certificate falls back
to independent checked solving; it never establishes UNSAT.

The `incremental_lrat` certificate is portable across service restart and bound
to the original formula. `IncrementalProof.lean` proves that every original input
valuation extends to the permanent graph definitions, and proves the resulting
LRAT check sound for any previous graph. Temporary root assumptions cannot leak
into the permanent checker base. Replayed learned clauses remain proposals until
the proof that uses them is checked. The existing untrusted clause adapter and
its archives remain supported by `--incremental`.

Proof histories are bounded to 512 queries and 100,000 derivation steps per
active branch; replay prefers at most 20,000 short clauses. Prior branches remain
archived. Native graph preparation and negative checking can traverse the whole
retained graph/proof. This closes the fresh-solve requirement for supported
traces, not the cost of incremental proof checking or arbitrary proof events.

Component wrappers retain their supported base-certificate formats; combining
`--components` with `--incremental-proofs` uses the checked base solver for leaf
acquisition. Interface expansion fallback honors `--backend lean`.


## Indexed updates, symbolic proposals, and measured selection

The default interface planner now builds incidence indexes once and updates them
as variables are eliminated. Delta snapshots retain the bucket plan. Changed
sources schedule only affected buckets in the retained order; unchanged output
identities stop propagation. Plan copies, active-source comparisons, snapshot
serialization and final checks remain charged global work. A width violation
tries a fresh ordering and then checked fallback.

`--symbolic` implies interfaces and builds bounded ROBDD proposals directly from
formula syntax, conjunction, restriction and existential projection. It does not
first enumerate a truth table. Symbolic objects are persisted, while native row
checks and final original-formula checks remain mandatory. The manager caps
allocated nodes (50,000), computed-table entries (200,000) and work per query
(500,000 manager operations). On exhaustion it uses the checked lazy path if
time remains. Reference-tree semantics are proved; Python unique-table and memo
bookkeeping are not kernel-verified. Small-scope row cache capacity and the
service interface cap remain in force.

```sh
python3 solver/persistent.py --symbolic --cache /tmp/oracle-symbolic.db serve
python3 solver/persistent.py --adaptive --max-archive-bytes 8388608 serve
```

`--adaptive` applies to full-input solve requests. It samples checked/interface
routes by a feature bucket (described below), uses prior measured mean query durations, and
periodically explores. Only the chosen route runs. Selection and observation
persistence have separate elapsed phases; the learning target includes solving,
checking and answer persistence but excludes the observation's own write and
subsequent storage telemetry (both still included in total wall time). Historical
observations persist. Exact cache hits are not treated as route observations.
Delta requests continue using their explicit interface policy. This selector has
no universal speedup, regret, or workload-shift guarantee.

`--incremental-proofs` now retains verified negative cores in the native session.
A matching archived incremental refutation is checked once after restart, then
reused only after checking its conjunct relation to each new formula. Native
facts are not restored from an unchecked flag. The standalone `conjunct`
certificate contains the base formula and original proof; it remains auditable.
The later fragment implementation below additionally reuses individual clause checks.

`--max-archive-bytes` sets SQLite's logical main-database page limit. At capacity,
acquisition returns a resource error and retains all committed history. It never
turns capacity failure into UNSAT. A cap smaller than an existing database is
rejected. This option does not bound WAL growth, temporary files, process RAM, or
another connection that chooses a different cap. Per-query `storage` records
report logical pages, physical database/WAL sizes and these limitations. See the
[SQLite documentation](https://www.sqlite.org/pragma.html#pragma_max_page_count).

The scaling study and raw measurements are in
[`experiments/results/scaling`](../experiments/results/scaling/README.md).

## Batched interface acquisition and symbolic projection

Interface operations now commit their writes together with full synchronization;
failed operations roll back their new objects and clear volatile proposal caches.
Expansion snapshots remain atomic and all previously committed states survive.
Native factor definitions are submitted in topological batches of at most 128.
Full-input interface attempts first run a write-free width simulation, bounded by
20% of remaining query time and 250 ms, before storing or registering factors.
Rejection routes to the existing checked solver and never means UNSAT.

BDD projection uses fused conjunction and abstraction after all factors for the
eliminated variable have been included. Safe-point garbage collection remaps all
retained roots and clears stale computed-table entries. Explicit alternative
variable orders are supported for controlled experiments, with ordering metadata
checked on replay. Native rows and original-formula checks remain authoritative.

## Balanced chain versions and checked proof fragments

The JSON-lines service accepts an explicit binary-relation chain:

```json
{"op":"chain","append":[6,6,6,6],"left":1,"right":1,"witness":true}
{"op":"chain","base":"<state>","replace":{"1":9},"left":1,"right":1}
```

Bit `2*x+y` of an edge mask permits endpoint values `(x,y)`; mask 6 is
inequality and mask 9 is equality. Endpoint masks permit false (1), true (2),
or either (3). New requests default to unrestricted endpoints; endpoint masks
are query assumptions, and must be supplied again if desired. A perfect tree
padded with equality relations shares unchanged nodes across versions. A single
replacement copies exactly height+1 nodes and composes height summaries.
`BalancedChain.lean` proves exact composition, update preservation and this
logarithmic-in-capacity ledger. Native construction uses those verified joins
and rejects wrong proposed summaries or unbalanced children. Witness output is
optional, linear in chain length, and checked against every edge. General SAT
is not automatically converted into a chain. Input conversion, storage, native
replay and Python indexing remain charged separately from the formal tree ledger.

General interface plans now retain bucket maps as immutable AVL objects rather
than serializing every unchanged bucket again. Source/order lists and final
context checking can still be linear. Existing version-1 plans remain readable.

Incremental proof mode now checks newly observed RUP fragments in a native
session and reuses accepted clauses. Dependencies refer either to checked earlier
fragments or to actual permanent circuit definitions. Root assumptions are
excluded from the permanent base. Graph reset clears all fragments; a changed
base retains them only when every old base clause remains present. Replayed
clauses after restart are checked again. Unsupported/rejected fragments cannot
justify answers; standalone LRAT checking and acquisition remain fallbacks.
The archive retains complete standalone certificates, so serialization/replay of
those certificates is still charged. `ProofFragments.lean` proves RUP soundness,
weakening under added premises, and the composition with the circuit CNF theorem.
The JSON/session bookkeeping is not a complete kernel-verified state-machine
refinement or cost proof.

Adaptive routing now groups measured costs by input size, variable count, graph
density and a bounded sample of reusable factors. Leaf-width/initial-degree
screening can select the checked route without registering factors. Feature
extraction gets at most 100 ms and 10% of remaining time; a full interface attempt
gets at most one second and 40% of remaining time, reserving time for fallback.
Every attempted route and selection cost is charged; no universal speedup or
adversarial-regret guarantee follows.

## Bounded layers, indexed metadata, and active payload limits

`PersistentSolver.layered(width, base=None, replace={}, append=[], left=None,
right=None, witness=False)` accepts explicitly supplied adjacent-layer relations.
For `q = 2**width`, relation bit `q*x+y` permits states `x,y`; endpoint bit `x`
permits state `x`. Width is 1–4 in the runtime. The JSON-lines equivalent uses
`op: "layered"` and the same fields. A state encodes `width` Boolean variables,
so this includes small transition systems and ladders with interacting bits.
It does not discover a decomposition or compile arbitrary SAT for free.

The service stores immutable balanced trees and checks new joins in Lean. One
replacement copies `height+1` nodes and composes `height` summaries. Dense
summaries have `q*q` entries; the declared full-scan composition budget is `q**3`.
Complete witnesses and restart replay are separately charged. Old roots remain
queryable. The runtime caps heights, batches and active native definitions;
capacity errors do not mean UNSAT. Python/JSON/SQLite protocol refinement remains
outside the kernel theorem. Native tables are now materialized inside the join:
inspection of generated C exposed arity expansion delaying the earlier
function-valued `freeze`, including on Boolean chains.

Version-three elimination plans persist source reference counts, ranks, order,
constants and bucket indexes. A named delta looks up changed constraints and
path-copies affected index nodes; duplicate sources remain until their last
reference is removed. Old plan versions remain readable. The counters separate
source delta reads from whole-set comparisons and plan copying. Final active
context checks, witnesses and negative certificates can still scan globally.

`--active-cache-bytes` (default 2 MiB per proposal cache),
`--symbolic-node-limit` (50,000), and `--wal-checkpoint-bytes` (4 MiB) control
retained proposals, symbolic nodes and safe-point WAL checkpoint attempts.
Payload bytes measure serialized JSON, not Python heap or total RSS. Mutable
entries are remeasured at operation boundaries. Oversized transient objects,
native state, indexes, other caches and blocked checkpoints prevent interpreting
these controls as a hard total-memory or physical-storage bound. Immutable
historical evidence is never evicted by these controls.

Adaptive routing now scores recent elapsed cost plus a query-budget penalty for
failures, divided by completed answers. A route with no successful completion
has no finite score. The last 32 observations inform each score; all observations
remain archived. Periodic exploration still retries routes. This is a measured
heuristic, not a regret bound or a guarantee of faster complete solving.

## Priority fixes and checked CNF input

Use `layered_cnf(width, clauses, layers, witness=False)` for a CNF with a supplied
ordered partition. Literals are signed DIMACS integers; each positive variable
ID occurs in exactly one block, and blocks contain at most `width` variables.
Every clause must fit within one block or two adjacent blocks. For example:

```python
result = solver.layered_cnf(1, [[1, 2], [-1, -2], [1]], [[1], [2]], witness=True)
```

The JSON-lines operation is `{"op":"layered_cnf","width":1,"clauses":[[1,2],[-1,-2],[1]],"layers":[[1],[2]],"witness":true}`.
There must be at least two blocks; an empty block can supply an unused boundary.
Empty clauses correctly produce UNSAT. The native checker compiles the source,
checks the proposed tree, and independently binds every source edge and identity
padding leaf to that tree. The native `BoundCompilation` now carries the checked
ordered-leaf equality and proves its decision agrees with the original CNF.
Both compilation passes, full binding and storage are charged. `source_binding`
identifies the archived source evidence; `state` is the
ordinary relation-tree version. Subsequent `layered` edits describe relations,
not automatically an edited version of the original CNF. Re-submit the complete
source to obtain a new source binding. Unsupported decompositions are errors,
never UNSAT. Finding a useful partition remains the caller's responsibility.

Full-source queries report `binding_leaves`, `binding_relation_comparisons`,
`binding_cell_bound` and `binding_source_test_bound` under `compilation`.
Initial source-version requests expose the same fields under `source_updates`.
The comparison count is proved equal to the padded logical leaf count N.
The last two fields are reference bounds N*q² and (N+c+L)*q², for q=2^width,
c clauses and L literals; they are not measured instructions or physical memory.
Mask reads, parsing, source indexing, allocation, output and storage cost extra.
Initial source-version binding pays an additional source-relation scan; warm
edits/current-source queries report zero for these four fields. Their mutable
identity/patch/replay invariants still need a complete Lean state theorem.

Source-version nodes now retain original clauses and their translation proofs in
a tree indexed by layout, width, start and height. Consecutive joins preserve this
alignment; the executed decision has SAT/UNSAT theorems for the original clauses
stored in that node. Warm decisions do not flatten or rescan those clauses.
Replay uses the same checked constructors. Formal agreement between named JSON
nodes, map entries and the requested patch is still a separate obligation.

`source_updates.original_source_nodes`, `original_clause_entries` and
`original_literal_entries` report newly registered original-source nodes and
logical payload entries, including replay. Duplicate native definitions add zero,
as do warm unchanged queries. The parsed original arrays remain reachable from
native leaves alongside existing JSON evidence and local translations. These are
diagnostic entry counts, not bytes, RSS or a proved total-memory bound.

`--native-layer-cells` defaults to 1,048,576 retained relation cells. Under
pressure, the worker retains the complete dependency closure of the requested
root and evicts only other native entries. A working set larger than this cap is
refused before native registration; the durable archive is unchanged. Reports
include retained cells, the cap, retention visits, evictions and replayed
registrations. This bounds a logical retained representation, not actual RSS or
transient Python/native allocations. Restart and older-branch access may replay
archived definitions. Source input and native definition caps still apply.

General elimination now distinguishes semantic value work from provenance work.
A complete equality check can establish an equivalent new summary. Downstream
projections with matching checked parent meanings reuse known row values, while
new evidence records the new parents. `semantic_stops` and `provenance_rebinds`
measure these cases; `affected_buckets` still includes every changed evidence
node. The suffix can remain linear. Row acquisition uses an explicit continuation
stack, so the old Python depth-256 fallback is removed. Native capacities,
symbolic recursion limits, full context checks, witnesses and certificates remain
separate limits.

Witness/refutation proposal attempts have separate native calls and measurements.
Their combined allowance is at most 250 ms and 10% of the remaining query budget.
A timeout kills the owned worker and resumes checked fallback with the original
deadline; replay costs remain charged. This bounds speculative effort but does
not guarantee fallback completion or learn an optimal gating policy. The Lean
reference backend retains its separately counted behavior.

A route observation now follows successful storage accounting. An API failure
gets at most one failed observation, rather than both success and failure.
Telemetry-write failures do not invalidate an already completed checked response;
they are returned as `routing.observation_error`. Logging is best effort and may
be absent under storage/deadline failure. A correctly committed answer can remain
in the archive even if a later service step fails.
