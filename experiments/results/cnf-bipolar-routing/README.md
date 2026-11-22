# Both cofactor polarities: recognition improves, nearby costs regress

See [the interpretation](../../../research/bipolar-routing.md), `protocol.json`
for the frozen policies/inputs and `analysis.json` for every paired cost.
The saved residual and its two sign variants fall from 30 to four expansions.
The guard remains experimental: controls/new edits take 21.31%/18.85% more query
time than binary-frequency routing, and new native payload grows about 35%.
All 15 targets were already decided by the original policy.

`next-target.json` binds a posthoc profile of the largest new-edit query
regression, with exact pre-query publications and no target answer in the seed.
Instrumented replay reproduces all frozen proof payloads. Profile times overlap
and include instrumentation overhead; use the serial paired trials for speed
comparisons. Normalization, publication and propagation all add work.

`validation.json` records 120 checked attempts, immutable prior ledgers, both
native readers and cumulative preservation. `checkpoint.json` points to the
union with 75,256 native records. Alternative valid payloads remain in individual
trial deltas. `checks.json` and `manifest.json` seal tests, the manuscript check,
source fingerprints and artifacts. The 44 full-suite SQLite warnings are retained;
92 focused tests emit none.

To reproduce without altering this checkpoint, use a new output directory and
run the following stages from the repository root:

```sh
mkdir experiments/results/cnf-bipolar-routing-reproduction
python3 experiments/compare_cnf_bipolar_routing.py prepare experiments/results/cnf-bipolar-routing-reproduction
python3 experiments/compare_cnf_bipolar_routing.py experiments/results/cnf-bipolar-routing-reproduction
python3 experiments/analyze_cnf_bipolar_routing.py experiments/results/cnf-bipolar-routing-reproduction
python3 experiments/profile_cnf_bipolar_routing.py experiments/results/cnf-bipolar-routing-reproduction
python3 experiments/validate_cnf_bipolar_routing.py experiments/results/cnf-bipolar-routing-reproduction
```

Run comparative timing before profiling, tests or other CPU-heavy diagnostics.
Preparation and every worker verify the frozen source hashes. The protocol keeps
both arm orders, all regressions, explicit probe counters, archive deltas, raw
sidecars, warm lookup, full cold replay, reconstruction and storage measurements.
The expansion budget bounds ordinary expansions, not total work or memory.
Donors/maps remain supplied; no efficient classification of arbitrary SAT follows.
