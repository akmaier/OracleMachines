# Reuse checked canonical form during complete cold verification

Case 19 now has a complete structural coverage proof, raising the retained
original-input coverage from **11/24 to 12/24**. Applying the existing canonical
form check inside the complete cold auditor reduces measured audit time
**6.75146 -> 6.46583 seconds (4.23%)**. Whole-stream time falls
**8.20199 -> 7.88948 seconds (3.81%)**. This is a modest representation-work
improvement. All acquisitions, proofs and snapshot bytes match; no SAT decision
procedure or acquisition policy changes.

## Why this candidate

The previous grouped-checkpoint experiment identified the final full audit as
59.6% of its three-query stream. A diagnostic `cProfile` run on that frozen
1,946-pattern / 194-pair parent reports 7,694 normalizations taking 4.237 seconds
cumulatively. The whole instrumented audit reports 19.351 seconds. These are
profiling costs, with substantial instrumentation overhead, not comparable raw
timings. Nested cumulative times overlap and must not be added.

Single-pass source reconstruction is already active. Earlier
[checker-index experiments](indexed-check.md) added allocation and were slower;
larger caches did not remove that regression. We retain those counterexamples.
The [checked canonical-source fast path](checked-canonical-sources.md), however,
was not installed in the current complete auditor's verifier views. This study
tests that existing fast path at this boundary, without adding another index.

## Exact condition and trust boundary

The optional `CanonicalAuditInventory` installs `canonical_key` in every current
and prepared verifier view. For each actual CNF, it checks strict literal and
clause ordering, absence of repeated or opposite literals, the empty-clause
convention and dense variable names. An accepted source already has the original
normalizer's output; its variable mapping is the identity. Other inputs use the
unchanged normalizer. Reordering, gaps, duplicates and mutable-input edits remain
subject to checking. This recognizes this normal form, not arbitrary variable
isomorphism or logical equivalence.

The complete auditor still checks every stored pattern, every split certificate,
all 24 original bindings and the full positive coverage proof. It reads an
independent cold inventory, forbids acquisition, enables SQLite query-only mode
and checks unchanged database bytes. It trusts no parent-validity attestation,
serialized Boolean, digest in place of semantic checking, or warm verifier.
The per-query positive proof is also independently checked on the exact snapshot.
There is no additional delay in unrelated-corruption detection in this study.

For an already canonical source, the precheck takes O(L+m) word operations under
the usual expected constant-time set model, for L literal occurrences and m
clauses. Adjacent clause comparisons inspect at most their available literal
slots. It builds a canonical tuple and variable sets, using O(L+m) auxiliary
space in this Python implementation. Fallback inputs pay the precheck plus the
old normalization cost. Integer bit costs, key serialization and all semantic
checking remain chargeable. This replaces repeated sorting/renaming on accepted
sources; it does not change the full audit's dependence on retained history.

## Matched costs

The [frozen protocol](../experiments/results/cnf-canonical-audit/protocol.json)
starts both modes from the same complete parent. Both run the unchanged scoped
case-19 continuation, with at most four batches of 128 admissions and sixteen
pair attempts. The input is an existing development case, not a new holdout.
Four paired fresh-process repetitions alternate execution order. No profiler,
validator or test suite runs concurrently with the timed streams.

Both modes finish in one batch, adding **35 patterns / five pairs / ten source
assumptions / 135 probes**, with 35 distinct admissions. Means across the four
runs are:

| Resource | Original normalization | Checked canonical form |
| --- | ---: | ---: |
| Restoration and setup, seconds | 0.14773 | 0.14852 |
| Local expansion, seconds | 0.23742 | 0.23289 |
| Bookkeeping, seconds | 0.11413 | 0.10967 |
| Cold query-proof check, seconds | 0.14043 | 0.14257 |
| Complete cold audit, seconds | 6.75146 | 6.46583 |
| Compression, seconds | 0.71133 | 0.71048 |
| Whole stream, seconds | 8.20199 | 7.88948 |
| Mean peak process RSS, bytes | 386,387,968 | 386,977,792 |
| SQLite bytes | 37,580,800 | 37,580,800 |
| Compressed snapshot bytes | 1,884,969 | 1,884,969 |

The whole-stream clock also includes report construction and other bookkeeping
outside the separately timed phases. Interpreter imports and the final summary
write are excluded; RSS includes imports and all phases. The parent acquisition
cost remains recorded in earlier experiments. Retrospective validation is
separate from these operational timings.

The candidate is faster in all four pairs, but its last pair saves only 0.08124
seconds whole-stream time. Four measurements on one history do not establish a
universal speedup. Mean peak RSS increases **589,824 bytes (0.153%)**, so this is
not a memory saving. Corresponding SQLite and gzip hashes match in every pair.

The candidate checks 6,008 canonicalization calls: **3,316** reuse canonical
order and **2,692** fall back. It avoids old normalization on **1,453,611 literal
slots**, while adding **2,207,436 precheck visits**. Old-normalizer visits fall
3,682,644 -> 2,229,033. The sum of counted visits therefore increases; the saving
comes from avoiding sorting, renaming and associated allocation on accepted
inputs, not from inspecting fewer literals. Both visits and fallback costs must
remain in the accounting.

## What the new proof reuses

The original case-19 input has **60 variables / 276 clauses / 828 literals**.
Its selected preprocessed residual had 58 variables and maximum width four.
The [checked explanation](../experiments/results/cnf-canonical-audit/explanation.json)
contains **42 distinct steps**: six conditional nodes, 35 unary reductions and
one contradiction terminal. The reductions comprise 28 probe steps, four
binary-path steps and three eliminations. Seven pattern steps and one split
predate this continuation; 35 pattern steps and five splits are new. No component
decomposition is used. Maximum conditional depth is three in changing local
coordinates, not a fixed backdoor-size or minimal-depth claim.

The seven conditional leaf occurrences all share contradiction. This reduces
48 unfolded occurrences to 42 stored proof steps; no larger nonterminal is
shared within the proof. Zero explicit `reused_pairs` acquisitions does not mean
zero reuse: the proof follows one already stored split without reacquiring it.
The proof is structural coverage evidence, not a new SAT/UNSAT output API.

Independent retrospective validation checks all eight archives with the frozen
full auditor, then rechecks each query proof and the full reachable split catalog.
Immutable prefixes and every corresponding SQLite/gzip hash agree. Parent and
union reconstruction also pass. The validator takes **119.72 seconds**, outside
the timed comparison and partly concurrent with the test suite. All **360 tests**
pass, including new forged-record, foreign-original, noncanonical-node and
mutable-source controls. Existing database ResourceWarnings remain in the raw
suite log. All earlier sources, artifacts and 64 proof blocks are unchanged.

[The new union](../experiments/results/cnf-canonical-audit/checkpoint.json)
contains **1,981 patterns / 199 pairs / 17 inherited missing children**, with a
**706-step proof for twelve originals**. Twelve remain unknown. Its own gzip
serialization is **1,883,472 bytes**, with **37,580,800 SQLite bytes**; growth
from the parent is 49,145 and 696,320 bytes. The eight research trial snapshots
also remain preserved; they are validation artifacts, not evidence of reduced
solver storage.

The [next bound target](../experiments/results/cnf-canonical-audit/next-discovery.json)
is case **6**, random 3-CNF, with a **36-variable / 148-clause / 444-literal /
width-three** residual. Its eight saved children all exist. The false child of
pivot **13** is already covered; its true sibling and the other six children
are not. Reuse that covered branch while investigating the remaining interaction.
Historical enumeration cost ranks this target and is not a new timing forecast.

## Remaining limits

The complete audit still takes **82.0%** of the candidate stream; compression
takes about **9.0%**, while fresh local expansion takes about **3.0%**. This
supports further audit work, but the small normalization gain does not justify
repeating the failed reconstruction-cache approach. Checked parent reuse would
need an explicit trust model and invalidation boundary; it is not implemented
here. The candidate remains optional, with public inference defaults unchanged.

Broader structural discovery and reusable nonterminal components remain the
primary objective. Coverage of a finite corpus, a short proof on one residual,
and cheaper verification do not bound conditional depth, total acquisition or
storage for arbitrary CNF. No unrestricted-SAT efficiency or P-versus-NP result
follows.
