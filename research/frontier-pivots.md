# Moving pivot deviations toward unresolved leaves

The previous two schedules inspected only the first four open elimination
ancestors. They mostly returned to the same selected unresolved cores and gained
no coverage. This study isolates ancestor choice before increasing projection
growth or trying coupled deviations.

## Frozen comparison

Both modes restore the exact union of the two previous pivot histories, including
all failed trials. They keep the recognizer, opposing-pair cap 64, candidate cap
64, clause-growth cap 2, and interaction-first candidate ordering unchanged.
The **early** control uses the first four elimination ancestors in breadth-first
selected-plan order. The **frontier** mode visits the whole selected open graph,
computes each node's longest path to a selected open terminal, and takes the four
elimination nodes with smallest height. Breadth-first discovery order breaks
ties. All children of a component conjunction and both children of the selected
conditioning alternative participate; closed children do not extend open height.
Unselected conditioning alternatives remain available to final recomposition.

Each open original can acquire at most **eight new trial records**. The two modes
start from independent clones of the same merged seed. A prior trial is reused
only for its exact source key and pivot, with the source key already binding the
recognizer configuration and remaining depth. The saved projection, target map
and summary are checked before skipping it. A failed cached trial does not rule
out different continuations of its target. Candidate construction and ranking
still run, so this cache does not avoid all preparation. New records are shared
across later inputs within each mode.

This differs from the previous cap of eight attempts, which could repeat old
trials. Both current modes have the same new-trial allowance. Earlier timings
are therefore historical context, not a matched control for this experiment.
The data remain selected development inputs, not an untouched holdout.

## Exactness and resource obligations

Every new edge uses the existing complete opposing-pair reconstruction and trial
checker. Successful local replacements count only after whole-source
recomposition; all old closed results survive. The definition of structural
coverage and the ordinary SAT solver are unchanged. The previously checked
existential-projection identity supplies the reduction semantics; no new formal
refinement or efficient search theorem is claimed.

Frontier selection adds O(V+E+M log M) graph/container work and O(V+E) graph
scratch for V selected open nodes, E selected edges and M elimination ancestors.
Source loading/checking and identifier lengths are additional. The graph may
include many nodes even though at most four are selected. Candidate construction
has the earlier per-ancestor costs. Eight new entry targets still do not bound
their inherited recognizer descendants, full-process memory or total discovery
time. A budget on distinct acquired descendant states remains a separate gap.

All seed rows, including prior trials, must be unchanged. Each output is a delta
relative to the merged seed, containing only new rows in all four tables. Both
original deltas and the original base remain necessary for reconstruction.
Exports are rebuilt and compared by logical table digests, applied twice to
check idempotence, fully cold-audited, and separately replayed for trial binding
and whole-source coverage. Cold checks deliberately repeat some dependencies;
their costs are recorded separately. Independent endpoint solving/model lifting
is performed for any new closed replacement, and its proofs are preserved.

## Results

The schedules above are frozen before the matched run. Results and limitations
will be recorded here after validation.
