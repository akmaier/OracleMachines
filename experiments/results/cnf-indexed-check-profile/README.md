# Reconstruction reuse: profile, capacity control and failed pilots

The source-1194 profile uses the prepared archive and starts with cold caches.
`profile.json` binds the earlier full report and profiling script. Its base runtime
is `3d032ef`; the new index is checkpoint `f6fb244`. The shared-restriction extension
is bound by its file hash. No earlier experiment is replaced.

- `profile.json`: 2,617 single-pass reconstruction calls, 0.33136 own seconds,
  0.48292 cumulative seconds, 3.08000 instrumented query seconds. Normalization
  is second by own time. Cumulative times overlap; this is not a performance ratio.
- `budget-diagnostic.json`: 32,768 versus 1,048,576 slots. Across both checker
  views, hits remain 80/2,617, admissions 2,537 and preparation literals 858,647.
  Retained entries grow 23 -> 1,002. Capacity alone does not help this case.
- `sharing-pilot.json`: previous / indexed / indexed-plus-restriction-memo times
  are 1.12695 / 1.17052 / 1.19950 seconds. All roots/profiles/summaries match.
  The combined prototype gets 498/3,231 restriction hits and 141/2,617 checker
  hits. Its preparation still visits 838,245 literals. No saving is demonstrated.
- `identity-diagnostic.json`: a separately instrumented no-eviction run holds
  all 2,537 source identities in 2,215,640 index slots, with 80 hits. There are
  2,167 exact CNF values (1,797 occurring once and 370 under two identities).
  Whole-source interning could avoid at most 370 duplicate admissions here,
  before paying its own costs. The observer's extra sets are analysis memory.
- `diagnostic-provenance.json` and `validation.json` bind source/report hashes,
  both complete control archives, test logs and unchanged manuscript proofs.

The next target is checked reuse across related but unequal residuals: unchanged
clause blocks and small assignment deltas. The earlier clause-support cache already
regressed, so a new design must justify cheaper recognition/maintenance and preserve
clause order, unit-reason positions and all source obligations. Structural interning
is a limited candidate, not an implemented speedup. Default behavior is unchanged.

All 490 Python tests and the unchanged Lean audit pass (4,148 declarations / 1,988
theorems). The manuscript keeps all 63 previous proof blocks and records the negative
result in section 12.74. No Lean refinement of these Python caches is claimed.

Reproduce individual diagnostics into new files:

```sh
python3 experiments/probe_cnf_reconstruction_limits.py --mode budget --output /tmp/reconstruction-budget.json
python3 experiments/probe_cnf_reconstruction_limits.py --mode sharing --output /tmp/reconstruction-sharing.json
python3 experiments/diagnose_cnf_reconstruction_identity.py /tmp/reconstruction-identities.json
```

The original budget/pilot calls were inline; the reproduction CLI preserves their
workloads. Original timings remain unchanged. Only one prepared source was profiled;
none of these diagnostics replaces a full matched prepared-corpus benchmark.
