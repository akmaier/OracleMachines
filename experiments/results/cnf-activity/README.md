# Checked activity and novel continuation variables

9 November 2026. The optional `ActivityLearningInventory` combines original-core
probes whose closure can change under the selected learned batch with variables
newly ranked by the existing continuation. It retains the existing two probe
phases and per-residual cap; there is no additional pass or inherited hint context.

## Recognition and checking

The original pass must be complete and clear before the selector runs. The
ordinary checker validates its deterministic assumptions, every unit/conflict
reason, absence of common/equivalence reductions, and the exact selected batch.
For each original variable it tests both closures against that batch. A pair is
inactive only when neither branch acquires a unit or conflict from the appended
clauses. Original reasons remain persistent even when a pair is omitted from
the continuation. No stored activity mask or choice list is trusted.

The policy retains old-ranked choices in their old order when they are novel or
have an active original pair. It then fills remaining positions with active core
variables in original order, truncating only these additional candidates. A
single invocation-scoped callback shares the already checked selected batch;
it introduces no cross-source cache. Empty choices produce a checked inconclusive
continuation. Successful reductions still require strict support decrease and
an exact original-clause core child with model lifting.

At a fixed source and batch, this retains any old local reduction: every omitted
old pair has unchanged, previously clear traces and cannot supply a forced,
common or equivalence outcome in this procedure. All other old choices fit the
same cap and retain their order. Additional probes may find an earlier-priority
reduction, but cannot remove every old reduction. This argument is local;
changed reduction kinds, assignments, substitutions and descendants can still
change whole-source coverage. Inactive propagation is not general irrelevance
of the variable or completeness for arbitrary SAT.

Beyond the existing old-ranking reconstruction, selecting candidates costs
expected O(U + p*q + p^2) in the unit-cost model, where U is the total original
unit-trace length, p the original variable cap, and q the bounded binary batch
size. The p^2 term accounts for list-membership checks when appending candidates.
Temporary state is O(p + u_max), beyond the existing batch and traces, for the
largest original unit trail u_max. Original proof acquisition/checking, ranking,
active/new propagation, normalization, serialization and persistent graph growth
remain charged. The auxiliary old first-four batch is still reconstructed;
sharing its sixteen-clause pool is a separate unimplemented optimization.

## Inputs and accounting

The full comparison retains all 1,389 preceding queries and adds 36 at seed
20261109083909: 24 new random 3-CNFs (eight each at 20, 32 and 48 variables) plus
twelve growing, signed or edited queries, including deliberate repeats. Routing
sees only the CNF. Caps are depth two, four probe variables and four learned
clauses per eligible residual. The same independent decision solver checks all
original inputs; structural closure is distinct from a SAT/UNSAT decision.

Operation time includes recognition, discovery, proof checking, serialization,
persistence, independent solving and successful root lifts. Initialization is
separately measured. Input generation, truth-table comparisons, summary walks,
compression, allocation diagnostics and cold audits are outside operation time.
Warm lookup and cold replay are separate. The matched six-case Python allocation
diagnostic excludes native SQLite, RSS and the full-corpus peak. Primary modes,
memory diagnostics, profiles, tests and builds run sequentially. These are single
synthetic samples, not significance estimates or industrial comparisons.

## Results: less repeated probing, no established runtime speedup

All 512 tiny cases close. Both policies close **806/913 non-tiny queries**, with
**no source gains or losses**. The previous 1,389-query subset retains 776/877
non-tiny closures, and both close 30/36 new queries, including 18/24 fresh random
sources. Source 956 is recovered relative to the previous core-order policy;
1024 remains closed. Source 977 now selects the previously unselected local
case-97 core. Its open part shrinks from two leaves / 138 literals to one leaf /
22 literals, but the source remains unresolved. Source 1189 remains open.

| Policy | Closed / 913 | Operation s | Discovery s | SQLite bytes | Cold s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary decision solver | — | 50.31254 | — | 121,438,208 | 12.54728 |
| Existing core policy | 806 | 161.35645 | 116.82649 | 376,205,312 | 55.11608 |
| Activity policy | 806 | 134.22746 | 99.01207 | 375,824,384 | 57.63553 |

The single full-run sample has a substantial timing confound: the unchanged
solver takes **44.42359 versus 35.13847 s** in the two combined modes. A separately
recorded **ABBA BAAB** control repeats eight source queries four times per policy,
using a fresh database each time. Mean total time is **3.85140 versus 3.88671 s**;
mean discovery is **3.64992 versus 3.68110 s**. Activity is slightly slower on this
subset. Every trial repeats its policy's exact answers, summaries, counters,
storage and database hash. These limited observations do not establish statistical
significance, but they do not support treating the single full-run difference as
an algorithmic speedup. Keep the policy optional. `timing-control.json` preserves
all trials and the timing script's hash; its corpus is not the full workload.

| Work or retained state | Existing core | Activity |
| --- | ---: | ---: |
| Continuation attempts | 31,741 | 7,184 |
| Total logical probe attempts | 127,741 | 103,413 |
| Verified probe attempts | 250,703 | 223,315 |
| Reused continuation probes | 26,407 | 1,615 |
| Active original continuation probes | 1,588 | 1,810 |
| Newly chosen continuation probes | 3,746 | 3,759 |
| Pattern nodes | 22,549 | 22,581 |
| Logical node bytes | 148,631,944 | 147,670,431 |
| Probing-field bytes | 16,760,009 | 15,465,288 |
| Source bytes (1,393 records) | 5,405,961 | 5,422,677 |
| Six-case Python peak bytes | 20,265,108 | 19,996,930 |
| Selected unresolved literal occurrences | 28,314 | 28,170 |

Continuation attempts fall **77.37%**, mainly by omitting unchanged pairs rather
than finding fewer fresh propagations. Active-plus-novel probes actually rise
**5,334 -> 5,569**. Across discovery/checking there are 9,460 choice calls, 32,620
inactive and 5,100 active original pairs, 28,424 omitted old inactive candidate
positions, 9,402 retained old positions and 682 added core positions. There are
3,088 empty continuations and 36 truncated candidate occurrences. These counts
include repeated checks and different descendants; they are not unique facts or
paired per-state timing differences. Old ranking reconstruction remains charged.

Warm lookup is **0.27624 -> 0.34976 s**, initialization **0.06187 -> 0.28580 s**,
and cold replay becomes slower despite the lower operation-time sample. Both
modes preserve all answers and 19,557 independent solver residuals. Three full,
three pilot and three previous archives replay byte-identically; warm reuse
inserts nothing. Logical bytes, policy-tag lengths, physical pages and traced
allocations are distinct measures.

## Local preservation and the next coverage opportunity

The separate control rechecks all **3,001** changed shared CNF/depth states from
the preceding experiment. All **421** old learned reductions survive; **16** old
clear states gain reductions, and 2,564 remain clear. All **255** saved gained/lost
transition cases therefore have a successful learned reduction under the new rule.
The seven five-candidate cases keep all informative old candidates and truncate
only additions. These are local reductions, not new source closures. The new
full archives also contain eighteen clear-to-learned transitions on shared states,
with no learned-to-clear transition.

The frontier has **107 unresolved sources / 147 distinct selected leaves**:
61 inconclusive continuations (12,984 literal occurrences), 39 empty continuations
(10,639), 46 clear passes without a learned batch (4,264), and one case without
original binary-ranked candidates (283). Thus simply choosing an initial variable
when no binary candidate exists addresses only one leaf here. Source **1194**
remains the largest unresolved discovery case at **1.47590 s**, with 424 selected
unresolved literals. Its separate profile records 5,763 restrictions, 4,657 unit
checks and 2,221 propagations; these remain major costs. Probe-kind nodes occupy
96.289 MB, including CNFs/identities/edges; probing fields alone occupy 15.465 MB.

The next diagnostic identifies a representation gap with explicit witnesses.
General **signed clause subsumption** changes 105 of the 147 frontier cores,
removing 217 clauses / 666 literals through 672,003 subset comparisons. Existing
basic recognition then identifies **seven 2-CNF cores**. In the 22-literal source-
977 leaf, `(-7,3)` subsumes `(-7,-1,3)`, and `(-3,9)` subsumes `(-3,7,9)`; the
remaining clauses are binary. Each removed clause has a retained signed subset,
so the reduction preserves every model, with arbitrary values allowed for any
variables that disappear from the core. Normalization maps are retained.

Conditional on integrating these exact reductions and recomposition, the current
selected plans of **977, 1044, 1053 and 1365** could become closed. Sources 907,
1179 and 1363 would still have another unresolved selected leaf. These are
**prospective** completions, not part of the measured 806/913 coverage. The new
`frontier-subsumption.json` saves all 147 source bindings, witnesses, normalized
cores, classifier outcomes and selected-plan links. The ordinary decision
prototype already has a positive-clause subsumption path; the pattern inventory
lacks this signed reduction. Subsumption is an established simplification, not a
new general SAT algorithm. Full recognition, checking, acquisition, persistence
and cold costs still need an integrated experiment. Prioritize that concrete
coverage opportunity over more ranking-only tuning.

All **388 Python tests** pass, including eight new tests for exact small model
fibers, forced/common/equivalence lifts, all 255 saved local transitions, the seven
budget overflows, empty checked continuations, corrupted traces/orders/children,
signed edits and cold coexistence. The unchanged Lean build and axiom audit pass
at **4,126 declarations / 1,968 theorems**. Both reports' **53** fingerprints,
archive hashes and diagnostic input/script hashes match. The local preservation
argument is documented; the Python selector and lifetime resource bounds are not
formally refined. No new unrestricted-SAT tractability claim follows.

Reproduce without overwriting previous data:

```sh
python3 experiments/compare_cnf_learning_activity.py --pilot --output /tmp/cnf-activity-pilot-new
python3 experiments/compare_cnf_learning_activity.py --output /tmp/cnf-activity-new
python3 experiments/analyze_cnf_activity.py /tmp/cnf-activity-new
python3 -m unittest solver.test_cnf_learning_activity -q
```

`report.json` and `summary.json` retain inputs, costs, decisions, counters and
fingerprints. `mechanisms.json` records source paths, shared states, the frontier,
separate profiling and checked controls against the previous ranking experiment.
Gzipped SQLite archives retain original proofs, unsuccessful attempts, every
alternative and independent solver results. Earlier archives are preserved.
