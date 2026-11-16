# Test two saved routes before committing expansion

A bounded pilot improves case 11: **19 new patterns instead of 44**, and **77
probes instead of 178**, including the work spent on both candidate routes.
Structural coverage rises **13/24 -> 14/24**. Local expansion time falls
**0.27211 -> 0.11072 seconds (59.31%)**; whole-stream time falls only
**8.23501 -> 7.85315 seconds (4.64%)**, because complete verification dominates.
This is one development input, not a general success guarantee for lookahead.

## The hypothesis and its restrictions

The previous [case-6 counterexample](saved-split-reuse.md) showed that the smallest
visible frontier can lead to more downstream work. The earlier
[one-profile lookahead](lookahead-bank.md) added unused probes without increasing
coverage, even after avoiding recomputation. This experiment therefore retains
and charges full exploratory acquisitions rather than treating scouting as free.
It tests a deeper but narrowly bounded comparison on an existing candidate pool.

Both modes start from the entire same 2,118-pattern / 209-pair parent and use
the same scoped registry, acquisition rules, independent query checker and
canonical complete auditor. The control commits to the saved split with the
smallest existing frontier score. The optional `PilotRefinement` selects the two
best saved alternatives, performs one completed nested acquisition on each,
then commits using lexicographic pending-task count, remaining literal count,
frontier-task count and pivot variable. These remain heuristic costs, not lower
bounds or proof certificates.

All pilot work shares the ordinary **128-admission / sixteen-operation batch
allowance** with subsequent expansion. No per-candidate budget reset occurs.
Both modes permit four batches. A partial acquisition stays on its current arm
until its children finish; a restart retains this phase and all saved decisions.
Thus two completed pilot steps can require more than two interrupted attempts.
Every attempt, repeated admission and probe remains chargeable. Scores,
lookups, checking and persistence also remain in the measured clock.

The current pilot requires an unresolved source below a unary selected root
prefix and at least two saved alternatives. It rejects unsupported prefixes;
it is not a general component scheduler. Scores and restart state select work
only. Exact closure always comes from the full checked route graph and the
unchanged positive-proof checker. Restart never trusts a serialized closure bit.
No inference default changes.

## What the pilot discovers

The original case-11 CNF has 48 variables and 197 clauses. Its selected residual
has 45 variables, 196 clauses, 608 literals and maximum width five. All eight
children of four saved source splits exist and are uncovered. Initial remaining
literal scores for pivots 2, 32, 7 and 6 are **1124, 1118, 1126 and 1106**.
The committed control selects pivot 6; the pilot compares pivots 6 and 32.

| Pilot route | Completed trial | New admissions | Probes | Remaining tasks / literals |
| --- | --- | ---: | ---: | ---: |
| Saved pivot 6 | Split the selected cofactor on local variable 3 | 3 | 28 | 3 / 1535 |
| Saved pivot 32 | Split the selected cofactor on local variable 18 | 7 | 27 | 1 / 559 |

The first route expands its visible obligations. The second closes the tested
cofactor and leaves one remaining obligation. After these ten admissions and
55 probes, the pilot selects pivot 32. One more acquisition, on local variable 2
in its remaining cofactor, completes the original. All six source assumptions
and three new split records are counted. The three pattern rows acquired on
the losing pilot route remain stored, although the final proof does not use them.

## Matched total costs

The [protocol](../experiments/results/cnf-pilot-refinement/protocol.json) fixes
two reversed-order paired fresh-process repetitions on this known development
input. There is no per-arm budget tuning. Tests and retrospective validation
run after the timed streams.

| Resource | Commit immediately | Pilot two saved routes |
| --- | ---: | ---: |
| Batches to coverage | 1 | 1 |
| Distinct admissions / new patterns | 44 | 19 |
| Probes | 178 | 77 |
| Fresh source assumptions | 18 | 6 |
| New split records | 9 | 3 |
| Restoration and setup, seconds | 0.15207 | 0.14347 |
| Expansion including pilot and scoring, seconds | 0.27211 | 0.11072 |
| Bookkeeping, seconds | 0.11285 | 0.09235 |
| Independent query-proof check, seconds | 0.13969 | 0.07903 |
| Complete cold audit, seconds | 6.70562 | 6.59457 |
| Compression, seconds | 0.76284 | 0.74649 |
| Whole stream, seconds | 8.23501 | 7.85315 |
| Mean peak process RSS, bytes | 388,456,448 | 382,541,824 |
| Final SQLite bytes | 40,247,296 | 39,776,256 |
| Compressed snapshot bytes | 2,022,398 | 1,993,471 |

New pattern count falls **56.82%**, probes **56.74%** and local expansion time
**59.31%**. Total peak RSS falls **1.52%**, total SQLite size **1.17%**, and gzip
size **1.43%**. The already acquired history dominates total storage and checking,
so the larger acquisition reductions do not transfer proportionally to total
runtime or memory. The candidate's full audit still takes **84.0%** of its
stream, compression **9.5%**, and local expansion about **1.4%**.

The clock includes restoration, setup, all selection and acquisition, bookkeeping,
compression and both cold checks. It excludes interpreter imports and the final
summary write; RSS includes imports and all phases. Parent acquisition remains
recorded in earlier experiments. No universal speedup, memory saving or optimal
choice follows from two pairs of runs on one input.

## Proofs and actual sharing

The control proof has **53 distinct steps**: ten conditional nodes, 42 unary
reductions and one contradiction terminal. Maximum conditional depth is five.
The pilot proof has **29 steps**: three conditional nodes, 25 unary reductions
and the same terminal, with maximum depth two. There are no component splits
in either proof. Control reductions comprise 29 probes, six binary-path steps
and seven eliminations; pilot reductions comprise sixteen probes, four
binary-path steps and five eliminations.

The control uses nine parent steps and 44 new steps; the pilot uses thirteen
parent steps and sixteen new steps. Each proof uses one saved source split.
Only contradiction is shared within either proof, with eleven and four leaf
occurrences respectively. Unfolded counts 63 and 32 become 53 and 29 distinct
steps. Changing local coordinates and intervening reductions mean these depths
are not fixed backdoor sizes or minimality results.

The two acquisitions share three new pattern rows and one split record from
the common first exploration. None of those new rows is shared by the two final
proofs: the winning pilot proof does not use the losing route's three rows.
This is reuse of a common exploratory prefix, not evidence of new reusable
nonterminal components across inputs. The conflict-checked union preserves all
**60 distinct new patterns / eleven new splits**, including exploratory work.

## Verified checkpoint and next test

The union contains **2,178 patterns / 220 pairs / seventeen inherited missing
children**, with an **807-step proof for fourteen originals**. Ten remain unknown.
It occupies **40,517,632 SQLite bytes / 2,037,803 gzip bytes**; storing both arms
is larger than either individual result. All **367 tests** pass. New tests cover
the single shared budget, pending-stage cold recovery, equivalence after restart,
and rejection of foreign or inconsistent scheduling state. Independent frozen
auditing checks the parent, four trial archives and union, plus per-query proofs,
original bindings, complete reachable catalogs and unchanged historical rows.
An additional eight-admission interruption check spends three admissions on
route 6 and only the remaining five on route 32; the second trial stays pending.
It stores seven rows. Cold reopening acquires nothing, then resumption stores
twelve more rows and produces the same 29-step proof. The second batch charges
twelve admissions, including one reentered unfinished state, so total admissions
are twenty rather than nineteen. It reuses the pending pair and charges only
two new source assumptions. This confirms that interrupted work is not free.
Successful retrospective validation takes **75.45 seconds**, outside operational
timings and partly concurrent with tests. All earlier sources, results and
64 manuscript proof blocks remain unchanged.

Next transfer the unchanged pilot and committed control to **case 13** before
considering adoption. Its selected residual has **47 variables / 213 clauses /
649 literals / maximum width four**. All eight children of saved pivots 47, 41,
44 and 5 exist. Pivot 41's true child is covered; the other seven are not. Both
original recognition-depth roots exist. Check the unary-prefix precondition,
preserve the covered side, and charge every trial. The case-6 counterexample and
older negative lookahead result remain active controls against overgeneralizing
this success. Efficient selection, compact retained closure and bounded total
acquisition for arbitrary SAT remain open.
