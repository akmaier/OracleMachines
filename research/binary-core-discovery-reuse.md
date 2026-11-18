# Reuse exact binary-core discovery across wide-clause edits

The optional `CachedBinaryEquivalenceSolver` factors discovery by the ordered
binary subset of a canonical source. Its exact key stores those clauses in their
current signed variable coordinates. Wide clauses do not enter this key. The
cache stores the original deterministic recognizer's selected two-tree block,
or its null discovery outcome, with binary-local clause indices. Before each
substitution, indices are translated into the current full source and the
unchanged checker validates the trees against its actual binary clauses. All
wide clauses still participate in substitution, solving and model validation.
A null discovery outcome is never a SAT or UNSAT answer.

This is an exact reuse pattern shared by mixed CNFs across category labels.
Adding, deleting or changing only wide clauses preserves the entry when canonical
variable coordinates stay fixed. Any binary-clause or coordinate change produces
a different key; it cannot inherit the old trees. This implementation does not
search for isomorphic cores, use hashes as identities, or update SCCs incrementally
after binary changes. Cache entries are immutable internally; transported evidence
is copied so a caller cannot modify the retained local trees.

## Why the reused discovery result is the same

The existing recognizer inspects wide clauses only for the mixed-source eligibility
gate. Its graph, SCC traversal order, block selection and trees depend solely on
the binary clauses and their relative order. Extracting that ordered subset
preserves traversal order; local indices change only edge references. The adapter
calls the unchanged recognizer on the binary subset plus a fixed wide gate clause
whose literals are never read by discovery. That clause is never solved, inserted
into the source, or used as certificate evidence. Translating the output references
back therefore gives the same evidence as full-source discovery. Units, empty
clauses, pure binary and pure wide sources retain their original eligibility rules.

Persistent entries use a separate `cnf_binary_core_discovery_v1` table. On first
use after restart, the reader parses the exact canonical key, recomputes the
complete discovery outcome, and compares its exact encoding before caching it in
memory. This checks null outcomes and the original block-selection policy as well
as positive trees. Subsequent calls in that process reuse the validated outcome.
SAT certificates remain in the existing native/v1/v2 tables and do not depend on
this advisory discovery table. Existing readers continue to work without it.

The optional solver's inherited `reuse` flag controls answer-certificate reuse;
its discovery cache is a separate feature of this solver class. The
`persistent_cache=False` mode retains discovery only for the live session. Both
modes preserve answer certificates on disk when a database path is supplied.
Neither mode changes recursive acquisition or the prepared production pipeline.

## Matched acquisition and replay

Six serial workers compare the previous compact solver, memory-only discovery
reuse and persistent discovery reuse in opposite orders on the same 68-input
catalog. Each starts empty and retains results within its stream. These are
replayed inputs, not new structural coverage. All arms return **21 SAT / 47 UNSAT**
and produce byte-identical native and compact-extension payloads. All 136 paired
chronological acquisitions match, including models, dependencies, 358 native
expansions, 51,326 propagation visits, 174 checked tree edges and 10,859
substitution/verification literal visits. The single-block policy still selects
45 blocks; `equiv_blocks_found=23` in cached runs counts newly discovered blocks,
not fewer applied reductions.

| Per worker, except mean times | Compact control | Memory cache | Persistent cache |
|---|---:|---:|---:|
| Eligible mixed inputs | 56 | 56 | 56 |
| Fresh binary graph constructions | 56 | 34 | 34 |
| Discovery cache hits | 0 | 22 | 22 |
| Graph edges constructed during acquisition | 4,276 | 2,372 | 2,372 |
| SCC edge visits during acquisition | 8,552 | 4,744 | 4,744 |
| Tree-search edge visits | 547 | 275 | 275 |
| Native / extension certificates | 398 / 42 | 398 / 42 | 398 / 42 |
| Certificate payload bytes | 492,731 | 492,731 | 492,731 |
| Retained discovery entries | 0 | 34 | 34 |
| Discovery key + value bytes | 0 | 11,906 | 11,906 |
| Discovery Python-object bytes | 0 | 25,887 | 25,887 |
| SQLite bytes | 892,928 | 892,928 | 929,792 |
| Compressed bytes | 85,164 | 85,164 | 88,782 |
| Query seconds, including audit metadata | 0.33415 | 0.32928 | 0.33486 |
| Complete-worker seconds | 0.51474 | 0.50078 | 0.51302 |
| Cold replay seconds | 0.08752 | 0.07863 | 0.08285 |

Acquisition graph/SCC work falls **44.53%**. Keying scans 4,276 binary literal
units and serializes 18,593 key bytes across eligible queries; source width
inspection still visits 3,810 clauses, and the recognizer's local scan adds 1,220
checks on misses. Ninety evidence edges are transported. Of 34 retained outcomes,
23 contain blocks and eleven contain null outcomes. Full keys use 10,385 bytes,
values 1,521. `sys.getsizeof` recursively measures the retained cache dictionary
with shared objects counted once; 25,887 bytes excludes solver state, temporary
graphs, allocator fragmentation and SQLite buffers. Mean process RSS is about
55.1 MB in all three arms and does not establish a memory-scaling improvement.

Persistence adds **36,864 SQLite / 3,618 compressed bytes** in the trial. More
significantly, full cold cache validation repeats another 2,372 constructed edges
and 4,744 SCC visits. Acquisition plus that validation therefore costs **4,744
constructed edges / 9,488 SCC visits**, **10.94% above** the compact control's
4,276 / 8,552 discovery work. Persistence currently skips no first-use SCC
computation after restart. It preserves a checkable outcome, but provides no
extra computational saving over reconstructing the memory cache in that process.

Timing is not a stable total-cost win. Memory-cache complete-worker paired deltas
are **-0.03855 / +0.01063 seconds**; query deltas also have opposite signs.
Persistent complete time is lower in both orders by only **0.00091 / 0.00254
seconds**, while query deltas are **+0.00860 / -0.00717 seconds**. Control cold
replay varies by about 17 ms even though memory mode has exactly the same stored
certificates, so the cold-time mean cannot be credited to discovery reuse. The
mean complete differences (-2.71% memory / -0.33% persistent) remain finite noisy
observations. Both APIs stay optional; use memory mode to investigate live-session
reuse, and retain the persistent result as its fully charged comparison.

Workers include setup, keying, discovery, index transport, checking, acquisition,
metadata scans, publication, warm source answers, cold certificate/cache checking,
sidecar serialization and compression. Imports/source audits, truth/chronology/
history checks and final report writing are outside timing. Per-query metadata
serializes retained cache entries too; `attribution.json` separately records public
`solve` time. Sidecars grow about 18.7 KB for memory / 24.6 KB for persistent mode.
No study tests/builds/audits overlapped the six timed workers.

## Bounds and next targets

Let `B_i` be an eligible query's exact binary core, `K_i` its encoded key length,
`m_i` its source-clause count, and `E_i` the selected evidence length. Within one
process, graph discovery is performed once per distinct `B_i`, rather than once
per query. The comparison is therefore the sum of those distinct discovery costs
plus every query's extraction/keying, lookup, transport, full substitution and
verification. Extraction/keying cannot be treated as free. Under ordinary
expected dictionary costs, the current recognizer uses `O(b + v log v)` work on
`b` binary clauses and `v` graph literals, including member sorting. Integer bit
costs, input canonicalization and SQLite indexing require additional accounting.
This is not a worst-case constant-time dictionary or a machine-level cost theorem.

The cache retains the sum of all distinct encoded keys and evidence; it has no
capacity or eviction bound. Every novel core adds state. Persisted exact-policy
validation pays the distinct discovery costs again after restart. Eliminating that
recomputation would require a different certificate for the recognizer outcome,
or explicitly weakening the contract to source-checked proposals whose maximality
and negative discovery claims are not trusted. It must not silently turn a cached
miss into an exclusion theorem.

**Next highest-value coverage target: substitute multiple disjoint blocks.** The
prior census identifies twelve inputs where a second block is left unused.
Acquisition still spends 51,326 propagation visits and 358 expansions; this cache
changes neither. Test all-block substitution with exact full-source recomposition,
model lifting and native negative dependencies, then price the resulting child
acquisition and evidence. The diagnostic two-variable/eight-literal reduction is
not yet a measured solving saving.

**Next reuse target:** share graph construction among existing recognizers after
profiling. The unchanged child pipeline still constructs 8,344 subset-implication
edges and 6,772 cover edges, performs 171 subset SCC calls, and scans 15,650 literals
for targeted ranking. These counters identify work, not additive wall-time shares.
The new exact-core cache is top-level only. Renamed cores, binary edits, recursive
reuse, larger novel mixtures and arbitrary-CNF interaction remain open. There is
no new Lean theorem or unrestricted-SAT resource bound.

## Preserved checkpoint and checks

Resume `experiments/results/cnf-binary-core-cache/checkpoint.json`. The union adds
34 discovery entries and 68 explicit decisions while preserving byte-for-byte
**28,691 native payloads, 26 affine records, 42 v1 and 42 v2 equivalence records**.
No certificate is inserted or replaced. Four alternative native roots remain in
trial archives. Union growth is **36,864 SQLite / 2,681 compressed bytes**. All
5,650 old composed records and 204 earlier pilot decisions remain readable.

Eight new tests cover 4,096 binary-core combinations with both wide-clause choices,
source-index transport, signed edits, changed coordinates, cached null results,
mutable-output isolation, cold validation, corrupt keys/outcomes, matching full
solver payloads/truth and disabled discovery. The validation checks 408 chronological
queries, 68 exhaustive truth tables, both cache outcomes, all old/new authorities
and complete historical replay. All 591 prior sources, 7,683 artifacts and 110
manifests remain unchanged.

All **1,236 full / 67 focused tests** pass, with 44 pre-existing SQLite warnings
in the full suite and none in the focused suite. The **223-page manuscript**
builds cleanly and all **64 previous proof blocks** are unchanged. Final source
ledger: **596**. New manifest: **39 artifacts**. Next preservation audit:
**7,722 artifacts / 111 manifests**.
