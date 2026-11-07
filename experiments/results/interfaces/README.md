# Local interfaces, delta snapshots, and incremental proof study

All **792 answers were correct**, including 198 UNSAT answers: six streams,
six modes, three repetitions, 108 isolated workers. Each query had a three-second
budget. No timeout or failed answer occurred. The runner rotates mode order and
executes one worker at a time; builds and tests had finished before timing.

```sh
python3 experiments/run_interfaces.py --output /tmp/oracle-interface-new-run
```

The output directory must not exist. Inputs, raw query events, disjoint measured
phases, storage categories, source/binary hashes, and process totals are retained.
The cases diagnose mechanisms; they are neither held-out learning tests nor a
representative SAT competition or equal-total-memory comparison.

| Stream | Checked ms | Full interfaces ms | Delta ms | Delta/restart ms | Live proof ms | Proof/restart ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Chain expansion | 169.81 | 202.26 | 210.44 | 465.71 | 140.71 | 392.60 |
| Tree expansion | 167.20 | 230.42 | 224.70 | 491.23 | 137.54 | 382.25 |
| Hub expansion | 166.98 | 203.15 | 211.00 | 468.37 | 137.17 | 384.13 |
| Local edits | 184.52 | 273.73 | 276.57 | 651.38 | 153.37 | 501.47 |
| Width shift | 165.27 | 165.30 | 167.60 | 393.21 | 134.69 | 381.26 |
| Proof reuse | 165.89 | 145.14 | 142.18 | 359.01 | 132.67 | 378.70 |

These are medians of total per-query elapsed time, including service setup.
Restart modes include every shutdown; whole-worker fields additionally include
final shutdown, observer serialization, and interpreter/workload startup. Three
repetitions do not resolve small timing differences. Every mode keeps completed
results, while full and delta APIs use different archival representations.

The chain reaches 48 edges/49 variables with bags of size two. Its last expansion
acquires 49 definitions and reuses 32 projections. Changing the endpoint in the
local-edit stream acquires two definitions and two rows, reusing 32 projections.
Removing that endpoint acquires one definition and one row, with no leaf-row
acquisition. A distant bridge instead needs 35 definitions and 152 rows. A local
edit therefore need not have local effects throughout the dependency graph.

Delta JSON input for the edit stream is 4,810 bytes instead of 29,436. This does
not yield a total-time gain here: checking, graph traversal, and storage outweigh
saved acquisition. The proof-enabled live and restart modes each check all 33 of
their negative queries with incremental LRAT, without standalone CDCL fallback.
Restart remains costly. All reported phase partitions sum to query wall time.

A chain delta database retains seven snapshots, 151 factor definitions, 359 row
entries, and five shared relation payloads, including unknown summaries. It uses
528,384 bytes against 253,952 for checked solving. Separate provenance, persistent
map paths, partial rows and historical evidence versions are included. No whole
archive compression claim follows from small relation objects. The per-query
`archive_new_objects` counter concerns objects created during acquisition; final
snapshot evidence is included in the complete `storage` record and wall time.
`unknown_rows` describes resident Python cache nodes, not the entire archive.

The separate encoding study supplies complete truth tables before compression.
At width 12, parity selects a 266-byte reduced decision diagram; a seeded random
relation selects the 1,404-byte dense known/value bitmap. Constants and one
exception select constant/sparse encodings. Construction time is recorded; this
is not symbolic acquisition or an amortization result. Small scope still has
exponential worst-case table capacity.

`persistence-before.json` was saved before changing the live database and records
a local full-backup hash, row fingerprints and historical experiment hashes.
`persistence.json` confirms preservation of all 2,130 older results, 516 proofs,
and all other old rows, plus 355 revalidated current results and 129 new proofs.
The new totals are 2,485 results and 645 proofs; an independent semantic audit
checks all 355 current inputs. Earlier experiment files remain unchanged.
