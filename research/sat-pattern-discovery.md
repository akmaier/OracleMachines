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

## Signed subset witnesses expose four sources (9 November 2026)

The [integrated terminal policy](../experiments/results/cnf-signed-subsumption/README.md)
now closes **977, 1044, 1053 and 1365**. No closure is lost. Across 1,461 inputs,
coverage rises **833 -> 837 / 949 non-tiny**; the old subset rises 806 -> 810 / 913.
Every removed clause has a retained signed subset. Exact source indices, core
normalization and model lifts are independently checked. Values on disappearing
variables are arbitrary, as established by three new Lean semantic lemmas.
Earlier discovery priorities remain; failed searches stay archived. Terminal-only
exposure preserves baseline boolean closure under unchanged earlier rules and
exact transports, without a formal Python refinement or resource guarantee.

The cost regression is retained: full single-sample total time **145.71977 ->
156.17943 s**, discovery **105.46141 -> 117.30413 s**, SQLite **404.410 -> 408.302 MB**
and cold replay **61.80056 -> 66.82085 s**. Twelve-query ABBA BAAB trials average
7.28617 -> 6.98024 seconds, but include all four gained sources; no general speedup
follows. New-query closure remains 27/36. The policy stays optional.

There are 3,753 terminal searches, 31 exposures and 3,722 unexposed cores. Each
of discovery/checking performs 33,367,619 subset comparisons. **81.17%** compare
equal-width distinct normalized clauses, which cannot contain one another.
Length filtering is the immediate cost target; no filtered implementation is
measured here. Saved search/evidence fields occupy 3.706 MB. Smaller node count
alone does not mean less memory or cheaper cold replay.

The remaining **112 sources / 149 distinct selected leaves** expose the next
structural gap. An offline control replays original probe proofs and uses all
their binary consequences as subset witnesses, including transitively redundant
clauses excluded by the current learning filter. It exposes **eight 2-CNF leaves**.
The current plans of **1185, 1289 and 1368** could close; five other affected sources
retain an unresolved leaf. These are prospective, not measured closures. The next
integration must charge implication enumeration, subset indexing, original-proof
checking, exact child mapping and cold replay without fresh probing or hidden
inherited context. All source witnesses and failed controls are saved.

Repeated restriction/propagation and proof checking remain the broader runtime
cost: source 1194 takes 1.60328 s discovery, with 5,763 restrictions, 4,657 unit
checks and 2,221 propagations in its separate profile. Efficient treatment of
irreducible interactions and a lifetime storage bound remain open. All **395 tests**,
the **4,129 / 1,971** Lean audit, three full/pilot/previous cold archives per group,
and 56 fingerprints in both new reports pass.

## Original implication proofs expose five more sources (9 November 2026)

The [integrated follow-up](../experiments/results/cnf-implied-subsumption/README.md)
uses all distinct absent binary implications from the original probe traces,
including binary-transitive consequences excluded by learning selection. A proved
binary can remove a longer clause even when it adds nothing to propagation.
Original subset exposures retain priority; only their failures try the augmented
core. Recognition still uses existing families and no generator labels. A new
Lean lemma proves model equivalence by composing entailment with signed-subset
coverage. Original proofs are checked before their origin coordinates, augmented
witnesses, normalization and lifts. Edited sources must be checked anew.

On **1,497 inputs**, closure rises **864 -> 869 / 985 non-tiny**, with gains on
**857, 1185, 1289, 1368 and 1467** and no losses. The old subset improves **837 ->
841 / 949**; fresh-query closure **27 -> 28 / 36**, including **15 -> 16 / 24** new
random 3-CNFs. All independent SAT answers agree. There are **82 implication
exposures** across encountered alternatives, not 82 additional source closures.
The remaining frontier has **116 sources / 148 leaves / 33,651 literals**.

Full-sample operation time is **169.84716 -> 169.80609 s**, discovery **127.44196 ->
126.71711 s**, SQLite **438.288 -> 437.621 MB**, cold replay **71.70525 -> 69.97623 s**,
but logical node state **178.289 -> 179.396 MB** and six-case Python peak **20.390 ->
21.161 MB**. No general speed or memory improvement follows. Pool enumeration,
proof replay, unsuccessful searches and persistence remain charged. Indexing skips
equal-width distinct clauses while preserving the old deterministic witnesses;
repeated literals use the old fallback. The new implication policy has its own
namespace; prior archives remain available.

An offline control filters every nonempty pool to proved binaries contained in a
long clause of the original minimal core. The pool shrinks **29,897 -> 7,505**,
with all **82** encountered exposures preserved. However, **no additional selected
leaf** becomes recognized, and the relevance scan costs **2,278,253 comparisons**.
This is a possible storage/acquisition improvement, not an integrated result or
universal family-preservation theorem. Further coverage needs new certified
relations or exact decompositions of unresolved interactions. Source 1194 remains
the largest unresolved discovery case at **1.67226 s**, with **5,763 restrictions,
4,657 simplification checks and 2,221 propagations** in its separate profile.

All **403 tests**, the **4,130 / 1,972** Lean audit, full/pilot/prior cold checks
and **59 report fingerprints** pass. Semantic composition does not formally refine
Python or establish polynomial acquisition, compact closure, lifetime storage or
an efficient partition for unrestricted SAT. Detailed controls and saved failed
pools are in the study; earlier results are preserved.

## Exact-check reuse preserves the discovery partition (9 November 2026)

The [bounded cache experiment](../experiments/results/cnf-checked-probe-reuse/README.md)
changes the cost of repeated proof replay while preserving every source profile,
selected plan, proof and database byte on all 1,497 saved inputs. Coverage remains
**869/985 non-tiny**, with **116 sources / 148 leaves / 33,651 literals** open.
A full source/proof/policy key binds each previously successful check; no first
check, newly edited input or unverified implication can enter through a hit.
Cold replay starts empty, and the persistent evidence remains unchanged.

Full-sample time falls **168.30879 -> 150.39216 s**, discovery **125.59834 ->
108.60557 s**, and cold replay **71.60183 -> 62.58623 s**. Twelve-query repeated
means are **6.17550 -> 5.33388 s**. SQLite is unchanged; six-case Python peak grows
**21.161 -> 22.258 MB**. These results are scoped to synthetic workloads. The
1 MiB retained-string cap is not a process-memory bound. All 410 tests pass;
the preliminary tuple/list key-alias counterexample and fix are retained.

The largest baseline miss, source 1194, now has **3,399 restrictions / 2,303
simplification checks**, down from 5,763 / 4,657; propagation stays at **2,221**.
First-time propagation and reusable source preparation are the next runtime
hypothesis. New coverage still needs new certified relations or exact decomposition
of unresolved interactions. This cache has no new family recognition, proof of
compact closure or unrestricted-SAT efficiency consequence. Prior Lean sources
are unchanged; the Python cache invariant is not formally refined.

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

## 2026-11-09: cheaper acquisition with identical structural coverage

The [ordered occurrence experiment](../experiments/results/cnf-ordered-propagation/README.md)
preserves all 1,497 profiles and database bytes while reducing discovery time
111.13169 -> 97.76173 s. Balanced selected-query controls support the saving;
short-conflict and forward-chain regressions remain visible. Coverage is still
869/985 non-tiny, with the same 116 open sources and 148 selected unresolved leaves.
The proof-order argument and per-call resource bounds are recorded in
[ordered propagation](ordered-propagation.md). No new recognized class or
unrestricted acquisition bound follows.

Restriction and residual reconstruction now outrank propagation in the expensive
source's profile. Sharing exact source/assumption state is the next acquisition
opportunity. Broader coverage still needs a concrete certified relation or exact
interaction decomposition in the unresolved frontier; faster repeated checks
are supporting work, not a substitute for that discovery obligation.

## 2026-11-09: source-index sharing preserves coverage but exposes a cost tradeoff

The [restriction-index study](../experiments/results/cnf-indexed-restriction/README.md)
shares prepared immutable source state across assumptions and preserves all previous
answers, profiles and archive bytes. Coverage remains 869/985 non-tiny, with the
same 116 sources unresolved. First-sample discovery and cold replay improve, but
full total initially regresses and six-case memory grows; selected controls favor
reuse, while new/equal-source controls regress. The reversed full run gives paired mean savings of
4.37% total, 8.36% discovery and 7.30% cold replay, with the initial regression
and memory increase retained. Two samples per mode establish no universal win.
The stronger structural discovery obligation is
unchanged. The next named compute bottleneck is independent simplification checking.

The [source/index invariant](indexed-restriction.md) makes immutability, object
lifetime, edited sources, fallback and output assembly explicit. It supports an
exact implementation of restriction, not a new SAT category. Further coverage
needs source-entailed relations or exact interaction decompositions; savings in
existing acquisition should support those experiments rather than replace them.

## 2026-11-09: cheaper independent checking and a concrete missing class

The [one-pass reconstruction study](../experiments/results/cnf-single-pass-check/README.md)
keeps all current recognition outcomes and archive bytes, with 6.60% less full
discovery time and 5.62% less total time. Cold replay slightly regresses and
six-case peak memory is unchanged. The support-cache alternative regresses and
is preserved; no additional cache is selected. Tests and the prefix invariant
support the independent direct checker without a Python/Lean refinement claim.

The next-gap probe finds **35 of the 148 selected unresolved leaves** admit a
consistent variable polarity change making every clause Horn. Positive flips are
directly checked; negative implication paths refute only the auxiliary pair
constraints. All 512 two-variable formulas agree with exhaustive flip enumeration.
The 35 positives contain 852 literals, versus 33,651 across the frontier, so most
remaining interaction is still unexplained. This is a known recognition reduction,
not a newly discovered tractable class; the full study links its primary source.

This gives the next concrete integration task: a source-bound, versioned polarity
certificate and exact model transport, followed by ancestor recomposition and
matched full acquisition/cold replay. No new root closure is claimed yet, and
the existing inventory remains at 869/985 non-tiny closure with 116 source misses.
Retain overlaps, negative class certificates and unresolved cases; do not interpret
failure to rename as an UNSAT certificate for the original CNF.

## 2026-11-09: checked renaming closes residuals across source classes

The [full integration](../experiments/results/cnf-polarity-horn/README.md) closes
all 35 saved positive leaves and recomposes **29 additional complete sources**.
Non-tiny structural coverage rises **869/985 -> 898/985** with no losses. The
current remainder is **87 sources / 106 selected leaves / 32,404 literals**. All
106 leaves have independently checked exclusions from renamable Horn; there are
no pair-budget misses on this selected frontier. Most are width-three CNFs.

A separate normalized-original-source probe records negative renaming
certificates for **all 29 gains**. Their whole source does not admit this renaming;
existing conditioning and reductions expose residuals that do. This supports
composition across classes, rather than merely adding a whole-source category.
The new recognizer is a terminal fallback, not a globally evaluated overlap
coordinate. A cap remains unresolved; auxiliary UNSAT never certifies original
UNSAT. Lean proves the polarity involution and SAT/UNSAT transport. Python
pair recognition, normalization, persistence and costs remain separate obligations.

Single-run discovery falls 4.95%, fresh SQLite 4.63% and six-case Python peak
15.73%; warm replay regresses. Old archives remain preserved and consume space.
All 441 tests, complete cold audits and the Lean axiom audit pass. Detailed
resource and provenance limits accompany the saved results.

The next investigation should use the saved auxiliary conflict paths as exact
obstructions to this recognition class. Search for shared obstruction variables
or interfaces whose conditioning exposes useful families in both branches,
measuring coverage and acquisition under matched budgets. The paths do not prove
a small interface exists, and a full Boolean partition alone is not an efficient
solution. The unresolved sources still consume 70.6% of discovery time; source
1448's profile puts reconstruction, normalization and indexed subset checking
ahead of polarity recognition. Reuse those computations where exact bindings
make it economical, without replacing the broader discovery objective.

## 2026-11-09: direct obstruction overlap misses indirect interactions

The [obstruction-conditioning experiment](../experiments/results/cnf-obstruction-frontier/README.md)
preserves checked source-linked negative evidence and tests a fixed alternative
ranking at the same budgets. Giving both policies one extra split at each saved
frontier leaf closes 60/106 under the existing ranking but only 57/106 under the
new rule. Three gains and six losses, slower discovery and larger SQLite are
preserved. The optional rule is not promoted. Original-source coverage remains
898/985; the frontier experiment must not be added to that denominator.

Five of the six displaced old winning variables lie outside the recorded
obstruction's source support. The raw-restriction invariant is still correct:
without assigning a source-support variable, those exact path clauses survive.
It does not imply that later propagation or a different recognized family cannot
close a branch. A guarded fixture also proves that pair endpoints alone omit
relevant whole-clause deletion variables.

Original checked probes already explain case 4's indirect interaction. Variable
6 lies outside the obstruction, but its two closures force variables inside it
and damage the saved paths without new propagation. This does not explain cases
17 and 50, whose original traces leave the paths intact; subsequent checked
acquisition closes their branches. Missing original probes for other candidates
remain explicit. The next task is reuse of these existing consequences across
classes and candidate diversity, not treating the first auxiliary refutation as
a complete model of structural opportunity. The union 63/106 is only a coverage
observation; a cheap combined policy remains to be constructed and measured.

All 448 tests pass; cold and warm replay preserve all results. The proof and
conditional resource account are in [obstruction conditioning](obstruction-conditioning.md).
Lean's existing exact branch semantics apply, but its sources are unchanged.

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

## 2026-11-09: the information gap in single-assumption probe ranking

The [probe-reuse test](probe-rank.md) keeps every baseline conditioning candidate.
Original checked unit counts only reorder them. Frontier closure stays 60/106,
but mean discovery regresses 4.82% across reversed execution orders. The fresh
96-case comparison keeps 71 closed and changes no order: 36/39 OR states lack
binary clauses, and 147/156 candidate positions have no paired original traces.
A normalized minimum-width-three CNF cannot yield a unit after assigning just
one variable. This identifies a concrete discovery gap: multi-variable interactions
or the newly exposed binary relation, rather than more tuning of unit counts.
Keep exact composition and recognition costs explicit; no uniformly small
interface is established. The old policy stays at 898/985 original-source coverage.

Two Lean lemmas prove membership preservation and local closure invariance under
explicit child correspondence. All 453 Python tests pass, including old-row/cold
preservation and exhaustive small model checks. The optional heuristic is not
promoted; both complete execution orders and every earlier result are retained.


## 2026-11-09: binary paths expose redundant wide clauses

The [retained-binary experiment](binary-paths.md) turns original implication
paths into checked wide-clause deletions, without deleting their binary reasons.
It expands original non-tiny closure 898/985 -> 901/985, with gains at sources
1007,1065,1072,1363 and one loss at 1471. The loss concerns bounded structural
search, not SAT correctness: a sound deletion removes variable 1 from a local
candidate pool even though its old plan closed. Both archives remain retained.
Their union covers 902/985 known inputs, without an efficient combined policy.

The extra-depth frontier closes 63/106 rather than 60/106, also against a direct
binary-subsumption control; transitive reasoning contributes three gains. A new
96-case sample stays at 75 closures. Discovery costs rise 19.06% and fresh archive
bytes 13.93% on the full corpus, so this extension is not the default. Acyclic
binary graphs dominate the unresolved states, limiting an SCC-only next step.

Next transport successful plans through equivalent reductions, reuse preparation
across those reductions, and test certified literal elimination using the same
relations. Explicit source/name transport and invalidation are necessary. The
rule is established SAT preprocessing; neither complete cheap classification nor
uniform polynomial acquisition follows. All 461 Python tests and the Lean build
and axiom audit pass. Four new lemmas prove the retained-path semantic rule.


## 2026-11-09: preserve a closure independently of the new scheduler

The [exact-plan reference](retained-plans.md) turns the previous archive union
into an integrated prepared-history policy. The earlier closed plan is verified
under its own configuration and referenced at the same normalized CNF and depth.
The new scheduler need not rediscover its successful variable choices. Full
closure rises 901/985 -> 902/985, recovering source 1471 without losses against
either earlier policy. Preparation remains an explicit prerequisite.

This expands available certified coverage, not the list of recognized SAT
families. The 96 fresh depth-two inputs still close 88; their 20 internal
references are all family leaves and give no acquisition-node saving. Discovery
regresses 3.46% there. Full prepared-history discovery improves 16.65% and added
storage 37.36%, while sampled Python peak grows 19.68%. General equivalent-core
transport and upgrades after later preparation remain open. The optional run
leaves 83 original sources, 99 selected leaves and 31,203 literals uncovered.

Next distinguish references that avoid nontrivial descendant acquisition from
cheap family matches, and investigate checked literal elimination or interfaces
on genuinely new cores. The newly identified repeated storage census is a large
metadata cost to remove, but does not itself broaden structural coverage. All
469 tests pass; the existing Lean audit passes, with no new Python refinement.


## 2026-11-12: archive accounting exposes the remaining discovery work

The optional [accounted residual solver](residual-accounting.md) eliminates a
full archive census after every ordinary query. The same 1,497 prepared sources
retain exactly the same profiles, plans and 902/985 non-tiny closures. All source,
pattern and residual evidence digests agree. Query cost drops 171.12270 ->
87.88366 seconds; discovery stays near 81 seconds and now accounts for about
92.6% of the remaining total. The 83 unresolved sources, 99 selected leaves and
31,203 literals are unchanged. This is not a discovery gain.

Prepared-history fresh controls keep 88/96 closures while query cost falls
15.20412 -> 8.38678 seconds; an empty-history control shows no clear acquisition
saving (7.70202 -> 7.73052). Opening and conflicts can still require a full scan.
One counter row and five triggers add 4 KiB; prior evidence is preserved.

The next discovery-supporting step is a source-bound checker for selected sound
proof dependencies, retaining the complete failed acquisition trace separately.
Then test transport into different equivalent cores and checked binary variable
elimination to broaden the unresolved cells. Accounting neither shrinks these
cells nor bounds their search. Keep the default 898/985 policy and optional
prepared 902/985 result distinct.


## 2026-11-12: reuse partial evidence without inventing closure

The [prepared-probe extension](prepared-probes.md) independently checks saved
probe traces from exact old unclosed plans. Other recognition and planning still
run. A failed overall expansion can thus supply valid intermediate analysis,
but the hint proves neither an old closure nor UNSAT. Source and settings changes
must prevent reuse; no old classification or descendant graph is trusted.

The 1,497-input comparison keeps every root, profile, summary, answer and stored
evidence byte unchanged. It reuses 2,437 traces and reduces fresh probe attempts
21.63%, while discovery time falls only 1.62% in this ordered run. Verified probe
attempts are unchanged, and no new structural coverage follows. The same 83
sources / 99 selected leaves / 31,203 literals remain open. The new cost attribution
puts 82.74% of previous discovery time in the 83 open sources, shifting immediate
attention from closed-proof references to their still-expensive intermediate
checks and transformations. Exact transport into shared cores and checked binary
variable elimination remain coverage candidates. Default coverage stays 898/985;
prepared optional coverage stays 902/985. No polynomial bound is established.


## 2026-11-12: distinguish equal CNFs from shared structure across different CNFs

The [reconstruction investigation](indexed-check.md) finds little amortization from
source-object indexing. A no-eviction audit of source 1194 observes 2,537 source
objects but 2,167 distinct exact CNFs. Only 370 admissions could be removed by exact
whole-CNF interning before charging recognition. The 96-input control and isolated
restriction-memo pilot regress; neither candidate is promoted. No new family closes.

The next discovery-supporting question is whether different branch residuals share
clause blocks or small checked edits that permit cheaper recognition and independent
checking. Preserve source bindings, clause order and reason positions. The previous
clause-support cache already regressed, so overlap alone is insufficient: a useful
pattern must avoid more work than recognizing and maintaining it adds. The earlier
83 unresolved original inputs remain the coverage target; these local diagnostics
are not a new full-corpus or unrestricted-SAT result.


## 2026-11-12: shared clauses do not yet make discovery cheaper

The [clause-mask investigation](clause-mask-reuse.md) confirms about 70% clause
identity reuse across different residuals in two costly sources. A bounded,
independently validated mask reduces literal work 55.10% in the 96-input control,
including preparation. However, both execution orders take more total time and
about 41% more sampled Python peak memory. All answers, evidence and 88 closures
agree; every cold replay preserves its archive. The candidate remains optional,
with no default change and no new full-corpus or structural-coverage result.

This narrows the next discovery question. Prefer bounded checked variable
elimination and transport into shared equivalent cores on the 83 unresolved
original sources. Measure eligibility and transformation growth before designing
another cache, retain source binding and model lifting, and count recognition,
checking and output work. Sharing unchanged clauses is already substantial;
merely adding scalar summaries does not remove their per-clause processing.
Coarser block or delta representations remain open but unimplemented. Complete
bookkeeping coverage still does not establish efficient closure of every cell.


## 2026-11-12: exact elimination exposes 29 additional original-source closures

The [bounded-elimination policy](variable-elimination.md) projects an unresolved
CNF by completely resolving a selected variable's opposing clauses. The checker
reconstructs every pair, rejects growth of clauses or literal occurrences, binds
the exact child and restores models. Its null witness means unresolved, not
nonmembership. Lean proves existential projection with explicit tail-independence
premises; Python refinement and cost verification remain open.

The 99-leaf study closes 37 leaves, compared with 14 for pure-only elimination and
zero for the preceding policy. A separate whole-input run on the 83 saved misses
closes 29 originals, versus 11 pure-only and zero baseline. The bounded result
retains every pure-only closure. It leaves 54 originals, 59 selected leaves and
26,205 literals unresolved. These are gains on the saved failures, not evidence
that every CNF admits a non-growing elimination or an efficient family endpoint.

All acquisition and retained state remain charged. Original-source query time
increases 64.76503 -> 80.09857 seconds and the archive increases
605,675,520 -> 621,146,112 bytes. The ordinary solver's counters do not change.
The next questions are the structure of the growth barrier and exact reuse of
failed occurrence-neighborhood analyses. Retained-clause subsumption of resolvents
is an explicit candidate. Recognition, source edits, witness checking and model
compatibility must be included; the added closures do not erase those costs.

## 2026-11-12: redundant resolvents do not explain the remaining closure gap

The checked [subsumption fallback](subsumed-elimination.md) permits ten new
elimination steps on the 59 remaining leaves, but closes none. On all 83 original
misses it preserves exactly 29 closures, with higher query time and storage.
The same 59 selected leaves retain 26,181 rather than 26,205 literals. This
separates the existence of a valid simplifying step from reaching a recognized
family. Every new edge is checked independently; source and child decisions
agree in separate diagnostics. The negative control remains optional.

A stronger discovery opportunity is the current literal non-growth restriction.
With non-growing clause count, normalized intermediate CNFs still have at most
m0*n0 literals along an elimination-only chain. The final diagnostic finds a
candidate in 48/59 leaves without subsumption, or 49/59 with it, if up to eight
additional literals are permitted. Fifteen plain candidates need only one. The
next experiment is plain clause-count-based admission with exact checking and
explicit intermediate width. These counts do not establish additional closures,
universal elimination availability or efficient classification of arbitrary SAT.

## 12 November: clause-count admission gives two more original closures

The [clause-count-only fallback](clause-bound-elimination.md) permits a checked
increase in literal count after the earlier joint non-growth proposal is null.
Full opposing-pair projection, exact source/target bindings and model restoration
remain checked. On the 59 final leaves from the previous subsumption run it
closes one; on the 83 original prior misses, with the same paid preparation, it
closes **31 versus 29**, losing none. Both added originals have 48 variables.
They are selected earlier failures, not untouched holdouts. There remain
**52 original sources / 57 selected leaves / 25,488 literal occurrences** open.

The gain costs more: original-source query time **78.06321 -> 113.63899 seconds**
and archive bytes **621,146,112 -> 674,234,368**. All 2,504 new elimination edges
pass independent endpoint solving and SAT model restoration; complete cold
replay preserves prior rows and bytes. The ordinary solver's answers and search
counters match. This is broader certified structural coverage, not reduced SAT
search or a fresh full-corpus measurement. The optional rule is not promoted.

Lean proves the conditional counting invariant: normalized formulas with at most
m0 clauses over decreasing support from n0 variables occupy at most m0*n0 literal
slots per formula, with at most n0 steps and (n0+1)*m0*n0 total formula slots on
one chain. It does not prove a next pivot exists, that a useful order can be found
efficiently, or that the whole discovery graph is small. A failed greedy chain
also does not exclude a successful order from its original formula. This keeps
recognition outcomes distinct from membership in a stronger semantic class.

The fixed B=64 opposing-pair cap would also bound a chain permitting clause
growth by m0+B*n0 clauses. Such a policy remains unimplemented. Local closure
opportunities, their transfer and their total acquisition cost must be measured
before inferring anything about efficient coverage of all CNFs.

## 12 November: extra low-growth steps do not imply useful endpoint coverage

The checked [additive budgets](additive-elimination.md) allow one or two extra
clauses after the preceding elimination rules fail. Fifty of the prior 57 leaves
had an eligible initial pivot at allowance two. Nevertheless, both new policies
close zero saved leaves and retain exactly the baseline's 31/83 original-source
closures. The extra 1,021 / 2,530 edges all pass independent endpoint checks and
SAT restoration. They expose no additional recognized original endpoint under
the selected orders. Selected residual literals and persistent acquisition bytes
increase. The controls therefore separate local availability, exact projection,
bounded formula size and successful structural classification.

Lean bounds one accepted normalized chain by n0 steps, m0+d*n0 clauses per state
and (n0+1)*n0*(m0+d*n0) formula slots. It does not prove pivot availability, an
efficient useful order or a small whole planner. The next discovery question is
which pivot choices expose units, implications, separators or a recognized
family, and whether that signal can be found and reused at lower total cost.
Small-budget alternative orders and explicit failed lookahead records are more
informative than assuming larger clause-growth budgets will improve coverage.
The current optional policies are not promoted. The full-corpus baseline remains
902/985; these selected old failures do not update that measurement.

## 12 November: reuse a necessary condition inside subset recognition

The [subset follow-up](anchored-subsets.md) finds no repeated ordered CNF within
independent proposal or checking roles on the costly retained trace. Whole-input
caching has zero hits there. A required-literal posting index instead skips
impossible retained subsumers, preserving exact first-witness certificates and
all source-level classifications. Independent checking rebuilds its own index.
Lean proves the abstract filtering and witness-order lemmas; all 521 tests pass.

This is supporting cost work, not broader coverage. Matched histories must be
byte-identical, so failed alternatives and prior proofs remain available. The
shared-literal regression and extra temporary index allocation are retained.
The next discovery question remains whether a small, charged set of alternative
pivot orders exposes a useful endpoint on the stalled cores. Local variable
reduction, a larger allowance and a conditional small-chain bound have already
failed to supply such progress in the preceding additive experiment.

## 12 November: different pivots mostly recover already known open cores

The [bounded alternative-pivot study](pivot-alternatives.md) retains up to eight
fully recognized alternative targets from four earlier elimination ancestors
per open original. It preserves exact projection, source/target bindings and
old plans. Any gained local endpoint must compose through the original AND,
conditioning and unary proof structure before counting as source coverage.

The first schedule tries 316 alternatives on the 83 originals and gains no
closure; 295/316 reach exactly the same selected unresolved canonical frontier.
A follow-up prioritizes pivots sharing a clause with the selected pivot, raising
interacting trials from 45 to 74 but still gaining no closure. It finds seventeen
novel selected leaves, compared with thirteen before. Both retain 31/83 original
and 88/96 repeated-control closures. These are negative development results,
not evidence that other orders or semantic classes have been excluded.

This exposes an important distinction: new immediate CNFs can lead to exactly
the same already stored unresolved problem. The next discovery target is a
useful divergent continuation, with exact-state reuse and a cap on newly explored
states. Later ancestors and coupled deviations remain untested. Compatible new
proof rows are retained as base-bound deltas, keeping every failed exploration
available for future reuse. All 527 tests pass; formal semantics are unchanged.

## 12 November: moving deviations toward unresolved terminals

The [ancestor-selection study](frontier-pivots.md) tests the previous later-node
gap explicitly. Both schedules reuse the union of all prior pivot proof graphs
and failed trials. Nearest-terminal selection ranks elimination nodes by longest
selected open path to a terminal and tries four, versus the early four-node
control. Both receive eight new trials per open input, with exact prior trials
checked and skipped rather than reacquired.

The frontier schedule adds 102 trials / 90 recognition nodes on the originals,
versus 145 / 266 for the control. Neither improves 31/83 coverage. Twenty trials
in each expose new selected leaves, and the frontier schedule still reconverges
in 82/102 trials. On the repeated control, frontier search exposes changed leaves
in 7/10 trials, but all seven increase unresolved literal count; coverage remains
88/96. Novelty, smaller local size and a later ancestor are insufficient endpoint
signals in these tests. This is evidence to narrow the next search toward coupled
changes at retained divergent states, with an explicit descendant-state budget.
It neither exhausts later ancestors nor supplies a tractable partition of all CNFs.

## 12 November: two-step continuations and a concrete growth obstruction

The [coupled continuation study](coupled-pivots.md) tests an interacting second
pivot on up to four previously retained divergent first routes. Both steps retain
the same pair/growth limits. An admission guard counts all newly entered recognizer
states and descendants, with a per-input limit of 32; it never turns a budget stop
into closure or a negative SAT result. All completed child proofs persist.

The selected originals gain 25 pair records and 32 nodes without changing 31/83
coverage. Repeated controls gain 15 / 17, retaining 88/96. No admission cap binds.
Relative to retained first routes, 17/25 original and 11/15 repeated trials have
the same unresolved frontier. All but one original trial use only seed leaves;
the repeated run introduces no new unresolved leaf. This separates new paths from
new structural coverage and from globally unseen residual states.

The sole new core (35 variables, 150 clauses) provides a reproducible local
obstruction. Within the 64-pair cap, its 30 admissible first pivots grow by at
least three clauses, and all 662 admitted ordered pairs grow by at least seven.
Interacting pairs grow by at least fifteen. The candidate cap truncates none of
these variables. A temporary relaxation with final growth at most four therefore
cannot unlock this core. The result concerns this representation and move rule,
not SAT complexity or semantic membership in every tractable family. The CNF and
all pairs persist for a controlled growth-three escape plus ordinary simplification.
Any subsequent leaf closure must be checked through the saved open alternative
routes before claiming an original-source gain.

## 13 November: bounded growth exposes a complete alternative plan

The [controlled escape](growth-escape.md) admits the unique minimum-growth-three
pivot in that saved core. Its raw projection grows from 150 to 153 clauses, but
the unchanged recognizer then closes it through four newly acquired probing
states. The target retains the old configuration and remaining depth, allowing
exact reuse of earlier descendants. Growth two admits no pivot on the same core;
a 32-state cap permits this four-state acquisition without being reached.

New finite route witnesses compose the result through saved open coupled/pivot
alternatives, requiring complete component and conditioning premises. A least
fixed point permits only finitely justified closure; replay rejects cycles,
missing premises and incorrect route bindings. Selected-original coverage rises
31/83 -> 32/83. The gained 48-variable original, core and target are independently
refuted by the complete reference solver, whose 212 proof nodes are preserved.

The pattern to investigate is an exact projection that enables effective bounded
probing, even when it initially enlarges the CNF. Minimum raw growth, support
reduction and a new residual do not individually promise such progress. Compare
the changed implication/probe structure before applying the same bounded policy
to other preserved cells. The earlier raw-pair admission obstruction is unchanged:
this success uses ordinary simplification after the first exception.

All 540 tests pass. The new source witness has 47 steps, including one coupled
route and one growth exception. These results concern one selected development
source, not an efficient covering partition, an independent holdout or a new
full-corpus measurement. Acquisition, paid-history verification, finite-plan
composition, serialization and cold replay are recorded separately.

## 13 November: the apparent growth barrier also hides a probe-selection gap

The [probe-window diagnostic](probe-window.md) finds that the successful projection
does not create its first useful failed assumption. Source variable 14=true was
already refutable; removing two binary clauses promotes it into the bounded probe
window. Complete checked single-assumption traces distinguish this ranking effect
from a new propagation refutation. They do not establish a universal relationship
between elimination and propagation strength.

A source-bound continuation now reuses the original recognizer configuration,
tries the next four untried binary-frequency variables, and persists both clear
and forced windows. At most four unresolved sources and 32 new recognition states
are visited per input. Checked transformations survive interrupted target
acquisition, but only actual checked targets become coverage premises.

Selected-original coverage rises 32/83 -> 36/83, with three SAT and one UNSAT
gain among the 48-variable development sources. All 36 stay covered when the
earlier growth-exception route is removed. The experiment adds 70 window records
and 81 nodes; paid-history verification remains much costlier than resident search.
All 543 tests and cold artifact/reference checks pass. No independent holdout,
full-corpus result or efficient arbitrary-SAT partition is asserted.

The largest observed discovery gap is continuation after a clear window: 51 of
52 still have 3--24 later ranked binary candidates available. Current reuse of a
source/width record avoids repeating a test but does not advance its position.
The next change should bind an explicit continuation position and reuse the
already checked prefix. Forced-but-open residuals remain a separate group; a
forced value alone does not guarantee complete structural coverage.


## 13 November: shared checked prefixes advance the discovery cursor

The [prefix-continuation study](probe-continuation.md) adds source-bound blocks
whose offsets require complete checked clear predecessors. Negative attempts are
referenced without rediscovery; forced blocks resume exact residuals. Missing or
foreign prefixes, skipped candidates and unsupported exhaustion are rejected.
All previous recognizer identities, failed trials and solver results persist.

Coverage rises **36/83 -> 39/83**: one SAT and two UNSAT 48-variable development
originals, independently checked. All 39 remain covered without growth-exception
routes. The run retains 51 continuation blocks (43 clear / eight forced), five
initial windows and 45 nodes. It performs 409 new assumption attempts while
reusing 408 previous ones. No budget binds: at most 13 new states / three sources.

Matched warm ranking/discovery/checking uses 373 versus 781 attempts and median
0.13230 versus 0.27631 seconds (2.09x substep speedup). This excludes already-paid
prefix verification, persistence and target recognition in both modes. Resident
expansion costs 0.56578 seconds, whereas preparation, full cold audit and separate
route replay cost 64.41, 110.39 and 63.13 seconds. Working storage grows 1,359,872
bytes. There is no end-to-end solver speedup, peak-RAM or new full-corpus claim.

All 547 tests and eight-table cold reconstruction/reference checks pass. The
saved suite log retains 20 existing SQLite warnings. The complete history now
has 41,461 pattern nodes, 75 windows and 51 continuation blocks, plus all previous
trial/source/proof tables. The separate reference archive retains 513 nodes.
Formal sources and manuscript are unchanged; earlier full coverage stays 902/985.

Next: 42 clear streams retain 2--20 eligible candidates, and four forced targets
remain open after finite composition. Continue these saved streams before raising
caps, inspect the unresolved targets, and profile cold proof replay for the largest
runtime opportunity. Candidate availability and complete cursor bookkeeping do
not establish efficient coverage of arbitrary CNF.


## 13 November: resumed prefixes close six originals and certify a probing limit

The [resumption study](probe-resumption.md) restores the complete verified
checkpoint lineage and keeps the four-source/32-state policy. Coverage increases
39/83 -> 45/83: four SAT and two UNSAT gains, independently checked on six reused
48-variable development sources. All 45 remain covered without growth-exception
routes. Forty-six new blocks (39 clear / seven forced), 327 attempts and 74 nodes
persist; 758 saved-prefix attempt references avoid repeating prior discovery.
Case 46 closes after using all 32 admissions. No input is interrupted.

Resident search/check/persist/compose costs 0.53596 seconds, preparation 65.21,
full cold inventory 108.60 and separate route replay 63.07. Storage grows
1,581,056 bytes. These are additional discovery costs, not a whole-solver speedup.
The current history has 41,535 pattern nodes, 75 windows and 97 continuation
blocks, with all previous trials, source bindings and solver proofs retained.
The separate reference archive adds 1,238 checked proof nodes.

The open selected paths expose 41 clear streams across 38 originals. Thirty-six
streams retain 1--16 candidates; five exhaust the binary ranking. A separate
source-bound diagnostic proves that these five have no single-assumption unit
refutation: 104 checked attempts cover all 52 binary-variable instances, and
79 remaining instances cannot create an initial unit under either value. This
excludes that inference rule, not satisfiability or stronger structural reasoning.
The 11-variable encoding-cap source has minimum width five: at most three assigned
variables leave clause width at least two. The other four sources have width two.

The useful next reuse gap is extracting common consequences, equivalences and
binary implications from all saved trace pairs. The old bounded initial profile
did not consume the later window traces. If those facts are insufficient, target
bounded nested reasoning on the width-two sources and a different structural or
adequately deep approach on the width-five source. Continue the remaining streams
as a coverage control, with cold dependency checking still the largest runtime
cost and peak RAM/independent evaluation still open.

All 557 tests pass. The acquisition artifact separately preserves 552-test and
cold-reconstruction/reference evidence. Two diagnostic status-assumption failures
are retained: learning_clear separates original-source attempts from a nested
augmented-source continuation. The final diagnostic directly checks the original
traces and excludes the nested ones. Its successful run costs 5.35440 seconds
including restoration, with 0.02974 seconds for the required source checks; the
aborted preliminary replay times were not retained. Manuscript and Lean sources
are unchanged, and the earlier full prepared result remains 902/985.

## Saved-pair reuse checkpoint, 13 November 2026

[Saved trace reuse](saved-trace-reuse.md) checks all 1,240 retained assumptions on
41 exposed clear sources. One equivalence, x27=x5, reduces a 37-variable source
to 36 variables; no common-value pair appears. Five acquired target nodes and
42 new target-recognition probes still leave the residual open, so coverage
remains 45/83. The independent residual UNSAT proof is retained separately and
is not a structural family certificate. All 40 negative pair scans are saved.

The larger opportunity is composition of checked implications: the capped scan
retains 284 candidate binary clauses on 39 sources, including 161 from later
traces on 37 sources. Test graph paths/components and then bounded augmented-CNF
propagation. Four sources reach the 16-clause cap, and initial-profile candidates
may repeat earlier learning. The width-five obstruction and a width-two stalled
source with no such candidates need different treatment. This refines the open
frontier; it does not partition arbitrary SAT into efficiently decidable cells.

## Retained implications with full-CNF lookahead, 13 November 2026

[The retained-implication study](saved-implication-learning.md) rules out a further
pure binary-graph gain on the saved evidence: complete checked reachability finds
only the old equivalence, with no forced literals or contradiction on 41 sources.
Using 284 checked clauses in 39 capped full-CNF follow-ups does strengthen two
sources: a new equivalence on case 32 and a forced value on case 31. Same-variable
controls on the original source remain clear, separating this from ranking changes.

Fifteen acquired nodes leave selected residuals with 27, 39 and 35 variables.
All remain open, so coverage stays 45/83; reference answers are kept separate.
The 27-variable leaf is the most concrete next target and has 17 untried ranked
variables. The 36 clear augmented trials are also retained for a bounded
continuation with explicit learned-clause dependencies. This improves exact
reductions on two examples without establishing a broader tractable SAT class.

## Learned-target continuation checkpoint, 13 November 2026

[Bounded continuation below the learned targets](learned-target-continuation.md)
raises the same development-original coverage from 45/83 to **46/83**. Case 58
is independently proved UNSAT, and all 46 remain covered without growth-exception
routes. Case 32's leaf shrinks from 27 to **23 variables / 97 clauses**, while
case 31 stays at 39 variables / 160 clauses. Both remaining leaves now exhaust
their ranked ordinary probes. The step-cap flag on case 32 occurs after its final
partial clear block; it does not identify unused candidates.

The next discovery opportunity is stronger reuse of the later traces on the
23-variable leaf, followed by a controlled comparison with bounded conditioning.
The other exhausted leaf and the 36 earlier clear augmented formulas remain
secondary targets. The gain demonstrates another exact composed route, not a
new tractable category or a controlled estimate of the marginal value of learned
clauses over equal extra probing. All unsuccessful blocks remain stored.

## Later augmented lookahead checkpoint, 13 November 2026

[Continuing exact learned formulas](frontier-learning-continuation.md) raises
coverage **46/83 -> 47/83**. Case 32's original is independently proved SAT;
its 23-variable residual closes after a later forced block and 17 target states.
All same-variable original-source controls remain clear, separating stronger
propagation from ranking changes. The complete original route also includes
further target recognition. All 47 remain covered without growth exceptions.

Saved pairs and complete binary graphs alone did not reduce either starting
source. The 39-variable source stays open even after its six-clause augmented
formula exhausts single-assumption unit refutation. Raising that same batch cap
alone adds nothing. Retained augmented traces may support another learning layer
with explicit dependencies, or serve as a control for bounded conditioning.
The highest immediate coverage opportunity is applying the new continuation
mechanism to the 36 earlier clear learning records, filtering already-covered
sources. This reuses their existing clauses and initial augmented probes.

Nine later blocks, eight inconclusive, remain persistent with both original-source
exhaustion certificates and the augmented exhaustion certificate. These findings
refine the remaining inference gap without establishing polynomial coverage of
arbitrary CNFs or an independent-workload performance result.

## Retained-learning batch checkpoint, 13 November 2026

[Continuation across the saved bases](retained-learning-batch.md) raises
structural coverage **47/83 -> 52/83**, independently proves all five newly
covered originals SAT, and retains all 52 closures without growth exceptions.
The pass acquires 141 later blocks and 77 recognition states under one shared
admission budget. It neither reacquires source clauses nor repeats initial probes.
Six of ten reduced targets arise with clear same-variable original controls;
four controls also force a value. The experiment therefore separates stronger
propagation from extra lookahead rather than attributing every gain to learning.

The remaining cells now distinguish 18 ready bases, nine exhausted bases, six
covered sources, five acquired open targets and three initially successful bases.
The smallest selected target leaf has ten variables, 51 clauses and one untried
ordinary probe; this is the next coverage target. The 18 ready augmented bases
retain 92 unused ranked variables. Five additional raw queue entries are already
exhausted, so queue size alone overstates remaining discovery opportunities.

All earlier proof rows and reference answers persist. This is a refinement of
the same development cases and of the scheduler's discovery outcomes, not a new
tractable CNF category, independent holdout result or unrestricted-SAT bound.

## Saved-cofactor checkpoint, 13 November 2026

[Splitting from retained unit traces](saved-trace-splitting.md) raises coverage
**52/83 -> 53/83**, independently proves case 2 (`holdout3`, n32, original 894)
SAT, and retains the growth-exception ablation. The ten-variable source has no
single-assumption unit refutation: both polarities of every binary variable are
checked clear, and the other five variables cannot start unit propagation.
Nevertheless, two of those saved clear traces supply exact cofactors whose plans
close after five new recognition states. Both branch premises remain mandatory.

This refines an unresolved inference cell: failed-literal exhaustion does not
make the retained cofactors useless. The split is standard exact conditioning,
with an additional explicit expansion step beyond the old depth policy. Its
source references, unit assignments and both canonical child transports are
checked; missing children cannot supply coverage. The method does not establish
a new polynomial SAT category. Four acquired open targets and the 18 previously ready
learned formulas remain for comparison of cofactor reuse with further lookahead.

Avoided search operations also do not imply lower runtime. The one warm matched
cofactor control is 0.50192 ms with saved traces versus 0.46004 ms fresh. The
negative timing result and the unsuccessful pilot checks remain persistent.

## Matched saved-cofactor acquisition, 13 November 2026

The [isolated split/probe comparison](saved-cofactor-batch.md) freezes four open
leaves and their saved-pair rankings on the same 53/83 parent. With at most 32
state admissions per source, splitting reaches **55/83**, ordinary probing
**54/83**. Case 37 is independently UNSAT; case 77 is SAT. The split arm closes
three of four selected fragments with 30 states in 0.14475 s, plus 0.05791 s
ranking. The control uses seven states in 0.09725 s and reproduces case 37's
closure. Both arms' partial/inconclusive work is retained. This supports selective
conditioning, not a claim that it is always cheaper.

Their immutable union adds 36 distinct pattern nodes, four ordinary windows,
thirteen continuations and four external splits; working SQLite grows 720,896
bytes. No state cap binds. All 585 tests and the full inventory audit pass;
independent cold arm/union replay disables discovery. All 1,175 earlier reference
proof nodes survive in the 1,721-node archive. The comparison pipeline takes
405.18 s, dominated by repeated cold preparation and verification.

The next selected frontier is **27 variables / 101 clauses**, below the true
cofactor of the remaining 33-variable parent. Its sibling is closed. Inspect
`diagnostics.json.gz` → `children`; the old target view does not follow open
external splits. Eighteen ready learned bases retain 92 ranked variables as an
alternative queue. Restore `experiments/results/cnf-split-batch/report.json`
through `compare_cnf_split_batch.restore_checkpoint` and `routes_for`, retaining
all five split records. The earlier loader alone loses this progress. Manuscript
and Lean are unchanged: finite checked coverage does not establish efficient
closure or polynomial construction for unrestricted SAT.

## Continuation below saved splits, 13 November 2026

[The split-frontier continuation](retained-split-frontier.md) replaces the old
33-variable scheduling view with its exact acquired 27-variable descendant,
then reduces that leaf to **22 variables / 90 clauses**. It adds six recognition
states, two windows and five continuations; **six blocks are clear, one forced**.
Coverage remains **55/83**, including the ablation. Navigation costs 0.00688 s and
bounded continuation 0.06866 s; working SQLite grows 176,128 bytes. All 589 tests
pass. The full inventory audit and cold replay preserve prior evidence; all 1,721
earlier reference nodes remain within the 1,750-node extended archive.

The remaining formula has a checked single-assumption unit-refutation obstruction:
38 saved clear traces cover both values of all 19 binary-clause variables; the
other three cannot create an initial unit. No retained pair yields the implemented
common-value/equivalence rewrite. These facts do not decide SAT/UNSAT or rule out
stronger inference. Next compare another source-proved learned batch against
nested cofactor splits, with the 18 ready bases / 92-variable queue as an
alternative. Do not restart ordinary probes on the unchanged exhausted source.

Resume `experiments/results/cnf-split-frontier/report.json` through
`continue_cnf_split_frontier.restore_checkpoint` and `routes_for`, including all
five splits. `diagnostics.json.gz` and `obstruction.json` preserve the exact
22-variable source and its remaining obligations. The frontier follows saved
splits, selected internal plans and ordinary forced routes; it is not a minimal
or exhaustive analysis of every alternative proof plan. Manuscript and Lean
remain unchanged; unrestricted efficient construction and compact closure remain
open.

## Learning versus saved conditioning, 13 November 2026

[The matched learning/split trial](learning-versus-saved-split.md) starts from
the exhausted 22-variable / 90-clause source. A new 16-clause batch has a clear
initial block and five clear later blocks, then exhausts the augmented candidate
pool without a reduction. The complete graph of saved source implications also
provides no forced value, equivalence or contradiction. These are retained
negative results for this precise inference, not barriers to arbitrary methods.

One split ranked from eight saved pairs needs four new recognition states and
reuses its already closed sibling. The selected remaining leaf becomes
**19 variables / 84 clauses**, but original coverage remains **55/83**, including
the ablation. Both cofactors are acquired. Local acquisition is 0.03825 s for
learning and 0.03446 s for splitting, with another 0.02471 s for pair ranking.
The 32-state allowances do not equalize CPU work. Cold preparation, full audit
and preservation scans dominate the 434.32-second pipeline.

The union adds 57,344 working SQLite bytes to 769,617,920 bytes, with 41,710
pattern nodes; all inherited rows remain unchanged. The reference archive
preserves all 1,750 old nodes within 1,775 checked nodes. Source, augmented formula
and both cofactors are independently SAT; reference answers are separate from
structural coverage. The failed first export and all completed proof archives
are preserved. Peak RAM and unrestricted compact closure remain unproved.

Resume `experiments/results/cnf-learning-split/report.json` through
`compare_cnf_learning_split.restore_checkpoint` and
`compare_cnf_split_batch.routes_for`, retaining all **six splits, 42 learned
bases and 155 augmented blocks**. `diagnostics.json.gz` -> `frontier` identifies
the 19-variable leaf and its ten untried ordinary candidates. The 18-base /
92-variable learned queue remains an alternative. Do not repeat the exhausted
source/batch. Dependency-local verification and delta export are high-cost
implementation gaps. Manuscript and Lean are unchanged.

Validation: all **589 tests** pass (88.787 s); full inventory audit and independent
cold replay pass. Cold replay takes 297.82 s with discovery disabled and history
bytes unchanged. On the 106-clause augmented formula, 42 saved clear traces cover
both values of 21 binary variables; variable 12 cannot trigger an initial unit.
This certifies failure of every single-variable unit-refutation attempt after
the new batch, without deciding a broader complexity question.

## Portable probing obstruction, 13 November 2026

[Continuation from the merged checkpoint](retained-split-frontier.md) tests all
ten remaining ordinary candidates on the 19-variable / 84-clause leaf. Three
clear blocks, then exhaustion, add no recognition states and no original closure:
coverage remains **55/83**, including the ablation. Twenty-eight saved clear
traces cover both values of all fourteen binary variables; the other five cannot
start unit propagation. No retained pair supplies the implemented common-value
or equivalence rewrite. This is a checked inference boundary, not SAT/UNSAT or a
lower bound for arbitrary methods.

A new self-contained certificate retains only the exact formula and the required
clear traces. It occupies **6,562 JSON bytes / 1,347 compressed bytes**. Two fresh
processes per mode, with reversed order, check identical proofs in **0.08218 /
0.12492 s** from the compact certificate versus **14.10469 / 14.20055 s** from
history reconstruction. Startup and teardown are included; OS caches are not
flushed. Packing/checking costs 0.00288 s once traces are available; the exporting
diagnostic also pays 14.03 s to restore history. These costs and all old evidence
remain charged. Compact replay verifies only this source's unit-refutation
obstruction, not whole-inventory correctness, ancestry or structural coverage.

The continuation itself costs 0.00870 s; its pipeline totals 271.54 s, including
a 113.33 s inventory audit and 64.40 s cold route reconstruction. The working
database grows 28,672 bytes to **769,646,592 bytes** with 41,710 pattern nodes,
87 windows and 128 ordinary continuations. The reference archive's 1,775 nodes
and bytes are unchanged. All 17 relevant tests, full inventory audit and
154.19 s independent cold replay pass. The parent's 589-test suite remains
preserved; no new full-suite run is claimed. Peak RAM is unmeasured.

Resume `experiments/results/cnf-reuse-frontier/report.json` through
`continue_cnf_reuse_frontier.restore_checkpoint` and `routes_for`, including six
splits, 42 learned bases and 155 augmented blocks. Stop unchanged ordinary probes
on this leaf. Compare source-proved augmentation, verified parent-lemma transport
and another split from its fourteen saved pairs. Elimination and binary-path
steps require explicit transport conditions; a parent's negative certificate
cannot simply be reused on a child. The 18-base / 92-variable queue remains an
alternative. Dependency-local positive-plan validation is the larger cost gap.
The manuscript now explains compact negative-fact replay and its limitations;
Lean sources and unrestricted-SAT claims are unchanged.

## 2026-11-13: parent lemmas survive, but do not bypass the current obstruction

[Parent-lemma transport](parent-lemma-transport.md) now has a portable checker for
source-proved consequences across conditioning, complete elimination, binary
path deletion and exact renaming. On the retained 22-to-19-variable path, eight
of sixteen lemmas survive; seven are absent from the final formula. The leaf's
saved traces already prove those seven plus four more. Both checked augmentations
remain clear under every binary-variable pair; new exhaustion certificates are
bound separately to their 91- and 95-clause formulas. No new structural closure
or recognition state is claimed, and the 55/83 coverage and 769,646,592-byte
history remain unchanged.

The positive transport proof is 2,362 compressed bytes. Compact replay of the
augmentation and obstruction facts takes 0.111--0.162 s; adding reconstruction
and ancestry checking takes 13.85--14.43 s. Export costs 14.05 s and earlier
acquisition remains charged. All 37 relevant tests and two read-only cold ancestry
checks pass. These are narrow fact checks, not a complete coverage-plan audit;
Python is not newly refined by Lean. The manuscript states the transport argument
and the negative coverage result.

The next structural candidate is another saved cofactor of the 19-variable leaf.
A second learning round from the new augmented traces is a distinct untested
alternative; do not infer full clause saturation from this one batch. Preserve
`experiments/results/cnf-lemma-transport/` as sidecar evidence while resuming the
unchanged inventory from `cnf-reuse-frontier/report.json` with all six splits,
42 learned bases and 155 augmented blocks. The other 18-base / 92-variable queue
and full dependency-local coverage verification remain open.

## 2026-11-13: saved conditioning closes the 19-variable leaf and one original

[The saved-cofactor checkpoint](saved-cofactor-closure.md) ranks all fourteen
retained pairs and selects variable 15. Its 11/36 and 17/71 cofactors both close
with eighteen new recognition states, under a shared 32-state allowance. This
completes the retained decomposition of development case 71 (original 1441,
48 variables / 204 clauses), raising coverage **55/83 -> 56/83**, also without
growth exceptions. The seven saved split sources and eleven acquired learned
targets now have no remaining open or pending obligations. Independent reference
proofs confirm SAT and verify both lifts; structural closure checks both branches.

The expansion costs 0.05914 s after 0.04395 s ranking, while the complete pipeline
costs 271.74 s and includes a 110.36 s inventory audit. Working SQLite grows
200,704 bytes to 769,847,296 bytes / 41,728 pattern nodes; the delta is 9,471
compressed bytes. All old rows survive unchanged. The reference archive preserves
all 1,775 earlier nodes within 1,869 nodes. Fourteen relevant tests, full inventory
audit and 163.74 s independent cold selection/coverage/reference replay pass.
These are adaptive development results, not a general runtime or coverage bound.

The cold snapshot maps 27 open originals to 29 distinct selected leaves, with no
exact leaf shared between originals. All eighteen ready learning bases (92 ranked
variables left) occur on those paths. A concrete next pair of candidates is the
20-variable / 80-clause exhausted leaf of case 73 for saved conditioning, versus
four unfinished augmented probes on the 29-variable / 120-clause leaf of case 30.
The 11-variable encoding-cap example has a previously established width-five
no-trigger obstruction; use different structure or explicitly deeper conditioning.
The previous split scheduler has completed its selected frontier and should not
be blindly rerun. Resume the new report through
`continue_cnf_saved_splits.restore_checkpoint`, preserving seven splits, 42 bases,
155 augmented blocks and all earlier sidecars. Lean and the older full-corpus
study are unchanged. Full dependency-local positive-plan verification is still
the dominant cost opportunity.

The encoding-cap source also exposes a concrete broader family to implement next:
the existing affine checker confirms two consistent equations and **one** leftover
eleven-literal clause (`encoding-cap-affine.json`). A particular affine solution
and nullspace basis determine whether any literal of that clause is compatible;
one compatible literal gives a model, while all forced-false literals give a
refutation. This ordinary linear-algebra argument avoids direct CNF expansion of
the affine relation. The new family checker and its integration are not yet
implemented; no additional coverage is claimed. Multiple interacting leftover
clauses retain the general SAT difficulty. Prioritize this exact structural
opportunity alongside the bounded cofactor/learning alternatives above.


## 2026-11-13: affine/one-clause family and the remaining non-affine frontier

The [checked affine/one-clause rule](affine-one-clause.md) raises structural
coverage **56/83 -> 57/83**, also without growth exceptions. It reuses triangular
rows to construct a particular solution and complete nullspace basis, checks the
full source partition and every vector, and either supplies a full CNF model or
proves that the sole remaining clause is forced false. More than one leftover
clause is outside this rule, not an UNSAT result. No new Lean refinement or
unrestricted-SAT bound is claimed.

All 29 selected open leaves were checked. The sole gain is case 0's encoding-cap
residual (11 variables / 49 clauses), closing its 14-variable / 132-clause original.
All **28 remaining selected leaves have zero directly extracted parity equations**.
This excludes a direct opportunity for the same rule on their current encodings,
not hidden affine structure. The next discovery target is the 20-variable /
80-clause exhausted leaf of case 73, compared with the four unfinished learned
candidates on case 30's 29-variable / 120-clause leaf. Do not repeat the unchanged
affine scan or the completed earlier split scheduler.

The selected-leaf pass costs 0.00599 s; the full pipeline costs 82.32152 s,
including 14.80944 s restoration and 64.60772 s preparation. The new family proof
is 1,056 compressed bytes; historical SQLite stays byte-identical at 769,847,296
bytes / 41,728 pattern nodes. All 1,869 reference nodes are preserved within 1,883.
Matched generated cases show 1.11--1.24x local exact-source reuse speedups, with
normalization and checks charged; a full nullspace representation can still use
quadratic bits. Complete positive-plan checking from actual dependencies remains
the largest measured runtime opportunity.

Twenty-one targeted tests and independent cold selection/coverage/reference
replay validate this step. The new cold check covers reachable inventory
obligations, not a new full scan of unrelated unchanged rows; the parent audit is
retained. Two diagnostic JSON key-comparison failures and their correction are
preserved. The old full-suite and 902/985 corpus results are unchanged.

Resume `experiments/results/cnf-affine-clause/report.json` through
`continue_cnf_affine_clause.restore_checkpoint` **and its `routes_for`**, preserving
all **five evidence lists**: rewrites, 42 learned bases, 155 augmented blocks,
seven splits and the new affine family record. Earlier lemma sidecars remain
separate and preserved. Using an older four-list route loader would lose the
newly checked closure.


## 2026-11-13: resume an original through its retained cofactor pair

The [original-frontier split](original-frontier-split.md) selects case 73's
20-variable / 80-clause / 285-literal leaf using support/literal order, ranks all
fourteen saved pairs and chooses variable 18. Ten new recognition states close
the true branch and reduce the false branch to **13 variables / 62 clauses /
219 literals** through binary-path deletion and five eliminations. Independent
reference proofs establish SAT of the source and both cofactors and verify
model lifting. Structural coverage stays **57/83**, also without growth exceptions;
the remaining leaf still needs a recognized decomposition.

That leaf has no directly extracted parity equation. Its already saved probes
cover variables **6, 9, 12 and 13**, while ordinary candidates **1, 4, 7 and 8**
remain untried. Test this single four-variable block before another conditioning
layer. Preserve a clear outcome if obtained, then compare newly available pairs
or source-proved augmentation. The older 18-base / 92-variable learned queue
remains available. Use the external split frontier to avoid restarting the
exhausted 20-variable parent; selected original routes expose a different view.

Local acquisition costs 0.04525 s, but the full pipeline costs 267.75550 s,
including 65.86672 s preparation, 107.92519 s full audit and 63.93178 s cold routes.
The two-trace matched control is one tiny resident sample and establishes no
robust timing advantage. SQLite adds 126,976 bytes to **769,974,272 bytes /
41,738 pattern nodes**. The immutable delta is 8,671 compressed bytes; sidecars
are additional. All earlier rows and 1,883 reference nodes remain preserved
(1,898 reference nodes now). A smaller live residual does not shrink the archive
or establish a polynomial expansion bound.

Twenty-seven targeted tests, full inventory audit and **164.80960 s** independent
cold replay pass, including source selection, both branch obligations, all five
evidence lists, baseline monotonicity, growth ablation, model lifting, immutable
preservation and no new discovery. The old full-suite and Lean results are
unchanged. The manuscript records this local structural progress and its costs.

Resume `experiments/results/cnf-original-split/report.json` through
`continue_cnf_original_splits.restore_checkpoint` and `routes_for`, keeping all
**five evidence lists**: rewrites, 42 learned bases, 155 augmented blocks,
**eight splits and one affine family record**. Earlier lemma sidecars remain
separate and intact. `frontier-profiles.json.gz` records the precise smaller
source and next variables; `open-originals.json.gz` retains the original/queue
mapping. Dependency-local verification of complete positive plans remains the
largest measured runtime opportunity alongside discovery of smaller residuals.

## 2026-11-13: forced continuation reduces the open split leaf to ten variables

The [probe continuation](original-frontier-probe.md) follows case 73's saved
split and tests the next four-variable candidate block on its 13-variable leaf.
The first attempt refutes variable 1 = false. Restricting the forced opposite
literal, two eliminations and binary-path deletion leave **10 variables /
44 clauses / 151 literals**, down from 13 / 62 / 219. Four new recognition states
suffice. Coverage stays **57/83**, also without growth exceptions; one acquired
structural leaf remains open and no child is pending.

That leaf has zero directly extracted parity equations and saved ordinary pairs
for **10, 3, 5 and 6**. The next ordinary candidate is **7**. Test it before another
split; if clear, retain the result and rank the saved cofactor pairs. Variables
are local to each normalized residual. Do not repeat the obsolete source's
remaining probes or use the original-frontier view to restart its larger parent.
The 18-base / 92-variable alternative learning queue remains retained.

Local acquisition costs **0.02000 s**, but the pipeline costs **282.11723 s**:
preparation 69.25253 s, full audit 115.65564 s and cold routes 65.40336 s dominate.
SQLite grows **57,344 bytes** to **770,031,616 bytes / 41,742 pattern nodes**;
the delta is **6,225 compressed bytes** plus sidecars. All old rows and 1,898
reference nodes remain preserved (1,906 reference nodes now). No global runtime
speedup, peak-RAM reduction, holdout gain or arbitrary-SAT bound is established.
Dependency-local verification of complete positive plans remains the largest
measured runtime opportunity.

Resume `experiments/results/cnf-original-probe/report.json` through
`continue_cnf_original_probes.restore_checkpoint` and `routes_for`, keeping all
**five evidence lists**: one rewrite, 42 learned bases, 155 augmented blocks,
eight splits and one affine family record, plus earlier lemma sidecars.
Twenty-nine targeted tests, the full inventory audit and **164.19006 s**
independent cold replay pass, with zero new discovery and unchanged reconstructed
bytes. Details are recorded in this checkpoint's `validation.json`.
The preliminary probe and corrected validator import failure are both retained.

## 2026-11-13: a completed probe pool and saved split close case 73

The [probe-and-split continuation](exhausted-probe-split.md) raises coverage
**57/83 -> 58/83**, also without growth-exception routes. The last ordinary
variable 7 is clear in both polarities. Ten saved traces cover all five binary
variables; the other five cannot start unit propagation. The source-bound
exhaustion certificate is not a SAT verdict. Ranking all five pairs selects
variable 10, with score **[1, 1, 9, 96, 10]**: its true branch reuses the empty-CNF
terminal, and seven new states close its nine-variable false branch through
probing, two eliminations, two binary-path reductions and a polarity change to
Horn form. Both plans complete the 48-variable / 204-clause original case 73.

All **nine saved splits** now have closed sources, with no open descendant or
pending child. The selected original queue retains **27 leaves across 25
originals**. Its smallest is **case 30, 29 variables / 120 clauses / 362 literals**,
with ordinary candidates **7, 10, 16, 18, 20, 21, 23, 28, 29** still available.
Compare the first four with the saved pair ranks and learned-clause route.
The selected pair in this run was already available before the new probe;
exhaustion is not a prerequisite for a split. The empty branch already witnesses
SAT, whereas acquiring both branches serves complete structural coverage. The alternative queue retains 18 bases / 92 candidates, including the
previous four augmented candidates on case 30. Use the original-input frontier
now; the current experiment intentionally requires an open split descendant.

Ordinary acquisition costs **0.00181 s**, exhaustion checking **0.00620 s**, pair
selection **0.04998 s** and cofactor acquisition **0.01667 s**. The full pipeline
costs **270.70538 s**, including 66.55717 s preparation, 108.42947 s full audit
and 64.45513 s cold routes. Saved two-trace replay is slower in the tiny matched
sample (0.000430 versus 0.000349 s fresh); no robust runtime comparison follows.
SQLite grows **90,112 bytes** to **770,121,728 bytes / 41,749 nodes**. The delta
is **5,411 compressed bytes**, plus sidecars. All prior rows and 1,906 reference
nodes survive (1,940 reference nodes now). Reference proofs independently establish
SAT and check model lifts. No new general tractability or minimum-cost claim is made.

Resume `experiments/results/cnf-probe-split/report.json` through
`continue_cnf_probe_split.restore_checkpoint` and `routes_for`, retaining all
five evidence lists: one rewrite, 42 learned bases, 155 augmented blocks,
**nine splits and one affine family record**, plus earlier lemma sidecars.
Thirty-eight targeted tests, the full inventory audit and **167.82586 s**
independent cold validation pass. Cold validation stages only the checked clear
window before replaying the original selection, then checks the complete child
checkpoint without fresh discovery;
its results and next-source mapping are retained in this checkpoint. Complete-plan
verification from actual dependencies remains the largest measured runtime gap.

## 2026-11-13: compare bounded lookahead before expanding another original

[The frontier-option comparison](frontier-option-comparison.md) retains a clear
ordinary continuation on case 30's 29-variable residual and exhausts its existing
augmented base with one further clear block. These results do not decide SAT or
exclude stronger inference. All twenty saved pairs are ranked before acquiring
children. Variable 24 was already preferred among the original sixteen pairs:
its false branch is the shared empty terminal; three new states reduce the true
branch from 28 variables / 114 clauses to **27 / 111**, via elimination and
binary-path deletion. Coverage remains **58/83**, including the growth ablation.
The empty branch witnesses SAT for the residual, separately from complete-plan
coverage. Literal count briefly grows during elimination.

Resume `experiments/results/cnf-frontier-comparison/report.json` with
`continue_cnf_frontier_comparison.restore_checkpoint` and `routes_for`, keeping
all five lists: 1 rewrite, 42 bases, **156 augmented blocks**, **10 splits**, 1
affine family, plus earlier sidecars. All prior rows and 1,940 reference nodes
survive (1,949 now). Forty-one targeted tests and the full audit pass; the cold
validator separately checks ranking using only staged clear evidence, then
checks the acquired delta, composition and reference models without discovery.
Independent cold replay passes in **176.26154 s**; its result is retained in
`validation.json`.

Acquisition takes **0.02748 s**; the pipeline takes **270.71536 s** and preflights
add **82.05829 s**. Independent validation is extra. SQLite grows **57,344 bytes**
to **770,179,072 bytes / 41,752 nodes**, with a **5,746-byte compressed delta**,
a 307-byte compressed learned block and other sidecars/reference data. Full
history preparation/checking dominates. The single matched trace sample is not
a robust or whole-solver runtime comparison; no peak-RAM or arbitrary-SAT bound
is established.

Next compare the new leaf's saved pairs **11, 5, 8, 15** with ordinary candidates
**19, 24, 9, 13**. Use the acquired split descendant, not the older source; its
exact key is in `frontier-profiles.json.gz`. It has 19 remaining ordinary
candidates and zero directly extracted affine rows. The wider queue now has
**17 ready learned bases / 88 candidates**. Do not repeat the exhausted older
learned base. Dependency-local complete-plan verification remains the principal
measured runtime gap.

## 2026-11-13: a failed literal avoids acquiring two new cofactor plans

[Forced continuation on case 30](frontier-forcing.md) reduces the open leaf from
**27 variables / 111 clauses / 342 literals** to **25 / 99 / 304**. The four saved
pairs all require two missing children. In the next ordinary block, variable 19
is clear and assuming normalized variable 24 false gives 21 unit reasons and a
contradiction. Its true restriction is acquired; binary-path deletion and one
elimination add three inventory states including the new unresolved terminal.
The proposed block stops before testing variables 9 or 13. Elimination increases
clauses and literals relative to its immediate input. Coverage stays **58/83**;
no new original or tractable family is closed, and a global minimum-cost claim
is not supported by comparing pair ranks alone.

The pipeline takes **277.21655 s**, including **0.02582 s** acquisition, 67.09237 s
preparation, 108.74312 s full audit and 67.28829 s cold routes. The direct preview
adds 0.00116 s of kernel work. SQLite grows **57,344 bytes** to **770,236,416 bytes /
41,755 nodes**; the compressed delta is **6,081 bytes**, with other artifacts
additional. All previous rows and 1,949 reference nodes survive (1,977 now).
The targeted 33-test suite, full audit and **174.55350 s** independent cold replay
validate the checkpoint; `validation.json` retains the separate replay checks.

Resume `experiments/results/cnf-frontier-forcing/report.json` through
`continue_cnf_frontier_forcing.restore_checkpoint` and `routes_for`, retaining
all five evidence lists (**1, 42, 156, 10, 1**) and earlier lemma sidecars. Use the
new split-frontier leaf, not its successful forced parent. Compare saved pairs
**5, 6, 8, 11** with the next ordinary block **13, 15, 7, 9**. There are 17 ordinary
candidates left at the new source, zero directly extracted affine equations,
and 17 ready learned bases / 88 candidates elsewhere. The next experiment should
batch bounded local continuation under one shared state allowance and compare
its evidence with the corresponding sequential prefix; a full reconstruction
and audit per window dominates local discovery. Dependency-local complete-plan
checking, measured batch savings and unrestricted resource guarantees remain open.


## 2026-11-13: batch ordinary continuation with a matched preparation control

[The bounded batch](frontier-batching.md) retains five clear probe blocks across
17 remaining ordinary candidates of case 30's 25-variable / 99-clause leaf.
A sixth advance detects exhaustion; no recognition state is admitted. All six
prefixes, final logical tables and coverage agree with a control that rebuilds
checked routes between advances while preserving the inventory cache, search
queue and common 32-state allowance. Coverage remains **58/83** and 21 saved
pairs can now support subsequent conditioning or common-consequence reuse.

Instrumented search is **0.31960 s** versus **5.46878 s**, including six snapshots
in each arm. Five avoidable route preparations cost **5.14561 s**. Initial
preparation is **65.62419 / 70.54924 s**; its single-run variation is not a batching
benefit. The pipeline, including both arms, takes **358.12190 s**. Full audit
(**111.99494 s**) and cold routes (**66.03018 s**) remain dominant. This is a
measured preparation saving on reused development data, not a general SAT-solver
speedup or an efficient complete partition.

SQLite grows **53,248 bytes** to **770,289,664 bytes** without adding pattern nodes
(41,755 total); one window and four continuation rows yield a **2,990-byte**
compressed delta. All previous results and the 1,977-node reference snapshot
survive. The targeted 37-test suite, full audit and independent replay validate
this checkpoint; detailed results and limitations are in the linked note.

Resume `experiments/results/cnf-frontier-batch/report.json` using
`continue_cnf_frontier_batch.restore_checkpoint` and `routes_for`; all five lists
(**1, 42, 156, 10, 1**) and earlier sidecars remain required. Use the retained
pair/rewrite diagnostics for the next expansion, rather than rerunning this
exhausted ordinary pool. The alternative learning queue has 17 bases / 88
candidates. Dependency-local complete-plan verification remains the major cost
gap, while finding a smaller certified decomposition remains the coverage gap.

The checked next-option ranking selects **variable 7**: its true cofactor is the
shared empty terminal, and its false cofactor (**24 variables / 94 clauses /
287 literals**) needs acquisition. This pair was available in the first new
window; requiring pool exhaustion would do avoidable discovery. No common-value
or equivalence rewrite is found among the 21 pairs. The four nonbinary variables
(2, 4, 12, 21) have unit-free restrictions, so single-assumption unit propagation
cannot start on them. Independent replay passes in **169.35837 s**. The retained
positive witness has **593 explicit steps**; measure its full dependency closure
before claiming a selective verification bound.


## 2026-11-13: acquire the missing branch of a retained pair

[The reused variable-7 split](reused-branch-expansion.md) shares the existing
empty true cofactor and acquires the false cofactor with three new recognition
states. Binary-path deletion and elimination reduce case 30's open leaf from
**25 variables / 99 clauses / 304 literals** to **23 / 93 / 288**. The intermediate
24-variable formula has 92 clauses and 281 literals, so elimination's support
reduction increases both other measures. Coverage remains **58/83**, also without
growth exceptions; no child is pending. Both cofactors are independently SAT,
with checked model transport. The unclosed structural plan is not an unknown
SAT verdict or a new tractability theorem.

Acquisition takes **0.02474 s** in a **271.17740 s** pipeline. Preparation costs
65.75065 s, full audit 106.37684 s and cold routes 63.97337 s. Reusing the chosen
pair avoids reacquiring its two propagation traces, but new child recognition
still reports 36 probe attempts. SQLite adds **49,152 bytes** to **770,338,816
bytes / 41,758 nodes**; immutable delta **4,841 compressed bytes**, with split and
other sidecars additional. All previous rows and 1,977 reference nodes survive;
the reference now has 1,998 nodes. The 37-test suite, full audit and independent
cold replay validate preservation and correctness.

Resume `experiments/results/cnf-reused-branch/report.json` with
`continue_cnf_reused_branch.restore_checkpoint` and `routes_for`, keeping all five
lists **(1, 42, 156, 11, 1)** and earlier sidecars. Compare the new leaf's saved
pairs with ordinary candidates **7, 9, 16, 17** before choosing the next bounded
step. Follow retained external splits; do not restart the exhausted parent.
Dependency-local checking of complete positive plans remains the dominant cost
opportunity; the retained 593-step witness still has unmeasured inherited
checking dependencies.

Cold replay passes in **171.36780 s**. The new leaf has saved pairs **5, 6, 11,
13**, each requiring two missing children; the best rank is **[2, 2, 20, 376, 5]**.
There is no common-value/equivalence rewrite among them and no directly extracted
affine equation. The wider queue retains **17 learned bases / 88 candidates**.
The exact source SHA-256 is
`a38c8326bbc493edae23be08aa73a85b288d74cf5a80dde578d126891e21ae92`.


## 2026-11-14: replay only the external dependencies of a positive proof

[Selected-route verification](selected-route-verification.md) replays the same
593-step certificate for 58/83 roots with the existing validators, loading only
selected external records and their required prefixes. In two cold repetitions
with reversed order, mean replay falls **35.72304 -> 30.35446 seconds (15.03%)**.
Both arms start with fresh verifier caches and check the same positive claim.
The comparator reconstructs all external routes; it is not a full archive audit
or the previous complete expansion pipeline.

Corrected to include the retained-policy verifier cache, the checking closure
falls **13,211 -> 11,955 pattern nodes**, and node JSON payload falls
**109,165,321 -> 97,225,536 bytes**. The original report counted only the current
view; timing samples already included both. Neither payload is a peak-RAM
measurement. Crucially, the selected replay still checks **11,362 nodes beyond
its 593 explicit steps**. Internal profiles, stored alternatives and summaries
remain recursively checked. Measure their successful semantic dependencies
before attempting a standalone positive checker; a short outer witness does
not establish cheap or compact complete checking.

All archive bytes and prior results remain unchanged; coverage remains 58/83.
This positive-only subset is not a complete discovery catalog, and omitted
routes prove no exclusion or UNSAT claim. The new six-test module checks lazy
prefix dependencies and tampering; matched cold replay disables fresh discovery.
The older expansion runners remain unchanged, so no full-pipeline reduction is
claimed. Resume the **23-variable / 93-clause** frontier from
`cnf-reused-branch/report.json`, preserving all five evidence lists **(1, 42,
156, 11, 1)**. Saved pairs **5, 6, 11, 13** and ordinary candidates **7, 9, 16,
17** remain the next discovery options. Detailed scope and reproduction commands
are in the linked note and `cnf-selected-routes/report.json`.


## 2026-11-14: expose retained proof steps and correct dependency totals

[Expanded positive coverage](expanded-coverage-dependencies.md) replaces the old
proof's implicit bases with explicit internal plans and exact retained-policy
references. The same 58 roots now have **2,748 ordered steps**, exposing **2,155**
hidden steps. Both conditioning branches, shared component occurrences and all
selected external rules survive. Independent cold replay passes with fresh
discovery disabled; the 57-test suite covers missing or forged dependencies.

The accounting audit found a separate prepared-policy cache omitted from the
previous dependency summary. Selected replay actually checks **11,955 nodes /
97,225,536 node JSON bytes**, including **1,697 prepared nodes / 8,610,646 bytes**.
Full-route replay checks **13,211 nodes / 109,165,321 bytes**. Timing samples had
included this work, so the prior 15.03% mean replay saving remains unchanged.
Historical reports are preserved; the new report records their corrected totals.

**9,207 checked nodes / 78,657,022 node JSON bytes** are outside the expanded
positive graph. They include primitive/external dependencies as well as history
and losing alternatives; they are not all proved removable. The next checker
must establish sufficient primitive premises before pruning them. Expansion
costs **0.26315 s** after checking; the graph is **777,176 compressed bytes** and
still depends on the full history. Cold expanded replay costs **34.50104 s**
versus **30.51477 s** for the old selected witness in this run, so this step makes
proof obligations explicit without an achieved runtime reduction.

Coverage, SQLite, every previous result and the 23-variable / 93-clause discovery
frontier are unchanged. Resume `cnf-reused-branch/report.json`, retaining all five
evidence lists **(1, 42, 156, 11, 1)**. The new report is a verification study,
not a new reconstructible discovery checkpoint or an unrestricted-SAT result.


## 2026-11-14: validate selected semantic steps without historical search replay

[Hybrid primitive replay](positive-primitive-replay.md) validates the unchanged
2,748-step graph for the same 58/83 roots. It handles 2,687 internal steps directly;
five subsumption steps and 56 external routes retain the original validators.
Exact CNF/configuration/depth bindings, complete resolvents, source-bound probe
reasons, retained references, component multiplicity and both conditioning
children remain required. Positive results never enter historical validation
caches: they do not certify search ranking, failed recognizers or losing plans.

Two matched cold repetitions in reversed order reduce mean replay from
**30.15238 to 2.71821 seconds (90.99%)**. Full historical checking falls
**11,955 -> 471 nodes**, including both policy views; distinct inventory rows
read fall **11,955 -> 2,797**. The old caches retain 97,225,536 node JSON bytes;
the hybrid's historical caches retain 3,096,763 bytes, with a further 18,568,514
bytes read directly for graph steps. These are logical payloads, not peak RAM.
The 56 external routes and their 25 ordinary/26 learned prefixes remain checked.

The warm regression is preserved: **0.25349 -> 1.88878 seconds** on average,
because direct transformations are revalidated rather than cached. Restoring
history and sidecars takes **20.91624 seconds**, now the larger preparation cost.
A sufficient selected-proof bundle plus explicit open-frontier dependencies is
the next integration target; a partial catalog cannot prove exhaustion. Older
expansion runners and complete archive audits are unchanged.

All **132 relevant tests** pass, including 512 two-variable clause subsets and
504 applicable normalized eliminations checked against exhaustive semantics,
changed bindings/reasons, missing resolvents and branches, retained references,
fused closures, projections and external evidence. The matched run disables
fresh recognition/discovery and confirms byte-identical SQLite and logical table
digests. The archive remains **770,338,816 bytes / 41,758 nodes**, all previous
results survive, and no new SAT family, Lean refinement or general polynomial
bound is asserted.

Resume discovery from `cnf-reused-branch/report.json` with all five lists
**(1, 42, 156, 11, 1)**. The 23-variable / 93-clause leaf, saved pairs **5, 6, 11,
13**, next ordinary candidates **7, 9, 16, 17**, and 17 learned bases / 88
candidates are unchanged. The new `cnf-positive-primitives/report.json` is a
verification study, not a discovery checkpoint.


## 2026-11-14: standalone data for positive proof replay

[The positive data bundle](positive-proof-bundle.md) captures exact SQL reads
from fresh checking caches, retains all five evidence lists, and binds the
ordered proof to separately supplied source/configuration claims. It includes
**2,797 pattern rows and 82 external-record rows**. Consumers build a new
read-only temporary database and rerun semantic checking; missing premises,
unused SQL rows, duplicate identities, changed claims and invalid scope fail.
No file digest or saved closure flag replaces the proof checks.

Independent processes outside the repository's working directory replay the
same **58/83 roots / 2,748 steps**, with lineage restoration disabled. Two
matched repetitions in reversed order reduce mean complete cold process time
**23.95282 -> 3.03614 seconds (87.32%)**. Semantic replay remains about 2.7 s;
the gain comes from preparation. The artifact is **3,169,051 compressed bytes**
and rebuilds **40,538,112 bytes** of temporary SQLite instead of 770,338,816.
The original archive is unchanged, so this adds persistent storage while reducing
cold working data. No peak-RAM reduction is claimed.

Production still pays **20.82422 s restoration, 2.78123 s capture, and 1.53465 s
serialization/compression**, plus integrity and diagnostic work. The complete
study, including producer and four consumers/controls, takes **80.64054 s**.
All **139 relevant tests** pass and the preceding artifacts remain unchanged.
The earlier warm-replay regression is not addressed by this data packaging.

This is positive-only data, not a discovery checkpoint or complete catalog.
Next establish source-local frontier dependencies and explicit completeness and
admission contracts: a row absent from the bundle is not necessarily a new state
or evidence of exhaustion. Keep full history authoritative and preserve all new
deltas. Resume discovery from `cnf-reused-branch/report.json`, retaining evidence
counts **(1, 42, 156, 11, 1)**. The 23-variable / 93-clause source, saved pairs
**5, 6, 11, 13**, next ordinary candidates **7, 9, 16, 17**, and wider 17-base /
88-candidate queue are unchanged. No new family, SAT verdict, Lean refinement or
unrestricted polynomial bound is established.


## 2026-11-14: source-local ordinary expansion and exact historical membership

[The source-local path](source-local-expansion.md) now advances the open
23-variable / 93-clause source without preparing a complete route catalog or
copying all history. Each local miss consults a pinned, read-only authoritative
snapshot; old nodes and saved prefixes pass their original validators, and every
insert checks authoritative membership. New-row metadata separates imported
premises from novel records. The partial maps cannot enumerate global routes.
A missing local row therefore never establishes novelty or stream exhaustion.

The matched single-block workers produce identical records, discovery counts
and byte-identical deltas. Mean complete worker process time falls **10.99932 ->
0.12683 s (98.85%)**, including preparation and delta export. Working SQLite
falls from **770,347,008 to 94,208 bytes**, but the separate full authority is still
required. First restoration costs **20.59393 s**; merge costs **0.10878 s** and
cold delta checking **0.06109 s**, outside that worker comparison. Probing itself
is slightly slower. The full four-worker study takes **45.50471 s**. Two reversed
samples share OS caches; this is no peak-RAM or complete SAT-solver speed claim.

The saved window checks both assumptions for **7, 9, 16, 17** and is clear. It
adds one record, no pattern nodes and no closure edge; coverage stays **58/83**.
History becomes **770,347,008 bytes / 41,758 pattern nodes**. Its **2,025-byte
compressed delta** merges idempotently and cold-checks, with all parent bytes
preserved. All **146 relevant tests** pass, including omitted-state reuse,
checked prefix restart, bounded exhaustion, forced pending work, shared admission,
rollback, changed identities and corrupt deltas. No new Lean refinement or
unrestricted complexity result is claimed.

Resume through `continue_cnf_source_local.restore_checkpoint` from
`experiments/results/cnf-source-local-checked/report.json`, retaining the five
lists **(1, 42, 156, 11, 1)**. The preliminary `cnf-source-local/` run is preserved
with an invalid-metadata note and is not a checkpoint. Next ordinary candidates
are **18, 21, 22, 23**, compared with saved split pairs **5, 6, 11, 13** under one
allowance. The learned queue remains 17 bases / 88 candidates. Source-local split
and learned dependencies, global selection and amortizing restoration remain
open; the ordinary-stream API does not provide their completeness contracts.


## 2026-11-14: source-local forced reduction and global recomposition gap

[Forced source-local expansion](source-local-forcing.md) advances the saved clear
prefix and proves **source variable 22=true**. The block checks both assumptions
for 18 and 21, then derives a conflict under 22=false. Fourteen unit reasons and
the conflict are checked. The exact target shrinks **23 variables / 93 clauses /
288 literals -> 22 / 88 / 272**, with one admitted unresolved node and no pending
acquisition. Coverage remains **58/83**, and the 2,748-step positive proof replays.
Reference solving confirms source and target SAT, with a checked lifted model;
all 1,998 former reference nodes survive among 2,012 verified nodes.

Eager and source-local workers produce identical records, ordinary probe counts,
admitted identities and byte-identical deltas. Two reversed fresh-process trials
reduce mean one-block process time **10.03384 -> 0.13717 s (98.63%)**, including
preparation and export with an available authority. Actual advance/recognition
is slightly slower. Local SQLite is **126,976 bytes**, but still depends on full
history. Initial reconstruction costs **21.99791 s**; global preparation costs
**6.47823 s**, and global composition/checking costs **55.48722 s**. The full
four-worker study takes **115.19078 s**, excluding the unmeasured exploratory
propagation used for adaptive selection. This is no complete SAT-solver or
peak-RAM claim. Global checking caches hold 22,603 nodes / 191,717,696 node-JSON
bytes, exposing the next maintenance cost.

The **4,447-byte compressed delta** adds one continuation and one pattern node.
Full history grows by **24,576 bytes** to **770,371,584 bytes / 41,759 nodes**;
parent records are unchanged and merge is idempotent. All **148 relevant tests**
pass. A fresh full checkpoint reconstruction checks the new records, table digests
and positive proof. No new Lean refinement, tractable category or unrestricted
construction bound is claimed.

Resume via `continue_cnf_local_forcing.restore_checkpoint` from
`experiments/results/cnf-local-forcing/report.json`, retaining all five lists
**(1, 42, 156, 11, 1)**. The new leaf has SHA-256
`545c51d457452dc1fd3dec970e5eadc1f85ba4012c889be2164277966968bf29`.
Next ordinary candidates are **16, 18, 21, 22**, in new canonical coordinates
(new 22 is old 23); saved split pairs rank **13, 5, 6, 11**. The learned queue
remains 17 ready bases / 88 candidates. Next investigate those discoveries and
exact incremental coverage maintenance with a complete reverse-dependency index;
partial catalogs or stale negative caches must not substitute for that contract.


## 2026-11-14: incremental finite coverage and the cold-cost boundary

[The complete coverage index](incremental-coverage.md) updates the affected
reachable rules after the saved forced append. Across full and without-growth
controls, four source-option checks replace 25,605 source visits. Warm composition
and original proof checking average **0.26146 -> 0.03949 seconds**; including the
shared **0.94030-second** complete external-route refresh gives an indicated
**18.47%** saving. The two full-control times vary substantially. Most of the old
55-second cold cost is historical semantic validation, already avoided by warm
verifier caches; do not attribute all of that difference to incremental closure.

The new index preserves both split obligations and duplicate premises, propagates
changed negative coverage results, and handles existing pending routes that become
available after target admission. It requires immutable historical pattern rows,
a fixed policy and a complete checked external catalog. Removed or rebound rules
require rebuilding. Cold loading recomputes closure and audits every reachable
option, rather than trusting persisted negative flags.

First index construction costs **55.68532 s**. Cold index replay is **64.41089 s**
versus **62.62709 s** for full recomposition: a retained regression. Both validate
22,603 historical nodes. Full snapshot serialization costs **7.96452 s** and adds
**11,241,021 compressed bytes / 94,113,609 raw JSON bytes** for two graphs, with
most source keys duplicated. No peak-RAM reduction is established. All **156
relevant tests** pass, including exhaustive graph/base combinations and real
pending-target activation; independent cold replay and full composition agree.

No new recognition state or structural coverage is acquired by this maintenance
study: coverage remains **58/83**, full history **770,371,584 bytes**, and the active
leaf **22 variables / 88 clauses**. The new index artifact is in
`experiments/results/cnf-incremental-coverage/`; discovery still resumes from
`experiments/results/cnf-local-forcing/report.json` through
`continue_cnf_local_forcing.restore_checkpoint`, preserving all five evidence lists
**(1, 42, 156, 11, 1)**. Next advance ordinary candidates **16, 18, 21, 22** or saved
split pairs **13, 5, 6, 11** in a bounded warm session with one admission allowance.
Complete route refresh, cold catalog revalidation and full-snapshot persistence
remain costs. Use the reusable graph for actual discovery before another isolated
verification optimization; no unrestricted construction claim follows.


## 2026-11-14: warm discovery batch reaches another original through 2-CNF

[The eight-step discovery batch](warm-expansion-batch.md) raises structural
coverage **58/83 -> 59/83**, closing original case **1189**, a 48-variable /
204-clause development input. A forced value on the 22-variable source exposes
five binary-implication path deletions and six eliminations, reaching a
15-variable / 55-clause leaf. Its remaining ordinary probes are clear; a saved
split on local variable 4 closes both cofactors through 2-CNF terminals. Both
branches independently check SAT. Closure propagates through 65 sources per
coverage graph, reusing retained ancestors. This is one observed interaction of
existing transformations, not a new unrestricted tractability guarantee.

The session consumes **21/32 state admissions** without resetting between eight
steps or between the two split branches. It retains **21 new pattern records,
two windows, five continuations and one split sidecar**. The database delta is
**15,484 compressed bytes**; full history grows by **335,872 bytes** to
**770,707,456 bytes / 41,780 pattern nodes**. All previous rows remain, and merge
is idempotent. The reference archive preserves all 2,012 old nodes and checks
2,041; the expanded positive proof now has 2,828 steps. All **160 relevant tests**
and fresh checkpoint reconstruction pass.

Actual acquisition costs **0.11884 s**, eight full route refreshes **7.59057 s**,
and warm composition/checking **1.30709 s full / 0.30604 s incremental**. Including
selection, acquisition and refresh gives an indicated **11.00%** saving, with
substantial first-control timing variation. Initial reconstruction, preparation
and complete catalog audit cost **91.13181 s**; the whole study costs 122.01047 s.
Saved split-trace replay is slower on this one pair (0.000719 versus 0.000452 s).
These costs and the absence of a peak-RAM bound remain explicit.

Resume **`experiments/results/cnf-warm-batch/report.json`** through
`continue_cnf_warm_batch.restore_checkpoint`, preserving all five evidence lists
**(1, 42, 156, 12, 1)**. The retained split frontier is now empty, but **24 original
inputs remain structurally uncovered**. Do not rerun only that empty selector.
Use `continue_cnf_original_splits.select` / `selected_frontiers` for another
original, or compare the **17 ready learned bases / 88 candidates**. The smallest
ready base has 33 variables / 359 literals, eight candidates left at offset 24,
and identity `1ad496f104725f62b5d8f754633a96c47aac13064bc6bf977b2f79001dfbde24`.
Test transfer of the restriction/implication/elimination/split pattern while
preserving one admission allowance. Complete-route maintenance remains the
largest repeated warm cost; cold auditing and persistence are still substantial.


## 2026-11-14: another original exposes a closed-cofactor scheduling gap

[The original-frontier batch](original-warm-expansion.md) selects case **1445**,
following its **33-variable / 121-clause / 359-literal** residual. Two saved splits,
three binary-path reductions and two eliminations leave one open **29 / 103 / 307**
residual with **7/32 admissions**. Both splits reuse the same earlier empty-CNF
terminal. Coverage remains **59/83**: part of the transformation sequence transfers,
but this batch does not close another original. All 74 new external probes are clear.

The selected split traces already existed in the immutable source nodes. Ordinary
exhaustion nevertheless consumed seven clear blocks before those two splits;
their full route refreshes cost **6.73336 s**. Compare earlier selection of a
known closed-cofactor pair against continued probing, including the possibility
of a cheaper forced reduction. This is an identified opportunity, not a measured
counterfactual speedup or a guarantee of such a pair for every CNF.

Discovery/acquisition totals **0.20427 s**, while twelve complete route refreshes
cost **11.55914 s**. Full/incremental warm composition and checking cost
**1.38586 / 0.47716 s**; with shared selection, acquisition and refresh, the indicated
saving is **6.80%**. Initial reconstruction and complete preparation remain
**94.52082 s**; the whole study costs **129.39795 s**. The **14,150-byte compressed
delta** preserves seven patterns and ten probe blocks; two split sidecars are
added. Full history is **770,924,544 bytes / 41,787 patterns**, growing by 217,088
bytes. Previous rows and all 2,041 reference nodes survive; 2,075 reference nodes
and the unchanged 2,828-step positive proof check. All **176 relevant tests** and
independent reconstruction with new recognition disabled pass.

Resume **`experiments/results/cnf-original-warm/report.json`** through
`continue_cnf_original_warm.restore_checkpoint`, with evidence counts
**(1, 42, 156, 14, 1)**. The new selector resumes retained obligations first, then
selects uncovered originals if that frontier is empty. It follows selected paths,
not all possible decompositions. The active leaf SHA-256 is
`ef925b9a7d10a3bab64accecd2ce12015dfa400b13bc949f39781e28c55069f8`.
Six ordinary candidates remain at offset 12: **18, 20, 23, 24, 28, 29**. The best
saved split is **local variable 12**, with one closed child and one missing
28-variable / 281-literal cofactor. Test that reuse opportunity next, retaining
case 1189 as a contrasting forced-reduction control. No unrestricted construction,
peak-RAM or new Lean guarantee is established.


## 2026-11-14: early closed-cofactor reuse helps one case and costs another

[The matched policy comparison](early-closed-expansion.md) tests using an already
checked closed cofactor before fresh ordinary probes. On case **1445**, early reuse
reaches the same state-budget boundary in **6 rather than 8 advances**, avoiding
12 assumption attempts. Expansion time falls **8.08296 -> 6.27974 s (22.31%)**;
complete worker time falls **20.70618 -> 17.90584 s (13.52%)**. Both arms enter the
same 32 state identities, store identical pattern payloads and choose identical
split records. Acquisition itself is slower because of extra candidate checks.

On the earlier forcing case **1189**, both policies preserve the same successful
8-step / 21-state proof, but early search takes **8.00118 versus 7.87241 s** for
expansion: a **1.64% regression**. It ranks 94 pairs versus 15, with eight misses.
These are single paired development runs, not independent holdout estimates or
a universal speedup. Saved forcing and unfinished pairs retain priority; both
children remain mandatory for structural coverage.

The current case reaches a **27-variable / 93-clause / 287-literal** source.
Its split on local variable **4** closes the false **22 / 72 / 211** cofactor
through 24 states, ending in a polarity transformation to a **6-variable Horn
terminal that is not 2-CNF**. The true **23 / 70 / 196** cofactor remains pending:
four more states were entered before the 32-state allowance ended, without
completed rows for those four states. Thus 32 admissions yield 28 new stored
patterns. Resume that exact target; the limit is not evidence of intrinsic hardness.

Both policies' results, including the regression, are preserved and merged into
current history. Each comparison arm has its own allowance; the union is not a
single 32-state experiment. Coverage remains **59/83**. The combined **19,191-byte
compressed delta** adds 28 patterns and six probe blocks, with two new split
sidecars. Full history is **771,342,336 bytes / 41,815 patterns**, growing by
417,792 bytes. All previous rows and all 2,075 reference nodes survive; 2,115
reference nodes and the unchanged 2,828-step positive proof check.

All **181 relevant tests** and independent reconstruction of all four arms pass.
Current/control reconstruction costs **32.97981 / 25.34922 s**; final complete
route preparation and all-original coverage checking cost **7.44994 / 60.00692 s**.
The full study costs **227.90943 s**. No peak-RAM, new Lean refinement or unrestricted
construction bound is supplied.

Resume **`experiments/results/cnf-early-closed/report.json`** through
`compare_cnf_early_closed.restore_checkpoint`, preserving evidence counts
**(1, 42, 156, 16, 1)**. Pending target SHA-256:
`69d0f3cad2b4d527495373e3fecf905d0c538d98adb833dbd0373598cfb0280e`;
split source SHA-256:
`6be85c519f3e56d3096ab3e1ed2ad63597d70459193d435d885457fca290ca39`.
Resume the pending true branch before another ranking search. Then investigate
incremental candidate checks with explicit invalidation for new traces, admitted
targets and changed coverage. Do not rerun all four comparison arms to continue.

## 2026-11-14: resume the pending cofactor and complete another original

[The exact saved split resumes](pending-warm-expansion.md) without reranking its
27-variable parent. Its closed false cofactor uses zero admissions. The true
23-variable cofactor uses twenty, ending at a seven-variable Horn and zero-valid
terminal after four probes, four binary-path deletions, ten eliminations and a
polarity transformation. It is not 2-CNF. Both branches now close, raising
structural coverage **59/83 -> 60/83**; the reference result for original case
1445 is SAT. All sixteen retained splits close, but 23 originals remain uncovered.

Four of the twenty entered states were unfinished at the previous cap and are
recomputed. All twenty now have completed rows. No previously completed identity
is admitted again. This measures a remaining persistence gap: local reduction
work on unfinished recursive ancestors is not checkpointed. A future pending
representation must preserve checked obligations without asserting their closure.

Acquisition takes **0.05998 s**, complete route refresh **0.98680 s**, and initial
reconstruction/preparation **103.25725 s**. The full producer takes **127.60236 s**.
The **11,805-byte compressed delta** adds twenty patterns and no external probe
blocks. Full SQLite grows **249,856 bytes** to **771,592,192 bytes / 41,835 patterns**.
The positive proof has **2,948 steps**, and all **2,115** earlier reference nodes
remain among **2,135**. All prior rows and experimental comparisons are preserved.

Resume `experiments/results/cnf-pending-warm/report.json` through
`continue_cnf_pending_warm.restore_checkpoint` with evidence counts
**(1, 42, 156, 16, 1)**. The next selected original is case **1304 / index 52**,
with a **34-variable / 148-clause / 490-literal** leaf; local variable **34** is
its last ordinary candidate at offset 12. Test transfer of the reduction chain
while amortizing complete preparation across useful steps. Neither this new
coverage nor an empty retained frontier establishes efficient arbitrary SAT.

## 2026-11-14: conditioning transfers through refutation and zero-valid structure

[Two warm advances](transfer-1304.md) close case **1304 / index 52**, raising
structural coverage **60/83 -> 61/83** in both views. On its 34-variable residual,
the last ordinary candidate is clear. A saved split on local variable **32** then
uses **10/32 admissions**: three failed-literal reductions refute its false
cofactor, while six reductions reach a **12-variable / 18-clause / 40-literal
zero-valid** SAT terminal on the true branch. The latter is neither Horn,
dual-Horn nor 2-CNF. Both branch answers and the SAT model lift are independently
checked. All seventeen retained splits close; 22 originals remain uncovered.

This exhibits a further reuse opportunity: the refuted cofactor proves a forced
value at its parent. The current checkpoint retains the split and branch proofs;
it does not introduce a new inferred-unit route. Reusing that value would require
the negative proof and exact source/transport binding, not a structural closure
bit. The two closed SAT branches in case 1445 show why that distinction matters.

Acquisition plus ranking costs **0.20118 s**, complete route refresh **2.01995 s**,
and initial reconstruction/preparation **106.78542 s**. The whole producer takes
**133.16301 s**. The early policy ranks 50 pairs, including seventeen immediately
rechecked after ordinary exhaustion; this is an avoidable candidate-maintenance
cost, subordinate to cold preparation. Two external assumption attempts and
nineteen retained internal assumption traces must be accounted for separately.

The **9,914-byte compressed delta** adds ten patterns and one continuation, plus
one split sidecar. Full history grows **122,880 bytes** to **771,715,072 bytes /
41,845 patterns**. All 2,135 earlier reference nodes remain among **2,259**, and
the expanded positive proof has **3,043 steps**. Cold reconstruction checks all
original coverage flags, exact next selection and reference proofs without fresh
recognition, taking **109.00529 s**.

Resume `experiments/results/cnf-transfer-1304/report.json` with
`continue_cnf_pending_warm.restore_checkpoint`, evidence counts
**(1, 42, 156, 17, 1)**. Next: case **1299 / index 48**, selected leaf
**36 / 162 / 517**, ordinary candidates **33, 34, 36** at offset 12. No currently
saved pair has a present child root; variable **17** has the best size rank.
These are adaptive development results, without a general expansion bound.

The next saved candidates expose a ranking tradeoff: variable **17** gives
34- and 32-variable children (927 total literals), while variable **1** gives
16- and 35-variable children (617 total literals). The latter's smaller branch
could be useful, but neither candidate has been acquired. Compare them under
matched allowances after the remaining probes, retaining both branch obligations.
All **181 relevant tests** pass for this checkpoint.

## 2026-11-14: matched first splits separate storage from completion cost

[Case 1299's matched comparison](split-cost-1299.md) retains thirteen new patterns
for initial variable 1 versus twenty-nine for variable 17. Each starts from the
same seed after six clear ordinary attempts, with twelve advances and a shared
32-state budget. Two repetitions reverse the arm order and yield identical
logical results. Compressed arm deltas are **15,849 vs 28,842 bytes**, but mean
expansion is **12.72181 vs 12.72706 s** and neither source closes. The runtime
comparison changes direction across repetitions; the smaller arm's complete
worker is **3.03% slower**. Complete route refresh consumes about **94%** of warm
expansion. The smaller acquired representation is no proof of a faster complete
solution or a minimum-cost split.

Both paths expose SAT terminals on one first cofactor: **5 / 5 / 10** is Horn,
2-CNF and zero-valid; **5 / 7 / 16** is Horn and zero-valid, but not 2-CNF. On the
other side, a later split refutes one cofactor through two probe reductions,
reusing the same empty-clause terminal. The remaining leaves are **28 / 110 / 351**
and **29 / 108 / 337**. Both have exhausted ordinary probes, with 21 clear pairs
and no candidate child presently acquired. Similar open leaves suggest checking
exact shared structure; they do not yet have a certified equivalence or transport.

Coverage stays **61/83** in both views. The preserved union has 42 unique new
patterns, 21 probe blocks and four split records; it is not one 32-state run.
The **43,317-byte compressed delta** grows full history by **884,736 bytes** to
**772,599,808 bytes / 41,887 patterns**. The positive proof remains 3,043 steps.
All 2,259 earlier reference nodes remain among 2,605. All **181 regression tests**
and the independent **214.315 s** audit pass, including exact seed/arm replay,
original closure flags, next selection and reference checking without fresh
recognition or reference solving.

Resume `experiments/results/cnf-split-cost-1299/report.json` through
`compare_cnf_split_cost.restore_checkpoint`, evidence counts **(1, 42, 156, 21, 1)**.
The next selected 28-variable source is
`dd04e43d15b115ab5d60b5b4aef44d03001fcfe6910263b218b5f35776ed70ab`;
its current best rank is **[2, 2, 26, 571, 17]**. Continue that obligation while
investigating shared structure with the alternative and incremental/deferred
catalog refresh. Keep decision witnesses, reference answers and structural
coverage separate. The complete producer costs **252.67688 s**; retained disk
bytes are not peak RAM, and no arbitrary-SAT efficiency bound follows.

## 2026-11-14: exact projection reuses a completed alternative

[The two leaves are connected by a certified projection](projection-bridge.md).
Eliminating variable 16 from **29 / 108 / 337** checks ten opposing clause pairs
and gives **28 / 111 / 356**. Removing one clause subsumed by `[-19, 5]` yields
the exact retained **28 / 110 / 351** target. The ordinary two-clause growth
budget rejects the intermediate result; the checked final target satisfies it.
This establishes existential equivalence with a bound variable transport, not
similarity or an inferred SAT/UNSAT label.

Both modes complete the same two leaves from independent identical seeds. Two
reversed repetitions use **25 vs 13 completed new states** and **7 vs 6 advances**
for independent vs bridge completion. Including **0.00691 s** of bridge discovery,
mean warm expansion falls **15.09%** and complete worker time **6.99%**. The bridge
adds **1,468 compressed bytes**; the pattern/probe delta plus that route is
**13,170 vs 18,956 bytes**. These are local development measurements, with shared
OS caches and no unrestricted bound or peak-RAM claim.

The retained union closes original **1299 / index 48**, raising structural
coverage **61/83 -> 62/83** in both views. It stores all 25 new patterns, four
probe blocks, three split records and the bridge. Full history is **772,972,544
bytes / 41,912 patterns**; its positive proof has **3,104 steps**. All 2,605 old
reference nodes remain among 2,921. Every source of the 24 saved split records now closes; 21
originals remain uncovered. The complete four-arm pipeline takes **219.34858 s**,
including **49.62108 s** of restoration and **67.16398 s** of final global checking.

Resume `experiments/results/cnf-projection-bridge/report.json` through
`compare_cnf_projection_bridge.restore_checkpoint`, preserving the five evidence
lists **(1, 42, 156, 24, 1)** **and** the separate `bridges` archive. Build routes
with `compare_cnf_projection_bridge.routes_for(h, evidence, bridges)` and check
extended positive proofs with `cnf_projection_bridge.verify_positive`.
The next original is **1298 / index 47**, leaf **37 / 151 / 455**, source SHA-256
`dd822fabc78af1efd220882ae9ead41593645ea916f4753c13b000b080a162b7`.
Next: recognize converging projections against retained structure before separate
acquisition, including final subsumption in the growth decision. Indexing,
failed proposals, arbitrary renaming and complete route refresh remain open costs.

## 2026-11-14: automatic projection target discovery and a bounded miss

[The new proposal catalog](projection-lookup.md) indexes **19,841 current-policy
formulas** by **17,801 minimal-clause signatures**. It recovers the previous
bridge without a supplied target, including the target's two redundant clauses.
Every hit still needs the original exact projection/subsumption checker and a
justified target proof. All **23 unresolved frontier sources** miss this bounded
search; coverage stays **62/83**, and the solver authority is unchanged.

Three alternating repetitions query 24 sources, including the known control.
Indexed discovery takes **0.87112 s**, versus **1.55276 s** scanning the same
prepared signatures. Construction costs **14.42661 s**, with **28,110,848 bytes**
of extra SQLite storage (**23,149,996 compressed bytes**). These are lookup
measurements, not demonstrated total expansion savings. Of 967 variable
proposals, 95 exceed the opposing-pair cap and 845 exceed final growth even after
subsumption; just 27 reach lookup. Only the known control has an acquired match.

Next: acquire the selected 37-variable residual's **variable-13** projection
within a bounded, matched comparison. Subsumption reduces its raw **154 clauses**
to **153 on 36 variables**, satisfying final growth two, but no acquired matching
target exists. Preserve the next ordinary probes **15, 18, 19, 20**. The exact
candidate is archived in the new study's `selected-diagnostics.json.gz`. Keep the
global index optional until broader reuse justifies its preparation and space.
Resume the unchanged `cnf-projection-bridge/report.json` authority with all five
evidence lists and its separate bridge archive. New catalog and negative results
are preserved in `experiments/results/cnf-projection-lookup/`.

## 2026-11-14: bounded projection acquisition closes a case but loses on cost

[Acquisition of the saved candidate](projection-acquisition.md) now closes
original **1298 / index 47**, raising structural coverage **62/83 -> 63/83** in
both views. Source **37 / 151 / 455** projects by local variable **13** to
**36 / 153 / 470** after one checked subsumption deletion. Pending acquisition
cannot become a bridge, and the helper preserves one shared admission budget.

Two reversed repetitions compare ordinary continuation with projection from
independent identical seeds, with **12 advances / 32 states** each. Both close
the source. Ordinary uses **4 advances / 8 new states / 4.45329 s** expansion;
projection uses **8 / 9 / 8.70178 s**. Complete worker means are **16.62221 vs
21.45978 s**. External continuation needs **20 vs 44** assumption attempts.
Full route refresh costs **4.05191 vs 8.15891 s**, over 90% of expansion.
The smaller formula is more expensive here; the prior successful bridge reused
an already acquired target. Candidate discovery is charged in the preceding
study, not repeated in these conditional means.

Both paths select the same variable under the projection map, source **22** /
target **21**. The false cofactor is refuted after three failed-literal reductions;
the true cofactor reaches the same five-variable disjoint-component key after
two reductions. These paths and independent reference witness lifts are checked.
Both split pairs already occur in their respective initial pattern records,
suggesting an earlier saved-pair policy as the next matched test. Transferring
unit-propagation traces or unsuccessful searches across projection still needs
additional justification.

The union preserves **14 new patterns**, eight continuation blocks, one probe
window, two split records and the new bridge. Three new exact keys are shared
between the arms. Full history is **773,255,168 bytes / 41,926 patterns**; the
union delta is **16,475 compressed bytes** and the positive proof has **3,145
steps**. Both bridge targets and all 26 retained split sources close. Twenty
originals remain uncovered. Independent cold replay takes **221.51064 s**, with
fresh recognition and reference expansion forbidden; all **3,022 reference
nodes**, both repetitions, global coverage and resumable selection check.
All **199 relevant tests pass**.

Resume `experiments/results/cnf-projection-acquisition/report.json` with
`compare_cnf_projection_acquisition.restore_checkpoint`, preserving five evidence
lists **(1, 42, 156, 26, 1)** and its separate two-bridge archive. Report SHA-256:
`d865c287709cccdd0af56c1a23a564618e369be41fd4e971c21c0834b3510b2a`.
Use the bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The new `projection_frontier` sidecar has two closed targets and no leaves.

Next original: **1160 / index 29**, selected **37 / 151 / 456** leaf, SHA-256
`614772f5cb0f59835870e117b1653b225e008eb44416371335350a725cac6149`.
Its next ordinary variables are **13, 15, 16, 17**; sixteen saved pairs have no
acquired candidate child root, with best rank **[2, 2, 35, 794, 19]**. Despite
similar dimensions, its normalized clause set shares no exact clause with the
completed leaf. Prioritize existing split evidence and incremental route
maintenance while continuing broader structural discovery. Neither a minimum-cost
policy nor an unrestricted SAT resource bound has been established.

## 2026-11-14: early saved-pair selection improves both matched cases

[The new scheduling comparison](early-saved-expansion.md) raises structural
coverage **63/83 -> 64/83**, closing original **1160 / index 29**. Saved clear
pairs already carry checked restrictions for both polarities; exhausting the
ordinary probe pool is not required for their correctness. `EarlySavedExpansion`
uses the best existing pair immediately, preserving pending/known-forcing
priority, both child obligations and one shared admission budget. The ordinary
policy already permits early pairs with closed children. Neither uses reference
answers or interprets a clear probe as a SAT certificate.

Two reversed repetitions per case use identical independent seeds, twelve
advances and 32 states. On case 1160, the same sixteen new keys require **2 vs 12
advances**; expansion falls **13.62996 -> 2.24986 s** and complete worker time
**26.38845 -> 14.69517 s** (**44.31% lower**). Extra external assumption attempts
fall **80 -> 0**, while recognizer-internal probing remains charged. Both paths
split source variable **19**, expose binary implications and elimination on its
false branch, then split the remaining **34 / 135 / 404** leaf on local variable
**14**. That split has a refuted branch and a SAT branch ending in **6 / 7 / 14
2-CNF**, neither Horn nor dual-Horn. The first split's true branch reaches the
retained empty-CNF terminal. Both first-level branches are independently SAT;
full structural classification remains distinct from earliest SAT decision.

On historical forcing control **1189**, reconstructed from its older seed,
complete worker time falls **20.45091 -> 15.37364 s** (**24.83% lower**) and
new states **21 -> 20**, using three splits instead of further forcing followed
by one split. Its two new pattern key sets are disjoint. The early policy stays
optional: two successful development examples do not bound the advantage of a
future forcing opportunity or establish a universal selection rule.

The combined checkpoint preserves both policies and all earlier results. It adds
**36 patterns**, nine continuation blocks, one probe window and five split
records. Full history is **773,828,608 bytes / 41,962 patterns**, with **27,393
compressed delta bytes** and a **3,190-step** positive proof. All 31 retained
split sources and both bridge targets close; nineteen originals remain uncovered.
The union is not one 32-state run. Full route refresh still consumes most warm
expansion. The complete study costs **334.32398 s**, including current restoration
**57.71801 s**, historical control restoration **25.38864 s** and final global
preparation/checking **68.76609 s**. Complete worker means charge preparation,
checking and persistence separately from the quoted expansion phase totals.

All **204 tests** pass. Independent cold replay checks all eight arms and
**3,203 reference nodes** with recognition and reference expansion forbidden,
including repeated results, exact next selection and idempotent merging. The
157-page paper builds, preserving all 64 proof blocks. All **533 earlier
artifacts / 17 manifests** remain hash-identical.

Resume `experiments/results/cnf-early-saved/report.json` through
`compare_cnf_early_saved.restore_checkpoint`, keeping the five evidence lists
**(1, 42, 156, 31, 1)** and the separate two-bridge archive. Use bridge-aware
`routes_for` and `cnf_projection_bridge.verify_positive`. Report SHA-256:
`995476297ac2e99710b26b67d9ecc3e95963ab624e68282e7b5108da077999d3`.
Next: original **1263 / index 42**, leaf **37 / 152 / 470**, source SHA-256
`746b92609a26b66fe74b529bdeb36a5a46ca58129c1bcca04c5088bd23d02eeb`.
Its remaining ordinary variables are **32, 33, 34, 37**. Sixteen saved pairs have
no acquired child root; best rank **[2, 2, 35, 817, 6]**. Broaden the comparison
while seeking forcing regressions, and test incremental route maintenance with
explicit activation and invalidation conditions. General efficient SAT coverage
and minimum-cost expansion remain unproved.

## 2026-11-14: clear probe metadata reuses the complete route catalog

[The checked maintenance comparison](clear-probe-maintenance.md) closes original
**1263 / index 42**, lifting coverage **64/83 -> 65/83** in both views. The new
helper retains a complete checked route catalog only after a verified clear
probe with no acquired state, no semantic edge and unchanged sidecars. Exact
SQLite accounting and row binding constrain the change; forcing, acquisition
and new evidence rebuild fully. External or schema changes require reopening
checked inventory state. Saved candidates remain available.

Identical ordinary scheduling on matched seeds yields the same operations,
patterns and final logical tables. Case 1263 uses **4 advances / 11 states**;
two skipped rebuilds reduce mean expansion **4.56885 -> 2.46956 s** and worker
**17.23793 -> 14.87208 s (13.72%)**. Historical forcing control 1189 uses **8
advances / 21 states**; six skipped rebuilds reduce expansion **8.10837 ->
2.24496 s** and worker **20.13427 -> 14.18042 s (29.57%)**. Both modes still
perform **16 / 51** external assumption attempts and retain both branch proofs.
The later forcing result is preserved and activated by a full rebuild.

Persistent deltas are identical: **12,933 / 15,484 compressed bytes** and
**241,664 / 397,312 SQLite bytes**, current case/control. Extra serialized
sidecar snapshots occupy **1,220,757 / 941,068 bytes**, excluding transient
serialization and Python overhead. This is computation reuse, not a storage
reduction or a peak-RAM estimate. Current authority reconstruction costs
**62.36289 s**, final preparation/global coverage **67.55856 s**, and the full
producer **316.04814 s**. Preparation and export remain major worker costs.
Two development cases and two reversed repetitions give no holdout or general
SAT guarantee; do not add these gains to early-saved scheduling gains untested.

The first split is source-local variable 6, then variable 9 of the remaining
31/125/377 leaf. Probe, binary-path and elimination reductions reach retained
Horn/dual-Horn 2-CNF and matching 2-CNF endpoints, plus an empty-clause UNSAT
endpoint. All SAT lifts and both split obligations are checked. Independent
cold replay passes in **313.36574 s** with new recognition/reference expansion
forbidden, including all **3,259 reference nodes**, repeated logical results,
exact selection and idempotent merges. All **209 relevant tests** pass.

Resume **`experiments/results/cnf-clear-maintenance/report.json`** through
**`compare_cnf_clear_maintenance.restore_checkpoint`**, SHA-256
`b4aa304049758bff8e80b2118437321a9edf7128657b3a9303a4985ae57daa78`.
Retain five evidence lists **(1, 42, 156, 33, 1)** and the separate two-bridge
archive; use bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The union adds **11 patterns, 1 window, 1 continuation and 2 splits**. History
is **774,000,640 bytes / 41,973 patterns**, **172,032 bytes** larger. All 33
split sources and both bridge targets close. Eighteen originals remain open.
Next: original **1154 / index 27**, **38 / 158 / 500**, source SHA-256
`f33c327595b24645a6f64e8a072295c51fb2a414872d0de0f84da49192f0085d`.
Its ordinary pool is exhausted. Eleven saved pairs have no acquired child;
best rank **[2, 2, 36, 906, 30]**. Test that pair, then investigate shared family
structure and scheduling choices in its descendants. Prepared checked state and
incremental activation after acquisition remain the next large maintenance gaps.

The manuscript builds to **158 pages** with all **64 proof blocks** unchanged,
no overfull boxes and no undefined references. All **660 earlier artifacts /
18 manifests** remain hash-identical. The new study preserves **124 manifested
artifacts** plus its manifest, including producer, cold-replay, test and build
logs, exact deltas, reference results and source fingerprints.

## 2026-11-14: combined reuse improves one cofactor but leaves pending expansion

[The combined-policy comparison](combined-expansion.md) acquires the best saved
pair of original **1154 / index 27**, **38/158/500**, at local variable 30. Both
modes use this same initial split and checked clear-probe maintenance, then
compare ordinary and early-saved descendant scheduling. Two reversed-order
repetitions preserve one twelve-advance / 32-state allowance per independent
worker. No production recognition rule or default policy changes.

Stepwise reconstruction proves that the same true cofactor closes after **9
advances / 30 states** ordinarily, versus **2 / 19** early. Beyond the common
ten states, this is **20 vs 9 additional states**, with mean expansion
**3.64836 vs 1.11924 s**. The early variable-23 split of the 31/130/416 leaf sends
both branches to the retained empty-CNF terminal. Ordinary forcing first reaches
26/101/329, then variable 5 reaches an empty terminal and an existing Horn 2-CNF
plan. These are different checked routes to the same completed cofactor.

The full original remains structurally open; coverage stays **65/83**. Ordinary
spends **12 advances / 30 admitted and stored states**; early spends **4 advances /
32 admitted / 27 stored / 5 unstored ancestors**, with both final split targets
pending. Mean worker time is **17.80102 / 17.20828 s** and expansion **4.98209 /
4.64624 s**. These unfinished obligations differ, so no whole-original speedup
is established. Both modes still pay about **4.3 s** for four full route refreshes;
eight extra ordinary clear blocks already avoid rebuilding. Stored delta sizes
**26,971 / 20,877 compressed bytes** likewise do not compare equal completed work.

The union preserves **47 new patterns** (ten shared, twenty ordinary-only,
seventeen early-only), **6 continuations / 4 windows / 5 splits**. History grows
**765,952 bytes** to **774,766,592 bytes / 42,020 patterns**. The union is not one
32-state run; the five interrupted ancestors are not counted as stored results.
Producer time is **231.79591 s**, including **67.80502 s** restoration and
**67.41552 s** global preparation/coverage. Independent cold replay passes in
**302.33071 s**, forbidding fresh recognition and reference expansion. It checks
all **3,422 reference nodes**, both polarities, SAT model lifts, interrupted
accounting, idempotence and exact next selections. First-repeat stepwise replay
inserts only then-available rows and certifies cofactor-completion times; exact
operation histories agree within each mode across repetitions. All reference
split sources and raw children are SAT. Complete structural coverage is a
stronger objective than producing a SAT witness.

Resume `experiments/results/cnf-combined-expansion/report.json` using
`compare_cnf_combined_expansion.restore_checkpoint`, report SHA-256
`33c45cc536dc9ada0acdb4d1ef9a17bd9a71e260704644aa656af42835c349c3`.
Keep five evidence lists **(1, 42, 156, 38, 1)** and the separate two-bridge archive;
use bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
Resume the pending **30/116/363**, local-variable-26 split, source SHA-256
`f68661ab48e945151f89e250ebbcc35eb2ff8034799d2a83e2ddd88d7306567d`.
Its targets **29/108/336** and **19/54/140** are absent; a **33/130/400** leaf
also remains. The last interrupted advance writes no pattern/probe row but pays
**1.06672 s** refreshing routes against **0.03448 s** acquisition. A guarded
pending-sidecar update is a more immediate maintenance target than that small
reentry cost. Preserve both obligations and test activation when targets later
arrive. General efficient coverage and minimal expansion remain unproved.

Verification: **209 regression tests pass**; the manuscript builds to **158
pages**, with all **64 proof blocks unchanged** and no undefined references or
overfull boxes. SHA-256 checks preserve all **784 artifacts in 19 prior
manifests**. The new manifest binds **81 artifacts** (4,377,743 bytes), including
producer/cold logs, both policy histories, stepwise findings, progress summaries
and validation metadata. One existing SQLite ResourceWarning appears in the
passing regression log; no solver or test module changed.

## 2026-11-14: inactive pending splits preserve routes; one cofactor remains

[The pending-split maintenance study](pending-split-maintenance.md) implements
an optional guard for zero-write interrupted splits. It checks the exact sidecar
change, both polarity bindings, missing targets and entered-state accounting.
A split with an absent child adds no active edge; any write or other sidecar
change rebuilds routes, including later activation. The guard is independent of
CNF category, with linear sidecar serialization plus split-checking costs.

Two reversed-order repetitions compare clear-only maintenance with this guard.
The historical interruption preserves identical operations and stored results
while the final route update falls **1.08509 -> 0.01138 s**. Mean expansion falls
**4.71930 -> 3.59923 s** and worker time **17.55753 -> 16.15178 s (8.01%)**.
The current resumption writes nodes in every advance, so all three updates
rebuild and expansion remains **3.54491 / 3.54578 s**. No persistent-memory
saving or completed-original speedup follows from the interruption comparison.

Resumption acquires the old variable-26 pair with nine states and closes its
23-variable leaf via a variable-13 split with eight more. The two new splits'
false branches reuse the same UNSAT empty-clause terminal; a true branch reaches
a **10/10/21** polarity-transformed Horn, zero-valid residual. The separate
**33/130/400** source splits at variable **18**, acquiring its false **29/96/275**
cofactor with two states but entering thirteen ancestors of the true
**30/111/330** cofactor without storing them. All **32 admissions** are charged;
**19 new patterns** are completed. The true cofactor is independently SAT; the
missing obligation is reusable structural decomposition. Coverage stays
**65/83**, with one pending target and no acquired open leaf in the frontier.

The union preserves old history and adds **19 patterns / 2 split records / no
external probe rows**, reaching **775,004,160 bytes / 42,039 patterns**. The delta
is **307,200 SQLite bytes / 12,874 compressed bytes**. The independent reference
archive preserves **3,422** prior nodes and has **3,467** total. The positive
certificate still has **3,239 steps**. Producer time is **368.96634 s**, including
**72.00904 s** current restoration, **67.51801 s** historical restoration and
**68.15113 s** final route preparation/global coverage.

Resume `experiments/results/cnf-pending-maintenance/report.json` using
`compare_cnf_pending_maintenance.restore_checkpoint`, report SHA-256
`9a48fc85512e52c566dd60f0396a4bacf842b48267ee47606394d271d221f8d0`.
Keep five evidence lists **(1, 42, 156, 40, 1)** and two separate bridges, using
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The pending source SHA-256 is
`1fab57607093cb833cc8fa0f21d88c2e7e9eb094dac7cdd416e8a786e3fcf056`;
its missing true target is
`5124e2d5f451e42b274ed6886d29676c94f89e27bb3054f77b530f2f3091a3a4`.
Resume this exact pair, retain its acquired false child and charge reentry of
the thirteen unstored keys. The next maintenance opportunity is complete
activation of affected routes after actual acquisition. A reverse dependency
index must cover all route types and newly satisfied old pending obligations.
Current final acquisition costs about **0.06 s**, versus **1.08 s** for rebuild;
continuation-checkpoint work should be judged against that measured difference.

Independent cold replay passes in **487.75798 s**, with all **3,467 reference
nodes** checked and no fresh recognition or reference search. All eight workers
have identical operations and logical results within each workload. Four
stepwise prefix replays compare complete maintained and fresh catalogs,
coverage and next selections using only then-available rows. All five previously
interrupted states are reentered and now stored; thirteen new unstored states
remain explicit.

Verification: **215 tests pass** (209 prior plus six new regressions). The
manuscript builds to **159 pages**, preserving all **64 proof blocks** exactly,
with no overfull boxes or undefined references. All **865 prior artifacts in
20 manifests** remain hash-identical. The new manifest binds **104 artifacts**
(3,977,775 bytes), including matched operations, deltas, independent findings,
reference results and logs. SQLite ResourceWarnings in the passing suite and
the initial external-write fixture correction are recorded in validation
metadata. No completed result or earlier experiment was removed.


## 2026-11-14: exact pending-pair resumption closes case 1154

[The retained-pair experiment](pending-pair-resumption.md) raises structural
coverage **65/83 -> 66/83**, also without growth exceptions. Both independent
repetitions resume the exact local-variable-18 split. Its already acquired
false branch takes no new admissions; sixteen states on the true **30/111/330**
cofactor expose a **19/66/214** residual. A saved variable-3 split takes eight
and six further states. The two branches reach different seven- and
nine-variable Horn, zero-valid terminals after checked reductions and polarity
changes; neither is 2-CNF. These are overlapping family recognitions and
similar reduction patterns, not a shared terminal proof. Both raw branches are
SAT in the independent reference check. Full structural closure still checks
both branch obligations.

All **30 admissions** are stored, including all thirteen ancestor keys that
were entered but unstored in the previous run; their reentry is charged.
No retained split obligation remains open. **Seventeen original formulas** are
still uncovered, and the next selected residual belongs to **1062 / index 14**,
with **39 variables / 161 clauses / 495 literal occurrences**.

Mean expansion costs **2.38750 s**: acquisition **0.12262 s**, complete route
updates **2.17729 s (91.2%)**, selection **0.08558 s**, and coverage **0.00201 s**.
Preparation and export cost **8.01578 s** and **4.76630 s**; whole worker time is
**15.23836 s**. These are two identical-policy repetitions, not a comparative
speedup. Both updates change patterns and correctly rebuild. Arrival of the
last missing target activates an old split; the following split attaches with
both targets acquired. These transitions are concrete fixtures for a future
complete dependency-based maintenance implementation.

The union adds **30 patterns / 1 split / no external probe records**. Internal
probe certificates are stored with pattern nodes. The delta is **446,464
SQLite bytes / 17,007 compressed bytes**, and full history grows **372,736 bytes**
to **775,376,896 bytes / 42,069 patterns**. The positive certificate has
**3,360 steps**; reference evidence preserves all **3,467** prior nodes and
contains **3,575**. Parent restoration costs **76.28286 s**, final preparation
and global coverage **68.16053 s**, and the complete producer **196.65984 s**.
Persistent byte counts do not measure peak RAM or establish arbitrary-SAT bounds.

Resume `experiments/results/cnf-pending-pair/report.json` through
`continue_cnf_pending_pair.restore_checkpoint`, SHA-256
`0e310e043cc74e29d102115663db88c513acf8bf865fac7412fea1e0eb4f5760`.
Keep evidence lists **(1, 42, 156, 41, 1)** and **two bridges**, using bridge-aware
`routes_for` and `cnf_projection_bridge.verify_positive`. The report's `source`
is the now closed 38-variable ancestor. **Select the next work from
`next_selection`**, not that completed focus. Broader conditional-family
discovery and complete incremental route activation remain the priorities.


Independent cold reconstruction passes in **289.93906 s**, checking all
**3,575 reference nodes** without fresh recognition or reference search.
Both repeat prefixes reconstruct only then-available rows and reproduce the
complete maintained/fresh catalogs, closure and next selections. All **3,467
previous reference payloads** and **969 earlier artifacts in 21 manifests**
remain unchanged. **215 tests pass**; the manuscript builds to **159 pages**
with all **64 proof blocks unchanged**, no overfull boxes and no undefined
references. The new manifest binds **40 artifacts (4,005,929 bytes)**,
including operations, deltas, reference evidence, cost and structural findings,
validation metadata and logs. No new Lean theorem or general SAT tractability
claim is made.


## 2026-11-14: selective activation after real pattern acquisition

[The activation helper](pattern-activation.md) closes the dominant warm
maintenance gap for guarded pattern-only appends. It indexes missing premises
of all conditional route types, activates affected routes when their targets
arrive, and preserves the full builder's order. Both split branches remain
required. Other writes or sidecar changes use existing checked maintenance;
external writers require reopening the inventory. Initial and cold checking
remain complete. The index is additional live state, not a persisted trust
cache or a storage reduction.

Two reversed-order repetitions compare identical scheduling and independent
seeds. Historical complete-worker time falls **15.08509 -> 12.86353 s (14.73%)**;
current bounded-worker time falls **16.85095 -> 13.40605 s (20.44%)**. Route-update
costs fall **2.18377 -> 0.02296 s** and **3.33336 -> 0.03679 s**, respectively.
Current acquisition/selection now cost **0.26735 / 0.13948 s**, compared with
**0.03679 s** maintenance. Preparation and export remain **7.83564 / 4.97464 s**,
and their variation is not an activation improvement. The historical case
closes the same thirty states; current partial expansion stores thirty-two
states but leaves identical unfinished obligations in both modes.

The current **39/161/495** source of original **1062 / index 14** splits on
local variable 25. Its false branch reaches an existing **36/144/434** unresolved
plan after two reductions; the true branch exposes **35/149/466**. A variable-8
split of that leaf takes **2 / 21** states, with the true branch reaching a new
**7/9/19** Horn, zero-valid terminal after checked reductions and polarity
change. The remaining **34/143/440** leaf splits at variable **5**. Its false
branch takes the last three states to reach **31/122/370**; its true
**32/136/405** target is absent and was never admitted. No entered state is
unstored. Every current split source and raw cofactor is SAT in the separate
reference check; complete structural coverage still requires both children.

Coverage stays **66/83**, with **3 open split records / 2 acquired leaves /
1 pending target**. The union preserves **32 patterns / 3 split records / no
external probe rows**, growing history **434,176 bytes** to **775,811,072 bytes /
42,101 patterns**. The delta is **516,096 SQLite bytes / 23,539 compressed bytes**,
identical across current modes. The index ends with **697 route entries** and
one missing-target link. The positive certificate has **3,360 steps**; reference
evidence preserves all **3,575** prior nodes and contains **3,734**.
The complete producer costs **369.75582 s**, including current restoration
**80.22699 s**, historical restoration **76.75811 s**, and final route preparation
and global coverage **68.84394 s**. Peak RAM and unrestricted-SAT bounds are not
measured or established.

Resume `experiments/results/cnf-pattern-activation/report.json` using
`compare_cnf_pattern_activation.restore_checkpoint`, SHA-256
`7af092282dfda5070c4dbf1006daa8cff22a218487af28e40b59e8dc51894c7c`.
Retain evidence lists **(1, 42, 156, 44, 1)** and **two bridges**, with complete
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
Resume the exact variable-5 pair; retain the acquired false child and both
other open leaves. Pending source:
`26f134186dbdd90745599fa2d41308823b8c08b752f19d5f53124ffd4ecd73f1`.
Missing true target:
`72697c710335660e1dc9c934e995f7c37577a9226c546fd7233d4e3685cb3615`.
After the maintenance saving, structural discovery and reuse in these remaining
cofactors, plus cold setup/export costs, are the priorities. The alternative
first variable-17 split remains untested.

Validation: independent cold reconstruction passes in **498.30431 s**, checking
all eight matched workers and **3,734 reference nodes** without fresh discovery
or reference solving. Four first-repeat prefixes match complete rebuilt
catalogs, order, closure, next selection and activation counts. All **222 tests**
pass; existing SQLite resource warnings remain in the log. The manuscript
builds to **160 pages**, with no overfull boxes or undefined references and all
**64 previous proof blocks** unchanged. All **22 prior manifests / 1,009
artifacts** and all **3,575 previous reference payloads** remain unchanged.
The new manifest binds **98 artifacts / 4,355,064 bytes**; commands, source
fingerprints and checks are in the checkpoint's `validation.json`.

## 2026-11-14: another conditional Horn branch and interrupted acquisition

[Conditional-frontier resumption](conditional-frontier-resumption.md) finishes
the missing true **32/136/405** branch of the retained variable-5 split in
**11 new states**, reaching a **17/26/62** Horn, zero-valid formula through
probes, binary-path reduction and a polarity change. Its acquired sibling
needs no new admissions but still leads to **31/122/370**. Both structural
obligations remain required; recognizing one branch does not close the source.

The next split uses local variable **2** on that 31-variable residual. Its false
**29/110/329** cofactor takes eight states to reach unresolved **24/88/274**.
Its true **29/115/343** cofactor enters thirteen states before exhausting the
shared allowance. Those thirteen have no stored pattern certificates. Each
repeat therefore enters **32 states / stores 19 / leaves 13 unstored**. Their
exact inputs remain in the operation logs; their shapes are not certified edges.
Two independent repeats reproduce the same operations and persistent results.
Coverage stays **66/83**; there are **4 open splits / 2 acquired leaves /
1 pending target**, including the earlier unresolved **36/144/434** plan.

Mean expansion is **0.25005 s**: selection **0.09339**, acquisition **0.13225**,
maintenance **0.02355** and focus coverage **0.00086 s**. Preparation/export are
**8.06032 / 4.85783 s** and the complete worker costs **13.25993 s**. This is
an identical-policy continuation, not a comparative speedup. Preparation and
export account for roughly 97% of worker time. The full producer costs
**209.79814 s**, including **92.09233 s** restoration and **67.60414 s** final
route preparation plus global coverage. The index ends with **698 routes /
one pending link**; no peak-RAM reduction is claimed.

The union adds **19 patterns / 1 split / no external probe rows**. History grows
**253,952 bytes** to **776,065,024 bytes / 42,120 patterns**. Its delta occupies
**319,488 SQLite bytes / 14,220 compressed bytes**. The positive certificate
remains **3,360 steps**; reference nodes grow **3,734 -> 3,781**.

The code stores a pattern only after its recursive acquisition returns. Thus,
for an unchanged history with a deterministic unary chain of L unrecorded
states and no intervening completed branches, a repeated allowance B < L can
fail before any row is stored on every retry. The linked analysis gives the
induction over retries and the requirements for checked local continuations.
This is a restart-policy limitation, not a SAT lower bound. The current
interruption does not show that its full path exceeds a fresh allowance of 32.

Resume `experiments/results/cnf-conditional-frontier/report.json` through
`continue_cnf_conditional_frontier.restore_checkpoint`, SHA-256
`f55bdcefe556222a5b6043f03591e38f10ad8c76bc3c3c73a8eb45aed73c0ef8`.
Keep evidence **(1, 42, 156, 45, 1)** and **two bridges**. Resume the variable-2
pair of source `09831bee0e0295f91c4d21b79ffe25508d3dad8b48e5052b4bfde74367574914`;
its missing true target is
`944e1c80b727c779838a814ab6d1509ae46b22afbde7e978523bb96c8f0ce859`.
Charge reentry of all unstored inputs, preserve the acquired false branch and
both open leaves, and distinguish pattern recurrence from identical-formula
reuse. Startup/export reuse promises the larger measured runtime saving;
interruption-safe continuations address progress and avoid repeated discovery.

Independent cold reconstruction passes in **305.33218 s**, verifies all
**3,781 reference nodes**, and reproduces global coverage and the next
selection without fresh discovery or reference search. Both stepwise prefixes
match full catalogs, ordering and activation counts. All **222 tests** pass;
existing SQLite resource warnings remain visible in the log. The **161-page**
manuscript builds with no overfull boxes or undefined references, and all
**64 previous proof blocks** remain unchanged. The restart-policy argument is
textual; no new Lean theorem is claimed.

All **23 previous manifests / 1,107 artifacts** and all **3,734 previous
reference payloads** are unchanged. The new manifest binds **40 artifacts /
3,720,830 bytes**, including operation logs, deltas, reference evidence,
structural findings, cost summary, validation metadata and test/build logs.
See `experiments/results/cnf-conditional-frontier/validation.json` for exact
commands and source fingerprints.

## 2026-11-15: export the appended evidence and retain the next conditional family

[The guarded exporter](append-delta-export.md) avoids comparing old payloads
when an exclusively owned, verified history has only appended rows. It checks
schema/data versions, suffix counts, total cardinality and connection-wide
write counts. Counting still touches historical index pages. Independent
certificate checks and full cold reconstruction remain required; the helper
is optional and does not change the frozen discovery implementation.

Two reversed-order repetitions use the same pending pair and shared 32-state
allowance. They produce identical operations and delta bytes. Mean export
falls **4.87738 -> 0.76122 s**, with **0.66334 s** boundary setup charged to
preparation. Complete worker time falls **13.11241 -> 9.92093 s (24.34%)**.
Preparation now costs **8.84331 s** and dominates. The complete comparison
producer costs **228.86791 s**, including **90.58347 s** historical restoration
and **68.23153 s** final route preparation plus global coverage. This is a
matched bounded-expansion result on reused development inputs, not a cold
end-to-end speedup or an arbitrary-SAT complexity bound.

The resumed true 29-variable cofactor closes through **21 new states** to a
**9/16/43 one-valid terminal**, neither Horn, dual-Horn nor 2-CNF. Its chain
contains nine elimination, eight probe and three binary-path nodes. All
thirteen previously unstored inputs are reentered, charged and now stored.
The sibling remains open at **24/88/274**. Its new split leaves both targets
missing: **20/68/198 false** and **21/71/208 true**. Eleven entered inputs
remain unstored. Coverage stays **66/83**, with **five open splits / one
acquired leaf / two pending targets**, including the separate unresolved
36-variable leaf. A SAT model on one branch does not discharge the other
structural obligation.

The union stores **21 patterns / one split / no external probe rows**. History
is **776,331,264 bytes / 42,141 patterns**, growing by **266,240 bytes**. Both
methods retain **327,680 SQLite bytes / 12,754 compressed bytes**. Reference
nodes grow **3,781 -> 3,803**; the positive certificate remains **3,360 steps**.
The activation index has **699 routes / two missing-target links**. There is
no persistent-space saving or measured peak-RAM reduction.

Resume `experiments/results/cnf-append-export-checked/report.json` through
`compare_cnf_append_export.restore_checkpoint`, SHA-256
`81e1c7c0b887277cefa62df011738e73c809a9fef16897ba5238e84bf45732d4`.
Keep evidence **(1, 42, 156, 46, 1)** and **two bridges**. The method note records
both pending target hashes. Priorities are checked startup profiling, resuming
both pending cofactors, and preserving unfinished recognition through checked
local continuations. No new Lean theorem or efficient unrestricted partition
is claimed.

The first attempted comparison rejected immutable legacy tables before
acquisition. Its baseline, rejected implementation and log are preserved under
`experiments/results/cnf-append-export/`; they support no matched speedup.
The corrected helper permits unchanged legacy tables and rejects their writes.

Independent cold replay passes in **365.45167 s**, checks all four workers and
all four intermediate catalogs, and verifies **3,803 reference nodes** without
fresh discovery or reference search. All **229 tests** pass. The manuscript
builds to **161 pages**, with no overfull boxes or undefined references; all
**64 previous proof blocks** are unchanged. All **1,147 artifacts across 24
prior manifests** and all **3,781 prior reference payloads** are preserved.
The new manifest binds **73 artifacts / 3,954,783 bytes**, including the rejected
attempt. Exact commands, source fingerprints, concurrency notes and checks
are in `experiments/results/cnf-append-export-checked/validation.json`.

## 2026-11-15: reuse checked state across bounded expansion batches

[The retained-session study](retained-expansion-session.md) profiles startup
before changing it. Checked route construction takes **7.56459 of 8.83102 s**
in the uninstrumented sample. The helper retains the same verified inventory,
cache and complete maintained catalog across batches. It resets only the
admission ledger after checking write/schema versions, maintenance state,
sidecars and policies. This requires exclusive ownership and immutable old
rows/cached objects. Cold process restart still reconstructs checked authority.

Two reversed-order repetitions compare two consecutive 32-entry batches under
each policy. The mean sum of complete workers falls **23.32780 -> 16.18611 s
(30.61%)**, including initial checking. Both policies enter **64 states**, store
**44 patterns** and produce identical per-batch deltas. Thirteen unfinished
first-batch entries are charged again; seven final entries remain unfinished.
Session retention preserves completed checking, not unfinished recursive work.
The producer separately charges **95.47416 s** historical restoration and
**69.18542 s** final route preparation/global coverage. The retained second
worker still spends **3.69664 s** on preparation; snapshot copying and digests
need separate measurement before the next optimization.

The acquired nodes include conditional **6/7/18 Horn/one-valid/zero-valid** and
**4/3/6 Horn/2-CNF/zero-valid** terminals. Coverage stays **66/83**. The frontier
shrinks to **two open splits / no acquired open leaf / one pending target**.
The remaining **36/144/434** source has an acquired false **31/120/344** child
and a pending true **32/110/308** child. Resume that exact split while preserving
the acquired child. The method note binds source and target hashes.

History grows **540,672 bytes** to **776,871,936 bytes / 42,185 patterns**.
The union adds **44 patterns / two split sidecars / no external probe rows**,
retaining **622,592 SQLite bytes / 22,766 compressed bytes**. Reference evidence
grows **3,803 -> 3,830 nodes**; the positive certificate remains **3,360 steps**.
The index ends with **701 routes / one missing-target link**. Retention extends
cache lifetime and gives no persistent-space or measured peak-RAM reduction.

Resume `experiments/results/cnf-expansion-session/report.json` through
`compare_cnf_expansion_session.restore_checkpoint`, SHA-256
`a9133c94e01789bb80298de290f17177f71ae428f6d827142bd287722dca9793`.
Keep evidence **(1, 42, 156, 48, 1)** and **two bridges**. Further priorities are
the pending conditional branch, separately measured snapshot/cold costs, and
checked local continuation of unfinished recognition. No new tractability or
Lean theorem, compact-state bound or efficient arbitrary-SAT partition is claimed.

Independent cold replay passes in **518.83008 s**, reproducing all eight
workers and their intermediate catalogs without fresh discovery or reference
search. It verifies **3,830 reference nodes**. All **233 tests** pass. The
manuscript builds to **162 pages**, with no overfull boxes or undefined
references; all **64 previous proof blocks** remain unchanged. All **1,220
artifacts across 25 prior manifests** and all **3,803 previous reference
payloads** are preserved. The new manifest binds **101 artifacts / 4,289,703
bytes**, including the startup profile, eight workers, cold replay, structural
findings and test/build logs. The initial failed external-write test fixture
is retained and explained; its correction changes stored bytes rather than
issuing an external no-op update. Exact commands, source fingerprints and
concurrency notes are in
`experiments/results/cnf-expansion-session/validation.json`.

## 2026-11-15: close the retained split without overstating original coverage

[The session-frontier continuation](session-frontier-closure.md) completes the
pending true **32/110/308** cofactor through **29 new patterns**: five probe,
five binary-path, eighteen elimination and one family node. Its **7/21/85**
terminal is one-valid and outside Horn, dual-Horn and 2-CNF. The completed false
branch and its empty-clause refutation are reused. Both independent repeats
stop after one advance in the first 32-entry batch; the second allowance is
unused. All seven previously unfinished entries are reentered and charged.

The enclosing **39/161/495** retained focus closes, leaving no open saved split,
leaf or pending target in that frontier. **Original-input coverage stays 66/83.**
Seventeen originals still have unresolved leaves; case 1062 retains a different
**40/174/541** leaf. Closing the acquired conditional obligations is not a
certificate for every original. The global navigator now selects **39/162/510**
from original **case 1120** (retained index **22**), with `learning_clear`
status, ordinary-probe offset twelve and no pending split.

Mean complete-worker time is **12.41063 s**, with **12.16111 s** preparation
(including **7.38139 s** initial checked session setup), **0.15429 s** expansion
and **0.01920 s** append export. Acquisition alone is **0.08840 s**. The producer
costs **221.94795 s**, including **99.77114 s** restoration and **70.02150 s**
final route preparation/global coverage. These are repeated discovery runs,
not competing implementations or a new speedup measurement. Profiling cold
restoration and the remaining snapshot preparation costs is still warranted.

The union retains **29 patterns / no new split sidecars / no external probe
rows**. History grows **364,544 bytes** to **777,236,480 bytes / 42,214 patterns**.
The delta occupies **438,272 SQLite bytes / 15,542 compressed bytes**. The
reference archive stays at **3,830 nodes**, the global positive certificate at
**3,360 steps**, and the live index at **701 routes / zero missing-target links**.
No memory reduction, compact-state bound or efficient arbitrary-CNF guarantee
is established. Conditional recognition of the existing all-true family does
not bound the work of finding comparable reductions for other inputs.

Resume `experiments/results/cnf-session-frontier/report.json` through
`continue_cnf_session_frontier.restore_checkpoint`, SHA-256
`8349c88556f684eaaed5d0ea296e465cddf85086c2d240d30644ecb2e7436625`.
Preserve evidence **(1, 42, 156, 48, 1)** and **two bridges**. Choose the source
from its bound `next_selection` archive; the report's `source` is the completed
focus and must not be reused as the next expansion target. The selected key is
`4270b94e85e15c2b76fb43fe6a320f98d3908c0020fa3a27e6daf5404c3831f5`.
The next investigation should retain this binding to an uncovered original,
inspect reusable interactions and saved alternatives, and distinguish local
closure from an original-input coverage gain.

Independent cold replay passes in **346.50085 s**, reproducing both workers
and every intermediate catalog without fresh discovery or reference search.
It checks all **3,830 reference nodes**, verifies both cofactor results and
confirms the seven previously interrupted states are now stored. All **233
tests** pass. The manuscript builds to **162 pages**, with no overfull boxes
or undefined references; all **64 previous proof blocks** are unchanged.
All **1,321 artifacts across 26 prior manifests** and all prior reference
payloads are preserved. The reference archive and global positive certificate
are byte-identical to the parent. The new manifest binds **40 artifacts /
4,103,023 bytes**, including the local/global frontier distinction and the
negative exact-overlap check on the next 32 candidate targets. Commands, source
fingerprints and concurrency notes are in
`experiments/results/cnf-session-frontier/validation.json`.


## 2026-11-15: signed-renaming exclusions and case-1120 expansion

The [new investigation](signed-renaming-filter.md) implements and checks a
necessary invariant for signed variable renaming. All 32 saved candidate
targets have different profiles: all 496 pairs are excluded, including the
three pairs with matching size counts. Equality is inconclusive; tests retain
a nonisomorphic equal-profile counterexample. Exclusion does not decide SAT,
rule out semantic equivalence, or justify efficient solving of every class.
The audit takes 0.03586 seconds including writing and changes no scheduler.

Two independent retained sequences each enter 64 states across two allowances,
store 54 patterns and reach a 5/4/9 Horn, zero-valid terminal. One first-batch
interruption is reentered and completed; nine final inputs remain unstored.
Coverage stays 66/83. The pending 25/96/309 split has targets 23/89/277 and
22/73/215. Resume it from `cnf-original-1120/report.json` using
`continue_cnf_original_1120.restore_checkpoint`, preserving evidence
(1, 42, 156, 54, 1) and two bridges. The linked record binds exact source and
report hashes and separates the pending selection from original case 1120.

Mean summed workers cost 18.01738 seconds, with 16.81073 seconds of preparation
and 0.91088 seconds of expansion. History grows 749,568 bytes to 777,986,048 bytes
and 42,268 patterns; the new delta is 38,073 compressed bytes. The reference
archive grows to 4,114 nodes with all 3,830 prior payloads preserved. The global
positive certificate remains byte-identical. Next priorities are convergence
after checked reduction, remaining preparation/cold costs, and checked local
continuations if repeated unfinished frames become dominant. No new speedup,
peak-memory saving or arbitrary-SAT complexity bound is asserted.

Independent cold reconstruction passes in **419.43195 seconds**, reproducing
both sequences and every intermediate catalog without fresh discovery or
reference search. All **238 tests** pass. All **1,361 prior artifacts / 27
manifests** and **3,830 previous reference payloads** remain unchanged. Cold
findings also identify actual reuse after reduction: an inherited two-variable
plan and the empty-CNF terminal, distinct from the newly recognized Horn
terminal. The manuscript preserves all 64 proof blocks and builds to 163 pages
without overfull boxes or undefined references. The checkpoint manifest and
`validation.json` bind the audit, results, source fingerprints and checks.


## 2026-11-15: mixed conditional terminals and preparation profile

The [new continuation](reduction-reuse-profile.md) resumes the exact pending
25-variable split inside case 1120's original-bound focus. It stores 35 patterns
and reaches a 7/7/19 zero-valid terminal outside Horn, dual-Horn and 2-CNF, plus
a 6/6/12 2-CNF terminal outside Horn, dual-Horn and both uniform-assignment
classes. The conditional pair closes; the enclosing focus remains open and
coverage stays 66/83. The next saved pair is 34/120/355, with pending targets
31/102/295 and 31/104/295. Sixteen first-batch interruptions are charged again;
thirteen final inputs remain unstored.

Ordinary workers cost 17.86459 seconds, including 17.31958 seconds preparation
and 0.34281 seconds expansion. A separate instrumented repetition locates the
remaining second-batch cost: 3.78143 of 4.78940 seconds recomputes all eight table
digests. Profiling timings are diagnostic, not a comparative speedup. Investigate
per-table costs and checked reuse of unchanged digests; changed tables and
cold authority still require validation. A key-ordered digest cannot generally
be updated by hashing newly appended rows alone.

History grows by 430,080 bytes to 778,416,128 bytes / 42,303 patterns. The union
delta occupies 18,876 compressed bytes and adds one split sidecar. All previous
reference payloads are preserved; reference nodes grow to 4,153. The global
positive certificate stays byte-identical. Resume `cnf-reduction-reuse/report.json`
through `continue_cnf_reduction_reuse.restore_checkpoint`, preserving evidence
(1, 42, 156, 55, 1) and two bridges. The linked record supplies source hashes,
commands, profile data, limitations and the distinction between focus and pending
interaction. No efficient arbitrary-CNF guarantee is inferred.

Independent cold replay passes in **417.85190 s**, checking every intermediate
catalog with fresh discovery and reference search disabled. It verifies all
**4,153 reference nodes**, preserves all **4,114 prior payloads** and all
**1,428 artifacts / 28 prior manifests**, and confirms exact reuse of the sixteen
completed false-cofactor certificates. All **238 tests** pass; the manuscript
builds to **163 pages** with all **64 previous proof blocks** unchanged. The
checkpoint manifest binds **65 artifacts**, with commands and limitations in
`validation.json`.

## 2026-11-15: live digest scans and closure of original case 1120

The [matched digest study](guarded-table-digests.md) resumes the 34/120/355 split
and closes the original-bound focus in one 32-entry batch. Six independent arms
(two reversed-order repetitions of copied full, live full and guarded live scans)
store identical patterns: 15 probe, 8 elimination, 6 binary-path, 2 family and
1 polarity. Coverage rises 66/83 to 67/83; no admitted input remains unstored.
History grows 405,504 bytes to 778,821,632 bytes / 42,335 patterns. The next open
original is case 1061, index 13, with source 39/167/519 and no pending split.

Mean copied/live-full worker costs are 12.68940/8.55304 seconds. Both hash every
row; this measures the effect of reading the owned database, not cached hash
reuse. The focus closes before any second expansion batch. A separate replay
of the exact append reuses seven unchanged tables but shows no average refresh
improvement (0.42716 guarded versus 0.42444 seconds full), with slower complete
sequences (6.22119 versus 4.71509 seconds). Preserve the regression. Favor live
full scans and investigate retaining the checked session across originals;
startup still consumes about 7.54 seconds and global preparation/coverage 69.47
seconds. Guarded initial count scans remain a smaller, explicitly charged overhead. No polynomial arbitrary-SAT or minimum-expansion result.

Resume `cnf-guarded-digests/report.json` via
`compare_cnf_guarded_digests.restore_checkpoint`; use `next_selection` because
`source` is completed. Detailed bounds, preconditions and validation are in the
linked investigation and checkpoint artifacts.

## 2026-11-15: checked state across original cases closes case 1061

The [original-transition comparison](original-session-handoff.md) replays the
completed case-1120 query, checks the binding to case 1061 and then compares
restarting with retaining that checked session. Two reversed-order repetitions
per method each store the same six probe patterns. Their two conditional chains
reach an inherited empty-clause contradiction. Coverage rises **67/83 -> 68/83**;
all admissions are complete. The raw new patterns are neither Horn, dual-Horn nor
2-CNF and accept neither uniform assignment. This is checked reduction to shared
contradiction evidence, not a new claim of tractability for their raw class.
The conditional residual is UNSAT, while original case 1061 has an independently
checked SAT model. Completing that residual covers one obligation of the original;
it does not refute the original formula.

Mean complete sequence time falls **18.99400 -> 11.61121 seconds (38.87%)**,
including the initial construction, stored-original query, original binding and
expansion. Worker-only time falls **8.56483 -> 0.94843 seconds**; this excludes
the common initial query. Retention ends with **3,100 / 108** checked pattern and
prepared objects, versus **2,453 / 11** after restart. Those separate cache counts
are not peak RAM. Persistent evidence is identical between methods. History
grows **77,824 bytes** to **778,899,456 bytes / 42,341 patterns**. The union delta
is **7,095 compressed bytes**; reference nodes increase **4,198 -> 4,413** and
positive coverage steps **3,518 -> 3,564**.

The next large live cost is global recomposition and navigation: final route
preparation plus coverage takes **69.64522 seconds**, versus **0.14447 seconds**
mean retained local expansion. Compare `CoverageIndex` with full composition on
exact appends, including complete catalog changes, implicit rules and pending
activation. The current transition consumes an already checked global selection;
it does not maintain that selector incrementally. Parent replay remains a
separate **119.01318-second** cold cost. No global minimum-expansion or uniformly
polynomial arbitrary-CNF guarantee follows.

Resume `cnf-original-handoff/report.json` through
`compare_cnf_original_handoff.restore_checkpoint`, preserving evidence
**(1, 42, 156, 56, 1)** and **two bridges**. Follow `next_selection`, since the
report's `source` is completed: **40/158/467**, original **case 1443**, retained
index **72**, no pending split. The linked record supplies exact source and
report hashes, costs, contracts and validation commands.

Independent cold replay passes in **514.17263 seconds**, reproducing all four
arms without fresh recognition or reference search and checking all **4,413
reference nodes**. All **4,198 prior reference payloads**, **1,567 artifacts /
30 prior manifests** and **91 historical source files** are unchanged. All
**249 tests** pass; the manuscript builds to **164 pages** with **64 previous
proof blocks** preserved. The new manifest binds **67 artifacts**. Cold validation
overlaps other checks and is not a speed comparison. The validation record also
preserves the corrected interpretation: conditional refutations do not imply
that the original is UNSAT; its SAT model is independently checked.

## 2026-11-15: retained global inventory and indexed original selection

[The global navigation comparison](indexed-original-navigation.md) replays the
saved six-pattern append without new acquisition. Retaining the checked inventory
reduces the complete measured two-query sequence **138.45321 ->
75.96089 seconds (45.14%)**, including initial
construction and both original selections. The final query alone falls
**65.45308 -> 1.40345 seconds**.
Most of the old cold global cost is repeated semantic checking.

**Next cost to remove:** complete route rebuilding still costs **1.12777 of
1.40345 seconds (80.36%)** in the warm full query. Original selection costs only
**0.07732 seconds**. Reuse the existing complete route-maintenance state during
fresh bounded expansion and global queries; do not prioritize more selector
micro-optimization. The index reduces graph visits (26,109 to six option-source
checks across two graphs), but it adds retained state and changes selection time
only slightly. All methods end with **20,270 / 2,916** checked pattern/prepared
objects; indexes additionally retain **13,055 / 13,054-node** graphs.

The new indexed selector preserves exact selections and uses full composition
for sources outside its original graph. Both indexed updates check only
**6 option sources**, but complete-sequence results against retained
full composition are mixed: **74.19371/73.95375 seconds** in the first repetition
and **75.46496/77.96803 seconds** in the second (indexed/full). Keep the index
optional. A mean from two variable observations does not establish a stable
net benefit or reduced peak RAM. Coverage remains **68/83**; this is replay of
previous work, not a newly completed original.

Resume fresh discovery from **`cnf-original-handoff/report.json`** using
**`compare_cnf_original_handoff.restore_checkpoint`**. Next is **40/158/467**,
original **case 1443**, retained index **72**, no pending split. Preserve evidence
**(1, 42, 156, 56, 1)** and **two bridges**. Keep the inventory and complete
maintained routes alive through a bounded sequence of new expansions and global
queries. Cold reconstruction, initial global checking and growth of retained
state remain open; no unrestricted-SAT efficiency bound follows.

Independent cold validation passes in **259.30996 seconds**, checking all
**twelve selections and coverage certificates** with the original algorithms on
fresh inventories and verifying all **4,413 reference nodes**. The copied
scheduler bodies match their frozen baseline after reversing only the closure
calls and extra argument. All **254 tests** pass; the manuscript builds to
**165 pages** with all **64 previous proof blocks** unchanged. All **1,634 prior
artifacts / 31 manifests** and **95 historical source files** are preserved.
The new manifest binds **32 artifacts**. Validation tasks overlapped, so cold
elapsed time is not a performance comparison.

## 2026-11-15: share maintained routes with global queries

[Maintained global queries](maintained-global-catalog.md) reduce mean updated
query time **1.52633 -> 0.23719 seconds (84.46%)** while performing the same
full composition, plan checks and original selection. Both methods retain the
same inventory and route maintenance; the baseline rebuilds another catalog.
The **complete short sequence regresses 70.96985 -> 71.79572 seconds (1.16%)**:
initial checking varies more than the warm-query saving. Preserve that result;
measure longer retained sessions before claiming a total-cost improvement.

Fresh expansion stores **27 patterns** and closes the selected residual of
**case 1443**. One cofactor reaches an inherited contradiction after two probes;
the other uses 25 new nodes, interleaving binary-path reductions, elimination
and probes before a polarity change exposes a **Horn, zero-valid** terminal.
Coverage stays **68/83**: other original obligations remain. This shows a
composable reduction chain, not a new tractable class for every CNF.

**Next discovery target:** **40/163/490**, original **case 1190**, index **31**,
no pending split. Keep the checked inventory and complete maintained catalog
alive across several such residuals, measuring startup amortization. Investigate
repeated reduction chains using exact certified edges, not shape similarity.
**Largest complete-cost gap:** parent restoration **124.46543 seconds** and
initial global checking/construction **67--69 seconds**; cold final coverage
is **71.74615 seconds**. These dominate the remaining **0.23719-second** warm
query. Positive-only stored proofs cannot certify negative frontier claims.
Within the first retained worker, preparation costs **1.04254 seconds** versus
**0.22849 seconds** local expansion; full-table digests alone cost **0.48173
seconds**, and a complete seed copy remains. Compare removing redundant
copying under the checked append boundary before further query tuning; retain
the earlier append-time guarded-digest regression.

Resume **`cnf-session-catalog/report.json`** using
**`compare_cnf_session_catalog.restore_checkpoint`**, report SHA-256
`f856409b5a58b402ccf6f545dc8570cae22952a79b2b06460a8f68ab2635e10b`.
Use `next_selection`, not the completed `source`. Evidence is
**(1, 42, 156, 57, 1)** with **two bridges**. History is **779,272,192 bytes /
42,368 patterns**, up **372,736 bytes**; delta **438,272 bytes / 20,280 compressed**.
Both methods end with **710 routes**, no pending targets, and
**20,297 / 2,916** checked pattern/prepared objects. Catalog sharing adds no
persistent index; peak RAM is unmeasured. Reference nodes grow **4,413 -> 4,481**;
positive coverage stays **3,564 steps**. Guards preserve acquisition ledgers and
reject stale authority, but rely on immutable caller-owned cached objects.

All **259 tests**, independent replay of **eight global queries**, prefix
catalog checks and reference validation pass; all **64 previous proof blocks**
are preserved. The detailed validation record binds previous artifacts and
sources. No unrestricted-SAT complexity or minimum-expansion bound follows.

## 2026-11-15: batch copies and continued conditional discovery

[The batch-copy comparison](expansion-without-batch-copy.md) stores **82 new
pattern records** across four bounded expansions: 30 eliminations, 27 probes,
17 binary-path reductions, three family terminals and five unresolved records.
The terminals include Horn/zero-valid and 2-CNF cases, but overall coverage stays
**68/83**. The sequence charges **105 admission entries**, including re-entry;
twelve final entries remain unstored. Recognized endpoints do not imply cheap
recognition or acquisition of every ancestor.

**Retain the negative result:** omitting all per-batch seed copies avoids
**3,118,911,488 logical copied bytes**, yet mean four-worker time regresses
**4.61350 -> 6.28484 seconds (36.23%)** and the complete sequence regresses
**75.23972 -> 77.78679 seconds (3.39%)**. Both methods still hash all historical
tables and retain identical evidence. The first digest without a copy takes
about **3.28 seconds**, versus **0.44--0.50 seconds** after copying; later scans
are similar. OS/cache causality is unmeasured. Keep the copied-seed default;
test copying the first batch only during subsequent fresh discovery. That
combined policy has not been measured and cannot inherit a speedup by adding
times from separate runs.

**Resume** `cnf-copyless-sequence/report.json` with
`compare_cnf_copyless_sequence.restore_checkpoint`, report SHA-256
`0cf43154fba97eae8b971d700b7381fa671d2347aac4f45a41300ad208e1dcfd`.
Use **`next_selection` with its pending split**, at **26/94/284**, not the initial
`source`. Preserve evidence **(1, 42, 156, 63, 1)** and **two bridges**. Initial
binding is original **case 1190, index 31**; retained selections have an empty
original-index list. Cold validation checks actual dependency ancestry rather
than inventing a selector binding. Such a path does not transfer SAT truth or
complete the original's other obligations.

**Largest total-cost gaps:** initial global checking/construction remains
**67--69 seconds**, parent restoration **129.01658 seconds**, and final cold
coverage **71.31630 seconds**. Warm query cost is only **0.25 seconds**, plus
**0.31 seconds** output serialization. Reuse the checked session, then investigate
complete cold authority and resumable unfinished work. Persisted positive
coverage alone cannot certify the unresolved frontier. For broader discovery,
track certified reduction chains and the interaction left after each terminal,
not just family labels or matching shapes.

History grows **1,085,440 bytes** to **780,357,632 bytes / 42,450 patterns**;
the union delta is **1,175,552 bytes / 52,938 compressed**. Both methods retain
**20,379 current / 2,916 prepared checked objects**, with no measured peak RAM.
Reference nodes grow **4,481 -> 4,750**. Failure-only archives preserve committed
rows as explicitly unchecked evidence and cannot become verified checkpoints.
All **266 tests**, independent acquisition-prefix and twenty-query replay, and
reference validation pass. No unrestricted-SAT or minimum-expansion bound follows.

## 2026-11-15: checked canonical order and the next original

[Checked canonical-source reuse](checked-canonical-sources.md) closes
**case 1190**, raising structural coverage **68/83 -> 69/83**, and stores **25
new records**. Twelve eliminations, seven binary-path reductions, four probes,
one polarity change and one Horn/zero-valid terminal complete the pending split.
The terminal has **8 variables / 10 clauses / 27 literals**. All twelve formerly
unstored states now have records; the batch enters and stores 25 states.

The new representation check avoids sorting and renaming only after scanning
the source and proving that its order and compact labels already satisfy the
old normal form. It keeps exact keys, maps, certificate policy and stored bytes;
other sources fall back to the original normalizer. No retained cache is added.
Two reversed-order repetitions reduce the **complete startup-and-expansion
sequence 71.96107 -> 68.45498 seconds (4.87%)**; initial global preparation drops
**69.51709 -> 65.98742 seconds (5.08%)**. These are development-case measurements,
not a held-out or unrestricted-SAT guarantee. Both methods keep the batch copy;
the preceding copy-removal regression remains unchanged.

**Next discovery target:** **40/165/494**, original **case 1227**, retained index
**38**, no pending split. Resume **`cnf-canonical-source/report.json`** with
**`compare_cnf_canonical_source.restore_checkpoint`**, report SHA-256
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`.
Use **`next_selection`**, not the completed `source`. Keep evidence
**(1, 42, 156, 63, 1)** and **two bridges**. The restorer and independent replay
still use the original normalizer; the new inventory is an optional equivalent
implementation for subsequent comparisons and discovery.

**Largest remaining costs:** parent restoration **134.48837 seconds** and
initial global checking still dominate. A cold profile places normalization
at about **20% of instrumented query time**; unit fixed-point reconstruction
is the larger individual primitive. Investigate repeated source-bound checking
and sharing of immutable structure before expanding caches. The existing probe
cache evicts often, but repeated use of those evicted keys has not been measured.
Check whether already validated authority can survive restoration into startup.
A positive certificate does not establish complete negative frontier information.

The candidate accepts **28,169 / 48,182** canonicalization calls and still pays
**20,013** fallbacks. It replaces 11,031,610 old-normalizer input-literal charges
but adds 16,666,740 precheck visits; these counts are not a total CPU-work saving.
History grows **319,488 bytes** to **780,677,120 bytes / 42,475 patterns**. Delta:
**380,928 bytes / 14,120 compressed**. Both methods retain **20,404 / 2,916**
checked current/prepared objects; peak RAM is unmeasured. Reference nodes grow
**4,750 -> 4,802**. All **274 tests**, independent eight-query/prefix replay and
reference checking pass. No previous proof blocks or experiment sources change.

## 2026-11-15: retain checked evidence through replay

[Checked checkpoint replay](checked-checkpoint-replay.md) removes repeated node
verification across the latest five append checkpoints and their startup query.
Two reversed-order runs reduce **replay plus startup 94.29444 -> 87.70659 seconds
(6.99%)**. Suffix replay falls **28.92930 -> 24.22978 seconds (16.24%)**; startup
falls **65.36514 -> 63.47681 seconds (2.89%)**. Node verifications fall
**28,059 -> 23,320**, avoiding **4,739 repeats (16.89%)**. Both arms keep full
archive/source identity checks, ten full table-digest scans, all delta/positive
checks and the complete global query. These are development-history observations.

The live verifier carries exact checked immutable dependencies through guarded,
conflict-checked appends. Failed appends roll back and invalidate it. External
changes, unexplained own-connection writes and policy/schema changes reject reuse;
exclusive file/connection ownership and immutable Python cache objects remain
requirements. No trust cache is persisted. Positive coverage does not establish
complete negative frontier information, so startup still builds and queries the
complete catalog. The fresh control uses the same merge guards and discards
verifiers between phases; the independent audit uses the frozen old restorers.

There are **no new pattern rows or coverage gains** in this replay experiment.
History remains **780,677,120 bytes / 42,475 patterns**, structural coverage
**69/83**, and reference evidence **4,802 nodes**. The candidate carries **1,027**
checked nodes into startup. Both arms finish with **23,320** checked nodes, also
their maximum recorded count. This is not a process-RAM measurement; retaining
objects longer and auxiliary caches still cost memory. All **283 tests** pass.

**Next priority:** resume structural discovery on **case 1227, index 38**, at
**40 variables / 165 clauses / 494 literals**, with no pending split. The verified
acquisition checkpoint remains **`cnf-canonical-source/report.json`**, SHA-256
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`; use its
**`next_selection`** and **`compare_cnf_canonical_source.restore_checkpoint`**.
Keep evidence **(1, 42, 156, 63, 1)** and **two bridges**. This run changes replay
machinery only, so it does not replace that acquisition checkpoint.

Cold startup still costs about **63.48 seconds**; older parent restoration is
separate (observed **114.50 seconds**, overlapping tests before measured arms).
Extend checked reuse into earlier checkpoint schemas only after verifying their
contracts. A further specific gap is repeated expanded-certificate traversal and direct
semantic rule checking: later positive checks still cost about **2.6 seconds** even when they verify
zero new inventory nodes. Measure source/evidence binding and decoding before
adding another cache. Current evidence supplies no unrestricted-SAT bound.

## 2026-11-15: conditional refutation and shared terminals

[Conditional refutation with a shared terminal](conditional-refutation-reuse.md)
closes **case 1227**, raising structural coverage **69/83 -> 70/83**. A saved
split exposes two chains of three and two new probe reductions. Both reach the
same existing contradiction terminal. Two independent runs store the same
**five new records** in one advance, with no interrupted admissions. This is
exact terminal reuse and a new covered original, not a new tractable SAT class.

Mean local expansion costs **0.15935 seconds**, the complete worker **1.18892
seconds**, and the full sequence **68.83255 seconds**. Initial construction,
global checking and serialization still cost **66.68418 seconds**; the separately
charged parent restore is **140.08953 seconds**. These repeated development runs
do not establish a speedup against another solver. Structural history grows
**73,728 bytes** to **780,750,848 bytes / 42,480 patterns**. Reference evidence
grows **4,802 -> 5,182 nodes**, adding **3,702,784 SQLite bytes**; that validation
cost remains separate from the structural delta. Peak RAM is unmeasured.

**Next discovery priority:** **case 1406, index 64**, **40/168/505**, no pending
split. Resume **`cnf-case1227/report.json`** with
**`continue_cnf_case1227.restore_checkpoint`**, report SHA-256
`240f8151528c19ef69cac3b958abfc489710ffa1961944799d957545ff10f722`.
Use **`next_selection`**, not the completed `source`. Preserve evidence
**(1, 42, 156, 64, 1)** and **two bridges**. Thirteen originals remain unresolved.

Cold checking remains the dominant measured cost. Continue discovery through
retained sessions where possible; extend checked replay only with its exact
source, policy and immutable-dependency guards. Similar reduction chains do not
supply proof transport between different CNFs, and a short refutation on this
case supplies no uniform acquisition bound for arbitrary SAT.

## 2026-11-15: retained discovery across original scopes

[Discovery across retained original scopes](retained-discovery-sequence.md)
raises structural coverage **70/83 -> 72/83**, covering **cases 1406 and 1195**
before continuing into **case 1062**. Two independent four-batch runs store the
same **63 records**: 19 probe reductions, 27 eliminations, 13 binary-path
reductions, one family terminal and three unresolved records. They charge **74
admission entries / 71 distinct inputs**; three entries repeat interrupted work,
and eight inputs still have no stored record.

The first two selected residuals are UNSAT, while their original formulas are
SAT. Their checked paths include earlier conditioning, so local refutation does
not transfer SAT truth to the original. A later **4/5/14** terminal is both
zero-valid and one-valid, but neither Horn nor 2-CNF. It does not close case 1062's
remaining branches. Classification coverage and SAT decision remain distinct.

Mean four-batch sequence time is **73.47861 seconds**, including **66.09003
seconds** initial catalog/global checking, **4.17511 seconds** workers and
**1.02047 seconds** local expansion within those workers. The shared parent
restore costs another **145.39246 seconds**. One paid startup now serves all four
batches; no matched fresh-per-batch comparison or universal speedup is claimed.
History grows **856,064 bytes** to **781,606,912 bytes / 42,543 patterns**.
Reference evidence grows **5,182 -> 5,488 nodes**; peak RAM remains unmeasured.

**Next priority:** resume the pending split at **19/77/261**, within **case 1062,
index 14**. The selector's original-index list is empty for this retained work;
independent dependency-path checking supplies the scope. Resume
**`cnf-retained-discovery/report.json`** with
**`continue_cnf_retained_discovery.restore_checkpoint`**, report SHA-256
`0d59f8bb3018c78b5da947a31d1a0d492103c15968df7d706b7ad1910b038f84`.
Use **`next_selection` and its pending split**, not the initial source bound to
case 1406. Preserve evidence **(1, 42, 156, 69, 1)** and **two bridges**.

The touched prefixes have **75 occurrences / 64 distinct records**. Within
these prefixes across three original scopes, only the inherited contradiction terminal is shared;
**none of the 63 new records is shared across scopes**. This limits the current
cross-input reuse claim. Eleven originals remain uncovered. Continue the mixed reduction chains and
measure whether any nonterminal identities or exact boundary summaries can be
shared; matching reduction names alone is not such reuse. Keep unsuccessful
choices and eight interrupted input identities. Cold reconstruction and checking
remain the largest costs, and support further guarded reuse or a verified
materialized checkpoint. No compact closure or polynomial acquisition bound for
arbitrary SAT follows from these observations.

## 2026-11-15: materialized checkpoint reuse

[Materializing a checked checkpoint](materialized-checkpoint-reuse.md) reduces
measured reconstruction **155.45916 -> 9.94660 seconds**.
Including a fresh complete catalog and global query, mean startup falls
**220.33037 -> 74.76157 seconds (66.07%)**.
Two reversed-order repetitions reconstruct byte-identical databases, retain all
five evidence groups and two bridges, and select the same pending split.
This is a checkpoint-reuse result; structural coverage remains **72/83** and no
new patterns or reference proofs are acquired.

The optional compressed snapshot adds **87,337,082 bytes** of local disk storage.
Publication from an already checked history costs **7.88791 seconds**; a
separate authoritative reconstruction costs **150.88545 seconds**.
Both are charged. The fast path checks the complete database byte identity
before opening SQLite, all logical table digests, code/policy/parent bindings,
all sidecar bytes, bridges and the positive coverage proof. Complete catalog and
negative-frontier checking remain separate, paid startup work. A hash is useful
only relative to the descriptor bound by the reviewed experiment report.

**Next priority:** use the optional restorer in
`experiments.cnf_materialized_resume.restore_checkpoint` with
`experiments/results/cnf-materialized-checkpoint/report.json`, or the unchanged
`continue_cnf_retained_discovery.restore_checkpoint` with the acquisition report.
The final entry point additionally checks all **125 historical source fingerprints**;
this separately measured guard costs **0.01286 seconds**. All **299 tests** pass.
Both return the same acquisition state. Resume its **`next_selection` plus
pending split at 19/77/261**, case **1062 / index 14**, whose selector original-index
list remains empty. Preserve evidence **(1,42,156,69,1)**, **two bridges** and the
**eight interrupted input identities** in the acquisition artifacts. Eleven
originals remain structurally uncovered. With reconstruction reduced, complete
startup checking (64.49429 seconds) remains the largest repeated
cost; keep one checked session across further discovery batches. Investigate
shared nonterminal or boundary descriptions in the pending mixed reductions.
No compact closure or uniformly polynomial acquisition bound is established.

## 2026-11-15: complete the pending mixed reductions

[Completing the pending mixed reduction chains](pending-discovery-closure.md)
closes **case 1062**, raising structural coverage **72/83 -> 73/83**. Two independent
four-batch runs store the same **68 records**: 23 probes, 22 eliminations, 13 binary-path
reductions, three polarity transformations, five family terminals and two unresolved
intermediate records. They charge **84 admission entries / 68 distinct inputs**;
16 entries repeat interrupted work inside this sequence. All **eight earlier
interrupted inputs** and all newly interrupted inputs are now stored.

Three polarity transformations expose Horn terminals without reducing variables,
clauses or literals: **8/10/23**, **14/17/43**, **6/6/16**. A separate **9/18/49**
terminal is all-zero satisfiable but neither Horn nor 2-CNF. These are applications
of existing checked rules, not new tractable classes. The first 19-variable branch
closes before another 36-variable branch is selected; selected size alone is not
monotone progress. Original coverage requires all outstanding structural premises.
The original and all four touched split sources are **SAT**; classification coverage
is separate from SAT decision.

Mean complete sequence time is **70.46120 seconds**, including
**63.74848 seconds** startup and **0.84877 seconds** local
expansion. Checked materialized parent restoration adds **8.70349 seconds**.
History grows **843,776 bytes** to **782,450,688 bytes /
42,611 patterns**; reference evidence grows **5,488 -> 5,612 nodes**. Peak RAM is
unmeasured. Repetition establishes reproducibility, not a matched speedup.

**Next priority:** **case 1121 / index 23**, **41/174/513**, no pending split.
Resume **`experiments/results/cnf-pending-discovery/report.json`** with
**`experiments.continue_cnf_pending_discovery.restore_checkpoint`**. Use
**`next_selection`**, not the completed initial 19-variable source. Preserve evidence
**(1,42,156,72,1)** and **two bridges**. Its default restorer uses the existing checked
materialization of its parent and then applies the new delta; independent audit
uses the original reconstruction chain with that cache disabled.

Touched prefixes reuse **two probe records and one contradiction terminal** from
the preceding case-1062 prefixes. The intersections with earlier cases 1195 and
1406 contain only that terminal. This supports reuse within a resumed original,
without establishing shared nonterminal representations between different inputs.
Across the six case-1062 batches in both checkpoints, **148 entries / 121 distinct
inputs** expose **27 repeated admissions**. All 121 records are now stored; preserving
unfinished control frames remains a possible way to avoid re-entry, with runtime
benefit still unmeasured. Ten originals remain uncovered. Continue discovery in a retained
session and measure actual shared identities or certified boundary descriptions.
No compact closure or uniformly polynomial arbitrary-SAT acquisition bound follows.

## 2026-11-15: a pending branch survives a complete admission ledger

[The next mixed-family sequence](case1121-discovery.md) closes cases 1121 and
1336, raising structural coverage to **75/83**, and stores **67 records**.
All 67 admitted inputs are eventually stored, yet case 1063 retains a pending
**22/89/309** split whose second branch has admitted zero inputs. Completed
serialization is not complete structural expansion. Preserve the pending split
alongside interrupted input identities. The same run checks a **14/16/34 ->
13/14/30** affine projection, including exhaustive boundary-model comparison.
History grows **913,408 bytes**; separate reference evidence grows **5,423,104 bytes**.
Resume the new `cnf-case1121-discovery` checkpoint's `next_selection` in a retained
session. Eight originals remain uncovered; neither cross-original boundary sharing
nor uniformly polynomial acquisition is established. Full costs, replay evidence
and preservation anchors are in the linked record.

## 2026-11-15: retained branches complete three more originals

[The case-1063 continuation](case1063-discovery.md) raises structural coverage
**75/83 -> 78/83**, completing cases 1063, 1371 and 1158 with **54 new records**.
Case 1063 needs three additional records after fifty had been stored; all nine
inputs interrupted later in case 1371 are also completed. Horn/2-CNF overlap and
a polarity transformation into Horn remain explicit. Case 1158's selected residual
is UNSAT while its original is SAT, preserving the need for checked conditioning
ancestry. History adds **733,184 bytes**, separate reference evidence **3,682,304 bytes**.
The next source is **1196 / index 36**, **43/181/549**, no pending split. Follow the
new checkpoint's `next_selection`. Five originals remain uncovered; exact prefix
reuse, full costs and validation are in the linked record. Coverage of this retained
corpus remains distinct from generalization to new CNFs and an arbitrary-SAT bound.

## 2026-11-15: the retained 83-source subset is complete

[The case-1196 sequence](case1196-completion.md) raises checked structural coverage
**78/83 -> 83/83**, using six batches with the existing per-batch limits. Both
repetitions store **144 records** on **147 admissions**; all interrupted inputs
are completed and the final source selection is null. Four small terminals and
two polarity maps pass exhaustive bounded checks. All 83 source formulas exactly
match the historical retained-policy misses, so this is development-set completion,
not a fresh holdout or a new full-corpus measurement. History adds **2,019,328 bytes**;
separate reference evidence adds **15,405,056 bytes**. Restore the completed
`cnf-case1196-discovery` checkpoint for combined-policy full-corpus checking and
then frozen-policy evaluation on new unlabelled inputs. Do not restart an old
pending source. Certified sharing beyond terminals, paid trace acquisition and
generalization remain open; no arbitrary-SAT polynomial bound follows.


## 2026-11-15: checked union of the full historical corpus

[The explicit policy union](full-corpus-coverage.md) checks **1,497/1,497 historical
inputs**, including **985/985 non-tiny cases**, without acquiring new states. Every
source is bound to its own policy configuration and positive proof. Four fresh
processes pass; all **306 tests** pass. Mean replay is **46.48527 s** with historical
restoration and **11.22907 s** from an **11,271,594-byte compressed** standalone
bundle. Historical acquisition remains charged; the bundle adds storage and
cannot resume expansion. Peak RAM is unmeasured.

The old successful set shares **67 nonterminal steps** up to eighteen variables
after duplicate roots are collapsed, whereas the old/new policy proofs share
only twenty tiny family steps. The next experiment should test whether these
larger edit-family components reduce acquisition on unseen edits and mixtures
under a frozen policy and budget. This closes the combined historical-replay gap,
not generalization, globally minimal expansion or unrestricted polynomial SAT.


## 2026-11-15: transfer control separates reuse from early family exposure

[The 42-input study](subsumption-transfer-controls.md) finds that the candidate
shared eighteen-variable source reduces to 2-CNF. Twelve template transfers are
valid, but an early-family control needs no template and bypasses probing on
33 inputs. Coverage remains **41/42**; fresh probes fall **1,022 -> 503**, new
patterns **197 -> 107**, working SQLite **2,510,848 -> 1,466,368 bytes**, and mean
preparation plus queries **0.49636 -> 0.38107 s**. Two repetitions and a constructed
sample establish no general speedup or arbitrary-SAT bound. All **318 tests** pass.

The inherited admission counter does not cover fused-conditioning `_discover_profile`
entries: the initial diagnostic finds eighteen recorded nodes outside it in each
arm. Historical “32-state” counts refer to that ledger, not a global acquisition
bound. Preserve this correction and count actual stored and unfinished states.
The largest remaining cost is new input 41, a **48/204/612** random CNF with 272
probe attempts and unknown coverage. Inspect its persistent frontier, retaining
the frozen inputs and all previous results. The original 83-source checkpoint
remains complete and must not be restarted.


## 2026-11-15: complete admission exposes the unresolved interaction

[The corrected admission layer](complete-admission-frontier.md) accounts for both
acquisition entrances before profile computation and keeps all old proof formats.
At allowance 32 it avoids **40 fresh probes**, producing the **same 107 stored
patterns and 41/42 coverage**. No storage gain is claimed. At allowance 4096 the
last query returns normally on 391 admissions and 357 new patterns, but still
has one connected **38/165/502** selected residual at depth zero. This is the next
structural target, bound in `cnf-complete-admission/selected-frontier.json` to the
original 48-variable input; the generous archive is the next restoration source.

Four preserved 32-state restarts add 79 patterns to the previous 107 but repeat
33 admissions and remain capped. Investigate checked persistence of unfinished
profiles and transient restrictions. A complete state ledger does not bound
verification, repeated visits or total time. All 323 tests and sixteen cold
archives pass; the old 83-source checkpoint remains complete and unchanged.


## 2026-11-15: a saved-pair ranking counterexample and 42/42 coverage

[The equal-budget pair comparison](transfer-split-selection.md) closes the last
transfer input via residual variable 14, with 13 new records and 30 probes. The
initial smaller-cofactor choice, variable 6, remains open after 45 probes. Of four
saved pairs, only variable 14 closes both children: one reduces to two 2-CNF
components and the other to a contradiction. Testing all four costs 38 admissions
and 188 probes per repetition. This is adaptive completion, not a holdout or a
uniform arbitrary-SAT result.

The union checkpoint preserves 477 patterns and all four alternatives; all 42
originals have checked coverage and `next_selection` is null. Restore
`cnf-transfer-split/checkpoint.json` through its validator's restoration helper.
Next investigate indicators or reusable bounded lookahead that predict these
propagation cascades on newly frozen inputs. Cold history verification dominates
local expansion, and source-only controls show no fresh-probe reuse benefit for
the initial pair. All 327 tests and thirteen cold archives pass; no old source,
proof block, result or incomplete alternative is deleted.


## 2026-11-15: lookahead reuse exposes a candidate-availability gap

[The frozen 24-input study](lookahead-bank.md) finds no saved source pairs on
22 selected residuals at conditioning depth zero: their binary-clause count is
zero. Only two connected mixtures exercise saved-pair ranking. An optional checked
probe bank avoids 36 repeated probes, but lookahead still uses 106 probes versus
72 for size ranking, chooses the same pairs, stores more bytes and adds no original
coverage. No arm is capped. The bank is not enabled as a default optimization.

Next acquire a common candidate pool through charged ordinary conditioning or
broader source assumptions before comparing ranking. Keep both polarities,
verification and persistence in the cost account. The new 24 depth-zero unknowns
are distinct from the completed previous 42-input stream. All 331 tests and the
seed plus eight comparison archives pass cold checks; all previous proofs and
results remain intact. This is no unrestricted-SAT or negative SAT verdict.


## 2026-11-16: broader candidates and repeated split verification

[Exact source conditioning](bootstrap-conditioning.md) supplies candidates for all
24 selected residuals, including those without binary clauses. Both unit-closed
branches are checked and persisted before expansion. Under the supplemental
workflow comparison, enumeration covers 5/24 versus ordinary depth one's 4/24,
with 3,946 versus 5,699 probes and 558 versus 737 new patterns. It takes longer:
7.41975 versus 6.13657 seconds for the query stream. First and size selection each
cover 2/24. Source assumptions are charged separately from recognition admissions;
ordinary restarts the original while external routes reuse depth-zero ancestors.

The immediate reuse opportunity is exact incremental split verification: a
separate diagnostic reproduces the graph and finds 3,913 checks for 86 distinct
records. Rebuilding all earlier routes after each pair causes the quadratic sum.
Cache immutable checked evidence with exact policy/source binding, retain pending
child dependencies, and preserve independent cold replay. Then attack the nineteen
uncovered originals through deeper interactions and better component/pivot choices.

The union checkpoint retains 1,154 patterns, 96 pairs, 17 missing children and
5/24 coverage. All 335 tests and eleven cold archive checks pass. The initial
validator's archive-path collision was repaired with byte-identical original seed
reconstruction; the failure and recovery are preserved separately. The final
checkpoint and all earlier results remain usable. No arbitrary-SAT efficiency
bound, SAT/UNSAT verdict or new Lean refinement is claimed.


## 2026-11-16: incremental split checking removes repeated route work

[The matched registry comparison](incremental-split-checking.md) reduces mean
query time 7.41290 -> 4.26395 seconds and split checks 3,913 -> 258, while preserving
candidate choices, 3,946 probes, 558 new patterns, all archive bytes, positive
proofs and 5/24 coverage. Live metadata is additional; there is no persistent-space
or peak-RAM reduction. Cold proof checking is unchanged. All 341 tests and nine
cold archives pass, including pending-child activation without a new pair,
invalidations and acquisition-free replay.

The next discovery target is case 16, the largest mean unresolved query after
optimization: 0.31922 seconds, 205 probes and 27 admissions, below the cap. Its
59-variable / 245-clause / 743-literal selected component has four saved splits
with all eight child records present, but none covered under the full retained
union. Follow existing reductions and investigate deeper interaction; do not
repeat these acquisitions. Cases 17 and 22 are useful uncapped controls.

Restore the unchanged 1,154-pattern / 96-pair parent union, using the exact source
and branch bindings in `cnf-split-registry/next-discovery.json`. The enumeration
comparison's 643-pattern histories contain fewer alternatives. All previous
results and 64 proof blocks remain intact; nineteen current originals remain
unknown. No unrestricted-SAT efficiency claim follows from the runtime saving.


## 2026-11-16: nested conditioning closes case 16

[The deeper continuation](nested-conditioning-discovery.md) raises current
coverage 5/24 -> 6/24. All 59 first-level source pivots leave the original uncovered
under the fixed recognizer and flat history; nesting eleven new pairs below the
saved pivot 7 closes it. The original proof has twelve conditional nodes, depth
five, 265 unary reductions and nine family leaves. This is branch-dependent
conditional exposure with reductions, not a fixed five-variable backdoor or a
minimum-depth result. Only the canonical contradiction is shared, on five paths;
no broad nonterminal reuse is demonstrated.

Nested work uses 2,403 probes, 275 patterns and 22 source assumptions, versus
2,291, 272 and 110 for the unsuccessful flat control. The successful final
resumption adds 27 patterns and 215 probes with no fresh source assumption,
retaining 248 earlier new patterns. All 345 tests pass. Every primary batch archive
and the union have acquisition-free cold proofs; all old artifacts and 64 proof
blocks remain unchanged.

Resume from `cnf-nested-refinement/checkpoint.json`: 1,701 patterns, 162 pairs,
17 inherited missing children and 6/24 coverage. Preserve the flat control's
unsuccessful records as well. Case 16 is complete; next test the adaptive policy
on case 17's 60-variable / 255-clause / 765-literal component, with case 22 as a
control. Eighteen originals remain unknown. The main discovery gap is predicting
useful adaptive reduction paths; the 265 unary proof steps are a supporting
storage/checking target. Neither finite success nor shallow observed depth implies
uniform polynomial expansion on arbitrary SAT.


## 2026-11-16: transfer the policy and measure the value of added history

[The unchanged nested policy](case17-policy-transfer.md) closes case 17 in one
batch, raising coverage to 7/24. Both the full union and the pre-case-16 control
produce identical acquisitions, choices and target proofs: 89 new patterns, nine
pairs, eighteen source assumptions and 531 probes. None of the 547 patterns or
66 pairs acquired for case 16 contributes to the new proof. Seven older pattern
steps still contribute. This is policy transfer on development data, not evidence
of broad cross-input reuse of nonterminal components.

The checked 96-step proof has ten conditional nodes, 84 unary reductions, two
constant family leaves and maximum conditional depth six. Only the contradiction
is shared, on ten paths. There is no fixed six-variable backdoor or minimum-depth
claim. Full-history startup plus cold replay costs 11.50553 seconds, versus
0.62379 seconds local expansion. Mean full-stream time is 12.86418 versus 8.59953
seconds for the older-history control; the arms start with different coverage and
check different amounts of evidence. A checked source-local working view with
exact global fallback is a supporting opportunity, not an implemented speedup.

The preservation union keeps 1,790 patterns, 171 pairs, seventeen inherited
missing children and a 446-step proof for seven originals. All 345 tests and
independent checks of both parents, four trial archives and the union pass.
Seventeen originals remain unknown. The next bound discovery target is case 22's
disjoint binary mixture with a 48-variable residual. Test policy transfer and
separate easy-component reuse from random-core closure. No arbitrary-SAT
efficiency bound or new Lean refinement follows from this finite experiment.


## 2026-11-16: root-complete checking closes the disjoint mixture

[The optional scoped registry](scoped-refinement.md) preserves all reachable
ordinary and split routes, while deferring unrelated semantic checks to the full
cold audit. Both modes use the complete history and unchanged acquisition policy.
Case 22 closes with nine new patterns, two pairs, four source assumptions and
29 probes, raising coverage to 8/24. Acquisitions, choices, proofs and archive
bytes match across two reversed repetitions. Whole-stream time falls 12.59685 ->
6.94722 seconds (44.85%); mean process RSS falls 21.83%. No persistent bytes are
saved. Startup still scans global identities and historical row maps.

The original proof has 32 distinct steps: one decomposition, three conditional
nodes, 26 reductions and two family leaves. Twenty-three steps were retained and
nine are new. An easy nine-variable 2-CNF component is separate from the random
core's four contradiction leaves. Only the contradiction is shared; depth three
is not a fixed backdoor or a minimum-depth guarantee. All 351 tests pass, including
pending activation, interrupted resume, relevant corruption and writer/policy
invalidation. The complete parent, four trial archives and union pass independent
acquisition-free checks. A scoped live query alone does not validate unrelated
history. All earlier artifacts, sources and 64 proof blocks remain intact.

The full union retains 1,799 patterns, 173 pairs, seventeen missing children and
a 477-step proof for eight originals; sixteen originals remain unknown. Case 23's
connected binary mixture is next, with a 59-variable / 255-clause / 767-literal /
width-four residual and eight present but uncovered saved children. Use the new
checkpoint and bound successor. Full cold checking now takes about 86% of scoped
stream time; sharing a guarded session and complete audit across queries is the
next cost opportunity, requiring a separate matched test. No uniform arbitrary-SAT
efficiency bound, new Lean refinement or new SAT/UNSAT output API is claimed.


## 2026-11-16: grouped audits close three originals with a memory tradeoff

[Sharing the complete audit](grouped-checkpoints.md) closes cases 23, 18 and 15,
raising coverage 8/24 -> 11/24. Both workflows add 147 patterns and 21 pairs with
42 source assumptions and 707 probes. Each query proof is checked independently
on its exact snapshot; every intermediate archive remains stored. Full auditing
moves from every batch to group end, reducing sequence time 24.13644 -> 11.65332
seconds (51.72%). All acquisitions, proofs and snapshot bytes match. Unrelated
corruption detection is delayed; the grouped intermediate archives are not
globally certified during execution. Final publication requires the full audit.

Mean peak RSS rises 7.70%, from 453.58 to 488.51 MB, and persistent bytes are
unchanged. Preserve this regression. A separate retrospective validator fully
checks all twelve prefixes, original bindings, immutable history and reachable
catalogs; its 165.97-second validation cost is outside paired stream timings.
All 356 tests pass. Earlier artifacts, source files and 64 proof blocks remain
unchanged; no inference default or new Lean refinement is introduced.

The connected input closes through eight conditional nodes and 63 reductions,
with no decomposition step. Its leaves expose contradiction and a five-variable
2-CNF. The random cases add Horn/zero-valid and zero/one-valid family overlaps.
Depths four, four and five are branch-dependent, not fixed backdoor sizes. Only
the contradiction is shared within each proof; no later proof uses a newly
acquired pattern from an earlier query. The saving is audit reuse, with broader
nonterminal reuse still open.

The union retains 1,946 patterns, 194 pairs, seventeen inherited missing children
and a 665-step proof for eleven originals; thirteen remain unknown. Resume from
cnf-grouped-checkpoints/checkpoint.json. Case 19 is next, with a 58-variable /
276-clause / 841-literal / width-four residual and eight present, uncovered saved
children. One final full audit still takes 59.6% of sequence time; compression
takes 17.0%. Investigate checked parent reuse plus new-record verification with
explicit trust and fallback, and profile memory before growing groups. No
unrestricted-SAT efficiency bound or SAT/UNSAT output claim follows.

## 2026-11-16: case 19 closes; checked canonical form trims the full audit

[Canonical cold auditing](canonical-cold-audit.md) closes case 19 with 35 new
patterns, five pairs, ten source assumptions and 135 probes in one batch.
Coverage rises **11/24 -> 12/24**. The 42-step proof has six conditional nodes,
35 reductions (28 probes, four binary-path steps, three eliminations) and one
contradiction terminal. It reuses seven retained pattern steps and one split.
Maximum conditional depth is three, with changing coordinates, not a fixed
backdoor of size three. Only contradiction is shared within the proof; 48
unfolded occurrences become 42 steps. Larger reusable components remain open.

A profile of the frozen parent identified repeated normalization as a cost.
The optional complete auditor now uses the existing checked canonical-source
fast path in all verifier views. Every actual source is scanned; fallback keeps
the old normalization. It still independently verifies every node, split,
original binding and coverage proof. No parent-validity flag or warm cache is
trusted, and acquisition remains forbidden during checking. Earlier negative
checker-index experiments are preserved, not repeated without new evidence.

Four alternating-order paired runs give audit time **6.75146 -> 6.46583 seconds
(4.23%)** and whole-stream time **8.20199 -> 7.88948 seconds (3.81%)**. All
acquisitions, proofs and corresponding snapshot hashes match. Mean peak RSS
increases **589,824 bytes (0.153%)**; persistence is unchanged. The fast path
accepts 3,316 calls and falls back on 2,692. It adds precheck work, so the saving
is avoided sorting/renaming rather than fewer counted literal visits. The full
audit still consumes **82.0%** of stream time; compression takes about **9.0%**.

All **360 tests** pass. Independent retrospective replay checks all eight trial
archives, positive proofs, original bindings, complete reachable catalogs and
immutable prefixes; parent and union replay also pass. This research validation
takes 119.72 seconds, outside operational means and partly concurrent with the
test suite. All previous 290 sources, 3,290 artifacts and 64 manuscript proof
blocks remain unchanged. There is no inference-default change or new Lean proof.

The new union retains **1,981 patterns / 199 pairs / 17 inherited missing children**
and a **706-step positive proof for twelve originals**. Twelve remain unknown.
It occupies **37,580,800 SQLite bytes / 1,883,472 gzip bytes**, growing by 696,320
and 49,145 bytes respectively relative to the parent. Restore
`experiments/results/cnf-canonical-audit/checkpoint.json`.

**Next discovery target:** case **6**, random 3-CNF, selected residual
**36 variables / 148 clauses / 444 literals / width three**. All eight children
of its four saved pairs exist. The false child of saved pivot **13 is already
covered**, while its true child is not; the other six children are also uncovered.
Inspect and reuse that covered side before further acquisition. Historical
costs rank this target; they do not predict a new runtime bound. Keep broader
nonterminal reuse and conditional-depth growth as discovery gaps. Audit work
remains dominant; avoid assuming that more caches or weaker validation will
improve it. These finite measurements do not establish efficient arbitrary SAT.

## 2026-11-16: saved splits expose a minimum-cost selection counterexample

[Case-6 split-history control](saved-split-reuse.md) raises coverage **12/24 ->
13/24** and exposes a failure of the current remaining-literal heuristic. The
complete parent already selects pivot 13 and skips its covered branch. This
route adds **74 patterns / 547 probes / ten source assumptions**. An isolated
copy omitting only the four source-split records, while retaining every pattern
and every other split, reconstructs pivot 11 and adds **63 patterns / 345 probes /
twelve assumptions**. Both close in one batch. The intervention changes saved
selection information and certificate reuse together; it is not an empty-history
solve or a reason to discard history generally.

Visible remaining-literal scores for pivots 11,15,8,13 are 796,820,758,409.
An acquisition-free diagnostic replacing this by distinct uncovered obligations
changes no choice at twelve remaining source nodes. Do not implement that
ineffective fix on this parent. The better next test retains all alternatives
and charges bounded downstream simplification trials, reusing every admitted
state before committing further budget. Consult existing lookahead experiments
and retain regressions. Minimum visible frontier is not minimum future cost.

Two reversed paired runs give whole-stream **8.07061 vs 7.82088 seconds**, and
mean peak RSS **410,058,752 vs 384,090,112 bytes**, retained versus control.
The retained route has 17.46% more new patterns and 58.55% more probes, but slightly
faster local expansion (0.24952 vs 0.25645 seconds). It has more SQLite bytes but
a 1,275-byte smaller gzip snapshot. Cost dimensions disagree; no general speed,
memory or compression claim follows. Complete auditing still takes about 82%.

The retained/control proofs have **86/76 steps**, conditional depth **5/4**, one
component decomposition each, and contradiction, 2-CNF and Horn/zero-valid
terminals. Neither depth is a fixed backdoor-size claim. Their new pattern and
split sets are disjoint: the union retains all **137 new patterns / ten new split
identities**, with no new nonterminal reuse between these two routes. The
control's first split matches a historical identity but was reconstructed.

All **363 tests** pass. Frozen independent replay checks both initial variants,
all four trial archives and the union, plus query proofs, original bindings,
reachable catalogs and immutable per-variant prefixes. Successful validation
takes 88.50 seconds outside operational means; an earlier next-pointer failure
and its code are preserved separately. Missing optional roots are now checked
before composition and remain unknown. All earlier 294 sources, 3,338 artifacts
and 64 proof blocks remain unchanged.

Restore `experiments/results/cnf-saved-split-reuse/checkpoint.json`: **2,118
patterns / 209 pairs / 17 inherited missing children / 13 of 24 originals covered**,
with a **779-step proof** and **39,448,576 SQLite / 1,970,166 gzip bytes**.
Eleven originals remain unknown. Next is **case 11**, with a selected **45-variable /
196-clause / 608-literal / width-five** residual. Eight saved children are present
and uncovered. Its depth-zero original root exists; its optional depth-one root
does not. No inference default, Lean proof or arbitrary-SAT bound is changed.

## 2026-11-16: a charged pilot improves downstream route selection

[Testing two saved routes](pilot-refinement.md) closes case 11 and raises coverage
**13/24 -> 14/24**. The optional pilot completes one nested acquisition on each
of the two best saved routes before committing. All work shares the ordinary
128-admission / sixteen-operation batch allowance. Partial trials stay on their
arm until complete and survive cold restart. The current implementation requires
an unresolved source below a unary selected root prefix and two saved choices;
it is not a general component scheduler. Exact closure uses the frozen checker.

Initially pivot 6 has score 1106 and pivot 32 has 1118. The pilot spends **three
admissions / 28 probes** on the first, leaving three obligations and 1535 literals,
and **seven admissions / 27 probes** on the second, leaving one obligation and
559 literals. It selects pivot 32, and one further acquisition closes the original.
All losing-trial results remain stored. The older failed one-profile lookahead
and the case-6 counterexample remain preserved.

Committed/pilot totals are **44/19 new patterns, 178/77 probes, eighteen/six source
assumptions and nine/three new splits**. Both close in one batch. Two reversed
paired runs give expansion **0.27211 -> 0.11072 s (59.31%)**, whole stream
**8.23501 -> 7.85315 s (4.64%)**, and mean peak RSS **388,456,448 -> 382,541,824
bytes (1.52%)**. Total SQLite/gzip size falls 1.17%/1.43%. Full auditing still
uses 84.0% of candidate time, compression 9.5%, and expansion 1.4%. Do not scale
acquisition savings into total-cost or unrestricted-SAT claims.

The control proof has **53 steps / depth five**, the pilot **29 steps / depth two**.
Both use conditional nodes and unary reductions to expose contradiction, with
no component decomposition. The pilot proof uses sixteen new and thirteen
parent steps; its three losing-trial patterns are unused but retained. The arms
share exactly those three exploratory patterns and one split; no new pattern
is common to both final proofs. This is not broader nonterminal or cross-input
reuse. Depth uses changing local coordinates, not a fixed backdoor-size bound.

All **367 tests** pass, and independent frozen replay checks the parent, four
trial archives, query proofs, reachable catalogs, budget accounting, cold pilot
recovery and the union. Validation takes 75.45 seconds outside operational means,
partly concurrent with tests. All earlier 298 sources, 3,378 artifacts and
64 proof blocks remain unchanged. No default solver or Lean theorem changes.

The union keeps **2,178 patterns / 220 pairs / seventeen inherited missing children**,
with an **807-step positive proof for fourteen originals**; ten remain unknown.
It occupies **40,517,632 SQLite / 2,037,803 gzip bytes**, retaining sixty distinct
new patterns and eleven splits from both arms. Restore
`experiments/results/cnf-pilot-refinement/checkpoint.json`.

**Next test:** transfer the unchanged pilot and committed control to case **13**.
Its selected residual is **47 variables / 213 clauses / 649 literals / width four**.
All eight saved children exist; pivot 41's true child is covered, the other seven
are not. Both original roots exist. Check the unary-prefix precondition and
charge all trial work. Broader replication is needed before adopting the pilot;
known negative controls and worst-case acquisition/space gaps remain open.

## 2026-11-16: pilot transfer exposes the cost of an unnecessary trial

[The unchanged pilot on case 13](pilot-transfer.md) raises structural coverage
**14/24 -> 15/24**, but gives the same 38-step proof as committing immediately.
Both choose saved pivot 41. Committed/pilot totals are **27/37 new patterns,
128/179 probes, six/eight source assumptions and three/four splits**. The pilot
inserts exactly one alternative trial after the first operation, then performs
the same continuation. Its ten extra patterns add no measured corpus coverage
and are unused by this proof. They remain stored; future reuse is unproven.

Local expansion rises **37.18%** (0.13244 -> 0.18168 seconds), peak RSS **0.40%**,
SQLite **0.41%** and gzip **0.53%**. Whole-stream means are 8.33858/8.24283 seconds,
but the two paired comparisons disagree on the faster mode. Do not claim the
small mean difference as a reliable total-time gain. Complete auditing remains
about **83--84%** of time. Both modes use the same full parent, frozen policy,
shared budgets and independent checks; this is a known development input.

The proof uses four conditional nodes, 32 unary reductions and two terminals:
contradiction and a five-variable dual-Horn/one-valid residual. Eleven steps and
one split predate this continuation; 27 steps and three splits are new. Only
contradiction is shared within the proof. Depth four uses changing coordinates,
not a fixed backdoor bound. Identical proofs on the same original do not establish
new cross-input reuse, and structural coverage is not a SAT/UNSAT output API.

All **367 tests** pass. Frozen independent replay checks the parent, four trial
archives, union, query proofs, original bindings, reachable catalogs, immutable
prefixes, cold pilot phases and shared budgets. Validation takes 76.24 seconds
outside timing, partly concurrent with tests. The acquisition-free preflight
costs another 0.15935 seconds separately. All 302 prior sources, 3,417 artifacts
and 64 manuscript proof blocks remain unchanged. Only a transfer driver is added.

Restore `experiments/results/cnf-pilot-transfer/checkpoint.json`: **2,215 patterns /
224 pairs / seventeen inherited missing children**, with an **844-step proof for
fifteen originals** and **41,099,264 SQLite / 2,073,167 gzip bytes**. Nine remain
unknown. Every losing-trial result is retained.

**Next:** decide when a second trial is worth acquiring, tested against committed
and always-pilot controls on **case 21, a connected binary mixture**. Its selected
residual has **45 variables / 201 clauses / 616 literals / width four**. All eight
saved children of pivots 2,1,23,17 are present and uncovered; only the depth-zero
original root exists. Check the pilot prefix precondition. A gate based on whether
the first trial reduces unresolved literal mass is a post-hoc hypothesis only:
case 11 grew 1106 -> 1535; case 13 shrank 610 -> 539. Freeze the gate before new
acquisition. The earlier case-6 counterexample rules out trusting covered-child
presence alone. No default policy or unrestricted-SAT guarantee changes.

## 2026-11-16: a progress gate avoids an unhelpful second route on case 21

[The optional progress gate](progress-pilot.md) closes the connected binary
mixture **case 21**, raising structural coverage **15/24 -> 16/24**. The rule was
frozen before acquisition: after one completed trial, skip the second if the
selected unresolved literal mass strictly decreases, or the query closes.
Otherwise use the unchanged two-route pilot. The baseline and partial work
survive restart; all work shares the same 128-admission / sixteen-operation
batch allowance. This is a scheduling heuristic, not a cost bound.

The first route at pivot 23 falls **1141 -> 1099 literals** after **eight
admissions / 53 probes**. The gate stops exploration. Always-pilot tries pivot
17 for **seven admissions / 52 probes**, seeing **1097 literals** and switching.
Gated and committed totals are **24 patterns / 100 probes / eight assumptions /
four splits**, versus **32 / 175 / twelve / six** for always-pilot. The gate
matches committed operations, proof and SQLite/gzip bytes. The two-literal
advantage did not justify extra exploration on this input.

The committed/gated proof has **42 steps**, five conditional nodes, 36 unary
reductions and six contradiction occurrences. Eighteen steps and one split
predate continuation; 24 steps and four splits are new. The pilot proof has
41 steps and uses 24 new proof nodes, but retains eight unused trial patterns.
The different final proofs share no new node. Only contradiction is shared
within each proof; neither decomposes into separate components. Both have
conditional depth three in changing coordinates, not a fixed backdoor bound.
A shorter final proof therefore need not be cheaper to acquire.

Against always-pilot, the gate reduces new patterns **25%**, probes **42.86%**,
local expansion **35.25%**, RSS **0.65%**, SQLite **0.40%** and gzip **0.57%**.
Whole-stream means are committed/pilot/gated **8.48923 / 8.75818 / 8.62917 s**.
Pilot/gated pair rankings disagree; the 1.47% lower mean is inconclusive. Gated
whole time is 1.65% higher than committed despite matching evidence. Full auditing
still consumes about 82--83% of time. Two triples, with pilot always in the middle
position, do not establish a robust timing advantage. Parent acquisition remains
charged in earlier results, and these are history continuations.

All **372 tests** pass, including five new checks of shared budgets, interrupted
trials, baseline retention, skipped/explored routes and cold restart. An initial
method-rebinding implementation error was fixed before measured acquisition;
its source and test failure are retained. Independent full replay checks six
archives, original bindings, complete catalogs, query proofs, prefixes, budgets
and scheduling state in 106.11 seconds outside operational timing, partly
concurrent with tests. Preflight costs 0.20920 seconds separately. All previous
303 sources, 3,453 artifacts and 64 manuscript proof blocks remain unchanged.

Restore `experiments/results/cnf-progress-pilot/checkpoint.json`: **2,263 patterns /
233 pairs / seventeen inherited missing children**, with an **884-step proof for
sixteen originals**. Eight remain unknown. The union retains every losing trial:
48 distinct new patterns and nine splits, using **42,033,152 SQLite / 2,131,824
gzip bytes**. No inference default, Lean theorem or SAT/UNSAT output API changes.

**Next:** transfer the unchanged gate and both controls to **case 10**, random
3-CNF with selected **45 variables / 180 clauses / 557 literals / width five**.
All eight children of pivots 20,3,17,22 exist and remain uncovered; only the
depth-zero original root is present. Check the prefix precondition. Look for an
early literal decrease that masks expensive continuation; a successful local
step is not a global potential or a minimum-cost certificate. Broader shared
nonterminal patterns and full-history audit cost remain unresolved.

## 2026-11-16: failed gate transfer reveals four exact nonterminal joins

[The unchanged transfer to case 10](progress-transfer.md) raises coverage
**16/24 -> 17/24**, but the gate follows always-pilot onto a more expensive route.
The first trial grows **1042 -> 1468 literals**, from two obligations to three;
its seven admissions and 64 probes trigger exploration. The second trial uses
ten admissions and 67 probes, leaving two obligations / 1040 literals. Both
pilots choose pivot 17. The committed control stays on pivot 22.

Committed versus either pilot: **106/119 new patterns, 653/778 probes,
eighteen/twenty-four assumptions and nine/twelve splits**. Both pilots have
identical operations, proofs and archived bytes. Gated local expansion rises
**17.79%**, peak RSS **0.65%**, SQLite **0.54%** and gzip **0.57%**. Whole-stream
means are committed/pilot/gated **9.31591 / 9.39216 / 9.41249 s**; two triples
do not establish a reliable small total-time effect. Complete auditing remains
78--79% of time. No policy or budget was tuned, and the gate remains optional.

The useful structural finding is four joins between the different final proofs.
They share **39 new nodes** with identical rules and children: **33 unary
reductions, four conditional nodes and two 2-CNF terminals**. The four exact
entry formulas have **27/32/39/4 variables** and disjoint new descendant regions
of **12/12/13/2 nodes**. Two entries follow elimination and two follow probing
from distinct parents. Their union includes one inherited contradiction and
has a **40-step positive subproof**, independently checked without acquisition.
Full keys, parent hashes, shapes and proof are preserved under
`experiments/results/cnf-progress-transfer/joins/`.

In particular, two different 40-variable / 151-clause parents with 460 and 457
literals eliminate to the same 39-variable / 153-clause / 475-literal formula.
Literal growth can accompany useful convergence. The exact cache can reuse the
saved result once reached; the open problem is recognizing and reaching that
boundary cheaply on a new input. Equality of shape or an approximate match
cannot substitute for the complete policy/depth/CNF key and checked mapping.
The observed joins concern two routes through one original, not cross-input
reuse. Direct whole-root reuse already handles repetition of this original.

The committed proof has 116 steps and depth four; pilot has 122 and depth six,
with six unused exploratory patterns. Depth uses changing local coordinates,
not a fixed backdoor bound. Their acquisitions share 45 new patterns and five
splits; their final proofs share 39 new nodes and four splits. Raw shared pattern
keys/payloads total 283,851 bytes plus 39,431 split bytes, excluding SQLite and
Python overhead. This is not a measured memory saving. Join analysis takes
0.18489 seconds outside benchmark timing; full retrospective replay takes
111.93 seconds, partly concurrent with tests. Preflight takes 0.17075 seconds.

All **372 tests** pass, and independent full replay checks six archives, original
bindings, query proofs, complete catalogs, prefixes, shared budgets and cold
state. All earlier 307 sources, 3,500 artifacts and 64 proof blocks are unchanged.
The post-hoc analyzer is separately source-bound; an initial SQL column-name
error and its source are preserved, and corrected certificate checking passes.
No solver, gate, inference default, Lean theorem or SAT/UNSAT output API changes.

Restore `experiments/results/cnf-progress-transfer/checkpoint.json`: **2,443
patterns / 249 pairs / seventeen inherited missing children**, with a **999-step
proof for seventeen originals**. Seven remain unknown. The union retains every
trial: 180 distinct new patterns and sixteen splits, using **44,810,240 SQLite /
2,271,560 gzip bytes**.

**Highest next reuse target:** test related inputs with previously unseen roots
that reach the saved elimination/probing joins, with edits that invalidate the
shared image. Compare matched histories and charge all recognition, boundary
verification, acquisition, persistence and cold replay. Avoid fitting another
scalar threshold to these cases. The independent discovery pointer is **case 7**,
with selected **33 variables / 152 clauses / 470 literals / width four**. All
saved children exist; pivot 14's true child is covered and seven remain open.
Only its depth-zero original root exists. No arbitrary-SAT efficiency claim follows.


## 2026-11-16: cross-input join transfer and clause-edit limits

[Cross-input join transfer](join-transfer.md) avoids **35 acquisitions and 154
probes** on 24 distinct constructed CNFs. The unchanged solver receives only
CNFs. Its two matched histories differ by exactly **39 saved proof nodes and
four splits**. All 24 query proofs match across histories; the second visit
acquires nothing. Acquisition falls **206 -> 171**, probes **1132 -> 978**.
Three first encounters account for the entire difference: twelve, ten and
thirteen saved nodes below the 27-, 32- and 39-variable joins. The small anchor
and two nodes above the useful 32-variable descendants remain unused.

**Highest next discovery target:** clause-deletion controls receive no
acquisition saving and account for **136/171 new patterns and 768/978 probes**.
Inspect constructed **case 13** (33 variables / 95 clauses / 274 literals /
width four, 29 new patterns / 218 probes) against its matching preimage. Determine
which clause dependencies block transfer, and seek an exact shared residual or
checked split transport. An edit invalidating one projection does not exclude
all reuse. Keep variable maps, boundary checks and proof dependencies explicit.
Original **case 7** remains a separate broader coverage control, with seven
open saved children and pivot 14's true child already covered.

**Largest measured whole-stream cost:** full cold auditing, about **52%** of
14.48/14.33 seconds. Mean solve/bookkeeping falls 4.48%, but whole runtime only
0.99%; two pairs do not establish a reliable small timing effect. RSS rises
0.168%, SQLite 0.091% and gzip 0.486%. The treatment ends with all control rows
plus four unused preloaded nodes. Seed preparation takes **16.014 seconds**
separately and historical acquisition remains charged. This is a local reuse
saving, not a demonstrated net acquisition-plus-use or memory improvement.

**Secondary opportunity:** some positive preimages miss their specified anchor
under the default reduction order despite a checked one-pair projection. Reuse
the earlier projection infrastructure cautiously; its expensive global-index
preparation and negative frontier results remain preserved. Do not tune a new
route heuristic on these 24 constructed cases alone.

Restore `experiments/results/cnf-join-transfer/checkpoint.json`: **2,614 patterns /
259 pairs / seventeen inherited missing children**, preserving all earlier rows
and all trial additions. Original structural coverage remains **17/24**, with
the same **999-step proof**. The separate 24 constructed inputs have a **208-step
proof**, bound by `supplemental_queries` and `supplemental_proof`. Preserve both
catalogs in later unions. Storage is **47,181,824 SQLite / 2,375,854 gzip bytes**.
All **376 tests**, four independent stream reconstructions and 192 query-proof
replays pass. Prior 309 sources, 3,550 artifacts / 61 manifests and all 64
manuscript proof blocks remain unchanged. Runtime binds 313 sources; the final
ledger also binds the post-hoc analyzer and supplemental replay checker (315). Synthetic structural
coverage does not imply efficient arbitrary SAT or supply SAT/UNSAT answers.
Checkpoint SHA-256: `5bd57b9b2bf1007a4b447764c40d8c4d920450f6f90699342926218c41b9a652`.
Report SHA-256: `98eb6b23f6bcb2d80c9dc7714bad65ce5de37c6fb0875cdd8e9ee7c4160cf346`.
The new manifest adds **38 artifacts**; the next audit inherits **3,588 artifacts /
62 manifests**. The manuscript builds to **186 pages**.

## 2026-11-16: checked UNSAT reuse under clause deletion

[Checked clause-deletion guards](clause-deletion-guard.md) reduce new reference
residual nodes **502 -> 427 (14.94%)**, decision splits **200 -> 174**, and complete
stream time **1.27860 -> 1.17492 seconds (8.11%)** on twelve constructed edits.
This is a separate SAT decision experiment with the unchanged `ResidualSolver`,
not a structural-coverage increase or a new production policy. Six retained
UNSAT proofs justify forcing the removed clause false; six SAT premises decline.
Both modes return nine SAT and three UNSAT answers, independently replayed.

**Highest next target:** positive witness transfer. Edits **19, 21 and 23** use
**364/427 remaining reference nodes**, although their undeleted formulas are SAT.
The analyzer verifies that all six retained SAT-template models satisfy their
edited inputs. Implement checked witness reuse before fresh search, preserving
the UNSAT guard and an ordinary control. Charge matching, model checking and
persistence. The current wrapper does not yet use this positive transfer.

**Limits exposed:** case 13 remains at **22 reference nodes / eleven splits**
after forcing two variables; this is distinct from its earlier 29 structural
patterns. Case 7 uses two more splits. Cases 15 and 17 supply 67 of 75 avoided
nodes, reducing **43/26 -> 1/1**. The general exceptional cofactor can remain
arbitrary SAT: `F = H AND NOT x AND x` is cheaply UNSAT, while deleting `x` and
forcing it false leaves arbitrary `H`. The underlying clause-deletion reasoning
is established in transition-clause/MUS work; no new complexity claim follows.

**Accounting:** preparing the common 613-node reference seed costs **0.91359 s**
separately. SQLite falls 6.42%, but compressed database plus raw query sidecar
increases **760,368 -> 810,993 bytes**. Two repetitions establish only this local
measurement; the small RSS change is not broad memory evidence. Cold archive
checking remains about 28% of stream time. Tests and retrospective validation
run outside the timed workers.

Resume `experiments/results/cnf-clause-deletion-guard/checkpoint.json`. It retains
the unchanged **2,614 structural patterns / 259 pairs / seventeen missing
children**, original **17/24 coverage / 999-step proof**, and separate **24/24
supplemental coverage / 208-step proof**. Its `reference_study` binding preserves
the new decision archives and guard sidecars; keep them on continuation.
All **382 tests**, all four reference streams and all **96 query-result replays**
pass. The analyzer also checks the hardness construction on all 512 two-variable
CNFs. Runtime binds 319 sources; the final ledger binds 320 with the analyzer.
All prior 315 sources, 3,588 artifacts / 62 manifests and 64 proof blocks remain
unchanged. Original case 7 remains the separate structural discovery pointer.
Checkpoint SHA-256: `e182f0023fc82ecb8ec674cbdc33c913ca91a104066b0a6d67c72812f8ea6b05`.
Report SHA-256: `70507d8854ddf5d7110b00c16604f5956e452e9003fb4af2cd011deb71f5b005`.
The new manifest adds **32 artifacts**; the next audit inherits **3,620 artifacts /
63 manifests**. The manuscript builds to **187 pages**.

## 2026-11-16: checked SAT witness reuse and new deletion candidates

[Checked SAT witness publication](clause-witness-reuse.md) removes the dominant
positive-query search on the twelve constructed edits. Relative to the UNSAT
guard alone, fresh reference expansions fall **427 -> 59**, with **six answer
publications / 65 new stored rows**. Whole time falls **1.19691 -> 0.59381 s
(50.39%)**, RSS **18.15%**, and SQLite **40.27%**. Ordinary solving needs 502
expansions and 1.26932 s. All modes return nine SAT and three UNSAT answers;
all repeated visits add zero rows. These are conditional decision measurements,
not structural-coverage gains or an unrestricted-SAT guarantee.

**Highest next discovery target:** previously unseen deletions of the UNSAT
templates. Existing twelve roots are now cached. A seven-attempt, one-variable
model-rotation screen finds two valid new-input witnesses from case 9, both for
**28 variables / 81 clauses / 238 literals**, with absent reference roots.
Flipping variable 260 leaves only `(-230,120,260)` false; flipping 150 leaves
only `(-100,150,160)` false. Their complete CNFs and models are preserved in
`rotation-screen.json`. Publish/check these candidates and test a fixed broader
set of neighboring deletions against ordinary and guard controls, charging
all failed proposals and full or indexed clause checking. This uses established
model-rotation reasoning; no rotation speedup has yet been measured.

**Retained failures:** case 7's three flips leave two or three clauses false;
both case-13 flips leave three. Case 13 still needs 22 of 59 fresh reference
expansions. No SAT witness supplies an UNSAT conclusion. A checked negative
premise still leaves an exceptional cofactor that can contain arbitrary SAT.

**Dominant measured costs now:** complete reference checking and compression,
about **68%** of the shorter stream. Database gzip plus raw query sidecar is
**676,971 bytes**, versus 811,502 guarded and 760,874 ordinary. Sidecar size alone
increases. All modes inherit the same 613-node seed, whose acquisition cost of
**0.91359 s** remains separate; this run's seed preflight costs **0.18338 s**.
Three triples balance position, but these remain development examples.

Resume `experiments/results/cnf-clause-witness-reuse/checkpoint.json`. Its new
`reference_union` retains **1,169 distinct keys**, using **5,931,008 SQLite /
450,067 gzip bytes**. No reference key is newly discovered relative to the
combined previous arms; alternate valid SAT certificates remain in the trial
archives, and the union keeps earlier payloads. Preserve `reference_study`,
`witness_reuse_study`, `reference_decisions` and the separate rotation proposals.
The structural authority remains **2,614 patterns / 259 pairs / seventeen
missing children**, with original **17/24 / 999 proof steps** and supplemental
**24/24 / 208 proof steps**. Original case 7 remains its discovery pointer.

All **388 tests**, nine new stream reconstructions / **216 query replays**, the
four prior streams and the reference union pass. The control databases match
the prior study byte for byte. All prior 320 sources, 3,620 artifacts / 63
manifests and 64 manuscript proof blocks remain unchanged. Runtime binds 324
sources; the post-hoc rotation screen raises the final ledger to 325.
Checkpoint SHA-256: `79c224246b77270980ddb5685ab32464df19057dfe95a7db976a5b18019de63b`.
Report SHA-256: `3005787a6d6eb257b19ee39a7b4cd33137384f93ec0f3c2547142b31bfd254d2`.
The new manifest adds **49 artifacts**; the next audit inherits **3,669 artifacts /
64 manifests**. The manuscript builds to **188 pages**.

## 2026-11-16: bounded model rotation and negative proof-support gap

[Bounded model rotation](model-rotation.md) reduces fresh reference expansions
**1,876 -> 1,509 (19.56%)** on **257 previously uncached deletions** of three
checked UNSAT templates. It publishes 57 checked SAT certificates, making 1,566
new rows. Complete runtime falls **11.28948 -> 10.48075 s (7.16%)**, mean peak RSS
**3.86%**, and SQLite **4.15%** against the guarded control. Ordinary solving uses
6,126 expansions and 27.82621 s. All modes agree on **72 SAT / 185 UNSAT**;
repeated visits add no rows. Three process triples balance mode position.

**Highest next target: reusable negative proof supports.** UNSAT queries consume
**1,216/1,509 expansions (80.58%)**, unchanged by rotation. Old template 12
accounts for 612 of these, with new deletion-catalog case 11 alone using 47.
The exact inputs, removed clauses and target hashes are retained in
`cost-attribution.json`. Determine whether checked UNSAT certificates expose
small clause supports or shared negative cofactors that transfer to further
queries by checked containment. Do not assume that failed rotations identify
UNSAT, or that two individually safe deletions can be combined safely.

**Retained limits:** 189 flips yield 99 singleton-false outcomes and 90 failures.
Of these, 57 publish absent keys and 42 reach old ones. Only 37 first query
encounters use a published direct answer; publication count is not avoided-solve
count. The first two templates hit 64-flip caps with six queued flips each;
the third exhausts its chosen-witness queue after 61 flips. Alternative witnesses
can open different routes. All attempts, origins, models and cursors persist;
cold certificate replay works, while engine-state import/resume remains open.

**Storage remains a gap:** combined database gzip and raw sidecars is 9,921,762
bytes, below guarded 10,419,742 but above ordinary 8,541,670. Guard sidecars repeat
whole stronger CNFs. The durable union preserves all old payloads and adds
7,935 distinct keys: **9,104 keys / 32,595,968 SQLite / 2,524,507 gzip bytes**.
Smaller arm memory does not mean smaller total retained history. One-witness
rotation has a bounded scan budget, not a uniform efficient SAT guarantee.

Resume `experiments/results/cnf-model-rotation/checkpoint.json`. Preserve all
inherited reference studies/decisions and the new `model_rotation_study`,
`model_rotation_decisions` and `reference_union`. Structural authority remains
**2,614 patterns / 259 pairs / seventeen missing children**, original **17/24 /
999 proof steps**, and separate supplemental **24/24 / 208 proof steps**.
Original case 7 remains its independent structural discovery pointer.

All **394 tests**, nine cold archive checks / **4,626 query replays**, rotation
origins and every union node pass. Earlier twelve reference decisions also
replay unchanged. Selection/preflight costs 0.35307 s separately; earlier
acquisition costs remain in historical records. These are constructed
neighboring inputs including known positive candidates, not a blind holdout.
Runtime binds 329 sources; the post-hoc attribution brings the final ledger
to 330. All prior 325 sources, 3,669 artifacts / 64 manifests and 64 manuscript
proof blocks are preserved.
Checkpoint SHA-256: `1049220a45fe5de68b1d3657ffd86dd0ea8ed0fd7202120324f94472b4304e1a`.
Report SHA-256: `91b60f9fb1b3403cae305cc5a23df6f76cc0a8aa92d772b084c281de0fd36535`.
The new manifest adds **54 artifacts**; the next audit inherits **3,723 artifacts /
65 manifests**. The manuscript builds to **189 pages**.

## 2026-11-16: checked negative supports and their accounting cost

[Checked UNSAT supports](unsat-support-reuse.md) recognize new negative inputs by
exact containment in a retained refutation core. On **192 unseen double
clause deletions**, the full bank certifies **40 UNSAT queries** by this route
and cuts fresh expansions **524 -> 355 (32.25%)**. However, complete runtime
rises **28.51440 -> 39.96590 s (40.16%)**, mean peak RSS **28.15%**, and SQLite
**23.74%**. The regression occurs in all three repetitions; this remains an
optional experiment. All modes return **102 SAT / 90 UNSAT**. The small
three-core bank saves only five expansions and has no reliable runtime gain.

**Highest next target: exact incremental archive accounting.** A separately
profiled warm pass spends **5.80760 s** copying full row inventories and
**3.45805 s** recomputing archive size: **84.55%** of its **10.95876 s** loop.
Core matching takes only **0.01618 s**. Replace per-query full-history scans
with checked append-only deltas and maintained size totals, preserving a full
final audit. Then compare further unseen edits using the **already persisted
core bank** and identical full initial unions. Charge initial core acquisition
and retained storage explicitly; no amortized break-even has been shown.

**Structural gain and limit:** all 188 known negative sources yield 145 distinct
supports. The original templates shrink 82 clauses to 64 and 63, and 96 to 80.
Derived nodes use the frozen verifier and existing certificate format. A failed
match never implies SAT or UNSAT. Supports are not minimal, arbitrary renamings
are not searched, and the acquired proof DAG can still be exponential. The
full bank leaves **328 negative / 27 positive** fresh expansions.

**Retained compression evidence:** removing dominated supports leaves **121**
and preserves the recognized family for every superset query. Its required
preparation graph shrinks **4,092 -> 3,804 nodes**; this candidate has not been
benchmarked. Only **10/4,102 preparation nodes** are unused by the current full
bank and query proofs, so simple pruning offers little. No rows were deleted.
The main cost is real retained proof data plus repeated accounting over it.

Resume `experiments/results/cnf-unsat-support/checkpoint.json`; the bound study
points to `all-0/cores.json`. Preserve inherited studies and decision catalogs,
plus `unsat_support_study`, `unsat_support_decisions` and `reference_union`.
The union retains **13,869 keys / 43,380,736 SQLite / 3,479,528 gzip bytes**.
The new catalog has **139 direct certificates and 53 explicit guarded cofactor
records**; never substitute a cofactor key for the complete query identity.
Structural authority remains **2,614 patterns / 259 pairs / seventeen missing
children**, original **17/24 / 999 proof steps**, and separate supplemental
**24/24 / 208 proof steps**. Original case 7 is its separate discovery pointer.

All **403 tests**, nine cold archive checks / **3,456 trial query replays**, the
support screen, every union node, 269 inherited decisions and all 192 new
decisions pass. Earlier 330 sources, 3,723 artifacts / 65 manifests and 64 proof
blocks are preserved. Runtime binds 334 sources; post-hoc attribution and warm
profiling bring the final ledger to 336. These are constructed development
inputs, not independent evidence for uniformly efficient arbitrary SAT.
Checkpoint SHA-256: `07e1a04864038caf4ba5a60b388e8c22b1c90116d9b11d819e7b7bd7dd7d31cf`.
Report SHA-256: `f732924b833023efc8f3a52a33071bdff524d7abc105790eed8f41c8bfb4fdba`.
The new manifest adds **60 artifacts**; the next audit inherits **3,783 artifacts /
66 manifests**. The manuscript builds to **191 pages**.


## 2026-11-16: exact insertion deltas over persisted proof graphs

[Incremental archive accounting](incremental-archive-accounting.md) removes the
full-history query scans identified by the previous profile. On the next **192
unseen double deletions**, complete time falls **37.48164 -> 14.81201 s (60.48%)**,
and query time **23.96449 -> 1.37640 s (94.26%)**. All modes use the same retained
145-core bank and 13,869-key seed; initial extraction remains charged separately.
The existing ledger accounts for an 18.65% complete-time reduction; adding the
new guarded insertion cursor saves a further 51.42%. Full inventories fall
**772 -> 3**, with final preservation and cold proof checks retained.

**Regressions and boundaries:** peak RSS rises **9.56%** to 448,435,541 bytes.
Accounting adds 4 KiB SQLite / 696 gzip bytes; logical proof rows are identical.
The cursor requires an exclusively owned append-only session, detects external
commits/schema changes and rejects local rewrites. Opening, conflict repair,
full cold replay and compression remain charged. No proof-space compression,
new search algorithm, broader structural closure or amortized break-even is shown.

**Highest next cost target:** the unchanged cold audit is 67.95% of candidate
worker time, compression another 17.09%. A separate cold profile attributes
**7.21981 s** to **384 full archive-size censuses** within a **14.87488 s**
instrumented audit. Test one independently checked census for an immutable
snapshot while retaining every proof and query check. Also locate the RSS
regression before claiming a memory improvement. Do not mix instrumented and
unprofiled timings or add nested profiling categories.

**Next structural target:** all modes return 96 SAT / 96 UNSAT, with 41 core
hits, 96 witness publications and 55 guarded negative queries. Of these, 44
use fresh search, accounting for all **202 expansions**, including 56 splits. Cases 66 and 76 each use 16
expansions, case 41 uses 12. Inspect their shared supports/cofactors for further
reuse. Case IDs belong to this experiment's catalog. Repeated visits add no rows.
The antichain of 121 old supports remains an unbenchmarked alternative; it
preserves recognized supersets but need not reduce these unresolved searches.

Resume `experiments/results/cnf-incremental-archive/checkpoint.json`. Preserve
all inherited studies and decisions plus `incremental_archive_study`,
`incremental_archive_decisions` and `reference_union`. The new union retains
**14,208 keys / 44,781,568 SQLite / 3,563,875 gzip bytes**. Its new catalog has
**137 direct query certificates / 55 guarded cofactor records**; the latter
require source, guard and child together. Structural authority is unchanged:
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 proof
steps, separate supplemental 24/24 / 208, and original case 7's discovery pointer.

All **418 tests**, nine cold archives / **3,456 trial query replays**, every union
node, 461 inherited decisions and all new decisions pass. Preserve 336 earlier
sources, 3,783 artifacts / 66 manifests and all 64 proof blocks. Runtime binds
341 sources; the attribution and cold-profile tools bring the final ledger to
343. The manuscript builds to 192 pages without warnings.
Checkpoint SHA-256: `53cf74216546839373aeb00d7d14321be0617a3b35da4a2cefa086aa1ee6a02d`.
Report SHA-256: `9feaf6eb279c05a8355c19e1d855eba693946a9be536d8367e24e299acab0c89`.
The new manifest adds **48 artifacts**; the next preservation audit inherits
**3,831 artifacts / 67 manifests**.


## 2026-11-16: one census per cold proof snapshot

[Snapshot replay](snapshot-replay.md) replaces 384 repeated cold size scans with
one independent census on a pinned read-only view. It runs the same frozen
complete audit and verifier. On the next 192 unseen double deletions, mean
complete time falls **15.15167 -> 7.84969 s (48.19%)** and cold replay
**10.43075 -> 3.12634 s (70.03%)**. Four alternating process pairs preserve
identical expansion work and identical logical/physical proof archives. Peak
RSS rises **0.39%**; no memory or storage reduction is shown. The earlier delta
memory regression remains open.

**Current largest costs:** complete cold verification is **39.83%** of candidate
worker time, compression **33.07%**, query work **16.20%**, setup **9.56%**.
Further total-cost improvements need evidence about repeated proof normalization,
allocation or rewriting unchanged persistent evidence. Profile before choosing
another checker optimization; retain every logical check and all old certificates.
Snapshot totals are independently computed, not trusted from saved accounting.
The benchmark uses private closed clones and one owned process per audit; shared
service concurrency and hostile private-connection changes are outside scope.

**Next primary structural target:** **37 negative queries** still require fresh
search and account for all **270 expansions / 85 splits**. They belong to 40
guarded negatives; all modes otherwise use 54 core hits and 98 witness answers,
returning 98 SAT / 94 UNSAT. Cases 100, 41 and 188 use 21, 19 and 18 expansions;
original template 12 supplies 129/270. Compare refutation supports and guarded
cofactors across these cases. A full-query negative certificate requires checked
composition of the stronger UNSAT premise and the restricted child; treating
the child as the query is invalid. Charge construction, checking and persistence
when testing any transfer. The 121-core antichain remains unbenchmarked and
preserves existing superset coverage rather than expanding it.

Resume `experiments/results/cnf-snapshot-replay/checkpoint.json`. Preserve every
inherited study/decision field plus `snapshot_replay_study`,
`snapshot_replay_decisions` and `reference_union`. The union adds 422 keys and
retains **14,630 keys / 46,530,560 SQLite / 3,674,583 gzip bytes**. The new catalog
has **152 direct roots / 40 guarded cofactor records**; guarded replay binds the
source, guard and child together. All 384 earlier double-deletion answers were
excluded from selection, including those without direct roots. Do not multiply
speedups across different input sets or ignore earlier acquisition costs.

All **426 tests**, eight complete archive checks / **3,072 trial query replays**,
every union node, **653 inherited decisions** and all new decisions pass using
the ordinary solver for independent validation. All 343 prior source bindings,
3,831 artifacts / 67 manifests and 64 proof blocks are preserved. Runtime binds
347 sources; the post-hoc analyzer brings the final ledger to 348. The manuscript
builds to 193 pages without warnings. Structural authority is unchanged:
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
Checkpoint SHA-256: `86ed6d602def81787d3b1b88c9b3151f8ccba1929f223d73a279acd438bd2bfe`.
Report SHA-256: `0b5be879e1beeda66a27fef48fd42cfa3fa5f7df02cd73bdc6e8202fe0f9fe22`.
The new manifest adds **42 artifacts**; the next preservation audit inherits
**3,873 artifacts / 68 manifests**.


## 2026-11-16: checked support transfer between guarded cofactors

[Cofactor support reuse](cofactor-support.md) certifies **16 previously uncached
restricted subproblems** through checked clause containment. Fresh expansions
fall **234 -> 162 (30.77%)**, and query time **1.33223 -> 0.87849 s (34.06%)**.
But constructing the whole bank adds **1,310 proof nodes** and makes complete
time **7.93324 -> 9.75898 s (23.01% worse)**, peak RSS **9.23% higher**, and SQLite
**3.23% larger**. Every matched pair regresses in total time. Keep this optional;
fewer expansions do not establish an end-to-end gain.

**Highest next target: defer new support proofs until a match.** Preparation
visits 1,075 old negative proof nodes and constructs 112 raw supports; the
containment antichain has 104 and preserves every superset match. Only 14 of
those supports are used here. The full retained bank needs 1,272 preparation
nodes, but the matched supports and query proofs need only **118**. Simple
pruning saves at most 38 nodes; building only after a checked match is the more
credible next test. Support proposals alone must never justify UNSAT. Discovery,
materialization, checking and persistence must all remain charged. The policy
has not yet been implemented or measured; selecting only the 14 observed cores
would use future workload information and can lose coverage.

**Preserve and reuse this acquired bank:** its 104 cores are already materialized
in the latest union. Load `cofactor_support_bank` and its `cores` field for warm
runs instead of extracting them again. To evaluate a new construction policy,
use explicitly matched historical seed clones or newly discovered supports, and
retain an unseen stream; do not present already-paid construction as a saving.

**Coverage limits and remaining cases:** 145 of 148 inherited guarded decisions
are negative; the three SAT cofactors do not supply negative supports. The new
stream returns 84 SAT / 108 UNSAT, with 63 old full-query core hits, 83 witness
publications and 46 guards (45 negative, one positive). Six targets were cached.
All 72 avoided expansions come from the 16 new cofactor hits. Each measured hit
shares the guard clause of its first retained origin; cross-guard transfer is
covered only by a unit test. No broader cross-category coverage is established.
The candidate still performs 151 negative / 11 positive expansions on 24 cases.
New-catalog case 7 is SAT; it is distinct from original structural case 7.
Largest remaining negatives are new cases 191, 82, 112, 184 and 87.

Resume `experiments/results/cnf-cofactor-support/checkpoint.json`. Preserve all
inherited fields plus `cofactor_support_study`, `cofactor_support_decisions`,
`cofactor_support_bank` and `reference_union`. The union retains **16,320 keys /
49,610,752 SQLite / 3,953,721 gzip bytes**. Earlier payloads win overlaps; sixteen
alternate certificate occurrences remain in trial archives. The new catalog has
**146 direct roots / 46 guarded records**. Guarded decisions bind source, guard
and child together; a negative child alone is not the complete-query identity.

All **434 tests**, eight complete archive checks / **3,072 trial query replays**,
every union node, **845 inherited decisions** and all new decisions pass. All
348 prior sources, 3,873 artifacts / 68 manifests and 64 proof blocks are
preserved. Runtime binds 352 sources; the post-hoc analyzer brings the ledger to
353. The paper builds to 194 pages without warnings. Structural authority stays
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
Checkpoint SHA-256: `c27c247ca9b278ab7ce44fab7db020a933dc5dc1a688c4a3e01e5fc85c3c11f8`.
Report SHA-256: `6d2f204b3476475735747858344b2caaef52e86921b2e7fecf20672e21226692`.
The new manifest adds **50 artifacts**; the next preservation audit inherits
**3,923 artifacts / 69 manifests**.


## 2026-11-16: support proofs constructed on demand

[Deferred support construction](deferred-support.md) now implements the prior
highest-priority experiment. On a further 192 unseen constructed inputs, eager
and deferred policies transfer the same 19 supports to **23 novel targets** and
reduce fresh expansions **302 -> 177 (41.39%)**. Deferral constructs **209 rather
than 1,310** support-proof rows, cutting all new rows **1,648 -> 547**. Complete
time falls **11.43996 -> 10.30105 seconds (9.96%)** against eager construction,
but remains **9.21% above the old-bank control's 9.43274 seconds**. All three
matched triples have both effects. Keep the mode optional.

**What is established:** discovery returns the same 104-support antichain without
publishing derived proofs. A matched proposal must be materialized and checked
before the frozen subset rule can publish UNSAT. All 209 materialization rows
are used by this stream's query proof closure; 83 proposed roots remain pending
in the deferred trial. Eager construction retains 1,101 additional preparation
rows outside that query closure. This is measured liveness, not a minimum-proof
guarantee. No prior result is deleted. Guarded answers still require the complete
source--guard--child evidence.

**Cost limits:** mean query time is 19.22% higher than eager construction because
needed construction moves to the query, although complete time improves. Mean
RSS is 3.78% lower than eager, but paired differences change sign; no robust memory
gain is established. SQLite falls 2.92% and gzip 4.47% against eager. Relative to
the old bank, mean RSS rises 1.87%, gzip rises 0.17%, and raw sidecars add further
space. Discovery still costs **1.22612 seconds**, against **0.33067 seconds** of
query savings over the old bank. Cold replay and compression remain the largest
phases, at 34.94% and 29.71% of complete deferred time.

**Next acquisition target:** reuse persisted ready supports and source-bound
proposals, then profile incremental discovery on genuinely new negative sources.
Do not repeatedly re-extract the existing 104-core bank. Before another global
recognizer, inspect the **21 unmatched negative queries / 177 expansions** for
shared conditional supports, particularly template 8 (**90 expansions**). New
study cases 164 (20), 35/160 (17 each) and 16/136 (16 each) are the largest misses.
Every measured hit still shares its first origin's guard clause. Cross-guard
and broad cross-category discovery remain open; constructed neighbouring inputs
do not demonstrate an efficient partition of arbitrary SAT.

**Comparison scope:** all workers use identical historical **14,630-key**
pre-acquisition clones. Selection excludes all **768** previous sidecar answers
and complete roots from the **16,320-key latest authority**, which stays
preserved with its already-ready bank. This isolates a construction policy,
not savings from rebuilding an already-paid bank. The new outer timer includes
final digest and report generation; historical percentages are not composable.

Resume `experiments/results/cnf-deferred-support/checkpoint.json`. Preserve every
inherited field plus `deferred_support_study`, `deferred_support_decisions`,
`deferred_support_proposals` and `reference_union`. The union has **16,760 keys /
51,294,208 SQLite / 4,046,593 gzip bytes**, with 440 new keys and 46 alternate
certificate occurrences retained in trials. The new catalog has **138 direct
roots / 54 guarded negatives**. All 104 previously ready cores remain ready in
the final union; the 83 pending proposals describe only the historical trial.

All **442 tests**, nine full archive checks / **3,456 trial query replays**, every
union node, **1,037 inherited decisions** and all new decisions pass. Prior
**353 sources / 3,923 artifacts / 69 manifests** are unchanged. Runtime binds
357 sources and the analyzer brings the ledger to 358. Structural authority stays
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
All 64 manuscript proof blocks remain unchanged; no new Lean claim.
Checkpoint SHA-256: `711be45dc4a9e5a79c3c94aaac179ee1a44af1013ca364f9633df8fc97af20cc`.
Report SHA-256: `3c762d725a6e0f058e309a098f124334a38feee3f4e8856069a2a41a5974bbb7`.
The manuscript builds to 195 pages without warnings. The new manifest binds
56 artifacts; the next audit inherits **3,979 artifacts / 70 manifests**.


## 2026-11-16: incremental discovery and old evidence costs

[Incremental support discovery](incremental-support.md) reuses the saved index
and extracts supports only from newly acquired negative results. Adding **99**
new sources to **145** old ones gives exactly the same frontier as full
rediscovery: **168 raw supports / 151 retained entries**, up from 112 / 104.
Three superseded old entries remain in history. Pending proposals survive
restart and further extension; they cannot justify UNSAT before materialization
and ordinary proof checking.

**Coverage gain:** on another 192 unseen constructed neighbours, the expanded
index transfers **18 rather than 14** targets and reduces expansions
**199 -> 162 (18.59%)**. Cases 53, 121, 163 and 190 account for all 37 saved
expansions. Three materializations add 39 proof rows. All modes return
**105 SAT / 87 UNSAT**, including one guarded SAT result. Every measured transfer
still shares its first origin's guard clause; broad cross-category discovery
remains open. Both extension modes have identical logical/physical archives.

**Cost result:** incremental extraction visits **715 rather than 1,697** proof
nodes (57.87% fewer), but preparation only falls **1.82786 -> 1.78856 seconds**.
Complete time is **11.69363 -> 11.64076 seconds**, a near-flat **0.45%** difference,
with no demonstrated practical speedup or memory improvement. Against loading
the ready bank (**11.17962 seconds**), extension still regresses **4.12%**, in
every matched triple. Gzip plus raw sidecars grows **11,064,817 -> 11,617,440 bytes**.
Keep extension optional. This is a current-union comparison, not another
historical construction replay: all workers begin with **16,760 keys**, and
selection excludes all **960** prior sidecar answers and cached complete roots.

**Next highest-value gap: repeated checking of saved evidence.** The diagnostic
records **7,216 proof reads / 14,281 canonicalizations** for incremental discovery,
versus **6,783 / 13,518** for rebuilding. Old provenance and ready-core checking
offset avoided extraction. Separate active match requirements from full lineage
audit, retaining both: a checked negative core justifies subset reuse independently
of its discovery guard, while a pending proposal needs checked materialization.
Test demand-driven checks or reuse within an owned append-only session, retaining
invalidation and a separately charged complete cold audit. Do not persist unchecked
trust flags. The diagnostic overlapped the correctness suite; use its call counts
and structure, not its elapsed times. Timed workers ran alone.

**Remaining coverage probes:** 18 negative cases need 154 expansions; guarded
SAT case 188 needs eight. Template 8 contributes 66 expansions, template 6 adds
51 and template 12 adds 45. Largest new-catalog negatives are 61 (19), 72 and
142 (18 each), and 19 (14). Keep these distinct from original structural case IDs.
Cold audit and compression remain 34.93% and 29.74% of complete incremental time.
The 151-entry trial frontier has 104 available roots and 47 pending proposals;
these 104 available roots are a different set from the original 104 ready cores.

Resume `experiments/results/cnf-incremental-support/checkpoint.json`. Preserve
all inherited fields plus `incremental_support_study`, `incremental_support_decisions`
and `incremental_support_proposals`. The latter stores the complete extended
index (including all raw supports, origins and dominance), not just ready cores.
For the next extension, supply the five old decision catalogs in their existing
order and only genuinely new batches. Repeated batch identities reject. Use the
extended index to preserve acquired discovery rather than returning to the old
104-entry frontier. Match-time proof checks still apply to every pending root.

The union retains **17,161 keys / 52,809,728 SQLite / 4,124,643 gzip bytes**, adding
401 keys while keeping every earlier payload. Eight alternate certificate
occurrences remain in trial archives. The new catalog has **149 direct roots /
43 guarded decisions** (42 negative, one positive). All 104 original ready cores
remain in history; the extended frontier has 104 available roots and 47 pending
proposals in the union as well as the candidate trials.

All **451 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,229 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **358 sources / 3,979 artifacts /
70 manifests** remain unchanged. Runtime binds 363 sources; the post-hoc analyzer
brings the ledger to 364. Structural authority remains 2,614 patterns / 259 pairs /
17 missing children, original 17/24 / 999 steps, separate supplemental 24/24 /
208, and original case 7's discovery pointer. No new Lean or unrestricted-SAT claim.
Checkpoint SHA-256: `6c60e95e1a8f0f0dc12fc2e24dba38178cc35ae5e13a07a28d43b30d0180700c`.
Report SHA-256: `c5c12f205dd77b370d4120ce0baf06e33ab0ecc1268e2fa7d8ac14fbd4ef5275`.
The manuscript builds to 196 pages without warnings; all 64 proof blocks are unchanged.
The new manifest binds 63 artifacts; next audit inherits **4,042 artifacts / 71 manifests**.


## 2026-11-16: active support checks with full cold lineage

[Active support checking](active-support.md) avoids checking unrelated old
lineage before queries while retaining complete cold proof, query and provenance
audit. Mean complete time falls **11.52069 -> 10.36579 seconds (10.02%)** versus
eager checking, and **6.85%** versus the loaded-index control. Every matched
triple improves. Both extension modes retain identical proof archives and search
work; no logical check is replaced by an unchecked persisted trust flag.

**Why it is sound:** a match checks the actual core's canonical identity and
ordinary negative proof before subset publication. Missing roots require checked
materialization. The current query's guard remains checked online. The cold
auditor runs the unchanged full proof/query audit, then checks all index origins
and dominance on the same pinned snapshot before closing it, including on
failure. Historical lineage is deferred, not removed. All modes pay for the
complete audit; this timing boundary is broader than earlier benchmarks.

**Measured work:** active preparation normalizes **517,355** literal occurrences
rather than **1,904,438**, and makes **1,563** database lookups rather than **6,625**.
Preparation falls **1.78958 -> 0.51719 seconds**. Query time rises **27.91%** as
checks move to active use, but complete time improves. Mean peak RSS is **7.89%**
below eager and **5.06%** below loaded; paired eager differences change sign.
There is no asymptotic memory improvement or persistent-space saving. Gzip plus
raw sidecars rises **11,657,158 -> 11,894,676 bytes** against loaded.

**Negative discovery result:** 42 new negative sources expand the frontier
**151 -> 170 entries**, but all modes still make **25 transfers / 187 expansions /
64 splits**. There are **no additional target hits**. Index growth is not a
coverage measure. The active method has not been compared with active loading
without extension, so this run does not establish that growing the bank pays.
Reuse the acquired 170-entry index rather than rebuilding it for a later claim.

**Next coverage target:** template 12 accounts for **169/187** remaining
expansions, template 8 for 18 and template 6 for none. Fifteen negative queries
need 145 expansions; guarded SAT cases **137 and 2** need **26 and 16**. Largest
negatives are 29 (23), 140 (18), 116 (17) and 149 (15). These are new-catalog IDs.
Inspect shared conditional structure and retained SAT-witness repair/transfer
on these residuals, including genuinely different guards. Every measured support
hit still shares its first origin's guard clause. Broader cross-category coverage
remains open. For cost work, compare active loading before further acquisition;
complete cold audit and compression now cost **40.03% / 31.81%** of active time.

All modes return **97 SAT / 95 UNSAT**, with 95 witness publications, 51 old
full-query core hits and 46 guards (44 negative, two positive). Four targets are
cached. Extension uses 22 supports for 25 transfers and materializes four roots
through 13 proof rows. Its frontier has 106 ready roots and 64 pending proposals.
The comparison uses the latest **17,161-key** union, excludes all **1,152** prior
sidecar answers and complete cached roots, and visits 192 new constructed
neighbours twice in three balanced process triples. This is not an arbitrary-SAT
benchmark, minimum-expansion result or uniform-polynomial guarantee.

Resume `experiments/results/cnf-active-support/checkpoint.json`. Preserve all
inherited fields plus `active_support_study`, `active_support_decisions` and
`active_support_proposals`. Load this complete 170-entry index, including pending
entries and its raw-support/origin history. Its six source catalogs stay in their
existing order; a subsequent extension must supply only a genuinely new batch.
The union contains **17,532 keys / 54,337,536 SQLite / 4,206,056 gzip bytes**,
adding 371 keys while retaining every old payload. Two alternate certificate
occurrences remain in trial archives. New decisions comprise **146 direct roots /
46 guards**, including the two SAT cases. The union also has 106 available retained
roots and 64 pending ones; pending entries cannot justify UNSAT before verification.

All **461 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,421 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **364 sources / 4,042 artifacts /
71 manifests** remain unchanged. Runtime binds 368 sources; the analyzer brings
the ledger to 369. Structural authority stays 2,614 patterns / 259 pairs / 17
missing children, original 17/24 / 999 steps, separate supplemental 24/24 / 208,
and original case 7's discovery pointer. No new Lean claim.
Checkpoint SHA-256: `ddab750444c8546722ca5d15acee2abbda32455e9dd2dcc785715ebdcfaa62b1`.
Report SHA-256: `9b616b087f471249cebe07ea6c29a864980c46d3736425e613b6cfa1de556b70`.
The manuscript builds to 197 pages without warnings; all 64 proof blocks are unchanged.
The new manifest binds 55 artifacts; next audit inherits **4,097 artifacts / 72 manifests**.


## 2026-11-16: witness signatures separate lookup from discovery

[Bounded witness exploration](witness-signatures.md) reaches two hard historical
SAT queries through sequences of flips, but adds no transfers on the next 192
inputs. All 96 SAT inputs already use the old witness route. Total runtime
regresses 6.04%; all 214 remaining expansions are UNSAT cases. Keep the new
bank optional. Equal false-clause signatures compress exact lookup but do not
preserve flip transitions; a two-variable counterexample is tested and recorded.
The fixed budget, all accepted assignments, failed attempts and seed origins persist.

The next coverage target is shared negative cofactors: template 6 now contributes
94 expansions, template 8 contributes 69 and template 12 contributes 51. Current
cases 123/189 share guard [130,140] and cost 17/16 expansions. Compare their
conditional supports and proof structure, then test transfer across different
guards and templates. Cold audit and compression remain 40.45%/33.11% of total
control runtime. Broader pattern coverage and efficient arbitrary-SAT acquisition
remain open; polynomial signature counts do not imply cheap construction.

Resume `experiments/results/cnf-witness-signatures/checkpoint.json` (17,947 keys).
All 473 tests, nine complete archive audits, every union node, 1,613 inherited
and 192 new decisions pass without fresh validation search. Old results and the
170-entry negative frontier are preserved. Structural authority remains 2,614
patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps and separate
supplemental 24/24 / 208. The paper builds to 198 pages with 64 unchanged proof
blocks. No new Lean or unrestricted polynomial SAT claim.


## 2026-11-17: causally sliced unit supports

[Causal support extraction](causal-support.md) removes propagated assignments
unused by the conflict or selected negative child proof, while retaining their
backwards dependency closure. All derived certificates use the unchanged checker.
Nine additional cofactor hits reduce expansions **195 -> 100 (48.72%)** on a
fresh 192-query stream. Extending the previous extraction with the same new
sources gives no additional hits. All measured causal hits still share the first
origin's guard, so broad cross-guard transfer remains open.

Complete time increases **15.87%** against active loading despite **27.04% lower
query time**. Re-extracting all 389 origins costs 2.33282 seconds; 31 materializations
add 275 proof rows, raising new rows 423 -> 553. The next cost target is active
loading of the acquired causal frontier, followed by incremental causal discovery
on novel queries. Repeated exact queries cannot establish that new acquisition
amortizes. Remaining work is 95 negative expansions plus five on SAT case 42;
negative cases 187/159/50/60 cost 20/17/16/16 expansions.

Resume `experiments/results/cnf-causal-support/checkpoint.json` (18,672 keys).
Causal proposals require `CausalCoreBank` and its matching materializer; 34 roots
are ready and 142 remain pending. Both new frontiers use eight ordered provenance
catalogs, while the old 170-entry bank retains its six-catalog history. Every old
checkpoint field and all trial certificates remain preserved.

All 486 tests, nine complete archive audits, all union nodes, 1,805 inherited and
192 new decisions pass without fresh validation search. All 375 prior sources
and 4,174 artifacts / 73 manifests are unchanged. Structural authority remains
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps and
separate supplemental 24/24 / 208. The paper builds to 199 pages with 64 unchanged
proof blocks. No new Lean, minimum-core or unrestricted polynomial SAT result.


## 2026-11-17: retain causal discovery and compare proof choices

[Retained causal loading](retained-causal.md) avoids all 2,851 repeated discovery
node visits, reducing preparation 2.29443 -> 0.08099 seconds and total runtime
12.74826 -> 10.63701 seconds (16.56%) against rebuilding. The frontier files
and proof databases are identical, and every match plus complete cold lineage
remains checked. Pending roots still require the causal materializer.

Against loading the legacy frontier, six extra hits reduce expansions 120 -> 93
(22.5%), but total time is effectively flat and measured peak RSS rises 14.56%.
On the 19 targets both banks cover, causal materialization creates 74 rows versus
33 for legacy. Choosing an already cheaper proof is the next matched experiment;
that apparent 41-row opportunity is not a guaranteed saving under changed cache
histories. Remaining work comprises 74 negative / 19 positive expansions. Negative
cases 14/161 cost 19/15; SAT cases 45/91 cost 14/five. All measured transfers still
share their first origin's guard, so broad cross-guard coverage remains open.

Resume `experiments/results/cnf-retained-causal/checkpoint.json` (19,091 keys).
It adds `retained_causal_study` and `retained_causal_decisions`, preserving earlier
frontiers, their pending entries and every prior field. Both measured indices
retain their eight-catalog / 389-origin lineage; this run adds no new sources.
The causal frontier has 48 ready roots and 128 pending in the union. Incremental
causal discovery from new batches remains separate and unimplemented here.

All 492 tests, nine complete archive audits, all union nodes, 1,997 inherited and
192 new decisions pass without fresh validation search. All 381 prior sources
and 4,230 artifacts / 74 manifests remain unchanged. The broader test log retains
24 unclosed-SQLite ResourceWarnings during older tests; focused new tests emit
none with warnings enabled, and allocation origins are untraced. Structural
authority remains 2,614 patterns / 259 pairs / 17 missing children, original
17/24 / 999 steps and separate supplemental 24/24 / 208. The paper builds cleanly
to 200 pages with 64 unchanged proof blocks. No new Lean or general SAT bound.


## 2026-11-17: choose among acquired negative proofs

[Proof choice](proof-choice.md) preserves the causal frontier's 30 target hits
while reducing support derivation 137 -> 57 rows. It adds no new support origins
and establishes no new arbitrary-SAT category. The composite references the same
389 distinct origins across two acquired extraction policies. All hits still
share their first origin's guard; whole-query guards remain mandatory.

The next coverage experiment should incrementally acquire supports from preserved
new guarded negatives. Seven current residuals account for all 35 remaining
expansions: cases 46/48 cost seven, 27 six, 7/101/156 four, and 86 three. Compare
their conditional structures and genuinely changed guards. These IDs are local
to the current query catalog. Complete partitioning and efficient solution of
every cell remain separate obligations.

Verified resume: `experiments/results/cnf-proof-choice/checkpoint.json` retains
19,543 keys, 149 new direct results and 43 guarded negative decisions, preserving
all earlier payloads and checkpoint fields. Both source banks and their pending
entries remain bound; 137 later guarded-negative records are available for the
next acquisition experiment. All 502 tests, nine complete archive audits, all
union nodes and 2,189 inherited decisions pass. Structural authority remains
2,614 patterns / 259 pairs / 17 missing children. The paper builds to 201 pages
with 64 unchanged proof blocks. Older-test SQLite warnings are preserved;
the 10 focused new tests emit none with warnings enabled.


## 2026-11-17: incremental acquisition and alternative guards

[Incremental acquisition](incremental-causal.md) adds 27 retained causal
supports from 137 guarded-negative records but produces no extra hits on the
next fresh-query stream. The index grows without a demonstrated coverage gain;
the old and extended policies produce byte-identical proof archives.

The next discovery target is alternative guarded decompositions. A read-only
probe finds that current case 121 has a second valid guard whose target contains
an old checked support, while the chosen target costs 20 expansions. This is
local potential, not a timed batch saving. Test a bounded alternative check
before fresh solving, retaining source/guard binding and charging recognition,
verification and changed later sharing. The remaining 126 expansions comprise
120 negative and six positive. Case IDs belong to this current stream.

Verified resume: `experiments/results/cnf-incremental-causal/checkpoint.json`
retains 19,907 keys, all previous payloads and checkpoint fields, plus the optional
203-entry causal frontier. All 510 tests, eight complete archive checks, all union
nodes and 2,381 inherited decisions pass. The new index has 62 ready roots /
141 pending. Structural authority remains 2,614 patterns / 259 pairs / 17 missing
children. The paper builds to 201 pages with 64 unchanged proof blocks. Older-test
SQLite warnings remain recorded; eight focused new tests emit none.


## 2026-11-17: bounded alternative-guard selection

[Bounded alternative guards](alternative-guard.md) expose one additional
checked residual on a fresh 192-query stream. Case 36 changes guard, saving seven
expansions without new acquisition or materialization. The original guard remains
the fallback when the additional checked candidate has no ready proof.

No unseen removed-clause assignment is established: case 101 differs from its
core's first origin but matches another recorded origin. Compare all provenance
records before calling a transfer cross-guard. Next, price pending alternatives
for cases 23/85 (11/six expansions), with one-expansion case 103 as a control.
These are acquired descriptions, not yet checked negative proofs at selection.
Controlled probes need the pre-query state; fresh tests must exclude cached cases.

Verified resume: `experiments/results/cnf-alternative-guard/checkpoint.json`
retains 20,270 keys, all previous payloads and checkpoint fields. All 518 tests,
eight fresh-trial archive checks, all union nodes and 2,573 inherited decisions
pass. Frozen-worker parity and historical case 121 also pass; its one additional
regression proof remains in a separately retained archive. Structural authority
stays 2,614 patterns / 259 pairs / 17 missing children. The paper builds to 202
pages with 64 unchanged proof blocks. Older-test SQLite warnings are preserved;
eight focused new tests emit none.


## 2026-11-17: price pending alternative proofs

[Controlled prefix probes](pending-guard-costs.md) check all six pending matches
from the preceding guard study. Only case 85 reduces the publication footprint:
six fresh expansions / six rows become two rows, with added payload 11,350 ->
1,805 bytes. Case 23 adds 35 rows versus eleven; case 103 adds twelve versus one
under every candidate. All alternatives avoid fresh SAT search, demonstrating
that expansion counts alone do not price total work.

The useful distinction is a checked terminal unit conflict versus a unit proof
with a child. One terminal origin needs at most one derived core row and one
target subset row; this bounds neither bytes nor recognition/checking time.
The next target is a terminal-origin filter on fresh excluded inputs, keeping
recursive cases as controls. No new source-query coverage or runtime guarantee
is claimed. Resume `experiments/results/cnf-pending-guards/checkpoint.json`
(20,340 keys, 70 added, all prior payloads preserved). Nine reconstructed arms,
2,765 inherited decisions and 32 relevant tests pass. Structural coverage and
its separate original/supplemental proof authorities remain unchanged.


## 2026-11-17: terminal admission misses the fresh unresolved structure

[The fresh comparison](terminal-guard.md) gives no added coverage: both policies
use 68 expansions and 309 new rows on 192 excluded neighbours. Historical
controls admit terminal case 85 and reject recursive cases 23/103. The new scan
adds 3,064 candidate inspections but finds no pending support in the eight
unresolved targets. Timing variation establishes no total speedup.

Current cases 56 and 176 account for 41/68 expansions. Checked cores missing one
clause justify additional restrictions, reducing sizes 79/218 -> 67/172 and
86/240 -> 77/209 clauses/literals. No restricted endpoint is already reusable.
The next task is checked composition and a matched remaining-solve comparison,
including SAT case 155 as a control against premature UNSAT. Preserve recognition,
premise publication, acquisition and persistence costs. Resume
`experiments/results/cnf-terminal-guard/checkpoint.json` (20,649 keys; all prior
payloads preserved). Full proof replay, 1,013 solver tests and two additional
condition tests pass; structural authority and existing proof blocks are unchanged.


## 2026-11-17: compose restrictions and locate duplicate checking cost

[Guard-chain composition](guard-chain.md) reduces expansions/new rows **68 -> 29**
on eight exact historical pre-query prefixes. Added native payload falls 57.72%;
serialized deltas plus composition records fall 13.47%. All six strengthened
premises already exist. Case 155 remains SAT. Selection/checking outweighs the
child-solve time saved in single samples; no total runtime or peak-memory gain
is established. A separate read-only probe finds that checking those premises
without a separate support-proof traversal reduces verified nodes **148 -> 57**.
Implement that lookup order and prepared near-containment membership next, then
test new excluded queries. Missing premises still require checked derivation.

Resume `experiments/results/cnf-guard-chain/checkpoint.json`: 20,666 native keys,
17 added and all prior payloads preserved, plus eight checked chain conclusions.
Native proof format is unchanged; optional `GuardChainBank` must load and check
the bound sidecars for composed source reuse. All 16 trial arms, 2,957 inherited
decisions and 1,022 solver tests pass. Original and supplemental structural
coverage remain separate and unchanged. Historical savings do not establish
fresh coverage, optimal expansion or a polynomial bound for arbitrary SAT.


## 2026-11-17: fresh premise-first guard chains

[Prepared recognition and checked-premise priority](premise-guard.md) reduce
expansions **139 -> 67** and new native rows **436 -> 364** on 192 fresh neighbours.
The new selector preserves the old chain policy's native proofs while reducing
additional verified nodes **247 -> 102**. All eight strengthened premises already
exist. Seven cases improve, with no per-case expansion/publication regression.
Complete timings have mixed paired signs; retained trial bytes rise 0.414% versus
ordinary because chain records offset the smaller archive. No stable total-cost
or general memory gain is established.

The largest remaining case, 68, costs 27/67 expansions and is three clauses from
an overlapping ready core. Cases 6/135 cost seven each and need three/two missing
clauses. Next, price exact alternative coverage or disjoint branches by the first
falsified clause. A checked negative conjunction of several missing clauses
forces some clause false, not all. The pre-query diagnosis publishes nothing;
multiple-clause inference remains open. Cold checking and compact sidecars remain
supporting cost targets. Resume `experiments/results/cnf-premise-guard/checkpoint.json`
with 21,128 native keys, all prior payloads preserved, eight inherited and 192 new
chain conclusions. All 1,028 tests, six native/chain audits, 2,957 inherited ordinary
decisions and frozen-worker parity pass. No new Lean or unrestricted-SAT bound.


## 2026-11-17: exact multiple-clause composition and plan-cost gap

[First-false partitions](clause-partition.md) now cover a target using an existing
negative strengthened premise, earlier missing clauses held true, and the selected
clause falsified. All branches must be negative for UNSAT; a checked SAT branch
lifts to the original query. Native proofs remain unchanged; composed lookup
requires the bound partition sidecars. Exhaustive small-formula and SAT controls,
1,035 full-suite tests and independent native/sidecar replay pass.

Historical case 68 improves **27 -> 11 expansions** in the best tested order,
case 6 improves **7 -> 3**, and both case-135 orders regress **7 -> 8/10**. Trying
all eight plans costs 105 expansions versus 41 for the three baselines. These
post-hoc choices establish no fresh coverage or cheap plan-selection policy.
A read-only propagation probe finds terminal-conflict signals for the better
orders, but case 135's smaller residual still costs more. Next, implement bounded
screening that reuses its unit traces, retain 135 as a fallback control, and test
new excluded inputs with preparation, premise publication and cold replay charged.

Resume `experiments/results/cnf-clause-partition/checkpoint.json`: 21,225 native
keys, all previous 21,128 payloads preserved, and eight partition records for
three historical sources. All 2,957 ordinary inherited decisions and 200 inherited
chains replay. Structural authority and all 64 existing proof blocks remain
unchanged. No new Lean or unrestricted-SAT bound is claimed.


## 2026-11-17: bounded partition screening and a terminal-baseline counterexample

[Retained unit traces](partition-screen.md) now support bounded plan selection
and checked publication without repeating selected-branch propagation. Historical
controls use 23 new rows versus 41 baseline; nine wrapper/conflict publications
replace expansion calls and must remain in the accounting. Case 135's nearest
two-clause orders are rejected, but a three-clause alternative is admitted.

On 192 fresh queries, expansions 27 -> 26 coexist with rows 247 -> 249 and native
payload 495,506 -> 499,414 bytes. The only screened target already has a unit
conflict, so partitioning is unnecessary. Combined propagation visits rise from
8,190 to 12,369. Keep the selector optional; no stable runtime or peak-memory
improvement follows. First reuse the baseline terminal trace, then inspect
cases 43/172 (19 of 26 remaining expansions) after their extra guard, where this
policy currently stops screening. Plan budgets do not bound posting discovery,
cold proof checking or remaining unrestricted residual search.

All 1,042 tests, four fresh trial audits, six historical controls, 2,957 inherited
ordinary decisions and 406 composed records pass. The final union retains all
21,225 prior payloads and has 21,482 keys. Resume
`experiments/results/cnf-partition-screen/expanded-checkpoint.json`; the intermediate
fresh checkpoint and failed harness assumption are also retained. Preserve all
mixed sidecar catalogs separately from ordinary schemas. Structural authorities
and 64 prior proof blocks remain unchanged; no new Lean or unrestricted-SAT bound.


## 2026-11-17: terminal-first reuse and conditioned-core matching

[Terminal-first screening](terminal-first-screen.md) corrects unnecessary
repartitioning on saved case 176: three proof rows become one, native bytes
6,137 -> 2,229 and propagation visits 5,289 -> 1,110. No posting search, core read
or plan construction is needed after its baseline unit conflict. Prepared-index
setup and native verification remain charged. Nonterminal controls preserve
exact plans and proof deltas; no fresh coverage or stable total-time gain follows.

Cases 43/172 still hold 19/26 expansions after an extra guard. Their original
core bank has no eligible plan, but restricting checked negative cores by the
same guard assignments exposes two-clause gaps. Case 172's three-clause core-209
cofactor is already native-checked; case 43's nearest restricted roots need
certification or acquisition. Price these plans against ordinary clause splitting,
including model lifting and discovery. The read-only full-bank probe visits about
32,000 restriction literals per case across two passes and publishes nothing.
Assignment-sensitive projection caching is a candidate, not a measured guarantee.

Resume `experiments/results/cnf-terminal-first-complete/checkpoint.json`: all
21,482 native keys and the existing compressed archive are retained unchanged;
eight sidecars preserve both control policies. All 1,047 tests, 2,957 ordinary
and 414 composed records pass. Earlier sources, artifacts, structural authorities
and 64 manuscript proof blocks remain preserved. No new Lean or arbitrary-SAT bound.


## 2026-11-17: conditioned patterns can hide simpler forced assignments

The [conditioned-core comparison](conditioned-core.md) implements checked native
cofactor acquisition after units expose a conflict or two-CNF. This broadens the
acquisition gate, not certified input coverage. Fifteen historical arms show
that the useful case-43 partition is equally available through a smaller direct
premise proof. Same-order branch certificates are identical. Case 172 is literally
an existing-clause split, and 70 regresses. Conditioned supports should therefore
be treated as candidate generators whose benefit needs a direct control.

A checked read-only probe discovers a more informative simplification: one
assumption suffices to unit-refute each target (43: [-230], 172/70: [-40]). The
corresponding forced assignments leave absent native children. Price this exact
one-child decomposition before widening the policy. In 70 the support is the
binary pair [40,50], [40,-50]; in 43/172 a new propagation trace after deleting
an assumption is needed. Slicing one existing trace is not minimum-assumption
recognition. Charge bounded probing, remaining acquisition, lifting and replay;
then test adversarial edits and excluded inputs. No partition of all CNFs into
efficient cells, compact closure or arbitrary-SAT bound is established.

Resume `experiments/results/cnf-conditioned-core-exposed/checkpoint.json` (21,525
keys, prior payloads preserved). All 1,057 tests and independent replay pass.
Original structural coverage and four frontier counts remain unchanged; fifteen
new composed conclusions revisit three already known sources.


## 2026-11-17: candidate validity and candidate value are separate

[Priced single-assumption guards](assumption-guard.md) reduce rows on 43/172 but
increase them on 70. All three were valid checked forced assignments. Retaining
unit traces avoids repeated premise propagation; it does not change the stored
proofs or remaining child search. Aggregate native storage falls, while total
propagation and serialized decision size rise. These historical measurements
supply no fresh category coverage or universal beneficial-reduction rule.

A local discovery probe ranks up to four unforced variables by binary incidence,
with deterministic identifier ties and false/true order. It finds different
unit-refuted assumptions for all three targets after one/one/two probes, without
another bank scan. Their native children remain absent. Original versus
unit-residual scoring select the same first conflict here, although later orders
differ; the latter adds a restriction pass. Price
these choices before extending the fixed policy to excluded queries and mixtures.
Unsuccessful probes certify nothing; successful ones certify only the forced
assignment, not cheap remaining acquisition. Retain the case-70 regression.

Resume `experiments/results/cnf-assumption-guard/checkpoint.json` (21,528 keys,
all previous payloads preserved). All 1,064 tests and independent cold checks
pass. Structural authorities and four frontier counts remain unchanged.

## 2026-11-17: distinguish a discoverable guard from a cheap remaining problem

[Local binary-incidence discovery](local-guard.md) has a fixed four-variable
budget, shared baseline propagation and checked trace publication. It requires
no additional core-bank scan. Exhaustive two-variable cases and transported
representations pass, as do six exact-prefix historical arms and four matched
streams on 192 new neighbouring inputs. Those inputs exclude earlier query and
native roots, but still come from three templates; this is not broad arbitrary-CNF
coverage. Failed probes do not establish absence of a useful guard.

Historical rows improve 23 -> 19. Fresh rows remain 250 -> 250, while propagation,
sidecar bytes and observed complete time increase. Case 144's local forced child
needs ten expansions and misses a cached negative dependency used by baseline;
cases 167/190 close under unit propagation. The next useful distinction is thus
between a checked forced assignment and a residual whose acquisition is cheap.
Screen existing native answers or unit-terminal traces before guard publication,
preserve cheap native-family priority, and price the fallback. A strict gate also
rejects useful nonterminal historical cases 43/172, so retain them as controls.
Exact-prefix and another excluded-set comparison are still required; posthoc
selection is not a deployed saving. The recorded dependency root enables a later
investigation of checked proof transport through conditioning.

The 21,801-key checkpoint preserves every prior payload and retains 390 new
composed records alongside 438 earlier records, 2,957 ordinary decisions and six
projections. All 1,069 tests and independent cold replay pass. Existing structural
authorities remain unchanged. Discovery bounds do not bound the unrestricted
child solve, prove compact closure or supply a uniform polynomial SAT algorithm.


## 2026-11-17: admit checked children and retain rejection costs

[Checking the remaining child](child-admission.md) distinguishes a valid guard
from a cheaply certifiable residual. A known native answer or unit-refuted child
admits the proposal with at most two new native rows and no general child search.
Rejection leaves the archive intact and uses ordinary solving; native syntactic
families retain priority. Tautological sources also fall back because deletion
guards require a stricter source representation.

At identical prefixes, case 144 falls 11 -> 3 rows and 167/190 retain two rows each.
The gate nevertheless rejects useful 43/172 guards. Their residuals and both
rejection controls remain outside two-CNF/Horn/dual-Horn; all post-UP native roots
are absent. Beneficial 172 has 112 literals, versus 111 in regressing 70, refuting an
absolute monotone smaller-residual selector for these controls. Broader structural
recognition and checked dependency transport remain open. Another excluded stream
must test the fixed gate without posthoc selection. All 1,076 tests and independent
cold checks pass; structural authority is unchanged and 18 composed controls are
retained against the same 21,801-key archive. No arbitrary-SAT efficiency follows.


## 2026-11-17: fresh admission reveals reuse after propagation

[The unchanged child gate on 192 excluded query roots](child-stream.md) gives
three admitted unit-conflict children, two terminal targets and one failed
proposal search. Its eight-row saving coexists with greater propagation,
sidecars and observed complete time. The new queries still belong to three
old template families and do not enlarge the separate structural authority.

New case 85 supplies the next pattern: a source outside the cheap syntactic
families reduces after forced propagation to an already checked binary SAT
residual. A read-only check validates exact pre-query availability, the native
answer and model transport through 23 forced assignments. The gate currently
recognizes families before propagation and misses this reuse, paying four
failed probes and repeated baseline propagation. Check the exposed normalized
residual before ranking candidates, reuse the unit trace, and retain no-hit and
nonterminal controls. Recognition/checking cost and an excluded-stream test are
still required; the diagnostic is not an implemented speedup.

All 1,076 tests and independent checks pass. The new 22,036-key checkpoint
preserves every previous payload and 384 new composed records. Original and
supplemental structural authorities remain unchanged. No unrestricted-SAT
efficiency or compact-closure claim follows.

## 2026-11-17: recognize a cached residual after propagation

[Propagated reuse](propagated-reuse.md) now accepts a checked native answer or
recognized native family exposed by a nonempty unit prefix. The unit trace
provides exact source/residual recomposition for SAT models and negative proofs.
The new route repairs the selected case-85 regression (5,750 -> 955 visits)
without new storage savings. Twenty-one equal-state arms preserve the other
controls. Another 192 excluded roots produce no successful new residual lookup:
both admission policies retain identical proofs and propagation counts. There
is no added structural authority or stable general timing gain.

Two remaining cases retain useful prefixes even though their proposals are
rejected. Reusing those traces before general residual solving is the next
implementation candidate. Case 36's exposed 11-variable residual also has a
checked single-variable decomposition: all three clauses wider than two contain
canonical variable 6, and both assignments leave two-CNF. The posthoc artifact
retains both restrictions and checks pointwise equivalence on all 2,048 full
assignments. Case 186 has no such variable under the same exhaustive syntactic
test. This distinguishes a useful restricted cell from an explicitly unresolved
one. It neither bounds conditioning size for every CNF nor prices an alternative
proof; discovery and two-branch acquisition are still to measure.

The new 22,259-key evidence union preserves all earlier results and adds 597
composed records. All 1,085 tests and independent replay pass. Structural and
supplemental authority, four frontier lineages and six projections are preserved.
No new Lean proof, compact closure or unrestricted-SAT efficiency follows.


## 2026-11-17: preserve rejected-prefix work and detect positive child closure

[Retained-prefix fallback](trace-fallback.md) avoids repeating baseline propagation
when a guard is rejected, while leaving residual search unrestricted. Fresh
propagation falls 6.29% with identical native proofs; discovery still exceeds
baseline work and no stable total speedup follows. This improves work reuse
without adding a general structural category or reducing native storage.

A separate replay identifies a recognition asymmetry: new case 146's rejected
child is satisfied by its 26 unit deductions, with no residual clauses. The gate
accepts known answers or conflicts, missing positive unit closure. Its canonical
child model is checked. Next, transport it through the proposed assignment to
the original target and verify that whole target before publishing SAT directly.
A verified target witness does not require acquiring the proposed negative
premise. Original-target transport and alternate acquisition remain unimplemented.

The largest unresolved cases 0/131 still have nonfamily children after the
proposed condition and propagation. They account for 31 of 43 remaining child
expansions. All four baseline residuals fail the complete single-variable test
for two immediate syntactic two-CNF restrictions. This is not exclusion of closure
under subsequent propagation or mixed-family decomposition. Preserve those
negative controls and the previous case-36 positive control when pricing broader
conditioning. No bounded conditioning size for arbitrary CNF is established.

All 1,094 tests and independent replay pass. The 22,532-key evidence union retains
all previous results and 603 new composed records. Structural and supplemental
authority are unchanged. No new Lean proof or unrestricted efficiency follows.


## 2026-11-17: recover positive witnesses and distinguish query from child novelty

[Positive-child recovery](positive-child.md) now turns case 146's checked unit
closure into a whole-target SAT witness. It restores the proposed condition and
checks all target clauses before publishing one native row, avoiding the
negative premise and child acquisition. At the saved prefix, six rows become
one and native bytes fall 73.12%; discovery still exceeds native baseline
propagation. Negative results retain their existing certificates. This is a
restricted publication improvement, not efficient recognition of every SAT cell.

The next 192 raw query roots are new but 190 targets become known after ordinary
preparation. The remaining two close through a cached propagated residual or
unit conflict. No new positive-model recovery activates, and all three policies
retain identical native additions. This distinguishes source-root exclusion from
unfamiliar child acquisition. The next study needs different template families,
pre-query target-familiarity strata, charged generation and matched total costs;
the old neighbours remain valid warm-reuse controls.

Retain cases 0/131/159 for nonfamily interaction and case 146 for model recovery.
The older case-36 one-variable two-CNF decomposition remains an unpriced positive
structural control. Prior single-variable failures concerned immediate syntactic
two-CNF, leaving propagation-assisted and mixed-family closure open. No bounded
conditioning size or compact closure for arbitrary CNF is established.

All 1,102 tests and independent replay pass. The 22,729-key union preserves all
previous results and 615 new composed records. Structural and supplemental
authority are unchanged; there is no new Lean or unrestricted efficiency result.


## 2026-11-17: unfamiliar family transfer and futile premise probes

[Cross-family evaluation](cross-family.md) adds 48 unlabelled CNFs from four
finite generators and twelve same-template controls. All 48 fresh targets remain
unfamiliar after preparation; the twelve neighbours become known. Independent
truth tables enumerate 22,345,728 assignments across the 48 small formulas after
timing (1.409 seconds); this exponential validator is not a solver algorithm.
Both acquisition policies produce identical 398-row / 483,695-byte additions.
The optional policy performs 384 unsuccessful probes and raises propagation
65,842 -> 246,726 visits, mean query time 0.354 -> 0.482 seconds and complete
worker time 21.512 -> 21.963 seconds. Both timing pairs regress. All failed
screens and exact query prefixes are retained.

A posthoc necessary-condition audit identifies 192 futile probes / 73,488 visits:
after consistent baseline propagation, an unassigned variable without residual
binary-clause incidence cannot create another unit or empty clause, so a single
assumption cannot be unit-refuted. Implement and price this filter while reusing
the baseline trace. Original widths are insufficient; the documented unit-prefix
counterexample must remain a control. Random 3-CNF and coupled parity account
for 261/386 acquisition rows and 47,263/65,842 acquisition visits. Preserve cases
32/56/52 and 21 for broader decomposition; keep earlier useful/regressing guards.
Cold replay still dominates complete cost, so local probe savings have limited
end-to-end scope. This extends evaluation coverage, not structural authority.

All **1,106 tests**, 12 focused tests and independent reconstruction pass. The
new checkpoint is `experiments/results/cnf-cross-family/checkpoint.json`:
**23,127 native keys**, all 22,729 old payloads, **120 new composed records**,
3,045 previous composed records, 2,957 ordinary decisions and six projections.
There are no alternate native payloads. The union occupies 74,706,944 database
bytes / 5,364,377 compressed bytes. Ready/pending banks remain 132/38, 141/66,
86/90 and 86/117. All earlier 498 sources, 5,617 artifacts and 93 manifests
are unchanged. Structural authorities and all 64 manuscript proof blocks remain
unchanged. The 209-page manuscript builds without overfull or undefined warnings.


## 2026-11-17: skip binary-ineligible probes and retain positive discovery targets

[Residual binary filtering](binary-probe.md) now skips unassigned candidates with
no binary incidence after consistent baseline propagation. Original ranking,
candidate prefix and successful selections are preserved; skipped candidates do
not refill the budget. The saved trace records each omission. Independent
reconstruction checks all omitted screens and source bindings, and 2,048 small
formula/representation comparisons preserve every previous selection.

Twenty-six historical arms retain identical native/composed certificates, with
21 probes and 38,189 visits in either policy. Filtering adds incidence-scan
cost there. On 60 further excluded queries, 49 targets remain unfamiliar after
preparation. The filter removes 192/386 probes, cuts propagation 252,999 ->
179,463 (29.07%) and query/warm sidecars 15.13%, with identical 450-row / 521,286
native-byte additions. Query timing differences have opposite signs; complete
times regress 21.947 -> 22.234 seconds. Native baseline uses only 69,351 visits.
Cold replay remains dominant. No overall speedup is established.

The next discovery target is a useful result discarded by premise probing:
case 50's assumption -169 has an empty residual and an independently verified
whole-target model, but the policy selects only unit conflicts and then acquires
three native rows / 2,503 bytes. Implement and price positive-premise recovery
at this saved prefix. Eighty-nine conditioned residuals across twenty queries
are syntactically constant/Horn/dual-Horn/two-CNF; they still need checked
acquisition and recomposition. One refuted condition does not refute the parent.
As supporting work, signed incidence could exclude 83 remaining probes / 28,774
visits. Neither new route is implemented or timed. Keep negative-probe filters
scoped so useful positive witnesses are not silently excluded.

All **1,113 tests**, 24 focused tests and independent reconstruction pass.
Resume `experiments/results/cnf-binary-probe/checkpoint.json`: **23,577 native
keys**, all 23,127 earlier payloads, **206 new composed records**, 3,165 earlier
composed records, 2,957 ordinary decisions and six projections. No alternate
payloads are needed. The union occupies 75,649,024 database bytes / 5,474,412
compressed bytes. Ready/pending banks remain 132/38, 141/66, 86/90 and 86/117.
Prior 503 sources / 5,655 artifacts / 94 manifests, structural authorities and
all 64 manuscript proof blocks remain unchanged. The 211-page paper builds
without overfull or undefined warnings. No new Lean theorem or unrestricted-SAT
resource bound is claimed.


## 2026-11-17: checked positive-premise model recovery

[Positive-premise recovery](positive-premise.md) now lifts and checks complete
models from already saved unit screens of target-plus-assumption. It preserves
existing admitted choices and probes; a full target model, checked again by
native publication, replaces fresh fallback search. Saved case 50 shrinks
3 -> 1 acquired nodes / 2,503 -> 1,482 native bytes. Thirteen older controls
retain exact certificates. Fresh gated-Horn cases 26/54 also save two nodes
each; stream additions are 410/406 nodes and 472,534/469,867 native bytes for
previous/recovered policies. Neither broad taxonomy coverage nor an efficient
arbitrary-SAT reduction follows.

Mean query times are 0.4220/0.4018 seconds. Complete paired differences have
opposite signs, diagnostic sidecars grow about 0.36%, and process RSS is
essentially unchanged. Earlier discovery is still charged. Gated-Horn discovery
uses 73,886 propagation visits versus 5,751 acquisition visits. The next target
is checked solving and model transport for nonterminal conditioned Horn,
dual-Horn and two-CNF residuals, with exact negative-branch recomposition.
Positive discovery outside the binary filter and early positive stopping remain
open. All 1,120 tests pass; seven new tests include 2,048 small transported
clause-set comparisons, malformed traces, false residual hints and cold replay.


All **1,120 tests**, 31 focused tests, 135 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-positive-premise/checkpoint.json`:
**23,987 native keys**, preserving all 23,577 prior payloads, with 210 new
composed records alongside 3,371 inherited records, 2,957 ordinary decisions
and six projections. The union uses 76,537,856 database bytes / 5,571,577
compressed bytes. Three alternate model payloads remain in measured evidence
(six occurrences); preserved native payloads are never replaced. Ready/pending
banks remain 132/38, 141/66, 86/90 and 86/117. All 508 earlier source fingerprints,
5,780 artifacts and 95 manifests remain intact. The paper builds at 212 pages
with all 64 existing proof blocks unchanged. The initial replay validator's
scratch-directory failure and its separate corrected replay revision are retained.
No new Lean theorem, structural authority or unrestricted-SAT bound is claimed.


## 2026-11-18: uniform completion of conditioned residuals

[Uniform completion](uniform-premise.md) now uses checked saved unit traces to
recognize and transport all-false/all-true residual models before fallback.
It covers unit-closed Horn/dual-Horn and broader sign patterns. The two predicates
partition residuals into four cells, but the neither-completion cell still
encodes arbitrary SAT via unit closure and a fresh unequal-variable pair.
No unrestricted-SAT efficiency or complete easy partition is claimed.

Seventeen saved-prefix contexts preserve earlier controls; case 14 saves two
acquired nodes. Nine fresh gated-Horn cases save eighteen nodes, taking additions
452 -> 434 nodes / 535,908 -> 521,248 native bytes. All twelve gated targets now
use direct model publication. There are 96 failed graph-colouring checks.
Query-time differences have mixed signs; both complete-worker differences are
negative, with no general scaling inference. Diagnostic sidecars grow 2.83%.
All 1,129 tests pass, including nine new tests. Independent counter attribution
covers 138 records and a 256-formula embedding check.

Posthoc SCC diagnosis identifies four checked mixed models for fresh graph case
39 and sixteen checked negative conditions on fresh 43/51/55/59. Their timed
acquisition and negative parent recomposition remain open. These IDs refer to
this corpus. Gated-Horn discovery still uses 74,194 propagation visits despite
zero acquisition propagation: early positive stopping and canonical-form reuse
are the next direct computation targets. Preserve failed uniform attempts and
the SAT/UNSAT counterexamples to interpreting failure as refutation.


All **1,129 tests**, 23 focused tests, 138 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-uniform-premise/checkpoint.json`:
**24,444 native keys**, preserving all 23,987 prior payloads, with 216 new
composed records alongside 3,581 inherited records, 2,957 ordinary decisions
and six projections. The union uses 77,484,032 database bytes / 5,677,574
compressed bytes. Five alternate model payloads remain preserved (fourteen
occurrences). Ready/pending banks are 132/38, 141/66, **87/89** and **87/116**.
The two gains refer to one 568-byte negative certificate acquired by shared
ordinary preparation for neighbour case 1 in every mode: causal core 46 and
incremental-causal core 51. This activation is not a uniform-policy gain.
All 514 earlier sources, 5,918 artifacts and 96 manifests remain unchanged.
The paper builds at 212 pages with all 64 existing proof blocks unchanged;
structural authority and original coverage remain unchanged. No new Lean theorem
or unrestricted-SAT resource bound is claimed.

## 2026-11-18: stop on a checked positive completion

[Inline completion](inline-completion.md) brings uniform witness recognition
into the existing probe loop. The canonical binding, forced values and residual
are reused directly; a raw source/assumption model check precedes native
publication. The candidate cap and filter remain unchanged. A positive model
can replace a later guard, and saved evidence distinguishes an unvisited suffix
from failed or filtered candidates. This is cheaper discovery, with unchanged
solved coverage in the new sixty-query stream: thirteen model publications in
both policies. Exhaustive small cases exercise guard preemption and coordinate
transport. General SAT remains in the unresolved uniform-miss cell.

Probes fall 190 -> 106 and total discovery/acquisition propagation
171,670 -> 109,554. Query time and diagnostic storage improve, while complete
workers rise slightly; native acquisition stays 446 nodes. Next, integrate
source-checked mixed two-CNF models at the previous study's preserved prefixes,
and investigate positive witnesses excluded by negative-probe filtering.
Negative conditions still require sound parent recomposition.

Resume `experiments/results/cnf-inline-completion/checkpoint.json`: 24,922 native
keys with all earlier payloads preserved. All 1,137 tests, 276 counter audits,
independent reconstruction and the 213-page manuscript build pass; the existing
64 proof blocks are unchanged. Posthoc mixed-model conditions on fresh graph
cases 15/27/39/51 now offer four concrete next acquisition controls.

## 2026-11-18: mixed binary residuals and exhaustive negative covers

[Mixed completion](mixed-completion.md) extends uniform recognition with SCC
solving of live two-CNF residuals. No extra assumptions or altered candidate
budgets are used. A transported positive model is checked against the whole
raw target and assumption before ordinary native publication. Negative paths
remain conditional evidence. Four saved positive controls and two fresh graph
cases gain direct model completion; other negative cases remain explicit.

One fresh negative case has an existing source clause covered by three retained
conditional refutations. This is an exhaustive parent argument, unlike a single
negative condition, and is the next recomposition target. A native combined
certificate and its measured resource cost are still missing. The remaining
nonuniform, nonbinary residual cell still encodes general SAT by a fresh-variable
conjunction; the manuscript and 257-formula audit make this restriction explicit.

Resume `experiments/results/cnf-mixed-completion/checkpoint.json`: 25,334 native
keys preserve all prior payloads. All 1,145 tests, 292 counter audits and full
independent replay pass; the 214-page manuscript retains all 64 existing proof
blocks. Fresh case 59 and saved controls 43/47 supply three exhaustive negative
clause covers whose present parent acquisitions total 36 nodes / 50,554 bytes.
Their combined publication and its cost remain open. No exact ordered SCC
residual repeats within a query on the fresh sample.

## 2026-11-18: certify parent UNSAT by complete conditional coverage

A source clause supplies an exhaustive case split. Refuting F-and-literal
for every literal in that clause refutes the parent; a partial cover does not.
[The new compiler](negative-cover.md) reuses checked negative SCC conditions
and unit traces to construct ordinary native proofs, with exact canonical
rebinding and restriction transport. This closes three saved acquisition
opportunities and one fresh target without new discovery probes. The class
requires complete conditional coverage and checked transport; outside it the
previous selector/fallback remains. The native proof schema and structural
authority are unchanged.

The next concrete discovery target is **cover-directed candidate admission**.
Fresh cases 51, 55 and 59 each have a source clause missing just one refuted
literal, and that literal lies outside the current candidate set. Case 51
needs -158 for [-158, -54, 16]; case 55 needs -156 for [-156, -113, -12]
(or 191 for [-151, -56, 191]); case 59 needs -320 for [-320, -71, 52].
These are candidates for measurement, not already checked extra conditions.
Charge the added probes and retain failures; the missing condition need not
have a binary residual or a cheap proof. Earlier stopping at a completed cover
and covers exposed by baseline propagation are separate opportunities. A gated
K4 regression preserves the latter recognition miss.

Independent analysis finds no new ready support and no change to the discovery
pass on all 48 fresh family queries. Random three-CNF and coupled parity still
cost 253 acquired nodes / 47,204 propagation visits. Neither exact recomposition
nor the finite graph checks establish efficient classification of arbitrary CNF.

All **1,153 tests**, 24 focused tests, 294 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-negative-cover/checkpoint.json`:
**25,757 native keys**, preserving all 25,334 earlier payloads, with 234 new
composed records alongside 4,245 inherited records, 2,957 ordinary decisions
and six projections. The preservation union uses 80,306,176 database bytes /
5,993,018 compressed bytes. Eight roots have alternate certificates in sixteen
retained evidence occurrences. Ready/pending banks remain 132/38, 141/66,
87/89 and 87/116; there are no new support activations. Original structural
coverage remains 17/24 and supplemental positive coverage 24/24. All 529 prior
sources, 6,431 artifacts and 99 manifests remain unchanged. The 215-page
manuscript builds with all 64 existing proof blocks unchanged. No new Lean
theorem or unrestricted-SAT resource guarantee is claimed.

## 2026-11-18: classify a useful extra condition by what it completes

[Cover-directed probing](cover-directed-probe.md) uses source-clause interaction
to choose a literal outside the fixed variable ranking. A clause with exactly
one missing condition gives an explicit objective for one additional probe.
The condition can be negative, positive, nonbinary or unit-conflicting; no
negative result is presumed. Binary refutations complete an exact parent cover,
and positive models require whole-source verification. Other outcomes preserve
the preceding fallback. Recognition uses no family labels.

All three motivating cases close, plus one older saved control. Four fresh
conditions also complete covers. Eight new tests exercise all 64 four-vertex
graphs in two coordinate systems, positive completion, misses, corruption and
cold replay. The policy broadens checked acquisition while keeping the original
discovery record unchanged. It cannot seed unrepresented negative conditions,
complete multiple missing conditions with its one-probe budget, or resolve the
general nonbinary residual cell. Next investigate earlier cover admission and
structural discovery for families without an initial negative condition.

**Largest remaining measured acquisition cost:** coupled parity and random
three-CNF still add **308 native nodes / 52,385 acquisition propagation visits**,
unchanged across policies. Coupled parity alone adds 163 nodes / 25,354 visits;
random three-CNF adds 145 / 27,031. These dominate the remaining native work.
The existing pattern-discovery layer already extracts explicit affine equations
and preserves leftover clauses, whereas this native acquisition path currently
has uniform and binary leaves. The next broad-coverage investigation should
measure a source-checked bridge from that existing affine extraction to native
acquisition on unlabelled coupled inputs: record rank, free dimension and
leftover interaction before choosing a completion rule. Charge extraction,
projection, checking and any enumeration; a 2^d free-coordinate search is only
cheap when d is small, not uniformly polynomial for arbitrary CNF. Positive
models require full-source verification and negative results require their own
checked recomposition. This is a concrete integration target, not an already
measured improvement.

All **1,161 tests**, 24 focused tests, 300 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-cover-probe/checkpoint.json`:
**26,279 native keys**, preserving all 25,757 earlier payloads, with 240 new
composed records alongside 4,479 inherited records, 2,957 ordinary decisions
and six projections. The union uses 81,416,192 database bytes / 6,113,510
compressed bytes. Fourteen roots have alternate certificates in 27 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 534 earlier sources,
6,641 artifacts and 100 manifests remain unchanged. The 216-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem or
unrestricted-SAT resource guarantee is claimed.

## 2026-11-18: reuse affine recognition beyond the native binary cell

[Affine completion](affine-completion.md) connects existing exact extraction to
the acquisition stream without family labels. Clause ownership, parity sign
patterns, row operations, a particular solution and the complete basis are
checked. A small total free dimension enables an explicit candidate walk over
all affine solutions, with leftover clauses retained. A successful model must
satisfy the whole raw target. No source or coupling is dropped.

The bridge adds nine fresh positive publications, while seventeen calls expose
no equations. Three fresh negative analyses are retained but not published:
one linear contradiction and two exhausted spaces. Their 51 native fallback
nodes are the next direct publication opportunity. Forty-one saved contexts
preserve all preceding cases; only eight positive coupled targets change native
acquisition. Small exhaustive and adversarial checks support correctness, not
complete efficient classification of arbitrary CNF.

The fresh base discovery agrees on all 49 locally unfamiliar queries across
the two policies. Eleven neighbour queries become known after preparation;
neighbour case 4 remains unfamiliar behind two checked guards and adds ten
nodes in every policy. This is a shared control miss, not an affine regression.
Random three-CNF still adds 169 nodes / 28,452 acquisition propagation visits.
Fresh graph case 47 retains incomplete covers with two missing conditions per
candidate clause, beyond the one-extra-probe rule. These misses are preserved
alongside the negative affine publication target.

All **1,169 tests**, 24 focused tests, 324 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-affine-completion/checkpoint.json`:
**26,743 native keys**, preserving all 26,279 prior payloads, with 264 new
composed records alongside 4,719 inherited records, 2,957 ordinary decisions
and six projections. The union uses 82,378,752 database bytes / 6,217,639
compressed bytes. Twenty-six roots have alternate certificates in 67 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 539 prior sources,
6,871 artifacts and 101 manifests remain unchanged. The 217-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem,
native proof kind or unrestricted-SAT resource guarantee is claimed.


## 2026-11-18: Checked negative affine cells can now be published

See [negative affine publication](affine-negative-publication.md). An optional
source-bound certificate now checks either a contradictory Gaussian row or every
point of a complete affine space with at most eight free coordinates. Each
point has a falsified leftover-clause witness. Direct Gray-coordinate checking
is independent of the discovery walk. The versioned extension table and guarded
chain reader leave native search and all old native payloads unchanged.

Seven selected negative prefixes replace 134 native nodes / 175,449 bytes with
seven certificates / 21,561 bytes, avoiding 20,949 propagation visits. Six
controls retain 47 native nodes. Across all thirteen cases and two opposite
orders, combined new payload falls 229,996 -> 76,108 bytes; summed query time
falls 0.13998 -> 0.05627 seconds, with both complete-arm deltas negative. This is
a retrospective mechanism pilot, not a fresh-stream coverage estimate. Full
historical replay is separate from per-arm timing; peak RSS was not measured.

All 26,743 prior native payloads remain. The extended archive adds 45,056 SQLite
bytes / 4,627 compressed bytes and preserves native alternatives. Its seven
cold extension-chain checks also read 134 native nodes because the current view
prefers native alternatives. Automatic discovery/checkpoint adoption, certificate
choice, a newly excluded stream and complete projection onto leftover variables
remain open. No-equation targets and large free dimension retain fallback.
The checkpoint explicitly identifies its extension reader; the previous ordinary
production checkpoint remains valid. No new Lean theorem or unrestricted-SAT
resource bound is claimed.


## 2026-11-18: resumable affine negatives on fresh inputs

[The new session](affine-session-reuse.md) checks exact-target negative lookup
before local discovery and persists new versioned refutations. Versioned chain
replay uses its checked extension terminal directly; native search cannot read
extension proofs. Guarded conclusions are indexed in a checked source-bound bank.

A newly excluded sixty-query stream returns 37 SAT / 23 UNSAT in both policies.
Three negatives replace 67 native nodes with three certificates; nine coupled
models remain. Combined additions fall 344 -> 280 certificates and payload
460,091 -> 384,362 bytes. Query time falls 7.76%, complete time only 0.45% on
average, with both orders improving. Sixty lookup misses cost about 0.00579
seconds; there are no fresh extension hits. All discovery traces/counters match.
Full historical replay remains about thirteen seconds. Trial storage and RSS
fall, but the preservation union adds 344 native keys and three extensions
because comparator proofs remain available: 888,832 SQLite / 95,921 compressed
bytes of growth, to 27,087 native keys and ten extension certificates.

Independent validation checks 240 chronological queries, six new-negative
publication-counter records, exhaustive truth for 48 family cases, warm answers
and full historical cold replay. The extension phase loads no native alternative
proofs. Largest remaining acquisition: random three-CNF, 140 expanded nodes /
27,761 propagation visits (start with case 56). Graph discovery pays 25,375
visits and has unresolved cases 47/35. Hidden/no-equation structures, large free
dimension, exact projection and extension-aware internal support remain open.
No unrestricted-SAT resource guarantee follows from these finite measurements.


## 2026-11-18: binary-subset refutation during native expansion

[The optional native rule](binary-subset-refutation.md) checks a mixed residual's
binary clauses for contradictory implication paths. Original source indices let
the unchanged checker validate the result. A satisfiable binary core is
inconclusive. Unit, pure-binary and uniform-core filters avoid redundant SCCs.

On sixty new queries, eight refutation leaves remove 22 native nodes / 16,393
payload bytes across random three-CNF and graph colouring. Discovery is unchanged.
The policy pays 76 failed SCCs; paired query timings have mixed signs and mean
complete-worker time rises 0.82%. This is a deterministic search/storage reduction,
with no established runtime dominance. The checkpoint preserves 27,087 old native
payloads and ten extensions, reaching 27,368 / thirteen. Alternative native
proofs remain in the trial archives; the union preserves first payloads.

The next cases are new random-three 56/44 (5,159/5,117 propagation visits), whose
remaining interaction is not refuted by their binary cores. Repeated binary
graphs, wide-clause compatibility, failed-recognition overhead and earlier graph
cover admission remain open. Full historical replay still costs about 13.5 s.
All 240 chronological queries, twelve publication-counter records, 48 exhaustive
family truths and full historical replay validate. This supplies no new Lean
or unrestricted-SAT resource guarantee.


## 2026-11-18: cover wider clauses through a satisfiable binary core

[The bounded cover rule](binary-clause-cover.md) shares implication reachability
between source-clause literals and checks that the core forces every literal
false. Retained paths, source clauses and native split/unit proofs preserve
exactness; the final pair reuses a contradiction cycle without new SCC work.
The earlier compiler with larger proof spines remains a rejected diagnostic.

On sixty new queries, three covers in two random-three-CNF cases replace eight
search expansions with six compiled children: native additions **226 -> 224**,
payload **293,179 -> 291,005 bytes**. Query and complete-worker means improve
1.27% / 0.40%, with both orders improving; peak RSS rises about 9.53 MB. All prior
discovery evidence matches. The policy stays optional. The union preserves every
old payload and reaches 27,600 native keys / eighteen extensions.

Next investigate partial binary backbones in new cases 32/40/52, rather than
requiring a whole covered clause. Check whether a forced literal avoids a costly
branch after charging recognition, proof children and persistence. Graph discovery
and historical replay remain larger costs. All 240 chronological queries, twenty
affine-publication counter records, 48 family truth tables and full cold history
validate. No new Lean or unrestricted-SAT resource bound follows.


## 2026-11-18: partial backbones with direct excluded-branch proofs

[The new optional policies](binary-backbone-reuse.md) reuse successful implication
paths from otherwise unresolved clause-cover searches. A surviving SAT cofactor
lifts a model; an UNSAT cofactor combines with a directly transported unit proof
of the excluded branch. The original native checker validates both outcomes.

On sixty fresh queries, first adds five native nodes despite less propagation.
The frequency gate saves two nodes / 1,767 bytes and improves query time 3.04%,
with both orders improving. Complete-worker timing stays mixed and its mean rises
0.02%. All earlier discovery evidence matches. The three-policy union preserves
all old payloads and reaches 27,888 native keys / twenty-two extensions.

The next target is selective recognition: six stored ordinary split nodes have
forced split variables omitted by cover-oriented candidate selection. Test a
bounded targeted implication query with full cost accounting. Seventy-five mixed
binary cores in the stored-node census have no forced literals; this method alone
cannot resolve them. Validation covers 360 chronological queries, 24 publication
counter records, 48 family truths and full historical replay. No new Lean or
unrestricted-SAT resource guarantee is claimed.


## 2026-11-18: targeted split-variable implication discovery

[The targeted policy](targeted-backbone-discovery.md) adds at most one implication
root after the unchanged whole-cover budget, with completed searches reused.
It recognizes all fourteen saved forced-variable misses, including six split
nodes. On sixty new queries, native additions fall 252 -> 250 and propagation
visits 29,008 -> 27,154, with twelve selected backbones instead of two. Fifty-six
new root searches, ranking, checking and five excluded children remain charged.
Timing varies substantially in unchanged preparation and cold replay; there is
no established end-to-end speedup. The policy remains optional.

The new diagnostic has twenty binary-equivalence sources with no forced literal,
including eleven ordinary split nodes. Exact full-source substitution with native
certificates is the next coverage target, reusing earlier probe-equivalence logic
where justified. The saved random-three case 56 is among them; it still pays
4,866 propagation visits. This is a measured discovery opportunity, not yet an
implemented speedup. No uniformly efficient arbitrary-CNF expansion follows.

All 1,212 tests, 43 focused tests, 240 chronological query audits, sixteen
publication counter audits, 48 family truth tables and full cold replay pass.
The new checkpoint preserves all old payloads and reaches 28,145 native keys /
twenty-six extensions. Previous defaults and proof formats remain unchanged.


## 2026-11-18: binary equivalence acquisition and its cost regression

[The quotient pilot](binary-equivalence-acquisition.md) implements full-source
substitution, checked signed model lifts and explicit negative dependencies.
Two shared implication trees use `2(k-1)` edges for a `k`-literal block. Old native
proof formats and recursive search remain unchanged; this top-level API requires
an explicit extension reader and is not yet in the prepared production pipeline.

On 68 reconstruction/edit/control inputs, propagation falls 16.57%, but combined
certificates grow 420 -> 440 and payload 525,136 -> 534,611 bytes. Complete time
regresses in both orders. All selected blocks merge one variable. The regression
is retained, and the policy remains optional. The next strongest compression
target is the 41,208 bytes of duplicated source/child formula fields in the new
negative payloads; reconstructing them from exact keys and checked substitution
must be measured. Twenty-two binary cores repeat, and twelve inputs have an
unused second equivalence block. Neither is yet a measured saving.

All 1,220 tests, 51 focused tests, 272 chronological audits, 68 exhaustive truth
tables and full historical/new replay pass. The checkpoint preserves prior results
and reaches 28,691 native keys, twenty-six affine and forty-two explicit equivalence
records. Native recursive integration, prepared admission, compact arbitrary
interaction and uniformly efficient expansion remain open.


## 2026-11-18: compact equivalence records with exact reconstruction

[Version-two certificates](compact-equivalence-certificates.md) omit duplicated
source/child formulas. The full canonical source key and checked substitution
reconstruct both identities before requiring the native UNSAT child. Old records
remain byte-identical and readable; native search never consults the extensions.

The same 68-input, empty-archive comparison retains identical native acquisitions
and source results. Equivalence storage falls 68,878 -> 26,998 bytes, combined
payload to 492,731 bytes: 6.17% below the native control. The certificate count
remains higher, and paired complete timing is mixed. Query time is still 3.93%
above the control. Keep the API optional; no new structural coverage is claimed.

The next target is reuse of 22 repeated binary cores among 56 eligible queries,
with binary-local indices, checked full-source transport, edit invalidation and
charged cache/cold costs. Multiple blocks and production integration remain open.
All 1,228 tests, 59 focused tests, 408 chronological audits, 68 exhaustive truths
and full old/new replay pass. The union preserves 28,691 native, twenty-six affine
and forty-two v1 records, adding forty-two v2 alternatives without replacing them.

## 2026-11-18: exact binary-core discovery reuse

[Binary-core discovery reuse](binary-core-discovery-reuse.md) implements the 22
repeated-core opportunities on the unchanged 68-input pilot. Binary-local trees
are translated to current source indices and checked before substitution; binary
or coordinate edits miss the exact key. Null discovery outcomes are never SAT
answers. Native and compact proof payloads match byte-for-byte.

Acquisition graph/SCC work falls **44.53%**: constructed edges 4,276 -> 2,372 and
SCC visits 8,552 -> 4,744. The 34 entries use **11,906 serialized / 25,887 Python
object bytes**. Persistent mode adds 36,864 SQLite / 3,618 trial gzip bytes and
recomputes every entry at cold validation. Acquisition plus cold discovery thus
rises **10.94%** above the uncached control. Memory-mode complete timings have
mixed signs; persistent total gains are only 0.00091 / 0.00254 seconds with mixed
query timing. Keep both modes optional; this is no established production speedup.

**Next:** multi-block substitution on the twelve diagnosed sources with a second
disjoint block. Child solving still costs 51,326 propagation visits / 358 expansions.
Price proof size and child acquisition before claiming broader gains. Sharing the
other recognizers' graph construction remains a separate target: 8,344 subset
edges, 6,772 cover edges and 171 subset SCC calls are unchanged.

Resume `experiments/results/cnf-binary-core-cache/checkpoint.json`: all **28,691
native / 26 affine / 42 v1 / 42 v2** records unchanged, plus 34 discovery entries.
Old/new histories, 408 chronological queries and 68 exhaustive truths validate.
All 591 prior sources / 7,683 artifacts / 110 manifests are preserved. No new
coverage, Lean theorem or unrestricted-SAT resource bound follows.

All **1,236 full / 67 focused tests** pass, with 44 pre-existing SQLite warnings
in the full suite and none in the focused suite. The **223-page manuscript**
builds cleanly and all **64 previous proof blocks** are unchanged. Final source
ledger: **596**. New manifest: **39 artifacts**. Next preservation audit:
**7,722 artifacts / 111 manifests**.

## 2026-11-18: simultaneous blocks expose quotient-choice cost

[Multiple-block equivalence](multiblock-equivalence.md) checks disjoint supports,
unions signed maps and substitutes every source clause once. Single-block
negatives retain v2; multiple-block negatives use compact v3 with native negative
dependencies. Twelve pilot inputs now use two blocks. All cached/uncached
all-block acquisitions match, and old formats remain readable.

On the unchanged 68-source pilot, applied merges rise **45 -> 57** and propagation
falls **51,326 -> 51,059 (0.52%)**. But native expansions rise **358 -> 366**, native
certificates **398 -> 408**, and combined payload **492,731 -> 496,214 bytes**.
SQLite grows 4,096 / gzip 2,114 bytes. Query time falls in both orders; complete
cached deltas **-0.03893 / +0.00438 seconds** remain mixed. Keep this optional and
retain the measured storage regression; more substitution is not less acquisition.

**Next highest-value target: choose an already known quotient.** At actual query
prefixes 7 and 34, both streams already contain the one-block quotient while the
all-block quotient is new. Ignoring it costs five and three extra native records;
two other later queries add one record each after their history changes. Compare
the exact one/all quotient keys before fresh solving, with checked recomposition
and charged second-quotient construction, lookup, verification and storage. The
diagnosis is not an implemented saving or a search for the globally optimal subset.

Resume `experiments/results/cnf-multiblock-equivalence/checkpoint.json`: all
**28,691 native / 26 affine / 42 v1 / 42 v2 / 34 discovery records** preserved;
45 new native keys and eleven v3 records added. Native union: **28,736**.
Union growth is 81,920 SQLite / 6,918 compressed bytes. Old/new histories, 408
chronological queries and 68 source truths validate, with both quotient truths
checked on the twelve affected sources. All 596 prior sources / 7,722 artifacts /
111 manifests remain unchanged. No new Lean or unrestricted-SAT bound follows.

The **224-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,245 full / 76 focused tests** pass (44 pre-existing SQLite
warnings in the full suite, none in focused tests). Final executable source
ledger: **601**. New manifest: **39 artifacts**. Next preservation audit:
**7,761 artifacts / 112 manifests**.

## 2026-11-18: checked known-quotient choice and normalization cost

[Known-quotient selection](known-quotient-selection.md) checks the complete native
target, then the first-block target only on a miss, before fresh acquisition.
Correct canonical-name transport and the selected source evidence retain existing
SAT models and v2/v3 proof authorities. At most two alternatives are considered.

The 68-query pilot plus 36 excluded fresh sources recover **eight native nodes**
versus all-block acquisition (560 -> 552), saving **3,406 payload / 28,672 SQLite /
2,938 gzip bytes**. All eight native savings occur on the original pilot; the fresh
segment has the same 152 native additions under every policy. Four first-target
hits include SAT and UNSAT. Thirty-eight lookups and fourteen extra transforms
are charged. Mean complete time rises 1.00% versus all blocks, with mixed paired
deltas, and 2.47% versus single block. Keep the policy optional.

**Next highest-value structural reuse target: per-query normalization results.**
A separate identical-output solve profile places normalization and individual
SQLite commits ahead of propagation in elapsed cost. An exact census finds 505
repeats among 1,715 normalization calls; 469 repeats occur within one query and
cover 96.39% of repeated input literals. Peak per-query encoded input/result state
is 73,860 bytes versus 1,448,226 for the full stream. Test a bounded immutable cache
of the CNF/name-map/key triple; charge validation, copying, hashing, lookup,
objects and eviction. Reject booleans/floats before hits. These are opportunities,
not implemented savings. Transaction batching remains a separate durability task.

Resume `experiments/results/cnf-known-quotient/checkpoint.json`: all prior **28,736
native / 26 affine / 42 v1 / 42 v2 / 11 v3 / 34 discovery records** preserved; union
now **28,886 native / 53 v2 / 22 v3**. Full histories, 624 chronological queries,
104 truths, 36 fresh exclusions and both orders of all known choices validate.
The failed benchmark dispatch and profile-comparison setups are retained. All
601 previous sources / 7,761 artifacts / 112 manifests are unchanged. No new
Lean or unrestricted-SAT resource bound follows.

The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,253 full / 84 focused tests** pass. Final executable source
ledger: **607**. New manifest: **46 artifacts**, including the retained failed
setups and posthoc profile. Next preservation audit:
**7,807 artifacts / 113 manifests**.
