# Conditional refutation with a shared terminal

2026-11-15. The next unresolved frontier, original **case 1227**, now has complete
checked structural coverage. Coverage of the retained difficult cases rises
**69/83 -> 70/83**. This advances the discovery priority after the preceding
cold-replay optimization. It uses the existing recognizers and saved-pair
scheduler; no new tractable family or universal search bound is claimed.

## The discovered structure

The selected residual has **40 variables / 165 clauses / 494 literal occurrences**.
The original has **48/204/612**. The unchanged scheduler ranks sixteen saved
pairs and selects local variable **20**. Its rank is `[2, 2, 37, 815, 20]`;
this is a deterministic heuristic ranking of checked candidates, not an optimum
for all possible expansion orders. Variable identifiers are local to the bound
canonical source.

The two checked restrictions yield **35/140/400** and **37/143/415**. The first
reduces through probe records at **35/140/400 -> 33/130/366 -> 30/109/294** to
the empty-clause terminal. The second reduces through **37/143/415 ->
34/127/357** to the **same stored terminal**. Five new probe records complete
both chains. No family record or external probe-window/continuation record is
added. The internal probe recognition and its checked reasons still cost work;
zero external assumption attempts does not mean zero probing.

The useful pattern is conditional refutation: a saved split exposes short
checked reduction chains in both polarities, which reconverge at an existing
contradiction. The five intermediate sources are distinct new identities.
Sharing the terminal avoids duplicating that terminal proof; matching rule
names or source shapes would not justify reusing the other records. Each source,
restriction, renaming, forced assignment and reduction target remains bound to
its exact evidence. Both branches are needed for the split refutation. Complete
original recomposition retains all earlier obligations. Independently acquired
reference evidence reports this original as **UNSAT**; that answer is distinct
from the structural-coverage count.

## Reproduction and charged costs

[The driver](../experiments/continue_cnf_case1227.py) restores the frozen canonical
checkpoint and runs two independent histories with the same policy. Each permits
up to four batches with **32 state admissions and twelve advances per batch**,
stopping when this original closes. Both stop after **one advance / five
admissions**, all stored, with no interrupted states or repeated admissions.
The full initial catalog, global query, copied batch seed, live table digests,
append verification, complete updated global query and serialized output remain
in the measured sequence. This is a repeated discovery run, not a comparison
against a different solver or an asserted speedup.

| Mean elapsed seconds | Cost |
| --- | ---: |
| Initial catalog, global query and serialization | 66.68418 |
| Worker, including preparation, checking and export | 1.18892 |
| Local selection, acquisition, refresh and coverage | 0.15935 |
| Updated global query | 0.24565 |
| Updated query serialization | 0.34866 |
| Complete sequence | 68.83255 |

Sequence observations are **67.33648 / 70.32863
seconds**. Local expansion is part of worker time; it must not be added again.
The full sequence also charges the initial history copy and diagnostic union
merge/check. Histories are independent, but the diagnostic union is shared;
the second identical merge is idempotent. Shared parent restoration costs **140.08953 seconds**,
final cold route/coverage checking **73.35126 seconds**, and the complete producer
**383.53841 seconds**. Full union-delta comparison separately costs
**6.16828 seconds**. Unit tests finish before the producer;
independent replay and documentation checks start afterward. Shared OS caches
and adaptive development-case selection remain limitations.

The original reference search costs **0.47185 seconds**, followed by separately
recorded split/source checks and cold reference checking. This is a different
certification workload with a different retained history, not a matched solver
comparison. In particular, the 0.16-second local structural expansion cannot be
presented as an end-to-end speedup over that reference solver.

## Storage and preservation

The structural history grows **73,728 bytes**, from **780,677,120 to 780,750,848
bytes**, with **42,475 -> 42,480 patterns**. Its union delta occupies **139,264
SQLite bytes / 6,803 compressed bytes**. A separate split sidecar increases the
evidence groups from **(1, 42, 156, 63, 1)** to **(1, 42, 156, 64, 1)**; both
bridges remain. These small incremental costs do not erase the paid historical
archive.

Both runs retain **20,409 current / 2,916 prepared checked objects**. Serialized
unique keys occupy **61,086,599 bytes** and node JSON **195,953,764 bytes** across
these views. These are logical serialized sizes, not resident Python memory or
peak RAM. Exact-key and decoded-node storage still duplicate representations.
No new compression claim follows from counting them.

Independent reference evidence grows **4,802 -> 5,182 nodes**, from **31,289,344
to 34,992,128 SQLite bytes**. Its compressed archive grows **2,194,628 ->
2,398,593 bytes**. Thus reference validation adds more storage than the five
structural records. All **4,802 prior reference payloads**, **2,077 earlier
artifacts / 37 manifests**, and earlier implementation fingerprints are preserved.

## Resume and next gaps

Resume **`experiments/results/cnf-case1227/report.json`**, SHA-256
`240f8151528c19ef69cac3b958abfc489710ffa1961944799d957545ff10f722`, with
**`experiments.continue_cnf_case1227.restore_checkpoint`**. Use **`next_selection`**,
not the completed `source`: **case 1406, retained index 64**, at **40/168/505**,
**no pending split**. Next source SHA-256 is
`e0c00ad1ae7cf6206de15039aaca9d2be80d75118f1353fe4dbb426a5459d9a7`.
Keep evidence **(1, 42, 156, 64, 1)** and **two bridges**. The checked-replay
experiment remains valid for its earlier five-checkpoint suffix; its report is
not the new acquisition checkpoint.

The next discovery target is whether another selected source exposes short
conditional refutations or reaches a different family. Record exact shared
identities, not merely similar chains. There are **13 remaining originals**;
this observation does not characterize or efficiently cover them all.

The dominant measured operational gap remains **cold verification and catalog
construction**, not this acquisition. Continue across selected originals in a
retained checked session when possible, while preserving admission boundaries
and complete global selection. For cold starts, extend the guarded checked-replay
contract and measure repeated trace reconstruction before introducing further
caches. These are supporting costs; they should not displace discovery with
another isolated microbenchmark. Recognition of all useful conditioning choices,
compact proof structure and bounded total acquisition for arbitrary SAT remain
open.

## Final validation

All **283 tests** pass. Independent replay takes **559.54505 seconds**, checks
both repeated histories and all **four saved global queries**, reconstructs every
acquisition prefix using only then-available rows, and validates all **5,182
reference nodes** with fresh recognition and reference search disabled. Operations,
compressed deltas, final logical tables and selections agree. Both split branches
are independently UNSAT; the original reference answer is also UNSAT.

The branch prefixes contain **seven node occurrences / six distinct nodes**:
five new probe nodes and one inherited terminal visited twice. They share no
prefix node with the immediately preceding case 1190's recorded split chains;
terminal reuse here is from the earlier history, not evidence of transport
between those two cases. The new records contain **12,564 key bytes / 28,424
payload bytes** and **1,832 stored CNF literal slots**. These representation
counts are not net compression savings.

The result manifest binds **52 artifacts / 7,111,693 bytes**, excluding itself.
Validation checks **122 implementation fingerprints**, all **37 prior manifests**
and **2,077 earlier artifacts**. The manuscript builds to **168 pages**, with all
**64 existing proof blocks** unchanged and no new proof blocks, overfull boxes,
or undefined references. Detailed logs and source identities are retained in
[the result directory](../experiments/results/cnf-case1227/README.md).
