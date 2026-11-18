# Compile negative source-clause covers into native proofs

The optional cover policy follows [mixed completion](mixed-completion.md).
If a source clause C contains only literals with retained negative conditions,
then F is unsatisfiable: every model of F must satisfy a literal of C, whereas
each corresponding F-and-literal condition is refuted. A partial cover gives
no parent verdict. Positive model routes keep priority, and the existing mixed
probe pass runs unchanged before the additional cover scan.

## Reuse and certificate construction

Selection collects negative SCC outcomes and scans original source clauses for
the first complete cover. The proposal retains the source-clause index and
references to the relevant premise attempts. Publication checks the parent
binding, exact source clause, every premise binding, each saved unit reason and
both contradictory implication paths before constructing any native nodes.
Discovery diagnostics are therefore proposals, not trusted conclusions.

For ordered clause literals l_1,...,l_w, the compiler builds a binary split
spine. Branch i sets earlier literals false and l_i true. The last branch needs
no additional split because the residual source clause forces l_w. Each branch
transports the corresponding original conditioned certificate under the
stronger assignment. Canonical variable maps and clause indices are rebound;
unit reasons that became satisfied disappear, forced reasons are retained, and
an exposed conflict closes the branch. Contradictory implication paths are
translated into the surviving residual. If additional assignments fix a vertex
of the contradictory cycle, the compiler performs a charged unit-propagation
repair instead of rerunning SCC or invoking general search.

The outputs use only the existing native `split`, `units`, `implications` and
`empty` proof kinds. The unchanged native verifier checks every published node,
and the existing full cold replay validates the resulting parent. Publication
never calls the general search entry point or the SCC solver. Intermediate
native nodes are retained for possible future reuse; existing payloads are
read and preserved, and identical planned keys are shared.

Every conditional proof concerns the same parent F and its own assumption.
The split spine makes stronger branch conditions explicit and covers all
assignments consistent with the source clause. Restriction transport must
preserve the unit-reason and implication-clause bindings; it is not enough to
reuse an old proof merely because the residual sizes agree. Tests exercise
these bindings, additional assignments that turn cycles into unit conflicts,
corrupted evidence, signed variable names, forced prefixes, already stored
nodes and the unchanged cold verifier.

## Incremental bounds and limitations

Let k be the number of retained completion records and L the source literal
payload. Cover recognition uses O(k+L) expected dictionary/set operations plus
source-clause sorting. The current list-based opposite-sign check additionally
costs O(sum_c w_c^2) comparisons over visited clause widths w_c; it is not
linear for unbounded-width clauses. Recognition stops at the first cover. Original
source ordering determines that choice, not an optimized certificate cost.
A width-w cover produces at most 3w-1 planned native nodes: w-1 split nodes
and at most two proof nodes for each conditioned branch. Shared canonical keys
or known nodes can reduce the number of insertions. This bound concerns the
certificate structure, not discovery time or total archive size.

Publication separately charges w premise canonicalizations and full-key
bindings, unit-reason and implication-path checks, cofactor construction,
transport, normalization, native verification, serialization and storage.
With n variables and L literal occurrences, scan-based repair can cost O(nL)
per affected branch; it is not silently counted as constant-time reuse. The
planned cofactor keys and full CNF payloads can occupy O(wL) words for the
short BFS paths emitted by the existing SCC solver, in addition
to assignments and the existing discovery screens. An arbitrary supplied path
may be longer; its actual certificate length is an additional charge. Integer widths and sorting
costs remain separate. No uniform bound on the unresolved SAT fallback follows
from the bounded compiler.

The current recognizer requires every literal of an original source clause to
have a retained negative SCC condition. It misses a clause that becomes fully
covered only after removing literals already falsified by baseline propagation.
An initial test expectation exposed this gap; the failed expectation is saved
and an explicit regression test now retains the miss. For example, gating the
K4 colouring clauses with an independently forced literal preserves UNSAT but
hides the original cover. Supporting propagated clauses requires a checked
baseline-prefix wrapper or a unified interface for unit-conflict conditions;
it is not enabled here. Incomplete covers and opportunities outside the probe
budget also remain open.

## Validation design

The previous 25 exact-prefix contexts are retained, and the previous fresh
negative case 59 adds one context. It repeats in reverse order (54 arms total).
The three motivating parents previously acquired 36 nodes / 50,554 native
bytes. Eight new tests include all 64 four-vertex graphs in two coordinate
systems (128 comparisons), checked against exhaustive three-colour assignments.
A separate synthetic case requires unit repair after restricting a retained
implication cycle. Corrupt or incomplete proposals are rejected before any
publication.

Preflight checks all 52 first-order control arms, 60 fresh selections and an
eight-query worker with warm and full inherited cold replay. Production then
compares native baseline, mixed completion and cover compilation on sixty new
excluded queries in two opposite serial orders. No tests, builds or profiles
run concurrently with timed workers. Labels are not inputs to selection.

## Measured outcomes

The three motivating controls shrink **36 -> 24 native nodes** and
**50,554 -> 33,240 native bytes**. Each compiled cover plans eight nodes. The
other 23 saved contexts retain their native certificates. The new saved target
repeats the saving in reverse policy order.

A fresh sixty-query stream returns 42 SAT / 18 UNSAT in every mode. All 48
family targets remain unfamiliar after shared preparation; twelve neighbours
become known. Fresh case 43, with source clause [-28, 85, 87], accepts a cover.
Its fourteen fallback expansions are replaced by eight compiled nodes. All
fourteen positive model publications are preserved, and all 95 premise probes
remain unchanged.

| Cost across sixty queries | Native baseline | Mixed completion | Cover compilation |
| --- | ---: | ---: | ---: |
| New native nodes | 400 | 370 | 364 |
| New native payload bytes | 485,485 | 464,868 | 457,715 |
| Expanded nodes | 388 | 344 | 330 |
| Discovery/acquisition propagation visits | 66,499 | 99,709 | 97,967 |
| Mean query seconds | 0.35788 | 0.35789 | 0.36050 |
| Mean complete worker seconds | 24.74371 | 24.62332 | 24.53426 |
| Mean full cold replay seconds | 12.10087 | 11.99807 | 11.93723 |

Additional recognition reads eighty completion records and scans 196 source
clauses / 410 literals. The accepted cover checks 417 premise literals,
45 unit-reason literals and 36 implication edges. Transport accounts for
45 reason literals and 72 path literals. No unit repair is needed on the
measured covers, although the synthetic test verifies that branch. Native
canonicalization, checking, serialization and archive census remain charged.
Graph acquisition propagation falls 11,827 -> 10,085 visits; discovery stays
24,650. Random three-CNF and coupled parity remain at **253 acquisition nodes /
47,204 propagation visits**, with no new probe access.

Paired query differences are -0.00440/+0.00963 seconds; the mean increases
slightly. Complete-worker differences are -0.15233/-0.02578 seconds. Cold replay
accounts for about 0.061 seconds of the mean 0.089-second complete-worker drop.
Two runs do not isolate this variation as a compiler benefit or establish a
scaling improvement. Native proof savings are the robust result on these cases.

Diagnostic query/warm sidecars grow about 0.05%, from 1,781,114/1,781,087 to
1,781,952/1,781,938 bytes. Trial SQLite size falls 80,228,352 -> 80,216,064 bytes
and compressed size 5,981,580 -> 5,980,950 bytes. Mean process RSS increases
about 1.57 MB (770.671 -> 772.243 MB). The preservation union also retains
comparator proofs and earlier payloads; its cumulative size is distinct from
the individual policy's trial archive.

## Remaining gaps

The next concrete discovery target is **cover-directed candidate admission**.
Fresh cases 51, 55 and 59 each have a source clause missing just one refuted
literal, and that literal lies outside the current candidate set. Case 51
needs -158 for [-158, -54, 16]; case 55 needs -156 for [-156, -113, -12]
(or 191 for [-151, -56, 191]); case 59 needs -320 for [-320, -71, 52].
These are candidates for measurement, not already checked extra conditions.
Charge the added probes and retain failures; the missing condition need not
have a binary residual or a cheap proof. Earlier stopping at a completed cover
and covers exposed by baseline propagation are separate opportunities. A gated
K4 regression preserves the latter recognition miss.

Cover discovery currently runs after the entire previous probe pass. Earlier
completion of a cover, candidates chosen to finish a nearly covered clause,
and integration of unit-conflict conditions could expose additional exact
compositions. A clause shortened by checked baseline propagation is a concrete
preserved miss. Any extension must account for additional discovery, source
bindings and certificate construction, rather than assuming missing conditions
will be cheap or unsatisfiable. Random three-CNF, coupled parity, broader
structural discovery and arbitrary-CNF bounds remain unresolved.

Evidence and reproduction:
[`experiments/results/cnf-negative-cover/`](../experiments/results/cnf-negative-cover/).

## Verified checkpoint

All **1,153 tests**, 24 focused tests, 294 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-negative-cover/checkpoint.json`:
**25,757 native keys**, preserving all 25,334 earlier payloads, with 234 new
composed records alongside 4,245 inherited records, 2,957 ordinary decisions
and six projections. The preservation union uses 80,306,176 database bytes /
5,993,018 compressed bytes. Eight roots have alternate certificates in sixteen
retained evidence occurrences. Ready/pending banks remain 132/38, 141/66,
87/89 and 87/116; there are no new support activations. Original structural
coverage remains 17/24 and supplemental positive coverage 24/24. All 529 prior
sources, 6,431 artifacts and 99 manifests remain unchanged. The 215-page
manuscript builds with all 64 existing proof blocks unchanged. No new Lean
theorem or unrestricted-SAT resource guarantee is claimed.

New manifest: **210 artifacts**. Next preservation audit: **6,641 artifacts / 100 manifests**. Final source ledger: **534**.
