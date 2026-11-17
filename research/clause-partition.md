# Exact partitions from several missing clauses

Let T be the target after its existing checked guards, and let C1,...,Ck be
ordered missing clauses. A checked negative proof of T ∧ C1 ∧ ... ∧ Ck implies
that every model of T falsifies at least one Ci. Partition models by the first
false clause. Branch i is

    Bi = (T ∧ C1 ∧ ... ∧ C(i-1)) restricted by every literal of Ci being false.

Every model of T belongs to exactly one branch, and each branch model lifts to
a model of T. Disjointness includes the branch's fixed literals; residual CNFs
viewed without those assignments can overlap. Earlier clauses remain constraints; assigning every missing clause
false at once is unsound. All branches must be checked negative to conclude
UNSAT. A SAT branch gives a model, so solving can stop after that branch. The
implementation retains the checked prefix of branch outcomes, requires earlier
outcomes to be negative, and verifies SAT model lifting through the partition
and the original guards.

The interface accepts distinct nonempty missing clauses over existing target
variables, in shared raw coordinates, absent from T. It rejects tautologies and
invalid literals using the existing clause interface. The strengthened negative
premise is checked directly when stored, or published from an actual checked
negative core by the frozen subset rule. Premise acquisition cannot call fresh
SAT search. Branch solving uses the ordinary native solver and shares its archive
within the plan. No general formula-equivalence recognition is introduced.

Native proof formats remain unchanged. A `checked-first-false-partition-v1`
sidecar binds the source, earlier guards, ordered missing clauses, strengthened
premise and native children. Branch CNFs are reconstructed, not copied into each
child record. Child keys still encode their canonical formulas, so the sidecar
is not constant size. `PartitionBank` checks these records on load and supports
normalized-source lookup in an exclusively owned immutable or append-only proof
session. Native root lookup alone need not contain the composed source result.

## Cost obligations

For k missing clauses, this step has at most k branches; recursive use can still
multiply work. If L bounds the target, strengthened formula and every branch
prefix/residual encoding, construction and retained child keys can require
O(kL) space in addition to source/guard records, models and native proof storage. Every branch solve, premise check/publication,
normalization, model lift, lookup, serialization and cold replay is charged.
The number of missing clauses does not bound child proof size or the combined
solve cost. Earlier true clauses and the selected false clause can expose reuse,
but can also duplicate work or hide a useful original propagation path.

The current implementation provides exact composition. It does not provide a
minimum-cost core or clause-order selector, a uniform polynomial construction
for arbitrary SAT, or a new Lean theorem.

## Historical matched comparison

The study restores the exact persistent prefix immediately before each of cases
68, 6 and 135 in the preceding premise-first stream. Every arm opens a cold live
checker and repeats ordinary preparation plus the failed single-clause selector.
The baseline reproduces the preceding native proof payloads exactly. For each
nearest ready core reported by the earlier diagnosis, the study tests the listed
clause order and its reverse. This gives three baseline and eight partition arms.
Every partition publishes one new strengthened-premise row without fresh SAT
search. Branches then share the same native archive within that arm.

| Case / plan | Branch expansions | Total expansions | New rows | Added native payload | Delta plus sidecar bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| 68 baseline | 27 | 27 | 27 | 32,827 | 49,672 |
| 68, core 210 forward | 19 / 1 / 1 | 21 | 22 | 27,086 | 46,642 |
| 68, core 210 reverse | 1 / 7 / 16 | 24 | 25 | 30,177 | 49,861 |
| 68, core 258 forward | 4 / 10 / 7 | 21 | 22 | 24,641 | 44,162 |
| 68, core 258 reverse | 9 / 1 / 1 | 11 | 12 | 16,605 | 35,676 |
| 6 baseline | 7 | 7 | 7 | 11,296 | 25,002 |
| 6, core 240 forward | 5 / 1 / 1 | 7 | 8 | 12,282 | 28,299 |
| 6, core 240 reverse | 1 / 1 / 1 | 3 | 4 | 6,122 | 21,959 |
| 135 baseline | 7 | 7 | 7 | 10,761 | 24,497 |
| 135, core 211 forward | 1 / 7 | 8 | 9 | 11,560 | 26,975 |
| 135, core 211 reverse | 9 / 1 | 10 | 11 | 14,567 | 30,072 |

The best tested case-68 plan reduces expansions **27 -> 11**, new rows **27 -> 12**,
added native payload **32,827 -> 16,605 bytes**, and retained delta-plus-sidecar
size **49,672 -> 35,676 bytes**. Case 6 improves **7 -> 3** in reverse order, but
its forward plan adds a row without reducing expansions. Both case-135 plans
regress. Even a smaller core distance of two missing clauses is not a guarantee
of useful reuse. All historical queries and branches are UNSAT; independent SAT
controls exercise positive branch selection and model lifting.

Baseline search totals 41 expansions. Trying all eight candidate plans costs
**105 expansions**, without cross-plan sharing. The best observed partition for
each case totals 22, or 21 if case 135 keeps its baseline. These are post-hoc
choices, not a deployed policy or an end-to-end saving after plan discovery.
All candidate results and regressions are retained. There is no fresh source-query
coverage in this experiment.

Single-sample query-phase costs include premise checking/publication, branch
construction/solving and composition. Case 68's best plan uses 0.014149 seconds
versus 0.021287 baseline; case 6's reverse plan uses 0.007501 versus 0.008276.
Both case-135 plans cost more (0.010548/0.012343 versus 0.007334). Complete cold
proof/sidecar/lineage replay costs roughly 5.02–5.30 seconds per arm. Preparation,
prefix reconstruction, warm-bank construction, serialization and snapshot/export
overhead remain additional charges. Single historical samples establish no
stable total runtime or peak-memory improvement. Native payload measures IDs
plus ASCII JSON, not live memory; the union retains all old proofs and all new
variants rather than shrinking to the best policy's footprint.

## Recognition signals and the next gap

A separate read-only probe runs the frozen unit propagator on each candidate
branch without searching or publishing. Its traces and conflicts match the
native certificates checked during independent replay. The best case-68 plan
has **two terminal conflicts and one residual with 122 literals**; the competing
core-210 forward plan also has two terminal conflicts but leaves 153 literals.
Core-258 forward leaves three nonterminal residuals. The better case-6 order
makes **all three branches terminal unit conflicts**; its forward order leaves
one 132-literal residual.

The next priority is bounded plan screening with these checks, retaining the
unit traces so recognition is not repeated during proof publication. Then test
on fresh excluded inputs with index construction, candidate checks, premise
publication and cold replay charged. This probe uses already selected plans;
it implements neither a selector nor a cheaper producer. Recognizing all-terminal
branches gives a concrete proof path, while choosing among unresolved branches
still needs a cost policy.

Case 135 is the necessary regression control. Its forward plan leaves only
117 nonterminal literals, fewer than the baseline's 158, yet costs eight rather
than seven expansions and adds two rows. Residual size and terminal-branch count
are therefore insufficient to certify a saving. Broad coverage, efficient plan
discovery, cross-plan sharing and uniform bounds remain open. General variable
branching also partitions models exactly; coverage alone cannot make arbitrary
SAT cheap.

## Validation and resume state

All **1,035 solver tests** and fourteen focused partition/chain tests pass. The
new tests exhaustively check two-variable model coverage and disjointness under
the fixed assignments, compare three-variable outcomes with independent truth
tables, exercise SAT success after an earlier negative branch, check original
guard lifting, replay from disk, and reject incomplete negative partitions,
reordered children, missing proofs and malformed clauses. A satisfiable control
shows why falsifying all missing clauses at once is unsound. The full suite
retains 44 older unclosed-SQLite ResourceWarnings; focused tests emit none.

Independent validation reconstructs every pre-query prefix and native delta,
checks all eleven complete native archives and both measured index lineages,
rebuilds the ordered branches independently of the partition constructor, and
replays all conclusions without fresh search. All **2,957 inherited ordinary
decisions**, **200 inherited chain records** and **eight new partition records**
pass. The latter describe three historical sources and alternative plans, not
eight fresh queries. All baseline native payloads match the earlier stream.

Resume `experiments/results/cnf-clause-partition/checkpoint.json`: **21,225 native
keys**, adding 97 while preserving all 21,128 prior payloads. There are no
alternate native certificate occurrences. The union occupies **66,703,360 SQLite
/ 4,911,472 gzip bytes**. Per-arm deltas and sidecars preserve every tested plan,
including regressions. Native source roots need not exist for composed answers;
load the bound records through `PartitionBank`. Four complete frontier lineage
checks pass, with ready/pending counts unchanged at **130/40 original, 137/70
legacy, 79/97 causal and 79/124 optional expanded causal**. No new support origins
are acquired.

The original structural authority remains 2,614 patterns / 259 pairs / 17 missing
children, with 17/24 original coverage and 999 steps; supplemental authority stays
24/24 with 208 steps. Prior semantic fields remain, apart from updated parent,
union and source bindings; two partition fields are added. The paper builds
cleanly to **204 pages**, preserving all **64 existing proof blocks**.

Runtime binds 433 sources; the post-hoc analyzer and propagation probe bring the
final ledger to 435. Preservation checks pass for **429 prior sources and 4,706
artifacts in 82 manifests**. No new Lean result, fresh coverage, stable total
runtime improvement or unrestricted-SAT resource theorem is claimed.

New manifest: **56 artifacts**. Next preservation audit: **4762 artifacts / 83 manifests**.
