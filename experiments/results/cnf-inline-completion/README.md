# Inline checked completion during premise discovery

See [`research/inline-completion.md`](../../../research/inline-completion.md)
for the argument, cost bounds, measurements, misses and remaining targets.
The new selector reuses the live canonical binding, forced assignment and
residual, verifies the full source model, and stops the unchanged candidate
sequence at its first successful completion. Old negative guard paths remain.
An earlier model can preempt a later valid certificate; alternate witnesses
are retained without replacing previous persistent payloads.

Seventeen saved-prefix contexts compare late uniform and inline completion;
the nonterminal control is repeated in reverse order (36 arms). Four positive
controls fall from eight premise probes to one. Sixty new excluded queries
are run in three modes and two opposite serial orders. All modes answer
42 SAT / 18 UNSAT. Both discovery policies publish thirteen models, with
446 new native nodes. Early stopping removes 84/190 probes and 62,116/171,670
propagation visits. Query time falls 7.33% and diagnostic sidecars 11.16%,
while full worker time rises slightly in both orders. Native storage and RSS
are essentially unchanged. No end-to-end scaling improvement is claimed.

## Reproduce

Run from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_inline_completion.py /tmp/new-inline-completion
python3 experiments/validate_cnf_inline_completion.py /tmp/new-inline-completion
python3 experiments/analyze_cnf_inline_completion.py /tmp/new-inline-completion
python3 -m unittest solver.test_cnf_inline_completion solver.test_cnf_uniform_premise solver.test_cnf_binary_probe -q
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

The six production workers run serially in baseline/uniform/inline order and
its reverse, without concurrent tests, builds or profiles. The baseline shares
native preparation. Family labels never enter recognition. All 48 family
targets remain unfamiliar after preparation; all twelve neighbours become known.
Independent truth enumeration and posthoc attribution occur after timing.

`protocol.json` freezes 523 runtime sources. The posthoc analyzer is additionally
fingerprinted in `validation.json`. Counter audits reconstruct completion work
from saved canonical premises and traces. Fresh chronological replay also
checks that the new sequence is exactly a prefix of the previous attempts.
Failed checks and unvisited suffixes are distinguished. Posthoc SCC diagnosis
retains thirteen source-checked mixed-model conditions on fresh cases
15/27/39/51 and fifteen negative conditions on 43/47/55/59. Timed acquisition
and negative parent recomposition remain open. Full independent native
replay validates all inherited payloads and recomposed decisions.

All 1,137 tests and 24 focused tests pass, including 2,048 exhaustive small
source/coordinate comparisons. Seven logs preserve preflight, production,
test, reconstruction and manuscript output. The full suite retains 44 existing
unclosed-SQLite warnings; focused tests have none. The manuscript builds at
213 pages with all 64 existing proof blocks unchanged. No new Lean theorem or
native certificate schema is claimed.

All 1,137 tests, 24 focused tests, 276 independent counter audits and
full reconstruction pass. Resume `experiments/results/cnf-inline-completion/checkpoint.json`:
24,922 native keys, preserving all 24,444 prior payloads, with 216 new
composed records alongside 3,797 inherited records, 2,957 ordinary decisions
and six projections. The union uses 78,471,168 database bytes / 5,788,630
compressed bytes. Alternate certificates for eight roots remain in fifteen
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116; no frontier activation is attributed to this change. Original structural
coverage stays 17/24 and supplemental positive coverage 24/24. All 519 prior
sources, 6,073 artifacts and 97 manifests remain unchanged. The manuscript
builds at 213 pages with all 64 existing proof blocks unchanged.
