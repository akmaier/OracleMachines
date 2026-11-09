# Pilot: old continuation choices with selected clauses

9 November 2026. This controlled policy reconstructs the old first-four learned
batch and its binary-frequency ranking, then applies the selected batch while
probing that old variable list/order. Recognition, checking and reconstruction
are charged. Original probe, clause and conditioning caps remain unchanged.
Inputs carry no generator labels into discovery.

| Mode | Closed / 3 | Total seconds | SQLite bytes | Cold seconds | Pattern nodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solver | -- | 0.07611 | 409,600 | 0.03269 | -- |
| First four clauses | 1 | 1.35986 | 3,936,256 | 0.57018 | 307 |
| Selected clauses | 1 | 1.31692 | 3,887,104 | 0.59521 | 321 |
| Selected clauses, old choices | 1 | 1.32219 | 3,887,104 | 0.57375 | 322 |

The three archived sources are 956, 1024 and 1189. Baseline closes only 956;
both selected policies close only 1024. Freezing the immediate continuation
choices does **not** recover the earlier lost closure. The locally improved
1189 still remains structurally unresolved. All original decisions agree with
the independent solver, which retains 86 residuals in each mode.

The separate three-case Python peak is 9,571,051 / 9,552,743 / 9,563,736 bytes
for baseline/selection/fixed; native SQLite, RSS and full-corpus peak are excluded.
Logical node bytes are 2,177,394 / 2,162,710 / 2,165,706. These small selected-case
differences do not predict the full comparison.

All four archives cold-replay byte-identically, and warm reuse inserts nothing.
The separate policy tag prevents stale cross-policy reuse. Original implication
proofs and inactive-delta checks still justify every added clause and reference;
the old ranking is recomputed from checked data, never trusted from persistence.

These are single sequential synthetic samples without concurrent tests, builds
or commits. The three-case pilot is deliberately selected and cannot establish
general coverage or performance. The [full comparison](../cnf-learning-fixed-order/README.md)
retains all previous inputs, fresh unlabelled samples and the unchanged result.
Use a fresh output directory to reproduce:

```sh
python3 experiments/compare_cnf_learning_fixed_order.py --pilot --output /tmp/new-fixed-order-pilot
```
