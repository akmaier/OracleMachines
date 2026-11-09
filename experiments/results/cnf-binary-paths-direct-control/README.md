# Checked binary-path reduction: direct-control

**Optional coverage method; not promoted as the default.** See the [proof, literature and resource account](../../../research/binary-paths.md).

| Measure | Early direct-only control | Transitive binary paths |
| --- | ---: | ---: |
| Structural closures | 60 | 63 |
| Discovery seconds | 6.369999 | 6.083622 |
| Total seconds | 9.781318 | 9.139234 |
| Ordinary solver seconds | 3.400898 | 3.046844 |
| Selected unresolved leaves | 54 | 53 |
| Their literal occurrences | 13,351 | 12,971 |
| SQLite bytes | 39,358,464 | 39,919,616 |
| Pattern nodes | 1,774 | 1,832 |
| Cold seconds | 3.884056 | 3.994329 |
| Warm seconds | 0.028240 | 0.027467 |

Gains: **[6, 13, 85]**. Losses: **[]**.

Mode `baseline` in this report is BinaryDirectInventory. Both modes apply early deletion, but the control uses only direct binary subset witnesses. Its 60 closures versus 63 distinguish transitive gains from scheduling direct subsumption earlier.

The same arbitrary-conditioning/probe/learning caps apply. Binary-path search adds a separately charged limit of 64 roots per residual. It retains every binary reason and checks source-linked proof edges and exact children. Empty proposals are inconclusive, not exclusions of a tractable class.

All 461 Python tests and the full Lean build/axiom audit pass (4,148 declarations / 1,988 theorem declarations). Cold checks verify every node, source binding and solver certificate without changing database bytes. Warm replay inserts no rows. Six-case (full) or four-case traced allocations exclude native SQLite, RSS and full-corpus peak. All prior archives remain retained.

Total charges discovery, independent checks, normalization, serialization, SQLite, ordinary solving and model lifts. Loading, summary walks, hashing and compression are excluded; initialization, cold and warm are separate. These are single synthetic comparisons, not significance estimates or general performance bounds. The frontier transitive archive is reproduced byte-for-byte in the reversed-order direct-only control.

`report.json` contains cases, per-query metrics and fingerprints. `mechanisms.json` counts direct-versus-transitive deletion and actual serialized proof costs; its independent-path encoding is documented there. Shared proof nodes can cost more bytes than separate paths. Full graph/source retention remains the main space increase.

```sh
python3 experiments/compare_cnf_binary_direct.py --suite frontier --output /tmp/binary-paths-direct-control
python3 experiments/analyze_cnf_binary_paths.py /tmp/binary-paths-direct-control
```
