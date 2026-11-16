# Incremental reference archive accounting

On 192 further unseen double deletions, guarded insertion deltas reduce complete
runtime 60.48% and query time 94.26%, with identical proof rows, answers and
search counts. Peak RSS increases 9.56%. See the
[analysis](../../../research/incremental-archive-accounting.md) for costs,
invalidation rules and remaining gaps.

Reproduce into a fresh directory, running the timed producer alone:

```sh
python3 experiments/compare_cnf_incremental_archive.py /tmp/cnf-incremental-archive
python3 experiments/validate_cnf_incremental_archive.py /tmp/cnf-incremental-archive
python3 experiments/analyze_cnf_incremental_archive.py /tmp/cnf-incremental-archive
python3 experiments/profile_cnf_incremental_archive.py /tmp/cnf-incremental-archive
```

`protocol.json` binds 341 runtime sources, the 13,869-key parent union, persisted
145-core and 260-template banks, selection and balanced process order. No mode
re-extracts the cores. Historical extraction, acquisition and retained storage
remain charged separately. All previous double-deletion queries, including
guarded answers lacking direct roots, are excluded before selection. These are
constructed development inputs, not an independent arbitrary-SAT sample.

`scanned` uses full row inventories and ordinary size scans; `ledger` reuses the
existing transactional size ledger; `delta` also exports only guarded committed
insertions. All modes keep full initial/final inventories and a complete ordinary
cold audit. Query sidecars, final archives and every trial cost remain retained.
Each candidate performs one opening census and no ledger repair. The delta
cursor performs 385 reads and exports 339 rows / 645,428 SQL length units.

All modes answer 96 SAT / 96 UNSAT with 41 core hits, 96 witness publications,
55 guards and 202 fresh expansions. Repeated visits add no rows. Every logical
proof row and query result agrees. Ledger and delta physical archives agree
within every repetition. `cost-attribution.json` preserves per-case expansions,
phase costs and memory/storage regressions. `cold-profile.json` and its raw
profile locate 384 full size censuses costing 7.21981 s of a 14.87488 s separately
instrumented audit; no profiling overlaps timed workers. Full proof checking
remains mandatory in the next optimization.

`checkpoint.json` preserves inherited fields and adds `incremental_archive_study`
and `incremental_archive_decisions`. Its plain-schema reference union contains
14,208 keys / 44,781,568 SQLite / 3,563,875 gzip bytes. Of 192 new decisions, 137
have direct query certificates; 55 retain source, guard and cofactor certificate
together. A cofactor root must not be treated as the complete query root.

All 418 tests, nine complete archives / 3,456 trial query replays, every union
node, 461 inherited decisions and all new decisions pass with fresh validation
search disabled. Structural authority remains original 17/24 and separate
supplemental 24/24. Prior 336 source bindings, 3,783 artifacts / 66 manifests and
64 manuscript proof blocks are unchanged. The paper builds to 192 pages without
warnings. The final source ledger includes both post-hoc tools (343 sources).
