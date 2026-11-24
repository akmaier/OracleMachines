# Conditional supports from unfinished searches

The previous whole-plan route required a completed negative origin. Seven of
the 24 exposed base/edit pairs instead stopped on both queries. This experiment
asks whether checked negative regions of those unfinished searches can still
supply reusable, source-bound descriptions. It establishes that they can, but
the first bounded-tree policy does not make either tested edit cheaper or
complete it within the budget.

## Capture and authority

`experiments/cnf_stopped_observer.py` adds optional passive observation to the
preceding lazy binary solver. It records negative residual keys, source-variable
maps, fixed assignments and branch guards. Unit consequences are distinguished
from branching assumptions. Unsupported transitions and exhausted observation
limits are misses. Observation supplies no proof authority and is intended for
exclusive synchronous use, like the existing composer.

The original 72-query stream is replayed unchanged. Every native search counter
and verdict agrees with its preceding run; all six final authority tables have
identical payloads. No support produced by the census is fed back into this
search. Origins are captured before their edit, including source 60 before its
later repeat obtains a result. No future answer supplies a missing endpoint.

The first developmental replay exposed a persistence limit: ordinary search
aborts its final uncommitted publication batch on a budget stop. Some negatives
observed during search therefore have no retained certificate. They are marked
`unretained` and excluded. The original transaction policy remains unchanged.
The failure, its explanation and the corrected replay are preserved.

`experiments/cnf_stopped_support.py` independently reads each retained negative,
checks that its mapped clauses belong to the source restricted by the recorded
assignment, then runs unit propagation on the full source under the branch
guards. Only an independently checked conflict supplies a template. Backward
reason slicing retains the original source clauses and necessary assumptions.
A negative endpoint whose guard does not give a unit refutation remains a miss.
This restriction includes endpoints with richer proofs; the observer does not
turn a stored implication or split proof into a unit certificate by assertion.

A template says that its source clauses cannot hold under its assumptions.
Reuse requires those clauses to remain in the target and the current context
to imply the assumptions. Deleting a required clause invalidates that leaf.
This study checks identical canonical variable coordinates for each pair;
arbitrary renaming transport and automatic origin discovery are not implemented.

## Census and bounded composition

All eight selected origins reach the 256-candidate cap. Seven are unfinished;
27 is the completed-origin control. The extraction gives:

| Origin/edit | Origin status | Distinct conditional templates | Templates used in the bounded plan |
|---|---|---:|---:|
| 0/1 | unfinished | 58 | 16 |
| 3/4 | unfinished | 45 | 5 |
| 27/28 | UNSAT | 53 | 9 |
| 36/37 | unfinished | 48 | 5 |
| 39/40 | unfinished | 46 | 5 |
| 60/61 | unfinished | 50 | 18 |
| 63/64 | unfinished | 44 | 7 |
| 66/67 | unfinished | 51 | 7 |

All 395 templates survive their respective one-clause replacement; 342 come
from the seven unfinished origins. Three captured endpoints of source 60 are
unretained. The cap rejects another 138 candidate events across the eight
origins, so this is a bounded census, not an enumeration of every useful region.

The deterministic builder selects the first compatible template, splits on
its smallest unassigned guard variable, and stops after at most 129 tree nodes.
Every assignment reaches either a checked conditional leaf or an explicit
open leaf. Native acquisition handles the open regions under one shared
256-dispatch budget. A stopped composition supplies no root verdict.

These plans use only 5--18 distinct templates each and all retain an open leaf.
Their closed regions cover 0.0254%--6.8146% of uniformly weighted assignments
to the source variables. This is the exact mass of the selected tree regions,
not coverage of SAT instances, an estimate of search cost, or a measure of the
union of all extracted templates. Source 63's plan covers about 1.0178%.

Every surviving template is also materialized as a native refutation of its
conditioned target in a separate archive, with fresh search disabled. These
conditional results remain persistent, but are not seeded into the diagnostic
workers or counted as complete edited roots.

## Costs and controls

The eight observed source attempts take 10.1341 seconds in total. This includes
the original search and capture; it is not an isolated measurement of observer
overhead. Independent extraction takes another 7.5308 seconds, tree construction
0.0361 seconds, separate conditional materialization 1.2669 seconds, and JSON
serialization 0.0723 seconds. Causal-prefix compression is also recorded. The
entire census takes 80.5263 seconds, including the other queries, snapshot
storage, comparison with the old archive and final reconstruction/compression.
These acquisition and storage costs are additional to later reuse timings.

The capture limits are 256 candidates, 4 MiB of candidate key bytes, 4,096
pending bindings and one million pending literal/context slots. Keys are full
serialized CNFs. Context lists, active frames, source size and construction
transients need their own account. The measured candidate/list-and-dedup graphs
are 2.25--5.15 MB and the pending graphs before cleanup are 3.62--10.31 MB.
They are separate selected object graphs, not process-memory bounds; they may
share objects. Pending bindings and the dedup set are cleared after capture.

For a source with literal volume L and n variables, each candidate may require
source restriction and a fresh unit pass. The current repeated-scan propagation
can take O(nL) word work per candidate. With C candidates, that alone can be
O(CnL), before endpoint proof replay, maps, sorting, serialization and checking.
Constructing a K-node tree scans candidate guards and can cost O(KCn) word work,
besides copied certificate storage. Fixed bookkeeping caps do not bound source
size, certificate dependencies or later open-region acquisition. No polynomial
bound for unrestricted SAT follows.

`experiments/compare_cnf_stopped_plans.py` freezes a separate comparison protocol
after the census. Four alternating serial repetitions compare two exposed
targets, 28 and 64. Each starts cold from the same causal source-prefix database.
The ordinary solver is a route baseline. The stronger controlled comparison
uses the same tree and composer in both arms, erasing all certificates in the
`open` arm and retaining them in `plan`. Thus tree selection and finish-on-stop
publication are shared. The ordinary solver has a different solve-session
handoff and abort-on-stop policy, so differences against it are not attributable
solely to conditional support reuse. No worker runs concurrently with tests or
profiling. Loading, cold checking, persistence and compression remain recorded.

All three routes stop on both targets. The support arm consumes 31 checked
leaves on target 28 and 15 on target 64, yet still acquires the full allowance
of 256 native dispatches. More local reuse has not closed the expensive open
regions. The machine-readable comparison records all four repetitions,
including the runtime and storage regressions.

| Target | Ordinary solve, s | Same tree, open leaves, s | Same tree with supports, s | Support/open worker change | Support/open database change |
|---|---:|---:|---:|---:|---:|
| 28 | 0.58767 | 0.95884 | 1.01934 | +1.63% | +1.06% |
| 64 | 0.66011 | 0.95982 | 1.01377 | +1.22% | +0.20% |

Supports increase solve mean 6.31% and 5.62% over the identical open tree.
Complete-worker means rise from 7.49814 to 7.62072 seconds and from 17.31944
to 17.53045 seconds. They include restore, setup, solving, complete cold native
replay, output serialization and archive compression; imports, source hashing
and initial case loading remain outside the timer. Each support/open solve
pair regresses. Native additions rise from 406 to 445 and from 417 to 440.
The final databases are 59,670,528 and 143,507,456 bytes, including the restored
prefix. These figures do not charge the already listed source acquisition a
second time: even before that cost is added, no saving is demonstrated.

## Decision and next gap

Keep this as an experimental discovery facility; do not enable it in the
ordinary solver. The new result is reusable conditional authority from an
unfinished origin, with explicit remaining regions. It is not broader whole-CNF
coverage or cheaper expansion on the measured targets.

The next target is the representation and use of the conditional exclusions.
The first-compatible tree spends its small node allowance on narrow guard
regions, duplicates leaf uses and imposes an expensive branching order. First
measure guard subsumption, shared prefixes and overlap among the retained
templates. Compare a bounded shared representation or checked guard-derived
clauses with this exact tree, charging recognition, implication checking and
the remaining open-region acquisition. A certificate with assumptions A can
justify excluding A only while its source support remains present. Any new
propagation or recomposition rule must preserve that condition.

Extraction is the second cost target: source mapping and unit propagation are
repeated per candidate. Shared conditional prefixes could avoid repeated work,
but must preserve clause origins and independent checking. Recovering aborted
tail nodes is a smaller separate gap here (three events), not a reason to
change transaction semantics during this experiment. New policies need fresh
unlabelled inputs and adversarial edits after the exposed diagnostics.

Artifacts and the resumable checkpoint are under
`experiments/results/cnf-stopped-origins/`. The cumulative history uses
`experiments.cnf_archive_parts.restore_archive`. Previous authoritative payloads
are unchanged; raw trial archives retain alternative valid proofs. The audit
checks every new cumulative node and its dependency closure with both native
readers, and verifies old payload identity. Earlier full-history and partition
audits remain bound by unchanged manifests rather than being rerun.

The cumulative union adds 1,281 native records and retains all earlier payloads,
bringing the native table to 157,111 records. Its database grows by 26,423,296
bytes to 2,048,270,336 bytes; compressed history grows by 2,190,187 bytes to
148,684,495 bytes. This combines conditional materialization and alternative
diagnostic acquisitions. It is research-history growth, not the memory cost of
one 256-dispatch run. All five other authority tables are unchanged.

The checks pass 1,708 full-suite tests and 64 focused tests. The full suite
retains the preceding 44 SQLite resource warnings; the focused run has none.
The 256-page manuscript builds without warnings, with all 64 earlier proof
environments unchanged. No Lean definitions or proofs changed in this step.

To reproduce into a new directory, run the following from the repository root
(the saved output directory must not be overwritten):

```sh
python3 experiments/study_cnf_stopped_origins.py prepare NEW_DIRECTORY
python3 experiments/study_cnf_stopped_origins.py census NEW_DIRECTORY
python3 experiments/compare_cnf_stopped_plans.py prepare NEW_DIRECTORY
python3 experiments/compare_cnf_stopped_plans.py run NEW_DIRECTORY
python3 experiments/validate_cnf_stopped_origins.py NEW_DIRECTORY
```

The original two-arm diagnostic entry point in the census script was superseded
before any timed trial by the frozen three-arm comparison, which adds the
same-tree open control. The census source and its original protocol remain
unchanged and hash-bound.
