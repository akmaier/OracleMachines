# Recognize stored canonical formulas without normalizing them again

Direct canonical-form recognition improves the measured verification cost across
the current SAT categories. On the same 104-source replay, query time falls 5.79%,
cold replay 18.12% and complete-worker time 6.63% against the unchanged
known-quotient control. Both query, cold and complete paired deltas are negative.
All answers, models, quotient choices, certificates and ordinary acquisition/proof
counters are identical. This is an optional research implementation with a small
workload result, not a new SAT category or a production/general speed guarantee.

## Exact condition and implementation

A certificate stores a formula that must already be a fixed point of the existing
normalizer. For JSON lists of literal lists, that condition is equivalent to:

- Every literal is an exact nonzero integer, excluding booleans and floats.
- Literals in each clause are strictly increasing, with no complementary pair.
- Clauses are strictly increasing in lexicographic order.
- The positive variable support is precisely `1..n` for some n.
- An empty clause, if present, is the only clause.

Necessity follows from the normalizer's validation, sorting, deduplication,
tautology removal, sorted-name renaming and empty-clause collapse. Conversely,
these conditions leave every normalization operation unchanged, including the
identity variable-name map. Empty CNF and the singleton empty clause are distinct
accepted cases. Distinct positive support with maximum equal to its cardinality
is precisely `1..n`; this check occurs before creating that range, so a sparse
huge integer cannot request a huge name tuple. This is a direct argument about
the implemented representation, not an added Lean theorem.

`experiments.cnf_canonical_verify.canonical_certificate` checks these conditions
and constructs an immutable CNF/name-map/full-key triple. It uses clause/support
sets and order comparisons, with no sorting or renaming. `CanonicalVerifyMixin`
passes this checked result into the original `_verify` through a binding that
matches the exact input object and is consumed once. The original verifier still
checks the exact key and formula, the header, the full SAT model or every negative
proof rule and child dependency. The binding is restored in `finally` on both
success and failure; it never authorizes a later equal-looking input. There is no
retained canonicalization cache.

The same mixin supplies `CanonicalVerifySolver` for acquisition and
`CanonicalVerifySnapshot` for cold replay. External source normalization and
transformed residual normalization remain unchanged. The accepted certificate
representation is JSON lists of exact integer lists, as in every existing archive;
arbitrary Python objects with custom equality/iteration or concurrent mutation of
private solver state are outside this contract. No format migration is needed.

## Costs and matched evidence

Six serial workers run the unchanged known-quotient control, the previous 128 KiB
cache and direct recognition in forward and reverse orders. Each starts empty
and receives exactly the preceding 104 inputs: 42 SAT and 62 UNSAT. This includes
the earlier designed edits; no source is newly discovered in this experiment.
The `linear` arm name denotes direct recognition, not a worst-case constant-time
hashing assumption or a linear-time SAT solver.

| Quantity | Known-quotient control | 128 KiB cache | Direct recognition |
|---|---:|---:|---:|
| Acquisition normalization literal visits | 175,148 | 140,863 | 119,547 |
| Direct canonical-form literal checks | 0 | 0 | 55,601 |
| Key bytes serialized | 678,378 | 545,747 | 678,378 |
| Verified native records | 552 | 552 | 552 |
| Fresh native expansions | 505 | 505 | 505 |
| Mean query time, seconds | 0.45985 | 0.47835 | 0.43324 |
| Mean warm time, seconds | 0.01075 | 0.01521 | 0.01062 |
| Mean cold time, seconds | 0.10076 | 0.09918 | 0.08249 |
| Mean complete-worker time, seconds | 0.69873 | 0.71872 | 0.65244 |

Direct recognition replaces 552 complete normalization calls covering 55,601
literals and 22,520 clauses. Normalization-only literal visits fall 31.75%, but
those literals are still checked by the recognizer. It also constructs 7,518
name-map entries. The saving is avoided sorting/deduplication/renaming machinery,
not omitted validation. Key serialization and all semantic proof checks remain.
Cold trial replay replaces the same 55,601 literal visits, reducing its normalizer
count from 113,436 to 57,835.

Query paired deltas are **-0.02943 / -0.02379 seconds**, cold deltas
**-0.02401 / -0.01251 seconds**, and complete deltas **-0.05423 / -0.03836 seconds**.
Warm deltas have mixed signs (-0.00035 / +0.00009 seconds); no warm speedup is
established. Two order-balanced observations describe this workload, not a
statistical production result.

All three arms retain the same 552 native / 53 extension records, 651,784 combined
payload bytes, 1,179,648 SQLite bytes and 125,493 gzip bytes. The pre-existing
discovery cache remains 46 entries / 35,779 measured Python object bytes in these
trials. Direct recognition adds no persistent result or canonical cache. Its
two query/warm sidecars grow from about 786 KB to 804 KB through counters. Mean
peak RSS is 59.45 MB for the control and 59.39 MB for direct recognition; this
difference does not establish a process-memory improvement.

Recognition uses passes over clauses/literals plus lexicographic comparisons and
set operations. Adjacent clause comparisons have total prefix work bounded by
the input literal count up to a constant factor. Under usual expected set costs
and unit-cost bounded integers, this is O(L+n) work for L literals and n variables;
integer bit lengths, hashing and key encoding remain charged in the actual
implementation. Temporary clause/support sets, immutable tuples and the full key
need space proportional to their represented data. The scalar object binding is
short-lived, but verification is not zero-space. The original proof and arbitrary
residual-solving costs remain unchanged.

Timing includes setup, recognition, normalization, keying, discovery, solving,
checking, metadata scans, publication, warm/cold replay, sidecars and compression.
Cold replay uses the corresponding reader; separate unchanged-reader audits
validate every trial afterward. Imports/source audits precede worker timing;
truth/history checks, tests, builds and posthoc profiles follow all timed workers.

## Validation and preservation

The audit checks 624 chronological queries, 416 exact alternative/control query
comparisons, 104 exhaustive truths, 144 quotient choices and 84 known hits.
Both readers then verify the complete preserved archive. All 28,886 native CNFs
also match the original normalizer's exact triple. Another 4,961 representation
mutations, including invalid literals, duplicate/reversed clauses and sparse
variable IDs, match the original acceptance criterion. Some mutations are
identities, so they are not all labelled invalid. Unit tests cover 1,111 small
clause combinations, generated canonical outputs, incorrect models/keys/proofs,
missing children, immutable snapshots, one-use binding and failure cleanup.

Full-archive normalization visits fall from 6,539,939 to 2,649,963, replaced by
3,889,976 direct canonical-form literal checks. Both readers retain all other
proof counters and exactly 26,243,013 serialized key bytes. These are resource
counts from the preservation audit, not matched full-archive timing claims.

Resume `experiments/results/cnf-canonical-verify/checkpoint.json`: the parent
union and all prior decision files are referenced unchanged. This preserves
28,886 native / 26 affine / 42 v1 / 53 v2 / 22 v3 / 34 discovery records, all
5,650 composed and 444 pilot decisions, and 613 prior source fingerprints. The
7,859 prior artifacts and 114 manifests remain unchanged. A test-generator setup
error (sample index outside its documented range) is retained under `failed-test/`;
it preceded source freezing and all timed workers.

## Next target selected from the remaining cost

A separate instrumented solve-only replay reproduces exact outputs, counters and
archive digests for each arm. Direct recognition leaves 1,163 ordinary normalizer
calls (0.17244 inclusive seconds), while its 552 recognizer calls take 0.04826
inclusive seconds. The largest exclusive site is now 605 SQLite transaction exits
at 0.12607 seconds, followed by 1,591 SQL executions at 0.06522 seconds. Inclusive
times overlap; these profiled timings locate costs and are not substitutes for
the matched wall-time comparison.

An additional untimed exact-output census narrows the next normalization
opportunity. Only 45 of 546 `_visit` calls receive an earlier normalized output
from the same source query, covering 8,011 literal units. The corresponding counts
are 53 / 6,243 for source-key decoding, 17 / 1,530 for cover-node construction and
7 / 1,004 for negative-child checks. All 552 `_verify` calls also receive an earlier
output, but their normalization has already been replaced; these are not another
552 savings. The census retains diagnostic state and implements no new transport.
Name-map correctness and all certificate checks remain obligations at every site.

**First investigate bounded batching of verified publications.** Compare fewer
SQLite commits across native and extension records, keeping completed results
durable and making the visibility/retention of partial queries explicit. A failed
batch must roll back its writes and invalidate only affected in-memory checked
state; a successful answer must not escape before its dependency closure commits.
Measure batch memory, commit overhead, recovery and cold replay, with injected
failures and reopened archives. This is a prospective design, not an implemented
saving. Direct transport at the 45 visitation opportunities remains a smaller
secondary target. Neither optimization expands certified structural coverage or
settles arbitrary SAT interaction.

All **1,271 full / 102 focused tests** pass. The full suite emits 43 SQLite
ResourceWarnings at pre-existing sites (the parent emitted 44); the focused suite
emits none. The seal verifies the warning sites against the parent and preserves
its initial count-mismatch failure under `failed-seal/`. The **226-page manuscript**
builds cleanly with all **64 prior proof blocks** unchanged.

Final executable source ledger: **619**. The new manifest binds **45 artifacts**;
next preservation audit: **7,904 artifacts / 115 manifests**.
