# Reusing prepared source indexes for exact restriction

The optional `IndexedRestrictionInventory` reuses occurrence indexes for validated
immutable source objects, updates only affected clauses, and shares unchanged
clause tuples in its residuals. Both modes use ordered propagation, the same
1 MiB successful-proof cache, the same discovery policy and the ordinary solver's
scan path. All **1,497 answers, profiles, roots and persistent bytes agree**.
Coverage remains **869/985 non-tiny**, with **116 sources / 148 selected leaves /
33,651 literals** unresolved. This is a locality-dependent acquisition optimization,
not a new recognized family or unrestricted SAT bound.

## First full sample: a mixed total-cost result

| Measurement | Ordered propagation baseline | Indexed restriction |
| --- | ---: | ---: |
| Full operation seconds | 132.36551 | 134.44214 |
| Discovery seconds | 93.85938 | 90.65563 |
| Ordinary solver seconds | 38.45513 | 43.72392 |
| Cold replay seconds | 60.86819 | 56.04772 |
| Warm inventory seconds | 0.25887 | 0.28366 |
| Initialization seconds, separate | 0.00156 | 0.22247 |
| SQLite bytes | 437,620,736 | 437,620,736 |
| Logical node bytes | 179,395,726 | 179,395,726 |
| Six-case Python peak bytes | 22,474,578 | 24,072,942 |
| Six-case retained Python bytes | 22,162,053 | 23,447,305 |

Discovery improves **3.41%** and cold replay **7.92%**, but full total **regresses
1.57%**. The ordinary solver phase, whose algorithm/path is unchanged, takes
13.70% longer. A single sequential full comparison cannot distinguish run
variation from cache-induced process or memory effects; the total regression
must not be dismissed or replaced by the pilot's larger saving. Python peak grows
**1,598,364 bytes**, and retained traced memory grows **1,285,252 bytes** on the
six-case diagnostic. These are not RSS or full-corpus memory bounds.

Twelve-query ABBA BAAB controls average **4.81769 -> 4.35747 s total (9.55%)** and
**4.52899 -> 4.06290 s discovery (10.29%)**. All four indexed totals
(4.25038--4.58653 s) are below the four baseline totals (4.79110--4.84498 s).
The unchanged solver averages 0.28761 -> 0.29334 s. These selected queries do not
resolve full-corpus total cost or establish significance. Because of that
uncertainty, a separate reversed-order full comparison is retained alongside
this original run; no first-run result is overwritten.

## Reversed full order and paired result

The [second full comparison](../cnf-indexed-restriction-reverse/README.md) runs
indexed first, baseline second, making the combined order **baseline / indexed /
indexed / baseline**. Its totals are **142.37374 baseline / 128.27877 indexed s**,
and discovery **100.72151 / 87.66682 s**. All within-mode operation counters,
storage and database hashes repeat exactly across the two runs.

| Mean of two full samples per mode | Baseline | Indexed |
| --- | ---: | ---: |
| Total seconds | 137.36963 | 131.36045 |
| Discovery seconds | 97.29044 | 89.16122 |
| Ordinary solver seconds | 40.02449 | 42.13410 |
| Cold replay seconds | 61.16937 | 56.70501 |

Paired means improve **4.37% total**, **8.36% discovery** and **7.30% cold replay**.
The ordinary solver phase still averages **5.27% longer**; the full total saving
is smaller than the isolated discovery saving. Two samples per mode, selected
after a mixed first result, balance order but do not establish significance or
industrial performance. The first total regression and sample spread remain
visible. This supports keeping the candidate as an optional resource tradeoff,
not claiming a pointwise or universal speedup.

Reverse-order six-case Python peaks are **22,474,570 baseline / 24,072,950 indexed
bytes**, repeating the roughly 1.60 MB increase. Its warm times are 0.27772 /
0.26131 s and initialization 0.24576 / 0.00167 s. Every full audit again starts
with empty caches and leaves all previous evidence unchanged. `order-control.json`
in the reverse directory binds both full reports and the wrapper/runner hashes.

## Reuse conditions and work charged

Admission validates an exact tuple of exact tuples of exact nonzero ints. Hits
require the same strongly held immutable object, with an explicit `is` check
following the object-ID lookup. The retained reference prevents recycled IDs;
validated immutability prevents stale postings. Mutable sources, subclasses,
bools/zeros and unusual assignments take the old scan path. These fallbacks
preserve the helper's prior behavior; they are not SAT classifications.

The cache does not merge separately allocated equal objects or reuse indexes
across changed formulas. It stores no assignment or restricted answer. Eviction
causes later preparation, and restart begins empty. Returned unchanged clauses
share immutable tuples; the outer residual tuple is assembled anew. No mutable
index state escapes through those results. The
[correctness and resource account](../../../research/indexed-restriction.md)
makes these conditions explicit.

Full operations record **275,865 indexed-helper calls / 241,198 hits / 34,599
admissions / 34,511 evictions**, with **68 fallback scans**. The baseline scans
**82,210,169 restriction literals**. The candidate instead charges:

- **3,672,644** source-validation clause checks;
- **10,412,650** validation literal checks and **10,412,650** preparation entries;
- **2,986,814** posting visits and **4,038,253** rebuilt-clause literal visits;
- **28,938,355** clause positions in complete residual assembly;
- **4,473** fallback literal visits and **277,169** assignment entries.

These are different operations, not an interchangeable speedup ratio. Full-source
preparation, validation, admission/eviction and output assembly are timed. Every
non-restriction operation counter is identical. Independent simplification
reconstruction remains **51,574,914 literal visits**, and propagation is unchanged.

The retained index cap is **32,768 units**, charging 1+m+L for each source with m
clauses and L literal occurrences. It bounds logical slots up to representation
factors, not bytes/RSS or long integer payloads. One incoming index may be built
before eviction, so transient preparation is additional. Source lookup uses
validated identity; it does not hide canonicalization or semantic matching.
A hit costs O(1+A+P+R+m) word operations under constant map/set access, for A
assignments, P retrieved occurrences and R affected unsatisfied-clause literals.
A miss adds O(1+m+L) preparation. Full output assembly remains O(m), and global
SAT search/acquisition, original graphs and lifetime archive growth remain open.

## Preserved controls and the next bottleneck

Thirty-two controls use 32-query streams at clause counts 16, 64, 256 and 1,024.
Each timing/allocation trial starts with an empty index, and preparation is charged.
All outputs are separately validated; timed loops retain only their last output,
whose equality is checked after stopping the clock. At 1,024 clauses:

| Stream, 32 queries | Baseline ms | Indexed ms |
| --- | ---: | ---: |
| Same source, sparse assignments | 17.81227 | 1.95817 |
| Equal source reallocated each time | 17.91109 | 23.80568 |
| Fresh append each time | 17.75385 | 23.29391 |
| Dense affected-clause updates | 17.90560 | 12.30488 |
| Mutable source fallback | 17.65874 | 17.75230 |
| Oversized source at a 32-unit cap | 17.49730 | 27.90861 |
| Variable absent from source | 17.68876 | 1.88096 |
| Empty assignment | 17.08585 | 10.01653 |

The favorable sparse stream has **31 hits / one admission**. Equal reallocations
and fresh appends have **no hits**, repay no preparation and consume more memory.
For equal reallocations, Python peak grows **173,608 -> 3,239,360 bytes**. Sparse
reuse also grows peak **173,608 -> 817,816 bytes**, despite less output copying.
Empty assignments avoid index retention and return the validated original tuple.
Control allocation excludes preconstructed inputs and is not a full-process cap.
The engine is not pointwise faster and does not solve novel-edit reuse.

On source 1194, separate instrumented discovery falls **3.53284 -> 2.91629 s**.
The same 3,399 restriction calls fall **0.82784 -> 0.21269 s cumulative**, including
dispatch; the new helper itself takes 0.20802 s. Its 3,044 hits and 355 admissions
match observed object locality. The largest remaining named own-time cost is now
**`check_simplification`**, with **2,303 calls / 0.27952 s own / 0.55562 s cumulative**.
Propagation and normalization follow at about 0.19931 and 0.19240 s own time.
These profiles are diagnostic, not primary timings; nested cumulative costs must
not be added.

The next cost question is how to reuse exactly bound checker reconstruction state
without losing independent validation. Full outer-tuple assembly and preparation
for equal/new sources also remain. Broader coverage still requires new certified
relations or exact decompositions of the same unresolved frontier. The current
index adds none, and the baseline remains available.

## Validation and persistence

All **425 tests** pass. New tests cover **87,516 exhaustive ordered-formula / partial
assignment pairs**, checking all compatible complete two-variable assignments,
plus **4,000 seeded random/edited restrictions**, source/assignment type aliases,
mutable edits, tuple sharing, cap/oversize/eviction behavior, scoped restoration,
all 148 saved frontier probes and byte-identical acquisition/cold replay.

Both full modes recreate the existing implication archive SHA256
`1a431206ef825d2a8f7d5697cf1342119fe68d97950ca6ca8f180d18b6bdccf3`, containing
25,047 pattern nodes, 1,465 source bindings and 21,838 solver residuals. The report
references it relative to the repository root instead of storing another full
archive. Cold audits start with empty proof/index caches, check all alternatives,
sources and ordinary solver certificates, and leave the bytes unchanged. Warm
replay inserts nothing. The smaller pilot retains one shared archive.

The checker reconstructs its input branch directly, but creating that branch now
uses the trusted indexed helper when enabled; checking does not prove the index
implementation itself. The manuscript adds an algorithm-level correctness argument,
preserving all 57 previous proof blocks. Lean sources remain unchanged and were
not rebuilt; there is no new Python refinement. Full and pilot reports have **70
fingerprints**. The diagnostic identifies its original implementation commit;
profiles/timing/controls have separate script/input hashes. Historical results
remain intact. Benchmark, allocation, timing and profiling jobs run sequentially.

Reproduce in a fresh destination:

```sh
python3 experiments/compare_cnf_indexed_restriction.py --output /tmp/new-indexed-restriction
python3 experiments/recheck_cnf_indexed_restriction_timing.py /tmp/new-indexed-restriction
python3 experiments/analyze_cnf_indexed_restriction.py /tmp/new-indexed-restriction
python3 experiments/measure_cnf_indexed_restriction_controls.py /tmp/new-indexed-restriction
```
