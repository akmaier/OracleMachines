# Learning versus a saved split at an exhausted frontier

The previous checkpoint leaves an exact **22-variable / 90-clause** residual.
Saved clear traces cover both polarities of its 19 binary-clause variables. The
other three cannot start unit propagation. Ordinary single-assumption refutation
is exhausted on that source, and the retained pairs provide no implemented
common-value or equivalence rewrite. This experiment compares two ways to make
progress beyond that inference boundary.

Both arms start from `experiments/results/cnf-split-frontier/report.json`, with
all inherited nodes, learned records and five external splits. Selection is fixed
before either arm runs. Each arm uses fresh verifier caches and a **32-state
recognition allowance**, shared across all of its acquisitions. These allowances
do not equalize CPU time, propagation work or retained bytes. The 83 originals
are reused development cases; historical `holdout` labels do not make this an
independent test set.

The learning arm selects at most 16 binary clauses from all saved assumption
traces on the selected source. Explicit clauses and consequences of the current
binary graph are filtered, including consequences of clauses already selected.
Every accepted clause has a unit-trace proof on the original source before any
probe uses the augmentation. The first four augmented candidates are probed,
followed by at most eight continuation advances if the initial block is clear.
A successful reduction may acquire one target. Clear blocks are retained as
negative evidence, and missing targets remain pending obligations.

The split arm ranks at most eight saved opposite-polarity pairs by uncovered
children, missing children, maximum child support, total literals and variable
identity. It acquires both exact cofactors of the first ranked pair under the
shared allowance. A saved parent split and closed sibling can then be reused.
Structural closure requires both child plans. This ranking is a bounded heuristic;
it is not a proof of minimum expansion cost.

The preparation also checks the full reachability graph of the original binary
clauses and the implications proved by saved traces. A tree for each root proves
reachability; edge closure proves that no reachable vertex was omitted. This
diagnostic concerns the retained binary theory, not the entire nonbinary CNF.

Each arm retains its immutable SQLite delta, admission identities, coverage plan,
open frontier and proof records. Their union checks payload agreement and keeps
both unsuccessful and successful work. New learning targets are reported
separately because the selected split-frontier view does not enumerate every
external learned route. Independent reference solving checks original/augmented
answer agreement, cofactor recomposition, canonical child transport and lifted
SAT models. Reference proof nodes from the parent remain present.

The standalone validator reconstructs the parent and each arm, disables new
recognition and probing, recomputes the declared clause/pair selections, checks
continuation prefixes and pending obligations, and replays the union and reference
proofs. It requires unchanged reconstructed database bytes and zero new reference
expansions. The full inventory audit checks all stored nodes separately.

```sh
python3 -m unittest discover -s solver > /tmp/cnf-learning-split-tests.log 2>&1
python3 experiments/compare_cnf_learning_split.py /tmp/cnf-learning-split-reproduction
python3 experiments/validate_cnf_learning_split.py /tmp/cnf-learning-split-reproduction --test-log /tmp/cnf-learning-split-tests.log
```

Resume the new report with `compare_cnf_learning_split.restore_checkpoint` and
construct routes with `compare_cnf_split_batch.routes_for`. The returned evidence
includes all inherited and new learned bases, continuation blocks and splits.
Neither bounded probing nor repeated conditioning establishes a polynomial
construction or compact closure for unrestricted SAT. Peak RAM is unmeasured.

The first execution stopped at learning-arm delta export because an inherited
loader had already created the same temporary SQLite filename. Its completed
proof and diagnostic archives and traceback are retained under
`experiments/results/cnf-learning-split-export-failure`; it has no completed
comparison report. The runner now reconstructs inherited files in a separate
temporary directory. The comparison is rerun from the identical immutable parent.

## Results, 13 November 2026

The completed comparison retains **55/83 structural coverage** in each arm and
their union, also without the growth exception. No admission cap binds.

| Measure | Learned batch | Saved cofactor split |
| --- | ---: | ---: |
| New recognition states | 0 | 4 |
| Selected open leaf, variables / clauses | 22 / 90 | 19 / 84 |
| Local acquisition | 0.03825 s | 0.03446 s |
| Cold arm preparation, including database copy | 70.71 s | 69.09 s |
| Composition and diagnosis | 1.14644 s | 1.09532 s |
| Working SQLite growth | 0 bytes | 57,344 bytes |

The split uses variable **4** of the exact selected source. Its false branch
needs four states and remains open at the smaller leaf; its true branch was
already present and structurally closed. Both children are acquired. Pair ranking
adds **0.02471 s** to the split policy, so the local acquisition times alone do not
establish a runtime advantage. No general speedup follows from this single trial.

The new learned batch contains **16 clauses**. Its initial four candidates and
five continuation blocks at offsets **4, 8, 12, 16 and 20** are all clear; the
sixth advance reports exhaustion. There are no successful learned targets. The
full original-source implication graph also has no forced literal, nontrivial
equivalence or contradictory variable. Neither result excludes stronger learning.
The failed first run and the completed run produce byte-identical clause, block,
selection and split archives; no alternative outcome was discarded.

Cold replay certifies a stronger negative statement on the exact **106-clause
augmented formula**. Its **42 clear traces** cover both values of all **21 binary
variables**. The remaining variable, **12**, occurs only in clauses of width at
least three and cannot initiate unit propagation. Hence assigning any single
variable still cannot produce a unit-propagation refutation after this batch.
This proof is persisted in `validation.json` under `learned_obstructions`; it is
not inferred merely from a search-budget stop. No bound on stronger methods or
other learned batches follows.

Shared preparation costs **64.19 s**, navigation and graph discovery/checking
**0.05334 s**, and cold union composition **70.29 s**. The complete inventory audit
costs **117.76 s**. The successful pipeline totals **434.32 s**, including parent
restoration, independent arm preparations, checking, serialization, delta exports,
persistence and reference work. Each arm delta export takes about **5.6 s**, even
for the empty learning delta, because preservation checking scans the inherited
tables. These costs dominate the subsecond expansion. They are not the cost of
a single warm expansion. The aborted run and standalone cold replay are separate
costs. Per-call reference metrics are retained in the answer rows; wrapper
`counts` fields reflect the last solve call and are not aggregate operation totals.

The merged working database is **769,617,920 bytes**, with **41,710 pattern nodes**.
Only four pattern rows are added; every inherited row in all eight tables remains
unchanged. The 86 ordinary windows and 126 ordinary continuation records are
unchanged. External evidence now has **42 learned bases, 155 augmented blocks
and six splits**. The union delta is 126,976 bytes, compressed to **5,603 bytes**.
The empty learning delta still has SQLite schema overhead; its external proofs
also take space. Coverage, diagnostic and reference archives add storage beyond
the working database, and peak RAM remains unmeasured.

Independent reference proofs establish that the source, augmented formula and
both raw cofactors are **SAT**. Those answers do not count as structural coverage
of the remaining leaf. All **1,750** previous reference nodes are preserved within
**1,775** checked nodes (13,553,664 bytes, compressed to 883,411 bytes). Thus the
negative learning result is not a disguised UNSAT claim or a claim that the
source cannot be solved by another method.

All **589 Python tests** pass (88.787 s). Standalone cold replay takes **297.82 s**,
rechecks the selections, both isolated arms, their immutable union, references
and augmented obstruction, with recognition/probe discovery disabled and database
bytes unchanged. Its hashes bind the report, validation script and full test log.

## Remaining work

The exact selected **19-variable / 84-clause** leaf has ten untried ordinary
ranked variables: **6, 12, 13, 15, 3, 7, 14, 17, 18 and 19**. Its original profile
is `learning_clear`. Continue there through the retained parent split and closed
sibling rather than restart either exhausted 22-variable source. The alternative
queue remains **18 ready learned bases / 92 ranked variables**; other statuses
are ten covered, ten exhausted, three initially successful and one acquired open
target. Compare useful structural coverage against full incremental cost.

Dependency-local validation and delta export are separate high-cost gaps: a
four-node change currently triggers scans and replay of much larger retained
state. Any shortcut must bind its dependencies and preserve invalidation checks.
No new theorem or general tractability result follows from this experiment;
the manuscript and Lean development are unchanged.
