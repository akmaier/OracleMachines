# One-way binary forcing before conditioned buckets

Date: 27 November 2026. Parent: `23f11990`.
Evidence: `experiments/results/cnf-forcing-buckets/`.

## Result and decision

Checked paths from a literal to its negation certify **7/27** exposed acquisition
misses (five SAT, two UNSAT), and increase frozen unique-panel coverage **17/24 to
20/24**. All four exact repeats remain covered; no coverage losses occur on this
panel. The unchanged fallback already supplies all 55 answers. This expands the
restricted acquisition family, not the underlying solver's answer coverage.

Separate path evidence reduces complete cost **12.41%** versus the preceding
relation policy in the same wrapper. Interning repeated implication edges gives
12.50% versus that baseline, but only **0.11%** versus separate paths, with two
paired wins and two regressions. It does not establish a reliable runtime gain.
Shared evidence reduces source-support checks **38%**, yet increases compact
forcing payload **13.18%**. Retain that negative compression result. The pipeline
still costs **2.88 times fresh solving**; production defaults remain unchanged.

## Exact rule and recognition

For a binary clause `(a or b)`, the implications `not a -> b` and `not b -> a`
are valid in every model of the complete cofactor, including its wide clauses.
A supported path `x -> not x` therefore entails `not x`; a return path is not
needed. This differs from equivalence substitution, which requires both directions
between a representative and its signed members. The prior conflict/equivalence
stage remains intact; forcing runs once on its normalized residual.

Discovery builds the binary implication graph and searches from every signed
variable for its negation. Each completed path records the forced literal and
clause-supported steps. Traversal stops after at most `work_limit` edge visits
per incoming cofactor. Already completed proofs remain valid when the cap is
reached; a failed or interrupted search supplies no negative SAT conclusion.
The same numeric policy separately caps bucket probes: these are independent
allowances, not one global budget. Graph setup, start enumeration, queue work,
path assembly, normalization, checking, persistence, time and RAM are additional.
None of the measured forcing calls exhausts the traversal allowance.

Verified forced units are conjoined to the current CNF. Because each is already
entailed, this preserves the entire model set. Indexed unit propagation then
restricts the augmented CNF. Replay verifies paths against the exact binary-clause
subsequence, recomputes the unit restrictions and inverse normalization, and
lifts the resulting assignment through the preceding signed relation/unit
transport. Every incoming edge keeps its own evidence. Every SAT edge lift is
checked, including branches not chosen for the final witness. UNSAT still requires
checked terminal evidence and both exact branches at a split; unknown stays unknown.

The new `cnf-forcing-buckets-v1` JSON authority has three structural modes:
`relations` wraps the preceding policy without forcing; `paths` stores each
forcing path separately; `shared` uses exactly the same discovered paths and
unit consequences but interns directed support edges. The audit expands every
shared proof back into its path representation and checks exact equality with
the matched path program, including all bucket nodes and branch decisions.
Native, equivalence, affine and Lean authorities are unchanged.

## Sharing conditions and limitations

In a separate path, the current literal is implicit; each step stores only its
next literal and binary-clause index. The shared format stores unique triples
`(start, end, clause index)` plus edge references in each path. Each pooled edge
must be supported by the same incoming CNF, unique, and used. Every path still
checks its start, consecutive endpoints and final forced literal. If there are
`P` path-step occurrences and `U` distinct edges, support checks fall from `P`
to `U`, but all `P` path steps still require traversal. The edge pool is not
assumed acyclic. Fewer support checks do not imply smaller serialized evidence:
the shared format adds start literals and references that the path format omits.

Pooling is scoped to one incoming forcing certificate. Edits or different clause
indices invalidate its source binding; an implication alone cannot authorize
reuse against a different cofactor. Complete root programs share within a stream,
and final residual/depth nodes share under one fixed policy. Each hit still pays
incoming recognition, lookup and transport checks. Every warm/cold program is
fully verified. Policy/depth changes invalidate a reuse key.

All structural arms retain root folding, initial units, binary conflict checking,
one signed SCC block per incoming edge, depth two, width eight and 262,144 reserved
bucket probes per node. Forcing has its own 262,144-visit allowance per incoming
edge; every unit invocation allows 512 steps and 262,144 reserved index-work units.
At depth `d`, the binary expansion still permits `2^(d+1)-1` incoming requests.
A single forcing pass is not closure to a fixed point: its later units can create
new binary clauses and new forcing paths. No small residual or efficient
unrestricted-SAT partition follows from these restricted transformations.

## Frozen comparison and costs

The panel contains 27 exposed sources (18 SAT, nine UNSAT), 24 frozen unique
constructions (twelve SAT, twelve UNSAT) and four repeats (one SAT, three UNSAT).
New controls include random three-CNFs on 14/18/22 variables; forcing funnels
with a shared middle chain attached to 10/14/18-variable cores; deleted chain
edges; parity prisms at sizes 7/9/11; and planted 11/15/19-variable funnels with
consistent or opposing wide clauses. Names, signs and input order are scrambled.
No new normalized source duplicates the preceding panel. Labels and descriptions
never guide acquisition. These are synthetic controls, not representative external
SAT evidence or a general coverage rate.

Four cyclic process orders start empty with one common fallback. Complete time
charges preparation, recognition, checking, JSON/SQLite persistence, warm reuse,
cold reconstruction and compression. Interpreter startup, report metadata,
generation, post-hoc profiling and preservation audit are additional. Both native
cold readers audit fallback records. Two additional JSON passes use the same
checker, not independent implementations. The baseline wraps the preceding
policy; it is not a timing rerun of a historical artifact.

| Workflow | Discovery (s) | Solve/check (s) | Warm (s) | Cold (s) | Complete (s) | Certificate bytes | Native-record bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0 | 0.35496 | 0.03018 | 0.25715 | 0.82811 | 0 | 1,095,175 | 76,333,056 |
| relations | 0.60956 | 0.60614 | 0.34658 | 0.88437 | 2.72120 | 4,481,627 | 955,621 | 78,692,352 |
| paths | 0.55955 | 0.49644 | 0.31348 | 0.78695 | 2.38363 | 3,969,462 | 751,391 | 74,727,424 |
| shared | 0.56275 | 0.49865 | 0.30975 | 0.77961 | 2.38109 | 3,963,403 | 751,391 | 74,760,192 |

Paths improve 11.64–13.83% over relations in every paired order. Shared improves
10.97–13.81% over relations. Shared-versus-paths ranges from **2.45% faster to
1.52% slower**. Its tiny mean difference is not evidence of dependable speedup.
Cold verification remains the largest phase. Evidence writes cost
0.03067 / 0.02451 / 0.02514 seconds for the structural arms; archive persistence
costs 0.17738 / 0.23495 / 0.19497 / 0.19663 seconds in table order. These are local
measurements, not asymptotic or cross-workload bounds.

Both forcing modes reduce bucket calls **232 to 204**, split nodes **109 to 94**,
and elimination steps **424 to 387**. They record 199 forced-literal occurrences
in 62 incoming certificates, using 794 path steps; the shared pools contain
492 distinct support entries. Subsequent unit traces have 241 steps. Root folding
performs 502 steps in all structural arms. Discovery makes 3,510 reachability
searches and traverses 9,705 implication edges, in addition to graph setup.

Across acquisition and its checks, shared support checks fall **2,400 to 1,488**;
path walks remain 2,400. Thirty queries reuse some support edges, including one
whole-program repeat. Their discovery is 1.06% and solve/check 1.30% slower than
paths; the other 25 queries have near-zero differences. Interning, set checks and
reference traversal can outweigh saved source checks. The count reduction is
real, but this implementation has no convincing total-cost advantage over paths.
Both forcing modes join fifteen distinct raw contexts only at constant residuals;
no new nonconstant residual-sharing gain is established.

Shared pretty-printed certificate files are 6,059 bytes smaller than paths
(0.15%). However, compact forcing records grow **12,185 to 13,791 bytes** (13.18%).
Combined compressed SQLite/JSON packages occupy
**212,745 / 263,143 / 221,537 / 222,534 bytes** in table order: shared costs 997
more compressed bytes than paths. Diagnostics add 0 / 138,655 / 125,500 / 125,500
bytes. Historical archives, repeated reports and container overhead are extra.
Peak RSS is modestly lower for forcing than fresh in these runs, but this
process-level observation is not a general peak-memory bound.

## Remaining gaps and next target

Twenty-four unique roots remain outside the acquisition family: twenty exposed
and four new; all repeats are covered. Their 43 unknown depth-zero nodes exceed
width eight: 32 have width nine, six width ten, and five width eleven. Six stop
before elimination; 37 retain partial bucket work before the cap.

A separately checked, source-bound profile finds no active units, unit conflicts,
disconnected components, Horn/dual-Horn form or contradictory binary subsets.
Four SCC blocks remain, merging eleven variable occurrences. More directly,
**13/43** nodes have new one-way forcing paths after the measured pass's unit
consequences. These paths give 58 forced-literal occurrences; subsequent units
assign 91 variable occurrences and expose six leaf conflicts. The measured
forcing searches were not capped, so this identifies omitted iteration rather
than an exhausted search budget. Leaf diagnostics are not additional root verdicts.

The full unit/component/SCC/forcing profile costs **0.02548 seconds**, including
1,192 forcing searches, 4,034 traversed implication edges and 250 checked path
edges. Full counters, paths, source bindings and follow-up unit traces are retained
in `remaining-structure-profile.json`; acquisition never reads this file.

**Next:** test bounded repeated unit/binary forcing until no new consequences
appear, with explicit progress, exact transport for every round and reuse of
unaffected structure where justified. Compare against the separate-path baseline;
further edge pooling has weak evidence here. Test whether iteration actually
certifies roots and whether full graph rebuilding/checking becomes the dominant
cost. Keep SCC interactions, wide random cores and deleted-edge failures visible.
Cold verification remains the largest measured cost. No compact arbitrary-SAT
closure or polynomial unrestricted solving guarantee is claimed.

## Validation and preservation

All **2,288 full and 30 focused tests pass**. Twelve new tests include all 512
two-variable clause sets, seeded mixtures, one-way forcing without a converse,
shared-edge counts, deleted-edge invalidation, forged references/endpoints,
partial traversal caps, conflicts with wide clauses, sparse signed witness
transport and cold replay with discovery disabled. All sixteen measured streams
reconstruct exactly. Three distinct native archives pass both cold readers;
paths and shared produce identical fallback archives. Existing SQLite
ResourceWarnings are preserved.

All **229 earlier manifests, 41,034 artifact entries, 1,258 scientific sources
and 71 proof blocks** are unchanged. Five source/test files raise the ledger to
1,263; one restricted proof is added. Resume
`experiments/results/cnf-forcing-buckets/checkpoint.json`, key
`forcing_buckets.remaining`, with its bound remaining-interaction profile.
