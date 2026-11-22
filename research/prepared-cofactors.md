# Reuse cofactor preparation without changing proof authority

The [two-polarity study](bipolar-routing.md) fixed a recognition blind spot but
increased normalization, publication and query costs on nearby edits. This
experiment tests one part of that overhead: reusing an exact normalization result
produced by a cofactor probe during native acquisition or child-proof checking.
It does not change recognition, probe admission, branch choice or proof rules.

## Why a narrow memo

The repository already contains [general query-local normalization reuse](query-canonicalization-reuse.md),
which saved normalizer work but increased total cost on its original catalog,
and [acquisition-to-proof normalization reuse](proof-normalization-reuse.md),
which gave a modest, inconsistent total-time improvement. We retain both results.
The new memo changes the producer/consumer boundary rather than claiming a new
normalization algorithm or SAT class.

Only a cofactor probe produces an entry. It runs the existing normalizer first,
then retains the immutable raw CNF, normalized CNF, original-variable name map
and full canonical key. Only the first canonicalization in a native visit or a
negative-child check can consume an entry. Other callers follow the existing
path. An empty memo skips consumer snapshot/lookup work.

Consumers validate exact nonzero Python integers before equality lookup. Thus
`True` or `1.0` cannot hit an entry for `1`, and equivalent normalized formulas
with different original variable names cannot exchange their maps. Input snapshots
prevent later caller mutation from changing an entry. Hash equality alone grants
nothing. A cache hit replaces only a pure normalization computation: referenced
keys, child availability, UNSAT status, certificates and model lifting are still
checked normally. Missing, wrong or positive children remain invalid negative
proof dependencies.

The memo lasts for one whole query, including the existing short probe and
subsequent partition branches. It clears in a `finally` block on success, stop
or exception and is never written to the archive. Completed proof nodes still
use the existing persistence rules. Inconclusive propagation and unfinished
search continuations are not retained by this change.

## Bound and charged work

The two saved ordinary-variable cofactors individually require conservative
retained charges of **92,763 and 95,187 bytes**, measured before solving. The
frozen cap is **256 KiB**, sufficient for both. Admission includes dictionary,
tuple, string and integer-object sizes, overcounting shared references. FIFO
eviction and oversize skipping affect performance only. The cap applies after
each memo operation; it excludes transient normalization/snapshot construction,
resizing, allocator overhead, accounting fields and the solver's existing state.

A hit still snapshots, validates, hashes and compares the complete raw formula.
This is input-dependent work, not constant-time recognition. Producers still
normalize and size their input. With `E` retained entries and `L` input literals,
validation/snapshot work is linear in the input, while worst-case hash collisions
can require comparisons against multiple entries. Integer widths and allocation
costs remain charged. A fixed retained memo cap does not bound arbitrary SAT
search, total proof storage or whole-process memory.

## Frozen comparison

Three policies run in separate serial workers in two opposite orders:
binary-frequency routing, two-polarity routing, and the same two-polarity routing
with the prepared-cofactor memo. The 15 targets comprise six previous edit
controls, the three saved sign variants and six new fixed-seed nearby edits.
New edit roots are absent from the preceding union. Every arm restores the
same appropriate cold prefix. Donors and maps remain supplied.

The native 256-expansion limit and probe/partition wrapper are unchanged.
Preparation, validation, sizing, lookup, eviction, cleanup, checking, publication,
persistence, warm reuse, cold replay and reconstruction remain measured. The
memo's query time includes opening and clearing its session. Per-query peak
charges are reported separately from sums of acquisition counters. Comparative
timing precedes profiling and correctness audits.

The decisive equivalence check requires identical decisions, models, partitions,
expansions and complete native proof payloads between the two-polarity and memo
arms. A normalization saving must not be attributed to weaker checking or a
different search tree. Persistent proof space is therefore expected to remain
unchanged; any gain would be a reduction in acquisition work at the cost of a
bounded transient memo.

## Result: less normalization, no demonstrated total-cost saving

All three policies return UNSAT on all 15 targets. The prepared and two-polarity
arms have identical decisions, models, expansions, partitions and native proof
payloads. The following totals sum separate streams and average both orders.

| Stream | Two-polarity query seconds | Prepared query seconds | Normalizer input literals, before -> after | Hits / misses |
| --- | ---: | ---: | ---: | ---: |
| Six prior controls | 0.21000 | 0.21145 | 124,393 -> 115,945 | 11 / 109 |
| Original sign variant | 0.01450 | 0.01419 | 10,335 -> 8,140 | 3 / 6 |
| Variable-76 sign flip | 0.01426 | 0.01409 | 9,582 -> 8,140 | 2 / 7 |
| Global complement | 0.01443 | 0.01432 | 10,310 -> 8,140 | 3 / 6 |
| Six new edits | 0.22539 | 0.22709 | 132,839 -> 123,095 | 13 / 101 |

On controls and new edits, normalizer input-literal visits decrease **6.79% and
7.34%**, but query means increase **0.69% and 0.75%**. Control order signs are
mixed; both new-edit orders regress. The sign variants have small lower query
means, with mixed signs on the variable-76 flip. These two repetitions do not
establish a statistical runtime gain. Retain the implementation as an unsuccessful
speed optimization and leave defaults unchanged.

The new-edit memo performs 114 lookups for 13 hits. Consumer snapshots/validation
visit 67,057 literals, and producer snapshots and sizing each visit another
16,961. The avoided normalizer inputs total 9,744 literals. These counts describe
different operations and are not interchangeable CPU costs. They nevertheless
show why reducing sorts/key generation can leave substantial new work.

New-edit native key/payload bytes remain **659,675**, compressed deltas plus raw
sidecars **167,221**, and endpoint checked-object totals **3,849,863 bytes** under
both compared arms. The endpoint measure excludes the already-cleared memo and
is not a process-memory bound. Maximum retained memo charge is **215,699 bytes**
across the trials. A separate object-graph walk on all 22 admissions in the
selected fresh case finds a maximum **159,794 actual graph bytes** below its
**215,169-byte** conservative charge. No oversize skip occurs in these trials;
FIFO eviction and final cleanup are exercised.

Complete measured control time rises 0.71%, in both orders. The new-edit mean
changes -0.01%, with opposite order signs. Complete times on all three sign
variants have higher means. Cold replay and reconstruction dominate this harness;
the memo is absent from the cold readers. Process RSS varies independently of
its small retained bound, and the new-edit sum rises 3.20%. We claim neither
reduced persistent storage nor reduced process memory.

The two-polarity admission problem remains larger than this optimization: on the
new edits, binary-frequency routing takes 53 expansions and 0.17910 seconds,
where both two-polarity arms take 61 expansions. Pure normalization reuse cannot
change that search tree or its additional proof storage.

## Next target: direct handoff and useful propagation evidence

The most expensive new prepared query is case 31's deletion, **110.66 ms**,
compared with **110.48 ms** without the memo. Its exact prefix has no prior-query
extra rows and lacks the query root. Instrumented replays reproduce all frozen
proof payloads and show normalization calls falling **130 -> 122**, while
publication stays at **39 calls** and propagation at **33 calls**. Memo wrapper
work offsets the saved normalization. Function times overlap and include
instrumentation; only the serial trials support performance comparisons.

`next-target.json` retains these paired profiles, the exact source/prefix and an
untimed probe census for both queries in that case stream. Of 22 probe propagation
calls, only three have no initial unit or empty clause; they consume 2,378 literal
visits without a deduction. Thus a trivial unit-free screen addresses only part
of this workload. The other misses can contain useful forced assignments even
without a conflict. They must never be treated as satisfiable answers.

**Next experiment:** avoid a general consumer lookup by handing a prepared,
immutable cofactor directly to the selected acquisition call. Investigate carrying
its non-conflicting unit trace and restricted residual as preparation, with exact
source/name bindings and unchanged discovery priority. A checked negative or a
full model is still required for an answer. Preserve cached-negative lookup;
a unit-free cofactor can already have a stored refutation. Charge any handoff,
checking and invalidation, and compare against binary-frequency routing as well
as both probe policies. Admission and continuation choice remain the larger cost
gaps; a smaller memo alone does not repair them.

## Validation and preserved state

All **1,418 full tests** and **100 focused tests** pass. The eight new tests cover
exact name maps, mutable callers, invalid equal-valued literals, wrong/missing/
positive proof children, capacity/oversize accounting, cleanup, retained budget
stops, 512 small formula/sign comparisons, identical native payloads and both
cold readers. The full suite retains 44 existing unclosed-SQLite warnings; the
focused suite has none.

Independent validation checks all **90 attempts** from **54 serial workers**,
chronological dependencies, exact prefixes, repeated-order agreement and prior
control reproduction. All 30 prepared/two-polarity pairs have byte-identical
native deltas and partition sidecars. Both readers replay cumulative authority,
24 new partition records and 146 preceding records. All earlier payloads remain
intact; the union adds **86 unique native records**, reaching **75,342**. The 68
alternative-payload observations remain in trial deltas, while the union retains
the earlier authoritative payload for existing keys. Other authority tables are
unchanged.

All 719 earlier source fingerprints and 10,203 artifacts in 131 manifests are
verified unchanged. Older unrelated composed/inventory audits remain manifest-
bound. The final source ledger contains 726 files. The manuscript builds to 239
pages without warnings, and all 64 previous proof blocks remain unchanged. Resume
`experiments/results/cnf-prepared-cofactors/checkpoint.json`. This checkpoint adds
no external SAT benchmark or Lean refinement theorem.
