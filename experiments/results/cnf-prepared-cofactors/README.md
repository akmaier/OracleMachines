# Prepared cofactor reuse: saved normalization, unchanged proof bytes

See [the interpretation](../../../research/prepared-cofactors.md), `protocol.json`
and `analysis.json`. A 256 KiB query-local memo removes 7.34% of normalizer input
work on six new edits, but mean query time rises 0.75% in both positive paired
changes. Decisions, expansions, partitions and every native proof payload match
the two-polarity arm. This is retained as an unsuccessful speed optimization.
The general solver defaults remain unchanged.

`next-target.json` binds the largest fresh prepared query, its exact pre-query
prefix, paired instrumented profiles and an independent memory/probe census.
There are 13 memo hits versus 101 misses on the new-edit stream. The next candidate
is direct handoff to the selected child, potentially with reusable unit-trace
preparation. No prepared object or inconclusive propagation result grants an
answer. Probe admission and continuation selection remain larger unresolved costs.

`validation.json` checks 90 attempts and all prior authority; `checkpoint.json`
points to 75,342 preserved native records. Alternatives remain in trial deltas.
The full 1,418-test suite and 100 focused tests pass. The full suite retains 44
existing SQLite warnings; focused tests emit none. `checks.json` and
`manifest.json` seal source, artifact and manuscript evidence.

Reproduce in a new directory without changing this checkpoint:

```sh
mkdir experiments/results/cnf-prepared-cofactors-reproduction
python3 experiments/compare_cnf_prepared_cofactors.py prepare experiments/results/cnf-prepared-cofactors-reproduction
python3 experiments/compare_cnf_prepared_cofactors.py experiments/results/cnf-prepared-cofactors-reproduction
python3 experiments/analyze_cnf_prepared_cofactors.py experiments/results/cnf-prepared-cofactors-reproduction
python3 experiments/profile_cnf_prepared_cofactors.py experiments/results/cnf-prepared-cofactors-reproduction
python3 experiments/validate_cnf_prepared_cofactors.py experiments/results/cnf-prepared-cofactors-reproduction
```

Finish serial comparative timing before profiling, tests or CPU-heavy audits.
Queries include cache setup/cleanup, snapshots, validation, sizing, lookup and
publication. Complete worker time additionally includes persistence, warm reuse,
full cold replay and reconstruction; earlier acquisition and supplied candidates
remain sunk. Peak memo charge bounds retained memo objects, not transient work,
whole-process memory or arbitrary SAT expansion. This adds no decision coverage.
