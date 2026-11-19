# Shared causal support derivations

The [analysis](../../../research/shared-support-derivations.md) describes the
optional implementation, measured regressions and next discovery target.
Query-local recipes retain exact support choices and emit ordinary certificates
through the unchanged native checker. A 4 MiB conservative retained charge
excludes encoding/decoding transients, emission workspace and the checked graph.
Plan-cap failure discards the plan and charges the original bounded fallback.

Twelve serial workers compare witness-only retrieval, negative edit reuse and
shared plans in opposite orders, with empty initial archives. Exposed scales are
24/48/72; a fresh holdout uses 42/66/90. Each has 108 attempts and 72 roots, drawn
from six designed generators with two samples and base/edit/repeat variants.
All sources and policy were frozen before timing. There is no outcome filtering.

Mean query time improves **6.45% / 2.62%** against negative edit reuse; complete
time improves **3.14% / 1.02%**. Both paired orders improve. The plan removes
415 / 518 repeated support-node visits while preserving every proof byte and
acquisition outcome. Holdout still costs **0.87% more than witness-only search**
on the mean, with mixed paired signs. Mean cold/warm time and measured memory
rise slightly against negative reuse. Permanent proof storage stays identical.
All regressions and original budget-stop observations are preserved.

Preparation, recognition, planning/sizing, emission, checking, publication,
graph sizing, warm/cold replay, reconstruction, sidecars and compression are
charged. Preparation of the study and posthoc audits/profiles are separate.
Process RSS includes the harness. No claim of representative performance or
uniform polynomial SAT expansion is made.

## Reproduce

Choose a fresh destination from the repository root:

```sh
python3 experiments/compare_cnf_support_plan.py prepare /tmp/cnf-plan-new
python3 experiments/compare_cnf_support_plan.py /tmp/cnf-plan-new
python3 experiments/validate_cnf_support_plan.py /tmp/cnf-plan-new
python3 experiments/profile_cnf_support_plan.py /tmp/cnf-plan-new
python3 -m unittest solver.test_cnf_support_plan solver.test_cnf_negative_edit_pool solver.test_cnf_causal_support solver.test_cnf_unsat_support solver.test_cnf_deferred_support
python3 -m unittest discover -s solver -p 'test_*.py'
```

The protocol/report/analysis retain every worker, query delta, archive, replay
and budget stop. The independent audit checks 1,296 chronological attempts,
432 exact plan/negative comparisons and 512 two-variable formulas. Both readers
check the union of 45,061 native records and prior extension tables. All 658 prior
sources and 8,197 artifacts across 121 manifests remain unchanged. Earlier
authoritative bytes are retained; 260 alternative valid-payload observations
remain in trial archives. `tiny/` stores exhaustive results.

`profile.json` preserves identical outputs/counters/native digests. `frontier.json`
records where native acquisition still costs most. `affine-screen.json` applies
the existing affine checker to all 108 holdout sources without labels. It retains
14 checked negative observations, including two native budget-stopped attempts;
the screen takes 0.099 seconds before publication/persistence/replay. Original
native outcomes are unchanged, and these certificates are separate from the
SQLite union. A consistent subsystem does not settle its remaining clauses.

Resume `checkpoint.json`. Next: integrate that source-checked affine-negative
probe under a budget, with a fresh split and complete costs, then investigate
transport of committed conditioned residuals across edits. Nine new tests cover
proof emission, limits, failed candidates, tampering, rollback and cold replay.
`checks.json` records full/focused suites, manuscript build, 64 unchanged proof
blocks and the final 664-source ledger. `manifest.json` seals the artifacts.
