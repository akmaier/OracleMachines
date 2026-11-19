# On-demand negative edit reuse

The [analysis](../../../research/on-demand-negative-edit-reuse.md) documents the
optional policy and its limits. Sixteen recent native UNSAT roots are proposed
without donor labels. A near edit triggers causal support discovery; only a fully
contained support is materialized and checked. A missing premise gives no verdict.

Eight serial workers compare the preceding witness pool against this policy in
opposite orders. Exposed sizes are 24/48/72 and fresh holdout sizes 36/60/84, each
with 108 queries/72 roots from six synthetic designs. Policy and sources are frozen
before both streams. Each worker starts empty. The native expansion cap is 256;
each separate support traversal caps processed nodes at 256 and literals at 131072.
Neither limit bounds all checks, emitted proof size, transient memory or runtime.

Ten checked negative transfers occur in each stream, saving 382/378 fresh expansions.
Mean query time **regresses 2.40%/5.81%**, and warm time also regresses in both orders.
Materialization adds 650/740 core or subset records. SQLite bytes fall 15.30%/9.37%,
although record counts rise. Complete time falls 7.40%/1.46%, with one holdout gain
only 12 ms. Keep the witness pool as the latency baseline and this path as an
optional space/replay tradeoff. Outcomes and structural closure coverage do not
improve. All unknown observations and regressions are retained.

Worker timing includes setup, retrieval, discovery, materialization, solving,
checking, publication, append metadata, graph sizing, warm/cold replay, cold solver
reconstruction, sidecars and compression. Preparation and posthoc audits/profiles
are separate. Process RSS includes the harness. Negative candidate state starts
empty on reopen; exact-root replay readmission is not restoration of the old pool.

## Reproduce

From the repository root, choose a fresh destination:

```sh
python3 experiments/compare_cnf_negative_edit_pool.py prepare /tmp/cnf-negative-new
python3 experiments/compare_cnf_negative_edit_pool.py /tmp/cnf-negative-new
python3 experiments/validate_cnf_negative_edit_pool.py /tmp/cnf-negative-new
python3 experiments/profile_cnf_negative_edit_pool.py /tmp/cnf-negative-new
python3 -m unittest solver.test_cnf_negative_edit_pool solver.test_cnf_causal_support solver.test_cnf_unsat_support solver.test_cnf_deferred_support
python3 -m unittest discover -s solver -p 'test_*.py'
```

Every trial retains a full archive, query deltas, warm observations, timing and
cold reconstruction metadata. `analysis.json` records cohorts, paired differences,
and budget-stop IDs. `profile.json` matches all outputs/counters/native digests;
it attributes duplicated support traversal and normalization without claiming a
faster implementation. Its first comparison used JSON string model keys against
in-memory integer keys. Failed source/log remain in `failed-profile/`; normalized
comparison passes. Timed workers were unchanged.

Both readers verify the append-only union of 39,211 native records and earlier
extensions. All 652 prior sources and 8,141 artifacts across 120 manifests remain
unchanged, along with 5,650 composed/444 pilot decisions, 864 witness observations,
108 larger-stream observations/recovery and 624 inventory nodes. The new audit
checks 864 chronological attempts and all 512 two-variable clause-set formulas.
All old payloads remain authoritative; 164 differing valid-payload observations
remain in their full trial archives. `tiny/` retains exhaustive audit results.

All 1,327 full/188 focused tests pass. The full suite retains 44 unchanged-site
SQLite warnings; focused tests emit none. The 230-page manuscript builds without
warnings and preserves 64 proof blocks. Final source ledger: 658. `checks.json`
and `manifest.json` bind the results.

Resume `checkpoint.json`. Next: share a bounded, source-bound derivation plan
between discovery and ordinary checked materialization. Failed deleted-premise
supports, broader pattern discovery and durable candidate retention remain open.
No uniform polynomial arbitrary-SAT result is established.
