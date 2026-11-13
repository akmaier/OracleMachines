# Reusing later probes across retained learned formulas

The [preceding study](frontier-learning-continuation.md) closed one original by
continuing beyond the initial four-variable block of a learned formula. This
experiment applies that mechanism to the earlier retained learning bases. It
does not repeat their clause selection, initial probes or source graph search.
All inputs are reused development cases; the historical group names do not
make them independent holdouts.

## Selection, reuse and stopping

The scheduler classifies every saved base before discovery. Already successful
bases, covered sources, exhausted candidate pools and acquired but unresolved
targets are separate outcomes. Missing successful targets have priority for
resumption. Remaining candidates are ordered by variable count, literal count
and complete base digest, then visited in round-robin order. Clear blocks go to
the queue's tail. A successful block is saved before target recognition and
leaves this queue; its target receives a separate diagnostic if still unresolved.

This pass allows at most 144 advances, 128 distinct newly entered recognition
states in total, and 32 new states per target. The shared admission set is reset
only once. Partially entered states and completed descendants remain available
to subsequent targets. Reusing an already acquired state costs no new admission,
but its lookup and checking still consume resources. These limits do not bound
state size, processing time, reference solving or peak memory.

Each later block refers to its exact source-justified learning base. The existing
checker validates the base, learned clauses, clear prefix, augmented reason
indices and successful child binding. A clear block adds no coverage route.
Successful routes require the child to exist and the finite original-level
composition to discharge every premise. Structural closure and SAT truth remain
separate: the reference solver checks answers and source-model lifting.

Matched controls probe the original formula with each new augmented block's
variable order. They distinguish a propagation change from a ranking change.
They are additional measured work, not an equal-total-cost solver comparison.
Old controls and old blocks are inherited rather than rediscovered.

## Persistent state and reproduction

`continue_cnf_learning.restore_checkpoint` accepts the frozen frontier-learning
checkpoint or a chain of new batch reports. It checks parent hashes, code
fingerprints, immutable row deltas and logical table digests. Later checkpoints
append only new augmented blocks and controls. Exact base evidence stays in the
ancestor archives. The reference archive starts with the parent's proof rows;
all those rows must remain byte-for-byte equal after extension. Each archived
reference database is still a full snapshot, so physical archive duplication is
not eliminated.

The per-block journal is closed before target acquisition. On completion it is
checked against the compressed additions archive before removal. This provides
a retained acquisition trail, not a power-loss durability guarantee. A nonempty
output directory is rejected so failed runs cannot silently overwrite evidence.

From the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/cnf-learning-batch-tests.log 2>&1
python3 experiments/continue_cnf_learning.py /tmp/cnf-learning-batch-reproduction
python3 experiments/validate_cnf_learning_batch.py /tmp/cnf-learning-batch-reproduction --test-log /tmp/cnf-learning-batch-tests.log
```

For a later pass, use a new output directory and supply `--parent` with the
current report. The independent validator replays parent selection and final
coverage with discovery disabled, checks controls and admission accounting, and
reads all reference proofs. The timed pipeline separately audits every retained
inventory node. Earlier results, manuscript and Lean theorems remain unchanged;
this experiment makes no new arbitrary-SAT tractability claim.

## Measured result, 13 November 2026

Structural coverage rises **47/83 -> 52/83**, including the ablation that removes
growth-exception routes. The five new originals all have independently checked
SAT witnesses:

| Case | Historical group | Original index | Variables |
| --- | --- | ---: | ---: |
| 24 | equivalence_holdout3 | 1122 | 48 |
| 40 | selection_holdout3 | 1230 | 48 |
| 50 | core_holdout3 | 1301 | 48 |
| 66 | activity_holdout3 | 1409 | 48 |
| 81 | implied_holdout3 | 1483 | 48 |

Selection finds 36 ready bases, one covered source, one exhausted source and
three initially successful bases. The 144 advances add **141 blocks**: 131 clear,
nine forced and one equivalence. Three advances report an exhausted pool without
adding a block. There are **1,073 direct augmented attempts**, **1,088 control
attempts** and **484 target-recognition attempts**. The 1,908 earlier prefix
attempts visited by the manager are reused checked evidence, not new probing.

Six of the ten successful augmented blocks have clear same-variable controls;
four controls also find a forced value. Thus stronger propagation is demonstrated
for six reductions, not all ten. The five original-level gains require subsequent
target recognition and exact recomposition; this does not isolate their total
benefit against an equal-cost original-only policy.

All ten successful targets are acquired with **77 new pattern nodes**. Individual
targets require 3--21 new states, so neither admission cap binds and no child is
pending. Five sources become covered; five successful reduced targets remain
structurally open. The prior successful target stays covered.

After filtering again, **18 bases have 92 untried ranked variables**, nine bases
are exhausted, six sources are covered, five have acquired open targets, and
three were successful initially. The raw remaining queue has 23 entries, but
five of those have already consumed their final clear block. They should be
filtered as exhausted, not reported as unused probe candidates.

| Phase | Seconds |
| --- | ---: |
| Restore parent archives | 8.29531 |
| Prepare routes, bases and selection | 66.28319 |
| Later augmented discovery and checking | 0.62674 |
| Matched original-source controls | 0.39536 |
| New target recognition | 0.32568 |
| Acquisition journal writes | 0.01177 |
| Final additions archive | 0.01162 |
| Compose plans and remaining-target diagnostics | 0.11550 |
| Export and compress database delta | 5.09622 |
| Full cold inventory audit | 107.69215 |
| Cold route and plan replay | 63.57421 |
| Restore reference seed | 0.00396 |
| Reference acquisition/reuse | 1.50316 |
| Cold reference proof checks | 0.44728 |
| Complete pipeline, including other I/O and checks | **263.21369** |

The search loop costs 1.36258 seconds including its discovery, control,
recognition and journal subphases; do not add it again to those rows. Preparation
and cold validation remain the dominant costs. There is no measured whole-solver
speedup. All **577 Python tests** pass; full test timing is separate from the
experiment. Standalone validation adds **147.33912 seconds**, replaying both
parent selection and the final checkpoint with discovery disabled. History and
reference database bytes remain unchanged. Peak RAM is unmeasured.

The working SQLite database grows **1,044,480 bytes**, from 767,553,536 to
**768,598,016 bytes**, and retains all prior eight-table rows. There are now
**41,659 pattern nodes**. The database delta is 1,097,728 bytes / 50,784 gzip bytes;
new augmented records and controls are 278,612 / 26,411 bytes, diagnostics
570,524 / 89,389, and the coverage plan 1,549,676 / 254,490. These are separate
artifacts, not part of the quoted working SQLite size. There are 150 cumulative
augmented blocks, with the 41 learning bases and ordinary 79 windows / 108
continuations unchanged.

The reference archive preserves all **164** inherited proof rows and contains
**1,156** checked proof nodes after extension. Its full snapshot is 8,839,168
bytes / 581,450 gzip bytes. Reference work and storage are additional to structural
discovery. Neither the old 902/985 prepared study nor a fresh holdout corpus was
re-evaluated.

## Next targets

1. **Follow the smallest acquired open target.** Its selected leaf has ten
   variables and 51 clauses, with one ordinary ranked variable still untried.
   This is a cheaper immediate coverage opportunity than increasing all caps.
   Its exact leaf-key SHA-256 is
   `6821d9f8652000ef43ff5765000265227059c52aa2c253785a6fead41450f277`.
   Preserve the other four selected leaves (33, 33, 36 and 38 variables) and the
   exact source-to-target links in the diagnostics.
2. **Resume the 18 genuinely ready augmented bases.** Their 92 remaining ranked
   variables can be reached without new clause selection or repeated prefixes.
   A fresh filtered selection avoids wasting advances on the five stale queue
   entries. Retain original-source controls; four matched controls here also
   find forced values.
3. **Use exhausted formulas to test stronger inference, and reduce cold cost
   separately.** Do not repeat unchanged clear pools. A further learning layer
   needs explicit augmented-proof dependencies, or compare bounded conditioning.
   Dependency-local cold verification remains the largest runtime opportunity,
   but this study has not implemented or measured that reduction.
