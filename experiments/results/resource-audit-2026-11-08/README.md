# Read-only resource audit, 8 November 2026

[The complete analysis](../../../research/resource-bounds.md) covers formal work,
logical payload, physical-memory gaps, archive growth and expansion costs.
`snapshot.json` pins code revision `fe7d767`, records the immutable source hashes,
SQLite page/object inventory and local cache allocation, and recomputes width-32
phase medians from the preceding five-repetition affine experiment. It adds no
new timing measurements and does not modify the solver or its old evidence.

The expanded affine budget formula was checked against the definition for every
supported width (1..128) at row counts 0, 1, b and 4,096. Its equality is an
algebraic restatement; this numeric check is not an additional Lean theorem.
The linked Lean constructor and bound theorems remain authoritative. Default-cap
payload estimates count logical cells, overcount shared references and exclude
metadata/temporary allocations. They must not be read as bytes or RSS bounds.

Phase medians need not sum to the median total. Python-process RSS and statistics
for reaped children do not provide the simultaneous peak of live native workers.
The local cache disk total includes all retained experiment databases and backups.
No old result, proof, source row or experiment artifact was deleted or rewritten.
