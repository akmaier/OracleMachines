# Reconstruct redundant formulas in equivalence certificates

The new optional `binary-equivalence-negative-v2` format stores only its format,
negative answer and two-tree equivalence evidence. The exact full source key
already contains the canonical CNF. The reader decodes that key, checks its exact
prefix and canonical serialization, checks the equivalence trees against those
source clauses, reconstructs the substituted quotient and requires its checked
native UNSAT certificate. Neither source identity nor child identity is guessed
or supplied by an unchecked hash. The full source key remains stored and charged.

The same reconstruction also runs before publication. The producer's supplied
source and child must equal the independently derived ones. Malformed or
noncanonical keys, extra fields, unsupported tree edges and missing/positive
native children fail before publication. Cached v2 records remain compact;
reconstructed source/child fields are not retained in a second hydrated copy.

Version two uses a separate table. The new reader also accepts the old table;
old records are never implicitly rewritten or deleted. When both versions exist,
the new lookup prefers v2 while the original v1 reader continues to validate v1.
Native recursive search and affine authorities remain unchanged. This extends
the top-level [equivalence pilot](binary-equivalence-acquisition.md), not the
prepared production pipeline or every recursive expansion.

## Matched representation comparison

Six serial workers compare the native targeted solver, v1 quotient solver and
compact quotient solver in opposite orders on the **same 68 inputs** as the
preceding pilot. Every worker starts empty and retains results within its stream.
The original catalog contains eleven saved residuals, 33 edits and 24 generated
controls; these are now replayed inputs, not newly unfamiliar coverage. Metadata
never enters search. Source-fingerprint audits and imports precede timing; setup,
discovery, checking, acquisition, persistence, metadata scans, warm answers, cold
replay, sidecars and compression are included. No study tests/builds/audits ran
concurrently with the timed workers.

All modes still return **21 SAT / 47 UNSAT**. Between v1 and v2, all 68 chronological
native acquisitions, full native payloads, source models, discovery and search
counters match. All 42 reconstructed source CNFs, child keys and tree certificates
match the explicit v1 fields. The optimization changes representation and replay;
it adds no new mathematical or empirical source coverage.

| Per worker, except mean times/RSS | Native control | Quotient v1 | Compact v2 |
|---|---:|---:|---:|
| Native certificates | 420 | 398 | 398 |
| Equivalence certificates | 0 | 42 | 42 |
| Combined certificates | 420 | 440 | 440 |
| Native payload bytes | 525,136 | 465,733 | 465,733 |
| Equivalence bytes, including keys | 0 | 68,878 | 26,998 |
| Combined payload bytes | 525,136 | 534,611 | 492,731 |
| Propagation visits | 61,517 | 51,326 | 51,326 |
| Query seconds | 0.29262 | 0.30673 | 0.30413 |
| Complete-worker seconds | 0.48003 | 0.47907 | 0.47543 |
| Cold replay seconds | 0.08436 | 0.07879 | 0.07767 |
| Mean peak RSS bytes | 55,427,072 | 55,779,328 | 54,575,104 |
| SQLite bytes | 929,792 | 954,368 | 892,928 |
| Compressed bytes | 85,405 | 86,336 | 85,164 |

Version two removes **41,880 bytes / 60.80%** from equivalence storage: 41,208
bytes of duplicated formula fields plus 672 bytes of field overhead. The payload
itself shrinks **47,533 -> 5,653 bytes**; the 21,345 bytes of exact source keys stay.
Combined certificate payload is now **6.17% below the native control**, although
it still contains twenty more certificates. SQLite falls 61,440 bytes versus v1
and 36,864 versus the native control. Gzip falls 1,172 / 241 bytes respectively;
compression already exploits much of the redundancy. Sidecars increase about
4.1 KB versus v1 because they record the new counters, and remain about 46.9 KB
above the native control. Archive savings do not imply every artifact shrinks.

The compact publisher parses 21,345 source-key bytes across the 42 publications.
It still checks 174 tree edges and scans 10,859 substitution/verification
literals, exactly as v1. Both versions perform 45 substitution steps, 358 native
expansions, 68 discovery calls, 4,276 constructed graph edges and 8,552 SCC edge
visits. No solving work is credited to the storage change.

Timing does not establish a stable end-to-end win. Against v1, complete-worker
deltas are **+0.00590 / -0.01318 seconds**, with a 0.76% lower mean. Query deltas
also have opposite signs. Cold replay is lower in both orders by 0.00073 / 0.00151
seconds, with a 1.42% lower mean. Against the native control, complete deltas are
**-0.01210 / +0.00290 seconds**; query time is **3.93% higher** in the mean and
higher in both orders. Mean RSS falls about 1.20 MB versus v1, an observation on
these runs rather than a memory-scaling bound. All policies remain optional.

## Bounds, persistence and next gap

The version-two record still requires `O(L+k)` encoded source/evidence units,
for source size `L` and a `k`-literal equivalence block. It removes the additional
source and quotient formula copies, not the source key. Key decoding takes
`O(L)` time; exact canonicalization, full substitution, native child verification
and history replay remain charged. The two-tree bound and satisfiability argument
are unchanged. There is no new Lean theorem or unrestricted-SAT resource bound.

**Next priority: reuse binary-core discovery across wide-clause edits.** On this
unchanged catalog, 56 eligible inputs contain only 34 distinct exact binary keys;
22 queries rebuild a binary graph already encountered. Cache complete discovery
outcomes and source-checkable trees in binary-local coordinates, transport their
clause references back into each current full source, and invalidate the key
when binary clauses or their variable coordinates change. Missing/changed edges
must not inherit an old equivalence. Measure cache construction, lookup, retained
space, verification, persistence and cold reconstruction as well as avoided SCC
work. The compact record retains exactness while leaving this duplicated
computation untouched. An observed cache opportunity is not yet a speedup.

Twelve inputs also have a second disjoint equivalence block, omitted by the
single-block policy. Full quotient keys were not already available at those
query prefixes. Multi-block reduction and integration with the existing SCC
pass remain later targets; more variable reduction alone does not guarantee
less acquisition or fewer records. Prepared production integration, broader
structural coverage and arbitrary-CNF interaction bounds remain open.

Resume `experiments/results/cnf-compact-equivalence/checkpoint.json`. All
**28,691 native payloads**, **twenty-six affine records** and **42 v1 equivalence
records** are preserved byte-for-byte. No new native or v1 payload is inserted;
the union adds **42 v2 alternatives** and 68 explicit compact decisions alongside
5,650 old composed and 136 old pilot decisions. Four alternative native roots
remain in trial archives. Union growth is **69,632 SQLite / 3,701 compressed
bytes**, retaining both versions. This preservation growth is separate from the
smaller v2-only trial archive. Negative equivalence roots still require their
explicit reader and are not ordinary native source roots.

All **1,228 tests**, **59 focused tests**, 408 chronological dependency audits,
68 exhaustive truth tables, warm reuse and full old/new cold history validate.
Eight new tests cover 4,096 small cross-version acquisitions, exact key parsing,
wrong source/child publication, positive dependencies, corrupt trees, old-only
and native-only archives, both formats coexisting, signed edits and disabled
recognition. Full tests retain 44 pre-existing SQLite warnings; focused tests
have none. All 586 prior sources, 7,642 artifacts and 109 manifests are unchanged.

The **223-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **591**. New manifest: **41
artifacts**. Next preservation audit: **7,683 artifacts / 110 manifests**.
