# Incremental causal acquisition and an alternative-guard opportunity

Incremental discovery reconstructs the same frontier as full acquisition with
**68.15% fewer support-node visits**. However, its 27 new retained entries give
**no extra fresh-query hits**, and mean complete runtime rises **4.89%**. Preserve
the learned bank and failed coverage test; keep acquisition optional. See
[analysis](../../../research/incremental-causal.md).

Reproduce in a fresh directory, with timed workers running alone:

```sh
python3 experiments/compare_cnf_incremental_causal.py /tmp/cnf-incremental-causal
python3 experiments/validate_cnf_incremental_causal.py /tmp/cnf-incremental-causal
python3 experiments/analyze_cnf_incremental_causal.py /tmp/cnf-incremental-causal
python3 experiments/probe_cnf_alternative_guards.py /tmp/cnf-incremental-causal
```

The protocol binds 395 runtime sources and the 19,543-key starting union.
Selection excludes 2,112 prior sidecar decisions and cached roots. Four alternating
fresh-process pairs compare fixed and incrementally extended ready-first
portfolios on 192 new neighbours, each visited twice. The 137 new negative
source records grow causal history from 389 to 526 origins, 189 to 217 raw
supports, and 176 to 203 retained entries. None of the new retained roots is
initially ready; no old retained entry is retired.

Both policies transfer 37 cofactors, expand 126 nodes and add 364 proof rows,
including 60 materialization rows. Every trial proof database is byte-identical.
Both answer 101 SAT / 91 UNSAT. The new descriptions save no search or proof rows.
Query time falls 29.01% as acquisition warms proof checks; preparation grows
0.11359 -> 1.39511 seconds. Mean complete time grows 12.70798 -> 13.32969 seconds,
with three of four pairs slower. Peak RSS has mixed signs and no demonstrated
improvement. The 2,183,937-byte new index is included in sidecars; gzip plus
first-trial sidecars grows 19.04%. All prior history and trial archives remain
additional retained state.

Only new source records enter extraction; their dependencies can still be old.
Incremental discovery visits 1,181 nodes versus 3,708 in independent untimed full
reconstruction. This is a traversal-count saving, not a matched total-time result
against rebuilding. Both complete lineages and ordinary proof/query audits
remain mandatory. Descriptions are hints; pending matches require checked causal
materialization, exact containment and current-query guards. All preparation,
merge, serialization, checking, persistence and replay costs are charged.

A separate read-only probe finds an old ready support under case 121's alternative
guard, potentially avoiding 20 local expansions. The probe uses the pre-query
archive, publishes no target proof and does not demonstrate a batch speedup.
Guard selection is the next matched experiment. Case 121 is now retained: restore
the starting snapshot for a controlled reproduction and use fresh queries for
generalization. Missing-clause proximity alone never justifies a negative answer.

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

The new manifest binds **61 artifacts**. The next preservation audit inherits
**4406 artifacts / 77 manifests**.
