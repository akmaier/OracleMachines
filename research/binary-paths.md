# Binary implications reduce wider clauses, with a coverage/cost tradeoff

9 November 2026. `BinaryPathInventory` is an optional, checked preprocessing
extension. It raises full-corpus structural coverage from **898/985 to 901/985**,
with four gains and one bounded-search loss, but discovery increases **19.06%**
and fresh archive size **13.93%**. **Do not promote it as the default policy.**
All ordinary SAT answers agree. Earlier results and the failed case remain intact.

## What selected this experiment

The previous unit-count experiment lacked evidence on binary-free formulas. We
therefore inspected binary relations after conditioning, preserving the diagnostic
in `cnf-binary-paths-frontier/exploration.json`. All 106 original unresolved leaves
have acyclic binary graphs. Their four candidate splits expose 58 cyclic and two
binary-conflicting raw branches among 848 branches; most are already handled by
the existing reductions. After the extra-depth baseline, 53/54 remaining leaves
still have acyclic graphs. SCC compression alone offers limited new coverage here.

Transitive paths are more broadly useful: an unrestricted diagnostic finds 334
removable wide clauses in 92/106 original leaves. This is an opportunity count,
not 92 new closures. The implementation then bounds reachability to 64 roots per
residual and charges its work in matched acquisitions. The root limit does not
bound arbitrary SAT complexity.

## Established literature and the exact rule

[Heule, Järvisalo and Biere (2010)](https://www.cs.helsinki.fi/u/mjarvisa/papers/heule-jarvisalo-biere.lpar10.pdf)
study hidden clause elimination. Their [2011 Unhiding paper](https://www.cs.helsinki.fi/u/mjarvisa/papers/heule-jarvisalo-biere.sat11.pdf)
uses binary implication graphs to simplify larger clauses, including inexpensive
approximations of reachability. The present rule is a restricted established
hidden-tautology simplification with explicit retained reasons, not a novel SAT
class or inference rule. The implementation and total-cost comparison are ours.

Let B be the binary clauses of F. An edge x -> y must name an **actual original
binary clause** (-x OR y). If a wide clause C contains a and b, a path -a -> b
in B proves C redundant. A model of the retained clauses either satisfies a or
follows the path to b. Because only clauses of width at least three are removed,
all binary reasons remain; any number of such deletions can be checked together
without circular justification. F and the retained formula have identical models
over the original variables. Variables appearing only in deleted clauses may be
assigned arbitrarily when extending a retained model.

These are original-formula implications. Taking pairs from a wide clause would
be unsound here; the checker rejects such a reason. This differs from the auxiliary
pair formula used to recognize Horn renamings. No auxiliary UNSAT result is used
as a refutation of the original formula.

## Implementation and persistence

The pass follows existing family, independent-component, simplification,
projection and checked-probe reductions. It precedes arbitrary conditioning and
terminal subset/renaming checks. A reduction leads to the exact normalized child
at the same conditioning depth. Clause count strictly decreases, and the child
cannot gain variables. Every parent, failed alternative and source binding remains
in the append-only archive.

Discovery builds the binary graph once per invocation and lazily searches at
most 64 distinct roots. It shares each reachability predecessor tree across
candidate clauses. Only proof prefixes needed for actual deletions persist:
`[root_literal]` starts a proof, `[parent_id, target_literal, binary_clause_id]`
extends it, and `[wide_clause_id, endpoint_id]` binds a deletion. Common prefixes
share proof IDs. Parent IDs must precede children. The checker validates every
edge, root/endpoint membership, unused fragments, retained binary reasons and the
exact reduced child. It performs no reachability search.

An empty proposal is deliberately inconclusive. The checker establishes sound
deletions, not completeness of the proposal search, its exact unsuccessful visit
order, or optimality of the selected proof. Source/policy keys prevent accidental
reuse under edits. No reachability cache persists across different source nodes.
Reusing such tables after deletion would require translating binary clause IDs
and normalized variable names, not trusting old indices.

## Full and controlled results

The [full comparison](../experiments/results/cnf-binary-paths-full/README.md)
uses the original 1,497 cases and depth/candidate/probe/learning budgets. The
added pass has its own charged 64-root cap; this is not equal total work.

| Measure | Retained baseline | Binary paths |
| --- | ---: | ---: |
| Non-tiny structural closures | 898/985 | 901/985 |
| Discovery/checking/persistence (s) | 81.47602 | 97.00720 |
| Total with ordinary solver/lifts (s) | 122.46371 | 139.46329 |
| Cold complete replay (s) | 52.18170 | 59.56008 |
| Warm inventory replay (s) | 0.27879 | 0.29428 |
| SQLite bytes | 417,370,112 | 475,529,216 |
| Pattern nodes | 22,071 | 25,578 |
| Selected unresolved leaves | 106 | 100 |
| Their literal occurrences | 32,404 | 31,283 |
| Six-case Python peak bytes | 20,286,044 | 22,804,740 |

Sources **1007, 1065, 1072, 1363** gain closure; **1471** loses bounded closure.
All five are satisfiable. `loss-alternatives.json` traverses every saved alternative,
not only the differing selected plans. It isolates a shared depth-one residual:
the old sequence 21,26,1 closes at variable 1; after equivalent deletion, the
candidate list is 21,26,13,16 and all four fail to close. Names remain unchanged.
The original successful plan is still stored. Logical equivalence does not
preserve this heuristic's bounded coverage. The two archives' union covers
**902/985** known inputs, but an efficient combined acquisition policy is absent.

The [106-leaf frontier comparison](../experiments/results/cnf-binary-paths-frontier/README.md)
closes 63 instead of 60, gaining cases 6,13,85 without loss. Discovery rises
5.24072 -> 6.05264 s. An [early direct-only control](../experiments/results/cnf-binary-paths-direct-control/README.md)
retains 60 closures; the transitive pass repeats all three gains. This separates
transitive reasoning from merely moving direct binary subsumption earlier.
The [96 fresh inputs](../experiments/results/cnf-binary-paths-fresh/README.md)
keep 75 closures under both policies, with discovery 1.78640 -> 2.26810 s.
Fresh cases use a new frozen seed, signed permutations, clause edits and disjoint
Horn mixtures. These synthetic samples support no industrial or general speedup.

## Sharing is not automatically compression

The full acquired graph has 3,555 reduction nodes and 9,870 removed wide clauses
(29,853 literal occurrences), including 3,797 without a direct original binary
subset witness. These include failed alternatives and repeated contexts, so they
must not be reported as original-source gains. Shared proofs contain 21,894 nodes,
compared with 25,359 root-and-path nodes in separate per-clause witnesses.

The **serialized result reverses that apparent saving**: positive shared
certificates occupy 334,245 bytes, whereas explicit independent paths occupy
230,535 bytes in the documented comparison encoding. All proposal records,
including inconclusive ones, occupy 456,745 bytes. Selecting the smaller encoding
would help locally, but even the entire proposal payload is much smaller than the
58,159,104-byte archive increase. Full parent/profile/key copies and extra acquired
states dominate. Historical archives are retained, not replaced by a smaller run.

For m clauses, L literals, v variables, m2 binary clauses, q searched roots and p
proof nodes, discovery costs O(m+L+q(v+m2)+sum(width(C)^2)+p+|D|) word operations
under ordinary hashing. Reachability retains O(qv) entries, with q<=min(64,2v)
under the measured policy. Independent checking costs O(m+L+p+L_D), where L_D is
the removed-clause literal count. Variable/ID bit costs, serialization and all
recursive states remain explicit. No compact closure for arbitrary SAT follows.

The separate cold source-1445 profile still leads with reconstruction (2,313 calls,
0.35722 s own / 0.51925 cumulative), propagation (2,349, 0.24361 / 0.38954) and
normalization (1,055, 0.22078 / 0.56271). The added source validation itself has
297 calls / 0.05277 s own. These instrumented costs are not full-history timing;
nested cumulative times overlap and must not be summed.

## Proofs, checks and next targets

Four new Lean lemmas in `Residuals.lean` prove binary edge soundness, path
soundness, clause entailment and simultaneous batch model equivalence. The graph
relation requires a retained binary clause in either order. Lean does not verify
Python clause indices, DAG serialization, normalization, persistence or scheduling.
The full build/axiom audit passes: **4,148 namespace declarations / 1,988 theorem
declarations**. All **461 Python tests** pass, including exhaustive small models,
signed edits, false wide-clause reasons, cyclic proofs, old-row preservation,
independent cold replay and the direct-only control. Cold checks verify all saved
nodes/sources/solver certificates without changing bytes. Warm replay inserts no
rows. All 62 previous manuscript proof blocks survive, with one new proposition.

The next priorities are (1) reuse already-proved plans through equivalent-state
changes without losing their bounded closure, (2) avoid repeated preparation and
full intermediate state around this useful reduction, and (3) test certified
literal elimination using the same binary relations to expose additional classes.
The last technique is also established; its source transport, scheduling and
total cost need a separate experiment. None is implemented by this checkpoint.
