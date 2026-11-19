# Recognize affine contradictions before native acquisition

`InputSafeAffineProbeSolver` adds an optional top-level probe to planned negative reuse.
It discovers complete direct XOR encodings from the input CNF, eliminates the
resulting equations and publishes a contradiction through the existing
`cnf-affine-negative-v1` checker. No family label or supplied donor relationship
enters the query path. This integrates an existing proof authority; it introduces
no new affine algorithm or unrestricted SAT result.

The public adapter snapshots finite outer and inner CNF iterables before the
frozen kernel makes multiple passes. Review found that the original kernel could
consume a one-shot outer iterator before fallback. The first list-only timing
runs remain preserved; all twelve workers were rerun with the snapshot cost.
The snapshot uses O(L+m) references/slots and traverses the complete raw input
before normalized-source limits apply. It is not bounded by those later limits.

## Recognition and exact fallback

Clauses are grouped by their variable support and the parity of their forbidden
assignment. A complete, distinct parity half represents one XOR equation; every
other clause remains in the coupling CNF. Empty clauses are contradictory
zero-variable equations. Discovery never enumerates missing sign patterns.
The independent checker verifies every source clause, complete parity half,
leftover index and elimination dependency before accepting a contradiction.

The probe runs only when the normalized source has at most 256 variables,
4,096 clauses and 16,384 literal occurrences. Discovery stops before exceeding
65,536 row XORs. A consistent extracted system, incomplete useful pattern or
exceeded budget gives no verdict and falls through to the preceding solver.
Consistency of a subsystem does not establish satisfiability of the coupling CNF.

Exact checked affine results are tried first. A known native/equivalence source
skips fresh extraction and follows its original query path. The source size check
comes after normalization and exact lookup, so its limits do not bound those
operations or the checking of a stored certificate. Misses can require a second
canonicalization in the original solver; that cost is measured.

Affine publication uses an immediate checked transaction while the owned
connection is idle. Its checked cache is populated only after successful commit.
Native batching then operates unchanged on fallback. No native certificate gains
an affine dependency. Cold replay uses the existing independent negative store,
and every exact source binding is checked again. Native and affine proof tables
retain their separate authority and old bytes.

## Resource accounting

For an admitted source with n variables, m clauses, L literal occurrences and
q extracted equations, grouping retains O(L+m) source indices and support data.
Support sorting, group sorting, hashing and integer representation costs remain
part of discovery. Elimination performs at most the configured number X of
n-bit row XORs and retains O(q*n+X*log(q+1)) bits for reduced rows and dependency
indices, in addition to the source description and Python container overhead.
This describes the representation, not an isolated process-memory measurement.
Under unrestricted configured limits, q can grow with m; the fixed probe limits
do not bound the subsequent native search.

Proof compilation copies the retained evidence, verifies it, serializes it and
commits it. Those transient copies and the complete checked archive are outside
the discovery limits. Persistent affine storage grows with the distinct accepted
source certificates, and is not capped across a stream. Canonicalization, cold
proof checking, native fallback and the number of unresolved residuals have their
own costs. An early contradiction can avoid a large native proof graph, but the
total saving must include every failed probe and all persistence/replay work.

## Validation and experiment design

Eleven tests cover source-bound contradiction publication, exact cold replay,
consistent subsystems with SAT and UNSAT coupling formulas, size/XOR fallback,
invalid limits, agreement with the original extractor, tampered evidence,
failed commits, corrupted persisted proofs, one-shot outer/inner iterators,
failed fallback accounting and all 512 two-variable formulas.
Two initial assertions used unsuitable fixtures: one root was already cached,
and one contradiction needed exactly the permitted XOR count. Their source and
failure log are retained; corrected fixtures exercise fresh misses and actual
budget exhaustion. The later input-boundary correction triggered a complete
rerun with identical cases and policy limits; no outcome or size selection changed.

The frozen comparison uses witness-only retrieval, planned negative reuse and
the affine probe in two opposite orders. All twelve workers start empty with
the same 256-native-expansion cap. Each arm creates the empty affine table so
setup is charged consistently. The exposed sizes are 42/66/90; a fresh larger
holdout uses 96/108/120. Each stream has 108 attempts and 72 distinct roots from
the same six designs, two samples and base/edit/repeat variants. Generator labels
are used only for reporting. These are constructed workloads, not a representative
external SAT benchmark.

Complete worker time includes setup, recognition and misses, elimination,
certificate construction/checking, publication, native fallback, retained-object
measurement, warm/cold replay, reconstruction, sidecars and compression. Study
preparation and independent posthoc audits are separate. Process RSS includes
harness and replay objects. All native budget-stop observations remain recorded.

## Measured acquisition and storage

| Measurement | Exposed plan | Exposed probe | Holdout plan | Holdout probe |
|---|---:|---:|---:|---:|
| Mean query seconds | 8.43813 | 6.72975 | 20.93019 | 12.16731 |
| Mean complete worker seconds | 16.91283 | 13.47263 | 40.64862 | 23.62610 |
| Native expansions | 4,479 | 3,607 | 8,261 | 4,982 |
| Native records | 5,443 | 4,161 | 8,955 | 5,655 |
| Affine records | 0 | 9 | 0 | 12 |
| SQLite bytes | 59,699,200 | 47,620,096 | 133,857,280 | 77,430,784 |
| Checked graph and candidate bytes | 146,313,471 | 117,696,918 | 368,606,936 | 210,148,243 |
| Mean cold proof seconds | 3.24151 | 2.71966 | 8.36092 | 4.78717 |

Against planned reuse, mean query time falls **20.25% / 41.87%**, complete time
**20.34% / 41.88%**, SQLite bytes **20.23% / 42.15%**, and checked-object bytes
**19.56% / 42.99%**. Both mode orders improve query and complete worker time.
Compared with witness-only search, query time falls **19.93% / 42.96%** and
complete time **23.36% / 44.47%**. These are fixed-stream observations with
different numbers of completed attempts, not equal-work asymptotic comparisons.

The probe adds 125,708 / 311,973 affine key/payload bytes while avoiding much
larger native proof graphs. Mean worker RSS falls from 526,344,192 to 482,885,632
bytes exposed and from 1,344,036,864 to 756,113,408 bytes on holdout against planned
reuse. RSS includes the harness and replay; it is not isolated solver peak memory.
Cold proof time improves **16.10% / 42.74%**, and reconstruction also improves.

Exposed outcomes change from **57 SAT / 41 UNSAT / 10 unresolved** to
**57 SAT / 43 UNSAT / 8 unresolved attempts**. Holdout outcomes change from
**50 SAT / 32 UNSAT / 26 unresolved** to **50 SAT / 43 UNSAT / 15 unresolved**
against planned reuse; witness-only has 27 unresolved. The probe makes 75 / 78
fresh extraction attempts, with 9 / 12 contradictions and 66 misses in each
stream. Exact affine replay supplies another 5 / 6 hits. No discovery size or
XOR budget stop occurs on these streams; separate tests exercise those stops.
All 18 holdout parity attempts finish through affine certificates with zero
native expansions. An earlier native budget stop remains a valid observation
about that earlier policy, not an UNSAT assertion or a record to overwrite.

**Warm replay regresses.** Overall warm time rises from 0.05578 to 0.10659 seconds
exposed and from 0.08649 to 0.17789 seconds on holdout against planned reuse, with
larger completed cohorts in the probe. Restricting to the same completed cases
still shows a regression: 98 exposed queries take 0.05552 versus 0.10517 seconds;
82 holdout queries take 0.08625 versus 0.16669 seconds. These matched solve totals
rise **89.44% / 93.27%**, in both orders. Input snapshots, extra lookups and repeated
normalization on native fallback add work. The acquisition savings must not be
presented as uniformly faster replay.

## Remaining structural gap

In the first holdout probe worker, random 3-CNF consumes 8.969 seconds and shared
mixtures 2.299 seconds: together **92.46%** of 12.187 query seconds. The fifteen
stopped attempts consume **9.335 seconds**, about **76.60%** of query time, and
commit **3,820 checked negative residual records**. All fit the previous 4,096-
literal candidate limit, but that alone does not predict useful retrieval.
Nine distinct source roots remain absent at stream end; some stopped attempts
therefore share roots or finish later. Planned reuse leaves sixteen absent roots;
the probe makes seven additional distinct roots available at stream end, without
losing any previously available root. Eleven additional completed attempts must
not be reported as eleven newly solved distinct formulas.

**Next primary target:** admit a bounded selection of checked residual proofs
from committed partial searches, then test their reusable supports at the current
target residual. The current negative pool admits only completed native query
roots. Exact residual memoization already exists; the new opportunity is checked
containment/support reuse when an edit changes the residual's exact key. Residual
refutations cannot be treated as unconditional refutations of their source queries.
Source/assumption transport or direct checked containment in the current residual
is required. Charge selection, support discovery, invalidation, checking and cold
candidate reconstruction before claiming a saving.

The all-input `residual-frontier.json` records affine rank, free dimension and
remaining coupling clauses after timing. It publishes no further conclusions.
Every remaining holdout budget stop has rank zero, with 96 to 120 free variables;
none qualifies for the existing at-most-eight-free-variable completion routine.
Alternative surviving supports, variable correspondence, shared-variable
decomposition and representative external evaluation remain open. Warm-path
overhead is a supporting optimization; it is much smaller than the outstanding
native acquisition cost on this stream. No uniformly polynomial arbitrary-SAT
method or complete efficient partition is established.

## Preserved evidence

Resume `experiments/results/cnf-affine-probe-safe/checkpoint.json`. Independent
readers verify the union of **54,418 native and 47 affine-negative records** plus
the unchanged equivalence/discovery tables. All 664 previous source files and
8,275 prior artifacts remain unchanged; another 57 artifacts preserve the first
timing and fixture failures. The audit checks 1,296 chronological attempts,
1,296 exact first-run comparisons, all 512 two-variable formulas and the earlier
composed, pilot and stream observations. Older authoritative bytes remain in
place; 78 alternative valid native payload observations stay in trial archives.

All **1,347 full / 208 focused tests** pass. The **232-page manuscript** builds
without warnings and preserves its 64 proof blocks. `checks.json` retains full
suite SQLite warnings and sites; focused tests emit none. The final source ledger
contains 672 files. The source-bound affine and partial-search descriptions,
matched warm cohorts, regressions and open obligations are preserved for later
runs, not inferred from a count of successful test cases.
