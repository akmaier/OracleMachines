# Case-13 transfer of the frozen pilot

The unchanged pilot closes case 13, but repeats the control's proof with ten
extra patterns and 51 extra probes. Structural coverage rises from 14/24 to
15/24 in both modes. This is a preserved negative transfer result; no scheduler
or solver default changes. See [analysis](../../../research/pilot-transfer.md).

From the repository root, reproduce into a fresh directory:

```sh
python3 experiments/compare_cnf_pilot_transfer.py /tmp/cnf-pilot-transfer-reproduction
python3 experiments/validate_cnf_pilot_refinement.py /tmp/cnf-pilot-transfer-reproduction
```

The validator is deliberately the frozen parent validator. The new driver reuses
the parent worker and scheduler byte-for-byte, preserving all policy parameters,
limits and paired orders. `protocol.json` binds the parent policy, history,
original, source ledger and acquisition-free preflight. Source fingerprints make
these commands fail rather than silently use changed sources.

`report.json` retains all four fresh-process streams and exact counts.
`reconstruction.json` records independent full replay, original bindings, cold
pilot recovery and shared budgets. `comparison.json`, both explanations and both
target proofs expose the identical proof and extra unused trial. `checkpoint.json`
binds the conflict-checked union, full catalog and 844-step proof for fifteen
originals. `next-discovery.json` points to the connected case-21 mixture.

All four trial archives and the union preserve earlier states and every new
trial result. The union has 2,215 patterns, 224 pairs and seventeen inherited
missing children. Nine originals remain unknown. Whole-runtime pair rankings
are mixed: the clear increase in expansion work does not establish a consistent
end-to-end slowdown or speedup. Complete auditing dominates measured time.

`tests.txt` records 367 passing tests; `test-command.txt` gives the exact command.
`validation.json` binds preservation checks, policy equality, identical proofs,
inserted-operation checks and manuscript build results. `manifest.json` hashes
every artifact in this directory except itself. Benchmark timing excludes tests,
retrospective validation and the separately recorded preflight.
