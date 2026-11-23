# Use checked pools before preparing recovery

The 23 November checkpoint moves existing negative-core and witness lookup ahead
of optional conditional recovery, after an exact-template miss. The useful arm
uses early pool lookup followed by ordinary native acquisition. It preserves
all proof bytes of the previous compact-cache arm. Combining early pools with
recovery still loses on total query cost, so no default solver policy changes.

## Recognition and authority

A negative candidate must have an existing checked native origin. The existing
negative pool checks clause containment, and may perform its bounded causal
support discovery and materialization on a near edit. The resulting subset proof
is checked again for the complete target. This is not a constant-time lookup.
A positive candidate is a packed vector indexed by compact variable count.
Every target clause is checked before native publication checks the full model
again. Matching variable count is only candidate selection, not an equivalence
or correctness assumption.

The caller supplies its already canonicalized target and full key. Publication
uses the existing bounded transaction wrapper and native verifier. An invalid
key, stale negative origin or failed witness never certifies a result. Commit
failure follows the existing rollback and checked-cache invalidation rules.
No fresh SAT search is called by the pool probe. A miss returns no answer and
can be tested again by the ordinary fallback: this implementation introduces no
miss cache or new invalidation assumption. Negative support proposals and the
small bounded witness pool retain their previous maintenance rules.

## Frozen comparison

The experiment retains all fifteen preceding inputs and adds four fixed-seed
two-clause deletions. Each of nineteen sources receives six supplied guards.
Five policies in two opposite serial process orders give 1,140 attempts. All
agree on 103 UNSAT and eleven SAT **cofactor** answers per worker. The common
donor acquisition costs nine expansions. Initial construction, preparation,
recognition, native checking, serialization, persistence, warm answer reuse,
reconstruction and cold answer replay remain charged. Persisted hint reload is
audited separately, outside complete-worker timing.

| Policy | Query expansion dispatches | Preparation + query mean (ms) | Native payload bytes | Compressed delta + hints (bytes) |
|---|---:|---:|---:|---:|
| Native | 133 | 361.09 | 1,343,598 | 126,777 |
| Compact templates | 55 | 374.89 | 1,237,109 | 126,657 |
| Gated recovery | 45 | 458.25 | 1,409,164 | 140,493 |
| Early pools, native fallback | 43 | 365.54 | 1,237,109 | 126,657 |
| Early pools, recovery | 39 | 434.98 | 1,383,341 | 138,090 |

Early pools with native fallback produce eight negative-core and four witness
hits, alongside 71 template hits, twelve cached roots and nineteen native
fallbacks. Those twelve pool hits previously returned through the native
expansion dispatcher. Moving them earlier removes twelve expansion-dispatch
counts; it does not shrink the branching proof. **Every stored proof byte,
chronological addition and final delta matches compact reuse in both orders.**
The selected-container Python endpoint is also identical at 6,847,167 bytes.
The measurement omits set contents, native allocations and other state, so it
is not a total-memory bound.

Preparation plus query mean falls 374.89 to 365.54 ms, or **2.50%**. Query-only
means fall 362.87 to 352.86 ms. The previous ninety controls save 3.22% in query
time and the twenty-four additional queries save 1.55%. Full-worker means are
2.829 and 2.838 seconds, respectively: there is no end-to-end gain in this pair.
Native-only preparation plus query time remains slightly lower at 361.09 ms.
Two process orders establish neither statistical significance nor a robust
speedup beyond this local comparison. Repeated pool misses and their costs
remain in the raw counters, including counters retained before native fallback
resets its accounting.

Early pools before recovery reduce the previous recovery regression, but its
434.98 ms preparation-plus-query mean remains above compact reuse and it grows
proof storage. Recovery changes the subsequently retained pool contents too:
that arm has four negative-core hits, four witness hits and nine recovery calls.
There is no basis for attributing every later difference to one isolated lookup.
The regressions and all alternative native payloads remain preserved.

## The next larger duplication

A separate query-only cProfile run reproduces the exact early-pool proofs and
routes. It is excluded from comparative means. Normalization costs about 0.297
profile seconds cumulatively, template materialization 0.295, and native
acquisition 0.271. These categories overlap and instrumented timings are not
additive phase costs. The profile locates repeated work rather than predicting
a speedup.

The **71 template hits** are the next concrete target. The query has already
restricted and canonicalized the source under its guard and checked that exact
root. `materialize` repeats template/source containment, full restriction and
canonicalization before ordinary publication. Both calls still have the same
source, assignment and canonical result available. The observed 173 template
checks equal 102 uncached first checks plus 71 repeated checks.

Reuse that exact preparation within the call, with immutable source/assignment
bindings and explicit variable-name maps. Retain all native verification and
account for ownership, retained state and input copying. Do not replace this
with an unchecked cross-query memo. This addresses a larger measured cost than
caching the small failed pool scans. Whole-source proof serialization and
cumulative native storage remain separate gaps even if construction is shared.

## Limits and validation

The existing negative pool has bounded candidate count, input-literal and causal
walk caps; its proposal and proof reconstruction can still be appreciable work.
The witness pool scans at most its configured number of same-size candidates,
and each requires full-target checking in the worst case. This scheduling
change proves no uniform efficient SAT family, automatic donor/map discovery,
compact closure under arbitrary edits, or P-versus-NP result. It adds no proof
rule, whole-input coverage cell or new Lean theorem.

Runtime code is `experiments/cnf_pool_priority.py`; the comparison and profiler
are separate frozen/diagnostic scripts. Resume from
`experiments/results/cnf-pool-priority/checkpoint.json`. `analysis.json` combines
pre-fallback and final counters so failed probes are charged. The first test
fixture accidentally used the generic affine dispatcher to populate a native
pool; its failures and source are retained, and the fixture now uses the same
native acquisition path as the experiment. Tests cover near and exact negative
hits, sparse witness transport, failed candidates, stale origins, key binding,
commit failure, independent cold readers and exhaustive small streams.

Validation passes 1,528 full tests and 236 focused tests. All 1,140 paired
attempts and 114 diagnostic-profile attempts replay with matching answers.
Both readers check 76,429 cumulative native records, the unchanged extension
tables and all 342 preceding partition records. The union adds 68 identities
without changing any earlier authoritative payload. All 12,606 older artifacts
across 142 manifests remain unchanged. The full suite retains 44 unclosed-SQLite
resource warnings; focused tests have none. The seal binds 810 source files.
The manuscript builds without LaTeX/layout warnings and preserves all 64 earlier
proof environments.
