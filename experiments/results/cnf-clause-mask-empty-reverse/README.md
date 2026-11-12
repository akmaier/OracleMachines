# Clause-mask empty-history control: reversed execution order

Runtime checkpoint `c7914b5`, the same 96 control inputs, mask then scan. This
checks whether the first comparison's result merely follows execution order.

| Measurement | Scan | Mask |
| --- | ---: | ---: |
| Discovery seconds | 6.17950 | 6.38115 |
| Total query seconds | 7.31352 | 7.57542 |
| Cold audit seconds | 3.50472 | 3.54492 |
| Warm combined seconds | 0.04757 | 0.04953 |
| Four-case peak Python bytes | 615,819 | 871,299 |
| Structural closures | 88 | 88 |
| Final database bytes | 33,460,224 | 33,460,224 |

Operation counts exactly match the [forward comparison](../cnf-clause-mask-empty/README.md).
Literal work is 55.10% lower, but total time is 3.58% higher and sampled peak Python
memory is about 41% higher. All answers and evidence agree; all four databases
across both orders are byte-identical after decompression. Each cold audit verifies
every stored node, source and residual and leaves the database unchanged.

```sh
python3 experiments/compare_cnf_clause_mask.py --suite empty --reverse --output /tmp/clause-mask-empty-reverse-new
```

Both complete archives and per-query records remain available. These are two
ordered comparisons of previously published synthetic inputs, not a statistical
study or independent holdout. Sampled Python memory excludes native SQLite, RSS
and full-history peak. See [joint validation](../cnf-clause-mask-pilot/validation.json)
and [the cost account](../../../research/clause-mask-reuse.md). The candidate stays
optional and disabled; no new full prepared-corpus result is claimed.
