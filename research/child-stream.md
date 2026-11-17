# Fresh child admission saves rows but misses a known residual

The unchanged child-admission gate now has a matched comparison on 192 new
query roots. It reduces new native rows by eight, but increases propagation,
serialized records and observed complete time. One SAT query exposes a concrete
reuse gap: propagation already reduces it to a cached binary clause before the
policy tries four unnecessary premises.

## Fixed protocol

The generator selects 64 double-deletion neighbours from each of three existing
templates, excluding every earlier ordinary/composed query root and native root.
It excludes 1,088 previous query roots per template. These are new roots within
three old families, not an independent arbitrary-SAT distribution. Catalogue
selection costs 2.339 seconds separately.

Two reversed-order pairs run in separate fresh processes: baseline/admitted,
then admitted/baseline. The frozen stream worker is reused through scoped
callbacks for inherited records, evaluation and summaries. The four-variable
ranking, child gate, native solver, ordinary reuse and near-guard preparation
are unchanged. Known targets bypass optional discovery. No tests, profiles or
builds overlap production. All eighteen earlier equal-state controls are retained.

## Measured complete costs

Both policies answer 101 SAT and 91 UNSAT queries. Warm replay acquires no new
rows. Six unknown targets reach admission: three unit-conflict children, two
already terminal targets, and one query with no successful proposal.

| Measure | Baseline | Admitted |
| --- | ---: | ---: |
| New native rows | 229 | 221 |
| Added native bytes | 460,398 | 448,420 |
| Expansion calls | 17 | 1 |
| Explicit trace publications | 0 | 8 |
| Probe + premise/child propagation visits | 5,590 | 11,343 |
| Mean query/warm sidecar bytes | 5,458,957 | 5,591,904.5 |
| Mean query seconds | 1.535 | 1.974 |
| Mean full cold replay seconds | 15.985 | 21.513 |
| Mean complete worker seconds | 28.229 | 31.695 |

The row reduction is 3.49%, and added native bytes decline 2.60%. Expansion calls
alone exaggerate the saving: eight explicit trace publications replace work
that the expansion counter would otherwise include. Propagation rises 102.92%
and sidecars grow 2.44%. Complete time is higher in both measured pairs by 4.676
and 2.257 seconds. Two pairs provide no stable general timing result. Mean process
peak RSS is 555 / 606 MB; this is not a live-state memory bound. SQLite bytes are
70,328,320 / 70,316,032 and compressed bytes 5,100,581 / 5,099,949, so the reduction
in retained archive size is small despite lower added logical bytes.

The changed queries are:

| Case in this new catalogue | Baseline / admitted rows | Outcome |
| --- | ---: | --- |
| 35 | 6 / 2 | Unit-refuted premise and child |
| 50 | 1 / 1 | Existing target propagation already refutes it |
| 76 | 4 / 2 | Unit-refuted premise and child |
| 85 | 1 / 1 | Four failed probes, then SAT fallback |
| 161 | 1 / 1 | Existing target propagation already refutes it |
| 169 | 4 / 2 | Unit-refuted premise and child |

These are contributions to matched streams whose prefixes may diverge, not
isolated equal-state causal comparisons. The earlier eighteen controls remain
the separate authority for the selected same-prefix comparisons.

## Highest-priority expansion gap: check the propagated residual before probing

Case 85 accounts for the only remaining child expansion. Baseline propagation
fixes 23 variables and leaves one clause over two variables. Its canonical root
is `cnf-residual-v1:[[-2,-1]]`. That exact positive result is already available
at this query's post-preparation prefix. The read-only diagnostic
checks the native result (80 payload bytes) and reconstructs a model satisfying
the restricted target using the retained forced assignments. This is exact
reuse of a checked answer, not a similarity-based inference.

The current gate checks cheap families before propagation. Local discovery
then records the forced prefix but still ranks the two unforced variables and
tries all four polarities. The discovery/probe stage uses 4,795 propagation
literal visits; ordinary fallback repeats 955 visits. Baseline needs 955.
The extra 4,795 visits account for most of the 5,753-visit stream increase.

Next, expose the normalized residual immediately after baseline propagation,
check its native answer and cheap family, and reuse the retained unit trace when
publishing the target result. Preserve source-coordinate reconstruction and
exact root binding. Test the case-85 prefix, no-hit and nonterminal controls,
renaming/polarity changes, then another excluded stream. Charge normalization,
lookup, certificate checking and publication; do not count a posthoc avoided-work
estimate as a measured implementation gain. This diagnostic has not changed the
policy or produced a new timing result.

Full cold replay still dominates complete time. Shared validation and compact
source references remain the larger supporting total-cost targets; the extra
composed sources can outweigh native-row savings. Broader nonterminal admission
and dependency transport remain open, including the earlier useful 43/172
controls that the strict gate rejects. Neither a complete partition of CNFs nor
a uniformly efficient unrestricted SAT solver follows from these measurements.

## Preservation

Resume `experiments/results/cnf-child-stream/checkpoint.json`: 22,036 native
keys, preserving all 21,801 prior payloads and adding 235 keys without alternative
payloads. The union retains both policies, rather than only the selected gate.
Its database is 70,344,704 bytes, compressed to 5,103,740 bytes. All four trial
archives, including the runtime and serialization regressions, remain retained.

There are 384 new composed records alongside 846 previous composed records,
2,957 ordinary decisions and six projections. All 1,076 tests and 19 focused tests
pass; independent prefix, exclusion, answer, witness, warm and cold checks pass.
The full suite retains 44 existing SQLite ResourceWarnings; focused tests emit
none. Earlier 480 sources / 5,186 artifacts / 89 manifests are unchanged.
Ready/pending retained-bank counts are 132/38, 140/67, 84/92 and 84/119. These
availability counts do not enlarge the separate structural authority: 2,614
patterns / 259 pairs, original 17/24 and supplemental 24/24 remain unchanged.
No new Lean, compact-closure or unrestricted-SAT result is claimed.
