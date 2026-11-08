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
   choices are disjoint. This is now implemented below. The next expansion cost
   is repeated source scanning and copying despite reuse of the unchanged core.
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

## Checked positive cores and redundant expansion

The next revision removes inclusion-nonminimal positive clauses before matching,
decomposition or branching, after unit propagation and the cheaper class leaves.
If a retained positive clause C is contained in D, requiring C already requires
D. Removing D preserves every model, with the negative and mixed clauses left
unchanged. Every deletion records a direct retained source-clause witness; no
chain or circular justification is accepted. The normalized reduced core is
looked up in the same persistent residual archive. A new negative source node
contains the deletion witnesses and exact core key; the checker validates the
containments and the negative child. Positive source nodes retain full checked
models. Old certificate kinds and keys keep their previous interpretation.

This is established **syntactic subsumption**, described explicitly in Section 3
of [Een and Biere, SAT 2005](https://www.cs.toronto.edu/~fbacchus/csc2512/Readings/EenBiere-SAT05.pdf).
The improvement here is its measured integration with this candidate's matching
leaf and persistent core reuse, not a new general SAT result.

For a finite family of nonempty positive clauses, each member contains a minimal
member. If the family is laminar (any two members are nested or disjoint), distinct
minimal members must be disjoint: nesting would contradict minimality. Thus a
laminar positive family with disjoint negative exclusion cliques reduces to the
proved matching class. Laminarity is sufficient, not necessary: crossing redundant
supersets also disappear if their minimal members are disjoint. Irreducible overlap
does not disappear; the arbitrary-SAT indicator construction remains a barrier to
claiming a universal bound from matching alone.

### Discovery, checking and retained space

Let L be literal occurrences, p positive clauses and w maximum positive width.
Process positives in increasing length, with deterministic tie order. Store each
retained clause under its least frequent literal in the current positive family.
For an incoming clause D, inspect postings of literals in D and verify full
containment for each candidate C. Every genuine C subset D must be reached because
its indexed literal lies in D. The anchor is a filter, not a proof or semantic
equivalence oracle. Previously retained clauses cannot be superseded by a shorter
one later in this order. No quadratic all-pairs scan is needed on disjoint choices,
but worst-case candidate count is still O(p^2), with O(p^2 w) membership probes.
The pass also scans L, builds sets/frequencies, and sorts the positives; those
costs, and variable-ID bit costs, are additional. The index and witnesses use
O(L+p) words conservatively. These are algorithmic bounds, not a Lean runtime
refinement or an assertion of constant-time Python hashing.

For deletion pairs (D,C), checking scans O(sum(|D|+|C|)) witness payload, plus
source canonicalization and core reconstruction. Cold UNSAT replay checks the
source wrapper and the core's dependency DAG; it does not rerun discovery or
matching search. If the core itself is a matching leaf, that is two checked
nodes. SAT replay checks the full source model without loading the core.

Once a core is acquired, each fresh source reducing to it needs one new source
node and no new core search. This does **not** make expansion constant cost:
normalization, full-source reduction, source verification, exact key lookup,
serialization and SQL costs remain. Current retained logical space is
O(B_core + sum_t (B_source_t + B_core_key + r_t log m_t)) for UNSAT wrappers,
where r_t is deletion count and m_t source clause count; SAT wrappers store a
source model instead of a core reference. Full keys, full source copies, SQL
index/page overhead and the checked in-memory node dictionary remain. In a
history whose source grows linearly, those per-version copies can yield quadratic
cumulative source payload even though the logical core never changes. The final
archive-size query also scans all stored rows. No delta-size update or total-RSS
bound is claimed.

The reuse condition is an exact normalized core, not merely the same answer.
Adding a superset preserves that core when it has a retained subset witness and
the other clauses stay unchanged. Deleting or weakening the supporting clause,
altering conflicts, or adding an uncovered clause requires reconstruction and a
new exact key. It may still happen to yield an old core, but that must be checked.
The pass is rebuilt on every new source; it maintains no incremental index yet.

`Residuals.lean` now proves positive-clause containment, preservation of all
models by a covered retained core, and coverage under a witnessed extension.
These statements do not verify the Python encoding, index, certificate checker
or database. The source-level mathematical proof and the implementation's tests
remain separate evidence.

Matched static and growing-history results are preserved in the
[positive-core experiment](../experiments/results/cnf-subsumption/README.md).
The next practical target is to retain the containment index and source deltas,
with source-linked witness invalidation, so unchanged structure is neither
rediscovered nor copied in every version. This addresses the remaining cost on
redundant expansions. It does not settle the separate arbitrary-overlap problem.

## Delta histories avoid repeating the unchanged source

`experiments/cnf_positive_history.py` adds an explicit prepared-state interface.
It solves a base CNF once, checks its source-to-residual binding, and builds an
index over its positive clauses. A version names that base and an immutable
parent/delta sequence. `append(parent, D)` accepts a nonempty positive clause
only after finding and checking a base clause C contained in D. It stores D,
the source-clause witness index, and integer parent/base references. Each version
denotes the original base followed by exactly its stored additions, including
duplicates and input literal order. Full source and full residual keys are not
copied into every version. The old residual table and certificate meanings are
unchanged; all new records use separate versioned tables.

The invariant is equality of models with the fixed base, not merely equality
of SAT answers. Every positive addition follows from a base clause, and all
other clauses are unchanged. A SAT base model satisfies every addition; variables
absent from the base can remain false. An UNSAT base remains UNSAT. The Lean
theorem `positive_history_models` proves the corresponding positive conjunction
invariant for an entire list of covered additions; unchanged background clauses
can be conjoined on both sides. This does not verify Python, SQL, or runtime.

### Recognition and invalidation

The index uses one least-frequent base literal per positive base clause. A
proposed D probes postings for its literals and checks full containment. The
independent checker verifies the recorded witness against the fixed base. A
successful warm append neither rescans the source nor rebuilds the index. The
parent must already belong to a valid history; an arbitrary supplied full CNF
cannot acquire this guarantee from a version number alone.

Uncovered positive additions raise `UnsupportedExpansion`, supplying no verdict
for that edit. The comparison driver explicitly materializes the parent source,
appends the new clause and acquires a fresh base by ordinary solving. Negative
additions, deletions, changed clauses or variable reinterpretation also require a
new base; this append API cannot express them. Older roots, branches and proofs
remain unchanged. Repeating the same parent and clause reuses its existing
version; appending an identical clause to a later parent records a new event.

IDs are local to one append-only archive and name checked records, not globally
canonical formulas. They are neither portable hashes nor authenticated external
identities. The prototype assumes the archive is not mutated outside its API
after a record has entered the checked memory cache. Cold validation rejects
cycles, cross-base parents, missing rows, unsupported operations and invalid
source/certificate bindings. This is a single-writer research interface, not a
new production trust or concurrency guarantee.

### Expansion, cold checking and storage bounds

Let the acquired base have p positive clauses, maximum positive width w, source
bit length B0, and K0 bits of residual records retained by base acquisition.
For a delta of d literal
occurrences, let c_D be the number of indexed candidates inspected (at most p).
Discovery builds the delta membership set, sorts its distinct literals, and
performs at most c_D w containment probes. The checker additionally reads the
delta and its selected witness. Serialization is proportional to the delta's
encoded length plus metadata. SQL index lookup/insertion and integer reference
bit costs depend on archive size; no constant-time database or Python hashing
assumption is part of a formal bound. With a checked parent and cached base,
there is no term for scanning all previous source clauses or re-solving the
base. Base preparation and index construction remain fully charged once per base.

For T additions over a fixed base, additional retained payload beyond a
preexisting archive is O(B0 + K0 + sum_t B_delta_t + T log(N+T+m0+1)) bits
conservatively, where m0 is the base clause count, N bounds preexisting record
counts and integer identifiers,
and metadata includes parent/base/witness IDs and record
framing. Fixed format strings contribute O(T). The resident history cache and
index retain the same records without materialized prefixes; Python object and
SQLite page/index overhead still matter. This avoids sum_t B_source_t full
prefix copies for this restricted update language, not for arbitrary edits.
The exact old residual-key representation is still used inside the base proof.

Cold query validates the needed base proof, constructs its index, and checks
every ancestor delta on that version's path. Its work grows with that path's
total payload and SQL lookups. Warm queries use checked version metadata. No
constant-cost restart is claimed. Explicit `materialize` assembles one full
source using immutable clause references and traverses the path; serializing or
independently checking that output still incurs its full payload cost. Exporting
a SAT witness copies the base assignment, with omitted variables false. Optional
archive-size statistics scan stored rows and are reported separately from append.

Two limits are deliberately tested in the
[history comparison](../experiments/results/cnf-positive-history/README.md).
Repeated identical clauses can be cheaper for the old canonical full-source
cache, while this exact event history retains each occurrence. Frequently novel
constraints force fresh bases, retain more setup metadata, and lose the fixed-base
storage guarantee. A favorable redundant stream therefore establishes neither
minimum work on every input nor a uniformly polynomial arbitrary-SAT solver.

The original positive-subset path remains available. The following extension
now implements the previously identified monotone UNSAT shortcut and checked
reuse of one surviving SAT model.

### Refutation and fixed-model additions

`append_decision` accepts any signed integer clause (including an empty clause)
when the fixed base is checked UNSAT. Otherwise it checks whether the fixed base
model satisfies the added clause, with every omitted variable false. If so, the
same model still satisfies every previous addition. This preserves SAT status
but can remove other base models. A failed model supplies no answer and changes
no rows; it can require a different SAT model or a refutation from fresh solving.
Deletion and replacement remain unsupported.

The new record kinds retain the clause and exact parent/base references. Cold
replay checks the rule against the checked base and every ancestor, including
mixed old positive-subset records. Warm additions validate the whole clause;
SAT requires at most two probes per literal across admission and record checks,
while UNSAT requires none. There is no containment-candidate factor, base scan
or residual solve on an accepted warm append. Bit serialization, integer/hash
lookup, SQL operations, preparation and cold proof replay remain charged. The
same fixed-base payload bound applies without the subset witness index. This
is a representation-level bound, not a verified machine-cost theorem.

[Matched evidence](../experiments/results/cnf-decision-history/README.md) retains
22 histories, 3,894 correct decisions and 66 archives. For size-16 SAT and 128
compatible signed additions, positive history needs 129 acquired bases and
15,195,873 logical bytes; decision history needs one base and 99,170 bytes.
Summed operation time is 3.611 versus 0.04691 seconds in single samples. The
full-source comparison uses 9,235,556 bytes and 2.781 seconds. All 313 preceding
archives replay unchanged. These are synthetic interface comparisons, not peak
RAM or competitive-CDCL results.

Repeated identical clauses still lose to canonical deduplication. Thirty-two
fresh positive units still force 32 fallback acquisitions; the fixed model sets
new variables false. Cold replay can also lose: at size-16 UNSAT it takes
10.13 ms versus 5.94 ms for positive history's isolated final base and 1.57 ms
for the full-source cache after an explicit empty clause. No universal speedup
or all-input polynomial acquisition follows.

Next work should share source structure across new bases and allow small checked
model repairs, with explicit occurrence/invalidation conditions. A truly fresh
variable can be assigned without breaking old clauses, but a variable absent
from the base model may already occur in earlier deltas. Repeated-event
compression and cold checking also remain. The general irreducible-overlap and
unrestricted polynomial-construction obligations are unchanged.


### Checked single-variable repairs with shared support

`experiments/cnf_repair_history.py` implements the first model-repair case.
A failed assignment can set a literal in the new clause true if the opposite
literal occurs nowhere in the parent source. This sufficient condition protects
all old clauses and includes genuinely fresh variables. A shared immutable
binary trie stores positive/negative occurrence flags and the current truth
value per variable, including every earlier delta and original tautology. Each
version retains a root; changed paths are copied, not the full source or model.
Cold replay rebuilds and checks these derived indexes from the exact history.

At most O((d+1)b) trie node operations suffice for an accepted warm d-literal
addition with identifiers of at most b bits, plus syntax, serialization and SQL
work. Integer shifts/comparisons and allocation require separate bit accounting.
Preparation scans the base, cold checks traverse required ancestors, and witness
export traverses the current trie. Retained map nodes grow with copied paths;
long sparse identifiers expose extra memory even though durable storage retains
only base/clauses/repair deltas. These are tested representation bounds, not a
verified machine-cost theorem. The pure-literal rule itself is elementary.

[The matched repair study](../experiments/results/cnf-repair-history/README.md)
preserves 20 histories, 3,924 decisions and 60 archives. For size-16 SAT with
128 fresh positive units, decision history needs 129 bases, 12,020,154 logical
bytes and 2.61853 seconds. Repair keeps one base, 100,706 bytes and takes
0.07326 seconds. Separate tracing reports peak Python allocations of 77,265,863
versus 1,740,168 bytes; this excludes native SQLite and process RSS. All 379 prior
archives still check without changes. Python/SQL remain outside the Lean boundary.

Counterexamples remain: a parent clause (-x or 1) with a unit (1) makes flipping
x safe, but purity still rejects the addition (x); both modes fall back 32 times
on this stream and repair adds index overhead. Already-compatible additions need
no repair but raise peak traced memory from 108,869 to 249,217 bytes. Thirty-two
variables near 2^1024 retain 32,801 trie nodes and take 38.73 ms versus 33.18 ms
for fixed-model fallback. Repeated events still lose to canonical deduplication.

Next investigate affected-clause satisfaction counts to admit safe flips despite
opposite occurrences; compress unary trie paths for sparse names; and build the
repair index only when it is useful. These require precise source/branch binding
and invalidation. Arbitrary model repair, polynomial acquisition for all CNFs,
whole-archive compression and constant-cost cold replay remain unestablished.
