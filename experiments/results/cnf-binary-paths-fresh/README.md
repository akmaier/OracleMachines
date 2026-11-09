# Checked binary-path reduction: fresh

**Optional coverage method; not promoted as the default.** See the [proof, literature and resource account](../../../research/binary-paths.md).

| Measure | Retained baseline | Transitive binary paths |
| --- | ---: | ---: |
| Structural closures | 75 | 75 |
| Discovery seconds | 1.786398 | 2.268099 |
| Total seconds | 3.096482 | 3.631579 |
| Ordinary solver seconds | 1.305278 | 1.358833 |
| Selected unresolved leaves | 22 | 22 |
| Their literal occurrences | 7,151 | 6,994 |
| SQLite bytes | 16,355,328 | 17,866,752 |
| Pattern nodes | 717 | 813 |
| Cold seconds | 1.267178 | 1.426604 |
| Warm seconds | 0.025104 | 0.024590 |

Gains: **[]**. Losses: **[]**.

The 96 fresh cases use seed 202611091650, variables 12/24/40, signed permutations, clause edits and disjoint Horn mixtures. No closure gain occurs.

The same arbitrary-conditioning/probe/learning caps apply. Binary-path search adds a separately charged limit of 64 roots per residual. It retains every binary reason and checks source-linked proof edges and exact children. Empty proposals are inconclusive, not exclusions of a tractable class.

All 461 Python tests and the full Lean build/axiom audit pass (4,148 declarations / 1,988 theorem declarations). Cold checks verify every node, source binding and solver certificate without changing database bytes. Warm replay inserts no rows. Six-case (full) or four-case traced allocations exclude native SQLite, RSS and full-corpus peak. All prior archives remain retained.

Total charges discovery, independent checks, normalization, serialization, SQLite, ordinary solving and model lifts. Loading, summary walks, hashing and compression are excluded; initialization, cold and warm are separate. These are single synthetic comparisons, not significance estimates or general performance bounds. The frontier transitive archive is reproduced byte-for-byte in the reversed-order direct-only control.

`report.json` contains cases, per-query metrics and fingerprints. `mechanisms.json` counts direct-versus-transitive deletion and actual serialized proof costs; its independent-path encoding is documented there. Shared proof nodes can cost more bytes than separate paths. Full graph/source retention remains the main space increase.

```sh
python3 experiments/compare_cnf_binary_paths.py --suite fresh --output /tmp/binary-paths-fresh
python3 experiments/analyze_cnf_binary_paths.py /tmp/binary-paths-fresh
```
