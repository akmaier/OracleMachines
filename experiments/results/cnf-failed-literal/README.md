# Bounded checked failed-literal discovery

9 November 2026. Optional analysis layer; the ordinary SAT solver is unchanged.

The previous fused-edge study left 107 of 437 non-tiny inputs unresolved. This
study adds standard failed-literal probing before arbitrary conditioning, after
the existing family, component, simplification and projection gates. Rank
variables by binary-clause incidence, tie by identifier, and test false then
true for up to one or four variables per eligible residual. Stop at the first
checked unit conflict and retain the opposite assumption plus its unit closure
as one edge, at unchanged branching depth. A successful rewrite strictly reduces
variable support; subsequent residuals receive their own probe budget.

This is established look-ahead, not a new SAT technique: Heule and van Maaren,
*March_dl: Adding Adaptive Heuristics and a New Branching Strategy*, JSAT 2
(2006), 47--59, Section 2, describe failed literals, preselection and additional
look-ahead. [Author-hosted paper](https://www.cs.cmu.edu/~mheule/publications/JSAT2_3_Heule.pdf).
Our contribution here is its checked, persistent integration and measurement in
the existing structural inventory. No novelty or unrestricted efficiency claim
is made for the reduction itself.

## Correctness and applicability

If unit reasons refute `F|x=b`, every model of F has `x != b`. Consequently F is
satisfiable exactly when `F|x=!b` is. Checked simplification of that branch gives
the exact existential relation on the remaining variables, and its models lift
through the forced value and saved unit assignments. A no-conflict probe only
means propagation stopped without a contradiction. It is not a model, a proof
of satisfiability, or a proof that no forced value exists.

In a normalized residual at a unit fixed point, a single assumption outside
every binary clause cannot start propagation: it leaves every unsatisfied
clause with at least two literals. Restricting candidates to binary incidence
therefore omits no direct failed-literal opportunity in that situation. Limiting
the number of these variables can omit opportunities. Larger look-ahead or
reasoning beyond unit propagation remains a separate obligation.

Every probe attempt, including an inconclusive one, is stored in the parent
profile. Independent checking regenerates the candidate order and verifies each
reason, conflict or no-conflict fixed point. It does not rerun probe discovery.
The retained branch closure, exact child identity, variable transport and lifted
parent model are checked. Policy identifiers isolate the new records; older
records remain unchanged. No separate full retained intermediate is acquired.

`failed_condition_forces` and `satisfiable_failed_condition` in
`formal/OracleMachines/Residuals.lean` prove the semantic implication and SAT
reduction from a supplied branch refutation. They do not verify the Python unit
trace checker, SQLite implementation or resource bounds.

## Matched results

All 949 earlier inputs are preserved. After the 48-case development pilot,
fixed policies were tested on another 64 seeded random inputs and 12 crafted,
renaming and invalidation controls: 1,025 inputs total. Planner depth two and
four arbitrary conditioning candidates are identical. Input labels never select
the method. Coverage means all selected leaves have checked structural closure;
it does not mean the formula is SAT. All modes independently run the same
original-source decision solver, retaining the same 5,379 solver residuals.

| Mode | Closed / 513 non-tiny | Fresh random / 64 | Total seconds | SQLite bytes | Cold seconds | Pattern nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ordinary solving alone | -- | -- | 7.62782 | 21,856,256 | 1.37401 | -- |
| Fused shortest-clause baseline | 358 | 19 | 27.11056 | 93,143,040 | 10.07933 | 8,761 |
| One probe variable | 465 | 43 | 18.93343 | 69,357,568 | 7.09169 | 5,555 |
| Four probe variables | 484 | 51 | 18.87839 | 65,056,768 | 6.41165 | 5,271 |

On the old 437 non-tiny inputs, closure rises from 330 to 412/423. On the fresh
32 pure 3-CNFs, it rises from 1 to 18/23; on the fresh 32 mixed-width CNFs, from
18 to 25/28. The four-variable policy gains 126 closures and loses none against
the baseline on this corpus. Of these gains, 88 inputs are SAT and 38 UNSAT.
The 12 constructed controls are not independent random holdout draws. More
probing is not a proven monotone coverage or cost improvement under a bounded
planner: reductions change later choices and sharing.

The four-variable policy stores 17,352 attempts, including 14,394 inconclusive
attempts, and 2,958 forced rewrites. Arbitrary conditioning candidates fall from
5,552 to 1,241. These forced rewrites consume computation even at depth zero
(1,799 such nodes), so unchanged branching depth does not mean equal search
effort. New policy metadata adds 199,875 exact-source bytes. All unsuccessful
traces are charged, including 1,603,667 JSON bytes for inconclusive attempts.

Timing includes discovery, recognition, checking, serialization, persistence,
original-source solving and successful root model lifting. Generation, truth
tables, summary traversals and offline compression are separate. Initialization,
warm reuse and full cold checking are separately recorded. These are single
sequential synthetic measurements, not significance estimates or an industrial
solver comparison. The analysis layer still costs more than ordinary solving
alone. Four-variable warm replay slightly regresses, 0.12492 -> 0.12835 s.

Separate six-case traced Python peaks fall from 3,776,338 to 2,024,266/1,968,117
bytes. The fixed case IDs are 777, 790, 819, 850, 885 and 889. This diagnostic
excludes native SQLite memory, RSS and full-corpus peak allocation. Its timings
do not enter the operation comparison.

The old 48-case in-memory pilot is retained in `pilot.json`: closure 13 -> 45/47,
time 2.67640 -> 0.79497/0.77578 s. It excludes the ordinary solver, root lifting,
disk persistence and full cold audit, and is not a holdout result.

## Remaining limits and reproduction

The four-variable policy still misses 29 non-tiny inputs. Some misses become
slower: old 32-variable case 894 is its largest discovery cost, 0.7495 s. Retained
probe nodes now account for 12,544,663 of 22,743,434 logical node bytes; failed
alternatives and original source records remain available. Fewer unresolved
leaves does not itself prove lower total cost or a polynomial decomposition.

The post-study `limits.json` diagnostic probes all binary-clause variables on
these 29 misses (cap 64; every source has at most 34 variables). It closes only
two additional cases, 968 and 1024. Inventory-only time rises from 6.81731 to
11.49531 s, SQLite from 20,533,248 to 24,760,320 bytes and cold audit from 2.92937
to 5.05773 s. The two separate archives retain all attempts. Every remaining
unresolved node in the cap-64 archive has probed every binary variable; this
exhausts direct unit-conflict probing at those nodes, not all logical inference
or alternative decompositions. Raising the probe cap globally is not justified
by this diagnostic. The first diagnostic archive lacked ordinary-solver tables;
the shared auditor created them and correctly failed byte preservation. The
initial archive and failure log remain saved. Initializing empty solver tables
before snapshotting fixes this harness issue; both final audits preserve bytes.

A separate profile of case 894 attributes most own time to restriction scans,
unit checks/propagation, normalization and their literal-processing helpers.
Its instrumented 1.95009 s is not comparable to the uninstrumented main timing.
`common-implication-opportunity.json` identifies a more targeted next discovery
step: in 245 archived clear-probe nodes, the two assumptions already imply a
common literal. Of these nodes, 179 are unresolved and 66 are OR nodes. By
Boolean case splitting such a common consequence is forced. These counts
include unsuccessful alternatives and do not measure new root coverage. The
planner does not yet use these consequences. Reusing their existing checked
traces could expose more structure without fresh propagation; certificate
selection, invalidation, composition and matched total costs still need testing.

Per residual with v variables and L literal occurrences, at most 2k probes
plus one retained closure use the existing scan propagation. A conservative
word-operation bound is O(k(v+1)L + v log v), plus existing recognition,
normalization, serialization and persistence. Each trace has at most v unit
reasons and one clause index; probe evidence is O(kv log(v+m+2)) bits, apart from
full CNF/profile/key storage. Budgets restart on reduced residuals and each
acquired branch. They do not bound the total number of residuals or provide an
efficient complete arbitrary-SAT classification.

All 319 Python tests pass, including exhaustive small fibers, random mixtures,
renamings, additions, invalid proof transport and cold corruption. All four new
and seven preceding complete archives replay without byte changes or fresh
solver expansion. The Lean build/audit passes at 4,089 declarations and 1,948
theorem declarations. `report.json` contains every source, record, fingerprint
and archive digest; `summary.json` and `mechanisms.json` retain coverage changes,
inconclusive probes and all remaining misses.

Run from the repository root with a new destination, preserving this result:

```sh
python3 experiments/compare_cnf_failed_literal.py --output /tmp/new-probe-study
python3 experiments/analyze_cnf_failed_literal.py /tmp/new-probe-study
python3 experiments/probe_failed_literal_limits.py /tmp/new-probe-study
python3 experiments/analyze_cnf_probe_implications.py /tmp/new-probe-study
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
