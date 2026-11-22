# Select binary consequences beyond the next split variable

The previous probe/partition study isolated a branch costing 61 native expansions.
Its exact pre-branch archive contains no answer for the branch. The formula has
125 variables and 326 clauses: 58 binary and 268 ternary, in one connected
component. Unit propagation assigns nothing. Its binary implication graph has no
nontrivial strongly connected component, but it still forces two signed literals,
`-50` and `117`, in the normalized variable names. Acyclic implication structure
therefore does not mean an absence of useful consequences.

The existing eight-root whole-clause search finds neither literal. The following
targeted search checks the variable with highest total occurrence count, breaking
ties by identifier; that variable is not binary-forced. The missed opportunity is
selection of a consequence, rather than a missing proof rule. The unrestricted
read-only census and separate binary counterchecks are saved in `inspection.json`.
They motivated the experiment and are excluded from comparative query timing.

## Two bounded alternatives

The new experimental recognizer preserves the preceding whole-cover phase exactly
and changes only the final target selection. `total4` examines at most the first
four variables by total occurrence count. `binary1` examines only the variable
with highest binary-clause occurrence count. Both break ties by identifier. On
the exposed branch, these choices discover `117` and `-50`, respectively.

For each candidate present in the binary core, a binary model rules out one
forced-false polarity. The recognizer searches from the other polarity to its
negation. An implication path is supported by source clauses and independently
checked. It refutes exactly the excluded assignment; the surviving cofactor must
still be solved. A native negative split combines both checked children, while a
positive child must lift to a full source witness. No path, a skipped candidate,
or exhausted discovery allowance is not a SAT or UNSAT verdict.

The graph and completed reachability searches are shared with whole-cover
discovery. Failed completed searches are reusable; skipped searches are not
cached as failures. The existing native excluded-child compiler and both proof
readers remain unchanged. This is established implication reasoning with a
different bounded ranking, not a new tractable SAT class.

For literal count `L`, variable count `V`, and binary graph size `V_B + E_B`,
the added ranking costs `O(L + V log V)` because this implementation sorts its
candidate counts. At most four extra breadth-first searches cost
`O(4(V_B + E_B))`; binary-only ranking requests one. The graph and bounded set of
paths require `O(V + V_B + E_B)` temporary space for fixed limits. Restriction,
canonicalization, recursive solving, certificate checking and persistence remain
additional costs. Neither consequence discovery nor variable elimination bounds
the size of the surviving search or stored proof.

## Comparison and preservation

The comparison freezes three policies and two opposite serial orders before any
timed solving. It includes the isolated branch, nine earlier residual targets, and
six new neighbouring edits generated with a fixed seed. Each new root is absent
from the preceding cumulative archive. The isolated branch uses its exact saved
prefix plus five pre-branch publications. Other trials restore the same cold seeds
as the preceding study. No later branch answer is imported.

All policies use the same probe/partition wrapper except the isolated native-only
diagnostic. Probe and branches share 256 native expansions; the eight-expansion
probe is included. The only changed component is native target ranking. The
general affine solver remains the baseline outside this experimental adapter.
Candidate donors and variable maps are still supplied. These local residual edits
do not establish automatic source-level coverage or external-benchmark gains.

The inherited measurement worker charges preparation, checking, publication,
serialization, persistence, warm reuse, full cold replay and reconstruction.
Complete-worker time also includes measurement and audit overhead. Endpoints sum
separate process states and are not peak memory bounds. The cumulative union
preserves prior authoritative payloads, and alternate valid proofs remain in the
individual trial deltas. Every earlier source and artifact stays hash-bound.

The policy replacement is scoped inside one serial experimental process. It is
not a thread-safe solver API and changes no default. The new source keeps the
old whole-cover implementation intact because prior source fingerprints are part
of the persistent evidence. Validation checks that copied portion byte-for-byte.

## Results and the routing counterexample

Every policy returns UNSAT on all 16 targets (96 attempts in 60 workers).
Decision coverage is unchanged. The table gives mean summed stream costs over
two opposite orders; the isolated branch is one separate diagnostic.

| Stream | Original expansions | Four total-frequency targets | One binary-frequency target | Original query seconds | Binary-frequency query seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Exposed boundary (3 targets) | 32 | 27 | 27 | 0.09745 | 0.09903 |
| Earlier edits (6 targets) | 122 | 106 | 88 | 0.35414 | 0.24951 |
| Isolated exposed branch | 61 | 25 | 9 | 0.14052 | 0.02580 |
| New edits (6 targets) | 107 | 67 | 51 | 0.35625 | 0.18101 |

Binary-frequency targeting reduces query time **81.64% on the isolated branch,
29.54% on the earlier edits, and 49.19% on new edits**, with both paired orders
favourable in each case. It regresses **1.63% on the exposed boundary** on average,
with mixed paired signs despite five fewer expansions. Four total-frequency
targets also reduce the expensive branch and both edit streams, but cost more
than the binary-frequency policy there. No policy dominates every input.

The important regression is the earlier case-31 replacement. Its total acquisition
rises **28 -> 53 / 51** for total-frequency / binary-frequency ranking. One of its
first-false branches rises **10 -> 35 / 33**. The preceding deletion improves
**86 -> 45 / 29**, so the two-query stream still improves **114 -> 98 / 80**.
The new case-31 deletion likewise improves **85 -> 45 / 29**, while its following
replacement remains at 14 expansions. The four other new queries remain cheap.

The read-only dependency audit rejects one tempting explanation for the
regression. The single previous-query proof used by the original replacement is
still available after binary-frequency acquisition, and all three policies reuse
it in the first, cheap branch. The expensive third branch's final proof has no
seed or previous-query dependencies under any policy. A smaller preceding archive
therefore does not by itself explain the extra work. Final proof reachability
does not capture every visited search state, so a controlled comparison from an
identical pre-branch state is still required to isolate routing effects.

| Cost | Exposed branch: original -> binary | New edits: original -> binary |
| --- | ---: | ---: |
| Complete measured seconds | 6.54320 -> 6.36469 | 24.97835 -> 24.32241 |
| New native key/payload bytes | 708,685 -> 126,937 | 1,123,355 -> 466,555 |
| Endpoint checked-object bytes | 2,978,070 -> 573,101 | 5,805,395 -> 3,038,216 |
| Endpoint SQLite bytes | 48,840,704 -> 47,910,912 | 189,431,808 -> 188,379,136 |
| Compressed delta plus raw sidecars | 50,394 -> 12,253 | 199,383 -> 149,999 |

The new-edit complete-time reduction is **2.63%**, favourable in both orders,
compared with the much larger acquisition reduction. Earlier-edit complete time
changes only **0.12%**, with mixed signs; the exposed boundary regresses **0.44%**.
The isolated branch's full cold replay is slightly slower despite fewer new
records. Warm reuse does not consistently improve: boundary setup plus lookup
rises from about 0.01167 to 0.01621 seconds. The prefix dominates retained storage
and replay, while raw partition sidecars are unchanged. These two-order
measurements do not establish broad or stable end-to-end performance bounds.

## Next gap and validation

Prioritize **reuse-aware choice among binary consequences**, using the replacement
branch that costs 10 under the original policy and 33 under binary-frequency
ranking. `next-target.json` binds the exact source and persistent state before
that branch: the common prefix plus 35 records from the preceding query and this
query's probe, preparation and completed branches. Its root is absent. The
diagnostic checks the retained prerequisites without search or publication.
Compare policies from that identical state before adding a new gate. Investigate
whether cheaply recognized cofactor structure predicts when a different forced
variable helps; neither occurrence ranking nor consequence existence guarantees
the cheapest continuation.

Keep the binary-frequency policy optional. Automatic donor/map retrieval,
source-level composition, compact sidecar storage and arbitrary wide-clause
interaction remain open. The results improve native acquisition within a supplied
residual partition; they add no whole-source coverage theorem or polynomial
unrestricted-SAT bound.

Resume `experiments/results/cnf-ranked-binary-targets/checkpoint.json`. All
**1,394 full and 76 focused tests pass**, including exhaustive truth-table checks
of 512 small mixtures, native SAT/UNSAT lifting, tampered-path rejection and cold
replay with both readers. There are 44 existing full-suite SQLite warnings and
none in the focused tests. The independent audit checks 96 chronological attempts,
30 new partition sidecars and 60 preceding sidecars. Both readers replay the
cumulative authority: **74,879 native records**, plus unchanged affine,
equivalence and binary-discovery records. The archive adds 362 unique native
records across all policies; 70 alternate-payload observations remain in trial
deltas. All 696 prior sources and 9,192 artifacts in 128 manifests are unchanged.
Older unrelated composed/inventory audits remain bound to the previous validation.

The manuscript builds to 237 pages without warnings. All 64 existing proof
blocks remain unchanged. The final source ledger contains 703 files.
