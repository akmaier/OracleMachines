# Initial budget screening

Before implementing targeted escalation, the unchanged `MatchingRepairHistory`
was run with budgets 4,096, 8,192 and 32,768 on equivalence chains of 256,
1,024 and 2,048 variables. `report.json` preserves all nine measurements and
storage/counter results. Every case prepares a fresh file-backed SQLite history
and then appends `(1)`, using the usual materialize-and-prepare fallback.

The 1,024-variable expansion took 0.77280 s at 4,096 visits and 0.01179 s at
8,192. The 2,048-variable expansion still fell back at 8,192 (3.09153 s), but
succeeded at 32,768 (0.02359 s). These single screening samples motivated the
[full three-policy comparison](../cnf-budgeted-history/README.md), which preserves
compressed archives, adverse controls and reproducible source fingerprints.
The screening stores measurements rather than archives; its source was commit
`aa8e592`, with no implementation changes. It is not a significance estimate.
