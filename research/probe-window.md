# Continue probe discovery without replacing the stored recognizer

## The successful projection changed the probe window

The [growth-three experiment](growth-escape.md) admits pivot 15 in a preserved
35-variable core. Its target then closes under the old recognizer. A complete
single-assumption unit-propagation diagnostic now separates a change in inference
strength from a change in which assumptions the bounded policy visits.

In source coordinates, the original formula has failed assumptions **14=true,
15=true and 32=true**. After projection, the remaining failed assumptions are
**14=true and 32=true**. Every assumption, including inconclusive ones, has a
separately checked unit trace. Projection adds ten resolvents, none binary, while
removing seven pivot clauses, including two binary clauses. Binary-clause count
falls **16 -> 14**. The first four binary-frequency candidates change from
**[17, 4, 8, 13] to [17, 8, 13, 14]**. The newly selected failed assumption was
already refutable on the original core.

Thus the initial trigger is access to a previously untried probe, not a new
single-assumption refutation created by that projection. Later residual paths
can still differ. This diagnostic concerns one source; it does not say that
elimination never strengthens propagation or is generally unnecessary.

## Exact bounded continuation

`cnf_probe_window.py` reads the already checked original probe attempts on an
unresolved node, removes those variables from the first 64 entries of the old
binary-frequency order, and tries the next four. It stops at the first failed
assumption and independently checks both the refutation and propagation under
the opposite value. The residual receives the original configuration and depth,
allowing exact reuse of prior recognition states. There is no new growth exception.

A window record binds its source, width, complete attempt prefix and exact
canonical residual/name map. Inconclusive windows are retained too; they imply
neither satisfiability nor exclusion from a semantic class. If the recognition
admission limit interrupts acquisition, the checked forced-value transformation
remains stored with a pending target. It becomes a coverage edge only after that
target's actual certificate exists and passes checking. Restart can resume the
target without repeating the saved probe discovery. No missing target or budget
stop counts as closure or UNSAT.

The frozen search visits at most **four distinct unresolved sources** per original
and reserves at most **32 newly entered recognition states**, including descendants
and unfinished parents. It starts from the selected unresolved frontier, following
new forced-value continuations before another original leaf. All completed nodes,
inconclusive windows and interrupted transformations remain reusable. Candidate
selection, proof checking, propagation per state and accumulated history are
additional costs; this is not a total runtime or RAM bound.

Finite route composition joins these new transformations with old plans, pivot
trials and the previous growth escape. Every component and both branches of a
chosen conditioning split must be covered. A separate ablation removes growth
routes to distinguish continued probing from dependence on the old exception.

## Evaluation scope and resumption

The comparison restores all six previous tables and adds
`cnf_probe_windows_v1`. The known successful core runs first as an explicitly
charged positive control. Its results remain available while processing the
previously open originals. This order is fixed and reported; these are reused
development sources, not untouched evaluations. In particular, historical group
names containing `holdout` do not establish independence.

The artifact separates preparation, admission/search, coverage checks, persistence,
serialization, full cold audit, route replay and independent reference solving.
Every new pattern node must correspond to an admission reservation. The
seven-table delta checks preservation of all old rows, reconstruction and
idempotent reapplication. The full original corpus is not rerun by this study.

The [frozen experiment](../experiments/results/cnf-probe-window/README.md)
(`a11cddf`) improves selected-original coverage **32/83 -> 36/83**. The four gains
are all 48-variable sources: cases 41, 49 and 62 are SAT; case 78 is UNSAT.
Independent reference solving checks their witnesses/refutations and all new
locally closed targets. Removing the earlier growth-exception route still leaves
**36/83** covered, including the previous successful 48-variable source.

The positive-control core needs two fallback windows and five newly admitted
states in the retained history. Its first forced-value continuation remains open;
the second supplies a complete plan. Thus merely probing the newly promoted
variable 14 once would not establish this closure. This is an alternative route
without the special growth-three allowance, not a claim that every descendant
avoids the original recognizer's permitted growth-two operations.

Across the positive control and 51 previously open originals, the run retains
**70 windows: 52 inconclusive and 18 forced**, containing 475 new assumption
attempts. It adds **81 recognition states**. Five immediate window targets are
already fully recognized after acquisition; other forced continuations need
further composition or remain open. No state limit binds (maximum 24 new states
on one input), and no target remains pending in this measured run. Pending-target
preservation and restart are covered by explicit tests.

| Work or storage | Measured value |
|---|---:|
| Resident search, checking, persistence and per-input composition | 0.84607 s |
| Of which positive control | 0.04175 s |
| Original eligibility checks / final recomposition | 0.04547 / 0.05027 s |
| Paid-history preparation | 65.30144 s |
| Full cold inventory / separate route replay | 106.59552 / 63.01694 s |
| Complete acquisition/validation pipeline before final report write | 252.05013 s |
| Working database increase | 2,142,208 bytes |
| Delta SQLite / compressed | 2,220,032 / 129,619 bytes |
| Finite coverage witness JSON / compressed | 468,460 / 71,810 bytes |
| Separate reference solver proof nodes / database bytes | 409 / 3,502,080 |

These are single-run measurements on selected development inputs. The extra
probing and state acquisition add work and storage; they do not demonstrate a
runtime or memory saving against the previous policy or a competitive solver.
Peak RAM was not measured. The explicit gain is broader certified structural
coverage, with prior results and identities retained. All **543 tests** and
independent artifact reconstruction/replay pass. Formal sources and manuscript
are unchanged; the earlier full prepared result remains 902/985.

To resume, use `restore` in `compare_cnf_probe_window.py` for the complete previous
history, verify and unpack the new delta, then apply the **seven-table**
`apply_delta` from that module. Check its logical table digests and load
`WindowRoutes` to replay every probe-window record and all previous trial types.
Pending targets remain pending until a later explicitly budgeted acquisition.

## Remaining obligations

A fixed continuation window can still miss useful variables, and a failed literal
can reduce a formula without yielding a complete structural plan. The selection
policy is a bounded heuristic, not an efficient partition covering arbitrary SAT.
Use the positive and negative outcomes to choose the next discovery target rather
than increasing windows without evidence. Incremental maintenance of finite-route
coverage, peak process memory and independent evaluation remain separate gaps.
No Lean refinement or unrestricted SAT complexity result is claimed.

The 52 clear windows provide a concrete next target: advance to a subsequent
window while reusing the checked prefix. The current record key binds source and
width, so repeating width four reuses its result; it does not automatically move
past it. A different width currently needs a new record and would repeat the
prefix unless an explicit continuation mechanism is added. Preserve this
distinction between avoiding rediscovery and making further discovery progress.
The forced-but-open paths are the other informative group: inspect their next
unresolved interfaces rather than assuming every forced literal closes a source.

The preserved `continuation-opportunity.json` checks availability without any new
probing: **51 of the 52 clear windows have 3--24 later ranked binary candidates**;
one has exhausted that ranked pool. Neither the four-source nor 32-state cap was
reached in the experiment. These facts favor explicit prefix continuation over
raising recognition-state budgets. Available candidates are not evidence of a
future closure.
