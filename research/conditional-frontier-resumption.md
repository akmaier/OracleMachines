# Conditional Horn progress and interrupted recognition

The continuation resumes the exact variable-5 split retained for original
1062. Both repeats use the existing scheduler and selective pattern activation,
on independent copies of the same checked history. Each has twelve advances
and one shared allowance of 32 distinct newly entered states. This is a
structural-coverage experiment, not a comparison with a different solver.

## Structural result

The pending **32/136/405** true cofactor now takes **11 new states** to reach a
**17/26/62** formula recognized as both Horn and zero-valid. The path contains
eight probe nodes, one binary-path reduction, one polarity transformation and
one family node. These are checked, source-bound transformations. The existing
false **32/124/375** cofactor needs no new admissions and still leads to the
unresolved **31/122/370** residual. The split activates, but its source remains
structurally open because both branches remain obligations.

The next advance splits that 31-variable residual on local variable **2**.
Its false **29/110/329** cofactor takes eight states: two probe nodes, two
binary-path reductions and three elimination nodes lead to an unresolved
**24/88/274** leaf. The true **29/115/343** cofactor enters thirteen states
before the shared cap stops recursive acquisition. None of those thirteen
states has a stored pattern certificate. Their exact inputs are retained in
the operation record; the independent analysis lists their shapes separately
from certified edges. Shapes alone do not certify a reduction path.

Thus each repeat enters **32 states**, stores **19**, and leaves **13 entered
but unstored**. The union adds the same nineteen patterns and one split. The
new Horn endpoint is a newly acquired formula, not an old terminal reused by
identity. What recurs across recent branches is the reduction pattern:
conditioning, forced-value probing, binary consequences and polarity changes
can expose Horn structure. Predicting this outcome before paying discovery
cost remains open. No small Horn backdoor in the original coordinates follows
merely from these local-variable traces.

Coverage stays **66/83**, including when growth exceptions are disabled. The
retained frontier has **four open split records / two acquired leaves / one
pending target**. Its acquired leaves are **24/88/274** and the earlier
**36/144/434** plan. A SAT answer for a cofactor is distinct from certification
of this complete structural decomposition.

## Costs and retained space

The two identical-policy repeats have the following mean costs:

| Phase | Seconds |
|---|---:|
| Worker preparation | 8.06032 |
| Selection | 0.09339 |
| Acquisition, including interrupted work | 0.13225 |
| Route maintenance | 0.02355 |
| Focus coverage | 0.00086 |
| Complete expansion | 0.25005 |
| Delta export | 4.85783 |
| Complete worker | 13.25993 |

The live index grows **697 -> 698 routes**. Arrival of the old missing target
activates one existing route. The newly selected split remains pending; the
index ends with one waiting route, target and link. Sidecar comparison reaches
**1,378,399 serialized bytes**. The index is additional memory, and these
counts do not measure peak RAM.

The full producer takes **209.79814 s**, including **92.09233 s** parent
restoration, **7.97754 s** final route preparation, **59.62660 s** global coverage
and **5.52626 s** union export. These costs remain charged. The current warm
worker spends roughly 97% of its time in preparation and export; preserving
interrupted recognition should therefore be evaluated against its added
checking, storage and replay cost, not assumed to be the largest runtime win.

History grows **253,952 bytes** to **776,065,024 bytes / 42,120 patterns**.
The union delta occupies **319,488 SQLite bytes / 14,220 compressed bytes**.
It contains ten probe nodes, three binary-path nodes, three elimination nodes,
one polarity node, one family node and one unresolved node. No external probe
rows are added. All previous reference nodes are retained; the reference
archive grows **3,734 -> 3,781 nodes**. The expanded positive certificate stays
at **3,360 steps**.

## Why repeated bounded retries need not progress

The current acquisition calls `_discover` before `_record_node`. A node is
stored only after recursive acquisition of the children needed by its
certificate. `AdmissionExhausted` unwinds the call stack; entered ancestor keys
are logged, but their partially computed recognition records are not retained.
This is the mechanism behind the thirteen unstored states in this checkpoint.

A conditional failure case follows directly from that control flow. Suppose
an unchanged history requires a deterministic unary path of **L** distinct,
unrecorded pattern states before any state can be stored. Assume every call
recurses to its next child before storing itself, with no other completed
branches. If a fresh admission allowance **B < L** is used on every retry,
acquisition raises before the deepest required state is entered. No call can
finish, so no row is added. The next retry starts from the same history and
repeats the same prefix. By induction over retries, no retry stores a node.
This is a limitation of this restart policy, not a SAT lower bound. The present
thirteen-state interruption does not establish that its full path exceeds a
fresh allowance of 32.

A resumable implementation needs a separate representation for checked local
transformations whose target is still pending. It must bind the source CNF,
configuration, depth, local certificate and target transport, retain any
branch obligations and candidate position, and reject mutation or mismatched
replay. Pending records must not enter the closed-pattern table or count as
complete coverage. A progress argument then needs a finite dependency measure
and fair resumption; compactness and polynomial bounds remain separate.
Increasing the allowance is another policy, but its additional cost must be
charged and it supplies no fixed-cost expansion guarantee.

## Next checkpoint and priorities

Resume `experiments/results/cnf-conditional-frontier/report.json` using
`continue_cnf_conditional_frontier.restore_checkpoint`, SHA-256
`f55bdcefe556222a5b6043f03591e38f10ad8c76bc3c3c73a8eb45aed73c0ef8`.
Retain all five evidence lists **(1, 42, 156, 45, 1)** and **two projection
bridges**, with the complete bridge-aware builder and positive verifier.

Resume the exact variable-2 pair of **31/122/370**, source SHA-256
`09831bee0e0295f91c4d21b79ffe25508d3dad8b48e5052b4bfde74367574914`.
Its missing true **29/115/343** target is
`944e1c80b727c779838a814ab6d1509ae46b22afbde7e978523bb96c8f0ce859`.
Reentry of the thirteen unstored keys must be charged again under the current
implementation. Preserve the acquired false cofactor and both open leaves.

For broader coverage, finish this pending target and inspect the remaining
24- and 36-variable interactions. For the largest total runtime saving,
measure how to reuse checked startup and export work: they dominate the
worker, and historical reconstruction is still more expensive. For reliable
bounded progress, evaluate local continuation records on repeated interruptions
and long unary paths, retaining both their overhead and failures. This run
changes neither the scheduler nor the pattern storage protocol and establishes
no new comparative speedup or unrestricted-SAT efficiency bound.

Independent cold reconstruction passes in **305.33218 s**, verifies all
**3,781 reference nodes**, and reproduces global coverage and the next
selection without fresh discovery or reference search. Both stepwise prefixes
match full catalogs, ordering and activation counts. All **222 tests** pass;
existing SQLite resource warnings remain visible in the log. The **161-page**
manuscript builds with no overfull boxes or undefined references, and all
**64 previous proof blocks** remain unchanged. The restart-policy argument is
textual; no new Lean theorem is claimed.

All **23 previous manifests / 1,107 artifacts** and all **3,734 previous
reference payloads** are unchanged. The new manifest binds **40 artifacts /
3,720,830 bytes**, including operation logs, deltas, reference evidence,
structural findings, cost summary, validation metadata and test/build logs.
See `experiments/results/cnf-conditional-frontier/validation.json` for exact
commands and source fingerprints.
