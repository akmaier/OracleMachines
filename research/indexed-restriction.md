# Reusing immutable source indexes for restriction

The preceding profile left source restriction as the largest named own-time
cost. A twelve-source diagnostic found that all observed restriction inputs were
tuples of tuples. Source 1194 performed 3,399 restrictions over 1,187,922 input
literal occurrences, although only 109,956 literals belonged to affected clauses.
There were 3,044 repeated source-object calls, 277 distinct source values and
355 distinct objects. The diagnostic retains objects and changes overhead, so
its timings and memory are not performance evidence.

## Recognition, reuse and invalidation

`IndexedRestrictionInventory` adds a private occurrence-index cache to the ordered
propagation inventory. Every new eligible source is validated as an exact tuple
of exact tuples of exact nonzero Python ints. Subclasses and bools are excluded
from the fast path. The caller's assignment must be an exact dict of positive
exact int keys and exact bool values. Other inputs retain the original scan
semantics through a fallback; they are not classified as invalid SAT instances
by this helper.

For an eligible source F, the index records every signed literal's clause IDs,
with multiplicity. A cache hit requires the same source object as the strongly
held validated source. The object ID is only a lookup aid; an `is` check and the
retained reference rule out recycling. Exact tuple/tuple/int validation makes
that object's contents immutable, so no new full-source comparison is needed
on a hit. There is no identity reuse for mutable inputs. Separately allocated
but equal CNFs prepare separately. A changed CNF likewise gets fresh preparation.
Eviction removes the source and its index; a later visit rebuilds them. Restart
starts empty. No assignment, restricted answer or proof-check verdict is cached.

Identity reuse here differs from trusting the identity of a mutable proof object.
Its safety depends on validating the full immutable representation once and
retaining it throughout the index's lifetime. Private posting tuples never escape
through returned residuals. The enclosing Python process and helper implementation
remain trusted; this is not protection against arbitrary internal memory mutation.

## Exact update and composition

For a Boolean assignment alpha, collect clause IDs containing a literal made
true by alpha, and IDs containing a literal made false. Drop the first set. For
clauses in the second set but not the first, remove all assigned literals while
preserving their order and multiplicity. Reassemble the result in original clause
order, sharing the original immutable tuple for each untouched clause. Empty
clauses remain unless a true literal satisfies their clause, which is impossible
for an originally empty clause. Tautologies and duplicate occurrences retain the
old restriction behavior; this step does not normalize or deduplicate them.

Correctness follows clause by clause. If a true occurrence exists, both the index
and scan remove the clause. Otherwise, any clause with an assigned occurrence
belongs to the false-occurrence set, and both retain exactly its unassigned
occurrences. A clause in neither set has no assigned variable and is unchanged.
The original-order assembly therefore returns exactly the scan's tuple of tuples.
The posting invariant is established during preparation and preserved by the
validated source's immutability. Eviction cannot change any returned immutable
residual. This gives exact restriction under arbitrary valid assignments on an
eligible source, not a new tractable SAT class.

The independent simplification checker is not optimized in this change: it still
reconstructs its input branch directly. However, constructing that branch from
the original source now uses this trusted indexed helper when enabled. That
boundary should not be concealed by saying that checking verifies the index
itself. Differential tests and the argument above support the helper; there is
no Lean refinement of the Python index or its identity/lifetime mechanism.

## Resource account

Let m and L be source clauses and literal occurrences, A the number of assignment
entries, P the number of retrieved posting entries, and R the total literal count
of the unsatisfied affected clauses that must be rebuilt. With constant-time map
and set operations and word arithmetic:

- A miss validates the source and builds its index in O(1+m+L), before query work.
  Validation and posting construction are counted separately.
- A hit validates A assignment entries and processes O(A+P+R+m) work. The m term
  is required to assemble the complete ordered output, even when very few clauses
  change. The result is still a materialized outer tuple, not a lazy view.
- Query scratch space is O(A+m+R) words in the worst case. Returned unchanged
  clauses share immutable tuples; changed clauses allocate fresh tuples.
- The cache charges 1+m+L units per source and retains at most B=32,768 units.
  Posting keys/entries, clause references and metadata occupy O(B) words under
  word-size assumptions. Integer bit lengths and Python object overhead prevent
  interpreting B as a byte or RSS cap. Existing graphs and archives are separate.
- One incoming index may be built before old entries are evicted, so transient
  preparation is additional to the retained cap. An oversized source is validated
  and scanned without admission. Cache maintenance is charged, and across the
  run each admission can be evicted at most once before re-admission.

Dictionary/set collisions and long integer labels add costs beyond that conditional
word account. No source hash, canonicalization or serialization is used to merge
distinct equal objects. That saves lookup work on warm identical sources but
leaves cross-object, append-prefix and cross-assumption output-result reuse open.
Dense assignments, one-time sources, equal reallocations and oversized fallbacks
can fail to repay preparation. Mutable sources retain scan cost. The matched
controls preserve these cases rather than assuming locality for every CNF.

## Evidence and next gap

The [diagnostic](../experiments/results/cnf-restriction-reuse-diagnostic/README.md)
precedes implementation. The [pilot](../experiments/results/cnf-indexed-restriction-pilot/README.md)
checks unchanged source identities, proof traces and cold archive bytes. The
[full comparison](../experiments/results/cnf-indexed-restriction/README.md) charges
preparation, checking, output assembly, persistence, warm reuse, cold replay and
memory. Saved source values, proofs, solver results and unsuccessful alternatives
are preserved. Structural coverage is unchanged; further discovery still needs
new certified relations or exact interaction decompositions.

The paired full comparison averages 8.36% less discovery time, 4.37% less total
time and 7.30% less cold replay, while six-case Python peak grows about 1.60 MB.
One full sample regresses total time; both are preserved. Equal-source reallocations,
novel appends and oversized fallbacks also regress in helper controls. The next
largest named own-time cost is independent simplification checking, with the same
51,574,914 full-workload reconstruction visits. Coverage remains unchanged.
