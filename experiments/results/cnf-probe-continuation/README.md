# Checked prefixes for continued probe discovery

Acquisition implementation: `6671637`. Reproduce from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/oraclemachines-continuation-tests.log 2>&1
python3 experiments/compare_cnf_probe_continuation.py experiments/results/NEW-DIRECTORY
python3 experiments/validate_cnf_probe_continuation.py experiments/results/NEW-DIRECTORY
```

Run timing experiments without concurrent tests or profiling. `report.json`
binds implementation/fixture fingerprints, the previous report, input policies,
per-input work, timings, preserved rows and exact table digests. All earlier
archives remain necessary and unchanged.

The policy extends a saved clear window by at most four additional candidates
per visited source. Each block requires its complete checked predecessor for
the same canonical source, width and depth; the cursor alone is insufficient.
Clear prefixes are referenced without rediscovery or trace duplication. Forced
blocks resume their exact residual, including after an admission interruption.
Only present checked residuals become coverage edges.

Coverage improves **36/83 -> 39/83**, with three gained 48-variable originals:

| Selected case | Historical group | Original case | Answer |
|---|---|---:|---|
| 39 | selection_holdout3 | 1229 | SAT |
| 68 | activity_holdout3 | 1412 | UNSAT |
| 79 | implied_holdout3 | 1480 | UNSAT |

Independent reference solving and cold proof replay check these answers.
Removing the earlier growth-exception routes retains all 39 closures. These are
reused development cases; their historical names do not establish independence.

The run processes 47 open originals, adds **51 continuation blocks (43 clear,
eight forced), five initial windows and 45 recognition nodes**. It performs
409 new assumption attempts and reuses 408 saved attempts without rediscovery.
Three immediate continuation targets close. The four-source/32-state policy never
binds: maximum three visited sources and 13 states; zero pending targets.

The warm matched probe substep uses **373 versus 781 attempts** and median
**0.13230 versus 0.27631 seconds** over five alternating-order repetitions,
about **2.09x** faster with shared prefixes. It charges ranking, new discovery
and checking in both modes. Prefixes are already checked; persistence and target
recognition are outside both timings. No whole-solver speedup is claimed.

Resident search/check/persist/compose costs **0.56578 s**. Paid-history preparation
costs **64.40934 s**, full cold inventory **110.38830 s**, and separate cold route
replay **63.12532 s**. Complete acquisition/validation before final report write
costs **257.42807 s**. Storage grows **1,359,872 bytes** above the seed with the
empty eighth table. The delta is **1,429,504 SQLite / 82,368 compressed bytes**;
the coverage witness is **98,652 compressed bytes**. Peak RAM is unmeasured.

All **547 tests** pass; 20 existing SQLite resource warnings remain in the saved
log. Reconstruction checks unchanged old rows, all source bindings, admission
accounting, eight-table delta idempotence, cold prefixes without new probe
discovery, finite coverage, growth ablation and reference proofs. The separate
reference archive contains 513 nodes in 4,546,560 SQLite bytes. The validator also
preserves the remaining candidate/forced-target analysis, with no extra probing.

Resume with `restore` from `compare_cnf_probe_continuation.py`, hash-check and
unpack this delta, then apply its **eight-table** `apply_delta`. Compare the
logical digests and construct `ContinuationRoutes` before using coverage edges.
The complete history has **41,461 pattern nodes, 75 windows, 51 continuation
blocks, 563 pivot trials, 25 coupled trials, one growth trial, 1,548 source
bindings and 21,838 older solver proof rows**. Separate reference archives are
additional. See the [study](../../../research/probe-continuation.md) for scope,
cost boundaries and remaining gaps. Formal sources and manuscript are unchanged.
