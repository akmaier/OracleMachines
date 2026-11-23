# Direct handoff of prepared cofactor work

See [the research record](../../../research/cofactor-handoff.md), `protocol.json`
and `analysis.json`. This study passes an immutable normalization and optional
unit-propagation result directly from a probe to its selected child. It preserves
discovery priority and all native proof checks. Nonconflicting propagation grants
no answer authority. The old content-indexed memo and its regression are retained.

The three arms are binary-frequency routing, two-polarity routing and two-polarity
routing with the handoff. Fifteen targets run in 54 serial workers in two opposite
orders, yielding 90 attempts. Trials restore exact pre-target prefixes, never the
final cumulative archive. Six controls are preceding edits; six fresh nearby edits
have roots absent from the prior union; three exposed sign variants are unchanged.
Donors/maps remain supplied. This measures acquisition, not wider SAT coverage.

`validation.json` audits chronological dependencies, exact proof/model equivalence,
old controls and cumulative preservation. `next-target.json` binds the most costly
fresh handoff query, paired profiles and a separate audit of live offer graphs.
`checkpoint.json`, `checks.json` and `manifest.json` preserve the verified state.

The six new edits reduce query time **2.66%** versus two-polarity routing, with
both orders improving, while complete worker time changes **+0.15%** with mixed
signs. Proof storage is unchanged; expansion counts are 55 for both arms versus
53 for binary-frequency routing. All regressions and timing-order differences
remain in `analysis.json`. The selected stream builds the same partition structure
four times per query, motivating the next preparation-sharing experiment.

The union contains **75,416 native records**, adding 74 unique nodes and retaining
42 alternate-payload observations in trial deltas. All **1,428 tests** and **136
focused tests** pass; full tests retain 44 existing SQLite warnings, focused tests
emit none. Both readers replay cumulative authority and current/earlier sidecars.

Reproduce in a new directory:

```sh
mkdir experiments/results/cnf-cofactor-handoff-reproduction
python3 experiments/compare_cnf_cofactor_handoff.py prepare experiments/results/cnf-cofactor-handoff-reproduction
python3 experiments/compare_cnf_cofactor_handoff.py experiments/results/cnf-cofactor-handoff-reproduction
python3 experiments/analyze_cnf_cofactor_handoff.py experiments/results/cnf-cofactor-handoff-reproduction
python3 experiments/profile_cnf_cofactor_handoff.py experiments/results/cnf-cofactor-handoff-reproduction
python3 experiments/validate_cnf_cofactor_handoff.py experiments/results/cnf-cofactor-handoff-reproduction
```

Finish serial timing before profiling, tests or CPU-heavy audits. Query time
includes the handoff session and cleanup. Complete worker time also includes
checking, persistence, warm reuse and cold reconstruction. Prior acquisition is
sunk. The 256 KiB cap covers retained offers, including active ancestors, but
excludes transient preparation, control fields and other solver/process memory.
All proof bytes, decisions and expansion counts must match the two-polarity arm.
General defaults remain unchanged; no uniform arbitrary-SAT bound is claimed.
