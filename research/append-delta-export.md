# Exporting only the committed append suffix

The previous worker spent about five seconds exporting a small delta from a
776 MB retained history. The full exporter checks every old key and payload,
then scans for keys absent from the seed. This study changes that persistence
step while keeping structural discovery, admission accounting, route
maintenance and certificate checking unchanged.

## Contract and checks

`AppendDelta` starts on an exclusively owned SQLite connection containing a
verified parent snapshot. It records the eight supported tables' row counts
and maximum row IDs, the schema/data versions and the connection's total
change count. Construction and export require committed acquisition. A short
`BEGIN IMMEDIATE` transaction prevents competing writes during each snapshot
or export. The boundary is in-process state, not a serialized trust cache.
Preexisting legacy tables may remain outside this eight-table delta format;
ordinary writes to them increase the global change count without adding an
exported suffix row, and therefore fail the guard.

For each table, let N be its initial row count, b its initial maximum row ID,
and k the current number of rows with row ID greater than b. Export requires:

- Unchanged schema and external-write versions.
- Current row count exactly N+k in every table.
- The connection's total-change difference exactly equal to the sum of k.

It then streams only the rows above each boundary, in row-ID order, into the
unchanged delta schema. Compression and hashing remain charged. The boundary
is not advanced, so repeated exports include every append since construction.
A failed guard requires the full comparison; it never silently omits a write.
External changes also require reopening any live checked solver caches.

Under ordinary SQL writes on this connection, every counted row operation can
increase the number of rows above the boundary by at most one. Equality with
the total-change difference therefore excludes writes that do not contribute
a retained suffix row, including rolled-back writes. A replacement or row-ID
update could move an old row into the suffix without increasing table
cardinality; the N+k condition excludes this case. Restoring a lost old row
would itself require an operation that fails to increase the suffix count.
Together the checks establish an unchanged prefix and a complete appended
suffix within this contract. They do not cover raw-file tampering or a caller
that changes SQLite's schema/version machinery to bypass the contract.
The caller must keep table-name resolution fixed (no temporary-table
shadowing or attached-database substitution), use ordinary row writes, and
not share the connection with another writing thread. These are conditions
of this optional solver helper, not a security boundary for arbitrary SQL.

SQLite documents that `total_changes` counts row writes on this connection,
including trigger writes, but excludes the implicit deletion used by REPLACE.
That exception is why cardinality is checked separately. Its `data_version`
comparison detects commits from other connections. See the primary
[change-counter documentation](https://www.sqlite.org/c3ref/total_changes.html)
and [data-version documentation](https://www.sqlite.org/pragma.html#pragma_data_version).

The helper does not decide whether an appended SAT certificate is valid. The
ordinary conflict-checked merge and independent cold certificate checks remain
mandatory. The caller still establishes the initial parent's identity.

## Costs and validation scope

Construction and export both count table rows. Counting may traverse index
pages; there is no claim of work solely proportional to the number of new
patterns. The improvement avoids reading and comparing every old payload and
performing full-history membership searches. New row retrieval, serialization,
compression, hashes and cold verification still depend on the delta size.
The boundary stores counts and IDs per table, but peak memory is unmeasured.
No persistent rows are removed, and smaller persistent output is not expected.

Seven targeted tests compare complete delta contents and database hashes with
the original exporter, exercise repeated and empty exports, and reject
updates, deletions, replacements, row-ID rewrites, inserts below the boundary,
rolled-back writes, external writers, schema changes, open transactions and
existing output paths. Legacy tables may remain unchanged but writes to them
are rejected. The source database is unchanged by successful export.

The matched experiment runs two reversed-order repetitions of each exporter
on independent copies of the conditional-frontier checkpoint. Both modes
resume the same retained variable-2 pair, use selective pattern activation,
and receive twelve advances with one shared 32-state allowance. Setup of the
append boundary is charged to worker preparation and reported separately.
The union still uses the original full exporter as an independent comparison.
Cold replay checks all four workers and all four stepwise prefixes, compares
operations and final logical state, and requires byte-identical SQLite deltas
and compressed archives across the two methods. Timings on this reused
development workload are not a holdout or a general SAT complexity bound.

The first attempted comparison rejected the append arm before acquisition:
the guard incorrectly required that the entire historical database contain
only the eight delta tables. The baseline artifacts, log and exact rejected
sources remain in `experiments/results/cnf-append-export/`. They establish no
matched speedup. The corrected run uses `cnf-append-export-checked/`; legacy
tables are allowed only while unchanged. A new test covers both acceptance
of their unchanged contents and rejection after a write.

## Matched result and retained frontier (15 November 2026)

Both repetitions retain identical operations, admissions, pattern payloads
and delta bytes. The mean measured costs, in seconds, are:

| Cost | Full comparison | Append suffix |
|---|---:|---:|
| Preparation | 7.91030 | 8.84331 |
| Boundary setup, included in preparation | 0.00000 | 0.66334 |
| Expansion | 0.23199 | 0.22483 |
| Delta export | 4.87738 | 0.76122 |
| Complete worker | 13.11241 | 9.92093 |

The observed worker saving is **24.34%**. Export plus boundary setup costs
1.42456 seconds instead of 4.87738 seconds. Other preparation and expansion
variation is not an exporter improvement. The producer costs **228.86791 s**,
including **90.58347 s** historical restoration and **68.23153 s** final route
preparation plus global coverage. These costs are outside the matched worker;
there is no measured cold end-to-end speedup. The actual extra table is
`cnf_residual_accounting_v1`, which remains unchanged.

Each worker enters **32 states**, completes **21**, and leaves **11 entered
but unstored**. Resuming the missing 29-variable true cofactor completes a
chain of nine elimination nodes, eight probe nodes, three binary-path nodes
and a **9/16/43 one-valid terminal**. That formula is neither Horn, dual-Horn
nor 2-CNF. The previously entered thirteen states are now stored, with their
reentry charged. The acquired false sibling still leads to **24/88/274**.
Splitting local variable 10 of that residual interrupts acquisition on its false **20/68/198**
target and leaves its true **21/71/208** target unentered. Both target roots
remain missing, so the split is not an available coverage rule.

The union adds **21 patterns / one split / no external probe rows**. History
grows by **266,240 bytes** to **776,331,264 bytes / 42,141 patterns**. Both
export methods produce **327,680 SQLite bytes / 12,754 compressed bytes**.
The positive certificate remains **3,360 steps**; reference evidence grows
from **3,781 to 3,803 nodes**. The live activation index has **699 routes /
two missing-target links**. Coverage remains **66/83**, with **five open
splits / one acquired leaf / two pending targets**. The separate acquired
36-variable leaf remains unresolved.

Resume `experiments/results/cnf-append-export-checked/report.json` through
`compare_cnf_append_export.restore_checkpoint`, SHA-256
`81e1c7c0b887277cefa62df011738e73c809a9fef16897ba5238e84bf45732d4`.
Keep evidence lists **(1, 42, 156, 46, 1)** and **two bridges**. The next source
is `4de3e4b743fbf475c9b0d663653f2d523578a50ece61b6a8a6d5fee2dab93add`;
its false target is
`59c3e32fa8d467475586e83e0427608a9222d0499b128eff3205974a92814d29`
and its true target is
`64cc767d3821b0a8fcb01af5c0f1864863fb2b4a96fef118ebcaa73fa22b2b96`.
Charge the eleven unfinished inputs again unless a separate checked
continuation mechanism is implemented.

The largest remaining warm cost is preparation: cloning, repeated historical
digests and checked catalog loading. Profile those phases before changing
their authority contract. The main structural task is resuming both pending
cofactors while preserving the unresolved 36-variable interaction. Local
continuation records remain a progress opportunity, but this run does not
implement them or establish efficient unrestricted-SAT expansion.

## Reproduction

From the repository root, choose a fresh output directory:

```sh
python3 -m unittest solver.test_cnf_append_delta
python3 experiments/compare_cnf_append_export.py /tmp/cnf-append-export-replay
python3 experiments/validate_cnf_append_export.py /tmp/cnf-append-export-replay
```

The producer binds its parent and source fingerprints. The validator restores
the parent independently, forbids fresh discovery and reference search,
replays all four workers and their stepwise catalogs, checks all reference
nodes and reproduces global coverage. It uses the old conflict-checked merge
and cold certificate checkers; it does not use the append helper to establish
the correctness of an exported delta.

Independent cold replay passes in **365.45167 s**, checks all four workers and
all four intermediate catalogs, and verifies **3,803 reference nodes** without
fresh discovery or reference search. All **229 tests** pass. The manuscript
builds to **161 pages**, with no overfull boxes or undefined references; all
**64 previous proof blocks** are unchanged. All **1,147 artifacts across 24
prior manifests** and all **3,781 prior reference payloads** are preserved.
The new manifest binds **73 artifacts / 3,954,783 bytes**, including the rejected
attempt. Exact commands, source fingerprints, concurrency notes and checks
are in `experiments/results/cnf-append-export-checked/validation.json`.
