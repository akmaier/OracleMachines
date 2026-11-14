# First-split cost: less new storage, unchanged expansion time

2026-11-14. The preselected comparison on case **1299 / index 48** shows that a
smaller acquired representation need not produce a faster expansion. Splitting
its **36-variable / 162-clause / 517-literal** residual on local variable **1**
stores **13** new patterns, compared with **29** for variable **17**. The respective
compressed deltas are **15,849** and **28,842 bytes**. Yet both twelve-step arms
take about **12.7 seconds** for expansion and leave the source structurally open.
Complete route refresh takes about **94%** of that time.

This is a measured storage difference for two incomplete expansion paths. It
does not establish the better split for completing the case, and it does not
justify replacing the current ranking globally. The saved alternatives provide
two smaller unresolved leaves and two newly recognized SAT terminals to study.

## Matched comparison

The parent is `experiments/results/cnf-transfer-1304/report.json`, SHA-256
`4ccd7e0ddec8c99acce4a6ad400b6098bf9a7eb3d71a37350670037543831ab4`.
The selected source SHA-256 is
`6b9b95c54e6bc4dcab8c537abb5c636401c87ad995a9ae5957fa2c821c19f1b0`.
Its final ordinary candidates, **33, 34 and 36**, are clear in both polarities.
That common six-attempt block is persisted once; it admits no patterns.

Each arm starts from an independent copy of exactly that post-probe seed, with
one shared **32-state allowance**, **12 advances**, and at most **64 saved
candidate pairs** per ranking. The first split is preselected. Every subsequent
advance uses the same existing early-closed policy, and both cofactor obligations
remain required. Orders are **17 then 1**, followed by **1 then 17**, with no
competing test or build process during measurement. The union accumulated for
resumption is never fed back into an arm. Repetitions produce identical logical
tables, admitted identities, split evidence, closure flags and next selections.

Two serial repetitions on this adaptively selected development residual provide
no confidence interval or fresh-holdout result. They share OS caches. The cap is
a bound on entered states, not time or RAM; both arms stop at the step limit,
before using all 32 admissions.

## Structural result

Under first variable **1**, the false cofactor reaches a **5-variable / 5-clause /
10-literal Horn, 2-CNF and zero-valid** terminal through one stored probe node.
The clear-trace target has 16 variables, 48 clauses and 115 literal occurrences;
canonical duplicate removal gives the stored 16 / 46 / 111 node. The size rank
charges the target before that canonical normalization. The true cofactor
remains open after a binary-path reduction. Its next split, on local variable
**9** of the 35-variable residual, refutes the false branch through two probe
nodes and the previously stored empty-clause terminal. The true branch reduces
to **29 / 108 / 337** and remains structurally unresolved.

Under first variable **17**, the true cofactor reaches a **20 / 78 / 237**
unresolved node through probes, binary paths and eliminations. The next ordinary
block refutes local variable 17=false, forcing a **19 / 75 / 219** target.
One more probe node reaches a **5 / 7 / 16 Horn and zero-valid** terminal that
is **not 2-CNF**. The false first cofactor has a different open residual,
**31 / 149 / 501**. Splitting that source on its local variable **9** again
refutes one branch through two probes and the same empty-clause terminal. The
other becomes **28 / 110 / 351**, still unresolved.

This is evidence of a recurring conditional-refutation pattern under two
different first choices. The two local variable-9 identities belong to distinct
canonical sources; equal numbers do not establish a shared original variable.
Exact empty-clause reuse is already certified. Stronger reuse between the open
leaves requires a separate transport or implication proof. Both first splits
eventually have a structurally closed SAT child, but neither has both children
closed. The independent reference solver reports UNSAT for the remaining branch
of each first split. That answer does not supply a structural-family certificate
and is not used in ranking or the closure count.

## Cost account

Times below are means of the two repetitions, in seconds. Arm delta sizes exclude
the common probe block and the other arm. Worker time includes local preparation,
delta export and checks, but excludes the shared parent reconstruction and final
whole-corpus work.

| Quantity | First variable 17 | First variable 1 |
|---|---:|---:|
| Initial cofactor supports | 34, 32 | 16, 35 |
| Initial combined literal occurrences | 927 | 617 |
| New admitted and completed patterns | 29 | 13 |
| Entered but unstored states | 0 | 0 |
| First split, ranking and acquisition | 0.23590 | 0.09080 |
| All selection | 0.02883 | 0.02602 |
| All acquisition and candidate checking | 0.73169 | 0.71052 |
| All route refresh | 11.96241 | 11.98228 |
| Local closure composition and proof checks | 0.00414 | 0.00298 |
| Expansion total | 12.72706 | 12.72181 |
| Local preparation | 7.37810 | 7.71372 |
| Complete worker | 24.82740 | 25.58026 |
| Fresh external assumption attempts | 61 | 70 |
| Compressed arm delta, bytes | 28,842 | 15,849 |
| Uncompressed arm delta, bytes | 626,688 | 372,736 |
| Full arm history, bytes | 772,288,512 | 772,030,464 |
| Next selected open leaf: variables / clauses / literals | 28 / 110 / 351 | 29 / 108 / 337 |

Variable 1 uses **55.17% fewer new pattern rows** and **45.05% fewer compressed
delta bytes** within these fixed twelve advances. This is not a 45% reduction in
full history or peak RAM. Its first acquisition is smaller, but later work and
maintenance erase that time difference: mean expansion differs by just **0.04%**,
and the direction reverses between repetitions. Its complete worker is **3.03%
slower** on the observed means. Retain this regression; the two paths have not
reached equivalent completed decompositions.

The whole producer costs **252.67688 s** for common preparation, all four arms,
merges, final checking, reference solving and persistence. Parent restoration
costs **45.38279 s**; final global route preparation costs **7.52674 s** and
whole-corpus closure checking **59.90156 s**. These costs are outside the warm
arm expansion totals. They must be amortized or reduced before small discovery
savings can matter to an end-to-end workload.
The shared ordinary block itself takes **0.00799 s** to acquire; its complete
preflight, including local preparation and delta persistence, takes **12.75192 s**.

## Preserved result and resume contract

Structural coverage remains **61/83**, also without growth-exception routes.
The union adds **42 distinct patterns**, **16 continuations** and **5 probe
windows**, with **4** separate split records. Pattern kinds are fourteen probe
reductions, twelve eliminations, nine binary-path reductions, five unresolved
nodes and two family terminals. Repeated arms add no duplicate logical rows.
The combined 42 patterns are **not** one 32-admission run.

The combined delta is **43,317 compressed bytes**, or **942,080 SQLite bytes**.
Full history grows **884,736 bytes** to **772,599,808 bytes / 41,887 patterns**.
This includes unsuccessful alternatives. The positive certificate remains
**3,043 steps**; all **2,259** earlier reference nodes remain among **2,605**.
Reference answers are a separate check and do not close structural obligations.
All arm deltas, ordinary traces, operations and reports are retained, in addition
to the combined checkpoint. Disk bytes do not measure peak RAM.
The complete new result directory occupies **4,865,384 logical file bytes**,
including its 95 manifested artifacts and the manifest itself. This includes
reference/positive certificates, repetitions and validation logs excluded from
the 43,317-byte combined proof-table delta.

Resume **`experiments/results/cnf-split-cost-1299/report.json`**, SHA-256
`76e56eb9db1dd60c2d171c3fa0b349b68f1628c25878e61ddc90c6a2667cd1fd`, through
**`experiments.compare_cnf_split_cost.restore_checkpoint`**. The five evidence
counts are **(1, 42, 156, 21, 1)**. Do not rerun the comparison to continue.
The next selected leaf is **28 / 110 / 351**, SHA-256
`dd04e43d15b115ab5d60b5b4aef44d03001fcfe6910263b218b5f35776ed70ab`.
The alternative retained leaf is **29 / 108 / 337**, SHA-256
`a42f143621e8ee85bca58cbe4157f510af9fd7b56f0bb5b2a67a098a8f5efdcf`.
Neither is pending acquisition; both have exhausted their ordinary candidate
pools and retain 21 clear split pairs. No candidate currently has a present child
root. The next size-ranked variables are respectively **17** and **18**.

## Next investigations

1. **Continue the smaller unresolved leaf while testing reuse across the two
   alternatives.** Their literal counts are close, but their exact keys differ.
   Check signed variable transports, implication or common restricted components
   before sharing proofs. Similar sizes or SAT/UNSAT labels cannot certify
   equivalence. Acquiring every alternative would also retain needless state;
   a useful scheduler needs measured progress toward completion per total cost.
2. **Stop complete route reconstruction after every clear block.** It dominates
   this warm comparison. Clear probe records still change future candidate
   availability, so record and invalidate that information explicitly. Test an
   incremental or deferred refresh against the complete catalog, including a
   forcing block, a newly acquired child and an inactive route becoming active.
   Preserving old closure flags alone does not validate a complete negative query.
3. **Separate decision witnesses from complete structural coverage.** A closed
   SAT cofactor can decide its source, while classifying both branches requires
   more work. Maintain these two metrics and their proof contracts explicitly.
   Do not treat reference-solver answers or one closed child as completed
   structural decomposition.

The runners and independent validator are additive files. Earlier producers,
proofs, artifacts and their fingerprints remain unchanged. The saved comparison
narrows the scheduling question; it supplies no polynomial expansion bound or
efficient partition of arbitrary SAT.

## Validation

All **181 relevant regression tests** pass. Independent replay reconstructs the
shared seed, every isolated arm and the union with new recognition forbidden;
checks the exact preselected ranks, source/trace bindings, both branches,
admission counts, completed rows, idempotent merges and repeated logical results;
and recomputes all 83 original closure flags and the exact next selection. All
**2,605 reference nodes** and the SAT model lifts are checked with fresh reference
expansion forbidden. This deliberately redundant audit takes **214.31500 s**,
including **68.64635 s** for final global routes, coverage and selection. The
manuscript build and artifact-preservation results are bound in `validation.json`,
`paper-check.json` and `manifest.json` in the result directory.
