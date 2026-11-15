# Expansion without a full batch-seed copy

2026-11-15. Four consecutive bounded expansions continue the frontier initially
bound to case 1190. Removing a full-history copy preserves the discovered
evidence but **increases measured runtime**. Keep the copied-seed default.
The [report](../experiments/results/cnf-copyless-sequence/report.json),
[timings](../experiments/results/cnf-copyless-sequence/timing-summary.json) and
[cold replay](../experiments/results/cnf-copyless-sequence/reconstruction.json)
preserve both the discovery and the unsuccessful optimization.

## Discovery and remaining interaction

All four sequences store the same **82 new pattern records**: 30 eliminations,
27 probes, 17 binary-path reductions, three family terminals and five unresolved
records. This counts stored records, not 82 solved inputs. The new terminals
are **5/5/11**, recognized as Horn and zero-valid, and **4/3/6** and **5/4/8**,
recognized as 2-CNF. Shapes give variables, clauses and literal occurrences.
Recognition of these endpoints does not bound the work required to reach them.

Each batch has the unchanged 32-state admission and 12-advance limits. Global
selection runs after each batch, so the third batch's local closure advances
the next batch to another retained obligation rather than ending the sequence.

| Batch | Selected shape | Admission entries | New records | Entered but unstored | Selected focus closes |
| --- | --- | ---: | ---: | ---: | --- |
| 0 | 40/163/490 | 32 | 22 | 10 | no |
| 1 | 38/151/448 | 32 | 31 | 1 | no |
| 2 | 11/44/158 | 9 | 9 | 0 | yes |
| 3 | 36/130/378 | 32 | 20 | 12 | no |

The sequence charges **105 admission entries** for **94 distinct keys**: eleven
entries revisit a key across batches. The saved
[admission accounting](../experiments/results/cnf-copyless-sequence/admission-accounting.json)
checks these identities in all four sequences. This counts repeated admissions,
not repeated CPU time. It retains six new split records. Overall structural coverage stays
**68/83**. The next selected source is **26/94/284**, with a pending split;
the final twelve unstored entries remain work to recharge if visited again.
No missing record can be treated as a checked reduction or solved component.

The initial selector binds to original index 31, case 1190. The frozen selector
returns an empty original-index list for subsequent retained work. Independent
replay checks actual coverage-dependency paths from case 1190 to each selected
focus and successor, preserving this distinction. Dependency ancestry alone
does not transfer SAT truth: a conditioning rule still requires all coverage
premises, and other obligations of the original remain open.

## Matched costs

Two repetitions reverse the method order. Both retain the checked inventory
and complete route catalog, hash every historical table through the live
connection, perform identical bounded acquisition and checking, export only
appended rows, and run the same complete global queries. Only the per-batch
seed copy differs. The initial arm copy and final full delta comparison remain
in both methods. This does not repeat the earlier guarded-digest experiment.

| Mean time in seconds | Copy every batch seed | Omit every batch-seed copy |
| --- | ---: | ---: |
| Initial construction, global query and serialization | 67.78272 | 68.43429 |
| Four workers including preparation, checks and export | 4.61350 | 6.28484 |
| Preparation per worker | 0.75681 | 1.17069 |
| Full live digest per worker | 0.44201 | 1.14669 |
| Local expansion per worker | 0.28317 | 0.28688 |
| Updated global query | 0.24608 | 0.25472 |
| Updated query serialization | 0.31134 | 0.31154 |
| Complete four-batch sequence | 75.23972 | 77.78679 |

Omitting copies makes the four workers **36.23% slower** and the complete
sequence **3.39% slower**. Complete sequence samples are **74.26957 / 76.20988**
seconds with copies and **77.45284 / 78.12074** without. The baseline copies
**3,118,911,488 logical bytes per sequence**; the candidate avoids those files.
Logical copied bytes are not physical device-write or peak-RAM measurements.

The regression is concentrated in the first batch. Its full digest takes
**0.44355 / 0.50362 seconds** after copying, versus **3.28374 / 3.27103 seconds**
without copying. Later digest scans take about **0.43--0.45 seconds** in both
methods, and the three later workers are individually faster without their
copies. Sequential read-ahead or cache effects are possible explanations;
neither was instrumented. Reversed order does not reset OS caches. A policy
that copies the first batch and omits later copies has **not been tested**;
adding times from different arms would not establish its performance.

Complete sequence time includes arm preparation, initial global checking,
workers, subsequent global queries and their serialization, and union-delta
merge/check work. Full catalog audits after each sequence are separately timed.
Each arm has an independent history, but the diagnostic union is shared: the
first arm appends its rows and subsequent arms merge identical rows idempotently.
The final full comparison is charged in the overall producer, outside the
individual sequences. The reference extension takes **0.26881 seconds**, with
**3.59535 seconds** cold checking; these also fall outside the sequence timings.
Shared parent restoration takes **129.01658 seconds**, final cold route and
coverage checking takes **71.31630 seconds**, and the full producer takes
**540.25637 seconds**. Two repetitions on development cases are descriptive,
not a statistical or held-out performance claim.

## Conditions, persistence and space

The append boundary, historical authority and checked session remain required.
Under their existing ordinary append-only SQL and exclusive-ownership
conditions, the successful acquisition, maintenance, checking and export body
is unchanged; a test compares its complete syntax tree with the frozen worker.
Omitting the seed copy does not omit full hashing or checking. Full-table
scanning still depends on the entire history; there is no improved asymptotic
bound for expansion, cold reconstruction or arbitrary SAT.

On failure, committed evidence is exported through the append boundary, or
compared with the seed when available. A rejected boundary instead preserves a
full SQLite backup for inspection. These artifacts are explicitly **unchecked**,
and the original exception propagates. They are not accepted as verified
checkpoints. Open transactions are rolled back before archival; uncommitted
work is not claimed preserved. Exceptional full backups can cost the whole
history's size. Failure injection tests cover both delta and backup paths.

Both successful methods retain identical state. History grows from
**779,272,192 to 780,357,632 bytes** (+1,085,440), and **42,368 to 42,450 patterns**.
The union delta is **1,175,552 SQLite bytes / 52,938 compressed bytes**. Reference
nodes grow **4,481 to 4,750**; the new reference snapshot is **30,830,592 SQLite
bytes / 2,168,399 compressed bytes**. Original coverage certificates retain
**938 compact / 3,564 expanded steps**. The final live inventory has **20,379
current and 2,916 prepared checked objects** in both methods. These figures
do not measure peak RAM or establish reduced retained space.

## Resume and next gaps

Resume **`experiments/results/cnf-copyless-sequence/report.json`**, SHA-256
`0cf43154fba97eae8b971d700b7381fa671d2347aac4f45a41300ad208e1dcfd`, using
**`experiments.compare_cnf_copyless_sequence.restore_checkpoint`**. Retain evidence
**(1, 42, 156, 63, 1)** and **two bridges**. Resume **`next_selection` including
its pending split**, not the initial `source`. Next source SHA-256 is
`e9fc98d4e0b76e362efd0bdbbb47990a0411f68b16df6cfc917e681bd58c9b77`.

1. Continue this pending frontier with the checked session and catalog alive.
   Test the first-copy/later-no-copy policy on matched fresh expansion, charging
   its entire sequence. The all-copy baseline remains the default meanwhile.
2. Examine repeated elimination/probe/binary-path chains using their actual
   certified edges. The three recognized endpoints do not establish an
   efficiently recognizable class for all their possible ancestors. Twelve
   unfinished states also leave an opportunity to retain resumable internal
   work rather than only completed certificates.
3. Initial global checking and cold restoration still dominate total cost.
   Reducing these requires complete checked authority, including unresolved
   alternatives; a saved positive coverage proof alone cannot justify the
   negative frontier. Warm query micro-optimization has lower measured value.

Independent replay checks every acquisition prefix, all twenty saved global
queries, exact operations and logical results, lineage, and all reference
nodes with new discovery and reference expansion disabled. All **266 tests**
pass. The validation record binds preserved artifacts, sources and proof blocks.

Cold replay completes in **1,160.86928 seconds**. Validation jobs overlap, so
that duration is not a performance comparison. All **1,745 prior artifacts
across 33 manifests**, **105 historical source files** and all **4,481 previous
reference payloads** remain unchanged. The new manifest binds **228 artifacts /
15,908,598 bytes**; this experimental archive includes repeated comparison
outputs and reference evidence, separately from solver-history growth. The
manuscript builds to **166 pages**, with all **64 existing proof blocks**
unchanged and no overfull boxes or undefined references.
