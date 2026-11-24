# Compose guard contradictions on their supporting clauses

24 November 2026. Deferred guard checking removed most unused local proof
preparation, but native composition still carried the full local CNF through
its implication paths. This experiment compiles the selected contradiction on
its actual clause support and lifts the result to the enclosing formula.

## Exact inference and recognition

For a selected pair of contradictory implication paths, collect the original
unit/binary clauses used by the paths and the local template clauses supporting
every selected nonoriginal edge. Their union H must be a nonempty subset of the
actual local CNF C. The selected checked consequences refute H. A native
refutation of H therefore refutes C, using the already supported negative
`component` certificate with exact clause indices. This rule needs no variable
independence and establishes no positive component join.

The support is an exact sufficient subset, not a minimum unsatisfiable core.
No search for a globally smallest support is performed. Full-support cases
retain the previous compiler. For a smaller support, the solver first checks
whether its canonical native root is already available. Otherwise it reuses
the previous path compiler on H and stores its refutation. The enclosing C gets
only the native subset wrapper. The candidate graph, selected local consequences,
source binding, dispatch order on misses and existing fallback remain unchanged.
Different proof keys can change later cache hits and search; equality of paths,
coverage or work is not assumed.

Path templates retain enclosing coordinates while each published native node
uses its canonical variables. The split variable is rebound through H's own
name map. If it is absent from H, conditioning on that premise leaves H itself:
the first path already refutes H and no split on a nonexistent variable is
published. Clause membership and native verification remain mandatory even
when variables overlap between H and the rest of C.

The recognizer can share a native support root across distinct enclosing
formulas when their chosen supports have the same normalized encoding. It does
not discover arbitrary signed isomorphisms, minimize supports, or guarantee
that a reusable compact core exists. Construction scans the full clause set,
selected path edges and selected template supports, plus sorting/canonicalizing
their union. Compilation, verification, serialization and retrieval costs
remain additional. Intermediate support maps and canonical buffers need space.
The template-bank byte counter does not account for all such transient objects.

Every native wrapper still contains the full local C and its subset indices;
this optimization removes repeated full-context intermediate proofs, not the
cost of recording C itself. A support can be as large as C. Existing rollback
semantics also distinguish attempted insertion counters from durable rows.
The cumulative research bank is append-only, so lower per-query state does not
mean that the preserved historical bank shrinks.

## Matched comparison

The protocol freezes the implementation, tests and comparison before timing.
It uses all eight exposed chronological edits, two serial repetitions in opposite
arm order, and ordinary search, the frozen witness gate, and support composition.
Every worker restores only the causal origin prefix and provisioned support
bank. Neither the cumulative result union nor a later query seeds the run.
The 256 native dispatch allowance and all preceding gate limits remain; compiled
proof nodes are additional. No new total-work or total-memory bound is asserted.

The unchanged worker charges restoration, setup, solve, accounting, warm and
cold native replay, serialization and compression. Imports, source hashing,
protocol/case loading, earlier acquisition/extraction and final audits remain
outside that interval. Comparisons retain both repetitions and regressions.
Selection of a profile target after comparison is explicitly adaptive.

## Results

The table gives sums of per-case means for two alternating repetitions. Times
are seconds; endpoint bytes are sums across separate runs, not simultaneous
space. All three arms leave all eight whole queries unresolved at 256 dispatches.

| Arm | Solve | Complete worker | Checked native bytes | SQLite bytes |
|---|---:|---:|---:|---:|
| Ordinary | 7.95907 | 91.38423 | 154,443,458 | 719,503,360 |
| Full-context witness gate | 8.63729 | 93.31281 | 164,001,110 | 723,243,008 |
| Support composition | 8.32519 | 92.13506 | 155,521,837 | 720,076,800 |

Support composition saves **3.61% solve time**, **1.26% complete-worker time**
and **5.17% checked native state** against the witness gate. SQLite endpoint
totals fall 0.44%. It still costs **4.60% more solve time**, **0.82% more complete
worker time**, 0.70% more checked native state and 0.08% more SQLite space than
ordinary search. All eight per-case solve means improve against the witness
gate and remain above ordinary search. The two repetitions are exposed
diagnostics, not confidence bounds or fresh performance evidence. No default
changes and no new whole-query coverage is claimed.

Both gates close 34 local contexts: 15 opposite-unit, one unit/binary and 18
binary-guard closures. Every support is a proper subset on these runs. Across
those compilation sites, source contexts contain 11,781 clauses and 32,371
literal occurrences; their support unions contain 1,043 clauses and **2,433
literals**, a 92.48% reduction in that aggregate literal volume. This compares
initial context sizes once per closure, not all computation or memory traffic.
The gate's actual restriction-literal counter falls from 253,291 to 17,276.
Five existing support roots are reused, and 29 are published; hit provenance
within the current query versus the origin prefix is not separately counted.
The guard discovery work remains: 33,006 candidate checks, 142,003 guard-pair
checks, 87 checked local consequences and 635 inconclusive sites out of 669.

Smaller proofs do not imply fewer records. Attempted native insertions rise from
3,093 to 3,101, while their payload bytes fall from 36,988,818 to 35,268,989.
Edit 4's checked native state increases from 20,001,701 to 20,057,827 bytes and
its SQLite file increases 36,864 bytes against the witness gate. Both raw
repetitions and all storage regressions are retained. Template/record bank
accounting is unchanged; temporary support maps remain additional. The sum of
per-case mean peak RSS falls only 0.12% versus the witness gate and is 0.69%
above ordinary search. These sums are not simultaneous memory, and no reliable
peak-RSS improvement is established.

## Largest publication cost: recompressing unchanged history

The final preservation audit adds only 173 native records and keeps all old
payloads byte-identical. Yet publishing the cumulative union recompresses its
entire 2,102,272,000-byte SQLite database: gzip alone takes **109.15 seconds**
within the **252.80-second preservation audit**, additional to the timed worker
intervals above. The union grows by 409,600 SQLite bytes, and the new complete
gzip is 152,623,819 bytes. This is a measured checkpoint-publication cost, not
SAT search or the cost of recognizing a pattern.

**Highest next publication target:** reuse the immutable parent archive and
export only checked append records, with a bound parent-plus-delta descriptor
and exact cold reconstruction. The repository already has `cnf_append_delta.py`
and append-cursor machinery; reuse those contracts where compatible instead
of rebuilding them. Check all six table schemas, duplicates/conflicts, parent
identity, new proof dependencies and unchanged old payloads. Measure export,
compressed storage, restoration and replay against the current full snapshot.
Preserve the full snapshot as the control, retain a fallback for non-append
changes, and distinguish logical table equality from binary SQLite identity.
No layered-archive implementation or saving is claimed in this checkpoint.

This publication gap ranks above another small gate optimization in total run
cost. The solver-specific target below remains useful but must not obscure the
cost of preserving the expanded knowledge base. Broader SAT coverage remains
an independent research obligation.

## Next bottleneck: repeated binding of the same local context

The adaptive profile again selects edit 28, the largest remaining support/ordinary
solve regression at 10.33%. Seven closure compilations fall from 0.17027 to
0.02096 cumulative seconds; the gate falls from 0.21922 to 0.06997. Selecting
the seven supports itself takes 0.00033 seconds. The previous composition
bottleneck is substantially reduced, including two existing support-root hits.

Selected consequence transport now takes 0.02328 cumulative seconds, including
0.02093 in exact-core RUP checking. Each admitted hint still builds a position
map for the same local C and revalidates C's canonical form. The next bounded
experiment should bind an immutable local context and its clause positions once
per witness attempt, then reuse that binding across the selected certificates.
Preserve each certificate's unit reasons, conflict, coordinates and actual
support containment; reset the binding on every changed component, assignment
or query. Native publication and cold readers remain independent checks.
This is a proposed saving, not implemented by the current checkpoint.

Full-query native verification still takes 0.66317 cumulative seconds and
normalization 0.52307, versus 0.63052 and 0.47956 for ordinary search. Nested
profile times overlap and cannot be added. Thus the remaining total cost is
largely inherited search/checking, not support selection. Any next improvement
must compare whole-query costs and misses, rather than extrapolating the large
local composition reduction to all runtime.

Broader discovery remains separate. Recognizing these ready compact cores before
rediscovering their guard witnesses may help, but the old negative/partial-residual
pools already preserve regressions from discovery and coordinate matching.
Do not reintroduce broad candidate scans without new evidence. Exact support
correspondence, origin acquisition, fresh unlabelled mixtures, wider interactions
and efficient arbitrary-CNF closure remain open. The current five root hits do
not establish a general cross-query recognition method.

## Correctness checks

Focused tests cover all 256 subsets of the eight nonempty unit/binary clauses
over two variables against a full candidate bank and extra enclosing clauses.
Independent truth tables check the decisions, and every returned refutation
passes native publication. Other tests cover sparse coordinates, an absent
contradictory variable, missing support, original binary edges, unchanged
full-support fallback, allowances, live routing and 40 seeded unlabelled CNFs.
A cold reuse test publishes two enclosing formulas with one shared support root
and checks both native readers. It establishes cross-formula reuse in that test. Live support-root hit counters
do not distinguish origin-prefix hits from reuse earlier in the same query. No new proof kind or Lean
refinement is introduced.

All previous sources and artifact manifests remain hash-bound. Exact old
archives can reuse their same-case two-reader audit; novel archives require
both readers and an append-only union merge. Existing payloads are never
replaced by alternative proofs. Raw trial archives preserve those alternatives.

## Validated checkpoint

All 56 focused tests and 1,778 solver tests pass. The full suite reports the
same 43 unclosed-SQLite ResourceWarnings; the focused tests report none. The
prior 64 manuscript proof blocks remain byte-identical; the 263-page paper
builds without warnings. No Lean code changed.

Preservation rechecks 168 prior manifests, 16,078 artifact entries and all 972
previously frozen sources. Seventeen exact archives reuse manifest-bound
two-reader audits; seven novel archives are freshly checked with both readers.
All 48 timed workers and three profiles also perform cold native replay. The
append-only union reaches 160,338 native records; the five other authority
tables are unchanged. Forty-five alternative-payload observations stay in raw
trial archives; they never replace older authoritative payloads.

Resume `experiments/results/cnf-guard-support/checkpoint.json` using its multipart
archive descriptor. The protocol, both repetitions, adaptive profiles, analysis,
decision, checks and sealed manifest retain the costs and limitations.
