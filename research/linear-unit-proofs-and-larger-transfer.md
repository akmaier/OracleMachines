# Implicit proof contexts and larger external transfer

This checkpoint separates two questions: whether the previous search transfers
to larger unseen inputs, and whether its existing refutations can be retained
and checked more cheaply. The search, seed proposer, order and 20,000-context
cap remain unchanged. Only the negative-proof representation and checker change.

## Exact representation and shared checking state

The prior proof records every node under a pair of integer masks describing its
flip and keep commitments. The new format stores nodes in preorder. A leaf is
`[unit_clause_indices, conflict_clause]`; a split is
`[unit_clause_indices, split_clause, ordered_variables]`. The root starts with
no commitments. Its source unit clauses determine forced values, and the split
order determines each child: keep earlier variables, flip the selected one.
The child arity tells the checker how many subtrees to consume.

A partial-assignment undo trail reconstructs contexts without storing or parsing
mask strings. Units and conflicts are checked against source clauses; every
split must name exactly all available variables of a false proposal clause.
All expected subtrees must occur, and no extra record may remain. Different
children retain incompatible commitments, so a complete explicit proof has an
unambiguous preorder encoding. Conversely a successfully checked stream expands
to the same kind of full-root refutation. A new manuscript proposition records
this equivalence. This is an encoding and checking improvement, not a new SAT
search algorithm or a new tractable class.

The conversion is untrusted until checked. It runs **after the unchanged search**
and charges source preparation, unit scans, context traversal and copying.
Both old and new representations coexist during packing. The independent
checker does not invoke packing, search or the old checker. SAT models and
unknown results retain their original obligations; partial trees never become
UNSAT certificates. Proof size and search may still be exponential.

## Matched costs on the exposed 36-input panel

Four fresh-process pairs alternate mode order. Both arms reproduce all eighteen
SAT models, all eighteen UNSAT answers and exactly the same 58,118 entered
contexts. The candidate's 42,333 stored refutation nodes correspond exactly to
the old nodes, regardless of dictionary insertion order. This comparison
isolates representation/checking effects on the same completed workload.

| Quantity | Explicit contexts | Preorder contexts |
| --- | ---: | ---: |
| Mean complete seconds | 12.73310 | 12.48055 |
| Acquisition including internal checks, seconds | 9.27654 | 9.51494 |
| Explicit checking, seconds | 0.64881 | 0.54562 |
| Warm reload/check, seconds | 0.72641 | 0.62710 |
| Two cold reload/checks, seconds | 1.44707 | 1.23281 |
| Model/refutation JSON bytes | 19,226,027 | 15,859,412 |
| Combined gzip bytes | 1,754,249 | 830,927 |
| Maximum observed RSS bytes | 108,396,544 | 76,546,048 |

Packing increases acquisition/internal-check time, while cheaper checks and
persistence lower complete cost by **1.98%**. Paired improvements are 2.50%,
3.52%, 1.02% and 0.92%. Combined gzip shrinks **52.63%**, and maximum observed
RSS falls **29.38%**. The total improvement is modest; it is not a
modern-solver speedup. Larger storage and replay reductions are specific to this
proof corpus and format, not a bound on arbitrary refutations.

Timing includes input JSON/DIMACS reads and hashes, preparation, search,
conversion, internal and explicit checks, proof and sidecar writes, three
compressions, warm replay and two cold source/proof reloads. No search state
survives replay; OS caches are not flushed. Imports/startup, reporting metadata,
downloads, independent audits and historical append-only storage are additional.
There are no production-default changes.

## Frozen larger-input transfer

Before acquisition, selection fixes zero-based lexicographic member indices
20 and 40 in four [SATLIB archives](https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html):
`uf125-538`, `uuf125-538`, `uf150-645` and `uuf150-645`. This gives eight originals.
Each group's first original also supplies one deterministic sparse signed
permutation and one edit removing its first clause and reversing a literal in
its last nonempty clause. The eight controls remain related inputs; edited
truth is not inherited. Discovery receives clauses alone.

The search and encoding source hashes are frozen before downloading these
contents. Exact normalized comparison finds no duplicates or matches against
the preceding 36-input transfer panel, original external 37, constructed 32 or
synthetic 182. This does not assert all-history semantic novelty, representative
sampling or independent controls. Publisher member bytes are retained exactly
in gzip; workflow DIMACS is re-emitted with normalized whitespace and verified
parsed equality. No tar archive paths are extracted.

Both proof formats certify **3/8 originals and 2/8 controls**, all SAT, with
identical models, outcomes and 236,197 entered contexts. Eleven cases reach the
20,000-context cap. No complete negative proof is obtained, so the new packing
path is not exercised on this sample. The separate single pair takes 47.66420
versus 47.83883 seconds; it supplies no larger-input speedup evidence. Proof JSON
is 20,071 versus 19,991 bytes, combined gzip 925 versus 919 bytes, and maximum
observed RSS 43,188,224 versus 44,646,400 bytes. These small byte differences
come from format tags, not packed refutations.

Separate isolated reference processes return **0/16 checked answers** for the
unchanged full portfolio and **8 SAT + 8 UNSAT** for Z3 5.4.1. Each Z3 SAT model
is checked against the source. Its UNSAT outputs remain trusted reference
claims, not project refutations. Process totals are 57.70698 and 1.72154 seconds,
respectively, without the matched persistence/replay workload; no speedup ratio
is inferred. Neither reference reaches its outer timeout. Labels agree where
applicable, and edited truth is assessed separately.

The new structural union remains **5/16**, leaving **three known-SAT and eight
reference-UNSAT cases**. The known-SAT misses are the first 150-variable SAT
original l004 and its signed and edited controls l012/l013. The remaining eight
are all selected UNSAT originals and their controls. Every unresolved input is
connected. Visited maximum commitment counts are 120--122 of 125 variables and
143--146 of 150; smallest observed false-clause counts are 1--9. These are policy
diagnostics, not minimum-width, minimum-repair or impossibility proofs. The
original source and checked reference models remain available for follow-up.
The prior completed 36-input panel and older unions remain unchanged and separate.

## Validation and remaining gaps

All **2,592 full and 20 focused tests pass**. A reproduced independent truth audit
checks **8,882 queries**, comprising 6,173 SAT and 2,709 UNSAT, and rejects all
2,709 truncated refutations. It covers all two-variable CNFs with all seeds,
three-variable CNFs with at most three clauses with two seeds, and the retained
128 sparse signed edited sources. Tests include empty sources/clauses, sparse
names, duplicate/tautological clauses, a 1,500-variable implication contradiction,
reordered dictionaries, missing/trailing children, invalid unit premises,
incomplete split orders and changed sources. Checking runs with discovery,
packing and the old checker disabled. Four eligible signed models transport
back to independently checked original-source witnesses.

Validation reproduces all eight exposed-panel workflows and both larger-panel
workflows, their counters and replay checks. It reproduces the unchanged search
against the preceding checkpoint, preserves **248 prior manifests, 83,640
artifact entries, 1,351 scientific sources and 87 proof blocks**, rechecks the
old external union, and validates publisher-byte and normalized-source equality.
Six new scientific files bring the source ledger to 1,357; the manuscript adds
one proof of representation equivalence.

The largest coverage gap is now the explicit larger-input residual: three SAT
cases and eight reference-UNSAT cases. Investigate shared conditional structure
and reusable negative consequences before simply increasing the cap. The format
change removes redundant context storage, but does not yet reuse logical
subproofs across different contexts or edits. Safe source-index transport,
guarded learned exclusions and component conditioning remain promising next
steps. Efficient recognition, preprocessing, compact general proofs and
unrestricted SAT expansion remain open. Finite coverage and exact recomposition
do not imply polynomial-time solution of every CNF class.

Resume `experiments/results/cnf-linear-unit-proof/checkpoint.json`, key
`linear_unit_proof`. The frozen selection, original member gzip files, old and
new proof formats, matched trials, source-bound checks and separate reference
results remain available in that directory and its `larger` subdirectory.
