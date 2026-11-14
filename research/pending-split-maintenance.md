# Pending splits can preserve an unchanged route catalog

The preceding combined-policy experiment spent about one second rebuilding the
route catalog after an interrupted split that stored no pattern or probe row.
Five recognizer states had been entered, but neither child root existed. This
study tests a guarded update for that case and then resumes the saved frontier.

## Condition for exact reuse

`PendingSplitMaintenance` extends the clear-probe helper. It first checks the
same SQLite connection, schema and external-write versions. Its additional path
requires zero database writes since the last snapshot, an exact account of newly
entered states, and an unchanged sidecar bundle except for adding or reusing the
reported split. It verifies both saved polarities and their canonical child
bindings with the existing checker. At least one child root must be absent.

Under the complete builder's existing `cnf_trace_split.attach` rule, a split
with an absent child contributes no route. Zero database writes preserve the
availability of every earlier target, and the unchanged other sidecars preserve
their routes. The reported split therefore leaves the active catalog unchanged.
The helper updates its sidecar snapshot, while the caller retains the checked
split in the scheduling evidence. Both targets remain obligations. No inference
from missing data, a clear probe, or a reference SAT answer establishes closure.

Any database write takes the existing rebuilding path, including acquisition
that makes a previous split usable. Unrelated sidecar changes also rebuild.
External writers or schema changes require reopening the checked inventory,
because rebuilding routes alone would not invalidate its node caches. This is
an optional in-process optimization for append-only history, not a serialized
trust cache or a new SAT recognizer.

This invariant does not depend on the source's SAT category. Its applicability
depends on the actual state change: a split that stores even one new child row
must take the general path in this implementation.

The additional guard charges serialization of the supplied and expected
sidecars, parsing the prior snapshot, exact split checking, target lookups and
admission-set comparisons. With sidecar size B, its work includes O(B), plus the
split checker and database lookups; it is not constant-time. It retains one
serialized snapshot as before and uses temporary parsed/serialized copies.
The experiment measures serialized payload sizes, not peak RAM. General
preparation and refresh after genuine acquisition remain open costs.

## Matched comparison

Both modes use early saved-pair scheduling, twelve advances and a single shared
32-state allowance per worker. The baseline uses `ClearProbeMaintenance`; the
candidate additionally handles inactive pending splits. Two repetitions reverse
mode order. Each worker owns an independent copy of its seed. Preparation,
acquisition, route maintenance, coverage, export and checking are charged;
authority reconstruction and union/global validation are reported separately.

The interruption control starts at the previous 38/158/500 exhausted source and
reproduces the earlier exact operation sequence. The resumption workload starts
from the preserved combined-policy union, follows its pending variable-26 split
of 30/116/363, and retains the separate 33/130/400 leaf. No budget is reset between
the two polarities or subsequent descendants. The union preserves all work from
both modes; it is not a single 32-state run.

Independent cold replay forbids fresh recognition and reference search. In the
first repetition of each mode it inserts only the rows available after each
advance, compares the complete maintained catalog with a fresh build, and checks
coverage and exact next selections. It also checks repeated operations, logical
tables, both polarities, SAT model lifts, idempotent deltas and preserved history.

## Measurements and retained progress

| Metric | Interruption: clear only | Interruption: pending guard | Resume: clear only | Resume: pending guard |
|---|---:|---:|---:|---:|
| Advances | 4 | 4 | 3 | 3 |
| Admitted states | 32 | 32 | 32 | 32 |
| Stored new patterns | 27 | 27 | 19 | 19 |
| Entered but unstored | 5 | 5 | 13 | 13 |
| Full route rebuilds | 4 | 3 | 3 | 3 |
| Mean expansion seconds | 4.71930 | 3.59923 | 3.54491 | 3.54578 |
| Mean worker seconds | 17.55753 | 16.15178 | 16.54782 | 16.37384 |
| Mean preparation seconds | 7.89928 | 7.81436 | 8.21124 | 8.06703 |
| Mean export seconds | 4.85609 | 4.65810 | 4.70976 | 4.67958 |
| Compressed delta bytes | 20,877 | 20,877 | 12,874 | 12,874 |

For the interruption, the final update falls **1.08509 -> 0.01138 s**, including
the new guard. Mean expansion falls **23.73%** and complete worker time **8.01%**.
The three earlier acquisition updates still rebuild. The two modes perform the
same work and leave the same pending obligations; this measures the maintenance
cost of that bounded run, not completion of the original. Preparation/export
variation contributes to the whole-worker difference. The maximum serialized
sidecar snapshot is **1,276,209 bytes** in both modes, and persistent deltas are
identical. No persistent space reduction is claimed.

The resume workload is a useful negative control. Every advance stores patterns,
so all three updates rebuild and expansion time is effectively unchanged.
The small observed worker difference supplies no evidence of a maintenance gain
there. The snapshot reaches **1,310,948 bytes**. Reconstructing and preparing the
large authority, as well as refresh after real acquisition, remain substantial.

The original variable-26 split of **30/116/363** resumes with nine admissions:
eight for the false **29/108/336** cofactor and one for the true **19/54/140**
cofactor. A remaining **23/81/253** leaf splits at local variable **13**, using
eight more states. Work then reaches the separate **33/130/400** leaf. Its
local-variable-18 split acquires the false **29/96/275** cofactor with two states,
then enters thirteen states in the true **30/111/330** descent without storing
any of those thirteen ancestor plans. The false child is available; the true
child root remains absent. The shared 32-state budget is preserved throughout.

The two new splits expose complementary reuse. The variable-13 false cofactor
**20/60/170** reaches the stored contradiction terminal in one probe reduction;
the variable-18 false cofactor reaches that same terminal through
**29/96/275 -> 21/59/153**, in two. That terminal is the CNF containing an empty
clause, not the satisfiable empty CNF reached by the old variable-26 true branch.
The variable-13 true cofactor follows
**20/67/190 -> 14/30/74 -> 12/21/51 -> 11/16/38 -> 10/14/33**, then a binary-path
reduction and polarity change reach the **10/10/21** Horn certificate. These are
checked reductions of the same source, not interchangeable formulas without
their transports. Independent reference answers for both new splits are
UNSAT on false and SAT on true. The pending true cofactor is therefore a missing
structural certificate even though its reference decision answer is known.

The union adds **19 patterns**: nine probe reductions, four eliminations, three
binary-path reductions, one unresolved leaf, one polarity transformation and
one family certificate. The transformed **10/10/21** residual is both Horn and
zero-valid; those recognitions overlap rather than defining disjoint classes.
The original residual requires the checked polarity transport. The union adds
**two split sidecars** and no external probe
records. Historical-control rows are already in the parent union and are not
counted again. Structural coverage remains **65/83**, with the same **3,239-step**
positive certificate. The retained frontier now has **one pending target and
no acquired open leaf**; three split records still depend on that pending work.

History grows **237,568 bytes** to **775,004,160 bytes / 42,039 patterns**. The
union delta is **307,200 SQLite bytes / 12,874 compressed bytes**, excluding
sidecars and reference evidence. The producer costs **368.96634 s**, including
**72.00904 s** for current restoration, **67.51801 s** for the historical control,
and **68.15113 s** for final route preparation/global coverage. Union export
costs **5.79921 s**. The reference archive preserves all **3,422** previous nodes
and grows to **3,467**. Reference answers do not supply structural coverage.

## Resume and next bottleneck

Resume `experiments/results/cnf-pending-maintenance/report.json` through
`compare_cnf_pending_maintenance.restore_checkpoint`, report SHA-256
`9a48fc85512e52c566dd60f0396a4bacf842b48267ee47606394d271d221f8d0`.
Keep the five evidence lists **(1, 42, 156, 40, 1)** and the separate **two
bridges**, using bridge-aware `routes_for` and
`cnf_projection_bridge.verify_positive`.

The scheduler resumes the exact local-variable-18 split of **33/130/400**,
source SHA-256
`1fab57607093cb833cc8fa0f21d88c2e7e9eb094dac7cdd416e8a786e3fcf056`.
Its true target **30/111/330** is absent, SHA-256
`5124e2d5f451e42b274ed6886d29676c94f89e27bb3054f77b530f2f3091a3a4`.
Reuse its acquired false child and charge reentry of the thirteen unstored keys;
do not rerank the pending split or treat interrupted plans as coverage.

For runtime, the larger remaining opportunity is updating only routes affected
by genuine acquisition. This needs complete dependency tracking across probe,
split, family and projection routes, including activation of old pending edges.
The current conservative helper does not attempt it. Acquisition in the final
resume advance costs about **0.06 s**, against **1.08 s** for rebuilding. A
recognizer continuation may save repeated admission work, but its bookkeeping
must be compared with that measured cost rather than with state counts alone.

## Reproduction

From the repository root, using a fresh output directory:

```sh
python3 experiments/compare_cnf_pending_maintenance.py experiments/results/cnf-pending-maintenance
python3 experiments/validate_cnf_pending_maintenance.py experiments/results/cnf-pending-maintenance
```

Run timed production and cold replay without concurrent tests or paper builds.
These are adaptively selected development workloads, with two repetitions and
shared process/OS caches. They do not establish a holdout estimate, a globally
minimal expansion strategy, or an efficient decomposition of arbitrary SAT.

Independent cold replay passes in **487.75798 s**, with all **3,467 reference
nodes** checked and no fresh recognition or reference search. All eight workers
have identical operations and logical results within each workload. Four
stepwise prefix replays compare complete maintained and fresh catalogs,
coverage and next selections using only then-available rows. All five previously
interrupted states are reentered and now stored; thirteen new unstored states
remain explicit.

Verification: **215 tests pass** (209 prior plus six new regressions). The
manuscript builds to **159 pages**, preserving all **64 proof blocks** exactly,
with no overfull boxes or undefined references. All **865 prior artifacts in
20 manifests** remain hash-identical. The new manifest binds **104 artifacts**
(3,977,775 bytes), including matched operations, deltas, independent findings,
reference results and logs. SQLite ResourceWarnings in the passing suite and
the initial external-write fixture correction are recorded in validation
metadata. No completed result or earlier experiment was removed.
