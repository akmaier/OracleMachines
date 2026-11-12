# Bounded pivot deviations over retained plans

The earlier additive-growth study admitted 2,530 additional exact elimination
edges but gained no original-source closures. The next question is whether a
different admissible pivot, before the selected chain stalls, exposes useful
structure. This experiment keeps the same two-clause growth and 64-pair limits.
It spends a separate, explicit budget on alternative targets and preserves the
previous proof graph.

## What is searched and checked

For each still-open original, the search visits its selected plan breadth-first
and takes at most four open elimination nodes. At each, it examines at most 64
variables ordered by opposing-pair count and identifier, excluding the already
selected pivot. It constructs all resolvents for pair-admissible candidates and
rejects targets exceeding the existing two-clause allowance. This enumeration
and every rejected candidate are charged even though no full target recognition
is acquired for them.

Admissible candidates are ranked by a cheap syntactic signal: minimum number of
clauses violating Horn, dual-Horn, binary, zero-valid or one-valid syntax; then
binary-width excess, literal count, opposing pairs and identifier. This is not
distance to a semantic SAT class and supplies no success guarantee. A round-robin
schedule over the four ancestors fully recognizes at most eight targets per
open original. Each target then uses the existing anchored subset/additive
recognizer at the source node's remaining conditioning depth. The search stops
when the whole original can be covered, or the attempt budget is exhausted.

Every proposed target is independently reconstructed by the existing complete
opposing-pair checker before recognition. A persisted trial binds its exact old
source key, pivot, canonical target key/name map and checked target summary.
Cold replay reconstructs the projection and checks that binding again, without
candidate rediscovery. The previous Lean existential-projection theorem supplies
the semantic identity; this experiment adds no Python refinement or efficient
order-search theorem. All failed recognized targets persist as ordinary proof
nodes, and null/failed structural coverage does not mean UNSAT.

## Exact reuse and whole-source composition

The previous acquisition archive is paid input. Target lookup reuses existing
canonical source/configuration/depth proofs, including open plans. New targets
acquire their full checked recognition histories. Old source nodes and selected
plans remain immutable. A successful alternative supplies another exact route
for its source; it does not overwrite a prior choice.

Final recomposition retains every previously closed node. An AND component node
needs all children covered. A conditioning alternative needs both restrictions,
and any complete previously checked alternative can cover its parent. An exact
unary reduction needs its child covered. Thus a successful local replacement is
checked through the old graph before it counts as an original-source gain.
Coverage still means a decomposition into recognized families, not a SAT verdict.
The unchanged ordinary solver is not being benchmarked as a faster decision path.

Trials and acquired nodes are saved as a delta bound to the exact old archive
hash. Restoring that base and applying the delta reconstructs identical logical
rows, which undergo complete cold checking. Physical SQLite page layout need not
match a differently ordered reconstruction. The full temporary working database
remains until reconstruction and verification finish; it is removed only after
the compressed delta and report are durable. This avoids exporting another full
copy of the paid base, without treating that base as free storage. Successful
replacement edges additionally retain independent endpoint SAT results and
checked model lifts in a separate reference archive.

## Resource account and restrictions

Let A be the ancestor cap, K the candidate cap, B the opposing-pair cap, L source
literal size and w maximum clause width. At each ancestor, preparation and ranking
can cost O(L+n log n+K(L+B*w)) expected container work, with target ordering and
integer encoding costs additional. Up to A*K complete candidate targets coexist
in the proposal lists; this scratch space can be O(A*K*L') for target size L'.
The implementation does not claim to stream this candidate storage.

At most T=8 targets receive full inherited recognition per open original. Their
recognition costs R_i and newly stored proof graphs remain separate, so the
budget does not bound total work by eight elementary operations. Each attempted
edge is checked twice during acquisition, with a further check when persisted
results are admitted to the success set. Recomposing closure can revisit the
old unresolved graph, adding up to O(T*(V+E)) traversal work with a fresh local
memo per call. All source loading, validation, key construction, checking and
persistence are measured. These container-level accounts exclude identifier bit
lengths and do not bound full-process peak memory or unrestricted SAT.

The fixed policy is frozen before comparing the selected original failures and
reused controls. The experiment tests one deviation at a bounded set of old
ancestors, followed by the old recognizer. It does not exhaust all pivot orders,
compose arbitrary successive deviations on newly acquired ancestors, or prove
that an unresolved source lacks an efficient decomposition. The full earlier
prepared result remains 902/985 unless a new whole-corpus run is performed.

## First frozen policy: no new closures, mostly reconvergence

On the 83 selected original prior misses, **316 trials** add **602 recognition
nodes** but no closed alternative and no original gain: coverage remains
**31/83**. Incremental expansion takes **6.45902 seconds**, after **63.19332
seconds** of base-source verification. The working database grows from
734,814,208 to **750,022,656 bytes**. Its delta contains 602 pattern rows and
316 trial rows, occupying **15,208,448 SQLite bytes / 857,460 compressed bytes**.
The original 40,292 pattern rows, 1,548 source bindings and 21,838 solver proof
rows remain intact. Full cold audit takes **115.84382 seconds**; a separate
trial/recomposition audit takes **75.59982 seconds**, including repeated checking
of old dependencies. These two verification passes are additional cost, not
part of the 6.45902-second expansion measurement. Warm recomposition in the
already verified process takes **0.01893 seconds**.

The 96-input repeated control makes **56 attempts / 40 unique trials**, adds
**105 pattern nodes**, and retains exactly **88/96 closures**. Expansion costs
**0.80309 seconds**, after **5.36455 seconds** of base verification. Its database
grows from 465,776,640 to **467,992,576 bytes**; the delta is **2,244,608 bytes**
before compression and **103,855 bytes** after. All proof and trial records cold
replay unchanged. No successful replacement exists in either suite, so the
reference endpoint archives are empty initialized stores, not new solved evidence.
These are incremental costs from paid histories, not speedups over fresh solving.

A read-only analysis explains the narrow search's failure. Among the 316 unique
original trials, **295 (93.35%)** have exactly the same multiset of selected
unresolved canonical leaf keys as their source plan. Their immediate target roots
are all new, so reuse happens farther down the recognition graph. Only 21 trials
expose a novel selected leaf; they yield 13 distinct new leaves. Four trials
reduce selected open literal count and seventeen increase it, with none closing.
The 57 old selected leaves remain the reference. Exact canonical equality retains
variable maps along each path; it is not a claim that all orders have the same
representation or cost.

Of these 316 choices, **271** alternate pivots share no source clause with the
selected pivot; **260** of those reconverge exactly. In the repeated control,
32/40 unique trials have the same selected frontier, and 23/27 noninteracting
choices reconverge. This does not justify deleting every independent candidate:
intermediate recognition and later choices can differ, and eleven noninteracting
original trials already have different selected frontiers.

## Follow-up hypothesis: prioritize interacting pivots

A second scheduler uses the same ancestors, pair/growth restrictions, eight-trial
cap and complete checker. It first ranks admissible pivots that share a source
clause with the selected pivot, keeping the earlier score within each group.
Independent candidates remain afterward; no semantic exclusion or pruning theorem
is asserted. One additional source scan builds the co-occurrence set and is
charged. This policy is motivated by the observed first-run data, so these same
sources are development inputs. It is evaluated from the same paid base archive,
not from the first policy's expanded state. Unchanged target/configuration keys
allow the two sets of acquired proofs to be combined later without overwriting
conflicting values.
