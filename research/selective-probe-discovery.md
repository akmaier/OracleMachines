# Selective continuation after a capped probe search

Checkpoint: 27 November 2026. The residual-bucket pipeline now continues capped
failed-literal acquisition only after a charged bucket attempt remains unresolved.
It certifies **105/110** frozen queries, versus **97/110** with the previous policy
and **103/110** with uniformly doubled probing. All eight gains retain whole-root
source-checked authority; none of the baseline verdicts is lost. The common fresh
fallback already answers all 110 queries. Production defaults remain unchanged.

This integrates the existing [checked-prefix](probe-continuation.md) and
[cursor](probe-cursor.md) ideas into the current bucket path. It does not introduce
a new tractable SAT family. The narrower cursor reuse ablation avoids repeated
work but has **no measured total-runtime win** on this panel.

## Policy, exact identity and proof

`experiments/cnf_selective_probes.py` supplies four experimental modes:

- **Base:** the preceding relation pipeline with 128 probes per incoming edge.
- **Eager:** the same engine with 256 probes before its single relation tail.
- **Restart:** initial 128 probes, the existing relation tail, a bucket gate, then
  at most 128 additional probes if acquisition was capped and the gate is unknown.
  Rebuild an index and repeat a completed clear prefix before continuing it.
- **Resume:** the identical selective schedule, retaining the index and offset
  for that exact unchanged CNF instead of repeating the clear prefix.

The selective modes do not run another relation tail after continuation. Their
order of applying consequences, renormalizing, substituting and choosing later
probes can differ from eager. A coverage difference therefore measures the full
selective schedule, not merely a larger budget or cursor reuse.

Only a truncated round with **no failed assumption** saves a cursor. It binds the
full normalized CNF tuple, literal order, offset and occurrence index within one
incoming visit. A consequence round restricts and renormalizes the source, so its
old index is discarded. An intervening relation transform also invalidates a
changed-source cursor. There is no cross-formula or persisted index authority.
A frozen cursor container does not expose the underlying index for mutation in
this pipeline; propagation only reads its occurrence tuples.

A repeated clear prefix would add no failed literal on an unchanged source.
Skipping it preserves the remaining acquisition questions. Every later failure
still requires an independently checked clause trace showing that its assumption
conflicts. Its opposite is a consequence; adjoining consequences, checked unit
restriction and inverse renaming preserve satisfiability and lift witnesses.
Cold replay checks those facts and the downstream bucket/conditioning proof.
**No cursor, successful probe or heuristic exhaustion claim certifies SAT.**
A successful child lifts a SAT witness; UNSAT at a split requires both children.
Exact residual/depth pairs may share a node, retaining incoming maps separately.

The original and eager controls translate exactly to the previous certificates.
Restart and resume proofs are identical modulo the mode field. The checker
rejects changed sources, malformed continuations, false conflict claims, missing
unit transport and invented cursor fields. It does not need to verify that the
selection heuristic made a good search decision.

## Bounded resources and measured costs

Initial and continuation allowances share at most eight accepted probe rounds.
Depth two permits at most seven incoming edges: at most **1,792 budgeted probe
attempts per root** for eager/selective, versus 896 base. Restart may additionally
repeat at most 896 clear probes per root. Propagation operations are not bounded
by the attempt count alone. Binary, unit, recognition and bucket allowances remain
separate; unsuccessful gates and changed-source rebuilds are charged. No global
wall-time guarantee, fixed point or unrestricted polynomial bound follows.

Five cyclic process orders start empty, use the same fallback, and charge input,
discovery with its internal check, explicit checking, evidence/database writes,
warm/cold replay and compression. Startup, protocol construction, labels,
historical acquisition, lineage validation and post-hoc diagnostics are extra.
Both native cold readers audit fallback archives. The two JSON replay passes
use the same checker, not independent implementations.

| Policy | Structural queries | Complete seconds | Compressed SQLite + JSON bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: |
| Fresh | 0/110 | 4.07538 | 988,298 | 160,481,280 |
| Base 128 | 97/110 | 6.18505 | 566,548 | 123,469,824 |
| Eager 256 | 103/110 | 5.50747 | 398,753 | 103,743,488 |
| Selective restart | 105/110 | 5.32977 | 354,570 | 98,402,304 |
| Selective resume | 105/110 | 5.36356 | 354,530 | 95,485,952 |

Resume is **13.28% cheaper than base** and **2.61% cheaper than eager**, with all
five paired signs favorable. It remains **31.61% more costly than fresh**. Against
restart it is **0.63% slower**, with all five paired signs unfavorable. Discovery
alone falls slightly, 1.59322 to 1.59018 seconds; cold/replay variation outweighs
that small difference. This is a retained negative result for the narrow reuse
hypothesis, not evidence that avoiding probes universally slows execution.
Selective restart is the cheapest structural control here; use it as the cost
reference for subsequent experiments and retain resume as an ablation.

Selective acquisition performs 47 gates and 3,516 continuation probes, retaining
44 rounds, 234 checked failures and 298 unit steps in 45,579 compact bytes.
Twenty cursors avoid **710 repeated probes and 20 index builds**; three cursors
are invalidated after a source change. Budgeted attempts total 23,074 base,
26,342 eager and 26,026 selective, with an additional 710 repeated attempts in
restart. Index builds are 472, 505, 531 and 511 respectively for base, eager,
restart and resume. These are acquisition counts over unique prepared programs;
subsequent checking is separately counted and timed.

Nodes fall 297 to 287 and splits 115 to 110 versus base; retained bucket steps
increase 917 to 972. Shared targets remain 28, with 23 distinct-raw merges, all
constant. **No broader nonconstant sharing is demonstrated.** Compressed JSON
falls only 213,301 to 211,009 bytes versus base; most package savings come from
fallback records falling 669 to 264. Restart/resume's 40 compressed bytes differ
because their mode strings differ, not because their proof structure compresses.
Diagnostics add 469,751 bytes. RSS values are process observations, not bounds.

The largest measured resume costs are **cold replay 1.73346 s** and **discovery
1.59018 s**, which includes internal checking. Solve/explicit checking costs
0.94340 s, warm replay 0.73561 s, archive persistence 0.29182 s and evidence writes
0.05686 s. Exact reuse of validated normalization/intermediate state within one
replay remains the leading cost opportunity; avoiding a few clear probes does
not address most of the remaining expense.

## Frozen coverage and the next unresolved pattern

The panel contains the previous 76 queries, six exposed frontier inputs, 24 new
unlabelled constructions and four exact normalized repeats. New inputs include
random three-CNFs at 32, 40 and 48 variables; nonfolding failed-literal/alias
mixtures with a deleted-direction control; and parity prisms. New exact sources
do not duplicate the previous 76-query panel. Families recur, so these are
synthetic controls, not evidence of representative external or arbitrary SAT.
There are 69 SAT and 41 UNSAT queries; labels and descriptions are audit-only.

| Cohort | Base | Eager | Selective |
| --- | ---: | ---: | ---: |
| Previous queries | 76/76 | 76/76 | 76/76 |
| Exposed frontier | 2/6 | 5/6 | 6/6 |
| New unique inputs | 17/24 | 19/24 | 20/24 |
| New repeats | 2/4 | 3/4 | 3/4 |

The four unique remaining sources are `j09` (48 variables, SAT), `j07` and `j06`
(40 variables, SAT), and `j11` (48 variables, UNSAT). `j09r` repeats the first.
Their seven unknown leaves have widths 9–12, six failing before any bucket
elimination. They have no units, disconnected components, binary conflicts,
forced binary literals or signed-equivalence block, and are neither Horn nor
dual-Horn. All **598** possible single-literal probes finish without a conflict;
none is truncated. Merely raising this allowance on the same leaves has no
remaining failed-literal opportunity.

**Next coverage target:** test stronger joint binary consequences, drawing on
[existing checked binary-consequence work](joint-binary-consequences.md), within
this residual pipeline. First compare their acquisition and exact recomposition
with bounded ordering/width or further conditioning controls. A two-assumption
conflict may justify a binary clause even when neither assumption alone fails;
whether enough useful clauses can be acquired cheaply here is still unmeasured.
The remaining cases are not proved hard. All unrestricted discovery, compact
representation, recomposition and total-cost obligations remain open.

## Validation and continuation

All **2,338 full tests and 62 focused tests pass**. Fifteen new tests cover every
two-variable CNF, wider random inputs with tiny quotas, exact legacy/restart
translation, changed sources/orders, sparse signed models, corrupted evidence,
clear-probe unknown results, gate reuse and cold checking with discovery disabled.
An additional 60-test relation-focused suite also passes. The full suite retains
pre-existing SQLite ResourceWarnings. An initial test used a
small-case exhaustive oracle on large frontier cases and was interrupted; its
log and the overlapping, excluded benchmark attempt are preserved. The corrected
tests use the existing independent DPLL oracle above eight variables. Frozen
inputs and search policy were unchanged.

The audit reconstructs certificates in all 25 measured reports, checks witnesses and oracle
answers, decodes JSON bundles, reopens native database archives and preserves
**233 prior manifests, 46,700 artifact entries, 1,278 scientific source files and
75 prior proof blocks**. Five new scientific sources and one appended proof are
added. The manuscript is compiled and its new pages rendered for inspection.
Resume `experiments/results/cnf-selective-probes/checkpoint.json`, key
`selective_probes`; `analysis.json` retains paired costs and all regressions,
`remaining.json` the five unresolved queries, and the two remaining-leaf profiles
the exact diagnostic evidence. No previous scientific file or experiment is
rewritten to obtain this result.
