# Progress-gated exploration on connected case 21

The gate freezes the first route's selected unresolved literal mass before
acquisition. After one completed nested acquisition, it skips the second trial
if that mass strictly decreases or the whole query is covered. Otherwise it
uses the existing second-trial selection. Shared budgets, partial work and
cold-restart state are preserved. This is optional scheduling, not a cost bound.

The rule was proposed from cases 11/13 and frozen before case-21 acquisition.
Case 21 remains part of the existing development corpus, not a held-out test.
See [analysis](../../../research/progress-pilot.md).

From the repository root, reproduce into a fresh directory:

```sh
python3 experiments/compare_cnf_progress_pilot.py /tmp/cnf-progress-pilot-reproduction
python3 experiments/validate_cnf_progress_pilot.py /tmp/cnf-progress-pilot-reproduction
```

`protocol.json` binds the parent, original, acquisition-free preflight, sources,
unchanged budgets and the gate. Two reversed-order triples compare committed,
always-pilot and gated policies. Every timed worker reconstructs independently.
`report.json` retains all six streams and exact measurements.

`reconstruction.json` records independent full replay using the frozen full
checker, positive query proofs, original bindings, complete catalogs, immutable
prefixes, cold scheduling state and shared budgets. `comparison.json` and all
three explanations and proofs expose reuse and unused exploratory work.

The gate matches committed operations, proof and SQLite/gzip bytes. Compared
with always-pilot, it reduces new patterns from 32 to 24 and probes from 175 to
100. Both whole-runtime pair rankings and limited replication constrain timing
claims. The always-pilot proof is one step shorter but costs more to acquire.

The union retains all 48 distinct new patterns and nine split records, totaling
2,263 patterns and 233 pairs, with seventeen inherited missing children and an
884-step structural coverage proof for 16/24 originals. Eight remain unknown.
`next-discovery.json` binds case 10 for the next investigation.

`tests.txt` records 372 passing tests; `test-command.txt` gives the command.
`targeted-tests.txt` records five focused tests. The initial implementation's
method-rebinding error, failed test and source are retained separately; the
fix predates every measured case-21 acquisition. No such failed run is included
in the benchmark. `validation.json` binds preservation, measurements, repeated
identities and the manuscript build. `manifest.json` hashes every artifact in
this directory except itself. Tests, retrospective replay and preflight are
outside the operational timing. Earlier acquisition remains in parent records.
