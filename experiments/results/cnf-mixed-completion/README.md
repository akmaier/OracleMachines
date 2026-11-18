# Mixed two-CNF completion from live premise residuals

See [`research/mixed-completion.md`](../../../research/mixed-completion.md)
for correctness, resource bounds, evidence and next targets. After uniform
completion fails, the optional selector invokes SCC solving only on a binary
residual. It reuses the fresh propagation state and checks a transported model
against every raw target clause and assumption before native publication.
Negative implication paths remain conditional evidence; probing continues.

Twenty-five saved contexts compare inline and mixed completion, with positive
case 51 repeated in reverse order (52 arms). Four positive controls reduce
14 -> 4 native nodes / 6,163 -> 2,357 bytes. Other controls retain their native
certificates. A sixty-query excluded stream adds two mixed models: native
additions fall 385 -> 381 nodes / 437,869 -> 436,179 bytes. Every mode returns
44 SAT / 16 UNSAT. Fourteen SCC calls include twelve negative conditions.

Both orders improve query and complete-worker timing, but cold replay variation
accounts for much of the total change. Diagnostic sidecars grow 1.18%, mean RSS
rises about 1.91 MB and database size is unchanged. No general scaling or memory
improvement is claimed. Fresh case 59 has a source clause covered by three
conditional refutations; native combined publication is a next target, not a
saving already enabled in this experiment.

## Reproduce

Run from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_mixed_completion.py /tmp/new-mixed-completion
python3 experiments/validate_cnf_mixed_completion.py /tmp/new-mixed-completion
python3 experiments/analyze_cnf_mixed_completion.py /tmp/new-mixed-completion
python3 -m unittest solver.test_cnf_mixed_completion solver.test_cnf_inline_completion solver.test_cnf_uniform_premise -q
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

Six production workers run serially in baseline/inline/mixed order and its
reverse, without concurrent tests, builds or profiles. Baseline shares native
preparation. Labels are not inputs to recognition. All 48 family queries remain
unfamiliar after preparation; twelve neighbours become known. Independent
truth enumeration and attribution run after production.

`protocol.json` freezes 528 runtime sources. `validation.json` adds the posthoc
analyzer. Independent reachability checks SCC status without calling the SCC
implementation, then checks all models and implication paths. Native replay
validates every chronological prefix, retained payload and composed record.
The analyzer audits completion costs, stopped prefixes, repeated exact
residuals and negative clause covers. Its 257-formula finite audit supports the
explicit reduction into the remaining nonuniform, nonbinary residual cell.

All 1,145 tests and 25 focused tests pass, including 512 small gated-source /
coordinate comparisons. The full suite retains 44 existing unclosed-SQLite
warnings; focused tests have none. The manuscript builds at 214 pages with all
64 existing proof blocks unchanged. The initial build's label-rerun message
was resolved; `latex-final.log` retains the clean final compiler log. No new
Lean theorem or native proof schema is claimed.

All 1,145 tests, 25 focused tests, 292 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-mixed-completion/checkpoint.json`:
25,334 native keys, preserving all 24,922 earlier payloads, with 232 new
composed records alongside 4,013 inherited records, 2,957 ordinary decisions
and six projections. The union uses 79,339,520 database bytes / 5,889,616
compressed bytes. Four roots have alternate certificates in eight retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116; no new activation is attributed to this policy. Original structural
coverage remains 17/24, supplemental positive coverage 24/24. All 524 prior
sources, 6,228 artifacts and 98 manifests remain unchanged. The manuscript
builds at 214 pages with all 64 existing proof blocks unchanged. The finite
embedding audit checks 257 formulas (255 SAT / two UNSAT).
