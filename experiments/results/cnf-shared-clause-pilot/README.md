# Rejected clause-support cache: revised pilot

The cache now batches common counters and intersects frozensets, avoiding repeated
iteration through the whole assignment dictionary. Discovery still increases
**2.39739 -> 2.64530 s**; total **2.54089 -> 2.78956 s** on the same eight queries.
All outputs and archive bytes agree, including cold replay. It has 358,109 clause
hits, but 194,785 admissions/preparations over 552,894 clause positions; these
savings do not repay the measured overhead. This is a sequential pilot, not
full-workload or significance evidence.

`invocation.json` binds the exact source snapshots and runner override. Its base
report inherits the earlier restriction-study description, so use this record
for interpretation. The revised cache remains available for controls/tests and is
not selected by `SinglePassCheckInventory` or the default inventory.
