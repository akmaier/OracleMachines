# Original-input expansion and early reuse of a closed cofactor

## Result

The next twelve-step batch selects original case **1445**, index 74 of the same
83 reused development inputs. It follows the smallest selected residual:
**33 variables / 121 clauses / 359 literals**. Two saved splits expose binary-path
deletion and variable elimination, leaving one open residual of **29 / 103 / 307**.
Only **seven of the shared 32 state admissions** are used. Both splits reuse the
same already stored empty-CNF terminal for their closed branch. Structural
coverage stays **59/83**; this experiment has no new original-level closure.

The result transfers part of the previous restriction/deletion/elimination
sequence to another original. It also identifies a scheduling gap: the chosen
split traces were already present in the immutable source nodes, but the policy
waited for ordinary-probe exhaustion before using them. Seven clear probe blocks
precede those two splits. Their complete route refreshes alone cost **6.73336 s**.
Earlier split selection is a candidate improvement, not a measured speedup: it
must be compared against the possibility that more probing finds a cheaper
forced reduction.

## Exact selection and decomposition

`experiments/cnf_original_frontier.py` first resumes retained unfinished targets
or open split descendants. When that frontier is empty, it traverses the selected
internal and ordinary routes of uncovered originals, deduplicates shared leaves,
and ranks them by support, literal count and exact identity. Pending ordinary
targets precede new original work and retain the source of their saved forced
trace. Selection performs no acquisition and does not reset the admission budget.

The caller must supply a complete checked route catalog and current closure
flags. This is a selected-path scheduling view, not an exhaustive comparison of
all decompositions or a proof of globally minimum expansion. Both branches of a
saved split remain required for structural coverage, even when one branch gives
a checked SAT witness. The five evidence lists are preserved.

| Stage | Checked structure | New states |
|---|---|---:|
| First ordinary continuation | Eight variable pairs at offsets 12 and 16 are clear | 0 |
| Split on local variable 12 | True reaches the existing empty terminal after 30 unit deductions; false reaches 32 / 113 / 333 | 3 |
| False-branch reduction | Binary-path deletion gives 32 / 112 / 330; elimination gives 31 / 114 / 341 | included above |
| Second ordinary continuation | Seventeen variable pairs across five blocks are clear | 0 |
| Split on local variable 26 | False reaches the same empty terminal after 27 unit deductions; true reaches 30 / 107 / 316 | 4 |
| True-branch reduction | Binary-path deletion gives 30 / 103 / 302; elimination gives 29 / 104 / 311; another deletion gives 29 / 103 / 307 | included above |
| Final ordinary continuation | Twelve further variable pairs across three blocks are clear | 0 |

Variable identifiers are local to each normalized source. Elimination reduces
support here while increasing clause and literal counts at that individual step;
those costs are not monotonically decreasing. The new nodes comprise three
binary-path reductions, two eliminations and two unresolved states. No new
terminal family is admitted. The two successful cofactors reuse one exact
canonical empty-CNF identity, including its recognition configuration and depth.

All **74 new external assumption attempts** are clear. The selected split pairs
refer directly to their respective immutable pattern rows, so their evidence
was available on source admission, before the new continuation blocks. Independent
replay checks both splits and lifts each empty-cofactor model back to its source.
Those are local SAT witnesses. They do not discharge the other structural branch.
The independent reference solver also reports both cofactors of both splits SAT.

## Runtime and retained storage

| Phase | Seconds |
|---|---:|
| Initial authority reconstruction | 29.07749 |
| Initial complete route preparation | 6.51664 |
| Initial coverage graph construction and semantic checks | 58.92669 |
| Selection across twelve steps | 0.21472 |
| Discovery and acquisition | **0.20427** |
| Twelve complete route refreshes | **11.55914** |
| Full warm composition and original plan checking | 1.38586 |
| Incremental composition and original plan checking | 0.47716 |
| Delta comparison, export and compression | 5.32914 |
| Cold new-row checking | 0.05602 |
| Cold positive replay and split checking | 3.02762 |

The two warm controls agree at every step, including without-growth coverage.
Adding shared selection, acquisition and route refresh gives **13.36399 s full
versus 12.45529 s incremental**, an indicated **6.80%** saving on this one batch.
Initial preparation is still **94.52082 s**. The complete experiment costs
**129.39795 s**, including both controls and reference/persistence work. These
are single-run measurements, not a stable complete-solver speedup estimate.

Saved split replay costs **0.001023 / 0.000906 s**, versus **0.001193 / 0.000997 s**
for fresh propagation and checking on the two pairs. These small local differences
do not explain the pipeline cost. Discovery is cheap relative to route maintenance
and initial historical validation.

The delta contains seven patterns, two windows and eight continuations:
**14,150 compressed bytes / 278,528 SQLite bytes**, plus two split sidecars.
Full history grows by **217,088 bytes** to **770,924,544 bytes / 41,787 patterns**.
Every earlier row remains unchanged; merging the delta again is bytewise
idempotent. Reference checking preserves all 2,041 earlier nodes and checks 2,075.
The positive proof still contains 2,828 steps. Sidecars, reference and validation
artifacts add storage beyond the delta; these figures are not peak RAM.

## Validation and resumption

All **176 relevant tests** pass, including shared original leaves, empty retained
frontiers, pending split precedence, cold forced-target resumption without
reprobing, deterministic ranking, stale-negative rejection and existing graph,
proof and transformation checks. Independent reconstruction with new recognition
disabled rechecks the checkpoint, positive proof and new records in **33.09457 s**.
No new Lean refinement or complete cold negative-catalog audit is claimed.

Resume **`experiments/results/cnf-original-warm/report.json`** through
`experiments.continue_cnf_original_warm.restore_checkpoint`, retaining all five
evidence lists **(1, 42, 156, 14, 1)**. Report SHA-256:
`1af9073c8902a2740fd596987f29544ff4ef90ebe7200169cf30361b6ea30df7`.

Reproduce with `python3 experiments/continue_cnf_original_warm.py NEW_DIRECTORY`;
use `--parent REPORT` for a compatible later checkpoint. Independently restore
and extract the split paths with
`python3 experiments/validate_cnf_original_warm.py DIRECTORY`.

## Next target

The single open split leaf has SHA-256
`ef925b9a7d10a3bab64accecd2ce12015dfa400b13bc949f39781e28c55069f8`.
At ordinary offset 12, six candidates remain: **18, 20, 23, 24, 28, 29**.
The best already saved pair is **local variable 12**, with one closed child and
one missing 28-variable / 281-literal cofactor. Compare promoting this known
closed-cofactor split against exhausting the remaining ordinary probes, charging
candidate recognition and checking as well as acquisition, refresh and storage.
Retain the forced-reduction case 1189 as a contrasting control; early splitting
could discard an opportunity for a cheaper forced step.

Only two selected splits are studied here. A one-closed-child pattern keeps one
open obligation on these steps; arbitrary CNFs need not provide such a child,
nor a short chain of them. Full coverage, compact representation and uniformly
efficient construction for unrestricted SAT remain open obligations.
