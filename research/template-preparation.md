# Share source-bound template preparation within a query

The 23 November experiment removes the 71 repeated template checks and full
cofactor constructions identified by the preceding profile. A synchronous
operation copies the source into immutable clause tuples, validates the guard,
restricts and canonicalizes once, checks the existing answer, and tests the
template once if needed. A hit builds the same native unit or empty proof using
the already computed cofactor and variable-name map. A miss carries that target
to the existing pools and native fallback. All native proof checks remain.

The preparation is descriptive data returned to that caller, not a certificate
accepted by another publisher. No external canonical target is trusted and no
cross-query cache is introduced. The source snapshot and guard are local to the
call; later input mutation cannot change them. Conditional assumptions must
still be extended by the query guard. Cached native answers remain sufficient
without another template check. The inherited matching interface excludes
tautological source clauses; this experiment does not expand that interface.

## Matched costs

Both policies restore the same historical prefix, acquire the same donor in
nine expansions, and prepare the same compact hints. The nineteen preceding
sources each receive the same six supplied guards. Four paired repeats alternate
serial process order, yielding 912 comparative attempts. An additional 114
query-only profiled attempts are excluded from the means. Guard, donor and
variable correspondence discovery remain supplied, not free accomplishments.

| Quantity per worker | Repeated preparation | Shared preparation |
|---|---:|---:|
| Preparation + query mean | 377.28 ms | 323.13 ms |
| Query mean | 364.42 ms | 310.50 ms |
| Complete-worker mean | 3.056 s | 3.083 s |
| Template checks | 173 | 102 |
| Restriction literal visits | 216,720 | 154,153 |
| Normalization literal visits | 221,946 | 162,778 |
| Database lookups | 263 | 192 |
| Native verification literal payload | 109,760 | 109,760 |
| Query expansion dispatches | 43 | 43 |
| Native payload bytes | 1,237,109 | 1,237,109 |
| Compressed proof delta + hints | 126,657 bytes | 126,657 bytes |
| Selected retained Python containers | 6,847,167 bytes | 6,847,167 bytes |

Preparation plus query falls **14.35%** locally and query time falls **14.80%**.
Each of the four pairs favors sharing on those measures. The ninety earlier
controls improve 16.87% in query time and the twenty-four preceding additional
queries improve 9.42%. The 71 template-hit queries fall from 197.05 to 141.53 ms
in total; the other routes gain nothing and show small overhead/noise. All proof
bytes, chronological additions, routes and answers are identical, including to
the previous checkpoint. There are 103 UNSAT and eleven SAT cofactor answers per
worker, twelve cached roots, eight negative-pool hits, four witness-pool hits and
nineteen native fallbacks.

Complete-worker time is slightly higher, so there is **no end-to-end gain in
these measurements**. That timer also includes frozen-source hashing, restored
state, donor construction, preparation, checking, serialization, persistence,
warm reads, cold answer replay and reconstruction. Hint reload is audited
separately. Four alternating pairs do not establish an external benchmark result
or eliminate environmental noise. This remains an experimental adapter.

The snapshot copies 95,244 literal references in 33,750 clauses across all 114
queries, including misses and cached roots. It retains temporary space of
O(m + L + g) for source clause count m, source literal occurrences L and guard
size g; sorting the guard costs O(g log g). Native full-target serialization and
verification remain charged. The retained container endpoint excludes temporary
state, sets and native allocations. Whole-worker RSS is recorded but does not
isolate this allocation. There is no claimed peak-memory or storage reduction.

All measured identities already occur in the previous cumulative archive. The
new checkpoint references that same immutable archive instead of storing another
copy. No previous authoritative record or alternative proof is replaced.

## Next target: supports across nearby native fallbacks

The profile still includes 164 native publications and 109,760 verification
literals. Normalization, native acquisition and publication overlap in cumulative
time; saving a constructor does not remove the full proof obligation. Across the
uninstrumented shared runs, template routes cost 141.53 ms and the nineteen
native fallbacks cost 128.32 ms. The next structural question is whether learned
conditional supports can avoid some of that acquisition on related edits.

Five UNSAT queries account for 72.21 ms, **56.28% of native-fallback time**, and
22 of 43 expansion dispatches:

| Source case | Template / guard | Query mean | Expansions |
|---|---:|---:|---:|
| 4, delete-reason-2 | 3 | 13.12 ms | 4 |
| 4, delete-reason-2 | 4 | 14.50 ms | 5 |
| 15, pool-additional-4-0 | 3 | 16.83 ms | 4 |
| 16, pool-additional-4-1 | 3 | 13.65 ms | 4 |
| 16, pool-additional-4-1 | 4 | 14.11 ms | 5 |

Cases 15 and 16 delete two more clauses from case 4. Study which source-bound
conditional reasons learned at the earlier case survive those edits. Current
early core reuse already runs and misses here, so a proposed support bank must
beat that baseline. Preserve every branch assumption and exact variable map;
do not treat a negative cofactor as a full-source refutation. The nearby case
7 / guard 4 is SAT and takes six expansions; retain it as an adversarial control.
`next-target.json` binds the queries, sources, earlier available identities and
cost ranking. Any useful transfer must use only earlier stream results and
charge extraction, matching, full recomposition, storage and cold verification.

This checkpoint improves construction within existing routes. It adds no new
whole-input coverage cell, automatic category partition, efficient arbitrary-CNF
algorithm, polynomial closure bound, or Lean theorem.

## Reproduction and checks

Implementation: `experiments/cnf_template_preparation.py`. The paired comparison,
profile and validator are separate source-bound scripts. Resume from
`experiments/results/cnf-template-preparation/checkpoint.json`.

Eleven targeted tests include all 256 deletions of a three-variable clause cube
under the extracted guards, sparse signed maps, stronger/missing assumptions,
duplicate clauses, source mutation, constants, invalid proof rejection and both
cold readers. An initial fixture included a tautology excluded by the inherited
interface; its source and failure log are retained, and rejection is now tested
explicitly. This did not require a solver change.

The full suite passes 1,539 tests; the focused preparation, pool and conditional
support suite passes 31. All 1,026 comparative/profile queries are audited.
Both independent readers replay 76,429 cumulative native records, the unchanged
extension tables and all 342 preceding partition records. All 12,684 older
artifacts across 143 manifests remain unchanged; the new seal binds 816 source
files. The full suite retains 44 unclosed-SQLite resource warnings, with none in
the focused suite. The 246-page manuscript builds without LaTeX/layout warnings
and preserves all 64 previous proof environments.
