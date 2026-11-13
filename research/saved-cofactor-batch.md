# Saved cofactors versus ordinary probe continuation

The saved-trace checkpoint covers 53 of the 83 retained development originals.
Four acquired open leaves below learned targets have 33, 33, 36 and 38 variables.
This experiment compares reuse of their existing cofactor traces with later
ordinary probing. It preserves both arms and merges their immutable evidence.

## Comparison contract

Both arms start from an identical parent database with fresh verifier caches.
All source identities and candidate rankings are frozen before acquisition. For
each source, at most eight retained opposite-polarity pairs are ranked using the
existing distinct uncovered/missing child, support and literal criteria. The
split arm chooses the first ranked pair. Both branches remain necessary for
structural closure; a SAT answer for one branch does not close the partition.

Each source receives at most 32 distinct recognition-state admissions. The split
arm also shares a global 128-state budget and does not reset it between branches
or sources. The ordinary arm uses up to eight advances and four visited sources
per initial leaf; its four separate 32-state allowances total at most 128. It
reports both the union of admitted identities and the sum of per-pass admissions:
an unfinished identity revisited in another ordinary pass can be charged again.
This is a matched admission allowance, not a matched CPU-work budget. Reentered
states, inference, proof checking and discovery can require additional work.

Candidate ranking, each arm's cold preparation, acquisition, composition,
serialization, persistence, merged replay and independent reference checks are
charged. Shared preparation is reported separately. No whole-solver timing
comparison or peak-RAM bound follows from these single measurements.

Each completed record remains immutable. Partial children and inconclusive
probe blocks survive. A split cannot contribute a coverage route until both
children exist; it closes only when both have checked structural plans. Each
newly completed child can also activate older pending probe or learned routes,
which are refreshed before coverage is measured. Diagnostics preserve both
cofactor obligations, including missing children and selected old-plan
frontiers; those frontiers do not enumerate every possible alternative plan.

## Reproduction and resumption

```sh
python3 -m unittest discover -s solver > /tmp/cnf-split-batch-tests.log 2>&1
python3 experiments/compare_cnf_split_batch.py /tmp/cnf-split-batch-reproduction
python3 experiments/validate_cnf_split_batch.py /tmp/cnf-split-batch-reproduction --test-log /tmp/cnf-split-batch-tests.log
```

The runner's parent is `experiments/results/cnf-trace-split/report.json`.
`compare_cnf_split_batch.restore_checkpoint` restores the merged child checkpoint
and returns rewrites, learning bases, augmented continuations and **all** split
records, including the inherited split. `routes_for` checks and attaches all
four evidence layers. Omitting the external split layer loses certified routes.

Four new regression tests check zero-budget pending branches, shared allowances,
partial resumption, duplicate-source skipping, cold reuse without discovery and
invalid limits. The standalone validator reconstructs each arm independently,
replays frozen selection, verifies all new nodes and proof routes, checks the
merged logical database against the union of both deltas, and checks preserved
reference proofs without new discovery. The runner also audits the full merged
inventory and checks idempotent delta replay. No historical implementation file,
experiment or Lean theorem is modified.

## Measured results, 13 November 2026

The merged checkpoint reaches **55/83**, from 53/83, also with the growth
exception disabled. Case **37** (`selection_holdout3`, n48, original 1226) is
independently **UNSAT**. Case **77** (`subsumption_holdout3`, n48, original 1448)
is independently **SAT**. Historical group names do not make these adaptively
reused development cases an independent holdout. The earlier 902/985 study is
not rerun and its counts must not be combined with these results.

| Isolated arm | Closed originals | New pattern states | Acquisition seconds | Working SQLite growth |
| --- | ---: | ---: | ---: | ---: |
| Later ordinary probes | 54/83 (case 37) | 7 | 0.09725 | 315,392 bytes |
| Saved cofactor splits | 55/83 (cases 37, 77) | 30 | 0.14475 | 413,696 bytes |

Split ranking additionally costs **0.05791 s**. Every source has four retained
pairs; all selected pairs initially have two absent children. Three of four
selected fragments close under splitting. The first 33-variable / 128-clause
fragment remains open; one cofactor closes while the other has a selected
**27-variable / 101-clause** leaf. The other selected fragments are 33/133,
36/156 and 38/155. Per-pair admissions are **8, 5, 5 and 12**. Every child is
acquired; no admission cap binds. Seven of eight child obligations close.

The ordinary arm acquires four windows and thirteen continuations: fifteen
clear blocks and two forced blocks. It uses **0, 4, 3 and 0** admissions on the
four sources. It closes case 37 but not case 77. Both isolated deltas are retained;
their union shares one new pattern identity, yielding **36** distinct new nodes.
Merged coverage remains 55/83: retaining the control contributes evidence but no
additional original closure beyond the split arm.

The merged working SQLite grows **720,896 bytes** to **769,384,448 bytes**. It
contains **41,700 pattern nodes**, **84 ordinary windows**, **121 ordinary
continuations**, 41 learning bases and 150 augmented blocks. There are **five
external split records**, including the inherited one. All earlier eight-table
rows remain unchanged. The union delta is 782,336 bytes, compressed to **38,965
bytes**; the four new split records are 55,063 bytes, compressed to **5,868 bytes**.
These archives, coverage certificates and reference proofs are additional to the
working database. The extended independent reference archive contains **1,721
nodes**, preserving all **1,175** inherited nodes; it is 13,426,688 bytes,
compressed to 869,591 bytes. These are storage measurements, not peak RAM.

The comparison pipeline costs **405.18 s**. Shared parent preparation takes
62.55 s; fresh split/probe arm preparation takes **65.37 / 67.69 s**; merged
composition with fresh verification takes **66.84 s**; the full cold inventory
audit takes **107.02 s**. Archive restoration, exports, checking and serialization
are also included in the pipeline. These repeated preparations are evaluation
costs, not the cost of one warm expansion. The source selection and cofactor
ranking likewise cannot be treated as free. The split arm buys one additional
original closure at higher local acquisition and storage cost; no general runtime
speedup follows.

All **585 Python tests** pass (80.818 s). The separate standalone cold replay
takes **292.78 s**, in addition to the comparison pipeline. It reconstructs both arms
and their union with discovery disabled, rechecks both gained originals and all
new split/forced-probe reference obligations, and leaves reconstructed database
bytes unchanged. The full inventory audit checks all 41,700 pattern nodes. This
is executable proof checking and finite evaluation, not a new Lean refinement or
an unrestricted-SAT complexity theorem; the manuscript's general claims remain
unchanged.

## Next useful discovery target

The first open split's true cofactor has a selected 27-variable / 101-clause leaf,
minimum clause width two, with 18 ranked ordinary variables. Its exact key and
both branch obligations are in `diagnostics.json.gz` under `children`. Start there
instead of repeating the already exhausted ordinary stream on the 33-variable
parent. The older `target_state` view alone follows selected old plans and can
still show that parent; it does not descend through an open external split.

After reapplying the merged coverage filter, the 41 learned bases comprise ten
covered, nine exhausted, **18 ready (92 remaining ranked variables)**, three
initially successful and one acquired open target. A small bounded continuation
on the 27-variable child is the next concrete structural experiment; compare its
cost with these ready learned bases before another broad acquisition pass. Keep
both partial partitions and their exact compatibility conditions. Recognition,
compact closure and uniform polynomial bounds for arbitrary CNFs remain open.

Resume `experiments/results/cnf-split-batch/report.json` through
`compare_cnf_split_batch.restore_checkpoint` and `routes_for`. All five external
splits must be attached. The old trace-split loader alone reconstructs only 53/83.
