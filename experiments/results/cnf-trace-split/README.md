# Saved cofactor traces: 52/83 to 53/83 coverage

Implementation checkpoint: `267d5c4`. Parent:
`experiments/results/cnf-learning-batch/report.json`. The complete account is in
[saved-trace-splitting.md](../../../research/saved-trace-splitting.md).

- Case 2 (`holdout3`, n32, original 894) gains a complete structural plan and an
  independently checked SAT witness. All 53 closures survive removal of the
  growth-exception routes. These are reused development cases.
- The selected ten-variable / 51-clause source exhausts ordinary single-assumption
  unit refutation. Two existing clear traces nevertheless describe useful
  cofactors. Both branch plans are required; recognition adds five pattern nodes.
- Five saved pairs are ranked. Variable 5 is selected; both cofactors are new
  to the pattern history. No state cap binds. One new clear ordinary window and
  one external split record are retained, along with all previous evidence.
- 581 tests pass, including exhaustive ten-variable source/cofactor checks.
  Standalone validation disables discovery, checks candidate selection, confirms
  both branch transports and leaves the final history/reference bytes unchanged.
- The matched warm control shows **no speedup**: saved replay 0.50192 ms versus
  fresh propagation/checking 0.46004 ms in one measurement. Two fresh assumption
  traces are avoided, but reference decoding/checking still costs time.
- Complete pipeline: 263.25700 seconds. Standalone validation: 148.83131 seconds.
  Preparation and cold checking dominate. Peak RAM remains unmeasured.

`report.json` binds parent, code and archives by hash. `splits.json.gz` holds the
two-polarity source references and exact child bindings. `diagnostics.json.gz`
retains the final ordinary probe, exhaustion evidence, all ranked candidates,
the matched control and the remaining targets. `proof-delta.sqlite3.gz` adds five
pattern rows and one window; all older rows remain unchanged. `coverage.json.gz`
is the finite original-level composition witness. `reference.sqlite3.gz` extends
the old proof archive from 1,156 to 1,175 nodes without changing any old proof row.
The full test log, independent validation and execution log are retained alongside.

Working SQLite adds 65,536 bytes and reaches 768,663,552 bytes. It contains 41,664
pattern nodes, 80 ordinary windows and 108 continuations. External evidence
includes 41 learning bases, 150 augmented blocks and this one split. External
proof, diagnostic and reference archives are additional storage.

Restore with `compare_cnf_trace_split.restore_checkpoint`. Build
`ContinuedLearningRoutes` using the returned rewrites, learning bases and
augmented blocks, then attach each returned split using `cnf_trace_split.attach`.
Earlier loaders omit the new coverage route. The next targets have 33, 33, 36
and 38 variables; compare their saved cofactors with further lookahead under
explicit acquisition caps. Re-filter the preceding batch's 18 ready bases before
continuing their 92 remaining ranked variables.

The preserved pilot is `../cnf-small-target-pilot.json`, including unsuccessful
consequence/learning checks and a corrected exploratory helper-call TypeError.
The split is standard exact conditioning with extra charged expansion, not a
new polynomial-time SAT result or a globally minimum-cost construction.
