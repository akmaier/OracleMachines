# A saved conditioning pair completes the transfer stream

The 42-input transfer stream now has **42/42 checked structural coverage**.
The last original input was a 48-variable, 204-clause random CNF. Its saved
selected frontier was a connected **38/165/502** residual. An external split on
residual variable **14** closes both children with **13 new pattern records and
30 fresh probe attempts**. The original root is justified through its existing
ancestors; no historical node or stored closure flag is rewritten.

This is adaptive completion of a finite development stream. It is not a new
holdout result, a uniformly efficient SAT algorithm, or a new SAT/UNSAT verdict.
The older 83-case and 1,497-input checkpoints remain unchanged.

## What the candidate comparison establishes

The residual already contains four checked, clear, top-level assumption pairs.
The initial policy ranks pairs by uncovered/missing distinct children, then
maximum cofactor support and total literals. It chooses variable 6, whose raw
cofactors have **36/142/423** and **34/140/406** variables/clauses/literals.
That split closes its true branch but leaves a **35/139/418** residual on the
false branch. Seven new records and 45 probes therefore make progress without
closing the original.

A separately frozen supplemental comparison tests **all four saved pairs**,
each from the same full history and under one complete 32-admission allowance.
Two repetitions reverse order. Every trial returns without a cap; incomplete
coverage is a structural outcome of this fixed policy, not an interrupted run.

| Split variable | Initial rank | New records | Fresh probes | Remaining selected frontier |
| ---: | ---: | ---: | ---: | --- |
| 6 | 1 | 7 | 45 | 35 variables, 418 literals |
| 14 | 2 | 13 | 30 | None: both branches covered |
| 27 | 3 | 9 | 29 | 35 variables, 469 literals |
| 37 | 4 | 9 | 84 | 33 and 34 variables, 843 total literals |

All raw pairs have the same maximum cofactor support, 36. Variable 14 has **863
cofactor literals**, against 829 for variable 6. Smaller cofactors did not predict
better eventual coverage. Nor did fewer probes alone: variable 27 uses only 29
but remains open. This is a counterexample to using either statistic as a reliable
minimum-expansion criterion, not evidence against their possible heuristic value.

On variable 14's false branch, seven probe reductions expose two independent
2-CNF components: **2 variables / 1 clause / 2 literals** and **5 / 4 / 8**. The
true branch uses three probe reductions and reaches the empty clause. Both
branches are checked, including their source-variable transports and saved unit
reasons. The original's expanded positive proof has 48 steps. The full stream
uses 33 early-family certificates and a 133-step positive graph for nine ordinary
roots. The branch contradiction does not make the unrestricted SAT problem UNSAT;
no unsupported conclusion is drawn about other inputs or residuals.

## Acquisition, reuse and cold costs

The successful pair's mean local expansion is **0.03200 s**, after **1.12121 s**
for restoring and checking the full history. Finding it by the measured four-pair
comparison charges **38 admissions, 188 fresh probes, 0.18237 s local expansion
and 4.52314 s startup per repetition**, plus selection and separately recorded
compression/replay. Quoting only the winning pair would omit candidate-discovery
cost. The initial selection phase takes 1.03376 s including restoration and root
checking. Across both initial-control repetitions and both four-pair repetitions,
all 556 fresh probe attempts remain recorded; inherited oracle construction is
also a prior cost, not free work.

The initial selected-pair control compares full history with the selected source
row alone. Both inherit its checked assumption traces. Full history saves **one
terminal record**, but saves **zero fresh probes**: 7 versus 8 new records and
45 probes in both arms. Mean local expansion is **0.04201 / 0.04092 s** and cold
startup **1.08738 / 0.00576 s**, respectively. This does not show a total-cost
benefit from loading the full history. The source-only control is not wholly
unprepared solving and cannot replace the original-root history. Retaining all
historical rows remains necessary for resumable research, while selective
verification is a separate opportunity.

Saved unit closures avoid reacquiring the two source-assumption traces. A matched
micro-control measures **0.00127 s replay** against **0.00145 s fresh propagation
plus checks** for the initial pair. This single tiny timing is not a reliable
speedup estimate, and it excludes descendant acquisition and full startup.

All alternatives are merged without conflicting or replaced rows. The union
keeps **443 inherited + 34 distinct new = 477 patterns**, plus all four split
records. The 38 independently acquired records overlap in four entries. The
union occupies **7,688,192 SQLite bytes / 412,774 gzip bytes**, compared with
**7,200,768 / 386,822** in its parent. The winning branch alone would add only
13 records, but discarding failed trials would lose reusable evidence.
Peak RAM is not measured; two repetitions and this one residual establish no
broad runtime or memory bound.

## Validation and next investigation

All **327 relevant tests** pass, including new zero-budget, partial-acquisition,
restart, both-polarity and checkpoint-scope checks. Independent reconstruction
checks twelve trial archives and the merged checkpoint, with acquisition disabled.
It binds each of the 42 original sources to its family certificate or positive
root. All 2,950 inherited artifacts, 47 manifests and 166 earlier source files
remain unchanged. The manuscript's 64 proof blocks remain unchanged; no new Lean
refinement theorem is asserted.

Use `checkpoint.json` as the next prepared state. It preserves unsuccessful
alternatives as well as the successful split. There is **no unfinished original
in this 42-input stream**; do not restart the previously selected variable-6
branch as though the original were still uncovered. Its negative result remains
useful for selection research.

The next structural gap is **predicting useful propagation cascades and component
exposure before paying for every candidate**. Compare cheap interaction features
or small checked lookahead budgets on newly frozen inputs, against current
size-based ranking and equal-budget candidate enumeration. Retain lookahead
profiles so selection work can be reused in acquisition, and charge checking,
invalidations and persistence. New motifs should include unresolved reduced
cores, not only sources reducible to known families before probing. The present
four-pair success supplies a concrete counterexample and candidate signal, not a
proved universal selector.

A supporting runtime gap is selective cold verification: about a second of full
history checking precedes tens of milliseconds of local expansion. Test reuse
of source-bound checked evidence without confusing a positive-proof-only bundle
with a complete discovery checkpoint. Profile persistence for interrupted work
also remains open, but is not needed to finish this now-complete stream.

```python
from pathlib import Path
from experiments.validate_cnf_transfer_split import restore_checkpoint
report, splits, checked = restore_checkpoint(
    'experiments/results/cnf-transfer-split/checkpoint.json',
    Path('/tmp/new-transfer-split-history.sqlite3'))
```

The destination must not already exist. Validation regenerates evidence reports;
copy this immutable result directory before rerunning it. Producer commands and
all measured costs are recorded beside the checkpoint.
