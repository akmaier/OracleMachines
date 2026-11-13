# Follow a forced literal below the retained split

2026-11-13. One checked failed literal reduces case 30's acquired obligation
**27 variables / 111 clauses -> 25 variables / 99 clauses**, with **three new
recognition states**. Structural coverage remains **58/83**, including the
ablation of growth-exception routes. All prior evidence is preserved. This is a
continuation on reused development data, not a fresh holdout result.

## Comparison and exact continuation

The preceding checkpoint leaves a 27-variable, 111-clause, 342-literal source
below a retained split. Its four saved pairs are ranked before acquisition:

| Variable | Uncovered children | Missing children | Maximum support | Total child literals |
|---|---:|---:|---:|---:|
| 5 | 2 | 2 | 25 | 509 |
| 15 | 2 | 2 | 25 | 609 |
| 8 | 2 | 2 | 26 | 350 |
| 11 | 2 | 2 | 26 | 530 |

The next ordinary block would test **19, 24, 9, 13**. Both values of 19 are
clear. Setting **24 false** produces 21 unit reasons and a checked conflicting
clause. The resulting certificate forces **24 true**, leaving 26 variables,
106 clauses and 325 literal occurrences. Probing stops at this successful
reduction: variables 9 and 13 in the proposed block are not tried. These are
variable numbers in the normalized 27-variable residual, not the older source's
coordinates. In particular, its variable 24 need not denote the earlier split's
variable 24.

The force changes the proof obligation from two cofactors to one checked
restriction. Its negated assumption is refuted by unit propagation, and every
model of the restricted formula extends with the forced assignment. The stored
record binds the exact source, child key and variable transport. This is the
existing failed-literal rule, not a new tractability theorem.

| Stage | Variables | Clauses | Literal occurrences |
|---|---:|---:|---:|
| Open source | 27 | 111 | 342 |
| Forced restriction | 26 | 106 | 325 |
| Binary-path deletion | 26 | 97 | 292 |
| Elimination, unresolved leaf | 25 | 99 | 304 |

The three new inventory nodes are a binary-path reduction, an elimination and
an unresolved terminal. Elimination reduces support while increasing clauses
and literal occurrences relative to its immediate input. The resulting leaf
is still outside the recognized families and has zero directly extracted
affine equations. No new original closes. The larger retained split's empty
branch already witnesses SAT for its source; completing its other branch remains
a separate structural-coverage objective.

We prefer the checked unary restriction to acquiring the two missing children
of a saved pair. We have **not acquired competing split plans** in matched arms,
so this does not establish that the unary route is fastest or globally cheapest.
The saved ranks and unsuccessful variable-19 probes remain available for reuse.

## Costs and persistence

| Work | Seconds |
|---|---:|
| Restore parent | 19.40327 |
| Prepare checked routes and roots | 67.09237 |
| Navigate split frontier | 0.01079 |
| Rank four saved pairs | 0.01290 |
| Probe, check and acquire the forced residual | 0.02582 |
| Compose coverage and diagnostics | 0.15513 |
| Export immutable delta | 5.15142 |
| Full inventory audit | 108.74312 |
| Cold route reconstruction | 67.28829 |
| Reference acquisition / cold DAG replay | 0.02069 / 0.75754 |
| Complete pipeline, including remaining I/O | **277.21655** |

The direct source-bound preflight adds **0.00116 s** of probe/check kernel time;
it does not reconstruct the full inventory. Its surrounding file I/O is outside
that kernel measurement. The integrated run repeats and charges the probe.
Pipeline plus preflight kernel is **277.21772 s**. Independent validation and
manuscript compilation are additional. The acquisition includes the new
recognizers' own inference work; the three top-level assumption traces do not
count every probe in the expansion.

SQLite grows **57,344 bytes** to **770,236,416 bytes / 41,755 pattern nodes**.
All previous rows survive. The immutable delta is **122,880 raw / 6,081 compressed
bytes**, containing three pattern nodes and one forced ordinary window. There
are now **90 ordinary windows / 129 ordinary continuation rows**. Diagnostic,
selection and reference archives are additional. No peak-RAM reduction is measured.

Reference proofs independently confirm SAT for the source and restriction and
check the lifted model. They retain all **1,949** earlier nodes within **1,977**.
The reference database is **14,667,776 bytes**, its compressed snapshot **968,187
bytes**. Full inventory audit checks all 1,548 sources, 41,755 pattern nodes and
21,838 residuals with unchanged reconstructed bytes. The remaining gap concerns
structural discovery and total accounting, not a missing reference SAT verdict.

## Next step and validation

The remaining leaf has SHA-256
`37446243b3a595420b6ac833e6487c74a239f8d18a4a7c67d06401545cdb9063`.
Its saved pairs are **5, 6, 8, 11**, and the next ordinary block is **13, 15, 7, 9**.
There are **17** untried ordinary candidates on this exact source. Use the retained
split frontier; the former 27-variable source now reuses its successful forced
route and should not be probed again. The wider queue still has **17 ready learned
bases / 88 candidates**.

The next experiment should combine this discovery work with **bounded batching**:
several local steps and sources in one `cnf_target_probe.search` invocation,
sharing one admission budget and one restored/checkable history. Compare the
resulting proof records and coverage with the corresponding sequential prefix.
Do not reset the admission allowance per source. Reconstructing and auditing
the entire history for each individual window dominates the observed cost.
Batching may amortize that fixed work; its total saving and discovery-policy
tradeoffs still need measurement. Checking complete plans from their actual
dependencies remains the stronger open verification opportunity.

The targeted **33-test** suite covers forced continuation, clear-prefix reuse,
state/step/source limits, pending resumption, exact split checking, composition
and affine-route preservation. Independent cold validation reconstructs and
ranks the parent before adding the delta, then checks the child checkpoint with
fresh recognition, probing, learning and affine discovery disabled. It checks
all five evidence lists, every new admitted state, coverage and growth ablation,
the reference DAG, model lifts and unchanged reconstructed bytes. Independent cold replay passes in **174.55350 s**, additional to the pipeline;
its result is retained in `validation.json`. Earlier full-suite and Lean
results remain unchanged; no new Python refinement or unrestricted SAT bound
is claimed.

Resume `experiments/results/cnf-frontier-forcing/report.json` with
`continue_cnf_frontier_forcing.restore_checkpoint` and `routes_for`. Preserve all
**five evidence lists**: one rewrite, 42 learned bases, 156 augmented blocks,
ten splits and one affine-family record, plus earlier sidecars. The current
runner deliberately requires one forced block and is not a general scheduler
for an unknown clear outcome on the next source.
