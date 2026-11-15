# Complete admission and the remaining transfer frontier

The optional `CompleteAdmissionInventory` closes the acquisition-accounting gap
without changing the inference policy, certificate schema or archived source
files. Both `_discover` and the fused-conditioning profile entrance charge a
canonical (policy, depth, CNF) state before recognition. A transient restricted
formula is charged even if only its simplified descendant is stored. A separate
recording guard rejects an unadmitted write. Cold verification remains available
at zero acquisition budget.

This caps distinct acquisition states per batch. It does not cap time, literal
work, repeated visits, canonicalization, lookup, independent checking or I/O.
Those costs remain explicit. The accounting guarantee covers the two acquisition
entrances of this fixed implementation; callers must not bypass them by directly
invoking the internal profile planner. The recording guard alone would detect a
missed admission too late to bound prior computation.

## Matched observations

The separately frozen experiment reuses the previous 42 inputs and early-family
control. Each stream starts with empty ordinary history; two repetitions reverse
arm order. The only policy difference is the admission gate. Results are not a
new holdout, a SAT decision benchmark or a uniform efficiency theorem.

| Per-query allowance | Ledger | Total admissions | New patterns | Off-ledger patterns | Fresh probes | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 32 | Legacy | 100 | 107 | 18 | 503 | 41/42 |
| 32 | Complete | 120 | 107 | 0 | 463 | 41/42 |
| 4096 | Legacy | 401 | 443 | 42 | 2710 | 41/42 |
| 4096 | Complete | 479 | 443 | 0 | 2710 | 41/42 |

At **both allowances the entire stored pattern graph is byte-identical** between
ledgers, not just equal in coverage. At allowance 32, the complete gate avoids
**40 fresh probes** that the old gate performs before a later interruption. The
largest input drops from 272 to 232 probes; its 21 persisted records are identical.
The stream reduces probe attempts by 7.95%. Its mean operation time is
**0.37586 -> 0.36206 s**, plus **0.00140 -> 0.00129 s** setup. Two repetitions are
insufficient for a strong timing claim. No memory reduction is observed: both
32-state histories occupy **1,351,680 SQLite bytes**, or **60,047 gzip bytes**.
These files omit the old per-query SQLite journal, so their absolute size and
elapsed time must not be compared directly with the previous study. The present
operation timer includes before/after row audits and proof persistence; JSON
report serialization, compression and full cold replay remain separate costs.

At allowance 4096, mean operations are **2.76625 / 2.75668 s** (legacy/complete),
with **7,200,768 SQLite / 386,822 gzip bytes**. The last input is no longer capped,
yet remains structurally unresolved. It consumes **391 distinct acquisition
states**, stores **357**, and runs **2,479 fresh probes**. Of its 58 admissions
through fused profiles, 24 are persisted and **34 remain transient**. Since the
run returns normally, these 34 are not interrupted ancestors. This is the cost
that a persisted-row count alone misses.

## Exact remaining interaction

`selected-frontier.json` binds the original root to its selected unresolved
frontier. The original input is **48 variables / 204 clauses / 612 literals**;
its selected residual is **38 / 165 / 502**, with maximum clause width four.
The residual remains connected and is at conditioning depth zero. Its
simplification is at a fixed point, bounded probing is clear, and the current
projection is inapplicable. Horn, dual-Horn, 2-CNF, zero/one-valid, matching,
explicit-affine and affine-conflict recognition are excluded by the current
checks; single-parity recognition remains unresolved under its width policy.
These are recognition outcomes, not a statement that no other tractable
representation exists.

The selected unclosed traversal has 13 nodes: six elimination, three binary-path,
two conditioning, one probe and one unresolved node. The saved history also
contains alternatives; it must not be replaced by this selected fragment.
Increasing the acquisition allowance alone therefore does not close the gap.
Next investigate exact conditioning or reusable interface structure at this
38-variable interaction, retaining its original-source ancestry and both
necessary branch obligations.

## Persistent restarts

Four cold-open batches of 32 complete admissions start from a copy of the saved
family-control archive. They preserve all **107 inherited rows** and add **79**,
ending at 186 records. The 128 admissions visit 95 distinct states: **33 admissions
repeat work**. They perform **842 probes**, take **1.41322 s** including opening
and row audits, and still stop at the cap. A matched empty-history four-batch run
stores 78 records on 89 distinct states, with **39 repeated admissions / 874
probes / 1.20849 s**. Prepared history saves some work but is slower in this small
comparison; it already contains 21 records acquired on this same last input, so
this is a continuation comparison, not cross-input generalization. Each batch
archive and the unsuccessful four-batch outcome are preserved. The 4096-state
archive is a more complete planner checkpoint and should be preferred for the
next structural investigation.

A second promising gap is retaining checked intermediate profiles of interrupted
ancestors or transient restrictions. Completed child records already survive;
profile work before an unfinished parent does not necessarily do so. Any new
profile cache must bind source, depth and policy, independently verify evidence,
and charge validation and storage. The repeated-admission counts locate a
candidate; they do not yet establish that caching all profiles is profitable.

## Validation and resumption

All **323 relevant tests** pass, including exhaustive compatibility on all 512
normalized two-variable clause subsets, both zero-budget gates, transient-state
accounting, saved-row preservation and zero-acquisition cold replay. Independent
reconstruction checks **16 archives** and every stored node, and binds 344 query
records to their original sources. All 2,906 inherited artifacts, 46 manifests
and 162 prior source fingerprints remain unchanged. The manuscript keeps its
64 existing proof blocks; no new Lean theorem is claimed.

Use `experiments/results/cnf-complete-admission/complete4096-0/report.json` and its
bound archive to restore the complete current-policy history. It contains 443
patterns across the full stream. Use `selected-frontier.json` to identify the
38-variable residual, keeping the original root context. The earlier 83-case
checkpoint remains complete and is not superseded by this new stream.

```sh
python3 -m unittest solver.test_cnf_complete_admission
python3 experiments/validate_cnf_complete_admission.py experiments/results/cnf-complete-admission
# Use a new output directory; the producer refuses to overwrite old evidence.
python3 experiments/compare_cnf_complete_admission.py /tmp/cnf-complete-admission-new-run
```

Reconstruction writes its report into the specified directory; copy the result
bundle before rerunning validation if preserving the original file hashes.
Peak RAM, broader distributions, efficient profile caching and unrestricted SAT
coverage remain open.
