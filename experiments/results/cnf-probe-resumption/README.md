# Resume deeper probe blocks and identify exhausted reasoning

Acquisition checkpoint: `ffebba0`. Reproduce from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/oraclemachines-probe-resume-tests.log 2>&1
python3 experiments/continue_cnf_probes.py experiments/results/NEW-DIRECTORY --parent experiments/results/cnf-probe-continuation/report.json
python3 experiments/validate_cnf_probe_resume.py experiments/results/NEW-DIRECTORY
python3 experiments/cnf_probe_exhaustion.py experiments/results/NEW-DIRECTORY/report.json experiments/results/NEW-DIRECTORY/single-probe-exhaustion.json
```

Run timing experiments without concurrent tests or profiling. The report binds
the parent, implementation/fixture hashes, all eight logical tables, row
preservation, per-input work and phase costs. Subsequent runs can pass **this
report** as `--parent`; the runner reconstructs and checks the whole lineage.

Coverage improves **39/83 -> 45/83**. The six gained originals have 48 variables:

| Selected case | Historical group | Original case | Answer |
|---|---|---:|---|
| 26 | learning_holdout3 | 1153 | SAT |
| 46 | core_holdout3 | 1297 | SAT |
| 56 | fresh3 | 1337 | SAT |
| 61 | order_holdout3 | 1372 | UNSAT |
| 65 | activity_holdout3 | 1408 | UNSAT |
| 75 | subsumption_holdout3 | 1446 | SAT |

Independent reference proofs confirm these answers. All 45 remain structurally
covered when growth-exception routes are removed. These are reused development
cases, despite their historical names; no independent holdout is claimed.

The same four-source/32-state policy processes 44 open originals. It adds
**46 continuation blocks (39 clear / seven forced), 327 attempts and 74 nodes**,
with 758 references to saved prefix attempts and no initial windows added. Source
visits reach at most three. Case 46 uses all 32 admissions and closes; no input
is interrupted and no continuation target remains pending.

Resident search/check/persist/compose is **0.53596 s**. Preparation costs
**65.21093 s**, full cold inventory **108.59972 s**, separate route replay
**63.06559 s**, and the acquisition/validation pipeline **257.27725 s** before
final report write. Working storage grows **1,581,056 bytes**. The delta is
**1,609,728 SQLite / 86,923 compressed bytes**; the coverage witness is
**171,985 compressed bytes**. The separate reference archive has **1,238 nodes /
9,826,304 SQLite bytes**, including all ten locally closed continuation targets
(three from the preceding pass). Peak RAM is unmeasured. These are additional
discovery costs, not a matched whole-solver speedup.

The open selected paths expose **41 clear streams across 38 originals**. Of these,
36 have 1--16 remaining ranked candidates and five exhaust that pool. There are
no unstarted selected leaves. `continuation-opportunity.json` records the exact
scope: saved forced rewrites are followed, composed-closed subplans are skipped,
and other alternatives and admission caps are not explored by this diagnostic.

The separate `single-probe-exhaustion.json` checks all five exhausted sources:
**104 saved attempts** cover both polarities of 52 binary variables, while
**79 remaining variable instances** cannot trigger a unit under either value.
Every source is normalized and has minimum clause width at least two. Thus no
single-assumption unit refutation exists on these exact sources. This is not a
SAT/UNSAT decision or a lower bound for stronger reasoning. The 11-variable
encoding-cap source has width at least five, so even three assigned variables
cannot create an initial unit. Common consequences, equivalences, learned
implications and other transformations are not excluded.

This successful diagnostic costs **0.02974 s** after **4.73048 s** restoration,
**5.35440 s** overall. It verifies only source facts required for this claim,
without replacing the full coverage audit. Two earlier status-assumption failures
are preserved in `exhaustion-*-failure.json`; their elapsed replay times were not
retained. `learning_clear` profiles have original and augmented-source traces;
only independently checked original-source attempts support this claim.

The acquisition artifact preserves its **552-test** log and independent cold
validation. The final diagnostic checkpoint passes **557 tests**, including
exhaustive small formulas, missing-evidence rejection, source binding and an
UNSAT counterexample to treating no-unit-trigger as SAT. The final suite retains
20 existing SQLite resource warnings. `exhaustion-validation.json` binds the
diagnostic, its tests and the preserved failed attempts.

The complete history has **41,535 pattern nodes, 75 windows, 97 continuation
blocks, 563 pivot trials, 25 coupled trials, one growth trial, 1,548 source
bindings and 21,838 earlier solver proof rows**. All previous archives remain
necessary. Restore this report with `restore_report` from `continue_cnf_probes.py`
and construct `ContinuationRoutes` before using coverage edges. The earlier full
prepared result remains 902/985. See the [study](../../../research/probe-resumption.md)
for the next reuse targets; manuscript and Lean sources are unchanged.
