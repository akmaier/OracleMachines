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
python3 experiments/validate_cnf_split_frontier.py /tmp/cnf-split-frontier-reproduction --test-log /tmp/cnf-split-frontier-tests.log
```

The initial parent is `experiments/results/cnf-split-batch/report.json`.
`continue_cnf_split_frontier.restore_checkpoint` supports a chain of subsequent
passes via `--parent`, returning rewrites, learned bases, augmented blocks and
all inherited split records. Construct routes with `compare_cnf_split_batch.routes_for`.
Preserve the explicit pending queue if no acquired leaf remains; this pass does
not acquire missing cofactor roots or silently switch to other learning queues.

Results follow after the measured run and independent cold replay. This is a
finite continuation experiment, not a new tractable SAT category or a uniform
polynomial bound for arbitrary CNFs. The existing manuscript and Lean statements
are unchanged.
