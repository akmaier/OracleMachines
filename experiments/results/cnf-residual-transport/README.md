# Bounded source-variable transport

Normalization maps now support automatic native-core transport across changing
compact ranks, with bounded durable hint metadata. Five transfers occur in the
numbering-shift diagnostic. The fresh larger holdout has **zero transfers and
5.26% higher mean query time than the affine baseline**, with identical native
and affine proof digests. Keep the baseline; see the
[analysis](../../../research/residual-variable-transport.md).

- `protocol.json` freezes sources, budgets and inputs before twelve serial workers.
- `mapping-*` compares width-3/4/5 numbering shifts, required-premise deletion and repeat.
- `holdout-*` compares 144/150/156-variable designed mixtures, without supplied labels.
- `report.json` includes query and complete timing, proof/candidate space and cold costs.
- `analysis.json` records family/variant costs, paired signs and outcome changes.
- `mismatch-analysis.json` reproduces every mapped result/counter/digest, counts all
  1,758 selected candidates, and retains eighteen bounded posthoc support trials.
- `support-diagnostic/` preserves its independently checked archive. Twelve supports
  still miss 3–19 clauses; six plans stop at budget; no refutation is added.
- `validation.json` checks 720 chronological attempts, hint origins, independent proof
  readers, all previous histories and 512 exhaustive two-variable formulas.
- `checkpoint.json` retains the proof union and an explicit mapped hint-resume archive.
- `checks.json` binds the 684-source ledger, tests, manuscript and unchanged proofs.
- `manifest.json` seals every result artifact.

The mutable hint table is separate from proof authority. Native and affine proof
payloads remain append-only. Each trial archive preserves its bounded hints;
the cumulative union merges proof authority only. For exact mapped candidate
state, restore `checkpoint.json` → `residual_transport_study.hint_resume_archive`
with the study's existing `base.restore_archive` helper, then open
`ResidualTransportSolver` using the protocol limits. The raw source IDs must still
propose a useful correspondence; arbitrary renaming is not automatically found.

The compact ablation follows the same rules but stores compact matching clauses.
Different representation charges can change evictions, so candidate sets are not
held fixed. The small mapping diagnostic limits affine discovery to one variable
equally in every arm; the larger holdout keeps ordinary affine limits. These are
constructed workloads, not representative external benchmarks.

The initial test failure indexed an absent zero-work metric after an exact hit.
Its source and log are preserved under `initial-policy/` and `initial-tests.log`;
the solver itself did not change. Final tests include the distinct unknown-renaming
case, failed native/metadata commits, conditional refutations, positive/forged
hints, map budgets, one-shot iterators, cold replay and truth-table comparisons.
`failed-finalize/` retains a separate sealing-helper error: a Python source binding
was passed to a JSON loader. Direct hash verification fixes it; no timed result
or solver code changed.

Reproduce in a new directory from the repository root:

```sh
python3 experiments/compare_cnf_residual_transport.py prepare /tmp/oracle-transport-study
python3 experiments/compare_cnf_residual_transport.py /tmp/oracle-transport-study
python3 experiments/analyze_cnf_residual_transport.py /tmp/oracle-transport-study
python3 experiments/validate_cnf_residual_transport.py /tmp/oracle-transport-study
```

Run posthoc work after the timed workers. Do not overwrite these preserved results.
Final sealing also requires the full/focused test logs and final LaTeX log.
