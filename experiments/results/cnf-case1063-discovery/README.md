# Complete retained branches from case 1063

Two independent four-batch sequences raise checked structural coverage
**75/83 -> 78/83**, completing cases **1063, 1371 and 1158**. All three originals
are SAT. Both sequences store **54 records** on **63 admissions / 54 distinct inputs**;
nine interrupted inputs are re-entered and completed. The existing inference rules
and scheduling policy remain unchanged. See the
[research account](../../../research/case1063-discovery.md).

Case 1063's pending branch completes with three new records after fifty had been
stored. Across both checkpoints, that original charges **67 entries / 53 distinct
inputs / 14 reentries**, with all inputs stored. The first selector keeps its empty
original-index list; an actual checked dependency path supplies scope 1063/index 15.
A **5/4/8** terminal overlaps Horn, 2-CNF and zero-valid. A polarity transformation
exposes a **10/12/25** Horn, zero-valid terminal. Case 1158's selected **43/176/531**
residual is UNSAT, while the **48/204/612 original is SAT**. Its conditioning ancestry
prevents unconditional transport of that refutation.

Mean sequence time is **71.68154 seconds**, including
**64.51870 seconds** startup and **1.01341 seconds** local
expansion. Parent restoration adds **21.22320 seconds**; the wrapper allows
materialization without reporting whether cache or fallback was actually used.
History grows **733,184 bytes**; separate reference evidence adds **496 nodes /
3,682,304 SQLite bytes**. These development repetitions establish reproducibility,
not a matched speedup. No new full snapshot is stored; peak RAM is unmeasured.

Reproduce into a fresh directory:

```sh
python3 experiments/continue_cnf_case1063_discovery.py /tmp/cnf-case1063-new
python3 experiments/validate_cnf_case1063_discovery.py /tmp/cnf-case1063-new
python3 experiments/analyze_cnf_case1063_discovery.py /tmp/cnf-case1063-new
python3 experiments/analyze_cnf_case1063_reuse.py /tmp/cnf-case1063-new
python3 experiments/analyze_cnf_case1063_inherited.py /tmp/cnf-case1063-new
```

Do not overwrite this frozen result. Independent reconstruction disables both
parent materialization paths, fresh discovery and reference search. It checks
both sequences, every prefix, ten saved global queries, the original SAT models
and all **6,779 reference nodes**. Replay passes in **961.01602 seconds** as an
audit cost. All **299 tests** pass before production. All **2,526 prior artifacts /
42 manifests**, **140 prior source fingerprints** and **6,283 old reference payloads**
remain unchanged. The manuscript builds to **172 pages**, preserving all **64
existing proof blocks**, with no undefined references or overfull boxes. No Lean
theorem changes are claimed.

`structural-findings.json` records checked ancestry, branch answers and prefixes;
`discovery-summary.json` records costs, entries and exact reuse;
`reuse-findings.json` adds cross-original prefix intersections, cumulative case-1063
admissions across checkpoints, branch admission counts and polarity transitions.
`inherited-findings.json` compares inherited unresolved records in the two saved
positive original-coverage proofs; earlier absence does not prove absence of a
local derivation. The reuse analysis also checks the two new immutable unresolved records' external split coverage in
the final positive proof. Prefix intersections do not exhaust all proof alternatives
or semantically equivalent representations. `validation.json` and `manifest.json`
bind checks, sources and preservation evidence.

Resume `experiments.continue_cnf_case1063_discovery.restore_checkpoint` with this
`report.json`. The default permits checked parent materialization; `materialized=False`
reconstructs the authoritative history. Follow **`next_selection`**, not the completed
initial source: **case 1196 / index 36**, **43/181/549**, **no pending split**. All admitted
inputs are stored. Preserve evidence **(1,42,156,82,1)** and two bridges. Five originals
remain structurally uncovered; no arbitrary-SAT polynomial bound follows.
