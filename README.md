# Oracle Machines

A perspective on **resource accounting for learned reasoning**: how preprocessing,
stored knowledge, neural representations, and exact solvers redistribute computation
between acquiring an answer and using it later.

**Terminology:** SAT with no fixed size cap remains the satisfiability problem.
UNSAT denotes unsatisfiable valid formulas and is coNP-complete. An invalid
encoding is neither a satisfiable nor an unsatisfiable formula.

The central architectural conclusion is that **the efficiency rationale for
combining System 1 and System 2 survives either resolution of P versus NP**.
Either way, the relevant comparison is avoided computation versus acquisition,
retrieval, verification, and control costs. Actual savings depend on the workload
and implementation.

The exact reuse identity applies to **every decidable language**, including
problems in PSPACE, EXPTIME, and EXPSPACE. This generality concerns the cost
comparison. Cheap certification, compact storage, and efficient acquisition need
their own justification, and finite tables for an undecidable language do not
provide a uniform computable way to construct them.

The project connects established ideas from complexity theory, knowledge
compilation, memoization, and amortized inference to the interaction between fast
and deliberative computation. Its contribution is an explanatory synthesis; the
finite-domain constructions do not establish a collapse of unrestricted complexity
classes.

## Paper

[The latest forced reduction](research/source-local-forcing.md) proves one
frontier variable true and shrinks the open source from **23 variables / 93
clauses to 22 / 88**, using one new recognition state. Coverage remains **58/83**.
The matched local expansion worker takes **0.137 seconds** with history available;
**55.49 seconds of global recomposition** is now the largest measured cost.
All **148 relevant tests** pass, and the new checkpoint preserves earlier results.

[Source-local expansion](research/source-local-expansion.md) now preserves the
next four ordinary probes while loading only their needed historical premises.
With full authoritative history already available, the matched one-block worker
falls from **11.00 to 0.127 seconds**; initial restoration still costs **20.59
seconds**. Coverage remains **58/83**. Resume from the checked source-local
checkpoint named in the [priority record](research/structural-reuse-priorities.md).

The latest [probe-and-split continuation](research/exhausted-probe-split.md)
raises structural coverage **57/83 -> 58/83**. The last ordinary probe is clear;
ranking its retained cofactor pairs then completes the ten-variable residual.
One branch reuses the empty-CNF terminal, while seven new recognition states
reduce the other to Horn form. Both checked plans close the original 48-variable,
204-clause development case. All earlier evidence remains retained.

The preceding [affine/one-clause investigation](research/affine-one-clause.md)
raises structural coverage **56/83 -> 57/83** on the reused development set.
Checked linear algebra closes a case missed by shallow probes, without expanding
the affine relation into CNF or changing the historical inventory. The positive
proof is 1,056 compressed bytes; 21 targeted tests and cold replay validate it.
All 28 remaining selected leaves lack directly recognized parity equations.
The [priority record](research/structural-reuse-priorities.md) identifies the next
discovery and verification gaps. No unrestricted-SAT complexity claim follows.

The earlier [saved-cofactor investigation](research/saved-trace-splitting.md)
raises structural coverage **52/83 -> 53/83** and independently proves the new
32-variable original SAT. A checked split reuses two clear assumption traces,
requires both cofactor plans and adds five pattern nodes. All **581 tests** pass.
The local timing control shows no replay speedup; cold checking still dominates.
Four acquired open targets remain for bounded cofactor reuse and comparison
against further probing.

The preceding [retained-learning investigation](research/retained-learning-batch.md)
raises structural coverage **47/83 -> 52/83** on the reused development originals;
all five gains are independently SAT. It reuses saved clauses and prefixes,
adds 141 later blocks and 77 pattern nodes, and preserves all older evidence.
Six successful augmented blocks have clear matched controls; four controls also
find forced values. All **577 tests** pass. Cold validation
still dominates runtime. The next targets are a ten-variable residual with one
untried probe and 18 learned formulas with unused later variables.

The earlier [resumed-probe investigation](research/probe-resumption.md) raises
coverage **39/83 -> 45/83**, with four SAT and two UNSAT gains on reused
48-variable development cases. It also certifies that five remaining sources
have **no single-assumption unit refutation**; more plain single-variable probes
cannot close those sources. Their saved paired traces may still support stronger
common consequences, equivalences or learned implications. All **557 tests** pass,
with previous results preserved. Cold verification remains the dominant cost.

The preceding [prefix-continuation investigation](research/probe-continuation.md)
shares checked probe prefixes and advances bounded discovery. Coverage rises
**36/83 -> 39/83**, with one SAT and two UNSAT gains on reused 48-variable
development cases. The matched warm probe substep is **2.09x faster** than
rediscovering the same prefix; full cold verification still dominates runtime.
All **547 tests** and cold artifact/reference checks pass. The eight-table history
retains all earlier results, 51 new continuation blocks and 45 new proof nodes.
This extends coverage and avoids repeated probing; it is not a whole-SAT speedup.

The preceding [probe-window investigation](research/probe-window.md) finds that the
growth escape first succeeds by promoting an already refutable assumption into
the bounded probe window. Continued probes preserve the original recognizer and
raise selected-original coverage **32/83 -> 36/83**: three SAT gains and one UNSAT
gain, all with 48 variables. Removing the growth-exception route retains all 36
closures. All **543 tests** and cold checks pass. The new 70 window records and
81 proof nodes add work and storage; this is broader coverage, not a speedup claim.

The preceding [growth-escape investigation](research/growth-escape.md) closes the
saved core with one explicitly budgeted three-clause growth step and four new
probing states. A finite checked witness propagates the result through a saved
coupled route, raising selected-original coverage **31/83 -> 32/83**. Removing
the growth edge from the same graph removes the gain. A separate solver confirms
UNSAT for the gained 48-variable original. All **540 Python tests** and cold
artifact checks pass; costs and previous results remain preserved. This is one
development case, not a general SAT speedup or a new full-corpus measurement.

The preceding [coupled-pivot investigation](research/coupled-pivots.md) reuses the
saved divergent routes and adds a cap covering every new recognition state,
including descendants. Its 25 original-input trials add 32 proof nodes but leave
coverage at 31/83. Only one unresolved core is new to the history; all 662 allowed
ordered pivot pairs there grow by at least seven clauses. This identifies a
concrete admission barrier for the next experiment. All **535 Python tests** pass,
and all earlier results and new trials persist. The preceding
[ancestor-selection study](research/frontier-pivots.md) retains the matched early
versus later-node controls.

The preceding [subset-search investigation](research/anchored-subsets.md) preserves
the exact recognition certificates while filtering impossible subsumers by a
required literal. Whole-input caching has zero hits within independent proposal
and checking roles on the retained costly trace. The optional index instead
reduces candidate work within each call; it changes no structural coverage or
stored results. All **521 tests** and the Lean audit of **4,219 declarations /
2,031 theorems** pass. Matched costs and adverse controls are retained in the study.

The next iterations prioritize [SAT pattern discovery](research/sat-pattern-discovery.md):
an exact classification covering all valid CNFs, explicit unresolved cases and
checked decomposition across interacting classes. Known-family optimization
continues as supporting work. Coverage and efficient solution of every class
remain separate obligations.

The [first pattern inventory](experiments/results/cnf-pattern-inventory/README.md)
records overlapping classes, explicit parity encodings and exact component/branch
decompositions. On 152 inputs beyond the exhaustive tiny cases, whole-formula
tests explain 39 and two conditioning levels explain 102. The remaining 50 cases
and all failed alternatives are retained. Analysis currently adds runtime and
memory; it identifies discovery gaps rather than accelerating the SAT engine.

The [affine discovery extension](experiments/results/cnf-affine-patterns/README.md)
extracts complete parity encodings, checks their equations and keeps all leftover
couplings. It closes 14 of those 50 cases; the remaining 36 and observed cost
regressions are preserved. Exact composition across small shared interfaces is
the next discovery target. The ordinary SAT solver is unchanged.

The [projection extension](experiments/results/cnf-affine-projection/README.md)
now implements exact interface reduction and checked model lifting. Six growing
coupled affine controls close without branching; the original 36 open sources
still expose gaps in mixed leftovers. Lean composition lemmas, cost regressions
and encoding-budget failures are preserved alongside the gains.

The [checked simplification study](experiments/results/cnf-simplification/README.md)
now exposes structure through unit propagation and whole-residual pure literals.
It closes all 36 old discovery misses; on the expanded corpus, depth-two coverage
rises from 217/329 to 290/329 beyond tiny exhaustive cases. Units alone reach
289/329 at lower runtime. The remaining 38 random 3-CNFs and one boundary-cap
case are retained. Tests, complete archives and cost regressions accompany the
results; this analysis is still separate from the ordinary decision solver.

The [conditioning comparison](experiments/results/cnf-conditioning/README.md)
finds eight additional closures over unit-only frequency ordering at the same
depth and candidate cap. Its shortest-clause policy costs more time and storage,
and loses five cases relative to combined unit/pure processing, so it remains
optional. The next target is duplicated intermediate state: conditioning and
forced-unit closure currently acquire separate full residuals. All fresh
20/32-variable 3-CNFs remain unresolved in this bounded discovery experiment.

The [fused-edge implementation](experiments/results/cnf-fused-conditioning/README.md)
now stores conditioning and its checked simplification together, preserving every
branching plan and coverage result. On the shortest-clause policy, total measured
time falls from 21.17 to 17.64 s and SQLite from 96.91 to 65.57 MB. Targeted Python
allocation also falls; regressions and measurement limits are retained. This
reduces acquisition overhead while leaving the discovery gap unchanged.

The [checked probing experiment](experiments/results/cnf-failed-literal/README.md)
now uses unit-conflict proofs under an assumption to force its opposite. On
1,025 matched inputs, four-candidate probing raises non-tiny structural closure
from 358/513 to 484/513, including 19/64 -> 51/64 on fresh random formulas.
Total time falls from 27.11 to 18.88 s and SQLite from 93.14 to 65.06 MB.
This is standard failed-literal reasoning in the separate discovery layer;
29 cases remain unresolved. Probing every binary variable closes only two more
and costs more. The next target is common consequences already present in both
inconclusive assumption traces, with their reuse and checking charged.

The [common-consequence study](experiments/results/cnf-common-consequence/README.md)
implements that reuse as an optional necessary-assignment policy. On 1,101
inputs it adds one structural closure (536/589 -> 537/589), with no fresh-random
gain, while time rises 32.12 -> 32.76 s and SQLite 104.44 -> 107.76 MB. The
policy stays optional and the regression is preserved. Smaller selected
residuals trigger additional probing and retained state. The next focused
discovery target is checked signed-equivalence substitution on the selected
unresolved paths where existing probe traces already imply such relations.

The [signed-equivalence study](experiments/results/cnf-probe-equivalence/README.md)
now applies those relations throughout the source and checks signed model lifts.
On 1,137 inputs it adds seven old closures (567/625 -> 574/625 non-tiny), with no
gain on 24 fresh random sources. Total time rises 38.29 -> 39.73 s and SQLite
130.60 -> 135.57 MB, so the policy stays optional. The next target is bounded
local learning from checked one-way implications beyond existing binary paths,
present on selected unresolved paths of 37 remaining source misses.

The [bounded-learning study](experiments/results/cnf-probe-learning/README.md)
now turns saved one-way implications into checked binary clauses for one extra
probe pass. It adds three closures (604/661 -> 607/661), including one fresh
48-variable source, but total time rises 48.18 -> 52.70 s and SQLite 163.53 ->
168.27 MB. The policy stays optional. Changed variable choices explain part of
the gains; added propagation matters for the fresh gain. The next supporting
target is reusing the 10,018 continuation certificates that exactly repeat earlier
ones, while keeping new implications, dependencies and unresolved cases explicit.

The [closure-reuse follow-up](experiments/results/cnf-probe-closure-compact/README.md)
now avoids 14,705 repeated propagations by checking added clauses under saved
unit closures. All 1,209 source plans and 13,066 semantic nodes are preserved.
Coverage stays 634/697 non-tiny inputs. A compact policy tag removes the first
trial's storage regression: total time is 62.76 -> 61.69 s, SQLite 197.10 ->
196.10 MB and cold replay 26.78 -> 25.09 s in single samples. The failed trial
and timing limitations remain recorded. All 348 Python tests and the full Lean
audit pass. The unused implication candidates motivate the following selection
experiment, with selection and changed probe choices charged.

The [bounded-selection study](experiments/results/cnf-learning-selection/README.md)
tests four clauses chosen from up to sixteen proved candidates. It gains one
source closure and loses another: coverage stays **662/733** non-tiny inputs and
**16/24** fresh random inputs. Total time rises **71.42 -> 73.19 s (+2.49%)** and
SQLite **227.39 -> 227.83 MB**, so the policy remains experimental. Saved controls
show that a changed first forced variable can redirect later discovery even when
both local probes succeed. The next experiment freezes continuation choices to
separate this effect from clause strength. All **353 tests**, the full Lean audit
and new/previous archive replays pass; all failed attempts remain preserved.

The [fixed-order control](experiments/results/cnf-learning-fixed-order/README.md)
now shows why retaining the old probe choices is insufficient. Coverage remains
**692/769** on the enlarged corpus, with the same gained and lost source. In the
lost case both policies force the same assignment and leave the same 54-clause
original core, but different redundant learned additions lead to different
subsequent discovery. Fixed order costs **80.72 s versus 77.92 s** for baseline;
it remains optional. Next: separate shared residual cores from checked propagation
hints while retaining each plan's hint context. All **358 tests**, the Lean audit
and cold archive checks pass. This does not establish efficient arbitrary-SAT coverage.

The [parent-scoped core experiment](experiments/results/cnf-learning-core/README.md)
now recovers that loss while retaining the earlier gain: **719/805** non-tiny
inputs close, versus **718/805**, with no lost closures. It uses checked hints
at the parent and gives the child only the original-clause core. The full run
costs **97.83 s versus 94.87 s** for baseline; the pilot's savings do not generalize.
It finds **319 clause occurrences** rediscovered in immediate children across
165 edges, making checked hint transport the next reuse target. No new shared
learned-child cores occur within the full run; broad compression is not measured.
All **366 tests**, the expanded Lean audit and new/previous archive checks pass.
Eighty-six sources remain structurally unresolved; arbitrary-SAT bounds stay open.

The [portable-hint follow-up](experiments/results/cnf-hint-transport/README.md)
translates all **1,005 eligible hint occurrences** into proofs checked directly
against child cores. An extra hint pass gains one local closure among 494 edges,
but increases time and memory. The gain occurs outside selected source paths and
comes from probe choices: the child's existing clauses also suffice with those
choices. This motivated ranking the existing continuation on its core without
adding another pass, tested below. Whole-source coverage in that study remains **719/805**. All **374 tests**, the Lean audit
and new cold archive checks pass; parent-independent proofs and failed cost
experiments remain persistent.

The [core-order trial](experiments/results/cnf-core-order/README.md) tests that
ranking change with the existing batch and probe budget. Across 1,389 queries,
non-tiny closure falls **776 -> 775 / 877**, with no gains and a loss on source
956. Time falls **120.82 -> 116.67 s**, but this single sample and coverage loss
do not justify replacing the existing policy. All **380 tests**, the unchanged
Lean audit and new/previous cold archive checks pass. The next discovery target
combines active core candidates with newly ranked variables: this union fits the
four-variable cap in all 255 gained/lost local states, but can exceed it elsewhere.
The failed ranking rule and its counterexamples remain preserved.

The [activity-guided follow-up](experiments/results/cnf-activity/README.md)
preserves **806/913** non-tiny closures and reduces continuation attempts
**31,741 -> 7,184**. Balanced repeated timing controls do **not** establish a
speedup. Source 977's open residual shrinks to 22 literals. Checked signed
subsumption then exposes seven prospective 2-CNF leaves, which could complete
four current source plans after integration. That is the next discovery target;
those closures are not yet counted. All **388 tests**, the Lean audit and new/
previous cold replay checks pass; failed timing claims and witnesses are preserved.

The [signed-subsumption integration](experiments/results/cnf-signed-subsumption/README.md)
now closes those four sources: **833 -> 837 / 949** non-tiny queries in the expanded
study, with no losses. The broad sample becomes slower and larger; the optional
policy is a coverage improvement, not a demonstrated general speedup. All **395
tests** and three new Lean lemmas pass. The [current priorities](research/structural-reuse-priorities.md)
target futile equal-width comparisons (81% of subset tests), reuse of already
proved implications, repeated propagation/checking and retained state. Eight
further residuals expose 2-CNF in a saved diagnostic; three potential source
closures still require integration. **112 sources** remain structurally unresolved.

The [original-implication follow-up](experiments/results/cnf-implied-subsumption/README.md)
closes five additional sources: **864 -> 869 / 985** non-tiny queries, with no losses.
It reuses existing proofs as subset witnesses and skips futile equal-width tests.
Full-sample time stays near **170 seconds**; logical state and the six-case Python
peak grow. All **403 tests** and the Lean audit pass. The current frontier has
**116 open sources** in the enlarged corpus. Repeated restriction/proof checking
remains the main profiled cost; an offline relevance filter removes 75% of saved
implication candidates while retaining the observed exposures, but adds no new
frontier coverage and has not yet been integrated or timed end to end.

The [bounded proof-check cache](experiments/results/cnf-checked-probe-reuse/README.md)
then preserves every result and database byte while reducing full-sample time
**168.31 -> 150.39 seconds** and cold replay **71.60 -> 62.59 seconds**. Repeated
selected controls also improve. The six-case Python peak rises by **1.10 MB**;
the cache is capped at 1 MiB of serialized strings, with other memory charged
separately. All **410 tests** pass. First-time propagation now dominates the
profiled remaining work; structural coverage stays **869/985** non-tiny inputs.

The [ordered propagation study](experiments/results/cnf-ordered-propagation/README.md)
reduces discovery from 111.13 to 97.76 seconds while preserving the exact old
proof traces and all archive bytes. Repeated selected-query controls support
about a 10% total-time reduction. Six-case Python peak rises by 216 KB; early
conflicts can regress because index preparation is wasted. All 417 tests pass.
Coverage stays 869/985 non-tiny: broader discovery remains open, while repeated
restriction and residual reconstruction are now the leading measured cost gaps.

The [immutable source-index study](experiments/results/cnf-indexed-restriction/README.md)
then reuses occurrence lists across restrictions and shares unchanged clause
tuples. Two full runs per mode average **8.36% less discovery time, 4.37% less
total time and 7.30% less cold replay**, with identical proofs and archive bytes.
Six-case Python peak grows **1.60 MB**. The first total-time regression and poor
reuse on newly allocated/edited sources are preserved. All **425 tests** pass;
independent simplification reconstruction is now the leading measured cost gap,
and structural coverage remains unchanged.

The [one-pass checking follow-up](experiments/results/cnf-single-pass-check/README.md)
shares untouched clause tuples while independently reconstructing residuals in
one pass. Full discovery improves **6.60%**, total **5.62%**; cold replay regresses
**1.07%**, and measured peak memory is essentially unchanged. All **433 tests**
pass, with identical archive bytes. The rejected clause-support caches and wide
clause regressions are preserved. A separate checked probe identifies **35 of
148 unresolved leaves** that become Horn after variable polarity changes; integrating
these certificates and measuring root coverage was the next discovery priority.

The [checked Horn-renaming integration](experiments/results/cnf-polarity-horn/README.md)
now closes all 35 saved leaves and **29 additional complete inputs**: non-tiny
structural coverage rises **869/985 -> 898/985**, with no lost closures. None of
the new gains admits a whole-source renaming; exposed residuals compose through
the existing decomposition. Single-run discovery falls **4.95%**, fresh SQLite
**4.63%** and six-case Python peak **15.73%**; warm replay regresses. Earlier
archives remain retained, so this is not a historical-storage reduction. All
**441 tests** and the Lean axiom audit pass. The **87 remaining sources / 106
leaves** now have checked renaming exclusions. Their auxiliary conflict paths
provide the next concrete target for interface and conditioning discovery.

The [obstruction-guided conditioning test](experiments/results/cnf-obstruction-frontier/README.md)
then checks whether those exclusions improve split selection. At the same budgets,
one extra level closes **60/106 frontier leaves** with the current ranking and
**57/106** with the new rule. Its three gains, six losses, higher discovery time
and larger archive are retained; the rule stays optional. Five lost winning
variables lie outside the recorded obstruction. Saved probe proofs expose an
indirect propagation effect in one case, giving a concrete next reuse target.
All **448 tests** pass. Original-source coverage remains **898/985**.

The [saved-probe ordering test](experiments/results/cnf-probe-rank-frontier/README.md)
keeps every baseline candidate and reuses original proofs to change only order.
Coverage is preserved, but two reversed-order runs regress in mean discovery
**4.82%**; the policy is not promoted. The [96 fresh controls](experiments/results/cnf-probe-rank-fresh/README.md)
change no order: **36/39 branching states have no binary clauses**, leaving most
candidates without unit-probe evidence. Bounded multi-variable interactions and
portable successful plans are the next targets. Two Lean lemmas capture the
local coverage condition; all **453 Python tests** pass. Original-source coverage
remains **898/985**.

The [binary-path extension](research/binary-paths.md) removes wide clauses entailed
by retained binary reasons. Full structural coverage becomes **901/985** (four
gains, one bounded-search loss), but discovery rises **19.06%** and fresh archive
size **13.93%**. It remains optional. The lost case exposes the next reuse gap:
a sound reduction displaces an earlier successful split from a capped candidate
list. Both proof archives remain intact. All **461 Python tests** and the Lean
build/axiom audit pass; four new semantic lemmas justify the deletion rule.

The [retained-plan follow-up](research/retained-plans.md) references old closed
graphs before new acquisition. With the same prepared archive, coverage reaches
**902/985** without lost closures, discovery falls **16.65%**, and added storage
falls **37.36%**. Six-case peak Python allocation rises **19.68%**; fresh-input
coverage is unchanged and slightly slower, so the method remains optional.
All **469 tests** and the unchanged Lean audit pass. At that checkpoint, the next measured cost was a
full residual-storage census repeated after every solver query, including hits.

The optional [archive-accounting follow-up](research/residual-accounting.md)
maintains exact totals transactionally. On the same prepared 1,497 inputs, query
time falls **171.12 -> 87.88 seconds (48.64%)**, with identical search, coverage
and stored evidence. Initialization includes one full census; retained overhead
is **4 KiB**. Empty-history acquisition shows no clear improvement. All **476
tests** and the unchanged Lean audit pass. Discovery now accounts for about **92.6%** of query time; selected
proof reuse and transport beyond exact prepared sources are the next targets.

The optional [prepared-probe follow-up](research/prepared-probes.md) reuses
independently checked traces from old unresolved plans. It avoids 21.63% of fresh
probe attempts on the prepared original corpus, but discovery time changes only
**79.80360 -> 78.51427 s** in one ordered comparison. Evidence and storage remain
identical; coverage stays **902/985**. Fresh-input and empty-history controls reuse
no traces, and the fresh control runs slower. All **481 tests** pass. The
[updated priorities](research/structural-reuse-priorities.md) concentrate on the
83 unresolved sources, which consume about 83% of discovery time.


The [independent reconstruction investigation](research/indexed-check.md) found a
limit to source-identity caching: the 96-input control regressed, and a 32-fold
larger cache left hard-case hits unchanged. A no-eviction audit found 2,167 distinct
CNFs among 2,537 source objects, so exact whole-formula sharing has limited headroom
there. Both unsuccessful candidates and their evidence remain optional; the next
target is checked reuse across related residuals. All **490 tests** and the unchanged
Lean audit pass. No new structural coverage is claimed.

The [clause-sharing follow-up](research/clause-mask-reuse.md) finds about 70%
clause reuse in two costly sources, but a bounded checker mask fails to turn it
into a total-cost benefit. Two 96-input controls cut literal work 55.10% while
total time rises 2.58% and 3.58%, and sampled Python peak rises about 41%.
Evidence and storage match exactly. All **496 tests** pass; the prototype stays
optional and disabled. The next priority is checked variable elimination and
equivalent-core discovery on the unresolved frontier.

The [checked variable-elimination extension](research/variable-elimination.md)
now closes **29 of the 83 previously unresolved original inputs**, compared with
11 for pure-only elimination. It broadens coverage at higher total cost:
**64.77 -> 80.10 seconds**, with a larger retained archive. The candidate remains
optional. All **501 tests** pass, and Lean proves the exact existential projection
identity, with implementation refinement still separate. This subset study does
not rerun the full corpus or establish a polynomial arbitrary-SAT solution.

A [checked subsumption follow-up](research/subsumed-elimination.md) passes all
**506 tests** and adds a Lean omission/projection proof, but yields **no further
closures**: the same 29/83 close, with higher time and storage. It remains
optional. The next measured opportunity is less restrictive growth admission:
**48/59** remaining leaves have a candidate with non-growing clause count and at
most eight extra literals, even without subsumption. Candidate availability is
not a new closure or a general SAT bound.

The [clause-count admission experiment](research/clause-bound-elimination.md)
relaxes the per-step literal limit while retaining complete resolvent checking.
All **511 Python tests** and the **4,195-declaration / 2,018-theorem** Lean audit
pass. Lean bounds one accepted elimination chain: at most n steps, mn literals
per formula and (n+1)mn retained formula slots under explicit normalization
and clause-count premises. It does not guarantee an admissible next step or
bound the full discovery graph. The optional policy closes **31/83** original prior misses versus **29/83**,
at higher time and storage cost, and adds no closures on the repeated 96-input
control. The next measured opportunity is a fixed allowance of one or two extra
clauses: 32/57 remaining leaves need one, and 50/57 at most two. These candidate
counts do not establish new closures or an efficient complete elimination order.

The [additive-growth follow-up](research/additive-elimination.md) implements
checked allowances of one and two extra clauses. All **516 tests** and the
**4,216-declaration / 2,028-theorem** Lean audit pass. Lean bounds one normalized
accepted chain by n steps, m+d*n clauses per state and (n+1)*n*(m+d*n) formula
slots, without guaranteeing a useful next pivot or a small full planner. Neither
budget adds a closure on the 57 saved leaves or the 83 original prior misses:
all original modes close the same **31**, while query time and storage increase.
The new endpoint proofs and models are retained, with their additional storage
charged. These policies remain optional. The next focus is useful endpoint
selection and reuse of failed recognition, not larger growth budgets by default.

The latest [arbitrary-CNF research candidate](research/residual-candidate.md)
combines tractable leaves, residual reuse, and recognized matching constraints.
The [matching experiment](experiments/results/cnf-matching/README.md) reduces a
nine-pigeon/eight-hole case from 5,191 acquired residuals to one checked Hall
certificate. This is a restricted-family improvement in a separate Python
prototype; no uniformly polynomial solution for every CNF has been established.

The [positive-core follow-up](experiments/results/cnf-subsumption/README.md)
removes checked redundant positive supersets and reuses the same stored core
across growing sources. Laminar choices reduce to disjoint minimal choices;
irreducible overlap remains open. The source copies and recognition work are
still charged, even when no new core search is needed.

The [delta-history comparison](experiments/results/cnf-positive-history/README.md)
now stores a fixed base once and keeps witnessed positive additions as parent
references and clause deltas. At 16 holes and 128 redundant additions, logical
storage falls from 10,957,771 to 118,668 bytes. Warm append avoids full-source
rediscovery; cold replay, novel constraints and repeated-event losses remain
explicit in the comparison.

The [decision-history extension](experiments/results/cnf-decision-history/README.md)
now reuses an UNSAT base for arbitrary clause additions, or a stored SAT model
when it still satisfies the new clause. Accepted updates avoid subset discovery
and fresh solving. The comparison retains failed-model fallback, repeated-event
losses and cold-replay costs; the rules do not bound general SAT acquisition.

The [repair-history study](experiments/results/cnf-repair-history/README.md)
adds checked single-variable repairs using persistent occurrence and assignment
indexes. A variable can change only when its opposite literal is absent from
the entire parent source. This avoids 128 fresh-base acquisitions on the measured
fresh-unit stream; blocked repairs, index memory and sparse-name costs remain.

The [affected-clause repair study](experiments/results/cnf-affected-history/README.md)
admits safe changes when both signs occur, using versioned clause counts and
occurrence lists. On the measured size-16 matching history it avoids 128 new
acquisitions, reducing operation time from 3.478 to 0.147 seconds and logical
storage from 12.46 MB to 0.158 MB. Eager indexing can increase memory and cold
replay costs.

The [joint-repair study](experiments/results/cnf-equivalence-history/README.md)
recognizes explicit signed-equivalence blocks and checks simultaneous changes
against all affected clauses, including earlier additions. On 32 blocks of 32
variables, acquisition/update time falls from 2.469 to 0.0668 seconds and logical
storage from 3.79 MB to 0.099 MB. Cold final replay is slightly slower. The
[cost map](research/structural-reuse-priorities.md) tracks the next measured gaps.

The [matching-history study](experiments/results/cnf-matching-history/README.md)
now retains matching endpoints and unit constraints, finds alternating changes,
and validates them with the same joint checker. On 32 blocks of eight choices,
operation time falls from 8.303 to 0.253 seconds and logical payload from 20.33 MB
to 0.424 MB. Over-budget recognized repairs, parity moves, mixed-base discovery
and non-unit coupling conflicts remain explicit gaps. These restricted gains do
not give a uniformly polynomial algorithm for arbitrary CNF.

The [budget comparison](experiments/results/cnf-budgeted-history/README.md)
adds an optional bounded retry for recognized equivalence moves. At 1,024
variables it reduces acquisition/update time from 0.785 to 0.059 seconds and
logical storage from 189,168 to 99,129 bytes. Simply raising the global budget
is slightly faster on these chains and handles dense controls that the targeted
cap misses; neither policy is established as optimal. Profiling identifies
repeated full-source unit propagation as the next large preparation cost.

The current draft is **Bounded-Domain SAT, Compiled Knowledge, and Amortized
Reasoning: A perspective on resource accounting for learned reasoning**.

- [LaTeX source](paper/bounded_domain_sat_and_amortized_reasoning.tex)
- Author: Andreas Maier
- Status: working draft
- Format: self-contained LaTeX with embedded bibliography and TikZ figures

The paper distinguishes the costs of construction, storage, inference, training,
verification, and fallback solving. It examines exact finite-domain SAT tables,
finite restrictions of language classes, oracle simulation, explicit ReLU
representations, nonuniform advice, caching, and certified fallback. System 1 and
System 2 serve as a computational analogy, not as complexity classes.

The expanded draft compares these ideas with neural-advice and speedup-learning
literature, discusses the failed Deolalikar argument and Wen's learned-oracle
claims, and proves conditional expected-savings and bounded-overhead results.
An exact reuse identity states when avoiding repeated solves repays cache costs.
These savings conditions apply whether P = NP or P != NP, and a scaling example
shows how reuse can help even when solving has polynomial cost.
The detailed argument audit makes setup costs explicit in every cache bound,
states the finite-expectation assumptions for unbounded query domains, and proves
that uniform computable construction of exact finite tables is equivalent to
decidability. It also explains why optimal metareasoning can remain hard.
The literature comparison attributes the utility criterion to Minton, discusses
self-improving algorithms for polynomial-time tasks, and relates fast/slow
arbitration to Milli et al. and SOFAI. These are established precedents for the
paper's explanatory cost bounds.
The follow-up search adds Goré and Nguyen's published global-caching solver for
an EXPTIME-complete problem and Ferrara et al.'s model-checking preprocessing
work. The finite-table construction criterion is explicitly attributed to
standard computability, and the EXPTIME obstruction to the time hierarchy.
These connections strengthen the perspective without establishing theorem novelty.
An explicit induction now constructs exact answers on successively larger finite
domains. Separate results state the uniform expansion bounds that would imply
polynomial-time decision and the workload conditions that amortize costly
expansion. The correctness induction supplies neither bound by itself and does
not prove P = NP.
The executable development now supplies an exact SAT solver, a counted binary
parser, polynomial bounds for fixed or logarithmically growing variable ranges,
and certified witness reuse. A reference fallback adds lazy search on distinct
occurring variables, sound partial-assignment pruning, and reusable checked
refutation trees. Bounded witness and refutation portfolios survive restarts;
all earlier results remain archived.
The default service now adds shared AIG simplification, a bounded local attempt,
and CaDiCaL's mature CDCL engine. SAT witnesses and LRAT UNSAT proofs must pass
Lean checkers. The formula-to-CNF connection is proved; the external solver's
verdict is never sufficient. Indexed proposals and a long-lived JSON-lines
service reduce retrieval and startup overhead. These modern paths report wall
time and explicitly mark their abstract work counts as unmeasured.
An explicit evaluator machine realizes the reported evaluation count exactly
and has a checked bound on intermediate data size. A converse encoding proof
extends the restricted bounds to every accepted binary request.
The [persistent solver](solver/README.md) retains every completed result across
restarts. The [reproducible studies](experiments/README.md) compare reuse with
lazy solving and checked CDCL, while retaining the earlier exhaustive reference.
They do not establish efficient exact learning on unrestricted instances.

The seven-item follow-up adds compact restricted coverage, a complete assignment
search transition system with payload bounds, live CaDiCaL clause reuse, a bounded
persistent predictor, query deadlines, strict cache checks, and disjoint measured
phases. At that milestone, all 69 tests and the 694-theorem axiom audit pass. The expanded study checks
1,260 answers on public and chronological streams and reports gains, overhead,
and memory costs. [Implementation scope](research/implementation-gaps.md) records
which engineering gaps are addressed and which stronger mathematical claims
remain open. None of these changes establishes unrestricted polynomial SAT.

The structural follow-up targets items 1 and 4. Lean proves exact composition
through a bounded shared interface, so total variables may grow while local
acquisition stays bounded. `--components` implements independent-component reuse
under variable renaming and checked transfer of UNSAT cores to added constraints.
`--incremental` now saves stable circuit definitions and selected learned clauses
across restarts. Shared immutable terms, shapes, maps and prefixes reduce
duplication; full request archival costs remain.

The [structural study](experiments/results/structural/summary.json) checks another
420 answers. One acquired shape serves 127 component occurrences through
expansion to 128 variables. Connected-chain and storage controls show the limits:
that component-only milestone leaves nonempty interfaces for the next extension,
and the whole database can grow despite sharing. Try
`python3 solver/persistent.py --components --incremental serve`.

The five-step extension now adds local bucket elimination, persistent add/replace/
remove snapshots, lazy checked rows, semantic relation storage, and checked
incremental LRAT. Use `--interfaces` for the delta API and `--incremental-proofs`
for the proof-enabled live CDCL path; they can be combined for checked fallback.
The [first interface study](experiments/results/interfaces/README.md) reports 792 correct
answers, local reuse and transport savings, and the overheads of checking,
restart and archival storage. That milestone passed 95 tests and audited 837
theorem declarations. All 2,130 older results and 516 proofs remain unchanged, with 355
newly revalidated results and 129 proofs added. The manuscript now includes the
local elimination and shared-circuit proof arguments, their cost boundaries,
and published BDD representation limits. Small width, affected-state size and
cheap acquisition for unrestricted SAT remain unproved.

The central question is when the expense of acquiring reusable knowledge is repaid
by reduced future computation. Exact representability alone establishes neither
compactness nor efficient learning, and a correct hybrid need not be faster overall.

## Build

Install a LaTeX distribution with `latexmk` and the packages used by the source
(including `newtx`, TikZ, and `natbib`). From the repository root:

```sh
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error bounded_domain_sat_and_amortized_reasoning.tex
```

Alternatively, run `pdflatex` twice:

```sh
cd paper
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
```

The PDF is generated alongside the source. To remove auxiliary build files while
keeping the PDF, run `latexmk -c` from `paper/`.

## Repository layout

```text
paper/
  bounded_domain_sat_and_amortized_reasoning.tex
formal/
  OracleMachines.lean
  OracleMachines/
  lean-toolchain
  lakefile.toml
  lake-manifest.json
  README.md
solver/
  persistent.py
  test_persistent.py
  README.md
experiments/
  run_workloads.py
  results/
research/
README.md
LICENSE
```

## Lean verification

The [Lean project](formal/README.md) checks the expansion invariant, explicit
table size, conditional polynomial cost bound, staged savings criterion, and
amortization limits. It also proves that the explicit table and exponential
expansion costs are not polynomially bounded. A theorem map identifies the exact
coverage and remaining obligations.

With Lean's version manager installed, run:

```sh
cd formal
lake exe cache get
lake build
```

The toolchain and dependencies are pinned. The default build audits all declarations in the formal library
namespace for admitted proofs and additional axioms. The formalization treats
general runtime costs as explicit numerical ledgers and connects a concrete
SAT parser and core to an operational cost model. It proves polynomial bounds
for a **fixed** variable cap and for variable width at most `floor(log2(L+1))`,
where `L` is the encoded length. These restrictions do not give a bound for all
SAT inputs or a formalization of P versus NP.
The evaluator's transition and data-size proofs are a component of a runtime
argument for complete-witness evaluation; combined machine simulations for
parsing, partial evaluation, and full search remain open. The lazy search has a
checked bound of `2^(d+1)-1` nodes for `d` distinct occurring variables. Refutation
size can still be exponential.

## Persistent solver

Build the executable with `./solver/build.sh`. Then, from
the repository root, run `python3 solver/persistent.py solve 010`. Subsequent
calls reuse the result from `solver/.cache/results.sqlite3`; new formulas can
also reuse retained witnesses and refutation certificates after checking them. SAT and UNSAT
results accumulate without eviction. The [service documentation](solver/README.md)
covers encoding, storage, restart behavior, integrity checks, and testing.
The database is local and ignored by Git; source code and reproducible experiment
results are versioned.
Use `python3 solver/persistent.py serve` for multiple JSON-lines queries in one
process. The default `auto` backend combines local checks with certified CDCL;
`--backend lean` retains the original counted lazy solver.

## Literature review

The [annotated literature review](research/literature-review-2026-11-07.md) compares
the draft with work on neural advice, speedup learning, compilation, and failed
complexity proofs, including Deolalikar and Wen. It includes
[supplementary BibTeX](research/related-work.bib) and saved OpenAlex/SemOpenAlex
query evidence. The closest precedents and relevant historical cautions are now
integrated into the manuscript's self-contained bibliography.

The review also contains a [detailed proof audit](research/literature-review-2026-11-07.md#detailed-argument-audit-and-scope-beyond-np)
covering every formal argument, the repaired accounting omission, and the limits
of extending the result beyond NP.
The [publication-status reassessment](research/literature-review-2026-11-07.md#publication-status-of-the-generalized-observations)
maps the generalized claims to prior work and distinguishes checked publications,
an MSc thesis, and sources whose full text could not be verified.
The [induction audit](research/literature-review-2026-11-07.md#inductive-expansion-proof-and-limitations)
checks the expanding-domain proof, its cost conditions, and counterexamples to
an unconditional polynomial-time conclusion.

## License

This repository includes an [MIT license](LICENSE).


## Scaling follow-up

The solver now supports affected-bucket updates, direct bounded BDD operations,
live graph/proof reuse, checked negative-core transfer, logical archive caps and
measured full-query route selection. All historical results remain persistent.
The [scaling study](experiments/results/scaling/README.md) records 1,470 correct
answers, including 672 UNSAT, across 147 runs. The earlier milestone passed 106 tests and
audited 879 theorem declarations. The [formal notes](formal/README.md) state
conditional resource bounds and the remaining refinement obligations.

Reuse reduces selected acquisition/planning costs, but checked solving remains
faster on several measured streams. Direct symbolic compression does not give a
polynomial bound on arbitrary intermediate diagrams. Logical database limits do
not bound whole-process memory; capacity exhaustion preserves history and stops
acquisition. The unrestricted polynomial SAT argument remains open.


## Durable reuse and balanced-chain follow-up

The latest implementation adds durable batches, persistent bucket maps, balanced
chain summaries, fused symbolic projection, individually checked proof fragments,
and structural routing with reserved fallback time. **114 tests pass**; Lean
checks **941 theorem declarations**. The explicit chain API uses ten compositions
and eleven node writes for a replacement at 1,024 edges. Whole witnesses and
service costs are accounted separately.

The [new study](experiments/results/followup/README.md) records 2,259 correct
answers and 30 archive-cap errors across 210 runs, including selected TACAS 2026
artifact inputs and a held-out counter. It preserves failures, resource samples,
and every older dataset. The live archive retains all historical rows and now
contains 3,550 results and 1,032 proofs. The [gap register](research/implementation-gaps.md)
and revised manuscript distinguish these implementation results from the open
unrestricted width, representation, acquisition and full-machine obligations.

## Bounded layers and comparable inputs

The latest [study](experiments/results/structured/README.md) adds checked Boolean
layers of width 1–4, persistent source/order indexes, payload-limited active
caches, WAL checkpoint controls, and failure-aware route scores. The layer
replacement theorem exposes exponential width dependence and logarithmic depth;
full witnesses and service overhead remain separate. Native materialization was
also repaired after inspecting generated C.

All **119 tests pass**, and Lean audits **991 theorem declarations**. A new
175-run comparison completes 2,450 queries correctly, with enabled learning,
three additional artifact families and identical full-formula service inputs.
Learning helps the signed-unit stream but does not improve the public-only
streams. A separate cache-pressure study retains every historical state while
measuring the cost of smaller active retention. All older datasets and archive
rows remain unchanged; the live store now holds 3,905 results and 1,161 proofs.
The [gap register](research/implementation-gaps.md) records what remains open.

## Seven-priority follow-up

The current implementation separates semantic row reuse from current provenance,
uses iterative lazy evaluation, retains complete native layered working sets,
and records final route outcomes once. Speculative witness/proof checking now
has a separate budget and measured outcomes. A new `layered_cnf` API checks and
compiles CNF under a supplied adjacent-block partition; it does not discover a
bounded-width decomposition for unrestricted SAT.

**129 tests pass**, and Lean audits **1,047 theorem declarations**. The new
costed reference returns operation counts and is proved equivalent to tree
replacement. Additional proofs cover relation comparison, full witness traces,
prefix/suffix composition and mathematical source binding. Whole-service cost
and protocol refinement remain open. The [priority gap register](research/implementation-gaps.md#seven-priority-implementation-follow-up)
distinguishes implemented improvements from those remaining obligations.

The [new evaluation](experiments/results/priorities/README.md) adds unused public
members, larger mixed-label application sources, a no-training polarity baseline,
matched live/restarted proof modes and distinct-relation pressure. Its
[development pilot](experiments/results/priorities-pilot/README.md) is preserved.
Every previous database row and all 93 historical experiment files remain intact.
The live solver contains **4,260 results / 1,290 proofs**, plus saved expansion
branches and source bindings checked again after restart.

## Incremental CNF source versions

`source_cnf` preserves the actual clauses in a balanced tree alongside their
checked relations. A local edit replaces an edge's entire clause bucket; an
empty bucket deletes its clauses. The supplied disjoint ordered variable
partition stays fixed, with a supplied width from one to four and at most that
many variables per block. Every clause must
fit in one block or two neighboring blocks. There is no decomposition discovery
or unrestricted-SAT width guarantee.

```python
from solver.persistent import PersistentSolver

with PersistentSolver() as solver:
    first = solver.source_cnf(1, [[1, 2], [-1, -2]], [[1], [2], [3]])
    contradiction = solver.source_cnf(base=first['state'], replace={0: [[1], [-1]]})
    deleted = solver.source_cnf(base=contradiction['state'], replace={0: []})
    assert first['answer'] and not contradiction['answer'] and deleted['answer']
```

Use `op: "source_cnf"` with the same fields in the JSON-lines service. Queries
are decision-only by default; `witness=True` requests the complete block-state
path and adds its output/checking cost. Versions remain in the SQLite archive
and are replayed and checked after restart. After a checker upgrade, the saved
clauses and summaries are checked by the new engine before a current result is
stored; old answer bits are ignored and every old row remains intact. The result
reports `revalidated_source=True` on first use from an older namespace. A
different partition starts a new source family and pays initial compilation.

The native decision carries a Lean proof connecting its cached summary to the
original clauses retained in its indexed source tree. Local patch checks reject changes to unedited
subtrees. Incremental reference tracking removes the former full-closure scan
under layered cache pressure. At a tight cap, a single height-h source edit
temporarily reserves up to h+1 additional relation nodes until its transition
is checked, then evicts obsolete nodes. Archive history, metadata, source
payloads and process memory have separate costs.

The reference update bound is proved. Original-variable translation and complete
CNF grouping and complete initial binding now have the proofs described below;
mutable node/patch identities, JSON, persistent maps, Python/SQLite and machine
costs still have refinement obligations.
General factor-DAG provenance, adaptive gating and unrestricted structural
coverage are unchanged. At this milestone **141 tests passed**, and Lean audited
**2,279 declarations / 1,106 theorem declarations**. See the
[source-update study](experiments/results/source-updates/README.md) for matched
full-source rebuilding, lifecycle costs, replay, stored bytes and sampled RSS.

The follow-up uses an indexed assumption check for general-factor negative
proofs. Lean proves equality with the previous membership condition, including
duplicates; counters report index entries and membership probes. It avoids
repeated list scans while retaining the full evidence traversal. Initialization
failures now close their database handles, and the two test-owned connection
leaks are fixed. At that checkpoint **144 tests passed without resource warnings**,
and Lean audited **2,290 declarations / 1,113 theorem declarations**.

That checkpoint's live archive held **4,970 results / 1,548 refutations**, with all older
rows preserved. The [context and upgrade report](experiments/results/context-index/README.md)
records the diagnostics and checked source adoption. To revalidate the earlier
source-study records after updating the solver, use:

```sh
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```

This checks historical source fingerprints and recorded evidence; it reports the
current binary separately and does not claim to rerun the historical executable.

The mapping checkpoint proves the conversion from original variable IDs to bounded
block states. Native positions carry array-lookup and width proofs; an alignment
pass establishes completeness. Both compilation paths now use checked local
translations. Lean proves that each translated CNF bucket is satisfiable exactly
when its boundary relation has an accepting pair. The proof includes short and
empty blocks and unused variables. The following checkpoint proves global clause
grouping; the connection through native node identities remains separate.

At that milestone **148 tests passed**, including exhaustive checks of 9,520 boundary
assignments across 112 local CNFs through both native compiler paths. Lean audited
**2,477 declarations / 1,188 theorem declarations**. Alignment and source
equality checks add passes and temporary arrays; these costs are outside the
existing relation-evaluation counter. This checkpoint makes no new speed claim.

The [mapping verification record](experiments/results/source-mapping/README.md)
preserves build/test logs, fingerprints and archive revalidation. That archive
held **5,325 results / 1,677 refutations**. Every old row in all 21 tables and
all 142 earlier experiment files remained intact. The five saved source versions
were rechecked under the new engine and after restart. The
[persistent gap analysis](research/implementation-gaps.md) records the next proof,
accounting and evaluation obligations.

The grouping checkpoint connects the **complete original CNF** to its grouped
relations. The compiler carries a permutation proof preserving every clause
occurrence, including duplicates and empty clauses, together with the local
semantic equalities. Lean proves SAT/UNSAT equivalence with a consistent path
through all buckets. Individually nonempty relations need not share such a path.
A tree-summary theorem follows when exact leaf binding and identity padding are
supplied. The following checkpoint supplies this premise for complete-source
checks; preservation through native patches and replay is still open, as are
reference-count and general row/equivalence-store invariants.

At that milestone **152 tests passed**, and Lean audited **2,562 declarations / 1,233 theorem declarations**
without admits or added axioms. The new global checks cover 11,680 complete
assignments across 60 CNFs, exact clause multiplicities, service witnesses,
incompatible shared boundaries, 65,537 blocks and 12,000 repeated clauses. The
[grouping verification record](experiments/results/source-grouping/README.md)
preserves the evidence. All historical rows and all 150 prior experiment files
remained intact. That archive held **5,680 results / 1,806 refutations** after
checked revalidation. Added grouping/equality work is explicitly outside the
relation-evaluation ledger. No new timing or unrestricted-SAT claim is made.

The binding checkpoint proves **executable complete-source binding** against the
actual stored tree. `SourceBinding.lean` checks every ordered leaf and individual
identity-padding relation, then returns a proof that its decision agrees with
the original CNF. Both native full-source queries and initial source-version
binding use this result. Original-clause/provenance checks remain in place.

The scan has a proved count of one relation comparison per logical leaf. New
metrics expose that count and diagnostic cell/source-evaluation bounds. Shared
nodes still incur work for each logical occurrence. Initial source-version binding
adds a source-evaluation pass; warm queries and local edits do not repeat it.
Allocation, bit costs, transport and storage still need separate accounting.

At that milestone **156 tests passed** and Lean audited **2,615 declarations / 1,259 theorem declarations**
without admits or added axioms. New tests cover incorrect binding despite a
matching final answer, nonidentity padding that composes to identity, dimensions,
counts and 65,536 logical leaves sharing 17 native nodes. The
[binding verification record](experiments/results/source-binding/README.md)
preserves the evidence. All old rows in 21 tables and all 158 earlier experiment
files remained intact. That archive held **6,035 results / 1,935 refutations**;
all 355 distinct generic inputs and five old source versions pass revalidation.
Native identity/patch/replay invariants and complete resource bounds remain open.
The historical timing study is unchanged; this proof adds no new speed claim.

The preceding checkpoint retains **original-source meaning through native joins**.
`SourceNodes.lean` indexes source nodes by their exact layout, width, start and
height. Logical leaves keep original clauses and translation proofs; joins require
consecutive intervals and preserve all clause occurrences. The cached decision
now has SAT/UNSAT equivalence theorems for those original clauses. Native
registration and replay use these constructors; warm decisions read the summary
without flattening or traversing the source.

New metrics count registered original-source nodes, clause entries and literal
entries, including replay. The retained original integer arrays have additional
storage cost alongside JSON evidence and local translations. These counters are
diagnostic entries, not bytes or RSS. No new timing or memory-reduction claim is made.

**159 tests pass**, and Lean audits **2,751 declarations / 1,320 theorem declarations**
without admits or added axioms. Regressions cover invalid joins/layouts, failed
batches, duplicate registration, shared-variable conflicts, sparse IDs, empty
blocks, payload counters and restart. The
[source-node verification record](experiments/results/source-nodes/README.md)
preserves the evidence. Every old row in 21 tables and all 166 earlier experiment
files remain intact. The archive now holds **6,390 results / 2,064 refutations**.
Its named-store obligation is partly closed by the following checkpoint.

The preceding checkpoint proves **paired native-map and decoded-metadata
correspondence**. `SourceStore.lean` couples each named relation tree to its exact
original-source model and retains matching identity, layout, width, start, height
and original leaf clauses. Initialization, insertion and erasure preserve the
invariant without a store scan. Lookup theorems connect the retrieved tree's
decision to its original clauses. Runtime parsing, comparisons and temporary
headers remain costs; proof fields erase.

**162 tests pass**, including 23 source-update tests. Lean audits **2,858
declarations / 1,367 theorem declarations** without admits or added axioms.
New regressions cover deletion-batch rollback, shared descendants, safe identifier
reuse, distinct provenance with equal relations and missing-field rollback.
The [source-store verification record](experiments/results/source-store/README.md)
preserves the evidence. All 355 older generic inputs and five saved source
versions pass current-engine revalidation. Every old row in 21 tables and all
174 earlier experiment files remain intact. The archive holds **6,745 results /
2,193 refutations**.

The preceding checkpoint proves **named child registration and serialized-summary
binding**. `SourceLinks.readJoin` connects decoded child names to the exact models
retrieved at registration, then proves original-clause composition and the need
for one valuation satisfying both sources. Conditional lemmas preserve links
under fresh insertion and deletion avoiding both children. The paired native
store also retains exact equality between each decoded mask's relation and its
model's cached summary.

**165 tests pass**, including 26 source-update tests. Lean audits **2,874
declarations / 1,380 theorem declarations** without admits or added axioms.
The [source-link verification record](experiments/results/source-links/README.md)
records malformed child/mask checks, distinct provenance under equal relations,
and shared-child retention across shuffled parent deletions. All 355 generic
inputs and five saved source versions pass revalidation. Every old row in 21
tables and all 182 earlier experiment files remain intact. The archive holds
**7,100 results / 2,322 refutations**.

The preceding checkpoint proves **native source dependency lifetime**.
`ReferenceCounts.lean` relates incoming counts to the exact number of decoded
child occurrences across live parents. `SourceLifetime.lean` uses count zero to
prove safe deletion and preserves each surviving branch's exact named children.
The executed source context carries these invariants through fresh insertion and
deletion; duplicate definitions change no state. The aggregate sum and finite
parent-domain witness exist only in proofs. Updates still touch at most two
direct child counts, without scanning the store.

**166 tests pass**, including 27 source-update tests. Lean audits **2,944
declarations / 1,416 theorem declarations** without admits or added axioms.
An independent full-graph recount checks eviction decisions for 44 nodes with
16 roots, shared descendants, duplicate registrations and randomized deletion,
followed by complete reclamation and reuse of the same names. The
[lifetime verification record](experiments/results/source-lifetime/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every previous row in 21 tables and all 190 earlier experiment files remain
intact. The archive holds **7,455 results / 2,451 refutations**.

Next is exact requested-patch semantics. Python retention, the generic relation
store, complete persistence refinement, acceptance completeness and full resource
costs remain separate obligations. No new timing or unrestricted-SAT guarantee
is claimed.


The preceding checkpoint proves **exact native source-patch semantics**.
`SourcePatch.lean` connects decoded request fields and current live root/child
lookups to the original arrays: every requested bucket gets its supplied clauses,
and every unedited bucket stays unchanged. Equal relations cannot substitute for
exact original arrays. The executed checker carries this certificate and keeps
its path-visit counter; the proofs add no full-source scan or relation join.

**169 tests pass**, including **30 source-update tests**. Lean audits **3,043
declarations / 1,461 theorem declarations**, with no admits or added axioms.
New checks cover split-path edits with padding, order and duplicate original
clauses under equal relations, invalid requests/roots/partitions, unchanged
aliases, and the complete 4,096-entry decoding cap. Runtime checkpoint `32b4748`
is committed and pushed. The [patch verification record](experiments/results/source-patches/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every old row in 21 tables and all 198 earlier experiment files remains intact.
The archive now holds **7,810 results / 2,580 refutations / 50 source-state rows**.

Next is composing initial raw-CNF binding, complete root coverage, the
bucket-to-flattened-CNF transition and the returned verdict/witness into one
successful-request theorem. Python retention, complete replay/SQLite refinement,
generic relation/factor stores, acceptance completeness and total resource costs
remain open. The updated checker pays for direct lookups, decoding, edit-list
filtering and array comparisons. Earlier timings are unchanged; no speedup or
unrestricted-SAT guarantee follows.


The preceding checkpoint proves **complete successor formulas and returned native
decisions**. `SourceFormula.lean` connects ordered bucket flattening to the exact
original clause list, characterizes interval coverage and empty padding, and
proves that an accepted patch gives the complete requested successor CNF.
`SourceVerdict.lean` certifies root coverage and the actual returned answer field.
The exposed query/patch functions have success theorems, including the nested
patch verdict, with both SAT and UNSAT equivalences for the original formula.

**171 tests pass**, including **32 source-update tests**. Lean audits **3,107
declarations / 1,506 theorem declarations**, with no admits or added axioms.
New tests reject incomplete, shifted and oversized roots and check actual verdicts
against exhaustive truth tables over 54 transitions with 1, 3 and 5 logical edges.
They include padding, old branches, deletion, repeated and empty clauses, and both
answer modes. Runtime checkpoint `9673dee` is committed and pushed. The
[verdict verification record](experiments/results/source-verdicts/README.md)
includes revalidation of 355 generic inputs and five saved source versions.
Every old row in 21 tables and all 206 earlier experiment files remains intact.
The archive holds **8,165 results / 2,709 refutations / 55 source-state rows**.

Next is the complete initial raw-CNF anchor and composition over accepted
operation histories. Serialized witness contents, byte transport, Python
retention and complete replay/SQLite refinement also remain open. Flattening is
specification work; warm decisions add no full-source scan or summary rebuild.
Total physical/resource costs and unrestricted coverage are not established.
Earlier timing evidence remains unchanged.


The latest checkpoint closes the **initial raw-CNF binding** gap.
`SourceInitial.lean` connects the actual request getters to the live root's exact
original buckets, complete coverage, clause permutation and returned verdict.
Grouping may reorder clauses globally; duplicate and empty clause occurrences
remain intact. `SourceUpdates.bindSource_success` covers the native JSON-returning
function. The executed original-bucket scan proves `visits + 1 = 2^(height + 1)`
and `height < 17`; this counts logical visits, not total machine work. Initial
compilation and both complete binding scans remain charged. Warm paths are unchanged.

**174 tests pass**, including **35 source-update tests**. Lean audits **3,154
declarations / 1,539 theorem declarations**, without admits or added axioms.
Runtime checkpoint `92a1ddd` is committed and pushed. The
[initial-binding verification record](experiments/results/source-initial/README.md)
records all 355 generic inputs revalidated, five source versions adopted and
restarted, every old row in 21 tables preserved, and all 214 earlier experiment
files unchanged. The archive holds **8,520 results / 2,838 refutations / 60
source-state rows**.

Next is composition over accepted operation histories. Serialized witness values,
byte transport, Python active-root retention, replay/SQLite refinement, generic
stores, acceptance completeness and complete resource bounds remain open. Earlier
timings are unchanged; no new unrestricted-SAT guarantee follows.

## Certified affine growth

The affine path adds fresh variable blocks while retaining an exact summary of
all preceding parity equations. Its summary has at most `b+1` equations over a
width-`b` boundary, or `(b+1)^2` coefficient/right-hand-side cells. One resident
append with `c` new equations has reference charge `O(b^3 + b^2*c)`. The native
solver executes the Lean-certified coefficient operations; it does not enumerate
boundary assignments. This is a restricted affine result using established
Gaussian elimination, with explicit construction and replay costs.

Original batches, immutable versions and results persist in SQLite. Restart
replays original equations, and adding a contradictory batch never changes a
saved parent's answer. The interface is decision-only, with an optional boundary
summary; it does not return a full-history witness. Width, batch and resident
version caps are explicit refusals. General CNF, arbitrary older-variable edits,
complete persistence refinement and total machine-cost bounds remain open.

See the [API and limits](solver/README.md#affine-growth),
[formal contracts](formal/README.md#affine-growth), and
[archived validation](experiments/results/affine-growth/README.md).
The checkpoint passes **184 tests** and the Lean audit of **3,485 declarations /
1,708 theorem declarations**. It retains all prior results and 268 affine versions.

The next checkpoint (`88f26a8`) composes the native source-CNF response contracts
across arbitrary finite request histories, including rejected batches and layout
resets. Earlier observations keep their event-specific source meaning; reused
names are not assumed to denote the same formula after deletion/reset.

Affine native histories now use erased proof data, so resident children do not
keep runtime ancestor states reachable. The service bounds resident versions independently
of archive length and replays old branches with eviction. A 4,101-append test grows
and restarts with only two resident versions. All **190 tests pass**; Lean audits
**3,625 declarations / 1,766 theorem declarations**. Complete Python/SQLite
refinement, broader decompositions and total machine costs remain open.
See the [history and retention record](experiments/results/history-retention/README.md).

Checkpoint `1037595` connects affine decoded Boolean inputs and named-store
histories to the original-equation invariant. **192 tests** and the Lean audit
of **3,794 declarations / 1,836 theorem declarations** pass. Expansion work is now
prioritized around compression and reuse: the repeated affine streams contain
14 identical algebraic calls among 18 distinct history expansions. This motivates
an exact transition cache, implemented in the next checkpoint below. See the
[current gap record](research/implementation-gaps.md) and
[pattern evidence](experiments/results/affine-history/README.md).

Checkpoint `f80f678` implements exact certified transition reuse. A cache hit
checks the full boundary summary and equation batch, reuses the algebraic result,
and attaches it to the new version's own history. Hash collisions cannot authorize
reuse. The cache is configurable, bounded by slots, and disabled with
`affine_kernel_slots=0`.

In five matched repetitions, repeated width-16 streams fall from **167.57 to
144.21 ms** and repeated width-32 streams from **496.37 to 215.54 ms** (2.30x).
Novel streams have no hits and roughly unchanged timings with slight median
overhead. These are synthetic affine results, without a general SAT speed claim.
All **197 tests** and the Lean audit of **3,938 declarations / 1,875 theorem
declarations** pass; all 405 older experiment files and old archive rows remain.
See the [cache experiment and limits](experiments/results/affine-kernel-cache/README.md).


## Shared affine batches and certified preparation

Checkpoint `e0cb8d3` adds duplicate-free computation and adaptive original-batch
sharing. Prepared typed rows and normalized transitions can be reused across
histories with different duplicate counts. The source archive retains exact row
order/multiplicity and legacy version identities; existing rows are unchanged.

In five matched repetitions, width-32 changing-multiplicity streams fall from
**1,246.55 to 430.52 ms** with both options. Repeated width-32 source payload falls
**16,656 -> 6,499 bytes**, and database size falls by **12 KiB**. That storage gain
costs **6.6%** more elapsed time on the exact repeated stream. Novel streams gain
no reuse. Native request JSON is still per version, so these measurements do not
establish a reduction in process memory. Each cache has its own slot occupancy;
byte budgets and batch handles remain open.

All **207 tests** pass; Lean audits **4,043 declarations / 1,911 theorem
declarations**. Every old archive row and all 583 earlier experiment files remain.
See the [four-mode evidence and remaining limits](experiments/results/affine-batch-reuse/README.md)
and [current expansion priorities](research/implementation-gaps.md).


The [current resource-bounds audit](research/resource-bounds.md) separates general
SAT, finite coverage, factor/layered expansion, affine hits/misses, cold replay,
live memory and archive growth. It records exact formal bounds, derived payload
accounts, configured refusals, measured phase costs and the remaining proof gaps.

The [resident-width follow-up](experiments/results/affine-resident-metadata/README.md)
removes a redundant parent decode: shared warm appends use seven instead of nine
object reads. All 210 tests pass; the native proof code and earlier archive remain
unchanged. The [KD-tree assessment](research/indexed-reuse.md) distinguishes exact
lookup from candidate search for a future checked repair path.

[Uniformly cheap expansion](research/expansion-preconditions.md) makes the next
target explicit: maintain a closed structural invariant that enables cheap
construction even for unseen updates. A diagnostic finds point boundaries in
all regular steps of the existing repeated/novel affine streams. Conditional
semantic lemmas are Lean-checked; specialized native recognition and construction
remain to be implemented and measured against richer boundary families.

The [arbitrary-SAT expansion analysis](research/arbitrary-sat-expansion.md)
refocuses the next milestone on interacting tractable classes: checked class
leaves, heterogeneous backdoors, recursive component splitting and persistent
residual reuse. It records the literature, an explicit obstruction to independent
class solving, and the discovery/recombination costs that remain unresolved.
