# Fresh streams for the unchanged child-admission gate

Four fresh processes run baseline/admitted and admitted/baseline on 192 new
query roots, excluding inherited ordinary/composed query results and native
roots. The inputs are 64 double-deletion neighbours per existing template,
with 1,088 earlier query roots excluded per template. No tests, profiling or
builds overlap production. The eighteen earlier exact-prefix controls remain
bound by the protocol. The gate and native solver are unchanged.

| Measure | Baseline | Admitted |
| --- | ---: | ---: |
| SAT / UNSAT answers | 101 / 91 | 101 / 91 |
| New native rows | 229 | 221 |
| Added native bytes | 460,398 | 448,420 |
| Expansion calls | 17 | 1 |
| Explicit trace publications | 0 | 8 |
| Probe + premise/child propagation visits | 5,590 | 11,343 |
| Mean complete worker seconds | 28.229 | 31.695 |

Rows decline 3.49%, but sidecars grow 2.44% and complete time increases in both
pairs. Two pairs establish no stable general runtime or live-memory bound.
Three unit-conflict children account for the eight-row saving. Two other targets
already unit-refute; one SAT query exhausts four probes and falls back.

Case 85's first propagation fixes 23 variables and exposes the checked SAT
root `cnf-residual-v1:[[-2,-1]]`, available at that exact prefix. The posthoc
diagnostic validates its 80-byte payload and lifts the model to the restricted
target. Current discovery still pays 4,795 propagation visits and fallback
another 955, versus baseline 955. Next, check and reuse the propagated residual
before probing. This is a checked opportunity, not a measured policy change.

The 22,036-key union preserves all 21,801 previous payloads, adding 235 keys
with no alternative payloads. It retains 384 new composed records, 846 earlier
composed records, 2,957 ordinary decisions and six projections. Database size
is 70,344,704 bytes; compressed size is 5,103,740 bytes. All trial archives remain
saved, including regressions. Ready/pending frontiers are 132/38, 140/67, 84/92,
84/119; the separate structural coverage authority is unchanged.

All 1,076 tests and 19 focused tests pass; the full suite retains 44 existing
SQLite ResourceWarnings and focused tests emit none. Independent exclusion,
prefix, proof, witness, warm and cold checks pass. The 207-page paper builds
cleanly and preserves 64 proof blocks. The protocol binds 482 runtime sources;
validation adds one posthoc source for 483 total. All 480 prior sources,
5,186 artifacts and 89 manifests are preserved.

Reproduce from the repository root into a new output directory:

```sh
python3 experiments/compare_cnf_child_stream.py /tmp/cnf-child-stream-reproduction
python3 experiments/validate_cnf_child_stream.py /tmp/cnf-child-stream-reproduction
python3 experiments/analyze_cnf_child_stream.py /tmp/cnf-child-stream-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_child_admission solver.test_cnf_local_guard solver.test_cnf_assumption_guard
```

The catalogue still belongs to three old families. Changes are matched-stream
contributions, not isolated equal-prefix causal gains or arbitrary-SAT coverage.
Cold replay dominates complete time. No new Lean or unrestricted-SAT theorem.

New manifest: **36 artifacts**. Next preservation audit: **5222 artifacts / 90 manifests**. Final source ledger: **483**.
