# Incremental split-route checking

Read [the analysis](../../../research/incremental-split-checking.md). The two arms
use the same enumeration policy and frozen 24-input stream. Only maintenance of
the checked external split catalog changes.

- `protocol.json` binds the prior seed, inputs, enumeration result and complete
  union checkpoint, with three alternating arm orders and implementation hashes.
- `report.json` contains paired timing and verification counts. Each of six arm
  directories retains its database and per-query counters.
- `diagnostic/` retains a separate profiled run. Its timings are excluded from
  the benchmark means; cumulative profile timings overlap.
- `reconstruction.json` checks all seven trial archives, the seed and the prior
  union with no fresh acquisition. Every trial database and proof equals the
  prior enumeration baseline. Cold registries check 86 pairs; unchanged refreshes
  recheck none.
- `next-discovery.json` identifies the largest unresolved query, case 16, with
  exact source/branch bindings to the existing union. This is a discovery pointer,
  not a new standalone solver checkpoint.
- `validation.json`, `manifest.json` and logs preserve the full validation and
  prior-artifact audit. The initial external-writer test log uses a no-op SQL
  update; the corrected test makes an actual payload edit.

Reproduce into a new directory from the repository root:

```sh
python3 experiments/compare_cnf_split_registry.py /tmp/split-registry-reproduction
python3 experiments/profile_cnf_split_registry.py /tmp/split-registry-reproduction/diagnostic /tmp/split-registry-reproduction
python3 experiments/validate_cnf_split_registry.py /tmp/split-registry-reproduction
```

Continue solving from the unchanged parent
`experiments/results/cnf-bootstrap-conditioning/checkpoint.json`, using
`experiments.validate_cnf_bootstrap.restore_checkpoint`. The union still preserves
1,154 patterns, 96 pairs and 5/24 coverage. The new live registry is rebuilt from
checked records; its derived state is never accepted as a cold proof.
