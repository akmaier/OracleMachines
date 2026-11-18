# Larger mixtures expose edit-reuse and discovery gaps

The new frozen evaluation uses 108 queries at scales 24, 48 and 72, rather than
replaying the earlier small catalog. Both recent normalization alternatives
regress against plain batching on mean query time: the memo by 1.49%, and ordered
normalization by 1.09%. All three produce exactly the same answers, work outside
normalization, and proof bytes. Their earlier local savings do not establish a
general runtime improvement.

There is also a concrete recovery result. A SAT model learned later in the stream
certifies the one source still unresolved at its end. A separate helper checks
the donor and the complete target, then publishes one native SAT certificate
without calling search. The original timed budget stops remain recorded as
unresolved. Candidate selection is supplied in this recovery experiment; a
cost-effective general candidate index is still missing.

## Frozen workload and accounting

Six deterministic generators produce random 3-CNF, parity equations with added
clauses, gated Horn/dual-Horn formulas, graph-colouring encodings, disjoint mixtures
and mixtures sharing two variables. Each scale has two samples per generator.
Each sample contributes a base, an edit deleting one clause and adding one, and
an order-reversed, monotonically relabelled repeat of the base. Disjoint edits
bridge the original supports. Actual support is recorded; shared mixtures have
two fewer constructed variables. The 108 queries contain 72 distinct canonical
roots, all absent from the parent archive. No case is filtered by solver outcome.
These designed families are not a representative distribution over arbitrary SAT.

Six serial workers compare batching, memo128 and ordered normalization in opposite
orders, starting with empty archives. Family labels never enter search. Each
attempt permits 256 native `_expand` calls. This does not cap all discovery,
helper proof compilation, time, memory or stored nodes. Only the specific budget
exception becomes an unresolved observation; other errors abort the run.
Committed verified prefixes survive; pending writes and their checked aliases
roll back. Metadata uses append deltas instead of rescanning the entire history
after every query. Generation and novelty auditing are reported separately.

| Mean measured cost | Batching | Memo128 | Ordered |
|---|---:|---:|---:|
| Query stream, seconds | 2.70053 | 2.74084 | 2.72996 |
| Complete worker, seconds | 5.31870 | 5.33886 | 5.38948 |
| Warm completed queries, seconds | 0.03615 | 0.03697 | 0.04106 |
| Cold proof replay, seconds | 1.15510 | 1.14514 | 1.18071 |
| Peak worker RSS, MB | 275.05 | 273.56 | 275.12 |

Query time includes metadata deltas, acquisition, discovery, normalization,
verification and publication. Complete time additionally includes setup, a final
retained-object walk, warm/cold replay, sidecars and compression. Compression
takes about 0.98 seconds per worker. Imports, posthoc profiles, classification and
history checks are outside worker timing. Cold readers and archives are identical;
their variation is not an optimization benefit. Worker RSS includes benchmark
metadata, cold readers and compression, not just solver state.

Both memo query deltas regress (+46.57 / +34.05 ms), as do both ordered query
deltas (+55.05 / +3.80 ms). Complete deltas are mixed for both. Warm regressions
are 2.28% and 13.59%, respectively. The memo avoids 632 normalizations but performs
1,862 evictions; its peak charge is 131,071 bytes. Preserve all measurements and
keep these alternatives optional. Two repeats do not establish statistical gains.

## Where expansion and memory go

The timed stream records 70 SAT, 36 UNSAT and two unresolved attempts. The stops
are the 72-variable random-three base and edit, cases 75 and 76. Each commits
256 proof records; 20 and 13 pending records roll back. Helper compilation makes
the number of stored records different from the native expansion counter.
The later repeat, case 77, solves the base with another 112 expansions using the
archive accumulated from both earlier attempts. Do not attribute that benefit to
the first attempt alone. Before the separate recovery, 71 of 72 source roots
have certificates: 47 SAT and 24 UNSAT.

Random-three consumes **58.48%** of query time and parity-bridge **21.54%**.
The two capped attempts alone consume about 0.823 seconds. Across all families,
the 36 edits require 1,013 expansions and 1,055 new records, close to the bases'
1,041 expansions and 1,086 records. Exact repeats need only 112 expansions and
118 records in total, all from the continuation of the previously capped base.
This makes transfer across small clause edits a stronger next target than another
small reduction in normalization overhead.

| After scale cohort | Cumulative native records | Cumulative key/payload bytes | Cohort query seconds |
|---|---:|---:|---:|
| 24 | 234 | 373,609 | 0.11300 |
| 48 | 914 | 3,268,388 | 0.64140 |
| 72 | 2,259 | 12,128,848 | 1.94613 |

These are cumulative measurements on this ordered stream, not an asymptotic
storage law. Final SQLite storage is 22,851,584 bytes, compressed to 1,438,997.
The deduplicated graph of checked proof and discovery caches occupies 53,930,391
Python bytes. All three variants retain the same graph and persisted bytes.
The measured memory gap is retained proof representation and growth in distinct
residuals, not the bounded normalization memo alone.

Posthoc profiling still places normalization first: batching uses 4,269 calls /
0.98884 exclusive / 2.50675 inclusive seconds. Restriction uses 3,821 calls /
1.29115 inclusive seconds, and propagation 1,990 calls / 0.93559 inclusive seconds.
Inclusive values overlap and instrumentation changes relative costs. Reducing
fresh residual acquisition can avoid these costs together; profile reductions
alone did not translate into matched runtime savings.

## Structural classification and a checked reuse opportunity

The existing bounded pattern inventory separately examines every query with
depth one, four conditioning candidates and parity-width cap eight. All 108 roots
share the same coarse outcome vector: six syntax tests exclude their named
representations, while single-parity recognition is unresolved at the width cap.
This does not exclude broader semantic equivalences or systems of parity equations.
Component decomposition produces 18 root AND nodes; the remaining 90 use bounded
conditioning. Only the 18 gated-Horn queries obtain closed family decompositions.
Native decision success on the other inputs must not be reported as structural
closure. All overlaps and unsuccessful alternatives remain in the inventory.

The inventory stores 624 checked pattern nodes and 108 source bindings. Its
acquisition takes 1.18314 seconds and independent cold replay 0.53552 seconds;
stored pattern/source payload is 5,183,569 bytes and retained checked objects
16,987,873 bytes. This posthoc discovery work is separate from timed solver search.

A posthoc full-source witness check finds that **21 of 23 available parent SAT
models** also satisfy their edits. Those edits incurred 225 expansions and 235
new records in the actual stream. This is an opportunity indicator, not an
additive saving: changing acquisition also changes future cache contents, and
candidate discovery was supplied by generator metadata.

The new `reuse_checked_model` helper requires an idle owned solver, obtains a
checked native SAT donor, transports its assignment through original variable
names, tries false for absent names, and checks the entire target source. A
failed check or unavailable/non-SAT donor returns only a miss. A valid target is
published through the original native witness verifier. No search is performed.
Candidate lookup, alternative renamings and a bounded selection policy remain
outside the helper.

After the timed stream, case 77's checked model supplies the donor for case 76.
With expansion disabled, recovery validates all 918 target literals and publishes
one certificate containing 7,895 key/payload bytes. The observed operation takes
2.84 ms, excluding donor discovery and earlier acquisition; this is not a speedup
comparison with the earlier failed attempt. Both native readers check the entire
recovery archive: all **72 distinct roots** now have certificates, **48 SAT / 24
UNSAT**. The two original budget-stop observations are unchanged. This finite
recovery result supplies no uniform bound for arbitrary SAT.

## Preservation, validation and next step

All 638 prior source fingerprints and 8,032 artifacts across 118 manifests remain
unchanged. Validation covers 648 chronological attempts, exact cross-arm/repeat
comparisons, every new proof and the prior 5,650 composed / 444 pilot decisions.
The enlarged union adds 2,254 records from the timed stream plus the recovered
certificate: **31,141 native** records, with the previous **26 affine / 42 v1 /
53 v2 / 22 v3 / 34 discovery** records preserved. The separate inventory and all
unsuccessful observations remain bound by the checkpoint.

An initial inventory audit omitted the default `decompose=True` from its expected
configuration and failed a source-binding assertion. The corrected audit uses
the complete configuration; the failed validator, log and already checked union
are preserved. The solver runs were not changed or repeated to select results.

All **1,311 full / 142 focused tests** pass, including six tests for donor names,
miss semantics, malformed targets, persistence and forbidden fresh search. The
full suite retains 44 unclosed-SQLite warnings at unchanged files; focused tests
emit none. The **228-page manuscript** builds without warnings with all **64 prior
proof blocks** unchanged. Final executable ledger: **647** fingerprints.

Resume `experiments/results/cnf-larger-mixtures/checkpoint.json`. The next concrete
implementation target is bounded, label-free SAT witness candidate retrieval,
with complete target validation, publication and misses charged. Compare it on
this now-exposed stream and freeze another evaluation split before tuning.
The highest-cost unresolved *mechanism* remains reuse of partial negative search
across edits to random 3-CNF: successful model reuse does not address UNSAT cases.
Support-sensitive proof reuse, shared interfaces and compact retained proof
representations remain open. A completed finite catalog is not an efficient
partition or solution of all SAT.
