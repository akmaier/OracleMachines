# Pass prepared missing leaves into native acquisition

The partial-cover traversal already constructs a conditioned formula, its
canonical form, variable map and full key before invoking native acquisition.
The optional handoff lets that next call consume this preparation once. It
preserves every native read, expansion budget, certificate check and model lift.

Five duplicate normalizations disappear, saving 3,133 literal visits and 13,573
bytes of key serialization on the existing stream. Total timing does not
improve: preparation plus query is 2.29% slower than the preceding carried-origin
policy, and complete-worker mean is 2.58% slower. Both comparisons have two
faster and two slower pairs. Keep this experiment optional and preserve the
regression; fewer operations alone do not establish a runtime advantage.

## Binding and correctness

The external target and cover still enter the existing validation and copying
path. Inside `recompose`, a private frame producer binds an immutable source
tuple to the exact normalization result computed for it. The native `_visit`
receives this same object. A temporary method wrapper returns the prepared
triple only for that object's identity, once, then restores ordinary
canonicalization before lookup, expansion, recursion or proof publication.

Equal-looking inputs do not consume the offer. A `finally` path restores the
previous method on exceptions, including failure before consumption and budget
exhaustion. No prepared triple arrives through an external hint or persistent
record. The solver requires exclusive use during the synchronous call, as the
existing partial composer does. This is internal transport of a pure result,
following the earlier [cofactor handoff](cofactor-handoff.md), rather than a new
certificate authority or a content-indexed cache.

For this native canonicalizer, re-evaluating the immutable source returns the
same normalized clauses, names and key. Replacing that single repeated call
therefore preserves the native continuation, apart from normalization counters.
The native reader and `_store` retain their checks. The model uses the same
names to return to source coordinates; recomposition still checks the full
target witness. UNSAT still requires every reachable branch, and one shared
expansion budget applies to all acquired leaves. No new Lean theorem or
unrestricted-SAT bound is claimed.

The partial-cover interface already rejects tautological clauses. An initial
test incorrectly expected acceptance; its failure log is preserved. The final
test checks unchanged rejection, including malformed literals. It does not
broaden this internal interface to every external CNF encoding.

## Matched evidence and resource accounting

The native baseline, carried-origin policy and handoff policy use the same
historical prefix, donor, 23 sources and six supplied guards in four alternating
serial orders: 1,656 conditional queries. Each worker returns 125 UNSAT and
13 SAT results. Timed workers finish before diagnostic profiling and audits.
All inputs were already solved under the baseline; structural coverage is
unchanged.

| Mean per worker | Native baseline | Carried origins | Leaf handoff |
| --- | ---: | ---: | ---: |
| Preparation + query, seconds | 0.420725 | 0.424623 | 0.434336 |
| Expansion dispatches | 55 | 32 | 32 |
| New native payload, bytes | 1,551,836 | 1,508,442 | 1,508,442 |
| Active hints, bytes | 11,505 | 42,031 | 42,031 |
| Selected retained Python state, bytes | 8,460,643 | 8,348,782 | 8,337,127 |
| Complete worker, seconds | 3.646220 | 3.703857 | 3.799307 |

Preparation/query mean is 3.24% above native baseline. Relative to the preceding
policy, the four pair differences are +10.17%, -4.78%, +4.24% and -0.47%.
Local measurement variability is substantial; neither these regressions nor
the operation savings establish a universal performance ordering.

| Query | Result | Baseline ms | Carried ms | Handoff ms |
| --- | --- | ---: | ---: | ---: |
| 7 / guard 4 | SAT | 9.347 | 17.477 | 15.703 |
| 15 / guard 3 | UNSAT | 16.429 | 22.371 | 22.025 |
| 19 / guard 3 | UNSAT | 17.658 | 13.418 | 17.404 |
| 20 / guard 3 | UNSAT | 23.210 | 19.504 | 20.082 |

Proof payloads, hints, chronological origins, branch events and all native
verification/publication counts remain identical between the reuse policies.
Independent profiles count 89 to 84 normalizations over these four queries,
with per-query counts 17/27/18/27 changing to 16/26/17/25. Restrictions remain
unchanged. Profiling adds overhead and cumulative times overlap; it is not a
second comparative timing trial.

The handoff adds constant-many temporary references and a wrapper around
objects already owned by traversal. It creates no retained dictionary, sizing
scan or serialized entry. The selected object graph at worker end is 11,655
bytes smaller (0.14%), consistent with sharing prepared keys and clauses.
This endpoint measurement excludes temporary allocations and is not a peak-RAM
bound. Stored bytes remain unchanged. Overall space, native verification costs,
search-tree growth and integer/key sizes still need their existing accounting.

## Next experiment: finer surviving branches, with a negative control

Acquisition and native checking remain substantial. The case-15 profile still
contains 26 normalizations and nine proof publications. Further preparation
sharing would leave the same unresolved branch computations. Investigate
whether an earlier recomposed proof can supply a finer surviving branch inside
a currently broken support, thereby avoiding some native work.

A separate diagnostic extracts from actual earlier recomposition proofs, with
the same supplied guard and no future origin. Both extractors agree exactly.
Cases 15 to 19, 15 to 20 and 19 to 20 preserve the missing-leaf counts: 1, 2
and 2 respectively. After the target's checked unit prefix, the case-15 proof
offers an extra split for case 20: one missing residual shrinks from 693 to
683 literals and from 113 to 112 variables; the other stays at 673 literals.
The case-19 proof yields exactly the same missing residuals as the current
policy. Preserve that failed admission idea rather than counting a newer
origin as an improvement.

This is a small, specific hypothesis. Price admission, extraction, candidate
ranking, extra branch publication, retained hints and cold replay before
preferring it. Missing-leaf counts alone cannot rank total cost. If the finer
branch does not pay for its upkeep, return to broader unlabelled guard/map
discovery rather than adding another general normalization cache. Automatic
useful guards, reusable descriptions across unfamiliar categories and efficient
acquisition for arbitrary CNFs remain open.

Twelve new tests cover all 256 clause deletions of the three-variable cube,
shared budgets, sparse names, source mutation, equal-but-distinct input,
restoration on errors, invalid certificates and unchanged input rejection.
The full suite passes 1,602 tests; the focused suite passes 93. Both readers
audit 76,501 cumulative native records, unchanged extension tables and 342
prior partition records. No new native identity or authoritative payload is
needed. The preceding 13,184 artifacts across 149 manifests remain unchanged;
851 source files are bound by the new seal. The full suite retains 44 existing
unclosed-SQLite warnings, with none in the focused suite. Evidence and the
development failure are retained in `experiments/results/cnf-leaf-handoff/`.

The final manuscript builds to 249 pages without LaTeX/layout warnings; its
64 existing proof environments are unchanged. The new manifest seals 89
artifacts, bringing the cumulative record to 150 manifests and 13,273 artifacts.
