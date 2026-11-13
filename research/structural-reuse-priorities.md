# Structural reuse: cost map and investigation priorities

Updated 2026-11-13 after the user's shift toward pattern discovery and a valid
partition of the entire SAT problem. This is the working record for the hourly
investigation. Start with the [discovery plan](sat-pattern-discovery.md), then
consult [implementation history](implementation-gaps.md),
[resource bounds](resource-bounds.md) and the measurements below.

**Primary objective:** discover useful SAT categories and exact decompositions
from arbitrary CNF input, retaining explicit coverage of unresolved cases.
Recognized-family optimization continues as supporting work. A complete
classification and efficient solution of every resulting cell are separate
obligations; retain overlaps, checked recognition and composition costs.

## Current investigation: checked prefixes let discovery advance without rediscovery

The [prefix-continuation study](probe-continuation.md) advances saved clear probe
windows while retaining their checked traces by reference. A continuation binds
the exact source/configuration/depth, width and offset, and requires its complete
clear predecessor. Missing, foreign or forced prefixes cannot authorize a cursor.
Pending forced residuals survive restart and become routes only after acquisition.

Coverage improves **36/83 -> 39/83**: one SAT and two UNSAT 48-variable development
cases, independently confirmed. All 39 remain covered without the growth-exception
routes. The run adds **51 continuation blocks (43 clear / eight forced), five
initial windows and 45 nodes**. It makes 409 new attempts and references 408 saved
attempts without rediscovery. No cap binds (maximum 13 new states / three sources).

The matched warm probe substep uses **373 versus 781 attempts**, with five-run
median **0.13230 versus 0.27631 seconds**: **2.09x** faster for ranking, discovery
and checking after prefix validation. Both microbenchmarks exclude persistence
and target recognition. Resident search/check/persist/compose costs **0.56578 s**;
preparation **64.41 s**, full cold inventory **110.39 s**, separate route replay
**63.13 s**, and the whole acquisition/validation pipeline **257.43 s**. Cold
checking remains the dominant measured cost. No end-to-end solver speedup or
peak-RAM reduction is claimed. Working storage grows **1,359,872 bytes**; the
delta is **1,429,504 SQLite / 82,368 compressed bytes**.

1. **Advance the remaining 42 clear streams with the existing mechanism.** They
   retain 2--20 eligible candidates each; one other clear stream is exhausted.
   Resume the full eight-table history and measure additional coverage per new
   attempt under the same bounds before expanding the policy or admission caps.
2. **Investigate four forced-but-open targets.** Three of eight forced targets
   close locally and one more through composed routes. The remaining four retain
   unresolved interactions. All five locally open targets have one selected
   unresolved leaf, giving concrete residuals for further structural diagnosis.
3. **Profile cold proof replay for the largest runtime win.** Distinguish required
   reachable dependencies from repeated reconstruction and unrelated history;
   preserve exact checking and invalidation requirements. Warm prefix savings
   do not remove the preparation cost. Peak RAM and independent evaluation remain
   separate obligations.

All **547 tests**, eight-table reconstruction, cold prefix/finite-plan replay,
growth ablation and independent reference checks pass. Resume from **41,461
pattern nodes, 75 initial windows, 51 continuation blocks, 563 pivot trials,
25 coupled trials and one growth trial**, retaining all 1,548 source bindings and
21,838 earlier solver rows. The new 513-node reference archive is additional
evidence. Earlier full prepared coverage remains 902/985. Manuscript and formal
sources are unchanged; these are reused development sources, not a new SAT class.

## Previous investigation: retained probe windows broaden coverage without the exception

The [probe-window investigation](probe-window.md) identifies the initial trigger
of the growth success: deleting two binary pivot clauses moves an already failed
assumption into the first four ranked probes. Complete source-coordinate traces
show no new remaining-variable single-assumption refutation after projection.
This is a selection-window effect on that core, not a general statement that
elimination cannot strengthen propagation.

Continuing with four previously untried binary-frequency candidates, at most four
unresolved sources and 32 new states per original improves coverage
**32/83 -> 36/83**. The four new 48-variable originals are independently confirmed
as **three SAT and one UNSAT**. Removing the earlier growth-exception route still
leaves all 36 covered. The positive-control core needs two continued windows;
the first forced value alone leaves an open residual.

The run preserves **70 windows** (52 clear, 18 forced), 475 assumption attempts
and **81 new recognition nodes**. Resident search/check/persist/compose costs
**0.84607 seconds**, including the positive control. Working storage increases
**2,142,208 bytes**; the delta is **2,220,032 SQLite / 129,619 compressed bytes**.
Preparation costs **65.30 seconds**, complete cold audit **106.60**, and separate
route replay **63.02**. Full pipeline time is **252.05 seconds**. This is additional
work for coverage, not a demonstrated runtime or RAM saving. Peak RAM is unmeasured.

Neither admission nor source-visit caps bind. The next evidence-backed gaps are:

1. **Advance a window while reusing its checked prefix.** Of 52 fully clear
   windows, **51 still have ranked binary candidates available** (3--24 each).
   Repeating the current source/width key correctly reuses its result but does
   not advance. Add an explicit continuation position and reuse the existing
   original and window traces before testing the next bounded block. This is
   further discovery, not a claim that those variables will close the source.
2. **Explain forced-but-open continuations.** Only five immediate window targets
   close; other forced values require more composition or leave open interfaces.
   Check whether combining compatible checked consequences can avoid repeated
   recognition, while preserving full source/name bindings and exact costs.
3. **Maintain finite-route coverage incrementally.** Repeated composition still
   scans reachable plans; cold verification remains the dominant measured time.
   A persisted reverse-premise index needs explicit update and invalidation rules.

All **543 tests**, seven-table reconstruction, cold finite-plan replay, growth
ablation and independent endpoint checks pass. Resume from **41,416 pattern nodes,
563 pivot trials, 25 coupled trials, one growth trial and 70 probe windows**;
all 1,548 source bindings and 21,838 older solver proof rows remain intact. The
409-node reference archive is additional evidence. These are reused development
sources; the earlier full prepared result remains **902/985**. Formal sources and
manuscript are unchanged, with no unrestricted SAT complexity claim.

## Previous investigation: one growth exception closes a saved alternative route

The [growth-three escape](growth-escape.md) closes the preserved 35-variable core.
Only its first projection receives allowance three; all descendants retain the
old recognizer and allowance two. Pivot 15 produces four new probing states and
no unresolved leaf, in **0.02275 resident seconds**. The growth-two control admits
no pivot. Warm search reuses the trial with zero new states in **0.00321 seconds**.
The delta is **122,880 SQLite / 7,870 compressed bytes**; working storage increases
69,632 bytes over the seed with an empty sixth table. Peak RAM was not measured.

Finite checked composition now follows open saved alternatives as well as old
plans. It requires every component/conditioning premise and rejects circular
support. This raises the selected-original coverage **31/83 -> 32/83**: case 33,
the 48-variable `reuse_holdout3` source (original case 1193). A separate complete
solver confirms UNSAT for the core, its target and the gained original. This is
one reused development case, despite its historical group name, not a fresh
holdout or a new tractable SAT family.

Composition visits 12,595 nodes / 13,176 premises in **0.05919 seconds** and retains
a **47-step, 41,065-byte compressed witness**. Its resident replay takes 0.00042
seconds; preparation costs **62.92 seconds** and fresh-cache route/witness replay
**12.17 seconds**. The escape run separately pays 65.69 seconds for preparation,
114.37 for complete cold audit and 67.68 for trial replay. These overlapping
verification phases are charged, not hidden in subsecond expansion timings.

1. **Identify when a small projection unlocks propagation.** Compare source and
   projected probe traces, binary clauses and forced values to explain why the
   unique growth-three move works here. Then test a frozen predictor on other
   preserved open cores with matched admission budgets and controls. Minimum raw
   clause growth alone is not a guarantee of useful simplification.
2. **Extend only where evidence supports the growth cost.** Check whether the
   same pattern covers other unresolved cells without repeated broad searches or
   unconditional budget increases. The earlier raw-pair lower-growth diagnostic
   remains valid; subsequent probing, rather than a net-four raw pair, closes this
   case. Keep unrecognized cases and negative trials in the history.
3. **Maintain route evidence incrementally.** The first finite composition scans
   the reachable graph. Its reverse-premise index could support updates only to
   ancestors of new closures, provided rule identity, invalidation and persistence
   are checked. Cold history verification still dominates end-to-end time.

All **540 tests** pass. Preserve the six-table history with **41,335 pattern nodes,
563 one-pivot trials, 25 coupled trials and one growth trial**, plus every earlier
source binding and solver proof. The source-coverage witness and its separate
212-node reference solver archive are additional artifacts. Formal sources and
manuscript are unchanged. The earlier full prepared result remains **902/985**;
there is no new full-corpus result or unrestricted SAT complexity claim.

## Previous investigation: state-capped coupled routes expose an admission barrier

The [coupled-pivot study](coupled-pivots.md) resumes every earlier history and
tries an interacting second pivot on retained divergent first routes. Both steps
keep the old pair/growth caps. It closes the entry-budget accounting gap by
guarding **every newly entered recognition state**, including descendants and
unfinished parents, at **32 per open input**. Completed certificates survive a
stop; cached states remain reusable. Preparation, checking, per-state work and
bytes are additional, so this is not a total runtime or RAM bound.

The original run acquires **25 trials / 32 nodes** in **0.62200 resident seconds**,
with no coverage gain: **31/83** remains. The repeated control adds **15 / 17** in
**0.21175 seconds**, retaining **88/96**. Neither run hits the state cap (maximum
11 and 6 states on an input). Original seed verification costs **69.09 seconds**,
full cold audit **114.40**, and separate trial replay **69.81**. These exceed the
new search cost and remain charged. The new delta is **937,984 SQLite / 54,883
compressed bytes**; no ordinary-solver speedup is claimed.

Only 18 still-open originals have retained divergent routes. The selected routes
admit just 25 interacting second pivots. Of their results, **17/25** return to the
first route's frontier and **24/25** use only seed leaves. Exactly one new unresolved
core appears. It has 35 variables / 150 clauses. An exhaustive candidate diagnostic
within the 64-pair cap finds minimum first-step growth **3**, minimum two-step net
growth **7**, and minimum interacting-pair growth **15**. All 662 admitted ordered
pairs fail a net-growth-four allowance, even with temporary intermediate growth.
This is a restricted move-rule obstruction, not a general SAT lower bound.

1. **Test the least-cost escape with ordinary simplification.** Start from the
   preserved new core and its minimum-growth-three first pivot; charge the extra
   clause allowance explicitly and keep the admission budget. A net-four coupled
   relaxation alone is already ruled out on this core under the current pair cap.
2. **Compose success through saved alternative routes.** A future closed leaf
   may be reachable only through an earlier open pivot/coupled trial. The present
   composition accepts individually closed replacements and does not recursively
   compose every open trial. Add checked finite route justification before counting
   any resulting whole-original gain. No gains are currently hidden or claimed.
3. **Keep move availability separate from exploration limits.** The state budget
   did not bind this experiment; increasing it without new admissible moves is not
   supported. Other moves, broader interactions and larger growth are hypotheses
   requiring matched checks, preserved failures and complete cost accounting.

All **535 tests** and artifact checks pass. Resume from **41,331 pattern nodes,
563 one-pivot trials and 25 coupled trials**, plus all earlier solver proofs and
source bindings, using the study's fifth-table reconstruction recipe. The earlier
full prepared measurement remains **902/985**; there is no new full-corpus result.

## Previous investigation: later ancestors reduce acquisition, not unresolved coverage

The [matched ancestor study](frontier-pivots.md) starts from the exact union of
both prior pivot histories, including their 345 original-suite trials. It compares
the first four open elimination ancestors with four ancestors nearest selected
unresolved terminals, keeping the same interaction-first candidate order and
pair/growth caps. Prior trials are checked and reused; each open input can acquire
at most eight **new** trials. That cap still does not bound descendant discovery.

On the 83 originals, early search acquires **145 trials / 266 new nodes** in
**3.76670 resident expansion seconds**. Near-frontier search acquires **102 trials /
90 nodes** in **1.75051 seconds**. Both retain **31/83** closures, with no closed
replacement. Near-frontier search reconverges in **82/102** trials; 20 trials
reach novel selected leaves, but none closes. The growth limit rejects 6,388 of
6,640 constructed candidates there. This is a narrower, cheaper exploration on
these inputs, not a same-work SAT speedup or a coverage improvement.

The seed costs **752,304,128 bytes** and **64--68 seconds** to verify before
resident search. Full cold checking is another **107--110 seconds**, and separate
trial replay costs **62 seconds**, with overlapping dependencies charged. The
frontier delta is **3,018,752 SQLite / 165,286 compressed bytes**, versus
**6,807,552 / 382,806** for early search. Repeated controls retain **88/96** in both
modes, adding 10 versus 12 new trials. All previous rows and failed acquisitions
are preserved. The earlier full prepared measurement remains **902/985**.

All **531 tests** pass. The new original deltas share 57 pattern rows / 29 trial
rows and add **299 unique nodes / 218 trials** together. The latest reusable
union now holds **41,299 pattern nodes / 563 trials**, plus every earlier source
binding and ordinary solver proof. Use the linked study's updated resume recipe.

1. **Test coupled deviations at retained divergent states with a new-state cap.**
   A later ancestor alone does not supply coverage at the tested limits. Keep
   source/configuration/depth identities and exact recomposition, and account for
   every newly acquired descendant rather than only entry targets. Distinguish
   this from relaxing the intermediate growth allowance.
2. **Explain the admission barrier before another broad sweep.** About 96% of
   near-frontier constructed candidates violate the current growth cap. Investigate
   a concrete interacting-variable structure that could permit a useful coupled
   continuation, including its intermediate clauses and recognition cost. Fewer
   literals or a novel residual are not successful-closure criteria.
3. **Reuse the compatible histories and retain the negative controls.** Candidate
   preparation still runs on cache hits; seed checking and cold replay dominate
   the measured elapsed work. Peak process memory, an independent holdout and a
   competitive incremental solver comparison remain separate gaps. Other ancestor
   choices and unselected branches are not exhausted by this experiment.

## Previous investigation: bounded pivot changes mostly reconverge

The [bounded-pivot study](pivot-alternatives.md) tests at most four earlier open
elimination ancestors and eight full alternative target recognitions per open
original. It preserves the same pair/growth caps and the entire paid proof graph.
**316 trials** add **602 pattern nodes**, but no closed alternative: original
coverage remains **31/83**. Resident expansion costs **6.45902 seconds**, after
**63.19332 seconds** of requested-source verification. The new rows are retained
as a **15,208,448-byte SQLite / 857,460-byte compressed delta** over the existing
734,814,208-byte base. Full cold and separate trial audits are additional costs.

The useful pattern is reconvergence: **295/316 (93.35%)** trials reach the exact
same multiset of selected unresolved canonical leaf keys as their source plans.
All immediate target roots are new, so reuse happens in their descendants.
Only 21 trials reach novel selected leaves (13 distinct); four reduce selected
open literals and seventeen increase them. None produces a recognized endpoint.
Also, **271/316** alternate pivots share no source clause with the selected one;
260 of those reconverge. Independence is not a safe universal pruning rule:
eleven such trials have different selected frontiers.

An interaction-first follow-up keeps the same four/eight budgets and pays an
extra source scan. It increases interacting trials **45 -> 74**, yet retains
**31/83** closures with no successful replacement. Expansion is **7.11551 seconds**
and acquires **660** pattern nodes, versus 602. This is another negative coverage
control. The first repeated-input control also remains **88/96**, with 56 attempts
and 40 unique persisted trials. These are selected/reused development inputs,
not untouched evaluations or a new full-corpus result.

The interaction-first follow-up still reconverges in **290/316 (91.77%)** trials,
with seventeen distinct novel leaves and no closed replacement. Both schedules
also retain **88/96** on repeated controls. All **527 tests** pass; the formal
sources and earlier projection theorem are unchanged. The original-suite deltas
share **554 pattern rows / 287 trial rows** and combine into **708 unique new
nodes / 345 trials**. Use the study's resume recipe to retain all of this work.

1. **Investigate where the paths first diverge, with a distinct-state budget.**
   Use the retained novel frontiers and ancestor-to-source links to test a small
   coupled continuation before returning to the greedy recognizer. Reuse exact
   residual/configuration/budget states and charge every new state, rather than
   assuming an eight-entry cap bounds the descendant discovery graph. Validate
   any endpoint all the way to its original source.
2. **Audit ancestor selection before raising trial or growth limits.** The current
   policy visits only the first four open elimination ancestors in breadth-first
   order. It does not exhaust later bottlenecks or all open branches. Compare a
   targeted later-ancestor schedule at the same cap before inferring that useful
   single-pivot alternatives do not exist. The tested growth and interaction
   changes are not sufficient success predictors.
3. **Preserve and reuse failed exploration at its actual scope.** Trials bind
   source, pivot, exact target and recognizer configuration. Compatible deltas
   can share immutable rows; the paid base and cold verification remain charged.
   An open result under this policy excludes neither a different continuation
   nor a tractable semantic class. Full-history peak memory, independent holdouts
   and a competitive incremental solver comparison remain open. The earlier full
   prepared measurement is still **902/985**.

## Previous investigation: exact subset filtering; useful orders remain the coverage gap

The [required-literal index](anchored-subsets.md) addresses the preceding profile's
largest own-time function while preserving every recognition outcome. The costly
source's 1,694 calls have **zero exact-input cache hits within either independent
role** (843 proposals / 851 checks). A whole-input LRU is therefore not the useful
reuse mechanism on this trace. A per-call anchor index filters impossible subset
candidates instead, retaining the old first-witness order and separate checking.

Five alternating-order kernel replays reduce the selected trace median from
**1.116163 to 0.556901 seconds**. Actual subset tests fall from **4,904,264 to
150,503**. Shared-literal controls can regress, and traced kernel peak rises from
84,047 to 88,045 Python bytes. These are kernel results, not a general SAT ratio.
All **521 tests** and the **4,219-declaration / 2,031-theorem** Lean audit pass.
The formal lemmas establish the necessary condition and first-match preservation;
Python refinement and total machine-cost proofs remain open.

The saved 57-leaf complete comparison falls from **4.54924 to 4.06818 seconds**
query and **1.73407 to 1.53721 seconds** cold checking, with the exact same
19,894,272-byte database and zero closures. Stored graphs and results are unchanged.
The optional index does not promote the previous negative additive-growth policy.

On the 83 original prior misses, matched query time falls **155.78451 ->
139.68494 seconds (10.33%)**, discovery **153.95887 -> 137.57819**, and complete
cold checking **111.46828 -> 102.79093 (7.78%)**. Both close exactly **31/83** and
reproduce the same **734,814,208-byte** archive, preserving all prior rows.
Four-source peak Python allocation is effectively unchanged at 17.35 MB; this
sample excludes native memory and full-history peak. No faster ordinary solver,
smaller history or new closure is claimed.

The repeated 96-input control retains **88 closures** and identical bytes. Query
time falls **14.44058 -> 13.76681 seconds (4.67%)**; cold replay is essentially
unchanged at **50.73523 / 50.49557**. A shared prefix and other pipeline costs
limit the kernel gain's effect on full acquisition. These are single matched
runs, with adverse controls retained and no untouched holdout.

1. **Find useful alternative orders under an explicit total discovery budget.**
   Test whether a small set of pivot choices exposes units, binary implications,
   separators, affine structure or another recognized endpoint. Validate success
   back to the original source. Charge unsuccessful lookahead and all index work.
   Do not automatically raise growth limits: the previous extra 2,530 valid edges
   gained zero source closures.
2. **Target remaining repeated work with evidence.** The zero-hit trace rules out
   whole-input proposal/check caching as the next shortcut on this source. Exact
   structural reuse across neighboring inputs needs changed-clause, implication
   origin and witness-order dependencies; those are not supplied by this ephemeral
   index. Reprofile after a coverage change before choosing further micro-optimization.
3. **Measure transfer and account for retained evidence.** Current inputs are
   selected failures and reused controls. Untouched holdouts, a common incremental
   CDCL comparison and full-history peak memory remain open. This index changes
   neither archived bytes nor the earlier full prepared result **902/985**.

## Previous investigation: useful endpoints, not just more admissible steps

The [fixed additive experiment](additive-elimination.md) implements independently
checked allowances of one and two clauses after earlier rules fail. Lean now
proves at most n0 steps, m0+d*n0 clauses per state and
(n0+1)*n0*(m0+d*n0) retained formula slots for one normalized accepted chain.
All **516 tests** and the **4,216-declaration / 2,028-theorem** Lean audit pass.
The theorem guarantees neither a useful pivot nor a small full discovery graph.

The candidate opportunity does **not** produce additional closures. On the 57
saved leaves, all three policies close zero; selected open literals increase
25,488 -> 25,838 -> 26,604. On the 83 original prior misses, all three close the
same **31**, with no gains or losses. Query time is
**121.61751 / 142.26465 / 163.21184 seconds** for baseline / allowance one / two;
acquisition databases are **674,234,368 / 700,178,432 / 734,814,208 bytes**.
Above the shared paid prefix, allowance two adds 23.6% more space and costs 34.2%
more query time. These are single ordered controls, not universal ratios.

The new rules acquire **1,021 / 2,530** additive edges across the originals.
Allowance two tests 155,645 candidates and rejects 151,131 for growth. All three
leave 52 original sources unresolved and 57 selected leaves. Cheap admission and
strict support decrease alone are therefore poor proxies for useful endpoint
progress. Both policies remain optional. Larger growth budgets should not be
the automatic next experiment.

The repeated 96-input control also retains exactly **88 closures** in all modes,
with query times **10.45184 / 12.74294 / 14.87718 seconds** and larger databases.
All nine acquisition archives and nine separate reference archives pass the
stated cold checks. The largest reference database adds **1,236,189,184 bytes**
before compression, beyond acquisition; its endpoint answers and models persist.

A separate profile of case 73 (48 variables / 204 clauses) identifies repeated
subset search as a concrete cost target: `indexed_certificate` runs **1,694**
times, with **1.67039 own / 2.21385 cumulative seconds** in **13.30082** instrumented
discovery seconds. `_find_core` has 3.48529 cumulative seconds; these nested times
must not be added. Direct additive discovery/checking total **0.24555 seconds**.
The profile is one source from the paid prefix, not the preceding ordered cache
history or a causal ablation. Count repeated exact source/augmented-CNF calls
before assuming a cache can remove all this work. Keep proposal and independently
checked-result caches distinct; ordered clauses and implication reasons matter.

The two-clause final frontier now contains **43 leaves needing three extra
clauses, eleven needing four, two needing five**, and one without a pair-bounded
candidate. These local margins have moved without gaining closures. Retained
subsumption permits a current-budget step in 22 leaves but is not an integrated
coverage result. Preserve these cases rather than automatically raising limits.

1. **Investigate which alternative orders expose useful endpoints.** Compare a
   small explicitly budgeted set of alternative pivots on retained stalled cores.
   Record whether they create units, binary implications, component separators,
   affine structure or a recognized family, then check whole-source composition.
   Keep candidate count and all failed lookahead work charged; a failed greedy
   order does not exclude another successful order. Avoid treating local growth
   margins as coverage gains.
2. **Reduce repeated recognition when it dominates acquisition.** Use the saved
   profile to measure repeated exact original/augmented subset queries before
   choosing a cache or admission rewrite. Reuse must bind actual source content,
   parent clauses, retained-resolvent membership, budgets and relevant recognition
   dependencies. Unchanged pivot occurrences alone are insufficient. Shared
   occurrence scans across growth thresholds are an opportunity, not yet a
   measured saving or the assumed dominant cost.
3. **Validate transfer and retain the full cost.** Preserve reference proofs and
   models as well as the acquisition databases; they consume additional space.
   Reused controls and selected prior failures do not replace an untouched
   holdout. The earlier full prepared result remains **902/985**; this subset
   experiment does not update it or establish efficient arbitrary-SAT coverage.

## Previous investigation: small additive clause growth was the next coverage test

The [clause-count fallback](clause-bound-elimination.md) is implemented, checked
and remains optional. It closes **31/83** original prior misses versus **29/83**,
with no losses and two distinct 48-variable gains. Query time grows
**78.06321 -> 113.63899 seconds (+45.57%)** and complete database bytes
**621,146,112 -> 674,234,368**. Added bytes above the paid prefix grow **26.05%**.
The separate 96-input repeated control retains the same **88 closures**, while
time grows **8.90872 -> 10.48245 seconds**. Opposite-order leaf runs reproduce
the same databases and one new leaf closure at higher cost. No default promotion
or fresh full-corpus result follows.

All **511 tests** and the **4,195-declaration / 2,018-theorem** Lean audit pass.
Lean proves conditional size bounds for one accepted chain, not pivot availability
or full discovery costs. All eight archives cold-check unchanged, prior rows
survive, and every new edge receives independent endpoint/model validation.
Original-input endpoint diagnostics cost **961.43125 seconds**, separately from
query time; their older reference solver still performs a per-solve SQL census.
No profile isolates that cost from solving. Production queries already use the
incremental accounting implementation.

The [exact frontier diagnostic](../experiments/results/cnf-clause-bound-elimination-originals/growth-barriers.json)
finds **57 selected leaves / 25,488 literals** remaining across **52 unresolved
originals**. Of these leaves, **32** have a pivot needing only one additional
clause, **50** need at most two, and **56** need at most four under current pair
and candidate caps. Removing the pair cap alone helps just one other leaf,
whose cheapest admissible pivots require 72 pairs. Retained-clause subsumption
would admit a non-growing pivot in 12 leaves. These counts describe candidate
opportunities, not successful chains or added closures.

1. **Test fixed additive clause budgets of one and two.** Preserve earlier
   accepted choices and exact complete-pair checks. A fixed allowance d keeps
   any elimination-only chain within m0+d*n0 clauses; alternatively the fixed
   pair cap B gives m0+B*n0. This bounds formula payload, not an efficient order
   search or all branches. Compare whole-source outcomes and total costs before
   promotion. The additive policy and its Lean resource theorem remain open.
2. **Measure and reduce repeated failed recognition.** The current extension
   tests 166,437 candidates, rejects 162,187 for clause growth and acquires
   2,504 new nodes for two extra original closures. Each new target reruns the
   structural pipeline. Profile a representative costly source before choosing
   between cheaper candidate admission, reusable unchanged occurrence analyses
   and more selective acquisition. Retained-clause duplicate membership can
   change even when pivot occurrences do not; include that invalidation dependency.
3. **Separate useful order discovery from checking one chain.** An unsuccessful
   greedy order does not exclude another useful order. Preserve alternatives,
   negative cases and the pair-cap exception. The repeated 96-input control gives
   no coverage transfer, so an untouched holdout and broader rerun remain open.
   Census optimization in the diagnostic is supporting work; it does not address
   the measured 111.89 seconds of original-source structural discovery.

The earlier full prepared measurement remains **902/985**. This optional subset
policy explains 31 of its saved 83 misses, without proving efficient arbitrary
SAT coverage or a uniformly polynomial construction.

## Previous investigation: literal-growth admission is the larger remaining gap

The [retained-clause subsumption fallback](subsumed-elimination.md) is implemented,
independently checked and proved at the semantic level in Lean. It permits ten
extra steps on the 59 remaining leaves, but closes none and removes only 24 more
literal occurrences. On the 83 original misses, both policies close **the same
29**. Total query time rises **79.65962 -> 88.16727 seconds** and database bytes
**621,146,112 -> 628,133,888**. Two opposite-order leaf comparisons also regress.
All **506 tests** and the **4,173-declaration / 2,009-theorem** Lean audit pass;
all six archives cold-check unchanged and every prior row survives. The fallback
stays optional, with the failed evidence preserved rather than promoted.

The more informative [diagnostic](../experiments/results/cnf-subsumed-elimination-originals/growth-opportunity.json)
separates clause growth from literal growth. **48/59** remaining leaves admit a
candidate with non-growing clause count without subsumption, or **49/59** with it,
under the existing pair/candidate caps. All need at most eight extra literals;
15 plain candidates need only one. None admits the current joint non-growth rule.
These are measured candidate opportunities, not new closures or runtime results.

The next ranked steps are:

1. **Test clause-count-based admission before further subsumption tuning.**
   Keep the plain baseline and explicit width/candidate/pair accounting. For an
   elimination-only chain with at most m0 clauses and decreasing variable count
   from n0, each normalized CNF has at most m0*n0 literal occurrences. The current
   per-step literal cap is stronger than needed for that local size bound. The
   argument guarantees neither a next pivot nor a bound on the entire branching
   history. Measure accepted-chain length, intermediate width, exact checks,
   cold replay and original-source closures, preserving any ordering losses.
2. **Reduce the dominant failed candidate work.** The added fallback tests 86,305
   pivots, rejects 85,902 for growth and performs 8,639,284 subset tests for no new
   original closure. Prefer a cheap plain clause-count policy to retaining this
   overhead by default. The earlier single-binary-occurrence sufficient rule and
   exact invalidation-aware reuse remain cost candidates; their timing benefit
   is still unmeasured. Operation counts alone do not establish a time breakdown.
3. **Test transfer only after a credible gain.** The two leaf orders and matched
   original misses are negative, so no fresh holdout or full-corpus promotion was
   attempted. Any stronger admission rule needs independent/adversarial controls
   and whole-source recomposition, not extrapolation from available pivots.

The optional bounded policy still closes 29 of the saved 83 misses; 54 originals
remain unresolved. The earlier full-corpus 902/985 measurement is not replaced by
these subset experiments. No efficient partition covering arbitrary SAT follows.

## Previous investigation: checked elimination broadens coverage at extra cost

The [bounded-elimination extension](variable-elimination.md) introduces complete
opposing-pair projection at previously unresolved terminal nodes, with independent
checking and model restoration. A separate pure-only control uses pair limit zero.
On the **99 saved unresolved leaves**, baseline / pure-only / bounded close
**0 / 14 / 37**. On the **83 original unresolved sources**, starting from the same
paid 417,370,112-byte prefix, they close **0 / 11 / 29**. The bounded candidate
retains every pure-only closure and leaves **54 originals / 59 selected leaves /
26,205 literals** unresolved. This is a measured whole-input gain on prior misses,
not a rerun of all 1,497 cases or a new default policy.

Coverage is more expensive here. Original-source total query time is
**64.76503 / 71.86221 / 80.09857 s**, and database bytes are
**605,675,520 / 627,138,560 / 621,146,112**. The ordinary solver still searches the
original CNFs with identical counters. All old rows are retained. Exact source
and child bindings, growth caps and all opposing pairs remain checked. Lean
proves the semantic projection identity; it does not refine Python or its costs.
All **501 Python tests** and the expanded **4,168-declaration / 2,004-theorem**
Lean audit pass. See the [frontier](../experiments/results/cnf-variable-elimination-frontier/README.md)
and [whole-input](../experiments/results/cnf-variable-elimination-originals/README.md)
records for separate cold, memory and model checks.

The new measured cost is failed candidate analysis: **167,129 candidates tested,
156,757 growth rejections, 1,457,523 opposing pairs visited**, versus **2,822**
accepted elimination nodes. Raising the pair cap alone does not address that
dominant rejection category. The next ranked investigations are:

1. **Profile and avoid repeated failed elimination analyses.** Test exact reuse
   of unchanged occurrence neighborhoods or inexpensive rejection bounds before
   building all resolvents. Source updates can change retained-clause duplicate
   membership even if pivot occurrences are unchanged; include that dependency
   in recognition, invalidation and checking. Do not assume counters equal time.
   The accepted mixed steps include 1,588 with a single occurrence on one side,
   versus 111 with multiple occurrences on both sides. Test a cheap sufficient
   rule for a single binary occurrence before exhaustive ranking, charging any
   changed order/coverage. Exact target sharing is sparse: 2,822 elimination edges
   reach 2,821 distinct targets, with only one repeated incoming reference.
2. **Remove provably redundant resolvents before judging growth.** A retained
   subclause may already imply a new resolvent. Measure this opportunity on the
   remaining frontier before changing the policy; preserve complete opposing-pair
   coverage, exact recomposition and model lifting. A smaller target is not by
   itself a cheaper expansion.
   The read-only follow-up identifies this opportunity in **10/59** current open
   leaves. **58/59** still have pair-bounded candidates but no currently non-growing
   step; simply increasing the pair cap is therefore not the main next test.
3. **Measure transfer and ordering effects.** The new study deliberately targets
   previous failures. A separate fresh/adversarial policy comparison, alternative
   elimination order and a full-corpus rerun remain open before promotion. Pure
   elimination is a control, not a novel method or an omitted baseline.

The prior full prepared result remains **902/985**. Twenty-nine of its saved
misses now have additional checked closures under the new policy. Keep this
source-level evidence separate from a new full-corpus timing/coverage claim.
No uniform polynomial solution for arbitrary SAT has been established.

## Previous investigation: clause overlap is real, but scalar caching loses

The [clause-mask follow-up](clause-mask-reuse.md) tests the smaller shared structure
suggested by the preceding source-index failure. Two costly prepared sources reuse
immutable clauses at **70.32% / 70.53%** of clause visits. A checker-owned 64-bit
mask can skip a clause only when assignment overlap is impossible; collisions
trigger ordinary scanning. The bounded FIFO stores validated representation facts,
with every source reason and fixed point still checked. All **496 tests** pass.

Two matched 96-input empty-history controls, in opposite execution orders, reject
promotion. Literal work including preparation falls **4,173,407 -> 1,873,711
(55.10%)**, but total query time rises **7.37185 -> 7.56226 s** and
**7.31352 -> 7.57542 s**. Sampled four-case Python peak rises about **41%**;
first-order values are **615,971 -> 871,147 bytes**. All four databases are identical
at **33,460,224 bytes**, answers and proof records agree, and cold replay passes.
Both modes retain **88/96** closures. The three-source prepared pilot is nearly
flat in runtime. The optional cache stays disabled; no full prepared-corpus run
is justified by these controls. This is not evidence of a universal slowdown,
but it defeats an inference from a high hit rate or lower literal counts alone.

The older full-run attribution still puts about **83% of discovery time in 83
unresolved sources**. Reconstruction is its largest profiled individual own-time
entry on source 1194; a short per-clause scan is not necessarily worth caching.
No new family closes, and the historical prepared frontier remains **83 sources /
99 selected leaves / 31,203 literals**. The next ranked targets are now:

1. **Bounded, independently checked variable elimination on the unresolved
   frontier.** First measure which inputs admit small transformations, including
   recognition and possible growth. Retain exact recomposition and model lifting.
   Prefer eliminating future residual acquisition or exposing a known family to
   another attempt at scalar cache tuning. This is an investigation, not an
   established efficient solution for each unresolved category.
2. **Transport into equivalent cores and coarse shared transformations.** A
   useful representation must avoid whole recognition/checking or substantial
   output work across different CNFs. Fixed-position block overlap was measured
   only by unbounded observer sets, not implemented as a production cache. Require
   stable order and proof-reason positions plus explicit invalidation and cost.
3. **Selected proof dependencies and append-only upgrades.** Preserve failed
   acquisition traces while checking only sound required dependencies. Keep this
   lower priority than unresolved-source discovery; exact closed-plan reuse has
   a smaller measured cost ceiling.

Do not repeat source-capacity increases or per-clause dictionary caches without
a new mechanism that avoids their measured overhead. Both negative comparisons,
their complete archives and the diagnostic counters are retained. The default
policy remains **898/985** and optional prepared coverage **902/985**; those are
historical full-corpus results, not new measurements of this checker candidate.

## Previous investigation: exact object identity misses reusable structure

A cold-cache profile of source 1194 identifies independent reconstruction as the
largest individual Python own-time cost: **2,617 calls / 0.33136 own seconds** in
a 3.08000-second instrumented query. The optional [checker source index](indexed-check.md)
was implemented and tested, but its first matched control failed to improve cost.
On 96 inputs with empty history, discovery changes **6.36510 -> 6.63704 s**,
total **7.54255 -> 7.89263 s**, and sampled Python peak **615,971 -> 738,163 bytes**.
All answers, evidence and 88 closures agree; storage is unchanged. No default changes.

The key result is the failed reuse mechanism. Only **658 / 15,071** checks hit the
source-identity index. Preparation examines **4,054,848** literals, followed by
**471,454** affected-clause literal visits; the old scan examines **4,173,407**.
Avoiding unaffected scans did not avoid rebuilding nearly all indexes. On source
1194, raising the budget **32-fold** leaves both views together at exactly
**80 / 2,617 hits**, with **2,537 admissions** and **858,647 preparation literals**.
Capacity alone does not fix this measured case.

An additional bounded source-identity/assignment memo for restricted results was
also preserved. In the same isolated source it gets **498 / 3,231** restriction
hits, but checker hits only rise to **141 / 2,617**. Timings are **1.12695 s** for
the existing implementation, **1.17052 s** for indexing alone and **1.19950 s** for
the combined candidate. These are single ordered diagnostics, not general ratios.
The negative control and pilot did not justify a full 1,497-input expansion run.
The candidates remain separate, experimental and unpromoted.

A no-eviction audit bounds the exact-whole-source opportunity: **2,537 distinct
source objects represent 2,167 distinct CNFs**, leaving **370 duplicate admissions**
(14.58% of object admissions). There are still only 80 identity hits. Holding all
sources costs 2,215,640 logical index slots in this diagnostic. Exact tuple interning
could at most eliminate those 370 duplicate admissions here, before its own hashing,
equality and retention costs. It cannot combine the 2,167 different CNFs.

Next investigate **checked reuse across related but unequal residuals**, especially
unchanged clause blocks and small assignment deltas. First measure their overlap
and how much preparation can be updated locally while preserving source binding,
clause order and unit-reason positions. The older clause-support cache already
regressed, so reuse its negative evidence rather than repeating a dictionary lookup
per clause without an amortization argument. Exact whole-CNF interning is a smaller
bounded opportunity in this case, not the main expected win. Charge discovery,
local verification, invalidation, output assembly and retained space; a shared
representation does not by itself justify cheaper independent checking.

Broader equivalent-core transport, checked binary variable elimination, selected
closed-proof checking and later append-only upgrades remain open. The latest full
prepared result is still the earlier **902/985**, with 83 unresolved sources; these
new controls establish no coverage gain. See [profile and failed pilots](../experiments/results/cnf-indexed-check-profile/README.md)
and [matched empty-history evidence](../experiments/results/cnf-indexed-check-empty/README.md).

## Previous investigation: reusable evidence from unsuccessful expansion

Cost attribution changes the immediate priority: the **83 unresolved inputs use
67.35991 / 81.41598 discovery seconds (82.74%)** in the accounted run. Directly
retained closed roots use only 13.74019 seconds. A selected closed-proof checker
therefore has a smaller measured ceiling than reuse that also addresses open
expansions. The per-case attribution is preserved with the new full experiment.

The optional [prepared-probe extension](prepared-probes.md) reuses source-bound
probe traces from old **unclosed** plans, after independent checking. In the
matched 1,497-query run, 2,437 traces avoid fresh acquisition: probe attempts
fall **77,804 -> 60,972 (21.63%)**, while checked attempts stay **77,498**.
Discovery changes **79.80360 -> 78.51427 s (1.62%)** and total query time
**85.97296 -> 84.07622 s**. This is a modest single-run timing difference; some
of the total change occurs in the unchanged ordinary solver and is not a search
saving. Both modes include transactional accounting. No new family closes.

All evidence tables and the final database bytes match. Storage stays
**629,280,768 bytes**, six-case Python peak is **24,164,349 / 24,199,805 bytes**,
and full cold audit costs **77.21884 / 76.58480 s**. The new hint has one-call
lifetime and uses the existing bounded verification cache; it does not remove
old evidence or reduce the two graph caches. The empty-history control reuses
zero traces, so its timing variation cannot support this mechanism. Fresh inputs
also reuse no traces and regress **7.70214 -> 8.61204 s** in total query time.
See the
[full evidence](../experiments/results/cnf-prepared-probes-full/README.md) and
fresh/empty controls there. All 481 Python tests pass.

The next ranked targets are:

1. **Avoid repeated checking and construction inside unresolved expansion.**
   The full run still performs 110,811 simplification checks over 41,141,207
   literal visits, and new probe checking barely changes. These are operation
   counts, not a time attribution. Profile a costly unresolved source to separate
   residual reconstruction, normalization, recognizers and evidence admission,
   then test sharing an exact checked intermediate state across transformations.
   Preserve source, assignment and policy bindings, bounded cache costs and
   invalidation. Another acquisition-only cache has a limited demonstrated gain.
2. **Broaden reuse beyond an exact CNF/depth match.** There are still 83 open
   originals / 99 selected leaves / 31,203 literals. Checked binary variable
   elimination or transport into an equivalent core may expose a shared solved
   structure. Measure actual source gains and all interface/model-lift costs;
   neither a local rewrite nor a complete partition guarantees efficient closure.
3. **Check selected sound dependencies of closed plans with shared state.**
   Keep failed alternatives archived, but avoid checking them when an independent
   selected proof suffices. This remains worthwhile, with the smaller cost ceiling
   above; it was not implemented in this run.
4. **Admission and later upgrades.** Reject references whose recognition/checking
   costs exceed avoided acquisition, and allow append-only upgrades after useful
   later preparation. The original fresh control's family-only references still
   save no descendant acquisition. Neither mechanism is implemented here.

Default coverage remains 898/985; optional prepared coverage stays 902/985.
No uniform arbitrary-SAT resource bound or new Lean refinement follows.

## Previous investigation: remove archive scans; return to discovery costs

The optional [transactional accounting](residual-accounting.md) removes the
per-query residual census without changing search or discovery. On the same
prepared prefix and 1,497 queries, total query cost falls **171.12270 -> 87.88366 s
(48.64%)**. The ordinary solver portion falls **90.03441 -> 6.40760 s**;
discovery stays **80.99467 -> 81.41598 s**, now about **92.6%** of the accounted
query total. This is a bookkeeping saving on prepared history, not faster fresh
SAT search or new structural coverage. Coverage remains **902/985** in both modes.

All per-query archive totals and all three stored evidence-table digests agree.
Every seed row remains unchanged. One opening census is charged; no further
census occurs during acquisition or warm reuse. Initialization grows
**0.00098 -> 0.12228 s**. Added archive overhead is **4,096 bytes**. Warm combined
discovery-and-solver replay falls **84.36440 -> 0.61496 s**; this is not the old
discovery-only warm metric. Full cold proof audits still cost **84.49631 / 79.18184
s**, and six-case Python peaks remain **24,159,525 / 24,164,413 bytes**. The
empty-history control has no clear acquisition gain (**7.70202 -> 7.73052 s**).
The 96 fresh-input controls with prepared history improve **15.20412 -> 8.38678
s**, keeping 88 closures and identical acquired evidence. Their saved scan work
does not imply faster underlying SAT search.
The original scan-based solver remains the control; use the optional accounted
mode in future prepared-archive experiments to expose reasoning costs clearly.

The next ranked targets are:

1. **Reuse a selected sound proof without rechecking all failed acquisition
   alternatives or retaining two large decoded graphs.** Discovery is now the
   dominant measured query cost. The existing profile points to reconstruction,
   propagation and normalization; the retained-plan run checks 13,315 old nodes
   and acquires 13,560 new ones. Develop a source-bound selected-proof checker,
   preserving the full historical trace separately. Compare its cold checking,
   admission and cache costs against the current full-policy checker. A smaller
   proof representation alone does not establish cheaper first use.
2. **Transfer useful structure beyond exact prepared sources.** The 83 unresolved
   original inputs / 99 selected leaves / 31,203 literals are unchanged. Checked
   binary literal elimination and transport of successful plans into different
   equivalent cores are the next coverage candidates. Preserve shared-variable
   compatibility, model lifting and remaining branch obligations explicitly.
3. **Avoid references that save no substantive acquisition.** The previous fresh
   control's 20 references are all family leaves and save no nodes. A cheap
   admission rule needs matched total-cost evidence, including its own lookup.
4. **Upgrade cached unsuccessful plans when later preparation becomes useful.**
   This needs append-only successor identities and explicit dependency rules;
   the exact-reference implementation only benefits first acquisition.

All **476 Python tests** and the unchanged Lean build/axiom audit pass (**4,148
declarations / 1,988 theorems**). The default classification policy is unchanged
(898/985); the 902/985 result uses the optional prepared policy. The accounting
change supplies no new Lean refinement, SAT family or unrestricted polynomial
bound. See the [full matched evidence](../experiments/results/cnf-accounting-full/README.md).

## Previous investigation: reuse closed plans; expose metadata and cache costs

The [retained-plan reference](retained-plans.md) reuses an independently checked
old graph before acquiring another graph for the exact same CNF and depth. On a
common 417,370,112-byte prepared prefix, non-tiny closure improves **901/985 ->
902/985**, recovering source 1471 with no losses. Discovery drops **98.33619 ->
81.96656 s (16.65%)**, total **190.63432 -> 177.05292 s (7.12%)**, added archive
**338,288,640 -> 211,906,560 bytes (37.36%)**, and combined archive
**755,658,752 -> 629,276,672 bytes (16.72%)**. Preparation remains charged as
earlier history; this is not a from-scratch portfolio. The default stays unchanged.

The tradeoffs are retained. Six-case Python peak rises **20,124,942 -> 24,084,738
bytes (19.68%)**, and warm replay **0.27327 -> 0.41059 s**. The 96 fresh inputs
at depth two keep 88 closures, with discovery **6.57530 -> 6.80303 s**. All 20
fresh internal references point to family nodes; both modes add 1,988 nodes.
The empty-history control also gains nothing and costs 4.76% more discovery.

The next ranked targets are now:

1. **Stop rescanning the complete residual archive for metadata on every query.**
   `ResidualSolver.solve` runs a full `count/sum(length(...))` census even on a
   cached decision. A separate 12-repeat diagnostic on 21,838 rows / 65,665,771
   payload units averages **57.14 ms** per scan. Multiplying by 1,497 queries
   suggests about 85.54 seconds of bookkeeping, not an exact attribution of the
   92.18/94.98-second solver portions. Maintain exact statistics or collect them
   outside the per-query decision path, with initial reconstruction, updates and
   invalidation tested. This is the largest concrete avoidable runtime cost in
   the current measured total; it is not SAT search or a complexity breakthrough.
2. **Share verification work without retaining two large decoded graphs.** The
   new run checks 13,315 old nodes and adds 13,560 new nodes. Old-policy validation
   still checks every failed alternative, even when only a selected closed proof
   is needed. Develop a source-bound soundness checker for reusable selected
   proofs, keeping the full historical trace archived separately. No selective
   checker, bounded shared cache or general proof transport is implemented yet.
3. **Prefer references that avoid real descendant acquisition.** The full run
   has 2,127 references, including 463 old OR and 1,116 probe nodes; the fresh
   control's 20 references are all family leaves and avoid no node acquisition.
   Measure an admission rule against these retained losses. An exact match alone
   does not imply a cheaper expansion.
4. **Expand beyond exact prepared sources.** There remain 83 uncovered original
   inputs / 99 selected unresolved leaves / 31,203 literals in this optional
   prepared run. Checked binary literal elimination and transport to genuinely
   different equivalent cores remain candidates. Cached misses also need explicit
   append-only upgrades when useful preparation arrives later. None follows from
   the exact-reference rule, and fresh-input coverage has not improved.

All **469 Python tests** and the unchanged Lean build/axiom audit pass (**4,148
declarations / 1,988 theorems**). No new Lean refinement is claimed. All 63 earlier
manuscript proof blocks are unchanged. The [full evidence](../experiments/results/cnf-retained-plans-full/README.md)
preserves both complete archives, reference-kind counts, cold checks, allocation
regressions and profile. Benchmark-only failures and frozen runner versions remain
retained; completed acquisitions were recovered from verified checkpoints.

## Previous investigation: binary paths broaden coverage but add acquisition state

The [binary-path experiment](binary-paths.md) deletes wide clauses entailed by
paths in retained original binary clauses. Checked transitive reasoning raises
full non-tiny coverage **898/985 -> 901/985**: four gains, one bounded-search loss.
All ordinary SAT answers agree. Extra-depth frontier closure rises **60/106 ->
63/106**, including against an early direct-subsumption control. A fresh 96-case
sample stays at 75 closures. This established simplification is optional; the
retained default remains **898/985**.

The full matched run charges discovery **81.47602 -> 97.00720 s (+19.06%)**, total
**122.46371 -> 139.46329 s (+13.88%)**, archive **417,370,112 -> 475,529,216 bytes
(+13.93%)**, and cold replay **52.18170 -> 59.56008 s**. A separate slow-source
profile still leads with reconstruction, propagation and normalization. Shared
proofs reduce node count but increase JSON bytes versus independent paths;
even all 456,745 proposal bytes are small beside the 58,159,104-byte archive
increase. Prioritize avoiding intermediate acquisition, not proof encoding alone.

The next ranked gaps are:

1. **Carry successful plans through equivalent-state changes.** Source 1471
   isolates a concrete loss: the old successful split at variable 1 drops out of
   a four-candidate child list after sound deletion. The earlier certificate is
   retained; the two complete archives cover 902/985 inputs in union. Build a
   source-bound, independently checked reuse path before acquiring another full
   policy graph. That observed union is not an efficient combined algorithm.
2. **Share preparation and avoid duplicate intermediate states.** The pass makes
   3,555 positive reductions but acquires 3,507 additional pattern nodes overall.
   Test whether retained-binary indexes and checked reduction plans can survive
   normalization with explicit clause/name transport. Preserve verification,
   invalidation and cold replay costs; no such shared layer exists yet.
3. **Use the same relations to expose more structure.** Certified hidden-literal
   elimination could shorten clauses that cannot be deleted. Test binary-free
   states after conditioning and adversarial edits, with exact model semantics.
   This is established preprocessing, not a new tractability claim; its useful
   scheduling and full acquisition cost remain open here.

All **461 Python tests** pass, and the Lean build/axiom audit passes at **4,148
declarations / 1,988 theorem declarations**. Four new semantic lemmas prove edge,
path, clause and batch soundness; Python refinement and uniform resource bounds
remain separate. The [full evidence](../experiments/results/cnf-binary-paths-full/README.md)
preserves every gain/loss, cold-checked archive, allocation diagnostic and profile.
All 62 earlier manuscript proofs survive alongside the new proposition.

## Previous investigation: saved unit counts do not predict cheaper closure

The [checked probe-ranking experiment](probe-rank.md) preserves the entire old
candidate set and changes only order. Two reversed-order frontier runs keep
**60/106** closed but regress in mean discovery **5.19854 -> 5.44908 s (4.82%)**
and total **8.22342 -> 8.63390 s (4.99%)**. Both attempt 268 candidates, despite
26 changed orders. Fewer nodes (1,540 -> 1,524) coexist with more SQLite bytes
(35,840,000 -> 35,979,264). The policy stays optional; do not promote it.

The frozen fresh controls keep **71/96** closed and change no order. Of 39 OR
states, **36 have no binary clauses**; just **9/156** candidate positions have
paired original traces. For a normalized CNF of minimum width three, one assignment
cannot create a unit, so these missing single-variable effects cannot be repaired
by another unit-count score. Both execution orders, archives and regressions remain
retained. Original-source coverage stays **898/985**.

The next ranked gaps are:

1. **Expose interactions invisible to a single-assumption probe.** Investigate a
   bounded two-variable interface or the binary relation exposed after one split
   on the unresolved binary-free states. Require exact recomposition and charge
   candidate discovery and all branches. There is no small-interface guarantee
   for arbitrary SAT. Do not replace missing evidence with a zero-effect score.
2. **Reuse a successful plan independently of the ranking that found it.** The
   prior obstruction/baseline union remains 63/106; running both costs extra.
   Source/child-bound, independently checked plans could avoid reacquisition and
   repeated policy-key state. No such portable plan layer is implemented yet.
3. **Reuse proof work directly before tuning another proxy.** Conditioning still
   constructs and normalizes residuals, then prepares/checks their closures.
   Reusing original probe reasons there requires clause-index and variable-name
   transport; ranking by the number of reasons performs none of that transport.
   Whole-source reconstruction/normalization remains the measured dominant cost.
4. **Keep coverage preservation distinct from efficiency.** Two new Lean lemmas
   prove candidate membership and local closure invariance given corresponding
   child closures. Global finite-expansion induction also requires unchanged
   reductions/budgets and no history-dependent timeout. There is no Python
   refinement, optimality result, or new unrestricted-SAT tractability claim.

Implementation/evidence checkpoint **7b5fa22**. The full Lean build and axiom
audit pass (**4,140 declarations / 1,981 theorem declarations**). All 61 previous
manuscript proof blocks survive, with one new local-closure proposition.

All **453 Python tests** pass. Cold replay checks every saved proof/source and
preserves bytes; warm replay adds nothing. Fresh-key overhead is measured rather
than ignored. Four-case allocation diagnostics do not bound total process memory.
See the [frontier evidence](../experiments/results/cnf-probe-rank-frontier/README.md)
and [fresh evidence](../experiments/results/cnf-probe-rank-fresh/README.md).

## Previous investigation: static obstruction ranking regresses

The [matched frontier experiment](../experiments/results/cnf-obstruction-frontier/README.md)
gives the 106 previously exhausted leaves one extra conditioning level in both
modes at the same four-candidate/probe/learning limits. A new checked ranking
based on auxiliary-path source clauses closes **57/106**, versus **60/106** for
the existing ranking: three gains, six losses. Discovery **4.96403 -> 5.21714 s**
regresses 5.10%, fresh SQLite **35,840,000 -> 37,498,880 bytes**, and cold replay
**3.49873 -> 3.53507 s**. The ordinary solver varies in the opposite direction,
leaving total almost unchanged. This is a negative result; **do not promote** the
optional `ObstructionChoicesInventory` or treat it as new whole-source coverage.
The retained original policy stays **898/985**, with 87 source misses.

The next ranked gaps are:

1. **Reuse checked propagation influence instead of relying on direct overlap.**
   All six losses discard the old winning variable; five such variables lie
   outside the saved obstruction's source support. In case 4, original checked
   traces under variable 6 reach the obstruction indirectly and damage three/four
   of its four auxiliary edges. No fresh propagation was needed to recover this
   information. Test those already-proved consequences in a class-aware bounded
   choice policy that retains baseline diversity. Cases 17 and 50 are mandatory
   counterexamples: their original probes damage no saved edge but later discovery
   closes the branches. Missing traces for other candidates are unknown, not zero
   influence. Breaking one recorded path proves neither renamability nor closure.
2. **Separate successful structural evidence from the ranking that found it.**
   The two frontier policies' union is 63/106. Merely running both has extra cost;
   an efficient combined policy is not implemented. The saved proofs can inform
   a future portable-plan layer with exact source/child bindings and cold checks,
   avoiding policy-key duplication and repeated acquisition. Preserve every old
   result and measure recognition/check/serialization costs before claiming reuse.
3. **Keep the whole-source bottleneck in view.** This extra-depth frontier study
   does not replace the earlier whole-corpus profile: the retained 87 source misses
   still account for 70.6% of discovery, with reconstruction, normalization and
   indexed subset checks leading on source 1448. Broader coverage needs interactions
   across classes, not another unguided increase in search depth or pair budget.
4. **Use fresh evidence before promoting a revised heuristic.** The 106 leaves
   are development data. New seeds, signed edits and adversarial mixtures must
   accompany any follow-up comparison; keep the same budget and retain losses.
   A single selected certificate is not an isomorphism-invariant structural model,
   and small traced memory diagnostics do not bound total process memory.

All **448 tests** pass, including independent cold replay without auxiliary
rediscovery. Both complete archives, all nine changed cases, guarded-support
counterexamples and original-probe influence traces are retained. The
[proof/resource account](obstruction-conditioning.md) distinguishes raw restriction
from propagation and other-family closure. All 60 earlier manuscript proof blocks
remain, with one new obstruction-preservation proposition. Lean sources are
unchanged; no new Python refinement or unrestricted tractability result follows.
Implementation/evidence checkpoint **d25a2e5**.

## Retained baseline: 35 renamed leaves yield 29 source closures

The [terminal Horn-renaming study](../experiments/results/cnf-polarity-horn/README.md)
closes all 35 saved positive leaves and **29 additional whole inputs**, with no
lost closures: **869/985 -> 898/985 non-tiny**. Full acquisition adds 188 checked
renaming edges; the ordinary SAT solver is unchanged. Most remaining work remains:
**87 sources / 106 selected leaves / 32,404 literals** unresolved, consuming
**70.6% of discovery time**. Every remaining leaf has a checked renaming exclusion;
none is merely capped. Auxiliary UNSAT is not original UNSAT.

Single-run discovery falls **84.99193 -> 80.78495 s (4.95%)**, total **126.02211 ->
122.78419 s**, cold replay **54.89246 -> 51.32492 s** and fresh SQLite **437,620,736
-> 417,370,112 bytes**. Warm replay regresses **0.26877 -> 0.29138 s**. Six-case
Python peak falls **24,073,154 -> 20,286,004 bytes**; this excludes native SQLite,
RSS and full-corpus peak. Old and new snapshots remain retained (854,990,848 raw
bytes together). Do not describe fresh-policy comparison as freed historical space.

The next ranked gaps are:

1. **Explain the checked renaming obstructions through interactions.** Of the 106
   remaining leaves, 92 have maximum width three, 13 width four and one width
   eleven. Source-linked negative auxiliary paths identify a concrete obstruction
   to this class. Investigate shared variables across those paths and small
   interfaces whose exact conditioning exposes different recognized families in
   different branches. Compare coverage and total discovery under matched budgets;
   a conflict path alone gives no small separator/backdoor guarantee. Do not rerun
   the same recognition as though the exclusion were a budget miss.
2. **Reduce repeated acquisition while preserving these proofs.** Source 1448 is
   the current slowest unresolved discovery query. Its separate instrumented
   profile has 909 reconstructions (0.16950 s own / 0.24526 s cumulative), 566
   normalizations (0.12614 / 0.32228 s) and 118 indexed subset-certificate calls
   (0.11573 / 0.15694 s). Polarity discovery is only 31 calls / 0.04967 s cumulative.
   Exact normalization/source-state reuse is supporting work; its lookup, memory
   and invalidation costs must beat rebuilding. Nested cumulative costs are not
   additive.
3. **Test earlier renaming only as an acquisition optimization.** The separate
   0.57908 s original-root probe recognizes 555 normalized inputs, all already
   closed by the baseline; none of the 29 gains admits a whole-source renaming.
   The gains therefore need residual exposure and composition. Earlier cheap
   admission might avoid known-family preprocessing but alone will not cover the
   remaining sources. Keep its recognition budget and overlap policy explicit.
4. **Broaden evidence and avoid policy-state duplication.** This is one sequential
   synthetic-corpus comparison. Full mixed-policy migration space, industrial
   transfer, total-process memory and repeated balanced timing remain unmeasured.
   Versioned keys preserve old rows but duplicate unchanged structures between
   policies. A policy-independent structural layer needs exact evidence bindings;
   never drop the prior verified archives merely to report smaller storage.

All **441 Python tests** and the full Lean build/axiom audit pass (**4,136
namespace declarations / 1,977 theorem declarations**). Both cold archives are
byte-preserving, all 188 new edges have independently agreeing endpoints and
checked model lifts, and warm replay inserts nothing. All 59 earlier manuscript
proof blocks survive; a new polarity proposition is added. Implementation
checkpoint **86d603b**. The exact 35-leaf target is complete; unrestricted efficient
coverage and the interaction obligations above remain open.

## Previous checkpoint: one-pass checking; 35 polarity-renaming opportunities

The [one-pass checker study](../experiments/results/cnf-single-pass-check/README.md)
reduces full discovery **93.90373 -> 87.70857 s (6.60%)** and total **137.78680 ->
130.04664 s (5.62%)**, with identical 1,497 answers, profiles and archive bytes.
It shares 44,643,882 untouched literal occurrences without another retained cache.
The initial clause-support cache regressed in both pilots and remains unselected.
Cold replay regresses **57.32273 -> 57.93447 s**; six-case Python peak is essentially
unchanged (**24,072,934 -> 24,073,162 bytes**). Twelve-query ABBA BAAB means support
4.60% total / 5.23% discovery savings, with overlapping samples. Forty-eight
controls retain five regressions, especially wide clauses with many removals.

Integrated coverage remains **869/985 non-tiny**, with **116 sources / 148 leaves /
33,651 literals** unresolved. A separate checked, read-only frontier probe now
identifies **35 leaves (852 literals)** that become Horn after consistent variable
flips. It checks positive renamings directly and negative auxiliary implication
paths, with 32,018 pair constraints. This established class is absent from the
current inventory. These are leaf opportunities, not achieved source closures.

The next ranked gaps are:

1. **Integrate checked polarity renaming before further cache tuning.** The 35
   frontier certificates provide concrete broader-coverage evidence. Use a
   versioned recognizer/terminal certificate, explicit model transport and exact
   recomposition; test unlabelled signed variants, edits, exhaustive small formulas
   and fresh mixtures. Compare full acquisition and cold replay. Auxiliary
   pair-formula UNSAT excludes renamability, not SAT of the original formula.
   The method is established: [Mannila and Mehlhorn (1985)](https://people.mpi-inf.mpg.de/~mehlhorn/ftp/RenamingHorn.pdf)
   describes the pair-constraint characterization. Most unresolved literal work
   lies outside these small positives; do not infer complete class coverage.
2. **Normalization and residual reconstruction remain substantial.** The current
   run's slowest unresolved source is 1446. In its separate profile, 1,063
   reconstructions fall 0.37732 -> 0.29957 s cumulative, while normalization has
   678 calls / 0.40226 s cumulative. The new helper remains largest named own time
   at 0.20778 s. Measure identical normalization inputs and exact transport costs
   before proposing reuse; do not skip canonical identities or checker bindings.
3. **Keep the measured copying limits visible.** Wide affected clauses regress
   in all three helper-control sizes. Mutable inputs still copy; partial buffers
   may be discarded after late satisfaction. No new cache helps the selected
   method, but the source/proof graph and 437,620,736-byte archive remain. The
   conditional worst-case reconstruction bound stays O(1+A+m+L).
4. **Remaining interactions and acquisition are still open.** The 35 positive
   renamings account for only 852 of 33,651 frontier literals. Keep the other 113
   selected leaves explicit and investigate exact decompositions/relations there
   after integrating and measuring the recognized class. Closed leaves do not
   by themselves establish closed roots or uniform polynomial expansion.

All **433 tests** pass; full cold replay is byte-identical. All 58 earlier proof
blocks survive, with one new reconstruction invariant; Lean is unchanged. The
implementation checkpoint is **d0b8917**. The result, failed cache attempts,
diagnostic, bounds and concrete next frontier certificates are all preserved.

## Previous checkpoint: source-index reuse exposes checker reconstruction

The [indexed-restriction study](../experiments/results/cnf-indexed-restriction/README.md)
reuses validated immutable source indexes across assumptions, rebuilding affected
clauses and sharing unchanged tuples. All **1,497 answers, profiles and archive
bytes agree**; coverage remains **869/985 non-tiny**, with **116 sources / 148 leaves /
33,651 literals** unresolved. The independent checker still reconstructs its input
branch directly; indexed branch construction remains trusted Python.

The first full comparison is mixed: discovery **93.85938 -> 90.65563 s**, cold
replay **60.86819 -> 56.04772 s**, but total **132.36551 -> 134.44214 s** regresses.
The unchanged solver path takes 13.70% longer; one sequential sample cannot
separate variation from cache-induced process/memory effects. Twelve-query ABBA
BAAB mean total **4.81769 -> 4.35747 s** supports locality-dependent savings,
not a general full-corpus result. A reversed-order full comparison is retained
separately in the linked study. Six-case Python peak grows **1,598,364 bytes**;
SQLite stays **437,620,736 bytes**. The 32,768-unit index cap is not a byte cap.

The reversed full run balances order across two samples per mode. Paired means
are **137.36963 -> 131.36045 s total (4.37%)**, **97.29044 -> 89.16122 s discovery
(8.36%)**, and **61.16937 -> 56.70501 s cold replay (7.30%)**. Counters and archive
hashes repeat exactly. These limited synthetic controls support an optional
tradeoff; the first regression and roughly 1.60 MB peak increase remain relevant.

The next ranked gaps are:

1. **Independent simplification reconstruction is now the largest named cost.**
   Source 1194's restriction cumulative time falls **0.82784 -> 0.21269 s** for
   the same 3,399 calls. Its **2,303 simplification checks** remain at **0.27952 s
   own / 0.55562 s cumulative**; full reconstruction stays **51,574,914 literal
   visits**. Measure repeated semantic inputs before choosing exact checked-result
   reuse or independent prepared-state reconstruction. Do not treat unverified
   discovery state, mutable proof identity or incomplete source bindings as checks.
2. **Broader SAT pattern coverage remains a primary research obligation.** These
   resource optimizations add no category. Select a concrete source-entailed
   relation or exact interaction decomposition in the 116 unresolved sources;
   measure removed unresolved leaves and recognition cost. Faster unchanged
   classifications alone do not resolve the discovery gap.
3. **New/equal-source preparation and materialized output remain expensive.**
   Full operations have 241,198 hits / 275,865 calls, but still validate and prepare
   **10,412,650 literals each**, then assemble **28,938,355 clause positions**.
   Equal reallocation and fresh-append controls have no hits and regress. Sharing
   exact source descriptions or append-prefix postings needs explicit binding and
   invalidation. Reusing exact source/assignment results could avoid repeated outer
   assembly, but adds retained state and must preserve immutability.
4. **Reduce memory and check broader workloads before wider adoption.**
   The index's logical cap does not make its 1.60 MB Python peak increase free.
   Sparse reuse is favorable, while equal reallocations peak at 3.24 MB in a helper
   control. Capacity sweeps, admission policies and total-process measurements
   remain open. Retain the baseline and all regressions; do not infer universal
   wins from a warm helper stream or selected timing subset.

All **425 tests** pass; full and pilot archives replay cold byte-identically.
Tests cover 87,516 small formula/partial-assignment pairs, 4,000 random/edited
restrictions and the 148 saved frontier probes. The
[correctness and resource account](indexed-restriction.md) explains validated
immutability, strong references, fallback behavior, output sharing and conditional
word costs. The implementation checkpoint is **2809c48**. This is not a Lean
refinement or unrestricted expansion bound; earlier proofs and results remain.

## Previous checkpoint: propagation savings expose source reconstruction

The [ordered propagation study](../experiments/results/cnf-ordered-propagation/README.md)
uses affected-clause updates while preserving the exact original unit/reason and
first-conflict order. All **1,497 answers, profiles and database bytes agree**;
coverage stays **869/985 non-tiny**, leaving **116 sources / 148 leaves / 33,651
literals** open. The ordinary SAT solver and independent proof checker are unchanged.

Full discovery falls **111.13169 -> 97.76173 s (12.03%)**; total **154.63114 ->
137.59078 s** also includes variation in the unchanged solver. Twelve-query ABBA
BAAB means support **5.38111 -> 4.83970 s total** and **5.08503 -> 4.55072 s discovery**.
Cold replay barely changes (**63.40473 -> 62.61754 s**). Six-case Python peak grows
**22,258,170 -> 22,474,570 bytes**; SQLite stays **437,620,736 bytes**. Results are
synthetic, with no universal speedup or full-process memory bound.

The next ranked gaps are:

1. **Share source restriction and residual reconstruction across assumptions.**
   Source 1194 still performs **3,399 restrictions** and **2,303 simplification
   checks**. After propagation cumulative time falls **0.79372 -> 0.31541 s**,
   restriction is the largest named own-time cost (**0.40355 s own / 0.82048 s
   cumulative**); checking has **0.27656 / 0.54588 s**. Full restriction and
   reconstruction visits remain **82,210,169 / 51,574,914**. Prepare immutable
   source indexes and update exact affected state, with source/assumption bindings
   and independent reconstruction checks. Charge lookup, construction and invalidation.
2. **Discover new structure in unresolved interactions.** The same 116 sources
   still need certified relations or exact decompositions. This optimization
   makes experiments cheaper but adds no category. Investigate the most informative
   remaining interactions rather than increasing blind budgets or only tuning caches.
3. **Amortize or avoid wasted occurrence-index preparation.** Every closure still
   builds fresh state: **32,071,047 index entries** versus **5,356,250 affected
   occurrence visits** in the full run. A reverse chain benefits greatly, but a
   two-clause prefix conflict with 1,024 unrelated clauses regresses **0.00248 ->
   0.41982 ms**, and its Python peak grows **1,752 -> 528,448 bytes**. Test shared
   preparation or a cheap prefix/lazy-index rule before calling this pointwise
   better. Forward-chain and colliding-integer-hash regressions are also preserved.
4. **Evidence/cache space remains secondary.** The 1 MiB proof-check cache,
   duplicated evidence and unintegrated implication relevance filter retain their
   previous opportunities. They do not remove first discovery or source scanning.

All **417 tests** pass. Full and pilot cold archives replay byte-identically;
32 adversarial controls and balanced timing runs preserve exact traces. The
[algorithm-level trace proof](ordered-propagation.md) gives a conditional
O(1+L+m log(m+1)) word-operation account per closure, with map and bit-cost caveats.
It is not a Lean refinement or unrestricted SAT bound. The implementation checkpoint
is **bbd2607**; the scan baseline remains available. Next runs should start from
these new measurements, not repeat the now-completed propagation experiment.

## Previous checkpoint: exact proof reuse reduces acquisition cost

The [bounded check-cache study](../experiments/results/cnf-checked-probe-reuse/README.md)
preserves every previous structural result and the complete archive byte for byte.
On the same **1,497 inputs**, coverage stays **869/985 non-tiny**, with **116 open
sources / 148 leaves / 33,651 literals**. A successful complete probe check may be
reused only under the same full source/proof/policy key. The cache is ephemeral,
starts empty on cold replay, returns fresh decoded results and retains at most
**1 MiB of serialized strings**. Edits and evictions cause rechecking. The old
checker remains available; persistent proofs and identities do not change.

Full single-sample total time falls **168.30879 -> 150.39216 s (10.65%)**, discovery
**125.59834 -> 108.60557 s**, and cold replay **71.60183 -> 62.58623 s**. Twelve-query
ABBA BAAB means are **6.17550 -> 5.33388 s** total. These are synthetic measurements,
not a general SAT speed guarantee or significance result. SQLite stays exactly
**437,620,736 bytes**; six-case Python peak grows **21,161,086 -> 22,258,162 bytes**.
The cap excludes allocator/LRU overhead, transient construction and original state.
All full modes share the existing archive rather than retaining another copy.

The next ranked gaps are now:

1. **First-time propagation and remaining clause scans.** Source 1194's separate
   profile reduces restrictions **5,763 -> 3,399** and simplification checks
   **4,657 -> 2,303**, but propagation stays **2,221 calls** and becomes the largest
   named own-time cost. The full workload still visits **105,860,805 propagation
   literals**. Test reusable occurrence indexes or affected-clause propagation
   across assumptions, charging preparation and invalidation. Preserve or
   explicitly version proof order: changed traces can alter learning selection.
2. **New structure in unresolved interactions.** This cache preserves coverage;
   it does not discover new relations. The 116 open sources need certified
   relations or exact decomposition hypotheses, measured against their remaining
   interactions. Neither larger blind budgets nor cache hits solve this gap.
3. **Lower cache/evidence overhead without losing useful reuse.** Full operations
   have 34,971 hits / 57,798 lookups, but serialize **135.221 MB** of key data and
   decode **29.376 MB**. A 256 KiB pilot gets 1,385 versus 1,387 hits at 1 MiB;
   compare full-corpus memory and time before choosing a smaller cap. The earlier
   relevance filter (29,897 -> 7,505 implication candidates, no coverage gain)
   remains a separate possible evidence reduction. First-check and discovery
   costs cannot be replaced by unverified context.

All **410 tests** pass. A found tuple/list serialization alias is fixed by checking
the old original-attempts container requirement before lookup; its counterexample,
preliminary pilot and aborted runs are preserved. Both final full modes and all
five guarded pilot modes replay cold byte-identically, including alternatives,
source bindings and solver certificates. Reports have **62 fingerprints**, with
explicit snapshots for superseded pilot scripts. Lean source and its preceding
4,130/1,972 audit remain unchanged; this cache has no formal Python refinement.
The implementation checkpoint is **9aba9df**. No unrestricted efficiency or new
tractable class follows from exact repeated-check reuse.

## Previous checkpoint: five more closures; proof replay remains dominant

The [implication-subset study](../experiments/results/cnf-implied-subsumption/README.md)
reuses binary consequences of original checked probes as signed-subset witnesses.
It adds no propagation phase. Earlier subset exposures retain priority, and failed
pools/searches persist. A separate indexing-only mode preserves old certificates
and archive identities while skipping impossible equal-width comparisons.

Across **1,497 queries**, closure rises **864 -> 869 / 985 non-tiny**, with gains
**857, 1185, 1289, 1368 and 1467** and no losses. The old subset rises **837 -> 841 /
949**, and new-query closure **27 -> 28 / 36**. This is structural coverage, not a
change to the independent SAT decision solver. All answers agree.

Full single-sample operation time is essentially unchanged: **169.84716 ->
169.80609 s**. Discovery is **127.44196 -> 126.71711 s**, SQLite **438.288 ->
437.621 MB**, and cold replay **71.70525 -> 69.97623 s**. Logical node payload
instead grows **178.289 -> 179.396 MB**, and six-case Python peak **20.390 ->
21.161 MB**. Fewer nodes (25,752 -> 25,047) do not establish lower retained state.
The optional candidate is a coverage improvement, not a general speedup.

The next gaps are ranked by the evidence:

1. **Reuse exact restriction and proof-checking state.** The largest unresolved
   source remains 1194, at **1.67226 s** discovery. Its separate profile again
   has **5,763 restrictions, 4,657 simplification checks and 2,221 propagations**.
   These costs dominate its own-time profile even after indexing. Share prepared
   clause/assumption state or checked evidence with explicit dependencies and
   invalidation; measure acquisition and replay, not just fewer logical probes.
2. **Discover structure in the remaining interactions.** There are **116 open
   sources / 148 distinct selected leaves / 33,651 literals** in the expanded
   corpus. Filtering the existing implication pools exposes **no additional
   selected leaf**. Broader coverage needs new source-entailed relations or a
   different exact decomposition, with charged discovery and recomposition.
   Do not increase probe budgets blindly or confuse an unresolved classification
   with an efficient solver for that category.
3. **Keep only useful implication witnesses, while charging recognition.** An
   offline control retains proved binaries only when they fit a long clause of
   the original minimal core. It reduces the pool **29,897 -> 7,505 (74.90%)**
   across all 3,684 nonempty pools and preserves all **82** encountered implication
   exposures. It uses **2,278,253 relevance comparisons**; augmented subset tests
   fall **8,990,250 -> 7,138,675** per search/check. This is an unintegrated storage
   and recognition opportunity, not a measured total-cost saving or a theorem
   preserving every syntactic family. Keep exact origin proofs and old results.
4. **Reduce duplicated state and cold replay.** Search fields grow **3.963 ->
   9.030 MB**, including **5.087 MB** of implication data. Many failed pools remain
   useful evidence of limits but need not duplicate all underlying proof state.
   Exact references or shared immutable evidence require source binding and
   cold reconstruction. There is no full-process or lifetime archive space bound.

All **403 tests** and the **4,130 / 1,972** Lean declaration/theorem audit pass.
The new semantic lemma composes entailment and signed-core equivalence; Python
refinement and unrestricted resource bounds remain open. Full, pilot and previous
archives replay byte-identically, and both new reports have **59 fingerprints**.
See the study for balanced timing and complete old-archive indexing controls.
The next run should use the profiled restriction/checking bottleneck or a concrete
coverage hypothesis; the smaller implication pool alone does not improve coverage.

## Previous checkpoint: four closures, costly failed subset searches

The [signed-subsumption study](../experiments/results/cnf-signed-subsumption/README.md)
integrates the previous frontier witnesses. Only exhausted unresolved leaves
are searched; a reduced core is followed only when an existing basic family
recognizer succeeds. Exact retained signed witnesses, source-index coverage,
normalization and model lifts are checked; failed searches persist. Earlier
reductions and budgets stay fixed. All previous solver results remain available.

On **1,461 queries**, non-tiny closure rises **833 -> 837 / 949**, with gains on
**977, 1044, 1053 and 1365** and no losses. The old subset improves **806 -> 810 /
913**; new-query closure stays 27/36. This is a coverage gain, not a SAT speedup.
The full single sample grows **145.71977 -> 156.17943 s**, discovery **105.46141 ->
117.30413 s**, SQLite **404.410 -> 408.302 MB**, cold replay **61.80056 -> 66.82085 s**
and six-case Python peak **19.997 -> 20.390 MB**. Twelve-query balanced controls
instead average **7.28617 -> 6.98024 s**, but include all four gained sources;
they do not establish a full-corpus speedup. Keep the policy optional.

The ranked gaps now have direct evidence:

1. **Avoid unsuccessful recognition work while extending proof reuse.** The
   3,753 terminal searches expose only 31 local families. Discovery and checking
   each perform 33,367,619 subset comparisons. Of these, **27,083,138 (81.17%)**
   compare distinct normalized clauses of equal width and cannot succeed.
   Length buckets should skip those comparisons with identical certificates;
   preserve a fallback/check for nonnormalized inputs if the helper admits them.
   This is the immediate acquisition-cost fix, not a measured saving yet.
2. **Use already proved implications to expose more families.** Eight of the
   remaining selected leaves become 2-CNF in an offline checked control when
   all original-probe binary consequences are made explicit. This includes
   consequences filtered as binary-transitive: redundant propagation clauses
   can still be useful subset witnesses. Sources **1185, 1289 and 1368** could
   complete their present plans; five other affected sources retain an open leaf.
   Integrate after earlier priorities, retain original proof dependencies, and
   charge enumeration, indexing, witness checking and cold replay. These are
   prospective gains, not part of 837/949.
3. **Reuse restriction and proof-checking state.** The largest unresolved source,
   1194, costs **1.60328 s** discovery. Its separate profile has 5,763 restrictions,
   4,657 simplification checks and 2,221 propagations. This remains a broader
   runtime target than subset comparisons alone. A reuse design must bind each
   fixed point to its exact clauses and assumptions; changed clauses invalidate
   unproved reuse. Fewer logical probes alone do not establish less total work.
4. **Control retained state and cold replay.** The new policy has fewer nodes
   (24,367 -> 24,122) but more logical node bytes (161.206 -> 166.021 MB). Search
   certificates/profiles alone add 3.706 MB; source bindings also grow. Indexed
   or shared evidence needs exact dependencies and byte-level measurements.
   Six-case traced Python memory is not RSS or a global memory bound; preserving
   multiple policy archives retains all their state.
5. **Cover the irreducible interactions.** There remain **112 open sources / 149
   selected leaves**, with 32,043 literal occurrences. Most subset reductions
   do not expose a basic family. The next methods must recognize interactions
   beyond this bounded search, with exact recomposition and charged discovery.
   An explicit unresolved category completes a partition, not an efficient
   solution for every member. No unrestricted-SAT polynomial bound follows.

All **395 tests**, three full/pilot/previous cold checks per group and **56 report
fingerprints** pass. The Lean build audits **4,129 / 1,971 declarations/theorems**,
including three signed-core semantic lemmas. Python refinement and global
acquisition/storage guarantees remain open. Next run: remove the provably futile
subset comparisons, verify identical coverage/certificates on the saved archives,
then integrate the saved implication-subset controls under a matched total-cost
comparison. Retain the naive policy and its regression as the control.

## Previous checkpoint: preserve useful probes, expose hidden 2-CNF

The [activity experiment](../experiments/results/cnf-activity/README.md) retains
old informative continuation candidates, omits checked unchanged pairs, and
fills freed positions with active original-core variables. It uses the same
batch, two phases and four-variable cap. On **1,425 queries**, closure remains
**806/913 non-tiny**, with no source gains or losses. Source 956 is recovered from
the preceding core-order regression. Source 977's unresolved part shrinks
**two leaves / 138 literals -> one leaf / 22 literals**, but remains open.

Continuation attempts fall **31,741 -> 7,184 (77.37%)**. This mainly avoids
unchanged pairs; active-plus-novel probes grow **5,334 -> 5,569**. All 421 old
local reductions in 3,001 saved states survive; sixteen clear states gain one.
All 255 earlier transition controls have a reduction. Local progress preservation
is justified, but different reductions/descendants still prevent a global
coverage monotonicity claim.

**Do not claim a runtime speedup.** The single full-run times are **161.35645 ->
134.22746 s**, but the unchanged solver varies **44.42359 -> 35.13847 s**. Balanced
ABBA BAAB trials on eight queries give mean totals **3.85140 -> 3.88671 s**, slightly
slower for activity. Cold replay also grows **55.11608 -> 57.63553 s**, and warm
lookup **0.27624 -> 0.34976 s**. SQLite shrinks **376.205 -> 375.824 MB**, logical
node payload **148.632 -> 147.670 MB**, and six-case Python peak **20.265 ->
19.997 MB**. Keep all single-sample and memory-scope limitations; the policy stays
optional.

**Highest-priority discovery target: checked signed-clause subsumption exposing
tractable cores.** The saved [frontier witnesses](../experiments/results/cnf-activity/frontier-subsumption.json)
remove 217 redundant clauses / 666 literals from 105 of 147 selected open leaves,
using 672,003 subset comparisons. Seven resulting cores are recognized as 2-CNF.
For source 977, binary clauses `(-7,3)` and `(-3,9)` subsume its two remaining
ternary clauses. The pattern crosses previous workload groups, and exposes an
existing tractable family rather than adding another bounded probe rule.

Integrating these exact reductions could complete the current selected plans of
**977, 1044, 1053 and 1365**; sources 907, 1179 and 1363 would still have another
open leaf. These are prospective completions, not executed source gains. Keep
signed subset witnesses tied to retained source clauses and reconstruct exact
child normalization/model lifts, including variables that disappear. Preserve
earlier recognized-family priorities. Compare recognition/checking/acquisition,
all unsuccessful searches, storage and cold replay on all relevant states, not
only the 147 selected frontier leaves. Reuse the existing positive-subsumption
ideas where appropriate, but its restricted solver path is not this signed
inventory reduction. Subsumption itself is established, not a general SAT advance.

Supporting targets follow the measured frontier: 61 inconclusive continuations
(12,984 literals), 39 empty continuations (10,639), 46 clear passes without a batch
(4,264), and one without initial binary candidates (283). Source 1194 costs
1.47590 s discovery; restriction, unit checking and propagation dominate its
separate profile. A larger initial-variable pool alone misses most of this gap.
Share preparation or propagation only when matched total costs justify it.

All **388 tests**, the unchanged Lean audit (**4,126 / 1,968 declarations/theorems**),
three full, three pilot and three prior cold archive checks pass. Both new reports
have 53 matching fingerprints; diagnostics and repeated timing trials retain
input/script hashes. Efficient arbitrary-CNF discovery and global resource bounds
remain open.

## Previous checkpoint: core-only probe choices

The [core-order experiment](../experiments/results/cnf-core-order/README.md)
changes only the continuation ranking, using the existing learned batch and
probe budget. On **1,389 inputs**, non-tiny closure falls **776 -> 775 / 877**:
no source gains, and source **956** is lost. The local hint-study case 97 closes,
but original source 977 remains open. Do not promote the new policy.

Total time falls **120.81853 -> 116.67493 s** (3.43%), discovery **88.69202 ->
85.68326 s**, SQLite **347.566 -> 346.976 MB**, cold replay **50.51029 -> 47.82982 s**,
and six-case Python peak **20.265 -> 19.623 MB**. These are single sequential
samples; the unchanged solver's time varies by 1.13 s between combined modes.
Selected unresolved literal occurrences worsen **26,137 -> 26,734**. No source
coverage improvement or general speedup follows from removing 8,772 ranking
reconstructions. All earlier policies and results remain available.

**Highest-priority discovery target:** use checked delta activity to combine
active original-core candidates with newly ranked candidates, under the existing
continuation budget. At equal CNF/depth, **239** old learned reductions become
clear and **16** old clear states gain a reduction. In **189/239** local losses,
all original core pairs are inactive under the learned batch. At source 956,
core choices `(9,17,18,2)` are all inactive; the old newly ranked variable 14
supplies the useful conflict. Reusing only original choices misses it.

Across all **255 gained/lost local states**, active core variables plus novel
old-ranking variables fit within four choices. Seven other changed shared states
already need five, so this is an observed opportunity, not a uniform bound.
Original clear traces must be checked before delta tests; inactive pairs retain
valid references. Unchanged unit sets cannot produce a new common/equivalence
witness in this procedure. Compare the proposed combined choices first on these
controls, 956 and local 97/original 977, then on full sources. Changed first
conflicts and descendants can still lose coverage. No combined policy or recovery
result has yet been implemented.

Supporting priorities:

1. **Preserve old choices while sharing preparation.** The first-cap batch is
   the prefix of the deterministic sixteen-clause pool for caps at most sixteen.
   Reuse the checked pool and ranking inputs rather than reconstructing them.
   This can isolate savings without changing coverage; no saving is measured yet.
2. **Reuse propagation state where it dominates.** The new frontier has 102 open
   sources and 142 distinct selected leaves (99 learning-clear, 43 clear).
   Source 1194 costs 1.45407 s discovery; restriction, unit checking and propagation
   dominate its separate profile. Probe-kind nodes account for 87.079 MB, but the
   probing field alone is 15.273 MB: whole-node payload is not proof-only storage.
3. **Integrate portable hints only within a justified continuation.** Keep exact
   source/context bindings and delta validation; the earlier extra pass still
   has unfavorable costs. Avoid adding another pass to repair a ranking miss.

All **380 Python tests**, the unchanged Lean build/axiom audit (**4,126 / 1,968**
declarations/theorems), three full, three pilot and four previous cold archive
checks pass. Both new reports have 50 matching fingerprints. The implementation
and preserved measurements are pushed in **544054d**. Global efficient arbitrary-
CNF discovery, compact closure and acquisition/storage bounds remain open.

## Previous checkpoint: portable proofs and the ranking hypothesis

**Previous proposed experiment (now tested above):** rank continuation variables on the original core,
using the existing learned batch and existing number of passes. The
[portable-hint control](../experiments/results/cnf-hint-transport/README.md)
isolates a local miss caused by ranking: both the transported and rediscovered
batches close local case **97** with core choices `(4,5,7,19)`, and both stay open
with baseline-continuation choices `(4,5,7,11)`. Test this case and original source
**977**, then the old **956/1024/1189** controls and full old/fresh source workloads.
Derive choices from the exact core or checked complete original traces, never an
unchecked stored list. Charge ranking, later graph changes and any losses. Do
not add another probe pass or promote the optional hint overlay.

The transport primitive now works on **1,005 eligible hint occurrences** from
**494 learned-parent edges** (449 prior and 45 fresh): every translated reason
prefix yields an independently checked child-core proof without fresh search.
There are **984** distinct core/clause records. Replay needs no parent graph;
the exact core and hint context still bind proof use and heuristic plans. This
implements portable evidence, not complete cross-generation planner integration.

The local hint overlay closes **224/494** children versus **223/494**, with no
losses. Its one gain is an **unselected alternative of source 977**, and is absent
from every saved selected source path. Do not add it to the previous **719/805**
original-source coverage. The controlled two-by-two comparison shows that the
gain needs different probe choices, not a stronger inherited batch.

The extra-pass policy costs **16.82765 versus 14.41354 s**, plus **0.95129 s** for
transport preparation. SQLite grows **55.120 -> 63.885 MB**, cold replay
**4.70738 -> 7.72522 s**, and six-core Python peak **7.372 -> 7.431 MB**. Ordinary
nodes fall 2,167 -> 1,999, but proof and context payloads add **2.181 + 3.097 MB**;
logical probes rise **14,468 -> 16,136**. The favorable reason-prefix scan count
(11,510 versus 287,160 fresh-search literal visits) is not an end-to-end speedup.
Fresh proof search is conditional on supplied candidate clauses; all parent
checking, preparation, storage and replay remain charged.

Prior priorities before the core-order test:

1. **Core-ranked continuation under the existing budget.** Isolate the measured
   variable-choice cause, avoiding reconstruction of a redundant learned view
   solely for ranking. Whole-source coverage and cost decide whether to adopt it.
2. **Integrate portable evidence into an existing pass.** The saved diagnostic
   finds 1,456 inactive and 102 active hint deltas at 196 original-probe cores.
   Reuse only after original closure validation and an inactive-delta check;
   these are opportunities, not saved probes. Avoid repeating a fresh pass that
   then falls back to another full discovery pass.
3. **Reduce proof/context duplication if integration earns its cost.** Full-core
   hint keys, per-hint normalization and separately replayed plan contexts now
   outweigh ordinary-node savings. Context omission is not a valid compression.

All **374 Python tests**, the full Lean build/axiom audit (**4,126 declarations /
1,968 theorem declarations**) and four new cold archive replays pass. All 51
fingerprints match; previous archives are preserved. These are sequential
synthetic local controls, not unrestricted-SAT bounds or an industrial speedup.

The preceding parent-scoped core study follows with its whole-source denominators.

The full **1,317-input** core experiment gives **719/805** non-tiny closures
versus **718/805** for baseline and fixed order, with no losses against either.
All close **14/24** fresh random cases; **86** core sources remain unresolved.
Total time is **94.870 / 97.402 / 97.835 s**, SQLite **284.111 / 284.299 / 284.094 MB**,
and cold replay **40.281 / 41.160 / 40.384 s** for baseline/fixed/core. Core is
3.13% slower than baseline in this single sample. Six-case Python peak rises
**20.022 / 20.127 / 20.265 MB**, excluding native memory/RSS and full-corpus peak.
The selected pilot's savings do not generalize; keep this policy optional.

At the saved 956 parent, all policies force only `14=false`. Removing the
redundant additions yields its **54-clause original restriction**, which closes.
This controlled core is shared exactly in a regression test. Within the full
core archive, however, **no two learned parents share a child core**. The measured
gain comes from altered descendant discovery, not demonstrated large core merging.
There are 449 successful learned edges, 385 with changed normalized child syntax.
All parent hints and proofs remain persistent; children receive no inherited hints.
The 907 absent eligible transported hint occurrences include the 319 immediately
reacquired clauses above, not 319 distinct implications or measured saved seconds.

Prior targets, now partly tested by the portable-hint experiment:

1. **Transport checked hints without changing core recognition.** Test the measured
   reacquisition opportunities and coverage controls before full old/fresh inputs.
   Charge proof/context storage, transport, checking and cold replay. Larger
   learning batches alone are not the experiment. Cached implication proofs do
   not automatically remove probes required by the current ranking policy.
2. **Reuse checked propagation state to expose additional structure.** The new
   largest unresolved source is **1297**, a fresh 48-variable CNF: **1.47150 s**
   discovery and 456 unresolved literals. Restriction, unit checking/propagation
   and literal helpers dominate its separate profile. Only one successful learned
   parent occurs there, so hint transport alone will not remove its main cost.
3. **Share proof payloads where the measurements justify it.** Probe records are
   **72.386 MB / 63.76%** of core logical node bytes. Source bindings, checking and
   cold replay must survive any compression. Neither physical database pages nor
   a successful selected pilot measures broad semantic-core compression.

The selected frontier contains **124** unresolved leaves, 86 learning-clear and
38 clear. All **366 Python tests**, the full Lean build/axiom audit (**4,125
declarations / 1,967 theorem declarations**) and four full, four pilot and four
preceding archive replays pass. Both reports' 47 fingerprints match. Primary and
diagnostic timings ran sequentially without concurrent tests, builds or commits.
Core construction adds work; no efficient arbitrary-SAT coverage or uniform
storage bound has been obtained.

The preceding fixed-order investigation follows with its own corpus and timings.

The [fixed-order experiment](../experiments/results/cnf-learning-fixed-order/README.md)
implements the previous target and explains why it is insufficient. All 1,281
inputs give the same **692/769** non-tiny and **18/24** fresh random closures under
baseline, selection and fixed order. Both selected modes gain 1024 and lose 956;
fixed order changes no source closure relative to selection. Seventy-seven
sources remain unresolved. Total time is **77.916 / 82.421 / 80.720 s** and SQLite
**252.244 / 252.498 / 252.391 MB** for baseline/selection/fixed. Fixed remains
3.60% slower than baseline in this single sample; no general timing advantage
over selection follows from its 2.06% lower sample time.

At source **956**'s saved 18-variable parent, baseline and fixed order both force
only `14=false`. Their restricted original CNF is **the identical 54-clause core**.
Baseline retains three extra learned clauses and its 17-variable, 57-clause child
closes. Fixed retains four and its 17-variable, 58-clause child stays open with
eighteen unresolved literals. All additions are entailed, so the two child
relations agree. Recognition, ranking and full persistent keys nevertheless see
different representations. The [checked controls](../experiments/results/cnf-learning-fixed-order/mechanisms.json)
retain the exact clauses and acquired child paths. This is a concrete opportunity
for certificate-backed core sharing, not cheap general semantic canonicalization.

Fixed order adds **6,418 ranking reconstructions** across acquisition/checking.
Nodes rise **16,052 -> 16,126**, logical probes **89,782 -> 90,713**, logical node
bytes **100.113 -> 100.315 MB**, cold replay **33.506 -> 34.309 s** and the same
six-case Python peak **20.022 -> 20.127 MB** versus baseline. Selected unresolved
literals fall **18,362 -> 17,971** without greater source coverage. The current
frontier has **111** distinct leaves, 71 learning-clear and forty clear. Source
**1194** remains the largest discovery case (1.417 s), dominated by restriction
and unit checking/propagation. Sharing proof records and avoiding repeated scans
remain supporting targets, after the representation-sensitive discovery experiment.

All **358 Python tests**, the unchanged Lean build/axiom audit (**4,122 declarations /
1,965 theorem declarations**) and four full, four pilot and three preceding archive
replays pass. Both reports' 43 fingerprints match. Measurements ran sequentially
without concurrent tests, builds or commits. Restricted exactness, incomplete
structural coverage and the open arbitrary-SAT construction bound remain distinct.

The preceding selection investigation follows; its smaller corpus has its own
denominators and timing samples.

The [bounded-selection experiment](../experiments/results/cnf-learning-selection/README.md)
implements the previous target: choose four clauses from at most sixteen proved
candidates by saved-closure activation and origin diversity. The thirteen-source
pilot gains source 1024; the complete 1,245-input comparison also loses source
956. Non-tiny closure stays **662/733**, fresh random closure **16/24**, with **71
source misses**. Total time rises **71.417 -> 73.194 s (+2.49%)**, SQLite
**227.385 -> 227.832 MB**, cold replay **29.815 -> 30.359 s**, and the same six-case
Python peak **20.022 -> 20.121 MB**. These are single sequential samples, without
concurrent tests, builds or commits during measurements. Keep the policy optional.

The saved [path controls](../experiments/results/cnf-learning-selection/selection-paths.json)
explain the key gap. At 1024, both batches use the same four choices and activate
the same single saved closure; only the new clauses refute its assumption. At
956, neither batch activates any original closure. The old choices first force
variable 14, the new choices variable 16, under either batch. All four local
controls report a reduction, but the actual new source plan later stays open.
Therefore activation counts, origin diversity and a coarse reduction label
miss consequential interactions. Track the first conflict and the resulting
child structure. The locally improved common reduction on 1189 still does not
close that source; preserve it as a negative control.

The [complete diagnostic](../experiments/results/cnf-learning-selection/mechanisms.json)
retains all 606 changed selection parents, including 126 reorder-only cases,
their four checked local controls, and the previous 94 selected unresolved leaves.
Local counterfactuals are not whole-source coverage. Selected unresolved literals
fall **17,687 -> 17,327**, yet nodes rise **14,592 -> 14,653** and logical probes
**82,036 -> 82,782**. Of the current 103 selected leaves, 66 remain learning-clear
and 37 clear. The largest discovery case remains **1194** (1.464 s); restriction,
unit checking/propagation and literal helpers dominate its separate profile.
Avoiding repeated scans and sharing probe records remain supporting cost targets.

All **353 Python tests**, the full Lean build/axiom audit (**4,122 declarations /
1,965 theorem declarations**), and three full, three pilot and four preceding
archive replays pass. The subset theorem preserves source models independently
of selection quality. The capped candidate filter can miss useful alternatives;
there is no complete efficient arbitrary-SAT construction or compactness result.

The preceding studies follow in reverse order. Their denominators and timings
belong to their own matched corpora and must not be compared as a single fixed
workload.

The [closure-reuse comparison](../experiments/results/cnf-probe-closure-compact/README.md)
retains all 1,209 sources and all 13,066 semantic nodes, including alternatives.
Coverage stays **634/697 non-tiny inputs**, **15/24 fresh random inputs**; 63
sources remain unresolved. Checked references avoid 14,705 of 17,548 continuation
propagations; 672 active repeated assumptions and 2,171 fresh ones still propagate.
The compact sample changes total time **62.759 -> 61.687 s**, SQLite **197.104 ->
196.096 MB**, cold replay **26.785 -> 25.094 s**, and the same six-case Python peak
**20.378 -> 20.022 MB**. These are small single-sample effects; a checkpoint commit
overlapped part of compact acquisition, so retain the timing limitation.

The [first representation](../experiments/results/cnf-probe-closure-reuse/README.md)
saves 807,098 local proof bytes but grows SQLite to 200.323 MB because an added
policy field is repeated in full keys. It remains preserved. Replacing the
local-learning version tag keeps a distinct namespace and removes that overhead.
The current compact logical node total is 78.533 MB; probe nodes still occupy
49.281 MB. Source 1194 is the largest remaining discovery case, with restriction,
unit checking/propagation and literal helpers dominating the separate profile.
The fixed-point/derivation lemmas pass Lean's full audit (4,121 declarations /
1,964 theorem declarations); all 348 Python tests and complete new/old archive
checks pass. No Python/SQLite refinement or unrestricted resource bound follows.

The [bounded-learning study](../experiments/results/cnf-probe-learning/README.md)
implements the preceding implication target. On 1,173 inputs, non-tiny closure
rises 604/661 -> 607/661, including a fresh 48-variable UNSAT source (18/24 ->
19/24 fresh closure). There are no observed lost closures. However, total time
rises 48.177 -> 52.697 s, SQLite 163.533 -> 168.268 MB, cold checking 20.785 ->
22.013 s and the targeted Python peak 18.466 -> 20.378 MB. Keep it optional.
The extra pass is charged; total probe budgets are not equal.

The attribution diagnostic matters: fixed continuation choices without added
clauses still reduce 49 of 229 successful learning nodes, including both old
source gains (956/1057). The selected node at fresh gain 1155 stays inconclusive
without additions. Thus stronger propagation and changed choices both matter;
local counterfactuals do not prove whole-source coverage or free recognition.
All 1,709 failed learning attempts remain archived. Logical node bytes grow
63.466 -> 66.573 MB despite four fewer nodes; batch/continuation JSON alone is
1.946 MB. Selected unresolved literals fall 12,686 -> 11,106. Support reduction
or fewer nodes alone is insufficient for low total acquisition cost.

The largest remaining discovery case is now **1063**, at 1.208 s main discovery.
Restriction, unit checks/propagation and literal helpers dominate a separate
profile. Probe nodes occupy **41.132 / 66.573 MB** logical payload. Reusing checked
closures and sharing their proof records targets these measured costs while
retaining the useful learned propagation. The follow-up above measures that opportunity without adding coverage. Fifty-four source cases remain structurally
unresolved; efficient arbitrary-CNF construction and compact coverage are open.

The [signed-equivalence study](../experiments/results/cnf-probe-equivalence/README.md)
implements the preceding target. Seven of sixteen selected source misses close
in the pilot, with slightly lower time and storage. On the full 1,137-input
comparison, closure rises 567/625 -> 574/625 non-tiny sources, but fresh random
closure stays 18/24. Time rises 38.293 -> 39.731 s, SQLite 130.597 -> 135.569 MB,
and cold checking 15.208 -> 15.856 s. Keep the policy optional. All seven gains
are old cases and three are variants of one input. The prior common policy and
all unsuccessful traces remain preserved.

The full run acquires 624 equivalence rewrites merging 1,145 variables across
nodes; 431 shared exact parents retain identical probe lists. Still, probes rise
37,049 -> 41,039, pattern nodes 9,584 -> 9,952 and logical bytes 50.062 -> 52.575
MB. Selected unresolved literals fall 10,300 -> 9,674. The six-case traced Python
peak falls 14.564 -> 11.586 MB, but this excludes native memory and full-corpus
peak. Local compactness, targeted live allocation and total durable storage must
remain separate accounts.

Probe nodes occupy **32.136 / 52.575 MB** logical payload. The remaining 48-variable
case 1061 again spends most profiled own time in restriction, unit checks/propagation,
normalization and literal helpers. Occurrence-driven scans and shared checked
rewrite chains remain supporting work. The new implication opportunity extends
beyond equivalence blocks, but neither its counts nor the successful reductions
provide efficient closure of arbitrary SAT.

The [common-consequence comparison](../experiments/results/cnf-common-consequence/README.md)
implements the previous target, with a narrow gain and a total-cost regression.
On 1,101 inputs it closes 537/589 non-tiny cases versus 536/589; fresh random
closure remains 40/64. Time rises 32.122 -> 32.759 s, SQLite 104.436 -> 107.758 MB
and cold checking 12.033 -> 12.563 s. Keep it optional. Although arbitrary
conditioning candidates and selected unresolved literals fall, probes rise
29,280 -> 31,745. Common facts require no new probe at the same node, but their
reduced children trigger new work. Do not equate smaller residuals with lower
total acquisition or promote all archived opportunities to claimed root gains.

Probe nodes now dominate logical storage (23.647 of 40.749 MB), and the largest
remaining 48-variable discovery case again spends most profiled own time in
restriction, unit checks/propagation, normalization and literal-processing
helpers. Occurrence-driven scans and shared rewrite chains remain supporting
cost work. The selected equivalence opportunity will not explain all larger
3-CNF misses; preserve those cases as a separate unresolved group.

The [failed-literal comparison](../experiments/results/cnf-failed-literal/README.md)
implements the preceding target. On 1,025 matched inputs, closure rises from
358/513 to 484/513 non-tiny cases and from 19/64 to 51/64 fresh random cases.
Time falls 27.111 -> 18.878 s, SQLite 93.143 -> 65.057 MB, and cold checking
10.079 -> 6.412 s. Twenty-nine cases remain open. Probing every binary variable
on these misses closes only two more, while inventory time rises 6.817 ->
11.495 s. Do not respond by raising the global cap unconditionally.

Probe nodes now dominate logical payload: 12.545 of 22.743 MB. The largest
remaining discovery case spends most profiled own time in restriction scans,
unit propagation/checks, normalization and their literal helpers. Reusing
existing implications is the primary discovery target; sharing forced chains
and avoiding repeated scans are supporting cost targets. No complete efficient
arbitrary-CNF partition or bounded total acquisition follows.

The [fused-edge comparison](../experiments/results/cnf-fused-conditioning/README.md)
implements the previous intermediate-state target. All 3,999 archived OR plans
across three policy pairs retain their choices and final child relations. On
shortest-clause ordering, nodes fall from 11,224 to 6,281, SQLite from 96.911 to
65.573 MB and total time from 21.170 to 17.638 s, with unchanged 330/437 coverage.
Frequency and combined unit/pure processing also improve. Targeted six-case
traced Python peaks fall, while the earlier easy-case diagnostic slightly grows;
all scope limits and the in-memory pilot runtime regression are retained.

The remaining shortest-clause node payload is mainly unresolved CNFs (12.124 MB)
and OR nodes (11.510 MB), rather than discarded simplification intermediates.
All 107 non-tiny misses remain, including the fresh 20/32-variable 3-CNFs. This
now favors stronger checked discovery over another unconditional representation
change. Repeated recognition still increases with fused incoming edges and is
supporting work if it dominates the next probe profile.

The optional balanced-short-clause policy improves cap-four unit-only coverage
from 322/437 to 330/437 but raises total time from 17.203 to 20.246 s and SQLite
from 79.118 to 96.911 MB. It tries fewer candidates yet acquires more nodes:
9,162 -> 11,224, with repeated child references falling from 3,344 to 2,469.
Simplification nodes account for about 91% of increased logical node payload.
This identifies a representation/reuse gap, not a reason to enable the heuristic
by default. Relative to combined unit/pure processing it gains six cases and
loses five. Keep both comparators. The rule is an established-heuristic variant,
not a new family certificate or an efficient unrestricted classification.

The frozen-policy holdout gain is only two of 72 fresh formulae. All 32 new
3-CNFs on 20/32 variables remain open under every measured policy, including
eight frequency candidates. A cheaper checked closure could support budgeted
lookahead that investigates these interactions. More candidates alone raises
total time to 42.110 s for 332/437 closure; this is not the preferred next step.

Checked unit/pure simplification now closes all 36 old misses and exposes the
matching/parity core without conditioning. At depth two, total non-tiny coverage
rises from 217/329 to 290/329; total analysis plus solving falls from 8.097 to
7.154 s and SQLite from 39.727 to 31.732 MB. Units alone reach 289/329 in 6.604 s:
keep that faster comparator rather than enabling both reductions unconditionally.
Pure-only and depth-zero regressions are retained. These are standard reductions
in an analysis layer; the separate decision solver already has unit propagation.

Supporting opportunities remain checked decision integration (the largest single
operation still solves an original affine source), native affine boundary rows
(one renamed cap miss), and avoiding repeated scans/unused parent profiles on
long unit/pure chains. Prioritize these when they enable discovery; arbitrary
SAT still has no proved small decomposition or uniformly polynomial acquisition.

The [projection study](../experiments/results/cnf-affine-projection/README.md)
implements exact affine projection with a bounded CNF encoding and checked model
lifting. It closes all six growing coupled controls at depth zero, including
128 equations/258 variables projecting to two variables and one clause. On 775
inputs, depth-two analysis plus solving falls from 4.471 to 3.750 s and SQLite
from 22.913 to 19.030 MB. That checkpoint adds no depth-two closures on the original
664 inputs; its 36 misses were later addressed by simplification. The small memory diagnostic grows, and mixed-case
overhead and encoding-budget failures are retained. Three new Lean theorems
establish semantic composition with invariant leftovers, not Python refinement.

The largest remaining measured cost on the 258-variable coupled control is now
ordinary solving of the original source: 565 of 579 ms, versus 13 ms discovery.
Using checked projected decisions could avoid this duplication; it is supporting
integration work alongside the primary discovery target. Native affine boundary
rows would avoid exponential CNF re-encoding. Neither improvement is implemented.

The [affine extraction study](../experiments/results/cnf-affine-patterns/README.md)
implements the previous support/sign-pattern target. Exact extraction plus checked
elimination closes 14 of the previous 50 unresolved inputs, leaving 34 seeded
CNFs and the coupled matching/parity pair. The eight seeded gains use small
unit/binary contradictions after conditioning, not large hidden XORs. On 733
sources, depth-two analysis plus solving falls from 3.305 to 2.901 s and SQLite
from 14.324 to 13.386 MB; on the original 664, time is almost unchanged (1.847
versus 1.841 s). Pure affine controls improve, while coupled controls retain
extra recognition cost without closure. Depth-zero storage increases. This is
still an additive analysis layer, not a faster general SAT solver.

The preserved [first inventory](../experiments/results/cnf-pattern-inventory/README.md)
is implemented: seven recognition outcomes retain overlaps in 24 observed root
cells. Beyond 512 exhaustive tiny sources, whole-formula tests explain 39/152
inputs, components 45/152, one conditioning level 57/152 and two levels 102/152.
The last mode leaves 42 seeded CNFs plus four structural cases and their variants
unresolved. Full analysis plus solving takes 2.021 s versus 0.301 s for solving
alone, and SQLite grows from 0.385 to 6.459 MB. It is an analysis tool, not a
speedup. The persistent result includes all failed alternatives and cold checks.

The propagation profile remains useful evidence: a pinned 2,048-variable chain
spends 2.67 s in preparation, with about 98% of instrumented time in repeated
propagation scans. The queue improvement is now supporting work, prioritized
when it enables discovery experiments or exposes new structural reuse.

Bounded equivalence retry is implemented as an optional layer. At 1,024
variables, total time falls from 0.78490 to 0.05932 s; at 4,096, from 11.88170
to 0.27261 s. The matched raised-global-budget comparator is slightly faster
on these chains and also solves dense controls that the targeted policy rejects.
There is no evidence that targeted escalation has lower expected total cost.
For supporting optimization work, investigate inert-posting compression/cost
estimation on the dense 1,024-variable miss (0.893 s versus 0.117 s with a larger global
budget). Parity remains the next repeated structural miss (32 fallbacks /
0.175 s / 326 KB). Successful matching preparation remains another profile target.

Matching repair is implemented. It removes all 80 old matching misses and keeps
the equivalence gains. The larger 32-block, 8-choice case falls from 8.303 s /
20.33 MB to 0.253 s / 0.424 MB. Mixed-base extraction and searching around
non-unit coupling conflicts remain important cross-category gaps, but their
current controls are small; scale/profile them before ranking their total saving.

## Current cost map

These matched synthetic measurements do not establish a globally dominant cost
across a representative SAT workload distribution. They inform the discovery
priorities without replacing the coverage objective.

The arbitrary-CNF history/residual code is an experimental Python path. The
production restricted-family engines and Lean semantic results are separate;
their capabilities are not already integrated into one verified general solver.

| Workload regime | Current costly work and evidence | Most promising investigation |
| --- | --- | --- |
| A local change needs several variables to move together | Equivalence blocks and matching paths now repair successfully. The 32-block, 8-choice matching case falls from 8.303 s / 20.33 MB / 33 bases to 0.253 s / 0.424 MB / one base. The original 40 parity misses remain. | Parity-preserving directions; component-local discovery and proposal search guided by coupling conflicts. |
| Unit implications activate in an unfavorable scan order | The pinned 2,048-variable chain takes 2.67 s to prepare. About 98% of a separate instrumented preparation is in propagation; 16.78 million charged literal visits for 8,189 source occurrences. | Supporting optimization: queue newly forced values and update affected occurrences; preserve independently checked reason traces. |
| Recognized equivalence repairs succeed | Optional bounded retry reduces the 4,096-variable chain from 11.882 to 0.273 s, including 0.217 s preparation. Every moved member/posting is still visited. | Shared group assignments/certificates and affected interfaces, with cold reconstruction and count invariants maintained. |
| A recognized move exceeds the fixed budget | Retry removes the ordinary-chain miss. Dense 1,024-variable control still takes 0.893 s with fallback, versus 0.117 s at global budget 32,768. A contradictory block incurs 40.36 rather than 31.01 ms expansion. | Compress inert postings and improve cost estimates; retain both extra-work losses and missed savings. No optimal budget policy established. |
| Matching moves succeed | At 32 blocks of 8 choices, initial preparation is 206.58 of 253.08 ms. A warm move changes four indicators, visits 32 postings per pass and allocates 439 trie nodes. Cold final replay is slightly slower. | Profile base preparation and cold checking; do not optimize two-edge path search while initialization dominates. |
| A small update defeats pure model reuse | New affected-clause repair removes all 32 original-control fallbacks. On matching size 16 / 128 protected flips it reduces operation time from 3.478 s to 0.147 s and logical payload from 12.46 MB to 0.158 MB. | Keep these gains while avoiding unnecessary index preparation; shared source/dependencies remain needed on genuine fallback. |
| A general residual escapes tractable recognizers | Branching creates distinct residuals; each is normalized, checked and persisted. There is no polynomial bound on their number. Existing matching recognition reduced one restricted example from 5,191 residuals to one. | Expose tractable components and small interfaces before branching; preserve useful state when a component changes class. |
| Reuse succeeds and the logical update is cheap | In the new 128-addition UNSAT diagnostic, SQLite execution and transaction-context exit account for about 87% of exclusive profiled time. | Reduce redundant archive work while preserving durability and version identities. |
| Sparse, very long variable identifiers | Near 2^1024, 32 updates retain 32,801 trie nodes. `map_get`/`map_set` account for about 62% of exclusive time in the new diagnostic. | Compress unary paths; compare exact-key representation and cold reconstruction costs. |
| The old assignment already satisfies every addition | Affected-clause indexing raises peak traced Python allocations from 249,217 to 473,849 bytes versus pure repair on the matched compatible stream. | Lazy or workload-selected index preparation, with activation cost charged. |
| One change affects many clauses | At 4,096 affected clauses, avoiding a new base still increases operation time from 109.99 to 125.48 ms; index preparation takes 103.32 ms. | Budget index activation and maintenance by anticipated reuse, not merely by avoided solver calls. |
| Restart, export or repeated events dominate | Cold repair replay can cost more than an isolated final base. Repeating a unit 128 times retains 10,719 logical bytes versus 1,393 for full-source semantic deduplication. | Separate shared semantic state from exact event provenance; measure cold validation and output costs explicitly. |

Evidence: [matched repair comparison](../experiments/results/cnf-repair-history/README.md),
[affected-clause comparison](../experiments/results/cnf-affected-history/README.md),
[joint equivalence comparison](../experiments/results/cnf-equivalence-history/README.md),
[retained matching comparison](../experiments/results/cnf-matching-history/README.md),
[bounded budget comparison and preparation profile](../experiments/results/cnf-budgeted-history/README.md),
[coordinated-change diagnostic](../experiments/results/structured-repair-gaps/README.md),
[new diagnostic profiles](evidence/2026-11-08/reuse-cost-profile/README.md),
[general-CNF investigation](arbitrary-sat-expansion.md). Times are individual
samples, not significance estimates. Profile percentages describe instrumented
diagnostics only. SQL execution is not a measurement of disk I/O alone.

The previous large gain came from eliminating repeated acquisition, not just
speeding up an already cheap append. On size-16 matching SAT plus 128 fresh units,
repair reduced 129 bases to one, operation time from 2.619 s to 0.073 s and
logical archive payload from 12,020,154 to 100,706 bytes. That opportunity is
already implemented for pure repairs. Its speedup must not be counted again as
evidence that the next optimization will produce the same gain.

## How each hourly run chooses work

1. Read the discovery plan and select one gap that can expand certified pattern
   coverage or explain a substantial unresolved cell. Use current cost evidence
   to judge whether the discovery is useful, not as the sole selection criterion.
2. Make the classifier, overlap policy, recognition certificate and exact
   decomposition/recomposition rule explicit. A failed recognizer is not proof
   of nonmembership or UNSAT. Track unresolved cases rather than dropping them.
3. Compare on matched unlabelled inputs, exhaustive small cases and adversarial
   mixtures/edits. Charge discovery, verification, state size, persistence and
   cold replay. Preserve failures and counterexamples.
4. Implement or prove one concrete improvement, persist its scope and costs,
   update the unresolved-cell priorities and commit/push verified checkpoints.
   Known-family optimization is secondary unless it enables this experiment.

Do not turn this into repeated status analysis. Keep complete coverage, exact
recomposition, compactness and efficient discovery as separate obligations.

## Ranked gaps across SAT categories

### 1. Discover categories and characterize unresolved interaction

The initial [audited pattern inventory](sat-pattern-discovery.md) is complete
for the stated bounded policy. Next, split its unresolved cells with useful
structural invariants. Forty-eight remaining inputs exclude every tested pattern;
two exceed the parity cap while failing the other tests. None of those outcomes
proves hardness or excludes semantic equivalence to a broader tractable class.
The current controlled misses include complete exclusion cubes, coupled matching
and parity, and an activated guarded CNF. Exact support/sign-pattern discovery
is the next concrete probe; random-CNF coverage must be reported alongside the
structured controls. Preserve separate construction and composition obligations.

### Supporting optimization: avoid repeated propagation scans

Occurrence-driven propagation remains a measured opportunity: 2.67 s preparation
on the pinned 2,048-variable chain, with about 98% of a separate profiled run in
propagation. Queue newly forced values and update affected occurrences, retaining
independently checked reason traces. Charge construction, queue memory and cold
replay. Schedule this when it supports discovery, rather than automatically
placing it ahead of the user's research objective.

### 2. Reuse coordinated structural changes

The preceding one-variable repair was too narrow even on easy subclasses. The
[diagnostic](../experiments/results/structured-repair-gaps/README.md) supplies and
independently validates a coordinated change at every rejected step:

| Structure | Preserved internal invariant | Appropriate change |
| --- | --- | --- |
| Literal-equivalence block | All equalities, including signed variants | Implemented for complementary binary pairs in a base; change all dependent variables and independently check the final state. |
| Affine equations A x = b over GF(2) | A(x + z) = b when A z = 0 | Apply a nullspace direction, potentially changing many variables. |
| Matching component | Choice coverage and resource exclusivity | Implemented for strict whole matching bases; retain endpoints and unit pins, search an alternating path, then check all affected clauses. |
| Horn component | Consequences of the retained facts/rules | Propagate a changed requirement with retained reasons; check negative constraints and couplings. |

Equivalence and matching now have measured implementations; parity and Horn
maintenance remain proposals. The joint comparison automatically discovers the
equivalence blocks, charges their recognition and preserves all old constraints.
On 32 blocks of 32 variables it reduces operation time from 2.4689 to 0.06676 s,
logical storage from 3,792,631 to 98,663 bytes, and peak traced Python allocations
from 45,575,163 to 1,925,402 bytes. Cold final query grows from 40.88 to 44.42 ms.
Repeating the last known update from its parent after restart takes 88.32 versus
45.98 ms; these archives already contain that result. That checkpoint's matching
control still retained 33 bases / 2,267,324 bytes; the following matching-state
implementation removes those fallbacks.

The generic joint record contains a changed-variable list, not trusted structural
claims. The matching adapter now supplies automatically discovered moves to it;
nullspace discovery remains open. Initial binary-pair discovery is cached
per base and invoked only after scalar failure; additions do not enlarge the
discovered blocks. Nonpaired implication cycles, new equalities and blocks beyond
the optional retry's size/density/identifier limits remain failures. A corrected signed benchmark forces 32 actual
repairs; the initial already-compatible signed control remains archived.

**Implementation obligations:** aggregate all true-literal count changes before
checking the final assignment. Intermediate one-variable states may violate
clauses, so repeated calls to the existing operation cannot implement a joint
repair. For a certified internal component E and remaining constraints G, a move
that preserves E still needs to preserve affected clauses of G and satisfy the
new addition. Earlier deltas belong to this check. A derived equivalence alone
does not certify preservation of every source clause using those variables.

Skipping internal clause checks also does not maintain their existing count-map
entries. Update them, or retain a typed component state with explicit invalidation
and charged reconstruction when a different engine needs those counts. Group
assignment representations can avoid rewriting every dependent variable, while
full witness export remains output-sized. Bounds must charge moved variables,
affected interfaces, discovery and maintenance, not only the number of groups.

**Completed acceptance checks:** 23 matched cases, 46 new archives, 255 Python
tests and the Lean axiom audit pass. The new archives' 1,144 versions and 869
residuals cold-check without changed bytes; 82 prior archives also replay
unchanged. Couplings, signed equalities, contradictions, repeated changes,
exact count recomputation and forged records are checked. Lean proves the
semantic final-state protection rule, not the Python count/index implementation.

**Completed matching checkpoint:** 37 matched cases retain 74 new archives,
1,414 versions and 608 residuals, all cold-checked without byte changes; 58 prior
archives also replay unchanged. All 261 tests pass. At 32 four-choice blocks,
operation time falls from 0.92416 to 0.04882 s, logical storage from 2,267,324 to
50,257 bytes, and peak traced Python allocation from 24,840,875 to 1,192,534 bytes.
The code retains choice/resource/unit-pin tries and updates only changed paths.
Cold final replay increases from 17.93 to 20.25 ms. No new Lean graph refinement
is claimed: matching moves use the existing joint semantic protection theorem.

**Remaining matching gaps:** one chosen path per literal can fail a non-unit
coupling although a longer valid path exists. Whole-base recognition misses a
matching component beside an unrelated equivalence component. Spare resources
permit valid models with extra true choice indicators, outside the retained
exact matching view. These controls all remain SAT but need fallback. Unit
constraints guide search, whereas arbitrary coupling clauses only enter final
checking. Recognizing subcomponents and using failed checks to guide a bounded
alternative-path search are promising, with their own discovery/maintenance cost.
Old versions and sources must remain available through every class transition.

Retaining a known matching and using alternating paths under edge deletions is
established in [Régin (1994), pp. 364–366](https://cdn.aaai.org/AAAI/1994/AAAI94-055.pdf).
The implemented contribution is a checked persistent integration with explicit
full-source accounting, not a new matching algorithm or a general CNF guarantee.

### Completed baseline: single-variable affected-clause repair

This is the broadest concrete implemented improvement: assignment validity is independent
of whether the model came from Horn solving, 2-SAT, matching, affine elimination
or general search. The preceding pure-repair interface only accepts a changed
literal whose opposite is absent from the whole parent source. The new
`AffectedRepairHistory` checks affected-clause counts and retains the older path
as a comparator; it is not automatically selected by the production solver.

For example, with `F = (y) AND (NOT x OR y)`, assignment `x=false, y=true`
satisfies F. Appending `(x)` can safely flip x; purity rejects it because `NOT x`
occurs in F. The retained control repeats this pattern 32 times. The new
interface now accepts all of these changes without new acquisition.

A stronger sufficient condition is to maintain each old clause's number of true
**distinct signed literals**. If a currently false literal l is set true, then

```
new_count(C) = old_count(C) - [opposite(l) in C] + [l in C].
```

Accept only if all affected old clauses still have a positive count and the new
clause is satisfied. Clauses containing neither sign are unchanged. The formula
also handles tautologies containing both signs; duplicate literal occurrences
must not inflate the counts. Exact signed occurrence lists and counts must refer
to the current version, including all earlier deltas and older branches.

For one candidate x, this requires O(|D| + occ(x)) logical literal/clause visits
with suitable indexes, plus persistent index, arithmetic, certificate and storage
costs. The affected set can include the entire formula. Trying many candidates
must be budgeted. Independently safe flips cannot be composed using stale counts;
joint repairs require joint changes to the counts and a new check. Failure to
find a bounded repair supplies no UNSAT verdict.

**Completed checks:** 35 matched cases include growing protected histories,
occurrence degree, contradictions, duplicate literals, tautologies, compatible
updates, sparse IDs and coordinated changes. That checkpoint passed 249 tests; old versions
and cold verification are preserved. Lean proves the semantic protection rule,
not the count-map implementation. The 512-flip control falls from 5.059 s to
0.327 s and 8,921,728 to 83,082 logical bytes. The size-16 matching control reduces
peak traced Python allocation from 86,261,287 to 2,837,728 bytes. Cold replay and
index preparation become more expensive; see the retained losses above.
Single-variable
local search is classical; the research question here is checked persistent reuse
and its full cost, not novelty of flipping a Boolean variable.

### 3. Retain propagation and class-specific intermediate state

The residual prototype caches exact normalized residual results, but rebuilds
many intermediate structures. A failed fast path can therefore discard useful
work even when most of the source is unchanged.

In particular, `_visit` stores a successful residual as its CNF and a flat model;
it does not retain the matching, implication graph or other producer state.
`PositiveHistory.prepare` stores the full source on a new base. These two choices
explain why solver-result caching does not yet provide persistent component-state
reuse. A component witness forest and immutable source references would also
avoid repeatedly flattening/copying unaffected models, with reconstruction and
variable mappings charged when a full witness is requested.

SAT categories overlap. An equivalence chain is simultaneously Horn, dual-Horn,
2-CNF and affine. Retain several checked views of one shared source component
instead of making its identity depend on a single class label. Common objects
should expose source/dependency references, assumptions, interface variables,
verdict/witness or refutation, and an explicitly exact or one-sided summary.

| Category | State worth retaining | Recognition, maintenance and limitation |
| --- | --- | --- |
| Horn / dual-Horn | Derived literals, dependency reasons and a propagation queue. | Replace repeated full propagation scans with affected work. Distinguish proved consequences from arbitrary choices in a model. Additions preserve old consequences; deletion requires dependency retraction. A new implication can still force a global cascade. |
| 2-CNF | Implication edges, SCC/condensation information and contradiction paths. | Check that new clauses remain binary or isolate the nonbinary interaction. An edge can merge many SCCs; arbitrary constant update time does not follow. |
| Matching / reducible positive cores | Matching, choice/resource graph, reduction witnesses and Hall certificates. | The new adapter retains the graph and selected endpoints for strict whole bases. Core reductions, component-local extraction, extra selected indicators and arbitrary coupling-guided search remain open. |
| Explicit affine/XOR | Row basis, rank changes and projected boundary equations. | Reuse the existing restricted engine through checked extraction/source bindings. Recognizing hidden XOR structure in arbitrary CNF is additional work. New independent equations can change every relevant boundary. |
| Disjoint or bounded-interface components | Component identities, dependency graph and exact boundary summaries. | Update affected components and stop propagation when their summary is unchanged. Coupling components or increasing width may invalidate the cheap decomposition. |

Prioritize the category where a profile shows repeated construction to be costly.
Do not implement five dynamic data structures merely because all are available.
The current propagation loop repeatedly scans clauses; implication SCCs, matching
and connected components are still reconstructed for new uncached residuals.
The matching history adapter avoids that acquisition only when its proposal works. These are
concrete maintenance gaps, not yet evidence of an end-to-end speedup.

### 4. Reduce hard interaction between otherwise easy components

This has the largest potential effect on search growth, but less immediate
measurement support than the repair control. Two components that are individually
satisfiable need not have compatible assignments on shared variables. Store or
derive an exact boundary relation

```
R_C(b) = there exists an assignment to C's private variables satisfying C at b.
```

Then reuse unaffected relations across source changes and across solver
categories. An affine basis, binary implications or a bounded diagram/table can
represent particular relations compactly; no one representation is compact for
all projected CNFs. Explicit tables may require 2^|b| entries. Converting between
representations, proving equivalence and discovering separators all need budgets.
A necessary condition must not be mistaken for the complete relation.

Before ordinary branching, investigate whether a small set of decisions splits
the residual into independently tractable parts, potentially of different types.
Choose decisions by exposed structure as well as occurrence count; charge the
lookahead. Measure distinct residuals and total work on mixed Horn/2-CNF/affine/
matching instances with controlled interface size and on adversarial overlap.

This direction is established in work on
[heterogeneous backdoors](https://www.cs.ox.ac.uk/standa.zivny/publications/gmosz14aaai-preprint.pdf)
and [component backdoor depth](https://drops.dagstuhl.de/opus/volltexte/2022/16984/pdf/LIPIcs-ESA-2022-46.pdf).
Those results motivate parameterized investigations; they do not guarantee cheap
discovery or a small parameter for every CNF. Our irreducible positive-overlap
encoding already shows why merely combining individually easy clause groups
does not give an unrestricted polynomial solver.

### 5. Share source, certificates and summaries across class transitions

Use durable clause identities, source deltas, assumptions and checked dependency
references as the common interface. A component changing class should not force
copies of unaffected components or invalidate facts whose dependencies still hold.
Separate exact event/source history from the shared semantic compilation cache.
SAT witnesses must satisfy the updated source; UNSAT refutations remain applicable
under conjunctive additions, with their source references checked.

The current residual key sorts/deduplicates and compacts ordered variable names;
it is not a full semantic or arbitrary-isomorphism canonical form. Try budgeted
type-specific normalization and candidate indexes followed by exact verification.
Do not assume an efficient arbitrary semantic-equivalence oracle. KD-trees or
similarity search can propose candidates but cannot establish reuse soundness.

The existing affine engine is useful evidence that repeated kernels can be
shared, but its successes and normalization costs belong to a restricted input
representation. Integration with the general CNF history needs a checked source
interface and measurements of recognition, conversion and proof reuse.

### 6. Remove representation costs where solving has already disappeared

Compress unary trie paths for long sparse identifiers and consider lazy support
index preparation for streams already satisfied by the current model. Activation
must reconstruct all earlier constraints and charge that cost. Physical input
and exact identifier output still cost their encoded length.

Repeated semantic no-ops should share state, but keeping every version identity
still requires provenance. Repeated events can share payloads or be run-length
encoded when exact reconstruction remains possible. Do not claim constant total
space for an unbounded version history.

On already-UNSAT streams, persistence currently dominates the new profile.
Investigate redundant SQL/serialization work or explicitly batched transactions
if the interface permits them. Do not claim a speedup by silently weakening the
guarantee that acknowledged updates are durable. Cold validation checkpoints must
also retain a stated trust boundary; skipping checks of an untrusted archive is
not free reuse. This priority moves upward when cheap-update streams dominate.

## Bounds and evidence still missing

Let M be the number of distinct acquired residuals and L_i their encoded sizes.
The prototype performs normalization, recognition, checking and persistence over
these residuals; storing full keys/certificates charges their aggregate sizes.
Reducing per-node overhead does not bound M polynomially. Likewise, incremental
maintenance helps only if affected structure or repeated summaries stay small.

When rejected updates repeatedly acquire copied prefixes of sizes L_t, source
storage alone can grow with their sum. Constant-size additions and a fresh copy
at every step can give quadratic cumulative source storage. Accepted repair on a
fixed base instead stores that base plus deltas and version references. Its
pure-repair assignment/support trie retains base nodes plus O(sum_t (d_t+1)b_t) copied
nodes and O(T) roots, with d_t addition length and b_t identifier bit length.
The stronger affected-clause index adds occurrence entries and persistent count
paths, with per-step path bound O(d_t*b_t + (r_t+1) log(m_t+2)), where r_t is the
affected clause count and m_t the parent clause count. Retained histories can
therefore still accumulate substantial state even when every update is accepted.
These node counts exclude integer/pointer/SQL byte overhead and cold rebuilding.
Joint repair adds the q_t moved variables: accepted retained paths are bounded by
O((d_t+q_t)b_t + (A_t+1) log(m_t+2)), with A_t distinct affected clauses, plus
posting entries and roots. It still scans the sum of moved variables' occurrence
lists. Discovery, cached block maps and repeated encoded move lists are additional;
see [the expanded accounting](resource-bounds.md#9-simultaneous-repair-in-the-experimental-cnf-history).

The next evaluation gap is a common workload matrix spanning categories and
their transitions, with growing easy and hard interactions, repeated and novel
components, sparse/dense identifiers, cold and warm histories. Record disjoint
phase times where possible, end-to-end time, retained logical/SQLite bytes,
allocation/RSS scope, replay time, residual count, fallback count and affected
clause/interface size. A competitive incremental-CDCL baseline is also missing
for this prototype. Five diagnostic samples cannot establish a global ranking.

No general small-interface, compact closure, bounded repair or uniformly
polynomial acquisition theorem has been established. The restrictions and
resource charges above remain necessary even when precomputed answers are cheap
to reuse.
