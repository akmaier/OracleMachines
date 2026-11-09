# Core-ranked continuation under the existing probe budget

9 November 2026. This optional policy tests the ranking cause isolated in the
previous portable-hint experiment. It retains the selected learned batch, original
core child, existing recognition priorities, and two bounded probe phases. It
extracts continuation variables from the complete original core probe trace.
The checker validates that trace, including its deterministic order, before any
choices or closure references can be reused. No persisted choice list is trusted.

Extraction takes O(p) time and temporary reference storage for a p-variable probe
cap. The original pass and checker still rank the source; selecting and proving
the learned batch, delta checks, active propagation, child acquisition and replay
remain charged. This removes reconstruction of a second first-four learned view
solely for ranking. It does not bound the total number or size of residuals.

The four-source pilot retains 956/977/1024/1189. Core ranking loses the closure
of source 956, retains 1024, and leaves 977/1189 open. The preceding local case 97
does close with the same learned batch and core choices, but it is an unselected
alternative of 977. That local success must not count as a source-level gain.

The full matched study uses all 1,317 preceding inputs, the 36 additional source
queries from the hint study, and 36 controls at seed 20261109073810: 24 new random
3-CNFs (eight each at 20/32/48 variables) and twelve growing, signed or edited
controls, including intentional repeats. Discovery receives only the CNF. The
512 exhaustive two-variable cases remain in the input ledger. Caps stay at
depth two, four probe variables and four retained learned clauses per eligible
residual. An unchanged independent decision solver checks every original input.

Operation timing includes discovery, recognition, checking, serialization,
persistence, exact solving and successful root lifts. Initialization is separately
timed. Generation, truth-table comparisons, summary walks, compression, allocation
diagnostics and cold audit are outside operation time. Warm reuse and cold replay
are measured separately. The six-case Python allocation diagnostic excludes
native SQLite allocations, RSS and the full-corpus peak. Modes, memory diagnostics,
profiling, tests and builds run sequentially; these synthetic single samples do
not establish statistical significance or an industrial comparison.

## Matched result and decision

| Policy | Closed / 877 non-tiny | Operation s | Discovery s | SQLite bytes | Cold s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary decision solver | — | 30.67714 | — | 110,891,008 | 6.48177 |
| Existing core policy | 776 | 120.81853 | 88.69202 | 347,566,080 | 50.51029 |
| Core-ranked continuation | 775 | 116.67493 | 85.68326 | 346,976,256 | 47.82982 |

The 512 exhaustive tiny inputs close under both discovery policies. There are
**no gained source closures and one loss, source 956**. Old-input closure falls
719 -> 718 / 805; both policies close 30/36 prior hint-study sources and 27/36
new queries, including 15/24 new random 3-CNFs. Source 1024 remains closed;
977 and 1189 remain open. All original decisions agree, and each mode retains
18,104 ordinary solver residuals. Closure is structural coverage, not a decision
of satisfiability; the independent solver still answers every input.

Operation time falls 3.43% in this single sample; discovery time falls 3.39%.
The unchanged solver alone varies by 1.13 s between combined modes, so the full
4.14 s difference cannot be attributed entirely to ranking. Keep this optional:
a small observed cost saving with lower coverage is not a dominating replacement.
The cold checks include every alternative, source and solver certificate, and
leave the databases byte-identical. Warm lookup costs 0.25672 -> 0.22710 s with
no insertion. Initialization costs 0.06160 -> 0.22272 s, separately measured.

| Work or retained state | Existing core | Core-ranked |
| --- | ---: | ---: |
| Pattern nodes | 21,122 | 21,005 |
| Logical pattern bytes | 137,740,084 | 137,076,682 |
| Source records / bytes | 1,365 / 5,225,670 | 1,365 / 5,250,240 |
| Six-case Python peak bytes | 20,265,108 | 19,623,309 |
| Logical probe attempts | 119,412 | 118,152 |
| Reused continuation probes | 24,672 | 27,611 |
| Active original continuation probes | 1,492 | 1,700 |
| Newly chosen continuation probes | 3,527 | 0 |
| Ranking literal visits | 20,935,654 | 17,949,416 |
| Learning graph literal visits | 6,433,538 | 3,516,760 |
| Learned candidate visits | 336,186 | 185,626 |
| Selected unresolved literal occurrences | 26,137 | 26,734 |

The old 8,772 ranking reconstructions disappear. New choice extraction occurs
8,106 times and copies 32,326 candidate entries across discovery and checking.
These counts have different residual populations and include repeated checks;
they are not a paired per-state saving. Physical database pages, longer policy
keys, logical payload and live allocation are separate accounts. Zero newly
chosen continuation probes follows from reusing the original candidate set; it
also removes useful discovery opportunities. Hints are still parent-scoped.

## Mechanism, remaining gap and next experiment

At the shared 18-variable, 62-clause depth-one parent on source 956, both policies
select the same learned batch. Old continuation choices are `(17,9,14,16)`;
the first conflict is `14=true`, forcing `14=false`. Core choices are
`(9,17,18,2)` and remain clear. All four original paired closures are inactive
under the selected batch. The new policy drops the two novel candidates 14 and
16, and source 956 ends with one unresolved leaf containing sixteen literals.
This differs from the previous representation-induced loss on the same source.

Across shared normalized-CNF/depth states, **239** old learned reductions become
clear and **16** old clear states acquire a learned reduction. The other shared
status counts, complete source paths, both probe records and candidate lists are
saved in `mechanisms.json`. Of the 239 local losses, **189** have no active core
pair. In every one of the 255 gained/lost local states, the union of active core
variables and novel old-ranking variables has size at most four. The respective
size distributions are `{1:166, 2:51, 3:17, 4:5}` for losses and
`{2:7, 3:6, 4:3}` for gains. These are states at specific depths, not 255 distinct
original inputs or demonstrated recovered source closures.

This motivates the next discovery experiment: keep the fully checked original
traces, identify pairs whose closure changes under the selected batch, and spend
the existing continuation budget on active core candidates plus newly ranked
variables. Inactive paired closures cannot gain a forced/common/equivalence
outcome when both traces and unit sets are unchanged; they remain reusable
references. Seven other changed shared states already have a union of five variables, so
the cap remains a real limitation.
Different first conflicts can also change later source coverage. Test the saved
255 controls, source 956 and the local 97/977 distinction before whole workloads.
No new combined policy or recovery result is implemented in this checkpoint.

A supporting exact-reuse opportunity preserves the old ranking: for caps at most
sixteen, `learning_batch(...,16)[:cap]` is the deterministic first-cap batch.
Sharing that already acquired pool can remove the second reconstruction without
changing choices. It must use the checked source/attempt context, not an unchecked
persistent pool. This is a proposal, not a measured additional saving.

The core-ranked frontier has **102 unresolved sources / 142 distinct selected
leaves**, 99 learning-clear and 43 clear. Source **1194** is the largest unresolved
discovery case at **1.45407 s** and 426 unresolved literal occurrences. Its separate
profile still identifies restriction, unit-proof checking and propagation as main
costs (5,307 restrictions, 4,311 simplification checks and 2,069 propagation calls).
Probe-kind nodes occupy 87.079 MB of logical state; the probing field alone is
15.273 MB. Do not describe the whole node payload as proof-only storage. Broad
propagation-state reuse remains relevant beyond this bounded ranking experiment.

All **380 Python tests** pass, including six new tests for exhaustive small
model fibers, forced/common/equivalence lifts, the saved ranking counterexample,
invalid original traces and continuations, signed mixtures/edits, disabled learning,
wrong child bindings and byte-identical cold coexistence. Three full, three pilot
and four preceding archives replay byte-identically. Both reports' **50** code,
test and Lean fingerprints and the analyzer/report hashes match. The unchanged
Lean build/axiom audit passes at 4,126 declarations / 1,968 theorem declarations;
no Python refinement or new
unrestricted-SAT resource bound is claimed.

Reproduce without overwriting any existing results:

```sh
python3 experiments/compare_cnf_learning_core_order.py --pilot --output /tmp/cnf-core-order-pilot-new
python3 experiments/compare_cnf_learning_core_order.py --output /tmp/cnf-core-order-new
python3 experiments/analyze_cnf_core_order.py /tmp/cnf-core-order-new
python3 -m unittest solver.test_cnf_learning_core_order -q
```

`report.json` preserves inputs, decisions, counters, policies and fingerprints;
`summary.json` aggregates costs and coverage; `mechanisms.json` preserves source
gains/losses, selected paths, changed shared states, unresolved frontier and a
separate profile. Gzipped SQLite archives retain proofs, all alternatives and
solver results. Existing archives and earlier policy implementations remain intact.
