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

## Follow-up: bounded local learning (9 November)

The optional [local-learning experiment](../experiments/results/cnf-probe-learning/README.md)
adds at most q proved binary clauses for one further k-candidate probe pass.
With d variables, m2 binary clauses and ell literal occurrences at a node, at
most 2kd saved unit entries provide candidates. Binary-path filtering currently
costs expected O(ell + kd(d+m2+q)); a batch adds at most 2q occurrences before
reduction. Repeated-scan continuation propagation costs O(k(d+1)(ell+q) + d log d),
in addition to checking, normalization, recognition and persistence. Both original
and continuation traces remain in the archive, including unsuccessful attempts.
Only a strict support reduction acquires a child, so clause-only learning cannot
recurse. There are at most d successful learning edges along a support-decreasing
path; this is not a polynomial bound on the acquired graph or lifetime storage.

On 1,173 sources, closure improves 604/661 -> 607/661 non-tiny, while time rises
48.177 -> 52.697 s, SQLite 163.533 -> 168.268 MB, cold replay 20.785 -> 22.013 s
and targeted Python peak 18.466 -> 20.378 MB. Peak excludes native SQLite/RSS and
full-corpus memory. Four fewer pattern nodes still require 3.108 MB more logical
node storage. The additional probe pass is charged, not an equal-total-budget
comparison. Of 15,052 continuation probes, 10,018 reproduce an original certificate
exactly; incremental fixed-point checks and shared proofs are the next opportunity,
not a measured saving. No uniformly efficient arbitrary-SAT bound follows.

## Follow-up: checked unit-closure references (9 November)

A checked closure with u assigned units and q binary additions can be reused
under the same assumption if every addition is satisfied or retains at least
two unassigned literals. Constructing its assignment map and testing additions
cost expected O(1+u+q) time and O(1+u) temporary space. The complete original
proof is still acquired, stored and checked; the saving is the repeated source
restriction/propagation/fixed-point scan. For probe cap k >= 1, a reference takes
O(1+log k) bits before framing, while the original proof remains retained. The
expanded checker uses aliases rather than copying referenced unit lists.

With r reusable continuations out of at most 2k, d variables and ell original
literal occurrences, the probe portion costs at most
O(ell + d log d + r(d+q) + (2k-r)(d+1)(ell+q)) with the current scan engine.
The retained opposite/common closures, original checks, batch discovery,
normalization, complete plan, persistence and cold replay remain charged.
No favorable bound applies if every addition activates the old closure or if
all choices are fresh. The unrestricted number of distinct nodes remains open.

The [1,209-source study](../experiments/results/cnf-probe-closure-compact/README.md)
preserves all semantic plans and 634/697 non-tiny closures. It reuses 14,705
continuations; 672 active repeated and 2,171 fresh assumptions still propagate.
The compact sample changes total time 62.759 -> 61.687 s, SQLite 197.104 ->
196.096 MB, cold replay 26.785 -> 25.094 s and the same six-case Python peak
20.378 -> 20.022 MB. The allocation bound excludes native SQLite/RSS and the
full corpus. Timings are single samples, with checkpoint overlap disclosed.

Local proof bytes fall by 807,098, but the first version grows SQLite to
200.323 MB because full keys repeat a new policy field. That failed version is
retained. A distinct replacement tag avoids the extra field and gives the
compact totals above. Therefore proof compression, namespace overhead, decoded
live memory and physical SQLite allocation must remain separate accounts.
No universal runtime or storage improvement, competitive SAT speedup or
polynomial arbitrary-SAT construction follows from this supporting optimization.

## Follow-up: bounded selection among proved clauses (9 November)

`SelectedLearningInventory` considers at most p=16 eligible clauses from saved
original-source implications, retaining at most q clauses under the unchanged
per-node cap. It prefers newly activated saved closures, a new origin assumption,
total activated closures, then original pool order. A closure activates when the
candidate is unsatisfied and has fewer than two unassigned literals. The checker
reconstructs this selection only after validating every original implication.
Any selected subset preserves source models independently of ranking quality.

With k probe variables and d source variables, assignment maps for at most 2k
closures require expected O(kd) time/space; p binary candidates cost O(pk) delta
visits. Greedy choice examines at most pq scores. The implemented k <= 64 bound
keeps each activation mask within a bounded number of words; if k is treated as
unbounded, bitwise operations and population counts must charge its bit length.
Pool graph filtering still costs up to expected O(ell+kd(d+m2+p)) under the
current selector, in addition to these scores, continuation propagation,
verification, descendant acquisition and persistence. Actual chosen size is
min(q,p). Equal per-node caps do not bound or equalize whole-graph work.

Filtering can use edges from earlier pool candidates that ranking later omits.
Their individual implications remain proved on the original source, so omission
cannot make a selected clause unsound; it can make the candidate pool less useful.
Neither the fixed pool cap nor the activation score provides complete discovery,
optimal selection, a universal speedup or a compact arbitrary-SAT representation.

The [1,245-input comparison](../experiments/results/cnf-learning-selection/README.md)
has unchanged 662/733 non-tiny coverage: one gained and one lost source closure.
Total time rises 71.417 -> 73.194 s, SQLite 227.385 -> 227.832 MB, cold replay
29.815 -> 30.359 s and six-case traced Python peak 20.022 -> 20.121 MB. Peak
excludes native allocations, RSS and the full corpus. Runs are single sequential
samples without concurrent tests, builds or commits. Logical probes rise
82,036 -> 82,782 and nodes 14,592 -> 14,653 despite fewer conditioning candidates
and unresolved literals. Selection charges 203,218 delta literal visits and
47,472 score evaluations across acquisition/checking. Warm reuse inserts nothing;
all new and preceding archives replay byte-identically.

The next controlled policy will freeze continuation choices to those induced by
the old batch while applying the new clauses, charging both batch/ranking work.
Its total cost and coverage are not yet measured. Local controls establish that
the choice order can change the first forced variable and subsequent acquisition;
a successful local reduction alone predicts neither source closure nor savings.

## Follow-up: selected clauses with baseline continuation choices (9 November)

`FixedOrderLearningInventory` reconstructs the old first-four batch from the
checked original probe traces, ranks variables on that augmented formula, then
propagates the selected batch using the reconstructed variable list/order. The
same procedure runs during independent checking; a persisted choice hint is
never trusted. The original phase, strict support reduction, recognition
priorities and per-node caps remain unchanged. A distinct replacement policy tag
keeps all preceding archives valid and separate.

For each eligible continuation, reconstruction adds expected
O(ell+kd(d+m2+q)) work for the old bounded implication filter, plus
O(ell+q+d log d) for binary-frequency ranking. Here ell is the source literal
count, d its variable count, m2 its binary clauses, k probe variables and q the
retained-clause cap. Temporary graph/maps, the augmented clause sequence and
repeated checks are also charged. No second propagation pass is introduced at
that same continuation, but later acquisition can still change. Fixed choices
at one exact parent do not freeze its child formula, later ranks or first
conflicts under different learned clauses.

The [1,281-input comparison](../experiments/results/cnf-learning-fixed-order/README.md)
has identical **692/769** non-tiny and **18/24** fresh closure under baseline,
selected and fixed-order policies. Fixed order retains the same gain/loss pair
as selection. Total time is **77.916 / 82.421 / 80.720 s**, SQLite **252.244 /
252.498 / 252.391 MB**, and cold replay **33.506 / 33.585 / 34.309 s**. The same
six-case Python peak is **20.022 / 20.121 / 20.127 MB**; native memory/RSS and
full-corpus peak are excluded. These are single sequential samples, without
concurrent tests, builds or commits during measurements.

Fixed order charges 6,418 reconstructions and 25,662 ranked candidate positions
across acquisition/checking; learned candidate visits grow 152,026 -> 254,742
versus selection. Its logical node bytes grow despite slightly lower SQLite
bytes; the shorter policy tag also affects keys/source records. Relative to
baseline, nodes rise 16,052 -> 16,126 and probes 89,782 -> 90,713, while selected
unresolved literals fall 18,362 -> 17,971 without greater source coverage.

The saved 956 control has identical forced assignments and the same 54-clause
restricted original core, yet three versus four retained redundant additions
change descendant closure. This motivates sharing a checked semantic core and
keeping propagation hints separately. Construction, hint checking, context-aware
discovery state, invalidation, canonicalization and persistence must all be
charged. No cost or coverage improvement from this next representation is yet
measured; arbitrary semantic equivalence recognition is not assumed available.

## Follow-up: parent-scoped hints and original-clause cores (9 November)

`CoreLearningInventory` first checks the same fixed-order learned continuation
in full. On a successful nonterminal reduction, it restricts or substitutes
only the original parent CNF to obtain the child. Checked terminal conflicts
remain false. Hints and their source proofs stay at the parent; descendants
acquire their own hints. This first version does not implement inherited hint
transport or context-sensitive reuse of descendant plans.

After the already charged augmented reduction, core construction adds expected
O(ell+q+d) time and O(ell+d) temporary space, with source literal count ell,
q learned binary clauses and d variables. Restriction/substitution, support
checks and omitted-occurrence counters all contribute. The checker still builds
the augmented target first. Acquisition, proof checking, parent hint storage,
child normalization, full keys, serialization and cold replay remain costs.
Equal normalized cores at equal depth/policy can share child nodes because
no parent hint context is inherited. This only recognizes explicit source-based
equivalence; it does not supply general semantic canonicalization or a bound
on the lifetime number of cores.

The [1,317-input comparison](../experiments/results/cnf-learning-core/README.md)
closes **719/805** non-tiny sources versus **718/805** for baseline/fixed order,
without losing any closure. Baseline/fixed/core total time is **94.870 / 97.402 /
97.835 s**, SQLite **284.111 / 284.299 / 284.094 MB**, cold replay **40.281 / 41.160 /
40.384 s**, and the same six-case Python peak **20.022 / 20.127 / 20.265 MB**.
These single sequential samples exclude native memory/RSS and full-corpus peak.
The selected pilot savings do not generalize; core is 3.13% slower than baseline.

Core retains **17,833** pattern nodes and **113,536,866** logical node bytes, of
which **72,386,084** (63.76%) are probe records. There are 1,347 core checks and
3,156 omitted clause / 6,312 omitted literal occurrences across repeated checks.
None of its 449 learned parents shares a child core with another learned parent
in this run. Thus the changed coverage demonstrates altered discovery, not broad
measured core merging. Distinct policy tags, logical payloads, physical SQLite
pages and traced live allocations must remain separate accounts.

Diagnostics find 907 eligible transported hint occurrences absent from the
immediate cores; 319 are learned again across 165 children. These are occurrences,
not distinct reusable facts or saved seconds. Transporting this evidence is the
next controlled discovery experiment. It must charge source/reduction/variable
checks and keep hint-dependent propagation context separate from shared core
identity. The largest unresolved source 1297 has only one successful learned
parent; restriction and unit checking/propagation dominate its separate profile.
Avoiding repeated scans remains a broader supporting target. Uniform efficient
arbitrary-SAT acquisition and lifetime storage bounds remain unproved.

## Follow-up: portable core-hint certificates and explicit local plans (9 November)

The new transport primitive fully checks its parent, translates unit-reason
prefixes through the exact assignment/substitution and normalized variable map,
then independently checks a unit refutation of each negated candidate clause
on the child core. No parent proof is needed for portable replay. Exact core and
clause payloads bind the record; all earlier proofs/archives remain preserved.
All 1,005 eligible occurrences in the [494-edge study](../experiments/results/cnf-hint-transport/README.md)
translate without fresh proof search, yielding 984 distinct core-clause records.
This is a measured scope, not a universal completeness result.

Let L be parent literal volume, q the bounded retained-hint count, and R the
literal volume of examined mapped reason clauses. Beyond full parent validation,
the implementation uses expected O(qL+R) map/prefix work, plus core normalization
and independent proof checking. It currently normalizes the core for every hint.
Each proof lookup validates the complete core/clause binding and every cited
unit/conflict reason; full-key comparison and serialization are not constant-time.
Storing full cores in keys/payloads adds O(qL+R) logical payload before context
plans and descendants. Variable-label bit costs and the lifetime number of cores
remain separate. This does not bound unrestricted SAT proof discovery.

The prefix walk visits **11,510 literals** versus **287,160** for fresh proof
search on the same supplied candidates. Transport preparation costs **0.95129 s**,
including full parent replay and index reconstruction. Conditional fresh proof
search/checking/persistence costs **0.93100 s**; these different scopes do not
support a wall-clock speedup claim. Fresh-source generation/solving costs another
**8.87824 s**, separately recorded. Previous parent acquisition is preserved and
is not erased by converting its proof.

The explicit hint plan keys core, ordered hint set, depth and policy, and adds one
bounded pass before the unchanged core planner. Earlier recognition priorities
are checked on the core. Local closure rises **223 -> 224 / 494**, with no losses,
but no whole-source gain: the one gained child is outside all saved selected
source paths and is explained by changed probe choices. Operation time rises
**14.41354 -> 16.82765 s**, or **17.77895 s** including transport preparation.
SQLite grows **55.120 -> 63.885 MB**, cold replay **4.70738 -> 7.72522 s**, warm
lookup **0.06691 -> 1.31088 s**, and six-core Python peak **7.372 -> 7.431 MB**.
Peak excludes preparation, native memory/RSS and the full corpus. These are
single sequential samples, not an industrial comparison or significance estimate.

Ordinary node payload falls **11.158 -> 9.943 MB** across **2,167 -> 1,999 nodes**,
but portable proofs add **2.181 MB** and 494 explicit context plans add **3.097 MB**.
Logical probes rise **14,468 -> 16,136**. Inconclusive extra passes repeat work
before falling back; 180 are clear and 83 skip because of eligibility/priorities.
Four new archives replay byte-identically and warm reuse inserts nothing.

Next isolate core-based continuation ranking with existing batches and passes.
The changed local case closes under either batch only when the core's fourth
variable (19) replaces the baseline continuation's fourth variable (11). A
separate diagnostic finds 1,456 inactive and 102 active hint deltas across 196
original-probe cores. Checked closure reuse can later avoid repeats in an existing
pass; these counts do not establish saved probes or justify omitting hint context.


## Follow-up: reuse of checked core ranking (9 November)

The [core-order experiment](../experiments/results/cnf-core-order/README.md)
extracts the p original variables from a fully checked, complete clear probe
trace in O(p) time and temporary reference space. The original discovery/checker
still reconstructs source ranking and validates every reason. Clause selection,
active-batch propagation, normalization, exact child checking and persistence
remain charged. This replaces the old auxiliary batch reconstruction and ranking;
it does not bound total graph size or complete arbitrary-CNF acquisition.

Same local caps do not mean equal global work. On 1,389 matched queries, operation
time is **120.81853 -> 116.67493 s**, discovery **88.69202 -> 85.68326 s**, and
SQLite **347,566,080 -> 346,976,256 bytes**. Old-input closure drops 719 -> 718 / 805;
full non-tiny closure drops 776 -> 775 / 877, with only source 956 lost. Both
combined modes retain 18,104 ordinary solver residuals; the solver's 1.13 s runtime
variation is not attributable to this heuristic. New unresolved literal occurrences
rise 26,137 -> 26,734. The policy stays optional.

Pattern nodes fall **21,122 -> 21,005**, logical node bytes **137,740,084 ->
137,076,682**, while source bytes rise **5,225,670 -> 5,250,240** across the same
1,365 distinct source records. Cold replay costs **50.51029 -> 47.82982 s**, warm
lookup **0.25672 -> 0.22710 s**, and separately timed initialization **0.06160 ->
0.22272 s**. Three full, three pilot and four previous archives replay unchanged.
Six-case Python peak is **20,265,108 -> 19,623,309 bytes**, excluding native SQLite,
RSS, preparation outside that diagnostic and full-corpus peak. Single sequential
samples are not a significance estimate or industrial comparison.

The old 8,772 ranking reconstructions disappear; new extraction performs 8,106
calls / 32,326 candidate copies across discovery/checking. Learning graph literal
visits fall 6,433,538 -> 3,516,760 and candidate visits 336,186 -> 185,626. Reused
continuation probes rise 24,672 -> 27,611, active original probes 1,492 -> 1,700,
and novel probes fall 3,527 -> zero. These counts include different descendants
and repeated checks, so they are not paired per-state work differences. Logical
probe attempts are 119,412 -> 118,152. Eliminating novel probes also eliminates
useful reductions: 239 shared states lose a learned reduction, while sixteen gain.

All 255 gained/lost shared CNF/depth states have at most four variables in the
union of active core candidates and novel old-ranking candidates. Seven other
changed shared states have five. This supports a next bounded selection experiment,
not a uniform candidate-size theorem or a new recovered-source result. Choosing
only reusable state is insufficient; accounting must include discovery beyond it.
The first-cap learned batch is a prefix of the already acquired sixteen-clause
pool for caps at most sixteen, allowing a separate future optimization that retains
old choices. Both proposals must charge preparation and checking.

The new unresolved frontier has 102 sources / 142 distinct leaves. Source 1194
costs 1.45407 s discovery; its instrumented profile records 5,307 restrictions,
4,311 simplification checks and 2,069 propagation calls. Probe-kind nodes occupy
87,079,296 bytes of logical state, including full identities and other fields;
probing fields alone occupy 15,272,772 bytes. Propagation/state reuse remains a
broader target than cheap choice extraction. Global efficient classification and
lifetime memory bounds are still open.


## Follow-up: activity-based continuation and measured limits (9 November)

The [activity policy](../experiments/results/cnf-activity/README.md) retains old
informative candidates, omits only pairs with two checked unchanged closures,
and fills freed positions with active original-core variables. Original traces
persist, and selected-batch/activity decisions are reconstructed after full source
checking. A fixed source/batch retains any old local reduction; higher-priority
new reductions and changed descendants prevent a whole-planner monotonicity claim.

Beyond the still-present auxiliary ranking reconstruction, selection adds expected
**O(U + p*q + p^2)** unit-cost work for total original unit-trace length U, probe
cap p and binary batch size q. The quadratic term charges list membership while
appending candidates. Temporary state is O(p + u_max), beyond existing traces and
batch, for the largest unit trail u_max. Original acquisition, verification,
normalization, active/new propagation and full-key persistence remain costs.
This is not a bit-machine runtime refinement or unrestricted-SAT acquisition bound.

On 1,425 queries, non-tiny closure stays **806/913** with no losses or gains.
Continuation attempts fall **31,741 -> 7,184**, total logical probes **127,741 ->
103,413**, and verified probes **250,703 -> 223,315**. Reused continuation probes
fall **26,407 -> 1,615**, but active/new propagations rise **5,334 -> 5,569**. Thus
most omitted work is repeated handling of unchanged closures, not avoided fresh
solving. Across discovery/checking, 9,460 choice calls record 3,088 empty
continuations, 28,424 omitted inactive positions, 682 added positions and 36
truncations. These are repeated-operation counts over different descendants.

Single full-run operation time falls **161.35645 -> 134.22746 s**, discovery
**116.82649 -> 99.01207 s**, while the unchanged solver varies **44.42359 ->
35.13847 s** between combined modes. Balanced ABBA BAAB trials on eight sources
instead average **3.85140 -> 3.88671 s** total and **3.64992 -> 3.68110 s** discovery.
Their answers, summaries, counters, storage and database hashes repeat exactly
within each policy. These limited controls do not establish significance or a
full-corpus estimate, and do not support a runtime speedup claim. Preserve the
negative timing result with the deterministic work reduction.

SQLite bytes are **376,205,312 -> 375,824,384**, pattern nodes **22,549 -> 22,581**,
logical node bytes **148,631,944 -> 147,670,431**, probing fields **16,760,009 ->
15,465,288**, and source bytes **5,405,961 -> 5,422,677** over 1,393 records. Cold
replay grows **55.11608 -> 57.63553 s**, warm lookup **0.27624 -> 0.34976 s**, and
separately measured initialization **0.06187 -> 0.28580 s**. Six-case traced Python
peak falls **20,265,108 -> 19,996,930 bytes**, excluding native SQLite, RSS and
full-corpus peak. Both modes retain 19,557 independent solver residuals; three
full, three pilot and three prior archives replay byte-identically. Earlier
results and proofs remain available.

The selected unresolved literal occurrences fall **28,314 -> 28,170**. Source
977 now uses the formerly unselected local case-97 core, leaving one leaf with
22 literals rather than two leaves with 138. The frontier has 107 open sources
and 147 distinct leaves: 61 inconclusive continuations (12,984 literals), 39 empty
ones (10,639), 46 clear passes without a batch (4,264), and one without initial
binary candidates (283). Source 1194 costs 1.47590 s discovery; its separate
profile records 5,763 restrictions, 4,657 unit checks and 2,221 propagations.

The next signed-subsumption diagnostic performs 672,003 subset comparisons on
these 147 leaves. Retained-clause witnesses remove 217 clauses / 666 literals
from 105 cores and expose seven 2-CNF cores. The existing selected plans of
977/1044/1053/1365 could become closed after integration; these are prospective,
not measured coverage. Recognition over all planner states, exact core mapping,
model lifting, storage and cold replay still need charging. No deployment runtime
or memory reduction follows from the selected-frontier count alone. General signed
subsumption is established simplification; efficiently covering arbitrary CNF
families remains open.

## Follow-up: terminal signed-subsumption exposure (9 November)

`SignedSubsumptionInventory` adds an optional reduction to the activity policy.
It searches only where earlier recognition, reductions and the configured
conditioning budget have exhausted discovery. It keeps inclusion-minimal signed
clauses and follows the core only if the existing basic classifier recognizes a
family. Failed searches persist alongside the original unresolved leaf. This is
exact syntactic simplification, not general semantic minimization or a new SAT
class. The ordinary decision solver remains unchanged.

For m source clauses, L literal occurrences and maximum width w, each subset
search costs expected **O(L + m log(m+1) + m²w)** unit-cost work and **O(L+m)**
temporary space. Literal identifiers and hash operations use that cost model;
this is not a bit-machine refinement. The checker independently verifies complete
index coverage and retained signed witnesses, then replays the deterministic
policy. Thus checking retains the same quadratic worst-case term, in addition
to profile reconstruction, child normalization and archive costs. Saved witness
indices use **O(m log(m+1)) bits**; complete node keys, evidence, bindings and any
new child remain separate retained costs. Every unsuccessful explored leaf counts.

Every removed clause contains a retained clause with identical literal signs.
The retained core therefore has exactly the same models over the original
universe. Any assignment to variables absent from the core is valid when lifting
a core model. The three new Lean lemmas prove signed inclusion, model equivalence
and this extension property; Python checks the integer/index/normalization
bindings separately. Editing a witness or adding an uncovered clause requires a
new certificate. Old source records and policy namespaces are preserved.

Keeping this transformation at previously unresolved terminal leaves preserves
baseline boolean closure: earlier successful leaves and fixed reductions remain,
AND composition is monotone, and OR search only stops early after a closed
alternative. This argument is scoped to unchanged earlier rules and exact
transports. It is not a Lean refinement of the planner or a runtime/space bound
for arbitrary SAT. Storing both policy versions in one lifetime archive still
retains both namespaces; isolated-mode size comparisons do not erase old results.

The quadratic subset search itself admits a narrower recognition opportunity:
distinct normalized clauses with equal width cannot strictly contain one another.
Length buckets can skip such pairs while preserving the witnesses. That filtering
is not implemented in this checkpoint; its total-cost value must be compared
against the larger propagation and proof-replay costs.

The complete 1,461-query comparison gains four closures (**833 -> 837 / 949
non-tiny**) and loses none. The old subset improves 806 -> 810 / 913; both modes
close 27/36 new queries. Full single-sample operation time grows **145.71977 ->
156.17943 s**, discovery **105.46141 -> 117.30413 s**, while the unchanged solver
varies **40.18383 -> 38.79213 s**. Twelve-query ABBA BAAB controls instead average
**7.28617 -> 6.98024 s** total; these include all four gains and do not estimate
repeated full-corpus performance or establish significance. The candidate remains
optional and makes no general solver speedup claim.

SQLite grows **404,410,368 -> 408,301,568 bytes**, logical pattern-node state
**161,206,197 -> 166,021,306 bytes**, and source bindings **5,617,826 -> 5,837,892
bytes** over 1,429 records. Pattern nodes fall **24,367 -> 24,122**, while saved
subset searches/profiles add 3,706,023 bytes. Cold replay grows **61.80056 ->
66.82085 s**, warm replay is **0.25731 -> 0.24904 s**, and initialization separately
costs **0.05716 -> 0.33504 s**. The same six-case Python peak grows **19,996,938 ->
20,390,270 bytes**, excluding native SQLite, RSS and full-corpus peak. Each mode
retains 20,544 independent solver residuals. All three full, three pilot and three
previous archives replay byte-identically, including every alternative and source.

There are **3,753** terminal searches, **31** local exposures and **3,722** failures.
Discovery and checking each perform **33,367,619** subset comparisons. Exact
saved-prefix analysis identifies **27,083,138 (81.17%)** equal-width comparisons
that cannot succeed; 6,284,481 compare shorter clauses. This is avoidable search
work, not a measured optimized runtime. Logical probes fall 112,276 -> 110,980,
verified probes 242,280 -> 239,308 and conditioning candidates 4,631 -> 4,575.
Those reductions do not establish lower total cost.

There remain **112 open sources / 149 distinct selected leaves**, containing
32,043 literals. The largest unresolved discovery case, 1194, costs 1.60328 s;
its separate profile retains 5,763 restrictions, 4,657 simplification checks and
2,221 propagations. A saved offline control reuses all original proved binary
implications to expose eight more 2-CNF leaves; sources 1185/1289/1368 could
complete their selected plans after integration. These prospective gains are not
counted in 837/949, and their enumeration, proof/transport, persistence and replay
costs remain to be integrated. All **395 tests**, the **4,129 / 1,971** Lean audit,
56 report fingerprints and independently hashed diagnostics pass.

## Follow-up: indexed subsets and original implication reuse (9 November)

`ImpliedSubsumptionInventory` first keeps the original signed-subset exposures.
Only after their failure does it enumerate distinct absent binary consequences
from the already acquired original probe traces and search the augmented CNF
for a recognized core. No fresh probe pass is added. All original reasons are
replayed before reconstructing clause origins, signed subset witnesses and child
bindings. An implication may use a subsequently removed original clause because
its proof is checked against the complete original source, before augmentation.
Failed pools remain persistent. The new Lean composition lemma establishes
model equivalence; it does not refine Python or its costs.

Length filtering preserves the old first-retained-witness policy: check strictly
shorter retained clauses, stop at equal width, and use an exact retained-set
lookup for duplicates. Repeated literals within a clause trigger the old fallback
because list length then differs from cardinality. With P tested shorter pairs,
this costs expected **O(L + m log(m+1) + P w)** work and **O(L+m)** temporary space.
The worst case still has P=O(m²). Original implication enumeration costs expected
**O(L+U)** for unit-trace length U and produces b<=U binary clauses. Augmented
search then has m+b clauses and L+2b literal occurrences. Original proof checking,
origin storage, profile reconstruction, normalization and archive identities remain
charged; validation reconstructs both the pool and the subset policy.

The indexing-only mode retains the previous policy identity and certificate
format, enabling complete old-archive replay without rekeying. The implication
policy has a separate namespace because it can produce different descendants.
The twelve-source pilot closes 1185/1289/1368 and preserves the four prior gains,
with no lost closures. Pilot time falls 9.03940 -> 7.40206 seconds and SQLite
22,654,976 -> 19,824,640 bytes; deliberately selected single samples do not justify
a general speed claim. The full matched results and all failed attempts follow
in the study record.

The full **1,497-query** study closes **864 -> 869 / 985 non-tiny** sources, with
five gains and no losses. Full single-sample total time is essentially unchanged
(**169.84716 -> 169.80609 s**), discovery **127.44196 -> 126.71711 s**, and unchanged
solver **42.32325 -> 43.00260 s**. Twelve-query ABBA BAAB controls average **6.99619
-> 6.17832 s** total and **6.69275 -> 5.88519 s** discovery; they include three gained
sources and do not estimate repeated full-corpus performance or significance.

SQLite falls **438,288,384 -> 437,620,736 bytes**, but logical node payload grows
**178,289,290 -> 179,395,726 bytes** despite fewer nodes (**25,752 -> 25,047**).
Source bindings occupy **6,028,353 -> 6,032,748 bytes** across 1,465 records. Cold
replay is **71.70525 -> 69.97623 s**, warm reuse **0.29428 -> 0.28194 s**, initialization
separately **0.07203 -> 0.32459 s**. Six-case Python peak grows **20,390,278 ->
21,161,046 bytes**, excluding native SQLite, RSS and full-corpus peak. Each mode
retains 21,838 ordinary solver residuals. These are finite measurements, not
bounds on lifetime state or general SAT memory requirements.

The complete old-archive indexing control checks all **24,122 nodes / 1,429 source
bindings**, with identical database bytes and no inserts. Its 3,753 terminal checks
reduce subset comparisons **33,367,619 -> 6,284,481**, avoiding exactly **27,083,138
(81.17%)** futile equal-width pairs. This isolates exact-work/certificate
compatibility, not an end-to-end timing gain. The expanded implication policy
instead has 3,916 terminal searches, 110 exposures (28 original, 82 implied) and
3,684 nonempty pools containing 29,897 binary clauses. Each discovery/check phase
performs 6,744,712 original and 8,990,250 augmented subset tests. The matched naive
baseline performs 35,880,691 tests per phase. Pool construction and width/exact
lookups remain additional work; changed alternatives prevent direct attribution.

Search data grows **3,962,842 -> 9,029,905 bytes**, including **5,086,738 bytes** of
implication evidence. The offline relevance control reduces the pool **29,897 ->
7,505**, retaining all 82 observed exposures and exposing no further frontier leaf.
It costs **2,278,253 relevance comparisons** and reduces augmented subset tests to
7,138,675 per search/check. No integrated storage/runtime or universal syntactic
family-preservation guarantee follows. Filtering and source-bound proof replay
must be included in any follow-up comparison.

The remaining frontier has **116 sources / 148 distinct leaves / 33,651 literals**.
The largest unresolved discovery case is again 1194 (**1.67226 s**). Its separate
profile contains 5,763 restrictions, 4,657 simplification checks and 2,221
propagations. These dominate own-time costs after indexing and motivate exact
prepared-state/proof reuse. Additional coverage requires new relations or exact
decompositions. All 403 tests, the 4,130/1,972 Lean audit, cold checks and 59 report
fingerprints pass; no unrestricted acquisition or compact-closure bound follows.

## Exact checked-probe replay cache (9 November)

`CheckedProbeReuseInventory` adds an ephemeral bounded LRU cache around the
existing complete probe checker. The persistent policy/configuration, source
identities, proof contents and discovery order do not change. A key contains the
complete source, probe evidence and policy configuration. An entry is admitted
only after the old checker succeeds. Full key equality, not a digest match,
licenses reuse; returned values are decoded afresh, so caller mutation cannot
change stored results. Restart starts empty, eviction requires later rechecking,
and source/proof/policy changes miss rather than inherit a result.

The invariant is narrow: each retained entry records a successful check of that
exact semantic input under this fixed checker implementation. It does not certify
new inputs, skip the first proof check or replace persistent proof evidence.
JSON distinguishes integer/bool fields, but identifies tuple/list containers.
The old checker requires original attempts to be a list, so non-list attempts
bypass caching and are handled by that checker before any lookup. This guard is
required: the preliminary implementation admitted a warm-cache type alias in a
malformed direct input. Its code, pilot and counterexample remain available;
the guarded implementation has a regression test. Other CNF/unit-trace iterable
containers have the same semantics under the existing checker. No formal Python
refinement is claimed.

Let K be encoded source/proof/config bytes, R the encoded result size, V the
uncached check cost and B the cache's retained-string budget. Each lookup pays
full serialization and key hashing/equality; a hit also decodes R bytes. Thus
reuse retains serialization work rather than making checking constant-time.
A miss pays the old V as well as key/result serialization and eviction work.
Expected map operations are constant-time after hashing; worst-case collisions
and encoder/sorting costs are not erased. Across the run each admitted entry can
be evicted only once before re-admission. Stored ASCII key/result strings total
at most B bytes; their Python objects and LRU entries add overhead. Transient
key/result construction can add O(K+R) space beyond retained cache state, and
original acquired graphs, source bindings and solver memory remain separate.
Oversized entries are checked without being retained. These bounds do not reduce
worst-case SAT search or establish an optimal cache budget.

The final full comparison uses the same **1,497 inputs** and preserves all answers,
profiles, source identities and database bytes. Coverage stays **869/985 non-tiny**.
Full single-sample time falls **168.30879 -> 150.39216 s**, discovery **125.59834 ->
108.60557 s** and cold replay **71.60183 -> 62.58623 s**. Twelve-query ABBA BAAB means
are **6.17550 -> 5.33388 s** total and **5.88231 -> 5.04230 s** discovery; four trials
per mode on a selected subset do not establish significance or general speedup.

The archive remains **437,620,736 bytes**, with **179,395,726 logical node bytes**,
25,047 nodes, 1,465 source bindings and 21,838 ordinary solver residuals. Both
modes reproduce the previous archive byte for byte, so it is referenced rather
than duplicated. Warm replay is **0.27219 -> 0.26053 s**; initialization separately
**0.00168 -> 0.24030 s**. Six-case Python peak grows **21,161,086 -> 22,258,162 bytes**.
The maximum retained cache-string state is exactly **1,048,576 bytes**; these
figures exclude native SQLite/RSS and do not bound full-corpus or lifetime memory.

Full operations have **57,798 lookups / 34,971 hits / 22,827 misses/admissions /
22,571 evictions**. Keys serialize **135,220,528 bytes**, results serialize
**22,273,703 bytes**, and hits decode **29,375,582 bytes**. Total admitted string
volume is **78,031,066 bytes**. Replayed probe attempts fall **248,307 -> 113,301**,
restriction literal visits **126,081,638 -> 82,210,169**, and simplification
reconstruction visits **82,973,454 -> 51,574,914**. Propagation visits remain
**105,860,805**. These operation metrics include successful root lifts.

Cold checking uses **40,357 lookups / 17,266 hits** with an initially empty cache;
verified probes fall **181,314 -> 115,029**, and all alternatives/source/solver
certificates are still covered. The separate source-1194 profile reduces
restrictions **5,763 -> 3,399** and simplification checks **4,657 -> 2,303**, with
propagation unchanged at **2,221 calls** and now the largest named own-time cost.
Its instrumented totals 4.99171 -> 3.99936 s are not primary operation timings.
Prepared source indexes or affected-clause updates are the next cost target;
proof order, dependencies and invalidation must remain explicit.

All 410 tests pass; full and guarded pilot cold checks are byte-identical. The
62 report fingerprints and diagnostic hashes are verified, with snapshots for
superseded pilot code. No Lean source changes or formal Python refinement are
claimed. Broader coverage remains a separate discovery gap.

## Ordered occurrence propagation: per-call savings and remaining preparation

The [trace-preserving engine](ordered-propagation.md) maintains unsatisfied-clause
counts/sums, signed occurrence lists and a queue ordered by (scan round, clause
ID). With m clauses, L occurrences and v variables, each call builds at most L
index entries, visits at most L occurrences during assignments, and inserts/pops
at most m events. Assuming constant map access and word arithmetic this is
O(1+L+m log(m+1)) work and O(1+L+m+v) temporary words. A no-unit call only checks
clause lengths. This is an algorithm-level account, not a Python/Lean refinement:
adversarial integer hash collisions and large-integer arithmetic remain costs.
Neither the number of propagation calls nor SAT branching is bounded by it.

The full run replaces 105,860,805 repeated-scan literal visits with 18,691,048
clause checks, 32,071,047 index entries, 5,356,250 occurrence updates and 645,555
event pops in 187,133 calls. There are 70,889 no-unit calls. These counters describe
different work; all preparation is timed. Maximum per-call occurrences/queue size
are 1,052/33. Summed per-query peak counters are not run-wide peaks.

Full discovery falls 111.13169 -> 97.76173 s; balanced subset discovery means are
5.08503 -> 4.55072 s. Total 154.63114 -> 137.59078 s includes an 8.44% variation
in the unchanged ordinary solver. Cold replay is 63.40473 -> 62.61754 s and warm
replay 0.26392 -> 0.29322 s. Six-case Python peak grows 22,258,170 -> 22,474,570
bytes; retained traced memory also grows 216,400 bytes. Native SQLite, RSS and
full-corpus/lifetime memory remain outside that allocation measurement. Archive
bytes remain exactly 437,620,736, shared with the earlier implication experiment.

At size 1,024 the reverse-chain control improves 337.58295 -> 0.84911 ms, while
a forward chain slightly regresses 0.76777 -> 0.84533 ms. Opposing initial units
with many unrelated clauses regress 0.00248 -> 0.41982 ms: building the full index
is wasted, and peak allocation grows 1,752 -> 528,448 bytes. Colliding hashes and
long identifiers are recorded separately. This engine does not dominate the
scan reference on every input. Reusing an immutable source index across related
assumptions, or avoiding its construction for a cheap prefix conflict, remains open.

All non-propagation operation counters remain identical. Source 1194's next
named own-time bottleneck is restriction, followed by simplification checking;
full restriction/reconstruction visits remain 82,210,169 / 51,574,914. Structural
coverage remains 869/985 non-tiny, with 116 sources unresolved. Cheaper closure
computation leaves the broader category/decomposition and unrestricted complexity
gaps unchanged. Complete evidence, controls and limitations are in the
[matched study](../experiments/results/cnf-ordered-propagation/README.md).

## Immutable-source restriction indexes: locality, output cost and memory

The [indexed restriction account](indexed-restriction.md) validates an immutable
source and reuses signed occurrence postings only while that exact source is
strongly retained. Changed, mutable and separately allocated equal sources cannot
inherit the identity shortcut. There is no result/proof cache in this index.
For m clauses, L occurrences, A assignments, P retrieved postings and R affected
unsatisfied-clause literals, a hit costs O(1+A+P+R+m) under constant map/set access
and word arithmetic. A miss adds O(1+m+L) validation/preparation. Complete output
assembly is still O(m), though unchanged clause tuples share storage.

Retained units sum 1+m+L per admitted source, capped at 32,768. This is O(B) words
up to representation constants; long integers, Python objects and original graphs
prevent a byte/RSS interpretation. One incoming index can be built before eviction.
Oversized inputs pay validation and then scanning. There is no unconditional bound
on dictionary/set performance, total SAT work or lifetime archive growth.

The first full sample's discovery is 93.85938 -> 90.65563 s and cold replay
60.86819 -> 56.04772 s, but total regresses 132.36551 -> 134.44214 s. The ordinary
solver phase varies by 13.70%; the single sample does not isolate variation from
process/memory effects. The selected repeated subset improves 4.81769 -> 4.35747 s
mean total. A full reverse-order comparison is retained separately. Six-case Python
peak rises 22,474,578 -> 24,072,942 bytes; retained allocation rises 22,162,053 ->
23,447,305 bytes. SQLite stays byte-identical at 437,620,736 bytes. Allocation
excludes native SQLite/RSS and full-corpus peak; no total-memory saving is claimed.

Full operations have 275,865 helper calls, 241,198 hits, 34,599 admissions,
34,511 evictions and 68 fallbacks. Against 82,210,169 baseline restriction visits,
the candidate pays 10,412,650 validation literals, the same preparation count,
2,986,814 posting visits, 4,038,253 rebuilt literals, 28,938,355 output clause
positions and 4,473 fallback literals. These different operations cannot be treated
as a single speedup ratio. All non-restriction counters agree, including 51,574,914
independent reconstruction visits. The next named own-time cost is simplification
checking, not source restriction.

At 1,024 clauses, a 32-query sparse stream on one source improves 17.81227 ->
1.95817 ms, but equal reallocation regresses 17.91109 -> 23.80568 ms and novel
appends regress 17.75385 -> 23.29391 ms. Their indexes receive no reuse. Equal
reallocation peak grows 173,608 -> 3,239,360 bytes; even favorable sparse reuse
peaks at 817,816 bytes. Oversized fallback also regresses. These retained controls
separate warm locality from arbitrary new sources. Structural coverage remains
869/985 non-tiny and supplies no unrestricted efficient-expansion construction.

The full reverse-order control is complete. Across two samples per mode, means
are 137.36963 -> 131.36045 s total, 97.29044 -> 89.16122 s discovery and 61.16937 ->
56.70501 s cold replay (4.37%, 8.36% and 7.30% reductions). All within-mode operation
counters and archive hashes repeat. The reverse allocation repeats the roughly
1.60 MB Python peak increase. These limited synthetic samples balance order but
do not erase the initial regression, establish significance or justify universal
speed claims. Both complete reports and the order-control hashes are preserved.

## One-pass checker reconstruction: less copying without another cache

The [independent reconstruction account](single-pass-checking.md) uses a prefix
invariant to scan each clause once. It shares untouched immutable tuples and
allocates a buffer only after the first false assigned occurrence. For A assignment
entries, m clauses, V visited literals and K logical copied entries, the conditional
word time is O(1+A+m+V+K), hence O(1+A+m+L) in the worst case. The asymptotic scan
bound is unchanged. Prefix slicing/list construction and final tuple conversion
add constant multiples of copied lengths, and partial buffers discarded after
late satisfaction are charged. Big integer and dictionary costs remain explicit.

Additional storage comprises O(m) output references, copied residual literals and
at most one clause-width pending buffer. No new cross-call cache is retained.
Mutable clauses copy; untouched exact tuples share existing storage. This is not
a bound on the retained source, proof graph, existing caches or archive growth.

Full discovery falls 93.90373 -> 87.70857 s and total 137.78680 -> 130.04664 s,
but cold replay increases 57.32273 -> 57.93447 s. Six-case Python peak is essentially
unchanged at 24,072,934 -> 24,073,162 bytes. Twelve-query balanced means improve
4.60% total / 5.23% discovery; all regressions and timing spread remain. SQLite
stays byte-identical at 437,620,736 bytes. This is no total-memory reduction claim.

The candidate visits 50,055,987 literals, shares 15,777,372 clauses containing
44,643,882 literal occurrences, and copies 1,609,390 logical buffer/output entries.
The baseline charges 51,574,914 input literals without separating its generator
passes; these counters are not interchangeable CPU work units. All counters outside
reconstruction agree. There are 840 reference-scan literal charges outside the
candidate's scope. Every unit reason, conflict and pure-round check remains.

Forty-eight controls retain five one-pass regressions. Width-32, 256-clause dense
removals increase time 21.06652 -> 22.12113 ms and peak 157,160 -> 162,504 bytes;
sparse reuse reduces peak 160,936 -> 7,296 bytes. Thus local copying savings do not
imply a global or pointwise improvement. The rejected support cache grows both
pilot discovery times despite repeated clause objects; its state/preparation cost
outweighs its savings there. It remains preserved, not selected.

An independent next-gap probe identifies 35 renamable-Horn leaves among the 148
selected unresolved leaves, covering only 852 of 33,651 literals. Pair-constraint
construction costs O(m+L+sum_C binomial(|C|,2)). Positive
polarity certificates and negative auxiliary refutations are checked, but this
probe has no integrated root, persistence or acquisition bound. It supplies a
concrete next discovery target without changing the current coverage claim.

## Terminal Horn renaming: coverage has acquisition and policy costs

The [checked integration](polarity-horn.md) attempts a renaming only after earlier
reductions and bounded conditioning fail. For a normalized residual with m clauses,
L occurrences, v variables and Q=sum_C binomial(|C|,2), explicit pair discovery
uses expected O(m+L+Q+v log(v+1)) word/comparison work and O(m+L+Q+v) temporary
words. The 65,536-pair cap is checked before enumeration. Failure at the cap is
unresolved; an auxiliary contradiction excludes renamability, not original SAT.
Long integers, hashing/bit costs and the previous acquisition stack are additional.

Positive certificates hold O(v) variable identifiers; discovery's negative
certificates hold O(v) source-coordinate tuples, not the full pair formula.
Positive replay costs O(m+L+v log(v+1)), before normalization/child recognition;
negative replay costs O(m+L+p) for actual supplied path length p. Generated paths
are simple, but the checker charges arbitrary submitted path lengths. These are
per-attempt bounds, not a polynomial bound on the complete decomposition.

Model transport complements a fixed coordinate set, an involution proved in Lean.
The original source, prior failed attempts, transformed child and canonical keys
remain stored. Policy version and cap are part of each key: old archives are
preserved and new policy rows use separate identities. Reusing previous answers
in the unchanged decision solver does not mean the new discovery archive is free.
Full historical-plus-new retention differs from comparing two fresh policy
archives; small mixed-policy coexistence tests do not measure full migration size.

The [completed matched run](../experiments/results/cnf-polarity-horn/README.md)
charges 3,233 terminal attempts and 1,183,603 pair constraints: 188 recognized,
3,045 excluded, no cap stops. Positive flip certificates total 10,517 JSON bytes;
negative paths 424,918 bytes. Full pattern nodes fall 25,047 -> 22,071, fresh
SQLite 437,620,736 -> 417,370,112 bytes and six-case Python peak 24,073,154 ->
20,286,004 bytes. Retaining both snapshots uses 854,990,848 raw bytes; the full
mixed-policy migration archive has not been measured. Logical source-binding
bytes actually increase 6,032,748 -> 6,375,558 due to new policy identities.

Single-run discovery falls 84.99193 -> 80.78495 s, total 126.02211 -> 122.78419 s
and cold replay 54.89246 -> 51.32492 s. Warm replay increases 0.26877 -> 0.29138 s.
Ordinary solver time also increases 40.95733 -> 41.92352 s on its unchanged path.
These synthetic observations do not establish significance or a universal win.
The 87 remaining unresolved sources consume 57.02871 s (70.6%) of discovery.
All 106 selected remaining leaves have class exclusions; raising the pair cap
would not change those outcomes.


## Obstruction-guided conditioning: recognition evidence can increase cost

The [optional conditioning policy](obstruction-conditioning.md) adds one auxiliary
certificate at each actual OR node. After pair discovery, ranking and replay cost
O(m+L+p+c log(c+1)+v log(v+1)) conditional word/comparison work for p supplied path
edges and c distinct source clauses. It retains generated O(v)-entry certificates,
checks them without SCC rediscovery and keeps the existing four-candidate cap.
Source-support influence is only a heuristic; later propagation and other-family
recognition may favor a variable outside that support.

In the [106-leaf diagnostic](../experiments/results/cnf-obstruction-frontier/README.md),
with one extra split for both modes, closure falls 60 -> 57. Discovery rises
4.96403 -> 5.21714 s, SQLite 35,840,000 -> 37,498,880 bytes and cold replay
3.49873 -> 3.53507 s. Total stays nearly flat as the unchanged solver varies in
the opposite direction. Four-case Python peak falls 2,902,681 -> 2,823,818 bytes;
this is not full-process memory. New ranking certificates themselves total only
15,629 JSON bytes, but different choices acquire more graph state. The policy is
not promoted. Both archives remain retained, and no original-source coverage
improvement is inferred from an extra-depth frontier study.

Saved original-probe traces identify an indirect influence missed by direct
support scoring in case 4, without new propagation. Their checking and source
restriction are charged in a separate diagnostic; loading/indexing are excluded
from that diagnostic's timer. Some candidates lack those traces, and cases 17
and 50 close later despite no original damage to the saved obstruction. Reuse
of such evidence across families is a next experiment, not an achieved saving.

## 2026-11-09: cheap ranking can still increase total cost

The [probe-ranking account](probe-rank.md) adds O(p+c) table/selection work and
transient entries for p original attempts and c existing candidates; lengths of
saved unit lists are read without rescanning units. Conservatively include O(L)
for exact source-context comparison. Ordinary hashing and bounded integer costs
are assumptions; the old O(L+v log(v+1)) ranking and all recursive acquisition
remain. There is no new unit certificate or retained cache, but versioned policy
configuration repeats in keys, references and source bindings.

Reversed-order frontier means: discovery 5.19854 -> 5.44908 s, total 8.22342 ->
8.63390, cold 3.49969 -> 3.58164, SQLite 35,840,000 -> 35,979,264 bytes despite
1,540 -> 1,524 nodes. Both try 268 candidates. Fresh means are nearly unchanged;
684 nodes persist under both modes, while SQLite grows 15,417,344 -> 15,585,280
bytes. Small traced allocations exclude native SQLite/RSS/full-corpus peak.
Historical archives are retained; no storage is freed. Closure preservation
under an unchanged candidate pool is not a runtime bound or a least-cost policy.
The two new Lean lemmas capture the local logical premise, not machine costs.


## 2026-11-09: retained binary reachability and repeated-state costs

For m clauses, L literal occurrences, v variables, m2 binary clauses, q searched
roots and p emitted proof nodes, the [binary-path pass](binary-paths.md) requires
O(m+L+q(v+m2)+sum(width(C)^2)+p+|D|) word operations under ordinary hashing.
The measured policy limits q to min(64,2v); transient predecessor tables retain
O(qv) entries. Source-bound checking costs O(m+L+p+L_D), with L_D the literal
count in deleted clauses. Binary reasons stay in the retained formula, making
simultaneous deletions model-equivalent. Integer widths, normalization, all
recursive acquisitions and serialization remain charged separately. The cap is
local and proves no polynomial global acquisition bound.

Full-corpus measured discovery rises 81.47602 -> 97.00720 seconds, total with
ordinary solving 122.46371 -> 139.46329, cold replay 52.18170 -> 59.56008, and
SQLite 417,370,112 -> 475,529,216 bytes. The six-case traced Python peak rises
20,286,044 -> 22,804,740 bytes; native SQLite, RSS and whole-corpus peak are
excluded. Coverage becomes 901/985 with one lost old closure, so the policy stays
optional. A single matched run does not establish a stable speed ratio.

Sharing 21,894 proof nodes instead of 25,359 independent path nodes increases
positive JSON bytes from 230,535 to 334,245 in the documented encodings. All
proposal payload is 456,745 bytes, much smaller than the 58,159,104-byte archive
increase. The graph expands 22,071 -> 25,578 nodes. A separate source profile
still leads with reconstruction, propagation and normalization; cumulative times
overlap. The next cost target is reused preparation/checked plans and avoided
intermediate states. Historical archives remain preserved, so no storage is freed.


## 2026-11-09: graph references save archive growth, not all resident memory

The [retained-plan rule](retained-plans.md) looks up an exact normalized CNF,
remaining depth and fixed old policy. Charge full source/key construction and
comparison, SQLite lookup, hint decoding and first-use checking of every newly
loaded old dependency. The original certificate checker includes failed
alternatives. Cached checks can be reused thereafter, but wrappers still copy
source/profile/reference data. Old preparation and storage remain part of the
lifetime cost; a small reference does not bound its dependency graph's check cost.

On the common 417,370,112-byte prefix, discovery falls 98.33619 -> 81.96656 s and
combined archive 755,658,752 -> 629,276,672 bytes. Added state falls 25,578 ->
13,560 nodes and 338,288,640 -> 211,906,560 bytes. First-use reuse still checks
13,315 old nodes in a separate cache. Six-case peak Python allocation increases
20,124,942 -> 24,084,738 bytes. The 2,127 wrappers occupy 14,169,766 logical
key-plus-payload bytes, including 3,698,166 reference-key bytes. Cold/warm replay
and native-memory exclusions remain explicit in the report.

A separate 12-repeat diagnostic measures the exact full-storage aggregate that
`ResidualSolver.solve` executes after every query. Its mean is 0.0571391 seconds
for 21,838 rows / 65,665,771 payload units. At 1,497 queries, the product is about
85.54 seconds, only an estimate of magnitude rather than exact attribution.
This metadata scan adds history-size work even to a cached decision. Incremental
statistics or reporting outside the query path could remove it; initial census,
updates, invalidation and audit cost must still be charged and checked.

The fresh control has 20 old-family references but saves no pattern nodes; both
add 1,988 and close 88/96. Lookup/storage overhead therefore worsens costs there.
References are a conditional reuse mechanism, not a general efficient expansion
or a guarantee for arbitrary SAT. No old archive is deleted to obtain a saving.


## 2026-11-12: charge archive metadata independently of search

The optional [accounting implementation](residual-accounting.md) replaces the
ordinary query's complete residual census with a maintained singleton. For Q
queries and residual payload B_t / row count R_t at query t, the old bookkeeping
cost scans sum_t (B_t+R_t). The new path charges an opening scan, Q one-row reads,
indexed conflict checks and lengths of changed records, metadata updates in each
write transaction, and another full scan whenever a dirty counter is read.
Counter values take a fixed number of SQLite integer words (logarithmic bit
length in an abstract unbounded model). Five fixed triggers add no key copies.
There is no claim that conflicts, opening, source parsing, proof checks or search
are constant-time. All earlier acquisition and retained knowledge remain charged.

On the 1,497 prepared queries, accounting adds 4 KiB and initialization changes
0.00098 -> 0.12228 seconds, while query cost falls 171.12270 -> 87.88366. Warm
combined replay falls 84.36440 -> 0.61496 seconds. Six-case Python peak is
24,159,525 / 24,164,413 bytes, excluding native SQLite, RSS and full-history peak;
there is no meaningful resident-memory improvement. Ordinary SAT search counters
and every stored evidence table are identical. The 96 empty-history controls
show no clear acquisition benefit. This is avoided bookkeeping, not a change to
SAT's worst-case complexity or the remaining 83 structural misses.
