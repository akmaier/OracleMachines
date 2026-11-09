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

The second attempt reached acquisition but its cold-audit harness used competing
SQLite connections for source replay. A shared audit connection fixes the lock;
an explicit mixed-policy audit test covers it. The completed third acquisition
and both cold audits were saved before another tuple/list equality assertion in
finalization. `finish_cnf_retained_plans.py` independently checks all 1,497 answers
and canonical profiles, verifies both archive hashes, and finalizes those saved
measurements. The timed runner and failure log remain frozen. Only the separate
allocation diagnostic is repeated. The initial restore timer was not checkpointed
and is recorded as null; no acquisition or audit timing is estimated or rerun.

Python tests cover exact reuse, normalization, novel and edited sources, unclosed
old states, corrupted references/profiles/dependencies, byte-preserving restart,
exhaustive small models, and the actual lost variable-1 plan. This change adds no
new Lean theorem or Python refinement claim; its certificate rule reuses the old
checked graph with an exact identity binding.

## Full prepared-history result

The [full comparison](../experiments/results/cnf-retained-plans-full/) starts
both modes from the same **417,370,112-byte** old archive with empty verifier
caches. Its earlier acquisition cost remains part of lifetime work. Reacquisition
reproduces the preceding binary-path coverage; references recover source 1471.

| Measure | Reacquire binary-path graph | Reference prepared plans |
| --- | ---: | ---: |
| Non-tiny structural closure | 901/985 | 902/985 |
| Discovery, checking and persistence (s) | 98.33619 | 81.96656 |
| Complete measured query cost (s) | 190.63432 | 177.05292 |
| Ordinary solver portion (s) | 92.17514 | 94.97869 |
| Combined SQLite bytes | 755,658,752 | 629,276,672 |
| Added SQLite bytes above the seed | 338,288,640 | 211,906,560 |
| Added pattern nodes | 25,578 | 13,560 |
| Selected unresolved leaves / literals | 100 / 31,283 | 99 / 31,203 |
| Full cold replay (s) | 95.64397 | 82.52345 |
| Warm replay (s) | 0.27327 | 0.41059 |
| Six-case peak traced Python bytes | 20,124,942 | 24,084,738 |

Discovery improves **16.65%**, complete query cost **7.12%**, combined storage
**16.72%**, and added storage **37.36%**. There are no lost closures against either
the old prepared policy or the binary-path comparison. All ordinary answers agree.
The 902 closures equal the previously observed archive union, now obtained by an
integrated reference policy. This remains a prepared-history result, not a cheap
from-scratch portfolio or a universal class construction.

The reference pass accepts 2,127 old nodes and performs no old-policy insertions.
There are 1,410 query-level references; the remaining original inputs still
require acquisition. During the run, the old verifier checks 13,315 nodes, and the
new graph adds 13,560. Both private caches retain their checked nodes. This helps
explain why fewer new stored nodes do not imply lower resident memory: the small
allocation sample rises **19.68%**. Native SQLite, RSS and full-history peak are
excluded. Warm replay also regresses, and the policy stays optional.

Ordinary solver time includes a complete `count/sum(length(...))` census of
`cnf_residual_v1` after every query, even when the decision is already cached.
This is metadata work with history-size dependence. It must not be interpreted
as fresh SAT search; the separate profile measures it before proposing a change.


## Fresh inputs and next targets

The prepared-history fresh control uses the same 96 previously published control
inputs at depth two. Both close 88, with discovery 6.57530 -> 6.80303 seconds and
total 14.10084 -> 14.40169. Both add 1,988 nodes; combined SQLite grows from
450,355,200 to 450,826,240 bytes under references. The 20 internal references all
point to family nodes. No whole-query root is referenced. Exact recognition alone
therefore does not imply cheaper acquisition. These are not newly drawn holdouts.

The full reference population is broader: 385 family, 103 AND, 463 OR, 1,116 probe,
24 projection, 21 simplification, four subsumption and 11 polarity nodes. Wrappers
use 14,169,766 logical key-plus-payload bytes. The source-1441 cold diagnostic still
leads with reconstruction (1,718 calls, 0.28391 s own), normalization (843, 0.18890)
and propagation (1,608, 0.17473). Cumulative times overlap; this is one instrumented
query, not the complete history's cost profile.

The separate ordinary-solver census averages 0.0571391 seconds over 12 repeats
on 21,838 rows / 65,665,771 payload units. A 1,497-query extrapolation is about
85.54 seconds, not an exact subtraction from the measured solver total. Removing
that unconditional metadata scan is the clearest measured runtime target. A
source-bound checker for selected sound proof dependencies, with shared/bounded
cache state, is the next memory target. Trivial family references need an admission
comparison. General equivalent-core transport and later upgrades of cached misses
remain open. None of these follow-ups is implemented by this checkpoint.

All **469 Python tests** pass. The unchanged Lean build/axiom audit passes at
**4,148 declarations / 1,988 theorem declarations**. All **63** existing manuscript
proof blocks are unchanged. The current paper adds the exact-reference guarantee,
measured savings, regressions and the remaining preparation obligations.
