# One size census per cold proof snapshot

On 192 further unseen double deletions, the read-only snapshot reduces complete
time 48.19% and cold replay 70.03%. All proof checks remain. Logical and physical
archives are identical across eight trials; peak RSS rises 0.39%. See the
[analysis](../../../research/snapshot-replay.md) for costs and restrictions.

Reproduce into a fresh directory, running the timed producer alone:

```sh
python3 experiments/compare_cnf_snapshot_replay.py /tmp/cnf-snapshot-replay
python3 experiments/validate_cnf_snapshot_replay.py /tmp/cnf-snapshot-replay
python3 experiments/analyze_cnf_snapshot_replay.py /tmp/cnf-snapshot-replay
```

`protocol.json` binds 347 runtime sources, the 14,208-key seed, 145 retained cores,
260 extensions and the selection rule. `previous-decisions.json` contains all
384 prior double-deletion answers, including guarded records, excluded before
selection. Four fresh-process pairs alternate mode order. Both use the frozen
delta worker and identical final preservation checks; only its cold audit is
substituted. No tests, builds or profilers overlap the timed workers.

Snapshot audit runs the frozen complete audit with a read-only transaction and
one independently computed size census, followed by 384 metadata returns.
Every one of the 14,630 proof nodes is still checked. No persisted accounting
value is trusted. Private closed archive clones supply the byte bindings. The
scoped substitution owns its process, not a multithreaded audit service; hostile
private-connection changes are outside the contract. The snapshot-reader WAL
test establishes a stable logical view, not a byte hash of a live external WAL.

All modes answer 98 SAT / 94 UNSAT with 54 core hits, 98 witness publications,
40 guards, 270 fresh expansions and 422 new keys. Of the guarded negative
queries, 37 require fresh search. Repeated visits add no rows. The complete
clock includes restoration, bank checks, expansion, bookkeeping, final full
preservation, cold proof replay, sidecars and compression; process launch,
imports, CLI protocol/catalog reads and final report writes are excluded.
Selection and earlier acquisition are separately charged. Do not combine the
speedup percentages with earlier experiments on different inputs and seeds.

`cost-attribution.json` retains paired costs, phase totals, per-case expansion
counts and the memory regression. Remaining complete time is 39.83% cold proof
checking and 33.07% compression; query work is 16.20%. The 37 negative search
cases provide the next structural-support/cofactor comparison set.

`checkpoint.json` preserves inherited fields and adds `snapshot_replay_study`
and `snapshot_replay_decisions`. The union retains 14,630 keys / 46,530,560 SQLite /
3,674,583 gzip bytes, including the existing accounting schema. The new decision
catalog has 152 direct query roots and 40 guarded source/child records; the
child root alone does not identify the original guarded query.

All 426 tests, eight full archive checks / 3,072 trial query replays, every union
node, 653 inherited decisions and all new decisions pass. Independent validation
uses the ordinary solver with fresh search disabled. Structural authority stays
original 17/24 and separate supplemental 24/24. Prior 343 sources, 3,831 artifacts /
67 manifests and 64 proof blocks are unchanged. The paper builds to 193 pages
without warnings. The final source ledger contains 348 sources with the analyzer.
