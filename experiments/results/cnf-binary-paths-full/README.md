# Checked binary-path reduction: full

**Optional coverage method; not promoted as the default.** See the [proof, literature and resource account](../../../research/binary-paths.md).

| Measure | Retained baseline | Transitive binary paths |
| --- | ---: | ---: |
| Structural closures | 1,410 | 1,413 |
| Discovery seconds | 81.476023 | 97.007198 |
| Total seconds | 122.463712 | 139.463288 |
| Ordinary solver seconds | 40.910299 | 42.379682 |
| Selected unresolved leaves | 106 | 100 |
| Their literal occurrences | 32,404 | 31,283 |
| SQLite bytes | 417,370,112 | 475,529,216 |
| Pattern nodes | 22,071 | 25,578 |
| Cold seconds | 52.181698 | 59.560079 |
| Warm seconds | 0.278793 | 0.294279 |

Gains: **[1007, 1065, 1072, 1363]**. Losses: **[1471]**.

The full 1,497 inputs include 512 tiny cases. Non-tiny coverage is 898/985 -> 901/985, with four gains and one loss. Archived plans jointly cover 902/985 known sources, but no efficient combined policy is implemented. The ordinary solver is unchanged and all answers agree.

The same arbitrary-conditioning/probe/learning caps apply. Binary-path search adds a separately charged limit of 64 roots per residual. It retains every binary reason and checks source-linked proof edges and exact children. Empty proposals are inconclusive, not exclusions of a tractable class.

All 461 Python tests and the full Lean build/axiom audit pass (4,148 declarations / 1,988 theorem declarations). Cold checks verify every node, source binding and solver certificate without changing database bytes. Warm replay inserts no rows. Six-case (full) or four-case traced allocations exclude native SQLite, RSS and full-corpus peak. All prior archives remain retained.

Total charges discovery, independent checks, normalization, serialization, SQLite, ordinary solving and model lifts. Loading, summary walks, hashing and compression are excluded; initialization, cold and warm are separate. These are single synthetic comparisons, not significance estimates or general performance bounds. The frontier transitive archive is reproduced byte-for-byte in the reversed-order direct-only control.

`report.json` contains cases, per-query metrics and fingerprints. `mechanisms.json` counts direct-versus-transitive deletion and actual serialized proof costs; its independent-path encoding is documented there. Shared proof nodes can cost more bytes than separate paths. Full graph/source retention remains the main space increase.

`gap-profile.json` preserves a separate source-1445 profile and selected loss plans. `loss-alternatives.json` traverses all alternatives and isolates the lost variable-1 split in source 1471. A semantic reduction changed its candidate list; it did not change satisfiability.

```sh
python3 experiments/compare_cnf_binary_paths.py --suite full --output /tmp/binary-paths-full
python3 experiments/analyze_cnf_binary_paths.py /tmp/binary-paths-full
```
