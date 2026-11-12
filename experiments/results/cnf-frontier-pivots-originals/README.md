# Matched early versus near-frontier pivot search

Frozen source: `691e52a`. Reproduce from the repository root:

```sh
python3 experiments/compare_cnf_frontier_pivots.py experiments/results/NEW-DIRECTORY
```

Both modes use the exact merged seed described in `report.json`: the original
additive-growth archive plus both earlier pivot-study deltas. That seed occupies
752,304,128 bytes and retains 345 old trials. Each open input receives at most
eight **new** trials; verified cache hits do not spend that allowance. Both modes
use interaction-first pivot ordering and the same recognizer and projection caps.

The early mode adds 145 trials / 266 pattern nodes in 3.76670 resident expansion
seconds. The frontier mode adds 102 trials / 90 pattern nodes in 1.75051 seconds.
Both retain **31/83** closures without any new closed replacement. Exact selected
frontier reconvergence is 125/145 and 82/102 respectively. The frontier mode scans
more graph nodes but admits fewer candidate projections; this is not a same-work
SAT speedup. Full phase times and counters are in the report.

Each mode directory contains only its own incremental proof delta, its full
report, and an endpoint reference archive. Since no new replacement closed,
endpoint stores are empty initialized databases, not new solved evidence. All
old rows and new proof nodes passed full cold verification; separate trial replay
reconstructs every saved projection and recomposes original coverage unchanged.
Rebuilt logical digests and idempotent delta application also passed.

To resume, reconstruct the merged seed from the report's two input reports,
checking all compressed and database hashes, then apply the new mode deltas with
`apply_delta`. The base and every prior result remain necessary. Failed trials
exclude only their exact source/pivot/recognizer continuation, not a SAT class.
