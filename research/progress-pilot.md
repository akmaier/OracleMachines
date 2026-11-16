# Gate the second trial by observed progress

The optional progress gate covers connected case 21 while avoiding unnecessary
exploration. Against the always-pilot policy it uses **25% fewer new patterns
and 42.86% fewer probes**. It matches the committed control's operations, proof
and stored bytes. This extends measured structural coverage **15/24 -> 16/24**;
it neither discovers a universally easy SAT category nor guarantees cheaper
expansion on the remaining inputs.

## Rule and applicable structure

Before any acquisition, record the selected first route's total unresolved
literal count. Complete one nested acquisition on that route. If the count
strictly decreases, retain that route and skip the second trial. Otherwise use
the existing second-trial policy and its remaining-frontier ranking. Coverage
already established by the complete checked graph also stops exploration.

The rule was proposed from cases 11 and 13 and frozen in the
[protocol](../experiments/results/cnf-progress-pilot/protocol.json) before
case-21 acquisition. Focused tests retain the useful second trial for case 11
(1106 -> 1535 literals) and skip it for case 13 (610 -> 539). Those are
development examples, and case 21 is also a known corpus member. This is a
transfer across categories within that corpus, not held-out evaluation.

The gate requires a stored unresolved source below a unary selected root prefix
and at least two saved alternatives. Initial candidate ranking, acquisition,
recognition, checking and continuation are unchanged. The baseline, partial
trial, gate decision and selected route survive cold restart. A partial trial
must complete before the gate fires. All work shares the ordinary **128-admission /
sixteen-operation allowance per batch**, with at most four batches. Earlier
admissions, including losing trials, remain stored. The new baseline and gate
walks inspect selected structure and are charged; scores never certify closure.

Relative to the old pilot, the gate adds one selected-frontier traversal at
initialization and one after the first completed trial. Their cost depends on
the traversed graph and frontier sorting; it is not constant-time recognition.
The new persistent fields are a fixed number of integer scores and one action,
alongside the existing event log and decisions. If exploration proceeds, the
old two-route scoring work remains. If it is skipped, later continuation may
still be more expensive on the chosen route; the gate supplies no worst-case
non-regression bound.

## The two-literal selection error

The original connected mixture has **57 variables / 215 clauses / 635 literals**.
Its selected residual has **45 variables / 201 clauses / 616 literals / width four**.
All eight children of the four saved source splits exist and are uncovered.
The leading routes are pivots **23 and 17**. The first route begins with two
obligations and **1141 literals**. Its first completed trial costs **eight
admissions / 53 probes**, leaving two obligations and **1099 literals**.
The gate therefore skips the second trial and stays on pivot 23.

Always-pilot also tries pivot 17, spending **seven admissions / 52 probes**.
That leaves two obligations and **1097 literals**, so it changes to pivot 17.
The two-literal apparent advantage does not recover the trial cost. Totals are:

| Resource | Committed | Always-pilot | Gated |
| --- | ---: | ---: | ---: |
| Batches to structural coverage | 1 | 1 | 1 |
| New patterns / distinct admissions | 24 | 32 | 24 |
| Probes | 100 | 175 | 100 |
| Fresh source assumptions | 8 | 12 | 8 |
| New split records | 4 | 6 | 4 |
| Completed trial admissions | — | 15 | 8 |
| Completed trial probes | — | 105 | 53 |
| Final source pivot | 23 | 17 | 23 |

The pilot's first eight patterns are unused by its final proof but preserved.
They are exactly the new states shared by its acquisition and the committed
control. The different final proofs share **no newly acquired node**. Identical
gated/committed evidence is a comparison of policies on the same input; it does
not demonstrate broader cross-input reuse.

## Complete costs and timing limits

Two reversed-order fresh-process triples use the same full parent. All imports
are shared across modes; they are excluded from the clock but included in RSS.

| Mean or final resource | Committed | Always-pilot | Gated |
| --- | ---: | ---: | ---: |
| Restoration and setup, seconds | 0.19276 | 0.18421 | 0.18635 |
| Expansion including selection/gate, seconds | 0.17016 | 0.25150 | 0.16285 |
| Bookkeeping, seconds | 0.11144 | 0.11341 | 0.11276 |
| Independent query check, seconds | 0.14994 | 0.16024 | 0.15606 |
| Complete cold audit, seconds | 6.97509 | 7.15993 | 7.12793 |
| Compression, seconds | 0.79584 | 0.79346 | 0.79012 |
| Whole stream, seconds | 8.48923 | 8.75818 | 8.62917 |
| Mean peak process RSS, bytes | 396,263,424 | 398,254,080 | 395,673,600 |
| Final SQLite bytes | 41,553,920 | 41,721,856 | 41,553,920 |
| Compressed snapshot bytes | 2,101,984 | 2,113,955 | 2,101,984 |

Against always-pilot, the gate lowers local expansion time **35.25%**, peak RSS
**0.65%**, SQLite **0.40%** and gzip **0.57%** in these runs. The whole-stream
mean is only **1.47% lower**, with mixed pair rankings: pilot/gated times are
**8.84348/8.42887** and **8.67288/8.82946 seconds**. This is not reliable evidence
of a total-time speedup. Complete auditing uses about **82--83%** of time.

Against committed selection, operations, proofs and SQLite/gzip bytes are
identical. Gated whole time is **1.65% higher**, while its local time and RSS
measure slightly lower; two repetitions cannot isolate the gate's timing
overhead from variation. The result supports avoiding extra acquisition relative
to always-pilot, not dominance over committed selection. Pilot stays in the
middle position of both triples, so the orderings do not fully counterbalance
all three positions.

The clock charges restoration, setup, selection, acquisition, bookkeeping,
persistence and query/full cold checks; only imports and final summary writing
are excluded. Parent acquisition remains charged in earlier experiments.
Preflight costs **0.20920 seconds** separately. Independent retrospective
validation costs **106.11 seconds**, outside operational means and partly
concurrent with tests. These are continuations of a large saved history, not
cold-from-scratch SAT measurements.

## Proofs, preservation and remaining gap

Committed/gated proofs have **42 unique steps / 47 unfolded occurrences**:
five conditional nodes, 36 unary reductions and a contradiction terminal with
six occurrences. The reductions are fifteen probes, five binary-path steps and
sixteen eliminations. Eighteen steps and one split predate continuation; 24 steps
and four splits are new. The pilot proof has **41 unique steps**, six conditional
nodes, 34 reductions and seven contradiction occurrences. Its 24 new proof
nodes use five new splits, with eight extra exploratory patterns unused.

Thus a slightly shorter proof can still cost more to acquire. Both proofs have
conditional depth three in changing local coordinates, not a fixed backdoor
size. Neither decomposes into separate components, and only contradiction is
shared within each proof. Coverage concerns recognized structural certificates;
this experiment does not add a SAT/UNSAT result API.

The conflict-checked union preserves all **48 distinct new patterns and nine
split records**. It contains **2,263 patterns / 233 pairs / seventeen inherited
missing children**, with an **884-step positive proof for sixteen originals**.
Eight remain unknown. Its serialization uses **42,033,152 SQLite bytes /
2,131,824 gzip bytes**. The complete independent checker replays the parent,
all six trial archives and the union, with original bindings, full catalogs,
query proofs, immutable prefixes, shared budgets and cold scheduling state.

All **372 tests** pass, including five new gate tests. All **303 previous sources,
3,453 artifacts and 64 manuscript proof blocks** remain unchanged. An initial
method-rebinding implementation error was caught by the tests and fixed before
the measured run; its source and failed log are retained separately. The optional
gate remains an experiment, with no default inference or Lean theorem change.

**Next target:** transfer the unchanged rule to **case 10**, a random 3-CNF with
selected **45-variable / 180-clause / 557-literal / width-five** residual. Pivots
20, 3, 17 and 22 have all children present and uncovered. Only the depth-zero
original root exists. Test particularly whether a small early decrease can
hide an expensive continuation that the skipped trial would avoid. A strict
decrease can still lead to greater total work; it is not a global potential or
a minimum-cost certificate. Keep both controls and investigate structural
differences between their obligations if their choices diverge. Broader
nonterminal reuse and full-history audit cost remain larger unresolved limits.
