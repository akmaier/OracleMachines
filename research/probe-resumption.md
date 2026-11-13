# Resume deeper probe blocks from verified checkpoints

The [first continuation pass](probe-continuation.md) left 42 clear streams with
later ranked candidates. This experiment resumes the complete eight-table
history and applies the same search policy once more. Each visited source may
acquire one new block of at most four candidates; each original still has limits
of four distinct source visits and 32 newly entered recognition states. No
recognizer, ranking, prefix-checking or recomposition rule changes.

`continue_cnf_probes.py` makes the parent report explicit. Its ordered lineage
terminates at the first prefix-continuation checkpoint. Each generation checks
the parent hash, implementation fingerprints, seed logical digests, baseline
coverage, delta hash and resulting table digests before adding the next delta.
Conflicting rows cannot replace old data. The base restoration also retains all
earlier solver proofs, failed attempts, source bindings and alternative routes.
The runner can resume its own output on a later pass, avoiding another bespoke
reconstruction script or accidentally restarting from an obsolete seed.

The experiment processes the same 83 selected development originals in their
saved order, skipping those already structurally covered. An earlier clear
prefix avoids repeated probe discovery. A forced record resumes its exact
residual. Results remain structural-coverage witnesses; complete reference
solving separately checks the answers of newly covered originals. Reused cases
whose historical group names contain `holdout` are not independent evaluations.

The saved opportunity analysis now distinguishes all retained streams from
ones exposed on selected paths of still-open originals. It follows existing
forced rewrites, skips subplans already closed by finite composition, and marks
unstarted leaves separately. This analysis does not acquire a new target or
probe an assumption, and it does not apply admission/source caps. Other saved
alternatives can offer different paths. Pool exhaustion refers only to the
bounded binary-frequency ranking; variables outside that pool are explicit.
Neither exhaustion nor a clear unit-propagation trace establishes SAT or UNSAT.

Preparation, acquisition, persistence, cold inventory checks, route replay,
serialization, restoration and reference solving remain charged. Previously
checked local continuation endpoints are included again in this run's reference
archive, with their cost included. This is additional bounded discovery, not a
claim of faster whole-SAT solving or a new general tractability result.

## Second-pass result

The [preserved experiment](../experiments/results/cnf-probe-resumption/README.md)
(`ffebba0`) raises selected-original coverage **39/83 -> 45/83**. Independent
reference solving confirms six new 48-variable cases:

| Selected case | Historical group | Original case | Answer |
|---|---|---:|---|
| 26 | learning_holdout3 | 1153 | SAT |
| 46 | core_holdout3 | 1297 | SAT |
| 56 | fresh3 | 1337 | SAT |
| 61 | order_holdout3 | 1372 | UNSAT |
| 65 | activity_holdout3 | 1408 | UNSAT |
| 75 | subsumption_holdout3 | 1446 | SAT |

All 45 remain covered with growth-exception routes removed. The run processes
44 previously open originals and retains **46 new continuation blocks (39 clear,
seven forced), 327 new assumption attempts and 74 recognition nodes**. It
references **758 saved prefix attempts** without rediscovering them; that is an
access count, not a count of distinct saved traces. No initial window is added.
Source visits reach at most three. Case 46 closes after using all **32** admission
reservations; no input is interrupted and no continuation target is pending.

| Work or storage | Measured value |
|---|---:|
| Resident search/check/persist/per-input composition | 0.53596 s |
| Eligibility checks / final recomposition | 0.04415 / 0.05049 s |
| Paid-history preparation | 65.21093 s |
| Full cold inventory / separate route replay | 108.59972 / 63.06559 s |
| Acquisition/validation pipeline before final report write | 257.27725 s |
| Working database growth | 1,581,056 bytes |
| Delta SQLite / compressed | 1,609,728 / 86,923 bytes |
| Coverage witness JSON / compressed | 1,038,527 / 171,985 bytes |
| Separate reference archive nodes / SQLite bytes | 1,238 / 9,826,304 |

These timings are for additional discovery on a smaller remaining set. They are
not a matched solver speedup against the preceding pass. The previous warm
prefix microbenchmark remains a separate measurement. Peak RAM is unmeasured;
cold history checking still dominates the pipeline. The new reference archive
includes all ten currently locally closed continuation targets, including three
from the preceding pass, as explicitly charged repeated checking.

The complete history now contains **41,535 pattern nodes, 75 initial windows and
97 continuation blocks**, plus all 563 pivot trials, 25 coupled trials, one growth
trial, 1,548 source bindings and 21,838 earlier solver proof rows. Earlier archives
and failed attempts remain unchanged. The full prepared 902/985 result is not
updated by this selected-original study. No manuscript or Lean source changes
are inferred from the coverage gain.

To continue, run `continue_cnf_probes.py` with this report as `--parent` and a new
output directory. To inspect the latest history without new discovery, call its
`restore_report` on this report, then construct `ContinuationRoutes` before using
the retained transformations. Loading only the newest delta loses required
prefix evidence.

## Remaining selected paths

The 38 still-open originals expose **41 clear streams**, following saved forced
rewrites and excluding composed-closed subplans. Of these, **36 have 1--16 later
ranked candidates**, while **five have exhausted the binary-ranked pool**. There
are no unstarted selected leaves in this analysis. These are the current selected
paths; other retained alternatives may expose different frontiers.

The five exhausted sources have 11, 18, 20, 38 and 44 variables. Their variables
outside the binary ranking require care: absence from that ranking is not
automatically a missed opportunity for single-assumption propagation. For a
normalized CNF of minimum clause width two, assigning a variable absent from all
binary clauses leaves every unsatisfied clause at width at least two. There is
no initial unit and no conflict, so unit propagation cannot start under either
polarity. Together with checked clear traces for every binary variable, this
can certify exhaustion of **all** single-assumption unit refutations, without
deciding satisfiability. A separate diagnostic checks this stronger condition.

## Certified limit of first-order probing

`single-probe-exhaustion.json` confirms this obstruction on **all five** sources.
The checker replays **104 source-bound attempts**, covering both values of 52
binary variables across the five formulas. The remaining **79 variable instances**
have no binary-clause occurrence; the no-unit-trigger argument covers both values
without new probing. The source sizes are 11, 18, 20, 38 and 44 variables, and
the saved original case indices are 0, 2, 73, 27 and 51 respectively. Counts are
across separate formulas, not distinct variables in one formula.

A complete non-conflicting unit fixed point excludes a unit refutation under
any propagation order: by induction, any further valid unit step must agree with
the checked assignment, since an unassigned unit or a falsified clause would
violate the fixed-point check. Combining this fact with the no-trigger argument
covers every single-variable assumption. It excludes only plain unit refutation
on the exact source, not learned-clause augmentation, common consequences,
equivalence substitution, elimination, deeper conditioning or other solvers.

The 11-variable `encoding_cap` source has minimum clause width **five**. Assigning
at most three variables leaves every unsatisfied clause at width at least two.
Thus even two-level or three-level plain assumption-plus-unit probing cannot
start propagation there; at least four assigned variables are needed before a
unit can appear. Other structural algorithms remain possible. The other four
sources have minimum width two and are more plausible targets for bounded
nested probing after reuse of their existing traces.

The diagnostic checks only its required source certificates and saved attempts,
without replaying unrelated alternative routes. It takes **0.02974 s** after
**4.73048 s** of archive restoration; the complete successful diagnostic takes
**5.35440 s**, separately from the acquisition pipeline above. No history bytes
change. This narrower proof obligation is not a replacement for full coverage
verification and does not demonstrate a whole-solver speedup.

Two preliminary diagnostics stopped on an invalid assumption about profile
status. The affected sources use `learning_clear`: top-level attempts concern
the original source, while a nested continuation concerns a formula augmented
with learned clauses. The final checker independently validates each original
trace against the source and excludes the nested continuation. Both failures
are retained; their full replay time was paid but was not recorded. Tests include
an augmented-source trace rejected as original-source evidence, omitted binary
variables/polarities, small exhaustive formulas and an UNSAT example with no
single-variable unit refutation. All **557 tests** pass; the final test log retains
20 existing SQLite warnings. The acquisition checkpoint separately preserves its
552-test log and independent eight-table/cold/reference validation.

## Next priorities

1. **Extract more from the saved paired traces.** Later windows checked failed
   literals, while common-consequence, equivalence and binary-implication
   discovery still use the old bounded initial profile. Inspect the complete
   retained trace pairs for these stronger certificates before acquiring more
   assumptions. The five-source obstruction does not rule out such reuse.
2. **Target stronger reasoning according to the obstruction.** Try a bounded
   second assumption on the four width-two sources if trace reuse does not close
   them. Preserve source bindings and both branch obligations. The width-five
   encoding-cap source needs different structural treatment or a sufficiently
   deep, explicitly charged conditioning step; shallow plain probing cannot help.
3. **Continue the 36 unfinished streams as a cheap coverage control.** Use this
   checkpoint as the parent and retain the same budgets. Cold verification is
   still the largest measured runtime cost; investigate exact proof dependencies
   before reducing its scope. Peak RAM and independent evaluation remain open.
