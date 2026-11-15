# Carry checked state across original cases

The same checked session can serve different originals when the recognition
policy, historical rows and complete route catalog retain their authority.
Switching the selected original does not itself invalidate a certificate. The
new coordinator checks the selected focus against the next original before
continuing. On the measured transition, this avoids a second session build and
closes **case 1061**, increasing coverage **67/83 -> 68/83**.

## Matched comparison

Both methods restore the same previous checkpoint, build a session, query the
already completed original **case 1120**, and bind the next focus **39/167/519**
to original **case 1061**, retained index **13**. This first query replays stored
knowledge; it does **not** acquire case 1120 again. The restart method then
discards the checked session. The retained method passes it to the unchanged
live-digest worker. Both charge the initial construction, query, binding,
copying, checking, acquisition, route maintenance and persistence.

There are two independent repetitions per method, with reversed method order.
All four workers take one advance, admit and store the same **six probe
patterns**, and close the focus. They use the same saved pair and produce
identical operation records and logical results. The budget allows 32 admissions
per batch and at most two batches, but neither method needs the second batch.

| Mean measured cost | Restart | Retain |
| --- | ---: | ---: |
| Complete query-and-expansion sequence | 18.99400 s | 11.61121 s |
| Expansion worker, including preparation and export | 8.56483 s | 0.94843 s |
| Worker session construction or boundary guard | 7.61459 s | 0.00374 s |
| Local expansion | 0.15137 s | 0.14447 s |

The complete sequence falls **38.87%**. The worker alone falls **88.93%**, but
that percentage excludes the common initial query and must not be presented as
the complete-sequence saving. Initial session construction costs about eight
seconds in both methods; the completed-original query and new-original binding
each cost about 1.2 seconds. Timing the entire sequence also charges serialization
of these records and union-delta checks. There is no end-to-end pipeline comparison:
the producer runs all four sequences and shared validation work in **275.67776 s**.
Parent reconstruction takes **119.01318 s** and final global route preparation
plus coverage takes **69.64522 s**. These costs remain.

The observations use development cases and shared operating-system caches.
Two observations per method are descriptive, not a confidence interval or a
holdout performance result. The worker and its search policy are unchanged.

## Structural result and storage

The selected saved pair has targets **37/150/452** and **36/148/444**. Their
new probe chains have two and four nodes respectively; both end at the already
stored empty-clause contradiction. No new tractable-family terminal is needed.
This is reuse of existing contradiction evidence after checked reduction, not
a proof that these raw inputs belong to Horn, dual-Horn or 2-CNF. All six new
profiles exclude those classes and both uniform assignments. The original
formula has shape **48/204/612** and is **satisfiable**, as its independently
checked model confirms. The selected conditional subproblem is unsatisfiable;
completing its coverage obligation does not refute the original. Fifteen of the
83 originals remain uncovered.

History grows **77,824 bytes**, from **778,821,632** to **778,899,456 bytes** and
**42,341 patterns**. The union delta is **147,456 SQLite bytes / 7,095 compressed
bytes**. Both methods store identical evidence; session retention does not
compress persistent storage. Reference nodes increase **4,198 -> 4,413** and
the expanded positive certificate grows **3,518 -> 3,564 steps**. Here a positive
certificate establishes structural coverage; it does not mean the formula is
satisfiable. The catalog has **709 activation routes**, with no pending target
or missing link.

Retaining checked state increases the live cache on this transition. At the end,
the retained method has **3,100 checked pattern objects / 108 prepared checked
objects**, versus **2,453 / 11** after restarting. These are separate cache
entry counts, not disjoint byte totals or measured peak RAM. The additional
objects avoid rechecking historical evidence. No cache eviction policy or
arbitrary-workload memory bound is established.

## Exact reuse condition and cost accounting

`cnf_original_binding.bind_original_focus` normalizes the specified originals,
follows their saved forced continuations and selected frontiers, and requires
the proposed source to occur as an open selected leaf of every specified
original. It rejects closed originals, unrelated sources and invalid or duplicate
indices. It returns detached binding records and performs no acquisition. This
is a source-to-original binding check, not a global minimum-cost selection rule.

The caller guards the live session before this read-only traversal and again
before expansion. The existing `ExpansionSession` checks database and schema
versions, fixed policy, sidecars, admission and change counters, and absence of
unfinished transactions or recursive checks. It requires exclusive ownership
and immutable historical rows and cached authority objects. Checked acquisition
and maintained route updates remain mandatory. A process restart reconstructs
and checks authority again; persisted closure flags are insufficient.

Write the cost of a sequence over originals as initial construction `C_0`,
query and binding costs `Q_i + B_i`, boundary guards `G_i`, and workers excluding
construction and boundary guards `W_i`. Retention pays

`C_0 + sum(Q_i + B_i + G_i + W_i)`.

Restarting at those boundaries additionally pays fresh construction `C_i`,
while later checking may differ because its caches are colder. These symbols
are measured costs, not constant-time assumptions: binding currently invokes
composition and traverses saved structure, and live digests still read all
eight tables. Memory retains the checked objects and complete maintained catalog
visited during the session. Neither their size nor fresh acquisition is bounded
polynomially for arbitrary SAT by this experiment.

## Validation and reproduction

Run `python3 -u experiments/compare_cnf_original_handoff.py OUTPUT`, followed by
`python3 -u experiments/validate_cnf_original_handoff.py OUTPUT`. The second
command independently reconstructs every intermediate catalog, recomputes the
original binding without the new helper, and disables fresh recognition and
reference search. It checks branch evidence, original coverage, identical
operations and deltas, and the next selected focus. The four new binding tests
cover shared-original binding, detached output, rejected scopes and reuse after
a completed query. Detailed checks and commands are recorded with the results.

Independent replay passes in **514.17263 seconds**, reproduces all four arms
and verifies all **4,413 reference nodes**, including the original SAT model.
All **4,198 prior reference payloads**, **1,567 artifacts / 30 prior manifests**
and **91 historical source files** are unchanged. All **249 tests** pass. The
manuscript builds to **164 pages**, preserving all **64 previous proof blocks**.
Validation tasks overlapped; cold elapsed time is not a speed comparison. The
checkpoint manifest binds **67 artifacts**, with fingerprints and commands in
`validation.json`. A preliminary finalization assertion incorrectly inferred
original UNSAT from the two refuted conditional targets; the independently
checked SAT model rejected it. The correction is retained in the validation
record and made explicit above. Solver results were unchanged.

## Resume and next gap

Resume `experiments/results/cnf-original-handoff/report.json` using
`compare_cnf_original_handoff.restore_checkpoint`, report SHA-256
`6944b224d026a09bc6aa1bc6bb118d55b29a94a851ef2f2fcc2054f7c9358175`.
Preserve evidence **(1, 42, 156, 56, 1)** and **two bridges**. The report's `source`
is completed; follow `next_selection`: **40/158/467**, original **case 1443**,
retained index **72**, source hash
`275abd014656ded13e9b3acab99c976726b7ca9b424f91c71d1a6ea057fd21f6`,
with no pending split.

The largest remaining live-session cost is global coverage and original navigation,
not the roughly 0.14-second local expansion. Compare the existing `CoverageIndex`
with full recomposition on the same checked append and across successive
originals. Charge initial construction, complete catalog comparison, implicit
rule changes and pending-target activation; preserve the same frontier and
original binding. The present experiment receives a previously checked global
selection and does not yet maintain that selector incrementally. Parent replay
is a separate, still larger cold cost. No minimum expansion or uniformly
polynomial arbitrary-SAT result follows.
