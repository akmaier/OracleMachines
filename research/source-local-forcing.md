# A forced frontier reduction through the source-local store

The ordinary continuation on the open 23-variable, 93-clause source proves that
**variable 22 must be true**. Its false assumption produces fourteen checked
unit deductions followed by a conflict. Applying the forced value leaves an
satisfiability-equivalent residual with **22 variables, 88 clauses and 272 literals**, down
from 23 variables, 93 clauses and 288 literals. One new recognition state retains
that residual. It is still unresolved, so structural coverage stays **58/83 reused
development inputs**.

The result extends [source-local expansion](source-local-expansion.md) from an
inconclusive probe block to actual target acquisition, persistence and replay.
The existing recognizer and validators are unchanged. No new tractable SAT
category or unrestricted complexity bound follows from this reduction.

## Exact evidence and retained work

The scheduler checks the saved clear window for variables 7, 9, 16 and 17 before
advancing to offset four. The new block checks both assumptions for 18 and 21,
then finds a conflict under 22=false. It stops after those **five new ordinary
assumption attempts**, without probing 22=true or 23. The conflict implies the
opposite value; restricting by 22=true produces the target, whose normal
recognizer runs under the same **32-state admission allowance**. Only one state
is admitted. The target's own recognition and checking are also charged, rather
than treating the five external attempts as all work.

The source-local store imports the exact source and old window from authoritative
history. It validates the old clear prefix, persists the new forced continuation,
and acquires the source-bound canonical target. It does not mistake absent local
rows for novel states. Both matched arms retain the same records, admitted keys,
ordinary probe counters and byte-identical delta database. The new delta contains
**one continuation and one unresolved pattern node**; both pass independent cold
checking after a conflict-checked merge into a copy of the full parent.

The reference solver independently confirms both source and residual SAT and
checks the lifted model. These answers are separate from structural coverage:
the residual still lacks a complete recognition plan. All **1,998 previous
reference nodes** are preserved; the reference archive now checks **2,012 nodes**.
All five structural evidence lists remain unchanged at **(1, 42, 156, 11, 1)**.

Candidate identifiers belong to each normalized formula. In the new residual,
variable **22 denotes the previous source's variable 23**. Thus a later candidate
numbered 22 does not ask again about the forced variable just removed. The exact
edge transport is retained and checked.

## Measured local work and the larger cost

Two reversed-order comparisons run eager/local and then local/eager in fresh
processes. Each receives the same already reconstructed authority and preselected
source and performs one advance, target acquisition and delta export. The eager
control prepares the old route catalog, copies full SQLite and uses the old
full-table delta exporter. The local mode loads only required records and exports
its indexed new rows. OS caches are shared; these are two samples, not a timing
confidence interval. No builds or tests overlap the timings.

| Mean measure | Eager control | Source-local mode |
|---|---:|---:|
| Preparation, seconds | 6.04190 | 0.01338 |
| Advance and target acquisition, seconds | 0.01204 | 0.01558 |
| Delta export, seconds | 3.62715 | 0.00117 |
| Worker operation, seconds | 9.90249 | 0.03068 |
| Complete worker process, seconds | **10.03384** | **0.13717** |
| Working SQLite bytes | 770,371,584 | 126,976 |
| Historical validation-cache nodes, including new target | 1,693 | 2 |

The **98.63% worker-time reduction** concerns preparation and persistence with
authority already available. Actual advance/recognition is slightly slower in
the local mode. This is not a full-pipeline or competitive SAT-solver speedup.
The local path imports **two rows / 14,725 key-plus-payload bytes**, makes five
read-path authority lookups and two additional insertion membership checks.
It still requires the complete **770,347,008-byte parent authority**. Working
SQLite and logical JSON bytes are not total memory or measured peak RAM.

The remaining pipeline cost is explicit:

| Operation outside the matched workers | Seconds |
|---|---:|
| First authoritative reconstruction | 21.99791 |
| Final copy and merge | 0.11313 |
| Cold checking of the two new delta records and dependencies | 0.00812 |
| Global route preparation | 6.47823 |
| Global coverage composition and plan checking | **55.48722** |
| Frontier/learning diagnostics | 0.04421 |
| Independent cold positive replay | 2.96193 |

The complete study takes **115.19078 seconds**, including all four workers,
integrity checks, serialization and reference work. A small unmeasured exploratory
propagation before this pipeline identified the forced candidate; selection is
adaptive. The unchanged positive proof still contains **2,748 explicit steps**.
After global preparation, composition and diagnostics, validation caches hold **22,603 nodes**,
191,717,696 node-JSON bytes and 59,762,047 key bytes. These are retained logical
payloads, not peak RAM. Checking all those old obligations is now the dominant
measured cost; the local gain must not hide it.

The preserved history grows **24,576 SQLite bytes**, to **770,371,584 bytes /
41,759 pattern nodes**. The new delta is **4,447 compressed bytes / 90,112 SQLite
bytes**, including fixed schema. Parent bytes and earlier artifacts are unchanged;
applying the delta twice leaves the merged archive byte-identical.
Reports, reference data and the re-emitted positive-proof artifacts occupy
additional study storage; the compressed delta is not the size of the whole study.

## Validation and next gaps

All **148 relevant tests** pass. New integration tests compare eager and local
forced acquisition, exact delta equality, cold reuse with discovery disabled and
zero-allowance pending edges. Earlier tests cover changed/missing prefixes,
authoritative membership, corrupt deltas, rollback and shared admission. An
independent checkpoint reconstruction checks the complete inherited lineage,
new records, all logical table digests and the positive proof. This validates
the new delta and its dependencies; it does not repeat a full audit of every
historical row. No new Lean refinement is claimed.

The open leaf is identified by SHA-256
`545c51d457452dc1fd3dec970e5eadc1f85ba4012c889be2164277966968bf29`.
Its next ordinary candidates are **16, 18, 21 and 22**, in the new coordinates.
The retained split pairs rank as follows before acquisition:

| Variable | Unclosed / missing distinct children | Maximum cofactor support | Total cofactor literals |
|---|---:|---:|---:|
| 13 | 2 / 2 | 20 | 346 |
| 5 | 2 / 2 | 20 | 363 |
| 6 | 2 / 2 | 21 | 267 |
| 11 | 2 / 2 | 21 | 392 |

These are heuristic ranks, not measured costs or a proof of a cheapest split.
No competing pair was acquired in this run. The broader learned queue remains
**17 ready bases / 88 candidates**.

There are two concrete next opportunities. Continue discovery on this smaller
leaf using the next ordinary block versus the retained pairs under one allowance.
The main implementation target is to replace repeated global composition with exact
updates to affected proof obligations. That requires a complete persisted rule
and reverse-dependency index, checked new edges and explicit invalidation for
pending premises; a partial positive catalog cannot certify noncoverage. Do not
reuse a stale negative result or infer that every reduction makes its target
cheap. First reconstruction also remains a cost to amortize across useful work.

## Reproduce and resume

Run `python3 experiments/continue_cnf_local_forcing.py OUTPUT_DIRECTORY` to repeat
this one-forced-block study from its fixed parent. The runner intentionally
rejects a different outcome rather than labeling an inconclusive block forced.

Resume discovery through
`experiments.continue_cnf_local_forcing.restore_checkpoint`, passing
`experiments/results/cnf-local-forcing/report.json`, a fresh database output and
a fresh temporary directory. It returns the new checkpoint and all five complete
evidence lists. The ordinary continuation and target are now part of that
checkpoint; restoring only its preceding source-local checkpoint would omit them.
