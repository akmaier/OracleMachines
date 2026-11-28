# Exact signed choices over conditioned forests

This investigation returns to structural coverage after the answer-certificate
cost work. It replaces the conservative treatment of a connected choice-conflict
component as one capacity-one resource with an exact finite-domain interaction
model. It is an optional experimental recognizer/checker, not a change to the
production dispatcher or the old evidence union.

## Recognition and exact recomposition

After canonicalization, demand clauses must be nonempty and have disjoint variable
supports. Their literals are signed choices. Every other clause must be a binary
exclusion of two choices. Source clauses are fully classified; an extra ternary
constraint cannot be silently omitted. Within-demand exclusions are permitted.
Raw support, including variables appearing only in tautologies, is retained when
checking a SAT model. Invalid CNF encodings are rejected.

A satisfying model can be reduced to one true choice per demand: setting other
choices false preserves every exclusion. Thus Boolean satisfiability is equivalent
to the existence of compatible representatives, although their full model sets
are different. The demand graph records cross-demand exclusions. Delete a supplied
cutset of at most two demands; the remaining graph must be a forest. Enumerate
cutset representatives, restrict remaining domains, and compute exact live choices
from leaves to roots. A value is live precisely when every child has a compatible
live choice. The checker verifies both included and omitted domain values.

Each branch covers a disjoint part of the representative assignment space. Any
checked successful branch lifts to a model of the original CNF. UNSAT requires
all branches to fail. A negative proper prefix is unknown. The checker rebuilds
the interaction graph from the source, checks acyclicity and local equations, and
never invokes demand discovery, cutset search, table construction or matching.
Persisted tables therefore have checked replay authority, not trusted outcomes.

Greedy source extraction makes two proposals (minimum clause width three, then
one), charges at most 4,096 total cutset candidates, and permits 50,000 construction
compatibility tests. These are separate caps; they do not bound source parsing,
verification, persistence, all transient memory or historical acquisition.
A recognition failure is not a SAT verdict or a proof excluding every possible
demand description. Given a checked description and fixed cutset size at most
two, complete tree computation is polynomial in explicit domain/graph size.
Allowing unbounded cutsets or arbitrary cyclic interaction does not inherit that
bound. The tree/CSP technique is established; the contribution here is its checked
integration and the measured boundary on our retained cases.

## Evidence and accounting

The protocol and four scientific source files are frozen before generating the
40 constructed inputs. All 37 earlier external inputs and the six-variable path
counterexample are retained, for 78 inputs total. Constructed shapes include
signed sparse renamings of paths, blocked paths, cycles, two linked triangles,
K4/K5 with tails, ternary edits, and random conflict trees. No outcome filtering
is used. These designed controls test structural recognition; they do not stand
in for a representative SAT distribution.

Three routes run in two opposite orders: the previous matching witness proposal,
forest-only recognition, and conditioning up to two demands. Six further fresh
processes replay persisted certificates with construction disabled. Process cold
means a fresh interpreter, not a flushed OS file cache. Discovery includes the
producer's internal check; a further independent check, encoding, gzip, writing,
RSS and replay are charged separately. No fallback is included. For unmatched
sources a stored null is only an unknown marker.

| Route | Constructed SAT / UNSAT / unknown | Old external SAT / unknown | Path SAT | Compact JSON / gzip bytes |
|---|---:|---:|---:|---:|
| Matching proposal | 4 / 0 / 36 | 1 / 36 | 0 | 3,782 / 3,146 |
| Forest only | 11 / 9 / 20 | 0 / 37 | 1 | 15,244 / 7,738 |
| At most two conditioned demands | 19 / 13 / 8 | 0 / 37 | 1 | 40,716 / 11,818 |

The constructed overlap is four answers shared with matching, 28 new-route-only
answers and eight unresolved by either route. The eight are K5-with-tail and
ternary-edit cases. Conditioning adds twelve answers beyond forest-only tables.
Matching still supplies one external answer (e036) outside the exact forest
schema; it is preserved rather than replaced. The old combined portfolio already
has witnesses for the five nonclique external cases. No new external or historical
union coverage is claimed. Original model checks remain authority for the old
proposal, even when it proposes a witness outside its strict matching class.

Costs below are means of two opposite-order trials over all 78 inputs. They solve
different numbers of cases and do **not** establish a solver speedup. Gzip totals
above include null markers for unknowns, which carry no solution authority.

| Route | Discovery (s) | Extra checking (s) | Encoding + gzip + write (s) | Process wall (s) | Cold worker / process (s) | Peak construction / replay RSS (bytes) |
|---|---:|---:|---:|---:|---:|---:|
| Matching | 0.04985 | 0.00093 | 0.00818 | 0.14753 | 0.00657 / 0.08735 | 40,730,624 / 39,911,424 |
| Forest | 0.06508 | 0.00540 | 0.00794 | 0.17185 | 0.01143 / 0.09084 | 40,779,776 / 40,026,112 |
| Cutset ≤2 | 0.09637 | 0.01129 | 0.00852 | 0.20916 | 0.01798 / 0.09592 | 40,894,464 / 40,255,488 |

Every certified forest case uses one representative branch. The four cyclic
controls use three branches each, and eight two-cut controls use nine branches
each. The tables summarize compatible subtree extensions; this run does not
implement a cross-edit table cache. A changed source must revalidate its complete
classification and table equations. Measurement noise and interpreter startup
matter at these small times; no fine-grained performance ranking is inferred.


## Remaining interaction and next step

All five previously retained fully described nonclique cases (e012–e015 and e031)
remain outside the new forest/cutset route. They are not newly unsolved SAT inputs:
earlier portfolio witnesses remain preserved. For each fixed proposed description,
the demand graph is connected, with 30 vertices, 60 edges and cycle rank 31.
An independent post-freeze census exhausts 1 empty, 30 singleton and 435 pair cuts
per case. The minimum remaining cycle rank after two removals is 21 for four
cases and 22 for e013. All selected minimizers still have one component of 28
vertices. Cycle rank is E-V+components; it is not treewidth or a runtime lower bound.
This establishes that no cutset of size at most two makes these particular demand
graphs forests. It says nothing about alternative demand descriptions.

Next: retain cycles inside small groups and check their complete separator
relations, starting with these five cases. A tree decomposition must certify edge
coverage and running intersection; its table width and all construction/replay
costs must be charged. This could expose a smaller interface than deleting enough
vertices to remove every cycle. Do not assume small width or discard hard cases.
Then freeze fresh sources and adversarial edits before claiming transfer.
Unclassified constraints, alternate source descriptions, larger separators,
preprocessing costs and efficient unrestricted SAT remain explicit gaps.

## Verification and reproduction

Fifteen focused tests cover the original nonclique path, complete cross-conflict
UNSAT, one/two-cut cycles, positive and negative prefixes, sparse signs, duplicate
and tautological input, source edits, invalid tables/schemas, cap stops and cold
replay with constructors disabled. Independent truth checks reproduce 3,880 small
CNFs, including all 512 two-variable clause sets and 3,304 three-variable sets of
at most three clauses. They also exhaust all 4,096 cross-conflict subsets of three
binary demands and all 12,288 branch prefixes, alternating within-demand
exclusions. Boolean models and representative models are enumerated independently.

All **2,723 full and 15 focused tests pass**. The full suite takes 281.443 seconds;
its existing unclosed-SQLite ResourceWarnings are retained in the log. All measured
certificates, outcomes, producer/checker counters and panel generation reproduce.
The two independent semantic runs and two interaction-census runs agree.
Validation checks **256 prior manifests and 85,223 artifact entries**,
preserves all **1,388 earlier scientific sources**, and adds four frozen scientific
files (1,392 total). All **93 earlier proof blocks** and 3 publication snapshots
are preserved; the manuscript adds one proposition/proof (94 total).


Commands (from repository root):

```sh
python3 -m unittest solver.test_cnf_choice_forest
python3 -m unittest discover -s solver
python3 experiments/validate_cnf_choice_forest.py semantic experiments/results/cnf-choice-forest semantic-audit-reproduced.json
python3 experiments/validate_cnf_choice_forest.py validate experiments/results/cnf-choice-forest
python3 experiments/results/cnf-choice-forest/interaction-census.py interaction-census-reproduced.json
```

The initial freeze/panel/worker commands are intentionally one-shot and should
use a new output directory for a new measurement. Resume
`experiments/results/cnf-choice-forest/checkpoint.json`, key `choice_forest`.
Older history, failures, formulas, proofs and publications remain intact.
