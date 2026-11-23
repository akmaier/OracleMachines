# Decide native fallback before unwinding the search stack

The preceding [binary-target study](binary-target-fallback.md) exposes a budget
boundary: one query takes eleven expansions directly, seventeen when an
eight-expansion probe stops and restarts, and eight with a different recognizer.
The last change combines better search with avoidance of the stop/restart path.
Completed proofs already persist; unfinished frames do not.

## Synchronous handoff

The new optional solver makes the existing routing decision at the native
visitor's expansion-budget guard, after canonical lookup and before charging the
next expansion. It first commits the dependency-closed prefix of completed,
checked proof nodes. Support preparation then runs while the native call stack
remains live. If the supplied support is ineligible, the solver raises the same
query's expansion allowance to its remaining total and continues that visit in
place. If the support is eligible, the native stack unwinds and the existing
checked first-false partition acquires its branches. Preparation is performed
once in either route; it receives its own accounting counters.

This is a synchronous decision inside an exclusively owned solver call. It does
not serialize Python frames, create threads or return a live continuation to a
caller. The source and solver are the ones already bound by the live frames;
there is no matching or lookup for unfinished work. The callback is removed at
the first boundary and in every exit path. Recursive acquisition during routing
is rejected. A new query or source edit starts a fresh stack. Routing and its
retained support plan temporarily overlap the live search frames in memory.

Final answers still require the unchanged native certificate checker or partition
checker, including a source model for SAT. Unfinished frames are not proofs and
never enter the answer archive. A later total-budget stop preserves completed
checked nodes from the resumed probe but discards the stack; unexpected errors
roll back pending publication using the existing cache-invalidation path. A crash
also loses unfinished frames. Cold reconstruction reuses complete proof records
and begins any incomplete query anew.

At a first pause after `b` ordinary expansions, at most `b+1` native `_visit`
frames can be active: every uncached ancestor has consumed an expansion, and a
cached visit returns without acquiring descendants. For this probe, that is at
most nine such frames. This counts native visits only, not the helper frames or
the sizes of their source-dependent locals. Routing is forbidden to acquire a
nested child. The byte census below is still required; a bounded frame count is
not a fixed memory bound.

The total expansion allowance remains 256, including the first eight. The
callback introduces no new recursive search and resumption makes no extra
expansion reservation. This does not bound recognition, canonicalization,
checking, support construction, SQLite work or RAM. In particular, retaining
frames through routing can increase peak memory. Avoiding repeated visits is not
an unrestricted SAT complexity improvement.

The resumed acquisition also preserves its live search-control flags. Restart
resets these flags and rechecks the root. Subsequent search can therefore differ;
a reduction in total expansions need not count identical repeated frames. The
comparison retains such changes and all alternative proof payloads.

## Frozen comparison

Both arms use the preceding one-target binary-frequency recognizer and shared
partition preparation. Six preceding edits become controls; six fixed-seed nearby
edits are generated before timing and have roots absent from the prior cumulative
union. Each arm receives the same exact historical prefix and supplied donor/map.
Twelve targets, two policies and two opposite serial orders give 48 attempts in
24 workers. Timing completes before profiling and cumulative checks. Full worker
time includes history restoration, publication, persistence, warm replay, cold
proof replay and diagnostic accounting; query time is reported separately.

Ten development tests cover exhaustive two-variable truth and visitor identity,
SAT/UNSAT resumption, budget stops, checked-prefix retention, partition routing,
failed preparation and commits, nested acquisition, changed sources and cold
checking. These checks establish implementation behavior within the tested
interface. No machine-checked refinement theorem or new tractable class is claimed.

## Results: the restart loss is avoidable, but most queries do not use it

All twelve targets close as UNSAT in both arms. Every paired native delta and
partition sidecar is byte-identical, across both orders. The exposed replacement
now takes **11 rather than 17** expansions, matching the preceding direct-acquisition
ablation. Mean query time falls from **31.14 to 24.69 ms (20.71%)**, with both
orders improving. Its profile reduces native visitor calls **20 -> 11**,
normalizations **56 -> 47**, propagation calls **16 -> 10** and discovery calls
**17 -> 11**. Native publications remain **12**. This is measured reuse of search
work, with the same resulting proof graph.

| Measurement | Controls: restart | Controls: resume | New edits: restart | New edits: resume |
| --- | ---: | ---: | ---: | ---: |
| Ordinary expansions | 69 | 63 | 53 | 53 |
| Query seconds | 0.18735 | 0.18252 | 0.16222 | 0.16852 |
| Complete measured worker seconds | 24.07175 | 23.96197 | 24.43936 | 24.40677 |
| New native key/payload bytes | 509,786 | 509,786 | 447,919 | 447,919 |
| Endpoint checked-object bytes | 3,432,343 | 3,428,048 | 2,956,603 | 2,956,603 |
| Compressed delta plus raw sidecars | 151,881 | 151,881 | 146,370 | 146,370 |

Control query time improves **2.58%**, with both orders better. The six new edits
have **no native fallback**: four finish within the probe and two choose a
partition. Their expansion counts remain unchanged and query time regresses
**3.89%**, with both orders worse. Complete measured worker means improve only
**0.46% / 0.13%**, with mixed paired signs in both groups. No broad or robust
complete-workflow speedup follows. General defaults remain unchanged.

The diagnostic census observes **315,998 bytes** reachable from native-frame
locals at the successful handoff, plus **10,568 bytes** of shallow frame objects.
At the new deletion's discarded continuation it observes **600,765 / 11,824
bytes** respectively. These graphs exclude the solver reference, routing plans
and interpreter/C-stack overhead, and overlap other caches. They are neither
marginal storage nor peak process memory. The graphs remain live during support
preparation; the discarded stack gives no search saving. No unfinished frame is
persisted. Saved proof storage is unchanged, and the small endpoint-object
change is not a process-memory claim.

## Next structural target

The dominant fresh query remains case 31's deletion: **81.82 ms** with restart
and **87.31 ms** with live routing, using 29 expansions in either arm. Its six
partition branches use **[1,9,1,6,1,3]**, after the eight-expansion probe. Profiles
still show 107 normalizations, 24 propagations and 29 native publications. The
handoff does not remove this search, and another routing micro-optimization is
unlikely to be the largest structural gain.

**Next, investigate joint propagation of independently forced binary consequences
inside the dominant mixed-width branch.** The preceding target census identified
multiple forced values whose implication closures need not cover each other.
Test whether a bounded, source-indexed set of paths can share graph construction
and reduce repeated restrictions or ordinary splits. Compare against the current
one-target and optional two-target policies; finding more consequences is not
itself a speedup. Charge path discovery, invalidation under conditioning, native
proof compilation, checking and retained graph size. The existing binary rules
provide the evidence; arbitrary CNFs need not have useful binary consequences.

`next-target.json` preserves the new deletion's complete prefix, profiles and
acquisition records. Its `novel` capture's acquisition at index **2** is the
nine-expansion branch: **125 variables, 57 binary and 261 ternary clauses, 897
literal occurrences**. Its seed is the bound historical prefix plus **three**
earlier native IDs from the same bound trial delta; no branch answer is included.
Its remaining budget is 247. This restores persistent availability, not warm
hint pools or the abandoned stack. The original exposed boundary remains a
separate control. Source-level recomposition, automatic donor/map discovery and
uniform unrestricted-SAT resource bounds remain open.

## Validation and resume checkpoint

Both cumulative readers validate **75,724 native records** (47 new), all prior
extension records and **258 partition records** (242 previous plus 16 new).
Every previous native payload is preserved; this comparison introduces no
alternative native payload. All **1,456 full tests** and **164 focused tests**
pass. The full suite retains the existing 44 unclosed-SQLite warnings, while the
focused suite emits none. The manuscript retains all 64 existing proof blocks.

Resume `experiments/results/cnf-live-fallback/checkpoint.json`. Its final manifest
preserves all 748 preceding source fingerprints and 11,279 preceding experiment
artifacts, plus this study's implementation, proof deltas, comparison, profiles,
allocation census and checks. The optional mechanism improves one demonstrated
acquisition route; it does not add an efficient unrestricted SAT classification.
