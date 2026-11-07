# Gap audit after the seven-priority implementation

This audit reviews runtime commit `269f095` without changing solver code. Run:

```sh
python3 experiments/analyze_priority_gaps.py --output /tmp/oracle-priority-gap-audit
```

The output directory must not already exist. All solver databases are temporary.
`audit.json` contains deterministic operation counts and actual SQL storage
deltas; `metadata.json` fingerprints the inputs, runtime and diagnostic script.
Elapsed times are observations from one execution, not a solver ranking. The
script checks 42 SAT answers against the construction of the diagnostic inputs.
The existing ten `solver.test_priorities` regressions also pass, including
negative/deletion, source-binding, restart and late-failure cases. The original
48-run study revalidates; none of its recorded outcomes is changed.

## Retention has a remaining full-closure cost

Each stream makes six distinct single-edge replacements, followed by an
unchanged query and a query of the original branch. All relations contain the
zero-to-zero transition. These are decision-only requests.

| Edges | Native node cap | New definitions per edit | Retention visits per edit | Node reads per edit |
| ---: | ---: | ---: | ---: | ---: |
| 256 | 511 | 9 | 511 | 554 |
| 256 | 1,022 | 9 | 0 | 43 |
| 1,024 | 2,047 | 11 | 2,047 | 2,100 |
| 1,024 | 4,094 | 11 | 0 | 53 |

All six edits in each stream have the displayed counts. Unchanged queries have
zero retention visits. Returning to the old branch at the tight cap needs
17/19 definitions and another 511/2,047 closure visits. At the larger cap it
needs neither. Extra capacity avoids pressure in this short experiment; it does
not prove a long-stream amortized bound. Python scans the closure and sorts its
retained IDs, and the native retention handler rebuilds and validates a map.

## Relation payload sharing does not eliminate provenance growth

An XOR-chain edit changes its first edge to equality. All three cases remain
SAT and have five native row acquisitions and two combination-row acquisitions.
The following are actual before/after SQL deltas, including the final saved
result, rather than the intermediate `archive_new_objects` counter.

| Edges | New relation payload objects | New knowledge objects | Packed payload bytes | Logical database growth |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 0 | 130 | 20,788 | 61,440 |
| 64 | 0 | 571 | 93,106 | 278,528 |
| 320 | 0 | 3,430 | 550,879 | 1,556,480 |

At 320 edges the new objects comprise 2,468 persistent-map objects, 638 interface
evidence objects, 321 elimination buckets, and one each of plan, source constraint
and result. There are also 322 new `interface_nodes` and 639 new `interface_rows`
rows, outside the knowledge-object payload sum. Object payload bytes exclude SQL
keys, indexes, page slack and WAL. The page delta is logical database allocation,
not physical storage or process memory. The existing relation-payload counter
charges serialized relation data even when insertion deduplicates it; it must
not be read as newly stored bytes.

This is positive evidence for relation-table compression and negative evidence
for a constant-cost complete edit. It does not establish a lower bound for other
provenance representations. See the current analysis in
[`research/implementation-gaps.md`](../../../research/implementation-gaps.md#gap-analysis-after-the-seven-priority-follow-up).
