# Checked UNSAT support reuse

On 192 unseen double deletions, 145 checked cores answer 40 negative queries
through containment and reduce fresh expansions 524 -> 355. Complete time
nevertheless increases 40.16% and peak RSS 28.15%. This optional experiment
preserves the regression. See [analysis](../../../research/unsat-support-reuse.md).

Reproduce the matched experiment into a fresh directory:

```sh
python3 experiments/compare_cnf_unsat_support.py /tmp/cnf-unsat-support
python3 experiments/validate_cnf_unsat_support.py /tmp/cnf-unsat-support
python3 experiments/analyze_cnf_unsat_support.py /tmp/cnf-unsat-support
python3 experiments/profile_cnf_unsat_support.py /tmp/cnf-unsat-support
```

`protocol.json` binds 334 runtime sources, the 9,104-key parent, selection rule
and balanced three-mode orders. Every mode pays its own preparation and visits
all queries twice. `screen.json` and the root `history.sqlite3.gz` preserve the
initial extraction diagnostic; the matched workers independently reproduce
extraction, so this optional screen is not required for a fresh reproduction.

Every trial retains its cores, queries, certificates, failed cost comparison
and archive. `all-0/cores.json` is the reusable 145-core bank. The post-hoc
`cost-attribution.json` preserves 121 nondominated core indices and their
containment witnesses, with unchanged superset coverage. This antichain has not
yet been benchmarked. Only ten preparation nodes are unused by current proofs.
`warm-profile.json` and `warm-profile.pstats` identify full-inventory and size
scans as 84.55% of a separately instrumented warm loop. No profiler runs during
the matched trials.

`checkpoint.json` preserves all inherited study and decision fields. It adds
`unsat_support_study` and `unsat_support_decisions`; its union retains 13,869
keys. The 192 new decisions comprise 139 direct query certificates and 53
explicit guarded cofactor records. For those 53, replay the source, guard and
child together rather than treating the child key as the query key. Earlier
payloads win overlaps; 21 alternate certificate occurrences remain in trial
archives. No previous results or proof nodes were deleted.

All 403 tests, 3,456 trial query replays, the support screen, every union node,
269 inherited decisions and all new decisions pass cold checks without fresh
search. Structural coverage remains 17/24 originals and 24/24 separate
supplemental inputs. The next target is exact incremental archive accounting,
then further unseen edits using the persisted cores with acquisition charged.

Preservation checks retain 330 prior sources, 3,723 artifacts across 65 manifests
and all 64 existing proof blocks. The manuscript builds to 191 pages. The final
ledger contains 336 sources including both post-hoc tools.
