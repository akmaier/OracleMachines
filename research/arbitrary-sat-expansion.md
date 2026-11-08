# Arbitrary SAT through tractable classes and controlled interaction

8 November 2026. The user's priority is now minimum-cost expansion for arbitrary
SAT. Specialized affine constructors remain useful leaves of a general solver;
they no longer define the whole next milestone. The research target is to make
the difficult interaction between tractable parts as small and reusable as
possible, while accepting arbitrary input through a complete checked fallback.

## What class decomposition can establish

Two different decompositions must be separated.

- **Classify whole inputs.** Recognize which tractable family contains the
  formula and invoke its solver. A finite collection of polynomially recognizable
  classes with polynomial-time solvers would give a polynomial-time SAT solver
  if it covered every SAT instance. Proof: run the finitely many recognizers and
  the selected solver; a finite sum of fixed polynomial bounds is polynomial.
  This would imply P=NP. An infinite list of finite/easy classes does not give
  the uniform recognition and runtime bounds. Schaefer's theorem is about fixed
  Boolean constraint languages, not a classification of every possible structural
  partition of SAT inputs.
- **Split one input into parts.** Each piece can be easy while their conjunction
  is hard. The shared-variable compatibility problem must be solved exactly.
  Independent satisfiability answers suffice only for variable-disjoint parts;
  otherwise retain the exact boundary relation or condition on shared variables.

For fixed Boolean constraint languages, Schaefer's tractable cases are Horn,
dual-Horn, bijunctive (2-CNF definable), affine, and the common all-zero or all-one
satisfying cases; all other such language families are NP-complete. These are
properties of the entire allowed constraint language. Mixing individually easy
relations can leave all of these cases. The result does not say every individual
formula outside a listed syntax is difficult.
[Schaefer, STOC 1978](https://doi.org/10.1145/800133.804350).

| Component representation | Applicable algorithm | Recognition/composition obligation |
|---|---|---|
| Horn or dual-Horn CNF | Propagation, polynomial; standard implementations linear | Check literal polarity bounds; arbitrary added clauses can violate them |
| 2-CNF | Implication-graph algorithm, polynomial; standard implementations linear | Check clause sizes; preserve the shared-variable relation |
| Explicit XOR equations | Gaussian elimination | Do not assume that finding hidden XOR structure in arbitrary CNF is free |
| Supplied bounded-width decomposition | Dynamic programming, 2^O(w) times polynomial input work | Charge finding/checking the decomposition and intermediate relation size |
| Small backdoor to tractable residuals | Branch on backdoor variables, solve each residual | Charge discovery and up to 2^k residuals |
| Small component-backdoor depth | Alternate variable branching and independent components | Charge constructing the tree and its depth; no constant-depth guarantee for all SAT |

The width row refers to suitable standard primal/incidence decompositions and
their corresponding algorithms, not an interchangeable width definition.
[Fomin et al., backdoors to small incidence treewidth](https://sites.cs.ucsb.edu/~daniello/papers/BackdoorsTreewidth.pdf)
gives a concrete bounded-clause-size result and explicitly charges parameter
dependence. Input bounds and decomposition assumptions must travel with each
algorithm's claim.

## A constructive obstruction: two easy pieces can encode all SAT

Given any CNF F, introduce two indicators p_x and n_x for each original variable.
Replace a positive literal x by p_x and a negative literal by n_x. Put all
translated clauses, and (p_x OR n_x) for each variable, in F_plus. Put
(NOT p_x OR NOT n_x) for each variable in F_minus.

F_plus is positive and therefore dual-Horn. F_minus is negative 2-CNF and Horn.
If F has no empty clause, each part is immediately satisfiable on its own:
all indicators true for F_plus, all false for F_minus. Their conjunction requires
exactly one indicator per pair. Its assignments are therefore in bijection with
assignments to the original variables, and the translated clauses hold exactly
when F holds. The transformation has linear size in variables plus literals.
Empty clauses remain contradictions and can be detected immediately.

Thus solving the interaction of these two tractable parts already suffices for
arbitrary SAT. No novelty is claimed for this elementary indicator construction.
It pinpoints the gap in a proposed "solve every class separately" argument.
[The diagnostic](../experiments/results/sat-class-decomposition/diagnostic.json)
checks the complete assignment correspondence on 460 small formulas, including
every subset of the eight nonempty, nontautological clauses over two variables.
These tests supplement the argument; they are not a Lean proof or a hardness
lower bound for all expansion algorithms.

## The closest published approach

**Heterogeneous strong backdoors** allow different assignments of selected
variables to yield different tractable classes. Gaspers et al. study this exact
generalization. Their Horn/2-CNF example needs only one heterogeneous backdoor
variable even though homogeneous choices can grow. Discovery has its own
parameterized complexity; favorable results do not extend to every combination
of classes without assumptions.
[Gaspers et al., AAAI 2014](https://www.cs.ox.ac.uk/standa.zivny/publications/gmosz14aaai-preprint.pdf).

For a supplied strong backdoor B of size k, the elementary identity is

    SAT(F) = OR over assignments a to B of SAT(F restricted by a).

If each restriction is recognized and solved in at most p(L) work, evaluation is
at most O(2^k*p(L)), plus discovering/checking B. Choosing all variables always
makes residuals constant, so this covers arbitrary SAT algorithmically, but it
recovers exponential search when k is large. No bound k=O(log L) is established
for all inputs. The diagnostic reproduces the published heterogeneous example
at sizes 3/4: one branch yields Horn and the other 2-CNF. Its enumerative search
is explicitly combinatorial, not an implementation of the paper's FPT algorithm.

**Scattered classes** additionally allow different disconnected components to
belong to different tractable classes. Ganian, Ramanujan and Szeider give detection
results for specified finite conservative constraint languages. Those hypotheses
must not be discarded when applying the result to a SAT portfolio.
[Discovering Archipelagos of Tractability, TALG 2017](https://doi.org/10.1145/3014587).

**Component-backdoor depth** more directly targets interaction: alternate
conditioning with independent component splitting. Dreier, Ordyniak and Szeider
give algorithms for bounded depth into Horn, dual-Horn and 2-CNF. For a supplied
component-backdoor tree of depth d and linear-time base solvers, their evaluation
bound is O(2^d*L). Finding the tree is separate; their approximation algorithms
have their own parameter dependence. Bounded depth can handle families with
unbounded global backdoor size.
[SAT Backdoors: Depth Beats Size, ESA 2022](https://drops.dagstuhl.de/opus/volltexte/2022/16984/pdf/LIPIcs-ESA-2022-46.pdf),
[journal version, JCSS 2024](https://doi.org/10.1016/j.jcss.2024.103520).

This favors local branching followed by immediate decomposition over choosing
one global set of variables for every component. That is our design inference;
it is not a new tractability theorem or a guarantee of optimal choices.

## Proposed general expansion representation

Use a persistent graph of exact residual problems with three logical node types:

1. **A checked tractable leaf:** retain original residual identity, assumptions,
   family certificate and an exact answer or boundary representation.
2. **A variable split:** its children are the two exact restrictions; SAT combines
   by OR. Negative conclusions require both branches, unless an independently
   checked contradiction already applies.
3. **An independent component split:** components have disjoint remaining
   variables; SAT combines by AND. Shared variables require conditioning or
   explicit boundary relations, not independent positive answers.

Hash-cons equal residuals and retain their source-linked results. A syntax hash
must not authorize semantic equivalence on its own. Proven renamings and other
transports can increase sharing later. Complete fallback handles leaves outside
the selected families; admission caps must return fallback/unknown, never UNSAT.
This is a proposed extension, not the current native protocol.

For a new input or edit, the operational objective is

    discovery + exact source comparison + restriction/decomposition
      + sum(cost of newly required distinct residuals)
      + verification + graph maintenance + transport + persistence.

Minimizing backdoor size alone need not minimize this expression. Different
leaves have different costs; a slightly larger decomposition may reuse far more
previous work. Record actual affected nodes, residual bytes, successful verified
reuse and unsuccessful discovery attempts. Candidate plans need bounded search
budgets and a comparison with the existing checked fallback.

On append, keep immutable old versions and revisit affected residuals. Recheck
class membership and component connectivity: a new bridge clause can merge
components or invalidate a formerly useful backdoor. Reuse a model only after
checking the added constraints; a verified UNSAT subset remains valid under
conjunction but not under deletion of its supporting constraints. Invalidation
must follow these semantic conditions. Cold reconstruction and metadata scans
remain charged even when mathematical subresults are reusable.

## Limits on "minimum cost"

A universally polynomial construction and query bound, starting from a uniformly
constructible initial state and covering arbitrary SAT inputs in polynomially
many steps, would establish P=NP. This is a precise implication, not a proof that
the goal is impossible. Our practical objective can be a broad adaptive solver
whose exponential parameter is the remaining interaction, with measured gains
on inputs where that parameter or the number of novel residuals is small.

Compact exact representations also have representation-specific limits. Bova et
al. give CNF families whose DNNF representations require exponential size. This
is an unconditional obstruction for that representation, not for every possible
SAT algorithm or summary language.
[A Strongly Exponential Separation of DNNFs from CNF Formulas](https://arxiv.org/abs/1411.1995).

## Revised implementation priorities

The repository already has checked generic solving, disjoint-component reuse,
bounded-interface/source updates, symbolic proposals and explicit affine history
solving. It does not yet have a general heterogeneous component-backdoor planner
or dedicated native Horn/dual-Horn/2-CNF class constructors. Proof-fragment reuse
is not such a class portfolio.

1. Add cheap syntactic recognizers and certificate-producing Horn/dual-Horn and
   2-CNF leaves, preserving the existing checker boundary. Keep explicit affine
   input separate from unproved recognition of XOR structure in CNF.
2. Implement a bounded recursive planner that interleaves propagation, component
   decomposition and branching on variables involved in nontractable parts.
   Ensure completeness through the existing checked fallback.
3. Persist an exact dependency graph for residual identity, assumptions and class
   certificates. Update affected nodes and retain all old versions. Prove both
   OR-branch and AND-component recomposition against original input semantics.
4. Measure discovery, branch depth, component width, new distinct residuals,
   certificate checking, archive growth and cold replay. Compare the same full
   inputs with current checked CDCL, including connected hard cases and edits
   that destroy the selected structure.
5. Investigate improved backdoor/width discovery and structural equivalences
   based on those measurements. Report achieved bounds for each restricted
   parameter regime, plus honest worst cases for arbitrary SAT.
