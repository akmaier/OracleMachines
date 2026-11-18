# One cover-directed premise beyond the fixed variable ranking

See [`research/cover-directed-probe.md`](../../../research/cover-directed-probe.md)
for correctness, costs, measured outcomes and remaining gaps. The optional
policy chooses an unattempted literal from the narrowest source clause with
exactly one missing negative condition, breaking ties by source index. At most
one extra premise is propagated. A negative binary result joins retained cover
conditions; a positive binary model must satisfy the entire raw premise.
Unit-conflict and nonbinary outcomes remain explicit misses. The prior discovery
record is unchanged and native publication/replay uses existing proof kinds.

Twenty-nine exact-prefix contexts compare cover-only and the additional probe;
one target repeats in reverse order (60 arms). Four changed parents shrink
52 -> 32 nodes / 63,028 -> 38,503 native bytes. Six serial workers compare
baseline/cover/probe and its reverse on sixty excluded queries, returning
40 SAT / 20 UNSAT in every mode. Four extra conditions reduce acquisition
431 -> 407 nodes / 542,374 -> 512,936 bytes. All 99 base probes and fourteen
positive publications remain unchanged. All 48 family targets are unfamiliar
after shared preparation; twelve neighbours become known.

Mean query time falls 10.22% and propagation including discovery falls 5.97%.
Complete-worker timing is mixed and the mean rises about 0.023 seconds.
Diagnostics grow 0.82%, trial SQLite falls 36,864 bytes, and mean RSS rises
about 1.61 MB. This is no end-to-end speedup or general scaling claim. The four
chosen clauses' required prior conditions appear after 8, 5, 7 and 4 base probes;
eight later probes could retrospectively be avoided for those clauses, but
no early-selection policy or timing gain has yet been established.

Coupled parity and random three-CNF still add 308 nodes / 52,385 acquisition
propagation visits. Reusing the existing affine extraction layer on unlabelled
coupled inputs is the next broader-coverage target; full model/refutation
checking and leftover interaction costs remain explicit.

## Reproduce

Run from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_cover_probe.py /tmp/new-cover-probe
python3 experiments/validate_cnf_cover_probe.py /tmp/new-cover-probe
python3 experiments/analyze_cnf_cover_probe.py /tmp/new-cover-probe
python3 -m unittest solver.test_cnf_cover_probe solver.test_cnf_negative_cover solver.test_cnf_mixed_completion -q
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

Preflight passes 58 exact-prefix arms, 60 independently reconstructed fresh
selections and an eight-query worker with inherited warm/cold replay. Clean
production workers run serially without concurrent tests, builds or profiles.
Truth enumeration, independent replay and attribution happen afterwards.
`protocol.json` freezes 538 runtime sources; `validation.json` adds the posthoc
analyzer for 539 sources. The 300 counter audits validate recognition, extra
premise payloads, SCC edges and checked cover reasons/paths alongside earlier
completion audits. Transport, repair and propagation costs are instrumented
measurements; the resulting native certificates are independently checked.

All 1,161 tests and 24 focused tests pass, including 128 graph/coordinate
comparisons, positive completion, explicit misses, corruption rejection, forced
prefixes, known-node preservation and cold replay. Full tests retain 44 existing
unclosed-SQLite warnings; focused tests have none. The 216-page manuscript builds
with all 64 existing proof blocks unchanged and a clean final compiler log.
No new Lean theorem or native proof schema is claimed.

## Excluded pilot

The first production attempt overlapped the tail of preflight and was stopped.
`excluded-overlap-pilot.tar.gz` preserves its incomplete output and an internal
manifest. Its bindings retain their originally requested paths and must not be
interpreted as bindings to the clean run. All sixty saved native control deltas
are byte-identical to the clean-run counterparts; it has no completed fresh
worker artifacts. `excluded-pilot.json` records this audit. All pilot timing is
excluded from the comparisons above. The complete run restarted after preflight
finished, with identical runtime sources.

All **1,161 tests**, 24 focused tests, 300 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-cover-probe/checkpoint.json`:
**26,279 native keys**, preserving all 25,757 earlier payloads, with 240 new
composed records alongside 4,479 inherited records, 2,957 ordinary decisions
and six projections. The union uses 81,416,192 database bytes / 6,113,510
compressed bytes. Fourteen roots have alternate certificates in 27 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 534 earlier sources,
6,641 artifacts and 100 manifests remain unchanged. The 216-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem or
unrestricted-SAT resource guarantee is claimed.

New manifest: **230 artifacts**. Next preservation audit: **6,871 artifacts / 101 manifests**. Final source ledger: **539**.
