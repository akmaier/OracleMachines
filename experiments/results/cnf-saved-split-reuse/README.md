# Case 6: saved source-split history control

Both variants close case 6 in one batch, raising coverage 12/24 -> 13/24.
Keeping the four saved source splits chooses pivot 13 and adds 74 patterns with
547 probes. The isolated control omits only those four certificates, retaining
every pattern and every other split; it reconstructs pivot 11 and adds 63
patterns with 345 probes. Thus the smaller visible frontier does not identify
the cheapest downstream expansion by either of these work measures.

The intervention changes selection information and certificate availability
together. It is not an empty-history solve, a general argument for forgetting
history, or a claim that pivot 11 is globally optimal. Both use unchanged scoped
refinement and canonical complete cold audits, with two reversed-order paired
fresh-process runs. Every acquisition from both variants is preserved.

Retained/control mean whole-stream times are 8.07061/7.82088 seconds and peak
RSS 410,058,752/384,090,112 bytes. The retained arm has slightly faster local
expansion despite more probes, more SQLite bytes but fewer gzip bytes. These
cost dimensions disagree. Full audits take about 82% of either stream.

The proofs have 86/76 steps and conditional depths 5/4, with one component
decomposition each and contradiction, 2-CNF and Horn/zero-valid terminals.
No new pattern or split identity is shared between the continuations. The union
therefore preserves 137 new patterns and ten new splits: 2,118 patterns, 209
pairs, seventeen inherited missing children and a 779-step proof for thirteen
originals. Eleven remain unknown. Union storage is 39,448,576 SQLite bytes and
1,970,166 gzip bytes. These finite proofs imply no arbitrary-SAT cost bound.

## Evidence

- `protocol.json` binds inputs, budgets, source versions and run order.
- `diagnostic.json` compares existing ranking with distinct uncovered work at
  twelve remaining sources, without acquisition. No choice changes; this
  diagnostic is not installed as a solver policy. Its cost is recorded separately.
- `report.json` binds all four stream reports and their trial snapshots;
  `producer.txt` preserves raw output. Each snapshot has an independent query
  check and complete cold audit. Repetitions within each mode match exactly.
- `retained-explanation.json`, `ablated-explanation.json` and the corresponding
  target proofs describe both routes. `prior_split_steps` counts identities in
  the full parent, while `available_initial_split_steps` and
  `reconstructed_omitted_split_steps` distinguish actual reuse in each variant.
- `comparison.json` records disjoint new states and the three common parent
  proof steps. This compares alternative routes through one input, not cross-input
  sharing or an observed saving from reusing newly acquired nonterminal states.
- `reconstruction.json` and its text log record frozen independent full audits
  of both initial variants, four trial archives and the union, plus proof,
  catalog, original-binding and immutable-prefix checks. The successful run took
  88.50 seconds outside operational timings and partly concurrent with tests.
- `first-reconstruction-failure.*` and `first-validator.py.txt` preserve the first
  attempt's next-pointer failure after union replay. It composed an absent
  optional root. Presence is now checked before composition; missing means
  unknown. The successful-run time excludes this earlier attempt.
- `checkpoint.json`, `queries.json`, `proof.json`, `pending.json` and `union/`
  preserve the full merged history. `next-discovery.json` binds case 11, its eight
  present/uncovered saved children and root-presence flags `[true, false]`.
- `tests.txt` records 363 passing tests; `targeted-tests.txt` records the three
  new tests separately. `test-command.txt` contains the full suite command.
  Existing database ResourceWarnings remain visible in the raw suite log.
- `paper-check.json` and `paper-build.txt.gz` record a 182-page build with the new
  findings, no overfull boxes or undefined references, and 64 unchanged proofs.
- `validation.json` binds 298 sources and preservation of 294 prior sources,
  3,338 previous artifacts and 56 manifests. `manifest.json` hashes every file
  in this directory except itself.

Reproduce in a new output directory from the repository root:

```sh
python3 experiments/compare_cnf_saved_split_reuse.py /tmp/cnf-saved-split-reuse-reproduction
python3 experiments/validate_cnf_saved_split_reuse.py /tmp/cnf-saved-split-reuse-reproduction
python3 -m unittest solver.test_cnf_saved_split_reuse
```

The producer deliberately starts at its frozen parent. For subsequent discovery,
restore this new union instead. See the
[analysis](../../../research/saved-split-reuse.md) for accounting, restrictions,
the failed heuristic interpretation and next selection experiment.
