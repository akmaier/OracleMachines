# Bounded elimination on the 83 previously unresolved original sources

Runtime checkpoint `e7a806b`. All three modes begin with the same already-acquired
417,370,112-byte PolarityHorn archive, conditioning depth two and the previous
probe/learning limits. The query list is precisely the 83 misses from the earlier
prepared 1,497-input comparison. This study evaluates whole-input recomposition;
it is not an extrapolation from the 99-leaf diagnostic or a new full-corpus run.

| Acquisition measurement | Baseline | Pure-only | Bounded |
| --- | ---: | ---: | ---: |
| Structural closures | 0 | 11 | 29 |
| Open original sources | 83 | 72 | 54 |
| Selected open leaves | 99 | 84 | 59 |
| Selected open literals | 31,203 | 28,653 | 26,205 |
| Discovery seconds | 62.92410 | 70.27491 | 78.27921 |
| Total query seconds | 64.76503 | 71.86221 | 80.09857 |
| Complete database bytes | 605,675,520 | 627,138,560 | 621,146,112 |
| Pattern nodes including prior history | 34,398 | 35,365 | 34,514 |
| Cold audit seconds | 73.18420 | 77.08544 | 79.28780 |
| Four-source peak Python bytes | 20,284,653 | 21,098,539 | 16,819,577 |

The bounded candidate retains every pure-only closure and adds 18. Its 29
closed sources include 28 SAT and one UNSAT instance, independently decided on
the original CNFs. All open sources remain explicitly unresolved. Source profiles,
answers and ordinary solver counters agree between modes. The old stored rows
remain unchanged. All three complete compressed archives are preserved, including
the prior paid prefix; the report separately charges restore, clone and opening.

The candidate acquires 2,822 elimination nodes, but total pattern-node count rises
only 116 over baseline because the resulting plans also contain fewer other nodes.
This does not establish cheaper total acquisition: query time and archive bytes
are higher. Discovery tests 167,129 candidates and rejects 156,757 for growth,
visiting 1,457,523 opposing pairs. Those failed attempts are a concrete next
cost to profile. The pure-only control is important because 11 closures need no
mixed-polarity resolution at all.

`report.json` retains every query, preserved-row counts, complete cold audits,
separate source/target model checks and the same four-source allocation sample.
The independent edge diagnostic is additional validation, not production query
time. `summary.json` retains aggregate counters. The ordinary decision solver
continues to solve original CNFs; no change to its search algorithm is claimed.

Every mode preserves all 22,071 old pattern nodes, 1,465 old source rows and
21,838 old residual rows. All cold audits leave bytes unchanged. Additional
independent endpoint/model checks cover 1,728 pure-only edges (1433 SAT / 295
UNSAT) and 2,822 bounded edges (2057 SAT / 765 UNSAT). These diagnostics cost
177.42878 and 688.09686 seconds respectively, outside query acquisition.

The [structure analysis](../cnf-variable-elimination-probe/structure-reuse.json)
finds only one repeated elimination target among 2,822 edges. Of the 59 remaining
selected leaves, 58 have pair-bounded candidates but no non-growing step under
the current rule. In 10, retained-clause subsumption of new resolvents would
permit a non-growing candidate. That follow-up is a diagnostic opportunity,
not yet an integrated policy or an additional structural closure.

```sh
python3 experiments/compare_cnf_variable_elimination.py --suite originals --output /tmp/bve-originals-new
```

This is one ordered comparison on selected prior failures. Historical group names
such as `holdout3` and `fresh3` identify old generation cohorts, not a new untouched
holdout or semantic SAT classes. Fresh/adversarial policy comparisons, alternative
orders and a full-corpus rerun remain open. Sampled Python allocation excludes
native SQLite, RSS and full-history peak. No uniform polynomial expansion or
Python-to-Lean refinement follows. See [the full resource account](../../../research/variable-elimination.md).
