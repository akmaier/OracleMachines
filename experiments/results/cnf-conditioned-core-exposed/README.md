# Conditioned-core acquisition with direct-premise controls

Fifteen historical exact-prefix arms compare baseline solving, checked cofactor
acquisition and direct native acquisition of the identical strengthened premise,
in both missing-clause orders. See [the analysis](../../../research/conditioned-core.md).

All six paired orders have identical child roots, proofs and expansion counts.
Separate cofactor acquisition adds a row in case 43 and bytes in every pair.
Case 43's direct reverse plan uses seven rows versus ten baseline; forward gives
the lowest native bytes. Case 172 is an ordinary split on an existing clause,
with a forward-order regression. Both case-70 orders regress. Trying all twelve
candidates costs 94 expansions against 23 baseline. No stable runtime, peak-memory,
fresh-coverage or cheap-selector guarantee follows.

The extended acquisition gate reuses existing checked native cofactors, or
permits fresh acquisition when unit propagation refutes the cofactor or exposes
two-CNF. It reuses the checked unit trace during native publication. The earlier
raw-two-CNF gate correctly rejected case 43; that attempt and its baseline are
retained in `../cnf-conditioned-core/`, with exact baseline parity verified here.

`checkpoint.json` retains all 21,482 old payloads and contains 21,525 native keys.
Six alternative certificates remain in the arm deltas. Ordinary catalogs remain
separate from composed/projection schemas: 2,957 ordinary decisions, 414 previous
composed records, 15 new composed records and six projections pass cold replay.
The four frontiers and structural authorities remain unchanged. All 1,057 tests
and 17 focused tests pass; the full suite retains 44 old SQLite ResourceWarnings.

`assumption-reduction-probe.json` checks single-assumption unit conflicts for
43 + [-230], 172 + [-40], 70 + [-40] without publication or search. All three
remaining native children are absent at their original prefixes. Acquisition,
composition and net savings for those narrower guards are the next experiment.

Reproduce from the repository root with a new output directory:

```sh
python3 experiments/run_cnf_exposed_core.py compare /tmp/cnf-conditioned-reproduction
python3 experiments/run_cnf_exposed_core.py validate /tmp/cnf-conditioned-reproduction
python3 experiments/analyze_cnf_conditioned_core.py /tmp/cnf-conditioned-reproduction
python3 experiments/probe_cnf_assumption_reduction.py /tmp/cnf-conditioned-reproduction
python3 experiments/finalize_cnf_conditioned_core.py /tmp/cnf-conditioned-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_conditioned_core solver.test_cnf_exposed_core solver.test_cnf_partition_screen
```

Production binds 459 sources (451 preserved plus eight new runtime/test files).
The final ledger adds three posthoc tools for 462. Prior 4,916 artifacts across
85 manifests are unchanged. Full source/parent hashes, costs, checked traces,
all regressions, validation logs and the 64 unchanged manuscript proof blocks
are recorded. The rebuilt paper has 205 pages and no overfull or undefined warnings.

New manifest: **92 artifacts** across complete and rejected runs. Next preservation audit: **5008 artifacts / 86 manifests**.
