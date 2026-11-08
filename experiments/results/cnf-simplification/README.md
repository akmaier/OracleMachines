# Checked unit and pure-literal simplification

This 841-source study extends all 775 projection-study sources with 48 seeded
random 3-CNFs (24 each on 12 and 20 variables at 4.25 clauses per variable), six
coupling controls with renamed/reordered variants, and six growing controls.
Generators supply no family labels to the inventory. Every mode uses the same
ordinary solver on the original source; this is a discovery experiment, not an
integrated SAT acceleration claim.

## Exact transformation and recognition

The inventory reuses the solver's unit propagation, then optionally removes
clauses satisfied by globally pure literals until a fixed point. A separate
checker replays unit reasons against the full source and all earlier forced
assignments, reconstructs restriction directly, and checks each complete pure
round against the entire remaining CNF. It retains assignments and exact child
bindings. Pure absence must include coupling clauses: a positive literal in an
easy component is insufficient if its negative occurs elsewhere.

These are standard SAT reductions. A reduced formula describes the existential
projection onto its remaining variables, not all original satisfying assignments
and not their count. Every child model lifts to a checked parent model by adding
the recorded choices and assigning any other disappeared variables arbitrarily.
Forced conflicts produce an empty clause only with a checked false reason.
Successful rewrites strictly reduce support and consume no conditioning depth.
All earlier family outcomes, source records and solver results remain available.
Versioned policies isolate the old records and the two ablations.
An edit has a new exact source identity. In particular, adding an opposite-sign
coupling invalidates an earlier purity argument; the new node must be checked
again. This implementation has no incremental purity-dependency maintenance.

The matching/parity example now follows `project -> simplify -> matching`:
13 variables/61 literals become 10/29, then 9/27 after setting the pure bridge
variable. It closes without branching. A bridge constrained in both polarities
is not removed as pure; the negative controls need further conditioning or
propagation. Root recognition cells remain unchanged; the new coverage comes
from checked transformations and decomposition, not a new root family.

## Matched results

Coverage excludes the 512 exhaustive two-variable sources, which every mode
closes. The remaining denominator is 329. A closed decomposition is a structural
certificate and may describe either SAT or UNSAT.

| Policy | Closed / 329 | Total seconds | Discovery seconds | SQLite bytes | Cold audit seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Solver only | n/a | 2.46113 | 0 | 9,433,088 | 0.46435 |
| Projection, depth 0 | 123 | 3.12964 | 0.73628 | 14,372,864 | 0.67701 |
| Units + pure, depth 0 | 162 | 3.52490 | 1.13643 | 14,831,616 | 0.88492 |
| Projection, depth 2 | 217 | 8.09694 | 5.66457 | 39,727,104 | 2.72370 |
| Units only, depth 2 | 289 | 6.60422 | 4.20884 | 32,190,464 | 2.24185 |
| Pure only, depth 2 | 249 | 8.50842 | 6.01604 | 38,719,488 | 2.88497 |
| Units + pure, depth 2 | 290 | 7.15375 | 4.62418 | 31,731,712 | 2.43583 |

Combined depth-two closure improves on 73 sources and loses none in this corpus.
All 36 prior misses among the original 664 sources close. Units alone close 35
of those 36; pure alone closes 15. Original case 631 needs the combination under
this planner. All 32 affine mixtures close. However, only 10 of the 48 new random
3-CNFs close, both for units-only and combined; pure-only closes none. The other
remaining miss is the arbitrarily renamed wide-boundary encoding-cap control.
The resulting 39 misses remain exact archived inputs, not discarded outliers.

Units-only is faster than the combined policy while missing just one additional
source. Pure-only takes longer than projection at depth two despite its coverage
gain. Depth-zero combined processing also increases time, space and cold replay.
The first 775 sources take 3.64266 s with projection versus 2.60284 s combined at
depth two. These are single sequential samples, not statistical speedup claims.

Combined depth-two pattern nodes fall from 6,358 to 3,526. Its 1,162 simplification
edges reference 550 distinct children, reusing 612 references within the same
policy and depth. This does not imply cross-policy or arbitrary-isomorphism
sharing. Full exact sources and bindings are retained: logical source payload
grows from 1,570,077 to 1,686,976 bytes. All modes retain the same 2,146 ordinary
solver residuals. Warm inventory time is 82.79 versus 82.62 ms for projection and
combined depth two. Separate six-case peak Python tracing is 153,371 versus
152,490 bytes; this small diagnostic excludes native SQLite memory and RSS and
does not measure the 841-source peak. At depth zero the traced peak increases.

## Costs, failures and next target

Random 3-CNFs account for 3.26227 of 4.62418 seconds of combined discovery and
3.95405 of 7.15375 seconds total. The 38 remaining misses there are the next
discovery target: profile retained alternatives and compare structure-aware
conditioning with the frequency-first policy under matched work budgets. Record
lookahead cost, exposed tractable components and residual identity reuse; merely
raising depth is not evidence of a better decomposition principle.

The largest individual operation is still the 258-variable coupled affine
source (548.78 ms total; 17.63 ms discovery): the separate solver recomputes its
original decision. Checked decision integration remains supporting work. Native
affine boundaries could avoid the retained direct-encoding cap. Neither is
implemented by this study.

Propagation and pure fixed points still scan repeatedly. On the control with a
512-variable unit chain, discovery takes 180.67 ms and counts 1,081,456 propagation
literal visits. The pure-chain control takes 144.71 ms and counts 276,026 pure
discovery visits. That generator contains a disjoint signed chain plus matching
with a pure bridge; its parent profile performs work even before decomposition.
It must not be presented as a connected chain-to-matching interaction. Avoiding
unused parent work and queue-based maintenance are supporting opportunities.

Operation time includes discovery, recognition, certificate checking, ordinary
solving, serialization, persistence and successful root lifting. Initialization,
generation, truth tables, summary walks, inter-operation checks and offline gzip
are separate. Full cold checks cover all attempted alternatives, every source
and all solver certificates. Seven new and five previous projection-study
archives replay with no byte changes. Compressed archives and SHA-256 hashes
are retained; the full report uses compact JSON to avoid multiplying whitespace.

All 301 Python tests pass. New checks enumerate all 512 two-variable clause sets
under all three policies, compare existential fibers and lifts, exercise random
renamings and adversarial couplings, and reject forged reasons, omitted steps,
false purity and corrupted cold records. Existing Lean pure-repair and condition
semantics remain applicable; the Lean build passes with no new theorem or Python
refinement. No compact closure or uniformly polynomial arbitrary-SAT solution
follows from these results.

## Reproduction

```sh
python3 experiments/compare_cnf_simplification.py --output /tmp/cnf-simplification-new
python3 experiments/analyze_cnf_simplification.py /tmp/cnf-simplification-new
python3 -m unittest discover -s solver -p 'test_*.py' -q
```

The output directory must be new. `report.json` preserves exact sources, policy
settings, every row and code fingerprints. `summary.json` contains aggregates;
`mechanisms.json` records ablations, rewrite chains, reused children and all
remaining misses. Previously published experiment files are unchanged.
