# Exact symbolic preprocessing before conditioned buckets

Date: 27 November 2026. Parent: `0b1d0184`.
Evidence: `experiments/results/cnf-symbolic-buckets/`.

## Result and decision

Exact complementary-clause folding closes **2/12** exposed acquisition gaps.
On 24 frozen unique synthetic inputs, the preceding conditioned method handles
**11/24**, unit propagation first handles **13/24**, and folding with unit
consequences handles **14/24**. All variants handle **3/4** separate repeat queries.
The existing fallback already decides all 40 queries. These are changes in the
certified acquisition family, not previously unavailable SAT answers.

The cost ablation matters: unit preprocessing lowers complete time **11.54%**
relative to the wrapped baseline, while folding is **2.95% slower than units**.
Every paired comparison has the same sign. Folding still improves **8.93%** over
the baseline, but the unit-only arm is the cheapest structural variant. Fresh
solving remains much cheaper than either. Defaults remain unchanged.

## Exact rule, witnesses and maintenance

A fold replaces precisely `(C or x)` and `(C or not x)` by `C`. Both parents must
be active, and their complete remainders must be identical. This preserves the
entire assignment set, including interactions with other clauses. General
resolution does not permit replacing both parents: `(x or a)` and `(not x or b)`
imply `(a or b)`, but the resolvent accepts `x=false, a=false, b=true`, which
violates the first parent. The checker rejects this tempting overgeneralization.

An active unit `[l]` records its forced value and restricts all affected clauses.
The invariant is `original = recorded units AND current residual`, over the
original variable names. Folding preserves the residual exactly. Unit restriction
preserves it under the newly recorded value. Final renaming is inverted during
model lifting; eliminated free variables default to false. The complete source
witness is checked again. UNSAT requires the checked residual verdict; an
unresolved residual remains unknown.

Each accepted fold removes two distinct clauses and inserts at most one; each
unit removes its own clause and inserts no more clauses than the other affected
parents. Thus at most the initial number of distinct clauses can be transformed,
even without a step cap. This termination statement concerns preprocessing only,
not the later exponential conditioning/bucket obligations.

Discovery maintains an occurrence index and, in the folding arm, an index of
single-literal deletions keyed by full remainder and pivot variable. Opposite
signs propose a fold. Removing parents deletes their signatures; adding shortened
clauses adds new ones. Units update only clauses containing either polarity of
the forced variable. Stale heap candidates are revalidated against current index
entries. Every active clause remains indexed, and accepted operations strictly
reduce the clause count. No stale candidate is evidence. The independent checker
uses full clause scans for units and active membership plus set differences for
folds; it does not trust the occurrence/signature indexes.

The symbolic budget permits 512 steps and 262,144 reserved index-maintenance work
units per root. An occurrence update charges clause width; folding also charges
width squared for deletion signatures. Budget admission happens before mutation.
Unit affected-clause reads, candidate construction, stale-heap handling,
normalization and verification are outside this allowance and remain timed.
Partial transformations are still exact and may pass to the unchanged terminal
solver. This is not a bound on total runtime or RAM.

`cnf-symbolic-buckets-v1` is a separate experimental JSON authority holding the
transformation and the complete preceding conditioned proof. Preprocessing runs
**only at the source root**, not again after each conditioning assignment. Exact
source programs share within a stream under the same policy; edits invalidate
them. Every warm/cold load rechecks the transformation and terminal proof. Both
native cold readers audit fallback records; the two additional cold passes use
the same symbolic/conditioned checker, not independent JSON verifiers. Native,
affine, equivalence and Lean formats remain unchanged.

## Frozen comparisons and full costs

The 24 constructions contain 18 SAT and six UNSAT inputs: random three-CNFs of
11/14/18/22 variables, one- and two-layer guarded cores, deleted/flipped guard
clauses, planted-unit problems and parity/gate mixtures. Sparse names, signs and
clause/literal ordering are scrambled. Four repeats contain two SAT and two UNSAT
cases. Twelve exposed inputs contain eight SAT and four UNSAT cases. No new
normalized source duplicates the preceding panel. These remain designed synthetic
controls, not a representative external SAT benchmark. Generator descriptions
and independent DPLL truth labels never guide solving.

All workflows start empty, use the same fallback and run in four cyclic process
orders. The `base` arm wraps the preceding memoized depth-two method in the new
identity-preprocessing authority; it is not a timing rerun of the earlier artifact.
All structural arms retain depth two, bag width eight and 262,144 reserved
bucket probes per node. Preparation, recognition, checking, index maintenance,
JSON/SQLite writes, warm replay, cold replay and compression are charged.
Interpreter startup, report metadata, panel generation and lineage audit are
additional.

| Workflow | Discovery (s) | Solve/check (s) | Warm (s) | Cold (s) | Complete (s) | Certificate-file bytes | Native-record bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0 | 0.21309 | 0.02577 | 0.14452 | 0.47792 | 0 | 569,593 | 64,307,200 |
| base | 0.72877 | 0.42716 | 0.28588 | 0.65272 | 2.24100 | 3,035,077 | 503,671 | 67,862,528 |
| units | 0.61030 | 0.38718 | 0.25008 | 0.59402 | 1.98240 | 2,779,900 | 498,799 | 66,764,800 |
| fold | 0.67591 | 0.37847 | 0.25229 | 0.59924 | 2.04088 | 2,413,891 | 455,322 | 65,486,848 |

Units improve 9.67–12.78% over base in every paired order. Folding improves
7.89–10.88% over base, but regresses 0.84–5.61% against units. The fold workflow
is **4.27 times as costly as fresh**; units are **4.15 times as costly**. Folding's
largest measured phase is discovery, followed by cold checking. Neither variant
is selected for production.

Folding performs 1,579 accepted folds and 40 unit steps across newly acquired
root programs, versus 39 unit steps without folding. Indexed maintenance charges
149,872 signature-literal visits, 36,078 occurrence updates and 2,458 stale pair
candidates. These operation counts describe the implemented index; there is no
matched full-index-rebuild ablation, so no separate incremental-index speedup is
claimed. Twenty-eight queries perform new folds. Their discovery is 12.44% more
expensive than units; the other twelve include four exact root-program replays.

After preprocessing, total root residual literals fall **14,527 to 5,941**
relative to units (59.10%), and certificate-file bytes fall 13.17%. Nevertheless,
conditioned states rise **173 to 188** and bucket steps **252 to 391**. Removing
guards changes which core variables use the conditioning budget and can expose
more work. Literal compression is not a runtime bound.

Certificate-file bytes include pretty-printed JSON. Combined compressed
SQLite/JSON packages are **108,094 / 137,313 / 132,352 / 140,561 bytes** in table
order: folding's smaller raw evidence does not give the smallest compressed
package. Diagnostic files additionally occupy 0 / 33,328 / 30,671 / 32,710 bytes.
Historical archives, repeated reports and database/container overhead are extra.
RSS is modestly smaller for fold than units, but remains above fresh; no general
peak-memory bound follows.

## Remaining gaps

Twenty unique sources remain outside the root-preprocessed family, plus one
repeat. They contain 74 unresolved depth-zero leaves: 53 have width nine, 20
width ten and one width eleven. Twenty-eight stop immediately; 46 do some bucket
work before exceeding width. Eighteen of these twenty roots have some folds, but
none obtains a root unit assignment. Exact root compression alone therefore
fails to keep the conditioned interactions small.

A separately preserved, post-hoc unit diagnostic finds forced assignments in
**55/74** unresolved cofactors and unit contradictions in **28/74**, with 331
assigned-variable occurrences. Its full-scan work is 24,509 literal visits and
0.01775 seconds, additional to the matched timings. The profile never guided
acquisition and supplies no new root authority: refuted leaves are not the same
as refuted root problems. It identifies a specific omitted preprocessing step.

The next priority is to test **checked unit closure after conditioning**, before
building each full bucket. Branch assignments can expose units that do not exist
at the root. The root-only units arm already provides the strongest cost ablation;
first separate this cheaper operation from deletion-signature indexing at every
node. Keep explicit proof transport and shared residual identities, charge
recognition/checking, and preserve the wide random-core cases. Increasing uniform
branch depth or applying folding everywhere is not justified by these timings.

The tests exhaust all 512 two-variable clause sets and check full assignment-set
equivalence, seeded mixtures, sparse witness lifting, multilevel folds, stale
candidates, partial budgets, invalid general resolution, corrupt certificates and
cold checking with discovery disabled. Resume
`experiments/results/cnf-symbolic-buckets/checkpoint.json`, key
`symbolic_buckets.remaining`. Previous 226 manifests, 37,635 artifact entries,
1,243 sources and 68 proof blocks are preserved. Five new source/test files raise
the ledger to 1,248; one restricted preprocessing proof is added. No general
compact classification or polynomial unrestricted-SAT guarantee is claimed.

Validation: **2,258 full tests and 24 focused tests pass**. The audit replays all sixteen measured arms, preprocessing steps, conditioned proofs and four unique SQLite archives; both native readers agree. Earlier artifacts and all 68 existing proofs remain unchanged. Existing SQLite ResourceWarnings are retained.
