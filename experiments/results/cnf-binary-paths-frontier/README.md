# Checked binary-path reduction: frontier

**Optional coverage method; not promoted as the default.** See the [proof, literature and resource account](../../../research/binary-paths.md).

| Measure | Retained baseline | Transitive binary paths |
| --- | ---: | ---: |
| Structural closures | 60 | 63 |
| Discovery seconds | 5.240717 | 6.052635 |
| Total seconds | 8.345434 | 9.114168 |
| Ordinary solver seconds | 3.081856 | 3.052350 |
| Selected unresolved leaves | 54 | 53 |
| Their literal occurrences | 13,755 | 12,971 |
| SQLite bytes | 35,840,000 | 39,919,616 |
| Pattern nodes | 1,540 | 1,832 |
| Cold seconds | 3.543102 | 3.926286 |
| Warm seconds | 0.027083 | 0.027781 |

Gains: **[6, 13, 85]**. Losses: **[]**.

Each of the 106 prior exhausted leaves receives one additional split in both modes. This is development data and does not establish new whole-source coverage.

The same arbitrary-conditioning/probe/learning caps apply. Binary-path search adds a separately charged limit of 64 roots per residual. It retains every binary reason and checks source-linked proof edges and exact children. Empty proposals are inconclusive, not exclusions of a tractable class.

All 461 Python tests and the full Lean build/axiom audit pass (4,148 declarations / 1,988 theorem declarations). Cold checks verify every node, source binding and solver certificate without changing database bytes. Warm replay inserts no rows. Six-case (full) or four-case traced allocations exclude native SQLite, RSS and full-corpus peak. All prior archives remain retained.

Total charges discovery, independent checks, normalization, serialization, SQLite, ordinary solving and model lifts. Loading, summary walks, hashing and compression are excluded; initialization, cold and warm are separate. These are single synthetic comparisons, not significance estimates or general performance bounds. The frontier transitive archive is reproduced byte-for-byte in the reversed-order direct-only control.

`report.json` contains cases, per-query metrics and fingerprints. `mechanisms.json` counts direct-versus-transitive deletion and actual serialized proof costs; its independent-path encoding is documented there. Shared proof nodes can cost more bytes than separate paths. Full graph/source retention remains the main space increase.

```sh
python3 experiments/compare_cnf_binary_paths.py --suite frontier --output /tmp/binary-paths-frontier
python3 experiments/analyze_cnf_binary_paths.py /tmp/binary-paths-frontier
```
