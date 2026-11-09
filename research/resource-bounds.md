# Current computation, memory, and expansion bounds

Audit date: **8 November 2026**. Code/evidence baseline: **`fe7d767`**;
reuse implementation: **`e0cb8d3`**. This is an inventory of the current system,
not a new unrestricted-SAT theorem. The accompanying
[read-only snapshot](../experiments/results/resource-audit-2026-11-08/snapshot.json)
records source fingerprints, database pages and the underlying measured counters.
The resident-width metadata update below is measured separately in
[the follow-up experiment](../experiments/results/affine-resident-metadata/README.md);
the original snapshot remains unchanged.

The strongest expansion result is **polynomial coefficient work and a quadratic
boundary summary for affine constraints**. The general SAT paths retain
exponential reference bounds, potentially large certificates and no complete
production time/RAM theorem. Reuse changes which calculations are repeated; it
does not bound the number of distinct difficult calculations in an arbitrary
stream. Persistent storage remains unbounded by default.

## 1. What a bound means here

We must keep four accounts separate:

1. **Proved abstract work:** parser operations, search nodes, intermediate-state
   tests or affine coefficient charges. These units differ across implementations.
2. **Logical payload:** answer entries, Boolean coefficient cells, relation cells,
   identifiers or serialized bytes. Shared references can reduce actual allocation.
3. **Measured execution:** elapsed phases, Python CPU/RSS, reaped-child statistics,
   transported bytes and SQLite sizes on the recorded workloads.
4. **Physical resource bounds:** whole-process-tree peak RAM, complete machine
   instructions, disk including WAL/temporary files, and hard elapsed deadlines.
   We do **not** have a complete bound for these quantities.

An algebraically zero elimination charge does not mean zero expansion time.
`counted_complete` must be read in its particular parser/core scope: even an
exact result-cache hit reported with zero core work reads and validates data and
accesses SQLite. It is not a zero-cost service request.

Notation:

| Symbol | Meaning |
|---|---|
| L | Encoded input length in the solver's unary-index formula format |
| v | One plus the largest variable index; zero for a variable-free formula |
| d | Number of distinct occurring variables; d <= v |
| N | Maximum input-string length covered by an explicit finite-domain table |
| T | Number of archived expansion steps/versions in a history or stream |
| b | Affine block width, or Boolean layer width when stated |
| c_t, c'_t | Original and duplicate-free affine row counts at step t |
| U | Distinct acquired batches/components; not assumed sublinear in T |
| m, h | Number of layered edges and balanced height, h = ceil(log2 m) |
| q | Number of states in a Boolean layer: q = 2^b |
| k, A | Generic factor scope size and number of affected factors |
| V, K, P | Retained affine versions, transition slots and preparation slots |
| D_t, Z_t | Certificate/checking work and durable bytes added at step t |

The encoded length L is not interchangeable with DIMACS file size or variable
count. Unary indices, dense output witnesses, JSON and intermediate encodings can
be much larger than the original sparse input. Runtime caps are refusals beyond
a supported workload, not asymptotic algorithms for all input sizes.

## 2. General SAT and the finite-domain construction

### Explicit coverage tables

`Expansion.lean` proves **2^(N+1)-1 answer entries** for all binary words of
length at most N. Growing from N to N+1 adds **2^(N+1) words** and therefore that
many labels if using the append decomposition. Work includes generating/storing
those words and the sum of their solver costs. `table_append` is an equality of
representations; it is not a physical incremental-allocation theorem, and directly
calling `table solver (N+1)` constructs the entire table.

Explicit key payload is **Theta(N*2^N)** for N >= 1, in addition to answer bits
and list metadata. This key-size statement is a direct counting derivation; the
Lean theorem explicitly counts entries. The implemented `lookup` scans a list:
a coarse worst-case comparison bound is O((N+1)*2^N), not constant-time RAM
lookup. The manuscript's alternative packed/random-access representation is a
separate model. `Limits.lean` proves that the explicit entry count and exponential
stage work are not polynomially bounded in N.

Every fixed finite restriction is decidable by a fixed finite table. Uniformly
constructing the tables as N grows still incurs these costs. Finite exactness
and induction on coverage therefore do not establish P = NP.

### Exhaustive reference solver

Let W be the syntactic weight, with v <= W <= L. The exact formal bounds are:

- Parser: at most **8L + 7** ledger units.
- Parsed exhaustive solving: **W^2 + 2^v*(W+13) + 2** units.
- Search machine over supplied complete assignments: at most
  **1 + 2^v*(W+2)** transitions.
- Reachable search data: at most
  **(v+1)*2^v + v + 2L + 2** payload symbols.

The last two do not include generating the candidate list, parsing it or a
verified Lean-runtime simulation. This reference eagerly materializes all
assignments. Its exponential memory is a property of this implementation, not
a claim that every SAT algorithm needs exponential working space.

If **2^v <= L+1**, the parser/core decision bound is **24*(L+1)^2** and the
search-machine payload bound is **5*(L+1)^2**. The sufficient promise
v <= floor(log2(L+1)) gives these restricted polynomial bounds. Padding to force
the promise already requires L >= 2^v-1. `CompactExpansion.lean` maintains a
unary coverage state of N cells in N construction steps, but its queries still
run this restricted solver. It stores coverage, not precomputed answers. The
coverage/promise guard and full deployment costs are outside that query ledger.

Sources: [CostedSAT](../formal/OracleMachines/CostedSAT.lean),
[Parsing](../formal/OracleMachines/Parsing.lean),
[SearchMachine](../formal/OracleMachines/SearchMachine.lean),
[Restricted](../formal/OracleMachines/Restricted.lean),
[CompactExpansion](../formal/OracleMachines/CompactExpansion.lean).

### Lazy search, checked CDCL and learned proposals

The improved sparse search branches only on d occurring variables and proves
**nodes + 1 <= 2^(d+1)**. It avoids the eager assignment list and may stop early.
Per-node partial evaluation and sparse lookup still cost work; the node bound
is not a complete time bound. It also constructs explicit refutation trees,
which can grow exponentially. Its pending assignment stack should not be
confused with its complete proof/result memory. A full peak-memory theorem for
this lazy implementation has not been supplied. Dense witness materialization
still produces v output positions.

The production path uses shared AIGs, bounded preliminary search, checked models,
LRAT refutations, and optional incremental CDCL. Correctness of accepted
certificates is proved, but **the current CDCL integration has no proved
end-to-end polynomial or complete machine-time/space bound**. We must parameterize
its cost by solving, circuit/CNF construction, proof size, verification, replay
and persistence. A certificate's existence or cheap verification relative to
its own size does not give a polynomial certificate-size bound in L.

Exact result reuse reads the request, looks up the stored record, validates its
checksum, retrieves measurements and may update active-witness state. It has at
least linear input/payload handling, plus database work; there is no proved
constant-time lookup bound. With `verify_cache=True`, checking the witness or
proof is added; a historical negative without a proof can require solving again.
Default exact-cache reuse trusts the previously checked local record plus its
integrity check. This differs from a new kernel certificate or a fresh proof check.

Witness/refutation proposals are bounded to four candidates of each kind, with
64 KiB per retained proposal. Their bounded count does not make each check free.
The learned predictor has five bounded weights and two bounded counters, so its
model state is constant-sized. Feature extraction still traverses the formula,
keeps per-variable features and emits a v-position witness. Its small model
provides no general-SAT complexity guarantee.

Sources: [Search](../formal/OracleMachines/Search.lean),
[persistent service](../solver/persistent.py),
[predictor](../solver/learning.py), [incremental proofs](../solver/incremental_proof.py).

## 3. Expansion through components and general interfaces

For the proved shared-interface construction, b variables are shared and each
component has at most p private variables. With s evaluation work per assignment,
U distinct component shapes and m occurrences, the declared structural budget is

    U * 2^(b+p) * s + m * 2^b

and the declared summary-bit account is **(U+1)*2^b**. Acquiring a component
is exponential in its local-plus-interface width. The budget assumes supplied
shape identification and decomposition; discovery, normalization, certificates
and all service work must be added. These are stated hypotheses, not properties
of arbitrary SAT instances. See [Components](../formal/OracleMachines/Components.lean).

The more general factor engine uses cached rows, projections and persistent
plans. For a formula of syntactic size s on a k-variable scope, the formal local
acquisition bound is **r*s*(k+2)** for r requested rows, with **r <= 2^k** for
one complete acquisition. Restart rechecks may reacquire rows. A full table can
have 2^k rows; explicit assignments add key payload. A bitmap, sparse encoding or
BDD may be smaller, depending on the relation. Choosing a compact encoding does
not bound every relation by a polynomial-size representation.

The general expansion account is

    H_t + A_t * R_t * C_t,

where H includes planning, matching, copying/indexing, provenance, verification,
replay and persistence. R is row capacity and C is per-row work. A change can
propagate throughout the dependency graph; A is not bounded by the number of
changed input clauses. `Scaling.lean` proves a conditional polynomial bound only
when **A, R, C and H are all separately polynomially bounded**. It also proves a
dependency-depth/fanout envelope, not a universal small affected region.

Persistent plans and unchanged-factor reuse reduce repeated work, but the general
factor route still has graph-wide context/provenance and original-answer work.
The specialized source-CNF path below removes particular global operations for
its supplied layout. That improvement must not be transferred to arbitrary edits.

The symbolic proposer caps its unique table at 50,000 nodes and its counted
operation requests at 500,000 by default; its memo table clears at four times
the node cap. These are counts, not bytes or a bound on complete verification.
Exceeding a cap uses a checked fallback or refuses work; it does not establish
that the compact representation always exists. The default interface cap is
three, configurable from zero to ten; the accepted bag can contain one more
variable than the separator cap.

Sources: [InterfaceCosts](../formal/OracleMachines/InterfaceCosts.lean),
[Scaling](../formal/OracleMachines/Scaling.lean),
[planner](../solver/planning.py), [interfaces](../solver/interfaces.py),
[symbolic proposer](../solver/symbolic.py).

## 4. Balanced layers and source-CNF edits

This family supplies a fixed sequence of blocks of width b, and constraints
between consecutive blocks. The runtime currently accepts b = 1..4. With q=2^b:

| Operation/payload | Current account |
|---|---|
| One complete boundary relation | q^2 = 4^b Boolean cells |
| One relation join | At most q^3 = 8^b intermediate-state tests |
| One leaf replacement at height h | At most h+1+h*q^3 reference units |
| New relation payload per single edit | O((h+1)*q^2) before sharing/compression |
| Initial full balanced relation tree | O(m*q^3) join work; O(m*q^2) relation payload |
| Several edits | At most their separate paths; common paths/subtrees may share |

These bounds exclude source compilation and bookkeeping. The source path scans
new clauses/literals over q^2 boundary pairs, then checks source-bearing leaves
and joins; some compilation/checking occurs in both paths. For changed source
payload of ell clause/literal visits, the corresponding source-test account is
O(ell*q^2). Source patch checking descends edited paths and compares unchanged
identities; its visit counter excludes payload comparisons, edit filtering,
string/hash/map operations and transport. The complete request is not thereby
proved O(delta*log m).

For a resident root, decision scans the allowed endpoint pairs in its summary,
at most q^2 relation tests, plus input/store work. Requesting a witness traverses
the tree and emits the layer path; it cannot be independent of history size.
A non-power-of-two witness request can additionally materialize prefix/suffix
relations, with the reported h*q^3 composition bound. The Python service further checks reported paths against retained leaf relations;
complete serialized-witness refinement remains open.

Unlike a single affine summary, the active layered/source tree retains reachable
children. If J distinct nodes are needed, retained relation payload is O(J*q^2),
with J=O(m) in the worst case, plus original leaf clauses, metadata and caches.
Sharing may reduce J. Old versions add only changed paths when reuse succeeds,
but every version/root/result remains archived. For single edits, a useful
logical archive envelope is initial O(m*q^2) plus
O(sum_edits (h_t+1)*q^2 + new_source_payload), before IDs, results, witnesses,
indexes and representation encodings. Full witnesses can add O(m) values per
requested version.

The default native relation budget is **1,048,576 cells**, with a separate
200,000-node native limit. The source patch path temporarily retains the old
state while checking the new one: up to the retained budget plus newly defined
nodes. If both working sets fit, a conservative derived envelope is twice the
cell budget; the native node limit may refuse earlier. It is not a hard cap on
transient bytes. An active tree that itself exceeds the budget is refused, not
silently evicted into a constant-memory exact decision.

Sources: [Layered](../formal/OracleMachines/Layered.lean),
[LayeredCosts](../formal/OracleMachines/LayeredCosts.lean),
[LayeredProtocol](../formal/OracleMachines/LayeredProtocol.lean),
[SourcePatch](../formal/OracleMachines/SourcePatch.lean),
[layer retention](../solver/layered.py), [source edits](../solver/source_updates.py).

## 5. Affine expansion: the strongest current bound

An append introduces a fresh b-variable block and c_t affine equations involving
only the preceding boundary and that new block. The exact summary has at most
**b+1 equations**, hence at most **(b+1)^2 coefficient/right-hand-side cells**.
After T appends the original system has (T+1)b variables, but the current
boundary still has width b. There is no enumeration of its 2^b assignments.

### Miss, hit, preparation and query

With c'_t unique rows, the proved append coefficient budget has this algebraic
form:

    B(b,c') = 4b^3 + 13b^2 + 18b + 8 + (3b^2+5b+3)c'.

This restates `appendBudget` in `AffineGrowth.lean`. Thus a miss has
**O(b^3+b^2*c')** elimination/decision charge. The actual executed charge can be
lower. Removing duplicate rows preserves all solutions and the original-source
history. It does not yet remove arbitrary linear dependencies before elimination.

For the actual hit set A, executed elimination/decision charge is exactly

    sum over t not in A of C(S_(t-1), U(E_t)),

where U retains first occurrences and C is the selected constructor's nominal
charge. The old unnormalized counterfactual requires normalization disabled.
A hit incurs zero elimination/decision charge, but these other accounts remain:

| Work | Payload/cost boundary |
|---|---|
| Original batch preparation key | c_t*(2b+1) coefficient cells when cache enabled |
| Preparation candidate comparison | At most one full original typed batch |
| Normalized kernel key | At most (b+1)^2+c'_t*(2b+1) cells |
| Kernel candidate comparison | At most one full boundary/batch candidate |
| Duplicate removal on preparation miss | Hash set over the original rows; input payload is counted, all hash/probe/resize work is not |
| Decoding/serialization/source validation | Original source still processed, including duplicates |
| Native append reply | Full summary is currently serialized even when the later public query uses summary=False |
| Ordinary resident query | Stored answer; source-record read, request/reply and result persistence still occur |

Hash collisions cannot authorize a false native cache hit, because complete
structural equality is checked. They can destroy useful cache entries. A hit
rate is not guaranteed, and normalized keys still distinguish first-occurrence
order and predecessor basis representation.

Source handling still has a parent dependency: `run` reads the base record,
and `ensure` reads a new source in its backward plan and forward replay. The
resident-width update removes the former additional parent read in forward
replay: the process-local residency map now retains the width confirmed by the
native definition. A new unshared append in the retained example drops from
four to **three** object reads; a shared append drops from nine to **seven**,
including referenced-batch validation and admission checking. The requested
base is still read and validated, so its original batch is still processed once.
The option `affine_reuse_metadata=False` reproduces the extra parent read for
matched comparisons. This changes source overhead, not the coefficient bound.

### Dependence on width and history

| b | Unique rows c'=b | Summary-cell bound | Append coefficient budget |
|---:|---:|---:|---:|
| 16 | 16 | 289 | 33,624 |
| 32 | 32 | 1,089 | 248,488 |
| 64 | 64 | 4,225 | 1,910,088 |
| 128 | 128 | 16,641 | 14,977,672 |

For c'=O(b), misses scale cubically with width and the summary quadratically.
For fixed b and bounded c', the algebraic charge per resident append does not
grow with T. Total successful append charge without useful reuse is O(T*B(b,c')).
Source metadata, step-counter bit lengths, archive access and cold replay still
depend on history. This is polynomial processing of **one restricted affine
history**, not coverage of all general SAT formulas up to a growing size.

The runtime accepts b <= 128 and c_t <= 4,096, subject to byte/deadline limits.
At those maximum values the reference budget is 212,564,232 coefficient units
before the additional work above. Fixed acceptance caps must not be described
as a universal constant-time solver.

### Retained memory and cold replay

Let c bound original rows and c' bound unique rows. A conservative sum of logical
coefficient/request payloads is

    V*((b+1)^2 + c*(2b+1))
      + K*(2*(b+1)^2 + c'*(2b+1))
      + P*((c+c')*(2b+1)).

The first term includes resident summaries and original request bodies. The
second includes transition keys and results. The third includes checked original
and normalized prepared batches. This deliberately overcounts shared references;
it excludes JSON keys, list/map structures, IDs and temporary allocations. In
big-O form it is **O((V+K+P)*(b^2+b*c))**. The proof establishes compact summaries;
this aggregate retained-payload expression is an implementation analysis, not
a proved heap-space theorem.

Defaults are **V=256, K=64 and P=64**. The latter two maps occupy slots
independently. At the largest accepted b,c and with c'=c, the conservative
logical envelope is 477,987,200 cells, illustrating how weak a slot cap is as a
memory policy. This is neither measured allocation nor bytes. Actual sharing
reduces some terms; runtime objects and temporary copies add other costs.
The resident-width update adds one bounded integer per existing residency entry,
O(V) logical metadata, sharing that entry's eviction/reset lifetime. It avoids
one transient parent-batch decode per replayed append; no RSS reduction has been
measured or proved.

Original histories are erased from native proof states, so retaining a child
no longer keeps every ancestor state alive. However, original request JSON
remains per version; preparation retains typed original inputs; JSON decoding,
deep copies, hashing, normalization and elimination create temporary data.
No full peak-allocation theorem covers these operations.

After restart or eviction of a needed old branch, native caches are empty or may
lack a prefix. Replaying r missing steps has a no-reuse coefficient bound
**sum B(b,c'_t)** over that prefix, plus original reads/normalization/transport.
Reuse found during replay can reduce this sum. The backward plan and cycle check
keep **O(r) identifiers**, while batches are reread during the forward pass.
The current service has no trusted durable kernel checkpoint that skips that
source history. Thus bounded resident versions do not imply constant-memory
or history-independent cold queries.

Sources: [AffineGrowth](../formal/OracleMachines/AffineGrowth.lean),
[AffineCosts](../formal/OracleMachines/AffineCosts.lean),
[AffineKernel](../formal/OracleMachines/AffineKernel.lean),
[AffineNormalize](../formal/OracleMachines/AffineNormalize.lean),
[AffineProtocol](../formal/OracleMachines/AffineProtocol.lean),
[Python affine replay](../solver/affine_growth.py).

## 6. Persistent storage and physical limits

Before batch sharing, original affine coefficient payload grows as
**O(sum_t b*c_t)**. With inline occurrences I and distinct shared original batches D,
the hybrid source account becomes

    O(sum_(t in I) b*c_t + sum_(B in D) b*|B|),

plus version links/metadata for all T versions. A frequent large exact batch can
therefore be stored a bounded number of times plus links. Novel batches, changed
row order or changed multiplicity can still give U=Theta(T) and the old growth
rate. Semantic computational reuse does not authorize changing original source
records. First admission incurs an extra object; short streams need not save.

Every completed result remains archived. Asking for summaries can add
O(T*b^2) coefficient payload; full layered witnesses and general proofs have
their own output sizes. New engine namespaces preserve preceding results and
can add new checked result/evidence records for existing logical inputs. Original
source objects may be shared across those namespaces. The general result tables
also repeat full encoded keys in result, proof, measurement and index structures.

Current read-only snapshot:

| Quantity | Value |
|---|---:|
| Main SQLite file | 19,738,624 bytes (18.82 MiB) |
| Generic result rows | 10,295 |
| Refutation rows | 3,483 |
| Source-CNF rows | 85 |
| Affine result rows | 1,340 |
| Distinct affine histories | 268 across five engine namespaces |
| All immutable knowledge-object payloads | 676,325 bytes |
| Retained local .cache tree | 1,085,068 KiB allocated, about 1.03 GiB |

The last line includes experiments and backups; it is not one active database
or live RAM. SQLite's page inventory attributes 4,792,320 bytes to the measurement
table and 2,179,072 to its primary index; results occupy 3,207,168 plus 2,441,216
for their primary index. Together these four structures consume about 64% of
the main file. Affine batch compression therefore addresses only part of overall
storage. All earlier records remain, by design.

Current deployment controls:

| Control | Default | What it does not bound |
|---|---:|---|
| Query / external-solver deadline | 30 s / 30 s | Hard wall-clock latency or complete decision on every input |
| Input / message / proof limits | 8 / 64 / 16 MiB | All simultaneous objects, solver heap, or file overshoot |
| Immutable-object decoding limit | 64 MiB per object | Total archive, live decoded objects or process memory |
| Proposal payload cache | 2 MiB per applicable cache | Combined caches, Python heap, transients or native memory |
| Native layered/source relation cells | 1,048,576 | Source clauses, metadata and patch reservation |
| Native affine versions | 256 | Bytes per version, preparation or kernel payload |
| Each affine cache | 64 slots | Byte/RSS usage or a positive hit rate |
| Batch-admission candidates | 256 hashes | Source batches and durable records |
| Symbolic unique nodes / work requests | 50,000 / 500,000 | Full checking cost, encoded node bytes or fallback work |
| Archive pages | No cap by default | Unbounded history growth |
| WAL checkpoint trigger | 4 MiB | Hard WAL/temporary/backup disk limit |

An optional archive cap refuses new acquisitions when logical SQLite pages fill;
it preserves old results. It does not bound WAL, temporary files, backups or
other databases. Python/SQLite deadlines are cooperative. External file growth
can overshoot between monitoring polls. These are deliberate fail-closed resource
policies: refusal is neither SAT nor UNSAT.

`service_peak_rss_bytes` measures cumulative **Python-process** RSS.
`reaped_children_peak_rss_bytes` concerns reaped children, not a simultaneous
peak of Python plus the still-running Lean/CDCL processes. The present metrics
therefore cannot substantiate a whole-process memory reduction from the new
sharing. Live process-tree and allocation profiling remain missing.

Sources: [resource controls](../solver/resources.py),
[active cache](../solver/active_cache.py), [archive](../solver/knowledge_store.py),
[sharing policy](../solver/affine_archive.py), [service configuration](../solver/persistent.py).

## 7. What the current measurements actually locate

The four-mode affine study uses the same binary and existing exact transition
cache in every mode. Five repetitions give 120 runs and 2,800 checked decisions.
These are synthetic restricted workloads, not a ranking of all SAT workloads.

- **Repeated width 32:** baseline 236.75 ms; normalization 234.90 ms; sharing
  260.44 ms; both 252.47 ms. Source payload falls 16,656 -> 6,499 bytes and the
  database falls by 12 KiB, while both options add 6.6% elapsed time.
- **Changing duplicate counts, width 32:** baseline 1,246.55 ms; normalization
  417.58 ms; both 430.52 ms. The coefficient ledger falls 30,266,133 -> 461,575
  and 14 transitions become reusable. Native append phase medians fall from
  about 974.96 to 148.47 ms across the stream with both options. Normalization
  attacks a real cost in this constructed family.
- **Novel width 32:** baseline 413.65 ms; both 412.89 ms. Native append takes
  approximately 235.5 ms in both. No hits or storage sharing occur. Small timing
  differences are not a benefit claim.
- **Repeated shared-hit example:** four source-object reads become nine; original
  input is 30,844 bytes, native requests total 31,131 bytes and responses 8,175
  bytes. Elimination charge is zero. Sharing reduces newly inserted packed bytes
  from 822 to 471 for that request but increases packed bytes read from 2,060
  to 2,904. This demonstrates a storage/read-work tradeoff.
- **Repeated-stream phase medians:** Python `affine_update` residual increases
  from 36.93 to 55.82 ms when both options are enabled. Native append stays around
  46--48 ms. These phases include several operations; they do not isolate the
  cost of each decompression or SQL statement.
- **Setup:** approximately 99--101 ms plus 31--32 ms attributed to the first
  native cache-configuration exchange, which includes worker startup. This is
  paid per fresh run, not per warm expansion. It matters for interpreting short
  benchmark totals.

Individual phase medians need not sum to the median total. No new timings were
run for this audit; its numbers are recomputed from the preserved measurements.
See [the experiment](../experiments/results/affine-batch-reuse/README.md).

## 8. Complete accounting model and open bounds

For a stream of requests, write total work as initial setup plus, for each t:

    input + identify/prepare + lookup + new calculation
      + certificate/check + transport + retention/persistence + recovery.

Reuse reduces the new-calculation term. It can add to the other terms. For a
fixed comparator, saved repeated solving must exceed acquisition and all reuse
overhead. That statement applies under either P = NP or P != NP and to more
complex decidable problems; neither resolution supplies a positive hit rate,
cheap certificates or compact acquired knowledge.

Similarly, peak memory is a simultaneous live account of native summaries,
cache keys/results, Python data, decoded input/output, temporary normalization
and elimination structures, proof data, solver-internal clauses and allocator
costs. Archive size is a different sum over retained historical objects. Bounding
one active model or summary does not bound either whole quantity.

The present gaps are now localized enough for a subsequent cost study:

| Area | Bound still missing / cost still paid | Evidence to collect next |
|---|---|---|
| General SAT | No uniform polynomial acquisition, representation or proof-size guarantee | Width/representation/certificate growth on broader input families |
| Warm affine hits | Repeated source reconstruction, parent reads, duplicate decoding and full summary replies | Per-object read/decode/hash timings; bytes avoided by checked batch handles and compact replies |
| Affine misses | O(b^3+b^2*c') elimination; only exact duplicates removed | Low-rank-change workloads, basis reuse and charged row-space normalization |
| Native memory | Slots bound entries, not bytes; original JSON and temporary data remain | Simultaneous process-tree peak and isolated live-allocation measurements |
| Cold queries | Original-history replay and O(T) identifier plan | Replay length, repeated reads, checkpoint validation cost and benefit |
| Layered/source expansion | Exponential width; active tree, source compilation and witness output | Separate width, history length, edit count, payload and certificate costs |
| General factor edits | Affected region and overhead H can be global | Dependency locality and full-context/provenance work per request |
| Archive | No default growth cap; keys, telemetry and namespaces dominate current file | Incremental bytes by table/index/object kind, without deleting old evidence |
| Formal resource refinement | Byte transport, Python/SQLite, allocation and compiled-runtime costs | Explicit machine models or bounded implementation contracts for targeted operations |

## 9. Simultaneous repair in the experimental CNF history

`EquivalenceRepairHistory` adds a proposal rule and an independent joint checker
to the affected-clause prototype. It does not change the native solver path.
The proposal rule groups variables connected by complementary binary clause
pairs in a SAT base. Signed equalities and inequalities both allow complementing
every variable of a connected block. Recognition is lazy and cached per base;
new equalities introduced only by subsequent additions are not recognized.
Conjunctive additions preserve the old equalities, but may prevent their block
from changing. Every affected old clause, including every earlier addition,
therefore participates in the independent final-state check.

Let Q be the proposed changed variables, q = |Q|, R the sum of their posting-list
lengths, A the number of distinct affected clauses, and d the added clause's
literal count. The checker aggregates signed true-literal count differences
across Q before testing positivity. It visits R postings, uses an O(A) temporary
map, changes q assignment entries, and updates at most A nonzero count entries.
It does not apply a sequence of independently accepted scalar changes. Internal
equivalence clauses have zero net difference and need no count-map writes, but
the implementation still visits their postings. No one-bit group assignment or
boundary-only update bound is implemented.

With identifiers of at most b bits and m parent clauses, accepted checking and
index maintenance use O((d+q)b + (A+1) log(m+2) + R) trie-node/literal operations,
apart from hash-map work, integer arithmetic, allocation, serialization and SQL.
New retained paths are O((d+q)b + (A+1) log(m+2)), plus at most d new posting nodes
and a constant number of roots. Discovery additionally charges every attempted
variable and posting, including failed scalar and joint candidates. Its default
4,096-visit budget counts joint variables plus their postings; it does not bound
base recognition, integer bit operations or persistent-trie path lengths.

Recognition scans the exact base's L literal occurrences, retains at most B
distinct binary pairs while building a union-find structure on n recognized
variables, then sorts and caches the blocks. Under unit-cost integer operations
and expected constant-time dictionaries, O(L + B log(n+2) + n log(n+2)) is a
conservative bound; hash collisions and large identifiers require further bit
accounting. Temporary space is O(B+n+maximum clause length), and the retained
block tuples and variable-to-block references are O(n). These costs recur per
newly recognized base and after a restart's first failed scalar repair.

The durable delta stores the exact added clause and q variable identifiers.
Older versions retain their sources, assignments and count roots. For a fixed
base, additional logical payload is proportional to encoded additions, move
lists and version references, not the full source per update. This is still
linear in the total encoded move lists: repeated use of the same block has no
shared durable block certificate yet. Cold replay reconstructs indexes and
checks all required moves. It does not run the block recognizer until another
proposal is needed; the matched study reports cold queries and resumed updates
separately. General fallback may still copy the whole source, retain another
base and require exponential search.

Measurements and retained failures are in the
[matched study](../experiments/results/cnf-equivalence-history/README.md).

## 10. Retained matching state in the experimental CNF history

The matching adapter runs after scalar/equivalence attempts fail. It recognizes
strict whole matching bases, preserving original variable identities: disjoint
positive choices, complete resource exclusion cliques, no parallel indicators
for one choice/resource pair and no unassigned negative-only indicators. The
normalization and graph recognition scan the base, construct sets, sort clauses
and adjacency and check the clique structure. These costs are paid once per
recognized base in a warm session, not per successful warm move. The original
CNF, including its explicit quadratic clique encodings, is still retained.

With e indicators, the cached graph/variable binding occupies O(e) entries.
Lazy view construction scans all e indicator values, validates exactly one
selected edge per choice and at most one per resource, then replays required
history deltas. It therefore charges O(e*b) assignment-trie node visits plus
endpoint construction and the earlier changed-variable/unit history work.
The view maps choices to selected indicators, resources to owners, and
unit-constrained indicators to pins. It uses three persistent tries, shared
across versions. Mixed-class bases, newly introduced graph structure and models
with extra selected choice indicators are not silently coerced to this view.

Let s count graph edges visited by a candidate BFS, q the changed indicators,
R their total posting occurrences, A the distinct affected clauses, d the added
clause length, b the variable-ID bit length and m the parent clause count.
Graph search, move sorting, joint checking and matching-view maintenance together
use a conservative bound

    O((s+d+q+1)*b + (A+q+1)*log(m+2) + R + q*log(q+2) + d)

on trie-node/literal/comparison work for one accepted matching candidate, apart
from dictionary/set operations, arithmetic, allocation, serialization and SQL.
Earlier scalar/equivalence attempts, other candidates, recognition and lazy
reconstruction are additional. Choice IDs are positive clause positions, while
resource IDs and pins use original variable identifiers. The proposal budget
charges earlier candidate visits, BFS edges, moved variables and postings; it
does not bound all those additional costs. The BFS and final check can touch the
whole component/source even for one unit addition.

Matching-view maintenance adds O(q*(b+log(m+2))+b) retained path nodes per accepted
update with an active view; a unit can add a pin. This is in addition to the
assignment/count/posting bound in Section 9. Temporary path/queue and aggregation
state scales with visited vertices/edges and affected clauses. The graph view is
not serialized: durable records reuse the existing joint move list. No extra
matching certificate is required for soundness, since the independent checker
validates the final assignment against all affected source clauses.

Cold final queries reconstruct/check only the base, occurrence indexes and
required joint history. A resumed failed scalar/equivalence request additionally
rebuilds the graph and matching view. Tests compare those operations separately.
Full witness output is still output-sized; historical roots retain all versions;
failed proposals may still copy and solve a whole new base.

At 32 blocks of eight choices, preparation is 206.58 ms of 253.08 ms total, so
further optimization of the two-edge warm search cannot remove the dominant
initial cost. The last move changes four indicators, visits 32 postings during
discovery and again during checking, updates four matching endpoints, and
allocates 439 total trie nodes. The larger 64-choice cycle changes 128 indicators
and visits 256 postings per pass. See the
[matched study](../experiments/results/cnf-matching-history/README.md) for retained
failures, cold costs and separate Python allocation measurements.

The first priority can differ by workload: normalization helped changing
multiplicities, source handling dominates much of already-reused work, novel
batches still pay elimination, and database telemetry/indexes dominate much of
the current retained file. We should keep these separate when selecting the
next optimization rather than assigning one universal bottleneck.

## 11. Bounded retry of recognized equivalence repairs

The optional `BudgetedRepairHistory` runs the preceding pipeline first. After
failure, it retries at most the first exhausted proposal that is exactly a cached
base-equivalence block. Completed rejections and matching proposals do not qualify.
For block size q, the extra proposal allowance is

    B = min(escalation_budget, 8*q),

with defaults escalation_budget=32,768, q<=8,192 and variable-ID length b<=64.
The sorted block's final ID gives its maximum bit length. Size/identifier refusal
does not inspect postings. A zero ordinary or escalation budget disables retry.
The multiplier is a heuristic, not an estimated optimum or a guarantee of saving.
The globally raised-budget comparator is faster on several retained cases.

Let q' variables and R' postings actually be visited in the retry, with A'
distinct affected clauses aggregated. Discovery satisfies q'+R'<=B, and uses
O(q'*b + R' + A'*log(m+2)) trie-node/posting work, apart from dictionary work,
integer arithmetic and allocation. The A' term accounts for checking completed
count differences; an incomplete aggregation is discarded. The temporary map
has O(A') entries. Prior failed work is additional and remains charged. The policy
retains one reference to an existing block tuple, not another full assignment.
It does not reuse the partial aggregate of the earlier exhausted attempt.

Success still requires the full independent check and index maintenance from
Section 9, including q assignment updates and a q-identifier durable move list.
No record format or persistent base/index structure is added by the budget policy.
The changed historical paths remain retained as before. The visit budget does
not cap recognition, cold parent reconstruction, checking, integer-bit operations,
serialization, SQL, or failed materialize-and-solve fallback. It is not a hard
time or byte bound on the full request.

For a plain q-variable equivalence chain, R=4q-4, so the complete proposal needs
5q-4 visits. At q=1,024 this is 5,116: the retry succeeds after the original
4,096 visits were already spent. Discovery and checking both visit internal
clauses, although their net count changes are zero. Additional clauses can make
R much larger or block the move. The dense 1,024-variable control exhausts its
8,192-visit retry and still falls back; a global budget of 32,768 succeeds.

Measured total time at 1,024 variables falls from 0.78490 to 0.05932 s, logical
payload from 189,168 to 99,129 bytes, and peak traced Python memory from 3,071,073
to 1,741,448 bytes. Cold final replay increases from 43.48 to 45.25 ms. A pinned
2,048-variable contradiction instead pays 40.36 rather than 31.01 ms expansion.
These single samples and all comparison policies are preserved in the
[budget study](../experiments/results/cnf-budgeted-history/README.md).

The same study identifies a separate preparation cost: repeated-scan propagation
takes 16,779,261 charged literal visits on an 8,189-occurrence pinned chain.
The existing scan engine has an O((v+1)*L) literal-visit envelope, where v is
the number of variables and L the CNF literal payload. It can revisit essentially
the whole source after each newly forced value. An occurrence-driven propagation
queue is the next proposed improvement; it has not yet replaced that engine.

## 12. Bounded pattern discovery and its reporting partition

`PatternInventory` is a separate analysis layer over the residual helpers. The
normal solver is unchanged. Seven recognition outcomes classify each normalized
formula; original source records retain exact syntax and name bindings. A fixed
policy yields a deterministic outcome vector for every valid finite input.
Its cells cover the input space, including unresolved cases. This says nothing
about polynomial solution of every cell or a useful compact universal oracle.

The direct single-parity recognizer scans the source and checks a half-cube clause
count and common forbidden parity, within a default eight-variable width cap.
It never enumerates a truth table to find hidden affine structure. General
overlapping equations and arbitrary CNF equivalence to an affine relation remain
outside that recognizer. Other tested properties are Horn/dual-Horn/2-CNF syntax,
uniform witnesses and the existing explicit matching representation.

Independent components split without increasing conditioning depth. Each child
has strictly fewer variables, and the checker reconstructs the complete parent
clause list with disjoint child supports. Variable conditioning decreases the
remaining depth and retains both exact residuals. These decreases establish
termination of the bounded planner on finite inputs. At most four candidates
per unresolved node and depth one are the defaults; configuration permits up
to 64 candidates and depth three. A cap refuses further discovery, not SAT.

Every attempted alternative is retained. Increasing depth can grow the number
of attempted branch paths exponentially before residual sharing. Classification,
sorting, normalization, key serialization and checking revisit input payloads;
the count of selected nodes does not include all this work. Keys contain full
residual identities, so source/edge copies and metadata also occupy space.
The inventory itself emits no verdict; the comparison separately runs the
unchanged potentially exponential solver on every input, including unresolved ones.
The Python code and these ledgers are outside Lean's implementation refinement.

On 664 inputs, two-level analysis adds 1.702 s, bringing analysis plus solving
to 2.021 s versus 0.301 s for solving alone. It stores 2,801 pattern nodes with
3,688,352 logical bytes and 664 source records with 452,011 bytes. SQLite including
the ordinary solver grows from 385,024 to 6,459,392 bytes. Cold full-archive
verification grows from 20.49 to 362.41 ms. A separate six-case memory diagnostic
increases peak traced Python allocations from 60,634 to 205,298 bytes; this
excludes native SQLite/RSS and is not the full corpus memory peak.

Coverage rises from 39/152 to 102/152 among non-exhaustive inputs. The reported
unresolved-literal aggregate counts distinct selected normalized leaves per
input, not globally unique archive data or tree multiplicity. It falls from
16,779 to 1,970, partly because one large explicit parity example becomes closed
after conditioning. These are coverage measurements, not a general search-cost
bound. See the [inventory study](../experiments/results/cnf-pattern-inventory/README.md)
for the unresolved cells, initial comparison, exact archives and limitations.

## 13. Explicit affine extraction and coupling interfaces

The optional `explicit-affine-v1` inventory policy adds extraction of all complete
sign halves grouped by clause support. It retains a pointwise-equivalent mixed
representation F(x) = (A x = b) AND R(x). R contains every clause not assigned to
a complete direct equation. No independent composition across shared variables
is assumed. A separately checked triangular row-operation trace preserves the
equation solution set. An inconsistent extracted subsystem refutes F regardless
of R. A consistent subsystem with R nonempty does not establish tractability.

Let normalized input have L literal occurrences, m clauses, n densely numbered
variables, and let extraction return e equations with S variable occurrences.
Grouping scans L and sorts supports and group keys. Conservative comparison
work is O(L log(L+1) + m log(m+1)); hashing and integer bit costs also apply.
Completeness is checked from the present group cardinality without constructing
2^q entries. A direct width-q parity source already contains q*2^(q-1) literal
occurrences. Reading it remains exponential in q and polynomial in its explicit
input size. Hidden affine equivalence is outside this recognizer.

Elimination and its independent checker each perform at most e min(e,n) XORs
on n-bit masks. Forming masks from S support occurrences also takes bit work
(a conservative O(S*n) bit envelope for the current integer construction).
The certificate holds O(m) clause-reference entries, O(S) variable entries,
O(en) mask bits, and O(e min(e,n)) dependency-index entries. IDs and JSON have
encoding costs. A representation of the equations alone can be much smaller
than the direct CNF, but full source clauses, keys and provenance remain in the
archive. There is no claim that the measured persistent state reaches the
equation-only size. Nor do these per-profile bounds limit the general planner's
number of residuals or the unchanged complete solver's search.

The [733-source study](../experiments/results/cnf-affine-patterns/README.md)
compares this policy to the same planner and solver. At depth two, pattern nodes
fall from 3,790 to 3,126, total analysis plus solving from 3.30542 to 2.90083 s,
SQLite from 14,323,712 to 13,385,728 bytes, and cold full audit from 0.87050 to
0.74019 s. On the original 664 sources, total time is nearly unchanged at
1.84691 versus 1.84100 s. At depth zero, SQLite increases from 5,152,768 to
5,644,288 bytes. Separate six-case peak Python tracing falls from 205,370 to
147,579 bytes at depth two but increases from 116,883 to 133,517 at depth zero.
The timing samples and limited allocation diagnostic do not establish general
speedup or full-process memory bounds.

Four growing coupled controls remain open: a binary clause connects just two
variables of an otherwise explicit affine system. At 32 equations, the source
has 66 variables. Exact existential projection onto that interface is the next
target. Recognition, row projection, compatibility, witness lifting, invalidation
and cold checking must be charged. Arbitrary leftover constraints can still
encode general SAT, even if the affine projection itself is cheap.

## 14. Exact affine projection with bounded boundary materialization

`ProjectionPatternInventory` now rewrites F = A AND R by eliminating only
variables H of A absent from R. Checked internal-first row operations give
boundary equations B with (exists H, F) equivalent to B AND R. Nonpivot internal
variables are free; back substitution through internal pivots lifts every
feasible boundary assignment. The checker validates all dependencies, complete
boundary rows, generated sign halves, exact child identities and strict support
decrease. Projection consumes no conditioning depth. A successful rewrite removes
at least one variable, preserving termination with existing components/branches.

For e equations on n variables and h internal variables, each equation performs
at most min(e,h) eliminations. Discovery and checking therefore each use at most
e min(e,h) XOR operations on n-bit masks, plus row construction/scans and the
earlier extraction costs. Stored row masks use O(en) bits and dependencies use
O(e min(e,h)) index entries, in addition to source references and bindings.
The current compiler materializes each projected width-w equation using
w*2^(w-1) literal occurrences. It checks the aggregate default budget B=4,096
before enumeration and counts an empty contradiction clause as one budget unit.
An encoding miss retains the original formula and planner; it never means UNSAT.
Native affine output would avoid this exponential materialization, but is not
yet integrated into mixed residual analysis.

Lifting visits reduced rows, reconstructs pivot values, checks original affine
equations and checks the entire parent CNF. It uses O(en+S+L) coefficient/literal
visits in a conservative dense accounting, with integer bit-operation costs
additional. Exact originals, certificate rows, full keys and source metadata
remain stored. No generic minimal-space or incremental-update bound follows.
The Lean composition lemmas extend the existing executable projection theorem
under an explicit remainder-invariance hypothesis. They do not refine this
Python extraction, sparse elimination, encoding, lifting or persistence code.

On [775 matched inputs](../experiments/results/cnf-affine-projection/README.md),
depth-two pattern nodes fall from 3,389 to 3,221; logical node payload falls from
9,983,460 to 6,669,670 bytes, while source payload grows from 1,305,669 to
1,369,994 bytes. SQLite including the unchanged solver falls from 22,913,024 to
19,030,016 bytes. Total analysis plus solving/lifting falls from 4.47144 to
3.75039 seconds, and full cold audit from 1.40055 to 0.98692 seconds. At depth
zero, total time instead rises from 2.17737 to 2.26272 seconds and SQLite grows
by 262,144 bytes. Six-case traced Python peaks rise at both depths; at depth two,
147,595 becomes 153,395 bytes. This excludes native SQLite/RSS.

The six new depth-two closures are growing affine systems with one binary
coupling clause. All project to two variables and close already at depth zero.
At 128 equations/258 variables, discovery falls from 390.46 to 13.13 ms, but
the original-source solver still takes 564.84 ms and lifting adds 0.52 ms.
Avoiding this duplicated solving is an integration opportunity. No additional
depth-two closure occurs among the original 664 sources. Arbitrary leftovers,
missed mixed structure and wide projected equations remain explicit gaps.

## 15. Checked simplification before structural discovery

`SimplifyingPatternInventory` reuses existing unit propagation, then optionally
reaches a whole-residual pure-literal fixed point. Unit traces retain a signed
literal and source-clause reason; pure traces retain the chosen signed literals
in each round. Independent replay reconstructs the reduced child and checks
global opposite-sign absence, including couplings. A full child model extends
through the saved assignments and is checked against the original parent CNF.
The relation is exact existential projection onto remaining variables; model
counts and all assignments on eliminated variables are not preserved.

Let v be the initial number of variables and L the literal count of a normalized
nonconstant node. Discovery's unit scans take O((v+1)L) literal visits in the
worst case, as do the complete sequence of pure scans. The checker independently
sorts polarity maps; a conservative comparison/word-operation envelope for the
whole simplification and its checker is
O((v+1)(L + v log(v+1))). It is not a bit-machine bound: identifiers, clause
references, integer operations and JSON encoding must also be charged. The
current checker is invoked several times during a cold construction/lift.
Family recognition, affine preparation, normalization and persistence are
additional. The stored trace has O(v) literal/reason entries and the temporary
working clause representation has O(L+v) words. These bounds exclude recursive
inventory children and SQLite/native allocation.

Every successful rewrite strictly decreases variable support, so a path has at
most v such rewrites before intervening branch choices. This termination fact
does not bound the number or total size of distinct residuals. Full source
identities, parent CNFs, repeated profile evidence and all tried alternatives
remain stored; semantic reduction does not delete provenance. On the
[841-source comparison](../experiments/results/cnf-simplification/README.md),
depth-two nodes fall from 6,358 to 3,526 and SQLite from 39,727,104 to 31,731,712
bytes, but logical source payload grows from 1,570,077 to 1,686,976 bytes. The
1,162 simplification edges share 550 children within the policy/depth identity.
All modes still acquire the same 2,146 ordinary solver residuals.

Total depth-two analysis plus original solving/lifting falls from 8.09694 to
7.15375 s; cold checking from 2.72370 to 2.43583 s. Units-only is faster at
6.60422 s, with 289 rather than 290 closed non-tiny sources. Pure-only and
depth-zero combined processing regress in time. The six-case traced Python
peak falls only from 153,371 to 152,490 bytes at depth two and increases at
depth zero; it excludes native memory and is not a full-corpus peak. Repeated
scans and unused pre-decomposition parent profiles remain measurable costs.
Most discovery time now lies in the new random 3-CNF group (3.26227 of 4.62418 s),
where 38/48 inputs remain open. Both discovery policy and decision integration
remain unproved opportunities, not unrestricted polynomial-time guarantees.

## 16. Conditioning policy and intermediate-state acquisition

`ShortestClauseInventory` ranks variables by positive/negative shortest-clause
occurrence product, then shortest-clause sum, then total occurrences, with IDs
as the deterministic final tie-break. Its policy is versioned; old frequency
records are unchanged. Ranking takes O(L + v log v) comparison/word operations
and O(v) count entries, with O(log m)-bit products up to constants for m clauses.
Cold checking independently recomputes the order. The exact OR partition and
support-reducing simplification are unchanged. Input edits require fresh source
identities and ranking; arbitrary-isomorphism invariance is not claimed.

Equal candidate caps and depth do not mean equal realized work. On the
[949-source study](../experiments/results/cnf-conditioning/README.md), cap-four
unit-only candidate attempts fall from 4,300 to 3,956, yet nodes grow from 9,162
to 11,224. Repeated child references fall from 3,344 of 11,839 to 2,469 of
13,026. Total time rises from 17.20315 to 20.24553 s and SQLite from 79,118,336
to 96,911,360 bytes. The selected unresolved-literal sum improves from 33,281
to 26,784; it is therefore not a sufficient total-cost objective.

Logical node payload rises from 35,730,036 to 44,967,792 bytes. Simplification
nodes account for 8,405,501 of that 9,237,756-byte increase. Their explicit
unsimplified sources, profiles, traces and children are a concrete acquisition
target. Combining the conditioning assumption and unit reasons in an exact edge
to the final residual might avoid some copies and repeated recognition. This is
not implemented; reconstructing and checking the intermediate restriction still
costs work, and not all simplification bytes would disappear.

The separate six-case traced Python peak is 152,392 versus 153,174 bytes and
does not measure full-corpus peak or native memory. Cold audit rises from 6.26480
to 7.64375 s. Warm inventory time is 107.98 versus 103.65 ms. All five modes retain
the same 4,034 ordinary solver residuals. A cap-eight frequency baseline reaches
332/437 closure but costs 42.11042 s and 194,686,976 SQLite bytes; cap-four
short-clause ordering reaches 330/437 and combined unit/pure reaches 329/437.
These are non-dominating synthetic results. There is no general optimal-policy,
compact-decomposition or unrestricted polynomial acquisition bound.

## 17. Fused conditioning and checked closure

`FusedConditioningInventory` omits a separate conditioned node only when the
existing planner would immediately simplify it. The edge retains unit/pure
reasons and composes the child binding into parent IDs. Its OR context supplies
the assumption. Checking reconstructs the normalized restriction, verifies the
old family/component gates and exact closure, and validates the final child.
Recognized families, component splits, root/source records and older archives
retain their behavior. For each branch b, the child represents exactly
`exists h, F(x=b,y,h)` on its remaining variables y. A model lifts through the
assumption and saved assignments and is checked against F.

Let A count incoming fused edges and U their distinct old intermediate nodes.
The old representation stores U full CNFs, keys, profiles and traces, plus
incoming references. Fusion stores A traces and final-child bindings/references;
the intermediate restriction is reconstructible from the parent and assumption.
It can duplicate traces formerly shared by a node. Full recognition and checks
are still performed per uncached context, so A much larger than U can erase a
time/space advantage. No uniform reduction follows, and original-source
retention remains proportional to its recorded encodings.

On the [matched comparison](../experiments/results/cnf-fused-conditioning/README.md),
shortest-clause processing omits 4,943 distinct intermediates using 5,428 fused
edges. The traces cost 430,620 JSON bytes. Logical node bytes fall from 44,967,792
to 25,908,912, and SQLite from 96,911,360 to 65,572,864. Source payload grows by
123,370 bytes for policy metadata. Total time falls from 21.16978 to 17.63829 s
and full cold audit from 7.89184 to 6.93005 s. Frequency and combined policies
also improve, while an in-memory 48-case pilot regresses slightly in runtime.
All 3,999 OR plans preserve their choices and final CNF/depth/bindings; semantic
coverage and all 4,034 ordinary solver residuals are unchanged.

Repeated classification increases (shortest-clause calls 22,448 -> 23,418), while
normalization payload and full-node persistence decrease. A targeted six-case
traced Python peak falls from 5,682,777 to 3,756,516 bytes; the older easy-case
diagnostic instead grows slightly. Neither includes native memory or full-corpus
peak. Warm replay also has small regressions in two policies. Preserved counters
and timings distinguish removed storage from avoided computation.

Remaining shortest-clause logical payload is mostly unresolved nodes and OR
alternatives: 12,124,411 and 11,510,391 bytes respectively. Bounded probing that
proves additional forced values is the next discovery opportunity. Its work and
certificates must be included even if it avoids spending a branching-depth level.
No efficient complete arbitrary-CNF classification has been established.

## 18. Bounded checked failed literals

The optional policy probes at most k binary-incidence variables, two assumptions
each, at a unit fixed point after earlier reduction gates. The first checked
conflict forces the opposite value; its checked unit closure reaches the child
without another full intermediate record. Inconclusive traces remain archived.
Each successful rewrite strictly reduces support but retains arbitrary-branch
depth. Thus k is a per-residual limit, not a total-work limit. Every new reduced
or conditioned residual can restart probing.

With v variables and L literal occurrences, the current scan-based propagation
uses at most v+1 passes per assumption. A conservative probe-phase bound is
O(k(v+1)L + v log v) word operations, including reason replay up to constant
factors, apart from existing classification, normalization, full keys and
persistence. Per-residual trace bits are O(kv log(v+m+2)) for m clauses. A chain
can contain up to v forced rewrites; distinct branches, components, alternative
plans and source retention must also be charged. No global polynomial-size
closure or uniformly efficient arbitrary-SAT expansion follows.

The [1,025-input comparison](../experiments/results/cnf-failed-literal/README.md)
raises non-tiny closure 358/513 -> 484/513, while total time falls 27.11056 ->
18.87839 s, SQLite 93,143,040 -> 65,056,768 bytes, nodes 8,761 -> 5,271 and cold
checking 10.07933 -> 6.41165 s. These costs include the same ordinary solver,
with 5,379 retained residuals in every mode; solver-only time is 7.62782 s.
Four-variable probing retains 17,352 attempts and 2,958 forced rewrites, while
arbitrary conditioning candidates fall 5,552 -> 1,241. Inconclusive attempts
alone cost 1,603,667 JSON bytes; policy metadata adds 199,875 source bytes.

The targeted six-case Python peak falls 3,776,338 -> 1,968,117 bytes, excluding
native memory and full-corpus peak. Warm time slightly rises. Probe nodes now
dominate logical state, 12,544,663 of 22,743,434 bytes. On the 29 remaining
misses, probing every binary variable closes only two more and increases
inventory-only time 6.81731 -> 11.49531 s and SQLite 20,533,248 -> 24,760,320
bytes. This diagnostic argues against unconditional cap escalation.

Both assumptions already propagate a common literal in 245 clear-probe archived
nodes, including 179 unresolved nodes. Those unit reasons can support a new
forced consequence by case splitting without another propagation search. This
is an identified opportunity, not an implemented saving or new root closure.
Shared trace storage, checking and invalidation still need explicit accounting.

## 19. Common consequences: smaller residuals can cost more

`CommonConsequenceInventory` preserves the old failed-literal probe sequence. If
it ends without a conflict, the policy intersects each pair's checked unit
assignments, chooses the first nonempty intersection and applies every common
literal of that pair. The parent entails these assignments by Boolean case
splitting. Their restricted CNF and checked unit closure preserve exact
existential fibers; support strictly decreases and arbitrary-branch depth stays
unchanged. Both implications, all inconclusive attempts and exact source/model
bindings remain checked and stored. No probe search is repeated to form the
intersection, but closure and later residual acquisition still cost work.

At most 2kv unit entries are scanned for k variables and v-unit traces. Expected
hash-set work is O(kv), with O(v log v) sorting of the retained intersection.
The added pair/literal witness needs O(v log(v+k+2)) bits. Scan-based closure
costs O((v+1)L) for L literal occurrences, with its reason trace additional.
All full CNFs, keys, profiles, child acquisition and replay costs remain charged.
This local bound does not control the global number of rewritten residuals.

On the [1,101-input study](../experiments/results/cnf-common-consequence/README.md),
closure rises only 536/589 -> 537/589, with no fresh-random gain (40/64 both).
Total time grows 32.12172 -> 32.75928 s, SQLite 104,435,712 -> 107,757,568 bytes,
and cold audit 12.03279 -> 12.56291 s. Selected unresolved literal payload falls
9,728 -> 8,101, but probes grow 29,280 -> 31,745 and logical node bytes grow
38,929,223 -> 40,749,002. The 477 common rewrites assign 663 literals; 355 share
the exact original probe lists with matched baseline CNF/depth nodes. Witnesses
and closures use only 34,415 JSON bytes, while probe-node payload grows by
2,410,587 bytes. The change in acquired residuals outweighs compact local evidence.

The policy remains optional. The six-case Python peak and warm time slightly
increase; full-corpus peak and native memory are unmeasured. All modes keep the
same 7,393 ordinary solver residuals, and solving alone takes 9.22197 s. The
next discovery opportunity is signed equivalence from opposite implications in
the paired traces. Selected-path counts restrict that opportunity to 16 nodes
on 16 of the 52 missed source paths; its substitution and costs are unimplemented.

## Follow-up: checked signed substitution (9 November)

The optional [paired-probe equivalence experiment](../experiments/results/cnf-probe-equivalence/README.md)
reuses checked implication traces and substitutes all clauses, preserving exact
existential fibers with signed model lifts. For k candidate variables, d occurring
variables and ell literal occurrences in this experimental CNF representation,
intersection costs expected O(k d) set work plus O(d log d) sorting; substitution
visits ell occurrences and emits at most ell before normalization. The witness
uses O(d log(d+k+2)) bits. These additions do not include existing probe acquisition
and checking, normalization, child recognition, persistence or the number of
acquired descendants. One merge chain has at most d-1 rewrites; this does not
bound the whole graph by a polynomial. In particular, the analysis does not
turn the unchanged independent general SAT solver into a polynomial algorithm.

On 1,137 matched sources, non-tiny closure improves 567/625 -> 574/625 while time
rises 38.293 -> 39.731 s, database 130.597 -> 135.569 MB and cold replay 15.208 ->
15.856 s. Logical node bytes rise 50.062 -> 52.575 MB; selected unresolved
literal occurrences fall 10,300 -> 9,674. A targeted six-case traced Python peak
falls 14.564 -> 11.586 MB, excluding native SQLite, RSS and full-corpus peak.
Reduced local support, live allocation on selected cases and durable whole-graph
storage are different quantities. The policy remains optional; no new uniform
arbitrary-SAT time or memory bound follows.
