# Share the complete audit across a bounded query group

Sharing one complete checkpoint audit across three queries reduces measured
sequence time **24.13644 -> 11.65332 seconds (51.72%)**. Both workflows independently
check each positive query proof on its exact snapshot and retain every snapshot.
They acquire identical records and finish with identical proofs and database
bytes. Structural coverage rises **8/24 -> 11/24**. Mean peak process memory
increases **7.70%** in this comparison; there is no persistent-storage saving.

## Changed audit granularity

The [frozen protocol](../experiments/results/cnf-grouped-checkpoints/protocol.json)
selects cases 23, 18 and 15 by their earlier enumeration costs. Both modes start
with the complete 1,799-pattern / 173-pair union and use the unchanged scoped
refinement policy in one live inventory. Each query has at most four batches of
128 recognition admissions and sixteen pair attempts. Both polarities and all
source-assumption closures remain charged. These are known development inputs,
not new holdouts; two repetitions reverse mode order in fresh processes.

The control performs a complete independent audit after every batch. The grouped
mode performs that audit once, at the end of the bounded three-query sequence.
Both modes also cold-check every issued positive coverage proof before proceeding
and preserve all intermediate archives. The original CNF is bound to the proof
root; only the exact split records used by that proof are fetched. Verification
forbids new acquisition and checks that the snapshot bytes remain unchanged.
An empty proof makes no negative claim, and coverage is not a SAT/UNSAT output.

The first two grouped snapshots are retained but **not globally certified during
the stream**. Unrelated semantic corruption can remain undetected until the final
full audit. The final globally verified checkpoint is published only after that
audit passes. Tests explicitly demonstrate that a valid query proof can coexist
with an unrelated corrupt record which the full checker rejects. Thus the modes
have the same final evidence and per-query positive-proof guarantees, with
different latency for whole-history error detection.

In an additive cost model with matched other work, let V(H_i) be complete audit
cost at snapshot i and let Q_i be its independent query-proof check. Grouping
replaces the sum of all V(H_i) by V(H_B); every Q_i and snapshot-persistence cost
remains. The removed work is the sum of complete audits before the final snapshot.
This is a reuse/accounting improvement, with unchanged recognition and expansion
costs. It does not give a size-independent verifier or a new SAT algorithm.

## Matched costs, including the regression

All three inputs close in one batch. Each stream acquires **147 patterns / 21
pairs / 42 source assumptions / 707 probes**. There are 147 distinct admissions,
with no repeated admission or exhausted budget in this sequence. The following
means include all three queries:

| Resource | Full audit each batch | Full audit at group end |
| --- | ---: | ---: |
| Initial restoration/setup, seconds | 0.05203 | 0.04217 |
| Query setup, seconds | 0.41480 | 0.42564 |
| Local expansion, seconds | 1.01401 | 1.01044 |
| Bookkeeping, seconds | 0.37871 | 0.38495 |
| Three cold query-proof checks, seconds | 0.67058 | 0.69552 |
| Complete cold audits, seconds | 19.32980 | 6.94599 |
| Compression, seconds | 1.99614 | 1.97996 |
| Whole sequence, seconds | 24.13644 | 11.65332 |
| Complete audits | 3 | 1 |
| Mean peak process RSS, bytes | 453,582,848 | 488,505,344 |

The timer includes all setup, expansion, report construction, snapshots, query
checks and scheduled full audits. Interpreter imports and the final summary write
are excluded; RSS includes imports and all phases. The parent history's earlier
acquisition is preserved and charged in its original experiments. The two grouped
RSS samples are 517,308,416 and 459,702,272 bytes, versus 452,739,072 and 454,426,624
for the control. Two repetitions do not explain the cause of this memory
regression or establish a universal speedup.

Each mode retains **5,342,834 compressed bytes** across its three snapshots.
The final per-mode database is **36,884,480 SQLite bytes / 1,840,638 gzip bytes**.
All corresponding snapshot hashes match across modes and repetitions. Grouping
does not reduce acquisition, snapshot count or historical storage.

A separate retrospective validator completely audits **all twelve intermediate
archives**, rechecks their query proofs, compares their full reachable catalogs,
and verifies immutable prefixes and exact cross-mode equality. Together with
parent and union checks this validation took **165.97 seconds**, outside the
paired stream measurements and partly concurrent with the test suite. It is
preserved as research-validation cost, not attributed to the operational saving.

## Structural coverage and actual component reuse

| Case | Input category | New patterns | Probes | Proof steps | Parent steps | Conditional nodes / depth |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 23 | Connected binary mixture | 53 | 255 | 73 | 20 | 8 / 4 |
| 18 | Random 3-CNF | 37 | 167 | 45 | 8 | 6 / 4 |
| 15 | Random 3-CNF | 57 | 285 | 73 | 16 | 10 / 5 |

The connected input has 69 variables and 266 clauses before preprocessing; the
previous selected frontier had 59 variables and maximum width four. Its final
proof contains **no component-decomposition step**. Eight conditional nodes and
63 checked unary reductions expose eight occurrences of contradiction and one
five-variable / four-clause 2-CNF leaf. This closes a connected interaction through
conditioning and reduction, rather than through the disjoint decomposition used
for case 22. The exact conditioning sources and shapes are preserved in its
[explanation](../experiments/results/cnf-grouped-checkpoints/case-23-explanation.json).

Case 18 has six conditional nodes, 38 reductions and seven contradiction leaf
occurrences. Case 15 has ten conditional nodes and sixty reductions, including a
polarity change. Its leaves are nine occurrences of contradiction, a twelve-variable
Horn/zero-valid residual, and an eight-variable residual recognized as both
zero-valid and one-valid. Family overlaps are retained. Only the contradiction is
shared within each proof; the respective unfolded counts are 80, 51 and 81 versus
73, 45 and 73 distinct steps. None of these depths identifies a fixed backdoor or
a minimum-depth proof.

**No later query proof uses a pattern newly acquired by an earlier query in this
group.** All reused proof steps predate the group. The measured speedup therefore
comes from sharing audit work, while these inputs still require distinct new
nonterminal states. General cross-input component reuse remains an open discovery
gap. Metadata labels are used for reporting; recognition and work selection
receive the CNFs and retained records.

Each proof uses one previously saved split, plus seven, five and nine newly
acquired splits respectively. The `reused_pairs` counter is zero because it counts
explicit calls that reacquire a saved pair; following an already acquired split
through the retained graph does not call that path. It does not mean zero reuse
of the parent history.

## Checkpoint and next gaps

[The union checkpoint](../experiments/results/cnf-grouped-checkpoints/checkpoint.json)
retains **1,946 patterns / 194 pairs / 17 inherited missing children**, with a
**665-step positive proof for eleven originals**. Thirteen originals remain
structurally unknown. Its own serialization is **36,884,480 SQLite bytes /
1,834,327 gzip bytes**. All **356 tests** pass, and every previous artifact,
source and existing manuscript proof block remains unchanged. The grouped mode
is optional; inference defaults are unchanged.

The remaining full audit is **59.6%** of grouped sequence time and compression is
**17.0%**. A next cost investigation can compare checked reuse of an immutable
parent with verification of its new records, making the trust boundary and full
fallback explicit; it must not trust a serialized validity flag. Larger groups
also trade delayed global error detection and more live state against repeated
verification. The observed RSS regression needs profiling before increasing
group size for a memory-saving claim.

For discovery, [the next bound source](../experiments/results/cnf-grouped-checkpoints/next-discovery.json)
is case **19**, with a selected **58-variable / 276-clause / 841-literal /
maximum-width-four** residual. All eight children of four saved splits are present
and uncovered. Continue from the new union, using historical timing only for
priority. Compact closure, uniformly bounded conditional depth and efficient
acquisition across arbitrary SAT remain unproved.
