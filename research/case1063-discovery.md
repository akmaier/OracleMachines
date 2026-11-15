# Completing retained branches across three originals

2026-11-15. Two independent four-batch histories raise checked structural coverage
of the retained difficult corpus **75/83 -> 78/83**, completing cases **1063,
1371 and 1158**, in that order. All three originals are independently SAT.
The existing inference rules and 32-state/twelve-advance batch policy are unchanged.
This extends certified coverage of development cases, not a held-out efficiency
claim or a new tractable SAT class.

## Preserve work before entering a pending branch

| Batch | Original scope | Initial variables / clauses / literals | Entries | Stored | Result |
| --- | --- | --- | ---: | ---: | --- |
| 0 | 1063 | 22 / 89 / 309 | 3 | 3 | Pending split and original close |
| 1 | 1371 | 43 / 168 / 505 | 32 | 23 | Advances through 39 / 153 / 460 to pending 27 / 109 / 337 |
| 2 | 1371 | 27 / 109 / 337 | 14 | 14 | Remaining branch and original close |
| 3 | 1158 | 43 / 176 / 531 | 14 | 14 | Selected residual and original coverage close |

The first selection retains empty original-index labels. Independent checking
follows an actual dependency path from **1063 / index 15**, preserving its pending
split. The preceding checkpoint stored every admitted input but left a second
branch with zero new admissions. This sequence completes that branch with **three
new records**; the earlier fifty records remain stored. Across the two checkpoints,
case 1063 charges **67 entries / 53 distinct inputs / 14 reentries**, with all
53 inputs stored. Its final three inputs are new, not repetitions of earlier admissions.
These counts show preserved work; they do not compare runtime with a fresh solver.

| Original | Entries this sequence | Distinct inputs | Reentries | Stored |
| --- | ---: | ---: | ---: | ---: |
| 1063 | 3 | 3 | 0 | 3 |
| 1158 | 14 | 14 | 0 | 14 |
| 1371 | 46 | 37 | 9 | 37 |

Case 1371 has nine interrupted inputs at the end of batch 1. Batch 2 re-enters
and stores all nine, with five additional inputs. All **54 distinct admitted
inputs** have records at the end; the next selection has **no pending split**.
The two new `unresolved` records retain their original payloads even when later
external split rules cover them. Coverage is derived from checked composition,
not by rewriting historical outcomes.

## Overlapping families and conditional refutation

The new delta contains **31 probes, twelve eliminations, six binary-path
reductions, two family terminals, two unresolved records and one polarity
transformation**. A **5/4/8** terminal is simultaneously Horn, 2-CNF and zero-valid.
The **10/12/25** terminal is Horn and zero-valid but not 2-CNF. It is reached by a
checked polarity transformation with unchanged variable, clause and literal counts.
Its source fails the recorded Horn, dual-Horn, 2-CNF and constant-assignment tests;
the parity recognizer remains unresolved. Family overlaps are retained, not
silently converted into a disjoint partition.

The selected **43/176/531** residual for original 1158 is **UNSAT**, with both
cofactors UNSAT, while the **48/204/612 original is SAT**. The checked ancestry
includes conditioning; the refutation therefore closes only that restricted
obligation. It must not be transported as an unconditional refutation of the
original. The other four touched split sources are SAT. Complete structural
classification checks both cofactor premises; finding one SAT witness has a
different stopping condition.

## Exact prefix reuse

Touched prefixes contain **75 occurrences /
71 distinct records**, including **17 inherited records**.
The comparison with the preceding checkpoint is:

| Current original | Previous original | Shared exact prefix identities | Kinds |
| --- | --- | ---: | --- |
| 1063 | 1063 | 16 | binary_paths: 3, eliminate: 11, family: 1, probe: 1 |
| 1063 | 1121 | 0 |  |
| 1063 | 1336 | 0 |  |
| 1158 | 1063 | 1 | retained_plan: 1 |
| 1158 | 1121 | 1 | retained_plan: 1 |
| 1158 | 1336 | 1 | retained_plan: 1 |
| 1371 | 1063 | 1 | retained_plan: 1 |
| 1371 | 1121 | 1 | retained_plan: 1 |
| 1371 | 1336 | 1 | retained_plan: 1 |

Within this sequence:

| First original | Second original | Shared prefix records | Shared new records |
| --- | --- | ---: | ---: |
| 1063 | 1158 | 0 | 0 |
| 1063 | 1371 | 0 | 0 |
| 1158 | 1371 | 1 | 0 |

Case 1063 reuses **sixteen exact prefix records** from its preceding expansion:
eleven eliminations, three binary-path reductions, one probe and one family terminal.
The inherited **39/159/482** and **22/89/309** unresolved records now occur in the
complete original-coverage proof through two-premise external split rules. Their
stored payloads remain unchanged. This compares the saved global positive proofs;
absence from the earlier proof does not exclude an earlier local derivation.
Across different originals, the nonempty measured intersections contain only the
**0/1/0 contradiction terminal**.

These intersections concern the measured split prefixes. They do not enumerate
all global alternatives or prove absence of other equivalent representations.
The distinction is between reusing an identical checked record and recognizing
the same method or family on a different input. A shared contradiction terminal
does not establish a common nonterminal or boundary description.

The new pattern keys occupy **115,797 bytes**, payloads
**328,811 bytes**, and stored CNFs contain
**14,802 literal slots**. Duplication in these representations
is not automatically a net compression saving; lookup, checking, indexes and
reconstruction must be charged.

## Full costs and continuation

Mean sequence time is **71.68154 seconds**, including
**64.51870 seconds** initial catalog/query/serialization,
**4.04797 seconds** in workers, and **1.01341 seconds**
local expansion within workers. Updated global queries cost
**0.97963 seconds** and their serialization
**1.65191 seconds**. Parent restoration adds
**21.22320 seconds**. Materialization is allowed; the wrapper does not
record whether cache or fallback was used. No new full snapshot is produced.
Four batch copies total **3,134,402,560 logical bytes** per sequence. Final route
preparation costs **8.98011 seconds**, final global coverage
**61.77243 seconds**, and the complete producer
**266.62376 seconds**. Repetition establishes reproducibility, not a
matched speedup; lightweight artifact inspection overlapped the final producer
stage. Peak RAM is unmeasured.

History grows **733,184 bytes** to **784,097,280 bytes / 42,732 patterns**.
The structural delta uses **802,816 SQLite bytes / 37,148 compressed bytes**.
Separate reference evidence grows **6,283 -> 6,779 nodes**, adding
**3,682,304 SQLite bytes**, to **46,723,072 bytes / 3,187,613 compressed bytes**.
Startup checking dominates local expansion time, while reference evidence
contributes most new working database bytes. Neither quantity is a peak-memory bound.

All **299 tests** pass before production. Independent reconstruction disables
materialization and fresh discovery/reference search, checking both sequences,
every prefix, ten saved global queries, original SAT models and all **6,779
reference nodes**. Its **961.01602 seconds** are an audit cost. All **2,526 prior
artifacts / 42 manifests**, **140 prior source fingerprints** and **6,283 prior
reference payloads** remain unchanged. See the
[saved experiment](../experiments/results/cnf-case1063-discovery/README.md).

**Next:** case **1196 / index 36**, **43/181/549**, no pending split. Resume
`experiments.continue_cnf_case1063_discovery.restore_checkpoint` with
`experiments/results/cnf-case1063-discovery/report.json`, following **`next_selection`**,
not the completed initial case 1063 source. Preserve evidence **(1,42,156,82,1)**
and two bridges. Keep a checked session through subsequent batches. Five originals
remain structurally uncovered: **1064, 1196, 1302, 1376 and 1443**. Investigate
certified shared nonterminal or boundary
descriptions while expanding them; completion of this retained corpus would still
require evaluation on new unlabelled inputs and adversarial mixtures. Neither
complete coverage of these 83 cases nor repeated use of a familiar reduction
establishes a uniformly polynomial solution of arbitrary SAT.
