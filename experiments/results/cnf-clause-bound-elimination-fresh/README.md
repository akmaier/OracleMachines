# Clause-count elimination: fresh

Runtime checkpoint `2c422ff`; execution order: baseline, clause_bound.
Baseline is the preceding joint clause/literal non-growth rule. The candidate
adds complete-pair clause-count-only admission after the earlier terminal
proposal is null, with the same candidate/pair caps. It does not add the
retained-clause subsumption fallback.

These 96 controls reuse the published `fresh_cases()` generator and seed
202611091650: random, renamed, clause-edited and disjoint-Horn-mixture inputs with
base sizes 12, 24 and 40 variables; mixtures append seven fresh variables. They are a separate comparison set, not an untouched
holdout. This run uses the paid 417,370,112-byte prepared prefix and depth two.

| Measurement | Previous bounded policy | Clause-count fallback |
| --- | ---: | ---: |
| Closures | 88 | 88 |
| Selected open leaves | 8 | 8 |
| Selected open literals | 2,713 | 2,682 |
| Total query seconds | 8.90872 | 10.48245 |
| Discovery seconds | 7.59693 | 9.14316 |
| Ordinary solver seconds | 1.30613 | 1.33354 |
| Complete database bytes | 453,582,848 | 456,785,920 |
| Added bytes above prefix | 36,212,736 | 39,415,808 |
| Pattern nodes | 24,160 | 24,318 |
| Cold audit seconds | 49.42162 | 49.38030 |
| Warm combined seconds | 0.04974 | 0.04974 |
| Four-case peak Python bytes | 625,585 | 628,417 |

Gained case indices: []. Lost case indices: [].
The candidate acquires 130 new elimination edges, including
111 SAT and 19 UNSAT endpoint pairs. Both endpoints are
independently solved; every SAT child model is lifted and checked against the
source. This additional diagnostic costs 5.07637 seconds. Earlier
rule edges receive full cold proof checking; their expensive endpoint-solving
diagnostic is not repeated here.

New edges increasing literal count: 130.
Maximum consecutive elimination-chain length: 8; maximum
new target width: 6. These chains stop at non-elimination nodes; they
are not the whole discovery graph. All observed target and chain formula sizes
satisfy the stated conditional bounds.

Additional fallback candidate tests: 11,112;
clause-growth rejections: 10,913; opposing
pairs visited: 132,328. Counts include failed and unselected
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
python3 experiments/compare_cnf_clause_bound_elimination.py --suite fresh --output /tmp/clause-bound-fresh-new
```

Run timed comparisons without concurrent tests, builds, profiling or archive
analysis. Earlier measurements, failed candidates and all proof history remain
preserved.
