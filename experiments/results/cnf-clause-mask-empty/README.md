# Clause-mask empty-history control: scan then mask

Runtime checkpoint `c7914b5`, 96 previously published synthetic controls, scan
then mask. Both modes use the accounted ordinary residual solver. The mask
changes independent residual reconstruction only; all proof obligations remain.

| Measurement | Scan | Mask |
| --- | ---: | ---: |
| Discovery seconds | 6.21594 | 6.38743 |
| Total query seconds | 7.37185 | 7.56226 |
| Cold audit seconds | 3.52632 | 3.54729 |
| Warm combined seconds | 0.04675 | 0.04791 |
| Four-case peak Python bytes | 615,971 | 871,147 |
| Structural closures | 88 | 88 |
| Final database bytes | 33,460,224 | 33,460,224 |

The mask gets 1,014,169 hits at 1,529,672 clause positions. Preparation costs
1,402,257 literal visits and possible-overlap scans cost 471,454, versus 4,173,407
old scan visits. The 55.10% reduction does not offset other work: query time is
2.58% higher. This is one ordered comparison, not a stable general ratio.

Both complete archives, per-input records and phase counters are preserved.
Answers, roots, profiles, summaries, solver counters, all evidence tables and raw
database bytes match. The cold audits check 1,988 pattern nodes, 96 sources and
1,287 residuals per mode without changing bytes. Opening, preservation checking
and compression are separately charged. Python tracing samples the first four
queries and excludes native SQLite, process RSS and full-history peak.

```sh
python3 experiments/compare_cnf_clause_mask.py --suite empty --output /tmp/clause-mask-empty-new
```

The [reverse-order comparison](../cnf-clause-mask-empty-reverse/README.md) also
regresses. [Joint validation](../cnf-clause-mask-pilot/validation.json) checks all
four archives and fingerprints. The optional cache is not enabled by default;
there is no new SAT coverage or full prepared-corpus result.
