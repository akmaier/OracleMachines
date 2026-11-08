# Conditioning diagnostic and development pilot

The baseline cProfile run uses the 48 `random3` sources retained by the previous
simplification study, with unit simplification, depth two, four candidates and
in-memory SQLite. `baseline-profile.json` preserves all measured function rows.
Its source checkpoint is `1496aee`, before the candidate-selection hook refactor.
Cumulative times overlap and must not be added; instrumented times are not the
unprofiled benchmark. Normalization costs 1.70 s cumulatively, whole profiles
2.83 s, and unit propagation 0.57 s. The complete checker includes several of
those operations and costs 3.43 s. Repeated residual acquisition/checking is the
main target, rather than optimizing propagation alone on these cases.

`report.json` retains exact sources, all operation metrics and this development
pilot. No ordinary solver, cold replay or gzip time is included in its elapsed
inventory totals. The later full comparison adds those charges and fresh inputs.

| Policy | Candidate cap | Closed / 48 | Inventory seconds | Pattern nodes |
| --- | ---: | ---: | ---: | ---: |
| Frequency | 4 | 10 | 2.12711 | 2,491 |
| Frequency | 8 | 14 | 7.02229 | 7,473 |
| Balanced shortest clauses | 4 | 13 | 2.71308 | 3,162 |
| Balanced shortest clauses | 8 | 15 | 8.22121 | 9,059 |

The four-candidate rule closes old cases 777, 790 and 819 without losing any old
closure in this subset, but takes longer and stores more distinct residuals.
Doubling its cap gains only two more closures at much greater cost. The rule
was frozen before generating the subsequent holdout; no coefficients were fitted.
The regressions remain evidence against making it the default policy.

The score uses positive/negative occurrence counts in shortest clauses, ordered
by their product, then sum, then total occurrences, then variable ID. Its link
to known MOMS and unit-propagation heuristic work is discussed in the full
comparison. It changes candidate order only; both restrictions remain checked.
The pilot fingerprints record the implementation used. Earlier archives and
all raw solver answers remain unchanged.
