# Skip probes that cannot start unit propagation

The optional selector now builds binary-clause incidence from the residual after
its existing, complete unit-propagation pass. For each unassigned variable in
the original candidate prefix, it omits both assumptions if that variable occurs
in no residual binary clause. Assigning such a variable cannot create another
unit or an empty clause. This excludes that single-assumption unit refutation;
it does not decide SAT, exclude a deeper refutation or guarantee cheap solving.

The implementation preserves original variable ranking, both-polarity order and
the candidate cap. Skipped candidates are not replaced by later ones. Every
successful prior proposal therefore remains available at the same position in
the original prefix. The attempt index changes when unsuccessful screens are
omitted, and the new trace records the skipped assumptions explicitly. The
existing forced-prefix fallback and checked positive-model recovery remain in
place. The module is an optional experimental policy, not a change to the native
solver's default acquisition path.

## Scope and correctness

The filter must inspect the propagated residual and only unassigned variables.
The saved counterexample `(a) AND (NOT a OR b OR c) AND (NOT a OR b OR NOT c)`
has no original binary clause but exposes two after propagation; `NOT b` is
unit-refuted. Tests also cover arbitrary source-coordinate renaming, polarity
reversal, disabled native leaves, known residuals and targets, candidate caps,
empty/tautological sources, and an unsatisfiable formula whose every single
assumption is correctly skipped. Across 1,024 clause subsets and two
representations, all 2,048 selected results match the previous selector.

The independent checker reconstructs the old screens, derives the residual
without calling the new filter and verifies that each omitted assumption leaves
only clauses of length at least two. It checks the selected proposal, compact
trace, all native/composed certificates and chronological archive availability.
No new native proof schema or Lean refinement of the Python program is claimed.

For a unit-closed residual with m clauses and B binary-literal occurrences,
incidence construction costs O(m+B) expected set operations. The trace also
sorts b distinct source names, costing O(b log(b+1)) comparisons. Membership
checks and skip recording add O(k) expected operations. Additional live
state is O(b+k) words for the incidence set and at most 2k skip records, for the
existing candidate cap k. Literal/name bit lengths and JSON serialization remain
charged. These costs are additional to normalization, the existing baseline unit
pass and original ranking. The native remaining search and retained proof DAG
keep their previous unrestricted costs.

## Matched evidence

Twenty-six exact-prefix arms revisit thirteen earlier contexts under previous
and filtered policies. All selected results, native payloads and composed
records are identical, including useful guards 43/172, regression 144, positive
model recovery 146 and unresolved 0/131/159. No probe can be skipped in these
controls: both use 21 probes and 38,189 propagation visits, adding 83 native rows
and 113,439 native bytes across the isolated arms. The filter additionally scans
684 residual clauses and 608 binary literals and transports 242 names. Equal
delta/record storage does not imply free filtering: the full reports retain the
extra incidence data and counters (727,547 -> 737,707 report bytes), and
measured evaluation includes that work.
Single-arm timing differences do not establish a speedup.

The fresh corpus contains 48 further excluded inputs from four finite generators
and twelve additional neighbours of the old templates. All 48 new-family targets
and one neighbour remain unfamiliar after preparation. Eleven neighbour targets
are known. Generation/selection costs 1.572 seconds separately. Six workers run
baseline/previous/filtered and the reverse order without concurrent tests or
profiles. Every mode answers **43 SAT / 17 UNSAT** and adds identical
**450 native rows / 521,286 native bytes**. Ten rows arise in ordinary preparation,
none in near-guard preparation, and 440 in acquisition. Optional policies reuse
one unit prefix: 439 expansion calls plus one explicit trace publication.
Baseline has 440 expansion calls. Warm replay adds no rows.

| Measure | Native baseline | Previous policy | Binary filter |
| --- | ---: | ---: | ---: |
| Premise probes | 0 | 386 | 194 |
| Structurally skipped probes | 0 | 0 | 192 |
| Discovery/acquisition propagation visits | 69,351 | 252,999 | 179,463 |
| Native rows added | 450 | 450 | 450 |
| Mean query time, seconds | 0.371 | 0.472 | 0.458 |
| Mean complete worker time, seconds | 21.567 | 21.947 | 22.234 |
| Query/warm sidecars, MB | 1.173 | 2.346 | 1.991 |

The filter eliminates 96 probes on random 3-CNF and 96 on coupled parity, saving
**73,536 propagation visits (29.07% of previous discovery/acquisition work)**.
All selections and native payloads remain identical. It scans 3,020 residual
clauses, 1,252 binary literals and transports 287 source names. Query/warm
sidecars shrink **15.13%** because compact skips replace repeated source-bound
screens. These are trace-storage savings, not native proof or process-memory
savings. Gated Horn and graph-colouring inputs retain all their probes.

The query-time differences are **-0.0414/+0.0134 seconds** in opposite orders.
Complete-time differences are **+0.0850/+0.4891 seconds**. Therefore the measured
work reduction does not establish a stable query or end-to-end speedup. Complete
worker means actually regress, with higher setup time in the filtered runs.
Cold replay remains dominant at 10.658/10.806/10.802 seconds; setup is
4.324/4.405/4.674, compression 3.903/3.905/3.920, and warm-bank setup
1.949/1.990/1.998. Mean process RSS is approximately 716/694/713 MB, including
inherited state. All trial databases occupy 75,649,024 bytes and compress to
5,474,412 bytes. Native baseline still has substantially lower acquisition work.

The 48 new-family formulas are checked by independent exhaustive bitset truth
tables after timing. This exponential validator is not part of the solver.
The twelve larger neighbours use native and composed certificates. Four finite
generators and a few small size settings establish neither a general partition
of SAT nor a scaling law. Prior failed screens and counterexamples stay intact.

## Remaining gaps

The user's reduction suggestion gives the right reuse criterion: search for a
cheap, certified transformation whose target is already acquired or tractable,
then price construction, target recognition, answering and witness/proof
transport. A polynomial SAT-to-SAT encoding change alone need not make its
target easier or present in the archive. A uniformly polynomial reduction of
every CNF to a polynomial-time decidable class would give P=NP by composition;
expensive offline compilation instead supports a different, online cost claim.
[Darwiche and Marquis (2002)](https://www.cril.univ-artois.fr/~marquis/darwiche-marquis-jair02.pdf)
separate representation size from supported polynomial queries/transformations.

Conditioning is cheap for a specified assignment but is not generally an
equisatisfiable reduction to one branch. A model lifts to the source; one
negative branch does not refute it. A supplied k-variable strong backdoor can
require 2^k residual queries, while discovering the backdoor must also be charged.
[Williams, Gomes and Selman (2003)](https://www.cs.cornell.edu/gomes/MYPAPERS/backdoor-ijcai03.pdf)
provide the original backdoor framework. These primary sources were rechecked
for the user's question. The following saved residuals make this direction
concrete without asserting that useful reduction paths exist cheaply for all CNFs.

The strongest new reuse target is a discarded positive result. Across the old
saved premise screens, 89 conditioned residuals in 20 queries are syntactically
constant, Horn, dual-Horn or two-CNF: 61 in all twelve gated Horn queries and
28 in eight graph-colouring queries. These are recognition observations, not
89 new SAT decisions. A family result still needs acquisition and exact
recomposition; one refuted branch does not refute its parent.

In **case 50**, assumption `-169` already leaves an empty residual. Independent
transport of its saved unit assignments verifies a complete target model, saved
in `attribution.json`. The current policy overlooks it because premise probing
only selects unit conflicts, then acquires three native rows / 2,503 bytes.
Next, recover and verify positive premise models before discarding the probe,
and price direct target publication at this exact prefix. Extend to recognized
conditioned families only with checked model lifting or negative certificates
and measured recognition/acquisition costs. No alternate acquisition or runtime
saving for case 50 has yet been measured. A filter safe for *unit-refutation*
discovery must not be treated as excluding useful positive witnesses.

The binary-variable condition is sufficient but coarse. An assumption can start
another unit deduction only if a residual binary clause contains its *falsified*
literal. A binary clause containing only its satisfied polarity disappears.
The posthoc audit finds **83 of the remaining 194 probes** with no such falsified
binary occurrence: 35 in gated Horn inputs and 48 in graph colouring. Replaying
those saved screens accounts for **28,774 propagation visits**. Extend the
incidence summary to signed literals, retain the existing candidate prefix and
price this refinement against both current policies. It is not implemented or
timed in this checkpoint. The residual must remain consistent and unit-closed,
and the assumed variable unassigned.

Gated Horn inputs still spend 75,825 discovery propagation visits versus 6,572
in native acquisition. Random 3-CNF and coupled parity contribute 279 of 432
new-family acquisition rows and 45,877 of 66,607 new-family acquisition visits;
they remain the larger fresh-search targets for mixed-family decomposition and
affine/leftover reuse. Preserve the earlier expensive cases as exact-prefix
controls. Binary filtering alone does not discover these decompositions or avoid
native acquisition. Shared checking, source references and persistence remain
necessary targets because inherited replay dominates complete runtime.

The reproduced study and persistent checkpoint are in
[the experiment record](../experiments/results/cnf-binary-probe/README.md).

All **1,113 tests**, 24 focused tests and independent reconstruction pass.
Resume `experiments/results/cnf-binary-probe/checkpoint.json`: **23,577 native
keys**, all 23,127 earlier payloads, **206 new composed records**, 3,165 earlier
composed records, 2,957 ordinary decisions and six projections. No alternate
payloads are needed. The union occupies 75,649,024 database bytes / 5,474,412
compressed bytes. Ready/pending banks remain 132/38, 141/66, 86/90 and 86/117.
Prior 503 sources / 5,655 artifacts / 94 manifests, structural authorities and
all 64 manuscript proof blocks remain unchanged. The 211-page paper builds
without overfull or undefined warnings. No new Lean theorem or unrestricted-SAT
resource bound is claimed.
