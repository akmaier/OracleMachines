# Restricted-child admission at equal saved states

This experiment compares native baseline, unconditional local discovery and an
optional admission gate. The gate preserves cheap syntactic families and admits
a guard only when its restricted child has a checked native answer or unit
refutation. Rejected proposals publish nothing; ordinary solving remains fallback.
Accepted premise/child traces are reused through the unchanged native verifier.

| Case | Baseline rows | Local rows | Admitted rows |
| --- | ---: | ---: | ---: |
| Historical 43 | 10 | 7 | 10 |
| Historical 70 | 4 | 5 | 4 |
| Historical 172 | 9 | 7 | 9 |
| Prior fresh 144 | 3 | 11 | 3 |
| Prior fresh 167 | 8 | 2 | 2 |
| Prior fresh 190 | 4 | 2 | 2 |

The gate repairs the 144 regression and retains the two unit-conflict wins,
but rejects useful 43/172 guards. Propagation for the three prior fresh controls
is 4,821 / 5,984 / 5,285; historical propagation is 4,501 / 5,763 / 8,666.
These are selected exact-prefix controls, not a new excluded stream or a stable
runtime/memory result. Every arm starts at identical native rows and an empty
checked-node cache, then replays the same previously accepted guards. Prefix
reconstruction is charged separately; shared bank preparation stays in the bound
original trials. Per-arm cold times check the selected composed result only.
Full inherited validation is separately retained in reconstruction.json.

An admitted guard publishes at most two native rows and needs no general child
expansion. The bound excludes preparation, proof checking, storage size, source
sidecars and fallback. All four rejected residuals remain unknown and outside
cheap syntactic families after unit propagation. Beneficial case 172 has 112 literals
and regressing case 70 has 111: an absolute smaller-residual threshold cannot distinguish
them. Next, measure another excluded stream and test structural admission or reuse
of failed-probe traces without treating posthoc selection as a deployed gain.

The native archive is reused byte-for-byte: 21,801 keys, no new native payloads.
Eighteen new composed records retain all arms alongside 828 prior composed records,
2,957 ordinary decisions and six projections. All 1,076 tests and 19 focused tests
pass, including 512 guarded mixtures under two representations. The full suite
retains 44 existing SQLite ResourceWarnings; focused tests emit none. The 206-page
paper builds without warnings and preserves all 64 proof blocks.

The protocol binds 479 runtime sources; validation adds one posthoc source for
480 total. All 475 prior sources / 5,115 artifacts / 88 manifests are unchanged.
All four frontier lineages and structural authorities pass. The posthoc analysis
first failed a key assertion because native keys include a format prefix; the
corrected analysis uses the native token function. Its failure log is retained;
measured policy sources and results were unaffected.

Reproduce from the repository root into a new output directory:

```sh
python3 experiments/compare_cnf_child_admission.py /tmp/cnf-child-reproduction
python3 experiments/validate_cnf_child_admission.py /tmp/cnf-child-reproduction
python3 experiments/analyze_cnf_child_admission.py /tmp/cnf-child-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_child_admission solver.test_cnf_local_guard solver.test_cnf_assumption_guard
```

No new Lean theorem, optimal-cost result or unrestricted-SAT efficiency claim.

New manifest: **71 artifacts**. Next preservation audit: **5186 artifacts / 89 manifests**. Final source ledger: **480**.
