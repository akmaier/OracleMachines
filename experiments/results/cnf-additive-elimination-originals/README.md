# Additive elimination: originals

Runtime checkpoint `5894bd8`; execution order: baseline, add_one, add_two.

The same 83 original prior misses, using the paid 417,370,112-byte prepared prefix and conditioning depth two. This is a selected subset, not a new full-corpus run.

Baseline is clause-count-only admission. The candidates permit at most one or two additional clauses only after earlier rules fail, with complete independent checking and the same 64 candidate/pair caps. The optional policies do not change the ordinary solver.

| Measurement | Baseline | +1 clause | +2 clauses |
| --- | ---: | ---: | ---: |
| Closures | 31 | 31 | 31 |
| Selected open leaves | 57 | 57 | 57 |
| Selected open literals | 25,488 | 25,752 | 26,260 |
| Query seconds | 121.61751 | 142.26465 | 163.21184 |
| Discovery seconds | 119.49592 | 140.20864 | 161.23142 |
| Ordinary solver seconds | 2.10829 | 2.04206 | 1.96745 |
| Complete acquisition database bytes | 674,234,368 | 700,178,432 | 734,814,208 |
| Added acquisition bytes above prefix | 256,864,256 | 282,808,320 | 317,444,096 |
| Cold acquisition audit seconds | 109.97163 | 107.04672 | 123.12474 |
| Warm combined seconds | 0.09908 | 0.11030 | 0.08754 |
| Four-case peak Python bytes | 16,028,492 | 16,717,304 | 17,353,939 |
| New additive edges | 0 | 1,021 | 2,530 |
| New SAT / UNSAT edge pairs | 0 / 0 | 568 / 453 | 1390 / 1140 |
| Endpoint diagnostic seconds | 2.36093 | 111.11488 | 273.64557 |
| Separate reference database bytes | 16,384 | 532,144,128 | 1,236,189,184 |
| Reference cold verification seconds | 0.00031 | 35.32182 | 94.64726 |
| Reference verified nodes | 0 | 68,039 | 155,448 |
| Maximum consecutive elimination steps | 13 | 13 | 13 |
| Maximum new target width | 0 | 8 | 9 |
| Additional candidates tested | 0 | 103,577 | 155,645 |
| Additional growth rejections | 0 | 102,219 | 151,131 |

add_one: gained case indices []; lost case indices [].
add_two: gained case indices []; lost case indices [].

All new edges have independently solved endpoints and checked SAT model restoration. The reference residual databases and endpoint JSONL records preserve this work, with hashes in report.json. All reference nodes pass cold proof checking without expansion or byte changes. Reference storage is additional evidence cost, excluded from the acquisition database row above. Earlier-rule edges receive full cold proof checking; their previous endpoint-solving diagnostics are not repeated.

Every paid-prefix row survives. Acquisition replay changes no bytes and warm queries acquire no new nodes. Ordinary answers, profiles and search counters match across modes; the validator additionally compares the retained ordinary residual tables. Structural closure is not a SAT verdict or a measured reduction in SAT search.

Query time charges discovery, checking, persistence, ordinary solving and successful root lifts. Restore, clone, opening, frontier walks, compression, cold replay, endpoint diagnostics and four-case allocation are separately recorded. Allocation excludes native SQLite, RSS and full-history peak. These are single ordered comparisons on selected failures or reused controls, not universal performance ratios.

See the [mechanism and limitations](../../../research/additive-elimination.md) and [validation](../cnf-additive-elimination-validation/README.md). Prior results and failed candidates remain preserved.

```sh
python3 experiments/compare_cnf_additive_elimination.py --suite originals --output /tmp/additive-originals-new
```

Run timings without concurrent tests, builds, profiling or archive analysis.
