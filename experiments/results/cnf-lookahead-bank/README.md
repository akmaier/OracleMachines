# Lookahead probe bank and negative selection result

See [the analysis](../../../research/lookahead-bank.md), `protocol.json`,
`seed.json`, `report.json` and `reconstruction.json`. All 24 inputs were frozen
before acquisition. At depth-zero preparation, 22 have no saved source pairs;
only two support this comparison. The bank avoids 36 repeated probes but the
lookahead score adds 34 probes over size ranking and no structural coverage.
All unknowns and eight arm archives are retained. This is an optional experiment,
not a default planner change or an unrestricted SAT result.

```sh
python3 -m unittest solver.test_cnf_lookahead_bank
python3 experiments/compare_cnf_lookahead.py /tmp/cnf-lookahead-new
python3 experiments/validate_cnf_lookahead.py /tmp/cnf-lookahead-new
```

Use a new output directory. Validation writes its report, so copy this immutable
bundle before replaying. Archives with banks can be read by `LookaheadInventory`;
all bank proofs require the original exact-source checker on cold reuse.
