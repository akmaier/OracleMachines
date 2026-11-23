# Reusing canonical clause structure in whole-clause probes

The preceding study found that many failed probes repeated preparation before
ordinary search. This experiment isolates one such cost: the general normalizer
revalidates and sorts literals that already belong to a checked canonical parent.
The specialization is optional and produces exactly the same search decisions
and proof bytes as the preceding whole-clause lookahead policy.

## Invariant and scope

Deleting satisfied clauses and falsified literals preserves strict literal order,
literal uniqueness and absence of tautologies within every surviving clause.
Signed rank renaming is strictly increasing, so it also preserves that order.
However, restriction can merge or reorder different clauses, and variables can
disappear. The specialized preparation therefore still deduplicates the clause
collection, collects and compacts support, sorts the resulting clauses and
serializes the complete canonical key. Empty-clause collapse remains exact.

`experiments/cnf_ordered_probe.py` uses this fact only when preparing a probe from
an already canonical expansion node with the scanning restriction used in the
workers. It is not an external-input normalizer or a contract for arbitrary
replacement restriction engines. External input validation, checked-cache lookup,
unit propagation and native certificate verification are unchanged. A cached
negative cofactor remains available even when unit propagation would miss.
No persistent memo, new proof rule or new default is introduced.

Tests compare preparation against the full normalizer on every two-variable CNF,
random wider formulas, support gaps, sparse labels, duplicate/reordered clauses
and empty collapse. End-to-end truth checks and independent cold readers retain
the full source obligations. The experiment checks exact proof payload equality,
not just matching SAT/UNSAT answers.

## Frozen comparison

The previous holdout becomes the exposed set: 72 base/edit/repeat queries at
generator sizes 84/108. A new 72-query holdout uses sizes 90/114 and seed
202611232056. Its 48 distinct canonical roots are absent from the parent archive.
All workers start empty; prior answers do not seed search. Family labels organize
analysis but never select solver actions. Four alternating serial repetitions
compare the current binary policy, whole-clause lookahead, and lookahead with
specialized preparation, each with the same 256-dispatch limit.

| Mean or retained measure | Exposed lookahead | Exposed ordered preparation | Fresh lookahead | Fresh ordered preparation |
|---|---:|---:|---:|---:|
| Solve seconds | 6.0636 | 6.0293 | 14.5789 | 13.9175 |
| Complete-worker seconds | 11.9634 | 12.0171 | 27.3997 | 26.7094 |
| Native expansion dispatches | 2,142 | 2,142 | 4,456 | 4,456 |
| Native key + payload bytes | 22,362,613 | 22,362,613 | 55,295,075 | 55,295,075 |
| Selected retained Python bytes | 98,725,860 | 98,725,860 | 235,327,604 | 235,327,604 |

Fresh-input solve mean improves **4.54%**, with all four pairs faster; complete
worker improves **2.52%**, also in all four pairs. On exposed inputs the solve
mean improves only **0.57%** and complete-worker mean regresses **0.45%**. The
first exposed pair regresses substantially; retain it rather than removing it
after seeing the result. This is a bounded local saving with mixed generalization.

General-normalizer visits fall by 839,311 exposed literals and 2,051,816 fresh
literals, across 1,308 and 2,506 preparations. This is not that many total literal
visits eliminated: specialized support collection and remapping each still visit
839,257 and 2,051,680 literals, respectively. Restriction, key construction,
lookup, propagation, checking and publication remain charged. In chronological
profiles, normalization calls fall 978 to 841 on exposed case 1 and 857 to 704
on fresh case 37; propagation calls stay 350 and 349. Profile times include
instrumentation overhead and are excluded from comparative means.

Retained native/extension payloads, checked objects and SQLite content are
identical between lookahead and ordered preparation. Selected Python graph size
does not include transient/native allocations; process RSS remains separately
reported. Worker time includes setup, querying, warm reuse, cold audit,
reconstruction and compression, while study preparation and cumulative auditing
are separate. The dispatch cap excludes probe publication and is neither a
wall-time nor a memory bound.

## The larger remaining gap is discovery

On the fresh stream the original binary policy completes 38/48 distinct roots,
against 39/48 for both lookahead policies. Their query-attempt counts are
27 SAT / 30 UNSAT / 15 unresolved versus 27 / 31 / 14. The additional refutation
is shared-mixture edit case 70, completed in 249 dispatches. Ordered preparation
adds no coverage beyond the preceding lookahead algorithm.

Even after the preparation saving, fresh solve time is **20.20% higher** than
the original binary policy and native payload **12.83% larger**. All twelve
random-three queries still exhaust the cap, accounting for eight distinct
unresolved roots. The earlier memory reduction was workload-specific; lookahead
can also grow the stored negative prefixes. Do not promote it as a universal
speed or memory improvement.

A source-derived diagnostic identifies a more useful next target. Unresolved
case 43 has **112 actual variables**, **111 extracted affine equations of rank
108**, and **61 leftover clauses**. All 108 variables in the affine subsystem
are fixed by its consistent full-rank equations. Four other variables remain
free, so its complete affine solution space has only **16 assignments**.
The generator size is 114; do not confuse that parameter with the actual support.
The eight random-three roots have no extracted direct affine equations.

The current top-level affine probe only publishes contradictory Gaussian rows.
It ignores consistent affine spaces coupled to leftover clauses. Existing
`cnf_affine_completion.py` already constructs and checks small complete solution
spaces, and `cnf_affine_negative.py` already verifies exhaustion certificates
with at most eight free coordinates. The next investigation should connect that
existing machinery to whole-input acquisition for case 43, with all 61 clauses
checked, positive models verified on the full source and negative exhaustion
published only through the existing separate authority. No new proof rule is
needed merely to try this integration. Use fresh validation cases and charge
the recognition cost on the eight no-equation controls.

The diagnostic in this checkpoint verifies extraction and rank only; it neither
enumerates those 16 assignments nor supplies a SAT/UNSAT verdict. Small affine
dimension is a restricted condition. The unresolved random-three roots and
uniformly efficient acquisition of arbitrary CNFs remain open.

## Reproduction

Resume `experiments/results/cnf-ordered-probe/checkpoint.json`. Matching compare,
validate, profile and finalize scripts live under `experiments/`; the frontier
inspector saves the checked affine descriptions. Raw trials preserve all stopped
prefixes and alternate payloads, and the cumulative archive preserves all earlier
authority. Development test failures are retained: counters reset per query, and
a cached affine extension is not automatically a native cached negative. The
corrected tests accumulate work across queries and construct a native certificate.

Validation: 1,628 tests pass, including 37 focused tests without warnings. The
full suite retains 44 existing SQLite resource warnings. Both readers check
1,728 query records, all retained prefixes and 342 prior partition records. The
cumulative archive contains 89,134 native and 90 affine certificates, preserving
all earlier authority and 13,461 prior artifacts. The sealed source inventory
has 872 fingerprints. The manuscript builds without warnings and preserves its
64 existing proof environments.
