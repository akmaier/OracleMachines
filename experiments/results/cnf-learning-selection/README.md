# Bounded learned-batch selection: a gain, a loss and an informative limit

9 November 2026. Selecting four proved clauses from a wider candidate pool
closes one previous source but loses closure of another. Coverage is unchanged,
while total time and storage rise. Keep this policy experimental; the preceding
compact closure policy remains available unchanged. All regressions and local
counterfactual traces are preserved.

## Selection and exact recomposition

After earlier recognition/reductions and original probing are inconclusive,
enumerate at most sixteen candidate binary clauses using the existing saved
unit implications and binary-path filter. If the pool fits the retained cap,
keep it unchanged. Otherwise greedily rank each remaining candidate by:

1. Number of previously uncovered original probe closures it activates.
2. Whether its origin assumption has not yet contributed a clause.
3. Total number of activated closures.
4. Earlier pool position.

An added clause activates a saved closure if it is unsatisfied and has fewer
than two unassigned literals under that closure and assumption. Retain at most
four clauses and use the same four-variable continuation cap. Activation does
not predict the resulting closure, first conflict or later structural discovery.
The retained clauses can change the binary-incidence variable ranking as well.

Every selected clause has a checked implication proof against the original CNF.
The checker verifies all original reasons before reconstructing the pool, scores,
chosen order and full continuation. Shared closures are accepted only after their
delta check. The existing strict support decrease, exact child and model-lift
checks remain. Unsuccessful attempts are stored without learning-only recursion.
Generator labels do not select routes, and earlier overlapping family recognition
remains available. This changes an optional discovery policy, not the decision solver.

A subset of a pool entailed by F is also entailed by F; hence appending the subset
preserves every source model. The existing exact reduction then preserves model
fibers and lifting. Lean's `selected_signed_batch_models` formalizes this
corollary without any ranking assumption. It proves neither useful selection nor
Python/SQLite correctness. Pool filtering may use edges of candidates eventually
omitted; this is sound but can exclude useful alternatives. The sixteen-candidate
cap also makes selection incomplete.

Local learning and look-ahead preselection are established techniques; Section 7
of Heule et al. (2005), *March_eq*, discusses selection cost and workload-dependent
benefits/losses ([author PDF](https://www.cs.cmu.edu/~mheule/publications/35420345.pdf)).
This study evaluates a specific bounded policy and its persistent accounting;
it makes no novelty claim for those principles.

## Full matched comparison

All 1,209 previous sources are retained, with 24 fresh random 3-CNFs (eight each
at 20/32/48 variables) and twelve growing, signed and edited controls. The 512
exhaustive tiny inputs are separate from 733 other inputs. Both policies use
arbitrary depth two, four conditioning candidates, four probe variables per
pass and at most four retained learned clauses. The wider pool has additional
recognition/checking cost, and per-node caps do not equalize total acquired work.

| Mode | Closed / 733 | Fresh / 24 | Total seconds | SQLite bytes | Cold seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solving | -- | -- | 17.56004 | 70,582,272 | 3.97771 |
| First four clauses | 662 | 16 | 71.41739 | 227,385,344 | 29.81471 |
| Activation/diversity selection | 662 | 16 | 73.19404 | 227,831,808 | 30.35939 |

The gain is **1024**, a satisfiable guarded input (`probe_invalidation:guard_32`).
The loss is **956**, a satisfiable 20-variable random input, previously gained by
bounded learning. Its structural miss does not make the SAT answer incorrect:
the independent solver decides every original input and retains **12,516**
residuals in each mode. All fresh-source closure counts and twelve new controls
are unchanged. Seventy-one sources remain structurally unresolved.

The [13-source pilot](../cnf-learning-selection-pilot/README.md) gains 1024 and
shows slightly higher time/storage; it did not contain the lost source 956.
This is why the full corpus and fresh inputs are necessary after opportunity
selection. Both favorable and unfavorable cases remain in the archives.

Total time rises **2.49%**, discovery **2.26%** (53.49192 -> 54.70319 s), SQLite
**0.20%**, and cold replay **1.83%**. Warm replay is 0.18843 -> 0.19257 s. The
same six-case Python peak is 20,021,677 -> 20,121,481 bytes, excluding native
SQLite, RSS and full-corpus peak. Nodes increase 14,592 -> 14,653; logical node
bytes 89,963,443 -> 90,219,745. Source bytes fall 4,462,996 -> 4,455,574, partly
reflecting the shorter distinct policy tag. Total logical probes rise 82,036 ->
82,782 even though conditioning candidates fall 2,850 -> 2,835. Selected
unresolved literals fall 17,687 -> 17,327, with 103 distinct selected leaves in
each mode. Smaller remaining interaction alone does not imply more closure or
lower acquisition cost.

Selection accounts for 64,480 assignment entries, 203,218 delta literal visits,
47,472 score evaluations and 23,028 pooled clauses across discovery and checking.
Successful learned continuations increase 313 -> 345, but this includes changed
parents and unselected alternatives; it is not 32 gained source closures.
The largest remaining discovery case is **1194**: 1.39726 -> 1.46397 s in the
main runs, and 4.55852 s under the separate new-policy profiler. Restriction,
unit checking/propagation and literal helpers remain dominant.

These are single sequential synthetic samples. Primary modes, memory diagnostics
and separate profiling ran without concurrent tests, Lean builds or commits.
Operation times include discovery, checking, serialization, persistence,
original-source solving and successful root lifting. Generation, small truth
tables, summary walks, initialization, compression and diagnostics are separate.

## Fixed-choice controls and the next gap

`mechanisms.json` stores four independently checked local controls on every
changed selection parent: old batch/old choices, old batch/new choices,
new batch/old choices and new batch/new choices. Among 606 changed nodes,
480 change the clause set and 126 only reorder it. Of these, 562 also occur in
the baseline archive with identical original probe proofs. The local controls
show 54 clear-to-reduction changes and eighteen reduction-to-clear changes;
94 remain reductions and 440 remain clear. They do not establish counterfactual
whole-source closure.

`selection-paths.json` keeps explicit normalized parents for the two changed
source paths, their clauses, assumptions, first conflicts and dependency hashes:

- At **1024**, a 28-variable parent has the same continuation choices
  `[26,3,5,9]` under both batches. Both activate only the saved `3=false` closure,
  yet the old batch remains clear and the new one refutes `3=false`. Thus changed
  clauses provide stronger propagation under fixed choices, although the scalar
  activation count is identical. Origin diversity changes from one to three.
- At **956**, an 18-variable parent has zero activated original closures under
  either batch. Diversity changes two -> four, and continuation choices change
  `[17,9,14,16]` -> `[9,18,16,17]`. All four controls report a forced reduction.
  Old choices first refute `14=true`; new choices first refute `16=false`, under
  either batch. The actual new source plan later remains unresolved. The coarse
  label `forced` misses this consequential difference in subsequent acquisition.

Replaying the prior 94 selected unresolved leaves gives 34 without a batch,
58 inconclusive learned passes, one forced reduction (1024) and one common
reduction on source 1189's selected path. The latter does not close that source.
All traces and failed candidates remain. The current selected remainder has
66 learning-clear and 37 clear leaves across the enlarged corpus.

**Next experiment:** freeze the continuation variable list/order to that obtained
from the old first-four batch while testing the selected batch. Keep the four
clause/probe caps and charge reconstruction of that baseline ranking. This can
separate stronger learned propagation from disruptive candidate/stop-order
changes. Test 956/1024 and the locally improved but still unresolved 1189, then
all prior and fresh sources. No whole-source benefit from this policy has yet
been measured, and fixed choices do not guarantee preservation of old coverage.
Trace interacting learned clauses on the activated closure as a further feature:
activation counts and origin diversity alone cannot distinguish the outcomes.

## Bounds, checks and reproduction

For at most 2k saved closures, d variables, p <= 16 candidates and q retained
clauses, saved assignment maps cost expected O(kd) time/space; candidate deltas
cost O(pk); greedy choice uses at most pq score evaluations. Implemented k <= 64
bounds mask-word cost; an unbounded-k analysis must charge mask length. Existing
pool filtering can still cost expected O(ell+kd(d+m2+p)), in addition to the
selection, propagation, repeated checks and descendant graph. No bound here
makes discovery complete or uniformly efficient for unrestricted SAT.

All **353 Python tests** pass (32.08 s), including all 512 two-variable inputs and
3,304 three-variable inputs with at most three clauses, at learning caps 0/1/4.
Tests check exact model fibers, full expanded-reference replay, deterministic
selection, masks against the independent delta predicate, signed mixtures/edits,
forged/omitted/wrong-order batches, corrupted reasons, disabled mode, old-policy
coexistence and cold corruption. Three new full, three pilot and four preceding
archives replay byte-identically. Warm reuse inserts nothing. Both reports' forty
source/test fingerprints match the measured code.

The full Lean build and axiom audit pass at **4,122 declarations / 1,965 theorem
declarations**. The subset corollary keeps original-source entailment explicit;
semantic preservation is separate from selection quality and resource guarantees.
The earlier proofs and experiments are unchanged.

```sh
python3 experiments/compare_cnf_learning_selection.py --pilot --output /tmp/new-selection-pilot
python3 experiments/compare_cnf_learning_selection.py --output /tmp/new-selection-full
python3 experiments/analyze_cnf_learning_selection.py /tmp/new-selection-full
python3 experiments/analyze_cnf_selection_paths.py /tmp/new-selection-full
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
