# Case 1227: conditional refutation and a shared terminal

Two independent repetitions close original case 1227 and increase structural
coverage **69/83 -> 70/83**. One saved split produces two probe chains, with
**five new records** and **one reused empty-clause terminal**. All five admissions
are stored; no states remain interrupted. The independent original reference
answer is UNSAT. This is broader checked coverage, not a new tractable class.

Mean local expansion is **0.15935 seconds**; worker time is **1.18892 seconds**;
the complete sequence is **68.83255 seconds**, including **66.68418 seconds**
initial preparation and global checking. Shared parent restoration and final
cold verification remain separate. There is no comparative solver speedup claim.
Structural history grows **73,728 bytes**; reference evidence grows by **380 nodes**.
See [the research account](../../../research/conditional-refutation-reuse.md).

Reproduce into a fresh output directory:

```sh
python3 experiments/continue_cnf_case1227.py /tmp/cnf-case1227-new
python3 experiments/validate_cnf_case1227.py /tmp/cnf-case1227-new
python3 experiments/analyze_cnf_case1227.py /tmp/cnf-case1227-new
```

Do not overwrite this frozen result. The parent checkpoint, implementation hashes,
exact delta, split records and certificates are bound in `report.json`.
`reconstruction.json` independently checks both repetitions, all **four saved
global queries**, every acquisition prefix and all **5,182 reference nodes**,
with fresh discovery and reference search disabled. The replay passes in
**559.54505 seconds**. Its elapsed time is an audit cost, not a comparison.
All **283 tests** pass. All **2,077 older artifacts / 37 manifests** and **4,802
older reference payloads** remain unchanged. The manuscript builds to **168 pages**
with all **64 existing proof blocks** preserved and no undefined references or
overfull boxes.

`structural-findings.json` records the exact chains, ancestor bindings and next
frontier. `discovery-summary.json` distinguishes five distinct new prefix nodes
from one inherited terminal visited twice. `cost-summary.json` retains samples
and individual preparation, acquisition, checking and persistence costs.
`validation.json` binds checks, sources and prior manifests; `manifest.json`
hashes this directory's artifacts except itself.

Resume with `experiments.continue_cnf_case1227.restore_checkpoint` and this
report's **`next_selection`**: **case 1406, index 64, 40/168/505**, no pending
split. Keep evidence **(1,42,156,64,1)** and **two bridges**. Thirteen originals
remain uncovered; no uniform polynomial bound on arbitrary SAT follows.
