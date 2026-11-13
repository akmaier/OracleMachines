# Complete a retained decomposition after ordinary probing is exhausted

2026-11-13. Structural coverage rises **57/83 -> 58/83**, also without
growth-exception routes. Completing the ten-variable residual closes development
case **73**, original **1444** (`subsumption_holdout3/n48`), with **48 variables
and 204 clauses**. Seven new recognition states suffice for this continuation;
all earlier reductions and proofs remain retained. These 83 inputs are reused
development cases, not a new holdout.

## Discovery, selection and exact recomposition

The [preceding continuation](original-frontier-probe.md) left ten variables,
44 clauses and 151 literal occurrences. The last ordinary candidate, variable
7, is clear in both polarities. Together with saved pairs for 10, 3, 5 and 6,
this supplies ten checked assumption traces for every variable occurring in a
binary clause. Variables 1, 2, 4, 8 and 9 occur only in clauses of width at least
three, so neither value can create a unit or empty clause and start propagation.
The retained portable certificate therefore establishes **no single-variable
assignment yields a unit-propagation refutation** on this exact CNF. It does not
decide SAT/UNSAT or exclude stronger inference.

All five saved pairs are ranked before acquiring any new cofactor. The rank is
uncovered distinct children, missing distinct children, maximum child support,
total child literals, then variable number. This heuristic selects variable 10,
with rank **[1, 1, 9, 96, 10]**. The true cofactor is already the empty CNF and
reuses a checked terminal; the false cofactor has nine variables and 31 clauses.
The reuse here includes that simple terminal, not an undisclosed hard solution.
Both branch plans are still required for structural coverage.
The chosen pair was available before the final variable-7 probe; that new probe
adds negative evidence but is not needed to justify this split. Moreover, the
empty true cofactor already supplies a satisfying partial assignment for the
residual. Acquiring the false branch serves the complete structural plan, not
a necessary step in a positive SAT decision. These objectives must remain
separate when comparing runtime with a conventional SAT solver.

| Stage of the false branch | Variables | Clauses | Literal occurrences |
|---|---:|---:|---:|
| Saved cofactor | 9 | 31 | 96 |
| Checked probe reduction | 8 | 26 | 79 |
| Binary-path clause deletion | 8 | 18 | 53 |
| First variable elimination | 7 | 15 | 48 |
| Second variable elimination | 6 | 10 | 25 |
| Binary-path clause deletion | 6 | 8 | 19 |
| Checked polarity change | 6 | 8 | 19 |

The final formula is Horn and zero-valid. The seven new nodes are one probe,
two binary-path reductions, two eliminations, one polarity change and one family
recognition. There is no pending child and no open descendant of any of the nine
retained splits. The three passes on case 73 added 21 recognition states to an
already substantial history; this count excludes the earlier acquisition of that
history and is not a bound on solving arbitrary 48-variable inputs.

The new ordinary window admits no recognition state. Both split branches then
share one 32-state admission allowance. A clear result is only used to justify
the next scheduling decision; the separate checked cofactor plans establish the
positive coverage result. Every certificate is bound to its exact normalized
source, and model transport retains the two branch assignments. Variable numbers
are local to each normalized residual.

## Remaining discovery gap

The saved split frontier is now empty. The selected original frontier has **27
open leaves across 25 originals**. Its smallest leaf is development **case 30**,
with **29 variables / 120 clauses / 362 literals**. Nine ordinary candidates
remain: **7, 10, 16, 18, 20, 21, 23, 28 and 29**. Compare the next four-variable
block with the saved pair ranks and the separate learned-clause continuation;
there is no need to exhaust probing before choosing a justified split.
The wider alternative queue still contains **18 learned bases / 92 candidates**;
earlier accounting also retains four augmented candidates on case 30.

No selected split is proved globally cheapest. Single-assumption exhaustion is
an obstruction to that inference alone, not a complexity lower bound. The Horn
terminal is an established tractable family; this continuation expands certified
structural coverage without establishing an efficient partition of arbitrary
SAT. Complete-plan checking from actual dependencies remains the main measured
runtime opportunity, alongside broader discovery on the larger residuals.

Resume `experiments/results/cnf-probe-split/report.json` with
`continue_cnf_probe_split.restore_checkpoint` and its imported `routes_for`.
Preserve all **five evidence lists**: one rewrite, 42 learned bases, 155 augmented
blocks, **nine splits** and one affine-family certificate, plus earlier lemma
sidecars. The current experiment requires an acquired open split descendant and
a final clear window; with that queue empty, the next runner must select from
the original-input frontier instead of rerunning this policy unchanged.

## Costs, persistence and validation

| Work | Seconds |
|---|---:|
| Restore previous checkpoint | 17.51568 |
| Prepare checked routes and roots | 66.55717 |
| Navigate retained split frontier | 0.00946 |
| Acquire and check the last ordinary window | 0.00181 |
| Construct and check the exhaustion certificate | 0.00620 |
| Rank all five saved pairs | 0.04998 |
| Acquire the cofactor plans | 0.01667 |
| Compose coverage and diagnostics | 0.14917 |
| Export immutable delta | 5.07017 |
| Full cold inventory audit | 108.42947 |
| Cold route reconstruction | 64.45513 |
| Reference acquisition / cold reference DAG replay | 0.04995 / 0.74115 |
| Complete pipeline, including remaining I/O | **270.70538** |

A preliminary probe/check preview adds **0.000241 s** of kernel time, recorded
separately with its exact source and counters. Surrounding preview file I/O is
outside that kernel measurement. The integrated pass repeats and charges this
probe. The acquisition above includes the descendant recognizers' own probes;
one new ordinary window is not a count of all inference work.

The matched local two-trace control is **slower for saved replay in this sample**:
**0.000430 s** versus **0.000349 s** for fresh propagation plus checking. Both arms
check cofactor bindings; the fresh arm performs two assumption traces. Preserve
this result rather than claiming that avoiding discovery always saves elapsed
time. A single sub-millisecond sample establishes neither a robust regression
nor a speedup. Historical acquisition, loading, verification and persistence
remain charged separately; this is not a competitive whole-solver comparison.

SQLite adds **90,112 bytes**, reaching **770,121,728 bytes / 41,749 pattern nodes**.
All previous rows survive unchanged. The 89 ordinary windows include the one
new clear record; all 128 continuation records are retained. The delta occupies
**147,456 raw / 5,411 compressed bytes**, with proof and diagnostic sidecars in
addition. The existing terminal is shared. No peak-RAM measurement or compact
closure bound is established.

Independent reference proofs establish SAT for the ten-variable source, both
cofactors and the original case, and validate model lifting. All **1,906** old
reference nodes survive within **1,940**. The reference database occupies
14,536,704 bytes; its full compressed snapshot occupies 956,430 bytes. Structural
coverage comes from the checked decomposition, not from these reference answers.

All **38 targeted tests** pass, including exhaustion certificates, clear-window
behavior, exact cofactor recomposition, partial acquisition, affine-route
preservation and model lifting. The full inventory audit covers 1,548 sources,
41,749 pattern nodes and 21,838 residual nodes and leaves the reconstruction
byte-identical. The independent validator reconstructs the parent and first
stages **only the checked clear window**. It ranks pairs before introducing the
new child nodes, avoiding a ranking contaminated by later acquisitions. It then
reconstructs the complete child checkpoint, checks both branch obligations,
coverage, growth ablation, every evidence list and the retained reference DAG
with fresh discovery disabled. Independent cold replay passes in **167.82586 s**
with unchanged checked reconstructions and reference bytes. This extra validation
time is separate from the pipeline table; its result is stored in `validation.json`.
Earlier full-suite and Lean results remain unchanged.

```sh
python3 -m unittest solver.test_cnf_original_splits solver.test_cnf_trace_split \
  solver.test_cnf_split_batch solver.test_cnf_split_frontier \
  solver.test_cnf_route_composition solver.test_cnf_affine_clause \
  solver.test_cnf_exhaustion_certificate solver.test_cnf_probe_window \
  solver.test_cnf_target_probe > /tmp/probe-split-tests.txt 2>&1
python3 experiments/validate_cnf_probe_split.py \
  experiments/results/cnf-probe-split --test-log /tmp/probe-split-tests.txt
```
