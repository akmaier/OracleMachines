# Share preparation inside partial-cover reconstruction

The prepared route reuses the conditioned formula, variable map and key already
constructed by the traversal when it publishes an intact leaf. A split already
fixed by the checked unit prefix also reuses that frame. It preserves identical
native proof payloads, learned hints, origins, decisions and expansion counts.
All native certificate checks remain enabled.

The construction saving is exact, but the timing gain is small. On the same
23-source, six-guard stream, preparation plus query improves 0.98% on average
against the preceding partial route. Three of four paired repeats improve and
one regresses. The mean differs from native baseline by only 0.06%; this is
effectively a tie on this experiment, not evidence of a robust baseline win.

## Binding and cost

Every call copies the raw target and cover and validates support containment,
unit reasons and cover paths. Prepared frames are created and consumed inside
that synchronous call. They are not accepted from callers or persisted as
authority. A reused context must still imply the leaf's assumptions. The leaf
publisher constructs the same unit proof from the already conditioned target,
and the ordinary native verifier checks it before storage.

An unchanged context can reuse the same canonical triple. An absent split
variable also leaves the cofactor unchanged. All other branches still restrict
and canonicalize their target. Positive witnesses, missing-leaf acquisition,
the shared dispatch budget and checked-prefix retention retain the preceding
semantics. Changes to source, cover or assumptions are validated on every call.

The measured stream avoids six repeated leaf preparations and one unchanged
frame reconstruction. A diagnostic rebuild produces the same native delta and
finds 96 to 89 normalization calls across the four partial queries. The helper
restriction counter falls by 5,549 literal visits. The new implementation also
counts its initial root canonicalization, which the preceding implementation
omitted when resetting counters. Both timings already charged it. Do not mix
that accounting correction with saved operations; the profiler call comparison
and direct old/new payload tests isolate the actual reduction.

The live frame and copied cover add temporary state. This is bounded by the
current target and the existing bounded cover, not a new constant-space claim.
Stored proof and hint bytes are identical. The measured selected Python-state
endpoint is slightly smaller; it does not include all transient allocations.

## Matched results

Three policies run in four alternating serial orders: 1,656 conditional queries.
Each worker agrees on 125 UNSAT and 13 SAT answers. No final hints or future
answers seed the chronological stream. The existing donor, extraction, matching,
checking, serialization, warm reads, persistence and cold reconstruction remain
charged. This experiment changes construction, not structural coverage.

| Mean per worker | Native baseline | Previous partial route | Prepared partial route |
| --- | ---: | ---: | ---: |
| Preparation + query, seconds | 0.440247 | 0.444333 | 0.439990 |
| Expansion dispatches | 55 | 32 | 32 |
| New native payload, bytes | 1,551,836 | 1,508,442 | 1,508,442 |
| Active hints, bytes | 11,505 | 42,031 | 42,031 |
| Compressed delta + hints, bytes | 156,321 | 180,373 | 180,373 |
| Selected retained Python state, bytes | 8,460,643 | 8,362,875 | 8,348,782 |
| Complete worker, seconds | 3.688698 | 3.668851 | 3.582865 |

Complete-worker mean is 2.34% below the preceding partial route, but it includes
variable restore, checking and reconstruction phases. Four local repeats do
not establish a general end-to-end improvement. Selected retained state is
0.17% lower, while persisted artifacts are identical. Hint validation/reload
is audited separately from complete-worker native-answer replay.

| Query | Result | Baseline ms | Previous partial ms | Prepared partial ms |
| --- | --- | ---: | ---: | ---: |
| 7 / guard 4 | SAT | 9.101 | 18.766 | 17.459 |
| 15 / guard 3 | UNSAT | 17.392 | 26.328 | 24.863 |
| 19 / guard 3 | UNSAT | 18.241 | 16.546 | 14.729 |
| 20 / guard 3 | UNSAT | 24.168 | 21.529 | 21.529 |

The later transfers still improve over baseline, but the first two attempts
remain expensive. Identical proof bytes rule out smaller proofs or easier
targets as the explanation for the caller-side preparation reduction.

## Next bottleneck: extracting original conditional reasons

The two first-use queries each still extract a cover from an earlier checked
negative origin. Extraction takes about 20 profiled milliseconds in each case;
the corresponding queries take about 49 and 71 profiled milliseconds. These
instrumented times include profiler overhead and are not the timings above.
The extractor rebuilds residual-to-original-clause representatives by scanning
the full source at each proof node. There are roughly 2,000 restriction calls
in each cold query. The later warm transfers avoid that discovery cost.

The next task is to carry original reason-clause provenance through unit,
split and component transitions, reusing unchanged residuals where possible.
Preserve source coordinates, exact assumptions, duplicate-clause handling and
the deterministic representative rule. Check whether existing preimage-reuse
machinery can supply this binding. Charge preparation and retained provenance;
retain unsupported endpoints and extraction-budget stops. Keep the SAT control
and compare first extraction with subsequent reuse on matched edits.

Learning new origins from recomposed outcomes, automatic useful guards and
variable correspondence remain secondary gaps. Missing leaves still require
general SAT acquisition. This bounded construction adds no unrestricted
polynomial-time guarantee.

Eight new tests compare exact old/new payloads for all 256 subsets of a
three-variable contradiction, verify both answer types and sparse labels,
compare shared-budget prefixes, reject invalid paths and unit prefixes, and
check invalidation after source edits. Raw comparisons and the separate
identical-proof profile are preserved in
`experiments/results/cnf-prepared-partial/`.

Validation passes 1,579 full tests and 90 focused tests. Both readers audit all
1,656 comparison queries, 76,501 cumulative native records, unchanged extension
tables and 342 prior partition records. No native identities or authoritative
payloads change. All 13,006 prior artifacts across 147 manifests remain intact;
the new seal binds 839 source files. The full suite reports 44 existing
unclosed-SQLite warnings, with none in the focused suite. The 248-page manuscript
builds without LaTeX/layout warnings and preserves its 64 proof environments.
