# Deeper conditional structure closes the 59-variable frontier

Updated 2026-11-16. This follows the [incremental split-checking study](incremental-split-checking.md)
and continues its largest unresolved query, case 16, from the complete preserved
1,154-pattern / 96-pair union. It is adaptive development work on the existing
24-input corpus, not a new holdout or an unrestricted-SAT result.

## Structural finding

The four saved pivots at the selected 59-variable source have eight acquired
branches. Following their stored internal reductions gives eight distinct
unresolved keys, of sizes 54--58 variables. There is **no exact frontier sharing**
between these eight states. Equal sizes do not make them interchangeable; no
semantic-equivalence or isomorphism search is implied.

A new optional work selector follows those saved reductions and commits to one
split at each unresolved source. It initially chooses the saved source pivot 7
by the total unresolved literal count of its existing branches, then refines the
smallest-support remaining obligation with a shortest-clause candidate. It keeps
choices across interrupted batches, merges exact repeated frontier keys, and
checks closure through the complete route graph. The choices schedule work; all
semantic rules and proof checks remain the previously frozen implementations.

This nested policy covers case 16. A control tries **all 55 remaining variables**
at the original 59-variable source, in the same shortest-clause ordering. Together
with the four prior choices, all **59 single-variable pairs** have both children
present, but **none closes under that recognizer and flat history**. The control
finishes without exhausting a recognition allowance. This finite contrast shows
why repeating one-level acquisition is insufficient here. It is not a lower bound
on SAT solving or on other preprocessing.

## Exact proof and reuse

The original input has a checked **286-node positive proof**: **12 conditioning
nodes, 265 unary reduction nodes and 9 distinct family leaves**. The conditional
depth is at most **five**. The conditioning variables are branch-dependent and
expressed in changing local coordinates after reductions; this is not a common
set of five original variables or a claimed minimum-depth certificate.

The unary reductions consist of **130 eliminations, 80 probe rewrites, 52 binary
path reductions and 3 polarity changes**. Family leaves include 2-CNF, Horn,
zero-valid and one-valid formulas, plus the empty formula and contradiction;
recognition overlaps are retained. The proof has thirteen leaf occurrences when
unfolded. Exactly one node is shared across paths: the canonical contradiction,
used five times. Thus 290 unfolded step occurrences compress to 286 distinct
nodes. This is useful exact terminal reuse, not evidence of large nonterminal
sharing across SAT categories.

The nested run adds **11 source pairs** beyond the initial saved split. Its
thirteen acquisition attempts include two resumptions of unfinished pairs, which
require no repeated source-assumption generation. Batches store **126, 122 and
27** new patterns. The final batch reuses its saved pair, adds 27 patterns and
215 probes, and closes the original without another source assumption. All 248
patterns from the two earlier incomplete batches remain available.

## Matched bounded comparison

Both workflows start from the same complete union. Each batch allows 128 distinct
recognition admissions and at most sixteen pair attempts; up to 32 explicit
source-assumption closures are separately charged. There are at most four
batches. Work stops on original closure or, for the control, exhaustion of all
source variables. Two repetitions reverse workflow order and reproduce identical
pattern/pair digests and outcomes. Equal limits do not mean equal actual work.

| Continuation cost | More first-level pivots | Nested refinement |
|---|---:|---:|
| Completed batches | 4 | 3 |
| Case 16 covered | No | Yes |
| Corpus structural coverage | 5/24 | 6/24 |
| Added source pairs | 55 | 11 |
| Fresh explicit source assumptions | 110 | 22 |
| Admission occurrences | 272 | 283 |
| Distinct admitted / new stored patterns | 272 / 272 | 275 / 275 |
| Fresh probes | 2,291 | 2,403 |
| Mean local expansion seconds | 3.54080 | 1.40774 |
| Mean initial reconstruction seconds | 3.61391 | 3.57977 |
| Mean cold replay seconds over all batch archives | 18.60694 | 12.84323 |
| Mean archive compression seconds | 1.92378 | 1.34494 |
| Final working SQLite bytes | 28,143,616 | 25,976,832 |
| Final compressed archive bytes | 1,398,397 | 1,265,228 |

The nested policy uses **more probes and slightly more pattern states**, but fewer
source assumptions and less local time. Its lower database size accompanies fewer
large split records, despite more pattern rows. Eight repeated admission
occurrences arise across its capped restarts. Both first nested batches reach
the state limit; the third completes. The flat control hits only its pair limit
before exhausting candidates. Unknown coverage is never classified as UNSAT.

Local expansion includes scheduling, source closures, child recognition, registry
and coverage maintenance, and row-preservation audits. Setup, cold checking and
compression are separately timed. Whole-corpus proof/report construction is
outside that local timer; do not sum these phase means into an end-to-end claim.
A separate fresh-process lifecycle control includes this remaining bookkeeping
and records process peak RSS. Its single-run measurements and limitations are
preserved in the result directory; they do not replace the paired local means.

| Supplemental whole-stream measurement | Flat | Nested |
|---|---:|---:|
| Wall seconds, including every batch archive and cold replay | 28.36860 | 18.75701 |
| Other bookkeeping seconds outside named phase timers | 0.41223 | 0.32124 |
| Peak process RSS, bytes on macOS | 449,069,056 | 371,310,592 |

Each control reproduces its workflow's batch databases, operations and proofs
exactly. Interpreter/import startup and the final resource report are outside
the stream timer; peak RSS includes imports and all phases. These are one-process
observations with different amounts of completed work, not an isolated cache
memory comparison or an asymptotic resource guarantee.

## Persistence, validation and limits

`experiments/results/cnf-nested-refinement/checkpoint.json` retains the union of
both workflows: **1,701 patterns / 162 pairs / 17 missing children**, with a
**352-step positive proof** for **6/24** originals. Eighteen remain unknown.
The new pattern sets of the two workflows have **zero overlap**; all 547 new rows,
including the 272 rows from the unsuccessful flat control, remain preserved.
The union occupies **32,346,112 SQLite bytes**, compressed to **1,537,733 bytes**.
The seventeen missing children are inherited obligations elsewhere in the corpus;
case 16's selected nested proof is complete.

Restore with the unchanged `experiments.validate_cnf_bootstrap.restore_checkpoint`
helper. Exact originals, policies, root bindings, pair traces, variable transports,
proofs, pending obligations and source hashes are checked without acquisition.
Every primary batch archive is independently replayed; the nested scheduling
choices reconstruct the same frontier after cold reopening. All **345 inherited
and new tests pass**, including interrupted-pair resumption and persistence before
child admission. The prior sources, artifacts and 64 manuscript proof blocks are
unchanged. No new Lean refinement or SAT/UNSAT verdict is asserted.

## Next target

Continue from the **new union**, not the smaller successful nested-only archive.
Case 17 is the next largest previously measured unresolved query: its selected
component has **60 variables, 255 clauses and 765 literals**. Test whether the
same conditional-refinement strategy transfers, keeping the already acquired
choices, recognition work and failures. Case 22 is another control.

The broader gap is predicting which reductions and adaptive branches reveal
known families before paying their acquisition cost. The current success does
not establish a uniformly small conditional depth, compact closure, or efficient
minimum-depth recognition for arbitrary CNF. With 265 unary steps in this proof,
retained reduction chains also remain a concrete storage and checking target;
any compressed chain must preserve intermediate source bindings and model lifts.
