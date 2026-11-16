# Bounded model rotation on 257 unseen deletions

The guarded-plus-rotation stream reduces fresh expansions 1,876 -> 1,509 and
complete time 7.16% against the guarded control. It publishes 57 checked SAT
certificates. All modes return 72 SAT / 185 UNSAT. See the
[analysis](../../../research/model-rotation.md) for the full cost table,
known-positive selection, retained failures, memory growth and limitations.

Reproduce into a fresh directory from the repository root:

```sh
python3 experiments/compare_cnf_model_rotation.py /tmp/cnf-model-rotation
python3 experiments/validate_cnf_model_rotation.py /tmp/cnf-model-rotation
python3 experiments/analyze_cnf_model_rotation.py /tmp/cnf-model-rotation
```

`protocol.json` freezes the 1,169-key parent union, input-selection rule, 64-flip
per-template budget, 329 runtime source fingerprints and balanced mode order.
`cases.json` retains all 257 selected and three excluded inputs. Nine complete
streams retain query sidecars and compressed databases. `rotation.json` retains
every attempted flip, its failed clauses, chosen models, origins and cursors.
The budget applies to the entire stream, not each query. No engine-state import
API is claimed; independent cold replay checks the saved evidence.

`reconstruction.json` records cold verification of 4,626 query replays, all
rotation evidence, all union nodes and the inherited structural catalogs.
`cost-attribution.json` is a separately bound post-hoc analysis, retaining the
largest costs and per-query regressions (none in fresh expansions on this order).
UNSAT inputs account for 1,216/1,509 remaining expansions. Small checked UNSAT
proof supports or common negative cofactors are the next discovery target.

`checkpoint.json` retains the unchanged structural authority and all earlier
reference study/decision bindings. Its `reference_union` grows to 9,104 keys;
`model_rotation_study` binds this report and `model_rotation_decisions` binds
257 actual query decisions. Earlier payloads win ties; 81 alternative certificate
occurrences remain in immutable trial archives. Original structural coverage
stays 17/24, separate supplemental coverage 24/24. No unrestricted-SAT
polynomial-time or new structural-family coverage claim follows.

All 394 tests pass. Preservation checks retain 325 earlier source files, 3,669
artifacts across 64 manifests and 64 proof blocks. The manuscript builds to 189
pages. The final source ledger adds the post-hoc analyzer, for 330 sources.
