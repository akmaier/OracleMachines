# Retaining checked routes after clear probes

This experiment separates route maintenance from search selection. Both arms
use the unchanged `EarlyClosedExpansion` policy, which continues ordinary
probing unless a saved pair already has a closed child. They start from the
same case-specific archive, use the same twelve-advance and shared 32-state
limits, and preserve both split branches. The optimized arm retains a complete
checked route catalog when the only change is a checked clear probe row.

## Exact reuse condition

The helper `experiments/cnf_clear_probe_maintenance.py` builds the complete
catalog initially. It snapshots the SQLite connection's change count, each
probe table's largest row ID, external data version, schema version, admitted
state set and exact serialization of all five evidence lists plus bridges.
After an ordinary advance, the fast path requires all of the following:

- The reported record is clear, has no residual edge and binds the same source.
  There is no pending acquisition or newly admitted state.
- The sidecars and admitted state set are unchanged. The operation has either
  inserted exactly one row beyond the previous row-ID maximum, or reused an
  unchanged row already in the complete catalog without any database write.
- The persisted identity and payload match the record exactly. The original
  window or continuation checker accepts it, including the clear predecessor
  chain for a continuation.

The helper then inserts the checked record into the in-memory probe map. It
does not add a semantic route. New states, forcing, new split evidence and
other writes use a complete rebuild. An external database change or schema
change rejects reuse and requires reopening the inventory, since rebuilding
routes alone would leave the inventory's checked-node cache stale. This is an
exclusive, append-only in-process workflow; it is not a general concurrent
database cache or a serialized proof of trust.

The preservation argument is direct. Every structural rule depends on immutable
pattern nodes, retained sidecars, or a probe record with a residual edge. Under
the guard, none of these changes. A clear record contributes no premise or
conclusion to the structural rule graph, so its least fixed-point closure and
the existing positive witnesses are unchanged. Its saved attempts *do* enlarge
the pool of future split candidates. The probe maps are updated, and candidate
enumeration reads the authoritative saved traces; therefore those candidates
remain visible. Repeating the argument is valid only while each guard succeeds.
Forced records and acquired targets require the general activation procedure.
This establishes reuse of the existing catalog, not a new SAT tractability
result or a reason to skip future probing.

The extra retained snapshot is linear in serialized sidecar size. Each guard
still serializes those sidecars, checks bounded metadata and replays the new
probe record and any unchecked prefix. There is no claim of constant-time
maintenance. The helper avoids scanning and checking the rest of the route
catalog on eligible steps. It adds no persistent certificate format or table;
cold reconstruction uses the existing independent checkers.

## Reproduction

From the repository root:

```sh
python3 experiments/compare_cnf_clear_maintenance.py experiments/results/cnf-clear-maintenance
python3 experiments/validate_cnf_clear_maintenance.py experiments/results/cnf-clear-maintenance
python3 -m unittest solver.test_cnf_clear_probe_maintenance
```

The producer requires a new output directory; use another directory when
repeating it. Run timings serially, without simultaneous tests or paper builds.
Both modes receive independent copies of the same case-specific seed. Two
repetitions reverse mode order, with the first order also reversed between
cases. Case 1263 uses the latest authority; control 1189 uses its preserved
earlier checkpoint, before its later results existed. All prior results and
the union of new rows are preserved. Reference solving checks saved reductions
and models separately and never feeds structural closure.

## Measured result

The next original, **1263 / index 42**, closes in both modes, moving structural
coverage from **64/83 to 65/83**, also without growth-exception routes. The
historical forcing control 1189 closes in both modes too. Each mode follows
four advances and acquires eleven states on case 1263; the control takes eight
advances and twenty-one states. There are no unfinished admissions.

| Mean cost or retained size | 1263 full rebuild | 1263 maintained | 1189 full rebuild | 1189 maintained |
|---|---:|---:|---:|---:|
| Expansion seconds | 4.56885 | 2.46956 | 8.10837 | 2.24496 |
| Complete worker seconds | 17.23793 | 14.87208 | 20.13427 | 14.18042 |
| Route maintenance seconds | 4.25464 | 2.16703 | 7.83406 | 1.98107 |
| Acquisition and ranking seconds | 0.30900 | 0.29736 | 0.27035 | 0.26015 |
| Initial preparation seconds | 7.75101 | 7.69031 | 7.29974 | 7.26581 |
| External assumption attempts | 16 | 16 | 51 | 51 |
| Full rebuilds during expansion | 4 | 2 | 8 | 2 |
| Compressed delta bytes | 12,933 | 12,933 | 15,484 | 15,484 |
| Delta SQLite bytes | 241,664 | 241,664 | 397,312 | 397,312 |
| Extra retained serialized sidecar bytes | 0 | 1,220,757 | 0 | 941,068 |

Mean expansion falls **45.95% / 72.31%** and complete worker time falls
**13.72% / 29.57%**. Worker time includes preparation, checking, serialization
and delta export. Expansion sums selection, acquisition, route maintenance and
composition, excluding per-operation archive writes; the worker includes them.
External assumption counts exclude recognizer-internal probing, whose cost
remains included in acquisition. The sidecar snapshot column is serialized
payload, not measured peak RAM. Transient serialization and ordinary Python
object overhead remain additional memory costs. Persistent state does not
shrink; this optimization avoids computation and adds a resident snapshot.

The complete producer takes **316.04814 s**, including **62.36289 s** to restore
the current authority, **25.27426 s** to restore the historical control, and
**67.55856 s** for final route preparation plus global coverage. Union delta
export costs **5.54242 s**. These costs are charged separately from worker
comparisons. Preparation, export and global checking now dominate more of the
remaining total. The cold checker deliberately reconstructs full checked routes;
no cold-replay acceleration is claimed.

The union adds eleven patterns, one window, one continuation and two split
records. All control results already existed in the current authority, so the
union adds only the current case's work. The history grows **172,032 bytes** to
**774,000,640 bytes / 41,973 patterns**. Five evidence lists now have lengths
**(1, 42, 156, 33, 1)**, alongside two projection bridges. All 33 split sources
and both bridge targets close. The expanded positive witness has **3,239 steps**.
The independent reference archive keeps all 3,203 old nodes and grows to 3,259;
reference answers remain separate from structural closure.

Two repetitions on two reused development cases do not establish a confidence
interval, holdout improvement, optimal expansion policy or unrestricted-SAT
bound. This is a maintenance comparison with the previous ordinary scheduler.
The prior early-saved policy can avoid the clear advances themselves; these
savings must not be added to that policy's savings without a matched combined
experiment. The helper remains an optional research component.

Resume `experiments/results/cnf-clear-maintenance/report.json` with
`compare_cnf_clear_maintenance.restore_checkpoint`. Its SHA-256 is
`b4aa304049758bff8e80b2118437321a9edf7128657b3a9303a4985ae57daa78`.
Keep all five evidence lists and the separate `bridges` archive, and use the
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
Eighteen original inputs remain structurally uncovered. The next selected
source is original **1154 / index 27**, **38 variables / 158 clauses / 500
literal occurrences**, SHA-256
`f33c327595b24645a6f64e8a072295c51fb2a414872d0de0f84da49192f0085d`.

## Structural findings and validation

The first split, local variable 6 of the 37-variable source, is already the best
saved pair before the final ordinary block and remains best afterwards. Its
false raw cofactor has shape 34/136/401 and canonical shape 34/134/394. Probing,
binary-path deletion and two eliminations leave 31/125/377 unresolved. Its true
cofactor 35/138/416 follows three probe reductions to a retained 2/1/2 plan
recognized as both Horn and dual-Horn 2-CNF.

A clear window on the remaining 31-variable leaf saves a new pair for local
variable 9. Its false branch directly reuses a different retained 2/1/2 plan,
recognized as matching, dual-Horn and 2-CNF. Its true branch 30/119/354 reduces
through 26/88/240 to the retained empty-clause UNSAT terminal. Both first-level
cofactors are independently SAT; the second split has one SAT and one UNSAT
branch. All applicable SAT model lifts pass. These are exact local-variable
bindings along saved reductions, not an assertion that the original formula
belongs directly to one of these tractable families.

Independent cold replay passes in **313.36574 s**, forbidding both fresh
`BudgetedInventory._discover` calls and reference `_expand` calls. It verifies
all eight workers, identical operation histories and logical tables between
modes, repeated results, pending/admission accounting, both branch obligations,
model lifts, all 3,259 reference nodes, global coverage and exact next selection.
All **209 regression tests** pass, including five new tests for clear-prefix
catalog/candidate agreement, forcing and later activation, changed sidecars and
unrelated writes, forged payloads, and external-writer invalidation.

The next source has **eleven saved pairs**, all with unacquired child roots.
Its ordinary probe pool is exhausted; the best rank is **[2, 2, 36, 906, 30]**.
Start by testing this exact saved pair, then inspect its unresolved descendants
for cross-family reductions or reuse. An early-versus-late comparison at an
already exhausted source cannot measure avoided ordinary probing. Compare
scheduling only where a descendant still offers a real choice.

The manuscript builds to **158 pages** with all **64 proof blocks** unchanged,
no overfull boxes and no undefined references. All **660 earlier artifacts /
18 manifests** remain hash-identical. The new study preserves **124 manifested
artifacts** plus its manifest, including producer, cold-replay, test and build
logs, exact deltas, reference results and source fingerprints.
