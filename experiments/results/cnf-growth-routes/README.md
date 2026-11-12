# Finite coverage through retained alternative routes

Frozen composition code: `835f1cb`. From the repository root:

```sh
python3 experiments/compose_cnf_growth_routes.py experiments/results/NEW-DIRECTORY
python3 experiments/audit_cnf_growth_routes.py experiments/results/NEW-DIRECTORY
```

The audit expects `/tmp/oraclemachines-route-tests.log`; the preserved 540-test
log is `full-validation.txt`. The exact paid input is the six-table history in
`../cnf-growth-escape/report.json`, including its four new nodes and growth trial.

Structural coverage rises **31/83 -> 32/83**. Case 33 (`reuse_holdout3`, `n48`,
original case 1193) becomes covered through a saved coupled route and the
growth-three exception. This repeatedly examined development source is not an
independent holdout. The separate ablation removes only the growth route from the
same checked graph and returns to **31/83**, attributing the gain to that escape.

The gained original's 16-step slice includes two complete conditioning choices,
nine unary edges, one coupled route, one growth exception and three already
closed plans. The full 32-root witness has 47 steps; old bases reuse complete
checked certificates rather than duplicating their internal proof graphs.

| Work or retained evidence | Value |
|---|---:|
| Preparing roots and all retained routes | 62.91922 s |
| Composition | 0.0591902 s |
| Reachable nodes / rule premises | 12,595 / 13,176 |
| Resident finite-witness replay | 0.0004235 s |
| Cold route and witness replay | 12.16892 s |
| Witness JSON / compressed bytes | 239,725 / 41,065 |
| Reference solving / cold proof replay | 0.57340 / 0.10216 s |
| Separate reference proof nodes | 212 |
| Separate reference database bytes | 1,896,448 |

The reference solver confirms UNSAT for the 35-variable core, its projected
target and the 48-variable original. All reference proofs are archived in
`endpoints.sqlite3.gz`. This is not a competitive solver comparison, and cold
preparation remains much more expensive than resident composition. No history
row or recognition state is acquired during composition or witness replay.

`coverage.json.gz` stores the finite ordered witness. Its checker reconstructs
the selected old or trial rule, requires every premise to appear earlier and
checks every claimed root. `validation.json` additionally records exact-growth
ablation, deterministic witness reproduction, gained-source traces and endpoint
replay. All 540 tests pass; the full log retains 20 existing SQLite resource
warnings. Earlier histories and failed trials remain unchanged. See
[the study](../../../research/growth-escape.md) for costs, restrictions and the
six-table resume recipe. No unrestricted SAT or new formal theorem is claimed.
