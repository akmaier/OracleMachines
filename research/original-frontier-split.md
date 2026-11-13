# Resume an uncovered original through a saved cofactor pair

2026-11-13. The next non-affine residual shrinks from **20 variables / 80 clauses**
to an open **13-variable / 62-clause** obligation, with its other branch closed.
Ten new recognition states suffice. Structural coverage remains **57/83**, also
without growth exceptions. This is progress within one retained decomposition,
not another original-level closure or an unrestricted-SAT complexity result.

## Selection and structural result

The new `continue_cnf_original_splits.py` scheduler preserves all five evidence
lists, including the affine family certificate. It first resumes missing children
of saved splits, then their open descendants. When those are complete, it selects
the smallest eligible original-frontier leaf by variable count, literal count
and stable source key. It ranks up to 64 saved pairs by uncovered children,
missing children, maximum cofactor support, total cofactor literals and variable
ID. These are deterministic heuristics, not a minimum-expansion proof.

With no old open split child, this chooses the **20-variable / 80-clause /
285-literal** leaf of development case **73** (original 1444, historical
`subsumption_holdout3/n48`). All **fourteen retained pairs** are ranked. Variable
**18** has score `[2, 2, 18, 433, 18]`. Both saved clear unit closures are reused.
No fresh source-assumption trace is required for the split itself; recognition
of its descendants still performs new work.

| Branch | Saved cofactor | Checked structural path | Result |
|---|---|---|---|
| 18 = false | 18 variables / 61 clauses | Binary-path deletion, then five variable eliminations | 13 variables / 62 clauses remain open |
| 18 = true | 18 variables / 72 clauses | Probe reductions to 9 variables / 20 clauses, then 4 variables / 5 clauses | Recognized as 2-CNF, dual-Horn and one-valid |

The false path passes clause counts 59, 57, 56, 58 and 60 before ending at 62;
smaller support does not require monotonically decreasing clause count. All row
bindings and exact projection obligations remain checked. Its final CNF has
**219 literal occurrences**, six binary clauses, thirty ternary clauses, fifteen
width-four clauses, nine width-five clauses and two width-six clauses. The direct
affine extractor still finds **zero equations**.

Independent reference proofs establish that the 20-variable source and both
cofactors are SAT and verify model lifting. This does not complete the requested
structural coverage: both branch decompositions must be available, and the
13-variable leaf remains outside the recognized families. No newly gained
original SAT verdict is claimed here; there is no coverage gain.

## Costs and persistence

| Work | Seconds |
|---|---:|
| Restore prior checkpoint | 15.43036 |
| Prepare checked routes and roots | 65.86672 |
| Navigate original frontier and rank retained pairs | 0.06676 |
| Acquire both branches under one shared 32-state allowance | 0.04525 |
| Compose coverage and diagnostics | 0.15643 |
| Export immutable delta | 5.18092 |
| Full cold inventory audit | 107.92519 |
| Cold route reconstruction and diagnostics | 63.93178 |
| Reference acquisition / cold reference DAG check | 0.01298 / 1.03740 |
| Complete pipeline, including remaining I/O | **267.75550** |

The ten new nodes are five eliminations, one binary-path reduction, two probe
reductions, one recognized family and one unresolved leaf. This shared admission
allowance charges every newly entered recognition state, not only published
roots. It is not a CPU, byte or peak-RAM bound. No branch is pending.

A small matched control rebuilds the same two unit closures and checks the same
cofactor bindings. Saved replay takes **0.000695 s**, versus **0.000774 s** for fresh
acquisition/checking in this single resident sample. Fresh acquisition charges
two traces and 994 propagation literal visits; both arms charge 994 reconstruction
literal visits. Saved replay also reads 6,244 bytes of trace records. This tiny
single-sample difference establishes no robust timing advantage or whole-solver
speedup. Prior acquisition and cold preparation remain charged.

Working SQLite grows **126,976 bytes**, from 769,847,296 to **769,974,272 bytes**,
and holds **41,738 pattern nodes**. All earlier rows survive unchanged, including
1,548 sources, 21,838 residuals, 563 pivot trials, 25 coupled trials, one growth
trial, 87 probe windows and 128 continuation rows. The immutable delta occupies
196,608 raw / **8,671 compressed bytes**. Split, selection, diagnostics and coverage
sidecars are additional storage. Smaller residuals do not shrink this append-only
archive.

The reference archive preserves all **1,883** earlier nodes within **1,898** nodes.
Its database is 14,311,424 bytes, an increase of 20,480 bytes, and the complete
compressed archive is 938,498 bytes. The inherited reference helper reports
counters for its last solve; they are not aggregate counters for all reference
queries. No new full-suite or Lean result is claimed.

## Validation, resumption and next target

Twenty-seven targeted tests pass, including a regression in which partial split
acquisition is resumed without losing the separate affine-family route. Duplicate
resumption preserves evidence and a conflicting split is rejected. The run checks
all inventory/residual nodes, old-row preservation and idempotent delta application.
The independent validator reproduces selection from the parent, validates both
branches, replays all five evidence lists and coverage/ablation, checks the saved
matched control, and verifies the reference DAG and model lifts with new discovery
disabled. This independent cold replay passes in **164.80960 s** with both
reconstructed inventories byte-identical after read-only checks. Its final result
and hashes are recorded in `validation.json`.

Resume **`experiments/results/cnf-original-split/report.json`** with
**`continue_cnf_original_splits.restore_checkpoint` and its imported `routes_for`**.
Keep all five evidence lists: rewrites, **42 learned bases, 155 augmented blocks,
eight splits and one affine family record**. Earlier lemma sidecars remain intact.
Original selected frontiers and external split frontiers are separate scheduling
views; use the latter to reach the new 13-variable leaf rather than restarting
its 20-variable parent.

The next inexpensive discovery opportunity is explicit: the 13-variable leaf
has already probed variables **6, 9, 12 and 13**, but ordinary candidates
**1, 4, 7 and 8** remain untried. Test that one four-variable block before paying
for another conditioning layer. If it is clear, retain the negative result and
compare its newly available pairs or source-proved augmentation. The wider
18-base / 92-variable learned queue, including four candidates on case 30's
29-variable leaf, remains available. Do not rerun the exhausted 20-variable
parent's ordinary stream or the unchanged affine scan.

Preparation and checking still dominate total runtime. Dependency-local checking
of complete positive coverage plans remains the main cost opportunity; compact
fact replay alone does not discharge that obligation. A uniformly cheap exact
decomposition of every CNF, compact persistent closure and a bound on total
expansion states remain open.

```sh
python3 -m unittest solver.test_cnf_original_splits solver.test_cnf_trace_split \
  solver.test_cnf_split_batch solver.test_cnf_split_frontier \
  solver.test_cnf_route_composition solver.test_cnf_affine_clause \
  > /tmp/original-split-tests.txt 2>&1
python3 experiments/validate_cnf_original_splits.py \
  experiments/results/cnf-original-split --test-log /tmp/original-split-tests.txt
```
