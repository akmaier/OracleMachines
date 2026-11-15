# Retained discovery across original scopes

Two independent four-batch sequences cover cases **1406 and 1195** and preserve
partial expansion of **case 1062**. Structural coverage rises **70/83 -> 72/83**.
The union stores **63 records**: 19 probes, 27 eliminations, 13 binary-path
reductions, one zero-valid/one-valid terminal and three unresolved records.

Both newly covered originals are **SAT**, while the selected conditional
residuals just refuted are **UNSAT**. Checked dependency paths retain the earlier
conditioning; selected-residual truth must not be transferred to an original.
The new **4/5/14** terminal in case 1062 does not close its other obligations.

Mean complete sequence time is **73.47861 seconds**, including **66.09003
seconds** initial catalog/query/serialization and **4.17511 seconds** in four
workers. Local expansion within workers is **1.02047 seconds**. Shared parent
restoration, final global checking, full delta comparison and reference work
remain separate. One startup serves four batches; there is no matched
fresh-per-batch control or general speedup claim. Structural storage grows
**856,064 bytes**; reference evidence adds **306 nodes**.

See [the research account](../../../research/retained-discovery-sequence.md).
Reproduce from the repository into a fresh output directory:

```sh
python3 experiments/continue_cnf_retained_discovery.py /tmp/cnf-retained-discovery-new
python3 experiments/validate_cnf_retained_discovery.py /tmp/cnf-retained-discovery-new
python3 experiments/analyze_cnf_retained_discovery.py /tmp/cnf-retained-discovery-new
```

Do not overwrite this frozen result. `report.json` binds the parent checkpoint,
implementation hashes, deltas, split records and positive certificates.
`reconstruction.json` independently checks both repetitions, all **ten saved
global queries**, each acquisition prefix, exact original scopes and all **5,488
reference nodes**, with fresh recognition and reference search disabled. Replay
passes in **918.21023 seconds**. Its elapsed time is an audit cost,
not a performance comparison. All **283 tests** pass. All **2,129 older artifacts /
38 manifests** and **5,182 older reference payloads** remain unchanged.

The four batches charge **74 admission entries / 71 distinct inputs**; all three
states interrupted in batch 2 are stored in batch 3. Eight inputs remain without
records. `structural-findings.json` preserves their keys, actual ancestor paths,
local family outcomes and the next source. `discovery-summary.json` distinguishes
exact prefix-node reuse across original scopes from repeated reduction methods;
prefix counts exclude other alternatives and include pending-split replays.
`cost-summary.json` retains individual timings and work counts. `validation.json`
binds the checks and prior manifests; `manifest.json` hashes this result directory
except itself. The manuscript builds to **169 pages**, preserving all **64
existing proof blocks**, with no undefined references or overfull boxes.

Resume with `experiments.continue_cnf_retained_discovery.restore_checkpoint` and
**`next_selection` plus its pending split**: **19/77/261**, within **case 1062,
index 14**. The selector's original-index list is empty; the checked lineage
provides its scope. The report's initial source belongs to completed case 1406.
Keep evidence **(1,42,156,69,1)** and **two bridges**. Eleven originals remain
structurally uncovered; no unrestricted-SAT polynomial bound follows.
