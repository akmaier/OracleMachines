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

## Published context and next structural target

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

Next: recognize disjoint positive choice groups and negative pairwise exclusion
cliques, solve the resulting bipartite matching problem, and retain either a
checked source model or a deficient Hall set. Recognition must reject overlapping
choice groups and non-clique conflict components unless a broader equivalence
is proved. Measure this added leaf on matched pigeonholes, satisfiable domain
assignments and near misses. This attacks a demonstrated gap without treating
the growing list of tractable families as a complete polynomial cover.
