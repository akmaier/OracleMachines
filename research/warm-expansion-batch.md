# Advance discovery while retaining checked history

The batch runner keeps the reconstructed inventory, historical validation caches
and complete coverage index available across useful discovery steps. It uses
`WarmExpansion` to resume ordinary probe blocks, follow forced residuals and,
after ordinary-pool exhaustion, acquire both cofactors of a retained clear pair.
This applies the preceding [coverage reuse](incremental-coverage.md) experiment
to actual expansion rather than another isolated replay benchmark.

## Discovery result

Structural coverage rises **58/83 -> 59/83** on the reused development set. The
newly covered case is index **30**, original case **1189**, `reuse_holdout3/n48`:
**48 variables / 204 clauses**. The historical group name does not make it a
fresh holdout after adaptive reuse. The reference solver independently confirms
it SAT. No new tractable family or unrestricted complexity bound is inferred.

The eight steps expose a useful sequence of existing transformations:

1. Three saved clear blocks check twelve more variables on the **22-variable /
   88-clause / 272-literal** source. The fourth block checks five assumptions and
   finds a conflict under source variable **20=false**, after nineteen unit
   deductions. Thus **20=true**. Restriction gives **21 / 74 / 214**; it does not
   by itself give the smaller final leaf.
2. The unchanged recognizer applies **five binary-implication path deletions and
   six variable eliminations**, reaching an unresolved **15 / 55 / 173** leaf.
   Together with that leaf, these are **twelve new pattern nodes**. Implication
   paths justify deleting redundant wide clauses while preserving their binary
   reasons. All eliminated variables and canonical transports remain checked.
3. Three more clear blocks exhaust the smaller source's ordinary pool. Including
   its internal probes, both assumptions have been checked for all fifteen
   variables without a unit-propagation conflict. This is inconclusive for SAT;
   it licenses switching the scheduler to a retained pair, not claiming UNSAT.
4. The ranked saved pair for **variable 4 in the 15-variable source** yields
   cofactors **13 / 37 / 99** and **10 / 32 / 86**. They acquire three and six
   states respectively. Further checked probes, one binary-path deletion and
   subsumption expose **4-variable / 3-clause** and **6-variable / 10-clause**
   2-CNF terminals. The first is also Horn and zero-valid. Both branches close,
   and the reference solver independently finds both satisfiable.

The batch uses **21 of 32 allowed states**, with no pending obligation. Closure
propagates through **65 sources in each coverage graph**, reusing retained
ancestors to close the larger original input. The new expanded positive proof
has **2,828 steps**, versus 2,748 previously. The pattern to investigate elsewhere
is the interaction: a forced restriction can expose redundant wide clauses,
enable bounded elimination, and leave a small split into recognized families.
This is evidence for that routing strategy on one input, not a guarantee that
the same sequence is short for arbitrary CNF.

## Fixed policy and preservation

The policy is fixed before the experiment: at most **eight steps**, one shared
**32-state admission allowance**, at most **32 admissions per split pair**, and
at most **64 retained candidate pairs** ranked by the existing heuristic. A
step selects the smallest acquired open leaf below retained splits, or resumes
an explicit pending obligation first. Ordinary blocks reuse checked prefixes.
If the ordinary pool is exhausted, the selected split reuses its two saved
unit-propagation traces. Both branches share the remaining global allowance.

The batch does not reset admissions between steps or between ordinary and split
acquisition. A pending target remains explicit; completed children and all probe
records survive a budget stop. Re-entered unfinished recognition states remain
charged according to the existing inventory's accounting. The allowance bounds
distinct entered recognition states in this session, not CPU, bytes, reference
solving, or total work over many future sessions.

After each step, the runner rebuilds the complete checked external-route catalog
and updates the retained coverage graphs. Full warm recomposition runs as a
matched control on exactly the same graph; order alternates between steps. Both
paths replay the original positive-plan checker. The control's time is part of
the study pipeline, not part of the proposed incremental operation. Catalog
refresh is charged separately and is still global. Pending routes activated by
new targets cannot be omitted.

The first session loads the previous persisted graph only after checking its
parent binding and every reachable rule against authoritative history. It pays
this cold audit once. Later sessions can reconstruct the graph from their own
checkpoint. The runner does not write another large full graph snapshot at the
end of each batch: it retains an append-only database delta, any new split
sidecars, operation records, the resulting coverage proof, and frontier
diagnostics. This avoids recurring snapshot production, but supplies no fast
trusted-negative cold restore. The complete authoritative SQLite and historical
validation caches remain required during this run; the earlier small
source-local working database is not used here.

The checkpoint restorer binds parent hashes, options and case lists, preserves
all five evidence lists, conflict-checks and cold-validates the new database
records and split traces, and independently replays the expanded positive proof.
Full and incremental coverage are compared after every step in the production
session. This is not a fresh cold audit of all historical records or negative
coverage flags. Initial complete catalog checking and immutable checked appends
remain prerequisites for negative finite-catalog conclusions.

## Reproduction

`python3 -m unittest solver.test_cnf_warm_expansion` checks shared allowances,
clear-prefix exhaustion followed by a split, both pending branches, exact pending
resume, reuse without reprobing, and rejection of mismatched scope or allowance.

Run `python3 experiments/continue_cnf_warm_batch.py NEW_DIRECTORY` for the first
batch, or pass `--parent REPORT` for a later compatible checkpoint. The batch
preserves failed acquisition deltas and evidence if a session raises an error.
It does not claim a globally cheapest split, a representative SAT benchmark,
or polynomial construction for unrestricted SAT.

## Cost and storage account

| Phase | Seconds |
|---|---:|
| Initial authority reconstruction | 25.09147 |
| Initial complete route preparation | 6.31734 |
| Initial persisted-index load and complete semantic audit | 59.72300 |
| Selection across eight steps | 0.08348 |
| Eight actual discovery/acquisition steps | **0.11884** |
| Eight complete external-route refreshes | **7.59057** |
| Full warm composition and original plan checking, total control | 1.30709 |
| Incremental composition and original plan checking, total | 0.30604 |
| Delta comparison/export/compression, once | 5.39005 |
| Cold checking of all new database rows and dependencies | 0.04017 |
| Independent positive replay, including new split checking | 3.04579 |

The matched warm composition totals differ by **1.00105 seconds**. Including
selection, acquisition and the shared route refresh gives **9.09998 versus
8.09893 seconds**, an indicated **11.00%** saving before persistence and initial
preparation. The first full-control sample is 0.49008 seconds, while later ones
range from 0.11307 to 0.12710 seconds; these are individual adaptive steps with
shared caches, not replicated whole-solver speedup estimates. First reconstruction,
route preparation and index auditing total **91.13181 seconds**. The complete
study takes **122.01047 seconds**, including both composition controls, reference
work and integrity checks. Initial and cold costs are not removed by batching.

Saved split-trace reuse itself is not faster on this measured pair: **0.000719 s**
for replay versus **0.000452 s** for fresh propagation plus checking. The replay
avoids two fresh assumption traces but reads **12,114 payload bytes**. This small
one-pair loss is preserved; avoided reasoning steps need not mean lower runtime.

The database delta contains **21 patterns, two windows and five continuations**:
**15,484 compressed bytes / 397,312 SQLite bytes**, plus one separate saved-split
record. Full authoritative SQLite grows by **335,872 bytes** to
**770,707,456 bytes / 41,780 pattern nodes**. All earlier rows survive unchanged,
and merging the delta twice is bytewise idempotent. The reference archive preserves
all **2,012** earlier nodes and now checks **2,041**. No total-memory reduction is
claimed; full history, historical verifier caches and both live coverage graphs
remain in use. Other study artifacts, including positive/reference archives,
add storage beyond the acquisition delta.

All **160 relevant tests** pass. A separate fresh reconstruction validates the
checkpoint and new records, preserves twelve saved split sidecars, and replays
the 59-root positive proof. The five evidence lists now have counts
**(1, 42, 156, 12, 1)**. Resume via
`continue_cnf_warm_batch.restore_checkpoint` from
**`experiments/results/cnf-warm-batch/report.json`**.

## Next discovery target

The retained split frontier is now empty: its selected descendants are closed,
but **24 of the 83 original inputs remain structurally uncovered**. The batch
stopped at its eight-step cap. Repeating its retained-frontier selector alone
would find no new work. The next run must use the original-input selector
(`continue_cnf_original_splits.select` / `selected_frontiers`) to seed another
open original, or explicitly select a learned base.

The preserved learned queue still has **17 ready bases / 88 candidates**. Its
smallest ready source has **33 variables / 359 literals**, with eight candidates
remaining at offset 24; base identity
`1ad496f104725f62b5d8f754633a96c47aac13064bc6bf977b2f79001dfbde24`.
Compare that option with ranked residuals of the remaining originals, keeping
source coordinates and already checked prefixes explicit. Prioritize transferring
the observed restriction/implication/elimination/split sequence to another open
input. Complete route refresh is the larger repeated warm maintenance cost, but
another overhead-only study would not expand structural coverage.
