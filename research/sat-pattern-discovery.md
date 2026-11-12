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
