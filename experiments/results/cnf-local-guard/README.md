# Target-local guard discovery: acquisition and fresh controls

The fixed policy shares baseline propagation, ranks unforced variables by
original binary-clause incidence, and tests false then true for at most four
variables. A checked terminal or premise trace is retained for publication.
The remaining child still uses general solving. No additional core-bank scan
is needed at the local discovery stage; inherited preparation remains charged.

Six historical arms restore exact saved prefixes. Four fresh workers run two
reversed-order baseline/local pairs on 192 new neighbouring inputs, excluding
inherited query and native roots. No tests, profiling or builds overlap production.

| Measure | Baseline | Local |
| --- | ---: | ---: |
| Historical native rows | 23 | 19 |
| Fresh native rows | 250 | 250 |
| Fresh native bytes added | 495,299 | 490,681 |
| Fresh expansion calls | 19 | 12 |
| Explicit trace publications | 0 | 7 |
| Probe + premise/child propagation visits | 6,634 | 7,797 |
| Mean complete worker seconds | 17.337 | 20.173 |

The lower expansion counter does not establish lower total work. Fresh case
144 grows 3 -> 11 rows and accounts for ten of twelve local child expansions.
The baseline hits a previously stored negative dependency; the conditioned path
does not. Cases 167/190 improve 8/4 -> 2/2 because the child unit-refutes. These
stream prefixes can diverge, so per-query differences are not equal-state causal
comparisons. `cost-attribution.json` preserves the relevant dependency roots.
Next, test child admission before guard publication at identical prefixes and
on another excluded set; retain useful nonterminal cases as rejection controls.
The apparent eight-row posthoc recovery is not a measured stream improvement.

The 21,801-key union preserves all 21,528 prior payloads and adds 273 keys with
no alternate payloads. It retains 390 new composed records, 438 prior composed
records, 2,957 ordinary decisions and six projections. All 1,069 tests and 12
focused tests pass; the full suite retains 44 existing SQLite ResourceWarnings,
and focused tests emit none. Independent reconstruction, cold replay, all four
frontier lineages and prior structural authorities pass. The 206-page manuscript
builds cleanly and preserves 64 proof blocks.

`protocol.json` binds 473 runtime sources; `validation.json` adds two posthoc
analysis/preservation sources for a final ledger of 475. All 469 earlier sources,
5,057 earlier artifacts and 87 earlier manifests are unchanged. The new archive
is 69,226,496 database bytes / 5,050,133 compressed bytes. Each trial remains saved.
The four union ready/pending counts are 131/39, 139/68, 83/93 and 83/120.

Reproduce from the repository root into a fresh output directory:

```sh
python3 experiments/compare_cnf_local_guard.py /tmp/cnf-local-reproduction
python3 experiments/validate_cnf_local_guard.py /tmp/cnf-local-reproduction
python3 experiments/analyze_cnf_local_guard.py /tmp/cnf-local-reproduction
python3 experiments/finalize_cnf_local_guard.py /tmp/cnf-local-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_local_guard solver.test_cnf_assumption_guard
```

The generated neighbours come from three templates; this is not a representative
sample of arbitrary SAT. Discovery has a bounded number of propagation calls,
not a bound on remaining child search. Two timing pairs give no stable general
runtime or peak-memory claim. No new Lean or unrestricted-SAT theorem is added.

New manifest: **58 artifacts**. Next preservation audit: **5115 artifacts / 88 manifests**.
