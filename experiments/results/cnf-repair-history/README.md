# Checked pure-literal repairs with shared occurrence and assignment indexes

The preceding fixed-model history must solve a new base whenever its assignment
fails. `experiments/cnf_repair_history.py` adds a restricted repair: set one
literal in the new clause true, but only if its opposite literal is absent from
the **entire parent source**. This covers genuinely fresh variables and existing
pure variables. Every old true literal either stays unchanged or becomes true,
so no old clause is invalidated. Failure of this sufficient condition supplies
no verdict; ordinary solving remains the fallback.

This is an application of the elementary pure-literal principle with persistent
indexes, not a new tractable SAT class. Unrestricted base acquisition and repair
when both signs occur are not bounded by this construction.

## Representation, verification and invalidation

The separate `RepairHistory` interface reads the preceding archive tables and
adds `append-pure` records with an exact clause and an optional signed repair
literal. It retains the base and parent references. Old records remain readable
and unchanged; older readers intentionally reject the new record kind. Production
code and its result archive are not modified.

An immutable binary trie maps each positive variable identifier to three flags:
positive occurrence, negative occurrence, and current assignment. One root per
version shares unchanged paths. Every original source occurrence and every delta
is indexed, including duplicate literals and tautologies removed by canonical
solving. Missing assignment values are false. Thus absence from the base model
alone cannot establish freshness. Updating or querying an older branch uses its
own root; new flags and assignment changes do not leak into other versions.

Cold loading reconstructs each index from the checked base and exact ancestor
deltas. It rechecks purity, membership of the repair literal in the new clause,
and satisfaction after the change. No persisted support mask is trusted. SAT
query/witness export uses the version's model, including all accepted repairs;
UNSAT additions retain the previous monotonicity rule without constructing an
index. The old positive-subset append operation remains safe because a repaired
assignment still satisfies the base. The fixed-model method on the new class
checks the current version model, never silently returns to the original model.

The archive remains single-writer and append-only, with local IDs and immutable
already-checked rows during a session. Deletion/replacement requires a new base.
The Python checker, trie and SQLite protocol are tested implementations outside
Lean's kernel boundary.

## Matched operation costs and retained storage

The study retains **20 histories, 3,924 correct decisions and 60 archives**. It
compares full-source solving, the preceding fixed-model decision history, and
the new repair history. Fresh positive-unit streams grow from 8 to 128 additions
on matching bases of sizes 4, 8 and 16. Other cases use existing pure variables,
repeated units, blocked-but-still-SAT changes, an actual contradiction, already
compatible clauses, sparse identifiers and an UNSAT control.

| History | Full source bytes / seconds | Decision history bytes / seconds | Repair history bytes / seconds |
| --- | ---: | ---: | ---: |
| Fresh units, size 4, 128 additions | 214,791 / 0.13154 | 406,551 / 0.22986 | 10,846 / 0.03360 |
| Fresh units, size 8, 128 additions | 804,027 / 0.28143 | 1,545,051 / 0.48903 | 19,594 / 0.03962 |
| Fresh units, size 16, 128 additions | 6,117,309 / 1.84959 | 12,020,154 / 2.61853 | 100,706 / 0.07326 |
| Existing pure variables, 128 additions | 420,848 / 0.15090 | 828,536 / 0.29061 | 14,617 / 0.03542 |

Bytes are retained logical archive payload, not RAM. Seconds sum base acquisition
and all updates, including rejected attempts and materialized fresh-base fallback.
Initialization and final export/statistics scans are recorded separately. These
are single sequential measurements collected after the tests and Lean audit.

At size 16, repair keeps one base rather than 129 and eliminates all 128 fallback
acquisitions. Relative to decision history, logical storage is about 119 times
smaller and measured operation time about 36 times shorter. SQLite size falls
from 21,618,688 to 208,896 bytes (full source: 9,543,680). The last append takes
0.346 ms versus 21.845 ms and invokes no residual solving. It visits 88 trie
nodes, makes two purity checks and two clause-model probes, allocates 28 trie
nodes across assignment/support updates, and serializes 54 JSON bytes plus SQL
references. The final history shares 2,048 distinct resident trie nodes. Allocation
counts include transient intermediate nodes; they are not all retained.

The base is more expensive: 18.64 ms versus 13.96 ms because repair also builds
its index. Cold final query takes 13.20 ms versus 7.58 ms for decision history's
isolated final base and 11.20 ms for the full-source solver. These initial and
restart costs are not removed by the warm update improvement.

## Separate Python allocation measurements

Two histories were rerun with `tracemalloc` after the timed experiment. These
runs include engine allocation and common input assembly, and sample retained
allocations after collection and peak allocations before exports. They exclude
native SQLite allocations and **are not process peak RSS**. Tracing distorts
runtime, so these runs do not contribute to the timing table.

| History | Mode | Retained traced bytes | Peak traced bytes |
| --- | --- | ---: | ---: |
| Fresh units, size 16 / 128 additions | Full source | 40,310,292 | 41,097,529 |
| Same | Decision history | 76,182,915 | 77,265,863 |
| Same | Repair history | 945,159 | 1,740,168 |
| Already-compatible negative units, size 4 / 128 | Decision history | 91,019 | 108,869 |
| Same | Repair history | 232,011 | 249,217 |

The successful fresh-unit case reduces measured peak Python allocations by about
44 times versus decision history. But when the old model already works, the
index raises peak traced allocations from about 109 KB to 249 KB. A repair policy
therefore needs to charge index preparation and maintenance, not just count
avoided solver calls.

## Bounds and retained counterexamples

For identifiers of at most b bits and d literal occurrences in an addition,
lookup and path copying visit O((d+1)b) trie nodes on the accepted warm path.
There is no full-parent scan or model copy. This is a node-operation bound;
Python large-integer shifts, comparisons, allocation, SQL indexing and serialized
bit costs remain additional. Base source/index construction is paid once per
acquired base. Each changed trie path has at most the variable's bit length.
Keeping all version roots therefore retains at most the base construction nodes
plus O(sum_t (d_t+1)b_t) copied nodes and O(T) root references. Pointer sizes and
Python tuple overhead must be charged for a bit/byte bound. Cold checking rebuilds
these structures from all required ancestors. Witness export traverses the
current trie and emits true variables; absent values are false. Full-source
reconstruction is separately charged.

Durable storage contains clause and repair deltas, not serialized full indexes.
For a fixed base of B0 source bits and K0 acquired-certificate bits, it uses
O(B0+K0+sum D_t+T log(N+T+1)) additional logical bits, with N bounding prior IDs
and records. The selected repair literal is part of its clause and contributes
at most another copy of its encoded length. Rejected repairs can still require
fresh copied bases; the fixed-base bound then does not describe the whole run.

| Control | Decision bytes / seconds | Repair bytes / seconds | Limitation |
| --- | ---: | ---: | --- |
| Repeated positive unit, 128 additions | 10,102 / 0.03367 | 10,719 / 0.03080 | Full-source deduplication needs only 1,393 bytes / 0.01301 s. |
| Opposite sign occurs but another literal protects it, 32 pairs | 41,311 / 0.03953 | 41,791 / 0.04697 | Both histories fall back 32 times; purity is conservative. |
| Contradiction introduced after a delta | 4,454 / 0.00900 | 4,469 / 0.00874 | The contradictory change is rejected and solved, never falsely repaired. |
| Already-compatible additions, 128 | 8,926 / 0.03201 | 10,846 / 0.03131 | More index memory; small time differences are not significant. |

The blocked-but-SAT family starts with the unit (1), then adds (-x or 1) and (x).
Changing x is safe because 1 still satisfies the older clause, but purity rejects
it. This is a concrete next opportunity for checking only the affected clauses
or maintaining their true-literal counts; those stronger invariants are not yet
implemented here.

Sparse identifiers expose another cost. Thirty-two units on identifiers near
2^10, 2^128 and 2^1024 retain 353, 4,129 and 32,801 trie nodes respectively. At
2^1024, repair takes 38.73 ms versus 33.18 ms for decision fallback and 10.78 ms
for the full-source interface, which canonicalizes names. Repair cold replay is
25.29 ms versus 0.22 ms for the final fixed base. Logical storage is still smaller
than decision history (22,108 versus 182,057 bytes). Compressing long unary trie
paths could remove much of this index overhead, while exact original identifier
serialization must still be charged. The full-source archive stores canonical
keys rather than the exact source provenance retained by the history APIs.

## Validation and reproduction

All **242 Python tests** pass. New tests compare 168 base/clause combinations
and 300 seeded branching proposals, validate witnesses against full sources,
exercise sparse 1,201-bit keys, preserve older roots, mix old/new APIs and replay
128 repairs after restart. Corruption tests reject opposite-sign repairs,
cross-base or cyclic parents, wrong repair literals and invalid trailing literals.
Adding a tautology to a stored base (which preserves its normalized residual key)
still changes support and causes an incompatible repair to be rejected.

Lean proves `signed_occurs_append`, `pure_repair_preserves`, and
`pure_repair_extension` for signed variable/polarity pairs. The audit passes
**4,079 declarations / 1,939 theorem declarations** with only standard allowed
axioms. It does not refine the integer encoding, trie, database or machine costs.

All **379 preceding archives** replay with unchanged row digests and no new
expansions. The new 60 snapshots occupy 57,266,176 raw SQLite bytes and 4,837,233
gzip bytes. Offline compression is not part of online solving. `archive-replay.json`
independently reloads the compressed new snapshots and checks exact history
sources, final witnesses/verdicts and unchanged rows. Timings exclude common
input assembly, offline snapshots/digests and compatibility audits. Full-source
solve retains its per-query size scan and model output; the history interfaces
export witnesses optionally. This remains an interface ablation, not a
competitive SAT benchmark or a universal minimum-expansion guarantee.

```sh
python3 -m unittest discover -s solver -v
PATH=/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin:$PATH lake -d formal build OracleMachines
python3 experiments/compare_cnf_repair_history.py --output /tmp/oracle-repair-new-run
```

Use a new output directory. Exact sources, artifacts, counters, failures to reuse,
allocation profiles and source fingerprints are retained in `report.json`.
