# Share one immutable source context across guard proofs

24 November 2026. The preceding profile identified repeated canonical-form
validation and clause-position construction inside selected local RUP checks.
This experiment prepares that source once per witness attempt and reuses it
across the selected guard certificates. It preserves the support compiler and
its native proof representation.

## What is reused

A local context contains an immutable snapshot of the exact normalized CNF, its
clause-to-position map, its variable count, and read-only copies of the current
source-coordinate map and fixed assignment. Preparation checks canonical form
once. The context is created lazily on the first candidate that actually needs
support transport and fits the existing allowance. A satisfiable tentative graph
or an exhausted allowance creates no context.

The context exists only inside one `_guard_closure` call. It is not stored on
the solver, attached to a certificate, shared across queries, or restored from
an archive. Thus a new component, assignment or query gets a new preparation.
Mutable inputs are copied to immutable values before validation; changing those
inputs later cannot change the prepared source. The internal checker accepts
that prepared context rather than an unrelated source argument.

Each selected hint still checks its clause literals and ordering, every unit
reason against the original CNF, and the final conflict under the negation of
the hint. Source-support membership, coordinate transport and the lifted local
template checks remain. The native compiler, source subset lift, native
publication checks, and cold readers are unchanged. Preparation is internal
implementation state, not a new portable certificate or proof authority.

The frozen witness controller has no transport override. The new subclass
therefore preserves its control flow in a separate method with one local context
and a bound transport call. The old solver and all frozen sources remain intact;
there is no process-global monkeypatch in the solver. Differential tests and
matched trials check that this duplication has not changed candidate ordering,
limits, proof payloads or decisions. Ordered execution traces are not inferred
solely from equal counters.

## Cost and scope

Let L describe the full local CNF and j the selected hints in one call. Previously,
position-map construction ran per transported candidate and canonical validation
ran per successfully transported hint. The new context performs these source
preparations once, while the sum of selected support, clause, unit-reason and
conflict checks remains. Sorting and encoding during canonical validation are
still charged. This saves repeated source work; it does not remove the cost of
checking j independent proofs or establish a polynomial solver for arbitrary CNF.

The optimization can add work on a miss: canonical preparation now precedes the
first support translation, so a site whose selected supports all fail can pay a
source validation that the old transport never reached. Recognition, failed
candidates and complete worker costs must therefore be measured. The one-context
lifetime prevents accumulation across sites, but the new tuple and maps require
transient memory. Clause/literal-slot counters describe the bound source extent,
not allocated Python bytes; immutable clause tuples may share existing objects.
The template bank byte counter excludes this transient context. Whole-worker RSS
and persistent native state are reported separately.

## Comparison and correctness

The protocol freezes code and tests before comparing ordinary search, the frozen
support compiler, and shared context preparation. It retains all eight exposed
chronological edits, their causal origin prefixes and provisioned template banks,
and two serial repetitions in opposite arm order. No later result or cumulative
union seeds a query. The existing 256-dispatch and guard allowances remain;
compiled proof nodes and verification costs are additional to that dispatch cap.

Workers charge restore, setup, solve, accounting, warm and cold native replay,
serialization and compression. Imports, source hashing, protocol loading,
earlier origin/template acquisition and final preservation audits are outside
that interval. A separate adaptive profile uses the largest remaining
context/ordinary solve ratio. Nested cumulative profile times overlap.

Focused validation includes all normalized formulas formed from the nine
possible two-variable clauses and their RUP consequences, all 256 subsets of
the eight nonempty unit/binary clauses with adversarial extra candidates, wrong
reasons and clauses, changed assignments, missing and alternative supports,
mutable source/map snapshots, and lazy preparation on misses. Forty-eight seeded
unlabelled small inputs are checked against truth tables and replayed through
both native readers. Those tests establish correctness, not fresh large-instance
performance or automatic discovery of useful origins.

## Results

Sums of per-case means over two repetitions; endpoint state totals are across
separate runs and are not simultaneous memory.

| Arm | Solve seconds | Complete-worker seconds | Checked native bytes |
|---|---:|---:|---:|
| Ordinary | 7.94209 | 91.26756 | 154,443,458 |
| Support compiler | 8.27046 | 92.09834 | 155,521,837 |
| Shared context | 8.24769 | 92.35632 | 155,521,837 |

Against the support compiler, solve time falls **0.28%**, while complete-worker
time rises **0.28%**. This does not establish an overall speedup. Shared context
remains **3.85% slower in solve** and **1.19% slower in complete-worker time**
than ordinary search. All eight whole queries remain unresolved at 256 dispatches.
Six case solve means improve against support, while edit 28 regresses 2.80% and
edit 37 regresses 0.18%. Preserve both repetitions and all regressions. Keep the
new implementation optional; no default changes.

The work reduction itself is exact on these runs. All 87 local hint checks remain,
but they use **34 source preparations**. Normalization literal visits fall from
82,753 to 32,371 (**60.88%**), and position-map clause visits from 32,305 to 14,012
(**56.63%**). The same 34 contexts close: 15 opposite-unit, one unit/binary and
18 binary-guard closures. Candidate checks remain 33,006, guard-pair checks
142,003, and 635 of the 669 sites remain inconclusive. Native record bytes,
compressed archives, stored proof choices and ordinary search/check counters
are identical to support. There is no retained-state saving.

The sum of per-case mean peak RSS is 3.55% lower than support, but this is not a
simultaneous peak or a reliable general memory bound. Both methods retain the
same native state; the context additionally owns transient maps and tuple
references. Do not equate reduced source visits with a reduction of all memory.

## What the profile says to prioritize

Edit 28 remains the largest context/ordinary solve regression, at 11.00%.
The separate profile shows the gate falling from 0.06852 to 0.05581 cumulative
seconds. Twenty-one calls to the old transport take 0.02294 seconds; seven
context preparations plus 21 bound transports take 0.00706 + 0.00262 seconds.
The per-hint RUP body falls from 0.02064 to 0.00058, while the source validation
cost moves into the once-per-context preparation. Seven native compositions
still take about 0.02069 seconds.

Full-query native verification and normalization remain much larger, at
0.65741 and 0.50331 cumulative seconds. These timings overlap and must not be
summed. The profile confirms the local mechanism, while the two ordinary timing
repetitions do not show a net end-to-end benefit. Prioritize useful additional
coverage instead of extrapolating another small local saving.

## Next coverage gap: learned guards excluding a wider source clause

`wide-clause-gap.json` preserves a deterministic 12-variable, 13-clause example,
its six source-bound conditional-unit templates, individually checked RUP hints,
a satisfying guard-graph model, and three literal-to-negation paths. Exhaustive
checking of all 4,096 assignments finds no model of the full CNF. The current
learned-guard SCC gate returns inconclusive, and the original-binary cover
recognizer also returns no cover. No claim is made that ordinary SAT search
fails or that a new policy would be faster on this small formula.

For i = 1, 2, 3, introduce variables x_i, a_i, u_i and v_i. Pair the two clauses
`(not x_i or a_i or u_i)` and `(not x_i or a_i or not u_i)`; their checked guard
is `(not x_i or a_i)`. Pair two analogous clauses with `not a_i` and opposite
signs of v_i; their guard is `(not x_i or not a_i)`. Add the actual source clause
`(x_1 or x_2 or x_3)`. All original clauses have width three, so the original
binary recognizer sees no binary edges. The learned graph is satisfiable when
all x_i are false, yet its paths `x_i -> a_i -> not x_i` exclude every literal
of that wider clause. The conjunction is therefore UNSAT. This is an elementary
resolvent pattern, not a new unrestricted tractability result.

**Highest next discovery target:** extend the existing bounded wide-clause cover
search to the augmented graph containing learned short guards. Start with an
offline inventory of the 635 inconclusive sites and fresh constructed controls;
measure which proposed covers survive support validation before enabling a live
gate. The existing original-binary machinery in `cnf_binary_clause_cover.py`
and supported path compiler in `cnf_guard_interactions.py` provide the starting
point. The current graph model can screen source clauses before bounded
literal-to-negation searches.

Every selected learned edge still needs its actual source-bound proof. Compile
each covered literal under the strengthened branch context and retain the
original wide-clause identity. Never pass synthetic graph indices to a native
checker as if they named original source clauses. Charge source scanning,
reachability, failed support translation, compilation, added proof state and
cold replay. Test signed renamings, missing supports, satisfiable edits, overlap
between paths and changed branch assignments. The templates in this separating
example are supplied; automatic acquisition, useful fresh coverage, and total
cost improvements remain open. The new cover policy is proposed, not implemented
or measured by this checkpoint.

## Preservation and continuation

The comparison is stored in `experiments/results/cnf-guard-context/`. The
preservation audit requires the same native archive bytes, table digests,
verdicts and ordinary proof/search counters as the previous matched controls.
Only source normalization/position counts and new context statistics may differ.
Exact same-case prior two-reader audits can then be reused. Every new timed
worker and profile still performs cold native replay independently.

The cumulative union remains unchanged: no new proof records or publication
layer are needed for an implementation producing identical native records.
The checkpoint retains its named layer-aware reader and the previous full
snapshot control. All historical results, failed experiments and alternative
proofs remain available. No Lean statement or previous proof block changes.

## Validated checkpoint

All 46 focused tests and 1,798 solver tests pass. The full suite retains the
43 existing unclosed-SQLite ResourceWarnings; the focused tests report none.
Preservation checks 170 prior manifests, 16,313 artifact entries and all 983
previously frozen sources. Twenty-four identical same-case archive audits are
reused; all 48 current workers and three profiles separately perform cold replay.
The 160,338-record cumulative native bank is unchanged, as are the other five
authority tables. No new publication archive is required.

The initial preservation audit stopped at an absolute-versus-relative profile
path comparison, with matching file content. Its source and failure log are
retained. The corrected audit requires resolved path equality and the unchanged
SHA-256; it does not weaken source identity. This failed audit is additional work
outside the worker comparison. The final sealed checks record the paper build,
all 64 unchanged prior proof blocks and the explicit next coverage target.
