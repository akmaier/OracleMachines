# Checked binary relations before conditioned buckets

Date: 27 November 2026. Parent: `9f00cf03`.
Evidence: `experiments/results/cnf-relation-buckets/`.

## Result and decision

Binary-subset contradiction checking and signed equivalence substitution certify
**2/21** exposed acquisition misses: one UNSAT case through binary implications
and one SAT case after quotienting equivalent variables. On a new frozen panel,
all structural arms certify **16/24** unique inputs and **4/4** separate repeats.
There are no coverage losses on these cases. The fallback already supplies all
49 answers. This expands a restricted acquisition family; it does not increase
the underlying solver's answer coverage.

Relative to the preceding shared unit policy in the same wrapper, binary conflict
checking reduces complete cost **5.34%**. Adding equivalence substitution saves
another **5.53%**, for **10.57%** overall. Every paired order improves. The full
relation pipeline still costs **3.09 times fresh solving** and remains optional.
Cold checking is the largest measured phase; defaults are unchanged.

## Rule, recognition and exact transport

After initial unit propagation, form the binary-clause subset of the current
cofactor. A binary clause `(a or b)` supports implications `not a -> b` and
`not b -> a`. Paths `x -> not x` and `not x -> x` refute this subset and therefore
the full cofactor. The certificate records both paths, with clause indices in
the exact binary subsequence. Replay checks each supporting clause, the starting
literal and both endpoints. It does not trust a discovery SCC label.

If the subset is consistent, the relation arm proposes **one largest signed SCC
block** using the existing recognizer. It proposes blocks only for mixed binary/wide
CNFs with no active unit or empty clause; budget-limited unit processing can
therefore leave a recognition miss. A positive representative has a directed
tree reaching every signed member and a reverse tree returning from each member.
The existing independent substitution checker validates both trees against
active binary clauses. It rejects one-way implication as equivalence, mixed
supports, cycles/disconnected trees and non-progressing substitutions. Variables
outside the block remain unchanged. The entire cofactor, including its wide
clauses, is then rewritten by the checked signed mapping.

The binary clauses imply all block equalities. Under these equalities, replacing
each member by its signed representative preserves every original clause.
Conversely, any quotient model extends by assigning each member its required
representative value. A representative that disappears from the quotient is free
and can default to false. Cleanup removes duplicate literals, tautologies and
duplicate clauses without changing variable IDs; unit propagation follows.
Replay reconstructs the resulting inverse normalization, signed substitution,
and initial-unit transport in reverse order, then checks the incoming witness.
Each edge keeps its own transformation evidence; quotient models do not carry
other edges' assignments.

This order matters. The first draft passed a substituted clause `[1,1,1]` directly
to the unit index and missed its unit consequence. Later normalization/bucket
checking remained sound, but the intended post-substitution propagation was
incomplete. The signed three-variable counterexample, failing tests, draft code
and pilot are preserved. Cleanup was fixed before the matched protocol was
frozen. The corrected test requires the unique assignment `1=true, 2=true,
3=false` and rejects changed transport. This failed experiment must not be counted
as the final measured implementation.

The three structural arms all retain root folding, per-cofactor initial units,
exact Shannon splits and shared normalized residual/depth nodes. `units` is the
preceding unit policy in a new wrapper; `conflict` additionally checks binary
contradictions; `relations` also substitutes one block and propagates units again.
This isolates each addition under the same persistence/checking format. There is
no tree-versus-DAG ablation in this experiment. Binary contradiction discovery
and equivalence discovery currently make separate graph traversals; their cost
is charged. The new code reuses the existing recognizer/checker rather than
changing native, affine, equivalence or Lean authorities.

Cache identity remains the full normalized quotient and remaining depth under
one fixed policy. Every incoming request prepares and checks its transport even
on a hit. Source edits invalidate incoming evidence; policy/depth changes alter
reuse identity. Exact complete root programs share within the stream, and every
warm/cold program is rechecked. SAT lifts through the selected branch; UNSAT needs
both exact UNSAT branches. Unknown stays unknown. The experimental format is
`cnf-relation-buckets-v1`.

One block per incoming cofactor is deliberately incomplete. The policy retains
depth two, width eight and 262,144 reserved bucket probes per node. Each initial
or post-substitution unit invocation allows 512 steps and 262,144 reserved
index-work units. These local quotas do not bound SCC traversal, path generation,
normalization, checking, total time or memory. The binary expansion still has at
most `2^(d+1)-1` incoming requests at depth `d`, exponential in depth. No bound
makes every unrestricted CNF reach a small quotient.

## Frozen comparison and full costs

The panel contains 21 exposed sources (16 SAT, five UNSAT), 24 new constructions
(ten SAT, fourteen UNSAT), and four repeats (three SAT, one UNSAT). New controls
cover random three-CNFs on 13/17/21 variables, guarded signed aliases of
9/13/17-variable cores and deleted implications, parity prisms at sizes 6/8/10,
and mixed wide clauses with consistent/inconsistent binary cycles at sizes
10/14/18. Input names, signs and order are scrambled. No new normalized source
duplicates the preceding panel. Labels and descriptions never guide acquisition.
These are designed synthetic controls, not representative external SAT evidence.

Four cyclic process orders start empty with a common fallback. Complete costs
include preparation, recognition, witness/checking work, JSON/SQLite persistence,
warm reuse, cold reconstruction and compression. Interpreter startup, report
metadata, generation, post-hoc diagnostics and preservation audit are additional.
Both native cold readers audit fallback records; two further JSON passes use the
same checker, not independent JSON implementations.

| Workflow | Discovery (s) | Solve/check (s) | Warm (s) | Cold (s) | Complete (s) | Certificate bytes | Native-record bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0 | 0.30476 | 0.02848 | 0.21376 | 0.70153 | 0 | 930,348 | 72,138,752 |
| units | 0.55266 | 0.53711 | 0.31705 | 0.78679 | 2.42425 | 4,143,384 | 832,384 | 76,333,056 |
| conflict | 0.51805 | 0.50149 | 0.29741 | 0.74978 | 2.29474 | 3,999,432 | 782,256 | 75,055,104 |
| relations | 0.48673 | 0.47290 | 0.27795 | 0.70451 | 2.16789 | 3,746,557 | 773,883 | 74,498,048 |

Paired complete reductions are 3.88–7.74% for conflict versus units, 2.50–6.75%
for relations versus conflict, and 7.93–13.52% for relations versus units.
Certificate writes add 0.02519 / 0.02518 / 0.02240 seconds to the structural arms;
archive persistence adds 0.14641 / 0.19641 / 0.19414 / 0.19525 seconds in table
order. Timings are local observations, not asymptotic or general workload bounds.

Across newly acquired programs, bucket calls fall **204 / 196 / 187** and bucket
elimination steps **430 / 368 / 295** for units/conflict/relations. The relation
arm uses thirteen checked binary conflicts and 54 equivalence substitutions,
merging 165 variable occurrences across those local blocks. Initial unit steps
fall from 406 to 329, with thirty additional steps after substitution. The common
root prefix performs 665 folds in every structural arm.

Twenty-nine queries perform substitutions. Their discovery improves 8.88% and
solve/check improves 7.44% relative to conflict-only. The other twenty queries
regress **1.60%** in discovery. All failed recognition and observed strata remain
in the report. Relations has 22 shared targets, but only thirteen join distinct
raw cofactors, all constant. Unlike the preceding policy's nine nonconstant
raw-cofactor merges on this panel, it demonstrates no such nonconstant merges.
The savings therefore do not establish improved general quotient reuse; the
transformation changes residual identities and branching trajectories.

Certificate sizes are pretty-printed file bytes. Combined compressed SQLite/JSON
packages occupy **179,759 / 225,856 / 216,256 / 216,503 bytes** in table order.
Despite smaller raw proofs, relations uses 247 more compressed bytes than
conflict-only. Diagnostics add 0 / 71,387 / 69,281 / 70,136 bytes. Historical
archives, repeated reports and container overhead are extra. Peak RSS falls
modestly versus units but remains above fresh. No peak-memory guarantee follows.

## Remaining interaction and next target

Twenty-seven unique roots remain outside this acquisition family: nineteen of
the exposed sources and eight new inputs; all repeat queries are covered. Their
fifty unknown depth-zero nodes have widths nine (31), ten (13), or eleven (six).
Thirteen stop before elimination; 37 retain partial bucket work before the cap.
The nodes have no active units, unit contradictions, disconnected components,
Horn/dual-Horn form or contradictory binary subsets. Only **one** further SCC
block remains, merging one variable. Repeating SCC quotienting everywhere is
therefore a weak next coverage candidate on these exact nodes.

Consistent binary graphs can still force values without merging an SCC: a
**one-way path `x -> not x` entails `not x`**. A separate post-hoc diagnostic
checks such paths in **32/50** leaves, finding 91 forced-literal occurrences.
Adding those individually checked consequences and running unit propagation
assigns 116 variable occurrences and produces five leaf conflicts. These are
not additional certified root results, and the measured acquisition did not
read this profile. Its evidence is bound to the exact saved node CNFs.

The complete unit/component/binary-SCC/forcing diagnostic costs **0.02944 s**,
including 1,364 forcing searches, 4,493 traversed implication edges and 346 checked
path edges. It uses a simple search from every signed variable, with no claimed
optimal recognition bound. Full counts, paths and follow-up unit traces are in
`remaining-structure-profile.json`.

**Next:** integrate and compare checked one-way binary forcing before full
buckets, then test whether its additional unit consequences reduce interaction
or enable residual reuse. Preserve the exact path source and edge-specific
transport, charge unsuccessful searches, and distinguish leaf conflicts from
root coverage. This is better supported here than repeating equivalence scans
or uniformly deepening the partition. Cold verification remains the largest
cost; graph/source validation cannot be removed merely because proofs share.
General semantic canonicalization and efficient coverage of arbitrary SAT
remain open.

## Validation and preservation

All **2,276 full tests and 26 focused tests pass**. Ten new tests include all
512 two-variable clause sets, seeded mixed CNFs, signed sparse lifting, free
representatives, newly exposed units, one-way non-equivalence, corrupt conflict
paths/graphs/transports, partial quotas and cold replay with recognition disabled.
All sixteen program streams replay exactly; four unique native archives pass
both cold readers. Existing SQLite ResourceWarnings are retained.

All **228 previous manifests, 39,818 artifact entries, 1,253 scientific sources
and 70 proof blocks** remain unchanged. Five source/test files raise the ledger
to 1,258 and one restricted proof is added. Resume
`experiments/results/cnf-relation-buckets/checkpoint.json`, key
`relation_buckets.remaining`, with the bound structural/forcing profile.
