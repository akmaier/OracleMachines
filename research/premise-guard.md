# Reuse checked premises before traversing support proofs

The prepared selector indexes each retained core by its clauses. A query counts
shared memberships through clause postings and examines, in the original bank
order, cores missing exactly one clause. It retains the earlier nonempty-clause,
shared-variable and changed-residual conditions. The bank owns copied metadata;
new or edited core descriptions require rebuilding it. Proof availability is
read afresh on each selection and can grow in the append-only session. Clause
membership uses shared raw variable coordinates; this index adds no arbitrary
renaming or formula-equivalence recognition.

For each suggested clause C, the selector first checks whether the strengthened
formula T ∧ C already has a negative native proof. That proof alone establishes
that all models of T falsify C. The separate core proof need not be traversed.
Core metadata is a search hint, never negative evidence. A pending core can
therefore suggest a valid guard if the strengthened formula itself is checked.
If the strengthened formula is absent, the selector checks the core and uses the
existing subset-publication rule. A positive strengthened formula is skipped.
No branch searches for a premise from scratch.

The guarded child is solved normally. Existing chain checking validates every
premise and child, and lifts SAT models through both guards. A checked conclusion
bank supports warm repeat visits. Native proof formats are unchanged; composed
answers still require their bound chain sidecars. This is one additional guard
per ordinary reuse miss, not an optimal restriction policy.

## Recognition and resource contract

Let B be the total retained clause memberships and H(T) the number of posting
entries visited by clauses of T. Index construction and storage charge the copied
core descriptions, clause sets and B posting indices. Query matching normalizes
T, visits H(T) entries, counts overlaps and sorts the candidate core indices.
It still scans the memberships of each selected near core to extract its missing
clause, and charges restriction, canonicalization and actual proof checking.
H(T) can be B: dense overlap gives no universal asymptotic improvement. The index
trades preparation and additional memory for avoided repeated core normalization.

The checked strengthened premise may itself have a large proof graph. A missing
premise still requires checking the core and publishing its subset proof. Neither
posting lookup nor a small clause core bounds this work or the final child solve.
All guarantees are conditional on the actual checked premises; no polynomial
arbitrary-SAT or minimum-expansion claim follows.

## Fresh matched comparison

All modes start from the same 20,666-key union and fixed 207-entry legacy /
176-entry causal portfolio. Input selection excludes 2,688 ordinary sidecar
records, eight chain records and cached native source roots, then selects the
next 64 neighbours from each of three templates. All 192 queries are visited
again through a checked conclusion bank. Two reversed-order triplets run in
fresh processes without concurrent tests, builds or profiling. The ordinary
policy, the previous core-first chain policy and the prepared premise-first
policy share preparation, chain persistence and warm replay.

| Measure | Ordinary | Core-first chain | Premise-first chain |
| --- | ---: | ---: | ---: |
| Fresh expansions | 139 | 67 | 67 |
| Splits | 46 | 19 | 19 |
| New native rows | 436 | 364 | 364 |
| Added native payload, bytes | 706,491 | 579,076 | 579,076 |
| Additional guards | 0 | 8 | 8 |
| Additional-premise publications | 0 | 0 | 0 |
| Mean query seconds | 2.37536 | 1.88600 | 1.77365 |
| Mean complete seconds | 20.14800 | 18.48525 | 19.60037 |
| Mean peak RSS, bytes | 474,415,104 | 450,600,960 | 437,657,600 |
| Compressed archive plus first-trial sidecars, bytes | 9,906,106 | 9,947,231 | 9,947,155 |

The extra guard is used on eight of eleven ordinary misses. Seven queries save
expansions; none increases expansions or publications. Fresh expansions fall
**51.80%**, new native rows **16.51%**, and added native payload **18.03%** versus
the ordinary policy. Answers remain 97 SAT / 95 UNSAT. The two chain policies
produce identical native proof payloads. Case 45 uses an earlier pending-core
hint in the premise-first policy, with the same checked strengthened premise
and the same child as the later ready core selected by the old policy.

The prepared policy reduces additional verified proof nodes **247 -> 102**,
verification literal payload **21,135 -> 12,491**, and read bytes **198,609 ->
109,646**. Additional-guard literal visits, including the new index's setup,
fall **208,132 -> 36,985** (29,906 setup plus 7,079 query visits). The index holds
11,953 memberships and 484 distinct clause keys and visits 42,548 posting entries
across eleven calls. These units describe different operations; the posting
count is not directly interchangeable with the old 2,504 core inspections.

Mean extra-selection/checking time falls **0.123182 -> 0.032626 seconds** versus
core-first, but complete time rises 6.03% on average, with paired changes
**-31.67%, +58.09%**. Versus ordinary, complete time averages 2.72% lower with
paired changes **-8.51%, +1.10%**. Neither comparison establishes a stable total
speedup. Peak RSS means are lower, but two samples do not establish a general
memory bound. Complete cold replay and compression consume about 61.9% and
20.2% of the premise-first mean, respectively; their variation dominates these
small selection costs.

Native payload measures identifier plus ASCII JSON length, not SQLite pages or
peak RAM. Larger chain records offset the smaller compressed archive: retained
trial size rises **0.414%** versus ordinary. Old history, indices, all repeated
trials and independent validation are additional costs. Original acquisition and
input selection are separately charged. Complete worker time includes restore,
setup, query/chain work, warm-bank construction/replay, serialization, full cold
audit, compression and report generation, excluding imports and final timing
rewrite. The frozen-worker parity check is untimed.

## Next discovery gap

The remaining expansions by template are **17 / 4 / 46**, versus **41 / 10 / 88**
for ordinary solving. Case **68 accounts for 27 of 67 expansions** and admits no
single-missing-clause guard. Read-only pre-query diagnosis finds that its nearest
overlapping ready cores miss **three clauses**. Cases **6 and 135**, with seven
expansions each, need three and two missing clauses respectively. Pending cores
do not improve these distances. Cases 29 and 146 still need nine and eight
expansions after the extra guard.

The next structural test should price an exact decomposition from several
missing clauses, beginning with case 68 and retaining 135 as the smaller control.
A checked negative T ∧ C1 ∧ ... ∧ Ck implies that some Ci is false, not that all
are false. A valid decomposition must cover these alternatives and account for
shared work and overlap, or partition them by the first falsified clause.
Recognition, premise derivation, branch composition and all child solving remain
charged. Missing-clause count is not a derivation-cost oracle. The present probe
publishes nothing and implements no multiple-clause inference. In parallel,
compact chain references and shared cold checking remain the measured total-cost
opportunity; structural coverage and total runtime are separate objectives.

## Validation and persistent state

All **1,028 solver tests** and thirteen focused chain/selector tests pass.
Tests check the posting index against exhaustive two-variable set scans, verify
SAT and UNSAT outcomes against truth tables, exercise missing-premise fallback,
and reject unsupported negative evidence. The first focused run exposed an
ordering mistake in the brute-force test expectation; the saved failure compares
identical literals in different orders. Normalizing that expectation fixes the
test without changing the implementation. The full suite retains 44 older
unclosed-SQLite ResourceWarnings; focused tests emit none.

Independent validation reconstructs fresh exclusions and each query's available
proof prefix, checks candidate order without the posting index, replays all six
complete native archives and chain records, and verifies warm answers. A separate
untimed run of the frozen ordinary worker matches all first-query guards,
cofactors, witnesses, child results, expansion counts, new keys and final native
payloads. All 2,957 inherited ordinary decisions and eight inherited chains pass.

Resume `experiments/results/cnf-premise-guard/checkpoint.json`: **21,128 native
keys**, adding 462 and preserving all 20,666 previous payloads, plus **192 new
checked chain conclusions**. All per-trial archives are retained, with no alternate
native certificates. The union occupies **66,498,560 SQLite / 4,889,065 gzip
bytes**; it retains historical results rather than deleting old proofs to realize
a per-policy saving. Four complete frontier lineage checks pass. Ready/pending
counts become **130/40 original, 137/70 legacy, 79/97 causal, and 79/124 optional
expanded causal**. No new support origins are acquired.

The structural authority remains 2,614 patterns / 259 pairs / 17 missing children,
original 17/24 with 999 steps and separate supplemental 24/24 with 208 steps.
All prior semantic fields remain; only parent/union/source bindings change and
two new premise-guard fields are added. The paper builds cleanly to **203 pages**
with all **64 existing proof blocks unchanged**. No new Lean or unrestricted-SAT
resource theorem is claimed.

The runtime protocol binds 426 sources. The analyzer, frozen-worker control and
remaining-gap probe bring the final source ledger to 429. Preservation checks
confirm all 422 prior sources and **4,649 artifacts in 81 manifests** unchanged.
The results directory retains raw timings, regression lists, unsuccessful matches,
all phase costs, historical exclusions, tests, control and reconstruction logs.

New manifest: **57 artifacts**. Next preservation audit: **4706 artifacts / 82 manifests**.
