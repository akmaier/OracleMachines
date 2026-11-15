# Complete the retained development subset

Two independent six-batch sequences raise checked structural coverage **78/83 ->
83/83**, completing cases 1196, 1376, 1064, 1302 and 1443. The independent answers
are three SAT and two UNSAT originals. Both sequences store **144 records** on
**147 admissions / 144 distinct inputs**; three interrupted inputs are completed.
The per-batch policy remains 32 admitted states and twelve advances. The run
permits six batches instead of four, so it is not a matched comparison with the
earlier shorter sequences. See the [research account](../../../research/case1196-completion.md).

Four small terminals expose Horn/zero-valid, 2-CNF and dual-Horn/2-CNF/one-valid
overlaps. A bounded diagnostic checks all **9,312 terminal assignments** and both
polarity maps on all **9,216 source assignments**, including name transport. The
83 inputs exactly match the old retained-policy misses in the historical
**1,497-input corpus**. They are adaptively reused development cases. No fresh
combined-policy replay of the full corpus or new holdout evaluation is claimed;
the old **902/985 non-tiny** result remains separate.

Mean six-batch time is **77.64131 seconds**, including
**64.54345 seconds** startup and **3.20071 seconds** local
expansion. Parent restoration adds **27.63698 seconds**, permitting the checked
materialization without reporting whether cache or fallback was used. History
grows **2,019,328 bytes**; separate reference evidence adds **2,010 nodes /
15,405,056 SQLite bytes**. No new full snapshot is stored; peak RAM is unmeasured.
These development repetitions establish reproducibility, not a matched speedup.

The complete selected proof has **4,822 steps**. Only **14 exact steps** are shared
across originals: ten family leaves and four direct retained-plan references to
family leaves. All shared CNFs have at most **two variables**. The sum of separate
per-root step visits is 4,991, versus 4,822 unique steps: **169 repeated visits**.
This is graph overlap, not a measured runtime saving or an exhaustive search for
equivalent larger components.

Reproduce the acquisition from its frozen parent into a fresh directory:

```sh
python3 experiments/continue_cnf_case1196_discovery.py /tmp/cnf-case1196-new
python3 experiments/validate_cnf_case1196_discovery.py /tmp/cnf-case1196-new
python3 experiments/analyze_cnf_case1196_discovery.py /tmp/cnf-case1196-new
python3 experiments/analyze_cnf_case1196_reuse.py /tmp/cnf-case1196-new
python3 experiments/analyze_cnf_case1196_completion.py /tmp/cnf-case1196-new
python3 experiments/analyze_cnf_case1196_sharing.py /tmp/cnf-case1196-new
```

Do not overwrite this frozen result. Independent reconstruction disables both
parent materialization paths, fresh discovery and reference search. It checks
both sequences, every acquisition prefix, **14 saved global queries**, original
SAT models and all **8,789 reference nodes**. Replay passes in **1234.36954 seconds**
as an audit cost. The bounded completion diagnostic costs
**0.19350 seconds** separately. All **299 tests** pass before production.
All **2,650 prior artifacts / 43 manifests**, **145 prior source fingerprints** and
**6,779 old reference payloads** remain unchanged. The manuscript builds to
**172 pages**, preserving all **64 existing proof blocks**, without undefined
references or overfull boxes. No Lean theorem changes are claimed.

`structural-findings.json` records checked ancestry, branches and prefixes;
`discovery-summary.json` records costs, entries and exact reuse;
`reuse-findings.json` records cross-original intersections, branch admission counts,
polarity transitions and the external use of immutable unresolved records.
`completion-findings.json` binds the exact historical subset and independently
checks the small family predicates and pointwise polarity equivalence.
`sharing-findings.json` measures sharing across all 83 selected proof roots and
checks owner bitsets against independent root-by-root traversal; the diagnostic
costs **0.06660 seconds** separately.
`validation.json` and `manifest.json` bind checks, sources and preservation evidence.

Restore `experiments.continue_cnf_case1196_discovery.restore_checkpoint` with this
`report.json` as the prepared state. The default permits checked materialization;
`materialized=False` reconstructs the authoritative history. **`next_selection.source`
is null**; there is no outstanding selected continuation on these 83 originals.
Do not restart the completed initial case 1196. Preserve evidence **(1,42,156,98,1)**
and two bridges. Next bind old successful plans in a combined full-corpus query,
then evaluate transfer to new unlabelled inputs under a frozen policy and budget,
charging preparation and forcing-trace acquisition. Finite completion does not
establish an efficient solution of arbitrary SAT.
