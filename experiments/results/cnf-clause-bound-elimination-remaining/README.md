# Clause-count elimination: remaining

Runtime checkpoint `2c422ff`; execution order: baseline, clause_bound.
Baseline is the preceding joint clause/literal non-growth rule. The candidate
adds complete-pair clause-count-only admission after the earlier terminal
proposal is null, with the same candidate/pair caps. It does not add the
retained-clause subsumption fallback.

These are the 59 final leaves of the previous subsumption run, with empty
history and conditioning depth zero. They are selected failures, not holdouts.

| Measurement | Previous bounded policy | Clause-count fallback |
| --- | ---: | ---: |
| Closures | 0 | 1 |
| Selected open leaves | 59 | 58 |
| Selected open literals | 26,181 | 26,126 |
| Total query seconds | 2.84076 | 4.09001 |
| Discovery seconds | 0.57939 | 1.77437 |
| Ordinary solver seconds | 2.25892 | 2.30488 |
| Complete database bytes | 17,518,592 | 19,488,768 |
| Added bytes above prefix | 17,489,920 | 19,460,096 |
| Pattern nodes | 59 | 168 |
| Cold audit seconds | 1.06376 | 1.61667 |
| Warm combined seconds | 0.03556 | 0.04362 |
| Four-case peak Python bytes | 1,919,676 | 2,719,945 |

Gained case indices: [8]. Lost case indices: [].
The candidate acquires 95 new elimination edges, including
63 SAT and 32 UNSAT endpoint pairs. Both endpoints are
independently solved; every SAT child model is lifted and checked against the
source. This additional diagnostic costs 5.35454 seconds. Earlier
rule edges receive full cold proof checking; their expensive endpoint-solving
diagnostic is not repeated here.

New edges increasing literal count: 95.
Maximum consecutive elimination-chain length: 7; maximum
new target width: 6. These chains stop at non-elimination nodes; they
are not the whole discovery graph. All observed target and chain formula sizes
satisfy the stated conditional bounds.

Additional fallback candidate tests: 5,810;
clause-growth rejections: 5,627; opposing
pairs visited: 70,865. Counts include failed and unselected
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
python3 experiments/compare_cnf_clause_bound_elimination.py --suite remaining --output /tmp/clause-bound-remaining-new
```

Run timed comparisons without concurrent tests, builds, profiling or archive
analysis. Earlier measurements, failed candidates and all proof history remain
preserved.
