# Preserve clause order during exact residual normalization

The optional `OrderedNormalizationSolver` checks clause-local literal order and
uses it to avoid rebuilding literal sets and sorting ordered clauses. It also
removes the second per-clause sort after compact variable renaming. On the same
104-input stream, it avoids 96,099 sort calls and reduces mean query time 2.17%
against the batched control, with both orders improving. It remains 1.19% slower
than the preceding 128-KiB memo in this comparison. Warm time regresses 2.95%.
Keep both alternatives optional; no default change or new SAT coverage follows.

## Exact transformation and its limits

Every clause is frozen and every literal is validated as a nonzero exact integer.
The scan checks strict ascending order. For an ordered clause, two pointers start
at its least and greatest literals. A sum of zero detects a complementary pair.
If the sum is negative, the least literal cannot pair with any remaining literal,
so advance the lower pointer. If positive, the greatest literal cannot pair with
any remaining literal, so decrease the upper pointer. Once one sign is absent,
no complementary pair remains. Each step removes one candidate or finds a pair;
the test is linear in clause length, charging integer arithmetic separately.

Unordered or duplicate-literal clauses use the original set, tautology check and
sort. This fallback covers valid inputs that fail the local recognizer; they are
not rejected or classified as unsatisfiable. Global duplicate clauses are still
removed. The entire input is validated before empty-clause collapse, so neither
an early empty clause nor a tautology hides a later malformed literal.

Let `r(v)` be the increasing rank of positive variable `v` in surviving support.
The signed map `f(x) = sign(x) r(abs(x))` is strictly increasing on that support:
positive order follows increasing ranks; negative order reverses both magnitude
and rank; negative literals still precede positives. Every surviving clause is
already sorted, including fallback outputs. Therefore mapping it through `f`
preserves order and the second sort is redundant. Distinct variables remain
distinct, and the original-name tuple remains the same. Sorting the support and
the complete set of mapped clauses produces exactly the original normal form
and full key for every valid finite CNF, not merely the measured families.

This is a proof of the normalization transformation, not a new SAT tractability
result or a Lean verification of the Python implementation. Restriction preserves
local order, distinctness and absence of tautologies. It can nevertheless create
duplicate clauses, change global clause order and leave noncompact names. For
example, restricting `((1,2),(1,3),(2,3))` by `1=false` yields
`((2,),(3,),(2,3))`, which is not globally sorted. Those obligations remain checked.

## Matched measurements

Six serial workers compare unchanged batching, the unchanged 128-KiB memo, and
the ordered path in opposite orders. The ordered path uses no memo. All start
from empty archives with the same 104 inputs, publication policy and direct cold
reader. Timing includes recognition, fallback, snapshots, keying, checking,
metadata, persistence, warm/cold replay, sidecars and compression. Diagnostic
profiling, exhaustive truths, history checks and tests follow the timed workers.

| Measurement | Batched control | 128 KiB memo | Ordered path |
|---|---:|---:|---:|
| Ordinary normalization calls | 1,163 | 901 | 1,163 |
| Normalization literal visits | 119,547 | 94,069 | 119,547 |
| All profiled `sorted` calls | 103,170 | 80,393 | 7,071 |
| Mean query seconds | 0.295351 | 0.285541 | 0.288951 |
| Mean complete seconds | 0.512607 | 0.501520 | 0.503999 |
| Mean warm seconds | 0.010516 | 0.010699 | 0.010826 |
| Additional retained normalization cache | None | Up to 128 KiB charged | None |

The ordered path recognizes 47,059 of 49,833 clauses (111,043 literal units).
It falls back on 2,774 clauses (8,504 units), performs 37,566 two-pointer steps,
and avoids 46,748 initial sorts and 49,351 mapped-clause sorts. It still validates
all input literals and snapshots 119,547 literal references. Of the ordered
clauses, 311 are tautologies and are discarded. Per-clause counts include repeats
across calls and queries; they are not distinct SAT patterns.

The two ordered query deltas against batching are -2.06 and -10.74 ms; complete
deltas are -6.76 and -10.45 ms. Mean complete time falls 1.68%. Warm deltas are
**+0.371 and +0.249 ms**. The earlier memo is faster on both query comparisons;
the ordered alternative avoids its retained cache but does not establish a
whole-process memory saving. Mean RSS is 60.64 / 60.90 / 60.83 MB, respectively.
All cold readers and archives are identical, so cold-time variation is not an
effect of ordered normalization. Two short replays do not establish statistical
or representative general-SAT performance.

Every answer, model, quotient choice, ordinary work counter and proof byte in the
ordered arm matches batching exactly. The memo retains its previously verified
normalization/key savings. All arms preserve 552 native / 53 extension records,
505 expansions, 104 commits, 651,784 combined key/payload bytes, 1,179,648 SQLite
bytes and 125,493 compressed bytes. No persisted answer or proof format changes.

## Resource account and checks

Ordered clauses require linear scans plus tuple hashing; fallback clauses still
require set construction and sorting. Support collection/sorting, compact-name
mapping, global clause sorting, full-key serialization and proof checking remain.
Integer bit lengths and tuple comparison costs matter. Temporary raw tuples and
the global clause set remain linear in input representation size. The change adds
no retained cache and removes some temporary sets/sort outputs, but we have not
measured a transient allocation bound. Removing sort calls does not establish an
asymptotic improvement in unrestricted solving or bound residual-DAG growth.

Eight new tests cover all 341 literal sequences of length at most four over two
signed variables, 441 pairs of short clauses, all 3,304 subsets of at most three
of the 27 canonical three-variable clauses, 500 seeded mixtures and their
reversals, sparse/huge names, invalid literals after empty clauses/tautologies,
restriction counterexamples, unchanged solver decisions, failure recovery and
cold proof reads. Both normalizers agree on all 28,886 archived canonical CNFs
and on 4,961 representation mutations, including their invalid-literal cases.

The broader audit checks 624 chronological queries, 416 exact alternative/control
pairs, 104 exhaustive truths, 144 quotient choices, 84 known hits and independent
proof validation after all 104 ordered-arm commits. Both old readers validate
the complete union and all 5,650 composed / 444 pilot decisions. All 632 prior
source fingerprints and 7,990 artifacts across 117 manifests remain unchanged.
The new checkpoint references the unchanged parent union rather than duplicating
it: `experiments/results/cnf-ordered-normalization/checkpoint.json`.

All **1,300 full / 131 focused tests** pass. The full suite emits 44 unclosed-SQLite
ResourceWarnings at unchanged files, as in the parent; focused tests emit none.
This existing suite issue remains open. The **228-page manuscript** builds without
warnings and keeps all **64 earlier proof blocks** unchanged. The final source
ledger contains **638** fingerprints; logs and checks are preserved with the data.

## Next investigation

The ordered normalizer remains the largest exclusive site in the posthoc profile:
1,163 calls / 0.07034 exclusive / 0.14104 inclusive seconds. Restriction remains
780 calls / 0.06935 inclusive seconds. These are instrumented overlapping times,
not independent portions to add or substitutes for matched wall-clock results.

The next priority is a larger held-out stream of mixed and unresolved CNFs, with
growth in variables, shared interfaces and edits. This 104-input stream now shows
small gains and warm regressions; it cannot establish whether normalization or
fresh solving dominates broader workloads. Freeze the new cases and budgets
before choosing another optimization, report unresolved classification outcomes
and peak retained proof state, and compare batching, memo and ordered variants.
Only then choose between transporting immutable residual invariants directly,
combining order recognition with targeted reuse, or reducing fresh acquisition
through a new structural decomposition. None of those savings is claimed here.
