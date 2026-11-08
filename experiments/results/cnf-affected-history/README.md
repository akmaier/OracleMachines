# Checked repairs over affected clauses

The next case after pure-literal repair is now implemented in
`experiments/cnf_affected_history.py`. A variable may change even when both signs
occur, provided all affected old clauses remain satisfied. This is an elementary
single-flip preservation rule with persistent verification, not a new tractable
class or an unrestricted polynomial repair algorithm.

## Invariant and representation

For a currently false literal l made true, each old clause's true-literal count
changes by `-[opposite(l) in C] + [l in C]`. Count distinct signed literals;
duplicates are not additional protection. A tautology containing both signs has
zero net change. Clauses containing neither sign are unchanged.

The new interface extends `RepairHistory`. It retains immutable tries for the
assignment/support flags, variable occurrence lists, and clause counts. Linked
occurrence entries carry a clause ID and its sign mask, with unchanged tails
shared across versions. Clause IDs are local to a version's base/history; forks
retain their own roots. No whole-parent source or model is copied on an accepted
warm append.

Discovery tries distinct literals from the new clause, with a default budget of
4,096 occurrence visits across all candidates. Failed or budget-exhausted repair
raises `UnsupportedExpansion`, never an UNSAT answer. A successful record is
checked independently before acceptance. Cold checking reconstructs indexes
from the exact source and ancestor records, ignoring the discovery budget; no
stored counts or claimed affected-clause subset are trusted. New records store
only the clause and optional repair literal with parent/base references. Earlier
formats remain readable, and older readers reject the new kind. The append-only,
single-writer archive assumption remains; deletion requires another interface.

## Matched measurements

The primary run follows completion of the test suite and Lean build. It retains
35 cases, 7,230 correct acquisition/update/replay decisions and 70 compressed
archives. Each mode includes base preparation, discovery, failed attempts,
materialization on fallback, checking and persistence. Initialization, final
source/model export, storage scans and cold/warm queries are recorded separately.
Common input assembly, offline gzip and verification digests are outside timed
operations. Times are single samples, not statistical or competitive-CDCL claims.

| Case | Pure-repair seconds / logical bytes | Affected-repair seconds / logical bytes | Fallbacks, old to new |
| --- | ---: | ---: | ---: |
| Original protected-flip control, 32 pairs | 0.08492 / 41,791 | 0.01768 / 5,340 | 32 to 0 |
| Protected flips, 128 pairs | 0.51684 / 556,058 | 0.07466 / 20,823 | 128 to 0 |
| Protected flips, 512 pairs | 5.05929 / 8,921,728 | 0.32684 / 83,082 | 512 to 0 |
| Matching SAT, size 16, 128 protected flips | 3.47813 / 12,460,337 | 0.14730 / 158,332 | 128 to 0 |
| One flip affecting 4,096 clauses | 0.10999 / 444,503 | 0.12548 / 222,352 | 1 to 0 |
| Already-compatible stream, 128 additions | 0.03441 / 10,846 | 0.05165 / 11,358 | 0 to 0 |

The matching case retains one base instead of 129. SQLite size falls from
22,241,280 to 294,912 bytes. The final unit update visits one affected clause in
discovery and again in checking, uses 202 trie-node visits, allocates 66 trie
nodes and one posting entry, and invokes no residual solver. These are counts
for this small-affected-set case, not uniform costs for every variable change.
The archive-size improvement avoids cumulative copied prefixes and certificates.

| Separate allocation run | Old peak Python bytes | New peak Python bytes |
| --- | ---: | ---: |
| Original 32-pair control | 873,786 | 254,720 |
| Matching size 16 / 128 protected flips | 86,261,287 | 2,837,728 |
| Already-compatible stream | 249,217 | 473,849 |
| Sparse identifiers near 2^1024 | 2,570,688 | 4,948,888 |

Tracing includes input assembly and engine allocations in a separate untimed
rerun. It excludes native SQLite allocations and process peak RSS. Logical
archive payload, SQLite pages and live Python allocations are different measures.

## Costs and counterexamples retained

Preparation of the size-16 matching base grows from 28.06 to 46.85 ms. Cold final
query grows from 14.29 to 38.94 ms: the new archive rechecks the required history,
whereas the previous final version has its own fresh base. For fresh positive
units already covered by purity, operation time grows from 54.78 to 75.22 ms.
The additional index should therefore not be built eagerly for every workload.

At degree 4,096, new-base avoidance loses in total runtime because the index costs
103.32 ms to prepare. On sparse identifiers, cold replay grows from 26.01 to
39.90 ms and traced peak allocation nearly doubles. Small timing comparisons
fluctuate: sparse-ID operation timings reverse between screening and primary
runs, with an anomalous 25 ms initialization/preparation sample in the old path.
We make no sparse-ID speedup claim. The unchanged UNSAT path also exhibits timing
noise; it builds neither repair index.

A 32-visit budget on a 64-occurrence variable rejects the otherwise safe repair
and falls back. The formula `x <-> y` with both false needs two changes to admit
the unit `(x)`; both interfaces still fall back. Independent flips cannot be
combined using stale counts. High affected degree, coordinated repairs, repeated
event storage and copied sources on genuine fallback remain open.

Let d be new literal occurrences, b the maximum variable-identifier bit length,
m the parent clause count, k candidate occurrence visits and r occurrences of
the accepted variable. The current tries require
`O((d+1)b + (k+r+1) log(m+2))` node operations, plus literal processing,
integer arithmetic, allocation, serialization and SQL. Newly retained paths use
`O((d+1)b + (r+1) log(m+2))` nodes per accepted version plus at most d posting
entries and a constant number of roots. Base construction and cold replay are
charged separately. r can be the entire parent clause set. Durable storage for
one retained base remains base source/certificates plus encoded deltas and
version references; it does not persist copies of all derived indexes.

**Next target:** keep the cheap pure-repair path and promote to the affected
index only when its avoided acquisition cost is likely to repay construction and
maintenance. Charge first activation and cold reconstruction; retain the current
method as a baseline. This targets the demonstrated index losses without
discarding the protected-flip gain.

## Proofs, preservation and reproduction

All 249 Python tests pass. Seven new tests include 294 base/clause combinations,
400 seeded branching proposals, exact index reconstruction checks, old/new
formats, cold replay with a zero discovery budget, duplicates, tautologies,
forged records and coordinated-flip limits. Lean proves
`affected_repair_preserves` and `affected_repair_extension` using protected old
clauses. The axiom audit passes 4,081 declarations / 1,941 theorem declarations.
These semantic proofs do not refine the integer encoding, count maps, Python/SQL
implementation or machine costs.

All 439 preceding benchmark archives replay without changed rows or new solving.
`archive-replay.json` independently decompresses the new snapshots and checks
every historical version's exact source and verdict, all SAT witnesses and every
retained residual. Database hashes remain unchanged. The earlier
[`cnf-affected-history-screening`](../cnf-affected-history-screening/README.md)
run is retained with its runner source; it overlapped with tests and compilation
and is excluded from the primary timing claims. No previous result is replaced.

```sh
python3 -m unittest discover -s solver -v
PATH=/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin:$PATH lake -d formal build OracleMachines
python3 experiments/compare_cnf_affected_history.py --output /tmp/oracle-affected-new-run
```

Choose a new output directory. `report.json` preserves recipes, per-operation
metrics, rejected attempts, storage, source fingerprints, allocations and replay
measurements; `summary.json` collects the cost comparison.
