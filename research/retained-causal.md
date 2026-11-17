# Loading acquired causal supports without repeating discovery

The [causal-support experiment](causal-support.md) found useful smaller
refutations, but re-extracting them from every old origin outweighed the query
saving. This comparison loads that acquired frontier on another novel stream.
It retains pending descriptions and the matching causal materializer, and still
charges complete proof, query and historical-lineage checks.

## What loading guarantees

`load_causal` checks the saved file's fingerprint and requires its explicit causal
slicing and deferred-construction markers. It preserves every saved field and
does not rediscover supports. `retained_bank` binds the description to
`CausalCoreBank`. On an actual match, that bank checks canonical identity and the
ordinary negative proof. A missing root requires causal materialization followed
by proof checking. A ready root avoids derivation, while still being checked.

The file fingerprint and markers are format/identity checks, not proofs of UNSAT
or historical provenance. A forged matched hint cannot publish an unchecked
answer. The complete cold auditor checks all query proofs and every index origin
on a pinned snapshot, including unmatched entries. The current source query's
guard is checked online. The exclusively owned live archive remains append-only;
there is no persistent unchecked validity flag.

The six new tests cover exact field preservation without rediscovery, changed
bytes, wrong materializer policy, pending causal materialization without fresh
solving, reuse of ready proofs without repeated extraction, and rejection of a
malformed matched identity. The broader suite and independent archive replay
remain part of verification.

## Matched histories and timing boundary

All modes start from the acquired 18,672-key union. The legacy mode loads the
207-entry old-rule frontier. Rebuilt discovers the causal frontier again from
the same 389 historical origins. Retained loads the acquired 176-entry causal
frontier. Both saved banks use the same eight ordered source catalogs; neither
adds the latest 51 guarded negative outcomes. Those outcomes remain preserved.

Query selection excludes all 1,728 earlier sidecar answers and cached full roots,
then selects the next 64 salted two-deletion neighbours from each of the three
templates. Three balanced fresh-process triples visit all 192 queries twice.
Timed workers run without overlapping tests, builds or profiles. The old
whole-query core and one-clause SAT witness routes remain enabled throughout;
positive witness exploration stays optional and disabled in this comparison.

Complete time includes restoration, common old-bank checks, reading and binding
the support description, discovery when requested, normalization, lookup, actual
proof checks, materialization, querying, persistence, complete cold proof/query
and index-lineage audit, compression, and final digest/report generation. Imports,
initial command-line JSON reads and the final wrapper rewrite are excluded.
Selection and all historical acquisition remain separately charged.

This is a current-union comparison on novel queries. It does not erase the
earlier cost of discovering the frontier or establish a general break-even point.
Simply repeating known queries already benefits from exact result caching.

## Resource obligations that remain

Loading costs the serialized frontier bytes, fingerprint computation, parsed
objects, copied core descriptions and clause-set construction. These are not
constant-time operations. It avoids the previous extraction traversal, but
ordinary proof validation remains necessary at actual use and in the complete
cold audit. Materialization can still add many proof nodes; full query input,
canonicalization, containment scans and serialization remain charged.

The negative frontier retains every raw support, origin and dominance witness.
Pending roots are not deleted merely because they are unused on this stream.
The acquired graph and future derivations may be exponential in the input CNF.
No bound on arbitrary-SAT acquisition, minimum cores, cross-guard coverage or
uniform polynomial expansion follows from loading a finite acquired index.

The experiment reuses a fixed frontier. Incremental causal discovery from a
genuinely new batch remains a separate next step; its source ordering, first
origins, materializer binding and invalidation rules must remain explicit.

## Results: the reconstruction cost is avoided

| Mode | Cofactor hits | Expansions / splits | New rows | Complete seconds | Query seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Load legacy frontier | 19 | 120 / 37 | 319 | 10.56570 | 1.48203 |
| Rebuild causal frontier | 25 | 93 / 30 | 365 | 12.74826 | 1.02010 |
| Load causal frontier | 25 | 93 / 30 | 365 | 10.63701 | 1.49335 |

Loading avoids all 2,851 support-discovery node visits. Preparation falls
**2.29443 -> 0.08099 seconds**, and complete runtime falls **16.56%** against
rebuilding. All three pairs improve (17.58%, 15.90%, 16.20%). Rebuilt and retained
frontiers, query answers and proof archives agree; their SQLite databases are
byte-identical. Complete cold proof/query and lineage audit remains charged.

Query time rises **46.39%** against rebuilding because reconstruction had warmed
ordinary proof checks before the query clock. Loading still reduces the complete
cost. It does not make the earlier discovery, common old-bank checks, parsing,
containment or actual proof verification free. The new loader's empty solver
preparation counters mean no support proof reads in that phase, not zero total
preparation work.

Against legacy loading, complete runtime is **0.67% higher**, with mixed paired
signs (-0.45%, +0.18%, +2.30%). There is no demonstrated net speedup. Six additional
targets—current cases 12, 119, 125, 141, 164 and 191—account for all 27 avoided
expansions, a **22.5% reduction**. No query regresses in expansions. All modes
answer **99 SAT / 93 UNSAT**; 45 guards include two positive children. All causal
hits still share their first origin's guard clause. Repeated visits add no rows.

## Why smaller supports still cost more certificates

Retained causal matches require **100 materialization rows** versus **33** for
legacy matches. The full accounting is:

- Legacy: 120 expansions + 33 materialization rows + 97 SAT witness publications
  + 50 whole-query core publications + 19 cofactor publications = 319 new rows.
- Retained: 93 expansions + 100 materialization rows + 97 SAT witness publications
  + 50 whole-query core publications + 25 cofactor publications = 365 new rows.

The 19 targets covered by both banks account for **74 causal versus 33 legacy**
materialization rows. The six extra causal hits require another 26 materialization
rows and six target publications. This identifies a concrete next experiment:
prefer an existing cheaper proof for overlapping targets, using the smaller
causal support where it adds coverage. The apparent 41-row opportunity is a
post-hoc attribution, not a proved saving for such a dispatcher; sharing and
later cache contents can change when the proof choice changes.

Retained causal trials have 48 ready frontier roots and 128 pending descriptions.
Mean peak RSS is **14.56% above legacy** and **11.24% above rebuilding**, with
positive differences in every pair, though their sizes vary substantially.
The allocation cause is not established. Gzip plus first-trial raw sidecars is
**12,173,774 bytes**, against 12,657,545 for legacy and 12,165,270 for rebuilt.
The saved frontier files are also identical. The sidecar difference comes from
query records with different checking counters and timings; proof archives are identical.
There is no improved asymptotic memory bound. Historical trials and the final
preservation union remain additional retained state.

## Updated priorities

Avoid routine re-extraction of this fixed bank. The next expansion-cost candidate
is proof choice on overlapping matches, measured against both current frontiers
on the same novel queries. Keep all acquisition and verification costs explicit.
Incremental causal acquisition from new origins remains separate and optional;
this run adds no new sources to either index.

The retained mode spends **41.29%** of complete time in full cold audit and
**33.65%** in compression, limiting gains from query search alone. Memory
attribution should distinguish loaded descriptions, duplicate strings, proof
objects and transient snapshots before claiming a particular allocation cause.
These are supporting cost questions, not evidence that checks can be skipped.

Remaining expansions comprise **74 negative / 19 positive**. Current negative
cases 14 and 161 cost 19 and 15; SAT cases 45 and 91 cost 14 and five. Templates
12/6/8 account for 54/33/6 expansions. Compare unresolved conditional structures
and test genuinely different guards; broad cross-guard coverage remains open.
These are current-catalog IDs, not the earlier streams' or original structural IDs.

The complete 492-test suite passes but emits unclosed-SQLite ResourceWarnings
during older tests; allocation origins were not traced. The focused six new
tests pass with ResourceWarnings enabled and none emitted. Both logs are retained.
This warning is an unresolved test-lifecycle issue, not a failed SAT proof check.

## Validation and retained authority

Independent validation passes **492 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,997 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. The union retains
**19,091 keys / 59,228,160 SQLite / 4,491,457 gzip bytes**, adding 419 keys while
preserving every earlier payload. All **48 alternate certificate occurrences**
remain in trial archives. New decisions have **147 direct roots / 45 guards**,
including two positive guarded results.

Resume `experiments/results/cnf-retained-causal/checkpoint.json`. It preserves
all inherited semantic fields, adding `retained_causal_study` and
`retained_causal_decisions`; the saved frontiers themselves are unchanged. Load
`causal_support_proposals` with the fingerprinted causal loader and matching
materializer. In the union, the causal frontier has **48 ready roots / 128 pending**;
the extended legacy frontier has **121 / 86**, and the original 170-entry frontier
has **120 / 50**. Both measured banks keep the same eight-catalog, 389-origin
lineage. The ninth catalog is excluded from selection but not added to discovery.
The original frontier retains its six-catalog lineage. All three union audits pass.

All prior **381 sources / 4,230 artifacts / 74 manifests** remain unchanged.
Runtime binds 385 sources; the analyzer brings the ledger to 386. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds to **200 pages** without warnings,
with **64 unchanged proof blocks**. No new Lean result or unrestricted-SAT bound.
The full test log retains 24 unclosed-SQLite ResourceWarnings during older tests;
the six focused new tests emit none with warnings enabled. Their allocation
origins remain untraced; this is not a failed proof check.

The new manifest binds **56 artifacts**. The next preservation audit inherits
**4286 artifacts / 75 manifests**.
