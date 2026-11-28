# Watched propagation with all retained knowledge active

The 128-clause admission experiment reduced work but lost two of three checked
answers. This experiment retains the full active clause set and changes how
partial assignments trigger propagation. It targets cheaper expansion without
sacrificing those earlier proof routes. Production defaults stay unchanged.

## Mechanism and exactness

Every non-unit clause has two watched literals. Assigning a variable scans only
the watch list for its newly false literal. A satisfied other watch permits an
early skip; otherwise an available replacement moves the watch. If none exists,
the clause enters a candidate set for a unit implication or conflict. Unit and
empty clauses enter that set initially. Candidate processing validates the whole
clause and chooses the smallest actual clause index, removing stale entries.
This preserves the reference engine's propagation order rather than switching
to FIFO propagation.

Learned clauses watch their highest-level literals, including the asserting
literal. Backjumping restores the assignment trail without restoring watches;
the asserting clause is queued explicitly. A previously propagated closed
prefix has no unprocessed unit, while a learned clause either retains its
lower-level implication or regains at least two free literals when the prefix
is shortened below its asserting level. Full proposed-model satisfaction counts
update only when an assignment differs from the target proposal, and those
updates are undone symmetrically. Counts with known list lengths are charged in
bulk. This is an implementation bundle, not an isolated timing attribution to
watch movement alone.

The same target-only seed, activity updates, phase choices, gain ties, first-UIP
resolution and budget remain in use. All surviving knowledge is still active,
checked, copied and persisted. The old checker validates every resulting proof
against the target alone. SAT requires a complete target model, UNSAT a derived
empty clause, and budget exhaustion remains unknown. Nothing here changes the
underlying CNF's models, preprocessing obligations or unrestricted SAT complexity.

## Frozen comparison

The scientific sources and two alternating orders are frozen before the measured
runs. The panel remains sixteen edits of eight already exposed refuted parents;
source bytes, trusted reference outcomes, target-only proposals and the
2,000-context cap are unchanged. No new labels or fresh external inputs guide
the watch policy. The sixteen other edits of SAT parents remain separately
recorded and are not added to the performance denominator.

Both policies certify **3/16**, leaving **13 unresolved**. All sixteen output
certificates are byte-identical and search diagnostics are identical, as are all **30,395 entered
contexts**, proof sizes, compression bytes and checking/replay counters. The
baseline reproduces the parent checkpoint exactly. The candidate improves
full-admission cost without discarding clauses; it does not increase coverage
beyond full admission.

| Quantity | Full occurrence index | Full clauses with watches |
| --- | ---: | ---: |
| Mean complete seconds | 173.19065 | 72.28360 |
| Acquisition including checks, seconds | 150.89725 | 50.08761 |
| Explicit checks, seconds | 3.70444 | 3.75885 |
| Warm reload/check, seconds | 4.37474 | 4.21989 |
| Two reload/check rounds, seconds | 8.38952 | 8.54323 |
| Writes, seconds | 0.33759 | 0.35695 |
| Three compressions, seconds | 5.44613 | 5.27781 |
| Proof JSON bytes | 110,545,079 | 110,545,079 |
| Combined gzip bytes | 4,114,583 | 4,114,583 |
| Maximum observed RSS bytes | 465,453,056 | 479,199,232 |

Mean complete cost changes **-58.26%**, with paired changes
-58.35% and -58.18%. The baseline makes
319,681,345 assignment and
319,366,134 undo occurrence visits. The candidate
makes 157,265,099 complete-model assignment
visits and 157,104,130 complete-model undo visits,
plus 19,313,921 watch visits,
30,730,939 replacement-literal inspections and
4,510,435 candidate-validation literal inspections.
These categories perform different work and should not be summed as equivalent
operations. Watch construction, moves and stale candidates are retained in the
full counter ledger. No proof material is removed.


Complete measured cost includes input/hash reads, parent reads and checks,
selective transport, full augmentation, watch construction and updates, search,
substitution, checks, writes, three compressions and reload/check rounds. Original
parent acquisition, imports/startup, reports and independent audits are additional.
The two rounds called cold in the data parse fresh objects in the same worker,
after a warm round; they are not independent cold-start process timings and do
not flush OS caches. An additional fresh Python worker per policy reproduces all
answers and checking counters with search, expansion and transport disabled.
That correctness validation is excluded from benchmark costs.

## Verification and remaining gaps

All **2,679 full and 20 focused tests pass**. A separately reproduced audit covers
all 512 two-variable clause sets with all seeds, 3,304 three-variable clause sets
of at most three clauses with two seeds, and 256 sparse signed mixtures with
duplicates, tautologies and some units. Budgets 0, 2 and 20,000 give **27,414 exact
proof-and-diagnostic comparisons**: 11,689 SAT, 5,576 UNSAT and 10,149 unknown.
Independent truth tables verify each completed answer and 3,971 learned-clause
occurrences. Across the audit, events include 19,394 watch moves, 4,533 stale candidates,
3,426 duplicate-learning encounters and six nonchronological jumps. These are
cumulative events across related queries, not distinct inputs. The mixtures
also receive **1,024 exact composed-trace comparisons** after source deletion or
shared-variable addition; the entire retained proof prefix survives each output.

One initial focused fixture failed to exercise a satisfied-watch skip because
canonical unit order moved the watch first. The failure log is preserved; a
forcing implication fixes the fixture. Search code did not change in response.
The existing SQLite ResourceWarnings remain preserved in the full-suite log.

Validation preserves **252 manifests, 84,641 artifact entries, 1,372 scientific
sources and 91 earlier manuscript proofs**. Five scientific files and one proof
are added. Resume `experiments/results/cnf-watched-learning/checkpoint.json`,
key `watched_learning`. Earlier coverage panels, policy losses and counterexamples
keep their separate denominators and records.

The next coverage gap is the thirteen capped edited targets. A separately frozen
expansion experiment can test whether saved propagation work buys more checked
answers. Remaining obligations include fresh external transfer, proof retention
cost, alternative supports after source deletion, efficient structural recognition
and unrestricted expansion. Faster processing of the same finite traces is not
a broader tractable SAT family or an end-to-end amortization result.
