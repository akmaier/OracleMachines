# Reuse the first cofactor during joint proof assembly

The [preceding profile](preimage-fusion.md) leaves a nine-expansion mixed branch.
Its surrounding deletion makes nine calls to joint consequence handling. Two
calls select two consequences; the other seven select one. In each two-consequence
call, forward prefix lookup and backward parent construction use exactly the same
source and first assignment. The exposed census finds **two repeated canonical
prefixes, with 1,518 residual literal occurrences**. Its following replacement
uses one single-consequence call and contains no such reuse opportunity.

## Exact binding and lifetime

Let the source be `F` and the two excluded literals be `l1,l2`. The forward pass
first computes the surviving prefix `F[l1=false]` (in signed-literal notation),
then its canonical CNF, original-variable name map and full serialized key. It
looks for a checked answer. A cached SAT or UNSAT prefix retains priority and
returns or truncates the batch exactly as before. Otherwise the solver visits
the cofactor satisfying both forced values.

After a negative child result, backward proof assembly returns to that first
prefix. The same canonical triple is still held in the caller's local variables;
the recursive visit has its own frame and cannot replace them. Reuse those
values directly. Do not restrict the original source and normalize the prefix
again. The root context still follows the original construction, excluded-path
compilation still checks and transports all reasons, and the native verifier
independently reconstructs every required edge. No name map is exchanged between
different sources merely because their compact keys match.

This relies on the existing bound of **at most two consequences** and immutable
normalizer results. The second backward iteration is exactly the first surviving
prefix; more than two consequences would require additional state and a new
argument. Invalid, repeated or oversized evidence lists remain rejected. Single
consequences, cached prefixes, positive results and disappearing later variables
retain their previous behavior. Budget exceptions unwind the frame normally.

There is no new retained CNF, hash lookup, global cache or invalidation policy.
The normalized prefix already remained live across the child visit in the old
implementation. The change adds a conditional and an accounting counter. Its
optional installation is scoped to a serial process and must not overlap other
threads using these functions.

## Resource bound and comparison

Each applicable negative batch avoids one source restriction, one normalization
of the surviving prefix and one full-key serialization. If the source has `L`
literal occurrences and the prefix has `r` clauses, `V` variables and width `w`,
this avoids the corresponding linear scans and sorting/renaming/encoding work;
it does not change the worst-case complexity of SAT. Existing stack retention,
parent checking, source composition and storage remain charged. Avoiding two
constructions in the exposed query need not yield a large or reliable runtime
saving. The census is an opportunity count, not a performance result.

Both policies use consequence-priority routing, fused causal preimages and shared
partition preparation with restart. Six preceding new edits become controls.
Three sign variants expose the saved nine-expansion source, restoring its exact
historical prefix plus three earlier native IDs, with budget 247. Six fixed-seed
nearby edits have roots absent from the preceding union. Fifteen targets, two
policies and two opposite serial orders produce 60 attempts in 36 workers. Mode
installation/removal is included in complete-worker time. Every paired native
delta and partition sidecar must remain identical. Donor/map selection and
historical acquisition remain sunk. This is a local construction comparison,
not a new whole-source coverage cell or an independent external benchmark.

## Results and limits

The following means average the two opposite orders. Control and new-edit rows
sum three separate two-query streams. All 15 targets already close as UNSAT.
Every paired native delta, partition and expansion count is identical.

| Group | Expansions in either arm | Fused query seconds | Prefix reuse seconds | Change |
|---|---:|---:|---:|---:|
| Six controls | 52 | 0.164418 | 0.159523 | -2.98% |
| Exposed original branch | 9 | 0.027083 | 0.026140 | -3.48% |
| One-variable sign change | 9 | 0.026700 | 0.025806 | -3.35% |
| Global sign complement | 9 | 0.026973 | 0.025544 | -5.30% |
| Six new edits | 70 | 0.188944 | 0.186257 | -1.42% |

Both aggregate edit-group order signs improve, but unevenly: control differences
are **-9.25 and -0.54 ms**, new-edit differences **-5.06 and -0.31 ms**. The
original isolated branch regresses 0.066 ms in the first order. Queries with no
prefix reuse also vary noticeably, including the control replacement that
appears faster. Keep these no-hit observations and every individual sample.
Two orders on nearby inputs do not establish a robust causal runtime saving,
statistical significance or external performance. No further timing selection
is used to replace these samples.

The exact work saving is smaller and easier to interpret. Each edit group reuses
two prefixes; each isolated branch reuses one. Controls remove **1,518 normalizer
literal visits, 1,554 restriction literal visits and 6,657 serialized key bytes**;
new edits remove **1,512, 1,548 and 6,633** respectively. These are saved work
counters, not bytes removed from the persistent archive. Native verification
counts remain 106/106 on controls and 105/105 on new edits. The largest query's
profile falls from **116 to 114 normalizations** and **103 to 101 restrictions**,
while all 51 verification calls remain. Instrumented cumulative times overlap.

Control/new native payloads remain **483,609 / 532,569 bytes**; summed checked
object endpoints remain **3,122,128 / 3,520,214 bytes**. Compressed deltas, database
sizes and partition bytes also match. Endpoint sums are not simultaneous or peak
RAM. The existing immutable prefix stays live in either implementation, so this
change introduces no new retained CNF; no process-peak reduction was measured.
Complete-worker means change from **24.047775 to 24.044536 s** on controls and
**24.472643 to 24.400351 s** on new edits, including historical reconstruction,
auditing, persistence and mode setup. The complemented branch's complete time
regresses 0.83%. These figures do not establish an overall speedup.

## Larger next opportunity: conditional mixed-width reasons

Keep direct prefix reuse optional, but move on from this small opportunity. The
largest new query is case 31's deletion, **86.36 ms** in the prefix mean. It still
uses branch counts `[1,9,1,6,1,3]` after an eight-expansion probe. In
`next-target.json`, the `novel` observation at query position 0, acquisition index
2, binds **125 variables, 258 ternary and 56 binary clauses**, 886 literal
occurrences, budget 247 and three earlier native IDs. Restore that prefix plus
only those IDs from the bound trial delta; replay the prior probe/branch for
warm pools. The final union must not seed comparisons.

Its checked reachable proof DAG has **14 new nodes: five splits and nine unit
nodes**. Six unit nodes end in conflicts and three depend on another child. The
nine nodes store CNFs containing **6,495 literal occurrences**, but their explicit
unit reasons and conflict clauses reference only **148 literal occurrences**:
18 unit, 47 binary and 12 ternary reason clauses, counting separately within each
node. The preceding control branch has the same reason-width totals and 6,510
stored unit-node literals. These are local counts, not a common 148-literal core
or a demonstrated compression ratio. Original-name maps differ; duplicate reason
shapes and conditional assignments have not yet been aligned.

The next primary investigation is whether source-bound conditional unit supports
can be recognized and reused across these mixed-width edits before constructing
all 14 full residual nodes. Compare with the existing causal support/core bank,
not an empty baseline. Preserve the conditions inherited from split and unit
ancestors, child obligations for nonterminal unit nodes, exact clause membership,
variable correspondence and full-source checking. Charge discovery, matching,
transport, publication and cold replay. A transferable negative support must be
checked under its recorded conditions; these 148 occurrences alone supply no
unconditional answer. If recognizing the transfer costs more than reconstruction,
retain that counterexample. Automatic correspondence and useful mixed-family
coverage remain open; this checkpoint adds no new class or arbitrary-SAT bound.

## Validation

Both readers replay **76,182 native records**, all prior extension records and
**342 partition records** (322 earlier plus 20 current observations). All earlier
payloads remain intact; 80 new native records are retained, with no alternative
payload observations. The source census reproduces earlier output exactly. Four
of its ten call frames have no stored answer after the stopped probe and remain
explicitly classified as unfinished work; their path evidence and construction
identities are checked without promoting the frames to answers.

All **1,496 full and 204 focused tests** pass. The full suite emits 44 unclosed
SQLite warnings and the focused suite none; collection-site reports do not
identify allocation sites. The new tests cover positive/negative results,
cached-prefix priority, disappearing variables, invalid evidence, random truth
and byte comparisons, scoped exceptions and cold rejection of tampered parents.
The 244-page manuscript builds without warnings, and all previous 64 proof
environments are unchanged. The final source ledger has
788 entries and preserves the previous 139 manifests and 12,236 artifacts.
The local invariant is argued and tested; no Lean implementation-refinement
proof or new SAT complexity result is claimed.
