# Small additive clause budgets: bounded chains and measured coverage

The preceding [clause-count policy](clause-bound-elimination.md) left 57 selected
leaves. Fifty admitted a complete opposing-pair projection adding at most two
clauses. That local opportunity does not imply a useful chain. This experiment
implements fixed allowances of one and two and measures actual structural
closure, discovery work and retained state.

## Exact admission and preservation

`AdditiveEliminationInventory` first runs the earlier joint non-growth and then
clause-count-only policies. Only an unresolved terminal invokes the additive
fallback. It retains all non-tautological resolvents, removes exact duplicates,
and accepts at most d additional clauses. Both candidate and opposing-pair caps
remain 64. Among eligible candidates it minimizes clause delta, then literal
delta, pair count and variable identifier. Thus the two-clause local rule agrees
with the one-clause rule when the latter has a candidate. This is not a proof of
monotone whole-source coverage: changed descendants can alter parent selection.

A certificate names the pivot. An independent checker reconstructs all opposing
pairs, validates the actual clause increase and strict support decrease, and
binds the exact target. The existing existential-projection identity applies;
SAT model restoration checks the whole source. Null proposals remain unresolved,
not UNSAT or a proof that no successful order exists. Policy-specific keys retain
all earlier results. Cold replay does not invoke discovery. This remains an
optional experiment, not a default solver change or a new elimination identity.

All 516 Python tests pass. New cases exhaust all 512 two-variable CNFs under
budgets zero, one and two; check every pivot, full truth-table projection and
model extension; exercise random six-variable formulas, edits and signed 130-bit
identifiers; distinguish one-, two- and three-clause growth; reject malformed
certificates and models; and check SQL history preservation and cold replay.
The 50 initial two-clause opportunities are independently verified, without
claiming they close their sources.

## Conditional resource bound

Let a normalized elimination-only chain start with m0 clauses and n0 variables.
After k accepted steps, support is at most n0-k and clause count at most m0+dk.
Consequently k is at most n0, every state has at most n0(m0+dn0) literal slots,
and retaining all formula states costs at most (n0+1)n0(m0+dn0) slots.
`AdditiveElimination.lean` proves these conditional bounds with explicit
normalization, reachability and list-size premises. The full Lean build and
axiom audit pass at 4,216 declarations / 2,028 theorem declarations.

The proof guarantees neither an admissible next pivot nor an efficient search
for a useful order. It does not refine Python, bound other branches, profiles,
keys or multiple inputs, or account for identifier bit lengths. A polynomial
formula payload on one chain does not bound total discovery or persistent state.
Fixed B opposing pairs also give the weaker m0+Bn0 clause bound; a useful pivot
can still exceed B.

Each additive attempt pays earlier failed recognition, source validation,
occurrence indexing, O(n log n) sorting, up to O(KL) parent accounting and
O(KBw) expected container work for K candidates, B pairs and maximum width w.
Checking rescans the source, reconstructs all admitted pairs and sorts the target.
Every accepted child runs structural recognition again. Hash and integer costs,
serialization, database updates and cold checking are additional charges.

## Persistent endpoint evidence

The matched query path still uses the ordinary SAT solver on the original CNF;
structural closure is a separate result. New elimination edges additionally
receive independent source and target solving, with every SAT child model lifted.
This diagnostic now uses incremental SQL accounting and retains a separate
compressed residual database plus a JSONL file of endpoint answers, roots and
models. All diagnostic residual rows are cold-checked without discovery or
changed bytes. Acquisition archives preserve every paid-prefix row. These
supporting changes preserve future reuse of computed evidence; their timing is
not comparable to the previous in-memory diagnostic with repeated SQL census.

Query timing includes discovery, checking, persistence, ordinary solving and
successful root lifts. Seed restoration, cloning, opening, frontier walks,
compression, cold replay, endpoint diagnostics and allocation sampling remain
separately recorded. Four-case Python allocation excludes native SQLite, RSS and
full-history peak. The prepared prefix is previously paid work, not free input.

## The local opportunity does not close the saved leaves

The 57 final leaves from the clause-count study are queried from empty history
at conditioning depth zero. Baseline, allowance one and allowance two all close
**zero**. Query times are **3.42106 / 3.76690 / 4.88712 seconds** and discovery
**0.72722 / 1.31486 / 2.29019 seconds**. Complete acquisition databases occupy
**17,551,360 / 18,509,824 / 19,894,272 bytes**. Selected unresolved literals
increase **25,488 / 25,838 / 26,604**. Larger admission budgets permit valid
progress in variable count while making the selected residual representation
larger, without reaching a recognized endpoint.

The two-clause mode acquires 105 new additive edges (68 SAT, 37 UNSAT), all
increasing both clause and literal count. Every endpoint pair is independently
solved and every SAT child model restored; consecutive elimination chains reach
five steps and target width six. Its extra endpoint diagnostic takes 7.44911
seconds and retains a 39,776,256-byte reference database, separately from the
19,894,272-byte acquisition archive. This additional storage is evidence cost,
not included in the query database comparison. Cold verification of that
reference takes 2.19721 seconds. All three acquisition databases also cold-check
unchanged. Ordinary solver answers and search counters match exactly.

These are selected old failures, one fixed execution order, not an independent
holdout or a general timing ratio. Whole-source recomposition is measured
separately. The negative leaf result rules out promoting these budgets merely
because a low-growth first pivot exists in 50/57 leaves.

## Original-source recomposition: no extra closures

On the same 83 original prior misses, using the paid 417,370,112-byte prefix and
conditioning depth two, **all three policies close exactly 31 sources**. Neither
additive budget gains or loses a closure. All retain 57 selected unresolved
leaves across the 52 open originals; their literal totals are
**25,488 / 25,752 / 26,260**. The available extra pivots do not resolve these
sources under the tested greedy policy and bounded parent selection.

Query times are **121.61751 / 142.26465 / 163.21184 seconds**, of which discovery
uses **119.49592 / 140.20864 / 161.23142 seconds**. Complete acquisition databases
are **674,234,368 / 700,178,432 / 734,814,208 bytes**. Added bytes above the shared
prefix are **256,864,256 / 282,808,320 / 317,444,096**. Thus allowance two costs
about 34.2% more query time and 23.6% more newly acquired database space than the
clause-count baseline, with no added closure. These are single ordered runs,
not general ratios or measurements of full-process peak RAM.

Allowance one tests 103,577 new candidates and rejects 102,219 for growth;
allowance two tests 155,645 and rejects 151,131. They acquire **1,021 / 2,530**
new additive edges, including alternatives that are not selected by the final
plan. The highest recorded single-source discovery cost occurs at case 73 in
all three modes. A separate profile is used below to attribute its work; a
single-source profile does not reproduce the preceding ordered cache history.

The ordinary solver answers, profiles and search counters match. Structural
closure remains separate from solving the original formula. Increasing the
allowed growth again is not justified by these results alone. The remaining
gap is useful endpoint discovery and avoiding repeated unsuccessful work,
rather than the correctness or conditional formula size of an accepted step.

All original-input acquisition archives pass cold replay without byte changes,
in **109.97163 / 107.04672 / 123.12474 seconds**. Every paid-prefix row survives;
the baseline exactly reproduces the previous clause-count acquisition database.
Allowance one has 568 SAT / 453 UNSAT new edge pairs; allowance two has
1,390 SAT / 1,140 UNSAT. Both endpoints of every new edge are independently
solved, every SAT child model is restored, and all diagnostic proof rows pass
cold replay. New targets reach widths eight and nine respectively; maximum
consecutive elimination-chain length remains thirteen, including earlier-rule
steps. All observed chain bounds hold.

Independent endpoint diagnostics cost **111.11488 / 273.64557 seconds**. Their
separate reference databases occupy **532,144,128 / 1,236,189,184 bytes** before
compression and hold **68,039 / 155,448** verified residual nodes. Cold reference
verification costs **35.32182 / 94.64726 seconds**. These files, hashes and
endpoint JSONL records persist the computed results; their space and time are
additional to acquisition. Incremental accounting uses one initialization census
per reference solver, rather than a census after each solve. No matched timing
comparison of the old and new diagnostic is claimed.

Four-source peak traced Python allocation is **16,028,492 / 16,717,304 /
17,353,939 bytes**. This small sample excludes native SQLite, RSS and full-history
peak. Complete phase records are retained in the
[original comparison](../experiments/results/cnf-additive-elimination-originals/README.md).

## Repeated controls also give no coverage gain

The separate 96-input control reuses random formulas, signed renamings, clause
replacement edits and disjoint Horn mixtures at base sizes 12, 24 and 40, with
the same paid prefix and conditioning depth two. Mixtures append seven variables.
The historical generator name `fresh_cases()` does not make it an untouched
holdout. **All three modes close the same 88 inputs**, with no gains or losses.
Query time increases **10.45184 / 12.74294 / 14.87718 seconds** and acquisition
bytes **456,785,920 / 461,209,600 / 465,776,640**. Selected open literals increase
**2,682 / 2,695 / 2,717**. The eight open sources stay unresolved by recognition.
All new endpoints, acquisition archives and reference archives pass their stated
checks. This control supplies no coverage transfer and no reason to promote
either larger budget. [Records](../experiments/results/cnf-additive-elimination-fresh/README.md)
retain the phase costs, proof archives and allocation sample.

## Where the work goes, and the next informative gap

A separate cProfile run selects the slowest measured two-clause source: case 73,
original corpus index 1444, 48 variables and 204 clauses. Its historical group
name is `subsumption_holdout3`, but it is a selected prior failure. The matched
query's discovery took 5.42821 seconds. Profiling the source alone from the paid
prefix takes **13.30082 instrumented seconds**, so those timings must not be
compared as a regression. The preceding ordered query cache history differs too.
The profile remains unresolved, with one selected leaf / 285 literals.

`indexed_certificate` is the largest own-time function: **1,694 calls, 1.67039
own / 2.21385 cumulative seconds**. `_find_core` runs **866** times and has
**3.48529 cumulative seconds**, including nested indexing and other work.
Single-pass reconstruction runs 7,154 times; normalization runs 3,875 times.
Direct additive discovery and checking total only **0.24555 cumulative seconds**
(105 discovery and 210 check calls), under 2% of the instrumented discovery total.
This is attribution on one costly source, not a causal whole-corpus ablation.
Nested cumulative times overlap and must not be added. The profile, raw pstats,
checked acquisition output and all old rows are retained in separate artifacts;
no additional full cold audit of the profile archive is claimed.

The exact final-frontier scan confirms the moving growth barrier. At allowance
one, 40/57 remaining original leaves have minimum next increase two, 13 need
three, three need four and one has no pair-bounded candidate. At allowance two,
43 need three, eleven need four, two need five and one has no pair-bounded
candidate. Removing the caps permits a current-allowance step in only one leaf
for each mode. Retained-clause subsumption would permit such a step in 18 and
22 leaves respectively, but integrated cost and eventual closure remain open.
These are local opportunities after selected orders, not a reason to repeat the
failed inference that more admitted steps must close sources.

The next cost experiment should first count exact duplicate original and
augmented CNFs at the repeated subset-search boundary, then reuse independently
checked results when the complete ordered source and policy agree. Cross-edit
reuse needs explicit invalidation for changed clauses, clause order, implied
clause pools and their source-linked reasons. A proposal cache cannot substitute
for an independent checker. The discovery question is a small budget of
alternative pivots that actually expose units, implications, separators or
recognized families. Charge every failed lookahead and compose any success back
to its original source. Neither promising signal nor a subset-cache speedup is
established yet. Both additive budgets remain negative optional controls; an
untouched holdout and a new full-corpus run remain open.
