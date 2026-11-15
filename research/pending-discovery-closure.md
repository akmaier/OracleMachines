# Completing the pending mixed reduction chains

2026-11-15. Four bounded batches complete **case 1062**, raising structural coverage
of the retained difficult corpus from **72/83 to 73/83**. Two independent histories
produce identical operations, stored records and complete global selections.
This extends an existing exact classification; it introduces no new recognizer,
SAT class or uniform acquisition bound.

## Resume every outstanding obligation

The initial source is the saved **19/77/261** residual and its pending split. Its
selector original-index list is empty. The validator independently follows a
coverage-dependency path from original **1062 / index 14**; it does not invent a
nonempty selector label or infer the original's truth from one branch.

| Batch | Initial selected variables / clauses / literals | Entries | Stored records | Result |
| --- | --- | ---: | ---: | --- |
| 0 | 19 / 77 / 261 | 11 | 11 | Pending branch closes; original still uncovered |
| 1 | 36 / 153 / 479 | 32 | 20 | Split proceeds to 26 / 104 / 335; 12 inputs interrupted |
| 2 | 26 / 104 / 335 | 32 | 28 | Split proceeds to 13 / 57 / 220; four inputs interrupted |
| 3 | 13 / 57 / 220 | 9 | 9 | Remaining branch and original close |

Every batch retains the existing 32-state and twelve-advance limits. There are
**84 admission entries on 68 distinct inputs**. The 12 and four interrupted inputs
are re-entered and charged again. The first batch also completes **all eight
inputs interrupted in the preceding checkpoint**; their earlier charges remain
in that checkpoint. No entered input remains without a stored record at the end.
The two stored `unresolved` records are intermediate nodes subsequently covered
through explicit external rules, rather than incomplete serialization.

Across both discovery checkpoints, the six batches belonging to case 1062 charge
**148 entries / 121 distinct inputs**, with
**27 repeated admissions** after counting the checkpoint boundary.
All **53 earlier records** remain disjoint from the **68 new records**;
all those inputs now have stored records. The counts exclude work on other originals.
They identify a remaining continuation gap: completed nodes persist, while unfinished
control frames may be re-entered. This is a state-count overhead, not a measured
runtime saving available from persisting those frames.

The selected size first grows from 19 to 36 variables because the query selects
a different outstanding branch after the first closes. Selected residual size is
therefore not a monotone measure of original coverage. This is not evidence that
a reduction enlarged the same source; the two selections have distinct identities.

## Existing families combined through checked transformations

The new delta contains:

| Stored rule | Records |
| --- | ---: |
| binary_paths | 13 |
| eliminate | 22 |
| family | 5 |
| polarity | 3 |
| probe | 23 |
| unresolved | 2 |

The five terminal records have the following recognized properties:

| Variables / clauses / literals | Recognized properties |
| --- | --- |
| 9 / 18 / 49 | zero_valid |
| 8 / 10 / 23 | horn, zero_valid |
| 14 / 17 / 43 | horn, zero_valid |
| 4 / 3 / 7 | horn, zero_valid |
| 6 / 6 / 16 | horn, zero_valid |

Three polarity records transform the **8/10/23**, **14/17/43** and **6/6/16**
formulas into Horn formulas with the same sizes. Before transformation their
recorded Horn, dual-Horn, 2-CNF and constant-assignment tests are excluded.
The checked literal flips expose Horn and all-zero witnesses in the targets.
Thus recognition can improve without any reduction in the size triple. The
**4/3/7** Horn terminal is reached without one of these new polarity edges.
The **9/18/49** terminal is all-zero satisfiable while Horn, dual-Horn and 2-CNF
are excluded; recognition of one class does not require recognition of another.
Unresolved recognizer outcomes, including some parity checks, remain unresolved.

All four touched split sources and original 1062 are independently **SAT**.
Their cofactor answers are **(UNSAT,SAT)** for the resumed 19-variable source,
then **(SAT,SAT)** for each of the other three sources. These reference answers
validate the stored structural work. The experiment measures completion of a
structural description with both conditioning premises, not the minimum work to
find one original SAT witness. Truth transfer still requires the complete checked
maps and recomposition; a refuted cofactor does not refute a satisfiable original.

## Exact reuse and its limits

The touched split prefixes contain **75 occurrences /
71 distinct records**. They include **68 new** and
**3 inherited** records; **4 repeated visits** include
pending-split replay and are separate from the sixteen repeated admission entries.
Comparing exact keys with the preceding checkpoint's touched prefixes gives:

| Previous original | Shared records with the current case-1062 prefixes | Record kinds |
| --- | ---: | --- |
| 1062 | 3 | probe: 2, retained_plan: 1 |
| 1195 | 1 | retained_plan: 1 |
| 1406 | 1 | retained_plan: 1 |

Reuse under the same original is concrete preserved work. The comparison does
not establish a shared nonterminal representation across unrelated original CNFs.
These are intersections of measured prefixes, not every global alternative or all
possible variable-renamed or semantically equivalent representations. Repeated
rule names, family labels and size triples alone are not certificate transport.
The new pattern keys occupy **113,237 bytes**, their payloads
**362,746 bytes**, and stored CNFs contain
**11,004 literal slots**. Those counts are not net compression savings;
indexes, serialization, reconstruction and the already applied gzip have separate costs.

## Full costs and validation

| Mean cost per four-batch sequence | Seconds |
| --- | ---: |
| Initial catalog, global query and serialization | 63.74848 |
| All workers | 3.91920 |
| Local expansion within workers | 0.84877 |
| Updated global queries | 0.88877 |
| Updated query serialization | 1.43440 |
| Complete sequence | 70.46120 |

The two complete sequence samples are **69.30152** and
**71.62088 seconds**. Checked parent restoration is separately
charged at **8.70349 seconds**. The existing compressed materialization
is reused; no new full snapshot is created. Final cold global route/coverage work
adds **70.69285 seconds** and the whole
producer takes **251.61519 seconds**. Repeated development runs establish
reproducibility, not a matched solver speedup. Batch seed copies and full live
digests remain enabled; the four batch copies total **3,127,705,600 logical bytes**.
Initial arm copies, serialization, append checking and reference acquisition are
also retained in the producer and its separate cost fields.

History grows **843,776 bytes** to **782,450,688 bytes /
42,611 patterns**. The structural delta occupies **905,216 SQLite bytes / 34,862
compressed bytes**, and three new split records increase the split evidence
count to 72. Both sequences retain **20,540 current / 2,916 prepared checked
objects**; peak RAM remains unmeasured. Independent reference evidence grows
**5,488 -> 5,612 nodes**, adding **491,520 SQLite bytes**. Its final archive occupies
**37,617,664 SQLite bytes / 2,593,137 compressed bytes**.

All **299 tests** pass before measured production. Independent replay disables the
materialized-cache path, fresh structural recognition and fresh reference search.
It reconstructs both sequences, every acquisition prefix and all **ten saved
global queries**, verifies the actual original scope, checks the original SAT
model and all **5,612 reference nodes**, and establishes identical operation and
delta outputs. It takes **934.44048 seconds** as an audit cost, not a performance
comparison. All **2,277 earlier artifacts / 40 manifests**, **131 earlier source
fingerprints** and **5,488 earlier reference payloads** remain unchanged.

## Continue from the new acquisition state

Resume `experiments/results/cnf-pending-discovery/report.json` using
`experiments.continue_cnf_pending_discovery.restore_checkpoint`. Its default
loads the checked parent materialization and applies the new delta; setting
`materialized=False` independently replays the original history. The new report's
SHA-256 is **2b552019b9eaba71a058d7d6a1dc1a28817aa6a6a40d18a16a18b34fb56c2c00**.
Use **`next_selection`**, not its completed initial source: **case 1121 / index 23**,
**41/174/513**, no pending split. Preserve evidence **(1,42,156,72,1)** and two bridges.

The next investigation should continue discovery on that original in a retained
session. Track coverage obligations and verified class transformations alongside
sizes, and test actual nonterminal or boundary equivalences before claiming reuse
across inputs. Ten originals remain structurally uncovered. Neither this finite
completion nor its short local expansion supplies a polynomial acquisition or
compact-closure construction for arbitrary SAT.
