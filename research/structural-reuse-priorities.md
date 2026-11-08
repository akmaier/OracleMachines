# Structural reuse: cost map and investigation priorities

Updated 2026-11-08 after the diagnostic of coordinated structural changes. This is the working
record for the hourly investigation. Start here; consult
[implementation history](implementation-gaps.md) and
[resource bounds](resource-bounds.md) for details. The ranking below is provisional:
we have useful matched synthetic controls, but no representative mixture of SAT
workloads from which to infer a single globally dominant cost.

**Next research experiment:** checked simultaneous repair for literal-equivalence
blocks. The new diagnostic finds 240 single-variable repair misses across 12
equivalence, parity and matching histories, although a supplied coordinated
change works in every case. Start with the equivalence case, charge recognition,
joint checking and state maintenance, and compare against current fallback.
Selective activation of the stronger index remains the smaller engineering task:
eager indexing roughly doubles allocations on compatible and sparse-ID streams.
Neither improvement has a measured replacement implementation yet.

## Current cost map

The arbitrary-CNF history/residual code is an experimental Python path. The
production restricted-family engines and Lean semantic results are separate;
their capabilities are not already integrated into one verified general solver.

| Workload regime | Current costly work and evidence | Most promising investigation |
| --- | --- | --- |
| A local change needs several variables to move together | All 240 updates in 12 constructed tractable histories still acquire a fresh base; none exhausts the repair budget. At 32 equivalence blocks of 32 variables, 32 units retain 33 bases / 3.79 MB logical payload. | Checked block changes, parity-preserving directions and matching swaps; share unchanged component source and state. |
| A small update defeats pure model reuse | New affected-clause repair removes all 32 original-control fallbacks. On matching size 16 / 128 protected flips it reduces operation time from 3.478 s to 0.147 s and logical payload from 12.46 MB to 0.158 MB. | Keep these gains while avoiding unnecessary index preparation; shared source/dependencies remain needed on genuine fallback. |
| A general residual escapes tractable recognizers | Branching creates distinct residuals; each is normalized, checked and persisted. There is no polynomial bound on their number. Existing matching recognition reduced one restricted example from 5,191 residuals to one. | Expose tractable components and small interfaces before branching; preserve useful state when a component changes class. |
| Reuse succeeds and the logical update is cheap | In the new 128-addition UNSAT diagnostic, SQLite execution and transaction-context exit account for about 87% of exclusive profiled time. | Reduce redundant archive work while preserving durability and version identities. |
| Sparse, very long variable identifiers | Near 2^1024, 32 updates retain 32,801 trie nodes. `map_get`/`map_set` account for about 62% of exclusive time in the new diagnostic. | Compress unary paths; compare exact-key representation and cold reconstruction costs. |
| The old assignment already satisfies every addition | Affected-clause indexing raises peak traced Python allocations from 249,217 to 473,849 bytes versus pure repair on the matched compatible stream. | Lazy or workload-selected index preparation, with activation cost charged. |
| One change affects many clauses | At 4,096 affected clauses, avoiding a new base still increases operation time from 109.99 to 125.48 ms; index preparation takes 103.32 ms. | Budget index activation and maintenance by anticipated reuse, not merely by avoided solver calls. |
| Restart, export or repeated events dominate | Cold repair replay can cost more than an isolated final base. Repeating a unit 128 times retains 10,719 logical bytes versus 1,393 for full-source semantic deduplication. | Separate shared semantic state from exact event provenance; measure cold validation and output costs explicitly. |

Evidence: [matched repair comparison](../experiments/results/cnf-repair-history/README.md),
[affected-clause comparison](../experiments/results/cnf-affected-history/README.md),
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

1. Identify the largest remaining **absolute** runtime or memory cost in the
   target workload, including acquisition, discovery, recognition, checking,
   serialization, persistence and restart. Profile a bounded representative
   sample if the dominant cost is unknown.
2. Choose one gap by credible recoverable cost, frequency across workloads and
   experiment cost. A large percentage gain on a tiny path is not enough.
   State the applicable structure and invalidation rule before implementing.
3. Compare old and new paths on matched growing cases: repeated and novel
   structure, class-preserving and class-breaking updates, cold and warm use.
   Preserve regressions and failed ideas. Charge index construction and updates.
4. Replace the affected cost-map entry with measured evidence; record the next
   bottleneck. Commit verified work. Report only meaningful changes or blockers.

Do not turn this into a repeated full review. If the evidence supports the next
experiment above, run it. Reorder the priorities when measurements justify it.

## Ranked gaps across SAT categories

### 1. Reuse coordinated structural changes

The current one-variable repair is too narrow even on easy subclasses. The new
[diagnostic](../experiments/results/structured-repair-gaps/README.md) supplies and
independently validates a coordinated change at every rejected step:

| Structure | Preserved internal invariant | Appropriate change |
| --- | --- | --- |
| Literal-equivalence block | All equalities, including signed variants | Change the block's independent representative and its dependent variables. |
| Affine equations A x = b over GF(2) | A(x + z) = b when A z = 0 | Apply a nullspace direction, potentially changing many variables. |
| Matching component | Choice coverage and resource exclusivity | Apply a valid alternating cycle/path, respecting earlier forced edges. |
| Horn component | Consequences of the retained facts/rules | Propagate a changed requirement with retained reasons; check negative constraints and couplings. |

The first three rows have concrete missed-reuse controls; the Horn maintenance
row is a proposed investigation. None is a general implementation claim.
Equivalence histories with 32 blocks of 32 variables currently spend 2.697 s and
retain 3,792,631 logical bytes for 32 unit updates, always acquiring a new base.
Matching with 32 independent 4-by-4 blocks spends 0.946 s and retains 2,267,324
bytes. These are current-path diagnostic costs, not predicted speedups. The
generator supplies the structure; automatic discovery has not been timed.

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

**Acceptance criteria:** remove the known equivalence-block fallbacks; preserve
old versions and cold checking; include coupled blocks, signed equalities,
contradictions, repeated changes within one block and large blocks with small
interfaces. Keep parity and matching cases as the next adapters. Do not generalize
the supplied moves into a uniformly cheap repair procedure for arbitrary CNF.

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
updates, sparse IDs and coordinated changes. All 249 tests pass; old versions
and cold verification are preserved. Lean proves the semantic protection rule,
not the count-map implementation. The 512-flip control falls from 5.059 s to
0.327 s and 8,921,728 to 83,082 logical bytes. The size-16 matching control reduces
peak traced Python allocation from 86,261,287 to 2,837,728 bytes. Cold replay and
index preparation become more expensive; see the retained losses above.
Single-variable
local search is classical; the research question here is checked persistent reuse
and its full cost, not novelty of flipping a Boolean variable.

### 2. Retain propagation and class-specific intermediate state

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
| Matching / reducible positive cores | Matching, choice/resource graph, reduction witnesses and Hall certificates. | Maintain disjoint groups, complete exclusion structure and justified redundant-clause reductions. Repair a matching locally when possible; overlapping choices can leave the class. |
| Explicit affine/XOR | Row basis, rank changes and projected boundary equations. | Reuse the existing restricted engine through checked extraction/source bindings. Recognizing hidden XOR structure in arbitrary CNF is additional work. New independent equations can change every relevant boundary. |
| Disjoint or bounded-interface components | Component identities, dependency graph and exact boundary summaries. | Update affected components and stop propagation when their summary is unchanged. Coupling components or increasing width may invalidate the cheap decomposition. |

Prioritize the category where a profile shows repeated construction to be costly.
Do not implement five dynamic data structures merely because all are available.
The current propagation loop repeatedly scans clauses; implication SCCs, matching
and connected components are reconstructed for new uncached residuals. These are
concrete maintenance gaps, not yet evidence of an end-to-end speedup.

### 3. Reduce hard interaction between otherwise easy components

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

### 4. Share source, certificates and summaries across class transitions

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

### 5. Remove representation costs where solving has already disappeared

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
