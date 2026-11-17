# Retain unit prefixes after rejected discovery

The optional selector reuses the original target's saved baseline unit trace
after the preceding discovery policy declines a candidate. It does not publish
the rejected guard. The existing checked publisher solves the remaining residual
normally; residual search is still unrestricted and subject to its expansion
budget. Explicit publication replaces the target expansion call.

Twenty-seven exact-prefix arms retain the previous seven controls and add prior
stream cases 36/186. The latter use 4,046/3,234 propagation visits, versus
5,299/3,608 under the preceding policy and 1,453/1,636 under native baseline.
The new and preceding policies retain identical native payloads in all controls.
Across all nine controls, visits fall 23,813 -> 20,896 with the same 42 rows.
Single-arm timings establish no improvement; discovery overhead remains.

Six fresh workers run baseline/propagated/retained and the reverse order on 192
new roots: 64 double-deletion neighbours of each of three old templates. The
generator excludes every earlier ordinary/composed query and native root,
including 1,216 previous query roots per template. Catalogue selection costs
1.541 seconds separately. Tests, profiles and builds do not overlap production.

| Measure | Baseline | Previous policy | Retained prefix |
| --- | ---: | ---: | ---: |
| SAT / UNSAT answers | 103 / 89 | 103 / 89 | 103 / 89 |
| New native rows | 271 | 269 | 269 |
| Added native bytes | 527,695 | 527,030 | 527,030 |
| Expansion calls | 53 | 46 | 43 |
| Explicit trace publications | 0 | 5 | 8 |
| Propagation literal visits | 14,126 | 24,342 | 22,811 |
| Mean complete worker seconds | 18.300 | 18.467 | 18.299 |

Three fresh prefix reuses remove 1,531 propagation visits (6.29%) while keeping
identical native archives. Additional prefix checks inspect sixteen unit-reason
literals. Sidecars grow 4,224 bytes (0.077%). The two complete-time differences
against the preceding policy are +0.091 and -0.426 seconds, establishing no
stable speedup. Both optional policies share two propagated-residual hits.
Warm replay acquires no rows. The earlier gate supplies the two-row reduction
against baseline; propagation still exceeds baseline by 61.48%.

Four cases contribute all remaining child expansions: 0/131/146/159 contribute
17/14/5/7. The posthoc diagnostic rechecks their rejected-child unit traces and
finds that case 146's child is positive-terminal: its 26 unit deductions satisfy
every clause. The current gate accepts known children or unit conflicts and
misses this positive closure. The canonical child model is checked, but lifting
it to the original target and publishing a direct SAT witness are unimplemented
and unmeasured. No projected row saving is counted. Cases 0/131/159 still leave
nonfamily residuals of 139/119/125 literals after the proposed condition and
propagation. All four baseline residuals fail the complete single-variable test
for two immediate syntactic two-CNF restrictions; further propagation is outside
that test. Preserve the negative controls and previous case-36 positive control.

The 22,532-key union preserves all 22,259 previous native payloads, adding 273
keys with no alternative payloads. It retains 603 new composed records alongside
1,827 earlier composed records, 2,957 ordinary decisions and six projections.
The union occupies 72,720,384 database bytes / 5,223,549 compressed bytes and
retains all arms, rather than one policy's working storage. Ready/pending banks
are 132/38, 141/66, 85/91 and 85/118. Structural and supplemental authorities
are unchanged; all prior 488 sources, 5,329 artifacts and 91 manifests remain
preserved.

All 1,094 tests and 25 focused tests pass. The full suite emits 44 existing
SQLite ResourceWarnings; focused tests emit none. Independent validation
reconstructs all control prefixes, regenerates the excluded catalogue, checks
availability and selection, and verifies native/composed proofs and warm/cold
replay without acquisition. It also asserts previous/new native payload equality
in all controls and fresh streams. The 208-page paper builds cleanly and retains
all 64 prior proof blocks. The protocol binds 492 runtime sources; validation
adds one posthoc analyzer for 493 total.

Reproduce from the repository root into a new output directory:

```sh
python3 experiments/compare_cnf_trace_fallback.py /tmp/cnf-trace-fallback-reproduction
python3 experiments/validate_cnf_trace_fallback.py /tmp/cnf-trace-fallback-reproduction
python3 experiments/analyze_cnf_trace_fallback.py /tmp/cnf-trace-fallback-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_trace_fallback solver.test_cnf_propagated_reuse solver.test_cnf_child_admission
```

The new queries remain within three old template families. Cold replay is the
largest complete-time component. No stable general speedup, live-memory bound,
new Lean theorem or unrestricted-SAT efficiency result is established.

New manifest: **126 artifacts**. Next preservation audit: **5455 artifacts / 92 manifests**. Final source ledger: **493**.
