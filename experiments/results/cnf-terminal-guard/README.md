# Terminal-conflict admission: no added fresh coverage

Both policies use the same 20,340-key initial union and 207/176 support banks,
exclude 2,496 prior sidecar answers and cached roots, and visit 192 new neighbours
twice in four alternating process pairs. The frozen previous worker runs both
arms; only the selector and symmetric reporting wrappers differ.

Both modes produce 68 expansions, 23 splits, 66 materialization rows, 309 new
rows, 31 cofactor hits and 99 SAT / 93 UNSAT answers. Proof databases are identical.
Twenty pending entries initially have terminal-conflict origins, but none
matches the eight unresolved alternatives. The candidate adds 3,064 containment
inspections and zero terminal derivations. Mean complete time is 13.93276 /
13.72331 seconds, with paired changes +1.35%, +27.06%, -27.90%, +2.31%; no stable
speedup. Query time averages 1.58% higher. Gzip plus sidecars grows by 300 bytes.

Reproduce from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_terminal_guard.py /tmp/new-terminal-guard
python3 experiments/validate_cnf_terminal_guard.py /tmp/new-terminal-guard
python3 experiments/analyze_cnf_terminal_guard.py /tmp/new-terminal-guard
python3 experiments/check_cnf_terminal_controls.py /tmp/new-terminal-guard
python3 experiments/probe_cnf_missing_clause.py /tmp/new-terminal-guard
```

`test-commands.txt` records the full 1,013-test solver suite, 15 focused tests,
and two subsequent condition tests. All pass. The full suite reports 44 unclosed
SQLite ResourceWarnings; focused suites report none. Allocation origins remain
untraced. Runtime binds 412 sources, including four new runtime/test/checker
files; four post-hoc validation sources bring the ledger to 416.

Historical controls admit old case 85 with two already-retained rows and reject
recursive cases 23/103 without publication. Their deltas and queries are saved;
reconstruct from the bound historical initial union and strict append prefix.
The missing-clause probe uses each fresh query's pre-query state and publishes
nothing. Six of eight unresolved cases admit sound further restrictions, but
none reaches a known or supported endpoint. Current cases 56 and 176 account for
41/68 expansions; checked composition and remaining solve cost are the next
experiment, with SAT case 155 retained as a negative-claim control.

All timing, recognition, derivation, checking, persistence, complete cold replay,
compression and sidecar costs remain in trial reports. Input selection, historical
acquisition and independent validation remain separate charges. This limited
neighbouring-input study establishes no unrestricted-SAT or optimal-cost bound.


## Validation and resume state

Independent validation passes eight complete trial archives / 3,072 query
replays, every union node, all 2,765 inherited decisions and all 192 new decisions.
The union contains **20,649 keys**, preserving all 20,340 prior payloads and
adding 309. There are no alternate certificates. New decisions have 144 direct
roots / 48 negative guards. The separate original structural authority remains
2,614 patterns / 259 pairs, 17/24 coverage with 999 steps; supplemental authority
remains 24/24 with 208 steps. No old discovery pointer is replaced.

Resume `experiments/results/cnf-terminal-guard/checkpoint.json`. It adds only
`terminal_guard_study` and `terminal_guard_decisions` to the prior semantic fields.
All prior diagnostic archives and proof deltas remain preserved. Retained support
ready/pending counts are **129/41 original, 136/71 legacy, 74/102 causal and
74/129 optional expanded causal**. All four complete lineage checks pass; no
support origins were acquired. The source ledger binds 416 files. Prior
preservation checks cover **408 sources / 4,513 artifacts / 79 manifests**.
The paper builds to **202 pages**, with all 64 existing proof blocks unchanged.

Checkpoint SHA-256: `cf7f56eddae920bef8474b92311f37caa65cb635d36973d7adab5d616d7a3358`.
Report SHA-256: `a462fccce08165e759429c6ac3a9ada5e3e1a9f0f8799177d49438fb2c0cdbc5`.

New manifest: **66 artifacts**. Next preservation audit: **4579 artifacts / 80 manifests**.
