# Structural moves missed by single-variable repair

This diagnostic investigates the next reuse gap after affected-clause repair.
The current implementation rejects all **240 updates** in **12 constructed
histories**, although an independently checked coordinated change exists for
every update. None of these rejections exhausts the discovery budget. The
histories remain satisfiable and lie in explicitly tractable structures.

This is evidence of missed reuse in our interface, not a measured speedup from
an implemented replacement. The generator supplies the structure and candidate
move. It does not solve discovery, general block repair, source certification or
incremental index maintenance.

## Cases and current costs

Each history has 8 or 32 disjoint blocks. Once per block, the generator adds a
unit that the current model fails. These additions depend on the current model;
the exact resulting clauses and proposed moves are retained in `report.json`.

| Family | Block sizes | Supplied coordinated change | Why one flip fails |
| --- | --- | --- | --- |
| Equivalence chains | 2, 8, 32 variables | Flip the whole chain. | Adjacent variables must remain equal. The formulas are simultaneously Horn, dual-Horn, 2-CNF and affine. |
| Even parity | 3 variables, explicit four-clause CNF | Flip two variables. | Changing one variable changes parity. |
| Complete bipartite matching | 2 or 4 choices/resources per block | Swap two matched edges, changing four indicator variables. | Setting the requested edge alone conflicts with its resource's existing owner. |

| 32-block case | Fresh acquisitions after the base | Logical archive bytes | Current acquisition/update seconds |
| --- | ---: | ---: | ---: |
| Equivalence, 2 variables/block | 32 | 127,127 | 0.1215 |
| Equivalence, 8 variables/block | 32 | 824,739 | 0.4880 |
| Equivalence, 32 variables/block | 32 | 3,792,631 | 2.6971 |
| Parity, 3 variables/block | 32 | 326,256 | 0.1848 |
| Matching, 2 choices/block | 32 | 245,911 | 0.1521 |
| Matching, 4 choices/block | 32 | 2,267,324 | 0.9459 |

Each case retains 33 bases. A short local update still triggers full-source
materialization and acquisition, even though the changed structure is known and
other blocks are independent. Candidate discovery in the current interface only
tries the variable in the new unit. Its failure is not evidence that finding the
coordinated change is difficult on these particular families.

Seconds include initial preparation plus each rejection and fallback operation,
including fallback source reconstruction, solving, index construction, checking
and persistence. Optional witness export, supplied-move construction/full-source
validation, row digests, cold replay and compression are outside these times.
There is no proposed-method timing comparison. These are single diagnostic
samples, not a representative SAT workload distribution or a memory/RSS profile.

## Implications for the next investigation

1. A literal-equivalence block can represent many variable changes with one
   independent Boolean choice. Start with checked simultaneous repairs over such
   blocks; test coupled and inconsistent controls as well as disjoint chains.
2. Reuse class-specific transformations: nullspace directions preserve old
   affine equations, and valid alternating cycles preserve matching constraints.
   A transformation must still respect earlier additions and all constraints
   outside its certified internal structure.
3. Retain component source, model and proof references across fallback. The
   general residual cache currently flattens SAT models and does not keep the
   matching, implication or affine state used to produce them. Those states need
   a common source/dependency interface before they can be reused reliably.
4. Aggregate all count changes before checking a simultaneous repair. Its
   intermediate one-variable states may be invalid even when the final state is
   valid. Internal preservation does not make existing per-clause counts correct
   automatically: maintain them, or use explicit lazy invalidation and rebuild.

The quantity to minimize is the number of independent structural choices and
affected interfaces, together with recognition and maintenance cost. A long
change vector may have a short structural description. Full witness output still
costs its encoded size, and arbitrary CNFs need not admit small descriptions or
cheaply discoverable moves.

## Preservation and reproduction

The runner retains all sources, additions, current solver metrics and proposed
changes. Every historical source and witness is cold checked. The independent
`archive-replay.json` check decompresses all 12 snapshots, validates every version
and proposed move, reads every residual and requires identical database hashes
with zero new expansions. Earlier experiments and solver code are unchanged.

```sh
python3 experiments/probe_structured_repair_gaps.py --output /tmp/oracle-structured-gaps-new
```

Use a new output directory. Source fingerprints and limitations are in
`report.json`. The [priority record](../../../research/structural-reuse-priorities.md)
connects these controls to the broader cross-category investigation.
