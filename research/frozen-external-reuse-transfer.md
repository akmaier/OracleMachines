# Frozen external transfer of selective resolution reuse

The previous larger-budget comparison completed sixteen exposed edits of refuted
parents. This checkpoint tests its fixed policy on new external parents, removes
the parent-outcome filter and accounts separately for acquiring those parents.

## Frozen sample and composition

`selection.json` binds all 1,384 scientific sources before downloading selected
members. The four SATLIB archives are uf125-538, uuf125-538, uf150-645 and uuf150-645.
Zero-based member indices 60 and 80 in (basename, full-name) order give eight
originals. Their publisher bytes, archive/member hashes, parsed DIMACS and
provenance are retained. No original has an exact normalized match in the six
specified earlier panels or among the new originals. The additional target
census is in `target-overlaps.json`. Exact inequality is not semantic independence.

Acquire each parent with the unchanged watched learner at 20,000 contexts.
Delete the canonical original clause starting its first stored derivation, or
canonical clause zero if no derivation exists. The paired edit additionally adds
`[smallest_original_variable, maximum_original_variable+101]` and the negative
unit on the fresh variable. Include both edits for every parent, irrespective of
SAT, UNSAT or unknown. The rule, fallbacks and two reversed target process orders
were fixed before observing parent results. The eight external parents are the
selection units; the sixteen targets are related edits. No statistical representativeness or generalization across
distributions is claimed.

Both target modes use the same target-only proposal and 8,000-context watched
search. Reuse checks the parent, filters recorded derivations by surviving
premises, activates all retained clauses, then substitutes their derivations
into a certificate checked against the target alone. SAT witnesses are not
inherited. Unknown retains consequences without granting an answer. This uses
previous exact-composition results; it adds no new structural recognizer or theorem.

## Coverage and resource cost

| Quantity | Parent acquisition | Fresh targets | Reused targets |
| --- | ---: | ---: | ---: |
| Checked answers | 8/8 | 9/16 | 16/16 |
| Entered contexts | 80,118 | 90,992 | 48,329 |
| Complete seconds | 79.67498 | 62.70943 | 115.99874 |
| Warm reload/check seconds | 2.25949 | 2.62639 | 5.17449 |
| Two reload/check rounds seconds | 4.41419 | 4.87807 | 10.59269 |
| Three compressions seconds | 2.74057 | 3.03846 | 6.39941 |
| Proof JSON bytes | 57,955,525 | 64,358,286 | 132,091,258 |
| Acquisition including checks, seconds | 68.10386 | 49.76647 | 88.82619 |
| Explicit checking seconds | 1.96408 | 2.17715 | 4.57421 |
| Writes seconds | 0.18329 | 0.20036 | 0.40905 |
| Combined gzip bytes | 2,070,763 | 2,299,823 | 4,957,007 |
| Peak RSS bytes | 244,137,984 | 240,107,520 | 483,672,064 |

| Parent outcome | Fresh target outcomes | Reused target outcomes |
| --- | --- | --- |
| SAT | 3 SAT, 1 UNSAT, 4 unknown | 5 SAT, 3 UNSAT |
| UNSAT | 5 UNSAT, 3 unknown | 8 UNSAT |

Reuse-only targets: **t008, t009, t010, t011, t012, t013, t014**. Fresh-only targets:
**none**. Both modes answer **9** targets.
Of the reuse-only answers, **4 arise from SAT parents**. Thus completed
SAT searches can supply useful retained consequences; the target still requires
its own model or refutation. Their bookkeeping union answers **16/16**, leaving **0**
unknowns; it is not a measured dispatcher. Per-target results, remaining
interaction components and proof-survival counts are retained in `analysis.json`.
All sixteen targets remain connected, with 125–151 variables. Across the paired
edits, **64,382** derivation occurrences survive and **9,136** are
discarded by the recorded-premise filter; these counts repeat parent records
across edits and are not independent discoveries or minimum support sizes.
Reference answers stay separate. A negative Z3 answer alone supplies no project
refutation; each reported project answer has a checked model or empty-clause proof.

Reused-target cost changes by **+84.98%** relative to fresh
search. Adding the single measured parent acquisition gives
**195.67372 seconds** for acquiring eight parents and
running one sixteen-target reuse workflow. This is an observed aggregate, not a
break-even estimate or equal-answer speedup. Uncompressed certificate files, all three compressed payloads and historical
append-only evidence add storage beyond the quoted combined gzip sizes.

Complete timings include raw reads/hash checks, required parent reads/checks,
proposal, transport, augmentation, search, proof substitution, explicit checks,
writes, three compressions, warm replay and two reload rounds. Target figures
average two reversed fresh-process orders; parent acquisition was measured once.
Download, edit preparation, imports/startup, report encoding and independent
audits are additional. The rounds named cold in inherited report fields create
fresh objects within the same worker and do not flush OS caches. Separate new
workers replay each policy with search/transport disabled as a correctness check.
Context caps count iterations, not equal work or wall time; RSS is observational.

## Validation and limits

All 2,697 full tests and eight focused tests pass. The independent audit runs
all 512 two-variable clause sets, 3,304 three-variable sets of at most three
clauses, and 64 sparse signed mixtures with duplicate clauses and tautologies.
A two-context parent cap yields 2,629 SAT, 867 UNSAT and
384 unknown parents; both fixed edits and target modes give
15,520 truth-checked outcomes on 7,760 targets. The audit reproduces exactly.
This small audit happens to retain no derivations after the chosen deletions;
it does not independently establish nonempty knowledge reuse. The unchanged
kernel's earlier truth audits remain preserved, while explicit transitive premise
sets check every retained path on the new external targets. All measured parent
and target proofs, diagnostics, counters and repeated target certificates
reproduce; all three fresh-worker replays pass. All 254 prior manifests,
84,935 artifact entries, 1,381 earlier scientific sources, 92 proof blocks and
three published snapshots remain intact. Three scientific files are added.

This experiment supplies finite transfer evidence and explicit failures/costs.
It does not establish polynomial preprocessing, cheap recognition, a compact
complete decomposition or efficient unrestricted SAT. Next inspect the actual
fresh/reuse differences and retained proof cost, then test justified support
selection or dispatch on a separately frozen sample. Raising a cap alone does
not resolve those obligations.
