# Exact cofactor sharing for deeper feedback

Date: 27 November 2026. Parent checkpoint: `ea7f5b48`.
Evidence: `experiments/results/cnf-feedback-cofactor-dag/`.

## Coverage result and controls

Two additional conditioning levels close **five of the six** exposed fresh-panel
UNSAT gaps. The unchanged feedback leaf routine runs on each normalized source
residual. Each parent refutation requires both children; one open child leaves
the parent unresolved. The existing fallback still solves every input, and no
feedback outcome is treated as a SAT certificate.

A separately frozen second panel has 24 inputs: 14 SAT and 10 UNSAT. Feedback
without extra conditioning refutes 2/10 UNSAT inputs; depth-two conditioning
refutes 6/10. This second-panel result needs an explicit control distinction:
the full clause cubes of widths 4, 5 and 6 also appear in the analytic/unit-test
controls. Widths 4 and 5 are exactly equal after normalization to earlier inputs.
They are not novel held-out structures. Excluding all three full-cube controls,
the remaining seven UNSAT cases improve **2/7 to 4/7**. All input descriptions
and exhaustive truth labels remain withheld from the solving workflows. These
are generated transfer cases, not a representative external SAT benchmark.

The combined 30-case experiment contains sixteen UNSAT cases: the new method
certifies eleven, versus two with the old depth-zero leaf method. Five remain
open to this bounded rule: two differently presented twelve-edge parity cases,
a fifteen-edge parity case, the width-six cube and the largest bridge mixture.
The old 246-snapshot frontier and earlier fresh-panel results remain unchanged.

## What is reused, and why it is exact

`cnf_feedback_cofactor_dag.py` shares a result when both the exact normalized CNF
and remaining conditioning depth are equal. Normalization sorts and deduplicates
clauses/literals, removes tautologies and compacts sorted variable names. It does
not recognize general isomorphism, polarity symmetry or semantic equivalence.
All lookup and normalization work is charged, including probes that miss.

Memoization is local to one discovery call with immutable search limits. It
retains both refuted and unresolved results at that exact remaining depth.
Different depths do not reuse open outcomes. A later call with larger bounds
starts new discovery; this experiment does not implement persistent discovery
resume. Native certificate reuse is persistent and separate. A context is reduced
against the source before normalization, so shared children denote the same
residual relation even when reached through different assignments. Native split
verification checks both exact restrictions again.

The serialized certificate uses postorder node indices. Every child index must
decrease, its CNF must equal the appropriate normalized restriction, and its
remaining depth must decrease by one. All nodes must be reachable. Each feedback
leaf is checked against its own CNF; a limit leaf is unresolved. Validation checks
canonical bindings, depth, state count and proof status. Inner search-limit
metadata does not by itself prove historical work usage: the experiment audit
replays discovery and compares the exact histories and counters. No open or
budget-exhausted state has negative authority.

Internal split certificates omit the preceding unsuccessful feedback history:
the two child certificates suffice to justify the split. Complete discovery
histories remain in the separate diagnostic logs. All incoming certificate nodes
are validated before a warm root hit. Native construction uses the existing
source compiler at leaves, shares one direct-unit shortcut allowance across the
whole root, and emits ordinary native split records. The allowance does not
bound total graph construction, verification, normalization or recursion.

## Restricted invariant: a chain hidden inside a full clause tree

Let `C_n` contain all `2^n` clauses selecting one signed occurrence of each of
`n` variables. Either setting of any variable gives the same normalized `C_(n-1)`.
The feedback leaf routine refutes `C_3` when its constant-size search completes,
but stalls on `C_m` for `m >= 4`: after its outer condition and a single probe,
all remaining clauses still have width at least two, so no new unit arises.

For `n >= 3`, conditioning limit `D`, and `d = min(D, n-3)`, with enough state
budget for the tree, discovery without memoization calls the feedback routine
`2^(d+1)-1` times. Exact cofactor memoization calls it only `d+1` times. Both
refute exactly when `D >= n-3`. The recurrence follows from two identical
children at every level; the memo key also has identical remaining depth.
Tests and the independent audit cover widths three through six at depth two.

This is a restricted call-count result. `C_n` already has `n*2^n` literal
occurrences in its explicit input. Reading, canonicalizing, checking and retaining
that input are not free. The recurrence is not a general SAT runtime bound or an
exponential speedup measured against input length. The parity and mixture cases
retain different residuals, showing where the same recognition rule does not
collapse a tree.

## Matched costs

Four cyclic process orders compare fresh solving, depth-zero feedback, depth-two
conditioning without discovery memoization, and the same conditioning with
memoization. All start with an empty archive and use the same case order and
fallback. Native sharing between cases is enabled in every mode. The three
feedback modes acquire their evidence online, write complete diagnostic histories,
validate the certificates, repeat queries warm, replay both cold authority
readers, and compress the archive. Interpreter startup, report-metadata writing
and the final lineage audit are additional. Fresh uses its existing 256-node
limit; the feedback modes have a 64-state conditioning ceiling and fixed inner
limits. More coverage than depth zero also spends more conditioning work.

| Workflow | Discover (s) | Solve/check (s) | Warm (s) | Both cold readers (s) | Complete (s) | Certificate bytes | Diagnostic bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fresh | 0.00000 | 0.03361 | 0.00733 | 0.02865 | 0.08160 | 0 | 0 |
| Depth zero | 0.60533 | 0.10498 | 0.07401 | 0.02837 | 0.85712 | 339,988 | 2,810,921 |
| Depth two, tree | 1.69649 | 0.19416 | 0.10886 | 0.03738 | 2.13136 | 467,561 | 7,728,917 |
| Depth two, shared cofactors | 1.62914 | 0.17378 | 0.09778 | 0.03709 | 2.02774 | 398,988 | 7,398,513 |

History persistence costs 0.03113, 0.07528 and 0.07066 s for flat, tree and memo respectively; archive persistence costs 0.00728, 0.00715, 0.01237 and 0.01240 s in the table order. These phases and input loading are included in complete times.

**Memoization saves 4.86% complete time**, with paired savings of 2.30–6.98% across the four orders. It reduces feedback calls/retained states **170 → 147**, records 17 memo hits, cuts certificate bytes **14.67%**, diagnostic bytes **4.27%**, and warm time **10.18%**. The twelve cases with observed reuse save **12.40% discovery time** (0.50989 → 0.44666 s); eighteen without reuse change only 1.18660 → 1.18248 s. This is conditional on actual repeated exact residuals.

Tree and memo have the same native graph: **168 records, 104,798 raw bytes and 21,858 compressed bytes**. Fresh has **70 records, 63,806 raw bytes and 14,722 compressed bytes**. Depth zero has 77 records, 66,257 raw bytes and 15,056 compressed bytes. Peak process RSS is 52,068,352 bytes fresh, 57,327,616 flat, 76,906,496 tree and 77,086,720 memo. Thus neither native graph size nor peak RSS improves through this discovery memoization.

The memoized online workflow still costs **24.85 times fresh solving**. Discovery is about 80% of its cost. The gain relative to the equally deep tree must not be reported as a gain over fresh or depth-zero solving; the coverage gain also spends more work.


No production default is changed. In particular, a smaller discovery DAG is not
a smaller native archive here: the native solver was already sharing exact
residuals. Neither shorter certificates nor saved feedback calls establishes a
process-RSS reduction. All older archives, unmatched controls and full diagnostic
searches remain retained on disk.

## Remaining priorities

The five unresolved inputs are preserved in the new `remaining.json`, together
with their exact bounded certificates. Prefer reusable **non-unit relations** on
the parity cases before merely increasing conditioning depth again. Compare
existing exact affine/clause recognition and mixed-CNF boundary descriptions,
including recognition, conversion and verification costs. The wider cube and
bridge are useful limits for the fixed-depth policy, not evidence that every
problem admits a compact cofactor chain.

Discovery dominates the full conditioned workflow. Within its unchanged feedback
leaf routine, the preceding profile identifies repeated checking and normalization
as significant costs. Reuse of owned checked seed/index data is supporting work,
with exact invalidation and complete cold verification. Any new representation
must be tested on another reserved panel with duplicate/control strata explicit.
Uniform coverage, economical recognition, compact composition and polynomial
acquisition/expansion bounds remain open for unrestricted SAT.
