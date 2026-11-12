# Repeated-input control for near-frontier discovery

Frozen source: `691e52a`. Command from the repository root:

```sh
python3 experiments/compare_cnf_frontier_pivots.py experiments/results/NEW-DIRECTORY --suite fresh --reverse
```

Despite the historical directory name, these 96 inputs are reused development
controls, not an untouched holdout. Mode order is frontier then early, opposite
the original-input run; this is not a reversed repeat on identical originals.
Both modes start from the same 468,307,968-byte merged seed with 45 old trials.

Frontier search adds 10 trials / 12 nodes in 0.18479 resident expansion seconds;
early search adds 12 / 19 in 0.26631 seconds. Both retain **88/96** closures.
Frontier changes the selected unresolved leaves in seven trials, all increasing
open literal count. Novelty alone does not produce a recognized endpoint.
Preparation, cold audits and separate trial replay remain additional charges.

All old rows survive. Each mode's delta reconstructs identical logical rows,
passes idempotent application, complete cold verification and separate exact
trial/recomposition replay. Empty endpoint archives represent no new solved
evidence. Restore the base and both preceding pivot deltas from the input reports
before applying these new deltas; their hashes and tables are recorded in
`report.json`. See `research/frontier-pivots.md` for scope and remaining gaps.
