# Preconditions for uniformly cheap expansion

8 November 2026. The target is a worst-case guarantee for every admitted update,
including its first occurrence. A cache-hit rate cannot supply that guarantee.
The key question is whether the state/update family is closed under an efficient
constructor. "Minimal" also needs a cost model and a lower bound; we have neither
a theorem of global algorithmic optimality nor a result for unrestricted SAT.

## Requirements before expansion

1. **A sufficient boundary.** The retained state must determine every query
   permitted after every allowed continuation. Future updates cannot refer to
   forgotten variables except through the boundary. Histories assigned the same
   summary must be indistinguishable by those continuations. Otherwise compression
   discards information needed for exact reuse. For affine histories this is the
   exact set of possible current boundary assignments.
2. **A closed state/update family.** Every admitted update must produce another
   state in the inexpensive representation. An occasional cheap case is
   insufficient: a later update may destroy the invariant. Restrictions can be
   enforced by the problem generator or verified at admission. Unsupported
   updates require an explicit richer path; they are not silently covered by the
   restricted bound.
3. **Cheap recognition and initialized auxiliary state.** Prove or check the
   boundary shape, update type and compatible interface before dispatch. Searching
   for a small decomposition, canonicalizing a row space, or calculating rank can
   be as costly as the work being avoided. Retain facts established at creation
   instead of reconstructing them, with precise invalidation and residency rules.
4. **A bounded affected region.** Express updates as changes to that interface,
   factor, separator or transformation. Reuse unchanged state by reference. Bound
   the number of affected dependents and their composition costs. If width, rank
   of the change or affected paths can grow arbitrarily, show that dependence in
   the bound rather than describing all updates as cheap.
5. **Direct checked construction.** Produce the exact new representation from the
   old one and the update, with a certificate/proof tied to the original source.
   Similarity and learned confidence only select candidates. A semantic theorem
   about an assumed function is not a theorem that decoded rows implement it.
6. **Full accounting and maintained availability.** Charge initialization,
   recognition, allocation, materialization, transport, validation, index updates
   and durable writes. State which objects must be resident and how cold recovery
   works. Eviction must not invalidate a promised warm bound without being charged.
   Bound metadata/index and retained-source growth separately from summaries.

If these hold with invariant I and parameters p, the useful statement is:

    I(s) and admitted(u) imply I(update(s,u)), exactness,
    and total_step_cost <= recognize(p,u) + construct(p,u)
                         + verify(p,u) + deliver(p,u) + persist(p,u).

Initialization is paid before the first step; cold recovery is additional when
the required resident state is unavailable. An induction then gives the sum of
these bounds for every allowed sequence. It does not establish the premises.
Nor does a restriction on history appends imply coverage of all SAT inputs up to
an expanding length. Precomputing every exceptional case moves its cost to
initialization and storage.

## Concrete affine structure

Write the predecessor boundary as S and the batch relation as R(u,v). Expansion
is the relational image R[S] = {v : exists u in S, R(u,v)}.

- If R is total, nonemptiness is preserved. This suffices to preserve the SAT
  answer for that step; it does not give the boundary needed by arbitrary later
  constraints. Uniformly total future updates would be a further restriction.
- If S={a} and R is v=f(u), then R[S]={f(a)}. This singleton invariant survives
  every total functional update, even a noninjective one. For v=A*u+t over GF(2),
  evaluate A*a+t; no elimination or search over old assignments is required.
- If f is bijective, the exact successor predicate is S(f^{-1}(v)). For a signed
  permutation v=P*u+t and arbitrary affine boundary C*u=d, this is
  C*P^{-1}*v = d + C*P^{-1}*t. It costs O(r*b) to permute and shift r summary rows
  after recognizing the batch. It remains within the same affine representation.
  Dense general inverses do not inherit this cost.

[StructuralExpansion.lean](../formal/OracleMachines/StructuralExpansion.lean)
checks these semantic facts and ties the singleton specialization to an exact
old affine history and an exact batch-function premise. It adds five theorem
declarations. It does **not** yet prove the executable recognizer, source decoding
of a specialized constructor, a cost ledger, or native dispatch. The audited
native solver still uses generic elimination on misses.

For a certified point boundary and a checked dense functional batch of c rows,
recognition/substitution is O(b*c); a point vector is O(b) logical state and
writing its b unit equations is O(b^2). A direct constructor therefore has the
derived target **O(b*c+b^2)**, versus the current general miss bound
**O(b^3+b^2*c')**. For c proportional to b, this targets quadratic rather than
cubic coefficient work even on unseen batches. Reading arbitrary dense source
coefficients and materializing a dense summary already costs their lengths in
this model. That supports input/output-scale work, not an unconditional global
minimum: sparse encodings, checked handles or deferred outputs change the bound.
The point vector alone is not the total retained memory; original batches,
request bodies, indexes, proof/result records and archive history remain.

## What the preserved inputs reveal

[The diagnostic](../experiments/results/affine-resident-metadata/structural-closure.json)
inspects the exact six repeated/novel streams at widths 16/32/64. Each has 32
regular updates, a contradictory branch and an unconstrained branch. **All 204
updates** admit a simple cube-substitution prototype. All 192 regular successor
boundaries are singleton assignments. Thus even the novel-batch evaluation has
an inexpensive shape invariant that our native dispatcher is not exploiting.
No claim of broad affine difficulty should be based on these streams.

The [prototype](../experiments/analyze_affine_closure.py) represents fixed/free
coordinates, substitutes only known old values, and accepts residual rows with
at most one new variable. It preserves duplicate constraints, detects conflicts,
and returns free coordinates when unconstrained. A row that still involves a
free old coordinate or couples new coordinates is declined for general solving.
A proved-empty predecessor or a detected contradiction can yield empty output
even when a richer row is otherwise present. All input rows undergo validation.

Across **11,862** small cases, **5,010 accepted** outputs equal the complete
existentially projected frontier; **6,852** are declined. Widths 1/2 enumerate
every cube (including empty) and all batches of at most two rows; width 3 adds
1,000 seeded cases. Wider benchmark decisions match independent elimination of
the full original history. This is experimental validation, not a formal proof
of the prototype or a native speed measurement. The coefficient-input payload
reported next to the existing elimination ledger is not a complete work ledger;
their ratio must not be described as a speedup.

## Next implementation and evaluation order

1. Maintain a source-linked empty/point/cube/general capability on native states.
   Establish it when constructing a summary; invalidate it with that state.
   Start with a point proof and checked functional-row recognizer. Guard failure
   must leave the generic constructor available, with guard work charged.
2. Construct point/cube successors directly and prove exactness, compactness and
   executed-work bounds. Integrate with the original chronological-history
   theorem and both positive and negative decisions. Ensure typed proofs erase
   without retaining full ancestors or recomputing elimination for certification.
3. Add signed-permutation transport for arbitrary correlated boundaries; this
   covers a different closed family. Measure whether noncanonical resulting
   bases reduce later cache hits, and charge any optional canonicalization.
4. Benchmark with partial and correlated frontiers of varying dimension, novel
   functional and nonfunctional updates, guards that fail late, growing width,
   repeated structure, eviction, and cold recovery. Compare against the same
   current generic solver with normalization and transition reuse enabled.
5. Reduce transport/decoding with checked batch handles and compact responses.
   Once a checked repair path exists, compare KD-tree proposals with hashes,
   buckets and support indexes. Indexing should serve a proven cheap operation.

This priority targets the measured dominant novel-stream elimination cost first.
It complements the completed parent-metadata optimization, which reduced source
reads without altering the mathematical calculation. A general representation
closed under arbitrary SAT updates with uniformly cheap construction remains
unestablished. Affine tractability and these narrower invariants do not supply it.
