# Reusing saved paired traces

The resumed probe windows retain unit-propagation traces, including clear
attempts. Their acquisition policy stops at failed literals; it does not apply
the original recognizer's common-consequence and equivalence rules to every
later pair. This study checks that unused evidence before requesting further
assumptions. The parent is `cnf-probe-resumption/report.json` with 45 of the 83
reused development originals covered.

## Exact rule and proof obligation

Fix the complete source CNF F and a variable x. Independently check the saved
unit reasons under x=false and x=true. Every reason must refer to the restricted
source's clause order, and each clear trace must end at a consistent unit fixed
point. Neither a stored success label nor a ranking cursor establishes an
implication. Only top-level original-source attempts are eligible: the nested
continuation of `learning_clear` refers to an augmented formula.

If both traces derive a literal l, every model of F satisfies l, since it must
have one of the two values of x. Restriction by these common literals, followed
by checked unit closure, preserves exactly the remaining model fibers. If one
trace derives l and the other derives its negation, their signs establish that
its variable equals x or its negation. A signed star mapping substitutes every
occurrence in every source clause, including clauses outside the reasons used
to prove the relation. The smallest member is the representative.

For an equivalence block, each source model obeys the mapping and restricts to
a target model. Conversely, extending a target model by the mapping satisfies
every original clause, because the target was obtained by that exact
substitution. Normalization retains the original-to-child variable transport.
The checker requires strict support reduction and recomputes that exact edge.
The model-lift checker validates the child model, applies the transport and
mapping, and checks the complete source once more.

The two traces are stored by reference, with their exact source, table, row and
top-level attempt indices. The checker replays the reasons even if the source
window was already read. Prefix completeness is unnecessary for this logical
rule: a valid pair proves the implication regardless of how it was selected.
Full route replay still checks the older window and continuation policies.

## Persistence and limits

The rewrite artifact is written before target recognition. A missing child is
a pending target; it cannot supply a coverage route. Recognition has a 32-state
admission limit per rewritten source. Completed descendants and the pending
rewrite survive independently. The finite coverage witness requires a complete
child plan, preserving the existing component and conditioning obligations.
It is evidence of structural coverage, not by itself a SAT answer.

`experiments/cnf_trace_reuse.py` implements the rule. The experiment exports an
additive delta in the existing eight-table format and a separate compressed
rewrite artifact; every old row is checked for preservation. Resume using
`restore_checkpoint` in `experiments/compare_cnf_trace_reuse.py` and pass its
returned rewrite records to `TraceRoutes`. Using only the parent probe runner
would omit these additional routes. The independent validator reconstructs
both artifacts, checks plans and source bindings without new discovery, and
replays separately retained SAT reference proofs.

Deriving an equivalence from the selected saved pair requires no new assumption
closure. It still pays reference lookup, decoding, source checking, two trace
checks, literal intersections, complete substitution and canonicalization.
For a source with L literal occurrences and traces of total size T, direct
restriction and reconstruction scan O(L) occurrences per attempt in addition
to reason checking; normalization and history lookup remain separate costs.
Scanning K retained attempts consequently still pays their verification work.
The current scanner also rereads the window index per source and decodes
referenced rows per attempt; it does not claim an optimal discovery index.

Target recognition, persistence and full cold history replay are additional
costs. Target recognition may perform new probes even though deriving the
paired rewrite does not. Reference proofs and the fresh microbenchmark control
also acquire computations and are reported separately. Explicit reference keys
have storage cost, and the scan preserves unsuccessful sources as diagnostic
data. Avoided trace duplication does not imply lower total archive size or RAM.
In the current encoding a row identity embeds the source key, so even two
references occupy space proportional to that key's encoding, rather than two
constant-size numeric IDs. The 32-state cap likewise bounds admitted state
count, not the literal size of each state or all resident history.

These are established logical reductions applied to previously unused evidence.
They do not give a polynomial construction for arbitrary CNF, guarantee small
equivalence classes, or resolve the exponential worst case of general search.
The implementation is checked in Python and is not a new Lean theorem.

The next low-discovery candidate is a binary implication graph built from the
checked source reasons. Each conditional unit gives an entailed binary clause,
including its contrapositive edge. Mutual paths can establish additional signed
equivalences; a path from a literal to its negation establishes a forced value,
and contradictory strongly connected literals refute the source. Those graph
conclusions would need retained path witnesses and exact source bindings before
becoming rewrites. If they do not suffice, adding the checked clauses may still
strengthen propagation through the remaining nonbinary clauses. This is a
proposed next experiment, not an implemented result or a complete SAT procedure.

## Measured result, 13 November 2026

The complete saved-pair scan checks **1,240 attempts on 41 sources** in
**0.52728 seconds**, including source validation, lookup, pair intersections and
the bounded binary-learning opportunity scan. It finds no common-value pair and
one equivalence, x27=x5, on the 37-variable residual of case 58 (`fresh3`, n48,
original 1340). Substitution leaves 36 variables. Target recognition takes
**0.04364 seconds**, adds five nodes and acquires **42 probe attempts**; no
admission cap binds and no target is pending. The target remains structurally
open. Original coverage stays **45/83**, including the growth-exception ablation.
The independent 49-node reference archive proves the residual UNSAT, without
promoting that fallback proof into the structural-coverage count.

The scan retains 284 candidate binary clauses across 39 sources, capped at 16
per source. **161 candidates on 37 sources use later-window evidence**; the
other 123 use initial-profile evidence and are not all new learning opportunities.
Four sources hit the cap. The five previously certified exhausted sources have
candidate counts 0, 10, 10, 3 and 0 for cases 0, 2, 73, 27 and 51 respectively.
These clauses have not been added to their sources in this experiment.

The chosen-pair microbenchmark runs 100 repetitions in each mode, five times
with alternating order. Median saved-reference replay/substitution is
**0.06768 s**, versus **0.11823 s** with fresh discovery and checking of the same
pair, about 1.75 times faster for this substep. Both modes know the chosen pair;
selection, preparation, persistence and target recognition are excluded. The
fresh control acquires 1,000 assumption closures in total, separate from target
recognition and from deriving the retained rewrite.

Archive restoration takes 4.73060 s, preparation 65.75355 s, full cold inventory
109.07921 s and separate cold route checking 62.85051 s. The measured pipeline
before final report writing is **257.49563 s**, excluding the subsequent standalone
validator, test suite and exploratory development. Reference solving takes
0.05668 s and reference replay 0.01925 s. No end-to-end solver speedup is claimed.

SQLite grows from 766,676,992 to 766,763,008 bytes (**86,016 bytes**), preserving
all old rows and adding five pattern nodes. The additive delta occupies 143,360
SQLite bytes / 5,818 compressed bytes; the rewrite record occupies 11,932 JSON
bytes / 1,957 compressed bytes. The complete unsuccessful/successful opportunity
log adds 4,090,411 JSON bytes / 73,273 compressed bytes. Reference proofs occupy
385,024 SQLite bytes / 23,047 compressed bytes. The unchanged coverage witness
is also retained. These separate artifact sizes must not be mistaken for RAM.

All **561 Python tests** pass, including exhaustive small model fibers, exact
source-reference checks, tampered witnesses/reasons/bindings, pending-child
restart and model transport. Cold reconstruction independently replays the scan,
rewrite, finite coverage and reference proofs with new discovery disabled and
unchanged database bytes. Manuscript and Lean sources are unchanged. Artifacts:
[cnf-trace-reuse](../experiments/results/cnf-trace-reuse/README.md).
