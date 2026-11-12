# Additive elimination: remaining

Runtime checkpoint `5894bd8`; execution order: baseline, add_one, add_two.

The 57 final leaves from the preceding clause-count original-source run, starting with empty history at conditioning depth zero.

Baseline is clause-count-only admission. The candidates permit at most one or two additional clauses only after earlier rules fail, with complete independent checking and the same 64 candidate/pair caps. The optional policies do not change the ordinary solver.

| Measurement | Baseline | +1 clause | +2 clauses |
| --- | ---: | ---: | ---: |
| Closures | 0 | 0 | 0 |
| Selected open leaves | 57 | 57 | 57 |
| Selected open literals | 25,488 | 25,838 | 26,604 |
| Query seconds | 3.42106 | 3.76690 | 4.88712 |
| Discovery seconds | 0.72722 | 1.31486 | 2.29019 |
| Ordinary solver seconds | 2.69013 | 2.44327 | 2.58372 |
| Complete acquisition database bytes | 17,551,360 | 18,509,824 | 19,894,272 |
| Added acquisition bytes above prefix | 17,522,688 | 18,481,152 | 19,865,600 |
| Cold acquisition audit seconds | 1.14729 | 1.42513 | 2.03743 |
| Warm combined seconds | 0.03730 | 0.04364 | 0.04778 |
| Four-case peak Python bytes | 3,804,255 | 4,067,475 | 4,321,252 |
| New additive edges | 0 | 43 | 105 |
| New SAT / UNSAT edge pairs | 0 / 0 | 27 / 16 | 68 / 37 |
| Endpoint diagnostic seconds | 0.00540 | 3.30338 | 7.44911 |
| Separate reference database bytes | 16,384 | 18,247,680 | 39,776,256 |
| Reference cold verification seconds | 0.00022 | 1.04177 | 2.19721 |
| Reference verified nodes | 0 | 2,564 | 5,517 |
| Maximum consecutive elimination steps | 0 | 3 | 5 |
| Maximum new target width | 0 | 6 | 6 |
| Additional candidates tested | 0 | 3,581 | 5,668 |
| Additional growth rejections | 0 | 3,524 | 5,461 |

add_one: gained case indices []; lost case indices [].
add_two: gained case indices []; lost case indices [].

All new edges have independently solved endpoints and checked SAT model restoration. The reference residual databases and endpoint JSONL records preserve this work, with hashes in report.json. All reference nodes pass cold proof checking without expansion or byte changes. Reference storage is additional evidence cost, excluded from the acquisition database row above. Earlier-rule edges receive full cold proof checking; their previous endpoint-solving diagnostics are not repeated.

Every paid-prefix row survives. Acquisition replay changes no bytes and warm queries acquire no new nodes. Ordinary answers, profiles and search counters match across modes; the validator additionally compares the retained ordinary residual tables. Structural closure is not a SAT verdict or a measured reduction in SAT search.

Query time charges discovery, checking, persistence, ordinary solving and successful root lifts. Restore, clone, opening, frontier walks, compression, cold replay, endpoint diagnostics and four-case allocation are separately recorded. Allocation excludes native SQLite, RSS and full-history peak. These are single ordered comparisons on selected failures or reused controls, not universal performance ratios.

See the [mechanism and limitations](../../../research/additive-elimination.md) and [validation](../cnf-additive-elimination-validation/README.md). Prior results and failed candidates remain preserved.

```sh
python3 experiments/compare_cnf_additive_elimination.py --suite remaining --output /tmp/additive-remaining-new
```

Run timings without concurrent tests, builds, profiling or archive analysis.
