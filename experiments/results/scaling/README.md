# Structural scaling and resource follow-up

All **1,470 answers were correct**, including **672 UNSAT answers**: seven streams, seven modes, three repetitions, 147 sequential workers. No query timed out or failed. Modes were rotated by repetition. Tests and builds finished before timing.

Each worker used a five-second query deadline and an 8 MiB logical SQLite page cap. The largest database was 3,829,760 bytes, so the cap did not bind in this study. WAL files, temporary files and simultaneous process-tree RAM are outside that cap; their exclusion prevents an equal-total-memory claim. The capacity-stop behavior is tested separately without deleting earlier results.

```sh
python3 experiments/run_scaling.py --archives /path/to/satlib-archives --output /tmp/oracle-scaling-new
```

The archive directory contains the five bundles used by `run_expanded.py`. Public inputs here are 11 fixed SATLIB instances from uf50-218, uuf50-218, flat30-60 and AIM. These are historical public benchmarks, not a modern competition suite. Source URLs, archive/member hashes, exact encoded inputs, binary/source hashes, failures, per-query counters and full storage records are retained.

| Stream | Checked | Indexed full | Indexed delta | Symbolic delta | Adaptive | Proof live | Proof restart |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| local_edits | 194.86 | 292.50 | 273.58 | 233.62 | 237.50 | 151.70 | 505.69 |
| width_shift | 170.18 | 171.70 | 170.65 | 166.47 | 173.07 | 135.12 | 386.86 |
| proof_reuse | 171.20 | 147.53 | 144.34 | 137.83 | 165.22 | 131.39 | 360.04 |
| chain128 | 185.64 | 309.41 | 341.59 | 293.10 | 186.51 | 165.38 | 430.05 |
| distant_edits | 283.35 | 598.12 | 566.34 | 377.54 | 418.48 | 237.90 | 1091.12 |
| public_satlib | 267.18 | 675.13 | 663.01 | 662.76 | 361.60 | 515.63 | 1543.78 |
| distribution_shift | 233.18 | 442.07 | 436.85 | 433.00 | 257.17 | 320.35 | 908.24 |

Median total stream milliseconds include service setup and query work. Restart modes include every shutdown. Raw whole-worker elapsed times include final shutdown and interpreter/serialization costs. The summary also contains minimum/maximum stream times and median query latency. Three repetitions do not resolve small differences. Timings compare modes within this run; they do not isolate every code change from the earlier study.

## What changed, and what did not

- An endpoint edit in the 32-edge chain recomputes one bucket and reuses 32. A distant bridge affects all 33. The 64-edge edit stream can affect all 65 buckets. Source comparisons and plan copies remain explicitly counted; endpoint updates still copy 67 plan entries. This is dependency-local recomputation, not constant whole-query cost.
- Direct symbolic acquisition improves the distant-edit stream from 566.34 ms (indexed delta) to 377.54 ms. Checked solving remains faster at 283.35 ms. On the local-edit stream, symbolic delta takes 233.62 ms versus 194.86 ms checked. Verification and storage remain material.
- The separate parity construction builds a 128-variable relation directly with 255 retained BDD nodes (3,166 serialized bytes), without enumerating its 2^128 rows. Construction/projection allocates 48,897 nodes and charges 194,319 manager operations. The retained size is not the peak allocation, and this favorable family does not bound general SAT representations. The service still enforces its local scope cap and verifies proposed rows independently.
- Live and restarted proof modes make 54 checked-core transfers across all repetitions: 27 reuse an already-verified native fact and 27 first revalidate an archived core. Other supported negative traces use LRAT. General proof traversal and restart remain costly.
- Every public SATLIB input exceeds the interface heuristic cap and uses checked fallback. Adaptive selection reduces the full-interface stream cost (675.13 ms) to 361.60 ms, but the checked baseline takes 267.18 ms. Exploration and fallback costs remain in the totals. The policy is empirical and has no adversarial regret guarantee.
- The 128-edge chain stores 626,688 bytes in checked mode, 1,286,144 in indexed delta, and 1,159,168 in symbolic delta. All retain their completed results. Symbolic objects, partial rows, plans, and evidence still cost archive space.

## Scope

These experiments establish observed behavior on specified streams. They do not establish optimal orderings, uniformly local edits, polynomial intermediate diagrams, bounded total RAM, representative current-solver performance, or a uniform polynomial SAT algorithm. The new Lean theorems state these scaling obligations as hypotheses. Earlier studies and their raw results remain unchanged.


The live archive was backed up before revalidation. `persistence-before.json`
records every older row fingerprint and all 44 earlier experiment-file hashes.
`persistence.json` confirms that all 2,485 old results, 645 proofs and all other
old rows remain unchanged. Revalidation adds 355 current-engine results and 129
proofs, for totals of **2,840 results / 774 proofs**. An independent semantic
audit checks all 355 current inputs. The backup itself stays in the ignored local
cache directory.
