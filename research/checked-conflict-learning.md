# Checked conflict learning and guarded negative knowledge

The final development policy closes all eleven retained larger-input gaps:
**5/16 → 16/16**, with eight source-checked SAT models and eight independently
checked resolution refutations. All eight originals and eight related controls
finish within 20,000 entered contexts; the largest uses 15,900. This is development
on an exposed panel, not new external transfer. No production defaults change.

## Exact exclusions reusable across contexts

The new kernel implements standard first-UIP conflict analysis, clause learning,
nonchronological backjumping, conflict-based variable activity, phase saving and
binary decisions. The prior kernel uses unit propagation and disjoint first-flip
branching. This is a bundled CDCL-style policy change, not an isolated learning
ablation or a new SAT algorithm/tractability theorem.

Every propagated value has a reason clause. On conflict, resolution eliminates
recent implied variables until only one literal belongs to the current decision
level. At the root, resolution instead continues to the empty clause. Each
retained record gives a starting clause, ordered pivot/parent pairs and the exact
claimed resulting clause. References may name only source clauses and earlier
learned clauses. The independent checker reconstructs each resolvent and compares
it with the claim. It does not run search or trust assignment reasons, activity,
backjump levels or mutable occurrence counts.

A learned clause is globally implied by the source. If its width is k, it excludes
the partial assignment falsifying its k literals, regardless of the other
variables. Such forbidden regions can overlap; conjunction with all learned
clauses leaves the source's model set exactly unchanged. They are reusable
constraints, not a disjoint family classification. After a first-UIP backjump,
all but one learned literal remain false and the other becomes free, so unit
propagation can force it. A source-checked full model grants SAT authority; only
a checked empty-clause derivation grants UNSAT. A capped run can retain useful
checked clauses while remaining unknown.

Discovery shares occurrence lists, full-proposal and partial-assignment counts,
reason/level information and an undo trail. Activity changes branching priority;
saved phases survive undo. All activity scans, clause indexing, unit work,
resolution, restoration and proof construction are charged. No restarts or clause
deletion are implemented. The finite source and proof checks do not supply a
polynomial bound on search, learned clause count or certificate size.

## Guarded reuse after a source edit

`transport_knowledge` checks the old proof, canonicalizes the target and remaps
source/derived clause indices. Each referenced original clause must still occur
exactly in the target; duplicate guard lookups are cached. Unreferenced original
clauses may be deleted. Every claimed learned clause is retained unchanged and
rechecked against the target. No fresh search occurs. A global refutation may
retain UNSAT authority; SAT outcomes transport only their negative knowledge and
become unknown. Added constraints can invalidate the old model.

The audit appends a shared-variable binary bridge and a fresh negative unit to
each of the sixteen sources. It reuses all sixteen knowledge sets, retaining
UNSAT for the eight refuted inputs and unknown for the other eight. Removing an
actually required source premise is rejected in every case. This is exact
same-variable premise reuse, not arbitrary semantic equivalence, renamed-source
recognition or unconstrained transfer. Recognition, source checking and proof
remapping are charged separately from fresh acquisition.

Across all retained learned clauses, width has median 14 and maximum 36.
However, each complete knowledge set references **90.23–100% of its source's
canonical clauses** (492–644 distinct premises, depending on the input). This
measures the whole retained set, not the minimum support of an individual
clause. Small exclusions therefore do not imply a small transport guard. The
current operation rejects the collection if any required premise disappears;
extracting and retaining the still-valid subset is a concrete next reuse gap.

## Measured coverage and costs

Two fresh-process alternating pairs compare the unchanged unit/preorder kernel
with the frozen learner. Both cap entered contexts at 20,000, although work per
context differs. Policy development and labels remain outside the measured
workflow. The baseline retains **5 SAT, 11 unknown**; the candidate retains
**8 SAT, 8 UNSAT**. Originals contribute 4 SAT and 4 UNSAT; signed and edited
controls each contribute 2 SAT and 2 UNSAT.

| Measured panel quantity | Unit/preorder baseline | Checked learning |
| --- | ---: | ---: |
| Entered contexts | 236,197 | 111,957 |
| Mean complete seconds | 47.52141 | 287.12925 |
| Mean acquisition including internal checks, seconds | 47.39490 | 271.00598 |
| Mean explicit checking, seconds | 0.01021 | 2.69844 |
| Mean warm reload/check, seconds | 0.03380 | 3.07490 |
| Mean two cold reload/checks, seconds | 0.05644 | 6.22661 |
| Mean writes, seconds | 0.00582 | 0.28182 |
| Mean three compressions, seconds | 0.00070 | 3.82129 |
| Proof JSON bytes | 20,023 | 93,048,057 |
| Combined gzip bytes | 922 | 2,879,747 |
| Maximum observed process RSS bytes | 43,515,904 | 302,465,024 |

Mean complete time rises **504.21% (6.04 times)**; paired increases are 504.70%
and 503.73%. Input reads/hashes, proposer/index creation, activity and undo work,
resolution, internal/explicit checks, writes, compression and replay are charged.
Imports/startup, reporting metadata and independent audits are additional. Cold
replay discards search state, but operating-system caches are not flushed.

The candidate retains **51,477 learned clauses**, produced by **1,372,091
resolution steps**, with **78,745 learned-clause propagations** and **6,481
nonchronological jumps**. Assignment occurrence updates rise **76,856,480 →
613,846,635** as the active index grows. These counters explain why fewer
contexts do not establish a speedup. The workflows complete different work:
eight additional refutations are obtained, and the candidate also preserves
learned derivations for SAT outcomes. Full knowledge retention is deliberate,
but its cost is substantial; answer-only or pruned-proof costs are unmeasured.

The initial fixed-branch learning probe and activity-based probe are retained
with their exact source bytes. The fixed-branch probe leaves several larger
cases unknown. Activity is not universally cheaper: original l001 takes 381
entered contexts in that initial probe versus 7,489 in the final policy. The
initial probe recorded its live source binding at completion after revision;
its actual executed bytes were archived before revision. The provenance record
corrects this mapping while preserving the late-bound raw field verbatim.
Large probe JSON files are stored losslessly as gzip, with uncompressed hashes.

## Validation and remaining obligations

All **2,618 full and 26 focused tests pass**. The reproduced truth audit checks
**8,882 queries** (6,225 SAT, 2,657 UNSAT): every two-variable clause set with
every seed, three-variable CNFs with at most three distinct clauses with two
seeds, and 128 fresh sparse signed mixtures with duplicate and tautological
clauses. It checks **1,911 learned clauses against source models**, with 2,591
satisfying-extension checks; these are cumulative checks, not distinct models.
All **853 bounded unknown outcomes** retain unknown authority.

Independent checking and transport are exercised with search disabled, including
changed premises, pivots, forward references, claims and conclusions; partial
knowledge; absent guards; unused source-clause deletion; sparse names; and a
1,500-variable implication contradiction. The prior 36-input and 32 constructed
panels receive checked answers in separate audits. All matched certificates,
search counters and reload checks are reproduced; old external 37/37 answers
are independently rechecked.

Validation preserves **249 prior manifests, 84,115 artifact entries, 1,357
scientific sources and all 88 prior manuscript proof blocks**. Five new
scientific files bring the ledger to 1,362, with one new proof of checked
exclusions and source-premise transport. Earlier 36/36, external 37/37,
constructed 32/32 and synthetic 182/182 panels remain separately denominated.
Initial and final development evidence, including the initial source-binding
correction, remain available. Existing SQLite ResourceWarnings are retained in
the full-suite log.

The next coverage obligation is genuinely new frozen transfer after this policy
change. The main reuse questions are how much learned knowledge survives useful
edits, whether necessary proof fragments can be retained more economically, and
how much source support each reusable exclusion really requires. Compact literal
width is not compact acquisition or a small source guard. Efficient recognition,
preprocessing and unrestricted expansion remain open. Exact recomposition and
finite panel completion do not prove polynomial-time SAT.

Resume `experiments/results/cnf-resolution-learning/checkpoint.json`, key
`resolution_learning`. Old panels, proof formats, counterexamples and cumulative
records remain separate and unchanged.
