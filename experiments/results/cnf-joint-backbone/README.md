# Shared discovery and joint conditioning of binary consequences

See [the interpretation](../../../research/joint-binary-consequences.md),
`protocol.json`, `analysis.json`, `next-target.json` and the sealed
`checks.json`/`manifest.json`.

The optional recognizer shares one source-bound graph, examines at most eight
ranked target variables, and retains at most two checked paths. Values already
implied by the first survivor are skipped. This is directional redundancy
filtering, not a minimum basis. Joint conditioning checks intermediate cached
answers before deeper acquisition; existing unit and split rules certify every
new native node, including paths conditioned by earlier assignments.

The exposed branch and two sign variants take four instead of nine expansions.
The original saves 24.10% query time and 24.86% native payload. A posthoc ablation
with the same discovery but one selected path takes six expansions. Six new edits
fall from 58 to 55 expansions but regress 4.05% in query time and grow native
payload 8.65%. Every regression is retained; defaults remain unchanged.

Reproduce in a separate directory, preserving this frozen checkpoint:

```sh
mkdir experiments/results/cnf-joint-backbone-reproduction
python3 experiments/probe_cnf_joint_backbone.py experiments/results/cnf-joint-backbone-reproduction
python3 experiments/compare_cnf_joint_backbone.py prepare experiments/results/cnf-joint-backbone-reproduction
python3 experiments/compare_cnf_joint_backbone.py experiments/results/cnf-joint-backbone-reproduction
python3 experiments/analyze_cnf_joint_backbone.py experiments/results/cnf-joint-backbone-reproduction
python3 experiments/profile_cnf_joint_backbone.py experiments/results/cnf-joint-backbone-reproduction
python3 experiments/validate_cnf_joint_backbone.py experiments/results/cnf-joint-backbone-reproduction
```

Complete serial timing before profiles, tests and cumulative audits. The frozen
protocol binds 15 targets, 54 workers and 90 attempts; all targets are UNSAT under
all policies. Each seed excludes its queried root. Donors/maps and earlier
acquisition remain supplied. Source coverage is unchanged.

Both native readers check the cumulative 75,896 native records, all older
extensions and 282 partition records. All 1,468 full and 176 focused tests pass;
the full suite retains 44 unclosed-SQLite warnings, and focused tests emit none.
The 242-page manuscript builds without warnings and retains all 64 proof blocks.
There is no new Lean refinement theorem. The final ledger binds 763 source files.

The next gap is recognizing when a forced value yields a cheaper full-CNF
continuation. Case 31 improves; case 61's new deletion rises from four to seven
expansions and more than doubles query time, with changed proof availability for
the following replacement. Use protocol prefix `61` and the bound
`novel-61-{mode}-0` streams for that counterexample. `next-target.json` binds
profiles and source-indexed paths for the exposed branch and largest new query;
restore its exact prefix plus only listed earlier trial IDs. The final union
contains the answers and must never seed these comparisons.
