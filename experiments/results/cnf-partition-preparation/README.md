# Shared immutable partition preparation

See [the research record](../../../research/partition-preparation.md),
`protocol.json`, `analysis.json` and `next-target.json`. The optional acquisition
path shares first-false branch preparation between premise publication, solving
and sidecar creation. The unchanged independent checker reconstructs the partition
and verifies its premise, exact child roots and models. Preparation grants no
authority and is never persisted.

The four arms pair binary-frequency routing and cofactor-handoff routing with and
without the same preparation. Twelve targets run in 48 serial workers in opposite
orders, yielding 96 attempts. Trials restore exact pre-target prefixes. Six controls
are preceding edits; six new nearby edits are absent from the prior union. Supplied
candidates/maps and sunk previous acquisition remain limitations.

New-edit query time falls **6.15%** with binary-frequency routing and **4.01%**
with cofactor handoff, in both orders. Full worker means regress **1.07% / 0.23%**;
all individual timings are retained. Models, expansions and persisted proof bytes
are identical within each pair. A single returned prepared graph is **35.72%**
smaller in the selected deletion, without a process-peak claim.

`next-target.json` binds four profiles, construction/graph audits and the dominant
nine-expansion branch. Its 125-variable binary/ternary source is captured before
acquisition, with exactly three earlier checked rows beyond the historical prefix.
The target answer is absent. This is the next recognition/reuse target.

The cumulative union has **75,508 native records**, adding 92 unique nodes.
Both readers recheck all authority and the current/earlier partition sidecars.
All **1,438 tests** and **146 focused checks** pass; 44 existing full-suite SQLite
warnings remain, and focused tests emit none. Source/artifact preservation and
manuscript evidence are sealed in `checks.json` and `manifest.json`.

Reproduce in a new directory:

```sh
mkdir experiments/results/cnf-partition-preparation-reproduction
python3 experiments/compare_cnf_partition_preparation.py prepare experiments/results/cnf-partition-preparation-reproduction
python3 experiments/compare_cnf_partition_preparation.py experiments/results/cnf-partition-preparation-reproduction
python3 experiments/analyze_cnf_partition_preparation.py experiments/results/cnf-partition-preparation-reproduction
python3 experiments/profile_cnf_partition_preparation.py experiments/results/cnf-partition-preparation-reproduction
python3 experiments/validate_cnf_partition_preparation.py experiments/results/cnf-partition-preparation-reproduction
```

Finish timing before profiling, tests or CPU-heavy audits. Independent graph walks
measure single returned structures, not simultaneous process peak memory. The
preparation descriptor has no fixed byte cap; its size follows source/prefix and
residual output size. Existing cofactor offers retain their separate 256 KiB cap.
No new SAT coverage class or unrestricted polynomial-time claim follows.
