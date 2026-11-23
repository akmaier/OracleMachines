# Bounded second-target binary recognition

See [the interpretation](../../../research/binary-target-fallback.md),
`protocol.json`, `analysis.json` and `next-target.json`. The optional policy tries
one additional binary-frequency target after the first misses, sharing the
existing implication graph and path cache. Native proof rules are unchanged.

`verified-exploration/` compares the original, binary1, total4, cover-partial and
new binary2 policies on the exact saved branch. The initial exploration and its
source are also preserved. Exploration is not held-out performance evidence.

The frozen comparison has 15 targets, 36 workers and 60 attempts in opposite
orders. Each arm restores its exact pre-target prefix; donors/maps remain supplied.
Changed proofs, unsuccessful probes and regressions are retained. The cumulative
validator checks all new native evidence plus earlier authority with both readers.

Reproduce the frozen-workload construction in a new directory:

```sh
mkdir experiments/results/cnf-binary-interactions-reproduction
python3 experiments/probe_cnf_binary_interactions.py experiments/results/cnf-binary-interactions-reproduction/verified-exploration
python3 experiments/compare_cnf_binary_interactions.py prepare experiments/results/cnf-binary-interactions-reproduction
python3 experiments/compare_cnf_binary_interactions.py experiments/results/cnf-binary-interactions-reproduction
python3 experiments/analyze_cnf_binary_interactions.py experiments/results/cnf-binary-interactions-reproduction
python3 experiments/profile_cnf_binary_interactions.py experiments/results/cnf-binary-interactions-reproduction
```

The cumulative validator also audits the preserved initial exploration. For a
separate reproduction, retain that original `exploration.json`, its policy folders
and `initial-exploration-source.py`, or adapt that historical-artifact audit without
changing this checkpoint. Complete serial timing before CPU-heavy checks.

The six new edits take 69 -> 60 expansions and 8.29% less query time, with both
orders improving. Controls regress 1.14%, and all exposed sign variants still
need nine expansions. Complete new-edit worker time improves only 0.61%.
`probe-boundary.json` separates one case's wrapped 17 -> 8 expansions from direct
11 -> 8: most of the wrapped saving comes from avoiding incomplete probe restart.
This posthoc ablation's proof bytes are subsets of the frozen trial deltas.

The cumulative union preserves 75,677 native records, all prior extensions and
242 partition records. Full/focused tests pass (1,446/154). See `validation.json`,
`checks.json` and `manifest.json` for the sealed audit; the optional policy adds
no whole-input coverage or general efficiency guarantee. The next target is
source-bound continuation reuse across the probe/fallback boundary.
