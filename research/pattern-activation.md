# Updating checked routes after pattern acquisition

The optional `PatternActivationMaintenance` helper addresses repeated catalog
checking after real acquisition. It retains the complete, checked route catalog
and indexes routes waiting for missing pattern roots. When those roots arrive,
it updates the affected routes in the same order as the full builder. The
ordinary scheduler, admission budget, recognition algorithms and persistent
proof formats are unchanged.

## Conditions and correctness argument

The helper binds the existing complete, bridge-aware builder. At initialization
that builder checks all database routes and all five evidence lists plus the
projection bridges. Immutable rows, a single writer and exclusive ownership of
the live checked catalog are required. Callers must not mutate checked routes
or cached records between updates. An external writer or schema change
requires reopening the inventory, including its checked-node caches.

A fast update requires exact agreement between reported new admissions and
the inventory's admission-set difference. It accepts only the following
changes:

1. Pattern rows appended after the last observed pattern row ID. Every inserted
   key must be admitted and load as a checked pattern. The SQLite connection's
   `total_changes` difference must equal the number of such rows. Additional
   writes, including rolled-back writes, fail this condition.
2. For a split operation, exactly the reported, independently checked split
   added to the previous sidecars; a resumed record may already be present.
   Both polarities and their canonical transports remain mandatory.
3. For ordinary resumption, unchanged sidecars and an exact window or
   continuation record already in the checked catalog. New external probe
   records use the previous maintenance policy.

All other transitions use the existing checked maintenance path, then rebuild
the dependency index. Unsupported builders are rejected. This is an in-process
optimization, not a persistent trust cache or permission to overwrite old rows.

For each pending conditional route, the reverse index stores every missing
target key. Its route types are probe windows, probe continuations, trace
rewrites, learned rewrites, learning continuations and saved splits. A split
activates only after **both target roots exist**. Pivot, coupled, growth,
affine-family and projection routes remain as initially checked: under the
permitted transition their immutable records and already acquired premises do
not change. Internal pattern rules are read from the newly acquired nodes by
the existing composition algorithm, rather than duplicated into this index.

This yields an inductive catalog invariant. Initially the catalog equals the
full builder's output. Under an eligible append, an old conditional route can
change availability only if one of its missing targets is among the inserted
keys. The reverse index visits every such route. It retains the remaining
obligations and attaches a route exactly when none is missing. The reported new
split is checked and registered separately. Every unaffected old route retains
its validity and availability. Sorting only affected source lists by the
builder's kind and within-kind order preserves tie-breaking during composition.
Therefore the updated catalog equals a full rebuild for this transition.

Existence of a target root is **not** structural closure, SAT, or UNSAT. The
unchanged least-fixed-point composition still requires every premise to have a
finite justification. A newly attached split can remain structurally open.
This distinction matters when acquisition reaches an unresolved child.

## Resource accounting

Initialization still pays for the complete builder and additionally scans its
route metadata to construct the index. The index retains an ordering entry per
route and reverse links for missing premises. Its number of entries is linear
in the route count plus missing-premise incidence; variable-length keys and
container overhead also consume memory. Nothing is removed from persistent
history, and index-entry counts are not peak RAM measurements.

Each eligible update still parses and compares the serialized sidecars, checks
admission sets, queries appended rows, loads new patterns and checks the
reported split. Its activation work depends on affected reverse links and the
ordered route lists of affected sources. Diagnostic counting also scans the
distinct waiting-target buckets. Hash-table operations and long string keys
are not free. Thus the update is not constant-time or solely a function of the
number of newly solved formulas. The saving is avoidance of repeated checking
of unchanged route certificates. Initial restoration, global composition,
serialization, export and cold verification remain separate costs.

## Evaluation protocol

`compare_cnf_pattern_activation.py` compares the previous pending-split helper
with selective activation under identical `EarlySavedExpansion` scheduling.
It uses two reversed-order repetitions on independent seeds for each workload:
the saved resumption of original 1154 and the next uncovered original 1062.
Each worker has twelve advances and one shared 32-state allowance. Completed
rows and interrupted admissions remain distinct; all arm results are retained.

`validate_cnf_pattern_activation.py` reconstructs both checkpoints without fresh
recognition or reference solving, checks every worker, and replays each first
repetition step by step using only then-available rows. It compares complete
catalogs, metadata, coverage, next selections and activation counts against
fresh construction. Identical operations and logical results across modes are
required before a runtime difference is attributed to maintenance. Historical
and current workloads are separate comparisons; their savings are not added.

Seven targeted tests cover pending and immediately available splits, second
child arrival, reverse arrival order, forced-continuation activation, fallback
after extra writes or sidecars, forged evidence, admission mismatch, external
writers and unsupported builders. The preserved archive supplies the broader
route mixture for independent replay. Development cases, repeated OS caches
and bounded state allowances do not establish a holdout speedup, globally
minimum expansion, or a polynomial algorithm for unrestricted SAT.


## Measured progress and the next frontier

The two modes reproduce the same operations and logical results within each
workload. Mean seconds over the two reversed repetitions are:

| Workload and phase | Previous maintenance | Selective activation |
|---|---:|---:|
| Historical completion: route updates | 2.18377 | 0.02296 |
| Historical completion: expansion | 2.41356 | 0.23051 |
| Historical completion: complete worker | 15.08509 | 12.86353 |
| Current partial expansion: route updates | 3.33336 | 0.03679 |
| Current partial expansion: expansion | 3.75094 | 0.44504 |
| Current partial expansion: complete worker | 16.85095 | 13.40605 |

The observed whole-worker reductions are **14.73%** and **20.44%**. Expansion
reductions are **90.45%** and **88.14%** because repeated catalog checking had
dominated that phase. Preparation and export variation also contributes to
whole-worker differences; it is not an activation improvement. Mean current
preparation is **8.27805 / 7.83564 s**, export **4.69058 / 4.97464 s** and
acquisition **0.28318 / 0.26735 s** (previous / selective). The selective path
therefore leaves acquisition and discovery as the largest expansion costs.
It does not remove startup or export.

The historical worker completes the same ancestor and thirty stored states in
two advances. Its first update activates the old variable-18 split when the
missing target arrives; its second installs the new variable-3 split with both
roots available. The index grows **693 -> 694 route entries**, with its single
pending dependency resolved. Current workers take three advances and store
**32 states**, but the original remains open. The index grows **694 -> 697
entries**, with **one pending route / one waiting target / one link** at the end.
Its serialized sidecar snapshot grows to **1,365,258 bytes**. These are metadata
counts and serialized payload sizes, not peak RAM. The helper adds resident
index storage; it does not reduce persistent bytes.

The current structural progress is source-bound:

- The **39/161/495** residual splits on local variable **25**, with **2 / 4**
  admissions on its false/true branches. Two false-branch reductions reach the
  existing **36/144/434** unresolved plan. This reuses intermediate work, not a
  completed proof. The true branch reaches a **35/149/466** unresolved leaf.
- That leaf splits on local variable **8**, with **2 / 21** admissions. The false
  child reaches **34/143/440**. The true child starts at **32/120/354** and follows
  probes, binary-path reduction, elimination and a polarity change to a new
  **7/9/19** terminal recognized as both Horn and zero-valid.
- The **34/143/440** leaf splits on local variable **5**, using the last three
  admissions on its false child to reach **31/122/370**. Its true **32/136/405**
  child is absent. All entered states are stored; this missing target has not
  been admitted. Both branches remain structural obligations even though the
  separate reference solver reports SAT for every current split source and
  raw cofactor.

Coverage remains **66/83**. The retained frontier has **three open split
records / two acquired leaves / one pending target**. The three new split
records and thirty-two new patterns are retained with all earlier work. Full
history grows **434,176 bytes** to **775,811,072 bytes / 42,101 patterns**.
Persistent deltas are identical across modes: **17,007 compressed bytes** for
the historical control and **23,539** for current progress. The current SQLite
delta is **516,096 bytes**. The expanded positive certificate still has
**3,360 steps**; reference evidence preserves all **3,575** previous nodes and
contains **3,734** nodes.

The full producer costs **369.75582 s**, including **80.22699 s** current
restoration, **76.75811 s** historical restoration, **8.09763 s** final route
preparation and **60.74631 s** global coverage. Union export costs **5.28907 s**.
These costs must not be described as eliminated by a warm update optimization.

Resume `experiments/results/cnf-pattern-activation/report.json` through
`compare_cnf_pattern_activation.restore_checkpoint`, SHA-256
`7af092282dfda5070c4dbf1006daa8cff22a218487af28e40b59e8dc51894c7c`.
Keep five evidence lists **(1, 42, 156, 44, 1)** and **two projection bridges**,
with bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
Resume the exact variable-5 pair before choosing another split. The pending
source SHA-256 is
`26f134186dbdd90745599fa2d41308823b8c08b752f19d5f53124ffd4ecd73f1`;
the missing true target is
`72697c710335660e1dc9c934e995f7c37577a9226c546fd7233d4e3685cb3615`.
The two acquired open leaves are **31/122/370** and **36/144/434**. Closing the
pending target alone need not close the original. The alternative first split
on variable 17 was not tested here: the maintenance comparison deliberately
keeps search choices identical.

## Checkpoint validation

Independent cold reconstruction passes in **498.30431 s**, checks all eight
workers and **3,734 reference nodes**, and reproduces coverage and the next
selection without fresh recognition or reference solving. Four first-repeat
prefixes reproduce the complete rebuilt catalogs, route order and activation
counts using only then-available rows. All **222 tests** pass; existing SQLite
resource warnings remain visible in the log. The manuscript builds to **160
pages** with no overfull boxes or undefined references, and all **64 existing
proof blocks** are unchanged. Lean sources are unchanged; no new Lean theorem
is claimed.

All **22 previous manifests / 1,009 artifacts** and all **3,575 previous
reference payloads** remain unchanged. The new manifest binds **98 artifacts /
4,355,064 bytes**, including the matched runs, independent replay, regression
and build logs. See `experiments/results/cnf-pattern-activation/validation.json`
for commands, source fingerprints and preservation checks.
