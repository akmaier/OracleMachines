# Implementation follow-up: seven remaining gaps

This record tracks the work requested on 7 November 2026. A completed
implementation is distinguished from a stronger theorem that it does not prove.
Earlier experiments and persisted results must remain intact.

## Latest evidence: transfer limits and six exported root refutations

[Frozen external transfer and root exclusions](boundary-transfer-and-root-exclusions.md)
expose the limit of the preceding constructed-panel success. On **24 new SATLIB
originals plus 12 derived controls**, both unchanged repair policies certify
**8/24 originals and 4/12 controls**, with no gained or lost SAT answer. Selection,
indices and policy were frozen before acquiring the new contents; this remains
a nonrepresentative, size-limited sample.

Mean complete cost changes **11.06400 → 10.96200 seconds (−0.92%)**, with mixed
paired signs: no reliable transfer speedup. Combined compressed evidence grows
**2,027 → 478,862 bytes** and two cold replays **0.09521 → 0.61522 seconds**.
Reduced search work is largely offset by conditional-proof costs.

A separate additive exporter recovers **six checked global root refutations**
that the repair wrapper discarded: four originals and two controls. Fresh
acquisition plus recording replay stays within the same 20,000 total states.
The repair kernel then certifies **12 SAT + 6 UNSAT**, leaving 18 unknown. These
six negatives overlap the older portfolio; the combined union stays **22/36**.
Only a checked full-support root refutation grants global UNSAT authority.

The unchanged portfolio certifies 9 SAT + 10 UNSAT. A fresh Z3 reference returns
18 SAT + 18 UNSAT; its SAT models are source-checked, but its UNSAT outputs are
trusted audit results, not project refutations. Combining the portfolio and
repair kernels leaves **14 cases: six reference-SAT and eight reference-UNSAT**.
All are connected. Attempted repair regions span **83–100 of 100 variables** or
**69–72 of 75**; these are observed widths, not minimum-width proofs.

All **2,552 full and six focused tests pass**. The exporter agrees with truth
tables on all 512 two-variable CNFs (95 SAT, 417 UNSAT). Validation reproduces
all paired outcomes/counters/replays and all exports, preserves 246 prior
manifests, 82,741 artifact entries, 1,341 old scientific sources and 86 proofs,
and rechecks the old external union. Old external 37/37, constructed 32/32 and
synthetic 182/182 results remain separate. Resume
`experiments/results/cnf-boundary-transfer/checkpoint.json`, key `boundary_transfer`.

**Largest remaining gaps:** analyze the retained six SAT and eight UNSAT misses;
reduce wide interactions; reuse or compress conditional negative evidence; and
export completed refutations without duplicate acquisition. Retuning must be
followed by new frozen transfer inputs. Efficient recognition, preprocessing and
unrestricted expansion bounds remain open.

## Previous evidence: proof-guided repair completes the exposed panel

[Proof-guided boundary repair](proof-guided-boundary-repair.md) closes the three
retained misses: **29/32 → 32/32** checked models on the exposed constructed
repair panel, at the unchanged **20,000 total states per input**. All 29 earlier
models survive unchanged. This is an exploratory kernel result; the external
37/37 and synthetic 182/182 unions remain separate and unchanged. No production
default changes or fresh transfer claims.

A freshly acquired near-model supplies an outside assignment. Exact conditioning
keeps every induced constraint; independently checked local refutations identify
outside variables to free. Prefix flip/keep commitments are released. Source
occurrences and projections are reused across rounds, while local search is
rebuilt and charged. Local UNSAT excludes only its outside context; SAT requires
a complete original-source model check.

The 10,000-state prefix and all subsequent rounds share the 20,000-state cap.
IDs 24, 25 and 29 finish in **10,468, 10,011 and 15,731 states**. Their successful
free sets have **77, 8 and 78 of 80 variables**. Eleven local exclusions guide
fourteen rounds. Near-model acquisition is charged, and broad interactions
remain in two cases; these widths are not proved minimal.

Mean complete measured cost falls **2.64746 → 2.18151 seconds (17.60%)**, with all
four paired signs favorable. States fall **118,552 → 94,762**. Checking and replay
increase; combined compressed model/discovery evidence grows **6,685 → 22,531
bytes**. A retained small-cap restart regression prevents a dominance claim.

All **2,546 full and 18 focused tests pass**. Truth tables validate **8,402**
conditional queries (1,033 SAT and 7,369 excluded), with 6,704 incremental/direct
checks and a reproduced audit. Validation preserves 245 prior manifests, 82,407
artifact entries, 1,336 old scientific sources and 85 old proof blocks, and
rechecks the old external union. Resume
`experiments/results/cnf-boundary-repair/checkpoint.json`, key `boundary_repair`.

**Largest remaining gaps:** freeze unseen external sources for transfer; measure
the fixed policy against the full portfolio and a fresh solver; explain the
77/80 and 78/80 residual coupling; and reuse negative evidence across contexts
and edits. Efficient recognition, preprocessing, compact proofs and unrestricted
expansion remain open. Complete finite coverage and exact conditioning do not
supply a polynomial solution of every CNF class.

## Previous evidence: disjoint repair closes seven retained misses

[Disjoint repair partitions](disjoint-repair-partitions.md) close **seven of the
ten** retained repair misses at the unchanged 20,000-state cap: **22/32 → 29/32**
on the already exposed constructed panel, with no lost SAT result. This is a
repair-kernel comparison, not fresh external coverage or full-portfolio status.
The old external 37/37 and synthetic 182/182 unions remain separate and unchanged.

Each state records flipped variables and variables fixed at their seed values.
A false clause branches on its first flipped available variable, keeping earlier
candidates unflipped. These child solution sets form an exact disjoint partition.
Occurrence lists and untouched satisfaction counts are shared across DFS states;
independent checkers verify full models or complete source-bound exclusion trees.
Budget exhaustion remains unknown. No production default changes.

Mean complete kernel cost falls **4.05347 → 2.56805 s (36.65%)**, with all four
paired signs favorable. Explored states fall 274,481 → 118,552. Storage grows
because seven more complete witnesses are retained: gzip 4,184 → 5,547 bytes.
A six-variable counterexample takes **9 states previously versus 13 now**, so
there is no universal ordering or fixed-budget dominance claim.

The prior radius-25 exclusion shrinks **35,065 → 4,307 states** and **272,571 →
56,512 gzip bytes**. A checked distance-26 model reconfirms the same minimum
repair distance. The new proof fits the 20,000-state cap; the old diagnosis and
its larger allowance remain preserved.

All **2,528 full and 23 focused tests pass**. Truth tables validate **25,534 ball
queries over 5,108 inputs**. Validation
reproduces all eight comparisons, checks 244 prior manifests and 82,078 artifact
entries, preserves 1,331 old scientific sources and 84 old proof blocks, and
rechecks the external 37/37 union. Resume
`experiments/results/cnf-partition-repair/checkpoint.json`, key `partition_repair`.

**Largest remaining gaps:** constructed IDs **24, 25 and 29** still exhaust the
fixed cap. All have eighty variables; rejected near-models with **one, one and
five false clauses** and their exact contexts are retained. Investigate small
conditional interfaces and guarded reuse of the remaining interactions before
raising budgets. Full-portfolio status of these three is unmeasured; freeze
unseen external inputs before transfer claims. General efficient recognition,
compact negative proof reuse and unrestricted expansion bounds remain open.

## Previous evidence: exact repair completes the exposed external panel

[Exact bounded repair](hamming-repair.md) closes `uf50-01000.cnf`, the last
unresolved input on the **already exposed** external panel: **24/25 → 25/25
originals**, with **12/12 derived controls** unchanged. The earlier synthetic
182/182 union remains separate. This is finite panel completion, not a new
tractable class or a representative external coverage estimate.

A clause-derived seed and a freshly built occurrence index support exact search
over flip sets. A false clause requires another flip; disjoint false-clause
supports give checked lower bounds. Memoized masks share convergent states.
The fixed 20,000-state gate finds a fully checked model in **12,669 states**.
Budget exhaustion remains unknown, and production defaults are unchanged.

A separate checked exclusion DAG rules out **all assignments within 25 flips**
of the retained seed; a distance-26 model proves the **minimum repair distance
is 26**. This explains why local repairs were difficult despite only 26 initially
false clauses. The larger diagnostic budget and its storage/checking costs are
recorded separately. Ball exclusion is not global UNSAT unless its radius spans
the full source support.

Mean measured complete cost is **23.43449 → 23.30960 s (−0.53%)**, with mixed
paired signs (+2.50%, −0.75%, −1.94%, −1.78%): no reliable speedup is claimed.
Discovery gets more expensive; replacing the incomplete proof by a 1,237-byte
model makes checking and replay cheaper. Gzip proofs fall 419,973 → 402,186 bytes.

Truth tables validate **25,629 ball queries over 5,108 inputs**, including all
228 retained SAT domain misses and fresh signed/edited mixtures. Explicit search
solving those small misses does not improve their structural classification.
All **2,505 full and 20 focused tests pass**. The evidence preserves 243 prior
manifests, 81,700 artifact entries, 1,326
scientific sources and all 83 earlier proof blocks; one exact-coverage proof is
added. Resume `experiments/results/cnf-hamming-repair/checkpoint.json`, key
`hamming_repair`.

A separately frozen repair-only probe on 32 new constructed planted-SAT sources
finds **22 models and 10 budget-exhausted cases** at the unchanged cap. These ten
sources are retained for the next structural investigation; they are not claimed
to be unresolved by the full portfolio. Five capped searches reach one false
clause, which supplies no certificate. This is not fresh external evidence.

**Largest remaining gaps:** analyze those ten fixed-policy repair failures;
freeze unseen external encodings at the fixed policy;
reduce coupled interactions through better seeds, small interfaces and richer
nonclique descriptions; and obtain economical, reusable negative evidence.
General recognition, edit invalidation, compact acquisition and unrestricted
SAT expansion bounds remain open. Removing this panel's final unresolved input
does not remove those obligations.

## Previous evidence: checked choices complete the derived controls

[Checked signed-choice witnesses](signed-choice-witnesses.md) close the edited
`hole10` with a complete SAT assignment. On the **already exposed** external
panel, original coverage stays **24/25**, and derived controls rise **11/12 →
12/12**. No old verdict is lost. This is an exploratory follow-up, not a fresh
external holdout; the prior synthetic 182/182 union remains separate.

The proposer extracts signed, variable-disjoint choices, groups binary conflicts
by connected component, and reuses the existing matching helper to construct an
assignment. A component need not be a clique: capacity one is conservative and
can miss SAT models. Matching success is only a proposal; **every original clause
is checked**. Failed matching or a rejected assignment grants no UNSAT authority.
The new edit has nonclique components and ten unclassified clauses, yet the
complete witness satisfies all 560 source clauses. Source checks, not structure
labels, authorize it.

Mean measured complete cost falls **25.55132 → 23.38105 s (8.49%)**, with all four
paired signs favorable. Discovery, verification, persistence and warm/two cold
replays are charged; compressed proofs shrink **445,436 → 419,935 bytes**.
There is no general fallback solver, so this is not complete solving cost or a
fresh-CDCL comparison. The optional gate leaves production defaults unchanged.

**Largest remaining external gap:** `uf50-01000.cnf`. Both choice attempts produce
the same rejected assignment, violating **26 of 218 clauses**; fifteen selected
ternary demands leave 203 clauses outside the proposed structure. The rejected
assignments and violated-clause indices are retained for bounded repair or
conditioning research, without assuming those repairs will be cheap.

**General recognition gap:** the first extraction separates six strict choice
instances, five fully represented nonclique instances and 26 partial structures.
These are policy-dependent categories, not canonical semantic classes. The truth
audit finds all 1,700 witnesses sound across 5,457 small/adversarial inputs, but
only 19/247 satisfiable domain restrictions and 5/47 SAT fresh controls receive a
witness. All 228 missed SAT domain inputs and fresh counterexamples are retained;
these are gate-only misses. Nonclique compatibility, overlapping demand selection
and remaining clauses need richer representations or explicit search.

All **2,485 full and 18 focused tests pass**. The validator reproduces all eight
runs and cold checks while preserving 242 prior manifests, 81,349 artifact entries,
1,321 scientific sources and 83 proof blocks. Resume
`experiments/results/cnf-choice-witness/checkpoint.json`, key `choice_witness`.
Prioritize the surviving clause interactions and retained recognition failures,
then freeze unseen external encodings before broader transfer claims. Unrestricted
SAT acquisition/expansion bounds remain open.

## Previous evidence: checked capacity cores close five external originals

[Clause-derived capacity cores](capacity-core-certificates.md) close all five
previously unresolved pigeonhole originals and their signed renaming. On the
**already exposed** external panel, coverage rises **19/25 → 24/25 originals**
and **10/12 → 11/12 derived controls**, with no lost result. This follow-up is
motivated by the prior gap; it is not fresh holdout or representative coverage.
The earlier synthetic 182/182 union remains separate and unchanged.

A checked inconsistent subset supplies whole-source UNSAT authority: selected
source clauses have disjoint literal sets, their literals are partitioned into
groups with checked pairwise exclusions, and demand exceeds capacity. Greedy
selection and a clique partition propose the structure; an alternating reachable
subset can isolate local deficiency. The checker verifies source containment,
disjointness, every exclusion and strict deficiency without discovery. Reuse
under additions or edits requires fresh current-source support checks. A matching
or failed recognition does not prove SAT. The remainder is unrestricted.

In four new paired runs, complete measured cost falls **35.06016 → 25.69409 s
(26.71%)**, with all paired signs favorable. Discovery, internal/explicit checking,
persistence and warm/two cold replays are charged. Compressed proofs shrink
**562,876 → 445,179 bytes**. There is no fallback solver and two inputs remain
unanswered, so this is not complete solving cost or a fresh-CDCL comparison.
The gate is optional; production defaults stay unchanged.

**Remaining external gap:** `uf50-01000.cnf` is the one unresolved original;
the edited `hole10` control also remains open. Inspect their coupled interaction
and possible checked SAT reconstruction. **Recognition gap:** independent truth
tables certify all 1,260 emitted refutations across 5,462 small/adversarial inputs,
but greedy search misses thirty UNSAT domain restrictions and two UNSAT mixtures.
Their exact sources are retained; these are gate-only misses, not claims that
the full pipeline leaves them unanswered. Better bounded demand selection or checked core
reuse through edits should target these counterexamples, followed by unseen
encodings. No general renaming invariance or compact-core guarantee is proved.

All **2,467 full and 20 focused tests pass**. The new counting proof preserves all
82 earlier proof blocks; all 241 preceding manifests, 80,996 artifact entries and
1,316 scientific sources are unchanged. The validator reproduces certificates,
counters and warm/cold checks for all eight runs. Resume
`experiments/results/cnf-capacity-core/checkpoint.json`, key `capacity_core`.
Broader auxiliary/non-clique encodings, economical recognition, validated context
reuse and unrestricted expansion bounds remain open.

## Previous evidence: frozen external coverage and capacity gaps

[Frozen external SATLIB audit](external-cutset-audit.md) separates the prior
synthetic completion from external transfer. On **25 original public inputs**,
unchanged cutset expansion raises certified coverage **17/25 → 19/25**, closing
`flat30-10.cnf` and `flat30-100.cnf`. Twelve related renaming/edit controls remain
**10/12**. No baseline result is lost. Selection and policies were frozen before
evaluation; labels are audit-only. The earlier 182/182 union is unchanged.

The full measured structural-discovery workflow costs **35.17482 s versus
15.70674 s (+123.95%)**, with all four paired signs unfavorable. This includes
new-input preparation, initial discovery, checking, persistence and warm/cold
replay. There is no fallback in this comparison, so unresolved inputs stay open;
this is not total time to answer every query or a speedup over fresh solving.
Compressed evidence grows **431,796→562,509 bytes**. Defaults remain unchanged.

**Largest new coverage gap: compact capacity/injectivity structure.** Five of the
six unresolved originals are pigeonhole inputs; the sixth is `uf50-01000.cnf`.
A renamed and an edited pigeonhole control also remain open. Investigate a
CNF-derived matching/Hall-style deficiency certificate, with recognition from
clauses rather than labels and explicit tests of mixtures/edits. This is a next
hypothesis, not an implemented authority or a general SAT claim.

**Cheaper admission is supporting work.** Of 185 checked width-four obstructions,
184 have a single excluded assignment; all fifteen budget-open factors have the
same simple single-clause shape. Direct width reasoning could avoid generic
consequence enumeration, while heterogeneous exact factors could avoid requiring
every relation to have a width-four cover. Neither alone establishes a root
verdict or measured saving. **Validated source/context reuse** remains the larger
workflow cost target: acquisition/internal checks cost 15.75755 s and two cold
passes 9.95976 s. Preserve exact bindings and invalidation when sharing them.

The 35 retained frontier attempts include three unmaterialized-width rejections;
128 cofactor programs contain 13 SAT, 47 UNSAT and **68 unresolved branches**.
The independent admission audit reparses all 37 raw files, rejects 148 malformed
variants and checks all six signed bijections. All prior evidence and 82 proof
blocks are preserved. All **2,447 full and 16 focused tests pass**; manuscript
checks are recorded in `checks.json`.
Resume `experiments/results/cnf-external-cutsets/checkpoint.json`, key
`external_cutsets`. Keep original, derived and prior-panel denominators separate;
this convenience sample is not representative external coverage.

## Previous evidence: conditioned factors close the retained panel

[Checked factor conditioning](factor-conditioning.md) supplies original-source
SAT witnesses for **both remaining roots**. The independently rechecked union
covers **182/182 queries on the existing synthetic panel**, preserving all 180
prior authorities. This is finite-panel completion, not arbitrary SAT or external
coverage. One internal frontier remains unresolved beneath an already-SAT root.

Exact local covers are shared across a complete Boolean partition on at most four
graph-degree-selected variables. Prefix work is charged once and all branches
share the original remaining projection allowance. Every source, cover, branch
and old root context is checked; models lift through all earlier reductions and
conditioning edges and must satisfy the original root. SAT needs one valid branch;
UNSAT requires every branch refuted. The adapter grants new root SAT authority
only from a complete source witness.

The 48 retained cut-four branches contain **6 SAT, 17 UNSAT and 25 unresolved**.
Two-variable conditioning closes one root; four closes both. The maximum was
selected after the retained screen and is explicitly exploratory. All modes pay
for all three frontiers, including the still-open third. Complete incremental cost
is **1.39737 s**, versus **0.59316 s** for width-ten continuation: **135.58% more**,
with all eight paired signs unfavorable. Compressed new evidence grows
730→15,980 bytes. This stage includes full old-context validation/root transport;
it is not a new full-pipeline or fresh-solving comparison. Defaults stay unchanged.

**Next coverage target: generalization and economical cutset recognition.** Freeze
new graph structures and external CNFs before tuning; measure overlap, remaining
interaction and whether small useful cutsets can be found cheaply. The old panel
has reached its coverage ceiling; broader nonconstant transfer remains weak.
**Next cost targets:** selective/adaptive branch expansion and validated source
contexts, charging construction, invalidation and all required UNSAT obligations.
No saving from those policies has yet been measured.

The independent semantic audit checks **632 inputs, 2,486 branches and 18,230
cofactor assignments**, with direct truth-table agreement and discovery-disabled
cold replay. Prior evidence and 81 proof blocks are preserved; development
failures are retained. All **2,431 full and 16 focused tests pass**; manuscript
checks are recorded in `checks.json`.
Resume `experiments/results/cnf-factor-conditioning/checkpoint.json`, key
`factor_conditioning`; the new `coverage-union.json` identifies every authority.

## Previous checkpoint: exact factor-width partition and obstructions

[Exact factor clause-width classification](factor-clause-width.md) identifies the
remaining obstruction more precisely. All **244 active factors** have exact
same-variable clause covers of width at most four. Among the seventeen dense
projected relations, one needs width two, four need width three, and **twelve
provably require width four**. The negative certificates supply local model
completions, not a solver-time lower bound; auxiliaries and external context are
outside this representation restriction.

The exact covers reduce frontier primal edges **130→116, 232→203, 217→201** and
permit four more width-nine eliminations, but **no new leaf or root verdict**.
The next greedy widths are eleven, ten and ten. The incremental stage costs
**11.95% more than width-ten continuation**, with all eight signs unfavorable,
and its compressed evidence grows 730→5,438 bytes. This is a three-frontier stage
comparison, not a new full-pipeline benchmark; structural coverage remains
**180/182**, and production defaults stay unchanged.

**Next coverage target: global interaction after exact local decomposition.**
Investigate a separator or conditioning step on the coupled factor graph, with
all branch obligations and source/model recomposition checked. Additional
clause-width enumeration on these unchanged factors cannot improve their already
complete covers. These current-order widths are not optimal-decomposition lower
bounds. Contextual or auxiliary representations remain separate possibilities.
**Next cost target:** validated source/intermediate reuse, still supported by the
previous full-pipeline profile's 5,449 normalizations and 6,127 restrictions.

The independent exhaustive audit checks all **65,536 four-variable relations**:
43,146 width-three covers and 22,390 obstructions. This partitions explicit local
tables; constructing those tables from arbitrary succinct CNFs and solving their
global conjunction remain separate obligations. All **2,415 full and 14 focused
tests pass**. Prior evidence and 80 proof blocks remain unchanged; unsuccessful
static/dynamic factorization screens are retained. Resume
`experiments/results/cnf-factor-refinement/checkpoint.json`, key
`factor_clause_width`.

## Previous checkpoint: ephemeral verified operator reuse

[Verified operator reuse](verified-operator-reuse.md) reduces complete cost
**10.37% versus unchanged checking**, with all five paired signs favorable.
Within-query reuse saves **6.91%**; sharing across a pass saves another **3.72%**.
All certificates and fallback evidence remain identical, preserving **180/182**
structural verdicts. The pipeline remains **38.78% more costly than fresh** on
this unchanged synthetic panel; production defaults stay unchanged. The uncached
new checker regresses 0.63% on average with mixed signs.

Every occurrence still checks source binding, complete incident factors, encoding,
coordinate mapping, verdict and source witness. An empty bounded bank skips only
a local row loop whose complete immutable input/pivot/output/choice description
has already passed that loop. Each warm/cold phase starts empty. One cold pass
avoids **39.51% of verification table probes**, retaining 1,325 keys accounting
for 1,797,404 key/value bytes, excluding dictionary infrastructure. This realizes
the earlier reuse opportunity; its work fraction is not a runtime fraction.

**Next coverage target:** the two coupled-factor roots `d-d-d-j06` and `d-d-k09`.
The three retained width-ten frontiers and failed width-ten diagnostic remain
unchanged. Investigate exact factor recognition, separators or conditioning with
recomposition. **Next cost target:** validated source/intermediate contexts.
Discovery/internal checking (**4.50848 s**) and cold replay (**3.81622 s**) still
dominate. A separate instrumented replay invokes normalization 5,449 times and
restriction 6,127 times; its overlapping profiled times are diagnostic, not
measured potential savings. Charge binding, construction and invalidation.

Broader transfer remains a major gap: only **six nonconstant operator occurrences
(144 probes)** match an earlier owner with a different stored family label after
excluding repeated sources. These are generator/frontier labels, not disjoint
semantic SAT classes; most gains are repeated checking within the retained panel.
There is no new coverage, whole-residual sharing or unrestricted-SAT result.
An independent audit checks 1,303 partial programs and rejects 6,515 mutations.
Prior evidence and 79 proof blocks are preserved; the initial failed test fixture
and its correction are retained. Resume
`experiments/results/cnf-verified-operators/checkpoint.json`, key
`verified_operators`. All **2,401 full and 33 focused tests pass**.

## Previous checkpoint: checked projection continuation

[Selective width expansion](selective-width-discovery.md) raises structural
coverage **177/182 to 180/182** after two checked pair rounds, with no feedback
verdict lost. It closes three previously exposed SAT roots; the 18 new unique
controls and four repeats were already covered. Complete cost rises **2.78%
versus feedback** and **54.91% versus fresh**; defaults stay unchanged. One-round
widening adds the same three roots but loses four feedback verdicts. Prefix reuse
avoids 104 repeated projections but is **0.055% slower than restart on average**,
with three favorable and three unfavorable pairs. Full checking offsets the
avoided projection work; there is no reliable runtime win or new nonconstant
merging across leaves.

**Next cost target: reuse verified exact operators within a checking pass.**
Discovery including internal checks (**5.15454 s**) and cold replay (**4.17227 s**)
remain the largest phases. A separate census finds **39.51% of bucket-verification
table probes** repeat exact local operators; within-query repetition accounts for
14.71%. Among distinct normalized sources, cross-source matches account for
15.90% of their probes. These are potential work savings, not runtime savings or
proof of transfer across categories. Charge first-use checking, exact occurrence
bindings, key construction, lookup, memory and invalidation before adopting reuse.

**Next coverage target: the coupled factor frontier.** Two SAT roots remain,
with three width-ten boundaries in the current factorization/order. A separately
checked width-ten continuation certifies none and stops at widths eleven/twelve.
These are not lower bounds on optimal decompositions. Investigate factor
recognition, separators or conditioning with exact recomposition; blind uniform
width growth has no new verdict in this screen. Broader external coverage,
recognition across categories and efficient unrestricted SAT remain open.

All **2,385 full and 30 focused tests pass**. The initial concurrent suite's
existing 100 ms resource-test timeout is retained; that test and the full suite
pass in isolation without changed deadlines or assertions. All 236 previous
manifests, 60,847 artifact entries, 1,294 scientific sources and 78 proof blocks
are preserved. Resume
`experiments/results/cnf-selective-width-buckets/checkpoint.json`, key
`selective_width_buckets`.

## Previous checkpoint: bounded feedback and selective elimination

[Bounded checked pair feedback](pair-feedback-discovery.md) raises structural
coverage **151/160 to 155/160**, versus **152/160** from a single batch with the
same maximum pair budget. It certifies three exposed SAT roots and one new UNSAT
root, with no baseline losses. Complete cost rises **3.38% versus current**,
**2.70% versus the larger batch**, and **34.72% versus fresh**, with all four
paired signs unfavorable. Defaults stay unchanged. Fewer pairs than the larger
control do not offset extra preparation and checking; no new nonconstant
cross-leaf sharing is demonstrated.

Five unique SAT roots remain, with six width-nine leaves. A third pair batch adds
81 clauses but certifies none; repeated width-eight preparation also certifies
none. Width-nine buckets certify three diagnostic leaves, **already available
after one pair batch**. Next compare selective width-nine elimination after
one-round closure with a two-round control, including full root transport and
complete costs. These leaf screens add no measured root verdicts. All 356 single
assumptions were probed; one failure remains, so the earlier zero-failure claim
does not apply to the changed frontier.

Discovery including internal checking (**3.81341 s**) and cold replay
(**3.31908 s**) remain the largest phases. Reusing validated intermediate maps
within checking is a concrete cost target; its avoidable fraction remains
unmeasured. All **2,368 full and 30 focused tests pass**; prior results and 77
proof blocks are preserved. Resume
`experiments/results/cnf-pair-feedback-buckets/checkpoint.json`. Efficient
arbitrary-SAT coverage, broader transfer and external validation remain open.

## Previous checkpoint: paired consequences and the feedback frontier

[Checked pair consequences](joint-probe-discovery.md) increase structural coverage
**124/138 to 131/138**, closing two exposed unique roots (SAT and UNSAT) plus a
repeat, and raising new unique coverage **15/24 to 19/24**. Width nine stays at
124/138. Shared prefixes avoid **6,935 state rebuilds** and about **42% of pair
occurrence visits**; pooled local evidence is **27.93% smaller** than explicit
prefix duplication. The complete cost is **11.62% below width nine**, but only
0.98% below base and 0.72% below pair restart with **mixed paired signs**. It remains
29.85% above fresh. No reliable baseline/restart runtime win or new nonconstant
cross-leaf sharing is established; defaults stay unchanged.

Seven unique roots remain, all with SAT labels. Their eight width-9–11 final
leaves have no ordinary binary/forced structure and no failure in **606 complete
single probes**. A separate next-pair diagnostic produces **177 new clauses** and
three checked SAT leaf terminals, excluded from measured root coverage. **Next:
bounded checked clause feedback versus a larger one-shot pair allowance**, with
exact changing-source bindings and whole-root transport. Discovery including
internal checks (**2.86258 s**) and cold replay (**2.62962 s**) dominate; validated
source/intermediate reuse and repeated terminal checking remain the cost targets.
Unrestricted efficient coverage and recomposition remain open. All **2,355 full
and 55 focused tests pass**, and prior evidence/proofs are preserved. Resume
`experiments/results/cnf-joint-probe-buckets/checkpoint.json`.

## Previous checkpoint: selective continuation and its reuse regression

[Selective capped-probe continuation](selective-probe-discovery.md) raises
structural coverage **97/110 to 105/110**, versus **103/110** with uniform doubling.
It closes all four exposed frontier misses, raises new unique coverage **17/24 to
20/24**, and loses no baseline verdict. Complete cost is **13.28% below base** and
**2.61% below uniform doubling**, but **31.61% above fresh**. Defaults stay unchanged.
The narrower cursor reuse avoids 710 repeated probes and 20 index builds but is
**0.63% slower than selective restart in all five pairs**; retain that negative
result. No new nonconstant residual sharing is observed.

Four unique roots plus one repeat remain. Their seven width-9–12 leaves have no
unit, disconnected component, binary conflict, forcing or alias; **598 complete
single-literal probes find no failure**. Next investigate stronger joint binary
consequences in this residual pipeline, comparing charged acquisition and exact
recomposition with bounded width/ordering or conditioning controls. More of the
same single-literal probing has no opportunity on these unchanged leaves.
Cold replay (**1.73346 s**) and discovery including internal checking
(**1.59018 s**) remain the largest costs: reuse validated normalization/intermediate
state within one replay. Efficient arbitrary-SAT coverage remains open.
All **2,338 full and 62 focused tests pass**; prior evidence and proofs are
preserved. Resume `experiments/results/cnf-selective-probes/checkpoint.json`.

## Previous checkpoint: source-checked relations after probing

[Post-probe signed substitution](probe-relation-discovery.md) certifies the last
exposed root within width eight and all 76 matched queries. It is 6.70% cheaper
than width nine, but 1.69% slower on average than probe-only and 1.66 times fresh;
production defaults remain unchanged. All **2,323 full and 47 focused tests pass**.
Prior scientific files and 74 proof blocks are unchanged. Resume
`experiments/results/cnf-probe-relations/checkpoint.json`.

The new post-hoc census retains four unresolved roots among six larger formulas.
Four of eight unknown leaves expose thirteen failed assumptions after the probe
quota stops acquisition; no further equivalence block is found. Next compare
selective probe continuation against a larger allowance with exact source/index
lifetimes. Discovery and cold checking remain the largest costs; reuse verified
normalization/intermediates before assuming extra preprocessing pays. Finite-panel
completion is not an efficient partition of arbitrary SAT.

## Previous checkpoint: full-CNF failed assumptions and shared probe indexes

[Checked full-CNF probing](probe-bucket-discovery.md) closes **19/20** exposed
structural gaps and increases new unique coverage **23/24 to 24/24**; all four
repeats remain covered. The 47/48 structural answers cost **37.23% less** than
repeated binary closure, still **1.67 times fresh**. Indexed traversal and shared
setup save **12.89%** versus repeated scans. Defaults stay unchanged. All **2,312
full and 36 focused tests pass**; previous scientific sources and 73 proofs remain
intact. Resume `experiments/results/cnf-probe-buckets/checkpoint.json`.

The last SAT source has two width-nine unknown leaves, no remaining failed
single assumptions and one new signed-equivalence block. Test composition of
relation substitution after full-CNF consequences, with bounded ordering/width
controls and new nonfolding inputs. Discovery and cold replay dominate; repeated
normalization and certificate reconstruction are the next cost-reuse gap.
The frozen controls' foldable-wide limitation is retained, and neither empirical
coverage nor local propagation bounds imply efficient arbitrary SAT.

## Previous checkpoint: bounded repeated binary forcing

[Repeated forcing](iterated-forcing-discovery.md) certifies six of 24 exposed
misses and lowers matched complete cost 18.23% versus one pass, still 2.56 times
fresh. New unique coverage stays 22/24; prior results and all 72 proofs remain
preserved. All 2,300 full and 34 focused tests pass. Resume
`experiments/results/cnf-iterated-forcing/checkpoint.json`.

The next gap is wider-clause propagation: binary forcing is exhausted on the
30 remaining unknown nodes, but a separately checked full-CNF probe census finds
failed assumptions in all thirty. Integrate bounded failed-literal closure with
exact round transport and complete costs; leaf diagnostics do not supply root
certificates or an unrestricted SAT bound. The new record retains the single-pass
misses, increased path evidence and repeated-query gap.


Previous expansion checkpoint (27 November, one-way forcing buckets):
[Checked binary forcing](forcing-bucket-discovery.md) closes 7/27 exposed misses
and raises new unique coverage 17/24 to 20/24. Separate-path complete cost improves
12.41% versus the wrapped relation policy, but remains about 2.88 times fresh.
Pooling support edges cuts checks 38% without a convincing runtime gain and
increases compact forcing payload 13.18%; the negative result is retained.
Twenty-four unique remaining sources have 43 wide nodes. New forcing appears in
13 nodes after earlier unit consequences; next test bounded repeated closure,
without treating six diagnostic leaf conflicts as new root verdicts. Resume
`experiments/results/cnf-forcing-buckets/checkpoint.json`. All 2,288 full and 30
focused tests pass. Prior 229 manifests, 41,034 artifact entries, 1,258 sources
and 71 proofs remain unchanged; one restricted proof is added. Defaults stay unchanged.

Previous expansion checkpoint (27 November, binary relation buckets):
[Checked binary conflicts and signed equivalence substitution](relation-bucket-discovery.md)
certify 2/21 exposed misses. Frozen unique coverage stays 16/24; all repeats are
covered. Total cost falls 10.57% versus shared units, but remains 3.09 times fresh
solving. No defaults change. Twenty-seven unique remaining sources retain fifty
wide nodes with only one more equivalence block. Checked one-way forcing paths
appear in 32/50 nodes and expose five conflicts after units: integrate those next,
without counting diagnostic leaves as root verdicts. Resume
`experiments/results/cnf-relation-buckets/checkpoint.json`. All 2,276 full and 26
focused tests pass. Previous 228 manifests, 39,818 artifact entries, 1,253 sources
and 70 proofs remain intact; one restricted proof is added. A substitution-cleanup
counterexample and the repaired draft's failed tests are preserved.

Previous expansion checkpoint (27 November, closed conditioned buckets):
[Unit closure with separate incoming transport](closed-bucket-discovery.md)
closes 6/20 exposed misses and raises unique-panel coverage 12/24 to 17/24.
Sharing closed residuals cuts 250 bucket calls to 219 and complete cost 4.22%
versus a tree; closure plus sharing improves 9.17% over the wrapped root-only
policy. The pipeline remains 3.34 times fresh solving; no default changes.
Twenty-one unique sources retain 45 unknown nodes without units or component
splits. A post-hoc checked diagnostic finds three binary contradictions and
fifteen equivalence blocks: next test binary closure with exact model transport,
without counting leaf diagnostics as root verdicts. Resume
`experiments/results/cnf-closed-buckets/checkpoint.json`. All 2,266 full and 24
focused tests pass; 227 prior manifests, 38,630 artifact entries, 1,248 sources
and 69 proofs are preserved. One restricted sharing proof is added.

Previous expansion checkpoint (27 November, symbolic bucket preprocessing):
[Exact complementary-clause folding](symbolic-bucket-preprocessing.md) closes
2/12 exposed misses and raises new unique coverage 11/24 to 14/24; units alone
reach 13/24 and are 2.95% faster than folding. Both remain slower than fresh
solving. Root-only preprocessing leaves 74 unresolved cofactors; a post-hoc
unit diagnostic finds 28 contradictions. Next test checked unit closure after
conditioning, without counting those diagnostics as root verdicts. Resume
`experiments/results/cnf-symbolic-buckets/checkpoint.json`. All 226 earlier
manifests, 37,635 artifacts, 1,243 sources and 68 proofs are preserved; one
restricted proof and a separate experimental JSON authority are added.

Previous expansion checkpoint (27 November, conditioned buckets):
[Conditioning before complete buckets](conditioned-bucket-discovery.md) closes
6/10 preceding acquisition misses and raises new unique synthetic coverage
11/24 to 16/24. Exact residual sharing reduces 158 calls to 149 and complete cost
3.43%, but remains 4.59 times as costly as fresh solving. Twelve unique sources
still exceed the width cap after the two-level partition. Next test cheap exact
small-factor combinations before deeper branching. Resume
`experiments/results/cnf-conditioned-buckets/checkpoint.json`. Previous 225
manifests, 36,689 artifacts, 1,238 sources and 67 proofs remain intact; a separate
JSON authority and one restricted proof are added. No default changes.

Previous expansion checkpoint (27 November, semantic bucket support):
[Exact non-affine table compression](semantic-bucket-support.md) reduces stored
output rows 35.26% and certificate bytes 12.51%, retaining full-boundary witness
choices. It covers the same 2/6 exposed misses and 18/24 new unique constructions
as raw bucket elimination; the existing fallback solves all cases. Complete cost
remains 50.53% above fresh, and operator caching adds storage. The ten remaining
misses exceed the width-eight cap before the first elimination. Next test exact
small factor combinations or conditioning before forming whole buckets. Resume
`experiments/results/cnf-semantic-buckets/checkpoint.json`. Prior 224 manifests,
35,821 artifacts, 1,233 sources and 66 proofs are unchanged; one restricted proof
and a separate experimental JSON authority are added. Defaults remain unchanged.

Previous expansion checkpoint (27 November, affine boundary completion):
[Exact projected-image completion](affine-boundary-completion.md) replaces total
free dimension with the rank visible to leftover clauses. It covers 18/24 unique
synthetic controls directly versus 14/24 for the old gate; the existing fallback
already decides all inputs. Complete matched time falls 19.66% against fresh,
and raw record/proof bytes fall 30.00%. Full basis retention, normalization,
projection, misses and cold verification remain charged. The previous five
feedback gaps were already affine-covered, not new solver-completeness gaps.
The remaining six distinct acquisition misses have no complete parity halves;
non-affine boundary discovery is the next coverage target. Resume
`experiments/results/cnf-affine-boundary/checkpoint.json`. Earlier 223 manifests,
35,068 artifacts, 1,228 sources and 65 proofs remain unchanged; a separate JSON
authority and one restricted completeness proof are added. No default changes.

Previous expansion checkpoint (27 November, exact cofactor feedback DAG):
[Bounded conditioning with shared residuals](feedback-cofactor-dag.md) closes
5/6 exposed fresh gaps. The second panel rises from 2/10 to 6/10 UNSAT refutations,
or 2/7 to 4/7 excluding three full-cube controls. Exact residual-plus-depth reuse
cuts calls 170 → 147, certificate bytes 14.67% and complete matched time 4.86%.
Native graphs remain identical; the memoized workflow still costs 24.85 times fresh.
Five bounded-feedback gaps remain, mainly parity interactions. Next compare
non-unit affine/boundary descriptions with fully charged discovery and conversion.
All 2,226 tests and 26 focused tests pass. Resume
`experiments/results/cnf-feedback-cofactor-dag/checkpoint.json`. All old scientific
sources, 222 manifests, 34,259 artifacts and 64 proof blocks remain unchanged;
one restricted full-cube call-count proof is added, without an arbitrary-SAT claim.

Previous expansion checkpoint (27 November, direct fresh-source feedback):
[A source-only compiler](fresh-seed-feedback.md) eliminates historical B13 input
requirements for checked feedback chains. Both cold readers validate eight
refutations on 36 fresh generated CNFs, including one two-level case. Independent
truth gives 22 SAT and 14 UNSAT cases; six UNSAT cases remain open to feedback,
while the existing fallback solves all 36. This closes an adapter restriction,
not unrestricted structural coverage. Full workflows cost 0.08072 s fresh,
0.12040 s prepared and 0.44621 s online; preserve this regression. Next investigate
non-unit interactions on the six fresh gaps and reuse checked preparation only
with exact ownership/invalidation. All 2,218 tests and 27 focused tests pass.
Resume `experiments/results/cnf-fresh-seed-feedback/checkpoint.json`; previous
sources, 221 manifests, 33,634 artifacts and 64 proof blocks remain unchanged.

Previous expansion checkpoint (26 November, repeated cross-pivot feedback):
[Two checked feedback levels](strengthened-cross-pivot.md) certify the final
`(61,50)` snapshot: **246/246 retained frontier snapshots covered**. Exact resume
avoids 6,078 probes and saves 29.01% with the first level already available.
Native conversion exhausts its shortcut budget (626 records, 3.017 s); a larger
ceiling gives 170 records and 1.043 s, still slower than 0.940 s fresh. All costs,
controls and previous proofs remain. All 2,210 tests and 27 focused tests pass.
Resume `experiments/results/cnf-strengthened-cross-pivot/checkpoint.json`; its
frontier is empty. Next broaden held-out discovery and decouple the generic kernel
from historical B13 provenance. The rule's retained four-variable UNSAT fixed
point demonstrates that this finite completion does not cover arbitrary SAT.

Previous expansion checkpoint (26 November, cross-pivot feedback):
[Joining saved failed-side implications](cross-pivot-feedback.md) certifies two
more original snapshots: **245/246 covered, one open**. Compact proof summaries
retain 7/9 and 3/10 branch proofs; both cold readers pass. Reuse costs 0.155 s versus
0.553 s from histories, with 77.35% fewer input bytes and 24.07% lower peak RSS.
Preparation costs 0.802 s, repaid after three measured replays. Native workflows
save 16.40% time and 31.25% raw bytes versus fresh, excluding acquisition; the full
summary route regresses on one case. All 2,200 tests and 25 focused tests pass.
Resume `experiments/results/cnf-cross-pivot-feedback/checkpoint.json`. Next search
the remaining `(61,50)` bank strengthened by its two checked units (334 → 314
clauses). Old sources, artifacts, native results and 64 proof blocks are unchanged.

Previous expansion checkpoint (26 November, conditioned saturation):
[Checked variable partitions](conditioned-saturation.md) certify nine more original
snapshots through both cold readers: **243/246 covered, three open**. Combining
one-sided implications across pivots already gives two further augmented-bank
contradictions, but source-only reconstruction is pending; those cases remain open.
The third bank shrinks 334 → 314 clauses. Next reconstruct the joint implications.
Discovery/checking takes 1.915 s versus 0.396 s flat at larger search allowances;
resume is 5.95% slower. Native conversion saves 7.41% aggregate time and 23.74%
bytes against fresh, with four regressions and additional discovery costs. All
2,191 tests and 24 focused tests pass. Resume
`experiments/results/cnf-conditioned-saturation/checkpoint.json`. Prior sources,
certificates, artifacts and 64 manuscript proof blocks remain unchanged.

Previous expansion checkpoint (26 November, causal saturation slicing):
[Backward dependency slicing](sliced-saturation.md) cuts `(37,39)`'s native graph
5,587 → 76 records and complete reconstruction 52.719 → 0.797 s, with the same
shortcut allowance. Both cold readers pass. An eightfold-budget control reaches
146 records; fresh solving remains cheaper. On the earlier case, raw bytes fall
9.18% but runtime increases 1.11%. Coverage and twelve frontier rows are unchanged
at **234/246**. All 2,183 full tests and 22 focused tests pass. Resume
`experiments/results/cnf-sliced-saturation/checkpoint.json`. Next return to stronger
interactions/decomposition on the remaining fixed points; preserve all regressions.

Previous expansion checkpoint (26 November, generic checked saturation):
[Reusable failed-literal rounds](probe-saturation.md) close `(37,39)` with fourteen
new failed assumptions and source-only certification: **234/246, twelve open**.
The generic schema supports interrupted rounds, exact checked reuse and a bound
of at most one productive round per seed variable. Fixed points remain unresolved.
Avoiding 270 probes is 1.65% slower after checking; direct native reconstruction
costs 67.79 times fresh runtime and 50.21 times its record bytes. Preserve these
regressions and investigate stronger interactions on the twelve fixed points.
All 2,175 full tests and 21 focused tests pass. Resume
`experiments/results/cnf-probe-saturation/checkpoint.json`; previous artifacts and
64 manuscript proof blocks remain unchanged.

Previous expansion checkpoint (26 November, native B13 feedback):
[Source-only reconstruction](b13-native-feedback.md) certifies `(67,63)` with both
cold readers: coverage **233/246**, thirteen open. Direct reconstruction is 32.83%
slower and stores 32.49% more bytes than fresh solving on this case; the disabled
shortcut arm's 2,507 records expose native proof expansion as a remaining cost.
Preserve the regression and `(37,39)`'s new closure. Resume
`experiments/results/cnf-b13-native-feedback/checkpoint.json`; earlier archives,
tables and frontier fields are unchanged. All 2,167 tests and 31 focused tests pass.

Previous expansion checkpoint (26 November, strengthened B13 histories):
[Longer checked histories in the existing B13 schema](b13-strengthened-histories.md)
find 14 new failed assumptions. `(37,39)` shrinks 545 → 534 residual clauses;
`(67,63)` yields a checked 34-step augmented-bank contradiction. Source-only native
reconstruction is now the highest-priority gap, so native coverage remains 232/246.
Strengthening costs 4.37% more than old continuation; records grow 28.95%. All 2,161
tests pass. Resume `experiments/results/cnf-b13-strengthened-histories/checkpoint.json`.
The initial incorrect expectation of open feedback is retained with its correction.

Previous expansion checkpoint (26 November, independent cold batch):
[Cold validation batching](b12-cold-batch.md) reduces checking 27% and complete
matched replay time 11–12%, keeping every snapshot's proof and cursor checks.
Cold preparation occurs 14 rather than 18 times per ordering. All saved results,
search counters and frontier bindings remain unchanged; coverage stays 232/246.
RSS slightly increases and result bytes are unchanged. All 2,154 tests pass.
Resume `experiments/results/cnf-b12-cold-batch/checkpoint.json`. Next compare the
two strengthened closures with B13 schedules; no phase now dominates runtime.

Previous expansion checkpoint (26 November, batched B12 continuation):
[Batched continuation](b12-continuation-batch.md) shares one checked preparation
across bounded rounds, saving 25% discovery and 9–10% total time. Exact per-round
results and search work are unchanged. Two new failures force four values across
`(37,39)` and `(67,63)`, shrinking their residuals to 545 and 330 clauses. Both
B12 policies are now exhausted on all fourteen fixed banks; coverage stays 232/246.
Cold checking is the next measured cost at about 40%; stronger residuals and
retained B13 schedules are the next coverage comparison. All 2,145 tests pass.
Resume `experiments/results/cnf-b12-continuation-batch/checkpoint.json`.

Previous expansion checkpoint (26 November, B13 versus continued B12):
[B13 comparison](b13-probe-cursor.md) retains a negative expansion result: no new
failure versus two from continued source-order B12. Their closure forces 116=true
and 119=true at `(67,63)`, reducing 358 clauses to 347. Coverage remains 232/246.
Twelve orders are exhausted; `(37,39)` and `(67,63)` remain unfinished. A balanced
follow-up after an unstable initial trial puts B13 7.91% above source continuation
in total cost; reuse saves only 1.86% versus matched fresh B13. All 2,136 tests pass.
Resume `experiments/results/cnf-b13-probe-cursor/checkpoint.json`; preserve productive
continuations and investigate stronger interactions for the exhausted cases.

Previous expansion checkpoint (26 November, shared B10 preparation inside B12):
[Shared B12 checking](shared-b12-preparation.md) cuts matched complete time
39.24% for source order and 39.65% for untested-first, with exact result, provenance
and search-counter equality. Every distinct upper history remains independently
checked. Coverage stays 232/246; result bytes and peak memory do not materially
improve. All 2,127 tests pass. Resume
`experiments/results/cnf-shared-b12-preparation/checkpoint.json`. Next use the
combined `(67,63)` closure while comparing continuation of both saved orders.

Previous expansion checkpoint (26 November, B12 progress-guided ordering):
[B12 ordering](b12-progress-order.md) finds `83` at `(67,63)` while source order
finds `-68`. The combined closure gains two assignments; coverage stays 232/246.
The heuristic reaches more previously unrecorded assumptions but does not dominate
source order or improve total runtime materially. B12 is 66.01% costlier than B11
continuation; repeated common-history checking is the next cost target. Both
orders, the redundant B11 implication and all regressions are retained. All 2,118
tests pass. Resume `experiments/results/cnf-b12-progress-order/checkpoint.json`.

Previous expansion checkpoint (26 November, complementary B11/B10 discovery):
[B11 probing](b11-probe-cursor.md) and continued B10 find three new failed
assumptions whose combined closure forces four assignments across two open cases.
Coverage remains 232/246. Reuse avoids 1,882 probes but saves 2.15% matched total
time and costs 8.67% more than B10 continuation. Preserve both histories; test
scheduling from older unfinished progress on the new bank without trusting old
open completions as proofs. All 2,109 tests and prior evidence audits pass.
Resume `experiments/results/cnf-b11-probe-cursor/checkpoint.json`.

Previous expansion checkpoint (26 November, shared B8 checking within B10):
[Shared B10 preparation](shared-b10-preparation.md) reduces complete matched
replay time 39.30%, discovery 49.61% and independent checking 49.69%. All results,
origins and search counters match the frozen route. Coverage remains 232/246;
no peak-memory or serialized-space saving is established. All 2,100 tests pass.
Resume `experiments/results/cnf-shared-b10-preparation/checkpoint.json`, which
retains the unchanged B10 frontier. Next: probe the two strengthened open banks.

Previous expansion checkpoint (26 November, combined B10 refutations):
[Joint B10 probing](b10-probe-cursor.md) certifies `(28,18)` and `(40,0)`, reaching
232/246 with fourteen open. B9 continuation already closes the latter; B10 adds
the former under the measured budget. New failures strengthen `(37,39)` and
`(67,63)`. Reuse saves 1,946 probes but just 2.82% matched total time; repeated
history preparation dominates and B10 costs 68.01% more than B9 continuation.
Direct native reconstruction regresses at `(28,18)`; on `(40,0)` it completes
where fresh solving stops at 256 nodes. The stopped trial and corrected harness
are preserved. All 2,091 tests, six native archive/root audits and prior ledgers
pass. Resume `experiments/results/cnf-b10-probe-cursor/checkpoint.json`.

Previous expansion checkpoint (26 November, complementary B8/B9 discovery):
[B9 frontier reuse](b9-probe-cursor.md) avoids 2,198 probes, improving matched
complete census time 3.26%. Continuing B8 remains 7.74% cheaper and finds four
failures absent from B9; B9 finds two absent from B8. Retaining both checked sets
forces 17 additional assignments across four cases, without a new refutation.
Coverage stays 230/246. The 10,429-byte overlay references prior history and both
result sets; all dependencies remain. All 2,082 tests pass. Resume
`experiments/results/cnf-b9-probe-cursor/checkpoint.json`; next compose both proof
sets with original-bank provenance and probe the four changed closures. Repeated
boundary checks, native proof expansion and unrestricted bounds remain open.

Previous expansion checkpoint (26 November, local source context reuse):
[Prepared reconstruction](prepared-prefix-replay.md) improves source reconstruction
45.00% and complete measured workflow time 23.41%, with identical hints, states,
results and downstream counters. All sixteen prefixes are empty; the profile
identified per-hint canonicalization. Novel/repeated-hint scaling improves, but
zero/single-hint and missing-support controls regress. Preserve those limits.
Coverage, native certificates and the open export are unchanged. Resume
`experiments/results/cnf-prepared-prefix-replay/checkpoint.json`; next investigate
boundary rechecks, cheap context admission and the retained coverage targets.

Previous expansion checkpoint (26 November, shared common provenance):
[One common preparation per independent call](shared-joint-preparation.md) reduces
complete replay time 22.07%, with identical prepared banks, search counters and
results on all sixteen current cases. Discovery and cold checking improve 38.30%
and 38.70%; memory and result size do not materially change. No new coverage or
native record. The next cost target is source-prefix reconstruction (50.89% of
shared total). Resume `experiments/results/cnf-shared-joint-preparation/checkpoint.json`;
the existing frontier, native regression and all prior proof/artifact ledgers remain.

Previous expansion checkpoint (26 November, probing the combined bank):
[Joint probe cursors and original-bank feedback](joint-probe-cursor.md) add the
native refutation `(28,19)`, reaching 230/246 with 16 open. Exact reuse saves
1,878 probes, but complete census time improves only 1.49%. The positive native
certificate is 67.29% slower and 52.21% larger than fresh solving; preserve this
regression. The open export grows 4.91%. Next: stronger `(28,18)`, unfinished
orders, common-prefix checking/reconstruction, and equivalence/source-support
reuse. Resume `experiments/results/cnf-joint-probe-cursor/checkpoint.json`.
All earlier proofs, artifacts, tables and reference bindings remain intact.

Previous expansion checkpoint (26 November, original-bank B6/B7 composition):
[Joint failure feedback](joint-cursor-feedback.md) adds the source-only native
refutation `(37,40)`, reaching 229/246 sampled recognition with 17 open. B7-only
feedback also refutes it; joint reasons reduce the certificate to 35 records
versus 51 B7-only and 77 fresh. Four open closures gain eight assignments and are
the next search targets. Both proof histories retain their original banks.
All 2,048 tests, four native archive/root audits and prior ledgers/proofs pass.
Resume `experiments/results/cnf-joint-cursor-feedback/checkpoint.json` and
`joint_cursor_feedback.remaining-closures`. Repeated prefix checking, source
support selection and unrestricted/lifetime-space bounds remain open.

Previous expansion checkpoint (26 November, shared B7 preparation and empty stages):
[One checked expansion](fused-b7-expansion.md) reduces expansion time 44.70% and
complete measured time 16.97%, with the same results on all eighteen measured
inputs. Eleven empty failure sets reuse the physical bank, closure and residual
view. Final cold validation remains independent. No new frontier or recognition;
retain the 30 B6 and 15 B7 failures for combined reasoning under original-bank
bindings. Source reconstruction is now 52.85% of measured runtime. All 2,039 tests
and prior source/artifact/proof ledgers pass. Resume
`experiments/results/cnf-fused-b7-expansion/checkpoint.json`; the open export is
referenced unchanged. Native B7 compilation and unrestricted bounds remain open.

Previous expansion checkpoint (26 November, B7 discovery and exact history reuse):
[B7 failure frontiers](b7-probe-cursor.md). Composition forces 26 new assignments;
B7 probing retains 15 failures across five cases, without a new refutation.
Reuse avoids 1,788 probes but improves matched complete time only 1.05%; adding
the layer costs 26.98% more than continuing B6. Preserve the 30-failure B6
comparison history too. Next: combine both proof sets with exact original-bank
checks, avoid empty layers and share composition/search preparation. All 2,030
tests and prior ledgers/proofs pass. Resume
`experiments/results/cnf-b7-probe-cursor/checkpoint.json`. No B7 native compiler,
new authority records, production defaults or unrestricted bounds are claimed.

Previous expansion checkpoint (26 November, checked cold B6 recovery):
[Share validated preparation](checked-b6-restore.md). Full-result checking and
session construction now reuse the same checked state, reducing complete measured
time 16.47% with identical continuations. No new refutation; 25 failures in seven
cases remain for composition and fresh B7 probing. Thirteen current orders are
exhausted. All 2,021 tests, prior source/artifact ledgers and 64 proof blocks pass.
No native records or production defaults change. Resume
`experiments/results/cnf-checked-b6-restore/checkpoint.json`, using appended
`b6_checked_restore_cursor`. Source-prefix reconstruction is the next major cost;
retain the unsuccessful 24-failure composition diagnostic.

Previous expansion checkpoint (26 November, owned B6 preparation):
[Reuse validated state across chunks](prepared-b6-search.md). Complete measured
incremental-search time falls 44.32% against ordinary chunk calls; single-pass
search remains faster, with no cold or peak-memory gain. Exact continuation adds
15 failures for 24 retained in seven cases, without a new refutation. Sampled
coverage remains 228/246 and 18 open; ten current orders are exhausted. All 2,013
tests, source/artifact ledgers and 64 manuscript proof blocks pass. No new native
records or production defaults change. Resume
`experiments/results/cnf-prepared-b6-search/checkpoint.json`, using appended
`b6_prepared_cursor` histories. Next compose all24 failures and investigate
checked cold-preparation handoff; retain the unsuccessful nine-failure diagnostic.

Previous expansion checkpoint (25 November, B6 frontier continuation):
[Advance exact B6 histories](b6-probe-cursor.md). One additional native refutation
reaches 228/246 sampled recognition with 18 open. Exact transfer avoids 1,472
repeated assumptions, but total census time barely changes and retained open
state grows 9.03%. Compose nine failures in six cases next; six other exhausted
literal orders need stronger interactions if feedback leaves them unchanged.
All 2,005 tests, two unique native archive/root audits, prior source/artifact
ledgers and 64 manuscript proof blocks pass. Resume
`experiments/results/cnf-b6-probe-cursor/checkpoint.json`. Cumulative tables and
production defaults remain unchanged; new archives are supplemental.

Previous expansion checkpoint (25 November, B5-failure composition):
[Compose the retained consequences](b5-cursor-feedback.md). One additional native
refutation reaches 227/246 sampled recognition with 19 open. Seven open closures
gain 22 assignments; probe these fresh, especially `(37,0)`, and preserve later
frontiers on unchanged banks. All 1,995 tests, three unique native archive/root
audits, previous source/artifact ledgers and 64 manuscript proof blocks pass.
Direct certification improves the gained root; complete discovery is slightly
slower and repeated preparation remains dominant. Resume
`experiments/results/cnf-b5-cursor-feedback/checkpoint.json`. All older histories
and cumulative authority tables remain unchanged; archives are supplemental.

Previous expansion checkpoint (25 November, exact B5 frontier transfer):
[Reuse histories only across equal banks](b5-probe-cursor.md). Five new native
refutations reach 226/246 sampled recognition, leaving 20 unresolved. Sixteen
exact bank/closure matches avoid 1,024 repeated assumptions while matching the
fresh extended frontier; complete census time improves only 1.48%. All 1,987
tests, ten unique archive/root pairs and prior source/artifact ledgers pass;
64 manuscript proof blocks remain unchanged. Next compose 26 checked failures
in eight open cases and investigate later candidates/interaction in twelve
others. Resume `experiments/results/cnf-b5-probe-cursor/checkpoint.json`.
No production default or cumulative authority table changes.

Previous expansion checkpoint (25 November, B4-failure composition):
[Compose the retained B4 consequences](b4-cursor-feedback.md). Four new native
roots pass both readers without new assumed probes, reaching 221/246 sampled
recognition with 25 unresolved. Direct-unit certificates improve all four
positive cases versus fresh solving, but prior acquisition and discovery are
additional. All 1,977 tests pass; earlier source/artifact ledgers and 64 proof
blocks remain unchanged. Next probe the nine stronger B5 closures, which gain
85 assignments, and advance the preserved frontier for sixteen unchanged cases.
Repeated reconstruction remains the main census cost. Resume
`experiments/results/cnf-b4-cursor-feedback/checkpoint.json`. Production defaults
and cumulative authority tables remain unchanged; new archives are supplemental.

Previous expansion checkpoint (25 November, fresh B4 cursor):
[Probe the strengthened banks](b4-probe-cursor.md). Fresh exact B4 bindings expose
69 checked failures in 13 cases without direct refutations. Coverage remains
217/246. Changed-only search avoids 640 probes; complete census time falls only
2.02% and peak RSS does not improve. All 1,969 tests pass. Prior source/artifact
ledgers and 64 proof blocks are preserved. Next compose these failures; continue
past the retained prefix for the other 16 cases. Resume
`experiments/results/cnf-b4-probe-cursor/checkpoint.json`. The full open export
grows to 1,379,665 bytes, including measured control history for skipped cases.
No native records or production defaults change.

Previous expansion checkpoint (25 November, direct native unit closure):
[Avoid expanding already unit-refutable residuals](direct-unit-closure.md).
Bounded direct unit proofs reduce complete local trial time 78.35% and bytes
80.33% versus the B4 compiler on the same eleven roots; records fall to 306
from 2,246. Both readers verify 44 unique archive/root pairs, and all 1,961
tests pass. All older proofs and artifacts remain preserved. One case still
regresses against fresh solving; acquisition/discovery and unresolved fallback
are additional. Coverage remains 217/246 with 29 unresolved. Next probe the
19 strengthened B4 closures using fresh bindings; retain the bounded shortcut
as the measured compilation baseline. Resume
`experiments/results/cnf-direct-unit-closure/checkpoint.json` and its inherited
`cursor_feedback` open-state bindings. Production defaults are unchanged.

Previous expansion checkpoint (25 November, cursor-failure feedback):
[Compose the saved B3 failures](cursor-feedback.md). A checked B4 propagation
pass closes 12 events without new assumed probes; all 11 distinct new native
roots pass both readers. Recognition reaches 217/246, leaving 29 unresolved.
Nineteen open closures gain 70 assignments. All 1,953 tests pass; 64 manuscript
proof blocks and all earlier artifacts remain unchanged. Complete positive-case
trials regress 60.18% against fresh solving, with 0.73% more encoded bytes.
Next probe strengthened B4 closures with new bindings and investigate repeated
native proof expansion. Old B3 cursor history cannot justify skipping B4 probes.
Resume `experiments/results/cnf-cursor-feedback/checkpoint.json` and its preserved
`remaining-closures.json`. No unrestricted-SAT or net workload gain is claimed.

Previous expansion checkpoint (25 November, persistent probe cursor):
[Resume the actual probe frontier](probe-cursor.md). Cold reload avoids 2,624
repeated probes with exact single-pass outcomes. Later candidates expose 142 new
failures in 31 cases; two first-prefix refutations reach 205/246 coverage. All
1,945 tests pass. Total census time falls 1.37% against restart but remains 15.77%
higher than uninterrupted search. Next compose the 161 B3 failures retained in
31 open cases, and reuse checked preparation. Honest history is required for
coverage reuse; every refutation remains independently checked. Resume
`experiments/results/cnf-probe-cursor/checkpoint.json`.

Previous expansion checkpoint (25 November, third-layer feedback):
[Compose the B2 failures](third-feedback.md). Two additional refutations require
no new assumed probes; both native roots pass both readers. Sampled coverage is
203/246, with 43 events unresolved. Six B3 closures gain 18 assignments. All
1,935 tests pass. Native compilation takes 2.16 times fresh-solving time and
encoded bytes grow 27.92% on these two gains. Next retain and advance a bound
candidate cursor on unchanged banks, and reduce checked proof construction.
Resume `experiments/results/cnf-third-feedback/checkpoint.json`; all prior
layers and complete B3 closures remain available.

Previous expansion checkpoint (25 November, changed closure probes):
[Target the changed closures](changed-closure-probes.md). Eight additional
refutations have native proofs checked by both readers, bringing coverage to
201/246; 45 events remain open. Skipping 32 unchanged events saves 2,048 probes,
11.75% discovery time and 2.21% complete census time. The scheduling policy does
not certify search exhaustion. All 1,927 tests pass. Native compilation still
regresses against fresh solving. Next compose 27 new failed probes retained in
eight open events, and retain a cursor for untested candidates in the others.
Resume `experiments/results/cnf-changed-closure-probes/checkpoint.json`.

Previous expansion checkpoint (25 November, prepared publication):
[Reuse the normalizer result at publication](prepared-publication.md). Compilation
falls 7.43% and complete local trials 3.72% on all fifteen cases. All native proof
payloads and rule checks stay identical; all 1,919 tests pass. Extra unchanged-context
reuse saves operations but adds no aggregate benefit over publication reuse alone.
Use the publication-only arm as the next measured baseline. Ordinary solving
remains faster; exact child-cofactor reuse and the 21 changed open closures are
next targets. Resume `experiments/results/cnf-prepared-publication/checkpoint.json`.

Previous expansion checkpoint (25 November, second-layer feedback):
[Compose failed probes with explicit proof layers](layered-feedback.md). One
propagation pass closes 16/69 events without new assumed probes. All 15 distinct
new roots have native proofs and both readers accept 30 archive/root pairs.
All 1,911 tests pass. The 53 open cases retain 207 assignments; 21 gain 120 facts
and 32 have unchanged closures. Native compilation is 54.24% slower than ordinary
solving despite 26.38% fewer bytes. Next reuse canonical cofactors/preparation
under strict checking, and target bounded new probes to changed closures. Resume
`experiments/results/cnf-layered-feedback/checkpoint.json`.

Previous expansion checkpoint (25 November, checked closure probes):
[Reuse the residual before another bounded search](closure-probes.md). An
additional 64-assumption budget closes 47/116 remaining events, with 41 distinct
new roots verified by both cold readers. Restart and conditioned arms agree on
coverage; conditioning cuts visits 50.06% and discovery time 8.45%, but total
census time only 1.51%. All 1,903 tests pass. The 69 unresolved cases retain 180
new failures in 37 events, with 125 old exclusions. Next compose that proof layer
by checked feedback and reuse expensive source/prefix preparation across rounds.
Native proof bytes roughly halve versus ordinary solving; compilation is still
6.57% slower. No complete workload advantage is established. Resume
`experiments/results/cnf-closure-probes/checkpoint.json`.

Previous expansion checkpoint (25 November, checked exclusion feedback):
[Compose saved failed probes by propagation](probe-feedback.md). One feedback
pass refutes 64 of 180 remaining events without new assumed probes. All 53 distinct
roots have native proofs and both readers accept 106 archive/root pairs. The
116 open cases preserve 656 checked assignments; 96 retain 348 exclusions and
20 have none. All 1,897 tests pass. Next condition on the saved unit fixed points
and test bounded new probes with acyclic provenance. Positive-case certificate
costs improve in aggregate after cold replay, but seed acquisition and unresolved
fallback remain outside that comparison. Resume
`experiments/results/cnf-probe-feedback/checkpoint.json`.

Previous expansion checkpoint (25 November, causal probe supports):
[Reduce full-cofactor proof reconstruction](probe-support.md). All 60 existing
roots compile with smaller source supports: 73.43% less compilation time and
78.93% fewer record bytes than the full compiler, with all 180 archive/root pairs
checked by both readers. All 1,889 tests pass, including cold exact-core reuse
across growing supersets. Coverage is unchanged. Ordinary solving is still faster
in aggregate; warm validation and 122 binary-prefix splits remain. Next test
checked exclusion feedback and profile remaining prefix/transport costs. Resume
`experiments/results/cnf-probe-support/checkpoint.json`.

Previous expansion checkpoint (25 November, complement scheduling):
[Reuse failures to schedule their opposites](complement-probes.md). Source/binary/
all recognition reaches 55/64/66 events, up from 16/24/26 at the same budget.
All 37 additional roots have native archives; two were unknown in prior inspected
snapshots, and ordinary local solving also proves them. Compilation is slower
and larger on all new cases. All 1,881 tests pass, including a counterexample to
monotone coverage under a fixed budget. Next investigate checked exclusion
feedback and compact source-support proofs: 160 unresolved events retain 851
exclusions, only 14 of which still have untested opposites. Resume
`experiments/results/cnf-complement-probes/checkpoint.json`.

Previous expansion checkpoint (25 November, wider-clause unit probes):
[Reuse checked guards in bounded propagation](wide-guard-probes.md). Source-only,
binary-guard and all-guard controls close 16/24/26 remaining events. The 23 distinct
roots have native proof archives; compilation is slower on all cases than ordinary
local solving and larger on 22. All 1,875 tests pass. Next reuse checked failed
probes to test untried opposites in 191 remaining events, then address iterative
feedback and full-cofactor proof expansion as separate gaps. Resume
`experiments/results/cnf-wide-guard-probes/checkpoint.json`.

Previous expansion checkpoint (25 November, discovery-budget frontier):
[Spend preparation savings on certified coverage](shortening-budget-frontier.md).
Recognition rises from 266 to 318/347/369 events at 96/128/256 roots; all earlier
successes remain. The 96/128 measured costs are below the older 64-root control,
but compilation and cold replay remain additional. All 67 new roots have native
archives and are already in ordinary-query stores. All 1,865 tests pass. Next
probe source clauses with the wider checked guards present in 228 of the 245
exhausted cases, retaining 15 unknown cases as unknown and testing native proof
costs. Resume `experiments/results/cnf-shortening-budget-frontier/checkpoint.json`.

Previous expansion checkpoint (25 November, immutable source preparation):
[Reuse original validation across conditioned states](shortening-prepared-source.md).
Discovery falls 21.46% in the matched sample; current-cofactor and native proof
checks remain. All 615 programs and 96 edit results are unchanged, with identical
6,535-record native archives for 173 roots. Persistent proof size is unchanged.
All 1,861 tests pass. Next measure whether broader search budgets convert this
saving into coverage of root-budget stops, separating fixed points that require
stronger guards. Resume `experiments/results/cnf-shortening-prepared-source/checkpoint.json`.

Previous expansion checkpoint (24 November, structural no-path filtering):
[Exploit contrapositive symmetry and retain limited filter gains](shortening-reach-filters.md).
Endpoint tests add three ternary-first successes; weak components add none and
repair none of the targeted regressions. The incoming index is mathematically
redundant for the constructed binary graphs and is removed in a checked
specialization. Both comparison phases and all regressions remain preserved.
All 1,853 tests pass. Ordinary search is faster on all three new local-proof
cases and retains fewer record bytes in aggregate. Next investigate immutable source/template preparation across
states. Resume `experiments/results/cnf-shortening-filters/checkpoint.json`.

Previous expansion checkpoint (24 November, ternary-first root ordering):
[Prioritize potential binary-clause yield](shortening-root-priority.md).
The bounded detector recognizes 263 saved events versus 202 with numeric reuse,
with 72 gains and 11 losses. Discovery falls 9.89% in the matched sample; 38
roots beyond both prior controls have checked native archives. Ordinary search
already stores every new root and remains faster in local solving comparisons.
All 1,844 tests pass. Next test charged endpoint/component reachability filters
on the 11 root-budget regressions, keeping the two zero-exclusion cases and all
unresolved events. Resume `experiments/results/cnf-shortening-priority/checkpoint.json`.

Previous expansion checkpoint (24 November, negative reachability reuse):
[Reuse closed failed-search sets across changed graphs](negative-reach-reuse.md).
The selected detector gains 60 saved events / 37 local roots over the 64-root
policy; all new native proofs are audited and already known to ordinary search.
A 128-root control recognizes more at similar measured time, with complementary
misses. Graph-delta checks, inverse indexing, memory and compilation regressions
remain charged. All 1,839 tests pass; the policy stays optional. Next investigate
structural root priorities and incremental conditioned-state preparation rather
than assuming fewer traversals give equal runtime savings. Resume
`experiments/results/cnf-reach-reuse/checkpoint.json`.

Previous expansion checkpoint (24 November, shared shortening preparation):
[Share one immutable context across each state's guard checks](shortening-context-reuse.md).
The optimized preparation retains source, support, reason and conflict checks.
Discovery falls 57.63% with identical programs; compilation falls 28.90% with
identical proof archives. Ordinary solving remains faster and the cumulative
bank is unchanged. A failed compilation exposed premature rejection
of a satisfied support clause containing an absent variable; the corrected
transport restricts the clause first, with the failure preserved. No live policy
or unrestricted-SAT claim changes. Resume the new checked checkpoint at
`experiments/results/cnf-shortening-context/checkpoint.json`.

Previous expansion checkpoint (24 November, iterative partial shortening):
[Use checked forced literals to expose new binary interactions](guard-partial-shortening.md).
All 615 prior graph events are replayed; 104 extensions beyond initial SCC and
full-clause covers represent 67 local roots. All 67 are already found by ordinary
search. Existing native certificates validate every forced step and terminal
contradiction, and selected supports remain reusable after cold reopen. Full
context and selected-support costs are compared on all 97 refuted local roots
and eight supplied chain controls. Misses and ordinary-solving regressions stay
in the evidence. Resume `experiments/results/cnf-guard-shortening/checkpoint.json`;
all prior banks remain unchanged and new archives are supplemental only.

Previous expansion checkpoint (24 November, selected cover supports):
[Compile and persist only the selected cover support](guard-cover-support.md).
Compile time falls 75.30% and record bytes 86.16% versus full-context composition
across 18 local CNFs. Six expansions after cold reopen each reuse a checked core
and add one wrapper. All seven pending proposals are supported; ordinary search
already retains all 18 roots. Source-binding costs still reverse the comparison
on the original 11-case subgroup, and small controlled cases regress. Keep this
optional. Next investigate exact partial clause shortening with proof-supported
binary consequences, using the preserved six-variable separation and unresolved
contexts. Resume `experiments/results/cnf-cover-support/checkpoint.json`; every
prior bank remains intact, with 89 new audited supplemental archives.

Previous expansion checkpoint (24 November, learned-guard clause covers):
[Check wider source clauses against learned binary consequences](guard-clause-covers.md).
Fifteen supported proposals produce 11 distinct native local refutations; nine
first occur at old inconclusive gate sites. Ordinary search eventually retains
all 11, and all eight whole queries remain unresolved. Local compilation is
3.07 times slower before support checking and uses 2.81 times the record bytes;
keep offline. Next compile and reuse only necessary supports, check the seven
additional relaxed-discovery proposals, and investigate exact partial clause
shortening on unresolved cases. All new proofs are preserved in checkpoint-linked
supplemental archives; the cumulative layered bank is unchanged. Resume
`experiments/results/cnf-guard-covers/checkpoint.json`.

Previous expansion checkpoint (24 November, shared guard contexts):
[Prepare a local source once for selected guard certificates](guard-context-reuse.md).
The same 87 hints use 34 context preparations. Normalization visits fall 60.88%
and position visits 56.63%, but complete-worker time rises 0.28% against support
composition. All native records and the 34 closures are unchanged; all eight
whole queries remain unresolved. Keep optional and retain the regressions.

A checked 12-variable, 13-clause counterexample identifies the next structural
gap: learned binary guards can exclude every literal of a wider source clause
even when their graph is satisfiable. The original binary cover and current
guard SCC gates both miss it. Next inventory augmented-graph covers on the 635
inconclusive sites and fresh controls before adding a live policy. Retain native
support proofs, exact conditioning and full resource accounting; a recognizer
separation is not a complete-solver failure or an unrestricted SAT result.
Resume `experiments/results/cnf-guard-context/checkpoint.json`; its cumulative
layered history is unchanged, with no new authority rows or publication layer.

Previous expansion checkpoint (24 November, immutable history layers):
[Publish only checked append records](history-layer-publication.md).
The exact preceding 173-record expansion now publishes about 38.1 KB while
reusing its immutable parent, versus 152.6 MB for another full snapshot.
Preparation plus publication falls 85.96%; complete workers fall 71.40%,
including slower cold restoration and full table comparison. The full 2.10 GB
materialized history, 160,338 native records and all prior authorities remain.
No SAT query or structural coverage result changes. Initial rejection of the
unchanged dirty accounting ledger is retained as a failed experiment; the new
reader preserves stale metadata without trusting its counters.

Preparation and logical comparison remain history-wide. Future append-boundary
capture needs explicit conflict/rollback/schema contracts; cold materialization
and chain compaction remain charged. Next within the solver, share exact local
context preparation across selected guard certificates and test complete costs
on fresh inputs. Resume `experiments/results/cnf-history-layers/checkpoint.json`
with its named `experiments.cnf_history_layers.restore_archive` reader; use
`full_snapshot_control` with legacy restore code. All prior proof blocks remain.

Previous expansion checkpoint (24 November, composition on clause supports):
[Reuse a compact native support and lift it to its enclosing CNF](guard-support-composition.md).
The 34 local closures use supports with 2,433 literals instead of carrying
32,371 full-context literals at those sites. Solve time falls 3.61% and checked
native state 5.17% against witness composition; five support roots are reused.
All eight exposed whole queries remain unresolved, solve time remains 4.60%
above ordinary search, and edit 4 has a small storage regression. Keep this
optional. The audit exposes a larger publication gap: 173 new native records
trigger 109.15 seconds recompressing the 2.10 GB historical union. First test
reusing that immutable parent with a checked append delta, charging export,
restoration and proof replay; keep the full archive control and all older bytes.
Within the solver, next share one exact local context binding across selected certificate
checks: composition now takes 0.02096 cumulative seconds on edit 28, while
support transport takes 0.02328, including 0.02093 in RUP checking. Reset binding
on changed coordinates/components and keep native verification. Broader core
retrieval must account for the preserved negative/partial-pool failures. Resume
`experiments/results/cnf-guard-support/checkpoint.json`; prior results remain intact.

Previous expansion checkpoint (24 November, witness-directed guard checking):
[Defer local support proofs until a contradiction witness needs them](guard-witness-deferral.md).
All 34 closures and native database bytes match the eager gate. Local consequence
checks fall 1,218 to 87, solve time 7.01% and complete-worker time 1.74% against
that gate. Ordinary search remains faster by the measured 7.87% solve overhead;
all eight exposed queries remain unresolved. There is no durable-state saving.
Next measure the actual clause support of each contradiction and compile over
that subset, using the existing checked negative-component lift to the full CNF.
Native composition now dominates the profiled gate (0.17224 / 0.22224 cumulative
seconds); support transport takes 0.02386. Smaller supports are not guaranteed,
and extraction, coordinate handling, checking, wrappers and cold replay must be
charged. Prior archives, all negative results and source fingerprints are
preserved. Resume `experiments/results/cnf-guard-witness/checkpoint.json`.

Previous expansion checkpoint (24 November, selective live guard closure):
[Measure local guard composition within whole queries](guard-closure-live.md).
The unit/binary gates close 25/34 local contexts on different paths, but all
eight queries remain unresolved. Solve time rises 7.40%/18.80% and complete-worker
time 2.02%/3.04% against ordinary search; checked-native-state totals also grow.
Binary checking admits 1,218 consequences while 635 of 669 sites are inconclusive.
The largest regression's profile charges 0.61726 cumulative seconds to support
transport (including 0.56672 in RUP checking), versus 0.28442 for seven closures.
Next build a tentative graph first, then validate only candidate witness-path
supports; reject a satisfiable superset graph without treating it as a source
verdict. Preserve native publication checks and explicit invalid-edge fallback.
Keep both current gates experimental. Resume
`experiments/results/cnf-guard-closure/checkpoint.json`.

Previous expansion checkpoint (24 November, local guard interaction composition):
[Compose conditional consequences into native local refutations](guard-interactions.md).
All 648 saved contexts are checked; 61 distinct local CNFs receive composed
native refutations. Forty close from opposite unit guards, one more from units
and original binary clauses, and 20 need binary guards. Three roots were absent
after the preceding query's shared budget, but no whole-query completion is
established. Local closure compilation takes 0.80095 versus 1.26243 seconds in
single cold pairs; isolated exclusions instead regress 8.79%. Discovery and
hint persistence add 7.32573 and 7.94632 seconds. Next test a selective live
closure gate with exact local support checks; defer wider guards and all-backbone
enumeration. Repeated core bodies in the 117,690,368-byte hint bank are a second
target. All 1,749 tests and 105 focused tests pass; old payloads remain intact.
Resume `experiments/results/cnf-guard-interactions/checkpoint.json`.

Previous expansion checkpoint (24 November, direct local certificate transport):
[Reuse checked unit traces on the actual cofactor](local-certificate-transport.md).
Four alternating comparisons reuse 148 local refutations with unchanged guided
choices. Fresh probe propagation visits fall 17.19%, but solve time only 0.55%;
complete-worker time rises 0.20%. No input completes. Native checked-cache totals
fall 0.135%, SQLite totals only 8,192 bytes, and peak RSS does not fall. Exact
support containment, fixed/name maps and native verification remain mandatory;
missing support or exhausted allowances use the original lazy probe. Keep this
optional. Next investigate interactions among multi-assumption guards at actual
local residuals, including overlaps, complementarity, components and open regions;
do not repeat the earlier guard-frontier tree without new structural evidence.
Resume `experiments/results/cnf-guard-certificate-reuse/checkpoint.json`.

Previous expansion checkpoint (24 November, live guard-guided probe selection):
[Select probes without retaining diagnostic event graphs](guard-probe-selection.md).
Four alternating comparisons on all eight exposed edits preserve the native
256-dispatch budget. Tracking alone reproduces counters and SQLite files at
1.27% aggregate solve overhead. Guided selection costs 1.84% more solve time and
0.77% more complete-worker time; all eight targets remain unresolved. Native
checked-cache endpoint totals rise 1.68%, plus the provisioned banks. Edit 28
regresses 11.13%: its query-only profile charges 0.50635 seconds to normalization,
0.49224 to native verification and 0.00188 to guard choice; cumulative costs
overlap. Next: test exact local transport of already checked conditional supports
under the same selection path, with component containment and native checking.
Existing memo/ordered-normalization experiments must remain comparison evidence.
Resume `experiments/results/cnf-guard-probe-selection/checkpoint.json` using the
multipart reader. Earlier payloads, raw controls and negative results stay saved.

Previous expansion checkpoint (24 November, guard-guided probe census):
[Use saved exclusions to identify probes ordinary search misses](guard-probe-census.md).
Eight causal cold edits expose 648 ordinary probe contexts and 394 distinct
unit-refutable cofactors. Ordinary probing does not try 260 of those polarities;
232 use different variables. All 260 are absent at observation time. Every
actual local child is independently checked, including 134 proposals from
strict source subsets. A retained counterexample rejects automatic lifting of
full-source negativity to a component. Search counters and SQLite files stay
identical, and all targets still stop at 256 dispatches. Capture adds 31.71%
aggregate solve time; off-line checking/storage adds 3.15887 seconds. Next:
bounded live probe selection with cheaper matching and coordinate maintenance,
native proof composition and order-matched controls. Provisioned origins and
exposed inputs leave recognition and fresh evaluation open. Resume
`experiments/results/cnf-guard-probe-census/checkpoint.json` with the multipart
reader; preserve all prior authority and alternative proofs.

Previous expansion checkpoint (24 November, shared guard-frontier selection):
[Use the split allowance on shared guarded regions](guard-frontier-selection.md).
The new bounded tree closes more assignment mass on all eight saved banks.
Edit 64 improves 27.38% in solve mean and 1.80% in database size against the old
plan, but edit 28 regresses 4.66%. Both remain unresolved and ordinary solving
is faster. The open-tree ablation attributes most of the improvement to branch
order; guard mass is not a cost model. Next: use checked exclusions within
ordinary search, reusing the existing trace-learning source checks where
applicable and adding the missing multi-assumption justification. Preserve
deletion alternatives and charge construction, checking and remaining acquisition.
Resume `experiments/results/cnf-guard-frontier/checkpoint.json` with the multipart
reader. Earlier proof payloads and all controls remain intact.

Previous expansion checkpoint (24 November, conditional supports from stopped origins):
[Capture checked regions while retaining open branches](stopped-origin-supports.md).
The seven unfinished origins yield 342 conditional templates; the completed
control adds 53. All survive their edits, and the original search is unchanged.
Cold diagnostics on 28/64 still stop: supports increase solve time 6.31%/5.62%
over identical open trees and retain more state. No default changes. Next:
measure shared and subsumed guard structure, avoiding the current expensive
branch order; then reduce repeated source restriction and unit extraction.
The census retains rolled-back candidates as misses and preserves causal
prefixes, conditional proofs and both controls. Resume
`experiments/results/cnf-stopped-origins/checkpoint.json` with the multipart
reader. Validation distinguishes fresh dependency replay from preserved earlier
full-history audits; previous authoritative payloads remain byte-identical.

Previous expansion checkpoint (24 November, deferred binary preparation):
[Normalize only when a binary contradiction needs publication](probe-binary-lazy.md).
The target drops 67 residual normalizations to six with the same certificates.
Four repetitions reduce solve mean 3.21% exposed / 3.57% fresh versus eager
closure, but remain 5.24% / 4.97% slower than handoff-only. All policies close
40/48 exposed and 34/48 fresh roots; retained proof bytes are unchanged between
binary policies. The gate remains experimental. Next: inspect source-bound
conditional leaves from unfinished origins. Fresh 63/64 differ by one removed
and one added clause but both stop; the existing whole-plan route requires a
completed negative root. All 24 edit pairs are recorded, including seven
unfinished origins and the failed completed-origin control 27/28. A stopped
root is never proof authority. Resume
`experiments/results/cnf-probe-binary-lazy/checkpoint.json` with the multipart
reader. All 1,697 tests and 86 focused checks pass.

Previous expansion checkpoint (24 November, binary closure inside whole probes):
[Keep new recognition subject to total cost](probe-binary-closure.md). An exact
census certifies 19 previously inconclusive cofactors using existing binary and
unit proofs. The live gate adds 80 fresh negative cofactors but retains the
same 40/48 coverage, raises solve mean 8.86% and worker mean 5.03%, and stores
2.72% more native payload. Every pair regresses; no default changes. Next:
defer full-residual normalization/key creation on binary misses. Fresh case
38 pays for 67 such normalizations and obtains only six refutations. Preserve
source-bound publication and the existing gate's decisions, then compare with
both controls. The eight unresolved roots still need broader structural work.
Resume `experiments/results/cnf-probe-binary-census/checkpoint.json` using the
multipart archive reader. All 1,689 tests and 78 focused checks pass.

Previous expansion checkpoint (24 November, consumed preparation lifetime):
[Separate cleanup, admission and active memory](probe-lifetime.md). Early release
reduces solve mean 4.57% exposed / 3.54% fresh and complete-worker mean 1.67% /
1.92% versus original 2 MiB retention. A 4 MiB original control nearly matches
it; cleanup alone regresses solve mean. Fresh pending charge stays below 2 MiB,
but its full-visit envelope reaches 4.61 MB. The selected allocation trace and
unchanged retained proof state do not show a substantial memory saving. All
four arms retain 42/48 exposed and 40/48 fresh coverage. Next: census existing
binary refutations in inconclusive probe residuals, including the hardest fresh
case 37 and unresolved mixture edits 61/67. Treat this as an untested discovery
hypothesis; preserve failed recognition and source-bound proof obligations.
Resume `experiments/results/cnf-probe-lifetime/checkpoint.json` with the multipart
archive reader. All 1,677 tests and 66 focused checks pass.

Previous expansion checkpoint (24 November, exact probe handoff):
[Reuse preparation at the actual child](probe-handoff.md). The 2 MiB policy
reduces mean solve time 3.58% exposed / 2.68% fresh, with all four pairs faster.
The 256 KiB policy regresses. Answers, models, proof bytes, retained solver state
and 42/48 coverage remain unchanged. Next: release consumed preparation before
descendant search; fresh acquisition rejects 684 offers despite its larger cap.
The six unresolved random-three roots still need broader structural discovery.
Resume `experiments/results/cnf-probe-handoff/checkpoint.json` using the existing
multipart archive reader; all earlier results remain preserved.

Previous expansion checkpoint (24 November, complete-result priority):
[Try complete reuse before a partial plan](whole-pool-priority.md). Five exposed
and five fresh queries use checked complete proofs without native expansion.
Coverage remains 42/48 in each stream. Exposed solve mean improves 2.17%; fresh
solve time is mixed, while complete-worker mean falls 1.63% and payload 3.03%.
Misses remain costly; the known 223-dispatch transfer survives with added lookup
work. Next: inspect prepared whole-clause cofactors on the six unresolved fresh
random-three roots. Restore the cumulative checkpoint with the new backward-
compatible `experiments.cnf_archive_parts.restore_archive` helper.

Previous expansion checkpoint (24 November, partial whole-proof plans):
[Retain reusable leaves at an open frontier](whole-proof-frontiers.md). The
automatic policy certifies exposed edit 70 in 223 dispatches using 22 surviving
supports, raising coverage from 38/48 to 39/48. Fresh coverage stays 42/48 and
solve mean regresses 4.04%. Next: prioritize existing complete proof/model pool
results; edits 31/34 unnecessarily grow from one dispatch each to 57/58. Keep
the successful partial transfer, explicit open leaves and all measured costs.

Previous expansion checkpoint (23 November, whole-input affine completion):
[Complete an already extracted affine space](whole-input-affine-completion.md).
The existing bounded completion and exhaustion checkers now serve whole-input
acquisition. All 16 candidates reject exposed case 43; checked UNSAT raises
coverage from 39/48 to 40/48 with zero native expansion for that query. The fresh
stream triggers no completion and retains the preceding proof bytes and
coverage. Exposed solve mean improves 6.94%; fresh solve mean regresses 0.46%.
Next: discover reusable branches of fresh case 69's checked refutation
for its still-unresolved edit 70. Preserve chronology, source correspondence,
all extraction costs and the ten unresolved fresh no-equation roots.

Previous expansion checkpoint (23 November, canonical probe preparation):
[Reuse the parent's clause invariant](ordered-probe-preparation.md). Exact proof
bytes and search decisions survive; fresh solve mean falls 4.54% against the
preceding lookahead policy, while exposed timing is mixed. Fresh lookahead still
costs more than the original binary policy. Next: unresolved whole-input case 43
has a consistent rank-108 affine subsystem on 112 actual variables, leaving only
16 assignments to check against 61 clauses. Reuse the existing affine completion
and separate negative-exhaustion authority; eight no-equation roots remain open.

Previous expansion checkpoint (23 November, whole-CNF lookahead):
[Price broader probing on fresh inputs](whole-cnf-lookahead.md). The policy uses
only CNF structure and existing checked proof rules. Expansion dispatches fall
12.1% exposed and 16.6% held out; native payload falls 2.5% and 7.4%. Solve time
rises 10.08% and 3.71%, so keep it optional. One query completes earlier and
supports its edit, but both arms eventually solve the same 47/48 distinct
held-out roots. Next: cheap recognition and prepared-cofactor reuse for the
499 inconclusive held-out probe attempts; retain the unresolved edited root.

Previous expansion checkpoint (23 November, finer recomposed origins):
[Price live origin admission](refined-proof-origins.md). Two completed partial
proofs become lazy candidates. The finer cover is selected, but expansion stays
at 32 dispatches; extra extraction/publication grows preparation/query time
2.39%, native payload 1.13% and hints 45.89%. The policy remains optional and is
rejected as a default. More intact leaves can leave the same missing residual.
Next: return to fresh unlabelled whole-CNF discovery using the current solver
and existing automatic guard recognizers, rather than further optimizing this
already solved conditional stream. Preserve unknowns and exact composition.

Previous expansion checkpoint (23 November, missing-leaf handoff):
[Pass prepared leaves into acquisition](missing-leaf-handoff.md). Five fewer
normalizations preserve all native proof payloads, hints and checks. Work falls
by 3,133 literal visits and 13,573 key bytes, but preparation/query time regresses
2.29% and complete-worker time 2.58%. Keep optional. Twelve new tests pass; no
new native identity is needed. Next: price a finer surviving branch from the
actual case-15 recomposed proof, including admission and extraction. It shrinks
one case-20 residual by only ten literals and one variable. Case-19 admission
provides no smaller missing residual; preserve this failed idea. All three
prospective origin pairs keep the same missing-leaf counts.

Previous expansion checkpoint (23 November, carried clause origins):
[Reuse original provenance](carried-clause-origins.md). Indexed path updates
retain exact minimum original representatives, covers, native payloads and
hints. Cover-phase mean improves 8.36%, but preparation/query mean regresses
1.79% and complete-worker mean 6.32%. All costs and negative results remain
visible. Next: pass the existing canonical triple at five missing-leaf calls
into native acquisition, preserving source validation and every proof check.
No new native identities or unrestricted bound.

Previous expansion checkpoint (23 November, shared partial preparation):
[Reuse conditioned leaf preparation](prepared-partial-recomposition.md).
Identical native proof bytes, hints, origins and dispatch counts isolate six
avoided leaf preparations and one unchanged frame. Preparation/query mean is
0.98% lower than the preceding partial route, with one of four pairs regressing;
it is effectively tied with baseline. The root-work counter omission is fixed.
Next: reuse original reason-clause provenance in cold cover extraction, which
still rescans the full source at each checked proof node. No new native IDs.

Previous expansion checkpoint (23 November, partial-cover recomposition):
[Preserve intact proof branches](partial-cover-recomposition.md). Four partial
attempts use native leaves for broken supports and reconstruct both SAT and
UNSAT answers. Dispatches fall 39 to 32, preparation/query improves 3.99% against
complete covers, and native payload falls 2.80% against baseline. The route is
still 2.45% slower than baseline. Next: share repeated conditioned-residual
construction and support preparation; preserve native checking and cold
extraction costs. Recomposition outcomes are not yet new learned origins.

Previous expansion checkpoint (23 November, unit-gated covers):
[Keep cheap unit proofs](unit-cover-gate.md). The largest cover regression falls
17.77 to 3.30 ms. Gated learning improves 5.53% against ungated learning, but
remains 6.76% slower than baseline. The gate-only ablation has identical native
proof bytes despite fewer expansion dispatches. Next: preserve intact leaves
when one deleted clause breaks a conditional cover. Cases 19/20 each admit an
earlier four-leaf cover with three intact supports; exact partial recomposition
and full witness/proof checking remain to be implemented and priced.

Previous expansion checkpoint (23 November, learned conditional covers):
[Transfer complete conditional supports](learned-conditional-covers.md).
Three chronological transfers reduce expansion dispatches 43 to 33, with native
unit/split checking and no future-answer seeding. Preparation plus query is
7.74% slower, native payload grows 1.95% and active hints grow. Keep optional.
Next: preserve a cheap unit conflict before cover discovery; the largest
regression replaces a 3.57 ms unit refutation with 17.60 ms of cover work.
Price miss handling, prefix sharing and discovery amortization explicitly.

Previous expansion checkpoint (23 November, shared template preparation):
[Reuse the live cofactor](template-preparation.md). Sharing one immutable
source/guard preparation removes 71 repeated checks and constructions with
identical proof bytes, routes, storage and native verification. Local
preparation-plus-query mean improves 14.35%; full-worker time does not improve.
Next: source-bound conditional supports across five related native fallbacks
that account for 56.28% of native-fallback time. Existing early negative reuse
already misses these cases. Charge discovery and recomposition, preserve
branch guards and the nearby SAT control, and use only earlier stream results.

Previous expansion checkpoint (23 November, early pool priority):
[Use checked answers before recovery](pool-priority.md). Eight negative-core
and four witness hits move ahead of native dispatch with identical proof bytes
and selected endpoint memory. Local preparation-plus-query mean improves 2.50%
over compact reuse; full-worker time is unchanged and native-only remains
slightly cheaper. Recovery remains more costly. Next: eliminate the 71 repeated
full-cofactor constructions and template checks while preserving input binding
and every native verification. This changes no coverage or unrestricted bound.

Previous expansion checkpoint (23 November, conditional recovery):
[One missing reason selects a forced value](conditional-support-recovery.md).
Native reconstruction validates UNSAT and SAT results, and the hard positive
case falls from six expansions to two. Across matched streams, however, the
ordinary-fallback recovery gate adds 10.66% preparation-plus-query time and
13.05% native payload despite fewer expansions. Keep it optional. Next: preserve
cheap negative-core and witness hits before recovery and reduce redundant full
proof construction. The one-new-literal property requires a unit fixed point
and a unit-refutable strengthening, not an arbitrary UNSAT donor.

Previous expansion checkpoint (23 November, conditional unit supports):
[Guarded refutations and compact active hints](conditional-unit-support.md) lift
ancestor reasons and preserve split assumptions. Forty conditional hits match the
existing conditioned causal-core baseline; fresh query expansions fall 68 to 28,
but preparation-plus-query time regresses against native-only solving. Compact
hints shrink 77.84%, with identical native proofs and retained provenance. Next:
bounded recovery after a reason deletion, including the surviving SAT case;
automatic guard/map discovery and full native proof-space growth remain open.

Previous expansion checkpoint (23 November, direct joint-prefix reuse):
[Reusing the already-live first cofactor](joint-prefix-reuse.md) removes two
normalizations and restrictions from the largest query without changing proof
bytes, storage or verification. Runtime differences are small and noisy. Next:
conditional mixed-width supports in the remaining 14-node proof; its nine unit
nodes use 148 reason literals within 6,495 stored CNF literals. These are local
reason counts, not an unconditional compressed core. Exact source/condition/map
checks and child obligations must accompany any transfer.

Previous expansion checkpoint (23 November, fused causal reconstruction):
[Order-preserving preimages](preimage-fusion.md) share untouched checked clauses
and avoid redundant normalization/reverse mapping. Six balanced repeat pairs,
including setup, save 6.32% on controls and 4.49% on new-edit query means, with
identical native proofs, partitions and storage. Complete-worker means barely
change; the policy stays optional and serial. Next: exact source/assignment
reuse in prefix and excluded-path construction around the new nine-expansion
mixed branch. No decision coverage cell or unrestricted bound is added.

Previous expansion checkpoint (23 November, consequence priority):
[Checked cofactor priority](consequence-priority.md) recovers the late-consequence
regression and preserves the exposed joint proof bytes. Six new edits save 4.54%
query time and 3.91% native payload versus joint conditioning. Controls still
regress 0.80% versus one-target search, so the rule stays optional. Next: exact
reuse of repeated conditioning and causal support around the remaining
six-expansion branch. Fewer expansions alone do not guarantee lower total cost;
no new coverage cell or unrestricted complexity claim follows.

Previous expansion checkpoint (23 November, joint binary consequences):
[Checked joint conditioning](joint-binary-consequences.md) reduces the exposed
branch and two sign variants from nine to four expansions. The original saves
24.10% query time and 24.86% proof payload. New edits regress 4.05% in time and
grow payload 8.65%, despite fewer expansions; keep the policy optional. Next:
assess full-CNF continuation cost, using the preserved case-61 regression against
the case-31 success. All prior proofs remain authoritative. No new coverage cell
or general complexity claim follows.

Previous expansion checkpoint (23 November, live fallback):
[Synchronous continuation](live-fallback.md) reduces the exposed replacement from
17 to 11 expansions and query time by 20.71%, with identical proof bytes. Six
controls improve 2.58%; six new edits never resume and regress 3.89%. Keep it
optional. Completed proofs persist, while unfinished frames remain local to the
call. Next: combine independently useful binary consequences in the saved dominant
partition branch, with recognition, compilation and source recomposition charged.

Previous expansion checkpoint (23 November, second binary target):
[Bounded consequence recognition](binary-target-fallback.md) adds a checked path
missed by the first target. New edits take 69 -> 60 expansions and 8.29% less query
time, but controls regress 1.14% and exposed branches remain nine expansions.
The main saving crosses the probe budget: direct 11 -> 8 versus wrapped 17 -> 8.
Next: retain source-bound unfinished continuation work across native fallback,
separately from checked proof authority. All 75,677 native records and 242 partition
records are preserved. No new whole-source coverage or default change is claimed.

Previous expansion checkpoint (23 November, partition preparation):
[Immutable partition preparation](partition-preparation.md) replaces four branch
constructions with shared acquisition data plus independent reconstruction.
New-edit binary-frequency query time falls 6.15%, preserving proof bytes and
expansions, but complete worker time regresses. The next target is a saved
125-variable binary/ternary branch requiring nine expansions. Its exact prior
state excludes its answer. All 75,508 native records and earlier experiments
remain preserved; no new whole-source coverage class is claimed.

Previous expansion checkpoint (23 November, direct cofactor handoff):
[One-use preparation](cofactor-handoff.md) reuses normalization and unit traces,
reducing new-edit query time 2.66% with identical proof bytes and decisions.
Complete worker time does not improve, and routing still costs more than the
binary-frequency baseline. The next concrete reuse target is the same six-branch
partition structure built four times per selected query. Preserve independent
source/child checking while sharing immutable construction work. All 75,416
native records and earlier experiments remain preserved.

Previous expansion checkpoint (23 November, prepared cofactors):
[Targeted normalization reuse](prepared-cofactors.md) preserves exact proof bytes
and removes 7.34% of normalizer input work on new edits, but increases query time
0.75%. Keep it optional. The saved dominant query motivates a direct prepared-child
handoff and sharing useful unit traces; cached-negative lookup and unchanged
proof checking remain required. The two-polarity routing regression is still open.

Previous expansion checkpoint (22 November, both cofactor polarities):
[Two-polarity recognition](bipolar-routing.md) closes the saved fixed-polarity
blind spot: all three sign variants take four expansions versus 30 under
binary-frequency routing. The extra probes increase time and proof storage on
nearby edits. The policy remains experimental. Price recognition and the surviving
continuation together; retain completed cofactor proofs and investigate reuse of
propagation work. No new whole-source coverage or unrestricted bound is claimed.

Previous expansion checkpoint (22 November, routing counterexample):
[matched-state routing](binary-routing.md) confirms the local policy effect and
rejects a false-only cofactor guard as a speed optimization. It lowers ordinary
expansion counts slightly but raises query time on controls and new edits. The
first later divergence has a checked true-cofactor contradiction missed by the
gate. Its exact pre-target state is saved for polarity-sensitive recognition and
signed-variant comparisons. General solver defaults remain unchanged.

Previous expansion checkpoint (22 November, binary target rankings):
[bounded binary targets](ranked-binary-targets.md) reduce the exposed branch from
61 to nine expansions and six new residual edits from 107 to 51. Native proof
rules are unchanged. A replacement branch regresses from ten to 33 despite the
original reused earlier proof still being available. Its exact pre-branch state
is saved for a controlled routing comparison. Keep the policy optional; automatic
retrieval, source composition and unrestricted-SAT bounds remain open.

Previous expansion checkpoint (22 November):
[probing before support partitioning](probed-support-partition.md) preserves
checked partial results and avoids preparing partitions for cheap native queries.
The six-clause boundary improves from 75 to 26 expansions including the probe,
but a fresh deletion regresses from 65 to 86. Its 61-expansion branch is saved
with the exact pre-branch state as the next structural target. Automatic donor
selection, source integration, continuation reuse and sidecar compression remain
open. The general affine baseline is unchanged.

Previous expansion checkpoint (19 November):
[transported support partitions](transported-support-partition.md) establish a
useful residual-level conditioning pattern and a failed admission heuristic.
Case 31 improves from 69 to 17 expansions; two already cheap cases regress.
Automatic donor selection and cost prediction remain open. Sidecar duplication
increases persisted delta space despite smaller native proofs. Resume the
`cnf-transported-partition` checkpoint; keep the affine policy as the baseline.

| Item | Concrete work | Stronger claim that must not be inferred |
| --- | --- | --- |
| 1. Uniform expansion | Executable compact coverage states for the logarithmic-width SAT family, with preservation, coverage, construction-size and query-cost theorems. | Uniform polynomial-time SAT for unrestricted inputs. |
| 2. Accounting | Disjoint elapsed phases, child resource measurements, certificate and storage sizes, explicit unknown formal costs. | A complete machine-level cost proof for external CDCL or SQLite. |
| 3. Machine/memory | Extend operational semantics and storage bounds beyond one evaluation; expose remaining bit-machine obligations. | Verified compilation/runtime or constant-memory search. |
| 4. Internal reuse | Long-lived CaDiCaL over shared circuit definitions and root assumptions; independently check answers. | An incremental UNSAT proof checker if negative answers still require a fresh LRAT run. |
| 5. Service guarantees | Deadlines covering native work and certificate checks, bounded message/proof sizes, recovery, checked-cache option, and rollback tests. | Kernel verification of Python, the OS, and SQLite. |
| 6. Learned proposals | Persist a compact online predictor, charge updates, check every proposal, and test chronological held-out transfer. | Efficient exact learning of unrestricted SAT. |
| 7. Evidence | Public SATLIB instances and structural/shift streams; direct and checked baselines; retained failures/timeouts; memory and acquisition costs. | Universal speedup or a representative SAT-competition result. |

First implementation milestone:

- `CompactExpansion.lean` proves preservation, eventual coverage, construction
  cells/steps, SAT/UNSAT soundness, and the restricted reference-query bound.
- `SearchMachine.lean` proves operational search composition and reachable-state
  payload bounds. Parsed programs and assignment generation remain supplied.
- Live CaDiCaL clause reuse, a checksummed bounded predictor, disjoint elapsed
  phases, deadline-aware I/O, monitored external files, and strict cache checking
  are implemented. Internal clauses remain live-session state; saved results,
  certificates and models survive restart.
- Lean's transitive axiom audit: 1,197 declarations / 651 theorem declarations.
  All 57 integration tests pass, including truth-table comparisons, timeout
  recovery, forged proposals/cache entries, concurrent model updates, and DIMACS
  conversion. No proof admits or new axioms were introduced.

The final public/chronological benchmark and manuscript now include this work.
The stronger claims in the final column remain open.

The public pilot exposed native stack exhaustion during counted length discovery.
A proved compiler replacement now preserves the exact value and ledger while
using stack-safe list length; ASCII decoding accumulates iteratively as well.
A regression test covers an encoding over 500,000 bits. The pilot is retained
in `experiments/results/expanded-pilot/`, including 32 failures (12 direct
DIMACS trailer errors, 20 checked-path stack overflows).

Evidence at the first follow-up milestone (items 1 and 4 are extended below):

| Item | Implemented and checked | Remaining boundary |
| --- | --- | --- |
| 1 | Compact coverage, exactness/preservation, unary construction, restricted decision ledger; native demonstration. | No unrestricted polynomial constructor. Coverage/promise checks are outside that ledger. |
| 2 | Disjoint wall-time phases, service/reaped-child CPU, process RSS, proof/model/database bytes, explicit unknown formal totals. | No full CDCL/SQLite instruction proof, simultaneous process-tree peak, energy or hard physical memory cap. |
| 3 | Complete assignment-search traces, reachable-state payload bound, restricted quadratic space, proved stack-safe length replacement. | Parsing/generation are supplied to the trace; no full bit-machine/compiled-runtime proof or production-CDCL memory proof. |
| 4 | Shared live circuit clauses, retained learned clauses and root assumptions; every proposed result checked independently. | Internal clauses do not survive restart; negative proposals still use a fresh LRAT run. |
| 5 | Query deadlines, size limits, bounded child I/O, reaping/recovery, SQLite rollback, strict-cache rechecking and adversarial tests. | Cooperative timing, outer transport and OS/runtime trust remain; budgeted service can return an error. |
| 6 | Bounded persistent predictor, charged training from checked answers, transactional concurrent updates, chronological new-witness transfer. | Simple tractable family; no exact general-SAT learning guarantee or universal savings under shift. |
| 7 | 28 public SATLIB instances, four chronological/structural streams, six modes, three repetitions; all 1,260 answers correct. | Older small suites, local host noise, no current competition baseline or equal-total-memory study. |

The benchmark and manuscript report regressions as well as gains. Internal
retention does not isolate the causal contribution of learned clauses. The
combined predictor policy includes other mechanisms; incremental alone performs
similarly on signed units. Initial benchmark execution overlapped the test suite
briefly; small timing differences should not be interpreted as significant.

The live store preserves all 1,420 previous rows and 258 proofs, adds 355 checked
current-engine results and 129 proofs, and retains a bounded current model.
`experiments/results/expanded/persistence.json` records the replay, semantic audit,
and hashes confirming preservation. Four historical experiment datasets are
unchanged. `expanded-pilot/` preserves the development failures; `expanded/`
contains the final data and source/binary fingerprints.


## Structural follow-up on items 1 and 4

The next implementation milestone adds bounded-interface composition in
`Components.lean` and durable structural knowledge in the service. The formal
result allows total variables to grow through disjoint private blocks: the
exponential parameter is local plus interface width. Its declared acquisition
budget charges each distinct shape once; intersections charge each occurrence.
It does not prove that arbitrary SAT admits such a decomposition.

`--components` implements the empty-interface case. It normalizes variable names,
shares component results and content-addressed terms/shapes/maps/prefix nodes,
and checks the recomposed witness. A native checked conjunct certificate allows
renamed UNSAT cores to survive new constraints, including component mergers.
It does not transfer under arbitrary deletion or negation. Nonempty-interface
summary construction and separator discovery remain implementation gaps.

Incremental sessions now archive stable circuit definitions and selected short
learned clauses in immutable compressed objects. Restarts replay a bounded
clause subset; concurrent workers fork sessions. This is untrusted proposal
state, not incremental LRAT certification. General negative proposals still
require an independent proof. Active caps never delete the historical archive.
The original full-input result archive still grows independently of structural
compression; all storage categories must remain in the accounting.

Validation at this milestone: 69 integration tests pass; the Lean axiom audit
checks 1,264 declarations / 694 theorem declarations. Tests cover incompatible
positive components, renamed and extended negative cores, forged component
records, truth-table comparisons, durable clauses, poisoned replay state,
concurrent sessions and schema migration without lost results.

The structural study completes this follow-up with 420/420 correct answers.
One two-variable component shape serves 127 occurrences across expansion to
128 variables; one UNSAT core survives six connected extensions. The chain
control still needs seven acquisitions. The full component database is larger
than the checked baseline despite reduced duplication, so no whole-archive
compression or universal speedup claim is made. The paper now contains both
restricted structural proofs, prior-work attribution, measured overheads and
remaining boundaries.

Next steps recorded at the structural milestone:

1. Find and verify small separators, then implement the nonempty-interface
   relations proved in Lean. The present runtime uses disjoint components only.
2. Support proof-carrying incremental learned clauses and certification of
   general negative proposals. Current certified negative reuse transfers
   existing conjunct cores; otherwise an independent LRAT run remains necessary.
3. Extend the declared structural ledger to concrete acquisition, normalization,
   compressed retrieval and verification costs. Establish total-memory policies
   without confusing an immutable evidence archive with a bounded active model.
4. Broaden equivalence detection beyond first-occurrence renaming and fixed term
   order, while charging the matching cost. The four-instance negative index
   deliberately provides incomplete retrieval.

These are implementation and restricted-proof tasks. No argument currently
bounds local/interface width, exact representation size or acquisition time
polynomially for unrestricted SAT.

## Implementation of local interfaces: first milestone

The local-interface engine now performs checked variable elimination, retains
its dependency DAG, shares semantic relation payloads, and accepts persistent
add/replace/remove snapshots. Native checks establish the original-constraint
partition, every table/projection, and the final query context. This includes
negative reuse after extension and rejection after removal of an assumption.
Lean proves the exact bucket-elimination rule and unaffected-factor invariance.
Snapshot maps are persistent AVL trees; all previous roots and results remain.

New relations select constant, dense bitmap, sparse, or reduced ordered decision
DAG encodings by actual serialized size. Immutable object storage uses raw or
zlib bytes, whichever is smaller. Existing schemas and old zlib objects remain
readable. General incremental clause proof integration, lazy row acquisition,
expanded cost proofs, the benchmark and manuscript reconciliation are the next
parts of the same requested five-step implementation.


## Five-step implementation: proof and lazy-acquisition milestone

1. Local bucket elimination handles nonempty interfaces and preserves the old
   order when it fits the width cap. Width failure uses checked complete solving.
2. Persistent manifests and factor dependencies preserve every previous state.
   Deltas parse supplied constraints; row and factor caches reuse unchanged
   dependencies. Planning and final checks can still scan the active graph.
3. Lazy rows are now operational, not just an encoding. Unknown rows cannot
   refute a query. Native row recomputation checks acquired/replayed proposals.
   `--incremental-proofs` additionally archives assumption-aware proof dependencies
   and checks negative live traces using Lean LRAT. Supported UNSAT queries no
   longer require a fresh CDCL solve. Unsupported/invalid traces use fallback.
4. Complete relations share behavior independently of syntax/evidence. Exact
   constant/bitmap/sparse/BDD encoding chooses the smallest serialized payload;
   raw-or-zlib storage never expands individual new object payloads. Partial
   rows, evidence and historical versions still consume additional archive space.
5. `InterfaceCosts.lean` connects local evaluation and projection to explicit
   operation bounds. All elapsed phases, acquisition/replay counters and storage
   remain charged. A whole-machine/CDCL/SQLite cost theorem remains open.

The complete Lean build audits 1,554 declarations / 837 theorem declarations.
All 92 integration tests pass, including poisoned partial rows, forged proof
hints, changed assumptions, restart replay and negative certificates checked
without permitting a fresh standalone solve. Benchmarking and manuscript
reconciliation complete this same five-step follow-up in the next commit.


The five-step follow-up is now implemented and documented in the manuscript.
The new study has 108 runs and 792/792 correct answers, including 198 negatives.
Both proof-enabled modes certify all their negatives through incremental LRAT.
Interface delta reuse reduces local acquisition and transport but often loses
on total time; the archive also remains larger. The paper attributes bucket
elimination, persistent structures, BDDs and incremental proof checking to prior
work, and adds published representation-specific lower bounds.

Remaining research limits are unrestricted width and representation size,
affected-dependency bounds under arbitrary edits, proof/restart cost, bounded
whole-archive memory, and a full machine-cost theorem. These are stronger than
the completed implementation tasks. No polynomial-time SAT claim follows.

Final compatibility review adds tests for semantic payload sharing with separate
provenance, Lean-only fallback, and component certificates combined with the new
proof option. All 95 tests pass. The compatibility fixes affect combinations
outside the timed modes (except a backend dispatch guard on width fallback);
the native binary and its Lean audit are unchanged.

## Scaling follow-up: indexed planning and direct symbolic proposals

The planner now maintains incidence counts instead of rebuilding adjacency at
every elimination step. Persistent plans route changed sources through affected
buckets in a retained order and stop propagation at identical output identities.
The counters separate affected buckets, reused buckets, source comparisons and
snapshot copying. Width failure rebuilds an order or uses checked fallback.
Copying/serializing plans, collecting active constraints and checking final
answers remain global operations; this is not an O(delta) whole-query bound.

The opt-in `--symbolic` path constructs reduced ordered decision diagrams from
formula syntax and performs conjunction, restriction and existential projection
directly. It archives symbolic proposals and enforces node/work caps. Native
factor-row and original-answer checks remain authoritative, including after
restart. This avoids Python truth-table acquisition, but native verification,
small-scope row-cache capacity and worst-case diagram growth are still charged.
Twenty-eight interface/scaling tests pass at this milestone, including exhaustive
small-formula comparisons, random edits, archived branching, poisoned symbolic
proposals, caps and an 80-variable parity diagram built without table rows.

The next milestone adds live incremental-LRAT checking against the existing
native graph, plus session-verified negative cores. A selected archived core is
rechecked once after restart; subsequent conjunct extensions reuse the checked
native fact. Removing a required conjunct fails the transfer check. General
per-clause verification reuse and zero-cost restart are not established.

`--max-archive-bytes` limits logical SQLite pages and refuses further acquisition
at capacity, preserving all committed history. WAL/temporary files and total
process memory are separately reported, not claimed bounded by that option.
`--adaptive` selects between checked and interface solving from prior measured
complete-query durations, persists observations, and charges selection/update
work. This is an empirical policy, not a universal speedup guarantee.

`Scaling.lean` checks symbolic restriction/conjunction/projection semantics on a
reference tree, conjunct-refutation transfer, a depth/fanout affected-node
envelope, conditional polynomial update costs, cumulative work/archive bounds,
and the fixed-capacity obstruction for positive archive increments. The common
polynomial bounds on affected work, representation capacity, per-row work and
all overhead remain explicit hypotheses. The full audit now checks 1,650
declarations / 879 theorem declarations. The ROBDD optimizer and native protocol
state are still outside an end-to-end kernel theorem.


The follow-up benchmark has 147 sequential runs and 1,470/1,470 correct answers
(672 UNSAT), including larger chains, distant edits, 11 public SATLIB instances
and distribution shifts. An endpoint edit recomputes one of 33 buckets; a bridge
can affect them all. Direct symbolic proposals improve the distant-edit stream
from 566.34 ms to 377.54 ms, while checked solving takes 283.35 ms. All public
instances exceed the interface width cap and use checked fallback. Adaptive
selection reduces wasted interface work but does not beat checked solving here.
Every mode has the same 8 MiB logical-page cap; no run reaches it. Total RAM and
WAL storage are not bounded by that cap. Full results, peak allocations, archive
costs, source hashes and uncertainty limits are retained in the scaling study.

Remaining obligations: avoid global plan/source copying and final scans; bound
or predict affected regions under edits; improve symbolic intermediate size and
variable order with charged matching; reuse general verified proof fragments;
prove native protocol/optimizer refinement and full machine costs; bound total
process-tree memory; evaluate modern application suites and stronger routing.
The uniform polynomial coverage/acquisition/representation/verification bounds
for all SAT instances remain unproved. No unrestricted lower bound is claimed.


Final verification: 106 tests pass; all 27 earlier manuscript proof texts are
unchanged, and the conditional scaling proposition adds one proof. The rebuilt
45-page PDF has no overfull boxes or unresolved references and was visually
reviewed. A new backup preserves the live archive; all 2,485 old results, 645
proofs and other older rows remain unchanged, along with 44 previous experiment
files. There are now 2,840 results and 774 proofs, including 355 revalidated
current-engine inputs independently audited. Validation/source hashes and row
fingerprints are recorded with the scaling study.


## Six-task follow-up: durable reuse and concrete restricted updates

All six implementation tasks have now been addressed. The following table keeps
the completed work separate from stronger unproved guarantees.

| Task | Implemented and checked | Remaining boundary |
| --- | --- | --- |
| 1. Overhead | One durable transaction per interface operation; native batches; persistent AVL bucket maps; write-free width preflight. | Source/order scans, full context checks and SQLite costs remain. No O(delta) whole-query claim. |
| 2. Balanced expansion | Explicit persistent binary-relation chain API, eager four-entry summaries, checked joins, logarithmic replacement ledger, preserved roots. | Recognition of arbitrary SAT, general graph edits and full witnesses are outside the bound. |
| 3. Symbolic work | Fused conjunction/abstraction, safe-point GC with root remapping, explicit variable-order metadata and experiments. | No general intermediate-size or efficient-order guarantee; exponential cases remain. |
| 4. Proof fragments | Native per-fragment hinted RUP checks, permanent-premise dependencies, final current-root check, checked restart replay; Lean soundness. | Full certificates still traversed/serialized; protocol/adapter refinement and unrestricted proof-size bounds remain. |
| 5. Routing/resources | Structural features, early screening, reserved fallback budgets, process-tree RSS and full scratch sampling. | No universal route gain/regret bound or hard total RAM/WAL cap. |
| 6. Proof/evidence | 114 tests; 1,828-declaration/941-theorem audit; fixed held-out counter and selected 2026 artifact inputs; manuscript and literature reconciliation. | Small selected suites, no competitive modern-solver benchmark, no full machine-cost proof or unrestricted polynomial SAT result. |

The study records 2,259 correct answers (1,188 UNSAT) and 30 archive-cap errors
from 2,289 attempts across 210 runs. All errors occur at the last two selected
towers increments in five full-input modes. Delta modes complete all twelve;
no wrong answers or timeouts occur. Incomplete stream totals include failures
and must not be used as full-solution times. Sampled RSS reaches 329.14 MiB,
with missed reads and finite sampling intervals explicitly retained.

The separate chain study confirms ten compositions and eleven node writes for
one replacement in a 1,024-edge chain; complete witness checking visits all
1,024 edges. The construction is an established finite-monoid dynamic word
problem (Frandsen et al. 1997; Amarilli et al. 2021), not a novel complexity bound.
The manuscript also cites CUDD relational products and Schreiber et al. 2026
for distributed incremental proof checking. Standard reuse principles are not
presented as new results.

The live archive retains all 3,195 previous results, 903 proofs, and other old
rows. New revalidation/audit adds 355 answers and 129 proofs, for 3,550 total
results and 1,032 proofs. All 63 historical experiment files are unchanged.
The reports are in `experiments/results/followup/`; previous studies stay intact.

## Current work on gaps 1, 3, 4, 6, and 7

The numbering below is the gap list selected for this task; earlier milestone
numbering above is retained as history.

| Gap | Completed change | Remaining limit |
| --- | --- | --- |
| 1. Beyond Boolean chains | Supplied bounded Boolean layers, checked finite-state joins, exact summaries, preserved old leaves and roots, explicit width-dependent replacement ledger. | No arbitrary-graph decomposition or unrestricted SAT width/acquisition bound; table size is exponential in layer width. |
| 3. Global planning metadata | Persistent source reference counts, rank/order, constants and bucket indexes; local named deltas avoid whole-source comparison and plan copying. | Full active-context validation, full witnesses and certificates remain global; an edit may propagate across all buckets. |
| 4. Compression and active memory | Payload-bounded proposal caches, symbolic root trimming/node caps, charged safe-point WAL checkpoint attempts; all archived evidence retained. | Serialized payload is not heap/RSS. Transient objects, native memory and blocked WAL checkpoints prevent a hard total bound; archive growth remains. |
| 6. Failure-aware routing | Recent completed-answer cost with a query-budget penalty per failure; failed-only routes cannot win by being fast. | Periodic exploration still retries; no universal speedup or regret theorem under arbitrary shifts. |
| 7. Broader comparable evidence | Frozen full-formula inputs across modes, enabled online learning, separate delta/layer evidence, new artifact families and sampled watchdog thresholds. | Small application prefixes, selected SATLIB examples and a toy prediction family remain limited evidence; sampled thresholds are not hard memory limits. |

The native audit exposed a concrete refinement pitfall: Lean arity expansion
could delay a function-valued `freeze` until lookup. The earlier mathematical
summary and replacement proofs remained sound, but the compiled representation
could repeat acquisition. Both chain and layered joins now materialize data
before creating lookup closures. Generated C confirms that ordering. This is
implementation evidence, not a formal compiler or complete runtime-cost proof.
The development timeout is retained with the new study. All 119 tests pass on
the corrected build; the transitive Lean audit checks 1,957 declarations and
991 theorem declarations without admits or new axioms.

A relevant published extension is Amarilli, Barloy, Jachiet and Paperman (MFCS
2025), *Dynamic Membership for Regular Tree Languages*,
[DOI 10.4230/LIPIcs.MFCS.2025.8](https://doi.org/10.4230/LIPIcs.MFCS.2025.8).
It establishes an O(log n / log log n) relabeling-update bound for a fixed regular
tree language. The fixed language, tree representation and permitted edits
matter. Implementing that richer interface is a possible next restricted step;
it does not remove unrestricted SAT's missing structural hypotheses.

## Post-implementation gap analysis

This analysis reviews commit `ee3ba62` and adds deterministic diagnostics in
`experiments/results/gap-analysis/`. It does not change the solver or reinterpret
an operation counter as total execution cost. The seven identifiers below keep
1/3/4/6/7 aligned with the preceding selected tasks; 2 and 5 name the remaining
cost and certification obligations.

Three concrete mechanisms now deserve priority over adding another instance
family. First, semantic equality does not stop general-plan propagation. Second,
the native layered-cache policy can repeatedly discard the entire useful working
set. Third, a late query failure can create both a successful and a failed route
observation for the same request. These are distinct from the open uniform
complexity question.

| Gap | Current evidence and remaining obligation | Concrete completion criterion |
| --- | --- | --- |
| 1. Uniform structural coverage | The layered family is supplied to the solver. At Boolean width b, summaries use 2^(2b) cells and the abstract composition budget is 2^(3b). No general-CNF recognizer/compiler or bound on width across arbitrary edits is proved. | Define a broader promised family, check its decomposition, and charge recognition, compilation, expansion count and updates. Logarithmic width in input length could support a polynomial restricted bound; that width guarantee must be proved, not assumed for arbitrary SAT. |
| 2. Executable cost refinement | `replacementWork` charges q^3 by definition and proves the resulting recurrence. This does not prove that native calls, table allocation, bit arithmetic, hashing, persistence and replay obey that ledger. The previous materialization defect illustrates the distinction. | Prove bounds for a costed executable composition and tree update, connect them to the supplied representation, then add explicit service/replay terms. Keep compiled-runtime costs separate until justified. |
| 3. Semantic reuse and global work | Version-three metadata avoids whole-plan copies. However, propagation compares output evidence identities. Equal projected truth tables with different parent identities can invalidate every bucket. Full context traversal, full witnesses and certificate extraction remain global; lazy recursion falls back at depth 256. | Separate semantic relation identity from current provenance, certify equality before stopping value propagation, preserve assumption/deletion checks, and use iterative evaluation. For a decision-only interface, establish an explicit bound on context updates as well as summary updates. |
| 4. Active retention and archive costs | Small Python payload caches preserve historical evidence, but native retention has a separate reset policy. A 256-edge width-four working set exceeds its reset threshold and replays all 511 nodes on every query. Fixed active limits still do not bound RSS, transient allocations, WAL or the growing archive. | Manage the live native working set explicitly, reuse unchanged verified root answers, and report what happens when the working set exceeds budget. Charge replay/eviction amortization. Preserve durable history in a separately budgeted archive; define refusal or storage expansion at capacity. |
| 5. Request-to-proof connection | `Tree.Valid` and summary exactness are proved. The layered protocol does not yet have a complete theorem connecting JSON masks, logical length, identity padding, endpoint restrictions, witness extraction and persistent updates to the user's source formula. General proof sizes and restart costs are unbounded here. | Prove protocol invariants, mask conversions, witness soundness/completeness and source-compilation correctness. Extend negative-proof context checks through edits and replay; do not assume polynomial UNSAT certificates for unrestricted instances. |
| 6. End-to-end arbitration | The route selector chooses only checked versus interfaces. It does not gate predictor/portfolio attempts. Portfolio `native_prepare` takes a median 10,806.82 ms on the chronological stream versus 52.23 ms for checked mode. A post-solve accounting failure also produces two contradictory observations for one request. | Record one final outcome per request; distinguish attempted path and fallback. Add proposal-specific measurements and budgets with reserved fallback capacity, then route among relevant mechanisms using complete measured cost. Test late failures and workload shifts. |
| 7. Evidence and attribution | The main study is reproducible and preserves failures, but application inputs are tiny all-UNSAT prefixes. Public examples were previously used during development. Prediction gains are on signed units, with no accepted prediction on the public shift. Repeated-relation layers mask native working-set pressure. | Freeze genuinely unused, larger mixed-label application streams; include distinct-relation and adversarial edits, cold/warm/restart modes, matched incremental baselines and a cheap deterministic signed-unit heuristic. Use enforced total-resource limits if claiming them. |

### Reproduced semantic-propagation gap

A 16-edge XOR chain is satisfiable. Replacing its first XOR by equality leaves
the first eliminated relation over variable 1 equal to `[true, true]`. The
projected scope and complete values are identical before and after the edit.
The evidence identity changes, because it records different parents. The current
planner therefore recomputes all 17 buckets: zero reused buckets and zero
propagation stops. No incorrect SAT answer occurs.

This exposes the difference between sharing a compressed relation payload and
using semantic equality to stop value propagation. A repair must retain new
provenance even when the value is unchanged. Reusing an old proof after deleting
one of its assumptions would be unsound. Full witness output may also need to
change even when the root decision is unchanged.

Evidence: `semantic.json`; implementation: `solver/planning.py` (`output !=
old_output`), `solver/interfaces.py` (`project_node` and `run`).

### Reproduced native replay gap

Use 256 distinct random relations with a planted zero-state path. At width three,
the first query registers 511 native nodes, a replacement registers nine, and an
unchanged query registers zero. At width four, the reset threshold is 187 nodes.
The first query registers 511 nodes, already exceeding that threshold. Both the
replacement and the unchanged next query reset and register all 511 again.
The unchanged query reports zero Python compositions but 511 native definitions.

This is a performance and accounting gap, not a refutation of the abstract
logarithmic tree-replacement theorem. It also shows that the reset threshold is
not a hard occupancy bound: the pending batch can exceed it. Raising the number
alone does not resolve the general working-set/memory tradeoff. An unchanged
verified root can be memoized; larger edits need an explicit retention/replay
policy with stated memory assumptions.

Evidence: `replay.json`; implementation: `solver/layered.py`, lines 97–117.

### Reproduced routing-observation gap

Inject a failure in `archive_usage` after solving one satisfiable query. The API
raises an error, but `route_observations` contains success=1 and success=0 for the
same attempted route. `solve` records success before storage accounting, then
its exception handler records failure. This is a fault-injection result, not a
failure observed in the timed study. The accepted solver result can remain
correctly persisted while the service request fails; those outcomes need
separate meanings rather than two indistinguishable request observations.

Evidence: `routing.json`; implementation: `solver/persistent.py`, lines 466–481.
The existing score regression tests inject route observations directly and do
not cover this late-failure path.

### Priority and interpretation

The fastest useful sequence is: repair final-outcome recording; stop native
reset/replay on unchanged working sets; separate semantic value propagation from
provenance maintenance; then remove recursive depth limitations and bound full
context checks. Validate each against these diagnostics before enlarging the
benchmark. Exact-count claims should include native replay, not only Python
composition counters.

For the paper, the main theoretical gap remains uniform resource control.
Inductive exactness at each finite stage does not establish polynomial
construction, representation, verification or cumulative expansion cost. The
current results support a perspective on accounting for reusable reasoning and
restricted verified constructions. They do not establish a new general SAT
complexity result or a universal System 1/System 2 speedup.

## Seven-priority implementation follow-up

The follow-up preserves the preceding diagnostics as historical evidence.
Implementation commits `d3321a7`, `580e1b1`, and `b080a39` address the practical
priorities before broadening the experiment. None closes the unrestricted
uniform-complexity question.

| Gap | Implemented progress | Remaining obligation |
| --- | --- | --- |
| 1. Structural coverage | Native CNF compilation checks a supplied disjoint ordered partition, width 1–4, with each clause confined to adjacent blocks. A second pass binds source edges and identity padding to the checked root. | Discover useful partitions; cover broader decompositions and edits; prove width/coverage/acquisition bounds for the promised family. No arbitrary-SAT width guarantee follows. |
| 2. Executable cost | A costed executable composition and replacement reference returns counts and the same values as production operations. Lean proves at most `q^3` middle-state tests per join and `h+1+h*q^3` tests plus node events per replacement. | Refine allocation, bit arithmetic, compiler execution, hashing, IPC, persistence and replay costs. This is not a whole-service machine-cost proof. |
| 3. Semantic reuse | Complete native equality checking and checked parent matching let downstream factors reuse row values while retaining new provenance. Iterative Python evaluation removes the depth-256 limit. | Evidence IDs still propagate; final context checks, witnesses and certificates can remain global. Prove the equivalence/row-cache state invariants and reduce context work without invalid assumption reuse. Symbolic and native capacity limits remain. |
| 4. Retention | Native layered retention keeps a complete live dependency closure, reports logical cells, and refuses a working set that exceeds its configured cap. Old versions remain durable. | Bound actual RSS/transient allocation and physical storage, rather than selected cells/pages; charge history replay and unbounded archive growth. |
| 5. Request/proof connection | Lean proves exact rowwise relation comparison, accepted full-tree witness traces/lengths, prefix/suffix composition, identity-padding preservation, local CNF clause semantics and mathematical source binding. Runtime checks reject forged shortened lengths and source/root mismatches. | Complete the refinement through JSON, partition construction, hash maps, Python, SQLite, truncated witnesses and restart state. General UNSAT proof-size bounds are not supplied. |
| 6. Arbitration | Final outcomes are logged at most once. Proposals have separate calls, outcomes and elapsed measurements, with at most 250 ms/10% reserved for all attempts before fallback. | Learn cost-sensitive gates among prediction, portfolio and solving; bound feature/model/replay overhead and failures. Budget reservation alone gives neither optimal routing nor a universal speedup. |
| 7. Evidence | A frozen study uses previously unused mixed-label circuit instances, later application horizons, a deterministic polarity baseline, matched live/restarted proof modes, distinct width-four relations, semantic edits/deletions and source compilation. All failures are retained. | Broader representative workloads, more repetitions, current competing solvers, hard comparable total-resource limits and independent replication. |

The semantic diagnostic now establishes one equality and rebinds 16 successor
projections after replacing the first XOR by equality in a 16-edge chain. It
performs two combination-row acquisitions while still updating all 17 evidence
buckets. This is a reduction in value computation, not a constant-time complete
update. Tests include adding a contradiction, deleting a necessary assumption,
branching from the old version and restart.

With 256 distinct width-four relations, initial registration needs 511 native
nodes, replacement nine, and an unchanged query zero. At a cap exactly equal to
the live set, nine obsolete native entries are evicted on replacement; the new
root fits without replaying all 511. A smaller cap refuses the request, while the
saved roots remain queryable after reopening with sufficient capacity.

The full-tree witness and source-binding theorems concern explicit mathematical
objects. Their presence does not certify every executable protocol branch. The
current audit includes 2,090 declarations and 1,047 theorem declarations, with
no admits or added axioms. The distinction between these proved components and
the remaining implementation refinement is part of the result.

## Gap analysis after the seven-priority follow-up

This 8 November 2026 analysis reviews runtime commit `269f095`. The final-outcome
logging defect, reset thrashing on unchanged layered roots, and Python's
depth-256 lazy-evaluation limit have targeted repairs and passing regressions.
They should not be listed as unchanged open defects. Remaining practical gaps
concern work outside relation evaluation, source coverage and proof refinement.

The new [diagnostic audit](../experiments/results/priority-gap-audit/README.md)
records temporary-store experiments and SQL deltas. The original priority study
revalidates: 1,047 correct completions, 105 resource failures and no wrong answers
among 1,152 attempts. The ten priority regressions pass again. These checks are
neither a complete correctness proof nor an independent replication.

### Semantic reuse works, but provenance updates remain global (gap 3)

The 16/64/320-edge equal-projection edits acquire only five native rows and two
combination rows. Nevertheless, they rebind 16/64/320 successor projections and
change 17/65/321 buckets. Existing three-repeat median edit times are
8.811/33.920/240.298 ms. The operation counts, rather than these few timing points,
identify the remaining global work.

The new audit finds **zero new `interface_relation` objects** in all three edits.
At 320 edges it nevertheless inserts 3,430 knowledge objects with 550,879
compressed payload bytes and grows logical database allocation by 1,556,480
bytes. Most objects are persistent-map nodes, interface evidence and elimination
buckets. Another 639 row-cache records store checked values under new evidence
identities. The intermediate counter reports 3,429 objects because the final
result is inserted after it is sampled.

Behavior already shares well here. The remaining question is whether evidence
can be maintained locally. New parent identities still flow through the suffix
(`solver/interfaces.py:398`, `solver/planning.py`). Each native rebind enumerates
all interface assignments, even if few rows are known
(`formal/OracleMachines/InterfaceProtocol.lean:250`). General expansion also
enumerates the manifest, reconstructs SAT witnesses and extracts full negative
proof DAGs. The native negative-context check uses list membership for every
reachable leaf; distinct leaves and active identities can require quadratically
many identity comparisons.

**Next obligation:** maintain shared semantic values separately from versioned
derivations and checked context roots, then update provenance and context by
deltas. Prove that removed assumptions cannot justify a new result. Add a
decision-only general-expansion API and charge full witness/certificate output
separately. Measure new SQL bytes and context visits, not only computed rows.
Simply stopping parent-identity propagation would invalidate provenance.

### Retention scans the live graph under pressure (gap 4)

The repair reduces new native definitions to 9/11 per 256/1,024-edge edit.
At a cap equal to the live closure, however, **each of six consecutive edits
visits all 511/2,047 live nodes**, reading 554/2,100 nodes in total. Doubling the
cap reduces those edits to zero retention visits and 43/53 node reads. Unchanged
queries require no closure scan at either cap.

`solver/layered.py:110` builds the live set, sorts retained IDs and sends them
all to native code. `LayeredProtocol.retain` rebuilds a map and checks dependency
closure. Logarithmic summary recomputation is therefore not a logarithmic
complete update at the tight cap. Headroom postpones this work; six edits do not
establish long-stream amortization. Historical branch selection and restart have
separate replay costs. General factor retention still resets its whole worker
at a separate threshold (`solver/interfaces.py:495`).

**Next obligation:** maintain live reachability incrementally for specified
active roots, or prove a batch-retention amortized bound with explicit headroom
and branch-switch assumptions. Test many eviction cycles and report total
visits, transport and native work. Retain durable history with an explicit
archive-capacity policy. Logical cells/pages do not bound actual RSS, transient
allocation or physical disk.

### Source-bound incremental CNF updates are missing (gap 1)

The compiler checks a supplied disjoint ordered partition with blocks of at most
four variables and clauses confined to neighboring blocks. It neither discovers
the partition nor covers general bounded-width decompositions. For example,
clauses `(x OR y_i)` with more than eleven distinct neighbors of `x` cannot fit
this width-four partition: every neighbor must fit in `x`'s block or its two
adjacent blocks. These formulas are easy to satisfy by setting `x` true. The
restriction therefore excludes some very simple families.

More immediately, `layered_cnf` requires a **fresh full source request**.
It compiles twice and compares every source edge against the checked tree.
Generic `layered` edits can reuse its state, but their new answers concern
edited relations and have no new binding to an edited original CNF. The source
API has no end-to-end logarithmic update guarantee.

**Next obligation:** introduce persistent checked source versions, clause-to-block
indexes and validated local source deltas. Preserve source identity through
replacement, deletion and restart. Prove this precise family before extending
to overlapping path/tree decompositions. Charge initial decomposition and
compilation. An unrestricted-SAT width or compactness guarantee remains a
research premise, not an implementation detail.

### Proved components do not yet prove the stateful service (gap 5)

The Lean results establish local clause semantics, mathematical source binding,
full-tree witness traces, and value equality of costed and production tree
operations. They do not establish the complete executable pipeline.

The most consequential next invariant concerns native factor equivalence classes
and transferred rows. `factorEquate` and `factor_rebind` maintain mutable hash-map
state; semantic lemmas justify the intended operations, but no theorem preserves
their store invariant through every protocol transition. JSON/partition
construction, native memo state, truncated witnesses, SQLite/Python recovery and
restart remain obligations. An axiom audit establishes proof hygiene, not that
every runtime branch satisfies its specification. These diagnostics found no
wrong answer.

**Next obligation:** prove that every stored row equals evaluation of its current
immutable definition and that every equivalence class denotes one relation on
its named scope. Prove preservation under define, acquire, equate, rebind and
reset; compose this with source/context binding and restart. State the remaining
trusted runtime boundary. General short UNSAT certificates are not assumed;
a proof-size refusal is not an UNSAT verdict.

### The complete cost ledger remains unproved (gap 2)

`LayeredCosts.lean` proves at most `q^3` tested middle states per join and
`h+1+h*q^3` tests/node events per reference replacement. It excludes allocation,
bit arithmetic, masks, hash maps, JSON, Python/SQL work, retention, source binding
and replay. The diagnostics show that these exclusions can dominate. Equality
also costs work to discover; `factorClass` has neither path compression nor
union by rank, and its cost is absent from the row-acquisition count.

**Next obligation:** implement a ledger for these terms and prove a restricted
service bound with explicit resident-state, output and restart conditions.
Measure actual new payload bytes separately from bytes serialized:
`relation_payload_bytes` increases even when SQL deduplicates every relation.
Functional equivalence of counted and production operations alone supplies no
native instruction or bit-machine bound.

### Budgeted speculation is not cost-sensitive selection (gap 6)

At-most-once final observations and the shared proposal deadline are implemented.
The limit is 250 ms or 10% of time remaining **when proposals start**, whichever
is smaller. Retrieval and feature/model work happen beforehand; training and
archive work happen afterward. A proposal timeout kills the native worker and
can incur later replay. These costs are measured in elapsed time but are not
bounded by the proposal budget. The router chooses checked versus interfaces,
not which predictor/portfolio actions are worthwhile.

The manuscript's fixed-policy break-even proposition does not directly prove
performance of this adaptive service. It excludes online updates and requires
the same baseline on fallback. An adaptive guarantee must charge updates and
interference as well as benefits from accepted answers.

**Next obligation:** gate mechanisms by avoided solver cost versus all incremental
costs, including worker-state loss. Keep an always-checked option and test workload
shifts. Regret or overhead guarantees need explicit workload/resource assumptions;
a timeout alone proves no universal speedup.

### Application evidence is insufficient for an efficiency claim (gap 7)

Chronological median times are 649.47 ms learned, 458.58 ms checked and 263.01 ms
for the deterministic polarity baseline. The learner accepts 30/32 signed units
per repetition; polarity accepts all 32. Neither accepts a public-shift or
application proposal. This supports a synthetic heuristic benefit, not a
learning-specific gain on those public applications.

Every service mode completes 9/24 application attempts, on different subsets.
Full-stream times include failures and cannot rank equivalent completed work.
Direct CNF completes 24/24 with a different certification/storage boundary.
All process-tree RSS reads failed, leaving no valid RSS peak measurement.

Representation is a concrete bottleneck: the saved Towers-38 CNF has 517,974 bytes,
while unary formula encoding needs 181,707,058 bytes, roughly 351 times as much.
Every service mode rejects it at the 8 MiB input cap. Full-study failures comprise
21 input-cap, 39 archive-cap, 30 proof-size and 15 deadline failures. These are
resource failures, not SAT/UNSAT decisions or complexity lower bounds.

**Next obligation:** verify a compact source interface, then compare matched
certified baselines on the same completed inputs. Report completion rates,
paired costs, storage growth and functioning RSS observation. Freeze a new
holdout after choosing the policy; add repetitions and realistic edit, restart
and branch streams. Universal System 1/System 2 superiority is not established.

### The theoretical premise and recommended order

Exact finite-domain expansion does not imply uniform polynomial construction.
A cost bound in the number of stored components does not bound how many
components or expansions cover every length-n SAT instance. The missing invariant
must jointly control width, acquisition, representation size, coverage schedule,
maintenance and evaluation. The manuscript states these conditions; it does not
prove them for unrestricted SAT. This audit supplies neither that proof nor a
counterexample to the conditional mathematics.

The practical order is **3, 4, 1, 5, 2, 6, 7**: reduce provenance and retention
work, connect local edits to source CNF, prove the new state transitions, complete
the restricted cost account, improve selection, then test the resulting claim.
Maintain regression checks throughout. Compact general input encoding is an
independent prerequisite for meaningful application evaluation and can precede
the final experiment.

A concrete next theorem should cover decision-only local CNF edits in a supplied
fixed-width decomposition: preserve checked source identity and current-context
validity, include retention and evidence in the full-update bound, and give
explicit additional terms for restart, history selection and full output. This
would strengthen the resource-accounting contribution without assuming a solution
to P versus NP.

## Source-update implementation after the audit

Commits `57a6d23` and `07354c8` address the concrete restricted target. The
general seven-item audit above remains the record of the starting point.

- **Retention:** live references and native incoming-reference counts now
  support incremental eviction. In the 256-edge tight-cap regression, 128
  consecutive edits each need nine evictions and at most 34 live-reference
  updates, without a 511-node closure scan. Old versions remain archived.
- **Provenance and source binding:** `source_cnf` stores current clauses in the
  same balanced tree as their relations. Warm bucket replacements change only
  the source path; the native checker verifies the requested edit and unchanged
  subtree identities. Empty replacement buckets delete clauses. Partition changes
  still require initial compilation of a new family.
- **Formal connection:** native `CheckedSource` nodes contain proofs aligning
  cached trees with the current local CNF. The executed decision has exact
  positive/negative theorems. Source edits preserve all unselected leaves, and
  the counted executable reference has the bound stated in `SourceInvariant.lean`.
- **Accounting:** source metrics distinguish transport bytes, serialization,
  newly inserted raw/packed payloads, node reads, patch/binding visits, reference
  work, final logical cells and transient reservation. Complete elapsed phases
  are measured. Archive and actual-memory costs are not inferred from cell counts.
- **Evidence:** all 141 tests pass; Lean audits 2,279 declarations and 1,106
  theorem declarations. The [matched source study](../experiments/results/source-updates/README.md)
  compares local updates with full rebuilding under the same source checker.

This addresses gaps 1/3/4 on the supplied adjacent-block family and strengthens
gaps 2/5. It does not optimize the general factor-DAG provenance suffix or prove
its mutable row/equivalence invariants. Complete JSON/global-mapping/storage
refinement, machine costs, archive-growth policy, cost-sensitive gating and
unrestricted coverage remain open. The new benchmark measures a restricted
structural mechanism, not a learning-specific or general SAT speedup.

## Indexed context and upgrade preservation follow-up

The next review closes three implementation gaps:

- General negative-proof context checks index the active identities once.
  Lean proves exact agreement with the old list-membership condition, including
  duplicates and arbitrary order. Membership probes are bounded by the proof's
  leaf count. The native response and Python ledger expose index-entry and probe
  counts. The graph traversal and context construction remain global, and hashing
  costs are not assumed constant in a worst-case machine bound.
- Source versions from earlier checker namespaces are now replayed under the
  current checker. Their stored verdicts are not trusted. Current-engine rows
  are added only after checked replay; previous rows and objects remain intact.
  A source-ID index supports the older-namespace lookup. Engine upgrades can
  still require full native replay and do not have a warm-update guarantee.
- Database cleanup covers configuration, migration, and later initialization
  failures. Two independent test-owned connection leaks are also fixed. The
  full suite passes 144 tests without resource warnings. Lean audits 2,290
  declarations and 1,113 theorem declarations without admits or added axioms.

The next highest-value obligations are the source compiler's global-ID mapping
proof, reference-count/eviction invariants, and the general factor row/equivalence
store invariant. After those, measure alternative representations for the global
provenance path and remove the unary-input expansion in application experiments.
These tasks can make the stated restricted guarantee more complete. They do not
establish efficient decompositions or compressed exact models for arbitrary SAT.

## Original-variable mapping proof follow-up (8 November)

The next checkpoint closes the local mapping obligation identified above.
`SourceMapping.lean` replaces unchecked position pairs with dependent entries
that prove the original block lookup and width bound. An executable alignment
check proves completeness for every supplied array coordinate. Global valuations
encode into bounded block states, and arbitrary block states yield agreeing
global valuations. These conversions include empty/short blocks and unused IDs.

The native initial compiler now uses proof-carrying clause translation. Its
local-edit compiler returns a `CheckedCNF` indexed by the requested original
clauses. Lean proves evaluation equality and SAT/UNSAT equivalence for each
translated bucket. Iterative accumulation is tied back to the request by array
equality checks. This is actual runtime construction of the proved values.

All 148 tests pass without resource warnings. Lean audits 2,477 declarations and
1,188 theorem declarations without admits or added axioms. Both compiler paths
agree with 9,520 exhaustive boundary assignments across 112 local CNFs. Additional
tests cover sparse IDs above 64 bits, slot permutations, missing/duplicate/zero
IDs, locality violations, empty clauses versus empty buckets, short and empty
blocks, old versions after restart, and long iterative translation inputs.

Resource limits remain explicit: the layout check makes an extra pass over
blocks and variables. Builders accumulate original arrays and compare them with
the input. Initial grouping scans literal positions before translation. These
linear entry visits, temporary arrays, ID hashing/comparison and allocation are
outside the existing relation-evaluation counter. We claim no speedup from this
proof change and preserve the earlier timing study as historical evidence.

Highest-priority remaining work:

1. Compose local translation with the **global grouping loop and source-tree
   binding**. Every original clause must reach exactly its intended edge; native
   node/layout identities must retain the proved meaning through requests and
   edits. The current local theorem does not prove that end-to-end property.
2. Prove the **native incoming-reference and Python live-reference invariants**
   through shared children, replacement, failure, eviction and replay. Current
   pressure/branch/restart tests remain evidence rather than a state theorem.
3. Prove the general factor **row/equivalence-store invariant**. The restricted
   adjacent-block compiler does not settle the general factor-DAG obligations.
4. Add mapping, checking, retention, serialization and archive access to an
   explicit restricted ledger; distinguish entry visits from bit-machine costs.
5. Replace unary general input encoding before broader application evaluation;
   retain failures and compare matched certified boundaries. Cost-sensitive
   routing, hard total-memory bounds and unrestricted coverage remain open.

Runtime checkpoint `dd0c44c` is committed and pushed. The manuscript and the
[verification record](../experiments/results/source-mapping/README.md) include
archive revalidation: all 355 distinct generic inputs pass; five older source
versions are checked under the new engine and after restart. Every old row in
all 21 tables and all 142 prior experiment files is preserved. The archive now
contains 5,325 generic results and 1,677 refutations. Historical timing results
remain tied to their original runtime; this checkpoint has no new timing study.

## Complete source grouping and path semantics (8 November)

`SourceGrouping.lean` closes the global flat-CNF grouping part of the preceding
priority. `GroupedCNF` contains both original and translated buckets, fixed edge
counts, a permutation proof preserving every original clause occurrence, and
the per-edge evaluation equalities. The actual grouping loop uses the proved
append operation and checks its accumulated input against the supplied CNF.
Repeated clauses and empty clauses cannot disappear from the proved partition.

The whole original CNF is satisfiable exactly when **one consistent sequence**
of bounded block states satisfies every compiled relation. Local nonemptiness
alone is insufficient. New path/sequence lemmas connect that sequence to the
composed relation. `CompiledSource.bound_tree_exact` and `bound_tree_unsat` then
connect the original CNF to a valid tree summary **assuming** exact ordered leaf
binding and identity padding. That assumption is explicit and is not discharged
by calling a theorem about the reference tree alone.

The native compiler now returns the grouped proof indexed by the supplied CNF.
This proves correctness of successful typed compilation, not completeness of
acceptance for every promised input and not refinement of JSON decoding. Warm
edits retain the existing local compiler; no full-source regrouping is added to
that path. Initial grouping adds a temporary array of clause references and a
final equality check, outside the relation-evaluation ledger. Proofs are erased;
runtime comparisons, allocation and arbitrary-size IDs still cost work.

The next highest-priority obligations are now:

1. **Native source-tree binding and identity preservation.** Carry original-source
   meaning, layout, start and span through stored nodes and joins. Prove that
   initial binding, patches and replay supply the leaf-binding premise above.
   The current runtime checks these facts, but has no complete state theorem.
2. **Reference-count/eviction invariants** across shared children, failures,
   historical branches and replay, in both native and Python stores.
3. **General row/equivalence-store refinement**, including source/context binding;
   the adjacent-block result does not establish general factor-DAG invariants.
4. **Complete restricted accounting**, including grouping/equality passes,
   retention, transport and archive access, with bit costs distinguished from
   entry counts. Acceptance completeness and cap behavior also need specification.
5. **Compact general input and matched application evidence**, followed by
   cost-sensitive selection. Hard total-resource and unrestricted-coverage
   guarantees remain open. This proof checkpoint makes no timing claim.

Validation: all 152 tests pass without resource warnings; Lean audits 2,562
declarations and 1,233 theorem declarations without admits or added axioms.
The new checks cover all 11,680 complete assignments of 60 generated global CNFs,
exact bucket contents and occurrence counts, and service decisions/witnesses.
They include individually nonempty relations with no common path, repeated empty
clauses, final-block units, the 65,537-block cap and 12,000 repeated clauses.
Runtime checkpoint `75483cd` is committed and pushed. The manuscript and the
[grouping verification record](../experiments/results/source-grouping/README.md)
include archive revalidation: all 355 distinct generic inputs pass semantic audit;
all five old source versions pass current-engine adoption and restart. Every old
row in all 21 tables and all 150 earlier experiment files is preserved. There
are now 5,680 generic results and 1,806 refutations. Historical timing evidence
remains unchanged and tied to its original runtime.

## Executable complete-source binding (8 November, third hourly follow-up)

`SourceBinding.lean` closes the initial complete-source part of priority 1.
Its executable constructor checks the actual stored tree's width and ordered
leaves, including each identity-padding leaf. On success it returns a
`BoundCompilation` carrying the binding premise, tree validity and exact
comparison-call count. Its positive and negative decision theorems concern the
complete original CNF. Both native full-source queries and initial source-version
binding use this result. Original-clause/provenance checks remain in place.

The accumulator traversal is proved to preserve leaf order; it visits logical
tree occurrences even when native nodes are shared. The tail-recursive scan is
proved to accept exactly equal leaf lists and to make one relation-comparison
call per logical leaf on success. Both Python APIs expose this count, together
with diagnostic row and source-evaluation reference bounds. Initial source-version
binding adds a source-relation evaluation pass. Allocation, original-source
indexing, bit/mask costs, endpoint queries, transport and storage are separate.
No speedup, RSS bound or complete native cost theorem is claimed. Warm edits and
current-source queries do not repeat the full scan.

All 156 tests pass without resource warnings; Lean audits 2,615 declarations and
1,259 theorem declarations without admits or added axioms. The new regressions
cover wrong ordered leaves despite a matching final answer, nonidentity padding
that composes to identity, dimensions, valid witnesses, counters at widths 1, 2
and 4, and 65,536 logical leaves sharing just 17 native nodes.

Remaining priorities:

1. **Preserve original-source identity through native joins, patches and replay.**
   Initial full binding now supplies its premise. Carry layout, start and span
   with original-source nodes and prove that mutable store transitions preserve
   them. The existing local-source invariant and transition tests do not yet
   establish that complete state theorem.
2. **Reference-count/eviction invariants** in native and Python stores, including
   shared children, failure, historical branches and replay.
3. **General factor row/equivalence-store refinement.** The adjacent-block
   proof does not discharge general source/context binding obligations.
4. **Complete restricted accounting:** the new scan counts comparison calls,
   not all relation evaluation, allocation, retention, serialization or bit costs.
   Acceptance completeness and cap behavior also need specification.
5. **Compact general input and matched application evidence**, then cost-sensitive
   selection. Hard total-resource and unrestricted-coverage guarantees remain open.

Runtime checkpoint `bc977eb` is committed and pushed. The manuscript and the
[binding verification record](../experiments/results/source-binding/README.md)
include successful revalidation/semantic audit of all 355 generic inputs and
checked adoption/restart of all five older source versions. Every old row in all
21 tables and all 158 earlier experiment files is preserved. The archive now
contains 6,035 generic results and 1,935 refutations. Historical timing evidence
remains unchanged and tied to its original runtime. The next run should start
with the node/layout/start/span invariant above, without treating this initial
full scan as a proof of later local transitions.

## Original-source nodes and consecutive joins (8 November, fourth hourly follow-up)

`SourceNodes.lean` retains the original clause arrays and their `CheckedCNF`
translations in a tree indexed by layout, width, start and height. Logical leaves
prove their edge is in range; padding leaves prove their edge is outside the
logical source and compile to identity. A join requires equal child heights and
the exact consecutive start. `CheckedNode` aligns this original tree with the
actual cached relation tree. The constructors carry the proof through registration
and joins. Join theorems preserve the complete original clause list and every
occurrence, including duplicate and empty clauses.

The executed node decision now has exact positive/negative theorems for the
original clauses stored in that node. Consistent paths use the indexed global
edge positions. Satisfying valuations extend through identity padding by repeating
the final block state; accepting paths yield agreeing global valuations via the
complete layout map. Clause flattening belongs to the specification and is not
executed by warm decisions or joins.

The native context's model map is typed by its exact layout and width. Registration
uses typed starts and the new constructors; replay rebuilds the same kind of
checked nodes. A context change resets both native maps, and failed batches expose
no partial state. These runtime paths have regression coverage. A formal theorem
relating the two named maps and JSON bodies is still missing.

Resource accounting records newly registered original-source nodes, clause entries
and literal entries. These diagnostics include replay and exclude duplicate
registrations. Original integer arrays now remain reachable from leaves alongside
JSON evidence and local translations. Joins retain child references; they do not
flatten the original source. The extra retention is not free, and entry counts
are not a byte/RSS or whole-runtime cost theorem. Warm unchanged queries report
zero new original-source nodes. No new timing claim is made.

All 159 tests pass without resource warnings, including 20 source-update tests.
Lean audits 2,751 declarations and 1,320 theorem declarations without admits or
added axioms. New cases cover nonconsecutive/reversed children, invalid dimensions
and layouts, failed-batch rollback, duplicate registration, shared-variable
conflicts, source-payload counts, sparse IDs above 64 bits, empty/short blocks,
branching, deletion and restart.

Next priorities:

1. **Named-store and requested-patch refinement.** The typed constructors now
   preserve layout, interval and original-source semantics. Prove correspondence
   between JSON identities, child references, relation-store entries and typed
   model entries. Then prove that `checkPatch` accepts the requested clause
   replacement and preserves every unedited original bucket. Correct semantics
   of the returned node does not alone prove it is the requested successor.
2. **Native/Python reference counts and eviction**, including shared children,
   failures, historical branches and replay.
3. **General factor row/equivalence-store refinement.** The new original-source
   proof remains specific to the supplied adjacent-block representation.
4. **Complete restricted costs and acceptance specification**, including original
   payload retention, mapping, transport, archive access and bit operations.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** Hard total-resource and unrestricted-coverage guarantees remain open.

Runtime checkpoint `b7dfcf4` is committed and pushed. The manuscript and the
[source-node verification record](../experiments/results/source-nodes/README.md)
include successful revalidation and semantic audit of 355 generic inputs and
checked adoption/restart of five saved source versions. Every previous row in
all 21 tables and all 166 earlier experiment files remains intact. The archive
now contains 6,390 generic results and 2,064 refutations. Historical timing data
remains tied to its original runtime. Resume with named-store correspondence and
requested-patch refinement; do not repeat or weaken the now-typed interval proof.

## Paired native maps and source metadata (8 November, fifth hourly follow-up)

`SourceStore.lean` closes the pointwise named-map part of priority 1. The native
context now contains one store carrying a proof that its relation and original
model maps have the same keys. At each key the stored relation tree is exactly
the model's checked tree. `BodyMatches` retains equations from the actual JSON
getters for identity, layout, width, start and height. Logical and padding leaves
also retain exact original-clause arrays, including order and duplicate/empty
entries. This is root metadata and leaf payload correspondence, not a complete
serialized graph theorem.

Initialization, paired insertion and paired erasure construct the invariant.
`lookup_exact` and `missing_exact` recover correspondence or matching absence at
any key. `lookup_semantics` connects a retrieved tree's positive and negative
decisions to satisfiability and unsatisfiability of its model's original clauses.
Native registration and deletion now use these operations. The proof needs no
store scan; parsed/header wrappers retain getter equations as erased proofs.
Temporary runtime wrappers, parsing, comparisons and reference-map operations
still cost work. No new timing, byte/RSS or complete machine-cost bound is claimed.

The generic and source stores share the same increment/decrement loops, including
underflow and referenced-node rejection. Refcount correctness is not assumed by
the map proof, and remains a separate theorem. Failed functional batches expose
no partial new state. New regressions check unknown/duplicate deletion midway
through a batch, child-reference rejection after rollback, parent-before-child
deletion, shared descendants, safe name reuse with different original clauses,
equal relations with distinct provenance, and missing-field rollback.

Remaining priorities:

1. **Named child links and requested-patch refinement.** Relate decoded left/right
   names and serialized masks to the actual typed children and summaries. Prove
   dependency lifetime/identity stability under permitted store changes. Then
   prove that `checkPatch` selects exactly the requested original-clause successor
   and preserves unedited buckets. Root metadata and map agreement alone do not
   prove this. `Store.insert` preserves correspondence even for replacement; the
   current protocol separately rejects changed bodies under a live identity.
2. **Native/Python reference counts and eviction**, including shared children,
   failed batches, historical branches and replay. The new erase proof covers
   paired map correspondence, not safety of dependency reclamation.
3. **General factor row/equivalence-store refinement.** The adjacent-block proof
   does not establish general factor-DAG or Python/SQLite invariants.
4. **Complete restricted costs and acceptance specification**, including decoding,
   header allocation, original payload retention, transport, archive and bit costs.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** Hard total-resource and unrestricted-coverage guarantees remain open.

Validation: all **162 tests pass**, including **23 source-update tests**, without
resource warnings. Lean audits **2,858 declarations / 1,367 theorem declarations**
without admits or added axioms. Runtime checkpoint `9cf68a4` is committed and
pushed. The manuscript and the
[source-store verification record](../experiments/results/source-store/README.md)
include successful revalidation and semantic audit of all 355 generic inputs and
checked adoption/restart of five older source versions. Every previous row in
all 21 tables and all 174 earlier experiment files remains intact. The archive
now contains 6,745 generic results, 2,193 refutations and 35 source-state rows
across checker namespaces. The historical timing study remains unchanged.
Resume with named child links/dependency lifetime and requested-patch refinement;
do not treat this pointwise root invariant as complete serialized-graph refinement.

## Named child registration and summary binding (8 November, sixth hourly follow-up)

`SourceLinks.lean` proves the registration-time portion of named child refinement.
The executed `readJoin` constructor returns a node with `JoinLinks` indexed by the
actual model map used in that call. It retains equations for decoded left/right
names, successful lookup of the exact child models, and equality to their checked
consecutive join. The original-clause theorem attributes every occurrence to
those children, even when distinct sources have equal relations. The decision
theorem requires one valuation satisfying both child sources; independent local
SAT answers do not suffice.

Fresh-key insertion preserves existing `JoinLinks`. Erasing a key preserves a
join when the key is neither decoded child. These are conditional transition
lemmas, not an established lifetime invariant for the full runtime. The latter
still needs to show that zero incoming references implies the erasure premise,
and that every live branch has links valid in the current map. The registration
proof is erased; it does not retain its model-map snapshot or perform a store scan.

`BodyMatches.summary` also binds the decoded mask to the model's actual cached
summary. Unlike the registration-snapshot predicate, this field is already part
of the paired native-store invariant and survives all its constructors. Leaf,
padding and branch registration retain proofs from their existing checks. No new
relation scan is added. Getter wrappers, comparisons and allocation still cost
work; there is no new machine/byte bound or measured speedup claim.

The join helper checks its child shape before the header start/height checks.
Malformed requests with several defects may therefore report a different first
error. Accepted request semantics and all resource caps are unchanged. Tests
exercise original-clause provenance under equal relations, missing/ill-typed
child names, live-identity rebinding rejection, incorrect but satisfiable masks,
and 12 parents removed in shuffled order while retaining their shared children.

Next priorities:

1. **Global named-link lifetime and requested-patch refinement.** Promote
   registration links to an invariant of every live branch. Prove fresh identity
   insertion and immutable duplicate handling; connect zero incoming references
   to the `erase_unreferenced` premise. Then prove that `checkPatch` selects
   exactly the requested successor and preserves unedited original buckets.
2. **Native/Python reference counts and eviction**, including shared children,
   failures, historical branches and replay. Tests are not an arithmetic proof.
3. **General factor row/equivalence-store refinement** and complete serialized
   replay/Python/SQLite correspondence.
4. **Complete restricted costs and acceptance specification**, including runtime
   parsing, allocation, payload retention, transport, archive access and bit costs.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** No unrestricted-SAT coverage or total-resource bound follows.

Validation: all **165 tests pass**, including **26 source-update tests**, without
resource warnings. Lean audits **2,874 declarations / 1,380 theorem declarations**
without admits or added axioms. The previous manuscript proof blocks remain
unchanged. Runtime checkpoint `6a73372` is committed and pushed. The manuscript
and [source-link verification record](../experiments/results/source-links/README.md)
include revalidation and semantic audit of all 355 older generic inputs and
checked adoption/restart of five source versions. Every previous row in all 21
tables and all 182 earlier experiment files remains intact. The archive now holds
7,100 results, 2,322 refutations and 40 source-state rows across checker namespaces.
Earlier timing evidence remains tied to its original runtime. Resume with a
global live-branch link invariant and the reference-count erasure premise; do not
treat registration correctness as completed lifetime or requested-patch refinement.

## Exact incoming counts and live dependency preservation (8 November, seventh hourly follow-up)

`ReferenceCounts.lean` defines each incoming count as the sum of decoded child
occurrences across all live native parents. The finite parent-domain witness and
sum occur only in a proposition and erase. The executed increment fold has an
exact addition theorem; successful decrement returns an exact subtraction
equation and retains underflow rejection. Fresh insertion and zero-count erasure
preserve the aggregate invariant. `Exact.zero_no_child` proves that count zero
excludes the key from every live parent's decoded child list.

`SourceLifetime.lean` wraps the paired store with exact counts and a global
`Linked` invariant: every live branch names its exact current child models.
Insertion uses fresh-key preservation; deletion combines the decoded metadata
with zero-count exclusion to discharge the conditional deletion premise from
`SourceLinks`. `lookup_branch` recovers current child links from a named relation
lookup. The native source context now uses this wrapper. Its registration path
supplies the actual missing-key equation and a leaf-or-checked-join proof.
Duplicate definitions change no state. Source deletion executes the proved
decrement and returns both preserved invariants. A failed batch exposes no new
state. Unreferenced identities can be reused without rebinding a live parent.

The new source operations decode at most two direct children per node. They do
not compute the proof's finite domain or global sum, scan the store, or retain
registration snapshots. Runtime hashing, maps, wrappers, integer/bit operations,
source payloads, transport and archive access remain costs. No new timing,
allocation/RSS or complete machine-cost bound is claimed. The generic relation
store still uses its earlier loops; the Python active-root/reference policy is
also outside this new native-source invariant.

A new regression independently recounts the complete live reference graph of
44 source nodes with 16 roots and shared internal descendants. It compares
deletion acceptance/rejection after randomized operations and duplicate
definitions, queries surviving roots, removes all remaining nodes in dependency
order, rebuilds the same names and reclaims them again. Earlier rollback,
parent-sharing, identity-reuse, branching and restart checks remain in place.

Next priorities:

1. **Exact requested-patch semantics.** Use current `lookup_branch` links to prove
   that successful `checkPatch` compares the actual typed children. Connect leaf
   clause equality to the requested replacement, and identical unedited names
   to unchanged original buckets. The current node's correct SAT semantics does
   not alone prove it is the requested successor. Root coverage, edit validation
   and complete initial binding remain part of this integration obligation.
2. **Python retention and complete serialized replay/SQLite refinement.** Native
   source dependency safety is now proved; this does not prove Python policy,
   archive integrity, outer transport, or the generic relation-store loops.
3. **General factor row/equivalence-store refinement.** Adjacent-block source
   invariants do not establish general factor-DAG guarantees.
4. **Complete restricted costs and acceptance specification**, including complete
   decrement/operation acceptance, caps, parsing, maps, allocation, payloads,
   transport, archive access and bit costs.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** No unrestricted-SAT coverage or total-resource bound follows.

Validation at the lifetime checkpoint: all **166 tests pass**, including **27
source-update tests**, without resource warnings. Lean audits **2,944 declarations /
1,416 theorem declarations** without admits or added axioms. Runtime checkpoint
`3382876` is committed and pushed. The manuscript and
[lifetime verification record](../experiments/results/source-lifetime/README.md)
include revalidation and semantic audit of all 355 older generic inputs and
checked adoption/restart of five saved source versions. Every previous row in
all 21 tables and all 190 earlier experiment files remains intact. The archive
now holds 7,455 results, 2,451 refutations and 45 source-state rows across checker
namespaces. Previous timing evidence remains unchanged. Resume with the typed
requested-patch argument using current child links; native source count/lifetime
preservation no longer needs to be assumed.


## 2026-11-08 08:08 UTC — exact native source-patch semantics

`SourcePatch.lean` defines the original clause bucket at each global edge of an
indexed source tree. `Patched old new edits` preserves start/height, makes every
requested edge equal its supplied original array, and preserves every edge
absent from the request. The leaf lemma retains clause order, duplicates and
empty clauses. The join lemma composes the two filtered edit lists at the typed
partition boundary; it does not infer source equality from relation equality.

`readNode` ties each executed relation/model lookup to the paired-store proof.
`readParts` decodes current child names, reads their current models, and uses the
live dependency invariant to identify the parent as their exact consecutive
join. That join equality is proof-only: checking a patch does not recompute a
relation join. `checkNodes` returns the visit count with a `Patched` certificate.
It accepts an unedited subtree only under identical names, handles a replacement
leaf with an exact original-array comparison, and combines the child proofs.
`check` attaches the two live root names to the transition.

The executed `checkRequest` also carries equations for the actual base, root and
edit-array JSON getters. `readEdits` proves entry-by-entry decoding of edge IDs
and clause arrays and the logical-edge bounds; the batch-size bound is recorded.
Duplicate rejection remains executed, and the transition proof does not assume
that the supplied edit list is unique. `SourceUpdates.patchQuery` now invokes
this checker before querying the same unchanged store and request.

The checker compares decoded original arrays, rather than raw JSON values.
Malformed payloads fail decoding. The specification's bucket functions and all
transition proofs erase. Runtime work includes typed node/body lookups, direct
child getters, edit-list filtering and original-array comparison, plus temporary
wrappers. Empty subtrees stop after identity and direct-root checks. There is no
flat-source traversal or summary recomposition. The visit counter keeps its prior
meaning; it is not a total native-instruction, allocation or bit-cost measure.
No timing improvement is claimed.

New regressions cover two edits across the root split with padding, request-order
independence, duplicate original clauses, literal order, equal-relation forged
payloads, omitted edits, duplicate/out-of-range/malformed requests, same-root
checks, different unedited aliases, missing roots and partition mismatch. The
alias rejection is deliberately conservative: source or relation equivalence
alone does not authorize changing an unedited identity.

Remaining priorities:

1. **Compose the full source API contract.** The native requested bucket
   transition is proved. Connect initial raw-CNF binding, root coverage and the
   serialized returned verdict/witness to a single successful-request theorem.
   Prove accepted source bucket equality gives the intended flattened original
   CNF, including padding and complete logical-edge coverage. Existing typed
   node decision semantics does not itself establish this whole API theorem.
2. **Python retention and complete serialized replay/SQLite refinement.** Native
   counts, live dependencies and patch semantics are proved; Python active-root
   policy, archive integrity, outer transport and generic relation loops are not.
3. **General factor row/equivalence-store refinement.** Adjacent-block guarantees
   do not establish general factor-DAG guarantees.
4. **Acceptance completeness and complete restricted costs.** Include caps,
   decrement acceptance, parsing, maps, integer/bit operations, array comparison,
   filter/lookup work, allocation, source payloads, transport and archive access.
5. **Compact general input, matched application evaluation and cost-sensitive
   selection.** No unrestricted-SAT coverage or total-resource bound follows.

Validation: **169 tests pass**, including **30 source-update tests**. The decoder
also accepts all 4,096 entries up to root lookup, rejects 4,097 entries at the cap,
and leaves the worker usable. Lean audits **3,043 declarations / 1,461 theorem
declarations**, with no admits or added axioms. Runtime checkpoint `32b4748`
is committed and pushed. All 355 older generic inputs pass revalidation and
semantic audit, and all five source versions pass checked adoption and restart.
Every old row in 21 tables and all 198 earlier experiment files remains intact.
The archive now holds 7,810 results, 2,580 refutations and 50 source-state rows.
The manuscript and [patch verification record](../experiments/results/source-patches/README.md)
record the result. Earlier timings and all 32 previous manuscript proof blocks
remain unchanged. Resume with full source-API composition and persistent replay;
the native requested bucket transition no longer needs to be assumed.


## 2026-11-08 09:06 UTC — complete successor formula and returned decision

`SourceFormula.lean` supplies the missing bucket-to-original-CNF step.
`flatten_source` proves that ordered flattening of the complete indexed interval
is exactly the node's original clause list, including order and multiplicity.
`bucket_present` characterizes its exact interval; `bucket_padding` proves that
padding contributes the empty clause array. `replaceBuckets` gives the requested
replacement function. `patched_buckets` and `patched_formula` connect an accepted
patch to that function and its complete flattened CNF. `patched_decide` and
`patched_unsat` give both SAT and UNSAT equivalences for this successor formula.
These flattening operations are specifications, not work on the native warm path.

`SourceVerdict.lean` certifies the native root checks: origin zero, enough leaves
for every logical edge, and the existing minimal padded height. Coverage proves
that every logical edge has a bucket and transfers to the predecessor through
the patch's start/height equalities. The query constructor records the actual
request root getter, current model lookup, coverage and returned Boolean getter.
The decision-only JSON getter equation holds definitionally. Witness-mode queries
reuse the existing returned-answer comparison; the proof does not yet certify
the serialized witness contents.

`compose_patch` identifies the queried node with the exact successor named in
the decoded patch request. It combines request decoding and bounds, both live
model lookups, coverage of both roots, the exact flattened successor formula and
both truth-value equivalences. `patchQuery` certifies the nested `verdict` getter
of the actual JSON result. `SourceUpdates.query_success` and
`patchQuery_success` transfer these certificates to the exposed JSON-returning
functions on every successful call. Native query and patch requests now execute
these constructors. Existing unknown-root diagnostics are preserved.

No flattening, full-source scan or relation-summary recomposition is introduced
on a warm decision/patch path. Direct lookups, root checks, decoding, comparisons,
filtering, wrappers, cached endpoint tests and requested witness work remain
costs. JSON getter proofs concern native JSON values; byte serialization and
outer transport are not thereby proved. There is no new timing, memory or
unrestricted-SAT guarantee.

New tests reject incomplete, shifted and nonminimal padded roots in both query
and empty-patch modes, with and without witnesses. Independent exhaustive
truth-table checks compare nested patch verdicts and direct queries against the
flattened original successor over 54 transitions, including historical branches,
1/3/5 logical edges, padding, deletion, repeated clauses and empty clauses. Both
SAT and UNSAT outcomes occur, and returned positive witnesses are checked
independently. These tests supplement, rather than replace, the proof.

Remaining priorities:

1. **Initial raw-CNF anchor and history composition.** Query/root coverage,
   complete successor formulas and the actual returned decision field are now
   proved. Connect the complete initial JSON CNF and original-bucket traversal
   to the live root under one native success theorem, then compose a history
   of accepted operations. Existing compiled-source and relation-binding theorems
   alone do not certify that entire initial source-provenance path.
2. **Serialized witnesses, Python retention and persistent replay.** Prove the
   truncated witness values and their original-variable interpretation, byte
   transport, active-root policy and complete replay/SQLite correspondence.
   Native live-child and incoming-count preservation remain established.
3. **Generic relation/factor stores.** Their retention loops and row/equivalence
   caches remain outside the adjacent-block source-store invariant.
4. **Acceptance completeness and complete costs.** Include source bounds, caps,
   decoding, array comparisons, map/bit operations, allocation, archive access,
   transport and restart. Logical path/event counts are not total machine costs.
5. **Compact general input, matched evaluation and cost-sensitive selection.**
   No unrestricted coverage or total-resource guarantee follows.

Verification: all **171 tests pass**, including **32 source-update tests**.
Lean audits **3,107 declarations / 1,506 theorem declarations**, with no admits
or added axioms. Runtime checkpoint `9673dee` is committed and pushed.
All 355 older generic inputs pass revalidation and semantic audit, and all five
saved source versions pass checked adoption and restart. Every old row in 21
tables and all 206 earlier experiment files remains intact. The archive holds
8,165 results, 2,709 refutations and 55 source-state rows. The manuscript and
[verdict verification record](../experiments/results/source-verdicts/README.md)
record the result. Earlier timing evidence and all 32 previous manuscript proof
blocks remain unchanged. Resume with the full initial raw-CNF anchor; complete
successor-formula equality, root coverage and returned native decision fields
no longer need to be assumed.


## 2026-11-08 10:15 UTC — initial raw-CNF binding and returned verdict

`SourceInitial.lean` closes the initial source-provenance path. The theorem
`compileSource_fields` derives actual width/layers/clauses getter equations from
success of the existing compiler. `readCompilation` carries these equations with
the compilation result, without a second parser or compilation implementation.

The executed `checkBinding` follows current live child names and models through
`readParts`; their join equalities come from the established live-store invariant.
Each leaf's original array must equal the compiled original bucket, including
literal order, duplicate clauses and empty clauses. Padding must match an empty
array. `matches_complete` proves equality with the full ordered concatenation of
these buckets. `matched_partition` composes this equality with the grouping
permutation. Thus the live root retains every raw input clause occurrence, but
global input order is not claimed to equal grouped tree order. `partition_eval`
proves equal evaluation for every original-variable valuation.

`InitialResponse` includes actual input and root getters, live model identity,
layout agreement, complete/minimal root coverage, exact bucket agreement, clause
permutation, nested returned verdict and SAT/UNSAT equivalences for the actual
input. `SourceUpdates.bindSource_success` transfers it to the exposed native
JSON-returning function. That function now executes the certified constructor.
The original relation-binding scan and decoded-answer comparison remain executed;
the checked verdict is returned unchanged instead of rewriting its equal answer.

The original-bucket traversal also certifies the actual `binding_visits` getter,
`visits + 1 = 2^(height + 1)` and `height < fuel`. The API uses fuel 17, covering
permitted heights through 16. The count covers logical node visits with padding.
It excludes parsing, map access, original-array comparisons, allocation, the
separate relation scan and witness work. Full initial binding remains charged;
warm query and patch paths are unchanged. Flattening is specification work.

New tests accept global clause permutations that preserve compiled bucket arrays,
then reject dropped/added duplicate clauses and changed literal order despite
equal SAT answers. They distinguish one empty clause from two, exercise both
response modes, and check exact padded scan counts for 1/2/3/5/17/33 logical edges.
Malformed input, wrong layouts, partial/shifted or missing roots and invalid
witness-mode fields are rejected while the original live root remains usable.
These finite tests do not establish cap-wide acceptance completeness.

Remaining priorities:

1. **Operation-history composition.** Initial, query and patch native APIs now
   have individual success theorems. Define a history with store states and
   retained source identities, then compose initial anchoring, successful node
   definitions/deletions and requested patches. Keep the original CNF permutation
   at initialization distinct from the exact ordered bucket replacements later.
2. **Serialized witnesses, Python retention and persistent replay.** Certify
   truncated witness values and original-variable interpretation, byte transport,
   active-root retention and complete replay/SQLite correspondence. Native current
   child identities and incoming counts remain proved.
3. **Generic relation/factor stores.** Their retention loops and row/equivalence
   caches remain outside the adjacent-block source-store invariant.
4. **Acceptance completeness and total costs.** Include source bounds, caps,
   error paths, decoding, array comparisons, map/bit operations, allocation,
   archive access, transport and restart. Successful logical visit counts are
   not total machine-cost bounds.
5. **Compact general input, matched evaluation and cost-sensitive selection.**
   No unrestricted coverage or total-resource guarantee follows from this result.

Verification: all **174 tests pass**, including **35 source-update tests**.
Lean audits **3,154 declarations / 1,539 theorem declarations**, without admits
or added axioms. Runtime checkpoint `92a1ddd` is committed and pushed. All 355
older generic inputs pass revalidation and semantic audit. All five saved source
versions pass checked adoption and restart. Every old row in 21 tables and all
214 earlier experiment files remains intact. The archive holds 8,520 results,
2,838 refutations and 60 source-state rows. The manuscript and
[initial-binding record](../experiments/results/source-initial/README.md) retain
the evidence. Earlier timings and all 32 previous manuscript proof blocks remain
unchanged. Resume with native operation-history composition; the complete initial
raw-CNF-to-live-root-to-returned-decision path no longer needs to be assumed.

## 2026-11-08 — certified affine growth instead of assignment-table expansion

User direction: attack the expansion bottleneck through genuine fresh-variable
growth, closed compact summaries, structural reuse and cumulative accounting.
Runtime checkpoint **3b953b8**, pushed. This is a separate restricted affine path;
it does not silently replace or weaken the existing CNF source-store contracts.

Implemented four Lean modules and `PersistentSolver.affine_grow`. Each append
introduces a fresh width-`b` block and equations on the old and fresh boundaries.
The exact summary is the existential projection of the full original history.
Elimination and basis compression operate directly on GF(2) coefficient vectors,
with at most `b+1` summary rows and `(b+1)^2` logical cells. Contradiction is explicit;
old version answers remain valid even when an added batch makes a successor UNSAT.
The native path executes the certified charged loops and returns proved decision
and charge fields for typed states. Both SAT and UNSAT refer to the specified
constraint history, not to different input-size conventions.

The charge bound is `O(b^3+b^2*c)` per resident append with `c` new equations.
`replayRun_bound` sums the same charges over typed original histories. Full-list
pivot scans, produced coefficients/rhs and terminal checks are charged; primitive
machine instructions, allocation, parsing, map work, transport and archive access
are not. This improves on a purely declared arithmetic ledger: value equivalence
and per-loop charges are now part of the executed coefficient implementation.
It still does not provide an end-to-end machine-cost theorem.

Immutable source batches and results persist in the new `affine_states` and
content-addressed object records. Replay reconstructs from original equations,
never saved summaries or answers. Corrupt source objects and malformed histories
are rejected. Failed transactions preserve old database rows; extra immutable
native nodes can remain until restart. The current summary is bounded; retained
history grows. No full-history witness is output. Caps (width 128, batch 4,096,
native versions 4,096) cause refusal, not a negative verdict. Native version
capacity includes initialization, so a single resident chain has at most 4,095
appends. The mathematical result has no such fixed cap.

Validation: **184 tests**, including **10 affine tests**; Lean audit **3,485
declarations / 1,708 theorem declarations**, with no admits or added axioms.
Exhaustive frontier sets cover 135 branching updates at widths 1..3. Independent
full-system elimination covers width 128. Archived evaluation checks **284**
decisions/restarts and retains **268** affine versions at widths 2/8/32/64.
An 80-step fixed-width regression has constant per-step charge and summary size.
All 355 earlier generic inputs and five source versions pass revalidation/restart.
All old rows in 21 tables and all 222 earlier experiment files remain intact,
including after the affine experiment. Archive counts: **8,875 generic results /
2,967 refutations / 65 source-state rows / 268 affine-state rows**. See the
[affine evidence](../experiments/results/affine-growth/README.md).
The manuscript adds the exact-growth proposition, cost model and limitations,
attributes affine tractability to Schaefer and Gaussian elimination, and preserves
all 32 earlier proof blocks. There is no matched speed comparison in this study.

Remaining priorities, with distinct scopes:

1. **Compose native operation histories.** For the general source-CNF API,
   compose existing initialization/query/patch success theorems with named-store
   definitions/deletions and retained source identities. For affine, typed history
   exactness is proved, but raw JSON/named-store history correspondence is still
   an integration boundary. Do not report the former as solved by the latter.
2. **Persistence and witness refinement.** Prove Python retention/replay/SQLite
   correspondence and serialized general-source witnesses. An affine witness API
   would require saved elimination information/back-substitution and output costs.
3. **Broader growth and mixed structure.** Add supplied tree decompositions with
   certified separators or extend the affine frontier contract. Recognition and
   maintenance costs must be charged. Arbitrary older-block edits are unsupported.
   A mixed CNF/XOR route could use supplied small backdoors; finding such backdoors
   and the worst-case `2^k` branching remain explicit restrictions.
4. **Complete costs and lifetime policy.** Refine coefficient charges to actual
   field/index/list operations and include native maps, decoding, allocation,
   archive growth, errors and restarts. Add bounded active affine retention without
   deleting durable versions; current native capacity refuses when full.
5. **Matched evaluation and dispatch.** Compare this path with a full Gaussian
   solver and checked CDCL on identical XOR workloads, include fixed/growing width,
   repeated/novel equations and restarts. Automatic recognition or selection needs
   conversion/verification costs. Current evidence establishes no competitive
   speedup, general-CNF coverage or unrestricted polynomial expansion.
6. **Generic relation/factor stores.** Their retention and equivalence caches
   remain outside the adjacent-block source-store invariant. Compact affine
   summaries do not establish polynomial closure for those general representations.

Resume with the general native history theorem or a matched affine cost study.
Retain `experiments/results/affine-growth/` and all earlier evidence; do not overwrite
older timing artifacts. The polynomial restricted step is now concrete and checked;
unrestricted SAT still lacks the required compact-closure/construction invariant.

## 2026-11-08: native histories, erased affine provenance and matched reuse

Runtime checkpoint **`88f26a8`** addresses native source-history composition,
bounded active affine retention, and the missing matched reuse comparison.
Evidence: [history-retention](../experiments/results/history-retention/README.md).
All older results and timing artifacts remain available.

**Native source-CNF histories.** The worker now executes `SourceHistory.handle`.
Its success contract retains the complete initial raw-CNF, current-root or exact
patch response certificate, as appropriate. Errors leave the predecessor store
unchanged, including failures after partial local construction. The finite-trace
induction composes arbitrary definition, deletion, reset, compilation, binding,
query and patch interleavings. Every successful query decides the complete
original CNF of its root in that event's store. Earlier observations remain valid
under continuation. This is eventwise semantics: a name deleted and reused can
refer to a different formula. It does not prove immutable Python content-hash
lineage across process generations, byte transport, serialized witness contents
or SQLite behavior. The worker does not accumulate the mathematical trace.

**Affine residency.** Inspection found that the earlier native `State` carried
its entire original history as runtime data. Deleting ancestor map entries alone
would not release those ancestors. `AffineResident` now retains original-history
semantics through Mathlib `Erased`; generated C has only the summary as the
resident state field. Current request JSON and node metadata remain additional
runtime data. The summary and coefficient-charge proofs still hold.
`dropNames_preserves` proves other native lookups unchanged after eviction.
Python protects the required parent and evicts older resident nodes, with a
configurable cap of 2..4,096 versions (default 256). It reconstructs evicted
versions from original archived equations, reading one batch at a time. Failed
transactions mark residency uncertain and trigger an affine-store reset before
the next checked replay. The simultaneous native cap no longer caps history
length: a regression appends 4,101 times, queries an evicted historical version,
and restarts with only two residents. The replay plan/cycle check still uses
O(T) identifiers; the durable history grows. A resident count is neither a byte
bound nor a formal proof of the Python policy.

**Validation and preservation.** All **190 tests** pass, including **15 affine /
36 source-update** tests. Lean audits **3,625 declarations / 1,766 theorem
declarations**, without admits or added axioms. All **355** earlier generic inputs
pass revalidation/audit; five source versions pass adoption/restart. All **268**
old affine versions pass source replay under a four-version cap, with positive
and negative restart checks under a two-version cap. Every old row in **22 tables**
and all **233** earlier experiment files remain intact. The live archive contains
**9,230 results / 3,096 refutations / 70 source-state rows / 536 affine-state rows**.
All 33 earlier manuscript proof blocks remain verbatim; one native-history proof
is added.

**Matched study.** Six fixed-width streams (2/8/16, repeated/novel equations), four
modes and three sequential repetitions give **72 runs / 1,296 correct decisions**,
including 72 negative decisions and no failed runs. Each mode receives the same
original parity systems and retains its results. Resident and full-parent-replay
modes share the delta input, archive and native algebra; restart and checked-CDCL
modes charge their lifecycle/conversion costs. At width 16, the median full-replay
times are **2.85 / 2.30** times the resident times. The smallest repeated stream
shows no gain. Three repetitions do not establish significance for small
differences or general workload performance. The CDCL pipeline uses a different
representation and certification path, so its timings do not isolate solver
algorithm speed. Independent full Gaussian elimination checks original-system
answers; it is not a certified timed baseline. A pilot overlapping archive
adoption is retained separately and excluded from the reported comparison.

Remaining priorities, with the newly closed scopes distinguished:

1. **Protocol and persistence refinement.** Connect affine raw JSON and native
   named-store histories to the typed history theorem. Prove Python content-hash
   lineage, retention/replay and SQLite correspondence, including failures and
   process-generation changes. The general native source-CNF eventwise history
   theorem is now available; it does not discharge these separate obligations.
2. **Witnesses.** Prove serialized general-source witness contents. Add an affine
   full-history witness route with retained elimination information and checked
   back-substitution; charge the necessarily growing output and archive work.
3. **Broader structure.** Extend supplied decompositions to certified separators
   on trees or mixed CNF/XOR with supplied small backdoors. Charge recognition,
   maintenance and conversion. Arbitrary older-block edits and worst-case `2^k`
   backdoor branching remain outside the current affine append guarantee.
4. **Complete costs.** Refine coefficient charges to actual field/index/list,
   decoding, native-map and allocation costs. Include archive growth, failure,
   replay planning, restarts and physical storage. The new eviction policy and
   erased provenance remove a concrete lifetime problem; total resource bounds
   and formal Python-policy correctness remain open.
5. **Evaluation and selection.** Extend the matched study to growing widths,
   adversarial mixes, realistic inputs and a timed complete Gaussian baseline.
   Add cost-sensitive dispatch only with charged recognition/conversion and
   comparable correctness obligations. Six synthetic streams do not show a
   uniform benefit, broad CNF coverage or significance for small differences.
6. **General relation/factor stores.** Prove their retention and equivalence-cache
   invariants separately. The adjacent-block source invariant and compact affine
   summaries do not establish compact closure for general representations.

Resume with affine protocol/history refinement or checked witness reconstruction.
Keep the matched and pilot evidence separate. There is still no compact-closure
or efficient-acquisition invariant for unrestricted SAT; no conclusion about
P versus NP follows from these restricted results.

## 2026-11-08: affine input provenance and expansion-focused priorities

Runtime checkpoint **`1037595`** closes the native affine decoded-input/history
connection. The user has redirected the existing hourly task toward **reducing
expansion work through compression and reuse patterns**. Proof, persistence and
evaluation work should support concrete expansion improvements rather than
continue as an independent general-hardening queue.

`AffineProtocol` now certifies exact Boolean row fields, dimensions, row order
and multiplicity, initial width, the actual parent lookup, returned node and
query lookup. `AffineHistory.handle` is the executed worker dispatcher. Its
chronological `Origin` invariant proves that every resident history after a trace
from the empty store comes from actual decoded requests in that trace. Successful
queries decide that original history. Rejections preserve the predecessor;
eviction retains only old nodes; reset empties the store. Mathematical trace and
origin evidence are erased from runtime states.

An important reuse distinction is now explicit and tested. Retrying a retained
child returns its existing history even if its parent name was deleted and
redefined. A fresh child binds the current parent. Deleting the old child and
reusing its name can therefore yield a different answer. The retry path also
checks decoded modes, widths or parent names, and typed equation lists; its
source-agreement proof does not assume correctness of Lean's partial general
JSON equality function. This adds parsing/comparison work on explicit retries.
Byte transport, cross-process content-hash lineage, Python/SQLite refinement and
serialized witnesses remain separate. There is no new performance claim for
this protocol checkpoint.

All **192 tests** pass, including **17 affine / 36 source-update** tests. Lean
audits **3,794 declarations / 1,836 theorem declarations**, without admits or
added axioms. All 355 old generic inputs, five source versions and 268 distinct
old affine versions pass revalidation; both affine verdicts pass restart under a
two-version cap. Every old row in 22 tables and all 394 prior experiment files
remain. The live archive has **9,585 results / 3,225 refutations / 75 source-state
rows / 804 affine-state rows**. All 34 prior manuscript proof blocks remain;
one affine-history proof is added. See
[the evidence](../experiments/results/affine-history/README.md).

### Current expansion costs and a concrete reuse pattern

For boundary width b and c new equations, a resident affine append has reference
coefficient-work bound **O(b^3 + b^2 c)** and summary payload **O(b^2)**. These do
not depend on the number T of earlier appends. Cold replay sums prior append
costs and retains O(T) identifiers in its plan. Parsing, comparison, maps,
hashing, serialization, allocation and archive work are additional costs. A
complete machine-time bound has not been proved. General CNF still lacks the
compact-closure guarantee needed for polynomial expansion.

`experiments/analyze_affine_reuse.py` replays the six frozen comparison streams,
retaining all source versions and checking 108 decisions independently. Each
repeated stream has **14 identical kernel inputs among 18 expansions**, despite
18 distinct version identities. Here a kernel input means the exact ordered
parent summary and the exact local equation batch, including its order. At
width 16, repeated calls account for **643,566 / 719,509 coefficient-work units
(89.4%)**; 240 duplicate rows also occur across the stream. All three novel
streams have zero such repeats. Sorting/deduplicating batches reveals no extra
repeated calls in these cases. The diagnostic installs no kernel cache and
establishes no realized speedup. It does not detect row-space equivalence or
variable symmetries. Earlier timing artifacts remain tied to their old binary.

### Next expansion priorities

1. **Reuse exact algebraic transitions across distinct histories.** Cache the
   boundary transformation for identical width, parent summary and equation
   batch. Construct a fresh source-history certificate for every append; do not
   return another version's history or confuse equal SAT answers with equivalent
   boundary relations. Check full keys rather than trusting hash equality.
   Charge comparison, lookup, insertion, eviction and durable version records.
   Compare against the current path on repeated and novel streams.
2. **Compress equation batches and boundary keys.** Prove and measure duplicate
   elimination first. Then test canonical row-space forms and variable renaming
   only when their discovery/normalization cost can repay the saved elimination.
   Preserve original row order and multiplicity in the source archive even when
   the computational representation removes redundancies.
3. **Update only changed structure.** Investigate small-rank equation changes,
   reusable elimination steps and shared separator components. State exactly
   which edits preserve the summary invariant and when reconstruction is needed.
   Expand supplied decomposition families with recognition/maintenance costs.
4. **Measure all acquisition and reuse costs.** Broaden repeated/novel workloads
   to growing widths, adversarial misses and cold reconstruction. Track stored
   components, compression ratios, reference work and elapsed phase costs.
   Retain unsuccessful trials and counterexamples; avoid repeating dead ends.
5. **Supporting obligations.** Complete Python/SQLite and witness refinement,
   general-store invariants and machine/resource accounting when they are needed
   to justify a specific expansion optimization. These are still open; the native
   source-CNF and native affine event-history scopes are now proved.

The scheduled task remains hourly in this chat, with these expansion priorities.
The next concrete target is an exact transition cache that separates a reusable
boundary calculation from each append's immutable original history.


## 2026-11-08: exact transition reuse implemented and measured

Runtime **`f80f678`** completes the first expansion priority above. The reusable
`Kernel previous equations` certifies its exact summary, verdict and nominal
coefficient charge. A hit checks width and both complete typed input lists after
hash selection, then attaches the result to the current parent's erased original
history. The native chronological origin theorem still applies, including the new
cache-configuration operation. Cache entries contain no source ancestor states.

The service defaults to 64 direct-mapped slots, configurable from 0 to 4,096.
Zero bypasses hashing/lookup. Version eviction leaves kernels available; reset
and restart clear them. Each entry retains O(b^2+b*c) coefficient cells; this is
not a byte/RSS bound. Hash collisions can evict useful entries but cannot cause a
false hit. Query reports retain creation metadata; per-request `affine_updates`
separates actually executed construction work, hits/misses, key scans and
candidate-comparison bounds. Completed source versions/results remain durable.

### Costs and evidence

- A miss retains the **O(b^3+b^2*c)** elimination bound and adds cache overhead.
- A hit skips elimination and decision. Its hashed coefficient payload is at most
  **(b+1)^2+c*(2*b+1)**, with at most one structural candidate comparison. List,
  dimension and map checks, hash arithmetic, allocation, decoding, transport and
  archive work remain additional costs. A hit is not a zero-cost expansion.
- Over actual hits A, the elimination/decision ledger is the sum of nominal
  charges for non-hits. Capacity, collisions and input variation determine A;
  no positive hit rate is guaranteed.
- Five sequential, rotated, same-binary repetitions compare 64 slots with zero.
  The six old input streams are unchanged. Two width-32 streams add longer
  histories. **80 runs / 1,760 independently checked decisions** retain all
  completed versions and results, under four resident versions.
- Width-16 repeated: **14/18 hits**, coefficient ledger **719,509 -> 75,943**
  (89.4% reduction); hashing **21,025** cells, candidate comparison at most
  **18,864**. Median elapsed service time **167.57 -> 144.21 ms** (13.9% less).
- Width-32 repeated: **30/34 hits**, ledger **10,987,813 -> 565,063**;
  median **496.37 -> 215.54 ms** (56.6% less, **2.30x**). Width and stream length
  both increase, so this does not isolate scaling with width alone.
- Novel streams: **zero hits**, median overhead approximately **0.1--0.5%**.
  Small differences are descriptive, not a significance test or overhead bound.
  An overlapping-adoption pilot is retained separately and excluded. The final
  run starts only after adoption finishes; both use identical input bytes/binary.

**197 tests** pass, including **22 affine / 36 source-update** tests. Lean audits
**3,938 declarations / 1,875 theorem declarations**, without admits or added
axioms. New regressions force single-slot collisions, distinguish SAT boundary
relations, compare complete frontiers with the cache off/on, and exercise source
rebinding, eviction, restart, configuration rejection and rollback. Generated C
inspection confirms no elimination call on hits and no runtime history ancestors.

All **355** earlier generic inputs, **five** source versions and **268** distinct
affine versions pass revalidation. Every old row in **22 tables**, all **405**
preceding experiment files and all **35** prior manuscript proof blocks remain.
The live archive now has **9,940 results / 3,354 refutations / 80 source-state
rows / 1,072 affine-state rows**. The disabled-cache pattern diagnostic reproduces
its previous counts and charges. The manuscript adds an exact-kernel proposition
and the measured comparison. See [the evidence](../experiments/results/affine-kernel-cache/README.md).

### Next concrete expansion work

1. **Remove redundant rows before elimination.** Start with exact duplicate rows,
   prove preservation of every boundary solution, retain original multiplicity in
   source records, and measure normalization versus saved construction on misses.
   The width-16 repeated stream still contains 240 duplicate rows. Exact kernel
   hits already avoid their elimination; compression must justify its own work.
2. **Expose equivalence beyond exact ordered keys.** Test canonical row-space
   forms and variable permutations with full certificates. Measure discovery and
   normalization before claiming a wider useful reuse class. The earlier batch
   sorting/dedup diagnostic found no additional hits in the six frozen streams.
3. **Share work across small changes.** Reuse elimination steps for low-rank
   equation updates or unchanged separator components; prove when changes preserve
   the retained interface and when reconstruction is required.
4. **Improve cache admission and collision behavior only with evidence.** Stress
   interleaved hot kernels, adversarial collisions, growing widths, cold replay
   and variable batch sizes. Compare slot policy, retained bytes and per-phase
   costs. No all-workload speedup is possible for blind exact caching.
5. **Retain the remaining proof boundary.** Durable kernel certificates, serialized
   witnesses, Python/SQLite correspondence, complete machine/space costs and
   general-CNF compact closure are still open. Current kernels are process-local;
   restart reconstructs from original source batches. This result says nothing
   new about unrestricted SAT or P versus NP.

## 2026-11-08: storage growth and an additional expansion opportunity

Read-only audit at `9773ede`: the main database is **18,907,136 bytes (18.03 MiB)**.
Its **1,072 affine result rows represent 268 distinct versions across four engine
namespaces**, not 1,072 distinct histories. The 268 `affine_version` objects occupy
**4,205,628 raw JSON bytes / 139,444 compressed payload bytes**; 537 result objects
occupy **117,090 compressed payload bytes**. Database pages/indexes and other
solver paths are additional. The much larger local `.cache` tree includes all
retained experiment databases and backups; it is not one solver's active state.

For width b, at most c equations per append, T archived versions, V resident
versions and K kernel slots:

- The current summary has at most `(b+1)^2` coefficient cells.
- Retained native version summaries **and request bodies** plus kernel keys and
  results have coefficient/request payload O((V+K)*(b^2+b*c)), before metadata
  and transient allocations. Defaults are V=256 and K=64. Neither cap bounds RSS.
- Original history records store a parent link plus the new batch, avoiding a
  complete-history copy on every append. Raw source coefficient payload grows
  as O(sum_t b*c_t), or O(T*b*c) with fixed upper bounds. Logical version/answer
  records also grow with T. Step counters, indexes, engine namespaces and their
  byte encodings are additional; this is not a strict constant-byte-per-step theorem.
- By default archived affine results contain no boundary summary (`summary=False`).
  Requesting and retaining summaries can add O(T*b^2) coefficient payload. Exact
  duplicate whole objects share one row, but report/engine variants can add records.
- Cold replay still keeps O(T) identifiers in its backward plan/cycle check and
  reconstructs from original batches. There is no durable checked-kernel shortcut.
- The archive has no default size cap. An optional page cap refuses new work when
  full; it neither discards old results nor establishes a hard physical-disk bound.

**New concrete target: share exact equation batches across version records.**
The source-object hash includes the parent, so an identical local batch inside a
new history is currently serialized/compressed again. `KnowledgeStore` deduplicates
whole objects and compresses each object independently; it does not intern the
embedded batch. Separate immutable batch objects could preserve exact order and
multiplicity while version records retain parent/batch links. For U distinct
batches, their coefficient payload would scale with U instead of T; version
metadata would still grow with T. A later native batch-registration interface could
also avoid decoding and hashing a known batch on every reuse, but needs a new
source-origin proof and explicit checking of registrations.

`experiments/results/affine-kernel-cache/storage-audit.json` records a serialization
model using the existing zlib setting. In the width-32 repeated stream, 35 source
versions contain only four distinct batches. Their compressed source payload is
**16,656 bytes**; the modeled batch objects plus links occupy **5,593 bytes**
(66.4% less). Width-16 repeated payload falls **4,265 -> 3,009 bytes** in this model.
The same split **increases** modeled novel-stream payload: **6,226 -> 7,616 bytes**
at width 16 and **22,000 -> 24,344 bytes** at width 32. These estimates exclude
additional SQLite/index costs and are not measured database savings. Existing
parent hashes are placeholders; migration, runtime and checking costs remain
unmeasured. Old rows are preserved; new formats would first apply to new versions.

Prioritize a measured sharing/admission policy alongside duplicate-row removal.
Preserve exact source batches; use semantic normalization only in a separately
certified computational representation. Bit-packed Boolean storage, byte-based
cache budgets and phase/RSS measurements are further concrete targets. Broader
canonicalization, low-rank updates, checked restart checkpoints and complete
Python/SQLite/resource refinement remain open. No compact-closure result for
general CNF follows from the current affine representation.


## 2026-11-08: shared batches and certified duplicate removal

Runtime **`e0cb8d3`** implements the two concrete targets from the storage audit.
`AffineNormalize.lean` proves exact row membership, no duplicates, length reduction
and preservation of every boundary assignment. `Kernel.restoreOriginal` attaches
a normalized calculation to the actual original batch and current parent history.
The native chronological origin proof remains valid. Prepared typed batches and
normalized transitions have separately occupied bounded maps (64 slots each by
default); each hit checks full equality after hash selection.

The archive now supports an `affine_batch_ref_v1` encoding under the same legacy
logical version hash. Reads validate the shared batch and reconstructed original
source. Every old inline object stays unchanged. Only repeated batches with at
least 128 compressed-payload bytes saved per reference are admitted; the discovery
index retains at most 256 hashes. Small and unique batches stay inline. The policy
can still add CPU work and first-admission overhead; it has no universal space or
time guarantee. Both new options are independently configurable and default on.

### Measured gains and remaining costs

The matched study compares baseline, normalization, sharing, and both options;
all modes keep the prior exact kernel cache. Five sequential rotated repetitions
cover 120 runs and **2,800 decisions**, independently checked against complete
original systems. Archive adoption finishes before the final run. The pilot is
retained separately and excluded; input and runtime fingerprints agree.

- Width-32 changing multiplicity: **0 -> 14/18 hits**, executed coefficient work
  **30,266,133 -> 461,575**, median time **1,246.55 -> 430.52 ms** with both options
  (65.5% less). Raw rows total 8,673, normalized rows 513. Normalization alone takes
  417.58 ms. Original batches remain distinct in storage.
- Width-16 changing multiplicity: **367.70 -> 223.19 ms** (39.3% less).
- Width-32 exact repeated batches: source payload **16,656 -> 6,499 bytes**
  (61.0% less); database **274,432 -> 262,144 bytes** (12 KiB less). One shared
  batch supports 30 references while all 35 versions remain. Median time with
  both options **236.75 -> 252.47 ms** (6.6% more). Extra reconstruction and
  validation remain a concrete cost to reduce.
- Width-16 repeated batches fail the savings threshold and stay inline. Novel
  streams gain no hits or shared objects and retain identical source payload.
  Small median timing changes (+0.8%, -0.2% with both) establish no broad benefit.

**Memory is not fully shared yet.** Prepared normalized lists are shared with
transition keys, but preparation entries retain the original typed input for
checking, and each resident version still stores its request JSON. Additional
cache entries may increase RAM. With width/row bounds b,c, retained coefficient
and request payload is O((V+K+P)*(b^2+b*c)), before metadata and temporary work,
where P is preparation slots. Slot counts are not byte/RSS bounds. No measured
process-memory reduction is claimed. Hash-set probes/resizing/collisions and
allocation remain outside the normalization input-cell counter.

**Storage now follows a hybrid model.** Inline versions keep their batch payload;
shared batches retain their coefficient payload once plus links for each version.
Thus source coefficient payload is O(sum_inline b*c_t + sum_shared_batches b*|B|),
before compression, metadata, results and indexes. Fully novel input still gives
O(sum_t b*c_t), and the archive has no default size cap. Existing inline records
are not rewritten, so old archive size does not automatically shrink. The main DB
is now **19,738,624 bytes**; it includes a new engine namespace and contains
**10,295 results / 3,483 refutations / 85 source rows / 1,340 affine rows**. The
latter remain **268 distinct histories**, now across five engine namespaces.
Retained experiments and backups consume additional disk space.

### Verification and preserved evidence

**207 tests** pass (26 affine growth / six affine archive / 36 source updates).
Lean audits **4,043 declarations / 1,911 theorem declarations** without admits or
added axioms. Tests cover complete frontier equivalence, changing multiplicities,
collisions, corrupt references, restart with sharing disabled, and rollback after
shared admission. Generated C skips deduplication on preparation hits and performs
no second elimination when transporting back to original-source meaning.
All 355 older generic inputs, five source versions and 268 affine versions pass
revalidation. Every old row in 22 tables and all **583** preceding experiment
files remain intact. The old unnormalized diagnostic reproduces its counts and
charges. All **36** preceding manuscript proofs are unchanged; one is added.
See [the complete evidence](../experiments/results/affine-batch-reuse/README.md).

### Next priorities for expansion effort

1. **Checked native batch handles.** Register original batches once and reuse
   typed/normalized data across requests. Eliminate repeated JSON decoding and
   per-version request copies where possible, with a revised source-origin proof.
   This targets the measured repeated-stream overhead as well as memory.
2. **Byte budgets and admission.** Profile live allocations and compressed reads;
   compare saved payload with added checking/reconstruction. Bound cache bytes,
   not just slots. Keep rejection atomic and all durable results intact.
3. **Broader certified equivalence.** First-occurrence normalization does not
   identify row permutations, equal row spaces or variable renaming. Charge
   discovery and transport before claiming extra useful hits.
4. **Low-rank changes.** Reuse elimination structure for small equation edits;
   identify exact interface conditions and reconstruction requirements.
5. **Checked restart checkpoints.** Native caches remain process-local; cold
   replay still walks source histories and keeps an O(T) identifier plan.
6. **Remaining refinement boundary.** Python/SQLite, serialized witnesses and
   complete machine/space costs remain open. None of this gives compact closure
   for general CNF or changes the status of unrestricted SAT or P versus NP.


## 2026-11-08: complete resource audit before the next optimization

[Current computation, memory and expansion bounds](resource-bounds.md) now
collects the formal results and implementation limits across every active solver
family. The [read-only snapshot](../experiments/results/resource-audit-2026-11-08/snapshot.json)
records the source revision, page/object inventory and recomputed phase medians.
No solver behavior or previous results changed in this audit.

Two concrete affine-hit costs are now identified in code and preserved records:
`AffineGrowth.run/ensure` reread the original source and parent, and native
`defineChecked` always returns the full summary. A measured width-32 shared hit
has zero elimination work but nine object reads and 8,175 response bytes. Checked
batch handles, lightweight parent metadata and compact append replies can target
these costs; the current proof must be maintained when changing the protocol.

Memory claims also need a better measurement boundary: service RSS is cumulative
Python-process RSS, and reaped-child statistics omit the simultaneous live native
process tree. Slot limits and compressed disk payload are not RAM bounds. The
archive inventory additionally shows that the measurement/result tables and their
primary indexes occupy about 64% of the current main DB. Which cost dominates
therefore depends on whether the workload has hits, novel rows, cold replay,
growing width, or many preserved result namespaces. Future changes should be
chosen against this inventory and measured independently.


## 2026-11-08: reuse checked resident widths; assess KD-tree search

`AffineGrowth.verified` now retains the width returned by a successful native
definition, after checking it against the validated original source. Forward
replay can compare a child's width with that resident parent metadata instead
of decompressing and decoding the parent's full batch again. The value exists
only with the resident node: eviction, worker replacement, reset and failed
transactions remove it. A mismatching native width fails before publication.
Every public base read still validates original archived content. Cold replay
still reads and checks every missing source and recreates native definitions.

This is a bounded Python orchestration improvement, not a new Lean theorem.
The native binary, its original-history theorem, all manuscript proofs and the
main archive are unchanged. Retained metadata adds O(V) bounded integers;
one transient parent decode disappears, but whole-process memory is unmeasured.
`affine_reuse_metadata=False` provides the matched previous read path.

The [matched evidence](../experiments/results/affine-resident-metadata/README.md)
contains five rotated repetitions of widths 16/32/64 and repeated/novel streams:
**60 runs / 2,160 decisions**, including two fresh-service cold reconstructions
per run. Independent full-history elimination verifies the inputs; original
source rows and identities are recovered in every run. Elimination counters and
kernel hits are identical across modes.

- Inline warm append: **4 -> 3** object reads. Shared warm append: **9 -> 7**;
  the width-32 sample reads **2,904 -> 2,291 packed bytes**. Wire bytes and
  inserted source/result payload are unchanged.
- Width-32 repeated stream: 28 warm appends **84.39 -> 78.22 ms**; whole stream
  including setup/shutdown **238.00 -> 232.72 ms**. Two cold reconstructions
  **214.46 -> 201.90 ms**, with **384 -> 258** object reads.
- Width-64 repeated: warm appends **280.72 -> 260.76 ms**; whole stream
  **534.69 -> 509.73 ms**. Cold reconstructions **640.65 -> 599.29 ms**.
- Novel streams still need the same elimination. Width-32 whole-stream median
  **388.70 -> 393.50 ms** is slightly worse despite fewer reads. Local timing
  differences are descriptive; no universal speedup or complexity-class change
  follows. Source payload and matched database sizes remain equal.

**210 tests pass**, including the existing long-history, source-corruption,
forged-width, branching-frontier and restart tests plus direct checks of the
metadata lifetime and read reduction. The initial additional test expected the
wrong exception for damaged compressed bytes; that failed test log is preserved.
Its fixture now selects raw encoding to test an explicit size-integrity rejection.
All **743** preceding experiment files and all rows of the main archive's **22**
tables are preserved; no new engine namespace was needed.

The user proposed KD-trees. [The indexed-reuse assessment](indexed-reuse.md)
records the literature, a one-bit SAT/UNSAT counterexample, source/interface and
invalidation requirements, full costs and a matched future experiment. Existing
native exact lookup examines one hash-selected candidate, not every stored state.
A KD-tree could shortlist candidates for low-rank or other checked repairs;
that repair path is currently missing. It cannot turn proximity into a valid
answer or replace exact checks. No KD-tree speedup has been measured.

**Next bottleneck:** seven reads remain on a shared warm append, together with
full request decoding, repeated source serialization and an 8,175-byte native
reply in the width-32 sample. Pursue checked batch handles and compact definition
replies, then measure byte admission and repair/canonicalization opportunities.
The backward replay plan remains O(T), persistent storage remains unbounded by
default, and unrestricted SAT receives no affine closure guarantee.


## 2026-11-08: cheap expansion as a maintained structural invariant

The user requested conditions that make the favorable case available for every
allowed expansion. [The precondition analysis](expansion-preconditions.md)
specifies sufficient boundary information, closure, cheap recognition, bounded
affected structure, checked construction, initialized/resident state and full
accounting. This supplies a meaningful restricted-family target; caching or
precomputing all cases cannot establish it without construction/space bounds.

The preserved affine benchmarks expose an immediate opportunity: all 192 regular
updates across six width-16/32/64 repeated and novel streams have point successor
boundaries. The initialization fixes the fresh block and each following batch
defines the next variables from old ones. The two final branches per stream are
contradictory and unconstrained. A substitution prototype covers **all 204**
updates. It matches complete frontiers on **5,010 accepted cases** among 11,862
small tests and declines 6,852 for general solving. This reveals an evaluation
restriction as well as an optimization opportunity: "novel batch" does not mean
"general correlated affine boundary."

`StructuralExpansion.lean` adds five checked semantic theorems: empty propagation,
total-relation nonemptiness, functional singleton closure, bijective transport,
and a singleton append tied to the original affine history and batch semantics.
The complete Lean audit passes **4,049 declarations / 1,916 theorems** without
admits or new axioms. These are conditional semantics; executable recognition,
native dispatch, source-origin integration and the specialized resource ledger
remain open. The native binary has not changed. The manuscript now states both
the structural result and the limitation discovered in the existing workloads.

For a known point and a recognized functional affine update, direct evaluation
targets O(b*c+b^2) dense coefficient work, including recognition and explicit
point-summary construction, instead of generic O(b^3+b^2*c') elimination. For an
arbitrary affine boundary and a signed-permutation update, column transport and
RHS adjustment target O(r*b) after O(b*c) recognition. These are derived targets,
not measured native speedups or optimality theorems. Original source/archive
growth and transport still have to be charged.

**Revised next priority:** certify a point-boundary capability and functional-row
recognizer, construct successors directly, and preserve native chronological
history and accounting. Add correlated/partial frontiers and unsupported updates
to matched evaluation before drawing general conclusions. Then implement the
signed-permutation case, checked batch handles and compact replies. KD-trees can
later shortlist candidates for a checked repair; they do not replace these
preconditions. Retain the generic path and every previous source/result.


## 2026-11-08: refocus on arbitrary SAT and interacting tractable classes

The user now prioritizes minimum-cost expansion for arbitrary SAT. The next
milestone therefore moves from an affine-only fast path to a general residual
decomposition with tractable leaves. [The analysis](arbitrary-sat-expansion.md)
distinguishes whole-input classification from splitting a formula into parts,
reviews Schaefer's language classification, heterogeneous/scattered backdoors,
component-backdoor depth and representation-specific compilation lower bounds.
Class recognition, discovery, recombination and persistent maintenance are part
of the cost. No uniformly cheap complete cover of arbitrary SAT is established.

An explicit linear-size indicator construction transforms any CNF into a
conjunction of positive dual-Horn and negative Horn/2-CNF parts. Their interaction
still encodes the original SAT problem. The retained diagnostic checks complete
assignment correspondence on **460 formulas** (224 SAT / 236 UNSAT), including
all 256 two-variable formulas formed from nonempty nontautological clauses. It
also reproduces Gaspers et al.'s published heterogeneous-backdoor example: one
variable yields Horn or 2-CNF residuals, while homogeneous searches through size
two can fail. The search counts and failures remain in
`experiments/results/sat-class-decomposition/diagnostic.json`; the enumerator is
a small diagnostic, not an efficient backdoor detector or native solver path.

**Next priority:** checked Horn/dual-Horn/2-CNF leaves and a bounded recursive
planner alternating variable splits with independent component splits, with
exact residual reuse and the existing complete checked fallback. Then add
source-linked dependency/invalidation and OR/AND recomposition proofs, matched
hard connected workloads, structural-change edits and cold replay. Optimize
total new work, not only the number of backdoor variables. Affine constructors
remain potential leaves; preserve their proofs and all earlier evidence.

For a supplied strong backdoor of size k the branch bound is 2^k times polynomial
leaf work; for a suitable supplied component-backdoor tree, depth d can replace
global size in published evaluation bounds. Neither k nor d is uniformly small
on all SAT inputs, and finding the structure is charged separately. A universal
polynomial acquisition/expansion/query result would prove P=NP; this logical
implication does not establish that such a result is impossible. Current runtime,
Lean theorems and manuscript are unchanged by this research checkpoint.


## 2026-11-08: distinguish prepared expansion from an ordinary SAT algorithm

The user's clarification changes how the previous implication should be read:
cheap expansion and queries after expensive size-dependent preparation do not
establish ordinary P=NP. The analysis and manuscript now explicitly separate
acquisition C_prep(n), incremental work U(H, delta), queries Q(H, x), and storage.
The uniform-expansion corollary retains its stronger hypotheses: one fixed finite
seed, uniformly polynomial total work, and coverage of all lengths. A very large
fixed seed is an asymptotic constant; a supplied family of states growing with n
can hide nonpolynomial acquisition and must be accounted for separately.

The oracle section now includes Baker-Gill-Solovay's PSPACE-complete example:
P^A=NP^A=PSPACE, with the polynomial-space simulation argument. This genuine
oracle model leaves internal answer computation uncharged. It neither supplies
a finite constructed archive nor proves that our acquired state has the same
power. No ordinary or relativized class collapse is claimed for our solver.

**Working objective:** minimize additional work given acquired state, record its
acquisition and memory cost, and prove precisely which future changes its stored
summaries support. The heterogeneous decomposition priorities remain; their
future bounds should expose the prepared-state invariant and new residual work.
No general polynomial expansion guarantee has been demonstrated. This checkpoint
changes exposition only; executable code, Lean proofs and stored solver results
remain unchanged.

Validation: checked the oracle argument against the original 1975 paper's
Theorem 2; all 38 existing manuscript proof blocks are byte-for-byte unchanged
and all 147 labels are unique. Two LaTeX passes produce a 76-page PDF with no
warnings or overfull/underfull boxes. Revised pages 6/18 and adjoining pages 7/19
were rendered and visually inspected. `git diff --check` passes. No solver or
Lean tests were rerun for this exposition-only change.


## 2026-11-08: executable arbitrary-CNF residual candidate

The user asks to pursue a uniform polynomial solution for every CNF, charging
all acquisition. [The candidate analysis](residual-candidate.md) records a new
research implementation with explicit Horn/dual-Horn/2-CNF leaves, independent
components, variable branching, and persistent exact residual reuse. Full CNF
keys avoid a collision-free-hash assumption. SAT models and UNSAT dependency
certificates are checked in Python on acquisition and cold replay; this is not
yet part of the production solver's Lean trust boundary.

All 217 Python tests pass. Lean proves conditioning and branch recomposition;
the audit passes 4,061 declarations / 1,924 theorems without additional axioms.
The first experiment retains 156 matched decisions over 26 inputs, including
warm and cold replay, plus all 104 result archives. Thirty-two repeated
components need 6 expansions versus 161 without search reuse. Seven pigeons
into six holes need 416 versus 1,235. Cold replay creates no new nodes but checks
all 416 negative-certificate nodes. All prior solver results remain untouched.

The residual count still lacks a uniform polynomial bound. The immediate
structural opportunity is matching: the pigeonhole family should be recognized
and solved with a matching/Hall certificate rather than residual branching.
This is established tractable-class reasoning, with a direct CMP-SAT precedent
in Lenchner's 2019 preprint, and does not cover every CNF. Initial evidence,
including cases where decomposition adds work, is preserved for comparison.


## 2026-11-08: matching structure replaces a growing search family

Implemented the next structural leaf in the experimental CNF candidate. It
recognizes disjoint positive choices and complete negative exclusion cliques,
solves the resulting bipartite matching problem, and independently checks a
source witness or Hall deficiency certificate. Missing clique edges and
overlapping choices are rejected; satisfiable counterexamples to these two
unsound relaxations are retained. This is established matching/CMP-SAT reasoning,
not a claimed novel class or a uniform solution of all CNFs.

[Matched evidence](../experiments/results/cnf-matching/README.md) contains 153
decisions over 39 inputs. Nine pigeons / eight holes drop from 5,191 acquired
residuals and 17,290,081 logical bytes to one residual and 6,208 bytes. Cold
checking drops to one source/Hall node. Matching-only scaling reaches 48 holes,
still with one node but 1,496,174 retained logical bytes, illustrating that the
source cost grows. Four near-miss cases and all previous difficult cases remain.
All 104 earlier archives reload with unchanged row digests and no new expansions.
Every new result/certificate is retained in 75 additional compressed snapshots.

All 220 Python tests pass. Lean checks conditioning, branch recomposition and the
cardinality obstruction, with an audit of 4,062 declarations / 1,925 theorems.
The manuscript adds the full mathematical matching reduction and proof. The
Python recognizer/checker is still outside the production Lean trust boundary;
production code and its result archive are not targeted by these experiments.

**Next mathematical priority:** positive-clause overlap. Replacing each SAT
variable by complementary indicators embeds arbitrary CNF into overlapping
positive clauses with disjoint negative pairs. Thus the resource graph can be
simple while shared satisfaction carries the full problem. Investigate removal
of redundant/laminar choices, overlap backdoors, and exact summaries of shared
satisfaction. A k-variable overlap backdoor can still require 2^k branches;
neither a universally small k nor a polynomial number of residuals is proved.
Keep acquisition, recognition, intermediate representation and cold checking in
the bound. Native source-linked certification is a separate implementation gap.

Final validation: all 38 previous manuscript proof blocks are unchanged and one
matching proof is added. The 78-page PDF builds without warnings and revised
pages 70/71, adjoining page 72, and bibliography pages 76/77 were rendered and
visually checked. The prior experiment's artifacts are unchanged; current
candidate/driver fingerprints match their report. The separate cold-baseline
audit confirms 5,191 checked nodes at eight holes, with zero new expansions.


## 2026-11-08: redundant positive expansion reuses a checked minimal core

Implemented the next recorded opportunity: positive-clause subsumption exposes
matching leaves hidden by redundant overlap and makes equivalent source versions
reuse one exact normalized core. Every deletion has a retained subset witness.
Negative source wrappers check those witnesses and the exact negative child;
positive sources retain full checked models. Laminar positive families have
disjoint minimal members, so complete negative exclusion cliques retain a
polynomial matching construction after this charged preprocessing. Arbitrary
irreducible overlap remains outside that guarantee.

[The matched experiment](../experiments/results/cnf-subsumption/README.md) retains
39 static inputs and four nine-query histories: 450 correct decisions and 86
compressed archives. A laminar eight-hole input drops from 23 nodes / 201,735
logical bytes to two nodes / 17,538 bytes. More substantially, eight redundant
extensions of an acquired eight-hole core drop from 23,046 total new nodes and
84,546,940 retained logical bytes to nine nodes and 82,514 bytes. After the first
query, each addition creates one source record and performs no new core search.
Final cold negative replay checks two nodes instead of 5,359. All 179 previously
preserved candidate archives still check with unchanged row digests and no new
expansions; the production result archive was not targeted.

All 224 Python tests pass. Added tests exhaustively preserve all models of 2,048
small positive families, check warm/cold SAT and UNSAT core reuse, and reject
invalid/circular containment witnesses and changed dependencies. Lean adds three
semantic lemmas for containment, covered-core models and witnessed extension;
the audit passes 4,066 declarations / 1,928 theorems. This does not bring the
Python checker or its database inside the native Lean trust boundary.

**Retained limitation and next expansion priorities:** the new pass still scans
and normalizes each full source, rebuilds the containment index, and copies the
source and core key into its new record. An unchanged core can therefore coexist
with quadratic cumulative source-copy payload over linearly growing histories.
Investigate an incremental retained-clause index and persistent source deltas,
with explicit invalidation when witnesses or conflicts change. Also evaluate a
cost policy: seeded case 20 increases from 12 to 20 nodes and 12,029 to 18,637
bytes because reduction wrappers do not repay their cost. Three other controls
also grow, and these unsuccessful comparisons are preserved. A useful next gate
would require an exposed tractable leaf or a cached core before paying for an
additional reduction node; that policy is not implemented or proved optimal.

Subsumption is published preprocessing (Een and Biere, SAT 2005), not a new
general SAT algorithm. Worst-case discovery still has O(p^2 w) containment probes
plus source scanning, sorting, index and bit costs. No universal minimum-expansion
or polynomial arbitrary-SAT bound follows from the successful restricted stream.

Manuscript checkpoint: Proposition 12.28 gives the model-preserving minimal-core
reduction, the laminar matching corollary and the witnessed-extension invariant.
All 39 preceding proof blocks are unchanged; there are now 40 proof blocks and
151 unique labels. The 79-page PDF builds without warnings or overfull/underfull
boxes. Revised pages 71/72, adjoining page 73 and bibliography page 76 were
rendered and visually inspected. All 86 new compressed snapshots decompress to
their recorded hashes, and candidate/driver fingerprints match the report.
Code, Lean, data and research documentation were committed and pushed in
`1d3b2eb`; the manuscript and this final validation follow in a separate checkpoint.


## 2026-11-08: persistent witnessed deltas remove repeated source copies

Implemented `experiments/cnf_positive_history.py`, a separate prepared-state
interface that stores a solved base once, retains its positive-clause index,
and appends clause deltas with checked subset witnesses and integer parent/base
references. The exact base-plus-delta source can be reconstructed on demand.
Warm append avoids full-source normalization, index reconstruction, full core-key
copying and solver expansion. Parent versions are archive-local checked handles;
they do not identify arbitrary externally supplied full CNFs. Unsupported edits
require a newly acquired base, while older versions and results remain immutable.

[The matched comparison](../experiments/results/cnf-positive-history/README.md)
preserves 24 histories / 4,848 decisions / 48 compressed archives. At 16 holes
and 128 redundant additions, retained logical payload drops from 10,957,771 to
118,668 bytes and SQLite size from 15,130,624 to 237,568 bytes. At four holes and
512 additions, logical payload drops from 6,034,220 to 45,043 bytes. The last
append reads its new clause, performs four containment probes, writes one small
delta and invokes no residual-solver operation. All 265 preceding candidate
archives replay with unchanged row digests and no new expansions.

All 230 Python tests pass, including exact reconstructed sources, SAT/UNSAT
witness behavior, sparse variable names, forks, duplicate operations, changed
constraints, cold corruption checks and a 1,200-step iterative cold replay.
Lean proves `positive_history_models`; its audit passes 4,067 declarations /
1,929 theorem declarations. This semantic proof does not verify the Python
implementation, its SQL identity protocol or its machine costs. The new API is
separate from the production solver, whose result archive was not targeted.

**Remaining costs and preserved failures:** cold query validates the base and
all required ancestor deltas; the 512-addition history checks 513 records. Full
source export remains charged, and novel constraints materialize and solve a
fresh base. Thirty-two new units grow logical storage from the old interface's
30,657 bytes to 57,756. Repeating one identical clause on successive parents uses
11,742 bytes versus 1,410 after old CNF normalization; repeating the identical
parent/operation reuses a version but still pays table overhead. The mixed
history also loses slightly. These cases remain in the archived comparison.
SAT timings expose the different witness-output interfaces; the old solver
returns a model on every call, while the history API exports it separately.

**Next concrete reuse patterns:** compress repeated event runs or separate
semantic no-op versions from exact event provenance; share unchanged source
structure when a new base is required; and consider the simpler monotone rule
for adding clauses to an already checked UNSAT base. The current uniform
positive-subset protocol does not exploit that negative-only shortcut. The
earlier subsumption policy regressions, cold-validation cost and arbitrary
irreducible positive overlap remain open. None of these measurements proves
minimum expansion work for every case or polynomial acquisition for all SAT.

Final validation: Proposition 12.29 states the history invariant and retained-bit
bound. All 40 previous manuscript proof blocks are unchanged; there are now
41 proofs and 153 unique labels. The 80-page PDF builds without warnings or
overfull/underfull boxes; pages 72/73 and adjoining page 74 were rendered and
visually inspected. All 48 new snapshots decompress to their recorded hashes,
and source fingerprints match the report. An independent gzip replay records
the final handles for all 24 history snapshots and checks their exact source
recipes, answers and unchanged row digests in `history-replay.json`. Code,
formalization and comparison evidence were committed and pushed in `fa7feb6`;
the manuscript and final validation follow in the next checkpoint.


## 2026-11-08: arbitrary UNSAT additions and surviving SAT assignments

Implemented two further reuse cases in the separate CNF history prototype.
`append_decision` accepts any well-formed signed clause, including an empty one,
over a checked UNSAT base. For a SAT base it accepts exactly when the fixed
stored assignment satisfies the new clause, treating missing variables as false.
The latter preserves a witness and verdict, not every base model. A failed model
supplies no UNSAT conclusion and writes no version. Fresh solving remains the
fallback. The old positive-subset API and its persisted records remain supported.

Both new record kinds retain exact clauses and parent/base references. Cold
replay checks every required ancestor and its rule against the checked base.
Warm accepted additions avoid subset discovery and residual solving. Syntax,
model probes where applicable, serialization, SQL indexing, preparation, source
export and cold replay remain charged. Deletion/replacement and externally
mutating already checked cached rows are outside the append-only interface.

[The matched comparison](../experiments/results/cnf-decision-history/README.md)
retains 22 histories, 3,894 correct decisions and 66 compressed archives. For
size-16 SAT and 128 compatible signed additions, the preceding history interface
acquires 129 bases and retains 15,195,873 logical bytes; the new interface keeps
one base and 99,170 bytes. Summed base-plus-update time falls from 3.611 to
0.04691 seconds in single samples. The full-source comparator uses 9,235,556
bytes and 2.781 seconds. Size-16 UNSAT arbitrary additions fall from 3,670,847
to 109,468 bytes and 0.71682 to 0.05710 seconds versus positive-only history.
Actual SQLite sizes are recorded separately; these are not peak-RSS results.

Preserved counterexamples matter: repeated signed clauses use 8,926 bytes versus
1,396 with full-source deduplication; 32 fresh positive units still force 32
fallback acquisitions and 58,812 bytes versus 30,657. A failed model that remains
SAT and a true SAT-to-UNSAT transition both need one fresh base, then reuse it
for 31 additions. Size-16 UNSAT cold replay takes 10.13 ms versus 5.94 ms for the
preceding history's isolated final base and 1.57 ms for the full-source cache,
whose input now contains an empty clause. No universal runtime gain follows.

All 235 Python tests pass, including 320 enumerated base/clause combinations,
model-set shrinkage, sparse assignments, failed-model non-refutation, mixed
legacy/new records, malformed and forged deltas, and 1,200-step UNSAT replay.
Lean adds four semantic lemmas for fixed-model and refuted histories; its audit
passes 4,071 declarations / 1,933 theorem declarations with standard axioms only.
These proofs do not verify Python, SQL or machine costs. All 313 earlier
archives replay unchanged with no new expansions. Every new compressed archive
was separately reloaded and checked against its exact source recipe and row
hash. The production solver and result archive were not targeted.

**Next expansion priorities:** (1) allow small checked model repairs and share
source structure across new bases; (2) compress repeated event provenance while
preserving old version identities; (3) reduce cold history validation and avoid
unused eager positive-index preparation. In particular, a positive unit on a
genuinely fresh variable can extend a model, but absence from the base model
does not prove freshness: previous deltas may constrain it. An occurrence or
other explicit invalidation invariant is required. General irreducible positive
overlap and unrestricted polynomial construction remain open. The new cases
reuse already acquired answers; they do not bound acquiring every CNF.

Manuscript validation: Section 12.38 and Proposition 12.30 now state both rules,
prove their distinct invariants, and report the comparison and losses. All 41
previous proof blocks remain unchanged; the paper now has 42 proofs and 155
unique labels. Two LaTeX passes produce an 81-page PDF without warnings or
box overflows/underflows. Pages 73/74 and adjoining page 75 were rendered and
visually inspected. The implementation, proof and experiment checkpoint was
committed and pushed as `8ad5f8e`; this manuscript update follows separately.


## 2026-11-08: checked pure-literal model repair without fresh base copies

Implemented the next recorded case in `experiments/cnf_repair_history.py`.
If the current assignment fails a new clause, it may change one literal to true
only when its opposite occurs nowhere in the complete parent source. This
protects all old clauses, handles both fresh and existing pure variables, and
retains fallback when the sufficient condition fails. A persistent binary trie
shares positive/negative occurrence flags and assignment values across versions.
It indexes exact original clauses and every delta, including tautologies and
prior non-repair additions. Older branches and models remain unchanged.

Cold verification reconstructs the derived index from checked source records and
validates each repair. The new reader accepts older history formats; old readers
reject new repair records. The preceding base class gained a certificate hook
with unchanged legacy behavior. Production code and its result archive remain
untouched. The Python trie/SQL checker is outside the Lean trust boundary.

[The comparison](../experiments/results/cnf-repair-history/README.md) preserves
20 histories, 3,924 correct decisions and 60 archives. At size-16 SAT with 128
fresh positive units, the preceding decision history acquires 129 bases and
retains 12,020,154 logical bytes. Repair keeps one base and 100,706 bytes; summed
acquisition/update time falls from 2.61853 to 0.07326 seconds. SQLite size falls
from 21,618,688 to 208,896 bytes. The last append uses 88 trie-node visits,
allocates 28 nodes across its assignment/support updates, and performs no solver
work. The final version set shares 2,048 distinct trie nodes. Separate tracing
reports peak Python allocations of 77,265,863 versus 1,740,168 bytes; it excludes
native SQLite allocations and total process RSS. Timings are single samples.

The accepted warm operation uses O((d+1)b) trie-node work for d literals and
b-bit identifiers, plus syntax, bit serialization, integer, dictionary and SQL
costs. Whole-parent scans/model copies are absent. Preparation and cold history
checking remain charged; size-16 cold query takes 13.20 ms versus 7.58 ms for
the preceding final fresh base. Exact source export and sparse witness output
are optional and explicitly measured. No unrestricted acquisition bound follows.

Preserved losses identify further structure. A parent containing (1) and
(-x or 1) permits changing x, but the pure-literal test rejects it. Both histories
fall back 32 times in this control, and repair adds overhead. Repeated units
retain 10,719 bytes versus 1,393 with full-source deduplication. Already-compatible
additions raise peak traced allocations from 108,869 to 249,217 bytes. Thirty-two
variables near 2^1024 create 32,801 trie nodes and take 38.73 ms versus 33.18 ms
for decision fallback; cold replay takes 25.29 ms versus 0.22 ms. These are
retained counterexamples to universal speedup, not omitted failures.

All 242 Python tests pass. They include 168 enumerated base/clause combinations,
300 seeded branching proposals, sparse 1,201-bit index keys, 128-repair cold
replay, exact source/witness checks, old API compatibility and forged-record
rejection. A base tautology preserving the normalized solver key still changes
support and correctly invalidates a claimed repair. Lean proves the signed
occurrence update and pure-repair preservation/extension rules; the axiom audit
passes 4,079 declarations / 1,939 theorem declarations. It does not verify the
integer parser, trie, persistence or machine costs. All 379 preceding archives
replay without row changes or new expansions. Every new compressed archive was
independently reloaded and matched to its exact source and row hash.

**Next bottlenecks and recognition requirements:**
1. Check affected opposite-sign clauses (or retain true-literal counts) to allow
   safe flips that purity rejects. Every affected prior occurrence must be found;
   a small affected set is an explicit condition, not an arbitrary-SAT guarantee.
2. Compress long unary trie paths for sparse identifiers. Exact identifiers and
   source serialization still cost their bit length. The current map uses one
   node per bit on an updated path.
3. Prepare the repair index lazily or select it by measured reuse. Compatible
   streams should not always pay eager support maintenance; activation/restart
   must still reconstruct and charge all earlier constraints.
4. Share fresh-base source structure and compress repeated provenance without
   losing historical versions. Repair rejection still triggers copied bases.
General irreducible overlap, arbitrary model repair and uniformly polynomial
construction for every CNF remain open.

Manuscript validation: Section 12.39 and Proposition 12.31 now give the repair
rule, proof, shared-index accounting, allocation measurements and counterexamples.
All 42 earlier proof blocks remain unchanged; the draft has 43 proof blocks and
157 unique labels. The 82-page PDF builds without warnings or box overflows or
underflows; pages 74/75 and adjoining page 76 were rendered and visually checked.
Code, proofs, all measurements and earlier-archive verification were committed
and pushed as `5c9f5ea`; the manuscript checkpoint follows separately.

## 2026-11-08: cost-directed priorities across SAT categories

The hourly investigation now starts from the compact
[structural-reuse cost map](structural-reuse-priorities.md). Its prompt was
shortened to identify the dominant remaining runtime or memory cost, choose one
gap with the highest credible total saving, compare on matched workloads and
update the ranking. The hourly schedule, target chat and notification intent
are unchanged.

[Five new diagnostic profiles](evidence/2026-11-08/reuse-cost-profile/README.md)
retain fresh archives without changing any preceding results. They distinguish
reacquisition after failed repair, residual search, sparse-identifier index cost
and persistence on already-cheap updates. In their respective instrumented
controls, trie lookup/update accounts for about 62% of exclusive time and SQLite
execution/transaction-context exit for about 87%. These are separate workloads,
not a global phase breakdown or uninstrumented speed claim.

The immediate next experiment is checked nonpure single-variable repair with
versioned affected-clause counts. The existing blocked-but-SAT control still
acquires 32 new bases unnecessarily. Broader opportunities are retained
propagation/class state, mixed-class boundary summaries, and shared source/proof
dependencies across class transitions. The cost map gives their recognition and
invalidation conditions, resource limitations and a workload-driven ranking.

This checkpoint adds analysis and profiling evidence only. General repair,
small interfaces for every CNF, compact closure and uniformly polynomial
acquisition remain open. The Python prototype is still outside the Lean
implementation trust boundary; no manuscript theorem was strengthened here.
Cold validation checks all 356 versions and 58 residuals in the five new archives
with no new expansions or database-byte changes. New local documentation links
resolve; the diagnostic runner refuses an existing output directory. No solver
code changed, so the prior full solver test/audit results are not claimed as
newly rerun checks.

## 2026-11-08: checked affected-clause repairs avoid copied fresh bases

Implemented the top cost-map experiment in `experiments/cnf_affected_history.py`.
The new interface keeps exact distinct-true-literal counts and variable-to-clause
occurrence lists in immutable versioned tries. It accepts a single-variable
change only when all affected old counts remain positive. Tautologies have zero
net count change; duplicate literals do not create false protection. Candidate
occurrence visits are budgeted. Rejection supplies no verdict and retains
ordinary solving as fallback. Cold checking rebuilds all derived indexes from
exact checked history, with no trusted persisted count or affected-clause list.

The [matched experiment](../experiments/results/cnf-affected-history/README.md)
retains 35 cases, 7,230 correct acquisition/update/replay decisions and 70 archives.
The original 32-fallback control now has zero fallbacks. On matching SAT size 16
with 128 protected flips, bases fall from 129 to one, operation time from 3.47813
to 0.14730 s and logical archive payload from 12,460,337 to 158,332 bytes. Separate
tracing reports peak Python allocations of 86,261,287 versus 2,837,728 bytes,
excluding native SQLite and process RSS. The last update checks one old clause
in discovery and again in verification; it performs 202 trie-node visits and
allocates 66 trie nodes without residual solving. At 512 protected flips the
operation sum falls from 5.05929 to 0.32684 s. These are single synthetic samples.

Losses are retained: compatible streams roughly double traced index allocations;
sparse-ID paths also nearly double peak allocations; cold replay is more costly.
A single flip affecting 4,096 old clauses avoids fallback but takes 125.48 ms
versus 109.99 ms because index preparation dominates. Budget exhaustion and a
coordinated-flip example still require fresh acquisition. A separate first
screening run overlapped with tests/builds and is retained without being used
for primary timing claims.

All 249 Python tests pass, including exact index reconstruction, 294 base/clause
combinations, 400 seeded branching proposals, forged records and old/new format
checks. Lean proves `affected_repair_preserves` and `affected_repair_extension`;
the axiom audit passes 4,081 declarations / 1,941 theorem declarations. These
semantic proofs do not verify the Python count maps or SQL. All 439 preceding
benchmark archives replay without new expansion or changed rows. Independent
decompression/replay checks every version and residual in the new primary and
screening archives, with exact source/witness checks and unchanged database bytes.

**Next target:** selectively activate the stronger index, keeping the pure path
for streams that need no nonpure repair. Account for first activation, all later
constraint maintenance and cold reconstruction. The current node-operation
bound is O((d+1)b + (k+r+1) log(m+2)), for d new literals, b-bit variable IDs,
m parent clauses, k discovery occurrence visits and r affected old clauses.
r can equal m. Coordinated repairs, general small affected sets, shared fresh
base sources and unrestricted polynomial acquisition remain open.

Manuscript Section 12.40 / Proposition 12.32 states the distinct-literal count
identity and its proof, the versioned index accounting, measurements and losses.
All 43 previous proof blocks remain unchanged; there are now 44 proofs and 159
unique labels. The 84-page PDF builds without LaTeX warnings or box diagnostics;
pages 75--78 were rendered and visually reviewed. Both new experiment runs were
independently replayed: 140 archives, 14,180 historical versions and 2,568 residual
records, with zero new expansions and unchanged database bytes.
The implementation, proofs, tests and preserved experiment checkpoint was
committed and pushed as `15e9c9e`; this manuscript and priority update follows.

## 2026-11-08: structural reuse across SAT categories, after single-variable repair

The [new diagnostic](../experiments/results/structured-repair-gaps/README.md)
finds 240 single-variable repair misses across 12 equivalence, parity and matching
histories. Every new unit has an independently checked coordinated repair; no
rejection exhausts the discovery budget. Equivalence needs a whole block flip,
parity needs two flips, and the matching control needs a four-indicator swap.
These supplied transformations are not yet a discovered/certified repair API.
The generator knows the structure, and full-source checking of supplied moves
is diagnostic validation rather than a measured optimized path.

For 32 equivalence blocks of 32 variables, the current implementation retains
33 bases and 3,792,631 logical bytes, taking 2.697 s for base preparation and the
32 rejected-update/fallback operations. The matching control with 32 independent
4-by-4 blocks retains 33 bases / 2,267,324 bytes and takes 0.946 s. Single samples
show repeated acquisition on these constructed easy families; they do not measure
the speed of a replacement or characterize typical SAT workloads.

The cost map now promotes checked simultaneous equivalence-block repair as the
next research experiment. Shared component source, witnesses and typed states
are the enabling architecture. Current positive residual records flatten models
and discard the solver's matching/implication state; new bases still copy their
source. Several class views can describe the same component, so class labels
should not define storage identity. Mixed-component boundary summaries and
structure-aware branching remain the larger search-growth opportunity.

Simultaneous repair must accumulate clause-count changes before checking: an
intermediate assignment may be invalid while the final assignment is valid.
Internal preservation does not keep old per-clause count indexes current for
free. Maintain them or explicitly invalidate/reconstruct them, and check every
affected external constraint and earlier addition. Selective index activation
remains a smaller engineering fix for the already measured allocation losses.

The diagnostic retains 12 new archives, exact sources, model-dependent additions,
proposed moves and source fingerprints. Independent decompression/replay checks
all historical versions, candidate moves and residual records without new
expansion or changed database bytes. Solver code and manuscript claims are
unchanged; the existing full test/audit results were not rerun for this analysis.
The established heterogeneous-backdoor and component-depth literature remains
the basis for the proposed mixed-class search direction, not a novelty claim.

## 2026-11-08: checked simultaneous equivalence repair

Implemented `EquivalenceRepairHistory`, with lazy per-base discovery of connected
variables in complementary binary clause pairs. The existing single-variable
rule runs first. A generic joint record stores the exact addition and changed
variables. Its independent checker aggregates all affected count changes before
checking the final assignment, including external clauses and earlier additions.
Old assignment/count roots remain immutable, and cold replay reconstructs all
indexes without trusting discovery or stored derived counts. New equivalences in
deltas and nonpaired implication SCCs are intentionally not discovered.

The [matched study](../experiments/results/cnf-equivalence-history/README.md)
removes all 120 unsigned-chain misses plus 32 signed-chain misses. At 32 blocks
of width 32, summed acquisition/update time falls from 2.46892 to 0.06676 s,
logical storage from 3,792,631 to 98,663 bytes, SQLite from 6,668,288 to 204,800
bytes, and peak separately traced Python allocations from 45,575,163 to 1,925,402
bytes. Bases fall from 33 to one. These are synthetic samples; tracing excludes
native SQLite and process RSS. Cold final query grows from 40.88 to 44.42 ms;
repeating the last known update after restart takes 88.32 versus 45.98 ms,
including reconstruction and fresh proposal recognition.

All 23 histories retain 46 archives, 1,144 historical versions and 869 residuals,
checked without byte changes or fresh expansion. Another 82 prior archives
(7,342 versions / 1,782 residuals) replay unchanged. The 255-test Python suite
passes, including randomized branches, exact count/posting recomputation,
couplings, signed/repeated changes, contradictory and budgeted cases, and forged
records. Lean adds `joint_repair_preserves` and `joint_repair_extension`; the full
build and axiom audit pass (4,083 declarations / 1,943 theorem declarations).
These are semantic protection lemmas, not a refinement of Python or SQL.
The verified implementation/evidence checkpoint is `12ae27a`, pushed to main.

The initial comparison is preserved separately: complementing the unsigned input
recipe produced signed additions already true under the solver's chosen model.
The corrected control explicitly forces 32 signed repairs. Its run also measures
cold resumption separately from querying the final version. No timing samples
from the two runs are pooled.

Remaining costs are explicit. A 1,024-variable block exceeds the default
4,096-visit discovery budget and still falls back. Every block variable and
internal posting is visited; zero-net counts avoid writes, not discovery/check
visits. Move lists are repeated in durable records, and assignments are not
represented by one group bit. Compatible and scalar-only histories never build
the new block index, although their older affected-clause indexes remain eager.
The resource-bounds document records recognition, checking, retained paths,
temporary aggregation, serialization and cold costs separately.

**Next target:** matching-state reuse and discovered alternating moves through
the joint checker. The 32-block, 4-choice control still requires 32 fallbacks,
retains 33 bases / 2,267,324 logical bytes, and takes 1.002 s on the new path
versus 0.934 s on the scalar baseline. Parity remains another missed adapter.
Both need prior-addition/external-constraint checks and explicit budgets; the
generic checker alone provides no procedure for finding a valid move. Shared
source/component state across genuine fallback remains open. No unrestricted
polynomial expansion or acquisition claim follows.

The manuscript now contains Section 12.41 and Proposition 12.33, with the joint
count identity, proof, discovery restrictions, operation/storage bounds and
matched gains and losses. All 44 earlier proof blocks are preserved, with one
new proof and 161 unique labels. `latexmk` builds the 85-page PDF without final
warnings or overfull/underfull boxes; pages 76--79 were rendered and inspected.

## 2026-11-08: retained matching state and alternating proposals

Implemented `MatchingRepairHistory` as an optional layer over the existing joint
checker. After scalar/equivalence failure, it recognizes a strict whole matching
base, retains selected choice/resource endpoints and earlier unit pins in shared
tries, and searches for an alternating path to satisfy the requested literal.
Accepted moves use the existing `append-joint` format and independently check
every affected original or added clause. Warm updates maintain only changed
endpoints; old versions remain immutable. Cold final checking requires no graph
state, and the previous equivalence reader accepts matching-generated records.

The [matched study](../experiments/results/cnf-matching-history/README.md) removes
all 80 matching misses from the prior diagnostic and avoids 161 acquisitions
across the enlarged 37-case matrix. At 32 four-choice blocks, operation time
falls from 0.92416 to 0.04882 s, logical payload from 2,267,324 to 50,257 bytes,
SQLite from 3,973,120 to 110,592 bytes, and separately traced peak Python
allocations from 24,840,875 to 1,192,534 bytes. Bases fall from 33 to one.
At 32 eight-choice blocks, time falls from 8.30345 to 0.25308 s and logical
payload from 20,331,832 to 424,089 bytes. Input sizes, graph recognition, failed
proposals, state maintenance, checking, serialization and persistence are charged;
tracing excludes native SQLite and RSS, and timings are single synthetic samples.

Cold final replay for four-choice blocks increases from 17.93 to 20.25 ms.
Repeating the last known update after restart takes 40.03 versus 23.46 ms,
including graph/view reconstruction; both archives already contain its result.
The last warm move scans two graph edges, changes four indicators, visits 16
postings in discovery and again in checking, updates four matching endpoints
and allocates 182 trie nodes. It performs no base scan or new residual solve.
A 64-choice cycle changes 128 indicators and visits 256 postings per pass, so a
unit addition can still affect the whole component.

All 261 Python tests pass. New tests include 400 branching unit histories
checked against all permutation models of a three-choice square instance, exact
count/endpoint/pin reconstruction, long cycles, free resources, old versions,
budget failure and cold/older-reader compatibility. All 74 new archives (1,414
versions / 608 residuals) and 58 prior archives (1,396 versions / 1,367 residuals)
replay with unchanged bytes and zero new expansion. The verified implementation
and evidence are committed/pushed as `5181faf`. The Lean build reuses the
existing joint semantic lemmas; its audit passes unchanged at 4,083 declarations
and 1,943 theorem declarations. No new graph/index/runtime refinement is claimed.

Retained failures are informative. Search tries one path per literal. A non-unit
coupling can defeat it while a longer valid cycle exists; a unit prohibition
guides search around the corresponding edge successfully. A disjoint unrelated
equivalence component prevents whole-base matching recognition. Parallel
indicators, unused negative-only indicators and new graph structure are also
outside recognition. With spare resources, a valid model can select extra
indicators in one choice; that invalidates the optional matching view, and
discarding an extra indicator may violate an earlier unit. All such misses
remain satisfiable controls or explicitly checked contradictions, not inferred
UNSAT verdicts from proposal failure.

The literature check confirms this is established matching machinery:
[Régin (1994), pp. 364–366](https://cdn.aaai.org/AAAI/1994/AAAI94-055.pdf) uses
alternating paths/cycles and retains a known matching while propagating edge
deletions. The manuscript's Section 12.42 cites it and distinguishes our
persistent, full-source-checked integration from that prior algorithm and its
complete filtering. All 45 previous proof blocks are preserved, with 162 unique
labels. The 87-page PDF builds without final warnings or box errors; changed
pages 78--80 and the added reference link on page 86 were visually inspected.

**Next measured target:** the 1,024-variable equivalence-block budget rejection
still takes 0.786 s, including about 0.741 s after preparation. Evaluate a charged,
structure-aware budget escalation or smaller checking representation against
fallback, retaining adverse high-degree controls. Do not raise all search budgets
without a total-cost comparison. Parity remains the largest measured repeated
miss stream (32 fallbacks / 0.170 s / 326,256 bytes). Preparation dominates the
successful larger matching stream (206.58 of 253.08 ms), so profile it before
optimizing its cheap path search. Component extraction and coupling-guided path
search have credible cross-category potential but need scaled evidence. General
SAT acquisition, closure size and uniform polynomial expansion remain open.

## 2026-11-08: bounded retry and the next measured bottleneck

Implemented optional `BudgetedRepairHistory` over the unchanged matching engine.
After ordinary failure it may retry only the first exhausted recognized base
block, with min(32,768, 8*q) variable/posting visits, at most 8,192 variables and
64-bit identifiers by default. It retains a reference to the existing tuple,
charges all failed work and uses the unchanged independent joint checker and
archive format. Discovery exhaustion never implies UNSAT. Completed rejections,
matching paths and unrecognized structures do not receive this retry.

The preserved [screening](../experiments/results/cnf-budget-screening/README.md)
motivated a [27-case, three-policy comparison](../experiments/results/cnf-budgeted-history/README.md).
At 1,024 variables, total operation time falls from 0.78490 to 0.05932 s,
expansion from 739.17 to 13.29 ms, logical payload from 189,168 to 99,129 bytes,
SQLite from 356,352 to 196,608 bytes and peak traced Python allocations from
3,071,073 to 1,741,448 bytes. Bases fall from two to one. At 4,096 variables,
total time falls from 11.88170 to 0.27261 s and expansion from 11.67323 to
0.05553 s. These are single synthetic timings, with allocation tracing separate.
The report charges preparation, failed discovery, checking, maintenance,
serialization, persistence and fallback; input assembly and audits are separate.

The simple alternative is important: globally raising the budget to 32,768
is slightly faster on the successful chains and also solves dense controls that
the targeted cap rejects. On 1,024 variables with 8,192 tautologies, the targeted
policy still takes 0.89334 s with fallback, versus 0.11656 s for the raised
policy. No expected-cost superiority or optimal budget claim is supported.
The pinned 2,048-variable conflict pays 40.36 rather than 31.01 ms expansion
because the extra check correctly rejects it. Cold final replay on the plain
1,024-variable chain increases from 43.48 to 45.25 ms. The global/targeted
tradeoff, caps and failures are retained, not hidden by the successful examples.

All 268 Python tests pass, including 120 random branching additions, old-version
count reconstruction, limits, disabled discovery, conflicts, rejected-operation
immutability and older-reader replay. All 81 new archives (582 versions / 357
residuals) and 74 preceding matching archives (1,414 versions / 608 residuals)
validate through the previous matching reader with unchanged bytes and zero
new expansions. The proposal policy adds no formal theorem: the existing Lean
joint semantic rules remain the boundary; Python indexes and resource accounting
are not refined by them. Source fingerprints match the recorded experiment.

**Next target:** repeated-scan unit propagation. The new pinned 2,048-variable
control spends 2.67 s in preparation. A separate in-memory cProfile run attributes
8.778 of 8.939 instrumented seconds (about 98%) to `propagate` and its callees,
with 16,779,261 charged literal visits for 8,189 source occurrences. Implement
an occurrence-driven queue with independently checked reasons, charging setup,
queue memory, conflicting/easy controls, fallback and cold replay. Preserve old
certificates; no speedup is yet claimed for this unimplemented change. Thereafter
address inert/dense postings and cost estimation, parity-preserving repair,
mixed-component extraction and coupling-guided alternative paths. General SAT
branching/closure and compact arbitrary-CNF representations remain open.

The manuscript's Section 12.43 now reports the budget comparison, regressions,
resource limits and next propagation target. It also makes the arbitrary-SAT
obligation concrete: G = AND_i(z OR C_i) has an immediate witness z=true, but
adding the single unit NOT z makes satisfiability equivalent to arbitrary
F = AND_i C_i. Cheap old witnesses therefore do not guarantee cheap expansion;
expensive preparation may have absorbed the unresolved work. This argument does
not rule out such preprocessing. The arbitrary-SAT research record now separates
complete fallback coverage from missing uniform recognition, composition,
representation, acquisition and update bounds.

Implementation/evidence checkpoint `df41bee` is pushed. The Lean build and audit
pass unchanged at 4,083 declarations / 1,943 theorem declarations. All 45 previous
proof blocks are unchanged, with 163 unique labels. The final PDF compiles without
warnings or box errors; changed pages 80--81 were visually inspected.

## 2026-11-08: prioritize pattern discovery and exact coverage

The user redirected the next iterations toward discovering SAT patterns and a
valid partition of the entire SAT problem. Known-family optimization remains
useful supporting work. The previous propagation-first execution order is
superseded by this research priority; its profile and all earlier results remain.

The new `research/sat-pattern-discovery.md` defines the first milestone: an
audited pattern inventory over existing residual-solver capabilities, tested on
unlabelled CNFs, exhaustive small cases and adversarial mixtures/edits. Record
all recognition outcomes and positive certificates, including overlaps; describe
unresolved cells and their interactions rather than only counting successful
specialized routes. A failed bounded recognizer is not a semantic exclusion.
Deterministic, versioned outcome vectors provide an exhaustive disjoint reporting
partition, but do not by themselves constitute an efficient structural solution.

The plan distinguishes whole-input classification from exact conditioning and
component decomposition within a formula. Shared-variable compatibility remains
explicit. Discovery, recomposition, compactness, acquisition and update costs
are separate obligations. The next discovery is selected by coverage and insight
into unresolved interaction, with total cost measured. Existing Horn/dual-Horn,
2-CNF, matching, component and variable-split paths are starting capabilities,
not missing features to reimplement.

The hourly heartbeat prompt now follows this discovery-first direction, keeping
its hourly cadence, active state and existing chat. It still requires preserved
results, tests, verified commits/pushes and quiet operation without material
progress. This checkpoint changes plans and scheduling, not solver behavior or
mathematical results; no manuscript change or new solver tests are needed.

## 2026-11-08: first persistent SAT pattern inventory

Implemented `PatternInventory` as a separate analysis layer using existing
residual helpers. It records seven overlapping syntax/witness outcomes, a
complete direct single-parity encoding certificate within a width cap, exact
source/name bindings, independent component partitions and bounded variable
conditioning. Failed recognition and all attempted alternative residuals remain
explicit and persistent. The SAT engine and its answer/certificate protocol are
unchanged; closed analysis means recognized-family coverage, not satisfiability.

The checker recomputes profiles, validates exact branch restrictions, and directly
reconstructs component source clauses with disjoint supports independently of
the component discoverer. A test injects a faulty overlapping discoverer and
confirms rejection. The parity argument uses distinct full-width clauses to
exclude exactly one half of the Boolean cube; hidden affine equivalence is not
recognized. Above the default eight-variable cap the outcome is unresolved.

The [664-input comparison](../experiments/results/cnf-pattern-inventory/README.md)
contains all 512 subsets of the nine non-tautological two-variable clauses,
120 seeded larger CNFs, 16 structural controls and 16 variants. The tiny sources
normalize to 257 distinct residuals, with exact originals preserved. There are
24 observed root signature cells. Of the other 152 inputs, whole-formula tests
explain 39, independent components 45, one conditioning level 57, and two levels
102. Pointwise checks cover both candidate restrictions and component assignment
recomposition on small inputs, including alternatives not selected for the final
coverage summary. Generator labels are never passed to discovery.

The costs are explicit: analysis plus unchanged solving takes 2.02127 s at two
levels versus 0.30139 s without analysis; analysis alone costs 1.70180 s. SQLite
increases from 385,024 to 6,459,392 bytes. All modes retain the same 699 ordinary
solver residuals. Two-level analysis adds 2,801 pattern nodes (3,688,352 logical
bytes) and 664 sources (452,011 bytes). Cold full audit increases from 20.49 to
362.41 ms. Separate tracing on six mixed/guarded cases measures 60,634 versus
205,298 peak Python bytes, excluding native SQLite/RSS. No solver acceleration
or representative-distribution claim is made.

All 276 Python tests pass. The five final archives contain 4,740 pattern nodes
and 2,656 sources in total, with 699 solver residuals per archive; they replay
without byte changes or new solving. The initial five-policy run and source
snapshots are preserved separately because its component checker only rederived
the discovered groups. All those valid initial archives also pass the stronger
final direct-partition checker unchanged. Recorded source fingerprints match.
The existing Lean conditioning identity is relevant, but no new refinement of
this Python inventory, parity recognizer or SQLite is claimed.

**Next discovery target:** 50 inputs remain unresolved after two levels: 42
seeded CNFs and four structural cases with variants. Forty-eight occupy the
all-excluded pattern cell; two exceed the parity cap while failing other tests.
The controlled misses are five/six-variable complete exclusion cubes, coupled
matching/parity and an activated guarded formula. Refine these connected cells
by exact clause support and sign patterns: complete parity halves, explicit
contradictions and collections of parity equations, preserving leftover couplings.
Evaluate the same recognizer on all unresolved inputs and variants, and retain
zero or negative results on random CNFs. Raising conditioning depth alone is
not the chosen next step. General efficient discovery, compact closure and
polynomial arbitrary-CNF acquisition remain open.

Implementation and evidence checkpoint `c1f39a0` is pushed. The manuscript's
Section 12.44 now records the classifier, elementary direct-parity argument,
exact recomposition checks, coverage gains, overhead and retained unresolved
cases. The Lean build passes unchanged (4,083 declarations / 1,943 theorem
declarations); no new implementation-refinement claim is made. All 45 prior
proof blocks are preserved, with 164 unique labels. The 89-page PDF compiles
without final warnings or box errors, and changed pages 81--82 were visually
inspected. The next discovery target is persisted in both research priority files.

## 2026-11-08: support/sign extraction with exact affine couplings

Implemented the planned connected-cell refinement in
`experiments/cnf_affine_patterns.py`. Complete parity halves on each support
become equations; every other clause remains in an exact leftover list. The
independent checker verifies source partition, supports, distinct signs, counts
and triangular elimination dependencies. Pure systems and contradictory affine
subsystems add separate outcome fields. Mixed consistent systems remain open.
The policy version is in every identity, and old inventory rows/decisions are
unchanged. This is an optional analysis layer, not solver/history integration.

The [preserved 733-source comparison](../experiments/results/cnf-affine-patterns/README.md)
includes all earlier sources plus growing systems, couplings, fresh random CNFs
and adversarial edits/variants. At depth two it closes 14 of the prior 50 open
inputs, leaving 34 seeded CNFs and coupled matching/parity with its variant.
The eight seeded gains use contradictory width-one/two equation subsystems
after conditioning. They are not evidence of discovering large hidden parity.
Five of 48 fresh seeded cases also gain closure, with the same limitation.
Whole-input random closure does not improve. The exact mechanisms and remaining
interfaces are persisted in `mechanisms.json` with an analysis script.

Across all 733 inputs, depth-two analysis plus solving falls from 3.30542 to
2.90083 seconds and SQLite from 14,323,712 to 13,385,728 bytes. Pattern nodes
fall from 3,790 to 3,126. On the original 664 sources total time stays almost
unchanged (1.84691 versus 1.84100 seconds). Depth-zero storage increases by
491,520 bytes. Coupled controls retain recognition overhead: the 16-equation
case increases from 0.05067 to 0.07849 seconds without closure. These are single
sequential samples. Separate six-case Python memory, warm reuse and cold audit
are included; the report distinguishes them from acquisition and process RSS.

All 284 Python tests pass, including exhaustive pointwise checks, random mixtures,
renamings, corrupt certificates, faulty discovery, and coexistence/cold replay
of old and new versions. All five new archives and all five prior final archives
replay without changes or new solving. Previous evidence is preserved.

**Next target:** exact projection and composition at affine/coupling interfaces.
The 32-equation coupled source has 66 variables but only two shared with its
one leftover binary clause. Current frequency-first conditioning misses this
opportunity. Retain arbitrary leftover clauses, checked witness lifting and
refutation semantics, with projection and persistence cost charged. Test the
matching/parity control and all unresolved random cases too. No new Lean
implementation refinement, efficient universal partition, compact universal
oracle or unrestricted polynomial SAT algorithm is established here.

Implementation/evidence checkpoint `e1e7608` is committed and pushed. Manuscript
Section 12.45 adds the exact extraction proposition and proof, checked elimination
scope, matched coverage/costs, retained regressions and next interface target.
All 45 earlier proof blocks remain intact (46 total; 166 unique labels). The
90-page PDF builds without warnings or box errors; changed pages 82--83 were
visually inspected. The existing Lean build and axiom audit pass unchanged
(4,083 declarations / 1,943 theorem declarations). No new Lean theorem is claimed.

## 2026-11-08: checked affine projection and existential composition

Implemented `experiments/cnf_affine_projection.py` and a versioned optional
inventory policy. Internal-first elimination projects extracted equations onto
the variables retained by leftover clauses. Independent checks verify row
dependencies, exact boundary constraints, budgeted direct CNF encoding, child
identity/bindings and strict variable decrease. Models lift by back substitution
and are checked against the full parent CNF. Projection has existential semantics;
it is not pointwise equivalence on eliminated variables. A budget miss retains
the original planner. Exact originals and old archive rows remain unchanged.

The [775-source comparison](../experiments/results/cnf-affine-projection/README.md)
includes all previous 733 sources, growing 64/128-equation coupled cases, exact
boundary/budget controls with variants and 32 fresh affine mixtures. Six growing
coupled cases gain closure even at depth zero. Depth-two closure beyond the 512
tiny cases rises from 209/263 to 215/263. The original 664-source result stays
at 116/152 non-tiny inputs: 34 seeded CNFs and the matching/parity pair remain
open. Initial test expectations that projection alone would close matching/parity
were disproved and corrected to retain the miss. Its source shrinks from 13/61
variables/literals to 10/29; selected unresolved literals shrink from 22 to 18.

Total depth-two analysis plus original solving and root lifting falls from
4.47144 to 3.75039 seconds, SQLite from 22,913,024 to 19,030,016 bytes, and full
cold audit from 1.40055 to 0.98692 seconds. Depth-zero operation time/storage and
the six-case peak Python diagnostic increase. All regressions remain recorded.
The selected unresolved-literal aggregate falls from 31,924 to 1,579, dominated
by growing controls rather than new random coverage. At 258 variables, discovery
is 13.13 ms but original-source solving still takes 564.84 ms, identifying an
integration cost rather than further projection cost.

All 292 Python tests pass, including exhaustive two-variable affine systems and
boundaries, existential fibers, lifting, forged dependencies, encoding-budget
checks before enumeration and cold corruption/coexistence. All five new and five
previous affine-study archives replay without byte changes or new solving. New
Lean lemmas in `AffineCoupling.lean` compose the existing executable projection
theorem with a leftover predicate invariant on eliminated variables, proving
fiber/SAT/UNSAT equivalence. They do not refine the Python pipeline.

**Next target:** checked simplification and interface-aware conditioning of mixed
leftovers. The remaining matching/parity bridge has a positive-only variable;
setting it true exposes matching. Test this against both-polarity couplings and
all unresolved random cases. Native affine boundary rows would avoid the observed
direct-encoding cap; integrating projected decisions could avoid expensive
original-source solving. Keep these supporting opportunities distinct from the
primary unresolved discovery obligation and arbitrary-SAT resource bounds.

Implementation checkpoint `b98dbe2` is committed and pushed. The six growing
coupled systems all share exactly one archived projected child, confirmed by
the retained identity hashes; original sources and bindings remain distinct.
Manuscript Section 12.46 adds the projection proposition/proof, cost account and
negative results. All 46 prior proof blocks remain intact (47 total; 168 unique
labels). The 92-page PDF builds without warnings or box errors; changed pages
83--85 were visually inspected. The Lean build and axiom audit pass with 4,087
declarations / 1,946 theorem declarations, including the three new composition
lemmas. The next discovery and integration targets are persisted in both priority
files and the evidence README.

## Checked simplification in the structural inventory (8 November, 22:19 run)

The mixed-leftover target is implemented in `cnf_simplification.py`. Unit
propagation reuses the existing solver routine. Independent replay checks forced
clause reasons, conflicts and whole-residual pure rounds; exact source bindings
and assignments support checked model lifting. A new `simplify` node strictly
reduces support without consuming conditioning depth. Policies have distinct
identities and coexist with all older records. The decision solver is unchanged.

The [841-source comparison](../experiments/results/cnf-simplification/README.md)
contains all prior 775 sources, 48 harder random 3-CNFs, adversarial bridges and
variants, and growing unit/pure controls. Depth-two non-tiny closure rises from
217/329 to 290/329; all 36 original misses close. Most gains use standard unit
propagation: units-only closes 289/329 in 6.60422 s versus 7.15375 s combined.
Projection takes 8.09694 s; pure-only regresses to 8.50842 s. The combined archive
shrinks from 39,727,104 to 31,731,712 bytes; exact source payload increases.
Six-case traced Python allocation is nearly unchanged and excludes native memory.

The matching/parity source follows projection, pure bridge removal, then matching
at depth zero. Both-polarity bridges are retained unless valid propagation or
conditioning resolves them. All 32 affine mixtures close at depth two. However,
38 of 48 new random 3-CNFs and the renamed wide-boundary cap case remain open.
The random group costs 3.26227 of 4.62418 s of discovery and is the next target:
profile its alternatives and test structure-aware conditioning at matched work
budgets. The unit-only policy remains an essential cheaper comparator. Actual
projected decision integration and native affine boundaries are supporting gaps.

All 301 Python tests pass (22.72 s), including exhaustive small existential
fibers, lifting, arbitrary renamings, false purity, malformed reasons and cold
corruption/coexistence. All seven new and five previous archives replay unchanged;
every mode retains the same 2,146 ordinary solver residuals. The Lean build passes
without a new formal claim: existing condition/pure-repair semantics support the
argument, while Python and persistence remain outside refinement. The 1,162 new
simplification edges reference 550 distinct children; this is within-policy
reuse, not arbitrary semantic canonicalization. The pure-chain control's signed
chain is disconnected from its matching-plus-bridge component; its unused parent
profile work and repeated scans are explicitly preserved as costs, not concealed
as a connected-interface result.

Verified implementation checkpoint `d264f5e` is pushed. Manuscript Section 12.47
now includes the exact existential simplification proposition and proof, the
policy ablations, reuse counts, resource bounds and remaining misses. All 47
earlier proof blocks remain intact (48 total; 170 unique labels). The 93-page
PDF builds without warnings or box errors; pages 85--87 were visually inspected.
The persistent next target is the expensive unresolved random 3-CNF group, with
structure-aware conditioning compared against the cheaper unit-only policy.

## Conditioning choices and the cost of intermediate residuals (8 November)

The current run profiles the prior 48 random 3-CNFs and tests a fixed
MOMS-inspired shortest-clause ordering. `cnf_conditioning.py` supplies an optional
versioned policy; the original frequency ordering and archive identities are
unchanged. Both Boolean branches and all attempted alternatives are checked.
Counting and sorting cost O(L + v log v) word/comparison operations plus encoding
costs; there is no new recognition class or optimality theorem. The primary
literature link and exact variant are recorded in the evidence README.

The [949-source comparison](../experiments/results/cnf-conditioning/README.md)
keeps all 841 old sources and adds 72 fresh formulae plus 36 transfer controls.
At depth two/cap four, coverage beyond tiny exhaustive inputs rises from 322/437
to 330/437 against the unit-only baseline, but total time rises from 17.20315 to
20.24553 s and SQLite from 79,118,336 to 96,911,360 bytes. Only two of the eight
gains are fresh inputs. Relative to combined unit/pure processing there are six
gains and five losses, including old case 631. Keep the policy optional. Even
cap-eight frequency conditioning closes none of the 32 fresh 3-CNFs at 20/32
variables. Bounded misses are not lower bounds on every decomposition.

Fewer attempted candidates (4,300 -> 3,956) produce more distinct nodes
(9,162 -> 11,224). Logical simplification-node payload increases by 8,405,501
bytes, about 91% of the total increase. Repeated child references also fall.
The next concrete target is one checked edge combining a conditioning assumption
and its forced-unit closure. Retain reason references, parent identity, exact
reconstruction and model transport; compare with the current full intermediate
node representation before spending more work on lookahead. Preserve terminal
recognition behavior and charge cold replay. This optimization is not implemented
and cannot be counted as an achieved saving.

The development profile, all pilot losses, exact gain/loss sources, node-kind
byte totals, paths and five new archives are persisted. Five new and seven old
archives replay unchanged, and every mode retains the same 4,034 ordinary solver
residuals. All 306 Python tests pass (22.90 s), covering branch semantics,
exhaustive tiny cases, random mixtures, renamings/edits, candidate-order corruption
and policy coexistence. The Lean build/audit still passes at 4,087 declarations /
1,946 theorem declarations; no new formalization is claimed.

Implementation/evidence checkpoint `42cb199` is pushed. Manuscript Section 12.48
records the conditioning rule, verified prior-work citation, fresh-input limits,
coverage/cost tradeoff and the next checked-edge opportunity. All 48 earlier
proof blocks remain intact, with 171 unique labels. The 94-page PDF builds
without warnings or box errors; changed pages 86--88 and bibliography pages
93--94 were visually inspected. The policy stays optional and all prior results
and counterexamples remain available for subsequent runs.

## Checked conditioning/closure edges (9 November)

`cnf_fused_conditioning.py` implements the proposed contraction. It fuses only
conditioned children whose old next step was simplification. Recognized leaves
and independent components keep their priority. The edge stores the existing
unit/pure certificate and final child binding in parent IDs; checking rebuilds
the intermediate restriction, validates gates/reasons and checks the exact
target. SAT models lift through the branch assumption and are checked against
the full parent. Root/source and pre-existing intermediate records are retained.

The [949-source comparison](../experiments/results/cnf-fused-conditioning/README.md)
checks three policy pairs. Every root profile, coverage summary and acquired
candidate count is identical. The full archive analyzer checks all 3,999 OR plans
for identical choices, selected alternatives and final child CNF/depth/bindings
after contraction. All non-simplification CNF/depth pairs remain. This is corpus
evidence and executable checking, not a new Lean implementation refinement.

For shortest-clause ordering, nodes fall from 11,224 to 6,281, SQLite from
96,911,360 to 65,572,864 bytes, and total time from 21.16978 to 17.63829 s.
Frequency falls 17.33216 -> 15.97544 s and combined unit/pure falls 18.49975 ->
17.14480 s. Shortest-clause cold audit falls 7.89184 -> 6.93005 s. A separate
branch-heavy six-case traced Python peak falls 5,682,777 -> 3,756,516 bytes.
The old easy-case diagnostic grows slightly; warm replay and the in-memory pilot
retain runtime regressions. Native memory and full-corpus peak are unmeasured.

All 312 Python tests pass (25.12 s), including exhaustive branch fibers, model
lifting, terminal/component priority, invalid/missing reasons and transport,
cold corruption and coexistence. Seven new and five prior archives replay
unchanged; every mode retains the same 4,034 solver residuals. The Lean build and
audit remain at 4,087 declarations / 1,946 theorem declarations.

No new cases close. The shortest-clause policy still has 107 non-tiny misses,
and all measured policies miss the 32 fresh 20/32-variable 3-CNFs. Its remaining
payload is chiefly unresolved CNFs and OR alternatives. Next investigate bounded
unit-conflict probing on binary-rich conditioned residuals, using checked
refutations to justify forced values. Charge probes even when they consume no
branching depth, retain failures, and compare against the existing policies.
Repeated recognition is a supporting cost, not a reason to omit validation.

Implementation/evidence checkpoint `041303e` is pushed. Manuscript Section 12.49
states and proves the exact existential relation for a fused branch, records the
matched savings and regressions, and separates representation savings from new
structural coverage. All 48 earlier proof blocks remain intact (49 total; 173
unique labels). The 96-page PDF builds without warnings or box errors; pages
87--89 were visually inspected. The next run should start with the bounded
unit-conflict probing opportunity above, retaining the fused and unfused archives
as baselines rather than repeating the completed contraction experiment.

## Bounded checked failed-literal discovery (9 November)

`cnf_failed_literal.py` implements the next discovery step. After existing
family, component, simplification and projection priorities, it probes binary
variables in incidence order with an optional per-residual cap. A checked unit
conflict forces the opposite value; that assumption and unit closure reach the
child directly. Forced rewrites preserve arbitrary-branch depth but strictly
reduce support. All inconclusive probes, reasons, exact children and model lifts
are checked and retained. The ordinary SAT decision solver is unchanged.

The [1,025-input study](../experiments/results/cnf-failed-literal/README.md)
retains all 949 previous inputs and adds 64 random holdout formulas and 12
constructed/transfer/invalidation controls. At depth two and four conditioning
candidates, four-variable probing raises closure 358/513 -> 484/513 non-tiny
inputs and 19/64 -> 51/64 fresh random inputs. Its 126 gains include 88 SAT and
38 UNSAT inputs; no baseline closure is lost on this corpus. Total time falls
27.11056 -> 18.87839 s, SQLite 93,143,040 -> 65,056,768 bytes and full cold audit
10.07933 -> 6.41165 s. The one-variable policy reaches 465/513 in 18.93343 s.
All modes retain the same 5,379 ordinary solver residuals. Six-case traced Python
peaks fall; native/full-corpus peaks are unmeasured and warm time slightly grows.

Twenty-nine misses remain. Probing every binary variable on these sources closes
only cases 968 and 1024, at higher inventory time (6.81731 -> 11.49531 s), storage
and cold cost. The initial diagnostic omitted ordinary-solver tables, causing
the shared auditor to create tables and fail byte preservation. Its archive and
failure log are retained; final diagnostic archives initialize empty tables and
both replay byte-identically. No certificate correctness failure occurred.

Probe nodes now occupy 12.545 of 22.743 MB logical state. Profiling the largest
discovery miss, case 894, points to repeated restriction, unit propagation/checks
and normalization. More promising for discovery than raising the cap: 245
archived inconclusive-probe nodes already have a common literal propagated by
both assumptions, including 179 unresolved nodes. By Boolean case splitting
that consequence is forced. These counts include unselected alternatives; using
the facts is not implemented and does not yet add coverage. Next implement
checked common-consequence reuse from existing traces, retaining failed probes,
transport and dependency checks, then compare total cost and remaining cases.
Probe-chain sharing and occurrence-driven scans are supporting cost targets.

All 319 Python tests pass (27.38 s), including exhaustive fibers, random mixtures,
renamings/edits, corrupt reasons/assumptions/transports and cold coexistence.
Four new and seven prior complete archives replay unchanged. The two new Lean
lemmas `failed_condition_forces` and `satisfiable_failed_condition` prove the
semantic rule from a supplied refutation; they do not refine Python or SQLite.
The full Lean build/audit passes at 4,089 declarations / 1,948 theorem declarations.

Implementation/evidence checkpoint `7d4f068` is pushed. Manuscript Section 12.50
adds the failed-assumption proposition and proof, the binary-incidence gate
argument, verified prior-work attribution, matched results and cap limitations.
All 49 earlier proof blocks remain intact (50 total; 175 unique labels). The
97-page PDF builds without warnings or box errors; pages 89--90 and bibliography
page 95 were visually inspected. Resume with checked common-consequence reuse
from the stored probe traces; retain the 29-case cap diagnostic and avoid
repeating unconditional probe-budget escalation.

## Checked common consequences and their downstream cost (9 November)

`cnf_common_consequence.py` implements the standard necessary-assignment rule.
It preserves all failed-literal attempts, then applies all common literals from
the first complete inconclusive pair with a nonempty intersection. Both unit
traces, pair selection, retained closure, exact target and model transport are
checked. Support strictly decreases. Earlier recognition/component/reduction
priorities and old-policy archives remain valid. Small hooks in the previous
inventory share checking/lifting without changing its record format or policy.

The [1,101-input comparison](../experiments/results/cnf-common-consequence/README.md)
preserves all 1,025 old inputs and adds 64 fresh random formulas (through 48
variables) and 12 growing/signed/edit controls. Coverage rises 536/589 -> 537/589
non-tiny cases, solely old case 968; no baseline closure is lost, and fresh
coverage remains 40/64. Total time rises 32.12172 -> 32.75928 s, SQLite
104,435,712 -> 107,757,568 bytes and cold audit 12.03279 -> 12.56291 s. The
post-selected 29-miss pilot also gains one closure at higher cost and is retained.
This policy stays optional; there is no measured general speedup.

There are 477 common rewrites assigning 663 literals. All 355 common nodes with
a matching baseline CNF/depth retain identical probe lists. Despite fewer
arbitrary candidates (2,036 -> 1,957) and selected unresolved literals
(9,728 -> 8,101), total probes rise 29,280 -> 31,745 and logical node bytes
38,929,223 -> 40,749,002. New residuals cause repeated acquisition. Witness and
closure JSON is only 34,415 bytes, while probe-node payload grows by 2,410,587.
The targeted six-case peak and warm replay also slightly regress. All modes
retain 7,393 ordinary solver residuals; the decision solver is unchanged.

Fifty-two non-tiny cases remain open. A fresh 48-variable miss is now the largest
discovery cost; profiling still points to restriction, unit checks/propagation,
normalization and literal helpers. Saved paired implications contain a more
structural next opportunity: signed variable equivalences not already expressed
by a direct binary pair. There are 269 such archived unresolved nodes, but only
16 on selected paths, affecting 16/52 missed sources and 799/8,101 selected
unresolved literals. Implement and check full-CNF substitution and signed model
transport on those selected residuals first. Measure whether a recognizable
family/component emerges before applying the rewrite to all alternatives.
These counts imply neither new coverage nor a resolution of the larger misses.

All 326 Python tests pass (27.50 s), including exhaustive fibers, multiple
common literals, saved-trace reuse, mixtures/edits, invalid/omitted witnesses,
transport and cold corruption. Three new and four preceding complete archives
replay byte-identically. Two new Lean lemmas prove the common-consequence rule
and exact SAT restriction from explicit implication hypotheses. The full build
and axiom audit pass at 4,091 declarations / 1,950 theorem declarations; Python,
SQLite and resource bounds remain outside the refinement.

Implementation/evidence checkpoint `79e1404` is pushed. Manuscript Section 12.51
adds the common-consequence proposition and proof, the verified necessary-
assignment citation, measured cost regression and selected-path limits on the
next equivalence opportunity. All 50 earlier proof blocks remain intact (51
total; 177 unique labels). The 99-page PDF builds without warnings or box errors;
pages 90--92 and bibliography page 96 were visually inspected. Resume with the
16 selected unresolved equivalence candidates, preserving this optional policy
and its negative cost evidence rather than enabling it unconditionally.

## Checked signed equivalence and its acquisition cost (9 November)

`cnf_probe_equivalence.py` implements exact full-CNF substitution using the first
eligible opposite-consequence probe pair. It preserves failed-literal/common
priority and all attempted probes. One star-shaped block receives the smallest
variable as representative, with explicit signs. The checker validates source
reasons, first-pair selection, complete map, strict support decrease and exact
child binding. Model lifting composes compact names and signed representatives,
including representatives that vanish after tautology removal, then checks the
full parent. Old policies/archives coexist unchanged. Recognition overlaps and
all remaining interactions are retained; this is not a new universal SAT class.

The [selected pilot](../experiments/results/cnf-probe-equivalence-pilot/README.md)
closes seven of sixteen old source misses. Total time slightly falls 4.92437 ->
4.86584 s, SQLite 16,863,232 -> 16,326,656 bytes and nodes 1,698 -> 1,585.
The [full comparison](../experiments/results/cnf-probe-equivalence/README.md)
retains all 1,101 previous sources and adds 24 fresh random 3-CNFs through 48
variables plus twelve growing, signed and edited controls. Non-tiny closure rises
567/625 -> 574/625; the same seven old cases gain and none lose on this corpus.
Three gains are variants of one source. Fresh random closure remains 18/24.
Fifty-one source misses remain. The independent decision solver is unchanged.

The full cost conclusion reverses the pilot: total time rises 38.29300 ->
39.73059 s, discovery 27.77853 -> 29.08758 s, SQLite 130,596,864 -> 135,569,408
bytes and cold audit 15.20846 -> 15.85644 s. Warm replay rises 0.14485 -> 0.29462
s. Keep this policy optional. These are single sequential synthetic measurements;
no significance or industrial-performance claim follows.

There are 624 equivalence rewrites merging 1,145 variables across acquired nodes.
All 431 shared exact parent CNF/depth pairs retain identical probe lists. Yet
attempts rise 37,049 -> 41,039 and pattern nodes 9,584 -> 9,952. Conditioning
candidates fall 2,232 -> 2,063 and selected unresolved literals 10,300 -> 9,674.
Logical bytes rise 50,062,370 -> 52,575,330; probe nodes alone occupy 32,136,270.
The signed witnesses use only 25,670 JSON bytes. Full keys/profiles, the added
policy identity and changed descendants remain charged. The six-case traced
Python peak falls 14,564,269 -> 11,586,228 bytes, but excludes native SQLite,
RSS and full-corpus peak. Reduced support, targeted live memory and total durable
storage must not be conflated. The 261 immediately unresolved equivalence children
also show that merging known relations need not expose a recognized family.

Next investigate **bounded local learning from saved one-way implications**.
Seventy of 77 selected unresolved nodes have 552 implied binary clauses absent
explicitly in their parent (node/clause pairs). Binary-graph analysis shows 333
already have implication paths; **219 lack such a path**, on **47 selected nodes
affecting 37 missed sources**. `implication-boundaries.json` preserves exact
assumption/reason dependencies and affected source IDs. No-path evidence is not
semantic nonredundancy; other reasoning may entail the clause. Case 1061 remains
the largest discovery cost (0.96542 s, separately instrumented 2.96676 s), with
restriction, unit checking/propagation, normalization and helpers dominant.
Start bounded learning on these selected misses, charge redundancy recognition,
extra propagation/clauses, checking and archive growth, and measure before enabling
it globally. Supporting scan/sharing optimizations remain relevant. None of these
opportunities establishes compact exact coverage of arbitrary SAT.

All 333 Python tests pass (27.90 s), including exhaustive small fibers, signed
and transitive blocks, disappeared representatives, mixtures, source edits,
invalid/omitted witnesses, lifts and cold corruption. Three new full archives,
three pilot archives and three preceding full archives replay byte-identically;
all 28 code/test fingerprints in each new benchmark report still match. Three
named Lean lemmas prove substitution evaluation, the opposite-assumption rule
and SAT preservation from explicit compatibility hypotheses. The full build and
axiom audit pass at 4,101 declarations / 1,957 theorem declarations (including
generated declarations). Python, SQLite and resource accounting are not refined
by those semantic lemmas.

Implementation/evidence checkpoint **4373610** is pushed. Manuscript Section 12.52
adds Proposition 12.40 with proof, the checked signed lift, verified prior-work
references, measured gains/regressions and the remaining implication opportunity.
All 51 earlier proof blocks remain intact (52 total; 179 unique labels). The
100-page PDF builds with no final-pass warnings or box errors; pages 92--94 and
bibliography pages 98--99 were visually inspected. Resume from the bounded-learning
target above, preserving the full-corpus regression and the remaining 51 misses.

## Bounded local learning and gain attribution (9 November)

`cnf_probe_learning.py` adds one bounded continuation round after the previous
probe rules are inconclusive. Saved original-source implications license at most
four binary clauses; duplicates and binary-path consequences are skipped, including
paths through earlier accepted batch clauses. The checker verifies original
reasons before trusting additions, preventing circular justification. A second
bounded probe pass receives the augmented source. Only strict support reduction
can acquire a child; a failed round remains in the profile and continues ordinary
planning on the original CNF. Exact children and forced/signed lifts are checked.
Old recognition overlaps, priorities and archives remain intact.

The [37-source pilot](../experiments/results/cnf-probe-learning-pilot/README.md)
closes only old source 1057, with time 16.98242 -> 19.27531 s and SQLite
53,002,240 -> 56,647,680 bytes. The
[full study](../experiments/results/cnf-probe-learning/README.md) retains all
1,137 previous inputs and adds 24 fresh random 3-CNFs through 48 variables plus
twelve growing, signed and edited controls. Non-tiny structural closure rises
604/661 -> 607/661, with no lost baseline closure on this corpus. Gains are
956 (old, 20 variables, SAT), 1057 (old, 48 variables, UNSAT) and 1155 (fresh,
48 variables, UNSAT). Fresh closure rises 18/24 -> 19/24. Fifty-four cases remain
structurally unresolved: 49 old and five fresh. The independent source solver
still decides all inputs and retains the same 9,760 residuals in all modes.

The policy stays optional. Total time rises 48.17697 -> 52.69690 s, discovery
35.64804 -> 39.96872 s, SQLite 163,532,800 -> 168,267,776 bytes and full cold
checking 20.78528 -> 22.01280 s. The six-case traced Python peak rises
18,466,093 -> 20,377,761 bytes; native memory, RSS and full-corpus peak are not
measured. These are single sequential synthetic measurements. Learning adds a
second probe pass, so the modes do not have equal total probe budgets. All extra
work is charged; the targeted pilot's minor test overlap is disclosed separately.

There are 1,938 learning attempts and 4,909 proposed clauses. Of these attempts,
1,709 are inconclusive; 229 yield support reductions (150 forced, 53 equivalence,
26 common). Only seven immediately reach a recognized family, while 68 still
lead to an unresolved child. All 1,780 shared exact parent CNF/depth pairs retain
their original attempt lists. Total probes rise 47,286 -> 62,784. Pattern nodes
fall 11,410 -> 11,406, yet logical bytes rise 63,465,538 -> 66,573,092. Batch and
continuation JSON occupies 1,945,661 bytes. Selected unresolved literals fall
12,686 -> 11,106. Eighty selected distinct unresolved nodes remain, with 48
inconclusive learning rounds and 32 clear profiles. Neither fewer nodes nor
smaller remaining interactions guarantees lower acquisition cost.

`learning-mechanisms.json` preserves an attribution diagnostic: use the same
continuation variables on the source without additions. Forty-nine of 229
successful nodes still reduce (39 forced, five common, five equivalence). This
includes the selected learning nodes on both old gains. The selected node on
fresh gain 1155 stays inconclusive without additions. Stronger propagation and
changed choices both contribute; neither semantic necessity nor counterfactual
whole-source closure follows. Obtaining the changed choices is not free. The
old 77 selected leaves are also replayed: thirty have no batch, 41 remain
inconclusive, five force assignments and one yields equivalence. All traces,
including failures, are retained. The published constraint-resolvent example's
unmodified all-true recognition and its signed learning variant remain tests.

**Next target:** reuse the checked original closure when the added batch has
no unit or conflict under that closure and its assumption; otherwise resume
propagation or retain the full fallback. Of 15,052 continuation probes, 13,194
repeat an original assumption and **10,018 repeat the complete certificate**.
This is a concrete opportunity to reduce scans and share proof records without
dropping stronger propagation. Preserve source/batch identities, clause-index
transport and all fresh candidate probes. Measure exact plans/coverage, fibers,
checking, total cost and cold replay before enabling it. This supports further
discovery on the 48 selected leaves where learning remains inconclusive; no
runtime saving or new closure from reuse is yet measured. The largest discovery
case is now 1063 (1.20829 s, separately profiled 4.07290 s). Restriction scans,
unit checking/propagation and literal helpers dominate; probe nodes account for
41,131,705 / 66,573,092 logical node bytes. Do not raise the global probe cap yet.

All **341 Python tests** pass (28.55 s), including all 512 two-variable sources
and 3,304 subsets with at most three three-variable clauses at caps 0/1/4,
pointwise learned-source equivalence, reduced fibers, signed mixtures, corrupted
or circular proofs, invalid lifts, source edits, cold corruption and policy
coexistence. Three new full archives, three pilot archives and three preceding
full archives replay byte-identically. All 31 code/test fingerprints in each
new benchmark report match. Two new Lean lemmas prove assumption-to-clause
entailment and batch model preservation under explicit original-source hypotheses.
The full build/axiom audit passes at **4,103 declarations / 1,959 theorem
declarations**. Python, SQLite and resource bounds remain outside refinement.

Implementation/evidence checkpoint **eb412fe** is pushed. Manuscript Section 12.53
adds Proposition 12.41, its proof, the established local-learning citation,
coverage/cost results, the changed-choice diagnostic and the next closure-reuse
condition. All 52 earlier proof blocks remain intact (53 total; 181 unique labels).
The 102-page PDF builds with no final-pass warnings or box errors; pages 93--96
were visually inspected. Resume from checked continuation reuse, preserving the
full cost regression and all 54 structurally unresolved sources.

## 9 November: checked closure reuse and bounded-batch selection frontier

The preceding target is implemented and verified in checkpoint **f275a49**,
already pushed. `ProbeClosureReuseInventory` references an old same-assumption
unit proof only after checking its original reasons, complete fixed point and
learned batch, then testing every added clause. An active addition or fresh
assumption uses the full pass. Restriction preserves the old clause prefix and
reason indices; wrong-source, edited, circular or corrupt references are rejected.
The final child and model lift remain fully checked. The independent solver is
unchanged and no unsuccessful attempt is discarded.

The [matched study](../experiments/results/cnf-probe-closure-compact/README.md)
retains all 1,173 old sources and adds 36 controls/holdouts. All **1,209 source
plans** and **13,066 semantic nodes** match, including alternatives and selected
paths. Closure stays **634/697** non-tiny and **15/24** fresh random inputs.
All policies retain 10,856 ordinary solver residuals. The continuation has
17,548 probes: **14,705** reused closures, **672** active repeated assumptions,
**2,171** fresh assumptions. Original passes account for 55,553 logical probes.

The first namespace stores an extra field in every full key. It compresses
807,098 local proof bytes but increases SQLite from 197,103,616 to 200,323,072
bytes. This failed representation and its complete archives remain preserved.
`CompactProbeClosureInventory` replaces the local-learning version tag instead,
keeping a distinct namespace and identical profile proofs. Its sample changes
total time **62.75908 -> 61.68668 s**, discovery **48.01501 -> 46.53708 s**, SQLite
**197,103,616 -> 196,096,000 bytes**, cold replay **26.78483 -> 25.09448 s**, and
six-case traced Python peak **20,377,769 -> 20,021,725 bytes**. These are modest
single-sample effects; checkpoint staging/commit overlapped compact acquisition.
No tests/builds/profiles overlapped primary timing. The compact report explicitly
inherits the three frozen reference modes and newly measures only its own mode.

All **348 Python tests** pass (30.12 s), including exhaustive small fibers,
independent full replay of expanded references, active deltas, new assumptions,
corrupted original reasons, wrong references, signed edits, invalid lifts, cold
coexistence and byte-identical replay. An eight-variable seeded example was added
because the older learning fixtures did not exercise active repeated assumptions;
it now verifies that merely matching an assumption cannot license reuse.
Three first-study archives, three preceding archives and the compact archive
all replay byte-identically. Fingerprints and inherited archive hashes are checked.

Lean formalizes signed unit reasons/derivations and the syntactic fixed-point
criterion. It proves append-only preservation of the whole old derivation and
that the added-clause check is necessary and sufficient once the original closure
is checked. `checked_unit_closure_append` combines these. Full build and axiom
audit pass at **4,121 declarations / 1,964 theorem declarations**. These lemmas
do not refine Python, clause-index serialization, SQLite or complexity bounds.

The manuscript adds Section **12.54**, Proposition **12.42**, its proof and
Table **15**, including both storage outcomes and the exact cost restrictions.
All 53 preceding proof blocks remain intact (54 total; 184 unique labels).
The 104-page PDF builds without final-pass warnings or box errors; changed
pages and the transition into discussion are visually checked.

**Next discovery experiment:** choose a better four-clause batch from already
proved implications, preserving current clause and probe caps. The selected
remainder contains 94 unresolved nodes, sixty learning-clear and 34 clear.
Twenty batches reach cap four; enumeration up to sixteen exposes **61 further
eligible clauses on sixteen leaves affecting thirteen source misses**. Thirty-eight
existing batches draw their clauses from one assumption. The complete
[frontier record](../experiments/results/cnf-probe-closure-compact/learning-frontier.json)
retains every candidate, dependency and no-opportunity leaf. It costs 1,805
candidate visits, 14,871 source literal visits, 6,203 graph vertices and 5,971
graph edges; its separately timed generation is 0.00378 s excluding archive
load/traversal. One leaf reaches the diagnostic cap; this is not exhaustive.

Rank candidates by activation of checked closures and diversity of assumptions,
charge selection, and use a fixed-choice control to distinguish stronger
propagation from altered continuation ranking. Start with the thirteen affected
sources then run all old and fresh unlabelled inputs. No alternate batch was
executed here; these are opportunities, not new closures. Source **1194** remains
the largest discovery cost, dominated by restriction and unit checking/propagation.
Sixty-three source cases remain structurally unresolved. Keep exact classification
and efficient arbitrary-SAT construction/compactness as separate obligations.

## 9 November: bounded clause selection exposes a continuation-order gap

Implementation/evidence checkpoint **69d7780** is pushed. The optional
`SelectedLearningInventory` chooses at most four clauses from sixteen eligible
original-source implications, preferring activation of uncovered saved closures,
origin diversity, total activation and pool order. Its distinct policy namespace
coexists with every old archive. The checker validates original traces first,
reconstructs the selection, then checks references, continuation, strict support
decrease, child and lift. Original defaults and the independent decision solver
are unchanged. The candidate filter can use earlier pool clauses later omitted;
this preserves entailment but can exclude useful alternatives.

The [thirteen-source pilot](../experiments/results/cnf-learning-selection-pilot/README.md)
gains source 1024, with slightly higher total cost. The
[full comparison](../experiments/results/cnf-learning-selection/README.md)
retains all 1,209 prior inputs and adds 24 random 3-CNFs at 20/32/48 variables and
twelve growing, signed and edited controls. It gains **1024**, a satisfiable
guarded source, but loses **956**, a satisfiable random 20-variable source. Thus
closure stays **662/733** non-tiny and **16/24** fresh random inputs, with **71
source misses**. All new controls close under either policy; the unchanged solver
decides every original source and keeps 12,516 residuals. A structural miss does
not change a SAT answer. Preserve this negative aggregate result.

Total time rises **71.41739 -> 73.19404 s (+2.49%)**, discovery **53.49192 ->
54.70319 s**, SQLite **227,385,344 -> 227,831,808 bytes**, cold replay **29.81471 ->
30.35939 s** and the same six-case Python peak **20,021,677 -> 20,121,481 bytes**.
Peak excludes native SQLite, RSS and full-corpus peak. All timing samples are
single sequential runs; primary modes, memory diagnostics and separate profiles
ran without concurrent tests, builds or commits. Nodes rise **14,592 -> 14,653**,
logical node bytes **89,963,443 -> 90,219,745** and logical probes **82,036 ->
82,782**. Fewer conditioning candidates (2,850 -> 2,835) and selected unresolved
literals (17,687 -> 17,327) do not establish lower total cost or greater coverage.
The largest discovery case remains 1194 (1.46397 s); restriction and unit
checking/propagation dominate its separate profile. Keep selection optional.

`mechanisms.json` retains every changed parent and four checked local controls
crossing old/new batches with old/new continuation choices. There are 606 changed
nodes, including 126 reorder-only cases and 562 exact common parents with identical
original proofs. `selection-paths.json` preserves explicit normalized CNFs,
clauses, choices, first conflicts and dependencies for the gained/lost sources.
At 1024, identical choices and equal scalar activation counts still allow only
the selected batch to refute `3=false`. At 956, no original closure activates;
all four controls force a variable, but old choices first refute `14=true` and
new choices `16=false`, under either batch. The actual selected source plan then
remains unresolved. This identifies an effect hidden by local reduction counts.
Replaying all 94 prior selected leaves also improves one local common reduction
on 1189 without closing that source. These are local controls, not counterfactual
whole-source coverage. Failed batches and regressions remain available.

**Next experiment:** hold continuation variable list/order fixed to the ranking
computed from the old first-four batch while applying the selected batch. Charge
old-batch/ranking construction and keep clause/probe caps. Start with 956, 1024
and 1189, then all old and fresh inputs. No whole-source benefit is yet measured;
fixed choices do not guarantee preservation of coverage. Track learned-clause
interactions, first conflict and resulting child structure; activation/diversity
scores alone cannot distinguish the observed outcomes. Do not repeat the same
greedy trial or globally raise caps as a substitute for this control.

All **353 Python tests** pass (32.08 s): exhaustive 512 two-variable inputs and
3,304 three-variable subsets of at most three clauses at learning caps 0/1/4,
exact model fibers, independently expanded proof references, masks against the
delta predicate, signed mixtures/edits, invalid selections/reasons, disabled mode,
cold corruption and policy coexistence. Three full, three pilot and four preceding
archives replay byte-identically; warm reuse inserts nothing. Both reports' forty
code/test fingerprints match. `selected_signed_batch_models` adds the semantic
subset corollary without a ranking hypothesis. The full Lean build and axiom
audit pass at **4,122 declarations / 1,965 theorem declarations**. No Python,
SQLite or resource refinement, compact arbitrary-SAT representation, or uniform
polynomial construction follows.

Manuscript Section **12.55** and Table **16** record the rule, subset argument,
costs, gain/loss, four-way controls and next experiment. All **54 earlier proof
blocks** remain intact, with **186 unique labels**. The **106-page** PDF builds
without final-pass warnings or box errors; pages 96--100, including the changed
section, table and discussion transition, were visually inspected. The discovery plan, ranked priorities,
resource bounds and project/formal READMEs record this completed experiment and
the controlled next target.

## 9 November: fixed continuation choices and a shared-core counterexample

Implementation/evidence checkpoint **bdc6dc7** is pushed. The optional
`FixedOrderLearningInventory` reconstructs the old first-four batch and its
binary-frequency ranking at each exact parent, then propagates the selected
batch under that variable list/order. Both reconstruction and checking are
charged. The checker validates original proofs before reconstructing choices;
no persisted ranking hint is trusted. The original phase, earlier recognition
and decomposition priorities, local caps, strict support decrease and exact
child/model-lift obligations remain unchanged. A separate policy tag preserves
all old archives. The independent decision solver is unchanged.

The [three-source pilot](../experiments/results/cnf-learning-fixed-order-pilot/README.md)
tests 956/1024/1189. Fixed order keeps the earlier gain 1024 but neither recovers
956 nor closes 1189. The [full comparison](../experiments/results/cnf-learning-fixed-order/README.md)
retains all 1,245 previous inputs and adds 24 random 3-CNFs at 20/32/48 variables
plus twelve growing/signed/edited controls. All three policies close **692/769**
non-tiny and **18/24** fresh random inputs. Both selected modes gain 1024 and lose
956 against baseline, with no closure changes between selection and fixed order.
**77 sources** remain structurally unresolved; all original decisions agree and
the ordinary solver retains **13,641 residuals** per mode.

Baseline/selection/fixed total time is **77.91555 / 82.42121 / 80.71966 s**, SQLite
**252,243,968 / 252,497,920 / 252,391,424 bytes**, cold replay **33.50593 / 33.58541 /
34.30859 s**, and same-six-case Python peak **20,021,661 / 20,121,465 / 20,127,074
bytes**. Fixed order is 3.60% slower than baseline. Its 2.06% lower sample time
than selection is not a general speed claim. Peak excludes native SQLite/RSS
and the full corpus. Primary modes, memory diagnostics and separate profiling
ran sequentially without concurrent tests, Lean builds or commits.

Nodes are **16,052 / 16,106 / 16,126**, logical probes **89,782 / 90,513 / 90,713**,
and logical node bytes **100,112,588 / 100,290,071 / 100,315,272**. Physical storage
and logical payload move differently; the shorter fixed-policy tag also changes
keys/source records. Fixed order incurs **6,418 reconstructions**, **25,662 ranked
candidate positions**, and 254,742 learned candidate visits versus selection's
152,026. Selected unresolved literals fall 18,362 -> 17,971 versus baseline
without greater coverage. The frontier retains 111 distinct leaves, 71
learning-clear and forty clear. Source **1194** remains the largest discovery
case at 1.41725 s; its separate 4.58346 s profile again identifies restriction,
unit checking/propagation and literal helpers.

The preserved `mechanisms.json` contains all three selected source paths, every
current unresolved leaf and controlled parent/child acquisitions. On 956's saved
18-variable parent, baseline and fixed order both first refute `14=true`, fix
only `14=false`, and leave **the identical 54-clause original restriction**.
Baseline retains three extra clauses `[1,17]`, `[9,13]`, `[16,17]`; its 17-variable,
57-clause child closes. Fixed retains four `[-18,16]`, `[9,13]`, `[13,18]`, `[16,17]`;
its 17-variable, 58-clause child stays open with eighteen unresolved literals.
All additions are originally entailed, so the two restricted model relations
agree. Immediate order was only part of the earlier loss; representation changes
still affect descendant discovery. At 1024, both selected policies force `3=true`
and close the 27-variable child. Do not promote fixed order as a coverage fix.

**Next experiment:** separate the restricted original core from checked learned
hints. Use the core for structural identity/recognition and retain scoped hints
for propagation. Test 956/1024/1189 and the saved frontier before old/fresh full
inputs. Charge core reconstruction, hint checks, transport, canonicalization,
serialization and cold replay. Keep hint/policy context on discovery plans even
when core decisions/certificates share storage. Edits, changed assignments and
dependencies require revalidation. Removing useful hints can lose coverage; no
improvement from this next representation is measured yet. The rule uses known
entailment and shared provenance, not unrestricted semantic equivalence testing.

All **358 Python tests** pass (30.30 s), including all 512 two-variable inputs and
3,304 three-variable subsets of at most three clauses at caps 0/1/4, exact fibers,
independently expanded references, a seeded changed-order fixture, signed
mixtures/edits, wrong orders, corrupt reasons, omitted/forged batches, disabled
mode and cold coexistence. Four full, four pilot and three preceding archives
replay byte-identically; warm reuse inserts nothing. Both reports' **43 code/test
fingerprints** match. The unchanged Lean build/axiom audit passes at **4,122
declarations / 1,965 theorem declarations**. Existing semantic lemmas justify the
choice-independent reductions; no new Python or complexity refinement is claimed.

Manuscript Section **12.56** and Table **17** record the policy, bounds, complete
negative coverage result and the same-core counterexample. Applying the existing
batch equivalence to valuations extending a partial assignment proves the stated
restricted-model equality. All **54 earlier proof blocks** remain unchanged, with
**188 unique labels**. The **107-page** PDF builds without final-pass warnings or
box errors; changed pages 99--102, including the table, equality and discussion
transition, were visually inspected. Project/formal READMEs, resource bounds, discovery plan and ranked
priorities now point to the shared-core/hint experiment.

## 9 November 2026: checked parent hints with original-clause child cores

Implemented the next representation experiment in `CoreLearningInventory`.
It fully checks the fixed-order learned continuation, retains its hints/proofs
at the parent, and builds a successful child only from the restricted or
substituted original parent clauses. Checked terminal conflicts remain false.
Children receive no inherited hint context and discover their own hints. Equal
normalized cores at equal depth/policy can therefore share plans safely; source
edits, changed reductions and proof dependencies still need full validation.
Earlier priorities, overlaps, exact decomposition and per-node caps are unchanged.
This optional inventory does not alter the complete decision solver.

The [pilot](../experiments/results/cnf-learning-core-pilot/README.md) recovers 956
and retains 1024, leaving 1189 open. Its lower time/storage are selected-case
results. The [full comparison](../experiments/results/cnf-learning-core/README.md)
preserves all 1,281 preceding inputs, adds 24 fresh random 3-CNFs and twelve
growing/signed/edited controls, and closes **719/805** non-tiny inputs versus
**718/805** under baseline/fixed order. There are no lost closures against either.
All close 14/24 fresh random sources; **86** core sources remain structurally
unresolved. All original SAT/UNSAT decisions agree, and the independent solver
retains **15,069 residuals** per mode.

Baseline/fixed/core total time is **94.86962 / 97.40244 / 97.83486 s**, discovery
**70.87369 / 72.76849 / 73.16855 s**, SQLite **284,110,848 / 284,299,264 /
284,094,464 bytes**, cold replay **40.28060 / 41.15963 / 40.38357 s**, and same-six
case Python peak **20,021,661 / 20,127,082 / 20,265,076 bytes**. Core is 3.13%
slower than baseline; the pilot savings do not generalize. These are single
sequential samples. Peak excludes native SQLite, RSS and the full corpus.
Timings, allocation diagnostics, prior archive audits and separate profiling ran
without concurrent tests, Lean builds or commits. Warm/cold replay are separate;
operation time excludes generation, truth tables, summary walks, initialization,
compression and post-run analysis, as specified in the retained report.

Core stores **17,833 nodes / 113,536,866 logical node bytes**, with **72,386,084
bytes (63.76%)** in probe nodes. Its 449 learned edges comprise 311 forced,
42 common and 96 signed-equivalence reductions; 385 change normalized child
syntax and none changes variable transport. There are 380 exact parent/depth
controls in fixed order with identical parent proof records. Reconstruction adds
expected O(L+q+v) time and O(L+v) temporary space after the augmented reduction
is already checked. Across 1,347 repeated reconstruction/checking calls, child
syntax omits 3,156 clause / 6,312 literal occurrences. Parent proofs remain stored.
These occurrence counts do not establish unique redundancy or bytes saved.

The saved 956 parent forces only `14=false` under all policies. Its original
54-clause restriction closes, while fixed order's 58-clause augmented child
stays open. A regression test obtains the same core from both independently
checked batches and confirms exact reuse. **No two learned parents share a child
core in the full run.** The coverage gain is therefore altered descendant
discovery, not evidence of broad within-run core merging or semantic canonicalization.

The [mechanism record](../experiments/results/cnf-learning-core/mechanisms.json)
preserves both parent controls, selected paths for 956/1024/1189 and actual gains,
all 124 selected unresolved leaves (86 learning-clear / 38 clear), every learned
core edge and a separate profile. Transporting proved clauses diagnostically
through exact assignments/substitutions and variable maps yields **992 eligible
hint occurrences**, 85 already in core and **907 absent**. Of these, **319 are
learned again in the immediate child's batch across 165 edges**, including 127
learning-clear and 38 learned children. None in this sample mentions variables
outside the core; that invalid transport possibility is recorded explicitly.
Counts are occurrences, not unique facts, avoided probes or saved seconds.

**Next experiment:** reuse checked hint evidence across these edges while keeping
structural recognition on the core. Preserve source entailment, exact reduction,
variable map and hint-dependent propagation context. Compare those 165 edges,
956/1024/1189, the frontier and full old/fresh inputs at unchanged caps, including
all checking/storage/replay costs and any losses. Cached implication proofs do
not automatically remove the original probes required by current ranking or
earlier reductions; skipping them needs a checked policy change. This inherited
hint policy is not yet implemented. The largest unresolved case is now fresh
48-variable source 1297 at **1.47150 s**, with 456 selected unresolved literals.
Its separate 3.36725 s profile is dominated by restriction, simplification checking,
propagation and literal helpers, and has only one successful learned parent.
Reusing checked propagation state remains the broader supporting cost target.

All **366 Python tests** pass (32.601 s). New tests include all 512 two-variable
CNFs and 3,304 three-variable subsets of at most three clauses at caps 0/1/4,
exact fibers and independently expanded references, forced/common/equivalence
fixtures, signed mixtures, edits, disabled mode, forged dependencies, wrong child
bindings, preserved learned conflicts and cold coexistence. A failed 25,000-input
random search for the conflict fixture is recorded; a constructive pair forcing
opposite shared outputs supplies the retained counterexample. Four full, four
pilot and four preceding archives cold-replay byte-identically; warm reuse inserts
nothing. Both reports' **47 code/test/Lean fingerprints** and all archive hashes match.

Lean adds `CompletePartial`, `entailed_signed_batch_partial_models` and
`entailed_signed_views_common_core`. Originally entailed batches preserve models
under any common partial assignment, including incompatible assignments with
no models. These semantic lemmas do not refine Python filtering, encoding, model
transport, SQLite or costs. The full build/axiom audit passes at **4,125 declarations
/ 1,967 theorem declarations**. Implementation, proofs and artifacts are pushed
in **599f921**. The manuscript records the method, complete tradeoff and next gap
in Section **12.57**, Table **18**. Prior proof blocks remain unchanged; efficient
arbitrary-SAT discovery, compact global closure and uniform acquisition bounds
remain open.


The rebuilt **109-page** PDF has no final-pass warnings or box errors. Changed
pages 100--103, including Table 18 and the discussion transition, were visually
inspected. All **54 prior proof blocks** remain unchanged and **190 labels** are
unique. Project/formal READMEs, resource bounds, discovery and ranked priorities
record both the modest coverage gain and the full-run time/memory regressions.

## 9 November 2026: portable core proofs, extra-pass regression, ranking control

Implemented `cnf_hint_transport.py`: map a checked parent's original implication
reason prefix through its exact forced/common assignment or signed equivalence
and normalized child transport. Parent probe reasons index the restricted parent,
so the translator reconstructs original clause indices before mapping to child
indices. Satisfied/tautological reasons disappear; missing refutations remain
explicit misses rather than invoking hidden fresh search. An independent RUP
checker accepts only a unit-conflict derivation against the exact child core.
The resulting record is portable without the parent graph, with complete
core/clause identity and independently checked reasons. Parent evidence and
earlier archives remain preserved.

`HintAssistedInventory.inspect_hints` supplies an explicit, context-keyed local
control. Recognition and earlier priorities stay on the core. Eligible children
receive one extra bounded pass using proved hints and core-ranked choices;
successful rewrites construct original-clause cores with exact lifting, and
inconclusive passes fall back to the unchanged ordinary planner. All hints and
their order, depth and policy are part of the persistent plan identity. Ordinary
descendants do not inherit hints implicitly. This is an optional local control,
not a replacement of the original whole-source planner at the same total budget.

The [preserved study](../experiments/results/cnf-hint-transport/README.md) covers
all **449** previous learned-parent edges and **45** distinct new parents from
36 fresh sources at seed **20261109064108**. The ordinary planner closes 30/36
fresh originals; their full graphs, answers and solver certificates are archived.
All **1,005** eligible hint occurrences (907 prior, 98 new) translate without
fresh search, into **984** distinct core-clause records. Omissions are 448 satisfied,
64 tautological, 99 explicit and four duplicate occurrences; no outside-variable
or failed-prefix miss occurs in this sample. Universal transport completeness
and Python refinement are not established.

The mapped-prefix walk visits **11,510 reason literals**, versus **287,160** for
fresh scan-based proof search given the same candidates. This is not an overall
speed ratio: transport preparation **0.95129 s** includes full parent checking,
core projection, normalization, index mapping and proof checks; fresh proof
search/checking/persistence costs **0.93100 s** conditional on supplied candidates.
The separately recorded fresh-source acquisition/solving costs **8.87824 s**.

Local baseline/hint closure is **223/494 -> 224/494**, with no losses. Prior-edge
closure is 198/449 -> 199/449; fresh-edge closure stays 25/45. The independent
solver verifies every child core, agrees in both modes and retains **6,051
residuals**. Operation time is **14.41354 / 16.82765 s** before hint preparation
(+16.75%, or +23.35% including preparation), discovery **6.06309 / 7.87721 s**,
SQLite **55,119,872 / 63,885,312 bytes**, cold replay **4.70738 / 7.72522 s**, warm
lookup **0.06691 / 1.31088 s**, and matched-six-core Python peak **7,372,293 /
7,430,827 bytes**. Peak excludes preparation, native SQLite, RSS and full corpus.
Hint cold time includes ordinary graph/solver and separate fresh hint-plan audits;
their repeated checking remains charged. Primary runs, memory diagnostics, builds,
tests and later controls ran sequentially without overlaps affecting primary timing.

Ordinary nodes fall **2,167 -> 1,999**, payload **11,157,841 -> 9,943,442 bytes**,
but portable hint records add **2,181,006 bytes** and 494 context plans add
**3,096,507 bytes**. Probes rise **14,468 -> 16,136**; selected unresolved literal
occurrences fall **57,827 -> 57,595**. The overlay is clear on 180 cases, skipped
on 83, forced on 169, common on 27 and equivalence-reducing on 35. Reductions do
not by themselves count as new closures. The extra-pass policy remains optional.

The local gain is **case 97**, a 25-variable, 81-clause core at depth zero, reached
through a common reduction in an **unselected alternative of original source 977**.
It is absent from every saved selected whole-source path. The source's selected
plan remains open with two leaves and 138 literals; the local baseline has one
open leaf with 223 literals. Do not increment the preceding **719/805** source
coverage using this local result.

The [mechanism record](../experiments/results/cnf-hint-transport/mechanisms.json)
crosses transported/rediscovered batches with core/baseline-continuation choices.
Both batches close using `(4,5,7,19)`, refuting `19=true` and forcing
`19=false,13=false`; both stay clear/open using `(4,5,7,11)`. This isolates the
variable-choice policy as sufficient to explain the gain. Stronger inherited
clauses are unnecessary for this control. A further diagnostic records **1,456
inactive / 102 active deltas** across original probe closures on **196 cores**.
Original proofs must be checked first; this is an opportunity count, not executed
reuse or avoided probes.

**Next experiment:** core-ranked continuation choices with the existing learned
batch, existing pass count and local caps. Derive choices from the checked original
traces or exact core, test 97/977 and 956/1024/1189 first, then complete old/fresh
source workloads. Record any losses and avoid rebuilding an old augmented batch
solely to rank. Portable hints can later enter a separately checked existing-pass
policy; do not assume an additional pass is efficient. Recognition, coverage,
total cost and full-source effects remain separate metrics.

All **374 Python tests** pass (32.796 s). Eight new tests cover exhaustive small
RUP soundness, forced/common/equivalence translations, signed renamings and edits,
wrong parent dependencies, corrupted core reasons, exact-source bindings,
empty/nonentailed clauses, model fibers, explicit contexts, wrong children and
cold replay without parent access. A first negative test mistakenly expected a
valid proof to fail after removing an unused clause; it was corrected to test
the store's exact-source binding separately from proof validity. The full Lean
build/axiom audit passes at **4,126 declarations / 1,968 theorem declarations**.
New `Fragments.core_fragment_sound` derives exact-core entailment from the existing
fragment checker and core-premise membership. It does not verify Python translation
or persistence. The manuscript attributes the underlying proof method to existing
hinted clausal checking rather than claiming novelty.

Four new archives replay byte-identically; warm reuse inserts nothing. All **51
code/test/Lean fingerprints**, four archive hashes and analyzer hashes match.
Implementation, proof and experiment checkpoint **a0f57c9** is pushed. Manuscript
Section **12.58**, Table **19**, and the discovery/resource/priority records retain
the successful portability result, unfavorable costs and ranking-dependent gain.
Efficient arbitrary-SAT classification, compact closure and global acquisition
bounds remain open.

The **111-page** PDF builds without final-pass warnings or box errors. Changed
pages 102--105, including Table 19 and the discussion transition, were visually
inspected. All **54 previous proof blocks** remain unchanged and **192 labels**
are unique. Object/database initialization was outside local operation timings
and not separately timed; this limitation is retained with the measured costs.


## 9 November 2026, 07:38 UTC heartbeat: core-order counterexample and next selection gap

Implemented optional `CoreOrderLearningInventory` in
[cnf_learning_core_order.py](../experiments/cnf_learning_core_order.py). It retains
the selected batch, existing two probe phases, exact core child and earlier
priorities. The continuation extracts choices from the complete original clear
trace only after original discovery or full independent checking. Extraction is
O(p), with O(p) temporary references; original ranking and all source/reason checks
remain charged. Separate policy identity preserves prior nodes and results.

Six new tests cover 512 exhaustive two-variable inputs and 3,304 three-variable
subsets with up to three clauses across multiple caps, exact model fibers,
forced/common/equivalence lifts, the saved local case 97, malformed original
traces/order/batches/continuations, signed mixtures and edits, disabled learning,
wrong-child rejection and byte-identical cold coexistence. All **380 tests** pass
in **33.602 s**. The unchanged full Lean build/axiom audit passes at **4,126
declarations / 1,968 theorem declarations**. There is no new Python refinement or
unrestricted acquisition bound.

The four-source pilot retains 956/977/1024/1189. The full
[matched study](../experiments/results/cnf-core-order/README.md) keeps all 1,317
previous inputs, all 36 original source queries from the hint study, and adds
36 controls at seed **20261109073810**: 24 fresh random 3-CNFs and twelve growing,
signed or edited queries, including repeats. Routing sees only CNF input. All
512 exhaustive tiny cases close. Non-tiny coverage falls **776 -> 775 / 877**,
with **no gains and only source 956 lost**. Old-input coverage is 719 -> 718 / 805;
both modes close 30/36 hint-study queries and 27/36 new queries. The unchanged
independent solver agrees on every answer and retains 18,104 residuals per mode.

Baseline/new operation times are **120.81853 / 116.67493 s**, discovery
**88.69202 / 85.68326 s**, SQLite **347,566,080 / 346,976,256 bytes**, cold replay
**50.51029 / 47.82982 s**, warm lookup **0.25672 / 0.22710 s**, and six-case Python
peak **20,265,108 / 19,623,309 bytes**. Initialization is separately measured at
0.06160 / 0.22272 s. Main timings include recognition, discovery, checking,
serialization, persistence, solving and successful root lifts, excluding generation,
truth tables, summary walks, compression, allocation diagnostics and cold replay.
Memory excludes native SQLite, RSS and full-corpus peak. Modes, memory diagnostics,
profiles, tests and builds run sequentially. The unchanged solver varies by 1.13 s
between combined modes, so the 3.43% total-time drop is not wholly a ranking saving
or a statistical result. Keep the policy optional with its coverage regression.

Pattern nodes fall **21,122 -> 21,005**, logical node bytes **137,740,084 ->
137,076,682**, and the same 1,365 source records occupy **5,225,670 -> 5,250,240
bytes**. Probe attempts fall 119,412 -> 118,152. Reused continuation probes rise
24,672 -> 27,611; active original probes rise 1,492 -> 1,700; newly chosen probes
fall 3,527 -> zero. The old 8,772 auxiliary ranking reconstructions disappear;
new extraction calls number 8,106 and copy 32,326 candidate entries. These are
counts over different residual populations and repeated checks. Selected unresolved
literal occurrences increase **26,137 -> 26,734**.

The loss has a concrete cause. At the common 18-variable, 62-clause depth-one
parent of source 956, both policies select exactly the same batch. Old choices
`(17,9,14,16)` refute `14=true`. New choices `(9,17,18,2)` are all inactive under
the batch, and stay clear. The new source path has one unresolved leaf containing
sixteen literals. The preceding local case 97 still closes with the same batch,
forcing `19=false,13=false`, but it remains outside the selected source-977 path.
Do not count it as an original-source gain. This new 956 ranking loss is separate
from the older redundant-child representation loss.

The [mechanism ledger](../experiments/results/cnf-core-order/mechanisms.json)
retains source paths, all changed shared CNF/depth states, both probe records,
old/core choices, validated batch activity, novel variables, the frontier and a
separate profile. There are **239 learned -> clear** and **16 clear -> learned**
shared-state transitions. In 189 of the local losses, no original core pair is
active. Every one of these 255 gained/lost local states has at most four variables
in the union of active core candidates and novel old-ranking candidates. Loss
union sizes are `{1:166,2:51,3:17,4:5}`; gain sizes are `{2:7,3:6,4:3}`. All 3,001
changed shared states retain identical learned batches; across that larger set,
seven unions already have five candidates. This is not a uniform width bound.

**Next discovery experiment:** use the checked original traces and batch-activity
masks to select active core plus novel candidates within the existing continuation
budget. Inactive unchanged paired closures cannot acquire new forced/common/
equivalence outcomes in the current procedure; retain their valid references.
Test all 255 local transition controls, then original 956 and local 97/original
977, before full source workloads. The union may exceed the cap, and differing
first conflicts or descendants can still change coverage. No combined rule or
recovered closure is implemented in this checkpoint. Supporting exact reuse can
share the deterministic sixteen-clause pool: for caps at most sixteen, its prefix
is the old first-cap batch. This could avoid reconstruction while preserving old
choices, but has not been measured.

The new frontier has **102 unresolved sources / 142 distinct selected leaves**,
99 learning-clear and 43 clear. Source **1194** costs **1.45407 s** discovery with
426 unresolved literal occurrences. Its separate profile records 5,307 restrictions,
4,311 unit-simplification checks and 2,069 propagations; those remain primary
costs. Probe-kind nodes hold 87,079,296 logical bytes, including CNFs, identities,
edges and other fields. Probing fields alone total 15,272,772 bytes. Do not confuse
whole-node storage with certificate payload.

Three full, three pilot and four prior archives replay byte-identically; warm
reuse inserts no records. Both new reports have **50 matching code/test/Lean
fingerprints**. Archive, analyzer and input-report hashes match. Implementation,
tests, measurements and counterexamples are committed and pushed as **544054d**.
Existing policies, previous solver results, proofs and archives are preserved.

Manuscript Section **12.59**, Table **20**, and the README/discovery/resource/
priority records now retain the cost/coverage trade-off and the proposed combined
selection. The **112-page PDF** builds with no final-pass warnings or box errors;
pages **104--106** were visually inspected. All **54 prior proof blocks** remain
unchanged, and **194 labels** are unique. One initial build placed outputs in the
repository root; its six generated files were removed and the final build used
the paper directory. Efficient arbitrary-CNF discovery, total closure size and
lifetime acquisition/storage bounds remain open.


## 9 November 2026, 08:39 UTC heartbeat: preserve local progress and expose signed cores

Implemented optional `ActivityLearningInventory` in
[cnf_learning_activity.py](../experiments/cnf_learning_activity.py). After complete
original probing or full independent replay, it checks both original closures
against the selected learned batch. It keeps old-ranked candidates unless both
closures are inactive, then fills freed positions with active core variables in
original order. Only additions may be truncated. The selected batch is shared
within one checked invocation; no persistent activity mask, unchecked candidate
list or cross-source cache is trusted. Original reasons, two phases, caps, earlier
priorities and exact original-core child binding remain intact. Empty continuations
are explicit checked clear results.

A fixed source/batch retains any old local reduction: omitted unchanged pairs
cannot supply a new forced/common/equivalence outcome; every informative old
candidate fits the cap and keeps its order. Added probes can cause earlier-priority
reductions, but still give local progress. This is not monotone whole-source
coverage, a Python refinement proof, or an unrestricted-SAT bound. Selection costs
expected O(U + p*q + p^2) beyond old-ranking reconstruction, with O(p + u_max)
temporary state beyond the existing traces/batch. All other acquisition, checking,
propagation, normalization and persistence remain charged.

Eight new tests cover exhaustive small model fibers, forced/common/equivalence
lifts, the local case 97, all **255** saved local transition controls, **seven**
overflow controls, empty continuations, malformed traces/orders/children, signed
edits, disabled learning and cold coexistence. All **388 tests pass in 39.515 s**.
The unchanged Lean build/axiom audit passes at **4,126 declarations / 1,968
theorem declarations**. Existing code, previous proofs and archives are preserved.

The [full study](../experiments/results/cnf-activity/README.md) retains all 1,389
prior queries and adds 36 at seed **20261109083909**: 24 fresh random 3-CNFs plus
twelve growing/signed/edited queries, including repeats. Both policies close all
512 tiny inputs and **806/913 non-tiny inputs**, with **no gains or losses**.
They close 30/36 fresh queries, including 18/24 new random inputs. All original
answers agree with the unchanged independent solver; all modes retain 19,557
solver residuals. The four-source pilot restores 956 relative to core-only ranking,
keeps 1024 closed, and leaves 977/1189 open. Source 977 now selects the formerly
unselected local case-97 core; its open part shrinks **two leaves / 138 literals ->
one leaf / 22 literals**. The whole source remains unresolved.

Continuation attempts fall **31,741 -> 7,184 (77.37%)**, logical probes
**127,741 -> 103,413**, and verified attempts **250,703 -> 223,315**. Reused
continuation probes fall 26,407 -> 1,615; active probes rise 1,588 -> 1,810 and
novel probes 3,746 -> 3,759. Active/new propagation therefore increases
**5,334 -> 5,569**. Most avoided work concerns unchanged pairs, not fresh solving.
Across discovery/checking there are 9,460 choice calls, 32,620 inactive / 5,100
active original pairs, 28,424 omitted inactive positions, 9,402 retained old
positions, 682 added positions, 3,088 empty continuations and 36 truncations.
These are repeated-operation counts over different descendants.

Single full-run baseline/activity time is **161.35645 / 134.22746 s**, discovery
**116.82649 / 99.01207 s**, but the unchanged solver varies **44.42359 / 35.13847 s**.
A new [balanced timing control](../experiments/results/cnf-activity/timing-control.json)
uses ABBA BAAB order, four fresh-database trials per policy on sources
858/875/907/970/1042/1061/956/977. Mean total time is **3.85140 / 3.88671 s** and
mean discovery **3.64992 / 3.68110 s**: activity is slightly slower on the subset.
All answers, summaries, counters, storage and database hashes repeat within each
mode. This does not establish statistical significance or a full-corpus estimate,
but prevents a speedup claim from the single full sample. Keep the policy optional
and preserve the unsuccessful timing result.

SQLite bytes are **376,205,312 / 375,824,384**, pattern nodes **22,549 / 22,581**,
logical node bytes **148,631,944 / 147,670,431**, probing-field bytes
**16,760,009 / 15,465,288**, and source bytes **5,405,961 / 5,422,677** across 1,393
records. Cold replay grows **55.11608 / 57.63553 s**, warm lookup **0.27624 /
0.34976 s**, and initialization **0.06187 / 0.28580 s**. Six-case Python peak is
**20,265,108 / 19,996,930 bytes**, excluding native SQLite, RSS and the full-corpus
peak. Operation timings include recognition, discovery, checking, serialization,
persistence, independent solving and successful lifts; generation, truth tables,
summary walks, initialization, compression, allocations and cold replay are outside.
Primary runs, allocation diagnostics, profiling, balanced trials, tests and builds
run sequentially. Exact preparation remains charged; no global cost guarantee follows.

The [mechanism ledger](../experiments/results/cnf-activity/mechanisms.json) replays
all **3,001** previously changed shared CNF/depth states: **421 learned -> learned**,
**16 clear -> learned**, and 2,564 remain clear. All 255 prior gained/lost local
controls reduce, and all informative old candidates survive the seven overflows.
In the new full archives, shared states have eighteen clear-to-learned and no
learned-to-clear transitions. These local reductions are not extra source closures.

The new frontier has **107 open sources / 147 distinct leaves**: 61 inconclusive
continuations (12,984 literals), 39 empty continuations (10,639), 46 clear passes
without a batch (4,264), and one without initial binary candidates (283). Source
**1194** costs **1.47590 s** discovery with 424 unresolved literal occurrences.
Its separate profile records 5,763 restrictions, 4,657 unit checks and 2,221
propagations. Probe-kind nodes occupy 96.289 MB including CNFs/keys/edges; probing
fields alone occupy 15.465 MB. Simply widening initial candidate selection when
binary ranking is empty addresses only one selected leaf here.

**Next discovery target: checked signed-clause subsumption exposing tractable
cores.** The [offline diagnostic](../experiments/results/cnf-activity/frontier-subsumption.json)
changes 105 frontier leaves, removing 217 clauses / 666 literals through 672,003
subset comparisons. Seven resulting cores are recognized as 2-CNF. Retained
signed-subset witnesses, complete source-index coverage, normalization maps and
classifier evidence are stored for every leaf. Removing a clause subsumed by a
retained clause preserves all models; values of disappearing variables are free.
For source 977, `(-7,3)` subsumes `(-7,-1,3)`, and `(-3,9)` subsumes `(-3,7,9)`.
The remaining clauses are binary.

Integrating these exact reductions could complete current selected plans for
**977, 1044, 1053 and 1365**. Sources 907, 1179 and 1363 retain another unresolved
leaf. These are **prospective completions**, not part of the measured 806/913.
The existing ordinary solver has positive-clause subsumption; the inventory lacks
this signed step. Subsumption is established simplification, not a novel arbitrary-
SAT solution. Next implement the source-bound transformation, checked exact child
binding and model lift, preserve earlier family priorities, and compare all relevant
states, failed recognition, storage and cold replay. The selected-frontier comparison
count is not a full-pipeline resource result. Add adversarial sign/order edits,
invalid retained dependencies and small exhaustive model-equivalence checks.

Three full, three pilot and three previous archives replay byte-identically, and
warm replay inserts nothing. Both reports have **53 matching fingerprints**;
archive and diagnostic/timing input/script hashes match. Verified implementation,
measurements, negative timing controls and prospective witnesses are pushed in
**e264fc3**. Manuscript Section **12.60**, Table **21**, README and persistent
priority/discovery/resource records now distinguish local progress, unchanged
source coverage, negative timing evidence and the next signed-core opportunity.
The **114-page PDF** builds with no final-pass warnings or box errors. Pages
**105--108** were visually inspected; all **54 earlier proof blocks** are unchanged
and **196 labels** are unique. Uniform arbitrary-CNF discovery, compact closure
and lifetime acquisition/storage bounds remain open.

## Checkpoint: terminal signed subsumption and its acquisition cost (9 November 2026)

The user's request to identify and work on the largest gaps led to integration
of the seven saved signed-subset opportunities. `SignedSubsumptionInventory`
extends the activity policy only at exhausted unresolved leaves. Every removal
has a retained signed source clause; complete index coverage, deterministic
search, normalization, family evidence and model lifting are checked. Failed
searches persist, with no new probe phase or hidden recursive budget. Earlier
policies, results and proofs remain available. Implementation/proofs and the
selected nine-source pilot are committed and pushed in **9924740**.

The [full study](../experiments/results/cnf-signed-subsumption/README.md) retains
all 1,425 old queries and adds 36 controls/holdouts. Non-tiny closure rises **833
-> 837 / 949**, with gains **977, 1044, 1053, 1365** and no losses. The old subset
rises 806 -> 810 / 913; both modes close 27/36 new queries. The ordinary solver
is unchanged and agrees in every mode, with 20,544 residuals per full archive.
Closure refers to recognized structural leaves, not satisfiability.

The gain has a broad-sample cost regression. Total operation time grows
**145.71977 -> 156.17943 s**, discovery **105.46141 -> 117.30413 s**, SQLite
**404.410 -> 408.302 MB**, cold replay **61.80056 -> 66.82085 s**, and six-case
Python peak **19.997 -> 20.390 MB**. Pattern nodes fall 24,367 -> 24,122, but
logical node bytes grow 161.206 -> 166.021 MB. Balanced twelve-query trials
instead average 7.28617 -> 6.98024 seconds; these include all four gains and
are not a full-corpus estimate or significance result. Keep the policy optional.

Three concrete next gaps are now saved with evidence:

1. **Futile subset comparisons.** The 3,753 searches expose 31 local families and
   retain 3,722 failures. Discovery and checking each perform 33,367,619 tests.
   `pair-costs.json` identifies **27,083,138 (81.17%)** equal-width comparisons
   that cannot succeed for distinct normalized clauses. Add length filtering,
   preserve duplicate/non-normalized helper semantics or enforce its precondition,
   and check that all saved witnesses/coverage remain identical. This saving is
   prospective until measured; do not replace the preserved naive result.
2. **Reuse proved implications for representation changes.** `mechanisms.json`
   independently replays original probe traces and uses all their binary
   consequences, including binary-transitive ones discarded by current learning
   selection, as subset witnesses. Eight remaining leaves expose 2-CNF. Current
   plans for **1185/1289/1368** could close; five other sources retain another
   open leaf. Integrate after existing priorities and charge enumeration,
   witness/proof checks, normalization, persistence and cold replay. These are
   not counted as executed source gains.
3. **Repeated restriction/checking and retained state.** Source 1194 still takes
   1.60328 s discovery; its separate profile records 5,763 restrictions, 4,657
   simplification checks and 2,221 propagations. Search evidence alone adds
   3.706 MB, and cold replay remains expensive. Share exact prepared state and
   certificates only with explicit dependency/invalidation rules and total-cost
   measurement. There is no lifetime archive or full-process memory bound.

The remaining frontier contains **112 sources / 149 distinct leaves / 32,043
literal occurrences**. Efficient discovery and recomposition for their general
interactions remain open. The subset routine has expected O(L + m log(m+1) + m²w)
work and O(L+m) temporary space per eligible CNF, with equally charged replay;
this is not an unrestricted-SAT efficiency claim or bit-machine refinement.

All **395 tests** pass. Three new Lean lemmas establish signed subsumption,
model equivalence and arbitrary extension on disappearing variables; the full
axiom audit passes **4,129 declarations / 1,971 theorem declarations**. All three
full, three pilot and three previous archives replay byte-identically; warm
reuse inserts nothing. Both reports have **56 matching fingerprints**, and the
mechanism, timing and pair-cost diagnostics have verified input/script hashes.

Manuscript Section **12.61**, Proposition **12.43** and Table **22** distinguish
the proved reduction, four measured gains, broad cost regression and unintegrated
implication opportunities. All **54 previous proof blocks** remain; there are
55 proofs and **199 unique labels**. The **116-page PDF** builds with no final-pass
warnings or box errors; pages **107--110** were rendered and visually inspected.
The ranked priority, discovery and resource records and README are updated for
the next run. No Python refinement, universal compact closure or P-versus-NP
conclusion is asserted.

## 2026-11-09: indexed witnesses and original implication exposure

The implementation/proof checkpoint **f978ad4** is committed and pushed. The
user's hourly-prompt correction was applied separately: the active hourly schedule
now has one concise paragraph pointing to the repository's gap analysis, with
flexibility to choose the next useful step and notifications only for meaningful
progress or blockers. Detailed procedures stay in this record and study files.

`ImpliedSubsumptionInventory` skips futile equal-width subset comparisons while
preserving the old first-retained witness; exact duplicates use a lookup and
repeated literals use the old fallback. Indexing-only mode keeps old archive
identities. A separate optional implication policy first preserves old exposures,
then uses every distinct absent binary from original probe traces as a potential
subset witness, including binary-transitive clauses filtered from learning. No
fresh propagation pass is added. Original reasons precede origin reconstruction,
subset checking, recognition and model lifting. Failed pools/searches persist.
The four-clause learned batch cap is unchanged; the additional subset-witness pool
has separate charged size b<=U, where U is original unit-trace length.

The [full study](../experiments/results/cnf-implied-subsumption/README.md) retains
1,461 old inputs and adds 36 controls/holdouts. Non-tiny closure rises **864 ->
869 / 985**, with gains **857, 1185, 1289, 1368 and 1467**, no losses, and every
independent solver answer unchanged. Old-subset coverage rises **837 -> 841 / 949**;
new-query coverage **27 -> 28 / 36**, including 15 -> 16 / 24 new random 3-CNFs.
This is checked structural coverage, not satisfiability or a faster SAT decision
procedure. The deliberately selected twelve-source pilot and old results remain.

Full single-sample total time is **169.84716 -> 169.80609 s**, discovery **127.44196
-> 126.71711 s**, SQLite **438.288 -> 437.621 MB**, and cold replay **71.70525 ->
69.97623 s**. Logical node bytes instead grow **178.289 -> 179.396 MB** despite
nodes falling **25,752 -> 25,047**. Six-case Python peak grows **20.390 -> 21.161 MB**.
Twelve-query ABBA BAAB means are **6.99619 -> 6.17832 s** total; these include three
gained sources and are not repeated full-corpus estimates or significance evidence.
Keep the candidate optional. All benchmark modes, allocations, profiles and
repeated timing controls ran sequentially after verification completed.

The separate indexing-only audit replays **24,122 old nodes / 1,429 sources** with
identical bytes and no inserts. Its 3,753 terminal checks reduce subset comparisons
**33,367,619 -> 6,284,481**, removing **81.17%** of pairs with identical certificates.
Its standalone node replay is 51.15654 s, excluding file preparation and source
binding replay; do not compare it directly with a full cold audit including
ordinary solver certificates. Expected indexed search is O(L+m log(m+1)+P w),
temporary space O(L+m), with P=O(m²) still possible. This does not improve an
unrestricted-SAT worst-case bound.

The new policy has 3,916 terminal searches, 110 local exposures (28 original,
82 implied), 3,684 nonempty pools and 29,897 binary clauses. Search evidence grows
**3.963 -> 9.030 MB**, including **5.087 MB** of implication data. The saved offline
relevance control retains only proved binaries fitting a long clause of the
original minimal core: **29,897 -> 7,505 (74.90%)**, all 82 observed exposures
preserved, **zero new frontier leaves**. It costs 2,278,253 relevance comparisons;
augmented subset tests fall 8,990,250 -> 7,138,675 per search/check. Integration,
end-to-end timing/storage and general syntactic family preservation remain open.
Do not count this as new executed coverage or a total-cost saving.

The next priorities have concrete evidence:

1. **Repeated restriction and proof checking.** Source 1194 remains the largest
   unresolved discovery case at 1.67226 s. Its separate profile again has 5,763
   restrictions, 4,657 simplification checks and 2,221 propagations, dominating
   own time. Share exact prepared clause/assumption or proof state with explicit
   source binding and invalidation; compare acquisition, persistence and cold replay.
2. **Unresolved structural interactions.** The enlarged frontier contains **116
   sources / 148 leaves / 33,651 literals**. Existing-pool relevance filtering
   adds no coverage. Test new source-entailed relations or exact decompositions,
   charging discovery and recomposition. A larger blind budget is not a structural
   explanation, and an unresolved category is not an efficient solver.
3. **Useful pools and shared evidence.** Integrate relevance filtering only with
   checked origins, preserved old results and all recognition costs; recorded local
   preservation is not a universal family-preservation theorem. Source references
   may reduce duplicated failed evidence, but lifetime archive and full-process
   memory bounds remain open.

All **403 Python tests** pass. The Lean lemma
`signed_core_of_entailed_batch_models` composes entailed augmentation and signed-core
model equivalence; the full build audits **4,130 declarations / 1,972 theorems**.
It does not refine Python's encodings, checker, persistence or costs. All three
full, three pilot and three previous archives replay byte-identically, including
all alternatives and sources; full modes retain **21,838 solver residuals**. Warm
reuse inserts nothing. Both new reports have **59 matching fingerprints**; all
mechanism, timing and index-control script/input hashes were verified.

Manuscript Section **12.62**, Corollary **12.44** and Table **23** record the semantic
composition, five measured gains, mixed resource effects and unintegrated pool
opportunity. All **55 previous proof blocks** remain, with 56 proofs and **202
unique labels**. The **118-page PDF** builds without final-pass warnings or box
errors; pages **109--112** were rendered and visually inspected. README, ranked
priorities, discovery and resource records are updated. No unrestricted efficient
partition, universal compact closure or P-versus-NP conclusion is asserted.

## 2026-11-09: bounded reuse of exact successful probe checks

The profiled restriction/checking bottleneck led to a narrow exact-reuse change.
`CheckedProbeReuseInventory` wraps the existing complete probe checker in an
optional ephemeral LRU cache. Keys serialize the full source, proof and config;
only successful checks admit results, and hits return fresh decoded values.
Edits miss, eviction requires rechecking, and cold replay begins empty. There is
no object-identity shortcut, partial signature, unchecked hint or persistent
policy change. Implementation, seven new tests and pilot/counterexample records
are committed and pushed as **9aba9df**. The hourly automation prompt is unchanged.

Two failures are preserved. The first full harness compared live tuple-containing
profiles with JSON-loaded lists; comparison now uses the exact canonical JSON
encoding. Subsequent review found that the preliminary cache could identify a
malformed tuple of original attempts with a valid list and bypass the old checker
on a warm hit. Non-list attempts now go to the original checker before cache
lookup. A regression test warms the cache then requires rejection. That full run
was intentionally interrupted before any completed full report. Preliminary code,
tests, pilot and logs remain; the final guarded pilot has fresh measurements.
The full runner also keeps extra pointwise checks out of the timed query stream
so they cannot supply uncharged cache warmup. Tests and the identical prior
archive retain that independent small-fiber validation.

The [full matched study](../experiments/results/cnf-checked-probe-reuse/README.md)
uses all **1,497** previous inputs. Both modes reproduce every answer, structural
profile, root identity and database byte. Coverage stays **869/985 non-tiny**,
with **116 sources / 148 distinct selected leaves / 33,651 literals** open. This
is cheaper repeated checking, not new structural coverage or a change to the
independent SAT decision solver. The archive is referenced once rather than
copied: **437,620,736 bytes**, 25,047 pattern nodes, 1,465 source bindings and
21,838 ordinary solver residuals. Both full and all five guarded pilot modes
replay cold byte-identically, including every alternative/source/solver proof;
warm replay inserts nothing.

Full single-sample total time falls **168.30879 -> 150.39216 s (10.65%)**, discovery
**125.59834 -> 108.60557 s (13.53%)**, and cold replay **71.60183 -> 62.58623 s (12.59%)**.
The six-case Python peak grows **21,161,086 -> 22,258,162 bytes**, a 1,097,076-byte
increase. Logical node storage is unchanged at 179,395,726 bytes. The 1 MiB cap
bounds retained serialized cache strings only, excluding allocator/LRU overhead,
transient construction, native SQLite/RSS and the original acquired state.

Twelve-query ABBA BAAB controls average **6.17550 -> 5.33388 s** total and
**5.88231 -> 5.04230 s** discovery. Four cached totals (5.27161--5.38252 s) are below
four baseline totals (6.11412--6.22190 s); unchanged solver means are 0.29174 ->
0.29045 s. Answers/summaries match the full study; within-mode counters, storage
and database hashes repeat. These selected synthetic measurements do not establish
significance, industrial performance or repeated full-corpus estimates. Benchmark
modes, allocation diagnostics, repeated controls and profiles ran sequentially.

Full operations make **57,798 lookups / 34,971 hits / 22,827 misses/admissions /
22,571 evictions**. They serialize 135,220,528 key bytes and 22,273,703 result
bytes, decode 29,375,582 bytes on hits, and admit 78,031,066 total string bytes
while retaining at most 1,048,576. Probe replays fall **248,307 -> 113,301**;
restriction visits **126,081,638 -> 82,210,169**; simplification reconstruction
visits **82,973,454 -> 51,574,914**. Propagation visits stay **105,860,805**.
Cold replay starts empty and has 17,266 hits / 40,357 lookups, reducing verified
probe attempts **181,314 -> 115,029** without skipping any first check.

The next priorities follow the saved profile and unchanged frontier:

1. **First-time propagation and remaining scans.** The largest baseline miss,
   source 1194, reduces restrictions **5,763 -> 3,399** and simplification checks
   **4,657 -> 2,303**. Propagation stays **2,221 calls** and becomes the largest
   named own-time cost. Test occurrence-index preparation and affected-clause
   propagation across assumptions. Bind indexes to the exact source; preserve
   or explicitly version proof order because traces affect later learning choices.
2. **Broader structural discovery.** The 116 open sources still need new
   source-entailed relations or exact decompositions. Neither this cache nor the
   saved implication relevance filter adds frontier coverage. Charge recognition,
   recomposition and unresolved interaction; a complete partition is not an
   efficient solution of every class.
3. **Smaller retained overhead.** The guarded eight-source pilot gets 1,385 hits
   at 256 KiB versus 1,387 at 1 MiB. Compare full-corpus costs before choosing a
   smaller capacity. The unintegrated 29,897 -> 7,505 implication-pool filter is
   another evidence-size opportunity, with its relevance comparisons charged.

All **410 tests** pass. Lean sources are unchanged from the preceding audit of
**4,130 declarations / 1,972 theorem declarations**; no new formal Python
refinement is claimed. The final full report has **62 verified fingerprints**;
both pilot reports resolve all 62 through current files or preserved snapshots.
Timing/profile hashes and the actual referenced gzip archive hash are verified.

Manuscript Section **12.63** and Table **24** record the cache invariant, its found
counterexample, charged recognition/storage costs, measurements and remaining
propagation/coverage gaps. All **56 previous proof blocks** remain; there are
**204 unique labels**. The **120-page PDF** builds without final-pass warnings or
box errors, and pages **111--114** were rendered and visually inspected. README,
ranked priorities, discovery and resource records are updated. No new tractable
family, compact closure or unrestricted-SAT worst-case improvement is asserted.

## 2026-11-09: affected-clause propagation with identical proof order

Implemented `OrderedPropagationInventory` over the existing 1 MiB check-cache
inventory. Simplification discovery uses an occurrence index and events ordered
by scan round and clause ID; the independent checker and ordinary SAT solver
stay unchanged. Exact order matters because different unit/conflict traces can
change later learning choices. Context-scoped selection restores the prior engine
on nesting and exceptions. The reference engine and all earlier results remain.

The [full study](../experiments/results/cnf-ordered-propagation/README.md) preserves
all 1,497 answers/profiles and the complete prior database bytes. Coverage stays
869/985 non-tiny, with 116 unresolved sources. Discovery falls 111.13169 ->
97.76173 s; balanced subset means are 5.08503 -> 4.55072 s. Total full time
154.63114 -> 137.59078 s includes variation in the unchanged solver. Cold replay
barely improves (63.40473 -> 62.61754 s); six-case Python peak rises by 216,400
bytes. SQLite stays 437,620,736 bytes. No new duplicate full archive is retained.

All 417 tests pass, including 9,724 exhaustive ordered small formulas, 3,000
random edits, all 148 saved frontier probe discoveries, archive identity and
independent reason checks. Both modes fully replay cold unchanged. The manuscript
adds an algorithm-level trace proof, preserving all 56 previous proof blocks;
Lean files remain unchanged and were not rebuilt. The full/pilot reports each
have 66 fingerprints. Thirty-two controls preserve strong reverse-chain gains
and early-conflict, forward-chain and hash-collision regressions. They prevent a
pointwise speed or unconditional word-cost claim.

Next: restriction is now the largest named own-time cost on source 1194, with
3,399 calls and 0.82048 s cumulative; simplification checking has 2,303 calls and
0.54588 s cumulative. Share exactly bound source/assumption state and residual
reconstruction, accounting for construction, invalidation and first-use costs.
Per-call occurrence indexes are still rebuilt; short conflicts expose wasted
preparation. Broader certified coverage and unrestricted SAT obligations remain
open. See [the current ranked record](structural-reuse-priorities.md).

## 2026-11-09: immutable-source occurrence reuse for restriction

Implemented `IndexedRestrictionInventory` above ordered propagation. A bounded
cache retains only sources validated as exact immutable tuple/tuple/nonzero-int
objects and their signed occurrence lists. Hits require the same strongly held
source; mutable/unusual/oversized inputs use the old scan, edits or separate equal
objects prepare afresh, and eviction/restart lose index reuse. Unaffected immutable
clause tuples are shared in the returned ordered residual. No proof verdict or
assignment result is cached, and the independent simplification checker is unchanged.
Indexed branch construction remains a trusted Python step, not a new Lean refinement.

The [full study](../experiments/results/cnf-indexed-restriction/README.md) preserves
all 1,497 answers/profiles and prior archive bytes. The first sample improves
discovery 93.85938 -> 90.65563 s and cold replay 60.86819 -> 56.04772 s, but total
regresses 132.36551 -> 134.44214 s as the ordinary solver phase also varies.
Selected ABBA BAAB mean total is 4.81769 -> 4.35747 s; a reversed-order full
comparison is retained separately to assess the mixed full result. Six-case
Python peak grows 1,598,364 bytes, and retained memory grows 1,285,252 bytes.
SQLite is still exactly 437,620,736 bytes, referenced rather than duplicated.

All 425 tests pass, covering 87,516 exhaustive formula/partial-assignment pairs,
4,000 random/edited restrictions, types/mutation, source lifetime, fallback/caps,
sharing and old archive replay. Both modes check all evidence cold unchanged.
Full/pilot reports each have 70 fingerprints; separate profiles, timing and
32 locality controls preserve favorable reuse and equal/new-source regressions.
The manuscript adds an algorithm-level correctness argument and preserves all
57 previous proof blocks; Lean sources are unchanged and were not rebuilt.

The cost target has shifted: restriction on source 1194 falls 0.82784 -> 0.21269 s
cumulative; simplification checking remains the largest named own-time cost, with
2,303 calls and 0.55562 s cumulative. Full reconstruction still visits 51,574,914
literals. Broader coverage remains 869/985 non-tiny, with 116 unresolved sources;
new certified relations or exact interaction decompositions are still required.
Retained-space reduction, independent checker reuse and exact new-source/append
preparation are recorded in the current ranked gap analysis.

The full reverse-order control is complete. Across two samples per mode, means
are 137.36963 -> 131.36045 s total, 97.29044 -> 89.16122 s discovery and 61.16937 ->
56.70501 s cold replay (4.37%, 8.36% and 7.30% reductions). All within-mode operation
counters and archive hashes repeat. The reverse allocation repeats the roughly
1.60 MB Python peak increase. These limited synthetic samples balance order but
do not erase the initial regression, establish significance or justify universal
speed claims. Both complete reports and the order-control hashes are preserved.


## 2026-11-09: one-pass independent reconstruction and the next coverage target

The [matched study](../experiments/results/cnf-single-pass-check/README.md) replaces
repeated checker scans with a direct prefix-invariant reconstruction. It lazily
copies affected clauses and shares untouched tuples without another retained cache.
Unit reasons, conflict and fixed-point checks, pure rounds and source bindings
remain independent of discovery. Default scan behavior and all previous evidence
are preserved. The proposed clause-support cache regressed in both pilots; its
code, exact snapshots and unsuccessful experiments remain available but unselected.

On 1,497 inputs, discovery falls 93.90373 -> 87.70857 s (6.60%) and total
137.78680 -> 130.04664 s (5.62%). Cold replay regresses 57.32273 -> 57.93447 s;
warm replay also increases. Six-case Python peak is essentially unchanged at
24,072,934 -> 24,073,162 bytes. All answers, profiles, identities and persistent
bytes agree. ABBA BAAB subset means support 4.60% total / 5.23% discovery savings,
with overlapping trials. Five of 48 helper controls regress, including wide
clauses where every clause changes. No pointwise speed or total-memory win follows.

All 433 tests pass. New tests cover 175,032 exhaustive reconstruction-policy
combinations per candidate, full-checker policies, random edits, unusual inputs,
forged certificates, independence from discovery, all saved frontier proofs and
cold corruption rejection. Full cold audits replay 25,047 pattern nodes, 1,465
source bindings and 21,838 solver residuals, preserving the existing 437,620,736-byte
archive. The full report has 75 fingerprints; separate timing, profile, control
and frontier diagnostics bind their scripts and inputs. Implementation checkpoint:
`d0b8917`. All 58 preceding manuscript proof blocks remain, with one new invariant;
Lean sources are unchanged and were not rebuilt.

The current profile selects source 1446: reconstruction cumulative time falls
0.37732 -> 0.29957 s, while normalization remains 0.40226 s cumulative. The
reconstruction helper still has the largest named own time. Further implementation
reuse must preserve checked input identities and charge preparation; the rejected
cache shows why a high hit count alone is insufficient.

A separate read-only discovery probe identifies 35 of 148 selected unresolved
leaves as Horn after consistent polarity changes (852 of 33,651 literals). It
checks every positive flip and negative auxiliary implication refutation, and
matches exhaustive flip enumeration on 512 tiny formulas. This is an established
renamable-Horn test, not a novel class. Negative auxiliary results do not imply
UNSAT of the original CNF. Current integrated coverage stays 869/985 non-tiny,
with 116 source misses. The next priority is versioned recognition, checked
polarity/model transport and exact ancestor recomposition, followed by matched
acquisition, storage and cold replay. Most remaining literals lie outside these
small positive leaves, so broader interaction discovery remains necessary.


## 2026-11-09: the 35 polarity opportunities are integrated

Checkpoint **86d603b** adds a versioned terminal Horn-renaming edge, direct
positive Horn checking, source-linked negative auxiliary paths and a pre-enumeration
pair cap. Models lift through normalized names and a fixed polarity involution;
Lean proves evaluation and SAT/UNSAT preservation. The old policy and archives
remain available. Negative auxiliary proofs exclude a class, not original SAT.

The [1,497-source comparison](../experiments/results/cnf-polarity-horn/README.md)
closes 29 additional whole sources, with no losses (**869/985 -> 898/985 non-tiny**).
All 35 saved positive leaves close independently; 188 acquired edges pass endpoint
and model checks. The 87 remaining sources have 106 selected unresolved leaves
and 32,404 literals, each with a checked renaming exclusion. Every new whole-source
gain is itself excluded from renaming, demonstrating residual composition across
source categories. Earlier decomposition priorities and budgets remain intact.

Single-run discovery is 80.78495 versus 84.99193 s; total 122.78419 versus
126.02211 s; cold replay 51.32492 versus 54.89246 s. Warm replay regresses. Fresh
SQLite is 417,370,112 versus 437,620,736 bytes; six-case traced peak is 20,286,004
versus 24,073,154 bytes. Historical archives still consume retained space. All
441 Python tests and the full Lean audit pass (4,136 declarations / 1,977 theorem
declarations). All 59 earlier manuscript proof blocks survive.

Next: exploit the saved non-renaming obstruction paths to find shared-variable
interfaces or conditioning choices that expose different tractable residuals,
with matched budgets and exact recomposition. Repeated recognition alone cannot
undo those exclusions. The remaining sources take 70.6% of discovery time;
normalization/reconstruction and indexed subset certificates are supporting cost
gaps. Repeated/industrial evaluation, full-process memory, policy-independent
storage sharing and unrestricted efficient coverage remain open.


## 2026-11-09: obstruction-only conditioning is not promoted

The [106-leaf experiment](../experiments/results/cnf-obstruction-frontier/README.md)
adds checked source-path ranking as an optional policy, with persistent certificates,
independent checker replay and unchanged candidate/branch/probe limits. Giving
both modes one additional conditioning level closes 60/106 under the retained
policy and 57/106 under the candidate. Its three gains and six losses are preserved;
discovery rises 5.10% and SQLite from 35,840,000 to 37,498,880 bytes. This negative
result does not change original-source coverage (898/985).

Checkpoint **d25a2e5** preserves both full archives, exact changed source/choice
records, a guarded-support counterexample and separately checked original-probe
influence. Five lost old winning variables lie outside the recorded obstruction's
support. In case 4, already-acquired unit traces show indirect propagation into
that support, without fresh solving. Cases 17 and 50 remain counterexamples to
using that effect alone: their original closures leave the saved edges intact,
but later discovery still closes the branches.

All 448 tests pass, including source context restoration, cold checking without
SCC rediscovery, corrupted evidence and old-row preservation. All 60 previous
manuscript proof blocks remain; the new proposition only concerns untouched
obstructions under raw restriction. Lean sources are unchanged. Next test checked
propagation influence across families and portable reuse of successful plans,
with baseline diversity, explicit missing traces, matched budgets and fresh data.
Do not repeat this static-overlap heuristic or promote its favorable small memory
subset as a general result.

## 2026-11-09: reuse unit traces to reorder, preserve coverage, reject slowdown

Added optional `ProbeRankInventory`, reusing only original source-bound traces
and promoting one existing candidate while retaining the rest. No new probe or
auxiliary discovery is requested; checking reconstructs the order after validating
the original proofs. All 453 Python tests pass. New Lean lemmas establish set
membership and the local closure implication, without a Python refinement.

The [two-run frontier comparison](../experiments/results/cnf-probe-rank-frontier/README.md)
keeps 60/106 closures but discovery increases 5.19854 -> 5.44908 seconds; total
8.22342 -> 8.63390. Attempts stay at 268. Nodes fall 1,540 -> 1,524 while SQLite
grows 35,840,000 -> 35,979,264 bytes. The [fresh controls](../experiments/results/cnf-probe-rank-fresh/README.md)
keep 71/96 closures, with no changed candidate orders and effectively flat mean
time. Thirty-six of 39 branching states lack binary clauses; only 9/156 candidate
positions have paired traces. Archive bytes are reproducible across execution
orders, independently cold-checked, and preserved under warm replay. No policy
promotion or original-source coverage gain follows. Next investigate bounded
multi-variable interfaces or exposed binary relations, and portable successful
plans/direct proof transport instead of another scalar ordering proxy.


## 2026-11-09: retained binary paths, new closures and a scheduling counterexample

Added optional `BinaryPathInventory` and an independent source-linked checker.
Binary implication paths entail wider clauses; only those wide clauses are
removed, preserving all reasons for simultaneous deletion. Reachability searches
at most 64 roots per residual and stores shared proof prefixes. Cold checking
validates edges, endpoints, normalized children and exact summaries without
reachability rediscovery. The default `PolarityHornInventory` stays unchanged.

The [full comparison](../experiments/results/cnf-binary-paths-full/README.md)
raises structural coverage 898/985 -> 901/985, with four gains and one loss. All
ordinary answers agree. Discovery rises 81.47602 -> 97.00720 s; total 122.46371 ->
139.46329 s; SQLite 417,370,112 -> 475,529,216 bytes. The frontier gains three
closures beyond the direct-only control, while 96 fresh cases gain none. Every
archive, failed alternative, source and previous experiment remains preserved.

`loss-alternatives.json` isolates source 1471: after equivalent deletion, an old
successful variable-1 split disappears from a child's four-candidate list. The
old closure-invariance theorem requires unchanged membership and therefore does
not cover this change. Reusing the existing checked plan, instead of acquiring
both policy graphs, is the next concrete gap. The archive union 902/985 is an
observation, not an implemented efficient portfolio.

The full graph stores fewer proof-prefix nodes than separate paths (21,894 vs
25,359), but more positive JSON bytes (334,245 vs 230,535). Full-state acquisition
and preparation dominate the remaining cost. Shared preparation needs explicit
clause/name transport; hidden-literal elimination is another unimplemented
coverage experiment. See [proof, costs and limitations](binary-paths.md).

All 461 Python tests pass. Four new Lean lemmas prove retained binary edge/path
soundness, clause entailment and batch equivalence. Full build/axiom audit passes
at 4,148 declarations / 1,988 theorem declarations. All 62 previous manuscript
proof blocks survive, with one added proposition. No unrestricted-SAT bound is
claimed, and this higher-cost optional policy is not promoted.


## 2026-11-09: exact references preserve the old plan and reduce reacquisition

`RetainedPlanInventory` checks a positive old closure with the original verifier
and records an exact source/depth/policy reference before new binary-path
acquisition. It keeps the old graph and all failed alternatives unchanged. A
reference does not require the new scheduler to choose the old winning variable.
Corrupt source/policy/depth/profile bindings, false positive hints and missing
proof dependencies reject reuse. An absent or non-closed hint only skips reuse.

The [full prepared-history comparison](../experiments/results/cnf-retained-plans-full/README.md)
recovers source 1471: 901/985 -> 902/985, with no losses. Discovery falls 98.33619
-> 81.96656 s, total 190.63432 -> 177.05292, added SQLite 338,288,640 -> 211,906,560
bytes, and combined SQLite 755,658,752 -> 629,276,672. Original acquisition and
417,370,112 seed bytes remain liabilities. Cold replay falls 95.64397 -> 82.52345 s;
warm replay regresses 0.27327 -> 0.41059. Six-case Python peak grows 19.68%.
The fresh and empty-history controls keep 88/96 closures and regress in discovery.

Benchmark-only tuple/list assertions and a mixed-connection audit lock were
retained and fixed. Completed full acquisition and cold audits were recovered
from preserved checkpoints after finalization failed; the original runner is
frozen, all profiles/answers/hashes rechecked, and no acquisition timer estimated.
Both full archives and every seed row remain preserved. Eight new tests cover
proof reuse, the actual lost split, edits/corruption, small models and cold replay;
all 469 tests pass. Lean sources are unchanged; the full build/axiom audit passes.

The next large cost is a full metadata census in `ResidualSolver.solve` on every
query: a separate scan averages 57.14 ms over 21,838 rows. Avoid or maintain that
aggregate without changing decisions. Then reduce duplicated verifier state and
checking of historical failed alternatives, reject unprofitable trivial references,
and develop exact transport/upgrades beyond a fixed prepared prefix. The default
policy is unchanged. See [mechanism and limits](retained-plans.md).


## 2026-11-12: transactional residual accounting, measured and preserved

Implementation checkpoint `e32b33f` introduces optional `AccountedResidualSolver`;
the historical `ResidualSolver` remains the full-census control. Opening rebuilds
one counter row; triggers maintain it transactionally for normal residual writes.
Possible key/rowid conflicts invalidate it for locked reconstruction. Rollback,
legacy writers, Unicode/NUL SQL length semantics, cold reconstruction and partial
budget failures are tested. Direct alteration of private accounting state during
a live connection is outside the contract. No proof/search method is replaced.

All 476 Python tests pass. Full, fresh and empty matched comparisons preserve all
prior rows, match every per-query total, and produce identical evidence-table
digests. Query cost is 171.12270 -> 87.88366 seconds on prepared original inputs,
15.20412 -> 8.38678 on the fresh prepared controls, and 7.70202 -> 7.73052 without
history. All acquired results and six complete compressed archives are retained.
Added SQLite overhead is 4,096 bytes. Ordinary counters perform one opening census
and no per-query rebuild in these runs; independent validation scans are separate.

No coverage or underlying search gain is claimed. Discovery and duplicated
verifier state now dominate the measured prepared workload. Next: selected sound
proof reuse, shared/bounded checking state, useful-reference admission and plan
transport beyond exact prepared sources. See [mechanism and limits](residual-accounting.md)
and the updated [priority record](structural-reuse-priorities.md).

The unchanged Lean build/axiom audit passes at 4,148 declarations / 1,988 theorems.
Its first rerun exposed 16 missing sidecar files in the temporary toolchain;
only those files were restored from the digest-verified official release. The
failure and repair record are preserved with the full benchmark. The manuscript
adds the accounting invariant, measured costs and controls; all 63 previous
proof blocks remain unchanged. No Lean refinement of SQLite is claimed.


## 2026-11-12: reuse checked traces from old unresolved plans

Cost attribution of the accounted run shows the 83 unresolved inputs consume
67.35991 / 81.41598 discovery seconds. This changed the immediate target from
selected closed-proof validation to useful intermediate evidence from failed
expansion. Implementation checkpoint `836fb96` adds optional
`PreparedProbeInventory` and a no-op extension hook to the retained-plan reader.
Saved probe traces from an exact old open plan undergo the ordinary independent
source-bound check before replacing acquisition. No old closure, classification
or child graph is trusted. Pending hints are scoped and cleared on failures;
source/settings edits, corrupted evidence and empty history are tested.

All 481 Python tests pass, including 512 exhaustive tiny CNFs, seeded larger
inputs and preserved cold replay. The full matched run reuses 2,437 traces,
reducing fresh probe attempts 77,804 -> 60,972, but verification attempts remain
77,498. Discovery falls 79.80360 -> 78.51427 seconds (1.62%); total query time
85.97296 -> 84.07622. The unchanged solver accounts for part of that timing
variation, so it is not all avoided acquisition. All three evidence tables and full
database bytes match, every old row survives and both cold audits pass. Storage
stays 629,280,768 bytes; sampled Python peak slightly increases. No new coverage
is claimed: the optional prepared result stays 902/985, default 898/985.

See [full evidence](../experiments/results/cnf-prepared-probes-full/README.md)
and [mechanism and limits](prepared-probes.md). This acquisition optimization
has limited measured headroom while intermediate verification and other discovery
work remain. Next profile the expensive open expansions, then share exact checked
intermediate states or expose equivalent cores. Selected closed-proof checking
is still open, with a smaller measured cost ceiling than the unresolved inputs.


The fresh and empty controls each reuse zero traces and keep 88/96 closures.
Fresh total time regresses 7.70214 -> 8.61204 seconds; empty changes
7.59890 -> 7.43109. Identical operation counts make these controls evidence
against claiming a general benefit. All six compressed archives and every paired
record are validated. The unchanged Lean audit passes (4,148 declarations /
1,988 theorems); the manuscript keeps all 63 proof blocks, adds section 12.73,
builds without warnings and passes visual review of the changed pages.


## 2026-11-12: source-identity indexing fails to amortize preparation

Profiled the costly unresolved source 1194 from the old prepared archive. Independent
reconstruction is the largest individual Python own-time entry. Checkpoint `f6fb244`
adds an optional checker-owned occurrence index, with exact immutable source binding,
separate discovery/checker state and a shared 32,768-slot checker budget. All original
proof reasons and fixed points remain checked. It passed 487 tests before timing.

The 96-input empty-history control retains 88 closures and byte-identical databases,
but discovery regresses 6.36510 -> 6.63704 seconds and total 7.54255 -> 7.89263. Only
658/15,071 reconstruction calls hit. Preparing nearly every source adds enough work
to erase the avoided untouched-clause scans. Sampled Python peak increases. Both
complete archives and failed timing evidence are retained, not promoted.

A 32-fold capacity increase on source 1194 leaves 80/2,617 hits across both views.
An extra exact source/assignment restriction memo also fails in a three-way pilot:
1.12695 seconds current, 1.17052 indexed, 1.19950 combined. It gets 498 restriction
hits but only 141 checker-index hits. Three additional tests verify its reuse, type
fallbacks, budget behavior and byte-preserving replay; the full 490-test suite passes.

A no-eviction observer proves the measured identity limit is not eviction: 2,537
retained source identities contain only 2,167 exact CNF values, with 370 duplicate
admissions. Exact whole-source interning has limited headroom here. Next measure
reuse of unchanged clause blocks and checked deltas across related but unequal
residuals; avoid repeating the earlier per-clause cache regression. No full new
prepared-corpus benchmark was justified after these negative controls. Historical
optional coverage stays 902/985; no new coverage or unrestricted bound is claimed.

The unchanged Lean audit passes (4,148 declarations / 1,988 theorems). The manuscript
keeps all 63 proof blocks, adds section 12.74, builds warning-free and passes visual
review. [Mechanism and limits](indexed-check.md), [preserved diagnostics](../experiments/results/cnf-indexed-check-profile/README.md)
and the priority record retain the next target and the unsuccessful alternatives.


## 2026-11-12: shared-clause masks reduce scans but fail total-cost controls

Checkpoint `c7914b5` adds an optional independent clause-mask reconstruction
engine and observer. Two hard prepared sources share exact immutable clauses at
70.32% and 70.53% of visits. Only independently validated representation facts
are retained. A zero mask intersection proves no assignment overlap; collisions
require scanning. Every unit reason, conflict and fixed-point obligation remains
checked. Both checker views share a 32,768-slot FIFO, with no new persistent state.

All 496 Python tests pass, including exhaustive tiny reconstruction, arbitrary
large/colliding identifiers, mutations, malformed types, forged evidence and
byte-preserving cold replay. The three-source pilot is almost flat in runtime.
Two matched 96-input empty-history comparisons, in opposite execution orders,
reduce literal work including preparation 4,173,407 -> 1,873,711 (55.10%). Yet total
query time rises 7.37185 -> 7.56226 and 7.31352 -> 7.57542 seconds. Four-case peak
traced Python allocation rises about 41%. Counters outside reconstruction are
identical. Both modes close 88/96; all four 33,460,224-byte databases match exactly
and all cold audits pass without changing bytes. Every archive is preserved.

The candidate remains optional and disabled. No full prepared-corpus run was
justified. Historical default/optional coverage remains 898/985 and 902/985;
the new controls do not remeasure that corpus. Overlap alone is not a gain when
lookup, preparation, FIFO maintenance and output assembly consume the avoided
short scans. A coarser representation still needs stable proof-reason positions
and a concrete cost advantage. The revised priority is bounded checked variable
elimination on the unresolved frontier, followed by transport into shared cores.

The existing Lean audit passes (4,148 declarations / 1,988 theorems); all 63
manuscript proof blocks remain unchanged. Section 12.74 records the follow-up,
the PDF builds warning-free and pages 127--129 pass visual review. See
[mechanism and limits](clause-mask-reuse.md) and
[preserved evidence](../experiments/results/cnf-clause-mask-pilot/README.md).

## 2026-11-12: checked elimination closes 29 earlier misses at extra cost

Checkpoint `e7a806b` adds optional bounded Davis--Putnam elimination at unresolved
terminal nodes. A certificate identifies a pivot; the independent checker rebuilds
all opposing-pair resolvents and checks exact binding, pair and growth limits.
SAT models lift back to the source. A null proposal proves neither impossibility
nor UNSAT. Lean proves the existential projection identity under explicit pivot
absence conditions; Python normalization, persistence and costs remain outside
that formal result. All 501 Python tests and the 4,168-declaration / 2,004-theorem
Lean audit pass.

The matched 99-leaf comparison closes 0 / 14 / 37 leaves for baseline / pure-only /
bounded elimination. A separate run queries all 83 original prior misses from the
same paid prefix: 0 / 11 / 29 close, retaining every pure-only closure. The bounded
candidate leaves 54 original sources, 59 selected open leaves and 26,205 literals.
It does not rerun the full 1,497-input corpus. Query time rises 64.76503 -> 80.09857
seconds and database bytes 605,675,520 -> 621,146,112. No default policy changes.
Every old row survives, all six complete archives cold-replay without changes,
and independent endpoint/model checks cover all 1,728 pure-only and 2,822 bounded
original-input elimination edges. The latter diagnostic costs 688.09686 seconds
in addition to query and cold-audit time; it is retained as validation cost.

The next bottleneck is concrete: 167,129 candidate tests, 156,757 growth rejections
and 1,457,523 discovery pairs. Accepted mixed steps mostly have one occurrence on
one side (1,588, versus 111 with multiple occurrences on both sides). A single
binary occurrence gives a cheap sufficient non-growth rule, whose frequency and
ordering effects remain unmeasured. Exact target sharing is limited: 2,822 edges
reach 2,821 target keys. The remaining frontier has 58/59 leaves with pair-bounded
candidates but no non-growing step under the current rule. Ten admit a candidate
if retained-clause subsumption removes redundant new resolvents. This opportunity
is not yet integrated or an additional closure. Profile failed candidate work,
then test cheap admission and checked redundancy before increasing caps.

The [mechanism and resource account](variable-elimination.md),
[frontier comparison](../experiments/results/cnf-variable-elimination-frontier/README.md),
[original-source comparison](../experiments/results/cnf-variable-elimination-originals/README.md)
and [analysis/provenance](../experiments/results/cnf-variable-elimination-probe/README.md)
preserve the evidence and limitations. Section 12.75 records the result while
keeping every earlier manuscript proof block. The PDF builds without warnings;
pages 128--130 pass visual review. The aggregate validator confirms report and
runtime hashes, all six archive integrity checks, identical ordinary-solver
residual tables, all 63 unchanged proof blocks and 225 unique labels. No
unrestricted polynomial SAT bound or complete efficient structural partition is
established.

## 2026-11-12: subsumption fallback is correct but does not close more inputs

Checkpoint `14ae642` adds an optional retained-clause subsumption fallback after
ordinary bounded elimination fails. Every omitted resolvent names its two
parents and a source subclause that survives pivot elimination. The independent
checker visits all pairs, verifies those reasons, checks non-growth and binds
the complete child. Source/model lifting and all earlier obligations remain.
Lean proves subclause implication, redundant-clause removal and the corresponding
existential projection. All 506 tests and the 4,173-declaration / 2,009-theorem
axiom audit pass; Python refinement and costs remain separate obligations.

The matched 59-leaf comparison permits ten new subsumed elimination edges and
one following ordinary elimination, but closes none. Selected open literals
fall only 26,205 -> 26,181. Query time rises 2.88938 -> 3.12938 seconds, and
2.96506 -> 3.30563 in reversed order; per-mode archives match exactly. The
83-original comparison preserves exactly the same 29 closures, with time
79.65962 -> 88.16727 seconds and storage 621,146,112 -> 628,133,888 bytes. The
baseline archive reproduces the previous bounded run. The candidate acquires
324 subsumed edges across all retained alternatives, with 86,305 candidate tests,
85,902 growth rejections and 8,639,284 subset tests. All new edges have independent
endpoint/model diagnostics; the original-input diagnostic costs 33.47933 seconds
outside acquisition. All six archives cold-check unchanged and all old rows
survive. Existing-rule edges receive complete cold proof checks without repeating
their extra endpoint diagnostic in these runs. The fallback is not promoted.

A read-only ablation finds the larger opportunity: 48/59 remaining leaves admit
a candidate without increasing clause count if up to eight extra literals are
allowed, or 49/59 with subsumption. Fifteen plain candidates need only one extra
literal. None satisfies the present joint non-growth rule. For a normalized CNF
with m clauses and n variables, L <= mn; an elimination-only chain with at most
m0 clauses and decreasing variables from n0 therefore has at most m0*n0 literals
per intermediate CNF and at most n0 steps. This does not guarantee a next pivot,
a tractable endpoint or a bound on all retained branching history. The next
controlled test is plain clause-count-based admission, with exact checks and
explicit intermediate-width costs. No such policy or extra closure is claimed
by the diagnostic.

The [mechanism and limitations](subsumed-elimination.md),
[remaining-leaf controls](../experiments/results/cnf-subsumed-elimination-remaining/README.md),
[original-source comparison](../experiments/results/cnf-subsumed-elimination-originals/README.md)
and [aggregate validation](../experiments/results/cnf-subsumed-elimination-validation/README.md)
retain the failed experiment, complete archives and next target. The manuscript
adds section 12.76 while preserving all 63 previous proof blocks. Fresh holdouts
and a new full-corpus run were not justified by the negative controls; there is
no new unrestricted SAT complexity claim.

The aggregate validator also confirms identical ordinary-solver residual tables,
opposite-order per-mode archive equality, all six SQLite integrity checks,
runtime/report fingerprints and 226 unique manuscript labels. The PDF builds
without warnings; pages 129--131 pass visual inspection with final file hashes
recorded alongside the proof and test logs.

## 12 November: permit literal growth while bounding an elimination chain

Implemented `ClauseBoundEliminationInventory`, preserving the earlier joint
non-growth choices and trying a clause-count-only fallback at unresolved
terminals. Complete opposing-pair reconstruction, strict support decrease,
exact child binding and SAT model lifting remain independently checked. All
**511 Python tests** pass, including exhaustive small projection, random edits,
large signed identifiers, explicit growing-literal examples, clause-growth
rejection, history preservation and corruption checks. Lean's audit passes
**4,195 declarations / 2,018 theorems**; `ClauseBoundElimination.lean` proves
conditional per-formula, chain-length and formula-state payload bounds.

The 59 post-subsumption leaves yield one closure versus zero, at higher time and
storage. Whole-source recomposition on the 83 prior misses yields **31 versus
29 closures**, with no losses; the two gains are distinct 48-variable sources.
There remain 52 original misses and 57 selected leaves / 25,488 literals. Query
time grows **78.06321 -> 113.63899 seconds**, complete archive bytes
**621,146,112 -> 674,234,368**, and newly added bytes above the common prefix
**203,776,000 -> 256,864,256**. Every old row survives. The baseline reproduces
the earlier bounded archive exactly. Complete cold checking preserves bytes;
all 2,504 new edges pass independent endpoint solving and SAT model lifting.

The new endpoints cost **961.43125 seconds** to diagnose. The diagnostic still
uses `ResidualSolver` and its per-solve SQL census; ordinary queries use the
already optimized `AccountedResidualSolver`. Census versus solving time is not
profiled here. Do not hide the diagnostic phase or attribute all of it to the
new discovery policy. Four-case Python allocation is only a sample, not a
full-history or native-memory bound.

There is still no admissible-pivot availability theorem or efficient complete
elimination-order search. The rule tests 166,437 additional candidates and
rejects 162,187 for clause growth. A fixed opposing-pair cap B would also keep
an accepted elimination-only chain within m0+B*n0 clauses if clause growth were
allowed; this looser policy remains unimplemented. Recognition, alternatives,
persistence and the final fallback remain separate from that formula bound.
See [the full mechanism and limitations](clause-bound-elimination.md).

## 12 November: checked additive growth, with a negative coverage result

`AdditiveEliminationInventory` and `AdditiveElimination.lean` implement and bound
fixed per-step allowances of one and two clauses after earlier non-growth rules
fail. Every projection has complete opposing-pair checking, strict support
decrease, exact target binding and checked model restoration. Prior rows and all
failed alternatives are preserved. All **516 tests** and the **4,216-declaration /
2,028-theorem** Lean audit pass. The chain bounds remain conditional and do not
establish an efficient arbitrary-SAT construction.

The [matched evidence](additive-elimination.md) is negative for the intended
coverage gain: zero new closures on 57 final leaves or 83 original prior misses.
All original modes close the same 31. Query time rises from 121.61751 to 142.26465
and 163.21184 seconds; acquisition bytes rise from 674,234,368 to 700,178,432 and
734,814,208. The added rules acquire 1,021 and 2,530 independently checked edges.
Reference endpoint proofs, models and answers now persist in separate archives;
the largest reference database occupies 1,236,189,184 bytes before compression.
It is charged separately from acquisition. No old solver evidence is replaced.

The current gap is useful order/endpoint discovery and avoiding unsuccessful
repeated recognition. Valid steps and a small formula bound are insufficient
progress criteria. The ranked [priority record](structural-reuse-priorities.md)
retains the controls, limits and next target. Default policy remains unchanged.

## 12 November: required-literal filtering preserves exact subset certificates

Added optional anchored subset inventories, leaving the earlier runtime classes
and archives intact. A retained nonempty clause is stored under one required
literal; candidate ranks preserve the earlier first-witness order. Empty clauses
and equal-width duplicates are explicit, with fallback for uniform-width and
repeated-literal inputs. Independent checking validates every witness and builds
its own index from the actual source. Original implication origins remain bound
to checked source traces. No cross-source answer cache or invalidation rule is
assumed.

The [retained study](anchored-subsets.md) records a negative whole-input cache
result, exact kernel comparisons and complete acquisition/cold comparisons.
All 521 Python tests and the Lean audit of 4,219 declarations / 2,031 theorems
pass. The three new abstract lemmas prove necessary-literal completeness and
first-match preservation, not Python refinement or machine costs. Coverage and
stored results are unchanged by design; new endpoint-producing discovery and
full-history memory bounds remain open.

The verified originals comparison reduces query time **155.78451 -> 139.68494
seconds (10.33%)** and cold checking **111.46828 -> 102.79093 (7.78%)**, with the
same 31/83 closures and 734,814,208-byte archive. The repeated control improves
query time by 4.67%, with unchanged 88/96 coverage and bytes; cold time and sampled
allocation are essentially unchanged. Reversed leaf order also favors the index.
All eight cold runs and three unique acquisition archive integrity checks pass.
The source/report validator preserves all 63 earlier proof blocks and checks 229
unique labels. The 142-page PDF builds without warnings; pages 133--135 pass
visual review. Evidence and failed cache/control ideas persist in the linked study.

## 12 November: bounded pivot deviations and exact descendant reuse

Implemented optional search over four earlier open elimination ancestors and
at most eight fully recognized target projections per open source. Complete
projection checking, exact target/name binding and independent trial replay
protect every alternative. Old nodes remain immutable, while original-source
recomposition checks component conjunction and both conditioning branches.
The search persists all acquired target histories and unique trial records as
an exact-base-bound delta. No default recognizer, ordinary solver or formal
source is changed. All **527 Python tests** pass.

The first original-source experiment makes **316 trials**, adds **602 pattern
nodes**, and retains **31/83** closures with no gains. **295/316** trials reach
the exact same selected frontier; 271 pivot pairs share no source clause, with
260 exact reconvergences. The interaction-priority follow-up raises interacting
trials **45 -> 74**, adds 660 nodes, but also gains no closure. Resident expansion
costs **6.45902 / 7.11551 seconds**, with initial and cold verification charged
separately. New delta SQLite bytes are **15,208,448 / 16,248,832** over the same
734,814,208-byte paid base. Repeated controls remain 88/96 in both schedules.
The [full study](pivot-alternatives.md) retains phase costs, failed attempts and
limitations. Coupled continuations, later ancestor selection and an explicit
new-state budget remain the next discovery gaps.

Both schedules' proof deltas also combine without conflicting payloads. The
original-suite union retains 708 distinct new pattern nodes / 345 trials, sharing
554 node rows and 287 trial rows between schedules. Repeated-control union counts
are 121 new nodes / 45 trials. The persistent resume recipe and logical table
hashes are in the study and validation record; later runs should reuse this union
rather than discard the unsuccessful acquisitions. Every constituent graph has
passed full cold checking. The final PDF preserves 63 existing proofs, has 230
unique labels, builds without warnings and passes visual review on pages 135--137.

## 12 November: reuse failed trials and test later elimination ancestors

Implemented a near-frontier ancestor schedule and a matched early-ancestor
control, both starting from the exact union of the two prior pivot histories.
Prior source/pivot/configuration trials are independently checked and reused;
only new trials spend the eight-entry budget. All old rows, including trial
records, are protected against modification. New deltas are relative to that
merged seed, with exact reconstruction, idempotence and cold/trial checks.

On selected originals, early search acquires 145 trials / 266 nodes and frontier
search 102 / 90; coverage remains 31/83. Frontier acquisition costs 1.75051 seconds
versus 3.76670, with fewer trials and separate 64--68-second seed verification.
Its new SQLite delta occupies 3,018,752 bytes versus 6,807,552. Repeated controls
add 10 / 12 trials and retain 88/96. These are negative coverage results, not a
solver speedup. The [study](frontier-pivots.md) records the preparation, graph
traversal, cold replay, storage and discovery limitations. Next: bounded coupled
continuations at retained divergent states, rather than an unmotivated larger
one-pivot sweep. No formal or manuscript theorem was changed.

All **531 tests** and the artifact validation pass. The two new original deltas
combine without conflicts, sharing 57 pattern rows / 29 trial rows. Their union
adds 299 unique pattern nodes / 218 trials; the complete original history now
retains 41,299 pattern nodes and 563 trials. The repeated-control union adds
25 nodes / 20 trials, reaching 24,982 nodes and 65 trials. The study's latest
resume recipe and validation digests preserve this work for the next iteration.

## 12 November: budget descendant acquisition and check coupled deviations

Implemented a separate coupled-trial table and exact two-projection checker/model
lift over retained divergent first routes. A new admission wrapper reserves each
missing recognizer state before discovery, including descendants and unfinished
ancestors. Completed children persist when the limit is reached. A zero-budget
restart can still reuse already stored results. Counts and new-node identities
are validated against each input's admission set. Candidate preparation, old
checking, per-state bytes and endpoint solving remain separately charged.

The frozen 32-state / eight-trial policy admits 25 coupled trials and 32 nodes on
original inputs, with no new closure; the repeated control admits 15 / 17, also
without gain. Neither hits its state limit. Detailed continuation analysis finds
only one genuinely new unresolved leaf across the original history; every other
new path ends in seed leaves. The 35-variable core's minimum permitted first-step
growth is three; its 662 permitted two-step orders all grow by at least seven.
The full source and pair audit are preserved. Thus a net-four temporary-growth
escape is ruled out there under the existing pair cap.

All **535 tests**, full cold replay, independent delta reconstruction, idempotence,
old-row preservation and exact old/coupled trial replay pass. The original history
now retains 41,331 pattern nodes, 563 one-pivot trials and 25 coupled trials; all
1,548 source bindings and 21,838 solver proof rows are unchanged. The repeated
history has 24,999 pattern nodes, 65 old trials and 15 coupled trials. The
[study](coupled-pivots.md) supplies the updated five-table resume recipe.

Next gaps are a controlled minimum-growth-three escape with ordinary simplification
and checked composition through saved open alternative routes. Existing composition
handles individually closed replacements; it does not recursively join all open
trial records. No new formal theorem or manuscript claim was introduced.

## 13 November: growth escape and finite alternative-route composition

Implemented and preserved the [growth-three escape](growth-escape.md). The sole
minimum-growth-three pivot (15) of the saved 35-variable core enables four new
failed-literal probing states under the unchanged recognizer. It closes the core
in 0.02275 resident seconds; the growth-two control admits no pivot. A warm retry
reuses its checked record without acquiring states. The sixth-table delta retains
four pattern nodes and one explicit-growth trial while preserving all old rows.

Implemented least-fixed-point composition over checked old rules and saved
projection alternatives. The retained finite witness requires every component
and both conditioning branches, orders premises before conclusions and rejects
circular support. It improves selected-original coverage 31/83 -> 32/83, gaining
case 33 (`reuse_holdout3`, n48, original case 1193). Independent reference solving
confirms UNSAT and preserves all 212 endpoint proof nodes. The historical group
name does not make this repeatedly investigated source a fresh evaluation.

All 540 tests pass, including real serialized escape checking, cycle rejection,
incomplete-branch rejection, repeated canonical premises, budget interruption,
restart and six-table persistence. The suite still reports 20 existing SQLite
ResourceWarnings; the full logs remain available. Formal sources and paper are
unchanged. Current original history: 41,335 pattern nodes, 563 pivot trials,
25 coupled trials, one growth trial, 1,548 source bindings and 21,838 older solver
proof rows. Follow the six-table resume recipe in the linked study.

The next discovery gap is predicting which small projections unlock propagation
on other open cores. Avoid assuming that every minimum-growth move does so.
The next reuse gap is maintaining finite-route closure incrementally rather than
rescanning all reachable alternatives. Full-history cold verification remains a
larger measured cost than the local expansion or graph composition.

## 13 November: persistent continued probes replace the special growth route

The [probe-window study](probe-window.md) explains the earlier successful
projection's first effect: it promotes an already failed assumption into the
four-variable probe window by removing two binary clauses. Source and projected
single-assumption traces are complete and independently checked. This narrows
the cause on that core without claiming elimination never strengthens propagation.

Implemented source-bound continued probe windows with exact residual bindings,
inconclusive-result persistence and pending-target restart. The unchanged
recognizer supplies target plans, preserving all earlier identities. Finite
composition accepts only present, verified targets. Four-source and 32-state
budgets bound each input's admission scope; neither binds in the measured run.

Coverage improves 32/83 -> 36/83 (three SAT gains, one UNSAT, all 48 variables).
The same 36 remain covered with the earlier growth-exception route removed.
Seventy windows (52 clear / 18 forced), 475 assumption attempts and 81 nodes are
preserved. Resident search/check/persist/compose is 0.84607 seconds, while the
complete preparation/acquisition/validation pipeline costs 252.05 seconds and
working storage grows 2,142,208 bytes. No speedup or peak-RAM reduction is claimed.

All 543 tests and independent seven-table/cold/reference checks pass. The suite
retains 20 existing SQLite resource warnings. Old histories and failures remain
unchanged; the latest graph has 41,416 pattern nodes and 70 window records in
addition to all previous trial tables. The separate reference archive adds
409 checked solver nodes. Formal sources and paper remain unchanged.

The next concrete gap is advancing a window without repeating its known prefix:
51 of 52 clear windows still have later ranked binary candidates. The current
source/width key reuses a result but does not advance automatically. A new
continuation identity and prefix-reuse rule are needed before the next bounded
block can be acquired efficiently. Combining compatible forced consequences
before repeated recognition is another hypothesis to test on the open residuals.


## 13 November: shared checked prefixes advance the discovery cursor

The [prefix-continuation study](probe-continuation.md) adds source-bound blocks
whose offsets require complete checked clear predecessors. Negative attempts are
referenced without rediscovery; forced blocks resume exact residuals. Missing or
foreign prefixes, skipped candidates and unsupported exhaustion are rejected.
All previous recognizer identities, failed trials and solver results persist.

Coverage rises **36/83 -> 39/83**: one SAT and two UNSAT 48-variable development
originals, independently checked. All 39 remain covered without growth-exception
routes. The run retains 51 continuation blocks (43 clear / eight forced), five
initial windows and 45 nodes. It performs 409 new assumption attempts while
reusing 408 previous ones. No budget binds: at most 13 new states / three sources.

Matched warm ranking/discovery/checking uses 373 versus 781 attempts and median
0.13230 versus 0.27631 seconds (2.09x substep speedup). This excludes already-paid
prefix verification, persistence and target recognition in both modes. Resident
expansion costs 0.56578 seconds, whereas preparation, full cold audit and separate
route replay cost 64.41, 110.39 and 63.13 seconds. Working storage grows 1,359,872
bytes. There is no end-to-end solver speedup, peak-RAM or new full-corpus claim.

All 547 tests and eight-table cold reconstruction/reference checks pass. The
saved suite log retains 20 existing SQLite warnings. The complete history now
has 41,461 pattern nodes, 75 windows and 51 continuation blocks, plus all previous
trial/source/proof tables. The separate reference archive retains 513 nodes.
Formal sources and manuscript are unchanged; earlier full coverage stays 902/985.

Next: 42 clear streams retain 2--20 eligible candidates, and four forced targets
remain open after finite composition. Continue these saved streams before raising
caps, inspect the unresolved targets, and profile cold proof replay for the largest
runtime opportunity. Candidate availability and complete cursor bookkeeping do
not establish efficient coverage of arbitrary CNF.


## 13 November: resumed prefixes close six originals and certify a probing limit

The [resumption study](probe-resumption.md) restores the complete verified
checkpoint lineage and keeps the four-source/32-state policy. Coverage increases
39/83 -> 45/83: four SAT and two UNSAT gains, independently checked on six reused
48-variable development sources. All 45 remain covered without growth-exception
routes. Forty-six new blocks (39 clear / seven forced), 327 attempts and 74 nodes
persist; 758 saved-prefix attempt references avoid repeating prior discovery.
Case 46 closes after using all 32 admissions. No input is interrupted.

Resident search/check/persist/compose costs 0.53596 seconds, preparation 65.21,
full cold inventory 108.60 and separate route replay 63.07. Storage grows
1,581,056 bytes. These are additional discovery costs, not a whole-solver speedup.
The current history has 41,535 pattern nodes, 75 windows and 97 continuation
blocks, with all previous trials, source bindings and solver proofs retained.
The separate reference archive adds 1,238 checked proof nodes.

The open selected paths expose 41 clear streams across 38 originals. Thirty-six
streams retain 1--16 candidates; five exhaust the binary ranking. A separate
source-bound diagnostic proves that these five have no single-assumption unit
refutation: 104 checked attempts cover all 52 binary-variable instances, and
79 remaining instances cannot create an initial unit under either value. This
excludes that inference rule, not satisfiability or stronger structural reasoning.
The 11-variable encoding-cap source has minimum width five: at most three assigned
variables leave clause width at least two. The other four sources have width two.

The useful next reuse gap is extracting common consequences, equivalences and
binary implications from all saved trace pairs. The old bounded initial profile
did not consume the later window traces. If those facts are insufficient, target
bounded nested reasoning on the width-two sources and a different structural or
adequately deep approach on the width-five source. Continue the remaining streams
as a coverage control, with cold dependency checking still the largest runtime
cost and peak RAM/independent evaluation still open.

All 557 tests pass. The acquisition artifact separately preserves 552-test and
cold-reconstruction/reference evidence. Two diagnostic status-assumption failures
are retained: learning_clear separates original-source attempts from a nested
augmented-source continuation. The final diagnostic directly checks the original
traces and excludes the nested ones. Its successful run costs 5.35440 seconds
including restoration, with 0.02974 seconds for the required source checks; the
aborted preliminary replay times were not retained. Manuscript and Lean sources
are unchanged, and the earlier full prepared result remains 902/985.

## Saved source traces reused as exact rewrites, 13 November 2026

`cnf_trace_reuse.py` adds checked common/equivalence rewrites referencing existing
source-bound traces. Both polarities are replayed, augmented-source continuations
are excluded, every clause is substituted, exact child bindings and model lift
are checked, and absent targets cannot close plans. The full frontier scan finds
one equivalence and no common values among 1,240 attempts on 41 sources.
Coverage stays 45/83 after five additional pattern nodes; 42 new probes belong to
target recognition, not derivation of the saved-pair equivalence. All 561 tests,
byte-preserving reconstruction and independent reference checks pass.

The complete study, negative results, cost ledger and next implication-graph
experiment are in [saved-trace-reuse.md](saved-trace-reuse.md). Restore the new
checkpoint with `compare_cnf_trace_reuse.restore_checkpoint` and retain its
external records in `TraceRoutes`; the parent runner alone omits this route.
The eight-table history now has 41,540 pattern nodes; no earlier rows are changed.

## Checked composition of saved implications, 13 November 2026

`cnf_trace_learning.py` now combines source-bound conditional units into an
independently checked graph and bounded augmented-CNF lookahead. Exact graph
closures find no new forced values or equivalences beyond the prior pair rule.
The full CNF with retained implications exposes two stronger reductions, confirmed
by same-variable no-clause controls. All 39 learning trials, including 36 clear
ones, and their source dependencies remain persistent. Fifteen new nodes leave
three open selected leaves (27, 39 and 35 variables); coverage remains 45/83.

All 566 tests and independent graph/clause/control/coverage/reference replay pass.
The history contains 41,555 pattern nodes with all older rows unchanged. Resume
with `compare_cnf_trace_learning.restore_checkpoint` and both external record
lists in `LearnedTraceRoutes`. The read-only target inspector persists exact
keys and candidate counts; start with the 27-variable leaf. Full measurements,
negative results, memory limits and remaining obligations are in
[saved-implication-learning.md](saved-implication-learning.md).

## Bounded continuation below learned targets, 13 November 2026

`cnf_target_probe.py` advances through saved clear prefixes and forced targets
under one shared admission budget per selected learned target. Three regression
tests cover step/source limits, budget reset scope and pending-target restart
without repeated discovery. The resumable driver preserves both external proof
layers and additive eight-table lineage; the standalone validator binds every
new block and independently checks all forced pairs and gained originals.

All 569 tests and cold checks pass. Coverage increases **45/83 -> 46/83**, with
case 58 independently proved UNSAT. Ten new states and 15 probe blocks reduce
case 32's remaining leaf to 23 variables; that leaf and the unchanged 39-variable
leaf exhaust their ranked probes. No target is pending. Resume from
`experiments/results/cnf-target-probe/report.json` with
`compare_cnf_target_probe.restore_checkpoint`, retaining both returned lists in
`LearnedTraceRoutes`. There are 41,565 pattern nodes, 79 windows and 108 continuation
blocks, with every old row unchanged.

The next useful expansion is stronger trace reuse or bounded conditioning on
the 23-variable source, not another unchanged ordinary-probe pass. Local work
costs 0.11697 seconds, but cold preparation/checking dominates the 256.68-second
pipeline; standalone validation adds 71.33 seconds. SQLite grows 327,680 bytes,
and peak RAM remains unmeasured. Complete costs, retained negative outcomes,
scheduling limits and the next priorities are in
[learned-target-continuation.md](learned-target-continuation.md). Manuscript and
Lean sources are unchanged; no unrestricted polynomial bound is established.

## Exact augmented-formula continuations, 13 November 2026

`cnf_learning_continuation.py` checks later four-variable blocks against a
source-justified learning base. Complete base digests share evidence without
copying it into each block; missing or changed bases, incomplete prefixes,
forged reasons and incorrect target bindings are rejected. Pending targets stay
uncovered. Reopened records reuse checked prefixes without new discovery, and
successful child models lift to the complete source. Four new regression tests
cover these obligations; all **573 tests** pass.

The measured study raises coverage **46/83 -> 47/83**, independently proves
case 32 SAT and retains the growth-exception ablation. It adds 17 pattern nodes,
two learning bases and nine augmented blocks. The 39-variable source remains
open with an exact augmented single-assumption obstruction; the most promising
next expansion is continuation of the 36 earlier clear learning bases.

Restore `experiments/results/cnf-frontier-learning/report.json` using
`compare_cnf_frontier_learning.restore_checkpoint`, then pass all three evidence
lists to `ContinuedLearningRoutes`. Older loaders omit the new route layer.
The history has **41,582 pattern nodes**, with all prior eight-table rows unchanged.
Cold verification, controls, finite composition and independent proofs pass;
no replay discovery or database-byte changes occur. Full costs, corrected test
fixture failure, limitations and next priorities are retained in
[frontier-learning-continuation.md](frontier-learning-continuation.md). Manuscript
and Lean sources are unchanged.

## Shared-budget continuation of retained learning, 13 November 2026

`cnf_learning_batch.py` filters retained bases and advances later blocks in
round-robin order. One shared set counts all newly entered recognition states;
a temporary per-target cap preserves completed and partially entered work.
The new generic runner resumes immutable checkpoint chains, persists each block
before target acquisition, keeps matched original controls and extends the
previous independent reference archive. Four regression tests cover shared caps,
partial acquisition, cached reuse, filtering, ordering and persistence-before-use;
all **577 tests** pass.

The [retained-learning batch](retained-learning-batch.md) raises coverage
**47/83 -> 52/83** with five independent SAT witnesses. It adds 141 blocks and
77 pattern nodes, preserving every old eight-table row and all 164 reference
proof rows. Six reduced targets have clear matched controls, while four controls
also force a value. There is no uniform learning-benefit or total-speedup claim.

Restore `experiments/results/cnf-learning-batch/report.json` with
`continue_cnf_learning.restore_checkpoint` and use `ContinuedLearningRoutes`.
The state contains 41,659 pattern nodes and 150 augmented blocks, alongside
unchanged ordinary windows, continuations and 41 learning bases. The next
smallest unresolved target is a ten-variable / 51-clause leaf with one remaining
ordinary probe; 18 augmented formulas retain 92 unused ranked variables. Cold
validation dominates the 263.21-second pipeline. Working SQLite adds 1,044,480
bytes, and separate artifacts retain successful and unsuccessful evidence.
Manuscript and Lean remain unchanged; this adds empirical coverage, not a theorem
covering arbitrary CNF efficiently.

## Exact splits from clear saved traces, 13 November 2026

`cnf_trace_split.py` reconstructs the two cofactors of one variable from clear
top-level source traces. References retain the source binding and unit reasons;
the checker rejects omitted polarities, forged transports and foreign sources.
Coverage requires both acquired cofactor plans, including multiplicity when both
branches share a canonical key. Model lifting restores the selected assumption
and units, then checks the whole source. Four new tests include all 1,024 source
assignments, all satisfying child models, partial acquisition and cold reuse;
all **581 tests** pass.

The [saved-cofactor study](saved-trace-splitting.md) raises coverage
**52/83 -> 53/83** with five new pattern nodes, one clear ordinary window and one
external split. Case 2 is independently SAT. The source's ordinary probe pool is
certified exhausted; its saved clear traces still enable an exact conditioning
plan. The local saved-trace timing is slightly slower than fresh propagation in
the single control, so no runtime speedup is claimed. Cold verification dominates
the 263.26-second pipeline. Working SQLite grows 65,536 bytes.

Restore `experiments/results/cnf-trace-split/report.json` with
`compare_cnf_trace_split.restore_checkpoint`; pass the inherited lists to
`ContinuedLearningRoutes`, then attach the returned split records. There are
41,664 pattern nodes, 80 windows, 108 ordinary continuations and 150 augmented
blocks. All 1,156 inherited reference proof rows survive in the 1,175-node archive.
The next structural test is capped cofactor acquisition on four remaining targets
(33, 33, 36 and 38 variables), compared with the 18 previously ready learned bases
after reapplying the coverage filter.
No new Lean theorem or unrestricted-SAT complexity bound is claimed.

## Matched saved-cofactor acquisition, 13 November 2026

The [isolated split/probe comparison](saved-cofactor-batch.md) freezes four open
leaves and their saved-pair rankings on the same 53/83 parent. With at most 32
state admissions per source, splitting reaches **55/83**, ordinary probing
**54/83**. Case 37 is independently UNSAT; case 77 is SAT. The split arm closes
three of four selected fragments with 30 states in 0.14475 s, plus 0.05791 s
ranking. The control uses seven states in 0.09725 s and reproduces case 37's
closure. Both arms' partial/inconclusive work is retained. This supports selective
conditioning, not a claim that it is always cheaper.

Their immutable union adds 36 distinct pattern nodes, four ordinary windows,
thirteen continuations and four external splits; working SQLite grows 720,896
bytes. No state cap binds. All 585 tests and the full inventory audit pass;
independent cold arm/union replay disables discovery. All 1,175 earlier reference
proof nodes survive in the 1,721-node archive. The comparison pipeline takes
405.18 s, dominated by repeated cold preparation and verification.

The next selected frontier is **27 variables / 101 clauses**, below the true
cofactor of the remaining 33-variable parent. Its sibling is closed. Inspect
`diagnostics.json.gz` → `children`; the old target view does not follow open
external splits. Eighteen ready learned bases retain 92 ranked variables as an
alternative queue. Restore `experiments/results/cnf-split-batch/report.json`
through `compare_cnf_split_batch.restore_checkpoint` and `routes_for`, retaining
all five split records. The earlier loader alone loses this progress. Manuscript
and Lean are unchanged: finite checked coverage does not establish efficient
closure or polynomial construction for unrestricted SAT.

## Continuation below saved splits, 13 November 2026

[The split-frontier continuation](retained-split-frontier.md) replaces the old
33-variable scheduling view with its exact acquired 27-variable descendant,
then reduces that leaf to **22 variables / 90 clauses**. It adds six recognition
states, two windows and five continuations; **six blocks are clear, one forced**.
Coverage remains **55/83**, including the ablation. Navigation costs 0.00688 s and
bounded continuation 0.06866 s; working SQLite grows 176,128 bytes. All 589 tests
pass. The full inventory audit and cold replay preserve prior evidence; all 1,721
earlier reference nodes remain within the 1,750-node extended archive.

The remaining formula has a checked single-assumption unit-refutation obstruction:
38 saved clear traces cover both values of all 19 binary-clause variables; the
other three cannot create an initial unit. No retained pair yields the implemented
common-value/equivalence rewrite. These facts do not decide SAT/UNSAT or rule out
stronger inference. Next compare another source-proved learned batch against
nested cofactor splits, with the 18 ready bases / 92-variable queue as an
alternative. Do not restart ordinary probes on the unchanged exhausted source.

Resume `experiments/results/cnf-split-frontier/report.json` through
`continue_cnf_split_frontier.restore_checkpoint` and `routes_for`, including all
five splits. `diagnostics.json.gz` and `obstruction.json` preserve the exact
22-variable source and its remaining obligations. The frontier follows saved
splits, selected internal plans and ordinary forced routes; it is not a minimal
or exhaustive analysis of every alternative proof plan. Manuscript and Lean
remain unchanged; unrestricted efficient construction and compact closure remain
open.

## Learning versus saved conditioning, 13 November 2026

[The matched learning/split trial](learning-versus-saved-split.md) starts from
the exhausted 22-variable / 90-clause source. A new 16-clause batch has a clear
initial block and five clear later blocks, then exhausts the augmented candidate
pool without a reduction. The complete graph of saved source implications also
provides no forced value, equivalence or contradiction. These are retained
negative results for this precise inference, not barriers to arbitrary methods.

One split ranked from eight saved pairs needs four new recognition states and
reuses its already closed sibling. The selected remaining leaf becomes
**19 variables / 84 clauses**, but original coverage remains **55/83**, including
the ablation. Both cofactors are acquired. Local acquisition is 0.03825 s for
learning and 0.03446 s for splitting, with another 0.02471 s for pair ranking.
The 32-state allowances do not equalize CPU work. Cold preparation, full audit
and preservation scans dominate the 434.32-second pipeline.

The union adds 57,344 working SQLite bytes to 769,617,920 bytes, with 41,710
pattern nodes; all inherited rows remain unchanged. The reference archive
preserves all 1,750 old nodes within 1,775 checked nodes. Source, augmented formula
and both cofactors are independently SAT; reference answers are separate from
structural coverage. The failed first export and all completed proof archives
are preserved. Peak RAM and unrestricted compact closure remain unproved.

Resume `experiments/results/cnf-learning-split/report.json` through
`compare_cnf_learning_split.restore_checkpoint` and
`compare_cnf_split_batch.routes_for`, retaining all **six splits, 42 learned
bases and 155 augmented blocks**. `diagnostics.json.gz` -> `frontier` identifies
the 19-variable leaf and its ten untried ordinary candidates. The 18-base /
92-variable learned queue remains an alternative. Do not repeat the exhausted
source/batch. Dependency-local verification and delta export are high-cost
implementation gaps. Manuscript and Lean are unchanged.

Validation: all **589 tests** pass (88.787 s); full inventory audit and independent
cold replay pass. Cold replay takes 297.82 s with discovery disabled and history
bytes unchanged. On the 106-clause augmented formula, 42 saved clear traces cover
both values of 21 binary variables; variable 12 cannot trigger an initial unit.
This certifies failure of every single-variable unit-refutation attempt after
the new batch, without deciding a broader complexity question.

## Portable probing obstruction, 13 November 2026

[Continuation from the merged checkpoint](retained-split-frontier.md) tests all
ten remaining ordinary candidates on the 19-variable / 84-clause leaf. Three
clear blocks, then exhaustion, add no recognition states and no original closure:
coverage remains **55/83**, including the ablation. Twenty-eight saved clear
traces cover both values of all fourteen binary variables; the other five cannot
start unit propagation. No retained pair supplies the implemented common-value
or equivalence rewrite. This is a checked inference boundary, not SAT/UNSAT or a
lower bound for arbitrary methods.

A new self-contained certificate retains only the exact formula and the required
clear traces. It occupies **6,562 JSON bytes / 1,347 compressed bytes**. Two fresh
processes per mode, with reversed order, check identical proofs in **0.08218 /
0.12492 s** from the compact certificate versus **14.10469 / 14.20055 s** from
history reconstruction. Startup and teardown are included; OS caches are not
flushed. Packing/checking costs 0.00288 s once traces are available; the exporting
diagnostic also pays 14.03 s to restore history. These costs and all old evidence
remain charged. Compact replay verifies only this source's unit-refutation
obstruction, not whole-inventory correctness, ancestry or structural coverage.

The continuation itself costs 0.00870 s; its pipeline totals 271.54 s, including
a 113.33 s inventory audit and 64.40 s cold route reconstruction. The working
database grows 28,672 bytes to **769,646,592 bytes** with 41,710 pattern nodes,
87 windows and 128 ordinary continuations. The reference archive's 1,775 nodes
and bytes are unchanged. All 17 relevant tests, full inventory audit and
154.19 s independent cold replay pass. The parent's 589-test suite remains
preserved; no new full-suite run is claimed. Peak RAM is unmeasured.

Resume `experiments/results/cnf-reuse-frontier/report.json` through
`continue_cnf_reuse_frontier.restore_checkpoint` and `routes_for`, including six
splits, 42 learned bases and 155 augmented blocks. Stop unchanged ordinary probes
on this leaf. Compare source-proved augmentation, verified parent-lemma transport
and another split from its fourteen saved pairs. Elimination and binary-path
steps require explicit transport conditions; a parent's negative certificate
cannot simply be reused on a child. The 18-base / 92-variable queue remains an
alternative. Dependency-local positive-plan validation is the larger cost gap.
The manuscript now explains compact negative-fact replay and its limitations;
Lean sources and unrestricted-SAT claims are unchanged.

## 2026-11-13: checked parent-lemma transport and retained negative comparison

The new `cnf_lemma_transport.py` checks source-bound positive consequences through
conditioning, complete elimination, binary-path deletion and renaming. It rejects
unsupported equisatisfiable rewrites and never drops just an eliminated literal
from a clause. [The experiment](parent-lemma-transport.md) transports eight parent
lemmas to the 19-variable leaf, seven not explicit there. All seven are also
derivable from saved leaf traces, whose local batch provides eleven clauses.
Neither exact augmentation reduces support; both have newly checked all-binary-
variable exhaustion evidence. Original coverage stays 55/83.

No working-history or reference bytes change. Six splits, 42 learned bases and
155 blocks remain in the 769,646,592-byte archive. The new positive and negative
facts are persistent sidecars under `experiments/results/cnf-lemma-transport/`,
not successful routes or a replacement inventory checkpoint. Positive transport
occupies 2,362 compressed bytes; the already acquired local alternative needs
749. Export costs 14.05 s. Compact fact replay is 0.111--0.162 s, while replay plus
inventory reconstruction/ancestry is 13.85--14.43 s. Their ancestry obligations
differ; neither timing is an unrestricted solver claim. Thirty-seven relevant
tests and two independent read-only cold ancestry checks pass; no new full-suite
or Lean-refinement result is claimed.

Next, use the saved 19-variable cofactor pairs to change the remaining structure,
or compare a separately budgeted second learning round on the augmented traces.
Do not repeat the two preserved batches or interpret their failure as complete
clause saturation. Full dependency-local coverage checking remains distinct from
the positive-fact replay implemented here. Resume the inventory with
`continue_cnf_reuse_frontier.restore_checkpoint`, retaining all older evidence.

## 2026-11-13: saved cofactor closure, 56/83 coverage, and a new scheduling boundary

`continue_cnf_saved_splits.py` ranks all fourteen available pairs on the exhausted
19-variable leaf and acquires the variable-15 cofactors with one shared 32-state
allowance. Eighteen new states close both branches and development case 71
(48 variables / 204 clauses). Coverage increases **55/83 -> 56/83**, also without
growth exceptions. All seven saved split sources and eleven acquired learned
targets are closed. No original-level result is inferred merely from smaller
support: the coverage plan and independent reference/model lifts are checked.

[The retained report](saved-cofactor-closure.md) charges 0.04395 s ranking,
0.05914 s acquisition and 271.74 s for the full pipeline, including the 110.36 s
inventory audit. SQLite adds 200,704 bytes to 769,847,296 bytes and 41,728 pattern
nodes; the immutable compressed delta is 9,471 bytes. All old solver rows and all
1,775 reference nodes are preserved (1,869 reference nodes now). Fourteen core
tests and 163.74 s independent cold reconstruction pass, including exact ranking,
both branch obligations, baseline monotonicity, growth ablation and no new discovery.
No new full-suite run or Lean refinement is claimed.

The scheduler must now leave the completed split frontier. The saved
`open-originals.json.gz` contains 27 open originals and 29 distinct selected leaves,
each in one original. The eighteen ready bases retain 92 candidates. Prioritize
the 20-variable / 80-clause exhausted leaf of case 73 for saved conditioning, with
the four remaining augmented candidates of case 30's 29-variable / 120-clause
leaf as an alternative. The 11-variable encoding-cap example needs a different
structural treatment or deeper conditioning; its width-five shallow obstruction
was already recorded. These mappings concern selected routes, not all alternatives.
Resume `experiments/results/cnf-saved-splits/report.json` through
`continue_cnf_saved_splits.restore_checkpoint`, retaining all seven splits,
42 learned bases, 155 augmented blocks and the parent-lemma sidecars. Dependency-
local verification of a complete positive plan remains distinct from compact
fact replay and is still the largest measured runtime gap.

A final read-only affine extraction check identifies a promising next family:
case 0's encoding-cap residual consists of two consistent parity equations and
one wide coupling clause. `encoding-cap-affine.json` preserves the exact source,
extraction and checked summary. A particular solution/nullspace basis can check
literal compatibility and construct a model for the single clause, or establish
that all its literals are forced false, without expanding the affine boundary to
CNF. Implement this recognized family with independent checks and resource
accounting next; it is not integrated or counted in this checkpoint. Arbitrarily
many leftover clauses remain outside this restricted linear-algebra argument.


## 2026-11-13: affine/one-clause family and the remaining non-affine frontier

The [checked affine/one-clause rule](affine-one-clause.md) raises structural
coverage **56/83 -> 57/83**, also without growth exceptions. It reuses triangular
rows to construct a particular solution and complete nullspace basis, checks the
full source partition and every vector, and either supplies a full CNF model or
proves that the sole remaining clause is forced false. More than one leftover
clause is outside this rule, not an UNSAT result. No new Lean refinement or
unrestricted-SAT bound is claimed.

All 29 selected open leaves were checked. The sole gain is case 0's encoding-cap
residual (11 variables / 49 clauses), closing its 14-variable / 132-clause original.
All **28 remaining selected leaves have zero directly extracted parity equations**.
This excludes a direct opportunity for the same rule on their current encodings,
not hidden affine structure. The next discovery target is the 20-variable /
80-clause exhausted leaf of case 73, compared with the four unfinished learned
candidates on case 30's 29-variable / 120-clause leaf. Do not repeat the unchanged
affine scan or the completed earlier split scheduler.

The selected-leaf pass costs 0.00599 s; the full pipeline costs 82.32152 s,
including 14.80944 s restoration and 64.60772 s preparation. The new family proof
is 1,056 compressed bytes; historical SQLite stays byte-identical at 769,847,296
bytes / 41,728 pattern nodes. All 1,869 reference nodes are preserved within 1,883.
Matched generated cases show 1.11--1.24x local exact-source reuse speedups, with
normalization and checks charged; a full nullspace representation can still use
quadratic bits. Complete positive-plan checking from actual dependencies remains
the largest measured runtime opportunity.

Twenty-one targeted tests and independent cold selection/coverage/reference
replay validate this step. The new cold check covers reachable inventory
obligations, not a new full scan of unrelated unchanged rows; the parent audit is
retained. Two diagnostic JSON key-comparison failures and their correction are
preserved. The old full-suite and 902/985 corpus results are unchanged.

Resume `experiments/results/cnf-affine-clause/report.json` through
`continue_cnf_affine_clause.restore_checkpoint` **and its `routes_for`**, preserving
all **five evidence lists**: rewrites, 42 learned bases, 155 augmented blocks,
seven splits and the new affine family record. Earlier lemma sidecars remain
separate and preserved. Using an older four-list route loader would lose the
newly checked closure.


## 2026-11-13: resume an original through its retained cofactor pair

The [original-frontier split](original-frontier-split.md) selects case 73's
20-variable / 80-clause / 285-literal leaf using support/literal order, ranks all
fourteen saved pairs and chooses variable 18. Ten new recognition states close
the true branch and reduce the false branch to **13 variables / 62 clauses /
219 literals** through binary-path deletion and five eliminations. Independent
reference proofs establish SAT of the source and both cofactors and verify
model lifting. Structural coverage stays **57/83**, also without growth exceptions;
the remaining leaf still needs a recognized decomposition.

That leaf has no directly extracted parity equation. Its already saved probes
cover variables **6, 9, 12 and 13**, while ordinary candidates **1, 4, 7 and 8**
remain untried. Test this single four-variable block before another conditioning
layer. Preserve a clear outcome if obtained, then compare newly available pairs
or source-proved augmentation. The older 18-base / 92-variable learned queue
remains available. Use the external split frontier to avoid restarting the
exhausted 20-variable parent; selected original routes expose a different view.

Local acquisition costs 0.04525 s, but the full pipeline costs 267.75550 s,
including 65.86672 s preparation, 107.92519 s full audit and 63.93178 s cold routes.
The two-trace matched control is one tiny resident sample and establishes no
robust timing advantage. SQLite adds 126,976 bytes to **769,974,272 bytes /
41,738 pattern nodes**. The immutable delta is 8,671 compressed bytes; sidecars
are additional. All earlier rows and 1,883 reference nodes remain preserved
(1,898 reference nodes now). A smaller live residual does not shrink the archive
or establish a polynomial expansion bound.

Twenty-seven targeted tests, full inventory audit and **164.80960 s** independent
cold replay pass, including source selection, both branch obligations, all five
evidence lists, baseline monotonicity, growth ablation, model lifting, immutable
preservation and no new discovery. The old full-suite and Lean results are
unchanged. The manuscript records this local structural progress and its costs.

Resume `experiments/results/cnf-original-split/report.json` through
`continue_cnf_original_splits.restore_checkpoint` and `routes_for`, keeping all
**five evidence lists**: rewrites, 42 learned bases, 155 augmented blocks,
**eight splits and one affine family record**. Earlier lemma sidecars remain
separate and intact. `frontier-profiles.json.gz` records the precise smaller
source and next variables; `open-originals.json.gz` retains the original/queue
mapping. Dependency-local verification of complete positive plans remains the
largest measured runtime opportunity alongside discovery of smaller residuals.

## 2026-11-13: forced continuation reduces the open split leaf to ten variables

The [probe continuation](original-frontier-probe.md) follows case 73's saved
split and tests the next four-variable candidate block on its 13-variable leaf.
The first attempt refutes variable 1 = false. Restricting the forced opposite
literal, two eliminations and binary-path deletion leave **10 variables /
44 clauses / 151 literals**, down from 13 / 62 / 219. Four new recognition states
suffice. Coverage stays **57/83**, also without growth exceptions; one acquired
structural leaf remains open and no child is pending.

That leaf has zero directly extracted parity equations and saved ordinary pairs
for **10, 3, 5 and 6**. The next ordinary candidate is **7**. Test it before another
split; if clear, retain the result and rank the saved cofactor pairs. Variables
are local to each normalized residual. Do not repeat the obsolete source's
remaining probes or use the original-frontier view to restart its larger parent.
The 18-base / 92-variable alternative learning queue remains retained.

Local acquisition costs **0.02000 s**, but the pipeline costs **282.11723 s**:
preparation 69.25253 s, full audit 115.65564 s and cold routes 65.40336 s dominate.
SQLite grows **57,344 bytes** to **770,031,616 bytes / 41,742 pattern nodes**;
the delta is **6,225 compressed bytes** plus sidecars. All old rows and 1,898
reference nodes remain preserved (1,906 reference nodes now). No global runtime
speedup, peak-RAM reduction, holdout gain or arbitrary-SAT bound is established.
Dependency-local verification of complete positive plans remains the largest
measured runtime opportunity.

Resume `experiments/results/cnf-original-probe/report.json` through
`continue_cnf_original_probes.restore_checkpoint` and `routes_for`, keeping all
**five evidence lists**: one rewrite, 42 learned bases, 155 augmented blocks,
eight splits and one affine family record, plus earlier lemma sidecars.
Twenty-nine targeted tests, the full inventory audit and **164.19006 s**
independent cold replay pass, with zero new discovery and unchanged reconstructed
bytes. Details are recorded in this checkpoint's `validation.json`.
The preliminary probe and corrected validator import failure are both retained.

## 2026-11-13: a completed probe pool and saved split close case 73

The [probe-and-split continuation](exhausted-probe-split.md) raises coverage
**57/83 -> 58/83**, also without growth-exception routes. The last ordinary
variable 7 is clear in both polarities. Ten saved traces cover all five binary
variables; the other five cannot start unit propagation. The source-bound
exhaustion certificate is not a SAT verdict. Ranking all five pairs selects
variable 10, with score **[1, 1, 9, 96, 10]**: its true branch reuses the empty-CNF
terminal, and seven new states close its nine-variable false branch through
probing, two eliminations, two binary-path reductions and a polarity change to
Horn form. Both plans complete the 48-variable / 204-clause original case 73.

All **nine saved splits** now have closed sources, with no open descendant or
pending child. The selected original queue retains **27 leaves across 25
originals**. Its smallest is **case 30, 29 variables / 120 clauses / 362 literals**,
with ordinary candidates **7, 10, 16, 18, 20, 21, 23, 28, 29** still available.
Compare the first four with the saved pair ranks and learned-clause route.
The selected pair in this run was already available before the new probe;
exhaustion is not a prerequisite for a split. The empty branch already witnesses
SAT, whereas acquiring both branches serves complete structural coverage. The alternative queue retains 18 bases / 92 candidates, including the
previous four augmented candidates on case 30. Use the original-input frontier
now; the current experiment intentionally requires an open split descendant.

Ordinary acquisition costs **0.00181 s**, exhaustion checking **0.00620 s**, pair
selection **0.04998 s** and cofactor acquisition **0.01667 s**. The full pipeline
costs **270.70538 s**, including 66.55717 s preparation, 108.42947 s full audit
and 64.45513 s cold routes. Saved two-trace replay is slower in the tiny matched
sample (0.000430 versus 0.000349 s fresh); no robust runtime comparison follows.
SQLite grows **90,112 bytes** to **770,121,728 bytes / 41,749 nodes**. The delta
is **5,411 compressed bytes**, plus sidecars. All prior rows and 1,906 reference
nodes survive (1,940 reference nodes now). Reference proofs independently establish
SAT and check model lifts. No new general tractability or minimum-cost claim is made.

Resume `experiments/results/cnf-probe-split/report.json` through
`continue_cnf_probe_split.restore_checkpoint` and `routes_for`, retaining all
five evidence lists: one rewrite, 42 learned bases, 155 augmented blocks,
**nine splits and one affine family record**, plus earlier lemma sidecars.
Thirty-eight targeted tests, the full inventory audit and **167.82586 s**
independent cold validation pass. Cold validation stages only the checked clear
window before replaying the original selection, then checks the complete child
checkpoint without fresh discovery;
its results and next-source mapping are retained in this checkpoint. Complete-plan
verification from actual dependencies remains the largest measured runtime gap.

## 2026-11-13: compare bounded lookahead before expanding another original

[The frontier-option comparison](frontier-option-comparison.md) retains a clear
ordinary continuation on case 30's 29-variable residual and exhausts its existing
augmented base with one further clear block. These results do not decide SAT or
exclude stronger inference. All twenty saved pairs are ranked before acquiring
children. Variable 24 was already preferred among the original sixteen pairs:
its false branch is the shared empty terminal; three new states reduce the true
branch from 28 variables / 114 clauses to **27 / 111**, via elimination and
binary-path deletion. Coverage remains **58/83**, including the growth ablation.
The empty branch witnesses SAT for the residual, separately from complete-plan
coverage. Literal count briefly grows during elimination.

Resume `experiments/results/cnf-frontier-comparison/report.json` with
`continue_cnf_frontier_comparison.restore_checkpoint` and `routes_for`, keeping
all five lists: 1 rewrite, 42 bases, **156 augmented blocks**, **10 splits**, 1
affine family, plus earlier sidecars. All prior rows and 1,940 reference nodes
survive (1,949 now). Forty-one targeted tests and the full audit pass; the cold
validator separately checks ranking using only staged clear evidence, then
checks the acquired delta, composition and reference models without discovery.
Independent cold replay passes in **176.26154 s**; its result is retained in
`validation.json`.

Acquisition takes **0.02748 s**; the pipeline takes **270.71536 s** and preflights
add **82.05829 s**. Independent validation is extra. SQLite grows **57,344 bytes**
to **770,179,072 bytes / 41,752 nodes**, with a **5,746-byte compressed delta**,
a 307-byte compressed learned block and other sidecars/reference data. Full
history preparation/checking dominates. The single matched trace sample is not
a robust or whole-solver runtime comparison; no peak-RAM or arbitrary-SAT bound
is established.

Next compare the new leaf's saved pairs **11, 5, 8, 15** with ordinary candidates
**19, 24, 9, 13**. Use the acquired split descendant, not the older source; its
exact key is in `frontier-profiles.json.gz`. It has 19 remaining ordinary
candidates and zero directly extracted affine rows. The wider queue now has
**17 ready learned bases / 88 candidates**. Do not repeat the exhausted older
learned base. Dependency-local complete-plan verification remains the principal
measured runtime gap.

## 2026-11-13: a failed literal avoids acquiring two new cofactor plans

[Forced continuation on case 30](frontier-forcing.md) reduces the open leaf from
**27 variables / 111 clauses / 342 literals** to **25 / 99 / 304**. The four saved
pairs all require two missing children. In the next ordinary block, variable 19
is clear and assuming normalized variable 24 false gives 21 unit reasons and a
contradiction. Its true restriction is acquired; binary-path deletion and one
elimination add three inventory states including the new unresolved terminal.
The proposed block stops before testing variables 9 or 13. Elimination increases
clauses and literals relative to its immediate input. Coverage stays **58/83**;
no new original or tractable family is closed, and a global minimum-cost claim
is not supported by comparing pair ranks alone.

The pipeline takes **277.21655 s**, including **0.02582 s** acquisition, 67.09237 s
preparation, 108.74312 s full audit and 67.28829 s cold routes. The direct preview
adds 0.00116 s of kernel work. SQLite grows **57,344 bytes** to **770,236,416 bytes /
41,755 nodes**; the compressed delta is **6,081 bytes**, with other artifacts
additional. All previous rows and 1,949 reference nodes survive (1,977 now).
The targeted 33-test suite, full audit and **174.55350 s** independent cold replay
validate the checkpoint; `validation.json` retains the separate replay checks.

Resume `experiments/results/cnf-frontier-forcing/report.json` through
`continue_cnf_frontier_forcing.restore_checkpoint` and `routes_for`, retaining
all five evidence lists (**1, 42, 156, 10, 1**) and earlier lemma sidecars. Use the
new split-frontier leaf, not its successful forced parent. Compare saved pairs
**5, 6, 8, 11** with the next ordinary block **13, 15, 7, 9**. There are 17 ordinary
candidates left at the new source, zero directly extracted affine equations,
and 17 ready learned bases / 88 candidates elsewhere. The next experiment should
batch bounded local continuation under one shared state allowance and compare
its evidence with the corresponding sequential prefix; a full reconstruction
and audit per window dominates local discovery. Dependency-local complete-plan
checking, measured batch savings and unrestricted resource guarantees remain open.


## 2026-11-13: batch ordinary continuation with a matched preparation control

[The bounded batch](frontier-batching.md) retains five clear probe blocks across
17 remaining ordinary candidates of case 30's 25-variable / 99-clause leaf.
A sixth advance detects exhaustion; no recognition state is admitted. All six
prefixes, final logical tables and coverage agree with a control that rebuilds
checked routes between advances while preserving the inventory cache, search
queue and common 32-state allowance. Coverage remains **58/83** and 21 saved
pairs can now support subsequent conditioning or common-consequence reuse.

Instrumented search is **0.31960 s** versus **5.46878 s**, including six snapshots
in each arm. Five avoidable route preparations cost **5.14561 s**. Initial
preparation is **65.62419 / 70.54924 s**; its single-run variation is not a batching
benefit. The pipeline, including both arms, takes **358.12190 s**. Full audit
(**111.99494 s**) and cold routes (**66.03018 s**) remain dominant. This is a
measured preparation saving on reused development data, not a general SAT-solver
speedup or an efficient complete partition.

SQLite grows **53,248 bytes** to **770,289,664 bytes** without adding pattern nodes
(41,755 total); one window and four continuation rows yield a **2,990-byte**
compressed delta. All previous results and the 1,977-node reference snapshot
survive. The targeted 37-test suite, full audit and independent replay validate
this checkpoint; detailed results and limitations are in the linked note.

Resume `experiments/results/cnf-frontier-batch/report.json` using
`continue_cnf_frontier_batch.restore_checkpoint` and `routes_for`; all five lists
(**1, 42, 156, 10, 1**) and earlier sidecars remain required. Use the retained
pair/rewrite diagnostics for the next expansion, rather than rerunning this
exhausted ordinary pool. The alternative learning queue has 17 bases / 88
candidates. Dependency-local complete-plan verification remains the major cost
gap, while finding a smaller certified decomposition remains the coverage gap.

The checked next-option ranking selects **variable 7**: its true cofactor is the
shared empty terminal, and its false cofactor (**24 variables / 94 clauses /
287 literals**) needs acquisition. This pair was available in the first new
window; requiring pool exhaustion would do avoidable discovery. No common-value
or equivalence rewrite is found among the 21 pairs. The four nonbinary variables
(2, 4, 12, 21) have unit-free restrictions, so single-assumption unit propagation
cannot start on them. Independent replay passes in **169.35837 s**. The retained
positive witness has **593 explicit steps**; measure its full dependency closure
before claiming a selective verification bound.


## 2026-11-13: acquire the missing branch of a retained pair

[The reused variable-7 split](reused-branch-expansion.md) shares the existing
empty true cofactor and acquires the false cofactor with three new recognition
states. Binary-path deletion and elimination reduce case 30's open leaf from
**25 variables / 99 clauses / 304 literals** to **23 / 93 / 288**. The intermediate
24-variable formula has 92 clauses and 281 literals, so elimination's support
reduction increases both other measures. Coverage remains **58/83**, also without
growth exceptions; no child is pending. Both cofactors are independently SAT,
with checked model transport. The unclosed structural plan is not an unknown
SAT verdict or a new tractability theorem.

Acquisition takes **0.02474 s** in a **271.17740 s** pipeline. Preparation costs
65.75065 s, full audit 106.37684 s and cold routes 63.97337 s. Reusing the chosen
pair avoids reacquiring its two propagation traces, but new child recognition
still reports 36 probe attempts. SQLite adds **49,152 bytes** to **770,338,816
bytes / 41,758 nodes**; immutable delta **4,841 compressed bytes**, with split and
other sidecars additional. All previous rows and 1,977 reference nodes survive;
the reference now has 1,998 nodes. The 37-test suite, full audit and independent
cold replay validate preservation and correctness.

Resume `experiments/results/cnf-reused-branch/report.json` with
`continue_cnf_reused_branch.restore_checkpoint` and `routes_for`, keeping all five
lists **(1, 42, 156, 11, 1)** and earlier sidecars. Compare the new leaf's saved
pairs with ordinary candidates **7, 9, 16, 17** before choosing the next bounded
step. Follow retained external splits; do not restart the exhausted parent.
Dependency-local checking of complete positive plans remains the dominant cost
opportunity; the retained 593-step witness still has unmeasured inherited
checking dependencies.

Cold replay passes in **171.36780 s**. The new leaf has saved pairs **5, 6, 11,
13**, each requiring two missing children; the best rank is **[2, 2, 20, 376, 5]**.
There is no common-value/equivalence rewrite among them and no directly extracted
affine equation. The wider queue retains **17 learned bases / 88 candidates**.
The exact source SHA-256 is
`a38c8326bbc493edae23be08aa73a85b288d74cf5a80dde578d126891e21ae92`.


## 2026-11-14: replay only the external dependencies of a positive proof

[Selected-route verification](selected-route-verification.md) replays the same
593-step certificate for 58/83 roots with the existing validators, loading only
selected external records and their required prefixes. In two cold repetitions
with reversed order, mean replay falls **35.72304 -> 30.35446 seconds (15.03%)**.
Both arms start with fresh verifier caches and check the same positive claim.
The comparator reconstructs all external routes; it is not a full archive audit
or the previous complete expansion pipeline.

Corrected to include the retained-policy verifier cache, the checking closure
falls **13,211 -> 11,955 pattern nodes**, and node JSON payload falls
**109,165,321 -> 97,225,536 bytes**. The original report counted only the current
view; timing samples already included both. Neither payload is a peak-RAM
measurement. Crucially, the selected replay still checks **11,362 nodes beyond
its 593 explicit steps**. Internal profiles, stored alternatives and summaries
remain recursively checked. Measure their successful semantic dependencies
before attempting a standalone positive checker; a short outer witness does
not establish cheap or compact complete checking.

All archive bytes and prior results remain unchanged; coverage remains 58/83.
This positive-only subset is not a complete discovery catalog, and omitted
routes prove no exclusion or UNSAT claim. The new six-test module checks lazy
prefix dependencies and tampering; matched cold replay disables fresh discovery.
The older expansion runners remain unchanged, so no full-pipeline reduction is
claimed. Resume the **23-variable / 93-clause** frontier from
`cnf-reused-branch/report.json`, preserving all five evidence lists **(1, 42,
156, 11, 1)**. Saved pairs **5, 6, 11, 13** and ordinary candidates **7, 9, 16,
17** remain the next discovery options. Detailed scope and reproduction commands
are in the linked note and `cnf-selected-routes/report.json`.


## 2026-11-14: expose retained proof steps and correct dependency totals

[Expanded positive coverage](expanded-coverage-dependencies.md) replaces the old
proof's implicit bases with explicit internal plans and exact retained-policy
references. The same 58 roots now have **2,748 ordered steps**, exposing **2,155**
hidden steps. Both conditioning branches, shared component occurrences and all
selected external rules survive. Independent cold replay passes with fresh
discovery disabled; the 57-test suite covers missing or forged dependencies.

The accounting audit found a separate prepared-policy cache omitted from the
previous dependency summary. Selected replay actually checks **11,955 nodes /
97,225,536 node JSON bytes**, including **1,697 prepared nodes / 8,610,646 bytes**.
Full-route replay checks **13,211 nodes / 109,165,321 bytes**. Timing samples had
included this work, so the prior 15.03% mean replay saving remains unchanged.
Historical reports are preserved; the new report records their corrected totals.

**9,207 checked nodes / 78,657,022 node JSON bytes** are outside the expanded
positive graph. They include primitive/external dependencies as well as history
and losing alternatives; they are not all proved removable. The next checker
must establish sufficient primitive premises before pruning them. Expansion
costs **0.26315 s** after checking; the graph is **777,176 compressed bytes** and
still depends on the full history. Cold expanded replay costs **34.50104 s**
versus **30.51477 s** for the old selected witness in this run, so this step makes
proof obligations explicit without an achieved runtime reduction.

Coverage, SQLite, every previous result and the 23-variable / 93-clause discovery
frontier are unchanged. Resume `cnf-reused-branch/report.json`, retaining all five
evidence lists **(1, 42, 156, 11, 1)**. The new report is a verification study,
not a new reconstructible discovery checkpoint or an unrestricted-SAT result.


## 2026-11-14: validate selected semantic steps without historical search replay

[Hybrid primitive replay](positive-primitive-replay.md) validates the unchanged
2,748-step graph for the same 58/83 roots. It handles 2,687 internal steps directly;
five subsumption steps and 56 external routes retain the original validators.
Exact CNF/configuration/depth bindings, complete resolvents, source-bound probe
reasons, retained references, component multiplicity and both conditioning
children remain required. Positive results never enter historical validation
caches: they do not certify search ranking, failed recognizers or losing plans.

Two matched cold repetitions in reversed order reduce mean replay from
**30.15238 to 2.71821 seconds (90.99%)**. Full historical checking falls
**11,955 -> 471 nodes**, including both policy views; distinct inventory rows
read fall **11,955 -> 2,797**. The old caches retain 97,225,536 node JSON bytes;
the hybrid's historical caches retain 3,096,763 bytes, with a further 18,568,514
bytes read directly for graph steps. These are logical payloads, not peak RAM.
The 56 external routes and their 25 ordinary/26 learned prefixes remain checked.

The warm regression is preserved: **0.25349 -> 1.88878 seconds** on average,
because direct transformations are revalidated rather than cached. Restoring
history and sidecars takes **20.91624 seconds**, now the larger preparation cost.
A sufficient selected-proof bundle plus explicit open-frontier dependencies is
the next integration target; a partial catalog cannot prove exhaustion. Older
expansion runners and complete archive audits are unchanged.

All **132 relevant tests** pass, including 512 two-variable clause subsets and
504 applicable normalized eliminations checked against exhaustive semantics,
changed bindings/reasons, missing resolvents and branches, retained references,
fused closures, projections and external evidence. The matched run disables
fresh recognition/discovery and confirms byte-identical SQLite and logical table
digests. The archive remains **770,338,816 bytes / 41,758 nodes**, all previous
results survive, and no new SAT family, Lean refinement or general polynomial
bound is asserted.

Resume discovery from `cnf-reused-branch/report.json` with all five lists
**(1, 42, 156, 11, 1)**. The 23-variable / 93-clause leaf, saved pairs **5, 6, 11,
13**, next ordinary candidates **7, 9, 16, 17**, and 17 learned bases / 88
candidates are unchanged. The new `cnf-positive-primitives/report.json` is a
verification study, not a discovery checkpoint.


## 2026-11-14: standalone data for positive proof replay

[The positive data bundle](positive-proof-bundle.md) captures exact SQL reads
from fresh checking caches, retains all five evidence lists, and binds the
ordered proof to separately supplied source/configuration claims. It includes
**2,797 pattern rows and 82 external-record rows**. Consumers build a new
read-only temporary database and rerun semantic checking; missing premises,
unused SQL rows, duplicate identities, changed claims and invalid scope fail.
No file digest or saved closure flag replaces the proof checks.

Independent processes outside the repository's working directory replay the
same **58/83 roots / 2,748 steps**, with lineage restoration disabled. Two
matched repetitions in reversed order reduce mean complete cold process time
**23.95282 -> 3.03614 seconds (87.32%)**. Semantic replay remains about 2.7 s;
the gain comes from preparation. The artifact is **3,169,051 compressed bytes**
and rebuilds **40,538,112 bytes** of temporary SQLite instead of 770,338,816.
The original archive is unchanged, so this adds persistent storage while reducing
cold working data. No peak-RAM reduction is claimed.

Production still pays **20.82422 s restoration, 2.78123 s capture, and 1.53465 s
serialization/compression**, plus integrity and diagnostic work. The complete
study, including producer and four consumers/controls, takes **80.64054 s**.
All **139 relevant tests** pass and the preceding artifacts remain unchanged.
The earlier warm-replay regression is not addressed by this data packaging.

This is positive-only data, not a discovery checkpoint or complete catalog.
Next establish source-local frontier dependencies and explicit completeness and
admission contracts: a row absent from the bundle is not necessarily a new state
or evidence of exhaustion. Keep full history authoritative and preserve all new
deltas. Resume discovery from `cnf-reused-branch/report.json`, retaining evidence
counts **(1, 42, 156, 11, 1)**. The 23-variable / 93-clause source, saved pairs
**5, 6, 11, 13**, next ordinary candidates **7, 9, 16, 17**, and wider 17-base /
88-candidate queue are unchanged. No new family, SAT verdict, Lean refinement or
unrestricted polynomial bound is established.


## 2026-11-14: source-local ordinary expansion and exact historical membership

[The source-local path](source-local-expansion.md) now advances the open
23-variable / 93-clause source without preparing a complete route catalog or
copying all history. Each local miss consults a pinned, read-only authoritative
snapshot; old nodes and saved prefixes pass their original validators, and every
insert checks authoritative membership. New-row metadata separates imported
premises from novel records. The partial maps cannot enumerate global routes.
A missing local row therefore never establishes novelty or stream exhaustion.

The matched single-block workers produce identical records, discovery counts
and byte-identical deltas. Mean complete worker process time falls **10.99932 ->
0.12683 s (98.85%)**, including preparation and delta export. Working SQLite
falls from **770,347,008 to 94,208 bytes**, but the separate full authority is still
required. First restoration costs **20.59393 s**; merge costs **0.10878 s** and
cold delta checking **0.06109 s**, outside that worker comparison. Probing itself
is slightly slower. The full four-worker study takes **45.50471 s**. Two reversed
samples share OS caches; this is no peak-RAM or complete SAT-solver speed claim.

The saved window checks both assumptions for **7, 9, 16, 17** and is clear. It
adds one record, no pattern nodes and no closure edge; coverage stays **58/83**.
History becomes **770,347,008 bytes / 41,758 pattern nodes**. Its **2,025-byte
compressed delta** merges idempotently and cold-checks, with all parent bytes
preserved. All **146 relevant tests** pass, including omitted-state reuse,
checked prefix restart, bounded exhaustion, forced pending work, shared admission,
rollback, changed identities and corrupt deltas. No new Lean refinement or
unrestricted complexity result is claimed.

Resume through `continue_cnf_source_local.restore_checkpoint` from
`experiments/results/cnf-source-local-checked/report.json`, retaining the five
lists **(1, 42, 156, 11, 1)**. The preliminary `cnf-source-local/` run is preserved
with an invalid-metadata note and is not a checkpoint. Next ordinary candidates
are **18, 21, 22, 23**, compared with saved split pairs **5, 6, 11, 13** under one
allowance. The learned queue remains 17 bases / 88 candidates. Source-local split
and learned dependencies, global selection and amortizing restoration remain
open; the ordinary-stream API does not provide their completeness contracts.


## 2026-11-14: source-local forced reduction and global recomposition gap

[Forced source-local expansion](source-local-forcing.md) advances the saved clear
prefix and proves **source variable 22=true**. The block checks both assumptions
for 18 and 21, then derives a conflict under 22=false. Fourteen unit reasons and
the conflict are checked. The exact target shrinks **23 variables / 93 clauses /
288 literals -> 22 / 88 / 272**, with one admitted unresolved node and no pending
acquisition. Coverage remains **58/83**, and the 2,748-step positive proof replays.
Reference solving confirms source and target SAT, with a checked lifted model;
all 1,998 former reference nodes survive among 2,012 verified nodes.

Eager and source-local workers produce identical records, ordinary probe counts,
admitted identities and byte-identical deltas. Two reversed fresh-process trials
reduce mean one-block process time **10.03384 -> 0.13717 s (98.63%)**, including
preparation and export with an available authority. Actual advance/recognition
is slightly slower. Local SQLite is **126,976 bytes**, but still depends on full
history. Initial reconstruction costs **21.99791 s**; global preparation costs
**6.47823 s**, and global composition/checking costs **55.48722 s**. The full
four-worker study takes **115.19078 s**, excluding the unmeasured exploratory
propagation used for adaptive selection. This is no complete SAT-solver or
peak-RAM claim. Global checking caches hold 22,603 nodes / 191,717,696 node-JSON
bytes, exposing the next maintenance cost.

The **4,447-byte compressed delta** adds one continuation and one pattern node.
Full history grows by **24,576 bytes** to **770,371,584 bytes / 41,759 nodes**;
parent records are unchanged and merge is idempotent. All **148 relevant tests**
pass. A fresh full checkpoint reconstruction checks the new records, table digests
and positive proof. No new Lean refinement, tractable category or unrestricted
construction bound is claimed.

Resume via `continue_cnf_local_forcing.restore_checkpoint` from
`experiments/results/cnf-local-forcing/report.json`, retaining all five lists
**(1, 42, 156, 11, 1)**. The new leaf has SHA-256
`545c51d457452dc1fd3dec970e5eadc1f85ba4012c889be2164277966968bf29`.
Next ordinary candidates are **16, 18, 21, 22**, in new canonical coordinates
(new 22 is old 23); saved split pairs rank **13, 5, 6, 11**. The learned queue
remains 17 ready bases / 88 candidates. Next investigate those discoveries and
exact incremental coverage maintenance with a complete reverse-dependency index;
partial catalogs or stale negative caches must not substitute for that contract.


## 2026-11-14: incremental finite coverage and the cold-cost boundary

[The complete coverage index](incremental-coverage.md) updates the affected
reachable rules after the saved forced append. Across full and without-growth
controls, four source-option checks replace 25,605 source visits. Warm composition
and original proof checking average **0.26146 -> 0.03949 seconds**; including the
shared **0.94030-second** complete external-route refresh gives an indicated
**18.47%** saving. The two full-control times vary substantially. Most of the old
55-second cold cost is historical semantic validation, already avoided by warm
verifier caches; do not attribute all of that difference to incremental closure.

The new index preserves both split obligations and duplicate premises, propagates
changed negative coverage results, and handles existing pending routes that become
available after target admission. It requires immutable historical pattern rows,
a fixed policy and a complete checked external catalog. Removed or rebound rules
require rebuilding. Cold loading recomputes closure and audits every reachable
option, rather than trusting persisted negative flags.

First index construction costs **55.68532 s**. Cold index replay is **64.41089 s**
versus **62.62709 s** for full recomposition: a retained regression. Both validate
22,603 historical nodes. Full snapshot serialization costs **7.96452 s** and adds
**11,241,021 compressed bytes / 94,113,609 raw JSON bytes** for two graphs, with
most source keys duplicated. No peak-RAM reduction is established. All **156
relevant tests** pass, including exhaustive graph/base combinations and real
pending-target activation; independent cold replay and full composition agree.

No new recognition state or structural coverage is acquired by this maintenance
study: coverage remains **58/83**, full history **770,371,584 bytes**, and the active
leaf **22 variables / 88 clauses**. The new index artifact is in
`experiments/results/cnf-incremental-coverage/`; discovery still resumes from
`experiments/results/cnf-local-forcing/report.json` through
`continue_cnf_local_forcing.restore_checkpoint`, preserving all five evidence lists
**(1, 42, 156, 11, 1)**. Next advance ordinary candidates **16, 18, 21, 22** or saved
split pairs **13, 5, 6, 11** in a bounded warm session with one admission allowance.
Complete route refresh, cold catalog revalidation and full-snapshot persistence
remain costs. Use the reusable graph for actual discovery before another isolated
verification optimization; no unrestricted construction claim follows.


## 2026-11-14: warm discovery batch reaches another original through 2-CNF

[The eight-step discovery batch](warm-expansion-batch.md) raises structural
coverage **58/83 -> 59/83**, closing original case **1189**, a 48-variable /
204-clause development input. A forced value on the 22-variable source exposes
five binary-implication path deletions and six eliminations, reaching a
15-variable / 55-clause leaf. Its remaining ordinary probes are clear; a saved
split on local variable 4 closes both cofactors through 2-CNF terminals. Both
branches independently check SAT. Closure propagates through 65 sources per
coverage graph, reusing retained ancestors. This is one observed interaction of
existing transformations, not a new unrestricted tractability guarantee.

The session consumes **21/32 state admissions** without resetting between eight
steps or between the two split branches. It retains **21 new pattern records,
two windows, five continuations and one split sidecar**. The database delta is
**15,484 compressed bytes**; full history grows by **335,872 bytes** to
**770,707,456 bytes / 41,780 pattern nodes**. All previous rows remain, and merge
is idempotent. The reference archive preserves all 2,012 old nodes and checks
2,041; the expanded positive proof now has 2,828 steps. All **160 relevant tests**
and fresh checkpoint reconstruction pass.

Actual acquisition costs **0.11884 s**, eight full route refreshes **7.59057 s**,
and warm composition/checking **1.30709 s full / 0.30604 s incremental**. Including
selection, acquisition and refresh gives an indicated **11.00%** saving, with
substantial first-control timing variation. Initial reconstruction, preparation
and complete catalog audit cost **91.13181 s**; the whole study costs 122.01047 s.
Saved split-trace replay is slower on this one pair (0.000719 versus 0.000452 s).
These costs and the absence of a peak-RAM bound remain explicit.

Resume **`experiments/results/cnf-warm-batch/report.json`** through
`continue_cnf_warm_batch.restore_checkpoint`, preserving all five evidence lists
**(1, 42, 156, 12, 1)**. The retained split frontier is now empty, but **24 original
inputs remain structurally uncovered**. Do not rerun only that empty selector.
Use `continue_cnf_original_splits.select` / `selected_frontiers` for another
original, or compare the **17 ready learned bases / 88 candidates**. The smallest
ready base has 33 variables / 359 literals, eight candidates left at offset 24,
and identity `1ad496f104725f62b5d8f754633a96c47aac13064bc6bf977b2f79001dfbde24`.
Test transfer of the restriction/implication/elimination/split pattern while
preserving one admission allowance. Complete-route maintenance remains the
largest repeated warm cost; cold auditing and persistence are still substantial.


## 2026-11-14: another original exposes a closed-cofactor scheduling gap

[The original-frontier batch](original-warm-expansion.md) selects case **1445**,
following its **33-variable / 121-clause / 359-literal** residual. Two saved splits,
three binary-path reductions and two eliminations leave one open **29 / 103 / 307**
residual with **7/32 admissions**. Both splits reuse the same earlier empty-CNF
terminal. Coverage remains **59/83**: part of the transformation sequence transfers,
but this batch does not close another original. All 74 new external probes are clear.

The selected split traces already existed in the immutable source nodes. Ordinary
exhaustion nevertheless consumed seven clear blocks before those two splits;
their full route refreshes cost **6.73336 s**. Compare earlier selection of a
known closed-cofactor pair against continued probing, including the possibility
of a cheaper forced reduction. This is an identified opportunity, not a measured
counterfactual speedup or a guarantee of such a pair for every CNF.

Discovery/acquisition totals **0.20427 s**, while twelve complete route refreshes
cost **11.55914 s**. Full/incremental warm composition and checking cost
**1.38586 / 0.47716 s**; with shared selection, acquisition and refresh, the indicated
saving is **6.80%**. Initial reconstruction and complete preparation remain
**94.52082 s**; the whole study costs **129.39795 s**. The **14,150-byte compressed
delta** preserves seven patterns and ten probe blocks; two split sidecars are
added. Full history is **770,924,544 bytes / 41,787 patterns**, growing by 217,088
bytes. Previous rows and all 2,041 reference nodes survive; 2,075 reference nodes
and the unchanged 2,828-step positive proof check. All **176 relevant tests** and
independent reconstruction with new recognition disabled pass.

Resume **`experiments/results/cnf-original-warm/report.json`** through
`continue_cnf_original_warm.restore_checkpoint`, with evidence counts
**(1, 42, 156, 14, 1)**. The new selector resumes retained obligations first, then
selects uncovered originals if that frontier is empty. It follows selected paths,
not all possible decompositions. The active leaf SHA-256 is
`ef925b9a7d10a3bab64accecd2ce12015dfa400b13bc949f39781e28c55069f8`.
Six ordinary candidates remain at offset 12: **18, 20, 23, 24, 28, 29**. The best
saved split is **local variable 12**, with one closed child and one missing
28-variable / 281-literal cofactor. Test that reuse opportunity next, retaining
case 1189 as a contrasting forced-reduction control. No unrestricted construction,
peak-RAM or new Lean guarantee is established.


## 2026-11-14: early closed-cofactor reuse helps one case and costs another

[The matched policy comparison](early-closed-expansion.md) tests using an already
checked closed cofactor before fresh ordinary probes. On case **1445**, early reuse
reaches the same state-budget boundary in **6 rather than 8 advances**, avoiding
12 assumption attempts. Expansion time falls **8.08296 -> 6.27974 s (22.31%)**;
complete worker time falls **20.70618 -> 17.90584 s (13.52%)**. Both arms enter the
same 32 state identities, store identical pattern payloads and choose identical
split records. Acquisition itself is slower because of extra candidate checks.

On the earlier forcing case **1189**, both policies preserve the same successful
8-step / 21-state proof, but early search takes **8.00118 versus 7.87241 s** for
expansion: a **1.64% regression**. It ranks 94 pairs versus 15, with eight misses.
These are single paired development runs, not independent holdout estimates or
a universal speedup. Saved forcing and unfinished pairs retain priority; both
children remain mandatory for structural coverage.

The current case reaches a **27-variable / 93-clause / 287-literal** source.
Its split on local variable **4** closes the false **22 / 72 / 211** cofactor
through 24 states, ending in a polarity transformation to a **6-variable Horn
terminal that is not 2-CNF**. The true **23 / 70 / 196** cofactor remains pending:
four more states were entered before the 32-state allowance ended, without
completed rows for those four states. Thus 32 admissions yield 28 new stored
patterns. Resume that exact target; the limit is not evidence of intrinsic hardness.

Both policies' results, including the regression, are preserved and merged into
current history. Each comparison arm has its own allowance; the union is not a
single 32-state experiment. Coverage remains **59/83**. The combined **19,191-byte
compressed delta** adds 28 patterns and six probe blocks, with two new split
sidecars. Full history is **771,342,336 bytes / 41,815 patterns**, growing by
417,792 bytes. All previous rows and all 2,075 reference nodes survive; 2,115
reference nodes and the unchanged 2,828-step positive proof check.

All **181 relevant tests** and independent reconstruction of all four arms pass.
Current/control reconstruction costs **32.97981 / 25.34922 s**; final complete
route preparation and all-original coverage checking cost **7.44994 / 60.00692 s**.
The full study costs **227.90943 s**. No peak-RAM, new Lean refinement or unrestricted
construction bound is supplied.

Resume **`experiments/results/cnf-early-closed/report.json`** through
`compare_cnf_early_closed.restore_checkpoint`, preserving evidence counts
**(1, 42, 156, 16, 1)**. Pending target SHA-256:
`69d0f3cad2b4d527495373e3fecf905d0c538d98adb833dbd0373598cfb0280e`;
split source SHA-256:
`6be85c519f3e56d3096ab3e1ed2ad63597d70459193d435d885457fca290ca39`.
Resume the pending true branch before another ranking search. Then investigate
incremental candidate checks with explicit invalidation for new traces, admitted
targets and changed coverage. Do not rerun all four comparison arms to continue.

## 2026-11-14: resume the pending cofactor and complete another original

[The exact saved split resumes](pending-warm-expansion.md) without reranking its
27-variable parent. Its closed false cofactor uses zero admissions. The true
23-variable cofactor uses twenty, ending at a seven-variable Horn and zero-valid
terminal after four probes, four binary-path deletions, ten eliminations and a
polarity transformation. It is not 2-CNF. Both branches now close, raising
structural coverage **59/83 -> 60/83**; the reference result for original case
1445 is SAT. All sixteen retained splits close, but 23 originals remain uncovered.

Four of the twenty entered states were unfinished at the previous cap and are
recomputed. All twenty now have completed rows. No previously completed identity
is admitted again. This measures a remaining persistence gap: local reduction
work on unfinished recursive ancestors is not checkpointed. A future pending
representation must preserve checked obligations without asserting their closure.

Acquisition takes **0.05998 s**, complete route refresh **0.98680 s**, and initial
reconstruction/preparation **103.25725 s**. The full producer takes **127.60236 s**.
The **11,805-byte compressed delta** adds twenty patterns and no external probe
blocks. Full SQLite grows **249,856 bytes** to **771,592,192 bytes / 41,835 patterns**.
The positive proof has **2,948 steps**, and all **2,115** earlier reference nodes
remain among **2,135**. All prior rows and experimental comparisons are preserved.

Resume `experiments/results/cnf-pending-warm/report.json` through
`continue_cnf_pending_warm.restore_checkpoint` with evidence counts
**(1, 42, 156, 16, 1)**. The next selected original is case **1304 / index 52**,
with a **34-variable / 148-clause / 490-literal** leaf; local variable **34** is
its last ordinary candidate at offset 12. Test transfer of the reduction chain
while amortizing complete preparation across useful steps. Neither this new
coverage nor an empty retained frontier establishes efficient arbitrary SAT.

## 2026-11-14: conditioning transfers through refutation and zero-valid structure

[Two warm advances](transfer-1304.md) close case **1304 / index 52**, raising
structural coverage **60/83 -> 61/83** in both views. On its 34-variable residual,
the last ordinary candidate is clear. A saved split on local variable **32** then
uses **10/32 admissions**: three failed-literal reductions refute its false
cofactor, while six reductions reach a **12-variable / 18-clause / 40-literal
zero-valid** SAT terminal on the true branch. The latter is neither Horn,
dual-Horn nor 2-CNF. Both branch answers and the SAT model lift are independently
checked. All seventeen retained splits close; 22 originals remain uncovered.

This exhibits a further reuse opportunity: the refuted cofactor proves a forced
value at its parent. The current checkpoint retains the split and branch proofs;
it does not introduce a new inferred-unit route. Reusing that value would require
the negative proof and exact source/transport binding, not a structural closure
bit. The two closed SAT branches in case 1445 show why that distinction matters.

Acquisition plus ranking costs **0.20118 s**, complete route refresh **2.01995 s**,
and initial reconstruction/preparation **106.78542 s**. The whole producer takes
**133.16301 s**. The early policy ranks 50 pairs, including seventeen immediately
rechecked after ordinary exhaustion; this is an avoidable candidate-maintenance
cost, subordinate to cold preparation. Two external assumption attempts and
nineteen retained internal assumption traces must be accounted for separately.

The **9,914-byte compressed delta** adds ten patterns and one continuation, plus
one split sidecar. Full history grows **122,880 bytes** to **771,715,072 bytes /
41,845 patterns**. All 2,135 earlier reference nodes remain among **2,259**, and
the expanded positive proof has **3,043 steps**. Cold reconstruction checks all
original coverage flags, exact next selection and reference proofs without fresh
recognition, taking **109.00529 s**.

Resume `experiments/results/cnf-transfer-1304/report.json` with
`continue_cnf_pending_warm.restore_checkpoint`, evidence counts
**(1, 42, 156, 17, 1)**. Next: case **1299 / index 48**, selected leaf
**36 / 162 / 517**, ordinary candidates **33, 34, 36** at offset 12. No currently
saved pair has a present child root; variable **17** has the best size rank.
These are adaptive development results, without a general expansion bound.

The next saved candidates expose a ranking tradeoff: variable **17** gives
34- and 32-variable children (927 total literals), while variable **1** gives
16- and 35-variable children (617 total literals). The latter's smaller branch
could be useful, but neither candidate has been acquired. Compare them under
matched allowances after the remaining probes, retaining both branch obligations.
All **181 relevant tests** pass for this checkpoint.

## 2026-11-14: matched first splits separate storage from completion cost

[Case 1299's matched comparison](split-cost-1299.md) retains thirteen new patterns
for initial variable 1 versus twenty-nine for variable 17. Each starts from the
same seed after six clear ordinary attempts, with twelve advances and a shared
32-state budget. Two repetitions reverse the arm order and yield identical
logical results. Compressed arm deltas are **15,849 vs 28,842 bytes**, but mean
expansion is **12.72181 vs 12.72706 s** and neither source closes. The runtime
comparison changes direction across repetitions; the smaller arm's complete
worker is **3.03% slower**. Complete route refresh consumes about **94%** of warm
expansion. The smaller acquired representation is no proof of a faster complete
solution or a minimum-cost split.

Both paths expose SAT terminals on one first cofactor: **5 / 5 / 10** is Horn,
2-CNF and zero-valid; **5 / 7 / 16** is Horn and zero-valid, but not 2-CNF. On the
other side, a later split refutes one cofactor through two probe reductions,
reusing the same empty-clause terminal. The remaining leaves are **28 / 110 / 351**
and **29 / 108 / 337**. Both have exhausted ordinary probes, with 21 clear pairs
and no candidate child presently acquired. Similar open leaves suggest checking
exact shared structure; they do not yet have a certified equivalence or transport.

Coverage stays **61/83** in both views. The preserved union has 42 unique new
patterns, 21 probe blocks and four split records; it is not one 32-state run.
The **43,317-byte compressed delta** grows full history by **884,736 bytes** to
**772,599,808 bytes / 41,887 patterns**. The positive proof remains 3,043 steps.
All 2,259 earlier reference nodes remain among 2,605. All **181 regression tests**
and the independent **214.315 s** audit pass, including exact seed/arm replay,
original closure flags, next selection and reference checking without fresh
recognition or reference solving.

Resume `experiments/results/cnf-split-cost-1299/report.json` through
`compare_cnf_split_cost.restore_checkpoint`, evidence counts **(1, 42, 156, 21, 1)**.
The next selected 28-variable source is
`dd04e43d15b115ab5d60b5b4aef44d03001fcfe6910263b218b5f35776ed70ab`;
its current best rank is **[2, 2, 26, 571, 17]**. Continue that obligation while
investigating shared structure with the alternative and incremental/deferred
catalog refresh. Keep decision witnesses, reference answers and structural
coverage separate. The complete producer costs **252.67688 s**; retained disk
bytes are not peak RAM, and no arbitrary-SAT efficiency bound follows.

## 2026-11-14: exact projection reuses a completed alternative

[The two leaves are connected by a certified projection](projection-bridge.md).
Eliminating variable 16 from **29 / 108 / 337** checks ten opposing clause pairs
and gives **28 / 111 / 356**. Removing one clause subsumed by `[-19, 5]` yields
the exact retained **28 / 110 / 351** target. The ordinary two-clause growth
budget rejects the intermediate result; the checked final target satisfies it.
This establishes existential equivalence with a bound variable transport, not
similarity or an inferred SAT/UNSAT label.

Both modes complete the same two leaves from independent identical seeds. Two
reversed repetitions use **25 vs 13 completed new states** and **7 vs 6 advances**
for independent vs bridge completion. Including **0.00691 s** of bridge discovery,
mean warm expansion falls **15.09%** and complete worker time **6.99%**. The bridge
adds **1,468 compressed bytes**; the pattern/probe delta plus that route is
**13,170 vs 18,956 bytes**. These are local development measurements, with shared
OS caches and no unrestricted bound or peak-RAM claim.

The retained union closes original **1299 / index 48**, raising structural
coverage **61/83 -> 62/83** in both views. It stores all 25 new patterns, four
probe blocks, three split records and the bridge. Full history is **772,972,544
bytes / 41,912 patterns**; its positive proof has **3,104 steps**. All 2,605 old
reference nodes remain among 2,921. Every source of the 24 saved split records now closes; 21
originals remain uncovered. The complete four-arm pipeline takes **219.34858 s**,
including **49.62108 s** of restoration and **67.16398 s** of final global checking.

Resume `experiments/results/cnf-projection-bridge/report.json` through
`compare_cnf_projection_bridge.restore_checkpoint`, preserving the five evidence
lists **(1, 42, 156, 24, 1)** **and** the separate `bridges` archive. Build routes
with `compare_cnf_projection_bridge.routes_for(h, evidence, bridges)` and check
extended positive proofs with `cnf_projection_bridge.verify_positive`.
The next original is **1298 / index 47**, leaf **37 / 151 / 455**, source SHA-256
`dd822fabc78af1efd220882ae9ead41593645ea916f4753c13b000b080a162b7`.
Next: recognize converging projections against retained structure before separate
acquisition, including final subsumption in the growth decision. Indexing,
failed proposals, arbitrary renaming and complete route refresh remain open costs.

## 2026-11-14: automatic projection target discovery and a bounded miss

[The new proposal catalog](projection-lookup.md) indexes **19,841 current-policy
formulas** by **17,801 minimal-clause signatures**. It recovers the previous
bridge without a supplied target, including the target's two redundant clauses.
Every hit still needs the original exact projection/subsumption checker and a
justified target proof. All **23 unresolved frontier sources** miss this bounded
search; coverage stays **62/83**, and the solver authority is unchanged.

Three alternating repetitions query 24 sources, including the known control.
Indexed discovery takes **0.87112 s**, versus **1.55276 s** scanning the same
prepared signatures. Construction costs **14.42661 s**, with **28,110,848 bytes**
of extra SQLite storage (**23,149,996 compressed bytes**). These are lookup
measurements, not demonstrated total expansion savings. Of 967 variable
proposals, 95 exceed the opposing-pair cap and 845 exceed final growth even after
subsumption; just 27 reach lookup. Only the known control has an acquired match.

Next: acquire the selected 37-variable residual's **variable-13** projection
within a bounded, matched comparison. Subsumption reduces its raw **154 clauses**
to **153 on 36 variables**, satisfying final growth two, but no acquired matching
target exists. Preserve the next ordinary probes **15, 18, 19, 20**. The exact
candidate is archived in the new study's `selected-diagnostics.json.gz`. Keep the
global index optional until broader reuse justifies its preparation and space.
Resume the unchanged `cnf-projection-bridge/report.json` authority with all five
evidence lists and its separate bridge archive. New catalog and negative results
are preserved in `experiments/results/cnf-projection-lookup/`.

## 2026-11-14: bounded projection acquisition closes a case but loses on cost

[Acquisition of the saved candidate](projection-acquisition.md) now closes
original **1298 / index 47**, raising structural coverage **62/83 -> 63/83** in
both views. Source **37 / 151 / 455** projects by local variable **13** to
**36 / 153 / 470** after one checked subsumption deletion. Pending acquisition
cannot become a bridge, and the helper preserves one shared admission budget.

Two reversed repetitions compare ordinary continuation with projection from
independent identical seeds, with **12 advances / 32 states** each. Both close
the source. Ordinary uses **4 advances / 8 new states / 4.45329 s** expansion;
projection uses **8 / 9 / 8.70178 s**. Complete worker means are **16.62221 vs
21.45978 s**. External continuation needs **20 vs 44** assumption attempts.
Full route refresh costs **4.05191 vs 8.15891 s**, over 90% of expansion.
The smaller formula is more expensive here; the prior successful bridge reused
an already acquired target. Candidate discovery is charged in the preceding
study, not repeated in these conditional means.

Both paths select the same variable under the projection map, source **22** /
target **21**. The false cofactor is refuted after three failed-literal reductions;
the true cofactor reaches the same five-variable disjoint-component key after
two reductions. These paths and independent reference witness lifts are checked.
Both split pairs already occur in their respective initial pattern records,
suggesting an earlier saved-pair policy as the next matched test. Transferring
unit-propagation traces or unsuccessful searches across projection still needs
additional justification.

The union preserves **14 new patterns**, eight continuation blocks, one probe
window, two split records and the new bridge. Three new exact keys are shared
between the arms. Full history is **773,255,168 bytes / 41,926 patterns**; the
union delta is **16,475 compressed bytes** and the positive proof has **3,145
steps**. Both bridge targets and all 26 retained split sources close. Twenty
originals remain uncovered. Independent cold replay takes **221.51064 s**, with
fresh recognition and reference expansion forbidden; all **3,022 reference
nodes**, both repetitions, global coverage and resumable selection check.
All **199 relevant tests pass**.

Resume `experiments/results/cnf-projection-acquisition/report.json` with
`compare_cnf_projection_acquisition.restore_checkpoint`, preserving five evidence
lists **(1, 42, 156, 26, 1)** and its separate two-bridge archive. Report SHA-256:
`d865c287709cccdd0af56c1a23a564618e369be41fd4e971c21c0834b3510b2a`.
Use the bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The new `projection_frontier` sidecar has two closed targets and no leaves.

Next original: **1160 / index 29**, selected **37 / 151 / 456** leaf, SHA-256
`614772f5cb0f59835870e117b1653b225e008eb44416371335350a725cac6149`.
Its next ordinary variables are **13, 15, 16, 17**; sixteen saved pairs have no
acquired candidate child root, with best rank **[2, 2, 35, 794, 19]**. Despite
similar dimensions, its normalized clause set shares no exact clause with the
completed leaf. Prioritize existing split evidence and incremental route
maintenance while continuing broader structural discovery. Neither a minimum-cost
policy nor an unrestricted SAT resource bound has been established.

## 2026-11-14: early saved-pair selection improves both matched cases

[The new scheduling comparison](early-saved-expansion.md) raises structural
coverage **63/83 -> 64/83**, closing original **1160 / index 29**. Saved clear
pairs already carry checked restrictions for both polarities; exhausting the
ordinary probe pool is not required for their correctness. `EarlySavedExpansion`
uses the best existing pair immediately, preserving pending/known-forcing
priority, both child obligations and one shared admission budget. The ordinary
policy already permits early pairs with closed children. Neither uses reference
answers or interprets a clear probe as a SAT certificate.

Two reversed repetitions per case use identical independent seeds, twelve
advances and 32 states. On case 1160, the same sixteen new keys require **2 vs 12
advances**; expansion falls **13.62996 -> 2.24986 s** and complete worker time
**26.38845 -> 14.69517 s** (**44.31% lower**). Extra external assumption attempts
fall **80 -> 0**, while recognizer-internal probing remains charged. Both paths
split source variable **19**, expose binary implications and elimination on its
false branch, then split the remaining **34 / 135 / 404** leaf on local variable
**14**. That split has a refuted branch and a SAT branch ending in **6 / 7 / 14
2-CNF**, neither Horn nor dual-Horn. The first split's true branch reaches the
retained empty-CNF terminal. Both first-level branches are independently SAT;
full structural classification remains distinct from earliest SAT decision.

On historical forcing control **1189**, reconstructed from its older seed,
complete worker time falls **20.45091 -> 15.37364 s** (**24.83% lower**) and
new states **21 -> 20**, using three splits instead of further forcing followed
by one split. Its two new pattern key sets are disjoint. The early policy stays
optional: two successful development examples do not bound the advantage of a
future forcing opportunity or establish a universal selection rule.

The combined checkpoint preserves both policies and all earlier results. It adds
**36 patterns**, nine continuation blocks, one probe window and five split
records. Full history is **773,828,608 bytes / 41,962 patterns**, with **27,393
compressed delta bytes** and a **3,190-step** positive proof. All 31 retained
split sources and both bridge targets close; nineteen originals remain uncovered.
The union is not one 32-state run. Full route refresh still consumes most warm
expansion. The complete study costs **334.32398 s**, including current restoration
**57.71801 s**, historical control restoration **25.38864 s** and final global
preparation/checking **68.76609 s**. Complete worker means charge preparation,
checking and persistence separately from the quoted expansion phase totals.

All **204 tests** pass. Independent cold replay checks all eight arms and
**3,203 reference nodes** with recognition and reference expansion forbidden,
including repeated results, exact next selection and idempotent merging. The
157-page paper builds, preserving all 64 proof blocks. All **533 earlier
artifacts / 17 manifests** remain hash-identical.

Resume `experiments/results/cnf-early-saved/report.json` through
`compare_cnf_early_saved.restore_checkpoint`, keeping the five evidence lists
**(1, 42, 156, 31, 1)** and the separate two-bridge archive. Use bridge-aware
`routes_for` and `cnf_projection_bridge.verify_positive`. Report SHA-256:
`995476297ac2e99710b26b67d9ecc3e95963ab624e68282e7b5108da077999d3`.
Next: original **1263 / index 42**, leaf **37 / 152 / 470**, source SHA-256
`746b92609a26b66fe74b529bdeb36a5a46ca58129c1bcca04c5088bd23d02eeb`.
Its remaining ordinary variables are **32, 33, 34, 37**. Sixteen saved pairs have
no acquired child root; best rank **[2, 2, 35, 817, 6]**. Broaden the comparison
while seeking forcing regressions, and test incremental route maintenance with
explicit activation and invalidation conditions. General efficient SAT coverage
and minimum-cost expansion remain unproved.

## 2026-11-14: clear probe metadata reuses the complete route catalog

[The checked maintenance comparison](clear-probe-maintenance.md) closes original
**1263 / index 42**, lifting coverage **64/83 -> 65/83** in both views. The new
helper retains a complete checked route catalog only after a verified clear
probe with no acquired state, no semantic edge and unchanged sidecars. Exact
SQLite accounting and row binding constrain the change; forcing, acquisition
and new evidence rebuild fully. External or schema changes require reopening
checked inventory state. Saved candidates remain available.

Identical ordinary scheduling on matched seeds yields the same operations,
patterns and final logical tables. Case 1263 uses **4 advances / 11 states**;
two skipped rebuilds reduce mean expansion **4.56885 -> 2.46956 s** and worker
**17.23793 -> 14.87208 s (13.72%)**. Historical forcing control 1189 uses **8
advances / 21 states**; six skipped rebuilds reduce expansion **8.10837 ->
2.24496 s** and worker **20.13427 -> 14.18042 s (29.57%)**. Both modes still
perform **16 / 51** external assumption attempts and retain both branch proofs.
The later forcing result is preserved and activated by a full rebuild.

Persistent deltas are identical: **12,933 / 15,484 compressed bytes** and
**241,664 / 397,312 SQLite bytes**, current case/control. Extra serialized
sidecar snapshots occupy **1,220,757 / 941,068 bytes**, excluding transient
serialization and Python overhead. This is computation reuse, not a storage
reduction or a peak-RAM estimate. Current authority reconstruction costs
**62.36289 s**, final preparation/global coverage **67.55856 s**, and the full
producer **316.04814 s**. Preparation and export remain major worker costs.
Two development cases and two reversed repetitions give no holdout or general
SAT guarantee; do not add these gains to early-saved scheduling gains untested.

The first split is source-local variable 6, then variable 9 of the remaining
31/125/377 leaf. Probe, binary-path and elimination reductions reach retained
Horn/dual-Horn 2-CNF and matching 2-CNF endpoints, plus an empty-clause UNSAT
endpoint. All SAT lifts and both split obligations are checked. Independent
cold replay passes in **313.36574 s** with new recognition/reference expansion
forbidden, including all **3,259 reference nodes**, repeated logical results,
exact selection and idempotent merges. All **209 relevant tests** pass.

Resume **`experiments/results/cnf-clear-maintenance/report.json`** through
**`compare_cnf_clear_maintenance.restore_checkpoint`**, SHA-256
`b4aa304049758bff8e80b2118437321a9edf7128657b3a9303a4985ae57daa78`.
Retain five evidence lists **(1, 42, 156, 33, 1)** and the separate two-bridge
archive; use bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The union adds **11 patterns, 1 window, 1 continuation and 2 splits**. History
is **774,000,640 bytes / 41,973 patterns**, **172,032 bytes** larger. All 33
split sources and both bridge targets close. Eighteen originals remain open.
Next: original **1154 / index 27**, **38 / 158 / 500**, source SHA-256
`f33c327595b24645a6f64e8a072295c51fb2a414872d0de0f84da49192f0085d`.
Its ordinary pool is exhausted. Eleven saved pairs have no acquired child;
best rank **[2, 2, 36, 906, 30]**. Test that pair, then investigate shared family
structure and scheduling choices in its descendants. Prepared checked state and
incremental activation after acquisition remain the next large maintenance gaps.

The manuscript builds to **158 pages** with all **64 proof blocks** unchanged,
no overfull boxes and no undefined references. All **660 earlier artifacts /
18 manifests** remain hash-identical. The new study preserves **124 manifested
artifacts** plus its manifest, including producer, cold-replay, test and build
logs, exact deltas, reference results and source fingerprints.

## 2026-11-14: combined reuse improves one cofactor but leaves pending expansion

[The combined-policy comparison](combined-expansion.md) acquires the best saved
pair of original **1154 / index 27**, **38/158/500**, at local variable 30. Both
modes use this same initial split and checked clear-probe maintenance, then
compare ordinary and early-saved descendant scheduling. Two reversed-order
repetitions preserve one twelve-advance / 32-state allowance per independent
worker. No production recognition rule or default policy changes.

Stepwise reconstruction proves that the same true cofactor closes after **9
advances / 30 states** ordinarily, versus **2 / 19** early. Beyond the common
ten states, this is **20 vs 9 additional states**, with mean expansion
**3.64836 vs 1.11924 s**. The early variable-23 split of the 31/130/416 leaf sends
both branches to the retained empty-CNF terminal. Ordinary forcing first reaches
26/101/329, then variable 5 reaches an empty terminal and an existing Horn 2-CNF
plan. These are different checked routes to the same completed cofactor.

The full original remains structurally open; coverage stays **65/83**. Ordinary
spends **12 advances / 30 admitted and stored states**; early spends **4 advances /
32 admitted / 27 stored / 5 unstored ancestors**, with both final split targets
pending. Mean worker time is **17.80102 / 17.20828 s** and expansion **4.98209 /
4.64624 s**. These unfinished obligations differ, so no whole-original speedup
is established. Both modes still pay about **4.3 s** for four full route refreshes;
eight extra ordinary clear blocks already avoid rebuilding. Stored delta sizes
**26,971 / 20,877 compressed bytes** likewise do not compare equal completed work.

The union preserves **47 new patterns** (ten shared, twenty ordinary-only,
seventeen early-only), **6 continuations / 4 windows / 5 splits**. History grows
**765,952 bytes** to **774,766,592 bytes / 42,020 patterns**. The union is not one
32-state run; the five interrupted ancestors are not counted as stored results.
Producer time is **231.79591 s**, including **67.80502 s** restoration and
**67.41552 s** global preparation/coverage. Independent cold replay passes in
**302.33071 s**, forbidding fresh recognition and reference expansion. It checks
all **3,422 reference nodes**, both polarities, SAT model lifts, interrupted
accounting, idempotence and exact next selections. First-repeat stepwise replay
inserts only then-available rows and certifies cofactor-completion times; exact
operation histories agree within each mode across repetitions. All reference
split sources and raw children are SAT. Complete structural coverage is a
stronger objective than producing a SAT witness.

Resume `experiments/results/cnf-combined-expansion/report.json` using
`compare_cnf_combined_expansion.restore_checkpoint`, report SHA-256
`33c45cc536dc9ada0acdb4d1ef9a17bd9a71e260704644aa656af42835c349c3`.
Keep five evidence lists **(1, 42, 156, 38, 1)** and the separate two-bridge archive;
use bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
Resume the pending **30/116/363**, local-variable-26 split, source SHA-256
`f68661ab48e945151f89e250ebbcc35eb2ff8034799d2a83e2ddd88d7306567d`.
Its targets **29/108/336** and **19/54/140** are absent; a **33/130/400** leaf
also remains. The last interrupted advance writes no pattern/probe row but pays
**1.06672 s** refreshing routes against **0.03448 s** acquisition. A guarded
pending-sidecar update is a more immediate maintenance target than that small
reentry cost. Preserve both obligations and test activation when targets later
arrive. General efficient coverage and minimal expansion remain unproved.

Verification: **209 regression tests pass**; the manuscript builds to **158
pages**, with all **64 proof blocks unchanged** and no undefined references or
overfull boxes. SHA-256 checks preserve all **784 artifacts in 19 prior
manifests**. The new manifest binds **81 artifacts** (4,377,743 bytes), including
producer/cold logs, both policy histories, stepwise findings, progress summaries
and validation metadata. One existing SQLite ResourceWarning appears in the
passing regression log; no solver or test module changed.

## 2026-11-14: inactive pending splits preserve routes; one cofactor remains

[The pending-split maintenance study](pending-split-maintenance.md) implements
an optional guard for zero-write interrupted splits. It checks the exact sidecar
change, both polarity bindings, missing targets and entered-state accounting.
A split with an absent child adds no active edge; any write or other sidecar
change rebuilds routes, including later activation. The guard is independent of
CNF category, with linear sidecar serialization plus split-checking costs.

Two reversed-order repetitions compare clear-only maintenance with this guard.
The historical interruption preserves identical operations and stored results
while the final route update falls **1.08509 -> 0.01138 s**. Mean expansion falls
**4.71930 -> 3.59923 s** and worker time **17.55753 -> 16.15178 s (8.01%)**.
The current resumption writes nodes in every advance, so all three updates
rebuild and expansion remains **3.54491 / 3.54578 s**. No persistent-memory
saving or completed-original speedup follows from the interruption comparison.

Resumption acquires the old variable-26 pair with nine states and closes its
23-variable leaf via a variable-13 split with eight more. The two new splits'
false branches reuse the same UNSAT empty-clause terminal; a true branch reaches
a **10/10/21** polarity-transformed Horn, zero-valid residual. The separate
**33/130/400** source splits at variable **18**, acquiring its false **29/96/275**
cofactor with two states but entering thirteen ancestors of the true
**30/111/330** cofactor without storing them. All **32 admissions** are charged;
**19 new patterns** are completed. The true cofactor is independently SAT; the
missing obligation is reusable structural decomposition. Coverage stays
**65/83**, with one pending target and no acquired open leaf in the frontier.

The union preserves old history and adds **19 patterns / 2 split records / no
external probe rows**, reaching **775,004,160 bytes / 42,039 patterns**. The delta
is **307,200 SQLite bytes / 12,874 compressed bytes**. The independent reference
archive preserves **3,422** prior nodes and has **3,467** total. The positive
certificate still has **3,239 steps**. Producer time is **368.96634 s**, including
**72.00904 s** current restoration, **67.51801 s** historical restoration and
**68.15113 s** final route preparation/global coverage.

Resume `experiments/results/cnf-pending-maintenance/report.json` using
`compare_cnf_pending_maintenance.restore_checkpoint`, report SHA-256
`9a48fc85512e52c566dd60f0396a4bacf842b48267ee47606394d271d221f8d0`.
Keep five evidence lists **(1, 42, 156, 40, 1)** and two separate bridges, using
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The pending source SHA-256 is
`1fab57607093cb833cc8fa0f21d88c2e7e9eb094dac7cdd416e8a786e3fcf056`;
its missing true target is
`5124e2d5f451e42b274ed6886d29676c94f89e27bb3054f77b530f2f3091a3a4`.
Resume this exact pair, retain its acquired false child and charge reentry of
the thirteen unstored keys. The next maintenance opportunity is complete
activation of affected routes after actual acquisition. A reverse dependency
index must cover all route types and newly satisfied old pending obligations.
Current final acquisition costs about **0.06 s**, versus **1.08 s** for rebuild;
continuation-checkpoint work should be judged against that measured difference.

Independent cold replay passes in **487.75798 s**, with all **3,467 reference
nodes** checked and no fresh recognition or reference search. All eight workers
have identical operations and logical results within each workload. Four
stepwise prefix replays compare complete maintained and fresh catalogs,
coverage and next selections using only then-available rows. All five previously
interrupted states are reentered and now stored; thirteen new unstored states
remain explicit.

Verification: **215 tests pass** (209 prior plus six new regressions). The
manuscript builds to **159 pages**, preserving all **64 proof blocks** exactly,
with no overfull boxes or undefined references. All **865 prior artifacts in
20 manifests** remain hash-identical. The new manifest binds **104 artifacts**
(3,977,775 bytes), including matched operations, deltas, independent findings,
reference results and logs. SQLite ResourceWarnings in the passing suite and
the initial external-write fixture correction are recorded in validation
metadata. No completed result or earlier experiment was removed.


## 2026-11-14: exact pending-pair resumption closes case 1154

[The retained-pair experiment](pending-pair-resumption.md) raises structural
coverage **65/83 -> 66/83**, also without growth exceptions. Both independent
repetitions resume the exact local-variable-18 split. Its already acquired
false branch takes no new admissions; sixteen states on the true **30/111/330**
cofactor expose a **19/66/214** residual. A saved variable-3 split takes eight
and six further states. The two branches reach different seven- and
nine-variable Horn, zero-valid terminals after checked reductions and polarity
changes; neither is 2-CNF. These are overlapping family recognitions and
similar reduction patterns, not a shared terminal proof. Both raw branches are
SAT in the independent reference check. Full structural closure still checks
both branch obligations.

All **30 admissions** are stored, including all thirteen ancestor keys that
were entered but unstored in the previous run; their reentry is charged.
No retained split obligation remains open. **Seventeen original formulas** are
still uncovered, and the next selected residual belongs to **1062 / index 14**,
with **39 variables / 161 clauses / 495 literal occurrences**.

Mean expansion costs **2.38750 s**: acquisition **0.12262 s**, complete route
updates **2.17729 s (91.2%)**, selection **0.08558 s**, and coverage **0.00201 s**.
Preparation and export cost **8.01578 s** and **4.76630 s**; whole worker time is
**15.23836 s**. These are two identical-policy repetitions, not a comparative
speedup. Both updates change patterns and correctly rebuild. Arrival of the
last missing target activates an old split; the following split attaches with
both targets acquired. These transitions are concrete fixtures for a future
complete dependency-based maintenance implementation.

The union adds **30 patterns / 1 split / no external probe records**. Internal
probe certificates are stored with pattern nodes. The delta is **446,464
SQLite bytes / 17,007 compressed bytes**, and full history grows **372,736 bytes**
to **775,376,896 bytes / 42,069 patterns**. The positive certificate has
**3,360 steps**; reference evidence preserves all **3,467** prior nodes and
contains **3,575**. Parent restoration costs **76.28286 s**, final preparation
and global coverage **68.16053 s**, and the complete producer **196.65984 s**.
Persistent byte counts do not measure peak RAM or establish arbitrary-SAT bounds.

Resume `experiments/results/cnf-pending-pair/report.json` through
`continue_cnf_pending_pair.restore_checkpoint`, SHA-256
`0e310e043cc74e29d102115663db88c513acf8bf865fac7412fea1e0eb4f5760`.
Keep evidence lists **(1, 42, 156, 41, 1)** and **two bridges**, using bridge-aware
`routes_for` and `cnf_projection_bridge.verify_positive`. The report's `source`
is the now closed 38-variable ancestor. **Select the next work from
`next_selection`**, not that completed focus. Broader conditional-family
discovery and complete incremental route activation remain the priorities.


Independent cold reconstruction passes in **289.93906 s**, checking all
**3,575 reference nodes** without fresh recognition or reference search.
Both repeat prefixes reconstruct only then-available rows and reproduce the
complete maintained/fresh catalogs, closure and next selections. All **3,467
previous reference payloads** and **969 earlier artifacts in 21 manifests**
remain unchanged. **215 tests pass**; the manuscript builds to **159 pages**
with all **64 proof blocks unchanged**, no overfull boxes and no undefined
references. The new manifest binds **40 artifacts (4,005,929 bytes)**,
including operations, deltas, reference evidence, cost and structural findings,
validation metadata and logs. No new Lean theorem or general SAT tractability
claim is made.


## 2026-11-14: selective activation after real pattern acquisition

[The activation helper](pattern-activation.md) closes the dominant warm
maintenance gap for guarded pattern-only appends. It indexes missing premises
of all conditional route types, activates affected routes when their targets
arrive, and preserves the full builder's order. Both split branches remain
required. Other writes or sidecar changes use existing checked maintenance;
external writers require reopening the inventory. Initial and cold checking
remain complete. The index is additional live state, not a persisted trust
cache or a storage reduction.

Two reversed-order repetitions compare identical scheduling and independent
seeds. Historical complete-worker time falls **15.08509 -> 12.86353 s (14.73%)**;
current bounded-worker time falls **16.85095 -> 13.40605 s (20.44%)**. Route-update
costs fall **2.18377 -> 0.02296 s** and **3.33336 -> 0.03679 s**, respectively.
Current acquisition/selection now cost **0.26735 / 0.13948 s**, compared with
**0.03679 s** maintenance. Preparation and export remain **7.83564 / 4.97464 s**,
and their variation is not an activation improvement. The historical case
closes the same thirty states; current partial expansion stores thirty-two
states but leaves identical unfinished obligations in both modes.

The current **39/161/495** source of original **1062 / index 14** splits on
local variable 25. Its false branch reaches an existing **36/144/434** unresolved
plan after two reductions; the true branch exposes **35/149/466**. A variable-8
split of that leaf takes **2 / 21** states, with the true branch reaching a new
**7/9/19** Horn, zero-valid terminal after checked reductions and polarity
change. The remaining **34/143/440** leaf splits at variable **5**. Its false
branch takes the last three states to reach **31/122/370**; its true
**32/136/405** target is absent and was never admitted. No entered state is
unstored. Every current split source and raw cofactor is SAT in the separate
reference check; complete structural coverage still requires both children.

Coverage stays **66/83**, with **3 open split records / 2 acquired leaves /
1 pending target**. The union preserves **32 patterns / 3 split records / no
external probe rows**, growing history **434,176 bytes** to **775,811,072 bytes /
42,101 patterns**. The delta is **516,096 SQLite bytes / 23,539 compressed bytes**,
identical across current modes. The index ends with **697 route entries** and
one missing-target link. The positive certificate has **3,360 steps**; reference
evidence preserves all **3,575** prior nodes and contains **3,734**.
The complete producer costs **369.75582 s**, including current restoration
**80.22699 s**, historical restoration **76.75811 s**, and final route preparation
and global coverage **68.84394 s**. Peak RAM and unrestricted-SAT bounds are not
measured or established.

Resume `experiments/results/cnf-pattern-activation/report.json` using
`compare_cnf_pattern_activation.restore_checkpoint`, SHA-256
`7af092282dfda5070c4dbf1006daa8cff22a218487af28e40b59e8dc51894c7c`.
Retain evidence lists **(1, 42, 156, 44, 1)** and **two bridges**, with complete
bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
Resume the exact variable-5 pair; retain the acquired false child and both
other open leaves. Pending source:
`26f134186dbdd90745599fa2d41308823b8c08b752f19d5f53124ffd4ecd73f1`.
Missing true target:
`72697c710335660e1dc9c934e995f7c37577a9226c546fd7233d4e3685cb3615`.
After the maintenance saving, structural discovery and reuse in these remaining
cofactors, plus cold setup/export costs, are the priorities. The alternative
first variable-17 split remains untested.

Validation: independent cold reconstruction passes in **498.30431 s**, checking
all eight matched workers and **3,734 reference nodes** without fresh discovery
or reference solving. Four first-repeat prefixes match complete rebuilt
catalogs, order, closure, next selection and activation counts. All **222 tests**
pass; existing SQLite resource warnings remain in the log. The manuscript
builds to **160 pages**, with no overfull boxes or undefined references and all
**64 previous proof blocks** unchanged. All **22 prior manifests / 1,009
artifacts** and all **3,575 previous reference payloads** remain unchanged.
The new manifest binds **98 artifacts / 4,355,064 bytes**; commands, source
fingerprints and checks are in the checkpoint's `validation.json`.

## 2026-11-14: another conditional Horn branch and interrupted acquisition

[Conditional-frontier resumption](conditional-frontier-resumption.md) finishes
the missing true **32/136/405** branch of the retained variable-5 split in
**11 new states**, reaching a **17/26/62** Horn, zero-valid formula through
probes, binary-path reduction and a polarity change. Its acquired sibling
needs no new admissions but still leads to **31/122/370**. Both structural
obligations remain required; recognizing one branch does not close the source.

The next split uses local variable **2** on that 31-variable residual. Its false
**29/110/329** cofactor takes eight states to reach unresolved **24/88/274**.
Its true **29/115/343** cofactor enters thirteen states before exhausting the
shared allowance. Those thirteen have no stored pattern certificates. Each
repeat therefore enters **32 states / stores 19 / leaves 13 unstored**. Their
exact inputs remain in the operation logs; their shapes are not certified edges.
Two independent repeats reproduce the same operations and persistent results.
Coverage stays **66/83**; there are **4 open splits / 2 acquired leaves /
1 pending target**, including the earlier unresolved **36/144/434** plan.

Mean expansion is **0.25005 s**: selection **0.09339**, acquisition **0.13225**,
maintenance **0.02355** and focus coverage **0.00086 s**. Preparation/export are
**8.06032 / 4.85783 s** and the complete worker costs **13.25993 s**. This is
an identical-policy continuation, not a comparative speedup. Preparation and
export account for roughly 97% of worker time. The full producer costs
**209.79814 s**, including **92.09233 s** restoration and **67.60414 s** final
route preparation plus global coverage. The index ends with **698 routes /
one pending link**; no peak-RAM reduction is claimed.

The union adds **19 patterns / 1 split / no external probe rows**. History grows
**253,952 bytes** to **776,065,024 bytes / 42,120 patterns**. Its delta occupies
**319,488 SQLite bytes / 14,220 compressed bytes**. The positive certificate
remains **3,360 steps**; reference nodes grow **3,734 -> 3,781**.

The code stores a pattern only after its recursive acquisition returns. Thus,
for an unchanged history with a deterministic unary chain of L unrecorded
states and no intervening completed branches, a repeated allowance B < L can
fail before any row is stored on every retry. The linked analysis gives the
induction over retries and the requirements for checked local continuations.
This is a restart-policy limitation, not a SAT lower bound. The current
interruption does not show that its full path exceeds a fresh allowance of 32.

Resume `experiments/results/cnf-conditional-frontier/report.json` through
`continue_cnf_conditional_frontier.restore_checkpoint`, SHA-256
`f55bdcefe556222a5b6043f03591e38f10ad8c76bc3c3c73a8eb45aed73c0ef8`.
Keep evidence **(1, 42, 156, 45, 1)** and **two bridges**. Resume the variable-2
pair of source `09831bee0e0295f91c4d21b79ffe25508d3dad8b48e5052b4bfde74367574914`;
its missing true target is
`944e1c80b727c779838a814ab6d1509ae46b22afbde7e978523bb96c8f0ce859`.
Charge reentry of all unstored inputs, preserve the acquired false branch and
both open leaves, and distinguish pattern recurrence from identical-formula
reuse. Startup/export reuse promises the larger measured runtime saving;
interruption-safe continuations address progress and avoid repeated discovery.

Independent cold reconstruction passes in **305.33218 s**, verifies all
**3,781 reference nodes**, and reproduces global coverage and the next
selection without fresh discovery or reference search. Both stepwise prefixes
match full catalogs, ordering and activation counts. All **222 tests** pass;
existing SQLite resource warnings remain visible in the log. The **161-page**
manuscript builds with no overfull boxes or undefined references, and all
**64 previous proof blocks** remain unchanged. The restart-policy argument is
textual; no new Lean theorem is claimed.

All **23 previous manifests / 1,107 artifacts** and all **3,734 previous
reference payloads** are unchanged. The new manifest binds **40 artifacts /
3,720,830 bytes**, including operation logs, deltas, reference evidence,
structural findings, cost summary, validation metadata and test/build logs.
See `experiments/results/cnf-conditional-frontier/validation.json` for exact
commands and source fingerprints.

## 2026-11-15: export the appended evidence and retain the next conditional family

[The guarded exporter](append-delta-export.md) avoids comparing old payloads
when an exclusively owned, verified history has only appended rows. It checks
schema/data versions, suffix counts, total cardinality and connection-wide
write counts. Counting still touches historical index pages. Independent
certificate checks and full cold reconstruction remain required; the helper
is optional and does not change the frozen discovery implementation.

Two reversed-order repetitions use the same pending pair and shared 32-state
allowance. They produce identical operations and delta bytes. Mean export
falls **4.87738 -> 0.76122 s**, with **0.66334 s** boundary setup charged to
preparation. Complete worker time falls **13.11241 -> 9.92093 s (24.34%)**.
Preparation now costs **8.84331 s** and dominates. The complete comparison
producer costs **228.86791 s**, including **90.58347 s** historical restoration
and **68.23153 s** final route preparation plus global coverage. This is a
matched bounded-expansion result on reused development inputs, not a cold
end-to-end speedup or an arbitrary-SAT complexity bound.

The resumed true 29-variable cofactor closes through **21 new states** to a
**9/16/43 one-valid terminal**, neither Horn, dual-Horn nor 2-CNF. Its chain
contains nine elimination, eight probe and three binary-path nodes. All
thirteen previously unstored inputs are reentered, charged and now stored.
The sibling remains open at **24/88/274**. Its new split leaves both targets
missing: **20/68/198 false** and **21/71/208 true**. Eleven entered inputs
remain unstored. Coverage stays **66/83**, with **five open splits / one
acquired leaf / two pending targets**, including the separate unresolved
36-variable leaf. A SAT model on one branch does not discharge the other
structural obligation.

The union stores **21 patterns / one split / no external probe rows**. History
is **776,331,264 bytes / 42,141 patterns**, growing by **266,240 bytes**. Both
methods retain **327,680 SQLite bytes / 12,754 compressed bytes**. Reference
nodes grow **3,781 -> 3,803**; the positive certificate remains **3,360 steps**.
The activation index has **699 routes / two missing-target links**. There is
no persistent-space saving or measured peak-RAM reduction.

Resume `experiments/results/cnf-append-export-checked/report.json` through
`compare_cnf_append_export.restore_checkpoint`, SHA-256
`81e1c7c0b887277cefa62df011738e73c809a9fef16897ba5238e84bf45732d4`.
Keep evidence **(1, 42, 156, 46, 1)** and **two bridges**. The method note records
both pending target hashes. Priorities are checked startup profiling, resuming
both pending cofactors, and preserving unfinished recognition through checked
local continuations. No new Lean theorem or efficient unrestricted partition
is claimed.

The first attempted comparison rejected immutable legacy tables before
acquisition. Its baseline, rejected implementation and log are preserved under
`experiments/results/cnf-append-export/`; they support no matched speedup.
The corrected helper permits unchanged legacy tables and rejects their writes.

Independent cold replay passes in **365.45167 s**, checks all four workers and
all four intermediate catalogs, and verifies **3,803 reference nodes** without
fresh discovery or reference search. All **229 tests** pass. The manuscript
builds to **161 pages**, with no overfull boxes or undefined references; all
**64 previous proof blocks** are unchanged. All **1,147 artifacts across 24
prior manifests** and all **3,781 prior reference payloads** are preserved.
The new manifest binds **73 artifacts / 3,954,783 bytes**, including the rejected
attempt. Exact commands, source fingerprints, concurrency notes and checks
are in `experiments/results/cnf-append-export-checked/validation.json`.

## 2026-11-15: reuse checked state across bounded expansion batches

[The retained-session study](retained-expansion-session.md) profiles startup
before changing it. Checked route construction takes **7.56459 of 8.83102 s**
in the uninstrumented sample. The helper retains the same verified inventory,
cache and complete maintained catalog across batches. It resets only the
admission ledger after checking write/schema versions, maintenance state,
sidecars and policies. This requires exclusive ownership and immutable old
rows/cached objects. Cold process restart still reconstructs checked authority.

Two reversed-order repetitions compare two consecutive 32-entry batches under
each policy. The mean sum of complete workers falls **23.32780 -> 16.18611 s
(30.61%)**, including initial checking. Both policies enter **64 states**, store
**44 patterns** and produce identical per-batch deltas. Thirteen unfinished
first-batch entries are charged again; seven final entries remain unfinished.
Session retention preserves completed checking, not unfinished recursive work.
The producer separately charges **95.47416 s** historical restoration and
**69.18542 s** final route preparation/global coverage. The retained second
worker still spends **3.69664 s** on preparation; snapshot copying and digests
need separate measurement before the next optimization.

The acquired nodes include conditional **6/7/18 Horn/one-valid/zero-valid** and
**4/3/6 Horn/2-CNF/zero-valid** terminals. Coverage stays **66/83**. The frontier
shrinks to **two open splits / no acquired open leaf / one pending target**.
The remaining **36/144/434** source has an acquired false **31/120/344** child
and a pending true **32/110/308** child. Resume that exact split while preserving
the acquired child. The method note binds source and target hashes.

History grows **540,672 bytes** to **776,871,936 bytes / 42,185 patterns**.
The union adds **44 patterns / two split sidecars / no external probe rows**,
retaining **622,592 SQLite bytes / 22,766 compressed bytes**. Reference evidence
grows **3,803 -> 3,830 nodes**; the positive certificate remains **3,360 steps**.
The index ends with **701 routes / one missing-target link**. Retention extends
cache lifetime and gives no persistent-space or measured peak-RAM reduction.

Resume `experiments/results/cnf-expansion-session/report.json` through
`compare_cnf_expansion_session.restore_checkpoint`, SHA-256
`a9133c94e01789bb80298de290f17177f71ae428f6d827142bd287722dca9793`.
Keep evidence **(1, 42, 156, 48, 1)** and **two bridges**. Further priorities are
the pending conditional branch, separately measured snapshot/cold costs, and
checked local continuation of unfinished recognition. No new tractability or
Lean theorem, compact-state bound or efficient arbitrary-SAT partition is claimed.

Independent cold replay passes in **518.83008 s**, reproducing all eight
workers and their intermediate catalogs without fresh discovery or reference
search. It verifies **3,830 reference nodes**. All **233 tests** pass. The
manuscript builds to **162 pages**, with no overfull boxes or undefined
references; all **64 previous proof blocks** remain unchanged. All **1,220
artifacts across 25 prior manifests** and all **3,803 previous reference
payloads** are preserved. The new manifest binds **101 artifacts / 4,289,703
bytes**, including the startup profile, eight workers, cold replay, structural
findings and test/build logs. The initial failed external-write test fixture
is retained and explained; its correction changes stored bytes rather than
issuing an external no-op update. Exact commands, source fingerprints and
concurrency notes are in
`experiments/results/cnf-expansion-session/validation.json`.

## 2026-11-15: close the retained split without overstating original coverage

[The session-frontier continuation](session-frontier-closure.md) completes the
pending true **32/110/308** cofactor through **29 new patterns**: five probe,
five binary-path, eighteen elimination and one family node. Its **7/21/85**
terminal is one-valid and outside Horn, dual-Horn and 2-CNF. The completed false
branch and its empty-clause refutation are reused. Both independent repeats
stop after one advance in the first 32-entry batch; the second allowance is
unused. All seven previously unfinished entries are reentered and charged.

The enclosing **39/161/495** retained focus closes, leaving no open saved split,
leaf or pending target in that frontier. **Original-input coverage stays 66/83.**
Seventeen originals still have unresolved leaves; case 1062 retains a different
**40/174/541** leaf. Closing the acquired conditional obligations is not a
certificate for every original. The global navigator now selects **39/162/510**
from original **case 1120** (retained index **22**), with `learning_clear`
status, ordinary-probe offset twelve and no pending split.

Mean complete-worker time is **12.41063 s**, with **12.16111 s** preparation
(including **7.38139 s** initial checked session setup), **0.15429 s** expansion
and **0.01920 s** append export. Acquisition alone is **0.08840 s**. The producer
costs **221.94795 s**, including **99.77114 s** restoration and **70.02150 s**
final route preparation/global coverage. These are repeated discovery runs,
not competing implementations or a new speedup measurement. Profiling cold
restoration and the remaining snapshot preparation costs is still warranted.

The union retains **29 patterns / no new split sidecars / no external probe
rows**. History grows **364,544 bytes** to **777,236,480 bytes / 42,214 patterns**.
The delta occupies **438,272 SQLite bytes / 15,542 compressed bytes**. The
reference archive stays at **3,830 nodes**, the global positive certificate at
**3,360 steps**, and the live index at **701 routes / zero missing-target links**.
No memory reduction, compact-state bound or efficient arbitrary-CNF guarantee
is established. Conditional recognition of the existing all-true family does
not bound the work of finding comparable reductions for other inputs.

Resume `experiments/results/cnf-session-frontier/report.json` through
`continue_cnf_session_frontier.restore_checkpoint`, SHA-256
`8349c88556f684eaaed5d0ea296e465cddf85086c2d240d30644ecb2e7436625`.
Preserve evidence **(1, 42, 156, 48, 1)** and **two bridges**. Choose the source
from its bound `next_selection` archive; the report's `source` is the completed
focus and must not be reused as the next expansion target. The selected key is
`4270b94e85e15c2b76fb43fe6a320f98d3908c0020fa3a27e6daf5404c3831f5`.
The next investigation should retain this binding to an uncovered original,
inspect reusable interactions and saved alternatives, and distinguish local
closure from an original-input coverage gain.

Independent cold replay passes in **346.50085 s**, reproducing both workers
and every intermediate catalog without fresh discovery or reference search.
It checks all **3,830 reference nodes**, verifies both cofactor results and
confirms the seven previously interrupted states are now stored. All **233
tests** pass. The manuscript builds to **162 pages**, with no overfull boxes
or undefined references; all **64 previous proof blocks** are unchanged.
All **1,321 artifacts across 26 prior manifests** and all prior reference
payloads are preserved. The reference archive and global positive certificate
are byte-identical to the parent. The new manifest binds **40 artifacts /
4,103,023 bytes**, including the local/global frontier distinction and the
negative exact-overlap check on the next 32 candidate targets. Commands, source
fingerprints and concurrency notes are in
`experiments/results/cnf-session-frontier/validation.json`.


## 2026-11-15: signed-renaming exclusions and case-1120 expansion

The [new investigation](signed-renaming-filter.md) implements and checks a
necessary invariant for signed variable renaming. All 32 saved candidate
targets have different profiles: all 496 pairs are excluded, including the
three pairs with matching size counts. Equality is inconclusive; tests retain
a nonisomorphic equal-profile counterexample. Exclusion does not decide SAT,
rule out semantic equivalence, or justify efficient solving of every class.
The audit takes 0.03586 seconds including writing and changes no scheduler.

Two independent retained sequences each enter 64 states across two allowances,
store 54 patterns and reach a 5/4/9 Horn, zero-valid terminal. One first-batch
interruption is reentered and completed; nine final inputs remain unstored.
Coverage stays 66/83. The pending 25/96/309 split has targets 23/89/277 and
22/73/215. Resume it from `cnf-original-1120/report.json` using
`continue_cnf_original_1120.restore_checkpoint`, preserving evidence
(1, 42, 156, 54, 1) and two bridges. The linked record binds exact source and
report hashes and separates the pending selection from original case 1120.

Mean summed workers cost 18.01738 seconds, with 16.81073 seconds of preparation
and 0.91088 seconds of expansion. History grows 749,568 bytes to 777,986,048 bytes
and 42,268 patterns; the new delta is 38,073 compressed bytes. The reference
archive grows to 4,114 nodes with all 3,830 prior payloads preserved. The global
positive certificate remains byte-identical. Next priorities are convergence
after checked reduction, remaining preparation/cold costs, and checked local
continuations if repeated unfinished frames become dominant. No new speedup,
peak-memory saving or arbitrary-SAT complexity bound is asserted.

Independent cold reconstruction passes in **419.43195 seconds**, reproducing
both sequences and every intermediate catalog without fresh discovery or
reference search. All **238 tests** pass. All **1,361 prior artifacts / 27
manifests** and **3,830 previous reference payloads** remain unchanged. Cold
findings also identify actual reuse after reduction: an inherited two-variable
plan and the empty-CNF terminal, distinct from the newly recognized Horn
terminal. The manuscript preserves all 64 proof blocks and builds to 163 pages
without overfull boxes or undefined references. The checkpoint manifest and
`validation.json` bind the audit, results, source fingerprints and checks.


## 2026-11-15: mixed conditional terminals and preparation profile

The [new continuation](reduction-reuse-profile.md) resumes the exact pending
25-variable split inside case 1120's original-bound focus. It stores 35 patterns
and reaches a 7/7/19 zero-valid terminal outside Horn, dual-Horn and 2-CNF, plus
a 6/6/12 2-CNF terminal outside Horn, dual-Horn and both uniform-assignment
classes. The conditional pair closes; the enclosing focus remains open and
coverage stays 66/83. The next saved pair is 34/120/355, with pending targets
31/102/295 and 31/104/295. Sixteen first-batch interruptions are charged again;
thirteen final inputs remain unstored.

Ordinary workers cost 17.86459 seconds, including 17.31958 seconds preparation
and 0.34281 seconds expansion. A separate instrumented repetition locates the
remaining second-batch cost: 3.78143 of 4.78940 seconds recomputes all eight table
digests. Profiling timings are diagnostic, not a comparative speedup. Investigate
per-table costs and checked reuse of unchanged digests; changed tables and
cold authority still require validation. A key-ordered digest cannot generally
be updated by hashing newly appended rows alone.

History grows by 430,080 bytes to 778,416,128 bytes / 42,303 patterns. The union
delta occupies 18,876 compressed bytes and adds one split sidecar. All previous
reference payloads are preserved; reference nodes grow to 4,153. The global
positive certificate stays byte-identical. Resume `cnf-reduction-reuse/report.json`
through `continue_cnf_reduction_reuse.restore_checkpoint`, preserving evidence
(1, 42, 156, 55, 1) and two bridges. The linked record supplies source hashes,
commands, profile data, limitations and the distinction between focus and pending
interaction. No efficient arbitrary-CNF guarantee is inferred.

Independent cold replay passes in **417.85190 s**, checking every intermediate
catalog with fresh discovery and reference search disabled. It verifies all
**4,153 reference nodes**, preserves all **4,114 prior payloads** and all
**1,428 artifacts / 28 prior manifests**, and confirms exact reuse of the sixteen
completed false-cofactor certificates. All **238 tests** pass; the manuscript
builds to **163 pages** with all **64 previous proof blocks** unchanged. The
checkpoint manifest binds **65 artifacts**, with commands and limitations in
`validation.json`.

## 2026-11-15: live digest scans and closure of original case 1120

The [matched digest study](guarded-table-digests.md) resumes the 34/120/355 split
and closes the original-bound focus in one 32-entry batch. Six independent arms
(two reversed-order repetitions of copied full, live full and guarded live scans)
store identical patterns: 15 probe, 8 elimination, 6 binary-path, 2 family and
1 polarity. Coverage rises 66/83 to 67/83; no admitted input remains unstored.
History grows 405,504 bytes to 778,821,632 bytes / 42,335 patterns. The next open
original is case 1061, index 13, with source 39/167/519 and no pending split.

Mean copied/live-full worker costs are 12.68940/8.55304 seconds. Both hash every
row; this measures the effect of reading the owned database, not cached hash
reuse. The focus closes before any second expansion batch. A separate replay
of the exact append reuses seven unchanged tables but shows no average refresh
improvement (0.42716 guarded versus 0.42444 seconds full), with slower complete
sequences (6.22119 versus 4.71509 seconds). Preserve the regression. Favor live
full scans and investigate retaining the checked session across originals;
startup still consumes about 7.54 seconds and global preparation/coverage 69.47
seconds. Guarded initial count scans remain a smaller, explicitly charged overhead. No polynomial arbitrary-SAT or minimum-expansion result.

Resume `cnf-guarded-digests/report.json` via
`compare_cnf_guarded_digests.restore_checkpoint`; use `next_selection` because
`source` is completed. Detailed bounds, preconditions and validation are in the
linked investigation and checkpoint artifacts.

## 2026-11-15: checked state across original cases closes case 1061

The [original-transition comparison](original-session-handoff.md) replays the
completed case-1120 query, checks the binding to case 1061 and then compares
restarting with retaining that checked session. Two reversed-order repetitions
per method each store the same six probe patterns. Their two conditional chains
reach an inherited empty-clause contradiction. Coverage rises **67/83 -> 68/83**;
all admissions are complete. The raw new patterns are neither Horn, dual-Horn nor
2-CNF and accept neither uniform assignment. This is checked reduction to shared
contradiction evidence, not a new claim of tractability for their raw class.
The conditional residual is UNSAT, while original case 1061 has an independently
checked SAT model. Completing that residual covers one obligation of the original;
it does not refute the original formula.

Mean complete sequence time falls **18.99400 -> 11.61121 seconds (38.87%)**,
including the initial construction, stored-original query, original binding and
expansion. Worker-only time falls **8.56483 -> 0.94843 seconds**; this excludes
the common initial query. Retention ends with **3,100 / 108** checked pattern and
prepared objects, versus **2,453 / 11** after restart. Those separate cache counts
are not peak RAM. Persistent evidence is identical between methods. History
grows **77,824 bytes** to **778,899,456 bytes / 42,341 patterns**. The union delta
is **7,095 compressed bytes**; reference nodes increase **4,198 -> 4,413** and
positive coverage steps **3,518 -> 3,564**.

The next large live cost is global recomposition and navigation: final route
preparation plus coverage takes **69.64522 seconds**, versus **0.14447 seconds**
mean retained local expansion. Compare `CoverageIndex` with full composition on
exact appends, including complete catalog changes, implicit rules and pending
activation. The current transition consumes an already checked global selection;
it does not maintain that selector incrementally. Parent replay remains a
separate **119.01318-second** cold cost. No global minimum-expansion or uniformly
polynomial arbitrary-CNF guarantee follows.

Resume `cnf-original-handoff/report.json` through
`compare_cnf_original_handoff.restore_checkpoint`, preserving evidence
**(1, 42, 156, 56, 1)** and **two bridges**. Follow `next_selection`, since the
report's `source` is completed: **40/158/467**, original **case 1443**, retained
index **72**, no pending split. The linked record supplies exact source and
report hashes, costs, contracts and validation commands.

Independent cold replay passes in **514.17263 seconds**, reproducing all four
arms without fresh recognition or reference search and checking all **4,413
reference nodes**. All **4,198 prior reference payloads**, **1,567 artifacts /
30 prior manifests** and **91 historical source files** are unchanged. All
**249 tests** pass; the manuscript builds to **164 pages** with **64 previous
proof blocks** preserved. The new manifest binds **67 artifacts**. Cold validation
overlaps other checks and is not a speed comparison. The validation record also
preserves the corrected interpretation: conditional refutations do not imply
that the original is UNSAT; its SAT model is independently checked.

## 2026-11-15: retained global inventory and indexed original selection

[The global navigation comparison](indexed-original-navigation.md) replays the
saved six-pattern append without new acquisition. Retaining the checked inventory
reduces the complete measured two-query sequence **138.45321 ->
75.96089 seconds (45.14%)**, including initial
construction and both original selections. The final query alone falls
**65.45308 -> 1.40345 seconds**.
Most of the old cold global cost is repeated semantic checking.

**Next cost to remove:** complete route rebuilding still costs **1.12777 of
1.40345 seconds (80.36%)** in the warm full query. Original selection costs only
**0.07732 seconds**. Reuse the existing complete route-maintenance state during
fresh bounded expansion and global queries; do not prioritize more selector
micro-optimization. The index reduces graph visits (26,109 to six option-source
checks across two graphs), but it adds retained state and changes selection time
only slightly. All methods end with **20,270 / 2,916** checked pattern/prepared
objects; indexes additionally retain **13,055 / 13,054-node** graphs.

The new indexed selector preserves exact selections and uses full composition
for sources outside its original graph. Both indexed updates check only
**6 option sources**, but complete-sequence results against retained
full composition are mixed: **74.19371/73.95375 seconds** in the first repetition
and **75.46496/77.96803 seconds** in the second (indexed/full). Keep the index
optional. A mean from two variable observations does not establish a stable
net benefit or reduced peak RAM. Coverage remains **68/83**; this is replay of
previous work, not a newly completed original.

Resume fresh discovery from **`cnf-original-handoff/report.json`** using
**`compare_cnf_original_handoff.restore_checkpoint`**. Next is **40/158/467**,
original **case 1443**, retained index **72**, no pending split. Preserve evidence
**(1, 42, 156, 56, 1)** and **two bridges**. Keep the inventory and complete
maintained routes alive through a bounded sequence of new expansions and global
queries. Cold reconstruction, initial global checking and growth of retained
state remain open; no unrestricted-SAT efficiency bound follows.

Independent cold validation passes in **259.30996 seconds**, checking all
**twelve selections and coverage certificates** with the original algorithms on
fresh inventories and verifying all **4,413 reference nodes**. The copied
scheduler bodies match their frozen baseline after reversing only the closure
calls and extra argument. All **254 tests** pass; the manuscript builds to
**165 pages** with all **64 previous proof blocks** unchanged. All **1,634 prior
artifacts / 31 manifests** and **95 historical source files** are preserved.
The new manifest binds **32 artifacts**. Validation tasks overlapped, so cold
elapsed time is not a performance comparison.

## 2026-11-15: share maintained routes with global queries

[Maintained global queries](maintained-global-catalog.md) reduce mean updated
query time **1.52633 -> 0.23719 seconds (84.46%)** while performing the same
full composition, plan checks and original selection. Both methods retain the
same inventory and route maintenance; the baseline rebuilds another catalog.
The **complete short sequence regresses 70.96985 -> 71.79572 seconds (1.16%)**:
initial checking varies more than the warm-query saving. Preserve that result;
measure longer retained sessions before claiming a total-cost improvement.

Fresh expansion stores **27 patterns** and closes the selected residual of
**case 1443**. One cofactor reaches an inherited contradiction after two probes;
the other uses 25 new nodes, interleaving binary-path reductions, elimination
and probes before a polarity change exposes a **Horn, zero-valid** terminal.
Coverage stays **68/83**: other original obligations remain. This shows a
composable reduction chain, not a new tractable class for every CNF.

**Next discovery target:** **40/163/490**, original **case 1190**, index **31**,
no pending split. Keep the checked inventory and complete maintained catalog
alive across several such residuals, measuring startup amortization. Investigate
repeated reduction chains using exact certified edges, not shape similarity.
**Largest complete-cost gap:** parent restoration **124.46543 seconds** and
initial global checking/construction **67--69 seconds**; cold final coverage
is **71.74615 seconds**. These dominate the remaining **0.23719-second** warm
query. Positive-only stored proofs cannot certify negative frontier claims.
Within the first retained worker, preparation costs **1.04254 seconds** versus
**0.22849 seconds** local expansion; full-table digests alone cost **0.48173
seconds**, and a complete seed copy remains. Compare removing redundant
copying under the checked append boundary before further query tuning; retain
the earlier append-time guarded-digest regression.

Resume **`cnf-session-catalog/report.json`** using
**`compare_cnf_session_catalog.restore_checkpoint`**, report SHA-256
`f856409b5a58b402ccf6f545dc8570cae22952a79b2b06460a8f68ab2635e10b`.
Use `next_selection`, not the completed `source`. Evidence is
**(1, 42, 156, 57, 1)** with **two bridges**. History is **779,272,192 bytes /
42,368 patterns**, up **372,736 bytes**; delta **438,272 bytes / 20,280 compressed**.
Both methods end with **710 routes**, no pending targets, and
**20,297 / 2,916** checked pattern/prepared objects. Catalog sharing adds no
persistent index; peak RAM is unmeasured. Reference nodes grow **4,413 -> 4,481**;
positive coverage stays **3,564 steps**. Guards preserve acquisition ledgers and
reject stale authority, but rely on immutable caller-owned cached objects.

All **259 tests**, independent replay of **eight global queries**, prefix
catalog checks and reference validation pass; all **64 previous proof blocks**
are preserved. The detailed validation record binds previous artifacts and
sources. No unrestricted-SAT complexity or minimum-expansion bound follows.

## 2026-11-15: batch copies and continued conditional discovery

[The batch-copy comparison](expansion-without-batch-copy.md) stores **82 new
pattern records** across four bounded expansions: 30 eliminations, 27 probes,
17 binary-path reductions, three family terminals and five unresolved records.
The terminals include Horn/zero-valid and 2-CNF cases, but overall coverage stays
**68/83**. The sequence charges **105 admission entries**, including re-entry;
twelve final entries remain unstored. Recognized endpoints do not imply cheap
recognition or acquisition of every ancestor.

**Retain the negative result:** omitting all per-batch seed copies avoids
**3,118,911,488 logical copied bytes**, yet mean four-worker time regresses
**4.61350 -> 6.28484 seconds (36.23%)** and the complete sequence regresses
**75.23972 -> 77.78679 seconds (3.39%)**. Both methods still hash all historical
tables and retain identical evidence. The first digest without a copy takes
about **3.28 seconds**, versus **0.44--0.50 seconds** after copying; later scans
are similar. OS/cache causality is unmeasured. Keep the copied-seed default;
test copying the first batch only during subsequent fresh discovery. That
combined policy has not been measured and cannot inherit a speedup by adding
times from separate runs.

**Resume** `cnf-copyless-sequence/report.json` with
`compare_cnf_copyless_sequence.restore_checkpoint`, report SHA-256
`0cf43154fba97eae8b971d700b7381fa671d2347aac4f45a41300ad208e1dcfd`.
Use **`next_selection` with its pending split**, at **26/94/284**, not the initial
`source`. Preserve evidence **(1, 42, 156, 63, 1)** and **two bridges**. Initial
binding is original **case 1190, index 31**; retained selections have an empty
original-index list. Cold validation checks actual dependency ancestry rather
than inventing a selector binding. Such a path does not transfer SAT truth or
complete the original's other obligations.

**Largest total-cost gaps:** initial global checking/construction remains
**67--69 seconds**, parent restoration **129.01658 seconds**, and final cold
coverage **71.31630 seconds**. Warm query cost is only **0.25 seconds**, plus
**0.31 seconds** output serialization. Reuse the checked session, then investigate
complete cold authority and resumable unfinished work. Persisted positive
coverage alone cannot certify the unresolved frontier. For broader discovery,
track certified reduction chains and the interaction left after each terminal,
not just family labels or matching shapes.

History grows **1,085,440 bytes** to **780,357,632 bytes / 42,450 patterns**;
the union delta is **1,175,552 bytes / 52,938 compressed**. Both methods retain
**20,379 current / 2,916 prepared checked objects**, with no measured peak RAM.
Reference nodes grow **4,481 -> 4,750**. Failure-only archives preserve committed
rows as explicitly unchecked evidence and cannot become verified checkpoints.
All **266 tests**, independent acquisition-prefix and twenty-query replay, and
reference validation pass. No unrestricted-SAT or minimum-expansion bound follows.

## 2026-11-15: checked canonical order and the next original

[Checked canonical-source reuse](checked-canonical-sources.md) closes
**case 1190**, raising structural coverage **68/83 -> 69/83**, and stores **25
new records**. Twelve eliminations, seven binary-path reductions, four probes,
one polarity change and one Horn/zero-valid terminal complete the pending split.
The terminal has **8 variables / 10 clauses / 27 literals**. All twelve formerly
unstored states now have records; the batch enters and stores 25 states.

The new representation check avoids sorting and renaming only after scanning
the source and proving that its order and compact labels already satisfy the
old normal form. It keeps exact keys, maps, certificate policy and stored bytes;
other sources fall back to the original normalizer. No retained cache is added.
Two reversed-order repetitions reduce the **complete startup-and-expansion
sequence 71.96107 -> 68.45498 seconds (4.87%)**; initial global preparation drops
**69.51709 -> 65.98742 seconds (5.08%)**. These are development-case measurements,
not a held-out or unrestricted-SAT guarantee. Both methods keep the batch copy;
the preceding copy-removal regression remains unchanged.

**Next discovery target:** **40/165/494**, original **case 1227**, retained index
**38**, no pending split. Resume **`cnf-canonical-source/report.json`** with
**`compare_cnf_canonical_source.restore_checkpoint`**, report SHA-256
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`.
Use **`next_selection`**, not the completed `source`. Keep evidence
**(1, 42, 156, 63, 1)** and **two bridges**. The restorer and independent replay
still use the original normalizer; the new inventory is an optional equivalent
implementation for subsequent comparisons and discovery.

**Largest remaining costs:** parent restoration **134.48837 seconds** and
initial global checking still dominate. A cold profile places normalization
at about **20% of instrumented query time**; unit fixed-point reconstruction
is the larger individual primitive. Investigate repeated source-bound checking
and sharing of immutable structure before expanding caches. The existing probe
cache evicts often, but repeated use of those evicted keys has not been measured.
Check whether already validated authority can survive restoration into startup.
A positive certificate does not establish complete negative frontier information.

The candidate accepts **28,169 / 48,182** canonicalization calls and still pays
**20,013** fallbacks. It replaces 11,031,610 old-normalizer input-literal charges
but adds 16,666,740 precheck visits; these counts are not a total CPU-work saving.
History grows **319,488 bytes** to **780,677,120 bytes / 42,475 patterns**. Delta:
**380,928 bytes / 14,120 compressed**. Both methods retain **20,404 / 2,916**
checked current/prepared objects; peak RAM is unmeasured. Reference nodes grow
**4,750 -> 4,802**. All **274 tests**, independent eight-query/prefix replay and
reference checking pass. No previous proof blocks or experiment sources change.

## 2026-11-15: retain checked evidence through replay

[Checked checkpoint replay](checked-checkpoint-replay.md) removes repeated node
verification across the latest five append checkpoints and their startup query.
Two reversed-order runs reduce **replay plus startup 94.29444 -> 87.70659 seconds
(6.99%)**. Suffix replay falls **28.92930 -> 24.22978 seconds (16.24%)**; startup
falls **65.36514 -> 63.47681 seconds (2.89%)**. Node verifications fall
**28,059 -> 23,320**, avoiding **4,739 repeats (16.89%)**. Both arms keep full
archive/source identity checks, ten full table-digest scans, all delta/positive
checks and the complete global query. These are development-history observations.

The live verifier carries exact checked immutable dependencies through guarded,
conflict-checked appends. Failed appends roll back and invalidate it. External
changes, unexplained own-connection writes and policy/schema changes reject reuse;
exclusive file/connection ownership and immutable Python cache objects remain
requirements. No trust cache is persisted. Positive coverage does not establish
complete negative frontier information, so startup still builds and queries the
complete catalog. The fresh control uses the same merge guards and discards
verifiers between phases; the independent audit uses the frozen old restorers.

There are **no new pattern rows or coverage gains** in this replay experiment.
History remains **780,677,120 bytes / 42,475 patterns**, structural coverage
**69/83**, and reference evidence **4,802 nodes**. The candidate carries **1,027**
checked nodes into startup. Both arms finish with **23,320** checked nodes, also
their maximum recorded count. This is not a process-RAM measurement; retaining
objects longer and auxiliary caches still cost memory. All **283 tests** pass.

**Next priority:** resume structural discovery on **case 1227, index 38**, at
**40 variables / 165 clauses / 494 literals**, with no pending split. The verified
acquisition checkpoint remains **`cnf-canonical-source/report.json`**, SHA-256
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`; use its
**`next_selection`** and **`compare_cnf_canonical_source.restore_checkpoint`**.
Keep evidence **(1, 42, 156, 63, 1)** and **two bridges**. This run changes replay
machinery only, so it does not replace that acquisition checkpoint.

Cold startup still costs about **63.48 seconds**; older parent restoration is
separate (observed **114.50 seconds**, overlapping tests before measured arms).
Extend checked reuse into earlier checkpoint schemas only after verifying their
contracts. A further specific gap is repeated expanded-certificate traversal and direct
semantic rule checking: later positive checks still cost about **2.6 seconds** even when they verify
zero new inventory nodes. Measure source/evidence binding and decoding before
adding another cache. Current evidence supplies no unrestricted-SAT bound.

## 2026-11-15: conditional refutation and shared terminals

[Conditional refutation with a shared terminal](conditional-refutation-reuse.md)
closes **case 1227**, raising structural coverage **69/83 -> 70/83**. A saved
split exposes two chains of three and two new probe reductions. Both reach the
same existing contradiction terminal. Two independent runs store the same
**five new records** in one advance, with no interrupted admissions. This is
exact terminal reuse and a new covered original, not a new tractable SAT class.

Mean local expansion costs **0.15935 seconds**, the complete worker **1.18892
seconds**, and the full sequence **68.83255 seconds**. Initial construction,
global checking and serialization still cost **66.68418 seconds**; the separately
charged parent restore is **140.08953 seconds**. These repeated development runs
do not establish a speedup against another solver. Structural history grows
**73,728 bytes** to **780,750,848 bytes / 42,480 patterns**. Reference evidence
grows **4,802 -> 5,182 nodes**, adding **3,702,784 SQLite bytes**; that validation
cost remains separate from the structural delta. Peak RAM is unmeasured.

**Next discovery priority:** **case 1406, index 64**, **40/168/505**, no pending
split. Resume **`cnf-case1227/report.json`** with
**`continue_cnf_case1227.restore_checkpoint`**, report SHA-256
`240f8151528c19ef69cac3b958abfc489710ffa1961944799d957545ff10f722`.
Use **`next_selection`**, not the completed `source`. Preserve evidence
**(1, 42, 156, 64, 1)** and **two bridges**. Thirteen originals remain unresolved.

Cold checking remains the dominant measured cost. Continue discovery through
retained sessions where possible; extend checked replay only with its exact
source, policy and immutable-dependency guards. Similar reduction chains do not
supply proof transport between different CNFs, and a short refutation on this
case supplies no uniform acquisition bound for arbitrary SAT.

## 2026-11-15: retained discovery across original scopes

[Discovery across retained original scopes](retained-discovery-sequence.md)
raises structural coverage **70/83 -> 72/83**, covering **cases 1406 and 1195**
before continuing into **case 1062**. Two independent four-batch runs store the
same **63 records**: 19 probe reductions, 27 eliminations, 13 binary-path
reductions, one family terminal and three unresolved records. They charge **74
admission entries / 71 distinct inputs**; three entries repeat interrupted work,
and eight inputs still have no stored record.

The first two selected residuals are UNSAT, while their original formulas are
SAT. Their checked paths include earlier conditioning, so local refutation does
not transfer SAT truth to the original. A later **4/5/14** terminal is both
zero-valid and one-valid, but neither Horn nor 2-CNF. It does not close case 1062's
remaining branches. Classification coverage and SAT decision remain distinct.

Mean four-batch sequence time is **73.47861 seconds**, including **66.09003
seconds** initial catalog/global checking, **4.17511 seconds** workers and
**1.02047 seconds** local expansion within those workers. The shared parent
restore costs another **145.39246 seconds**. One paid startup now serves all four
batches; no matched fresh-per-batch comparison or universal speedup is claimed.
History grows **856,064 bytes** to **781,606,912 bytes / 42,543 patterns**.
Reference evidence grows **5,182 -> 5,488 nodes**; peak RAM remains unmeasured.

**Next priority:** resume the pending split at **19/77/261**, within **case 1062,
index 14**. The selector's original-index list is empty for this retained work;
independent dependency-path checking supplies the scope. Resume
**`cnf-retained-discovery/report.json`** with
**`continue_cnf_retained_discovery.restore_checkpoint`**, report SHA-256
`0d59f8bb3018c78b5da947a31d1a0d492103c15968df7d706b7ad1910b038f84`.
Use **`next_selection` and its pending split**, not the initial source bound to
case 1406. Preserve evidence **(1, 42, 156, 69, 1)** and **two bridges**.

The touched prefixes have **75 occurrences / 64 distinct records**. Within
these prefixes across three original scopes, only the inherited contradiction terminal is shared;
**none of the 63 new records is shared across scopes**. This limits the current
cross-input reuse claim. Eleven originals remain uncovered. Continue the mixed reduction chains and
measure whether any nonterminal identities or exact boundary summaries can be
shared; matching reduction names alone is not such reuse. Keep unsuccessful
choices and eight interrupted input identities. Cold reconstruction and checking
remain the largest costs, and support further guarded reuse or a verified
materialized checkpoint. No compact closure or polynomial acquisition bound for
arbitrary SAT follows from these observations.

## 2026-11-15: materialized checkpoint reuse

[Materializing a checked checkpoint](materialized-checkpoint-reuse.md) reduces
measured reconstruction **155.45916 -> 9.94660 seconds**.
Including a fresh complete catalog and global query, mean startup falls
**220.33037 -> 74.76157 seconds (66.07%)**.
Two reversed-order repetitions reconstruct byte-identical databases, retain all
five evidence groups and two bridges, and select the same pending split.
This is a checkpoint-reuse result; structural coverage remains **72/83** and no
new patterns or reference proofs are acquired.

The optional compressed snapshot adds **87,337,082 bytes** of local disk storage.
Publication from an already checked history costs **7.88791 seconds**; a
separate authoritative reconstruction costs **150.88545 seconds**.
Both are charged. The fast path checks the complete database byte identity
before opening SQLite, all logical table digests, code/policy/parent bindings,
all sidecar bytes, bridges and the positive coverage proof. Complete catalog and
negative-frontier checking remain separate, paid startup work. A hash is useful
only relative to the descriptor bound by the reviewed experiment report.

**Next priority:** use the optional restorer in
`experiments.cnf_materialized_resume.restore_checkpoint` with
`experiments/results/cnf-materialized-checkpoint/report.json`, or the unchanged
`continue_cnf_retained_discovery.restore_checkpoint` with the acquisition report.
The final entry point additionally checks all **125 historical source fingerprints**;
this separately measured guard costs **0.01286 seconds**. All **299 tests** pass.
Both return the same acquisition state. Resume its **`next_selection` plus
pending split at 19/77/261**, case **1062 / index 14**, whose selector original-index
list remains empty. Preserve evidence **(1,42,156,69,1)**, **two bridges** and the
**eight interrupted input identities** in the acquisition artifacts. Eleven
originals remain structurally uncovered. With reconstruction reduced, complete
startup checking (64.49429 seconds) remains the largest repeated
cost; keep one checked session across further discovery batches. Investigate
shared nonterminal or boundary descriptions in the pending mixed reductions.
No compact closure or uniformly polynomial acquisition bound is established.

## 2026-11-15: complete the pending mixed reductions

[Completing the pending mixed reduction chains](pending-discovery-closure.md)
closes **case 1062**, raising structural coverage **72/83 -> 73/83**. Two independent
four-batch runs store the same **68 records**: 23 probes, 22 eliminations, 13 binary-path
reductions, three polarity transformations, five family terminals and two unresolved
intermediate records. They charge **84 admission entries / 68 distinct inputs**;
16 entries repeat interrupted work inside this sequence. All **eight earlier
interrupted inputs** and all newly interrupted inputs are now stored.

Three polarity transformations expose Horn terminals without reducing variables,
clauses or literals: **8/10/23**, **14/17/43**, **6/6/16**. A separate **9/18/49**
terminal is all-zero satisfiable but neither Horn nor 2-CNF. These are applications
of existing checked rules, not new tractable classes. The first 19-variable branch
closes before another 36-variable branch is selected; selected size alone is not
monotone progress. Original coverage requires all outstanding structural premises.
The original and all four touched split sources are **SAT**; classification coverage
is separate from SAT decision.

Mean complete sequence time is **70.46120 seconds**, including
**63.74848 seconds** startup and **0.84877 seconds** local
expansion. Checked materialized parent restoration adds **8.70349 seconds**.
History grows **843,776 bytes** to **782,450,688 bytes /
42,611 patterns**; reference evidence grows **5,488 -> 5,612 nodes**. Peak RAM is
unmeasured. Repetition establishes reproducibility, not a matched speedup.

**Next priority:** **case 1121 / index 23**, **41/174/513**, no pending split.
Resume **`experiments/results/cnf-pending-discovery/report.json`** with
**`experiments.continue_cnf_pending_discovery.restore_checkpoint`**. Use
**`next_selection`**, not the completed initial 19-variable source. Preserve evidence
**(1,42,156,72,1)** and **two bridges**. Its default restorer uses the existing checked
materialization of its parent and then applies the new delta; independent audit
uses the original reconstruction chain with that cache disabled.

Touched prefixes reuse **two probe records and one contradiction terminal** from
the preceding case-1062 prefixes. The intersections with earlier cases 1195 and
1406 contain only that terminal. This supports reuse within a resumed original,
without establishing shared nonterminal representations between different inputs.
Across the six case-1062 batches in both checkpoints, **148 entries / 121 distinct
inputs** expose **27 repeated admissions**. All 121 records are now stored; preserving
unfinished control frames remains a possible way to avoid re-entry, with runtime
benefit still unmeasured. Ten originals remain uncovered. Continue discovery in a retained
session and measure actual shared identities or certified boundary descriptions.
No compact closure or uniformly polynomial arbitrary-SAT acquisition bound follows.

## 2026-11-15: a pending branch survives a complete admission ledger

[The next mixed-family sequence](case1121-discovery.md) closes cases 1121 and
1336, raising structural coverage to **75/83**, and stores **67 records**.
All 67 admitted inputs are eventually stored, yet case 1063 retains a pending
**22/89/309** split whose second branch has admitted zero inputs. Completed
serialization is not complete structural expansion. Preserve the pending split
alongside interrupted input identities. The same run checks a **14/16/34 ->
13/14/30** affine projection, including exhaustive boundary-model comparison.
History grows **913,408 bytes**; separate reference evidence grows **5,423,104 bytes**.
Resume the new `cnf-case1121-discovery` checkpoint's `next_selection` in a retained
session. Eight originals remain uncovered; neither cross-original boundary sharing
nor uniformly polynomial acquisition is established. Full costs, replay evidence
and preservation anchors are in the linked record.

## 2026-11-15: retained branches complete three more originals

[The case-1063 continuation](case1063-discovery.md) raises structural coverage
**75/83 -> 78/83**, completing cases 1063, 1371 and 1158 with **54 new records**.
Case 1063 needs three additional records after fifty had been stored; all nine
inputs interrupted later in case 1371 are also completed. Horn/2-CNF overlap and
a polarity transformation into Horn remain explicit. Case 1158's selected residual
is UNSAT while its original is SAT, preserving the need for checked conditioning
ancestry. History adds **733,184 bytes**, separate reference evidence **3,682,304 bytes**.
The next source is **1196 / index 36**, **43/181/549**, no pending split. Follow the
new checkpoint's `next_selection`. Five originals remain uncovered; exact prefix
reuse, full costs and validation are in the linked record. Coverage of this retained
corpus remains distinct from generalization to new CNFs and an arbitrary-SAT bound.

## 2026-11-15: the retained 83-source subset is complete

[The case-1196 sequence](case1196-completion.md) raises checked structural coverage
**78/83 -> 83/83**, using six batches with the existing per-batch limits. Both
repetitions store **144 records** on **147 admissions**; all interrupted inputs
are completed and the final source selection is null. Four small terminals and
two polarity maps pass exhaustive bounded checks. All 83 source formulas exactly
match the historical retained-policy misses, so this is development-set completion,
not a fresh holdout or a new full-corpus measurement. History adds **2,019,328 bytes**;
separate reference evidence adds **15,405,056 bytes**. Restore the completed
`cnf-case1196-discovery` checkpoint for combined-policy full-corpus checking and
then frozen-policy evaluation on new unlabelled inputs. Do not restart an old
pending source. Certified sharing beyond terminals, paid trace acquisition and
generalization remain open; no arbitrary-SAT polynomial bound follows.


## 2026-11-15: checked union of the full historical corpus

[The explicit policy union](full-corpus-coverage.md) checks **1,497/1,497 historical
inputs**, including **985/985 non-tiny cases**, without acquiring new states. Every
source is bound to its own policy configuration and positive proof. Four fresh
processes pass; all **306 tests** pass. Mean replay is **46.48527 s** with historical
restoration and **11.22907 s** from an **11,271,594-byte compressed** standalone
bundle. Historical acquisition remains charged; the bundle adds storage and
cannot resume expansion. Peak RAM is unmeasured.

The old successful set shares **67 nonterminal steps** up to eighteen variables
after duplicate roots are collapsed, whereas the old/new policy proofs share
only twenty tiny family steps. The next experiment should test whether these
larger edit-family components reduce acquisition on unseen edits and mixtures
under a frozen policy and budget. This closes the combined historical-replay gap,
not generalization, globally minimal expansion or unrestricted polynomial SAT.


## 2026-11-15: transfer control separates reuse from early family exposure

[The 42-input study](subsumption-transfer-controls.md) finds that the candidate
shared eighteen-variable source reduces to 2-CNF. Twelve template transfers are
valid, but an early-family control needs no template and bypasses probing on
33 inputs. Coverage remains **41/42**; fresh probes fall **1,022 -> 503**, new
patterns **197 -> 107**, working SQLite **2,510,848 -> 1,466,368 bytes**, and mean
preparation plus queries **0.49636 -> 0.38107 s**. Two repetitions and a constructed
sample establish no general speedup or arbitrary-SAT bound. All **318 tests** pass.

The inherited admission counter does not cover fused-conditioning `_discover_profile`
entries: the initial diagnostic finds eighteen recorded nodes outside it in each
arm. Historical “32-state” counts refer to that ledger, not a global acquisition
bound. Preserve this correction and count actual stored and unfinished states.
The largest remaining cost is new input 41, a **48/204/612** random CNF with 272
probe attempts and unknown coverage. Inspect its persistent frontier, retaining
the frozen inputs and all previous results. The original 83-source checkpoint
remains complete and must not be restarted.


## 2026-11-15: complete admission exposes the unresolved interaction

[The corrected admission layer](complete-admission-frontier.md) accounts for both
acquisition entrances before profile computation and keeps all old proof formats.
At allowance 32 it avoids **40 fresh probes**, producing the **same 107 stored
patterns and 41/42 coverage**. No storage gain is claimed. At allowance 4096 the
last query returns normally on 391 admissions and 357 new patterns, but still
has one connected **38/165/502** selected residual at depth zero. This is the next
structural target, bound in `cnf-complete-admission/selected-frontier.json` to the
original 48-variable input; the generous archive is the next restoration source.

Four preserved 32-state restarts add 79 patterns to the previous 107 but repeat
33 admissions and remain capped. Investigate checked persistence of unfinished
profiles and transient restrictions. A complete state ledger does not bound
verification, repeated visits or total time. All 323 tests and sixteen cold
archives pass; the old 83-source checkpoint remains complete and unchanged.


## 2026-11-15: a saved-pair ranking counterexample and 42/42 coverage

[The equal-budget pair comparison](transfer-split-selection.md) closes the last
transfer input via residual variable 14, with 13 new records and 30 probes. The
initial smaller-cofactor choice, variable 6, remains open after 45 probes. Of four
saved pairs, only variable 14 closes both children: one reduces to two 2-CNF
components and the other to a contradiction. Testing all four costs 38 admissions
and 188 probes per repetition. This is adaptive completion, not a holdout or a
uniform arbitrary-SAT result.

The union checkpoint preserves 477 patterns and all four alternatives; all 42
originals have checked coverage and `next_selection` is null. Restore
`cnf-transfer-split/checkpoint.json` through its validator's restoration helper.
Next investigate indicators or reusable bounded lookahead that predict these
propagation cascades on newly frozen inputs. Cold history verification dominates
local expansion, and source-only controls show no fresh-probe reuse benefit for
the initial pair. All 327 tests and thirteen cold archives pass; no old source,
proof block, result or incomplete alternative is deleted.


## 2026-11-15: lookahead reuse exposes a candidate-availability gap

[The frozen 24-input study](lookahead-bank.md) finds no saved source pairs on
22 selected residuals at conditioning depth zero: their binary-clause count is
zero. Only two connected mixtures exercise saved-pair ranking. An optional checked
probe bank avoids 36 repeated probes, but lookahead still uses 106 probes versus
72 for size ranking, chooses the same pairs, stores more bytes and adds no original
coverage. No arm is capped. The bank is not enabled as a default optimization.

Next acquire a common candidate pool through charged ordinary conditioning or
broader source assumptions before comparing ranking. Keep both polarities,
verification and persistence in the cost account. The new 24 depth-zero unknowns
are distinct from the completed previous 42-input stream. All 331 tests and the
seed plus eight comparison archives pass cold checks; all previous proofs and
results remain intact. This is no unrestricted-SAT or negative SAT verdict.


## 2026-11-16: broader candidates and repeated split verification

[Exact source conditioning](bootstrap-conditioning.md) supplies candidates for all
24 selected residuals, including those without binary clauses. Both unit-closed
branches are checked and persisted before expansion. Under the supplemental
workflow comparison, enumeration covers 5/24 versus ordinary depth one's 4/24,
with 3,946 versus 5,699 probes and 558 versus 737 new patterns. It takes longer:
7.41975 versus 6.13657 seconds for the query stream. First and size selection each
cover 2/24. Source assumptions are charged separately from recognition admissions;
ordinary restarts the original while external routes reuse depth-zero ancestors.

The immediate reuse opportunity is exact incremental split verification: a
separate diagnostic reproduces the graph and finds 3,913 checks for 86 distinct
records. Rebuilding all earlier routes after each pair causes the quadratic sum.
Cache immutable checked evidence with exact policy/source binding, retain pending
child dependencies, and preserve independent cold replay. Then attack the nineteen
uncovered originals through deeper interactions and better component/pivot choices.

The union checkpoint retains 1,154 patterns, 96 pairs, 17 missing children and
5/24 coverage. All 335 tests and eleven cold archive checks pass. The initial
validator's archive-path collision was repaired with byte-identical original seed
reconstruction; the failure and recovery are preserved separately. The final
checkpoint and all earlier results remain usable. No arbitrary-SAT efficiency
bound, SAT/UNSAT verdict or new Lean refinement is claimed.


## 2026-11-16: incremental split checking removes repeated route work

[The matched registry comparison](incremental-split-checking.md) reduces mean
query time 7.41290 -> 4.26395 seconds and split checks 3,913 -> 258, while preserving
candidate choices, 3,946 probes, 558 new patterns, all archive bytes, positive
proofs and 5/24 coverage. Live metadata is additional; there is no persistent-space
or peak-RAM reduction. Cold proof checking is unchanged. All 341 tests and nine
cold archives pass, including pending-child activation without a new pair,
invalidations and acquisition-free replay.

The next discovery target is case 16, the largest mean unresolved query after
optimization: 0.31922 seconds, 205 probes and 27 admissions, below the cap. Its
59-variable / 245-clause / 743-literal selected component has four saved splits
with all eight child records present, but none covered under the full retained
union. Follow existing reductions and investigate deeper interaction; do not
repeat these acquisitions. Cases 17 and 22 are useful uncapped controls.

Restore the unchanged 1,154-pattern / 96-pair parent union, using the exact source
and branch bindings in `cnf-split-registry/next-discovery.json`. The enumeration
comparison's 643-pattern histories contain fewer alternatives. All previous
results and 64 proof blocks remain intact; nineteen current originals remain
unknown. No unrestricted-SAT efficiency claim follows from the runtime saving.


## 2026-11-16: nested conditioning closes case 16

[The deeper continuation](nested-conditioning-discovery.md) raises current
coverage 5/24 -> 6/24. All 59 first-level source pivots leave the original uncovered
under the fixed recognizer and flat history; nesting eleven new pairs below the
saved pivot 7 closes it. The original proof has twelve conditional nodes, depth
five, 265 unary reductions and nine family leaves. This is branch-dependent
conditional exposure with reductions, not a fixed five-variable backdoor or a
minimum-depth result. Only the canonical contradiction is shared, on five paths;
no broad nonterminal reuse is demonstrated.

Nested work uses 2,403 probes, 275 patterns and 22 source assumptions, versus
2,291, 272 and 110 for the unsuccessful flat control. The successful final
resumption adds 27 patterns and 215 probes with no fresh source assumption,
retaining 248 earlier new patterns. All 345 tests pass. Every primary batch archive
and the union have acquisition-free cold proofs; all old artifacts and 64 proof
blocks remain unchanged.

Resume from `cnf-nested-refinement/checkpoint.json`: 1,701 patterns, 162 pairs,
17 inherited missing children and 6/24 coverage. Preserve the flat control's
unsuccessful records as well. Case 16 is complete; next test the adaptive policy
on case 17's 60-variable / 255-clause / 765-literal component, with case 22 as a
control. Eighteen originals remain unknown. The main discovery gap is predicting
useful adaptive reduction paths; the 265 unary proof steps are a supporting
storage/checking target. Neither finite success nor shallow observed depth implies
uniform polynomial expansion on arbitrary SAT.


## 2026-11-16: transfer the policy and measure the value of added history

[The unchanged nested policy](case17-policy-transfer.md) closes case 17 in one
batch, raising coverage to 7/24. Both the full union and the pre-case-16 control
produce identical acquisitions, choices and target proofs: 89 new patterns, nine
pairs, eighteen source assumptions and 531 probes. None of the 547 patterns or
66 pairs acquired for case 16 contributes to the new proof. Seven older pattern
steps still contribute. This is policy transfer on development data, not evidence
of broad cross-input reuse of nonterminal components.

The checked 96-step proof has ten conditional nodes, 84 unary reductions, two
constant family leaves and maximum conditional depth six. Only the contradiction
is shared, on ten paths. There is no fixed six-variable backdoor or minimum-depth
claim. Full-history startup plus cold replay costs 11.50553 seconds, versus
0.62379 seconds local expansion. Mean full-stream time is 12.86418 versus 8.59953
seconds for the older-history control; the arms start with different coverage and
check different amounts of evidence. A checked source-local working view with
exact global fallback is a supporting opportunity, not an implemented speedup.

The preservation union keeps 1,790 patterns, 171 pairs, seventeen inherited
missing children and a 446-step proof for seven originals. All 345 tests and
independent checks of both parents, four trial archives and the union pass.
Seventeen originals remain unknown. The next bound discovery target is case 22's
disjoint binary mixture with a 48-variable residual. Test policy transfer and
separate easy-component reuse from random-core closure. No arbitrary-SAT
efficiency bound or new Lean refinement follows from this finite experiment.


## 2026-11-16: root-complete checking closes the disjoint mixture

[The optional scoped registry](scoped-refinement.md) preserves all reachable
ordinary and split routes, while deferring unrelated semantic checks to the full
cold audit. Both modes use the complete history and unchanged acquisition policy.
Case 22 closes with nine new patterns, two pairs, four source assumptions and
29 probes, raising coverage to 8/24. Acquisitions, choices, proofs and archive
bytes match across two reversed repetitions. Whole-stream time falls 12.59685 ->
6.94722 seconds (44.85%); mean process RSS falls 21.83%. No persistent bytes are
saved. Startup still scans global identities and historical row maps.

The original proof has 32 distinct steps: one decomposition, three conditional
nodes, 26 reductions and two family leaves. Twenty-three steps were retained and
nine are new. An easy nine-variable 2-CNF component is separate from the random
core's four contradiction leaves. Only the contradiction is shared; depth three
is not a fixed backdoor or a minimum-depth guarantee. All 351 tests pass, including
pending activation, interrupted resume, relevant corruption and writer/policy
invalidation. The complete parent, four trial archives and union pass independent
acquisition-free checks. A scoped live query alone does not validate unrelated
history. All earlier artifacts, sources and 64 proof blocks remain intact.

The full union retains 1,799 patterns, 173 pairs, seventeen missing children and
a 477-step proof for eight originals; sixteen originals remain unknown. Case 23's
connected binary mixture is next, with a 59-variable / 255-clause / 767-literal /
width-four residual and eight present but uncovered saved children. Use the new
checkpoint and bound successor. Full cold checking now takes about 86% of scoped
stream time; sharing a guarded session and complete audit across queries is the
next cost opportunity, requiring a separate matched test. No uniform arbitrary-SAT
efficiency bound, new Lean refinement or new SAT/UNSAT output API is claimed.


## 2026-11-16: grouped audits close three originals with a memory tradeoff

[Sharing the complete audit](grouped-checkpoints.md) closes cases 23, 18 and 15,
raising coverage 8/24 -> 11/24. Both workflows add 147 patterns and 21 pairs with
42 source assumptions and 707 probes. Each query proof is checked independently
on its exact snapshot; every intermediate archive remains stored. Full auditing
moves from every batch to group end, reducing sequence time 24.13644 -> 11.65332
seconds (51.72%). All acquisitions, proofs and snapshot bytes match. Unrelated
corruption detection is delayed; the grouped intermediate archives are not
globally certified during execution. Final publication requires the full audit.

Mean peak RSS rises 7.70%, from 453.58 to 488.51 MB, and persistent bytes are
unchanged. Preserve this regression. A separate retrospective validator fully
checks all twelve prefixes, original bindings, immutable history and reachable
catalogs; its 165.97-second validation cost is outside paired stream timings.
All 356 tests pass. Earlier artifacts, source files and 64 proof blocks remain
unchanged; no inference default or new Lean refinement is introduced.

The connected input closes through eight conditional nodes and 63 reductions,
with no decomposition step. Its leaves expose contradiction and a five-variable
2-CNF. The random cases add Horn/zero-valid and zero/one-valid family overlaps.
Depths four, four and five are branch-dependent, not fixed backdoor sizes. Only
the contradiction is shared within each proof; no later proof uses a newly
acquired pattern from an earlier query. The saving is audit reuse, with broader
nonterminal reuse still open.

The union retains 1,946 patterns, 194 pairs, seventeen inherited missing children
and a 665-step proof for eleven originals; thirteen remain unknown. Resume from
cnf-grouped-checkpoints/checkpoint.json. Case 19 is next, with a 58-variable /
276-clause / 841-literal / width-four residual and eight present, uncovered saved
children. One final full audit still takes 59.6% of sequence time; compression
takes 17.0%. Investigate checked parent reuse plus new-record verification with
explicit trust and fallback, and profile memory before growing groups. No
unrestricted-SAT efficiency bound or SAT/UNSAT output claim follows.

## 2026-11-16: case 19 closes; checked canonical form trims the full audit

[Canonical cold auditing](canonical-cold-audit.md) closes case 19 with 35 new
patterns, five pairs, ten source assumptions and 135 probes in one batch.
Coverage rises **11/24 -> 12/24**. The 42-step proof has six conditional nodes,
35 reductions (28 probes, four binary-path steps, three eliminations) and one
contradiction terminal. It reuses seven retained pattern steps and one split.
Maximum conditional depth is three, with changing coordinates, not a fixed
backdoor of size three. Only contradiction is shared within the proof; 48
unfolded occurrences become 42 steps. Larger reusable components remain open.

A profile of the frozen parent identified repeated normalization as a cost.
The optional complete auditor now uses the existing checked canonical-source
fast path in all verifier views. Every actual source is scanned; fallback keeps
the old normalization. It still independently verifies every node, split,
original binding and coverage proof. No parent-validity flag or warm cache is
trusted, and acquisition remains forbidden during checking. Earlier negative
checker-index experiments are preserved, not repeated without new evidence.

Four alternating-order paired runs give audit time **6.75146 -> 6.46583 seconds
(4.23%)** and whole-stream time **8.20199 -> 7.88948 seconds (3.81%)**. All
acquisitions, proofs and corresponding snapshot hashes match. Mean peak RSS
increases **589,824 bytes (0.153%)**; persistence is unchanged. The fast path
accepts 3,316 calls and falls back on 2,692. It adds precheck work, so the saving
is avoided sorting/renaming rather than fewer counted literal visits. The full
audit still consumes **82.0%** of stream time; compression takes about **9.0%**.

All **360 tests** pass. Independent retrospective replay checks all eight trial
archives, positive proofs, original bindings, complete reachable catalogs and
immutable prefixes; parent and union replay also pass. This research validation
takes 119.72 seconds, outside operational means and partly concurrent with the
test suite. All previous 290 sources, 3,290 artifacts and 64 manuscript proof
blocks remain unchanged. There is no inference-default change or new Lean proof.

The new union retains **1,981 patterns / 199 pairs / 17 inherited missing children**
and a **706-step positive proof for twelve originals**. Twelve remain unknown.
It occupies **37,580,800 SQLite bytes / 1,883,472 gzip bytes**, growing by 696,320
and 49,145 bytes respectively relative to the parent. Restore
`experiments/results/cnf-canonical-audit/checkpoint.json`.

**Next discovery target:** case **6**, random 3-CNF, selected residual
**36 variables / 148 clauses / 444 literals / width three**. All eight children
of its four saved pairs exist. The false child of saved pivot **13 is already
covered**, while its true child is not; the other six children are also uncovered.
Inspect and reuse that covered side before further acquisition. Historical
costs rank this target; they do not predict a new runtime bound. Keep broader
nonterminal reuse and conditional-depth growth as discovery gaps. Audit work
remains dominant; avoid assuming that more caches or weaker validation will
improve it. These finite measurements do not establish efficient arbitrary SAT.

## 2026-11-16: saved splits expose a minimum-cost selection counterexample

[Case-6 split-history control](saved-split-reuse.md) raises coverage **12/24 ->
13/24** and exposes a failure of the current remaining-literal heuristic. The
complete parent already selects pivot 13 and skips its covered branch. This
route adds **74 patterns / 547 probes / ten source assumptions**. An isolated
copy omitting only the four source-split records, while retaining every pattern
and every other split, reconstructs pivot 11 and adds **63 patterns / 345 probes /
twelve assumptions**. Both close in one batch. The intervention changes saved
selection information and certificate reuse together; it is not an empty-history
solve or a reason to discard history generally.

Visible remaining-literal scores for pivots 11,15,8,13 are 796,820,758,409.
An acquisition-free diagnostic replacing this by distinct uncovered obligations
changes no choice at twelve remaining source nodes. Do not implement that
ineffective fix on this parent. The better next test retains all alternatives
and charges bounded downstream simplification trials, reusing every admitted
state before committing further budget. Consult existing lookahead experiments
and retain regressions. Minimum visible frontier is not minimum future cost.

Two reversed paired runs give whole-stream **8.07061 vs 7.82088 seconds**, and
mean peak RSS **410,058,752 vs 384,090,112 bytes**, retained versus control.
The retained route has 17.46% more new patterns and 58.55% more probes, but slightly
faster local expansion (0.24952 vs 0.25645 seconds). It has more SQLite bytes but
a 1,275-byte smaller gzip snapshot. Cost dimensions disagree; no general speed,
memory or compression claim follows. Complete auditing still takes about 82%.

The retained/control proofs have **86/76 steps**, conditional depth **5/4**, one
component decomposition each, and contradiction, 2-CNF and Horn/zero-valid
terminals. Neither depth is a fixed backdoor-size claim. Their new pattern and
split sets are disjoint: the union retains all **137 new patterns / ten new split
identities**, with no new nonterminal reuse between these two routes. The
control's first split matches a historical identity but was reconstructed.

All **363 tests** pass. Frozen independent replay checks both initial variants,
all four trial archives and the union, plus query proofs, original bindings,
reachable catalogs and immutable per-variant prefixes. Successful validation
takes 88.50 seconds outside operational means; an earlier next-pointer failure
and its code are preserved separately. Missing optional roots are now checked
before composition and remain unknown. All earlier 294 sources, 3,338 artifacts
and 64 proof blocks remain unchanged.

Restore `experiments/results/cnf-saved-split-reuse/checkpoint.json`: **2,118
patterns / 209 pairs / 17 inherited missing children / 13 of 24 originals covered**,
with a **779-step proof** and **39,448,576 SQLite / 1,970,166 gzip bytes**.
Eleven originals remain unknown. Next is **case 11**, with a selected **45-variable /
196-clause / 608-literal / width-five** residual. Eight saved children are present
and uncovered. Its depth-zero original root exists; its optional depth-one root
does not. No inference default, Lean proof or arbitrary-SAT bound is changed.

## 2026-11-16: a charged pilot improves downstream route selection

[Testing two saved routes](pilot-refinement.md) closes case 11 and raises coverage
**13/24 -> 14/24**. The optional pilot completes one nested acquisition on each
of the two best saved routes before committing. All work shares the ordinary
128-admission / sixteen-operation batch allowance. Partial trials stay on their
arm until complete and survive cold restart. The current implementation requires
an unresolved source below a unary selected root prefix and two saved choices;
it is not a general component scheduler. Exact closure uses the frozen checker.

Initially pivot 6 has score 1106 and pivot 32 has 1118. The pilot spends **three
admissions / 28 probes** on the first, leaving three obligations and 1535 literals,
and **seven admissions / 27 probes** on the second, leaving one obligation and
559 literals. It selects pivot 32, and one further acquisition closes the original.
All losing-trial results remain stored. The older failed one-profile lookahead
and the case-6 counterexample remain preserved.

Committed/pilot totals are **44/19 new patterns, 178/77 probes, eighteen/six source
assumptions and nine/three new splits**. Both close in one batch. Two reversed
paired runs give expansion **0.27211 -> 0.11072 s (59.31%)**, whole stream
**8.23501 -> 7.85315 s (4.64%)**, and mean peak RSS **388,456,448 -> 382,541,824
bytes (1.52%)**. Total SQLite/gzip size falls 1.17%/1.43%. Full auditing still
uses 84.0% of candidate time, compression 9.5%, and expansion 1.4%. Do not scale
acquisition savings into total-cost or unrestricted-SAT claims.

The control proof has **53 steps / depth five**, the pilot **29 steps / depth two**.
Both use conditional nodes and unary reductions to expose contradiction, with
no component decomposition. The pilot proof uses sixteen new and thirteen
parent steps; its three losing-trial patterns are unused but retained. The arms
share exactly those three exploratory patterns and one split; no new pattern
is common to both final proofs. This is not broader nonterminal or cross-input
reuse. Depth uses changing local coordinates, not a fixed backdoor-size bound.

All **367 tests** pass, and independent frozen replay checks the parent, four
trial archives, query proofs, reachable catalogs, budget accounting, cold pilot
recovery and the union. Validation takes 75.45 seconds outside operational means,
partly concurrent with tests. All earlier 298 sources, 3,378 artifacts and
64 proof blocks remain unchanged. No default solver or Lean theorem changes.

The union keeps **2,178 patterns / 220 pairs / seventeen inherited missing children**,
with an **807-step positive proof for fourteen originals**; ten remain unknown.
It occupies **40,517,632 SQLite / 2,037,803 gzip bytes**, retaining sixty distinct
new patterns and eleven splits from both arms. Restore
`experiments/results/cnf-pilot-refinement/checkpoint.json`.

**Next test:** transfer the unchanged pilot and committed control to case **13**.
Its selected residual is **47 variables / 213 clauses / 649 literals / width four**.
All eight saved children exist; pivot 41's true child is covered, the other seven
are not. Both original roots exist. Check the unary-prefix precondition and
charge all trial work. Broader replication is needed before adopting the pilot;
known negative controls and worst-case acquisition/space gaps remain open.

## 2026-11-16: pilot transfer exposes the cost of an unnecessary trial

[The unchanged pilot on case 13](pilot-transfer.md) raises structural coverage
**14/24 -> 15/24**, but gives the same 38-step proof as committing immediately.
Both choose saved pivot 41. Committed/pilot totals are **27/37 new patterns,
128/179 probes, six/eight source assumptions and three/four splits**. The pilot
inserts exactly one alternative trial after the first operation, then performs
the same continuation. Its ten extra patterns add no measured corpus coverage
and are unused by this proof. They remain stored; future reuse is unproven.

Local expansion rises **37.18%** (0.13244 -> 0.18168 seconds), peak RSS **0.40%**,
SQLite **0.41%** and gzip **0.53%**. Whole-stream means are 8.33858/8.24283 seconds,
but the two paired comparisons disagree on the faster mode. Do not claim the
small mean difference as a reliable total-time gain. Complete auditing remains
about **83--84%** of time. Both modes use the same full parent, frozen policy,
shared budgets and independent checks; this is a known development input.

The proof uses four conditional nodes, 32 unary reductions and two terminals:
contradiction and a five-variable dual-Horn/one-valid residual. Eleven steps and
one split predate this continuation; 27 steps and three splits are new. Only
contradiction is shared within the proof. Depth four uses changing coordinates,
not a fixed backdoor bound. Identical proofs on the same original do not establish
new cross-input reuse, and structural coverage is not a SAT/UNSAT output API.

All **367 tests** pass. Frozen independent replay checks the parent, four trial
archives, union, query proofs, original bindings, reachable catalogs, immutable
prefixes, cold pilot phases and shared budgets. Validation takes 76.24 seconds
outside timing, partly concurrent with tests. The acquisition-free preflight
costs another 0.15935 seconds separately. All 302 prior sources, 3,417 artifacts
and 64 manuscript proof blocks remain unchanged. Only a transfer driver is added.

Restore `experiments/results/cnf-pilot-transfer/checkpoint.json`: **2,215 patterns /
224 pairs / seventeen inherited missing children**, with an **844-step proof for
fifteen originals** and **41,099,264 SQLite / 2,073,167 gzip bytes**. Nine remain
unknown. Every losing-trial result is retained.

**Next:** decide when a second trial is worth acquiring, tested against committed
and always-pilot controls on **case 21, a connected binary mixture**. Its selected
residual has **45 variables / 201 clauses / 616 literals / width four**. All eight
saved children of pivots 2,1,23,17 are present and uncovered; only the depth-zero
original root exists. Check the pilot prefix precondition. A gate based on whether
the first trial reduces unresolved literal mass is a post-hoc hypothesis only:
case 11 grew 1106 -> 1535; case 13 shrank 610 -> 539. Freeze the gate before new
acquisition. The earlier case-6 counterexample rules out trusting covered-child
presence alone. No default policy or unrestricted-SAT guarantee changes.

## 2026-11-16: a progress gate avoids an unhelpful second route on case 21

[The optional progress gate](progress-pilot.md) closes the connected binary
mixture **case 21**, raising structural coverage **15/24 -> 16/24**. The rule was
frozen before acquisition: after one completed trial, skip the second if the
selected unresolved literal mass strictly decreases, or the query closes.
Otherwise use the unchanged two-route pilot. The baseline and partial work
survive restart; all work shares the same 128-admission / sixteen-operation
batch allowance. This is a scheduling heuristic, not a cost bound.

The first route at pivot 23 falls **1141 -> 1099 literals** after **eight
admissions / 53 probes**. The gate stops exploration. Always-pilot tries pivot
17 for **seven admissions / 52 probes**, seeing **1097 literals** and switching.
Gated and committed totals are **24 patterns / 100 probes / eight assumptions /
four splits**, versus **32 / 175 / twelve / six** for always-pilot. The gate
matches committed operations, proof and SQLite/gzip bytes. The two-literal
advantage did not justify extra exploration on this input.

The committed/gated proof has **42 steps**, five conditional nodes, 36 unary
reductions and six contradiction occurrences. Eighteen steps and one split
predate continuation; 24 steps and four splits are new. The pilot proof has
41 steps and uses 24 new proof nodes, but retains eight unused trial patterns.
The different final proofs share no new node. Only contradiction is shared
within each proof; neither decomposes into separate components. Both have
conditional depth three in changing coordinates, not a fixed backdoor bound.
A shorter final proof therefore need not be cheaper to acquire.

Against always-pilot, the gate reduces new patterns **25%**, probes **42.86%**,
local expansion **35.25%**, RSS **0.65%**, SQLite **0.40%** and gzip **0.57%**.
Whole-stream means are committed/pilot/gated **8.48923 / 8.75818 / 8.62917 s**.
Pilot/gated pair rankings disagree; the 1.47% lower mean is inconclusive. Gated
whole time is 1.65% higher than committed despite matching evidence. Full auditing
still consumes about 82--83% of time. Two triples, with pilot always in the middle
position, do not establish a robust timing advantage. Parent acquisition remains
charged in earlier results, and these are history continuations.

All **372 tests** pass, including five new checks of shared budgets, interrupted
trials, baseline retention, skipped/explored routes and cold restart. An initial
method-rebinding implementation error was fixed before measured acquisition;
its source and test failure are retained. Independent full replay checks six
archives, original bindings, complete catalogs, query proofs, prefixes, budgets
and scheduling state in 106.11 seconds outside operational timing, partly
concurrent with tests. Preflight costs 0.20920 seconds separately. All previous
303 sources, 3,453 artifacts and 64 manuscript proof blocks remain unchanged.

Restore `experiments/results/cnf-progress-pilot/checkpoint.json`: **2,263 patterns /
233 pairs / seventeen inherited missing children**, with an **884-step proof for
sixteen originals**. Eight remain unknown. The union retains every losing trial:
48 distinct new patterns and nine splits, using **42,033,152 SQLite / 2,131,824
gzip bytes**. No inference default, Lean theorem or SAT/UNSAT output API changes.

**Next:** transfer the unchanged gate and both controls to **case 10**, random
3-CNF with selected **45 variables / 180 clauses / 557 literals / width five**.
All eight children of pivots 20,3,17,22 exist and remain uncovered; only the
depth-zero original root is present. Check the prefix precondition. Look for an
early literal decrease that masks expensive continuation; a successful local
step is not a global potential or a minimum-cost certificate. Broader shared
nonterminal patterns and full-history audit cost remain unresolved.

## 2026-11-16: failed gate transfer reveals four exact nonterminal joins

[The unchanged transfer to case 10](progress-transfer.md) raises coverage
**16/24 -> 17/24**, but the gate follows always-pilot onto a more expensive route.
The first trial grows **1042 -> 1468 literals**, from two obligations to three;
its seven admissions and 64 probes trigger exploration. The second trial uses
ten admissions and 67 probes, leaving two obligations / 1040 literals. Both
pilots choose pivot 17. The committed control stays on pivot 22.

Committed versus either pilot: **106/119 new patterns, 653/778 probes,
eighteen/twenty-four assumptions and nine/twelve splits**. Both pilots have
identical operations, proofs and archived bytes. Gated local expansion rises
**17.79%**, peak RSS **0.65%**, SQLite **0.54%** and gzip **0.57%**. Whole-stream
means are committed/pilot/gated **9.31591 / 9.39216 / 9.41249 s**; two triples
do not establish a reliable small total-time effect. Complete auditing remains
78--79% of time. No policy or budget was tuned, and the gate remains optional.

The useful structural finding is four joins between the different final proofs.
They share **39 new nodes** with identical rules and children: **33 unary
reductions, four conditional nodes and two 2-CNF terminals**. The four exact
entry formulas have **27/32/39/4 variables** and disjoint new descendant regions
of **12/12/13/2 nodes**. Two entries follow elimination and two follow probing
from distinct parents. Their union includes one inherited contradiction and
has a **40-step positive subproof**, independently checked without acquisition.
Full keys, parent hashes, shapes and proof are preserved under
`experiments/results/cnf-progress-transfer/joins/`.

In particular, two different 40-variable / 151-clause parents with 460 and 457
literals eliminate to the same 39-variable / 153-clause / 475-literal formula.
Literal growth can accompany useful convergence. The exact cache can reuse the
saved result once reached; the open problem is recognizing and reaching that
boundary cheaply on a new input. Equality of shape or an approximate match
cannot substitute for the complete policy/depth/CNF key and checked mapping.
The observed joins concern two routes through one original, not cross-input
reuse. Direct whole-root reuse already handles repetition of this original.

The committed proof has 116 steps and depth four; pilot has 122 and depth six,
with six unused exploratory patterns. Depth uses changing local coordinates,
not a fixed backdoor bound. Their acquisitions share 45 new patterns and five
splits; their final proofs share 39 new nodes and four splits. Raw shared pattern
keys/payloads total 283,851 bytes plus 39,431 split bytes, excluding SQLite and
Python overhead. This is not a measured memory saving. Join analysis takes
0.18489 seconds outside benchmark timing; full retrospective replay takes
111.93 seconds, partly concurrent with tests. Preflight takes 0.17075 seconds.

All **372 tests** pass, and independent full replay checks six archives, original
bindings, query proofs, complete catalogs, prefixes, shared budgets and cold
state. All earlier 307 sources, 3,500 artifacts and 64 proof blocks are unchanged.
The post-hoc analyzer is separately source-bound; an initial SQL column-name
error and its source are preserved, and corrected certificate checking passes.
No solver, gate, inference default, Lean theorem or SAT/UNSAT output API changes.

Restore `experiments/results/cnf-progress-transfer/checkpoint.json`: **2,443
patterns / 249 pairs / seventeen inherited missing children**, with a **999-step
proof for seventeen originals**. Seven remain unknown. The union retains every
trial: 180 distinct new patterns and sixteen splits, using **44,810,240 SQLite /
2,271,560 gzip bytes**.

**Highest next reuse target:** test related inputs with previously unseen roots
that reach the saved elimination/probing joins, with edits that invalidate the
shared image. Compare matched histories and charge all recognition, boundary
verification, acquisition, persistence and cold replay. Avoid fitting another
scalar threshold to these cases. The independent discovery pointer is **case 7**,
with selected **33 variables / 152 clauses / 470 literals / width four**. All
saved children exist; pivot 14's true child is covered and seven remain open.
Only its depth-zero original root exists. No arbitrary-SAT efficiency claim follows.


## 2026-11-16: cross-input join transfer and clause-edit limits

[Cross-input join transfer](join-transfer.md) avoids **35 acquisitions and 154
probes** on 24 distinct constructed CNFs. The unchanged solver receives only
CNFs. Its two matched histories differ by exactly **39 saved proof nodes and
four splits**. All 24 query proofs match across histories; the second visit
acquires nothing. Acquisition falls **206 -> 171**, probes **1132 -> 978**.
Three first encounters account for the entire difference: twelve, ten and
thirteen saved nodes below the 27-, 32- and 39-variable joins. The small anchor
and two nodes above the useful 32-variable descendants remain unused.

**Highest next discovery target:** clause-deletion controls receive no
acquisition saving and account for **136/171 new patterns and 768/978 probes**.
Inspect constructed **case 13** (33 variables / 95 clauses / 274 literals /
width four, 29 new patterns / 218 probes) against its matching preimage. Determine
which clause dependencies block transfer, and seek an exact shared residual or
checked split transport. An edit invalidating one projection does not exclude
all reuse. Keep variable maps, boundary checks and proof dependencies explicit.
Original **case 7** remains a separate broader coverage control, with seven
open saved children and pivot 14's true child already covered.

**Largest measured whole-stream cost:** full cold auditing, about **52%** of
14.48/14.33 seconds. Mean solve/bookkeeping falls 4.48%, but whole runtime only
0.99%; two pairs do not establish a reliable small timing effect. RSS rises
0.168%, SQLite 0.091% and gzip 0.486%. The treatment ends with all control rows
plus four unused preloaded nodes. Seed preparation takes **16.014 seconds**
separately and historical acquisition remains charged. This is a local reuse
saving, not a demonstrated net acquisition-plus-use or memory improvement.

**Secondary opportunity:** some positive preimages miss their specified anchor
under the default reduction order despite a checked one-pair projection. Reuse
the earlier projection infrastructure cautiously; its expensive global-index
preparation and negative frontier results remain preserved. Do not tune a new
route heuristic on these 24 constructed cases alone.

Restore `experiments/results/cnf-join-transfer/checkpoint.json`: **2,614 patterns /
259 pairs / seventeen inherited missing children**, preserving all earlier rows
and all trial additions. Original structural coverage remains **17/24**, with
the same **999-step proof**. The separate 24 constructed inputs have a **208-step
proof**, bound by `supplemental_queries` and `supplemental_proof`. Preserve both
catalogs in later unions. Storage is **47,181,824 SQLite / 2,375,854 gzip bytes**.
All **376 tests**, four independent stream reconstructions and 192 query-proof
replays pass. Prior 309 sources, 3,550 artifacts / 61 manifests and all 64
manuscript proof blocks remain unchanged. Runtime binds 313 sources; the final
ledger also binds the post-hoc analyzer and supplemental replay checker (315). Synthetic structural
coverage does not imply efficient arbitrary SAT or supply SAT/UNSAT answers.
Checkpoint SHA-256: `5bd57b9b2bf1007a4b447764c40d8c4d920450f6f90699342926218c41b9a652`.
Report SHA-256: `98eb6b23f6bcb2d80c9dc7714bad65ce5de37c6fb0875cdd8e9ee7c4160cf346`.
The new manifest adds **38 artifacts**; the next audit inherits **3,588 artifacts /
62 manifests**. The manuscript builds to **186 pages**.

## 2026-11-16: checked UNSAT reuse under clause deletion

[Checked clause-deletion guards](clause-deletion-guard.md) reduce new reference
residual nodes **502 -> 427 (14.94%)**, decision splits **200 -> 174**, and complete
stream time **1.27860 -> 1.17492 seconds (8.11%)** on twelve constructed edits.
This is a separate SAT decision experiment with the unchanged `ResidualSolver`,
not a structural-coverage increase or a new production policy. Six retained
UNSAT proofs justify forcing the removed clause false; six SAT premises decline.
Both modes return nine SAT and three UNSAT answers, independently replayed.

**Highest next target:** positive witness transfer. Edits **19, 21 and 23** use
**364/427 remaining reference nodes**, although their undeleted formulas are SAT.
The analyzer verifies that all six retained SAT-template models satisfy their
edited inputs. Implement checked witness reuse before fresh search, preserving
the UNSAT guard and an ordinary control. Charge matching, model checking and
persistence. The current wrapper does not yet use this positive transfer.

**Limits exposed:** case 13 remains at **22 reference nodes / eleven splits**
after forcing two variables; this is distinct from its earlier 29 structural
patterns. Case 7 uses two more splits. Cases 15 and 17 supply 67 of 75 avoided
nodes, reducing **43/26 -> 1/1**. The general exceptional cofactor can remain
arbitrary SAT: `F = H AND NOT x AND x` is cheaply UNSAT, while deleting `x` and
forcing it false leaves arbitrary `H`. The underlying clause-deletion reasoning
is established in transition-clause/MUS work; no new complexity claim follows.

**Accounting:** preparing the common 613-node reference seed costs **0.91359 s**
separately. SQLite falls 6.42%, but compressed database plus raw query sidecar
increases **760,368 -> 810,993 bytes**. Two repetitions establish only this local
measurement; the small RSS change is not broad memory evidence. Cold archive
checking remains about 28% of stream time. Tests and retrospective validation
run outside the timed workers.

Resume `experiments/results/cnf-clause-deletion-guard/checkpoint.json`. It retains
the unchanged **2,614 structural patterns / 259 pairs / seventeen missing
children**, original **17/24 coverage / 999-step proof**, and separate **24/24
supplemental coverage / 208-step proof**. Its `reference_study` binding preserves
the new decision archives and guard sidecars; keep them on continuation.
All **382 tests**, all four reference streams and all **96 query-result replays**
pass. The analyzer also checks the hardness construction on all 512 two-variable
CNFs. Runtime binds 319 sources; the final ledger binds 320 with the analyzer.
All prior 315 sources, 3,588 artifacts / 62 manifests and 64 proof blocks remain
unchanged. Original case 7 remains the separate structural discovery pointer.
Checkpoint SHA-256: `e182f0023fc82ecb8ec674cbdc33c913ca91a104066b0a6d67c72812f8ea6b05`.
Report SHA-256: `70507d8854ddf5d7110b00c16604f5956e452e9003fb4af2cd011deb71f5b005`.
The new manifest adds **32 artifacts**; the next audit inherits **3,620 artifacts /
63 manifests**. The manuscript builds to **187 pages**.

## 2026-11-16: checked SAT witness reuse and new deletion candidates

[Checked SAT witness publication](clause-witness-reuse.md) removes the dominant
positive-query search on the twelve constructed edits. Relative to the UNSAT
guard alone, fresh reference expansions fall **427 -> 59**, with **six answer
publications / 65 new stored rows**. Whole time falls **1.19691 -> 0.59381 s
(50.39%)**, RSS **18.15%**, and SQLite **40.27%**. Ordinary solving needs 502
expansions and 1.26932 s. All modes return nine SAT and three UNSAT answers;
all repeated visits add zero rows. These are conditional decision measurements,
not structural-coverage gains or an unrestricted-SAT guarantee.

**Highest next discovery target:** previously unseen deletions of the UNSAT
templates. Existing twelve roots are now cached. A seven-attempt, one-variable
model-rotation screen finds two valid new-input witnesses from case 9, both for
**28 variables / 81 clauses / 238 literals**, with absent reference roots.
Flipping variable 260 leaves only `(-230,120,260)` false; flipping 150 leaves
only `(-100,150,160)` false. Their complete CNFs and models are preserved in
`rotation-screen.json`. Publish/check these candidates and test a fixed broader
set of neighboring deletions against ordinary and guard controls, charging
all failed proposals and full or indexed clause checking. This uses established
model-rotation reasoning; no rotation speedup has yet been measured.

**Retained failures:** case 7's three flips leave two or three clauses false;
both case-13 flips leave three. Case 13 still needs 22 of 59 fresh reference
expansions. No SAT witness supplies an UNSAT conclusion. A checked negative
premise still leaves an exceptional cofactor that can contain arbitrary SAT.

**Dominant measured costs now:** complete reference checking and compression,
about **68%** of the shorter stream. Database gzip plus raw query sidecar is
**676,971 bytes**, versus 811,502 guarded and 760,874 ordinary. Sidecar size alone
increases. All modes inherit the same 613-node seed, whose acquisition cost of
**0.91359 s** remains separate; this run's seed preflight costs **0.18338 s**.
Three triples balance position, but these remain development examples.

Resume `experiments/results/cnf-clause-witness-reuse/checkpoint.json`. Its new
`reference_union` retains **1,169 distinct keys**, using **5,931,008 SQLite /
450,067 gzip bytes**. No reference key is newly discovered relative to the
combined previous arms; alternate valid SAT certificates remain in the trial
archives, and the union keeps earlier payloads. Preserve `reference_study`,
`witness_reuse_study`, `reference_decisions` and the separate rotation proposals.
The structural authority remains **2,614 patterns / 259 pairs / seventeen
missing children**, with original **17/24 / 999 proof steps** and supplemental
**24/24 / 208 proof steps**. Original case 7 remains its discovery pointer.

All **388 tests**, nine new stream reconstructions / **216 query replays**, the
four prior streams and the reference union pass. The control databases match
the prior study byte for byte. All prior 320 sources, 3,620 artifacts / 63
manifests and 64 manuscript proof blocks remain unchanged. Runtime binds 324
sources; the post-hoc rotation screen raises the final ledger to 325.
Checkpoint SHA-256: `79c224246b77270980ddb5685ab32464df19057dfe95a7db976a5b18019de63b`.
Report SHA-256: `3005787a6d6eb257b19ee39a7b4cd33137384f93ec0f3c2547142b31bfd254d2`.
The new manifest adds **49 artifacts**; the next audit inherits **3,669 artifacts /
64 manifests**. The manuscript builds to **188 pages**.

## 2026-11-16: bounded model rotation and negative proof-support gap

[Bounded model rotation](model-rotation.md) reduces fresh reference expansions
**1,876 -> 1,509 (19.56%)** on **257 previously uncached deletions** of three
checked UNSAT templates. It publishes 57 checked SAT certificates, making 1,566
new rows. Complete runtime falls **11.28948 -> 10.48075 s (7.16%)**, mean peak RSS
**3.86%**, and SQLite **4.15%** against the guarded control. Ordinary solving uses
6,126 expansions and 27.82621 s. All modes agree on **72 SAT / 185 UNSAT**;
repeated visits add no rows. Three process triples balance mode position.

**Highest next target: reusable negative proof supports.** UNSAT queries consume
**1,216/1,509 expansions (80.58%)**, unchanged by rotation. Old template 12
accounts for 612 of these, with new deletion-catalog case 11 alone using 47.
The exact inputs, removed clauses and target hashes are retained in
`cost-attribution.json`. Determine whether checked UNSAT certificates expose
small clause supports or shared negative cofactors that transfer to further
queries by checked containment. Do not assume that failed rotations identify
UNSAT, or that two individually safe deletions can be combined safely.

**Retained limits:** 189 flips yield 99 singleton-false outcomes and 90 failures.
Of these, 57 publish absent keys and 42 reach old ones. Only 37 first query
encounters use a published direct answer; publication count is not avoided-solve
count. The first two templates hit 64-flip caps with six queued flips each;
the third exhausts its chosen-witness queue after 61 flips. Alternative witnesses
can open different routes. All attempts, origins, models and cursors persist;
cold certificate replay works, while engine-state import/resume remains open.

**Storage remains a gap:** combined database gzip and raw sidecars is 9,921,762
bytes, below guarded 10,419,742 but above ordinary 8,541,670. Guard sidecars repeat
whole stronger CNFs. The durable union preserves all old payloads and adds
7,935 distinct keys: **9,104 keys / 32,595,968 SQLite / 2,524,507 gzip bytes**.
Smaller arm memory does not mean smaller total retained history. One-witness
rotation has a bounded scan budget, not a uniform efficient SAT guarantee.

Resume `experiments/results/cnf-model-rotation/checkpoint.json`. Preserve all
inherited reference studies/decisions and the new `model_rotation_study`,
`model_rotation_decisions` and `reference_union`. Structural authority remains
**2,614 patterns / 259 pairs / seventeen missing children**, original **17/24 /
999 proof steps**, and separate supplemental **24/24 / 208 proof steps**.
Original case 7 remains its independent structural discovery pointer.

All **394 tests**, nine cold archive checks / **4,626 query replays**, rotation
origins and every union node pass. Earlier twelve reference decisions also
replay unchanged. Selection/preflight costs 0.35307 s separately; earlier
acquisition costs remain in historical records. These are constructed
neighboring inputs including known positive candidates, not a blind holdout.
Runtime binds 329 sources; the post-hoc attribution brings the final ledger
to 330. All prior 325 sources, 3,669 artifacts / 64 manifests and 64 manuscript
proof blocks are preserved.
Checkpoint SHA-256: `1049220a45fe5de68b1d3657ffd86dd0ea8ed0fd7202120324f94472b4304e1a`.
Report SHA-256: `91b60f9fb1b3403cae305cc5a23df6f76cc0a8aa92d772b084c281de0fd36535`.
The new manifest adds **54 artifacts**; the next audit inherits **3,723 artifacts /
65 manifests**. The manuscript builds to **189 pages**.

## 2026-11-16: checked negative supports and their accounting cost

[Checked UNSAT supports](unsat-support-reuse.md) recognize new negative inputs by
exact containment in a retained refutation core. On **192 unseen double
clause deletions**, the full bank certifies **40 UNSAT queries** by this route
and cuts fresh expansions **524 -> 355 (32.25%)**. However, complete runtime
rises **28.51440 -> 39.96590 s (40.16%)**, mean peak RSS **28.15%**, and SQLite
**23.74%**. The regression occurs in all three repetitions; this remains an
optional experiment. All modes return **102 SAT / 90 UNSAT**. The small
three-core bank saves only five expansions and has no reliable runtime gain.

**Highest next target: exact incremental archive accounting.** A separately
profiled warm pass spends **5.80760 s** copying full row inventories and
**3.45805 s** recomputing archive size: **84.55%** of its **10.95876 s** loop.
Core matching takes only **0.01618 s**. Replace per-query full-history scans
with checked append-only deltas and maintained size totals, preserving a full
final audit. Then compare further unseen edits using the **already persisted
core bank** and identical full initial unions. Charge initial core acquisition
and retained storage explicitly; no amortized break-even has been shown.

**Structural gain and limit:** all 188 known negative sources yield 145 distinct
supports. The original templates shrink 82 clauses to 64 and 63, and 96 to 80.
Derived nodes use the frozen verifier and existing certificate format. A failed
match never implies SAT or UNSAT. Supports are not minimal, arbitrary renamings
are not searched, and the acquired proof DAG can still be exponential. The
full bank leaves **328 negative / 27 positive** fresh expansions.

**Retained compression evidence:** removing dominated supports leaves **121**
and preserves the recognized family for every superset query. Its required
preparation graph shrinks **4,092 -> 3,804 nodes**; this candidate has not been
benchmarked. Only **10/4,102 preparation nodes** are unused by the current full
bank and query proofs, so simple pruning offers little. No rows were deleted.
The main cost is real retained proof data plus repeated accounting over it.

Resume `experiments/results/cnf-unsat-support/checkpoint.json`; the bound study
points to `all-0/cores.json`. Preserve inherited studies and decision catalogs,
plus `unsat_support_study`, `unsat_support_decisions` and `reference_union`.
The union retains **13,869 keys / 43,380,736 SQLite / 3,479,528 gzip bytes**.
The new catalog has **139 direct certificates and 53 explicit guarded cofactor
records**; never substitute a cofactor key for the complete query identity.
Structural authority remains **2,614 patterns / 259 pairs / seventeen missing
children**, original **17/24 / 999 proof steps**, and separate supplemental
**24/24 / 208 proof steps**. Original case 7 is its separate discovery pointer.

All **403 tests**, nine cold archive checks / **3,456 trial query replays**, the
support screen, every union node, 269 inherited decisions and all 192 new
decisions pass. Earlier 330 sources, 3,723 artifacts / 65 manifests and 64 proof
blocks are preserved. Runtime binds 334 sources; post-hoc attribution and warm
profiling bring the final ledger to 336. These are constructed development
inputs, not independent evidence for uniformly efficient arbitrary SAT.
Checkpoint SHA-256: `07e1a04864038caf4ba5a60b388e8c22b1c90116d9b11d819e7b7bd7dd7d31cf`.
Report SHA-256: `f732924b833023efc8f3a52a33071bdff524d7abc105790eed8f41c8bfb4fdba`.
The new manifest adds **60 artifacts**; the next audit inherits **3,783 artifacts /
66 manifests**. The manuscript builds to **191 pages**.


## 2026-11-16: exact insertion deltas over persisted proof graphs

[Incremental archive accounting](incremental-archive-accounting.md) removes the
full-history query scans identified by the previous profile. On the next **192
unseen double deletions**, complete time falls **37.48164 -> 14.81201 s (60.48%)**,
and query time **23.96449 -> 1.37640 s (94.26%)**. All modes use the same retained
145-core bank and 13,869-key seed; initial extraction remains charged separately.
The existing ledger accounts for an 18.65% complete-time reduction; adding the
new guarded insertion cursor saves a further 51.42%. Full inventories fall
**772 -> 3**, with final preservation and cold proof checks retained.

**Regressions and boundaries:** peak RSS rises **9.56%** to 448,435,541 bytes.
Accounting adds 4 KiB SQLite / 696 gzip bytes; logical proof rows are identical.
The cursor requires an exclusively owned append-only session, detects external
commits/schema changes and rejects local rewrites. Opening, conflict repair,
full cold replay and compression remain charged. No proof-space compression,
new search algorithm, broader structural closure or amortized break-even is shown.

**Highest next cost target:** the unchanged cold audit is 67.95% of candidate
worker time, compression another 17.09%. A separate cold profile attributes
**7.21981 s** to **384 full archive-size censuses** within a **14.87488 s**
instrumented audit. Test one independently checked census for an immutable
snapshot while retaining every proof and query check. Also locate the RSS
regression before claiming a memory improvement. Do not mix instrumented and
unprofiled timings or add nested profiling categories.

**Next structural target:** all modes return 96 SAT / 96 UNSAT, with 41 core
hits, 96 witness publications and 55 guarded negative queries. Of these, 44
use fresh search, accounting for all **202 expansions**, including 56 splits. Cases 66 and 76 each use 16
expansions, case 41 uses 12. Inspect their shared supports/cofactors for further
reuse. Case IDs belong to this experiment's catalog. Repeated visits add no rows.
The antichain of 121 old supports remains an unbenchmarked alternative; it
preserves recognized supersets but need not reduce these unresolved searches.

Resume `experiments/results/cnf-incremental-archive/checkpoint.json`. Preserve
all inherited studies and decisions plus `incremental_archive_study`,
`incremental_archive_decisions` and `reference_union`. The new union retains
**14,208 keys / 44,781,568 SQLite / 3,563,875 gzip bytes**. Its new catalog has
**137 direct query certificates / 55 guarded cofactor records**; the latter
require source, guard and child together. Structural authority is unchanged:
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 proof
steps, separate supplemental 24/24 / 208, and original case 7's discovery pointer.

All **418 tests**, nine cold archives / **3,456 trial query replays**, every union
node, 461 inherited decisions and all new decisions pass. Preserve 336 earlier
sources, 3,783 artifacts / 66 manifests and all 64 proof blocks. Runtime binds
341 sources; the attribution and cold-profile tools bring the final ledger to
343. The manuscript builds to 192 pages without warnings.
Checkpoint SHA-256: `53cf74216546839373aeb00d7d14321be0617a3b35da4a2cefa086aa1ee6a02d`.
Report SHA-256: `9feaf6eb279c05a8355c19e1d855eba693946a9be536d8367e24e299acab0c89`.
The new manifest adds **48 artifacts**; the next preservation audit inherits
**3,831 artifacts / 67 manifests**.


## 2026-11-16: one census per cold proof snapshot

[Snapshot replay](snapshot-replay.md) replaces 384 repeated cold size scans with
one independent census on a pinned read-only view. It runs the same frozen
complete audit and verifier. On the next 192 unseen double deletions, mean
complete time falls **15.15167 -> 7.84969 s (48.19%)** and cold replay
**10.43075 -> 3.12634 s (70.03%)**. Four alternating process pairs preserve
identical expansion work and identical logical/physical proof archives. Peak
RSS rises **0.39%**; no memory or storage reduction is shown. The earlier delta
memory regression remains open.

**Current largest costs:** complete cold verification is **39.83%** of candidate
worker time, compression **33.07%**, query work **16.20%**, setup **9.56%**.
Further total-cost improvements need evidence about repeated proof normalization,
allocation or rewriting unchanged persistent evidence. Profile before choosing
another checker optimization; retain every logical check and all old certificates.
Snapshot totals are independently computed, not trusted from saved accounting.
The benchmark uses private closed clones and one owned process per audit; shared
service concurrency and hostile private-connection changes are outside scope.

**Next primary structural target:** **37 negative queries** still require fresh
search and account for all **270 expansions / 85 splits**. They belong to 40
guarded negatives; all modes otherwise use 54 core hits and 98 witness answers,
returning 98 SAT / 94 UNSAT. Cases 100, 41 and 188 use 21, 19 and 18 expansions;
original template 12 supplies 129/270. Compare refutation supports and guarded
cofactors across these cases. A full-query negative certificate requires checked
composition of the stronger UNSAT premise and the restricted child; treating
the child as the query is invalid. Charge construction, checking and persistence
when testing any transfer. The 121-core antichain remains unbenchmarked and
preserves existing superset coverage rather than expanding it.

Resume `experiments/results/cnf-snapshot-replay/checkpoint.json`. Preserve every
inherited study/decision field plus `snapshot_replay_study`,
`snapshot_replay_decisions` and `reference_union`. The union adds 422 keys and
retains **14,630 keys / 46,530,560 SQLite / 3,674,583 gzip bytes**. The new catalog
has **152 direct roots / 40 guarded cofactor records**; guarded replay binds the
source, guard and child together. All 384 earlier double-deletion answers were
excluded from selection, including those without direct roots. Do not multiply
speedups across different input sets or ignore earlier acquisition costs.

All **426 tests**, eight complete archive checks / **3,072 trial query replays**,
every union node, **653 inherited decisions** and all new decisions pass using
the ordinary solver for independent validation. All 343 prior source bindings,
3,831 artifacts / 67 manifests and 64 proof blocks are preserved. Runtime binds
347 sources; the post-hoc analyzer brings the final ledger to 348. The manuscript
builds to 193 pages without warnings. Structural authority is unchanged:
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
Checkpoint SHA-256: `86ed6d602def81787d3b1b88c9b3151f8ccba1929f223d73a279acd438bd2bfe`.
Report SHA-256: `0b5be879e1beeda66a27fef48fd42cfa3fa5f7df02cd73bdc6e8202fe0f9fe22`.
The new manifest adds **42 artifacts**; the next preservation audit inherits
**3,873 artifacts / 68 manifests**.


## 2026-11-16: checked support transfer between guarded cofactors

[Cofactor support reuse](cofactor-support.md) certifies **16 previously uncached
restricted subproblems** through checked clause containment. Fresh expansions
fall **234 -> 162 (30.77%)**, and query time **1.33223 -> 0.87849 s (34.06%)**.
But constructing the whole bank adds **1,310 proof nodes** and makes complete
time **7.93324 -> 9.75898 s (23.01% worse)**, peak RSS **9.23% higher**, and SQLite
**3.23% larger**. Every matched pair regresses in total time. Keep this optional;
fewer expansions do not establish an end-to-end gain.

**Highest next target: defer new support proofs until a match.** Preparation
visits 1,075 old negative proof nodes and constructs 112 raw supports; the
containment antichain has 104 and preserves every superset match. Only 14 of
those supports are used here. The full retained bank needs 1,272 preparation
nodes, but the matched supports and query proofs need only **118**. Simple
pruning saves at most 38 nodes; building only after a checked match is the more
credible next test. Support proposals alone must never justify UNSAT. Discovery,
materialization, checking and persistence must all remain charged. The policy
has not yet been implemented or measured; selecting only the 14 observed cores
would use future workload information and can lose coverage.

**Preserve and reuse this acquired bank:** its 104 cores are already materialized
in the latest union. Load `cofactor_support_bank` and its `cores` field for warm
runs instead of extracting them again. To evaluate a new construction policy,
use explicitly matched historical seed clones or newly discovered supports, and
retain an unseen stream; do not present already-paid construction as a saving.

**Coverage limits and remaining cases:** 145 of 148 inherited guarded decisions
are negative; the three SAT cofactors do not supply negative supports. The new
stream returns 84 SAT / 108 UNSAT, with 63 old full-query core hits, 83 witness
publications and 46 guards (45 negative, one positive). Six targets were cached.
All 72 avoided expansions come from the 16 new cofactor hits. Each measured hit
shares the guard clause of its first retained origin; cross-guard transfer is
covered only by a unit test. No broader cross-category coverage is established.
The candidate still performs 151 negative / 11 positive expansions on 24 cases.
New-catalog case 7 is SAT; it is distinct from original structural case 7.
Largest remaining negatives are new cases 191, 82, 112, 184 and 87.

Resume `experiments/results/cnf-cofactor-support/checkpoint.json`. Preserve all
inherited fields plus `cofactor_support_study`, `cofactor_support_decisions`,
`cofactor_support_bank` and `reference_union`. The union retains **16,320 keys /
49,610,752 SQLite / 3,953,721 gzip bytes**. Earlier payloads win overlaps; sixteen
alternate certificate occurrences remain in trial archives. The new catalog has
**146 direct roots / 46 guarded records**. Guarded decisions bind source, guard
and child together; a negative child alone is not the complete-query identity.

All **434 tests**, eight complete archive checks / **3,072 trial query replays**,
every union node, **845 inherited decisions** and all new decisions pass. All
348 prior sources, 3,873 artifacts / 68 manifests and 64 proof blocks are
preserved. Runtime binds 352 sources; the post-hoc analyzer brings the ledger to
353. The paper builds to 194 pages without warnings. Structural authority stays
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
Checkpoint SHA-256: `c27c247ca9b278ab7ce44fab7db020a933dc5dc1a688c4a3e01e5fc85c3c11f8`.
Report SHA-256: `6d2f204b3476475735747858344b2caaef52e86921b2e7fecf20672e21226692`.
The new manifest adds **50 artifacts**; the next preservation audit inherits
**3,923 artifacts / 69 manifests**.


## 2026-11-16: support proofs constructed on demand

[Deferred support construction](deferred-support.md) now implements the prior
highest-priority experiment. On a further 192 unseen constructed inputs, eager
and deferred policies transfer the same 19 supports to **23 novel targets** and
reduce fresh expansions **302 -> 177 (41.39%)**. Deferral constructs **209 rather
than 1,310** support-proof rows, cutting all new rows **1,648 -> 547**. Complete
time falls **11.43996 -> 10.30105 seconds (9.96%)** against eager construction,
but remains **9.21% above the old-bank control's 9.43274 seconds**. All three
matched triples have both effects. Keep the mode optional.

**What is established:** discovery returns the same 104-support antichain without
publishing derived proofs. A matched proposal must be materialized and checked
before the frozen subset rule can publish UNSAT. All 209 materialization rows
are used by this stream's query proof closure; 83 proposed roots remain pending
in the deferred trial. Eager construction retains 1,101 additional preparation
rows outside that query closure. This is measured liveness, not a minimum-proof
guarantee. No prior result is deleted. Guarded answers still require the complete
source--guard--child evidence.

**Cost limits:** mean query time is 19.22% higher than eager construction because
needed construction moves to the query, although complete time improves. Mean
RSS is 3.78% lower than eager, but paired differences change sign; no robust memory
gain is established. SQLite falls 2.92% and gzip 4.47% against eager. Relative to
the old bank, mean RSS rises 1.87%, gzip rises 0.17%, and raw sidecars add further
space. Discovery still costs **1.22612 seconds**, against **0.33067 seconds** of
query savings over the old bank. Cold replay and compression remain the largest
phases, at 34.94% and 29.71% of complete deferred time.

**Next acquisition target:** reuse persisted ready supports and source-bound
proposals, then profile incremental discovery on genuinely new negative sources.
Do not repeatedly re-extract the existing 104-core bank. Before another global
recognizer, inspect the **21 unmatched negative queries / 177 expansions** for
shared conditional supports, particularly template 8 (**90 expansions**). New
study cases 164 (20), 35/160 (17 each) and 16/136 (16 each) are the largest misses.
Every measured hit still shares its first origin's guard clause. Cross-guard
and broad cross-category discovery remain open; constructed neighbouring inputs
do not demonstrate an efficient partition of arbitrary SAT.

**Comparison scope:** all workers use identical historical **14,630-key**
pre-acquisition clones. Selection excludes all **768** previous sidecar answers
and complete roots from the **16,320-key latest authority**, which stays
preserved with its already-ready bank. This isolates a construction policy,
not savings from rebuilding an already-paid bank. The new outer timer includes
final digest and report generation; historical percentages are not composable.

Resume `experiments/results/cnf-deferred-support/checkpoint.json`. Preserve every
inherited field plus `deferred_support_study`, `deferred_support_decisions`,
`deferred_support_proposals` and `reference_union`. The union has **16,760 keys /
51,294,208 SQLite / 4,046,593 gzip bytes**, with 440 new keys and 46 alternate
certificate occurrences retained in trials. The new catalog has **138 direct
roots / 54 guarded negatives**. All 104 previously ready cores remain ready in
the final union; the 83 pending proposals describe only the historical trial.

All **442 tests**, nine full archive checks / **3,456 trial query replays**, every
union node, **1,037 inherited decisions** and all new decisions pass. Prior
**353 sources / 3,923 artifacts / 69 manifests** are unchanged. Runtime binds
357 sources and the analyzer brings the ledger to 358. Structural authority stays
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208, and original case 7's discovery pointer.
All 64 manuscript proof blocks remain unchanged; no new Lean claim.
Checkpoint SHA-256: `711be45dc4a9e5a79c3c94aaac179ee1a44af1013ca364f9633df8fc97af20cc`.
Report SHA-256: `3c762d725a6e0f058e309a098f124334a38feee3f4e8856069a2a41a5974bbb7`.
The manuscript builds to 195 pages without warnings. The new manifest binds
56 artifacts; the next audit inherits **3,979 artifacts / 70 manifests**.


## 2026-11-16: incremental discovery and old evidence costs

[Incremental support discovery](incremental-support.md) reuses the saved index
and extracts supports only from newly acquired negative results. Adding **99**
new sources to **145** old ones gives exactly the same frontier as full
rediscovery: **168 raw supports / 151 retained entries**, up from 112 / 104.
Three superseded old entries remain in history. Pending proposals survive
restart and further extension; they cannot justify UNSAT before materialization
and ordinary proof checking.

**Coverage gain:** on another 192 unseen constructed neighbours, the expanded
index transfers **18 rather than 14** targets and reduces expansions
**199 -> 162 (18.59%)**. Cases 53, 121, 163 and 190 account for all 37 saved
expansions. Three materializations add 39 proof rows. All modes return
**105 SAT / 87 UNSAT**, including one guarded SAT result. Every measured transfer
still shares its first origin's guard clause; broad cross-category discovery
remains open. Both extension modes have identical logical/physical archives.

**Cost result:** incremental extraction visits **715 rather than 1,697** proof
nodes (57.87% fewer), but preparation only falls **1.82786 -> 1.78856 seconds**.
Complete time is **11.69363 -> 11.64076 seconds**, a near-flat **0.45%** difference,
with no demonstrated practical speedup or memory improvement. Against loading
the ready bank (**11.17962 seconds**), extension still regresses **4.12%**, in
every matched triple. Gzip plus raw sidecars grows **11,064,817 -> 11,617,440 bytes**.
Keep extension optional. This is a current-union comparison, not another
historical construction replay: all workers begin with **16,760 keys**, and
selection excludes all **960** prior sidecar answers and cached complete roots.

**Next highest-value gap: repeated checking of saved evidence.** The diagnostic
records **7,216 proof reads / 14,281 canonicalizations** for incremental discovery,
versus **6,783 / 13,518** for rebuilding. Old provenance and ready-core checking
offset avoided extraction. Separate active match requirements from full lineage
audit, retaining both: a checked negative core justifies subset reuse independently
of its discovery guard, while a pending proposal needs checked materialization.
Test demand-driven checks or reuse within an owned append-only session, retaining
invalidation and a separately charged complete cold audit. Do not persist unchecked
trust flags. The diagnostic overlapped the correctness suite; use its call counts
and structure, not its elapsed times. Timed workers ran alone.

**Remaining coverage probes:** 18 negative cases need 154 expansions; guarded
SAT case 188 needs eight. Template 8 contributes 66 expansions, template 6 adds
51 and template 12 adds 45. Largest new-catalog negatives are 61 (19), 72 and
142 (18 each), and 19 (14). Keep these distinct from original structural case IDs.
Cold audit and compression remain 34.93% and 29.74% of complete incremental time.
The 151-entry trial frontier has 104 available roots and 47 pending proposals;
these 104 available roots are a different set from the original 104 ready cores.

Resume `experiments/results/cnf-incremental-support/checkpoint.json`. Preserve
all inherited fields plus `incremental_support_study`, `incremental_support_decisions`
and `incremental_support_proposals`. The latter stores the complete extended
index (including all raw supports, origins and dominance), not just ready cores.
For the next extension, supply the five old decision catalogs in their existing
order and only genuinely new batches. Repeated batch identities reject. Use the
extended index to preserve acquired discovery rather than returning to the old
104-entry frontier. Match-time proof checks still apply to every pending root.

The union retains **17,161 keys / 52,809,728 SQLite / 4,124,643 gzip bytes**, adding
401 keys while keeping every earlier payload. Eight alternate certificate
occurrences remain in trial archives. The new catalog has **149 direct roots /
43 guarded decisions** (42 negative, one positive). All 104 original ready cores
remain in history; the extended frontier has 104 available roots and 47 pending
proposals in the union as well as the candidate trials.

All **451 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,229 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **358 sources / 3,979 artifacts /
70 manifests** remain unchanged. Runtime binds 363 sources; the post-hoc analyzer
brings the ledger to 364. Structural authority remains 2,614 patterns / 259 pairs /
17 missing children, original 17/24 / 999 steps, separate supplemental 24/24 /
208, and original case 7's discovery pointer. No new Lean or unrestricted-SAT claim.
Checkpoint SHA-256: `6c60e95e1a8f0f0dc12fc2e24dba38178cc35ae5e13a07a28d43b30d0180700c`.
Report SHA-256: `c5c12f205dd77b370d4120ce0baf06e33ab0ecc1268e2fa7d8ac14fbd4ef5275`.
The manuscript builds to 196 pages without warnings; all 64 proof blocks are unchanged.
The new manifest binds 63 artifacts; next audit inherits **4,042 artifacts / 71 manifests**.


## 2026-11-16: active support checks with full cold lineage

[Active support checking](active-support.md) avoids checking unrelated old
lineage before queries while retaining complete cold proof, query and provenance
audit. Mean complete time falls **11.52069 -> 10.36579 seconds (10.02%)** versus
eager checking, and **6.85%** versus the loaded-index control. Every matched
triple improves. Both extension modes retain identical proof archives and search
work; no logical check is replaced by an unchecked persisted trust flag.

**Why it is sound:** a match checks the actual core's canonical identity and
ordinary negative proof before subset publication. Missing roots require checked
materialization. The current query's guard remains checked online. The cold
auditor runs the unchanged full proof/query audit, then checks all index origins
and dominance on the same pinned snapshot before closing it, including on
failure. Historical lineage is deferred, not removed. All modes pay for the
complete audit; this timing boundary is broader than earlier benchmarks.

**Measured work:** active preparation normalizes **517,355** literal occurrences
rather than **1,904,438**, and makes **1,563** database lookups rather than **6,625**.
Preparation falls **1.78958 -> 0.51719 seconds**. Query time rises **27.91%** as
checks move to active use, but complete time improves. Mean peak RSS is **7.89%**
below eager and **5.06%** below loaded; paired eager differences change sign.
There is no asymptotic memory improvement or persistent-space saving. Gzip plus
raw sidecars rises **11,657,158 -> 11,894,676 bytes** against loaded.

**Negative discovery result:** 42 new negative sources expand the frontier
**151 -> 170 entries**, but all modes still make **25 transfers / 187 expansions /
64 splits**. There are **no additional target hits**. Index growth is not a
coverage measure. The active method has not been compared with active loading
without extension, so this run does not establish that growing the bank pays.
Reuse the acquired 170-entry index rather than rebuilding it for a later claim.

**Next coverage target:** template 12 accounts for **169/187** remaining
expansions, template 8 for 18 and template 6 for none. Fifteen negative queries
need 145 expansions; guarded SAT cases **137 and 2** need **26 and 16**. Largest
negatives are 29 (23), 140 (18), 116 (17) and 149 (15). These are new-catalog IDs.
Inspect shared conditional structure and retained SAT-witness repair/transfer
on these residuals, including genuinely different guards. Every measured support
hit still shares its first origin's guard clause. Broader cross-category coverage
remains open. For cost work, compare active loading before further acquisition;
complete cold audit and compression now cost **40.03% / 31.81%** of active time.

All modes return **97 SAT / 95 UNSAT**, with 95 witness publications, 51 old
full-query core hits and 46 guards (44 negative, two positive). Four targets are
cached. Extension uses 22 supports for 25 transfers and materializes four roots
through 13 proof rows. Its frontier has 106 ready roots and 64 pending proposals.
The comparison uses the latest **17,161-key** union, excludes all **1,152** prior
sidecar answers and complete cached roots, and visits 192 new constructed
neighbours twice in three balanced process triples. This is not an arbitrary-SAT
benchmark, minimum-expansion result or uniform-polynomial guarantee.

Resume `experiments/results/cnf-active-support/checkpoint.json`. Preserve all
inherited fields plus `active_support_study`, `active_support_decisions` and
`active_support_proposals`. Load this complete 170-entry index, including pending
entries and its raw-support/origin history. Its six source catalogs stay in their
existing order; a subsequent extension must supply only a genuinely new batch.
The union contains **17,532 keys / 54,337,536 SQLite / 4,206,056 gzip bytes**,
adding 371 keys while retaining every old payload. Two alternate certificate
occurrences remain in trial archives. New decisions comprise **146 direct roots /
46 guards**, including the two SAT cases. The union also has 106 available retained
roots and 64 pending ones; pending entries cannot justify UNSAT before verification.

All **461 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,421 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **364 sources / 4,042 artifacts /
71 manifests** remain unchanged. Runtime binds 368 sources; the analyzer brings
the ledger to 369. Structural authority stays 2,614 patterns / 259 pairs / 17
missing children, original 17/24 / 999 steps, separate supplemental 24/24 / 208,
and original case 7's discovery pointer. No new Lean claim.
Checkpoint SHA-256: `ddab750444c8546722ca5d15acee2abbda32455e9dd2dcc785715ebdcfaa62b1`.
Report SHA-256: `9b616b087f471249cebe07ea6c29a864980c46d3736425e613b6cfa1de556b70`.
The manuscript builds to 197 pages without warnings; all 64 proof blocks are unchanged.
The new manifest binds 55 artifacts; next audit inherits **4,097 artifacts / 72 manifests**.


## 2026-11-16: witness signatures separate lookup from discovery

[Bounded witness exploration](witness-signatures.md) reaches two hard historical
SAT queries through sequences of flips, but adds no transfers on the next 192
inputs. All 96 SAT inputs already use the old witness route. Total runtime
regresses 6.04%; all 214 remaining expansions are UNSAT cases. Keep the new
bank optional. Equal false-clause signatures compress exact lookup but do not
preserve flip transitions; a two-variable counterexample is tested and recorded.
The fixed budget, all accepted assignments, failed attempts and seed origins persist.

The next coverage target is shared negative cofactors: template 6 now contributes
94 expansions, template 8 contributes 69 and template 12 contributes 51. Current
cases 123/189 share guard [130,140] and cost 17/16 expansions. Compare their
conditional supports and proof structure, then test transfer across different
guards and templates. Cold audit and compression remain 40.45%/33.11% of total
control runtime. Broader pattern coverage and efficient arbitrary-SAT acquisition
remain open; polynomial signature counts do not imply cheap construction.

Resume `experiments/results/cnf-witness-signatures/checkpoint.json` (17,947 keys).
All 473 tests, nine complete archive audits, every union node, 1,613 inherited
and 192 new decisions pass without fresh validation search. Old results and the
170-entry negative frontier are preserved. Structural authority remains 2,614
patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps and separate
supplemental 24/24 / 208. The paper builds to 198 pages with 64 unchanged proof
blocks. No new Lean or unrestricted polynomial SAT claim.


## 2026-11-17: causally sliced unit supports

[Causal support extraction](causal-support.md) removes propagated assignments
unused by the conflict or selected negative child proof, while retaining their
backwards dependency closure. All derived certificates use the unchanged checker.
Nine additional cofactor hits reduce expansions **195 -> 100 (48.72%)** on a
fresh 192-query stream. Extending the previous extraction with the same new
sources gives no additional hits. All measured causal hits still share the first
origin's guard, so broad cross-guard transfer remains open.

Complete time increases **15.87%** against active loading despite **27.04% lower
query time**. Re-extracting all 389 origins costs 2.33282 seconds; 31 materializations
add 275 proof rows, raising new rows 423 -> 553. The next cost target is active
loading of the acquired causal frontier, followed by incremental causal discovery
on novel queries. Repeated exact queries cannot establish that new acquisition
amortizes. Remaining work is 95 negative expansions plus five on SAT case 42;
negative cases 187/159/50/60 cost 20/17/16/16 expansions.

Resume `experiments/results/cnf-causal-support/checkpoint.json` (18,672 keys).
Causal proposals require `CausalCoreBank` and its matching materializer; 34 roots
are ready and 142 remain pending. Both new frontiers use eight ordered provenance
catalogs, while the old 170-entry bank retains its six-catalog history. Every old
checkpoint field and all trial certificates remain preserved.

All 486 tests, nine complete archive audits, all union nodes, 1,805 inherited and
192 new decisions pass without fresh validation search. All 375 prior sources
and 4,174 artifacts / 73 manifests are unchanged. Structural authority remains
2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps and
separate supplemental 24/24 / 208. The paper builds to 199 pages with 64 unchanged
proof blocks. No new Lean, minimum-core or unrestricted polynomial SAT result.


## 2026-11-17: retain causal discovery and compare proof choices

[Retained causal loading](retained-causal.md) avoids all 2,851 repeated discovery
node visits, reducing preparation 2.29443 -> 0.08099 seconds and total runtime
12.74826 -> 10.63701 seconds (16.56%) against rebuilding. The frontier files
and proof databases are identical, and every match plus complete cold lineage
remains checked. Pending roots still require the causal materializer.

Against loading the legacy frontier, six extra hits reduce expansions 120 -> 93
(22.5%), but total time is effectively flat and measured peak RSS rises 14.56%.
On the 19 targets both banks cover, causal materialization creates 74 rows versus
33 for legacy. Choosing an already cheaper proof is the next matched experiment;
that apparent 41-row opportunity is not a guaranteed saving under changed cache
histories. Remaining work comprises 74 negative / 19 positive expansions. Negative
cases 14/161 cost 19/15; SAT cases 45/91 cost 14/five. All measured transfers still
share their first origin's guard, so broad cross-guard coverage remains open.

Resume `experiments/results/cnf-retained-causal/checkpoint.json` (19,091 keys).
It adds `retained_causal_study` and `retained_causal_decisions`, preserving earlier
frontiers, their pending entries and every prior field. Both measured indices
retain their eight-catalog / 389-origin lineage; this run adds no new sources.
The causal frontier has 48 ready roots and 128 pending in the union. Incremental
causal discovery from new batches remains separate and unimplemented here.

All 492 tests, nine complete archive audits, all union nodes, 1,997 inherited and
192 new decisions pass without fresh validation search. All 381 prior sources
and 4,230 artifacts / 74 manifests remain unchanged. The broader test log retains
24 unclosed-SQLite ResourceWarnings during older tests; focused new tests emit
none with warnings enabled, and allocation origins are untraced. Structural
authority remains 2,614 patterns / 259 pairs / 17 missing children, original
17/24 / 999 steps and separate supplemental 24/24 / 208. The paper builds cleanly
to 200 pages with 64 unchanged proof blocks. No new Lean or general SAT bound.


## 2026-11-17: choose among acquired negative proofs

[The combined dispatcher](proof-choice.md) checks ready negative roots across
both acquired frontiers before materializing another support. With no ready
match it uses legacy-first fallback and the appropriate checked extractor.
Both complete provenance histories are audited on the same frozen snapshot;
compact references avoid duplicating the historical metadata in the composite.
Independent replay reconstructs choices from the actual append history.

On 192 fresh queries, materialization falls 137 -> 57 rows and new rows
351 -> 271 versus causal-only reuse, retaining 30 transfers / 35 expansions.
Mean complete time improves 10.78%, with one paired regression; peak RSS rises
5.53% in all pairs. Keep the policy optional. The next discovery gap is incremental
acquisition and the seven remaining negative residuals, rather than repeated
reconstruction of old support descriptions. Full cold replay and compression
still consume 43.69% / 31.96% of complete time.

Verified resume: `experiments/results/cnf-proof-choice/checkpoint.json` retains
19,543 keys, 149 new direct results and 43 guarded negative decisions, preserving
all earlier payloads and checkpoint fields. Both source banks and their pending
entries remain bound; 137 later guarded-negative records are available for the
next acquisition experiment. All 502 tests, nine complete archive audits, all
union nodes and 2,189 inherited decisions pass. Structural authority remains
2,614 patterns / 259 pairs / 17 missing children. The paper builds to 201 pages
with 64 unchanged proof blocks. Older-test SQLite warnings are preserved;
the 10 focused new tests emit none with warnings enabled.


## 2026-11-17: incremental acquisition and alternative guards

[Incremental causal extension](incremental-causal.md) extracts only new
source records and merges exact containment coverage while retaining raw history
and first-origin provenance. Complete independent discovery gives the same
frontier: 3,708 versus 1,181 support-node visits. Both full old/new lineages and
all proof/query audits remain mandatory; pending hints need checked derivation.

The 27 added retained entries are unused on the next 192 queries. Both modes
make 37 transfers, expand 126 nodes and add 364 rows, with byte-identical proof
databases. Mean complete time regresses 4.89%. Preserve the learned state but
keep acquisition optional. Next, test alternative guards: the diagnostic finds
an old ready support for case 121's other target, with 20 local expansions
potentially avoided. No new guard-selection policy has been benchmarked yet.

Verified resume: `experiments/results/cnf-incremental-causal/checkpoint.json`
retains 19,907 keys, all previous payloads and checkpoint fields, plus the optional
203-entry causal frontier. All 510 tests, eight complete archive checks, all union
nodes and 2,381 inherited decisions pass. The new index has 62 ready roots /
141 pending. Structural authority remains 2,614 patterns / 259 pairs / 17 missing
children. The paper builds to 201 pages with 64 unchanged proof blocks. Older-test
SQLite warnings remain recorded; eight focused new tests emit none.


## 2026-11-17: bounded alternative-guard selection

[The bounded selector](alternative-guard.md) checks at most one additional
matching extension after a first-target archive/support miss. It reads only
available target proofs or ready negative supports; the unchanged ordinary
publication and guard path completes the result. Independent reconstruction
checks every selection against archive contents before its query.

One changed guard reduces expansions 142 -> 135 and new rows 362 -> 356. Mean
complete time rises 1.30% with large order-correlated variation. Keep the policy
optional. Frozen-worker replay preserves semantic baseline records and identical
proof bytes. Historical case 121 works with fresh search disabled and one new
subset proof, retained in a separate regression archive. The next implementation
gap is safely pricing/bounding pending alternative materialization on cases
23/85, rather than deriving every match regardless of cost.

Verified resume: `experiments/results/cnf-alternative-guard/checkpoint.json`
retains 20,270 keys, all previous payloads and checkpoint fields. All 518 tests,
eight fresh-trial archive checks, all union nodes and 2,573 inherited decisions
pass. Frozen-worker parity and historical case 121 also pass; its one additional
regression proof remains in a separately retained archive. Structural authority
stays 2,614 patterns / 259 pairs / 17 missing children. The paper builds to 202
pages with 64 unchanged proof blocks. Older-test SQLite warnings are preserved;
eight focused new tests emit none.


## 2026-11-17: price pending alternative proofs

[Controlled prefix probes](pending-guard-costs.md) check all six pending matches
from the preceding guard study. Only case 85 reduces the publication footprint:
six fresh expansions / six rows become two rows, with added payload 11,350 ->
1,805 bytes. Case 23 adds 35 rows versus eleven; case 103 adds twelve versus one
under every candidate. All alternatives avoid fresh SAT search, demonstrating
that expansion counts alone do not price total work.

The useful distinction is a checked terminal unit conflict versus a unit proof
with a child. One terminal origin needs at most one derived core row and one
target subset row; this bounds neither bytes nor recognition/checking time.
The next target is a terminal-origin filter on fresh excluded inputs, keeping
recursive cases as controls. No new source-query coverage or runtime guarantee
is claimed. Resume `experiments/results/cnf-pending-guards/checkpoint.json`
(20,340 keys, 70 added, all prior payloads preserved). Nine reconstructed arms,
2,765 inherited decisions and 32 relevant tests pass. Structural coverage and
its separate original/supplemental proof authorities remain unchanged.


## 2026-11-17: terminal admission misses the fresh unresolved structure

[The fresh comparison](terminal-guard.md) gives no added coverage: both policies
use 68 expansions and 309 new rows on 192 excluded neighbours. Historical
controls admit terminal case 85 and reject recursive cases 23/103. The new scan
adds 3,064 candidate inspections but finds no pending support in the eight
unresolved targets. Timing variation establishes no total speedup.

Current cases 56 and 176 account for 41/68 expansions. Checked cores missing one
clause justify additional restrictions, reducing sizes 79/218 -> 67/172 and
86/240 -> 77/209 clauses/literals. No restricted endpoint is already reusable.
The next task is checked composition and a matched remaining-solve comparison,
including SAT case 155 as a control against premature UNSAT. Preserve recognition,
premise publication, acquisition and persistence costs. Resume
`experiments/results/cnf-terminal-guard/checkpoint.json` (20,649 keys; all prior
payloads preserved). Full proof replay, 1,013 solver tests and two additional
condition tests pass; structural authority and existing proof blocks are unchanged.


## 2026-11-17: compose restrictions and locate duplicate checking cost

[Guard-chain composition](guard-chain.md) reduces expansions/new rows **68 -> 29**
on eight exact historical pre-query prefixes. Added native payload falls 57.72%;
serialized deltas plus composition records fall 13.47%. All six strengthened
premises already exist. Case 155 remains SAT. Selection/checking outweighs the
child-solve time saved in single samples; no total runtime or peak-memory gain
is established. A separate read-only probe finds that checking those premises
without a separate support-proof traversal reduces verified nodes **148 -> 57**.
Implement that lookup order and prepared near-containment membership next, then
test new excluded queries. Missing premises still require checked derivation.

Resume `experiments/results/cnf-guard-chain/checkpoint.json`: 20,666 native keys,
17 added and all prior payloads preserved, plus eight checked chain conclusions.
Native proof format is unchanged; optional `GuardChainBank` must load and check
the bound sidecars for composed source reuse. All 16 trial arms, 2,957 inherited
decisions and 1,022 solver tests pass. Original and supplemental structural
coverage remain separate and unchanged. Historical savings do not establish
fresh coverage, optimal expansion or a polynomial bound for arbitrary SAT.


## 2026-11-17: fresh premise-first guard chains

[Prepared recognition and checked-premise priority](premise-guard.md) reduce
expansions **139 -> 67** and new native rows **436 -> 364** on 192 fresh neighbours.
The new selector preserves the old chain policy's native proofs while reducing
additional verified nodes **247 -> 102**. All eight strengthened premises already
exist. Seven cases improve, with no per-case expansion/publication regression.
Complete timings have mixed paired signs; retained trial bytes rise 0.414% versus
ordinary because chain records offset the smaller archive. No stable total-cost
or general memory gain is established.

The largest remaining case, 68, costs 27/67 expansions and is three clauses from
an overlapping ready core. Cases 6/135 cost seven each and need three/two missing
clauses. Next, price exact alternative coverage or disjoint branches by the first
falsified clause. A checked negative conjunction of several missing clauses
forces some clause false, not all. The pre-query diagnosis publishes nothing;
multiple-clause inference remains open. Cold checking and compact sidecars remain
supporting cost targets. Resume `experiments/results/cnf-premise-guard/checkpoint.json`
with 21,128 native keys, all prior payloads preserved, eight inherited and 192 new
chain conclusions. All 1,028 tests, six native/chain audits, 2,957 inherited ordinary
decisions and frozen-worker parity pass. No new Lean or unrestricted-SAT bound.


## 2026-11-17: exact multiple-clause composition and plan-cost gap

[First-false partitions](clause-partition.md) now cover a target using an existing
negative strengthened premise, earlier missing clauses held true, and the selected
clause falsified. All branches must be negative for UNSAT; a checked SAT branch
lifts to the original query. Native proofs remain unchanged; composed lookup
requires the bound partition sidecars. Exhaustive small-formula and SAT controls,
1,035 full-suite tests and independent native/sidecar replay pass.

Historical case 68 improves **27 -> 11 expansions** in the best tested order,
case 6 improves **7 -> 3**, and both case-135 orders regress **7 -> 8/10**. Trying
all eight plans costs 105 expansions versus 41 for the three baselines. These
post-hoc choices establish no fresh coverage or cheap plan-selection policy.
A read-only propagation probe finds terminal-conflict signals for the better
orders, but case 135's smaller residual still costs more. Next, implement bounded
screening that reuses its unit traces, retain 135 as a fallback control, and test
new excluded inputs with preparation, premise publication and cold replay charged.

Resume `experiments/results/cnf-clause-partition/checkpoint.json`: 21,225 native
keys, all previous 21,128 payloads preserved, and eight partition records for
three historical sources. All 2,957 ordinary inherited decisions and 200 inherited
chains replay. Structural authority and all 64 existing proof blocks remain
unchanged. No new Lean or unrestricted-SAT bound is claimed.


## 2026-11-17: bounded partition screening and a terminal-baseline counterexample

[Retained unit traces](partition-screen.md) now support bounded plan selection
and checked publication without repeating selected-branch propagation. Historical
controls use 23 new rows versus 41 baseline; nine wrapper/conflict publications
replace expansion calls and must remain in the accounting. Case 135's nearest
two-clause orders are rejected, but a three-clause alternative is admitted.

On 192 fresh queries, expansions 27 -> 26 coexist with rows 247 -> 249 and native
payload 495,506 -> 499,414 bytes. The only screened target already has a unit
conflict, so partitioning is unnecessary. Combined propagation visits rise from
8,190 to 12,369. Keep the selector optional; no stable runtime or peak-memory
improvement follows. First reuse the baseline terminal trace, then inspect
cases 43/172 (19 of 26 remaining expansions) after their extra guard, where this
policy currently stops screening. Plan budgets do not bound posting discovery,
cold proof checking or remaining unrestricted residual search.

All 1,042 tests, four fresh trial audits, six historical controls, 2,957 inherited
ordinary decisions and 406 composed records pass. The final union retains all
21,225 prior payloads and has 21,482 keys. Resume
`experiments/results/cnf-partition-screen/expanded-checkpoint.json`; the intermediate
fresh checkpoint and failed harness assumption are also retained. Preserve all
mixed sidecar catalogs separately from ordinary schemas. Structural authorities
and 64 prior proof blocks remain unchanged; no new Lean or unrestricted-SAT bound.


## 2026-11-17: terminal-first reuse and conditioned-core matching

[Terminal-first screening](terminal-first-screen.md) corrects unnecessary
repartitioning on saved case 176: three proof rows become one, native bytes
6,137 -> 2,229 and propagation visits 5,289 -> 1,110. No posting search, core read
or plan construction is needed after its baseline unit conflict. Prepared-index
setup and native verification remain charged. Nonterminal controls preserve
exact plans and proof deltas; no fresh coverage or stable total-time gain follows.

Cases 43/172 still hold 19/26 expansions after an extra guard. Their original
core bank has no eligible plan, but restricting checked negative cores by the
same guard assignments exposes two-clause gaps. Case 172's three-clause core-209
cofactor is already native-checked; case 43's nearest restricted roots need
certification or acquisition. Price these plans against ordinary clause splitting,
including model lifting and discovery. The read-only full-bank probe visits about
32,000 restriction literals per case across two passes and publishes nothing.
Assignment-sensitive projection caching is a candidate, not a measured guarantee.

Resume `experiments/results/cnf-terminal-first-complete/checkpoint.json`: all
21,482 native keys and the existing compressed archive are retained unchanged;
eight sidecars preserve both control policies. All 1,047 tests, 2,957 ordinary
and 414 composed records pass. Earlier sources, artifacts, structural authorities
and 64 manuscript proof blocks remain preserved. No new Lean or arbitrary-SAT bound.


## 2026-11-17: conditioned acquisition and assumption reduction

[Conditioned-core controls](conditioned-core.md) add source-bound projection
records and checked acquisition when units refute a cofactor or expose two-CNF.
The narrower initial gate rejection is retained. Fifteen historical arms compare
baseline, both partition orders and direct acquisition of the identical premise.
All six conditioned/direct pairs have identical branch proofs and work; separate
cofactor acquisition adds storage. Case 43 improves by branch choice (10 -> 7
rows in direct reverse), 172 duplicates an existing-clause split, and 70 regresses.
Trying all alternatives costs 94 expansions versus 23 baseline. No cheap selector
or stable runtime/memory gain follows.

Next, price the single-assumption guards found by a checked read-only probe:
43 + [-230], 172 + [-40], 70 + [-40] each unit-refute. Their remaining child roots
are absent. Reuse traces, acquire and check the residual, then compare total cost
and excluded inputs. Causal slicing alone misses the removable assumptions in
43/172; repropagation after deletion finds them. General discovery remains open.

All 1,057 tests, fifteen audits, 2,957 ordinary decisions, 429 composed records
and six projections pass. Resume `experiments/results/cnf-conditioned-core-exposed/checkpoint.json`:
21,525 keys, all 21,482 old payloads preserved, six alternative certificates
retained separately. Prior 451 sources / 4,916 artifacts / 85 manifests and all
four frontier lineages pass preservation. Structural authorities and 64 paper
proof blocks remain unchanged. No new Lean or unrestricted-SAT bound.


## 2026-11-17: acquire single-assumption guards and expose local candidates

[Single-assumption acquisition](assumption-guard.md) now checks an unsplit terminal
before at most two supplied clause probes, retains failed attempts and publishes
only a checked unit-refuted premise. The remaining child is solved normally.
Nine historical arms give native rows 23 -> 20 and bytes 29,615 -> 24,582; case
70 regresses 4 -> 5 rows. Direct and trace acquisition store identical proofs.
Trace reuse avoids 1,166 repeated propagation visits, but total visits exceed
baseline (4,501 -> 5,907), and serialized deltas plus chains grow 10.91%.
A valid forced assignment is not a minimum-cost certificate.

Next, price target-local binary-incidence ranking: read-only checked probes find
43 + [-20], 172 + [-140], 70 + [50] within one/one/two attempts, without another
core-bank scan. All corresponding children are absent at the exact prefixes.
Both rankings select the same first conflict; later orders can differ. Fix the policy before testing
excluded inputs; retain 70 as fallback control and account for failed probes,
remaining solving, full chain sources and cold replay. No fresh gain is claimed.

All 1,064 tests and independent replay pass. Resume
`experiments/results/cnf-assumption-guard/checkpoint.json`: 21,528 keys, all
21,525 prior payloads preserved, nine new composed records and no alternative
native payloads. All 462 prior sources / 5,008 artifacts / 86 manifests, four
frontiers, structural authorities and 64 paper proof blocks remain preserved.
No new Lean or unrestricted-SAT theorem.

## 2026-11-17: fresh local guards expose the residual-admission gap

[Target-local discovery](local-guard.md) now reuses baseline propagation, ranks
unforced variables by original binary-clause incidence, and tests at most four
variables without another core-bank scan. Six historical arms lower rows
23 -> 19. Four workers on 192 excluded neighbouring inputs give 250 -> 250 rows:
seven explicit trace publications accompany the 19 -> 12 expansion reduction.
Propagation and serialized records increase, and both complete-time pairs regress.
The optional policy is therefore not promoted as a general improvement.

Fresh case 144 grows 3 -> 11 rows and contributes 10/12 remaining local child
expansions. The baseline reuses a checked negative dependency that the conditioned
path does not hit. Cases 167/190 shrink 8/4 -> 2/2 because their restricted children
unit-refute. Next, screen the child before publishing a guard, preserve cheap
native-family priority, reuse terminal traces, and retain ordinary fallback.
Measure at identical prefixes and another excluded set; keep useful nonterminal
historical cases 43/172 as controls. Cached-proof transport remains unimplemented.

All 1,069 tests, 12 focused tests, independent stream and cold checks pass.
Resume `experiments/results/cnf-local-guard/checkpoint.json`: 21,801 native keys,
all 21,528 old payloads preserved, 390 new composed records, no alternate payloads.
The 2,957 ordinary decisions, 438 earlier composed records and six projections
remain checked. All 469 prior sources / 5,057 artifacts / 87 manifests are preserved.
Union ready/pending frontiers are 131/39 (active), 139/68 (extended), 83/93
(causal), 83/120 (incremental causal); these are retained-bank availability counts,
not new structural authority. Structural checks and 64 proof blocks are preserved.
No new Lean, minimum-cost expansion or unrestricted-SAT result is established.


## 2026-11-17: admit checked children and retain rejection costs

[Child admission](child-admission.md) now checks an existing native child or a
unit-conflict trace before publishing a local guard, preserving cheap syntactic
families and native fallback for tautological sources. Eighteen exact-prefix
arms repair prior fresh case 144 (11 -> 3 rows), keep 167/190 at two rows, but
reject beneficial historical 43/172. Admission has at most two new native rows
and no general child expansion; fallback remains unrestricted. Rejected probes
are costly: historical propagation rises 4,501 -> 8,666 against baseline.

Next, measure another excluded stream and explore trace reuse or structural
admission for nonterminal children. All four rejected post-UP roots remain unknown
and outside cheap families; absolute literal size cannot separate beneficial 172
(112 literals) from regressing 70 (111). No fresh-stream or stable timing gain is
claimed. The 21,801-key archive is unchanged; 18 new composed records retain all
arms. All 1,076 tests, 19 focused tests and independent cold replay pass. Prior
475 sources / 5,115 artifacts / 88 manifests, four frontiers and structural
coverage are preserved. Resume `experiments/results/cnf-child-admission/checkpoint.json`.
No new Lean or unrestricted-SAT theorem.


## 2026-11-17: fresh admission reveals reuse after propagation

[Fresh child-admission streams](child-stream.md) now exclude inherited query and
native roots: four workers, 192 new queries, 101 SAT / 91 UNSAT answers. Rows fall
229 -> 221, but propagation rises 5,590 -> 11,343, sidecars grow 2.44% and both
complete-time pairs regress. Keep the gate optional. Eight trace publications
must be counted alongside the 17 -> 1 expansion reduction.

Case 85 exposes a concrete missing reuse step: after 23 forced variables the
residual is a checked positive binary clause already available at that prefix.
A read-only native/model check succeeds, yet discovery tries four premises and
fallback repeats propagation (4,795 + 955 visits versus baseline 955). Next,
recognize the propagated residual before probing, reuse the unit trace, and
price exact-prefix controls plus another excluded stream. No modified-policy
gain is claimed. Cold checking and duplicated sources remain larger supporting
full-cost targets.

All 1,076 tests, 19 focused tests and independent replay pass. Resume
`experiments/results/cnf-child-stream/checkpoint.json`: 22,036 keys, all 21,801
old payloads preserved, 384 new composed records and no alternative payloads.
Earlier 846 composed records, 2,957 ordinary decisions, six projections, 480
sources / 5,186 artifacts / 89 manifests and four frontier lineages are retained.
Structural authority is unchanged; no new Lean or unrestricted-SAT bound.

## 2026-11-17: reuse propagated residuals and retain the no-hit comparison

[The optional propagated-residual selector](propagated-reuse.md) checks the root
exposed by a nonempty forced prefix before probing new premises. It reuses the
saved unit trace for checked target publication, preserves old family priority
and rejection behavior, and admits missing native-family leaves only when enabled.
Case 85 now uses 955 rather than 5,750 propagation visits with the same one-row
result. Twenty-one exact-prefix arms retain all previous controls.

On another 192 excluded queries the new route never activates. Both admission
policies produce identical native payloads, 199 new rows and 14,907 propagation
visits, versus baseline's 215 rows and 9,528 visits. Added lookup/recognition and
0.12% larger sidecars remain charged; opposite timing-pair signs establish no
stable speedup. The new check does not earn the previous gate's fresh row saving.

Next, reuse baseline unit traces after a miss or rejected guard. Fresh cases
36/186 retain 13/1 forced variables but account for all eleven child expansions.
A posthoc diagnostic also checks that either value of case 36's canonical
variable 6 leaves two-CNF; case 186 has no such single-variable decomposition.
Recognition and two-branch acquisition need measurement before claiming savings.

All 1,085 tests, 21 focused tests and independent replay pass. Resume
`experiments/results/cnf-propagated-reuse/checkpoint.json`: 22,259 keys,
all 22,036 previous payloads, 597 new composed records, 1,230 earlier composed
records, 2,957 ordinary decisions and six projections. No alternate payloads.
All 483 prior sources / 5,222 artifacts / 90 manifests and the four frontier
lineages are preserved. Structural authorities remain unchanged. This is an
optional experiment route, with no new Lean or unrestricted-SAT theorem.


## 2026-11-17: retain unit prefixes after rejected discovery

[Retained-prefix fallback](trace-fallback.md) reuses a saved baseline trace while
solving the original target's residual normally; it does not acquire the rejected
guard. Twenty-seven exact-prefix arms preserve identical previous/new native
payloads, reducing visits 23,813 -> 20,896. On another 192 excluded queries, three
prefix reuses reduce visits 24,342 -> 22,811 (6.29%), with identical 269-row
additions. Three explicit publications replace three expansion calls. Sidecars
grow 0.077%; opposite timing signs establish no stable total gain. Native baseline
still uses only 14,126 visits, so rejected discovery remains expensive.

The next concrete gap is positive closure after a proposed condition. Case 146's
rejected child has 26 checked unit deductions and no remaining clauses, but the
gate tests only known children or unit conflict. The diagnostic verifies its
canonical child model; lift and check the original-target witness before direct
SAT publication, then measure costs. No alternate acquisition has been executed.
Cases 0/131 account for 31 of 43 remaining child expansions and need broader
structural investigation. None of four baseline residuals has a single-variable
immediate two-CNF decomposition; further propagation remains outside that test.

All 1,094 tests, 25 focused tests and independent replay pass. Resume
`experiments/results/cnf-trace-fallback/checkpoint.json`: 22,532 keys, all 22,259
previous payloads, 603 new composed records, 1,827 previous composed records,
2,957 ordinary decisions and six projections. No alternative payloads. Prior
488 sources / 5,329 artifacts / 91 manifests are unchanged. Ready/pending banks
are 132/38, 141/66, 85/91, 85/118; structural authority and 64 proof blocks are
preserved. No new Lean or unrestricted-SAT bound.


## 2026-11-17: recover full-target models from positive proposed children

[Positive-child recovery](positive-child.md) binds and checks the retained child
unit trace, restores the proposed assignment and validates every target clause
before direct SAT publication. It adds at most one target row after preparation,
without acquiring the negative premise or child node. Other choices and negative
proof obligations remain unchanged. The discovery work still includes the
failed-literal probe; no universal cheap-witness claim follows.

Thirty-nine exact-prefix arms reduce case 146 from six rows to one, native bytes
6,688 -> 1,798, and visits 3,304 -> 2,045 versus the preceding policy. The other
twelve controls preserve previous payloads. Another 192-query comparison has
zero activations: 190 targets are already known after preparation, and the two
remaining calls close through existing paths. All policies add identical 197
rows / 441,084 native bytes. Timing signs disagree. Broader evaluation now needs
new template families and explicit target-familiarity counts, retaining the
previous unresolved 0/131/159 and positive 36/146 controls.

All 1,102 tests, 26 focused tests and independent replay pass. Resume
`experiments/results/cnf-positive-child/checkpoint.json`: 22,729 keys, every
22,532 old payload preserved, 615 new composed records, 2,430 earlier composed
records, 2,957 ordinary decisions and six projections. No alternative payloads.
Prior 493 sources / 5,455 artifacts / 92 manifests are unchanged. Ready/pending
banks are 132/38, 141/66, 86/90 and 86/117. Structural authorities and 64 proof
blocks remain unchanged. No new Lean or unrestricted-SAT theorem.


## 2026-11-17: unfamiliar family transfer and futile premise probes

[Cross-family evaluation](cross-family.md) adds 48 unlabelled CNFs from four
finite generators and twelve same-template controls. All 48 fresh targets remain
unfamiliar after preparation; the twelve neighbours become known. Independent
truth tables enumerate 22,345,728 assignments across the 48 small formulas after
timing (1.409 seconds); this exponential validator is not a solver algorithm.
Both acquisition policies produce identical 398-row / 483,695-byte additions.
The optional policy performs 384 unsuccessful probes and raises propagation
65,842 -> 246,726 visits, mean query time 0.354 -> 0.482 seconds and complete
worker time 21.512 -> 21.963 seconds. Both timing pairs regress. All failed
screens and exact query prefixes are retained.

A posthoc necessary-condition audit identifies 192 futile probes / 73,488 visits:
after consistent baseline propagation, an unassigned variable without residual
binary-clause incidence cannot create another unit or empty clause, so a single
assumption cannot be unit-refuted. Implement and price this filter while reusing
the baseline trace. Original widths are insufficient; the documented unit-prefix
counterexample must remain a control. Random 3-CNF and coupled parity account
for 261/386 acquisition rows and 47,263/65,842 acquisition visits. Preserve cases
32/56/52 and 21 for broader decomposition; keep earlier useful/regressing guards.
Cold replay still dominates complete cost, so local probe savings have limited
end-to-end scope. This extends evaluation coverage, not structural authority.

All **1,106 tests**, 12 focused tests and independent reconstruction pass. The
new checkpoint is `experiments/results/cnf-cross-family/checkpoint.json`:
**23,127 native keys**, all 22,729 old payloads, **120 new composed records**,
3,045 previous composed records, 2,957 ordinary decisions and six projections.
There are no alternate native payloads. The union occupies 74,706,944 database
bytes / 5,364,377 compressed bytes. Ready/pending banks remain 132/38, 141/66,
86/90 and 86/117. All earlier 498 sources, 5,617 artifacts and 93 manifests
are unchanged. Structural authorities and all 64 manuscript proof blocks remain
unchanged. The 209-page manuscript builds without overfull or undefined warnings.


## 2026-11-17: skip binary-ineligible probes and retain positive discovery targets

[Residual binary filtering](binary-probe.md) now skips unassigned candidates with
no binary incidence after consistent baseline propagation. Original ranking,
candidate prefix and successful selections are preserved; skipped candidates do
not refill the budget. The saved trace records each omission. Independent
reconstruction checks all omitted screens and source bindings, and 2,048 small
formula/representation comparisons preserve every previous selection.

Twenty-six historical arms retain identical native/composed certificates, with
21 probes and 38,189 visits in either policy. Filtering adds incidence-scan
cost there. On 60 further excluded queries, 49 targets remain unfamiliar after
preparation. The filter removes 192/386 probes, cuts propagation 252,999 ->
179,463 (29.07%) and query/warm sidecars 15.13%, with identical 450-row / 521,286
native-byte additions. Query timing differences have opposite signs; complete
times regress 21.947 -> 22.234 seconds. Native baseline uses only 69,351 visits.
Cold replay remains dominant. No overall speedup is established.

The next discovery target is a useful result discarded by premise probing:
case 50's assumption -169 has an empty residual and an independently verified
whole-target model, but the policy selects only unit conflicts and then acquires
three native rows / 2,503 bytes. Implement and price positive-premise recovery
at this saved prefix. Eighty-nine conditioned residuals across twenty queries
are syntactically constant/Horn/dual-Horn/two-CNF; they still need checked
acquisition and recomposition. One refuted condition does not refute the parent.
As supporting work, signed incidence could exclude 83 remaining probes / 28,774
visits. Neither new route is implemented or timed. Keep negative-probe filters
scoped so useful positive witnesses are not silently excluded.

All **1,113 tests**, 24 focused tests and independent reconstruction pass.
Resume `experiments/results/cnf-binary-probe/checkpoint.json`: **23,577 native
keys**, all 23,127 earlier payloads, **206 new composed records**, 3,165 earlier
composed records, 2,957 ordinary decisions and six projections. No alternate
payloads are needed. The union occupies 75,649,024 database bytes / 5,474,412
compressed bytes. Ready/pending banks remain 132/38, 141/66, 86/90 and 86/117.
Prior 503 sources / 5,655 artifacts / 94 manifests, structural authorities and
all 64 manuscript proof blocks remain unchanged. The 211-page paper builds
without overfull or undefined warnings. No new Lean theorem or unrestricted-SAT
resource bound is claimed.


## 2026-11-17: checked positive-premise model recovery

[Positive-premise recovery](positive-premise.md) now lifts and checks complete
models from already saved unit screens of target-plus-assumption. It preserves
existing admitted choices and probes; a full target model, checked again by
native publication, replaces fresh fallback search. Saved case 50 shrinks
3 -> 1 acquired nodes / 2,503 -> 1,482 native bytes. Thirteen older controls
retain exact certificates. Fresh gated-Horn cases 26/54 also save two nodes
each; stream additions are 410/406 nodes and 472,534/469,867 native bytes for
previous/recovered policies. Neither broad taxonomy coverage nor an efficient
arbitrary-SAT reduction follows.

Mean query times are 0.4220/0.4018 seconds. Complete paired differences have
opposite signs, diagnostic sidecars grow about 0.36%, and process RSS is
essentially unchanged. Earlier discovery is still charged. Gated-Horn discovery
uses 73,886 propagation visits versus 5,751 acquisition visits. The next target
is checked solving and model transport for nonterminal conditioned Horn,
dual-Horn and two-CNF residuals, with exact negative-branch recomposition.
Positive discovery outside the binary filter and early positive stopping remain
open. All 1,120 tests pass; seven new tests include 2,048 small transported
clause-set comparisons, malformed traces, false residual hints and cold replay.


All **1,120 tests**, 31 focused tests, 135 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-positive-premise/checkpoint.json`:
**23,987 native keys**, preserving all 23,577 prior payloads, with 210 new
composed records alongside 3,371 inherited records, 2,957 ordinary decisions
and six projections. The union uses 76,537,856 database bytes / 5,571,577
compressed bytes. Three alternate model payloads remain in measured evidence
(six occurrences); preserved native payloads are never replaced. Ready/pending
banks remain 132/38, 141/66, 86/90 and 86/117. All 508 earlier source fingerprints,
5,780 artifacts and 95 manifests remain intact. The paper builds at 212 pages
with all 64 existing proof blocks unchanged. The initial replay validator's
scratch-directory failure and its separate corrected replay revision are retained.
No new Lean theorem, structural authority or unrestricted-SAT bound is claimed.


## 2026-11-18: uniform completion of conditioned residuals

[Uniform completion](uniform-premise.md) now uses checked saved unit traces to
recognize and transport all-false/all-true residual models before fallback.
It covers unit-closed Horn/dual-Horn and broader sign patterns. The two predicates
partition residuals into four cells, but the neither-completion cell still
encodes arbitrary SAT via unit closure and a fresh unequal-variable pair.
No unrestricted-SAT efficiency or complete easy partition is claimed.

Seventeen saved-prefix contexts preserve earlier controls; case 14 saves two
acquired nodes. Nine fresh gated-Horn cases save eighteen nodes, taking additions
452 -> 434 nodes / 535,908 -> 521,248 native bytes. All twelve gated targets now
use direct model publication. There are 96 failed graph-colouring checks.
Query-time differences have mixed signs; both complete-worker differences are
negative, with no general scaling inference. Diagnostic sidecars grow 2.83%.
All 1,129 tests pass, including nine new tests. Independent counter attribution
covers 138 records and a 256-formula embedding check.

Posthoc SCC diagnosis identifies four checked mixed models for fresh graph case
39 and sixteen checked negative conditions on fresh 43/51/55/59. Their timed
acquisition and negative parent recomposition remain open. These IDs refer to
this corpus. Gated-Horn discovery still uses 74,194 propagation visits despite
zero acquisition propagation: early positive stopping and canonical-form reuse
are the next direct computation targets. Preserve failed uniform attempts and
the SAT/UNSAT counterexamples to interpreting failure as refutation.


All **1,129 tests**, 23 focused tests, 138 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-uniform-premise/checkpoint.json`:
**24,444 native keys**, preserving all 23,987 prior payloads, with 216 new
composed records alongside 3,581 inherited records, 2,957 ordinary decisions
and six projections. The union uses 77,484,032 database bytes / 5,677,574
compressed bytes. Five alternate model payloads remain preserved (fourteen
occurrences). Ready/pending banks are 132/38, 141/66, **87/89** and **87/116**.
The two gains refer to one 568-byte negative certificate acquired by shared
ordinary preparation for neighbour case 1 in every mode: causal core 46 and
incremental-causal core 51. This activation is not a uniform-policy gain.
All 514 earlier sources, 5,918 artifacts and 96 manifests remain unchanged.
The paper builds at 212 pages with all 64 existing proof blocks unchanged;
structural authority and original coverage remain unchanged. No new Lean theorem
or unrestricted-SAT resource bound is claimed.

## 2026-11-18: inline completion closes redundant discovery suffixes

The new versioned selector `experiments/cnf_inline_completion.py` tests the
fresh residual during discovery and stops at a verified target model. It
avoids both later probes and late reconstruction of already computed bindings,
forced values and residuals. The ranking, cap and binary filter are unchanged;
negative guard and positive-child paths retain their certificate checks.
An independent selector reconstruction checks the exact stopped prefix, and
full raw-model verification prevents a bad propagation result from publishing
an invalid answer. Four alternative fresh witnesses are retained without
replacing historical payloads.

On sixty new queries, 84 probes and 62,116 propagation visits disappear; native
acquisition and coverage do not change. Diagnostic sidecars shrink 11.16%.
Query time improves in both orders, but complete workers worsen in both,
so end-to-end speedup remains unestablished. See [the detailed record](inline-completion.md).
Mixed two-CNF acquisition, negative parent recomposition, opportunities outside
the filter, and arbitrary-CNF resource guarantees remain open.

Resume `experiments/results/cnf-inline-completion/checkpoint.json`: 24,922 native
keys with all earlier payloads preserved. All 1,137 tests, 276 counter audits,
independent reconstruction and the 213-page manuscript build pass; the existing
64 proof blocks are unchanged. Posthoc mixed-model conditions on fresh graph
cases 15/27/39/51 now offer four concrete next acquisition controls.

## 2026-11-18: integrate mixed two-CNF models, retain negative evidence

The versioned selector `experiments/cnf_mixed_completion.py` reuses the current
residual for SCC solving after uniform completion fails. Full raw-source model
checks precede publication. An independent reachability checker validates SCC
status, source models and both negative implication paths. Native search is
never enabled inside selection. Negative conditions remain diagnostics and do
not silently become parent refutations.

Four saved controls reduce fourteen native nodes to four. Fresh acquisition
falls 385 -> 381 nodes, with two additional models; twelve failed SCC conditions
are charged and retained. Diagnostic sidecars grow 1.18%. Both timing orders
show query and complete-worker reductions, without a general scaling claim.
Next implement the combined certificate for a source clause whose literals all
have conditional refutations: fresh mixed-stream case 59 currently costs twelve
nodes. Preserve explicit misses without such an exhaustive cover.

Resume `experiments/results/cnf-mixed-completion/checkpoint.json`: 25,334 native
keys preserve all prior payloads. All 1,145 tests, 292 counter audits and full
independent replay pass; the 214-page manuscript retains all 64 existing proof
blocks. Fresh case 59 and saved controls 43/47 supply three exhaustive negative
clause covers whose present parent acquisitions total 36 nodes / 50,554 bytes.
Their combined publication and its cost remain open. No exact ordered SCC
residual repeats within a query on the fresh sample.

## 2026-11-18: compile exhaustive negative covers without rediscovery

The versioned cover compiler checks every retained premise trace and
contradictory implication path, then transports them into existing split,
unit, implication and empty nodes. Restricted cycles may need charged unit
repair. Native checking and full cold replay remain unchanged; existing
payloads are preserved. A width-w cover plans at most 3w-1 nodes, separately
from discovery, full keys, checking and persistence costs.

The three saved covers shrink 36 -> 24 nodes; one fresh cover takes total
acquisition 370 -> 364 nodes / 464,868 -> 457,715 bytes. Query timing remains
mixed and mean RSS rises despite smaller native payload. All earlier probe
work remains. See [the measured record](negative-cover.md).

The next concrete discovery target is **cover-directed candidate admission**.
Fresh cases 51, 55 and 59 each have a source clause missing just one refuted
literal, and that literal lies outside the current candidate set. Case 51
needs -158 for [-158, -54, 16]; case 55 needs -156 for [-156, -113, -12]
(or 191 for [-151, -56, 191]); case 59 needs -320 for [-320, -71, 52].
These are candidates for measurement, not already checked extra conditions.
Charge the added probes and retain failures; the missing condition need not
have a binary residual or a cheap proof. Earlier stopping at a completed cover
and covers exposed by baseline propagation are separate opportunities. A gated
K4 regression preserves the latter recognition miss.

All **1,153 tests**, 24 focused tests, 294 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-negative-cover/checkpoint.json`:
**25,757 native keys**, preserving all 25,334 earlier payloads, with 234 new
composed records alongside 4,245 inherited records, 2,957 ordinary decisions
and six projections. The preservation union uses 80,306,176 database bytes /
5,993,018 compressed bytes. Eight roots have alternate certificates in sixteen
retained evidence occurrences. Ready/pending banks remain 132/38, 141/66,
87/89 and 87/116; there are no new support activations. Original structural
coverage remains 17/24 and supplemental positive coverage 24/24. All 529 prior
sources, 6,431 artifacts and 99 manifests remain unchanged. The 215-page
manuscript builds with all 64 existing proof blocks unchanged. No new Lean
theorem or unrestricted-SAT resource guarantee is claimed.

## 2026-11-18: one extra probe completes retained partial covers

The optional versioned selector `experiments/cnf_cover_probe.py` retains the
old discovery record and adds at most one unattempted literal from a clause
with exactly one missing negative condition. Narrowest clause then source index
sets the priority. A negative binary residual feeds the existing cover compiler;
a positive model must satisfy the full raw premise. Unit-conflict and nonbinary
outcomes remain explicit misses. Old native routes and payloads remain intact.

Four saved contexts shrink 52 -> 32 native nodes. Four fresh added conditions
reduce acquisition 431 -> 407 nodes and propagation 104,544 -> 98,303 visits.
Query time improves in both orders; complete-worker time remains mixed and mean
RSS grows. The first overlapped timing pilot is excluded and preserved, with
all sixty pilot deltas equal to the clean comparison. See
[the complete measured record](cover-directed-probe.md).

Next: select and maintain partial covers during the original discovery pass.
For the chosen fresh clauses, eight later base probes could retrospectively
be avoided; this saving is not implemented or timed. Broader discovery still
needs a way to seed useful conditions outside the current partial-cover cell.

**Largest remaining measured acquisition cost:** coupled parity and random
three-CNF still add **308 native nodes / 52,385 acquisition propagation visits**,
unchanged across policies. Coupled parity alone adds 163 nodes / 25,354 visits;
random three-CNF adds 145 / 27,031. These dominate the remaining native work.
The existing pattern-discovery layer already extracts explicit affine equations
and preserves leftover clauses, whereas this native acquisition path currently
has uniform and binary leaves. The next broad-coverage investigation should
measure a source-checked bridge from that existing affine extraction to native
acquisition on unlabelled coupled inputs: record rank, free dimension and
leftover interaction before choosing a completion rule. Charge extraction,
projection, checking and any enumeration; a 2^d free-coordinate search is only
cheap when d is small, not uniformly polynomial for arbitrary CNF. Positive
models require full-source verification and negative results require their own
checked recomposition. This is a concrete integration target, not an already
measured improvement.

All **1,161 tests**, 24 focused tests, 300 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-cover-probe/checkpoint.json`:
**26,279 native keys**, preserving all 25,757 earlier payloads, with 240 new
composed records alongside 4,479 inherited records, 2,957 ordinary decisions
and six projections. The union uses 81,416,192 database bytes / 6,113,510
compressed bytes. Fourteen roots have alternate certificates in 27 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 534 earlier sources,
6,641 artifacts and 100 manifests remain unchanged. The 216-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem or
unrestricted-SAT resource guarantee is claimed.

## 2026-11-18: checked affine spaces now supply native positive models

The optional selector `experiments/cnf_affine_completion.py` runs after the
previous admitted routes, reusing exact parity extraction and complete-basis
checks. Its dimension cap includes every source variable. Packed leftover
clauses and a Gray walk avoid repeated clause packing and basis reconstruction.
Only a whole-target checked model reaches native publication; source guards
retain checked outer recomposition. Negative and budget-miss outcomes preserve
the prior fallback, with diagnostics retained.

Eight saved targets shrink 80 -> 8 nodes; nine fresh models reduce additions
395 -> 336 nodes and propagation 95,711 -> 83,024 visits. Query time improves
in both orders, complete timing is mixed, diagnostics grow and mean RSS falls.
See [the full measured record](affine-completion.md). Eight new tests include
512 exhaustive coordinate variants and 64 random affine mixtures.

Next publish the retained negative evidence with explicit checking and storage
costs. Fresh cases 29/41/57 still acquire 51 fallback nodes despite an inconsistent
row or completely exhausted small space. No small translation into existing
native proof kinds has been established; any checker extension must preserve
all older proofs. No-equation and large-dimension inputs remain open.

The fresh base discovery agrees on all 49 locally unfamiliar queries across
the two policies. Eleven neighbour queries become known after preparation;
neighbour case 4 remains unfamiliar behind two checked guards and adds ten
nodes in every policy. This is a shared control miss, not an affine regression.
Random three-CNF still adds 169 nodes / 28,452 acquisition propagation visits.
Fresh graph case 47 retains incomplete covers with two missing conditions per
candidate clause, beyond the one-extra-probe rule. These misses are preserved
alongside the negative affine publication target.

All **1,169 tests**, 24 focused tests, 324 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-affine-completion/checkpoint.json`:
**26,743 native keys**, preserving all 26,279 prior payloads, with 264 new
composed records alongside 4,719 inherited records, 2,957 ordinary decisions
and six projections. The union uses 82,378,752 database bytes / 6,217,639
compressed bytes. Twenty-six roots have alternate certificates in 67 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 539 prior sources,
6,871 artifacts and 101 manifests remain unchanged. The 217-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem,
native proof kind or unrestricted-SAT resource guarantee is claimed.


## 2026-11-18: Versioned negative affine publication

See [negative affine publication](affine-negative-publication.md). An optional
source-bound certificate now checks either a contradictory Gaussian row or every
point of a complete affine space with at most eight free coordinates. Each
point has a falsified leftover-clause witness. Direct Gray-coordinate checking
is independent of the discovery walk. The versioned extension table and guarded
chain reader leave native search and all old native payloads unchanged.

Seven selected negative prefixes replace 134 native nodes / 175,449 bytes with
seven certificates / 21,561 bytes, avoiding 20,949 propagation visits. Six
controls retain 47 native nodes. Across all thirteen cases and two opposite
orders, combined new payload falls 229,996 -> 76,108 bytes; summed query time
falls 0.13998 -> 0.05627 seconds, with both complete-arm deltas negative. This is
a retrospective mechanism pilot, not a fresh-stream coverage estimate. Full
historical replay is separate from per-arm timing; peak RSS was not measured.

All 26,743 prior native payloads remain. The extended archive adds 45,056 SQLite
bytes / 4,627 compressed bytes and preserves native alternatives. Its seven
cold extension-chain checks also read 134 native nodes because the current view
prefers native alternatives. Automatic discovery/checkpoint adoption, certificate
choice, a newly excluded stream and complete projection onto leftover variables
remain open. No-equation targets and large free dimension retain fallback.
The checkpoint explicitly identifies its extension reader; the previous ordinary
production checkpoint remains valid. No new Lean theorem or unrestricted-SAT
resource bound is claimed.


## 2026-11-18: resumable affine negatives on fresh inputs

[The new session](affine-session-reuse.md) checks exact-target negative lookup
before local discovery and persists new versioned refutations. Versioned chain
replay uses its checked extension terminal directly; native search cannot read
extension proofs. Guarded conclusions are indexed in a checked source-bound bank.

A newly excluded sixty-query stream returns 37 SAT / 23 UNSAT in both policies.
Three negatives replace 67 native nodes with three certificates; nine coupled
models remain. Combined additions fall 344 -> 280 certificates and payload
460,091 -> 384,362 bytes. Query time falls 7.76%, complete time only 0.45% on
average, with both orders improving. Sixty lookup misses cost about 0.00579
seconds; there are no fresh extension hits. All discovery traces/counters match.
Full historical replay remains about thirteen seconds. Trial storage and RSS
fall, but the preservation union adds 344 native keys and three extensions
because comparator proofs remain available: 888,832 SQLite / 95,921 compressed
bytes of growth, to 27,087 native keys and ten extension certificates.

Independent validation checks 240 chronological queries, six new-negative
publication-counter records, exhaustive truth for 48 family cases, warm answers
and full historical cold replay. The extension phase loads no native alternative
proofs. Largest remaining acquisition: random three-CNF, 140 expanded nodes /
27,761 propagation visits (start with case 56). Graph discovery pays 25,375
visits and has unresolved cases 47/35. Hidden/no-equation structures, large free
dimension, exact projection and extension-aware internal support remain open.
No unrestricted-SAT resource guarantee follows from these finite measurements.


## 2026-11-18: binary-subset refutation during native expansion

[The optional native rule](binary-subset-refutation.md) checks a mixed residual's
binary clauses for contradictory implication paths. Original source indices let
the unchanged checker validate the result. A satisfiable binary core is
inconclusive. Unit, pure-binary and uniform-core filters avoid redundant SCCs.

On sixty new queries, eight refutation leaves remove 22 native nodes / 16,393
payload bytes across random three-CNF and graph colouring. Discovery is unchanged.
The policy pays 76 failed SCCs; paired query timings have mixed signs and mean
complete-worker time rises 0.82%. This is a deterministic search/storage reduction,
with no established runtime dominance. The checkpoint preserves 27,087 old native
payloads and ten extensions, reaching 27,368 / thirteen. Alternative native
proofs remain in the trial archives; the union preserves first payloads.

The next cases are new random-three 56/44 (5,159/5,117 propagation visits), whose
remaining interaction is not refuted by their binary cores. Repeated binary
graphs, wide-clause compatibility, failed-recognition overhead and earlier graph
cover admission remain open. Full historical replay still costs about 13.5 s.
All 240 chronological queries, twelve publication-counter records, 48 exhaustive
family truths and full historical replay validate. This supplies no new Lean
or unrestricted-SAT resource guarantee.


## 2026-11-18: cover wider clauses through a satisfiable binary core

[The bounded cover rule](binary-clause-cover.md) shares implication reachability
between source-clause literals and checks that the core forces every literal
false. Retained paths, source clauses and native split/unit proofs preserve
exactness; the final pair reuses a contradiction cycle without new SCC work.
The earlier compiler with larger proof spines remains a rejected diagnostic.

On sixty new queries, three covers in two random-three-CNF cases replace eight
search expansions with six compiled children: native additions **226 -> 224**,
payload **293,179 -> 291,005 bytes**. Query and complete-worker means improve
1.27% / 0.40%, with both orders improving; peak RSS rises about 9.53 MB. All prior
discovery evidence matches. The policy stays optional. The union preserves every
old payload and reaches 27,600 native keys / eighteen extensions.

Next investigate partial binary backbones in new cases 32/40/52, rather than
requiring a whole covered clause. Check whether a forced literal avoids a costly
branch after charging recognition, proof children and persistence. Graph discovery
and historical replay remain larger costs. All 240 chronological queries, twenty
affine-publication counter records, 48 family truth tables and full cold history
validate. No new Lean or unrestricted-SAT resource bound follows.


## 2026-11-18: partial backbones with direct excluded-branch proofs

[The new optional policies](binary-backbone-reuse.md) reuse successful implication
paths from otherwise unresolved clause-cover searches. A surviving SAT cofactor
lifts a model; an UNSAT cofactor combines with a directly transported unit proof
of the excluded branch. The original native checker validates both outcomes.

On sixty fresh queries, first adds five native nodes despite less propagation.
The frequency gate saves two nodes / 1,767 bytes and improves query time 3.04%,
with both orders improving. Complete-worker timing stays mixed and its mean rises
0.02%. All earlier discovery evidence matches. The three-policy union preserves
all old payloads and reaches 27,888 native keys / twenty-two extensions.

The next target is selective recognition: six stored ordinary split nodes have
forced split variables omitted by cover-oriented candidate selection. Test a
bounded targeted implication query with full cost accounting. Seventy-five mixed
binary cores in the stored-node census have no forced literals; this method alone
cannot resolve them. Validation covers 360 chronological queries, 24 publication
counter records, 48 family truths and full historical replay. No new Lean or
unrestricted-SAT resource guarantee is claimed.


## 2026-11-18: targeted split-variable implication discovery

[The targeted policy](targeted-backbone-discovery.md) adds at most one implication
root after the unchanged whole-cover budget, with completed searches reused.
It recognizes all fourteen saved forced-variable misses, including six split
nodes. On sixty new queries, native additions fall 252 -> 250 and propagation
visits 29,008 -> 27,154, with twelve selected backbones instead of two. Fifty-six
new root searches, ranking, checking and five excluded children remain charged.
Timing varies substantially in unchanged preparation and cold replay; there is
no established end-to-end speedup. The policy remains optional.

The new diagnostic has twenty binary-equivalence sources with no forced literal,
including eleven ordinary split nodes. Exact full-source substitution with native
certificates is the next coverage target, reusing earlier probe-equivalence logic
where justified. The saved random-three case 56 is among them; it still pays
4,866 propagation visits. This is a measured discovery opportunity, not yet an
implemented speedup. No uniformly efficient arbitrary-CNF expansion follows.

All 1,212 tests, 43 focused tests, 240 chronological query audits, sixteen
publication counter audits, 48 family truth tables and full cold replay pass.
The new checkpoint preserves all old payloads and reaches 28,145 native keys /
twenty-six extensions. Previous defaults and proof formats remain unchanged.


## 2026-11-18: binary equivalence acquisition and its cost regression

[The quotient pilot](binary-equivalence-acquisition.md) implements full-source
substitution, checked signed model lifts and explicit negative dependencies.
Two shared implication trees use `2(k-1)` edges for a `k`-literal block. Old native
proof formats and recursive search remain unchanged; this top-level API requires
an explicit extension reader and is not yet in the prepared production pipeline.

On 68 reconstruction/edit/control inputs, propagation falls 16.57%, but combined
certificates grow 420 -> 440 and payload 525,136 -> 534,611 bytes. Complete time
regresses in both orders. All selected blocks merge one variable. The regression
is retained, and the policy remains optional. The next strongest compression
target is the 41,208 bytes of duplicated source/child formula fields in the new
negative payloads; reconstructing them from exact keys and checked substitution
must be measured. Twenty-two binary cores repeat, and twelve inputs have an
unused second equivalence block. Neither is yet a measured saving.

All 1,220 tests, 51 focused tests, 272 chronological audits, 68 exhaustive truth
tables and full historical/new replay pass. The checkpoint preserves prior results
and reaches 28,691 native keys, twenty-six affine and forty-two explicit equivalence
records. Native recursive integration, prepared admission, compact arbitrary
interaction and uniformly efficient expansion remain open.


## 2026-11-18: compact equivalence records with exact reconstruction

[Version-two certificates](compact-equivalence-certificates.md) omit duplicated
source/child formulas. The full canonical source key and checked substitution
reconstruct both identities before requiring the native UNSAT child. Old records
remain byte-identical and readable; native search never consults the extensions.

The same 68-input, empty-archive comparison retains identical native acquisitions
and source results. Equivalence storage falls 68,878 -> 26,998 bytes, combined
payload to 492,731 bytes: 6.17% below the native control. The certificate count
remains higher, and paired complete timing is mixed. Query time is still 3.93%
above the control. Keep the API optional; no new structural coverage is claimed.

The next target is reuse of 22 repeated binary cores among 56 eligible queries,
with binary-local indices, checked full-source transport, edit invalidation and
charged cache/cold costs. Multiple blocks and production integration remain open.
All 1,228 tests, 59 focused tests, 408 chronological audits, 68 exhaustive truths
and full old/new replay pass. The union preserves 28,691 native, twenty-six affine
and forty-two v1 records, adding forty-two v2 alternatives without replacing them.

## 2026-11-18: exact binary-core discovery reuse

[Binary-core discovery reuse](binary-core-discovery-reuse.md) implements the 22
repeated-core opportunities on the unchanged 68-input pilot. Binary-local trees
are translated to current source indices and checked before substitution; binary
or coordinate edits miss the exact key. Null discovery outcomes are never SAT
answers. Native and compact proof payloads match byte-for-byte.

Acquisition graph/SCC work falls **44.53%**: constructed edges 4,276 -> 2,372 and
SCC visits 8,552 -> 4,744. The 34 entries use **11,906 serialized / 25,887 Python
object bytes**. Persistent mode adds 36,864 SQLite / 3,618 trial gzip bytes and
recomputes every entry at cold validation. Acquisition plus cold discovery thus
rises **10.94%** above the uncached control. Memory-mode complete timings have
mixed signs; persistent total gains are only 0.00091 / 0.00254 seconds with mixed
query timing. Keep both modes optional; this is no established production speedup.

**Next:** multi-block substitution on the twelve diagnosed sources with a second
disjoint block. Child solving still costs 51,326 propagation visits / 358 expansions.
Price proof size and child acquisition before claiming broader gains. Sharing the
other recognizers' graph construction remains a separate target: 8,344 subset
edges, 6,772 cover edges and 171 subset SCC calls are unchanged.

Resume `experiments/results/cnf-binary-core-cache/checkpoint.json`: all **28,691
native / 26 affine / 42 v1 / 42 v2** records unchanged, plus 34 discovery entries.
Old/new histories, 408 chronological queries and 68 exhaustive truths validate.
All 591 prior sources / 7,683 artifacts / 110 manifests are preserved. No new
coverage, Lean theorem or unrestricted-SAT resource bound follows.

All **1,236 full / 67 focused tests** pass, with 44 pre-existing SQLite warnings
in the full suite and none in the focused suite. The **223-page manuscript**
builds cleanly and all **64 previous proof blocks** are unchanged. Final source
ledger: **596**. New manifest: **39 artifacts**. Next preservation audit:
**7,722 artifacts / 111 manifests**.

## 2026-11-18: simultaneous blocks expose quotient-choice cost

[Multiple-block equivalence](multiblock-equivalence.md) checks disjoint supports,
unions signed maps and substitutes every source clause once. Single-block
negatives retain v2; multiple-block negatives use compact v3 with native negative
dependencies. Twelve pilot inputs now use two blocks. All cached/uncached
all-block acquisitions match, and old formats remain readable.

On the unchanged 68-source pilot, applied merges rise **45 -> 57** and propagation
falls **51,326 -> 51,059 (0.52%)**. But native expansions rise **358 -> 366**, native
certificates **398 -> 408**, and combined payload **492,731 -> 496,214 bytes**.
SQLite grows 4,096 / gzip 2,114 bytes. Query time falls in both orders; complete
cached deltas **-0.03893 / +0.00438 seconds** remain mixed. Keep this optional and
retain the measured storage regression; more substitution is not less acquisition.

**Next highest-value target: choose an already known quotient.** At actual query
prefixes 7 and 34, both streams already contain the one-block quotient while the
all-block quotient is new. Ignoring it costs five and three extra native records;
two other later queries add one record each after their history changes. Compare
the exact one/all quotient keys before fresh solving, with checked recomposition
and charged second-quotient construction, lookup, verification and storage. The
diagnosis is not an implemented saving or a search for the globally optimal subset.

Resume `experiments/results/cnf-multiblock-equivalence/checkpoint.json`: all
**28,691 native / 26 affine / 42 v1 / 42 v2 / 34 discovery records** preserved;
45 new native keys and eleven v3 records added. Native union: **28,736**.
Union growth is 81,920 SQLite / 6,918 compressed bytes. Old/new histories, 408
chronological queries and 68 source truths validate, with both quotient truths
checked on the twelve affected sources. All 596 prior sources / 7,722 artifacts /
111 manifests remain unchanged. No new Lean or unrestricted-SAT bound follows.

The **224-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,245 full / 76 focused tests** pass (44 pre-existing SQLite
warnings in the full suite, none in focused tests). Final executable source
ledger: **601**. New manifest: **39 artifacts**. Next preservation audit:
**7,761 artifacts / 112 manifests**.

## 2026-11-18: checked known-quotient choice and normalization cost

[Known-quotient selection](known-quotient-selection.md) checks the complete native
target, then the first-block target only on a miss, before fresh acquisition.
Correct canonical-name transport and the selected source evidence retain existing
SAT models and v2/v3 proof authorities. At most two alternatives are considered.

The 68-query pilot plus 36 excluded fresh sources recover **eight native nodes**
versus all-block acquisition (560 -> 552), saving **3,406 payload / 28,672 SQLite /
2,938 gzip bytes**. All eight native savings occur on the original pilot; the fresh
segment has the same 152 native additions under every policy. Four first-target
hits include SAT and UNSAT. Thirty-eight lookups and fourteen extra transforms
are charged. Mean complete time rises 1.00% versus all blocks, with mixed paired
deltas, and 2.47% versus single block. Keep the policy optional.

**Next highest-value structural reuse target: per-query normalization results.**
A separate identical-output solve profile places normalization and individual
SQLite commits ahead of propagation in elapsed cost. An exact census finds 505
repeats among 1,715 normalization calls; 469 repeats occur within one query and
cover 96.39% of repeated input literals. Peak per-query encoded input/result state
is 73,860 bytes versus 1,448,226 for the full stream. Test a bounded immutable cache
of the CNF/name-map/key triple; charge validation, copying, hashing, lookup,
objects and eviction. Reject booleans/floats before hits. These are opportunities,
not implemented savings. Transaction batching remains a separate durability task.

Resume `experiments/results/cnf-known-quotient/checkpoint.json`: all prior **28,736
native / 26 affine / 42 v1 / 42 v2 / 11 v3 / 34 discovery records** preserved; union
now **28,886 native / 53 v2 / 22 v3**. Full histories, 624 chronological queries,
104 truths, 36 fresh exclusions and both orders of all known choices validate.
The failed benchmark dispatch and profile-comparison setups are retained. All
601 previous sources / 7,761 artifacts / 112 manifests are unchanged. No new
Lean or unrestricted-SAT resource bound follows.

The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,253 full / 84 focused tests** pass. Final executable source
ledger: **607**. New manifest: **46 artifacts**, including the retained failed
setups and posthoc profile. Next preservation audit:
**7,807 artifacts / 113 manifests**.


## 2026-11-18 checkpoint: avoid rediscovering already validated canonical results

[Bounded query-local normalization reuse](query-canonicalization-reuse.md) now
implements the previous repeat opportunity with exact CNF/name-map/key triples,
strict pre-lookup literal validation, conservative object charging, FIFO eviction
and unconditional query-end clearing. Both 128 KiB and 8 KiB arms preserve all
answers, models, quotient choices, ordinary acquisition counters and certificates.

On the same 104 replayed inputs, 128 KiB saves **19.57% of normalization visits /
19.55% of serialized key bytes**, with **368 hits / 470 evictions** and a peak
**131,018 charged bytes / 20 entries**. Yet mean complete time rises **3.65%**,
with positive deltas in both orders. At 8 KiB it rises **8.44%**, with only fourteen
hits and 1,295 oversized skips. Every lookup adds validation/copying/hash work.
Warm streams have zero cache hits and regress. Keep the optional experiment and
its negative result; no production/default change or storage saving is claimed.

**Next highest-value target: reuse validated canonical results directly along
native verification and child visitation.** The separate control profile assigns
552 calls / 0.08700 inclusive seconds to `_verify`, and 546 / 0.08263 seconds to
`_visit`. The cache increases both costs. Investigate passing exact immutable
triples between appropriate callers or cheaper explicit canonical-form recognition,
while preserving external-input validation and all proof checks. Charge warm-path
cost and identity transport; increasing the general cache size is not the next
default step. The 605 individual SQLite commits remain a separate durability task.

Resume `experiments/results/cnf-query-canonical-cache/checkpoint.json`. Its parent
archive is referenced unchanged: **28,886 native / 26 affine / 42 v1 / 53 v2 /
22 v3 / 34 discovery records**, all 5,650 composed and 444 pilot decisions.
Validation covers 832 chronological queries, 416 exact cache/control comparisons,
104 exhaustive truths, 144 choice checks and 84 known hits. All **607 prior sources /
7,807 artifacts / 113 manifests** remain unchanged. Two validator setup errors are
preserved; timing workers and solver results were unaffected. All **1,262 full /
93 focused tests** pass, with 44 pre-existing SQLite warnings in the full suite and
none in focused tests. No new coverage, Lean theorem or unrestricted SAT bound.

The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. Final executable source ledger: **613**. The new manifest binds **52
artifacts**. Next preservation audit: **7,859 artifacts / 114 manifests**.

## 2026-11-18 checkpoint: batch verified publication without losing durable results

[Direct canonical verification](direct-canonical-verification.md) now recognizes
stored normalizer fixed points without sorting/renaming, then passes the checked
immutable CNF/name-map/key triple once to the original verifier. Every key, SAT
model, negative proof rule and child dependency remains checked. Acquisition and
cold replay share this optional recognizer; no canonical cache is retained.

On the same 104-source stream, **552 normalization calls / 55,601 literal visits**
are replaced by explicit canonical-form checks. Normalization-only visits fall
**31.75%**; total input validation is not removed. Mean query time falls **5.79%**,
cold replay **18.12%**, and complete time **6.63%**. Both paired query/cold/complete
deltas improve; warm deltas remain mixed. All answers, models, quotient choices,
ordinary proof/acquisition counters, 552 native / 53 extension payloads and
1,179,648 SQLite bytes remain identical. No general speedup or new coverage claim.

**Next highest-value target: bounded publication transactions.** The posthoc
identical-output profile leaves **605 SQLite transaction exits / 0.12607 exclusive
seconds**, now the largest exclusive site, plus 1,591 SQL executions. A separate
census finds only **45 visitation opportunities / 8,011 literal units** that equal
an earlier normalized output in the same query; direct transport remains a smaller
secondary target. Test batching with explicit dependency-closure durability,
partial-query visibility, memory limits, rollback/invalidation and injected
failures. Preserve committed history and commit a returned answer's dependencies
before success. This is a next design investigation, not an implemented saving.

Resume `experiments/results/cnf-canonical-verify/checkpoint.json`. Parent archive
and all decisions are referenced unchanged: **28,886 native / 26 affine / 42 v1 /
53 v2 / 22 v3 / 34 discovery records**, all **5,650 composed / 444 pilot decisions**.
Both readers validate every native record; all 28,886 formulas match the original
normalizer, and 4,961 representation mutations match its acceptance criterion.
The audit also covers 624 chronological queries, 416 exact alternative/control
comparisons, 104 exhaustive truths, 144 choices and 84 known hits. All **613 prior
sources / 7,859 artifacts / 114 manifests** remain unchanged. A test-generator
setup error is preserved. All **1,271 full / 102 focused tests** pass, with 43
SQLite warnings at pre-existing sites in the full suite and none in focused tests. The
**226-page manuscript** builds cleanly with all **64 prior proof blocks** unchanged.
No production-default change, new Lean theorem or unrestricted SAT bound follows.

Final executable source ledger: **619**. The new manifest binds **45 artifacts**;
next preservation audit: **7,904 artifacts / 115 manifests**.

## 2026-11-18 checkpoint: reuse repeated residual construction and normalization

[Bounded publication batches](bounded-publication-batches.md) group the unchanged
verified INSERT stream, flushing before a successful answer. Failed queries roll
back the pending suffix and evict its checked aliases; committed prefixes remain.
Uncertain rollback poisons the instance until reopening. Exclusive ownership is
required. The optional policy changes partial-query visibility, with no proof
format or journal/synchronous-setting change.

On the same 104 sources, **605 commits fall to 104**. Mean query time falls
**35.55%** versus direct verification and **36.30%** versus a one-record adapter,
with gains in both orders. Observed complete reductions are 26.87% / 24.24%, but
an unusually slow first control cold sample must not be attributed to batching.
Every non-batch counter, answer, model, certificate and storage byte count matches.
The timed 32-record / 256-KiB policy peaks at **27 records / 39,747 payload bytes /
17,086 charged pending-key object bytes**; neither limit is reached here. Separate
tests exercise cuts and oversized records. Journal sampling rises **49,760 ->
103,112 bytes**; process RSS also rises. These limits do not cap SQLite journals,
whole-solver RAM or lock duration. Completed results remain durable; unfinished
batches may be lost on failure.

**Next highest-value target: repeated residual construction and canonicalization
across acquisition and proof checking.** The posthoc profile leaves **1,163
normalizer calls / 0.07401 exclusive / 0.18230 inclusive seconds** as the largest
exclusive site,
while 104 commits take 0.03340 seconds. Restriction still costs 780 calls / 0.06973
inclusive seconds. Count exact raw repeats, including noncompact name maps, at
those call sites before selecting transport/reuse. Keep source/conditioning
identity, variable maps, full keys and independent proof checks bound. The earlier
already-normalized-output census found only 45 visitation opportunities; do not
claim additional savings yet or reinstate the regressing general cache.

Resume `experiments/results/cnf-publication-batches/checkpoint.json`. The parent
archive and decisions are referenced unchanged: **28,886 native / 26 affine /
42 v1 / 53 v2 / 22 v3 / 34 discovery records**, all **5,650 composed / 444 pilot
results**. Validation covers 624 chronological queries, 416 alternative/control
comparisons, 104 exhaustive truths, 144 choices and 84 known hits. An independent
replay certifies every externally visible archive after **104 batch commits**.
Full old histories/readers and all 28,886 canonical fixed points remain valid.
All **619 prior sources / 7,904 artifacts / 115 manifests** remain unchanged.
All **1,283 full / 114 focused tests** pass, including process-exit recovery and
rollback tests; 43 pre-existing-site SQLite warnings remain in the full suite,
none in focused tests. The **227-page manuscript** builds with all **64 prior
proof blocks** unchanged. No new structural coverage, Lean theorem or unrestricted
SAT resource bound follows.

Final executable source ledger: **625**. The new manifest binds **43 artifacts**;
next preservation audit: **7,947 artifacts / 116 manifests**.

## 2026-11-18: targeted acquisition-to-proof normalization reuse

[Targeted proof-normalization reuse](proof-normalization-reuse.md) now retains
`_visit` results only for `_negative_child` checks. Exact raw inputs bind the
immutable CNF, name map and key; the original child-key and checked-UNSAT tests
still run. Invalid equal-hash literals are rejected before lookup. Query-local
FIFO state clears on success/failure and adds no persisted proof authority.

On the same 104 inputs, the 128-KiB cap avoids **262 of 311** negative-child
normalizations, reducing normalization visits **21.31%**. Mean query time improves
**3.88%**, with both orders improving, but mean complete time improves only 2.07%
and its second paired delta **regresses 1.86 ms**. The 32-KiB arm also regresses
in its second query measurement. Keep this optional; there is no robust general
speedup claim. All decisions, proofs, expansions, publication counters and final
storage remain identical. Peak retained charge is **131,020 bytes / 13 entries**;
an independent graph walk measures 83,489 bytes. The cap excludes transients,
allocator overhead and full-solver memory. Persistent storage does not shrink.

**Next highest-value target: preserve local clause order during residual
normalization.** The census finds **501/546 producer inputs / 47,894 literal units**
with sorted, distinct, tautology-free literals. Restrictions preserve that local
property, but not global clause order, duplicates or compact names. Prove and
check those boundaries before bypassing any sorting or renaming. Memo128 still
spends 901 normalization calls / **0.14642 inclusive profiled seconds**, compared
with 780 restrictions / 0.07031 seconds. Its admission sizing alone costs
0.02845 seconds; shorter-lived direct transport is the second candidate. Profile
times overlap and are separate from matched wall times. No new pattern coverage
or unrestricted SAT bound follows from this supporting optimization.

Resume `experiments/results/cnf-proof-normalization-reuse/checkpoint.json`.
The parent union and **5,650 composed / 444 pilot results** remain unchanged.
Validation covers **624 queries / 416 exact comparisons / 104 truths / 104 visible
committed prefixes**, both old readers, all **28,886 fixed points / 4,961 mutations**.
All **625 prior sources / 7,947 artifacts / 116 manifests** are preserved. Nine
new tests cover proof authority, name maps, invalid literals, capacity and failure
cleanup. All **1,292 full / 123 focused tests** pass. The full suite emits 44 SQLite
ResourceWarnings versus 43 in the parent, at unchanged source/stdlib files;
focused tests emit none. The **227-page manuscript / 64 prior proof blocks**
remain valid. Final source ledger: **632**; details are in `checks.json`.

## 2026-11-18: exact normalization from local clause order

[Ordered residual normalization](ordered-residual-normalization.md) checks local
literal order and uses a two-pointer tautology test; unordered/duplicate-literal
clauses keep the original fallback. Signed compact renaming preserves order, so
the mapped clause needs no second sort. Global deduplication/sorting, support,
name maps, exact keys and every proof check remain unchanged. Empty clauses do
not bypass validation of the remaining input. This exact transformation applies
to valid CNFs generally but adds no tractable SAT category.

On the same 104 sources, the optional path avoids **96,099 sort calls**. Mean query
time falls **2.17%** and complete time **1.68%** against batching, with both orders
improving. It is still **1.19% slower than the 128-KiB memo** on query time, and
warm time **regresses 2.95%**. It adds no retained normalization cache, but measured
RSS does not fall. Answers, models, all ordinary counters, proofs and persistent
storage match batching exactly. Keep both alternatives optional; do not promote
small measured gains into a general runtime claim.

**Next highest-value gap: representative cost and discovery evidence on a larger
held-out mixture stream.** Ordered normalization remains the largest exclusive
site here (1,163 calls / 0.07034 exclusive / 0.14104 inclusive profiled seconds);
restriction costs 780 calls / 0.06935 inclusive seconds. After several optimizations
on the same 104 small sources, another local reduction needs stronger evidence.
Freeze larger novel/mixed/edited CNFs and deterministic budgets, measure
recognition outcomes and unresolved interactions alongside acquisition, runtime
and retained proof state, then choose the dominant bottleneck. Compare the three
preserved variants. Direct invariant transport and combining ordering with reuse
are candidates only; broader structure discovery remains the main objective.

Resume `experiments/results/cnf-ordered-normalization/checkpoint.json`.
All **632 prior sources / 7,990 artifacts / 117 manifests** and the full proof/decision
union remain unchanged. Validation covers **624 chronological queries / 416 exact
comparisons / 104 truths / 104 committed prefixes**, both old readers, and ordered
normalization agreement on **28,886 archived CNFs / 4,961 mutations**. Eight new
tests add exhaustive small clauses/formulas, adversarial inputs, failure recovery
and full-key/model/proof comparisons. All **1,300 full / 131 focused tests** pass. The full suite retains 44 SQLite
ResourceWarnings at unchanged files; focused tests emit none. The **228-page
manuscript** builds without warnings and preserves **64 earlier proof blocks**.
Final source ledger: **638**; build and suite details are in `checks.json`.

## 2026-11-19: larger mixtures and checked witness recovery

[The larger-mixture study](larger-mixture-expansion-costs.md) freezes **108 queries /
72 new canonical roots**, with scales 24/48/72, six designs, edits and exact-root
repeats. Plain batching now wins mean query time: the memo regresses **1.49%** and
ordered normalization **1.09%**, in both orders. Keep all timings and alternatives;
the earlier small-catalog improvements did not generalize to this designed stream.

All variants initially return **70 SAT / 36 UNSAT / 2 unresolved attempts** under
256 native expansions per attempt. Budget stops are not UNSAT. Both preserve
256 committed records, rolling back 20/13 pending records. A later repeat solves
one stopped base using the accumulated archive. **Random 3-CNF consumes 58.48% of
query time**, parity mixtures 21.54%. Edits need **1,013 expansions / 1,055 records**,
nearly matching bases' 1,041 / 1,086. New acquisition across edits is the main
reuse gap. Normalization remains the largest profiled exclusive routine; avoiding
whole acquisitions can avoid its work together with restriction and propagation.

The timed archive grows to **2,259 records / 12.13 MB encoded payload / 22.85 MB
SQLite**, with **53.93 MB** in checked Python cache objects. Cohort measurements
are cumulative observations, not asymptotic bounds. Worker RSS includes benchmark
metadata and cold replay. The separate bounded inventory closes only **18/108**
family decompositions, despite 106 completed decisions. Every root has the same
coarse syntax vector; unresolved interactions remain explicit. Its 624 checked
nodes and 108 source bindings are persisted separately.

**Concrete recovery:** a fully checked later donor model also satisfies the one
root still unresolved at stream end. The new optional helper validates the full
target and publishes **one SAT certificate / 7,895 payload bytes / zero expansions**.
Both readers now certify **48 SAT / 24 UNSAT distinct roots**. This post-timing
recovery preserves both original budget-stop observations; candidate selection
was supplied, so it is not yet a general retrieval algorithm or complexity result.

**Next highest-value implementation target: bounded, label-free candidate retrieval
for SAT witnesses**, with complete checks, misses and persistence charged. A
posthoc check finds **21/23 available parent models** also satisfy their edits;
those edits incurred 225 expansions, but their work is not an additive guaranteed
saving. The hardest remaining mechanism is partial negative-search reuse across
clause edits; witness reuse does not solve UNSAT cases. Preserve a fresh evaluation
split before tuning on this now-exposed stream. Compact proof state and better
recognition of mixed/shared interactions remain open.

Resume `experiments/results/cnf-larger-mixtures/checkpoint.json`. All **638 prior
sources / 8,032 artifacts / 118 manifests** are unchanged. The union now contains
**31,141 native** records, with all old affine/equivalence/discovery records and
**5,650 composed / 444 pilot decisions** intact. The failed inventory audit's
incomplete expected configuration is preserved and corrected. All **1,311 full / 142 focused tests** pass; 44 existing-site SQLite warnings
remain in the full suite, none in focused tests. The **228-page manuscript**
builds without warnings with **64 prior proof blocks** unchanged. Final source
ledger: **647**; details are in `checks.json`.


## 2026-11-19: bounded automatic witness retrieval

The [new study](bounded-witness-pool.md) removes supplied donor relationships from
SAT model reuse. A 64-vector pool tries at most four same-count compact-rank
assignments, validates the entire target, and publishes through the original
native witness verifier. Misses never certify UNSAT. This applies as a proposal
mechanism across categories; it adds no semantic family closure.

Eight serial workers on exposed and separately frozen size-holdout streams show
2.97% / 8.27% lower mean query time and 4.36% / 9.06% lower complete worker time.
Holdout edit expansions fall 1,342 to 955; native records fall 3,292 to 2,873.
Two capped attempts remain in each arm/split. Parity receives zero hits and incurs
extra probe work. Cold seeding from a 64-row tail yields zero exposed candidates
and 33 holdout candidates, exposing the need for selective durable retention.

Both old readers verify all proof records. The append-only union now has 34,426
native records, retaining earlier authoritative bytes when another trial yields
a different valid witness. All prior sources/artifacts and earlier composed,
pilot, larger-stream and inventory observations are preserved. Validation covers
864 chronological attempts, 512 exhaustive two-variable formulas, 1,319 full and
150 focused tests. The 229-page manuscript builds with all 64 proof blocks
unchanged. Forty-four existing-site SQLite warnings remain in the full suite.
The first audit used an incorrect nested key for the preceding recovery result;
its source/log are preserved, and the corrected audit passes.

Resume `experiments/results/cnf-witness-pool/checkpoint.json`. Priorities are
negative proof dependencies across edits, a bounded durable SAT candidate index,
and cheaper failed-probe selection. Candidate caps bound proposals only;
residual count, cumulative proof size and arbitrary-SAT expansion remain unbounded
by a polynomial guarantee. The fresh split shares the same six synthetic designs,
so external representative workloads remain necessary.


## 2026-11-19: on-demand negative support reuse and its acquisition cost

The [new optional policy](on-demand-negative-edit-reuse.md) retrieves recent checked
UNSAT roots, discovers a causal support only after a near-edit match, and emits
ordinary core/subset proofs only after containment. It finds ten negative transfers
per stream without supplied donor labels. All new results are independently checked.

Exposed/holdout native expansions fall 1,961 to 1,579 / 3,159 to 2,781, but query
time rises 2.40% / 5.81% in both orders. Materialization adds 650 / 740 smaller
proof records. SQLite bytes fall 15.30% / 9.37%; cold replay improves, while warm
time regresses. Outcome and family closure coverage are unchanged. Keep this as
a space/replay tradeoff and retain the previous witness pool as the latency baseline.

Next: reuse a bounded, exact derivation plan between support discovery and checked
materialization, which now repeat causal traversal and coordinate reconstruction.
Holdout visits 994 support nodes in discovery and another 488 in materialization.
Six failed supports need a deleted clause; alternative surviving supports remain
a distinct coverage gap. Negative proposals and candidate order are not restored
on reopening. Budgeted extraction is not a total time/space or arbitrary-SAT bound.

Resume `experiments/results/cnf-negative-edit-pool/checkpoint.json`. All 652 prior
sources and 8,141 artifacts across 120 manifests remain unchanged. The union now
contains 39,211 native records; old payloads remain authoritative and all trial
alternatives are preserved. Both readers recheck earlier composed/pilot decisions,
864 witness-pool observations, larger-stream results/recovery and inventory.
All 1,327 full / 188 focused tests and 512 exhaustive two-variable checks pass.
The 230-page manuscript builds cleanly with 64 proof blocks unchanged. Forty-four
SQLite warnings remain at unchanged full-suite sites. The first profiler's
JSON-versus-integer model-key comparison failure is preserved; corrected comparison
matches all semantic fields, counters and native digests. Timed runs are unchanged.


## 2026-11-19: share causal derivations and expose an affine integration gap

[Shared support derivations](shared-support-derivations.md) remove repeated
support selection during proof emission. The query-local plan keeps exact source
choices under a 4 MiB retained charge; all output uses the unchanged native
verifier. The cap excludes encoding/decoding transients and emission workspace.
Capacity fallback and failed/rolled-back queries discard their plans safely.

Twelve frozen serial workers compare witness-only retrieval, negative edit reuse
and shared plans on exposed 24/48/72 and fresh 42/66/90 scales. Mean query time
falls 6.45% / 2.62% against negative reuse, in both orders; complete time falls
3.14% / 1.02%. Plans eliminate 415 / 518 repeated support-node visits. Proof bytes,
expansions, outcomes and permanent storage match negative reuse exactly. Accepted
plan charges peak at 711,610 / 1,378,956 bytes. Holdout query time still exceeds
witness-only search by 0.87% on the mean, with mixed paired signs. Memory and
mean warm/cold replay costs rise slightly against negative reuse.

Decision and family closure coverage do not increase: exposed outcomes remain
70 SAT / 36 UNSAT / 2 unresolved attempts, holdout 57 SAT / 41 UNSAT / 10 unresolved.
Random 3-CNF and parity mixtures consume 79.16% of first-order holdout query time.
The ten stops commit 2,622 checked negative residuals, whose conditions cannot be
silently dropped during reuse. Six distinct source roots remain absent at stream
end; query stops are not counts of permanently unresolved distinct roots.

A posthoc label-free screen applies the existing affine-negative checker to all
108 holdout inputs. It preserves 14 checked negative observations, including
stopped cases 42 and 43; case 43 is still absent at native stream end. Screen time
is 0.099 seconds before publication/persistence/replay. Native observations are
unchanged and the screen certificates remain separate from the SQLite union.
Consistent extracted subsystems give no verdict for leftover clauses. Next:
integrate a bounded source-checked affine probe with all costs measured on a fresh
split, then address transport of conditioned residuals and surviving supports.

Resume `experiments/results/cnf-support-plan/checkpoint.json`. All 658 prior
sources and 8,197 artifacts across 121 manifests are unchanged. Both readers
verify the union of 45,061 native records and all earlier extensions/observations.
The audit checks 1,296 chronological attempts, 432 exact plan/negative comparisons,
and 512 exhaustive formulas. All 1,336 full / 197 focused tests pass. Final build,
64 unchanged proof blocks and the 664-source ledger are recorded in `checks.json`.
No uniform polynomial expansion or arbitrary-SAT result is established.


## 2026-11-19: bounded affine probing and the remaining partial-search gap

[The bounded affine probe](bounded-affine-probe.md) integrates the existing
source-checked negative authority before native acquisition. It accepts only
contradictions; consistent/incomplete or budget-stopped subsystems fall back.
No native certificate acquires an affine dependency. The public input adapter
snapshots finite outer/inner iterables after review exposed consumption before
fallback in the first kernel. Both twelve-worker runs and exact comparisons are
preserved; final timings include copying, checking, persistence and cold replay.

On exposed 42/66/90 and fresh 96/108/120 streams, mean query time falls 20.25% /
41.87% against planned reuse and 19.93% / 42.96% against witness-only retrieval.
Holdout native expansions fall 8,261 to 4,982, SQLite bytes 133,857,280 to
77,430,784, and checked objects 368,606,936 to 210,148,243. Complete time improves
in both orders. Holdout outcomes change from 50 SAT / 32 UNSAT / 26 unresolved to
50 SAT / 43 UNSAT / 15 unresolved attempts, with no newly stopped completed case.
Seven additional distinct roots are available at stream end, leaving nine absent.
All eighteen parity attempts use affine certificates without native expansion.

Retain the warm regression: on matched completed cohorts, warm solve time rises
89.44% exposed / 93.27% holdout against planned reuse. Discovery limits exclude
input copying, canonicalization, stored-proof checking, publication, native
fallback and full archive/cache growth. These designed workloads and fixed budgets
do not establish representative performance or unrestricted SAT closure.

Next: bounded support/containment reuse from committed partial searches. Random
3-CNF and shared mixtures consume 92.46% of holdout query time. Fifteen stops
consume 9.335 of 12.187 seconds and commit 3,820 checked negative residuals;
all fit the current 4,096-literal origin limit. The negative pool currently admits
completed query roots only, while exact residual memoization already exists.
Conditional refutations need checked source/assumption transport or containment
in the current residual before broader reuse. Charge selection, extraction,
checking, invalidation and cold reconstruction. Every remaining stopped source
has affine rank zero; no low-free-dimension completion shortcut applies directly.

Resume `experiments/results/cnf-affine-probe-safe/checkpoint.json`. The union has
54,418 native and 47 affine-negative records plus unchanged prior extension
records. All 664 previous sources, 8,275 previous artifacts and 57 preserved
first-run artifacts remain intact. The audit checks 1,296 chronological attempts,
1,296 exact first-run comparisons, 512 exhaustive formulas and all earlier
observations. All 1,347 full / 208 focused tests pass. The 232-page manuscript
builds without warnings and keeps all 64 proof blocks. Final source ledger: 672.
Initial fixture failures, the corrected input boundary, regressions and remaining
SQLite warning sites are recorded; old authoritative bytes remain unchanged.


## 2026-11-19: partial-residual retrieval fails the total-cost comparison

[The bounded residual pool](partial-residual-retrieval.md) admits committed
nonterminal negative proofs, including proofs left by stopped searches. It caps
retained pool/index charge at 512 KiB, probes at 32 per query, candidates at four
per probe, and causal support planning at one bounded attempt per query. The
original native checker validates every origin/core and target containment.
Conditional refutations cannot become unconditional source verdicts. Cold tail
seeding is supported; exact pool-order and source-map restoration are not.

On exposed 96/108/120 and fresh 126/132/138 streams, mean query time **increases
5.88% / 4.27%** and complete time **3.08% / 2.13%**, in both orders. Outcomes and
recorded expansion counts are unchanged: holdout remains 42 SAT / 39 UNSAT /
27 unresolved attempts. Holdout SQLite bytes fall only 0.034%, while compressed
storage and checked-object space grow. Keep the input-safe affine policy as the
performance baseline; this optional experiment does not widen certified coverage.

Holdout yields one hit from 1,346 probes and 37 candidates, after 28.15 MB of tail
reads, 993 admissions and 985 evictions. An instrumented replay reproduces all
query counters, results and native/affine digests; admission costs 1.863 seconds
versus 0.341 for retrieval, with repeated size charging a large component. These
profile times overlap and are diagnostic. Total bounds exclude transient decode,
prerequisite checking, full checked state, publication and fallback.

A separate checked counterexample shows literal anchors in separately compacted
coordinates missing a core that the unchanged subset checker accepts under a
supplied injective map. The map is not automatically discovered; frequency and
savings on the timed streams remain unknown. Next: retain bounded source-variable
correspondence for residuals across same-source branches and edits, recheck
transported containment, and charge map admission, maintenance and cold restart.
Selective admission and incremental size accounting are supporting work once
useful transport is demonstrated. Random/shared mixtures still consume 86.02% of
holdout query time, and stopped attempts 19.463 of 23.074 seconds.

Resume `experiments/results/cnf-partial-residual-pool/checkpoint.json` for the
preserved evidence union. All 672 preceding sources and 8,402 artifacts across
124 manifests are checked unchanged; earlier proofs and observations remain
authoritative. The audit covers 864 chronological attempts, both independent
readers and old histories, plus 512 exhaustive formulas. All 1,355 full / 216
focused tests pass; the 233-page manuscript builds without warnings and preserves
64 proof blocks. The final source ledger has 678 entries. Full-suite SQLite
warning sites and the prefreeze policy revision are retained. Detailed union
counts and evidence bindings are in `checks.json`. No arbitrary-SAT resource bound
or complete efficient classification follows from this experiment.


## 2026-11-19: retain residual variable maps; locate multi-clause reuse gaps

[Source-variable transport](residual-variable-transport.md) composes existing
normalization maps along native visits, stages bounded negative hints, admits
only committed origins, and restores hint metadata after restart. Exact target
subset identity and the original native proof checker remain authority. A
conditional residual never refutes its unconditioned source by itself. Stable
external IDs supply the proposal; arbitrary renaming discovery remains open.

Three policies run in two opposite orders on twelve serial workers: affine
baseline, compact-coordinate ablation and mapped matching. The diagnostic finds
five mapped transfers versus none compact, reducing recorded expansions 17 to 16,
but mapped runtime stays above baseline. On the fresh 144/150/156 holdout, all
arms preserve identical native/affine proof digests, 10,249 expansions and
33 SAT / 38 UNSAT / 37 unresolved attempts. Mean mapped query time **rises 5.26%**
against baseline and 1.56% against compact, in both orders. Complete time rises
2.09% against baseline. SQLite grows 0.024%; checked objects grow 0.087%. Retain
the affine baseline. Separate stage/pool/map limits do not cap total computation.

Mapped matching produces 1,758 candidates versus 31, but no holdout transfer.
A posthoc census reproduces every result, counter and native/affine digest.
All candidates miss 7–220 clauses (median 89). Bounded causal support extraction
on eighteen closest proposals gives six budget stops and twelve supports still
missing 3–19 clauses, with no new refutation. The old one-missing-clause policy
therefore cannot help these observed candidates. The exact residuals, origins,
maps, counterexamples and trial costs remain preserved.

Next: price the existing guarded/first-false composition rules on transported
supports with small gaps, starting with the selected residual from case 61
(30 support clauses, three missing), then cases 25/31 (five missing). Reconstruct
and check the core and bind the target before screening or acquisition. The
augmented target contains the UNSAT core; only the all-true region of the missing
clauses is excluded. Other regions need checked branches, and SAT branches must
lift correctly. Preserve historical partition regressions and follow the pilot
with fresh inputs. Random/shared mixtures consume 81.26% of holdout query time;
stops consume 27.627 of 30.091 seconds. No arbitrary-SAT bound follows.

Resume `experiments/results/cnf-residual-transport/checkpoint.json`. Its proof
union contains 73,835 native / 71 affine-negative records plus all previous
extensions. All 678 preceding sources and 8,462 artifacts across 125 manifests
are unchanged; previous authoritative bytes remain intact. The mapped trial's
hint state has a separate resume archive. Validation checks 720 chronological
attempts, independent readers, old histories and 512 exhaustive formulas.
All 1,366 full / 227 focused tests pass. The 234-page manuscript builds without
warnings and preserves all 64 proof blocks. Final source ledger: 684. Initial
fixture failure, full-suite SQLite warning sites and all regressions are retained.
