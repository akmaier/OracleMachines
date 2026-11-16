# Checked UNSAT reuse across a clause deletion

A separately verified UNSAT premise forces all literals of a deleted clause
false. The optional wrapper solves only that cofactor, verifies lifted SAT
models, and retains the old negative premise for UNSAT replay. Structural
coverage is not used as an UNSAT answer.

On twelve constructed edits, new reference residual nodes fall 502 -> 427 and
measured complete stream time falls 8.11%. Cases 15 and 17 supply most gains;
case 13 has no node saving, and case 7 uses more splits. SAT premises correctly
fall back to ordinary solving. See [analysis](../../../research/clause-deletion-guard.md).

Reproduce into a fresh destination, from the repository root:

```sh
python3 experiments/compare_cnf_clause_deletion_guard.py /tmp/cnf-clause-guard
python3 experiments/validate_cnf_clause_deletion_guard.py /tmp/cnf-clause-guard
python3 experiments/analyze_cnf_clause_deletion_guard.py /tmp/cnf-clause-guard
```

`protocol.json` fixes the histories, limits and modes before preparation.
`seed.json` binds the separately acquired 613-node reference history; acquisition,
cold audit and compression cost 0.91359 seconds. Each stream retains every
reference row and query sidecar. Cold validation disables fresh search and
checks all nodes, witnesses and negative certificates. All 382 tests pass.

`checkpoint.json` preserves the prior structural archive and both its catalogs,
with no new structural rows: 2,614 patterns / 259 pairs, 17/24 original coverage
and separate 24/24 supplemental coverage. Its `reference_study` descriptor binds
this decision experiment. Retain both reference snapshots and the guard sidecars;
a guarded UNSAT conclusion requires its bound old premise and its cofactor proof.

`analysis.json` records the case-13 partition diagnostic, the unrestricted
exceptional-cofactor construction, and six checked SAT witnesses that already
satisfy their edited inputs. Positive witness reuse is the next implementation
target. More compact sidecars and broader workloads remain open. This wrapper
is not enabled in the structural planner or production solver.
