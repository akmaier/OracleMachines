# Defer canonical preparation on inconclusive binary checks

The preceding binary-closure experiment found more refutable cofactors but
increased total time and retained proof storage without completing more roots.
Its worst fresh query normalized 67 post-unit residuals and obtained only six
binary refutations. This experiment addresses that specific wasted preparation.
It retains both the handoff-only solver and the slower binary gate as controls.

## Mechanism and exact correspondence

The new helper receives an exact canonical cofactor and the complete,
nonconflicting unit propagation result already computed for it. If no variable
was forced, the formula is already canonical and the original closure runs
directly. There is no extra preflight in that case.

Otherwise, restrict the cofactor using its forced assignment, extract the raw
binary clauses, and test their implication graph. A uniform satisfying
assignment can skip the graph test. An inconclusive result returns neither a
canonical residual nor a key nor any authority. The ordinary prepared-child
handoff and search continue unchanged. An empty or unit clause is rejected as
an incomplete unit closure; a conflicting unit result is outside the helper's
input contract.

Only a raw binary contradiction triggers normalization of the full residual,
key serialization and a second SCC pass on its canonical binary clauses. The
second pass preserves the preceding gate's exact path choices and certificate
bytes. Existing native implication and unit certificates bind the result back
to its original cofactor. The full native verifier checks every publication.
Raw paths are never installed as proof authority.

This correspondence relies on the input invariant, not on treating arbitrary
clause lists as canonical. In a normalized cofactor each clause has distinct
literals and contains no complementary pair. Restriction preserves those
properties. It can create duplicate clauses and holes in variable numbering.
Normalization then removes duplicate clauses and applies an injective variable
renaming; both operations preserve satisfiability of the binary subset, and
clause widths are unchanged. Thus raw and canonical binary tests have the same
verdict. Canonical reconstruction uses the same ordered clauses and deterministic
SCC routine as the preceding gate, yielding the same certificate. All broader
search choices and source checking remain necessary implementation invariants.

A satisfiable binary subset does not certify the full CNF. A negative cofactor
excludes one parent polarity; it does not alone refute the parent. This change
introduces no new tractable family or claim about unrestricted SAT.

## Resource account

For a post-unit residual with literal volume `L`, `m` clauses, `b` binary
clauses and `v` variables in the binary subset, raw discovery pays restriction,
a width/sign scan and the existing SCC routine. The graph routine uses
`O(b + v log(v+1))` expected word operations, including its variable sort, and
`O(b+v)` graph space. The raw residual itself uses `O(L)` word space. Literal
bit lengths and Python representation costs remain separate from this word
account.

Restriction scans the input cofactor's literal volume `L0`, even if its residual
is small. For a valid complete nonconflicting unit closure, a forced-assignment
miss therefore costs `O(L0 + m + b + v log(v+1))` expected word operations in
this helper. This excludes the already completed unit pass and the later
ordinary-search continuation, which remain charged to the whole query.

An inconclusive forced-assignment probe avoids one full-residual normalization
and one full-key serialization. The keys are full serialized CNFs, not fixed-size
hashes. A successful probe still pays those costs and now also pays a raw graph
pass before canonical graph reconstruction. Raw duplicate clauses can enlarge
the graph compared with the deduplicated gate. Both costs are charged in the
measurements. Original source/cofactor preparation, unit propagation, checking,
publication and persistence remain in place.

The helper adds no retained cache or database schema. Exact naive/lazy proof
identity should imply identical retained authoritative payloads on the same
chronological search; this is checked rather than inferred from verdicts alone.
Construction transients and process RSS need not decrease. The native dispatch
cap still excludes compiled cofactor certificates and is not a total-work bound.

## Reproducible comparison

The implementation is `experiments/cnf_probe_binary_lazy.py` and
`experiments/cnf_probe_binary_lazy_solver.py`. The measured constructor is
`LazyBinaryClosureSolver(..., handoff_bytes=2*1024*1024)`; the inherited default
is still 256 KiB. No production default changes.

`experiments/compare_cnf_probe_binary_lazy.py` freezes the preceding 126/150
holdout as exposed data and a new 132/156 stream with seed 202611240406 before
evaluation. Each stream has 72 queries, 48 distinct roots and six construction
families. Only source CNFs enter search. Four alternating serial repetitions
compare the handoff-only control, eager binary closure and lazy binary closure;
every worker starts empty with native dispatch cap 256 and the same pending
preparation allowance. No cases are removed based on outcomes.

Worker time includes setup, recognition, failed checks, canonical reconstruction,
native checking, fallback, serialization, persistence, retained-state accounting,
warm/cold replay, reconstruction and compression. Imports, source hashing, case
loading, final bookkeeping, tests and the historical preservation audit are
outside the matched means. Tests and profiling do not run concurrently with
the timed workers.

Raw trials, protocols, failures, checked archives and the next resumable
checkpoint are preserved under `experiments/results/cnf-probe-binary-lazy/`.
The initial test attempted to read legacy tables before their lazy creation on
a budget-zero run. The corrected test compares absent tables as empty without
creating solver state. Its original source and failure log remain preserved;
the algorithm did not change.

## The exposed preparation gap

On the preceding worst regression, exposed case 38, all policies still exhaust
256 native dispatches. Both binary gates make 100 closure attempts and refute
six cofactors. Lazy preparation delegates 33 already-canonical probes to the
original gate, inspects 67 raw residuals, and normalizes only the six refuted
ones. It avoids exactly the 61 previously identified unnecessary normalizations
and adds six canonical SCC reconstructions. This closes the specified redundant
preparation gap without deciding that root.

Across the exposed stream, the new gate skips 1,321 normalizations and serializes
5,243,487 fewer key bytes. Normalization literal visits fall from 12,874,145 to
11,662,365. Restriction visits stay at 15,465,261; graph edges increase from
341,918 to 369,868 and closure SCC calls from 2,028 to 2,106. Of 80 negative
cofactors, 78 need canonical reconstruction after forced assignments. These
operation counts explain the saving and its added costs; they do not replace
the complete runtime comparison.

## Matched result: cheaper than the eager gate, still behind handoff-only

| Stream and policy | Mean solve seconds | Mean complete-worker seconds | Completed distinct roots |
|---|---:|---:|---:|
| Exposed handoff-only | 17.0551 | 34.4708 | 40/48 |
| Exposed eager closure | 18.5433 | 36.4709 | 40/48 |
| Exposed lazy closure | 17.9483 | 35.8882 | 40/48 |
| Fresh handoff-only | 24.1536 | 48.5653 | 34/48 |
| Fresh eager closure | 26.2932 | 51.2914 | 34/48 |
| Fresh lazy closure | 25.3543 | 50.5323 | 34/48 |

Lazy preparation reduces solve mean by **3.21% exposed / 3.57% fresh** versus
the eager gate, and complete-worker mean by **1.60% / 1.48%**. Every solve pair
improves. One exposed worker pair regresses by 0.11%; the other seven improve.
These four fixed repetitions per stream do not establish population performance.

Against handoff-only, lazy closure still raises solve mean **5.24% / 4.97%**
and complete-worker mean **4.11% / 4.05%**. Every such pair regresses. Keep the
gate experimental. Deferred preparation is a measured local improvement, not
evidence for enabling the broader gate by default.

Both binary gates have identical verdicts, models, dispatch counts, proof bytes,
selected retained state and persisted database size. On fresh inputs they use
6,351 native dispatches versus handoff-only's 6,402, but retain 9,045 native
records versus 8,829. Their native key-plus-payload bytes are 108,801,475 versus
105,972,793 (+2.67%), and selected retained Python state is 446,762,601 versus
435,267,649 bytes (+2.64%). SQLite occupies 167,227,392 versus 163,074,048 bytes;
compressed archives occupy 12,234,389 versus 11,874,502 bytes.

Mean peak RSS is 1.409 GB eager / 1.379 GB lazy / 1.345 GB handoff-only on fresh
workers. Exposed values are 1.255 / 1.200 / 1.211 GB. These process measurements
include allocator and transient effects and are not retained-space guarantees.
Fresh cold replay is 10.4583 / 10.4188 / 10.1906 seconds in the same order;
reconstruction is 1.1811 / 1.3917 / 1.1852 seconds. All costs, including the
reconstruction regression, remain in complete-worker means.

Fresh lazy closure attempts 2,923 cofactors and refutes 114. It avoids 1,549
normalizations and adds 108 canonical SCC passes. Of the 2,809 inconclusive
attempts, 1,260 already have no forced assignment and cannot benefit from
deferred normalization. The overall raw/previously-canonical
split is 1,657/1,266; six refutations are already canonical. Normalization
literal visits fall 17,672,856 to 16,193,580 and serialized key bytes
129,828,899 to 123,398,953 versus the eager gate. Graph edges increase
490,408 to 529,200. No new persistent hint table is introduced.

The different streams have different unresolved sets. All policies complete
40/48 exposed roots and 34/48 fresh roots; this is not a policy-induced coverage
loss. The 14 fresh unresolved roots comprise eight random-three sources, four
disjoint-mixture sources and two shared-mixture sources. Fresh lazy solve time
is 14.5877 seconds in random-three, 6.0933 in disjoint mixtures and 3.9457 in
shared mixtures, together 97.13% of its 25.3543 seconds. Broader structural reuse
on unfinished searches is the next coverage question.

## Next investigation: retain useful structure from unfinished origins

The posthoc exact-prefix profile selects fresh case 64, the largest mean
lazy-minus-handoff query regression at 0.1557 seconds. It is a disjoint-mixture
edit and remains unresolved in every arm. Lazy preparation removes 61
normalizations there, but the profile still records 375 native stores, 722
normalizations and 895 restrictions. The helper accounts for 0.0898 of 1.9508
instrumented query seconds. Profile times overlap and include instrumentation;
they are not estimates of unprofiled savings from further changes.

Its preceding source, case 63, also exhausts 256 dispatches. The two canonical
formulas use identical variable coordinates and differ by exactly one deleted
and one added clause. Yet the whole-plan lookup scans ten completed negative
origins, finds no eligible plan, and never uses case 63 as a plan origin.
`WholeProofReuseSolver._try_whole_plan` searches the checked negative pool;
`extract_partial` requires a checked negative root. Existing individual
residual reuse remains available. The missing route is a source-bound branch
plan obtained from an unfinished origin.

`experiments/inspect_cnf_stopped_origins.py` records all 24 fresh base/edit pairs.
Seven have unfinished origins when their edits are queried: 0/1, 3/4, 36/37, 39/40, 60/61, 63/64 and 66/67.
They span random-three and both mixture categories. All seven targets remain
unresolved. Origin status is chronological: case 60 is unfinished at edit 61,
but its later repeat 62 completes that root. That future answer cannot be used
at edit 61. The completed-origin control 27/28 already reuses 22/27 leaves and
still stops, so extending eligibility alone cannot be assumed to solve them.

The next step is a census of actually reusable checked conditional leaves and
their source mappings on these unfinished searches, beginning with 63/64 and
using 27/28 as a control. Retain a bounded branch skeleton, mark unfinished
leaves explicitly open, and record the exact source clauses, guards and variable
maps needed by each checked leaf. A deleted supporting clause invalidates a
leaf; matching syntax or a stopped parent is never a negative certificate.
Composition must cover both sides of every split and solve remaining open
leaves against the actual edited source. Measure extraction, retention,
recognition, invalidation, checking and cold reconstruction before adding a
live gate. No reusable-leaf count, timing gain or new coverage is claimed yet.

The census must also classify leaf proof kinds. The current partial extractor
handles empty, unit, split and component rules; other endpoints become open
holes. In particular, a stored implication certificate is not automatically
a reusable conditional unit template. Separate missing origin eligibility from
missing endpoint transport, and keep unsupported leaves open until their source
bindings and composition rules are implemented and checked.

## Validation and persistence

All 1,697 tests pass, including 86 focused checks. The full suite retains 44
pre-existing SQLite ResourceWarnings; focused tests have none. The 255-page
manuscript builds without warnings, with all 64 preceding proof environments
unchanged. No Lean source or formal theorem is changed by this implementation.

The independent audit checks 1,728 query records, all six table payloads and
the chronological plan/pool bindings. Both native readers verify every retained
trial node, including stopped prefixes, and the cumulative archive with all
342 preceding partition records. The 353 earlier exposed census probes reproduce
their UP bindings, binary verdicts and exact canonical certificates; deferred
preparation avoids 164 normalizations there while retaining all 19 refutations.

All 159 preceding manifests and 14,390 artifact entries remain unchanged. The
cumulative archive adds 9,070 native and eight affine-negative records, retaining
155,830 native and 147 affine-negative records alongside all earlier equivalence
and core tables. It occupies 2,021,847,040 database bytes and 146,494,308 compressed
bytes. Raw trials preserve alternative valid proofs; earlier authoritative
payloads are not replaced. The multipart archive round-trip is byte-identical.
Resume its checkpoint with `experiments.cnf_archive_parts.restore_archive`.

Audit time is 1,117.2 seconds, including cumulative verification and archive
packaging, outside the matched worker means. This research-history expense is
separate from the measured empty-start solver trials and remains recorded.
