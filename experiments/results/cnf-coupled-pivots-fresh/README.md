# Reused control for state-capped coupled search

Frozen search code: `b79c757`. Despite the historical `fresh` directory name, these
96 inputs are previously used development controls. Command:

```sh
python3 experiments/compare_cnf_coupled_pivots.py experiments/results/NEW-DIRECTORY --suite fresh
```

The same policy adds **15 new coupled trials / 17 nodes**, retains **88/96**
closures and reuses eight exact coupled trials within the run. No state cap binds
(maximum six admitted states per input). Resident expansion takes 0.21175 seconds
after 5.80214 seconds of seed verification. Full cold audit costs 51.43271 seconds;
separate old/coupled replay costs 5.89978 seconds.

Eleven trials have the retained first route's selected frontier. The other four
reduce open literal count without closing. Every final unresolved leaf already
exists in the seed. The five-table delta is 499,712 SQLite bytes / 24,584 compressed
bytes over a 468,971,520-byte seed. All old bindings, solver proofs and first-pivot
trials survive. Full cold checks, reconstruction and exact trial replay pass.
The endpoint archive is empty because no replacement closes. Use the coupled
study's five-table restore recipe to retain these failed explorations.
