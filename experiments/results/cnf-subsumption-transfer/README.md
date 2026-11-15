# Subsumption transfer and the early-family control

A frozen 42-input synthetic stream tests transfer from the shared eighteen-variable
component. Twelve variants reuse its checked proof, but its minimum is already
**2-CNF (16/18/36)**. The separately frozen supplemental control shows the stronger
result is **early family exposure**, not demonstrated reuse of a nonterminal core.

In the supplemental comparison, early family recognition handles 33 inputs before
probing, reduces fresh probes **1,022 -> 503**, reduces new stored patterns
**197 -> 107**, and reduces working SQLite bytes **2,510,848 -> 1,466,368**. Mean
preparation plus queries is **0.49636 -> 0.38107 s**. All arms cover **41/42**;
case 41, a fresh 48-variable CNF, remains unknown and dominates cost.

[Full analysis and limitations](../../../research/subsumption-transfer-controls.md)
include the preserved preflight failure, incidental warm-reuse regression, the
post hoc control, and an admission-accounting correction: fused conditioning
records states outside the inherited `_discover` ledger. Its cap is not a total
bound on all recognition work. All **318 tests** and independent replay pass.

Reproduce into fresh directories:

```sh
python3 experiments/compare_cnf_subsumption_transfer.py /tmp/cnf-transfer-new
python3 experiments/validate_cnf_subsumption_transfer.py /tmp/cnf-transfer-new
python3 experiments/compare_cnf_early_subsumption.py /tmp/cnf-transfer-new/family-control --parent /tmp/cnf-transfer-new/report.json
python3 experiments/compare_cnf_early_subsumption.py /tmp/cnf-transfer-new/family-control --validate
python3 -m unittest solver.test_cnf_subsumption_transfer solver.test_cnf_early_subsumption
```

Each experiment freezes its policy before its own timed acquisitions. All saved
queries and fallback states persist in the twelve archives. `protocol.json`
contains the unchanged inputs; `template-proof.json.gz` is positive-proof-only.
`reconstruction.json` includes initial costs and the admission audit; the nested
control has its own report and reconstruction. Neither is a replacement for the
full discovery checkpoint, an unbiased benchmark, or an arbitrary-SAT guarantee.
