# Automatic bounded witness retrieval

See the [analysis](../../../research/bounded-witness-pool.md) and `protocol.json`.
The optional solver remembers 64 packed vectors and tests at most four recent
same-variable-count assignments per residual. It receives no donor relationships
or family labels. Every hit satisfies the complete target and the unchanged native
verifier. Misses supply no UNSAT evidence. Existing proof formats are unchanged.

## Frozen evaluation

Eight serial workers compare batching with the pool in opposite orders, on two
separate 108-query streams. Exposed sizes are 24/48/72; holdout sizes are 30/54/78,
using the same six designs with two samples and base/edit/repeat variants. Policy
and sources were frozen before both streams. Each worker starts empty, with 256
native expansions per attempt; budgets do not cap all work, memory or stored nodes.
No outcome filtering, donor labels or holdout tuning occur.

Mean query time improves 2.97% exposed and 8.27% holdout in both orders; complete
worker time improves 4.36% and 9.06%. Holdout edit expansions fall 1,342 to 955,
native records 3,292 to 2,873, and SQLite bytes 34,770,944 to 30,937,088. The
candidate pool's conservative retained charge stays below 14,200 bytes. Two
attempts remain unresolved in every arm/split. Parity has no hits and incurs extra
probe work; some other family timings and holdout warm time also regress.

Worker timing includes setup, solving, candidate checks/admissions, native
verification, publication, append metadata, retained-object measurement, warm and
cold proof replay, cold solver reconstruction, sidecars and compression. Preparation
and posthoc validation are separate. RSS includes harness objects and replay.
The exposed 64-row archive tail seeds zero models; holdout seeds 33 vectors.
Seed payload bytes and transient decoding are outside the vector-state cap.
Two orders and a synthetic size holdout do not establish general speedups.

## Reproduce

Use a fresh destination from the repository root:

```sh
python3 experiments/compare_cnf_witness_pool.py prepare /tmp/cnf-witness-new
python3 experiments/compare_cnf_witness_pool.py /tmp/cnf-witness-new
python3 experiments/validate_cnf_witness_pool.py /tmp/cnf-witness-new
python3 -m unittest solver.test_cnf_witness_pool
python3 -m unittest discover -s solver -p 'test_*.py'
```

Each trial retains its full compressed archive, query observations, warm results,
seed metrics, and timing report. `analysis.json` records cohort costs, paired
regressions and unknown case IDs. `tiny/` retains the 512-formula exhaustive audit.
`union/` adds new checked keys while keeping old payloads authoritative. Different
valid witnesses are retained in trial archives, not overwritten during merging.

## Checks and restart

All 647 previous sources and 8,088 artifacts across 119 manifests remain unchanged.
Both readers verify the union of 34,426 native records plus all earlier extension
records. Historical 5,650 composed / 444 pilot decisions, 108 larger-stream
observations, recovery and 624 inventory nodes are rechecked. The audit validates
864 chronological attempts and every new certificate. It records 130 differing
valid-payload observations, preserving their full trial archives. Exhaustive
checking of all 512 clause-set CNFs over two variables yields 95 SAT / 417 UNSAT.

The first validator attempted to read the preceding recovery result through an
incorrect nested `result` key. Its source and log are preserved in `failed-audit/`.
The corrected validator passes; timed runs are unchanged. All 1,319 full and 150
focused tests pass. The full suite emits 44 SQLite warnings at unchanged files;
focused tests emit none. The 229-page paper builds without warnings and retains
all 64 proof blocks unchanged. `checks.json` and `manifest.json` seal the results.
Final executable source ledger: 652.

Resume from `checkpoint.json`. The next primary gap is negative-search reuse
across edits with checked clause dependencies; bounded durable SAT-only candidate
retention is the concrete supporting persistence gap. No new structural family
closure or uniform polynomial arbitrary-SAT bound is established.
