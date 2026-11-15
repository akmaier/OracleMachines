# Checked coverage of the full historical corpus

2026-11-15. The combined query now checks **1,497/1,497 historical inputs**,
including **985/985 outside the two-variable exhaustive block**, without new
recognition states or fresh SAT solving. This replaces the earlier arithmetic
inference with an explicit source- and configuration-bound replay. It is a
regression result on development data, not a new holdout result or a partition
that efficiently decides every CNF.

## Exact composition

The independently supplied claim fixes the ordered source formulas, two named
policies, their options and an exhaustive disjoint partition of input indices.
The original retained policy contributes **1,414 roots / 8,159 proof steps**; the
expanded policy contributes **83 roots / 4,822 steps**. Every root is recomputed
from its source under its own configuration and every selected premise is checked.
There is no implicit conversion between policies or trust in historical closure
flags. Empty conjunctions and contradictions are both structurally covered; the
certificate does not equate coverage with satisfiability.

The new consumer rejects changed claims, missing or duplicated indices, foreign
policy proofs, omitted roots or components, missing or corrupted rows, conflicting
exact-key payloads and unused table rows. Seven focused tests exercise these
cases. All **306 relevant tests** pass. Existing inference rules and proof blocks
are unchanged; no new Lean theorem is claimed.

The producer first checks the historical successful plans under their original
validators. It then captures only the rows consumed by positive replay, together
with the five current evidence lists and two bridges. Both archives remain
unchanged. Identical rows are stored once: **20 duplicated row occurrences** are
removed from the union. The consumer rechecks the proof in a disposable database;
it does not import a trusted verification cache.

## Costs of prepared proof replay

| Measurement | Result |
| --- | ---: |
| Full-history process times | 47.90732 / 45.06322 s |
| Standalone bundle process times | 11.25230 / 11.20584 s |
| Mean full-history replay | 46.48527 s |
| Mean standalone replay | 11.22907 s |
| Observed process-time reduction | 75.84% |
| Bundle compressed / uncompressed JSON | 11,271,594 / 146,344,695 bytes |
| Temporary bundle SQLite database | 146,747,392 bytes |
| Original retained / expanded databases | 629,276,672 / 786,116,608 bytes |
| Pattern rows needed for the union | 13,023 |
| Other consumed table rows | 112 |

Two reversed-order comparisons run in fresh processes. Bundle consumers run
outside the repository and receive only the bundle, the independent claim and
checker code. Both arms forbid recognition and reference-solver acquisition.
The operating-system caches are shared. Full mode restores historical state and
then replays the same positive proofs; bundle mode only certifies the requested
positive coverage. It cannot replace the full discovery catalog or a full archive
audit. Full mode processes the retained policy first; standalone mode uses the
serialized policy order. These are reproducibility samples, not a confidence
interval or a solver-runtime comparison.

Producer costs are separate: original restoration **0.59256 s**, expanded
restoration **35.86218 s**, historical plan expansion/checking **10.34703 s**,
row capture **3.96033 + 6.60811 s**, and serialization/compression of both the
bundle and separate proof-parts artifact **8.35912 s**. The complete study takes
**182.57847 s**, including four consumer processes. Expanded restoration permits
checked materialization without reporting whether cache or fallback was used.
The prior acquisition cost and retained history remain liabilities. The new
bundle adds persistent bytes; it does not delete old data or reduce expansion
state. Peak RAM is unmeasured, and the two original database sizes are not summed
into a simultaneous resident-memory claim.

The saved study contains **14 manifested artifacts / 15,892,168 bytes**, excluding
the manifest itself. This includes the independent claim, separate control proofs,
four worker logs, diagnostics and validation. All **2,837 earlier artifacts across
44 manifests** and **151 earlier frozen sources** remain unchanged. The updated
manuscript builds to 173 pages with all 64 existing proof blocks preserved and
without undefined references or overfull boxes. The new source ledger binds
155 files; the next audit inherits 2,851 artifacts across 45 manifests.

## Where larger reuse is present

The earlier successful set has **1,414 source occurrences but 1,113 distinct
canonical roots**. After collapsing the 301 duplicate root occurrences, its proof
has **154 shared steps**, including **67 nonterminal steps**: 42 edge reductions,
14 conditioning steps and eleven component decompositions. The largest shared
source is **18 variables / 22 clauses / 48 literals**, used by three distinct roots
from the subsumption-edit cases **1454, 1457 and 1460**. Additional shared reductions
reach sixteen variables in other edit families. Owners are propagated through the
checked proof and independently compared with root-by-root traversal.

This is broader evidence than the previous audit of only the 83 misses, where
shared steps have at most two variables. Between the two policy proofs there are
**20 exact shared step identities**, all identical family steps with at most
**three variables**. Larger reuse in the old edit families has therefore not been
shown to transfer into the previously uncovered set. Repeated group labels can
refer to the same canonical roots; the diagnostic retains group and input-index
context without counting those copies as different root owners.

These are selected-proof graph counts, not measured acquisition savings. They
exclude alternatives, internal forcing traces, reference-SAT proofs and semantic
or unrestricted renaming searches. Nested shared nodes cannot be added as
independent savings.

## Next experiment

Freeze a new-input generator, policy and acquisition budget before evaluating
prepared versus empty history. Include edits around the shared **18/22/48** core,
variable renamings, connected mixtures, changes that invalidate a retained premise,
and genuinely new formulas. Charge recognition and transport as well as fresh
forcing-trace acquisition, checking, persistence and cold replay. Measure larger
nonterminal hits separately from tiny terminals and duplicate roots. Keep misses
and regressions instead of tuning the frozen policy on their answers.

For expansion, continue to restore
`experiments.continue_cnf_case1196_discovery.restore_checkpoint` from its existing
report. Its selection is null and all 83 development sources are complete. The
new bundle is **positive-proof-only**, not an expansion checkpoint. Finite corpus
coverage and cheaper replay establish no uniform polynomial bound for arbitrary
SAT.
