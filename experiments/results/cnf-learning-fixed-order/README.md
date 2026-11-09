# Fixed continuation choices expose representation-sensitive discovery

9 November 2026. Holding the old continuation choices while propagating selected
clauses does not recover the earlier lost closure. On 1,281 matched inputs,
coverage is unchanged from selection, with higher cost than the first-four
baseline. The experiment remains optional. The informative counterexample has
the **same forced assignment and same restricted original CNF**, but different
retained redundant clauses and different subsequent structural closure.

## Policy, soundness and accounting

After the original probe phase is inconclusive, select at most four of sixteen
proved implications as before. Separately reconstruct the old first-four batch
and rank its augmented source by binary incidence. Propagate the selected batch
using that old variable list/order. Every checker reconstructs both the batch and
ranking after validating all original proofs. Stored hints do not choose the
policy. Earlier recognition, decomposition and reduction priorities, original
four-variable probing, and arbitrary conditioning depth two/cap four are unchanged.

The existing implication/subset lemmas preserve source models under either batch.
The checked forced/common/equivalence rewrite and lift preserve exact composition
under the chosen order. Original saved closures are reused only after the same
inactive-delta check. Children still require strict support decrease; unsuccessful
probes remain recorded. The new version tag keeps preceding policies distinct.
This changes optional discovery, not the independent SAT decision solver.

At each eligible continuation, reconstructing the old bounded batch adds expected
O(ell+kd(d+m2+q)) work, plus O(ell+q+d log d) ranking, with source literal count ell,
variables d, binary clauses m2, probe cap k and retained cap q. Temporary graph,
maps and augmented clause sequence are charged too. The same work repeats during
checking. It adds no second continuation pass at that parent, but can change later
acquisition. The fixed order is local to an exact parent, not a frozen global tree.

## Full matched comparison

All 1,245 previous inputs remain, with 24 fresh random 3-CNFs (eight each at
20/32/48 variables) and twelve growing, signed and edited controls. The 512 tiny
exhaustive inputs are separate from 769 others. Inputs carry no generator labels
into discovery. A three-source [pilot](../cnf-learning-fixed-order-pilot/README.md)
first tested the previous gain, loss and locally improved miss (1024/956/1189).

| Mode | Closed / 769 | Fresh / 24 | Total seconds | SQLite bytes | Cold seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solver | -- | -- | 19.41276 | 78,266,368 | 4.35795 |
| First four clauses | 692 | 18 | 77.91555 | 252,243,968 | 33.50593 |
| Selected clauses | 692 | 18 | 82.42121 | 252,497,920 | 33.58541 |
| Selected clauses, old choices | 692 | 18 | 80.71966 | 252,391,424 | 34.30859 |

Both selected modes gain source **1024** and lose **956** versus first-four;
there are no changed source closures between selected and fixed-order modes.
Source 1189 stays open. All twelve new controls close in every discovery mode;
**77 sources remain structurally unresolved**. All original decisions agree with
the unchanged solver, which retains **13,641 residuals** in each mode.

Against baseline, fixed order raises total time **3.60%**, discovery **58.15101 ->
60.48437 s**, cold replay **33.50593 -> 34.30859 s**, and the same six-case traced
Python peak **20,021,661 -> 20,127,074 bytes**. Native SQLite, RSS and full-corpus
peak are excluded. Its total time is 2.06% below selection in this single sample;
that does not establish a general runtime advantage. Warm replay costs
0.18731 / 0.19641 / 0.19450 s for baseline/selection/fixed and inserts nothing.

Nodes are **16,052 / 16,106 / 16,126**; logical node bytes are **100,112,588 /
100,290,071 / 100,315,272**. Fixed has slightly fewer physical SQLite bytes than
selection despite more logical node bytes; its shorter policy tag also changes
keys/source records. Keep these separate accounts. Logical probes are **89,782 /
90,513 / 90,713**, conditioning candidates **3,106 / 3,089 / 3,092**, and selected
unresolved literal occurrences **18,362 / 18,002 / 17,971**. Smaller remaining
interaction is not greater source coverage. The fixed remainder has 111 distinct
leaves: 71 learning-clear and forty clear.

Fixed ranking incurs **6,418 reconstructions** and **25,662 candidate positions**
across discovery and checking. Learned candidate visits rise from 152,026 under
selection to 254,742 under fixed order. Learned successes are 342 / 376 / 378;
these are local events, not gained source closures. Source **1194** remains the
largest discovery case at 1.41725 s under fixed order. A separate 4.58346 s profile
again identifies restriction, unit checking/propagation and literal helpers.

These are single sequential synthetic samples. Primary modes, memory diagnostics
and separate profiling ran without concurrent tests, builds or commits. Operation
times include discovery, verification, serialization, persistence, original-source
solving and successful root lifts. Generation, tiny truth tables, summary walks,
initialization, compression and diagnostics remain separate.

## Exact counterexample and next experiment

`mechanisms.json` preserves every remaining selected leaf, all three selected
source paths, and independently checked controls at the two earlier changed
parents, including normalized children and their acquired subtrees.

On the lost source 956's 18-variable parent at depth one:

- Baseline and fixed order both first refute `14=true` and fix only `14=false`.
- Both leave **the identical 54-clause restricted original source**.
- Baseline retains three learned clauses `[1,17]`, `[9,13]`, `[16,17]` and its
  17-variable, 57-clause child closes.
- Fixed order retains four `[-18,16]`, `[9,13]`, `[13,18]`, `[16,17]` and its
  17-variable, 58-clause child remains open with eighteen unresolved literals.

The earlier selected mode instead first refutes `16=false`; its child also stays
open. Thus immediate first-conflict order was only part of the mechanism. At 1024,
both selected modes still refute `3=false`; the resulting 27-variable child closes.

For any explicitly justified batch B with F entailing B, restriction gives
`(F and B)|rho` and `F|rho` identical model relations on the remaining variables.
In the 956 control rho is identical and already forced by F, so different retained
additions are semantically redundant. Syntactic recognition, ranking and persistent
keys nevertheless see different children. This is a concrete representation/reuse
gap, not evidence that general semantic canonicalization is cheap.

**Next experiment:** separate the restricted original core from its checked learned
hints. Use the core for structural identity/recognition and retain optional, scoped
proof hints for propagation. Test 956/1024/1189 and the saved frontier, then full old
and fresh inputs; charge core reconstruction, hint checks, canonicalization and
storage. Compare to both current policies. Discovery plans must retain their hint
and policy context even if semantic cores share an identity; do not reuse a plan
from the wrong context. Deletions, edits and changed assignments require fresh
dependency checks. Dropping useful hints might lose coverage, so no gain is claimed
until measured. This is a restricted, certificate-backed equivalence pattern,
not a complete canonical form or efficient arbitrary-SAT partition.

## Verification and reproduction

All **358 Python tests** pass (30.30 s). New tests cover all 512 two-variable inputs
and 3,304 three-variable subsets of at most three clauses at caps 0/1/4, exact model
fibers and independent expanded-reference checks, changed-order fixtures, signed
mixtures/edits, omitted/forged batches, corrupt reasons, wrong continuation order,
disabled learning, old-policy coexistence and byte-identical cold reuse.
Four full, four pilot and three preceding archives replay byte-identically.
Both reports' **43 fingerprints** match measured code. No original archive is replaced.
Existing Lean semantic lemmas are unchanged; no Python or complexity refinement
is asserted by this heuristic change.

```sh
python3 experiments/compare_cnf_learning_fixed_order.py --pilot --output /tmp/new-fixed-pilot
python3 experiments/compare_cnf_learning_fixed_order.py --output /tmp/new-fixed-full
python3 experiments/analyze_cnf_learning_fixed_order.py /tmp/new-fixed-full
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
