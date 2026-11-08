# Structural reuse: cost map and investigation priorities

Updated 2026-11-08 after the user's shift toward pattern discovery and a valid
partition of the entire SAT problem. This is the working record for the hourly
investigation. Start with the [discovery plan](sat-pattern-discovery.md), then
consult [implementation history](implementation-gaps.md),
[resource bounds](resource-bounds.md) and the measurements below.

**Primary objective:** discover useful SAT categories and exact decompositions
from arbitrary CNF input, retaining explicit coverage of unresolved cases.
Recognized-family optimization continues as supporting work. A complete
classification and efficient solution of every resulting cell are separate
obligations; retain overlaps, checked recognition and composition costs.

**Next research experiment:** build an audited pattern inventory over the existing
residual solver. Record all recognition outcomes, source-linked certificates,
components, interfaces, conditioning and unresolved residual structure. Test
unlabelled inputs, exhaustive small CNFs, renamings and class-changing mixtures.
Use the unresolved cells to select the next discovery improvement. Measure
coverage and remaining interaction as well as full runtime and memory costs.
Do not treat "known families plus fallback" alone as the achieved partition.

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

The first priority is the [audited pattern inventory](sat-pattern-discovery.md).
Retain overlapping class certificates and make the recognition-outcome partition
exhaustive. Then refine unresolved cells through component-local recognition and
conditioning, with costs and counterexamples attached. The existing residual
solver already performs several tractable-leaf and decomposition operations;
the next work makes their coverage inspectable and extends what they discover.

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
