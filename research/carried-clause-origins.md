# Carry original-clause provenance through cover extraction

The optional extractor carries the smallest original-clause index for each
residual instead of rebuilding that map from the full source at every proof
node. A source-variable index selects only live representatives affected by
new path assignments. Extracted bundles, hints, decisions and every native
proof payload remain identical to the preceding prepared route.

Local discovery work falls, but total performance does not improve in this
comparison. Cover-phase mean is 8.36% lower, improving in all four pairs.
Preparation plus query is 1.79% higher on average, with two wins and two losses;
complete-worker mean is 6.32% higher. Preserve this negative total-cost result
and keep the route experimental.

## Exact reuse invariant

For a checked canonical source and the current path assignment, the map contains
each distinct unsatisfied residual clause and the minimum original index of a
clause that reduces to it. At the root this follows from canonical order. When
two clauses have the same residual, every extension of the same assignment
affects them identically. Their minimum index is therefore sufficient for all
later transitions. New duplicate images merge by minimum original index,
regardless of dictionary iteration order. Satisfied images disappear.

This proves the invariant by induction over path restrictions. The variable
postings remain valid: every literal in a residual occurred in its retained
original representative. A new assignment can affect only representatives in
those postings. Discarded duplicates cannot later diverge from the retained
representative. The implementation removes changed old images before inserting
new images, so a collision with another old image does not lose provenance.

Component edges keep the global source map, including clauses outside the
selected component. Otherwise a smaller original representative could be lost
when it later coincides with a component clause. Unit and split edges use the
already checked path assignments; every parent-to-child canonical key is still
checked, and leaf assumptions and unit reasons use the existing checker.
Unsupported endpoints and bounded extraction failures remain unresolved.

This uses the same unchanged-clause sharing principle as
[fused preimages](preimage-fusion.md). That helper maps selected child clauses
back to a parent. Here the required map is global to the original source across
the whole path, so directly substituting the parent-subset helper would change
representative selection. No native proof rule or persistent schema changes.

## Costs and limitations

The two cold extractions retain the same seven checked proof-node occurrences
each. Together they index 1,593 source literals and inspect 480 literals in
affected live representatives. There are 260 posting visits, 223 affected
representatives and 2,647 untouched representatives whose clauses are shared.
The old full-source provenance reconstruction charged 11,151 restriction
literal visits; those visits are avoided. These counters describe different
operations and should not be collapsed into one cost-free reduction ratio.

Dictionary snapshots still cost work: 5,740 map slots are copied across the
two extractions. Their peak live origin-map slots are 2,408 and 2,388. These
counts exclude the postings, temporary sets and tuples, integer/key sizes,
allocator overhead and the rest of the solver. A sparse edit can therefore
inspect few clause literals while still copying maps proportional to the
current number of representatives. No whole-process memory saving is claimed.

For L source literals and m clauses, initial indexing is O(L + m) under the usual
unit-cost operation model. An affected transition pays for posting visits,
sorting affected identifiers, inspected residual literals, duplicate handling
and O(m) map copies. Live snapshots can retain O(d m) map entries along proof
depth d, plus postings and shared/shortened clause tuples. Integer bit lengths
and Python hash-table costs remain relevant. No assignment, proof-size or
unrestricted SAT bound follows from this extraction optimization.

## Matched results

Three policies use the same historical prefix, donor, 23 sources and six supplied
guards in four alternating serial orders: 1,656 conditional queries. Each worker
returns 125 UNSAT and 13 SAT answers. Initial static hint extraction is unchanged;
only lazy learned-cover extraction uses the new indexed map. A scoped serial
override is restored afterward and is not intended for overlapping threads.

| Mean per worker | Native baseline | Prepared route | Carried origins |
| --- | ---: | ---: | ---: |
| Preparation + query, seconds | 0.397487 | 0.397843 | 0.404978 |
| Expansion dispatches | 55 | 32 | 32 |
| New native payload, bytes | 1,551,836 | 1,508,442 | 1,508,442 |
| Active hints, bytes | 11,505 | 42,031 | 42,031 |
| Selected retained Python state, bytes | 8,460,643 | 8,348,782 | 8,348,782 |
| Complete worker, seconds | 3.421121 | 3.308544 | 3.517758 |

Preparation/query mean is 1.88% above native baseline. Endpoint retained state
and persisted native/hint bytes are identical between the two reuse routes;
the new index is temporary. Full worker timing includes setup, reconstruction,
checking and persistence, and separate cold hint validation remains recorded.
Local wins do not explain away the whole-stream regressions or authorize a
default-policy change.

| Query | Result | Baseline ms | Prepared ms | Carried ms |
| --- | --- | ---: | ---: | ---: |
| 7 / guard 4 | SAT | 7.992 | 16.062 | 15.678 |
| 15 / guard 3 | UNSAT | 16.054 | 23.088 | 21.758 |
| 19 / guard 3 | UNSAT | 16.896 | 12.732 | 12.821 |
| 20 / guard 3 | UNSAT | 22.014 | 20.122 | 19.405 |

For the first two queries, the cover phase changes from 6.69/6.67 ms to
5.29/4.97 ms. The combined cover phase across all queries changes from 34.83 to
31.92 ms. A separate identical-proof profile counts 1,996 to 15 and 2,048 to 25
generic restriction calls in those cold queries. Normalization calls remain
89 across the four profiled partial queries. Profile overhead prevents using
instrumented wall times as comparative performance measurements.

## Next target

Native acquisition and checking now dominate more of the remaining partial
construction. On case 15, the diagnostic profile attributes about 24 of 62 ms
to normalization and 17 ms to verification; these cumulative times overlap.
All five missing-leaf acquisitions already hold a conditioned formula, variable
map and key in the traversal, then `_visit` normalizes that input again.
Investigate explicit transport of that immutable preparation into the next
consumer, while retaining all source and native certificate checks.

The [previous general canonicalization cache](query-canonicalization-reuse.md)
already lost after charging lookup, validation and memory bookkeeping. Do not
repeat that design merely because fewer normalizations look attractive. Start
with the precise producer/consumer boundary, preserve both SAT and UNSAT
controls, and compare complete cost. Broader guard/map discovery and efficient
acquisition of arbitrary missing leaves remain open.

Eleven new tests compare original representatives over all 4,608 small-source
and partial-assignment combinations, dense and sparse edits, duplicate merges,
branch order, component subsets, exact extracted bundles, unsupported endpoints
and budget failures. The validator independently compares eight extracted
bundles across four repeats. Raw regressions, profiles and source bindings are
preserved in `experiments/results/cnf-carried-origins/`.

Validation passes 1,590 full tests and 111 focused tests. Both readers audit all
1,656 comparative queries, 76,501 cumulative native records, unchanged extension
tables and 342 prior partition records. No native identities or authoritative
payloads change. All 13,095 prior artifacts across 148 manifests remain intact;
the seal binds 845 source files. The full suite retains 44 unclosed-SQLite
warnings, with none in the focused suite. The manuscript builds to 248 pages
without LaTeX/layout warnings and preserves its 64 proof environments.
