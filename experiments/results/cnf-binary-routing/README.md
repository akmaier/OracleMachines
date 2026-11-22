# Checked cofactor priority and a polarity counterexample

See [the research account](../../../research/binary-routing.md).

`exploration/` retains an instrumented comparison from identical persistent
prestate, reproducing 10/35/33 expansions under the earlier three rankings.
These times are excluded from the performance comparison. The frozen
`protocol.json` then compares original, binary-frequency and cofactor-priority
policies on six prior controls, two isolated branches and six new local edits.
Every seed excludes the target answer.

Worker directories retain native proof deltas, query traces, checked partition
sidecars, warm results, restoration, cold replay and reconstruction measurements.
`analysis.json` retains paired orders and individual regressions.
`next-target.json` records the first later routing divergence and a checked unit
refutation of the unprobed true cofactor. Its exact prestate consists of the
regression prefix plus one earlier row from the bound priority trial delta.

A brief diagnostic overlapped the last timing stratum. Both orders and every
policy for novel case 61 were repeated together after the diagnostic finished.
`first-pass-report.json` and the original worker directories remain intact;
`timing-repeat.json` binds the replacement samples and confirms identical proofs
and decisions. No faster-sample selection was used. `diagnostic-first-attempt/`
preserves an assertion failure caused by comparing SQLite tuple rows with JSON
list rows; normalization fixed the diagnostic without changing the timed policy.

`validation.json`, `checks.json`, `checkpoint.json` and `manifest.json` bind the
chronological proof audits, cumulative preservation, tests and manuscript build.
The general solver defaults remain unchanged.

Reproduce into a new directory from the repository root:

```sh
mkdir /tmp/oracle-routing-repeat
python3 experiments/inspect_cnf_binary_routing.py /tmp/oracle-routing-repeat/exploration
python3 experiments/compare_cnf_binary_routing.py prepare /tmp/oracle-routing-repeat
python3 experiments/compare_cnf_binary_routing.py /tmp/oracle-routing-repeat
python3 experiments/analyze_cnf_binary_routing.py /tmp/oracle-routing-repeat
python3 experiments/diagnose_cnf_binary_routing.py /tmp/oracle-routing-repeat
python3 experiments/validate_cnf_binary_routing.py /tmp/oracle-routing-repeat
```

Use the preserved protocol for exact input comparisons. Never reconstruct these
trials from the final cumulative union, which already contains their answers.
