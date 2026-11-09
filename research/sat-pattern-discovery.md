# Discovery and exact coverage of arbitrary CNF

Direction set by the user on 8 November 2026: prioritize discovering SAT patterns
and a valid partition covering the entire problem. Continue improving known
families as supporting work. This is a research plan, not an achieved efficient
partition or a new tractability theorem.

## What a valid partition must mean

The universe is all valid finite CNF encodings, including satisfiable and
unsatisfiable formulas. Invalid encodings are reported separately. Keep two
objects distinct: classification of whole formulas and decomposition of the
assignments/constraints of one formula. Splitting clauses into easy families
does not make their conjunction easy; shared-variable compatibility must remain
in the representation and cost account.

For whole-input classification, retain a versioned vector of deterministic
recognition outcomes rather than hiding overlapping patterns behind the first
successful recognizer. With outcomes in {recognized, excluded, unresolved},
the sets of inputs producing each outcome vector form disjoint cells covering
the universe. Empty cells can be omitted. "Excluded" requires a complete test
or a checked exclusion argument for the stated property; a budget stop or a
failed sufficient recognizer is "unresolved". Recognition-policy version,
deterministic work budget and any fixed seed or archive snapshot belong to the
cell definition. Wall-clock timing measures cost, not reproducible membership.
Cells describe recognition outcomes,
not necessarily the formula's full semantic class membership.

This supplies a bookkeeping partition immediately, but is not the research
achievement. The objective is to explain and progressively split its unresolved
cells using useful structural invariants and checked transformations. Reporting
only "known family versus everything else" does not meet the next milestone.
Overlapping class certificates remain available for alternative solver choices;
a routing priority must not erase them. Recognizers must terminate with an
explicit outcome, including when their search budget expires.

For decomposition within one formula, record exact source-linked residuals:

- Conditioning on x=false and x=true partitions assignments and combines by OR.
  UNSAT needs both branches unless another checked refutation already applies.
- Components on disjoint remaining variables combine by AND. Shared variables
  require an exact interface relation or conditioning before independent solving.
- A recognized residual can retain a family certificate and reuse operation.
  Unresolved residuals remain explicit and use the complete checked fallback.

These rules give semantic coverage, with no promise of a small decomposition.
The supplied strong-backdoor, scattered-class and component-depth literature in
[the existing analysis](arbitrary-sat-expansion.md) is the starting point. Read
primary sources before extending their results; retain their hypotheses.

## First milestone: an audited pattern inventory

**Implemented checkpoint:** the [664-input study](../experiments/results/cnf-pattern-inventory/README.md)
now records seven overlapping pattern outcomes, source bindings, independently
checked component partitions and bounded conditioning alternatives. It recognizes
the full direct encoding of one parity equation within a width cap. Two levels
explain 102/152 non-exhaustive inputs; 50 remain unresolved. Analysis adds time
and space and is not enabled as a solver optimization. The 24 observed root cells
are not a complete enumeration of all possible signatures. The next experiment
refines connected unresolved cells by exact clause support/sign patterns.

**Follow-up implemented:** [explicit affine extraction](../experiments/results/cnf-affine-patterns/README.md)
groups complete parity halves by support, retains every leftover clause, and
checks triangular GF(2) row operations. It recognizes direct overlapping affine
systems and inconsistent affine subsystems with couplings. New outcomes have
versioned identities; the previous inventory and archives remain valid. At depth
two, original non-tiny closure rises from 102/152 to 116/152. All eight seeded
gains come from unit/binary contradictions exposed by conditioning. Pure growing
affine cases close, but adding one binary coupling clause keeps four growing
controls unresolved. Their two-variable interfaces are the next target for
exact projection and composition, with checked witness lifting. General hidden
affine recognition and efficient arbitrary-CNF decomposition remain open.

**Exact projection implemented:** the [775-input study](../experiments/results/cnf-affine-projection/README.md)
eliminates only affine variables absent from leftovers, checks the resulting
boundary relation, and lifts reduced models. Direct boundary CNF encoding is
budgeted before enumeration; a miss preserves the original planner. All six
growing coupled controls now close without conditioning, but the original 36
open sources remain open at depth two. The matching/parity remainder still mixes
an easy matching component with one bridge clause. Its positive-only bridge
variable identifies the next discovery target: checked leftover simplification
and interface-aware conditioning, tested against constrained and random cases.
Lean now proves composition with an arbitrary leftover predicate invariant on
eliminated variables; the Python pipeline remains outside that refinement.

**Checked simplification implemented:** the [841-source study](../experiments/results/cnf-simplification/README.md)
reuses unit propagation and checks whole-residual pure elimination, exact child
bindings and model lifts. The matching/parity remainder now exposes matching
without conditioning. Combined depth-two coverage rises from 217/329 to 290/329
beyond the exhaustive tiny sources, closing all 36 old misses. Units alone reach
289/329 and are faster; most gains are standard propagation, not new families.
Harder controls retain 38 of 48 new random 3-CNFs unresolved, plus one renamed
wide-boundary case. These are the next discovery targets. The random group costs
3.26 of 4.62 seconds of combined discovery. Profile its failed alternatives and
test structure-aware conditioning under matched work budgets before adding more
families or depth. Preserve the unit-only comparator and all regressions.

**Conditioning investigation completed:** the [949-source comparison](../experiments/results/cnf-conditioning/README.md)
tests a frozen MOMS-inspired ordering at the same depth and candidate cap. It
improves unit-only coverage from 322/437 to 330/437, with two gains on 72 fresh
formulae. On gains with an OR root, the winning root variable was already tried
by the old policy; subsequent short-clause choices expose the new closure.
The policy creates more distinct intermediate residuals despite trying fewer
candidates, increasing time and storage. Combined unit/pure processing retains
five closures it misses. All new 20/32-variable 3-CNFs remain unresolved under
every measured policy. The next experiment is a checked conditioning-plus-unit
edge that avoids duplicated intermediate acquisition while retaining source
dependencies, failed alternatives and cold verification. This supports further
discovery; it does not resolve the remaining interaction or depth obligation.

**Checked edge fusion implemented:** the [same 949-source corpus](../experiments/results/cnf-fused-conditioning/README.md)
now contracts conditioning followed by simplification into one source-bound edge.
All choices, terminal/component behavior and coverage results are unchanged;
full comparison checks all 3,999 archived OR plans across three policy pairs.
Shortest-clause SQLite falls from 96.911 to 65.573 MB and total time from 21.170
to 17.638 s. No new closure follows. The remaining payload is dominated by
unresolved CNFs and OR alternatives. Next test bounded unit-conflict probing on
binary-rich conditioned residuals, deriving forced values only from checked
refutations of the opposite assumption. Keep probe work, failed probes and
unresolved cases explicit; a fixed discovery budget need not cover arbitrary SAT.

**Checked failed literals implemented:** the [1,025-input study](../experiments/results/cnf-failed-literal/README.md)
preserves the 949 old sources and adds 64 fresh random formulas plus 12 controls.
The optional four-variable probe policy raises non-tiny closure 358/513 ->
484/513, and fresh random closure 19/64 -> 51/64. SAT and UNSAT gains are both
present. Reasons independently justify each forced value; inconclusive probes
are retained, and units/components/recognized families keep their priority.
Total time and storage fall, but 29 inputs remain open and some become slower.
Full binary-variable probing on these misses closes only two more at higher
cost. Existing inconclusive traces already contain common consequences under
both assumptions in 245 archived nodes (179 unresolved). Using these consequences
is the next exact-discovery experiment; it has not yet added root coverage.
Keep arbitrary split depth separate from per-residual probes and forced chains.

**Checked common consequences implemented:** the [1,101-input comparison](../experiments/results/cnf-common-consequence/README.md)
applies the necessary assignments from the first complete probe pair with a
nonempty unit intersection, after the unchanged failed-literal phase. It proves
and checks exact reduction and lifting, with all attempts retained. One old case
gains closure (536/589 -> 537/589); the 64 fresh random cases have no gain.
Time, storage and cold replay all increase, so the policy remains optional.
Smaller selected residuals trigger more subsequent probing. Next test checked
signed-equivalence substitution from the saved paired traces on selected
unresolved nodes: 16 selected nodes affect 16 of the 52 missed source paths.
Complete recognition, full-CNF substitution, transport and matched costs remain
implementation obligations; these opportunities are not achieved new coverage.

**Checked signed substitution implemented:** the
[1,137-source study](../experiments/results/cnf-probe-equivalence/README.md)
substitutes a signed block certified by the first eligible opposite probe pair
through the full CNF. Exact child binding and model lifting preserve shared-variable
interactions; old recognition priorities and archives remain valid. Seven old
sources gain closure (567/625 -> 574/625 non-tiny), but 24 fresh random formulas
show no gain. The targeted pilot slightly reduces time/storage; the full run
increases both, so the policy remains optional. The 51 remaining source misses
contain 77 selected unresolved nodes. Their saved reasons imply 552 absent binary
clauses, of which 333 are already reachable through binary paths. The remaining
219 node/clause pairs affect 37 missed sources. Next test bounded checked local
learning on these paths, preserving the implication dependencies and charging
extra clause/propagation/archive work. No-path evidence is not semantic
nonredundancy, and no added closure or total-cost benefit is yet established.

**Bounded implication learning implemented:** the
[1,173-source study](../experiments/results/cnf-probe-learning/README.md)
checks each learned binary clause on the original source, then permits one
bounded continuation pass. A child requires strict support reduction; unsuccessful
learning stays recorded without clause-only recursion. Non-tiny closure rises
604/661 -> 607/661, including one fresh 48-variable source, with higher runtime,
space and cold cost. Counterfactual continuation choices without additions still
reduce the selected nodes on both old gains, while the fresh gain's node needs
the additional propagation in this pass. Do not conflate changed ranking with
stronger inference. The next supporting target is reuse of checked closures:
10,018 continuation certificates are identical to earlier ones. Test the added
clauses under the old closure before recomputing it, with exact dependencies and
shared proof checking. This could support further investigation of the 48 selected
leaves where learning remains inconclusive; no new benefit is yet measured.
The policy remains optional and all 54 remaining source misses are explicit.

## Checked closure reuse and the next selection gap (9 November 2026)

The [closure-reuse study](../experiments/results/cnf-probe-closure-compact/README.md)
implements the preceding supporting target. After checking all original probe
reasons and the learned batch, test additions under the same saved assumption
and unit closure. Reuse its proof only when every added clause is satisfied or
has at least two unassigned literals; otherwise perform full propagation.
Restriction preserves the original clause prefix and reason indices. Fresh
assumptions, edits and active additions cannot silently inherit the closure.
The old trace remains a valid derivation under extension, but a fixed point is
not a SAT answer. Lean proves the derivation and exact added-clause criterion;
Python separately checks references, source bindings, transport and model fibers.

The 1,209-input study preserves all 13,066 semantic nodes and every source plan,
with 634/697 non-tiny and 15/24 fresh random closures. Of 17,548 continuations,
14,705 reuse checked closures; 672 active repeated assumptions and 2,171 fresh
assumptions remain full probes. The compact sample gives modest total savings
(time 62.759 -> 61.687 s, SQLite 197.104 -> 196.096 MB, cold replay 26.785 ->
25.094 s). The failed verbose identity instead grows storage to 200.323 MB and
is preserved. Single-sample timings and checkpoint overlap are disclosed; the
ordinary solver is unchanged and no new family coverage is claimed.

Sixty-three source misses remain. Their selected remainder has 94 distinct
unresolved leaves: sixty learning-clear and 34 clear. Twenty batches reach cap
four; candidate enumeration up to sixteen exposes 61 further eligible clauses
on sixteen leaves across thirteen missed source paths. Thirty-eight existing
batches draw all clauses from a single assumption. The
[frontier](../experiments/results/cnf-probe-closure-compact/learning-frontier.json)
retains each candidate and its checked source reason, including no-opportunity
leaves. It does not execute a new batch or establish extra closure.

**Next experiment:** preserve the four-clause and probe caps, and compare batch
selection by activation of saved closures and diversity of assumptions with the
current first-four order. Check exact entailment/composition, charge candidate
recognition and ranking, retain all failures, and include a fixed-variable-choice
control. This returns the priority to splitting unresolved discovery cells;
active-continuation resumption is a smaller supporting optimization. General
compact coverage and polynomial arbitrary-SAT acquisition remain unproved.

## Bounded clause selection: one gain and one loss (9 November 2026)

The [selection experiment](../experiments/results/cnf-learning-selection/README.md)
implements the preceding target. It selects at most four clauses from sixteen
eligible original-source implications, preferring activation of uncovered saved
closures, a new origin assumption, total activation and original candidate order.
The checker first validates the source proofs, then reconstructs the exact
selection and checks the continuation, strict support reduction, child and lift.
Earlier family recognition/decomposition priorities remain unchanged. Any subset
of originally entailed clauses preserves all source models; Lean now records
that corollary. Neither its correctness nor a high score guarantees useful discovery.

The thirteen-source pilot gains one previous miss. The full comparison retains
all 1,209 previous inputs and adds 24 random 3-CNFs at 20/32/48 variables plus
twelve growing, signed and edited controls. It gains **1024** (SAT guarded input)
but loses **956** (SAT random 20-variable input): **662/733** non-tiny closures and
**16/24** fresh random closures under either policy. All twelve new controls
remain closed. The independent solver checks every original source and keeps
12,516 residuals per mode; a structural miss is not an incorrect SAT answer.
Seventy-one sources and 103 distinct selected leaves remain unresolved.

Total time rises **71.417 -> 73.194 s**, SQLite **227.385 -> 227.832 MB**, cold
replay **29.815 -> 30.359 s** and targeted Python peak **20.022 -> 20.121 MB**.
The peak excludes native memory/RSS and full-corpus peak. These are single
sequential samples without concurrent tests, builds or commits. Selected
unresolved literals fall 17,687 -> 17,327 while acquired nodes and logical probes
rise. Preserve this failed aggregate improvement; do not enable it by default.

Four independently checked local controls at each of 606 changed parents cross
old/new batches with old/new continuation choices. They distinguish a changed
clause set from changed choices but do not recompute whole-source coverage.
The [explicit path fixtures](../experiments/results/cnf-learning-selection/selection-paths.json)
show that source 1024 gains a forced reduction under identical choices and equal
scalar activation counts. At source 956 both batches activate zero saved
closures, and all four controls still force a variable. Old choices first
refute `14=true`; new choices first refute `16=false`, under either batch.
The actual new source plan then stays open. A local `forced` label, activation
count and origin diversity fail to capture this relevant structural difference.
Source 1189 has a locally improved common reduction but still does not close.

**Next experiment:** apply the selected batch while freezing continuation
variable choices/order to those computed from the old first-four batch. Charge
that baseline batch/ranking work; retain the clause/probe caps. Test 956, 1024
and 1189, then all old and fresh inputs. This policy is not yet implemented or
measured, and fixed choices do not guarantee old coverage. Track interacting
learned clauses, the first conflict and the child structure to refine discovery
features. Keep the existing pool-filter incompleteness explicit: it can use
edges from candidates later omitted, although every retained clause is sound.

All **353 Python tests** pass, including exhaustive small model fibers, signed
mixtures/edits, independent full replay, forged selections, corrupt reasons,
disabled mode and cold coexistence. All three full, three pilot and four preceding
archives replay byte-identically; warm reuse inserts nothing. Lean's build/axiom
audit passes at **4,122 declarations / 1,965 theorem declarations**. No Python
refinement, efficient complete classification or unrestricted SAT bound follows.

## Fixed choices reveal a residual-representation gap (9 November 2026)

The [fixed-order comparison](../experiments/results/cnf-learning-fixed-order/README.md)
executes the preceding controlled policy. At each exact parent, it reconstructs
the old first-four batch and variable ranking, then propagates the selected batch
under those choices. The checker recomputes the ranking after validating original
proofs. Earlier recognition/decomposition, exact reductions, strict support
decrease, model lifting and all local caps remain unchanged. The rule stays
optional and has a separate persistent identity.

The three-source pilot and full comparison both keep the previous gain 1024 and
loss 956; 1189 remains open. On all 1,245 old inputs plus 24 fresh random 3-CNFs and
twelve growing/signed/edited controls, non-tiny closure is **692/769** and fresh
closure **18/24** under all three policies. Fixed order changes no source closure
relative to selection. **77 sources** remain unresolved; the unchanged decision
solver checks every original source and retains **13,641 residuals** per mode.
All twelve new controls close. This is an exact but incomplete discovery layer.

Total time is **77.916 / 82.421 / 80.720 s** for baseline/selection/fixed, with
SQLite **252.244 / 252.498 / 252.391 MB** and cold replay **33.506 / 33.585 /
34.309 s**. Fixed order is 3.60% slower than baseline; the lower sample time than
selection is not a general speed claim. Selected unresolved literals fall
18,362 -> 17,971 while nodes and probes rise. The current frontier preserves
111 distinct unresolved leaves, including recognition outcomes, full probe
traces and unused implications. All timing samples are sequential and exclude
concurrent tests, builds and commits; targeted Python peak excludes native/RSS
and full-corpus allocations.

The [saved parent controls](../experiments/results/cnf-learning-fixed-order/mechanisms.json)
identify the missing structure. At source 956's 18-variable parent, baseline and
fixed order both force only `14=false`, leaving the **same 54-clause original
restriction**. Their learned views then retain three versus four extra clauses.
The baseline 17-variable/57-clause child closes; the fixed 17-variable/58-clause
child stays open with eighteen unresolved literals. Both batches are entailed
by the original source, so their restrictions have identical model relations.
Fixing immediate choices has not made recognition or descendant search invariant
to redundant representation. On 1024, the selected clauses still close the
27-variable child under the same forced `3=true` assignment.

**Next experiment:** represent the restricted original core separately from
checked propagation hints. Compare core-based identity/recognition with current
learned views on 956/1024/1189, the saved frontier and full old/fresh inputs. Keep
hint/policy context on discovery plans, even if a semantic core can share stored
decisions or certificates. Charge reconstruction, implication checks, transport,
lookup, serialization and cold replay. Changed source clauses, assignments or
dependencies invalidate stale hints. Retain failures and useful hints rather
than assuming all redundancy should be deleted. The proposed change is not yet
implemented or a measured gain. It uses explicit certified entailment and a shared
original source, not unrestricted semantic canonicalization.

All **358 Python tests** pass, including exhaustive small fibers, independent
full trace checks, changed-order fixtures, adversarial edits, invalid orders,
corrupt reasons and cold coexistence. Four full, four pilot and three preceding
archives replay byte-identically; both reports' 43 fingerprints match. The
unchanged Lean build/axiom audit passes at **4,122 declarations / 1,965 theorem
declarations**. Complete efficient classification, compact arbitrary-CNF coverage
and uniform acquisition bounds remain open.

## Parent-scoped hints recover the lost core (9 November 2026)

The [core comparison](../experiments/results/cnf-learning-core/README.md) implements
a deliberately scoped version of the previous proposal. The parent checks and
uses its learned hints, then restricts/substitutes only its original clauses into
the child. Terminal conflicts remain false. Descendants rediscover their own
hints; this is not yet inherited hint transport. Identical normalized cores at
the same policy/depth can therefore share plans without hidden context. Earlier
recognition overlaps, priorities, exact recomposition and unresolved cases remain.

The full 1,317-input study closes **719/805** non-tiny sources, versus **718/805**
for baseline and fixed order. It recovers 956 relative to fixed order and retains
1024, with no lost closures against either. All close **14/24** fresh random
inputs; **86 core sources** remain structurally unresolved. The independent
solver checks every original decision and retains 15,069 residuals per mode.
The saved 956 parent has the same forced `14=false` assignment and 54-clause
original core under both checked batches; that core closes while the fixed-order
58-clause augmented child stays open. The common-core test reuses the exact child.

This discovery gain has a cost. Baseline/fixed/core totals are **94.870 / 97.402 /
97.835 s**, SQLite **284.111 / 284.299 / 284.094 MB**, cold replay **40.281 / 41.160 /
40.384 s**, and six-case traced Python peaks **20.022 / 20.127 / 20.265 MB**.
These are single sequential samples; peak excludes native memory/RSS and full
corpus. The selected pilot's favorable time/memory results do not carry over.
The implementation still constructs the checked augmented target before its core.
This adds expected O(L+q+v) time and O(L+v) space; parent proofs remain stored.

The archive has 449 successful learned edges, 385 with changed normalized child
syntax, but **no two learned parents share a child core**. Its measured gain is
therefore a discovery effect, not large observed within-run core compression.
The frontier retains 124 distinct unresolved leaves (86 learning-clear, 38 clear).
Fresh 48-variable source 1297 is the largest unresolved discovery case at 1.47150 s;
its profile again identifies restriction, unit checking and propagation. Only
one successful learned parent appears there, limiting the reach of hint transport.

The next experiment transports checked implication evidence separately from core
recognition. Diagnostics find **907** eligible clause occurrences absent from the
immediate child core; **319** are learned again in that child's batch across
**165 edges**. Bind each transported hint to its source proof, exact reduction,
variable map and propagation context. Test those edges, 956/1024/1189, the saved
frontier and all old/fresh inputs, charging recognition, checking, storage and
cold replay. Repeated occurrences do not establish unique implications, saved
seconds or additional closure. Useful hints may expose structure, while context
changes can still alter bounded search. Supporting work should reuse checked
propagation state on the remaining dominant scans.

All **366 Python tests** pass, including exhaustive small fibers, independently
expanded reference checks, signed/adversarial edits, preserved terminal conflicts,
wrong-child rejection and cold coexistence. Two new Lean semantic restriction
lemmas pass the full build/audit at **4,125 declarations / 1,967 theorem
declarations**; Python and resource refinement remain open. Four full, four pilot
and four preceding archives replay byte-identically, warm reuse inserts nothing,
and both reports' 47 fingerprints match. There is still no uniformly efficient
construction of all arbitrary-CNF classes or compact global closure.

## Portable evidence isolates a ranking miss (9 November 2026)

The [hint-transport study](../experiments/results/cnf-hint-transport/README.md)
translates parent implication prefixes into independently checked unit-refutation
proofs against the exact normalized child. All **1,005 eligible occurrences**
across 494 learned-parent edges succeed without fresh proof search. The 449 prior
parents are extended by 45 distinct parents from 36 fresh sources. There are 984
distinct core/clause records. Source proof, assignment/substitution and variable
mapping are checked during preparation; portable replay needs only the exact core.
These are established proof-checking ideas applied to this representation gap,
not a new SAT class or a universal transport-completeness theorem.

An explicit context-keyed local plan recognizes the core, preserves earlier
overlaps/priorities, then optionally tries one bounded pass with transported
hints and core-ranked variables. An inconclusive pass falls back to the original
planner; ordinary descendants receive no implicit inherited context. The complete
ordered hint set is part of plan identity. Checked reductions and model lifts
preserve the exact child relation, but this extra pass is additional work.

Local closure is **223 -> 224 / 494**, with no losses. The one gain is local case
**97**, a 25-variable, 81-clause depth-zero core in an **unselected alternative of
source 977**. No saved selected source path includes it. In a controlled crossing,
both transported and child-rediscovered batches close with choices `(4,5,7,19)`;
both remain open with baseline-continuation choices `(4,5,7,11)`. Both successful
controls refute `19=true` and force `19=false,13=false`. Thus the observed cause
is ranking, not stronger transported clauses. Original-source coverage remains
the preceding study's **719/805**; this local result must not increment that count.

Runtime rises **14.41354 -> 16.82765 s**, plus **0.95129 s** preparation, SQLite
**55.120 -> 63.885 MB**, cold replay **4.70738 -> 7.72522 s**, and six-core Python
peak **7.372 -> 7.431 MB**. Ordinary nodes shrink but hint/context state outweighs
that saving. All **374 Python tests**, the Lean audit (**4,126 / 1,968 declarations /
theorems**) and four new byte-identical cold replays pass, with 51 matching
fingerprints. These local synthetic controls do not show a global speedup.

**Next:** use core-ranked continuation choices with the existing learned batch
and number of passes, beginning with 97/977 and 956/1024/1189 before full source
workloads. Keep all prior policies and any losses. Integrate portable hints into
an existing continuation only as a separate experiment. Original probe closures
show 1,456 inactive versus 102 active hint deltas across 196 cores; their reuse
requires proof validation and delta checks, and is not yet a measured saving.
Efficient arbitrary-CNF discovery, total closure size and global resource bounds
remain open.

## Core-order trial: reduced work, lost coverage (9 November 2026)

The [matched continuation-order study](../experiments/results/cnf-core-order/README.md)
keeps the selected learned batch, core child, priorities and caps. Choices come
from a complete original trace only after independent validation. Extraction is
O(p), avoiding a second learned view solely for ranking; earlier acquisition and
proof checking remain charged. No additional pass or inherited hint context is
introduced, and distinct policy identity preserves prior plans.

On 1,389 input queries (512 exhaustive tiny, 877 non-tiny), closure falls
**776 -> 775 / 877**, with no gains and a loss on source **956**. Both close
30/36 prior hint-study queries and 27/36 new queries. The local case 97 closes,
but source 977 remains open. Whole-source decisions all agree with the independent
solver. Operation time falls **120.81853 -> 116.67493 s**, discovery **88.69202 ->
85.68326 s**, SQLite **347.566 -> 346.976 MB**, cold replay **50.51029 -> 47.82982 s**,
and six-case Python peak **20.265 -> 19.623 MB**. The 1.13 s solver-time variation,
limited memory sample and single sequential run prevent a general speed claim.
This optional policy does not dominate the existing one.

At the saved 18-variable, 62-clause parent of 956, the selected batch is unchanged.
The old choices `(17,9,14,16)` refute `14=true`. The core choices `(9,17,18,2)`
are all inactive under the batch and stay clear. This separates useful old-trace
reuse from discovery of a newly informative variable. The resulting source has
one unresolved leaf with sixteen literals. The saved full paths retain this
ranking failure separately from the earlier redundant-child representation loss.

Among shared CNF/depth states, **239** learned reductions become clear, and
**16** clear states gain a reduction. In 189 of the losses, no original pair is
active. In all 255 gained/lost local states, active core variables plus novel
old-ranking variables have union size at most four; seven other changed states
already require five. This suggests a bounded continuation using these two
kinds of evidence, with original certificates retained and delta checks charged.
Inactive unchanged pairs cannot acquire a new outcome in the present forced/
common/equivalence procedure. This is not an executed combined policy, proof of
source-level recovery, or universal bound on the necessary candidate set.

The next run should test that combined selection on the saved controls, then
full old/fresh queries; preserve first-conflict and descendant regressions. The
frontier has **102 sources / 142 distinct leaves**, 99 learning-clear and 43 clear.
Source 1194 remains a useful cost control at 1.45407 s discovery; restriction,
unit checking and propagation dominate its separate profile. Sharing the already
checked sixteen-clause candidate pool can separately preserve old choices while
avoiding reconstruction, but cannot by itself expand structural coverage.

All **380 tests**, the unchanged Lean audit (**4,126 / 1,968 declarations/theorems**),
three full, three pilot and four previous cold archive checks pass. Fifty report
fingerprints and analyzer/report hashes match. The new choice policy's Python
implementation and lifetime resource bounds are not formally refined. No new
tractable category covering every CNF has been established.

## Activity-guided continuation and a signed-core gap (9 November 2026)

The [new policy](../experiments/results/cnf-activity/README.md) keeps old
continuation candidates unless both original closures remain inactive under the
checked selected batch. It fills freed positions with active core variables,
truncating only additions. All original proofs and earlier priorities remain.
A fixed source/batch cannot lose an old local reduction: omitted unchanged pairs
cannot supply a new outcome; all informative old candidates fit the cap and remain
ordered. An additional higher-priority reduction still gives local progress.
This argument does not give monotone whole-source coverage or formally refine
Python's implementation.

The full 1,425-query run preserves **806/913 non-tiny closures** with no gains or
losses. Source 956 is recovered relative to core-only ranking. Source 977 now
selects the old local case-97 core; its open part falls 138 -> 22 literals and two
leaves -> one. It remains unresolved. All 421 old learned reductions among 3,001
saved states survive; sixteen clear states gain one. All 255 prior gained/lost
local controls now reduce. The seven five-candidate controls truncate additions
while retaining every informative old choice.

Logical continuation attempts fall **31,741 -> 7,184**, but active/new propagation
increases **5,334 -> 5,569**. Single full-run time falls **161.35645 -> 134.22746 s**,
with substantial unchanged-solver timing variation. Balanced repeated eight-query
trials instead average **3.85140 -> 3.88671 s**. No runtime speedup is established;
the policy remains optional. Cold replay also grows, despite slightly lower stored
bytes and traced memory. All costs, unchanged/failed paths and trials are retained.

The next frontier is more informative than another ranking variation. It contains
107 sources and 147 distinct leaves: 61 inconclusive continuations, 39 empty ones,
46 clear passes without a learned batch and one without binary-ranked candidates.
An offline signed-subsumption diagnostic changes 105 leaves, removes 217 clauses /
666 literals, and exposes **seven 2-CNF cores**. Each removed clause has a retained
signed subset; exact source indices, complete coverage, normalized cores and
variable maps are saved. Original and reduced formulas have the same models on
the original variable universe, with disappearing variables unconstrained.

These witnesses could complete the current selected plans of **977, 1044, 1053
and 1365**, while 907, 1179 and 1363 retain another open leaf. This is a conditional
integration target, not four new measured source closures. The existing decision
solver's positive-clause subsumption does not provide this general signed step
in the pattern inventory. Next implement exact family exposure with source-bound
witnesses, checked lifting/recomposition and persistence, retaining earlier family
recognition. Charge discovery over all relevant states and cold replay; the
672,003 subset comparisons on the selected frontier are not full-workload cost.
Test signed/reordered/edited inputs and invalid retained-clause dependencies.

All **388 tests**, the unchanged Lean audit (**4,126 / 1,968 declarations/theorems**),
three full, three pilot and three previous cold checks pass. Both reports have 53
matching fingerprints, and diagnostic/timing hashes are retained. The existing
UP, model-lifting and semantic arguments remain distinct from an unproved global
acquisition, closure-size or unrestricted-SAT efficiency guarantee.

The original acceptance criteria and remaining integration scope follow.

Build an analysis mode over the current residual solver. It should discover
patterns from CNF input without generator labels and preserve source identities.
The solver already has propagation, Horn/dual-Horn/2-CNF leaves, matching
recognition, independent components and exact variable splits. Instrument and
extend these capabilities rather than presenting them as absent or duplicating
their logic. The history adapters' whole-base restrictions are a separate gap.

Record, per formula and residual: all recognition outcomes; checked evidence;
connected components and shared interfaces; attempts at explicit equivalence,
parity and matching structure; discovered conditioning variables/depth; and the
size and structural profile of the unresolved part. Report measured or supplied
width bounds separately from an uncomputed optimum. Explicit XOR input is not
evidence that hidden parity in arbitrary CNF has been recognized.

Start with exhaustive normalized CNFs over two variables (including empty
formulas and empty clauses), then seeded larger samples and structured mixtures.
Include renamings, literal/clause reorderings, duplicates, redundant encodings,
connected mixtures, bridge clauses and the guarded arbitrary-CNF unit expansion.
Evaluate whole inputs and conditioned components. Compare to existing routing
on identical inputs; the corpus generator's label must not select the method.

Acceptance criteria:

1. Every valid input receives exactly one outcome-vector cell, with all applicable
   positive certificates retained and unresolved cases visible.
2. Exhaustive small cases check coverage, classifier consistency and exact
   branch/component recomposition against truth tables. Tests complement proofs;
   they do not establish universal coverage or complexity by themselves.
3. Report how much unresolved literal/residual work remains, new distinct
   residuals and certified reuse, not just total SAT successes or timing wins.
4. Charge discovery failures, certificate verification, preprocessing, memory,
   updates, serialization, persistence and cold replay. Preserve regressions.
5. Save counterexamples that expose missing patterns or invalid combinations.
   Repeated restarts should reuse these results rather than rediscover them.

## Following iterations

First split the largest informative unresolved cells. Favor discoveries that
transfer across several families: component-local recognition, shared-variable
interaction, and conditioning that reveals different tractable classes in
different branches. Then investigate canonical descriptions and checked transports
that let equivalent discovered structures share state across histories.

Test edits that preserve a certificate and edits that invalidate it. A bridge
clause can merge components; a unit can expose an arbitrary guarded CNF. Preserve
old results while rebuilding only the affected valid dependency closure.

Choose each iteration by likely expansion of certified structural coverage and
reduction of unresolved interaction, with discovery and total cost measured.
Propagation queues, dense-posting compression and known-family speedups remain
useful, especially when they enable the discovery experiment; they no longer
automatically outrank discovery merely because a synthetic case is expensive.

The remaining universal question is whether all inputs admit useful states and
updates with uniform construction, size and evaluation bounds. An exhaustive
partition, small-case coverage or inexpensive updates after unbounded preparation
does not settle it. Keep the cost of the prepared oracle explicit.
