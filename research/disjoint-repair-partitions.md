# Disjoint repair partitions and explicit branch context

On the **already exposed constructed repair panel**, replacing overlapping
first-flip branches by disjoint cases raises checked SAT coverage **22/32 →
29/32** at the same 20,000-state cap. Seven of the ten retained misses close;
IDs **24, 25 and 29** remain budget-exhausted. This is a repair-kernel comparison,
not fresh external transfer and not the full portfolio's status on these inputs.
The earlier external 37/37 and synthetic 182/182 unions remain separate and
unchanged. No production default changes.

## Exact partition and recomposition

For a complete seed `s`, a state records both the variables `M` already flipped
and the variables `K` fixed at their seed values. The sets are disjoint. A target
flip set `T` must contain `M`, avoid `K` and have size at most the radius `r`.
If clause `C` is false at `s XOR M`, every satisfying extension must flip a
variable in `vars(C) minus (M union K)`. With these available variables ordered
`v1, ..., vt`, child `j` flips `vj` and keeps `v1, ..., v(j-1)` at their seed
values. Each satisfying target has a unique first flipped variable in this
order, so the child **solution sets** form a disjoint union of the parent's
solution set. The all-kept case violates `C` and needs no search child.

This replaces overlapping OR branches and exact-mask memoization by an exact
partition. The original proposer, gain ranking, false-clause ordering, radius
and node allowance remain fixed. Available variables exclude the new keep set,
so subsequent clause choices can change. These are stronger states, not equal
units of computation; both complete costs and operation categories are measured.

The implementation retains one source occurrence index and current satisfaction
counts. Flip/undo touches only incident clauses. Keeping a variable changes its
future admissibility but not its present Boolean value. An explicit DFS stack
shares the source and unaffected clause counts across branches without retaining
all visited flip masks. Optional exclusion recording stores the explored proof.
No source index is imported as trusted state after an edit or cold restart.

An independent exclusion checker recomputes false clauses at each `(M,K)` state,
checks disjoint available-variable packings, and verifies every child prescribed
by a complete, nonrepeating branch order. Both masks are part of certificate
identity. Dropping a keep constraint, omitting a child, repeating an ordered
variable or overlapping the masks is rejected. Children add a flipped variable,
so induction is acyclic. The root requires both masks empty. A complete exclusion
proves no model in that ball; only a full-support radius establishes global
UNSAT. Budget exhaustion has no negative authority. Positive authority is still
an ordinary complete model checked against every original clause.

This is ordinary exhaustive case partitioning, not a new polynomial SAT
algorithm. Arbitrary flip/keep contexts have up to three states per variable;
removing overlap does not bound the number of required contexts polynomially.
It also does not establish uniform dominance over a different branch ordering.

## Matched repair-kernel measurements

Four fresh-process pairs alternate mode order. Each arm receives the same 32
raw CNFs, without publisher labels or planted witnesses. The independent audit
uses the retained planted witnesses only to validate truth. Initial JSON parsing,
proposal construction, normalization, occurrence indexing, discovery/internal
checks, explicit model checks, writes, compression, warm reload and two cold
reload/checks are charged. Each replay reloads sources and certificates; no
search state survives between phases. OS caches are not flushed. Imports, final
metadata, semantic audits and the auxiliary distance diagnosis are additional.

| Measurement | Overlapping repair | Disjoint partition |
|---|---:|---:|
| Certified SAT sources | 22 | 29 |
| Budget-exhausted sources | 10 | 3 |
| Explored states | 274,481 | 118,552 |
| Mean complete seconds | 4.05347 | 2.56805 |
| Acquisition/internal checks | 3.99505 | 2.50607 |
| Explicit checks | 0.01013 | 0.01099 |
| Warm replay | 0.01347 | 0.01430 |
| Two cold replays | 0.02731 | 0.02890 |
| JSON certificate bytes | 37,061 | 49,362 |
| Gzip certificate bytes | 4,184 | 5,547 |
| Maximum observed RSS bytes | 31,162,368 | 29,147,136 |

Mean complete cost falls **36.65%**. Paired reductions are **36.20%, 37.27%,
35.10% and 38.01%**. The baseline still leaves ten sources unanswered and the
new method leaves three; this is not complete-solving cost or a comparison with
fresh CDCL. Storage and checking/replay increase because seven additional full
models are retained. Total append-only research storage also includes old
certificates and supplementary proofs, not just these trial-byte figures.

Generated branch edges fall 282,392 → 119,341 and incident updates fall
7,814,357 → 3,243,218. False-clause literal charges fall 10,830,261 → 5,694,279,
and gain occurrences 3,924,656 → 1,640,059. Baseline memoization records 7,154
hits. These are distinct operation categories; neither equal caps nor their
sum is a complete instruction count. Input and occurrence construction remain
charged in both arms.

## A smaller checked exclusion and a retained regression

For the previous random external source and its unchanged seed, the complete
radius-25 exclusion shrinks **35,065 → 4,307 states**. The new proof has 3,225
splits, 695 blocked leaves and 387 packing leaves. JSON falls **2,408,673 →
432,642 bytes**, and gzip falls **272,571 → 56,512 bytes**. A distance-26 model
is found in 2,076 states, reconfirming the same minimum repair distance of 26.
Both new searches fit the 20,000-state cap; the older radius-25 diagnosis used
an explicit 100,000-state allowance. The old proof remains intact.

New proof construction takes 0.08271 seconds and two reload/checks take 0.01720
and 0.01635 seconds. These are supplementary measurements, outside matched
panel timing. The model at distance 26 proves existence; the checked radius-25
exclusion proves minimality for this seed only.

A post-hoc small adversarial search retains a **six-variable, twenty-clause**
SAT counterexample: baseline finds a model in **9 states**, while the new order
needs **13**. At an illustrative cap of nine, baseline answers SAT and the new
search remains unknown. This demonstrates non-dominance; it never changes the
frozen panel policy. Both complete models and the exact source are retained.

## Verification and next gaps

Independent truth tables validate **25,534 ball queries over 5,108 inputs**:
all 512 two-variable CNFs with every seed, 3,304 three-variable CNFs with at most
three distinct clauses, 1,000 newly seeded random small sources, 228 retained
SAT domain misses, and 64 fresh signed/edited/mixed sources. All **12,485 SAT
balls and 13,049 exclusions** agree with truth. A one-state cap produces 2,839
explicit unknown attempts. All 39 fresh SAT witnesses survive a satisfied
addition and fail a contradictory addition. Checker calls disable discovery.
A repeated audit reproduces all semantic records exactly.

Twenty-three focused tests cover malformed seeds, masks and branch orders,
sparse signed names, empty sources, duplicates and tautologies, exact small
balls, missing branches, overlapping packings, changed sources and required keep
contexts. The old external 37/37 union is cold-checked again. Every earlier
scientific source, artifact and proof block is preserved.

All three remaining panel cases have 80 variables and 349 clauses (density
rounded from 4.36). The searches reach rejected assignments with **one, one and
five false clauses**, respectively. A trace-only copy retains each strictly
improving model and both context masks; final outputs and counters exactly match
the timed runs, and original/canonical violated-clause indices are independently
checked. These models are not SAT certificates and no resumable frontier is
claimed. Their contexts and violated clauses supply concrete targets for small
conditional interfaces, guarded reuse and better residual descriptions before
increasing a budget. Full-portfolio status on this constructed panel remains
unmeasured. Unseen external transfer, economical recognition, compact negative
proof reuse and unrestricted expansion bounds remain open.

All **2,528 full and 23 focused tests pass**. Validation reproduces all eight
comparisons and cold counters, preserves 244 prior manifests, 82,078 artifact
entries, 1,331 earlier scientific sources and 84 earlier proof blocks, and
rechecks the external union. Five scientific sources and one proof are added;
existing unclosed-SQLite warnings remain recorded.

Resume `experiments/results/cnf-partition-repair/checkpoint.json`, key
`partition_repair`.
