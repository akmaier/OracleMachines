# Pending discovery through mixed reductions

Two independent four-batch sequences complete **case 1062**, raising structural
coverage **72/83 -> 73/83**. Both store **68 records**: 23 probes, 22 eliminations,
13 binary-path reductions, three polarity transformations, five family terminals
and two unresolved intermediate records covered through later explicit split rules.

The three polarity transformations expose Horn formulas without changing their
size triples. Four terminals are Horn and all-zero satisfiable; a fifth is all-zero
satisfiable outside Horn and 2-CNF. Original 1062 and all four touched split sources
are SAT. The experiment completes structural coverage with both conditioning
premises, separately from finding one original SAT witness. See the
[research account](../../../research/pending-discovery-closure.md).

The sequence charges **84 entries / 68 distinct inputs**, including sixteen
re-entries from interrupted batches. All eight inputs interrupted in the preceding
checkpoint are completed too. No entered input remains unstored. Closing the first
19-variable branch exposes a different 36-variable branch: selected size is not
monotone progress in original coverage. Exact reuse is measured by stored identities,
not by matching reduction names or sizes.

Mean complete sequence time is **70.46120 seconds**, including
**63.74848 seconds** initial startup and **0.84877 seconds** local
expansion. Checked parent restoration costs **8.70349 seconds** using the
existing materialization. No new full snapshot is stored. History grows
**843,776 bytes**; reference evidence adds **124 nodes / 491,520 SQLite bytes**.
These repeated development runs establish reproducibility, not a matched speedup;
peak RAM is unmeasured.

Reproduce into a fresh result directory:

```sh
python3 experiments/continue_cnf_pending_discovery.py /tmp/cnf-pending-new
python3 experiments/validate_cnf_pending_discovery.py /tmp/cnf-pending-new
python3 experiments/analyze_cnf_pending_discovery.py /tmp/cnf-pending-new
python3 experiments/analyze_cnf_pending_reuse.py /tmp/cnf-pending-new
```

Do not overwrite this frozen result. Independent reconstruction disables the
materialization path, fresh recognition and reference search. It checks both
sequences, every acquisition prefix, all ten saved global queries, actual original
scope, the original SAT model and all **5,612 reference nodes**. Replay passes in
**934.44048 seconds** as an audit cost. All **299 tests** pass. All **2,277 prior
artifacts / 40 manifests**, **131 prior source fingerprints** and **5,488 prior
reference payloads** remain unchanged. The manuscript builds to **170 pages**,
preserving all **64 existing proof blocks**, with no undefined references or overfull boxes.

`structural-findings.json` records checked ancestry, branch results and prefixes;
`discovery-summary.json` separates admission re-entry, stored identity reuse and
family recognition. `reuse-findings.json` compares touched prefixes across old
original scopes and checks the three polarity transitions and the two formerly
unresolved records' presence in the final positive proof. These prefix intersections
do not cover every proof alternative or all possible equivalent encodings.
`validation.json` and `manifest.json` bind checks, sources and preserved artifacts.

Resume `experiments.continue_cnf_pending_discovery.restore_checkpoint` with this
`report.json`. The default uses the checked parent materialization and applies
this new delta; `materialized=False` replays the original history independently.
Use **`next_selection`**, not the completed initial source: **case 1121 / index 23**,
**41/174/513**, no pending split. Preserve evidence **(1,42,156,72,1)** and two bridges.
Ten originals remain structurally uncovered; no arbitrary-SAT polynomial bound follows.
