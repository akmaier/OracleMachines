# Rejected clause-support cache: initial pilot

Eight fixed sources, current indexed-restriction baseline versus independently
cached immutable clause supports. Discovery increases **2.42915 -> 2.77177 s**;
total increases **2.57045 -> 2.91654 s**. Outputs, profiles, roots and database bytes
agree, and both archives replay cold without mutation. This sequential pilot
does not establish significance or full-workload behavior.

Source snapshots and the exact runner override are bound by `invocation.json`.
The original report uses the restriction-study runner and its inherited description;
this file and the invocation record describe the actual candidate. No later edits
overwrite these snapshots. The separate revised pilot batches counters and compares
sets directly; it still regresses. The cache remains unselected.
