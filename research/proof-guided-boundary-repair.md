# Proof-guided boundary repair and exact outside contexts

The three remaining misses on the **exposed constructed repair panel** now have
checked models: **29/32 → 32/32**, with the same total **20,000 search states per
input**. All 29 earlier models are reproduced unchanged. Mean complete measured
cost falls **17.60%**, while checking, replay and retained evidence grow. This is
an exploratory repair-kernel result, not fresh external generalization or a
new tractable class. Production defaults and the separate external 37/37 and
synthetic 182/182 unions remain unchanged.

## Exact conditioning and proof-guided expansion

Let `a` be a complete, possibly rejected proposal and `U` the free variables.
Fix every variable outside `U` to its value in `a`. Drop a clause only if a fixed
outside literal satisfies it; otherwise retain its projection onto `U`, including
empty clauses. Call this exact cofactor `F[U,a]`. Assignments satisfying that
cofactor correspond exactly to models of the original source agreeing with `a`
outside `U`. In particular, fixing all outside assignments partitions all models
of every valid CNF; enumerating those assignments may be exponential.

A complete full-radius refutation of `F[U,a]` excludes **that outside context**,
not the whole source. For each projected clause used by the checked refutation,
choose one original parent clause, deterministically preferring fewer outside
variables and then literal order. Any global model must change at least one
outside variable in these chosen parents: keeping those outside values leaves
the same contradictory projected clauses. Free those parent variables and
reconstruct the cofactor. This is a justified direction for relaxation, not a
promise that the wider context has a model. The growing contexts are nested;
they are not disjoint branches and their sizes must not be summed as coverage.

The first free set contains all variables in the near-model's false clauses.
Every induced constraint is retained, including clauses that were satisfied
before a free variable changed. Prefix flip/keep commitments are released when
recentering. Earlier negative search context is never transferred to the new
seed. A local witness is lifted with the fixed outside assignment and checked
against **every original clause**.

A fresh source occurrence index, outside-satisfaction counts and projected
clauses are reused as the free set grows. Each newly released variable updates
only incident clauses; the active clause set grows monotonically. Snapshot
sorting/deduplication, support extraction, parent selection and copies are
charged. Local disjoint search is rebuilt and restarted every round; this work
and independent full-source cofactor reconstruction remain explicit costs.
The index has 3,141 source occurrences across the three misses and processes
2,157 release incidences; snapshots scan 1,783 active clauses and charge 4,595
projected literals. These categories are not a complete instruction count.

The checker independently reconstructs the cofactor from the raw source,
complete proposal and free set, then checks the old disjoint exclusion at full
local-support radius. It never trusts the incremental index. Changed outside
values, source clauses or free sets must be checked again. For example,
`(x OR y) AND (NOT x OR y)` is contradictory when only `x` is free and `y=false`,
but globally satisfiable with `y=true`. The retained counterexample rejects
stale proofs after changing `y`, freeing it, or deleting a source clause.

## Acquisition is included in the common budget

Both arms collect the best complete proposal during the unchanged disjoint
traversal; baseline behavior and existing counters reproduce the prior run
exactly. The new arm stops that prefix at **10,000 states** and shares the
remaining allowance across at most **eight** conditional rounds. No retained
near-model is supplied free to timed discovery. The policy was chosen after
exploratory probes on the already exposed cases, and those probe scripts and
outputs are preserved. Truth witnesses and case identifiers never enter search.

The prefix's rejected models have **2, 1 and 8** false clauses, respectively.
The earlier 20,000-state snapshots with 1, 1 and 5 failures are preserved, but
are not used without charging acquisition. Eleven independently checked local
refutations guide fourteen rounds in total:

| ID | Free-set sizes, in order | Local states | Prefix + local states | Distance from near-model |
|---|---|---:|---:|---:|
| 24 | 6, 15, 25, 39, 59, 77 | 468 | 10,468 | 27 |
| 25 | 3, 8 | 11 | 10,011 | 2 |
| 29 | 21, 26, 32, 43, 63, 78 | 5,731 | 15,731 | 42 |

All three sources have 80 variables and 349 clauses. One repair is genuinely
confined to eight free variables. The others require **77/80 and 78/80** free
variables under this policy, so broad coupling remains. These widths and model
distances are observed, not proved minimal. A stalled boundary or exhausted
state/round limit returns unknown. Even a complete local refutation is never
promoted by this wrapper to a global negative answer.

## Matched costs and persistence

Four fresh-process pairs alternate mode order. The clock includes raw source
JSON reads, proposals, index construction and updates, near-model copies, local
solver restarts, discovery checks, explicit checks, writes, compression, warm
reload and two cold reload/checks. The discovery sidecar stores every local
exclusion and the context needed to reconstruct it. Each replay reloads sources,
models and sidecars; no search state survives. OS caches are not flushed.
Imports, reporting metadata and independent audits are additional.

| Measurement | Full disjoint prefix | Prefix + boundary repair |
|---|---:|---:|
| Certified SAT sources | 29 | 32 |
| Unresolved sources | 3 | 0 |
| Total explored states | 118,552 | 94,762 |
| Mean complete seconds | 2.64746 | 2.18151 |
| Acquisition/internal checks | 2.54117 | 1.99924 |
| Explicit checks | 0.02148 | 0.03862 |
| Warm replay | 0.02484 | 0.04344 |
| Two cold replays | 0.05011 | 0.08599 |
| Model JSON bytes | 49,362 | 55,478 |
| Discovery JSON bytes | 65,107 | 204,878 |
| Model gzip bytes | 5,547 | 6,217 |
| Discovery gzip bytes | 6,238 | 17,016 |
| Combined gzip bytes | 6,685 | 22,531 |
| Maximum observed RSS bytes | 29,376,512 | 30,474,240 |

Paired complete-time reductions are **15.92%, 19.88%, 15.53% and 19.05%**.
Mean reduction is **17.60%**. Combined compression shares repeated content;
separate gzip sizes do not add to the combined size. The measured persistence
phase charges all three compressions. The baseline still leaves three sources
unanswered, so these are fixed-policy workflow costs, not equal complete-solving
costs or a fresh CDCL comparison. Append-only historical storage is additional.

A four-variable, fourteen-raw-clause counterexample illustrates lack of universal
restart-budget dominance. At a small cap of two states, uninterrupted traversal
finds a model; a one-state prefix followed by one local state remains unknown.
This post-hoc example is retained and does not test or change the frozen
10,000/20,000 policy. No claim of dominance at arbitrary caps is made.

## Verification and remaining gaps

Independent truth tables validate **8,402 outside contexts** over 576 inputs:
all 512 subsets of the nine canonical clauses on two named variables, with every
actual-support seed and free subset, plus 64 fresh sparse signed sources with
duplicates, tautologies and edits. The fresh inputs use two seeds and three free
sets each. All **1,033 satisfiable contexts and 7,369 exclusions** agree with
truth. There are **6,704** incremental/direct reconstruction comparisons and
**1,728** bounded policy runs, of which 312 return fully checked models. A second
audit reproduces the semantic records exactly.

Eighteen focused tests cover unchanged prefix traversal/counters, incremental
conditioning, empty sources, signed sparse names, invalid seeds/free sets and
budgets, partial refutations, edits, lost context, stale proofs, parent choice,
and checking with discovery disabled. All **2,546 full and 18 focused tests
pass**. Validation reproduces all eight measured runs and their cold counters,
preserves **245 prior manifests, 82,407 artifact entries and 1,336 scientific
sources**, and cold-checks the old external 37/37 union again. All **85** earlier
manuscript proofs remain unchanged; one exact-conditioning proof is added.
Existing unclosed-SQLite warnings remain in the full-test log.

**Next priorities:** freeze unseen external inputs before transfer claims;
compare the fixed policy with the full portfolio and an appropriate fresh solver;
explain or reduce the nearly full-width residual interactions; and reuse checked
negative supports economically across related contexts and edits. General
recognition, source-dependent preprocessing, compact proof acquisition and
unrestricted SAT expansion bounds remain open. Finite panel completion and an
exact decomposition of all CNFs do not establish efficient solution of every
class.

Resume `experiments/results/cnf-boundary-repair/checkpoint.json`, key
`boundary_repair`.
