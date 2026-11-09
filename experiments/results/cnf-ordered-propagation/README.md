# Updating affected clauses while preserving propagation proofs

The optional `OrderedPropagationInventory` replaces repeated whole-formula unit
scans during discovery with occurrence updates and events ordered by (scan round,
clause ID). It returns the exact old assignment, unit/reason trace and first
conflict. The independent checker, discovery policy and ordinary SAT decision
solver remain unchanged. Both compared inventories use the same 1 MiB successful
probe-check cache.

All **1,497 answers, profiles, roots and persistent bytes agree** with the previous
study. Non-tiny structural coverage stays **869/985**, leaving **116 sources /
148 distinct selected leaves / 33,651 literals** unresolved. This is an acquisition
cost improvement, not broader family coverage or faster unrestricted SAT search.

| Measurement | Repeated scans | Ordered occurrence updates |
| --- | ---: | ---: |
| Full operation seconds | 154.63114 | 137.59078 |
| Discovery seconds | 111.13169 | 97.76173 |
| Unchanged ordinary solver seconds | 43.44073 | 39.77480 |
| Cold replay seconds | 63.40473 | 62.61754 |
| Warm inventory seconds | 0.26392 | 0.29322 |
| Initialization seconds, separate | 0.00141 | 0.23095 |
| SQLite bytes | 437,620,736 | 437,620,736 |
| Logical node bytes | 179,395,726 | 179,395,726 |
| Six-case Python peak bytes | 22,258,170 | 22,474,570 |
| Six-case retained Python bytes | 21,945,645 | 22,162,045 |

Full discovery falls **12.03%**; total operation time falls **11.02%**. The
unchanged ordinary solver varies by **8.44%**, so the entire full-run difference
cannot be assigned to the propagation change. Cold replay falls only **1.24%**;
warm replay is slightly slower. These are single sequential synthetic samples,
not universal speedups. The six-case Python peak and retained measurements both
grow **216,400 bytes**; they exclude native SQLite, RSS and full-corpus memory.
The temporary index has no lifetime cap on the original graph or archive.

Twelve-query ABBA BAAB controls give mean total **5.38111 -> 4.83970 s (10.06%)**
and discovery **5.08503 -> 4.55072 s (10.51%)**. All four ordered totals
(4.82035--4.85730 s) lie below the four scan totals (5.34338--5.43274 s).
The unchanged solver averages 0.29492 -> 0.28783 s. The selected subset, four
trials and order control do not establish significance or industrial performance.
Within-mode counters/storage/database hashes repeat; every answer and summary
matches the full run.

## Work, proof compatibility and preparation

The full baseline records **105,860,805 propagation literal visits**. Across
**187,133** candidate calls, the replacement records:

- **18,691,048** clause-length inspections;
- **32,071,047** occurrence-index entries built;
- **5,356,250** affected occurrence visits;
- **645,555** event pops;
- **70,889** calls with no initial unit/empty clause, requiring no index.

These are different operations and must not be collapsed into a literal-visit
speedup ratio. All index construction, event handling and checking are timed.
The largest per-call occurrence count is **1,052**, and the largest live queue
has **33 events** in the full run. Per-query peak fields in the summary's generic
counter sum are not whole-run peaks; the maxima above are computed from records.
Every non-propagation operation counter is identical between modes.

An unsatisfied clause maintains the count and signed sum of its remaining literal
occurrences. Assignment first marks true occurrences satisfied, then removes false
occurrences from remaining clauses. Each clause becomes actionable at most once.
Scheduling by round and ID preserves the reference's exact next actionable scan
position, including conflicts that arise behind the scan position and satisfied
stale events. Repeated literals and tautologies retain reference behavior.
See the [trace argument and bounds](../../../research/ordered-propagation.md).

For m clauses, L occurrences and v variables, a call uses at most L index entries,
L affected-occurrence visits and m event insertions/removals. Under constant map
access and word arithmetic this is O(1+L+m log(m+1)) work and O(1+L+m+v) temporary
words. A no-unit call only inspects clause lengths. Dictionary collisions and
large-integer bit costs remain explicit. This is a bound on one closure, not
on all closures in an expansion. Every assumption still gets a fresh index;
sharing preparation across probes is not implemented.

Clause-counter propagation is established, including the discussion preceding
watched literals in [Chaff, Section 2](https://www.princeton.edu/~chaff/publication/DAC2001v56.pdf).
The contribution here is preserving the existing proof order and measuring all
costs in this inventory. There is no algorithmic novelty or Lean refinement claim.

## Controls, regressions and the next target

Thirty-two standalone controls cover sizes 16, 64, 256 and 1,024, with four
alternating timing trials per mode and separate allocation runs. Every trace,
assignment and first conflict agrees, and every certificate is independently
checked. At size 1,024:

| Control | Scan milliseconds | Ordered milliseconds |
| --- | ---: | ---: |
| Forward chain | 0.76777 | 0.84533 |
| Reverse chain | 337.58295 | 0.84911 |
| No initial units | 0.35198 | 0.07707 |
| Small cascade with unrelated clauses | 0.82900 | 0.41934 |
| Immediate opposing units plus unrelated clauses | 0.00248 | 0.41982 |
| Initial empty clause | 0.00120 | 0.00090 |
| Forward chain with colliding integer hashes | 40.69740 | 42.37221 |
| Reverse chain with 1,025-bit identifiers | 589.43548 | 1.24672 |

The reverse chain replaces 2,098,175 reference literal visits with 2,047 index
entries, 2,047 affected-occurrence visits and 1,024 events. This is a favorable
scan-order case, not the full-workload gain. The forward chain slightly regresses.
The immediate-conflict control exposes full preparation wasted after the reference
stops at two clauses; Python peak grows 1,752 -> 528,448 bytes. Collision and
long-identifier controls retain dictionary/bit-cost caveats. These failures and
full data are preserved in `controls.json`; the scan baseline stays available.

On source 1194, separate instrumented total time falls **4.01314 -> 3.51471 s**.
Propagation still has **2,221 calls**, but its cumulative time falls **0.79372 ->
0.31541 s**. The next largest named own-time cost is now **restriction**, with
**3,399 calls / 0.40355 s own / 0.82048 s cumulative**. Simplification checking
remains **2,303 calls / 0.27656 s own / 0.54588 s cumulative**. These instrumented
figures are not primary timing results and cumulative times must not be summed
across nested calls.

The next cost experiment should share exact source/assumption restriction and
reconstruction state with explicit dependencies, including per-assumption index
preparation. A cheap prefix or lazy-index policy may address the short-conflict
regression, but is not implemented here. Broader coverage remains a separate
priority: the 116 open sources still require new certified relations or exact
interaction decompositions. No amount of cheaper replay alone closes them.

## Persistent evidence and validation

Both full modes reproduce the existing implication-study archive SHA256
`1a431206ef825d2a8f7d5697cf1342119fe68d97950ca6ca8f180d18b6bdccf3` byte for byte.
It contains **25,047 nodes, 1,465 source bindings and 21,838 solver residuals**.
The report references that archive using a repository-relative path, without
storing another 437.621 MB raw database. The smaller eight-source pilot keeps
its own shared archive in the adjacent pilot directory.

Both cold audits begin with empty checked state and an empty proof-check cache,
verify every node/alternative, source binding and ordinary solver certificate,
and leave the database bytes unchanged. Warm replay inserts nothing. The exact
proof-check cache has the same 57,798 lookups and 34,971 hits in both modes.

All **417 tests** pass. New tests cover **9,724 ordered small formulas** including
repeated literals and tautologies, **3,000 seeded random/edited formulas**, reverse
chains, competing reasons/conflicts, scoped-engine restoration, all 148 saved
frontier probe discoveries, and byte-identical acquisition/cold replay for tiny
and random inventories. Each direct propagation comparison also independently
checks its certificate. The new algorithm-level trace proof is in the manuscript;
all 56 preceding proof blocks remain. Lean sources are unchanged from their
preceding 4,130-declaration/1,972-theorem audit and were not rebuilt for this change.

The full and pilot reports each have **66 fingerprints**. Diagnostic and control
scripts record their own hashes; historical implementations remain in their
recorded commits. Operation timing charges discovery, proof checking, index and
cache preparation, serialization, persistence, solving and root lifts. Generation,
summary walks, comparisons, hashing, compression, initialization and audits are
outside operation timing or measured separately. Primary runs, allocation,
repeated controls and profiles run sequentially without competing benchmark jobs.

Reproduce with a fresh destination:

```sh
python3 experiments/compare_cnf_ordered_propagation.py --output /tmp/new-ordered-propagation
python3 experiments/recheck_cnf_ordered_propagation_timing.py /tmp/new-ordered-propagation
python3 experiments/analyze_cnf_ordered_propagation.py /tmp/new-ordered-propagation
python3 experiments/measure_cnf_ordered_propagation_controls.py /tmp/new-ordered-propagation
```
