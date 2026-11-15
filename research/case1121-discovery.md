# Mixed-family discovery and a branch with no new admissions

2026-11-15. Two independent four-batch histories raise checked structural coverage
**73/83 -> 75/83**, completing **case 1121 (SAT)** and **case 1336 (UNSAT)** before
continuing into **case 1063**. Both produce identical operations and logical results.
The existing recognizers, policy and 32-state/twelve-advance batch limits are unchanged.
This is broader certified coverage of the retained corpus, not a new SAT algorithm.

## Every pending premise must persist

| Batch | Initial variables / clauses / literals | Entries | Stored | Result |
| --- | --- | ---: | ---: | --- |
| 0 | 41 / 174 / 513 | 7 | 7 | Case 1121 closes |
| 1 | 42 / 166 / 493 | 10 | 10 | Case 1336 closes |
| 2 | 43 / 170 / 501 | 32 | 18 | Case 1063 pending at 39 / 159 / 482 |
| 3 | 39 / 159 / 482 | 32 | 32 | Resumed split closes; another split remains at 22 / 89 / 309 |

The table gives selected residual sizes. Both newly covered originals have size
**48/204/612**; their full formulas and independent reference answers are retained.

The sequence charges **81 entries / 67 distinct inputs**, with **14 repeated
admissions** after interruption. All 67 inputs have stored records by the end.
Nevertheless, the final split remains pending: its first branch admits sixteen
inputs and completes, while its second branch admits **zero new inputs** and is still pending.
The preceding resumed split used the other sixteen admissions in the final batch.
An empty entered-but-unstored ledger therefore does not mean complete expansion.
Persist both unfinished admissions and the separate pending structural frontier.
Zero new admissions does not imply zero lookup, checking or preparation work.

| Original | Entries | Distinct inputs | Reentries | Stored |
| --- | ---: | ---: | ---: | ---: |
| 1063 | 64 | 50 | 14 | 50 |
| 1121 | 7 | 7 | 0 | 7 |
| 1336 | 10 | 10 | 0 | 10 |

## Affine projection and family transitions

The delta stores **31 probes, 23 eliminations, six binary-path reductions, three
unresolved records, two family terminals, one polarity transformation and one
affine projection**. The polarity transformation exposes an **11/10/22** Horn,
zero-valid terminal. A separate **6/15/51** terminal is one-valid, outside the
recorded Horn, dual-Horn and 2-CNF families. Overlaps remain explicit.

The projection rewrites **14/16/34 -> 13/14/30**. Two explicitly recognized affine
equations interact with twelve leftover clauses. Only one variable is absent from
those leftovers and can be eliminated. The checked boundary has one equation of
width two, encoded as **two clauses / four literals**. Its target continues through
a probe; projection alone is not a terminal classification.

An additional bounded diagnostic enumerates all **16,384 source assignments** and
**8,192 boundary assignments**, independently checking equality between the target
models and the existential projection of source models. It checks lifts for all
**72 satisfying boundary assignments**. This costs
**0.06950 seconds** beyond producer and cold replay. In general,
explicit boundary CNF encoding can be exponential in equation width; the existing
literal budget rejects oversized encodings. The example does not establish cheap
projection for every CNF or shared boundaries between unrelated originals.

## Measured identity reuse

Touched split prefixes contain **79 occurrences /
69 distinct records**, including **2 inherited records**.
Against the immediately preceding checkpoint's touched prefixes:

| Current original | Previous original | Exact shared records | Kinds |
| --- | --- | ---: | --- |
| 1063 | 1062 | 1 | {'retained_plan': 1} |
| 1121 | 1062 | 1 | {'retained_plan': 1} |
| 1336 | 1062 | 1 | {'retained_plan': 1} |

Every listed intersection contains the same **0/1/0 contradiction terminal**.
Each pair of current originals also shares exactly that one prefix record, with
no newly stored record shared across originals. These measurements establish
terminal reuse, without demonstrating shared nonterminal or boundary descriptions.

These are exact identity intersections, not all proof alternatives or semantic
equivalence searches. Similar reductions and equal size triples do not justify
certificate transport. The new keys contain **134,443 bytes**,
payloads **409,236 bytes**, and stored CNFs
**16,008 literal slots**. These are accounting observations,
not demonstrated net compression savings.

## Charged costs and next target

Mean complete sequence time is **72.02025 seconds**, including
**64.41599 seconds** initial catalog/query/serialization,
**4.41406 seconds** in workers, and **1.23698 seconds**
local expansion within workers. Updated global queries cost
**1.09000 seconds**, their serialization
**1.58363 seconds**. Parent restoration adds
**14.70057 seconds**; materialization is permitted but this wrapper
does not record whether the parent actually used its cache or fallback. No new
full snapshot is stored. Four batch copies total **3,130,576,896 logical bytes**
per sequence. Final cold route preparation costs **9.76638 seconds**
and global coverage **62.17005 seconds**, separately.
The full producer takes **260.88405 seconds**. These are descriptive
development repetitions, not a matched speedup comparison; peak RAM is unmeasured.

History grows **913,408 bytes** to **783,364,096 bytes / 42,678 patterns**.
The new structural delta uses **970,752 SQLite bytes / 47,697 compressed bytes**.
Reference evidence grows **5,612 -> 6,283 nodes**, adding **5,423,104 SQLite bytes**
to **43,040,768 bytes / 2,939,333 compressed bytes**. Thus reference evidence,
separately from reusable structure, contributes most new working database bytes.

All **299 tests** pass. Independent replay, with materialization, fresh recognition
and reference search disabled, checks both histories, every prefix, ten saved
global queries, original answers and all **6,283 reference nodes**. Its
**946.06368 seconds** are an audit cost. All **2,400 prior artifacts / 41
manifests**, **135 prior source fingerprints** and **5,612 old reference payloads**
remain unchanged. See [the saved experiment](../experiments/results/cnf-case1121-discovery/README.md).

**Next priority:** resume **case 1063 / index 15**, pending **22/89/309**, using
`experiments.continue_cnf_case1121_discovery.restore_checkpoint` and
`experiments/results/cnf-case1121-discovery/report.json`. Use **`next_selection`
and its pending split**, not the completed initial case 1121 source. The selector's
original-index list remains empty; scope 1063 comes from the checked dependency
path of the preceding batch. Preserve evidence **(1,42,156,78,1)** and two bridges.
Continue the pending branch before extending recognition claims. Reuse one
checked session because startup dominates local expansion. The next research gap
is a certified shared nonterminal or boundary description across originals;
observing another use of projection is insufficient. Eight originals remain
structurally uncovered; no unrestricted polynomial bound follows.
