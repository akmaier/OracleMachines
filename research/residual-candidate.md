# Searching for a uniform CNF bound through reusable residuals

8 November 2026. The requested target is now a uniformly polynomial algorithm
covering every CNF, with all acquisition included. No such bound has been proved
here. This file records concrete candidates, measured failures, and the precise
remaining obligation rather than treating favorable data as a complexity proof.

## Candidate 1: heterogeneous residual decision DAG

`experiments/cnf_residual_dag.py` implements the next portfolio milestone from
`arbitrary-sat-expansion.md`: unit propagation, Horn/dual-Horn/2-CNF leaves,
independent component splitting, exact normalized residual reuse, and complete
variable branching as the mathematical fallback. Actual execution has a node
budget and Python stack/memory limits; exhaustion reports no verdict. It is a
research prototype with independently checked Python certificates, not a new
trusted path in the Lean-backed production solver.

For one input of bit length L, let M count newly expanded residuals. Each
normalization, class test, propagation pass sequence, graph computation, witness
check, and structural certificate edge has polynomial work in L. A fresh run
can therefore be bounded by M times polynomial local work, plus exact key/index,
serialization and archive costs. SQLite key comparisons involve both key length
and archive size. The implementation also scans the archive for its final size
report. Full CNF keys and their copies on proof edges consume space; no ideal
hash or free canonicalization is assumed.

The missing implication is **M(L) <= poly(L) for every CNF**, or a representation
that avoids visiting those states with polynomial discovery, maintenance,
evaluation and checking costs. Merely noting that each branch removes a
variable yields a binary branching recurrence, not a polynomial bound. Arbitrary
semantic equivalence is not available as a free merging operation: deciding
whether a CNF is equivalent to false already decides UNSAT. The implemented
syntactic normalization is deliberately sound and incomplete.

On a stream, total acquired state includes residuals from earlier inputs. Warm
lookup does not erase acquisition. Cold negative checking traverses the needed
certificate DAG and can be proportional to the whole prior proof. Physical
Python/SQLite memory, cold replay, and bit costs remain outside a fully formal
machine-level bound. None of the small measurements proves or disproves the
existence of a different uniformly polynomial algorithm.

[The first experiment](../experiments/results/cnf-residual-dag/README.md) preserves
26 inputs, four matched acquisition modes, warm/cold replays, and every acquired
certificate. Repeated components show useful exact reuse. Novel components and
pigeonhole instances expose increasing acquisition. Disabling decomposition
occasionally improves the count, so the policy itself needs cost control.

## Published context and the implemented matching leaf

Residual caching and component decomposition are established methods, including
[Sang et al., SAT 2004](https://www.satisfiability.org/SAT04/accepted/65.html) and
[Huang and Darwiche, IJCAI 2005](https://ijcai.org/proceedings/2005/98). We do not
claim a new general SAT architecture or a lower bound for every possible solver.

The pigeonhole growth has a specific remedy: recover the underlying matching
problem instead of repeatedly searching assignments. The `alldifferent`
matching connection is classical
[Régin, AAAI 1994](https://cse.unl.edu/~choueiry/Documents/ReginAAAI-1994.pdf).
Lenchner's 2019 preprint explicitly studies a matching-derived tractable SAT
class, CMP-SAT, beyond the familiar Horn/2-CNF/XOR syntax
([arXiv:1904.07218v4](https://arxiv.org/abs/1904.07218v4)). This is a relevant
precedent, not a claim of novelty or an assumption that every CNF has that form.

The next revision implements this recognition and a polynomial augmenting-path
solver. It accepts disjoint positive choice groups and negative pairwise
exclusion cliques, returning either a checked source model or a deficient Hall
set. Optional variables without positive occurrences can be false. Recognition
rejects overlapping choice groups and non-clique conflict components. Tests
include small satisfiable counterexamples to both unsound relaxations.

Correctness has two directions. A satisfying assignment chooses a true variable
from each disjoint positive clause, and negative cliques require distinct
resources. A covering matching chooses one variable per positive clause from
distinct resources; setting precisely these variables true satisfies the CNF.
A Hall set with fewer neighboring resources than choice groups forbids the
required injection. The manuscript now states and proves this reduction.
Lean checks the abstract cardinality obstruction, not the whole implementation.

Recognition scans the normalized clauses and conflict graph, including clique
completeness. Sorting and normalization are charged. With p choice groups and e
choice-resource edges, matching uses O(p*e) graph traversals after adjacency
sorting; auxiliary graph space is O(p+e+v), in addition to the explicit conflict
graph and source representation. Hall checking repeats recognition and collects
the selected neighbors, without the prior residual search. These are standard
polynomial algorithms, not machine-level Lean runtime bounds. The repeated-scan
unit propagation before recognition also has its own O(v*L) literal-visit bound.

[The matching experiment](../experiments/results/cnf-matching/README.md) preserves
153 decisions over 39 inputs, including 36 matched acquisitions. Nine pigeons
into eight holes drop from 5,191 residuals and 17,290,081 logical bytes to one
residual and 6,208 bytes. Cold negative checking drops from the full dependency
graph to one source/Hall check. Matching-only scaling through 48 holes retains
one residual, but input and retained source grow; this is not constant cost.
All 104 previous result archives reload with no changed or new rows.

## The next mathematical gap: overlapping choices

Allowing arbitrary overlap between the positive clauses already suffices to
encode every CNF while retaining conflict cliques of size two. The indicator
construction in `arbitrary-sat-expansion.md` replaces each original x by p_x/n_x,
translates original clauses to positive clauses, and adds (p_x OR n_x) and
(NOT p_x OR NOT n_x). Negative constraints are disjoint pairs, and exactly one
indicator per pair is true. The original CNF and the transformed instance are
equisatisfiable by direct assignment correspondence.

Consequently, this is a precise smaller-looking target for a uniform solution:
**solve arbitrary overlapping positive requirements under disjoint complementary
pairs, with all discovery and acquisition polynomially bounded.** Ordinary
matching does not solve it: the same chosen variable may satisfy several
positive clauses, so one resource per clause is no longer the right invariant.
The five-variable near miss in the experiment exhibits that failure directly.

There are useful intermediate questions, without a universal conclusion:

1. Remove redundant positive supersets, then check whether the remaining minimal
   choices are disjoint. Laminar choice families have disjoint minimal members;
   this extends recognition at an explicitly charged subsumption cost.
2. Identify a small set of variables responsible for positive overlap. Fixing
   them leaves disjoint choices; with the clique-exclusion syntax, propagation
   then exposes a matching leaf. Enumerating k such variables costs up to 2^k
   polynomial work, including recognition; no small k is proved for all CNFs.
3. Seek a richer exact summary that represents shared satisfaction of multiple
   positive clauses without enumerating all combinations. Bound intermediate
   size and construction, not only final representation size or observed hits.
4. Connect the recognizer and Hall certificate to the original-source Lean
   checker before enabling this experimental route in the production service.

This is the current point at which a universal polynomial proof remains open.
