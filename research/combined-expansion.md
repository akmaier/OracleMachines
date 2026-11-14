# Combining saved-pair selection with checked route maintenance

The next selected leaf belongs to original **1154 / index 27** and has **38
variables, 158 clauses and 500 literal occurrences**. Its bounded ordinary probe
pool is exhausted. Eleven saved pairs have unacquired child roots, and the best
rank is **[2, 2, 36, 906, 30]**. Both modes therefore start with the same checked
split on local variable 30. The comparison concerns the unresolved descendants
that this split exposes, not an opportunity to skip already exhausted probing.

Each worker starts from an independent copy of the same authority, receives
twelve advances including the initial split, and shares one 32-state admission
allowance across both polarities and all descendants. The ordinary mode uses
`EarlyClosedExpansion`: it continues probes unless a saved pair has a closed
child. The early mode uses `EarlySavedExpansion` after the common first step.
Both use `ClearProbeMaintenance`, preserve pending/known-forced priority, and
require both branches for structural coverage. Two repetitions reverse mode
order. No new production recognition rule or default scheduling policy is added.

## The combined comparison does not finish the target

Neither mode closes the original within these limits. Coverage stays **65/83**.
The common first split acquires ten patterns and exposes unresolved leaves
**31/130/416** and **36/143/443**. Ordinary continuation spends the remaining
advances on forcing, probing and splitting. Early selection spends its remaining
state allowance on three more splits.

| Metric | Ordinary with maintenance | Early saved pairs with maintenance |
|---|---:|---:|
| Advances | 12 | 4 |
| Admitted recognition states | 30 | 32 |
| Completed new pattern rows | 30 | 27 |
| Entered but unstored states | 0 | 5 |
| External assumption attempts | 61 | 0 |
| Full route rebuilds | 4 | 4 |
| Clear appends retaining the catalog | 8 | 0 |
| Mean expansion seconds | 4.98209 | 4.64624 |
| Mean complete worker seconds | 17.80102 | 17.20828 |
| Mean acquisition/ranking seconds | 0.62102 | 0.33991 |
| Mean route-maintenance seconds | 4.33169 | 4.29539 |
| Mean initial preparation seconds | 7.67697 | 7.83099 |
| Delta SQLite bytes | 593,920 | 462,848 |
| Compressed delta bytes | 26,971 | 20,877 |

Ordinary continuation reaches the twelve-step limit with two admission slots
left; early splitting reaches the 32-state limit with a split still pending.
These unequal unfinished obligations prevent interpreting the smaller early
runtime or stored delta as a saving for a completed original. Two repetitions
also supply no confidence interval. The extra ordinary clear blocks already
avoid full rebuilds, explaining why skipping them no longer produces the large
runtime differences seen before maintenance was optimized. Both modes still
pay for four semantic route refreshes. Their acquisition costs are smaller than
maintenance, preparation and export.

The early mode's last split is local variable **26** of **30/116/363**. Its
false target is **29/108/336**, its true target **19/54/140**. The five remaining
admission slots are entered while descending the first target, but none of
those five ancestor plans completes serialization before the cap is reached.
The second target receives no admission. Their exact split certificate and
entered keys are retained, and both missing target roots remain explicit.
Completed historical results are preserved; the interrupted ancestor work is
not falsely counted as a reusable completed pattern. Restarting that descent
can repeat work, making resumable recognition state a concrete persistence gap.

## A completed common cofactor gives a fair local comparison

Cold reconstruction inserts only the rows available at each advance. It proves
that the same **true cofactor** of the initial variable-30 split closes after
**nine advances / thirty admitted states** in ordinary mode, versus **two
advances / nineteen states** in early mode. The common first split accounts for
ten states. Thus completing this cofactor needs **20 vs 9 additional states**;
all are stored by that completion point. Mean expansion after the common split
is **3.64836 vs 1.11924 s**. Including the shared first step gives **4.85956 vs
2.38038 s**. These prefix timings exclude initial catalog preparation and final
export. The second repeat has the same exact operations within each mode.

The common true cofactor is 36/145/454; probing, binary-path reductions and
elimination reach 31/130/416. The early policy selects local variable 23 there.
Its false cofactor 27/105/305 takes two probe reductions to an existing empty-CNF
terminal; its true cofactor 29/100/303 takes seven and reaches the same terminal.
Ordinary continuation first discovers forcing down to 26/101/329, then selects
local variable 5. The false branch 17/45/124 reaches the empty-CNF terminal; the
true branch 24/93/289 follows ten probe reductions to a retained 3/2/4 Horn
2-CNF plan. Different acquisition paths close the same cofactor, and early
conditioning exposes the shorter one on this source. This is a measured local
choice, not a universal selector or a compact representation theorem.

The other initial cofactor remains open. Early mode splits its 36/143/443 leaf
at variable 11, exposing 30/116/363 and 33/130/400 after checked reductions.
The smaller leaf produces the interrupted variable-26 split described above;
the 33/130/400 leaf also remains unresolved. Finishing the pending split alone
must not be assumed to close the whole original.

All five retained split sources and both raw cofactors of each are SAT in the
independent reference check. Available SAT model lifts are verified. The open
obligation is complete structural decomposition, which is stronger than finding
one SAT witness. Reference answers never fill an absent structural certificate.
The first repeat is audited step by step; exact operation histories and final
logical results agree between repetitions within each mode. Independent cold
replay passes in **302.33071 s**, with fresh recognition and reference expansion
forbidden, including all **3,422 reference nodes**, both split polarities,
interrupted admission accounting, exact next selections and idempotent deltas.

## Preserved union and remaining work

The two modes share the ten initial new patterns and otherwise acquire disjoint
new keys: **20 ordinary-only / 17 early-only** completed patterns. Their union
keeps **47 new patterns**, six continuations, four windows and five split
certificates. It is not one run with a 32-state limit. The history grows
**765,952 bytes** to **774,766,592 bytes / 42,020 patterns**. The union delta is
**831,488 SQLite bytes / 37,999 compressed bytes**, excluding sidecars and
reference evidence. All previous rows and unsuccessful ordinary probes remain.
There are five evidence lists of lengths **(1, 42, 156, 38, 1)** plus the two
previous projection bridges.

The producer takes **231.79591 s**, including **67.80502 s** for authority
reconstruction and **67.41552 s** for final route preparation/global coverage.
Union delta export takes **5.58306 s**. The independent reference archive grows
from **3,259 to 3,422 nodes**; reference solving does not supply structural
coverage. The existing positive certificate still has **3,239 steps** and covers
the same 65 originals. All timings charge preparation, checking and persistence
at the reported level. Stored bytes are not peak RAM, and these development
cases do not establish a bound for arbitrary SAT or minimum-cost expansion.

Resume `experiments/results/cnf-combined-expansion/report.json` using
`compare_cnf_combined_expansion.restore_checkpoint`, retaining all five evidence
lists and the separate `bridges` archive. Report SHA-256:
`33c45cc536dc9ada0acdb4d1ef9a17bd9a71e260704644aa656af42835c349c3`.
Use bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The scheduler first resumes the exact pending split of the 30-variable source:
`f68661ab48e945151f89e250ebbcc35eb2ff8034799d2a83e2ddd88d7306567d`.
Do not rerank it or drop either polarity. The retained frontier has two pending
target entries and one acquired unresolved leaf.

## Reproduction

From the repository root, with a fresh output directory:

```sh
python3 experiments/compare_cnf_combined_expansion.py experiments/results/cnf-combined-expansion
python3 experiments/validate_cnf_combined_expansion.py experiments/results/cnf-combined-expansion
python3 experiments/summarize_cnf_combined_progress.py experiments/results/cnf-combined-expansion
```

Run timing producers and cold reconstruction without concurrent tests or paper
builds. The validator additionally reconstructs each step of the first repeat
from only the pattern rows and probe records available at that step. It checks
the common cofactors' closure and next selections before inserting later work.
This avoids assigning later or union knowledge to an earlier expansion prefix.

Verification: **209 regression tests pass**; the manuscript builds to **158
pages**, with all **64 proof blocks unchanged** and no undefined references or
overfull boxes. SHA-256 checks preserve all **784 artifacts in 19 prior
manifests**. The new manifest binds **81 artifacts** (4,377,743 bytes), including
producer/cold logs, both policy histories, stepwise findings, progress summaries
and validation metadata. One existing SQLite ResourceWarning appears in the
passing regression log; no solver or test module changed.
