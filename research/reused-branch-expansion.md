# Expansion with a previously closed cofactor

This checkpoint continues the matched batching experiment on case 30, one of
83 reused development inputs. It ranks all 21 saved pairs and selects normalized
variable 7. Its true cofactor is the existing empty-CNF terminal. Only its false
cofactor needs new recognition. Both branches share one allowance of 32 distinct
admissions, and the new split is retained alongside all earlier alternatives.
This is exact saved-trace conditioning, not a new tractability theorem or a
proof that this split has minimum total cost.

## Structural progress

| Stage | Variables | Clauses | Literal occurrences |
|---|---:|---:|---:|
| Open split source | 25 | 99 | 304 |
| False cofactor | 24 | 94 | 287 |
| Binary-path deletion | 24 | 92 | 281 |
| Elimination, unresolved leaf | 23 | 93 | 288 |
| Reused true cofactor | 0 | 0 | 0 |

Three new inventory nodes retain the binary-path reduction, elimination and
unresolved terminal. The true cofactor costs no new recognition admission.
There are no pending children. Structural coverage stays **58/83**, also without
growth exceptions. No newly recognized original or tractable family is claimed.
The false cofactor remains a structural obligation even though the empty true
cofactor already witnesses SAT for the source. The independent reference solver
checks source and child decisions and restores each successful child model.
Its answers remain separate from the structural coverage count.

Elimination reduces support but increases clauses from 92 to 93 and literal
occurrences from 281 to 288. The final leaf even has one more literal occurrence
than the immediate false cofactor. This rules out using variable reduction alone
as evidence of monotone formula-size or runtime improvement.

## Saved propagation and costs

The chosen pair refers to indices 4 and 5 of the first ordinary window from the
previous batch. Neither assumption needs fresh propagation during acquisition.
The matched local control compares checking those references with acquiring two
fresh unit-closure traces and checking the same canonical child bindings. Saved
replay takes **0.00070 s**, fresh propagation/checking **0.00091 s** in this one
measurement. Reuse avoids 1,712 propagation-literal visits and reduces restriction
visits from 1,824 to 1,216, but reads 6,914 bytes of trace payload. Both arms replay
four simplification checks. This is a local operation comparison, without timing
replications or a whole-solver speedup claim.

| Pipeline work | Seconds |
|---|---:|
| Restore parent | 21.22073 |
| Prepare checked routes and roots | 65.75065 |
| Navigate and rank retained pairs | 0.08981 |
| Acquire the missing cofactor and attach the split | **0.02474** |
| Compose coverage and diagnostics | 0.15839 |
| Export immutable delta | 5.16632 |
| Full inventory audit | 106.37684 |
| Cold route reconstruction | 63.97337 |
| Reference acquisition / cold proof replay | 0.02246 / 0.77400 |
| Complete pipeline, including remaining I/O | **271.17740** |

Independent validation and manuscript compilation are additional. The new
recognizers still perform work: the acquisition ledger includes 36 probe attempts
and reports 12 learning-continuation probe attempts. These counters are not added
as disjoint operations. Reusing the selected source pair does not eliminate
probing inside recognition of newly normalized child formulas. Neither the
three-state admission count nor reduced support bounds all CPU or retained bytes.

SQLite grows **49,152 bytes** to **770,338,816 bytes / 41,758 pattern nodes**.
All previous rows survive, including **91 ordinary windows / 133 continuations**;
this run adds no ordinary probe row. The new delta is **118,784 raw / 4,841
compressed bytes**. The saved split is a separate **1,641-byte compressed sidecar**;
selection, diagnostics, coverage and reference archives are additional. Peak RAM
is unmeasured, and this is no competitive end-to-end timing comparison.

The independent reference solver confirms **SAT for both cofactors and the
source**, with checked canonical transport and lifted models. Its archive retains
all **1,977** previous nodes within **1,998** nodes. The reference database is
**14,733,312 bytes**, compressed to **975,830 bytes**. These individual answers do
not provide a uniformly efficient structural rule for the unresolved family.

## Next expansion and validation

The new source has 23 variables, 93 clauses and 288 literal occurrences. Its next
ordinary block is **7, 9, 16, 17**, with 17 candidates remaining. These numbers
refer to the new leaf's normalization; use the exact source in the saved profile.
Compare its already saved cofactor pairs and any checked common-value/equivalence opportunity
before further probing. The preceding batch found the chosen reusable branch in
its first window, so exhausting every ordinary candidate is not a prerequisite
for a justified split. Use one shared admission allowance across subsequent
local steps and stop for a better retained route when warranted.

The four saved pairs are **5, 6, 11, 13**. Their checked ranks, ordered by
uncovered children, missing children, maximum support and total literal count,
are **[2, 2, 20, 376, 5]**, **[2, 2, 21, 410, 13]**,
**[2, 2, 22, 283, 6]** and **[2, 2, 22, 417, 11]**. Each needs two missing children;
this rank alone does not estimate their downstream acquisition cost. Ranking
takes **0.01104 s** in cold validation. No common-value/equivalence rewrite is
found among these pairs, and no affine equation is directly extracted. The wider
queue retains **17 ready learned bases / 88 candidates**.

The exact unresolved source has SHA-256
`a38c8326bbc493edae23be08aa73a85b288d74cf5a80dde578d126891e21ae92`.
Independent cold replay passes in **171.36780 s**, additional to the pipeline,
with fresh recognition, probing, learning and affine discovery disabled. It
confirms zero new admissions for the reused branch, preserved evidence, all new
states, reference answers/model lifts and unchanged reconstructed bytes.

Resume `experiments/results/cnf-reused-branch/report.json` through
`continue_cnf_reused_branch.restore_checkpoint` and `routes_for`. Preserve all
five evidence lists: **1 rewrite, 42 learned bases, 156 augmented blocks, 11 saved
splits and 1 affine family**, together with earlier sidecars. Follow the new
split descendant rather than restarting the exhausted 25-variable source.

The targeted 37-test suite covers both cofactor obligations, shared admission
limits, pending resumption, cold reuse, composition and affine-route preservation.
Independent validation reconstructs and reranks the parent, verifies every new
node and the full resulting coverage, checks all five evidence lists, and
replays the retained reference DAG and model lifts with fresh discovery disabled.
The full inventory audit and unchanged-byte checks cover preserved history.
Existing Lean results remain unchanged; this run adds no new refinement theorem.
