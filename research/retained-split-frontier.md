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

## Continuing after the learned-clause/split comparison

`continue_cnf_reuse_frontier.py` carries the same bounded continuation policy
forward from `experiments/results/cnf-learning-split/report.json`. It preserves
all six inherited external splits, 42 learned bases and 155 augmented blocks.
Inherited temporary reconstruction files are isolated from the new delta export.
The new checkpoint lineage supports subsequent passes with `--parent`, without
changing any fingerprinted historical implementation or report.

```sh
python3 -m unittest solver.test_cnf_exhaustion_certificate solver.test_cnf_probe_exhaustion solver.test_cnf_split_frontier solver.test_cnf_target_probe > /tmp/cnf-reuse-frontier-tests.log 2>&1
python3 experiments/continue_cnf_reuse_frontier.py /tmp/cnf-reuse-frontier-reproduction
python3 experiments/diagnose_cnf_reuse_frontier.py /tmp/cnf-reuse-frontier-reproduction/report.json /tmp/cnf-reuse-frontier-reproduction/obstruction.json
python3 experiments/compare_cnf_exhaustion_replay.py compare /tmp/cnf-reuse-frontier-reproduction/report.json /tmp/cnf-reuse-frontier-reproduction/obstruction.json /tmp/cnf-reuse-frontier-reproduction/replay-comparison.json
python3 experiments/validate_cnf_reuse_frontier.py /tmp/cnf-reuse-frontier-reproduction --test-log /tmp/cnf-reuse-frontier-tests.log
```

The seventeen targeted regression tests exercise the unchanged frontier and probe
mechanisms, the no-unit-trigger argument and compact certificate rejection cases.
Full inventory auditing and standalone cold replay validate the new
checkpoint, its inherited evidence, exact new rows, coverage and reference proofs.
The parent retains the earlier 589-test full-suite result; it is not counted as a
new full-suite run here. Report recognition-state counts separately from proof
storage, preparation, delta export and reconstruction costs. The repeated 83-case
development workload is not an independent holdout.

## The 19-variable obstruction and cheaper replay, 13 November 2026

The continuation makes four advances on one source: clear blocks at offsets
**0, 4 and 8**, followed by exhaustion. It probes the ten remaining candidates,
adds **no recognition nodes** and leaves structural coverage at **55/83**, also
without the growth exception. The leaf remains **19 variables / 84 clauses**.
There are no pending children or binding budget stops. Saved splits and closed
siblings remain available.

The old four candidate pairs and ten new pairs provide **28 clear traces** for
all fourteen binary variables. The other variables, **1, 2, 10, 11 and 16**, occur
only in clauses of width at least three, so neither assignment creates an initial
unit or empty clause. This certifies that no assignment of a single source
variable produces a unit-propagation refutation. None of the retained pairs gives
the implemented common-value or equivalence rewrite. Neither statement decides
SAT/UNSAT or excludes stronger inference.

Acquisition costs **0.00870 s**, navigation **0.00731 s** and composition/diagnosis
**0.12424 s**. The successful continuation pipeline costs **271.54 s**, including
**66.54 s** preparation, **113.33 s** full inventory audit and **64.40 s** cold
route reconstruction. Delta preservation/export alone costs **5.40 s**. These
single-run timings concern a bounded continuation, not a faster SAT solver.

The working database grows **28,672 bytes** to **769,646,592 bytes**. Its 41,710
pattern nodes are unchanged; the added window and two ordinary continuations
bring their totals to **87** and **128**. The delta occupies 94,208 bytes,
compressed to **2,424 bytes**. All eight inherited tables retain their previous
rows unchanged. The 1,775-node reference archive is byte-identical to its parent;
no new reference answer was needed. External evidence still includes all six
splits, 42 learned bases and 155 augmented blocks. Peak RAM is unmeasured.
The unchanged reference archive is still copied into this checkpoint, adding
883,411 compressed file bytes without new proof nodes. A checked reference to
the existing immutable archive could avoid that duplication in later exporters;
the working-database growth alone is not total retained artifact growth.

### A certificate with only the dependencies of the negative fact

`cnf_exhaustion_certificate` retains the exact formula and exactly two clear
traces per binary variable. Its checker verifies the formula binding, unit
reasons, nonconflicting fixed points and complete binary-variable coverage; the
no-unit-trigger argument accounts for the remaining variables. It does not load
the inventory. Duplicate source traces and unrelated acquisition records are
unnecessary for this assertion. The retained bundle is **6,562 JSON bytes** or
**1,347 compressed bytes**, including the source key and formula binding.

The certificate applies only to the explicit source. Clause edits, conditioning
and variable transport require a new binding and checked evidence. In particular,
an exhausted parent does not imply an exhausted child. A test accepts the eight
ternary clauses that forbid all three-variable assignments: these are UNSAT but
have no single-assignment unit trigger. Thus this certificate cannot be treated
as a SAT answer, a complete structural exclusion, or a general hardness claim.

Two fresh processes per mode, with execution order reversed, compare identical
retained proofs. History reconstruction plus checking costs **14.20055 s** and
**14.10469 s**. Compact replay costs **0.12492 s** and **0.08218 s**. These wall
times include Python startup, imports and teardown; OS caches are not flushed.
The compact check itself takes about 0.0028 s. Packing/checking the portable proof
costs **0.00288 s** after source traces are available; the exporting diagnostic
also pays **14.03 s** to reconstruct its history and totals **14.64 s**. The
earlier probe acquisition and all retained storage remain charged.

This saving is confined to replaying the unit-refutation obstruction. Compact
replay does not audit ancestry, original-level coverage, paired rewrites or the
entire inventory, and it does not discard or compress that inventory into 1,347
bytes. The baseline deliberately reconstructs the retained proof from history;
this is not a comparison with every possible lightweight extraction method.
Fresh-process measurements and proof identities are retained in
`replay-comparison.json`.

All **17 targeted tests** pass (0.413 s). Full inventory audit and independent
cold replay pass; cold replay takes **154.19 s**, checks the compact proof against
the actual restored source and both replay modes, disables discovery, and leaves
database bytes unchanged. The manuscript now describes the narrow certificate
and resource comparison. No new Lean refinement or unrestricted-SAT result is
asserted; Lean files are unchanged.

### Next gap and resumption

Resume `experiments/results/cnf-reuse-frontier/report.json` with
`continue_cnf_reuse_frontier.restore_checkpoint` and `routes_for`. Do not repeat
ordinary probing on the unchanged 19-variable source. Compare a source-proved
clause augmentation with another split from its fourteen saved pairs. Transport
of earlier parent lemmas is another candidate, but the saved route includes
elimination and binary-path steps: surviving-variable bindings and projection
conditions must be checked before any inherited clause is admitted. An exhausted
parent's negative certificate cannot supply that transport proof.

The alternative queue still has **18 ready bases / 92 ranked variables**. The
larger cost gap is dependency-local checking for positive routes and complete
coverage plans; the small negative certificate demonstrates a restricted case,
not a solution of the 113-second whole-inventory audit. Preserve full dependency
and invalidation obligations when extending it.
