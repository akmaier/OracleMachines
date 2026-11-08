# Preserved initial pattern-inventory experiment

This is the first completed 664-input, five-policy comparison. Its exact
implementation, runner and test file are saved alongside `report.json` and all
five compressed databases. The later checker adds direct reconstruction of
parent clauses and disjoint-support verification independently of component
discovery, plus a test injecting a faulty discoverer. The first run contained
valid partitions; it is retained rather than overwritten or mixed with final
measurements. Every archive passes the final checker unchanged.

Use [the final study](../cnf-pattern-inventory/README.md) for current measurements,
scope, limitations and the next discovery target. Original source fingerprints
in this report correspond to the local snapshots where the files changed; the
unchanged solver and matching generator remain at their repository paths.
