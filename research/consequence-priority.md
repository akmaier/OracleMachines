# Give a checked full-CNF cofactor priority over one late consequence

The [joint-consequence study](joint-binary-consequences.md) improves one exposed
branch but makes a case-61 deletion slower. Correct forced values can still lead
to expensive continuations and different intermediate proofs. This study follows
that counterexample with exact historical seeds, without changing earlier kernels
or solver defaults.

## What the failure reveals

A source-bound diagnostic replays the two case-61 queries under the original
one-target policy, broader discovery consuming one selected path, and joint
conditioning. The first query takes **4, 8 and 7 expansions**, respectively. The
second takes one under all three. Baseline and joint emitted bytes match their
preceding frozen trials. The single-selected ablation is exposed diagnostic work,
not an independent performance sample; its new proofs are retained and checked.

At the first 65-variable residual, broader discovery finds one binary forced
value at rank four. Its variable is 17. The ordinary full-frequency split chooses
46: setting it false gives a full-CNF unit refutation, while setting it true
propagates seventeen values. Neither child was already in the database at the
observation point. The following replacement has a similar rank-three consequence.
In the slower continuations, a 62-variable residual offers two binary consequences;
consuming them jointly saves one expansion relative to consuming just one. Thus
batching is not the initial cause of this regression: wider discovery displaced
a useful ordinary full-CNF branch.

These variable numbers are local diagnostic coordinates, never recognition rules.
The preliminary driver also retained its corrected reporting error: an early
version expected a wrapper-added root field in the raw query result. No kernel
or proof-checking behavior changed, and the final diagnostic records bind the
corrected script and exact native outputs.

## A bounded arbitration rule

Keep the preceding binary-subset refutation and whole-clause-cover priorities.
Use the same eight-target discovery and at most two selected paths. If there are
two selected paths, retain joint conditioning. If the single selected variable
is already first in binary-frequency order, retain the preceding policy too.
Only a **single later consequence** opens the new arbitration step.

Rank the ordinary candidate by full-CNF frequency, with the existing identifier
tie break. If it differs from the selected consequence and the source has at most
256 variables, 4,096 clauses and 16,384 literal occurrences, call the existing
cofactor probe on false then true, stopping at the first checked refutation.
That probe can reuse a checked negative child or produce a checked unit trace.
A failed probe gives no SAT/UNSAT answer. If neither succeeds, use the original
selected consequence. A success chooses the surviving ordinary cofactor and
combines it with the excluded child's native certificate. A surviving model is
lifted and checked on the original source.

This is a heuristic choice of which established certificate to seek first, not
a theorem that a cheap refutation yields the cheapest continuation. It reuses the
[two-polarity cofactor mechanism](bipolar-routing.md); the new contribution here is
its narrow arbitration trigger and measured interaction with broader discovery.
It adds no inference rule, trust assumption or persistent proof format. The earlier
bipolar guard had mixed total-cost results, so all new misses and regressions
remain part of this comparison.

## Resource and validity conditions

Selected binary paths remain bound to the exact normalized source. Every preferred
cofactor is restricted, normalized and read through the ordinary checked cache;
a newly compiled negative unit proof passes the unchanged native checker before
publication. The parent split is checked too. No stale coordinate map or previous
formula's reachability information grants authority. No speculative cofactor or
unfinished native frame is stored as an answer. A later budget stop retains only
completed checked records.

The extra ranking scans are linear in source length `L` under the stated RAM
assumptions. At most two cofactors are examined. The inherited repeated-scan unit
propagator costs `O((V+1)L)` per probe, not linear time. Restriction, normalization,
key construction, cache lookup and proof verification remain additional charges;
reading a cached proof can recursively verify its prerequisites. Temporary child
and unit-trace data are `O(L+V)` machine words apart from integer width and Python
allocation overhead. The checked cache and persistent archive have separate
growth. The fixed size guard bounds this optional probe, not surviving native
search on arbitrary SAT.

A compiled excluded child need not increment the ordinary expansion counter.
Publication counts and payload bytes therefore matter alongside expansion counts.
A successful probe may still select an expensive surviving branch or change which
proofs a later query can reuse. The current rule promises neither minimum total
work nor a polynomial unrestricted-SAT procedure.

## Frozen comparison

Three modes use the same seeds: one-target binary frequency, the preceding joint
policy, and joint discovery with the new priority rule. Six preceding new edits
become controls; the original exposed branch and its two sign variants remain;
six fixed-seed nearby edits have roots absent from the preceding union. Fifteen
targets and two opposite serial orders give 90 attempts across 54 workers.
Preparation, recognition, publication, retained space, warm/cold replay and worker
overhead are measured. Supplied donors/maps and historical acquisition remain
sunk. Serial timing finishes before profiles or cumulative audits. This local
residual experiment is not a representative external SAT benchmark.

## Result: recover the failure without losing the joint benefit

All 15 targets remain UNSAT under all policies and both orders. Every target
already closed under the baseline, so this is an acquisition-policy improvement,
not a new whole-input coverage cell. The table sums streams within each group and
averages the two orders; payload includes compiled native nodes.

| Group / policy | Expansions | Query time | New native payload |
| --- | ---: | ---: | ---: |
| Six controls / one-target | 58 | 173.21 ms | 516,574 bytes |
| Six controls / joint | 55 | 182.61 ms | 561,233 bytes |
| Six controls / priority | 51 | 174.60 ms | 524,167 bytes |
| Six new edits / one-target | 71 | 203.02 ms | 652,631 bytes |
| Six new edits / joint | 63 | 205.56 ms | 653,601 bytes |
| Six new edits / priority | 57 | 196.23 ms | 628,044 bytes |

Against joint conditioning, priority saves **4.39% query time and 6.60% native
payload on controls**, and **4.54% time and 3.91% payload on new edits**. Both
query-order signs improve. Against the original one-target baseline, new edits
improve **3.34%** in time and **3.77%** in payload, but controls still regress
**0.80%** in time and **1.47%** in payload. General defaults remain unchanged.

The exposed original branch and two sign variants retain four expansions and
exactly the joint policy's native delta bytes. Original-branch time is **22.43 /
17.18 / 17.25 ms** under one-target / joint / priority. Its guard does no cofactor
probe: one first-ranked selection and one pair of consequences bypass it. Extra
ranking/checking still has a cost; small timing differences against joint have
mixed order signs.

On the case-61 control deletion, the three policies take **4 / 7 / 3 expansions**
and **6.33 / 16.42 / 6.16 ms**. Priority restores exactly the baseline's native
proof bytes across both case-61 queries. Its reduction from four to three counts
reflects compiling a unit refutation instead of visiting that child; it does not
remove a proof node. The following replacement is **4.66 / 9.46 / 5.03 ms**.
The corresponding new deletion is **6.47 / 16.14 / 6.58 ms** and its replacement
**4.76 / 9.85 / 4.96 ms**, again with baseline-identical native deltas. The remaining
small regression versus the baseline shows that broader discovery and arbitration
still have costs even after recovering the useful continuation.

Priority makes three arbitration selections on controls and five on new edits;
every eligible candidate here yields a checked cofactor. These local successes
are not a general hit-rate bound. New edits publish **80 nodes**, versus 91 under
joint and 82 under one-target. Summed checked-object endpoint size falls **2.09%**
versus joint and **1.97%** versus baseline; it is not peak resident memory. New-edit
compressed deltas rise **1.71%** versus joint despite smaller raw payload, while
falling **9.67%** versus baseline. Compression and raw proof savings differ.

Complete-worker means on new edits improve **0.36% versus joint** and **1.44%
versus baseline**. Controls worsen **0.33% versus joint** and improve **0.53% in
mean versus baseline**, with mixed order signs for the latter. Workers include
full-history cold replay and reconstruction, which dominate query time. All phase
measurements and individual regressions remain in `analysis.json`; this is not a
general deployment speedup or a peak-memory guarantee.

## Next structural bottleneck and exact resume point

The largest new priority query is case 31's replacement. Its counts are **32 /
27 / 25** and times **98.42 / 91.25 / 94.12 ms** under one-target / joint /
priority. Priority is **3.15% slower than joint** there despite fewer expansions.
It uses eight probe expansions, then branches **[1,4,1,6,1,4]**. The profile exposes
**142 normalizations**, **6,353 restriction calls**, seven negative-reuse calls
and 26 causal preimage calls. Instrumented cumulative times are roughly **101 ms
normalizing**, **42 ms in causal preimage extraction**, within a **256 ms** query;
these nested costs overlap and are not comparative timing estimates.

The next target is repeated source-bound preparation and causal support extraction
around the remaining six-expansion branch. Determine which exact conditioned
clauses, propagated reasons or support descriptions recur before adding another
recognizer. Reuse must preserve the original source, assignment, dependency and
availability checks. Earlier broad normalization/cofactor memos already failed
total-cost tests; consult those records rather than repeating them. A smaller
expansion count alone is insufficient, as this replacement demonstrates.

In `next-target.json`, the `novel` observation at query position **1** contains
acquisition index **4**: **125 variables, 257 ternary clauses, 60 binary clauses,
one unit clause and 892 literal occurrences**, with **242 expansions remaining**.
Restore its bound prefix plus its **42 earlier native IDs** from the observation's
bound trial delta. Its root was absent. The source and earlier IDs reconstruct
persistent availability; replay the stream for warm pools. Do not seed from the
final union containing the answers. Completed and budget-stopped observation
frames are distinguished; an unfinished continuation is not a rejected candidate
or proof. The diagnostic reporting correction is retained separately from all
frozen timings.

Automatic donor/map discovery, source-level recomposition, compact summaries for
unrestricted interactions and a uniform polynomial expansion bound remain open.

## Validation and persistence

Both native readers replay **76,003 native records**, all earlier affine,
binary and equivalence extensions, and **306 partition records**. The checkpoint
adds 107 native IDs and 24 partition records. All earlier payloads remain
unchanged; 80 alternative-payload observations are retained in trial and diagnostic
deltas instead of replacing prior authority. The single-selected diagnostic
proofs are included in the cumulative merge.

All **1,478 full tests** and **186 focused tests** pass, including truth-table
comparisons on 192 small mixed CNFs, signed/sparse sources, both cofactor polarities,
inconclusive probes, size limits, prior negative evidence and budget-stop recovery.
The full suite emits 43 unclosed-SQLite warnings; focused tests emit none. Warning
collection sites do not establish allocation sites. The manuscript builds to
**243 pages** without LaTeX warnings and retains all 64 earlier proof environments
byte for byte. No new Lean refinement theorem is claimed.

Resume `experiments/results/cnf-consequence-priority/checkpoint.json`. Its sealed
ledger binds **771 source files**, verifies **11,721 earlier artifacts across
137 manifests**, and retains the corrected diagnostic reporting failures alongside
the final profiles and evidence. The benchmark sources and policies were frozen
before comparative timing; subsequent diagnostic reporting fixes changed neither
kernel behavior nor timed samples.
