# Share discovery across several forced binary values

The [live-fallback checkpoint](live-fallback.md) removes one exposed restart loss,
but the dominant partition branch still takes nine expansions. Its saved source
has 125 variables, 57 binary clauses and 261 ternary clauses. The exact seed
excludes the answer and includes only three earlier native rows beyond the
historical prefix.

## The structural opportunity

A complete exploratory reachability census follows the baseline's nine-expansion
trace. At the root, the first-ranked forced value already implies the other three
binary forced values. Adding those three explicitly would be redundant. After
restriction and propagation, a 121-variable residual has two useful groups: the
second-ranked binary variable implies two forced values, while the eighth-ranked
variable implies three others. Neither of these two closures covers the other.
The one-target policy misses both because its first-ranked variable is not forced.

This suggests sharing discovery and conditioning across several consequences.
The census is exposed diagnostic work, not an efficient procedure included in
query timing. Other traced binary subsets are themselves contradictory and are
already handled by the existing whole-subset checker. A contradictory subset's
many implication paths should not be mistaken for new independent deductions.

## Bounded discovery and directional redundancy

The optional recognizer preserves the binary-subset and whole-clause-cover
priorities. It shares their implication graph and completed reachability cache.
It then inspects at most eight variables ranked by binary occurrence count, using
the binary model to choose the only polarity that can be refuted. It retains at
most two source-indexed paths from a literal to its complement.

After finding the first path, it computes the implication closure of the surviving
literal. Later candidates already implied by that survivor are skipped. This is
a directional redundancy filter, not an independence test or a minimum basis:
a later selected value may imply an earlier one. Skipping already covered values
saves redundant path searches, but does not ensure the cheapest continuation.

With source length `L`, binary literal vertices `V_b` and edges `E_b`, recognition
charges source scans, sorting and at most eight cover roots, eight target roots
and one surviving-literal closure. Under expected constant-time dictionary
operations, a comparison/RAM bound is
`O(L + V_b log V_b + 17(V_b + E_b))`. Integer widths and allocation are separate.
Completed paths and misses are local to this exact normalized source. No evidence
is carried into a changed formula merely because variable identifiers coincide.

## Exact joint conditioning with existing proof rules

Every selected original-source path is checked before use. The solver considers
the surviving assignments together, while checking intermediate cofactor caches
before fresh acquisition. A cached positive prefix supplies a lifted source model;
a cached negative prefix avoids deeper acquisition. This prevents a batch from
skipping a previously solved intermediate problem.

If the surviving cofactor is SAT, its model is lifted with the fixed values and
passes the ordinary full-source witness check. If it is UNSAT, the compiler
builds the ordinary native split chain backwards. Each excluded branch is
refuted using the original path's reason clauses, conditioned by earlier surviving
assignments. Satisfied reasons are skipped; remaining reasons are renamed and
looked up in the exact excluded cofactor, then checked as a unit trace. If earlier
conditioning removes a later variable entirely, that redundant split is omitted
only when the live residual identity is unchanged. The original checker validates
every emitted unit certificate and split parent.

There is no new trusted inference or persistent proof format. At most two paths
are selected, but compilation can add excluded nodes and an intermediate parent
outside the ordinary expansion counter. Canonicalization, intermediate lookup,
verification, publication and stored source copies must still be charged. Cold
lookup can recursively check a prior proof graph; it is not a constant-cost oracle.
The native surviving search and unrestricted SAT obligations remain unchanged.

## Frozen comparison

One-target binary frequency, the earlier optional two-target policy and joint
discovery use identical historical seeds and shared partition preparation with
restart. The optional live-fallback change is not included. Six previous edits
become controls, three sign variants expose the saved branch, and six new
fixed-seed nearby edits are generated before timing with roots absent from the
prior union. Fifteen targets, three policies and two opposite serial orders give
90 attempts in 54 workers. Candidate donors/maps and earlier acquisition remain
supplied/sunk; this is not a representative external SAT benchmark.

The joint policy changes discovery breadth and batching together. A separate
posthoc ablation retains the same discovery but consumes only its first
selected path, to distinguish batch effects on the exposed case. It is a count
ablation, not an independent timing comparison. All native deltas, regressions,
compiled parents and alternative payloads are retained and checked.

## Measured result and counterexample

All 15 targets remain UNSAT under all three policies, with matching decisions
across both orders. The comparison adds no whole-input coverage cell. Times below
sum the case streams within each group and average the two orders; bytes are new
native payload, including compiled certificates. These are local measurements,
not expected costs over an external distribution.

| Group | One-target expansions | Joint expansions | Query time, one / joint | New proof bytes, one / joint |
| --- | ---: | ---: | ---: | ---: |
| Original exposed branch | 9 | 4 | 22.54 / 17.11 ms | 114,266 / 85,865 |
| One-variable sign flip | 9 | 4 | 22.58 / 17.09 ms | 114,260 / 85,859 |
| Global complement | 9 | 4 | 22.00 / 16.45 ms | 110,575 / 83,203 |
| Six control edits | 53 | 50 | 162.19 / 164.09 ms | 447,919 / 468,106 |
| Six new edits | 58 | 55 | 179.37 / 186.64 ms | 516,574 / 561,233 |

On the original branch, query time falls **24.10%**, new payload **24.86%** and
checked-object endpoint size **22.61%**. Compressed new proofs fall from **10,250
to 5,877 bytes**. The other sign variants have similar savings. The earlier
two-target policy remains at nine expansions and produces more proof bytes on
all three. The same-discovery single-selected ablation takes **six** expansions
and stores **95,421 bytes**, versus four expansions and 85,865 bytes jointly.
This distinguishes part of the batch benefit from the broader eight-target
search; it does not isolate causal timing, since later residuals differ.

The savings do not transfer uniformly. Controls regress **1.17%** and new edits
**4.05%** in query time, in both order signs. New-edit native payload rises
**8.65%**, compressed deltas **0.75%**, and summed checked-object endpoint bytes
**5.71%**. These retained-object measurements are not peak resident memory.
Full-worker time changes by **+0.21%** on controls and **-0.81%** on new edits;
it includes historical reconstruction, full-history cold audit and measurement
work. Cold-query audit totals dominate those workers and do not establish a
useful general cold-start speedup. All phase measurements remain in `analysis.json`.

The most informative failure is case 61. The new deletion rises from **4 to 7**
expansions and **6.58 to 16.06 ms**. It publishes **11 instead of 4 nodes**, with
payload **24,340 -> 71,373 bytes**. The following replacement still needs only
one expansion, but takes **4.83 -> 9.89 ms**: acquisition has changed which reusable
intermediate proofs exist. Its seven versus fourteen new nodes include compiled
certificates outside the expansion counter. The exact causal role of changed
proof availability still needs a matched-state ablation; the times alone do not
identify it. Both failures are preserved, not removed from aggregate results.

## Next gap: select consequences by their full-CNF continuation cost

A forced binary literal is correct, but may be an expensive way to reach a proof
already available through a different split or propagation sequence. The next
primary question is whether a cheap, source-bound assessment of the surviving
mixed-width cofactor can reject harmful consequence choices without erasing the
case-31 saving. Compare single-selected and joint policies on case 61, preserve
ordinary propagation and cache priorities, and price any assessment, restriction,
proof publication and effect on later queries. Do not use benchmark case IDs or
source-specific thresholds as a general acceptance rule.

The largest new query is still case 31's deletion: **29 -> 23 expansions** and
**84.15 -> 76.14 ms**. Joint branch counts are **[1,4,1,5,1,3]** after the initial
eight expansions. The source-bound posthoc profile records **104 normalizations**
with about **76 ms cumulative** instrumented time and **23 discovery calls** with
about **10 ms cumulative**, inside a 205 ms instrumented query. These nested
times overlap and are not comparative speedups. They suggest that repeated
conditioning/canonicalization and checked proof construction are larger costs
than the bounded graph search in this case. Any reuse must preserve exact source,
assignment and availability bindings plus independent final checking. Earlier
broad cofactor memoization already regressed; use the preserved counterexample
before proposing another global cache.

`next-target.json` retains the exact branch and largest-query sources, profiles,
selected paths and trial bindings. To reconstruct persistent availability, restore
the profile's prefix and add only its `extra_ids` from the bound trial delta;
replay its preceding stream for warm state. The case-61 failure uses the protocol's
`61` prefix and `novel-61-{mode}-0` stream. Never seed from the final union that
already contains these answers. Automatic donors/maps, original-source
recomposition, compact unrestricted summaries and a uniform polynomial bound
remain separate open obligations.

## Validation and persistent checkpoint

Both native readers independently replay **75,896 native records**, all older
affine/binary/equivalence extensions and **282 partition records**. This adds
172 native IDs and 24 partition records while retaining every prior payload.
Sixty alternative-payload observations remain in trial/exploration deltas; the
union keeps older authoritative payloads. The census and single-selected ablation
are independently checked and their new records are merged, not discarded.

All **1,468 full tests** and **176 focused tests** pass. The full suite retains
44 unclosed-SQLite warnings at pre-existing collection sites; focused tests emit
none. Tests include exhaustive small truth comparisons, conditioned path
transport, signed/sparse inputs, cached intermediate SAT and UNSAT, and recovery
after a budget stop. The manuscript builds to **242 pages** without LaTeX warnings;
all 64 preceding proof environments remain byte-identical. This is tested native
compilation, not a new Lean refinement proof.

Resume `experiments/results/cnf-joint-backbone/checkpoint.json`. The sealed ledger
binds **763 source files** and verifies all **11,420 earlier artifacts across 136
manifests** before adding this run. Results, failures, alternative proofs and
source-bound diagnostic paths remain available for subsequent runs.
