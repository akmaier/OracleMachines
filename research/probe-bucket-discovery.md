# Full-CNF failed assumptions before bucket expansion

Date: 27 November 2026. Parent: `4e9fe251`.
Evidence: `experiments/results/cnf-probe-buckets/`.

## Result and decision

Checked full-CNF probes certify **19/20** exposed structural misses, thirteen
SAT and six UNSAT. New unique-panel coverage rises **23/24 to 24/24**; all four
repeats remain covered. There are no observed coverage losses. Thus the new path
certifies **47/48** queries without fallback. The unchanged fallback already
supplies all answers; these are improvements in restricted structural acquisition,
not a success rate on arbitrary SAT.

The scan version reduces complete cost **27.94%** against the preceding repeated
binary closure in the same wrapper. The indexed version saves another **12.89%**
against scans, or **37.23% overall**. All four paired comparisons improve. It
still costs **1.67 times fresh solving**, so production defaults stay unchanged.
Indexed probing becomes the next research baseline. Its comparison changes both
propagation traversal and index reuse; it does **not** isolate the runtime effect
of sharing an otherwise identical index implementation.

## Exact consequence and recomposition

For an assumption `a`, start with `a` true, then record each forced literal and
its exact source clause. The independent checker requires that clause to have
exactly that one unassigned literal and no satisfied literal. A final clause must
be entirely false. This certifies `F and a` UNSAT, hence `F` entails `not a`.
No conclusion follows from a probe that reaches a fixed point without conflict.

After initial unit/conflict/signed-equivalence preparation and repeated binary
forcing, probe both signs of active variables in a fixed order. Collect checked
failed assumptions, add their opposite literals as units, propagate and normalize.
Retain the unit values and inverse renaming at every round. A successor round
requires a strict decrease in active variables. As with repeated binary forcing,
there are at most `n` accepted rounds on an incoming formula with `n` variables,
including a possible final nonprogressing round. Partial processing remains exact.

Replay reconstructs the exact CNF for each probe, verifies the unit reasons and
conflict without rerunning discovery, then checks the recorded unit restriction.
SAT models lift through the round maps in reverse order, before the earlier
binary/equivalence maps. Every SAT incoming transport is checked. A split is
UNSAT only if both exact children are refuted; unresolved remains unresolved.
Old native, equivalence, affine and Lean formats are unchanged.

A targeted five-variable example distinguishes this rule from binary reachability:
`(-x or a), (-x or b), (-a or -b or c), (-a or -b or d), (-c or -d)`.
Assuming `x` forces `a,b,c,d` and a conflict, so `not x` is entailed. Its binary
subformula has no forcing path, and its two wide clauses are not complementary
parents of the existing folding rule. Deleting the final clause invalidates the
failed-assumption certificate; that adversarial edit is tested.

## Shared structure and resource bounds

The indexed engine builds one literal-to-clause occurrence map per unchanged
round CNF and shares it across that round's probes. Assignments, satisfied-clause
sets, pending counts and queues are private to each probe. Processing a true
literal marks its occurrence clauses satisfied and decreases pending counts for
its false occurrences. A newly unit clause is scanned to recover its reason.
The immutable occurrence map and initial-unit list are never modified by a probe.
Source edits, restriction and renaming invalidate this index; this experiment
rebuilds it after a round rather than claiming incremental maintenance.

With `L` literal occurrences, `m` clauses and `n` variables, index preparation
uses `O(L+m)` time and space in the unit-cost model with constant-time map access.
Each assigned literal is processed once, each occurrence visited at most once,
and each clause reaches the unit threshold at most once. A probe therefore has
`O(L+m+n)` worst-case work, including private state and reason scans. Scan-based
propagation can take `O((n+1)(L+m))`. These are local bounds; integer bit costs,
normalization, transport and the rest of the solver must also be charged.

The checker rebuilds the active-variable set **for every stored failed probe**,
so its cost includes a full `L` scan as well as the reason/conflict literals.
The `probe_checked_literals` counter counts the latter only; measured time covers
both. There is no claim that cold replay is proportional only to trace length.
Evidence stores clause references and at most `n-1` propagation steps per failure.
Discovering the index does not provide a proof: cold checking uses only the exact
source and recorded reasons.

Discovery attempts at most **128 probes cumulatively per incoming cofactor**,
with at most eight probe rounds. Unsuccessful probes consume this allowance.
The checker bounds stored failures, not the unrecorded unsuccessful attempts.
The preceding binary forcing has its separate eight-round/262,144-edge allowance;
each unit invocation has 512 steps and 262,144 reserved index-work units.
Buckets retain depth two, width eight and 262,144 probes per node. These are not
wall-time or memory caps. There is no per-probe work cutoff; conditioning remains
exponentially branching as depth grows. Complete efficient unrestricted SAT
coverage and compact closure remain open.

Exact full normalized residual plus depth still identifies local reusable nodes
under a fixed policy. Different incoming histories keep separate transports.
Whole-root programs share within a stream and are checked on warm/cold use.
Source and policy changes invalidate these bindings. Both scan and indexed arms
have the same residual graph, failed-assumption sets, unit steps and verdicts;
propagation order and reason traces may differ.

## Frozen controls and complete costs

Twenty exposed unique sources, twenty-four new constructions and four repeats
make 48 queries (26 SAT, 22 UNSAT). Seed `2711271005` freezes random three-CNFs at
16/20/24 variables, failure motifs with deleted terminal clauses, parity prisms
at 9/11/13, and shared modules with compatible/opposed clauses. Names, signs and
clause/literal order are scrambled. Labels/descriptions are audit-only. No new
normalized source duplicates the parent panel. These synthetic controls do not
establish representative external coverage.

**Retained control limitation:** the constructed wide-failure motifs have two
complementary clauses, so root folding can turn them into binary constraints.
They were not replaced after seeing the result. Their coverage is not evidence
that probing discovered genuinely new wide interactions. The targeted example
above and exposed-gap gains supply separate evidence.

Four cyclic orders run all four arms in fresh processes with the same fallback.
Complete cost includes input preparation, discovery, checking, evidence/database
writes, warm use, cold reconstruction and compression. Interpreter startup,
metadata, generation, historical acquisition, post-hoc profiles and final lineage
audit are additional. Both native cold readers check fallback archives; the two
JSON replay passes share one checker, not independent implementations.

| Measure | Fresh | Binary closure | Full scans | Shared index |
|---|---:|---:|---:|---:|
| Complete seconds | 0.68633 | 1.83009 | 1.31870 | 1.14876 |
| Discovery seconds | 0 | 0.42673 | 0.54328 | 0.37682 |
| Solve/check seconds | 0.30222 | 0.39255 | 0.16439 | 0.16409 |
| Warm seconds | 0.02326 | 0.23111 | 0.17424 | 0.17441 |
| Cold seconds | 0.21145 | 0.59120 | 0.36429 | 0.36359 |
| Evidence-write seconds | 0 | 0.02143 | 0.01845 | 0.01743 |
| Archive-persistence seconds | 0.14181 | 0.15935 | 0.04762 | 0.04644 |
| Raw certificate bytes | 0 | 3,210,867 | 2,399,422 | 2,337,285 |
| Native record bytes | 910,854 | 636,170 | 18,445 | 18,445 |
| Combined compressed SQLite/JSON bytes | 178,225 | 177,387 | 62,907 | 61,437 |
| Peak process RSS bytes | 71,876,608 | 71,270,400 | 60,489,728 | 60,407,808 |

Diagnostic bytes are separately 0/144,342/119,268/119,268. Historical copies and
container overhead remain extra; peak RSS is an observation, not a memory bound.
Indexed versus scan paired reductions are 13.35%, 13.43%, 12.88% and 11.90%;
indexed versus binary reductions range 36.71% to 37.52%.

Binary-to-indexed bucket nodes fall **158 to 101** and split nodes **71 to 34**,
but elimination steps **increase from 272 to 327**: smaller accessible residuals
can expose more elimination work. The indexed graph has 84 accepted probe rounds,
475 failed assumptions, 418 ensuing unit steps and at most four accepted rounds
per edge. Its 3,838 reason steps occupy 64,110 compact probe-round bytes, versus
4,620 steps/70,075 bytes for scans. Different traversal orders give shorter traces
here; that is not a general compression theorem. Both have eleven shared targets
and six distinct-raw joins, all constant; no new nonconstant semantic sharing is
established.

Both probe arms attempt **5,116 probes**. The indexed arm builds **151 indexes**,
visiting 26,573 source literals at setup, 124,804 occurrences during probes and
25,364 literals in unit-reason searches. The scan arm charges 1,455,513 literal
visits. These counters cover different operations, not interchangeable time units.
Acquisition checks visit 31,959 reason/conflict literals indexed and 38,364 scan;
other checker scans are included in time. Forty-five edges stop constant,
65 without another failed literal and two at the 128-probe limit. Both capped
edges belong to a source the full pipeline certifies. The remaining miss hits
neither cap, so a larger allowance does not explain it.

## Remaining gaps and ranked next work

1. **Coverage: combine newly exposed relations and improve the decomposition.**
   The one remaining source is a satisfiable random three-CNF with 23 variables.
   Its two depth-zero unresolved leaves stop at width nine after 4,544 and 1,216
   bucket probes. A separately checked census finds no units, components,
   Horn/dual-Horn form, binary conflict or forcing. One signed-equivalence block
   merges two variable occurrences. Test reapplying checked relation substitution
   after full-CNF consequences, with strict progress and correct transport;
   compare against a bounded ordering/width-nine control. This is a hypothesis,
   not demonstrated additional root coverage. Use new nonfolding wide mixtures
   and adversarial edits rather than tuning only to this one source.
2. **Cost: avoid repeated reconstruction and checking within one verified source.**
   Discovery (0.37682 s, including an internal certificate check) and cold replay
   (0.36359 s) dominate. Separately charged profiling identifies normalization,
   bucket verification and restriction scans as leading work. Reuse a checked
   normalized source and validated intermediate residuals within a single replay,
   keeping incoming histories and external source validation explicit. Do not
   trust a cache merely because it contains a digest. Next compare identical
   certificate streams and charge preparation, lookup and invalidation.
3. **Selective acquisition and broader validation.** The first indexed trial
   spends 1,334 probes on 27 queries the binary baseline already certifies.
   A cheap structural-first gate could avoid some work, but obtaining that gate
   can itself duplicate bucket search. Test it with total costs and new inputs;
   external SAT benchmarks remain necessary before distribution-wide claims.

The remaining structural census costs 0.00120 s. A separate full-CNF census tries
68 assumptions across both leaves, checks every reason, and finds **zero** failed
literals without truncation (0.00512 s, 25,630 propagation visits and 417 checked
reason literals). The two phases add no root authority. The instrumented discovery
and two-pass JSON profile take 1.06136/0.99623 s; full-suite validation ran
concurrently, cumulative entries overlap, and these timings are not matched
speedups. All diagnostic records and drivers are preserved separately.

## Validation and preservation

All **2,312 full tests and 36 focused tests pass**. Twelve new tests cover all
512 two-variable CNFs in each mode, 90 seeded wider cases with both signs of every
variable, independently checked failures, nonfolding wide consequences, immutable
index reuse, deleted clauses, malformed/corrupt traces, caps, sparse signed model
lifting, exact binary-control translation and discovery-disabled cold replay.

All 231 preceding research manifests, 43,681 artifact entries, 1,268 scientific
sources and 73 manuscript proof blocks remain unchanged. Five new scientific
files bring fingerprints to 1,273; one restricted proposition is added. Prior
alphaXiv publication snapshots remain unchanged. Existing SQLite ResourceWarnings,
scan regressions, the foldable-control limitation and the final structural miss
are preserved. Resume `experiments/results/cnf-probe-buckets/checkpoint.json`.
