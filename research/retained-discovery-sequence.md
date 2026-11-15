# Discovery across retained original scopes

2026-11-15. Four bounded expansion batches now follow the complete global
selection within one checked session. This covers **cases 1406 and 1195**, raising
structural coverage of the retained difficult corpus **70/83 -> 72/83**, and
preserves partial work on **case 1062**. The work extends the discovery sequence;
it does not introduce a new recognizer or change the solver's inference rules.

## Why continue across originals

The previous investigation spent about 66.7 seconds on initial catalog checking
for 0.16 seconds of local expansion. Rebuilding that state after every completed
original would repeatedly pay preparation. Here the initial checked inventory,
prepared view and complete maintained route catalog survive four batches. After
each batch a complete query selects the next original or retained pending split.
The existing guarded admission reset, live table digests, copied batch seed,
append verification and output serialization remain enabled.

Two independent histories start from the same preserved parent. Each permits
four batches with at most **32 admitted states / twelve advances per batch**.
The sequence stops early only if the global selector has no source. This is a
bounded discovery policy, not a minimum-expansion algorithm. Both runs follow
the same four batches and retain the same operations and logical state.

| Batch | Actual original scope | Input variables / clauses / literals | Admission entries | Stored patterns | Result |
| --- | --- | --- | ---: | ---: | --- |
| 0 | 1406, index 64 | 40 / 168 / 505 | 7 | 7 | Original structurally covered |
| 1 | 1195, index 35 | 40 / 171 / 517 | 3 | 3 | Original structurally covered |
| 2 | 1062, index 14 | 40 / 174 / 541 | 32 | 29 | Pending split at 26 / 111 / 367 |
| 3 | 1062, retained scope | 26 / 111 / 367 | 32 | 24 | Pending split at 19 / 77 / 261 |

The original-index list is empty for the retained selection in batch 3. It is
left empty. The validator checks an actual coverage-dependency path from the
previous original scope instead of inventing a new selector binding. A path is
not a SAT-truth implication: its conditioning rules retain both premises, and
other component or branch obligations remain in complete original recomposition.

## Conditional refutation is not original refutation

The first two batches repeat the useful structure found in the preceding case
1227, but with a different original truth value. Each ranks sixteen saved pairs.
Case 1406's selected residual splits on local variable **9**, yielding
**38/154/451** and **37/148/422**. Chains of four and three new probe reductions
reach the existing empty-clause terminal. Case 1195's selected residual splits
on local variable **17**, yielding **38/150/441** and **38/161/469**. One and two
new probe reductions again reach that terminal. The selected residuals and all
four of these cofactors are independently **UNSAT**.

Both **original formulas are SAT**, with independent models checked against
the originals. Earlier conditioning puts these refuted residuals inside formulas
that have satisfying alternatives. This is why dependency ancestry must not be
used to transfer the truth value of a selected branch to an original. The new
closure concerns a complete checked structural description; it is separate from
a SAT decision and does not imply these SAT answers were previously unavailable
to another solver.

Case 1062 develops a different mixture. Binary-path reductions and bounded
elimination recur between probe reductions and further splits. A new terminal
of size **4/5/14** is both **zero-valid and one-valid**, but neither Horn nor
2-CNF. Its local all-zero and all-one assignments satisfy that terminal; their
transport to an ancestor requires the stored source maps and reduction evidence.
Other structural obligations remain open. Independent reference solving reports
SAT for the three touched split sources in this original; their cofactor answers
are respectively **(SAT, SAT)**, **(SAT, SAT)** and **(UNSAT, SAT)**. Those reference
answers are validation evidence, not substitutes for the missing classification
records.

The union adds **63 patterns**: **19 probe reductions, 27 eliminations, 13
binary-path reductions, one family terminal and three unresolved records**.
Thus the gain is reuse of existing methods and exact stored terminals, with new
source-bound intermediate proofs. Similar sequences of rule names do not make
intermediate CNFs equivalent and cannot authorize cross-source proof transport.

The reconstructed split prefixes contain **75 node occurrences / 64 distinct
records**: all 63 new records and one inherited empty-clause terminal. Every
pair of original scopes shares exactly that terminal and **no new record**.
Case 1062 uses 53 new prefix nodes; cases 1195 and 1406 use three and seven.
The eleven repeated prefix occurrences include pending-split replay within one
original and are distinct from the three repeated admission entries. These
counts describe the touched single-edge prefixes, not every alternative in the
complete original proof. They expose the remaining reuse gap: the method and
terminal recur, while intermediate semantic obligations are still separately
acquired. Equal rule names are not a compressed representation of those CNFs.

There are **74 admission entries on 71 distinct inputs**. Three entries repeat
work interrupted in batch 2, and all three are stored in batch 3; eight distinct
inputs still have no stored record
at the end. Their exact keys and partial split obligations are preserved. The
next resume must charge any re-entry again. A smaller selected variable count
alone does not establish cheaper remaining search: the 19-variable residual
has clause widths **{2: 10, 3: 40, 4: 18, 5: 6, 6: 2, 7: 1}**.

## Time and space

| Mean elapsed seconds per four-batch sequence | Cost |
| --- | ---: |
| Initial catalog, full global query and serialization | 66.09003 |
| Four workers, including preparation, checks and export | 4.17511 |
| Local selection, acquisition, refresh and coverage within workers | 1.02047 |
| Four updated global queries | 1.24832 |
| Updated-query serialization | 1.40627 |
| Complete sequence | 73.47861 |

Sequence observations are **72.80775 / 74.14947 seconds**. The complete sequence
also charges the initial history copy and diagnostic union merge/check. Each
history is independent; the diagnostic union is shared, so the second identical
merge is idempotent. Local expansion is included in worker time and must not be
added again. The four per-batch copies account for **3,123,806,208 logical copied
bytes**, in addition to the initial arm copy; mean per-batch-copy time sums to
**0.95475 seconds**. This is neither peak storage nor physical memory traffic.

Shared parent restoration costs **145.39246 seconds**. Final cold route/coverage
checking costs **71.37039 seconds**, and full union-delta comparison **5.36843
seconds**. Reference acquisition costs **0.17332 seconds** for gained originals
and **0.21711 seconds** for split-related checks; their cold reference checks
cost **1.78551 / 1.84436 seconds**. The complete producer takes **392.16512
seconds**, including both repetitions and the shared checks. The two covered
originals and the unfinished third source are adaptively selected development
cases. There is no matched fresh-per-batch control, statistical speedup claim or
unrestricted-SAT bound. The measured fact is that one startup serves four
batches and that their complete costs remain recorded.

Structural history grows **856,064 bytes**, from **780,750,848 to 781,606,912
bytes**, with **42,480 -> 42,543 patterns**. The union delta is **946,176 SQLite
bytes / 39,688 compressed bytes**. Five new split records increase evidence from
**(1, 42, 156, 64, 1)** to **(1, 42, 156, 69, 1)**; both bridges remain. Both
runs retain **20,472 current / 2,916 prepared checked objects**. These counts do
not measure peak RAM or the cost of retained Python objects.

Reference evidence grows **5,182 -> 5,488 nodes**, from **34,992,128 to 37,126,144
SQLite bytes** and **2,398,593 to 2,551,039 compressed bytes**. Its **2,134,016-byte**
SQLite growth is separate from structural storage. All **5,182 earlier reference
payloads**, **2,129 prior artifacts / 38 manifests** and earlier implementation
fingerprints remain unchanged. The paid historical archive remains part of the
resource account even when the marginal structural delta is small.

## Resume state and next priorities

Resume **`experiments/results/cnf-retained-discovery/report.json`**, SHA-256
`0d59f8bb3018c78b5da947a31d1a0d492103c15968df7d706b7ad1910b038f84`, with
**`experiments.continue_cnf_retained_discovery.restore_checkpoint`**. Use its
**`next_selection` and saved pending split**, at **19/77/261**. Next source
SHA-256 is `6dc3baf529a3e0f1996e284da088a331844005832f980aaa48aa7721f50c250e`.
The original-index list is empty for this retained work; the checked dependency
path binds it to **case 1062, index 14**. The report's initial `source` and
`source_original_indices` belong to the completed case 1406 and must not be
used as the next acquisition focus. Keep evidence **(1, 42, 156, 69, 1)** and
**two bridges**.

The next discovery priority is the pending pair in case 1062. Preserve both
cofactors, the eight interrupted inputs and all existing alternatives. Look for
shared intermediate identities or exact boundary summaries across the mixed
probe/elimination/binary-path chains. Repetition of a reduction method is useful
engineering reuse but is not yet compression of distinct semantic obligations.

Keep the earlier distinction between decision progress and complete structural
coverage visible in the next comparison. A checked original SAT witness can
justify returning SAT without classifying both cofactors. The present coverage
experiment deliberately checks the other obligations as well; those extra costs
must not be described as necessary SAT-decision work. The existing
[case-1299 priorities](split-cost-1299.md) already identify this separate metric.
Reference answers do not silently replace the structural certificates.

Cold reconstruction and verification remain the largest measured costs. A future
supporting experiment can extend guarded checked replay or test a materialized
history checkpoint bound to full logical table digests and unchanged policies.
It must preserve all old archives, account for extra snapshot space and validation,
and must not turn a missing-row lookup into negative evidence. Neither change
has been measured in this sequence. Eleven originals remain structurally open;
compact coverage and bounded acquisition for arbitrary CNFs remain unresolved.

## Final validation and preservation

All **283 tests** pass. Independent cold replay takes **918.21023 seconds**,
checks both four-batch histories and all **ten saved global queries**, reconstructs
every acquisition prefix with only then-available rows, and validates all **5,488
reference nodes** with fresh recognition and reference search disabled. Original
SAT models are checked against the original inputs. Both sequences have identical
operations, compressed deltas, logical tables and selections. The checked paths
for both newly covered originals contain two earlier conditioning steps; the
retained case-1062 scope also includes its acquired split and reduction path.

The result manifest binds **122 artifacts / 11,125,414 bytes**, excluding itself.
Validation checks **125 implementation fingerprints**, all **38 prior manifests**
and **2,129 earlier artifacts**. All **5,182 earlier reference payloads** remain
byte-for-byte present. The manuscript builds to **169 pages**, with all **64
existing proof blocks** unchanged and no new proof blocks, overfull boxes or
undefined references. Logs, source identities and resume details are retained in
[the result directory](../experiments/results/cnf-retained-discovery/README.md).
