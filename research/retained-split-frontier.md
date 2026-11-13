# Continuing below a retained split

The saved cofactor comparison leaves one acquired open target whose selected
parent has 33 variables. A saved split already closes one branch; the other
contains a 27-variable, 101-clause leaf. Restarting the parent overlooks this
retained reduction and repeats a stream of ordinary probes already exhausted
there. The next expansion should start from the exact child identity.

## Checked frontier navigation

`cnf_split_frontier.frontier` checks every external split record and follows both
branch obligations, skipping already closed subgraphs. It follows selected
internal plans and saved ordinary forced continuations to their remaining leaves.
If a leaf itself has a saved external split, traversal descends again. Visited
identities are shared; active cycles are rejected. Missing cofactor children
remain explicit pending obligations with source, split, branch value and target.
They cannot disappear into a successful coverage claim.

Multiple splits on one source are alternative decompositions. This scheduling
view chooses the lexicographically first record identity. It does not claim a
minimum-cost plan, enumerate every learned alternative, or identify the cheapest
work needed to close an original. Structural composition and its checked proof
remain the authority for coverage. The view starts from saved split sources;
these need not all be necessary if another route already closes an original.

The bounded continuation selects the smallest acquired leaf by support, literal
count and canonical identity. It allows eight ordinary advances, four visited
sources and 32 distinct recognition admissions. Previously acquired child states,
parent splits and closed siblings remain reusable. Preparation, navigation,
checking, acquisition, persistence and cold replay are measured separately.
No admission count bounds total CPU, proof bytes or reference-solving work.

## Validation and resumption

Four tests use actual retained formula shapes to check replacement of the
33-variable parent by its 27-variable descendant, omission of the closed sibling,
duplicate sharing, nested pending obligations, deterministic traversal, closed
partitions and forged-edge rejection. The standalone validator disables new
recognition and probe acquisition, reconstructs the parent selection, checks
all new records and original-level coverage, verifies independent reference
answers and preserves previous proof rows.

```sh
python3 -m unittest discover -s solver > /tmp/cnf-split-frontier-tests.log 2>&1
python3 experiments/continue_cnf_split_frontier.py /tmp/cnf-split-frontier-reproduction
python3 experiments/diagnose_cnf_split_frontier.py /tmp/cnf-split-frontier-reproduction/report.json /tmp/cnf-split-frontier-reproduction/obstruction.json
python3 experiments/validate_cnf_split_frontier.py /tmp/cnf-split-frontier-reproduction --test-log /tmp/cnf-split-frontier-tests.log
```

The initial parent is `experiments/results/cnf-split-batch/report.json`.
`continue_cnf_split_frontier.restore_checkpoint` supports a chain of subsequent
passes via `--parent`, returning rewrites, learned bases, augmented blocks and
all inherited split records. Construct routes with `compare_cnf_split_batch.routes_for`.
Preserve the explicit pending queue if no acquired leaf remains; this pass does
not acquire missing cofactor roots or silently switch to other learning queues.

## Measured continuation, 13 November 2026

The pass reduces the remaining selected leaf from **27 variables / 101 clauses**
to **22 variables / 90 clauses**. It does **not** add an original-level closure:
coverage stays **55/83**, also without the growth exception. The same 83 inputs
remain adaptively reused development cases, regardless of their historical
`holdout` labels. No claim about the separate 902/985 study changes.

On the 27-variable source, offsets 0 and 4 are clear; offset 8 forces a value.
The pass then follows the exact acquired target. On the remaining 22-variable
leaf, offsets 0, 4, 8 and 12 are clear; the next advance reports exhaustion.
There are eight advances across two sources, **six clear blocks**, **one forced
block** and **six new recognition states**. No state or source cap binds; the
queue is exhausted on the eighth advance rather than truncated by the step cap.
No cofactor child is pending. The parent split and closed sibling are retained.

Navigation costs **0.00688 s**, continuation/recognition **0.06866 s** and final
composition/diagnosis **0.12094 s**. Shared preparation costs **64.68 s**, full
inventory audit **104.39 s**, and cold route reconstruction **63.60 s**. The
comparison pipeline totals **256.65 s**, including restoration, checking,
serialization, persistence and reference work. These are single-run measurements;
there is no matched competing policy or general runtime speedup claim.

Working SQLite grows **176,128 bytes** to **769,560,576 bytes**. It retains
**41,706 pattern nodes**, **86 ordinary windows**, **126 ordinary continuations**,
41 learning bases, 150 augmented blocks and all five external splits. The delta
adds six nodes, two windows and five continuations; it is 237,568 bytes compressed
to **11,423 bytes**. All previous eight-table rows remain unchanged.

The independent reference solver proves the forced source and its exact target
both **SAT**. That answer is separate from structural closure; it does not close
the remaining partition. All **1,721** earlier reference nodes survive in a
**1,750-node** archive (13,492,224 bytes, compressed to 877,787 bytes). Reference
and diagnostic archives add storage beyond working SQLite. Peak RAM remains
unmeasured. All **589 Python tests** pass (80.008 s). Separate standalone cold
replay takes **151.51 s** and checks selection, new nodes, all routes, reference
proofs and the obstruction
below with discovery disabled and reconstructed database bytes unchanged.

## Certified obstruction on the remaining leaf

The separate diagnostic reuses **38 distinct saved assumption traces**, covering
both values of all **19 variables occurring in binary clauses**. Every trace
ends at a nonconflicting unit fixed point. The other three source variables,
**1, 12 and 18**, occur only in clauses of width at least three. Assigning one
of them cannot create a unit or empty clause, so unit propagation cannot start.
Consequently **no assignment of a single source variable produces a
unit-propagation refutation of this exact 22-variable formula**.

The diagnostic also checks every retained opposite-polarity pair for the
implemented common-value and equivalence rewrites. None applies. It performs
no new assumption probing or recognition acquisition and leaves the history
unchanged. Restoration costs 11.21 s, local checking 0.01541 s, and the whole
separate diagnostic 11.80 s. The standalone validator independently rechecks
these facts from the saved traces and source clauses.

This obstruction does not decide SAT/UNSAT, exclude stronger inference or give
a lower bound for arbitrary SAT algorithms. In particular, an entailed clause
batch can change unit propagation without changing the model set. Conditioning
on another variable can also expose useful structure. No new Lean theorem or
unrestricted complexity result is claimed; manuscript and Lean are unchanged.

## Next target and resumption

Stop ordinary probing of the unchanged 22-variable source. Inspect unused
source-proved binary consequences for a new bounded learned batch, and compare
its predicted target cost with nested saved-cofactor splits. The 19 checked
pairs can supply the latter without fresh assumption discovery. Pair closure
alone is insufficient, as the common/equivalence checks above demonstrate. Keep
all preparation, checking and new children in the cost comparison.

The alternative queue still has **18 ready learned bases / 92 ranked variables**;
the other statuses are ten covered, nine exhausted, three initially successful
and one acquired open target. The open source and its exact split ancestry are
in `diagnostics.json.gz` under `after`; `obstruction.json` records the checked
inference limit. Resume `experiments/results/cnf-split-frontier/report.json`
through `continue_cnf_split_frontier.restore_checkpoint` and `routes_for`,
including all five inherited splits. The older batch checkpoint omits the new
27-to-22 reduction and the exhausted child stream.
