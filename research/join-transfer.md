# Saved nonterminal proofs transfer to new CNFs

2026-11-16. The four joins exposed by [case 10](progress-transfer.md) now have a
controlled cross-input test. Preloading their 39 new nodes and four split
certificates avoids **35 pattern acquisitions and 154 probes** on 24 previously
unseen roots. Both histories cover the same 24 constructed inputs and produce
identical query proofs. This demonstrates intermediate proof reuse beyond an
already cached root, but does not establish a large total runtime or memory gain.

## Construction and matched histories

For each saved anchor, split one clause `A ∨ B` into `(A ∨ x)` and `(B ∨ ¬x)`
with fresh `x`. Existentially eliminating `x` gives exactly the original clause:
if either side holds, choose `x` to satisfy the other clause; if neither holds,
the two clauses demand opposite values. The existing complete elimination
checker verifies this projection and the existing lifting rule reconstructs a
model. No new SAT inference rule or Lean theorem is introduced.

Each of four anchors contributes three fixed variants and three paired edits,
for **12 matching preimages and 12 clause-deletion controls**. An edit removes a
different original clause. Independent checking rejects its claimed original
image; this does not imply a changed SAT answer or the absence of other reuse.
Clause/literal order is shuffled and original variable labels are scaled without
changing their order. Fresh labels occupy low, middle and high positions. This
is not arbitrary variable-isomorphism recognition. Every complete root is absent
from both initial histories and from the latest full checkpoint.

The control history is the pre-case-10 checkpoint: **2,263 patterns / 233 pairs**.
The treatment adds precisely the saved subproof dependencies: **39 patterns /
four pairs**. These are isolated copies. The latest **2,443-pattern** authority
remains preserved and is the starting point of the final union.

The solver receives only CNFs; construction witnesses and anchor labels are
used for validation and attribution, never route selection. Ordinary depth-zero
acquisition is followed, when necessary, by unchanged committed scoped
continuation. Limits are 128 prefix admissions plus at most two continuation
batches of 128 admissions and sixteen operations each: **384 charged stage
admissions per query visit**, not one shared 128 limit. Each history processes
all 24 inputs, then repeats them. All queried roots remain distinct within a
visit, while intermediate results can transfer between queries. No stage hits
its cap in the observed runs.

Two fresh-process repetitions reverse mode order. All query proofs are checked
through separate read-only connections; full history auditing and compression
occur at stream end. Neither tests nor builds run during these measurements.
The [frozen protocol](../experiments/results/cnf-join-transfer/protocol.json)
records the workload and limits before preparation or solving.

## Where the reuse occurs

| Anchor variables | Matching preimages: new patterns, base / joins | Matching preimages: probes, base / joins | Edited controls: patterns / probes, either mode |
| --- | ---: | ---: | ---: |
| 4 | 6 / 6 | 24 / 24 | 5 / 16 |
| 27 | 29 / 17 | 143 / 90 | 39 / 196 |
| 32 | 19 / 9 | 127 / 72 | 59 / 408 |
| 39 | 16 / 3 | 70 / 24 | 33 / 148 |

The whole acquisition difference occurs on cases **10, 12 and 18**. They save
12, ten and thirteen nodes, and 53, 55 and 46 probes respectively. The first
and third enter the 27- and 39-variable anchors directly. Case 12 joins below
the 32-variable anchor, reusing ten descendants while bypassing its first two
nodes. The four-variable anchor is never needed. Later related queries benefit
from what either history has already acquired; the comparison does not count
that common reuse as another treatment gain.

The 35 avoided nodes are exactly preloaded rows that the control reconstructs.
The treatment acquires no node absent from the control's additions. Final query
proofs match for every case, and repeated trials have identical records and
archive bytes within each mode. The treatment's final inventory contains the
control's complete inventory plus **four unused preloaded nodes**. Its final
split catalog is identical to the control's. Retention has moved acquisition
earlier; it has not made those historical acquisitions free.

Both second visits acquire **zero patterns, zero splits and zero probes**.
Lookup, proof reconstruction, bookkeeping and verification still cost time.
The 12 edited controls gain no acquisition reduction, even though some proofs
reach common descendants. They consume **136 of 171 new patterns (79.5%)** and
**768 of 978 probes (78.5%)** in the treatment. The largest is **case 13**,
with **33 variables / 95 clauses / 274 literals / width four**, requiring
29 patterns and 218 probes. This is the most informative remaining interaction
in this constructed set.

## Runtime, memory and persistence

| Resource, 24 inputs and their second visit | Base history | History with joins |
| --- | ---: | ---: |
| New patterns | 206 | 171 |
| Probes | 1,132 | 978 |
| New split certificates / source assumptions | 14 / 28 | 10 / 20 |
| Solve and bookkeeping, seconds | 3.26149 | 3.11546 |
| Per-query checks, seconds | 1.06750 | 1.06783 |
| Complete cold audit, seconds | 7.53518 | 7.51164 |
| Compression, seconds | 0.84189 | 0.85021 |
| Restoration/setup, seconds | 0.05503 | 0.05160 |
| Other charged stream overhead, seconds | 1.71452 | 1.73501 |
| Whole stream, seconds | 14.47562 | 14.33176 |
| Mean peak RSS, bytes | 463,216,640 | 463,994,880 |
| Final patterns / pairs | 2,469 / 247 | 2,473 / 247 |
| SQLite bytes | 44,937,216 | 44,978,176 |
| Gzip bytes | 2,265,225 | 2,276,240 |

Acquisitions fall **16.99%**, probes **13.60%**, and solve/bookkeeping time
**4.48%**. Whole-stream mean time falls only **0.99%**: paired base times are
14.21148 and 14.73976 seconds, versus 14.14394 and 14.51958 with joins.
Both differences have the same sign, but two pairs do not establish a reliable
small timing effect. Full auditing still takes about **52%** of total time.
Peak RSS rises **0.168%**, SQLite **0.091%** and compressed storage **0.486%**.
These are measured costs, not a general memory reduction.

The stream clock includes all work between restoration and final archival
completion; the table's residual overhead keeps time outside named internal
windows visible. Imports and final report writing are excluded. Whole-history
row snapshots used for experimental prefix checking are included in bookkeeping.
Peak RSS includes all phases. Preparing the workload and both fully audited
seed histories takes **16.01400 seconds separately**, without a per-mode split.
Historical acquisition is retained in earlier reports. Retrospective independent
validation takes **98.03284 seconds**, partly concurrent with tests, and is not
an operational latency estimate. These preparation and history costs prevent
claiming a net acquisition-plus-use speedup from the local comparison alone.

## Durable result and next target

The final union retains **171 additional patterns and ten splits** over the
latest authority: **2,614 patterns / 259 pairs / seventeen inherited missing
children**, using **47,181,824 SQLite / 2,375,854 gzip bytes**. Original coverage
remains **17/24**, with the same **999-step** positive proof. The separate new
24-input catalog has a **208-step** combined positive proof; its bindings are
included in the checkpoint. Structural coverage is not a SAT/UNSAT answer.

All **376 tests** pass. The independent validator reconstructs both initial
histories, both experimental seeds, all four streams and the union. It checks
192 query-proof replays, stage budgets, exact seed differences, complete catalogs,
original bindings, unchanged prefixes and rejection of all twelve incorrect
anchor-image claims. Prior sources, artifacts and 64 manuscript proof blocks
remain preserved. The default solver and old proof checkers are unchanged.

Restore `experiments/results/cnf-join-transfer/checkpoint.json`.
Checkpoint SHA-256: `5bd57b9b2bf1007a4b447764c40d8c4d920450f6f90699342926218c41b9a652`.
Report SHA-256: `98eb6b23f6bcb2d80c9dc7714bad65ce5de37c6fb0875cdd8e9ee7c4160cf346`.
The checkpoint retains both `supplemental_queries` and `supplemental_proof`;
future unions must preserve those artifacts as well as the original corpus.
The new result directory retains **38 manifested artifacts plus its manifest,
68,154,280 bytes** in total. This includes both seeds, all trial archives and
verbose proof/counter records; it is separate from the union database size.
The next preservation audit inherits **3,588 artifacts across 62 manifests**.

**Next:** inspect which clause dependencies prevent reuse on the costly edited
case 13, compared with its matching preimage. Look for a shared checked residual
or transferable split under an explicit variable map; exact equality of dimensions
or a deleted-clause assumption is insufficient. Reuse is valid only after the
new boundary and all proof obligations are checked. For the matching cases, the
missed 27-variable entries also expose a route-ordering question: a one-pair
projection exists, yet ordinary normalization can reach a different residual.
The earlier [projection index](projection-lookup.md) and its costly negative
frontier results remain relevant; do not rebuild that global index by default.
Use original **case 7** as a separate broader discovery control. Neither these
constructed positives nor complete finite coverage establish efficient arbitrary SAT.
