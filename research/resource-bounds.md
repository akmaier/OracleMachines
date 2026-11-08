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

The first priority can differ by workload: normalization helped changing
multiplicities, source handling dominates much of already-reused work, novel
batches still pay elimination, and database telemetry/indexes dominate much of
the current retained file. We should keep these separate when selecting the
next optimization rather than assigning one universal bottleneck.
