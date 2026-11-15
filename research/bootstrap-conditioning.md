# Broader conditioning candidates and the cost of checking them

Updated 2026-11-16. This is a supplemental experiment on the same 24 inputs as
[the lookahead study](lookahead-bank.md), following its finding that 22 selected
depth-zero residuals offered no binary-based source pairs. It is adaptive
development evidence, not a fresh holdout.

## Exact expansion without a binary-clause prerequisite

The optional `experiments/cnf_bootstrap_conditioning.py` can select any occurring
variable of a checked source. For each Boolean value, it restricts the source,
acquires and checks a unit-propagation trace, and records the canonical child and
its variable transport. Both traces are persisted before further recognition.
The existing shortest-clause/balanced-occurrence heuristic supplies at most four
variables. All 24 selected components now have candidates, including those with
no binary clauses. No frozen inference module or default policy is changed.

The semantic obligation is ordinary conditioning:

\[
 F\equiv(\neg x\land F[x=0])\lor(x\land F[x=1]).
\]

Unit closure preserves each branch's models together with its recorded forced
assignment. The checker reconstructs each restriction and closure, verifies the
canonical child binding, and requires strictly smaller variable support. A
positive coverage rule requires independently justified plans for both children.
A stored pair, a present child, or an exhausted allowance does not by itself
establish coverage. Conflicting branches are valid obligations and must reach
checked contradiction leaves. Model lifting verifies the transported assignment
against the source. This construction offers exact recursive decomposition for
any finite CNF; it does not bound the number of resulting branches polynomially.

## Matched workflows and explicit costs

The common policy permits depth one, with probe/learning limits 4 and clause
growth limit 2. Preparation initially runs each input at remaining depth zero,
creating 85 patterns with 85 admissions and 168 probes in 0.76235 seconds, including
archiving. Policy keys include maximum depth, so this seed is rebuilt and charged
instead of relabelling the earlier depth-zero archive.

Each query has 40 distinct recognition admissions. The three external-split arms
also acquire at most four source pairs/eight assumption closures, separately from
that recognition limit. Their propagation, checking, serialization and SQL costs
are included in elapsed time and separately counted. This is not an equal total
operation budget. The ordinary arm restarts the entire original at depth one;
external splits retain depth-zero ancestors and expand one selected unresolved
component. Therefore this compares workflows, not only variable rankings.

Two repetitions reverse arm order and produce identical semantic graphs within
each arm. Times below are means for all 24 warm queries. Each arm additionally
spends 0.264--0.273 seconds restoring and checking the common seed. The common
preparation, cold replay and compression are recorded separately.

| Workflow | Covered originals | New patterns | Admissions | Fresh probes | Explicit source assumptions | Saved pairs | Query seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ordinary depth one | 4/24 | 737 | 775 | 5,699 | 0* | 0 | 6.13657 |
| First candidate | 2/24 | 165 | 165 | 1,137 | 48 | 24 | 1.39313 |
| Smallest unit-closed cofactors | 2/24 | 173 | 173 | 1,181 | 192 | 96 | 2.51594 |
| Enumerate up to four | 5/24 | 558 | 558 | 3,946 | 172 | 86 | 7.41975 |

*Zero means no separately persisted bootstrap assumption traces. Ordinary
conditioning's internal assumptions and unit propagation remain charged in its
planner and elapsed time; they are not absent.

First and enumeration acquire candidates lazily. Size ranking acquires all four
pairs before choosing one. Enumeration stops when the original has coverage or
the four choices are exhausted, sharing one recognition allowance across choices.
Seven ordinary queries and one enumeration query hit that allowance. Neither
single-choice arm is capped, but their unused allowances do not establish that
their selected pair can close the source. Closed originals, using zero-based
case indices, are ordinary `{1,2,3,9}`, first `{1,3}`, size `{2,3}`, and enumeration
`{1,2,3,4,9}`. Later queries do not increase these sets.

Enumeration avoids 1,753 probes and 179 new patterns relative to ordinary depth
one, while taking about 20.9% longer. First selection is cheaper but covers fewer
inputs. Size ranking spends more preparation than first selection and covers the
same number, with a different success set. These results support neither a
universal best selector nor a blanket runtime improvement.

| Workflow | Working SQLite bytes | Compressed archive bytes |
|---|---:|---:|
| Ordinary depth one | 14,835,712 | 700,767 |
| First candidate | 4,558,848 | 237,457 |
| Smallest unit-closed cofactors | 6,037,504 | 298,376 |
| Enumerate up to four | 12,156,928 | 629,031 |

These are retained database sizes, including the seed and external pair table
where applicable, not peak process memory. Input normalization, preparation,
recognition, route verification, complete row-preservation audits and persistence
all remain relevant. No peak-RAM or large-scale asymptotic claim is made.

## Measured next bottleneck: repeated split verification

A separate instrumented enumeration run reproduces the graph, coverage and work
counters. During querying it calls the split verifier **3,913 times for 86 distinct
records**, including **3,827 repetitions**. Cold replay performs another 263 calls
for those same 86 records. Profiling overhead excludes this run from the timing
means; overlapping cumulative function times must not be added.

The query count is explained exactly by the implementation. After each of 86
pairs, `routes_for` rebuilds the route catalog and checks every earlier pair:

\[
\sum_{j=1}^{86}j+2\cdot86=3,741+172=3,913.
\]

The additional two checks per pair occur when acquiring its record and acquiring
its child patterns. The sum is quadratic in the number of tried pairs; actual
runtime also depends on source and trace sizes. This is avoidable maintenance
work, not an intrinsic SAT lower bound.

The next target is an incremental registry of checked split records. Bind it to
the exact source, full policy and immutable record contents. Check each new record
once, retain pending child obligations in a reverse index, and activate its route
when both children become available. Existing coverage must then be updated, not
replaced by stale closure flags. Reopening or changed evidence requires checking
again. Do not cache by object identity or waive the cold proof checker. Compare
against this frozen enumeration baseline before changing candidate selection.

After removing that avoidable cost, investigate the 19 uncovered originals:
deeper interactions, alternative unresolved components, and selectors that predict
propagation or component exposure. Four candidates on one frontier are only a
bounded discovery policy, not a partition into uniformly tractable SAT classes.

## Persistent checkpoint and validation

`experiments/results/cnf-bootstrap-conditioning/checkpoint.json` preserves the
union of all alternatives: **85 old + 1,069 new = 1,154 patterns**, 96 split records,
and 17 missing child obligations. Across the four workflows, 564 acquired pattern
rows overlap. Union coverage remains **5/24**; pooling alternatives gives no
additional original closure. The checked positive proof contains 68 steps. The
union database occupies **21,790,720 bytes**, compressed to **1,055,418 bytes**;
split keys and payloads occupy **1,298,089 logical UTF-8 bytes** within it.

Restore with `experiments.validate_cnf_bootstrap.restore_checkpoint`. This helper
binds the code, policy, exact original query catalog, source roots, positive proof,
pending obligations and archive hashes. It verifies all patterns and pair records
without fresh acquisition. The seed, eight comparison histories, one diagnostic
history and the union pass cold checks. All **335 inherited and new tests pass**,
including exhaustive two-variable fibers, lifted models, missing polarity,
foreign bindings and acquisition-free cold reuse.

The initial validator reused the seed archive's filename for the union. Final
readback detected the collision. The seed was reproduced with **identical original
database and gzip hashes**, and the corrected validator writes the union to its
own directory. Original seed metadata and all measured reports are unchanged.
The failed validator, first report and recovery evidence are retained under
`validation-recovery/`; they are not valid restoration entry points.

The protocol binds 267 sources, extending the inherited ledger to loaded local
experiment dependencies and the test fixture. The final checkpoint binds 269,
including the profiler and validator. All 175 previously bound sources and 3,023
prior artifacts remain unchanged. The manuscript's 64 existing proof blocks are
preserved. No new Lean refinement, SAT/UNSAT verdict, arbitrary-SAT efficiency
bound, or P-versus-NP result is claimed.
