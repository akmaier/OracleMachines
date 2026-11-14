# Closing a retained split through two conditional Horn reductions

The exact pending pair now closes original **1154 / index 27**, raising
structural coverage **65/83 -> 66/83**, including the view that excludes growth
exceptions. All earlier results remain available. The retained split frontier
has no pending targets or open leaves; **17 original formulas remain uncovered**.
An independent SAT answer is not substituted for either branch's structural
obligation.

## What was acquired and reused

The preserved source has **33 variables / 130 clauses / 400 literal
occurrences**, with a saved split on local variable **18**. Its false cofactor
already has a checked refutation through the stored contradiction terminal.
Resumption charges **zero new admissions** to that branch. Its true cofactor,
**30/111/330**, requires **16 admissions**: six probe reductions, four binary
path reductions and five elimination steps reach a new **19/66/214** unresolved
node. The thirteen ancestor keys entered but unstored in the previous run are
charged again. Recognition work was not retained for those interrupted keys.

The next advance selects local variable **3** of the 19-variable residual from
its already saved pairs. The rank is **[2, 2, 17, 268, 3]**: two unclosed
children, two absent roots, maximum child support seventeen and 268 total
cofactor literal occurrences. This heuristic does not minimize total cost.

| Branch | Raw cofactor | New states | Checked reduction path | Terminal |
|---|---|---:|---|---|
| False | 17/57/179 | 8 | Two probes, one binary-path reduction, three eliminations, polarity change, family | 7/7/16, Horn and zero-valid |
| True | 13/31/89 | 6 | Three probes, one binary-path reduction, polarity change, family | 9/15/37, Horn and zero-valid |

Neither terminal is 2-CNF. Horn and zero-valid recognition overlap; they are
not disjoint categories. The two terminal keys differ and both are new, so
this is a recurring **type of reduction chain**, not reuse of the same formula
or a shared terminal proof. The existing false branch of the variable-18 split
is exact reuse. Every intermediate reduction and local variable transport is
checked. The family reached after these transformations does not by itself
establish a strong Horn backdoor in the original variable coordinates.

The two advances use **30 of 32 available admissions**, all stored. They add
eleven probe nodes, six binary-path nodes, eight elimination nodes, two
polarity nodes, two family nodes and one initially unresolved node subsequently
closed by the new split. There is **one new split sidecar** and no new external
probe window or continuation. Internal probe certificates remain in the new
pattern nodes; no external probe row does not mean no propagation work.

## Costs and persistence

Two independent seed copies execute the same scheduler and reproduce identical
operations and logical results. These repetitions test reproducibility; they
do not compare against a different policy or establish a new speedup.

| Mean worker phase | Seconds |
|---|---:|
| Preparation | 8.01578 |
| Selection | 0.08558 |
| Acquisition | 0.12262 |
| Complete route updates | 2.17729 |
| Coverage after advances | 0.00201 |
| Total expansion | 2.38750 |
| Delta export | 4.76630 |
| Complete worker | 15.23836 |

Both advances write patterns, so both correctly rebuild routes. The inactive
pending-split guard cannot avoid either update. Route updates consume **91.2%**
of expansion time. The first advance acquires the missing root and can activate
an old split; the second adds a new split whose children are already available.
These are two concrete activation transitions that an incremental replacement
must reproduce. It must also maintain every other route kind, including the
two projection bridges, without treating an acquired but unresolved node as a
completed structural proof.

The immutable union adds **30 patterns**, not sixty: the two repetitions produce
the same rows. The SQLite delta is **446,464 bytes**, compressed to **17,007
bytes**. Full history grows **372,736 bytes** to **775,376,896 bytes / 42,069
patterns**. The expanded positive certificate grows **3,239 -> 3,360 steps**.
The reference archive preserves all **3,467** previous nodes and contains
**3,575** nodes. These are storage figures, not peak RAM measurements.

The complete producer takes **196.65984 s**, including **76.28286 s** of parent
restoration, **7.88543 s** of final route preparation, **60.27510 s** of global
coverage and **5.44556 s** of union delta export. These costs remain separate
from the bounded warm expansion. Development inputs and shared OS caches do
not supply a holdout estimate or a complexity bound for arbitrary SAT.

## Reproduction and next obligation

Producer:
`python3 experiments/continue_cnf_pending_pair.py experiments/results/cnf-pending-pair`
(use a new output directory to repeat it). Independent replay:
`python3 experiments/validate_cnf_pending_pair.py experiments/results/cnf-pending-pair`.
Replay forbids fresh structural recognition and reference search, checks both
repeat prefixes using only then-available rows, and compares the complete
maintained and freshly reconstructed catalogs, coverage and next selections.
Cold replay passes in **289.93906 s**, verifying all **3,575 reference nodes**.
All **215 regression tests** pass. The paper builds to **159 pages**, preserving
all **64 proof blocks**. All **969 earlier manifested artifacts** and **3,467
prior reference payloads** remain unchanged. The new manifest binds **40
artifacts**; validation results and hashes are recorded beside the report.

Resume `experiments/results/cnf-pending-pair/report.json` through
`continue_cnf_pending_pair.restore_checkpoint`. Keep the five evidence lists
**(1, 42, 156, 41, 1)** and **two bridges**, with bridge-aware `routes_for` and
`cnf_projection_bridge.verify_positive`. The saved `source` field is the now
closed 38-variable ancestor; **select new work from `next_selection`**, not that
old focus. The next selected original is **1062 / index 14**, with a
**39/161/495** residual and no pending retained split.

Its sixteen saved split candidates all have absent cofactor roots. The current
rank prefers variable **25**, giving **37/150/450** and **37/147/446** children.
Variable **17** instead gives **38/152/464** and **32/111/301** children: a larger
maximum support but **765 rather than 896 total literals**. Four ordinary
candidates, **28, 29, 30 and 33**, remain. A matched comparison should determine
whether either saved choice exposes a useful family with less total work;
these shape statistics do not establish that conclusion.

The structural opportunity is to identify where conditioning exposes the same
sequence of checked transformations toward a tractable family on this next
unlabelled input. Similar shapes alone cannot transport proofs. The measured
runtime opportunity is maintenance of only routes affected by real acquisition;
the complete catalog currently costs far more than acquiring these reductions.
Neither opportunity supplies compact closure or uniformly polynomial discovery
for all CNFs.
