# Unit propagation inside exact repair partitions

The new experimental kernel closes all **14 retained combined-portfolio gaps**
on the already exposed transfer panel. It certifies **18 SAT and 18 UNSAT**, up
from the prior repair/export kernel's 12 SAT and six UNSAT. The combined union
therefore grows **22/36 → 36/36**. All 24 originals and twelve related controls
are answered below the unchanged 20,000 entered-context limit; the largest run
uses 7,687 contexts. This is development on known inputs, not new transfer.

The concrete change is ordinary unit propagation under **both flip and keep
commitments** before first-flip branching. It exposes implications that the old
full-proposal false-clause search did not exploit. This is standard DPLL-style
search, not a new SAT tractability theorem. No production defaults change.

## Recognition, exact recomposition and reusable state

For a complete seed, a context fixes some variables opposite to that seed and
others at their seed values. Every other variable is still uncommitted, even
though the current full proposal assigns it its seed value. Unit recognition
must use the committed partial assignment. A clause currently satisfied by an
uncommitted seed value can force that value to be kept. Treating only currently
false clauses as implications misses this deduction.

A source clause with no committed true literal and exactly one uncommitted
literal forces that literal true. Record its source clause index and fix the
variable, as either a flip or a keep. A clause with no committed true literal and
no free variable closes the context. Otherwise, a clause false under the full
proposal supplies the prior disjoint split: flip its first available variable
that differs from the seed, keeping earlier candidates at their seed values.
These children cover exactly the surviving assignments, without overlap.
Unit deductions preserve all models of the parent context. Every child adds a
commitment, so a finite complete root refutation excludes every assignment.
Interrupted search remains unknown; a satisfying full proposal always requires
a complete original-source witness check.

Discovery builds one occurrence index, full-proposal satisfaction counts, counts
of free variables and counts of committed true literals. Assignment and undo
update only incident clauses; an explicit stack avoids recursive search depth.
Unit selection, literal scans, branch assignment copies and undo occurrences
are charged. The root proof is recorded during acquisition, avoiding a second
search merely to reconstruct it. A separate checker derives every unit and
checks every branch and conflict from the source; it does not run discovery or
trust its incremental index. A complete proof can still be exponentially large.

The retained two-variable illustration has clauses `(1)`, `(-1,2)`, `(-2)` and
seed `(true,false)`. A forced keep and a forced flip produce a checked conflict
in one context. The supplemental search found no state-order regression in its
1,000 six-variable probes; this supplies no general dominance claim. Earlier
ordering and restart counterexamples remain unchanged.

## Exposed-panel evidence and costs

The baseline is the **unchanged boundary policy plus its full-root recording
exporter**, including the duplicate acquisition previously needed for six
refutations. The candidate uses the same proposer and gain tie-break rule,
full-support unit closure and disjoint branching. Both allow 20,000 entered
contexts per source; the work per context differs. Labels and reference models
stay outside discovery. Four fresh-process pairs alternate execution order.

| Quantity | Prior boundary/export | Unit propagation |
| --- | ---: | ---: |
| Original SAT / UNSAT / unknown | 8 / 4 / 12 | 12 / 12 / 0 |
| Signed-control SAT / UNSAT / unknown | 2 / 1 / 3 | 3 / 3 / 0 |
| Edited-control SAT / UNSAT / unknown | 2 / 1 / 3 | 3 / 3 / 0 |
| Entered contexts, panel total | 446,191 | 58,118 |
| Mean complete seconds | 11.80695 | 12.69544 |
| Acquisition including internal checks, seconds | 9.97076 | 9.24028 |
| Explicit checking, seconds | 0.34238 | 0.64448 |
| Warm reload/check, seconds | 0.38365 | 0.72917 |
| Two cold reload/checks, seconds | 0.78142 | 1.44612 |
| Model/refutation JSON bytes | 2,713,364 | 19,226,099 |
| Discovery-sidecar JSON bytes | 5,510,680 | 291 |
| Combined gzip bytes | 739,687 | 1,754,206 |
| Maximum observed RSS bytes | 89,489,408 | 108,036,096 |

Complete time increases **7.53%**, with paired increases 9.28%, 4.79%, 8.94% and
7.12%. These are unequal completed workloads: the candidate certifies eighteen
more inputs and retains twelve more global UNSAT proofs. This is a coverage gain,
not a complete-workflow speedup. The new run performs 547,679 forced keeps and
446,288 forced flips. Sharing incident-clause state cuts the search-context count,
but unit work, proof construction, storage and independent replay remain costly.
The candidate retains 42,333 contexts in its eighteen root refutations.

All input JSON/DIMACS reads and hashes, proposal/index preparation, discovery and
internal/explicit checks, model and sidecar writes, three compressions, warm and
two cold source/proof reloads are timed. No search state survives replay; OS
caches are not flushed. Imports/startup, reporting metadata, independent audits
and historical append-only evidence storage are additional. The new JSON envelope
makes baseline bytes differ from the preceding single-export measurement. No
modern-solver speedup ratio is inferred from the earlier reference runs.

Six new SAT and twelve new UNSAT kernel answers include four negatives already
certified by the older portfolio. Hence the combined union gains six SAT and
eight UNSAT, exactly the fourteen retained gaps. All eighteen negative results
now have independently checked project refutations; the previous Z3 UNSAT
reference alone had no such authority. The original external 37/37, constructed
32/32 and synthetic 182/182 unions remain separately denominated and immutable.
Full support is still searched. Completion does not certify small separators,
low interaction width or an efficient structural class.

## Validation and remaining obligations

All **2,572 full and 20 focused tests pass**. An independently reproduced truth
audit checks **8,882 queries**: 6,173 SAT and 2,709 UNSAT. It includes all 512
canonical two-variable CNFs with every seed, all 3,304 three-variable CNFs with
at most three distinct clauses with all-false/all-true seeds, and 128 fresh sparse
signed edited sources with two seeds. The 836 one-context interruptions retain
unknown. All 49 eligible fresh SAT witnesses survive a satisfied addition and
are rejected after a contradictory addition. The old 32 constructed cases also
produce checked models, as a separate audit, not a new transfer denominator.

Tests cover empty clauses, empty formulas, tautologies, duplicates, sparse names,
undo restoration, a 1,500-variable implication contradiction, missing children,
invalid unit premises, changed sources, incomplete orders and malformed masks.
Checking succeeds with discovery disabled. Validation reproduces all eight
matched outcomes, counters and warm/cold checks, exactly reproduces the frozen
baseline exporter, rechecks the old 37-input union, and preserves **247 prior
manifests, 83,273 artifact entries, 1,346 scientific sources and 86 proof blocks**.
The five new scientific files bring the source ledger to 1,351. The manuscript
adds one proof of the unit-plus-partition composition.

The largest next coverage gap is **fresh, larger external transfer after this
policy change**, with explicit unresolved sources and charged comparison against
both the old policy and a modern solver. The largest measured reuse gap is
**smaller, cheaper negative evidence**, including guarded reuse across contexts
and edits rather than repeating large unit traces. Better unit selection can be
supporting work, but preprocessing, recognition costs and unrestricted search
remain explicit. A complete finite panel and an exact description of all CNFs
do not prove a polynomial SAT algorithm.

Resume `experiments/results/cnf-unit-partition/checkpoint.json`, key
`unit_partition`. The protocol, eight trials, initial development probe and its
exact archived source, reproduced audits and manifest remain available there.
