# Reuse canonical clause structure while reconstructing causal support

The [consequence-priority checkpoint](consequence-priority.md) exposes a query
with 142 normalizations and 6,353 restriction calls. Causal support extraction
uses 26 parent-to-child reconstructions in that query. This study replaces the
repeated transformations inside that reconstruction, preserving every support
choice and the resulting native proof bytes.

## What the census found

Replaying the exact preceding case-31 stream produces eight preimage requests
for the deletion and 26 for the replacement. The latter process **6,239 parent
clauses and 17,095 literal occurrences**. Twenty requests use single-variable
assignments; six use assignments of two to six variables. Only **one duplicate
reduced clause** appears across those 26 requests. Duplicate compression alone
therefore offers little evidence of a large gain on this source.

The repeated work is in representation changes. The old method restricts each
parent clause through a separate function call, sorts its literals, accumulates
a residual list and an origin dictionary, runs general normalization, then maps
selected normalized clauses back through the variable names and origin dictionary.
The parent was already checked and canonical before this walk began.

## Shared construction and exact invariants

The fused method restricts each clause in one pass. If no literal is removed,
it reuses the original immutable tuple. It allocates a shortened tuple only after
the first deletion and discards satisfied clauses. A dictionary retains the first
parent ID for each reduced clause, using the original `ids` iteration order,
including when it differs from numerical parent-index order.

Restriction of a checked canonical clause preserves its strict signed literal
order and cannot introduce a duplicate literal or tautology. Sort the distinct
reduced clauses once. Compact surviving variable names by increasing absolute
identifier. The resulting mapping is strictly increasing on the signed literal
alphabet: it preserves negative order, positive order and the boundary between
the two. Its componentwise application therefore preserves lexicographic clause
order, including proper prefixes. Thus the sorted raw clauses and their compact
versions have exactly the same positions. A selected child index can address the
shared raw-clause description directly; reversing the renaming and sorting that
clause again is unnecessary.

An empty reduced clause is handled separately, with the normalizer's exact
collapse to the singleton empty clause. An empty residual remains the true CNF.
For duplicates, the same first representative is returned as before. The complete
serialized child key is reconstructed and compared with the expected child; no
hash-injectivity assumption replaces it. Selected indices are checked for exact
integer type and range. Every emitted native certificate still passes the
unchanged verifier.

The specialization requires the immutable canonical parent obtained from a
checked proof and this repository's fixed order-preserving normalizer. It does
not replace external-input validation, arbitrary canonicalization schemes or
native proof checking. It makes no semantic-equivalence or general-isomorphism
claim. Causal plans remain proposals until checked materialization. No new cache
or persistent representation is introduced, so there is no new invalidation or
retention policy. The experimental override is scoped to a serial worker; it
must not overlap other threads using that class in the same interpreter.

## Cost model

With `L` parent literal occurrences, `r` distinct reduced clauses, `V` surviving
variables and maximum clause width `w`, one pass constructs the origin map under
expected dictionary costs. Sorting costs at most `O(r log(r) w + V log(V))`
comparisons/word operations; compaction and full-key serialization add work
proportional to the surviving literal/encoding length. General normalization has
similar asymptotic costs. The intended saving is fewer scans, function calls,
sorts and temporary copies by reusing known order and clause identity, not a new
polynomial-time bound.

Temporary descriptions remain `O(L+V+r)` machine words, with integer widths and
Python allocation separate. Unchanged tuples share the checked parent's storage.
There is no claim that all temporary or process peak memory decreases. Parent
proof checking, key construction, discovery, support emission, source composition
and persistence remain charged. Surviving native search can still be exponential.

## Frozen comparison

Both arms use the same consequence-priority solver, shared partition preparation
and restart policy. Six preceding new edits become controls. Three sign variants
expose the saved six-expansion source: its exact historical prefix includes only
42 earlier native IDs, with 242 expansions remaining. Cold restoration does not
restore warm hint pools. Six fixed-seed nearby edits have roots absent from the
preceding union. Fifteen targets, two policies and two opposite serial orders
give 60 attempts in 36 workers. Mode installation/removal is added to complete
worker time. Serial timing precedes profiles, tests and cumulative audits.

Supplied donors/maps and earlier acquisition remain sunk. All paired native
deltas and partition sidecars must stay byte-identical, across policies and
orders. The exposed preimage census produces no extra proof; its output matches
the preceding trial exactly. This is a local construction-cost comparison, not
an independent external benchmark or broader SAT decision coverage.

## Measured result and negative controls

The initial comparison averages two opposite worker orders. Each controls/new
row sums six queries in three separate historical streams. Every target already
closes as UNSAT, and expansion counts stay 57 on controls and 52 on new edits.

| Measurement | Priority | Fused | Change |
|---|---:|---:|---:|
| Controls query seconds | 0.193101 | 0.182417 | -5.53% |
| New edits query seconds | 0.176619 | 0.166637 | -5.65% |
| Controls complete-worker seconds | 24.178436 | 24.243947 | +0.27% |
| New edits complete-worker seconds | 24.551525 | 24.512422 | -0.16% |
| Controls new native payload bytes | 628,044 | 628,044 | unchanged |
| New edits new native payload bytes | 483,609 | 483,609 | unchanged |
| Controls checked-object endpoint bytes, summed | 3,702,425 | 3,702,425 | unchanged |
| New edits checked-object endpoint bytes, summed | 3,122,128 | 3,122,128 | unchanged |

Complete-worker time includes historical reconstruction/audit, persistence and
measurement work, with mode setup/removal added. The six controls regress in both
complete-worker orders; new-edit order signs differ. This does not demonstrate an
end-to-end or cold-replay speedup. Checked-object sums are not simultaneous or
peak RAM. Compressed proof deltas, database sizes and partition bytes also match.

The three isolated branches never call the changed preimage routine. Nevertheless,
the original's initial mean appears 10.10% faster. That is a negative control for
timing attribution, not a gain from this algorithm. Before more timing, we freeze
`repeat-protocol.json`: six balanced paired repeats of controls, new edits and
that original branch, restoring each exact historical prefix. This adds 36
aggregate samples, 84 case streams and 156 query attempts. It repeats exposed
inputs in one interpreter and does not repeat full historical cold audits.

All six control pairs improve; five of six new-edit pairs improve, with the
remaining pair **5.15 ms slower**. Mean query time falls 6.35% and 4.52%; including
scoped mode setup/removal gives **6.32% and 4.49%**. The zero-hit branch now appears
12.49% slower, driven by one 15.60 ms pair; other pair signs vary. Keep every
sample and avoid claiming a branch speedup, statistical significance, external
representativeness or a robust complete-worker improvement.

The exposed replacement's profile changes from **142 to 116 normalizations** and
**6,353 to 114 restriction calls**. Its 26 old preimage calls are replaced by 26
fused calls. Instrumented cumulative times overlap and are not standalone
comparative timings. Across the new edits, negative discovery reports 7,469
untouched clauses and 20,842 reused literal slots, 244 shortened clauses, 427
satisfied clauses and three duplicates. Recognition and renaming still cost work;
normalization-counter reduction alone is not a total-work bound.

A separate traced-allocation probe replays the 34 captured preimages, with inputs
already allocated, in both policy orders. Priority/fused peaks are **141,016 /
48,093 bytes** in the first order and **71,728 / 43,837 bytes** in reverse order.
The probe includes counters and assertion temporaries, excludes the existing
solver graph, SQLite, input objects and untraced allocations, and depends on
allocator history. It supports fewer temporary allocations in this kernel only.
No persistent-memory or process-peak reduction follows.

## Next target

Keep fusion as a serial optional construction specialization. The largest new
query is now case 31's deletion, 89.04 ms in the initial fused mean. Its profile
still has 116 normalizations, 103 restrictions and 51 verification calls. Its
branch expansions are `[1,9,1,6,1,3]` after the eight-expansion probe. In
`next-target.json`, the `novel` observation at query position 0, acquisition index
2, binds a **125-variable source with 259 ternary and 56 binary clauses**, 889
literal occurrences, budget 247 and exactly three earlier native IDs. The target
was absent. Restore that prefix plus those IDs from its bound trial delta; replay
the preceding probe and branch to recover warm pools. Never seed from the final
union.

Census the exact conditioned-source and path-reason descriptions produced and
consumed by `force_all` and `excluded_context`. Prefix preparation, backwards
parent construction and excluded-branch compilation may share immutable work.
Determine the source/assignment/renaming bindings and consumer lifetime before
trying a bounded handoff. The native verifier must independently check every
edge. Broad cofactor and normalization memos already regressed and remain
preserved. Useful whole-source discovery, automatic donors/maps, source-level
composition, persistent growth and unrestricted interaction bounds remain open.

## Validation and preserved evidence

Both native readers replay all **76,102 native records**, the 71 affine negatives,
34 binary discovery records and 42/53/22 equivalence records. All **322 partition
records** (306 earlier plus 16 current observations) are checked. Every prior
payload is retained; this run adds 99 native records from the new streams. Prior
138 manifests bind 12,026 earlier artifacts. The final source ledger has 780
entries. Repeated timings and the exposed census add no distinct proof payload.

All **1,488 full tests and 196 focused tests** pass, including 4,608 small
clause-set/assignment comparisons, 192 random subset/selection comparisons,
invalid edges/indices, empty residuals, reordered duplicate representatives,
scoped cleanup, budget limits and identical plan/proof emission. The full suite
reports 43 unclosed-SQLite warnings; the focused suite reports none. Warning sites
can be collection rather than allocation sites. The 243-page manuscript builds
without warnings, and all 64 previous proof environments remain byte-identical.
The order invariant is argued above and tested; no new Lean refinement theorem
is claimed.

The first audit completed replay but failed while writing its report because a
local extractor variable shadowed the new-record counter. Its failure log is
retained. After separating those names, the complete audit was rerun successfully;
no frozen algorithm, cases or timings changed. `checks.json` and `manifest.json`
seal the evidence and bindings for continuation.
