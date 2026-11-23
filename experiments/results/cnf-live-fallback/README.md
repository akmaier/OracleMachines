# Live native fallback at the probe boundary

See [the interpretation](../../../research/live-fallback.md), `protocol.json`,
`analysis.json`, `next-target.json` and the sealed `checks.json`/`manifest.json`.

The new synchronous visitor commits completed proofs and makes the existing
routing decision before discarding the native stack. Ineligible support resumes
the same query; an eligible partition discards its frames. No incomplete frame
is stored as proof or serialized across restarts.

The exposed replacement takes 17 -> 11 expansions and 20.71% less query time,
with the same proof bytes. Six control edits improve 2.58%; six new edits never
need native fallback and regress 3.89%. All paired native deltas and partition
sidecars are identical. Complete-worker changes have mixed signs. Defaults remain
unchanged, and the frame census is not a peak-memory bound.

Reproduce the frozen local comparison in a separate directory:

```sh
mkdir experiments/results/cnf-live-fallback-reproduction
python3 experiments/compare_cnf_live_fallback.py prepare experiments/results/cnf-live-fallback-reproduction
python3 experiments/compare_cnf_live_fallback.py experiments/results/cnf-live-fallback-reproduction
python3 experiments/analyze_cnf_live_fallback.py experiments/results/cnf-live-fallback-reproduction
python3 experiments/profile_cnf_live_fallback.py experiments/results/cnf-live-fallback-reproduction
python3 experiments/validate_cnf_live_fallback.py experiments/results/cnf-live-fallback-reproduction
```

Complete serial timing before CPU-heavy tests and cumulative audits. The frozen
protocol binds 12 targets, 24 workers and 48 attempts in opposite orders. Every
seed excludes the queried root. Donors/maps and prior acquisition remain supplied.

The cumulative checkpoint retains 75,724 native records, all older extensions,
and 258 partition records. All 1,456 full and 164 focused tests pass. The next
structural candidate is jointly useful binary consequences in the dominant saved
125-variable branch. In `next-target.json`, use the `novel` capture's acquisition
at index 2: restore its bound prefix plus the three earlier native IDs from its
bound trial delta, with 247 expansions remaining. This reconstructs persistent
availability only, not warm pools or live frames.
