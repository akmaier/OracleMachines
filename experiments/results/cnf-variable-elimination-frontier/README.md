# Bounded elimination on the 99 selected unresolved leaves

Runtime checkpoint `e7a806b`. Three modes start from identical empty history,
with conditioning depth zero and the previous probe/learning limits. The 99
inputs are saved unresolved leaves from 83 original inputs, not an independent
test set. Baseline uses `PreparedProbeInventory`; pure-only and bounded use
`VariableEliminationInventory` with opposing-pair caps zero and 64.

| Measurement | Baseline | Pure-only | Bounded |
| --- | ---: | ---: | ---: |
| Structural closures | 0 | 14 | 37 |
| Selected open leaves | 99 | 85 | 62 |
| Selected open literals | 31,203 | 29,164 | 27,130 |
| Discovery seconds | 0.67469 | 1.27667 | 2.41501 |
| Total query seconds | 3.21234 | 3.83297 | 4.97015 |
| Cold audit seconds | 1.23433 | 1.51291 | 2.09154 |
| Warm combined seconds | 0.04554 | 0.05084 | 0.05671 |
| Database bytes | 20,000,768 | 22,454,272 | 26,185,728 |
| Four-case peak Python bytes | 718,814 | 1,344,096 | 1,923,674 |

Bounded elimination retains all 14 pure-only closures and adds 23. Its 37
closed leaves comprise 35 SAT and 2 UNSAT inputs, independently decided on the
original CNFs. The unchanged ordinary solver's counters agree in all modes;
no reduction in its original-input search is claimed. Every mode's complete
archive, per-input outcomes and phase counters are preserved.

Both endpoints of all 163 pure-only and 379 bounded elimination edges are
independently solved. SAT child models lift to checked source models. These
additional diagnostics cost 1.89829 and 6.33214 seconds respectively, outside
acquisition. All three cold audits leave database bytes unchanged. Source and
pattern rows are never deleted. The bounded inventory stores 587 pattern nodes
versus 99 baseline nodes; smaller formulas do not give smaller proof histories.

The Python allocation samples the same first four queries and excludes native
SQLite, RSS and full-history peak. Acquisition includes discovery, checking,
ordinary solving, source/model lifts and commits. Initialization, summary walks,
compression, preservation checking and audit are separately reported. This is
one ordered synthetic comparison, not a general runtime ratio or proof of
whole-input closure. The whole-input study is recorded separately.

```sh
python3 experiments/compare_cnf_variable_elimination.py --suite frontier --output /tmp/bve-frontier-new
```

Run timed comparisons without concurrent tests, builds or archive analysis.
See [the exact rule and costs](../../../research/variable-elimination.md).
