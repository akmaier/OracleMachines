# Reuse checked plans before acquiring another policy graph

9 November 2026. This experiment addresses the bounded-coverage regression in
[binary-path simplification](binary-paths.md): source 1471 had a successful plan,
but simplification changed the candidate list and lost its winning split.

## Exact reference rule

`RetainedPlanInventory` first looks for a closed `PolarityHornInventory` node with
the same normalized CNF, remaining depth and old policy configuration. The existing
SQLite primary key already supplies this lookup; no corpus scan, nearest-neighbor
index or new classification oracle is needed. A positive lookup is checked by the
original verifier, including all recorded alternatives and exact source bindings.
The new graph stores a `retained_plan` reference and its exact source/profile/summary,
instead of acquiring another descendant graph. Its closure survives a new
scheduler's different candidate choices because that scheduler is not invoked.

A row's unverified `closed` flag is only a lookup hint. A positive must survive
full independent verification. A missing or non-closed row permits ordinary
binary-path acquisition; it certifies no exclusion. Source, depth or policy
mismatches, corrupt references, invalid profiles and missing dependencies reject
reuse. Clause order and order-preserving variable renaming are handled by the
existing normalization and binding rules. A genuine clause edit requires a new
match or new acquisition. Arbitrary semantic equivalence is not recognized.

The prepared verifier has its own initially empty proof/index caches and shares
the archive connection. It only loads and checks old nodes during reuse. Neither
old nodes nor their failed alternatives are overwritten. Source/profile/key copies
remain in the small new wrapper; this is graph sharing, not a compact encoding
of all CNFs. A supplied model lifts by identity on the exact normalized source
and is checked again. Structural closure is not itself a SAT answer.

## Guarantee and scope

Suppose an old closed node exists before the new source is first acquired, with
exactly the required source, depth and fixed old configuration. If the dependency
graph passes the old checker, the new acquisition returns a closed reference.
The proof is direct: the original source-bound certificate is still the same
certificate; no new candidate-membership premise is needed. This recovers the
recorded variable-1 example without reacquiring its choice sequence.

This guarantee requires prepared evidence. It does not transport internal clause
IDs to a different reduced CNF, establish a compact description of every input,
or bound the preparation needed to obtain the old plan. Already-cached new-policy
misses are not upgraded automatically when old-policy evidence is added later.
The implemented experiment uses a fixed prepared prefix. Such later upgrades
need append-only versioning or a separately checked preferred-plan index.

## Resource account

For a query source of serialized length S and old policy description of length K,
constructing the lookup key and comparing bindings costs at least O(S+K) work.
Include SQLite lookup/I/O and the returned old node's serialized length. The first
positive reference may trigger checking its entire previously unseen dependency
graph, including failed alternatives. That cost is charged, not inferred to be
linear in the query alone. Later references can reuse the verifier's checked-node
cache; the current implementation still fetches and decodes its lookup hint.

The new wrapper retains the source/profile/reference but not copied descendants.
The original graph remains stored once. Both old and new verifier caches contribute
to resident memory. The historic acquisition cost and all seed bytes remain part
of lifetime cost; reusing a prepared archive does not make its construction free.

The no-history control retains 88/96 closures at depth two and gains nothing.
Discovery rises 6.36236 -> 6.66536 seconds, total 7.70944 -> 7.98044, and SQLite
33,030,144 -> 33,456,128 bytes. Both retain 1,988 nodes. This overhead is preserved
in [the empty-history evidence](../experiments/results/cnf-retained-plans-empty/).
These fresh cases differ in depth from the preceding binary-path experiment.

## Validation protocol

Both matched modes start from the same archive prefix with empty checker caches.
One reacquires the binary-path graph; the other first tries the retained reference.
Measured acquisition includes source preparation, lookup, full first-use checking,
serialization, persistence, ordinary solving and model checks. Initial seed restore,
database cloning, initialization, warm replay and full cold replay are separate.
Cold replay verifies both policies and all ordinary-solver certificates. Every
seed row is compared byte-for-byte after acquisition; old evidence is not removed.

The first full run stopped at a benchmark assertion comparing in-memory tuples
with JSON-loaded lists. Canonical JSON comparison repairs that assertion without
changing runtime or certificates. The original runner and failure log are retained
in `cnf-retained-plans-full-attempt-1`; no result from that attempt is used.

Python tests cover exact reuse, normalization, novel and edited sources, unclosed
old states, corrupted references/profiles/dependencies, byte-preserving restart,
exhaustive small models, and the actual lost variable-1 plan. This change adds no
new Lean theorem or Python refinement claim; its certificate rule reuses the old
checked graph with an exact identity binding.
