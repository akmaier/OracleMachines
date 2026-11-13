# A forced literal below a retained split

2026-11-13. Continuing the [original-frontier split](original-frontier-split.md)
reduces its open obligation from **13 variables / 62 clauses / 219 literals**
to **10 variables / 44 clauses / 151 literals**. Four new recognition states
suffice. Structural coverage remains **57/83**, also without growth exceptions.
The reduced formula is still unresolved by the structural inventory.

## What the checked reduction establishes

The scheduler follows the retained split of development case 73 (original 1444),
skips its closed sibling, and selects the acquired 13-variable leaf. Its earlier
ordinary probes covered variables 6, 9, 12 and 13. The next candidate block is
1, 4, 7 and 8. The first attempt, variable 1 set false, produces a checked unit
contradiction. Every model of this exact source therefore sets variable 1 true;
the rest of that candidate block need not be tested on the obsolete source.

| Stage | Variables | Clauses | Literal occurrences |
|---|---:|---:|---:|
| Previously open leaf | 13 | 62 | 219 |
| Restrict the forced literal | 12 | 48 | 165 |
| First variable elimination | 11 | 45 | 151 |
| Binary-path clause deletion | 11 | 42 | 137 |
| Second variable elimination | 10 | 44 | 151 |

The new inventory nodes are two eliminations, one binary-path reduction and
one unresolved leaf. The ordinary window stores the forcing certificate outside
that node table. All four admissions share one 32-state allowance. Neither this
allowance nor the smaller support bounds total CPU, retained bytes or peak RAM.
Child recognition performs additional probes and family tests; those costs are
included in the acquisition counters. One new ordinary-window attempt is not
the total number of probes performed by the pass.
The final elimination increases clause count; support reduction alone does not
imply a runtime speedup.

The final leaf has three binary clauses, 25 ternary clauses, ten width-four
clauses and six width-five clauses. Its ordinary candidate pool has one untried
variable, **7**. Original saved pairs cover **10, 3, 5 and 6**. Variable IDs are
local to each normalized residual; the earlier literal 1 does not identify a
fixed variable number in the original input. Reference answers and structural
coverage are recorded separately.

## Scope and next step

This is one adaptively selected residual of the same 83 reused development
inputs. It is not a new tractable class, an independent holdout result, or a
minimum-expansion construction for arbitrary SAT. It demonstrates that revisiting
probing after conditioning and elimination can expose a reduction absent from
the parent's exhausted probe stream. Invalidation is explicit: each certificate
is bound to its exact source CNF, and the reduced child has its own candidate pool.

Test the remaining variable 7 on the 10-variable leaf before another split. If
both polarities are clear, retain that negative result and rank its saved pairs
for exact conditioning. Do not restart the 13-variable source or treat its
unvisited variables as outstanding obligations after the forced reduction. The
wider learned-clause queue remains available. Complete-plan checking from actual
dependencies remains the main measured runtime gap alongside structural discovery.

Resume `experiments/results/cnf-original-probe/report.json` using
`continue_cnf_original_probes.restore_checkpoint` and its imported `routes_for`.
Preserve all **five evidence lists**: rewrites, 42 learned bases, 155 augmented
blocks, eight splits and one affine family record, plus earlier lemma sidecars.
Use the saved split frontier to reach the ten-variable residual; selected
original routes alone may expose its older parent.

## Costs, persistence and verification

| Work | Seconds |
|---|---:|
| Restore prior checkpoint | 16.70334 |
| Prepare checked routes and roots | 69.25253 |
| Navigate the saved split frontier | 0.00911 |
| Acquire the new window and four recognition states | 0.02000 |
| Compose coverage and diagnostics | 0.16348 |
| Export the immutable delta | 5.53181 |
| Full cold inventory audit | 115.65564 |
| Cold route reconstruction | 65.40336 |
| Reference acquisition / cold reference DAG check | 0.00717 / 1.06650 |
| Complete pipeline, including remaining I/O | **282.11723** |

A preliminary direct probe/check preview took **0.000614 s** and produced the
same source-bound forcing certificate. Its artifact and counters are retained
separately; the integrated acquisition reacquires and checks that result. The
preview timing covers the probe/check kernel, not its surrounding file I/O. The
report exposes that extra kernel cost rather than hiding it inside the main pass.
No matched whole-solver runtime advantage is claimed.

Working SQLite grows **57,344 bytes** to **770,031,616 bytes / 41,742 pattern
nodes**. All 41,738 old pattern nodes and every old table row remain unchanged.
One new ordinary probe window brings that table to 88 rows; the 128 continuation
rows are unchanged. The new delta is **126,976 raw / 6,225 compressed bytes**;
selection, coverage, diagnostics and other sidecars add storage. These are disk
sizes, not peak-RAM measurements. The full audit checks 1,548 sources and 21,838
residual nodes as well as every inventory node.

Independent reference proofs establish SAT of the 13-variable source and its
12-variable restriction and verify the lifted model. The reference archive
retains all **1,898** earlier nodes within **1,906** nodes, occupies 14,331,904
raw bytes, and has a 940,445-byte compressed snapshot. This does not turn the
unresolved ten-variable structural obligation into a recognized family. No new
original coverage gain is counted from a reference solver answer.

Twenty-nine targeted tests cover probe windows, continuation, split frontiers,
affine-route preservation and composition. The standalone validator reconstructs
both checkpoints with discovery disabled, rechecks selection, the new forcing
record, every saved evidence list, coverage and the growth ablation, and checks
reference preservation and model lifting. `frontier-profiles.json.gz` records
the precise next source and its remaining candidates. Its startup initially
failed on an incorrect module import before reading a checkpoint; the failure
log is retained and the import corrected. The solver and saved acquisition
artifacts were unaffected. Independent cold replay passes in **164.19006 s**,
with no new discovery and byte-identical reconstructed inventories and reference
archive after checking. Earlier full-suite and Lean results remain unchanged.

```sh
python3 -m unittest solver.test_cnf_target_probe solver.test_cnf_probe_continuation \
  solver.test_cnf_probe_window solver.test_cnf_split_frontier \
  solver.test_cnf_original_splits solver.test_cnf_affine_clause \
  solver.test_cnf_route_composition > /tmp/original-probe-tests.txt 2>&1
python3 experiments/validate_cnf_original_probes.py \
  experiments/results/cnf-original-probe --test-log /tmp/original-probe-tests.txt
```
