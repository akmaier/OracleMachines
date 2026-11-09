# Checked terminal signed-subsumption exposure

The policy closes four previously unresolved sources: **977, 1044, 1053 and
1365**. No closure is lost. Across **1,461 queries**, including 512 exhaustive
tiny CNFs, non-tiny closure rises **833 -> 837 / 949**. The old 1,425-query subset
improves **806 -> 810 / 913**; both policies close 27/36 new queries, including
15/24 fresh random 3-CNFs. All independent solver answers agree. Structural
closure means all selected leaves have recognized families, not satisfiability.

The optional candidate searches only after the existing activity policy has
exhausted discovery. Earlier reductions and depth-two/four-probe/four-clause caps
remain. Every removed clause has a retained signed subset, and complete source
indices, normalized child identities and model lifts are checked. Failed searches
persist. No classifier uses generator labels; the ordinary solver is unchanged.

| Measurement | Activity baseline | Signed subsumption |
| --- | ---: | ---: |
| Total operation seconds | 145.71977 | 156.17943 |
| Discovery seconds | 105.46141 | 117.30413 |
| Unchanged solver seconds | 40.18383 | 38.79213 |
| SQLite bytes | 404,410,368 | 408,301,568 |
| Pattern nodes | 24,367 | 24,122 |
| Logical node bytes | 161,206,197 | 166,021,306 |
| Source-binding bytes, 1,429 records | 5,617,826 | 5,837,892 |
| Cold replay seconds | 61.80056 | 66.82085 |
| Warm inventory seconds | 0.25731 | 0.24904 |
| Initialization seconds, separate | 0.05716 | 0.33504 |
| Six-case Python peak bytes | 19,996,938 | 20,390,270 |
| Selected unresolved literal occurrences | 32,239 | 32,043 |

The broad single sample becomes slower and larger. In contrast, twelve-query
ABBA BAAB controls average **7.28617 -> 6.98024 s** total and **7.00234 -> 6.69509 s**
discovery. Those controls include all four gained sources and are not a repeated
full-corpus estimate. Four trials per mode do not establish statistical
significance. Answers and summaries match the full run; counters, storage and
database hashes repeat within each mode. Do not infer a general SAT speedup or
promote the optional policy from this selective timing gain.

There are **3,753 terminal searches**, including unsuccessful alternatives;
**31** expose a family and **3,722** remain unresolved. Some earlier branches now
stop sooner, reducing conditioning candidates **4,631 -> 4,575**, logical probes
**112,276 -> 110,980** and verified probes **242,280 -> 239,308**. However, discovery
performs **33,367,619 subset comparisons**, and checking repeats them. The saved
search/evidence fields add **3,706,023 bytes**. Across all searched nodes, 3,030
cores change; 7,302 clauses / 22,147 literals are removable. Most such changes
do not expose a basic family and are retained as failed evidence, not followed.

The [pair-cost diagnostic](pair-costs.json) reconstructs every tested prefix from
the checked archive. **27,083,138 comparisons (81.17%)** are between distinct
normalized clauses of equal width, which cannot strictly subsume one another.
Only 6,284,481 compare strictly shorter clauses. Length filtering can avoid those
equal-width tests; no optimized implementation or runtime saving is measured here.
Recognition still has to account for preprocessing, shorter-clause comparisons,
verification, normalization and persistence. The current subset algorithm costs
expected O(L + m log(m+1) + m²w) work and O(L+m) temporary space per eligible CNF,
plus classification and acquired graph costs; checking repeats this search.

The remaining selected frontier contains **112 sources / 149 distinct leaves**,
with 32,043 literal occurrences. Source 1194 remains the largest unresolved
discovery case at **1.60328 s**, closely followed by new source 1447 at 1.60226 s.
A separate profile of 1194 records 5,763 restrictions, 4,657 simplification checks
and 2,221 propagations. Repeated restriction/proof checking remains a broader
runtime target than subset search alone. Stored state and cold replay remain
substantial, without a lifetime memory bound.

The next structural opportunity reuses **all original checked unit implications**,
including binary-transitive clauses excluded from the current learned batch.
Such a clause can be redundant for propagation yet useful as a subset witness.
The offline [mechanism diagnostic](mechanisms.json) independently replays the
original traces, adds their proved binary consequences, and checks the retained
core. It exposes **eight further 2-CNF leaves**. Existing selected plans for
**1185, 1289 and 1368** could close; 1064, 1120, 1245, 1299 and 1410 retain another
open leaf. These are prospective completions, not measured source gains. Charge
enumeration, indexing, proof transport and cold replay when integrating them.

All **395 Python tests** pass. Three new Lean semantic lemmas prove signed
subsumption, model equivalence and extension on disappearing variables; the full
axiom audit passes **4,129 declarations / 1,971 theorem declarations**. This does
not formally refine Python's encoding, normalization, checker or resource costs.
All three full, three pilot and three previous archives replay byte-identically,
including every alternative and source; warm replay inserts nothing. Each full
mode retains 20,544 ordinary solver residuals. Both new reports have **56 matching
fingerprints**, with separately hashed diagnostic/timing scripts and inputs.

Operation timings include discovery, checking, serialization, persistence,
solving and successful root lifts. Generation, truth tables, summary walks,
compression, initialization and cold replay are excluded or measured separately.
Allocation diagnostics cover six fixed cases and exclude native SQLite, RSS and
the full-corpus peak. Full tests, modes, profiles and timing controls ran
sequentially. These are synthetic discovery experiments, not an industrial solver
comparison, minimum-cost expansion result or efficient partition of arbitrary SAT.
All previous archives remain; storing both policies retains both namespaces.

Reproduce using a new destination:

```sh
python3 experiments/compare_cnf_signed_subsumption.py --output /tmp/new-signed-study
python3 experiments/analyze_cnf_signed_subsumption.py /tmp/new-signed-study
python3 experiments/recheck_cnf_subsumption_timing.py /tmp/new-signed-study
python3 experiments/analyze_cnf_subsumption_pairs.py /tmp/new-signed-study
```
