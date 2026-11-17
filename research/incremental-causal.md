# Incremental causal acquisition: more supports, unchanged fresh coverage

Extending the causal frontier from 137 newer guarded-negative records adds
27 retained supports, but none is selected on the next 192 queries. Both modes
make 37 cofactor transfers, expand 126 nodes and add 364 proof rows. Every trial
produces a byte-identical proof database. Mean complete time rises **4.89%**.
The acquisition method is validated and its results are preserved; enlargement
alone is not a reason to enable it for every query batch.

## What the extension preserves

`extend_causal` checks source identities and the causal/deferred policy, extracts
supports only from the new catalog records, then merges the old and new raw
supports into an exact containment frontier. Old first-origin bindings, raw
supports, dominance witnesses and pending entries remain in the history. New
extraction may traverse old proof dependencies; it does not revisit old source
records as a new acquisition batch. Discovery publishes no proof nodes and
performs no fresh SAT search.

The merge preserves syntactic coverage: every raw support still has a retained
subset. This is not a proof-cost ordering. A newly smaller support could displace
a cheaper ready alternative from the lookup frontier, while retaining that
alternative in raw history. No old frontier entry is retired in this experiment.

Saved descriptions remain hints. A matched support needs an ordinary checked
negative proof or checked causal materialization. Current-query guards remain
mandatory. The legacy bank retains its eight-catalog lineage; the extended
causal bank uses eleven catalogs. Both full lineages are checked after the
unchanged complete proof/query audit on the same pinned read-only snapshot.
An unused corrupted provenance record still rejects. Independent reconstruction
compares the merged frontier with complete causal discovery from all source
records, without search or proof publication. Full reconstruction visits 3,708
support nodes versus 1,181 for incremental acquisition, **68.15% fewer visits**
for the same frontier. This reconstruction check is outside timed trials; it
does not establish the same percentage reduction in total runtime.

## Matched experiment

```sh
python3 experiments/compare_cnf_incremental_causal.py /tmp/cnf-incremental-causal
python3 experiments/validate_cnf_incremental_causal.py /tmp/cnf-incremental-causal
python3 experiments/analyze_cnf_incremental_causal.py /tmp/cnf-incremental-causal
python3 experiments/probe_cnf_alternative_guards.py /tmp/cnf-incremental-causal
```

Both modes start from the same **19,543-key union**. Selection excludes 2,112
prior sidecar answers and cached full roots, then takes the next 64 neighbours
per template, interleaved. Four alternating fresh-process pairs visit each query
twice. Timed workers run without overlapping tests, builds or profilers. Fixed
loads the acquired ready-first portfolio; extended loads it and acquires the
137 newer negative guarded records before querying. Original acquisition remains
separately charged. The 526 total origin records need not represent 526 distinct
residual structures.

| Measure | Fixed | Extended |
| --- | ---: | ---: |
| Causal origin records | 389 | 526 |
| Raw causal supports | 189 | 217 |
| Retained causal supports | 176 | 203 |
| Retained causal clause occurrences | 4,568 | 5,328 |
| Initially ready retained causal roots | 60 | 60 |
| New discovery-node visits | 0 | 1,181 |
| Cofactor transfers | 37 | 37 |
| Expansions / splits | 126 / 43 | 126 / 43 |
| Materialization / total new rows | 60 / 364 | 60 / 364 |
| Mean preparation seconds | 0.11359 | 1.39511 |
| Mean query seconds | 1.62996 | 1.15715 |
| Mean complete seconds | 12.70798 | 13.32969 |
| Mean peak RSS, bytes | 574,181,376 | 572,407,808 |
| Final SQLite bytes | 62,066,688 | 62,066,688 |
| Gzip plus first-trial sidecars, bytes | 11,901,671 | 14,167,905 |

The merge finds 64 duplicate descriptions and 28 new raw supports; 27 new
entries enter the retained frontier. None of the new entries has an initially
ready proof root, and no measured hit is first bound to a new origin. All
transfers still share their first origin's guard. Both modes answer **101 SAT /
91 UNSAT**; repeated visits add no rows. The extended policy chooses 33 ready
proofs and four materializations, with exactly the same resulting proof archive
as fixed loading.

Query time falls **29.01%**, while preparation performs **3,572 proof-node
verifications** and query verification falls **3,333 -> 1,895**. Acquisition warms
proof checks before queries; lower query time is not evidence of reduced search.
The complete clock regresses 4.89% on average, with paired changes **+14.45%,
+3.72%, +12.41%, -7.84%**. Peak RSS has mixed paired signs and a -0.31% mean
change; this does not establish a memory improvement. The newly serialized
causal index costs **2,183,937 bytes**, fully charged in sidecars. Gzip plus
sidecars grows **19.04%**, while earlier artifacts and all trial archives remain
additional retained storage.

Complete time includes restoration, loading, acquisition, merging, index
serialization, matching, proof checking, materialization, queries, persistence,
complete cold audit, compression and final digest/report generation. Imports,
initial CLI reads and the final wrapper rewrite are excluded. Selection and
historical acquisition are separately charged. There is no demonstrated
amortization from new support acquisition on this fresh workload.

## More promising next target: choose the guard before fresh solving

A separate read-only diagnostic examines the twelve queries that still expand,
using only the pre-query union and acquired banks. Each has two valid deletion
guards. **Case 121** has an alternative guard whose target contains an already
checked causal support. Its chosen guard costs **20 expansions**. The alternative
uses an old ready support, so this opportunity does not depend on acquiring the
27 new entries. The diagnostic publishes no new target certificate and does not
change the measured search policy.

This gives a concrete next experiment: when the first guarded target misses
both the archive and support bank, try the other checked guard before fresh
solving. Charge extra guard discovery, verification, matching and publication.
Twenty expansions is a local opportunity, not a guaranteed batch saving:
changed choices can alter later sharing, and additional checks may exceed saved
work. A matched control-flow experiment is required before claiming a speedup.

Case 121 is already represented in the new union. A controlled reproduction
must restore the 19,543-key pre-query snapshot; a generalization test must select
fresh queries from the new checkpoint. Re-solving the retained case would only
measure exact cache reuse.

The largest remaining negative cases are **182 (26 expansions), 121 (20),
51 (19), 10/81 (15 each)**. In total, **120 expansions are negative and six
belong to SAT case 67**. Templates 6/8/12 contribute 34/56/36. Current catalog IDs
are distinct from earlier streams and original structural cases.

The diagnostic also records overlapping near-supports and their exact missing
clauses. Cases 182, 51 and 10 are each one missing clause from a checked support;
that missing clause cannot be ignored. Distance calculations require an actual
shared clause: otherwise the empty-clause refutation is trivially distance one
from every nonempty target. Such proximity is a discovery hint, not a certificate
or an efficient classification of arbitrary SAT.

## Validation and retained authority

Independent validation passes **510 tests**, eight complete archive checks /
**3,072 trial query replays**, every union node, **2,381 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. Incremental and
complete acquisition have identical frontier structure. Every portfolio choice
is reconstructed from the append history available before its query. All eight
trial proof databases are byte-identical; there are no alternate certificates.
The union retains **19,907 keys / 62,033,920 SQLite / 4,632,742 gzip bytes**,
adding 364 keys while preserving all prior payloads. New decisions comprise
**141 direct roots / 51 guards**, including one positive guarded result.

Resume `experiments/results/cnf-incremental-causal/checkpoint.json`. It preserves
all previous semantic fields and adds `incremental_causal_study`,
`incremental_causal_decisions`, `incremental_causal_proposals` and
`incremental_causal_portfolio`. Keep the enlarged bank optional. Its 203 retained
entries have **62 ready roots / 141 pending**, with eleven-catalog / 526-origin
lineage. The old causal bank has **62/114**, legacy **131/76**, and original
170-entry bank **125/45** (ready/pending). All four lineage checks pass.
The newest catalog adds 50 guarded-negative records that have not been acquired
into the expanded index; broad automatic reacquisition has no demonstrated
benefit on this workload.

All prior **391 sources / 4,345 artifacts / 76 manifests** remain unchanged.
Runtime binds 395 sources; the analyzer and guard probe bring the ledger to
397. Structural authority stays **2,614 patterns / 259 pairs / 17 missing
children**, original **17/24 / 999 steps**, separate supplemental **24/24 / 208**,
and original case 7's discovery pointer. The manuscript builds cleanly to
**201 pages** with **64 unchanged proof blocks**. No new Lean or unrestricted-SAT
resource bound. The full test log retains 24 unclosed-SQLite ResourceWarnings
from older tests; eight focused new tests emit none with warnings enabled.
Their allocation origins remain untraced.

Checkpoint SHA-256: `f3941f25743a6ce157e446a4d5aec53a0750ce4bfa1dcaf26970833d477a5e0b`.
Report SHA-256: `f58224656b5addf7c9ae648a7c94f0d827cfc05838e96d295e35493038b5141b`.
