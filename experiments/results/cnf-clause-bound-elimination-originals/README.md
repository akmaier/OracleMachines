# Clause-count elimination: originals

Runtime checkpoint `2c422ff`; execution order: baseline, clause_bound.
Baseline is the preceding joint clause/literal non-growth rule. The candidate
adds complete-pair clause-count-only admission after the earlier terminal
proposal is null, with the same candidate/pair caps. It does not add the
retained-clause subsumption fallback.

These are the same 83 original prior misses, starting from the paid
417,370,112-byte prepared prefix at conditioning depth two. This is not a
new run on the full corpus.

| Measurement | Previous bounded policy | Clause-count fallback |
| --- | ---: | ---: |
| Closures | 29 | 31 |
| Selected open leaves | 59 | 57 |
| Selected open literals | 26,205 | 25,488 |
| Total query seconds | 78.06321 | 113.63899 |
| Discovery seconds | 76.41349 | 111.88597 |
| Ordinary solver seconds | 1.63815 | 1.74111 |
| Complete database bytes | 621,146,112 | 674,234,368 |
| Added bytes above prefix | 203,776,000 | 256,864,256 |
| Pattern nodes | 34,514 | 37,234 |
| Cold audit seconds | 79.31544 | 93.78991 |
| Warm combined seconds | 0.07550 | 0.07829 |
| Four-case peak Python bytes | 16,820,521 | 16,028,812 |

Gained case indices: [12, 21]. Lost case indices: [].
The candidate acquires 2,504 new elimination edges, including
1,493 SAT and 1,011 UNSAT endpoint pairs. Both endpoints are
independently solved; every SAT child model is lifted and checked against the
source. This additional diagnostic costs 961.43125 seconds. Earlier
rule edges receive full cold proof checking; their expensive endpoint-solving
diagnostic is not repeated here.

New edges increasing literal count: 2,504.
Maximum consecutive elimination-chain length: 13; maximum
new target width: 8. These chains stop at non-elimination nodes; they
are not the whole discovery graph. All observed target and chain formula sizes
satisfy the stated conditional bounds.

Additional fallback candidate tests: 166,437;
clause-growth rejections: 162,187; opposing
pairs visited: 2,091,250. Counts include failed and unselected
alternatives. The original-input solver answers, profiles and search counters
match exactly; its retained residual table is checked separately for equality.

`report.json` retains every query, counter, complete archive hash, old-row
preservation result, cold audit, chain diagnostic and allocation sample.
`summary.json` aggregates outcomes. Query time charges discovery, checking,
persistence, ordinary solving and successful root lifts. Restore, clone, opening,
selected-frontier walks, compression, cold audit and endpoint/model diagnostics
are outside query time. Allocation samples the same first four cases and
excludes native SQLite, RSS and full-history peak.

Every prior row survives and cold replay preserves database bytes. The candidate
remains optional. These controls establish neither default-policy promotion,
an efficient arbitrary-CNF partition nor a general timing ratio. See the
[mechanism and limits](../../../research/clause-bound-elimination.md) and
[validation record](../cnf-clause-bound-elimination-validation/README.md).

```sh
python3 experiments/compare_cnf_clause_bound_elimination.py --suite originals --output /tmp/clause-bound-originals-new
```

Run timed comparisons without concurrent tests, builds, profiling or archive
analysis. Earlier measurements, failed candidates and all proof history remain
preserved.
