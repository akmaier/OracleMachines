# Turning clear probes into reusable cofactor plans

The [retained-learning batch](retained-learning-batch.md) left a ten-variable,
51-clause residual as the smallest selected open target. Its last ordinary probe
is clear. Repeating unchanged single-variable lookahead therefore cannot provide
a failed-literal reduction once the remaining variables are accounted for.
The useful information is the pair of simplified cofactors already established
by each saved assumption trace.

## Exact recomposition

For a source formula F and variable x, a checked unit trace under x=b produces
a residual R_b and a partial assignment U_b containing x=b and the derived
units. In the original source coordinates,

    F = (U_0 and R_0) or (U_1 and R_1).

Here an assignment denotes the conjunction of its literals. The equality is
logical equivalence: restriction splits all assignments by x, and each checked
unit is forced in its branch. Unit simplification preserves all models after
those assignments are restored. The branches are disjoint because they assign
opposite values to x. In particular, SAT(F) is SAT(R_0) or SAT(R_1).

The structural coverage rule requires plans for **both** cofactors. One branch's
SAT answer may decide satisfiability, but it does not certify complete structural
coverage of this partition. A missing child leaves the split pending. Even when
both cofactors normalize to the same key, both edges and their separate variable
transports are retained. Model lifting restores the selected branch's units and
checks the full source formula.

`cnf_trace_split.py` references two opposite, clear, top-level source traces.
Each reference resolves to an existing pattern, ordinary window or continuation
record. Nested traces on an augmented formula are ineligible. The checker verifies
the source binding, both assumption values, unit reasons, strict support reduction
and both canonical child bindings before exposing a route. This extends the
existing exact conditioning mechanism; it is not a new tractable SAT category.

The external split adds a conditioning step beyond the frozen recognizer's old
depth policy. Its children use the source's remaining internal depth. This is
additional explicitly charged expansion, not evidence that the old depth-two
recognizer covered the input all along. Repeated external splits can still
produce exponentially many states.

## Choosing and charging a split

The experiment selects the smallest acquired open leaf below retained learned
targets. It finishes ordinary probing under an eight-advance, one-source,
32-state cap. The selected experiment requires the resulting stream to be clear;
a different outcome stops this experiment rather than silently changing policy.
All binary-variable assumptions and the no-unit-trigger condition for other
variables are checked before the split is selected.

At most eight saved variable pairs are ranked by:

1. The number of distinct child keys not already structurally covered.
2. The number of distinct child keys absent from the current history.
3. Maximum remaining support, combined literal count and source variable number.

Canonical equality enables exact reuse. The ranking only predicts recognition
cost; it neither proves a globally cheapest split nor searches all possible
inference methods. It charges source-record lookup, checking, reconstruction,
normalization and coverage queries. At most 32 new recognition states may be
entered for the chosen pair. Completed work survives a partial acquisition.

The split record is archived before acquisition. It stores references and child
bindings, not duplicate unit traces. A matched control freshly propagates the
same two assumptions, checks the same cofactors and compares exact child
identities. Both arms replay the unit reasons twice; the saved arm also resolves
its source references. This is a small, warm cofactor comparison, not a whole
solver benchmark or a stable timing estimate from repeated trials.

## Evidence and reproducibility

The preserved pilot is `experiments/results/cnf-small-target-pilot.json`. It
records the clear last probe, unsuccessful paired consequences, a two-clause
learned batch whose six-variable augmented pool remains clear, and five cofactor
candidates. Its first exploratory helper call passed a clause list where full
batch records were required; the resulting TypeError and correction are recorded.
The pilot informed the chosen experiment and is separate from its timing.

Four regression tests check exhaustive source/cofactor equivalence on all 1,024
assignments of the ten-variable fixture, lifting of every satisfying canonical
child assignment, partial acquisition, cold reuse, forged references/edges and
two branches sharing one canonical child. All 581 Python tests pass. This is
Python verification and finite testing; no new Lean theorem is claimed.

From the repository root, with a fresh output directory:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/cnf-trace-split-tests.log 2>&1
python3 experiments/compare_cnf_trace_split.py /tmp/cnf-trace-split-reproduction
python3 experiments/validate_cnf_trace_split.py /tmp/cnf-trace-split-reproduction --test-log /tmp/cnf-trace-split-tests.log
```

The parent checkpoint is fixed in the runner. Restoration returns the parent
rewrites, learning bases and augmented continuations plus the new split records.
Construct `ContinuedLearningRoutes` from the first three lists, then call
`cnf_trace_split.attach` on each split before composing coverage. Omitting this
external layer loses the new route. All old eight-table rows and reference proof
rows remain immutable; the new reference archive is a full extended snapshot.

## Measured result, 13 November 2026

Coverage rises **52/83 -> 53/83**, including the growth-exception ablation.
Case **2** (`holdout3`, n32, original index 894) gains a complete structural plan
and an independent **SAT** witness. This historical group name does not make it
an independent holdout. The selected ten-variable source and both exact cofactors
are independently SAT as well; neither branch is discarded on that basis.

The remaining ordinary variable, 8, yields two clear attempts. Together with
the eight earlier attempts, these cover both polarities of all five binary-clause
variables (2, 3, 5, 6, 8). Variables 1, 4, 7, 9 and 10 cannot start unit propagation
under one assignment. The checker therefore certifies a **single-assumption unit
refutation obstruction** on this source. This does not exclude stronger inference
or decide SAT by itself.

All five retained pairs are ranked; every candidate has two distinct, absent
cofactor keys, so this trial has no pre-existing child-key hit. Every pair has
maximum residual support nine. Combined cofactor literal counts are 245, 246,
261, 282 and 291, selecting variable **5**. Its two source traces were already
in the original pattern record; the new variable-8 trace is not needed to justify
the split. Recognition of the chosen cofactors adds **five pattern nodes** and
uses 32 additional internal probe attempts. No admission cap binds.

The single matched control records **0.50192 ms** for saved-proof replay versus
**0.46004 ms** for fresh propagation and checking. The saved arm avoids two
fresh assumption traces and 519 propagation literal visits, but reads 10,454
bytes of referenced source payload. Both arms perform the same four unit-trace
checks and reconstruct the same cofactors. This small, unreplicated timing does
**not** demonstrate faster replay. Retaining proof evidence and avoiding search
operations do not automatically reduce elapsed time.

| Phase | Seconds |
| --- | ---: |
| Restore parent | 9.71424 |
| Prepare routes and choose the leaf | 66.51807 |
| Final ordinary probe and exhaustion advance | 0.00209 |
| Check exhaustion and rank five saved pairs | 0.01640 |
| Saved-trace control / fresh control | 0.00050 / 0.00046 |
| Persist split record | 0.00044 |
| Acquire and check cofactor plans | 0.01348 |
| Compose and diagnose | 0.11091 |
| Full cold inventory audit | 107.44875 |
| Cold routes and plan replay | 63.68636 |
| Seed reference archive | 0.01321 |
| Acquire/reuse reference answers | 0.02136 |
| Check all reference proofs cold | 0.74932 |
| Complete pipeline, including export and other I/O/checks | **263.25700** |

The full 581-test run costs 81.516 seconds separately. Preparation and cold
verification still dominate; there is no demonstrated whole-solver speedup.
Standalone validation takes **148.83131 seconds**, including reconstruction of
pre-acquisition candidate availability and final cold replay. It performs no
fresh probing and leaves the final history and reference database bytes unchanged.

Working SQLite grows **65,536 bytes** to **768,663,552 bytes** and retains every
old row. It now has **41,664 pattern nodes**, **80 ordinary windows**, and the
unchanged 108 ordinary continuations. The 41 learning bases and 150 augmented
blocks remain intact. The additive database delta is 126,976 bytes / 5,293 gzip
bytes. The external split is 8,594 / 1,050 bytes; diagnostics are 316,760 / 43,756,
and the coverage certificate 1,627,993 / 263,534. These external artifacts are
not included in working SQLite size.

All **1,156** inherited reference proof rows survive; the extended reference
archive has **1,175** checked nodes and occupies 8,900,608 bytes / 586,037 gzip
bytes. It remains a full snapshot with physical duplication of old proof rows.
Peak RAM is unmeasured. Earlier experiments, manuscript, Lean and the 902/985
prepared study remain unchanged.

## Next opportunities

1. **Rank saved clear pairs on the four remaining acquired open targets.** Their
   selected leaves have 33, 33, 36 and 38 variables. This split mechanism needs
   a checked pair, not exhaustion of every other variable; do not repeat all
   lookahead merely to enable it. Compare the capped cofactor acquisition with
   continuing their ordinary or augmented probes, and retain failed candidates.
2. **Recheck the 18 previously ready bases and their 92 untried ranked variables.**
   Further work must load the new split records as well as the previous learning
   layer; restoring only the preceding batch would omit the latest coverage gain.
   Reapply the coverage filter before scheduling more blocks.
3. **Separate avoided propagation from actual runtime savings.** Shared decoding
   and validation of exact source records could remove local replay overhead.
   Full cold verification remains much larger. Neither optimization is measured
   here, and neither removes the potentially exponential number of future splits.
