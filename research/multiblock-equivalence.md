# Substitute disjoint equivalence blocks together

The optional `MultiEquivalenceSolver` discovers every nontrivial, consistent
binary SCC block in one graph pass. It selects one member of each complementary
SCC pair, retaining the previous largest-block ordering. Two source-indexed
spanning trees certify every selected block. The checker rejects overlapping
variable supports, unions the signed maps and substitutes every source clause
once. All remaining interactions stay in the resulting CNF.

This implements the twelve second-block opportunities identified in the previous
pilot. It is a broader exact reduction, but **more reduction is not automatically
cheaper acquisition**: on the same 68 inputs it reduces propagation only 0.52%
and increases stored native certificates by ten. The policy remains optional.

## Exact recomposition and format compatibility

For each block, the forward tree proves that its representative implies every
signed member. The reverse tree proves the converse. A satisfying source
assignment therefore gives each signed member the representative's value.
Distinct blocks have disjoint absolute-variable supports. Their simultaneous
substitution is consistent, and no representative is eliminated by another block.
Every source model satisfies the substituted formula. Conversely, a model of the
substituted formula extends to a source model by assigning each eliminated
variable its signed representative value. Every source clause is accounted for,
including wide clauses shared between blocks. No independence assumption is made
about the remaining representatives or clauses.

The checker validates tree shape, each exact source-clause reference, matching
forward/reverse supports, signed-variable uniqueness and cross-block disjointness.
It performs one full substitution for the combined map, then requires strict
support reduction. SAT acquisition lifts and checks a full-source witness. UNSAT
publication requires an independently checked ordinary native negative quotient.
That exact quotient is reconstructed from the canonical source key and the trees.
An extension root is not an ordinary native root; recursive native search is
unchanged.

Single-block negatives retain the existing compact v2 format. Only sources with
multiple blocks need `binary-equivalence-negative-v3` in the new table. The new
reader also supports v1/v2, and old readers remain valid for their original tables.
Old records are never rewritten or deleted. The v3 reader rejects malformed
headers, overlapping or corrupt trees, incorrect publication source/child and
missing or positive native dependencies. There is no new Lean theorem or formal
refinement of the Python implementation.

The optional exact-core memory cache now stores the list of blocks in binary-local
coordinates and translates each tree to current source indices. Binary or signed
coordinate changes miss its exact key; wide-clause edits can reuse it. Unlike the
previous persistent comparison, this cache is session-local. Its proof results
still persist. Cold proof replay validates source trees and native dependencies,
without reconstructing discovery maximality. Completeness of block discovery is
not a requirement for a certificate's soundness.

## Matched study

Six serial workers compare the previous memory-cached single-block solver, an
uncached all-block solver and a memory-cached all-block solver in opposite orders.
Every worker starts empty on the same 68-source catalog. These are replayed inputs,
not fresh problem coverage. All return **21 SAT / 47 UNSAT**. All-block arms have
identical native and extension payloads, models and chronological acquisitions;
the cache changes only discovery. Both use 31 v2 and eleven v3 negative records.
Twelve inputs receive two blocks, including one positive lift and eleven negative
publications. All other selected sources use one block.

| Per worker, except mean times | Single, cached | All blocks | All, cached |
|---|---:|---:|---:|
| Applied blocks / variables merged | 45 | 57 | 57 |
| Native expansions | 358 | 366 | 366 |
| Propagation literal visits | 51,326 | 51,059 | 51,059 |
| Native certificates | 398 | 408 | 408 |
| Negative extension certificates | 42 | 42 | 42 |
| Native payload bytes | 465,733 | 468,450 | 468,450 |
| Extension payload bytes | 26,998 | 27,764 | 27,764 |
| Combined payload bytes | 492,731 | 496,214 | 496,214 |
| SQLite bytes | 892,928 | 897,024 | 897,024 |
| Compressed bytes | 85,164 | 87,278 | 87,278 |
| Retained discovery entries | 34 | 0 | 34 |
| Discovery key/value bytes | 11,906 | 0 | 12,149 |
| Discovery Python-object bytes | 25,887 | 64 | 30,967 |
| Query seconds, including metadata | 0.32463 | 0.31112 | 0.31241 |
| Complete-worker seconds | 0.50055 | 0.48287 | 0.48328 |
| Cold replay seconds | 0.07989 | 0.07702 | 0.07535 |

The twelve additional variable merges remove two variables per affected source
instead of one. Nevertheless, native expansions increase by eight and native
certificates by ten. Combined payload grows **3,483 bytes (0.71%)**, including
2,717 native and 766 extension bytes. SQLite grows 4,096 bytes and gzip 2,114 bytes.
The all-block memory cache adds 5,080 Python-object bytes relative to single-block
reuse; this measurement excludes temporary graphs, allocator and SQLite overhead.
Mean process RSS is about 55.1--55.3 MB, with no demonstrated memory-scaling gain.

Full-source substitution/verification still scans 10,859 literals: the implementation
does not repeat the full scan separately for each block. Acquisition/publication
checks **220 tree edges** (158 in the new checker plus 62 through reused v2
publication) versus 174 before. With the cache, SCC work remains 4,744 edge visits,
but tree-search visits rise 275 -> 341 and transported evidence edges 90 -> 114.
Without the cache, SCC work is 8,552 and tree-search visits 679. Twenty-two exact
core hits are retained. Thus added block selection and certificate work are charged.

Query time falls in both orders: all-block cached deltas are **-0.02086 / -0.00356
seconds**. Complete-worker deltas are **-0.03893 / +0.00438 seconds**; cold replay
also has mixed signs. The corresponding complete-time mean is 3.45% lower, but
two orders do not establish a stable total-time advantage. The uncached all-block
arm also has mixed complete-time deltas (-0.03554 / +0.00017 seconds). Discovery
cache savings do not imply better wall time on this small corpus. Keep the
storage regression and timing variation alongside the propagation reduction.

Worker time includes setup, extraction/keying, discovery, transport, acquisition,
verification, metadata scans, publication, warm source replay, cold proof replay,
sidecars and compression. Imports/source audits, truth/chronology/history audits
and final reports are outside timing. Per-query metadata includes serialized
retained caches; public `solve` time is separately recorded. No study tests,
builds or history audits overlapped the timed workers.

## The largest actionable gap: choose a known quotient before fresh solving

`attribution.json` records both the previous one-block quotient and the complete
quotient at each of the twelve multi-block query prefixes, separately for the
actual single/all-block streams. **Queries 7 and 34** already have their one-block
quotient in both streams, but their all-block quotient is new. The all-block policy
ignores those exact known alternatives. In those queries native additions rise
**0 -> 5** and **1 -> 4**, and propagation rises **0 -> 150** and **0 -> 60**.
Both are graph-colouring descendants of old case 51. Final-archive membership is
not used to make this diagnosis; the saved lists include only preceding queries.

Two other queries (1 and 16, descendants of old case 31) each add one more native
certificate after earlier changes to the acquired history, despite having only
one block themselves. That accounts for all ten extra native certificates. A
policy choice affects later reuse, as well as the immediately smaller child.
The current study does not implement an alternative-selection policy, so these
observed opportunities must not be reported as recovered savings.

**Next priority:** before acquiring a new complete quotient, compare its exact
key with the original one-block quotient's exact key and check whether either
native dependency is already available. Preserve a known valid quotient when it
avoids fresh solving, using the corresponding source-checked block subset and
correct model/proof recomposition. Charge construction of the second quotient,
canonicalization, lookup, cold validation and any added retained state. Test
positive and negative known targets, misses, edited sources and chronological
held-out streams. The first experiment needs only two alternatives, not all
exponentially many block subsets; it must not claim a globally minimum-cost
quotient or speculate about future cache hits.

## Limits and persistence

If blocks have sizes `k_1,...,k_q`, their evidence has exactly
`2 * sum(k_i - 1)` implication edges. With disjoint supports, their total support
is at most the source variable count. The discovery graph/SCC pass is shared;
tree searches across distinct chosen SCCs scan each selected adjacency at most
once per direction. Member/block sorting, exact keying, checking and full-source
substitution remain charged. Under ordinary expected dictionary costs discovery
has the existing `O(b + v log v)` bound, for `b` binary clauses and `v` graph
literals, plus source inspection. Integer bit costs, canonicalization and database
operations need separate accounting. The final child can still be arbitrary SAT.
One pass need not expose equivalences that appear only after wide clauses shrink.

The cache remains unbounded in distinct exact cores. No automatic cold maximality
certificate, renamed-core lookup, incremental binary edit repair, recursive
all-block integration or prepared production admission is supplied. This widens
an exact transformation, not a uniformly efficient partition of all CNFs.

Resume `experiments/results/cnf-multiblock-equivalence/checkpoint.json`. It preserves
all **28,691 native / 26 affine / 42 v1 / 42 v2 / 34 discovery-cache records** and
adds **45 native certificates and eleven v3 records**, giving 28,736 native keys.
No old payload is replaced, and no new alternative payload collision occurs in
this pilot. Prior alternatives remain in their older trial archives. Union growth
is **81,920 SQLite / 6,918 compressed bytes**, retaining both policies' work.
All 5,650 old composed records and 272 old pilot decisions remain readable, with
68 explicit new decisions added.

Nine new tests cover all 4,096 three-variable binary cores against the old first
block; 1,020 two-block sign/wide-clause mixtures and all 32 assignments each;
2/4/8/16-block controls; corrupt and overlapping evidence;
old/new cold readers, memory index transport, unchanged single-block bytes,
generated truths, warm reuse and disabled discovery. Validation includes 408
chronological query/dependency audits, 68 exhaustive source truths, both quotient
truths for twelve sources and full historical replay. All 596 prior executable
sources, 7,722 artifacts and 111 manifests remain unchanged.

The **224-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,245 full / 76 focused tests** pass (44 pre-existing SQLite
warnings in the full suite, none in focused tests). Final executable source
ledger: **601**. New manifest: **39 artifacts**. Next preservation audit:
**7,761 artifacts / 112 manifests**.
