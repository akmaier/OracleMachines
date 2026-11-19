# First-false composition from transported supports

This pilot tests whether an acquired UNSAT support remains useful when a nearby
residual lacks several of its clauses. It combines the existing causal support
planner, order-preserving variable transport and checked first-false partition.
The supplied origin and variable map propose a route; the original native and
partition checkers remain the authority. The general solver is unchanged.

## Exact scope and cost

Let T be the target residual and K a checked UNSAT core transported injectively
into T's variable coordinates. Write D1,...,Dk for the clauses of K absent from T.
Then T conjoined with every Di is UNSAT, because it contains K. Every satisfying
assignment of T must therefore falsify at least one Di. Its first falsified clause
selects exactly one branch: T, all earlier Dj, and the negation of Di. A clause is
false precisely when each of its literals is false; those assignments reduce the
branch to a residual CNF. This is the previously checked first-false rule.

Every negative branch must be checked before a negative conclusion. A positive
branch supplies a witness that lifts through its fixed assignments and is checked
against T. A branch budget stop gives no conclusion. A result about T, which was
a residual encountered inside an earlier source query, does not discharge that
source query's assumptions or siblings.

The adapter accepts two to five missing clauses whose variables already occur
in T, and requires overlap between T and K. It prepares one causal plan under
32-node, 8,192-literal and 128 KiB retained-plan limits. It emits that same plan
only after choosing the route. The transported core and strengthened premise
pass unchanged native checks. All branches together share a 256-expansion cap.
Unit-trace publication can consume zero recorded expansions while still checking
and storing a new proof; publication counts and bytes are measured separately.

The total work is support discovery and checking, premise publication, branch
construction and screening, the sum of branch solving costs, composition,
serialization and persistence. Constructing k prefixes copies O(kL + kD) literals
before normalization, where L is the target size and D the total missing-clause
size. Screening both orders adds propagation and normalization over those copies.
Sorting, integer operations, proof verification and memory allocation have their
own costs. The small fixed k bounds this particular branching layer; it does not
bound the size of the branch searches or their proofs. Nor do the causal-plan
caps bound prerequisite proof checking, transients or retained archive space.

## Evaluation boundary

The three cases, 25, 31 and 61, come from the preceding mapped-retrieval mismatch
census. The final trial archive already knows each target. Therefore every worker
starts from a fresh database containing only proof rows committed *before* that
case's original source query. All three candidate origins are present in their
prefixes; all target roots are absent. This removes both future results and work
performed earlier within the original query. It is a residual-level comparison,
not a replay of the original source query or a claim of faster discovery.

The preflight log used the final archive only to reconstruct supports and inspect
unit propagation. Its descriptive timings are excluded from the comparison.
Prefix-only validation independently reproduces each support. The timed protocol
supplies the selected candidate rather than searching for it again. Prior
precomputation and candidate selection remain sunk, separately preserved work.

Each prefix also seeds a fixed addition/deletion stream, using one added signed
three-literal clause and one deleted original clause. These six edited roots are
absent from the preceding cumulative proof union. They were generated before
timing without examining their outcomes. The same donor is supplied for each
case's edits. This probes local stability; it is not a broad fresh SAT sample.

Five arms run in separate serial processes in two opposite orders: the current
input-safe affine baseline, a native-only ablation, forward and reverse
first-false orders, and a screen. The native ablation accounts for the fact that
partition children use native proof authority rather than affine/quotient root
dispatch. The screen first handles an unsplit unit conflict; otherwise it checks
both orders and admits an all-terminal cover, or exactly one remaining branch
with at least two unit conflicts and fewer residual literals than the unsplit
screen. Both gains and rejected opportunities are retained without changing the
selector after timing.

The worker measures query work, archive restoration and setup, endpoint checked
objects, RSS, proof deltas, partition sidecars, warm-bank setup and retrieval,
full cold checking, serialization, persistence and reconstruction. Complete time
includes these measurement and replay costs. RSS also includes input archives,
diagnostic snapshots and measurement allocations. Endpoint object measurements
are not peak bounds. Repeated full-prefix checking can dominate complete time.

Proof deltas retain dependency-ordered rows. A checked partition lives in a
separate sidecar and replays through `PartitionBank`; its target need not have a
native proof row. The cumulative union keeps earlier payloads authoritative,
while trial deltas retain alternative proofs. All previous solver archives and
experiments remain intact.

## Results and regressions

All nine targets are UNSAT under every arm; the 60 workers contain 90 query
attempts. Thus this pilot improves selected acquisition costs, not decision
coverage under the shared budget. The table sums the independent case streams
and averages the two orders; times are seconds.

| Measurement | Historical affine | Historical reverse | Edits affine | Edits reverse |
| --- | ---: | ---: | ---: | ---: |
| Query time | 0.16301 | 0.12246 | 0.33742 | 0.31737 |
| Complete measured worker time | 23.88415 | 23.75305 | 24.55101 | 24.40052 |
| Native expansions | 75 | 28 | 155 | 112 |
| New native records | 89 | 61 | 177 | 162 |
| New native key/payload bytes | 825,854 | 309,683 | 1,648,926 | 1,164,063 |
| Endpoint checked-object bytes | 3,510,443 | 2,414,553 | 6,991,998 | 6,148,055 |
| Endpoint SQLite bytes | 188,391,424 | 187,621,376 | 189,726,720 | 188,981,248 |
| Compressed delta plus partition sidecar bytes | 63,713 | 138,360 | 123,386 | 232,098 |
| Full cold proof time | 11.05987 | 11.09044 | 11.23248 | 11.18609 |
| Warm-bank setup plus lookups | 0.00390 | 0.01525 | 0.00686 | 0.02268 |

These endpoint byte totals are sums across three separate archives, not one
combined live archive. The common prefixes dominate SQLite space and complete
workflow time. Historical query time falls 24.87%, edits 5.94%, with faster query totals in both paired
orders. Complete measured time falls only 0.55% and
0.61%, respectively. Two repeats are insufficient to establish a stable gain at
that scale. Historical cold checking becomes slightly slower in both orders.
Warm retrieval alone is cheaper, but loading/checking the partition bank makes
setup plus retrieval more expensive. Persisted delta-plus-sidecar space grows
117.16% and 88.11%: the raw JSON sidecar duplicates source and child descriptions.
Counting only the compressed native proof delta would conceal this regression.

Case 31 explains the benefit. Its reverse partition takes **17 expansions versus
69**, with mean query time **0.06522 versus 0.14747 seconds**, and stores **30
native records versus 81**. The combined edit stream takes **92 versus 143 expansions** and
**0.22353 versus 0.30542 seconds**, storing **111 versus 161 records**. This gain
comes from the addition (17 versus 69 expansions). The deletion removes a core
clause, leaving six missing clauses outside the pilot limit; it falls back and
takes 75 versus 74 expansions in the changed stream state. Case 25's deletion
also exceeds the five-clause limit. Thus the gain does not survive both edit
types individually. Both
nonterminal historical branches invoke binary-backbone reasoning; their recorded
expansions are ten and four. The three unit-conflict branches take one each in
the unscreened arm. New split proof records fall from 32 to eight for the
historical target, and from 64 to 40 across its edits. This is a concrete
conditioning pattern worth investigating, not evidence that all five-clause
gaps or all binary-containing mixtures are easy.

Cases 25 and 61 already need only two and four ordinary expansions. Reverse
partitioning takes six and five and raises query time from 0.00761/0.00793 to
0.02730/0.02994 seconds. Their edits also regress. The screen makes the wrong
selection on this set: it accepts those two cases but rejects case 31 because two
branches remain nonterminal. Its aggregate query time increases **49.47% on the
historical cases and 26.81% on the edits**. Reducing a terminal publication's
recorded expansions to zero does not make its checking and storage free.

Forward ordering has smaller aggregate query gains, 14.85% historical and
1.05% edits. Neither measured order is a justified automatic routing policy.
The affine baseline stays in place. The supplied-candidate adapter is optional
and the earlier failed screen remains an explicit regression control.

## Next gap

The largest remaining edit acquisition is case 31's deletion: 75 of the reverse
arm's 112 edit expansions and about half its edit query time. A read-only
posthoc check reconstructs exactly the prefix plus the first addition, excluding
all deletion results. Allowing its six missing clauses in branch construction
produces four unit conflicts and two nonterminal branches in either order. None
of those branch roots or propagated residual roots has a known native proof in
that state. The reverse nonterminal residuals contain 817/821 literals, 68/70
binary clauses and 227 ternary clauses each; neither is purely binary, Horn or
dual-Horn. No solving or publication occurs. The same useful two-branch shape
therefore survives this boundary, but its partition solving cost remains unmeasured. Preserve
`next-boundary.json` and test it under a new protocol before widening the policy.

Test a bounded structural/cost probe for the first-false branches. It should
inspect exact archive hits and the binary implication/backbone structure exposed
by conditioning, allow multiple unresolved branches when their combined cost is
credible, and avoid spending a large preparation budget on already cheap native
queries. Charge the probe against a shared budget and compare it with the affine
baseline on a new stream. Branch count and residual literal count alone have now
failed as admission rules. The evidence does not yet establish a cheap predictor
of native search effort.

Automatic discovery and selection of the donor/map, broader unlabelled mixtures,
SAT outcomes, and source-level integration remain open. A separate supporting
target is compressing or interning partition sidecars while retaining exact source
bindings and independent replay; this study preserves their current storage cost.
There is no uniform polynomial bound for unrestricted SAT, and no new tractability
or P-versus-NP theorem.

Resume `experiments/results/cnf-transported-partition/checkpoint.json`.
`protocol.json` freezes the cases and policies; `analysis.json` retains paired
costs, branch counters and proof-kind counts. Each trial's `delta.json.gz` and
`partitions.json`, combined with its bound prefix, reconstructs its exact evidence.
The cumulative union and historical audits preserve all previous results. The
initial test fixture error (tuple instead of certificate list) is retained in
`initial-tests/` and `development-tests.log`; it was fixed before timing.

Validation passes: 1,378 full tests and 60 focused tests; independent replay of
90 attempts and 36 partition records; all 684 prior sources and 8,539 prior
artifacts unchanged. The cumulative union grows by 369 native records to 74,204,
with all 71 affine-negative, 42/53/22 equivalence and 34 binary-discovery records
preserved. Six alternative payload observations remain in trial deltas. The
236-page manuscript builds without warnings and its 64 proof blocks are unchanged.
The full suite retains 44 existing unclosed-SQLite ResourceWarnings; the focused
suite emits none. This does not constitute a Lean refinement proof of the Python
adapter. Final source ledger: 690 files.
