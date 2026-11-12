# Additive elimination: fresh

Runtime checkpoint `5894bd8`; execution order: baseline, add_one, add_two.

The same 96 previously used controls: random CNFs, signed renamings, clause replacement edits and disjoint Horn mixtures at base sizes 12/24/40. Mixtures append seven variables. The historical fresh_cases name does not make these untouched holdouts. The paid 417,370,112-byte prefix and depth two are shared.

Baseline is clause-count-only admission. The candidates permit at most one or two additional clauses only after earlier rules fail, with complete independent checking and the same 64 candidate/pair caps. The optional policies do not change the ordinary solver.

| Measurement | Baseline | +1 clause | +2 clauses |
| --- | ---: | ---: | ---: |
| Closures | 88 | 88 | 88 |
| Selected open leaves | 8 | 8 | 8 |
| Selected open literals | 2,682 | 2,695 | 2,717 |
| Query seconds | 10.45184 | 12.74294 | 14.87718 |
| Discovery seconds | 9.11523 | 11.43879 | 13.57874 |
| Ordinary solver seconds | 1.33052 | 1.29776 | 1.29259 |
| Complete acquisition database bytes | 456,785,920 | 461,209,600 | 465,776,640 |
| Added acquisition bytes above prefix | 39,415,808 | 43,839,488 | 48,406,528 |
| Cold acquisition audit seconds | 49.91774 | 51.00370 | 51.25086 |
| Warm combined seconds | 0.05089 | 0.05083 | 0.05063 |
| Four-case peak Python bytes | 628,609 | 632,506 | 632,258 |
| New additive edges | 0 | 175 | 345 |
| New SAT / UNSAT edge pairs | 0 / 0 | 151 / 24 | 295 / 50 |
| Endpoint diagnostic seconds | 1.00211 | 7.80309 | 13.77993 |
| Separate reference database bytes | 16,384 | 34,488,320 | 64,126,976 |
| Reference cold verification seconds | 0.00027 | 1.53321 | 3.11741 |
| Reference verified nodes | 0 | 6,106 | 11,243 |
| Maximum consecutive elimination steps | 8 | 8 | 8 |
| Maximum new target width | 0 | 5 | 6 |
| Additional candidates tested | 0 | 12,241 | 17,400 |
| Additional growth rejections | 0 | 11,991 | 16,790 |

add_one: gained case indices []; lost case indices [].
add_two: gained case indices []; lost case indices [].

All new edges have independently solved endpoints and checked SAT model restoration. The reference residual databases and endpoint JSONL records preserve this work, with hashes in report.json. All reference nodes pass cold proof checking without expansion or byte changes. Reference storage is additional evidence cost, excluded from the acquisition database row above. Earlier-rule edges receive full cold proof checking; their previous endpoint-solving diagnostics are not repeated.

Every paid-prefix row survives. Acquisition replay changes no bytes and warm queries acquire no new nodes. Ordinary answers, profiles and search counters match across modes; the validator additionally compares the retained ordinary residual tables. Structural closure is not a SAT verdict or a measured reduction in SAT search.

Query time charges discovery, checking, persistence, ordinary solving and successful root lifts. Restore, clone, opening, frontier walks, compression, cold replay, endpoint diagnostics and four-case allocation are separately recorded. Allocation excludes native SQLite, RSS and full-history peak. These are single ordered comparisons on selected failures or reused controls, not universal performance ratios.

See the [mechanism and limitations](../../../research/additive-elimination.md) and [validation](../cnf-additive-elimination-validation/README.md). Prior results and failed candidates remain preserved.

```sh
python3 experiments/compare_cnf_additive_elimination.py --suite fresh --output /tmp/additive-fresh-new
```

Run timings without concurrent tests, builds, profiling or archive analysis.
