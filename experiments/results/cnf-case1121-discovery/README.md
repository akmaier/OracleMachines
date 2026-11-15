# Mixed-family discovery from case 1121

Two independent four-batch sequences complete **case 1121 (SAT)** and **case 1336
(UNSAT)**, raising checked structural coverage **73/83 -> 75/83**, then continue
into case 1063. Both store **67 records** and charge **81 admissions / 67 distinct
inputs / 14 reentries**. The existing inference rules and scheduling policy are unchanged.
See the [research account](../../../research/case1121-discovery.md).

All admitted inputs are stored at the end, yet the final **22/89/309** split
remains pending. Its first branch admits sixteen states and completes; its second
branch admits zero new inputs and remains pending. Preserve both the admission ledger and
this separate structural obligation. An affine projection reduces **14/16/34 ->
13/14/30**; an exhaustive bounded audit checks all **16,384 source assignments**
and **8,192 boundary assignments** and lifts every satisfying boundary model.
General projection still requires recognition and may exceed the boundary encoding budget.

Mean four-batch sequence time is **72.02025 seconds**, including
**64.41599 seconds** initial startup and **1.23698 seconds** local
expansion. Parent restoration adds **14.70057 seconds**, permitting the
checked materialization without recording whether cache or fallback was actually used.
History grows **913,408 bytes**; separate reference evidence adds **671 nodes /
5,423,104 SQLite bytes**. No new full snapshot is stored. These development
repetitions establish reproducibility, not a matched speedup; peak RAM is unmeasured.

Reproduce into a fresh result directory:

```sh
python3 experiments/continue_cnf_case1121_discovery.py /tmp/cnf-case1121-new
python3 experiments/validate_cnf_case1121_discovery.py /tmp/cnf-case1121-new
python3 experiments/analyze_cnf_case1121_discovery.py /tmp/cnf-case1121-new
python3 experiments/analyze_cnf_case1121_reuse.py /tmp/cnf-case1121-new
python3 experiments/analyze_cnf_case1121_projection.py /tmp/cnf-case1121-new
```

Do not overwrite this frozen result. Independent reconstruction disables the
materialization path, fresh recognition and reference search. It checks both
sequences, every acquisition prefix, all ten saved global queries, original scope,
the original SAT model and all **6,283 reference nodes**. Replay passes in
**946.06368 seconds** as an audit cost. The separate exhaustive projection
diagnostic costs **0.06950 seconds**. All **299 tests** pass before production.
All **2,400 prior artifacts / 41 manifests**, **135 prior source fingerprints** and
**5,612 prior reference payloads** remain unchanged. The manuscript builds to
**171 pages**, preserving all **64 existing proof blocks**, with no undefined
references or overfull boxes. No Lean theorem changes are claimed.

`structural-findings.json` records ancestry, branches and prefixes;
`discovery-summary.json` separates entries, storage and exact reuse;
`reuse-findings.json` compares measured prefixes across original scopes and
inspects polarity and unresolved records. `projection-findings.json` records the
exhaustive projection check and the pending branch with no new admissions in both repeats.
These intersections do not exhaust every proof alternative or equivalent encoding.
`validation.json` and `manifest.json` bind checks, sources and preserved artifacts.

Resume `experiments.continue_cnf_case1121_discovery.restore_checkpoint` with this
`report.json`. Its default permits the checked parent materialization and applies
this delta; `materialized=False` replays the authoritative history independently.
Use **`next_selection` plus its pending split**, not the completed initial source:
**case 1063 / index 15**, **22/89/309**. Selector indices remain empty; actual
dependency ancestry supplies that scope. Preserve evidence **(1,42,156,78,1)** and
two bridges. Eight originals remain structurally uncovered; no arbitrary-SAT
polynomial bound follows.
