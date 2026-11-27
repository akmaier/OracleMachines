# Selective width expansion and reuse of a projection prefix

Checkpoint: 27 November 2026. Selective width-nine elimination after two checked
pair rounds raises structural coverage **177/182 to 180/182**, adding three
original-source SAT certificates without losing a feedback verdict. It costs
**2.78% more than feedback** and **54.91% more than fresh solving**. Prefix reuse
avoids projection work but gives no reliable total-runtime improvement. Defaults
stay unchanged; the common fallback already answers every query.

The next strongest measured cost opportunity is **repeated verification**:
39.51% of bucket-verification table probes in one cold pass repeat an exact local
operator. That is a census of potential reuse, not a measured speedup. Two roots
remain structurally unresolved; increasing their width to ten still certifies
none.

## Exact continuation and its scope

`cnf_bucket_continuation.py` checks an unresolved width-eight bucket prefix,
reconstructs its factors and active indices, and continues at width nine. It
preserves the original factor numbering, full projection tables and reconstruction
choices. The old prefix is immutable. The original reserved-work allowance remains
262,144 for the **complete prefix plus suffix**; expansion does not reset the
budget. Clauses beyond the expanded width are rejected before table materialization.

Every projection existentially eliminates its pivot from all incident factors.
Replaying the old prefix and appending verified projections therefore preserves
the exact relation on the remaining active variables. Reverse traversal of all
old and new choices reconstructs a full source witness. A zero active factor
proves UNSAT. Support removal requires equal cofactors, while witness choices
retain the complete pre-reduction boundary. Unfinished work remains unresolved.

`cnf_selective_width_buckets.py` applies this expansion only to unresolved
depth-zero leaves after one or two checked pair batches. Each next source and
its inverse maps are reconstructed from the checked terminal. The widened model
lifts through every earlier preparation and pair-consequence layer, then through
the original conditioning graph. It checks every SAT edge and the final root
model. No index or factor state is reused across changed CNFs.

The certificate stores only the widening suffix, referring to the exact prefix
already retained in its containing terminal (or the original bucket when no pair
clause was learned). Cold replay independently checks the complete combined
program. It performs no discovery. This saves repeated **storage** of the prefix;
it does not silently bypass its verification.

At depth two, there are at most four original leaves and four widening attempts.
One-round policies retain at most 1,024 pair attempts and 128 clauses per root;
two-round policies retain 2,048/256. Earlier preparation, ordering, materialization,
support checking, validation and unsuccessful attempts remain additional charged
work. These finite bounds do not establish unrestricted efficiency or a new
tractable SAT family.

## Frozen controls and coverage

The comparison retains all 160 preceding queries and freezes 18 new unique
constructions plus four exact normalized repeats before evaluation. Families
include random three-CNFs, hidden-pair/deleted-conflict controls and parity prisms.
There are **114 SAT and 68 UNSAT queries**. No new normalized source duplicates
the preceding panel, although families recur. Labels are audit-only. Both old
controls already cover every new query; the gains concern exposed prior cases.
This is synthetic evidence, not representative external SAT coverage.

| Policy | Previous queries | New unique | New repeats | Total |
| --- | ---: | ---: | ---: | ---: |
| Single pair round | 151/160 | 18/18 | 4/4 | 173/182 |
| Feedback, two rounds | 155/160 | 18/18 | 4/4 | 177/182 |
| One round + selective width | 154/160 | 18/18 | 4/4 | 176/182 |
| Two rounds + selective width | 158/160 | 18/18 | 4/4 | 180/182 |

Both widening policies add `d-d-k14`, `d-d-k15`, `d-f03`. However, one-round
widening misses four feedback verdicts: `d-d-d-j07`, `d-d-k16`, `d-d-k17`, `d-f05`.
It does not dominate feedback. Two-round widening retains all feedback verdicts.
All old-control certificates for the preceding panel match their saved versions.

The one-round widening comparison has **restart** and **resume** acquisition
variants. Restart invokes the unchanged bucket implementation and must reproduce
the earlier prefix. Resume validates and reconstructs that prefix, projecting only
the suffix. Both persist the same suffix representation and execute the same final
checking schedule on successful discovery. Their certificates are identical modulo
the outer mode field.

A preliminary run initially omitted a successful-discovery internal check in the
resume path. It was stopped and excluded before accepting timings. Seven completed
reports, incomplete artifacts, original source snapshots and relocation bindings
are preserved under `preliminary-check-schedule/` and `preliminary-retention.json`.
The accepted comparison below uses the corrected schedule and unchanged panel.

## Complete costs and the failed runtime hypothesis

Six cyclic process orders start empty with the same fallback. Complete time
includes input, discovery with internal checks, explicit checks, evidence/database
writes, warm/cold replay and compression. Startup, final report metadata, labels,
historical acquisition, lineage audits and post-hoc profiles are additional. Two
independent native readers audit fallback archives; JSON replay uses two passes
of the same checker.

| Policy | Complete seconds | Compressed SQLite + JSON bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: |
| Fresh | 9.06609 | 2,193,009 | 281,706,496 |
| Single pair round | 13.16906 | 792,451 | 141,737,984 |
| Feedback | 13.66497 | 712,790 | 133,234,688 |
| One round + width, restart | 13.74160 | 684,474 | 136,232,960 |
| One round + width, resume | 13.74914 | 684,851 | 136,577,024 |
| Two rounds + width, resume | 14.04422 | 607,765 | 127,041,536 |

Two-round widening regresses **2.78% versus feedback in all six pairs** and
**54.91% versus fresh**. One-round widening regresses **4.40% versus single** in
all six pairs and averages **0.62% above feedback**, with mixed signs. Resume
averages **0.055% slower than restart**, with three favorable and three unfavorable
pairs. None establishes a runtime win for prefix reuse. RSS values are process
observations, not memory bounds.

One-round widening reuses **104 steps**, avoiding **3,960 projected rows** and
**34,024 reserved table probes**. It adds exactly **3,960 verified rows and 34,024
verification table probes** to validate that prefix. The avoided projection work
does not eliminate its checking cost. There are 20 widening attempts and 71 suffix
steps; five leaves become SAT, but only three add root verdicts. Retained suffix
step lists use **10,293 compact bytes**, versus **19,463** if each also duplicated
its old prefix. This counterfactual byte comparison is not an unimplemented
format's runtime measurement.

Two-round widening makes 15 attempts, reuses 78 prefix steps and adds 56 suffix
steps. Three leaves become SAT; twelve remain unresolved, including nine beneath
already-SAT roots. The outer graph remains **509 nodes, 202 splits and 2,133 bucket
steps**, with 46 shared targets and 41 distinct-raw merges, all constant. There is
no new nonconstant merging across leaves. Feedback and two-round widening both
attempt 16,218 pairs and retain 1,706 clauses.

Compared with feedback, two-round JSON grows **573,019 to 577,137 bytes**, while
fallback records fall **300 to 61**. The smaller combined package is not a smaller
structural certificate. Restart/resume compressed-byte differences come from their
mode strings. Two-round diagnostics add 1,068,073 bytes.

## Gaps ranked by current evidence

1. **Reuse verified operators during checking.** Two-round discovery including
   internal checks costs **5.15454 s** and cold replay **4.17227 s**, the largest
   phases. One full cold pass contains 3,279 operator occurrences but only 1,325
   distinct exact local descriptions. Repeated operators account for **288,484 of
   730,144 verification table probes (39.51%)** and 32,930 of 87,474 verified rows.
   Within-query repetition accounts for 107,408 probes. Separately, among 158
   distinct normalized sources, first local occurrences matching an earlier source
   account for **100,948 of 634,824 probes (15.90%)**. There are also 24 repeated
   queries. Of the repeated rows, 26,668 have nonconstant outputs; that aggregate
   does not isolate nonconstant transfer across SAT categories. Exact proposed
   key/result descriptions serialize to 127,839 bytes, not a cache-RAM bound.

   **Next experiment:** verify an exact operator once within a checking pass, then
   reuse that established result while still checking each occurrence's input
   factors, coordinate map, result and complete choice table. Charge first-use
   verification, key construction, lookup, memory and invalidation. The earlier
   [operator proposal cache](semantic-bucket-support.md) rechecked every proposal;
   this is a different potential saving. The census implements no such cache and
   does not imply a 39.51% runtime reduction.

2. **Resolve the remaining coupled factor boundary.** Roots `d-d-d-j06` and
   `d-d-k09` remain structurally unknown, both SAT by the independent oracle.
   Their three frontiers have 71/86/87 active factors over 19/30/29 active variables
   and require width ten. A separately checked width-ten continuation certifies
   none: the first next requires width twelve, the other two width eleven. All
   stop on width rather than the reserved-work cap. Investigate factor descriptions,
   separators or conditioning with exact recomposition before more uniform table
   growth. These are Boolean factor relations after projection, not unchanged CNFs.
   The widths describe the current factorization and order, not lower bounds on
   optimal decompositions.

3. **Establish broader transfer.** New controls are already covered by the old
   policies; these gains do not demonstrate improved coverage of a new external
   distribution. Exact source programs and local operator descriptions do not
   recognize general variable/sign permutations or semantic equivalence. External
   workloads, efficient recognition across categories and unrestricted expansion
   bounds remain open. Neither a finite panel nor an explicit unresolved cell
   supplies an efficient solution of arbitrary SAT.

## Verification and continuation

Seventeen new tests cover exhaustive two-variable formulas, seeded small inputs,
exact restart/resume agreement, unchanged prefixes, total work-budget accounting,
changed source and suffix rejection, leaf admission, signed model transport and
cold replay with discovery disabled. All **30 focused and 2,385 full tests pass**.
The initial full run, concurrent with certificate audits, hit the unchanged
100 ms write-lock timeout test before its expected SQLite exception. That test
and the full suite pass in isolation without changed deadlines or assertions.
The initial failure log is retained; scheduling pressure is a plausible cause,
not a proved diagnosis. Existing unclosed-database ResourceWarnings are also
retained in the full-suite logs.

The independent semantic audit checks **31,088 source assignments and 28,600
active-factor assignments over 180 CNFs**, including 90 reused prefix steps and
132 suffix steps. It checks exact existential relations and all 1,410 feasible
active-model reconstructions. There are 36 SAT and ten UNSAT continuations, with
134 unresolved. The initial dense-only audit had no nonempty reused prefix and is
retained separately; the final audit adds private-variable tails and refutation
controls. The operator census exactly matches both measured cold-verification
counters after accounting for the two passes.

All **236 previous manifests, 60,847 artifact entries, 1,294 scientific sources
and 78 proof blocks** are preserved. Six new scientific sources and one restricted
correctness proof are added. Resume
`experiments/results/cnf-selective-width-buckets/checkpoint.json`, key
`selective_width_buckets`. `analysis.json` retains costs and coverage losses;
`remaining-profile.json` records the exact factor frontier;
`checker-reuse-profile.json` records the separately charged reuse opportunity.
Final test and manuscript results are recorded in `checks.json`.
